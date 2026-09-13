---
type: analysis
title: 'Cloud scaling for ML microservices'
description: 'Rent compute, functions, and orchestration per stage. The source vendor plate is a catalogue, not a support matrix. Mis-sized GPUs dominate the bill.'
tags: [ml-solutions-arch, cloud, scaling, cost, kubernetes]
---

# Cloud scaling for ML microservices

**See also:** [microservices](microservices-in-ml.md) · [big data and GPUs](big-data-microservices.md) · [techniques](modular-implementation.md)

Cloud here is **elastic placement**: give training a GPU instance for the job, give inference a cheaper pool, stop paying when idle. That only helps if the [service cut](microservices-in-ml.md) is real. Autoscaling a monolith scales the cold parts with the hot ones.

## Three cloud knobs

| Knob | What you rent | ML use | Watch |
|---|---|---|---|
| **Compute** | VMs / nodes (EC2, GCE, Azure VMs in the dump) | GPU boxes for training; CPU (or mixed) for inference | Huge models may need GPUs at *serve* time too |
| **Serverless** | Short-lived functions (Lambda, Cloud Functions) | Burst inference, light transforms | Time limits, cold start, no sticky GPU |
| **Orchestration** | Kubernetes (named in the dump) | Place containers, restart, autoscale | Cluster ops become the product |

The dump flags the cost failure mode explicitly: **misconfigured autoscaling** and **idle high-end GPU instances**. That is a fitness function, not a footnote. The source points at a later chapter for cost tactics; this bundle does not invent them.

## Source comparison plate (Table 4-3)

Named products as the **chapter listed them**. Not a live capability matrix, not a recommendation, not a region/SLA claim.

| Plate row | Description (as listed) | Tools (as listed) | Use case (as listed) |
|---|---|---|---|
| AWS | Broad ML services | EC2, S3, Lambda, SageMaker | Compute, storage, serverless, training |
| Google Cloud | AI-specific services, scale | Compute Engine, GCS, Vertex AI | Compute, big data, training |
| Microsoft Azure | Integrated, enterprise support | Azure ML, VMs, Blob Storage | Orchestration, enterprise deploy |
| IBM Cloud | AI-driven enterprise | Watson Machine Learning | AI microservices, train/infer |
| Alibaba Cloud | Compute and storage | PAI, ECS, OSS | Storage, compute, pipeline management |

Read it as “these are the *kinds* of building blocks” (VM, object store, function, managed ML). Substitute your actual vendor later; do not treat the row as an endorsement.

**Architect takeaway:** map each [service](microservices-in-ml.md) to a *SKU class* (CPU, GPU, function) and a *lifetime* (always-on vs job vs request). Put a budget alarm on GPU node groups before you put a replica count. Orchestration places the boxes; it does not choose the quantum — [principles](modular-design-principles.md) did.
