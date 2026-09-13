---
type: analysis
title: 'Challenges of ML microservices'
description: 'The split costs complexity, network latency, and model-version skew. If the project is not large enough, do not pay it.'
tags: [ml-solutions-arch, microservices, trade-offs, latency, versioning]
---

# Challenges of ML microservices

**See also:** [microservices](microservices-in-ml.md) · [patterns](ml-microservices-patterns.md) · [dependencies](ml-dependency-management.md) · [chapter map](modular-scalar.md)

The source dump’s own gate: **if the project is not big enough, do not use microservices.** The benefits in the sibling Concept are real only after you can staff the extra failure domain.

## Increased complexity

N services means N runtimes, N health checks, N release units, and a communication graph. A change in preprocessing still has to be *checked* against training and inference even when you do not ship them together — the contract moved to the network, it did not vanish.

This is the opposite of “easier maintenance” unless the organisation already has platform engineering. You traded module complexity for **system** complexity (Hohpe: the network is not a local call).

## Latency

Every hop is a network call: serialisation, transfer limits, tail latency, and worse if stages sit in different regions. Real-time inference that chained three sync services can miss the SLO the monolith hit in-process.

Mitigations live in [patterns](ml-microservices-patterns.md): collapse the score path to one hop (gateway → inference), keep features local or cached, make training **async**. Do not put a preprocess RPC on the user-facing path unless the SLO allows it.

## Model versioning

Serving, training, and evaluation now disagree about *which* model is in play unless versioning is a first-class artefact (registry, explicit version on the request, or both). Without that, you get silent skew: training writes v17, two replicas still score v16, monitoring attributes the drop to “data drift.”

Version the **model artefact and the feature schema** together. A saga that deploys “the new model” without pinning the scaler is a partial deploy.

## The last-responsible-moment test

Stay in a [modular monolith](modular-design-principles.md) (or a [pipeline of jobs](modular-implementation.md)) while:

- One team owns the whole pipeline
- The scale bottleneck is a batch job, not independent SLOs
- You cannot yet name the contract that would cross a service boundary

Split when a stage needs its own *release cadence*, *hardware class*, or *language*, and you can staff the [dependency](ml-dependency-management.md) and observability bill.

**Architect takeaway:** microservices are an expensive way to buy independent scale. Latency and version skew are not “ops later” — they are the architecture. If you cannot answer “what is the model version on this prediction?”, you are not ready for the split.
