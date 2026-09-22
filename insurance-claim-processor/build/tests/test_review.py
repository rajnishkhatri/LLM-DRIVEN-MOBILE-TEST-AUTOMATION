from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.review import apply_decision


def _pending(**overrides: object) -> dict:
    payload = {
        "extracted_info": {
            "claimant_name": "A. Claimant",
            "policy_number": "POL-1",
            "incident_date": "2026-01-01",
            "claim_amount": 100.0,
            "incident_description": "fender bender",
        },
        "summary": "original summary — must survive correct",
        "citations": ["chunk-1"],
        "ungrounded": False,
        "validation": {"accepted": True, "flags": []},
        "route": "human_review",
        "review": None,
        "schema_version": "1.0",
    }
    payload.update(overrides)
    return payload


class ApplyDecisionTests(unittest.TestCase):
    def test_correct_records_field_changes_and_final_values(self) -> None:
        pending = _pending()
        out = apply_decision(
            pending,
            decision="correct",
            reviewer_id="examiner-1",
            timestamp="2026-09-21T12:00:00Z",
            corrections={"claim_amount": 90.0, "policy_number": "POL-FIXED"},
        )
        self.assertEqual(out["extracted_info"]["claim_amount"], 90.0)
        self.assertEqual(out["extracted_info"]["policy_number"], "POL-FIXED")
        self.assertEqual(out["extracted_info"]["claimant_name"], "A. Claimant")
        self.assertEqual(
            out["review"],
            {
                "decision": "correct",
                "reviewer_id": "examiner-1",
                "timestamp": "2026-09-21T12:00:00Z",
                "field_changes": [
                    {"field": "claim_amount", "from": 100.0, "to": 90.0},
                    {"field": "policy_number", "from": "POL-1", "to": "POL-FIXED"},
                ],
            },
        )
        self.assertEqual(out["summary"], "original summary — must survive correct")
        self.assertEqual(out["validation"], {"accepted": True, "flags": []})
        self.assertEqual(out["citations"], ["chunk-1"])

    def test_correct_requires_corrections(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            apply_decision(
                _pending(),
                decision="correct",
                reviewer_id="examiner-1",
            )
        self.assertIn("corrections", str(ctx.exception).lower())

    def test_approve_leaves_extracted_info_unchanged(self) -> None:
        pending = _pending()
        original = dict(pending["extracted_info"])
        out = apply_decision(
            pending,
            decision="approve",
            reviewer_id="examiner-2",
            timestamp="2026-09-21T13:00:00Z",
        )
        self.assertEqual(out["extracted_info"], original)
        self.assertEqual(out["review"]["decision"], "approve")
        self.assertEqual(out["review"]["reviewer_id"], "examiner-2")
        self.assertEqual(out["review"]["field_changes"], [])
        self.assertEqual(out["review"]["timestamp"], "2026-09-21T13:00:00Z")
        self.assertNotEqual(out["review"]["decision"], "auto_approve")

    def test_reject_leaves_extracted_info_unchanged(self) -> None:
        pending = _pending()
        original = dict(pending["extracted_info"])
        out = apply_decision(
            pending,
            decision="reject",
            reviewer_id="examiner-3",
            timestamp="2026-09-21T14:00:00Z",
        )
        self.assertEqual(out["extracted_info"], original)
        self.assertEqual(out["review"]["decision"], "reject")
        self.assertEqual(out["review"]["field_changes"], [])

    def test_review_expired_never_auto_approves(self) -> None:
        out = apply_decision(
            _pending(route="human_review"),
            decision="review-expired",
            reviewer_id="system",
            timestamp="2026-09-28T00:00:00Z",
        )
        self.assertEqual(out["review"]["decision"], "review-expired")
        self.assertEqual(out["review"]["reviewer_id"], "system")
        self.assertEqual(out["review"]["field_changes"], [])
        self.assertNotEqual(out["route"], "auto_approve")
        self.assertEqual(out["extracted_info"]["claim_amount"], 100.0)

    def test_default_timestamp_is_iso8601(self) -> None:
        out = apply_decision(
            _pending(),
            decision="approve",
            reviewer_id="examiner-4",
        )
        stamp = out["review"]["timestamp"]
        self.assertIsInstance(stamp, str)
        self.assertRegex(stamp, r"^\d{4}-\d{2}-\d{2}T")

    def test_unknown_decision_is_named_failure(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            apply_decision(
                _pending(),
                decision="maybe",
                reviewer_id="examiner-5",
            )
        self.assertIn("decision", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
