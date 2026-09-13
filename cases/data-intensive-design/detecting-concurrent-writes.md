---
type: analysis
title: 'Detecting concurrent writes'
description: 'Two writes are concurrent when neither happens-before the other. Version numbers on one replica, version vectors on many. A wall clock is not a causality test.'
tags: [data-intensive-design, replication, causality, version-vector, happens-before]
---

# Detecting concurrent writes

**See also:** [chapter overview](replication-overview.md) · [leaderless](leaderless-replication.md) · [conflict resolution](conflict-resolution.md) · [multi-leader topologies](multi-leader-replication.md#topologies) · [lost updates](lost-updates.md) · [unreliable clocks](unreliable-clocks.md) · [references](replication-references.md)

[Leaderless](leaderless-replication.md) stores, like
[multi-leader](multi-leader-replication.md), allow concurrent
writes to one key. The conflict may appear at write time, or later
during read repair, hinted handoff, or anti-entropy.

Events arrive in different orders at different nodes. Figure 6-14:
clients A and B write key *X* on three nodes.

- Node 1 sees only A.
- Node 2 sees A then B.
- Node 3 sees B then A.

If each node overwrites on every write, the replicas **diverge for
good**. Eventual consistency requires a merge: LWW (Cassandra,
ScyllaDB), siblings + manual resolve, or CRDTs (Riak) — see
[conflict resolution](conflict-resolution.md).

LWW is easy and does not tell you *whether* two values conflict or
one superseded the other. Explicit resolution needs a concurrency
test.

## The happens-before relation and concurrency

Figure 6-8: A’s insert happens before B’s increment because B
incremented the value A inserted — B is **causally dependent** on
A. Figure 6-14: neither client knew the other was writing — no
causal edge.

Operation *A* **happens before** *B* if *B* knows about *A*,
depends on *A*, or builds on *A*. Two operations are **concurrent**
if neither happens before the other ([58](replication-references.md)).

For any pair: *A* before *B*, *B* before *A*, or concurrent. If one
happened before the other, the later overwrites. If concurrent,
resolve a conflict.

## Capturing happens-before (one replica)

Start with one replica; then generalize.

1. The server keeps a **version number** per key, increments it on
   every write, and stores it with the value.
2. A client **must read before write**. The read returns all
   siblings not yet overwritten, plus the latest version.
3. The write includes that version and a merge of the siblings
   just read (CRDT, or user input). The write response returns
   current siblings so the client can chain writes (the shopping
   cart).
4. On a write with version *v*, the server may overwrite values
   at version ≤ *v* (they were merged in). It must **keep** values
   with a higher version — those are concurrent with the incoming
   write.

The server compares version numbers. It never inspects the value.

A write with **no** version number is concurrent with everything:
it overwrites nothing and becomes another sibling. Figure 6-15
walks two clients adding cart items:

1. Client 1 adds milk → version 1.
2. Client 2 adds eggs, unaware of milk → version 2; siblings
   `{eggs}`, `{milk}`.
3. Client 1 adds flour from version 1 → `[milk, flour]` overwrites
   milk, stays concurrent with eggs → version 3.
4. Client 2 adds ham from version 2, merging what it last saw →
   `[eggs, milk, ham]` overwrites eggs, concurrent with
   `[milk, flour]` → version 4.
5. Client 1 adds bacon from version 3 → merges to
   `[milk, flour, eggs, bacon]`, concurrent with
   `[eggs, milk, ham]`.

Old versions get overwritten; no write is dropped. Figure 6-16 is
the causal graph: arrows are happens-before.

## Version vectors

One version number is not enough when several replicas accept
writes. You need a version number **per replica and per key**. Each
replica increments its own number on a write and remembers the
numbers it has seen from the others. That collection is a
**version vector** ([59](replication-references.md)).

Variants exist; the interesting one is the **dotted version
vector** ([60](replication-references.md),
[61](replication-references.md)), used in Riak 2.0
([62](replication-references.md), [63](replication-references.md)).
The cart example is the same idea with more counters.

Replicas send the vector to the client on read; the client sends it
back on write (Riak: a string called **causal context**). The
vector distinguishes overwrite from concurrent write.

It is safe to read from one replica and write to another. You may
create siblings; you do not lose data if you merge them.

## Version vectors and vector clocks

People say **vector clock** for version vector. They are not the
same; the difference is subtle
([61](replication-references.md), [64](replication-references.md),
[65](replication-references.md)). When comparing *replica state*,
use version vectors.

**Architect takeaway:** concurrency is a causal fact, not a
timestamp. If you cannot carry a version vector (or equivalent)
from read to write, you cannot tell overwrite from conflict, and
LWW will delete someone’s work at random.
