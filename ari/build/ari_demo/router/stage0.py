"""Deterministic stage-0 router — WORKER A. Shape locked in HANDOVER §8.

Rules first; a single Tier.A capability hit wins outright; otherwise a weighted
score resolved by THRESHOLD/MARGIN; never a guess (a miss returns FallThrough).

THRESHOLD/MARGIN are OUTPUTS of the sweep (sweep.py), committed in
sweep-report.md. Gate 1 parses the report's `CHOSEN theta=<x> margin=<y>` line
and asserts these constants equal it, so they are kept in lockstep with the
committed report below.
"""
from __future__ import annotations

from collections import defaultdict

from ..domain.types import FallThrough, RouteDecision, Tier
from .rules import RULES

# Chosen by sweep.py over the golden set (see ari/build/sweep-report.md):
# maximum fast-path coverage subject to precision >= 0.99, most-stringent tie.
THRESHOLD: float = 0.8
MARGIN: float = 0.5


def norm(utterance: str) -> str:
    """Normalize an utterance for matching (lowercase, collapse whitespace)."""
    return " ".join(utterance.lower().split())


def route_stage0(
    utterance: str,
    threshold: "float | None" = None,
    margin: "float | None" = None,
) -> "RouteDecision | FallThrough":
    """Rules first; a single Tier.A hit wins; else score + threshold/margin;
    never guess. Returns FallThrough(reason=...) on a miss.

    `threshold`/`margin` default to the committed module constants; the sweep
    passes grid values so it measures exactly this decision function.
    """
    threshold = THRESHOLD if threshold is None else threshold
    margin_bar = MARGIN if margin is None else margin

    text = norm(utterance)
    fired = [r for r in RULES if r.pattern.search(text)]
    fired_ids = tuple(r.id for r in fired)

    tier_a = {r.capability for r in fired if r.tier is Tier.A}
    if len(tier_a) == 1:
        cap = next(iter(tier_a))
        return RouteDecision(route=cap, score=1.0, margin=1.0, fired=fired_ids)

    scores: "defaultdict[object, float]" = defaultdict(float)
    for r in fired:
        scores[r.capability] += r.weight
    if not scores:
        return FallThrough(reason="no_signal")

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top, s1 = ranked[0]
    s2 = ranked[1][1] if len(ranked) > 1 else 0.0
    if s1 >= threshold and (s1 - s2) >= margin_bar:
        return RouteDecision(route=top, score=s1, margin=s1 - s2, fired=fired_ids)
    return FallThrough(reason="ambiguous" if s2 else "weak_signal", fired=fired_ids)
