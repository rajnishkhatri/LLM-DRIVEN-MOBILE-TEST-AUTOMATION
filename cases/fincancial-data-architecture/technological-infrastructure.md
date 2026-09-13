---
type: architecture
title: 'Technological infrastructure'
description: 'Storage follows use case: SQL for OLTP, warehouse for analytics, lake for raw and ML I/O, kdb+ for HFT time series. Processing is stream or batch, on-prem, cloud, or managed.'
tags: [financial-data-architecture, infrastructure, storage, kafka, kdb]
---

# Technological infrastructure

**See also:** [components](architecture-components.md) · [classifying — storage](classifying-architectures.md#classification-by-storage-technology) · [legacy systems](legacy-systems.md) · [scalability](scalability-performance.md)

Foundational tech for storing, processing, and retrieving data. **Storage follows use case**, not fashion.

| Store | Fit named in the chapter |
|---|---|
| **Relational (SQL)** | Operational systems with transactional needs |
| **Data warehouse** | Analytical workloads |
| **Data lake** | Diverse, large, unstructured — archives, backups, ML input/output |
| **Specialised** | In-memory time series such as **kdb+** for high-frequency trading and real-time market analytics — high volume of time-stamped data, low latency |

**High-frequency trading (HFT)** (source footnote): algorithmic trading that uses fast machines and algorithms to execute large volumes of orders in milliseconds or microseconds to capture small price moves.

## Processing

Frameworks for real-time and batch. Chapter examples: **Apache Kafka** or **Apache Flink** for streams; **Apache Airflow** for batch ETL. Deploy on-premises, in the cloud, or as managed services from cloud vendors.

See [constraints — technology](architecture-constraints.md#technology-drivers) for latency, lock-in, and legacy limits on these choices.

**Architect takeaway:** name the access pattern first (point transaction, scan, tick). kdb+ for the book and Snowflake for the warehouse can both be right. A single “lakehouse for everything” that must also clear is usually a [classification](classifying-architectures.md) collision, not a simplification.
