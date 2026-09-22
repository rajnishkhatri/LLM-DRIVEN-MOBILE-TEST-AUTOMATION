from __future__ import annotations

import sys
import unittest
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.models import ProcessingResult, ValidationResult


def _minimal_result(**overrides: object) -> ProcessingResult:
    kwargs: dict = {
        "extracted_info": {"claimant_name": "A"},
        "summary": "ok",
        "citations": ["chunk-1"],
        "ungrounded": False,
        "validation": ValidationResult(accepted=True, flags=["note"]),
        "extract_model_id": "extract-resolved",
        "summary_model_id": "summary-resolved",
        "prompt_versions": {"extract_info": "1"},
    }
    kwargs.update(overrides)
    return ProcessingResult(**kwargs)


class ProcessingResultSerializationTests(unittest.TestCase):
    def test_asdict_includes_new_fields_with_defaults(self) -> None:
        result = _minimal_result()
        payload = asdict(result)
        self.assertEqual(payload["route"], None)
        self.assertEqual(payload["review"], None)
        self.assertEqual(payload["guardrail"], None)
        self.assertEqual(payload["sfn_execution_arn"], None)
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["understand_model_id"], None)
        self.assertEqual(payload["embeddings"], None)

    def test_to_record_includes_new_fields_with_defaults(self) -> None:
        result = _minimal_result()
        record = result.to_record()
        self.assertEqual(record["route"], None)
        self.assertEqual(record["review"], None)
        self.assertEqual(record["guardrail"], None)
        self.assertEqual(record["sfn_execution_arn"], None)
        self.assertEqual(record["schema_version"], "1.0")
        self.assertEqual(record["understand_model_id"], None)
        self.assertEqual(record["embeddings"], None)
        self.assertNotIn("claim_key", record)

    def test_to_record_flattens_validation_and_optional_claim_key(self) -> None:
        result = _minimal_result()
        record = result.to_record("claims/auto-fl-collision.txt")
        self.assertEqual(record["claim_key"], "claims/auto-fl-collision.txt")
        self.assertEqual(record["validation"], {"accepted": True, "flags": ["note"]})
        self.assertNotIn("parsed", record["validation"])

    def test_to_record_serializes_populated_provenance(self) -> None:
        result = _minimal_result(
            route="human_review",
            review={
                "decision": "correct",
                "reviewer_id": "examiner-1",
                "timestamp": "2026-09-21T12:00:00Z",
                "field_changes": [
                    {"field": "claim_amount", "from": 100.0, "to": 90.0},
                ],
            },
            guardrail={"intervened": True, "actions": ["ANONYMIZE"]},
            sfn_execution_arn="arn:aws:states:us-east-1:1:execution:sm:x",
            understand_model_id="understand-resolved",
            embeddings={"model_id": "embed-resolved", "dims": 1024},
        )
        record = result.to_record("claims/k")
        self.assertEqual(record["route"], "human_review")
        self.assertEqual(record["review"]["decision"], "correct")
        self.assertEqual(
            record["review"]["field_changes"],
            [{"field": "claim_amount", "from": 100.0, "to": 90.0}],
        )
        self.assertEqual(record["guardrail"], {"intervened": True, "actions": ["ANONYMIZE"]})
        self.assertEqual(
            record["sfn_execution_arn"],
            "arn:aws:states:us-east-1:1:execution:sm:x",
        )
        self.assertEqual(record["understand_model_id"], "understand-resolved")
        self.assertEqual(record["extract_model_id"], "extract-resolved")
        self.assertEqual(record["summary_model_id"], "summary-resolved")
        self.assertEqual(record["embeddings"], {"model_id": "embed-resolved", "dims": 1024})


if __name__ == "__main__":
    unittest.main()
