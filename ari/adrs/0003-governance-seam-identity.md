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

## Notes
Author: session pipeline (sdd-brainstorm → arch-characteristics → arch-decide)
Approved by / date: Rajnish Khatri / 2026-09-30
Last modified: 2026-09-29 / new
