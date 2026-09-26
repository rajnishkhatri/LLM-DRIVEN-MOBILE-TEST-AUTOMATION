from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class MetricsLoggingLevelTests(unittest.TestCase):
    """F16: without an explicit level the package logger inherits root's
    WARNING and every INFO-level EMF record is dropped in-process."""

    def test_lambda_entry_import_enables_info_metrics(self) -> None:
        import claim_processor.lambda_entry  # noqa: F401  (level set at import)

        level = logging.getLogger("claim_processor.metrics").getEffectiveLevel()
        self.assertLessEqual(level, logging.INFO)

    def test_emf_record_reaches_the_log_stream(self) -> None:
        import claim_processor.lambda_entry  # noqa: F401

        from claim_processor.metrics import emit_metric

        with self.assertLogs("claim_processor.metrics", level="INFO") as captured:
            emit_metric(
                "ClaimProcessor",
                {"Errors": (1, "Count")},
                {"ModelId": "test-model", "Outcome": "error"},
            )
        self.assertIn('"_aws"', captured.output[0])


if __name__ == "__main__":
    unittest.main()
