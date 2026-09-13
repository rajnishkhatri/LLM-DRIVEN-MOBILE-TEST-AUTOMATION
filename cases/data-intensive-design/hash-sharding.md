---
type: analysis
title: 'Hash sharding'
description: 'Hash the partition key, then map to a shard. Mod N reshuffles almost everything. Fixed shards move whole shards. Hash ranges and consistent hashing adapt with less churn.'
tags: [data-intensive-design, sharding, consistent-hashing, hash-range, rebalancing]
---

# Hash sharding

**See also:** [chapter overview](sharding-overview.md) · [key-range sharding](key-range-sharding.md) · [hot spots](sharding-hot-spots.md) · [rebalancing](rebalancing.md) · [references](sharding-references.md)

[Key-range sharding](key-range-sharding.md) groups nearby partition
keys. If you do not care about that — tenant IDs in a
[multitenant](sharding-multitenancy.md) app — hash the partition key
first, then map the hash to a shard.

A good hash takes skewed input and makes it uniform. A 32-bit hash
of a string returns a number in `0 … 2³² − 1`. Similar strings still
spread evenly; the same input always hashes the same.

The hash need not be cryptographic. MongoDB uses MD5; Cassandra and
ScyllaDB use Murmur3. Language `hashCode` / `Object#hash` may differ
across processes — unsuitable for sharding
([16](sharding-references.md)).

## Hash modulo number of nodes

First thought: `hash(key) % N` with *N* nodes. Easy. When *N*
changes, **most keys move** (Figure 7-3). Three nodes, add a fourth:
keys that lived on node 0 at hashes 0, 3, 6, 9 scatter to other
nodes. Too much unnecessary movement.

## Fixed number of shards

Create many more shards than nodes and assign several shards per
node. Ten nodes, 1,000 shards → 100 shards each. Key goes to
`hash(key) % 1,000`. A separate map says which shard sits on which
node.

Add a node: reassign some whole shards until the map is fair again
(Figure 7-4). Remove a node: reverse. Only entire shards move —
cheaper than splitting. The key-to-shard map does not change. During
the transfer, reads and writes still use the old assignment.

Pick a shard count with many factors so the dataset splits evenly
across various node counts — not only powers of two
([4](sharding-references.md)). Stronger hardware can take more
shards.

Used by Citus (PostgreSQL), Riak, Elasticsearch, Couchbase. Works if
you guessed the shard count well at create time. You cannot have more
nodes than shards.

Guess wrong — more nodes than shards — and you need an expensive
**reshard**: split every shard, rewrite files, extra disk. Some
systems forbid resharding while writes continue, so the change needs
downtime.

Variable dataset size makes the guess hard. Each shard is a fixed
fraction of the total, so shard size grows with the cluster. Huge
shards make rebalance and recovery expensive; tiny shards waste
overhead. “Just right” is hard when the count is fixed and the data
is not.

## Sharding by hash range

If you cannot predict shard count, let the number of shards adapt.
Key-range already does that, but nearby keys can
[hot-spot](sharding-hot-spots.md). Combine: each shard owns a
**range of hash values**, not a range of keys (Figure 7-5). Even
consecutive timestamps hash uniformly. Split a shard when it is too
big or too hot — still expensive, but on demand.

Cost versus key-range: range queries on the partition key scatter
across shards. If the key has several columns and only the first is
the partition key, range queries on the later columns stay in one
shard — all records in that query share the partition key.

YugabyteDB and DynamoDB ([17](sharding-references.md)) use
hash-range; it is an option in MongoDB. Cassandra and ScyllaDB use a
variant (Figure 7-6): split the hash space into contiguous ranges
with **random** boundaries, several ranges per node (Cassandra
default 16, ScyllaDB 256). Some ranges are bigger; many ranges per
node even that out ([15](sharding-references.md)). Add or remove a
node: adjust boundaries, split or merge. The new node takes an
approximately fair share without moving more data than needed.

## Consistent hashing

A **consistent hashing** algorithm maps keys to a given number of
shards with two properties:

1. Roughly equal keys per shard.
2. When the shard count changes, as few keys as possible move.

*Consistent* here is not replica consistency or ACID consistency. It
means a key tends to stay put.

Cassandra and ScyllaDB are close to the original definition
([18](sharding-references.md)). Other algorithms:
**highest random weight** / rendezvous hashing
([20](sharding-references.md)), **jump consistent hashing**
([21](sharding-references.md)) ([19](sharding-references.md)).
Those assign the new node individual keys previously scattered
across all others, instead of splitting a few existing shards.
Which is better depends on the application.

Uniform keys still do not imply uniform **load**. See
[hot spots](sharding-hot-spots.md).

**Architect takeaway:** never `hash % N` in a cluster that will
grow. Fixed shards are operationally simple until the guess is
wrong. Hash-range and consistent hashing buy elasticity; you pay
with lost partition-key range scans.
