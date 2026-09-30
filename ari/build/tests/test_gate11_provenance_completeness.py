"""Gate 11 (F7, WAVE 2): provenance completeness on 100% of answers — including
refusals, clarifications and degraded answers — across the wired pipeline. The
record IS the truth; a stochastic answer that cannot be reconstructed is a
breach of the audit posture (eval-spec §9, TC-01)."""
from conftest import ctx_for


def test_every_answer_carries_a_complete_provenance_tuple(pipeline, golden):
    incomplete = []
    for r in golden:
        resp = pipeline.handle(r.query, ctx_for(r))
        if not resp.provenance.is_complete():
            incomplete.append(r.id)
    assert not incomplete, f"answers missing a complete provenance tuple: {incomplete}"


def test_degraded_answer_still_carries_provenance(pipeline, golden):
    r = next(rr for rr in golden if rr.id == "Q-001")
    resp = pipeline.handle(r.query, ctx_for(r), inject_timeout=True)
    assert resp.degraded is True
    assert resp.ticket_offer is True
    assert resp.provenance.is_complete()


def test_happy_data_path_tuple_is_populated(pipeline, golden):
    r = next(rr for rr in golden if rr.id == "Q-001")
    resp = pipeline.handle(r.query, ctx_for(r))
    p = resp.provenance
    assert p.route.value == "DATA"
    assert p.sources, "a data answer cites its Omni source + version"
    assert p.model_version and p.prompt_version
    assert p.entitlement_scope
    assert p.rule_ids, "stage-0 rule ids are part of provenance"
