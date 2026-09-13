---
type: analysis
title: 'Dataflow through databases'
description: 'Writing is encoding; reading is decoding. Data outlives code, so a database holds mixed schema versions. Forward compatibility is required, not optional.'
tags: [data-intensive-design, encoding, databases, schema-evolution]
---

# Dataflow through databases

**See also:** [chapter overview](encoding-overview.md) · [Avro](avro-schema-evolution.md) · [log-structured storage](log-structured-storage.md) · [data warehousing](operational-vs-analytical.md#data-warehousing) · [column compression](columnar-analytics-storage.md#column-compression) · [references](encoding-references.md)

In a database the writer encodes and the reader decodes. A single process
talking to its own store is sending a message to its future self —
**backward compatibility** is mandatory or that future self cannot read
what you wrote.

Usually several processes share the store: different applications, or
several instances of the same service (scale-out or rolling upgrade).
Some run newer code, some older. A value written by new code is then
read by old code that is still up. **Forward compatibility** is required
too.

## Different values written at different times

Any value can be updated at any time. One database holds rows written
five milliseconds ago and rows written five years ago.

A server-side deploy may replace every process in minutes. Database
contents do not: five-year-old bytes stay in the original encoding
until you rewrite them. **Data outlives code.**

Rewriting a large dataset into a new schema is expensive. Most stores
defer it — asynchronous, best-effort. [LSM engines](log-structured-storage.md)
rewrite during compaction using the latest format. Relational databases
often add a nullable column without rewriting rows; a missing on-disk
column becomes null at read time. Schema evolution then makes the
database *appear* encoded with one schema even though disk holds
historical versions.

Harder migrations — single-valued to multi-valued, or moving columns
into another table — still rewrite data, often in application code
([28](encoding-references.md)). Maintaining compatibility across those
migrations is still a research problem ([29](encoding-references.md)).

## Archival storage

Snapshots for backup or for loading a
[warehouse](operational-vs-analytical.md#data-warehousing) are usually
encoded with the **latest** schema, even if the source mixed versions.
You are copying anyway; encode the copy consistently.

A dump written once and then immutable fits Avro object container
files. It is also a good moment to switch to an analytics-friendly
columnar format such as Parquet
([column compression](columnar-analytics-storage.md#column-compression)).

**Architect takeaway:** treat the database as a message queue to your
future (and older) selves. Plan for mixed encodings on disk. Cheap
additive changes (`ADD COLUMN … DEFAULT NULL`) are compatible; shape
changes are migrations, not schema edits.
