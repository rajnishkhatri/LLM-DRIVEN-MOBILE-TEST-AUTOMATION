"""R-10 — CloudWatch metrics via EMF through the safe logger (ADR 0015).

AC-Q1 (EMF shape, no put_metric_data), AC-Q2 (routed through the redacting
logger — no raw PII beside a metric).
"""

from __future__ import annotations

import json
import logging
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor import metrics as metrics_mod
from claim_processor.metrics import Metric, build_emf, emit_metric

_SSN = "078-05-1120"


class EmfShapeTests(unittest.TestCase):
    def test_build_emf_has_directive_and_values(self) -> None:
        record = build_emf(
            "ClaimProcessor",
            {Metric.LATENCY_MS: (123.0, "Milliseconds")},
            {"ModelId": "us.anthropic.claude-x"},
        )
        directive = record["_aws"]["CloudWatchMetrics"][0]
        self.assertEqual(directive["Namespace"], "ClaimProcessor")
        self.assertEqual(directive["Dimensions"], [["ModelId"]])
        self.assertIn({"Name": Metric.LATENCY_MS, "Unit": "Milliseconds"}, directive["Metrics"])
        self.assertEqual(record[Metric.LATENCY_MS], 123.0)
        self.assertEqual(record["ModelId"], "us.anthropic.claude-x")

    def test_no_put_metric_data_call(self) -> None:
        source = Path(metrics_mod.__file__).read_text()
        self.assertNotIn("put_metric_data", source)

    def test_uses_logging_safe_redaction_primitive(self) -> None:
        source = Path(metrics_mod.__file__).read_text()
        self.assertIn("from claim_processor.logging_safe import redact", source)


class EmfRedactionTests(unittest.TestCase):
    def test_string_pii_is_redacted_numbers_preserved(self) -> None:
        logger = logging.getLogger("claim_processor.metrics.test")
        with self.assertLogs(logger, level="INFO") as captured:
            emit_metric(
                "ClaimProcessor",
                {Metric.HUMAN_REVIEW: (1, "Count"), Metric.LATENCY_MS: (1700000000000, "Milliseconds")},
                {"ModelId": "m"},
                properties={"note": f"claimant ssn {_SSN}"},
                logger=logger,
            )
        blob = "\n".join(captured.output)
        self.assertNotIn(_SSN, blob)
        self.assertIn("[REDACTED]", blob)
        # EMF still parses and the numeric metric survived redaction.
        payload = json.loads(captured.records[0].getMessage())
        self.assertIn("_aws", payload)
        self.assertEqual(payload[Metric.LATENCY_MS], 1700000000000)


if __name__ == "__main__":
    unittest.main()
