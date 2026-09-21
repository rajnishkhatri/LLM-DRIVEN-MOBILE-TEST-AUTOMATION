from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.validator import ContentValidator


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.v = ContentValidator()

    def test_parses_fenced_json(self) -> None:
        raw = '```json\n{"claimant_name":"A","policy_number":"1","incident_date":"2026-01-01","claim_amount":10,"incident_description":"x"}\n```'
        result = self.v.parse_extraction(raw)
        self.assertTrue(result.accepted)
        self.assertEqual(result.parsed["claim_amount"], 10.0)

    def test_flags_missing_keys(self) -> None:
        result = self.v.parse_extraction('{"claimant_name":"A"}')
        self.assertFalse(result.accepted)
        self.assertTrue(any(f.startswith("missing_keys:") for f in result.flags))

    def test_flags_ssn_in_summary(self) -> None:
        extraction = {
            "claimant_name": "A",
            "policy_number": "1",
            "incident_date": "2026-01-01",
            "claim_amount": 1,
            "incident_description": "x",
        }
        result = self.v.validate_result(extraction, "SSN 078-05-1120", ["auto-florida"], False)
        self.assertFalse(result.accepted)
        self.assertIn("pii_ssn", result.flags)

    def test_ungrounded_skips_citation_requirement(self) -> None:
        extraction = {
            "claimant_name": "A",
            "policy_number": "1",
            "incident_date": "2026-01-01",
            "claim_amount": 1,
            "incident_description": "x",
        }
        result = self.v.validate_result(extraction, "No policy match.", [], True)
        self.assertIn("ungrounded", result.flags)
        self.assertNotIn("missing_citations", result.flags)


if __name__ == "__main__":
    unittest.main()
