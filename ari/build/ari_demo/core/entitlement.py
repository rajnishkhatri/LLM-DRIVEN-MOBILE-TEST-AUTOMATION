"""Pre-model entitlement check — WORKER A (stub).

Runs BEFORE any model or adapter sees data (ADR 0003). Decides allow / narrow /
refuse by tenant + role, emits an audit event on every non-allow, and fails
closed. The model cannot leak what it never receives.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..domain.types import RequestContext, Route


@dataclass(frozen=True)
class EntitlementDecision:
    action: str  # "allow" | "narrow" | "refuse"
    scope: str   # entitlement scope string for the provenance tuple
    audit_event: Optional[str]  # set on every non-allow decision
    reason: str


def precheck(ctx: RequestContext, query: str, route: Route) -> EntitlementDecision:
    """Deterministic allow/narrow/refuse. Cross-tenant -> refuse; role-overreach
    -> narrow or refuse; in-scope -> allow. Always set audit_event on non-allow."""
    raise NotImplementedError(
        "worker A: deterministic tenant+role entitlement pre-check, fail closed"
    )
