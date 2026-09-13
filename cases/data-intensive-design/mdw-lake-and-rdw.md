---
type: analysis
title: 'Lake and RDW roles in an MDW'
description: 'The lake stages, refines, streams, and sandboxes. The RDW serves, secures, and hosts dashboards. Power users on files; business users on a metadata layer.'
tags: [data-intensive-design, mdw, data-lake, data-warehouse, self-service-bi, elt]
---

# Lake and RDW roles in an MDW

**See also:** [chapter overview](mdw-overview.md) · [data journey](mdw-data-journey.md) · [trade-offs](mdw-tradeoffs.md) · [data fabric extras](data-fabric-components.md) · [Medallion](medallion-overview.md) · [Fabric foundation](medallion-foundation-overview.md) · [OLTP vs OLAP](operational-vs-analytical.md) · [columnar storage](columnar-analytics-storage.md) · [cloud native](cloud-vs-self-hosting.md#cloud-native-system-architecture)

In the hybrid, function is split on purpose. The lake is for
**staging and preparing**. The RDW is for **serving, security, and
compliance**. Mixing those jobs is how the architecture collapses
back into one overloaded store.

## Data lake

Access is for data scientists and other power users. Folder/file
layout plus metadata that does not travel with the file makes the
lake hard to wander. The tools are heavier.

What lives here:

- **Batch transform** and **stream landing** — the lake is the
  buffer for both
  ([event-driven dataflow](event-driven-dataflow.md))
- **Refine and clean**, with compute sized to the job and a choice
  of engines ([disaggregated compute](mdw-data-journey.md#3-transformation))
- **ELT** — load files first, shape them with lake compute
- **Age-out and backup** — older slices, and a backup of the
  warehouse itself, cheaper than keeping history hot in the RDW
- **Sandboxes** — copies you can break without touching serving
- **Exploration** — [schema-on-read](operational-vs-analytical.md#from-data-warehouse-to-data-lake)
  so you can judge a dataset before paying the warehouse load
- **Quick reports** when the question is “is this worth promoting?”

The lake is where you go when you do **not** yet know the question.
That is the opposite of the RDW default.

## Relational data warehouse

Access is for people who already speak relational databases.
Latency is the point: MPP (when you need it) makes ad-hoc joins
and interactive tuning cheap enough to repeat. Concurrent
dashboard users are a warehouse workload; they are not a lake
workload.

What lives here:

- **Low-latency SQL**, including many-way joins
- **Interactive ad-hoc** — change the query, wait milliseconds to
  seconds, not a job
- **Concurrency** — many report users at once
- **Row- and column-level security** as first-class warehouse
  features
- **Tooling density** — decades of BI clients; the lake still
  trails
- **Dashboards** — millisecond refresh is an RDW claim; do not
  put the executive tile on a file scan
- **Forced metadata** above the tables — more up-front work,
  much easier self-service

You build the RDW when you **already know** the questions. The
model is the product.

## Who sits where

| Audience | Default store | Why |
|---|---|---|
| Data scientist / power user | Lake (raw → presentation, or sandbox) | Files, engines, experiments |
| Business analyst / self-service BI | RDW | Metadata, joins already done, security model |
| Dashboard consumer | RDW | Latency and concurrency |
| Streaming / ML feature work | Lake, sometimes RDW extract | Variety and compute choice |

**Architect takeaway:** keep prepare and serve on opposite sides
of the copy. If the lake is asked to host the dashboard, or the
RDW is asked to clean raw files, you have paid for a hybrid and
are running a single overloaded store.
