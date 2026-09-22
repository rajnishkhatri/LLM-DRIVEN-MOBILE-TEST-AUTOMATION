"""R-11 — alarm → bounded, reversible remediation (ADR 0015).

AC-Q4 (bounded reversible action only; destructive not representable),
AC-Q5 (the action taken is recorded).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.remediation import (
    RemediationAction,
    decide_remediation,
    remediation_record,
)

_BOUNDED = {"open_breaker", "close_breaker", "switch_model", "disable_ensemble", "rollback_deployment", "none"}
_DESTRUCTIVE = {"delete", "delete_stack", "terminate", "scale_up", "scale_down", "redeploy"}


class RemediationMappingTests(unittest.TestCase):
    def test_model_error_rate_opens_breaker(self) -> None:
        self.assertEqual(
            decide_remediation("ModelErrorRate", "ALARM").action,
            RemediationAction.OPEN_BREAKER,
        )

    def test_latency_switches_model(self) -> None:
        self.assertEqual(
            decide_remediation("LatencyP99", "ALARM").action,
            RemediationAction.SWITCH_MODEL,
        )

    def test_cost_disables_ensemble(self) -> None:
        self.assertEqual(
            decide_remediation("CostPerClaim", "ALARM").action,
            RemediationAction.DISABLE_ENSEMBLE,
        )

    def test_bake_alarm_rolls_back(self) -> None:
        self.assertEqual(
            decide_remediation("DeploymentBake", "ALARM").action,
            RemediationAction.ROLLBACK_DEPLOYMENT,
        )

    def test_non_alarm_state_takes_no_action_for_other_alarms(self) -> None:
        self.assertEqual(
            decide_remediation("LatencyP99", "OK").action, RemediationAction.NONE
        )
        self.assertEqual(
            decide_remediation("CostPerClaim", "OK").action, RemediationAction.NONE
        )

    def test_model_error_rate_recovery_closes_breaker(self) -> None:
        """Re-review #6 / AC-N4: an opened breaker was a one-way latch — no
        component ever closed it. ModelErrorRate leaving ALARM (OK, or
        INSUFFICIENT_DATA because the open breaker starved it of traffic)
        maps to the reversal; re-tripping re-opens (coarse half-open)."""
        self.assertEqual(
            decide_remediation("ModelErrorRate", "OK").action,
            RemediationAction.CLOSE_BREAKER,
        )
        self.assertEqual(
            decide_remediation("ModelErrorRate", "INSUFFICIENT_DATA").action,
            RemediationAction.CLOSE_BREAKER,
        )

    def test_unknown_alarm_is_no_action(self) -> None:
        self.assertEqual(
            decide_remediation("SomethingElse", "ALARM").action, RemediationAction.NONE
        )
        self.assertEqual(
            decide_remediation("SomethingElse", "OK").action, RemediationAction.NONE
        )


class RemediationBoundaryTests(unittest.TestCase):
    def test_action_set_is_bounded_and_reversible(self) -> None:
        values = {a.value for a in RemediationAction}
        self.assertEqual(values, _BOUNDED)
        self.assertEqual(values & _DESTRUCTIVE, set())

    def test_remediation_record_is_auditable(self) -> None:
        record = remediation_record(decide_remediation("ModelErrorRate", "ALARM", target="m1"))
        self.assertEqual(record["alarm"], "ModelErrorRate")
        self.assertEqual(record["state"], "ALARM")
        self.assertEqual(record["action"], "open_breaker")
        self.assertEqual(record["target"], "m1")


if __name__ == "__main__":
    unittest.main()
