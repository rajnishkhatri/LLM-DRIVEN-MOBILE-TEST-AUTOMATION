"""CloudWatch custom metrics via EMF, through the safe logger (ADR 0015).

Metrics are emitted as Embedded Metric Format JSON on the log stream — no
`cloudwatch:PutMetricData` call and no IAM beyond CloudWatch Logs (AC-Q1).
Emission goes through the redacting logger so no raw PII rides alongside a
metric (AC-Q2). These metrics are also the breaker's trip signal (ADR 0012)
and the A/B comparison signal (ADR 0010).
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from claim_processor.logging_safe import redact

DEFAULT_NAMESPACE = "ClaimProcessor"


def _redact_strings(value: Any) -> Any:
    """Apply the AC-H1 redaction to string leaves only.

    EMF numeric fields (Timestamp is a 13-digit epoch-ms, token counts, dollar
    amounts) must survive — running the message-level PAN regex over the whole
    JSON would corrupt them (a 13-digit timestamp looks like a card number).
    So string fields are redacted with the shared `logging_safe.redact`
    primitive and numbers are left intact, keeping the metric valid (AC-Q2).
    """
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, dict):
        return {k: _redact_strings(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_strings(v) for v in value]
    return value


class Metric:
    """Metric-name vocabulary (the signals the clinic §2 named)."""

    LATENCY_MS = "LatencyMs"
    ERRORS = "Errors"
    GUARDRAIL_INTERVENED = "GuardrailIntervened"
    UNGROUNDED = "Ungrounded"
    HUMAN_REVIEW = "HumanReview"
    ENSEMBLE_DISAGREEMENT = "EnsembleDisagreement"
    DEGRADATION = "Degradation"
    BREAKER_TRANSITION = "BreakerTransition"
    COST_USD = "CostUsd"
    CONFIG_REJECTED = "ConfigRejected"


def build_emf(
    namespace: str,
    metrics: dict[str, tuple[float, str]],
    dimensions: dict[str, str],
    *,
    properties: dict[str, Any] | None = None,
    timestamp_ms: int | None = None,
) -> dict[str, Any]:
    """Build one EMF record. `metrics` = {name: (value, unit)}."""
    ts = timestamp_ms if timestamp_ms is not None else int(time.time() * 1000)
    record: dict[str, Any] = {
        "_aws": {
            "Timestamp": ts,
            "CloudWatchMetrics": [
                {
                    "Namespace": namespace,
                    "Dimensions": [list(dimensions.keys())] if dimensions else [[]],
                    "Metrics": [
                        {"Name": name, "Unit": unit}
                        for name, (_value, unit) in metrics.items()
                    ],
                }
            ],
        }
    }
    for name, value in dimensions.items():
        record[name] = value
    for name, (value, _unit) in metrics.items():
        record[name] = value
    if properties:
        record.update(properties)
    return record


def emit_metric(
    namespace: str,
    metrics: dict[str, tuple[float, str]],
    dimensions: dict[str, str],
    *,
    properties: dict[str, Any] | None = None,
    logger: Any = None,
) -> dict[str, Any]:
    """Build a string-redacted EMF record, log it, and return it.

    String fields are scrubbed with the `logging_safe` redaction primitive so
    no raw PII rides beside a metric (AC-Q2); numeric fields are preserved.
    """
    logger = logger or logging.getLogger("claim_processor.metrics")
    record = _redact_strings(
        build_emf(namespace, metrics, dimensions, properties=properties)
    )
    logger.info(json.dumps(record))
    return record
