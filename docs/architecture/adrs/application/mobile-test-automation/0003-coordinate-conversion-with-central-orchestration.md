---
type: architecture
title: ADR 0003 — Coordinate conversion with central orchestration
description: 'Resolves the question deferred at the stage-2 gate: the conversion state machine is driven by one central orchestrator rather than event-driven choreography. Reproducibility and traceability win over fan-out distribution; the CE = 11 concentration is accepted because nothing depends on the coordinator (CA = 0), with the standing mitigation that it holds no certification policy.'
tags: [architecture, mobile-test-automation, adr, arch-decide]
---

# ADR 0003. Coordinate conversion with central orchestration

## Status

Accepted

## Context

**Forces.** The conversion flow is a bounded sequence — ingest, interpret,
resolve, generate, verify, replay, certify — with two bounded repair loops, a
human escalation, per-test checkpoints, and retry budgets. Someone must own
the state transitions. The stage-2 coupling pass found the coordinator at
**CE = 11, I = 1.00, CA = 0** — the maximum-instability profile — and deferred
the orchestration-vs-choreography question to the style stage; stage 3
resolved it in passing and handed the record here.

**Alternatives considered.**

- **Central orchestration** — one component owns transitions, checkpoints,
  retry budgets (chosen).
- **Event-driven choreography** — components react to events; no single
  high-fan-out point; the book rates EDA evolvability 5★ but simplicity and
  testability LO, and reconstructing "what happened in what order" from events
  is its known cost.

**Qualification.** Nygard test: passes — structure and dependencies. Third-law
test: passes — concentrated fan-out vs distributed traceability loss are both
significant. Timing: the state machine is week-one work; last responsible
moment reached.

### Trade-off matrix

| Contextual factor (weight) | Central orchestration | Choreography |
|---|---|---|
| Reproducibility — a verdict's path is re-readable (5) | **++** one place holds the sequence | −− event-order reconstruction is the audit gap |
| Auditability & traceability (4) | **++** state transitions are rows in one table | − distributed correlation required |
| Fit to a request-shaped bounded batch (4) | **++** the domain is a workflow, not reactions | − choreography suits "react to what happened" |
| Fan-out concentration (3) | − CE = 11 in one component | ++ no single fan-out point |
| Evolvability of the flow itself (2) | + edits localized to the coordinator | ++ add a subscriber without touching others |

## Decision

**We will drive the conversion state machine from one central orchestrator**
(the Coordinate Conversion component): it owns state transitions, per-test
checkpoint/resume, retry budgets (3 static, 3 device), the two bounded repair
loops, and the escalation to Route Human Decisions. It holds **no admission
policy** — gate thresholds and verdict logic stay in Certify Conversion.

**Technical justification:**

- Reproducibility is top-3, and its measure is that a verdict's history is
  reconstructable from stored evidence. Under orchestration that history is a
  readable sequence written by one component; under choreography it is a
  correlation exercise across event logs — the exact failure mode the
  auditability measure names.
- CE = 11 is acceptable *because* CA = 0: maximal instability is correct for
  an orchestrator nothing depends on. The mitigation from stage 2 §8 stands —
  the coordinator depends only on stable component contracts.

**Business justification:**

- **Time to market:** a Spring state machine over relational checkpoints is
  boring week-one work; an event backbone is infrastructure the week-3 gate
  does not need.
- **Cost:** no broker topology to operate beyond the two queues ADR 0007
  already requires.
- **Strategic positioning:** the audit story ("here is the sequence, row by
  row") is materially stronger in a regulated review than an event-correlation
  story.

## Consequences

- The CE = 11 concentration stays and is safe only while CA = 0 holds — the
  moment another component depends *on* the coordinator, this decision's
  premise is violated (compliance rule below).
- The coordinator is the component Phase 2 rewrites (the "human driver"
  replacement), so keeping policy out of it is what keeps the rewrite cheap.
- Forfeited from choreography: subscriber-style extensibility of the flow and
  the absence of a single fan-out point. Accepted — the flow is bounded and
  its shape is stable across both phases.

## Compliance

- **Automated (CI):** ArchUnit rule — no component outside the coordinator's
  module depends on a coordinator type (asserts CA = 0 permanently).
- **Manual (per release):** review that no gate threshold, fidelity rule, or
  verdict logic has migrated into the coordinator; any such migration requires
  revisiting ADR 0004's boundary, not a refactor.

## Notes

Author: arch-decide stage 4 (agent draft)
Date: 2026-07-26
Approved by / date: Rajnish Khatri / 2026-07-26
Superseded date: —
Last modified / by / what: —
