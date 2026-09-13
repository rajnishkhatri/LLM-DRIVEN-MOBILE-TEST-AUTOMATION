---
type: analysis
title: 'Replication lag'
description: 'Async followers scale reads and can lie. Eventual consistency is unbounded. Read-your-writes, monotonic reads, and consistent prefix are the practical guarantees.'
tags: [data-intensive-design, replication, eventual-consistency, session-guarantees]
---

# Replication lag

**See also:** [chapter overview](replication-overview.md) · [single-leader](single-leader-replication.md) · [distributed vs single-node](distributed-vs-single-node.md) · [scalability](scalability.md) · [performance](performance.md) · [references](replication-references.md)

[Single-leader](single-leader-replication.md) is not only for
[faults](reliability.md). It also buys
[read scale](scalability.md) and latency (replicas near users).

Writes still go through one node. Read-only queries can go to any
replica. For read-heavy online services: add followers and spread
reads. That is **read-scaling**. It only works with
**asynchronous** replication. Sync to every follower and one outage
stops all writes; more nodes make that likelier.

An async follower can be stale. The same query on leader and
follower can disagree. Stop writing and wait, and the followers
catch up. That temporary disagreement is **eventual consistency**
([22](replication-references.md)).

The term comes from Terry et al. ([23](replication-references.md))
and was popularized by Vogels ([24](replication-references.md)). It
is not a NoSQL exclusive: async relational followers are the same
thing.

“Eventually” has **no bound**. Lag is often a fraction of a second.
Near capacity or on a bad network it becomes seconds or minutes.
Then the anomalies below are product bugs, not theory.

## Read-your-writes

The user submits data, then views it. The write went to the leader;
the view hit a follower. If the follower is behind, the submit looks
lost (Figure 6-3).

**Read-after-write** (read-your-writes)
([23](replication-references.md)) says: if *this* user reloads, they
see their own updates. Other users may still see older data.

Techniques:

- Read anything the user might have just edited from the leader (or
  a sync follower). A profile page is a clean case: always read
  *your* profile from the leader, everyone else’s from a follower.
- If almost everything is editable, that kills read-scaling. Then:
  send reads to the leader for a minute after the last write
  ([25](replication-references.md)), or skip followers whose lag
  exceeds a threshold.
- The client remembers the last-write timestamp (logical: a log
  sequence number; or a wall clock — then
  [clock sync](unreliable-clocks.md) matters). Serve the read from a replica that has reached
  that timestamp, or wait ([26](replication-references.md)).

Cross-region: any “must hit the leader” request goes to the leader’s
region.

**Cross-device** read-after-write (desktop then phone) is harder:
one device does not know the other’s last timestamp, so that
metadata must be centralized; different devices may land in
different regions.

## Monotonic reads

A user can see time go **backward**. Figure 6-4: first query hits a
fresh follower and sees a new comment; refresh hits a staler
follower and the comment vanishes.

**Monotonic reads** ([22](replication-references.md)) forbid that
for one user’s sequential reads. Weaker than strong consistency;
stronger than unbounded eventual consistency. You may see old data;
you may not see *older* data after newer data.

One implementation: pin each user to one replica (hash of user ID).
If that replica dies, reroute.

## Consistent prefix reads

Causality can invert. Mrs. Cake’s reply replicates faster than
Mr. Poons’s question ([27](replication-references.md)); an observer
hears the answer first (Figure 6-5).

**Consistent prefix reads** ([22](replication-references.md)): if
writes happened in an order, readers see them in that order.

A single log that applies writes in one order cannot break this.
**Sharded** databases (a later chapter) often have no global write
order, so one read can mix old shards and new shards. One fix: put
causally related writes on the same shard. Some algorithms track
causal dependencies explicitly — see
[happens-before](detecting-concurrent-writes.md#the-happens-before-relation-and-concurrency).

## Solutions for replication lag

Ask what the app does if lag is minutes or hours. If the answer is
“fine,” keep async. If users suffer, design a stronger guarantee
instead of pretending the replica is sync.

You can paper over this in application code (leader reads, lag
caps). That code is easy to get wrong. The simplest model for
developers is a database that offers **linearizability** (a later
chapter) and
**[ACID transactions](transactions-overview.md)** and lets you
treat the store as one node.

Early-2010s NoSQL argued those features capped scale. Since then,
distributed databases have offered strong consistency *and* HA /
scale — the **NewSQL** trend (less about SQL, more about scalable
transactions; see
[relational versus document](relational-vs-document.md)).

Weaker replication still has reasons: better behavior under network
cuts, lower overhead than transactional systems. The rest of this
chapter is those designs.

**Architect takeaway:** eventual consistency is a product decision,
not a slogan. Name the session guarantee you owe the user
(read-your-writes, monotonic, prefix). If you cannot name it, you
are shipping stale-read bugs.
