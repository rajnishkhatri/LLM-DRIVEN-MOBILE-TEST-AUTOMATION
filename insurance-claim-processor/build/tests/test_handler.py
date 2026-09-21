from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.fake import FakeModelInvoker
from claim_processor.pipeline import ClaimPipeline, result_key_for
from claim_processor.prompts import PromptTemplateManager
from claim_processor.rag import PolicyRetriever
from claim_processor.store import LocalDocumentStore, get_pending_review, pending_review_key
from claim_processor.validator import ContentValidator


def _pipeline(root: Path) -> ClaimPipeline:
    return ClaimPipeline(
        store=LocalDocumentStore(root),
        invoker=FakeModelInvoker(),
        templates=PromptTemplateManager(),
        validator=ContentValidator(),
        retriever=PolicyRetriever(ROOT / "samples" / "policies"),
    )


class HandlerAdapterTests(unittest.TestCase):
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
        self.pipeline = _pipeline(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_understand_extract_maps_sfn_event(self) -> None:
        from claim_processor.handler import understand_extract

        out = understand_extract(
            {"bucket": "work", "key": "claims/auto-fl-collision.txt"},
            pipeline=self.pipeline,
        )
        self.assertIn("extracted_info", out)
        self.assertIn("document_text", out)
        self.assertEqual(out["extracted_info"]["claimant_name"], "Maria Elena Ruiz")

    def test_validate_then_retrieve_summarize_then_route_field(self) -> None:
        from claim_processor.handler import retrieve_summarize, validate

        extracted = self.pipeline.understand_extract(
            "work", "claims/auto-fl-collision.txt"
        )
        event = {
            "bucket": "work",
            "key": "claims/auto-fl-collision.txt",
            **extracted,
        }
        validated = validate(event, pipeline=self.pipeline)
        self.assertIn("validation", validated)
        self.assertTrue(validated["validation"]["accepted"])
        summarized = retrieve_summarize(validated, pipeline=self.pipeline)
        self.assertTrue(summarized["citations"] or summarized["ungrounded"])
        self.assertIn(summarized["route"], ("auto_approve", "human_review"))

    def test_record_auto_writes_results(self) -> None:
        from claim_processor.handler import record, retrieve_summarize, validate

        extracted = self.pipeline.understand_extract(
            "work", "claims/auto-fl-collision.txt"
        )
        event = retrieve_summarize(
            validate({"bucket": "work", "key": "claims/auto-fl-collision.txt", **extracted}, pipeline=self.pipeline),
            pipeline=self.pipeline,
        )
        self.assertEqual(event["route"], "auto_approve")
        written = record(event, pipeline=self.pipeline)
        self.assertEqual(written["route"], "auto_approve")
        path = self.root / "work" / result_key_for("claims/auto-fl-collision.txt")
        self.assertTrue(path.is_file())

    def test_record_flagged_writes_pending_review(self) -> None:
        from claim_processor.handler import record, retrieve_summarize, validate

        extracted = self.pipeline.understand_extract(
            "work", "claims/incomplete-claim.txt"
        )
        event = retrieve_summarize(
            validate(
                {"bucket": "work", "key": "claims/incomplete-claim.txt", **extracted},
                pipeline=self.pipeline,
            ),
            pipeline=self.pipeline,
        )
        self.assertEqual(event["route"], "human_review")
        written = record(event, pipeline=self.pipeline)
        self.assertEqual(written["route"], "human_review")
        pending = get_pending_review(
            self.pipeline.store, "work", "claims/incomplete-claim.txt"
        )
        self.assertEqual(pending["route"], "human_review")
        self.assertFalse(
            (self.root / "work" / result_key_for("claims/incomplete-claim.txt")).exists()
        )

    def test_record_review_expired_never_auto_approves(self) -> None:
        from claim_processor.handler import expire_review, record, retrieve_summarize, validate

        extracted = self.pipeline.understand_extract(
            "work", "claims/incomplete-claim.txt"
        )
        event = retrieve_summarize(
            validate(
                {"bucket": "work", "key": "claims/incomplete-claim.txt", **extracted},
                pipeline=self.pipeline,
            ),
            pipeline=self.pipeline,
        )
        record(event, pipeline=self.pipeline)
        pending = get_pending_review(
            self.pipeline.store, "work", "claims/incomplete-claim.txt"
        )
        expired = expire_review(pending, pipeline=self.pipeline)
        self.assertEqual(expired["review"]["decision"], "review-expired")
        self.assertNotEqual(expired.get("route"), "auto_approve")
        written = record(expired, pipeline=self.pipeline)
        self.assertEqual(written["review"]["decision"], "review-expired")
        self.assertEqual(written["route"], "human_review")
        self.assertTrue(
            (self.root / "work" / result_key_for("claims/incomplete-claim.txt")).is_file()
        )
        self.assertEqual(
            json.loads(
                (self.root / "work" / pending_review_key("claims/incomplete-claim.txt")).read_text(
                    encoding="utf-8"
                )
                if (self.root / "work" / pending_review_key("claims/incomplete-claim.txt")).exists()
                else "{}"
            ).get("review", {})
            .get("decision"),
            None,
        )

    def test_handler_does_not_import_boto3_at_load(self) -> None:
        import claim_processor.handler as handler_mod

        source = Path(handler_mod.__file__).read_text(encoding="utf-8")
        self.assertNotRegex(
            source,
            r"^import boto3|from boto3",
            msg="handler must not import a client at load (Wave 0 §11)",
        )


if __name__ == "__main__":
    unittest.main()
