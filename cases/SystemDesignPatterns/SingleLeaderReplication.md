---
type: reference
title: 'Single-leader replication'
description: 'One writer per shard streams a log to followers, or a Raft/Paxos leader commits after a majority persists. Streaming can lose acknowledged writes on failover; consensus cannot. Failover runbooks stay on the failover card.'
tags: [system-design-patterns, replication, single-leader, B2b]
---

# Single-leader replication

**See also:** [replication overview](../data-intensive-design/replication-overview.md) · [single-leader (DDIA)](../data-intensive-design/single-leader-replication.md) · [replication logs](../data-intensive-design/replication-logs.md) · [replication lag](../data-intensive-design/replication-lag.md) · [quorums and fencing](../data-intensive-design/quorums-and-fencing.md) · [partitioning](Partitioning.md) · [multi-leader](MultiLeaderReplication.md) · [leaderless](LeaderlessReplication.md) · [failover and health checks](Failover.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/b2-partition-replicate-external-research.md)

This card owns **what a commit means** when one replica accepts writes and the others follow. The shape — leader writes locally, ships a [log](../data-intensive-design/replication-logs.md), followers apply in the same order — already lives in [single-leader replication](../data-intensive-design/single-leader-replication.md). Two implementations share that shape and not the *commit* meaning: **streaming / WAL shipping** (Postgres) can lose a client-visible write on failover; **Raft / Multi-Paxos** (etcd, Cockroach, DynamoDB, Kafka ISR+KRaft) commits only after a majority persists. [Failover](Failover.md) owns election timeouts as an availability mechanism, health checks, RTO/RPO. This card records the knobs that *feed* that card.

Quality attributes: **durability** of an acknowledged write, **write availability** (one writer; sync replicas can stall it), **read scale** on async followers. Costs: a single writer per shard, [lag](../data-intensive-design/replication-lag.md) on async reads, and a failover that is either lossy (streaming) or majority-bound (consensus).

If the store is [sharded](Partitioning.md), each shard is its own replica set. Different shards put their leader on different nodes.

## Lineage and vocabulary

- **Kleppmann / this tree.** Leader-based = primary-backup. Sync buys a second up-to-date copy and stalls writes if that copy is down. Async buys write availability and can lose unreplicated writes after the client saw success. Production "sync" is usually **semisync**: one follower sync, the rest async. Sync to *every* follower is the failure mode already named in the case.
- **Ongaro & Ousterhout, USENIX ATC 2014 *Raft*.** Single-leader consensus with randomized election timeout (paper example **150–300 ms**) so split votes are rare. Invariant: `broadcastTime ≪ electionTimeout ≪ MTBF`. Used by etcd, CockroachDB, TiDB, Kafka KRaft, YugabyteDB.
- **PostgreSQL 17 docs (fetched 2026-09-13).** Streaming physical replication is **async unless `synchronous_standby_names` is non-empty**. `synchronous_commit` default `on` then means "local flush"; with standbys named it means "standby durable flush".
- **Elhemali et al., ATC 2022 *Amazon DynamoDB*.** Per-partition **Multi-Paxos** group; only the lease-holding leader serves writes and strongly consistent reads; any replica serves eventually consistent reads. A typical group is **three storage replicas across AZs**; the paper adds *log replicas* (Paxos acceptors without the B-tree) to restore a write quorum faster than cloning a full replica. The new leader will not serve writes or consistent reads until the previous lease expires — fencing, owned by [quorums and fencing](../data-intensive-design/quorums-and-fencing.md) and [failover](Failover.md).
- **Kafka 4.3.** Single-leader *per partition*. Broker defaults (`default.replication.factor = 1`, `min.insync.replicas = 1`) are **dev-safe and prod-wrong**.

**Replica family ≠ consensus.** Single-leader *streaming* can lose acknowledged writes on failover. Single-leader *Raft/Paxos* cannot, short of losing a majority. Do not treat them as one durability class.

## Streaming vs consensus

**A. Streaming / WAL shipping (Postgres 17).** Leader writes WAL, standbys stream it. Default is **asynchronous**: `synchronous_standby_names` empty → commits do not wait for any replica. `synchronous_commit` default `on` then only waits for *local* flush.

| `synchronous_commit` (with standbys named) | What COMMIT waits for |
|---|---|
| `on` (default) | Standby has flushed the commit record to durable storage. |
| `remote_write` | OS write on the standby (survives Postgres crash, not OS crash). |
| `remote_apply` | Commit replayed and visible on the standby (causal read-your-writes *on that standby*; larger commit delay). |
| `local` / `off` | This transaction opts out of waiting. |

Slots vs `wal_keep_size`: default `wal_keep_size = 0` keeps **no extra** WAL for standbys. A disconnected replica that falls behind the last checkpoint is done unless (a) a replication slot holds WAL, (b) `wal_keep_size` is large enough, or (c) a WAL archive exists. Slots can fill `pg_wal`; `max_slot_wal_keep_size` default **-1** = unlimited. `max_wal_senders` default **10**, `max_replication_slots` default **10**. `wal_sender_timeout` / `wal_receiver_timeout` default **60 s**. `hot_standby` default **on**; `hot_standby_feedback` default **off** (on = fewer query cancels, more primary bloat). `max_standby_streaming_delay` default **30 s** (then cancel the conflicting standby query). `wal_receiver_status_interval` default **10 s** — this is what feeds `pg_stat_replication`.

**B. Consensus-backed (Raft / Multi-Paxos).** The leader is *elected*; a write is committed when a **majority** persists it. etcd: heartbeat **100 ms**, election timeout **1000 ms**, same on every member; election timeout ≥ **10× RTT**; hard cap **50 s** (global-cluster only). The Raft paper's own example interval is **150–300 ms** randomized — etcd chose a more conservative 1 s default for LAN. CockroachDB: each *range* is a Raft group, `num_replicas` default **3** (5 for `.meta` / `.liveness` / `.system` and for multi-region survive-region).

**C. Kafka per-partition leader + ISR.** Broker defaults (Kafka 4.3): `default.replication.factor = 1`, `num.partitions = 1`, `min.insync.replicas = 1`, `unclean.leader.election.enable = false`. The documented production pairing is RF **3**, `min.insync.replicas` **2**, producer `acks=all`. With `acks=all`, *every current ISR member* must ack, and if `|ISR| < min.insync.replicas` the producer gets `NotEnoughReplicas` / `NotEnoughReplicasAfterAppend`. Messages are not visible to consumers until they are on all in-sync replicas *and* the min-ISR condition holds. Unclean election (default off since 0.11.0.0) is the durability-vs-availability switch: a non-ISR leader can restore writes at the cost of losing committed messages. In KRaft, a dynamic enable waits for a periodic thread (docs: default **5 minutes**) unless `kafka-leader-election.sh --unclean` is run.

The *producer* `acks` default in 4.x clients was **not** re-verified per language this pass. The broker `min.insync.replicas=1` *is* verified.

**New followers.** A naive file copy sees different parts of the database at different times. The zero-downtime path is already in the [DDIA case](../data-intensive-design/single-leader-replication.md): consistent snapshot → copy → catch up from the named log position (Postgres LSN; MySQL binlog / GTID). Archive the replication log plus periodic snapshots to an object store — that is backup/DR *and* steps 1–2 of a new follower. Operational add: `wal_keep_size=0` without a slot or archive means a 2-hour blip is a full base-backup, not a resume.

**Follower failure vs leader failure.** Catch-up recovery is conceptually simple and operationally a load spike: high write throughput or a long outage means a large backlog on both sides. The leader may drop WAL it has already shipped to every *live* follower; a slot that holds it forever fills the disk. Leader failure — detect, choose, reconfigure — is [failover](Failover.md). This card only names the durability you had *before* the election: async streaming can lose the client-visible write; Raft/ISR+min-ISR cannot, short of losing a majority / falling below min-ISR.

## Streaming vs Raft — pick the commit meaning

| Need | Prefer | Do not |
|---|---|---|
| Money rows, one region, you can name a sync standby | Postgres `FIRST 1` + `synchronous_commit=on` | Empty `synchronous_standby_names` plus an SLO that says RPO 0 |
| Multi-AZ, majority persist, no human-named standby | Raft / DynamoDB Multi-Paxos / Kafka `acks=all` + min-ISR 2 | Kafka broker defaults (RF=1, min-ISR=1) |
| Read scale next to the writer | Async standbys + session guarantees ([lag](../data-intensive-design/replication-lag.md)) | `remote_apply` to *every* standby (sync-to-all stall) |
| Cross-region write availability | Do **not** name the remote as sync; or move the workload to [multi-leader](MultiLeaderReplication.md) / global tables | A 70 ms COMMIT wait you did not budget |
| Linearizable reads of the same key | Leader (or Raft leaseholder); DynamoDB consistent read = leader | An async follower, or DynamoDB eventually-consistent read, as if it were the leader |

## Verified defaults (fetched 2026-09-13)

| Knob | Postgres 17 | Kafka 4.3 | etcd (v3.6 docs) | DynamoDB (current + ATC 2022) | CockroachDB v26.2 |
|---|---|---|---|---|---|
| Replica count | 1 primary + N standbys (you attach them) | `default.replication.factor` **1** | cluster size (odd; 3 or 5 typical, not a single default) | 3 storage replicas / AZ-spread + optional log replicas | `num_replicas` **3** (5 for meta/liveness/system) |
| Durability | `synchronous_commit=on`; sync repl **off** until `synchronous_standby_names` set | `min.insync.replicas` **1**; `acks` is a *producer* setting | majority of members | write ack after quorum of WAL persists; consistent read = leader | Raft majority of `num_replicas` |
| Failure detection | `wal_sender_timeout` **60 s**, `wal_receiver_timeout` **60 s** | ISR + replica lag; unclean election **false** | heartbeat **100 ms**, election **1000 ms** | lease + peer failure-detect; new leader waits out old lease | Raft per range |
| Catch-up | replication slot or archive; `wal_keep_size` **0** | replica fetch; ISR shrink | (v3 snapshot policy not separately verified) | autoadmin + log replicas | automatic split/merge/rebalance |
| Read-on-replica | `hot_standby=on`; feedback **off**; cancel after **30 s** | consume any ISR (after min-ISR) | linearizable by default (Raft) | eventually consistent = any replica | leaseholder serves |

MongoDB replica-set election timeout and Cockroach follower-read staleness were **not** fetched — do not invent them. Patroni / pg_auto_failover fencing is [failover](Failover.md).

## Observability

| Signal | What it means | Where |
|---|---|---|
| **Replication lag** (write / flush / apply LSN or bytes/time) | Async replica staleness. Apply ≫ flush = replay bottleneck (CPU/IO/conflicts), not the network. | Postgres `pg_stat_replication` (`sent_lsn`, `write_lsn`, `flush_lsn`, `replay_lsn`, `*_lag`); updated at least every `wal_receiver_status_interval` (10 s). |
| **Commit wait** | Sync replica is the write SLO. | Postgres wait events `SyncRep`; `remote_apply` wait includes replay. |
| **ISR size / under-replicated partitions** | Kafka durability remaining. `\|ISR\| < min.insync.replicas` → writes fail with `acks=all`. | Broker metrics; `UnderReplicatedPartitions`. |
| **Leader distribution** | One node holds too many shard leaders. | Kafka `PreferredReplicaImbalance`; Cockroach leaseholder maps. |
| **Election rate / term** | Raft flapping. | etcd `etcd_server_leader_changes_seen_total`; disk `wal_fsync` duration (missed heartbeat → spurious election). |
| **Client op duration** | User-visible. | OTel `db.client.operation.duration` by system + operation + **shard bucket** — see [partitioning](Partitioning.md). |

Session guarantees on async followers — read-your-writes, monotonic reads, consistent prefix — are [replication lag](../data-intensive-design/replication-lag.md). Eventual consistency has **no bound**.

## Tuning

Defaults are *safe for a laptop*. Production values come from RTT, item size, and the failure you will actually take.

### Postgres 17 — name what COMMIT means

Measure intra-AZ RTT and cross-region RTT with ICMP *and* a WAL-sized payload — etcd's "use ping" under-reads disk.

| Deploy | `synchronous_standby_names` | `synchronous_commit` | What a COMMIT means | Failover ([C3](Failover.md)) |
|---|---|---|---|---|
| Laptop / CI | empty | `on` (default) | local flush only | local flush happened; *replica* data may be gone |
| One-AZ HA | `FIRST 1 (az1)` | `on` | primary + 1 standby durable | promote the sync standby; RPO ≈ 0 for that pair |
| Read scale in-region | empty or `FIRST 1` | `on` for money rows, `local` for telemetry | per-transaction durability | session-sticky read-your-writes |
| Cross-region | do **not** name the remote as sync | `on` locally | remote is async | accept RPO = replay_lag; or move the workload to Raft / global tables |

Always create a **replication slot** (or archive). `wal_keep_size=0` plus a 2-hour network blip is a full base-backup. Cap the slot with `max_slot_wal_keep_size` once you know peak WAL/hour × max-acceptable disconnect, or a stuck slot fills the disk and takes the primary down — the failure mode of "unlimited" (`-1`). Turn `hot_standby_feedback` on only after you measure primary bloat; the 30 s cancel is the other side of that trade-off.

`max_wal_senders` **10** and `max_replication_slots` **10** are enough for a laptop and tight for a fleet that also runs logical decoding / CDC (catalog B7). Count senders *before* you attach the fifth standby. `wal_sender_timeout` / `wal_receiver_timeout` **60 s** is the failure-detection feed into [failover](Failover.md) — it is not an election timeout; a 60 s silent primary is a minute of unknown RPO on async. `wal_receiver_status_interval` **10 s** is why `pg_stat_replication` can look stale for ten seconds while the standby is fine.

Semisync reminder: making *every* follower synchronous is impracticable — any one outage halts writes. Production "sync" is **one** named standby (or a majority via Raft) and the rest async. `remote_apply` on that one standby is how you buy read-your-writes *on that standby* without making every replica a commit waiter.

### etcd / Raft — time from measured RTT

Invariant from the Raft paper + etcd tuning page:

`heartbeat ≈ 0.5–1.5 × RTT`, `election_timeout ≥ 10 × RTT`, same values on every member, election timeout ≤ **50,000 ms**.

| Measured RTT | Heartbeat | Election timeout | Comment |
|---|---|---|---|
| 2 ms LAN | **100 ms** (default) | **1000 ms** (default) | 50× / 500× RTT — conservative, fine |
| 10 ms metro | 10–15 ms | ≥ 100 ms (etcd example) | defaults still work; lowering heartbeat saves little |
| 130 ms continental US (etcd's own figure) | ~130–200 ms | ≥ 1,300 ms; etcd discusses **5 s** as a safe *global* RTT upper and **50 s** as the election cap | defaults will **false-elect** |
| 350–400 ms US–Japan (etcd's figure) | do not run one etcd cluster across this | — | put a consensus cluster *in* each region; replicate the *data* with a different family |

Disk `fsync` p99 must sit well under the heartbeat. etcd's docs: other processes' disk IO → missed heartbeats → leader loss. `ionice` / dedicated disk / `performance` governor are the knobs, not a larger election timeout (that only hides the problem and lengthens failover). Same values on every member — mixed election timeouts are how you get a permanent minority leader. The hard cap **50 s** is for a *global* cluster you have already decided to run; etcd's own US–Japan 350–400 ms figure is "do not." Snapshot policy on the v3 backend was not separately verified this pass — do not copy a v2 `snapshot-count` of 10 000 into a v3 runbook.

### Kafka — ISR as the durability remaining

Start from the documented production triple: **RF=3, min.insync.replicas=2, acks=all**. Then size partitions for *throughput and consumer parallelism* ([partitioning](Partitioning.md)).

- Broker defaults (`RF=1`, `min.ISR=1`, `num.partitions=1`) acknowledge a write on **one** disk. That is not HA.
- One broker down: ISR=2 ≥ 2, writes live. Two brokers down: ISR=1 < 2, writes stop. That *is* the design.
- Enabling unclean election restores writes and **drops** the messages that only lived on the dead ISR — [failover](Failover.md)'s availability/durability fork. Record it in an ADR; it is not a Tuesday default.
- Consumers: messages are not visible until they are on all in-sync replicas *and* the min-ISR condition holds. A dashboard that shows produce-success and consume-lag as if they were independent is lying during an ISR shrink.

DynamoDB operational remainder: any replica may start an election; the winner holds a **lease** and will not serve writes or consistent reads until the previous lease expires. Log replicas restore a write quorum faster than cloning a full storage replica. That is fencing + catch-up, not a second writer — do not describe it as [multi-leader](MultiLeaderReplication.md).

## Testing and operating

- **Name COMMIT in a test.** Kill the async standby, commit, kill the primary, promote. If the client-visible row is gone, your SLO was lying. Repeat with `FIRST 1` / `acks=all`+min-ISR 2 and confirm the opposite.
- **Slot fill.** Pause a standby, write WAL until `max_slot_wal_keep_size` would have mattered. Default `-1` takes the primary down — that is the drill, not a surprise.
- **Raft false-elect.** Inject disk latency above the heartbeat (etcd: other processes' IO). Confirm leader changes. The fix is dedicated disk / `ionice`, not a larger election timeout that lengthens [failover](Failover.md).
- **ISR shrink.** Stop one Kafka broker at RF=3, min-ISR=2: produces live. Stop a second: produces fail with `NotEnoughReplicas*`. Enabling unclean election is a *separate* tested decision.
- **Half-open analogy.** A [breaker](CircuitBreaker.md) over the leader endpoint must be per shard. A blended error rate across shards never trips or takes the healthy two-thirds offline (Brooker / Azure resource differentiation).

## Placement

| Placement | What it owns | Trade-off |
|---|---|---|
| **Store-native streaming** (Postgres sync standbys) | Commit meaning you can name per transaction. | App cannot add HA later without a migration; one slow sync replica stalls writes. |
| **Store-native consensus** (etcd, Cockroach, DynamoDB, Kafka ISR+KRaft) | Majority persist before ack. | Write availability dies with the majority; election timeout is a latency *and* a false-elect knob. |
| **Read replicas** | Read scale, geo latency. | [Lag](../data-intensive-design/replication-lag.md); session stickiness or `remote_apply` for read-your-writes. |

## Failure modes

| Mode | How it happens | What to do |
|---|---|---|
| **Wrong-family commit** | Async Postgres / Kafka `acks=1` treated as "durable". Promote or unclean-elect and the client-visible write is gone. | Name the durability in the SLO. Money rows go through sync / majority / `acks=all` + min-ISR 2. |
| **Slot disk bomb** | Unlimited Postgres slot (`max_slot_wal_keep_size=-1`). Primary fills disk. | Cap the slot; page the replica. |
| **False Raft election** | Election timeout ≤ disk/network p99. | Measure fsync; dedicated disk; raise timeout with RTT, not with hope. |
| **Unclean / async promote** | Availability win, durability loss. | Product decision, recorded, tested. |
| **Sync-to-all stall** | Every standby is in the sync set; one slow replica blocks all writes. | Semisync: one sync + the rest async, or a majority via Raft. |
| **Blind breaker** | One breaker over "Postgres" trips healthy shards with a sick leader. | Break per shard ([circuit breaker](CircuitBreaker.md)). |

Catch-up recovery after a follower outage is conceptually simple and operationally a load spike — the leader may drop WAL it has already shipped to every *live* follower ([single-leader](../data-intensive-design/single-leader-replication.md)).

## When not to use this family

- You need **write availability through a region partition** — [multi-leader](MultiLeaderReplication.md) (and you pay conflicts) or a leader per region with async catch-up.
- You need **no failover** and can live with quorum staleness — [leaderless](LeaderlessReplication.md).
- You need a uniqueness or non-negative invariant *and* you were about to add a second writer. Stay single-leader for those keys.
- Cross-region sync streaming: do not name the remote as a sync standby. The commit wait *is* the WAN RTT.

## Trade-offs

| Buy | Pay |
|---|---|
| One writer: no concurrent-write merge | Write unavailable if you cannot reach the leader |
| Streaming async: write stays up if every follower is behind | Client-visible writes can vanish on failover |
| Semisync / `FIRST 1` | One slow sync replica stalls money rows; the rest of the fleet can still lag |
| Raft majority commit | Write stops when a majority is unreachable; election timeout is load-bearing |
| Kafka ISR + `acks=all` + min-ISR 2 | Two brokers down stops writes — that is the design, not a bug |
| Async followers for read scale | Unbounded lag; session guarantees are product work |

The leader decides **who may write**. Sync vs majority decides **what COMMIT means**. [Failover](Failover.md) decides **who writes next**. Do not treat "we have a standby" as a durability strategy.

Fully asynchronous is widely used when there are many followers or they are far away: the leader keeps writing if every follower is behind, and unreplicated writes are **lost** even after the client saw success. That weakening is a product decision, not an accident of defaults. Name it in the SLO, or name a sync/majority path for the rows that cannot take it. Session stickiness for read-your-writes, monotonic reads, and consistent prefix are the operational substitutes for a bound that eventual consistency will not give you.

## Leaves to siblings

| Sibling | What they take |
|---|---|
| [Failover](Failover.md) | Detect, elect, reconfigure; RTO/RPO; split-brain as a failure mode. |
| [Quorums and fencing](../data-intensive-design/quorums-and-fencing.md) | Lease tokens; majority-as-death. |
| [Partitioning](Partitioning.md) | Which shard this leader owns. |
| [Multi-leader](MultiLeaderReplication.md) / [leaderless](LeaderlessReplication.md) | When one writer is the wrong family. |
| [Replication lag](../data-intensive-design/replication-lag.md) | Session guarantees on async followers. |
| Catalog B7 | CDC / logical decoding from the same WAL. |

etcd disk knobs (`ionice`, dedicated disk, `performance` governor) sit here because they are *commit-path* timing, not a failover runbook. Mixed election timeouts across members are how you get a permanent minority leader — same values on every member, from measured RTT.

## Sources

Verified 2026-09-13; URLs, provenance, and items left out (Mongo election timeout, Cockroach follower-reads, Kafka client `acks` default, etcd v3 snapshot policy) are in the [external research note](../../docs/research/sysdesign/b2-partition-replicate-external-research.md).

- Canon: [single-leader-replication.md](../data-intensive-design/single-leader-replication.md); Raft ATC 2014; DynamoDB ATC 2022.
- Products: Postgres 17 runtime-config-replication / WAL / warm-standby; Kafka 4.3 broker + topic configs + Confluent replication design; etcd v3.6 / v3.8 tuning; CockroachDB v26.2 zone config; DynamoDB partitions + ATC 2022.
