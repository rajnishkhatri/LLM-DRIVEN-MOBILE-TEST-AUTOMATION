"""gate-wrap CLI: run a gate tool, translate its exit code per the active
InvocationDescriptor row, emit the mapped decision output, exit per the map.

Harness particulars live only in descriptor data (spec S2). The wrapper's own
usage/internal failures exit 1 (plan F1); mapped exits come from the row.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _usage(message: str) -> int:
    sys.stderr.write(f"gate-wrap: error: {message}\n")
    return 1


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--" in args:
        split = args.index("--")
        head, tool_argv = args[:split], args[split + 1 :]
    else:
        head, tool_argv = args, []

    descriptors_path: str | None = None
    harness: str | None = None
    i = 0
    while i < len(head):
        if head[i] == "--descriptors" and i + 1 < len(head):
            descriptors_path = head[i + 1]
            i += 2
        elif head[i] == "--harness" and i + 1 < len(head):
            harness = head[i + 1]
            i += 2
        else:
            return _usage(f"unrecognized argument '{head[i]}'")

    if not descriptors_path or not harness:
        return _usage("--descriptors and --harness are required")
    if not tool_argv:
        return _usage("no gate tool given after '--'")

    path = Path(descriptors_path)
    if not path.is_file():
        return _usage("descriptor file not found")
    try:
        descriptors = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError):
        return _usage("descriptor file is not valid JSON")

    row = next(
        (
            r
            for r in descriptors.get("rows", [])
            if isinstance(r, dict) and r.get("harness") == harness
        ),
        None,
    )
    if row is None:
        return _usage(f"no descriptor row for harness '{harness}'")

    try:
        proc = subprocess.run(tool_argv, capture_output=True)
    except (OSError, ValueError):
        return _usage("gate tool could not be executed")

    entry = next(
        (
            m
            for m in row.get("exit_code_map", [])
            if isinstance(m, dict) and m.get("tool_exit") == proc.returncode
        ),
        None,
    )
    if entry is None:
        return _usage(f"exit-code map has no row for tool exit {proc.returncode}")

    sys.stdout.write(str(entry["decision_output"]) + "\n")
    return int(entry["wrapper_exit"])


if __name__ == "__main__":
    raise SystemExit(main())
