"""Pre-model entitlement check — WORKER A.

Runs BEFORE any model or adapter sees data (ADR 0003). Decides allow / narrow /
refuse by tenant + role, emits an audit event on every non-allow, and fails
closed. The model cannot leak what it never receives.

Detection is deterministic and text-based (no model call): cross-tenant intent
(another tenant named, "other customers", "all/every tenant/company", or a
social-engineering "auditor for all tenants" claim) refuses; junior-analyst
role-overreach ("every/all user(s)" limits, "admin audit log") narrows. No
canary value is ever placed in reason/audit_event/scope.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from ..domain.types import RequestContext, Route


@dataclass(frozen=True)
class EntitlementDecision:
    action: str  # "allow" | "narrow" | "refuse"
    scope: str   # entitlement scope string for the provenance tuple
    audit_event: Optional[str]  # set on every non-allow decision
    reason: str


# Known tenants, each matched by a distinctive token. Naming a tenant OTHER
# than the caller's own is a cross-tenant reach; naming the caller's OWN tenant
# is not (an Acme user may ask about Acme).
_KNOWN_TENANTS = {
    r"\bacme\b": "Acme Corp",
    r"\bmeridian\b": "Meridian Foods",
}
# A request that reaches across the tenant boundary in words (independent of any
# named tenant).
_CROSS_TENANT = re.compile(
    r"other customers"
    r"|all tenants|every tenant"
    r"|all companies|every company"
    r"|every company's"
    r"|auditor for all"
)

# Junior-analyst overreach: org-wide limits, or the admin audit log.
_ROLE_OVERREACH = re.compile(
    r"every user|all users|for every user in the company|admin audit log"
)


def _norm(query: str) -> str:
    return " ".join(query.lower().split())


def _other_tenant_named(text: str, own_tenant: str) -> bool:
    """True iff the query names a KNOWN tenant other than the caller's own."""
    for pattern, canonical in _KNOWN_TENANTS.items():
        if canonical != own_tenant and re.search(pattern, text):
            return True
    return False


def precheck(ctx: RequestContext, query: str, route: Route) -> EntitlementDecision:
    """Deterministic allow/narrow/refuse. Cross-tenant -> refuse; role-overreach
    -> narrow; in-scope -> allow. Always set audit_event on non-allow."""
    scope = f"tenant:{ctx.tenant}/role:{ctx.role}"
    text = _norm(query)

    if _other_tenant_named(text, ctx.tenant) or _CROSS_TENANT.search(text):
        return EntitlementDecision(
            action="refuse",
            scope=scope,
            audit_event="entitlement.cross-tenant.refused",
            reason="request reaches outside the caller's tenant boundary",
        )

    if ctx.role == "junior-analyst" and _ROLE_OVERREACH.search(text):
        return EntitlementDecision(
            action="narrow",
            scope=scope,
            audit_event="entitlement.role-overreach.narrowed",
            reason="org-wide/privileged data narrowed to the caller's role scope",
        )

    return EntitlementDecision(
        action="allow",
        scope=scope,
        audit_event=None,
        reason="in-scope for tenant and role",
    )
