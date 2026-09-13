---
type: analysis
title: 'Conflict resolution'
description: 'Concurrent writes on two leaders are not a clock problem. Avoid them, discard with LWW, keep siblings, or merge with CRDTs or operational transformation.'
tags: [data-intensive-design, replication, crdt, operational-transformation, lww]
---

# Conflict resolution

**See also:** [chapter overview](replication-overview.md) · [multi-leader](multi-leader-replication.md) · [leaderless](leaderless-replication.md) · [detecting concurrent writes](detecting-concurrent-writes.md) · [unreliable clocks](unreliable-clocks.md) · [references](replication-references.md)

The largest cost of [multi-leader](multi-leader-replication.md) —
geo-replicated servers *or* a local-first sync engine — is
**concurrent writes** that must be resolved.

Figure 6-9: two users edit a wiki title, A→B and A→C, each on their
own leader. After async replication, a conflict. Single-leader
cannot do this.

Two writes are concurrent when **neither was aware of the other**
when it was made. Wall-clock overlap does not matter; offline
writes hours apart can still be concurrent. Detection is
[detecting concurrent writes](detecting-concurrent-writes.md).
Assume we can detect; the question is how to resolve.

## Conflict avoidance

Route all writes for a record through one leader. The database is
multi-leader; that record is not. Impossible for an offline sync
client; sometimes possible in geo-replicated servers
([30](replication-references.md)).

Example: a user edits only their own data. Pin them to a home
region. From that user’s point of view the system is single-leader.

Changing the designated leader (region down, user moved) reopens
the race: a write in flight during the move is a conflict again.

IDs: two leaders, one issues odd autoincrement values, the other
even. Other ID schemes are a later chapter (logical clocks).

## Last write wins (discarding concurrent writes)

Attach a timestamp; keep the greatest. Ties: compare values (for
strings, earlier in the alphabet). Called **last write wins (LWW)**.
The name lies: for concurrent writes there is no “last,” so the
winner is essentially random.

Real meaning: one concurrent write is kept, the others are
**silently discarded** even though their leaders accepted them.
Replicas converge; updates are lost.

LWW is fine if you only insert unique keys and never update. If you
update, or two leaders insert the same key, decide whether lost
updates are acceptable.

Wall-clock LWW is also clock-sensitive. A node whose clock is ahead
can make later overwrites look older
([unreliable clocks](unreliable-clocks.md#timestamps-are-not-an-event-order)).
Logical clocks (a later chapter) fix the *order* without trusting
NTP.

## Manual conflict resolution

Git-style: stop and merge. A database cannot halt replication for a
human. Typical pattern: store all concurrent values as **siblings**.
The next read returns the set; the app (or the user) writes back
one resolved value. CouchDB does this.

Costs:

- The API changes: a string field becomes a set of strings.
- Asking the user is expensive to build and confusing to use.
- Naive auto-merge surprises. Amazon’s cart took the union of
  siblings; a delete on one device reappeared if another sibling
  still held the item (Figure 6-10,
  [45](replication-references.md)).
- Two nodes can resolve the same conflict differently (`B/C` vs
  `C/B`) and create a *new* conflict.

## Automatic conflict resolution

An algorithm merges concurrent writes so every replica that has
seen the same set of writes ends in the **same state**, regardless
of arrival order. Eventual consistency plus that convergence is
**strong eventual consistency** ([46](replication-references.md)).

LWW is the simplest such algorithm. Richer merges try to keep the
*intent* of every update:

| Data | Merge idea |
|---|---|
| Text | Preserve all inserts and deletes; order concurrent inserts at the same position deterministically |
| Collection | Track inserts *and* deletes so a removed cart item stays gone |
| Counter | Add increments and decrements from each sibling; no double-count, no drop |
| Map | Merge per key with one of the other algorithms |

Limits: “at most five items” plus concurrent adds has no merge
except dropping items. Still enough for many collaborative apps.
If the product *is* offline-first, merge is not optional.

## Conflict-free replicated datatypes and operational transformation

Two families: **CRDTs** ([46](replication-references.md)) and
**operational transformation (OT)**
([47](replication-references.md)). Different philosophy and
performance; both merge text, lists, maps, counters.

Figure 6-11: both replicas start at `ice`. One prepends `n`
(`nice`); the other appends `!` (`ice!`). Both want `nice!`.

**OT** records indexes: insert `n` at 0, `!` at 3. After applying
`n`, index 3 would produce `nic!e`. Transform the `!` to index 4.

**CRDT** gives each character an immutable ID. Insert `!` after
character `3A`, not “at index 3.” Concurrent inserts at the same
spot order by ID. No transform step.

Lists work the same way with elements instead of characters. Hybrid
algorithms exist ([48](replication-references.md)).

OT dominates real-time text (Google Docs
([32](replication-references.md))). CRDTs appear in Redis
Enterprise, Riak, Azure Cosmos DB
([49](replication-references.md)). JSON sync engines: CRDT
(Automerge, Yjs) or OT (ShareDB).

## Types of conflict

Two writes to the same field are obvious. Others are not. A meeting
room: insert a booking row; the invariant is “no overlapping
bookings.” Two clients can both see the room free and both insert.
There is no one-line fix.
[Write skew](write-skew-phantoms.md) and
[serializability](serializability.md) return to this; so does
later material on detecting conflicts at scale.

**Architect takeaway:** LWW is convergence by deletion. Siblings
push the merge into the app. CRDT/OT are the merge *in the
datatype*. If you cannot state which of those you are running, you
do not have a multi-writer design.
