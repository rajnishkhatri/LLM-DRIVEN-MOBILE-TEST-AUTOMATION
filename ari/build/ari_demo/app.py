"""Composition root + CLI — WAVE 2.

Wires the one-quantum hexagon end to end:

    identity gate → entitlement pre-check (before any data) → stage-0 router
    → stage-1 classifier fallback → adapter via the guarded wrapper
    → synthesis (full provenance tuple) → decision log

This is the only file that knows all the pieces; every component still depends
only on ports + domain. Gates 7 (injection canaries) and 11 (provenance
completeness) pass once this wiring exists — the proof the pieces composed.

CLI:  python -m ari_demo "question" --persona treasurer [--inject-timeout]
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Optional

from .adapters.docs import DocsAdapter
from .adapters.omni import OmniAdapter
from .adapters.ticket import TicketAdapter
from .core.entitlement import precheck
from .core.identity import gate
from .domain import tokens
from .domain.types import (
    AriResponse,
    FallThrough,
    RequestContext,
    Route,
    RouteDecision,
)
from .model.classifier import OfflineClassifier
from .model.model_port import OfflineModel
from .resilience.guarded import GuardTimeout, guarded_read
from .router.stage0 import route_stage0
from .synthesis.synthesis import DecisionLog, synthesize

_PERSONAS = {
    "treasurer": ("treasurer@Meridian Foods", "Meridian Foods", "treasurer"),
    "junior": ("analyst@Meridian Foods", "Meridian Foods", "junior-analyst"),
}


class Pipeline:
    """The wired Ari pipeline. `handle` runs one turn end to end."""

    def __init__(
        self,
        *,
        omni: OmniAdapter,
        docs: DocsAdapter,
        ticket: TicketAdapter,
        model: OfflineModel,
        classifier: OfflineClassifier,
        decision_log: Optional[DecisionLog] = None,
    ):
        self._omni = omni
        self._docs = docs
        self._ticket = ticket
        self._model = model
        self._classifier = classifier
        self._log = decision_log

    # -- routing ------------------------------------------------------------
    def _route(self, query: str, ctx: RequestContext):
        """Stage-0 first; fall through to the stage-1 classifier; never guess.

        Returns (route|None, rule_ids, confidence, clarify)."""
        decision = route_stage0(query)
        if isinstance(decision, RouteDecision):
            return decision.route, decision.fired, decision.score, False

        # Stage-0 fell through — ask the classifier (ADR 0001).
        result = self._classifier.classify(ctx, query)
        if result.route is not None and not result.clarify:
            return result.route, (), result.confidence, False

        # Below the classifier's bar → clarify, never a guess.
        return None, (), result.confidence, True

    # -- one turn -----------------------------------------------------------
    def handle(
        self,
        query: str,
        ctx: RequestContext,
        *,
        inject_timeout: bool = False,
    ) -> AriResponse:
        route, rule_ids, _conf, clarify = self._route(query, ctx)

        # Clarify: genuinely ambiguous. No capability, no data touched.
        if clarify or route is None:
            resp = synthesize(
                route=Route.OUT_OF_SCOPE,  # neutral marker; clarify flag carries it
                ctx=ctx,
                entitlement=precheck(ctx, query, Route.OUT_OF_SCOPE),
                model=self._model,
                clarify=True,
                rule_ids=rule_ids,
            )
            return self._record(resp, ctx, query)

        # Entitlement pre-check BEFORE any adapter/model sees data (ADR 0003).
        # Both refuse and narrow short-circuit here, so no org-wide or
        # cross-tenant data is ever fetched; synthesize emits the scoped copy.
        entitlement = precheck(ctx, query, route)
        if entitlement.action in ("refuse", "narrow"):
            resp = synthesize(
                route=route, ctx=ctx, entitlement=entitlement,
                model=self._model, rule_ids=rule_ids,
            )
            return self._record(resp, ctx, query)

        # Route to the capability, each adapter call under the guarded wrapper.
        if route is Route.DATA:
            resp = self._handle_data(query, ctx, entitlement, rule_ids, inject_timeout)
        elif route is Route.HOWTO:
            docs = self._docs.retrieve(ctx, query)
            resp = synthesize(
                route=Route.HOWTO, ctx=ctx, entitlement=entitlement,
                model=self._model, docs=docs, rule_ids=rule_ids,
            )
        elif route is Route.TICKET:
            receipt = self._ticket.create(ctx, query, ctx.idempotency_key)
            resp = synthesize(
                route=Route.TICKET, ctx=ctx, entitlement=entitlement,
                model=self._model, ticket=receipt, rule_ids=rule_ids,
            )
        else:  # OUT_OF_SCOPE, ACTION_P2 — recognitions, no adapter call
            resp = synthesize(
                route=route, ctx=ctx, entitlement=entitlement,
                model=self._model, rule_ids=rule_ids,
            )
        return self._record(resp, ctx, query)

    def _handle_data(self, query, ctx, entitlement, rule_ids, inject_timeout):
        omni = OmniAdapter(force_timeout=True) if inject_timeout else self._omni
        try:
            result = guarded_read(lambda: omni.query(ctx, query))
        except GuardTimeout:
            # The model never covers for a dead dependency (F6): degrade honestly.
            return synthesize(
                route=Route.DATA, ctx=ctx, entitlement=entitlement,
                model=self._model, degraded=True, rule_ids=rule_ids,
            )
        return synthesize(
            route=Route.DATA, ctx=ctx, entitlement=entitlement,
            model=self._model, omni=result, rule_ids=rule_ids,
        )

    def _record(self, resp: AriResponse, ctx: RequestContext, query: str) -> AriResponse:
        if self._log is not None:
            self._log.record(resp, ctx, query)
        return resp


def build_pipeline(
    *,
    persona: str = "treasurer",
    decision_log_path: Optional[Path] = None,
    ticket_store_path: Optional[Path] = None,
) -> Pipeline:
    """Assemble an offline Pipeline. The ticket store defaults to a fresh temp
    file so a run never mutates the committed fixture seed."""
    if ticket_store_path is None:
        tmp = tempfile.NamedTemporaryFile(
            prefix="ari-jira-", suffix=".json", delete=False
        )
        tmp.close()
        ticket_store_path = Path(tmp.name)
        # Start from a valid empty store (the adapter fills in any missing keys).
        ticket_store_path.write_text('{"next_seq": 1, "tickets": [], "by_key": {}}')

    log = DecisionLog(decision_log_path) if decision_log_path else None
    return Pipeline(
        omni=OmniAdapter(),
        docs=DocsAdapter(),
        ticket=TicketAdapter(store_path=ticket_store_path),
        model=OfflineModel(),
        classifier=OfflineClassifier(),
        decision_log=log,
    )


def _ctx_for_persona(persona: str, *, turn_id: str = "t1") -> RequestContext:
    if persona not in _PERSONAS:
        raise SystemExit(f"unknown persona {persona!r}; choose from {list(_PERSONAS)}")
    user, tenant, role = _PERSONAS[persona]
    # Exercise the identity gate in the demo: mint a signed token, then gate it.
    return gate(tokens.mint_token(user, tenant, role, "conv-cli", turn_id))


def _format(resp: AriResponse) -> str:
    p = resp.provenance
    flags = [n for n, v in (
        ("degraded", resp.degraded), ("clarify", resp.clarify),
        ("refused", resp.refused), ("ticket_offer", resp.ticket_offer),
    ) if v]
    lines = [
        "",
        resp.text,
        "",
        "— provenance " + "-" * 52,
        f"  route            : {p.route.value}",
        f"  sources          : "
        + (", ".join(f"{s.system}:{s.doc_id}@{s.version}" for s in p.sources) or "(none)"),
        f"  confidence       : {p.confidence}",
        f"  model / prompt   : {p.model_version} / {p.prompt_version}",
        f"  entitlement scope: {p.entitlement_scope}",
        f"  rule ids         : {', '.join(p.rule_ids) or '(classifier/none)'}",
    ]
    if resp.audit_event:
        lines.append(f"  audit event      : {resp.audit_event}")
    if resp.ticket_id:
        lines.append(f"  ticket           : {resp.ticket_id}")
    if flags:
        lines.append(f"  flags            : {', '.join(flags)}")
    lines.append("-" * 66)
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ari_demo", description="Ari — governed treasury assistant (offline demo)"
    )
    parser.add_argument("question", help="the user's turn")
    parser.add_argument("--persona", default="treasurer", choices=list(_PERSONAS))
    parser.add_argument("--inject-timeout", action="store_true",
                        help="force the Omni call to time out (TC-08)")
    parser.add_argument("--log", default=None, help="append a decision-log JSONL here")
    args = parser.parse_args(argv)

    pipeline = build_pipeline(
        persona=args.persona,
        decision_log_path=Path(args.log) if args.log else None,
    )
    ctx = _ctx_for_persona(args.persona)
    resp = pipeline.handle(args.question, ctx, inject_timeout=args.inject_timeout)
    print(_format(resp))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
