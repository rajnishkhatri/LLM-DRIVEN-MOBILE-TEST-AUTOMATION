"""Gate 10 (F6, worker B): an injected Omni timeout degrades deterministically —
honest copy, a ticket offer, no invented numbers, and a COMPLETE (degraded)
provenance tuple. The model never writes the degraded copy, so it is
string-assertable (eval-spec §9, TC-08)."""
import pytest

from ari_demo.adapters.omni import OmniAdapter
from ari_demo.domain.types import Route
from ari_demo.resilience.guarded import (
    DEGRADED_COPY,
    GuardTimeout,
    degrade,
    guarded_read,
)


def test_guarded_read_raises_on_injected_timeout(treasurer_ctx):
    adapter = OmniAdapter(force_timeout=True)
    with pytest.raises(GuardTimeout):
        guarded_read(lambda: adapter.query(treasurer_ctx, "cash_position"))


def test_degrade_is_deterministic_with_ticket_offer(treasurer_ctx):
    resp = degrade(Route.DATA, treasurer_ctx)
    assert resp.degraded is True
    assert resp.ticket_offer is True
    assert resp.text == DEGRADED_COPY, "degraded copy must be deterministic"
    assert resp.provenance.is_complete(), "degraded answers still carry provenance"
    # no invented numbers: the deterministic copy must not assert a figure
    assert "$" not in resp.text and "USD" not in resp.text
