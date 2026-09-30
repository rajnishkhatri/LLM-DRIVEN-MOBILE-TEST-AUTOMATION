"""Gate 8 (F5, worker B): duplicate-injection on the ticket write — a retry or
double-click yields exactly one ticket; the duplicate returns the same receipt.
Idempotency key = conversation + turn (C9) (eval-spec §9, TC-09)."""
import json

from ari_demo.adapters.ticket import TicketAdapter


def test_duplicate_submit_creates_exactly_one_ticket(treasurer_ctx, tmp_jira):
    adapter = TicketAdapter(store_path=tmp_jira)
    key = treasurer_ctx.idempotency_key
    summary = "Barclays feed has not updated since Tuesday"

    first = adapter.create(treasurer_ctx, summary, key)
    second = adapter.create(treasurer_ctx, summary, key)  # retry / double-click

    assert first.ticket_id == second.ticket_id, "duplicate must reuse the ticket"
    assert first.created is True, "first write creates"
    assert second.created is False, "second write is an idempotent replay"

    store = json.loads(tmp_jira.read_text())
    assert len(store["tickets"]) == 1, "exactly one ticket must exist"


def test_distinct_turns_create_distinct_tickets(treasurer_ctx, tmp_jira):
    from dataclasses import replace

    adapter = TicketAdapter(store_path=tmp_jira)
    r1 = adapter.create(treasurer_ctx, "issue one", "conv-demo:t1")
    ctx2 = replace(treasurer_ctx, turn_id="t2")
    r2 = adapter.create(ctx2, "issue two", ctx2.idempotency_key)
    assert r1.ticket_id != r2.ticket_id
    store = json.loads(tmp_jira.read_text())
    assert len(store["tickets"]) == 2
