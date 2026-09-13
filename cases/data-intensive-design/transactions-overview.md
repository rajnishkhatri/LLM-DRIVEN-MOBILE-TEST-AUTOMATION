---
type: overview
title: 'Transactions'
description: 'Group reads and writes into one unit: commit or abort. Isolation levels name which races the database hides. Serializability hides all of them; weaker levels leave some for you.'
tags: [data-intensive-design, transactions, isolation, acid, overview]
---

# Transactions

> Some authors have claimed that general two-phase commit is too
> expensive to support, because of the performance or availability
> problems that it brings. We believe it is better to have application
> programmers deal with performance problems due to overuse of
> transactions as bottlenecks arise, rather than always coding around
> the lack of transactions.
>
> — James Corbett et al., “Spanner: Google’s Globally-Distributed
> Database” (2012)

Many things go wrong in a data system: a crash mid-write, a network
cut, two clients overwriting each other, a read of a half-updated
row. A **transaction** groups several reads and writes into one
logical unit. The whole unit **commits** or **aborts**. On abort the
application can retry. Partial failure becomes one error.

Transactions are not a law of nature. They exist to simplify the
programming model: the database absorbs certain faults and races
(**safety guarantees**). You can weaken or drop them for
[performance](performance.md) or availability. Some safety is
possible without them. The Post Office Horizon scandal is a reminder
of the other direction: missing
[ACID](acid.md) accounting transactions can ruin lives
([1](transactions-references.md); [reliability](reliability.md)).

Prior chapter: [sharding](sharding-overview.md).

## What is a transaction?

Relational databases still follow IBM System R (1975)
([2](transactions-references.md), [3](transactions-references.md),
[4](transactions-references.md)). MySQL, PostgreSQL, Oracle, SQL
Server look uncannily similar fifty years later.

Early NoSQL dropped transactions, or reused the word for a much
weaker guarantee — [replication](replication-overview.md) and
[sharding](sharding-overview.md) by default, transactions as the
casualty. The claim that transactions cannot scale turned out to be
wrong. **NewSQL** systems (CockroachDB, TiDB, Spanner, FoundationDB,
YugabyteDB) combine sharding with consensus [5]–[8] and keep strong
ACID at scale.

That does not mean every system must be transactional. Know the
guarantees and the cost.

## Topic map

| Topic | The question | Concept |
|---|---|---|
| ACID | Abortability, invariants, isolation, durability — which letter is the database’s? | [The meaning of ACID](acid.md) |
| Read committed | No dirty reads, no dirty writes. Enough? | [Read committed](read-committed.md) |
| Snapshot | A consistent point in time. Readers never block writers? | [Snapshot isolation](snapshot-isolation.md) |
| Lost updates | Read-modify-write: atomic op, lock, detect, or CAS? | [Preventing lost updates](lost-updates.md) |
| Write skew | Two transactions, two objects, one invariant broken? | [Write skew and phantoms](write-skew-phantoms.md) |
| Serializability | Serial loop, 2PL, or optimistic SSI? | [Serializability](serializability.md) |
| Distributed | All commit or all abort across nodes. 2PC, XA, or idempotence? | [Distributed transactions](distributed-transactions.md) |

Citations for this chapter live in
[transaction references](transactions-references.md). Earlier
chapters keep their own lists: [trade-off references](references.md),
[NFR references](nfr-references.md),
[data-model references](data-models-references.md),
[storage references](storage-references.md),
[encoding references](encoding-references.md),
[replication references](replication-references.md),
[sharding references](sharding-references.md).

## Anomalies at a glance

| Isolation | Dirty reads | Read skew | Phantom reads | Lost updates | Write skew |
|---|---|---|---|---|---|
| Read uncommitted | possible | possible | possible | possible | possible |
| [Read committed](read-committed.md) | prevented | possible | possible | possible | possible |
| [Snapshot](snapshot-isolation.md) | prevented | prevented | prevented (reads) | depends | possible |
| [Serializable](serializability.md) | prevented | prevented | prevented | prevented | prevented |

Almost every implementation also prevents **dirty writes** (not in
the table). Snapshot isolation prevents straightforward phantoms on
read-only queries; phantoms that feed
[write skew](write-skew-phantoms.md) need serializability or a
manual lock.

## Summary

A transaction is an abstraction: pretend certain concurrency bugs
and certain faults do not exist. A large class of errors collapses
to abort-and-retry.

A single-record read/write can live without transactions. Complex
access — denormalized counters, foreign keys,
[secondary indexes](sharding-secondary-indexes.md) — cannot, not
without making every error path the application’s problem.

Weak isolation protects some races and leaves the rest to you
(`SELECT FOR UPDATE`, uniqueness constraints, materializing
conflicts). Only serializable isolation protects all of them. Three
implementations: a serial loop, two-phase locking, or serializable
snapshot isolation.

[Distributed atomic commit](distributed-transactions.md) is a
separate problem. Database-internal 2PC can work. Heterogeneous XA
does not, operationally. Idempotence often replaces cross-system
atomic commit.

**Architect takeaway:** pick the isolation level by the races you
refuse to handle in application code. Read committed is the common
default and is not enough for counters, unique names, or “at least
one doctor on call.” Snapshot isolation is a consistent backup and
analytics snapshot, not serializability — even when the vendor
labels it that way. Distributed XA is a last resort; prefer one
database’s internal transactions, or make the side effect
idempotent.

Next chapter: [the trouble with distributed systems](distributed-systems-overview.md)
— partial failure, unreliable networks and clocks, process
pauses, quorums, fencing, and system models.
