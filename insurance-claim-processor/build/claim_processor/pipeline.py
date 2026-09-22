from __future__ import annotations

import json
import time
from typing import Any

from claim_processor.adapter import (
    BedrockConverseAdapter,
    CallOutcome,
    ModelAdapter,
    ThrottlingException,
)
from claim_processor.breaker import breaker_open
from claim_processor.config import EscalationPolicy
from claim_processor.degrade import (
    RULE_BASED,
    DegradationDisabledError,
    is_degraded,
    walk_tiers,
)
from claim_processor.ensemble import combine, has_quorum, resolve_quorum
from claim_processor.flags import assign_variant, ensemble_enabled, flag
from claim_processor.invoker import ModelInvoker
from claim_processor.metrics import DEFAULT_NAMESPACE, Metric, emit_metric
from claim_processor.models import (
    EXTRACT_FIELDS,
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
        adapter: ModelAdapter | None = None,
        config_provider: Any = None,
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
        # Model resilience (ADRs 0010-0015). When no adapter is injected, wrap
        # the existing invoker so the default path is unchanged.
        self.adapter: ModelAdapter = adapter or BedrockConverseAdapter.from_invoker(
            self.invoker, default_model_id=self.extract_model_id
        )
        self.config_provider = config_provider
        self._bootstrap = self.policy
        self._config_rejected: tuple[str, ...] = ()

    def process(self, bucket: str, key: str) -> ProcessingResult:
        self._refresh_policy()
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
        _apply_config_rejected(validation, extracted.get("config_rejected"))
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
            config_snapshot=extracted.get("config_snapshot"),
            model_variant=extracted.get("model_variant"),
            ensemble=extracted.get("ensemble"),
            degradation_tier=extracted.get("degradation_tier"),
            breaker_state=extracted.get("breaker_state"),
        )
        result.route = self.route(result)
        self.record(bucket, key, result)
        return result

    def refresh_policy(self) -> None:
        """Per-invocation config adoption for the handler layer (AC-K3).

        Review #4: the refresh ran only inside `process()` (the CLI path), so
        the deployed Step Functions handlers never saw a live AppConfig change.
        """
        self._refresh_policy()

    def breaker_is_open(self) -> bool:
        """Shared breaker state for the primary extract model (AC-N2/N3)."""
        return breaker_open(self.policy.flags or {}, self.extract_model_id)

    def _refresh_policy(self) -> None:
        """Adopt a runtime config change (AC-K3) with no code deploy."""
        if self.config_provider is None:
            return
        resolved = self.config_provider.get()
        # Rejected keys must reach routing as flags (AC-K4, review #10).
        self._config_rejected = tuple(resolved.rejected or ())
        self.policy = EscalationPolicy.from_config(resolved.config, base=self._bootstrap)
        self.extract_model_id = self.policy.extract_model_id
        self.summary_model_id = self.policy.summary_model_id

    def understand_extract(self, bucket: str, key: str) -> dict[str, Any]:
        payload = self.store.get_bytes(bucket, key)
        blocks = to_content_blocks(payload, filename=key)
        first = blocks[0]
        is_image = "image" in first
        flags = self.policy.flags or {}

        document_text = "" if is_image else first["text"]
        prompt_doc = "(image packet)" if is_image else document_text
        extract_prompt = self.templates.get_prompt("extract_info", document_text=prompt_doc)
        system = "You extract insurance claim fields as JSON."
        guardrail_config = self._guardrail_config()

        call_usage: dict[str, Any] = {}
        call_guardrail: dict[str, Any] = {"intervened": False, "actions": []}

        def invoke(model_id: str):
            nonlocal call_guardrail
            started = time.perf_counter()
            call_content = [{"text": extract_prompt}, first] if is_image else None
            result = self.adapter.invoke(
                extract_prompt,
                model_id=model_id,
                system=system,
                max_tokens=1000,
                content=call_content,
                guardrail_config=guardrail_config,
            )
            _accumulate_usage(call_usage, result.usage)
            call_guardrail = _merge_guardrail(call_guardrail, result.guardrail)
            self._emit_call_metrics(model_id, result, started)
            if result.outcome == CallOutcome.THROTTLED:
                raise ThrottlingException(f"model {model_id} throttled")
            return result

        primary = self._select_extract_model(key, flags, is_image)
        variant = "control" if is_image else assign_variant(key, flags)
        breaker_state: str | None = None
        ensemble_record: dict[str, Any] | None = None
        degradation_tier: str | None = None

        use_ensemble = (
            not is_image
            and ensemble_enabled(flags)
            and len(self.policy.ensemble_models) >= self._ensemble_quorum()
        )
        extracted_payload: Any
        understand_model_id: str | None
        if use_ensemble:
            member_outputs: list[tuple[str, dict]] = []
            for member in self.policy.ensemble_models:
                if breaker_open(flags, member):
                    breaker_state = "open"
                    continue
                result = invoke(member)
                if result.outcome == CallOutcome.OK:
                    parsed = self.validator.parse_extraction(result.text)
                    member_outputs.append(
                        (member, parsed.parsed if parsed.parsed is not None else {})
                    )
            if has_quorum(len(member_outputs), quorum=self._ensemble_quorum()):
                combined = combine(member_outputs, required_fields=EXTRACT_FIELDS)
                extracted_payload = combined.extracted
                ensemble_record = {
                    "members": [m for m, _ in member_outputs],
                    "agreement": combined.agreement,
                    "low_confidence_fields": combined.low_confidence_fields,
                }
                if combined.low_confidence_fields:
                    emit_metric(
                        DEFAULT_NAMESPACE,
                        {Metric.ENSEMBLE_DISAGREEMENT: (1, "Count")},
                        {"ModelId": "ensemble"},
                    )
                extract_model_id = "ensemble:" + "+".join(m for m, _ in member_outputs)
                understand_model_id = None
            else:
                use_ensemble = False  # sub-quorum → single-model fallback (AC-O5)

        if not use_ensemble and not flag(flags, "degradation_enabled"):
            # Kill-switch honored (review #11): no ladder, no rule-based floor.
            if breaker_open(flags, primary):
                raise DegradationDisabledError(
                    f"breaker open for {primary} and degradation disabled"
                )
            result = invoke(primary)
            if result.outcome != CallOutcome.OK:
                raise DegradationDisabledError(
                    f"extract failed ({result.outcome.value}) and degradation disabled"
                )
            parsed = self.validator.parse_extraction(result.text)
            extracted_payload = parsed.parsed if parsed.parsed is not None else result.text
            extract_model_id = result.model_id or primary
            understand_model_id = result.model_id if is_image else None
        elif not use_ensemble:
            tiers = self._extract_tiers(primary, is_image)
            walk = walk_tiers(
                document_text or "(image packet)",
                tiers,
                invoke,
                is_open=lambda m: breaker_open(flags, m),
            )
            if walk.trigger == "breaker":
                breaker_state = "open"
            if walk.tier == RULE_BASED:
                extracted_payload = walk.extracted
                extract_model_id = RULE_BASED
                understand_model_id = self.policy.understand_model_id if is_image else None
                degradation_tier = RULE_BASED
            else:
                parsed = self.validator.parse_extraction(walk.text)
                extracted_payload = parsed.parsed if parsed.parsed is not None else walk.text
                extract_model_id = walk.model_id or primary
                understand_model_id = walk.model_id if is_image else None
                degradation_tier = walk.tier if is_degraded(walk.tier) else None

        return {
            "document_text": document_text,
            "extracted_info": extracted_payload,
            "extract_model_id": extract_model_id,
            "understand_model_id": understand_model_id,
            "usage": call_usage,
            "guardrail": call_guardrail,
            "degradation_tier": degradation_tier,
            "ensemble": ensemble_record,
            "model_variant": f"{variant}:{primary}",
            "breaker_state": breaker_state,
            "config_snapshot": self._config_snapshot(),
            "config_rejected": list(self._config_rejected),
        }

    def _select_extract_model(self, key: str, flags: dict, is_image: bool) -> str:
        if is_image:
            return self.policy.understand_model_id
        if assign_variant(key, flags) == "candidate":
            return flags.get("candidate_model_id") or self.extract_model_id
        return self.extract_model_id

    def _extract_tiers(self, primary: str, is_image: bool) -> list[str]:
        configured = [t for t in self.policy.degradation_tiers if t != primary]
        tiers = [primary] + configured
        if RULE_BASED not in tiers:
            tiers = tiers + [RULE_BASED]  # always a floor (AC-P1)
        return tiers

    def _ensemble_quorum(self) -> int:
        flags = self.policy.flags or {}
        return resolve_quorum(
            flags.get("ensemble_quorum"), len(self.policy.ensemble_models)
        )

    def _guardrail_config(self) -> dict | None:
        if self.policy.guardrail_id:
            return {
                "guardrailIdentifier": self.policy.guardrail_id,
                "guardrailVersion": "DRAFT",
            }
        return None

    def _config_snapshot(self) -> dict[str, Any]:
        return {
            "extract_model_id": self.policy.extract_model_id,
            "summary_model_id": self.policy.summary_model_id,
            "understand_model_id": self.policy.understand_model_id,
            "amount_threshold": self.policy.amount_threshold,
            "ensemble_models": list(self.policy.ensemble_models),
            "degradation_tiers": list(self.policy.degradation_tiers),
            "flags": dict(self.policy.flags or {}),
        }

    def _emit_call_metrics(self, model_id: str, result: Any, started: float) -> None:
        elapsed_ms = (time.perf_counter() - started) * 1000
        metrics: dict[str, tuple[float, str]] = {
            Metric.LATENCY_MS: (round(elapsed_ms, 3), "Milliseconds")
        }
        if result.outcome != CallOutcome.OK:
            metrics[Metric.ERRORS] = (1, "Count")
        if result.outcome == CallOutcome.GUARDRAIL_INTERVENED:
            metrics[Metric.GUARDRAIL_INTERVENED] = (1, "Count")
        emit_metric(
            DEFAULT_NAMESPACE,
            metrics,
            {"ModelId": model_id or "unknown", "Outcome": result.outcome.value},
        )

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
        # Summary is single-model cascade — never ensembled (ADR 0013 / AC-O3).
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

    def result_from_event(
        self, event: dict[str, Any], validation: ValidationResult
    ) -> ProcessingResult:
        """Build the routed record from a merged SFN event.

        AC-R3: the resilience provenance (ensemble/degradation/breaker/config)
        must reach `route_claim` on the Step Functions path exactly as it does
        in `process()` — dropping a field here silently widens auto-approve.
        """
        _apply_config_rejected(validation, event.get("config_rejected"))
        return ProcessingResult(
            extracted_info=event["extracted_info"],
            summary=event["summary"],
            citations=event["citations"],
            ungrounded=event["ungrounded"],
            validation=validation,
            extract_model_id=event.get("extract_model_id") or "",
            summary_model_id=event.get("summary_model_id") or "",
            prompt_versions=self.templates.versions(),
            usage=event.get("usage") or {},
            guardrail=event.get("guardrail"),
            understand_model_id=event.get("understand_model_id"),
            config_snapshot=event.get("config_snapshot"),
            model_variant=event.get("model_variant"),
            ensemble=event.get("ensemble"),
            degradation_tier=event.get("degradation_tier"),
            breaker_state=event.get("breaker_state"),
            remediation=event.get("remediation"),
        )

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


def _apply_config_rejected(
    validation: ValidationResult, rejected: tuple[str, ...] | list[str] | None
) -> None:
    """Surface rejected AppConfig keys as routing flags (AC-K4, review #10)."""
    for key in rejected or ():
        rejected_flag = f"config_rejected:{key}"
        if rejected_flag not in validation.flags:
            validation.flags.append(rejected_flag)


def _accumulate_usage(into: dict[str, Any], delta: dict[str, Any] | None) -> None:
    """Sum token counts across calls — `dict.update` kept only the last call's
    usage, under-reporting an N-member ensemble's cost N× (review #6)."""
    for key, value in (delta or {}).items():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            base = into.get(key)
            into[key] = (base if isinstance(base, (int, float)) else 0) + value
        else:
            into[key] = value


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
