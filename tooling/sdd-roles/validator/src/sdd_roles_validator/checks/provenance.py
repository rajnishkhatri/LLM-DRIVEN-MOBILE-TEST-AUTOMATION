"""Provenance cluster: CHK-SCHEMA, CHK-PROV-PRESENT, CHK-FENCE, CHK-TAINT, CHK-TOOLBIND."""

from __future__ import annotations

import hashlib

from jsonschema import Draft202012Validator

Finding = tuple[str, str, str]  # (artifact_label, json_pointer, detail)


def _ptr(parts) -> str:
    return "".join(f"/{p}" for p in parts)


def _iter_handoffs(ctx):
    for art in ctx.artifacts:
        if art.atype == "handoff_contract" and not art.parse_error:
            yield art


def _provenance_sites(handoff: dict):
    """Yield (pointer, container) for every content-bearing site that carries provenance."""
    if isinstance(handoff.get("summary"), dict):
        yield "/summary", handoff["summary"]
    for i, d in enumerate(handoff.get("decisions") or []):
        if isinstance(d, dict):
            yield f"/decisions/{i}", d
    for i, ev in enumerate(handoff.get("completion_evidence") or []):
        if isinstance(ev, dict):
            yield f"/completion_evidence/{i}", ev


def chk_schema(ctx) -> list[Finding]:
    findings: list[Finding] = []
    for art in ctx.artifacts:
        if art.parse_error:
            findings.append((art.label, "", "unparseable JSON"))
            continue
        if art.atype is None:
            findings.append((art.label, "/artifact_type", "missing or unknown artifact_type"))
            continue
        validator = Draft202012Validator(ctx.schemas[art.atype])
        errors = sorted(
            validator.iter_errors(art.data),
            key=lambda e: (_ptr(e.absolute_path), str(e.validator), e.message),
        )
        for err in errors:
            base = _ptr(err.absolute_path)
            if err.validator == "additionalProperties" and isinstance(err.instance, dict):
                allowed = set((err.schema or {}).get("properties", {}))
                for prop in sorted(set(err.instance) - allowed):
                    findings.append((art.label, f"{base}/{prop}", "unexpected property"))
            else:
                findings.append(
                    (art.label, base, f"{err.validator}: {err.message[:120]}")
                )
    return findings


def chk_prov_present(ctx) -> list[Finding]:
    findings: list[Finding] = []
    for art in _iter_handoffs(ctx):
        for ptr, container in _provenance_sites(art.data):
            if "provenance" not in container:
                findings.append(
                    (art.label, f"{ptr}/provenance", "field lacks its provenance discriminator")
                )
    return findings


def chk_fence(ctx) -> list[Finding]:
    findings: list[Finding] = []
    for art in _iter_handoffs(ctx):
        for i, fence in enumerate(art.data.get("fences") or []):
            if not isinstance(fence, dict):
                continue
            base = f"/fences/{i}"
            content = fence.get("content", "")
            digest = hashlib.sha256(str(content).encode("utf-8")).hexdigest()
            if fence.get("fence_id") != digest:
                findings.append(
                    (art.label, f"{base}/fence_id", "fence id is not the full sha256 of the fenced bytes")
                )
            if not fence.get("source_uri"):
                findings.append((art.label, f"{base}/source_uri", "fence lacks source URI"))
            if not fence.get("retrieved_at"):
                findings.append((art.label, f"{base}/retrieved_at", "fence lacks retrieval timestamp"))
    return findings


def chk_taint(ctx) -> list[Finding]:
    findings: list[Finding] = []
    for art in _iter_handoffs(ctx):
        fence_ids = {
            f.get("fence_id")
            for f in (art.data.get("fences") or [])
            if isinstance(f, dict) and f.get("fence_id")
        }
        for ptr, container in _provenance_sites(art.data):
            prov = container.get("provenance")
            if not isinstance(prov, dict):
                continue
            derived = set(prov.get("derived_from") or [])
            if derived & fence_ids and prov.get("source") != "environment_quoted":
                findings.append(
                    (
                        art.label,
                        f"{ptr}/provenance",
                        "derived from an environment_quoted fence but not labeled environment_quoted",
                    )
                )
    return findings


def chk_toolbind(ctx) -> list[Finding]:
    findings: list[Finding] = []
    allowlist = set((ctx.config or {}).get("gate_tool_allowlist") or [])
    for art in _iter_handoffs(ctx):
        for ptr, container in _provenance_sites(art.data):
            prov = container.get("provenance")
            if not isinstance(prov, dict) or prov.get("source") != "tool_output":
                continue
            tool = prov.get("tool")
            base = f"{ptr}/provenance/tool"
            if not isinstance(tool, dict):
                findings.append((art.label, base, "tool_output lacks a registered tool binding"))
                continue
            if tool.get("id") not in allowlist:
                findings.append((art.label, f"{base}/id", "tool id not in KernelConfig gate-tool allowlist"))
            if not tool.get("version"):
                findings.append((art.label, f"{base}/version", "tool binding lacks tool_version"))
            if not tool.get("invocation_digest"):
                findings.append((art.label, f"{base}/invocation_digest", "tool binding lacks invocation digest"))
    return findings
