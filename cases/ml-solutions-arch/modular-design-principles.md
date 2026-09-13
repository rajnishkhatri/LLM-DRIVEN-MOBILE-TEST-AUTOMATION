---
type: architecture
title: 'Modular design principles for ML systems'
description: 'Five properties — SoC, high cohesion, low coupling, reuse, abstraction — plus independent scale. They apply inside a process before they apply across a network.'
tags: [ml-solutions-arch, modularity, cohesion, coupling, solid]
---

# Modular design principles for ML systems

**See also:** [chapter map](modular-scalar.md) · [techniques](modular-implementation.md) · [in-process exercise](modular-pipeline-exercise.md)

These are software-design properties applied to an ML workflow. They do **not** require a network. A well-cut Python package can satisfy them; a badly cut “microservice” can violate all of them.

## Separation of concerns

One module, one job. In an ML pipeline the usual cuts are **ingest / preprocess**, **train**, **evaluate**, **deploy / infer**. Mixing `read_csv` + fill-na + min-max + `LogisticRegression.fit` + accuracy in one script is the anti-pattern: a feature-extraction change forces a re-test of training and scoring.

This is Single Responsibility applied to the pipeline, not to a class name.

## High cohesion, low coupling

**High cohesion:** the parts *inside* a module belong together (a preprocessor owns cleaning, transforms, and feature prep — not training).

**Low coupling:** modules meet at a **narrow interface**. Training consumes a feature matrix (and a schema), not a raw database. If training opens the warehouse itself, you have not separated the concerns; you have hidden a join.

A cohesive `preprocess(X) -> X'` plus `train(X', y) -> model` can swap the trainer without rewriting the cleaner. A `process_and_train()` that reads the CSV internally cannot.

## Reusability

A module that encodes a *policy* (scale with a fitted scaler; validate missingness) can run on the next dataset. A script that `fit_transform`s one file in place cannot: the scaler never leaves the notebook.

The architectural move is to return **both the transformed data and the fitted artefact** (scaler, encoder, imputer) so later rows see the same transform. That is the same contract a feature store or a model registry will later demand.

## Abstraction

Callers see data in, model (or predictions) out. Optimizer choice, batch size, and convergence sit behind the interface. Leaking `solver='lbfgs'` and `model.coef_` into every caller is an Interface Segregation failure: every consumer is coupled to sklearn’s training knobs.

Abstraction is what makes [independent scale](#independent-scale) possible later: you can replace the body (Spark job, GPU trainer, remote service) without rewriting the callers.

## Independent scale

Because modules are separate, you scale the **hot** one. If ingest is the bottleneck, add workers (or a distributed frame such as Spark) to ingest; leave the trainer’s replica count alone. The source dump’s PySpark sketch is that idea: stop looping columns in a single pandas process when the data no longer fits.

Independent scale is a *deployment* property. In-process functions give you independent *change*; they do not give you independent *capacity* until the module is a process or a job.

**Architect takeaway:** write the five properties as tests on the *cut*, not on the brand. If two “services” share a database and a lock-step release, you have a distributed monolith — high coupling with extra latency. If four classes in one repo talk only through typed artefacts, you already have the design the [exercise](modular-pipeline-exercise.md) is teaching.
