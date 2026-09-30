"""Guarded-call wrapper — WORKER B (stub). One wrapper for every adapter call
(ADR 0001): C7 timeout budget, C11 degradation ladder (ticket stream is the
floor), C2 single jittered retry on idempotent reads only, C9 handled in the
ticket adapter. Circuit breaker (C1) is deferred; this is where it slots later.

The degraded path is DETERMINISTIC — the model never writes it, so DEGRADED_COPY
is string-assertable (gate 10). Worker B sets the final copy; the placeholder
keeps the symbol importable.
"""
from __future__ import annotations

from ..domain.types import AriResponse, RequestContext, Route

TIMEOUT_BUDGET_S: float = 2.0
MAX_RETRIES: int = 1  # single retry, idempotent reads only (C2)

# Deterministic degraded copy (worker B finalizes). Must state the honest
# failure and offer a ticket — no invented numbers (F6).
DEGRADED_COPY: str = (
    "I could not reach the data service just now, so I will not guess at the "
    "numbers. I can open a support ticket so someone follows up — want me to?"
)


class GuardTimeout(Exception):
    """Raised when an adapter call exceeds its timeout budget (C7)."""


def guarded_read(fn, *, retries: int = MAX_RETRIES):
    """Run an idempotent read under the timeout budget with one jittered retry.
    Raises GuardTimeout when the budget is exhausted."""
    raise NotImplementedError("worker B: C7 timeout + C2 single jittered retry")


def degrade(route: Route, ctx: RequestContext) -> AriResponse:
    """Build the deterministic degraded response: honest copy + ticket offer +
    a COMPLETE (degraded) provenance tuple (gate 11 covers degraded answers)."""
    raise NotImplementedError("worker B: deterministic degrade + ticket offer")
