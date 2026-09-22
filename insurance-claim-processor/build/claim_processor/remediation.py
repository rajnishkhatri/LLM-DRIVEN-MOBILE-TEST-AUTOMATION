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
    CLOSE_BREAKER = "close_breaker"
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

# Alarm leaving ALARM → the reversal of its action (AC-N4, re-review #6).
# An open breaker starves its model of traffic, so ModelErrorRate recovers to
# INSUFFICIENT_DATA (no samples), not only OK — both close the breaker; if the
# fault persists, the next real traffic re-fires ALARM and re-opens (a coarse
# half-open: the alarm's own evaluation window is the probe budget).
_RECOVERY_ACTIONS: dict[str, RemediationAction] = {
    "ModelErrorRate": RemediationAction.CLOSE_BREAKER,
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
    """Map an alarm state to a bounded action or its recovery reversal."""
    if alarm_state == "ALARM":
        action = _ALARM_ACTIONS.get(alarm_name, RemediationAction.NONE)
    elif alarm_state in ("OK", "INSUFFICIENT_DATA"):
        action = _RECOVERY_ACTIONS.get(alarm_name, RemediationAction.NONE)
    else:
        action = RemediationAction.NONE
    return RemediationDecision(alarm_name, alarm_state, action, target)


def remediation_record(decision: RemediationDecision) -> dict[str, str | None]:
    """Auditable record of an automated change (AC-Q5)."""
    return {
        "alarm": decision.alarm,
        "state": decision.state,
        "action": decision.action.value,
        "target": decision.target,
    }
