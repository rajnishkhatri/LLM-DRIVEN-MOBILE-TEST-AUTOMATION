---
type: analysis
title: 'Snapshot isolation'
description: 'Each transaction reads a consistent point in time. MVCC keeps several row versions so readers never block writers. The SQL name is a mess: repeatable read, serializable, and snapshot are not the same thing.'
tags: [data-intensive-design, transactions, snapshot-isolation, mvcc, repeatable-read]
---

# Snapshot isolation

**See also:** [chapter overview](transactions-overview.md) · [read committed](read-committed.md) · [lost updates](lost-updates.md) · [write skew](write-skew-phantoms.md) · [serializability](serializability.md) · [TrueTime snapshots](unreliable-clocks.md#global-snapshots) · [references](transactions-references.md)

[Read committed](read-committed.md) allows abort, hides incomplete
results, and keeps concurrent writes from interleaving. That is
already more than a store with no transactions.

It is not enough. Figure 8-6: Aaliyah has $1,000 in two accounts
of $500. A transfer moves $100. She reads one account before the
credit and the other after the debit, and sees $900. Both values
were committed when she read them. The anomaly is **read skew**
(a **nonrepeatable read**). Read committed allows it.

*Skew* here is a timing anomaly, not a [hot shard](sharding-hot-spots.md).

A reload a few seconds later usually looks fine. These cases do
not:

| Workload | Why a torn view hurts |
|---|---|
| **Backup** | A multi-hour copy mixes old and new pages. Restore makes the missing $100 permanent. |
| **Analytics / integrity checks** | A scan that sees different times is nonsense ([OLTP vs OLAP](operational-vs-analytical.md)). |

**Snapshot isolation** ([38](transactions-references.md)): each
transaction reads the database as it was at the start of that
transaction. Later commits do not appear in that snapshot.

Popular: PostgreSQL, MySQL/InnoDB, Oracle, SQL Server — details
differ ([30](transactions-references.md),
[42](transactions-references.md), [43](transactions-references.md)).
Oracle, TiDB, and Aurora DSQL stop here as their strongest level.
Warehouses (BigQuery) use it for a point-in-time scan.

## Multiversion concurrency control

Writers still take write locks, so two writers of the same row
block ([read committed](read-committed.md#implementation)). Reads
take **no** locks. **Readers never block writers, and writers
never block readers.** Long read-only queries (backup, analytics)
run beside ordinary writes.

Read committed kept two versions of a row. Snapshot isolation
keeps **several committed versions** — in-flight transactions
started at different times. That is **MVCC**.

PostgreSQL sketch ([42](transactions-references.md),
[44](transactions-references.md), [45](transactions-references.md)):
each transaction gets a monotonic `txid` (32-bit; vacuum handles
wrap). Across shards that counter is a coordination bottleneck;
Spanner uses a clock confidence interval instead
([unreliable clocks](unreliable-clocks.md#global-snapshots)).
Every write is tagged with the writer’s id. A row has
`inserted_by` and `deleted_by` (empty until someone deletes).
Delete is a mark, not a remove. GC frees the row when no snapshot
can still see it. Update = delete + insert
([46](transactions-references.md)). Versions of one row live in
the same heap as a linked list
([47](transactions-references.md), [48](transactions-references.md)).

## Visibility rules

At start, the database lists other in-progress transactions.
Roughly, a reader ignores:

1. Writes by those still-in-progress transactions — even if they
   commit later.
2. Writes by a later `txid` (started after this reader), committed
   or not.
3. Writes by aborted transactions (no need to delete them at once).

A row is visible if the inserter had already committed at snapshot
time, and either nobody marked it deleted, or the deleter had not
yet committed at snapshot time.

A long reader keeps seeing values that everyone else considers
dead. No in-place update — a new version per change — makes that
cheap.

## Indexes

Usual design: the index points at one version (oldest or newest);
the version chain walks to a visible match. GC drops old index
entries with the row. PostgreSQL can skip an index update if both
versions fit on one page ([42](transactions-references.md)). Some
engines store diffs, not full copies.

CouchDB, Datomic, LMDB use **immutable (copy-on-write) B-trees**
([49](transactions-references.md)): a write copies the path to
the root; untouched pages are shared. Each new root *is* a
snapshot. No `txid` filter. Compaction/GC still required.

## Naming

| Product | What it calls this | What it actually is |
|---|---|---|
| PostgreSQL | `repeatable read` | Snapshot isolation |
| Oracle | `serializable` | Snapshot isolation |
| MySQL/InnoDB | `repeatable read` | MVCC weaker than snapshot ([43](transactions-references.md)) |
| IBM Db2 | `repeatable read` | Serializability ([10](transactions-references.md)) |

The SQL standard has no snapshot isolation — it predates the idea
and defines **repeatable read** from System R
([3](transactions-references.md)). PostgreSQL uses that name
because the implementation meets the standard’s letter.

The standard’s isolation definitions are ambiguous
([38](transactions-references.md)). Formal repeatable read
([39](transactions-references.md), [40](transactions-references.md))
is not what most products ship. Nobody really knows what the name
means.

**Architect takeaway:** snapshot isolation is the right tool for
backups and long reads. It is not serializability, even when the
knob says so. Check the product’s actual anomaly table before you
trust a name.
