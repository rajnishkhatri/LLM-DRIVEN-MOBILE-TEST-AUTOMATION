from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


EXTRACT_FIELDS = (
    "claimant_name",
    "policy_number",
    "incident_date",
    "claim_amount",
    "incident_description",
)

# Examples to RE-VERIFY via list_foundation_models / list_inference_profiles.
# Many current ids are inference-profile-only (us./global. prefix).
EXTRACT_MODEL_EXAMPLE = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
SUMMARY_MODEL_EXAMPLE = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
UNDERSTAND_MODEL_EXAMPLE = "us.amazon.nova-pro-v1:0"


@dataclass
class PolicyChunk:
    chunk_id: str
    source: str
    text: str
    score: float
    jurisdiction: str = ""
    line_of_business: str = ""


@dataclass
class ValidationResult:
    accepted: bool
    flags: list[str] = field(default_factory=list)
    parsed: dict[str, Any] | None = None


@dataclass
class ProcessingResult:
    extracted_info: dict[str, Any] | str
    summary: str
    citations: list[str]
    ungrounded: bool
    validation: ValidationResult
    extract_model_id: str
    summary_model_id: str
    prompt_versions: dict[str, str]
    usage: dict[str, Any] = field(default_factory=dict)
    route: str | None = None
    review: dict[str, Any] | None = None
    guardrail: dict[str, Any] | None = None
    sfn_execution_arn: str | None = None
    schema_version: str = "1.0"
    understand_model_id: str | None = None
    embeddings: dict[str, Any] | None = None

    def to_record(self, claim_key: str | None = None) -> dict[str, Any]:
        """§7-shaped dict: validation flattened to {accepted, flags};
        includes new defaulted fields. Optional claim_key."""
        record: dict[str, Any] = {
            "extracted_info": self.extracted_info,
            "summary": self.summary,
            "citations": self.citations,
            "ungrounded": self.ungrounded,
            "validation": {
                "accepted": self.validation.accepted,
                "flags": self.validation.flags,
            },
            "extract_model_id": self.extract_model_id,
            "summary_model_id": self.summary_model_id,
            "prompt_versions": self.prompt_versions,
            "usage": self.usage,
            "route": self.route,
            "review": self.review,
            "guardrail": self.guardrail,
            "sfn_execution_arn": self.sfn_execution_arn,
            "schema_version": self.schema_version,
            "understand_model_id": self.understand_model_id,
            "embeddings": self.embeddings,
        }
        if claim_key is not None:
            record["claim_key"] = claim_key
        return record
