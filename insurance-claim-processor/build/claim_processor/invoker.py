from __future__ import annotations

from typing import Any

from botocore.config import Config

from claim_processor.models import EXTRACT_MODEL_EXAMPLE


def bedrock_client_config(region: str = "us-east-1") -> Config:
    """C7 timeouts + C2 adaptive retries. One retry layer — do not wrap this."""
    return Config(
        region_name=region,
        retries={"mode": "adaptive", "max_attempts": 5},
        connect_timeout=10,
        read_timeout=300,
        tcp_keepalive=True,
    )


class ModelInvoker:
    """Converse envelope — Invoke Foundation Model component.

    Accepts an injected bedrock-runtime client so Stubber can bind.
    Never uses the legacy completions contract (prompt / max_tokens_to_sample /
    response['completion']).
    """

    def __init__(self, bedrock_runtime_client: Any, default_model_id: str = EXTRACT_MODEL_EXAMPLE):
        self._client = bedrock_runtime_client
        self.default_model_id = default_model_id

    def converse(
        self,
        prompt: str,
        *,
        model_id: str | None = None,
        system: str | None = None,
        max_tokens: int = 1000,
        content: list[dict] | None = None,
        guardrail_config: dict | None = None,
    ) -> dict[str, Any]:
        model = model_id or self.default_model_id
        body = content if content is not None else [{"text": prompt}]
        kwargs: dict[str, Any] = {
            "modelId": model,
            "messages": [{"role": "user", "content": body}],
            "inferenceConfig": {"maxTokens": max_tokens},
        }
        if system:
            kwargs["system"] = [{"text": system}]
        if guardrail_config is not None:
            kwargs["guardrailConfig"] = guardrail_config
        resp = self._client.converse(**kwargs)
        message = resp["output"]["message"]
        text = "".join(block["text"] for block in message["content"] if "text" in block)
        return {
            "text": text,
            "model_id": model,
            "stop_reason": resp.get("stopReason"),
            "usage": resp.get("usage") or {},
            "guardrail": {
                "intervened": resp.get("stopReason") == "guardrail_intervened",
                "actions": [],
            },
        }
