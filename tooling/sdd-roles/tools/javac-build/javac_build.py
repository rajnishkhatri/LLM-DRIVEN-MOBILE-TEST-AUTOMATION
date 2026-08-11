#!/usr/bin/env python3
"""javac-build — o7's build gate engine (kernel gate id "build").

Deterministic wrapper around `mvn compile` for a Maven Java workspace: the
R-KATA-STUDY equipment seam's build leg. The gate proves exactly one thing —
the module source compiles with zero compiler errors (canon threshold
`build_errors_max: 0`).

Verdict basis: the engine's parsed compiler diagnostics, never raw exit
codes alone. A workspace the engine cannot evaluate (no pom.xml, engine
failure without parseable diagnostics, timeout) FAILS with a `not_evaluable`
reason: fail-closed, never fail-open. The report is written on red too; only
usage/environment errors (exit 3) write nothing.

Exit taxonomy (ir-gate-checker template): 0 = green (report written);
2 = red (report written); 3 = usage or environment error (nothing written).
The report carries tool_version (the gate-runner refuses versionless
outcomes) and echoes the canon threshold.

Determinism: same workspace bytes -> same verdict. The report contains no
clocks, no absolute paths (diagnostics are workspace-relative), and sorted
entries. Engine timings never enter the report.

Environment preconditions (probed, exit 3 when absent — never a fake
report): `mvn` on PATH; a JDK for Maven to run on. First-ever run needs
network for Maven plugin downloads (cached in ~/.m2 afterwards).

Subcommands:
  --workspace <dir> --report <path>   (the KernelConfig row shape; no subcommand)
  selftest                            (fixture corpus x2, byte-stable)
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

TOOL_ID = "javac-build"
TOOL_VERSION = "1.0.0"
CONTRACT = "o7-kata-seam.1"
ENGINE = "mvn compile"
THRESHOLD = {"name": "build_errors_max", "value": 0}
ENGINE_TIMEOUT_S = 900

# Maven compiler diagnostic line, e.g.
#   [ERROR] /abs/path/src/main/java/fx/Broken.java:[5,20] ';' expected
DIAGNOSTIC = re.compile(r"^\[ERROR\] (?P<path>/[^\[\]]+\.java):\[(?P<line>\d+),(?P<col>\d+)\] (?P<message>.*)$")


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


def _run_engine(mvn: str, workspace: Path, goals: list[str]) -> tuple[int | None, str]:
    """Returns (exit code | None on timeout, combined output text)."""
    argv = [mvn, "--batch-mode", "-q", "-Dstyle.color=never", *goals]
    try:
        proc = subprocess.run(argv, cwd=str(workspace), capture_output=True,
                              timeout=ENGINE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None, ""
    text = proc.stdout.decode("utf-8", errors="replace") + proc.stderr.decode("utf-8", errors="replace")
    return proc.returncode, text


def _relativize(path_str: str, workspace: Path) -> str:
    try:
        return str(Path(path_str).resolve().relative_to(workspace.resolve()))
    except ValueError:
        return Path(path_str).name


def parse_diagnostics(text: str, workspace: Path) -> list[dict]:
    seen: set[tuple] = set()
    for line in text.splitlines():
        match = DIAGNOSTIC.match(line.strip())
        if match is None:
            continue
        seen.add((
            _relativize(match.group("path"), workspace),
            int(match.group("line")),
            int(match.group("col")),
            match.group("message").strip(),
        ))
    return [
        {"path": p, "line": l, "col": c, "message": m}
        for p, l, c, m in sorted(seen)
    ]


def evaluate(workspace: Path, mvn: str) -> dict:
    not_evaluable: str | None = None
    errors: list[dict] = []
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
        code, text = _run_engine(mvn, workspace, ["compile"])
        if code is None:
            not_evaluable = f"engine timeout after {ENGINE_TIMEOUT_S}s"
        else:
            errors = parse_diagnostics(text, workspace)
            if code != 0 and not errors:
                not_evaluable = f"engine failed without parseable compiler diagnostics (mvn exit {code})"

    total = len(errors)
    red = not_evaluable is not None or total > THRESHOLD["value"]
    return {
        "artifact_type": "build_report",
        "tool": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "contract": CONTRACT,
        "engine": ENGINE,
        "inputs": {"pom_sha256": pom_sha},
        "errors": errors,
        "errors_total": total,
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
    suffix = f"; not evaluable: {report['not_evaluable']}" if report["not_evaluable"] else ""
    sys.stdout.write(f"build: {report['verdict']} ({report['errors_total']} error(s){suffix})\n")
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
