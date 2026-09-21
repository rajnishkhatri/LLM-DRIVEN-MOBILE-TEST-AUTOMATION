from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.fake import FakeModelInvoker
from claim_processor.models import ValidationResult
from claim_processor.pipeline import ClaimPipeline
from claim_processor.prompts import PromptTemplateManager
from claim_processor.rag import PolicyRetriever
from claim_processor.store import LocalDocumentStore
from claim_processor.validator import ContentValidator

_TEXT_KEYS = (
    "claims/auto-fl-collision.txt",
    "claims/home-tx-water.txt",
    "claims/incomplete-claim.txt",
)
_IMAGE_KEY = "claims/auto-fl-photo.png"
_SPIKE_KEYS = _TEXT_KEYS + (_IMAGE_KEY,)


def _without_real_aws_gate():
    env = {k: v for k, v in os.environ.items() if k != "CLAIM_PROCESSOR_REAL_AWS"}
    return patch.dict(os.environ, env, clear=True)


def _fake_pipeline() -> ClaimPipeline:
    return ClaimPipeline(
        store=LocalDocumentStore(ROOT),
        invoker=FakeModelInvoker(),
        templates=PromptTemplateManager(),
        validator=ContentValidator(),
        retriever=PolicyRetriever(ROOT / "samples" / "policies"),
    )


class RealSpikeGateTests(unittest.TestCase):
    def test_real_spike_refuses_without_gate(self) -> None:
        from claim_processor.__main__ import main

        with _without_real_aws_gate():
            with self.assertRaises(SystemExit) as ctx:
                main(["--real", "--spike"])
        self.assertIn("CLAIM_PROCESSOR_REAL_AWS", str(ctx.exception))

    def test_injected_spike_covers_three_text_and_one_image(self) -> None:
        from claim_processor.__main__ import SPIKE_CLAIM_KEYS, run_real_spike

        self.assertEqual(tuple(SPIKE_CLAIM_KEYS), _SPIKE_KEYS)
        report = run_real_spike(
            _fake_pipeline(),
            "samples",
            gold_dir=ROOT / "samples" / "gold",
        )
        keys = [row["key"] for row in report["claims"]]
        self.assertEqual(keys, list(_SPIKE_KEYS))
        self.assertEqual(report["totals"]["count"], 4)
        self.assertGreaterEqual(report["totals"]["latency_seconds"], 0)
        for row in report["claims"]:
            self.assertTrue(row["extract_model_id"], msg=row["key"])
            self.assertTrue(row["summary_model_id"], msg=row["key"])
            self.assertIn("ungrounded", row)
            self.assertIn("citations", row)
            self.assertIn("pii_flags", row)
            self.assertIn("guardrail", row)
            self.assertIn("guardrail_intervened", row)
            self.assertIn("usage", row)
            self.assertIn("latency_seconds", row)
            self.assertIn("accepted", row)

        image = next(r for r in report["claims"] if r["key"] == _IMAGE_KEY)
        self.assertIsNotNone(image["understand_model_id"])
        self.assertEqual(image["amount_rel_error"], 0)

    def test_capture_records_guardrail_intervened(self) -> None:
        from claim_processor.__main__ import capture_claim
        from claim_processor.models import ProcessingResult

        result = ProcessingResult(
            extracted_info={"claim_amount": 1},
            summary="ok",
            citations=["auto-florida"],
            ungrounded=False,
            validation=ValidationResult(accepted=True, flags=["pii_ssn"]),
            extract_model_id="resolved-extract",
            summary_model_id="resolved-summary",
            prompt_versions={},
            usage={"extract": {"inputTokens": 10}},
            guardrail={"intervened": True, "actions": ["ANONYMIZE"]},
            understand_model_id="resolved-understand",
        )
        row = capture_claim(result, latency_seconds=0.5)
        self.assertTrue(row["guardrail_intervened"])
        self.assertEqual(row["pii_flags"], ["pii_ssn"])
        self.assertEqual(row["extract_model_id"], "resolved-extract")
        self.assertEqual(row["summary_model_id"], "resolved-summary")
        self.assertEqual(row["understand_model_id"], "resolved-understand")
        self.assertEqual(row["usage"], {"extract": {"inputTokens": 10}})
        self.assertEqual(row["latency_seconds"], 0.5)

    @unittest.skip(
        "env-gated: live 3-text + 1-image Bedrock spike "
        "(CLAIM_PROCESSOR_REAL_AWS=1); not run in this environment"
    )
    def test_live_spike_three_text_one_image(self) -> None:
        from claim_processor.__main__ import main

        main(["--real", "--spike"])


if __name__ == "__main__":
    unittest.main()
