"""R-04 — EscalationPolicy carries the resilience config-plane fields and can
be built from a ConfigProvider-resolved dict.

AC-K2 (runtime source), AC-K3 (adopt a changed value with no code change).
Frozen `test_config.py` stays untouched — this is the additive home.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.config import EscalationPolicy

_NEW_ENV = (
    "CLAIM_PROCESSOR_ENSEMBLE_MODELS",
    "CLAIM_PROCESSOR_DEGRADATION_TIERS",
)


def _clean_env(**set_vars: str):
    env = {k: v for k, v in os.environ.items() if k not in _NEW_ENV}
    env.update(set_vars)
    return patch.dict(os.environ, env, clear=True)


class ConfigResilienceTests(unittest.TestCase):
    def test_new_fields_default_empty(self) -> None:
        policy = EscalationPolicy()
        self.assertEqual(policy.ensemble_models, ())
        self.assertEqual(policy.degradation_tiers, ())
        self.assertEqual(policy.flags, {})

    def test_from_env_reads_ensemble_and_tiers(self) -> None:
        with _clean_env(
            CLAIM_PROCESSOR_ENSEMBLE_MODELS="m1,m2,m3",
            CLAIM_PROCESSOR_DEGRADATION_TIERS="advanced,basic,rule_based",
        ):
            policy = EscalationPolicy.from_env()
        self.assertEqual(policy.ensemble_models, ("m1", "m2", "m3"))
        self.assertEqual(policy.degradation_tiers, ("advanced", "basic", "rule_based"))

    def test_from_config_overrides_base(self) -> None:
        base = EscalationPolicy(extract_model_id="boot-extract", amount_threshold=10000.0)
        policy = EscalationPolicy.from_config(
            {
                "amount_threshold": "25000",
                "extract_model_id": "cfg-extract",
                "ensemble_models": ["m1", "m2"],
                "degradation_tiers": ["advanced", "rule_based"],
                "flags": {"ensemble_enabled": True},
            },
            base=base,
        )
        self.assertEqual(policy.amount_threshold, 25000.0)  # coerced to float
        self.assertEqual(policy.extract_model_id, "cfg-extract")
        self.assertEqual(policy.ensemble_models, ("m1", "m2"))
        self.assertEqual(policy.degradation_tiers, ("advanced", "rule_based"))
        self.assertEqual(policy.flags, {"ensemble_enabled": True})

    def test_from_config_falls_back_to_base_for_missing(self) -> None:
        base = EscalationPolicy(summary_model_id="boot-summary", region="eu-west-1")
        policy = EscalationPolicy.from_config({"extract_model_id": "cfg-x"}, base=base)
        self.assertEqual(policy.extract_model_id, "cfg-x")
        self.assertEqual(policy.summary_model_id, "boot-summary")
        self.assertEqual(policy.region, "eu-west-1")


if __name__ == "__main__":
    unittest.main()
