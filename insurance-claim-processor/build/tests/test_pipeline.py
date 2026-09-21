from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.config import EscalationPolicy
from claim_processor.fake import FakeModelInvoker
from claim_processor.models import ProcessingResult, UNDERSTAND_MODEL_EXAMPLE
from claim_processor.pipeline import ClaimPipeline, result_key_for
from claim_processor.prompts import PromptTemplateManager
from claim_processor.rag import PolicyRetriever
from claim_processor.review import apply_decision
from claim_processor.store import LocalDocumentStore, get_pending_review, pending_review_key
from claim_processor.validator import ContentValidator

_PROVENANCE_KEYS = (
    "extracted_info",
    "summary",
    "citations",
    "ungrounded",
    "validation",
    "route",
    "review",
    "guardrail",
    "extract_model_id",
    "summary_model_id",
    "prompt_versions",
    "usage",
    "sfn_execution_arn",
)


class PipelineFakeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = ROOT
        self.pipeline = ClaimPipeline(
            store=LocalDocumentStore(self.root),
            invoker=FakeModelInvoker(),
            templates=PromptTemplateManager(),
            validator=ContentValidator(),
            retriever=PolicyRetriever(self.root / "samples" / "policies"),
        )

    def test_auto_claim_is_grounded(self) -> None:
        result = self.pipeline.process("samples", "claims/auto-fl-collision.txt")
        self.assertFalse(result.ungrounded)
        self.assertIn("auto-florida", result.citations)
        self.assertTrue(result.validation.accepted)
        self.assertEqual(result.extracted_info["claimant_name"], "Maria Elena Ruiz")
        self.assertEqual(result.extracted_info["claim_amount"], 4820.5)

    def test_home_claim_does_not_pull_florida_auto(self) -> None:
        result = self.pipeline.process("samples", "claims/home-tx-water.txt")
        self.assertEqual(result.citations, ["homeowners-texas"])
        self.assertNotIn("auto-florida", result.citations)

    def test_incomplete_claim_flags_empty_fields(self) -> None:
        result = self.pipeline.process("samples", "claims/incomplete-claim.txt")
        self.assertTrue(any(f.startswith("empty_fields:") for f in result.validation.flags))
        self.assertTrue(result.ungrounded)
        self.assertEqual(result.citations, [])

    def test_idempotent_overwrite(self) -> None:
        self.pipeline.process("samples", "claims/home-tx-water.txt")
        self.pipeline.process("samples", "claims/home-tx-water.txt")
        path = self.root / "samples" / pending_review_key("claims/home-tx-water.txt")
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["extracted_info"]["claimant_name"], "James K. Patel")
        self.assertIn("homeowners-texas", payload["citations"])
        self.assertEqual(payload["route"], "human_review")


class PipelineHubTests(unittest.TestCase):
    """T-09: step units, route+record, pending vs results, idempotent put."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        claims = self.root / "work" / "claims"
        claims.mkdir(parents=True)
        src = ROOT / "samples" / "claims"
        for name in (
            "auto-fl-collision.txt",
            "home-tx-water.txt",
            "incomplete-claim.txt",
        ):
            shutil.copy(src / name, claims / name)
        self.store = LocalDocumentStore(self.root)
        self.pipeline = ClaimPipeline(
            store=self.store,
            invoker=FakeModelInvoker(),
            templates=PromptTemplateManager(),
            validator=ContentValidator(),
            retriever=PolicyRetriever(ROOT / "samples" / "policies"),
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _results_path(self, key: str) -> Path:
        return self.root / "work" / result_key_for(key)

    def _pending_path(self, key: str) -> Path:
        return self.root / "work" / pending_review_key(key)

    def test_auto_path_records_results_with_provenance(self) -> None:
        result = self.pipeline.process("work", "claims/auto-fl-collision.txt")
        self.assertEqual(result.route, "auto_approve")
        self.assertTrue(result.citations or result.ungrounded)
        path = self._results_path("claims/auto-fl-collision.txt")
        self.assertTrue(path.is_file())
        payload = json.loads(path.read_text(encoding="utf-8"))
        for key in _PROVENANCE_KEYS:
            self.assertIn(key, payload)
        self.assertEqual(payload["route"], "auto_approve")
        self.assertEqual(payload["claim_key"], "claims/auto-fl-collision.txt")
        self.assertEqual(payload["validation"]["accepted"], True)
        self.assertFalse(self._pending_path("claims/auto-fl-collision.txt").exists())

    def test_flagged_claim_writes_pending_review_not_results(self) -> None:
        result = self.pipeline.process("work", "claims/incomplete-claim.txt")
        self.assertEqual(result.route, "human_review")
        self.assertTrue(
            result.ungrounded
            or any(f.startswith("empty_fields:") for f in result.validation.flags)
        )
        pending_path = self._pending_path("claims/incomplete-claim.txt")
        self.assertTrue(pending_path.is_file())
        payload = json.loads(pending_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["route"], "human_review")
        self.assertIn("extracted_info", payload)
        self.assertFalse(self._results_path("claims/incomplete-claim.txt").exists())

    def test_amount_over_threshold_routes_to_pending(self) -> None:
        result = self.pipeline.process("work", "claims/home-tx-water.txt")
        self.assertEqual(result.route, "human_review")
        self.assertTrue(self._pending_path("claims/home-tx-water.txt").is_file())
        self.assertFalse(self._results_path("claims/home-tx-water.txt").exists())

    def test_duplicate_key_overwrites_one_result_object(self) -> None:
        key = "claims/auto-fl-collision.txt"
        self.pipeline.process("work", key)
        self.pipeline.process("work", key)
        path = self._results_path(key)
        self.assertTrue(path.is_file())
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["extracted_info"]["claimant_name"], "Maria Elena Ruiz")
        self.assertEqual(payload["route"], "auto_approve")
        siblings = list(path.parent.glob("**/*"))
        json_files = [p for p in siblings if p.is_file() and p.suffix == ".json"]
        self.assertEqual(len(json_files), 1)

    def test_duplicate_flagged_key_overwrites_one_pending_object(self) -> None:
        key = "claims/incomplete-claim.txt"
        self.pipeline.process("work", key)
        self.pipeline.process("work", key)
        path = self._pending_path(key)
        self.assertTrue(path.is_file())
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["route"], "human_review")
        self.assertFalse(self._results_path(key).exists())

    def test_record_after_human_approve_writes_results(self) -> None:
        key = "claims/incomplete-claim.txt"
        result = self.pipeline.process("work", key)
        self.assertEqual(result.route, "human_review")
        pending = get_pending_review(self.store, "work", key)
        decided = apply_decision(
            pending,
            decision="approve",
            reviewer_id="examiner-1",
            timestamp="2026-09-21T12:00:00Z",
        )
        self.pipeline.record("work", key, decided)
        payload = json.loads(self._results_path(key).read_text(encoding="utf-8"))
        self.assertEqual(payload["review"]["decision"], "approve")
        self.assertEqual(payload["review"]["reviewer_id"], "examiner-1")
        self.assertEqual(payload["route"], "human_review")
        self.assertNotEqual(payload["route"], "auto_approve")

    def test_record_after_correct_writes_final_values_without_resummarize(self) -> None:
        key = "claims/incomplete-claim.txt"
        result = self.pipeline.process("work", key)
        original_summary = result.summary
        pending = get_pending_review(self.store, "work", key)
        decided = apply_decision(
            pending,
            decision="correct",
            reviewer_id="examiner-2",
            timestamp="2026-09-21T13:00:00Z",
            corrections={"policy_number": "POL-FIXED"},
        )
        self.pipeline.record("work", key, decided)
        payload = json.loads(self._results_path(key).read_text(encoding="utf-8"))
        self.assertEqual(payload["extracted_info"]["policy_number"], "POL-FIXED")
        self.assertEqual(payload["summary"], original_summary)
        self.assertEqual(payload["review"]["decision"], "correct")
        self.assertEqual(
            payload["review"]["field_changes"],
            [{"field": "policy_number", "from": None, "to": "POL-FIXED"}],
        )

    def test_injected_policy_threshold_changes_route(self) -> None:
        tight = ClaimPipeline(
            store=self.store,
            invoker=FakeModelInvoker(),
            templates=PromptTemplateManager(),
            validator=ContentValidator(),
            retriever=PolicyRetriever(ROOT / "samples" / "policies"),
            policy=EscalationPolicy(amount_threshold=1000.0),
        )
        result = tight.process("work", "claims/auto-fl-collision.txt")
        self.assertEqual(result.route, "human_review")
        self.assertTrue(self._pending_path("claims/auto-fl-collision.txt").is_file())
        self.assertFalse(self._results_path("claims/auto-fl-collision.txt").exists())

    def test_record_refuses_unclean_auto_approve(self) -> None:
        result = self.pipeline.process("work", "claims/incomplete-claim.txt")
        result.route = "auto_approve"
        with self.assertRaises(ValueError):
            self.pipeline.record("work", "claims/incomplete-claim.txt", result)
        self.assertFalse(self._results_path("claims/incomplete-claim.txt").exists())

    def test_step_units_are_invocable(self) -> None:
        extracted = self.pipeline.understand_extract(
            "work", "claims/auto-fl-collision.txt"
        )
        self.assertIn("extracted_info", extracted)
        self.assertIn("document_text", extracted)
        summarized = self.pipeline.retrieve_summarize(
            extracted["extracted_info"],
            extracted["document_text"],
        )
        self.assertTrue(summarized["citations"] or summarized["ungrounded"])
        validation = self.pipeline.validate(
            extracted["extracted_info"],
            summary=summarized["summary"],
            citations=summarized["citations"],
            ungrounded=summarized["ungrounded"],
        )
        result = ProcessingResult(
            extracted_info=extracted["extracted_info"],
            summary=summarized["summary"],
            citations=summarized["citations"],
            ungrounded=summarized["ungrounded"],
            validation=validation,
            extract_model_id=extracted["extract_model_id"],
            summary_model_id=summarized["summary_model_id"],
            prompt_versions=PromptTemplateManager().versions(),
        )
        result.route = self.pipeline.route(result)
        self.assertEqual(result.route, "auto_approve")
        written = self.pipeline.record(
            "work", "claims/auto-fl-collision.txt", result
        )
        self.assertEqual(written["route"], "auto_approve")
        self.assertTrue(self._results_path("claims/auto-fl-collision.txt").is_file())

    def test_understand_extract_loads_image_bytes(self) -> None:
        png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
        (self.root / "work" / "claims" / "photo.png").write_bytes(png)
        out = self.pipeline.understand_extract("work", "claims/photo.png")
        self.assertEqual(out["understand_model_id"], UNDERSTAND_MODEL_EXAMPLE)
        self.assertIn("extracted_info", out)


if __name__ == "__main__":
    unittest.main()
