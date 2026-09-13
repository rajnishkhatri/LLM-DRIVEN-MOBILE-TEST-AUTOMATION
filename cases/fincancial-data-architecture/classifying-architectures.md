---
type: analysis
title: 'Categorising financial data architectures'
description: 'Six lenses: storage, deployment, modeling, processing, business function, and ownership. They overlap. This book leads with business function and domain problems.'
tags: [financial-data-architecture, classification, lakehouse, data-mesh, lambda]
---

# Categorising financial data architectures

**See also:** [chapter 2 map](fin-data-arch.md) · [components](architecture-components.md) · [constraints](architecture-constraints.md) · [definition](defining-financial-data-architecture.md)

“Data architecture” is used inconsistently: sometimes a processing pattern (Lambda), sometimes a domain design (payments data architecture). There is no single correct taxonomy. It depends whether you are looking at technology, business function, or data movement — like describing a car by engine, purpose, or style.

These lenses are **not mutually exclusive**. A large institution often needs a hybrid. A small fintech may pick a simpler cloud architecture aimed at one business need.

**This book’s lead lens is business function and domain problems** (e.g. Chapter 7: design a financial data ledger). Storage, processing, governance, and deployment enter when they are relevant to that problem.

## Classification by storage technology

Natural for implementers: “SQL, warehouse, lake, or a mix?”

| Class | What it is | Examples in the chapter |
|---|---|---|
| **Traditional relational (SQL)** | Structured data in relational stores | MySQL, PostgreSQL, Oracle |
| **Data warehouse** | Analytical / historical queries | Snowflake, Amazon Redshift, Google BigQuery |
| **NoSQL** | Un/semi-structured; dynamic schema; horizontal scale | MongoDB, Cassandra, Couchbase |
| **Data lake** | Raw, native format | HDFS; Amazon S3; Azure Data Lake Storage |
| **Lakehouse** | Lake flexibility + warehouse structure and performance | Databricks Lakehouse; Google BigLake; Microsoft Fabric Lakehouse; AWS Lake Formation + Athena + Redshift Spectrum |

## Deployment-based classification

Resonates with infrastructure and ops: “our DC, the cloud, or both — and is the cloud compliant?”

| Class | Where data is managed |
|---|---|
| **On-premises mainframe** | Local physical servers or mainframes |
| **Cloud-based** | Cloud platforms; scale and flexibility |
| **Hybrid** | Mix of local control and cloud scale |

## Classification by data modeling approach

Questions for modellers and analytics engineers: consistency, query speed, or a vault?

| Approach | Intent |
|---|---|
| **Normalised** | Minimise redundancy, maximise consistency; tables with defined relationships |
| **Denormalised** | Query speed for analytics; accept some redundancy |
| **Dimensional** | Fact + dimension tables for fast, business-friendly analytics. **Star**: denormalised dimensions around a fact. **Snowflake**: normalised dimension sub-tables |
| **Data Vault** | Enterprise warehouse: auditability, traceability, long history from many sources. Hubs (business concepts), links (relationships), satellites (descriptive attributes) |

## Processing-focused classification

For engineers writing the applications behind the architecture.

| Class | How data is processed |
|---|---|
| **Batch** | Large batches on a schedule — reports, ML training |
| **Stream** | Process as it arrives — fraud, market-data feeds |
| **Hybrid** | Batch + stream; **Kappa** and **Lambda** named |
| **Medallion** | Lakehouse quality path: raw Bronze → cleaned Silver → curated Gold |

## Business-focused classification

How product and business stakeholders think.

| Class | Priority | Chapter example |
|---|---|---|
| **Operational** | Reliability, performance, security, scale for daily transactions | A **payment** architecture built for high-volume handling plus security and compliance |
| **Analytical** | Store and analyse history; BI, analytics, AI | A warehouse of customer transactions to detect spend patterns and predict churn |

## Classification by data ownership and governance

Top-of-mind for data managers, EAs, and executives: central control vs domain products.

| Class | Ownership | Chapter notes |
|---|---|---|
| **Centralised** | A dedicated central team (classic warehouse or lake). **Data fabric** aims at a central view for discovery, integration, governance — often via **data virtualisation** (query many sources without physically moving data) | — |
| **Decentralised** | Ownership distributed across business domains. **Data mesh**: data as a product, owned by domain teams — aimed at large organisations that cannot scale a single platform | — |

**Architect takeaway:** say which lens you are using in the sentence. “We need a lakehouse” is storage. “We need operational vs analytical paths” is business. “We need a mesh” is ownership. Mixing the words without naming the lens is how a payments book gets redesigned as a Gold table.
