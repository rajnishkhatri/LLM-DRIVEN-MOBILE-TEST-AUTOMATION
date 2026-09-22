"""Circuit-breaker decision — measured signal, not a naive counter (ADR 0012).

`decide_state` is a **pure** function of an injected `BreakerSignal` and the
current state (passed in, never stored) — there is no in-process breaker, so
independent Step Functions executions see a consistent state via the shared
AppConfig flag (AC-N3). A window of slow successes (low error rate) never opens
the breaker (AC-N1); an undersized window holds state rather than tripping on
noise (clinic §2).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from claim_processor.flags import flag

CLOSED = "closed"
OPEN = "open"
HALF_OPEN = "half_open"


@dataclass(frozen=True)
class BreakerSignal:
    error_rate: float  # fraction of calls that failed (throttle+timeout+invalid)
    sample_size: int  # calls observed in the window


@dataclass(frozen=True)
class BreakerConfig:
    open_threshold: float = 0.5  # error rate that opens a closed breaker
    close_threshold: float = 0.1  # error rate under which it recovers
    min_samples: int = 20  # window must be honest before it can trip


def decide_state(signal: BreakerSignal, current: str, config: BreakerConfig) -> str:
    """Next breaker state given the measured signal and current state."""
    if signal.sample_size < config.min_samples:
        return current  # not enough data to trip or clear (AC-N1)
    if current == CLOSED:
        return OPEN if signal.error_rate >= config.open_threshold else CLOSED
    if current == OPEN:
        # Recovery detected → probe (half-open) before fully closing (AC-N4).
        return HALF_OPEN if signal.error_rate < config.close_threshold else OPEN
    if current == HALF_OPEN:
        return CLOSED if signal.error_rate < config.close_threshold else OPEN
    return current


def breaker_open(flags: dict[str, Any] | None, model_id: str) -> bool:
    """Read the shared breaker state for a model (AC-N2/N3).

    The list of open models is the AppConfig flag flipped by remediation
    (ADR 0015). Disabled breaker (kill switch) never reports open.
    """
    if not flag(flags, "breaker_enabled"):
        return False
    open_models = flag(flags, "breaker_open_models") or []
    return model_id in open_models
