---
type: architecture
title: 'Monitoring and observability'
description: 'Not set-and-forget. Watch pipelines and stores for failures; watch quality metrics for bad records. Observability is itself a data problem: metrics, events, logs, traces.'
tags: [financial-data-architecture, observability, monitoring, quality]
---

# Monitoring and observability

**See also:** [components](architecture-components.md) · [pipelines](pipelines-orchestration.md) · [data quality](data-quality.md) · [scalability](scalability-performance.md)

A financial data architecture is not “set it and forget it.” The chapter’s metaphor: a living organism. It needs ongoing health checks.

| Kind | What you watch |
|---|---|
| **Operational monitoring** | Pipelines, storage, processing — failures and bottlenecks that stop flow |
| **Data-quality monitoring** | Error ratio (share of incorrect or invalid data); issues on individual records (e.g. invalid identifiers) |

The source book’s **Chapter 4** will treat quality dimensions and metrics in more detail. Those notes are not in this bundle yet.

## Observability

Monitoring evolved from reactive checks to **observability**: you understand internal behaviour from external outputs. The chapter calls this **a data-management problem first**. Systems emit heterogeneous time series that must be indexed, stored, and queried near-real-time.

Four instrumentation types (industry names: **metrics, events, logs, traces**):

| Type | Shape |
|---|---|
| **Metrics** | Numeric gauges and counts |
| **Events** | Highly structured system events |
| **Logs** | Unstructured strings |
| **Traces** | Graph of a request’s execution path |

**Architect takeaway:** budget an observability store the way you budget a market-data store. If quality metrics are only in a weekly email, you cannot catch the [bad-data consequences](data-quality.md) before a report goes out.
