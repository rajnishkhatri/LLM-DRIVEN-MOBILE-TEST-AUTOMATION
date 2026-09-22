"""R-09 — routing integrity: no new path auto-approves (AC-R3).

Degraded tier (P3), ensemble split (O1), breaker-open (N2), rejected config
(K4) all route to human review. The clean predicate (AC-E1) stays the single
auto-approve gate.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.config import EscalationPolicy
from claim_processor.models import ProcessingResult, ValidationResult
from claim_processor.routing import route_claim

_POLICY = EscalationPolicy(amount_threshold=10000.0)


def _clean(**kw) -> ProcessingResult:
    return ProcessingResult(
        extracted_info={"claim_amount": 100},
        summary="s",
        citations=["c1"],
        ungrounded=False,
        validation=ValidationResult(accepted=True, flags=list(kw.pop("flags", []))),
        extract_model_id="e",
        summary_model_id="s",
        prompt_versions={},
        **kw,
    )


class RoutingIntegrityTests(unittest.TestCase):
    def test_clean_still_auto_approves(self) -> None:
        self.assertEqual(route_claim(_clean(), _POLICY), "auto_approve")

    def test_degraded_tier_routes_review(self) -> None:
        self.assertEqual(
            route_claim(_clean(degradation_tier="rule_based"), _POLICY), "human_review"
        )

    def test_advanced_tier_is_not_degraded(self) -> None:
        # degradation_tier None (advanced FM) does not block auto-approve.
        self.assertEqual(route_claim(_clean(degradation_tier=None), _POLICY), "auto_approve")

    def test_ensemble_low_confidence_routes_review(self) -> None:
        result = _clean(ensemble={"members": ["m1", "m2"], "low_confidence_fields": ["claim_amount"]})
        self.assertEqual(route_claim(result, _POLICY), "human_review")

    def test_ensemble_full_agreement_auto_approves(self) -> None:
        result = _clean(ensemble={"members": ["m1", "m2"], "low_confidence_fields": []})
        self.assertEqual(route_claim(result, _POLICY), "auto_approve")

    def test_breaker_open_routes_review(self) -> None:
        self.assertEqual(route_claim(_clean(breaker_state="open"), _POLICY), "human_review")

    def test_config_rejected_routes_review(self) -> None:
        self.assertEqual(
            route_claim(_clean(flags=["config_rejected"]), _POLICY), "human_review"
        )


if __name__ == "__main__":
    unittest.main()
