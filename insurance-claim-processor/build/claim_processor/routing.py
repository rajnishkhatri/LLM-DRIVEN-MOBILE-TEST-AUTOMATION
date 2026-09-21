from __future__ import annotations

from typing import Literal

from claim_processor.config import EscalationPolicy
from claim_processor.models import ProcessingResult


def route_claim(
    result: ProcessingResult,
    policy: EscalationPolicy,
) -> Literal["auto_approve", "human_review"]:
    flags = result.validation.flags
    if not result.validation.accepted:
        return "human_review"
    if any(
        flag.startswith("missing_keys:")
        or flag == "invalid_json"
        or flag == "not_an_object"
        for flag in flags
    ):
        return "human_review"
    if any(flag.startswith("empty_fields:") for flag in flags):
        return "human_review"
    if (
        result.ungrounded
        or "ungrounded" in flags
        or "missing_citations" in flags
    ):
        return "human_review"
    if any(flag.startswith("pii_") for flag in flags):
        return "human_review"
    if any(
        any(flag == prefix or flag.startswith(prefix) for prefix in policy.force_review_flags)
        for flag in flags
    ):
        return "human_review"
    amount = _numeric_claim_amount(result.extracted_info)
    if amount is None or amount > policy.amount_threshold:
        return "human_review"
    return "auto_approve"


def _numeric_claim_amount(extracted_info: object) -> float | None:
    if not isinstance(extracted_info, dict):
        return None
    raw = extracted_info.get("claim_amount")
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        try:
            return float(raw)
        except ValueError:
            return None
    return None
