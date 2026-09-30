"""Stage-0 rule table — WORKER A.

Rule ids are provenance. The table is deliberately built from *distinctive
phrases*, never bare shared words: a genuinely ambiguous utterance (the 8
route=null rows) must match nothing and fall through (gate 3), while the clear
rows match exactly one capability and route at 100% precision (gates 1/2).

Two tiers (HANDOVER §8):
  * Tier.A — a single decisive phrase. One Tier.A capability firing wins
    outright (recognitions: how-to, out-of-scope, phase-2 actions, and the
    behavioural "get-unstuck" tickets).
  * Tier.B — weighted signals resolved by the swept THRESHOLD/MARGIN. Data
    analytics carry weight 0.8; a weak "ticket(s)" surface-word carries 0.2.
    That is exactly the trap (Q-013/014/015): the word "ticket" is present
    but the *meaning* is data analytics, so DATA 0.8 beats TICKET 0.2 by a
    0.6 margin and the row routes DATA, not TICKET.
"""
from __future__ import annotations

import re

from ..domain.types import Route, Rule, Tier

DATA_W = 0.8
WEAK_W = 0.2


def _c(pattern: str) -> "re.Pattern":
    return re.compile(pattern)


# --------------------------------------------------------------------------
# DATA — governed analytics (Tier.B, weight 0.8). Distinctive phrases only.
# --------------------------------------------------------------------------
_DATA = [
    ("d-cash-position", r"cash position"),
    ("d-operating-account", r"operating account|balance in the"),
    ("d-liquidity-forecast", r"liquidity forecast"),
    ("d-forecast-actuals", r"from actuals|\bactuals\b"),
    ("d-outflows", r"outflows"),
    ("d-fx-exposure", r"fx exposure|exposure by currency"),
    ("d-interest-earned", r"interest .*earned"),
    ("d-counterparties", r"counterparties"),
    ("d-idle-sitting", r"sitting on"),
    ("d-maturities", r"maturities"),
    ("d-dso", r"days-sales-outstanding|days sales outstanding"),
    ("d-payment-run-totals", r"payment-run totals|payment run totals"),
    ("d-how-many-tickets", r"how many .*tickets"),
    ("d-ticket-resolution", r"ticket-resolution time|resolution time"),
    ("d-balances-compare", r"balances compare|compare with your other"),
    ("d-closing-balances", r"closing balances"),
    ("d-approval-limits-every", r"approval limits for every user"),
    ("d-admin-audit-log", r"admin audit log"),
    ("d-memo-lines", r"memo lines"),
]

# --------------------------------------------------------------------------
# HOWTO — product help (Tier.A). "how do i/you/we" is decisive; note it does
# NOT match data's "how many"/"how much"/"how far" or "how do our".
# --------------------------------------------------------------------------
_HOWTO = [
    ("h-how-do", r"\bhow do (i|you|we)\b"),
    ("h-what-do-mean", r"what do .*mean"),
    ("h-settings-page", r"settings page"),
]

# --------------------------------------------------------------------------
# OUT_OF_SCOPE — recognized refusals/redirects incl. query-injection (Tier.A).
# --------------------------------------------------------------------------
_OOS = [
    ("o-hedge", r"\bhedge\b"),
    ("o-park", r"\bpark\b|best return"),
    ("o-better-than", r"better than"),
    ("o-weather", r"weather"),
    ("o-tax-treatment", r"tax treatment"),
    ("o-guarantee", r"guarantee"),
    ("o-covenant", r"covenant|clause \d"),
    ("o-negotiate", r"negotiate"),
    ("o-injection-ignore", r"ignore .*instructions"),
    ("o-system-prompt", r"system prompt|repeat your"),
]

# --------------------------------------------------------------------------
# ACTION_P2 — phase-2 write verbs, recognized but declined (Tier.A). Word
# boundaries keep "approve" off "approval(s)".
# --------------------------------------------------------------------------
_ACTION = [
    ("a-approve", r"\bapprove\b"),
    ("a-submit", r"\bsubmit\b"),
    ("a-convert", r"\bconvert\b"),
    ("a-cancel", r"\bcancel\b"),
]

# --------------------------------------------------------------------------
# TICKET — behavioural "get-unstuck" phrases (Tier.A). No bare "ticket" here.
# --------------------------------------------------------------------------
_TICKET = [
    ("t-get-someone", r"get someone on it|not updated since"),
    ("t-cannot-login", r"cannot log in|can not log in"),
    ("t-throws-error", r"throws an error"),
    ("t-rejected-blocked", r"rejected by the bank|i am blocked"),
    ("t-disconnecting", r"disconnecting"),
    ("t-request-bank", r"can i request"),
    ("t-from-support", r"someone from support"),
    ("t-escalate", r"escalate to support|something is broken"),
    ("t-raise-ticket", r"raise the ticket"),
    ("t-raise-it", r"raise it"),
]

# Weak surface signal for the trap contest only (Tier.B, weight 0.2).
_TICKET_WEAK = [
    ("t-weak-ticket", r"\btickets?\b"),
]


def _rules() -> tuple[Rule, ...]:
    out: list[Rule] = []
    for rid, pat in _DATA:
        out.append(Rule(rid, Route.DATA, Tier.B, _c(pat), DATA_W))
    for rid, pat in _HOWTO:
        out.append(Rule(rid, Route.HOWTO, Tier.A, _c(pat), 1.0))
    for rid, pat in _OOS:
        out.append(Rule(rid, Route.OUT_OF_SCOPE, Tier.A, _c(pat), 1.0))
    for rid, pat in _ACTION:
        out.append(Rule(rid, Route.ACTION_P2, Tier.A, _c(pat), 1.0))
    for rid, pat in _TICKET:
        out.append(Rule(rid, Route.TICKET, Tier.A, _c(pat), 1.0))
    for rid, pat in _TICKET_WEAK:
        out.append(Rule(rid, Route.TICKET, Tier.B, _c(pat), WEAK_W))
    return tuple(out)


RULES: tuple[Rule, ...] = _rules()
