---
type: reference
title: 'Rebalance and request routing'
description: 'Move shards without cascading, and send each key to a node that owns it. Size-balance is not QPS-balance. The map wants consensus; gossip is cheaper and admits split-brain. C5 stays L4/L7 of interchangeable instances.'
tags: [system-design-patterns, partitioning, rebalancing, request-routing, B2e]
---

# Rebalance and request routing

**See also:** [rebalancing (DDIA)](../data-intensive-design/rebalancing.md) · [request routing (DDIA)](../data-intensive-design/request-routing.md) · [sharding overview](../data-intensive-design/sharding-overview.md) · [partitioning](Partitioning.md) · [single-leader](SingleLeaderReplication.md) · [leaderless](LeaderlessReplication.md) · [load balancing](LoadBalancing.md) · [failover](Failover.md) · [quorums and fencing](../data-intensive-design/quorums-and-fencing.md) · [circuit breaker](CircuitBreaker.md) · [scaling strategies](ScalingStrategies.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/b2-partition-replicate-external-research.md)

This card owns **how the key → node map moves**, and **who looks it up**. [Rebalancing](../data-intensive-design/rebalancing.md) already names the danger: automation plus false death detection cascades. [Request routing](../data-intensive-design/request-routing.md) already names the three placements (any-node forward, routing tier, smart client). This card adds product thresholds, the gossip-vs-consensus fork for the *map*, and the cutover window. [Load balancing](LoadBalancing.md) (C5) is **stateless** placement of interchangeable instances — L4/L7, consistent-hash *proxies*, sticky sessions. A shard can serve a key only on a replica that owns it. Cells (catalog E13) wrap these units; they are not themselves a shard.

Quality attributes: **operability** (moves that do not take the cluster), **availability** of the *key* during cutover, **correctness** of ownership (one owner, or a split-brain map). Costs: a human commit step that is slower than autoscale, a router fleet that is a new HA problem, and a stale client ring.

## Lineage and vocabulary

- **Kleppmann / this tree.** Rebalancing is expensive: reroute, move a large amount of data, keep writes live. Near maximum write throughput the split may not keep up. Middle ground: suggest an assignment, wait for an administrator to commit (Couchbase, Riak). A human in the loop is slower than full automation and prevents operational surprises. Manual rebalance is also how you **preempt** a named surge.
- **DeCandia et al., SOSP 2007 *Dynamo*.** Membership change is **explicit**. Transient failure must *not* reshuffle the ring. Named both routing placements: load-balancer → random coordinator, or partition-aware client that skips a hop (clients refreshed membership every **10 s** in the paper).
- **Elhemali et al., ATC 2022 *Amazon DynamoDB*.** The map lives in a **metadata service** consulted by a **request-router** fleet; storage nodes are source of truth and push changes up.
- **MongoDB current manual (fetched 2026-09-13).** Balancer always on by default. A collection is balanced if the data-size difference between shards is **< 3× configured range size**. Default range **128 MB** → migrate when the gap is **≥ 384 MB**.
- **CockroachDB v26.2.** Split at **512 MiB**, merge below **128 MiB**; automatic rebalance on node join/leave, honoring zone constraints. Docs' rationale: small enough to move, large enough that keys accessed together stay together.

No controlled measurement of a rebalance-induced cascade was found beyond the qualitative warning already in the rebalancing case and Dynamo's "do not auto-rebalance on transient failure." Do not invent a numeric cascade threshold.

**Fixed shards vs adaptive ranges** (the [hash](../data-intensive-design/hash-sharding.md) fork, operationally). A fixed shard count ≫ node count (Citus, Riak, Elasticsearch, Couchbase) rebalances by moving *whole* shards: the key-to-shard map does not change. Guess the count wrong — more nodes than shards — and you need an expensive reshard, sometimes with downtime. Adaptive ranges (Mongo, Cockroach, Cassandra tokens) split on demand and pay metadata churn and jumbo-chunk risk instead. Pick the unit of move *before* you turn the balancer on: moving a 128 MB range is a different incident from rewriting a 1,000-shard map.

## Rebalance — size, heat, and a human

| System | When it moves | What it balances | What it will not save |
|---|---|---|---|
| **MongoDB** | Gap ≥ **3×** configured range (default **384 MB**). Since 6.0.3 automatic *split* is off; chunks may exceed 128 MB (docs mention a **1 TB** chunk). `chunkSize` (**1–1024 MB**) now mainly caps how much one migration moves. | **Data size**, not QPS. | A 100 MB celebrity chunk will not move, and should not — moving it relocates the hot key ([partitioning](Partitioning.md)). |
| **CockroachDB** | Split at 512 MiB, merge below 128 MiB; join/leave. | Range size + zone constraints. | Zone constraints can pin a hot range to the node you wanted to drain. |
| **Cassandra / Dynamo** | **Explicit** join / decommission. | Token ranges (`num_tokens` **16**). | Transient failure must not reshuffle. Cassandra will not drop a node from gossip without operator decommission or `replace_address_first_boot`. |
| **Kafka** | Partition reassignment (preferred-replica election is *leader* move, not data move). | Leaders vs replicas. | More partitions ≠ a rebalance strategy; each partition is a single-leader log. |

Smaller Mongo ranges → more frequent I/O; larger → fewer metadata updates, jumbo-chunk risk. A jumbo chunk cannot move. Disable the balancer during an incident; a move through peak QPS is a self-inflicted outage. Mongo's balancer window is the productization of that sentence: migrations allowed only in the hours you name. A window that includes the peak is worse than no window — you get the cascade *and* a calendar that said it was fine.

Cloud "adds and removes shards within minutes of a load change" (DynamoDB, cited in the rebalancing case) is elasticity of *managed* partitions, not a license to auto-rebalance an operator-owned ring on a slow node. Dynamo itself kept membership explicit for that reason.

**The cascade.** One node is overloaded and slow. Others declare it dead and rebalance away from it. That puts more load on the remaining nodes and the network. Other nodes look dead. More moves. Architect takeaway from the case, unchanged: if detection can be wrong, require a **commit step**. Pre-split and pre-move for events you can name on a calendar. Autoscale of *compute* ([B1](ScalingStrategies.md)) is a different loop; horizontally scaling a database "usually involves data partitioning, which is generally not automated" (Azure Autoscaling Guidance, cited on that card).

## Request routing — three placements

A sharded store can handle a key only on a node that is a replica of the shard that owns that key. Routing must know key → shard and shard → node.

| Approach | Path | Role of the node | Trade-off |
|---|---|---|---|
| **Any node** | Client hits any replica (often via round-robin). | If it owns the shard, serve; else forward, wait, reply. | Extra hop; the coordinator is a new timeout. Dynamo's random-coordinator path. |
| **Routing tier** | All clients hit a proxy first (`mongos`, DynamoDB request-router, Vitess, Citus coordinator). | Shard-aware load balancer; it does not serve data. | Router fleet is a new HA problem; stale map during cutover drops in-flight requests. |
| **Smart client** | Client connects to the right node (Cassandra token-aware driver; Dynamo partition-aware library). | No intermediary. | Every language needs a correct client; membership refresh lag (Dynamo paper: **10 s**) is a consistency window. |

[Load balancing](LoadBalancing.md) may sit *in front of* a coordinator fleet. It must not pick a *storage* node as if storage nodes were interchangeable. Consistent hashing on a proxy (ketama, Maglev, Envoy ring hash) is C5: it spreads *stateless* work. It does not replace a shard map.

**The three hard questions** (already in the routing case):

1. **Who assigns shards to nodes?** A single coordinator is simple. Then: how is it fault-tolerant? If the role fails over, how do you prevent two coordinators with contradictory maps?
2. **How does the router learn the map?** The router may be a node, the routing tier, or the client.
3. **Cutover.** While a shard moves, the new node has taken over but requests to the old node are still in flight. What happens to those?

## Gossip vs consensus for the map

The hard questions are already in [request routing](../data-intensive-design/request-routing.md): who assigns shards to nodes, how the router learns the map, and what happens to in-flight requests at cutover.

| Map mechanism | Split-brain | Cost | Use when |
|---|---|---|---|
| **Consensus** (etcd, ZooKeeper, MongoDB config servers, Kafka KRaft, TiDB/Yugabyte/Scylla built-in Raft) | Protected. Two coordinators with contradictory maps is the failure [failover](Failover.md) and [fencing](../data-intensive-design/quorums-and-fencing.md) exist to stop. | A consensus cluster to operate. etcd timing lives on [single-leader](SingleLeaderReplication.md) — do not run one etcd across a 350 ms RTT. | The data plane can still be leaderless; the **control plane should not be**. |
| **Gossip** (Cassandra, Riak) | Possible — different parts of the cluster disagree which node owns a shard. | Cheaper; no extra store. | Only if the store already lives with weak consistency. |

HBase and SolrCloud use ZooKeeper; Kubernetes uses etcd for instance placement (not your shard map unless you built that). MongoDB is similar with its own config servers and `mongos` as the routing tier.

Dynamo evaluated both client paths in one system: a load balancer to a random coordinator (any-node), or a partition-aware client that skips the hop. DynamoDB split the difference — a request-router *fleet* plus a metadata service — so the storage nodes are not gossiping the map at the client. The control-plane rule is the same: the map is consensus (or a managed equivalent); the data plane can still be whatever replica family you chose.

**Cutover.** While a shard moves, the new node has taken over but requests to the old node are still in flight. Those requests fail, retry, or get forwarded — product-specific, and a stale smart-client ring extends the window to the refresh interval. Do not assume the store will buffer them. A [retry](RetryBackoff.md) of a non-idempotent write during cutover is a duplicate unless the write carries a key ([idempotency](Idempotency.md)). Prefer fail-fast to the client with "wrong owner, retry against X" over silently applying twice.

Leader vs data moves are different operations. Kafka preferred-replica election moves *leadership* without moving the log; Cockroach leaseholder maps are the same idea. A cluster can look "unbalanced" on CPU with perfectly even *data* size — that is a leader-distribution problem, not a chunk-size problem. `PreferredReplicaImbalance` is the signal; do not answer it by migrating terabytes.

## Verified defaults (fetched 2026-09-13)

| Knob | MongoDB current | CockroachDB v26.2 | Cassandra 5.0.8 | Dynamo / DynamoDB |
|---|---|---|---|---|
| Range / chunk | **128 MB** default; **1–1024 MB** allowed | split **512 MiB**, merge **128 MiB** | `num_tokens` **16** | managed partitions; LSI collection **10 GB** hard |
| Balance trigger | gap **< 3×** range (384 MB at default) | automatic on join/leave + zone | explicit decommission | explicit (Dynamo); metadata service push (DynamoDB) |
| Auto-split | **off** since 6.0.3 | yes (size) | n/a (tokens) | split-for-heat with LSI / monotonic caveats — [partitioning](Partitioning.md) |
| Membership | config servers (consensus) | built-in Raft | gossip; no auto-remove | Dynamo: admin join; DynamoDB: router + metadata |

Citus default shard count, Vitess default shard count, and Yugabyte tablet split thresholds were **not** fetched.

## Observability

| Signal | What it means |
|---|---|
| **Shard size skew / chunk imbalance** | Balancer should have fired, or a jumbo chunk cannot move. MongoDB `sh.status`, balancer window; Cockroach range-size histograms. |
| **Balancer / migration in progress** | Extra I/O and metadata ops. A balancer running through peak QPS is the incident. |
| **Leader / leaseholder distribution** | Rebalance of *leadership* without data move (Kafka preferred replica; Cockroach leaseholder). One node holding too many leaders is a tail-latency problem. |
| **Router / client map age** | Cutover window. Smart-client refresh lag; `mongos` / request-router vs storage as source of truth. |
| **Under-replicated / hint backlog during a move** | The move is racing repair. Do not decommission the source until the destination is in the quorum. |
| **Client op duration + errors on a key range** | Cutover drops. Break the dashboard **per shard**, not fleet-average. |

A [circuit breaker](CircuitBreaker.md) over "the database" without **resource differentiation** trips healthy shards with the one being moved. Granularity = endpoint + shard.

## Tuning — Mongo size-balance vs a named surge

MongoDB will migrate when shard data differs by **384 MB** at the default 128 MB range. That is *size* balance, not *QPS* balance.

| Situation | Action | Why |
|---|---|---|
| Calendar event (Cyber Monday, ticket drop) | Pre-split and pre-move; optionally pause the balancer during the peak | Automation reacts *after* the cluster is on fire. |
| 100 MB celebrity chunk | Do **not** migrate it. Write-shard the key ([partitioning](Partitioning.md)). | Migration relocates the heat. |
| Jumbo / 1 TB chunk (auto-split off) | Manual split if the key allows; otherwise live with it and cap `chunkSize` for *future* moves | `chunkSize` no longer forces a split. |
| Node looks dead | Disable balancer; confirm death ([failover](Failover.md)); *then* decommission | False death + auto-move is the cascade. |
| Adding a node | Commit the take of a fair share; watch migration I/O against peak WAL / compaction | A commit step is slower than autoscale and prevents rebalancing *onto* an overloaded node that looks dead. |

Smaller `chunkSize` → more frequent I/O; larger → jumbo risk. Pick from measured range sizes, not from a blog "128 is fine."

## Testing and operating

- **False-death cascade.** Make one node slow (disk, not killed). If the balancer moves ranges off it, the remaining nodes take the I/O, look slow, and the next move starts — stop the balancer *before* that sentence finishes. The [rebalancing](../data-intensive-design/rebalancing.md) case is the acceptance criterion: a commit step would have prevented it.
- **Size ≠ QPS.** Put a 100 MB celebrity chunk on a shard that is otherwise small. Confirm the balancer does not move it (Mongo 384 MB trigger) and that moving it by hand only relocates `KeyRangeThroughputExceeded`.
- **Cutover.** Migrate one range under live write. Count in-flight errors on the old owner vs the new. Measure smart-client map age; Dynamo's paper figure is a **10 s** refresh — treat that as a *window*, not a default to copy.
- **Jumbo.** With auto-split off (Mongo ≥ 6.0.3), grow a chunk past 128 MB. Confirm it still serves and that `chunkSize` only caps the *next* migration, not the existing chunk.
- **Decommission.** Drain a Cassandra / Kafka node. Writes must stay at RF / min-ISR on the destination *before* the source leaves. Hints covering the drain are not "the destination is in the quorum."
- **Gossip vs consensus.** Two coordinators, contradictory maps, is a [failover](Failover.md) / [fencing](../data-intensive-design/quorums-and-fencing.md) drill. Do it on a store that claims a single owner; do not do it as a surprise on Monday.

## Alternatives that beat a balancer

| Situation | Prefer | Why |
|---|---|---|
| Interchangeable stateless instances | [Load balancing](LoadBalancing.md) | C5. No shard map. |
| Only *leaders* are skewed | Preferred-replica / leaseholder rebalance | Do not move the data. |
| One hot key | Write-shard ([partitioning](Partitioning.md)) | The balancer will not save you. |
| Named calendar surge | Pre-split, pre-move, pause balancer | Automation reacts after the fire. |
| Compute ran out | [Autoscaling](ScalingStrategies.md) | Different loop; do not add Mongo shards as if they were Pods. |
| You need a hard blast-radius cap | Cell-aligned key (E13) | Cross-cell queries become federated. |

## Placement

| Placement | What it owns | Trade-off |
|---|---|---|
| **Store-native balancer** | Size (and sometimes heat) moves. | Will not fix a hot key; can cascade on false death. |
| **Coordinator / router** | Key → node map. | Router HA; stale map at cutover. |
| **Smart client** | Skips a hop; caches the ring. | Per-language correctness; refresh lag. |
| **Consensus sidecar** (etcd/ZooKeeper for the *map*, not the data) | Split-brain-safe assignment. | The data plane can still be leaderless; this sidecar must not be. |
| **Cell boundary** (E13) | Align partition key with a deployable quantum. | Cross-cell queries become federated. |

## Failure modes

| Mode | How it happens | What to do |
|---|---|---|
| **Rebalance cascade** | Autodetect death → move data → remaining nodes look dead → more moves. | Human commit; disable balancer during incidents. |
| **Map split-brain** | Two coordinators, two owners of shard S. | Consensus for the map; fencing token on the storage side. Gossip-only maps only on stores that already accept divergence. |
| **Cutover drop** | New owner is live; in-flight requests still hit the old node; smart client has a 10 s-class stale ring. | Forward or fail-fast + retry on the *new* owner; refresh the client; do not assume a buffer. |
| **Size-balance misses heat** | Celebrity chunk under the 384 MB trigger. | Write-shard; do not wait for the balancer. |
| **Jumbo chunk** | Auto-split off; one chunk cannot move. | Manual split, or live with a pinned range. |
| **Decommission while under-replicated** | Source leaves before destination is in the quorum. | Wait for RF / ISR / repair; hints are not a substitute. |
| **C5 vocabulary error** | L4/L7 of storage nodes as if they were stateless. | Key-aware routing here; interchangeable instances on [load balancing](LoadBalancing.md). |
| **Blind breaker** | One Open circuit for the whole store during a single-shard move. | Per-shard breaker. |

## When not to automate rebalance

Detection can be wrong. Pre-split for calendar events; require a commit step if a false death can cascade. Do not turn on a balancer as a substitute for a partition-key redesign. Do not use a gossip map on a store that promises a single owner.

Do not treat adding Kafka partitions or Mongo shards as [autoscaling](ScalingStrategies.md). The compute loop adds interchangeable replicas; this loop moves *state*.

## Trade-offs

| Buy | Pay |
|---|---|
| Automatic size-balance (Mongo 3× range, Cockroach split/merge) | Moves on the wrong signal (size ≠ QPS); cascade risk |
| Human commit / explicit decommission | Slower than autoscale; prevents the cascade |
| Consensus map | Split-brain-safe ownership; a consensus cluster to operate |
| Gossip map | Cheap; admits two owners |
| Routing tier | Clients stay dumb; router fleet is now HA |
| Smart client | One less hop; stale ring = cutover window |
| C5 in front of coordinators | Spreads *router* work; must not spray keys at storage |

The balancer decides **when a slice moves**. The map mechanism decides **who may own it**. The router decides **which hop the client pays**. [Partitioning](Partitioning.md) decides **what the slice is**. Coordinate all four; do not treat "balancer on" as a complete data-plane scale strategy.

Writes must continue during a move. Near maximum write throughput, the split may not keep up with incoming writes — the case already names this, and cloud "minutes after a load change" claims do not repeal it. A balancer window (Mongo) is how you keep migrations off the peak; a paused balancer plus a commit step is how you keep a false death from becoming a second outage. Gossip membership that *does not* remove a silent node is the same instinct: transient failure must not reshuffle the ring.

## Leaves to siblings

| Sibling | What they take |
|---|---|
| [Partitioning](Partitioning.md) | What the slice *is* (key, range size, heat). |
| [Load balancing](LoadBalancing.md) | L4/L7 of interchangeable instances; consistent-hash *proxies*. |
| [Failover](Failover.md) | Death detection that must not trigger a data move by itself. |
| [Quorums and fencing](../data-intensive-design/quorums-and-fencing.md) | Two coordinators, two owners of shard S. |
| [Single-leader](SingleLeaderReplication.md) | Preferred-replica / leaseholder moves (leadership, not bytes). |
| Catalog E13 | Cell topology; this card's units sit inside a cell. |

## Sources

Verified 2026-09-13; URLs, provenance, and items left out (Citus/Vitess/Yugabyte thresholds, a numeric cascade study, app hash-ring libraries) are in the [external research note](../../docs/research/sysdesign/b2-partition-replicate-external-research.md).

- Canon: [rebalancing.md](../data-intensive-design/rebalancing.md); [request-routing.md](../data-intensive-design/request-routing.md); Dynamo SOSP 2007; DynamoDB ATC 2022.
- Products: MongoDB sharding-data-partitioning, chunk-size, balancer-administration; CockroachDB v26.2 zone config; Cassandra 5.0.8 `cassandra.yaml` (`num_tokens`, no auto-remove); DynamoDB request-router + metadata service (ATC 2022).
- C5 boundary: [LoadBalancing.md](LoadBalancing.md).
- Observability: OpenTelemetry `db.client.operation.duration` is caller-side; pair it with balancer / ISR / hint metrics during a move — see [partitioning](Partitioning.md). Do not label raw keys.

