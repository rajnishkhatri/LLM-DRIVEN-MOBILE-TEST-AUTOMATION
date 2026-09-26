---
type: architecture
title: 'ADR 1. Stand up the sdp-* tactical-patterns skill family as a new skill-sync node'
description: 'A new independent skill family (router sdp-lifecycle + category sdp-resilience) teaches the tactical system-design loop via self-contained, stably-addressed pattern cards; registered as a new skill-sync manifest node, projected Cursor→Claude.'
tags: [architecture, adr]
---

# ADR 1. Stand up the sdp-* tactical-patterns skill family as a new skill-sync node

## Status

Accepted
<!-- Proposed and Accepted at the plan gate 2026-09-13 (owner ratified plan+ADR;
PLAN-OK). Accepted ahead of the originally-stated implement/converge gate, at the
owner's call. NOTE: the T2b topology bet's killing-test — the V1 trigger eval
(AC-8, Compliance) — has NOT yet run; it executes during implement. A red result
routes to a superseding ADR at skill #2 per the normal status flow, not to
reopening this acceptance. First ADR of a new tooling/sdp/ seam. Governs
docs/sdd/specs/sdp-resilience.spec.md. -->

## Context

`arch-*` brings disciplined reasoning to architecture characteristics, components,
style, decisions, risk, and validation — but there is **no skill for tactical,
intra-service system-design patterns** (circuit breakers, retry budgets,
timeouts/deadlines, bulkheads, idempotency, load shedding, graceful degradation).
The gap is verified: `arch-*` bodies contain no `circuit|bulkhead|saga|outbox|
idempoten|rate limit` hits (Hs3). The knowledge exists as 47 canonical Concepts in
the `cases/SystemDesignPatterns/` bundle, but it is **not skill-addressable and not
self-contained** — a consumer cannot cite a pattern's trade-off surface as a unit,
and the latent demand is already visible (`arch-risk/SKILL.md:62` improvises
"backpressure queue → priority channel" mitigations with no card to cite).

The Stage-1 gate (closed 2026-09-13) fixed the direction; the alternatives it
weighed are recorded here, not re-litigated:

- **W1 — agents just read the bundle Concepts** (no skill). Rejected: a line-cited
  Concept is a fragile join, carries no stable addressable id (§13 consumer
  invariant), and gives an agent no diagnose→select→apply→verify loop.
- **W2 — patch `arch-*`** to hold the patterns. Rejected (C3): `arch-*` owns
  style/decision discipline, not intra-service mechanics; folding them in blurs a
  clean boundary that is already mutual (`arch-style` disclaims "intra-service
  design patterns", `arch-style/SKILL.md:11-13`).
- **Topology T2a (catalog groups A/B/C/D)** vs **T2b (agent-job categories:
  resilience/messaging/data/traffic/coordination)** vs the review's **T2-defer**.
  The owner chose **T2b, commit now** — a bet that clinic symptoms cluster inside
  one job bucket. That bet is **PLAUSIBLE, not validated** (Ht2b).

## Decision

We will **stand up a new independent `sdp-*` skill family** — wave 1 = router
**`sdp-lifecycle`** + category skill **`sdp-resilience`** — that teaches the
tactical loop over **self-contained, stably-addressed pattern cards** (P1,
hand-distilled on one frozen template), and **register it as a new `skill_sync`
manifest node** (`id = "sdp"`, `source = ".cursor/skills"`, projected to
`.claude/skills`), the same source→projection model as the `arch`/`aws-ai`
families and their generated-projection discipline (ADR sdd-roles/0003).

Justification:

- **Technical.** Fills the verified mechanics gap with a clinic an agent can run in
  isolation; the card layer gives every consumer (arch-risk first) a citable unit
  with a stable id (§13); the manifest node puts the family under the existing
  byte-diff drift guard for free (no new gate).
- **Strategic / independence.** C3 independent-first: the family ships without
  coupling to `arch-*` (J1 — seams reserved, none built). The addressable card is
  the durable substrate later joins project from, so topology (which skill holds a
  card) stays nearly invisible to consumers and the design weight sits on the card
  contract, not the grouping.

The **new abstraction** (G1) is the family + its manifest node + the frozen card
template. What it buys and the simpler thing rejected are stated above (W1/W2).

## Consequences

- **Good.** Under the drift guard from day one; independent of `arch-*`;
  consumer-addressable cards; one template proven on seven real cards before any P2
  generator is attempted; a clean, mutual boundary with `arch-style`.
- **Cost / accepted downside — the T2b bet.** If real resilience symptoms hop job
  buckets, the job-shaped cut is wrong and consumers would have been better served
  by catalog-group or deferred topology. This is **not** resolved here; it is
  **instrumented** (see Compliance). A red result routes to revisiting T2a/T2-defer
  at **skill #2**, not to reworking wave 1 — the seven owned cards are the same set
  under either cut, so the sunk work is topology-neutral.
- **Cost — naming proximity.** `sdp-*` is one character from `sdp-*`'s sibling
  `sdd-*`; mis-invocation is a real risk, mitigated by explicit negative-boundary
  clauses in every `description` (there is no separate trigger field to lean on —
  triggering is 100% description prose).
- **Cost — a new ADR seam** (`docs/architecture/adrs/tooling/sdp/`) that the
  workspace turn-end decision-record hook may not detect if it keys strictly on the
  bound `adr_home`. Flagged; does not change the decision.
- **No new runtime dependency; no new gate binding** (`check_gate` stays skill-sync,
  `test_gate` stays `<none>`).

## Compliance

- **The T2b bet's killing-test is the V1 trigger eval** (spec AC-8,
  `sdp-lifecycle/evals/evals.json`): a resilience symptom must route to
  `sdp-resilience` and pull only resilience cards; the eval records **in-bucket vs
  bucket-hop**. Non-clustering = revisit topology at skill #2.
- **`check_gate`** (`python3 tooling/skill-sync/skill_sync.py check`) exits 0 with
  the `sdp` node added — the family is byte-clean across projections (fitness:
  automated, every run).
- **V5 card lint** (`tooling/sdp-card-lint/sdp_card_lint.py`) enforces the §13
  invariant on every card: a stable `id`, a `## Trade-offs` section, a `## Sources`
  section, and a definition+motivation intro (fitness: automated).
- **Card contract** (`architecture-principles.mdc:24,27,28`): definition,
  motivation, example/diagram, trade-offs on every decision, cited sources —
  spec AC-17 (manual review at the gate + V5 for the mechanical subset).
- **Acceptance** is manual: the owner ratifies Proposed → Accepted at the
  implement/converge gate.

## Notes

Author: Rajnish Khatri (with Claude)
Approved by / date: Rajnish Khatri / 2026-09-13 (plan gate — PLAN-OK)
Superseded date: —
Last modified / by / what: 2026-09-13 / Accepted at the plan gate (Proposed → Accepted).
