from __future__ import annotations

import os
from dataclasses import dataclass

from claim_processor.models import (
    EXTRACT_MODEL_EXAMPLE,
    SUMMARY_MODEL_EXAMPLE,
    UNDERSTAND_MODEL_EXAMPLE,
)


def _env(name: str) -> str | None:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return None
    return raw


def _force_review_flags(raw: str | None) -> tuple[str, ...]:
    if raw is None:
        return ()
    return tuple(part.strip() for part in raw.split(",") if part.strip())


@dataclass(frozen=True)
class EscalationPolicy:
    amount_threshold: float = 10000.0
    region: str = "us-east-1"
    extract_model_id: str = EXTRACT_MODEL_EXAMPLE
    summary_model_id: str = SUMMARY_MODEL_EXAMPLE
    understand_model_id: str = UNDERSTAND_MODEL_EXAMPLE
    guardrail_id: str | None = None
    kb_id: str | None = None
    force_review_flags: tuple[str, ...] = ()

    @classmethod
    def from_env(cls) -> EscalationPolicy:
        raw_threshold = _env("CLAIM_PROCESSOR_AMOUNT_THRESHOLD")
        return cls(
            amount_threshold=(
                float(raw_threshold) if raw_threshold is not None else 10000.0
            ),
            region=_env("CLAIM_PROCESSOR_REGION") or "us-east-1",
            extract_model_id=_env("CLAIM_PROCESSOR_EXTRACT_MODEL_ID")
            or EXTRACT_MODEL_EXAMPLE,
            summary_model_id=_env("CLAIM_PROCESSOR_SUMMARY_MODEL_ID")
            or SUMMARY_MODEL_EXAMPLE,
            understand_model_id=_env("CLAIM_PROCESSOR_UNDERSTAND_MODEL_ID")
            or UNDERSTAND_MODEL_EXAMPLE,
            guardrail_id=_env("CLAIM_PROCESSOR_GUARDRAIL_ID"),
            kb_id=_env("CLAIM_PROCESSOR_KB_ID"),
            force_review_flags=_force_review_flags(
                _env("CLAIM_PROCESSOR_FORCE_REVIEW_FLAGS")
            ),
        )
