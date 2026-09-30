"""Stage-1 classifier — WORKER C. ADR 0001 / HANDOVER §9.

A port (ClassifierPort). Offline default = deterministic fixture-backed
classifier: recorded intents for the golden set's fall-through rows; below the
confidence floor -> clarify or ticket, never a guess. The Agent Squad library is
the LIVE adapter, referenced here in comments/config, NOT installed.

Design invariant (gate 3): the genuinely-ambiguous golden rows (route-null) and
anything scoring below CLASSIFIER_CONFIDENCE_FLOOR must return
ClassifierResult(route=None, clarify=True) — the classifier never emits a
confident guess for them. Fall-through rows that carry a clear recorded intent
MAY return a confident route.
"""
from __future__ import annotations

import re

from ..domain.types import ClassifierResult, RequestContext, Route

CLASSIFIER_CONFIDENCE_FLOOR: float = 0.6

# Live adapter (NOT installed this build): Agent Squad would sit behind this
# same ClassifierPort as the online implementation.
#   from agent_squad.classifiers import BedrockClassifier  # live only

_WS = re.compile(r"\s+")


def _norm(utterance: str) -> str:
    """Lowercase, strip punctuation to spaces, collapse whitespace."""
    lowered = utterance.lower().strip()
    lowered = re.sub(r"[^a-z0-9 ]+", " ", lowered)
    return _WS.sub(" ", lowered).strip()


# The eight genuinely-ambiguous rows (golden set, expected.route == null). These
# are recorded as clarify: two or more capabilities are plausible and the honest
# move is to ask one question, never to guess (ADR 0001, gate 3).
_AMBIGUOUS = {
    "why is my forecast off",
    "the numbers do not match",
    "i need help with approvals",
    "export is not working",
    "set up nordbank",
    "my balance is wrong",
    "what happened to my report",
    "approvals",
}

# Keyword signals for the fall-through rows that DO carry a clear recorded
# intent (e.g. terse follow-ups whose capability is unambiguous even without
# context). Each term contributes a confident vote toward one capability.
_SIGNALS: tuple[tuple[Route, tuple[str, ...]], ...] = (
    (Route.DATA, ("eur", "by bank", "balance", "forecast variance", "q2",
                  "currency", "outflow", "cash")),
    (Route.HOWTO, ("how do i", "settings page", "which settings", "set up",
                   "configure", "where do i")),
    (Route.TICKET, ("raise a ticket", "raise the ticket", "open a ticket",
                    "support to", "someone from support")),
)


class OfflineClassifier:
    """Deterministic ClassifierPort over recorded intents."""

    def classify(self, ctx: RequestContext, utterance: str) -> ClassifierResult:
        norm = _norm(utterance)

        # 1. Genuinely-ambiguous rows -> clarify, never a confident route.
        if norm in _AMBIGUOUS:
            return ClassifierResult(route=None, confidence=0.3, clarify=True)

        # 2. Deterministic keyword vote for rows with a clear recorded intent.
        votes: dict[Route, int] = {}
        for route, terms in _SIGNALS:
            hits = sum(1 for t in terms if t in norm)
            if hits:
                votes[route] = votes.get(route, 0) + hits

        if votes:
            ranked = sorted(votes.items(), key=lambda kv: kv[1], reverse=True)
            (top_route, top_hits) = ranked[0]
            runner_hits = ranked[1][1] if len(ranked) > 1 else 0
            # A single dominant capability clears the floor; a tie is ambiguous.
            if top_hits > runner_hits:
                # Map hit strength to a confidence at or above the floor.
                confidence = min(0.95, CLASSIFIER_CONFIDENCE_FLOOR + 0.1 * top_hits)
                return ClassifierResult(
                    route=top_route, confidence=confidence, clarify=False
                )

        # 3. No clear signal (below the floor) -> clarify, never a guess.
        return ClassifierResult(route=None, confidence=0.2, clarify=True)
