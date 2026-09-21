from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from claim_processor.compare import compare_models
from claim_processor.invoker import ModelInvoker, bedrock_client_config
from claim_processor.models import EXTRACT_MODEL_EXAMPLE, SUMMARY_MODEL_EXAMPLE
from claim_processor.pipeline import ClaimPipeline
from claim_processor.prompts import PromptTemplateManager
from claim_processor.rag import PolicyRetriever
from claim_processor.store import (
    LocalDocumentStore,
    S3DocumentStore,
    get_pending_review,
)
from claim_processor.validator import ContentValidator

_DECIDE_DECISIONS = frozenset({"approve", "correct", "reject"})

_HERE = Path(__file__).resolve().parent.parent

SPIKE_CLAIM_KEYS = (
    "claims/auto-fl-collision.txt",
    "claims/home-tx-water.txt",
    "claims/incomplete-claim.txt",
    "claims/auto-fl-photo.png",
)


def _refuse_real_aws() -> None:
    if os.environ.get("CLAIM_PROCESSOR_REAL_AWS") == "1":
        return
    raise SystemExit(
        "Refusing to create real AWS clients. Offline is the default.\n"
        "Set CLAIM_PROCESSOR_REAL_AWS=1 only at the gated aws-ai-validate step."
    )


def build_local_pipeline(root: Path, extract_model: str, summary_model: str) -> ClaimPipeline:
    return ClaimPipeline(
        store=LocalDocumentStore(root),
        invoker=ModelInvoker(_require_client("bedrock-runtime"), default_model_id=extract_model),
        templates=PromptTemplateManager(),
        validator=ContentValidator(),
        retriever=PolicyRetriever(root / "samples" / "policies"),
        extract_model_id=extract_model,
        summary_model_id=summary_model,
    )


def resolve_model_id(cli_value: str | None, env_name: str, example: str) -> str:
    """CLI flag > env > example default (Wave 0 §4 — T-11)."""
    if cli_value:
        return cli_value
    env = os.environ.get(env_name)
    if env:
        return env
    return example


def send_decision(
    sfn_client,
    *,
    task_token: str,
    decision: str,
    reviewer_id: str,
    corrections: dict | None = None,
) -> dict:
    """Resume a waitForTaskToken via SendTaskSuccess (ADR 0005)."""
    if decision not in _DECIDE_DECISIONS:
        raise ValueError(f"unknown decision: {decision!r}")
    payload: dict = {"decision": decision, "reviewer_id": reviewer_id}
    if corrections is not None:
        payload["corrections"] = corrections
    sfn_client.send_task_success(taskToken=task_token, output=json.dumps(payload))
    return payload


def inspect_pending(store, bucket: str, key: str) -> dict:
    return get_pending_review(store, bucket, key)


def capture_claim(result, *, latency_seconds: float, gold: dict | None = None) -> dict:
    """Record A4/H2/J2 spike metrics: resolved ids, grounding, PII, usage, latency."""
    extracted = result.extracted_info if isinstance(result.extracted_info, dict) else {}
    amount_rel_error = None
    if gold is not None and extracted.get("claim_amount") is not None:
        gold_amount = float(gold["claim_amount"])
        got = float(extracted["claim_amount"])
        amount_rel_error = abs(got - gold_amount) / gold_amount if gold_amount else abs(got)
    flags = list(result.validation.flags)
    guardrail = result.guardrail or {"intervened": False, "actions": []}
    return {
        "accepted": result.validation.accepted,
        "ungrounded": result.ungrounded,
        "citations": list(result.citations),
        "pii_flags": [f for f in flags if f.startswith("pii_")],
        "guardrail": guardrail,
        "guardrail_intervened": bool(guardrail.get("intervened")),
        "usage": result.usage,
        "latency_seconds": latency_seconds,
        "extract_model_id": result.extract_model_id,
        "summary_model_id": result.summary_model_id,
        "understand_model_id": result.understand_model_id,
        "amount_rel_error": amount_rel_error,
    }


def run_real_spike(
    pipeline,
    bucket: str,
    keys: tuple[str, ...] = SPIKE_CLAIM_KEYS,
    *,
    gold_dir: Path | None = None,
) -> dict:
    started = time.perf_counter()
    claims: list[dict] = []
    for key in keys:
        t0 = time.perf_counter()
        result = pipeline.process(bucket, key)
        gold = None
        if gold_dir is not None:
            gold_path = gold_dir / f"{Path(key).stem}.json"
            if gold_path.is_file():
                gold = json.loads(gold_path.read_text(encoding="utf-8"))
        row = capture_claim(
            result, latency_seconds=time.perf_counter() - t0, gold=gold
        )
        row["key"] = key
        claims.append(row)
    return {
        "claims": claims,
        "totals": {
            "count": len(claims),
            "latency_seconds": time.perf_counter() - started,
        },
    }


def _require_client(service: str):
    _refuse_real_aws()
    import boto3

    session = boto3.Session(region_name="us-east-1")
    if service == "bedrock-runtime":
        return session.client("bedrock-runtime", config=bedrock_client_config())
    return session.client(service)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Claim document PoC (offline-first)")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["decide", "inspect"],
        help="decide: SendTaskSuccess resume; inspect: print pending-review JSON",
    )
    parser.add_argument("--bucket", default="samples")
    parser.add_argument("--key", default="claims/auto-fl-collision.txt")
    parser.add_argument("--root", type=Path, default=_HERE)
    parser.add_argument("--extract-model", default=None)
    parser.add_argument("--summary-model", default=None)
    parser.add_argument("--compare", action="store_true")
    parser.add_argument(
        "--compare-models",
        default=f"{EXTRACT_MODEL_EXAMPLE},{SUMMARY_MODEL_EXAMPLE}",
        help="Comma-separated example ids to re-verify",
    )
    parser.add_argument("--s3", action="store_true", help="Use S3 (requires CLAIM_PROCESSOR_REAL_AWS=1)")
    parser.add_argument(
        "--real",
        action="store_true",
        help="Use real AWS (requires CLAIM_PROCESSOR_REAL_AWS=1). --s3 stays valid.",
    )
    parser.add_argument("--fake", action="store_true", help="Run the pipeline with a deterministic FakeModelInvoker (no AWS)")
    parser.add_argument(
        "--spike",
        action="store_true",
        help="Feasibility spike: 3 text + 1 image; capture accuracy/grounding/PII/$/latency",
    )
    parser.add_argument("--task-token", help="Step Functions task token (decide)")
    parser.add_argument(
        "--decision",
        choices=["approve", "correct", "reject"],
        help="HITL decision (decide)",
    )
    parser.add_argument("--reviewer-id", help="Reviewer identity recorded on resume (decide)")
    parser.add_argument("--corrections", help="JSON object of field corrections (decide correct)")
    args = parser.parse_args(argv)

    extract_model = resolve_model_id(
        args.extract_model, "CLAIM_PROCESSOR_EXTRACT_MODEL_ID", EXTRACT_MODEL_EXAMPLE
    )
    summary_model = resolve_model_id(
        args.summary_model, "CLAIM_PROCESSOR_SUMMARY_MODEL_ID", SUMMARY_MODEL_EXAMPLE
    )

    if args.command == "decide":
        if not args.task_token or not args.decision or not args.reviewer_id:
            parser.error("decide requires --task-token, --decision, and --reviewer-id")
        corrections = json.loads(args.corrections) if args.corrections else None
        payload = send_decision(
            _require_client("stepfunctions"),
            task_token=args.task_token,
            decision=args.decision,
            reviewer_id=args.reviewer_id,
            corrections=corrections,
        )
        print(json.dumps(payload, indent=2))
        return 0

    if args.command == "inspect":
        if args.s3 or args.real:
            store = S3DocumentStore(_require_client("s3"))
        else:
            store = LocalDocumentStore(args.root)
        print(json.dumps(inspect_pending(store, args.bucket, args.key), indent=2))
        return 0

    if args.fake:
        from claim_processor.fake import FakeModelInvoker

        pipeline = ClaimPipeline(
            store=LocalDocumentStore(args.root),
            invoker=FakeModelInvoker(),
            templates=PromptTemplateManager(),
            validator=ContentValidator(),
            retriever=PolicyRetriever(args.root / "samples" / "policies"),
            extract_model_id=extract_model,
            summary_model_id=summary_model,
        )
        return _emit_pipeline(pipeline, args)

    if args.s3 or args.real:
        store = S3DocumentStore(_require_client("s3"))
        invoker = ModelInvoker(_require_client("bedrock-runtime"), default_model_id=extract_model)
        pipeline = ClaimPipeline(
            store=store,
            invoker=invoker,
            templates=PromptTemplateManager(),
            validator=ContentValidator(),
            retriever=PolicyRetriever(args.root / "samples" / "policies"),
            extract_model_id=extract_model,
            summary_model_id=summary_model,
        )
        return _emit_pipeline(pipeline, args)

    if args.compare:
        _refuse_real_aws()
        text = (args.root / args.bucket / args.key).read_text(encoding="utf-8")
        invoker = ModelInvoker(_require_client("bedrock-runtime"))
        models = [m.strip() for m in args.compare_models.split(",") if m.strip()]
        print(json.dumps(compare_models(text, invoker, models), indent=2))
        return 0

    parser.error("Local mode has no FM without AWS. Run tests (Stubber) or pass --s3 with CLAIM_PROCESSOR_REAL_AWS=1.")
    return 2


def _emit_pipeline(pipeline, args) -> int:
    if args.spike:
        report = run_real_spike(
            pipeline,
            args.bucket,
            gold_dir=args.root / "samples" / "gold",
        )
        print(json.dumps(report, indent=2))
        return 0
    result = pipeline.process(args.bucket, args.key)
    print(json.dumps(_result_dict(result), indent=2))
    return 0 if result.validation.accepted else 2


def _result_dict(result) -> dict:
    return {
        "extracted_info": result.extracted_info,
        "summary": result.summary,
        "citations": result.citations,
        "ungrounded": result.ungrounded,
        "validation": {"accepted": result.validation.accepted, "flags": result.validation.flags},
        "extract_model_id": result.extract_model_id,
        "summary_model_id": result.summary_model_id,
    }


if __name__ == "__main__":
    sys.exit(main())
