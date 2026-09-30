"""Guarded-call wrapper — WORKER B. One wrapper for every adapter call
(ADR 0001): C7 timeout budget, C11 degradation ladder (ticket stream is the
floor), C2 single jittered retry on idempotent reads only, C9 handled in the
ticket adapter. Circuit breaker (C1) is deferred; this is where it slots later.

The degraded path is DETERMINISTIC — the model never writes it, so DEGRADED_COPY
is string-assertable (gate 10). Jitter is deterministic and bounded (a seeded
RNG, ≤ a few ms) so the offline gates stay fast.
"""
from __future__ import annotations

import random
import time

from ..domain.types import AriResponse, Provenance, RequestContext, Route

TIMEOUT_BUDGET_S: float = 2.0
MAX_RETRIES: int = 1  # single retry, idempotent reads only (C2)

# Deterministic, bounded jitter (C2). Seeded so runs are reproducible and the
# sleep is capped at a couple of milliseconds — never a real backoff wait.
_JITTER = random.Random(0xA71)
_JITTER_MAX_S: float = 0.002

# Deterministic degraded copy (C11). Must state the honest failure and offer a
# ticket — no invented numbers (F6): no "$", no "USD", no figures.
DEGRADED_COPY: str = (
    "I could not reach the data service just now, so I will not guess at the "
    "numbers. I can open a support ticket so someone follows up — want me to?"
)

# Degraded provenance is still complete (gate 11 covers degraded answers).
_DEGRADED_MODEL_VERSION = "none-degraded"
_DEGRADED_PROMPT_VERSION = "degrade-v1"


class GuardTimeout(Exception):
    """Raised when an adapter call exceeds its timeout budget (C7)."""


def _jittered_pause() -> None:
    time.sleep(_JITTER.uniform(0.0, _JITTER_MAX_S))


def guarded_read(fn, *, retries: int = MAX_RETRIES):
    """Run an idempotent read under the C7 timeout budget with one jittered
    retry (C2). Raises GuardTimeout when the budget is exhausted; non-timeout
    exceptions propagate unchanged. Deterministic and fast."""
    attempts = retries + 1  # initial call + `retries` retries
    last_exc: Exception | None = None

    for attempt in range(attempts):
        started = time.monotonic()
        try:
            result = fn()
        except TimeoutError as exc:
            last_exc = exc
        else:
            # Treat an over-budget read as a timeout too (C7).
            if (time.monotonic() - started) > TIMEOUT_BUDGET_S:
                last_exc = TimeoutError("exceeded timeout budget")
            else:
                return result

        # A timeout on a non-final attempt gets one jittered retry (C2).
        if attempt < attempts - 1:
            _jittered_pause()

    raise GuardTimeout("timeout budget exhausted after retry") from last_exc


def degrade(route: Route, ctx: RequestContext) -> AriResponse:
    """Build the deterministic degraded response (C11): honest copy + ticket
    offer + a COMPLETE (degraded) provenance tuple. The model writes none of
    this."""
    provenance = Provenance(
        route=route,
        sources=(),
        confidence=0.0,
        model_version=_DEGRADED_MODEL_VERSION,
        prompt_version=_DEGRADED_PROMPT_VERSION,
        entitlement_scope=f"tenant:{ctx.tenant}/role:{ctx.role}",
        rule_ids=(),
    )
    return AriResponse(
        text=DEGRADED_COPY,
        provenance=provenance,
        route=route,
        degraded=True,
        ticket_offer=True,
        audit_event="degraded_ticket_offer",
    )
