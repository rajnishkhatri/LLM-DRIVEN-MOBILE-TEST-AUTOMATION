"""Port Protocols — FROZEN. The seams stay in our code (HANDOVER §9, B1):
managed services are adapter *implementations* behind these.

`@runtime_checkable` lets the gate-12 structural test assert both the identity
argument on every method and that concrete adapters satisfy the Protocol.
"""
from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from ..domain.types import (
    ActionReceipt,
    Approval,
    ClassifierResult,
    DocsResult,
    ModelRequest,
    ModelResponse,
    OmniResult,
    RequestContext,
    SourceRef,
    TicketReceipt,
)


@runtime_checkable
class ModelPort(Protocol):
    """Normalizes request/response into typed outcomes (ADR 0002). The
    RequestContext rides inside ModelRequest."""

    def generate(self, request: ModelRequest) -> ModelResponse: ...


@runtime_checkable
class ClassifierPort(Protocol):
    """Stage-1 fallback classifier (ADR 0001). Offline = deterministic;
    live adapter = Agent Squad (referenced, not installed — HANDOVER §9)."""

    def classify(self, ctx: RequestContext, utterance: str) -> ClassifierResult: ...


@runtime_checkable
class OmniPort(Protocol):
    """Governed data query, run AS THE USER and scoped by tenant (ADR 0003)."""

    def query(self, ctx: RequestContext, intent: str) -> OmniResult: ...


@runtime_checkable
class DocsPort(Protocol):
    """How-to retrieval. Returns cited chunks; flags doc-injection."""

    def retrieve(self, ctx: RequestContext, topic: str) -> DocsResult: ...


@runtime_checkable
class TicketPort(Protocol):
    """Get-unstuck write. Idempotent on `idempotency_key` (C9)."""

    def create(
        self, ctx: RequestContext, summary: str, idempotency_key: str
    ) -> TicketReceipt: ...


@runtime_checkable
class ActionPort(Protocol):
    """Phase-2 write path — CONTRACT ONLY in v1 (ADR 0003). Any conforming
    implementation must reject a missing/negative approval before doing
    anything else (unbypassable), even while unimplemented."""

    def execute(
        self, ctx: RequestContext, action: str, approval: Approval
    ) -> ActionReceipt: ...
