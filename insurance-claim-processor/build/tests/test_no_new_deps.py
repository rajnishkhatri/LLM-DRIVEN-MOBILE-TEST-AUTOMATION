"""R-16 — the resilience increment adds NO new pip dependency (AC-R1).

AppConfig Data ships in botocore; EMF is structured logging; alarms/SNS are
[infra]. So every claim_processor import must be stdlib, botocore, or internal.
"""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PKG = ROOT / "claim_processor"
REQUIREMENTS = ROOT / "requirements.txt"

_STDLIB = {
    "__future__", "argparse", "ast", "collections", "copy", "dataclasses",
    "datetime", "enum", "hashlib", "json", "logging", "os", "pathlib", "re",
    "sys", "time", "typing", "io", "functools", "itertools",
}
_ALLOWED_THIRD_PARTY = {"botocore", "boto3"}
_ALLOWED = _STDLIB | _ALLOWED_THIRD_PARTY | {"claim_processor"}


def _import_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                roots.add(node.module.split(".")[0])
    return roots


class NoNewDepsTests(unittest.TestCase):
    def test_requirements_only_boto3_botocore(self) -> None:
        lines = [
            l.strip().split(">=")[0].split("==")[0].lower()
            for l in REQUIREMENTS.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.strip().startswith("#")
        ]
        self.assertEqual(set(lines), {"boto3", "botocore"})

    def test_modules_import_only_allowed_roots(self) -> None:
        for path in sorted(PKG.glob("*.py")):
            roots = _import_roots(path)
            unexpected = roots - _ALLOWED
            self.assertEqual(
                unexpected, set(), f"{path.name} imports non-allowed roots: {sorted(unexpected)}"
            )

    def test_no_moto_or_pillow_or_emf_lib(self) -> None:
        for path in PKG.glob("*.py"):
            roots = _import_roots(path)
            for banned in ("moto", "PIL", "aws_embedded_metrics", "openai", "anthropic", "requests"):
                self.assertNotIn(banned, roots, f"{path.name} imports {banned}")


if __name__ == "__main__":
    unittest.main()
