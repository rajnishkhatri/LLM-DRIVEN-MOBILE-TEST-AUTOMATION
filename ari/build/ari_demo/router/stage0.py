"""Deterministic stage-0 router — WORKER A (stub). Shape locked in HANDOVER §8.

THRESHOLD/MARGIN are OUTPUTS of the sweep (sweep.py), not opinions: import the
chosen values from the committed sweep-report.md. The values below are
placeholders that keep the module importable until the sweep runs; gate 1
requires the report to exist and these to match it.
"""
from __future__ import annotations

from ..domain.types import FallThrough, RouteDecision

# Placeholders (HANDOVER §8). Worker A replaces these with values read from the
# committed sweep-report.md.
THRESHOLD: float = 0.6
MARGIN: float = 0.3


def norm(utterance: str) -> str:
    """Normalize an utterance for matching (lowercase, collapse whitespace)."""
    return " ".join(utterance.lower().split())


def route_stage0(utterance: str) -> "RouteDecision | FallThrough":
    """Rules first; a single Tier.A hit wins; else score + threshold/margin;
    never guess. Returns FallThrough(reason=...) on a miss."""
    raise NotImplementedError("worker A: implement the HANDOVER §8 ladder")
