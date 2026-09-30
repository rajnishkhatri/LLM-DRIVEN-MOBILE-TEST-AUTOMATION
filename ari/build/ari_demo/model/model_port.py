"""ModelPort implementations — WORKER C (stub). ADR 0002.

OfflineModel: deterministic, temperature-0, recorded responses (default for the
demo and all gates). BedrockModelAdapter: behind a config toggle, lazy boto3
import, with a `guardrail_id` config slot passed through when live (HANDOVER §9
B1 — the one managed-service absorption). Never exercised by the gates.
"""
from __future__ import annotations

from ..domain.types import ModelRequest, ModelResponse

MODEL_VERSION: str = "offline-deterministic-v1"
PROMPT_VERSION: str = "synthesis-v1"


class OfflineModel:
    """Deterministic ModelPort. Resolved model id lands in provenance."""

    model_version = MODEL_VERSION

    def generate(self, request: ModelRequest) -> ModelResponse:
        raise NotImplementedError("worker C: deterministic recorded response")


class BedrockModelAdapter:
    """Live ModelPort (ADR 0002). boto3 imported lazily, only here, only when
    generate() is called with the live toggle on. NOT used offline."""

    def __init__(self, model_id: str, guardrail_id: str | None = None):
        self.model_id = model_id
        self.guardrail_id = guardrail_id  # the B1 one-slot absorption

    def generate(self, request: ModelRequest) -> ModelResponse:
        raise NotImplementedError(
            "worker C: lazy boto3 Converse; pass guardrail_id when set"
        )
