---
type: research
title: 'Idempotency & deduplication — external research (2026-09-13)'
description: >-
  Source-verified research backing the Idempotency Concept (C9):
  delivery-semantics vocabulary (Kleppmann, two generals), Kafka idempotent
  producer and EOS (KIP-679/447/854), SQS/SNS FIFO dedup windows, Pub/Sub
  exactly-once delivery, AIP-155 and payment-provider key retention, the
  inbox/conditional-write/precondition pattern set, fencing tokens vs
  idempotency, and Temporal/Step Functions execution semantics.
tags: [research, idempotency, deduplication, exactly-once, system-design-patterns]
---

# C9 Idempotency & deduplication — external research (2026-09-13)

**Method.** Facts verified against primaries 2026-09-13. Cited forward from [retry-backoff-external-research.md](retry-backoff-external-research.md): RFC 9110 safe/idempotent semantics + SHOULD-NOT-auto-retry rules; Stripe keys (≥ 24 h, ≤ 255 chars, first status+body stored, payload-mismatch error, POST-only); IETF Idempotency-Key draft-07 (400/422/409; expired draft); EC2 client tokens; the double-charge scenario.

## 1. Delivery-semantics vocabulary

- **Kleppmann, Cambridge *Distributed Systems* notes (2021/22)**: at-most-once (send, don't retry); at-least-once (retry until ack — may repeat); **exactly-once = "retry + idempotence or deduplication"** — an *effect*, not a wire guarantee. Two generals (§2.1, Gray 1978): over a lossy channel sender/receiver never reach certainty, so wire choices are only lose-or-repeat; exactly-once is reconstructed above delivery. Dedup in a crash-recovery model needs **stable storage**. Caveat: idempotence alone fails under concurrent interleaving (set-add retry after a causally later remove) — needs dedup or causal metadata.
- **Confluent "Exactly-Once Semantics Are Possible" (2017-06-30, upd. 2025-03)**: Kafka's claim is exactly-once **stream processing** ("processed results reflected once"), built from idempotent producers + transactions; an end-to-end contract requiring app cooperation.
- **Kafka design "Message Delivery Semantics"** (Confluent mirror, pub. 2026-08-04): consumer position bookkeeping decides consumer semantics (save-then-process = at-most-once; process-then-save = at-least-once); exactly-once into **external systems** requires offsets stored with the output (or 2PC).

## 2. Kafka

- **Idempotent producer**: `enable.idempotence` default **true** (Kafka 4.3 config; flipped false→true with `acks` 1→all in **3.0 via KIP-679**). Broker dedupes on **PID + per-partition sequence numbers**. Scope limits (KafkaProducer javadoc): idempotence "only … within a single session"; application-level double `send()` is NOT deduplicated; enabling defaults `retries` to MAX_VALUE. Per-session, per-partition, broker-retry duplicates only.
- **Transactions/EOS**: `transactional.id` (default null) implies idempotence, extends across sessions, fences zombies via epochs. Consumer `isolation.level` default **read_uncommitted**. **KIP-447** removed producer-per-partition (fencing via consumer-group metadata; brokers 2.5+); Streams `processing.guarantee` default **at_least_once**, alternative **exactly_once_v2**; EOS wants ≥ 3 brokers by default.
- **Consumer reality**: auto-commit default true (5 s) → crash/rebalance between processing and commit **replays records**; transactions close the loop only when the output is Kafka; external effects need inbox dedup or natural idempotency.
- **PID retention**: `producer.id.expiration.ms` default **86 400 000 ms (1 day)** (KIP-854; in 3.4.0 notes); keep ≥ `delivery.timeout.ms` or duplicates return. `transactional.id.expiration.ms` default **7 days**.

## 3. Queue services

- **SQS standard**: at-least-once ("more than one copy … might be delivered"), best-effort ordering.
- **SQS FIFO**: **5-minute deduplication interval** for `SendMessage` retries; content-based dedup (SHA-256 over **body, not attributes**) or explicit `MessageDeduplicationId` (overrides the hash; neither set → send fails); duplicate acknowledged but not delivered; dedup id tracked even after delete. Window covers **producer retries only** — receive-side single-processing depends on deleting within the visibility timeout (default 30 s, max 12 h).
- **High-throughput FIFO**: `DeduplicationScope` {messageGroup, queue} + `FifoThroughputLimit` {perQueue, perMessageGroupId}; perMessageGroupId **requires** messageGroup scope — throughput bought by narrowing dedup.
- **SNS**: standard concedes occasional duplicates; FIFO mirrors SQS (5-min window; scope follows FifoThroughputScope); end-to-end exactly-once into SQS FIFO only with correct permissions, timely deletes, **no filter policy**, no network disruption.
- **EventBridge**: durable service events delivered **at least once**; target retry default 24 h / up to 185 attempts with backoff+jitter; exhausted → dropped unless DLQ.
- **Pub/Sub exactly-once delivery** (GA 2022-12-01): really *no redelivery after successful ack* (none while deadline outstanding; only the latest AckID can ack). **Pull subscriptions only, one region, publisher-side duplicates out of scope** — producer dedup stays yours.

## 4. API-design guidance

- **AIP-155 `request_id`** (changelog 2024-01-08): "Providing a request ID must guarantee idempotency"; duplicates *should* return the prior successful response; UUID4 annotation required for UUID ids; retention "any reasonable timeframe"; stale-success may return current state.
- **Adyen**: `Idempotency-Key` header, POST; keys "valid for a period of 7 to 14 days"; UUIDv4 ≤ 64 chars; scoped to the company account; repeat replays the original; simultaneous duplicate → 422/409 error 704.
- **PayPal**: `PayPal-Request-Id`; reuse returns latest status; unique per request AND call type; ≤ 38 chars. Retention varies **per API**: general page example "up to 45 days"; Orders 6 h, extendable to 72 h. Industry spread: Stripe ≥ 24 h · Adyen 7–14 d · PayPal 6 h–45 d.

## 5. Implementation patterns (one canonical source each)

- **Idempotent consumer / inbox** (microservices.io): `PROCESSED_MESSAGE` table PK (subscriberId, messageId), inserted **in the same ACID transaction** as the business update; duplicate hits the PK. Pairs with transactional outbox. Ancestor: EIP Idempotent Receiver (dedup by tracked ids, or semantics that make repeats harmless).
- **Dedup table / insert-first**: unique-key insert first; the constraint violation IS the duplicate signal. Server-side variant (Builders' Library "Making retries safe with idempotent APIs"): record the client token + apply mutations atomically; retried RunInstances returns the same instance id even as state progresses.
- **Conditional writes**: DynamoDB `attribute_not_exists(Id)` = create-once; optimistic concurrency = condition on current value/version.
- **HTTP preconditions**: RFC 9110 ETag §8.8.3, If-Match §13.1.1, If-None-Match §13.1.2; If-Match on writes exists "to prevent the 'lost update' problem"; `If-None-Match: *` = HTTP's attribute_not_exists (wording via RFC 7232 §3, semantics unchanged).
- **Natural idempotency**: likeCount+1 is not idempotent; likeSet ∪ {user} is — store the set, derive the count (Kleppmann). PUT (absolute replacement) vs POST.

## 6. Retention sizing

Verified anchors: Stripe ≥ 24 h · Adyen 7–14 d · PayPal 6 h–72 h/45 d · AIP-155 "reasonable" · SQS/SNS FIFO fixed **5 min** (vs 4–14 d retention and 12 h visibility) · Kafka PID 1 day (rule: ≥ delivery.timeout.ms, KIP-854) · transactional.id 7 d. The general rule — dedup memory must outlive client retries + redelivery/DLQ-redrive + operator replay — is **inference**; only Kafka states its own version.

## 7. Locks vs idempotency

**Kleppmann, "How to do distributed locking" (2016-02-08)**: efficiency locks (duplicate work is the cost) vs correctness locks; any TTL lock is unsafe alone — GC pause/preemption can outlive the lease, and checking expiry before writing doesn't help; the fix is a **fencing token** (monotonic, storage rejects older); Redlock criticized ("does not have any facility for generating fencing tokens"; synchronous-timing assumptions); recommendation: single Redis for efficiency, consensus + fencing for correctness. Synthesis (flagged): fencing requires the store to compare-and-reject — i.e., a conditional write; once the store can do that, the same mechanism often enforces the invariant directly, demoting the lock to a contention optimization. Locks serialize workers; idempotency + conditional writes make the effect safe however many run.

## 8. LLM/agent angle

- **Temporal**: "Temporal recommends that Activities be idempotent"; activities are effectively **at-least-once** (may "partially complete more than once"); recommended key = **Workflow Run ID + Activity ID**; workflow code must be deterministic (replay) — API calls, **LLM invocations**, DB queries belong in Activities. Mapping: every side-effectful tool call = an activity; assume at-least-once; key from (run id, step id); keep the orchestrating loop replayable.
- **Step Functions**: Standard = exactly-once ("never run more than once, unless you have specified Retry") — positioned for **non-idempotent** actions (payments); `StartExecution` name-dedup. Express async = **at-least-once** (idempotent actions); Express sync = at-most-once; Express has no name-based idempotency. Fine print: your own Retry blocks reintroduce at-least-once at the task level.

## Sources

cl.cam.ac.uk dist-sys-notes.pdf (2021/22) · confluent.io exactly-once blog (2017-06-30/2025-03) · docs.confluent.io delivery-semantics (2026-08-04) · kafka.apache.org/43 producer/consumer/broker/streams configs + KafkaProducer javadoc · KIP-679, KIP-447, KIP-854 · 3.4.0 release notes · MSK config table · SQS dev guide (standard, FIFO exactly-once, MessageDeduplicationId, high-throughput) + API_CreateQueue · SNS FAQ + fifo-message-dedup · EventBridge delivery-level + retry policy · Pub/Sub exactly-once-delivery + GA blog (2022-12-01) · aip.dev/155 · Adyen API idempotency · PayPal idempotency guidelines + requests + Orders use-cases · microservices.io idempotent-consumer · enterpriseintegrationpatterns.com IdempotentReceiver · DynamoDB condition expressions · httpwg RFC 9110 TOC + RFC 7232 · Builders' Library making-retries-safe · martin.kleppmann.com distributed-locking (2016-02-08) · docs.temporal.io activity/workflow definitions · Step Functions execution guarantees.

## Uncertain / could not verify (excluded from the Concept)

- RFC 9110 §13 verbatim truncated in fetches; wording from RFC 7232 — don't attribute verbatim to 9110.
- KIP-447 release split (2.5 API / 2.6 Streams) — say "brokers 2.5+".
- PayPal retention: state the spread, not one number.
- producer.id.expiration.ms default from KIP-854 + release notes (4.3 page truncated).
- Retention-sizing rule is assembled inference; only Kafka's own rule is sourced.
- SQS FIFO consumer-side exactly-once has no single quotable sentence.
- §7 fencing≈conditional-write and §8 agent framing are analysis.
- EventBridge bus-level phrasing rests on durable-delivery + retry-policy pages.
