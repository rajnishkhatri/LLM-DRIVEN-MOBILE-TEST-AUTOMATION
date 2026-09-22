"""R-12 — pipeline wires adapter + flags + ensemble + degradation + metrics.

AC-K5 (config_snapshot), M2/M3 (variant), O2/O3/O4 (ensemble extraction only),
O1 (disagreement → review), P1/P3 (degrade → review), Q1 (metrics), R4
(recorded). The default (no-flags) path stays byte-identical — covered by the
existing test_pipeline.py, which must stay green.
"""

from __future__ import annotations

import json
import logging
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from botocore.exceptions import ClientError, ReadTimeoutError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.adapter import ThrottlingException
from claim_processor.config import EscalationPolicy
from claim_processor.config_provider import ConfigResult
from claim_processor.degrade import DegradationDisabledError
from claim_processor.models import EXTRACT_MODEL_EXAMPLE, SUMMARY_MODEL_EXAMPLE
from claim_processor.pipeline import ClaimPipeline, result_key_for
from claim_processor.prompts import PromptTemplateManager
from claim_processor.rag import PolicyRetriever
from claim_processor.store import LocalDocumentStore, pending_review_key
from claim_processor.validator import ContentValidator

_MARIA = {
    "claimant_name": "Maria Elena Ruiz",
    "policy_number": "POL-FL-AU-88421",
    "incident_date": "2026-03-11",
    "claim_amount": 4820.5,
    "incident_description": "Third party failed to yield; struck Civic quarter panel in Miami-Dade.",
}


def _extract(**overrides) -> str:
    return json.dumps({**_MARIA, **overrides})


def _throttle() -> ClientError:
    return ClientError({"Error": {"Code": "ThrottlingException", "Message": "slow down"}}, "Converse")


class _ScriptedInvoker:
    """Invoker-like: per-model extract behavior; single summary."""

    def __init__(self, *, extract_by_model=None, raise_by_model=None):
        self.extract_by_model = extract_by_model or {}
        self.raise_by_model = raise_by_model or {}
        self.calls: list[str] = []

    def converse(self, prompt, *, model_id=None, content=None, guardrail_config=None, **_):
        self.calls.append(model_id)
        is_extract = "Extract the following fields" in prompt or bool(content)
        if is_extract:
            if model_id in self.raise_by_model:
                raise self.raise_by_model[model_id]
            text = self.extract_by_model.get(model_id, _extract())
        else:
            text = "Summary grounded in the retrieved policy excerpts."
        return {
            "text": text,
            "model_id": model_id or "fake",
            "stop_reason": "end_turn",
            "usage": {"inputTokens": 5, "outputTokens": 5, "totalTokens": 10},
            "guardrail": {"intervened": False, "actions": []},
        }


class PipelineResilienceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        claims = self.root / "work" / "claims"
        claims.mkdir(parents=True)
        shutil.copy(
            ROOT / "samples" / "claims" / "auto-fl-collision.txt", claims / "auto-fl-collision.txt"
        )
        self.store = LocalDocumentStore(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _pipeline(self, invoker, policy) -> ClaimPipeline:
        return ClaimPipeline(
            store=self.store,
            invoker=invoker,
            templates=PromptTemplateManager(),
            validator=ContentValidator(),
            retriever=PolicyRetriever(ROOT / "samples" / "policies"),
            policy=policy,
        )

    def _pending(self, key: str) -> Path:
        return self.root / "work" / pending_review_key(key)

    def _results(self, key: str) -> Path:
        return self.root / "work" / result_key_for(key)

    def test_default_path_records_config_snapshot_and_variant(self) -> None:
        pipe = self._pipeline(_ScriptedInvoker(), EscalationPolicy())
        result = pipe.process("work", "claims/auto-fl-collision.txt")
        self.assertIsNotNone(result.config_snapshot)
        self.assertEqual(result.config_snapshot["extract_model_id"], EXTRACT_MODEL_EXAMPLE)
        self.assertTrue(result.model_variant.startswith("control:"))
        self.assertIsNone(result.degradation_tier)

    def test_ensemble_agreement_auto_approves_and_records_members(self) -> None:
        members = ("m-a", "m-b", "m-c")
        invoker = _ScriptedInvoker(extract_by_model={m: _extract() for m in members})
        policy = EscalationPolicy(ensemble_models=members, flags={"ensemble_enabled": True})
        result = self._pipeline(invoker, policy).process("work", "claims/auto-fl-collision.txt")
        self.assertEqual(result.route, "auto_approve")
        self.assertEqual(result.ensemble["members"], list(members))
        self.assertEqual(result.ensemble["low_confidence_fields"], [])

    def test_ensemble_disagreement_routes_review(self) -> None:
        members = ("m-a", "m-b", "m-c")
        invoker = _ScriptedInvoker(
            extract_by_model={
                "m-a": _extract(claim_amount=100),
                "m-b": _extract(claim_amount=200),
                "m-c": _extract(claim_amount=300),
            }
        )
        policy = EscalationPolicy(ensemble_models=members, flags={"ensemble_enabled": True})
        result = self._pipeline(invoker, policy).process("work", "claims/auto-fl-collision.txt")
        self.assertEqual(result.route, "human_review")
        self.assertIn("claim_amount", result.ensemble["low_confidence_fields"])
        self.assertTrue(self._pending("claims/auto-fl-collision.txt").is_file())

    def test_summary_stays_single_model(self) -> None:
        members = ("m-a", "m-b", "m-c")
        invoker = _ScriptedInvoker(extract_by_model={m: _extract() for m in members})
        policy = EscalationPolicy(ensemble_models=members, flags={"ensemble_enabled": True})
        result = self._pipeline(invoker, policy).process("work", "claims/auto-fl-collision.txt")
        # summary model called exactly once (not ensembled — O3)
        self.assertEqual(invoker.calls.count(SUMMARY_MODEL_EXAMPLE), 1)
        self.assertEqual(result.summary_model_id, SUMMARY_MODEL_EXAMPLE)

    def test_primary_failure_degrades_and_routes_review(self) -> None:
        # Timeout (not throttle) triggers the ladder: a throttle now re-raises
        # for the SFN Retry tier (review #7) — see ThrottleReRaiseTests.
        invoker = _ScriptedInvoker(
            raise_by_model={EXTRACT_MODEL_EXAMPLE: ReadTimeoutError(endpoint_url="x")}
        )
        policy = EscalationPolicy(degradation_tiers=(EXTRACT_MODEL_EXAMPLE, "rule_based"))
        result = self._pipeline(invoker, policy).process("work", "claims/auto-fl-collision.txt")
        self.assertEqual(result.degradation_tier, "rule_based")
        self.assertEqual(result.route, "human_review")

    def test_throttle_re_raises_for_sfn_retry_tier(self) -> None:
        """Review #7: swallowing a throttle degraded the claim instead of
        letting the ASL Retry (ThrottlingException, backoff 2.0) re-run the
        step — C2: retries belong to the orchestrator, not the app."""
        invoker = _ScriptedInvoker(raise_by_model={EXTRACT_MODEL_EXAMPLE: _throttle()})
        policy = EscalationPolicy(degradation_tiers=(EXTRACT_MODEL_EXAMPLE, "rule_based"))
        with self.assertRaises(ThrottlingException):
            self._pipeline(invoker, policy).process("work", "claims/auto-fl-collision.txt")

    def test_ensemble_usage_accumulates_across_member_calls(self) -> None:
        """Review #6: `dict.update` kept only the LAST call's tokens — an
        N-member ensemble under-reported cost N×."""
        members = ("m-a", "m-b", "m-c")
        invoker = _ScriptedInvoker(extract_by_model={m: _extract() for m in members})
        policy = EscalationPolicy(ensemble_models=members, flags={"ensemble_enabled": True})
        result = self._pipeline(invoker, policy).process("work", "claims/auto-fl-collision.txt")
        # 3 member calls × 5/5/10 each
        self.assertEqual(result.usage["extract"]["inputTokens"], 15)
        self.assertEqual(result.usage["extract"]["outputTokens"], 15)
        self.assertEqual(result.usage["extract"]["totalTokens"], 30)

    def test_rejected_config_flags_and_routes_review(self) -> None:
        """Review #10: `ConfigResult.rejected` was dropped in `_refresh_policy`
        so the AC-K4 routing gate (`config_rejected`) could never fire."""

        class _RejectingProvider:
            def get(self):
                return ConfigResult(
                    config={"amount_threshold": 10000.0},
                    source="appconfig",
                    rejected=("extract_model_id",),
                )

        pipe = self._pipeline(_ScriptedInvoker(), EscalationPolicy())
        pipe.config_provider = _RejectingProvider()
        result = pipe.process("work", "claims/auto-fl-collision.txt")
        self.assertIn("config_rejected:extract_model_id", result.validation.flags)
        self.assertEqual(result.route, "human_review")

    def test_degradation_disabled_failing_primary_raises(self) -> None:
        """Review #11: the `degradation_enabled` kill-switch was never read —
        off must mean FAIL the step, not silently walk the ladder (AC-M5)."""
        invoker = _ScriptedInvoker(
            raise_by_model={EXTRACT_MODEL_EXAMPLE: ReadTimeoutError(endpoint_url="x")}
        )
        policy = EscalationPolicy(
            degradation_tiers=(EXTRACT_MODEL_EXAMPLE, "rule_based"),
            flags={"degradation_enabled": False},
        )
        with self.assertRaises(DegradationDisabledError):
            self._pipeline(invoker, policy).process("work", "claims/auto-fl-collision.txt")

    def test_degradation_disabled_healthy_primary_unaffected(self) -> None:
        policy = EscalationPolicy(flags={"degradation_enabled": False})
        result = self._pipeline(_ScriptedInvoker(), policy).process(
            "work", "claims/auto-fl-collision.txt"
        )
        self.assertIsNone(result.degradation_tier)
        self.assertEqual(result.route, "auto_approve")

    def test_metrics_emitted_during_process(self) -> None:
        pipe = self._pipeline(_ScriptedInvoker(), EscalationPolicy())
        logger = logging.getLogger("claim_processor.metrics")
        with self.assertLogs(logger, level="INFO") as captured:
            pipe.process("work", "claims/auto-fl-collision.txt")
        self.assertTrue(any("_aws" in line for line in captured.output))


if __name__ == "__main__":
    unittest.main()
