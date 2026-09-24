"""D0-b — AC-A5: WHERE Guardrails are enabled, EVERY Converse call carries
`guardrailConfig` (live-v1 defect, 2026-09-23).

The extract path passed it, but the summary call in
`ClaimPipeline.retrieve_summarize` did not, so the live summary output was
never guardrail-masked. These tests record every `converse` call on both the
CLI (`process`) path and the Step Functions handler path.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor import handler
from claim_processor.config import EscalationPolicy
from claim_processor.fake import FakeModelInvoker
from claim_processor.pipeline import ClaimPipeline
from claim_processor.prompts import PromptTemplateManager
from claim_processor.rag import PolicyRetriever
from claim_processor.store import LocalDocumentStore
from claim_processor.validator import ContentValidator

_BUCKET = "work"
_KEY = "claims/auto-fl-clean.txt"
_GUARDRAIL = {"guardrailIdentifier": "gr-test", "guardrailVersion": "DRAFT"}


class _RecordingInvoker(FakeModelInvoker):
    def __init__(self) -> None:
        super().__init__()
        self.guardrail_configs: list[Any] = []

    def converse(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        self.guardrail_configs.append(kwargs.get("guardrail_config"))
        return super().converse(prompt, **kwargs)


class GuardrailOnEveryCallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        target = self.tmp / _BUCKET / _KEY
        target.parent.mkdir(parents=True)
        shutil.copy(ROOT / "samples" / "claims" / "auto-fl-clean.txt", target)
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

    def test_process_path_sends_guardrail_on_extract_and_summary(self) -> None:
        self._pipeline("gr-test").process(_BUCKET, _KEY)
        self.assertGreaterEqual(len(self.invoker.guardrail_configs), 2)  # extract + summary
        self.assertEqual(self.invoker.guardrail_configs, [_GUARDRAIL] * len(self.invoker.guardrail_configs))

    def test_handler_summary_step_sends_guardrail(self) -> None:
        pipe = self._pipeline("gr-test")
        event = handler.understand_extract({"bucket": _BUCKET, "key": _KEY}, pipeline=pipe)
        self.invoker.guardrail_configs.clear()
        handler.retrieve_summarize(event, pipeline=pipe)
        self.assertEqual(self.invoker.guardrail_configs, [_GUARDRAIL])

    def test_no_guardrail_configured_sends_none(self) -> None:
        self._pipeline(None).process(_BUCKET, _KEY)
        self.assertTrue(self.invoker.guardrail_configs)
        self.assertTrue(all(c is None for c in self.invoker.guardrail_configs))


if __name__ == "__main__":
    unittest.main()
