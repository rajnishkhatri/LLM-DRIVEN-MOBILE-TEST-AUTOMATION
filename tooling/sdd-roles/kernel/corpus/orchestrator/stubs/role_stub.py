#!/usr/bin/env python3
"""Scenario-driven role stub (ADR 0002): a deterministic byte-writer standing
in for a headless harness invocation. Behavior comes entirely from the
scenario table; the k-th invocation of a role executes the role's k-th action.

Invocation counters live at <workspace>/scratch/<role>.count so repair rounds
and stage revisits stay distinguishable while remaining pure workspace data.
"""

import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

_TOKEN = re.compile(r"\{([a-z_]+)\}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--attempt", required=True)
    args = parser.parse_args()

    scenario_path = Path(__file__).resolve().parent.parent / "scenarios" / args.scenario / "scenario.json"
    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    workspace = Path(args.workspace)
    run_dir = Path(args.run_dir)

    counter = workspace / "scratch" / f"{args.role}.count"
    counter.parent.mkdir(parents=True, exist_ok=True)
    k = (int(counter.read_text()) if counter.is_file() else 0) + 1
    counter.write_text(str(k))

    actions = (scenario.get("roles") or {}).get(args.role) or []
    if k > len(actions):
        sys.stderr.write(f"role_stub: no action for invocation {k} of {args.role}\n")
        return 1
    action = actions[k - 1]

    for w in action.get("workspace_writes") or []:
        dest = workspace / w["path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(w["content"], encoding="utf-8")

    # guarded_writes: consult the mounted hook command before writing, the way
    # a hook-bearing harness would (item-3 spec S7/HP4). No mounted config
    # means no guard — the write lands unhooked (the FP11 negative control).
    hooks_cfg = workspace / "harness-settings" / "stub-hooks.json"
    for gw in action.get("guarded_writes") or []:
        allowed = True
        if hooks_cfg.is_file():
            mounted = json.loads(hooks_cfg.read_text(encoding="utf-8"))
            rules = (mounted.get("events") or {}).get("pre_write") or []
            rule = next((r for r in rules if r.get("matcher") == args.role), None)
            if rule is not None:
                fixture_dir = Path(__file__).resolve().parent.parent
                binds = {
                    "python": sys.executable,
                    "descriptors": str(fixture_dir / "descriptors-stub.json"),
                    "kernel": str(fixture_dir.parents[1]),
                    "config": str(run_dir / "kernel-config.json"),
                    "registry": str(run_dir / "role-registry.json"),
                    "workspace": str(workspace),
                    "run_dir": str(run_dir),
                }
                argv = [
                    _TOKEN.sub(lambda m: binds.get(m.group(1), m.group(0)), tok)
                    for tok in shlex.split(rule["command"])
                ]
                payload = json.dumps(
                    {"write": {"mode": gw["mode"], "targets": [{"file": gw["path"]}]}}
                )
                proc = subprocess.run(argv, input=payload.encode(), capture_output=True)
                allowed = proc.returncode == 0
        if allowed:
            dest = workspace / gw["path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(gw["content"], encoding="utf-8")

    draft = json.loads(json.dumps(action["draft"]))  # deep copy
    for directive in action.get("run_dir_files") or []:
        dest = run_dir / directive["path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        content = directive["content"]
        data = (
            (json.dumps(content, sort_keys=True, indent=2, ensure_ascii=True) + "\n")
            if isinstance(content, (dict, list))
            else str(content)
        ).encode()
        dest.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        ref = {"path": directive["path"], "sha256": digest}
        if directive.get("as") == "debug_report_ref":
            draft["debug_report_ref"] = ref
        elif directive.get("as") == "completion_evidence":
            ref["provenance"] = {"source": "role_authored"}
            draft.setdefault("completion_evidence", []).append(ref)

    (run_dir / "handoff.draft").write_text(
        json.dumps(draft, sort_keys=True, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
