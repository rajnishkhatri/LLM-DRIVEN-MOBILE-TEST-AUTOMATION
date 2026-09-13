---
type: research
title: 'Data partitioning & replication — external research (2026-09-13)'
description: >-
  Source-verified operational pass for catalog B2: partition-key families,
  rebalance/routing knobs, and the three replication styles (single-leader,
  multi-leader, leaderless) with product defaults (Postgres 17, Dynamo/DynamoDB,
  Cassandra 5, Kafka 4.3, etcd/Raft, MongoDB, CockroachDB), observability,
  worked calibration, and failure modes. Existing cases/ notes are linked, not
  rewritten.
tags: [research, system-design-patterns, B2, partition, replicate]
---

# Data partitioning & replication — external research (2026-09-13)

> **What this is.** The evidence pass behind catalog id **B2** (Group B, full operational bar). The existing DDIA-adjacent notes in `cases/data-intensive-design/` already own the vocabulary and the three-family taxonomy. This note does **not** re-derive them. It adds the *operational* layer the CircuitBreaker.md bar requires: verified product knobs, observability, tuning, worked calibration, and failure modes, fetched 2026-09-13.
>
> **Method.** Primary pages only for every numeric default (Postgres 17 docs, Cassandra 5.0.8 `cassandra.yaml` + architecture pages, Kafka 4.3 broker/topic configs, etcd v3.6 tuning, Dynamo SOSP 2007 PDF, DynamoDB USENIX ATC 2022 + current AWS developerguide, MongoDB current manual, CockroachDB v26.2 zone config, Raft ATC 2014, OpenTelemetry database semconv). Paraphrase only; numbers and identifiers reproduced exactly. Unverified items live in §11 and are **not** implied as fact.
>
> **Existing notes — link, do not rewrite** (main-repo `cases/`; same relative shape as the catalog of record, one extra `../` from this directory):
> [sharding-overview](../../../cases/data-intensive-design/sharding-overview.md) ·
> [replication-overview](../../../cases/data-intensive-design/replication-overview.md) ·
> [rebalancing](../../../cases/data-intensive-design/rebalancing.md) ·
> [request-routing](../../../cases/data-intensive-design/request-routing.md) ·
> [single-leader-replication](../../../cases/data-intensive-design/single-leader-replication.md) ·
> [multi-leader-replication](../../../cases/data-intensive-design/multi-leader-replication.md) ·
> [leaderless-replication](../../../cases/data-intensive-design/leaderless-replication.md) ·
> [hash-sharding](../../../cases/data-intensive-design/hash-sharding.md) ·
> [key-range-sharding](../../../cases/data-intensive-design/key-range-sharding.md) ·
> [quorums-and-fencing](../../../cases/data-intensive-design/quorums-and-fencing.md).

---

## 1. Scope and non-goals

**This note owns:** the *join* of partitioning and replication as one operational control plane. A record belongs to exactly one shard; that shard is then copied under one of the three replication families. The architect's job is choosing the partition key, the replica family, the durability knob that makes a "commit" mean something, and the rebalance/routing policy that will not cascade. Group B depth: mechanics, knobs with verified defaults, observability, tuning, worked calibration, failure modes.

**Out of scope (siblings own them):**

| Sibling | What they take |
|---|---|
| **B1** Scaling strategies | Vertical vs horizontal, autoscaling, Little's law. Partition/replica are *how* you go horizontal; B1 owns *when*. |
| **C3** Failover & split-brain | Leader election timeout as an *availability* mechanism, health checks, RTO/RPO, DNS/LB failover. This note only records the replica-family knobs that *feed* C3 (Postgres `wal_sender_timeout`, etcd election timeout, Kafka unclean election). |
| **C5** Routing vs load balancing | Stateless LB of interchangeable instances. This note covers *key-aware* shard routing only; C5 owns L4/L7, consistent-hash *proxies*, and sticky sessions. |
| **E13** Cells | Isolation of a *whole* failure domain (cell = deployable quantum). A cell *contains* partitions and replicas; it is not itself a shard. |
| **C8** Bulkhead / shuffle sharding | Isolation of *callers* from a bad dependency. Adjacent to partition isolation; different unit. |
| Existing cases | Vocabulary, three-family taxonomy, key-range vs hash, lag session guarantees, conflict resolution, secondary-index placement. Cited, not restated. |

**Non-goals.** No Concept. No skill family. No book-text reconstruction. No invented SLAs. Dynamo (2007, leaderless) and DynamoDB (2012+, single-leader Multi-Paxos per partition) are different systems — treating them as one is a vocabulary error already called out in [leaderless-replication](../../../cases/data-intensive-design/leaderless-replication.md).

---

## 2. Lineage / vocabulary

| Source (date) | What it named |
|---|---|
| Karger et al., STOC 1997 *Consistent Hashing and Random Trees* | Hash-ring placement: add/remove a node moves only its neighbours. The later "virtual node" (vnode) fix for imbalance is Dynamo, not Karger. |
| DeCandia et al., SOSP 2007 *Dynamo* | Preference list; N replicas on the ring; sloppy quorum + hinted handoff; Merkle-tree anti-entropy; vector clocks; gossip membership. Common production knob: **(N,R,W) = (3,2,2)**. Measured on "a couple hundred nodes". 99.9995% of requests succeeded without timeout in the paper's two-year window; **that figure is Dynamo-internal, not a product SLA**. |
| Ongaro & Ousterhout, USENIX ATC 2014 *Raft* | Single-leader consensus with randomized election timeout (paper example **150–300 ms**) so split votes are rare. Invariant: `broadcastTime ≪ electionTimeout ≪ MTBF`. Used by etcd, CockroachDB, TiDB, Kafka KRaft, YugabyteDB (see [request-routing](../../../cases/data-intensive-design/request-routing.md)). |
| Elhemali et al., USENIX ATC 2022 *Amazon DynamoDB* | Per-partition **Multi-Paxos** replication group; only the lease-holding leader serves writes and strongly consistent reads; any replica serves eventually consistent reads; request-router + metadata service; burst (300 s unused capacity) then adaptive capacity then global admission control. Prime Day 2021 peak **89.2 million requests/s** is a published event figure, not a customer SLO. |
| Cassandra architecture (current `stable` docs, fetched 2026-09-13) | Dynamo-style ring + LSM storage. **Last-write-wins** (client or coordinator timestamp, NTP assumed), not vector clocks. `NetworkTopologyStrategy` per-DC RF. Consistency *menu* (`ONE`/`QUORUM`/`LOCAL_QUORUM`/…) instead of raw R,W. |
| PostgreSQL 17 docs (fetched 2026-09-13) | Streaming physical replication is **async unless `synchronous_standby_names` is non-empty**. `synchronous_commit` default `on` then means "local flush"; with standbys named it means "standby durable flush". |
| Vogels / Terry (cited in [replication-lag](../../../cases/data-intensive-design/replication-lag.md)) | "Eventual consistency" has **no bound**. The operational substitutes are read-your-writes, monotonic reads, consistent prefix. |

**Two words that must not be collapsed.**

- **Partition / shard / tablet / range / chunk / vnode.** Same idea (a contiguous or hashed slice of the keyspace owned by a replica set). Product names: DynamoDB *partition*, Cassandra *token range*, MongoDB *chunk/range*, CockroachDB *range*, Kafka *partition*, Citus *shard*, Vitess *shard*.
- **Replica family ≠ consensus.** Single-leader *streaming* (Postgres) can lose acknowledged writes on failover. Single-leader *Raft/Paxos* (etcd, Cockroach, DynamoDB, Kafka ISR+KRaft) commits only after a majority persists. Leaderless quorums (`w + r > n`) make staleness *unlikely*, not linearizable — see [leaderless-replication](../../../cases/data-intensive-design/leaderless-replication.md) and [quorums-and-fencing](../../../cases/data-intensive-design/quorums-and-fencing.md).

---

## 3. Mechanics

### 3.1 Partitioning — two families, one compromise

The taxonomy is already in [sharding-overview](../../../cases/data-intensive-design/sharding-overview.md), [key-range-sharding](../../../cases/data-intensive-design/key-range-sharding.md), [hash-sharding](../../../cases/data-intensive-design/hash-sharding.md). Operational restatement:

| Family | Placement | Cheap query | Failure mode | Rebalance unit |
|---|---|---|---|---|
| **Key range** | Shard owns `[min, max)` of the partition key. MongoDB default range size **128 MB**; CockroachDB splits at **512 MiB**, merges below **128 MiB**. | Range scan / `Query` inside the key. | Sequential keys (timestamps, autoincrement) write one hot shard. | Split the range; move one child. |
| **Hash** | `hash(key)` then map. Cassandra default partitioner **Murmur3Partitioner** (cannot change without reload). DynamoDB hashes the partition key internally. | Point get by key. | `hash % N` reshuffles almost everything when N changes. Celebrity key still hashes to one shard — [hot spots](../../../cases/data-intensive-design/sharding-hot-spots.md). | Move whole virtual shards, or walk the ring (consistent hashing). |
| **Composite** | Hash (or tenant) prefix + sorted suffix. DynamoDB partition key + sort key = *item collection*. | Range *inside* one partition key. | Monotonic sort key defeats split-for-heat (below). | Split by sort-key cut, unless an LSI pins the collection to one partition. |

**Fixed-shard vs ring.** [hash-sharding](../../../cases/data-intensive-design/hash-sharding.md) already contrasts `mod N`, a fixed shard count ≫ node count, hash ranges, and consistent hashing. Dynamo §6 evaluated decoupling partition *identity* from *placement*: Q equal hash ranges, T tokens per node, `Q >> N` and `Q >> S·T`. Cassandra 3.x+ dropped the 2.x default of **256** random vnodes (too many neighbours → correlated unavailability) for a deterministic allocator; current `cassandra.yaml` default **`num_tokens = 16`**. Trade-off: more vnodes = smoother add/remove, more neighbour combinations that lose a token range, slower repair.

**Per-partition throughput caps are a first-class knob, not a footnote.** DynamoDB documents that **each physical partition** is designed for **3,000 read units/s and 1,000 write units/s** (1 RCU = one strongly consistent 4 KB read/s, or two eventually consistent; 1 WCU = one 1 KB write/s). A 20 KB item costs 5 RCU on a consistent read → 600 consistent reads/s to that item before the partition cap. Throttling reason `KeyRangeThroughputExceeded` means the *partition* is saturated while table-level capacity is still free. Burst retains up to **five minutes (300 s)** of unused capacity (best-effort; AWS says the detail may change). Adaptive capacity boosts a hot partition and can isolate a single hot item up to the same 3,000/1,000 cap; it **will not** split an item collection that has an LSI, and split-for-heat is **not beneficial** when the sort key only ever increases (every new write lands on the newest child). LSI item collections are capped at **10 GB** (the documented maximum size of a partition); without an LSI there is no documented upper bound on sort-key cardinality.

### 3.2 Combining partition + replica

Independence is the useful lie: the sharding scheme and the replica family *compose*, but failover, routing, and rebalance couple them.

```
key ──► partition function ──► shard S
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
              single-leader   multi-leader   leaderless
              (1 writer +        (N writers,    (N writers
               log to N-1)        conflicts)     in parallel)
```

Each shard is its own replica set. A node commonly **leads some shards and follows others** ([sharding-overview](../../../cases/data-intensive-design/sharding-overview.md)). That is why a "the primary is down" incident is usually "the leaders of shards {S17, S44, S91} are on the dead node" — blast radius = shards whose leader lived there, not the whole dataset. Cells (E13) push the same idea up one level: a cell failure takes a *slice of users*, not a random set of hash ranges, if the partition key is cell-aligned.

### 3.3 Single-leader — streaming vs consensus

Mechanics live in [single-leader-replication](../../../cases/data-intensive-design/single-leader-replication.md). Two implementations that share the *shape* and not the *commit* meaning:

**A. Streaming / WAL shipping (Postgres 17).** Leader writes WAL, standbys stream it. Default is **asynchronous**: `synchronous_standby_names` empty → commits do not wait for any replica. `synchronous_commit` default `on` then only waits for *local* flush. Naming one or more standbys turns `on` into "standby has flushed the commit record to durable storage"; `remote_write` waits for OS write (survives Postgres crash, not OS crash); `remote_apply` waits until the commit is replayed and visible on the standby (causal read-your-writes on that standby; larger commit delay). `local` / `off` opt a transaction out of waiting. Sync to *every* standby is the failure mode already named in the case note: one slow replica stalls all writes. Production shape is **one sync + the rest async** (semisync), or a majority if you have moved to Raft.

Slots vs `wal_keep_size`: default `wal_keep_size = 0` keeps **no extra** WAL for standbys. A disconnected replica that falls behind the last checkpoint is done unless (a) a replication slot holds WAL, (b) `wal_keep_size` is large enough, or (c) a WAL archive exists. Slots can fill `pg_wal`; `max_slot_wal_keep_size` default **-1** = unlimited. `max_wal_senders` default **10**, `max_replication_slots` default **10**. `wal_sender_timeout` / `wal_receiver_timeout` default **60 s**. `hot_standby` default **on**; `hot_standby_feedback` default **off** (on = fewer query cancels, more primary bloat). `max_standby_streaming_delay` default **30 s** (then cancel the conflicting standby query). `wal_receiver_status_interval` default **10 s** — this is what feeds `pg_stat_replication`.

**B. Consensus-backed single-leader (Raft / Multi-Paxos).** The leader is *elected*; a write is committed when a **majority** persists it. DynamoDB ATC 2022: any replica may start an election; the winner holds a **lease** and will not serve writes or consistent reads until the previous lease expires (fencing — C3 / [quorums-and-fencing](../../../cases/data-intensive-design/quorums-and-fencing.md)). A replication group is typically **three storage replicas across AZs**; the paper adds *log replicas* (Paxos acceptors without the B-tree) to restore a write quorum faster than cloning a full replica. CockroachDB: each *range* is a Raft group, `num_replicas` default **3** (5 for `.meta` / `.liveness` / `.system` and for multi-region survive-region). etcd: heartbeat **100 ms**, election timeout **1000 ms**, same on every member; election timeout ≥ **10× RTT**; hard cap **50 s** (global-cluster only). Raft paper's own example interval is **150–300 ms** randomized — etcd chose a more conservative 1 s default for LAN.

**Kafka** is single-leader *per partition*. Broker defaults (Kafka 4.3 docs): `default.replication.factor = 1`, `num.partitions = 1`, `min.insync.replicas = 1`, `unclean.leader.election.enable = false`. Those defaults are **dev-safe and prod-wrong**. The documented production pairing is RF **3**, `min.insync.replicas` **2**, producer `acks=all`. With `acks=all`, *every current ISR member* must ack, and if `|ISR| < min.insync.replicas` the producer gets `NotEnoughReplicas` / `NotEnoughReplicasAfterAppend`. Messages are not visible to consumers until they are on all in-sync replicas *and* the min-ISR condition holds. Unclean election (default off since 0.11.0.0) is the durability-vs-availability switch: a non-ISR leader can restore writes at the cost of losing committed messages. In KRaft, a dynamic enable waits for a periodic thread (docs: default **5 minutes**) unless `kafka-leader-election.sh --unclean` is run.

### 3.4 Multi-leader

Mechanics live in [multi-leader-replication](../../../cases/data-intensive-design/multi-leader-replication.md) and [conflict-resolution](../../../cases/data-intensive-design/conflict-resolution.md). Operational points this note adds:

- **Sync multi-leader is single-leader in disguise.** A partition between two sync leaders blocks writes the same way an unreachable primary does. The only interesting mode is *async* multi-leader.
- **Topologies (all-to-all / circular / star)** are already tabulated in the case. Operational failure: circular and star need forwarding and *manual* rewire around a dead hop; all-to-all allows messages to **overtake** (insert on L1, update on L3, L2 sees the update first). Version vectors detect that; wall clocks do not. Cassandra's LWW is a deliberate simplification that *depends on NTP* — the architecture page says so.
- **When it pays:** geo write-availability, offline devices, collaboration. **When it does not:** uniqueness constraints ("username is unique", "balance ≥ 0") are not enforceable — each leader can accept a locally valid write. Prefer a single leader, or a consensus shard for the constrained keys only (a common hybrid: multi-leader for the document, single-leader for the uniqueness index).
- **DynamoDB global tables** are a managed multi-region *single-leader-per-partition* story plus async cross-region replication, not Dynamo-style leaderless. Conflict policy is last-writer-wins on item version (do not invent the exact clock; see §11).

### 3.5 Leaderless

Mechanics live in [leaderless-replication](../../../cases/data-intensive-design/leaderless-replication.md). Operational restatement with product numbers:

Dynamo writes the first N *healthy* preference-list nodes (**sloppy quorum**). If A is down, the write intended for A is stored on D with a *hint*; D later hands it back. Cassandra: `hinted_handoff_enabled` default **true**, `max_hint_window` default **3h**, `hinted_handoff_throttle` default **1024 KiB/s** per delivery thread (divided by cluster size). Hints that outlive the window are gone — **repair** is the backstop, not a hint.

Cassandra consistency is a menu over Dynamo's R,W. `QUORUM` = `n/2 + 1` of RF (RF=3 → 2). `LOCAL_QUORUM` = majority in the coordinator's DC (the geo-latency knob). `EACH_QUORUM` = majority in *every* DC. `ANY` (writes only) may succeed on a hint alone — not readable until a real replica has it. Writes always fan out to all replicas; the level is how many acks the coordinator waits for. Reads contact enough replicas to satisfy the level (plus speculative retry). Intersection `W + R > RF` is the *usual* visibility argument; sloppy membership, hinted handoff, clock skew, and partial quorum on different replica sets are why it is not a linearizability proof.

Anti-entropy: Dynamo Merkle trees over the whole keyspace; Cassandra adds **sub-range** and **incremental** repair. Tombstones live `gc_grace_seconds` default **864000 (10 days)**. If a node is down longer than that and you have not repaired, a delete can **resurrect** (zombie). Repair period must be **< gc_grace**. `phi_convict_threshold` default **8** (Phi accrual); UP/DOWN is a *local* decision, not gossipped. Cassandra will not remove a node from gossip without an operator decommission or `replace_address_first_boot` — intentional, to avoid needless rebalance on transient failure (same instinct as [rebalancing](../../../cases/data-intensive-design/rebalancing.md)).

### 3.6 Rebalance and request routing (operational delta)

Do not rewrite [rebalancing](../../../cases/data-intensive-design/rebalancing.md) or [request-routing](../../../cases/data-intensive-design/request-routing.md). Add only product knobs:

- **MongoDB balancer** (current manual): always on by default. A collection is balanced if the data-size difference between shards is **< 3× configured range size**. Default range **128 MB** → migrate when the gap is **≥ 384 MB**. Since 6.0.3 automatic *split* is off; chunks may *exceed* 128 MB (docs mention seeing a **1 TB** chunk). `chunkSize` now mainly caps how much one migration moves. Allowed range size **1–1024 MB**. Smaller → more frequent I/O; larger → fewer metadata updates, jumbo-chunk risk.
- **CockroachDB**: split at 512 MiB, merge below 128 MiB; automatic rebalance on node join/leave, honoring zone constraints. Docs' own rationale: small enough to move, large enough that keys accessed together stay together.
- **Dynamo / Cassandra**: membership change is **explicit** (admin join/decommission). Transient failure must *not* reshuffle the ring. Gossip (Cassandra, Riak) vs consensus map (etcd/ZooKeeper, MongoDB config servers, Kafka KRaft, TiDB/Yugabyte/Scylla built-in Raft) is the C3/C5 boundary: gossip is cheaper and admits split-brain maps; use it only if the store already lives with weak consistency.
- **Three routing placements** (any-node forward / routing tier / smart client) stay in the case. Dynamo named both: load-balancer → random coordinator, or partition-aware client that skips a hop (Dynamo clients refreshed membership every **10 s** in the paper). DynamoDB put the map in a **metadata service** consulted by a **request-router** fleet; storage nodes are source of truth and push changes up.

---

## 4. Verified defaults / standards

Fetched 2026-09-13. Empty cells = not a default of that product.

| Knob | Postgres 17 | Cassandra 5.0.8 / stable | Kafka 4.3 | etcd (v3.6 docs) | DynamoDB (current + ATC 2022) | MongoDB current | CockroachDB v26.2 |
|---|---|---|---|---|---|---|---|
| Partition / range size | n/a (one instance = one replica set unless Citus/etc.) | token ranges via `num_tokens` **16** | `num.partitions` **1** | n/a (whole keyspace replicated) | managed; ~**10 GB** physical partition; LSI collection **10 GB** hard | chunk/range **128 MB** | `range_max_bytes` **512 MiB**, `range_min_bytes` **128 MiB** |
| Replica count | 1 primary + N standbys (you attach them) | per-keyspace RF; prod = `NetworkTopologyStrategy` | `default.replication.factor` **1** | cluster size (odd; 3 or 5 typical, not a single default) | 3 storage replicas / AZ-spread + optional log replicas | replica-set members (you choose) | `num_replicas` **3** (5 for meta/liveness/system) |
| Durability / quorum | `synchronous_commit=on`; sync repl **off** until `synchronous_standby_names` set | CL menu; cqlsh/driver default historically **ONE** (DataStax 3.0 page — confirm per driver, §11) | `min.insync.replicas` **1**; `acks` is a *producer* setting | majority of members | write ack after quorum of WAL persists; consistent read = leader | majority write concern is a client choice | Raft majority of `num_replicas` |
| Failure detection | `wal_sender_timeout` **60 s**, `wal_receiver_timeout` **60 s** | `phi_convict_threshold` **8**; hints **3 h** | ISR + replica lag; unclean election **false** | heartbeat **100 ms**, election **1000 ms** | lease + peer failure-detect; new leader waits out old lease | election timeout (replica-set; §11) | Raft per range |
| Catch-up / repair | replication slot or archive; `wal_keep_size` **0** | incremental repair + Merkle; `gc_grace_seconds` **864000** | replica fetch; ISR shrink | snapshot every **10 000** changes (v2 backend note) | autoadmin + log replicas | balancer + range deleter | automatic split/merge/rebalance |
| Read-on-replica | `hot_standby=on`; feedback **off**; cancel after **30 s** | any replica; CL picks how many | consume any ISR (after min-ISR) | linearizable by default (Raft) | eventually consistent = any replica | secondary reads optional | leaseholder serves (follower reads are a separate feature; §11) |
| Concurrency | — | `concurrent_reads/writes` **32** (tune: 16×drives / 8×cores) | — | disk/CPU priority notes (ionice, `performance` governor) | GAC + per-node token buckets | — | — |

**OpenTelemetry (database semconv, live spec + v1.38.0 source, 2026-09-13).** Client histogram `db.client.operation.duration` (unit `s`, stable; recommended buckets `[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5, 10]`). Required attribute `db.system.name`; `db.operation.name` conditionally required. This is the *caller-side* duration of the API call including internal retries. It does **not** replace store-native lag/ISR/hint metrics — emit both. Conventions marked stable for MariaDB, SQL Server, MySQL, PostgreSQL; Cassandra/Mongo/Cosmos notes exist as system-specific.

---

## 5. Observability

Partition+replica incidents are almost never "the database is down". They are *this key's shard*, *this leader*, *this DC's quorum*, or *this rebalance*. Dashboards that average across shards hide the failure.

| Signal | What it means | Where it lives |
|---|---|---|
| **Replication lag** (write / flush / apply LSN or bytes/time) | Async replica staleness. Apply ≫ flush = replay bottleneck (CPU/IO/conflicts), not the network. | Postgres `pg_stat_replication` (`sent_lsn`, `write_lsn`, `flush_lsn`, `replay_lsn`, `*_lag`); updated at least every `wal_receiver_status_interval` (10 s). |
| **Commit wait** | Sync replica is the write SLO. | Postgres wait events `SyncRep`; `synchronous_commit=remote_apply` wait includes replay. |
| **ISR size / under-replicated partitions** | Kafka durability remaining. `\|ISR\| < min.insync.replicas` → writes fail with `acks=all`. | Broker metrics; `UnderReplicatedPartitions`. |
| **Hint backlog / hint window remaining** | Down replica is borrowing durability from coordinators. After 3 h (Cassandra default) new hints stop. | `nodetool tpstats` / hint metrics; alert at 50% of `max_hint_window`. |
| **Repair age vs `gc_grace_seconds`** | Tombstone safety. | Last successful incremental repair timestamp per range; must be < 10 d (or your `gc_grace`). |
| **Per-partition / per-key consumed RCU/WCU** | Hot key. Table-level ConsumedCapacity being "fine" is the usual lie. | DynamoDB CloudWatch + Contributor Insights; `KeyRangeThroughputExceeded` vs `TableWriteProvisionedThroughputExceeded`. |
| **Shard size skew / chunk imbalance** | Balancer should have fired, or a jumbo chunk cannot move. | MongoDB `sh.status`, balancer window; Cockroach range-size histograms. |
| **Leader distribution** | One node holds too many shard leaders → CPU/WAL tail. | Kafka `PreferredReplicaImbalance`; Postgres only one leader (whole instance); Cockroach/Yugabyte leaseholder maps. |
| **Election rate / term** | etcd/Raft flapping. | etcd `etcd_server_leader_changes_seen_total`; disk `wal_fsync` duration (etcd is disk-latency sensitive — missed heartbeat → spurious election). |
| **Client op duration** | User-visible. | OTel `db.client.operation.duration` by `db.system.name` + `db.operation.name` + **shard / partition key hash bucket** (low cardinality — do not label raw keys). |

**Alert shapes (own formulations, not vendor rules — see §11):** lag p99 > read-your-writes SLO for 5 min; ISR < RF for 2 min; hint window > 50%; repair age > 0.5 × `gc_grace`; `KeyRangeThroughputExceeded` burst; etcd leader changes > N/15 min; balancer running through peak QPS.

---

## 6. Tuning and worked calibration

Defaults are *safe for a laptop*. Production values are derived from RTT, item size, and the failure you will actually take.

### 6.1 Partition-key / hot-key calibration (DynamoDB numbers)

Given: items **20 KB**, target **4 000 writes/s** to one logical entity (a "hot user"), eventually consistent reads not in this budget.

1. WCU per write = `ceil(20 KB / 1 KB) = 20`.
2. One partition's write cap = **1 000 WCU/s** → `floor(1000 / 20) = 50` writes/s to that key *even after adaptive isolation*.
3. Write-shard count `N = ceil(4000 / 50) = 80` random suffixes (`userId#00` … `userId#79`).
4. Read path pays scatter (`N` gets) or a precomputed rollup. Trade-off: write scale vs read amplification — already the [hot spots](../../../cases/data-intensive-design/sharding-hot-spots.md) lesson.
5. If the sort key is a timestamp, **do not** expect split-for-heat to save you; N suffixes *are* the design. An LSI on that table would also pin each suffix's collection to **10 GB**.

Same arithmetic applies to a Cassandra partition (one partition key = one storage partition that must compact/repair as a unit) even though Cassandra does not publish a 1 000 WCU number — the unit of heat is still "one partition key".

### 6.2 Leaderless quorum calibration (Cassandra RF=3)

Goal: read-your-writes inside one DC, survive one node, do not wait on WAN.

| Choice | W | R | Survives | Pays |
|---|---|---|---|---|
| `LOCAL_QUORUM` / `LOCAL_QUORUM` | 2 | 2 | 1 node in-DC | Intra-DC majority RTT |
| `ONE` / `ONE` | 1 | 1 | more availability | stale reads; not `W+R>RF` |
| `QUORUM` / `QUORUM` cross-DC RF=3+3 | 4 | 4 | 1 node globally | WAN on every op |
| `EACH_QUORUM` write + `LOCAL_QUORUM` read | maj/DC | 2 local | DC-local RYW after each-DC persist | write waits on every DC |

Hints: if p95 node-restarts are **20 min**, the **3 h** hint window covers them; if a rack outage is **8 h**, hints expire and you are on repair. Schedule incremental repair so the oldest unrepaired range is **< 5 days** (half of `gc_grace` 10 d) — margin for a failed repair window. Lowering `gc_grace` without tightening repair is how zombies appear. `num_tokens=16` with the 3.x+ allocator is the current default; do not jump to 256 on a new cluster (neighbour explosion).

### 6.3 Single-leader streaming calibration (Postgres 17)

Measure intra-AZ RTT (example **0.5 ms**) and cross-region RTT (example **70 ms**) with ICMP *and* with a WAL-sized payload — etcd's own advice is "use ping", which under-reads disk. Then:

| Deploy | `synchronous_standby_names` | `synchronous_commit` | What a COMMIT means | Failover (C3) |
|---|---|---|---|---|
| Laptop / CI | empty | `on` (default) | local flush only | lose unflushed? no — local flush happened; lose *replica* data |
| One-AZ HA | `FIRST 1 (az1)` | `on` | primary + 1 standby durable | promote the sync standby; RPO ≈ 0 for that pair |
| Read scale in-region | empty or `FIRST 1` | `on` for money rows, `local` for telemetry | per-transaction durability | session-sticky read-your-writes ([replication-lag](../../../cases/data-intensive-design/replication-lag.md)) |
| Cross-region | do **not** name the remote as sync | `on` locally | remote is async | accept RPO = replay_lag; or move the workload to Raft/global tables |

Always create a **replication slot** (or archive). `wal_keep_size=0` plus a 2-hour network blip is a full base-backup. Cap the slot with `max_slot_wal_keep_size` once you know peak WAL/hour × max-acceptable disconnect, or a stuck slot fills the disk and takes the primary down — the failure mode of "unlimited" (`-1`). Turn `hot_standby_feedback` on only after you measure primary bloat; the 30 s cancel (`max_standby_streaming_delay`) is the other side of that trade-off.

### 6.4 Raft timing calibration (etcd)

Invariant from the Raft paper + etcd tuning page:

`heartbeat ≈ 0.5–1.5 × RTT`, `election_timeout ≥ 10 × RTT`, same values on every member, election timeout ≤ **50 000 ms**.

| Measured RTT | Heartbeat | Election timeout | Comment |
|---|---|---|---|
| 2 ms LAN | **100 ms** (default) | **1000 ms** (default) | 50× / 500× RTT — conservative, fine |
| 10 ms metro | 10–15 ms | ≥ 100 ms (etcd example) | defaults still work; lowering heartbeat saves little |
| 130 ms continental US (etcd's own figure) | ~130–200 ms | ≥ 1 300 ms; etcd discusses **5 s** as a safe *global* RTT upper and **50 s** as the election cap | defaults will **false-elect** |
| 350–400 ms US–Japan (etcd's figure) | do not run one etcd cluster across this | — | put a consensus cluster *in* each region; replicate the *data* with a different family |

Disk `fsync` p99 must sit well under the heartbeat. etcd's docs call this out explicitly: other processes' disk IO → missed heartbeats → leader loss. `ionice` / dedicated disk is the knob, not a larger election timeout (that only hides the problem and lengthens failover — C3).

### 6.5 Kafka partition + ISR calibration

Start from the documented production triple: **RF=3, min.insync.replicas=2, acks=all**. Then size partitions for *throughput and consumer parallelism*, not for "more is better":

- Partition count ≥ max downstream consumer instances you want in parallel (one consumer per partition per group).
- Each partition is a single-leader log; more partitions = more open files, more replication traffic, longer recovery.
- Broker defaults (`RF=1`, `min.ISR=1`, `num.partitions=1`) acknowledge a write on **one** disk. That is not HA.
- One broker down: ISR=2 ≥ 2, writes live. Two brokers down: ISR=1 < 2, writes stop. That *is* the design. Enabling unclean election restores writes and **drops** the messages that only lived on the dead ISR — C3's availability/durability fork.

### 6.6 Rebalance window (MongoDB / the human-in-the-loop rule)

MongoDB will migrate when shard data differs by **384 MB** at the default 128 MB range. That is *size* balance, not *QPS* balance — a 100 MB celebrity chunk will not move, and should not (moving it just relocates the hot key). Pre-split and pre-move before a named surge ([rebalancing](../../../cases/data-intensive-design/rebalancing.md)): the automation-plus-false-death cascade is still the dominant failure. Trade-off: a commit step is slower than autoscale and prevents the cluster from rebalancing *onto* an overloaded node that looks dead.

---

## 7. Placement

Where the mechanism sits, and what that choice costs.

| Placement | What it owns | Trade-off |
|---|---|---|
| **Store-native** (Cassandra RF+CL, Postgres sync standbys, Kafka ISR, Cockroach zones, DynamoDB partitions) | Correctness of copies. | App cannot "add HA" later without a migration. |
| **Coordinator / router** (MongoDB `mongos`, DynamoDB request router, Vitess, Citus coordinator, any-node forward) | Key → node map. | Router fleet is a new HA problem; stale map during cutover drops in-flight requests ([request-routing](../../../cases/data-intensive-design/request-routing.md)). |
| **Smart client** (Dynamo partition-aware library, Cassandra token-aware driver) | Skips a hop; caches the ring. | Every language needs a correct client; membership refresh lag (Dynamo paper: 10 s poll) is a consistency window. |
| **App-level write sharding** (random suffix, time bucket) | Beats a hot key the store cannot split. | Read path becomes scatter or a rollup job. |
| **Consensus sidecar** (etcd/ZooKeeper for the *map*, not the data) | Split-brain-safe assignment. | The data plane can still be leaderless; the control plane should not be. |
| **Cell boundary** (E13) | Align partition key with deployable quantum. | Cross-cell queries become federated; worth it when you need a hard blast-radius cap. |

A circuit breaker over "the database" (C1) without **resource differentiation** (Azure's term; Brooker on shard-blind breakers) trips the healthy shards with the sick one. Granularity = endpoint + shard, not "Postgres".

---

## 8. Failure modes and when-not-to-use

**Failure modes of the mechanism itself**

| Mode | How it happens | What to do |
|---|---|---|
| **Hot key / hot range** | Celebrity, monotonic key, `Scan` walking one range at 3 000 RCU. Adaptive capacity cannot split a monotonic sort key or an LSI collection. | Redesign the key; write-shard; parallel scan. Adding table-level WCU does nothing. |
| **Wrong-family commit** | Async Postgres / Kafka `acks=1` / Cassandra `ONE` treated as "durable". Promote or unclean-elect and the client-visible write is gone. | Name the durability in the SLO. Money rows go through sync / majority / `LOCAL_QUORUM`. |
| **Sloppy quorum ≠ intersection** | Hinted write on D, read of A+B, A still stale. `W+R>N` assumed. | Read-repair + repair; do not claim linearizability. |
| **Clock-skew LWW** | Cassandra / some multi-leader products. A rewinded clock wins. | NTP (Cassandra docs require it); or version vectors / CRDTs ([conflict-resolution](../../../cases/data-intensive-design/conflict-resolution.md)). |
| **Tombstone zombie** | Node down > `gc_grace`, delete compacted away, node returns with the old row. | Repair period < `gc_grace`; replace-from-scratch if the node missed the window. |
| **Slot / hint disk bomb** | Unlimited Postgres slot (`max_slot_wal_keep_size=-1`) or hint pile during a 3 h outage. Primary or coordinator fills disk. | Cap the slot; page the replica; throttle hints (`1024 KiB/s` is a starting point, not a target). |
| **Rebalance cascade** | Autodetect death → move data → remaining nodes look dead → more moves. | Human commit ([rebalancing](../../../cases/data-intensive-design/rebalancing.md)); disable balancer during incidents. |
| **Map split-brain** | Two coordinators, two owners of shard S. | Consensus for the map (C3); fencing token on the storage side ([quorums-and-fencing](../../../cases/data-intensive-design/quorums-and-fencing.md)). Gossip-only maps only on stores that already accept divergence. |
| **False Raft election** | Election timeout ≤ disk/network p99. | Measure fsync; dedicated disk; raise timeout with RTT, not with hope. |
| **Unclean / async promote** | Availability win, durability loss. | Product decision, recorded in an ADR, tested. Not a Tuesday default. |
| **Secondary-index surprise** | Local index = scatter/gather; global index = multi-shard write. GSI throttle back-pressures the DynamoDB base table. | [sharding-secondary-indexes](../../../cases/data-intensive-design/sharding-secondary-indexes.md). |
| **Cross-shard write** | One shard commits, the other does not. | Avoid; or distributed txns / sagas (B5), not "retry until it looks fine". |

**When not to shard.** One machine still holds the data *and* the write rate. Sharding is heavyweight ([sharding-overview](../../../cases/data-intensive-design/sharding-overview.md)): irreversible-looking partition key, secondary-index tax, distributed transactions. Prefer vertical scale (B1) + read replicas.

**When not to multi-lead.** You need uniqueness or a non-negative invariant. Sync multi-leader buys you the conflicts *and* the partition unavailability.

**When not to go leaderless.** You need linearizability, or the app cannot reconcile. Quorums are a probability-of-staleness bet. Dynamo's (3,2,2) was chosen for *Amazon shopping-cart* semantics (never lose an add-to-cart), not for a ledger.

**When not to automate rebalance.** Detection can be wrong. Pre-split for calendar events; require a commit step if a false death can cascade.

---

## 9. Cross-links

**Catalog siblings.** B1 (when to scale out). C3 (failover, health, split-brain, RTO/RPO — consumes the timeouts in §4). C5 (stateless LB vs key-aware routing). C1 (breakers must be per-shard). C8 (shuffle sharding / bulkheads). E13 (cells wrap this note's units). B3 (cache stampede after a shard move). B5 / B7 (cross-shard writes, CDC from the replication log).

**Existing cases (main repo, do not rewrite).** The ten files listed in the header, plus [replication-lag](../../../cases/data-intensive-design/replication-lag.md), [replication-logs](../../../cases/data-intensive-design/replication-logs.md), [conflict-resolution](../../../cases/data-intensive-design/conflict-resolution.md), [detecting-concurrent-writes](../../../cases/data-intensive-design/detecting-concurrent-writes.md), [sharding-hot-spots](../../../cases/data-intensive-design/sharding-hot-spots.md), [sharding-secondary-indexes](../../../cases/data-intensive-design/sharding-secondary-indexes.md), [sharding-multitenancy](../../../cases/data-intensive-design/sharding-multitenancy.md).

---

## 10. Recommended split into future cards

This file stays one deep research note. When Concepts are cut, do **not** ship B2 as a single card — the CircuitBreaker bar applied to five mechanisms produces an unreadable Concept. Proposed ids:

| Future id | Title | Owns | Leaves behind |
|---|---|---|---|
| **B2a** | Partitioning (key-range, hash, composite, hot keys) | Partition-key design, DynamoDB 3k/1k + split-for-heat, Cassandra tokens, Mongo chunk size, Cockroach ranges, write-sharding arithmetic (§6.1). Links key-range / hash / hot-spots cases. | Replica family. |
| **B2b** | Single-leader replication | Streaming vs Raft/Paxos commit meaning. Postgres 17 knobs, Kafka ISR, etcd timing, DynamoDB Multi-Paxos lease. Worked calibrations §6.3–6.5. | Failover runbooks → C3. |
| **B2c** | Multi-leader replication | Async-only scope, topologies, when uniqueness dies, managed global tables vs true multi-writer. | Conflict algorithms → existing conflict-resolution case. |
| **B2d** | Leaderless replication | Sloppy vs strict quorum, Cassandra CL menu, hints 3 h, repair vs `gc_grace`, Dynamo (3,2,2). Calibration §6.2. | Fencing / majority-as-death → C3 + quorums-and-fencing. |
| **B2e** | Rebalance & request routing | Balancer thresholds, human-in-the-loop, three routing placements, gossip vs consensus maps, cutover. Calibration §6.6. Overlaps C5 — B2e is *key-aware* and *stateful*; C5 is interchangeable instances. | Cell topology → E13. |

A later Concept index page can keep the join diagram in §3.2 and point at B2a–e. Do not split the *research* file; the supervisor asked for one deep note plus this proposal.

---

## 11. Uncertain / left out (excluded from any future Concept)

- Dynamo paper PDF extracted via HTML conversion; (3,2,2), sloppy quorum, 99.9995% success, "couple hundred nodes", 300 ms / 99.9% / 500 rps *target*, 10 s client membership refresh, and Strategy-2 `Q >> N` are from that text. Page-level section numbers not re-checked against a print SOSP proceedings PDF.
- DataStax Cassandra 3.0 page says CL defaults to `ONE`; Cassandra 5 driver/session defaults were **not** re-verified per language driver (Java/Python/gocql may differ). Treat "default ONE" as *historical / cqlsh*, not universal.
- `gc_grace_seconds = 864000` verified on Cassandra current `ALTER TABLE` reference; older 3.11 compaction page agrees. Not re-read from 5.0.8 source.
- DynamoDB burst "up to 300 seconds" is documented with "these burst capacity details might change". ATC 2022 adaptive-capacity "eliminated over 99.99% of throttling due to skewed access" is the paper's internal claim, not a customer SLO.
- DynamoDB global-table conflict clock (HLC vs wall vs per-item version) not pinned to a primary page this pass.
- MongoDB replica-set election timeout / `settings.electionTimeoutMillis` default not fetched (C3).
- CockroachDB follower-reads staleness window and exact lease duration not fetched.
- Citus default shard count, Vitess default shard count, Yugabyte tablet split thresholds: not fetched.
- MySQL Group Replication / InnoDB Cluster and EDB Postgres Distributed knobs: not fetched; multi-leader products are named in the existing case only.
- Patroni / pg_auto_failover fencing behaviour: C3.
- Kafka `acks` *producer* default in 4.x clients (historically `acks=all` in recent clients, was `1`) — not re-verified per client language this pass. The *broker* `min.insync.replicas=1` *is* verified.
- etcd v3.6 vs v3.8 tuning pages agree on 100/1000 ms; which minor is "current" on etcd.io can shift. Snapshot-count **10 000** is documented on the v2-backend paragraph of the tuning page — v3 backend snapshot policy not separately verified.
- OTel `db.client.operation.duration`: GitHub v1.38.0 source says **required**; live `opentelemetry.io` spec page says **recommended**. Use the live spec wording until the versions are reconciled.
- PromQL / alert thresholds in §5 are own formulations.
- Consistent-hashing *library* defaults (e.g. hash-ring vnode counts in app code) not surveyed — product rings only.
- No controlled measurement of rebalance-induced cascade was found beyond the qualitative warning already in the rebalancing case and Dynamo's "do not auto-rebalance on transient failure".

---

## 12. Sources

Retrieved 2026-09-13.

**Canon / papers.** [allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf) · [allthingsdistributed.com/2007/10/amazons_dynamo.html](https://www.allthingsdistributed.com/2007/10/amazons_dynamo.html) · [usenix.org/system/files/atc22-elhemali.pdf](https://www.usenix.org/system/files/atc22-elhemali.pdf) (DynamoDB ATC 2022) · [raft.github.io/raft.pdf](https://raft.github.io/raft.pdf) · [usenix.org/system/files/conference/atc14/atc14-paper-ongaro.pdf](https://www.usenix.org/system/files/conference/atc14/atc14-paper-ongaro.pdf) · Karger et al. STOC 1997 (consistent hashing; cite-only).

**Postgres 17.** [postgresql.org/docs/17/runtime-config-replication.html](https://www.postgresql.org/docs/17/runtime-config-replication.html) · [postgresql.org/docs/17/runtime-config-wal.html](https://www.postgresql.org/docs/17/runtime-config-wal.html) (`synchronous_commit`) · [postgresql.org/docs/17/warm-standby.html](https://www.postgresql.org/docs/17/warm-standby.html).

**Cassandra.** [cassandra.apache.org/doc/stable/cassandra/architecture/dynamo.html](https://cassandra.apache.org/doc/stable/cassandra/architecture/dynamo.html) · [cassandra.apache.org/doc/5.0.8/cassandra/managing/configuration/cass_yaml_file.html](https://cassandra.apache.org/doc/5.0.8/cassandra/managing/configuration/cass_yaml_file.html) · [cassandra.apache.org/doc/5.0.8/cassandra/managing/operating/hints.html](https://cassandra.apache.org/doc/5.0.8/cassandra/managing/operating/hints.html) · [cassandra.apache.org/doc/latest/cassandra/reference/cql-commands/alter-table.html](https://cassandra.apache.org/doc/latest/cassandra/reference/cql-commands/alter-table.html) (`gc_grace_seconds`) · [docs.datastax.com/en/cassandra-oss/3.0/cassandra/dml/dmlConfigConsistency.html](https://docs.datastax.com/en/cassandra-oss/3.0/cassandra/dml/dmlConfigConsistency.html) (historical CL default ONE).

**etcd / Raft ops.** [etcd.io/docs/v3.6/tuning/](https://etcd.io/docs/v3.6/tuning/) · [etcd.io/docs/v3.4/op-guide/configuration/](https://etcd.io/docs/v3.4/op-guide/configuration/) · [etcd.io/docs/v3.8/tuning/](https://etcd.io/docs/v3.8/tuning/).

**DynamoDB.** [docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.Partitions.html](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.Partitions.html) · [docs.aws.amazon.com/amazondynamodb/latest/developerguide/burst-adaptive-capacity.html](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/burst-adaptive-capacity.html) · [docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html) · [docs.aws.amazon.com/amazondynamodb/latest/developerguide/throttling-diagnosing-workflow.html](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/throttling-diagnosing-workflow.html) · [docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html) · [docs.aws.amazon.com/amazondynamodb/latest/developerguide/LSI.html](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/LSI.html) · [aws.amazon.com/blogs/database/part-3-scaling-dynamodb-how-partitions-hot-keys-and-split-for-heat-impact-performance/](https://aws.amazon.com/blogs/database/part-3-scaling-dynamodb-how-partitions-hot-keys-and-split-for-heat-impact-performance/).

**Kafka.** [kafka.apache.org/43/configuration/topic-configs/](https://kafka.apache.org/43/configuration/topic-configs/) · [kafka.apache.org/43/configuration/broker-configs/](https://kafka.apache.org/43/configuration/broker-configs/) · [docs.confluent.io/kafka/design/replication.html](https://docs.confluent.io/kafka/design/replication.html).

**MongoDB / CockroachDB.** [mongodb.com/docs/manual/core/sharding-data-partitioning/](https://www.mongodb.com/docs/manual/core/sharding-data-partitioning/) · [mongodb.com/docs/manual/tutorial/modify-chunk-size-in-sharded-cluster/](https://www.mongodb.com/docs/manual/tutorial/modify-chunk-size-in-sharded-cluster/) · [mongodb.com/docs/manual/core/sharding-balancer-administration/](https://www.mongodb.com/docs/manual/core/sharding-balancer-administration/) · [cockroachlabs.com/docs/v26.2/configure-replication-zones](https://www.cockroachlabs.com/docs/v26.2/configure-replication-zones).

**Observability.** [opentelemetry.io/docs/specs/semconv/db/database-metrics/](https://opentelemetry.io/docs/specs/semconv/db/database-metrics/) · [github.com/open-telemetry/semantic-conventions/blob/v1.38.0/docs/database/database-metrics.md](https://github.com/open-telemetry/semantic-conventions/blob/v1.38.0/docs/database/database-metrics.md).
