"""Graceful-degradation tier ladder + rule-based floor (ADR 0014).

`walk_tiers` descends advanced FM → basic FM → rule-based extractor so core
intake survives a model outage (AC-P1). The rule-based extractor is a
deterministic floor that yields the five-field schema shape (AC-P2); a result
produced below the advanced tier is `is_degraded` and the pipeline routes it to
human review, never auto-approve (AC-P3, enforced in routing R-09).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable

from claim_processor.adapter import AdapterResult, CallOutcome
from claim_processor.models import EXTRACT_FIELDS

RULE_BASED = "rule_based"


class DegradationDisabledError(RuntimeError):
    """Extract failed while the `degradation_enabled` kill-switch is off.

    The switch existed but was never read (review #11): off must mean the step
    fails loudly — never a silent walk down the ladder (AC-M5)."""
_ADVANCED = "advanced"
_BASIC = "basic"

_POLICY_RE = re.compile(r"\b([A-Z]{2,}[-\s]?[A-Z]*[-\s]?\d[\w-]*)\b")
_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_AMOUNT_RE = re.compile(r"\$\s*([\d,]+(?:\.\d{1,2})?)")


@dataclass
class DegradeResult:
    tier: str  # "advanced" | "basic" | "rule_based"
    trigger: str | None  # "breaker" | "exhausted_retry" | None (advanced ok)
    text: str = ""
    model_id: str | None = None
    extracted: dict[str, Any] | None = None
    outcome: CallOutcome | None = None


def is_degraded(tier: str) -> bool:
    """True for any tier below the advanced FM (AC-P3)."""
    return tier != _ADVANCED


class RuleBasedExtractor:
    """Deterministic last-resort extractor — a floor, not an FM competitor."""

    def extract(self, document_text: str) -> dict[str, Any]:
        text = document_text or ""
        return {
            "claimant_name": self._labelled(text, "name"),
            "policy_number": self._first(_POLICY_RE, text),
            "incident_date": self._first(_DATE_RE, text),
            "claim_amount": self._amount(text),
            "incident_description": text.strip()[:280],
        }

    @staticmethod
    def _first(pattern: re.Pattern[str], text: str) -> str:
        match = pattern.search(text)
        return match.group(1) if match else ""

    @staticmethod
    def _amount(text: str) -> float | str:
        match = _AMOUNT_RE.search(text)
        if not match:
            return ""
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            return ""

    @staticmethod
    def _labelled(text: str, label: str) -> str:
        match = re.search(rf"{label}\s*[:\-]\s*([^\n,;]+)", text, re.IGNORECASE)
        return match.group(1).strip() if match else ""


def walk_tiers(
    document_text: str,
    tiers: list[str],
    invoke: Callable[[str], AdapterResult],
    *,
    is_open: Callable[[str], bool] | None = None,
) -> DegradeResult:
    """Descend the configured tier list; return the first usable result.

    `tiers` is model ids, optionally ending with the sentinel ``rule_based``.
    `invoke(model_id)` calls the adapter; `is_open(model_id)` reports the
    breaker (AC-N2 → skip an open model to the next tier).
    """
    is_open = is_open or (lambda _m: False)
    trigger: str | None = None
    for index, tier_model in enumerate(tiers):
        if tier_model == RULE_BASED:
            return _rule_based(document_text, trigger)
        if is_open(tier_model):
            trigger = trigger or "breaker"
            continue
        result = invoke(tier_model)
        if result.outcome == CallOutcome.OK:
            label = _ADVANCED if index == 0 else _BASIC
            return DegradeResult(
                tier=label,
                trigger=None if index == 0 else (trigger or "exhausted_retry"),
                text=result.text,
                model_id=result.model_id,
                outcome=result.outcome,
            )
        trigger = trigger or "exhausted_retry"
    # All FM tiers exhausted with no rule_based sentinel → floor anyway (never empty).
    return _rule_based(document_text, trigger)


def _rule_based(document_text: str, trigger: str | None) -> DegradeResult:
    return DegradeResult(
        tier=RULE_BASED,
        trigger=trigger or "exhausted_retry",
        extracted=RuleBasedExtractor().extract(document_text),
    )


# Re-export for callers that only need the field names.
__all__ = [
    "DegradationDisabledError",
    "DegradeResult",
    "RuleBasedExtractor",
    "walk_tiers",
    "is_degraded",
    "RULE_BASED",
    "EXTRACT_FIELDS",
]
