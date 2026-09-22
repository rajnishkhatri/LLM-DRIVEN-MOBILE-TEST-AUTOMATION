from __future__ import annotations

import time
from typing import Any

from claim_processor.invoker import ModelInvoker
from claim_processor.prompts import PromptTemplateManager
from claim_processor.validator import ContentValidator


def compare_models(
    document_text: str,
    invoker: ModelInvoker,
    models: list[str],
    templates: PromptTemplateManager | None = None,
    validator: ContentValidator | None = None,
) -> dict[str, Any]:
    """Same extract prompt, different resolved model ids. Wall time is not a
    production SLO — it is the PoC comparison the exam asks for.
    """
    templates = templates or PromptTemplateManager()
    validator = validator or ContentValidator()
    prompt = templates.get_prompt("extract_info", document_text=document_text)
    results: dict[str, Any] = {}
    for model_id in models:
        started = time.perf_counter()
        response = invoker.converse(prompt, model_id=model_id, max_tokens=1000)
        elapsed = time.perf_counter() - started
        parsed = validator.parse_extraction(response["text"])
        output = response["text"]
        results[model_id] = {
            "time_seconds": round(elapsed, 4),
            "output_length": len(output),
            "output_sample": output[:120] + ("..." if len(output) > 120 else ""),
            "validator_accepted": parsed.accepted,
            "validator_flags": parsed.flags,
            "usage": response.get("usage") or {},
        }
    return results
