"""Thin SFN ↔ module adapter. Clients are never imported at load (Wave 0 §11)."""

from __future__ import annotations

from typing import Any

from claim_processor.models import ValidationResult
from claim_processor.pipeline import ClaimPipeline, _merge_guardrail
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


def breaker_probe(
    event: dict[str, Any],
    context: Any = None,
    *,
    pipeline: ClaimPipeline | None = None,
) -> dict[str, Any]:
    """SFN entry state: produce `$.breaker_open` for the BreakerCheck Choice.

    Review #3: the Choice read a variable no state populated, so the
    DegradedExtract path was unreachable. The probe adopts the live config
    first (AC-K3) and reads the shared breaker flag (AC-N2/N3).
    """
    pipe = _require_pipeline(pipeline)
    pipe.refresh_policy()
    return {**event, "breaker_open": pipe.breaker_is_open()}


def understand_extract(
    event: dict[str, Any],
    context: Any = None,
    *,
    pipeline: ClaimPipeline | None = None,
) -> dict[str, Any]:
    pipe = _require_pipeline(pipeline)
    pipe.refresh_policy()
    out = pipe.understand_extract(event["bucket"], event["key"])
    return {**event, **out}


def degraded_extract(
    event: dict[str, Any],
    context: Any = None,
    *,
    pipeline: ClaimPipeline | None = None,
) -> dict[str, Any]:
    """Breaker-open entry (AC-N2): extract via the degradation ladder.

    Same thin adapter as `understand_extract`; the deployed Lambda's config
    marks the primary model's breaker open, so `understand_extract` walks to a
    lower tier and never invokes the failing model.
    """
    pipe = _require_pipeline(pipeline)
    pipe.refresh_policy()
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
    pipe.refresh_policy()
    extract_usage = event.get("usage") or {}
    out = pipe.retrieve_summarize(event["extracted_info"], event["document_text"])
    merged = {**event, **out}
    merged["usage"] = {"extract": extract_usage, "summary": out.get("usage") or {}}
    merged["guardrail"] = _merge_guardrail(event.get("guardrail"), out.get("guardrail"))
    validation = pipe.validate(
        merged["extracted_info"],
        summary=merged["summary"],
        citations=merged["citations"],
        ungrounded=merged["ungrounded"],
    )
    result = pipe.result_from_event(merged, validation)
    merged["validation"] = _validation_dict(validation)
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
