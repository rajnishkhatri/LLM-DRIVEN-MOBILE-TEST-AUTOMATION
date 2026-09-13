---
type: architecture
title: 'Design patterns for ML microservices'
description: 'Five patterns that absorb the distributed-system bill: saga, circuit breaker, API gateway, events, sidecar. They do not make a bad cut good.'
tags: [ml-solutions-arch, microservices, patterns, saga, event-driven]
---

# Design patterns for ML microservices

**See also:** [microservices](microservices-in-ml.md) · [challenges](microservices-challenges.md) · [big data](big-data-microservices.md)

A service cut creates three problems the monolith did not have: **cross-stage consistency**, **partial failure**, and **who the client talks to**. The source dump names five patterns. They are standard distributed-system moves applied to an ML pipeline.

| Pattern | Problem it absorbs | ML-shaped example |
|---|---|---|
| **Saga** | A multi-stage workflow is not one ACID transaction | Preprocess → train → deploy must complete as a *sequence of local steps with compensations*, not a distributed commit |
| **Circuit breaker** | A down or slow neighbour cascades | Inference stops calling a saturated training or feature service instead of retry-storming it |
| **API gateway** | Clients should not know the topology | One front door routes “score this” to inference, “retrain” to training |
| **Event-driven** | Stages should not wait on RPC | Preprocess *emits* “features ready”; training *reacts*. Decouples runtime |
| **Sidecar** | Cross-cutting ops without bloating the model server | Logs, metrics, and mTLS sit beside inference; the predictor stays a predictor |

The dump’s “sage pattern” is the **saga** pattern (long-running, per-service local transactions). Treat the spelling as a source slip.

## How they compose

A typical serving path:

1. Client hits the **gateway**.
2. Gateway calls inference (sync, because the user is waiting).
3. Inference writes a prediction event; monitoring **reacts** (async).
4. If the feature service is sick, a **circuit breaker** fails fast and the gateway returns a degraded answer or an error — it does not wait out the training cluster.
5. A **sidecar** on the inference pod ships traces without a new library in the model code.

A typical training path is almost all **events + saga**: features landed → train → register model → flip serving. Each step commits locally; a failed train does not un-write the feature batch — it compensates (mark run failed, page, leave serving on the last good version).

## What they are not

- A saga is not 2PC. Do not expect a single rollback across feature store, trainer, and registry.
- A gateway is not an orchestration engine. Long DAGs belong in a [pipeline](modular-implementation.md), not in the API layer.
- Events do not remove [model versioning](microservices-challenges.md); they make the version part of the event payload.

**Architect takeaway:** sync on the user-facing score path; async on everything that can wait (train, evaluate, monitor). Put a breaker on every *sync* hop. If you need a saga, you have already accepted that “the pipeline” is a workflow, not a transaction — version the model artefact accordingly.
