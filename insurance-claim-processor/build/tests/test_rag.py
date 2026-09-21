from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.rag import PolicyRetriever


class RagTests(unittest.TestCase):
    def test_auto_query_prefers_florida_auto(self) -> None:
        retriever = PolicyRetriever(ROOT / "samples" / "policies")
        hits = retriever.retrieve("collision third party Florida auto Civic Miami")
        self.assertTrue(hits)
        self.assertEqual(hits[0].chunk_id, "auto-florida")

    def test_filter_excludes_other_jurisdiction(self) -> None:
        retriever = PolicyRetriever(ROOT / "samples" / "policies")
        hits = retriever.retrieve(
            "collision water plumbing Florida Texas auto home",
            jurisdiction="texas",
            line_of_business="homeowners",
        )
        self.assertEqual([h.chunk_id for h in hits], ["homeowners-texas"])

    def test_empty_query_returns_nothing(self) -> None:
        retriever = PolicyRetriever(ROOT / "samples" / "policies")
        self.assertEqual(retriever.retrieve(""), [])


if __name__ == "__main__":
    unittest.main()
