---
type: research
title: 'Publisher–subscriber, queues & streams — external research (2026-09-13)'
description: >-
  Source-verified research backing the Pub/sub Concept (A2): the EIP pattern
  set, queue vs log vs visibility-timeout consume models (RabbitMQ, Kafka,
  SQS), precise ordering scopes and their caveats, dead-letter mechanics with
  defaults (SQS retention subtlety, RabbitMQ x-death, Pub/Sub permissions),
  fan-out topologies (SNS filter limits, consumer groups, KIP-848, exchanges),
  poison-message bounds and backlog levers, push-vs-pull delivery policies,
  and schema-registry compatibility modes.
tags: [research, pubsub, queues, kafka, rabbitmq, sqs, system-design-patterns]
---

# A2 Publisher–subscriber, queues & streams — external research (2026-09-13)

**Method.** Facts verified against primaries 2026-09-13 (RabbitMQ 4.x docs, Kafka 4.3 configs, live AWS/GCP/Confluent pages). **[cited forward]** = verified in [idempotency-dedup-external-research.md](idempotency-dedup-external-research.md) (FIFO dedup windows, visibility 30 s/12 h, idempotent producer/EOS, EventBridge retries, Pub/Sub exactly-once), [load-shedding-backpressure-external-research.md](load-shedding-backpressure-external-research.md) (max.poll.*), [retry-backoff-external-research.md](retry-backoff-external-research.md)/[circuit-breaker-external-research.md](circuit-breaker-external-research.md) (Spring Kafka DefaultErrorHandler → <topic>-dlt; Connect errors.tolerance; pause/resume rebalance loss).

## 1. EIP canon

Publish-Subscribe Channel (a copy per subscriber) · Point-to-Point Channel (exactly one receiver consumes; the channel arbitrates) · Competing Consumers (only on point-to-point — "multiple consumers on a Publish-Subscribe Channel just create more copies"; concurrency sacrifices cross-consumer ordering; key what must stay ordered) · Message Router (consume one channel, republish by condition, message unmodified) · Dead Letter Channel (the *messaging system* moves undeliverable/expired/over-limit messages) · Invalid Message Channel (the *receiver* moves contract-violating messages — the split modern DLQs conflate) · Guaranteed Delivery (store-and-forward; delete only after the next store holds it).

## 2. Queue vs log vs cloud queue

- **RabbitMQ**: ordered FIFO; ack discards (destructive); nack/channel-death → redelivery with `redeliver` set. `basic.qos` prefetch bounds *unacked* deliveries; unlimited when unset (quorum queues effectively cap ~2,000); per-consumer by default (global=true = channel-wide). **Quorum queues** (Raft) are the stated default choice for replicated queues; 4.x **delivery-limit defaults to 20** (3.13: none; −1 restores), tracked in `x-delivery-count`; over → drop or DLX.
- **Kafka**: retained log; consumption = advancing an offset (`seek*`); per-topic retention bounds replay; partition is the ordering unit ("exactly the same order as they were written").
- **SQS**: receive hides for the visibility timeout (default 30 s [cited forward]); delete or it reappears; `ChangeMessageVisibility` extends up to a hard **12 h from first receipt** (extensions don't reset it); 0 releases immediately; ~120,000 in-flight cap (standard).

| | RabbitMQ | Kafka | SQS |
|---|---|---|---|
| Consume | ack-discard | cursor over retained log | hide-then-delete |
| Ordering unit | one queue (until requeue/parallelism) | partition | FIFO: message group |
| Replay | none once acked | seek within retention | none (redrive = move) |
| Fan-out | exchanges → N queues | consumer groups get full stream | SNS → N queues |
| DLQ | DLX policy + x-death | framework-level only | redrive maxReceiveCount |

## 3. Ordering, precisely

- **Kafka**: per partition. Key → `hash(key) % partitions`; **adding partitions changes the mapping and existing data is not redistributed — per-key order breaks at the boundary** (Confluent post-deployment). `max.in.flight` 5 with idempotence keeps ordering on retries (broker retains ≤ 5 batches/producer); idempotence=false + in-flight > 1 risks reorder.
- **RabbitMQ**: FIFO per queue; requeue returns "to its original position … if possible", else near the head; multiple consumers make redelivery interleave. Rule: order = one queue + one consumer + no requeues; delivery-limit/DLX prevents head-of-line freeze.
- **SQS FIFO**: strict order per `MessageGroupId`; one in-flight per group (rest withheld); groups interleave across consumers — the group is both parallelism and ordering unit.
- **Pub/Sub**: ordering keys (same region, subscription-enabled) → publish order; **1 MB/s per ordering key**; redelivery of one message redelivers all subsequent for that key (prefix contract).

## 4. Dead-letter mechanics

- **SQS**: `maxReceiveCount` (1–1,000) receives-without-delete → DLQ; set well above normal retries; standard queues with count > 3 shuffle a thrice-received message backward. DLQ: same account/Region/type; never auto-created; redrive-allow policy on the DLQ side (all | byQueue ≤ 10 | denyAll). **Retention subtlety**: standard — expiration keeps the *original* enqueue timestamp (DLQ retention must exceed source); **FIFO — the timestamp resets on the move**. Redrive can move back.
- **RabbitMQ DLX**: exchange via policy/args (`dead-letter-exchange`, optional routing key); fires on exactly four events — reject/nack requeue=false, per-message TTL expiry, max-length drop, quorum delivery-limit; queue-TTL expiry does NOT dead-letter. Each hop appends to **`x-death`** (queue, reason, count, timestamps). Default dead-lettering is at-most-once; quorum offers at-least-once mode.
- **Kafka**: no broker DLQ; Spring DLT (ten attempts default) and Connect sink DLQ are the framework story [cited forward].
- **Pub/Sub**: max delivery attempts default **5** (5–100), best-effort counting (can reset on inactive pulls); the per-project service account needs publisher-on-DLT + subscriber-on-source or forwarding silently fails; forwarded messages carry `CloudPubSubDeadLetterSource*` attributes; **a dead-letter topic with no subscription loses the messages**.
- **SNS/EventBridge**: SNS DLQ = an SQS queue per *subscription* (client-side errors go straight there; server-side after the retry policy); EventBridge ≤ 24 h/185 attempts then drop-or-DLQ [cited forward].

## 5. Fan-out topologies

- **SNS → SQS**: publish → one message per subscribed queue (JSON envelope unless raw delivery). Filter policies per subscription: scope MessageAttributes (default) or MessageBody; ≤ 5 keys; value-combinations product ≤ 150; policy ≤ 256 KB; defaults 200/topic, 10,000/account; wildcard complexity ≤ 100.
- **Kafka consumer groups**: each group reads the whole topic; within a group each partition → exactly one member (extras idle). KIP-429 cooperative incremental rebalance (2.4); **KIP-848 broker-driven protocol GA in 4.0** (ConsumerGroupHeartbeat; no global sync barrier).
- **RabbitMQ exchanges**: direct (default `""` exchange binds every queue by name), fanout (all bound queues, key ignored), topic (wildcards), headers (x-match any/all). Fan-out = exchange → N queues, each its own competing-consumer pool.

## 6. Poison messages and backlog ops

- **Poison message** (RabbitMQ's definition): repeatedly requeued, never positively acked. Bounds: RabbitMQ delivery-limit 20 → DLX; SQS maxReceiveCount → DLQ; Pub/Sub 5–100 → DLT; Kafka: app/framework counters.
- **Lease extension**: SQS heartbeat via ChangeMessageVisibility (start ~2 min if unsure; 12 h ceiling); Pub/Sub ack deadline 10 s (10–600), pull clients extend; push cannot.
- **Backlog levers** (mechanics verified; framing analysis): pause (Kafka pause/resume [cited forward]); scale out (bounded by partitions/groups/queues); skip/replay (Kafka seek; Pub/Sub seek with acked-retention on, subscription retention default 7 d, 10 min–31 d; SQS/RabbitMQ have no rewind — redrive is the only again).
- **SQS timing**: DelaySeconds 0–15 min at enqueue (message timers override per message; queue-delay change retroactive only on FIFO); short polling default samples a server subset (can miss); long polling ≤ 20 s queries all — best practice: 20 s, one thread per queue, HTTP timeout > wait.

## 7. Push vs pull

- **Pub/Sub push**: POST per message; 102/200/201/202/204 ack, else nack; ack deadline governs redelivery (no per-message modification on push); slow-start delivery window + exponential push backoff 100 ms–60 s; OIDC JWT in Authorization.
- **SNS HTTP/S**: retries only 5xx and 429 (other errors permanent → subscription DLQ or discard). AWS-managed endpoints: 100,015 attempts/23 days (SQS/Lambda — never quote for HTTP). HTTP/S: only customizable protocol; attribute defaults numRetries 3, delays 20 s, linear; **total HTTP/S retry ≤ 3,600 s**; numRetries ≤ 100; jitter; `maxReceivesPerSecond` re-queues without burning retries.
- Push delivery converts queue semantics into HTTP semantics (status codes, endpoint auth) — the webhook boundary; A5 owns the receiver side.

## 8. Schema management on the bus

- **Confluent Schema Registry**: default compatibility **BACKWARD** — consumers on the new schema read data produced with the **last** schema (delete fields / add optional; upgrade consumers first). FORWARD (add fields / delete optional; producers first); FULL (both, optional-only); `*_TRANSITIVE` checks all prior versions (plain modes check one back); NONE.
- **Glue Schema Registry**: Avro 1.11.4 / JSON Schema / proto; 8 modes incl. *_ALL (≈ transitive from a movable checkpoint); BACKWARD recommended.
- **Pub/Sub schemas**: Avro/proto attached to a topic; non-conforming publishes are rejected; ≤ 20 revisions with accepted ranges.

## Sources

enterpriseintegrationpatterns.com (7 pattern pages) · rabbitmq.com docs: consumer-prefetch, quorum-queues, queues, dlx, confirms, amqp-concepts · kafka.apache.org intro + 43 producer config + KafkaConsumer javadoc · docs.confluent.io post-deployment + schema-evolution · cwiki KIP-429, KIP-848 · AWS SQS dev guide (visibility, DLQ ×2, FIFO, message groups, polling ×2, delay) · SNS dev guide (retries, DLQs, sqs-subscriber, filtering + constraints) · Glue schema-registry · docs.cloud.google.com pubsub: ordering, push, handling-failures, schemas, subscription-properties. Cited forward: idempotency-dedup-, load-shedding-backpressure-, retry-backoff-, circuit-breaker-external-research.md.

## Uncertain / could not verify (excluded from the Concept)

- SNS HTTP/S "default policy" read from attribute-defaults, not a per-protocol row.
- Kafka partition-add caveat: paraphrase only (extractor blockquote suspect).
- KIP-848 GA cited from the KIP status line (4.0 blog page unfetchable).
- RabbitMQ vhost default_queue_type knob unverified; ~2,000 quorum prefetch cap mechanism unpinned.
- SQS FIFO per-message timers: excluded.
- Pub/Sub push TLS-cert wording unfetched.
- Lag-SLO guidance and the pause/scale/skip framing are analysis.
- EIP Guaranteed Delivery trade-off text not in the free page.
