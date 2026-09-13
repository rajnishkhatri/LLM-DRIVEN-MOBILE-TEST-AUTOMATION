---
type: analysis
title: 'Single-leader replication'
description: 'One replica accepts writes and streams a log to followers. Sync buys a second up-to-date copy; async buys write availability. Failover is the hard case.'
tags: [data-intensive-design, replication, single-leader, failover, durability]
---

# Single-leader replication

**See also:** [chapter overview](replication-overview.md) · [replication logs](replication-logs.md) · [replication lag](replication-lag.md) · [multi-leader](multi-leader-replication.md) · [reliability](reliability.md) · [fencing](quorums-and-fencing.md) · [timeouts](timeouts-and-delays.md) · [references](replication-references.md)

Each node that stores a copy is a **replica**. Every write must reach
every replica or the copies diverge. The most common solution is
**leader-based** (primary-backup, active/passive) replication
(Figure 6-1):

1. One replica is the **leader** (primary, source
   ([2](replication-references.md))). Clients send writes there. The
   leader writes locally first.
2. The others are **followers** (read replicas, secondaries, hot
   standbys). The leader ships each change as a
   [replication log](replication-logs.md) or change stream. Followers
   apply writes in the **same order** as the leader.
3. Clients may read from the leader or any follower. Writes are
   accepted only by the leader.

If the database is [sharded](sharding-overview.md), each shard has
one leader. Different shards may put that leader on different nodes.

Single-leader is built into PostgreSQL, MySQL, Oracle Data Guard
([3](replication-references.md)), SQL Server Always On
([4](replication-references.md)), some document stores (MongoDB,
DynamoDB ([5](replication-references.md))), Kafka, DRBD, and some
network filesystems. Consensus algorithms such as Raft — CockroachDB
([6](replication-references.md)), TiDB ([7](replication-references.md)),
etcd, RabbitMQ quorum queues — also elect one leader and replace it
on failure (consensus is a later chapter).

Older docs say *master–slave*. Same mechanism; the term is widely
considered offensive ([8](replication-references.md)). Use leader /
follower.

## Synchronous versus asynchronous

Does the leader wait for a follower before telling the client the
write succeeded? (Figure 6-2.)

| Mode | Leader waits? | If that follower is down |
|---|---|---|
| **Synchronous** | Yes — until the follower confirms | Writes block |
| **Asynchronous** | No — send and continue | Writes proceed; that replica may be minutes behind |

Replication is usually fast (sub-second). There is **no guarantee**.
A recovering follower, a near-capacity cluster, or a bad network can
lag by minutes.

Synchronous replication means the follower is consistent with the
leader. If the leader dies, that copy is current. The cost: one
unresponsive synchronous replica stalls every write.

Making *every* follower synchronous is impracticable — any one outage
halts the system. In practice “synchronous” often means **one**
follower is sync and the rest are async. If the sync follower slows
or dies, another is promoted. Two nodes then hold a current copy:
leader plus one follower. That is **semisynchronous**.

Some systems sync a **majority** (for example three of five,
including the leader) and leave the rest async. That is a
[quorum](leaderless-replication.md#using-quorums-for-reading-and-writing).
Majority quorums show up in eventually consistent systems and in
consensus-based leader election (a later chapter).

Fully asynchronous: if the leader is unrecoverable, unreplicated
writes are **lost** even after the client saw success. The gain: the
leader keeps writing if every follower is behind. That weakening of
durability is widely used when there are many followers or they are
far away ([9](replication-references.md)). See
[replication lag](replication-lag.md).

## Setting up new followers

A naive file copy sees different parts of the database at different
times. Locking the database for a consistent copy fights
[availability](reliability.md). The usual zero-downtime path:

1. Take a **consistent snapshot** of the leader without a full write
   lock if the engine allows it (the same feature backups need;
   Percona XtraBackup for MySQL is the third-party example).
2. Copy the snapshot to the new node.
3. The follower connects and asks for changes **since the snapshot**.
   The snapshot must name an exact log position: PostgreSQL log
   sequence number; MySQL binlog coordinates or GTIDs.
4. When the backlog is applied, the follower has **caught up** and
   follows the live stream.

Steps vary from fully automated to an arcane runbook.

Archive the replication log plus periodic snapshots to an object
store. That is backup and disaster recovery, and it is also steps 1–2
of a new follower (WAL-G for PostgreSQL / MySQL / SQL Server;
Litestream for SQLite).

## Handling node outages

Reboot a node for a kernel patch without taking the service down.
Keep the impact of one outage small.

### Follower failure: catch-up recovery

Each follower keeps a log of changes from the leader. After a crash
or a network blip it reconnects and requests everything after the
last applied transaction, then resumes the stream.

Conceptually simple; operationally a load spike. High write
throughput or a long outage means a large backlog on both the
follower and the leader. The leader may drop log it has already
shipped to every *live* follower. If one follower stays down, the
leader chooses: retain log (disk risk) or delete it (that follower
must restore from backup).

### Leader failure: failover

Promote a follower, point clients at the new leader, retarget the
other followers. Manual or automatic. Automatic failover usually:

1. **Detect** the dead leader. There is no foolproof signal. Most
   systems use a timeout (say 30 seconds of missed heartbeats).
   Planned maintenance can hand off first.
2. **Choose** a new leader — election by a majority, or appointment
   by a controller ([13](replication-references.md)). Prefer the
   replica with the most recent log to limit data loss. Agreement on
   the winner is a consensus problem (a later chapter).
3. **Reconfigure** writes onto the new leader
   ([request routing](request-routing.md)). If the old leader
   returns, it must become a follower. It may still believe it is
   the leader.

What goes wrong:

- **Async data loss.** The new leader may not have every write. When
  the old leader rejoins, unreplicated writes are usually
  **discarded** — a write the client thought was committed was not
  durable.
- **External coordination.** GitHub promoted a lagging MySQL
  follower. Autoincrement reused primary keys that a Redis store
  still used; private data leaked to the wrong users
  ([14](replication-references.md)).
- **Split brain.** Two nodes both accept writes. Without
  [conflict resolution](conflict-resolution.md), data is lost or
  corrupted. Some systems shut down a node when two leaders appear;
  a clumsy fence can shut *both* down
  ([15](replication-references.md)), or detect too late.
- **Timeouts.** Long timeout: slow recovery. Short timeout: a load
  spike or network glitch triggers a failover that makes things
  worse.

Guarding against split brain by limiting or killing old leaders is
**[fencing](quorums-and-fencing.md)** — a token the storage
layer rejects when stale, not STONITH alone. No easy fix. Some
teams fail over by hand even when the software can do it
automatically.

Pick the most up-to-date follower. Sync or semisync: the one the old
leader waited on. Async: highest log sequence number. A fraction of
a second of loss may be tolerable; a follower days behind is not.

Node failures, unreliable networks, and the consistency / durability
/ availability / latency trade-offs are the distributed-systems
core. Later chapters return to them.

**Architect takeaway:** single-leader is an operations contract. Sync
to one follower if “the write I acknowledged still exists after a
crash” is non-negotiable. Failover is not a checkbox — it is data
loss, split brain, and timeout design.
