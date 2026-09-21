from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.store import (
    LocalDocumentStore,
    get_pending_review,
    pending_review_key,
    put_pending_review,
)


class PendingReviewStoreTests(unittest.TestCase):
    def test_pending_review_key_shape(self) -> None:
        self.assertEqual(
            pending_review_key("claims/home-tx-water.txt"),
            "pending-review/claims/home-tx-water.txt.json",
        )

    def test_pending_review_json_roundtrip(self) -> None:
        claim_key = "claims/home-tx-water.txt"
        payload = {
            "claim_key": claim_key,
            "route": "human_review",
            "extracted_info": {"claimant_name": "James K. Patel"},
        }
        with tempfile.TemporaryDirectory() as tmp:
            store = LocalDocumentStore(Path(tmp))
            put_pending_review(store, "b", claim_key, payload)
            loaded = get_pending_review(store, "b", claim_key)
            self.assertEqual(loaded, payload)
            path = Path(tmp) / "b" / pending_review_key(claim_key)
            self.assertTrue(path.is_file())
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), payload)


if __name__ == "__main__":
    unittest.main()
