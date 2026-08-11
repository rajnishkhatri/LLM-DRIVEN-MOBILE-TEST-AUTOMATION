"""Static config/registry cluster: CHK-REFS, CHK-EVIDENCE, CHK-DECISIONS(v1),
CHK-ARM, CHK-THRESH(v1), CHK-PROTECT, CHK-MAP, CHK-HARNESS-ROWS, CHK-DEBUG,
CHK-IRGATE-PIN."""

from __future__ import annotations

import hashlib
from pathlib import Path

Finding = tuple[str, str, str]

PROTECTED_KEYS = (
    "kernel_config",
    "role_registry",
    "ledger_dir",
    "tests_globs",
    "gate_configs",
    "harness_enablement",
    "speckit_constitution",
)
CONSTITUTION_PATH = ".specify/memory/constitution.md"


def _iter_typed(ctx, atype: str):
    for art in ctx.artifacts:
        if art.atype == atype and not art.parse_error:
            yield art


def _ref_ok(root: Path, path_str: str, sha256: str) -> str | None:
    """Return None if the ref resolves, else a short deterministic reason."""
    if not path_str or path_str.startswith("/") or path_str.startswith("\\"):
        return "ref path must be target-relative"
    candidate = (root / path_str).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return "ref path escapes the target root"
    if not candidate.is_file():
        return "referenced file missing"
    actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if actual != sha256:
        return "sha256 mismatch against recorded digest"
    return None


def _collect_refs(art) -> list[tuple[str, dict]]:
    refs: list[tuple[str, dict]] = []
    data = art.data
    if art.atype == "handoff_contract":
        for i, ev in enumerate(data.get("completion_evidence") or []):
            refs.append((f"/completion_evidence/{i}", ev))
        for i, go in enumerate(data.get("gate_outcomes") or []):
            if isinstance(go, dict) and isinstance(go.get("report_ref"), dict):
                refs.append((f"/gate_outcomes/{i}/report_ref", go["report_ref"]))
        if isinstance(data.get("debug_report_ref"), dict):
            refs.append(("/debug_report_ref", data["debug_report_ref"]))
    elif art.atype == "gate_outcome":
        if isinstance(data.get("report_ref"), dict):
            refs.append(("/report_ref", data["report_ref"]))
    elif art.atype == "stage_ledger_entry":
        for i, ar in enumerate(data.get("artifacts") or []):
            if isinstance(ar, dict):
                refs.append((f"/artifacts/{i}", ar))
    return refs


def chk_refs(ctx) -> list[Finding]:
    findings: list[Finding] = []
    for art in ctx.artifacts:
        if art.parse_error or art.atype is None:
            continue
        for ptr, ref in _collect_refs(art):
            if not isinstance(ref, dict):
                continue
            reason = _ref_ok(ctx.root, str(ref.get("path", "")), str(ref.get("sha256", "")))
            if reason:
                findings.append((art.label, ptr, reason))
    return findings


def _green_outcome(ctx, handoff, gate_id: str) -> bool:
    for go in handoff.get("gate_outcomes") or []:
        if not isinstance(go, dict) or go.get("gate_id") != gate_id:
            continue
        if go.get("exit_code") != 0:
            continue
        ref = go.get("report_ref")
        if isinstance(ref, dict) and _ref_ok(
            ctx.root, str(ref.get("path", "")), str(ref.get("sha256", ""))
        ) is None:
            return True
    return False


def chk_evidence(ctx) -> list[Finding]:
    findings: list[Finding] = []
    roles = {
        r.get("id"): r
        for r in ((ctx.registry_data or {}).get("roles") or [])
        if isinstance(r, dict)
    }
    for art in _iter_typed(ctx, "handoff_contract"):
        if art.data.get("stage_status") != "complete":
            continue
        role = roles.get(art.data.get("from_role"))
        if not role:
            continue
        for gate_id in role.get("gates") or []:
            if not _green_outcome(ctx, art.data, gate_id):
                findings.append(
                    (
                        art.label,
                        "/stage_status",
                        f"complete without a green outcome for assigned gate '{gate_id}'",
                    )
                )
    return findings


def chk_decisions_v1(ctx) -> list[Finding]:
    findings: list[Finding] = []
    for art in _iter_typed(ctx, "handoff_contract"):
        if art.data.get("stage_status") == "in_progress":
            continue
        decisions = art.data.get("decisions")
        if not decisions:
            findings.append((art.label, "/decisions", "stage-transition contract carries no decisions"))
            continue
        for i, d in enumerate(decisions):
            if not isinstance(d, dict):
                continue
            base = f"/decisions/{i}"
            if not str(d.get("choice") or "").strip():
                findings.append((art.label, base, "decision lacks a non-empty choice"))
            if not str(d.get("rationale") or "").strip():
                findings.append((art.label, base, "decision lacks a rationale"))
            rejected = d.get("rejected_alternatives")
            sentinel = d.get("alternatives_considered") == "none"
            if sentinel:
                if not str(d.get("alternatives_rationale") or "").strip():
                    findings.append(
                        (art.label, base, "alternatives sentinel requires its own rationale")
                    )
            elif not rejected:
                findings.append(
                    (art.label, base, "decision lacks rejected_alternatives or the explicit sentinel")
                )
    return findings


def chk_arm(ctx) -> list[Finding]:
    findings: list[Finding] = []
    for art in _iter_typed(ctx, "role_registry"):
        roles = [r for r in (art.data.get("roles") or []) if isinstance(r, dict)]
        role_ids = {r.get("id") for r in roles}
        diag_ids = {r.get("id") for r in roles if r.get("diagnostic_capability")}
        for i, arm in enumerate(art.data.get("arms") or []):
            if not isinstance(arm, dict):
                continue
            base = f"/arms/{i}"
            unknown = sorted(set(arm.get("roles") or []) - role_ids)
            if unknown:
                findings.append((art.label, base, f"arm references unknown role id '{unknown[0]}'"))
            if not (set(arm.get("roles") or []) & diag_ids) and "ablation" not in arm:
                findings.append(
                    (
                        art.label,
                        base,
                        "arm omits every diagnostic-capability role without an ablation marker",
                    )
                )
    return findings


def _iter_outcomes(ctx):
    for art in _iter_typed(ctx, "gate_outcome"):
        yield art, "", art.data
    for art in _iter_typed(ctx, "handoff_contract"):
        for i, go in enumerate(art.data.get("gate_outcomes") or []):
            if isinstance(go, dict):
                yield art, f"/gate_outcomes/{i}", go


def chk_thresh_v1(ctx) -> list[Finding]:
    findings: list[Finding] = []
    named = {
        t.get("name"): t.get("value")
        for t in ((ctx.config or {}).get("thresholds") or [])
        if isinstance(t, dict)
    }
    for art, base, outcome in _iter_outcomes(ctx):
        threshold = outcome.get("threshold")
        ptr = f"{base}/threshold"
        if not isinstance(threshold, dict):
            findings.append((art.label, ptr, "gate outcome lacks a named threshold"))
            continue
        name = threshold.get("name")
        if name not in named:
            findings.append((art.label, f"{ptr}/name", "threshold name not declared in KernelConfig"))
        elif threshold.get("value") != named[name]:
            findings.append(
                (art.label, f"{ptr}/value", "threshold value mismatches the committed KernelConfig")
            )
    return findings


def chk_protect(ctx) -> list[Finding]:
    findings: list[Finding] = []
    for art in _iter_typed(ctx, "kernel_config"):
        protected = art.data.get("protected")
        if not isinstance(protected, dict):
            findings.append((art.label, "/protected", "protected set missing"))
            continue
        for key in PROTECTED_KEYS:
            values = protected.get(key)
            if not values:
                findings.append(
                    (art.label, "/protected", f"mandatory protected member '{key}' missing or empty")
                )
        constitution = protected.get("speckit_constitution") or []
        if constitution and CONSTITUTION_PATH not in constitution:
            findings.append(
                (art.label, "/protected/speckit_constitution", "constitution path not protected")
            )
    return findings


def chk_map(ctx) -> list[Finding]:
    findings: list[Finding] = []
    config = ctx.config or {}
    required = list(config.get("required_mappings") or [])
    roots = tuple(config.get("speckit_roots") or [])
    for art in _iter_typed(ctx, "speckit_mapping"):
        rows = [m for m in (art.data.get("mappings") or []) if isinstance(m, dict)]
        covered = {m.get("artifact_type") for m in rows}
        for member in sorted(set(required) - covered):
            findings.append(
                (art.label, "/mappings", f"required mapping '{member}' has no row")
            )
        for i, m in enumerate(rows):
            target = str(m.get("target_path") or "")
            if roots and not target.startswith(roots):
                findings.append(
                    (art.label, f"/mappings/{i}/target_path", "target outside the declared roots")
                )
    return findings


def chk_harness_rows(ctx) -> list[Finding]:
    findings: list[Finding] = []
    for art in _iter_typed(ctx, "invocation_descriptor_set"):
        rows = [r for r in (art.data.get("rows") or []) if isinstance(r, dict)]
        by_harness = {r.get("harness") for r in rows}
        for name in sorted(set(art.data.get("declares") or []) - by_harness):
            findings.append((art.label, "/rows", f"declared harness '{name}' has no descriptor row"))
        for i, row in enumerate(rows):
            exits = {
                m.get("tool_exit")
                for m in (row.get("exit_code_map") or [])
                if isinstance(m, dict)
            }
            for required_exit in (2, 3):
                if required_exit not in exits:
                    findings.append(
                        (
                            art.label,
                            f"/rows/{i}/exit_code_map",
                            f"exit-code map omits the gate-tool exit-{required_exit} translation",
                        )
                    )
    return findings


IR_GATE_ID = "ir-gate"
IR_GATE_TOOL = "ir-gate-checker"


def chk_irgate_pin(ctx) -> list[Finding]:
    """ADR 0005: the 'ir-gate' gate id is pinned to one backing tool. A
    KernelConfig gates[] row or a gate outcome that binds 'ir-gate' to any
    other tool is the config-level alias of "map the IR gate to tests" and
    must red the corpus."""
    findings: list[Finding] = []
    for art in _iter_typed(ctx, "kernel_config"):
        for i, row in enumerate(art.data.get("gates") or []):
            if (
                isinstance(row, dict)
                and row.get("id") == IR_GATE_ID
                and row.get("tool") != IR_GATE_TOOL
            ):
                findings.append(
                    (
                        art.label,
                        f"/gates/{i}/tool",
                        "ir-gate must bind the pinned tool 'ir-gate-checker' (ADR 0005)",
                    )
                )
    for art, base, outcome in _iter_outcomes(ctx):
        if outcome.get("gate_id") == IR_GATE_ID and outcome.get("tool") != IR_GATE_TOOL:
            findings.append(
                (
                    art.label,
                    f"{base}/tool",
                    "ir-gate outcome not produced by the pinned tool 'ir-gate-checker' (ADR 0005)",
                )
            )
    return findings


def chk_debug(ctx) -> list[Finding]:
    findings: list[Finding] = []
    diag_ids = {
        r.get("id")
        for r in ((ctx.registry_data or {}).get("roles") or [])
        if isinstance(r, dict) and r.get("diagnostic_capability")
    }
    for art in _iter_typed(ctx, "handoff_contract"):
        rework = art.data.get("rework")
        if not isinstance(rework, dict):
            continue
        if rework.get("target_role") in diag_ids and "debug_report_ref" not in art.data:
            findings.append(
                (
                    art.label,
                    "/rework",
                    "rework edge targets the diagnostic-capability role without a DebugReport ref",
                )
            )
    return findings
