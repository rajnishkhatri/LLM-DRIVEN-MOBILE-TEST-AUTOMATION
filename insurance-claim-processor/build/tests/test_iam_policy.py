"""Offline policy-lint for the three least-privilege IAM documents (AC-I1, AC-I2)."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any

IAM_DIR = Path(__file__).resolve().parents[1] / "iam"
POLICY_FILES = ("sfn-exec.json", "step-lambda.json", "operator.json")

CLAUDE_FOUNDATION_ARN = "arn:aws:bedrock:*::foundation-model/anthropic.claude-*"
NOVA_FOUNDATION_ARN = "arn:aws:bedrock:*::foundation-model/amazon.nova-*"
CLAUDE_INFERENCE_ARN = "arn:aws:bedrock:*:*:inference-profile/us.anthropic.claude-*"
NOVA_INFERENCE_ARN = "arn:aws:bedrock:*:*:inference-profile/us.amazon.nova-*"
NAMED_INVOKE_ARNS = (
    CLAUDE_FOUNDATION_ARN,
    NOVA_FOUNDATION_ARN,
    CLAUDE_INFERENCE_ARN,
    NOVA_INFERENCE_ARN,
)
INVOKE_ACTIONS = {
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream",
}
OPERATOR_ALLOWED_ACTIONS = {
    "states:SendTaskSuccess",
    "states:SendTaskFailure",
    "s3:GetObject",
    "bedrock:InvokeModel",
}
SFN_ALLOWED_ACTION_PREFIXES = ("lambda:", "logs:")
SERVICE_WIDE_ACTION = re.compile(r"^(\*|[a-z0-9-]+:\*)$")
BUCKET_WIDE_S3_RESOURCE = re.compile(
    r"^(?:\*|arn:aws:s3:::(?:\*|[^/]+|/*))$|arn:aws:s3:::[^/]+/\*$"
)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _statements(policy: dict[str, Any]) -> list[dict[str, Any]]:
    return [s for s in _as_list(policy.get("Statement")) if isinstance(s, dict)]


def _actions(statement: dict[str, Any]) -> list[str]:
    return [a for a in _as_list(statement.get("Action")) if isinstance(a, str)]


def _resources(statement: dict[str, Any]) -> list[str]:
    return [r for r in _as_list(statement.get("Resource")) if isinstance(r, str)]


def _is_invoke_statement(statement: dict[str, Any]) -> bool:
    return bool(set(_actions(statement)) & INVOKE_ACTIONS)


def _model_id_segment(arn: str) -> str:
    return arn.rsplit("/", 1)[-1] if "/" in arn else arn


class IamPolicyLintTests(unittest.TestCase):
    def _load(self, name: str) -> dict[str, Any]:
        path = IAM_DIR / name
        self.assertTrue(path.is_file(), f"missing policy file: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsInstance(payload, dict)
        self.assertIn("Statement", payload)
        return payload

    def _all_policies(self) -> dict[str, dict[str, Any]]:
        return {name: self._load(name) for name in POLICY_FILES}

    def test_policy_documents_load(self) -> None:
        policies = self._all_policies()
        self.assertEqual(set(policies), set(POLICY_FILES))

    def test_no_full_access_managed_policy_style(self) -> None:
        for name, policy in self._all_policies().items():
            raw = json.dumps(policy)
            with self.subTest(name):
                self.assertNotIn(
                    "FullAccess",
                    raw,
                    f"{name} carries a FullAccess managed-policy style grant",
                )
                self.assertNotIn("AmazonBedrockFullAccess", raw)
                for statement in _statements(policy):
                    for action in _actions(statement):
                        self.assertIsNone(
                            SERVICE_WIDE_ACTION.fullmatch(action),
                            f"{name} uses service-wide action {action!r}",
                        )

    def _s3_resources(self, policy: dict[str, Any], action: str) -> list[str]:
        found: list[str] = []
        for statement in _statements(policy):
            if action in _actions(statement):
                found.extend(_resources(statement))
        return found

    def test_step_lambda_s3_get_claims_put_results_and_pending(self) -> None:
        policy = self._load("step-lambda.json")
        get_resources = self._s3_resources(policy, "s3:GetObject")
        put_resources = self._s3_resources(policy, "s3:PutObject")
        self.assertTrue(get_resources, "step-lambda must GetObject")
        self.assertTrue(put_resources, "step-lambda must PutObject")
        for resource in get_resources:
            self.assertIn("/claims/", resource)
            self.assertNotIn("/results/", resource)
            self.assertNotIn("/pending-review/", resource)
        self.assertTrue(any("/results/" in r for r in put_resources))
        self.assertTrue(any("/pending-review/" in r for r in put_resources))
        for resource in put_resources:
            self.assertNotIn("/claims/", resource)

        operator = self._load("operator.json")
        operator_gets = self._s3_resources(operator, "s3:GetObject")
        self.assertTrue(operator_gets)
        for resource in operator_gets:
            self.assertIn("/pending-review/", resource)
            self.assertNotIn("/claims/", resource)
            self.assertNotIn("/results/", resource)

    def test_no_bucket_wide_s3_star(self) -> None:
        for name, policy in self._all_policies().items():
            with self.subTest(name):
                for statement in _statements(policy):
                    for action in _actions(statement):
                        self.assertNotEqual(action, "s3:*", f"{name} grants bucket-wide s3:*")
                    if any(a.startswith("s3:") for a in _actions(statement)):
                        self.assertTrue(_resources(statement), f"{name} S3 statement has no Resource")
                        for resource in _resources(statement):
                            self.assertIsNone(
                                BUCKET_WIDE_S3_RESOURCE.fullmatch(resource),
                                f"{name} S3 resource is bucket-wide: {resource!r}",
                            )
                            self.assertIn("/", resource)

    def test_apply_guardrail_uses_named_pattern(self) -> None:
        policy = self._load("step-lambda.json")
        apply_statements = [
            s
            for s in _statements(policy)
            if "bedrock:ApplyGuardrail" in _actions(s)
        ]
        self.assertTrue(apply_statements, "step-lambda must grant ApplyGuardrail")
        for statement in apply_statements:
            resources = _resources(statement)
            self.assertTrue(resources, "ApplyGuardrail has no Resource")
            for resource in resources:
                self.assertIn("guardrail/", resource)
                self.assertFalse(
                    resource.endswith("guardrail/*"),
                    f"ApplyGuardrail must be a named pattern, not {resource!r}",
                )
                segment = _model_id_segment(resource)
                self.assertNotEqual(segment, "*")
                self.assertIn("claim-processor", segment)

    def test_bedrock_invoke_names_both_arn_patterns(self) -> None:
        for name, policy in self._all_policies().items():
            invoke_statements = [
                s for s in _statements(policy) if _is_invoke_statement(s)
            ]
            if name == "sfn-exec.json":
                self.assertEqual(invoke_statements, [], f"{name} must not invoke Bedrock")
                continue
            self.assertTrue(invoke_statements, f"{name} must grant a Bedrock invoke")
            for statement in invoke_statements:
                resources = _resources(statement)
                with self.subTest(name):
                    self.assertTrue(
                        any("foundation-model/" in r for r in resources),
                        f"{name} invoke is missing foundation-model/",
                    )
                    self.assertTrue(
                        any("inference-profile/" in r for r in resources),
                        f"{name} invoke is missing inference-profile/",
                    )
                    for required in NAMED_INVOKE_ARNS:
                        self.assertIn(
                            required,
                            resources,
                            f"{name} invoke is missing named pattern {required}",
                        )
                    for resource in resources:
                        if "foundation-model/" in resource or "inference-profile/" in resource:
                            segment = _model_id_segment(resource)
                            self.assertNotEqual(
                                segment,
                                "*",
                                f"{name} model-id segment is a lone '*': {resource!r}",
                            )
                            self.assertIn(
                                "*",
                                segment,
                                f"{name} model-id segment is pinned, not a pattern: {resource!r}",
                            )

    def test_operator_is_scoped(self) -> None:
        policy = self._load("operator.json")
        seen: set[str] = set()
        for statement in _statements(policy):
            actions = _actions(statement)
            seen.update(actions)
            extra = set(actions) - OPERATOR_ALLOWED_ACTIONS
            self.assertFalse(extra, f"operator grants out-of-scope actions: {sorted(extra)}")
            if "s3:GetObject" in actions:
                for resource in _resources(statement):
                    self.assertIn("pending-review/", resource)
                    self.assertNotIn("claims/", resource)
                    self.assertNotIn("results/", resource)
            if set(actions) & {"states:SendTaskSuccess", "states:SendTaskFailure"}:
                for resource in _resources(statement):
                    self.assertEqual(
                        resource,
                        "*",
                        "HITL SendTask* must be Resource '*' (AWS empty Resource types)",
                    )
                    self.assertNotIn("stateMachine:", resource)
                    self.assertNotIn("execution:", resource)
            if "bedrock:InvokeModel" in actions:
                self.assertNotIn("bedrock:InvokeModelWithResponseStream", actions)
        self.assertTrue(
            {"states:SendTaskSuccess", "states:SendTaskFailure"} <= seen,
            "operator must grant HITL SendTaskSuccess/SendTaskFailure",
        )
        self.assertIn("s3:GetObject", seen)
        self.assertIn("bedrock:InvokeModel", seen)
        self.assertNotIn("s3:PutObject", seen)
        self.assertNotIn("lambda:InvokeFunction", seen)

    def test_only_operator_hitl_uses_star_resource(self) -> None:
        hitl = {"states:SendTaskSuccess", "states:SendTaskFailure"}
        for name, policy in self._all_policies().items():
            for statement in _statements(policy):
                actions = set(_actions(statement))
                for resource in _resources(statement):
                    if resource != "*":
                        continue
                    self.assertEqual(
                        name,
                        "operator.json",
                        f"{name} uses Resource '*' outside operator HITL",
                    )
                    self.assertTrue(
                        actions & hitl,
                        f"{name} uses Resource '*' on non-HITL actions {sorted(actions)}",
                    )

    def test_kms_viaservice_pinned_us_east_1(self) -> None:
        """PoC IAM is us-east-1 only; other CLAIM_PROCESSOR_REGION values
        are unsupported for IAM until T-15 (DEPLOY.md). key/* stays — no named CMK.
        """
        policy = self._load("step-lambda.json")
        kms_statements = [
            s
            for s in _statements(policy)
            if any(a.startswith("kms:") for a in _actions(s))
        ]
        self.assertTrue(kms_statements, "step-lambda must grant KMS via ViaService")
        via: list[str] = []
        keys: list[str] = []
        for statement in kms_statements:
            keys.extend(_resources(statement))
            cond = statement.get("Condition") or {}
            equals = cond.get("StringEquals") or {}
            via.extend(_as_list(equals.get("kms:ViaService")))
        self.assertEqual(
            set(via),
            {"s3.us-east-1.amazonaws.com", "bedrock.us-east-1.amazonaws.com"},
        )
        self.assertTrue(keys, "KMS statement has no Resource")
        for resource in keys:
            self.assertEqual(resource, "arn:aws:kms:*:*:key/*")
            self.assertNotIn("alias/", resource)

    def test_sfn_exec_is_lambda_and_logs_only(self) -> None:
        policy = self._load("sfn-exec.json")
        seen: set[str] = set()
        for statement in _statements(policy):
            for action in _actions(statement):
                seen.add(action)
                self.assertTrue(
                    action.startswith(SFN_ALLOWED_ACTION_PREFIXES),
                    f"sfn-exec grants something other than lambda/logs: {action!r}",
                )
        self.assertIn("lambda:InvokeFunction", seen)
        self.assertTrue(any(a.startswith("logs:") for a in seen), "sfn-exec must allow logs")
        self.assertFalse(any(a.startswith("bedrock:") or a.startswith("s3:") for a in seen))


if __name__ == "__main__":
    unittest.main()
