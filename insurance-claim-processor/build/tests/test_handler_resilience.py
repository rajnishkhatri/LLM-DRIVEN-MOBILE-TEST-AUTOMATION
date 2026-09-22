"""R-13 — degraded_extract handler is a thin SFN↔module adapter (AC-N2).

The breaker-open Lambda extracts via the degradation ladder and passes the
event through, exactly like the normal understand_extract handler.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.handler import MissingPipelineError, breaker_probe, degraded_extract


class _StubPipeline:
    def __init__(self):
        self.seen = None
        self.refreshes = 0

    def refresh_policy(self):
        self.refreshes += 1

    def understand_extract(self, bucket, key):
        self.seen = (bucket, key)
        return {
            "document_text": "",
            "extracted_info": {"claim_amount": 1},
            "extract_model_id": "rule_based",
            "degradation_tier": "rule_based",
            "breaker_state": "open",
        }


class DegradedExtractHandlerTests(unittest.TestCase):
    def test_delegates_and_merges_event(self) -> None:
        pipe = _StubPipeline()
        event = {"bucket": "work", "key": "claims/x.txt", "breaker_open": True}
        out = degraded_extract(event, pipeline=pipe)
        self.assertEqual(pipe.seen, ("work", "claims/x.txt"))
        self.assertEqual(out["degradation_tier"], "rule_based")
        self.assertEqual(out["breaker_state"], "open")
        self.assertEqual(out["bucket"], "work")  # event passed through

    def test_requires_pipeline(self) -> None:
        with self.assertRaises(MissingPipelineError):
            degraded_extract({"bucket": "b", "key": "k"}, pipeline=None)

    def test_extract_handlers_refresh_config_per_invocation(self) -> None:
        """Review #4: `_refresh_policy` ran only in the CLI `process()` path —
        the deployed handlers never adopted a live AppConfig change (AC-K3)."""
        pipe = _StubPipeline()
        degraded_extract({"bucket": "b", "key": "k"}, pipeline=pipe)
        self.assertEqual(pipe.refreshes, 1)


class BreakerProbeTests(unittest.TestCase):
    """Review #3: no state populated `$.breaker_open`; the probe handler is
    its producer, reading the shared AppConfig flag per execution (AC-N2/N3)."""

    def _pipeline(self, flags):
        from claim_processor.config import EscalationPolicy
        from claim_processor.pipeline import ClaimPipeline

        return ClaimPipeline(
            store=None,
            invoker=None,
            templates=None,
            validator=None,
            retriever=None,
            policy=EscalationPolicy(extract_model_id="m-primary", flags=flags),
        )

    def test_open_breaker_sets_true(self) -> None:
        pipe = self._pipeline({"breaker_open_models": ["m-primary"]})
        out = breaker_probe({"bucket": "b", "key": "k"}, pipeline=pipe)
        self.assertIs(out["breaker_open"], True)
        self.assertEqual(out["bucket"], "b")  # event passed through

    def test_closed_breaker_sets_false(self) -> None:
        pipe = self._pipeline({})
        out = breaker_probe({"bucket": "b", "key": "k"}, pipeline=pipe)
        self.assertIs(out["breaker_open"], False)

    def test_probe_adopts_live_config_change(self) -> None:
        """AC-K3 on the SFN path: a flag flipped between two executions is
        seen by the next probe with no deploy."""
        from claim_processor.config_provider import ConfigResult

        class _FlippingProvider:
            def __init__(self):
                self.calls = 0

            def get(self):
                self.calls += 1
                flags = (
                    {"breaker_open_models": ["m-primary"]} if self.calls > 1 else {}
                )
                return ConfigResult(
                    config={"flags": flags, "extract_model_id": "m-primary"},
                    source="appconfig",
                )

        pipe = self._pipeline({})
        pipe.config_provider = _FlippingProvider()
        first = breaker_probe({"bucket": "b", "key": "k"}, pipeline=pipe)
        second = breaker_probe({"bucket": "b", "key": "k"}, pipeline=pipe)
        self.assertIs(first["breaker_open"], False)
        self.assertIs(second["breaker_open"], True)


if __name__ == "__main__":
    unittest.main()
