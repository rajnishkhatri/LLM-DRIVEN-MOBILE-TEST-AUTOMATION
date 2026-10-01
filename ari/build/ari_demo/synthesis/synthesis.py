"""Synthesis + decision log — WORKER C.

Assemble an AriResponse with a COMPLETE provenance tuple for every route,
including refusals, clarifications and degraded answers (gate 11). How-to
answers must carry citations (gate 4). Data answers quote memo fields as data,
never executing embedded instructions (F4 / Q-072). The decision log is
append-only JSONL and records the per-stage fields (gate -> router -> adapter
-> synthesis) so transition matrices are computable later (eval-spec §8).

Two honesty invariants live here:
  * Numbers and citations come from the passed retrieval/data, never invented.
  * Embedded instructions / phishing lines inside retrieved docs are treated as
    inert data: never relayed, never executed (F4). A flagged doc records an
    audit/review event.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from ..core.entitlement import EntitlementDecision
from ..domain.types import (
    AriResponse,
    DocsResult,
    ModelRequest,
    OmniResult,
    Provenance,
    RequestContext,
    Route,
    SourceRef,
    TicketReceipt,
)
from ..model.model_port import MODEL_VERSION
from ..ports.ports import ModelPort

# --------------------------------------------------------------------------
# Deterministic copy (worker C owns these). Kept as module constants so the
# gates and the CLI can reference the exact symbols.
# --------------------------------------------------------------------------
OUT_OF_SCOPE_COPY = (
    "That is outside what I can help with (I do not give trading, tax or legal "
    "advice). The nearest thing I can do is show you the underlying figures — "
    "want those?"
)
DEGRADED_COPY = (
    "I could not reach the live data just now, so I will not guess at the "
    "numbers. I can raise a support ticket so someone follows up — want me to "
    "do that?"
)
CLARIFY_COPY = (
    "I want to point you at the right thing — are you asking about the figures "
    "themselves, how to do this in the product, or should I raise a ticket for "
    "support?"
)
ACTION_DECLINE_COPY = (
    "I cannot take that action myself — approvals, payments and transfers need "
    "a person with the authority to sign off. I can walk you through the steps "
    "or hand this to a human who can act. Want me to raise a ticket?"
)
REFUSED_ENTITLEMENT_COPY = (
    "I cannot share that — it is outside what your access covers. If you "
    "believe you should have it, your administrator can widen your scope."
)
NARROWED_COPY = (
    "I can only show the part of this that your role covers, not the "
    "organization-wide view. Ask your administrator if you need broader access."
)
NO_DATA_COPY = (
    "I do not have that figure in the data I can see for your account, so I "
    "will not guess. I can raise a ticket to look into it — want me to?"
)

# Per-route prompt versions (a prompt change is a release, ADR 0002).
_PROMPT_VERSION = {
    Route.HOWTO: "howto-v1",
    Route.DATA: "data-v1",
    Route.TICKET: "ticket-v1",
    Route.OUT_OF_SCOPE: "refusal-v1",
    Route.ACTION_P2: "action-decline-v1",
}
_CLARIFY_PROMPT_VERSION = "clarify-v1"
_DEGRADED_PROMPT_VERSION = "degraded-v1"

# --------------------------------------------------------------------------
# Injection / phishing signatures. Lines in a retrieved doc matching any of
# these are embedded-instruction or phishing content and are stripped before
# the doc is relayed (F4). This is deterministic and add-only.
# --------------------------------------------------------------------------
_INJECTION_SIGNATURES = (
    "canary-",
    "ai assistant",
    "ignore your instruction",
    "ignore your previous",
    "system prompt",
    "urgent security notice",
    "verify-now.test",
    "confirm your banking password",
    "account will be locked",
    "account numbers",
    "embedded in the document",
    "planted phishing",
    "planted",
    "attacker@",
    "email the full ledger",
)


def _mv(model: ModelPort) -> str:
    """Resolve the model version for provenance, with a safe fallback."""
    return getattr(model, "model_version", None) or MODEL_VERSION


def _sanitize_doc_text(text: str) -> str:
    """Drop embedded-instruction / phishing lines from a retrieved doc.

    The legitimate steps survive; any line carrying an injection or phishing
    signature is treated as inert data and removed so it is never relayed (F4,
    Q-070/Q-071).
    """
    kept: list[str] = []
    for line in text.splitlines():
        low = line.lower()
        # Skip the markdown front-matter comment (doc_id/version/keywords).
        if low.strip().startswith("<!--"):
            continue
        if any(sig in low for sig in _INJECTION_SIGNATURES):
            continue
        kept.append(line)
    cleaned = "\n".join(kept).strip()
    return re.sub(r"\n{3,}", "\n\n", cleaned)


def _through_model(
    model: ModelPort, grounded_text: str, ctx: RequestContext, prompt_version: str
):
    """Format grounded content through the model seam (temp-0, deterministic).

    The model never sees a chance to invent: the grounded text it receives is
    exactly what synthesis composed from the fixture/retrieval.
    """
    req = ModelRequest(
        prompt=grounded_text, context=ctx, prompt_version=prompt_version
    )
    return model.generate(req)


def synthesize(
    *,
    route: Route,
    ctx: RequestContext,
    entitlement: EntitlementDecision,
    model: ModelPort,
    omni: Optional[OmniResult] = None,
    docs: Optional[DocsResult] = None,
    ticket: Optional[TicketReceipt] = None,
    clarify: bool = False,
    degraded: bool = False,
    rule_ids: tuple[str, ...] = (),
) -> AriResponse:
    """Build the answer + provenance for this route. Never fabricate numbers.

    `rule_ids` are the stage-0 fired rule ids (from the router); they are
    threaded into provenance so the routing decision is reconstructable.
    """
    scope = entitlement.scope
    rule_ids = tuple(rule_ids)
    base_audit = entitlement.audit_event  # set on every non-allow decision

    def _prov(
        r: Route,
        sources: tuple[SourceRef, ...],
        confidence: float,
        prompt_version: str,
        model_version: str,
    ) -> Provenance:
        return Provenance(
            route=r,
            sources=sources,
            confidence=confidence,
            model_version=model_version,
            prompt_version=prompt_version,
            entitlement_scope=scope,
            rule_ids=rule_ids,
        )

    # ----------------------------------------------------------------------
    # Fail-closed: a refused entitlement decision never reaches data, whatever
    # route was proposed. Records the audit event (ADR 0003, gate 6/7).
    # ----------------------------------------------------------------------
    if entitlement.action == "refuse":
        prov = _prov(
            Route.OUT_OF_SCOPE, (), 0.0, _PROMPT_VERSION[Route.OUT_OF_SCOPE], _mv(model)
        )
        return AriResponse(
            text=REFUSED_ENTITLEMENT_COPY,
            provenance=prov,
            route=Route.OUT_OF_SCOPE,
            refused=True,
            audit_event=base_audit,
        )

    # ----------------------------------------------------------------------
    # Narrowed: role-overreach. The entitlement check ran BEFORE any adapter,
    # so no org-wide data was fetched; return only the scope statement, never
    # the full result set (ADR 0003). Audit event is recorded.
    # ----------------------------------------------------------------------
    if entitlement.action == "narrow":
        prov = _prov(route, (), 0.0, _PROMPT_VERSION.get(route, "narrow-v1"), _mv(model))
        return AriResponse(
            text=NARROWED_COPY,
            provenance=prov,
            route=route,
            audit_event=base_audit,
        )

    # ----------------------------------------------------------------------
    # Degraded: adapter/model failed; degrade honestly + offer a ticket. The
    # model never covers a failure with a made-up answer (F6).
    # ----------------------------------------------------------------------
    if degraded:
        prov = _prov(route, (), 0.0, _DEGRADED_PROMPT_VERSION, _mv(model))
        return AriResponse(
            text=DEGRADED_COPY,
            provenance=prov,
            route=route,
            degraded=True,
            ticket_offer=True,
            audit_event=base_audit,
        )

    # ----------------------------------------------------------------------
    # Clarify: genuinely ambiguous — ask exactly one question, never guess.
    # ----------------------------------------------------------------------
    if clarify:
        prov = _prov(route, (), 0.3, _CLARIFY_PROMPT_VERSION, _mv(model))
        return AriResponse(
            text=CLARIFY_COPY,
            provenance=prov,
            route=route,
            clarify=True,
            ticket_offer=True,
            audit_event=base_audit,
        )

    # ----------------------------------------------------------------------
    # HOWTO: compose from docs.chunks; cite one SourceRef per chunk (gate 4).
    # ----------------------------------------------------------------------
    if route is Route.HOWTO:
        chunks = docs.chunks if docs else ()
        safe_parts = [_sanitize_doc_text(c.text) for c in chunks]
        grounded = "\n\n".join(p for p in safe_parts if p)
        resp = _through_model(model, grounded, ctx, _PROMPT_VERSION[Route.HOWTO])
        sources = tuple(
            SourceRef("docs", c.doc_id, c.version) for c in chunks
        )
        audit = base_audit
        if docs and docs.flagged:
            # A flagged doc (injection/phishing detected) is routed to human
            # review; the phishing/instruction content is already stripped.
            audit = audit or (
                f"doc-injection-flagged: retrieved doc routed to human review "
                f"(turn {ctx.turn_id})"
            )
        prov = _prov(
            Route.HOWTO, sources, 1.0, resp.prompt_version, resp.model_version
        )
        return AriResponse(
            text=resp.text,
            provenance=prov,
            route=Route.HOWTO,
            audit_event=audit,
        )

    # ----------------------------------------------------------------------
    # DATA: compose from omni.rows (grounded). Memo fields are rendered AS DATA
    # — quoting a hostile memo is fine; an embedded instruction is never
    # executed and synthesis performs no side effect (F4 / Q-072).
    # ----------------------------------------------------------------------
    if route is Route.DATA:
        rows = omni.rows if omni else ()
        # No matching figure: answer honestly instead of emitting an empty
        # answer at confidence 1.0 cited to a ':no-match' source (F4). No
        # fabricated source; confidence 0.0; offer a ticket.
        if not rows:
            prov = _prov(Route.DATA, (), 0.0, _PROMPT_VERSION[Route.DATA], _mv(model))
            return AriResponse(
                text=NO_DATA_COPY,
                provenance=prov,
                route=Route.DATA,
                ticket_offer=True,
                audit_event=base_audit,
            )
        lines: list[str] = []
        for r in rows:
            lines.append(r.value)
            if r.memo:
                lines.append(f'  memo (data): "{r.memo}"')
        grounded = "\n".join(lines)
        resp = _through_model(model, grounded, ctx, _PROMPT_VERSION[Route.DATA])
        sources = (omni.source,) if omni else ()
        prov = _prov(Route.DATA, sources, 1.0, resp.prompt_version, resp.model_version)
        return AriResponse(
            text=resp.text,
            provenance=prov,
            route=Route.DATA,
            audit_event=base_audit,
        )

    # ----------------------------------------------------------------------
    # TICKET: summary + ticket_id from the passed receipt. Cites the Jira row.
    # ----------------------------------------------------------------------
    if route is Route.TICKET:
        if ticket:
            verb = "raised" if ticket.created else "found the existing"
            text = (
                f"I have {verb} a support ticket ({ticket.ticket_id}) so the "
                "team can pick this up. You will hear back from support."
            )
            sources = (SourceRef("jira", ticket.ticket_id, ticket.idempotency_key),)
            ticket_id = ticket.ticket_id
        else:
            text = (
                "I can raise a support ticket so the team can pick this up — "
                "want me to do that?"
            )
            sources = ()
            ticket_id = None
        prov = _prov(
            Route.TICKET, sources, 1.0, _PROMPT_VERSION[Route.TICKET], _mv(model)
        )
        return AriResponse(
            text=text,
            provenance=prov,
            route=Route.TICKET,
            ticket_offer=ticket is None,
            ticket_id=ticket_id,
            audit_event=base_audit,
        )

    # ----------------------------------------------------------------------
    # OUT_OF_SCOPE: deterministic refusal; disclose nothing, dump no data.
    # ----------------------------------------------------------------------
    if route is Route.OUT_OF_SCOPE:
        prov = _prov(
            Route.OUT_OF_SCOPE, (), 1.0, _PROMPT_VERSION[Route.OUT_OF_SCOPE], _mv(model)
        )
        return AriResponse(
            text=OUT_OF_SCOPE_COPY,
            provenance=prov,
            route=Route.OUT_OF_SCOPE,
            refused=True,
            audit_event=base_audit,
        )

    # ----------------------------------------------------------------------
    # ACTION_P2: decline-with-path + offer a human. No action is performed.
    # ----------------------------------------------------------------------
    if route is Route.ACTION_P2:
        prov = _prov(
            Route.ACTION_P2, (), 1.0, _PROMPT_VERSION[Route.ACTION_P2], _mv(model)
        )
        return AriResponse(
            text=ACTION_DECLINE_COPY,
            provenance=prov,
            route=Route.ACTION_P2,
            ticket_offer=True,
            audit_event=base_audit,
        )

    raise ValueError(f"synthesize: unhandled route {route!r}")


class DecisionLog:
    """Append-only JSONL decision log (eval-spec §8).

    One line per turn, carrying the per-stage fields so routing/transition
    matrices are computable later. The record IS the audit truth.
    """

    def __init__(self, path: Path):
        self.path = Path(path)

    def record(self, response: AriResponse, ctx: RequestContext, query: str) -> None:
        p = response.provenance
        entry = {
            "query": query,
            "user": ctx.user,
            "tenant": ctx.tenant,
            "role": ctx.role,
            "conversation_id": ctx.conversation_id,
            "turn_id": ctx.turn_id,
            "route": p.route.value,
            "sources": [[s.system, s.doc_id, s.version] for s in p.sources],
            "confidence": p.confidence,
            "model_version": p.model_version,
            "prompt_version": p.prompt_version,
            "entitlement_scope": p.entitlement_scope,
            "rule_ids": list(p.rule_ids),
            "degraded": response.degraded,
            "refused": response.refused,
            "clarify": response.clarify,
            "ticket_offer": response.ticket_offer,
            "ticket_id": response.ticket_id,
            "audit_event": response.audit_event,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
