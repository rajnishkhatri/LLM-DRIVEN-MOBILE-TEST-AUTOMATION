"""Gate 1 (F1a, worker A): fast-path routing precision >= 99% at the swept
theta/margin, with the sweep report committed (eval-spec §6, §9)."""
import re

from ari_demo.domain.types import RouteDecision
from ari_demo.router import stage0, sweep
from ari_demo.router.stage0 import route_stage0


def test_sweep_report_committed_and_values_match():
    assert sweep.REPORT_PATH.exists(), "sweep-report.md must be committed (gate 1)"
    text = sweep.REPORT_PATH.read_text()
    m = re.search(r"CHOSEN\s+theta=([0-9.]+)\s+margin=([0-9.]+)", text)
    assert m, "sweep-report.md must carry a 'CHOSEN theta=<x> margin=<y>' line"
    assert abs(stage0.THRESHOLD - float(m.group(1))) < 1e-9, "THRESHOLD != report"
    assert abs(stage0.MARGIN - float(m.group(2))) < 1e-9, "MARGIN != report"


def test_fast_path_precision(golden):
    routable = [r for r in golden if r.expected_route is not None]
    decided = correct = 0
    misroutes = []
    for r in routable:
        d = route_stage0(r.query)
        if isinstance(d, RouteDecision):
            decided += 1
            if d.route.value == r.expected_route:
                correct += 1
            else:
                misroutes.append((r.id, r.expected_route, d.route.value))
    assert decided > 0, "stage-0 must decide rows on the fast path"
    precision = correct / decided
    assert precision >= 0.99, (
        f"fast-path precision {precision:.4f} < 0.99; misroutes={misroutes}"
    )
