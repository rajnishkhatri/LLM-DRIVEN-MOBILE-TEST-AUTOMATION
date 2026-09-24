from __future__ import annotations

import sys
import unittest
from pathlib import Path
from string import Formatter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.prompts import PromptTemplateManager


class PromptTests(unittest.TestCase):
    def test_unknown_template(self) -> None:
        with self.assertRaises(ValueError):
            PromptTemplateManager().get_prompt("nope")

    def test_extract_template_fills(self) -> None:
        text = PromptTemplateManager().get_prompt("extract_info", document_text="HELLO")
        self.assertIn("HELLO", text)


class ContentBlockTests(unittest.TestCase):
    """F14 / AC-A5a — claim-derived fields render as `guardContent`."""

    def test_extract_tags_the_document_and_keeps_the_instructions_plain(self) -> None:
        blocks = PromptTemplateManager().get_content_blocks("extract_info", document_text="CLAIM TEXT")
        self.assertEqual([next(iter(b)) for b in blocks], ["text", "guardContent"])
        self.assertTrue(blocks[0]["text"].startswith("Extract the following fields"))
        self.assertEqual(blocks[1], {"guardContent": {"text": {"text": "CLAIM TEXT"}}})

    def test_trusted_fields_stay_in_the_surrounding_text(self) -> None:
        blocks = PromptTemplateManager().get_content_blocks(
            "generate_summary", extracted_info="{}", policy_context="POLICY EXCERPT"
        )
        self.assertEqual([next(iter(b)) for b in blocks], ["text", "guardContent", "text"])
        self.assertIn("POLICY EXCERPT", blocks[2]["text"])

    def test_blocks_read_exactly_like_the_prompt(self) -> None:
        mgr = PromptTemplateManager()
        values = {"document_text": "D", "extracted_info": "{}", "policy_context": "P"}
        for name, template in mgr.templates.items():
            fields = {f: values[f] for _, f, _, _ in Formatter().parse(template) if f}
            joined = "".join(
                b["text"] if "text" in b else b["guardContent"]["text"]["text"]
                for b in mgr.get_content_blocks(name, **fields)
            )
            self.assertEqual(joined.strip(), mgr.get_prompt(name, **fields).strip())

    def test_blank_segments_are_dropped(self) -> None:
        # Converse rejects blank text blocks. A blank document leaves no
        # guarded block, so the guardrail evaluates the whole turn.
        blocks = PromptTemplateManager().get_content_blocks("extract_info", document_text="  \n")
        self.assertEqual([next(iter(b)) for b in blocks], ["text"])

    def test_every_template_declares_its_claim_derived_fields(self) -> None:
        mgr = PromptTemplateManager()
        for name, template in mgr.templates.items():
            fields = {f for _, f, _, _ in Formatter().parse(template) if f}
            self.assertIn(name, mgr.untrusted_fields, f"{name}: classify its fields")
            self.assertLessEqual(mgr.untrusted_fields[name], fields)

    def test_custom_templates_are_not_tagged_by_default(self) -> None:
        mgr = PromptTemplateManager({"t": "Say {x}."})
        self.assertEqual(mgr.get_content_blocks("t", x="hi"), [{"text": "Say hi."}])


if __name__ == "__main__":
    unittest.main()
