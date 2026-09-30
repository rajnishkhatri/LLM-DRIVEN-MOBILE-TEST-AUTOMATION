"""Phase-2 ActionPort — WORKER C (stub). CONTRACT ONLY in v1 (ADR 0003).

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
        raise NotImplementedError(
            "worker C: reject missing/negative approval FIRST (ApprovalRequired), "
            "then raise NotImplementedError('phase 2') when approved"
        )
