from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

_ALLOWED_DECISIONS = frozenset({"approve", "correct", "reject", "review-expired"})


class UnknownDecisionError(ValueError):
    """decision is not approve, correct, reject, or review-expired."""


class CorrectionsRequiredError(ValueError):
    """corrections is required when decision is correct."""


def apply_decision(
    pending: dict,
    *,
    decision: str,
    reviewer_id: str,
    timestamp: str | None = None,
    corrections: dict | None = None,
) -> dict:
    """Apply a HITL decision to a pending-review record.

    correct         → reviewer's values are the final extracted_info;
                      no re-summarize / re-validate / re-retrieve (AC-E3).
                      field_changes[] = [{field, from, to}, ...]
    approve/reject  → record decision; extracted_info unchanged
    review-expired  → mark review.decision = "review-expired" and escalate
                      (never auto-approve)
    """
    if decision not in _ALLOWED_DECISIONS:
        raise UnknownDecisionError(f"unknown decision: {decision!r}")
    if decision == "correct" and corrections is None:
        raise CorrectionsRequiredError("corrections required for decision='correct'")

    record = deepcopy(pending)
    field_changes: list[dict[str, Any]] = []
    if decision == "correct":
        original = record["extracted_info"]
        updated = dict(original)
        for field, new_value in corrections.items():
            field_changes.append(
                {"field": field, "from": original.get(field), "to": new_value}
            )
            updated[field] = new_value
        record["extracted_info"] = updated
    elif decision == "review-expired":
        record["route"] = "human_review"

    record["review"] = {
        "decision": decision,
        "reviewer_id": reviewer_id,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "field_changes": field_changes,
    }
    return record
