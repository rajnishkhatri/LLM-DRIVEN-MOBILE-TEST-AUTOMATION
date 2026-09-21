from __future__ import annotations

import json
from typing import Any

from claim_processor.config import EscalationPolicy
from claim_processor.invoker import ModelInvoker
from claim_processor.models import (
    EXTRACT_MODEL_EXAMPLE,
    SUMMARY_MODEL_EXAMPLE,
    ProcessingResult,
    ValidationResult,
)
from claim_processor.prompts import PromptTemplateManager
from claim_processor.rag import RetrieverProtocol, infer_scope
from claim_processor.routing import route_claim
from claim_processor.store import DocumentStore, put_pending_review
from claim_processor.understand import to_content_blocks
from claim_processor.validator import ContentValidator


def result_key_for(claim_key: str) -> str:
    """C9: one result object per claim key — overwrite is the PoC idempotent put."""
    return f"results/{claim_key}.json"


class UncleanAutoApproveError(ValueError):
    """auto_approve was requested for a result that fails the clean predicate."""


class MissingRouteError(ValueError):
    """record() requires route to have been set."""


class UnknownRouteError(ValueError):
    """route is not auto_approve or human_review."""


class ClaimPipeline:
    def __init__(
        self,
        store: DocumentStore,
        invoker: ModelInvoker,
        templates: PromptTemplateManager,
        validator: ContentValidator,
        retriever: RetrieverProtocol,
        *,
        extract_model_id: str = EXTRACT_MODEL_EXAMPLE,
        summary_model_id: str = SUMMARY_MODEL_EXAMPLE,
        policy: EscalationPolicy | None = None,
    ):
        self.store = store
        self.invoker = invoker
        self.templates = templates
        self.validator = validator
        self.retriever = retriever
        self.policy = policy or EscalationPolicy(
            extract_model_id=extract_model_id,
            summary_model_id=summary_model_id,
        )
        self.extract_model_id = self.policy.extract_model_id
        self.summary_model_id = self.policy.summary_model_id

    def process(self, bucket: str, key: str) -> ProcessingResult:
        extracted = self.understand_extract(bucket, key)
        summarized = self.retrieve_summarize(
            extracted["extracted_info"],
            extracted["document_text"],
        )
        validation = self.validate(
            extracted["extracted_info"],
            summary=summarized["summary"],
            citations=summarized["citations"],
            ungrounded=summarized["ungrounded"],
        )
        result = ProcessingResult(
            extracted_info=extracted["extracted_info"],
            summary=summarized["summary"],
            citations=summarized["citations"],
            ungrounded=summarized["ungrounded"],
            validation=validation,
            extract_model_id=extracted["extract_model_id"],
            summary_model_id=summarized["summary_model_id"],
            prompt_versions=self.templates.versions(),
            usage={
                "extract": extracted.get("usage") or {},
                "summary": summarized.get("usage") or {},
            },
            guardrail=_merge_guardrail(
                extracted.get("guardrail"), summarized.get("guardrail")
            ),
            understand_model_id=extracted.get("understand_model_id"),
        )
        result.route = self.route(result)
        self.record(bucket, key, result)
        return result

    def understand_extract(self, bucket: str, key: str) -> dict[str, Any]:
        payload = self.store.get_bytes(bucket, key)
        blocks = to_content_blocks(payload, filename=key)
        first = blocks[0]
        is_image = "image" in first
        if is_image:
            document_text = ""
            extract_prompt = self.templates.get_prompt(
                "extract_info", document_text="(image packet)"
            )
            extracted = self.invoker.converse(
                extract_prompt,
                model_id=self.policy.understand_model_id,
                system="You extract insurance claim fields as JSON.",
                max_tokens=1000,
                content=[{"text": extract_prompt}, first],
            )
            understand_model_id = extracted["model_id"]
        else:
            document_text = first["text"]
            extract_prompt = self.templates.get_prompt(
                "extract_info", document_text=document_text
            )
            extracted = self.invoker.converse(
                extract_prompt,
                model_id=self.extract_model_id,
                system="You extract insurance claim fields as JSON.",
                max_tokens=1000,
            )
            understand_model_id = None
        parsed = self.validator.parse_extraction(extracted["text"])
        extracted_payload: Any = (
            parsed.parsed if parsed.parsed is not None else extracted["text"]
        )
        return {
            "document_text": document_text,
            "extracted_info": extracted_payload,
            "extract_model_id": extracted["model_id"],
            "understand_model_id": understand_model_id,
            "usage": extracted.get("usage") or {},
            "guardrail": extracted.get("guardrail"),
        }

    def validate(
        self,
        extracted_info: dict[str, Any] | str,
        *,
        summary: str | None = None,
        citations: list[str] | None = None,
        ungrounded: bool | None = None,
    ) -> ValidationResult:
        if summary is None and citations is None and ungrounded is None:
            return self.validator.parse_extraction(extracted_info)
        return self.validator.validate_result(
            extracted_info,
            "" if summary is None else summary,
            [] if citations is None else citations,
            bool(ungrounded),
        )

    def retrieve_summarize(
        self,
        extracted_info: dict[str, Any] | str,
        document_text: str,
    ) -> dict[str, Any]:
        query_parts = []
        if isinstance(extracted_info, dict):
            query_parts.extend(
                str(extracted_info.get(f) or "")
                for f in ("incident_description", "policy_number")
            )
        query = " ".join(query_parts) or document_text[:500]
        parsed_for_scope = extracted_info if isinstance(extracted_info, dict) else None
        jurisdiction, line = infer_scope(parsed_for_scope, document_text)
        if jurisdiction is None:
            chunks = []
        else:
            chunks = self.retriever.retrieve(
                query, jurisdiction=jurisdiction, line_of_business=line
            )
        ungrounded = len(chunks) == 0
        policy_context = (
            "\n\n".join(f"[{c.chunk_id}] ({c.source})\n{c.text}" for c in chunks)
            if chunks
            else "(no policy excerpts retrieved)"
        )
        summary_prompt = self.templates.get_prompt(
            "generate_summary",
            extracted_info=json.dumps(extracted_info, indent=2)
            if not isinstance(extracted_info, str)
            else extracted_info,
            policy_context=policy_context,
        )
        summarized = self.invoker.converse(
            summary_prompt,
            model_id=self.summary_model_id,
            system="You summarize insurance claims. You do not invent coverage.",
            max_tokens=500,
        )
        return {
            "summary": summarized["text"],
            "citations": [c.chunk_id for c in chunks],
            "ungrounded": ungrounded,
            "summary_model_id": summarized["model_id"],
            "usage": summarized.get("usage") or {},
            "guardrail": summarized.get("guardrail"),
        }

    def route(self, result: ProcessingResult) -> str:
        return route_claim(result, self.policy)

    def record(
        self,
        bucket: str,
        key: str,
        result: ProcessingResult | dict[str, Any],
    ) -> dict[str, Any]:
        if isinstance(result, ProcessingResult):
            payload = _as_record(result, key)
        elif isinstance(result, dict):
            payload = dict(result)
            payload.setdefault("claim_key", key)
        else:
            raise TypeError(
                f"record expects ProcessingResult or dict, got {type(result).__name__}"
            )

        route = payload.get("route")
        if route is None:
            raise MissingRouteError("record requires route")
        if route not in ("auto_approve", "human_review"):
            raise UnknownRouteError(f"unknown route: {route!r}")

        review = payload.get("review")
        if route == "auto_approve":
            if isinstance(result, ProcessingResult):
                if route_claim(result, self.policy) != "auto_approve":
                    raise UncleanAutoApproveError(
                        "auto_approve requires the clean predicate (AC-E1)"
                    )
            self.store.put_json(bucket, result_key_for(key), payload)
        elif review:
            self.store.put_json(bucket, result_key_for(key), payload)
        else:
            put_pending_review(self.store, bucket, key, payload)
        return payload


def _as_record(result: ProcessingResult, claim_key: str) -> dict[str, Any]:
    return result.to_record(claim_key)


def _merge_guardrail(
    extract_guardrail: dict[str, Any] | None,
    summary_guardrail: dict[str, Any] | None,
) -> dict[str, Any]:
    left = extract_guardrail or {"intervened": False, "actions": []}
    right = summary_guardrail or {"intervened": False, "actions": []}
    return {
        "intervened": bool(left.get("intervened") or right.get("intervened")),
        "actions": list(left.get("actions") or []) + list(right.get("actions") or []),
    }
