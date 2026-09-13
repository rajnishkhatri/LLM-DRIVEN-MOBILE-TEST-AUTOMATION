---
type: overview
title: 'Sharding'
description: 'Split a dataset that no longer fits on one node. Each record belongs to one shard. Key-range, hash, and how you route, rebalance, and index are the real design.'
tags: [data-intensive-design, sharding, partitioning, overview]
---

# Sharding

> Clearly, we must break away from the sequential and not limit the
> computers. We must state definitions and provide for priorities and
> descriptions of data. We must state relationships, not procedures.
>
> — Grace Murray Hopper, *Management and the Computer of the Future*
> (1962)

A distributed database typically spreads data in two ways:

1. **[Replication](replication-overview.md)** — a copy of the same
   data on several nodes (Chapter 6).
2. **Sharding** (partitioning) — if the data or the write throughput
   no longer fits on one node, split into smaller shards and put
   different shards on different nodes.

Normally each record, row, or document belongs to **exactly one
shard**. Each shard is a small database of its own; some systems
still run operations that touch several shards at once.

Sharding is usually combined with replication, so copies of each
shard live on several nodes. A record still belongs to one shard; it
may still sit on several nodes for fault tolerance.

A node may store more than one shard. Under
[single-leader](single-leader-replication.md) replication, each
shard’s leader is on one node and its followers on others
(Figure 7-1). A node may lead some shards and follow others; each
shard still has one leader. Everything in Chapter 6 about replicating
a database applies to replicating a shard. The sharding scheme is
mostly independent of the replication scheme, so this chapter ignores
replication.

Prior chapter: [replication](replication-overview.md).

## Why shard, and why not

The primary reason is **[scalability](scalability.md)**. Spread data
and writes across nodes when volume or write throughput exceeds one
machine. Read throughput alone does not require sharding — use
[read scaling](replication-overview.md) on replicas.

Sharding is the main tool for **horizontal scaling**
([shared-nothing](scalability.md#shared-memory-shared-disk-and-shared-nothing)):
grow by adding machines, not by buying a bigger one. If each shard
takes a roughly equal share, those shards run in parallel.

Replication is useful at small and large scale. Sharding is
heavyweight and mostly relevant at large scale. If one machine can
hold the data and the writes — and a single machine can do a lot —
prefer a single-shard database.

Sharding adds complexity:

- You choose a **partition key**; all records with that key land in
  the same shard ([4](sharding-references.md)). Knowing the shard
  makes access fast; not knowing it means a search across all shards.
  The scheme is hard to change.
- Key-value data shards easily. Relational data is harder: secondary
  indexes and joins may cross shards
  ([sharding and secondary indexes](sharding-secondary-indexes.md)).
- A write may update related records in several shards.
  Single-node transactions are common;
  **[distributed transactions](distributed-transactions.md)**
  are slower and can bottleneck the whole system.

Some systems shard even on one machine: one single-threaded process
per CPU core, for CPU parallelism or NUMA
([5](sharding-references.md)). Redis, VoltDB, and FoundationDB do
this ([6](sharding-references.md)).

## Topic map

| Topic | The question | Concept |
|---|---|---|
| Multitenancy | One tenant per shard, or many small tenants together? | [Sharding for multitenancy](sharding-multitenancy.md) |
| Key range | Contiguous keys, range scans, split when hot? | [Key-range sharding](key-range-sharding.md) |
| Hash | Hash then map; mod *N*, fixed shards, hash range, consistent hashing? | [Hash sharding](hash-sharding.md) |
| Hot spots | Celebrity keys, random suffixes, heat management? | [Hot spots](sharding-hot-spots.md) |
| Rebalancing | Automatic split/move, or a human in the loop? | [Rebalancing](rebalancing.md) |
| Routing | Any node, a routing tier, or a sharding-aware client? | [Request routing](request-routing.md) |
| Secondary indexes | Local (scatter/gather) or global (term-partitioned)? | [Sharding and secondary indexes](sharding-secondary-indexes.md) |

Citations for this chapter live in
[sharding references](sharding-references.md). Earlier chapters keep
their own lists: [trade-off references](references.md),
[NFR references](nfr-references.md),
[data-model references](data-models-references.md),
[storage references](storage-references.md),
[encoding references](encoding-references.md),
[replication references](replication-references.md).

## Summary

Sharding is necessary when storing and processing on one machine is
no longer feasible. The goal is to spread data and query load evenly
and avoid **hot spots**. That requires a scheme that fits the data,
and rebalancing when nodes are added or removed.

Two main approaches:

| Family | Order | Rebalance |
|---|---|---|
| [Key range](key-range-sharding.md) | Keys sorted; a shard owns min–max. Range queries are cheap; nearby keys can hot-spot. | Split a range into subranges when a shard grows. |
| [Hash](hash-sharding.md) | Hash the key; a shard owns a hash range (or consistent hashing maps hashes to shards). Destroys key order. | Often a fixed number of shards, several per node, move whole shards. Splitting is also possible. |

A common compromise: the first part of the key is the partition key;
records with the same partition key stay together and sort on the
rest, so range queries *inside* a partition key stay cheap.

[Request routing](request-routing.md) finds the node for a key.
A coordination service often holds the shard-to-node map.

[Secondary indexes](sharding-secondary-indexes.md) must be sharded
too:

| Index | Write | Read of the postings list |
|---|---|---|
| **Local** | One shard | All shards (scatter/gather) |
| **Global** | Several index shards | One shard (fetching records may still hit many) |

Every shard operates mostly independently — that is how a sharded
database scales. Operations that write several shards are the next
problem: what if one shard succeeds and another fails? That is
[transactions](transactions-overview.md).

**Architect takeaway:** shard only when one node cannot hold the
writes or the data. The partition key is an irreversible-looking
choice. Key range buys scans and risks hot sequential writes. Hash
buys evenness and kills range queries. Local indexes make writes
cheap and reads scatter; global indexes invert that. Put a human in
the rebalance loop if automation plus false failure detection can
cascade.

Next chapter: [transactions](transactions-overview.md) — ACID,
isolation levels, write skew, serializability, and two-phase
commit.
