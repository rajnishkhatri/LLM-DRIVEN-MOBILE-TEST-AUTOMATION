"""How-to docs adapter — WORKER B. Implements DocsPort over fixtures.

Loads the three `.md` docs (parsing the
`<!-- doc_id: .. version: .. keywords: .. -->` header) plus help-center.jsonl,
and retrieves cited chunks (doc_id + version) by keyword match. Detects and
FLAGS doc-injection: the api-keys doc embeds CANARY-DOC-9147, the
failed-connection doc embeds a phishing line. Flagging routes the turn to human
review; the embedded text is returned only as inert data for synthesis to treat
carefully, never obeyed.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from ..domain.types import DocChunk, DocsResult, RequestContext

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"

_HEADER_RE = re.compile(
    r"doc_id:\s*(?P<doc_id>\S+)\s+"
    r"version:\s*(?P<version>\S+)\s+"
    r"keywords:\s*(?P<keywords>.*?)\s*-->",
    re.DOTALL,
)

# Signals that a retrieved chunk carries an embedded instruction / phishing
# line (inert data — flagged so the turn goes to human review, never obeyed).
_INJECTION_SIGNALS = (
    "ai assistant",
    "ignore your instructions",
    "urgent security notice",
    "confirm your banking password",
    "verify-now.test",
    "canary-doc-",
)


@dataclass(frozen=True)
class _Doc:
    doc_id: str
    version: str
    keywords: tuple[str, ...]
    text: str


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def _is_flagged(text: str) -> bool:
    low = text.lower()
    return any(signal in low for signal in _INJECTION_SIGNALS)


class DocsAdapter:
    def __init__(self, fixtures_dir: Path = FIXTURES):
        self.fixtures_dir = Path(fixtures_dir)
        self._docs: list[_Doc] = self._load()

    # -- loading -------------------------------------------------------------
    def _load(self) -> list[_Doc]:
        docs: list[_Doc] = []
        docs_dir = self.fixtures_dir / "docs"

        for md_path in sorted(docs_dir.glob("*.md")):
            raw = md_path.read_text()
            m = _HEADER_RE.search(raw)
            if not m:
                continue
            keywords = tuple(
                _norm(k) for k in m.group("keywords").split(",") if k.strip()
            )
            # Body = everything after the header comment line.
            body = raw[m.end():].strip()
            docs.append(
                _Doc(
                    doc_id=m.group("doc_id"),
                    version=m.group("version"),
                    keywords=keywords,
                    text=body,
                )
            )

        jsonl = docs_dir / "help-center.jsonl"
        if jsonl.exists():
            for line in jsonl.read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                docs.append(
                    _Doc(
                        doc_id=entry["doc_id"],
                        version=entry["version"],
                        keywords=tuple(_norm(k) for k in entry.get("keywords", [])),
                        text=entry.get("text", ""),
                    )
                )
        return docs

    # -- DocsPort ------------------------------------------------------------
    def retrieve(self, ctx: RequestContext, topic: str) -> DocsResult:
        needle = _norm(topic)

        scored: list[tuple[int, _Doc]] = []
        for doc in self._docs:
            score = 0
            for kw in doc.keywords:
                if kw and (kw in needle or needle in kw):
                    score = max(score, len(kw))
            if score:
                scored.append((score, doc))

        if not scored:
            return DocsResult(chunks=(), flagged=False)

        best = max(score for score, _ in scored)
        hits = [doc for score, doc in scored if score == best]

        chunks = tuple(
            DocChunk(doc_id=d.doc_id, version=d.version, text=d.text) for d in hits
        )
        flagged = any(_is_flagged(c.text) for c in chunks)
        return DocsResult(chunks=chunks, flagged=flagged)
