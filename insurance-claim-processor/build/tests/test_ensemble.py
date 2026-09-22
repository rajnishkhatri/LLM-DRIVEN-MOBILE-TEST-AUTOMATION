"""R-08 — field-level extraction ensembling (ADR 0013).

AC-O1 (disagreement → low-confidence → HITL, enforced in routing R-09),
AC-O2 (majority/agreement combine), AC-O4 (members recorded),
AC-O5 (quorum helper for the pipeline's primary fallback).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.ensemble import combine, has_quorum, resolve_quorum
from claim_processor.models import EXTRACT_FIELDS


def _row(amount, policy="POL-1", name="Ada", date="2026-01-01", desc="crack"):
    return {
        "claimant_name": name,
        "policy_number": policy,
        "incident_date": date,
        "claim_amount": amount,
        "incident_description": desc,
    }


class CombineTests(unittest.TestCase):
    def test_full_agreement_scores_one_no_low_conf(self) -> None:
        outputs = [("m1", _row(4200)), ("m2", _row(4200)), ("m3", _row(4200))]
        result = combine(outputs, required_fields=EXTRACT_FIELDS)
        self.assertEqual(result.low_confidence_fields, [])
        self.assertEqual(result.agreement["claim_amount"], 1.0)
        self.assertEqual(result.extracted["claim_amount"], 4200)

    def test_total_disagreement_marks_low_confidence(self) -> None:
        outputs = [("m1", _row(100)), ("m2", _row(200)), ("m3", _row(300))]
        result = combine(outputs, required_fields=EXTRACT_FIELDS)
        self.assertIn("claim_amount", result.low_confidence_fields)
        self.assertLess(result.agreement["claim_amount"], 0.5)

    def test_majority_wins(self) -> None:
        outputs = [("m1", _row(100, policy="POL-A")), ("m2", _row(999, policy="POL-A")), ("m3", _row(999, policy="POL-B"))]
        result = combine(outputs, required_fields=EXTRACT_FIELDS)
        self.assertEqual(result.extracted["policy_number"], "POL-A")
        self.assertAlmostEqual(result.agreement["policy_number"], 2 / 3)
        self.assertNotIn("policy_number", result.low_confidence_fields)

    def test_members_recorded(self) -> None:
        outputs = [("m1", _row(1)), ("m2", _row(1))]
        result = combine(outputs, required_fields=EXTRACT_FIELDS)
        self.assertEqual(result.members, ["m1", "m2"])

    def test_missing_field_is_low_confidence(self) -> None:
        rows = [{"claim_amount": ""} for _ in range(3)]
        result = combine(
            [("m1", rows[0]), ("m2", rows[1]), ("m3", rows[2])],
            required_fields=("claim_amount",),
        )
        self.assertIn("claim_amount", result.low_confidence_fields)
        self.assertIsNone(result.extracted["claim_amount"])

    def test_has_quorum(self) -> None:
        self.assertTrue(has_quorum(2, quorum=2))
        self.assertFalse(has_quorum(1, quorum=2))


class EvenSplitTests(unittest.TestCase):
    """Review #5: a vote with no strict majority must be low-confidence.

    A 2-model 50/50 split scored agreement exactly 0.5, and `0.5 < 0.5` never
    flagged it — a genuine model disagreement could auto-approve (AC-O1).
    """

    def test_two_member_split_is_low_confidence(self) -> None:
        outputs = [("m1", _row(100)), ("m2", _row(200))]
        result = combine(outputs, required_fields=EXTRACT_FIELDS)
        self.assertIn("claim_amount", result.low_confidence_fields)

    def test_single_vote_of_two_members_is_low_confidence(self) -> None:
        outputs = [("m1", _row("")), ("m2", _row(200))]
        result = combine(outputs, required_fields=EXTRACT_FIELDS)
        self.assertIn("claim_amount", result.low_confidence_fields)

    def test_two_member_agreement_stays_confident(self) -> None:
        outputs = [("m1", _row(4200)), ("m2", _row(4200))]
        result = combine(outputs, required_fields=EXTRACT_FIELDS)
        self.assertNotIn("claim_amount", result.low_confidence_fields)

    def test_four_member_two_two_tie_is_low_confidence(self) -> None:
        outputs = [("m1", _row(100)), ("m2", _row(100)), ("m3", _row(200)), ("m4", _row(200))]
        result = combine(outputs, required_fields=EXTRACT_FIELDS)
        self.assertIn("claim_amount", result.low_confidence_fields)


class ResolveQuorumTests(unittest.TestCase):
    """Review #9: `True` is an `int` — a boolean flag value must never become
    a quorum of 1 and let a single model 'win' an ensemble vote."""

    def test_explicit_int_wins(self) -> None:
        self.assertEqual(resolve_quorum(3, member_count=5), 3)

    def test_bool_true_falls_back_to_majority_default(self) -> None:
        self.assertEqual(resolve_quorum(True, member_count=2), 2)
        self.assertEqual(resolve_quorum(True, member_count=5), 3)

    def test_bool_false_zero_and_junk_fall_back(self) -> None:
        self.assertEqual(resolve_quorum(False, member_count=3), 2)
        self.assertEqual(resolve_quorum(0, member_count=3), 2)
        self.assertEqual(resolve_quorum("3", member_count=3), 2)

    def test_no_members_defaults_to_two(self) -> None:
        self.assertEqual(resolve_quorum(None, member_count=0), 2)


if __name__ == "__main__":
    unittest.main()
