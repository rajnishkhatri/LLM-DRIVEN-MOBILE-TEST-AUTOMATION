"""Threshold sweep — WORKER A. eval-spec §6.

Grid-sweep theta in [0.3, 0.9] x margin in [0.1, 0.5] over the golden set,
measuring the *actual* stage-0 decision function at each grid point. Choose the
point with MAXIMUM fast-path coverage subject to fast-path precision >= 0.99
over the routable rows (expected route not null); break ties toward the most
stringent (largest theta, then largest margin) so the committed thresholds are
as conservative as full coverage allows.

Run as a module to (re)generate the committed report:
    python3 -m ari_demo.router.sweep
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..domain.types import RouteDecision
from ..evals.golden_set import load_golden_set
from .stage0 import route_stage0

# Report lives at ari/build/sweep-report.md (committed with the chosen values).
REPORT_PATH = Path(__file__).resolve().parents[2] / "sweep-report.md"

THETA_GRID = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
MARGIN_GRID = [0.1, 0.2, 0.3, 0.4, 0.5]
PRECISION_BAR = 0.99


@dataclass(frozen=True)
class SweepResult:
    theta: float
    margin: float
    coverage: float
    precision: float


def _measure(rows, theta: float, margin: float) -> SweepResult:
    routable = [r for r in rows if r.expected_route is not None]
    decided = correct = 0
    for r in routable:
        d = route_stage0(r.query, threshold=theta, margin=margin)
        if isinstance(d, RouteDecision):
            decided += 1
            if d.route.value == r.expected_route:
                correct += 1
    coverage = decided / len(routable) if routable else 0.0
    precision = (correct / decided) if decided else 0.0
    return SweepResult(theta, margin, coverage, precision)


def _grid(rows) -> list[SweepResult]:
    return [
        _measure(rows, theta, margin)
        for theta in THETA_GRID
        for margin in MARGIN_GRID
    ]


def run_sweep(rows) -> SweepResult:
    """Return the chosen (theta, margin) and its coverage/precision."""
    feasible = [r for r in _grid(rows) if r.precision >= PRECISION_BAR]
    if not feasible:
        raise RuntimeError("no (theta, margin) meets the precision bar")
    # max coverage; tie-break: largest theta, then largest margin (stringent).
    return max(feasible, key=lambda r: (r.coverage, r.theta, r.margin))


def write_report(path: Path = REPORT_PATH) -> SweepResult:
    """Run the sweep and write sweep-report.md. Returns the chosen result."""
    rows = load_golden_set()
    grid = _grid(rows)
    feasible = [r for r in grid if r.precision >= PRECISION_BAR]
    chosen = max(feasible, key=lambda r: (r.coverage, r.theta, r.margin))
    n_routable = len([r for r in rows if r.expected_route is not None])
    n_decided = round(chosen.coverage * n_routable)

    lines: list[str] = []
    lines.append("# Stage-0 threshold sweep report\n")
    lines.append(
        "Worker A. Grid-sweep of the stage-0 router's THRESHOLD (theta) and "
        "MARGIN over the 72-row golden set, measured against the actual "
        "`route_stage0` decision function.\n"
    )
    lines.append(
        "Objective: **maximum fast-path coverage subject to fast-path "
        f"precision >= {PRECISION_BAR:.2f}** over the "
        f"{n_routable} routable rows (expected route not null). Ties broken "
        "toward the most stringent (largest theta, then largest margin).\n"
    )
    lines.append(f"CHOSEN theta={chosen.theta:g} margin={chosen.margin:g}\n")
    lines.append(
        f"At the chosen point: coverage={chosen.coverage:.3f} "
        f"({n_decided}/{n_routable} routable rows decided on the fast path), "
        f"precision={chosen.precision:.3f}. All 8 route=null rows fall through "
        "(gate 3), so they never enter this table.\n"
    )
    lines.append("## Grid (precision · coverage) per (theta, margin)\n")
    header = "| theta \\ margin | " + " | ".join(
        f"{m:g}" for m in MARGIN_GRID
    ) + " |"
    sep = "|" + "---|" * (len(MARGIN_GRID) + 1)
    lines.append(header)
    lines.append(sep)
    by_pt = {(r.theta, r.margin): r for r in grid}
    for theta in THETA_GRID:
        cells = []
        for margin in MARGIN_GRID:
            r = by_pt[(theta, margin)]
            mark = " *" if (r.theta, r.margin) == (chosen.theta, chosen.margin) else ""
            cells.append(f"{r.precision:.2f}·{r.coverage:.2f}{mark}")
        lines.append(f"| {theta:g} | " + " | ".join(cells) + " |")
    lines.append(
        "\nEach cell is `precision·coverage`; `*` marks the chosen point. "
        "Precision holds at 1.00 across the grid (the rules only ever fire one "
        "capability per row; the Q-013/014/015 traps resolve DATA 0.8 vs "
        "TICKET 0.2 by a 0.6 margin), so coverage is the only free variable. "
        "theta=0.9 drops the DATA rows (weight 0.8 < 0.9) and margin>0.6 would "
        "drop the traps; the chosen point is the most stringent that still "
        "keeps full coverage.\n"
    )
    Path(path).write_text("\n".join(lines))
    return chosen


if __name__ == "__main__":  # pragma: no cover - operator entrypoint
    result = write_report()
    print(
        f"CHOSEN theta={result.theta:g} margin={result.margin:g} "
        f"coverage={result.coverage:.3f} precision={result.precision:.3f}"
    )
    print(f"report written to {REPORT_PATH}")
