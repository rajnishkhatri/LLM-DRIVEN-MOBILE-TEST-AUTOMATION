"""Signed-token codec — FROZEN shared primitive (ADR 0003).

The identity gate (core/identity.py, worker A) *validates* a token and stamps a
RequestContext; this module is only the sign/verify mechanism, shared so tests
and the gate agree on the format. A demo HMAC stands in for the real signing
authority — the point is that a tampered token fails closed, not the crypto.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json

from .types import IdentityError

# Demo signing key. NOT a production secret — the live gateway verifies a real
# JWT/enterprise token; here we only need tamper-evidence for the offline gate.
DEMO_SECRET = b"ari-demo-signing-key-not-for-production"

REQUIRED_CLAIMS = ("user", "tenant", "role")


def _sign(raw: bytes) -> str:
    return hmac.new(DEMO_SECRET, raw, hashlib.sha256).hexdigest()


def mint_token(
    user: str,
    tenant: str,
    role: str,
    conversation_id: str = "conv-0",
    turn_id: str = "t0",
) -> str:
    """Produce a signed token string `<b64(payload)>.<hexsig>`."""
    payload = {
        "user": user,
        "tenant": tenant,
        "role": role,
        "conversation_id": conversation_id,
        "turn_id": turn_id,
    }
    raw = base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True).encode())
    return f"{raw.decode()}.{_sign(raw)}"


def verify_token(token: str) -> dict:
    """Return the claims dict, or raise IdentityError. Fails closed."""
    if not isinstance(token, str) or token.count(".") != 1:
        raise IdentityError("malformed token")
    raw_str, sig = token.split(".")
    raw = raw_str.encode()
    if not hmac.compare_digest(sig, _sign(raw)):
        raise IdentityError("bad signature (tampered token)")
    try:
        claims = json.loads(base64.urlsafe_b64decode(raw))
    except Exception as exc:  # noqa: BLE001 - any decode failure is a bad token
        raise IdentityError("undecodable payload") from exc
    for claim in REQUIRED_CLAIMS:
        if not claims.get(claim):
            raise IdentityError(f"missing required claim: {claim}")
    return claims
