"""Synthesis + decision log — WORKER C (stub).

Assemble an AriResponse with a COMPLETE provenance tuple for every route,
including refusals, clarifications and degraded answers (gate 11). How-to
answers must carry citations (gate 4). Data answers quote memo fields as data,
never executing embedded instructions (F4 / Q-072). The decision log is
append-only JSONL and records the per-stage fields (gate -> router -> adapter
-> synthesis) so transition matrices are computable later (eval-spec §8).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..core.entitlement import EntitlementDecision
from ..domain.types import (
    AriResponse,
    DocsResult,
    OmniResult,
    RequestContext,
    Route,
    TicketReceipt,
)
from ..ports.ports import ModelPort

# Deterministic refusal / clarify copy (worker C finalizes). Kept as module
# constants so the gates can reference the symbols.
OUT_OF_SCOPE_COPY = (
    "That is outside what I can help with (I do not give trading, tax or legal "
    "advice). The nearest thing I can do is show you the underlying figures — "
    "want those?"
)


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
) -> AriResponse:
    """Build the answer + provenance for this route. Never fabricate numbers."""
    raise NotImplementedError("worker C: assemble answer + full provenance tuple")


class DecisionLog:
    """Append-only JSONL decision log (eval-spec §8)."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def record(self, response: AriResponse, ctx: RequestContext, query: str) -> None:
        raise NotImplementedError("worker C: append-only JSONL record")
