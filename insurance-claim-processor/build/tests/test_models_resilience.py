"""R-02 — ProcessingResult carries the model-resilience provenance fields.

AC-R4 / K5 / M3 / N5 / O4 / P5: config_snapshot, model_variant, ensemble,
degradation_tier, breaker_state, remediation — all optional/defaulted so a
pre-increment result still serializes.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.models import ProcessingResult, ValidationResult

_NEW_FIELDS = (
    "config_snapshot",
    "model_variant",
    "ensemble",
    "degradation_tier",
    "breaker_state",
    "remediation",
)


def _minimal_result(**kw) -> ProcessingResult:
    return ProcessingResult(
        extracted_info={"claim_amount": 100},
        summary="s",
        citations=[],
        ungrounded=False,
        validation=ValidationResult(accepted=True, flags=[]),
        extract_model_id="e",
        summary_model_id="s",
        prompt_versions={},
        **kw,
    )


class ResilienceFieldsTests(unittest.TestCase):
    def test_new_fields_default_none_and_serialize(self) -> None:
        result = _minimal_result()
        for attr in _NEW_FIELDS:
            self.assertIsNone(getattr(result, attr), attr)
        record = result.to_record("claims/x")
        for key in _NEW_FIELDS:
            self.assertIn(key, record)
            self.assertIsNone(record[key])

    def test_pre_increment_record_still_serializes(self) -> None:
        # Construction with no new kwargs must not raise (backward compat).
        record = _minimal_result().to_record("claims/x")
        self.assertEqual(record["claim_key"], "claims/x")
        self.assertEqual(record["schema_version"], "1.0")

    def test_resilience_fields_roundtrip(self) -> None:
        result = _minimal_result(
            config_snapshot={"extract_model_id": "m", "flags": {"ensemble": True}},
            model_variant="candidate:us.anthropic.claude-x",
            ensemble={"members": ["m1", "m2"], "agreement": 1.0},
            degradation_tier="rule_based",
            breaker_state="open",
            remediation={"alarm": "ModelErrorRate", "action": "open_breaker"},
        )
        record = result.to_record()
        self.assertEqual(record["config_snapshot"]["extract_model_id"], "m")
        self.assertEqual(record["model_variant"], "candidate:us.anthropic.claude-x")
        self.assertEqual(record["ensemble"]["agreement"], 1.0)
        self.assertEqual(record["degradation_tier"], "rule_based")
        self.assertEqual(record["breaker_state"], "open")
        self.assertEqual(record["remediation"]["action"], "open_breaker")


if __name__ == "__main__":
    unittest.main()
