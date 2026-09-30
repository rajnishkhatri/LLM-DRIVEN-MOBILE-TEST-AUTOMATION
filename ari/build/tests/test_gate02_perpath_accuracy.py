"""Gate 2 (F1a, worker A): per-path routing accuracy reported; regression blocks
(eval-spec §9). Stage-0 metrics are asserted; the classifier path is reported
when it is implemented offline (worker C), not gated on here."""
from ari_demo.domain.types import RouteDecision
from ari_demo.router.stage0 import route_stage0


def test_stage0_path_metrics(golden, capsys):
    routable = [r for r in golden if r.expected_route is not None]
    decisions = [(r, route_stage0(r.query)) for r in routable]
    fast = [(r, d) for r, d in decisions if isinstance(d, RouteDecision)]
    coverage = len(fast) / len(routable)
    accuracy = sum(1 for r, d in fast if d.route.value == r.expected_route) / len(fast)

    with capsys.disabled():
        print(f"\n[gate2] stage0 coverage={coverage:.3f} accuracy={accuracy:.3f} "
              f"({len(fast)}/{len(routable)} routable rows decided fast)")

    assert coverage >= 0.5, f"fast-path coverage {coverage:.3f} too low (< 0.5)"
    assert accuracy >= 0.99, f"stage0 fast-path accuracy {accuracy:.3f} < 0.99"


def test_classifier_path_reported(golden, capsys):
    fell_through = [
        r for r in golden
        if r.expected_route is not None
        and not isinstance(route_stage0(r.query), RouteDecision)
    ]
    try:
        from ari_demo.model.classifier import OfflineClassifier
        clf = OfflineClassifier()
        from ari_demo.domain.types import RequestContext
        ctx = RequestContext("u", "Meridian Foods", "treasurer")
        hits = 0
        for r in fell_through:
            res = clf.classify(ctx, r.query)
            if res.route is not None and res.route.value == r.expected_route:
                hits += 1
        with capsys.disabled():
            n = len(fell_through) or 1
            print(f"[gate2] classifier recovered {hits}/{len(fell_through)} "
                  f"fall-through rows")
    except NotImplementedError:
        with capsys.disabled():
            print("[gate2] classifier: offline-not-implemented "
                  "(reported; composed proof at wave 2)")
