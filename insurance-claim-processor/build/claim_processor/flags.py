"""Feature-flag evaluation for progressive delivery (ADR 0010).

Flags fail to the **conservative** default when absent or when the source is
unavailable (AC-M1). A/B assignment is deterministic on `claim_key` so a
re-run of the same claim gets the same variant — C9 idempotency is preserved
(AC-M2). Kill switches force a candidate model or the ensemble OFF within one
poll interval, no deployment (AC-M5).
"""

from __future__ import annotations

import hashlib
from typing import Any

_SAFE_DEFAULTS: dict[str, Any] = {
    "candidate_rollout_pct": 0,  # 0% → everyone on control
    "ensemble_enabled": False,  # off by default (cost — ADR 0013)
    "breaker_enabled": True,  # protection on by default
    "degradation_enabled": True,  # graceful degradation on by default
}


def flag(flags: dict[str, Any] | None, name: str) -> Any:
    """Return the flag value, or its safe default if absent/unavailable."""
    if not isinstance(flags, dict) or name not in flags:
        return _SAFE_DEFAULTS.get(name)
    return flags[name]


def _bucket(claim_key: str) -> int:
    """Stable 0–99 bucket from the claim key (deterministic A/B — AC-M2)."""
    digest = hashlib.sha256(claim_key.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 100


def assign_variant(claim_key: str, flags: dict[str, Any] | None) -> str:
    """`control` | `candidate`, deterministic on `claim_key`."""
    if flag(flags, "kill_switch_candidate"):
        return "control"
    pct = flag(flags, "candidate_rollout_pct") or 0
    try:
        pct = int(pct)
    except (TypeError, ValueError):
        pct = 0
    return "candidate" if _bucket(claim_key) < pct else "control"


def ensemble_enabled(flags: dict[str, Any] | None) -> bool:
    """Ensemble is on only when explicitly enabled and not kill-switched."""
    if flag(flags, "kill_switch_ensemble"):
        return False
    return bool(flag(flags, "ensemble_enabled"))
