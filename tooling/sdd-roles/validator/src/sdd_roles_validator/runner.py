"""gate-runner — the between-run gate orchestrator (build item 2).

The deterministic gate-runner principal: drives headless one-shot role
invocations from InvocationDescriptor data, runs the role's gates between
invocations, branches on exit codes only, and is the stage ledger's sole
writer. Harness particulars arrive exclusively as data (descriptor rows,
role invocation values, gate bindings); machine values arrive only via
--bind pairs, so committed fixtures stay byte-portable.

Run-directory shape: append-only. Each stage writes its own handoff file
(handoff-<seq>-<stage>.json) and per-attempt reports (reports/<gate>-a<n>);
nothing is overwritten, so every ledger artifact snapshot stays resolvable
(CHK-REFS) and cross-stage decisions stay comparable (CHK-DECISIONS item-2).
The run carries its own kernel-config.json + role-registry.json copies so
genesis pins resolve against run-local bytes forever (S8 self-containment).

Exit taxonomy (plan F1): 0 = run complete, all gates green, final validation
green; 1 = usage/internal error, nothing written; 2 = run failed (gate red at
the rework bound, validation red at the bound, resume refusal). An honestly-
failed run's ledger still validates green — failure lives in outcomes, never
in ledger integrity.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

from .ledger_model import (
    artifacts_map,
    sha256_hex,
    tree_digest_of_map,
)

_TOKEN = re.compile(r"\{([a-z0-9_]+)\}")  # digits: canon binds like {crap4java}

SCAN_EXCLUDE_DIRS = {".git"}  # plus the run dir and ledger dir (F2, fixed)


class Usage(Exception):
    pass


class RunFailed(Exception):
    pass


def _fail(msg: str) -> int:
    sys.stderr.write(f"gate-runner: error: {msg}\n")
    return 1


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Usage(f"cannot read {path.name}: {type(exc).__name__}")


def _canonical_artifact(data: dict) -> bytes:
    return (json.dumps(data, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode()


def _load_ledger(path: Path) -> list[tuple[bytes, dict]]:
    out = []
    for raw in path.read_bytes().split(b"\n"):
        if raw.strip():
            out.append((raw, json.loads(raw)))
    return out


def _edges_of(entries: list[tuple[bytes, dict]]):
    for _raw, e in entries:
        rw = e.get("rework")
        if isinstance(rw, dict):
            yield f"{rw.get('target_role')}::{rw.get('from_stage')}", rw


class Clock:
    def __init__(self, spec: str):
        if spec == "wall":
            self.fixed = None
        elif spec.startswith("fixed:") and spec[len("fixed:") :]:
            self.fixed = spec[len("fixed:") :]
        else:
            raise Usage("malformed --clock (expected wall or fixed:<iso8601>)")

    def now(self) -> str:
        if self.fixed is not None:
            return self.fixed
        return _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z")


class Runner:
    def __init__(self, args):
        self.kernel = Path(args.kernel).resolve()
        self.workspace = Path(args.workspace).resolve()
        self.run_dir = Path(args.run_dir).resolve()
        self.clock = Clock(args.clock)
        self.binds: dict[str, str] = {}
        for pair in args.bind or []:
            if "=" not in pair:
                raise Usage(f"malformed --bind '{pair}' (expected key=value)")
            k, v = pair.split("=", 1)
            self.binds[k] = v
        if not self.kernel.is_dir():
            raise Usage("kernel directory not found")
        if not self.workspace.is_dir():
            raise Usage("workspace directory not found")
        self.config_path = Path(args.config).resolve()
        self.registry_path = Path(args.registry).resolve()
        self.config = self._load_schema_valid(self.config_path, "kernel_config")
        self.registry = self._load_schema_valid(self.registry_path, "role_registry")
        descriptors = self._load_schema_valid(
            Path(args.descriptors).resolve(), "invocation_descriptor_set"
        )
        self.harness = args.harness
        self.row = next(
            (r for r in descriptors.get("rows", []) if r.get("harness") == self.harness),
            None,
        )
        if self.row is None:
            raise Usage(f"no descriptor row for harness '{self.harness}'")
        self.roles = {r["id"]: r for r in self.registry.get("roles", [])}
        arm_id = self.config.get("arm")
        arm = next((a for a in self.registry.get("arms", []) if a.get("id") == arm_id), None)
        if arm is None:
            raise Usage(f"arm '{arm_id}' not found in the role registry")
        self.sequence = list(arm.get("roles", []))
        self.gate_rows = {g["id"]: g for g in self.config.get("gates") or []}
        self.thresholds = {t["name"]: t["value"] for t in self.config.get("thresholds", [])}
        for role_id in self.sequence:
            role = self.roles.get(role_id)
            if role is None:
                raise Usage(f"arm role '{role_id}' not in the registry")
            if not role.get("invocation"):
                raise Usage(f"role '{role_id}' carries no invocation values")
            for gate_id in role.get("gates", []):
                row = self.gate_rows.get(gate_id)
                if row is None:
                    raise Usage(f"gate '{gate_id}' has no KernelConfig gates[] row")
                if row.get("threshold") not in self.thresholds:
                    raise Usage(f"gate '{gate_id}' names no declared threshold")
                if row.get("tool") not in (self.config.get("gate_tool_allowlist") or []):
                    raise Usage(f"gate '{gate_id}' tool not in the gate_tool_allowlist")
        self.max_rounds = int((self.config.get("rework") or {}).get("max", 0)) or 1
        self.ledger_dirs = [
            Path(p) for p in (self.config.get("protected") or {}).get("ledger_dir", [])
        ]
        self.mappings = self._load_mappings()
        # mutable run state
        self.run_id: str = ""
        self.ledger_path: Path | None = None
        self.lines: list[bytes] = []
        self.tracked: dict[str, str] = {}
        self.edge_counts: dict[str, int] = {}

    # -- inputs ------------------------------------------------------------

    def _load_schema_valid(self, path: Path, atype: str) -> dict:
        if not path.is_file():
            raise Usage(f"{atype} file not found: {path.name}")
        data = _read_json(path)
        import jsonschema

        from .loader import SCHEMA_FILES

        schema = _read_json(self.kernel / "schemas" / SCHEMA_FILES[atype])
        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError:
            raise Usage(f"{atype} does not validate against its schema")
        return data

    def _load_mappings(self) -> dict[str, str]:
        """The SpecKitMapping instance travels next to the config file."""
        rows: dict[str, str] = {}
        candidate = self.config_path.parent / "speckit-mapping.json"
        if candidate.is_file():
            for m in (_read_json(candidate)).get("mappings", []):
                if isinstance(m, dict) and m.get("artifact_type"):
                    rows[m["artifact_type"]] = str(m.get("target_path", ""))
        return rows

    # -- ledger ------------------------------------------------------------

    def _schema_version(self) -> str:
        return (self.kernel / "VERSION").read_text(encoding="utf-8").strip()

    def _append(self, entry: dict) -> None:
        line = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
        self.lines.append(line)
        assert self.ledger_path is not None
        with self.ledger_path.open("ab") as fh:
            fh.write(line + b"\n")

    def _entry(self, role: str, event: str, **kw) -> dict:
        entry = {
            "schema_version": self._schema_version(),
            "artifact_type": "stage_ledger_entry",
            "run_id": self.run_id,
            "seq": len(self.lines),
            "prev_entry_digest": sha256_hex(self.lines[-1]) if self.lines else None,
            "stage": kw.get("stage", role),
            "role": role,
            "event": event,
            "gates": kw.get("gates", []),
            "writes": kw.get("writes", []),
            "tree_digest": tree_digest_of_map(self.tracked),
            "artifacts": [
                {"path": p, "sha256": h} for p, h in sorted(self.tracked.items())
            ],
            "harness": kw["harness"],
            "writer": self.config["gate_runner"],
            "ts": self.clock.now(),
        }
        if "input_tree" in kw:
            entry["input_tree_digest"] = kw["input_tree"]
        if "rework" in kw:
            entry["rework"] = kw["rework"]
        if "handoff_digest" in kw:
            entry["handoff_contract_digest"] = kw["handoff_digest"]
        return entry

    def _harness_obj(self, role_id: str, attempt: int) -> dict:
        role = self.roles[role_id]
        definition = json.dumps(
            {
                "command_template": self.row.get("command_template"),
                "invocation": role.get("invocation"),
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode()
        return {
            "name": self.harness,
            "resume_handle": f"{role_id}-a{attempt}",
            "agent_definition_digest": sha256_hex(definition),
        }

    # -- workspace ---------------------------------------------------------

    def _scan(self) -> dict[str, str]:
        out: dict[str, str] = {}
        excluded = [self.run_dir] + [
            (self.workspace / d).resolve() for d in self.ledger_dirs
        ]
        for path in sorted(self.workspace.rglob("*")):
            if not path.is_file():
                continue
            if any(part in SCAN_EXCLUDE_DIRS for part in path.parts):
                continue
            resolved = path.resolve()
            if any(resolved == ex or ex in resolved.parents for ex in excluded):
                continue
            out[path.relative_to(self.workspace).as_posix()] = sha256_hex(path.read_bytes())
        return out

    @staticmethod
    def _diff(before: dict[str, str], after: dict[str, str]) -> list[dict]:
        writes: list[dict] = []
        for path in sorted(set(before) | set(after)):
            b, a = before.get(path), after.get(path)
            if b == a:
                continue
            change = "added" if b is None else ("deleted" if a is None else "modified")
            writes.append(
                {"path": path, "change": change, "sha256_before": b, "sha256_after": a}
            )
        return writes

    # -- invocation --------------------------------------------------------

    def _fill(self, template_argv: list[str], extra: dict[str, str]) -> list[str]:
        fill = dict(self.binds)
        fill.update(extra)

        def sub(match: re.Match) -> str:
            key = match.group(1)
            if key not in fill:
                raise Usage(f"unresolved template placeholder '{{{key}}}'")
            return str(fill[key])

        return [_TOKEN.sub(sub, token) for token in template_argv]

    def _invoke_role(self, role_id: str, attempt: int) -> int:
        role = self.roles[role_id]
        # {next_role}: the arm successor; the final stage points back to the
        # arm's entry stage (the orchestrator-corpus handoff convention)
        idx = self.sequence.index(role_id) if role_id in self.sequence else -1
        if 0 <= idx < len(self.sequence) - 1:
            next_role = self.sequence[idx + 1]
        else:
            next_role = self.sequence[0] if self.sequence else ""
        extra = {
            "workspace": str(self.workspace),
            "run_dir": str(self.run_dir),
            "stage": role_id,
            "role": role_id,
            "attempt": str(attempt),
            "next_role": next_role,
        }
        extra.update({k: str(v) for k, v in (role.get("invocation") or {}).items()})
        argv = self._fill(shlex.split(self.row["command_template"]), extra)
        proc = subprocess.run(argv, cwd=str(self.workspace), capture_output=True)
        return proc.returncode

    def _run_gate(self, role_id: str, gate_id: str, attempt: int, input_tree: str) -> dict:
        row = self.gate_rows[gate_id]
        # seq-keyed report names are unique across attempts, stage revisits,
        # and parent/child runs sharing one run directory (append-only shape)
        report_rel = f"reports/{self.run_id}-{gate_id}-s{len(self.lines):03d}.json"
        report_path = self.run_dir / report_rel
        extra = {
            "workspace": str(self.workspace),
            "run_dir": str(self.run_dir),
            "gate": gate_id,
            "role": role_id,
            "attempt": str(attempt),
            "report": str(report_path),
        }
        argv = self._fill(list(row["argv"]), extra)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(argv, cwd=str(self.workspace), capture_output=True)
        if not report_path.is_file():
            raise RunFailed(f"gate '{gate_id}' wrote no report at {report_rel}")
        report_bytes = report_path.read_bytes()
        try:
            tool_version = str(json.loads(report_bytes).get("tool_version", ""))
        except ValueError:
            tool_version = ""
        if not tool_version:
            raise RunFailed(f"gate '{gate_id}' report names no tool_version")
        return {
            "gate_id": gate_id,
            "tool": row["tool"],
            "tool_version": tool_version,
            "exit_code": proc.returncode,
            "input_tree_digest": input_tree,
            "attempt_number": attempt,
            "report_ref": {"path": report_rel, "sha256": sha256_hex(report_bytes)},
            "threshold": {
                "name": row["threshold"],
                "value": self.thresholds[row["threshold"]],
            },
        }

    # -- run ---------------------------------------------------------------

    def genesis(self, run_id: str, parent_run_id: str | None) -> None:
        self.run_id = run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path = self.run_dir / f"{run_id}.ndjson"
        if self.ledger_path.exists():
            raise Usage(f"ledger {self.ledger_path.name} already exists (resume instead)")
        cfg_dest = self.run_dir / "kernel-config.json"
        reg_dest = self.run_dir / "role-registry.json"
        if not cfg_dest.exists():
            cfg_dest.write_bytes(self.config_path.read_bytes())
        if not reg_dest.exists():
            reg_dest.write_bytes(self.registry_path.read_bytes())
        # the SpecKitMapping travels with the run too (S8 self-containment:
        # resume re-reads everything from the run dir + workspace alone)
        mapping_src = self.config_path.parent / "speckit-mapping.json"
        mapping_dest = self.run_dir / "speckit-mapping.json"
        if mapping_src.is_file() and not mapping_dest.exists():
            mapping_dest.write_bytes(mapping_src.read_bytes())
        parent = None
        if parent_run_id is not None:
            parent_ledger = self.run_dir / f"{parent_run_id}.ndjson"
            if not parent_ledger.is_file():
                raise Usage(f"parent ledger {parent_ledger.name} not found in the run dir")
            p_entries = _load_ledger(parent_ledger)
            parent = {
                "run_id": parent_run_id,
                "final_entry_digest": sha256_hex(p_entries[-1][0]),
            }
            for key, rw in _edges_of(p_entries):
                if isinstance(rw.get("count"), int):
                    self.edge_counts[key] = rw["count"]
            self.tracked = artifacts_map(p_entries[-1][1])
        entry = {
            "schema_version": self._schema_version(),
            "artifact_type": "stage_ledger_entry",
            "run_id": run_id,
            "seq": 0,
            "prev_entry_digest": None,
            "kernel_config_digest": sha256_hex(cfg_dest.read_bytes()),
            "role_registry_digest": sha256_hex(reg_dest.read_bytes()),
            "tree_digest": tree_digest_of_map(self.tracked),
            "parent_run": parent,
            "writer": self.config["gate_runner"],
            "ts": self.clock.now(),
        }
        self._append(entry)

    def _serialize(self, handoff_name: str) -> None:
        """C4: serialize required_mappings artifacts through the mapping rows
        into the workspace's declared roots (runner output, not in writes[])."""
        for atype in self.config.get("required_mappings", []):
            target = self.mappings.get(atype)
            if not target:
                raise RunFailed(f"required mapping '{atype}' has no SpecKitMapping row")
            dest_dir = self.workspace / target
            dest_dir.mkdir(parents=True, exist_ok=True)
            if atype == "handoff_contract":
                src = self.run_dir / handoff_name
                (dest_dir / handoff_name).write_bytes(src.read_bytes())
            elif atype == "stage_ledger_entry":
                assert self.ledger_path is not None
                (dest_dir / f"{self.run_id}.ndjson").write_bytes(
                    self.ledger_path.read_bytes()
                )

    def _validate_run(self) -> tuple[int, dict]:
        from .registry import run_validate

        report = run_validate(self.run_dir, self.kernel)
        return int(report["exit_code"]), report

    def _track_handoff_refs(self, handoff: dict) -> None:
        refs = []
        refs.extend(handoff.get("completion_evidence") or [])
        if isinstance(handoff.get("debug_report_ref"), dict):
            refs.append(handoff["debug_report_ref"])
        for ref in refs:
            if isinstance(ref, dict) and isinstance(ref.get("path"), str):
                target = self.run_dir / ref["path"]
                if target.is_file():
                    self.tracked[ref["path"]] = sha256_hex(target.read_bytes())

    def _stage(self, role_id: str, attempt: int) -> str:
        """One attempt of one stage. Returns 'passed' | 'retry' | 'rework'."""
        role = self.roles[role_id]
        harness = self._harness_obj(role_id, attempt)
        if attempt == 1:
            self._append(self._entry(role_id, "entered", harness=harness))
        before = self._scan()
        rc = self._invoke_role(role_id, attempt)
        if rc != 0:
            self._append(self._entry(role_id, "failed", harness=harness))
            raise RunFailed(f"role '{role_id}' invocation exited {rc}")
        after = self._scan()
        input_tree = tree_digest_of_map(after)
        workspace_writes = self._diff(before, after)
        gate_ids = list(role.get("gates", []))
        outcomes = []
        tracked_writes: list[dict] = []
        for gate_id in gate_ids:
            outcome = self._run_gate(role_id, gate_id, attempt, input_tree)
            rel = outcome["report_ref"]["path"]
            digest = outcome["report_ref"]["sha256"]
            if rel not in self.tracked:
                tracked_writes.append(
                    {"path": rel, "change": "added", "sha256_before": None, "sha256_after": digest}
                )
                self.tracked[rel] = digest
            outcomes.append(outcome)
        self._append(
            self._entry(
                role_id,
                "gate_run",
                gates=gate_ids,
                writes=workspace_writes + tracked_writes,
                input_tree=input_tree,
                harness=harness,
            )
        )
        red = [o for o in outcomes if o["exit_code"] != 0]
        if red:
            self._append(
                self._entry(
                    role_id,
                    "failed",
                    gates=[o["gate_id"] for o in red],
                    harness=harness,
                )
            )
            return "retry"
        draft_path = self.run_dir / "handoff.draft"
        if not draft_path.is_file():
            raise RunFailed(f"role '{role_id}' wrote no handoff draft")
        try:
            draft = json.loads(draft_path.read_text(encoding="utf-8"))
        except ValueError:
            raise RunFailed("handoff draft is not valid JSON")
        draft["gate_outcomes"] = outcomes
        handoff_bytes = _canonical_artifact(draft)
        handoff_name = f"handoff-{self.run_id}-{len(self.lines):03d}.json"
        (self.run_dir / handoff_name).write_bytes(handoff_bytes)
        draft_path.unlink()
        prior_map = dict(self.tracked)
        self.tracked[handoff_name] = sha256_hex(handoff_bytes)
        self._track_handoff_refs(draft)
        handoff_writes: list[dict] = []
        for path, digest in sorted(self.tracked.items()):
            if path not in prior_map:
                handoff_writes.append(
                    {"path": path, "change": "added", "sha256_before": None, "sha256_after": digest}
                )
            elif prior_map[path] != digest:
                handoff_writes.append(
                    {
                        "path": path,
                        "change": "modified",
                        "sha256_before": prior_map[path],
                        "sha256_after": digest,
                    }
                )
        rework = None
        if draft.get("stage_status") == "rework":
            target_role = (draft.get("rework") or {}).get("target_role")
            key = f"{target_role}::{role_id}"
            count = self.edge_counts.get(key, 0) + 1
            if count > self.max_rounds:
                self._append(self._entry(role_id, "failed", harness=harness))
                raise RunFailed(
                    f"rework edge to '{target_role}' would exceed the bound {self.max_rounds}"
                )
            self.edge_counts[key] = count
            rework = {
                "from_stage": role_id,
                "target_role": target_role,
                "count": count,
                "max": self.max_rounds,
            }
        # the edge is recorded once, on the rework event entry — a duplicate
        # on the handoff entry would (correctly) trip CHK-REWORK monotonicity
        self._append(
            self._entry(
                role_id,
                "handoff",
                writes=handoff_writes,
                harness=harness,
                handoff_digest=sha256_hex(handoff_bytes),
            )
        )
        self._serialize(handoff_name)
        code, report = self._validate_run()
        if code != 0:
            first = next((e for e in report["checks"] if e["outcome"] == "fail"), {})
            self._append(self._entry(role_id, "failed", harness=harness))
            raise RunFailed(
                f"between-run validation red at stage '{role_id}' "
                f"({first.get('check_id')} {first.get('artifact')})"
            )
        if rework is not None:
            self._append(self._entry(role_id, "rework", rework=rework, harness=harness))
            return "rework"
        self._append(self._entry(role_id, "passed", harness=harness))
        return "passed"

    def conveyor(self, start_index: int = 0) -> int:
        i = start_index
        while i < len(self.sequence):
            role_id = self.sequence[i]
            outcome = "retry"
            attempt = 0
            while True:
                attempt += 1
                if attempt > self.max_rounds:
                    raise RunFailed(
                        f"stage '{role_id}' still red after {self.max_rounds} rounds"
                    )
                outcome = self._stage(role_id, attempt)
                if outcome != "retry":
                    break
            if outcome == "rework":
                last = json.loads(self.lines[-1])
                target = (last.get("rework") or {}).get("target_role")
                if target not in self.sequence:
                    raise RunFailed(f"rework target '{target}' not in the active arm")
                i = self.sequence.index(target)
                continue
            i += 1
        code, _report = self._validate_run()
        if code != 0:
            raise RunFailed("final validation red")
        return 0

    # -- resume ------------------------------------------------------------

    def resume(self) -> int:
        ledgers = sorted(self.run_dir.glob("*.ndjson"))
        if not ledgers:
            raise Usage("nothing to resume: no ledger in the run dir")
        code, report = self._validate_run()
        if code != 0:
            first = next((e for e in report["checks"] if e["outcome"] == "fail"), {})
            sys.stderr.write(
                "gate-runner: resume refused: existing run does not validate "
                f"({first.get('check_id')} {first.get('artifact')} "
                f"{first.get('json_pointer')})\n"
            )
            return 2
        ledger_path = ledgers[-1]
        entries = _load_ledger(ledger_path)
        genesis = entries[0][1]
        self.run_id = genesis["run_id"]
        self.ledger_path = self.run_dir / f"{self.run_id}.ndjson"
        if self.ledger_path != ledger_path:
            raise Usage("latest ledger does not match its run_id filename")
        self.lines = [raw for raw, _ in entries]
        last_entry = entries[-1][1]
        if last_entry.get("seq") == 0:
            # genesis-only ledger: seed = empty, or the parent's final map
            parent = last_entry.get("parent_run")
            self.tracked = {}
            if isinstance(parent, dict):
                parent_ledger = self.run_dir / f"{parent.get('run_id')}.ndjson"
                if parent_ledger.is_file():
                    self.tracked = artifacts_map(_load_ledger(parent_ledger)[-1][1])
        else:
            self.tracked = artifacts_map(last_entry)
        for key, rw in _edges_of(entries):
            if isinstance(rw.get("count"), int):
                self.edge_counts[key] = rw["count"]
        last = entries[-1][1]
        role = last.get("role")
        event = last.get("event")
        if last.get("seq") == 0:
            start = 0
        elif event == "passed":
            start = self.sequence.index(role) + 1
        elif event == "rework":
            target = (last.get("rework") or {}).get("target_role")
            if target not in self.sequence:
                raise Usage(f"rework target '{target}' not in the active arm")
            start = self.sequence.index(target)
        elif role in self.sequence:
            start = self.sequence.index(role)  # mid-stage: redo the stage
        else:
            raise Usage(f"cannot reconstruct position: role '{role}' not in the arm")
        return self.conveyor(start)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gate-runner", description=__doc__)
    sub = parser.add_subparsers(dest="cmd")
    for name in ("run", "resume"):
        p = sub.add_parser(name)
        p.add_argument("--kernel", required=True)
        p.add_argument("--workspace", required=True)
        p.add_argument("--run-dir", required=True)
        p.add_argument("--config", required=True)
        p.add_argument("--registry", required=True)
        p.add_argument("--descriptors", required=True)
        p.add_argument("--harness", required=True)
        p.add_argument("--clock", default="wall")
        p.add_argument("--bind", action="append", default=[])
        if name == "run":
            p.add_argument("--run-id", required=True)
            p.add_argument("--parent", help="parent run id to continue (same run dir)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 1 if exc.code else 0
    if args.cmd is None:
        return _fail("a subcommand is required (run | resume)")
    try:
        runner = Runner(args)
        if args.cmd == "resume":
            return runner.resume()
        runner.genesis(args.run_id, args.parent)
        return runner.conveyor()
    except Usage as exc:
        return _fail(str(exc))
    except RunFailed as exc:
        sys.stderr.write(f"gate-runner: run failed: {exc}\n")
        return 2
    except Exception as exc:  # internal error: usage-class, per F1
        sys.stderr.write(f"gate-runner: internal error: {type(exc).__name__}: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
