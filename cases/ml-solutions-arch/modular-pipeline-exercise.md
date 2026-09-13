---
type: notes
title: 'Worked exercise — in-process modular ML pipeline'
description: 'Five classes (load, preprocess, train, predict, orchestrate) prove cohesion, not distribution. Fit the scaler on train only. This is a modular monolith, not microservices.'
tags: [ml-solutions-arch, modularity, exercise, pipeline]
---

# Worked exercise — in-process modular ML pipeline

**See also:** [principles](modular-design-principles.md) · [microservices](microservices-in-ml.md) · [chapter map](modular-scalar.md)

The source chapter ends with a sklearn walk-through on Iris. Architecturally it is a **modular monolith**: one process, five cohesive units, narrow constructors. It is **not** a microservices system. The dump’s own next-step (“add APIs and Docker”) is the moment the quantum would change.

Do not copy the listing into a service mesh and call it done. Use this as a *cut test*.

## The five units

| Unit | Responsibility | Interface |
|---|---|---|
| **Data loader** | Fetch the dataset | `load() -> (X, y)` |
| **Preprocessor** | Scale / prepare features | `fit_transform(X_train)`; `transform(X_test)` on the *fitted* scaler |
| **Trainer** | Fit the model | `train(X, y)`; `get_model()` |
| **Predictor** | Score with a *given* model | constructor takes the model; `predict(X)` |
| **Orchestrator** | Sequence only | load → split → fit/transform → train → predict → metric |

That cut maps 1:1 onto [separation of concerns](modular-design-principles.md): loader does not train; predictor does not fit; the scaler fitted on train is the one applied to test (no leakage).

## What the exercise is proving

| Principle | How the cut shows it |
|---|---|
| SoC | Each class has one pipeline job |
| High cohesion / low coupling | Trainer never opens the dataset; it receives arrays |
| Reuse | Preprocessor and trainer can run on another matrix with the same shape |
| Abstraction | Orchestrator does not see `max_iter` or solver knobs unless you leak them |
| Independent *change* | You can swap logistic regression for another estimator behind `Trainer` |

Independent *scale* is **not** proven. There is one Python VM. Spark, GPU nodes, and Kubernetes are out of scope here — see [techniques](modular-implementation.md) and [cloud](cloud-scaling-ml.md).

## Honest next quantum

If you later split these classes into services:

- The **preprocessor’s fitted scaler** must travel with the model (same version story as [challenges](microservices-challenges.md)).
- The orchestrator becomes a [pipeline or saga](ml-microservices-patterns.md), not `main()`.
- `load_iris` as a service is the wrong cut — the bounded context is *features*, not the toy loader.

**Architect takeaway:** pass the class-cut before you pass the network-cut. If `Preprocessor.transform` and `Trainer.train` still share global state, four REST wrappers will share it too — with latency.
