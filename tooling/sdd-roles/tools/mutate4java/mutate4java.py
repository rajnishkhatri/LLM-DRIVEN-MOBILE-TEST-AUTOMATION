#!/usr/bin/env python3
"""mutate4java — o7's mutation gate engine (kernel gate id "mutation").

Deterministic wrapper around PIT (pitest) mutation testing for a Maven Java
workspace: the R-KATA-STUDY equipment seam's mutation leg. The gate proves
exactly one thing — the suite detects at least the canon fraction of
generated mutants (threshold `mutation_score_min: 0.85`).

Engine: `mvn test-compile <pitest>:mutationCoverage` with the PIT plugin
invoked by full coordinates (the workspace pom needs no PIT configuration
and the plugin version cannot drift per-workspace), XML output, untimestamped
report directory. PIT runs the suite itself; a failing suite aborts the
engine and the gate fails closed.

Verdict basis: the parsed `mutations.xml`, integer arithmetic only —
    mutation_score_scaled = detected * 10000 // total   (floor)
    green  iff  total > 0  and  mutation_score_scaled >= 8500
The scaled integer is the decision value (the kata rig is integer-only —
kernel/docs/kata-seam.md); the float `mutation_score` in the report is
display-rounded from the same division. Surviving and uncovered mutants are
enumerated so a red is actionable.

Fail-closed paths (red with a `not_evaluable` reason): missing pom.xml,
engine failure before a mutations.xml exists (failing tests, PIT abort),
unparseable XML, zero generated mutants (vacuous), engine timeout. Exit
taxonomy: 0 = green (report written); 2 = red (report written); 3 = usage
or environment error (nothing written).

Environment preconditions (probed, exit 3 when absent): `mvn` on PATH.
First-ever run needs network for the PIT plugin download.

Subcommands:
  --workspace <dir> --report <path>   (the KernelConfig row shape; no subcommand)
  selftest                            (fixture corpus x2, byte-stable)
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TOOL_ID = "mutate4java"
TOOL_VERSION = "1.0.0"
CONTRACT = "o7-kata-seam.1"
ENGINE = "mvn test-compile + pitest mutationCoverage (mutations XML)"
THRESHOLD = {"name": "mutation_score_min", "value": 0.85}
THRESHOLD_SCALED = 8500  # 0.85 on the integer [0, 10000] scale — the decision value
ENGINE_TIMEOUT_S = 900
PITEST = "org.pitest:pitest-maven:1.16.1"


class Usage(Exception):
    pass


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_dumps(obj) -> str:
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


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


def _mvn_path() -> str:
    mvn = shutil.which("mvn")
    if mvn is None:
        raise Usage("environment: mvn not found on PATH (the Java toolchain is a "
                    "precondition of this gate — install Maven; a report is never faked)")
    return mvn


def _run_engine(mvn: str, workspace: Path) -> int | None:
    argv = [
        mvn, "--batch-mode", "-q", "-Dstyle.color=never",
        "test-compile", f"{PITEST}:mutationCoverage",
        "-DoutputFormats=XML",
        "-DtimestampedReports=false",
        "-DfailWhenNoMutations=false",
    ]
    try:
        proc = subprocess.run(argv, cwd=str(workspace), capture_output=True,
                              timeout=ENGINE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None
    return proc.returncode


def _short_mutator(mutator: str) -> str:
    return mutator.rsplit(".", 1)[-1]


def parse_mutations(xml_path: Path) -> tuple[int, int, dict, list[dict]]:
    """Returns (total, detected, by_status, survivors) from mutations.xml."""
    root = ET.parse(str(xml_path)).getroot()
    total = 0
    detected = 0
    by_status: dict[str, int] = {}
    survivors: list[dict] = []
    for mutation in root.iter("mutation"):
        total += 1
        status = mutation.get("status", "UNKNOWN")
        by_status[status] = by_status.get(status, 0) + 1
        is_detected = mutation.get("detected") == "true"
        if is_detected:
            detected += 1
        else:
            def text(tag: str) -> str:
                node = mutation.find(tag)
                return (node.text or "") if node is not None else ""
            survivors.append({
                "class": text("mutatedClass"),
                "method": text("mutatedMethod"),
                "line": int(text("lineNumber") or "0"),
                "mutator": _short_mutator(text("mutator")),
                "status": status,
            })
    survivors.sort(key=lambda s: (s["class"], s["method"], s["line"], s["mutator"], s["status"]))
    return total, detected, dict(sorted(by_status.items())), survivors


def evaluate(workspace: Path, mvn: str) -> dict:
    not_evaluable: str | None = None
    total = detected = 0
    by_status: dict[str, int] = {}
    survivors: list[dict] = []
    pom_sha: str | None = None

    if not workspace.is_dir():
        not_evaluable = "workspace directory not readable"
    else:
        pom = workspace / "pom.xml"
        if pom.is_file():
            pom_sha = sha256_hex(pom.read_bytes())
        else:
            not_evaluable = "no pom.xml at the workspace root"

    if not_evaluable is None:
        code = _run_engine(mvn, workspace)
        if code is None:
            not_evaluable = f"engine timeout after {ENGINE_TIMEOUT_S}s"
        else:
            xml_path = workspace / "target" / "pit-reports" / "mutations.xml"
            if not xml_path.is_file():
                not_evaluable = (f"mutation engine produced no mutations.xml (mvn exit {code}; "
                                 "PIT runs the suite itself — a failing suite aborts the engine)")
            else:
                try:
                    total, detected, by_status, survivors = parse_mutations(xml_path)
                except ET.ParseError:
                    not_evaluable = "mutations.xml is unparseable"
                if not_evaluable is None and total == 0:
                    not_evaluable = "no mutants generated (a vacuous pass is fail-open)"

    scaled = detected * 10000 // total if total > 0 else 0
    red = not_evaluable is not None or scaled < THRESHOLD_SCALED
    return {
        "artifact_type": "mutation_report",
        "tool": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "contract": CONTRACT,
        "engine": ENGINE,
        "inputs": {"pom_sha256": pom_sha},
        "mutants": {
            "total": total,
            "detected": detected,
            "by_status": by_status,
        },
        "survivors": survivors,
        "mutation_score": round(scaled / 10000, 4),
        "mutation_score_scaled": scaled,
        "not_evaluable": not_evaluable,
        "threshold": dict(THRESHOLD),
        "threshold_scaled": THRESHOLD_SCALED,
        "verdict": "red" if red else "green",
    }


def cmd_check(args: list[str]) -> int:
    flags = _parse_flags(args, {"workspace": True, "report": True})
    mvn = _mvn_path()
    report = evaluate(Path(flags["workspace"]), mvn)
    report_path = Path(flags["report"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(canonical_dumps(report), encoding="utf-8")
    m = report["mutants"]
    suffix = f"; not evaluable: {report['not_evaluable']}" if report["not_evaluable"] else ""
    sys.stdout.write(
        f"mutation: {report['verdict']} ({m['detected']}/{m['total']} detected, "
        f"scaled {report['mutation_score_scaled']}/{THRESHOLD_SCALED}{suffix})\n"
    )
    return 0 if report["verdict"] == "green" else 2


# --------------------------------------------------------------- selftest --


def cmd_selftest(args: list[str]) -> int:
    if args:
        raise Usage("selftest takes no arguments")
    import tempfile

    _mvn_path()  # environment precondition, probed up front
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
        for attempt in (1, 2):
            with tempfile.TemporaryDirectory() as tmp:
                workspace = Path(tmp) / "workspace"
                shutil.copytree(case / "workspace", workspace)
                report_path = Path(tmp) / "report.json"
                code = cmd_check(["--workspace", str(workspace), "--report", str(report_path)])
                runs.append((code, report_path.read_bytes()))
        if runs[0] != runs[1]:
            problems.append(f"{case.name}: nondeterministic across the double run")
        code, report_bytes = runs[0]
        if code != spec["expected_exit"]:
            problems.append(f"{case.name}: exit {code} != {spec['expected_exit']}")
        if report_bytes != golden:
            problems.append(f"{case.name}: report diverges from the committed golden")
        verdict = json.loads(report_bytes)["verdict"]
        if verdict != spec["expected_verdict"]:
            problems.append(f"{case.name}: verdict {verdict} != {spec['expected_verdict']}")
    # usage probes: argv misuse exits 3 and writes nothing
    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp) / "never.json"
        for argv in (
            ["--bogus", "x", "--report", str(probe)],
            ["--workspace", str(tmp)],
            ["nonsense"],
        ):
            if main(argv) != 3:
                problems.append(f"usage probe {argv[:2]}: did not exit 3")
        if probe.exists():
            problems.append("usage probe wrote a report on usage error")
    for problem in problems:
        sys.stderr.write(f"{TOOL_ID} selftest: {problem}\n")
    sys.stdout.write(
        f"selftest: {len(cases)} case(s), "
        f"{'fail' if problems else 'pass'} ({len(problems)} problem(s))\n"
    )
    return 2 if problems else 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if not args:
            raise Usage("usage: --workspace <dir> --report <path> | selftest")
        if args[0] == "selftest":
            return cmd_selftest(args[1:])
        if args[0].startswith("--"):
            return cmd_check(args)
        raise Usage(f"unknown subcommand '{args[0]}'")
    except Usage as exc:
        sys.stderr.write(f"{TOOL_ID}: error: {exc}\n")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
