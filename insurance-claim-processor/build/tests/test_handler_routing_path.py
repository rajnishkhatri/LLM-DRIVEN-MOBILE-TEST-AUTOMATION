"""R-19/R-26 — SFN-path routing integrity (AC-R3 through the handler layer).

Stage-7 review #1: `handler.retrieve_summarize` rebuilt `ProcessingResult`
without the resilience provenance, so a breaker-open / degraded / ensemble-split
/ config-rejected claim could auto-approve in the Step Functions runtime while
the CLI `process()` path routed the same claim to review. These tests drive
routing THROUGH the handler with the real `ClaimPipeline` — a stub pipeline
would hide exactly the gap that shipped.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from botocore.exceptions import ReadTimeoutError

from claim_processor.config import EscalationPolicy
from claim_processor.handler import breaker_probe, retrieve_summarize, understand_extract
from claim_processor.models import EXTRACT_MODEL_EXAMPLE
from claim_processor.pipeline import ClaimPipeline
from claim_processor.prompts import PromptTemplateManager
from claim_processor.rag import PolicyRetriever
from claim_processor.store import LocalDocumentStore
from claim_processor.validator import ContentValidator

_DOC = (ROOT / "samples" / "claims" / "auto-fl-collision.txt").read_text()

_MARIA = {
    "claimant_name": "Maria Elena Ruiz",
    "policy_number": "POL-FL-AU-88421",
    "incident_date": "2026-03-11",
    "claim_amount": 4820.5,
    "incident_description": "Third party failed to yield; struck Civic quarter panel in Miami-Dade.",
}


class _SummaryInvoker:
    """The retrieve_summarize step only calls the summary model."""

    def converse(self, prompt, *, model_id=None, **_):
        return {
            "text": "Summary grounded in the retrieved policy excerpts.",
            "model_id": model_id or "fake-summary",
            "stop_reason": "end_turn",
            "usage": {"inputTokens": 7, "outputTokens": 3, "totalTokens": 10},
            "guardrail": {"intervened": False, "actions": []},
        }


def _event(**overrides):
    """A merged SFN event as UnderstandExtract emits it — clean by default."""
    event = {
        "bucket": "work",
        "key": "claims/auto-fl-collision.txt",
        "document_text": _DOC,
        "extracted_info": dict(_MARIA),
        "extract_model_id": EXTRACT_MODEL_EXAMPLE,
        "understand_model_id": None,
        "usage": {"inputTokens": 5, "outputTokens": 5, "totalTokens": 10},
        "guardrail": {"intervened": False, "actions": []},
        "config_snapshot": {"extract_model_id": EXTRACT_MODEL_EXAMPLE},
        "model_variant": f"control:{EXTRACT_MODEL_EXAMPLE}",
        "ensemble": None,
        "degradation_tier": None,
        "breaker_state": None,
    }
    event.update(overrides)
    return event


class HandlerRoutingIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pipe = ClaimPipeline(
            store=LocalDocumentStore(ROOT),
            invoker=_SummaryInvoker(),
            templates=PromptTemplateManager(),
            validator=ContentValidator(),
            retriever=PolicyRetriever(ROOT / "samples" / "policies"),
            policy=EscalationPolicy(),
        )

    def _route(self, event) -> str:
        return retrieve_summarize(event, pipeline=self.pipe)["route"]

    def test_clean_event_auto_approves(self) -> None:
        """Fixture sanity: the integrity gates must not over-block (AC-E1)."""
        self.assertEqual(self._route(_event()), "auto_approve")

    def test_degraded_event_routes_review(self) -> None:
        """AC-P3: a below-advanced extraction never auto-approves via SFN."""
        out = retrieve_summarize(
            _event(degradation_tier="rule_based", extract_model_id="rule_based"),
            pipeline=self.pipe,
        )
        self.assertEqual(out["route"], "human_review")

    def test_breaker_open_event_routes_review(self) -> None:
        """AC-N2: breaker-open provenance must survive into routing."""
        self.assertEqual(self._route(_event(breaker_state="open")), "human_review")

    def test_ensemble_split_event_routes_review(self) -> None:
        """AC-O1: a split vote flagged upstream must reach the Route choice."""
        split = {
            "members": ["m-a", "m-b"],
            "agreement": {"claim_amount": 0.5},
            "low_confidence_fields": ["claim_amount"],
        }
        self.assertEqual(self._route(_event(ensemble=split)), "human_review")

    def test_config_rejected_event_routes_review(self) -> None:
        """AC-K4: a rejected config value must not widen auto-approve."""
        self.assertEqual(
            self._route(_event(config_rejected=["amount_threshold"])),
            "human_review",
        )

    def test_merged_payload_keeps_both_usages(self) -> None:
        """Faithful record: summary usage must not overwrite extract usage."""
        out = retrieve_summarize(_event(), pipeline=self.pipe)
        self.assertEqual(out["usage"]["extract"]["inputTokens"], 5)
        self.assertEqual(out["usage"]["summary"]["inputTokens"], 7)


class _ChainInvoker:
    """Extract + summary invoker for the full handler chain."""

    def __init__(self, *, raise_by_model=None):
        self.raise_by_model = raise_by_model or {}

    def converse(self, prompt, *, model_id=None, content=None, **_):
        import json as _json

        if "Extract the following fields" in prompt or bool(content):
            if model_id in self.raise_by_model:
                raise self.raise_by_model[model_id]
            text = _json.dumps(_MARIA)
        else:
            text = "Summary grounded in the retrieved policy excerpts."
        return {
            "text": text,
            "model_id": model_id or "fake",
            "stop_reason": "end_turn",
            "usage": {"inputTokens": 5, "outputTokens": 5, "totalTokens": 10},
            "guardrail": {"intervened": False, "actions": []},
        }


class HandlerChainTests(unittest.TestCase):
    """R-26: drive BreakerProbe → UnderstandExtract → RetrieveSummarize with
    the real pipeline, so provenance produced BY the pipeline (not hand-built
    events) is proven to survive the SFN merges into the Route choice."""

    def _pipeline(self, invoker, policy) -> ClaimPipeline:
        import shutil
        import tempfile

        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        claims = root / "work" / "claims"
        claims.mkdir(parents=True)
        shutil.copy(
            ROOT / "samples" / "claims" / "auto-fl-collision.txt",
            claims / "auto-fl-collision.txt",
        )
        return ClaimPipeline(
            store=LocalDocumentStore(root),
            invoker=invoker,
            templates=PromptTemplateManager(),
            validator=ContentValidator(),
            retriever=PolicyRetriever(ROOT / "samples" / "policies"),
            policy=policy,
        )

    def _run_chain(self, pipe) -> dict:
        event = {"bucket": "work", "key": "claims/auto-fl-collision.txt"}
        event = breaker_probe(event, pipeline=pipe)
        event = understand_extract(event, pipeline=pipe)
        return retrieve_summarize(event, pipeline=pipe)

    def test_clean_chain_auto_approves(self) -> None:
        pipe = self._pipeline(_ChainInvoker(), EscalationPolicy())
        out = self._run_chain(pipe)
        self.assertEqual(out["route"], "auto_approve")
        self.assertIs(out["breaker_open"], False)

    def test_degraded_chain_routes_review(self) -> None:
        """Primary timeout → ladder → provenance flows through both merges."""
        from claim_processor.models import EXTRACT_MODEL_EXAMPLE as PRIMARY

        pipe = self._pipeline(
            _ChainInvoker(raise_by_model={PRIMARY: ReadTimeoutError(endpoint_url="x")}),
            EscalationPolicy(degradation_tiers=(PRIMARY, "rule_based")),
        )
        out = self._run_chain(pipe)
        self.assertEqual(out["degradation_tier"], "rule_based")
        self.assertEqual(out["route"], "human_review")

    def test_breaker_open_chain_probes_true_and_routes_review(self) -> None:
        """Open breaker on the primary: the probe steers the ASL Choice AND
        the walked extraction carries breaker provenance into routing."""
        from claim_processor.models import EXTRACT_MODEL_EXAMPLE as PRIMARY

        pipe = self._pipeline(
            _ChainInvoker(),
            EscalationPolicy(
                degradation_tiers=(PRIMARY, "basic-model"),
                flags={"breaker_open_models": [PRIMARY]},
            ),
        )
        out = self._run_chain(pipe)
        self.assertIs(out["breaker_open"], True)
        self.assertEqual(out["breaker_state"], "open")
        self.assertEqual(out["route"], "human_review")


if __name__ == "__main__":
    unittest.main()
