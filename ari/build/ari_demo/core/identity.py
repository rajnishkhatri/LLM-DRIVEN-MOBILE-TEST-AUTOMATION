"""Identity gate — WORKER A (stub).

Validate the signed token and stamp an immutable RequestContext. No port is
callable without one (ADR 0003 / gate 12). Use domain.tokens.verify_token for
the signature check; fail closed on anything malformed.
"""
from __future__ import annotations

from ..domain import tokens
from ..domain.types import RequestContext


def gate(raw_token: str) -> RequestContext:
    """Token string -> frozen RequestContext, or raise IdentityError."""
    raise NotImplementedError(
        "worker A: verify_token(raw_token) -> RequestContext, fail closed"
    )
