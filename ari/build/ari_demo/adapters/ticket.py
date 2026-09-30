"""Jira ticket adapter — WORKER B. Implements TicketPort.

Idempotent on idempotency_key = conversation+turn (C9): a second create with
the same key returns the SAME ticket_id with created=False and does not append.
Backed by the JSON store at store_path
(schema: {next_seq, tickets:[], by_key:{}}).
"""
from __future__ import annotations

import json
from pathlib import Path

from ..domain.types import RequestContext, TicketReceipt

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


class TicketAdapter:
    def __init__(self, store_path: Path = FIXTURES / "jira_store.json"):
        self.store_path = Path(store_path)

    # -- store I/O -----------------------------------------------------------
    def _load(self) -> dict:
        if self.store_path.exists():
            store = json.loads(self.store_path.read_text())
        else:
            store = {}
        store.setdefault("next_seq", 1)
        store.setdefault("tickets", [])
        store.setdefault("by_key", {})
        return store

    def _persist(self, store: dict) -> None:
        self.store_path.write_text(json.dumps(store, indent=2))

    # -- TicketPort ----------------------------------------------------------
    def create(
        self, ctx: RequestContext, summary: str, idempotency_key: str
    ) -> TicketReceipt:
        store = self._load()

        # C9: an existing key is an idempotent replay — same receipt, no append.
        existing = store["by_key"].get(idempotency_key)
        if existing is not None:
            return TicketReceipt(
                ticket_id=existing,
                idempotency_key=idempotency_key,
                created=False,
            )

        # Mint a fresh ticket, keyed by conversation+turn, and persist.
        ticket_id = f"JIRA-{store['next_seq']}"
        store["tickets"].append(
            {
                "ticket_id": ticket_id,
                "idempotency_key": idempotency_key,
                "tenant": ctx.tenant,
                "user": ctx.user,
                "summary": summary,
            }
        )
        store["by_key"][idempotency_key] = ticket_id
        store["next_seq"] += 1
        self._persist(store)

        return TicketReceipt(
            ticket_id=ticket_id,
            idempotency_key=idempotency_key,
            created=True,
        )
