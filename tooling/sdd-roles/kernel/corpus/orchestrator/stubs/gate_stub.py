#!/usr/bin/env python3
"""Scenario-driven gate-tool stub (ADR 0002): exits per the scenario's exit
sequence for the gate and writes its own deterministic report to the path the
gate-runner names. The k-th invocation of a gate uses the k-th exit code
(sequence exhausted -> 0). Counters live under <workspace>/scratch/."""

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--gate", required=True)
    parser.add_argument("--attempt", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    scenario = json.loads(Path(args.scenario).read_text(encoding="utf-8"))
    workspace = Path(args.workspace)

    counter = workspace / "scratch" / f"{args.gate}.count"
    counter.parent.mkdir(parents=True, exist_ok=True)
    k = (int(counter.read_text()) if counter.is_file() else 0) + 1
    counter.write_text(str(k))

    gate = (scenario.get("gates") or {}).get(args.gate) or {}
    exits = gate.get("exits") or []
    exit_code = int(exits[k - 1]) if k <= len(exits) else 0

    report = {
        "tool_version": str(gate.get("tool_version", "9.9.1")),
        "gate": args.gate,
        "invocation": k,
        "result": "pass" if exit_code == 0 else "fail",
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, sort_keys=True, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
