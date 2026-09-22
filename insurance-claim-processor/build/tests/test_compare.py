from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.compare import compare_models
from claim_processor.fake import FakeModelInvoker


class CompareTests(unittest.TestCase):
    def test_records_per_model_metrics(self) -> None:
        fake = FakeModelInvoker(
            canned={
                "extract": json.dumps(
                    {
                        "claimant_name": "A",
                        "policy_number": "1",
                        "incident_date": "2026-01-01",
                        "claim_amount": 1,
                        "incident_description": "x",
                    }
                )
            }
        )
        table = compare_models("doc", fake, ["model-a", "model-b"])
        self.assertEqual(set(table), {"model-a", "model-b"})
        self.assertTrue(table["model-a"]["validator_accepted"])
        self.assertIn("time_seconds", table["model-b"])


if __name__ == "__main__":
    unittest.main()
