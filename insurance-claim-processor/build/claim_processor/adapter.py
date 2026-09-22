"""Bedrock-family foundation-model adapter (ADR 0011).

One `ModelAdapter` interface normalizes request/response across Bedrock
families (Claude, Nova) and returns a typed per-call `CallOutcome` that the
breaker (ADR 0012), ensemble (ADR 0013), degradation (ADR 0014), and metrics
(ADR 0015) all consume — none of them ever sees a raw Bedrock response.

Preserves the frozen invariants (AC-L4): exactly one app-level call (the
wrapped `ModelInvoker` has no nested retry — C2), no legacy completions
contract (ADR 0001), `guardrailConfig` passthrough (ADR 0008), resolved id
recorded (ADR 0001). Cross-provider is out of scope — Bedrock only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from botocore.exceptions import ClientError, ConnectTimeoutError, ReadTimeoutError

from claim_processor.invoker import ModelInvoker
from claim_processor.models import EXTRACT_MODEL_EXAMPLE

_THROTTLE_CODES = frozenset(
    {
        "ThrottlingException",
        "TooManyRequestsException",
        "ProvisionedThroughputExceededException",
    }
)


class CallOutcome(str, Enum):
    OK = "ok"
    THROTTLED = "throttled"
    TIMED_OUT = "timed_out"
    INVALID = "invalid"
    GUARDRAIL_INTERVENED = "guardrail_intervened"


class AdapterError(Exception):
    """Model returned a response shape the adapter does not recognize (AC-L1)."""


class ThrottlingException(RuntimeError):
    """A throttled model call, re-raised for the orchestrator's Retry tier.

    The class NAME is load-bearing: a Python Lambda surfaces it as the error
    string the ASL `Retry.ErrorEquals: ["ThrottlingException"]` matches, so
    Step Functions owns the backoff (C2 — no app-level retry). Swallowing the
    throttle instead silently degraded the claim (review #7).
    """


def _empty_guardrail() -> dict[str, Any]:
    return {"intervened": False, "actions": []}


@dataclass
class AdapterResult:
    text: str
    model_id: str
    outcome: CallOutcome
    usage: dict[str, Any] = field(default_factory=dict)
    stop_reason: str | None = None
    guardrail: dict[str, Any] = field(default_factory=_empty_guardrail)


class ModelAdapter(Protocol):
    def invoke(
        self,
        prompt: str,
        *,
        model_id: str | None = None,
        system: str | None = None,
        max_tokens: int = 1000,
        content: list[dict] | None = None,
        guardrail_config: dict | None = None,
    ) -> AdapterResult: ...


class BedrockConverseAdapter:
    """Claude/Nova implementation of `ModelAdapter` over Bedrock Converse."""

    def __init__(self, client: Any, default_model_id: str = EXTRACT_MODEL_EXAMPLE):
        self._invoker = ModelInvoker(client, default_model_id=default_model_id)
        self.default_model_id = default_model_id

    @classmethod
    def from_invoker(cls, invoker: Any, default_model_id: str = EXTRACT_MODEL_EXAMPLE) -> "BedrockConverseAdapter":
        """Wrap an existing invoker-like (`.converse(prompt, model_id=...)`).

        The pipeline is injected an invoker (real `ModelInvoker` or the
        `FakeModelInvoker`), not a raw client — reuse it rather than build a new
        client wrapper.
        """
        self = cls.__new__(cls)
        self._invoker = invoker
        self.default_model_id = default_model_id
        return self

    def invoke(
        self,
        prompt: str,
        *,
        model_id: str | None = None,
        system: str | None = None,
        max_tokens: int = 1000,
        content: list[dict] | None = None,
        guardrail_config: dict | None = None,
    ) -> AdapterResult:
        resolved = model_id or self.default_model_id
        try:
            raw = self._invoker.converse(
                prompt,
                model_id=model_id,
                system=system,
                max_tokens=max_tokens,
                content=content,
                guardrail_config=guardrail_config,
            )
        except (ReadTimeoutError, ConnectTimeoutError):
            # C7 deadline hit — a degradation signal, not a crash (AC-L5).
            return AdapterResult(text="", model_id=resolved, outcome=CallOutcome.TIMED_OUT)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in _THROTTLE_CODES:
                return AdapterResult(
                    text="", model_id=resolved, outcome=CallOutcome.THROTTLED
                )
            # AccessDenied / ValidationException are config bugs, not model
            # degradation — surface them, do not mask (A2/G9).
            raise
        except KeyError as exc:
            # ModelInvoker.converse subscripts the response shape; a KeyError
            # here means an unrecognized Converse envelope (AC-L1).
            raise AdapterError(
                f"unrecognized Converse response shape: missing {exc}"
            ) from exc

        guardrail = raw.get("guardrail") or _empty_guardrail()
        if guardrail.get("intervened"):
            outcome = CallOutcome.GUARDRAIL_INTERVENED
        elif not raw.get("text"):
            outcome = CallOutcome.INVALID
        else:
            outcome = CallOutcome.OK
        return AdapterResult(
            text=raw.get("text", ""),
            model_id=raw.get("model_id") or resolved,
            outcome=outcome,
            usage=raw.get("usage") or {},
            stop_reason=raw.get("stop_reason"),
            guardrail=guardrail,
        )
