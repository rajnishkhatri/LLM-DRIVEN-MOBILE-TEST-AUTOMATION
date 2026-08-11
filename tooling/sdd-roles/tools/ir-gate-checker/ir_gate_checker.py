#!/usr/bin/env python3
"""ir-gate-checker — o7's IR gate engine (ADR 0005; tool id "ir-gate-checker").

Deterministic, pre-device, zero-compilation checker for a committed
`TestCaseIR` + `LocatorCandidate` manifest. Runs the seven checks the o7
interpreter spec fixes (spec "IR gate" row + EARS failure paths):

  schemaValid     IR parses, satisfies the spec-derived closed shape,
                  healPolicy is the fixed "NONE", and the irDigest seal
                  matches the canonical IR (sha256 over the compact
                  sorted-key JSON with the irDigest field removed)
  opcodeClosed    only {TAP, TYPE, SWIPE, WAIT, ASSERT, LAUNCH, NAVIGATE};
                  assertion kinds only {TEXT_EQUALS, ELEMENT_PRESENT,
                  VALUE_CHECK}
  boundedWaits    every step carries a finite positive integer timeoutMs
                  (determinism control, not style — spec EARS)
  locatorManifest every locator the IR references resolves in the committed
                  manifest with a non-empty candidate cascade; no orphans
  noLiteralCreds  vault-key indirection only: a sensitive step must use
                  {"vaultRef": ...}, and no literal value may match the
                  fixed credential token list
  ambiguityClear  no step flagged ambiguous survives to replay
  dryRun          a no-device structural walk of every step succeeds
                  (per-opcode field contracts; walks only closed-set
                  opcodes — closure itself is opcodeClosed's finding)

All seven checks ALWAYS run and are enumerated in the report — there is no
short-circuit (a short-circuiting check is the exact mutant the hardener is
told to kill). A check that cannot evaluate (unreadable input) FAILS with a
not-evaluable violation: fail-closed, never fail-open.

Exit taxonomy (ADR 0005): 0 = all seven pass (report written); 2 = any
violation (report written); 3 = usage error (nothing written). The report
carries tool_version (the gate-runner refuses versionless outcomes) and the
ADR threshold {ir_gate_violations_max: 0}.

The authoritative TestCaseIR JSON Schema is the o7 repo's T05-regenerated
schema; this tool enforces the SPEC-DERIVED contract documented in README.md
and must be reconciled against T05 at integration time (seam, not a fork).

Subcommands:
  check    --ir <path> [--manifest <path>] --report <path>
  seal     --ir <path> --out <path>      (authoring utility: fix the irDigest
                                          seal; not part of the gate contract)
  selftest                               (fixture corpus x2, byte-stable)
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

TOOL_ID = "ir-gate-checker"
TOOL_VERSION = "1.0.0"
CONTRACT = "o7-spec-derived.1"

OPCODES = ("TAP", "TYPE", "SWIPE", "WAIT", "ASSERT", "LAUNCH", "NAVIGATE")
ASSERTION_KINDS = ("TEXT_EQUALS", "ELEMENT_PRESENT", "VALUE_CHECK")
SYNC_VALUES = ("WAIT_FOR_IDLE", "NONE")
CHECK_ORDER = (
    "schemaValid",
    "opcodeClosed",
    "boundedWaits",
    "locatorManifest",
    "noLiteralCreds",
    "ambiguityClear",
    "dryRun",
)
THRESHOLD = {"name": "ir_gate_violations_max", "value": 0}

TOP_REQUIRED = ("testCaseId", "irDigest", "healPolicy", "steps")
TOP_OPTIONAL = ("schemaVersion",)
STEP_KEYS = ("opcode", "timeoutMs", "syncAfter", "target", "value", "assertion", "ambiguous", "sensitive")

# Fixed, versioned credential-token list (case-insensitive substring match on
# literal string values). Extending it is a contract change, never a tweak.
CRED_TOKENS = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "bearer",
    "credential",
    "private_key",
)

# Per-opcode structural walk contract: (target, value, assertion) each one of
# "required" | "forbidden" | "optional".
WALK_CONTRACT = {
    "TAP": ("required", "forbidden", "forbidden"),
    "TYPE": ("required", "required", "forbidden"),
    "SWIPE": ("required", "optional", "forbidden"),
    "WAIT": ("forbidden", "forbidden", "forbidden"),
    "ASSERT": ("required", "forbidden", "required"),
    "LAUNCH": ("forbidden", "required", "forbidden"),
    "NAVIGATE": ("forbidden", "required", "forbidden"),
}


class Usage(Exception):
    pass


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_dumps(obj) -> str:
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def canonical_ir_digest(ir: dict) -> str:
    """The seal: sha256 over the compact sorted-key JSON, irDigest removed."""
    body = {k: v for k, v in ir.items() if k != "irDigest"}
    blob = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256_hex(blob.encode("utf-8"))


def _parse_flags(args: list[str], spec: dict[str, bool]) -> dict[str, str]:
    out: dict[str, str] = {}
    i = 0
    while i < len(args):
        token = args[i]
        if not token.startswith("--") or token[2:] not in spec:
            raise Usage(f"unrecognized argument '{token}'")
        if i + 1 >= len(args):
            raise Usage(f"missing value for '{token}'")
        out[token[2:]] = args[i + 1]
        i += 2
    for name, required in spec.items():
        if required and name not in out:
            raise Usage(f"--{name} is required")
    return out


# ------------------------------------------------------------- the checks --


def _is_vault_ref(value) -> bool:
    return isinstance(value, dict) and set(value) == {"vaultRef"}


def _steps_of(ir) -> list:
    steps = ir.get("steps")
    return steps if isinstance(steps, list) else []


def check_schema_valid(ir: dict) -> list[tuple[str, str]]:
    v: list[tuple[str, str]] = []
    known = set(TOP_REQUIRED) | set(TOP_OPTIONAL)
    for key in sorted(set(ir) - known):
        v.append((f"/{key}", "unknown top-level field (closed shape)"))
    for key in TOP_REQUIRED:
        if key not in ir:
            v.append((f"/{key}", "required field missing"))
    if not isinstance(ir.get("testCaseId", ""), str) or ir.get("testCaseId") == "":
        v.append(("/testCaseId", "must be a non-empty string"))
    declared = ir.get("irDigest")
    if not (isinstance(declared, str) and len(declared) == 64 and all(c in "0123456789abcdef" for c in declared)):
        v.append(("/irDigest", "must be 64 lowercase hex characters (sha256)"))
    elif canonical_ir_digest(ir) != declared:
        v.append(("/irDigest", "seal broken: digest does not match the canonical IR"))
    if "healPolicy" in ir and ir.get("healPolicy") != "NONE":
        v.append(("/healPolicy", "fixed to \"NONE\" by the o7 spec (no self-heal, ever)"))
    steps = ir.get("steps")
    if steps is not None and not isinstance(steps, list):
        v.append(("/steps", "must be an array"))
    for i, step in enumerate(_steps_of(ir)):
        base = f"/steps/{i}"
        if not isinstance(step, dict):
            v.append((base, "step must be an object"))
            continue
        for key in sorted(set(step) - set(STEP_KEYS)):
            v.append((f"{base}/{key}", "unknown step field (closed shape)"))
        if not isinstance(step.get("opcode", ""), str):
            v.append((f"{base}/opcode", "must be a string"))
        if "timeoutMs" in step and (isinstance(step["timeoutMs"], bool) or not isinstance(step["timeoutMs"], int)):
            v.append((f"{base}/timeoutMs", "must be an integer"))
        if "syncAfter" not in step:
            v.append((f"{base}/syncAfter", "required field missing"))
        elif step["syncAfter"] not in SYNC_VALUES:
            v.append((f"{base}/syncAfter", "must be WAIT_FOR_IDLE or NONE"))
        if "target" in step:
            target = step["target"]
            if not (isinstance(target, dict) and set(target) == {"locatorRef"} and isinstance(target.get("locatorRef"), str) and target["locatorRef"]):
                v.append((f"{base}/target", "must be {\"locatorRef\": <non-empty string>}"))
        if "value" in step:
            value = step["value"]
            if not (isinstance(value, str) or _is_vault_ref(value)):
                v.append((f"{base}/value", "must be a string or {\"vaultRef\": <key>}"))
            elif _is_vault_ref(value) and not (isinstance(value["vaultRef"], str) and value["vaultRef"]):
                v.append((f"{base}/value/vaultRef", "must be a non-empty string"))
        if "assertion" in step:
            a = step["assertion"]
            if not (isinstance(a, dict) and set(a) <= {"kind", "expected"} and isinstance(a.get("kind"), str)):
                v.append((f"{base}/assertion", "must be {\"kind\": <string>, \"expected\"?: <string>}"))
            elif "expected" in a and not isinstance(a["expected"], str):
                v.append((f"{base}/assertion/expected", "must be a string"))
        for flag in ("ambiguous", "sensitive"):
            if flag in step and not isinstance(step[flag], bool):
                v.append((f"{base}/{flag}", "must be a boolean"))
    return v


def check_opcode_closed(ir: dict) -> list[tuple[str, str]]:
    v = []
    for i, step in enumerate(_steps_of(ir)):
        if not isinstance(step, dict):
            continue
        opcode = step.get("opcode")
        if opcode not in OPCODES:
            v.append((f"/steps/{i}/opcode", f"opcode outside the closed set {list(OPCODES)}"))
        a = step.get("assertion")
        if isinstance(a, dict) and a.get("kind") is not None and a.get("kind") not in ASSERTION_KINDS:
            v.append((f"/steps/{i}/assertion/kind", f"assertion kind outside the closed set {list(ASSERTION_KINDS)}"))
    return v


def check_bounded_waits(ir: dict) -> list[tuple[str, str]]:
    v = []
    for i, step in enumerate(_steps_of(ir)):
        if not isinstance(step, dict):
            continue
        timeout = step.get("timeoutMs")
        if timeout is None:
            v.append((f"/steps/{i}/timeoutMs", "every step must carry a finite timeoutMs (unbounded wait breaks pass^k determinism)"))
        elif isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0:
            v.append((f"/steps/{i}/timeoutMs", "must be a finite integer > 0"))
    return v


def check_locator_manifest(ir: dict, manifest, manifest_error: str | None) -> list[tuple[str, str]]:
    refs_used = []
    for i, step in enumerate(_steps_of(ir)):
        if isinstance(step, dict) and isinstance(step.get("target"), dict):
            ref = step["target"].get("locatorRef")
            if isinstance(ref, str) and ref:
                refs_used.append((i, ref))
    if manifest_error is not None:
        if refs_used or manifest is None:
            return [("", f"not evaluable: {manifest_error}")]
        return []
    entries = manifest.get("locators") if isinstance(manifest, dict) else None
    if not isinstance(entries, list):
        return [("/locators", "manifest must carry a locators array")]
    by_ref: dict[str, int] = {}
    v = []
    for j, entry in enumerate(entries):
        if not isinstance(entry, dict) or not isinstance(entry.get("ref"), str) or not entry["ref"]:
            v.append((f"/locators/{j}", "manifest entry must carry a non-empty ref"))
            continue
        if entry["ref"] in by_ref:
            v.append((f"/locators/{j}/ref", f"duplicate manifest ref '{entry['ref']}'"))
        by_ref[entry["ref"]] = j
        candidates = entry.get("candidates")
        if not (isinstance(candidates, list) and candidates):
            v.append((f"/locators/{j}/candidates", "empty candidate cascade is vacuously exhausted (would hard-fail at runtime)"))
    for i, ref in refs_used:
        if ref not in by_ref:
            v.append((f"/steps/{i}/target/locatorRef", f"orphan locator '{ref}': not present in the committed manifest"))
    return v


def check_no_literal_creds(ir: dict) -> list[tuple[str, str]]:
    v = []
    for i, step in enumerate(_steps_of(ir)):
        if not isinstance(step, dict):
            continue
        value = step.get("value")
        literal = value if isinstance(value, str) else None
        if step.get("sensitive") is True and literal is not None:
            v.append((f"/steps/{i}/value", "sensitive step carries a literal value: vault-key indirection only"))
        candidates = []
        if literal is not None:
            candidates.append((f"/steps/{i}/value", literal))
        a = step.get("assertion")
        if isinstance(a, dict) and isinstance(a.get("expected"), str):
            candidates.append((f"/steps/{i}/assertion/expected", a["expected"]))
        for pointer, text in candidates:
            lowered = text.lower()
            for tok in CRED_TOKENS:
                if tok in lowered:
                    v.append((pointer, f"literal value matches credential token '{tok}' (vault-key indirection only)"))
                    break
    return v


def check_ambiguity_clear(ir: dict) -> list[tuple[str, str]]:
    return [
        (f"/steps/{i}/ambiguous", "ambiguous step must be resolved before commit, never at replay")
        for i, step in enumerate(_steps_of(ir))
        if isinstance(step, dict) and step.get("ambiguous") is True
    ]


def check_dry_run(ir: dict) -> list[tuple[str, str]]:
    steps = _steps_of(ir)
    if not steps:
        return [("/steps", "structural walk impossible: no steps to walk")]
    v = []
    for i, step in enumerate(steps):
        base = f"/steps/{i}"
        if not isinstance(step, dict):
            v.append((base, "unwalkable step: not an object"))
            continue
        contract = WALK_CONTRACT.get(step.get("opcode"))
        if contract is None:
            continue  # closure is opcodeClosed's finding; the walk skips it
        for field, rule in zip(("target", "value", "assertion"), contract):
            present = field in step
            if rule == "required" and not present:
                v.append((f"{base}/{field}", f"{step['opcode']} step requires {field}"))
            elif rule == "forbidden" and present:
                v.append((f"{base}/{field}", f"{step['opcode']} step must not carry {field}"))
        a = step.get("assertion")
        if step.get("opcode") == "ASSERT" and isinstance(a, dict):
            kind = a.get("kind")
            if kind in ("TEXT_EQUALS", "VALUE_CHECK") and "expected" not in a:
                v.append((f"{base}/assertion/expected", f"{kind} assertion requires expected"))
            elif kind == "ELEMENT_PRESENT" and "expected" in a:
                v.append((f"{base}/assertion/expected", "ELEMENT_PRESENT assertion must not carry expected"))
    return v


# -------------------------------------------------------------- the gate --


def run_checks(ir_bytes: bytes | None, ir_error: str | None,
               manifest_bytes: bytes | None, manifest_error: str | None) -> dict:
    ir = None
    if ir_error is None:
        try:
            ir = json.loads(ir_bytes.decode("utf-8"))
            if not isinstance(ir, dict):
                ir, ir_error = None, "IR is not a JSON object"
        except (ValueError, UnicodeDecodeError):
            ir, ir_error = None, "IR is not valid JSON"
    manifest = None
    if manifest_error is None and manifest_bytes is not None:
        try:
            manifest = json.loads(manifest_bytes.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            manifest, manifest_error = None, "manifest is not valid JSON"

    results: dict[str, list[tuple[str, str]]] = {}
    if ir is None:
        detail = f"not evaluable: {ir_error}"
        results["schemaValid"] = [("", ir_error or "IR unavailable")]
        for check in CHECK_ORDER[1:]:
            results[check] = [("", detail)]
    else:
        results["schemaValid"] = check_schema_valid(ir)
        results["opcodeClosed"] = check_opcode_closed(ir)
        results["boundedWaits"] = check_bounded_waits(ir)
        results["locatorManifest"] = check_locator_manifest(ir, manifest, manifest_error)
        results["noLiteralCreds"] = check_no_literal_creds(ir)
        results["ambiguityClear"] = check_ambiguity_clear(ir)
        results["dryRun"] = check_dry_run(ir)

    checks = []
    total = 0
    for check in CHECK_ORDER:
        violations = sorted(results[check])
        total += len(violations)
        checks.append(
            {
                "id": check,
                "outcome": "fail" if violations else "pass",
                "violations": [{"pointer": p, "detail": d} for p, d in violations],
            }
        )
    declared = ir.get("irDigest") if isinstance(ir, dict) else None
    return {
        "artifact_type": "ir_gate_report",
        "tool": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "contract": CONTRACT,
        "inputs": {
            "ir_sha256": sha256_hex(ir_bytes) if ir_bytes is not None else None,
            "manifest_sha256": sha256_hex(manifest_bytes) if manifest_bytes is not None else None,
        },
        "ir_digest": {
            "declared": declared if isinstance(declared, str) else None,
            "computed": canonical_ir_digest(ir) if isinstance(ir, dict) else None,
        },
        "checks": checks,
        "violations_total": total,
        "threshold": dict(THRESHOLD),
        "verdict": "green" if total == 0 else "red",
    }


def _read_input(path_str: str | None, label: str):
    """Returns (bytes|None, error|None). A missing/unreadable input is a
    check failure (fail-closed), never a usage error."""
    if path_str is None:
        return None, None
    path = Path(path_str)
    try:
        return path.read_bytes(), None
    except OSError:
        return None, f"{label} not readable at the given path"


def cmd_check(args: list[str]) -> int:
    flags = _parse_flags(args, {"ir": True, "manifest": False, "report": True})
    ir_bytes, ir_error = _read_input(flags["ir"], "IR")
    manifest_bytes, manifest_error = _read_input(flags.get("manifest"), "manifest")
    report = run_checks(ir_bytes, ir_error, manifest_bytes, manifest_error)
    report_path = Path(flags["report"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(canonical_dumps(report), encoding="utf-8")
    sys.stdout.write(
        f"ir-gate: {report['verdict']} "
        f"({report['violations_total']} violation(s) across {len(CHECK_ORDER)} checks)\n"
    )
    return 0 if report["verdict"] == "green" else 2


def cmd_seal(args: list[str]) -> int:
    flags = _parse_flags(args, {"ir": True, "out": True})
    try:
        ir = json.loads(Path(flags["ir"]).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise Usage("cannot read IR to seal")
    if not isinstance(ir, dict):
        raise Usage("IR to seal is not a JSON object")
    ir["irDigest"] = canonical_ir_digest(ir)
    Path(flags["out"]).write_text(canonical_dumps(ir), encoding="utf-8")
    sys.stdout.write(f"sealed: {ir['irDigest']}\n")
    return 0


# --------------------------------------------------------------- selftest --


def cmd_selftest(args: list[str]) -> int:
    if args:
        raise Usage("selftest takes no arguments")
    import tempfile

    fixtures = Path(__file__).resolve().parent / "fixtures"
    if not fixtures.is_dir():
        raise Usage("fixtures directory missing")
    problems: list[str] = []
    cases = sorted(p for p in fixtures.iterdir() if p.is_dir())
    if not cases:
        problems.append("no fixture cases found")
    for case in cases:
        spec = json.loads((case / "case.json").read_text(encoding="utf-8"))
        golden = (case / "expected-report.json").read_bytes()
        runs = []
        with tempfile.TemporaryDirectory() as tmp:
            for attempt in (1, 2):
                report_path = Path(tmp) / f"report-{attempt}.json"
                argv = ["--ir", str(case / "ir.json")]
                if (case / "manifest.json").is_file():
                    argv += ["--manifest", str(case / "manifest.json")]
                argv += ["--report", str(report_path)]
                code = cmd_check(argv)
                runs.append((code, report_path.read_bytes()))
        if runs[0] != runs[1]:
            problems.append(f"{case.name}: nondeterministic across the double run")
        code, report_bytes = runs[0]
        if code != spec["expected_exit"]:
            problems.append(f"{case.name}: exit {code} != {spec['expected_exit']}")
        if report_bytes != golden:
            problems.append(f"{case.name}: report diverges from the committed golden")
        expected_red = spec.get("expected_red_checks")
        if expected_red is not None:
            report = json.loads(report_bytes)
            red = [c["id"] for c in report["checks"] if c["outcome"] == "fail"]
            if red != expected_red:
                problems.append(f"{case.name}: red checks {red} != expected {expected_red}")
    # usage probes: argv misuse exits 3 and writes nothing
    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp) / "never.json"
        for argv in (
            ["check", "--bogus", "x", "--report", str(probe)],
            ["check", "--ir", str(fixtures / "green" / "ir.json")],
            ["nonsense"],
        ):
            if main(argv) != 3:
                problems.append(f"usage probe {argv[:2]}: did not exit 3")
        if probe.exists():
            problems.append("usage probe wrote a report on usage error")
    for problem in problems:
        sys.stderr.write(f"ir-gate-checker selftest: {problem}\n")
    sys.stdout.write(
        f"selftest: {len(cases)} case(s), "
        f"{'fail' if problems else 'pass'} ({len(problems)} problem(s))\n"
    )
    return 2 if problems else 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if not args:
            raise Usage("subcommand required: check | seal | selftest")
        cmd, rest = args[0], args[1:]
        if cmd == "check":
            return cmd_check(rest)
        if cmd == "seal":
            return cmd_seal(rest)
        if cmd == "selftest":
            return cmd_selftest(rest)
        raise Usage(f"unknown subcommand '{cmd}'")
    except Usage as exc:
        sys.stderr.write(f"ir-gate-checker: error: {exc}\n")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
