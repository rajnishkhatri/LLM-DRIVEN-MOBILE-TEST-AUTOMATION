---
type: reference
title: 'Data partitioning'
description: 'Split a dataset so each record belongs to one shard: key-range, hash, or composite. The operational job is the partition key, per-partition throughput caps, and write-sharding a hot key — not inventing a new sharding taxonomy.'
tags: [system-design-patterns, partitioning, sharding, B2a]
---

# Data partitioning

**See also:** [sharding overview](../data-intensive-design/sharding-overview.md) · [key-range sharding](../data-intensive-design/key-range-sharding.md) · [hash sharding](../data-intensive-design/hash-sharding.md) · [hot spots](../data-intensive-design/sharding-hot-spots.md) · [secondary indexes](../data-intensive-design/sharding-secondary-indexes.md) · [multitenancy](../data-intensive-design/sharding-multitenancy.md) · [single-leader replication](SingleLeaderReplication.md) · [rebalance & request routing](RebalanceRouting.md) · [scaling strategies](ScalingStrategies.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/b2-partition-replicate-external-research.md)

This card owns **how a record finds its shard**. [Sharding](../data-intensive-design/sharding-overview.md) already states the rule: each record, row, or document belongs to **exactly one** shard; that shard is then copied under a replica family ([B2b](SingleLeaderReplication.md)–[B2d](LeaderlessReplication.md)). [Scaling strategies](ScalingStrategies.md) decide *when* to go horizontal; this card decides the key that makes horizontal work. Do not re-derive key-range vs hash here.

Quality attributes: **write scalability** (spread ingest), **read locality** (range scan vs point get), **isolation** (one shard's heat stays on one replica set). Costs: an irreversible-looking partition key, a secondary-index tax, and a celebrity key that hashing cannot save.

```
key ──► partition function ──► shard S ──► replica family (B2b / B2c / B2d)
```

Independence is the useful lie: the scheme and the replica family *compose*, but failover, routing, and rebalance couple them. A node commonly **leads some shards and follows others**. "The primary is down" is usually "the leaders of shards {S17, S44, S91} lived on the dead node" — blast radius = those shards, not the dataset. Align the key with a cell (catalog E13) if you need a *user-slice* blast radius rather than a random set of hash ranges.

## Lineage and vocabulary

- **Kleppmann / this tree.** [Sharding overview](../data-intensive-design/sharding-overview.md): shard when data *or write throughput* no longer fits on one node; read throughput alone is replica scale. [Key-range](../data-intensive-design/key-range-sharding.md) is the encyclopedia volume. [Hash](../data-intensive-design/hash-sharding.md) is `hash(key)` then a map — never `hash % N` in a cluster that will grow. [Hot spots](../data-intensive-design/sharding-hot-spots.md): uniform keys are not uniform *load*.
- **Karger et al., STOC 1997.** Consistent hashing: add/remove a node moves only its neighbours. The later **vnode** fix for imbalance is Dynamo (2007), not Karger.
- **DeCandia et al., SOSP 2007 *Dynamo*.** Preference list on the ring; Strategy-2 evaluated decoupling partition *identity* from *placement* (`Q` equal hash ranges, `T` tokens per node, `Q >> N`). Product rings only — app hash-ring libraries were not surveyed.
- **Elhemali et al., USENIX ATC 2022 *Amazon DynamoDB* + current developerguide.** Per-partition throughput is a first-class knob. Dynamo (2007, leaderless) and DynamoDB (2012+, single-leader Multi-Paxos per partition) are different systems — collapsing the names is a vocabulary error already called out in [leaderless replication](../data-intensive-design/leaderless-replication.md).
- **Cassandra architecture (stable docs, fetched 2026-09-13).** Dynamo-style ring + LSM. Default partitioner **Murmur3Partitioner** (cannot change without reload). Cassandra 3.x+ dropped the 2.x default of **256** random vnodes (too many neighbours → correlated unavailability) for a deterministic allocator; current `cassandra.yaml` default **`num_tokens = 16`**.

**Names that must not be collapsed.** Partition / shard / tablet / range / chunk / vnode are the same idea: a contiguous or hashed slice of the keyspace owned by a replica set. Product words: DynamoDB *partition*, Cassandra *token range*, MongoDB *chunk/range*, CockroachDB *range*, Kafka *partition*, Citus *shard*, Vitess *shard*.

## Two families, one compromise

The taxonomy lives in the cited cases. Operational restatement:

| Family | Placement | Cheap query | Failure mode | Rebalance unit |
|---|---|---|---|---|
| **Key range** | Shard owns `[min, max)` of the partition key. MongoDB default range **128 MB**; CockroachDB splits at **512 MiB**, merges below **128 MiB**. | Range scan / `Query` inside the key. | Sequential keys (timestamps, autoincrement) write one hot shard. | Split the range; move one child. |
| **Hash** | `hash(key)` then map. Cassandra **Murmur3Partitioner**. DynamoDB hashes the partition key internally. | Point get by key. | `hash % N` reshuffles almost everything when N changes. A celebrity key still hashes to one shard. | Move whole virtual shards, or walk the ring. |
| **Composite** | Hash (or tenant) prefix + sorted suffix. DynamoDB partition key + sort key = *item collection*. | Range *inside* one partition key. | Monotonic sort key defeats split-for-heat. | Split by sort-key cut, unless an LSI pins the collection to one partition. |

**Fixed-shard vs ring** is already contrasted in [hash sharding](../data-intensive-design/hash-sharding.md): `mod N`, a fixed shard count ≫ node count, hash ranges, consistent hashing. Trade-off on vnodes: more tokens = smoother add/remove, more neighbour combinations that lose a token range, slower repair. Cassandra's move from 256 → **16** is that trade made concrete.

Dynamo §6 evaluated decoupling partition *identity* from *placement*: `Q` equal hash ranges, `T` tokens per node, `Q >> N` and `Q >> S·T`. The identity of a partition stays put when a node joins; only placement changes. That is the opposite of `hash % N`, and it is why a later vnode count is a *placement* knob, not a new key scheme. Pick `Q` (or `num_tokens`, or Mongo `chunkSize`) knowing you are trading move-smoothness against neighbour blast radius and repair time.

Language `hashCode` / `Object#hash` may differ across processes — unsuitable for a cluster map ([hash sharding](../data-intensive-design/hash-sharding.md)).

**Hash-range vs consistent hashing** is the elasticity fork already in the hash case. Hash-range: each shard owns a range of *hashes*; split when a shard is too big or too hot — still expensive, but on demand. Range queries on the partition key scatter. If only the first column is the partition key, range queries on later columns stay in one shard. Consistent hashing (Karger sense): a key tends to stay put when the node count changes. Cassandra/Scylla are close to that definition; rendezvous / jump-consistent hashing assign the new node individual keys previously scattered across all others, instead of splitting a few existing shards. Which is better depends on the application. Uniform keys still do not imply uniform **load**.

## Designing the key

The scheme is hard to change ([sharding overview](../data-intensive-design/sharding-overview.md)). Pick the key for the query you cannot afford to scatter, then write-shard the keys that will burn a partition.

| Pattern | Key shape | Buys | Pays |
|---|---|---|---|
| **Tenant / cell** | `tenantId` (or a group of small tenants) as the partition key | Isolation, restore-one-tenant, residency, gradual schema — [multitenancy](../data-intensive-design/sharding-multitenancy.md). A cell (E13) is this idea at a larger grain. | One tenant that outgrows a node; a noisy neighbour if many small tenants share a shard. |
| **Time-first range** | timestamp or autoincrement as the leading key | Cheap "last month" scans. | Live writes hit *this* interval's shard; others idle. Prefix with sensor / user / bucket. |
| **Hash then sort** | `hash(userId)` or tenant + sort key `ts` | Even write spread *and* a range inside one item collection. | `Query` / `Scan` of "all users this hour" is scatter. Monotonic sort key defeats split-for-heat. |
| **Write-sharded celebrity** | `userId#00` … `userId#N-1` | Beats the per-partition write cap. | Read is N gets or a rollup. Book-keep which keys are split. |

A SaaS tenant that is also a celebrity is both rows: isolate the tenant, then write-shard *inside* that tenant if one partition key still saturates.

## Per-partition throughput is a knob

DynamoDB documents that **each physical partition** is designed for **3,000 read units/s and 1,000 write units/s** (1 RCU = one strongly consistent 4 KB read/s, or two eventually consistent; 1 WCU = one 1 KB write/s). A 20 KB item costs 5 RCU on a consistent read → 600 consistent reads/s to that item before the partition cap. Throttling reason `KeyRangeThroughputExceeded` means the *partition* is saturated while table-level capacity is still free.

Burst retains up to **five minutes (300 s)** of unused capacity (best-effort; AWS says the detail may change). Adaptive capacity boosts a hot partition and can isolate a single hot item up to the same 3,000/1,000 cap; it **will not** split an item collection that has an LSI, and split-for-heat is **not beneficial** when the sort key only ever increases (every new write lands on the newest child). LSI item collections are capped at **10 GB** (the documented maximum size of a partition); without an LSI there is no documented upper bound on sort-key cardinality.

The same *unit of heat* applies to a Cassandra partition even though Cassandra does not publish a 1,000 WCU number: one partition key = one storage partition that must compact and repair as a unit. Adding table-level WCU / RF does nothing to a celebrity key.

**Item collections.** DynamoDB partition key + sort key is one collection. Split-for-heat cuts the sort-key space so two physical partitions share the same partition-key prefix — unless an LSI exists, in which case the collection is pinned to one partition and hard-capped at **10 GB**. A collection whose sort key only ever increases (event time, sequence) will not benefit from the split: every new write is the new maximum and lands on the newest child. That is why the write-shard suffixes in the calibration *are* the design, not a fallback after adaptive capacity.

**Burst.** Unused capacity can be retained up to **300 s** (best-effort; AWS documents that the detail may change). Burst is not a plan for a sustained 4,000 writes/s celebrity. Adaptive capacity can isolate a single hot item up to the same 3,000/1,000 cap; it will not invent a second write path for a monotonic collection.

## Secondary indexes and cross-shard writes

A secondary index does not map to one shard. [Local vs global](../data-intensive-design/sharding-secondary-indexes.md): local = write one shard, scatter-gather on read; global = one-shard lookup, multi-shard write, possible staleness. A DynamoDB GSI that throttles back-pressures the base table.

A write that updates two shards is not "retry until it looks fine" — that is a saga / distributed transaction (catalog B5), not a partitioning trick. Kafka's "one partition = one ordered log" is the same constraint: a join across partitions is an app-level merge, not a store guarantee.

## Kafka partitions are not "more is better"

`num.partitions` default **1** (Kafka 4.3 broker). Each partition is a [single-leader](SingleLeaderReplication.md) log. Size for *consumer parallelism and throughput*, not for elasticity theatre:

- Partition count ≥ max downstream consumer instances you want in parallel (one consumer per partition per group).
- More partitions = more open files, more replication traffic, longer recovery, more ISR objects to watch.
- A hot *key* inside one partition is still one leader's disk. Adding partitions later does not split a key; it only gives new keys somewhere to land. Pre-plan the key → partition function the same way you pre-plan a DynamoDB partition key.

Broker `default.replication.factor = 1` is the companion foot-gun — durability lives on [B2b](SingleLeaderReplication.md), not here.

## Verified defaults (fetched 2026-09-13)

| Product | Partition / range size | Notes |
|---|---|---|
| **MongoDB** (current manual) | chunk/range **128 MB**; allowed **1–1024 MB** | Balanced if the data-size gap between shards is **< 3×** configured range → migrate when the gap is **≥ 384 MB** at the default. Since 6.0.3 automatic *split* is off; chunks may *exceed* 128 MB (docs mention seeing a **1 TB** chunk). `chunkSize` now mainly caps how much one migration moves. Smaller → more frequent I/O; larger → fewer metadata updates, jumbo-chunk risk. |
| **CockroachDB v26.2** | `range_max_bytes` **512 MiB**, `range_min_bytes` **128 MiB** | Docs' rationale: small enough to move, large enough that keys accessed together stay together. |
| **Cassandra 5.0.8** | token ranges via `num_tokens` **16** | Do not jump a new cluster to 256 (neighbour explosion). Partitioner is load-bearing. |
| **Kafka 4.3** | `num.partitions` **1** | Broker default is **dev-safe and prod-wrong**. Size partitions for consumer parallelism, not "more is better": each partition is a single-leader log; more partitions = more open files, more replication traffic, longer recovery. |
| **DynamoDB** (current + ATC 2022) | managed; ~**10 GB** physical partition; LSI collection **10 GB** hard | 3,000 RCU / 1,000 WCU per partition. |
| **Postgres 17** | n/a | One instance = one replica set unless Citus / equivalent. |

Empty cells in the research table are not defaults of that product. Citus / Vitess / Yugabyte tablet thresholds were **not** fetched this pass — do not invent them.

## Observability

Partition incidents are almost never "the database is down". They are *this key's shard*. Dashboards that average across shards hide the failure.

| Signal | What it means |
|---|---|
| **Per-partition / per-key consumed RCU/WCU** | Hot key. Table-level ConsumedCapacity being "fine" is the usual lie. DynamoDB: `KeyRangeThroughputExceeded` vs `TableWriteProvisionedThroughputExceeded`. Contributor Insights for the keys. |
| **Shard size skew / chunk imbalance** | Balancer should have fired, or a jumbo chunk cannot move. MongoDB `sh.status`; Cockroach range-size histograms. |
| **Leader distribution** | One node holds too many shard leaders → CPU/WAL tail. Kafka `PreferredReplicaImbalance`; Cockroach/Yugabyte leaseholder maps. Postgres has one leader for the whole instance. |
| **Client op duration** | User-visible. OpenTelemetry `db.client.operation.duration` (unit `s`; recommended buckets `[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5, 10]`; `db.system.name` + `db.operation.name`) **plus a low-cardinality shard / partition-key hash bucket**. Do not label raw keys. This is caller-side duration including internal retries — it does not replace store-native heat metrics. |

OTel conventions marked stable for MariaDB, SQL Server, MySQL, PostgreSQL; Cassandra/Mongo notes exist as system-specific. Live spec wording: attributes are **recommended** (a v1.38.0 source file says "required" — use the live spec until reconciled).

## Tuning — write-shard a hot key

Given: items **20 KB**, target **4,000 writes/s** to one logical entity (a "hot user"), eventually consistent reads not in this budget. DynamoDB arithmetic from the research note:

1. WCU per write = `ceil(20 KB / 1 KB) = 20`.
2. One partition's write cap = **1,000 WCU/s** → `floor(1000 / 20) = 50` writes/s to that key *even after adaptive isolation*.
3. Write-shard count `N = ceil(4000 / 50) = 80` random suffixes (`userId#00` … `userId#79`).
4. Read path pays scatter (`N` gets) or a precomputed rollup. That is the [hot spots](../data-intensive-design/sharding-hot-spots.md) lesson: write scale vs read amplification.
5. If the sort key is a timestamp, **do not** expect split-for-heat to save you; N suffixes *are* the design. An LSI on that table would also pin each suffix's collection to **10 GB**.

Track which keys are split; most keys would pay the suffix tax for nothing. Load moves with time — a viral key is hot for two days, then quiet.

A 100 MB celebrity chunk will not (and should not) migrate: moving it just relocates the hot key. Pre-split and pre-move before a named surge; size-balance is not QPS-balance ([rebalance](RebalanceRouting.md)).

Same arithmetic, Cassandra: one partition key = one storage partition that must compact and repair as a unit. There is no published 1,000 WCU number; the unit of heat is still "one partition key." Wide partitions (a partition key that collects an unbounded sort) are a repair/compaction incident waiting for a large delete.

## Testing and operating

- **Heat before launch.** Drive the celebrity key at the target write rate on a single partition (DynamoDB: watch `KeyRangeThroughputExceeded` while table-level ConsumedCapacity stays green). If it throttles at the 1,000 WCU math above, the suffix count is the design, not a later optimization.
- **Monotonic sort-key drill.** Insert only-increasing sort keys into a composite collection that also has an LSI. Confirm split-for-heat does *not* create a new write path — every new write still lands on the newest child.
- **Reshard rehearsal.** Adding a node under `hash % N` vs a ring / fixed-shard map: measure how many keys move. The hash case's "most keys move" is the acceptance test for never shipping `mod N`.
- **Scatter budget.** For each secondary-index or write-sharded read, count the fan-out *before* the first incident. A 80-way get that was fine at 50 rps is a fleet event at 4,000 rps.

## Alternatives that beat a reshard

| Situation | Prefer | Why |
|---|---|---|
| Data and writes still fit on one machine | Vertical scale + read replicas ([B1](ScalingStrategies.md), [single-leader](SingleLeaderReplication.md)) | Sharding is heavyweight and mostly relevant at large scale. |
| Only *reads* grew | Async followers, not a new partition key | Read throughput alone does not require sharding. |
| One tenant is noisy | Tenant-aligned shard / cell, not a finer hash | Isolation, restore, residency — [multitenancy](../data-intensive-design/sharding-multitenancy.md). |
| One *key* is noisy | Write-shard or a dedicated shard for that key | Hashing already spread keys; it did not spread load. |
| Callers need isolation from a bad dependency | [Bulkhead](Bulkhead.md) / shuffle shard | Different unit: callers, not records. |
| You needed interchangeable instances | [Load balancing](LoadBalancing.md) | C5; a shard is not interchangeable. |

## Placement

| Placement | What it owns | Trade-off |
|---|---|---|
| **Store-native** (DynamoDB partitions, Cassandra tokens, Cockroach ranges, Kafka partitions) | Correctness of the slice. | App cannot "add HA" later without a migration. |
| **App-level write sharding** (random suffix, time bucket) | Beats a hot key the store cannot split. | Read path becomes scatter or a rollup job. |
| **Cell-aligned key** (catalog E13) | Blast radius = a deployable quantum of users. | Cross-cell queries become federated. |

A [circuit breaker](CircuitBreaker.md) over "the database" without **resource differentiation** (Azure's term; Brooker on shard-blind breakers) trips the healthy shards with the sick one. Granularity = endpoint + shard, not "Postgres".

## Failure modes

| Mode | How it happens | What to do |
|---|---|---|
| **Hot key / hot range** | Celebrity, monotonic key, `Scan` walking one range at 3,000 RCU. Adaptive capacity cannot split a monotonic sort key or an LSI collection. | Redesign the key; write-shard; parallel scan. Adding table-level WCU does nothing. |
| **`hash % N` on growth** | Node count changes; almost every key moves. | Fixed shards ≫ nodes, hash ranges, or consistent hashing ([hash sharding](../data-intensive-design/hash-sharding.md)). |
| **Wrong family for the query** | Hash when you needed a month-of-sensor range scan; range when you needed even write spread. | Composite: hash (or tenant) prefix + sorted suffix. |
| **Secondary-index surprise** | Local index = scatter/gather; global = multi-shard write. | [sharding-secondary-indexes](../data-intensive-design/sharding-secondary-indexes.md). |
| **Cross-shard write** | One shard commits, the other does not. | Avoid; or a saga / distributed txn. |
| **Vnode neighbour explosion** | 256 random tokens × RF → correlated unavailability on one node loss. | Cassandra's current **16**; do not cargo-cult 256 onto a new cluster. |

## When not to shard

One machine still holds the data *and* the write rate. Sharding is heavyweight ([sharding overview](../data-intensive-design/sharding-overview.md)): irreversible-looking partition key, secondary-index tax, distributed transactions. Prefer vertical scale ([B1](ScalingStrategies.md)) + read replicas. Read throughput alone does not require sharding.

Do not shard *only* to isolate callers from a bad dependency — that is a [bulkhead](Bulkhead.md) / shuffle shard, a different unit.

## Trade-offs

| Buy | Pay |
|---|---|
| Key-range: cheap range scans, split/merge as the unit | Sequential keys write one hot shard |
| Hash: even key spread, point gets | Lost partition-key range scans; celebrity key still one shard |
| Composite: range *inside* a partition key | Monotonic sort key + LSI pins heat and size |
| Per-partition caps (3k/1k) make heat *visible* | Table-level capacity looks fine while one key dies |
| App-level write-sharding | Read amplification or a rollup |

The partition key decides **where a record lives**. The replica family decides **what a commit means**. [Rebalance and routing](RebalanceRouting.md) decide **how the map moves**. Pick the key first; the rest cannot rescue a celebrity timestamp.

Some systems shard even on one machine: one single-threaded process per CPU core (Redis, VoltDB, FoundationDB — cited in the sharding overview). That is CPU/NUMA parallelism, not a cluster. Do not confuse it with the operational cards above; the partition function is the same idea at a smaller grain.

## Leaves to siblings

| Sibling | What they take |
|---|---|
| [B2b](SingleLeaderReplication.md)–[B2d](LeaderlessReplication.md) | What a commit means once the record has a shard. |
| [B2e](RebalanceRouting.md) | How the key → node map moves; key-aware routing. |
| [B1](ScalingStrategies.md) | When to go horizontal at all. |
| [C5](LoadBalancing.md) | L4/L7 of interchangeable instances. |
| Catalog E13 | Cell = deployable quantum that *contains* partitions. |
| [C8](Bulkhead.md) | Isolating *callers*, not records. |

## Sources

Verified 2026-09-13; URLs, per-claim provenance, and items left out (driver defaults, Citus/Vitess/Yugabyte thresholds, app hash-ring libraries) are in the [external research note](../../docs/research/sysdesign/b2-partition-replicate-external-research.md). Vocabulary is owned by the cited `cases/data-intensive-design/` notes — not rewritten here.

- Canon: Karger et al. STOC 1997; DeCandia et al. SOSP 2007 *Dynamo*; Elhemali et al. ATC 2022 *Amazon DynamoDB*.
- Products: DynamoDB partition / burst-adaptive / partition-key-design / LSI / Constraints pages; Cassandra 5.0.8 `cassandra.yaml` + architecture; MongoDB sharding + chunk-size + balancer manuals; CockroachDB v26.2 zone config; Kafka 4.3 broker `num.partitions`.
- Observability: OpenTelemetry database semconv (live spec + v1.38.0).
