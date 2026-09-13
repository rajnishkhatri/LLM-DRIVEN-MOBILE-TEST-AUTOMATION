---
type: analysis
title: 'Techniques for modular ML systems'
description: 'Seven implementation styles — pipelines, containers, microservices, serverless, libraries, cloud orchestration, FaaS — each with a different operational bill.'
tags: [ml-solutions-arch, modularity, orchestration, containers, trade-offs]
---

# Techniques for modular ML systems

**See also:** [principles](modular-design-principles.md) · [microservices](microservices-in-ml.md) · [cloud](cloud-scaling-ml.md) · [dependencies](ml-dependency-management.md)

The source chapter’s Table 4-1 is a **menu of deployment styles**, not a stack you install together. Pick the cheapest style that gives the [principle](modular-design-principles.md) you actually need.

| Technique | Job | Named tools (source plate) | Buys | Pays |
|---|---|---|---|---|
| **Pipeline frameworks** | Orchestrate reusable ML tasks as a DAG | Airflow, Kubeflow, Luigi | Scheduling, dependencies, retries | Orchestrator complexity at large DAGs |
| **Containerization** | Package a module with its runtime | Docker | Isolated deps, portable deploy | You now need a container platform |
| **Microservices** | Deploy each module as a service | REST, Kubernetes | Independent update and scale | Network + ops (see [challenges](microservices-challenges.md)) |
| **Serverless** | Run a module as an event-triggered function | AWS Lambda, Azure Functions | No servers to size; auto-scale | Stateless, hard time limits |
| **Modular libraries** | Share tested code for common ML steps | scikit-learn, TensorFlow | Reuse without a network | Less room to customise; still in-process |
| **Cloud orchestration** | Managed workflow of the same DAGs | AWS Step Functions, GCP Composer | Built-in monitoring and scale | Cost and vendor gravity |
| **FaaS** | Call a task as a function when needed | Lambda, Google Cloud Functions | Scale-to-zero economics | Cold start; same time-box as serverless |

Serverless and FaaS overlap on the plate — treat them as one *style* (short-lived functions) listed twice, not two architectures.

## How to read the table

- **Libraries** are the default quantum: they give reuse and abstraction with no new failure domain. Start here.
- **Pipelines** add *time*: retries, schedule, lineage of jobs. They do not by themselves isolate runtimes.
- **Containers** add *isolation of dependencies* — the prerequisite for [dependency management](ml-dependency-management.md) at more than one version of numpy.
- **Microservices** add *isolation of change and capacity* across a network. Only after the module already has a stable interface.
- **Cloud orchestration / FaaS** rent the pipeline and the scale. They do not remove the need for a clean cut; they bill you if the cut is chatty.

## Benefits that are not a style

The source dump lists four payoffs of modular design (any of the rows above can produce them if the cut is real):

| Payoff | What it actually is |
|---|---|
| Easier maintenance | A fault is local to a module; you do not retest the world to fix a scaler. |
| Team collaboration | Data engineering owns preprocess; ML owns training — Conway’s law as a *feature* of the cut. |
| Scalability | Scale the hot module only ([independent scale](modular-design-principles.md#independent-scale)). |
| Flexibility / reuse | Replace or share a module without rewriting callers. |

**Architect takeaway:** a Kubeflow DAG of tightly coupled notebooks is not modular. A single-repo library with stable artefacts often is. Choose the row that matches the quantum you already designed, not the row that matches last quarter’s conference talk.
