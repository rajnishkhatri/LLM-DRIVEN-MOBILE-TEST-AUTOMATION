"""Jira ticket adapter — WORKER B (stub). Implements TicketPort.

Idempotent on idempotency_key = conversation+turn (C9): a second create with
the same key returns the SAME ticket_id with created=False. Backed by an
in-memory/file store seeded from fixtures/jira_store.json.
"""
from __future__ import annotations

from pathlib import Path

from ..domain.types import RequestContext, TicketReceipt

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


class TicketAdapter:
    def __init__(self, store_path: Path = FIXTURES / "jira_store.json"):
        self.store_path = Path(store_path)

    def create(
        self, ctx: RequestContext, summary: str, idempotency_key: str
    ) -> TicketReceipt:
        raise NotImplementedError("worker B: idempotent ticket write (C9)")
