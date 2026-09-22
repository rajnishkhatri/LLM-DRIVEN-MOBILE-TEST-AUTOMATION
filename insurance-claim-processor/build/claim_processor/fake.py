from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent.parent
_IMAGE_GOLD = _HERE / "samples" / "gold" / "auto-fl-photo.json"


class FakeModelInvoker:
    """Deterministic stand-in for Converse so the CLI can demo without AWS."""

    def __init__(self, canned: dict[str, str] | None = None):
        self.canned = canned or {}
        self.calls: list[str] = []

    def converse(
        self,
        prompt: str,
        *,
        model_id: str | None = None,
        content: list[dict] | None = None,
        guardrail_config: dict | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        self.calls.append(model_id or "default")
        if "Extract the following fields" in prompt or _has_image(content):
            text = self.canned.get("extract") or _extract_from_prompt(prompt, content)
        else:
            text = self.canned.get("summary") or (
                "Summary: see extracted fields. Coverage follows the retrieved policy excerpts."
            )
        return {
            "text": text,
            "model_id": model_id or "fake",
            "stop_reason": "end_turn",
            "usage": {"inputTokens": 10, "outputTokens": 20, "totalTokens": 30},
            "guardrail": {"intervened": False, "actions": []},
        }


def _has_image(content: list[dict] | None) -> bool:
    if not content:
        return False
    return any(isinstance(block, dict) and "image" in block for block in content)


def _extract_from_prompt(prompt: str, content: list[dict] | None = None) -> str:
    if _has_image(content):
        return _IMAGE_GOLD.read_text(encoding="utf-8")
    if "Maria Elena Ruiz" in prompt:
        return json.dumps(
            {
                "claimant_name": "Maria Elena Ruiz",
                "policy_number": "POL-FL-AU-88421",
                "incident_date": "2026-03-11",
                "claim_amount": 4820.50,
                "incident_description": "Third party failed to yield; struck Civic quarter panel in Miami-Dade.",
            }
        )
    if "James K. Patel" in prompt:
        return json.dumps(
            {
                "claimant_name": "James K. Patel",
                "policy_number": "HO-TX-10993-B",
                "incident_date": "2026-04-02",
                "claim_amount": 12500,
                "incident_description": "Upstairs supply line failed; water into kitchen in Austin.",
            }
        )
    return json.dumps(
        {
            "claimant_name": "A. Nguyen",
            "policy_number": None,
            "incident_date": None,
            "claim_amount": None,
            "incident_description": "windshield chip on the interstate",
        }
    )
