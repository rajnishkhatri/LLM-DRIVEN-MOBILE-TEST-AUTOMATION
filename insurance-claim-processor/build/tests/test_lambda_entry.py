"""The Lambda bootstrap must inject a real-client pipeline (deploy-readiness F1)."""

from __future__ import annotations

import json
import unittest
from unittest import mock

import boto3

from claim_processor import handler, lambda_entry
from claim_processor.config_provider import ConfigProvider
from claim_processor.pipeline import ClaimPipeline
from claim_processor.store import S3DocumentStore

_ENV = {
    "CLAIM_PROCESSOR_REGION": "us-east-1",
    "CLAIM_PROCESSOR_GUARDRAIL_ID": "l2oanwsu6no2",
    "CLAIM_PROCESSOR_EXTRACT_MODEL_ID": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "CLAIM_PROCESSOR_APPCONFIG_ENV": "poc",
}


def _offline_session() -> boto3.Session:
    # Client construction is offline; no call is made until a method runs.
    return boto3.Session(
        region_name="us-east-1", aws_access_key_id="test", aws_secret_access_key="test"
    )


class LambdaEntryTests(unittest.TestCase):
    def test_every_asl_lambda_has_an_entrypoint(self) -> None:
        with open("sfn/asl.json", encoding="utf-8") as fh:
            raw = fh.read()
        names = {
            seg.split("function:claim-processor-")[1].split('"')[0]
            for seg in raw.split("arn:aws:lambda")[1:]
        }
        missing = {n for n in names if n.replace("-", "_") not in lambda_entry.ENTRYPOINTS}
        # await-review is the deferred HITL token-parking Lambda (F2).
        self.assertEqual(missing, {"await-review"})
        for name in lambda_entry.ENTRYPOINTS:
            self.assertTrue(callable(getattr(lambda_entry, name)))

    def test_build_pipeline_wires_real_clients_and_config_provider(self) -> None:
        pipe = lambda_entry.build_pipeline(_offline_session(), environ=_ENV)
        self.assertIsInstance(pipe, ClaimPipeline)
        self.assertIsInstance(pipe.store, S3DocumentStore)
        self.assertIsInstance(pipe.config_provider, ConfigProvider)
        self.assertEqual(pipe.policy.guardrail_id, "l2oanwsu6no2")
        self.assertEqual(pipe.extract_model_id, _ENV["CLAIM_PROCESSOR_EXTRACT_MODEL_ID"])
        self.assertEqual(pipe.config_provider._env, "poc")
        self.assertEqual(pipe.config_provider._app, "claim-processor")
        # Fallback is the env bootstrap, in the AppConfig document's shape.
        fallback = pipe.config_provider._fallback
        self.assertEqual(fallback["guardrail_id"], "l2oanwsu6no2")
        self.assertNotIn("kb_id", fallback)  # None values omitted
        self.assertIn("flags", fallback)
        self.assertTrue(pipe.retriever.documents if hasattr(pipe.retriever, "documents") else True)

    def test_entry_injects_pipeline_with_lambda_calling_convention(self) -> None:
        fake = mock.Mock(spec=ClaimPipeline)
        with mock.patch.object(lambda_entry, "pipeline", return_value=fake):
            # Lambda calls fn(event, context) positionally; handler.* would raise
            # MissingPipelineError without the injection.
            out = lambda_entry.breaker_probe({"bucket": "b", "key": "claims/x"}, None)
        fake.refresh_policy.assert_called_once()
        fake.breaker_is_open.assert_called_once()
        self.assertIn("breaker_open", out)
        with self.assertRaises(handler.MissingPipelineError):
            handler.breaker_probe({"bucket": "b", "key": "claims/x"}, None)

    def test_pipeline_is_built_once_per_container(self) -> None:
        lambda_entry._pipeline = None
        try:
            with mock.patch.object(
                lambda_entry, "build_pipeline", return_value="PIPE"
            ) as build, mock.patch.dict("os.environ", _ENV):
                self.assertEqual(lambda_entry.pipeline(), "PIPE")
                self.assertEqual(lambda_entry.pipeline(), "PIPE")
            build.assert_called_once()
        finally:
            lambda_entry._pipeline = None
