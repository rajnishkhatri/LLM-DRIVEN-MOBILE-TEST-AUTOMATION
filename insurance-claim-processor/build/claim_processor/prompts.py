from __future__ import annotations

from string import Formatter

TEMPLATE_VERSION = "1"

_TEMPLATES = {
    "extract_info": """Extract the following fields from this insurance claim document.
Return ONLY valid JSON with keys:
claimant_name, policy_number, incident_date, claim_amount, incident_description.
Use null for missing values. claim_amount must be a number without currency symbols.

Document:
{document_text}
""",
    "generate_summary": """Write a concise adjuster-facing summary of this claim.
Use ONLY the extracted fields and the policy excerpts. If the excerpts do not
support a coverage conclusion, say so explicitly and do not invent one.

Extracted fields (JSON):
{extracted_info}

Policy excerpts:
{policy_context}
""",
}

# Fields that carry claim-derived (claimant-controlled) text. With a guardrail,
# only these travel as Converse `guardContent`, so the guardrail evaluates the
# claim, not our instructions or policy excerpts (F14 / AC-A5a). Every
# template declares its set, even when empty.
_UNTRUSTED_FIELDS = {
    "extract_info": frozenset({"document_text"}),
    "generate_summary": frozenset({"extracted_info"}),
}


class PromptTemplateManager:
    """Named, versioned templates — Skill 1.1.3 / Render Prompt component."""

    def __init__(
        self,
        templates: dict[str, str] | None = None,
        version: str = TEMPLATE_VERSION,
        untrusted_fields: dict[str, frozenset[str]] | None = None,
    ):
        self.templates = dict(templates or _TEMPLATES)
        self.version = version
        if untrusted_fields is None:
            untrusted_fields = {} if templates else _UNTRUSTED_FIELDS
        self.untrusted_fields = dict(untrusted_fields)

    def get_prompt(self, template_name: str, **kwargs: str) -> str:
        return self._template(template_name).format(**kwargs)

    def get_content_blocks(self, template_name: str, **kwargs: str) -> list[dict]:
        """The rendered prompt as Converse content blocks, claim-derived fields
        tagged as `guardContent`. Joined, the blocks read like `get_prompt`;
        blank segments are dropped (Converse rejects blank text blocks)."""
        untrusted = self.untrusted_fields.get(template_name, frozenset())
        formatter = Formatter()
        blocks: list[dict] = []
        text = ""
        for literal, field, spec, conversion in formatter.parse(self._template(template_name)):
            text += literal
            if field is None:
                continue
            value, _ = formatter.get_field(field, (), kwargs)
            rendered = formatter.format_field(formatter.convert_field(value, conversion), spec or "")
            if field not in untrusted:
                text += rendered
                continue
            _append_text(blocks, text)
            text = ""
            if rendered.strip():
                blocks.append({"guardContent": {"text": {"text": rendered}}})
        _append_text(blocks, text)
        return blocks

    def _template(self, template_name: str) -> str:
        template = self.templates.get(template_name)
        if template is None:
            raise ValueError(f"Template {template_name} not found")
        return template

    def versions(self) -> dict[str, str]:
        return {name: self.version for name in self.templates}


def _append_text(blocks: list[dict], text: str) -> None:
    if text.strip():
        blocks.append({"text": text})
