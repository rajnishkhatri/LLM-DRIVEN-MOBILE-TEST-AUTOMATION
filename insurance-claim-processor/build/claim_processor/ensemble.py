"""Field-level extraction ensembling (ADR 0013).

`combine` votes each required field across member outputs and reports a
per-field agreement fraction. A field whose winning value has agreement below
the threshold is `low_confidence` — the pipeline routes such a claim to human
review and never auto-approves (AC-O1, enforced in routing R-09). `has_quorum`
lets the pipeline fall back to the single primary model when too few members
answer (AC-O5). Extraction only — the summary stays single-model (AC-O3).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any


@dataclass
class EnsembleResult:
    extracted: dict[str, Any]
    agreement: dict[str, float]
    members: list[str]
    low_confidence_fields: list[str]


def _norm(value: Any) -> str:
    """Comparable key: numbers by float value, everything else case-folded."""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return str(float(value))
    text = str(value).strip()
    try:
        return str(float(text.replace(",", "")))
    except ValueError:
        return text.lower()


def combine(
    member_outputs: list[tuple[str, dict[str, Any]]],
    *,
    required_fields: tuple[str, ...],
    agreement_threshold: float = 0.5,
) -> EnsembleResult:
    """Majority-vote each required field; flag low-agreement fields."""
    members = [model_id for model_id, _ in member_outputs]
    parsed = [d for _, d in member_outputs if isinstance(d, dict)]
    denom = len(parsed) or 1

    extracted: dict[str, Any] = {}
    agreement: dict[str, float] = {}
    low_confidence: list[str] = []

    for field in required_fields:
        values = [d.get(field) for d in parsed if d.get(field) not in (None, "")]
        if not values:
            extracted[field] = None
            agreement[field] = 0.0
            low_confidence.append(field)
            continue
        counts = Counter(_norm(v) for v in values)
        winner_norm, winner_count = counts.most_common(1)[0]
        winner_value = next(v for v in values if _norm(v) == winner_norm)
        frac = winner_count / denom
        extracted[field] = winner_value
        agreement[field] = frac
        # Confidence requires a STRICT majority of members (review #5): an even
        # split (2-model 50/50, 2-2 tie) scores exactly the 0.5 threshold and
        # must flag, or a real disagreement auto-approves (AC-O1).
        if frac < agreement_threshold or winner_count * 2 <= denom:
            low_confidence.append(field)

    return EnsembleResult(extracted, agreement, members, low_confidence)


def has_quorum(usable_count: int, *, quorum: int) -> bool:
    """True when enough members answered to trust the vote (AC-O5)."""
    return usable_count >= quorum


def resolve_quorum(configured: Any, member_count: int) -> int:
    """Quorum from config, guarding the `bool ⊂ int` trap (review #9).

    `ensemble_quorum: true` in a flag document is boolean noise, not a quorum
    of 1 — only an explicit positive non-bool int wins; anything else falls
    back to a strict majority of the configured members.
    """
    if (
        isinstance(configured, int)
        and not isinstance(configured, bool)
        and configured > 0
    ):
        return configured
    return max(2, member_count // 2 + 1) if member_count else 2
