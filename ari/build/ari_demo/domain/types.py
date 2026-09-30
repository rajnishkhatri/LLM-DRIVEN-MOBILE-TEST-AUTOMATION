"""Shared vocabulary as types — FROZEN (HANDOVER §3, §5, §8).

Workers may read these; they must not edit this file. A worker that needs a
contract change reports it in its summary; the integrator applies it in wave 2.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Sequence


# --------------------------------------------------------------------------
# Enums (HANDOVER §3)
# --------------------------------------------------------------------------
class Route(str, Enum):
    """A stage-0 hit, or a recognized non-adapter route. Never a guess."""
    DATA = "DATA"
    HOWTO = "HOWTO"
    TICKET = "TICKET"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    ACTION_P2 = "ACTION_P2"


# A routing decision selects a capability; "Capability" reads better in the
# rule table (HANDOVER §8) but is the same closed set as Route.
Capability = Route


class ModelOutcome(str, Enum):
    """Typed model outcomes (ADR 0002). No caller sees a raw provider response."""
    OK = "ok"
    THROTTLED = "throttled"
    TIMED_OUT = "timed-out"
    INVALID = "invalid"
    GUARDRAIL_INTERVENED = "guardrail-intervened"


class Tier(str, Enum):
    """Rule tier for stage-0 (HANDOVER §8): a single Tier.A hit wins outright."""
    A = "A"
    B = "B"


# --------------------------------------------------------------------------
# Exceptions (fail closed — ADR 0003)
# --------------------------------------------------------------------------
class IdentityError(Exception):
    """Raised by the identity gate on a missing/invalid/tampered token."""


class EntitlementRefused(Exception):
    """Raised when the pre-model entitlement check refuses a request."""


class ApprovalRequired(Exception):
    """Raised by any ActionPort when approval is absent — unbypassable."""


# --------------------------------------------------------------------------
# Identity (ADR 0003) — stamped at the gate, immutable, carried everywhere.
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class RequestContext:
    """{user, tenant, role} from a signed token + conversation coordinates.

    No port is callable without one (structural test, gate 12).
    """
    user: str
    tenant: str
    role: str
    conversation_id: str = "conv-0"
    turn_id: str = "t0"

    @property
    def idempotency_key(self) -> str:
        """C9 ticket-write key = conversation_id + turn_id."""
        return f"{self.conversation_id}:{self.turn_id}"


# --------------------------------------------------------------------------
# Routing (ADR 0001, HANDOVER §8)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Rule:
    id: str
    capability: Capability
    tier: Tier
    pattern: re.Pattern
    weight: float


@dataclass(frozen=True)
class RouteDecision:
    """A confident route. `fired` rule ids are part of provenance."""
    route: Route
    score: float
    margin: float
    fired: tuple[str, ...] = ()


@dataclass(frozen=True)
class FallThrough:
    """Not confident enough to route. Never a guess (ADR 0001)."""
    reason: str  # "no_signal" | "weak_signal" | "ambiguous"
    fired: tuple[str, ...] = ()


@dataclass(frozen=True)
class ClassifierResult:
    """Stage-1 classifier outcome. Below the floor -> clarify or ticket."""
    route: Optional[Route]
    confidence: float
    clarify: bool = False


# --------------------------------------------------------------------------
# Provenance (ADR 0003, characteristic #3) — the audit record IS the truth.
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class SourceRef:
    """A cited source with its version id (provenance pointing at mutable
    sources is theater — record the version)."""
    system: str   # "omni" | "docs" | "jira"
    doc_id: str
    version: str


@dataclass(frozen=True)
class Provenance:
    """(route · sources+versions · confidence · model+prompt version ·
    entitlement scope). Complete on 100% of answers, incl. degraded ones."""
    route: Route
    sources: tuple[SourceRef, ...]
    confidence: float
    model_version: str
    prompt_version: str
    entitlement_scope: str
    rule_ids: tuple[str, ...] = ()

    def is_complete(self) -> bool:
        """Structural completeness of the tuple (gate 11).

        Every scalar component must be present; `sources` may legitimately be
        empty (a refusal cites nothing). Citation *presence* on how-to answers
        is a separate assertion (gate 4).
        """
        return (
            isinstance(self.route, Route)
            and isinstance(self.confidence, (int, float))
            and bool(self.model_version)
            and bool(self.prompt_version)
            and bool(self.entitlement_scope)
            and isinstance(self.sources, tuple)
        )


# --------------------------------------------------------------------------
# Adapter result records (HANDOVER §5.2, ports are typed around these)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class OmniRow:
    tenant: str
    metric: str
    value: str
    memo: str = ""
    version: str = "v1"


@dataclass(frozen=True)
class OmniResult:
    rows: tuple[OmniRow, ...]
    source: SourceRef


@dataclass(frozen=True)
class DocChunk:
    doc_id: str
    version: str
    text: str


@dataclass(frozen=True)
class DocsResult:
    chunks: tuple[DocChunk, ...]
    flagged: bool = False  # doc-injection detected in a retrieved chunk


@dataclass(frozen=True)
class TicketReceipt:
    ticket_id: str
    idempotency_key: str
    created: bool  # True = newly created; False = idempotent replay


@dataclass(frozen=True)
class Approval:
    approved_by: str
    approved: bool


@dataclass(frozen=True)
class ActionReceipt:
    action: str
    performed: bool


# --------------------------------------------------------------------------
# Model seam (ADR 0002)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class ModelRequest:
    prompt: str
    context: RequestContext
    prompt_version: str = "synthesis-v1"
    temperature: float = 0.0


@dataclass(frozen=True)
class ModelResponse:
    outcome: ModelOutcome
    text: str
    model_version: str
    prompt_version: str


# --------------------------------------------------------------------------
# The thing the pipeline returns
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class AriResponse:
    text: str
    provenance: Provenance
    route: Route
    degraded: bool = False
    ticket_offer: bool = False
    clarify: bool = False
    refused: bool = False
    audit_event: Optional[str] = None
    ticket_id: Optional[str] = None
