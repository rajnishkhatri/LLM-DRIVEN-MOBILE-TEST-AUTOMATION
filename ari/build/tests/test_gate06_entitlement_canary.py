"""Gate 6 (F3, worker A): tenant + role canary probes, 0 violations, build-failing
and permanent. The pre-model entitlement check refuses cross-tenant and
narrows/refuses role-overreach, always with an audit event, before any adapter
is reached (ADR 0003 / eval-spec §9)."""
from canaries import CANARY_ACME

from ari_demo.core.entitlement import precheck
from ari_demo.domain.types import Route


def test_cross_tenant_refused_before_model(golden, treasurer_ctx):
    cross = [r for r in golden if r.entitlement == "cross-tenant"]
    assert cross, "expected cross-tenant probe rows"
    for r in cross:
        d = precheck(treasurer_ctx, r.query, Route.DATA)
        assert d.action == "refuse", f"{r.id} must be refused, got {d.action}"
        assert d.audit_event, f"{r.id} must emit an audit event"
        # the canary lives only in the other tenant's fixtures; a refusal that
        # never fetches cannot contain it
        blob = f"{d.reason} {d.audit_event} {d.scope}"
        assert CANARY_ACME not in blob, f"{r.id} leaked the cross-tenant canary"


def test_role_overreach_narrowed_or_refused(golden, junior_ctx):
    role = [r for r in golden if r.entitlement == "role-overreach"]
    assert role, "expected role-overreach probe rows"
    for r in role:
        d = precheck(junior_ctx, r.query, Route.DATA)
        assert d.action in ("narrow", "refuse"), (
            f"{r.id} must narrow or refuse for a junior-analyst, got {d.action}"
        )
        assert d.audit_event, f"{r.id} must emit an audit event"


def test_in_scope_allowed(golden, treasurer_ctx):
    in_scope = [r for r in golden
                if r.entitlement == "in-scope" and r.intent == "data"][:3]
    for r in in_scope:
        d = precheck(treasurer_ctx, r.query, Route.DATA)
        assert d.action == "allow", f"{r.id} is in-scope and must be allowed"
        assert d.scope, "an allow decision still records an entitlement scope"
