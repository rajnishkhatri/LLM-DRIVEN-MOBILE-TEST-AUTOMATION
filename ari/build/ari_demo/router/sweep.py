"""Threshold sweep — WORKER A (stub). eval-spec §6.

Grid-sweep theta in [0.3, 0.9] x margin in [0.1, 0.5] over the golden set;
choose MAXIMUM fast-path coverage subject to fast-path precision >= 99%; write
`sweep-report.md` next to this package's build root and expose the chosen
values so stage0 can import them.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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


def run_sweep(rows) -> SweepResult:
    """Return the chosen (theta, margin) and its coverage/precision."""
    raise NotImplementedError("worker A: grid sweep over the golden set")


def write_report(path: Path = REPORT_PATH) -> SweepResult:
    """Run the sweep and commit sweep-report.md. Returns the chosen result."""
    raise NotImplementedError("worker A: emit sweep-report.md")
