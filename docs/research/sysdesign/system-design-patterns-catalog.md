---
type: reference
title: 'System design patterns — catalog of record'
description: >-
  The confirmed catalog for the cases/SystemDesignPatterns bundle and the
  future skill family: five groups (communication, scaling, availability,
  reliability/monitoring, architectural styles), 43 topics with ids, status,
  group-appropriate depth bars, and the owner decisions of 2026-09-13.
tags: [system-design-patterns, catalog, skills]
---

# System design patterns — catalog of record

**Owner decisions (2026-09-13).** R1: the catalogue below (owner's five groups, plus the five resilience topics, plus high-signal completions per group — marked ⊕). R2: group-appropriate depth bars (§ per group). R3: one group per research cycle. R4: every Concept lives in `cases/SystemDesignPatterns/`, including architectural styles (arch-style will cite them later). R5: the skill-family direction gate (G1/G2/G4/G5/G6 in [the brainstorm](system-design-patterns-skill-brainstorm.md)) stays open until this catalog's research is materially complete. Goal: a complete system-design skill family — breadth across groups, depth per Concept.

**Method per topic** (set by [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md) and [RetryBackoff.md](../../../cases/SystemDesignPatterns/RetryBackoff.md)): parallel source-verified research tracks → a research note in `docs/research/sysdesign/` (facts with URLs and dates, an "uncertain" list that stays out of the Concept) → a Concept at the group's depth bar → index/log updated → OKF lint green. Existing mechanism notes elsewhere in `cases/` are linked, never re-derived.

Status legend: ✅ done · 🔬 research in flight · ▢ pending.

## Group A — Communication (protocol depth bar) — ✅ complete 2026-09-13

Bar: wire semantics, connection lifecycle, scaling limits and fan-out, failure and reconnect behavior, proxy/LB interactions, verified defaults, when-not-to-use.

| Id | Topic | Status | Existing notes to link |
|---|---|---|---|
| A1 | Request–response (REST / gRPC) | ✅ | [Concept](../../../cases/SystemDesignPatterns/RequestResponse.md) · [research](request-response-external-research.md) |
| A2 | Publisher–subscriber, queues & streams | ✅ | [Concept](../../../cases/SystemDesignPatterns/PubSubQueues.md) · [research](pubsub-queues-external-research.md) |
| A3 | WebSocket communication | ✅ | [Concept](../../../cases/SystemDesignPatterns/WebSockets.md) · [research](websocket-external-research.md) |
| A4 | Server-sent events | ✅ | [Concept](../../../cases/SystemDesignPatterns/ServerSentEvents.md) · [research](sse-external-research.md) |
| ⊕A5 | Webhooks & callbacks | ✅ | [Concept](../../../cases/SystemDesignPatterns/Webhooks.md) · [research](webhooks-external-research.md) |
| ⊕A6 | API contracts & versioning | ✅ | [Concept](../../../cases/SystemDesignPatterns/ApiVersioning.md) · [research](api-versioning-external-research.md) |

## Group B — Scaling (full operational depth bar)

Bar: the CircuitBreaker.md bar — mechanics and variants, knobs with verified defaults, observability, tuning, worked calibration, failure modes, sources.

| Id | Topic | Status | Existing notes to link |
|---|---|---|---|
| B1 | Scaling strategies (vertical/horizontal, autoscaling, Little's law) | ▢ | [scalability](../../../cases/data-intensive-design/scalability.md) |
| B2 | Data partitioning & replication (operational cards over the DDIA notes) | ▢ | [sharding-overview](../../../cases/data-intensive-design/sharding-overview.md), [replication-overview](../../../cases/data-intensive-design/replication-overview.md), [rebalancing](../../../cases/data-intensive-design/rebalancing.md), [request-routing](../../../cases/data-intensive-design/request-routing.md) |
| B3 | Caching strategies (aside/through/behind, invalidation, stampede) | ▢ | [home-timeline case study](../../../cases/data-intensive-design/home-timeline-case-study.md), [performance](../../../cases/data-intensive-design/performance.md) |
| B4 | Strangler fig | ▢ | [aws ch08](../../../cases/aws/ch08.md) |
| B5 | Saga | ▢ | [aws ch08](../../../cases/aws/ch08.md), [distributed-transactions](../../../cases/data-intensive-design/distributed-transactions.md), [durable-workflows](../../../cases/data-intensive-design/durable-workflows.md) |
| B6 | Sidecar | ▢ | [aws ch08](../../../cases/aws/ch08.md), [ml-microservices-patterns](../../../cases/ml-solutions-arch/ml-microservices-patterns.md) |
| ⊕B7 | Transactional outbox & CDC | ▢ | [aws ch08](../../../cases/aws/ch08.md), [replication-logs](../../../cases/data-intensive-design/replication-logs.md) |
| ⊕B8 | CDN & edge (cache keys, stale-while-revalidate, dynamic acceleration) | ▢ | — |

## Group C — Availability (full operational depth bar) — ✅ complete 2026-09-13

| Id | Topic | Status | Notes |
|---|---|---|---|
| C1 | Circuit breaker | ✅ | [Concept](../../../cases/SystemDesignPatterns/CircuitBreaker.md) · [research](circuit-breaker-external-research.md) |
| C2 | Retry, backoff & retry budgets | ✅ | [Concept](../../../cases/SystemDesignPatterns/RetryBackoff.md) · [research](retry-backoff-external-research.md) |
| C3 | Failover mechanisms & health checks | ✅ | [Concept](../../../cases/SystemDesignPatterns/Failover.md) · [research](failover-degradation-external-research.md) |
| C4 | Rate limiting & throttling | ✅ | [Concept](../../../cases/SystemDesignPatterns/RateLimiting.md) · [research](rate-limiting-external-research.md) |
| C5 | Load balancing techniques | ✅ | [Concept](../../../cases/SystemDesignPatterns/LoadBalancing.md) · [research](load-balancing-external-research.md) |
| C6 | API gateway patterns (+ BFF) | ✅ | [Concept](../../../cases/SystemDesignPatterns/ApiGateway.md) · [research](api-gateway-external-research.md) |
| ⊕C7 | Timeouts & deadline propagation | ✅ | [Concept](../../../cases/SystemDesignPatterns/TimeoutsDeadlines.md) · [research](timeouts-deadlines-external-research.md) |
| ⊕C8 | Bulkhead & isolation | ✅ | [Concept](../../../cases/SystemDesignPatterns/Bulkhead.md) · [research](bulkhead-isolation-external-research.md) |
| ⊕C9 | Idempotency & deduplication | ✅ | [Concept](../../../cases/SystemDesignPatterns/Idempotency.md) · [research](idempotency-dedup-external-research.md) |
| ⊕C10 | Load shedding & backpressure | ✅ | [Concept](../../../cases/SystemDesignPatterns/LoadShedding.md) · [research](load-shedding-backpressure-external-research.md) |
| ⊕C11 | Graceful degradation & kill switches | ✅ | [Concept](../../../cases/SystemDesignPatterns/GracefulDegradation.md) · [research](failover-degradation-external-research.md) |

## Group D — Reliability & monitoring (instrumentation depth bar)

Bar: signals and their semantics, golden-metric frameworks, instrumentation standards (OpenTelemetry), alerting policy, tool-neutral defaults, failure modes of monitoring itself.

| Id | Topic | Status |
|---|---|---|
| D1 | Monitoring & observability foundations (signals, RED/USE) | ▢ |
| D2 | Client-side monitoring (RUM, web vitals, crash & error reporting, mobile) | ▢ |
| D3 | Server-side monitoring (golden signals, alerting) | ▢ |
| ⊕D4 | Distributed tracing & correlation | ▢ |
| ⊕D5 | SLOs, error budgets & alerting policy | ▢ |

## Group E — Architectural styles (decision depth bar)

Bar: what the style is and is not, characteristics ratings and quanta (Richards & Ford style), when-to-use / when-not, migration paths in and out, worked example, trade-off table, sources. No library-defaults section — styles have none.

| Id | Topic | Status | Note |
|---|---|---|---|
| E1 | Monolithic architecture | ▢ | |
| E2 | Microservice architecture | ▢ | |
| E3 | Layered architecture | ▢ | |
| E4 | Event-driven architecture | ▢ | style-level; mechanisms live in A2/B7 |
| E5 | Client–server architecture | ▢ | |
| E6 | Service-oriented architecture (+ modern service-based variant) | ▢ | |
| E7 | Microkernel / plug-in | ▢ | owner's "Micro Kernel -port" |
| E8 | Hexagonal = ports-and-adapters | ▢ | one Concept, both names (same pattern, Cockburn) |
| E9 | Hub-and-spoke | ▢ | |
| ⊕E10 | Modular monolith | ▢ | |
| ⊕E11 | Serverless & FaaS | ▢ | |
| ⊕E12 | CQRS & event sourcing (style-level card) | ▢ | links [event-sourcing-cqrs](../../../cases/data-intensive-design/event-sourcing-cqrs.md), [aws ch08](../../../cases/aws/ch08.md) |
| ⊕E13 | Cell-based architecture | ▢ | links [aws ch08](../../../cases/aws/ch08.md) cellular section |

**Totals:** 43 topics; **17 done** (groups C and A complete 2026-09-13); 26 pending. Research order (R3): next **B (scaling)**, then D → E, one group per cycle; the owner can reorder between cycles.

**Out of scope for the bundle:** security patterns (a separate family if ever); architecture *governance* (arch-validate owns it); anything the linter classifies as evidence.
