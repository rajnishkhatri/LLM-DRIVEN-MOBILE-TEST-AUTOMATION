---
type: architecture
title: 'Pipelines and orchestration'
description: 'Pipelines are the sequenced tasks of ingest, transform, deliver. Orchestration adds dependencies, retries, alerts, audit, and batch-or-stream — often several tools, not one.'
tags: [financial-data-architecture, pipelines, orchestration, airflow]
---

# Pipelines and orchestration

**See also:** [components](architecture-components.md) · [transformation](processing-transformation.md) · [infrastructure](technological-infrastructure.md) · [observability](monitoring-observability.md)

Pipelines are structured task sequences that move data through ingest, transform, and delivery so flow is automatic, predictable, consistent, and timely.

**Orchestration** keeps those pipelines running. Features the chapter lists:

| Capability | Job |
|---|---|
| **Task dependency** | Prerequisites finish before the next task starts |
| **Error handling and retries** | Detect, log, retry failed tasks |
| **Monitoring and alerting** | Live status; notify before the business notices |
| **Logging and auditing** | Timestamps, status, errors — the compliance trail |
| **Batch and real-time** | Scheduled high-volume *and* continuous low-latency |

Tools named: **Apache Airflow** (batch), **AWS Step Functions** (real-time, event-driven). Some firms build custom orchestrators for specific needs. In practice, organisations **rarely use one tool for everything**; different tools orchestrate different pipeline types.

**Architect takeaway:** the architecture is the *set* of pipelines and their contracts, not the orchestrator brand. If audit logs and retries live in three tools with no shared identity, [governance](financial-data-governance.md) cannot answer “what ran when.”
