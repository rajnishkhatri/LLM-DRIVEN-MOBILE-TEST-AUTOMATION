"""Stage 15 — the claim-status specialist, built with Strands (code-first).

Contrast with the Bedrock Agents lab: there, AWS ran the agentic loop. Here the
loop runs in THIS process. The model decides to call a tool; our Python executes
it, in-process, synchronously; the result goes back to the model; it answers.

Three things below are the whole mechanism:
  (1) @tool turns a plain function into something the model can call. Strands
      builds the tool's JSON schema from the type hints + docstring — so the
      signature and the docstring are not decoration, they are the contract.
  (2) BedrockModel is just the model handle; we pin it to Haiku 4.5, which the
      claim-processor profile already has enabled. Status triage is light work.
  (3) Agent(model, tools, system_prompt) wires them together. Calling
      agent("...") runs the loop and returns the final answer.
"""

from __future__ import annotations

import os
import sys
import json

import boto3
from botocore.exceptions import ClientError
from strands import Agent, tool
from strands.models import BedrockModel

BUCKET = os.environ.get("CLAIM_BUCKET", "claim-documents-poc-rk-20260922")
RESULTS_PREFIX = "results/claims/"
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

# One boto3 session for both the model handle and the tool, pinned to the
# claim-processor profile so a local run uses the same identity as the pipeline.
_session = boto3.Session(
    profile_name=os.environ.get("AWS_PROFILE", "claim-processor"),
    region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
)
_s3 = _session.client("s3")


def _result_key(claim_id: str) -> str:
    """Map a claim id to the S3 key the pipeline wrote its result under."""
    if claim_id.endswith(".json"):
        return claim_id if claim_id.startswith(RESULTS_PREFIX) else RESULTS_PREFIX + claim_id
    return f"{RESULTS_PREFIX}{claim_id}.txt.json"


def _available_ids() -> list[str]:
    """List the claim ids that actually have a result (for an honest miss)."""
    resp = _s3.list_objects_v2(Bucket=BUCKET, Prefix=RESULTS_PREFIX)
    ids = []
    for obj in resp.get("Contents", []):
        stem = obj["Key"][len(RESULTS_PREFIX):]
        if stem:  # skip the prefix "folder" marker itself
            ids.append(stem.removesuffix(".json").removesuffix(".txt"))
    return ids


@tool
def get_claim_status(claim_id: str) -> dict:
    """Look up the processing status and decision for one insurance claim.

    Args:
        claim_id: The claim identifier, e.g. "auto-fl-clean" or "breaker-test-1".

    Returns a dict with the decision (route), whether validation accepted it,
    the claimant and amount, and whether it went through a degraded path. If the
    claim has no result, returns found=False plus the ids that do exist.
    """
    key = _result_key(claim_id)
    try:
        body = _s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
            return {"found": False, "claim_id": claim_id, "available": _available_ids()}
        raise
    doc = json.loads(body)
    info = doc.get("extracted_info") or {}
    return {
        "found": True,
        "claim_id": claim_id,
        "decision": doc.get("route"),
        "validation_accepted": (doc.get("validation") or {}).get("accepted"),
        "validation_flags": (doc.get("validation") or {}).get("flags", []),
        "claimant_name": info.get("claimant_name"),
        "claim_amount": info.get("claim_amount"),
        "incident_date": info.get("incident_date"),
        "degraded": bool(doc.get("degradation_tier")),
        "breaker_state": doc.get("breaker_state"),
    }


SYSTEM_PROMPT = (
    "You are a claim-status assistant for an insurance pipeline. When a customer "
    "asks about a claim, call get_claim_status with the claim id, then answer in "
    "two or three plain sentences: the decision (approved automatically, or sent "
    "for human review), the claimant and amount, and anything unusual (a degraded "
    "extraction or a validation flag). If the id is not found, tell the customer "
    "which claim ids exist. Never invent a status the tool did not return."
)

agent = Agent(model=BedrockModel(model_id=MODEL_ID, boto_session=_session),
              tools=[get_claim_status], system_prompt=SYSTEM_PROMPT)


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is the status of claim auto-fl-clean?"
    print(f"\n>>> {question}\n")
    agent(question)  # Strands streams the loop (tool call + answer) to stdout.
    print()
