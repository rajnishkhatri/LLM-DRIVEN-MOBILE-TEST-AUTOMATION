"""R-13 — ASL BreakerCheck Choice routes an open-breaker claim to the degraded
path without invoking the failing model (ADR 0012 / AC-N2).

SFN-Local is not in this environment; step logic is unit-tested elsewhere, so
this asserts the state-machine STRUCTURE offline.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ASL_PATH = ROOT / "sfn" / "asl.json"


def _states() -> dict:
    raw = json.loads(ASL_PATH.read_text(encoding="utf-8"))
    definition = raw if "States" in raw else raw["Definition"]
    return definition


class BreakerChoiceTests(unittest.TestCase):
    def test_start_at_breaker_probe(self) -> None:
        """Review #3: the BreakerCheck Choice read `$.breaker_open` but no
        state ever produced it — DegradedExtract was unreachable. A probe Task
        must populate the variable before the Choice."""
        self.assertEqual(_states()["StartAt"], "BreakerProbe")

    def test_breaker_probe_feeds_breaker_check(self) -> None:
        states = _states()["States"]
        probe = states["BreakerProbe"]
        self.assertEqual(probe["Type"], "Task")
        self.assertEqual(probe["Next"], "BreakerCheck")
        self.assertIn("breaker-probe", probe["Resource"])

    def test_breaker_check_is_choice_on_breaker_open(self) -> None:
        states = _states()["States"]
        breaker = states["BreakerCheck"]
        self.assertEqual(breaker["Type"], "Choice")
        # open breaker → degraded path
        open_targets = [
            c.get("Next")
            for c in breaker["Choices"]
            if c.get("Variable") == "$.breaker_open"
        ]
        self.assertIn("DegradedExtract", open_targets)
        # closed → normal extract
        self.assertEqual(breaker["Default"], "UnderstandExtract")

    def test_degraded_extract_skips_to_validate(self) -> None:
        states = _states()["States"]
        self.assertIn("DegradedExtract", states)
        self.assertEqual(states["DegradedExtract"]["Type"], "Task")
        self.assertEqual(states["DegradedExtract"]["Next"], "Validate")

    def test_ungrounded_fallback_keeps_wave3_provenance(self) -> None:
        """Re-review #7: the Pass state's Parameters whitelist predated Wave 3
        and stripped provenance, usage, and model ids from the RAG-down path —
        exactly the executions most worth auditing (AC-K5/P5/R4)."""
        params = _states()["States"]["UngroundedFallback"]["Parameters"]
        for field in (
            "extract_model_id.$",
            "understand_model_id.$",
            "usage.$",
            "guardrail.$",
            "config_snapshot.$",
            "config_rejected.$",
            "model_variant.$",
            "ensemble.$",
            "degradation_tier.$",
            "breaker_state.$",
            "breaker_open.$",
        ):
            self.assertIn(field, params)
        self.assertEqual(params["route"], "human_review")  # AC-R3 unchanged

    def test_exhausted_throttle_degrades_instead_of_failing(self) -> None:
        """Re-review #3, resolved as option B (2026-09-22): after the Retry
        tier exhausts on a sustained throttle, the claim walks the degradation
        ladder (AC-P1 'retries exhausted → degrade') rather than failing the
        execution. Short spikes stay absorbed by the Retry tier (C2); only
        what survives it degrades (C11)."""
        states = _states()["States"]
        catches = states["UnderstandExtract"].get("Catch", [])
        throttle_targets = [
            c.get("Next")
            for c in catches
            if "ThrottlingException" in c.get("ErrorEquals", [])
        ]
        self.assertEqual(throttle_targets, ["DegradedExtract"])

    def test_normal_path_unchanged(self) -> None:
        states = _states()["States"]
        self.assertEqual(states["UnderstandExtract"]["Next"], "Validate")
        self.assertEqual(states["Route"]["Type"], "Choice")


if __name__ == "__main__":
    unittest.main()
