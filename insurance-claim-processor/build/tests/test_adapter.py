"""R-03 — ModelAdapter normalizes Bedrock-family I/O + a typed outcome.

AC-L1 (bad shape → AdapterError, not KeyError), L2/L3 (one interface),
L4 (one call, no completions, resolved id, guardrail passthrough),
L5 (outcome enum: ok/throttled/timed_out/invalid/guardrail_intervened).
"""

from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, ReadTimeoutError
from botocore.stub import Stubber

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.adapter import (
    AdapterError,
    AdapterResult,
    BedrockConverseAdapter,
    CallOutcome,
)


def _converse_ok(text: str, *, stop_reason: str = "end_turn") -> dict:
    return {
        "output": {"message": {"role": "assistant", "content": [{"text": text}]}},
        "stopReason": stop_reason,
        "usage": {"inputTokens": 12, "outputTokens": 8, "totalTokens": 20},
        "metrics": {"latencyMs": 15},
    }


class _FakeClient:
    def __init__(self, *, exc: Exception | None = None, response: dict | None = None):
        self._exc = exc
        self._response = response

    def converse(self, **kwargs):
        if self._exc is not None:
            raise self._exc
        return self._response


def _stub_adapter(response: dict, model_id: str = "example.model"):
    client = boto3.client("bedrock-runtime", region_name="us-east-1")
    stub = Stubber(client)
    stub.add_response("converse", response, {
        "modelId": model_id,
        "messages": [{"role": "user", "content": [{"text": "hi"}]}],
        "inferenceConfig": {"maxTokens": 32},
    })
    return BedrockConverseAdapter(client, default_model_id=model_id), stub


class AdapterTests(unittest.TestCase):
    def test_ok_outcome_and_resolved_id(self) -> None:
        adapter, stub = _stub_adapter(_converse_ok("hello"))
        stub.activate()
        result = adapter.invoke("hi", model_id="example.model", max_tokens=32)
        stub.deactivate()
        self.assertIsInstance(result, AdapterResult)
        self.assertEqual(result.outcome, CallOutcome.OK)
        self.assertEqual(result.text, "hello")
        self.assertEqual(result.model_id, "example.model")

    def test_guardrail_intervened_outcome(self) -> None:
        adapter, stub = _stub_adapter(
            _converse_ok("redacted", stop_reason="guardrail_intervened")
        )
        stub.activate()
        result = adapter.invoke("hi", model_id="example.model", max_tokens=32)
        stub.deactivate()
        self.assertEqual(result.outcome, CallOutcome.GUARDRAIL_INTERVENED)

    def test_invalid_outcome_on_empty_text(self) -> None:
        adapter, stub = _stub_adapter(_converse_ok(""))
        stub.activate()
        result = adapter.invoke("hi", model_id="example.model", max_tokens=32)
        stub.deactivate()
        self.assertEqual(result.outcome, CallOutcome.INVALID)

    def test_throttled_outcome(self) -> None:
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        stub = Stubber(client)
        stub.add_client_error("converse", "ThrottlingException")
        adapter = BedrockConverseAdapter(client, default_model_id="m")
        stub.activate()
        result = adapter.invoke("hi", model_id="m", max_tokens=32)
        stub.deactivate()
        self.assertEqual(result.outcome, CallOutcome.THROTTLED)
        self.assertEqual(result.text, "")

    def test_timed_out_outcome(self) -> None:
        client = _FakeClient(exc=ReadTimeoutError(endpoint_url="https://bedrock"))
        adapter = BedrockConverseAdapter(client, default_model_id="m")
        result = adapter.invoke("hi", model_id="m", max_tokens=32)
        self.assertEqual(result.outcome, CallOutcome.TIMED_OUT)

    def test_bad_shape_raises_adapter_error_not_keyerror(self) -> None:
        client = _FakeClient(response={"stopReason": "end_turn"})  # no "output"
        adapter = BedrockConverseAdapter(client, default_model_id="m")
        with self.assertRaises(AdapterError):
            adapter.invoke("hi", model_id="m", max_tokens=32)

    def test_access_denied_is_reraised_not_swallowed(self) -> None:
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        stub = Stubber(client)
        stub.add_client_error("converse", "AccessDeniedException")
        adapter = BedrockConverseAdapter(client, default_model_id="m")
        stub.activate()
        with self.assertRaises(ClientError):
            adapter.invoke("hi", model_id="m", max_tokens=32)
        stub.deactivate()

    def test_one_call_no_completions_contract(self) -> None:
        source = inspect.getsource(BedrockConverseAdapter.invoke)
        self.assertNotIn("max_tokens_to_sample", source)
        self.assertNotIn('"completion"', source)


if __name__ == "__main__":
    unittest.main()
