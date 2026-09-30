"""Omni data adapter — WORKER B. Implements OmniPort over fixtures.

Scope every query by ctx.tenant (defense in depth behind the entitlement
pre-check): a Meridian ctx reads only omni_meridian.json, an Acme ctx only
omni_acme.json — never the other tenant's file. `force_timeout` is the
fault-injection hook for gate 10 — it makes query() raise TimeoutError so the
guarded wrapper degrades.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..domain.types import OmniResult, OmniRow, RequestContext, SourceRef

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"

# Tenant -> fixture file. Strictly scoped; an unknown tenant has no fixture.
_TENANT_FILES = {
    "Meridian Foods": "omni_meridian.json",
    "Acme Corp": "omni_acme.json",
}


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


class OmniAdapter:
    def __init__(self, fixtures_dir: Path = FIXTURES, force_timeout: bool = False):
        self.fixtures_dir = Path(fixtures_dir)
        self.force_timeout = force_timeout

    def _load_tenant(self, tenant: str) -> dict:
        fname = _TENANT_FILES.get(tenant)
        if fname is None:
            raise KeyError(f"no Omni fixture for tenant {tenant!r}")
        return json.loads((self.fixtures_dir / fname).read_text())

    def query(self, ctx: RequestContext, intent: str) -> OmniResult:
        # Fault-injection hook (gate 10): drive the guarded wrapper's C7 path.
        if self.force_timeout:
            raise TimeoutError("injected Omni timeout")

        data = self._load_tenant(ctx.tenant)
        source_version = data.get("source_version", "unknown")
        needle = _norm(intent)

        best_row = None
        best_score = 0
        for row in data.get("rows", []):
            metric = row.get("metric", "")
            score = 0
            if metric and _norm(metric) == needle:
                score = max(score, 1000)  # exact metric id wins outright
            for kw in row.get("keywords", []):
                nkw = _norm(kw)
                if nkw and (nkw in needle or needle in nkw):
                    score = max(score, len(nkw))
            if score > best_score:
                best_score, best_row = score, row

        if best_row is None:
            # No match: an honest empty result, still tenant-scoped + versioned.
            return OmniResult(
                rows=(),
                source=SourceRef("omni", f"{ctx.tenant}:no-match", source_version),
            )

        omni_row = OmniRow(
            tenant=ctx.tenant,
            metric=best_row.get("metric", ""),
            value=best_row.get("value", ""),
            memo=best_row.get("memo", ""),
            version=source_version,
        )
        return OmniResult(
            rows=(omni_row,),
            source=SourceRef(
                "omni", f"{ctx.tenant}:{omni_row.metric}", source_version
            ),
        )
