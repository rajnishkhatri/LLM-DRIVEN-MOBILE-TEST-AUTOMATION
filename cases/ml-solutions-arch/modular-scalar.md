---
type: overview
title: 'Building scalable and modular ML systems'
description: 'Modularity is independent change and independent scale. Microservices are one style of that, not the only one — and they buy a distributed system.'
tags: [ml-solutions-arch, modularity, microservices, overview]
---

# Building scalable and modular ML systems

**See also:** [principles](modular-design-principles.md) · [implementation techniques](modular-implementation.md) · [microservices](microservices-in-ml.md) · [when not](microservices-challenges.md)

Modularity splits an ML system into pieces that can be **changed, tested, reused, and scaled on their own**. Without that split, every new feature, dataset, or model version couples to everything else, and the cost of integration grows faster than the model quality.

This chapter is the join of two ideas that the source dump treats as one:

1. **Modular design** — cohesion, coupling, interfaces, independent scale. Still true inside a process.
2. **Microservices** — each module becomes a separately deployable service. That is a *style*, not a synonym for modularity. It buys isolation and independent scale; it pays in network, consistency, and operations.

The source dump’s closing project is **in-process classes**, not a service mesh. Treat that as a [modularity exercise](modular-pipeline-exercise.md), not a microservices proof.

## Bundle map (chapter 4)

| Need | Concept |
|---|---|
| SoC, cohesion/coupling, reuse, abstraction, independent scale | [Modular design principles](modular-design-principles.md) |
| Pipelines, containers, services, serverless, libraries — with costs | [Implementation techniques](modular-implementation.md) |
| What an ML microservice is; typical services | [Microservices in ML](microservices-in-ml.md) |
| Partition, stream, store, batch; where GPUs sit | [Big data and GPUs](big-data-microservices.md) |
| Saga, circuit breaker, gateway, events, sidecar | [Design patterns](ml-microservices-patterns.md) |
| Compute, serverless, orchestration; vendor plate; cost trap | [Cloud scaling](cloud-scaling-ml.md) |
| Complexity, latency, model versions — when *not* to split | [Challenges](microservices-challenges.md) |
| Isolation, lock files, immutable images, drift | [Dependency management](ml-dependency-management.md) |
| Class-per-stage pipeline (still one process) | [Worked exercise](modular-pipeline-exercise.md) |

## What this chapter is not

- A Kubernetes how-to. Containers and orchestration appear as *placement* choices; the source dump defers the deep dive to a later chapter.
- A current cloud support matrix. The [vendor table](cloud-scaling-ml.md) is the source chapter’s comparison plate, not a live catalog.
- A bibliography. The dump cited numbered notes (`[1]`, `[17]`, `[20]`–`[24]`) with **no reference list**. Those numbers are left as pointers, not invented citations.
- No figures were in the drop.

**Architect takeaway:** decide the **quantum of change** first (a function, a library, a container, a service). Microservices are the expensive end of that spectrum. If the bottleneck is a single training job on one team, a modular monolith plus a pipeline orchestrator is usually the cheaper quantum.
