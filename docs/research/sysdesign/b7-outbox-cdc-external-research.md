---
type: research
title: 'Transactional outbox & CDC — external research (2026-09-13)'
description: >-
  Source-verified research backing catalog B7: the dual-write problem,
  transactional outbox in the same DB transaction as the business write,
  polling vs log-tail CDC (Debezium 3.6.2, DynamoDB Streams, Postgres
  logical decoding), inbox/idempotent consumers, ordering, at-least-once,
  schema evolution, and relay failure modes.
tags: [research, system-design-patterns, B7, outbox, cdc]
---

# Transactional outbox & CDC — external research (2026-09-13)

> Evidence pass for catalog **B7** (Group B / CircuitBreaker depth bar).
> Primary pages fetched 2026-09-13. Paraphrase; numbers exact. Unverified
> items stay in §8. **Cite, do not rewrite:**
> [ch08.md](../../../cases/aws/ch08.md),
> [replication-logs.md](../../../cases/data-intensive-design/replication-logs.md),
> [A2](a2-pubsub-queues-external-research.md),
> [A6](a6-api-contracts-external-research.md),
> [B4](b4-strangler-fig-external-research.md).

---

## 1. Scope and non-goals

**This note owns** how a service turns a committed business write into a
durable, eventually published event *without* a distributed transaction
across the database and the broker. Operational depth: the dual-write
failure modes; the outbox write in the *same* local transaction; polling
vs log-tail relays; Debezium / DynamoDB Streams / Postgres logical
decoding knobs; inbox/idempotent consumers (point **C9**); ordering,
at-least-once, and payload schema evolution (point **A6**); and how the
relay itself fails.

**Stays in sibling catalog ids**

| Id | Why it is not this card |
|---|---|
| **A2** Pub/sub, queues & streams | Transport once the event is *on* a channel: DLQ, competing consumers, fan-out, broker acks. B7 ends at "relay published." |
| **A6** API contracts & versioning | How a published contract evolves (REST/gRPC/GraphQL). Event *payload* Avro/protobuf rules live in [avro-schema-evolution](../../../cases/data-intensive-design/avro-schema-evolution.md) / [protobuf-schema-evolution](../../../cases/data-intensive-design/protobuf-schema-evolution.md); this note only names the outbox/CDC hook. |
| **B5** Saga | Orchestration / choreography that *uses* an outbox to emit a saga step. Do not restack saga recovery here. |
| **C9** Idempotency & deduplication | The consume-side inbox. This note names the pairing and the Azure/Richardson mechanics; C9 owns the general card. |
| **E4** Event-driven architecture | Style. Mechanisms live in A2/B7 (catalog). |
| **E12** CQRS & event sourcing | Style-level SoR. Event sourcing is a *sibling* dual-write fix (Confluent; ch08 contrast), not this card. |
| **replication-logs.md** | WAL / binlog / logical-row *storage*. Cite; do not re-derive statement vs physical vs logical. |
| **ch08.md** | CDC taxonomy (audit columns, log-based, stream-based, table deltas, trigger-based) and the one-line outbox. Cite; do not rewrite. |

**Non-goals.** 2PC / XA across DB + broker as a recommended path;
rewriting [event-sourcing-cqrs](../../../cases/data-intensive-design/event-sourcing-cqrs.md);
warehouse/lake CDC product matrices; a second A2 transport card.

---

## 2. Lineage / vocabulary

**Dual-write.** Two independent writes cannot be atomic without a
spanning transaction. Fail after the first commit → **lost event**
(state changed, nobody notified) or **phantom event** (broker has a
fact the DB rolled back). Kleppmann (2015-05-27, also B4): two clients
dual-writing key X leave store 1 at B and store 2 at A — **permanent**
inconsistency, no error.
https://martin.kleppmann.com/2015/05/27/logs-for-data-infrastructure.html
Confluent (Waldron, 2024-05-29) anti-patterns: reverse the order; wrap
the Kafka produce in a DB txn (produce is not rolled back); in-memory
retry after a crash that purged the event.
https://www.confluent.io/blog/dual-write-problem/

**Transactional outbox (Richardson).** Store the message in the same
DB transaction as the business write; a separate **relay** publishes.
Forces: no 2PC; messages leave iff the DB commits; order is the
application's send order across instances of the same aggregate.
Relational = a table; NoSQL = a document property or a second item in
the same atomic batch. Drawback: forgotten insert. Issue: relay can
publish twice (crash after produce, before recording) → idempotent
consumers.
https://microservices.io/patterns/data/transactional-outbox.html

**Two relays (Richardson).** **Polling publisher** — `SELECT` unsent
rows, publish, mark/delete. Any SQL; "tricky to publish events in
order"; not all NoSQL.
https://microservices.io/patterns/data/polling-publisher.html
**Transaction log tailing** — MySQL binlog / Postgres WAL / DynamoDB
streams. Accurate; DB-specific; "tricky to avoid duplicate
publishing."
https://microservices.io/patterns/data/transaction-log-tailing.html

**Debezium (Morling, 2019-02-19; SMT update 2019-09-13).** Outbox
keeps *read-your-own-writes* on the request path and gives other
services reliable, replayable, eventually consistent propagation. The
custom SMT in the post is obsolete; use Event Router.
https://debezium.io/blog/2019/02/19/reliable-microservices-data-exchange-with-the-outbox-pattern/

**Azure** (`ms.date` 2026-02-23; `updated_at` 2026-02-27). Cosmos:
`TransactionalBatch` in one logical partition + change feed + Service
Bus. Consume-side companion: **Idempotent Consumer / inbox**.
https://learn.microsoft.com/en-us/azure/architecture/databases/guide/transactional-out-box-cosmos
· https://learn.microsoft.com/en-us/azure/architecture/patterns/idempotent-consumer

**AWS Prescriptive Guidance.** (1) RDS outbox in the same
`@Transactional`, scheduled poller → SQS; (2) DynamoDB Streams /
Kinesis CDC of the item or a dedicated outbox item. Duplicates →
idempotent consumer. Order via timestamps + sequence numbers.
Rollback → do not notify. Cross-service txns → **B5** saga.
https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html

**Workspace (link only).** [ch08.md](../../../cases/aws/ch08.md): CDC
taxonomy (audit columns, log-based/Debezium, stream-based/DynamoDB
Streams, table deltas, triggers) and the one-line outbox; event
sourcing vs CDC (intent vs state-change log).
[replication-logs.md](../../../cases/data-intensive-design/replication-logs.md):
logical row log (MySQL binlog beside WAL; Postgres decodes WAL) is
what external CDC parses.

---

## 3. Mechanics (Group B depth)

### 3.1 What the pattern is

One local ACID transaction writes (a) the business row and (b) an
outbox row / event document / item. After commit, a **relay** that is
*not* on the request path publishes (b) to a broker. The request path
never talks to the broker. Delivery is **at-least-once**: the relay
retries until the broker acks, so a crash between ack and "mark
published" republishes. Consumers therefore need an **inbox** (C9).

That is *not* event sourcing (E12): the business table stays SoR; the
outbox is a queue of facts to emit and is usually deleted or TTL'd.
It is *not* A2: the broker is a destination, not the subject.

### 3.2 Dual-write shapes this replaces

| Failure | Symptom | Outbox outcome |
|---|---|---|
| Commit then crash before produce | Lost event; downstream never learns | Relay sees the committed row later |
| Produce then DB rollback | Phantom event; payment for a missing order | Produce never happens |
| Two writers, two stores (Kleppmann) | Permanent split-brain on the same key | Single writer; second store is a consumer |
| Reorder: Kafka first, then DB (Confluent) | Phantom if the DB write fails | Still dual-write |
| DB transaction wrapping a Kafka send | Event already left when the txn rolls back | Outbox insert is *inside* the txn |

### 3.3 Variants (where the event is stored, how it is relayed)

| Variant | Atomic write | Relay | Trade-off |
|---|---|---|---|
| **Polling outbox** (Richardson; AWS RDS sample) | `INSERT` business + outbox in one SQL txn | Periodic `ORDER BY id` / timestamp; publish; delete or mark | Works on any SQL; poll load + lag; delete-after-send races with crash (at-least-once) |
| **Log-tail outbox** (Richardson; Debezium SMT) | Same SQL txn; connector captures *only* the outbox table | WAL/binlog → Kafka; Event Router SMT unwraps payload | Near-real-time; no poll tax on the table; DB-specific; WAL/slot ops |
| **Document / item outbox** (Azure Cosmos; AWS DynamoDB) | `TransactionalBatch` (same logical partition) or `TransactWriteItems` (≤ 100 actions, 4 MB) | Change feed / Streams → bus | No 2PC; partition-key / item-identity constraints |
| **CDC of the business table** (AWS "CDC" option; ch08 log-based) | The business write *is* the event | Connector emits `op=c/u/d` | No forgotten outbox insert; consumers see storage shape, not a designed event; schema coupling (A6) |
| **Listen-to-yourself** (Confluent) | Write the event to Kafka first | A consumer materializes the DB | Fast ack; **no** read-your-own-writes (Morling's objection) |
| **Event sourcing** (Confluent / E12) | Append-only event is the write | CDC or a publisher flag | No separate outbox; SoR *is* the log |

These compose: an outbox table + Debezium + Event Router is the
canonical log-tail shape. Cosmos change feed + Service Bus is the
same automaton on a document store.

### 3.4 Ordering, at-least-once, schema (point A6)

**Ordering.** Richardson: T1→E1 before T2→E2 for one aggregate, even
across instances. Debezium Event Router keys Kafka with `aggregateid`
so one aggregate hits one partition. Azure: change-feed order is
**per logical partition**; Service Bus `SessionId = partitionKey` is
FIFO per contact. DynamoDB Streams: order is **per item** (not per
partition); Lambda keeps that when `ParallelizationFactor` > 1. AWS
PG: timestamps + sequence numbers. Cross-aggregate global order is
A2 (single partition / session / FIFO).

**At-least-once.** Relays that checkpoint *after* produce republish on
crash. Cosmos change-feed processor: exception → restart from last
lease. Lambda: "process each event at least once." Richardson: crash
after publish before recording. Close is the C9 inbox.

**Schema (point A6, do not redo).** Outbox `payload` is a published
contract. Morling: emit an *external* event so `PurchaseOrder` table
changes do not break consumers. SMT default is JSON (`jsonb`); Avro
via `BinaryDataConverter` + a registry. Postgres connector:
default-value propagation is "primarily … for safe schema evolution
when using … a schema registry"; defaults can appear late, early, or
never. Full rules stay in A6 +
[avro-schema-evolution](../../../cases/data-intensive-design/avro-schema-evolution.md)
/ [encoding-overview](../../../cases/data-intensive-design/encoding-overview.md).
CDC-of-the-business-table *is* the internal schema on the wire.

### 3.5 Inbox / idempotent consumers (point C9)

Azure Idempotent Consumer: most brokers are at-least-once; broker
"exactly-once" does not cover external side effects. Inbox = processed
key **in the same txn** as side effects; uniqueness constraint
arbitrates competing consumers. Key = producer `MessageId` or
CloudEvents `source`+`id`, **not** `CorrelationId` or a regenerated
delivery id. Service Bus send-side `MessageId` window is a
producer-retry filter, **not** an inbox. Inbox TTL must outlast
redelivery / DLQ-resubmit. C9 owns the general card.

### 3.6 Placement

| Layer | What it does | Failure if misplaced |
|---|---|---|
| **Request path** | One local txn: business + outbox | Talking to Kafka/SQS here *is* dual-write |
| **Relay (poller, Debezium, change-feed processor, Lambda/Pipes)** | Publish committed outbox rows | Treating it as optional "best effort" loses the guarantee |
| **Broker (A2)** | Persist, fan-out, DLQ | Using it as the first write unless you accepted listen-to-yourself |
| **Inbox (C9)** | Atomic consume + marker | Check-then-set without a unique constraint double-applies |
| **Saga orchestrator (B5)** | Decides *which* events the outbox emits | Putting saga state only in the broker |

---

## 4. Verified defaults / standards (knobs)

Fetched 2026-09-13. Debezium numbers are from the **stable** docs
whose example envelope carries `"version": "3.6.2.Final"` (release
2026-09-01; series page https://debezium.io/releases/3.6/). 3.7.0.Beta1
(2026-08-26) is **not** used as a default source.

### 4.1 Debezium PostgreSQL connector (3.6.2.Final)

https://debezium.io/documentation/reference/stable/connectors/postgresql.html

| Knob | Default | Outbox / CDC use |
|---|---|---|
| `snapshot.mode` | `initial` | Snapshot iff no offsets for the logical name; then stream from stored LSN. `no_data` starts at slot-create LSN (only if WAL still holds everything). `when_needed` snapshots if offsets are missing or the LSN is gone. `always` after failover when WAL was pruned. |
| `snapshot.isolation.mode` | `serializable` | Strictest; blocks concurrent DDL / index creation on captured tables for the snapshot. `read_committed` is the "mirroring" trade (possible double-capture of rows inserted during the snapshot). |
| `snapshot.fetch.size` | `10240` | Rows per snapshot batch. |
| `snapshot.lock.timeout.ms` | `10000` | Snapshot fails if locks are not acquired in 10 s. `snapshot.locking.mode` default `none`. |
| `incremental.snapshot.chunk.size` | `1024` | Ad-hoc / watermarked snapshot while streaming continues. Watermark default `insert_insert`. |
| `poll.interval.ms` | `500` | Wait per iteration for new events; **capped at 5000 ms** if you set higher. |
| `max.batch.size` / `max.queue.size` | `2048` / `8192` | Queue must stay larger than batch; `max.queue.size.in.bytes` `0` (unlimited). |
| `heartbeat.interval.ms` | `0` (off) | Required when captured tables are quiet but the WAL is busy — otherwise LSN is never flushed and WAL piles up. With `lsn.flush.mode=connector_and_driver` and no txn metadata, Debezium **internally sets 600000 ms (10 min)**. |
| `plugin.name` | `decoderbufs` | RDS / Cloud SQL / IAM setups must set **`pgoutput`**. `publication.autocreate.mode` default `all_tables` (needs `CREATE PUBLICATION … FOR ALL TABLES`; docs recommend `filtered` if the user is not superuser). `publication.name` `dbz_publication`. |
| `slot.name` | `debezium` | Unique per connector. `slot.drop.on.stop` **`false`** — leaving it `true` in prod drops the resume point. `slot.max.retries` 6, `slot.retry.delay.ms` 10000. |
| `lsn.flush.mode` | `connector` | Debezium flushes LSN after each logical event. `manual` = you flush or WAL grows without bound. |
| `tombstones.on.delete` | `true` | Follows a delete with a tombstone for Kafka log compaction. Outbox tables that are insert-only should usually set this **false** (SMT already filters deletes). |
| `tasks.max` | `1` | Single-task connector. |
| `event.processing.failure.handling.mode` | `fail` | `warn` / `skip` drop the bad event. |
| `skipped.operations` | `t` | Truncates skipped. `status.update.interval.ms` **10000**. |

MySQL common knobs (same fetch): `snapshot.mode=initial`,
`heartbeat.interval.ms=0`, `incremental.snapshot.chunk.size=1024`,
`max.batch.size=2048`, `max.queue.size=8192`.
https://debezium.io/documentation/reference/stable/connectors/mysql.html

### 4.2 Debezium Outbox Event Router SMT

https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html

Expected columns: `id` uuid, `aggregatetype`, `aggregateid`, `type`,
`payload` jsonb. SMT class
`io.debezium.transforms.outbox.EventRouter`.

| Option | Default |
|---|---|
| `table.field.event.id` | `id` (copied to header `id` for consumer dedup) |
| `table.field.event.key` | `aggregateid` (Kafka key → per-aggregate order) |
| `table.field.event.payload` | `payload` |
| `table.expand.json.payload` | `false` |
| `table.op.invalid.behavior` | `warn` (`error` / `fatal`); **updates are not allowed** — outbox is insert-only; deletes are filtered |
| `route.by.field` | `aggregatetype` |
| `route.topic.replacement` | `outbox.event.${routedByValue}` |
| `route.tombstone.on.empty.payload` | `false` |
| `tracing.span.context.field` | `tracingspancontext` |
| `tracing.operation.name` | `debezium-read` |

Capture **only** the outbox table (`table.include.list`); apply the
SMT via a predicate so heartbeats / schema-change events are not
routed as domain events. Not compatible with the MongoDB connector
(separate Mongo SMT).

### 4.3 PostgreSQL logical decoding (storage side — cite replication-logs)

https://www.postgresql.org/docs/current/runtime-config-wal.html ·
https://www.postgresql.org/docs/current/runtime-config-replication.html
(PG 18/current, fetched 2026-09-13)

| GUC | Default | CDC consequence |
|---|---|---|
| `wal_level` | `replica` | Must be **`logical`** (restart) to decode row events. `logical` increases WAL volume, "particularly if many tables are configured for `REPLICA IDENTITY FULL`". |
| `max_replication_slots` | `10` | One slot per Debezium connector (+ headroom). Restart. |
| `max_wal_senders` | `10` | ≥ slots + physical standbys. `0` disables replication. Restart. |
| `max_slot_wal_keep_size` | `-1` (unlimited) | A stalled slot retains WAL forever and can fill the disk. A finite cap **invalidates** the slot when `restart_lsn` lags more than the cap — CDC then needs `snapshot.mode=when_needed` / `always`. PG 13+. |

`REPLICA IDENTITY DEFAULT` (Postgres default for user tables): UPDATE
/ DELETE carry the old PK only; unchanged TOAST values are omitted.
Debezium substitutes `unavailable.value.placeholder`
(`__debezium_unavailable_value`). Outbox payloads that live in `jsonb`
avoid that hole if the whole event is in one column.

### 4.4 DynamoDB Streams + Lambda / Pipes

https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html
· https://docs.aws.amazon.com/lambda/latest/dg/with-ddb.html
· https://docs.aws.amazon.com/lambda/latest/api/API_CreateEventSourceMapping.html
· https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_TransactWriteItems.html
· GetShardIterator: iterator expires **15 minutes**.

| Knob | Verified number |
|---|---|
| Stream retention | **24 hours** (fixed). Older records "susceptible to trimming at any moment." Disable → still readable 24 h, then gone. |
| `StreamViewType` | `KEYS_ONLY` / `NEW_IMAGE` / `OLD_IMAGE` / `NEW_AND_OLD_IMAGES`. **Cannot be edited** in place — disable and recreate. |
| Per-item order | Guaranteed for one primary key; **not** across a partition. ≤ **2** readers per shard (1 recommended on global tables). |
| Lambda poll | Base **4 times per second** per shard. |
| `BatchSize` | Default **100**, max 10 000. `MaximumBatchingWindowInSeconds` default **0**; if `BatchSize` > 10, window must be ≥ 1. Window max 300 s (docs also say buffer "up to 5 minutes"). Payload cap 6 MB. |
| `ParallelizationFactor` | Default **1**, max **10**; still per-item order. |
| `StartingPosition` | `LATEST` can miss events while the mapping is created/updated ("several minutes"); use `TRIM_HORIZON` if you cannot miss. |
| `TransactWriteItems` | Up to **100** actions, aggregate **4 MB**, distinct items, same account/Region. |

EventBridge Pipes can replace the Lambda relay (filter
`eventName: INSERT`, retries, DLQ) — AWS Compute Blog, no extra
numeric defaults fetched beyond Streams itself.

### 4.5 Azure Cosmos outbox + Service Bus

https://learn.microsoft.com/en-us/azure/cosmos-db/transactional-batch
· https://learn.microsoft.com/en-us/azure/cosmos-db/concepts-limits
· https://learn.microsoft.com/en-us/azure/service-bus-messaging/duplicate-detection

| Knob | Verified number |
|---|---|
| `TransactionalBatch` | Same logical partition; **100** operations; payload **2 MB**; execution **5 s**. Failure → that op's status; others **424**. Create-exists → **409**. Snapshot isolation. |
| Sample change-feed processor | `WithMaxItems(25)`, `WithPollInterval(3 s)`, `WithStartTime(2000-01-01)` (replay from the beginning of the feed). **Sample knobs, not platform defaults.** |
| Event `ttl` in the sample JSON | `120` seconds. Production text: "multiple days, like **10 days**" so a down relay/bus can catch up. Business docs use `ttl: -1` (never expire). |
| Service Bus duplicate detection | Default history window **10 minutes**; min 20 s; max **7 days**. Standard/Premium only. Dedup key = `MessageId` (or `MessageId+PartitionKey` when partitioned). **Does not** replace the inbox. |

### 4.6 Observability

Emit at least:

| Signal | Why |
|---|---|
| **Outbox lag** (oldest unrelayed row age, or Debezium `MilliSecondsBehindSource` / DynamoDB `IteratorAge`) | The user-visible consistency window. |
| **Relay publish rate vs business-write rate** | Growing gap = stuck slot / lease / poller. |
| **WAL / slot size** (`pg_replication_slots`, `restart_lsn` vs current LSN) | Heartbeat off + quiet captured tables = disk fill. |
| **SMT / converter errors** (`table.op.invalid.behavior` warnings; Avro registry rejects) | A6 mismatch shows up here, not as a 5xx from the writer. |
| **Inbox duplicate rate** (C9) | Rising rate → producer retries, undersized ack/lock, or a flapping relay. |
| **Change-feed lease owner / Lambda iterator age** | Silent stall after a processor crash. |

Alert shapes (own formulations — **not** vendor PromQL; see §8):
*iterator age / outbox lag above the consumer SLO*; *replication slot
invalidated* (`max_slot_wal_keep_size`); *Debezium connector `fail`
state*; *change-feed processor not checkpointing*.

OTel: SMT field `tracingspancontext`, op `debezium-read`. No
outbox-specific semantic convention found (§8).

### 4.7 Tuning

| Knob | Too aggressive | Too timid | Starting point (sourced) |
|---|---|---|---|
| Relay style | Poll every 10 ms on a hot OLTP primary | CDC "later" with no lag SLO | Log-tail for prod OLTP (Morling); poll is the compatibility fallback (Richardson) |
| `heartbeat.interval.ms` | Flood the heartbeat topic | `0` on a shared WAL with quiet outbox | Non-zero whenever captured traffic ≪ WAL traffic (Debezium WAL-disk section) |
| `snapshot.mode` | `always` on every bounce | `no_data` after a slot recreate | `initial`; `when_needed` if WAL can be pruned |
| `max_slot_wal_keep_size` | Tiny cap → constant resnapshot | `-1` → one dead connector fills disk | Finite cap + alert + `when_needed` |
| Inbox / Service Bus window | 20 s (late redelivery looks new) | 7-day send-side dedup as the *only* defense | Inbox TTL > broker redelivery + DLQ hold; Service Bus window is extra |
| CDC of business table vs outbox | Every column change is a public event | Forgotten outbox insert | Outbox when the event is a designed contract (Morling); CDC-of-table for warehouse mirrors (ch08) |

### 4.8 Worked calibration — checkout `OrderPlaced`

Design drill (not a vendor SLA). Constraints: 200 writes/s to
`orders`; one `OrderPlaced` event per write; Kafka consumers must see
per-order order; p99 relay lag ≤ 2 s; crash of the API pod must not
lose the event; payment consumer is not naturally idempotent.

| Step | Choice | Why |
|---|---|---|
| Atomic write | `INSERT orders` + `INSERT outbox` in one Postgres txn; columns match the SMT defaults (`id`, `aggregatetype='Order'`, `aggregateid=orderId`, `type='OrderPlaced'`, `payload` jsonb) | Richardson + Debezium table |
| Relay | Debezium Postgres 3.6.2, `table.include.list=public.outbox`, Event Router SMT, `tombstones.on.delete=false` | Insert-only queue; no poll tax |
| Plugin | `plugin.name=pgoutput` (RDS), publication `filtered` to `public.outbox` | Default `decoderbufs` is not on RDS; `all_tables` needs superuser |
| Snapshot | `snapshot.mode=initial` once; then streaming | Empty outbox snapshot is cheap |
| Heartbeat | `heartbeat.interval.ms=10000` + `heartbeat.action.query` touching a tiny table in *this* DB if sibling DBs share the instance | Quiet outbox on a busy WAL |
| Ordering | Kafka key = `aggregateid` | SMT default |
| Consumer (C9) | Inbox row keyed by header `id`; unique constraint; same txn as the payment hold | Azure inbox; at-least-once |
| Schema (A6) | Payload Avro in the registry, BACKWARD compat; do **not** CDC the `orders` table as the public event | Morling external event |
| Rollback drill | Kill the API after `COMMIT`, before any produce — event must still appear. Kill Debezium after Kafka ack, before offset flush — consumer inbox absorbs the duplicate. | Relay failure modes below |

---

## 5. Failure modes and when-not-to-use

**Failure modes of the outbox / CDC path itself**

- **Forgotten outbox insert** (Richardson's drawback). CDC-of-the-
  business-table avoids it and couples consumers to storage.
- **Relay crash after publish, before checkpoint** — duplicate. Inbox
  (C9), not "exactly-once Kafka," is the fix.
- **Poller `DELETE` before broker ack** (AWS sample deletes after
  `sendMessageBatch` — if the process dies after send and before
  delete, at-least-once; if you inverted the order you **lose** the
  event). Mark-then-delete only after ack.
- **WAL / slot stall.** `heartbeat.interval.ms=0` + quiet captured
  tables: LSN never flushed, `pg_wal` grows. `max_slot_wal_keep_size=-1`
  makes it unbounded; a finite cap invalidates the slot and you miss
  data unless you resnapshot.
- **`slot.drop.on.stop=true` in production** — next start has no
  resume LSN.
- **Wrong `plugin.name`** (`decoderbufs` on RDS) — connector never
  streams.
- **TOAST / `REPLICA IDENTITY DEFAULT`** — UPDATE/DELETE events miss
  unchanged wide columns (`__debezium_unavailable_value`).
- **Outbox UPDATE** — SMT `table.op.invalid.behavior=warn` by default
  (skip + log); `fatal` stops the connector. Treat the table as
  insert-only.
- **Cosmos / Dynamo partition rules.** Events for a different
  partition key cannot join the batch (`TransactionalBatch`) or the
  same item cannot appear twice (`TransactWriteItems`).
- **DynamoDB 24 h trim.** A relay down > 24 h **cannot** catch up;
  `TrimmedDataAccessException`. Iterator idle > 15 min expires.
- **`LATEST` on a new Lambda mapping** — missed records during the
  "several minutes" of eventual-consistent polling.
- **More than two readers per Streams shard** — throttle.
- **Service Bus 10-minute dedup as the only inbox** — redelivery
  after the window is a new message. Azure says this explicitly.
- **Listen-to-yourself** — lost read-your-own-writes (Morling).
- **Schema break on the payload** (A6) — registry reject stalls the
  connector (`fail` default).
- **Trigger-based CDC** (ch08) — write amplification on the primary.

**When not to use (sourced)**

| Situation | Source | Prefer |
|---|---|---|
| A single process, one database, no other consumer | Implicit in every dual-write write-up | Just the transaction |
| Naturally idempotent upsert / event-carried state | Azure C9 "not suitable" | Skip the inbox; still use outbox if you must notify |
| Storage has no transactions and you cannot append events | Confluent | Listen-to-yourself (accept stale reads) or E12 |
| Cross-service atomicity of *several* stores | AWS PG | **B5** saga, each step using an outbox |
| You need the broker to be SoR and replay forever | Confluent event sourcing; E12; ch08 contrast | Event-sourced log, not a deletable outbox |
| Warehouse mirror of *tables*, not domain events | ch08 CDC | Log-based CDC of the tables (replication-logs.md) |
| Greenfield where the first write *is* Kafka and stale reads are OK | Confluent listen-to-yourself | Skip the outbox table |

---

## 6. Cross-links

- **Catalog:** B7 in [system-design-patterns-catalog.md](system-design-patterns-catalog.md).
- **Siblings:** A2 transport · A6 payload · B4 strangler dual-write · B5 saga · C9 inbox · E4 / E12 styles.
- **Cite, do not rewrite:** [ch08.md](../../../cases/aws/ch08.md) ·
  [replication-logs.md](../../../cases/data-intensive-design/replication-logs.md) ·
  [event-driven-dataflow.md](../../../cases/data-intensive-design/event-driven-dataflow.md) ·
  [event-sourcing-cqrs.md](../../../cases/data-intensive-design/event-sourcing-cqrs.md) ·
  [distributed-transactions.md](../../../cases/data-intensive-design/distributed-transactions.md) ·
  [avro-schema-evolution.md](../../../cases/data-intensive-design/avro-schema-evolution.md) ·
  [encoding-overview.md](../../../cases/data-intensive-design/encoding-overview.md).
- **Depth-bar (topics not copied):**
  [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md),
  [RetryBackoff.md](../../../cases/SystemDesignPatterns/RetryBackoff.md).

---

## 7. Sources

Retrieved 2026-09-13.

**Canon.** microservices.io/patterns/data/transactional-outbox.html ·
microservices.io/patterns/data/polling-publisher.html ·
microservices.io/patterns/data/transaction-log-tailing.html ·
debezium.io/blog/2019/02/19/reliable-microservices-data-exchange-with-the-outbox-pattern
(SMT update 2019-09-13) ·
martin.kleppmann.com/2015/05/27/logs-for-data-infrastructure.html ·
confluent.io/blog/dual-write-problem (2024-05-29) ·
learn.microsoft.com/en-us/azure/architecture/databases/guide/transactional-out-box-cosmos
(`ms.date` 2026-02-23) ·
learn.microsoft.com/en-us/azure/architecture/patterns/idempotent-consumer ·
docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html
· aws.amazon.com/blogs/compute/implementing-the-transactional-outbox-pattern-with-amazon-eventbridge-pipes

**Debezium 3.6.2.Final (2026-09-01).**
debezium.io/releases/3.6 ·
debezium.io/blog/2026/09/01/debezium-3-6-2-final-released ·
debezium.io/documentation/reference/stable/connectors/postgresql.html ·
debezium.io/documentation/reference/stable/connectors/mysql.html ·
debezium.io/documentation/reference/stable/transformations/outbox-event-router.html
· debezium.io/documentation/reference/stable/configuration/signalling.html

**Postgres / DynamoDB / Cosmos knobs.**
postgresql.org/docs/current/runtime-config-wal.html ·
postgresql.org/docs/current/runtime-config-replication.html ·
docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html ·
docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_streams_GetShardIterator.html
· docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_TransactWriteItems.html
· docs.aws.amazon.com/lambda/latest/dg/with-ddb.html ·
docs.aws.amazon.com/lambda/latest/api/API_CreateEventSourceMapping.html ·
learn.microsoft.com/en-us/azure/cosmos-db/transactional-batch ·
learn.microsoft.com/en-us/azure/cosmos-db/concepts-limits ·
learn.microsoft.com/en-us/azure/cosmos-db/change-feed-processor ·
learn.microsoft.com/en-us/azure/service-bus-messaging/duplicate-detection

**Workspace.** cases/aws/ch08.md · cases/data-intensive-design/replication-logs.md · docs/research/sysdesign/system-design-patterns-catalog.md · a2 / a6 / b4 research notes

---

## 8. Uncertain / left out (excluded from the Concept)

- Kleppmann 2015 body not re-fetched; permanent-inconsistency claim
  and date are B4's.
- Defaults are **stable 3.6.2**, not nightly / 3.7 Beta / Confluent's
  older packaged connector page (`never` snapshot mode ignored).
- `decoderbufs` as connector default vs whether stock PG 16+ / RDS
  ships the extension — not probed (docs: set `pgoutput` on RDS).
- AWS sample `sqs.polling_ms` / `batchSize`; EventBridge Pipes
  retry/DLQ numbers; NServiceBus / MassTransit outbox retention —
  not opened.
- Cosmos change-feed **platform** defaults for `MaxItems` / poll
  (sample uses 25 / 3 s) — not found.
- Service Bus PeekLock / session lock — C9 / A2.
- DynamoDB → Kinesis Data Streams path in the AWS PG CDK snippet —
  mentioned, not knob-audited.
- PromQL recipes and outbox-specific OTel conventions — none found;
  §4.6 shapes are this note's.
- ch08 / DDIA book text not copied; trigger/audit/snapshot-diff CDC
  has no numeric source; Cosmos "All versions and deletes" unused.
