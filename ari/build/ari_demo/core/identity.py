"""Identity gate — WORKER A.

Validate the signed token and stamp an immutable RequestContext. No port is
callable without one (ADR 0003 / gate 12). Uses domain.tokens.verify_token for
the signature + required-claim check; fails closed on anything malformed
(verify_token raises IdentityError, which we let propagate).
"""
from __future__ import annotations

from ..domain import tokens
from ..domain.types import RequestContext


def gate(raw_token: str) -> RequestContext:
    """Token string -> frozen RequestContext, or raise IdentityError.

    verify_token validates the HMAC signature and the required claims
    (user/tenant/role); any defect raises IdentityError. A tampered or
    malformed token therefore never yields a context — fail closed.
    """
    claims = tokens.verify_token(raw_token)
    return RequestContext(
        user=claims["user"],
        tenant=claims["tenant"],
        role=claims["role"],
        conversation_id=claims.get("conversation_id", "conv-0"),
        turn_id=claims.get("turn_id", "t0"),
    )
