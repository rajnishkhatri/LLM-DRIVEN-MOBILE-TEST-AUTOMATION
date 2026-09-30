"""Judge — WORKER C (stub per eval-spec §7). The offline demo replays recorded
verdicts; this stub pins the contract and the CALIBRATION GATE.

A judge that answers "faithful" every time scores ~85% on an imbalanced slice
(wrong-metric-outcome). So verdicts carry NO authority until the judge clears
TPR >= 0.9 AND TNR >= 0.9 on the 20-row human-labeled slice. Offline we have no
human labels, so the calibration gate stays closed — gate 5 asserts the guard,
not verdict quality, and the judge never sole-gates F3/F4/F5.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ..domain.types import SourceRef

RUBRIC_VERSION = "faithfulness-v1"
CALIBRATION_TPR_BAR = 0.9
CALIBRATION_TNR_BAR = 0.9


@dataclass(frozen=True)
class ClaimCheck:
    claim: str
    supported: bool
    source: SourceRef | None


@dataclass(frozen=True)
class Verdict:
    passed: bool
    rubric_version: str
    claims: tuple[ClaimCheck, ...]
    judge_model: str


class CalibrationError(RuntimeError):
    """Raised when the judge is used before it is calibrated."""


def is_calibrated() -> bool:
    """Offline there are no human labels, so the judge is never calibrated."""
    raise NotImplementedError("worker C: return False offline (no human slice)")


def judge_faithfulness(answer: str, sources: Sequence[SourceRef]) -> Verdict:
    """Claim-decomposed support check. CALIBRATION GATE: verdicts carry no
    authority until TPR and TNR >= 0.9 on the labeled slice (eval-spec §7)."""
    raise NotImplementedError("stub - offline demo replays recorded verdicts")
