---
type: overview
title: 'Storage and retrieval'
description: 'OLTP engines are log-structured or update-in-place; analytics engines are columnar. Pick the engine for the access pattern, not the brand.'
tags: [data-intensive-design, storage, overview]
---

# Storage and retrieval

> One of the miseries of life is that everybody names things a little bit
> wrong. And so it makes everything a little harder to understand in the
> world than it would be if it were named differently. A computer does not
> primarily compute in the sense of doing arithmetic. […] They primarily
> are filing systems.
>
> — Richard Feynman, *Idiosyncratic Thinking* seminar (1985)

On the most fundamental level, a database needs to do two things: when you
give it some data, it should store the data, and when you ask it again
later, it should give the data back to you.

[Data models and query languages](data-models-overview.md) are the format
in which you give the database your data, and the interface through which
you ask for it again. This chapter is the same problem from the database’s
point of view: how it stores what you give it, and how it finds the data
when you ask.

You are probably not going to implement a storage engine from scratch. You
do need to **select** one that fits the workload, and to configure it you
need a rough idea of what it is doing under the hood. The big split is the
same as [OLTP versus OLAP](operational-vs-analytical.md): engines optimized
for transactional point queries look very different from engines optimized
for analytics scans.

Prior chapter: [data models and query languages](data-models-overview.md).

## Topic map

| Topic | The question | Concept |
|---|---|---|
| Log-structured / LSM | Append immutable files, compact later? | [Log-structured storage](log-structured-storage.md) |
| B-trees | Overwrite fixed-size pages in place? | [B-trees](b-trees.md) |
| LSM vs B-tree | Writes, reads, amplification, disk space | [Comparing LSM-trees and B-trees](lsm-vs-btree.md) |
| Secondary indexes | Search by something other than the primary key | [Secondary indexes and in-memory stores](secondary-indexes.md) |
| Columnar analytics | Scan few columns over many rows | [Column-oriented storage for analytics](columnar-analytics-storage.md) |
| Query CPU and cubes | Compilation, vectorization, precomputed aggregates | [Query execution and data cubes](query-execution-cubes.md) |
| Multi-condition search | Two ranges, keywords, or semantic similarity | [Multidimensional, full-text, and vector indexes](multidimensional-search.md) |

Citations for this chapter live in
[storage references](storage-references.md). Earlier chapters keep their
own lists: [trade-off references](references.md),
[NFR references](nfr-references.md),
[data-model references](data-models-references.md).

## Summary

OLTP systems are optimized for a high volume of requests, each of which
reads and writes a small number of records and needs a fast response.
Records are typically reached via a primary key or a
[secondary index](secondary-indexes.md). Those indexes are ordered
key-to-record maps and also support range queries.

Two schools of thought for OLTP:

- The **log-structured** approach appends files and deletes obsolete ones
  but never updates a file that has been written. High write throughput.
  SSTables, LSM-trees, RocksDB, Cassandra, HBase, ScyllaDB, Lucene.
- The **update-in-place** approach treats the disk as fixed-size pages that
  can be overwritten. B-trees are the standard in almost every relational
  OLTP database. As a rule of thumb they are better for reads.

Data warehouses are optimized for complex read queries that scan many
records. They use a [column-oriented layout](columnar-analytics-storage.md)
with compression so a query reads less off disk, and
[JIT compilation or vectorization](query-execution-cubes.md) so less CPU
is spent per row.

Indexes that search several conditions at once:
[R-trees](multidimensional-search.md#multidimensional-indexes) for points
on a map, inverted indexes for keywords in the same text, and
[vector indexes](multidimensional-search.md#vector-embeddings) for
semantic similarity.

**Architect takeaway:** choose the storage engine for the access pattern.
Write-heavy OLTP leans LSM; read-heavy point/range OLTP leans B-tree;
analytics leans columnar. Tuning knobs only make sense once you can picture
what a higher or lower value does to I/O.

Next chapter: [encoding and evolution](encoding-overview.md) — backward
and forward compatibility, schema-driven encodings, and the four
dataflow modes.
