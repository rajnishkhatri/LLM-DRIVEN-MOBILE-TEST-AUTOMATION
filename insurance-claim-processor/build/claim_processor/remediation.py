"""Automated remediation — bounded, reversible actions only (ADR 0015).

`decide_remediation` is a **pure** mapping from a CloudWatch alarm in ALARM to
one bounded, reversible action (flip an AppConfig flag, or roll back an
AppConfig deployment). Destructive or scaling actions are **not representable**
in the action set (AC-Q4). Every decision is recorded for audit (AC-Q5). The
remediation Lambda applies the chosen action against AppConfig; this module
owns only the decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RemediationAction(str, Enum):
    OPEN_BREAKER = "open_breaker"
    SWITCH_MODEL = "switch_model"
    DISABLE_ENSEMBLE = "disable_ensemble"
    ROLLBACK_DEPLOYMENT = "rollback_deployment"
    NONE = "none"


# Alarm name → bounded action. Unknown alarms map to NONE (fail safe).
_ALARM_ACTIONS: dict[str, RemediationAction] = {
    "ModelErrorRate": RemediationAction.OPEN_BREAKER,
    "LatencyP99": RemediationAction.SWITCH_MODEL,
    "CostPerClaim": RemediationAction.DISABLE_ENSEMBLE,
    "DeploymentBake": RemediationAction.ROLLBACK_DEPLOYMENT,
}


@dataclass(frozen=True)
class RemediationDecision:
    alarm: str
    state: str
    action: RemediationAction
    target: str | None = None


def decide_remediation(
    alarm_name: str,
    alarm_state: str,
    *,
    target: str | None = None,
) -> RemediationDecision:
    """Map an alarm state to a bounded action. Only ALARM triggers action."""
    if alarm_state != "ALARM":
        return RemediationDecision(alarm_name, alarm_state, RemediationAction.NONE, target)
    action = _ALARM_ACTIONS.get(alarm_name, RemediationAction.NONE)
    return RemediationDecision(alarm_name, alarm_state, action, target)


def remediation_record(decision: RemediationDecision) -> dict[str, str | None]:
    """Auditable record of an automated change (AC-Q5)."""
    return {
        "alarm": decision.alarm,
        "state": decision.state,
        "action": decision.action.value,
        "target": decision.target,
    }
