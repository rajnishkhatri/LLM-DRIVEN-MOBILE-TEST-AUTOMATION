"""Stage-1 classifier — WORKER C (stub). ADR 0001 / HANDOVER §9.

A port (ClassifierPort). Offline default = deterministic fixture-backed
classifier: recorded intents for the golden set's fall-through rows; below the
confidence floor -> clarify or ticket, never a guess. The Agent Squad library
is the LIVE adapter, referenced here in comments/config, NOT installed.
"""
from __future__ import annotations

from ..domain.types import ClassifierResult, RequestContext

CLASSIFIER_CONFIDENCE_FLOOR: float = 0.6


class OfflineClassifier:
    """Deterministic ClassifierPort over recorded intents."""

    def classify(self, ctx: RequestContext, utterance: str) -> ClassifierResult:
        raise NotImplementedError("worker C: recorded-intent classifier")
