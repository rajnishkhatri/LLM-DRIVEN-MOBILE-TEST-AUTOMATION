---
type: analysis
title: 'Sysdesign catalog research — index'
description: >-
  Supervisor index for the 2026-09-13 one-shot catalog research run:
  41 remaining topics (C1/C2 skipped) measured after wave 3 closed.
tags: [system-design-patterns, supervisor]
---

# Sysdesign catalog research — index

Home: `docs/research/sysdesign/` (merged from the 2026-09-13 worktree `research/sysdesign-catalog-notes`).  
Run date: 2026-09-13. C1/C2 already Concepts; not repeated here.

**Status legend** (file-measured, not agent-reported):

- **done** — file exists, ≥150 lines, and has the 8 required sections (Scope, Lineage, Mechanics, Verified defaults or E-group equivalent, Failure modes, Cross-links, Sources, Uncertain).
- **thin** — exists but &lt;150 lines or missing a required section.
- **failed** — missing.

Rollup: [supervisor-rollup.md](supervisor-rollup.md).

| Id | Topic | File | Lines | Status |
|---|---|---|---|---|
| A1 | Request–response (REST / gRPC sync) | [a1-request-response-external-research.md](a1-request-response-external-research.md) | 323 | done |
| A2 | Publisher–subscriber, queues & streams | [a2-pubsub-queues-external-research.md](a2-pubsub-queues-external-research.md) | 258 | done |
| A3 | WebSocket communication | [a3-websocket-external-research.md](a3-websocket-external-research.md) | 601 | done |
| A4 | Server-sent events | [a4-sse-external-research.md](a4-sse-external-research.md) | 516 | done |
| A5 | Webhooks & callbacks | [a5-webhooks-external-research.md](a5-webhooks-external-research.md) | 466 | done |
| A6 | API contracts & versioning | [a6-api-contracts-external-research.md](a6-api-contracts-external-research.md) | 288 | done |
| B1 | Scaling strategies | [b1-scaling-strategies-external-research.md](b1-scaling-strategies-external-research.md) | 301 | done |
| B2 | Data partitioning & replication | [b2-partition-replicate-external-research.md](b2-partition-replicate-external-research.md) | 366 | done |
| B3 | Caching strategies | [b3-caching-external-research.md](b3-caching-external-research.md) | 423 | done |
| B4 | Strangler fig | [b4-strangler-fig-external-research.md](b4-strangler-fig-external-research.md) | 560 | done |
| B5 | Saga | [b5-saga-external-research.md](b5-saga-external-research.md) | 553 | done |
| B6 | Sidecar | [b6-sidecar-external-research.md](b6-sidecar-external-research.md) | 559 | done |
| B7 | Transactional outbox & CDC | [b7-outbox-cdc-external-research.md](b7-outbox-cdc-external-research.md) | 508 | done |
| B8 | CDN & edge | [b8-cdn-edge-external-research.md](b8-cdn-edge-external-research.md) | 577 | done |
| C3 | Failover mechanisms & health checks | [c3-failover-health-external-research.md](c3-failover-health-external-research.md) | 370 | done |
| C4 | Rate limiting & throttling | [c4-rate-limiting-external-research.md](c4-rate-limiting-external-research.md) | 324 | done |
| C5 | Load balancing techniques | [c5-load-balancing-external-research.md](c5-load-balancing-external-research.md) | 372 | done |
| C6 | API gateway patterns (+ BFF) | [c6-api-gateway-external-research.md](c6-api-gateway-external-research.md) | 342 | done |
| C7 | Timeouts & deadline propagation | [c7-timeouts-external-research.md](c7-timeouts-external-research.md) | 302 | done |
| C8 | Bulkhead & isolation | [c8-bulkhead-external-research.md](c8-bulkhead-external-research.md) | 310 | done |
| C9 | Idempotency & deduplication | [c9-idempotency-external-research.md](c9-idempotency-external-research.md) | 354 | done |
| C10 | Load shedding & backpressure | [c10-load-shedding-external-research.md](c10-load-shedding-external-research.md) | 578 | done |
| C11 | Graceful degradation & kill switches | [c11-graceful-degradation-external-research.md](c11-graceful-degradation-external-research.md) | 291 | done |
| D1 | Monitoring & observability foundations | [d1-observability-foundations-external-research.md](d1-observability-foundations-external-research.md) | 616 | done |
| D2 | Client-side monitoring | [d2-client-monitoring-external-research.md](d2-client-monitoring-external-research.md) | 404 | done |
| D3 | Server-side monitoring | [d3-server-monitoring-external-research.md](d3-server-monitoring-external-research.md) | 545 | done |
| D4 | Distributed tracing & correlation | [d4-tracing-external-research.md](d4-tracing-external-research.md) | 292 | done |
| D5 | SLOs, error budgets & alerting policy | [d5-slos-external-research.md](d5-slos-external-research.md) | 596 | done |
| E1 | Monolithic architecture | [e1-monolith-external-research.md](e1-monolith-external-research.md) | 400 | done |
| E2 | Microservice architecture | [e2-microservices-external-research.md](e2-microservices-external-research.md) | 370 | done |
| E3 | Layered architecture | [e3-layered-external-research.md](e3-layered-external-research.md) | 377 | done |
| E4 | Event-driven architecture | [e4-event-driven-external-research.md](e4-event-driven-external-research.md) | 325 | done |
| E5 | Client–server architecture | [e5-client-server-external-research.md](e5-client-server-external-research.md) | 400 | done |
| E6 | SOA (+ service-based variant) | [e6-soa-external-research.md](e6-soa-external-research.md) | 231 | done |
| E7 | Microkernel / plug-in | [e7-microkernel-external-research.md](e7-microkernel-external-research.md) | 400 | done |
| E8 | Hexagonal = ports-and-adapters | [e8-hexagonal-external-research.md](e8-hexagonal-external-research.md) | 398 | done |
| E9 | Hub-and-spoke | [e9-hub-and-spoke-external-research.md](e9-hub-and-spoke-external-research.md) | 399 | done |
| E10 | Modular monolith | [e10-modular-monolith-external-research.md](e10-modular-monolith-external-research.md) | 394 | done |
| E11 | Serverless & FaaS | [e11-serverless-external-research.md](e11-serverless-external-research.md) | 400 | done |
| E12 | CQRS & event sourcing | [e12-cqrs-es-external-research.md](e12-cqrs-es-external-research.md) | 349 | done |
| E13 | Cell-based architecture | [e13-cell-based-external-research.md](e13-cell-based-external-research.md) | 399 | done |

**Totals:** 41 / 41 notes written. **41 done. 0 thin. 0 failed.** Shortest file that still clears the bar: E6 at 231 lines.

Supervisor scaffolding (not topic notes): [_agent-brief.md](_agent-brief.md), [_remaining-queue.md](_remaining-queue.md), [supervisor-rollup.md](supervisor-rollup.md).
