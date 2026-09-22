"""R-06 — pure circuit-breaker decision over a measured signal (ADR 0012).

AC-N1 (measured signal, not raw count; slow-success does not open),
AC-N3 (state read from shared flag, not in-process),
AC-N4 (recover → half-open → close).
"""

from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.breaker import (
    BreakerConfig,
    BreakerSignal,
    breaker_open,
    decide_state,
)


class DecideStateTests(unittest.TestCase):
    def test_slow_success_does_not_open(self) -> None:
        # High volume, zero errors (slow successes) must stay closed (N1).
        signal = BreakerSignal(error_rate=0.0, sample_size=100)
        self.assertEqual(decide_state(signal, "closed", BreakerConfig()), "closed")

    def test_high_error_rate_opens(self) -> None:
        signal = BreakerSignal(error_rate=0.8, sample_size=100)
        self.assertEqual(decide_state(signal, "closed", BreakerConfig()), "open")

    def test_below_min_samples_holds_state(self) -> None:
        # A tiny window cannot fill the breaker honestly (N1 / clinic §2).
        signal = BreakerSignal(error_rate=1.0, sample_size=3)
        self.assertEqual(decide_state(signal, "closed", BreakerConfig()), "closed")

    def test_open_to_half_open_on_recovery(self) -> None:
        signal = BreakerSignal(error_rate=0.05, sample_size=100)
        self.assertEqual(decide_state(signal, "open", BreakerConfig()), "half_open")

    def test_half_open_to_closed_when_healthy(self) -> None:
        signal = BreakerSignal(error_rate=0.0, sample_size=100)
        self.assertEqual(decide_state(signal, "half_open", BreakerConfig()), "closed")

    def test_half_open_back_to_open_if_still_failing(self) -> None:
        signal = BreakerSignal(error_rate=0.8, sample_size=100)
        self.assertEqual(decide_state(signal, "half_open", BreakerConfig()), "open")

    def test_decide_state_is_pure(self) -> None:
        # State is a parameter, not module storage (N3 — no in-process breaker).
        params = inspect.signature(decide_state).parameters
        self.assertIn("current", params)


class BreakerOpenFlagTests(unittest.TestCase):
    def test_reads_shared_flag_per_model(self) -> None:
        flags = {"breaker_open_models": ["m1"]}
        self.assertTrue(breaker_open(flags, "m1"))
        self.assertFalse(breaker_open(flags, "m2"))

    def test_disabled_breaker_never_open(self) -> None:
        flags = {"breaker_enabled": False, "breaker_open_models": ["m1"]}
        self.assertFalse(breaker_open(flags, "m1"))

    def test_absent_flags_never_open(self) -> None:
        self.assertFalse(breaker_open({}, "m1"))


if __name__ == "__main__":
    unittest.main()
