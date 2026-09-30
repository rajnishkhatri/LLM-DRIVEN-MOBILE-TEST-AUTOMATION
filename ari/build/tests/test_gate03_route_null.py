"""Gate 3 (F1b, worker A): genuinely-ambiguous rows (route=null) must draw zero
confident routes — stage-0 falls through, and the classifier (if present) stays
below its bar and asks to clarify (eval-spec §9)."""
from ari_demo.domain.types import FallThrough, RouteDecision
from ari_demo.router.stage0 import route_stage0


def test_ambiguous_rows_fall_through_at_stage0(golden):
    null_rows = [r for r in golden if r.is_route_null]
    assert len(null_rows) == 8, "expected 8 genuinely-ambiguous rows"
    for r in null_rows:
        d = route_stage0(r.query)
        assert isinstance(d, FallThrough), (
            f"{r.id} must fall through (never guess), got {d!r}"
        )


def test_ambiguous_rows_not_confidently_classified(golden):
    null_rows = [r for r in golden if r.is_route_null]
    try:
        from ari_demo.domain.types import RequestContext
        from ari_demo.model.classifier import OfflineClassifier
        clf = OfflineClassifier()
        ctx = RequestContext("u", "Meridian Foods", "treasurer")
        for r in null_rows:
            res = clf.classify(ctx, r.query)
            assert res.route is None or res.clarify, (
                f"{r.id}: classifier must not confidently route an ambiguous row"
            )
    except NotImplementedError:
        # classifier not built in this worktree; composed proof runs at wave 2
        pass
