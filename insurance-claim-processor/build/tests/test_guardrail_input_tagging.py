"""F14 — AC-A5a: WHERE Guardrails are enabled, the guarded input of a text
claim is ONLY claim-derived text (`guardContent`); our instructions and policy
excerpts travel as plain `text` (live-v1 finding, 2026-09-23).

With no `guardContent` block, the guardrail evaluates the whole user turn, and
its prompt-attack filter (strength HIGH) blocked our own summary instructions
(PROMPT_ATTACK, confidence LOW): every clean claim routed to human review.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

import boto3
from botocore.stub import Stubber

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor import handler
from claim_processor.config import EscalationPolicy
from claim_processor.fake import FakeModelInvoker
from claim_processor.invoker import ModelInvoker
from claim_processor.pipeline import ClaimPipeline
from claim_processor.prompts import PromptTemplateManager
from claim_processor.rag import PolicyRetriever
from claim_processor.store import LocalDocumentStore
from claim_processor.validator import ContentValidator

_BUCKET = "work"
_TEXT_KEY = "claims/auto-fl-clean.txt"
_IMAGE_KEY = "claims/auto-fl-photo.png"
_CLAIMANT = "Maria Elena Ruiz"
_GUARDRAIL = {"guardrailIdentifier": "gr-test", "guardrailVersion": "DRAFT"}


class _RecordingInvoker(FakeModelInvoker):
    def __init__(self) -> None:
        super().__init__()
        self.requests: list[dict[str, Any]] = []

    def converse(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        self.requests.append({"prompt": prompt, **kwargs})
        return super().converse(prompt, **kwargs)


def _guarded(blocks: list[dict] | None) -> list[str]:
    return [b["guardContent"]["text"]["text"] for b in blocks or [] if "guardContent" in b]


def _plain(blocks: list[dict] | None) -> str:
    return "".join(b["text"] for b in blocks or [] if "text" in b)


def _joined(blocks: list[dict]) -> str:
    return "".join(
        b["text"] if "text" in b else b["guardContent"]["text"]["text"] for b in blocks
    )


class PipelineInputTaggingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        for key in (_TEXT_KEY, _IMAGE_KEY):
            target = self.tmp / _BUCKET / key
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / "samples" / key, target)
        self.document = (ROOT / "samples" / _TEXT_KEY).read_text(encoding="utf-8")
        self.invoker = _RecordingInvoker()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _pipeline(self, guardrail_id: str | None) -> ClaimPipeline:
        return ClaimPipeline(
            store=LocalDocumentStore(self.tmp),
            invoker=self.invoker,
            templates=PromptTemplateManager(),
            validator=ContentValidator(),
            retriever=PolicyRetriever(ROOT / "samples" / "policies"),
            policy=EscalationPolicy(guardrail_id=guardrail_id),
        )

    def test_extract_guards_the_claim_document_only(self) -> None:
        self._pipeline("gr-test").understand_extract(_BUCKET, _TEXT_KEY)
        content = self.invoker.requests[0]["content"]
        self.assertEqual(_guarded(content), [self.document])
        self.assertIn("Extract the following fields", _plain(content))
        self.assertNotIn(_CLAIMANT, _plain(content))

    def test_summary_guards_the_extracted_fields_not_the_policy_excerpts(self) -> None:
        pipe = self._pipeline("gr-test")
        extracted = pipe.understand_extract(_BUCKET, _TEXT_KEY)
        self.invoker.requests.clear()
        out = pipe.retrieve_summarize(extracted["extracted_info"], extracted["document_text"])
        request = self.invoker.requests[0]
        guarded = _guarded(request["content"])
        self.assertEqual(len(guarded), 1)
        self.assertEqual(json.loads(guarded[0]), extracted["extracted_info"])
        self.assertTrue(out["citations"], "the FL auto claim must retrieve excerpts")
        for chunk_id in out["citations"]:
            self.assertIn(chunk_id, _plain(request["content"]))
            self.assertNotIn(chunk_id, guarded[0])
        self.assertIn("do not invent one", _plain(request["content"]))
        self.assertNotIn(_CLAIMANT, _plain(request["content"]))
        self.assertEqual(request["guardrail_config"], _GUARDRAIL)

    def test_handler_summary_step_is_tagged(self) -> None:
        pipe = self._pipeline("gr-test")
        event = handler.understand_extract({"bucket": _BUCKET, "key": _TEXT_KEY}, pipeline=pipe)
        self.invoker.requests.clear()
        handler.retrieve_summarize(event, pipeline=pipe)
        self.assertEqual(len(_guarded(self.invoker.requests[0]["content"])), 1)

    def test_tagging_does_not_change_what_the_model_reads(self) -> None:
        self._pipeline("gr-test").process(_BUCKET, _TEXT_KEY)
        self.assertEqual(len(self.invoker.requests), 2)  # extract + summary
        for request in self.invoker.requests:
            self.assertEqual(_joined(request["content"]).strip(), request["prompt"].strip())

    def test_no_guardrail_sends_the_plain_v1_request(self) -> None:
        self._pipeline(None).process(_BUCKET, _TEXT_KEY)
        self.assertTrue(self.invoker.requests)
        for request in self.invoker.requests:
            self.assertIsNone(request.get("content"))

    def test_image_claim_keeps_whole_message_evaluation(self) -> None:
        # Tagging only the text would take the image (the claimant content)
        # out of the guardrail's view.
        self._pipeline("gr-test").understand_extract(_BUCKET, _IMAGE_KEY)
        content = self.invoker.requests[0]["content"]
        self.assertEqual(_guarded(content), [])
        self.assertTrue(any("image" in block for block in content))


class TaggedRequestShapeTests(unittest.TestCase):
    def test_tagged_request_passes_botocore_validation(self) -> None:
        blocks = PromptTemplateManager().get_content_blocks(
            "generate_summary",
            extracted_info='{"claimant_name": "A. Nguyen"}',
            policy_context="[auto-florida#1] (auto-florida.md)\nCollision coverage applies.",
        )
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        stubber = Stubber(client)
        stubber.add_response(
            "converse",
            {
                "output": {"message": {"role": "assistant", "content": [{"text": "ok"}]}},
                "stopReason": "end_turn",
                "usage": {"inputTokens": 1, "outputTokens": 1, "totalTokens": 2},
                "metrics": {"latencyMs": 1},
            },
            {
                "modelId": "example.model",
                "messages": [{"role": "user", "content": blocks}],
                "inferenceConfig": {"maxTokens": 32},
                "guardrailConfig": _GUARDRAIL,
            },
        )
        with stubber:
            out = ModelInvoker(client).converse(
                "unused when content is given",
                model_id="example.model",
                max_tokens=32,
                content=blocks,
                guardrail_config=_GUARDRAIL,
            )
        self.assertEqual(out["text"], "ok")


if __name__ == "__main__":
    unittest.main()
