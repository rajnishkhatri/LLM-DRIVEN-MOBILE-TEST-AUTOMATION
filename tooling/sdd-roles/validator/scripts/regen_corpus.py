#!/usr/bin/env python3
"""regen_corpus.py — the F4 restamp + C2 regeneration engine (dev tooling).

Never on the acceptance path. Rewrites the committed corpus mechanically:

  restamp   flip kernel/VERSION + every schema const/$id + every corpus
            artifact's schema_version string OLD -> NEW, then re-synchronize
            every digest relation that was VALID before the restamp (ledger
            chains, artifact refs, genesis pins, handoff digests, tree
            digests). Relations that were deliberately broken (the invalid
            families' defects) keep their broken values — the restamp
            preserves the validity relation, it never repairs a fixture.
            Applies the C2 cold-start restructure (reports + input_tree_digest
            recorded at the gate_run entry) when the marker is absent.
  goldens   regenerate the orchestrator golden runs by executing gate-runner
            against the stub scenarios under the pinned clock (WP4 hook).

Hard rule (asserted): this script never writes an expect.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]  # tooling/sdd-roles/
KERNEL = REPO / "kernel"
CORPUS = KERNEL / "corpus"

# OLD is always the committed kernel/VERSION; NEW comes from restamp --to
# (defaulting to OLD, which makes a bare restamp a pure idempotence pass).
OLD = (KERNEL / "VERSION").read_text(encoding="utf-8").strip()
NEW = OLD

WRITTEN: list[Path] = []


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write(path: Path, data: bytes) -> None:
    assert path.name != "expect.json", f"regen must never write {path}"
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)
        WRITTEN.append(path)


def tree_digest(pairs: list[dict]) -> str:
    blob = b"".join(
        p["path"].encode() + b"\x00" + p["sha256"].encode() + b"\n"
        for p in sorted(pairs, key=lambda a: a["path"])
    )
    return sha(blob)


def compact(entry: dict) -> bytes:
    return json.dumps(entry, separators=(",", ":"), ensure_ascii=True).encode()


# ---------------------------------------------------------------- restamp --


def restamp_version_strings() -> None:
    write(KERNEL / "VERSION", f"{NEW}\n".encode())
    for path in sorted((KERNEL / "schemas").glob("*.json")):
        write(path, path.read_text(encoding="utf-8").replace(OLD, NEW).encode())
    for path in sorted(KERNEL.rglob("*")):
        if path.suffix not in (".json", ".ndjson") or not path.is_file():
            continue
        if path.name == "expect.json" or (KERNEL / "schemas") in path.parents:
            continue
        text = path.read_text(encoding="utf-8")
        for pat in (f'"schema_version": "{OLD}"', f'"schema_version":"{OLD}"'):
            text = text.replace(pat, pat.replace(OLD, NEW))
        write(path, text.encode())


def snapshot_validity() -> dict:
    """Record, BEFORE any byte changes, which digest relations hold."""
    state: dict = {
        "refs": {}, "chains": {}, "genesis": {}, "trees": {}, "handoff": {}, "writes": {},
    }
    canon_cfg = sha((CORPUS / "valid/KernelConfig/kernel-config.json").read_bytes())
    canon_reg = sha((CORPUS / "valid/RoleRegistry/role-registry.json").read_bytes())
    for path in sorted(KERNEL.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix == ".json" and path.name not in ("expect.json", "invocation.json", "case.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except ValueError:
                continue
            if not isinstance(data, dict):
                continue
            for ptr, ref in iter_refs(data):
                target = path.parent / ref.get("path", "")
                ok = target.is_file() and sha(target.read_bytes()) == ref.get("sha256")
                state["refs"][f"{path}::{ptr}"] = ok
        elif path.suffix == ".ndjson":
            lines = [l for l in path.read_bytes().split(b"\n") if l.strip()]
            entries = [json.loads(l) for l in lines]
            for i, e in enumerate(entries):
                key = f"{path}::L{i}"
                if i > 0:
                    state["chains"][key] = e.get("prev_entry_digest") == sha(lines[i - 1])
                if e.get("seq") == 0:
                    state["genesis"][key] = {
                        "cfg_ok": e.get("kernel_config_digest") == canon_cfg,
                        "reg_ok": e.get("role_registry_digest") == canon_reg,
                    }
                arts = e.get("artifacts")
                if arts is not None:
                    state["trees"][key] = e.get("tree_digest") == tree_digest(arts)
                    ref_ok = {}
                    for a in arts:
                        target = path.parent / a["path"]
                        ref_ok[a["path"]] = (
                            target.is_file() and sha(target.read_bytes()) == a["sha256"]
                        )
                    state["refs"][key] = ref_ok
                    art_map = {a["path"]: a["sha256"] for a in arts}
                    w_ok = {}
                    for w in e.get("writes") or []:
                        if isinstance(w, dict) and w.get("path") in art_map:
                            w_ok[w["path"]] = w.get("sha256_after") == art_map[w["path"]]
                    state["writes"][key] = w_ok
                hd = e.get("handoff_contract_digest")
                if hd:
                    target = path.parent / "handoff.json"
                    state["handoff"][key] = target.is_file() and sha(target.read_bytes()) == hd
    return state


def iter_refs(data: dict):
    atype = data.get("artifact_type")
    if atype == "handoff_contract":
        for i, ev in enumerate(data.get("completion_evidence") or []):
            if isinstance(ev, dict) and "path" in ev:
                yield f"/completion_evidence/{i}", ev
        for i, go in enumerate(data.get("gate_outcomes") or []):
            if isinstance(go, dict) and isinstance(go.get("report_ref"), dict):
                yield f"/gate_outcomes/{i}/report_ref", go["report_ref"]
        if isinstance(data.get("debug_report_ref"), dict):
            yield "/debug_report_ref", data["debug_report_ref"]
    elif atype == "gate_outcome" and isinstance(data.get("report_ref"), dict):
        yield "/report_ref", data["report_ref"]


def resync(state: dict) -> None:
    """Re-point every relation that was valid pre-restamp at the new bytes."""
    canon_cfg = sha((CORPUS / "valid/KernelConfig/kernel-config.json").read_bytes())
    canon_reg = sha((CORPUS / "valid/RoleRegistry/role-registry.json").read_bytes())
    # standalone artifacts' refs
    for path in sorted(KERNEL.rglob("*.json")):
        if not path.is_file() or path.name in ("expect.json", "invocation.json", "case.json"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
            data = json.loads(text)
        except ValueError:
            continue
        if not isinstance(data, dict):
            continue
        changed = False
        for ptr, ref in iter_refs(data):
            if state["refs"].get(f"{path}::{ptr}"):
                target = path.parent / ref["path"]
                new = sha(target.read_bytes())
                if ref["sha256"] != new:
                    ref["sha256"] = new
                    changed = True
        if changed:
            write(path, (json.dumps(data, indent=2, ensure_ascii=True) + "\n").encode())
    # ledgers: refs -> trees -> genesis pins -> handoff digests -> chains
    for path in sorted(KERNEL.rglob("*.ndjson")):
        lines = [l for l in path.read_bytes().split(b"\n") if l.strip()]
        entries = [json.loads(l) for l in lines]
        for i, e in enumerate(entries):
            key = f"{path}::L{i}"
            for a in e.get("artifacts") or []:
                if state["refs"].get(key, {}).get(a["path"]):
                    a["sha256"] = sha((path.parent / a["path"]).read_bytes())
            art_map = {a["path"]: a["sha256"] for a in e.get("artifacts") or []}
            for w in e.get("writes") or []:
                if isinstance(w, dict) and state["writes"].get(key, {}).get(w.get("path")):
                    w["sha256_after"] = art_map[w["path"]]
            if e.get("artifacts") is not None and state["trees"].get(key):
                e["tree_digest"] = tree_digest(e["artifacts"])
            if e.get("seq") == 0:
                g = state["genesis"].get(key, {})
                if g.get("cfg_ok"):
                    e["kernel_config_digest"] = canon_cfg
                if g.get("reg_ok"):
                    e["role_registry_digest"] = canon_reg
            if state["handoff"].get(key):
                e["handoff_contract_digest"] = sha((path.parent / "handoff.json").read_bytes())
        out = []
        for i, e in enumerate(entries):
            if i > 0 and state["chains"].get(f"{path}::L{i}"):
                e["prev_entry_digest"] = sha(out[i - 1])
            out.append(compact(e))
        write(path, b"\n".join(out) + b"\n")


def cold_start_c2() -> None:
    """C2 restructure: reports + input_tree_digest recorded at the gate_run
    entry (idempotent: keyed on the input_tree_digest marker)."""
    path = CORPUS / "runs/cold-start/ledger.ndjson"
    entries = [json.loads(l) for l in path.read_bytes().split(b"\n") if l.strip()]
    gate = next(e for e in entries if e.get("event") == "gate_run")
    if "input_tree_digest" in gate:
        return
    handoff = json.loads((CORPUS / "runs/cold-start/handoff.json").read_text())
    input_tree = handoff["gate_outcomes"][0]["input_tree_digest"]
    reports = sorted(
        {go["report_ref"]["path"]: go["report_ref"]["sha256"] for go in handoff["gate_outcomes"]}.items()
    )
    gate["input_tree_digest"] = input_tree
    gate["writes"] = [
        {"path": p, "change": "added", "sha256_before": None, "sha256_after": s}
        for p, s in reports
    ]
    gate["artifacts"] = [{"path": p, "sha256": s} for p, s in reports]
    gate["tree_digest"] = tree_digest(gate["artifacts"])
    final = next(e for e in entries if e.get("event") == "handoff")
    report_paths = {p for p, _ in reports}
    final["writes"] = [w for w in final["writes"] if w["path"] not in report_paths]
    out = []
    for i, e in enumerate(entries):
        if i > 0:
            e["prev_entry_digest"] = sha(out[i - 1])
        out.append(compact(e))
    write(path, b"\n".join(out) + b"\n")


# ---------------------------------------------------------------- goldens --


def regen_goldens(python: str) -> None:
    """Execute every goldens.json recipe with the pinned clock and commit the
    resulting run-dir + workspace-after trees (ADR 0002: the runner writes its
    own conformance fixtures; the selftest holds it to them forever after)."""
    import tempfile

    fixture = CORPUS / "orchestrator"
    recipes = json.loads((fixture / "goldens.json").read_text(encoding="utf-8"))
    clock = recipes["clock"]
    for spec in recipes["sets"]:
        scenario = fixture / "scenarios" / spec["scenario"]
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp) / "workspace"
            rd = Path(tmp) / "run-dir"
            shutil.copytree(scenario / "workspace-template", ws)
            if spec.get("mount"):
                proc = subprocess.run(
                    [
                        python, "-m", "sdd_roles_validator.guard", "mount",
                        "--descriptors", str(fixture / "descriptors-stub.json"),
                        "--harness", spec["mount"],
                        "--registry", str(scenario / "role-registry.json"),
                        "--out", str(ws),
                    ],
                    capture_output=True, text=True,
                )
                if proc.returncode != 0:
                    sys.stderr.write(proc.stderr)
                    raise SystemExit(f"golden {spec['golden']}: mount exit {proc.returncode}")
            for run in spec["runs"]:
                argv = [
                    python, "-m", "sdd_roles_validator.runner", "run",
                    "--kernel", str(KERNEL),
                    "--workspace", str(ws),
                    "--run-dir", str(rd),
                    "--config", str(scenario / "kernel-config.json"),
                    "--registry", str(scenario / "role-registry.json"),
                    "--descriptors", str(fixture / "descriptors-stub.json"),
                    "--harness", run["harness"],
                    "--run-id", run["run_id"],
                    "--clock", clock,
                    "--bind", f"python={python}",
                    "--bind", f"fixture_dir={fixture}",
                ]
                if run.get("parent"):
                    argv += ["--parent", run["parent"]]
                proc = subprocess.run(argv, capture_output=True, text=True)
                if proc.returncode != run.get("expected_exit", 0):
                    sys.stderr.write(proc.stderr)
                    raise SystemExit(f"golden {spec['golden']}/{run['run_id']}: exit {proc.returncode}")
            dest = CORPUS / "runs" / spec["golden"]
            if dest.exists():
                shutil.rmtree(dest)
            if spec.get("resume_set"):
                shutil.copytree(rd, dest / "completed" / "run-dir")
                shutil.copytree(ws, dest / "completed" / "workspace-after")
                # interrupted = genesis-only truncation + the run's own
                # config/registry/mapping copies + a pristine workspace
                int_rd = dest / "interrupted" / "run-dir"
                int_rd.mkdir(parents=True)
                ledger = next(rd.glob("*.ndjson"))
                first_line = ledger.read_bytes().split(b"\n")[0]
                (int_rd / ledger.name).write_bytes(first_line + b"\n")
                for name in ("kernel-config.json", "role-registry.json", "speckit-mapping.json"):
                    if (rd / name).is_file():
                        (int_rd / name).write_bytes((rd / name).read_bytes())
                shutil.copytree(
                    scenario / "workspace-template", dest / "interrupted" / "workspace"
                )
            else:
                shutil.copytree(rd, dest / "run-dir")
                shutil.copytree(ws, dest / "workspace-after")
        print("golden:", spec["golden"])
    print("goldens regenerated")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("restamp")
    r.add_argument("--to", default=None, help="target schema_version (default: current kernel/VERSION)")
    g = sub.add_parser("goldens")
    g.add_argument("--python", default=sys.executable)
    args = parser.parse_args()
    if args.cmd == "restamp":
        if args.to:
            global NEW
            NEW = args.to
        state = snapshot_validity()
        restamp_version_strings()
        cold_start_c2()
        resync(state)
        print(f"restamped: {len(WRITTEN)} files written")
    else:
        regen_goldens(args.python)
    assert not any(p.name == "expect.json" for p in WRITTEN)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
