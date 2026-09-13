---
type: analysis
title: 'Multi-leader replication'
description: 'Several nodes accept writes. Async multi-leader hides inter-region delay and partitions. Topologies and sync engines are the same bet: conflicts instead of a single writer.'
tags: [data-intensive-design, replication, multi-leader, geo-replication, local-first]
---

# Multi-leader replication

**See also:** [chapter overview](replication-overview.md) · [single-leader](single-leader-replication.md) · [conflict resolution](conflict-resolution.md) · [RPC problems](rest-rpc-dataflow.md#the-problems-with-remote-procedure-calls) · [references](replication-references.md)

[Single-leader](single-leader-replication.md) has one hard limit:
if you cannot reach the leader, you cannot write.

**Multi-leader** (active/active, bidirectional) lets more than one
node accept writes. Each writer still forwards every change to the
others; each leader is a follower of the others.

Synchronous multi-leader is almost single-leader in disguise: a
partition between A and B blocks writes on A the same way a
unreachable leader would. Treat sync multi-leader as single-leader.
The rest of this note is **asynchronous** multi-leader: any leader
keeps writing when the link to the others is down.

It rarely pays inside one region. The interesting cases are
geo-replication, offline devices, and real-time collaboration.

## Geographically distributed operation

Replicas in several regions: survive a region loss, or sit near
users. With one leader, every write crosses the internet to that
region (Figure 6-6).

With a leader per region: inside the region, ordinary
leader–follower (followers maybe in another AZ); between regions,
leaders replicate to each other.

| Concern | Single-leader, multi-region | Async multi-leader |
|---|---|---|
| **Performance** | Every write pays the inter-region RTT | Local write; replicate later |
| **Regional outage** | Fail over the leader to another region | Each region keeps writing; catch up later |
| **Network** | Writes depend on the inter-region link | Each region proceeds through a blip |
| **Consistency** | Can offer [serializable](serializability.md) transactions | Weaker. Unique usernames and “account cannot go negative” are not enforceable — two leaders can each accept a locally valid write |

That last row is a distributed-systems limit
([28](replication-references.md)). If you need those constraints,
prefer a single leader. Many apps do not; see
[conflict resolution](conflict-resolution.md).

Supported in MySQL, Oracle, SQL Server, YugabyteDB; as an add-on in
Redis Enterprise, EDB Postgres Distributed, pglogical
([29](replication-references.md)). Because it is often retrofitted,
autoincrement, triggers, and integrity constraints surprise you.
Dangerous territory if you can avoid it
([30](replication-references.md)).

## Topologies

A **replication topology** is the path writes take (Figure 6-7).

| Topology | Path | Failure mode |
|---|---|---|
| **All-to-all** | Every leader sends to every other | Best path diversity; messages can **overtake** on a slow link (Figure 6-8) |
| **Circular** | Each node forwards to the next | One dead node cuts the ring |
| **Star** (or tree) | One root fans out | The root is a single point of failure |

Circular and star need **forwarding**. Tag each write with the node
IDs it has visited so a node can drop its own echo
([31](replication-references.md)). Reconfiguring around a dead node
is often manual.

Figure 6-8: A inserts on leader 1; B updates that row on leader 3;
leader 2 may see the update *before* the insert. That is the same
causality problem as
[consistent prefix reads](replication-lag.md#consistent-prefix-reads).
A wall-clock timestamp is not enough (clocks, a later chapter).
[Version vectors](detecting-concurrent-writes.md#version-vectors)
order these events. Many multi-leader products do not; read the
docs and test the guarantees you think you have.

## Sync engines and local-first software

A calendar on phone and laptop must read and write offline, then
sync. Each device is a local leader; sync is async multi-leader
with lag of hours or days. Architecturally this is geo-replication
taken to the extreme: each device is a “region” and the network is
terrible.

### Real-time collaboration, offline-first, local-first

Google Docs, Figma, Linear
([32](replication-references.md), [33](replication-references.md),
[34](replication-references.md)): local edits paint immediately;
collaborators see them with low latency. Each open tab is a replica.
Even without offline edit, concurrent unsynchronized writes already
make the system multi-leader.

A **sync engine** captures local changes, sends them now or later,
merges inbound changes, and updates the UI
([35](replication-references.md), [36](replication-references.md),
[37](replication-references.md)). **Offline-first** means the user
keeps editing without a network
([38](replication-references.md)). **Local-first** adds: the app
still works if the vendor shuts the cloud — open sync protocol,
more than one provider ([39](replication-references.md),
[40](replication-references.md)). Git is local-first (not real-time).

### Pros and cons of sync engines

Default web apps keep almost no client state and call the server
for every read or write. A sync engine flips that: persistent
client state; the network is a background process.

- UI can hit the next frame (16 ms at 60 Hz) because data is local.
- Offline is just a large delay, not a separate mode.
- Fewer explicit
  [RPC error paths](rest-rpc-dataflow.md) in UI code
  ([41](replication-references.md)): local reads and writes almost
  never fail.
- Pair with a reactive model to apply collaborator edits
  ([42](replication-references.md)).

Works when the working set fits on the device (the user’s own
files). Not for “download the entire catalog.”

Lotus Notes pioneered the idea in the 1980s
([43](replication-references.md)). Today: proprietary backends
(Firestore, Realm, Ditto) and open backends suited to local-first
(PouchDB/CouchDB, Automerge, Yjs). Game **netcode** is the same
need with game-specific techniques
([44](replication-references.md)); it does not transfer.

**Architect takeaway:** a second writer is never free. You buy
partition tolerance and local latency; you pay
[conflict resolution](conflict-resolution.md). If you do not have a
merge story, you do not have multi-leader — you have split brain
with extra steps.
