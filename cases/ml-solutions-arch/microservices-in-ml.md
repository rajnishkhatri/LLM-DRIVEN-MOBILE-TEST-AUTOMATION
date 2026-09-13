---
type: architecture
title: 'Microservices in ML'
description: 'An ML microservice is one pipeline stage as a self-contained deployable: own runtime, own scale, API or events to neighbours. Heterogeneous stacks are the point.'
tags: [ml-solutions-arch, microservices, ml-pipeline, architecture]
---

# Microservices in ML

**See also:** [chapter map](modular-scalar.md) · [principles](modular-design-principles.md) · [patterns](ml-microservices-patterns.md) · [challenges](microservices-challenges.md)

A **microservice** is a loosely coupled, independently deployable unit with its own process, dependencies, and lifecycle. In ML, that unit is usually **one stage of the pipeline**, not “the model.”

The monolith being decomposed is the end-to-end script: ingest → features → train → infer → watch. After the split, each stage is a service you can restart, version, and scale without shipping the others.

This is an architecture *style* (distributed, service-per-stage). It is a stronger claim than [modular libraries](modular-implementation.md). If you only need independent *change*, stay in-process; if you need independent *capacity or release*, you are in this Concept.

## Typical services

The source dump’s worked cut (four services). Names are roles, not products:

| Service | Responsibility | Talks to |
|---|---|---|
| **Preprocessing** | Clean, engineer, transform | Upstream data; emits features |
| **Training** | Fit a model from preprocessed data | Feature artefact in; model artefact out |
| **Inference** | Score new inputs with a trained model | Model artefact + live requests |
| **Monitoring** | Health and performance in production | Inference outputs, data drift signals |

Self-contained means each service **brings its own runtime**. Preprocessing can be Python/pandas; inference can be C++ or a GPU runtime. That heterogeneity is the design goal, not an accident — it is also why [dependency isolation](ml-dependency-management.md) becomes mandatory.

## What you buy (when the cut is real)

| Benefit | Mechanism | Failure if fake |
|---|---|---|
| **Independent scale** | Training saturates GPUs; inference stays on cheap CPU replicas (or the reverse for huge models) | One replica count for the whole pipeline |
| **Technology flexibility** | Best tool per stage | A shared base image that pins every stage to one Python |
| **Safer deploy** | A preprocessing bug does not require redeploying the model server | Lock-step release of all four “services” |

## Boundary test

A stage is a microservice only if **three** things are true:

1. It can fail without taking the others down (isolation).
2. It can ship on its own cadence (independent deploy).
3. It can grow replicas without growing the others (independent scale).

Sharing a database, a release train, or a notebook kernel fails the test. Use the [challenge list](microservices-challenges.md) before drawing four boxes.

**Architect takeaway:** draw the four services as *bounded contexts* (features, training, serving, observe). The contract is the artefact that crosses the line (a feature batch, a model version, a prediction log) — not a REST path. Then pick [sync or async](ml-microservices-patterns.md) for that contract.
