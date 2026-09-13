---
type: analysis
title: 'The meaning of ACID'
description: 'Atomicity is abortability. Consistency is the application’s invariants. Isolation is concurrency. Durability is a risk reduction, not a guarantee. Single-object CAS is not a transaction.'
tags: [data-intensive-design, transactions, acid, atomicity, durability]
---

# The meaning of ACID

**See also:** [chapter overview](transactions-overview.md) · [read committed](read-committed.md) · [reliability](reliability.md) · [replication lag](replication-lag.md) · [references](transactions-references.md)

The safety story is usually **ACID**: atomicity, consistency,
isolation, durability (Härder and Reuter, 1983
([9](transactions-references.md))). One vendor’s ACID is not
another’s. Isolation in particular is ambiguous
([10](transactions-references.md)). “ACID compliant” is mostly
marketing.

Systems that miss ACID are sometimes called **BASE** — basically
available, soft state, eventual consistency
([11](transactions-references.md)). That is even vaguer. The only
honest definition is “not ACID.”

## Atomicity

In threads, *atomic* means no other thread sees a half-done
operation. In ACID it is **not** about concurrency — that is
isolation.

ACID atomicity is what happens if several writes are in flight and
a fault hits: crash, network cut, disk full, constraint violation.
The transaction **aborts** and the database discards every write
from that transaction. **Abortability** would have been the better
word.

Without it you do not know which writes landed. Retry risks
duplicates. With it, abort means nothing changed, so retry is safe.

## Consistency

The word is overloaded:

| Sense | Where |
|---|---|
| Replica / eventual consistency | [Replication lag](replication-lag.md) |
| Consistent snapshot (happens-before) | [Detecting concurrent writes](detecting-concurrent-writes.md) |
| Consistent hashing | [Hash sharding](hash-sharding.md#consistent-hashing) |
| CAP “consistency” | Linearizability (a later chapter) |
| ACID consistency | Application invariants |

ACID consistency is “the database is in a good state”: credits
equal debits; a foreign key points at a real row. If the
transaction starts valid and every write preserves the invariant,
the invariant holds at commit (it may be broken *during* the
transaction).

The database enforces only the constraints you declare: foreign
keys, uniqueness, check constraints, sometimes triggers or
[materialized views](query-execution-cubes.md)
([12](transactions-references.md)). Complex invariants often cannot
be declared. Then **C is the application’s job**. Bad writes that
violate an undeclared invariant go through. C is not a property of
the database alone.

## Isolation

Several clients at once. Different keys: fine. Same records: races.

Figure 8-1: two clients increment a counter (read, add one, write).
The counter should go 42 → 44; it goes to 43.

ACID isolation means concurrent transactions do not step on each
other. Textbooks formalize that as
[serializability](serializability.md): the committed result matches
some serial order, even if they ran in parallel
([13](transactions-references.md)).

Serializability costs throughput. Many databases use weaker
isolation. Oracle’s level named “serializable” is
[snapshot isolation](snapshot-isolation.md)
([10](transactions-references.md), [14](transactions-references.md)).
Races remain.

## Durability

After a successful commit, the writes are not forgotten — crash or
hardware fault. On one node that usually means nonvolatile storage
plus `fsync`, plus a [write-ahead log](b-trees.md#making-b-trees-reliable)
for crash recovery, plus checksums so a torn log does not look
committed. On a replica set it may mean “copied to *n* nodes”
before the commit ack ([reliability](reliability.md)).

Nothing is perfect:

- Disk-only: the machine dies and the data is unreachable until
  you move the disk.
- Replicas-only: a correlated fault (power, a crash-on-this-input
  bug) wipes in-memory copies.
- Async replication: recent writes die with the leader
  ([node outages](single-leader-replication.md#handling-node-outages)).
- SSDs have violated their own promises on power cut; `fsync` is
  not always honest ([15](transactions-references.md)). Firmware
  bugs exist — drives that die at 32,768 hours
  ([18](transactions-references.md)). PostgreSQL used `fsync`
  incorrectly for twenty years [19]–[21].
- Engine ↔ filesystem bugs corrupt files after a crash [22]–[23];
  one replica’s filesystem error can spread
  ([24](transactions-references.md)).
- Silent bit rot; backups and replicas may already be bad [25]–[26].
- 30–80% of SSDs grow a bad block in four years
  ([27](transactions-references.md)). Worn SSDs lose data weeks
  after unplug ([28](transactions-references.md)).

Write to disk, replicate, and back up. Treat “guarantees” as risk
reduction.

## Single-object versus multi-object

Atomicity and isolation matter when one client writes several
objects.

**Atomicity:** fault mid-sequence → abort, discard the prefix.
**Isolation:** another transaction sees all of those writes or
none.

The email unread-counter is the running example. Denormalize the
count ([normalization](relational-vs-document.md)). Insert a
message *and* increment the counter. Without isolation, the
mailbox shows unread mail and the counter says zero (Figure 8-2,
a dirty read). Without atomicity, a crash leaves the message
without the increment (Figure 8-3).

Relational databases group statements on one TCP connection
between `BEGIN` and `COMMIT`. Drop the connection, abort. Many
nonrelational stores have a multi-put with **no** transaction
semantics: some keys succeed, some fail.

### Single-object writes

A 20 kB JSON document: half the bytes arrive; power fails mid-
overwrite; another client reads a splice. Storage engines almost
universally give atomicity and isolation **per object on one
node** — a recovery log and a per-object lock.

Atomic increment and **conditional write** (compare-and-set)
remove some [lost-update](lost-updates.md) cycles. They are not
transactions. Aerospike “strong consistency,” Cassandra/ScyllaDB
“lightweight transactions” are linearizable single-object reads
and CAS. No multi-object guarantee.

### When you need several objects

- Relational / graph: foreign keys and edges must stay valid
  while you insert the pair.
- Document: one document is one object. Denormalized copies
  across documents need a multi-object write
  ([which model](relational-vs-document.md)).
- [Secondary indexes](sharding-secondary-indexes.md): the index is
  another object. Without isolation a record can appear in one
  index and not another.

You can build these without transactions. Error handling and
races get much harder.

## Errors and aborts

ACID philosophy: if atomicity, isolation, or durability is at
risk, **abort** rather than leave a half-finished unit.
[Leaderless](leaderless-replication.md) stores are often “best
effort”: do what you can; do not undo. Recovery is the
application’s.

ORMs (ActiveRecord, Django) typically do not retry. The exception
bubbles; user input is gone. That wastes the point of rollback.

Retry is not perfect:

| Case | Risk |
|---|---|
| Commit succeeded; ack lost | Double apply unless you dedupe |
| Overload / contention | Retry feeds the fire — cap, back off, treat overload apart ([metastable failure](reliability.md)) |
| Transient (deadlock, isolation, blip, failover) | Retry |
| Permanent (constraint) | Do not retry |
| Side effect outside the DB (email) | The email may already have gone. Cross-system atomicity is [two-phase commit](distributed-transactions.md) |
| Client dies while retrying | The write is lost |

**Architect takeaway:** A, I, and D are database properties. C is
mostly yours. Single-object atomicity is table stakes, not a
transaction. Design the retry: idempotence for the “commit
succeeded, ack lost” case, and do not retry overload as if it
were a blip.
