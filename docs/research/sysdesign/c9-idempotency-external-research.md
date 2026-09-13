---
type: research
title: 'Idempotency & deduplication — external research (2026-09-13)'
description: >-
  Group C catalog evidence pass for C9: HTTP method idempotency vs application
  keys, Stripe Idempotency-Key TTL (v1 ≥24 h, v2 30 d), IETF draft-07 status
  (expired 2026-04-18, not an RFC), at-least-once + inbox/dedup stores, knobs,
  observability, and a checkout calibration.
tags: [research, system-design-patterns, C9, c9-idempotency]
---

# C9 Idempotency & deduplication — catalog research (2026-09-13)

> **What this is.** Catalog evidence pass for **C9** at the Group C / [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md) bar: mechanics and variants, knobs with verified defaults, observability, tuning, a worked checkout calibration, failure modes, sources. Retry (**C2**) decides *whether* to try again; this note owns whether trying again is *safe*. A Concept already exists in the main repo ([Idempotency.md](../../../cases/SystemDesignPatterns/Idempotency.md)); this note is the fetch-dated evidence, not a rewrite of that Concept.
>
> **Method.** Primary pages fetched 2026-09-13. Numbers and option names reproduced exactly; everything else paraphrased. Facts marked **[→C2]** / **[→A1]** / **[→A2]** / **[→A5]** live in sibling catalog notes and are not re-derived. Unverifiable items are in §10 and are **not** asserted as fact.

---

## 1. Scope and non-goals

**Owns.** The gap between *HTTP-method* idempotency (RFC 9110 §9.2) and *application* idempotency keys; the `Idempotency-Key` header as practiced (Stripe v1/v2, Adyen, PayPal-Request-Id, AIP-155) and as drafted (IETF `draft-ietf-httpapi-idempotency-key-header-07`); at-least-once delivery plus an idempotent consumer; inbox / dedup-store mechanics (ACID insert, conditional write, recovery-point state machines); verified retention windows; observability and a worked calibration.

**Does not own.**

| Sibling | What stays there |
|---|---|
| **A1** | Wire methods, connection reuse, 421 retry-regardless-of-method. This note only takes §9.2 safe/idempotent and the “SHOULD NOT auto-retry POST” rule. |
| **A2** | Broker delivery claims, visibility timeouts, DLQ. This note only takes “at-least-once *will* redeliver” as the reason an inbox exists. |
| **A5** | Webhook signing and producer retry *schedules*. Receiver *keys* (`evt_…`, `webhook-id`) are named there; how to *store* them is here. |
| **B5** | Saga compensation choreography. A compensating refund is a **new** business operation (new key), not a replay of the capture key. |
| **B7** | Transactional outbox / CDC (the *send* half). This note is the *receive* half: inbox insert in the same ACID transaction as the effect. |
| **C2** | Jitter formulas, SRE ~10% budgets, `4³=64`, what is worth retrying. Cite only: a timeout on a capture is unknown-outcome and needs a key. |
| **C7** | Deadline propagation. Hedging a non-idempotent call is their failure mode #10. |

**Does not re-derive.** [lost-updates.md](../../../cases/data-intensive-design/lost-updates.md) (atomic SQL, `SELECT FOR UPDATE`, snapshot lost-update detection, CAS / optimistic locking). [detecting-concurrent-writes.md](../../../cases/data-intensive-design/detecting-concurrent-writes.md) (happens-before, version numbers, version vectors). [distributed-transactions.md](../../../cases/data-intensive-design/distributed-transactions.md) § exactly-once message processing (the four-step inbox). [durable-workflows.md](../../../cases/data-intensive-design/durable-workflows.md) (engine replay still needs idempotent callees).

---

## 2. Lineage / vocabulary

| Term | Meaning | Named source (fetched 2026-09-13) |
|---|---|---|
| **Safe method** | Client does not *request* a state change. GET, HEAD, OPTIONS, TRACE. | RFC 9110 §9.2.1 |
| **Idempotent method** | Intended *effect* of N identical requests = effect of one. PUT, DELETE, and all safe methods. POST and CONNECT are not. PATCH is outside 9110 (RFC 5789) and is not idempotent. | RFC 9110 §9.2.2 |
| **Application idempotency key** | Client-minted unique value that *makes* a non-idempotent method (POST/PATCH) fault-tolerant by binding retries to one stored outcome. | Stripe API; IETF draft-07 §2 |
| **Fingerprint** | Server-side digest of the payload (or selected fields) compared on reuse so a key cannot be pointed at a different body. | IETF draft-07 §2.4; Stripe “compares incoming parameters” |
| **Inbox / idempotent consumer** | `(subscriberId, messageId)` inserted in the **same** DB transaction as the business write; a duplicate hits the PK and is dropped, then the broker is acked. | Hohpe EIP *Idempotent Receiver*; Richardson microservices.io; Kleppmann / [distributed-transactions.md](../../../cases/data-intensive-design/distributed-transactions.md) |
| **Dedup window** | How long a store remembers a key. After it, reuse is a *new* operation. | Stripe v1 “at least 24 hours”; IETF §2.3 (resource publishes policy; no mandated TTL) |
| **Recovery point** | Named checkpoint on the key row so a retry resumes after the last committed atomic phase, not from zero. | Brandur, *Implementing Stripe-like Idempotency Keys in Postgres* (2017-10-27) |
| **Exactly-once (effect)** | “retry + idempotence or deduplication.” Not a wire property. | Kleppmann, Cambridge *Distributed Systems* notes 2024/25, slides 94–96 |

**RFC 9110 §9.2.2 (STD 97, June 2022).** A method is idempotent if “the intended effect on the server of multiple identical requests with that method is the same as the effect for a single such request.” The property applies to what the *user requested*; a server may still log, version, or otherwise produce non-idempotent side effects. A client **SHOULD NOT** automatically retry a non-idempotent method unless it has some means to know the semantics are actually idempotent or that the original never applied. A **proxy MUST NOT** automatically retry non-idempotent requests. A client **SHOULD NOT** automatically retry a failed automatic retry. Trade-off: treating POST as retryable buys availability and loses exactly-once — the RFC names the “idle persistent connection closed before any response” guess as the risky path **[→A1]**.

**.NET `DisableForUnsafeHttpMethods()`** turns retries off for POST, PATCH, PUT, DELETE, CONNECT and cites RFC 7231 *safety*, not idempotency — it also disables PUT/DELETE, which *are* idempotent **[→C2]**.

**Kleppmann (Cambridge notes, 2024/25 PDF fetched 2026-09-13).** At-most-once = send, don’t retry (update may not happen). At-least-once = retry until acknowledged (may repeat). Exactly-once = retry + idempotence *or* deduplication. `f(likeCount) = likeCount + 1` is not idempotent; `f(likeSet) = likeSet ∪ {userID}` is — derive the count from the set. Dedup in a crash-recovery model needs the seen-IDs (or a vector clock) in **stable storage**. Limitation (slide 96): a delayed retry of an idempotent set-add can resurrect an element after a causally later remove — `f(f(x)) = f(x)` but `f(g(f(x))) ≠ g(f(x))`. That is why an inbox *by id* (or causal metadata) covers what a naturally idempotent write does not. The same CAS / version-vector machinery lives in the two DDIA notes this catalog **links**, not rewrites.

**Hohpe / Woolf, EIP *Idempotent Receiver*.** Even if the sender sends once, the receiver may see the message more than once. Two means: explicit de-duping, or message semantics that are naturally idempotent (`f(x) = f(f(x))`).

**Richardson, microservices.io *Idempotent Consumer*.** After beginning the DB transaction, insert the message ID into `PROCESSED_MESSAGE`. Primary key is `(subscriberId, messageID)`. The INSERT fails if the message was already processed successfully; rollback and ignore.

**Brandur Leach (2017-02-22 Stripe blog; 2017-10-27 brandur.org).** A key is “a unique value generated by a client”; the server bookkeeps request state and, once finished, short-circuits to the stored result. Keys are “not a permanent request archive” — recycle beyond a horizon of “say 24 hours or so.” The Postgres reference design adds *atomic phases* (local ACID work between foreign mutations), *recovery points* (`started` → `ride_created` → `charge_created` → `finished`), a *completer* that pushes unfinished keys through remaining phases after the client stops retrying, and a *reaper*. Suggested reaper threshold: **about 72 hours** (Friday-bug → Monday completer). Foreign mutations (Stripe charge, Kafka emit, email) cannot be rolled back by a local transaction; commit the phase *before* the call.

**Amazon Builders’ Library, Featonby, “Making retries safe with idempotent APIs.”** Preferred contract: a caller-provided client request identifier (EC2: `ClientToken`). Record the token and the mutation as one ACID operation. AWS SDK/CLI generate and **reuse** a token across their own retries when the caller does not supply one.

---

## 3. Mechanics

### 3.1 HTTP-method idempotency is not application idempotency

| Method | Safe? | Idempotent? | What a retry does without a key |
|---|---|---|---|
| GET / HEAD / OPTIONS / TRACE | yes | yes | Same intended effect; response may differ |
| PUT | no | yes | Replace the representation again |
| DELETE | no | yes | Resource stays gone (response may be 200 then 404/410) |
| POST | no | no | A second order / charge / email |
| PATCH | no | no | A second partial apply |
| CONNECT | no | no | New tunnel |

PUT/DELETE being idempotent does **not** make them safe to fire from a crawler, and does **not** make a *create-via-POST* retryable. The control for POST is a key minted **once per business operation** — before the first attempt — and reused across HTTP retries, queue replays, breaker fallbacks, and Temporal/Step Functions activity retries. Minting a key per HTTP attempt is dedup theater.

RFC 9110 idempotency is about *intended effect*, not byte-identical responses. A first DELETE may return 200 and a second 404; the resource state is the same. Application-key stores usually go further and **replay the first status + body** so the client can treat the retry as the original answer (Stripe v1, IETF “respond with the result of the previously completed operation”).

Conditional HTTP (`If-Match: <etag>`, `If-None-Match: *`) is the web’s CAS and belongs with [lost-updates.md](../../../cases/data-intensive-design/lost-updates.md) (RFC 9110 §13). It prevents a lost update on a *known* resource; it does not bind two POSTs that have not yet created one.

### 3.2 The key protocol — Stripe (verified) and IETF draft-07 (status 2026-09-13)

**IETF status on 2026-09-13.** `draft-ietf-httpapi-idempotency-key-header-07` (Jena & Dalal, 2025-10-15) is the latest **numbered** revision on datatracker.ietf.org. Type: *Expired Internet-Draft (httpapi WG) — Expired & archived*. Last updated 2026-04-18 (expiry of -07). IESG state: **Expired**. Stream: WG Document. Intended RFC status: **(None)**. It is **not an RFC**. No `-08` appears in the version list. A GitHub editor’s copy (`ietf-wg-httpapi/idempotency`, `docname: …-latest`) exists; it is not a submitted draft and is **not** cited as current text below. The `-07` `.txt` was fetched from `ietf.org/archive/id/`.

Draft-07 mechanics (paraphrase; MUSTs as written):

- `Idempotency-Key` is an Item Structured Header (RFC 8941) whose value **MUST** be a String. Example: `Idempotency-Key: "8e03978e-40d5-43e8-bc93-6894a57f9324"`.
- The key **MUST** be unique and **MUST NOT** be reused with a different payload. UUID (RFC 4122) or similar random identifier is **RECOMMENDED**.
- Expiry: the resource **MAY** require time-based keys so it can purge; it **SHOULD** define and **publish** that policy. **No numeric TTL is specified.**
- Fingerprint **MAY** be a checksum of the whole body, selected fields, field-value match, or a request digest.
- First sight of (key, fingerprint): process normally. Completed duplicate: return the stored result (success *or* error). In-flight duplicate: conflict.
- Errors: **400** if the header is missing on a documented-required operation (RFC 7807 `application/problem+json` example, or a `Link`); **422 Unprocessable Content** (RFC 9110 §15.5.21) if the key is reused with a different payload; **409 Conflict** if the original is still outstanding. Clients **MUST** correct 400/422 before retrying; 409 needs no correction — wait and reuse the same key.
- Security: validate the key; look up on a **composite** of client key + server-only attributes so low-entropy keys cannot fetch another tenant’s cache.

The draft’s own introduction lists OPTIONS, HEAD, GET, PUT, DELETE as idempotent and omits TRACE (which RFC 9110 §9.2.1 marks safe, hence idempotent). Use 9110 for the method table; use the draft for the header.

**Stripe API v1** (`docs.stripe.com/api/idempotent_requests` + `error-low-level`, fetched 2026-09-13):

- Header `Idempotency-Key`. Suggested V4 UUID or another high-entropy string; **up to 255 characters**; do not put email/PII in the key.
- **All POST** accept keys. **Do not send on GET or DELETE** — “it has no effect. These requests are idempotent by definition.”
- Saves “the resulting status code and body of the first request … regardless of whether it succeeds or fails.” Subsequent same-key requests return that result, **including `500` errors**.
- “You can remove keys from the system automatically after they’re **at least 24 hours** old.” Reuse after prune = a **new** request.
- Incoming parameters are compared to the original; mismatch **errors** (exact status not named on this page — do not assert 422).
- Results are saved **only after endpoint execution begins**. Validation failure, or conflict with a concurrently executing request, is **not** saved; those may be retried with the same key.
- `429` can produce a different result with the same key “because rate limiters run **before** the API’s idempotency layer.” Same for a `401` that omitted a key and most `400`s with invalid parameters. Safest 4xx strategy: **new key** after you change the request. Do **not** mint a new key on a `500` — the original may have had side effects; Stripe “tries to roll it forward” or back and fire webhooks; treat `500` as indeterminate.
- Replay marker: response header **`Idempotent-Replayed: true`**.
- Status table lists **409 Conflict**: “The request conflicts with another request (perhaps due to using the same idempotent key).”
- `Stripe-Should-Retry: true|false` overrides status-code guesswork; official SDKs honour it. Example: `Stripe.max_network_retries = 2`.

**Stripe API v2** (`docs.stripe.com/api-v2-overview`, fetched 2026-09-13) — different contract, do not mix with v1:

| | API v1 | API v2 |
|---|---|---|
| Verbs | POST only | POST **and DELETE** |
| Replay window | same key within **24 hours** | same key, **same API**, same account/sandbox, within **30 days** |
| Failed first attempt | replay the cached error, including 5xx | **re-execute** the failed work without producing side effects; return the new outcome (or explain why a replay can no longer succeed) |
| Missing key | (client must send) | Stripe **generates a UUID** |

v2 successful-first-request path: skip new changes and return an *updated* response. That is AIP-155’s “stale success” permission, not v1’s frozen first body.

**Other verified header dialects** (draft-07 §4 lists these as implementers; numbers below are from the *vendor* pages, fetched 2026-09-13):

| Vendor | Header / field | Retention / scope | Concurrent duplicate |
|---|---|---|---|
| **Adyen** | `idempotency-key` (case-insensitive), max **64** chars, UUID recommended | **7 to 14 days**; uniqueness at **company account**; **not** checked across regional endpoints | HTTP **422 or 409**, error **704** “request already processed or in progress”; `transient-error: true` means retry same key later. Store down → **503** + **703**. |
| **PayPal** | `PayPal-Request-Id` (not `Idempotency-Key`) | Guidelines page (updated 2026-08-11): “as long as the server stores the ID” — **see the API reference**. Requests page (updated 2026-07-27): refund-captured-payment example **up to 45 days**. UUID, **38** single-byte-char limit. Must be unique **per request and per API call type** (authorize ≠ capture). | “Processes the first and **might fail** the second.” Returns **latest** status, not the original snapshot. |
| **AIP-155** | `request_id` on the *request message* (not the resource), optional, UUID4, “Restricted to **36** ASCII characters” | “any reasonable timeframe” | Duplicate **should** return the previously successful response; if history is gone, **may** return current resource state. |
| **AWS EC2** | `ClientToken`, case-sensitive, up to **64** ASCII | (page does not publish a TTL) | Parameter change → `IdempotentParameterMismatch`. 200: do not retry. 5xx: retry same token. |
| **Square** | `idempotency_key` **in the body** (draft-07 §4.1) | — | — |

### 3.3 At-least-once + idempotent consumer

Every at-least-once path **will** redeliver: SQS visibility expiry, Kafka crash after process-before-commit, Pub/Sub expired ack, webhook producer retry **[→A2]** **[→A5]**. “Exactly-once” labels on brokers are scoped:

| Claim (do not treat as end-to-end EOS) | What the primary page actually covers | Cite |
|---|---|---|
| Kafka `enable.idempotence` | Broker-side retry duplicates, **per partition, per producer session**, via `(producerId, epoch, sequence)`. Your second `send()` is two messages. Default **true** since 3.0 (KIP-679) if no conflicting configs; requires `acks=all`, `retries>0`, `max.in.flight ≤ 5`. | kafka.apache.org/43/configuration/producer-configs; **[→A2]** |
| Kafka EOS / Streams `exactly_once_v2` | Output records **and** input offsets in one transaction. Side effects outside Kafka are not in it. Consumer default `isolation.level=read_uncommitted`, `enable.auto.commit=true`. | **[→A2]** |
| SQS FIFO “exactly-once processing” | Producer retries inside a **5-minute** `MessageDeduplicationId` window (or SHA-256 of **body**, attributes excluded). Visibility expiry still redelivers to a consumer. Window is **not configurable**. | AWS SQS Developer Guide + `SendMessage` API |
| Pub/Sub “exactly-once delivery” | No resend of an **acked** `messageId`. Publisher retries mint **new** ids. Pull, one region. | **[→A2]** |
| EventBridge | Target retries default **24 hours** and up to **185** times (exponential backoff + jitter); then drop or DLQ. `MaximumEventAgeInSeconds` 60–86400 (default 86400); `MaximumRetryAttempts` 0–185 (default 185). | `eb-rule-retry-policy` + `API_RetryPolicy` |
| Step Functions Standard | “Tasks and states are never run more than once, **unless you have specified `Retry`** in ASL.” Marketed for non-idempotent actions. Same-name start while running → idempotent reject. History kept **90 days** (reducible to 30). | `choosing-workflow-type` |
| Step Functions Express | Async: **at-least-once** (idempotency “not automatically managed”). Sync: **at-most-once**. Max duration **5 minutes**. | same |
| Temporal Activities | “May be executed multiple times and may even **partially complete more than once**.” Recommended key: **Workflow Run ID + Activity ID** (stable across retries, unique among executions). Completed activities do not re-run on *workflow* replay; they *do* retry if the worker dies before reporting. | `docs.temporal.io/activity-definition` |

**Inbox algorithm** (link, do not rewrite: [distributed-transactions.md](../../../cases/data-intensive-design/distributed-transactions.md)):

1. Unique message / business-operation ID.
2. Begin DB transaction; insert ID (or look up). Duplicate → commit nothing, ack broker, drop.
3. Else insert ID, do business writes, commit.
4. Then ack the broker.
5. Optionally delete the ID later (space). Leftover IDs only waste space.

Crash before commit → abort, broker retries. Crash after commit, before ack → retry sees the ID. A uniqueness constraint serializes two in-flight retries. An email server that is not in the transaction will still double-send — every *effect* needs its own guard.

Two storage placements (Richardson): a separate `PROCESSED_MESSAGES` table, or the IDs *on the business row* (the order’s `idempotency_key` unique index). The second is natural when the message *is* “create this order.”

### 3.4 Dedup-store variants

| Variant | Mechanism | When it wins | When it loses |
|---|---|---|---|
| **Replay-the-first-response** (Stripe v1, IETF completed-duplicate) | Store status+body; short-circuit | Client can treat retry as the original HTTP answer | Frozen 500s; store must be consistent |
| **Re-execute failed, skip succeeded** (Stripe v2, Brandur recovery points) | Persist phase; resume | Timeout mid-flight can still finish | More moving parts; completer required |
| **ACID inbox PK** | Insert `(subscriber, id)` + effect | Local DB is the system of record | Foreign mutations (card, email) need their own key |
| **Conditional write** | DynamoDB `attribute_not_exists`; SQL `WHERE version=` | One item, no extra table | Lost-update / OCC belongs in [lost-updates.md](../../../cases/data-intensive-design/lost-updates.md) |
| **Broker producer window** | SQS FIFO 5 min; Azure Service Bus `MessageId` history | Cheap first line for client send-retries | Window << queue retention / DLQ redrive |
| **Natural idempotency** | PUT-replace; set-add; `CREATE IF NOT EXISTS` | No extra store | Kleppmann add-then-remove; increments |

**Azure Service Bus duplicate detection** (fetched 2026-09-13): Standard/Premium only. Tracks application `MessageId` for a history window — default **10 minutes**, min **20 seconds**, max **7 days**. Send is accepted but the duplicate is dropped. Only `MessageId` is compared (plus `PartitionKey` when partitioned). Larger windows cost throughput. This is *producer-send* dedup, same class as SQS FIFO 5 min — the consumer still needs an inbox.

**AWS Lambda Powertools (Python) idempotency** (`docs.aws.amazon.com/powertools/python/latest/utilities/idempotency/`, fetched 2026-09-13). Default persistence: DynamoDB (Redis also documented). `IdempotencyConfig.expires_after_seconds` default **3600** (1 hour); “no limit” on how large you set it. Hash default **md5**. Local cache off; `local_cache_max_items` 256 in the config signature (docs also mention 1024 in one constructor comment — use the documented `expires_after_seconds=3600` as the number). Record states `INPROGRESS` → `COMPLETE`; a second invocation while `INPROGRESS` is rejected until `in_progress_expiration`. They **do not** rely on DynamoDB TTL to decide expiry (TTL delete is asynchronous, “typically within a few days”).

### 3.5 Concurrent in-flight (the 409)

Two retries of the same key can overlap. Stripe v1 does not save the result of a concurrent conflict (retry same key). IETF **SHOULD** 409. Adyen 422 or 409 + 704. PayPal “might fail” the second. Powertools holds `INPROGRESS`. The client must **reuse the key** after a 409 — minting a new one is how a double charge is born.

---

## 4. Verified defaults / standards (fetched 2026-09-13)

| Knob | Default / published value | Source |
|---|---|---|
| RFC 9110 idempotent methods | PUT, DELETE + GET, HEAD, OPTIONS, TRACE | rfc-editor.org/rfc/rfc9110.txt §9.2 |
| IETF `Idempotency-Key` draft | **-07**, 2025-10-15, **expired 2026-04-18**, not an RFC; 400 / 422 / 409; no TTL | datatracker + archive `.txt` |
| Stripe v1 key length | ≤ **255** chars | `api/idempotent_requests` |
| Stripe v1 retention | prune after **≥ 24 hours** | same + `error-low-level` (“keys expire … after 24 hours”) |
| Stripe v1 verbs | POST only | same |
| Stripe v2 retention | **30 days**, same API + account/sandbox | `api-v2-overview` |
| Stripe v2 verbs | POST and DELETE | same |
| Stripe replay header | `Idempotent-Replayed: true` | `error-low-level` |
| Adyen key length | ≤ **64** chars | `docs.adyen.com/.../api-idempotency` |
| Adyen retention | **7 to 14 days**, company account | same |
| PayPal header | `PayPal-Request-Id`, UUID, **38** bytes | `api/rest/reference/idempotency` (2026-08-11) |
| PayPal example TTL | **45 days** (refund captured payment) | `api/rest/requests` (2026-07-27) |
| AIP-155 | optional UUID4, **36** ASCII; “any reasonable timeframe” | google.aip.dev/155 |
| AWS Powertools expiry | **3600 s**; hash **md5** | Powertools Python latest |
| AWS EventBridge target retry | **24 h** / **185** attempts | `eb-rule-retry-policy` |
| SQS FIFO producer dedup | **5 minutes**, not configurable; id ≤ **128** chars | SQS Developer Guide + `SendMessage` |
| SQS retention (for contrast) | default **4 days**, max **14 days** | **[→A2]** |
| Azure Service Bus dup history | default **10 min**, min 20 s, max **7 days** | learn.microsoft.com duplicate-detection |
| Kafka `enable.idempotence` | **true** if no conflicting configs (3.0+ / 4.3 page) | kafka.apache.org/43 + KIP-679 |
| Kafka `producer.id.expiration.ms` | **86400000** (1 day); keep ≥ `delivery.timeout.ms` | KIP-854 |
| Step Functions Standard | exactly-once **unless `Retry`**; history **90 days** | `choosing-workflow-type` |
| Step Functions Express async | at-least-once; max **5 min** | same |
| Temporal activity key | `workflowRunId + activityId` | temporal.io activity-definition + blog |
| Brandur recycle / reaper | “~24 hours” recycle; **~72 hours** reaper suggestion | brandur.org/idempotency-keys (2017-10-27) |
| EC2 `ClientToken` | ≤ **64** ASCII | EC2 API idempotency |

---

## 5. Knobs, observability, tuning

### 5.1 Knobs

| Knob | Role | Too small | Too large |
|---|---|---|---|
| **Key retention** | Outlive the longest path a duplicate can travel (client retry horizon **[→C2]**, queue visibility + DLQ redrive, operator replay, Brandur completer) | Late redrive is a new charge (SQS 5 min vs 14-day retention) | Store growth; accidental key-reuse after the business operation ended looks like a conflict |
| **Key scope** | Tenant × operation × API | Cross-tenant leaks (IETF composite-key warning; Adyen: two credentials under one company share the cache) | Duplicates across scopes undetected (PayPal: authorize vs capture must differ) |
| **Fingerprint** | Bind key to payload | Key reuse with a “fixed” body charges the new amount | Over-strict (unsigned JSON key order) rejects legitimate retries |
| **In-flight lock** | 409 / INPROGRESS | Two workers both execute | Client storms 409s; lock expiry (Powertools) re-runs while the first is still going |
| **Inbox PK grain** | `(subscriber, messageId)` vs business key | Whole-request only → emails/loyalty fire twice | Per-effect table sprawl |
| **Broker window** | First-line send-dedup | SQS 5 min / SB 10 min miss redrives | Throughput cost (Azure: “keep the window as small as possible”) |

Placement: **client** (mint once, persist on the order row) → **edge/API** (Stripe-shaped store) → **consumer inbox** (ACID with the effect) → **foreign callee** (same key on the payment API). The key must be the same string on every hop. A gateway that mints its own UUID on each proxy attempt breaks the chain.

### 5.2 Observability (feeds D1 / D4)

| Signal | Why |
|---|---|
| **Replay rate** (`Idempotent-Replayed: true`, inbox PK collisions, Powertools cache hits) | Baseline ≈ retry rate **[→C2]**; a spike is a new duplicate source (rebalance, DLQ redrive, client double-submit) |
| **409 / in-flight conflicts** | Overlapping retries; if you mint a new key here you will double-charge |
| **422-class / parameter mismatch** | Client is reusing a key for a *different* operation (or JSON reordering failed the fingerprint) |
| **400 missing key** on a required POST | Client or proxy stripped the header |
| **Dedup-store size and age of oldest row** | Retention vs actual redrive horizon |
| **Effects without a guard** (email/loyalty counts vs keyed orders) | Partial idempotency |
| **Kafka `enable.idempotence` vs app-level double `send()`** | Producer EOS does not collapse two business operations |
| Span attribute: the key (or its hash) | Correlate retries across C2 / A5 / inbox without putting PII in the key |

No vendor PromQL recipe was found. OTel does not define a standard `idempotency.key` semantic convention on the pages fetched this pass (§10).

### 5.3 Tuning

1. Mint the key with the **business operation** (order id, or UUID stored *on* the order), never in the HTTP client’s retry loop.
2. Set retention ≥ `max(client retry schedule, queue retention + DLQ redrive, EventBridge 24 h, operator replay window)` plus a Monday-morning Brandur margin if you run a completer.
3. Do not trust a 5-minute or 10-minute *broker* window as the consumer inbox.
4. Fingerprint the semantic body; exclude timestamps and server-injected fields.
5. On 409 / `transient-error: true`: wait, **same key**. On 422 / mismatch: **new** key only after you intend a new operation.
6. On 500 with a stored result (Stripe v1): do not rotate the key; reconcile via webhooks / GET.
7. One inbox row per hop that has an external effect. The outbox (**B7**) is the other direction.

---

## 6. Worked calibration — checkout capture (double-charge drill)

Constraints are a **design drill**, not a vendor SLA. Method: Stripe v1 retention + IETF 409 + Brandur phases + inbox in [distributed-transactions.md](../../../cases/data-intensive-design/distributed-transactions.md) + the C7/C2 checkout budget (user-facing **3 s**, two retries, payment hop).

| Point | Control | Why |
|---|---|---|
| Key mint | `order_id`-derived key (or UUID written on `orders` at insert) | Survives process death between attempts; one operation, one key |
| HTTP `POST /capture` | Same `Idempotency-Key` on attempt 1 and every C2 retry | Timeout = unknown outcome; retry must collide, not re-charge |
| Fingerprint | Amount, currency, customer, `order_id` — not `requested_at` | A legit retry with a clock field must still match |
| In-flight | Treat 409 / Adyen 704 as “wait, same key” | Two browsers / two retries |
| Open-breaker fallback queue **[→C1]** | Message carries the **same** key | Queue replay is attempt *n*, not a new capture |
| Consumer inbox | `INSERT processed(consumer, key)` in the charge transaction | Rebalance / visibility expiry hits the PK |
| Gateway | Stripe v1 store, **≥ 24 h** (covers EventBridge 24 h and same-day redrive; **not** a 14-day SQS DLQ — for that, keep your *own* inbox) | Both sides of the wire dedupe |
| Refund | **New** key (`refund:` + refund id) | Same order, different operation (PayPal: unique per call type; B5 compensation) |
| Retention | Inbox **≥ 14 days** if SQS DLQ redrive is in play; Stripe key only covers *their* 24 h | Broker window is the first line, not the last |
| Completer | Optional job: keys stuck at `charge_created` for > 60 s | Client gave up; Brandur completer finishes the receipt |

Hedging stays off on `POST /capture` **[→C7]**. Status `GET /capture/{id}` may hedge; it is RFC-idempotent.

---

## 7. Failure modes and when-not-to-use

1. **Key per attempt.** Every retry is a new operation. The mint point is the design decision.
2. **HTTP method as the only control.** PUT is idempotent; `POST /charges` is not. Proxies that retry POST against RFC 9110 §9.2.2 create duplicates.
3. **Window shorter than the replay horizon.** SQS FIFO 5 min vs 4–14 day retention; Azure SB 10 min vs a weekend redrive; Kafka `producer.id.expiration.ms` < `delivery.timeout.ms` (KIP-854).
4. **Trusting “exactly-once” labels.** Kafka EOS is Kafka-to-Kafka; SQS FIFO is send-dedup + at-least-once consume; Pub/Sub exactly-once is ack-scoped; Step Functions Standard **excludes** your `Retry` blocks; Express async is at-least-once.
5. **Partial idempotency.** Order row is keyed; email / loyalty / webhook side effects are not. One order, three receipts.
6. **Rotating the key on 409 or 500.** 409 means in-flight; Stripe v1 500 may already have charged. Reuse, then reconcile.
7. **v1 frozen-500 vs v2 re-execute.** Mixing mental models: a v1 client that “retries until 200 with a new key” double-charges; a v2 client that assumes the first body is frozen will mis-handle a recovered failure.
8. **Idempotent-but-not-concurrent** (Kleppmann slide 96). Set-add after a causal remove; inbox-by-id or versions, not `f(f(x))=f(x)` alone. Version vectors: [detecting-concurrent-writes.md](../../../cases/data-intensive-design/detecting-concurrent-writes.md).
9. **Low-entropy or cross-tenant keys.** IETF injection / data-leak warning; Adyen: lowering a credential’s access does not hide past responses if the attacker still has the key.
10. **Fingerprint over- or under-matching.** Unsigned JSON key order; or no fingerprint so `amount` can change under the same key.
11. **Inbox in a different DB than the effect.** The PK no longer serializes with the write — you are back to 2PC or lost-update. Link [lost-updates.md](../../../cases/data-intensive-design/lost-updates.md).
12. **Dedup store as a new SPOF.** Adyen 503/703: fall back to *non-idempotent* processing (their documented option) or pause. Falling back is how you double-charge during the outage.
13. **TTL lock as correctness** without a fencing token — [quorums-and-fencing.md](../../../cases/data-intensive-design/quorums-and-fencing.md). Once the store can CAS, prefer the conditional write.
14. **IETF draft treated as an RFC.** As of 2026-09-13 it is expired; vendors already diverge (header names, 409 vs “might fail,” 24 h vs 7–14 d vs 45 d).

**When not to add a key store.** Reads (GET is already idempotent). True at-most-once you can afford to lose (metrics fire-and-forget). Natural PUT-replace of a whole aggregate you own, with no foreign mutation. A single-threaded in-process loop with no retry and no network.

**When a key store is the wrong *first* tool.** You needed an atomic SQL increment or `SELECT FOR UPDATE` ([lost-updates.md](../../../cases/data-intensive-design/lost-updates.md)). You needed causal metadata across replicas ([detecting-concurrent-writes.md](../../../cases/data-intensive-design/detecting-concurrent-writes.md)). You needed an outbox so the publish commits with the write (**B7**).

---

## 8. Cross-links

| Id / note | Why |
|---|---|
| **A1** | RFC 9110 methods; proxy MUST NOT retry POST; 421 may retry even if non-idempotent |
| **A2** | At-least-once *will* duplicate; Kafka/SQS/Pub/Sub scope lines |
| **A5** | Webhook receiver keys (`evt_…`, `webhook-id`); persist-then-2xx |
| **B5** | Compensation = new key |
| **B7** | Outbox is the send half of the inbox pair ([ch08.md](../../../cases/aws/ch08.md)) |
| **C1** | Fallback path must carry the same key (breaker research already names Stripe 24 h + IETF 422/409) |
| **C2** | Timeout on capture; `DisableForUnsafeHttpMethods`; do not rewrite jitter |
| **C7** | Do not hedge POST /capture |
| Cases | [lost-updates.md](../../../cases/data-intensive-design/lost-updates.md) · [detecting-concurrent-writes.md](../../../cases/data-intensive-design/detecting-concurrent-writes.md) · [distributed-transactions.md](../../../cases/data-intensive-design/distributed-transactions.md) · [durable-workflows.md](../../../cases/data-intensive-design/durable-workflows.md) |
| Concept | [Idempotency.md](../../../cases/SystemDesignPatterns/Idempotency.md) (distilled; this file is the fetch log) |

---

## 9. Sources

Fetched 2026-09-13 unless noted.

**HTTP / IETF.** rfc-editor.org/rfc/rfc9110.txt §9.2.1–9.2.2, §13, §15.5.21 · datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/ (status: expired -07) · ietf.org/archive/id/draft-ietf-httpapi-idempotency-key-header-07.txt · github.com/ietf-wg-httpapi/idempotency (repo only; editor’s copy not used as text)

**Stripe / Brandur.** docs.stripe.com/api/idempotent_requests · docs.stripe.com/error-low-level · docs.stripe.com/api-v2-overview · stripe.com/blog/idempotency (2017-02-22) · brandur.org/idempotency-keys (2017-10-27)

**Other APIs.** docs.adyen.com/development-resources/api-idempotency · developer.paypal.com/api/rest/reference/idempotency (2026-08-11) · developer.paypal.com/api/rest/requests (2026-07-27) · google.aip.dev/155 · docs.aws.amazon.com/ec2/latest/devguide/ec2-api-idempotency.html · docs.aws.amazon.com/wellarchitected/latest/framework/rel_prevent_interaction_failure_idempotent.html (REL04-BP04)

**Inbox / exactly-once vocabulary.** www.enterpriseintegrationpatterns.com/patterns/messaging/IdempotentReceiver.html · microservices.io/patterns/communication-style/idempotent-consumer.html · www.cl.cam.ac.uk/teaching/2425/ConcDisSys/dist-sys-notes.pdf (Kleppmann, slides 94–96) · cases/data-intensive-design/distributed-transactions.md (do not rewrite)

**Dedup stores / platforms.** docs.aws.amazon.com/powertools/python/latest/utilities/idempotency/ · docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/using-messagededuplicationid-property.html · docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SendMessage.html · learn.microsoft.com/azure/service-bus-messaging/duplicate-detection · kafka.apache.org/43/configuration/producer-configs.html · cwiki.apache.org KIP-679 · cwiki.apache.org KIP-854 · docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html · docs.aws.amazon.com/eventbridge/latest/APIReference/API_RetryPolicy.html · docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html · docs.temporal.io/activity-definition · temporal.io/blog/idempotency-and-durable-execution · aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/ (Featonby; live page fetched)

**Siblings.** [a1-request-response-external-research.md](a1-request-response-external-research.md) §3.1 · [a2-pubsub-queues-external-research.md](a2-pubsub-queues-external-research.md) §3.3–4 · [a5-webhooks-external-research.md](a5-webhooks-external-research.md) §3.1 · [retry-backoff-external-research.md](retry-backoff-external-research.md) §1 Stripe/IETF · [c7-timeouts-external-research.md](c7-timeouts-external-research.md) hedge-vs-POST

---

## 10. Uncertain / left out

- **Editor’s copy** of the IETF draft (`ietf-wg-httpapi.github.io/idempotency/…-latest.html`). Search snippets disagreed on expiry (2026-12-08 vs 2027-01-14). Not fetched as normative; datatracker **-07 expired** is the status asserted above. No `-08` on datatracker this day.
- **Stripe v1 payload-mismatch HTTP status.** Docs say “errors”; `error-low-level` names **409** for same-key *conflict*, not specifically for body mismatch. Do not claim Stripe returns IETF’s **422**.
- **PayPal per-API TTLs.** Only the refund example (**45 days**) and “see the API reference” are asserted. A “6 h–72 h Orders” figure appearing elsewhere in this tree was **not** re-found on the two PayPal pages fetched.
- **Adyen “minimum 7 days”** vs current page **“7 to 14 days”** — the fetched page is the range used above.
- **Powertools Python semver** on `/latest/` (page has no version banner this fetch). `local_cache_max_items` 256 vs a 1024 mention in one constructor docstring — not used. Exact `INPROGRESS` timeout default in seconds not extracted from the long page.
- **Kafka 4.3.x vs 4.1** broker HTML: `enable.idempotence` text fetched from **/43/**; A2 used 4.1. A silent default flip between 4.1 and 4.3 was not re-diffed beyond that page.
- **Pub/Sub exactly-once GA date (2022)** and SNS/EventBridge *consumer* semantics: broker facts stay in **[→A2]** except EventBridge 24 h / 185, which was re-fetched.
- **OTel** semantic convention for an idempotency-key attribute — not found; span advice above is a recommendation, not a spec.
- **NServiceBus / MassTransit / Spring Kafka** inbox table defaults — not fetched.
- **Featonby** live Builders’ Library page rendered; if it 409s in other sessions, use the PDF mirrors already cited by the breaker note.
- **Draft-07** implementation-status URLs (Worldpay, Yandex, Chargebee, …) were not re-fetched; only Stripe, Adyen, PayPal, AIP-155, EC2, Square-as-body-field are used as facts.
- PromQL alert shapes are own formulations.
- Nygard *Release It!* has no dedicated idempotency pattern in the breaker-research twelve; not forced in.
- The main-repo Concept points at `docs/research/sysdesign/idempotency-dedup-external-research.md`; that path is **not** this catalog file and was not written here.
