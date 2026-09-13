---
type: research
title: 'Saga — external research (2026-09-13)'
description: >-
  Source-verified research backing catalog B5: Garcia-Molina/Salem 1987 sagas,
  choreography vs orchestration, compensating transactions, ACD isolation,
  execution-log durability, timeout/retry interaction with C2/C7, outbox as
  the start of a saga (B7), and Temporal / Cadence / Step Functions / Azure
  Durable as dated engine examples — not a vendor how-to.
tags: [research, system-design-patterns, B5, saga]
---

# Saga — external research (2026-09-13)

> **What this is.** Evidence pass for catalog **B5** (Group B, CircuitBreaker
> depth bar). The Concept (when written) carries the distilled result; this
> note keeps verified facts, defaults, and URLs.
>
> **Method.** Primary pages fetched 2026-09-13. Paraphrase; numbers reproduced
> exactly. Unverified items are in **Uncertain / left out** and must **not**
> be asserted in the Concept.
>
> **Existing notes** (cite; do not rewrite):
> [aws/ch08.md](../../../cases/aws/ch08.md)
> (choreography vs orchestration; one-paragraph Saga),
> [distributed-transactions.md](../../../cases/data-intensive-design/distributed-transactions.md)
> (2PC / XA — do **not** re-derive),
> [durable-workflows.md](../../../cases/data-intensive-design/durable-workflows.md)
> (WAL-for-control-flow, Temporal fragment, versioning). Row-grain isolation:
> [lost-updates.md](../../../cases/data-intensive-design/lost-updates.md),
> [read-committed.md](../../../cases/data-intensive-design/read-committed.md).

---

## 1. Scope and non-goals

**Owns** the long-running *business* transaction that spans services without
a distributed lock: local commits + compensating transactions, coordinated
by choreography or orchestration. Depth: compensation semantics, execution-log
durability, isolation across steps, timeout/retry composition with C2/C7,
idempotent steps (C9), outbox/CDC as the *start* (B7), engine knobs as dated
examples.

| Id | Why it is not this card |
|---|---|
| **B7 Outbox & CDC** | Atomic DB write + message that *starts* a step. B5 names the dual-write hole. |
| **C9 Idempotency** | Keys / IETF `Idempotency-Key`. Every `Ti` and `Ci` must be idempotent; mechanics live here. |
| **C2 Retry / C7 Timeouts** | Classification, jitter, budgets, deadlines. B5 owns the branch: retry first, compensate after the budget. |
| **C1 Circuit breaker** | Fail-fast at a hop. Do not restack. |
| **E12 CQRS & ES / E4 EDA** | *Styles*. ES can persist saga events; choreography *uses* events. Neither owns compensation. |
| **A2 Pub/sub** | Broker, DLQ, ordering. B5 uses them as the choreography bus. |

**Non-goals.** Re-deriving 2PC/XA; rewriting the three existing notes; a
Temporal / Step Functions / Durable Functions / Cadence how-to; BPMN as a
second card; Eventuate as a recommended product.

---

## 2. Lineage / vocabulary

**García-Molina & Salem, *Sagas*, ACM SIGMOD 1987** (DOI
`10.1145/38713.38742`; PDF ISBN fragment `0-89791-236-5/87/0005/0249`;
https://www.cs.cornell.edu/andru/cs711/2002fa/reading/sagas.pdf ). A
**long-lived transaction (LLT)** that holds locks for hours/days blocks
shorter work and raises deadlock/abort rates. A **saga** is an LLT as a
sequence of *real* local transactions `T1…Tn` that **may interleave** with
others. Guarantee: either `T1,…,Tn` **or** `T1,…,Tj, Cj,…,C1`. `Ci` is a
**semantic undo** of `Ti` — not a restore of the bytes that existed when
`Ti` began (other transactions may have run). Airline: `Ti` reserves a
seat; `Ci` decrements the count — it must **not** write back the old
count. **No notify/abort** of transactions that already saw `Ti`. That is
the isolation hole.

**Richardson, *Pattern: Saga*** (fetched 2026-09-13)
https://microservices.io/patterns/data/saga.html — Database-per-Service
transaction as local commits + messages; business-rule failure →
compensates. **Choreography** = participants exchange domain events;
**orchestration** = a persistent orchestrator sends commands and processes
replies. No automatic rollback; **no isolation** (the "I" in ACID) —
countermeasures in *Microservices Patterns* ch. 4 §4.3 (book body not
fetched; the list is on Azure and in the 2017 talk — §3.4). Each step must
atomically update DB + publish (outbox / ES → **B7 / E12**). HTTP `POST`
outcomes: wait, poll, or push.

Coordination posts: part 2 (2019-08-04)
https://microservices.io/post/sagas/2019/08/04/developing-sagas-part-2.html
· part 3 (2019-08-15)
https://microservices.io/post/sagas/2019/08/15/developing-sagas-part-3.html
— first step is an external command; later steps are event-triggered;
choreography scatters the saga. QCon SF 2017 slides
https://qconsf.com/sf2017/system/files/presentation-slides/dataconsistencyinmicroserviceusingsagasqconsf2017-1711151847291.pdf
name the model **ACD** and **compensatable → pivot → retryable**.

**Azure *Saga* pattern** (`ms.date` **2025-02-25** on
https://github.com/MicrosoftDocs/architecture-center/blob/main/docs/patterns/saga.yml ;
Learn fetched 2026-09-13)
https://learn.microsoft.com/en-us/azure/architecture/patterns/saga —
same two styles; compensable / pivot / retryable; anomalies + six
countermeasures. Companion **Compensating Transaction**
https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction
— application-specific, eventually consistent, resumable, idempotent;
retry transients *before* compensating; human-in-the-loop for high-impact
choices (offer another hotel before cancelling flights). **Choreography**
pattern points at Saga + DLQ after a dead letter
https://learn.microsoft.com/en-us/azure/architecture/patterns/choreography

**AWS Prescriptive Guidance** (fetched 2026-09-13). Overview: *continuation*
(retry / forward) vs *compensation* (backward). Platform failure → retry;
application failure → compensate.
https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-patterns.html
Choreography: EventBridge; **dual-write** named; outbox as the fix; ES for
audit/replay.
https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-choreography.html
Orchestration: Step Functions; order → inventory → payment with reverse
`Revert*` Lambdas; `TracingEnabled = true`; sample
`aws-samples/saga-orchestration-netcore-blog`.
https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-orchestration.html

**Workspace (link only).** [aws/ch08.md](../../../cases/aws/ch08.md) §
choreography vs orchestration (hybrid: orchestrate pay/reserve/ship,
choreograph notifications) and the one-paragraph Saga. 2PC stays in
[distributed-transactions.md](../../../cases/data-intensive-design/distributed-transactions.md);
engine replay stays in
[durable-workflows.md](../../../cases/data-intensive-design/durable-workflows.md).

---

## 3. Mechanics (Group B depth)

### 3.1 What it is

Atomicity *reconstructed* from already-committed local transactions. Each
`Ti` commits in its own DB (or at a third-party API). **Business** failure
→ compensate completed steps. **Transient / platform** failure → retry
that step (AWS continuation). There is never a prepare-phase lock across
services — that is 2PC
([distributed-transactions.md](../../../cases/data-intensive-design/distributed-transactions.md)).
The guarantee is **ACD**, not ACID (Richardson 2017).

### 3.2 Variants

| Variant | Who decides next | Trade-off |
|---|---|---|
| **Choreography** | Each participant, by publishing a domain event | No orchestrator SPOF; cyclic deps; scattered logic; AWS: timeouts/retries "must be implemented on individual components." |
| **Orchestration** | Persistent orchestrator / state machine | Central compensate, timeout, retry; SPOF unless the *engine* is HA (AWS names Step Functions Multi-AZ). |
| **Hybrid** ([ch08.md](../../../cases/aws/ch08.md)) | Orchestrate the core; choreograph side effects | Clear compensate ownership; overlapping-responsibility risk. |
| **Durable-execution engine** ([durable-workflows.md](../../../cases/data-intensive-design/durable-workflows.md)) | Workflow definition; history is the log | Replay is "exactly-once *workflow*" only if callees are idempotent (C9). |

A choreographed *start* (outbox event) can create an orchestrated saga.

### 3.3 Compensating transactions

García-Molina: semantic undo. Azure: cannot "restore original state" if
concurrent work moved the data; apply **business rules** (partial refund,
not a full restore). Need **not** run in exact reverse (undo the most
inconsistency-sensitive store first; some undos parallel). Compensation
**can fail** — journal, resume, every `Ci` idempotent; human path is
first-class.

**Retry before compensate** (Azure; AWS: platform → continuation). Prefer
an *alternative path* over cancelling (another hotel). Pause for a human
when the choice is high-impact.

**Pivot** (Azure + Richardson 2017). After it succeeds, compensable steps
are no longer the recovery path. Later steps are **retryable** and must
eventually succeed. Place irreversible / legally binding steps (card
capture, regulatory file) at or after the pivot.

```
compensatable T1…Tk   →   pivot Tk+1   →   retryable Tk+2…Tn
     Ck…C1 on fail          fail → Ck…C1     fail → retry until done
```

### 3.4 Isolation (lost updates / dirty reads across steps)

Locks drop at each local commit. Azure + Richardson 2017 name three
anomalies (row-grain versions of
[lost-updates.md](../../../cases/data-intensive-design/lost-updates.md) /
[read-committed.md](../../../cases/data-intensive-design/read-committed.md),
but the window is the *whole saga*):

| Anomaly | Across-step shape |
|---|---|
| **Lost update** | Saga A writes; B writes the same row without reading A; A's later `Tj`/`Ci` clobbers B. |
| **Dirty read** | B reads a value A wrote in a compensatable step; A then compensates. |
| **Fuzzy / nonrepeatable read** | Two steps of the *same* saga read one key and get different results because another saga wrote between them. |

**Countermeasures** (Azure; same six on the 2017 slides):

1. **Semantic lock.** Compensatable step sets `PENDING` / a flag; others
   must not treat the row as committed. Richardson `Create Order`:
   `cancelOrder` only if `APPROVED`. Application-level; needs a
   **timeout** or it deadlocks (2017: "deadlock detection, e.g. timeout").
   AWS PG independently recommends semantic locking.
2. **Commutative updates.** Debit/credit so compensate is `+N` after `-N`.
3. **Pessimistic view.** Reorder so the risky write is retryable (never
   compensated) — decrease credit compensatably, increase it retryably.
4. **Reread values.** Before a later write, re-read; abort/restart if changed.
5. **Version files.** Append-only ops so create-then-cancel = cancel-then-create
   (2017: "sounds like event sourcing" — **E12**, not this card).
6. **Risk-based concurrency.** Low-risk → saga; high-risk → one DB or
   *database-internal* 2PC, not XA.

### 3.5 Execution / log durability

Forgetting "we already reserved inventory" double-reserves or skips
compensate. The log *is* the atomicity mechanism.

| Approach | What is durable | If missing |
|---|---|---|
| **Outbox / CDC (B7)** | Local write + next message in **one** commit; relay publishes | Dual-write split-brain (AWS choreography; Richardson's reliability requirement). Eventuate Tram = one implementation, not a recommendation. |
| **Orchestrator journal** | Azure example: Cosmos records each forward step **and** its compensate | Crash after `Ti` commits, before the journal → `Ti` invisible to compensate. |
| **Engine history** ([durable-workflows.md](../../../cases/data-intensive-design/durable-workflows.md)) | Temporal Event History / SFN execution history / Durable History table; replay skips completed RPCs | History-quota kill; non-deterministic workflow code; version skew. |

**Engine caps (examples, fetched 2026-09-13).**

| Engine | Hard caps | Escape |
|---|---|---|
| **Temporal** Cloud + self-hosted defaults (Cloud: non-configurable). Server **v1.31.2** (2026-07-08). | **51 200 events or 50 MB** (warn 10 240 / 10 MB); 2 000 Updates; 10 000 Signals; payload **2 MB**; history txn **4 MB**; gRPC **4 MB**; no Workflow time cap | Continue-As-New; offload blobs. https://docs.temporal.io/workflow-execution/event · https://docs.temporal.io/cloud/limits |
| **Step Functions Standard** | **25 000** events (event 25 000 must be `ExecutionSucceeded` or fail); **1 year**; idle 1 year; history **90 days** (reducible to 30); I/O **256 KiB**; 1 000 000 open exec / account / Region | Nested `StartExecution`, Distributed Map. Express: **5 min**, unlimited history, at-least-once — wrong for capture. https://docs.aws.amazon.com/step-functions/latest/dg/service-quotas.html |
| **Azure Durable Functions** | `maxOrchestrationActions` **100 000** / cycle; worker `functionTimeout`: Consumption **5 / 10** min; Flex/Premium/Dedicated **30** min default, unbounded max | Sub-orchestrations; async HTTP (HTTP trigger still **230 s** LB idle). https://learn.microsoft.com/en-us/azure/durable-task/durable-functions/durable-functions-host-json-settings · https://learn.microsoft.com/en-us/azure/azure-functions/functions-scale |

Replay still needs idempotent callees + deterministic workflow code —
[durable-workflows.md](../../../cases/data-intensive-design/durable-workflows.md).
Version in-flight definitions like an encoding.

### 3.6 Timeout + retry (C2 / C7) and idempotency (C9)

C2 owns whether/how to retry a hop; C7 owns how long and remaining
deadline. B5 owns the **branch**:

1. **Transient / platform** (timeout, 502/503, worker crash) → retry the
   *same* step under the remaining saga deadline. Do **not** compensate
   yet.
2. **Business reject** (no credit, bad card, out of stock) → do not retry
   unchanged; compensate preceding compensatable steps (or take an
   alternative path).
3. **Timeout-unknown** (capture: the 200 may be lost) → "maybe succeeded."
   Safe only with a **C9 key** minted once per (saga-id, step) and reused
   on retry *and* compensate. Compensating a never-applied capture = no-op;
   retrying an applied capture must not double-charge.
4. **Open circuit (C1)** → fail fast into the saga decision. Do not retry
   Open (C2).
5. **Stacked retries** — orchestrator + SDK + broker redelivery is three
   layers. One retry owner per hop (usually the orchestrator / activity
   policy); callee fail-fast.

Choreography has no *global* timeout (AWS). A missing hop timeout leaves
the saga `PENDING` and the semantic lock never releases.

**C9** owns key stores. Saga-specific: mint once per `(saga-id, step)`;
reuse across retry, outbox replay, and the `Ci` that undoes that step;
`Ci` for a never-applied `Ti` is a documented no-op.

### 3.7 Outbox as the *start* (B7)

The first local TX must **atomically** update state and publish the
event/command that creates the rest. Crash between `COMMIT` and
`producer.send` → saga never starts, or starts twice. **B7** is the
mechanism. Eventuate `SagaManager.create` in the same `@Transactional`
as `orderRepository.save` is the *shape*. ES (E12) is an alternative
log, not a second saga card.

### 3.8 Placement

| Layer | Coordinates | Compensate / rollback |
|---|---|---|
| HTTP edge | Accept command; 202 + saga id (Richardson option 2) | Client polls; no 2PC. |
| Outbox in first service (B7) | Durable *start* | Relay; at-least-once to bus or orchestrator. |
| Choreography bus (A2) | Next `Ti` / `Ci` | Compensation events; DLQ → human (Azure Choreography). |
| Orchestrator / engine | Sequence, timeouts, retries, reverse `Ci` | Catch → compensate; journal/history is SoT. |
| Participant | Local ACID + idempotent handler | Semantic lock; local `Ci`. |

Domain rules do not belong in the bus (same Hold as C6 / B4).

---

## 4. Verified defaults / standards (knobs)

Fetched 2026-09-13. No Resilience4j of sagas. These are **engine**
defaults for the orchestrator variant. Choreography inherits the broker (A2).

### 4.1 Temporal — Activity Retry Policy

Server **v1.31.2** (2026-07-08).
https://docs.temporal.io/encyclopedia/retry-policies ·
https://docs.temporal.io/encyclopedia/detecting-activity-failures ·
`io.temporal:temporal-sdk` **1.31.0** javadoc (same numbers).

| Knob | Default | Saga reading |
|---|---|---|
| Activity retries | **On** (Workflow retries **off**) | Retry the *step*, not the whole saga. |
| `InitialInterval` | **1 s** | |
| `BackoffCoefficient` | **2.0** | |
| `MaximumInterval` | **100 × Initial** (100 s) | |
| `MaximumAttempts` | **0 = unlimited** | Bound with `ScheduleToCloseTimeout` or a business error retries forever. |
| `NonRetryableErrorTypes` | `[]` | Put business rejects here so they fail into compensate. |
| `ScheduleToCloseTimeout` | **∞** | Overall step budget incl. retries. Required: this *or* `StartToClose`. |
| `StartToCloseTimeout` | = Schedule-To-Close if unset | Per-attempt. **Strongly recommended** — server detects worker crash *only* via this. |
| `ScheduleToStartTimeout` | **∞**; **non-retryable** | Prefer metric `temporal_activity_schedule_to_start_latency`. |
| Heartbeat throttle | `min(heartbeatTimeout×0.8, max)`; default interval **30 s**, max **60 s** | Long captures must heartbeat. |
| Workflow Execution Timeout | **unlimited** | History size is the real cap. |

Disable retries: `MaximumAttempts = 1`. Non-retryable `ApplicationFailure`
(invalid charge) skips the policy.

### 4.2 AWS Step Functions — Task + Retry

https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html
· `/state-task.html` · `/sfn-best-practices.html`

| Knob | Default | Saga reading |
|---|---|---|
| Unhandled error | **Fail the execution** | `Catch` onto compensate. AWS sample sets `RetryOnServiceExceptions = false` so a business `ERROR` can branch to `Revert*`. |
| Task `TimeoutSeconds` / `HeartbeatSeconds` | **99 999 999** | ASL specifies no *useful* timeout; unspecified Task **waits forever**. HTTP Task hard-cap **60 s**. |
| `Retry.IntervalSeconds` | **1** (max 99 999 999) | |
| `Retry.MaxAttempts` | **3** (`0` = never) | Then Catch / fail. |
| `Retry.BackoffRate` | **2.0** | |
| `Retry.MaxDelaySeconds` | unset = **no cap** | Range (0, 31 622 401). |
| `Retry.JitterStrategy` | **`NONE`** | `FULL` = `random(0, interval)` (C2). Turn on for a fleet of sagas. |
| Standard vs Express | 1 year / 25k events / history vs 5 min / unlimited / at-least-once | Capture+compensate → **Standard**. |
| Payload | **256 KiB** | Store ids, not cart blobs. |

Retries are billed state transitions. Redrive resets the retry counter
(14-day Standard window).

### 4.3 Azure Durable Functions / Durable Task

https://learn.microsoft.com/en-us/azure/durable-task/common/durable-task-error-handling
· `…/durable-functions-host-json-settings` ·
https://learn.microsoft.com/en-us/azure/azure-functions/functions-scale
(scale `ms.date` 2025-12-09; `updated_at` 2026-06-02).

**Activity retry** — none unless you pass `RetryPolicy`:

| Knob | Documented default |
|---|---|
| Max attempts | You set it; **1** = no retries |
| First retry interval | Required when a policy is set |
| Backoff coefficient | **1** (no growth — unlike Temporal / SFN 2.0) |
| Retry timeout | **indefinite** |
| Unhandled orchestrator exception | instance → **`Failed`**; **cannot be retried** — compensate *inside* try/catch first |

**host.json `durableTask` defaults that bite:**

| Knob | Default |
|---|---|
| `maxConcurrentActivityFunctions` | Consumption **10**; Dedicated/Premium **10 × processors** |
| `maxConcurrentOrchestratorFunctions` | Consumption **5**; Dedicated/Premium **10 × processors** |
| `maxOrchestrationActions` | **100 000** |
| Control / work-item visibility timeout | **00:05:00** |
| `partitionCount` | **4** (1–16; change = new hub) |
| `versionMatchStrategy` / `versionFailureStrategy` | `CurrentOrOlder` / `Reject` |
| `traceInputsAndOutputs` / `traceReplayEvents` | **false** / **false** |
| Activity `functionTimeout` | Consumption **5 / 10** min; Flex/Premium/Dedicated **30** min default, unbounded max |

A Consumption activity-step dies at 5 minutes (10-minute ceiling). Long
captures belong on Flex/Premium or webhook + Durable external event.

### 4.4 Cadence (Java client, fetched 2026-09-13)

https://cadenceworkflow.io/docs/java-client/retries · `cadence-client`
4.0.0 javadoc: `setRetryOptions` default **null = no retries**.
`RetryOptions`: `InitialInterval` **required**; `BackoffCoefficient`
default **2.0**; `MaximumInterval` default **100 × Initial**; either
`ExpirationInterval` or `MaximumAttempts` required (`0` = unlimited).
Timeouts: `ScheduleToClose` **or** both `ScheduleToStart` +
`StartToClose`; if only `ScheduleToClose`, the other two default to it;
all capped by workflow timeout. Sample on that page: `bookingsaga`.
Cadence = Temporal's predecessor — dated example of *opt-in* retries vs
Temporal *opt-out*.

### 4.5 Observability

No official OTel saga convention (GenAI `invoke_workflow` is a different
domain — §8). Design rule (Azure/AWS "observability" bullets + W3C Trace
Context on the bus):

| Signal | Why |
|---|---|
| Root `saga.id` / `saga.type` / `saga.outcome` (`completed` \| `compensated` \| `failed` \| `pending`) | Join key across choreography hops. |
| Per-step span (`name`, `number`, `status`) + compensate span (`for_step`) | Azure: correlate original and compensate. |
| Attempt count + reason (`transient` \| `business` \| `timeout-unknown`) | Distinguishes C2 retry from compensate. |
| Semantic-lock age | Deadlock / forgotten TTL. |
| History size (Temporal warn 10 240 / 10 MB; SFN → 25 000) | Quota-kill is a silent death. |
| Outbox lag (B7); compensate DLQ | Never-started / compensate-failed. |

Temporal withholds `ActivityTaskStarted` until the activity completes or
exhausts retries — use Describe for in-flight attempts. SFN: logging +
`TracingEnabled` (AWS sample). Durable: keep `traceInputsAndOutputs`
false on payments.

Alert shapes (this note's, **not** vendor PromQL): `PENDING` > lock TTL;
compensate failure rate; history > 80% of cap; outbox age; orchestrator
`Failed` with no compensate span.

### 4.6 Tuning

| Knob | Too aggressive | Too timid | Starting point (sourced) |
|---|---|---|---|
| Style | Choreography of 8+ (AWS: "harder to track") | Orchestrator for emit-and-forget | Few independent participants → choreography; branching / compensate-heavy → orchestration. |
| Retry vs compensate | Compensate on first timeout | Retry a business reject 100× | Platform → retry; business → compensate; timeout-unknown → retry **with C9 key**, then human/compensate. |
| Step timeout | Start-To-Close ≪ p99 (false timeout → double apply) | Default ∞ / 99 999 999 s (stuck `PENDING`) | Start-To-Close > max body; Schedule-To-Close = step SLA (Temporal: always set Start-To-Close). |
| Retry budget | Unlimited Temporal attempts on a payment | `MaxAttempts = 1` on a flaky RPC | Temporal: cap with Schedule-To-Close; SFN default 3 + Catch; mark business errors non-retryable. |
| Pivot | Charge first | Forever-compensatable "maybe" charge | First irreversible step, after validations (Azure). |
| Semantic-lock TTL | None (deadlock) | TTL ≪ remaining p99 | ≥ remaining downstream Schedule-To-Close + compensate budget. |
| History | One workflow, a year of retries | Continue-As-New every step | Stay under Temporal warn (10 240 / 10 MB) or SFN 25 000. |

### 4.7 Worked calibration — `CreateOrder`

Design drill (not a vendor SLA): Richardson Customers & Orders + AWS PG
three-participant diagram. 200 orders/s peak; credit p99 200 ms;
inventory p99 80 ms; capture p99 1.2 s / p99.9 8 s; must roll back if
capture fails; notifications are *not* atomic.

| Step | Choice | Why |
|---|---|---|
| Start | `POST /orders` → 202 + `orderId`; Order `PENDING` + outbox `ReserveCredit` in **one** TX (B7) | Richardson option 2; dual-write closed. |
| Style | Orchestrate credit → inventory → capture; choreograph email after `OrderApproved` | ch08.md hybrid. |
| Engine | SFN Standard *or* Temporal (not Express: 5 min + at-least-once) | |
| T1 `ReserveCredit` | Compensatable; key `saga:{id}:credit`; Start-To-Close 2 s; Schedule-To-Close 15 s; `CreditLimitExceeded` **non-retryable** | `Ci` = commutative `+N`. |
| T2 `ReserveInventory` | Compensatable; key `saga:{id}:inv`; Start-To-Close 1 s; Schedule-To-Close 10 s; `OutOfStock` non-retryable; SKU `PENDING` reservation row | Prevents oversell (semantic lock). |
| T3 `CapturePayment` | **Pivot**; key `saga:{id}:pay` (C9, reused); Start-To-Close 15 s; Schedule-To-Close 60 s; heartbeat 10 s if 3-D Secure; SFN-like 3 attempts | Timeout-unknown = double-charge case. Success → refund is a *new* saga, not `C3`. |
| T4 `ApproveOrder` | Retryable (`PENDING` → `APPROVED`) | Releases the lock. |
| T3 business fail | Compensate T2 then T1 (Azure allows parallel); order `REJECTED` | Commutative credit/inventory tolerate either order. |
| T3 timeout-unknown | Retry T3 with the **same** key; if Schedule-To-Close expires → **human** | Do not auto-compensate a maybe-captured charge. |
| Client | Poll `GET /orders/{id}` | Do not hold HTTP for capture p99.9. |
| Out of saga | Email, loyalty, search | Losing them must not compensate the capture. |

---

## 5. Failure modes and when-not-to-use

**Failure modes**

- Forgotten / failed compensate (Azure: "might not always succeed") — journal + DLQ + human.
- Snapshot-restore compensate clobbers concurrent work (García-Molina airline).
- Dirty read: another saga shipped against a `PENDING` reservation later compensated.
- Lost update on compensate: two sagas `+credit` via read-modify-write instead of commutative `+N`.
- Semantic lock without TTL → stuck `PENDING`.
- Dual-write start → zombie `PENDING` (**B7**).
- Retry of a non-idempotent pivot → double capture (**C9**).
- Retry of a business reject → credit-limit storm (C2 classification).
- Timeout-unknown auto-compensate → refund of nothing, or captured charge without an order.
- History-quota kill (Temporal 51 200 / 50 MB; SFN 25 000) mid-compensate.
- Orchestrator SPOF / SFN unspecified Task timeout waits forever.
- Choreography cycles / no global timeout (AWS).
- Replay non-determinism / version skew ([durable-workflows.md](../../../cases/data-intensive-design/durable-workflows.md)).
- Untested compensate path = modal fallback (C1 research / Gabrielson).

**When not to use (sourced)**

| Situation | Source | Prefer |
|---|---|---|
| One DB already owns the rows | Richardson force is Database-per-Service | Local ACID. |
| Tight coupling / cyclic deps | Azure Saga "might not be suitable" | Collapse services, or orchestrate *and* break the cycle. |
| Cannot tolerate intermediate reads | Azure Compensating Transaction; AWS eventual-consistency warning | Single-node TX or *internal* 2PC — not XA. |
| Retries alone suffice | Azure Compensating Transaction | C2 only. |
| Compensate cannot restore a valid state | Azure Compensating Transaction | Don't start the irreversible step until you can finish. |
| High-risk funds on one ledger | Richardson 2017 "by value" | Internal 2PC or one service. |
| Must answer every POST synchronously | Richardson option 1 "reduced availability" | 202 + poll, or keep work in one service. |

Azure's third "not suitable" bullet ("Compensating transactions occur in
earlier participants") is opaque — §8.

---

## 6. Cross-links

- **Catalog:** B5 in
  [system-design-patterns-catalog.md](system-design-patterns-catalog.md).
- **Siblings:** B7 outbox; C9 keys; C2 + C7 hop policy; C1 breaker; E12 /
  E4 styles; A2 bus; B4 dual-write
  ([b4-strangler-fig-external-research.md](b4-strangler-fig-external-research.md)).
- **Existing notes:** [aws/ch08.md](../../../cases/aws/ch08.md) ·
  [distributed-transactions.md](../../../cases/data-intensive-design/distributed-transactions.md)
  · [durable-workflows.md](../../../cases/data-intensive-design/durable-workflows.md)
  · [lost-updates.md](../../../cases/data-intensive-design/lost-updates.md)
  · [event-driven-dataflow.md](../../../cases/data-intensive-design/event-driven-dataflow.md)
  · [event-sourcing-cqrs.md](../../../cases/data-intensive-design/event-sourcing-cqrs.md).
- **Depth-bar examples:**
  [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md),
  [RetryBackoff.md](../../../cases/SystemDesignPatterns/RetryBackoff.md).

---

## 7. Sources

Retrieved 2026-09-13.

**Canon.** cornell.edu `sagas.pdf` (García-Molina & Salem 1987) ·
dl.acm.org/doi/10.1145/38713.38742 · microservices.io/patterns/data/saga.html
· microservices.io/post/sagas/2019/08/04/developing-sagas-part-2.html ·
…/2019/08/15/developing-sagas-part-3.html · qconsf.com 2017 slides (above)
· infoq.com/news/2018/02/data-consistency-microservices ·
learn.microsoft.com/en-us/azure/architecture/patterns/{saga,compensating-transaction,choreography}
· github.com/MicrosoftDocs/architecture-center `docs/patterns/saga.yml`
(`ms.date` 2025-02-25) ·
docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/{saga-patterns,saga-choreography,saga-orchestration}.html
· aws.amazon.com/blogs/compute/building-a-serverless-distributed-application-using-a-saga-orchestration-pattern
· github.com/aws-samples/saga-orchestration-netcore-blog

**Outbox as start.** microservices.io/patterns/data/transactional-outbox.html
· github.com/eventuate-tram/{eventuate-tram-core,eventuate-tram-sagas}

**Engines.** docs.temporal.io/encyclopedia/{retry-policies,detecting-activity-failures}
· docs.temporal.io/{workflow-execution/event,workflow-execution/continue-as-new,cloud/limits,troubleshooting/blob-size-limit-error}
· github.com/temporalio/temporal/releases/tag/v1.31.2 · javadoc.io
`io.temporal/temporal-sdk/1.31.0` ·
docs.aws.amazon.com/step-functions/latest/dg/{concepts-error-handling,state-task,service-quotas,sfn-best-practices}.html
· learn.microsoft.com/en-us/azure/durable-task/{common/durable-task-error-handling,durable-functions/durable-functions-host-json-settings}
· learn.microsoft.com/en-us/azure/azure-functions/{functions-scale,functions-host-json}
· cadenceworkflow.io/docs/java-client/retries · javadoc.io
`com.uber.cadence/cadence-client/4.0.0` · github.com/uber/cadence-java-client
`RetryOptions.java` / `ActivityOptions.java`

**Workspace.** cases/aws/ch08.md ·
cases/data-intensive-design/{distributed-transactions,durable-workflows,lost-updates}.md
· docs/research/sysdesign/system-design-patterns-catalog.md

---

## 8. Uncertain / left out (excluded from the Concept)

- **Richardson *Microservices Patterns* ch. 4 §4.3 body** — not fetched.
  Anomaly names + six countermeasures from Azure + 2017 QCon PDF. No page
  numbers.
- ACM DOI twin `10.1145/38714.38742` (Record) vs `10.1145/38713.38742`
  (proceedings). Cornell PDF is the text used. Printed pages 249–259
  inferred from the ISBN fragment, not re-checked against a publisher ToC.
- Azure "not suitable: Compensating transactions occur in earlier
  participants" — wording unclear; do not invent a meaning.
- Azure Learn HTML hid `ms.date`; **2025-02-25** is GitHub `saga.yml`.
  Compensating Transaction `ms.date` not captured.
- Azure "pivot = last compensable **or** first retryable" — treat as the
  two legal placements the 2017 slides already allow, not as Azure
  forbidding one of them.
- Temporal Java SDK **1.31.0** vs server **v1.31.2** (2026-07-08) — retry
  numbers agree; not one product release.
- Durable Functions JSON *example* shows orchestrator concurrency 10 and
  Event Grid publish retry 3; the **defaults table** says Consumption
  orchestrator **5** and Event Grid retry **0**. Use the table.
- host.json `orchestrationTimeout` on Q&A / SO is **not** on the official
  settings page — do not assert it.
- Cadence `cadence-client` 4.0.0 release *day* not fetched; defaults from
  4.0.0 javadoc + current `RetryOptions` source.
- Eventuate CDC env-var sample — B7 territory.
- §4.5 OTel attributes are this note's design rule. GenAI
  `invoke_workflow` (semantic-conventions PR 3249) is unrelated.
- PromQL recipes — none found; alert shapes are this note's.
- Camunda / Zeebe / Restate / Orkes / Conductor — not fetched as numeric
  sources.
- Course-dump JS / class diagrams — none in this tree for B5.
