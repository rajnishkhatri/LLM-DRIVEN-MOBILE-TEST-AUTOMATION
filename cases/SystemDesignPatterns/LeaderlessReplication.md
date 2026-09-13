---
type: reference
title: 'Leaderless replication'
description: 'Any replica accepts writes; quorums (w + r > n) make staleness unlikely, not linearizable. Sloppy quorum plus hinted handoff is not an intersection proof. Repair must beat tombstone grace or deletes resurrect.'
tags: [system-design-patterns, replication, leaderless, quorum, B2d]
---

# Leaderless replication

**See also:** [replication overview](../data-intensive-design/replication-overview.md) · [leaderless (DDIA)](../data-intensive-design/leaderless-replication.md) · [quorums and fencing](../data-intensive-design/quorums-and-fencing.md) · [conflict resolution](../data-intensive-design/conflict-resolution.md) · [detecting concurrent writes](../data-intensive-design/detecting-concurrent-writes.md) · [single-leader](SingleLeaderReplication.md) · [multi-leader](MultiLeaderReplication.md) · [partitioning](Partitioning.md) · [rebalance & request routing](RebalanceRouting.md) · [failover](Failover.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/b2-partition-replicate-external-research.md)

This card owns **quorum math as an operational control**, not a linearizability proof. The shape — any replica accepts writes; the coordinator does **not** impose a write order; reads also fan out — already lives in [leaderless replication](../data-intensive-design/leaderless-replication.md). Majority-as-death and fencing tokens stay on [quorums and fencing](../data-intensive-design/quorums-and-fencing.md) and [failover](Failover.md). Dynamo (2007, leaderless) and DynamoDB (2012+, single-leader Multi-Paxos per partition) are **different systems**.

Quality attributes: **write availability** while a node is down (nothing to fail over), **durability** as a *probability* set by `(n, w, r)` and repair. Costs: stale reads even when `w + r > n`, clock-skew LWW, and a repair/tombstone contract that resurrects deletes if you miss it.

## Lineage and vocabulary

- **DeCandia et al., SOSP 2007 *Dynamo*.** Preference list; N replicas on the ring; **sloppy quorum** + hinted handoff; Merkle-tree anti-entropy; vector clocks; gossip membership. Common production knob: **(N, R, W) = (3, 2, 2)**. Measured on "a couple hundred nodes". The paper's success-rate figure is Dynamo-internal, not a product SLA — do not quote it as one.
- **Kleppmann / this tree.** `w + r > n` makes an up-to-date value *likely* in the read set because the sets overlap. Quorums need not be majorities — they need overlap. Even with the inequality, edge cases (restored-from-backup, rebalance, concurrent read/write, a "failed" write that landed on some replicas, LWW clock skew) mean this is **not** a linearizability proof. Dynamo-style stores are built for apps that can live with eventual consistency.
- **Cassandra architecture + 5.0.8 `cassandra.yaml` (fetched 2026-09-13).** Dynamo-style ring + LSM. **Last-write-wins** (client or coordinator timestamp, NTP assumed), not vector clocks. `NetworkTopologyStrategy` per-DC RF. Consistency is a **menu** (`ONE` / `QUORUM` / `LOCAL_QUORUM` / …) instead of raw R, W. Hinted handoff default **on**, window **3 h**. `gc_grace_seconds` default **864000 (10 days)**.
- **Vogels / Terry** (cited in [replication lag](../data-intensive-design/replication-lag.md)). "Eventual consistency" has **no bound**. The operational substitutes are read-your-writes, monotonic reads, consistent prefix — which leaderless does not give you for free.

Riak, Cassandra, and ScyllaDB are Dynamo-inspired. Amazon's original Dynamo was never released outside Amazon.

## Mechanics

Three replicas, one rebooting. [Single-leader](SingleLeaderReplication.md) may need failover. Leaderless has nothing to fail over: write all three in parallel; two acknowledge; that is enough. The down replica misses the write. Reads also go to several nodes; values carry a version or timestamp; the client keeps the greatest.

### Catch-up

| Mechanism | What it does | Best for | Operational trap |
|---|---|---|---|
| **Read repair** | A parallel read sees a stale replica and writes the newer value back | Hot keys | Cold keys stay stale until repair |
| **Hinted handoff** | A live replica stores writes for a down peer, then forwards them | Keys that are never read | Hints that outlive the window are **gone** |
| **Anti-entropy** | Background compare-and-copy; Dynamo Merkle trees over the whole keyspace; Cassandra adds **sub-range** and **incremental** repair | Residual drift | Repair period must be **< `gc_grace`** or deletes resurrect |

### Sloppy vs strict

Dynamo writes the first N *healthy* preference-list nodes (**sloppy quorum**). If A is down, the write intended for A is stored on D with a *hint*; D later hands it back. Intersection `W + R > RF` is the *usual* visibility argument; sloppy membership, hinted handoff, clock skew, and partial quorum on different replica sets are why it is not a linearizability proof. A hinted write on D plus a read of A+B (A still stale) is the textbook miss.

Cassandra: `hinted_handoff_enabled` default **true**, `max_hint_window` default **3 h**, `hinted_handoff_throttle` default **1024 KiB/s** per delivery thread (divided by cluster size). Hints that outlive the window are gone — **repair** is the backstop, not a hint.

### Consistency menu (Cassandra)

Writes always fan out to all replicas; the level is how many acks the coordinator waits for. Reads contact enough replicas to satisfy the level (plus speculative retry).

| Level | Meaning (RF = n) |
|---|---|
| `ONE` | One replica (or, for writes, a commit log + memtable) |
| `QUORUM` | `n/2 + 1` of RF (RF=3 → 2) |
| `LOCAL_QUORUM` | Majority in the coordinator's DC (the geo-latency knob) |
| `EACH_QUORUM` | Majority in *every* DC |
| `ANY` (writes only) | May succeed on a **hint alone** — not readable until a real replica has it |

cqlsh / some historical DataStax pages defaulted CL to `ONE`. Cassandra 5 driver/session defaults were **not** re-verified per language this pass. Treat "default ONE" as *historical / cqlsh*, not universal. Set the level in the session; do not inherit it.

**RF is per keyspace, not per cluster.** Production placement is `NetworkTopologyStrategy` with an RF per DC (commonly 3/3), not a single `SimpleStrategy` RF that straddles a WAN. `LOCAL_QUORUM` then means "majority in *this* DC"; `QUORUM` on RF=3+3 waits for 4 and pays the WAN; `EACH_QUORUM` waits for a majority in every DC. Pick the strategy *before* you pick the menu — a `LOCAL_QUORUM` on `SimpleStrategy` is not a geo knob.

Requests still go to all `n` in parallel. `w` and `r` are how many successes you **wait for**. Fewer than `w` or `r` reachable nodes: error. Why a node failed does not matter. There may be more than `n` nodes in the cluster; a given value lives on only `n` of them ([partitioning](Partitioning.md)).

`phi_convict_threshold` default **8** (Phi accrual); UP/DOWN is a *local* decision, not gossipped. Cassandra will not remove a node from gossip without an operator decommission or `replace_address_first_boot` — intentional, to avoid needless rebalance on transient failure ([rebalance](RebalanceRouting.md)).

## What `w + r > n` does not prove

The inequality is the *usual* visibility argument. [Leaderless](../data-intensive-design/leaderless-replication.md) already lists the edge cases; operational restatement — do not treat a green `LOCAL_QUORUM` dashboard as linearizability:

- A node with the new value dies and is restored from an old replica: copies of the new value can fall below `w`.
- During [rebalance](RebalanceRouting.md), nodes disagree on who holds the *n* copies; quorums stop overlapping.
- A read concurrent with a write may or may not see it; a later read can see the *old* value.
- A write that succeeded on some replicas and failed on others, totaling fewer than `w`, is not rolled back. A "failed" write can still appear on a later read.
- Wall-clock LWW can drop a later write from a slower clock.
- Two concurrent writes can land in different orders on different replicas — the [multi-leader conflict](../data-intensive-design/conflict-resolution.md) again.
- Sloppy quorum: the write set and the read set may be *different replica identities* (hint on D, read A+B).

Quorums adjust the **probability** of a stale read. They are not a proof of "always the latest value."

## Verified defaults (fetched 2026-09-13)

| Knob | Cassandra 5.0.8 / stable | Dynamo (2007 paper) |
|---|---|---|
| Replica count | per-keyspace RF; prod = `NetworkTopologyStrategy` | N on the preference list; common **3** |
| Durability / quorum | CL menu; do not assume a driver default | common **(N,R,W) = (3,2,2)** |
| Failure detection | `phi_convict_threshold` **8**; hints **3 h** | gossip membership |
| Catch-up / repair | incremental repair + Merkle; `gc_grace_seconds` **864000** | Merkle anti-entropy + hints |
| Read-on-replica | any replica; CL picks how many | R of N |
| Tokens | `num_tokens` **16** | Strategy-2 `Q >> N` (see [partitioning](Partitioning.md)) |
| Concurrency | `concurrent_reads/writes` **32** (tune: 16×drives / 8×cores) | — |

Those concurrency defaults are *thread pools on the replica*, not a quorum. Raising them does not raise `w`. A coordinator waiting on `LOCAL_QUORUM` still needs two acks; a saturated `concurrent_writes` pool just makes those acks late. Tune pools from disk/core counts after you have named CL; do not use pool size as a substitute for RF.

DynamoDB is **not** a column of this table. It is [single-leader](SingleLeaderReplication.md) Multi-Paxos per partition.

## Observability

Leaderless systems have no single apply order, so there is no Postgres-style lag number. Hint count is a weak health signal; operability still needs a number.

| Signal | What it means |
|---|---|
| **Hint backlog / hint window remaining** | Down replica is borrowing durability from coordinators. After 3 h (Cassandra default) new hints stop. `nodetool tpstats` / hint metrics. |
| **Repair age vs `gc_grace_seconds`** | Tombstone safety. Last successful incremental repair timestamp per range must be < 10 d (or your `gc_grace`). |
| **Read-repair vs digest mismatch rate** | How often a parallel read found siblings or stale copies. |
| **Per-partition heat** | One partition key is still one repair/compaction unit — [partitioning](Partitioning.md). |
| **Phi / local UP-DOWN** | Coordinator conviction. A flap here is not a cluster-wide membership change (by design). |
| **Client op duration** | Includes the coordinator's wait for CL. OTel `db.client.operation.duration` + shard bucket; do not label raw keys. |

Alert *shapes* (operator judgment, not vendor rules): hint window past halfway; repair age past half of `gc_grace`; digest-mismatch spike after a node returns.

## Tuning — RF=3, one DC, survive one node

Goal: read-your-writes inside one DC, survive one node, do not wait on WAN.

| Choice | W | R | Survives | Pays |
|---|---|---|---|---|
| `LOCAL_QUORUM` / `LOCAL_QUORUM` | 2 | 2 | 1 node in-DC | Intra-DC majority RTT |
| `ONE` / `ONE` | 1 | 1 | more availability | stale reads; not `W+R>RF` |
| `QUORUM` / `QUORUM` cross-DC RF=3+3 | 4 | 4 | 1 node globally | WAN on every op |
| `EACH_QUORUM` write + `LOCAL_QUORUM` read | maj/DC | 2 local | DC-local RYW after each-DC persist | write waits on every DC |

Hints: if p95 node-restarts are **20 min**, the **3 h** hint window covers them; if a rack outage is **8 h**, hints expire and you are on repair. Schedule incremental repair so the oldest unrepaired range is **< 5 days** (half of `gc_grace` 10 d) — margin for a failed repair window. Lowering `gc_grace` without tightening repair is how zombies appear. `num_tokens=16` with the 3.x+ allocator is the current default; do not jump to 256 on a new cluster (neighbour explosion — [partitioning](Partitioning.md)).

Write-rare / read-heavy can set `w = n`, `r = 1` — faster reads, any one failure blocks writes. The inequality is a *choice*, not a law.

Reads contact enough replicas to satisfy the level **plus speculative retry** (Cassandra): if the first replica is slow, the coordinator asks another. That is hedging on the read path, not a [retry storm](RetryBackoff.md) — but it is extra load on a sick replica. Bound it; do not stack an application retry of the same CL on top.

## Testing and operating

- **Hint expiry.** Take a replica down longer than `max_hint_window` (default 3 h). Confirm new hints stop and that incremental repair is what heals, not a coordinator reboot.
- **Zombie drill.** Delete a row, keep a replica down past `gc_grace_seconds` without repair, bring it back. The old row returning is the acceptance test for "repair period < `gc_grace`." Replace-from-scratch if the node missed the window.
- **Sloppy miss.** Write at `ONE` while A is down (hint on D); read A+B at `ONE` before read-repair. Stale is expected. Repeat at `LOCAL_QUORUM`/`LOCAL_QUORUM` and record whether *your* cluster still missed (sloppy + different replica sets).
- **Clock.** Skew one node past typical write spacing; LWW discard should be visible. NTP is load-bearing, not a hygiene item.
- **CL inheritance.** Open a session without setting CL. Do not assume `ONE` or `LOCAL_QUORUM` — driver defaults were not re-verified. Set it.
- **Decommission.** Confirm Cassandra will *not* drop a silent node from gossip by itself. Operator decommission / `replace_address_first_boot` is the membership API; gossip UP/DOWN is local.

## Alternatives that beat a quorum menu

| Situation | Prefer | Why |
|---|---|---|
| Linearizable money / uniqueness | [Single-leader](SingleLeaderReplication.md) consensus, or a consensus shard for those keys | `(3,2,2)` was a shopping-cart bet. |
| Write availability through a *region* partition, mergeable docs | [Multi-leader](MultiLeaderReplication.md) | Topology + merge, not R/W. |
| You wanted "no failover" and also RPO 0 | You cannot have both without majority persist | Leaderless + `ONE` is availability; Raft + majority is durability. |
| DynamoDB on the order form | [Single-leader](SingleLeaderReplication.md) per partition | Different product. |

## Placement

| Placement | What it owns | Trade-off |
|---|---|---|
| **Store-native** (Cassandra RF+CL, Riak, Scylla) | Correctness of copies *as a probability*. | App cannot "add linearizability" later without a migration. |
| **Smart client** (token-aware driver) | Skips a hop; caches the ring. | Every language needs a correct client; membership refresh lag is a consistency window. Dynamo clients refreshed membership every **10 s** in the paper. |
| **Any-node coordinator** | Client hits any replica; it fans out. | Extra hop; the coordinator's CL wait *is* the user-visible latency. |
| **Consensus for the map, leaderless for the data** | Split-brain-safe assignment ([rebalance](RebalanceRouting.md)). | Two mechanisms; gossip-only maps only if the store already accepts divergence. |

## Failure modes

| Mode | How it happens | What to do |
|---|---|---|
| **Sloppy quorum ≠ intersection** | Hinted write on D, read of A+B, A still stale. `W+R>N` assumed. | Read-repair + repair; do not claim linearizability. |
| **Clock-skew LWW** | A rewinded clock wins. | NTP (Cassandra docs require it); or version vectors / CRDTs. |
| **Tombstone zombie** | Node down > `gc_grace`, delete compacted away, node returns with the old row. | Repair period < `gc_grace`; replace-from-scratch if the node missed the window. |
| **Hint disk bomb** | Hint pile during a 3 h outage. Coordinator fills disk. | Throttle (`1024 KiB/s` is a starting point, not a target); page the replica. |
| **Wrong-family commit** | Cassandra `ONE` treated as "durable". | Name the durability in the SLO. Money rows go through `LOCAL_QUORUM` (or stricter). |
| **`ANY` write** | Succeeded on a hint; not readable. | Do not use `ANY` for a read-your-writes path. |
| **Rebalance during quorum** | Nodes disagree on who holds the *n* copies; quorums stop overlapping. | [Rebalance](RebalanceRouting.md); human commit on membership. |

A write that succeeded on some replicas and failed on others, totaling fewer than `w`, is not rolled back. A "failed" write can still appear on a later read.

## When not to go leaderless

You need linearizability, or the app cannot reconcile. Quorums are a probability-of-staleness bet. Dynamo's (3, 2, 2) was chosen for *Amazon shopping-cart* semantics (never lose an add-to-cart), not for a ledger. Uniqueness and "balance ≥ 0" belong on [single-leader](SingleLeaderReplication.md) (or a consensus shard), not here.

Do not pick leaderless because you wanted "no failover" and then treat `ONE`/`ONE` as HA. You bought availability *and* staleness.

Do not pick it because the AWS console says DynamoDB. That product is [single-leader](SingleLeaderReplication.md) per partition.

## Trade-offs

| Buy | Pay |
|---|---|
| Write while a replica is down; nothing to elect | Stale reads; no single apply order to graph |
| `(3,2,2)` / `LOCAL_QUORUM` overlap | Intra-DC majority RTT; still not linearizable |
| `ONE` / `ONE` | Availability; not `W+R>RF` |
| Sloppy quorum + hints | Intersection can miss; hints expire |
| Incremental repair + 10 d `gc_grace` | A missed repair window resurrects deletes |
| LWW (Cassandra) | Simple; NTP is load-bearing; concurrent writes discard |
| Token-aware client | One less hop; stale ring for the refresh interval |

Leaderless decides **how many copies you wait for**. It does not decide **an order**. [Conflict resolution](../data-intensive-design/conflict-resolution.md) decides what two concurrent writes become. [Repair](RebalanceRouting.md) decides whether a delete stays dead.

`n`, `w`, `r` are typically configurable. Common: odd `n` (3 or 5), `w = r = (n + 1) / 2`. You can set `w + r ≤ n` — more stale reads, lower latency, more availability through a partition. The database is unavailable for writes or reads only after reachable replicas drop below `w` or `r`. That is the availability you bought; it is also the staleness you accepted. Do not put a [breaker](CircuitBreaker.md) over "Cassandra" as one dependency when one token range is the sick unit.

## Leaves to siblings

| Sibling | What they take |
|---|---|
| [Quorums and fencing](../data-intensive-design/quorums-and-fencing.md) | Majority-as-death; fencing tokens — not `w + r > n`. |
| [Failover](Failover.md) | Health / RTO when you *do* have a leader (you do not, here). |
| [Conflict resolution](../data-intensive-design/conflict-resolution.md) | LWW vs siblings vs CRDT. |
| [Rebalance](RebalanceRouting.md) | Membership that must not reshuffle on transient failure; repair vs move. |
| [Single-leader](SingleLeaderReplication.md) | DynamoDB; any ledger / uniqueness path. |
| [Partitioning](Partitioning.md) | One value lives on only `n` of the cluster's nodes. |

## Sources

Verified 2026-09-13; URLs, provenance, and items left out (per-driver CL defaults, Dynamo PDF page numbers, Dynamo success-rate as an SLA) are in the [external research note](../../docs/research/sysdesign/b2-partition-replicate-external-research.md).

- Canon: DeCandia et al. SOSP 2007 *Dynamo*; [leaderless-replication.md](../data-intensive-design/leaderless-replication.md); [quorums-and-fencing.md](../data-intensive-design/quorums-and-fencing.md).
- Products: Cassandra architecture, 5.0.8 `cassandra.yaml`, hints, `ALTER TABLE` `gc_grace_seconds`. Historical DataStax 3.0 CL page cited only as *historical*.
- Do not cite DynamoDB developerguide as a leaderless default.
