from __future__ import annotations

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


class PromptTemplateManager:
    """Named, versioned templates — Skill 1.1.3 / Render Prompt component."""

    def __init__(self, templates: dict[str, str] | None = None, version: str = TEMPLATE_VERSION):
        self.templates = dict(templates or _TEMPLATES)
        self.version = version

    def get_prompt(self, template_name: str, **kwargs: str) -> str:
        template = self.templates.get(template_name)
        if template is None:
            raise ValueError(f"Template {template_name} not found")
        return template.format(**kwargs)

    def versions(self) -> dict[str, str]:
        return {name: self.version for name in self.templates}
