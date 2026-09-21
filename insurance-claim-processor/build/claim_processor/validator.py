from __future__ import annotations

import json
import re
from typing import Any

from claim_processor.models import EXTRACT_FIELDS, ValidationResult

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_PAN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")


def strip_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


class ContentValidator:
    """Schema + PII + citation gate — Validate Extracted Content component.

    Stands in for Bedrock Guardrails in the PoC (see solution-design §4).
    """

    def parse_extraction(self, raw: str | dict[str, Any]) -> ValidationResult:
        flags: list[str] = []
        if isinstance(raw, dict):
            parsed = raw
        else:
            try:
                parsed = json.loads(strip_fences(raw))
            except json.JSONDecodeError:
                return ValidationResult(accepted=False, flags=["invalid_json"])
        if not isinstance(parsed, dict):
            return ValidationResult(accepted=False, flags=["not_an_object"])
        missing = [f for f in EXTRACT_FIELDS if f not in parsed]
        if missing:
            flags.append("missing_keys:" + ",".join(missing))
        amount = parsed.get("claim_amount")
        if amount is not None:
            try:
                parsed["claim_amount"] = float(amount)
            except (TypeError, ValueError):
                flags.append("claim_amount_not_numeric")
                parsed["claim_amount"] = None
        empty = [f for f in EXTRACT_FIELDS if parsed.get(f) in (None, "")]
        if empty:
            flags.append("empty_fields:" + ",".join(empty))
        accepted = "invalid_json" not in flags and "not_an_object" not in flags and "missing_keys" not in "".join(flags)
        # empty fields flag but still accepted so C11/HITL can proceed
        if any(f.startswith("missing_keys:") for f in flags):
            accepted = False
        return ValidationResult(accepted=accepted, flags=flags, parsed=parsed)

    def scan_pii(self, text: str) -> list[str]:
        flags: list[str] = []
        if _SSN.search(text):
            flags.append("pii_ssn")
        if _PAN.search(text):
            flags.append("pii_pan")
        return flags

    def require_citations(self, citations: list[str], ungrounded: bool) -> list[str]:
        if ungrounded:
            return []
        if not citations:
            return ["missing_citations"]
        return []

    def validate_result(
        self,
        extraction_raw: str | dict[str, Any],
        summary: str,
        citations: list[str],
        ungrounded: bool,
    ) -> ValidationResult:
        base = self.parse_extraction(extraction_raw)
        flags = list(base.flags)
        flags.extend(self.scan_pii(summary))
        flags.extend(self.require_citations(citations, ungrounded))
        accepted = base.accepted and "pii_ssn" not in flags and "pii_pan" not in flags
        if ungrounded:
            flags.append("ungrounded")
        return ValidationResult(accepted=accepted, flags=flags, parsed=base.parsed)
