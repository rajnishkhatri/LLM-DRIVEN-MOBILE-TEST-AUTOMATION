"""R-05 — feature-flag evaluation (ADR 0010).

AC-M1 (absent/unavailable flag → safe default), AC-M2 (deterministic
claim_key assignment; a re-run is stable — preserves C9), AC-M5 (kill-switch
forces off with no deployment).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.flags import assign_variant, ensemble_enabled, flag


class FlagDefaultsTests(unittest.TestCase):
    def test_absent_flag_returns_safe_default(self) -> None:
        self.assertIs(flag({}, "ensemble_enabled"), False)
        self.assertIs(flag({}, "breaker_enabled"), True)
        self.assertIs(flag({}, "degradation_enabled"), True)
        self.assertEqual(flag({}, "candidate_rollout_pct"), 0)

    def test_flag_source_unavailable_returns_safe_default(self) -> None:
        # None (flag service down) must not crash — conservative default (M1).
        self.assertIs(flag(None, "ensemble_enabled"), False)
        self.assertIs(flag(None, "breaker_enabled"), True)


class VariantAssignmentTests(unittest.TestCase):
    def test_zero_pct_is_all_control(self) -> None:
        self.assertEqual(assign_variant("claims/x", {"candidate_rollout_pct": 0}), "control")

    def test_hundred_pct_is_all_candidate(self) -> None:
        self.assertEqual(
            assign_variant("claims/x", {"candidate_rollout_pct": 100}), "candidate"
        )

    def test_assignment_is_deterministic_per_key(self) -> None:
        flags = {"candidate_rollout_pct": 50}
        first = assign_variant("claims/stable-key", flags)
        second = assign_variant("claims/stable-key", flags)
        self.assertEqual(first, second)

    def test_kill_switch_forces_control_even_at_full_rollout(self) -> None:
        flags = {"candidate_rollout_pct": 100, "kill_switch_candidate": True}
        self.assertEqual(assign_variant("claims/x", flags), "control")


class EnsembleFlagTests(unittest.TestCase):
    def test_ensemble_enabled_reads_flag(self) -> None:
        self.assertTrue(ensemble_enabled({"ensemble_enabled": True}))
        self.assertFalse(ensemble_enabled({"ensemble_enabled": False}))
        self.assertFalse(ensemble_enabled({}))  # safe default off

    def test_ensemble_kill_switch_forces_off(self) -> None:
        flags = {"ensemble_enabled": True, "kill_switch_ensemble": True}
        self.assertFalse(ensemble_enabled(flags))


if __name__ == "__main__":
    unittest.main()
