"""Phase-2 ActionPort — WORKER C. CONTRACT ONLY in v1 (ADR 0003).

The port is unimplemented, but approval-required must be UNBYPASSABLE: any call
with a missing or negative approval raises ApprovalRequired *before* anything
else happens. With approval present, v1 still refuses — it is not built — but
the ordering proves the gate cannot be skipped (gate 9).
"""
from __future__ import annotations

from ..domain.types import ActionReceipt, Approval, ApprovalRequired, RequestContext


class PhaseTwoActionPort:
    def execute(
        self, ctx: RequestContext, action: str, approval: Approval
    ) -> ActionReceipt:
        # UNBYPASSABLE approval check FIRST — before any action logic, so the
        # gate can never be skipped (ADR 0003, gate 9). A missing or negative
        # approval fails closed.
        if approval is None or not getattr(approval, "approved", False):
            raise ApprovalRequired(
                f"action {action!r} requires an explicit approval; "
                "none was granted"
            )
        # Approval present and positive: recognized, but the write path is not
        # built in v1 (phase 2). The refusal here is deliberate, not a gap.
        raise NotImplementedError("phase 2 - not built in v1")
