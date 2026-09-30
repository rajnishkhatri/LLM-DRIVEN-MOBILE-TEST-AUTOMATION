"""ModelPort implementations — WORKER C. ADR 0002.

OfflineModel: deterministic, temperature-0, recorded responses (default for the
demo and all gates). BedrockModelAdapter: behind a config toggle, lazy boto3
import, with a `guardrail_id` config slot passed through when live (HANDOVER §9
B1 — the one managed-service absorption). Never exercised by the gates.

The model is a thin, honest seam: offline it echoes the grounded prompt that
synthesis already composed from retrieval/fixtures, so numbers are never
fabricated here. temperature-0 semantics = deterministic output for a given
input.
"""
from __future__ import annotations

from ..domain.types import ModelOutcome, ModelRequest, ModelResponse

MODEL_VERSION: str = "offline-deterministic-v1"
PROMPT_VERSION: str = "synthesis-v1"


class OfflineModel:
    """Deterministic ModelPort. Resolved model id lands in provenance.

    Offline the model does not invent content: it returns, verbatim and
    deterministically, the grounded prompt synthesis handed it. That keeps the
    "numbers come from the fixture, never the model" invariant structural.
    """

    model_version = MODEL_VERSION

    def generate(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            outcome=ModelOutcome.OK,
            text=request.prompt,
            model_version=MODEL_VERSION,
            prompt_version=request.prompt_version,
        )


class BedrockModelAdapter:
    """Live ModelPort (ADR 0002). boto3 imported lazily, only here, only when
    generate() is called with the live toggle on. NOT used offline — the gates
    never exercise this path, but it must stay import-clean.

    The `guardrail_id` config slot is the single managed-service absorption
    (HANDOVER §9, B1): when set it is threaded into the Converse call so Bedrock
    Guardrails run in front of the model; a guardrail intervention surfaces as a
    typed outcome, never as a raw provider response.
    """

    def __init__(self, model_id: str, guardrail_id: str | None = None):
        self.model_id = model_id
        self.guardrail_id = guardrail_id  # the B1 one-slot absorption

    @property
    def model_version(self) -> str:
        return self.model_id

    def generate(self, request: ModelRequest) -> ModelResponse:
        # Lazy, method-local import: boto3 is optional and never imported at
        # module top-level, so the offline gates load this module with no AWS
        # dependency present (ground rule §2).
        import boto3  # noqa: PLC0415  (intentional lazy import)

        client = boto3.client("bedrock-runtime")
        kwargs: dict = {
            "modelId": self.model_id,
            "messages": [
                {"role": "user", "content": [{"text": request.prompt}]}
            ],
            "inferenceConfig": {"temperature": request.temperature},
        }
        if self.guardrail_id:
            # Guardrails run in front of the model; guardrailIdentifier is the
            # passed-through config slot (HANDOVER §9, B1).
            kwargs["guardrailConfig"] = {
                "guardrailIdentifier": self.guardrail_id,
                "guardrailVersion": "DRAFT",
            }

        raw = client.converse(**kwargs)

        stop_reason = raw.get("stopReason")
        if stop_reason == "guardrail_intervened":
            outcome = ModelOutcome.GUARDRAIL_INTERVENED
            text = ""
        else:
            outcome = ModelOutcome.OK
            text = raw["output"]["message"]["content"][0]["text"]

        return ModelResponse(
            outcome=outcome,
            text=text,
            model_version=self.model_id,
            prompt_version=request.prompt_version,
        )
