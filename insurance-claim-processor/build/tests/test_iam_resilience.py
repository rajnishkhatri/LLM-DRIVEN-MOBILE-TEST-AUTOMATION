"""R-14 — IAM deltas for the resilience increment.

step-lambda gains scoped AppConfig read; a new remediation role gets scoped,
reversible AppConfig writes only; no policy uses cloudwatch:PutMetricData (EMF
via Logs — AC-Q1); remediation never uses Resource '*' (only operator HITL may).
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

IAM_DIR = ROOT / "iam"
ALL_FILES = ("sfn-exec.json", "step-lambda.json", "operator.json", "remediation.json")
SERVICE_WIDE = re.compile(r"^(\*|[a-z0-9-]+:\*)$")


def _load(name: str) -> dict[str, Any]:
    return json.loads((IAM_DIR / name).read_text(encoding="utf-8"))


def _statements(policy: dict) -> list[dict]:
    stmt = policy.get("Statement", [])
    return stmt if isinstance(stmt, list) else [stmt]


def _actions(statement: dict) -> list[str]:
    a = statement.get("Action", [])
    return a if isinstance(a, list) else [a]


def _resources(statement: dict) -> list[str]:
    r = statement.get("Resource", [])
    return r if isinstance(r, list) else [r]


class AppConfigReadTests(unittest.TestCase):
    def test_step_lambda_reads_appconfig_scoped(self) -> None:
        policy = _load("step-lambda.json")
        actions = {a for s in _statements(policy) for a in _actions(s)}
        self.assertIn("appconfig:GetLatestConfiguration", actions)
        self.assertIn("appconfig:StartConfigurationSession", actions)
        for statement in _statements(policy):
            if any(a.startswith("appconfig:") for a in _actions(statement)):
                for resource in _resources(statement):
                    self.assertNotEqual(resource, "*")
                    self.assertIn("application/", resource)

    def test_no_appconfig_arn_uses_the_application_name(self) -> None:
        """Re-review #1: AppConfig ARNs embed system-generated IDs, never the
        application NAME — `application/claim-processor*` matches nothing, so
        the grant is dead and the config plane fails silently (fail-safe
        swallows the AccessDenied). Data-plane reads wildcard the app segment;
        write grants carry the APPCONFIG_APP_ID placeholder that DEPLOY.md
        substitutes at role-creation time."""
        for name in ALL_FILES:
            for statement in _statements(_load(name)):
                for resource in _resources(statement):
                    if resource.startswith("arn:aws:appconfig:"):
                        self.assertNotIn(
                            "application/claim-processor",
                            resource,
                            f"{name}: {resource} scopes by application NAME",
                        )

    def test_no_policy_uses_appconfigdata_namespace(self) -> None:
        """`appconfigdata` is the API/client name, NOT an IAM action namespace.

        The data-plane actions authorize under `appconfig:` (AWS
        service-authorization reference). An `appconfigdata:` action grants
        nothing → silent AccessDenied → config never adopted (review #2).
        """
        for name in ALL_FILES:
            actions = {a for s in _statements(_load(name)) for a in _actions(s)}
            for action in actions:
                self.assertFalse(
                    action.startswith("appconfigdata:"),
                    f"{name}: {action} uses the non-existent appconfigdata: namespace",
                )


class RemediationRoleTests(unittest.TestCase):
    def test_remediation_file_exists_and_loads(self) -> None:
        policy = _load("remediation.json")
        self.assertIn("Statement", policy)

    def test_remediation_appconfig_writes_are_scoped(self) -> None:
        policy = _load("remediation.json")
        actions = {a for s in _statements(policy) for a in _actions(s)}
        self.assertTrue(any(a.startswith("appconfig:") for a in actions))
        for statement in _statements(policy):
            for action in _actions(statement):
                self.assertIsNone(SERVICE_WIDE.fullmatch(action), f"service-wide {action}")
            for resource in _resources(statement):
                self.assertNotEqual(resource, "*")
                self.assertTrue(resource.startswith("arn:aws:appconfig:"), resource)
                # Writes pin the app to the deploy-time-substituted ID — never
                # a wildcard application segment (re-review #1).
                if "application/" in resource:
                    self.assertIn("application/APPCONFIG_APP_ID", resource)

    def test_remediation_start_deployment_not_scoped_to_deployment_arn(self) -> None:
        """Re-review #1 (second half): StartDeployment authorizes against
        application/environment/configurationprofile/deploymentstrategy ARNs;
        only StopDeployment targets a `deployment/N` resource. Scoping
        StartDeployment to `.../deployment/*` makes rollback impossible."""
        policy = _load("remediation.json")
        for statement in _statements(policy):
            if "appconfig:StartDeployment" in _actions(statement):
                for resource in _resources(statement):
                    self.assertNotIn("/deployment/", resource)

    def test_deploy_runbook_documents_the_id_substitution(self) -> None:
        deploy = (ROOT / "DEPLOY.md").read_text(encoding="utf-8")
        self.assertIn("APPCONFIG_APP_ID", deploy)

    def test_remediation_no_fullaccess(self) -> None:
        self.assertNotIn("FullAccess", json.dumps(_load("remediation.json")))


class NoPutMetricDataTests(unittest.TestCase):
    def test_no_policy_uses_put_metric_data(self) -> None:
        for name in ALL_FILES:
            actions = {a for s in _statements(_load(name)) for a in _actions(s)}
            self.assertNotIn("cloudwatch:PutMetricData", actions, name)

    def test_only_operator_uses_star_resource(self) -> None:
        for name in ALL_FILES:
            for statement in _statements(_load(name)):
                for resource in _resources(statement):
                    if resource == "*":
                        self.assertEqual(name, "operator.json", f"{name} uses '*'")


if __name__ == "__main__":
    unittest.main()
