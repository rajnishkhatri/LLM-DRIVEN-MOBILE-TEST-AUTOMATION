---
type: reference
title: 'Multi-leader replication'
description: 'Several nodes accept writes and replicate asynchronously. You buy geo write-availability and offline devices; you pay conflicts that uniqueness constraints cannot survive. Sync multi-leader is single-leader in disguise.'
tags: [system-design-patterns, replication, multi-leader, B2c]
---

# Multi-leader replication

**See also:** [replication overview](../data-intensive-design/replication-overview.md) · [multi-leader (DDIA)](../data-intensive-design/multi-leader-replication.md) · [conflict resolution](../data-intensive-design/conflict-resolution.md) · [detecting concurrent writes](../data-intensive-design/detecting-concurrent-writes.md) · [unreliable clocks](../data-intensive-design/unreliable-clocks.md) · [single-leader](SingleLeaderReplication.md) · [leaderless](LeaderlessReplication.md) · [partitioning](Partitioning.md) · [replication lag](../data-intensive-design/replication-lag.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/b2-partition-replicate-external-research.md)

This card owns **when a second writer is worth the merge**. The shape — more than one node accepts writes; each forwards every change; each leader is a follower of the others — already lives in [multi-leader replication](../data-intensive-design/multi-leader-replication.md). Conflict *algorithms* (avoid, LWW, siblings, CRDT, OT) stay in [conflict resolution](../data-intensive-design/conflict-resolution.md). This card adds the operational filter: async-only scope, topology failure, when uniqueness dies, and the managed products that look like multi-writer and are not.

Quality attributes: **write availability** through a region or device partition, **latency** of a local write. Costs: concurrent writes that must be resolved, invariants you can no longer enforce, and topologies that need a human to rewire.

## Lineage and vocabulary

- **Kleppmann / this tree.** [Single-leader](SingleLeaderReplication.md) has one hard limit: if you cannot reach the leader, you cannot write. Multi-leader (active/active, bidirectional) lifts that. It rarely pays inside one region. The interesting cases are **geo-replication**, **offline devices**, and **real-time collaboration**.
- **Sync multi-leader is single-leader in disguise.** A partition between two sync leaders blocks writes the same way an unreachable primary does. The only interesting mode is *async* multi-leader: any leader keeps writing when the link to the others is down. Treat sync multi-leader as [single-leader](SingleLeaderReplication.md).
- **Cassandra architecture (stable docs, fetched 2026-09-13).** Last-write-wins (client or coordinator timestamp, **NTP assumed**), not vector clocks. That is a deliberate simplification. Wall clocks are not an event order ([unreliable clocks](../data-intensive-design/unreliable-clocks.md)).
- **DynamoDB global tables** are a managed multi-region *single-leader-per-partition* story plus async cross-region replication, **not** Dynamo-style leaderless and **not** two writers on the same item in one region. Conflict policy is last-writer-wins on item version. The exact clock (HLC vs wall vs per-item version) was **not** pinned this pass — do not invent it.

Older docs say *master–master*. Same mechanism; use leader / multi-leader.

## When a second writer pays

| Concern | Single-leader, multi-region | Async multi-leader |
|---|---|---|
| **Performance** | Every write pays the inter-region RTT | Local write; replicate later |
| **Regional outage** | Fail over the leader to another region | Each region keeps writing; catch up later |
| **Network** | Writes depend on the inter-region link | Each region proceeds through a blip |
| **Consistency** | Can offer serializable transactions on the leader | Weaker. Unique usernames and "account cannot go negative" are **not enforceable** — two leaders can each accept a locally valid write |

That last row is a distributed-systems limit, not a product bug. If you need those constraints, prefer a single leader, or a **consensus shard for the constrained keys only** (a common hybrid: multi-leader for the document, single-leader for the uniqueness index).

Supported in MySQL, Oracle, SQL Server, YugabyteDB; as an add-on in Redis Enterprise, EDB Postgres Distributed, pglogical. Because it is often retrofitted, autoincrement, triggers, and integrity constraints surprise you. MySQL Group Replication / InnoDB Cluster and EDB knobs were **not** fetched this pass — name the product, then read *its* conflict docs.

## Topologies

A **replication topology** is the path writes take. The table is already in the [DDIA case](../data-intensive-design/multi-leader-replication.md); operational restatement:

| Topology | Path | Operational failure |
|---|---|---|
| **All-to-all** | Every leader sends to every other | Best path diversity. Messages can **overtake** (insert on L1, update on L3, L2 sees the update first). Version vectors detect that; wall clocks do not. |
| **Circular** | Each node forwards to the next | One dead hop cuts the ring. Rewire is often **manual**. |
| **Star** (or tree) | One root fans out | The root is a single point of failure. Same manual rewire. |

Circular and star need **forwarding**. Tag each write with the node IDs it has visited so a node can drop its own echo. Reconfiguring around a dead node is often manual — budget a runbook, not an automatic failover. All-to-all does not need forwarding and pays overtake: the same causality problem as [consistent prefix reads](../data-intensive-design/replication-lag.md). A wall-clock timestamp is not enough. Many multi-leader products do not ship version vectors; read the docs and test the guarantees you think you have.

Cassandra's LWW is a *different family* (leaderless) that operators sometimes reach for as a multi-leader substitute. It is not one: any coordinator accepts the write, there is no topology to rewire, and the merge is a timestamp. Do not run a circular pglogical ring and a Cassandra CL menu as if they were the same control.

## Conflicts — detect, then pick a policy

Two writes are concurrent when **neither was aware of the other** when it was made. Wall-clock overlap does not matter; offline writes hours apart can still be concurrent. Detection is [detecting concurrent writes](../data-intensive-design/detecting-concurrent-writes.md). Resolution is [conflict resolution](../data-intensive-design/conflict-resolution.md) — do not re-derive the algorithms here.

Operational menu:

| Policy | What ops must believe | When it bites |
|---|---|---|
| **Avoid** | All writes for a record go through one leader (home region, home device). The *database* is multi-leader; that *record* is not. | Changing the designated leader (region down, user moved) reopens the race. Impossible for a true offline client. |
| **Last-write-wins** | NTP (or whatever clock the product documents) is good enough; losing a concurrent write is acceptable. | A rewinded clock wins. Cassandra's architecture page says it depends on NTP. Shopping-cart "never lose an add" is the opposite bet. |
| **Siblings / merge** | The app or a CRDT/OT engine can merge. | You do not have multi-leader until you have a merge story — you have split brain waiting to be noticed. |

IDs: two leaders issuing the same autoincrement sequence collide. Odd/even per leader is the textbook dodge; treat generated IDs as part of the topology design, not an afterthought.

**Conflict avoidance in operations.** Route all writes for a record through one leader (home region, home device). The database is multi-leader; that record is not. Example: a user edits only their own data — pin them to a home region. From that user’s point of view the system is single-leader. Changing the designated leader (region down, user moved) reopens the race: a write in flight during the move is a conflict again. Impossible for a true offline client; sometimes possible in geo-replicated servers. This is the cheapest merge policy (there is no merge) and the one that silently fails when the pin is a *preference* in the app and a *second writer* in the store.

Because multi-leader is often retrofitted, assume autoincrement, triggers, unique indexes, and cascading FKs fire on *each* leader until a concurrent-write test says otherwise. Dangerous territory if you can avoid it — the DDIA case's own warning.

## Sync engines and local-first

A calendar on phone and laptop must read and write offline, then sync. Each device is a local leader; sync is async multi-leader with lag of hours or days. Architecturally this is geo-replication taken to the extreme: each device is a "region" and the network is terrible. [Multi-leader](../data-intensive-design/multi-leader-replication.md) already covers offline-first vs local-first and the working-set limit (the user's own files — not "download the entire catalog"). The operational point: the merge policy is now in *client* code, and a bad merge ships to every device.

## Managed global tables vs true multi-writer

| Thing | Writers per item, per region | Cross-region | Conflict |
|---|---|---|---|
| **True multi-leader** (pglogical, EDB PGD, MySQL GR in multi-primary, Couch / Pouch) | N | async | Whatever the engine documents — test it |
| **DynamoDB global tables** | One leader per partition (Multi-Paxos); any replica in-region for eventually consistent reads | async replication to other regions | LWW on item version (clock not pinned this pass) |
| **Single-leader + async replica in another region** | One | async | None — the remote cannot write |

Global tables buy **regional read/write locality** without giving two writers in the same region a chance to conflict on the same item. They do **not** give you Cassandra-style "any coordinator accepts the write." Do not size a uniqueness invariant as if they did.

## Three workloads, one family

| Workload | What "leader" means | Merge you must have | Typical failure |
|---|---|---|---|
| **Geo** | One writer per region; async between regions | Conflict policy on records that *can* be edited in two regions (a user who travels; a shared cart) | Naming the remote as sync — you paid WAN on every COMMIT and still have two writers if you failover wrong |
| **Offline / local-first** | Each device is a leader; lag of hours or days | CRDT / OT / app merge that has been tested at *that* lag | LWW on a document edited on a plane |
| **Real-time collaboration** | Each open tab is a replica | OT or CRDT with a reactive apply; not LWW | Treating it as "just websocket fan-out" (the transport is not the replica family) |

A calendar on phone and laptop is geo taken to the extreme: each device is a "region" and the network is terrible. Works when the working set fits on the device (the user's own files). Not for "download the entire catalog." The operational point: the merge policy is now in *client* code, and a bad merge ships to every device. Lotus Notes pioneered the idea; today's backends (Firestore, Realm, Ditto; PouchDB/CouchDB, Automerge, Yjs) differ in merge — read the one you shipped.

Game **netcode** is the same *need* with game-specific techniques; it does not transfer.

## Observability

Multi-leader incidents are *this record's siblings*, *this hop's backlog*, or *this clock*.

| Signal | What it means |
|---|---|
| **Inter-leader lag** (bytes/time per link, not a single "replication lag") | Async backlog. A circular topology hides a dead hop as lag on the next edge. |
| **Conflict / sibling rate** | Merge load. A spike after a region cut is expected; a spike at steady state is a home-region pin that is not pinning. |
| **Clock offset** (NTP / chrony) | LWW products. An offset that exceeds typical write spacing is a silent discard. |
| **Forwarding / apply errors** | Circular and star: a node that cannot forward is a partition of the *topology*, not of the network. |
| **Client op duration** | Local write should *not* include the WAN. If it does, someone named a remote as sync. |

There is no single-leader `pg_stat_replication` equivalent that every product ships. Emit per-link apply lag and a conflict counter in the app when the store will not.

## Tuning — hybrid uniqueness

Goal: users in three regions edit documents with local latency; usernames stay unique.

| Knob | Choice | Why |
|---|---|---|
| Document / profile body | Async multi-leader, all-to-all, home-region *preference* (avoid) not a hard pin | Region loss must not block edits. Preference reduces conflicts without pretending they cannot happen. |
| Username / email uniqueness | Single-leader (or a consensus shard) for the constrained key only | Two leaders cannot both accept "alice". |
| Balance / inventory | Single-leader, or a ledger that records intents and reconciles | "≥ 0" is not enforceable on two writers. |
| Topology | All-to-all if N is small (3 regions) | Circular/star need a runbook to rewire; all-to-all needs version vectors or a store that will not overtake silently. |
| Clock | Do not use LWW for the document | Concurrent title edits hours apart (offline) are not a clock problem. |
| Sync window | Treat a 24 h offline device as a region that was partitioned | Merge must be exercised on that lag, not only on a 50 ms WAN. |

Revisit after a week of per-link lag and conflict rate. If conflicts cluster on one key class, pin that class; do not "turn up LWW".

## Testing and operating

- **Concurrent write fixture.** Two leaders, same record, disconnect the link, write A→B and A→C, restore. Assert the merge you documented — not the merge you hoped. If the product is LWW, rewind one clock and confirm a discard; that is the NTP incident in miniature.
- **Overtake.** All-to-all: insert on L1, update on L3, delay L1→L2. L2 must not apply the update before the insert, or you need version vectors ([detecting concurrent writes](../data-intensive-design/detecting-concurrent-writes.md)).
- **Uniqueness.** Two regions register `alice` while partitioned. If both succeed, the uniqueness index was not a single-leader shard.
- **Topology cut.** Kill the star root or one circular hop. Writes must either continue (all-to-all) or the runbook to rewire must have been rehearsed — "we will rewire" is not a control until it has a ticket.
- **Offline lag.** Sync a client that was off for 24 h. Merge must be exercised at that lag, not only at 50 ms WAN.
- **Global-table vocabulary.** Confirm in-region there is still one writer per partition. A test that writes the same item in two regions is a *cross-region* conflict test, not a leaderless test.

## Alternatives that beat a second writer

| Situation | Prefer | Why |
|---|---|---|
| One region, one AZ | [Single-leader](SingleLeaderReplication.md) + read replicas | A second writer is never free. |
| Cross-region *reads*, writes can wait | Single-leader + async remote replica | No merge. |
| Cross-region *writes*, uniqueness required | Single-leader (or consensus) for those keys; multi-lead the rest | Hybrid. |
| Any replica, no topology, shopping-cart siblings | [Leaderless](LeaderlessReplication.md) | Different family; still not a ledger. |
| Regional locality without in-region dual writers | Managed global tables | Not multi-writer in one region; not a merge engine. |

## Placement

| Placement | What it owns | Trade-off |
|---|---|---|
| **Store-native multi-primary** | Correctness of copies *and* the merge. | App cannot add a second writer later without a migration and a merge story. |
| **Hybrid** (multi-leader document + single-leader uniqueness) | Invariants stay enforceable. | Two replica families to operate; the uniqueness shard is a regional bottleneck. |
| **Managed global table** | Regional locality without in-region dual writers. | Not leaderless; not a substitute for a merge engine. |
| **Client sync engine** | Offline / local-first. | Merge bugs ship to every device; working set must fit. |

## Failure modes

| Mode | How it happens | What to do |
|---|---|---|
| **Uniqueness / invariant split** | Two leaders accept a locally valid write. | Do not multi-lead those keys. Hybrid, or single-leader. |
| **Clock-skew LWW** | A rewinded clock wins. | NTP where the product requires it; or version vectors / CRDTs. |
| **Overtake on all-to-all** | Update arrives before insert. | Version vectors; do not trust wall-clock order. |
| **Dead hop, circular/star** | One node down, the ring/tree does not forward. | Manual rewire; or all-to-all. |
| **Sync multi-leader under partition** | Both "leaders" block. | You bought the conflicts *and* the unavailability. Use async, or one leader. |
| **Retrofit surprises** | Autoincrement, triggers, unique indexes fire on each leader. | Assume they are wrong until proven; test with concurrent writes. |
| **Global-table vocabulary error** | Treated as Dynamo (2007) leaderless or as two writers per item. | One leader per partition; async across regions. |

## When not to multi-lead

- You need uniqueness or a non-negative invariant on the same keys that would be multi-written. Sync multi-leader buys you the conflicts *and* the partition unavailability.
- Everything sits in one region and one AZ. A second writer is never free; [single-leader](SingleLeaderReplication.md) plus read replicas is the default.
- The app cannot merge and you were hoping LWW would "probably be fine" for money rows.
- You actually wanted [leaderless](LeaderlessReplication.md) quorums (any replica, no topology) or [single-leader consensus](SingleLeaderReplication.md) (one writer, majority persist).

## Trade-offs

| Buy | Pay |
|---|---|
| Local writes through a region or device partition | Concurrent writes; a merge policy that is now a product decision |
| Async: each region proceeds through a blip | Unbounded lag; overtake; no uniqueness |
| All-to-all path diversity | Messages overtake; N² links |
| Circular / star: fewer links | Manual rewire; a dead hop is a partition |
| Home-region pin (conflict avoidance) | A move or a region loss reopens the race |
| Managed global tables | Regional locality without in-region dual writers — and without a merge engine |

A second writer is never free. You buy partition tolerance and local latency; you pay [conflict resolution](../data-intensive-design/conflict-resolution.md). If you do not have a merge story, you do not have multi-leader — you have split brain.

Default web apps keep almost no client state and call the server for every read or write. A sync engine flips that: persistent client state; the network is a background process. UI can hit the next frame because data is local; offline is a large delay, not a separate mode; local reads and writes almost never fail. Pair with a reactive model to apply collaborator edits. That is still this family: the replica set includes the device, and the merge is the product.

## Leaves to siblings

| Sibling | What they take |
|---|---|
| [Conflict resolution](../data-intensive-design/conflict-resolution.md) | Avoid / LWW / siblings / CRDT / OT algorithms. |
| [Detecting concurrent writes](../data-intensive-design/detecting-concurrent-writes.md) | Happens-before; version vectors. |
| [Single-leader](SingleLeaderReplication.md) | The hybrid uniqueness shard; sync multi-leader in disguise. |
| [Leaderless](LeaderlessReplication.md) | Any-coordinator writes; no topology to rewire. |
| [Failover](Failover.md) | Region failover when you *did* pin a home leader. |
| [Unreliable clocks](../data-intensive-design/unreliable-clocks.md) | Why LWW is not an event order. |

## Sources

Verified 2026-09-13; URLs, provenance, and items left out (DynamoDB global-table clock, MySQL GR / EDB knobs) are in the [external research note](../../docs/research/sysdesign/b2-partition-replicate-external-research.md). Algorithms stay in the cited cases.

- Canon: [multi-leader-replication.md](../data-intensive-design/multi-leader-replication.md); [conflict-resolution.md](../data-intensive-design/conflict-resolution.md); [detecting-concurrent-writes.md](../data-intensive-design/detecting-concurrent-writes.md).
- Products: Cassandra architecture (LWW + NTP); DynamoDB ATC 2022 (per-partition Multi-Paxos — the global-table *shape*, not an invented clock).
