from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

import boto3
from botocore.stub import Stubber

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.invoker import ModelInvoker, bedrock_client_config


def _converse_ok(text: str, *, stop_reason: str = "end_turn") -> dict:
    return {
        "output": {"message": {"role": "assistant", "content": [{"text": text}]}},
        "stopReason": stop_reason,
        "usage": {"inputTokens": 12, "outputTokens": 8, "totalTokens": 20},
        "metrics": {"latencyMs": 15},
    }


PNG_BLOCK = {
    "image": {
        "format": "png",
        "source": {"bytes": b"\x89PNG\r\n\x1a\n" + b"\x00" * 8},
    }
}


class InvokerStubberTests(unittest.TestCase):
    def test_converse_shape_not_legacy_completion(self) -> None:
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        stubber = Stubber(client)
        expected = {
            "modelId": "example.model",
            "messages": [{"role": "user", "content": [{"text": "hi"}]}],
            "inferenceConfig": {"maxTokens": 32},
        }
        stubber.add_response("converse", _converse_ok("ok"), expected)
        stubber.activate()
        invoker = ModelInvoker(client, default_model_id="example.model")
        out = invoker.converse("hi", model_id="example.model", max_tokens=32)
        stubber.deactivate()
        self.assertEqual(out["text"], "ok")
        self.assertNotIn("completion", out)
        self.assertNotIn("prompt", expected)

    def test_client_config_has_timeouts_and_adaptive_retries(self) -> None:
        cfg = bedrock_client_config()
        self.assertEqual(cfg.connect_timeout, 10)
        self.assertEqual(cfg.read_timeout, 300)
        self.assertEqual(cfg.retries["mode"], "adaptive")
        self.assertEqual(cfg.retries["max_attempts"], 5)

    def test_content_blocks_replace_prompt_as_message_body(self) -> None:
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        stubber = Stubber(client)
        expected = {
            "modelId": "example.vision",
            "messages": [{"role": "user", "content": [PNG_BLOCK]}],
            "inferenceConfig": {"maxTokens": 32},
        }
        stubber.add_response("converse", _converse_ok("ok"), expected)
        stubber.activate()
        invoker = ModelInvoker(client, default_model_id="example.vision")
        out = invoker.converse(
            "IGNORED-PROMPT",
            model_id="example.vision",
            max_tokens=32,
            content=[PNG_BLOCK],
        )
        stubber.deactivate()
        self.assertEqual(out["text"], "ok")
        self.assertEqual(out["model_id"], "example.vision")
        self.assertNotIn("completion", out)

    def test_guardrail_config_passed_as_camel_case_wire_key(self) -> None:
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        stubber = Stubber(client)
        guardrail_config = {
            "guardrailIdentifier": "gr-test",
            "guardrailVersion": "1",
        }
        expected = {
            "modelId": "example.model",
            "messages": [{"role": "user", "content": [{"text": "hi"}]}],
            "inferenceConfig": {"maxTokens": 32},
            "guardrailConfig": guardrail_config,
        }
        stubber.add_response("converse", _converse_ok("ok"), expected)
        stubber.activate()
        invoker = ModelInvoker(client, default_model_id="example.model")
        out = invoker.converse(
            "hi",
            model_id="example.model",
            max_tokens=32,
            guardrail_config=guardrail_config,
        )
        stubber.deactivate()
        self.assertEqual(out["text"], "ok")
        self.assertEqual(
            out["guardrail"],
            {"intervened": False, "actions": []},
        )

    def test_guardrail_absent_when_config_is_none(self) -> None:
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        stubber = Stubber(client)
        expected = {
            "modelId": "example.model",
            "messages": [{"role": "user", "content": [{"text": "hi"}]}],
            "inferenceConfig": {"maxTokens": 32},
        }
        stubber.add_response("converse", _converse_ok("ok"), expected)
        stubber.activate()
        invoker = ModelInvoker(client, default_model_id="example.model")
        out = invoker.converse("hi", model_id="example.model", max_tokens=32)
        stubber.deactivate()
        self.assertNotIn("guardrailConfig", expected)
        self.assertEqual(
            out["guardrail"],
            {"intervened": False, "actions": []},
        )

    def test_guardrail_intervened_from_stop_reason(self) -> None:
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        stubber = Stubber(client)
        expected = {
            "modelId": "example.model",
            "messages": [{"role": "user", "content": [{"text": "hi"}]}],
            "inferenceConfig": {"maxTokens": 32},
            "guardrailConfig": {"guardrailIdentifier": "gr-test", "guardrailVersion": "1"},
        }
        stubber.add_response(
            "converse",
            _converse_ok("redacted", stop_reason="guardrail_intervened"),
            expected,
        )
        stubber.activate()
        invoker = ModelInvoker(client, default_model_id="example.model")
        out = invoker.converse(
            "hi",
            model_id="example.model",
            max_tokens=32,
            guardrail_config={
                "guardrailIdentifier": "gr-test",
                "guardrailVersion": "1",
            },
        )
        stubber.deactivate()
        self.assertEqual(out["guardrail"]["intervened"], True)
        self.assertEqual(out["guardrail"]["actions"], [])
        self.assertEqual(out["model_id"], "example.model")

    def test_resolved_model_id_is_the_id_sent(self) -> None:
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        stubber = Stubber(client)
        expected = {
            "modelId": "us.anthropic.claude-resolved",
            "messages": [{"role": "user", "content": [{"text": "hi"}]}],
            "inferenceConfig": {"maxTokens": 16},
        }
        stubber.add_response("converse", _converse_ok("ok"), expected)
        stubber.activate()
        invoker = ModelInvoker(client, default_model_id="default.unused")
        out = invoker.converse(
            "hi",
            model_id="us.anthropic.claude-resolved",
            max_tokens=16,
        )
        stubber.deactivate()
        self.assertEqual(out["model_id"], "us.anthropic.claude-resolved")

    def test_no_application_retry_loop_around_converse(self) -> None:
        source = inspect.getsource(ModelInvoker.converse)
        self.assertEqual(source.count("self._client.converse"), 1)
        self.assertNotIn("max_tokens_to_sample", source)
        self.assertNotIn("completion", source)


if __name__ == "__main__":
    unittest.main()
