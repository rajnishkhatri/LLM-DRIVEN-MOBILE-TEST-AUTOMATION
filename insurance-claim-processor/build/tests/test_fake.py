from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.fake import FakeModelInvoker
from claim_processor.models import EXTRACT_FIELDS
from claim_processor.understand import to_content_blocks
from claim_processor.validator import ContentValidator

IMAGE_SAMPLE = ROOT / "samples" / "claims" / "auto-fl-photo.png"
IMAGE_GOLD = ROOT / "samples" / "gold" / "auto-fl-photo.json"


class FakeImageEvalTests(unittest.TestCase):
    def test_image_sample_and_gold_exist(self) -> None:
        self.assertTrue(IMAGE_SAMPLE.is_file(), f"missing image sample: {IMAGE_SAMPLE}")
        self.assertTrue(IMAGE_GOLD.is_file(), f"missing gold: {IMAGE_GOLD}")

    def test_image_sample_extracts_schema_valid_five_fields_matching_gold(self) -> None:
        gold = json.loads(IMAGE_GOLD.read_text(encoding="utf-8"))
        blocks = to_content_blocks(IMAGE_SAMPLE.read_bytes(), filename=IMAGE_SAMPLE.name)
        self.assertIn("image", blocks[0])

        out = FakeModelInvoker().converse(
            "Extract the following fields from this image packet",
            content=[{"text": "Extract the following fields"}, blocks[0]],
        )
        parsed = json.loads(out["text"])
        for field in EXTRACT_FIELDS:
            self.assertIn(field, parsed)
            self.assertIsNotNone(parsed[field])
            self.assertNotEqual(parsed[field], "")

        validation = ContentValidator().parse_extraction(out["text"])
        self.assertTrue(validation.accepted)
        self.assertFalse(
            any(f.startswith("empty_fields:") or f.startswith("missing_keys:") for f in validation.flags)
        )

        gold_amount = float(gold["claim_amount"])
        got_amount = float(parsed["claim_amount"])
        self.assertNotEqual(gold_amount, 0)
        relative_error = abs(got_amount - gold_amount) / gold_amount
        self.assertEqual(relative_error, 0)
        self.assertEqual(parsed["claimant_name"], gold["claimant_name"])
        self.assertEqual(parsed["policy_number"], gold["policy_number"])
        self.assertEqual(parsed["incident_date"], gold["incident_date"])
        self.assertEqual(parsed["incident_description"], gold["incident_description"])

    def test_image_path_records_guardrail_when_config_passed(self) -> None:
        gold = json.loads(IMAGE_GOLD.read_text(encoding="utf-8"))
        blocks = to_content_blocks(IMAGE_SAMPLE.read_bytes(), filename=IMAGE_SAMPLE.name)
        out = FakeModelInvoker().converse(
            "Extract the following fields",
            content=[{"text": "Extract the following fields"}, blocks[0]],
            guardrail_config={"guardrailIdentifier": "gr-test", "guardrailVersion": "1"},
        )
        parsed = json.loads(out["text"])
        self.assertEqual(parsed["claim_amount"], gold["claim_amount"])
        self.assertEqual(out["guardrail"], {"intervened": False, "actions": []})


if __name__ == "__main__":
    unittest.main()
