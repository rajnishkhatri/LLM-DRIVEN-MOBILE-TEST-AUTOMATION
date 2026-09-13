---
type: analysis
title: 'Leaderless replication'
description: 'Clients write and read several replicas in parallel. Quorums (w + r > n) make staleness unlikely, not impossible. No failover; gray failures hurt less; conflicts remain.'
tags: [data-intensive-design, replication, leaderless, quorum, dynamo]
---

# Leaderless replication

**See also:** [chapter overview](replication-overview.md) · [single-leader](single-leader-replication.md) · [conflict resolution](conflict-resolution.md) · [detecting concurrent writes](detecting-concurrent-writes.md) · [performance](performance.md) · [request routing](request-routing.md) · [ACID aborts](acid.md#errors-and-aborts) · [fencing](quorums-and-fencing.md) · [references](replication-references.md)

[Single-leader](single-leader-replication.md) and
[multi-leader](multi-leader-replication.md) send the write to one
node; that node orders writes; others follow.

**Leaderless** systems drop the leader. Any replica accepts client
writes. Some of the earliest replicated stores were leaderless
([1](replication-references.md), [50](replication-references.md));
the idea faded under relational dominance and returned with Amazon
Dynamo in 2007 ([45](replication-references.md)). Riak, Cassandra,
and ScyllaDB are Dynamo-inspired — **Dynamo-style**.

Amazon’s original Dynamo was never released outside Amazon. Amazon
**DynamoDB** is a different architecture: single-leader Multi-Paxos
([5](replication-references.md), [51](replication-references.md)).

The client may send writes to several replicas, or a coordinator
may do it. The coordinator does **not** impose a write order. That
difference drives everything below.

## Writing while a node is down

Three replicas, one rebooting. Single-leader may need
[failover](single-leader-replication.md#leader-failure-failover).
Leaderless has nothing to fail over (Figure 6-12).

The client writes all three in parallel. Two acknowledge; that is
enough. The down replica misses the write. When it returns, a
single-replica read can be stale.

So reads also go to several nodes. Values carry a version or
timestamp (same idea as
[LWW](conflict-resolution.md#last-write-wins-discarding-concurrent-writes)).
The client keeps the greatest. See
[detecting concurrent writes](detecting-concurrent-writes.md).

### Catching up on missed writes

| Mechanism | What it does | Best for |
|---|---|---|
| **Read repair** | A parallel read sees a stale replica and writes the newer value back | Hot keys |
| **Hinted handoff** | A live replica stores writes for a down peer, then forwards them | Keys that are never read |
| **Anti-entropy** | Background compare-and-copy of missing data; no fixed order; can be slow | Residual drift |

## Using quorums for reading and writing

If every successful write is on at least two of three replicas, at
most one is stale. Read two and at least one is current.

Generally: *n* replicas, write succeeds after *w* confirmations,
read waits for *r* responses. If **w + r > n**, a read should see
an up-to-date value because the read and write sets overlap. Those
are **quorum** reads and writes ([50](replication-references.md)).

*n*, *w*, *r* are typically configurable. Common: odd *n* (3 or 5),
*w* = *r* = (*n* + 1) / 2. A write-rare / read-heavy workload may
set *w* = *n*, *r* = 1 — faster reads, any one failure blocks
writes.

There may be more than *n* nodes in the cluster; a given value
lives on only *n* of them (sharding, a later chapter).

| If | Then |
|---|---|
| *w* < *n* | Writes survive one (or more) down nodes |
| *r* < *n* | Reads survive one (or more) down nodes |
| *n* = 3, *w* = *r* = 2 | Tolerate one down node (Figure 6-12) |
| *n* = 5, *w* = *r* = 3 | Tolerate two (Figure 6-13) |

Requests still go to all *n* in parallel. *w* and *r* are how many
successes you **wait for**. Fewer than *w* or *r* reachable nodes:
error. Why a node failed does not matter.

## Limitations of quorum consistency

*w* + *r* > *n* usually means the latest value is in the read set.
Majorities (*w*, *r* > *n* / 2) guarantee overlap and tolerate
⌊*n* / 2⌋ failures. Quorums need not be majorities — they need
overlap. Other assignments exist ([52](replication-references.md)).

You can set *w* + *r* ≤ *n*. More stale reads; lower latency; more
availability through a partition. The database is unavailable for
writes or reads only after reachable replicas drop below *w* or *r*.

Even with *w* + *r* > *n*, edge cases:

- A node with the new value dies and is restored from an old
  replica: copies of the new value can fall below *w*.
- During rebalancing (a later chapter), nodes disagree on who holds
  the *n* copies; quorums stop overlapping.
- A read concurrent with a write may or may not see it; a later
  read can see the *old* value (linearizability, a later chapter).
- A write that succeeded on some replicas and failed on others,
  totaling fewer than *w*, is not rolled back. A “failed” write
  can still appear on a later read
  ([53](replication-references.md)).
- Wall-clock LWW (Cassandra, ScyllaDB) can drop a later write from
  a slower clock
  ([unreliable clocks](unreliable-clocks.md#timestamps-are-not-an-event-order)).
- Two concurrent writes can land in different orders on different
  replicas — the
  [multi-leader conflict](conflict-resolution.md) again.

Quorums adjust the **probability** of a stale read
([54](replication-references.md)). They are not a proof of “always
the latest value.” Dynamo-style stores are built for apps that can
live with eventual consistency.

## Monitoring staleness

Even if the app tolerates stale reads, operations need to know when
replication is sick.

Leader-based systems expose **replication lag**: same write order
on every node; subtract follower position from leader position.

Leaderless systems have no fixed apply order. Hint count is a weak
health signal ([55](replication-references.md)). “Eventual” is
vague; operability still needs a number.

## Single-leader versus leaderless performance

A single leader can offer consistency leaderless designs struggle
to match. Async followers can still return stale values — see
[replication lag](replication-lag.md).

Reading only the leader is current and:

- Caps read throughput at the leader.
- Pauses writes (and often reads) during
  [failover](single-leader-replication.md#leader-failure-failover).
- Couples user latency to whatever is wrong on that one node.

Leaderless resilience: no failover; requests already fan out; a
slow or dead replica is ignored. Using the fastest responses is
**request hedging** and cuts tail latency
([56](replication-references.md)). The design does not distinguish
“normal” from “failure,” which helps with
**gray failures** — a node that is up but pathologically slow
([57](replication-references.md)) — and with overload during hinted
handoff after a long outage.

Leaderless costs:

- Someone must still detect a down replica, store hints, and
  replay them — extra load when the system is already strained
  ([55](replication-references.md)).
- Larger quorums wait for more of the slowest of *r* or *w*
  parallel replies ([performance](performance.md)). In practice
  quorums stay small (4 of 7, 5 of 9).
- A large partition can make a quorum impossible. Some stores
  accept a write on any reachable replica (**sloppy quorum** in
  Riak/Dynamo ([45](replication-references.md)); consistency level
  `ANY` in Cassandra/ScyllaDB). Later reads may miss it.

[Multi-leader](multi-leader-replication.md) can ride out a
partition with communication to only the local leader. Reads can
then be arbitrarily stale. Quorums sit in between: decent fault
tolerance and a high chance of a current read.

## Multi-region operation

Leaderless also fits multi-region: it already expects conflicts,
blips, and latency spikes.

Cassandra / ScyllaDB: the client picks a local **coordinator**.
That node writes all local replicas and one replica per other
region; those peers fan out. Consistency level chooses a global
quorum, a per-region quorum, or a **local** quorum (no wait on
other regions; more stale).

Riak keeps client–node traffic inside one region (*n* is
per-region). Cross-region replication is async, multi-leader-like.

**Architect takeaway:** *w* + *r* > *n* is an overlap argument, not
linearizability. Use it when you want to keep writing through a
node loss and can tolerate rare stale reads. If you need a single
order of writes, you wanted a leader (or consensus).
