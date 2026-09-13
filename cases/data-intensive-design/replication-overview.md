---
type: overview
title: 'Replication'
description: 'Keep a copy on several machines. The hard part is change. Three families — single-leader, multi-leader, leaderless — trade consistency, availability, and conflict handling.'
tags: [data-intensive-design, replication, overview]
---

# Replication

> The major difference between a thing that might go wrong and a thing
> that cannot possibly go wrong is that when a thing that cannot
> possibly go wrong goes wrong, it usually turns out to be impossible
> to get at or repair.
>
> — Douglas Adams, *Mostly Harmless* (1992)

**Replication** means keeping a copy of the same data on multiple
machines connected by a network. Reasons to do it, from
[distributed versus single-node](distributed-vs-single-node.md):

- Put data near users and cut access latency.
- Keep serving if some parts fail — availability and
  [durability](reliability.md).
- Scale out the machines that can serve reads.

This chapter assumes each machine holds a **full copy**.
[Sharding](sharding-overview.md) (partitioning) covers datasets that
do not fit on one machine. Later chapters also treat the deeper
fault models of replicated systems.

If the data never changes, copy it once and stop. All the difficulty
is **handling changes**. Three families of algorithms do that. Almost
every distributed database uses one of them.

Prior chapter: [encoding and evolution](encoding-overview.md).

## Topic map

| Topic | The question | Concept |
|---|---|---|
| Single-leader | One writer; sync or async; failover? | [Single-leader replication](single-leader-replication.md) |
| Replication logs | Statements, WAL shipping, or a logical row log? | [Replication logs](replication-logs.md) |
| Lag | Read-your-writes, monotonic reads, consistent prefix? | [Replication lag](replication-lag.md) |
| Multi-leader | Several writers; geo, topologies, sync engines? | [Multi-leader replication](multi-leader-replication.md) |
| Conflicts | Avoid, LWW, merge by hand, CRDT, or OT? | [Conflict resolution](conflict-resolution.md) |
| Leaderless | Quorums, hinted handoff, anti-entropy? | [Leaderless replication](leaderless-replication.md) |
| Concurrency | Happens-before, version vectors, not wall clocks? | [Detecting concurrent writes](detecting-concurrent-writes.md) |

Citations for this chapter live in
[replication references](replication-references.md). Earlier chapters
keep their own lists: [trade-off references](references.md),
[NFR references](nfr-references.md),
[data-model references](data-models-references.md),
[storage references](storage-references.md),
[encoding references](encoding-references.md).

## Why it is still hard

The principles have not changed much since the 1970s
([1](replication-references.md)). Networks have the same constraints.
**Eventual consistency** still causes confusion. The term is
deliberately vague: there is no bound on how far a replica can fall
behind. [Replication lag](replication-lag.md) makes that precise with
read-your-writes, monotonic reads, and consistent prefix reads.

Configuration choices — synchronous versus asynchronous, how to treat
a failed replica — vary by product. The trade-offs do not.

## Summary

Replication is simple to state and hard to operate. It serves
[high availability](reliability.md), durability, disconnected
operation, latency, and [read scalability](scalability.md). At a
minimum you must handle unavailable nodes and network interruptions —
before silent corruption or software bugs.

Three approaches:

| Family | Writes | Reads |
|---|---|---|
| [Single-leader](single-leader-replication.md) | One node (the leader) | Any replica; followers may be stale |
| [Multi-leader](multi-leader-replication.md) | Any of several leaders | Any replica; conflicts are the cost |
| [Leaderless](leaderless-replication.md) | Several nodes in parallel | Several nodes in parallel; repair on read |

Single-leader is popular because it is understandable and can offer
strong consistency. Multi-leader and leaderless tolerate partitions
and latency spikes better, at the cost of
[conflict resolution](conflict-resolution.md) and weaker guarantees.

Synchronous versus asynchronous changes what a confirmed write
*means*. Promote an asynchronous follower after a leader crash and
recently “committed” data may be gone.

**Architect takeaway:** pick the family for the failure you will
actually see. A single leader is a consistency and operations bet. A
second writer is a conflict-resolution bet. Quorums are a
probability-of-staleness bet, not a linearizability proof. Measure
lag; do not pretend async is sync.

Next chapter: [sharding](sharding-overview.md) — key-range vs hash,
hot spots, request routing, and local vs global secondary indexes.
