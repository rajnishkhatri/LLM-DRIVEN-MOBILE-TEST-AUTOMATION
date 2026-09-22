from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

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
    # Model-resilience config plane (ADR 0010). Bootstrap defaults; AppConfig
    # overrides at runtime via `from_config`.
    ensemble_models: tuple[str, ...] = ()
    degradation_tiers: tuple[str, ...] = ()
    flags: dict[str, Any] = field(default_factory=dict)

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
            ensemble_models=_force_review_flags(
                _env("CLAIM_PROCESSOR_ENSEMBLE_MODELS")
            ),
            degradation_tiers=_force_review_flags(
                _env("CLAIM_PROCESSOR_DEGRADATION_TIERS")
            ),
        )

    @classmethod
    def from_config(
        cls,
        config: dict[str, Any],
        *,
        base: EscalationPolicy | None = None,
    ) -> EscalationPolicy:
        """Build a resolved policy from an AppConfig document (ADR 0010).

        Missing keys fall back to `base` (the env/default bootstrap), so a
        partial or unreachable config degrades safely (AC-K2/K3).
        """
        base = base or cls()
        return cls(
            amount_threshold=float(
                config.get("amount_threshold", base.amount_threshold)
            ),
            region=config.get("region", base.region),
            extract_model_id=config.get("extract_model_id", base.extract_model_id),
            summary_model_id=config.get("summary_model_id", base.summary_model_id),
            understand_model_id=config.get(
                "understand_model_id", base.understand_model_id
            ),
            guardrail_id=config.get("guardrail_id", base.guardrail_id),
            kb_id=config.get("kb_id", base.kb_id),
            force_review_flags=tuple(
                config.get("force_review_flags", base.force_review_flags)
            ),
            ensemble_models=tuple(config.get("ensemble_models", base.ensemble_models)),
            degradation_tiers=tuple(
                config.get("degradation_tiers", base.degradation_tiers)
            ),
            flags=dict(config.get("flags", base.flags)),
        )
