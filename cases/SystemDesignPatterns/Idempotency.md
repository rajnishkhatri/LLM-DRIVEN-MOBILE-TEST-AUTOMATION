---
type: reference
title: 'Idempotency and deduplication'
description: 'Exactly-once is at-least-once plus idempotence or dedup. HTTP safety is not application idempotency: mint one Idempotency-Key per business operation, keep an ACID inbox, size the TTL past the replay horizon, and retry only if the callee is idempotent (C2). Cites lost-updates and detecting-concurrent-writes; does not rewrite them.'
tags: [system-design-patterns, resilience, idempotency, deduplication, exactly-once]
---

# Idempotency and deduplication

**See also:** [retry, backoff, and retry budgets](RetryBackoff.md) · [circuit breaker](CircuitBreaker.md) · [timeouts](TimeoutsDeadlines.md) · [lost updates (DDIA)](../data-intensive-design/lost-updates.md) · [detecting concurrent writes (DDIA)](../data-intensive-design/detecting-concurrent-writes.md) · [exactly-once inbox (DDIA)](../data-intensive-design/distributed-transactions.md#exactly-once-message-processing) · [durable workflows](../data-intensive-design/durable-workflows.md) · [quorums and fencing](../data-intensive-design/quorums-and-fencing.md) · [catalog research (2026-09-13)](../../docs/research/sysdesign/c9-idempotency-external-research.md)

Every retry, redelivery, and failover replay asks the same question: what happens if this work runs **twice**? Idempotency makes the second run harmless; deduplication prevents it. Together they are what "exactly-once" actually means — **at-least-once delivery plus an idempotent or deduplicated effect** — because the two-generals argument rules out certainty at the wire: a sender's only choices are don't-retry (risk loss) or retry (risk repeat). [Retry (C2)](RetryBackoff.md) decides **whether, when, and how often** to try again. This pattern answers the complementary question: **whether trying again is safe**. Quality attributes: **correctness under retries** (no double charge, no duplicate order) and **safe automation** (retries, queues, and failover become usable). Costs: a key that must travel every path, dedup state with a retention question, and semantics that must be designed, not bolted on.

## Lineage and vocabulary

- **RFC 9110 §9.2 (STD 97, 2022)** splits *safe* (the client does not *request* a state change — GET, HEAD, OPTIONS, TRACE) from *idempotent* (the intended *effect* of N identical requests equals the effect of one — PUT, DELETE, and all safe methods). POST and CONNECT are neither. PATCH lives in RFC 5789 and is not idempotent. A client **SHOULD NOT** automatically retry a non-idempotent method unless it knows the semantics are actually idempotent or that the original never applied; a **proxy MUST NOT**; a client **SHOULD NOT** automatically retry a failed automatic retry.
- **Kleppmann** (Cambridge *Distributed Systems* notes): at-most-once = send, don't retry; at-least-once = retry until ack (may repeat); **exactly-once = retry + idempotence or deduplication** — an *effect*, not a wire property. Dedup in a crash-recovery world needs **stable storage**. Caveat: `f(f(x)) = f(x)` is not concurrency-proof — a delayed retry of an idempotent set-add can resurrect an element after a causally later remove. Inbox-by-id, or the version / version-vector machinery in [detecting concurrent writes](../data-intensive-design/detecting-concurrent-writes.md), covers what a naturally idempotent write does not.
- **Hohpe / Woolf, EIP *Idempotent Receiver***: even a once-sent message may be seen twice. Two means: explicit de-duping, or message semantics that make repeats harmless.
- **Richardson, microservices.io *Idempotent Consumer***: insert `(subscriberId, messageId)` into `PROCESSED_MESSAGE` **in the same ACID transaction** as the business update; a duplicate hits the primary key. The receiving half of the [outbox](../aws/ch08.md) pair. The four-step algorithm is already in [distributed transactions](../data-intensive-design/distributed-transactions.md#exactly-once-message-processing) — cite, do not rewrite.
- **Brandur / Stripe (2017)**: a client-minted key; the server bookkeeps request state and, once finished, short-circuits to the stored result. Keys are not a permanent archive. The Postgres reference design adds *atomic phases*, *recovery points*, a *completer* for abandoned keys, and a *reaper* (~72 hours).
- **Amazon Builders' Library (Featonby)**: caller-provided client request identifier (EC2 `ClientToken`); record the token and the mutation as one ACID operation. SDKs generate and **reuse** a token across their own retries.
- **IETF `Idempotency-Key` draft-07** (2025-10-15): **expired 2026-04-18, not an RFC**. Specifies the header grammar and 400 / 422 / 409. Vendors already diverge; treat it as vocabulary, not a standard.

## HTTP safety is not application idempotency

| Method | Safe? | Idempotent? | Retry without a key |
|---|---|---|---|
| GET / HEAD / OPTIONS / TRACE | yes | yes | Same intended effect; body may differ |
| PUT | no | yes | Replace the representation again |
| DELETE | no | yes | Resource stays gone (200 then 404/410 is fine) |
| POST | no | no | A second order / charge / email |
| PATCH | no | no | A second partial apply |
| CONNECT | no | no | A new tunnel |

PUT/DELETE being idempotent does **not** make them safe to fire from a crawler, and does **not** make a *create-via-POST* retryable. RFC 9110 idempotency is about *intended effect*, not byte-identical responses. Application-key stores usually go further and **replay the first status + body** so the client can treat the retry as the original answer.

`.NET`'s `DisableForUnsafeHttpMethods()` turns retries off for POST, PATCH, PUT, DELETE, CONNECT and cites RFC 7231 *safety*, not idempotency — it also disables PUT/DELETE, which *are* idempotent. That is a conservative C2 default, not a substitute for a key. The HTTP method is not the control; the key is.

Conditional HTTP (`If-Match: <etag>`, `If-None-Match: *`) is the web's compare-and-set. It prevents a lost update on a *known* resource; it does not bind two POSTs that have not yet created one. The lost-update shapes — atomic SQL, `SELECT FOR UPDATE`, snapshot detection, CAS / optimistic locking — live in [lost updates](../data-intensive-design/lost-updates.md). Do not re-derive them here.

## The key protocol

Mint an **idempotency key once per business operation** — before the first attempt — and reuse it across HTTP retries, queue replays, breaker fallbacks, and Temporal / Step Functions activity retries. Minting a key per HTTP attempt is dedup theater.

**IETF draft-07** (expired; MUSTs as written): `Idempotency-Key` is an RFC 8941 String; UUID recommended; the key **MUST NOT** be reused with a different payload. The resource **SHOULD** publish its purge policy; **no numeric TTL is specified**. Fingerprint **MAY** be a checksum of the body, selected fields, or a request digest. Errors: **400** if the header is missing when required; **422 Unprocessable Content** if the key is reused with a different payload; **409 Conflict** if the original is still in flight. Clients **MUST** correct 400/422 before retrying; 409 needs no correction — wait and reuse the same key. Look up on a **composite** of client key + server-only attributes so a low-entropy key cannot fetch another tenant's cache.

**Stripe API v1** (fetched 2026-09-13): header `Idempotency-Key`, ≤ **255** characters, no PII. **All POST** accept keys; **do not send on GET or DELETE**. Saves the first status + body **including 500s**. Prune after **at least 24 hours**; reuse after prune = a new request. Incoming parameters are compared; mismatch **errors** (this page does **not** name 422 — do not assert it). Results are saved only after endpoint execution begins; validation failure and concurrent conflict are **not** saved and may be retried with the same key. `429` can produce a different result because rate limiters run **before** the idempotency layer. Replay marker: `Idempotent-Replayed: true`. Status table lists **409** for same-key conflict. `Stripe-Should-Retry` overrides status-code guesswork.

**Stripe API v2** is a different contract: POST **and DELETE**; replay window **30 days** (same API, same account/sandbox); a failed first attempt is **re-executed** without producing side effects; a missing key is generated as a UUID. Do not mix v1's frozen-first-body mental model with v2.

| Vendor | Header | Retention / scope | Concurrent duplicate |
|---|---|---|---|
| **Adyen** | `idempotency-key`, ≤ **64** chars | **7–14 days**, company account | **422 or 409**, error **704**; store down → **503** + **703** |
| **PayPal** | `PayPal-Request-Id`, ≤ **38** bytes | "as long as the server stores the ID"; refund example **45 days**. Unique **per request and per call type** | Processes the first and **might fail** the second; returns **latest** status |
| **AIP-155** | `request_id` on the request message, UUID4, **36** ASCII | "any reasonable timeframe" | Duplicate **should** replay the prior success; if history is gone, **may** return current state |
| **AWS EC2** | `ClientToken`, ≤ **64** ASCII | (page publishes no TTL) | Parameter change → `IdempotentParameterMismatch`. 200: do not retry. 5xx: same token |
| **AWS Powertools** | DynamoDB (or Redis) record | `expires_after_seconds` **3600**; they do **not** trust DynamoDB TTL for the decision | `INPROGRESS` rejected until `in_progress_expiration` |

Two retries of the same key can overlap. IETF **SHOULD** 409; Stripe v1 does not save a concurrent conflict; Adyen 422/409 + 704; Powertools holds `INPROGRESS`. The client must **reuse the key** after a 409 — minting a new one is how a double charge is born.

## Key lifecycle

A key is not a boolean "seen / not seen." Brandur's Postgres design (and Powertools' `INPROGRESS` → `COMPLETE`) treat it as a **recovery-point state machine**. Foreign mutations — a card capture, a Kafka emit, an email — cannot be rolled back by the local transaction; commit the phase *before* the call.

```
started → <local ACID work> → ride_created → <Stripe charge> → charge_created → finished
```

A retry arriving at `charge_created` resumes after the last committed phase, not from zero. A **completer** job pushes unfinished keys through remaining phases after the client stops retrying (Brandur's suggested reaper threshold: **about 72 hours** — Friday bug, Monday completer). Without recovery points, a timeout mid-flight leaves you choosing between "replay from scratch" (double charge if the foreign call succeeded) and "give up" (orphan charge, no receipt).

Stripe v1 collapses this to *one* stored outcome: once execution begins, the first status+body is frozen, 500s included. Stripe v2 is closer to recovery points: a failed first attempt is re-executed. Mixing the two mental models is a failure mode below.

## Inbox: at-least-once plus an idempotent consumer

Every at-least-once path **will** redeliver: SQS visibility expiry, Kafka crash after process-before-commit, Pub/Sub expired ack, webhook producer retry. "Exactly-once" labels on brokers are scoped — treat them as a first line, then design the consumer as at-least-once anyway.

| Claim | What it actually covers |
|---|---|
| Kafka `enable.idempotence` (default **true** since 3.0, KIP-679) | Broker-side retry duplicates, **per partition, per producer session**, via `(producerId, epoch, sequence)`. Your second `send()` is two messages. PID kept **1 day** (`producer.id.expiration.ms`; keep ≥ `delivery.timeout.ms`, KIP-854) |
| Kafka EOS / Streams `exactly_once_v2` | Output records **and** input offsets in one transaction. Side effects outside Kafka are not in it |
| SQS FIFO "exactly-once processing" | Producer retries inside a **5-minute** `MessageDeduplicationId` window (or SHA-256 of **body**, attributes excluded). Visibility expiry still redelivers. Window is **not configurable** |
| Azure Service Bus duplicate detection | Application `MessageId` history: default **10 minutes**, min 20 s, max **7 days**. Producer-send dedup only |
| Pub/Sub "exactly-once delivery" | No resend of an **acked** `messageId`. Publisher retries mint **new** ids. Pull, one region |
| EventBridge | Target retries default **24 h** / **185** attempts; then drop or DLQ |
| Step Functions Standard | Tasks run once **unless you specified `Retry`**. History **90 days**. Express async is **at-least-once**; Express sync is at-most-once |
| Temporal Activities | "May even **partially complete more than once**." Recommended key: **Workflow Run ID + Activity ID** |

The inbox algorithm — unique id, insert-or-drop in the same DB transaction as the effect, then ack the broker — is the four-step recipe in [distributed transactions](../data-intensive-design/distributed-transactions.md#exactly-once-message-processing). Crash before commit → abort, broker retries. Crash after commit, before ack → retry sees the id. A uniqueness constraint serializes two in-flight retries. An email server that is not in the transaction will still double-send: **every effect needs its own guard**.

Two placements (Richardson): a separate `PROCESSED_MESSAGES` table, or the id *on the business row* (the order's `idempotency_key` unique index). The second is natural when the message *is* "create this order." Inbox in a different database than the effect no longer serializes with the write — you are back to 2PC or a [lost update](../data-intensive-design/lost-updates.md).

## TTL: the window must outlive the replay

The dedup memory must outlive the longest path a duplicate can travel — client retry schedule ([C2](RetryBackoff.md)), queue visibility + DLQ redrive, operator replay, Brandur completer. Only Kafka states its own version (PID expiry ≥ delivery timeout); the composite rule is inference. After the window, reuse is a **new** operation.

Verified spread to design against: Stripe v1 **≥ 24 h** · Stripe v2 **30 days** · Adyen **7–14 days** · PayPal refund example **45 days** · AIP-155 "any reasonable timeframe" · SQS/SNS FIFO a fixed **5 minutes** against default **4-day** / max **14-day** retention · Azure Service Bus **10 min** default (max 7 days) · Kafka PID **1 day** · Powertools **3600 s** · Brandur recycle "~24 hours", reaper **~72 hours**.

SQS FIFO's 5-minute producer window against a 14-day redrive is exactly why a consumer-side business-key inbox remains necessary. Do not treat a broker window as the last line.

## Where the key lives

The same string must survive every hop. Placement is a layering decision, not a different pattern.

| Layer | What it stores | Trade-off |
|---|---|---|
| **Client / order row** | Key minted with the business operation, persisted before the first attempt | Survives process death; the HTTP client must *read* it, not generate one |
| **Edge / API idempotency store** (Stripe-shaped, Powertools DynamoDB, Adyen) | First outcome (v1) or phase (v2 / Brandur) keyed by `(tenant, key)` | Gives the caller a stable HTTP answer; retention is *their* window, not yours |
| **Consumer inbox** | `(subscriber, messageId)` in the same ACID transaction as the effect | Covers rebalance / visibility expiry / DLQ redrive the provider window misses |
| **Foreign callee** (payment API, email provider) | The **same** key on their idempotent-request header | Both sides of the wire dedupe; still keep your inbox |
| **Broker producer window** | SQS `MessageDeduplicationId`, Azure `MessageId`, Kafka PID+seq | Cheap send-retry shield; scopes are narrow (5 min / 10 min / per session) |
| **Mesh / HTTP client retry** | Nothing, unless you disable unsafe-method retries | A sidecar that retries POST without the key is a duplicate generator |

A gateway that mints its own UUID on each proxy attempt breaks the chain. So does an SDK that generates a fresh `ClientToken` per attempt instead of reusing the one on the order.

## Retries only if the callee is idempotent

A transient failure is necessary but not sufficient. [C2](RetryBackoff.md) owns classification, Brooker jitter, SRE budgets, and the one-layer rule — do not rewrite them. The rule this pattern contributes: **retry only if the callee (or this hop) is idempotent**.

- Timeout / `DEADLINE_EXCEEDED` on a payment capture is **unknown-outcome**: the first attempt may have succeeded. Retry is safe only with the **same** key. Without it, C2's retry *is* the double charge.
- Circuit **Open** → do not retry that dependency; fail into the fallback, and put the **same** key on the queued message. Half-open probe is one attempt; retries falsify recovery.
- Hedging a non-idempotent write is C7's failure mode — keep hedges on GET / `GET /capture/{id}`, not on `POST /capture`.
- SDK defaults (Anthropic / OpenAI `max_retries` 2 on 408/409/429/5xx) retry mutating tool endpoints. A tool without a key is a double-execution generator by design.
- Compensation (a refund) is a **new** business operation and needs a **new** key. Never reuse the capture key.

## Dedup-store variants

| Variant | Mechanism | Wins when | Loses when |
|---|---|---|---|
| **Replay-the-first-response** (Stripe v1, IETF completed-duplicate) | Store status+body; short-circuit | Client treats retry as the original HTTP answer | Frozen 500s; store must be consistent |
| **Re-execute failed, skip succeeded** (Stripe v2, Brandur recovery points) | Persist phase; resume | Timeout mid-flight can still finish | Completer required; more moving parts |
| **ACID inbox PK** | Insert `(subscriber, id)` + effect | Local DB is the system of record | Foreign mutations (card, email) need their own key |
| **Conditional write** | `attribute_not_exists`; `WHERE version=` | One item, no extra table | OCC / lost-update lives in [lost updates](../data-intensive-design/lost-updates.md) |
| **Broker producer window** | SQS FIFO 5 min; Azure SB `MessageId` | Cheap first line for send-retries | Window ≪ queue retention / DLQ redrive |
| **Natural idempotency** | PUT-replace; set-add; `CREATE IF NOT EXISTS` | No extra store | Kleppmann add-then-remove; increments |

Locks serialize workers for *efficiency*. Correctness under concurrent writers is a fencing token or a conditional write — [quorums and fencing](../data-intensive-design/quorums-and-fencing.md) and [lost updates](../data-intensive-design/lost-updates.md). Once the store can compare-and-reject, prefer the idempotent write over a TTL lock.

## Observability

| Signal | What it tells you |
|---|---|
| **Replay rate** (`Idempotent-Replayed: true`, inbox PK collisions) | Baseline ≈ C2 retry rate; a spike is a new duplicate source (rebalance, DLQ redrive, client double-submit) |
| **409 / in-flight conflicts** | Overlapping retries. Minting a new key here double-charges |
| **422-class / parameter mismatch** | Client reused a key for a *different* operation, or the fingerprint over-matched |
| **400 missing key** on a required POST | Client or proxy stripped the header |
| **Dedup-store size and age of oldest row** | Retention vs the actual redrive horizon |
| **Effects without a guard** (emails / loyalty vs keyed orders) | Partial idempotency |

Log the key (or its hash) with the correlation id so C2 retries, A5 webhooks, and the inbox collide in one trace. Do not put PII in the key. No vendor publishes a PromQL recipe; alert on mismatch rate and oldest-row age, not a copied query.

## Tuning

| Knob | Too small | Too large | Starting point |
|---|---|---|---|
| Key retention | Late redrive is a new charge | Store growth; accidental reuse looks like a conflict | `max(client retry horizon, queue retention + DLQ redrive, EventBridge 24 h)` + operator margin |
| Key scope | Cross-tenant leaks (IETF composite-key warning) | Duplicates across scopes undetected (PayPal: authorize ≠ capture) | Per business operation, per tenant, per API |
| Fingerprint | Same key, new `amount` charges the new amount | Unsigned JSON key order rejects legitimate retries | Semantic body; exclude timestamps and server-injected fields |
| In-flight lock | Two workers both execute | Client storms 409s; lock expiry re-runs the first | 409 → wait, **same key** |
| Inbox grain | Whole-request only; emails fire twice | Per-effect table sprawl | Key at the business operation; conditional writes at each effect |
| Broker window | SQS 5 min / SB 10 min miss redrives | Throughput cost (Azure: keep it small) | First line only; inbox is the last line |

Placement chain is the table above: the key is the same string on every hop.

## Worked calibration — checkout capture (double-charge drill)

Constraints from the [C2 order-service drill](RetryBackoff.md#worked-calibration--order-service-3-s-slo) and the [C1 checkout drill](CircuitBreaker.md#worked-calibration--checkout--payment-gateway): 3 s user-facing SLO, inventory then payment, Open-breaker fallback queue, consumer that replays on rebalance. Design drill, not a vendor SLA.

| Point | Control | Why |
|---|---|---|
| Key mint | `order_id`-derived key written on `orders` at insert | Survives process death; one operation, one key |
| HTTP `POST /capture` | Same `Idempotency-Key` on attempt 1 and every C2 retry | Timeout = unknown outcome; retry must collide, not re-charge |
| Fingerprint | Amount, currency, customer, `order_id` — not `requested_at` | A legit retry with a clock field must still match |
| In-flight | 409 / Adyen 704 → wait, same key | Two browsers / two retries |
| Open-breaker queue | Message carries the **same** key | Queue replay is attempt *n*, not a new capture |
| Consumer inbox | `INSERT processed(consumer, key)` in the charge transaction | Rebalance / visibility expiry hits the PK |
| Gateway | Stripe v1 store, **≥ 24 h** | Covers EventBridge 24 h and same-day redrive — **not** a 14-day SQS DLQ |
| Inbox retention | **≥ 14 days** if SQS DLQ redrive is in play | Broker window is the first line |
| Refund | **New** key (`refund:` + refund id) | Same order, different operation |
| Hedge | Off on `POST /capture`; allowed on `GET /capture/{id}` | GET is RFC-idempotent |

Payment itself takes **no** RPC retry in the C2 drill (one 1 500 ms retry already misses 3 s). The key still rides the *queue* replay. Revisit after a week of replay rate vs C2 retry rate.

## Testing and operating

- Duplicate-injection: fire every mutation twice (same key) and assert one effect + identical response; fire with a mismatched payload and assert the 422-class (or vendor-equivalent) rejection.
- Kill the process between effect and ack (Toxiproxy `timeout`, or a crash hook) and assert the replay is absorbed.
- Rebalance drills for consumers; DLQ redrive drills **after** the provider / broker window has lapsed — that is the case SQS's 5 minutes does not cover.
- Force a 409 (two overlapping callers) and assert the client reuses the key, not rotates it.
- C2's rule of thumb: never inject faults into a non-idempotent request you have not keyed yet.
- Completer drill: abandon a key at `charge_created` and assert the job finishes the receipt.

## Failure modes

- **Key per attempt.** Dedup theater. The mint point is the design decision.
- **HTTP method as the only control.** PUT is idempotent; `POST /charges` is not. Proxies that retry POST against RFC 9110 §9.2.2 create duplicates.
- **Window shorter than the replay horizon.** SQS FIFO 5 min vs 4–14 day retention; Azure SB 10 min vs a weekend redrive; Kafka PID expiry below delivery timeout.
- **Trusting "exactly-once" labels.** Kafka EOS is Kafka-to-Kafka; SQS FIFO is send-dedup + at-least-once consume; Pub/Sub is ack-scoped; Step Functions Standard **excludes** your `Retry` blocks; Express async is at-least-once.
- **Partial idempotency.** Order row is keyed; email / loyalty / webhook side effects are not. One order, three receipts.
- **Rotating the key on 409 or 500.** 409 means in-flight; Stripe v1 500 may already have charged. Reuse, then reconcile.
- **v1 frozen-500 vs v2 re-execute.** Mixing mental models double-charges or mis-handles a recovered failure.
- **Idempotent-but-not-concurrent** (Kleppmann). Set-add after a causal remove — [detecting concurrent writes](../data-intensive-design/detecting-concurrent-writes.md), not `f(f(x)) = f(x)` alone.
- **Inbox in a different DB than the effect.** The PK no longer serializes with the write.
- **Dedup store as a new SPOF.** Adyen 503/703: falling back to *non-idempotent* processing is how you double-charge during the outage.
- **TTL lock as correctness** without a fencing token — [quorums and fencing](../data-intensive-design/quorums-and-fencing.md).
- **IETF draft treated as an RFC.** As of 2026-09-13 it is expired; vendors already diverge (header names, 409 vs "might fail," 24 h vs 7–14 d vs 45 d).

**When not to add a key store.** Reads (GET is already idempotent). True at-most-once you can afford to lose. Natural PUT-replace of a whole aggregate you own, with no foreign mutation. A single-threaded in-process loop with no retry and no network. **When a key store is the wrong first tool:** you needed an atomic increment or `SELECT FOR UPDATE` ([lost updates](../data-intensive-design/lost-updates.md)); causal metadata across replicas ([detecting concurrent writes](../data-intensive-design/detecting-concurrent-writes.md)); or an outbox so the publish commits with the write.

## Around LLM and agent workloads

Tool calls are side effects executed by an at-least-once loop: agents retry, workflows replay, queues redeliver. The discipline transfers whole: assume every tool call can run twice; derive its key from `(run id, step id)` — Temporal's recommended shape — and pass it to the downstream API's idempotency mechanism; keep the orchestration loop deterministic and replayable, with effects quarantined in activities. Anthropic's and OpenAI's SDKs retry on 408/409/429/5xx by default ([C2](RetryBackoff.md)); a mutating tool endpoint without keys is a double-execution generator. LLM *invocations* themselves belong in activities (Temporal: do not call the model from workflow code). A refusal or context-window stop is HTTP 200 — not a retryable failure, and not a reason to rotate the key.

## Trade-offs

| Buy | Pay |
|---|---|
| Retries, queues, failover become safe automation | Key plumbing through every client, queue, and fallback path |
| Exactly-once *effects* on at-least-once infrastructure | Dedup state: storage, retention, and its own consistency |
| Cheaper than distributed locks; no liveness coupling | Per-effect design work; "add a key" is never just one field |
| Provider windows as a free first line | Their scopes are narrow; the business key remains yours |
| Replay-the-first-response gives the client a stable HTTP answer | Frozen 500s (v1); v2 re-execute is a different contract |

Delivery guarantees end at the wire; **effects are yours**. [C2](RetryBackoff.md) decides whether to try again; idempotency decides whether trying again is safe. The [breaker](CircuitBreaker.md) decides whether to call; the fallback must carry the same key.

## Sources

Verified 2026-09-13; full URLs, per-claim provenance, and items deliberately left out are in the [catalog research note](../../docs/research/sysdesign/c9-idempotency-external-research.md). Do not treat the IETF draft as an RFC; do not assert Stripe v1 returns 422 on payload mismatch (docs say "errors").

- Canon: RFC 9110 §9.2 / §13; Kleppmann Cambridge notes (slides 94–96) and *How to do distributed locking* (2016); Hohpe EIP *Idempotent Receiver*; Richardson *Idempotent Consumer*; Brandur 2017; Featonby, Builders' Library *Making retries safe with idempotent APIs*.
- Keys: Stripe v1 `idempotent_requests` + `error-low-level` and v2 overview; IETF `draft-ietf-httpapi-idempotency-key-header-07` (expired 2026-04-18); Adyen API idempotency; PayPal `PayPal-Request-Id` (2026-08-11) + requests page (45-day refund example); AIP-155; EC2 `ClientToken`; AWS Powertools Python idempotency (`expires_after_seconds` 3600).
- Platforms: Kafka 4.3 producer configs + KIP-679/854; SQS FIFO `MessageDeduplicationId`; Azure Service Bus duplicate detection; EventBridge retry policy; Step Functions workflow types; Temporal activity-definition.
- Already in this tree: [C2 research](../../docs/research/sysdesign/retry-backoff-external-research.md) (RFC 9110 retry rules, Stripe ≥ 24 h, draft-07 400/422/409); [lost updates](../data-intensive-design/lost-updates.md); [detecting concurrent writes](../data-intensive-design/detecting-concurrent-writes.md); [distributed transactions](../data-intensive-design/distributed-transactions.md#exactly-once-message-processing).
