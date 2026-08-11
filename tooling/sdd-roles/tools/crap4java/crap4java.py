#!/usr/bin/env python3
"""crap4java — o7's CRAP gate engine (kernel gate id "crap").

Deterministic per-method CRAP scorer for a Maven Java workspace: the
R-KATA-STUDY equipment seam's complexity-vs-coverage leg. Runs the suite
under the JaCoCo agent (direct plugin goals — the workspace pom needs no
JaCoCo configuration), then computes the classic crap4j composite per
method from the JaCoCo XML report:

    CRAP(m) = comp(m)^2 * (1 - cov(m))^3 + comp(m)

with comp(m) = cyclomatic complexity (JaCoCo COMPLEXITY counter,
missed + covered) and cov(m) = line coverage fraction (JaCoCo LINE
counter). The canon threshold `crap_composite: 6` is the per-method
ceiling: the gate is green iff NO method's (rounded) CRAP exceeds 6 —
the workspace CRAP<=6 clause of the kata seam (C8), deliberately tighter
than the crap4j folklore default of 30.

The report carries {max, mean, over_threshold_count, per_method} under
`crap` — exactly the fields the kata extraction step reads
(kernel/docs/kata-seam.md).

Fail-closed paths (red with a `not_evaluable` reason): missing pom.xml,
engine failure before a JaCoCo XML exists (including failing tests — this
gate measures the coverage of a PASSING suite), unparseable XML, zero
measured methods (vacuous), engine timeout. Exit taxonomy: 0 = green
(report written); 2 = red (report written); 3 = usage or environment error
(nothing written).

Determinism: same workspace bytes -> same verdict. No clocks, no absolute
paths, sorted entries; scores rounded (coverage 4 dp, CRAP 2 dp) before
comparison so the report IS the decision basis.

Environment preconditions (probed, exit 3 when absent): `mvn` on PATH.
First-ever run needs network for the JaCoCo plugin download.

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

TOOL_ID = "crap4java"
TOOL_VERSION = "1.0.0"
CONTRACT = "o7-kata-seam.1"
ENGINE = "mvn test under the JaCoCo agent (jacoco XML)"
THRESHOLD = {"name": "crap_composite", "value": 6}
ENGINE_TIMEOUT_S = 900
JACOCO = "org.jacoco:jacoco-maven-plugin:0.8.12"


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
        f"{JACOCO}:prepare-agent", "test", f"{JACOCO}:report",
    ]
    try:
        proc = subprocess.run(argv, cwd=str(workspace), capture_output=True,
                              timeout=ENGINE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None
    return proc.returncode


def crap_score(complexity: int, coverage: float) -> float:
    return complexity ** 2 * (1.0 - coverage) ** 3 + complexity


def parse_jacoco(xml_path: Path) -> list[dict]:
    """Per-method rows from the JaCoCo XML report, sorted by method id."""
    root = ET.parse(str(xml_path)).getroot()
    rows: list[dict] = []
    for package in root.iter("package"):
        for cls in package.iter("class"):
            cls_name = (cls.get("name") or "?").replace("/", ".")
            for method in cls.findall("method"):
                counters = {c.get("type"): (int(c.get("missed", "0")), int(c.get("covered", "0")))
                            for c in method.findall("counter")}
                if "LINE" not in counters or "COMPLEXITY" not in counters:
                    continue
                missed_l, covered_l = counters["LINE"]
                total_l = missed_l + covered_l
                if total_l == 0:
                    continue
                complexity = sum(counters["COMPLEXITY"])
                coverage = round(covered_l / total_l, 4)
                rows.append({
                    "method": f"{cls_name}#{method.get('name', '?')}{method.get('desc', '')}",
                    "complexity": complexity,
                    "coverage": coverage,
                    "crap": round(crap_score(complexity, coverage), 2),
                })
    rows.sort(key=lambda r: r["method"])
    return rows


def evaluate(workspace: Path, mvn: str) -> dict:
    not_evaluable: str | None = None
    rows: list[dict] = []
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
            xml_path = workspace / "target" / "site" / "jacoco" / "jacoco.xml"
            if not xml_path.is_file():
                not_evaluable = (f"coverage engine produced no jacoco.xml (mvn exit {code}; "
                                 "this gate measures the coverage of a passing suite)")
            else:
                try:
                    rows = parse_jacoco(xml_path)
                except ET.ParseError:
                    rows, not_evaluable = [], "jacoco.xml is unparseable"
                if not_evaluable is None and not rows:
                    not_evaluable = "no methods measured (a vacuous pass is fail-open)"

    ceiling = float(THRESHOLD["value"])
    over = [r for r in rows if r["crap"] > ceiling]
    crap_values = [r["crap"] for r in rows]
    summary = {
        "max": max(crap_values) if crap_values else None,
        "mean": round(sum(crap_values) / len(crap_values), 2) if crap_values else None,
        "over_threshold_count": len(over),
        "per_method": rows,
    }
    red = not_evaluable is not None or len(over) > 0
    return {
        "artifact_type": "crap_report",
        "tool": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "contract": CONTRACT,
        "engine": ENGINE,
        "inputs": {"pom_sha256": pom_sha},
        "methods_total": len(rows),
        "crap": summary,
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
    sys.stdout.write(
        f"crap: {report['verdict']} ({report['methods_total']} method(s), "
        f"{report['crap']['over_threshold_count']} over CRAP<={THRESHOLD['value']}{suffix})\n"
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
