from __future__ import annotations

import ast
import os
import sys
import unittest
from dataclasses import fields
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.config import EscalationPolicy
from claim_processor.models import (
    EXTRACT_MODEL_EXAMPLE,
    SUMMARY_MODEL_EXAMPLE,
    UNDERSTAND_MODEL_EXAMPLE,
)

# Frozen env names from wave0-contracts.md. from_env() reads only these.
_POLICY_ENV = (
    "CLAIM_PROCESSOR_AMOUNT_THRESHOLD",
    "CLAIM_PROCESSOR_REGION",
    "CLAIM_PROCESSOR_EXTRACT_MODEL_ID",
    "CLAIM_PROCESSOR_SUMMARY_MODEL_ID",
    "CLAIM_PROCESSOR_UNDERSTAND_MODEL_ID",
    "CLAIM_PROCESSOR_GUARDRAIL_ID",
    "CLAIM_PROCESSOR_KB_ID",
    "CLAIM_PROCESSOR_FORCE_REVIEW_FLAGS",
)

_ROUTING_CONSTANT_NAMES = frozenset(
    {
        "AMOUNT_THRESHOLD",
        "DEFAULT_AMOUNT_THRESHOLD",
        "ESCALATION_THRESHOLD",
        "THRESHOLD",
    }
)


def _policy_env(**set_vars: str):
    """Isolate frozen policy vars: unset all, then apply the given ones."""
    env = {k: v for k, v in os.environ.items() if k not in _POLICY_ENV}
    env.update(set_vars)
    return patch.dict(os.environ, env, clear=True)


class EscalationPolicyTests(unittest.TestCase):
    def test_default_amount_threshold_is_10000(self) -> None:
        self.assertEqual(EscalationPolicy().amount_threshold, 10000.0)
        with _policy_env():
            self.assertEqual(EscalationPolicy.from_env().amount_threshold, 10000.0)

    def test_from_env_reads_amount_threshold(self) -> None:
        with _policy_env(CLAIM_PROCESSOR_AMOUNT_THRESHOLD="25000"):
            self.assertEqual(EscalationPolicy.from_env().amount_threshold, 25000.0)

    def test_empty_amount_threshold_falls_back_to_default(self) -> None:
        with _policy_env(CLAIM_PROCESSOR_AMOUNT_THRESHOLD=""):
            self.assertEqual(EscalationPolicy.from_env().amount_threshold, 10000.0)

    def test_whitespace_amount_threshold_falls_back_to_default(self) -> None:
        with _policy_env(CLAIM_PROCESSOR_AMOUNT_THRESHOLD="  \t"):
            self.assertEqual(EscalationPolicy.from_env().amount_threshold, 10000.0)

    def test_amount_threshold_is_not_a_module_level_routing_constant(self) -> None:
        import claim_processor.config as config

        exported = {name for name in dir(config) if name in _ROUTING_CONSTANT_NAMES}
        self.assertEqual(exported, set())

        names = {f.name for f in fields(EscalationPolicy)}
        self.assertIn("amount_threshold", names)

        tree = ast.parse(Path(config.__file__).read_text())
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in _ROUTING_CONSTANT_NAMES:
                    self.fail(
                        f"routing threshold must live on EscalationPolicy, "
                        f"not module constant {target.id}"
                    )

    def test_default_force_review_flags_empty(self) -> None:
        self.assertEqual(EscalationPolicy().force_review_flags, ())
        with _policy_env():
            self.assertEqual(EscalationPolicy.from_env().force_review_flags, ())

    def test_from_env_reads_force_review_flags(self) -> None:
        with _policy_env(CLAIM_PROCESSOR_FORCE_REVIEW_FLAGS="pii_,fraud_"):
            self.assertEqual(
                EscalationPolicy.from_env().force_review_flags,
                ("pii_", "fraud_"),
            )

    def test_from_env_default_model_ids(self) -> None:
        with _policy_env():
            policy = EscalationPolicy.from_env()
        self.assertEqual(policy.extract_model_id, EXTRACT_MODEL_EXAMPLE)
        self.assertEqual(policy.summary_model_id, SUMMARY_MODEL_EXAMPLE)
        self.assertEqual(policy.understand_model_id, UNDERSTAND_MODEL_EXAMPLE)

    def test_from_env_reads_model_ids(self) -> None:
        with _policy_env(
            CLAIM_PROCESSOR_EXTRACT_MODEL_ID="extract-from-env",
            CLAIM_PROCESSOR_SUMMARY_MODEL_ID="summary-from-env",
            CLAIM_PROCESSOR_UNDERSTAND_MODEL_ID="understand-from-env",
        ):
            policy = EscalationPolicy.from_env()
        self.assertEqual(policy.extract_model_id, "extract-from-env")
        self.assertEqual(policy.summary_model_id, "summary-from-env")
        self.assertEqual(policy.understand_model_id, "understand-from-env")

    def test_from_env_reads_region_guardrail_and_kb(self) -> None:
        with _policy_env():
            defaults = EscalationPolicy.from_env()
        self.assertEqual(defaults.region, "us-east-1")
        self.assertIsNone(defaults.guardrail_id)
        self.assertIsNone(defaults.kb_id)

        with _policy_env(
            CLAIM_PROCESSOR_REGION="eu-west-1",
            CLAIM_PROCESSOR_GUARDRAIL_ID="gr-abc",
            CLAIM_PROCESSOR_KB_ID="kb-xyz",
        ):
            policy = EscalationPolicy.from_env()
        self.assertEqual(policy.region, "eu-west-1")
        self.assertEqual(policy.guardrail_id, "gr-abc")
        self.assertEqual(policy.kb_id, "kb-xyz")
