---
type: analysis
title: 'Distributed transactions'
description: 'Atomic commit across nodes is not “send commit to everyone.” 2PC is a system of promises; the coordinator is a single point of failure. XA makes that worse. Idempotence often replaces cross-system 2PC.'
tags: [data-intensive-design, transactions, two-phase-commit, xa, exactly-once]
---

# Distributed transactions

**See also:** [chapter overview](transactions-overview.md) · [serializability](serializability.md) · [ACID](acid.md) · [sharding](sharding-overview.md) · [durable workflows](durable-workflows.md) · [timeouts](timeouts-and-delays.md) · [process pauses](process-pauses.md) · [references](transactions-references.md)

On one node — or under
[single-leader](single-leader-replication.md) replication — the
leader runs isolation; followers apply the committed write log.

Several nodes in one transaction: multiple
[shards](sharding-overview.md), or a
[global secondary index](sharding-secondary-indexes.md) whose
entry lives on another node. Isolation algorithms still apply
(serial loop per shard, distributed 2PL, distributed SSI
checkers ([8](transactions-references.md))). **Atomicity** is
the new problem.

On one node, commit is “WAL the data, then append a commit
record” ([B-tree reliability](b-trees.md#making-b-trees-reliable)).
The disk’s finish of that record is the atomic moment
([22](transactions-references.md)).

“Tell every node to commit” is not enough (Figure 8-12):

- One node hits a conflict or constraint; another would commit.
- Some commit messages are lost; others land.
- One node crashes before the commit record and rolls back;
  another has committed.

A committed write is visible to others under
[read committed](read-committed.md) or stronger. You cannot
retract it because another node aborted. User 2 may already
have read the data. Mixed commit/abort leaves the nodes
inconsistent. The requirement is **atomic commitment**: all
commit or all abort.

## Two-phase commit

Classic algorithm ([13](transactions-references.md),
[73](transactions-references.md), [74](transactions-references.md)).
Used internally in some databases; exposed as
[XA](#xa-transactions) ([75](transactions-references.md)) or
WS-AtomicTransaction [76]–[77].

A **coordinator** (transaction manager) — often a library in
the app process (Narayana, JOTM, BTM, MSDTC), sometimes a
service — drives two phases (Figure 8-13):

1. **Prepare.** Ask every **participant** “can you commit?”
2. If all say yes → **commit**. If any says no → **abort**.

The Western wedding analogy: two “I do”s, then the pronouncement
([78](transactions-references.md)).

### A system of promises

Why two phases, when prepare and commit can also be lost?

1. App asks the coordinator for a globally unique transaction
   ID.
2. App opens a single-node transaction on each participant,
   tagged with that ID. Any fault here may abort.
3. Coordinator sends **prepare** with the ID. Timeout or failure
   → abort everyone.
4. A participant that votes **yes** has already `fsync`’d the
   data and checked constraints. It **surrenders the right to
   abort**, but has not committed. Crash is not an excuse later.
5. Coordinator decides (commit only if every vote is yes) and
   **writes the decision to its own log** — the **commit
   point**.
6. Coordinator sends commit or abort and **retries forever**.
   A recovered participant that voted yes must obey.

Two points of no return: the yes vote, and the coordinator’s
logged decision. Single-node commit collapses both into one
log write.

### Coordinator failure

Prepare fails → abort. Commit/abort message fails → retry.
If the coordinator dies **after** a yes vote and **before**
the participant hears the decision, that participant is
**in doubt** (Figure 8-14). It cannot abort (another node may
have committed) or commit (another may have aborted). 2PC
does not let participants compare votes.

Completion waits for the coordinator to recover and read its
log. Transactions with no commit record abort. The commit
point is an ordinary single-node atomic write **on the
coordinator**. Lose that disk and an administrator must
finish in-doubt transactions by hand. A partial log loss can
make the recovered coordinator abort already-committed work.

2PC is a **blocking** atomic commit. **Three-phase commit**
([13](transactions-references.md), [79](transactions-references.md))
is non-blocking only under bounded delay and bounded process
pauses — false on Ethernet/IP
([timeouts](timeouts-and-delays.md),
[process pauses](process-pauses.md)). The practical
fix is a **fault-tolerant consensus** coordinator (next chapter).

## Heterogeneous versus internal

2PC has a mixed reputation: a safety property that is hard
to get otherwise, and a source of outages and latency
[80]–[83]. Many cloud services refuse distributed transactions
([84](transactions-references.md)). Extra `fsync`s and extra
round trips are inherent.

Two different beasts:

| Kind | Participants | Typical fate |
|---|---|---|
| **Database-internal** | Nodes of one product (Spanner, TiDB, FoundationDB, YugabyteDB, VoltDB, Cassandra, MySQL NDB, Kafka [87]) | Can work well — custom protocol, no lowest common denominator |
| **Heterogeneous** | Two vendors, or a database plus a broker | XA / 2PC across drivers; operationally fragile |

### Exactly-once message processing

Heterogeneous 2PC’s best story: ack the queue **iff** the
database transaction commits. Fail either → abort both → the
broker redelivers. Side effects of the aborted unit disappear.
That is **exactly-once semantics** — if every side effect
speaks 2PC. An email server that does not will still double-
send on retry.

You do **not** need cross-system 2PC for this. A table of
processed message IDs inside **one** database is enough:

1. Unique message ID. Begin a DB transaction; if the ID is
   already stored, ack the broker and drop.
2. Else insert the ID, do the business writes, commit.
3. Then ack the broker.
4. Then delete the ID (separate transaction). Leftover IDs
   only waste space.

Crash before the DB commit → abort, broker retries. Crash
after commit, before ack → retry sees the ID and drops. A
uniqueness constraint stops two in-flight retries. The
processing step is **idempotent**. Kafka Streams uses the
same idea (a later chapter). Internal distributed
transactions still help if the ID table and the business
rows live on different shards.

## XA transactions

X/Open XA (1991) is a **C API**, not a network protocol
([75](transactions-references.md)). JTA on Java EE; JDBC and
JMS drivers that speak XA. PostgreSQL, MySQL, Db2, SQL Server,
Oracle; ActiveMQ, HornetQ, MSMQ, IBM MQ.

The coordinator is usually a **library in the application
process**, log on that machine’s disk. The app dies → the
coordinator dies → prepared participants sit in doubt until
that server is restarted and the library reads the log.
Participants cannot call the coordinator; everything goes
through the client driver.

### Locks while in doubt

[Read committed](read-committed.md) holds exclusive row locks
until commit. 2PL also holds shared locks on reads. 2PC holds
those locks for the whole in-doubt window. A 20-minute
coordinator restart holds them for 20 minutes. A lost
coordinator log holds them until a human acts. Other
transactions that need those rows block. Large parts of the
app freeze.

Orphaned in-doubt transactions happen
([85](transactions-references.md), [86](transactions-references.md)).
Rebooting the database must **not** drop those locks (that
would break atomicity). An administrator inspects each
participant and forces the same outcome. **Heuristic
decisions** — a participant unilaterally commits or aborts —
are a euphemism for breaking the promises. Emergency only.

### Why XA stays fragile

The coordinator is a SPOF. Its local disk is as precious as
the databases. Replicating it does not fix XA’s deeper
constraint: coordinator and participants **cannot talk except
through the application and its drivers**. The application
code is then the SPOF. Fixing that looks like
[durable execution](durable-workflows.md) — replicated,
restartable app code. Almost nobody does that for XA.

XA is a lowest common denominator: no cross-system deadlock
detection, no [SSI](serializability.md#serializable-snapshot-isolation).

## Database-internal 2PC

NewSQL systems use 2PC across shards without XA’s problems
because they may:

- Replicate the coordinator and fail it over.
- Let coordinator and shards speak directly.
- Replicate participants so one shard fault need not abort.
- Couple atomic commit with distributed concurrency control
  (deadlock detection, consistent cross-shard reads).

Consensus (Chapter 10) is the usual way to replicate
coordinator and shards. Isolation can still be
[snapshot](snapshot-isolation.md) ([6](transactions-references.md))
or SSI ([5](transactions-references.md),
[8](transactions-references.md)) across shards.

**Architect takeaway:** do not send an independent commit to
each node. Database-internal atomic commit is a product
feature; treat it as such. Heterogeneous XA is an operational
hazard — in-doubt locks, a coordinator disk, heuristic
escapes. For “process this message exactly once,” record the
message ID in the same database transaction as the writes and
make the handler idempotent. Save 2PC for when you truly
cannot.
