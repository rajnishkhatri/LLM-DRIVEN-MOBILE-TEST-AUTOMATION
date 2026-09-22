"""Thin SFN ↔ module adapter. Clients are never imported at load (Wave 0 §11)."""

from __future__ import annotations

from typing import Any

from claim_processor.models import ProcessingResult, ValidationResult
from claim_processor.pipeline import ClaimPipeline
from claim_processor.review import apply_decision


class MissingPipelineError(TypeError):
    """handler was invoked without an injected ClaimPipeline."""


def _require_pipeline(pipeline: ClaimPipeline | None) -> ClaimPipeline:
    if pipeline is None:
        raise MissingPipelineError(
            "inject ClaimPipeline; handlers do not construct clients"
        )
    return pipeline


def _validation_dict(validation: ValidationResult) -> dict[str, Any]:
    return {"accepted": validation.accepted, "flags": validation.flags}


def understand_extract(
    event: dict[str, Any],
    context: Any = None,
    *,
    pipeline: ClaimPipeline | None = None,
) -> dict[str, Any]:
    pipe = _require_pipeline(pipeline)
    out = pipe.understand_extract(event["bucket"], event["key"])
    return {**event, **out}


def validate(
    event: dict[str, Any],
    context: Any = None,
    *,
    pipeline: ClaimPipeline | None = None,
) -> dict[str, Any]:
    pipe = _require_pipeline(pipeline)
    validation = pipe.validate(
        event["extracted_info"],
        summary=event.get("summary"),
        citations=event.get("citations"),
        ungrounded=event.get("ungrounded"),
    )
    return {**event, "validation": _validation_dict(validation)}


def retrieve_summarize(
    event: dict[str, Any],
    context: Any = None,
    *,
    pipeline: ClaimPipeline | None = None,
) -> dict[str, Any]:
    pipe = _require_pipeline(pipeline)
    out = pipe.retrieve_summarize(event["extracted_info"], event["document_text"])
    merged = {**event, **out}
    validation = pipe.validate(
        merged["extracted_info"],
        summary=merged["summary"],
        citations=merged["citations"],
        ungrounded=merged["ungrounded"],
    )
    merged["validation"] = _validation_dict(validation)
    result = ProcessingResult(
        extracted_info=merged["extracted_info"],
        summary=merged["summary"],
        citations=merged["citations"],
        ungrounded=merged["ungrounded"],
        validation=validation,
        extract_model_id=merged.get("extract_model_id") or "",
        summary_model_id=merged.get("summary_model_id") or "",
        prompt_versions=pipe.templates.versions(),
    )
    merged["route"] = pipe.route(result)
    return merged


def record(
    event: dict[str, Any],
    context: Any = None,
    *,
    pipeline: ClaimPipeline | None = None,
) -> dict[str, Any]:
    pipe = _require_pipeline(pipeline)
    payload: dict[str, Any] = dict(event)
    hitl = event.get("hitl") or {}
    decision = hitl.get("decision") or event.get("decision")
    review = event.get("review") or {}
    if decision in {"approve", "correct", "reject"} and not review.get("decision"):
        payload = apply_decision(
            event,
            decision=decision,
            reviewer_id=hitl.get("reviewer_id") or event["reviewer_id"],
            corrections=hitl.get("corrections") or event.get("corrections"),
        )
    return pipe.record(event["bucket"], event["key"], payload)


def expire_review(
    event: dict[str, Any],
    context: Any = None,
    *,
    pipeline: ClaimPipeline | None = None,
) -> dict[str, Any]:
    _require_pipeline(pipeline)
    return apply_decision(
        event,
        decision="review-expired",
        reviewer_id="sfn-timeout",
    )
