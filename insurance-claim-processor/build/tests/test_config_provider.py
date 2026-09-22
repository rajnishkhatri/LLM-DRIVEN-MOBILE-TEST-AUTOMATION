"""R-01 — ConfigProvider over AppConfig Data, with fallback + validation.

AC-K1 (fail-safe fallback), AC-K2 (runtime source, injectable), AC-K4
(malformed value rejected, last-known-good retained). Stubber only — no creds,
no new pip dep (appconfigdata ships in botocore).
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import boto3
from botocore.stub import Stubber

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.config_provider import ConfigProvider, validate_config

FALLBACK = {"amount_threshold": 10000.0, "extract_model_id": "boot-extract"}
_APP, _ENV, _PROF = "claim-processor", "poc", "model-selection"


def _client():
    return boto3.client("appconfigdata", region_name="us-east-1")


def _provider(client) -> ConfigProvider:
    return ConfigProvider(
        client,
        application=_APP,
        environment=_ENV,
        profile=_PROF,
        fallback=FALLBACK,
    )


def _session(token: str = "tok-1") -> dict:
    return {"InitialConfigurationToken": token}


def _latest(doc, next_token: str = "tok-2") -> dict:
    data = json.dumps(doc).encode() if isinstance(doc, (dict, list)) else doc
    return {
        "NextPollConfigurationToken": next_token,
        "NextPollIntervalInSeconds": 60,
        "ContentType": "application/json",
        "Configuration": data,
    }


class ConfigProviderTests(unittest.TestCase):
    def test_reads_appconfig(self) -> None:
        client = _client()
        stub = Stubber(client)
        stub.add_response(
            "start_configuration_session",
            _session(),
            {
                "ApplicationIdentifier": _APP,
                "EnvironmentIdentifier": _ENV,
                "ConfigurationProfileIdentifier": _PROF,
            },
        )
        stub.add_response(
            "get_latest_configuration",
            _latest({"amount_threshold": 25000, "extract_model_id": "m-x"}),
            {"ConfigurationToken": "tok-1"},
        )
        stub.activate()
        result = _provider(client).get()
        stub.deactivate()
        self.assertEqual(result.source, "appconfig")
        self.assertEqual(result.config["amount_threshold"], 25000.0)
        self.assertEqual(result.config["extract_model_id"], "m-x")
        self.assertEqual(result.rejected, ())

    def test_fetch_error_falls_back(self) -> None:
        client = _client()
        stub = Stubber(client)
        stub.add_response(
            "start_configuration_session",
            _session(),
            {
                "ApplicationIdentifier": _APP,
                "EnvironmentIdentifier": _ENV,
                "ConfigurationProfileIdentifier": _PROF,
            },
        )
        stub.add_client_error("get_latest_configuration", "ThrottlingException")
        stub.activate()
        result = _provider(client).get()
        stub.deactivate()
        self.assertEqual(result.source, "fallback")
        self.assertEqual(result.config, FALLBACK)

    def test_empty_configuration_uses_last_known_good(self) -> None:
        client = _client()
        stub = Stubber(client)
        stub.add_response("start_configuration_session", _session(), {
            "ApplicationIdentifier": _APP,
            "EnvironmentIdentifier": _ENV,
            "ConfigurationProfileIdentifier": _PROF,
        })
        stub.add_response(
            "get_latest_configuration",
            _latest({"amount_threshold": 25000}, next_token="tok-2"),
            {"ConfigurationToken": "tok-1"},
        )
        stub.add_response(
            "get_latest_configuration",
            _latest(b"", next_token="tok-3"),  # empty == unchanged
            {"ConfigurationToken": "tok-2"},
        )
        stub.activate()
        provider = _provider(client)
        first = provider.get()
        second = provider.get()
        stub.deactivate()
        self.assertEqual(first.source, "appconfig")
        self.assertEqual(second.source, "cache")
        self.assertEqual(second.config["amount_threshold"], 25000.0)

    def test_malformed_value_rejected_last_known_good_retained(self) -> None:
        client = _client()
        stub = Stubber(client)
        stub.add_response("start_configuration_session", _session(), {
            "ApplicationIdentifier": _APP,
            "EnvironmentIdentifier": _ENV,
            "ConfigurationProfileIdentifier": _PROF,
        })
        stub.add_response(
            "get_latest_configuration",
            _latest({"amount_threshold": "not-a-number", "extract_model_id": "m-x"}),
            {"ConfigurationToken": "tok-1"},
        )
        stub.activate()
        result = _provider(client).get()
        stub.deactivate()
        self.assertIn("amount_threshold", result.rejected)
        # bad value dropped → bootstrap value retained
        self.assertEqual(result.config["amount_threshold"], 10000.0)
        self.assertEqual(result.config["extract_model_id"], "m-x")

    def test_key_removed_upstream_leaves_the_merge(self) -> None:
        """Review #8: `_last_good` was the merge base, so a key deployed once
        stuck forever — removing it from the AppConfig document must actually
        remove it (fall back to bootstrap)."""
        client = _client()
        stub = Stubber(client)
        stub.add_response("start_configuration_session", _session(), {
            "ApplicationIdentifier": _APP,
            "EnvironmentIdentifier": _ENV,
            "ConfigurationProfileIdentifier": _PROF,
        })
        stub.add_response(
            "get_latest_configuration",
            _latest({"guardrail_id": "g-1", "amount_threshold": 25000}, next_token="tok-2"),
            {"ConfigurationToken": "tok-1"},
        )
        stub.add_response(
            "get_latest_configuration",
            _latest({"amount_threshold": 30000}, next_token="tok-3"),
            {"ConfigurationToken": "tok-2"},
        )
        stub.activate()
        provider = _provider(client)
        first = provider.get()
        second = provider.get()
        stub.deactivate()
        self.assertEqual(first.config["guardrail_id"], "g-1")
        self.assertNotIn("guardrail_id", second.config)
        self.assertEqual(second.config["amount_threshold"], 30000.0)

    def test_malformed_on_later_poll_retains_last_good_value(self) -> None:
        """AC-K4 across polls: the retained value is the last GOOD one, not
        the bootstrap — must survive the fresh-merge fix for review #8."""
        client = _client()
        stub = Stubber(client)
        stub.add_response("start_configuration_session", _session(), {
            "ApplicationIdentifier": _APP,
            "EnvironmentIdentifier": _ENV,
            "ConfigurationProfileIdentifier": _PROF,
        })
        stub.add_response(
            "get_latest_configuration",
            _latest({"amount_threshold": 25000}, next_token="tok-2"),
            {"ConfigurationToken": "tok-1"},
        )
        stub.add_response(
            "get_latest_configuration",
            _latest({"amount_threshold": "junk"}, next_token="tok-3"),
            {"ConfigurationToken": "tok-2"},
        )
        stub.activate()
        provider = _provider(client)
        provider.get()
        second = provider.get()
        stub.deactivate()
        self.assertIn("amount_threshold", second.rejected)
        self.assertEqual(second.config["amount_threshold"], 25000.0)

    def test_failed_poll_restarts_session_next_get(self) -> None:
        """Re-review #2: AppConfig Data tokens are single-use and expire; a
        failed poll left the dead token in place so every later poll failed
        identically until a cold start — AC-K3 silently violated forever."""
        client = _client()
        stub = Stubber(client)
        session_params = {
            "ApplicationIdentifier": _APP,
            "EnvironmentIdentifier": _ENV,
            "ConfigurationProfileIdentifier": _PROF,
        }
        stub.add_response("start_configuration_session", _session("tok-1"), session_params)
        stub.add_response(
            "get_latest_configuration",
            _latest({"amount_threshold": 25000}, next_token="tok-2"),
            {"ConfigurationToken": "tok-1"},
        )
        stub.add_client_error(
            "get_latest_configuration", "BadRequestException", expected_params=None
        )
        # recovery: a FRESH session must be started, not the dead token reused
        stub.add_response("start_configuration_session", _session("tok-9"), session_params)
        stub.add_response(
            "get_latest_configuration",
            _latest({"amount_threshold": 42000}, next_token="tok-10"),
            {"ConfigurationToken": "tok-9"},
        )
        stub.activate()
        provider = _provider(client)
        first = provider.get()
        failed = provider.get()
        recovered = provider.get()
        stub.deactivate()
        stub.assert_no_pending_responses()
        self.assertEqual(first.config["amount_threshold"], 25000.0)
        self.assertEqual(failed.source, "cache")  # fail-safe held (AC-K1)
        self.assertEqual(recovered.source, "appconfig")
        self.assertEqual(recovered.config["amount_threshold"], 42000.0)

    def test_validate_config_is_pure(self) -> None:
        clean, rejected = validate_config(
            {
                "amount_threshold": "abc",
                "extract_model_id": "  ",
                "summary_model_id": "ok",
            }
        )
        self.assertNotIn("amount_threshold", clean)
        self.assertNotIn("extract_model_id", clean)
        self.assertEqual(clean["summary_model_id"], "ok")
        self.assertEqual(set(rejected), {"amount_threshold", "extract_model_id"})


if __name__ == "__main__":
    unittest.main()
