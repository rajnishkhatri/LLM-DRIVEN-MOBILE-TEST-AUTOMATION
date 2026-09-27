from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.remediation import RemediationAction, decide_remediation
from claim_processor.remediation_entry import apply_to_flags, lambda_handler

SONNET = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

ENVIRON = {
    "CLAIM_PROCESSOR_APPCONFIG_APP_ID": "3kx1rfd",
    "CLAIM_PROCESSOR_APPCONFIG_ENV_ID": "l8gkgvm",
    "CLAIM_PROCESSOR_APPCONFIG_PROFILE_ID": "lfhpx38",
    "CLAIM_PROCESSOR_EXTRACT_MODEL_ID": SONNET,
}


def _sns_event(alarm_name: str, state: str) -> dict:
    return {
        "Records": [
            {
                "Sns": {
                    "Message": json.dumps(
                        {"AlarmName": alarm_name, "NewStateValue": state}
                    )
                }
            }
        ]
    }


class FakeAppConfigData:
    def __init__(self, document: dict):
        self._doc = document

    def start_configuration_session(self, **kwargs):
        self.session_kwargs = kwargs
        return {"InitialConfigurationToken": "tok"}

    def get_latest_configuration(self, **kwargs):
        body = json.dumps(self._doc).encode("utf-8")
        return {"Configuration": io.BytesIO(body)}


class FakeAppConfig:
    def __init__(self):
        self.deployed_content: dict | None = None

    def create_hosted_configuration_version(self, **kwargs):
        self.deployed_content = json.loads(kwargs["Content"].decode("utf-8"))
        return {"VersionNumber": 7}

    def start_deployment(self, **kwargs):
        self.deployment_kwargs = kwargs
        return {"DeploymentNumber": 3}


class ApplyToFlagsTests(unittest.TestCase):
    def test_open_breaker_adds_target_once(self) -> None:
        decision = decide_remediation("ModelErrorRate", "ALARM", target=SONNET)
        flags = apply_to_flags(decision, {"breaker_open_models": []})
        self.assertEqual(flags["breaker_open_models"], [SONNET])
        self.assertIsNone(apply_to_flags(decision, flags))  # idempotent

    def test_close_breaker_removes_target(self) -> None:
        decision = decide_remediation("ModelErrorRate", "OK", target=SONNET)
        flags = apply_to_flags(decision, {"breaker_open_models": [SONNET]})
        self.assertEqual(flags["breaker_open_models"], [])
        self.assertIsNone(apply_to_flags(decision, flags))

    def test_insufficient_data_also_closes(self) -> None:
        decision = decide_remediation("ModelErrorRate", "INSUFFICIENT_DATA", target=SONNET)
        self.assertEqual(decision.action, RemediationAction.CLOSE_BREAKER)

    def test_disable_ensemble_sets_kill_switch(self) -> None:
        decision = decide_remediation("CostPerClaim", "ALARM")
        flags = apply_to_flags(decision, {"kill_switch_ensemble": False})
        self.assertTrue(flags["kill_switch_ensemble"])
        self.assertIsNone(apply_to_flags(decision, flags))

    def test_non_flag_actions_return_none(self) -> None:
        for alarm in ("LatencyP99", "DeploymentBake", "UnknownAlarm"):
            decision = decide_remediation(alarm, "ALARM")
            self.assertIsNone(apply_to_flags(decision, {"breaker_open_models": []}))


class HandlerTests(unittest.TestCase):
    def _doc(self) -> dict:
        return {"extract_model_id": SONNET, "flags": {"breaker_open_models": []}}

    def test_alarm_opens_breaker_via_new_deployment(self) -> None:
        appconfig = FakeAppConfig()
        out = lambda_handler(
            _sns_event("claim-processor-ModelErrorRate", "ALARM"),
            appconfig=appconfig,
            appconfigdata=FakeAppConfigData(self._doc()),
            environ=ENVIRON,
        )
        record = out["records"][0]
        self.assertEqual(record["action"], "open_breaker")
        self.assertTrue(record["applied"])
        self.assertEqual(record["config_version"], 7)
        self.assertEqual(
            appconfig.deployed_content["flags"]["breaker_open_models"], [SONNET]
        )
        self.assertEqual(
            appconfig.deployment_kwargs["DeploymentStrategyId"], "AppConfig.AllAtOnce"
        )

    def test_recovery_closes_breaker(self) -> None:
        appconfig = FakeAppConfig()
        doc = {"flags": {"breaker_open_models": [SONNET]}}
        out = lambda_handler(
            _sns_event("claim-processor-ModelErrorRate", "OK"),
            appconfig=appconfig,
            appconfigdata=FakeAppConfigData(doc),
            environ=ENVIRON,
        )
        self.assertTrue(out["records"][0]["applied"])
        self.assertEqual(appconfig.deployed_content["flags"]["breaker_open_models"], [])

    def test_already_in_state_deploys_nothing(self) -> None:
        appconfig = FakeAppConfig()
        doc = {"flags": {"breaker_open_models": [SONNET]}}
        out = lambda_handler(
            _sns_event("claim-processor-ModelErrorRate", "ALARM"),
            appconfig=appconfig,
            appconfigdata=FakeAppConfigData(doc),
            environ=ENVIRON,
        )
        record = out["records"][0]
        self.assertFalse(record["applied"])
        self.assertIsNone(appconfig.deployed_content)

    def test_human_needed_actions_are_recorded_not_applied(self) -> None:
        appconfig = FakeAppConfig()
        out = lambda_handler(
            _sns_event("claim-processor-LatencyP99", "ALARM"),
            appconfig=appconfig,
            appconfigdata=FakeAppConfigData(self._doc()),
            environ=ENVIRON,
        )
        record = out["records"][0]
        self.assertEqual(record["action"], "switch_model")
        self.assertFalse(record["applied"])
        self.assertIsNone(appconfig.deployed_content)

    def test_direct_alarm_payload_without_sns_wrapper(self) -> None:
        appconfig = FakeAppConfig()
        out = lambda_handler(
            {"AlarmName": "claim-processor-ModelErrorRate", "NewStateValue": "ALARM"},
            appconfig=appconfig,
            appconfigdata=FakeAppConfigData(self._doc()),
            environ=ENVIRON,
        )
        self.assertTrue(out["records"][0]["applied"])


if __name__ == "__main__":
    unittest.main()
