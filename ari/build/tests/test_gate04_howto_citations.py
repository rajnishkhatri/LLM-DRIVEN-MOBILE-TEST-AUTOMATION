"""Gate 4 (F2, worker C): how-to citation presence 100%. Synthesis of a how-to
answer must cite at least one versioned source (eval-spec §9, TC-10). Tested at
the synthesis seam with a hand-built DocsResult so it stands alone from the
docs adapter (worker B)."""
from ari_demo.core.entitlement import EntitlementDecision
from ari_demo.domain.types import DocChunk, DocsResult, Route
from ari_demo.model.model_port import OfflineModel
from ari_demo.synthesis.synthesis import synthesize


def _allow(ctx):
    return EntitlementDecision(
        action="allow",
        scope=f"tenant:{ctx.tenant}/role:{ctx.role}",
        audit_event=None,
        reason="in-scope",
    )


def test_howto_answer_carries_versioned_citations(treasurer_ctx):
    docs = DocsResult(
        chunks=(
            DocChunk("kb-add-bank-connection", "kb-2026-09-15",
                     "1. Go to Settings -> Connections -> Banks. 2. Add connection."),
        )
    )
    resp = synthesize(
        route=Route.HOWTO,
        ctx=treasurer_ctx,
        entitlement=_allow(treasurer_ctx),
        model=OfflineModel(),
        docs=docs,
    )
    assert resp.provenance.sources, "how-to answer must cite a source"
    for s in resp.provenance.sources:
        assert s.version, "citations must carry a version id (not mutable pointers)"
    assert resp.provenance.is_complete()
