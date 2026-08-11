#!/usr/bin/env python3
"""junit-runner — o7's tests gate engine (kernel gate id "tests").

Deterministic wrapper around `mvn test` for a Maven Java workspace: the
R-KATA-STUDY equipment seam's tests leg. The gate proves exactly one thing —
the committed suite runs with zero failures and zero errors (canon
threshold `tests_failures_max: 0`).

Verdict basis: the surefire XML result files, never the raw engine exit
alone. A suite that discovers ZERO tests is RED ("no tests discovered") —
a vacuous pass is fail-open, and deleting the suite must never turn this
gate green. A workspace the engine cannot evaluate (no pom.xml, no
parseable results, count/parse inconsistency, timeout) FAILS with a
`not_evaluable` reason: fail-closed, never fail-open.

Exit taxonomy (ir-gate-checker template): 0 = green (report written);
2 = red (report written); 3 = usage or environment error (nothing written).
The report carries tool_version and echoes the canon threshold.

Determinism: same workspace bytes -> same verdict. The report contains no
clocks, no absolute paths, no per-test timings, and sorted entries.

Environment preconditions (probed, exit 3 when absent): `mvn` on PATH.
First-ever run needs network for Maven plugin downloads.

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

TOOL_ID = "junit-runner"
TOOL_VERSION = "1.0.0"
CONTRACT = "o7-kata-seam.1"
ENGINE = "mvn test (surefire XML)"
THRESHOLD = {"name": "tests_failures_max", "value": 0}
ENGINE_TIMEOUT_S = 900


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


def _run_engine(mvn: str, workspace: Path, goals: list[str]) -> int | None:
    """Returns the exit code, or None on timeout."""
    argv = [mvn, "--batch-mode", "-q", "-Dstyle.color=never", *goals]
    try:
        proc = subprocess.run(argv, cwd=str(workspace), capture_output=True,
                              timeout=ENGINE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None
    return proc.returncode


def _first_line(text: str | None) -> str:
    if not text:
        return ""
    return text.strip().splitlines()[0].strip() if text.strip() else ""


def parse_surefire(reports_dir: Path) -> tuple[dict, list[dict]] | None:
    """Parses TEST-*.xml files. Returns (counts, failing) or None when no
    result files exist. Raises ValueError on unparseable XML (fail-closed
    upstream)."""
    files = sorted(reports_dir.glob("TEST-*.xml"))
    if not files:
        return None
    counts = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    failing: list[dict] = []
    for path in files:
        root = ET.parse(str(path)).getroot()
        for key in counts:
            counts[key] += int(root.get(key, "0"))
        for case in root.iter("testcase"):
            test_id = f"{case.get('classname', '?')}#{case.get('name', '?')}"
            for kind in ("failure", "error"):
                node = case.find(kind)
                if node is not None:
                    failing.append({
                        "test": test_id,
                        "kind": kind,
                        "message": _first_line(node.get("message") or node.get("type")),
                    })
    failing.sort(key=lambda f: (f["test"], f["kind"], f["message"]))
    return counts, failing


def evaluate(workspace: Path, mvn: str) -> dict:
    not_evaluable: str | None = None
    counts = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    failing: list[dict] = []
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
        code = _run_engine(mvn, workspace, ["test"])
        if code is None:
            not_evaluable = f"engine timeout after {ENGINE_TIMEOUT_S}s"
        else:
            try:
                parsed = parse_surefire(workspace / "target" / "surefire-reports")
            except (ET.ParseError, ValueError):
                parsed, not_evaluable = None, "surefire result files are unparseable"
            if not_evaluable is None:
                if parsed is None:
                    if code != 0:
                        not_evaluable = f"engine failed without parseable test results (mvn exit {code})"
                    else:
                        not_evaluable = "no tests discovered (a vacuous pass is fail-open)"
                else:
                    counts, failing = parsed
                    if counts["tests"] == 0:
                        not_evaluable = "no tests discovered (a vacuous pass is fail-open)"
                    elif len(failing) != counts["failures"] + counts["errors"]:
                        not_evaluable = (f"surefire counts ({counts['failures']}+{counts['errors']}) "
                                         f"disagree with parsed failing cases ({len(failing)})")

    failures_total = counts["failures"] + counts["errors"]
    red = not_evaluable is not None or failures_total > THRESHOLD["value"]
    return {
        "artifact_type": "tests_report",
        "tool": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "contract": CONTRACT,
        "engine": ENGINE,
        "inputs": {"pom_sha256": pom_sha},
        "counts": counts,
        "failing": failing,
        "failures_total": failures_total,
        "not_evaluable": not_evaluable,
        "threshold": dict(THRESHOLD),
        "verdict": "red" if red else "green",
    }


def cmd_check(args: list[str]) -> int:
    flags = _parse_flags(args, {"workspace": True, "report": True})
    mvn = _mvn_path()
    report = evaluate(Path(flags["workspace"]), mvn)
    report_path = Path(flags["report"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(canonical_dumps(report), encoding="utf-8")
    c = report["counts"]
    suffix = f"; not evaluable: {report['not_evaluable']}" if report["not_evaluable"] else ""
    sys.stdout.write(
        f"tests: {report['verdict']} ({c['tests']} test(s), "
        f"{report['failures_total']} failing{suffix})\n"
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
