from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.fake import FakeModelInvoker
from claim_processor.handler import MissingPipelineError, await_review
from claim_processor.pipeline import ClaimPipeline
from claim_processor.prompts import PromptTemplateManager
from claim_processor.rag import PolicyRetriever
from claim_processor.store import (
    LocalDocumentStore,
    get_pending_token,
    pending_token_key,
)
from claim_processor.validator import ContentValidator


def _pipeline(root: Path) -> ClaimPipeline:
    return ClaimPipeline(
        store=LocalDocumentStore(root),
        invoker=FakeModelInvoker(),
        templates=PromptTemplateManager(),
        validator=ContentValidator(),
        retriever=PolicyRetriever(ROOT / "samples" / "policies"),
    )


class PendingTokenKeyTests(unittest.TestCase):
    def test_token_key_sits_beside_the_pending_record(self) -> None:
        self.assertEqual(
            pending_token_key("claims/home-tx-water.txt"),
            "pending-review/claims/home-tx-water.txt.token.json",
        )


class AwaitReviewHandlerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.pipeline = _pipeline(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_persists_token_beside_parked_claim(self) -> None:
        event = {
            "token": "AAAAKgAAAAIAAAAA-task-token",
            "bucket": "work",
            "key": "claims/home-tx-water.txt",
        }
        out = await_review(event, pipeline=self.pipeline)
        stored = get_pending_token(
            self.pipeline.store, "work", "claims/home-tx-water.txt"
        )
        self.assertEqual(stored["task_token"], "AAAAKgAAAAIAAAAA-task-token")
        self.assertEqual(stored["bucket"], "work")
        self.assertEqual(stored["claim_key"], "claims/home-tx-water.txt")
        self.assertIn("parked_at", stored)
        self.assertEqual(
            out,
            {
                "parked": True,
                "token_key": "pending-review/claims/home-tx-water.txt.token.json",
            },
        )

    def test_missing_token_fails_loudly(self) -> None:
        with self.assertRaises(KeyError):
            await_review(
                {"bucket": "work", "key": "claims/home-tx-water.txt"},
                pipeline=self.pipeline,
            )

    def test_missing_pipeline_raises(self) -> None:
        with self.assertRaises(MissingPipelineError):
            await_review({"token": "t", "bucket": "b", "key": "k"})

    def test_lambda_entry_exposes_await_review(self) -> None:
        from claim_processor import lambda_entry

        self.assertEqual(lambda_entry.await_review.__name__, "await_review")


if __name__ == "__main__":
    unittest.main()
