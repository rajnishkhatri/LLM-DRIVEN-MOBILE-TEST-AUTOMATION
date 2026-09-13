---
type: architecture
title: 'Big data and GPUs in ML microservices'
description: 'Four data-path techniques — partition, stream, shared store, batch — plus putting GPUs only on the services that burn them.'
tags: [ml-solutions-arch, big-data, gpu, streaming, batch]
---

# Big data and GPUs in ML microservices

**See also:** [microservices](microservices-in-ml.md) · [cloud](cloud-scaling-ml.md) · [patterns](ml-microservices-patterns.md)

Once a pipeline is cut into services, **data volume** and **compute intensity** become placement problems. You do not “make it distributed” by adding REST; you pick a data path and you pin accelerators to the stages that need them.

## Four data-path techniques

Source chapter Table 4-2. These are complementary, not alternatives.

| Approach | What it does | Named tools (source plate) | Use when |
|---|---|---|---|
| **Data partitioning** | Split a large set so several preprocess workers run in parallel | Hadoop, Spark, Kubernetes | Volume is the problem; work is embarrassingly parallel |
| **Streaming** | Continuous ingest into preprocess or inference | Kafka, Flink | The model must see data as it arrives; batch lag is the SLO miss |
| **Distributed storage** | One shared object/file store; services do not keep a full local copy | GCS, HDFS, S3 | Artefacts (features, models, logs) must outlive a container |
| **Batch processing** | Process in bounded chunks | Dask, Spark | Throughput over latency; easier retries than an infinite stream |

Partitioning without a shared store just copies the dataset N times. Streaming without back-pressure turns inference into a lossy queue. Batch without a partition key recreates a single-node pandas loop on a cluster.

## Where the GPU sits

Training (especially deep models) is the usual GPU consumer. In a service cut:

- Deploy the **training** service on GPU nodes.
- Leave preprocess and (often) inference on CPU — unless the model is large enough that scoring also needs an accelerator.
- Let the orchestrator (Kubernetes in the source dump) **schedule** GPU SKUs; do not bake “has a GPU” into every image.

That is [independent scale](modular-design-principles.md#independent-scale) applied to *hardware class*, not just replica count. It is also the main [cloud cost](cloud-scaling-ml.md) lever: an idle GPU replica is an expensive no-op.

**Architect takeaway:** pick one **system of record** for features and models (the shared store). Then choose stream vs batch by the SLO, and GPU vs CPU by the stage. A Kafka topic in front of a pandas service that still loads the world into RAM is a streaming façade, not a big-data design.
