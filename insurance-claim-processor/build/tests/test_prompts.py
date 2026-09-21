from __future__ import annotations

import sys
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
