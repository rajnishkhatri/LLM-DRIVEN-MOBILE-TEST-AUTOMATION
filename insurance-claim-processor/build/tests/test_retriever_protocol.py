from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import get_type_hints

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.fake import FakeModelInvoker
from claim_processor.models import PolicyChunk
from claim_processor.pipeline import ClaimPipeline
from claim_processor.prompts import PromptTemplateManager
from claim_processor.rag import PolicyRetriever
from claim_processor.store import LocalDocumentStore
from claim_processor.validator import ContentValidator


class RetrieverProtocolTests(unittest.TestCase):
    def test_retriever_protocol_matches_keyword_retrieve(self) -> None:
        from claim_processor.rag import RetrieverProtocol
        from typing import Protocol

        self.assertTrue(issubclass(RetrieverProtocol, Protocol))
        hints = get_type_hints(RetrieverProtocol.retrieve)
        self.assertEqual(hints.get("return").__origin__, list)
        self.assertEqual(hints["return"].__args__[0], PolicyChunk)

        retriever = PolicyRetriever(ROOT / "samples" / "policies")
        self.assertIsInstance(retriever, RetrieverProtocol)

    def test_pipeline_depends_on_protocol_not_keyword_class(self) -> None:
        from claim_processor.pipeline import ClaimPipeline as PipelineCls
        from claim_processor.rag import RetrieverProtocol

        hints = get_type_hints(PipelineCls.__init__)
        self.assertIs(hints["retriever"], RetrieverProtocol)

        chunks = [
            PolicyChunk(
                chunk_id="protocol-chunk",
                source="protocol.md",
                text="Florida personal auto collision Civic Miami third party",
                score=3.0,
                jurisdiction="florida",
                line_of_business="personal_auto",
            )
        ]

        class ProtocolOnlyRetriever:
            def retrieve(
                self,
                query: str,
                top_k: int = 2,
                *,
                jurisdiction: str | None = None,
                line_of_business: str | None = None,
            ) -> list[PolicyChunk]:
                return chunks[:top_k]

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        claims = root / "work" / "claims"
        claims.mkdir(parents=True)
        shutil.copy(
            ROOT / "samples" / "claims" / "auto-fl-collision.txt",
            claims / "auto-fl-collision.txt",
        )
        pipeline = ClaimPipeline(
            store=LocalDocumentStore(root),
            invoker=FakeModelInvoker(),
            templates=PromptTemplateManager(),
            validator=ContentValidator(),
            retriever=ProtocolOnlyRetriever(),
        )
        result = pipeline.process("work", "claims/auto-fl-collision.txt")
        self.assertEqual(result.citations, ["protocol-chunk"])
        self.assertFalse(result.ungrounded)
        payload = json.loads(
            (root / "work" / "results" / "claims" / "auto-fl-collision.txt.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(payload["citations"], ["protocol-chunk"])


if __name__ == "__main__":
    unittest.main()
