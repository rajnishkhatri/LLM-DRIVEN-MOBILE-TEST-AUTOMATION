"""Omni data adapter — WORKER B (stub). Implements OmniPort over fixtures.

Scope every query by ctx.tenant (defense in depth behind the entitlement
pre-check). `force_timeout` is the fault-injection hook for gate 10 — it must
make query() raise so the guarded wrapper degrades.
"""
from __future__ import annotations

from pathlib import Path

from ..domain.types import OmniResult, RequestContext

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


class OmniAdapter:
    def __init__(self, fixtures_dir: Path = FIXTURES, force_timeout: bool = False):
        self.fixtures_dir = Path(fixtures_dir)
        self.force_timeout = force_timeout

    def query(self, ctx: RequestContext, intent: str) -> OmniResult:
        raise NotImplementedError("worker B: tenant-scoped fixture read")
