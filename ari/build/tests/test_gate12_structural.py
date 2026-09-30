"""Gate 12 (all classes, worker A): structural invariants — the identity gate
stamps a frozen RequestContext and fails closed; no port is callable without a
RequestContext; imports point inward (eval-spec §9, ADR 0001/0003)."""
import dataclasses
import inspect
import re
from pathlib import Path

import pytest

from ari_demo.domain import tokens
from ari_demo.domain.types import IdentityError, ModelRequest, RequestContext
from ari_demo.ports import ports

PKG_ROOT = Path(ports.__file__).resolve().parents[1]


def test_identity_gate_stamps_frozen_context():
    from ari_demo.core.identity import gate

    ctx = gate(tokens.mint_token("treasurer@Meridian Foods", "Meridian Foods",
                                 "treasurer"))
    assert isinstance(ctx, RequestContext)
    assert ctx.tenant == "Meridian Foods" and ctx.role == "treasurer"
    with pytest.raises(dataclasses.FrozenInstanceError):
        ctx.tenant = "Acme Corp"  # type: ignore[misc]


def test_identity_gate_fails_closed_on_tampered_token():
    from ari_demo.core.identity import gate

    with pytest.raises(IdentityError):
        gate("not-a-valid-token.deadbeef")


def test_no_context_no_call():
    """Every port's method takes a RequestContext, or a ModelRequest that
    carries one. No adapter is callable without an identity."""
    checks = {
        "OmniPort": "query",
        "DocsPort": "retrieve",
        "TicketPort": "create",
        "ActionPort": "execute",
        "ClassifierPort": "classify",
        "ModelPort": "generate",
    }
    for port_name, method_name in checks.items():
        proto = getattr(ports, port_name)
        sig = inspect.signature(getattr(proto, method_name))
        anns = [p.annotation for p in sig.parameters.values()]
        # PEP 563: `from __future__ import annotations` makes these lazy
        # strings, so match the class, its __name__, or the string form.
        identity = {RequestContext, ModelRequest, "RequestContext", "ModelRequest"}
        carries_identity = any(
            a in identity or getattr(a, "__name__", "") in identity
            for a in anns
        )
        assert carries_identity, (
            f"{port_name}.{method_name} must take a RequestContext/ModelRequest"
        )


def test_imports_point_inward():
    """domain/ imports nothing outward; ports/ may import domain only."""
    outward = ("adapters", "router", "core", "synthesis", "model",
               "resilience", "app")
    forbidden = {
        "domain": outward + ("ports",),  # domain is innermost
        "ports": outward,                # ports may import domain, nothing else
    }
    for layer, banned in forbidden.items():
        for py in (PKG_ROOT / layer).glob("*.py"):
            text = py.read_text()
            for mod in banned:
                pat = rf"(from\s+\.\.?{mod}[\s.]|import\s+ari_demo\.{mod})"
                assert not re.search(pat, text), (
                    f"{layer}/{py.name} imports outward module '{mod}' "
                    "(imports must point inward)"
                )
