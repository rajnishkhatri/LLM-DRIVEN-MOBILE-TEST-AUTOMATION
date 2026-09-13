---
type: analysis
title: 'Replication logs'
description: 'Statement logs break on nondeterminism. WAL shipping couples you to the storage engine. A logical row log decouples versions and enables CDC.'
tags: [data-intensive-design, replication, wal, logical-log, cdc]
---

# Replication logs

**See also:** [chapter overview](replication-overview.md) · [single-leader](single-leader-replication.md) · [write-ahead log](b-trees.md#making-b-trees-reliable) · [event sourcing](event-sourcing-cqrs.md) · [references](replication-references.md)

How does [leader-based replication](single-leader-replication.md)
work under the hood? Three log styles in practice.

## Statement-based replication

The leader logs every write *statement* and sends that log to
followers. For SQL that is every `INSERT`, `UPDATE`, or `DELETE`.
Each follower parses and executes it as if a client had sent it.

It breaks:

- Nondeterministic functions (`NOW`, `RAND`) yield different values
  on each replica.
- Autoincrement columns and `UPDATE … WHERE <condition>` require
  **exactly the same order** on every replica — painful with
  concurrent transactions.
- Triggers, stored procedures, and UDFs can produce different side
  effects unless they are absolutely deterministic.

Workarounds exist: the leader can replace nondeterministic calls
with a fixed value in the log. Deterministic statements in a fixed
order is the same idea as
[event sourcing](event-sourcing-cqrs.md) — **state machine
replication** (shared logs are a later chapter).

MySQL used statement-based replication before 5.1. It is compact and
still appears, but MySQL now switches to row-based when a statement
is nondeterministic. VoltDB keeps statement-based and requires
deterministic transactions ([16](replication-references.md)).
Determinism is hard; many engines prefer another method.

## Write-ahead log shipping

A [write-ahead log](b-trees.md) makes B-tree engines crash-safe:
every modification hits the WAL first so the tree can be rebuilt.
That log also builds a replica. The leader writes the WAL to disk
*and* ships it. The follower applies it and reconstructs the same
files.

PostgreSQL and Oracle do this
([17](replication-references.md), [18](replication-references.md)).
The cost: the log is **physical** — which bytes changed in which
disk blocks. Replication is coupled to the storage engine. A format
change usually means leader and followers cannot run different
software versions.

That is an operations problem, not a footnote. If a follower may run
a *newer* version than the leader, you upgrade followers first, then
fail over — zero-downtime. WAL shipping often forbids that mismatch,
so upgrades take downtime.

## Logical (row-based) log replication

Use a different log for replication than for the storage engine.
A **logical log** describes writes at row grain, not pages:

| Change | What the log carries |
|---|---|
| Insert | New values of all columns |
| Delete | Enough to identify the row (primary key, or all old columns if there is no key) |
| Update | Identity plus new values (or at least the changed columns) |

A multi-row transaction is several such records plus a commit
record. MySQL row-based replication keeps a separate logical
**binlog** beside the WAL. PostgreSQL decodes the physical WAL into
insert / update / delete events ([19](replication-references.md)).

Because the log is decoupled from engine internals, it is easier to
keep **backward compatible**. Leader and follower can run different
versions — the path to a low-downtime upgrade
([20](replication-references.md)).

A logical log is also easier for *external* consumers to parse. Ship
it to a warehouse or a custom index / cache
([21](replication-references.md)). That is **change data capture**
(a later chapter).

**Architect takeaway:** the log format is an upgrade and integration
contract. Statement logs are compact and fragile. Physical WAL is
simple and version-locks the cluster. Logical row logs cost an extra
format and buy rolling upgrades plus CDC.
