---
type: analysis
title: 'Preventing lost updates'
description: 'Read-modify-write loses the earlier write. Atomic SQL, SELECT FOR UPDATE, automatic detection under some snapshots, or CAS. LWW in a replica set is a lost update by policy.'
tags: [data-intensive-design, transactions, lost-update, compare-and-set, optimistic-locking]
---

# Preventing lost updates

**See also:** [chapter overview](transactions-overview.md) · [read committed](read-committed.md) · [snapshot isolation](snapshot-isolation.md) · [conflict resolution](conflict-resolution.md) · [references](transactions-references.md)

[Read committed](read-committed.md) and
[snapshot isolation](snapshot-isolation.md) are mostly about what
a reader may see. Concurrent writers have more than dirty writes.

The classic is the **lost update** (Figure 8-1): read, modify,
write. Two transactions do it; the second write does not include
the first modification. It **clobbers**. Common shapes
([50](transactions-references.md)):

- Counter or balance (read, add, write).
- Local edit to a JSON document (parse, patch, write back).
- Two wiki editors, each saving the whole page.

## Atomic write operations

Best when the change fits one statement:

```sql
UPDATE counters SET value = value + 1 WHERE key = 'foo';
```

MongoDB has atomic local JSON ops; Redis has atomic structure
ops. Arbitrary wiki text does not fit — that is
[CRDT / OT](conflict-resolution.md).

Implementation: exclusive lock from read through write, or a
single thread for those ops.

ORMs make it easy to emit an unsafe read-modify-write instead
[51]–[53]. Tests rarely catch it.

## Explicit locking

If the database has no matching atomic op — game rules that
cannot be a single query — lock, then read-modify-write:

```sql
BEGIN TRANSACTION;
SELECT * FROM figures
  WHERE name = 'robot' AND game_id = 222
  FOR UPDATE;
-- validate the move, then:
UPDATE figures SET position = 'c4' WHERE id = 1234;
COMMIT;
```

`FOR UPDATE` locks the returned rows. Forget a lock, get a race.
Lock several objects, risk **deadlock**; most databases abort one
transaction. Retry that one.

This still does not stop two *different* figures moving onto the
same square — that is [write skew](write-skew-phantoms.md).

## Automatic detection

Allow the cycles in parallel; abort if the manager sees a lost
update. Cheap to combine with snapshot isolation.

PostgreSQL `repeatable read`, Oracle `serializable`, SQL Server
`snapshot` do this. MySQL/InnoDB `repeatable read` does **not**
([30](transactions-references.md), [43](transactions-references.md)).
Some authors require lost-update prevention to call the level
snapshot isolation ([38](transactions-references.md),
[40](transactions-references.md)); by that definition MySQL does
not provide it.

You cannot forget a lock you never had to take. You still must
retry aborts.

## Conditional writes (compare-and-set)

Stores without transactions often offer “write if unchanged since
I read” — CPU CAS by another name (also
[single-object writes](acid.md#single-object-writes)).

```sql
UPDATE wiki_pages SET content = 'new content'
  WHERE id = 1234 AND content = 'old content';
```

If `content` moved, zero rows; retry. A version column you
increment is the same idea (**optimistic locking**
([54](transactions-references.md))).

Under MVCC the new content may be invisible to the snapshot.
Many engines special-case `UPDATE`/`DELETE` `WHERE` so concurrent
writes are visible there even when the snapshot would hide them.

## Replication

Locks and CAS assume **one** current copy.
[Multi-leader](multi-leader-replication.md) and
[leaderless](leaderless-replication.md) accept concurrent writes
and replicate later. There is no single current copy.
Linearizability (a later chapter) is the name of that assumption.

The usual path is **siblings** plus a merge
([conflict resolution](conflict-resolution.md)). Commutative
updates (increment, set-add) merge cleanly — the CRDT bet.
CAS is not commutative.

**Last write wins** is a lost update by policy.

**Architect takeaway:** if the update is one SQL expression, use
it — do not let the ORM hide a read-modify-write. If the product
detects lost updates at your isolation level, prefer that to
hand-placed locks. If you are multi-writer-async, you do not
have lost-update prevention; you have a merge problem.
