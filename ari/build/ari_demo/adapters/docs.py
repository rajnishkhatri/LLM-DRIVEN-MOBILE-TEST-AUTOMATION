"""How-to docs adapter — WORKER B (stub). Implements DocsPort over fixtures.

Return cited chunks (doc_id + version). Detect and FLAG doc-injection: the
API-keys doc embeds CANARY-DOC-9147; the failed-connection doc embeds a
phishing line. Flagging routes the turn to human review; the embedded text is
returned only as inert data for synthesis to treat carefully, never obeyed.
"""
from __future__ import annotations

from pathlib import Path

from ..domain.types import DocsResult, RequestContext

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


class DocsAdapter:
    def __init__(self, fixtures_dir: Path = FIXTURES):
        self.fixtures_dir = Path(fixtures_dir)

    def retrieve(self, ctx: RequestContext, topic: str) -> DocsResult:
        raise NotImplementedError("worker B: doc retrieval + injection flagging")
