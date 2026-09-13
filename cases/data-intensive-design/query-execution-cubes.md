---
type: analysis
title: 'Query execution and data cubes'
description: 'Compilation and vectorization spend less CPU per row. Materialized views and data cubes precompute aggregates at the cost of write work and flexibility.'
tags: [data-intensive-design, storage, vectorization, jit, materialized-view, olap-cube]
---

# Query execution and data cubes

**See also:** [chapter overview](storage-overview.md) · [columnar storage](columnar-analytics-storage.md) · [home timelines](home-timeline-case-study.md#materializing-and-updating-timelines) · [event sourcing](event-sourcing-cqrs.md) · [references](storage-references.md)

A complex analytical SQL query becomes a plan of **operators**, often
distributed across machines. Planners choose which operators, in what
order, and where they run.

Inside an operator the engine compares or calculates column values —
membership in a set, greater-than, several columns of the same row
(“bananas in this store”). For scans of millions of rows, disk I/O is
not the only cost: **CPU time per operator** matters. Interpreting the
query row by row — looking up which comparison to run on which column
— is too slow. Two alternatives
([77](storage-references.md)):

## Query compilation

Generate code for the SQL: iterate rows, test the columns of interest,
copy matches to an output buffer. Compile that (often via LLVM) and
run it on column-encoded data already in memory. Same idea as JVM
JIT.

## Vectorized processing

Still interpreted, but **batches of column values** instead of one
row at a time. A fixed set of operators takes arguments and returns a
batch ([50](storage-references.md), [73](storage-references.md)).

Example: pass the `product_sk` column and the “bananas” ID to an
equality operator → a bitmap (1 if that row matches). Same for
`store_sk` and the store of interest. Bitwise AND the two bitmaps →
sales of bananas in that store.

The implementations differ; both are used
([77](storage-references.md)). Both exploit modern CPUs:

- Sequential memory access over random, to cut cache misses
  ([78](storage-references.md))
- Tight inner loops (few instructions, no function calls) to keep the
  pipeline busy and avoid branch mispredicts
- Threads and SIMD ([79](storage-references.md),
  [80](storage-references.md))
- Operate on **compressed** data without decoding into a separate
  in-memory representation

“Vector” here means a batch of values. That is not the same as a
[vector embedding](multidimensional-search.md#vector-embeddings)
(an array of floats locating a document in semantic space).

## Materialized views and data cubes

A **materialized view** is a table-like object whose contents are the
result of a query — an actual copy on disk. A **virtual view** is only
a query shortcut: reading it expands into the underlying SQL.

We met materialization in
[home timelines](home-timeline-case-study.md#materializing-and-updating-timelines)
and again as derived read models in
[event sourcing / CQRS](event-sourcing-cqrs.md). When the underlying
data changes, the copy must be updated. Some databases do that
automatically; Materialize specializes in it
([81](storage-references.md)). More write work; faster repeated reads.

**Materialized aggregates** cache `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`
that many warehouse queries share. A **data cube** (OLAP cube) is a
grid of those aggregates grouped by dimension
([82](storage-references.md)).

Two dimensions (`date_key`, `product_sk`): a table with dates on one
axis and products on the other; each cell is `SUM(net_price)` for that
pair. Aggregate along a row or column and you drop a dimension (sales
by product regardless of date, or by date regardless of product).

Facts often have more than two dimensions (date, product, store,
promotion, customer in the
[star schema](star-snowflake-analytics.md)). A five-dimensional
hypercube is hard to picture; the rule is the same: each cell is one
combination, then summarize along each axis.

**Advantage:** some queries become a lookup — yesterday’s sales per
store is already on that dimension, no scan of millions of rows.

**Disadvantage:** less flexible than raw data. You cannot ask what
share of sales came from items over $100 if price is not a dimension.
Warehouses therefore keep as much raw data as they can and use cubes
only as a boost for known queries.
