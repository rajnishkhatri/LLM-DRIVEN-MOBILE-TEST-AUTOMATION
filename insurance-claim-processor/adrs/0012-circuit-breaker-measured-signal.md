# ADR 0012. Trip a measured circuit breaker in the workflow, not a naive one

## Status
Accepted — **amends the C1 deferral** in `../risk/resilience-clinic.md` §3/§5
("C1 / C8 / C10: named, not applied until the metrics above exist")

## Context
The resilience clinic deliberately did **not** apply a circuit breaker: the PoC
had no live error-rate metric, and a breaker whose "failures" are actually slow
successes converts a slowdown into an outage (C1 doctrine, clinic §2). Best
practice #4 asks for a Step Functions breaker that detects model failure and
routes to fallback/degraded modes. The blocker the clinic named — no metric — is
removed by ADR 0015. Two forces now hold: a production claim stream can fill a
breaker window honestly, and catastrophe bursts make "keep calling a dead model"
expensive and slow.

A breaker needs state **shared across executions**: each Step Functions
execution is independent, so an in-process breaker sees nothing. State
alternatives: (a) a **CloudWatch composite alarm as the trip signal + an
AppConfig flag** the workflow reads; (b) a DynamoDB token-bucket/counter the
workflow reads and writes; (c) an in-process breaker — rejected, blind across
executions.

## Decision
We will add a circuit breaker to the Step Functions workflow whose open/close
signal is a **measured per-model error/timeout rate** (from ADR 0015), exposed
to the workflow as a CloudWatch-alarm-backed **AppConfig flag** (ADR 0010),
read at a `Choice` state.

- WHILE a model's breaker is open, the workflow routes claims for that model to
  the degraded path (ADR 0014) without invoking it.
- The breaker half-opens on recovery (probe a bounded number of claims), then
  closes.
- Rejected: **DynamoDB token-bucket** (adds a stateful store + hot-path
  read/write and a second source of truth for model health, separate from the
  metrics that answer exactly that); **in-process breaker** (invisible across
  SFN executions); **count-based trip** (trips on slow successes — the named C1
  antipattern).

Business justification: during a model outage or throttle storm, a breaker stops
paying latency + tokens on calls that will fail and shifts to a cheaper tier —
protecting both `$/claim` and the review SLA.

## Consequences
Good: honors the clinic's own "confirm the metric first" rule (the trip signal
*is* the metric); one source of truth for model health; the trip is auditable
(alarm history + `breaker_state` on results); reversible via the same flag
(ADR 0010). Bad: alarm evaluation adds trip/close latency (seconds–minutes,
acceptable for back-office); a mis-tuned alarm trips early or late (mitigate:
start conservative, tune from the p99/p99.9 the clinic §2 named); the breaker
depends on ADR 0015 shipping first.

## Compliance
Fitness (offline): the breaker decision is a pure function of the injected
signal — a slow-success series does NOT open it (AC-N1); with the flag "open",
routing selects the degraded path and does not call the model (AC-N2, unit +
`[sfn]` Choice); half-open→close on a recovering signal (AC-N4); transitions
recorded as metric + `breaker_state` (AC-N5). `[off]` asserts the state is read
from the injected provider, never in-process (AC-N3). `[sfn]` asserts the Choice
on breaker state in the ASL.

## Notes
Author: sdd-spec (model-resilience increment)
Approved by / date: Rajnish Khatri / 2026-09-21
Superseded date:
Last modified: 2026-09-21 / amends resilience-clinic C1 deferral
