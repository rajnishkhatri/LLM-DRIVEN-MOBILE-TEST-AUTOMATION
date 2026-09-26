---
type: reference
title: 'System design patterns — catalog of record'
description: >-
  The confirmed catalog for the cases/SystemDesignPatterns bundle and the
  future skill family: five groups (communication, scaling, availability,
  reliability/monitoring, architectural styles), 43 topics all written as
  Concepts, group-appropriate depth bars, and the owner decisions of
  2026-09-13.
tags: [system-design-patterns, catalog, skills]
---

# System design patterns — catalog of record

**Owner decisions (2026-09-13).** R1: the catalogue below (owner's five groups, plus the five resilience topics, plus high-signal completions per group — marked ⊕). R2: group-appropriate depth bars (§ per group). R3: one group per research cycle (all five groups now have Concepts). R4: every Concept lives in `cases/SystemDesignPatterns/`, including architectural styles (arch-style will cite them later). R5: catalog research is closed; the skill-family direction gate is a separate decision — live structure in [the MECE handover](system-design-patterns-skill-mece-handover.md), historical record in [the brainstorm](system-design-patterns-skill-brainstorm.md). Goal: a complete system-design skill family — breadth across groups, depth per Concept.

**Depth-audit (2026-09-13).** Concepts scored against the group bars and their catalog-wave notes. Most cards already met the bar; the pass folded one missing B1 failure mode (scale-to-zero split brain) and retargeted stale sibling links (B3↔B8, B4/B5/B7/A2↔B7, E4/E12). Catalog rows for A1/A2/A4/A5 and C4–C11 now name the catalog-wave research file first (first-pass notes kept as trail). Uncertain items stay in the research notes.

**Method per topic** (set by [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md) and [RetryBackoff.md](../../../cases/SystemDesignPatterns/RetryBackoff.md)): parallel source-verified research tracks → a research note in `docs/research/sysdesign/` (facts with URLs and dates, an "uncertain" list that stays out of the Concept) → a Concept at the group's depth bar → index/log updated → OKF lint green. Existing mechanism notes elsewhere in `cases/` are linked, never re-derived.

Status legend: ✅ done · 🔬 research in flight · ▢ pending.

## Group A — Communication (protocol depth bar) — ✅ complete 2026-09-13

Bar: wire semantics, connection lifecycle, scaling limits and fan-out, failure and reconnect behavior, proxy/LB interactions, verified defaults, when-not-to-use.

| Id | Topic | Status | Existing notes to link |
|---|---|---|---|
| A1 | Request–response (REST / gRPC) | ✅ | [Concept](../../../cases/SystemDesignPatterns/RequestResponse.md) · [research](a1-request-response-external-research.md) · first-pass [request-response-external-research.md](request-response-external-research.md) |
| A2 | Publisher–subscriber, queues & streams | ✅ | [Concept](../../../cases/SystemDesignPatterns/PubSubQueues.md) · [research](a2-pubsub-queues-external-research.md) · first-pass [pubsub-queues-external-research.md](pubsub-queues-external-research.md) |
| A3 | WebSocket communication | ✅ | [Concept](../../../cases/SystemDesignPatterns/WebSocket.md) · [research](a3-websocket-external-research.md) · first-pass [WebSockets.md](../../../cases/SystemDesignPatterns/WebSockets.md) |
| A4 | Server-sent events | ✅ | [Concept](../../../cases/SystemDesignPatterns/ServerSentEvents.md) · [research](a4-sse-external-research.md) · first-pass [sse-external-research.md](sse-external-research.md) |
| ⊕A5 | Webhooks & callbacks | ✅ | [Concept](../../../cases/SystemDesignPatterns/Webhooks.md) · [research](a5-webhooks-external-research.md) · first-pass [webhooks-external-research.md](webhooks-external-research.md) |
| ⊕A6 | API contracts & versioning | ✅ | [Concept](../../../cases/SystemDesignPatterns/ApiContracts.md) · [research](a6-api-contracts-external-research.md) · first-pass [ApiVersioning.md](../../../cases/SystemDesignPatterns/ApiVersioning.md) |

## Group B — Scaling (full operational depth bar) — ✅ complete 2026-09-13

Bar: the CircuitBreaker.md bar — mechanics and variants, knobs with verified defaults, observability, tuning, worked calibration, failure modes, sources. Catalog B2 is five operational cards (supervisor split; one research note).

| Id | Topic | Status | Existing notes to link |
|---|---|---|---|
| B1 | Scaling strategies (vertical/horizontal, autoscaling, Little's law) | ✅ | [Concept](../../../cases/SystemDesignPatterns/ScalingStrategies.md) · [research](b1-scaling-strategies-external-research.md) · [scalability](../../../cases/data-intensive-design/scalability.md) |
| B2 | Data partitioning & replication (five operational cards) | ✅ | [Partitioning](../../../cases/SystemDesignPatterns/Partitioning.md) · [Single-leader](../../../cases/SystemDesignPatterns/SingleLeaderReplication.md) · [Multi-leader](../../../cases/SystemDesignPatterns/MultiLeaderReplication.md) · [Leaderless](../../../cases/SystemDesignPatterns/LeaderlessReplication.md) · [Rebalance & routing](../../../cases/SystemDesignPatterns/RebalanceRouting.md) · [research](b2-partition-replicate-external-research.md) |
| B3 | Caching strategies (aside/through/behind, invalidation, stampede) | ✅ | [Concept](../../../cases/SystemDesignPatterns/CachingStrategies.md) · [research](b3-caching-external-research.md) |
| B4 | Strangler fig | ✅ | [Concept](../../../cases/SystemDesignPatterns/StranglerFig.md) · [research](b4-strangler-fig-external-research.md) · [aws ch08](../../../cases/aws/ch08.md) |
| B5 | Saga | ✅ | [Concept](../../../cases/SystemDesignPatterns/Saga.md) · [research](b5-saga-external-research.md) |
| B6 | Sidecar | ✅ | [Concept](../../../cases/SystemDesignPatterns/Sidecar.md) · [research](b6-sidecar-external-research.md) |
| ⊕B7 | Transactional outbox & CDC | ✅ | [Concept](../../../cases/SystemDesignPatterns/OutboxCdc.md) · [research](b7-outbox-cdc-external-research.md) |
| ⊕B8 | CDN & edge (cache keys, stale-while-revalidate, dynamic acceleration) | ✅ | [Concept](../../../cases/SystemDesignPatterns/CdnEdge.md) · [research](b8-cdn-edge-external-research.md) |

## Group C — Availability (full operational depth bar) — ✅ complete 2026-09-13

| Id | Topic | Status | Notes |
|---|---|---|---|
| C1 | Circuit breaker | ✅ | [Concept](../../../cases/SystemDesignPatterns/CircuitBreaker.md) · [research](circuit-breaker-external-research.md) |
| C2 | Retry, backoff & retry budgets | ✅ | [Concept](../../../cases/SystemDesignPatterns/RetryBackoff.md) · [research](retry-backoff-external-research.md) |
| C3 | Failover mechanisms & health checks | ✅ | [Concept](../../../cases/SystemDesignPatterns/FailoverHealth.md) · [research](c3-failover-health-external-research.md) · first-pass [Failover.md](../../../cases/SystemDesignPatterns/Failover.md) |
| C4 | Rate limiting & throttling | ✅ | [Concept](../../../cases/SystemDesignPatterns/RateLimiting.md) · [research](c4-rate-limiting-external-research.md) · first-pass [rate-limiting-external-research.md](rate-limiting-external-research.md) |
| C5 | Load balancing techniques | ✅ | [Concept](../../../cases/SystemDesignPatterns/LoadBalancing.md) · [research](c5-load-balancing-external-research.md) · first-pass [load-balancing-external-research.md](load-balancing-external-research.md) |
| C6 | API gateway patterns (+ BFF) | ✅ | [Concept](../../../cases/SystemDesignPatterns/ApiGateway.md) · [research](c6-api-gateway-external-research.md) · first-pass [api-gateway-external-research.md](api-gateway-external-research.md) |
| ⊕C7 | Timeouts & deadline propagation | ✅ | [Concept](../../../cases/SystemDesignPatterns/TimeoutsDeadlines.md) · [research](c7-timeouts-external-research.md) · first-pass [timeouts-deadlines-external-research.md](timeouts-deadlines-external-research.md) |
| ⊕C8 | Bulkhead & isolation | ✅ | [Concept](../../../cases/SystemDesignPatterns/Bulkhead.md) · [research](c8-bulkhead-external-research.md) · first-pass [bulkhead-isolation-external-research.md](bulkhead-isolation-external-research.md) |
| ⊕C9 | Idempotency & deduplication | ✅ | [Concept](../../../cases/SystemDesignPatterns/Idempotency.md) · [research](c9-idempotency-external-research.md) · first-pass [idempotency-dedup-external-research.md](idempotency-dedup-external-research.md) |
| ⊕C10 | Load shedding & backpressure | ✅ | [Concept](../../../cases/SystemDesignPatterns/LoadShedding.md) · [research](c10-load-shedding-external-research.md) · first-pass [load-shedding-backpressure-external-research.md](load-shedding-backpressure-external-research.md) |
| ⊕C11 | Graceful degradation & kill switches | ✅ | [Concept](../../../cases/SystemDesignPatterns/GracefulDegradation.md) · [research](c11-graceful-degradation-external-research.md) · first-pass [failover-degradation-external-research.md](failover-degradation-external-research.md) |

## Group D — Reliability & monitoring (instrumentation depth bar) — ✅ complete 2026-09-13

Bar: signals and their semantics, golden-metric frameworks, instrumentation standards (OpenTelemetry), alerting policy, tool-neutral defaults, failure modes of monitoring itself.

| Id | Topic | Status | Existing notes to link |
|---|---|---|---|
| D1 | Monitoring & observability foundations (signals, RED/USE) | ✅ | [Concept](../../../cases/SystemDesignPatterns/MonitoringObservabilityFoundations.md) · [research](d1-observability-foundations-external-research.md) |
| D2 | Client-side monitoring (RUM, web vitals, crash & error reporting, mobile) | ✅ | [Concept](../../../cases/SystemDesignPatterns/ClientSideMonitoring.md) · [research](d2-client-monitoring-external-research.md) |
| D3 | Server-side monitoring (golden signals, alerting) | ✅ | [Concept](../../../cases/SystemDesignPatterns/ServerSideMonitoring.md) · [research](d3-server-monitoring-external-research.md) |
| ⊕D4 | Distributed tracing & correlation | ✅ | [Concept](../../../cases/SystemDesignPatterns/DistributedTracing.md) · [research](d4-tracing-external-research.md) |
| ⊕D5 | SLOs, error budgets & alerting policy | ✅ | [Concept](../../../cases/SystemDesignPatterns/SlosErrorBudgets.md) · [research](d5-slos-external-research.md) |

## Group E — Architectural styles (decision depth bar) — ✅ complete 2026-09-13

Bar: what the style is and is not, characteristics ratings and quanta (Richards & Ford style), when-to-use / when-not, migration paths in and out, worked example, trade-off table, sources. No library-defaults section — styles have none.

| Id | Topic | Status | Note |
|---|---|---|---|
| E1 | Monolithic architecture | ✅ | [Concept](../../../cases/SystemDesignPatterns/Monolith.md) · [research](e1-monolith-external-research.md) |
| E2 | Microservice architecture | ✅ | [Concept](../../../cases/SystemDesignPatterns/Microservices.md) · [research](e2-microservices-external-research.md) |
| E3 | Layered architecture | ✅ | [Concept](../../../cases/SystemDesignPatterns/LayeredArchitecture.md) · [research](e3-layered-external-research.md) |
| E4 | Event-driven architecture | ✅ | [Concept](../../../cases/SystemDesignPatterns/EventDriven.md) · [research](e4-event-driven-external-research.md); mechanisms live in A2/B7 |
| E5 | Client–server architecture | ✅ | [Concept](../../../cases/SystemDesignPatterns/ClientServer.md) · [research](e5-client-server-external-research.md) |
| E6 | Service-oriented architecture (+ modern service-based variant) | ✅ | [Concept](../../../cases/SystemDesignPatterns/ServiceOriented.md) · [research](e6-soa-external-research.md) |
| E7 | Microkernel / plug-in | ✅ | [Concept](../../../cases/SystemDesignPatterns/Microkernel.md) · [research](e7-microkernel-external-research.md) |
| E8 | Hexagonal = ports-and-adapters | ✅ | [Concept](../../../cases/SystemDesignPatterns/Hexagonal.md) · [research](e8-hexagonal-external-research.md); one Concept, both names (Cockburn) |
| E9 | Hub-and-spoke | ✅ | [Concept](../../../cases/SystemDesignPatterns/HubAndSpoke.md) · [research](e9-hub-and-spoke-external-research.md); enterprise integration hub, not WAN hub-spoke |
| ⊕E10 | Modular monolith | ✅ | [Concept](../../../cases/SystemDesignPatterns/ModularMonolith.md) · [research](e10-modular-monolith-external-research.md) |
| ⊕E11 | Serverless & FaaS | ✅ | [Concept](../../../cases/SystemDesignPatterns/Serverless.md) · [research](e11-serverless-external-research.md) |
| ⊕E12 | CQRS & event sourcing (style-level card) | ✅ | [Concept](../../../cases/SystemDesignPatterns/CqrsEventSourcing.md) · [research](e12-cqrs-es-external-research.md) · [event-sourcing-cqrs](../../../cases/data-intensive-design/event-sourcing-cqrs.md) |
| ⊕E13 | Cell-based architecture | ✅ | [Concept](../../../cases/SystemDesignPatterns/CellBased.md) · [research](e13-cell-based-external-research.md) · [aws ch08](../../../cases/aws/ch08.md) cellular section |

**Totals:** 43 catalog topics, all ✅. Bundle has **47 canonical Concepts** (B2 split into five cards) plus **3 first-pass cards** tagged `superseded` (A3 `WebSockets.md`, A6 `ApiVersioning.md`, C3 `Failover.md`). Research notes live under [docs/research/sysdesign/](./). Skill-family gate: [MECE handover](system-design-patterns-skill-mece-handover.md) (live) · [brainstorm](system-design-patterns-skill-brainstorm.md) (history).

**Out of scope for the bundle:** security patterns (a separate family if ever); architecture *governance* (arch-validate owns it); anything the linter classifies as evidence.
