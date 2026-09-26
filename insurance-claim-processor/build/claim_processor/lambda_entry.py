"""AWS Lambda entrypoints — the deploy-time bootstrap (deploy-readiness F1).

`handler.py` is a thin SFN adapter whose functions are keyword-only on
`pipeline=` and construct no clients (Wave 0 §11). Lambda invokes a handler as
`fn(event, context)`, so pointing a function straight at `handler.*` raises
`MissingPipelineError`. This module is the one place that:

1. builds the real clients (S3, bedrock-runtime, appconfigdata) — once per warm
   container, never at import;
2. seeds the AppConfig fallback from the `CLAIM_PROCESSOR_*` env bootstrap
   (AC-K1: config unreachable → last-known-good → env → defaults);
3. constructs `ClaimPipeline(..., config_provider=ConfigProvider(...))` so a
   config change is adopted within one poll with no redeploy (AC-K3 — DEPLOY.md
   §5.1's warning);
4. injects that pipeline into each `handler.*` function.

Lambda handler string per function: `claim_processor.lambda_entry.<name>`.
Env (all optional; defaults match DEPLOY.md §1):
  CLAIM_PROCESSOR_APPCONFIG_APP / _ENV / _PROFILE  (names, not IDs — data plane)
  CLAIM_PROCESSOR_POLICY_DIR  (RAG policy documents; default = bundled samples/policies)
  plus the `CLAIM_PROCESSOR_*` keys read by `EscalationPolicy.from_env`.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from claim_processor import handler
from claim_processor.config import EscalationPolicy
from claim_processor.config_provider import ConfigProvider
from claim_processor.invoker import ModelInvoker, bedrock_client_config
from claim_processor.pipeline import ClaimPipeline
from claim_processor.prompts import PromptTemplateManager
from claim_processor.rag import PolicyRetriever
from claim_processor.store import S3DocumentStore
from claim_processor.validator import ContentValidator

_DEFAULT_POLICY_DIR = Path(__file__).resolve().parent.parent / "samples" / "policies"

_pipeline: ClaimPipeline | None = None


def bootstrap_config(policy: EscalationPolicy) -> dict[str, Any]:
    """The env bootstrap in the AppConfig document's shape (ConfigProvider fallback).

    `None` values are omitted so `EscalationPolicy.from_config` falls through to
    the dataclass default instead of adopting an explicit null.
    """
    doc: dict[str, Any] = {
        "region": policy.region,
        "extract_model_id": policy.extract_model_id,
        "summary_model_id": policy.summary_model_id,
        "understand_model_id": policy.understand_model_id,
        "guardrail_id": policy.guardrail_id,
        "kb_id": policy.kb_id,
        "amount_threshold": policy.amount_threshold,
        "force_review_flags": list(policy.force_review_flags),
        "ensemble_models": list(policy.ensemble_models),
        "degradation_tiers": list(policy.degradation_tiers),
        "flags": dict(policy.flags),
    }
    return {k: v for k, v in doc.items() if v is not None}


def build_pipeline(session: Any, *, environ: dict[str, str] | None = None) -> ClaimPipeline:
    """Pure builder: every client comes from `session` (a boto3.Session or a test double)."""
    env = os.environ if environ is None else environ
    policy = EscalationPolicy.from_env() if environ is None else _policy_from(environ)
    provider = ConfigProvider(
        session.client("appconfigdata"),
        application=env.get("CLAIM_PROCESSOR_APPCONFIG_APP", "claim-processor"),
        environment=env.get("CLAIM_PROCESSOR_APPCONFIG_ENV", "poc"),
        profile=env.get("CLAIM_PROCESSOR_APPCONFIG_PROFILE", "model-selection"),
        fallback=bootstrap_config(policy),
    )
    policy_dir = Path(env.get("CLAIM_PROCESSOR_POLICY_DIR") or _DEFAULT_POLICY_DIR)
    return ClaimPipeline(
        store=S3DocumentStore(session.client("s3")),
        invoker=ModelInvoker(
            session.client("bedrock-runtime", config=bedrock_client_config(policy.region)),
            default_model_id=policy.extract_model_id,
        ),
        templates=PromptTemplateManager(),
        validator=ContentValidator(),
        retriever=PolicyRetriever(policy_dir),
        policy=policy,
        config_provider=provider,
    )


def _policy_from(environ: dict[str, str]) -> EscalationPolicy:
    """`EscalationPolicy.from_env` against an explicit mapping (tests)."""
    saved = dict(os.environ)
    try:
        os.environ.clear()
        os.environ.update(environ)
        return EscalationPolicy.from_env()
    finally:
        os.environ.clear()
        os.environ.update(saved)


def pipeline() -> ClaimPipeline:
    """One pipeline per warm Lambda container (clients are built on first call)."""
    global _pipeline
    if _pipeline is None:
        import boto3  # never at module import (Wave 0 §11)

        region = os.environ.get("CLAIM_PROCESSOR_REGION") or "us-east-1"
        _pipeline = build_pipeline(boto3.Session(region_name=region))
    return _pipeline


def _entry(fn: Callable[..., dict[str, Any]]) -> Callable[[dict[str, Any], Any], dict[str, Any]]:
    def _lambda_handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
        return fn(event, context, pipeline=pipeline())

    _lambda_handler.__name__ = fn.__name__
    _lambda_handler.__doc__ = fn.__doc__
    return _lambda_handler


breaker_probe = _entry(handler.breaker_probe)
understand_extract = _entry(handler.understand_extract)
degraded_extract = _entry(handler.degraded_extract)
validate = _entry(handler.validate)
retrieve_summarize = _entry(handler.retrieve_summarize)
await_review = _entry(handler.await_review)
record = _entry(handler.record)
expire_review = _entry(handler.expire_review)

ENTRYPOINTS = (
    "breaker_probe",
    "understand_extract",
    "degraded_extract",
    "validate",
    "retrieve_summarize",
    "record",
    "expire_review",
)
