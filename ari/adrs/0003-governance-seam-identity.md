# ADR 0003. One governance seam: propagate the user's identity, never widen it; the phase-2 action gate is designed now, built never (yet)

## Status
Accepted

## Context
Ari is a new path to governed, multi-tenant treasury data. If Ari calls
backends as a privileged service account and filters afterwards, it is a
**confused deputy**: every prompt injection becomes an entitlement-bypass
attempt against application code. The brief defers actions ("phase two, don't
worry about it now"), but retrofitting identity and authorization through
every port later is a rewrite — the last responsible moment for the *seam* is
now, because every port signature carries the context. Cert principles
applied: enforce identity server-side; route human review by stakes, not
volume.

Alternatives: (a) **Service super-user + post-filtering** — confused deputy;
rejected. (b) **Prompt-level enforcement** ("only show the user their own
data") — a wish, not a control; the model never saw the rules; rejected.
(c) **Defer the seam wholesale to phase 2** — rewrite later, and actions
would arrive on an ungoverned base; rejected. (d) **Chosen:** the seam now,
the write path later.

## Decision
- The gateway validates a **signed user token** {user, tenant, role} on every
  request; an immutable **RequestContext** flows through every port — no
  adapter is callable without it (structural test).
- Adapters call backends **as the user** (Omni governed query with the user's
  identity; Jira ticket created as the user). Ari propagates identity; it
  never escalates it.
- **Deterministic entitlement pre-check before any model sees data** — the
  model cannot leak what it never receives. Output screening after synthesis;
  control errors **fail closed**, even when slow.
- **ActionPort — contract only, no implementation:** any future action
  (approve a payment run, submit a forecast) requires a pre-action human
  approval routed by stakes, an idempotency key, and an audit event. The
  conformance test pins approval-required as unbypassable even though the
  port is unimplemented in v1.
- The decision log records the provenance tuple including **entitlement
  scope**; CloudTrail is the infra/identity audit plane beneath it.

## Consequences
Good: the blast radius of any prompt trick is exactly what the asker could
already see; phase-2 lands as an adapter + an approval flow with zero core
surgery; every stream plugged into the platform inherits audit-readiness.
Bad: context-plumbing tax on every call; cross-tenant probes are a standing,
build-failing eval class forever; the gate costs latency (budgeted; fail
closed even when slow).

## Compliance
Cross-tenant probe evals = 0 violations (build-failing); structural
no-context-no-call test; provenance-tuple completeness = 100% of answers;
ActionPort conformance test (approval cannot be bypassed); decision-log +
CloudTrail planes wired per the observability design.

## Amendment — v2 confirm-before-write + adapter default-deny (2026-10-03)
Extends the Decision for the v2 enhancement
([ari-v2-breakdown.md](../../cases/ripple/ari-v2-breakdown.md)); the ADR
stays Accepted. The decision is made now; the v2 build is its implementation.

- **The ticket write gets the stakes rule the action port already has.** A
  ticket route returns a **draft**; `TicketPort.create` runs only on a human
  **confirm** on a later turn. A cancel drops the draft and does not call the
  port; an unrelated turn leaves the draft pending. This applies this ADR's
  "human review routed by stakes" to the one write v1 actually performs,
  closing the v1 behavior where a misroute or a frustrated utterance wrote a
  Jira row on the same turn. The idempotency key is the draft's
  `(conversation, draft id)`, fixed at creation (see ADR 0001 amendment); a
  confirm must match the draft id it confirms, so a second ticket-shaped turn
  cannot commit the wrong draft.
- **Adapter entitlement defaults to deny.** The deterministic pre-check still
  runs before the model, but it cannot see a query that names no tenant, so
  the confused-deputy control also lives in the adapter, scoped by the token
  (the rejected "service super-user + post-filter" alternative, refused one
  layer down). A docs chunk is returned only when the token is entitled to
  it: a chunk stamped for a tenant goes only to that tenant; a chunk is
  treated as the shared help center only when it is **explicitly** marked
  shared; a chunk with neither marker is **withheld**. The fail-open default
  (unstamped = visible to all) is rejected — the realistic error is
  forgetting to stamp a tenant doc, and a fail-open default would leak it to
  every tenant. Omni's existing per-tenant file selection is the same control
  one layer over. Prompt-level enforcement stays rejected.

Identity propagation, fail-closed control errors, and "ActionPort is a
contract, unimplemented" stay exactly as written.

**Compliance delta.** Add: Gate 8 — exactly one ticket, on the confirm turn,
with cancel calling no port and a duplicate confirm replaying to one id; Gate
6 extended — an un-annotated docs chunk is withheld cross-tenant
(build-failing) and a fixture-lint flags any un-annotated chunk; the adapter
entitlement assertion calls the adapter, not only `precheck`.

## Notes
Author: session pipeline (sdd-brainstorm → arch-characteristics → arch-decide)
Approved by / date: Rajnish Khatri / 2026-09-30
Last modified: 2026-10-03 / v2 amendment (confirm-before-write + adapter default-deny)
