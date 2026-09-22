from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol, runtime_checkable

from claim_processor.models import PolicyChunk

_TOKEN = re.compile(r"[a-z0-9]+")
_META = {
    "auto-florida": ("florida", "personal_auto"),
    "homeowners-texas": ("texas", "homeowners"),
}


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN.findall(text.lower()) if len(t) > 2}


@runtime_checkable
class RetrieverProtocol(Protocol):
    def retrieve(
        self,
        query: str,
        top_k: int = 2,
        *,
        jurisdiction: str | None = None,
        line_of_business: str | None = None,
    ) -> list[PolicyChunk]: ...


class PolicyRetriever:
    """In-process keyword RAG — Retrieve Policy Context component.

    Production promotes this to bedrock-agent-runtime.retrieve + metadata
    filters. Keyword overlap keeps the PoC offline (no embeddings API).
    """

    def __init__(self, policy_dir: Path):
        self.chunks: list[PolicyChunk] = []
        for path in sorted(policy_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            jurisdiction, line = _META.get(path.stem, ("", ""))
            self.chunks.append(
                PolicyChunk(
                    chunk_id=path.stem,
                    source=path.name,
                    text=text,
                    score=0.0,
                    jurisdiction=jurisdiction,
                    line_of_business=line,
                )
            )

    def retrieve(
        self,
        query: str,
        top_k: int = 2,
        *,
        jurisdiction: str | None = None,
        line_of_business: str | None = None,
    ) -> list[PolicyChunk]:
        q = _tokens(query)
        if not q:
            return []
        scored: list[PolicyChunk] = []
        for chunk in self.chunks:
            if jurisdiction and chunk.jurisdiction != jurisdiction:
                continue
            if line_of_business and chunk.line_of_business != line_of_business:
                continue
            overlap = len(q & _tokens(chunk.text))
            if overlap <= 0:
                continue
            scored.append(
                PolicyChunk(
                    chunk_id=chunk.chunk_id,
                    source=chunk.source,
                    text=chunk.text,
                    score=float(overlap),
                    jurisdiction=chunk.jurisdiction,
                    line_of_business=chunk.line_of_business,
                )
            )
        scored.sort(key=lambda c: c.score, reverse=True)
        return scored[:top_k]


def infer_scope(extracted: dict | None, document_text: str) -> tuple[str | None, str | None]:
    """Fail closed: unknown jurisdiction ⇒ no retrieve (C11 ungrounded)."""
    blob = " ".join(
        [
            document_text,
            json_blob(extracted),
        ]
    ).lower()
    jurisdiction = None
    line = None
    if "florida" in blob or "pol-fl" in blob or "miami" in blob:
        jurisdiction = "florida"
    elif "texas" in blob or "ho-tx" in blob or "austin" in blob:
        jurisdiction = "texas"
    if "auto" in blob or "collision" in blob or "civic" in blob or "windshield" in blob:
        line = "personal_auto"
    elif "home" in blob or "cabinet" in blob or "plumbing" in blob or "supply line" in blob:
        line = "homeowners"
    return jurisdiction, line


def json_blob(extracted: dict | None) -> str:
    if not extracted:
        return ""
    return " ".join(str(v) for v in extracted.values() if v is not None)
