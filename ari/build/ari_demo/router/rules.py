"""Stage-0 rule table — WORKER A (stub).

Populate RULES so the fast path decides the golden set at >= 99% precision
(gate 1) while leaving genuinely ambiguous rows to fall through (gate 3).
Rule ids are part of provenance. Watch the traps (Q-013/014/015): surface
vocabulary of one capability, meaning of another.
"""
from __future__ import annotations

from ..domain.types import Rule

# Worker A fills this. Empty until then.
RULES: tuple[Rule, ...] = ()
