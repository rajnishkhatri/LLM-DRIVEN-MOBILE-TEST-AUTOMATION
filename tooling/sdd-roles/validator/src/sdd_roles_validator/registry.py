"""The CHK table as data — the single executable enumeration (spec: no second
list to drift) — plus the validate pipeline that runs it.

Row phases: "v1" (static), "item-2" (run-directory — LIVE since build item 2),
"dual" (v1 half via `fn` + item-2 half via `fn2`). No row is DEFERRED anymore;
CHK-DEFER now enforces the inverse: an implemented check must never report
DEFERRED (the anti-rot rule cuts both ways).
Cluster "self" rows run per-invocation over the produced core report.
"""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import VALIDATOR_VERSION
from .checks import config_registry, provenance, run_directory
from .loader import Context, build_context
from .report import Entry, build_report, canonical_dumps, sort_entries

CheckFn = Callable[[Context], list[tuple[str, str, str]]]


@dataclass(frozen=True)
class Check:
    check_id: str
    phase: str  # v1 | item-2 | dual
    cluster: str  # artifact | ledger | self
    fn: CheckFn | None
    fn2: CheckFn | None = None  # dual rows: the item-2 half


CHECKS: list[Check] = [
    Check("CHK-SCHEMA", "v1", "artifact", provenance.chk_schema),
    Check("CHK-PROV-PRESENT", "v1", "artifact", provenance.chk_prov_present),
    Check("CHK-FENCE", "v1", "artifact", provenance.chk_fence),
    Check("CHK-TAINT", "v1", "artifact", provenance.chk_taint),
    Check("CHK-TOOLBIND", "v1", "artifact", provenance.chk_toolbind),
    Check("CHK-CHAIN", "item-2", "ledger", run_directory.chk_chain),
    Check("CHK-TREE", "item-2", "ledger", run_directory.chk_tree),
    Check("CHK-WRITER", "item-2", "ledger", run_directory.chk_writer),
    Check("CHK-GENESIS", "item-2", "ledger", run_directory.chk_genesis),
    Check("CHK-REFS", "v1", "artifact", config_registry.chk_refs),
    Check("CHK-GATE-BIND", "item-2", "ledger", run_directory.chk_gate_bind),
    Check("CHK-EVIDENCE", "v1", "artifact", config_registry.chk_evidence),
    Check(
        "CHK-DECISIONS", "dual", "artifact",
        config_registry.chk_decisions_v1, run_directory.chk_decisions_item2,
    ),
    Check("CHK-SCOPE", "item-2", "ledger", run_directory.chk_scope),
    Check("CHK-REWORK", "item-2", "ledger", run_directory.chk_rework),
    Check("CHK-ARM", "v1", "artifact", config_registry.chk_arm),
    Check(
        "CHK-THRESH", "dual", "artifact",
        config_registry.chk_thresh_v1, run_directory.chk_thresh_item2,
    ),
    Check("CHK-PROTECT", "v1", "artifact", config_registry.chk_protect),
    Check("CHK-MAP", "v1", "artifact", config_registry.chk_map),
    Check("CHK-NEUTRAL", "v1", "self", None),
    Check("CHK-HARNESS-ROWS", "v1", "artifact", config_registry.chk_harness_rows),
    Check("CHK-DEBUG", "v1", "artifact", config_registry.chk_debug),
    Check("CHK-IRGATE-PIN", "v1", "artifact", config_registry.chk_irgate_pin),
    Check("CHK-DET", "v1", "self", None),
    Check("CHK-NET", "v1", "self", None),
    Check("CHK-SELF", "v1", "self", None),
    Check("CHK-DEFER", "v1", "self", None),
]

CHECK_IDS = [c.check_id for c in CHECKS]
ITEM2_IDS = [c.check_id for c in CHECKS if c.phase == "item-2"]
DUAL_IDS = [c.check_id for c in CHECKS if c.phase == "dual"]
SELF_IDS = [c.check_id for c in CHECKS if c.cluster == "self"]


class NetGuard:
    """Socket-denying guard: any network attempt inside the guarded block
    raises and is recorded (CHK-NET)."""

    def __init__(self) -> None:
        self.attempts: list[str] = []

    def __enter__(self) -> "NetGuard":
        self._socket = socket.socket
        self._create = socket.create_connection

        def _blocked(*_args, **_kwargs):
            self.attempts.append("socket")
            raise OSError("network access disabled: contract-lint is an offline validator")

        socket.socket = _blocked  # type: ignore[misc,assignment]
        socket.create_connection = _blocked  # type: ignore[assignment]
        return self

    def __exit__(self, *exc_info) -> None:
        socket.socket = self._socket  # type: ignore[misc]
        socket.create_connection = self._create


def run_core(ctx: Context) -> list[Entry]:
    """Artifact- and ledger-cluster rows — everything except the self cluster.
    Every row is live; dual rows emit a v1 entry (fn) and an item-2 entry (fn2)."""
    entries: list[Entry] = []
    for check in CHECKS:
        if check.cluster == "self":
            continue
        phase = "item-2" if check.phase == "item-2" else "v1"
        findings = check.fn(ctx) if check.fn else []
        if findings:
            entries.extend(
                Entry(check.check_id, phase, "fail", label, pointer, detail)
                for label, pointer, detail in findings
            )
        else:
            entries.append(Entry(check.check_id, phase, "pass", "", "", ""))
        if check.phase == "dual":
            findings2 = check.fn2(ctx) if check.fn2 else []
            if findings2:
                entries.extend(
                    Entry(check.check_id, "item-2", "fail", label, pointer, detail)
                    for label, pointer, detail in findings2
                )
            else:
                entries.append(Entry(check.check_id, "item-2", "pass", "", "", ""))
    return entries


def core_fragment_bytes(entries: list[Entry]) -> bytes:
    return canonical_dumps([e.as_dict() for e in sort_entries(entries)]).encode("utf-8")


def load_neutral_tokens(kernel_dir: Path) -> list[str]:
    data = json.loads((kernel_dir / "neutral_tokens.json").read_text(encoding="utf-8"))
    return [t.lower() for t in data["tokens"]]


def scan_neutral_text(label: str, text: str, tokens: list[str]) -> list[tuple[str, str, str]]:
    lowered = text.lower()
    return [
        (label, "", f"harness-identifying token '{t}'") for t in tokens if t in lowered
    ]


def scan_neutral(kernel_dir: Path) -> list[tuple[str, str, str]]:
    """Live CHK-NEUTRAL scope: kernel schemas + validator source + check ids.
    Exclusions (by construction of the scope): descriptor instances, corpus."""
    tokens = load_neutral_tokens(kernel_dir)
    findings: list[tuple[str, str, str]] = []
    for path in sorted((kernel_dir / "schemas").glob("*.json")):
        findings.extend(
            scan_neutral_text(f"schemas/{path.name}", path.read_text(encoding="utf-8"), tokens)
        )
    src_dir = Path(__file__).resolve().parent
    for path in sorted(src_dir.rglob("*.py")):
        rel = path.relative_to(src_dir).as_posix()
        findings.extend(
            scan_neutral_text(f"validator-src/{rel}", path.read_text(encoding="utf-8"), tokens)
        )
    for check_id in CHECK_IDS:
        findings.extend(scan_neutral_text(f"check-id/{check_id}", check_id, tokens))
    return findings


def audit_self(entries: list[Entry], root: Path) -> list[tuple[str, str, str]]:
    """CHK-SELF per-invocation audit: no absolute-path leakage into the report
    (path-independence precondition) and every fail entry names a check id and
    carries a json_pointer field. The full temp-copy stability procedure runs
    under `contract-lint selftest`."""
    findings: list[tuple[str, str, str]] = []
    root_str = str(root.resolve())
    for e in entries:
        if e.artifact.startswith("/") or root_str in e.artifact or root_str in e.detail:
            findings.append((e.check_id, "", "report entry leaks an absolute path"))
        if e.outcome == "fail" and (not e.check_id or e.json_pointer is None):
            findings.append((e.check_id, "", "fail entry does not name check id + JSON pointer"))
    return findings


IMPLEMENTED_ITEM2_IDS = sorted(
    c.check_id
    for c in CHECKS
    if (c.phase == "item-2" and c.fn is not None) or (c.phase == "dual" and c.fn2 is not None)
)
UNIMPLEMENTED_ITEM2_IDS = sorted(
    c.check_id
    for c in CHECKS
    if (c.phase == "item-2" and c.fn is None) or (c.phase == "dual" and c.fn2 is None)
)


def audit_defer(entries: list[Entry]) -> list[tuple[str, str, str]]:
    """CHK-DEFER per-invocation audit, both directions of the anti-rot rule:
    an IMPLEMENTED item-2 check must never report DEFERRED (the build-item-2
    inversion), an unimplemented one must never report anything else, and every
    item-2 row must be present."""
    findings: list[tuple[str, str, str]] = []
    for check_id in sorted(set(ITEM2_IDS) | set(DUAL_IDS)):
        rows = [e for e in entries if e.check_id == check_id and e.phase == "item-2"]
        if not rows:
            findings.append((check_id, "", "item-2 row missing from the report"))
        for e in rows:
            if check_id in IMPLEMENTED_ITEM2_IDS and e.outcome == "deferred":
                findings.append(
                    (check_id, "", "implemented item-2 check still reports DEFERRED")
                )
            if check_id in UNIMPLEMENTED_ITEM2_IDS and e.outcome != "deferred":
                findings.append(
                    (check_id, "", "unimplemented item-2 check not reported DEFERRED")
                )
    return findings


def run_validate(target: Path, kernel_dir: Path) -> dict:
    """Full validate pipeline: core rows + the five self-cluster rows."""
    with NetGuard() as guard:
        ctx = build_context(target, kernel_dir)
        core = run_core(ctx)
        ctx2 = build_context(target, kernel_dir)
        rerun = run_core(ctx2)
    entries = list(core)

    det_ok = core_fragment_bytes(core) == core_fragment_bytes(rerun)
    entries.append(
        Entry("CHK-DET", "v1", "pass" if det_ok else "fail", "", "",
              "" if det_ok else "two runs on identical input produced different output")
    )
    entries.append(
        Entry("CHK-NET", "v1", "pass" if not guard.attempts else "fail", "", "",
              "" if not guard.attempts else "network access attempted during validation")
    )
    neutral = scan_neutral(kernel_dir)
    if neutral:
        entries.extend(Entry("CHK-NEUTRAL", "v1", "fail", a, p, d) for a, p, d in neutral)
    else:
        entries.append(Entry("CHK-NEUTRAL", "v1", "pass", "", "", ""))
    self_findings = audit_self(core, ctx.root)
    if self_findings:
        entries.extend(Entry("CHK-SELF", "v1", "fail", a, p, d) for a, p, d in self_findings)
    else:
        entries.append(Entry("CHK-SELF", "v1", "pass", "", "", ""))
    defer_findings = audit_defer(core)
    if defer_findings:
        entries.extend(Entry("CHK-DEFER", "v1", "fail", a, p, d) for a, p, d in defer_findings)
    else:
        entries.append(Entry("CHK-DEFER", "v1", "pass", "", "", ""))

    schema_version = (kernel_dir / "VERSION").read_text(encoding="utf-8").strip()
    return build_report(schema_version, VALIDATOR_VERSION, target.name, entries)
