"""R-07 — graceful-degradation tier ladder + rule-based floor (ADR 0014).

AC-P1 (advanced down → next tier → rule-based), AC-P2 (rule-based 5-field
shape), AC-P5 (tier + trigger recorded). A degraded result never auto-approves
— that assertion lives in routing (R-09).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.adapter import AdapterResult, CallOutcome
from claim_processor.degrade import RuleBasedExtractor, is_degraded, walk_tiers
from claim_processor.models import EXTRACT_FIELDS

_SAMPLE = "Policy POL-FL-123 claim amount $4,200 on 2026-03-01 windshield crack."


def _ok(model_id: str) -> AdapterResult:
    return AdapterResult(text="{}", model_id=model_id, outcome=CallOutcome.OK)


def _fail(model_id: str, outcome: CallOutcome) -> AdapterResult:
    return AdapterResult(text="", model_id=model_id, outcome=outcome)


class RuleBasedExtractorTests(unittest.TestCase):
    def test_produces_five_field_schema(self) -> None:
        extracted = RuleBasedExtractor().extract(_SAMPLE)
        for field in EXTRACT_FIELDS:
            self.assertIn(field, extracted)


class WalkTiersTests(unittest.TestCase):
    def test_advanced_ok_is_not_degraded(self) -> None:
        result = walk_tiers(
            _SAMPLE, ["adv", "basic", "rule_based"], lambda m: _ok(m)
        )
        self.assertEqual(result.tier, "advanced")
        self.assertIsNone(result.trigger)
        self.assertFalse(is_degraded(result.tier))

    def test_advanced_fails_falls_to_basic(self) -> None:
        def invoke(model_id: str) -> AdapterResult:
            return _fail(model_id, CallOutcome.THROTTLED) if model_id == "adv" else _ok(model_id)

        result = walk_tiers(_SAMPLE, ["adv", "basic", "rule_based"], invoke)
        self.assertEqual(result.tier, "basic")
        self.assertEqual(result.trigger, "exhausted_retry")
        self.assertTrue(is_degraded(result.tier))

    def test_all_fm_fail_uses_rule_based(self) -> None:
        result = walk_tiers(
            _SAMPLE,
            ["adv", "basic", "rule_based"],
            lambda m: _fail(m, CallOutcome.TIMED_OUT),
        )
        self.assertEqual(result.tier, "rule_based")
        self.assertEqual(result.trigger, "exhausted_retry")
        for field in EXTRACT_FIELDS:
            self.assertIn(field, result.extracted)

    def test_breaker_open_skips_to_next_tier(self) -> None:
        result = walk_tiers(
            _SAMPLE,
            ["adv", "basic", "rule_based"],
            lambda m: _ok(m),
            is_open=lambda m: m == "adv",
        )
        self.assertEqual(result.tier, "basic")
        self.assertEqual(result.trigger, "breaker")

    def test_no_rule_based_tier_still_floors_never_empty(self) -> None:
        result = walk_tiers(
            _SAMPLE, ["adv", "basic"], lambda m: _fail(m, CallOutcome.INVALID)
        )
        self.assertEqual(result.tier, "rule_based")
        self.assertIsNotNone(result.extracted)


if __name__ == "__main__":
    unittest.main()
