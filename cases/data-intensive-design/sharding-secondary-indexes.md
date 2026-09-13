---
type: analysis
title: 'Sharding and secondary indexes'
description: 'A secondary index does not map to one shard. Local indexes write one shard and scatter-gather on read. Global indexes invert that: one-shard lookup, multi-shard writes, possible staleness.'
tags: [data-intensive-design, sharding, secondary-index, scatter-gather, global-index]
---

# Sharding and secondary indexes

**See also:** [chapter overview](sharding-overview.md) · [secondary indexes](secondary-indexes.md) · [full-text search](multidimensional-search.md#full-text-search) · [replication lag](replication-lag.md) · [tail latency](performance.md#use-of-response-time-metrics) · [distributed transactions](distributed-transactions.md) · [references](sharding-references.md)

The schemes so far assume the client knows the **partition key**.
That is easy in a key-value model: the partition key is the first
part of the primary key (or the whole primary key), so you route
reads and writes to the node for that key.

A [secondary index](secondary-indexes.md) usually does not identify
a record uniquely. It searches for a value: all actions by user 123,
all articles containing *hogwash*, all red cars.

Key-value stores often have no secondary indexes. Relational and
document databases do. Full-text engines (Solr, Elasticsearch) exist
for this. Secondary indexes do not map neatly to shards. Two
approaches: **local** and **global**.

## Local secondary indexes

Each shard maintains its own secondary indexes, covering only the
records it holds. A write (add, remove, update) touches only the
shard that owns the record. That is a **local index**, or in
information retrieval a **document-partitioned index**
([29](sharding-references.md)).

Used-car site: listing ID is the partition key (Figure 7-9) — IDs
0–499 in shard 0, 500–999 in shard 1. Search by color and make needs
secondary indexes on those fields. Add a red car: that shard appends
the ID to the postings list for `color:red` (see
[storage chapter](secondary-indexes.md)).

If the database is only key-value, you might build this mapping in
application code. Then you must keep the index consistent with the
data. Races and partial writes (some changes saved, others not) desync
it quickly — multi-object transactions are a later chapter.

**Read:** if you already know the partition key, search that shard.
If you want *some* results, any shard will do. If you want **all**
matches and do not know the partition key, send the query to **every**
shard and combine — matching records may be anywhere. Red cars sit
in both shard 0 and shard 1 in Figure 7-9.

Scatter/gather makes secondary-index reads expensive. Parallel
queries still suffer
[tail-latency amplification](performance.md#use-of-response-time-metrics).
Adding shards stores more data; it does **not** raise query
throughput if every shard must process every query.

Still widely used ([30](sharding-references.md)): MongoDB, Riak,
Cassandra ([31](sharding-references.md)), Elasticsearch
([32](sharding-references.md)), SolrCloud, VoltDB
([33](sharding-references.md)).

## Global secondary indexes

A **global** index covers data in all shards. It cannot live on one
node — that would bottleneck and undo sharding. The index is itself
sharded, **differently** from the primary-key index.

Figure 7-10: IDs of red cars from all shards sit under `color:red`,
but the index is sharded by color (`a`–`r` on shard 0, `s`–`z` on
shard 1). Make is partitioned similarly (boundary between `f` and
`h`).

Also called **term-partitioned** ([29](sharding-references.md)). In
[full-text search](multidimensional-search.md#full-text-search) a
term is a keyword; here it is any searchable secondary value.

The global index uses the **term** as partition key, so a lookup of
one value hits one shard. That shard may own a contiguous range of
terms or a hash of the term.

Advantage: `color = red` reads one shard’s postings list. Fetching
the actual records still hits every shard that owns those IDs.

Multiple conditions (`color` and `make`, or several words in one
text) likely land on different shards. AND of two postings lists is
fine when the lists are short; long lists are slow to ship across
the network for intersection ([29](sharding-references.md)).

Writes are harder than with local indexes: one record may touch
several index shards (every term may live elsewhere). Keeping the
index in sync may mean a distributed transaction on the primary
record and its index shards (a later chapter).

Used by CockroachDB, TiDB, YugabyteDB. DynamoDB supports both;
global-index writes are **asynchronous**, so reads may be stale
([replication lag](replication-lag.md)). Global indexes still win
when read throughput is higher than write throughput and postings
lists are not too long.

| | Local (document-partitioned) | Global (term-partitioned) |
|---|---|---|
| **Write** | One data shard | Several index shards |
| **Lookup of one term** | All shards | One index shard |
| **Fetch records** | From those shards | Still from the primary shards |
| **Freshness** | Same as the write | May lag if the index is async |

**Architect takeaway:** pick the index grain for the dominant
operation. Write-heavy, partition-key-known → local. Read-heavy,
search-by-attribute → global, and budget either distributed
transactions or staleness.
