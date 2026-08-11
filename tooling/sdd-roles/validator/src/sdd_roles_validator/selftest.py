"""`contract-lint selftest` — the build-item gate (spec WHERE criterion).

Runs the whole committed corpus against the validator and asserts, offline
and deterministically:
- registry <-> corpus bijection and corpus completeness (no second list to drift),
- VERSION <-> schema-const <-> corpus drift checks, metaschema + closedness,
- every corpus case behaves exactly as its expect.json annotation says,
- CHK-DET (double sweep, byte-identical), CHK-NET (socket-denying canary),
- CHK-NEUTRAL (live token scan + doctored fixture),
- CHK-SELF (temp-copy verdict stability + report-naming auditor),
- CHK-DEFER (item-2 cases DEFERRED, doctored green report rejected),
- the errors/ exit-1 family and the gate-wrap mapping-row corpus,
- the emitter projection goldens ×2 + verify green/red + failure family (item 4),
- the real catalog: registry + doctrine-body bijection + projection goldens (item 5),
- corpus arithmetic (types, families, exit-code coverage, mapping coverage).

This module is the only place tempfile is used (plan §4).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

from . import VALIDATOR_VERSION
from .emitter import DOCTRINE_PLACEHOLDER
from .loader import KNOWN_TYPES, SCHEMA_FILES, load_target
from .mounts import render_mount
from .registry import (
    CHECKS,
    IMPLEMENTED_ITEM2_IDS,
    UNIMPLEMENTED_ITEM2_IDS,
    NetGuard,
    load_neutral_tokens,
    run_validate,
    scan_neutral,
    scan_neutral_text,
)
from .report import canonical_dumps

VALID_DIRS = {
    "RoleRegistry": "role_registry",
    "HandoffContract": "handoff_contract",
    "StageLedgerEntry": "stage_ledger_entry",
    "GateOutcome": "gate_outcome",
    "DebugReport": "debug_report",
    "InvocationDescriptorSet": "invocation_descriptor_set",
    "SpecKitMapping": "speckit_mapping",
    "KernelConfig": "kernel_config",
    "KataPreregistration": "kata_preregistration",
    "KataWorkload": "kata_workload",
    "KataPlan": "kata_plan",
    "KataResults": "kata_results",
    "KataVerdict": "kata_verdict",
}

CLI_MODULES = {
    "contract-lint": "sdd_roles_validator.cli",
    "gate-wrap": "sdd_roles_validator.gate_wrap",
    "gate-runner": "sdd_roles_validator.runner",
    "write-guard": "sdd_roles_validator.guard",
    "role-emit": "sdd_roles_validator.emitter",
    "kata": "sdd_roles_validator.kata",
}

GOLDEN_SETS = (
    "orchestrator-green",
    "orchestrator-rework",
    "orchestrator-parent",
    "orchestrator-resume",
    "orchestrator-hooked",
    "orchestrator-unhooked",
)

GUARD_DECISION_CASES = 28
GUARD_MOUNT_GOLDENS = 4
EMITTER_TREES = 4
EMITTER_FAILURE_CASES = 3
CATALOG_TREES = 3
CATALOG_COMPOSITES = ("solo", "maker3", "checker3")
KATA_ARMS = 4
KATA_INSTANCES = 12
KATA_REPS = 5
KATA_CELLS = KATA_ARMS * KATA_INSTANCES * KATA_REPS  # 240
KATA_BRANCHES = (
    "six-roles",
    "three-roles",
    "gates-not-roles",
    "tamper",
    "solo",
)
KATA_REASONS = {
    "six-roles-earned",
    "three-roles",
    "gates-not-roles",
    "tamper-invalid",
    "default-solo",
}
KATA_FAILURE_CASES = 4  # prereg-edited, results-inconsistent, stamp-mismatch, reps-deviation (F2)


class Section:
    def __init__(self, name: str):
        self.name = name
        self.problems: list[str] = []

    def fail(self, problem: str) -> None:
        self.problems.append(problem)

    def as_dict(self) -> dict:
        return {
            "section": self.name,
            "outcome": "fail" if self.problems else "pass",
            "detail": "; ".join(self.problems[:6]),
        }


def _case_dirs(family_dir: Path) -> list[Path]:
    return sorted(
        p for p in family_dir.iterdir() if p.is_dir() and (p / "expect.json").is_file()
    )


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _walk_closedness(node, trail: str, problems: list[str]) -> None:
    if isinstance(node, dict):
        if node.get("type") == "object" and node.get("additionalProperties") is not False:
            problems.append(f"open object schema at {trail or '/'}")
        for key, value in node.items():
            _walk_closedness(value, f"{trail}/{key}", problems)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            _walk_closedness(value, f"{trail}/{i}", problems)


def _collect_consts(node, key_name: str, out: list) -> None:
    if isinstance(node, dict):
        candidate = node.get(key_name)
        if isinstance(candidate, dict) and "const" in candidate:
            out.append(candidate["const"])
        for value in node.values():
            _collect_consts(value, key_name, out)
    elif isinstance(node, list):
        for value in node:
            _collect_consts(value, key_name, out)


def _audit_report_naming(report: dict) -> list[str]:
    problems = []
    for entry in report.get("checks", []):
        if entry.get("outcome") == "fail":
            if not entry.get("check_id"):
                problems.append("fail entry lacks a check id")
            if "json_pointer" not in entry:
                problems.append("fail entry lacks a json_pointer field")
    return problems


def _audit_report_defer(report: dict) -> list[str]:
    """Inverted since build item 2: an implemented item-2 check must never
    report DEFERRED; an unimplemented one must never report anything else."""
    problems = []
    for entry in report.get("checks", []):
        if entry.get("phase") != "item-2":
            continue
        check_id = entry.get("check_id")
        outcome = entry.get("outcome")
        if check_id in IMPLEMENTED_ITEM2_IDS and outcome == "deferred":
            problems.append(f"implemented item-2 row '{check_id}' still reports deferred")
        if check_id in UNIMPLEMENTED_ITEM2_IDS and outcome != "deferred":
            problems.append(f"item-2 row '{check_id}' reported {outcome}")
    return problems


def _sweep(
    kernel_dir: Path, corpus_root: Path, targets: list[Path]
) -> tuple[dict[str, dict], str]:
    """Validate every target; return reports keyed by corpus-relative label
    (basenames collide across families) + an aggregate digest."""
    reports: dict[str, dict] = {}
    hasher = hashlib.sha256()
    for target in targets:
        report = run_validate(target, kernel_dir)
        label = target.relative_to(corpus_root).as_posix()
        reports[label] = report
        hasher.update(label.encode("utf-8"))
        hasher.update(canonical_dumps(report).encode("utf-8"))
    return reports, hasher.hexdigest()


def run_selftest(kernel_dir: Path) -> dict:
    corpus = kernel_dir / "corpus"
    invalid_dir = corpus / "invalid"
    valid_dir = corpus / "valid"
    sections: list[Section] = []

    checks_by_id = {c.check_id: c for c in CHECKS}
    artifact_family_ids = sorted(
        c.check_id for c in CHECKS if c.cluster in ("artifact", "ledger")
    )
    self_family_ids = sorted(c.check_id for c in CHECKS if c.cluster == "self")

    # -- structure: registry <-> corpus bijection + completeness -------------
    s = Section("structure")
    family_dirs = (
        sorted(p.name for p in invalid_dir.iterdir() if p.is_dir())
        if invalid_dir.is_dir()
        else []
    )
    if set(family_dirs) != set(checks_by_id):
        missing = sorted(set(checks_by_id) - set(family_dirs))
        extra = sorted(set(family_dirs) - set(checks_by_id))
        s.fail(f"invalid-family bijection broken (missing {missing}, extra {extra})")
    valid_names = (
        sorted(p.name for p in valid_dir.iterdir() if p.is_dir())
        if valid_dir.is_dir()
        else []
    )
    if set(valid_names) != set(VALID_DIRS):
        s.fail("valid corpus does not cover exactly the 13 schema types")
    for family in artifact_family_ids:
        if (invalid_dir / family).is_dir() and not _case_dirs(invalid_dir / family):
            s.fail(f"family {family} has no case dirs")
    if not (corpus / "runs" / "cold-start").is_dir():
        s.fail("runs/cold-start fixture missing")
    if not sorted((corpus / "errors").glob("*/case.json")):
        s.fail("errors/ exit-1 family missing")
    if not sorted((corpus / "gatewrap").glob("*/invocation.json")):
        s.fail("gatewrap/ mapping corpus missing")
    orch = corpus / "orchestrator"
    for needed in ("descriptors-stub.json", "goldens.json", "stubs/role_stub.py", "stubs/gate_stub.py"):
        if not (orch / needed).is_file():
            s.fail(f"orchestrator fixture {needed} missing")
    for name in GOLDEN_SETS:
        if not (corpus / "runs" / name).is_dir():
            s.fail(f"golden run set {name} missing")
    for needed in ("common/kernel-config.json", "common/role-registry.json", "common/workspace"):
        if not (corpus / "guard" / needed).exists():
            s.fail(f"guard fixture {needed} missing")
    if not (corpus / "guard" / "decisions").is_dir():
        s.fail("guard decision corpus missing")
    if not (corpus / "guard" / "mounts").is_dir():
        s.fail("guard mount goldens missing")
    for needed in ("common/role-registry.json", "common/bodies", "failures"):
        if not (corpus / "emitter" / needed).exists():
            s.fail(f"emitter fixture {needed} missing")
    for needed in ("catalog/role-registry.json", "catalog/bodies"):
        if not (kernel_dir / needed).exists():
            s.fail(f"catalog {needed} missing")
    if not (corpus / "catalog-projections").is_dir():
        s.fail("catalog-projections golden family missing")
    sections.append(s)

    # -- drift + metaschema + closedness -------------------------------------
    s = Section("schema-drift")
    version = (kernel_dir / "VERSION").read_text(encoding="utf-8").strip()
    try:
        from jsonschema import Draft202012Validator

        for atype, fname in sorted(SCHEMA_FILES.items()):
            schema = _read_json(kernel_dir / "schemas" / fname)
            Draft202012Validator.check_schema(schema)
            problems: list[str] = []
            _walk_closedness(schema, "", problems)
            for p in problems:
                s.fail(f"{fname}: {p}")
            versions: list = []
            _collect_consts(schema, "schema_version", versions)
            if not versions or any(v != version for v in versions):
                s.fail(f"{fname}: schema_version const drift against VERSION")
            atypes: list = []
            _collect_consts(schema, "artifact_type", atypes)
            if not atypes or any(a != atype for a in atypes):
                s.fail(f"{fname}: artifact_type const drift")
    except Exception as exc:
        s.fail(f"metaschema validation error: {type(exc).__name__}")
    descriptor_instance = kernel_dir / "descriptors" / "invocation-descriptors.json"
    if not descriptor_instance.is_file():
        s.fail("committed descriptor instance missing")
    else:
        if _read_json(descriptor_instance).get("schema_version") != version:
            s.fail("descriptor instance schema_version drift")
    sections.append(s)

    # -- corpus sweeps --------------------------------------------------------
    valid_targets = [valid_dir / name for name in sorted(VALID_DIRS)]
    cold_start = corpus / "runs" / "cold-start"
    invalid_targets: list[tuple[Path, dict]] = []
    for family in artifact_family_ids:
        for case in _case_dirs(invalid_dir / family):
            invalid_targets.append((case, _read_json(case / "expect.json")))

    all_targets = valid_targets + [cold_start] + [c for c, _ in invalid_targets]
    with NetGuard() as sweep_guard:
        reports, digest_one = _sweep(kernel_dir, corpus, all_targets)
        _, digest_two = _sweep(kernel_dir, corpus, all_targets)

    exit_codes_seen: set[int] = set()

    s = Section("valid-corpus")
    for target in valid_targets + [cold_start]:
        report = reports[target.relative_to(corpus).as_posix()]
        exit_codes_seen.add(report["exit_code"])
        if report["exit_code"] != 0:
            fails = [e for e in report["checks"] if e["outcome"] == "fail"]
            first = fails[0] if fails else {}
            s.fail(
                f"{target.name}: expected pass, got exit {report['exit_code']} "
                f"({first.get('check_id', '')} {first.get('artifact', '')} "
                f"{first.get('json_pointer', '')})"
            )
    for name, atype in sorted(VALID_DIRS.items()):
        _, artifacts, _ledgers = load_target(valid_dir / name)
        if not any(a.atype == atype for a in artifacts):
            s.fail(f"{name}: no artifact of type {atype}")
        if any(
            a.data.get("schema_version") != version
            for a in artifacts
            if isinstance(a.data, dict) and "schema_version" in a.data
        ):
            s.fail(f"{name}: corpus schema_version drift")
    sections.append(s)

    s = Section("invalid-corpus")
    flipped_ok: list[str] = []
    for case, expect in invalid_targets:
        report = reports[case.relative_to(corpus).as_posix()]
        exit_codes_seen.add(report["exit_code"])
        label = f"{case.parent.name}/{case.name}"
        check_id = expect.get("check_id", "")
        entries = [e for e in report["checks"] if e["check_id"] == check_id]
        expected = expect.get("expected")
        if expected == "deferred":
            # The item-2 flip (C5 / corpus-guide): the committed
            # expected_when_implemented is now the executable verdict.
            expected = expect.get("expected_when_implemented")
            flipped_ok.append(label)
        if expected == "fail":
            if report["exit_code"] != 2:
                s.fail(f"{label}: expected exit 2, got {report['exit_code']}")
            fails = [e for e in entries if e["outcome"] == "fail"]
            if not fails:
                s.fail(f"{label}: no fail entry for {check_id}")
            wanted = expect.get("json_pointer")
            if wanted is not None and not any(
                e["json_pointer"] == wanted for e in fails
            ):
                s.fail(f"{label}: no {check_id} fail entry at pointer {wanted}")
        elif expected == "pass":
            if report["exit_code"] != 0:
                s.fail(f"{label}: expected exit 0, got {report['exit_code']}")
            all_fails = [e for e in report["checks"] if e["outcome"] == "fail"]
            if all_fails:
                first = all_fails[0]
                s.fail(
                    f"{label}: pass-when-implemented case produced a fail "
                    f"({first.get('check_id')} {first.get('json_pointer')})"
                )
        else:
            s.fail(f"{label}: expect.json has unknown expected value")
    sections.append(s)

    # -- CHK-DET: double sweep byte-identity + differing-pair fixture --------
    s = Section("chk-det")
    if digest_one != digest_two:
        s.fail("two corpus sweeps differed (nondeterministic output)")
    pair_dir = invalid_dir / "CHK-DET"
    pairs = sorted(pair_dir.rglob("*.json"))
    fixture_jsons = [p for p in pairs if p.name != "expect.json"]
    if len(fixture_jsons) >= 2:
        a, b = fixture_jsons[0].read_bytes(), fixture_jsons[1].read_bytes()
        if a == b:
            s.fail("CHK-DET fixture pair is not a differing pair")
    else:
        s.fail("CHK-DET differing-pair fixture missing")
    sections.append(s)

    # -- CHK-NET: canary + sweep guard + module scan --------------------------
    s = Section("chk-net")
    if sweep_guard.attempts:
        s.fail("network access attempted during the corpus sweep")
    canary_raised = False
    with NetGuard() as guard:
        try:
            socket.create_connection(("127.0.0.1", 9), timeout=0.1)
        except OSError:
            canary_raised = True
    if not (canary_raised and guard.attempts):
        s.fail("socket-denying guard did not block the canary connection")
    banned = {"requests", "urllib3", "httpx"} & set(sys.modules)
    if banned:
        s.fail(f"network-capable modules imported: {sorted(banned)}")
    sections.append(s)

    # -- CHK-NEUTRAL: live scan + doctored fixture ----------------------------
    s = Section("chk-neutral")
    live = scan_neutral(kernel_dir)
    for label, _ptr, detail in live[:5]:
        s.fail(f"live tree not neutral: {label}: {detail}")
    tokens = load_neutral_tokens(kernel_dir)
    doctored = sorted((invalid_dir / "CHK-NEUTRAL").rglob("schema-fixture.json"))
    if not doctored:
        s.fail("CHK-NEUTRAL doctored fixture missing")
    elif not scan_neutral_text(
        "fixture", doctored[0].read_text(encoding="utf-8"), tokens
    ):
        s.fail("doctored fixture not flagged by the neutral scan")
    sections.append(s)

    # -- CHK-SELF: temp-copy stability + report-naming auditor ----------------
    s = Section("chk-self")
    with tempfile.TemporaryDirectory() as tmp:
        for target in [c for c, _ in invalid_targets] + valid_targets:
            rel = target.relative_to(corpus).as_posix()
            copy = Path(tmp) / target.name
            shutil.copytree(target, copy)
            original = canonical_dumps(reports[rel])
            moved = canonical_dumps(run_validate(copy, kernel_dir))
            if original != moved:
                s.fail(f"{rel}: verdict changed under temp-path copy")
            shutil.rmtree(copy)
    for label, report in sorted(reports.items()):
        for problem in _audit_report_naming(report):
            s.fail(f"{label}: {problem}")
    doctored_self = sorted((invalid_dir / "CHK-SELF").rglob("report.json"))
    if not doctored_self:
        s.fail("CHK-SELF doctored report fixture missing")
    elif not _audit_report_naming(_read_json(doctored_self[0])):
        s.fail("doctored unnamed-finding report not rejected by the auditor")
    sections.append(s)

    # -- CHK-DEFER: the anti-rot rule, both directions ------------------------
    s = Section("chk-defer")
    for label, report in sorted(reports.items()):
        for problem in _audit_report_defer(report):
            s.fail(f"{label}: {problem}")
    lingering = sum(
        1
        for report in reports.values()
        for e in report["checks"]
        if e["outcome"] == "deferred"
    )
    if lingering:
        s.fail(f"{lingering} DEFERRED entries remain after the item-2 flip")
    item2_families = [
        c.check_id for c in CHECKS if c.phase == "item-2" or c.phase == "dual"
    ]
    covered = {label.split("/", 1)[0] for label in flipped_ok}
    for family in sorted(item2_families):
        if family not in covered:
            s.fail(f"no flipped item-2 corpus case exercised for {family}")
    doctored_green = sorted((invalid_dir / "CHK-DEFER").rglob("report.json"))
    if not doctored_green:
        s.fail("CHK-DEFER doctored report fixture missing")
    elif not _audit_report_defer(_read_json(doctored_green[0])):
        s.fail("doctored lingering-DEFERRED report not rejected by the auditor")
    sections.append(s)

    # -- errors/ exit-1 family -------------------------------------------------
    s = Section("errors-family")
    for case_file in sorted((corpus / "errors").glob("*/case.json")):
        spec = _read_json(case_file)
        module = CLI_MODULES.get(spec.get("command", ""))
        if module is None:
            s.fail(f"{case_file.parent.name}: unknown command")
            continue
        args = [
            str(a)
            .replace("<KERNEL>", str(kernel_dir))
            .replace("<PY>", sys.executable)
            for a in spec.get("args", [])
        ]
        proc = subprocess.run(
            [sys.executable, "-m", module, *args],
            capture_output=True,
            cwd=case_file.parent,
        )
        exit_codes_seen.add(proc.returncode)
        if proc.returncode != spec.get("expected_exit"):
            s.fail(
                f"{case_file.parent.name}: exit {proc.returncode} "
                f"!= {spec.get('expected_exit')}"
            )
    sections.append(s)

    # -- gate-wrap mapping corpus ----------------------------------------------
    s = Section("gatewrap-corpus")
    seen_pairs: set[tuple[str, int]] = set()
    descriptor_path = kernel_dir / "descriptors" / "invocation-descriptors.json"
    for case_file in sorted((corpus / "gatewrap").glob("*/invocation.json")):
        spec = _read_json(case_file)
        harness = spec["harness"]
        tool_exit = int(spec["tool_exit"])
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                CLI_MODULES["gate-wrap"],
                "--descriptors",
                str(descriptor_path),
                "--harness",
                harness,
                "--",
                sys.executable,
                "-c",
                f"raise SystemExit({tool_exit})",
            ],
            capture_output=True,
            text=True,
        )
        seen_pairs.add((harness, tool_exit))
        if proc.stdout != spec["expected_stdout"] or proc.returncode != int(
            spec["expected_exit"]
        ):
            s.fail(
                f"{case_file.parent.name}: got ('{proc.stdout.strip()}', {proc.returncode}), "
                f"expected ('{spec['expected_stdout'].strip()}', {spec['expected_exit']})"
            )
    descriptors = _read_json(descriptor_path)
    for row in descriptors.get("rows", []):
        for entry in row.get("exit_code_map", []):
            pair = (row["harness"], int(entry["tool_exit"]))
            if pair not in seen_pairs:
                s.fail(f"mapping row {pair} has no gate-wrap corpus case")
    sections.append(s)

    # -- orchestrator golden runs (ADR 0002) ----------------------------------
    def _tree_map(root: Path) -> dict[str, str]:
        return {
            p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*"))
            if p.is_file()
        }

    def _compare_trees(section: Section, label: str, got: Path, want: Path) -> None:
        got_map, want_map = _tree_map(got), _tree_map(want)
        if got_map != want_map:
            missing = sorted(set(want_map) - set(got_map))[:3]
            extra = sorted(set(got_map) - set(want_map))[:3]
            drift = sorted(
                k for k in set(got_map) & set(want_map) if got_map[k] != want_map[k]
            )[:3]
            section.fail(
                f"{label}: tree diverges (missing {missing}, extra {extra}, drift {drift})"
            )

    def _validate_green(section: Section, label: str, target: Path) -> None:
        report = run_validate(target, kernel_dir)
        fails = [e for e in report["checks"] if e["outcome"] == "fail"]
        deferred = [e for e in report["checks"] if e["outcome"] == "deferred"]
        if report["exit_code"] != 0 or fails:
            first = fails[0] if fails else {}
            section.fail(
                f"{label}: golden run dir not green "
                f"({first.get('check_id')} {first.get('artifact')} {first.get('json_pointer')})"
            )
        if deferred:
            section.fail(f"{label}: golden report carries DEFERRED rows")

    def _validate_red(section: Section, label: str, target: Path, check_id: str) -> None:
        report = run_validate(target, kernel_dir)
        fails = [e for e in report["checks"] if e["outcome"] == "fail"]
        if report["exit_code"] != 2 or not fails:
            section.fail(f"{label}: negative-control run dir did not validate red")
        others = sorted({e["check_id"] for e in fails} - {check_id})
        if others:
            section.fail(f"{label}: unexpected failing checks {others}")
        if not any(e["check_id"] == check_id for e in fails):
            section.fail(f"{label}: expected {check_id} failure absent")
        if any(e["outcome"] == "deferred" for e in report["checks"]):
            section.fail(f"{label}: report carries DEFERRED rows")

    orch_fixture = corpus / "orchestrator"
    recipes = _read_json(orch_fixture / "goldens.json")

    def _execute_recipe(spec: dict, dest: Path) -> None:
        scenario = orch_fixture / "scenarios" / spec["scenario"]
        ws = dest / "workspace"
        rd = dest / "run-dir"
        shutil.copytree(scenario / "workspace-template", ws)
        if spec.get("mount"):
            proc = subprocess.run(
                [
                    sys.executable, "-m", CLI_MODULES["write-guard"], "mount",
                    "--descriptors", str(orch_fixture / "descriptors-stub.json"),
                    "--harness", spec["mount"],
                    "--registry", str(scenario / "role-registry.json"),
                    "--out", str(ws),
                ],
                capture_output=True, text=True,
            )
            if proc.returncode != 0:
                raise AssertionError(f"{spec['golden']}: mount exit {proc.returncode}")
        for run in spec["runs"]:
            argv = [
                sys.executable, "-m", CLI_MODULES["gate-runner"], "run",
                "--kernel", str(kernel_dir),
                "--workspace", str(ws),
                "--run-dir", str(rd),
                "--config", str(scenario / "kernel-config.json"),
                "--registry", str(scenario / "role-registry.json"),
                "--descriptors", str(orch_fixture / "descriptors-stub.json"),
                "--harness", run["harness"],
                "--run-id", run["run_id"],
                "--clock", recipes["clock"],
                "--bind", f"python={sys.executable}",
                "--bind", f"fixture_dir={orch_fixture}",
            ]
            if run.get("parent"):
                argv += ["--parent", run["parent"]]
            proc = subprocess.run(argv, capture_output=True, text=True)
            if proc.returncode != run.get("expected_exit", 0):
                raise AssertionError(
                    f"{spec['golden']}/{run['run_id']}: exit {proc.returncode} "
                    f"({proc.stderr.strip().splitlines()[-1] if proc.stderr else ''})"
                )

    s = Section("orchestrator-goldens")
    with tempfile.TemporaryDirectory() as tmp:
        for spec in recipes["sets"]:
            golden = corpus / "runs" / spec["golden"]
            golden_rd = (
                golden / "completed" / "run-dir"
                if spec.get("resume_set")
                else golden / "run-dir"
            )
            golden_ws = (
                golden / "completed" / "workspace-after"
                if spec.get("resume_set")
                else golden / "workspace-after"
            )
            try:
                one = Path(tmp) / f"{spec['golden']}-1"
                two = Path(tmp) / f"{spec['golden']}-2"
                one.mkdir()
                two.mkdir()
                _execute_recipe(spec, one)
                _execute_recipe(spec, two)
            except AssertionError as exc:
                s.fail(str(exc))
                continue
            _compare_trees(s, f"{spec['golden']}: run-dir vs golden", one / "run-dir", golden_rd)
            _compare_trees(s, f"{spec['golden']}: workspace vs golden", one / "workspace", golden_ws)
            _compare_trees(s, f"{spec['golden']}: execution 1 vs 2", one / "run-dir", two / "run-dir")
            if spec.get("red_check"):
                _validate_red(s, spec["golden"], golden_rd, spec["red_check"])
            else:
                _validate_green(s, spec["golden"], golden_rd)
    # serialization presence: every serialized handoff copy byte-matches its
    # run-dir source, and the serialized ledger is a prefix of the final one
    green = corpus / "runs" / "orchestrator-green"
    for copy in sorted((green / "workspace-after" / ".specify" / "handoffs").glob("*.json")):
        src = green / "run-dir" / copy.name
        if not src.is_file() or src.read_bytes() != copy.read_bytes():
            s.fail(f"serialized handoff {copy.name} does not byte-match its source")
    for copy in sorted((green / "workspace-after" / ".specify" / "ledgers").glob("*.ndjson")):
        src = green / "run-dir" / copy.name
        if not src.is_file() or not src.read_bytes().startswith(copy.read_bytes()):
            s.fail(f"serialized ledger {copy.name} is not a prefix of the final ledger")
    # the hooked set proves the stateless live block (item-3 S6/HP4): the
    # blocked write leaves no ledger trace and never lands in the workspace
    hooked = corpus / "runs" / "orchestrator-hooked"
    hooked_ledger = b"".join(p.read_bytes() for p in sorted((hooked / "run-dir").glob("*.ndjson")))
    if b"tests/test_base.py" in hooked_ledger:
        s.fail("hooked golden: the blocked write left a trace in the ledger")
    tampered_target = hooked / "workspace-after" / "tests" / "test_base.py"
    if not tampered_target.is_file() or b"tampered" in tampered_target.read_bytes():
        s.fail("hooked golden: the tamper write landed despite the mounted hook")
    sections.append(s)

    # -- guard decision corpus (item-3, ADR 0002 extended) ---------------------
    s = Section("guard-decisions")
    guard_dir = corpus / "guard"
    guard_common = guard_dir / "common"
    decision_dirs = sorted(
        p for p in (guard_dir / "decisions").iterdir() if p.is_dir()
    ) if (guard_dir / "decisions").is_dir() else []
    with tempfile.TemporaryDirectory() as tmp:
        for case in decision_dirs:
            spec = _read_json(case / "case.json")
            expect = _read_json(case / "expect.json")
            outcomes = []
            for attempt in (1, 2):
                base = Path(tmp) / f"{case.name}-{attempt}"
                ws = base / "ws"
                shutil.copytree(guard_common / "workspace", ws)
                if spec.get("setup") == "symlink-escape":
                    outside = base / "outside"
                    outside.mkdir(parents=True)
                    (ws / "link").symlink_to(outside)
                if spec.get("setup") == "handoff-symlink-escape":
                    # A handoff.draft that is really a symlink onto a protected
                    # test — the laundering attack the carve-out must refuse.
                    rd = base / "run-dir"
                    rd.mkdir(parents=True, exist_ok=True)
                    (rd / "handoff.draft").symlink_to(ws / "tests" / "test_base.py")
                binds = {
                    "{workspace}": str(ws),
                    "{case}": str(case),
                    "{orchestrator}": str(corpus / "orchestrator"),
                    "{kernel}": str(kernel_dir),
                }
                argv = [
                    sys.executable, "-m", CLI_MODULES["write-guard"], "decide",
                    "--kernel", str(kernel_dir),
                    "--config", str(guard_common / "kernel-config.json"),
                    "--registry", str(guard_common / "role-registry.json"),
                    "--workspace", str(ws),
                    "--run-dir", str(base / "run-dir"),
                    "--role", spec["role"],
                ]
                for extra in spec.get("argv_extra", []):
                    for token, value in binds.items():
                        extra = extra.replace(token, value)
                    argv.append(extra)
                proc = subprocess.run(
                    argv, input=(case / spec["stdin"]).read_bytes(), capture_output=True
                )
                exit_codes_seen.add(proc.returncode)
                outcomes.append((proc.returncode, proc.stdout))
            if outcomes[0] != outcomes[1]:
                s.fail(f"{case.name}: nondeterministic across the double run")
            code, stdout = outcomes[0]
            if code != expect["exit_code"] or stdout.decode("utf-8") != expect["stdout"]:
                s.fail(
                    f"{case.name}: got exit {code} stdout {stdout!r}, "
                    f"expected {expect['exit_code']} {expect['stdout']!r}"
                )
    sections.append(s)

    # -- guard mount goldens ----------------------------------------------------
    s = Section("guard-mount")
    rows_by_harness: dict[str, Path] = {}
    for df in (
        kernel_dir / "descriptors" / "invocation-descriptors.json",
        orch_fixture / "descriptors-stub.json",
    ):
        for row in _read_json(df).get("rows", []):
            if isinstance(row, dict) and isinstance(row.get("hooks"), dict):
                rows_by_harness[row["harness"]] = df
    mount_dirs = sorted(
        p for p in (guard_dir / "mounts").iterdir() if p.is_dir()
    ) if (guard_dir / "mounts").is_dir() else []
    if len(mount_dirs) != len(rows_by_harness):
        s.fail(
            f"mount goldens ({len(mount_dirs)}) do not cover the "
            f"hooks-bearing rows ({len(rows_by_harness)})"
        )
    with tempfile.TemporaryDirectory() as tmp:
        for mdir in mount_dirs:
            df = rows_by_harness.get(mdir.name)
            if df is None:
                s.fail(f"{mdir.name}: no hooks-bearing descriptor row")
                continue
            renders = []
            failed_mount = False
            for attempt in (1, 2):
                out = Path(tmp) / f"{mdir.name}-{attempt}"
                proc = subprocess.run(
                    [
                        sys.executable, "-m", CLI_MODULES["write-guard"], "mount",
                        "--descriptors", str(df),
                        "--harness", mdir.name,
                        "--registry", str(guard_common / "role-registry.json"),
                        "--out", str(out),
                    ],
                    capture_output=True,
                )
                if proc.returncode != 0:
                    s.fail(f"{mdir.name}: mount exit {proc.returncode}")
                    failed_mount = True
                    break
                renders.append(out)
            if failed_mount:
                continue
            _compare_trees(s, f"mount {mdir.name}: vs golden", renders[0], mdir)
            _compare_trees(s, f"mount {mdir.name}: render 1 vs 2", renders[0], renders[1])
    sections.append(s)

    # -- emitter projection goldens (item-4, ADR 0002 extended / ADR 0003) ----
    s = Section("emitter-projections")
    emitter_dir = corpus / "emitter"
    emitter_common = emitter_dir / "common"
    proj_rows: dict[str, Path] = {}
    for df in (
        kernel_dir / "descriptors" / "invocation-descriptors.json",
        orch_fixture / "descriptors-stub.json",
    ):
        for row in _read_json(df).get("rows", []):
            if isinstance(row, dict) and isinstance(row.get("projection"), dict):
                proj_rows[row["harness"]] = df
    tree_dirs = sorted(
        p
        for p in emitter_dir.iterdir()
        if p.is_dir() and p.name not in ("common", "failures")
    ) if emitter_dir.is_dir() else []
    if len(tree_dirs) != len(proj_rows):
        s.fail(
            f"emitter trees ({len(tree_dirs)}) do not cover the "
            f"projection-bearing rows ({len(proj_rows)})"
        )

    def _emit_argv(subcmd: str, df: Path, harness: str, out: Path) -> list[str]:
        return [
            sys.executable, "-m", CLI_MODULES["role-emit"], subcmd,
            "--kernel", str(kernel_dir),
            "--descriptors", str(df),
            "--harness", harness,
            "--registry", str(emitter_common / "role-registry.json"),
            "--bodies", str(emitter_common / "bodies"),
            "--out", str(out),
        ]

    with tempfile.TemporaryDirectory() as tmp:
        for tdir in tree_dirs:
            df = proj_rows.get(tdir.name)
            if df is None:
                s.fail(f"{tdir.name}: no projection-bearing descriptor row")
                continue
            renders = []
            failed_emit = False
            for attempt in (1, 2):
                out = Path(tmp) / f"{tdir.name}-{attempt}"
                proc = subprocess.run(
                    _emit_argv("project", df, tdir.name, out), capture_output=True
                )
                exit_codes_seen.add(proc.returncode)
                if proc.returncode != 0:
                    s.fail(f"{tdir.name}: project exit {proc.returncode}")
                    failed_emit = True
                    break
                renders.append(out)
            if failed_emit:
                continue
            _compare_trees(s, f"emit {tdir.name}: vs golden", renders[0], tdir)
            _compare_trees(s, f"emit {tdir.name}: render 1 vs 2", renders[0], renders[1])
    # the never-emit rule (spec FP6): no projection golden carries a
    # lifecycle-command token
    for tdir in tree_dirs:
        for path in sorted(p for p in tdir.rglob("*") if p.is_file()):
            if b"speckit." in path.read_bytes():
                s.fail(
                    f"{path.relative_to(corpus).as_posix()}: "
                    "emitted bytes contain 'speckit.'"
                )
    # mount-copy identity (spec HP3): the projected copy byte-equals the
    # shared render_mount output — one rendering source, two consumers
    emitter_registry = (
        _read_json(emitter_common / "role-registry.json")
        if (emitter_common / "role-registry.json").is_file()
        else {}
    )
    for tdir in tree_dirs:
        df = proj_rows.get(tdir.name)
        if df is None:
            continue
        row = next(
            r for r in _read_json(df)["rows"] if r.get("harness") == tdir.name
        )
        for target in row["projection"]["targets"]:
            if target["kind"] != "mount-copy":
                continue
            golden_file = tdir / target["path_template"]
            if not golden_file.is_file():
                s.fail(f"{tdir.name}: mount-copy golden {target['path_template']} missing")
                continue
            want = render_mount(
                tdir.name, row.get("hooks") or {}, emitter_registry.get("roles", [])
            )
            if golden_file.read_bytes() != want:
                s.fail(f"{tdir.name}: mount-copy diverges from render_mount output")
    sections.append(s)

    # -- emitter verify + failure family ---------------------------------------
    s = Section("emitter-verify")
    for tdir in tree_dirs:
        df = proj_rows.get(tdir.name)
        if df is None:
            continue
        proc = subprocess.run(
            _emit_argv("verify", df, tdir.name, tdir), capture_output=True, text=True
        )
        exit_codes_seen.add(proc.returncode)
        if proc.returncode != 0:
            s.fail(f"{tdir.name}: verify on the committed golden exited {proc.returncode}")
    failure_cases = sorted(
        (emitter_dir / "failures").glob("*/case.json")
    ) if (emitter_dir / "failures").is_dir() else []
    for case_file in failure_cases:
        spec = _read_json(case_file)
        module = CLI_MODULES.get(spec.get("command", ""))
        if module is None:
            s.fail(f"{case_file.parent.name}: unknown command")
            continue
        args = [str(a).replace("<KERNEL>", str(kernel_dir)) for a in spec.get("args", [])]
        outcomes = []
        for attempt in (1, 2):
            proc = subprocess.run(
                [sys.executable, "-m", module, *args],
                capture_output=True, text=True, cwd=case_file.parent,
            )
            outcomes.append((proc.returncode, proc.stdout, proc.stderr))
        if outcomes[0] != outcomes[1]:
            s.fail(f"{case_file.parent.name}: nondeterministic across the double run")
        code, stdout, stderr = outcomes[0]
        exit_codes_seen.add(code)
        if code != spec.get("expected_exit"):
            s.fail(f"{case_file.parent.name}: exit {code} != {spec.get('expected_exit')}")
        for frag in spec.get("expect_stdout_contains", []):
            if frag not in stdout:
                s.fail(f"{case_file.parent.name}: stdout lacks '{frag}'")
        for frag in spec.get("expect_stderr_contains", []):
            if frag not in stderr:
                s.fail(f"{case_file.parent.name}: stderr lacks '{frag}'")
        no_out = spec.get("expect_no_out_dir")
        if no_out and (case_file.parent / no_out).exists():
            s.fail(f"{case_file.parent.name}: failed render left output behind")
    sections.append(s)

    # -- the real catalog: registry + doctrine bodies + projections (item 5) --
    s = Section("catalog")
    catalog_dir = kernel_dir / "catalog"
    catalog_registry_path = catalog_dir / "role-registry.json"
    bodies_dir = catalog_dir / "bodies"
    catalog_tree_root = corpus / "catalog-projections"
    catalog_trees = sorted(
        p for p in catalog_tree_root.iterdir() if p.is_dir()
    ) if catalog_tree_root.is_dir() else []
    catalog_ok = True
    try:
        catalog_registry = _read_json(catalog_registry_path)
        import jsonschema

        jsonschema.validate(
            catalog_registry,
            _read_json(kernel_dir / "schemas" / SCHEMA_FILES["role_registry"]),
        )
    except Exception as exc:
        s.fail(f"catalog registry unreadable or schema-invalid: {type(exc).__name__}")
        catalog_registry = {}
        catalog_ok = False
    role_ids = {
        r["id"] for r in catalog_registry.get("roles", []) if isinstance(r, dict)
    }
    body_files = sorted(bodies_dir.glob("*.md")) if bodies_dir.is_dir() else []
    body_stems = {p.stem for p in body_files}
    for missing in sorted(role_ids - body_stems):
        s.fail(f"role '{missing}' has no doctrine body")
        catalog_ok = False
    for stray in sorted(body_stems - role_ids):
        s.fail(f"body '{stray}.md' names no registry role")
        catalog_ok = False
    neutral_tokens = load_neutral_tokens(kernel_dir)
    for body in body_files:
        text = body.read_text(encoding="utf-8")
        if "Sources:" not in text or "## Stage exit" not in text:
            s.fail(f"{body.name}: F2 layout markers missing")
        if body.stem in CATALOG_COMPOSITES and "Merged role:" not in text:
            s.fail(f"{body.name}: composite lacks the 'Merged role:' opener")
        if DOCTRINE_PLACEHOLDER in text:
            s.fail(f"{body.name}: contains the placeholder marker")
        for _label, _ptr, detail in scan_neutral_text(body.name, text, neutral_tokens)[:3]:
            s.fail(f"{body.name}: doctrine not harness-neutral: {detail}")
    real_descriptor_path = kernel_dir / "descriptors" / "invocation-descriptors.json"
    real_proj_harnesses = sorted(
        row["harness"]
        for row in _read_json(real_descriptor_path).get("rows", [])
        if isinstance(row, dict) and isinstance(row.get("projection"), dict)
    )
    if [p.name for p in catalog_trees] != real_proj_harnesses:
        s.fail(
            f"catalog trees {[p.name for p in catalog_trees]} do not cover the "
            f"real projection rows {real_proj_harnesses}"
        )
        catalog_ok = False

    def _catalog_argv(subcmd: str, harness: str, out: Path) -> list[str]:
        return [
            sys.executable, "-m", CLI_MODULES["role-emit"], subcmd,
            "--kernel", str(kernel_dir),
            "--descriptors", str(real_descriptor_path),
            "--harness", harness,
            "--registry", str(catalog_registry_path),
            "--bodies", str(bodies_dir),
            "--out", str(out),
        ]

    if catalog_ok:
        with tempfile.TemporaryDirectory() as tmp:
            for tdir in catalog_trees:
                renders = []
                failed_render = False
                for attempt in (1, 2):
                    out = Path(tmp) / f"{tdir.name}-{attempt}"
                    proc = subprocess.run(
                        _catalog_argv("project", tdir.name, out), capture_output=True
                    )
                    exit_codes_seen.add(proc.returncode)
                    if proc.returncode != 0:
                        s.fail(f"{tdir.name}: catalog project exit {proc.returncode}")
                        failed_render = True
                        break
                    renders.append(out)
                if failed_render:
                    continue
                _compare_trees(s, f"catalog {tdir.name}: vs golden", renders[0], tdir)
                _compare_trees(
                    s, f"catalog {tdir.name}: render 1 vs 2", renders[0], renders[1]
                )
                proc = subprocess.run(
                    _catalog_argv("verify", tdir.name, tdir), capture_output=True
                )
                if proc.returncode != 0:
                    s.fail(f"{tdir.name}: catalog verify exited {proc.returncode}")
        for tdir in catalog_trees:
            for path in sorted(p for p in tdir.rglob("*.md") if p.is_file()):
                text = path.read_text(encoding="utf-8")
                if DOCTRINE_PLACEHOLDER in text:
                    s.fail(
                        f"{path.relative_to(corpus).as_posix()}: "
                        "a role rendered without its doctrine"
                    )
                for _label, _ptr, detail in scan_neutral_text(
                    path.name, text, neutral_tokens
                )[:3]:
                    s.fail(
                        f"{path.relative_to(corpus).as_posix()}: "
                        f"rendered card not harness-neutral: {detail}"
                    )
    sections.append(s)

    # -- orchestrator resume + tamper refusal ---------------------------------
    s = Section("orchestrator-resume")
    resume_spec = next(x for x in recipes["sets"] if x.get("resume_set"))
    scenario = orch_fixture / "scenarios" / resume_spec["scenario"]
    golden = corpus / "runs" / resume_spec["golden"]

    def _resume_argv(rd: Path, ws: Path) -> list[str]:
        return [
            sys.executable, "-m", CLI_MODULES["gate-runner"], "resume",
            "--kernel", str(kernel_dir),
            "--workspace", str(ws),
            "--run-dir", str(rd),
            "--config", str(rd / "kernel-config.json"),
            "--registry", str(rd / "role-registry.json"),
            "--descriptors", str(orch_fixture / "descriptors-stub.json"),
            "--harness", resume_spec["runs"][0]["harness"],
            "--clock", recipes["clock"],
            "--bind", f"python={sys.executable}",
            "--bind", f"fixture_dir={orch_fixture}",
        ]

    with tempfile.TemporaryDirectory() as tmp:
        rd = Path(tmp) / "run-dir"
        ws = Path(tmp) / "workspace"
        shutil.copytree(golden / "interrupted" / "run-dir", rd)
        shutil.copytree(golden / "interrupted" / "workspace", ws)
        proc = subprocess.run(_resume_argv(rd, ws), capture_output=True, text=True)
        if proc.returncode != 0:
            s.fail(f"resume exited {proc.returncode}: {proc.stderr.strip()[-200:]}")
        else:
            _compare_trees(s, "resume: run-dir vs completed", rd, golden / "completed" / "run-dir")
            _compare_trees(
                s, "resume: workspace vs completed", ws, golden / "completed" / "workspace-after"
            )
        # tamper: a doctored genesis pin must refuse to resume, writing nothing
        rd2 = Path(tmp) / "run-dir-tampered"
        ws2 = Path(tmp) / "workspace-tampered"
        shutil.copytree(golden / "interrupted" / "run-dir", rd2)
        shutil.copytree(golden / "interrupted" / "workspace", ws2)
        ledger = next(rd2.glob("*.ndjson"))
        raw = ledger.read_bytes()
        marker = b'"kernel_config_digest":"'
        at = raw.index(marker) + len(marker)
        doctored = raw[:at] + b"0" * 16 + raw[at + 16 :]  # same length, wrong pin
        ledger.write_bytes(doctored)
        before = doctored
        proc = subprocess.run(_resume_argv(rd2, ws2), capture_output=True, text=True)
        if proc.returncode != 2:
            s.fail(f"tampered resume exited {proc.returncode}, expected refusal (2)")
        if "resume refused" not in proc.stderr:
            s.fail("tampered resume did not report a refusal")
        if ledger.read_bytes() != before:
            s.fail("tampered resume modified the ledger")
    sections.append(s)

    # -- the kata rig: plan / analyze / report determinism + digest triangle --
    s = Section("kata")
    from .kata_analyzer import PREREG_CONSTANTS, PREREG_DIGEST, rate10k, wilson_interval

    kata_dir = corpus / "kata"
    catalog_dir = kernel_dir / "catalog"
    kata_module = CLI_MODULES["kata"]

    def _kata(subcmd: str, *pairs: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", kata_module, subcmd, *pairs],
            capture_output=True, text=True,
        )

    # (1) digest triangle: the committed pre-registration's own constants block
    # must byte-agree with the frozen code digest (ADR 0004; the anti-p-hacking
    # bind). Recompute over exactly the PREREG_CONSTANTS keys.
    committed_prereg_path = catalog_dir / "kata-preregistration.json"
    prereg_ok = True
    if not committed_prereg_path.is_file():
        s.fail("committed kata-preregistration.json missing")
        prereg_ok = False
    else:
        committed = _read_json(committed_prereg_path)
        try:
            block = {k: committed[k] for k in PREREG_CONSTANTS}
        except KeyError as exc:
            s.fail(f"pre-registration missing constant {exc}")
            prereg_ok = False
            block = None
        if block is not None:
            recomputed = hashlib.sha256(
                canonical_dumps(block).encode("utf-8")
            ).hexdigest()
            if recomputed != PREREG_DIGEST:
                # name the first diverging constant for the pointer
                diverged = [
                    k for k in PREREG_CONSTANTS if committed.get(k) != PREREG_CONSTANTS[k]
                ]
                ptr = f"/{diverged[0]}" if diverged else "/prereg_digest"
                s.fail(f"committed pre-registration constants drift from code at {ptr}")
                prereg_ok = False
            if committed.get("prereg_digest") != PREREG_DIGEST:
                s.fail("committed pre-registration self-stamp != code PREREG_DIGEST")
                prereg_ok = False

    prereg_arg = str(kata_dir / "preregistration.json")
    plan_arg = str(kata_dir / "plan.json")
    golden_plan = kata_dir / "plan.json"

    # (2) plan determinism: render x2, byte-equal, vs golden; cell count.
    with tempfile.TemporaryDirectory() as tmp:
        renders = []
        for attempt in (1, 2):
            out = Path(tmp) / f"plan-{attempt}.json"
            proc = _kata(
                "plan", "--kernel", str(kernel_dir),
                "--registry", str(catalog_dir / "role-registry.json"),
                "--prereg", prereg_arg,
                "--workload", str(kata_dir / "workload.json"),
                "--reps", str(KATA_REPS),
                "--default-model", "UNBOUND",
                "--out", str(out),
            )
            exit_codes_seen.add(proc.returncode)
            if proc.returncode != 0:
                s.fail(f"kata plan exited {proc.returncode}: {proc.stderr.strip()[-120:]}")
                break
            renders.append(out.read_bytes())
        if len(renders) == 2:
            if renders[0] != renders[1]:
                s.fail("kata plan is nondeterministic across a double render")
            if golden_plan.is_file() and renders[0] != golden_plan.read_bytes():
                s.fail("kata plan output diverges from the committed golden")
    if golden_plan.is_file():
        planned = _read_json(golden_plan)
        if len(planned.get("cells", [])) != KATA_CELLS:
            s.fail(
                f"golden plan has {len(planned.get('cells', []))} cells, "
                f"expected {KATA_CELLS}"
            )
        cells = planned.get("cells", [])
        if cells != sorted(cells, key=lambda c: (c["arm"], c["instance"], c["rep"])):
            s.fail("golden plan cells are not canonically sorted")

    # (3) analyze determinism: each branch results -> verdict golden x2; all 5
    # decision reasons covered; the tamper branch proves precedence.
    reasons_seen: set[str] = set()
    with tempfile.TemporaryDirectory() as tmp:
        for branch in KATA_BRANCHES:
            res = kata_dir / f"results-{branch}.json"
            golden_v = kata_dir / f"verdict-{branch}.json"
            if not res.is_file() or not golden_v.is_file():
                s.fail(f"kata branch '{branch}' fixture or verdict golden missing")
                continue
            renders = []
            for attempt in (1, 2):
                out = Path(tmp) / f"{branch}-{attempt}.json"
                proc = _kata(
                    "analyze", "--kernel", str(kernel_dir),
                    "--plan", plan_arg, "--prereg", prereg_arg,
                    "--results", str(res), "--out", str(out),
                )
                exit_codes_seen.add(proc.returncode)
                if proc.returncode != 0:
                    s.fail(f"kata analyze '{branch}' exited {proc.returncode}: "
                           f"{proc.stderr.strip()[-120:]}")
                    break
                renders.append(out.read_bytes())
            if len(renders) != 2:
                continue
            if renders[0] != renders[1]:
                s.fail(f"kata analyze '{branch}' is nondeterministic")
            if renders[0] != golden_v.read_bytes():
                s.fail(f"kata analyze '{branch}' diverges from its verdict golden")
            reasons_seen.add(_read_json(golden_v).get("decision_reason"))
    if reasons_seen != KATA_REASONS:
        missing = sorted(KATA_REASONS - reasons_seen)
        s.fail(f"kata branches do not cover all decision reasons (missing {missing})")
    # tamper precedence: the tamper branch's raw operands would otherwise win C
    # (six-roles matrix), yet it must resolve to tamper-invalid / winner none.
    tamper_v = kata_dir / "verdict-tamper.json"
    if tamper_v.is_file():
        tv = _read_json(tamper_v)
        if tv.get("winner") != "none" or tv.get("decision_reason") != "tamper-invalid":
            s.fail("tamper branch did not resolve to winner none / tamper-invalid")
        if not tv.get("tamper_fail"):
            s.fail("tamper branch verdict does not carry tamper_fail")

    # (4) Wilson integer-exactness: recompute the committed (k,n)->bounds table.
    wilson_ref = kata_dir / "wilson-exactness.json"
    if wilson_ref.is_file():
        ref = _read_json(wilson_ref)
        for case in ref.get("cases", []):
            lo, hi = wilson_interval(case["k"], case["n"])
            if (lo, hi) != (case["lo"], case["hi"]):
                s.fail(
                    f"wilson bounds drift for k={case['k']} n={case['n']}: "
                    f"got ({lo},{hi}) committed ({case['lo']},{case['hi']})"
                )
            if rate10k(case["k"], case["n"]) != case["rate"]:
                s.fail(f"rate10k drift for k={case['k']} n={case['n']}")
    else:
        s.fail("wilson-exactness.json fixture missing")

    # (5) report determinism: verdict -> scorecard golden x2; neutral prose.
    scorecard = kata_dir / "scorecard.md"
    if scorecard.is_file():
        with tempfile.TemporaryDirectory() as tmp:
            renders = []
            for attempt in (1, 2):
                out = Path(tmp) / f"scorecard-{attempt}.md"
                proc = _kata(
                    "report", "--kernel", str(kernel_dir),
                    "--verdict", str(kata_dir / "verdict-six-roles.json"),
                    "--out", str(out),
                )
                exit_codes_seen.add(proc.returncode)
                if proc.returncode != 0:
                    s.fail(f"kata report exited {proc.returncode}")
                    break
                renders.append(out.read_bytes())
            if len(renders) == 2:
                if renders[0] != renders[1]:
                    s.fail("kata report is nondeterministic")
                if renders[0] != scorecard.read_bytes():
                    s.fail("kata report diverges from the scorecard golden")
        neutral_tokens = load_neutral_tokens(kernel_dir)
        for _label, _ptr, detail in scan_neutral_text(
            "scorecard.md", scorecard.read_text(encoding="utf-8"), neutral_tokens
        )[:3]:
            s.fail(f"scorecard not harness-neutral: {detail}")
    else:
        s.fail("scorecard.md golden missing")

    # (6) failures family: each doctored input exits 2 writing nothing (tamper
    # trio; each flips this section alone).
    kata_failures = sorted(
        (kata_dir / "failures").glob("*/case.json")
    ) if (kata_dir / "failures").is_dir() else []
    for case_file in kata_failures:
        spec = _read_json(case_file)
        module = CLI_MODULES.get(spec.get("command", ""))
        if module is None:
            s.fail(f"kata failure {case_file.parent.name}: unknown command")
            continue
        args = [str(a).replace("<KERNEL>", str(kernel_dir)) for a in spec.get("args", [])]
        outcomes = []
        for attempt in (1, 2):
            proc = subprocess.run(
                [sys.executable, "-m", module, *args],
                capture_output=True, text=True, cwd=case_file.parent,
            )
            outcomes.append((proc.returncode, proc.stdout, proc.stderr))
        if outcomes[0] != outcomes[1]:
            s.fail(f"kata failure {case_file.parent.name}: nondeterministic")
        code, _stdout, stderr = outcomes[0]
        exit_codes_seen.add(code)
        if code != spec.get("expected_exit"):
            s.fail(f"kata failure {case_file.parent.name}: exit {code} "
                   f"!= {spec.get('expected_exit')}")
        for frag in spec.get("expect_stderr_contains", []):
            if frag not in stderr:
                s.fail(f"kata failure {case_file.parent.name}: stderr lacks '{frag}'")
        no_out = spec.get("expect_no_out_dir")
        if no_out and (case_file.parent / no_out).exists():
            s.fail(f"kata failure {case_file.parent.name}: left output behind")
    sections.append(s)

    # -- corpus arithmetic ------------------------------------------------------
    s = Section("arithmetic")
    if len(family_dirs) != 27:
        s.fail(f"expected 27 invalid families, found {len(family_dirs)}")
    for code in (0, 1, 2):
        if code not in exit_codes_seen:
            s.fail(f"exit code {code} not exercised by the corpus")
    for family in self_family_ids:
        if not (invalid_dir / family).is_dir():
            s.fail(f"self-integrity family {family} missing")
    if len(recipes.get("sets", [])) != len(GOLDEN_SETS):
        s.fail("goldens.json recipes do not cover the committed golden sets")
    if len(flipped_ok) != 12:
        s.fail(f"expected 12 flipped item-2 cases, found {len(flipped_ok)}")
    if len(decision_dirs) != GUARD_DECISION_CASES:
        s.fail(
            f"expected {GUARD_DECISION_CASES} guard decision cases, "
            f"found {len(decision_dirs)}"
        )
    if len(mount_dirs) != GUARD_MOUNT_GOLDENS:
        s.fail(
            f"expected {GUARD_MOUNT_GOLDENS} mount goldens, found {len(mount_dirs)}"
        )
    if len(tree_dirs) != EMITTER_TREES:
        s.fail(f"expected {EMITTER_TREES} emitter trees, found {len(tree_dirs)}")
    if len(failure_cases) != EMITTER_FAILURE_CASES:
        s.fail(
            f"expected {EMITTER_FAILURE_CASES} emitter failure cases, "
            f"found {len(failure_cases)}"
        )
    if len(catalog_trees) != CATALOG_TREES:
        s.fail(f"expected {CATALOG_TREES} catalog trees, found {len(catalog_trees)}")
    # kata rig counts (the pre-registered shape, gate-pinned)
    kata_result_branches = sorted(
        (corpus / "kata").glob("results-*.json")
    )
    kata_verdict_goldens = sorted((corpus / "kata").glob("verdict-*.json"))
    if len(kata_result_branches) < len(KATA_BRANCHES):
        s.fail(
            f"expected >= {len(KATA_BRANCHES)} kata result branches, "
            f"found {len(kata_result_branches)}"
        )
    for branch in KATA_BRANCHES:
        if not (corpus / "kata" / f"verdict-{branch}.json").is_file():
            s.fail(f"kata branch verdict golden missing: {branch}")
    kata_failure_cases = sorted((corpus / "kata" / "failures").glob("*/case.json"))
    if len(kata_failure_cases) != KATA_FAILURE_CASES:
        s.fail(
            f"expected {KATA_FAILURE_CASES} kata failure cases, "
            f"found {len(kata_failure_cases)}"
        )
    if (corpus / "kata" / "plan.json").is_file():
        kplan = _read_json(corpus / "kata" / "plan.json")
        if len(kplan.get("cells", [])) != KATA_CELLS:
            s.fail(f"kata plan cells != {KATA_CELLS}")
        if len(kplan.get("arms", [])) != KATA_ARMS:
            s.fail(f"kata plan arms != {KATA_ARMS}")
        if len(kplan.get("instances", [])) != KATA_INSTANCES:
            s.fail(f"kata plan instances != {KATA_INSTANCES}")
    sections.append(s)

    failed = [x for x in sections if x.problems]
    return {
        "schema_version": version,
        "validator_version": VALIDATOR_VERSION,
        "sections": [x.as_dict() for x in sections],
        "summary": {
            "pass": len(sections) - len(failed),
            "fail": len(failed),
            "flipped_cases": len(flipped_ok),
            "guard_cases": len(decision_dirs),
            "emitter_trees": len(tree_dirs),
            "catalog_trees": len(catalog_trees),
            "kata_cells": KATA_CELLS,
            "kata_result_branches": len(kata_result_branches),
            "kata_verdict_goldens": len(kata_verdict_goldens),
            "deferred_entries": sum(
                1
                for report in reports.values()
                for e in report["checks"]
                if e["outcome"] == "deferred"
            ),
        },
        "exit_code": 2 if failed else 0,
    }
