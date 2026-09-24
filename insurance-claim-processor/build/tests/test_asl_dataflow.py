"""D0-a — every Catch must preserve the claim's state (live-v1 defect, 2026-09-23).

A Catcher with no `ResultPath` defaults to `$`, so the error object
`{Error, Cause}` REPLACES the state input. The next state then has no
`bucket`/`key`: the degraded extract (AC-P1), the RAG-down fallback
(C11 / AC-G2) and the review-expiry path (AC-E4) all fail on real AWS.

The structural tests in `test_asl*.py` checked only each Catch's *target*.
These tests replay each catch→next-state hop through the REAL handlers,
feeding them exactly the input Step Functions would build, so a missing
`ResultPath` fails here instead of in production.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.test_asl import _load_definition

from claim_processor import handler
from claim_processor.fake import FakeModelInvoker
from claim_processor.pipeline import ClaimPipeline
from claim_processor.prompts import PromptTemplateManager
from claim_processor.rag import PolicyRetriever
from claim_processor.store import LocalDocumentStore
from claim_processor.validator import ContentValidator

_BUCKET = "work"
_KEY = "claims/auto-fl-clean.txt"
_ERROR = {"Error": "States.ALL", "Cause": "simulated failure"}


def _apply_result_path(state_input: dict, result_path: str | None, result: dict) -> dict:
    """ASL ResultPath semantics for the subset the definition uses.

    Absent or "$" → the result REPLACES the input (the defect).
    "$.name"      → the input is kept and the result is placed under `name`.
    """
    if result_path in (None, "$"):
        return dict(result)
    if not result_path.startswith("$.") or "." in result_path[2:]:
        raise AssertionError(f"unsupported ResultPath in test harness: {result_path!r}")
    merged = dict(state_input)
    merged[result_path[2:]] = result
    return merged


def _resolve(document: dict, path: str) -> Any:
    """Resolve a `$.a.b` JSONPath; KeyError = States.Runtime on real AWS."""
    if path == "$":
        return document
    node: Any = document
    for part in path[2:].split("."):
        node = node[part]
    return node


def _evaluate_parameters(parameters: dict, state_input: dict) -> dict:
    """Pass-state `Parameters` evaluation (static values + `.$` paths)."""
    out: dict[str, Any] = {}
    for key, value in parameters.items():
        if key.endswith(".$"):
            out[key[:-2]] = _resolve(state_input, value)
        else:
            out[key] = value
    return out


class _Harness:
    def __init__(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        target = self.tmp / _BUCKET / _KEY
        target.parent.mkdir(parents=True)
        shutil.copy(ROOT / "samples" / "claims" / "auto-fl-clean.txt", target)
        self.pipeline = ClaimPipeline(
            store=LocalDocumentStore(self.tmp),
            invoker=FakeModelInvoker(),
            templates=PromptTemplateManager(),
            validator=ContentValidator(),
            retriever=PolicyRetriever(ROOT / "samples" / "policies"),
        )

    def run(self, fn, event: dict) -> dict:
        return fn(event, None, pipeline=self.pipeline)

    def close(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)


def _catcher(states: dict, state: str, error: str) -> dict:
    for catcher in states[state].get("Catch") or []:
        if error in catcher.get("ErrorEquals", []):
            return catcher
    raise AssertionError(f"{state} has no Catch for {error}")


class CatchPreservesStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.states = _load_definition()["States"]
        self.h = _Harness()

    def tearDown(self) -> None:
        self.h.close()

    def test_every_catcher_keeps_the_input_under_error(self) -> None:
        for name, state in self.states.items():
            for catcher in state.get("Catch") or []:
                self.assertEqual(
                    catcher.get("ResultPath"),
                    "$.error",
                    f"{name} Catch {catcher.get('ErrorEquals')} must set ResultPath '$.error' "
                    "(absent/'$' replaces the claim state with the error object)",
                )

    def test_exhausted_throttle_reaches_degraded_extract_with_the_claim(self) -> None:
        start = {"bucket": _BUCKET, "key": _KEY}
        probed = self.h.run(handler.breaker_probe, start)
        catcher = _catcher(self.states, "UnderstandExtract", "ThrottlingException")
        self.assertEqual(catcher["Next"], "DegradedExtract")
        caught = _apply_result_path(
            probed, catcher.get("ResultPath"), {"Error": "ThrottlingException", "Cause": "x"}
        )
        out = self.h.run(handler.degraded_extract, caught)  # KeyError('bucket') before the fix
        self.assertEqual(out["bucket"], _BUCKET)
        self.assertIn("extracted_info", out)

    def test_rag_failure_reaches_ungrounded_fallback_and_parks_for_review(self) -> None:
        start = {"bucket": _BUCKET, "key": _KEY}
        event = self.h.run(handler.breaker_probe, start)
        event = self.h.run(handler.understand_extract, event)
        event = self.h.run(handler.validate, event)  # = RetrieveSummarize's input
        catcher = _catcher(self.states, "RetrieveSummarize", "States.ALL")
        self.assertEqual(catcher["Next"], "UngroundedFallback")
        caught = _apply_result_path(event, catcher.get("ResultPath"), _ERROR)
        fallback = _evaluate_parameters(  # States.Runtime (KeyError) before the fix
            self.states["UngroundedFallback"]["Parameters"], caught
        )
        self.assertEqual(fallback["route"], "human_review")
        self.assertTrue(fallback["ungrounded"])
        parked = self.h.run(handler.record, fallback)  # ParkPending
        self.assertEqual(parked["route"], "human_review")
        self.assertTrue(
            (self.h.tmp / _BUCKET / "pending-review" / f"{_KEY}.json").is_file()
        )

    def test_review_timeout_reaches_expire_and_record(self) -> None:
        pending = {
            "bucket": _BUCKET,
            "key": _KEY,
            "route": "human_review",
            "extracted_info": {"claimant_name": "Maria Elena Ruiz"},
            "validation": {"accepted": True, "flags": []},
        }
        catcher = _catcher(self.states, "AwaitReview", "States.Timeout")
        self.assertEqual(catcher["Next"], "ExpireReview")
        caught = _apply_result_path(
            pending, catcher.get("ResultPath"), {"Error": "States.Timeout", "Cause": "x"}
        )
        expired = self.h.run(handler.expire_review, caught)
        recorded = self.h.run(handler.record, expired)  # KeyError('bucket') before the fix
        self.assertEqual(recorded["review"]["decision"], "review-expired")
        self.assertTrue((self.h.tmp / _BUCKET / "results" / f"{_KEY}.json").is_file())


if __name__ == "__main__":
    unittest.main()
