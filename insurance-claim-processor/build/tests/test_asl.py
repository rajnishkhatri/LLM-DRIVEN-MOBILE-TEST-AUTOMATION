from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ASL_PATH = ROOT / "sfn" / "asl.json"
_SEVEN_DAYS = 7 * 24 * 60 * 60


def _load_definition() -> dict:
    raw = json.loads(ASL_PATH.read_text(encoding="utf-8"))
    if "States" in raw:
        return raw
    return raw["Definition"]


class AslStructureTests(unittest.TestCase):
    def test_asl_file_exists(self) -> None:
        self.assertTrue(ASL_PATH.is_file(), f"missing {ASL_PATH}")

    def test_standard_type_not_express(self) -> None:
        raw = json.loads(ASL_PATH.read_text(encoding="utf-8"))
        machine_type = (raw.get("Type") or raw.get("type") or "").upper()
        comment = (
            (raw.get("Comment") or "")
            + (raw.get("Definition", {}).get("Comment") or "")
        ).upper()
        self.assertEqual(machine_type, "STANDARD")
        self.assertIn("STANDARD", comment)
        self.assertNotEqual(machine_type, "EXPRESS")

    def test_named_states_and_choice_to_wait_for_task_token(self) -> None:
        definition = _load_definition()
        states = definition["States"]
        for name in (
            "UnderstandExtract",
            "Validate",
            "RetrieveSummarize",
            "Route",
            "AwaitReview",
            "Record",
        ):
            self.assertIn(name, states, f"missing state {name}")
        # Entry is the breaker Choice (ADR 0012); its Default is the normal path.
        self.assertEqual(definition["StartAt"], "BreakerProbe")  # review #3
        self.assertEqual(states["BreakerCheck"]["Default"], "UnderstandExtract")
        self.assertEqual(states["UnderstandExtract"]["Next"], "Validate")
        self.assertEqual(states["Validate"]["Next"], "RetrieveSummarize")
        self.assertEqual(states["RetrieveSummarize"]["Next"], "Route")
        self.assertEqual(states["Route"]["Type"], "Choice")
        await_review = states["AwaitReview"]
        resource = await_review.get("Resource", "")
        self.assertEqual(await_review["Type"], "Task")
        self.assertIn("waitForTaskToken", resource)
        self.assertEqual(await_review.get("TimeoutSeconds"), _SEVEN_DAYS)
        timeout_catch = [
            c
            for c in await_review.get("Catch") or []
            if "States.Timeout" in (c.get("ErrorEquals") or [])
        ]
        self.assertTrue(timeout_catch, "AwaitReview must Catch States.Timeout (AC-E4)")
        self.assertEqual(states["Record"]["Type"], "Task")

    def test_retry_catch_c2_c7_c11(self) -> None:
        states = _load_definition()["States"]
        for name in ("UnderstandExtract", "RetrieveSummarize"):
            retries = states[name].get("Retry") or []
            error_names = [e for block in retries for e in block.get("ErrorEquals") or []]
            self.assertTrue(
                any("Throttl" in e for e in error_names),
                f"{name} Retry must cover throttle (C2)",
            )
            self.assertGreaterEqual(states[name].get("TimeoutSeconds") or 0, 300)
            catches = states[name].get("Catch") or []
            self.assertTrue(catches, f"{name} needs Catch (C7)")
        retrieve_catch = states["RetrieveSummarize"].get("Catch") or []
        catch_nexts = [c.get("Next") for c in retrieve_catch]
        self.assertTrue(
            any("Ungrounded" in (n or "") for n in catch_nexts),
            "RetrieveSummarize Catch must branch ungrounded (C11)",
        )

    def test_one_execution_per_claim_no_map_fanout(self) -> None:
        states = _load_definition()["States"]
        for name, state in states.items():
            self.assertNotEqual(state.get("Type"), "Map", f"{name} would fan out executions")
            self.assertNotEqual(state.get("Type"), "Parallel")


if __name__ == "__main__":
    unittest.main()
