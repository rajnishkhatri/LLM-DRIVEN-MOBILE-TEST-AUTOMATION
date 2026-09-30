"""Gate 9 (F5, worker C): ActionPort conformance — approval is unbypassable even
though the port is unimplemented in v1 (ADR 0003 / eval-spec §9)."""
import pytest

from ari_demo.domain.types import Approval, ApprovalRequired
from ari_demo.ports.ports import ActionPort
from ari_demo.synthesis.action import PhaseTwoActionPort


def test_reference_port_satisfies_protocol():
    assert isinstance(PhaseTwoActionPort(), ActionPort)


def test_missing_or_negative_approval_is_rejected_first(treasurer_ctx):
    port = PhaseTwoActionPort()
    with pytest.raises(ApprovalRequired):
        port.execute(treasurer_ctx, "approve-payment-run", Approval("nobody", False))


def test_approved_action_is_recognized_but_unbuilt(treasurer_ctx):
    port = PhaseTwoActionPort()
    # approval present -> not rejected; v1 simply has not built the write path
    with pytest.raises(NotImplementedError):
        port.execute(treasurer_ctx, "approve-payment-run", Approval("cfo", True))
