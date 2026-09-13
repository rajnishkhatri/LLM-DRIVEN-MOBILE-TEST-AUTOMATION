---
type: analysis
title: 'Serializability'
description: 'The strongest isolation: the result matches some serial order. Three implementations — a single-thread loop, two-phase locking, or optimistic SSI — trade throughput, tail latency, and abort rate.'
tags: [data-intensive-design, transactions, serializability, two-phase-locking, ssi]
---

# Serializability

**See also:** [chapter overview](transactions-overview.md) · [write skew](write-skew-phantoms.md) · [snapshot isolation](snapshot-isolation.md) · [distributed transactions](distributed-transactions.md) · [references](transactions-references.md)

[Read committed](read-committed.md) and
[snapshot isolation](snapshot-isolation.md) miss races —
especially [write skew and phantoms](write-skew-phantoms.md).
The sad facts:

- Isolation *names* are inconsistent (`repeatable read` means
  three different things).
- You cannot tell from application code whether a level is safe,
  especially in a large app.
- There are no good race detectors in daily use. Static analysis
  exists in papers ([35](transactions-references.md)); tests are
  nondeterministic.

This has been true since weak isolation was introduced in the
1970s ([3](transactions-references.md)). The research answer is
unchanged: use **serializable** isolation.

Serializable means the committed result matches some **serial**
execution, even if transactions ran in parallel. If each
transaction is correct alone, they stay correct together. Every
race in this chapter is prevented.

Why isn’t it the default? Implementation cost. Three families:

1. Actually run one transaction at a time.
2. [Two-phase locking](#two-phase-locking) — the 30-year default.
3. Optimistic **serializable snapshot isolation**.

## Actual serial execution

Remove concurrency. One thread, one transaction at a time. By
definition serializable.

Serious only since the 2000s ([59](transactions-references.md)):

- RAM is cheap enough that the **active** set often fits
  ([in-memory stores](secondary-indexes.md#keeping-everything-in-memory)).
- [OLTP](operational-vs-analytical.md) transactions are short and
  touch few records. Long analytics are read-only and can sit on
  a snapshot **outside** the serial loop.

VoltDB/H-Store, Redis, Datomic [60]–[62]. No lock coordination,
so a single core can beat a locking engine — until you need more
than one core.

### Stored procedures

Interactive `BEGIN` … query … think … query … `COMMIT` spends
most of its life on the network. A serial loop waiting on that
is unusable. Humans were already removed from the transaction
(one HTTP request); the remaining chatty style still needs
concurrency.

Serial engines forbid interactive multi-statement transactions.
Submit **one statement**, or the whole body as a **stored
procedure** ([63](transactions-references.md)). If the working
set is in RAM, the procedure runs without network or disk waits
(Figure 8-9).

Stored procedures have a reputation: vendor languages (PL/SQL,
T-SQL, PL/pgSQL), hard to test and deploy, one bad procedure
hurts every tenant, untrusted code next to the kernel
([64](transactions-references.md)). Modern engines use ordinary
languages (Java, Groovy, Clojure, Lua, JavaScript). GraphQL
proxies that cannot validate often push rules into a procedure.

VoltDB replicates by running the **same deterministic
procedure** on every replica (state-machine replication; a later
chapter). Dates and clocks must go through deterministic APIs
([durable workflows](durable-workflows.md)).

### Sharding the loop

Throughput is one core. Read-only work can leave the loop.
Writes that do not fit one core need [shards](sharding-overview.md).
If every transaction stays inside one shard, each shard has its
own thread and throughput scales with cores
([61](transactions-references.md)).

A cross-shard transaction must run the procedure in lockstep on
every touched shard. VoltDB quoted ~1,000 cross-shard writes/s
— orders of magnitude below single-shard, and adding machines
does not raise it ([63](transactions-references.md)). Later work
tries to scale multi-shard ([65](transactions-references.md)).
[Secondary indexes](sharding-secondary-indexes.md) make
single-shard transactions harder.

Constraints: every transaction small and fast (one slow one
stalls the world); active data in memory; write rate one core
or shardable without cross-shard coordination; cross-shard
possible but not scalable.

## Two-phase locking

For ~30 years, **2PL** (strong strict 2PL) was the serializable
algorithm. **2PL is not 2PC.** 2PL is isolation; 2PC is
[distributed atomic commit](distributed-transactions.md).

Read-committed already locks writers of the same row. 2PL is
stricter:

- A has read *x*; B wants to write *x* → B waits for A to end.
- A has written *x*; B wants to read *x* → B waits. Reading the
  old version (Figure 8-4) is **not** allowed.

Writers block readers and readers block writers. That is the
opposite of snapshot isolation’s mantra. 2PL prevents lost
updates and write skew.

Used as `serializable` in MySQL/InnoDB and SQL Server, and as
`repeatable read` in Db2 ([30](transactions-references.md)).

Each object has a **shared** or **exclusive** lock
(multi-reader, single-writer):

- Read → shared. Several readers; wait if anyone holds exclusive.
- Write → exclusive. Wait for any lock.
- Read then write → upgrade shared to exclusive.
- Hold until commit or abort. **Growing** phase (acquire only),
  then **shrinking** phase (release only). No acquire after a
  release.

Deadlocks are common; the database aborts one transaction; the
application retries.

### Performance

2PL is why it is not the default. Throughput and latency are
worse than weak isolation — not mainly lock bookkeeping, but
**lost concurrency**. Anything that *might* race waits.

A table scan (backup, analytics, integrity check) takes a shared
lock on the **table**. Writers wait for the scan; the scan waits
for in-flight writers. The database is write-unavailable for
the duration. High-percentile latency becomes unstable
([performance](performance.md)). One fat transaction stalls
everyone. Timeouts and slow-query monitors are load-bearing.
Deadlocks (and wasted retry work) are much more frequent than
under read committed.

### Predicate and index-range locks

Object locks do not stop [phantoms](write-skew-phantoms.md).
Serializable isolation must.

A **predicate lock** ([4](transactions-references.md)) covers
every object matching a search — including objects that do not
exist yet:

```sql
SELECT * FROM bookings
  WHERE room_id = 123
    AND end_time   > '2026-01-01 12:00'
    AND start_time < '2026-01-01 13:00';
```

A reader takes a shared predicate lock on that condition. An
inserter whose new or old value matches must wait. That closes
write skew.

Predicate locks are slow to match. Most 2PL engines approximate
with **index-range (next-key) locks**
([56](transactions-references.md), [66](transactions-references.md)):
widen the predicate (all times for room 123, or all rooms in
that hour). Safe — every write that matched the real predicate
matches the wider one — and cheaper. Attach the lock to the
`room_id` index entry or to a time range. No useful index →
fall back to a table lock.

## Serializable snapshot isolation

2PL is slow. Serial execution does not scale. Weak isolation
races. **SSI** (2008: [55](transactions-references.md),
[67](transactions-references.md)) gives serializability at a
small tax over snapshot isolation.

In production: PostgreSQL `serializable`
([56](transactions-references.md)), SQL Server Hekaton
([68](transactions-references.md)), HyPer
([69](transactions-references.md)), CockroachDB, FoundationDB,
BadgerDB.

### Pessimistic versus optimistic

2PL is **pessimistic**: if a lock says “maybe unsafe,” wait.
Serial execution is pessimistic to the extreme — exclusive lock
on the whole (shard of the) database, held briefly because the
transaction is tiny.

SSI is **optimistic** ([70](transactions-references.md),
[71](transactions-references.md)): proceed; at commit, abort if
isolation broke. High contention → many aborts → retries can
push a saturated system over the edge. Spare capacity and
moderate contention favor optimistic. Commutative atomics
(concurrent increments you do not also read) reduce conflicts.

SSI = snapshot isolation + a conflict detector.

### Outdated premises

Write skew is “I acted on a fact that was true at snapshot time
and may be false at commit” (“two doctors on call”). The
database cannot see your application logic, so it treats any
change to a query result as a possible causal dependency and
aborts if that happened.

Two detections:

1. **Stale MVCC read** — you ignored an uncommitted write that
   later committed (Figure 8-10). Track ignored writes; at
   commit, if any of them committed, abort. Do not abort
   immediately: the reader may be read-only, or the writer may
   still abort. That preserves long snapshot reads.
2. **Write after read** — someone else changes data you already
   read (Figure 8-11). Use the index like a range lock, but as
   a **tripwire**, not a block. The writer notifies prior
   readers. First committer wins; the other aborts if the
   conflicting write has already committed.

### Performance of SSI

Finer tracking → fewer unnecessary aborts, more bookkeeping.
PostgreSQL uses theory to skip some aborts
([14](transactions-references.md), [56](transactions-references.md)).

Versus 2PL: no waiting on another transaction’s locks. Readers
and writers do not block each other. Latency is more predictable.
Read-only queries stay lock-free on a snapshot.

Versus serial execution: not capped at one core. FoundationDB
spreads conflict detection across machines and still allows
cross-shard serializable transactions.

Versus plain snapshot isolation: the check has a cost. Some
argue it is not worth it ([72](transactions-references.md));
others that SSI is now good enough to drop weak snapshot
([69](transactions-references.md)). Abort rate dominates: long
read/write transactions collide. Long **read-only** is fine.
SSI is less sensitive to one slow transaction than 2PL or a
serial loop.

**Architect takeaway:** if the invariant matters, pay for
serializability. Prefer SSI when the product has it — it keeps
snapshot-isolation’s operational shape. Use a serial in-memory
loop when transactions are tiny, stored procedures, and
single-shard. Use 2PL only if that is what the engine has; budget
for tail latency and deadlocks. Never trust the word
“serializable” on the isolation menu without checking which of
these three you actually got.
