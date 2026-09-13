---
type: analysis
title: 'Read committed'
description: 'No dirty reads, no dirty writes. The common default. Row locks stop dirty writes; two versions of a row stop dirty reads without blocking readers. Lost updates and read skew remain.'
tags: [data-intensive-design, transactions, isolation, read-committed, dirty-read]
---

# Read committed

**See also:** [chapter overview](transactions-overview.md) · [ACID](acid.md) · [snapshot isolation](snapshot-isolation.md) · [lost updates](lost-updates.md) · [references](transactions-references.md)

If two transactions touch different data, or both are read-only,
they can run in parallel. Races appear when one reads what another
is writing, or both write the same objects.

Those bugs are timing-dependent and hard to test. An attacker can
also *force* the timing
([32](transactions-references.md)). Isolation exists so the
application can pretend concurrency is not happening.
[Serializable](serializability.md) isolation makes that pretence
true. It costs. Most systems ship a weaker level
([10](transactions-references.md), [30](transactions-references.md)).

Weak isolation has bankrupted a Bitcoin exchange [31]–[34], drawn
auditors ([35](transactions-references.md)), and corrupted customer
data ([36](transactions-references.md)). “Use an ACID database for
money” misses the point: popular relational systems use weak
isolation too. (Much of actual banking is text files over FTP plus
an audit trail ([37](transactions-references.md)).)

**Read committed** is the most basic useful level. Two guarantees:

1. A read sees only **committed** data (no dirty reads).
2. A write overwrites only **committed** data (no dirty writes).

Default in Oracle, PostgreSQL, SQL Server, and many others
([10](transactions-references.md)). Formal treatments: [38]–[41].

## No dirty reads

Transaction A has written *x* = 3 but not committed. Can B see 3?
If yes, that is a **dirty read** ([3](transactions-references.md)).
Read committed forbids it: A’s writes become visible only at
commit, and then all at once (Figure 8-4).

Why it matters:

- Multi-row update: B might see the new email but not the unread
  counter ([ACID](acid.md) Figure 8-2).
- If A aborts, B must not have seen data that never committed.
  Otherwise B must abort too — **cascading aborts**.

## No dirty writes

Two transactions update the same row. The later write wins — but
not if it overwrites a value that is still uncommitted. That is a
**dirty write** ([38](transactions-references.md)). Read committed
delays the second write until the first transaction commits or
aborts.

Figure 8-5: two buyers, one car. Listing update and invoice are
two rows. Dirty writes can award the car to Bryce and send the
invoice to Aaliyah. Read committed prevents that mix.

It does **not** fix the two-increment counter
([lost updates](lost-updates.md)). The second write happens after
the first commit, so it is not dirty. It is still wrong.

## Implementation

Dirty writes: **row-level lock**, held until commit or abort. One
writer per row. Automatic at read committed and stronger.

Dirty reads, option A: readers take the same lock briefly. A long
writer then stalls every reader of that row. Bad for
[response time](performance.md) and operability — a slow write in
one feature blocks reads in another. Still used in IBM Db2 and
SQL Server with `read_committed_snapshot=off`
([30](transactions-references.md)).

Option B (Figure 8-4): keep the old committed value **and** the
locked new value. Readers get the old one until commit. That is
the seed of [MVCC](snapshot-isolation.md#multiversion-concurrency-control).

**Read uncommitted** is weaker still: no dirty writes, dirty reads
allowed. Cheaper (one version of the row). It can *reduce* the
chance of a lost update; it does not prevent one.

**Architect takeaway:** read committed is “you will not see or
overwrite in-flight work.” It is not “your read-modify-write is
safe” and not “your multi-row read is from one point in time.”
Those are the next two Concepts.
