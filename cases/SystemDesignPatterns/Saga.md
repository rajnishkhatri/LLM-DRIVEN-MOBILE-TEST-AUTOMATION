---
type: reference
title: 'Saga'
description: 'A long-running business transaction as local commits plus compensating undos, coordinated by choreography or orchestration. ACD, not ACID: the execution log is the atomicity mechanism. Complements retries and idempotency keys; cites 2PC and durable-workflow replay instead of rewriting them.'
tags: [system-design-patterns, consistency, saga]
---

# Saga

**See also:** [retry, backoff, and retry budgets](RetryBackoff.md) · [idempotency](Idempotency.md) · [timeouts](TimeoutsDeadlines.md) · [circuit breaker](CircuitBreaker.md) · [distributed transactions (2PC / XA)](../data-intensive-design/distributed-transactions.md) · [durable workflows](../data-intensive-design/durable-workflows.md) · [lost updates](../data-intensive-design/lost-updates.md) · [read committed](../data-intensive-design/read-committed.md) · [event sourcing and CQRS (E12, later)](../data-intensive-design/event-sourcing-cqrs.md) · [choreography vs orchestration](../aws/ch08.md) · [pub/sub and queues](PubSubQueues.md) · [catalog of record](../../docs/research/sysdesign/system-design-patterns-catalog.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/b5-saga-external-research.md)

The Saga pattern is a **long-running business transaction** that spans services without a distributed lock. Each step `Ti` is a real local commit in its own database (or at a third-party API). The guarantee is either `T1,…,Tn` **or** `T1,…,Tj, Cj,…,C1`. `Ci` is a **semantic undo** of `Ti` — not a restore of the bytes that existed when `Ti` began, because other work may have run in between.

A checkout that reserves credit, reserves inventory, and captures a card cannot sit in [two-phase commit](../data-intensive-design/distributed-transactions.md): there is no prepare-phase lock across those systems, and a card gateway will not join XA. The saga reconstructs *business* atomicity from already-committed locals. **Business** failure compensates completed steps. **Transient / platform** failure retries the current step. That is **ACD** (Richardson), not ACID — the missing letter is isolation.

Quality attributes in play: **consistency** (eventual, across service boundaries), **availability** of the participants (locks drop at each local commit), and **recoverability** of the business operation. The costs are an isolation hole the size of the whole saga, a compensate path that is rarely exercised, and a new durability requirement: the **execution log** is the atomicity mechanism. Forget "we already reserved inventory" and you double-reserve or skip compensate.

Outbox / CDC (catalog **B7**, later) is how the first local write *starts* the saga. This card owns the sequence, the undos, and the log.

## Lineage and vocabulary

- **García-Molina & Salem, *Sagas*, SIGMOD 1987.** A long-lived transaction that holds locks for hours or days blocks shorter work and raises deadlock and abort rates. Split it into real local transactions that **may interleave**. `Ci` decrements a reserved seat; it must **not** write back the old count. There is **no notify/abort** of transactions that already saw `Ti`. That is the isolation hole.
- **Richardson, *Pattern: Saga*** (microservices.io) and the 2017 QCon model. Database-per-Service transactions become local commits plus messages. **Choreography** = participants exchange domain events. **Orchestration** = a persistent orchestrator sends commands and processes replies. No automatic rollback; the model is **ACD**. Steps are **compensatable → pivot → retryable**. Each step must atomically update its DB and publish (outbox, or an event-sourced log — [E12](../data-intensive-design/event-sourcing-cqrs.md), later).
- **Azure Architecture Center *Saga*** (`ms.date` 2025-02-25) plus *Compensating Transaction*. Same two styles; same three anomalies and six countermeasures; compensations are application-specific, eventually consistent, resumable, and idempotent. Retry transients **before** compensating. Prefer an alternative path (another hotel) over cancelling; pause for a human on high-impact choices.
- **AWS Prescriptive Guidance.** *Continuation* (retry / forward) on platform failure; *compensation* (backward) on application failure. Choreography names the **dual-write** hole and the outbox as the fix. Orchestration is the Step Functions sample: order → inventory → payment with reverse `Revert*` actions.
- **Workspace (cite, do not rewrite).** [ch08.md](../aws/ch08.md) has the choreography / orchestration / hybrid comparison and a one-paragraph saga. 2PC and XA stay in [distributed-transactions.md](../data-intensive-design/distributed-transactions.md). Engine history, replay, and versioning stay in [durable-workflows.md](../data-intensive-design/durable-workflows.md).

## Variants

| Variant | Who decides next | Trade-off |
|---|---|---|
| **Choreography** | Each participant, by publishing a domain event | No orchestrator SPOF; cyclic dependencies; scattered logic; AWS: timeouts and retries "must be implemented on individual components"; no *global* timeout. |
| **Orchestration** | Persistent orchestrator / state machine | Central compensate, timeout, retry; SPOF unless the *engine* is HA. |
| **Hybrid** ([ch08.md](../aws/ch08.md)) | Orchestrate the core; choreograph side effects | Clear compensate ownership on pay / reserve / ship; overlapping-responsibility risk on notifications. |
| **Durable-execution engine** ([durable-workflows.md](../data-intensive-design/durable-workflows.md)) | Workflow definition; history is the log | Replay is "exactly-once *workflow*" only if callees are idempotent ([C9](Idempotency.md)). |

A choreographed *start* (outbox event) can create an orchestrated saga. Domain rules do not belong on the bus.

## Compensating transactions

García-Molina: semantic undo. Azure: you cannot "restore original state" if concurrent work moved the data; apply **business rules** (partial refund, not a snapshot restore). Compensations need **not** run in exact reverse — undo the most inconsistency-sensitive store first; some undos can run in parallel. A `Ci` **can fail**: journal it, resume it, make every `Ci` idempotent; the human path is first-class.

**Retry before compensate** (Azure; AWS continuation). Do not compensate a timeout on first sight. Prefer an alternative path over cancelling.

**Pivot** (Azure + Richardson 2017). After the pivot succeeds, compensable steps are no longer the recovery path. Later steps are **retryable** and must eventually succeed. Place irreversible or legally binding work (card capture, regulatory file) at or after the pivot.

```
compensatable T1…Tk   →   pivot Tk+1   →   retryable Tk+2…Tn
     Ck…C1 on fail          fail → Ck…C1     fail → retry until done
```

A successful capture that later needs a refund is a **new** saga, not `C_capture`.

## Isolation across steps

Locks drop at each local commit. The window is the *whole saga*, not a single statement — the row-grain versions live in [lost-updates.md](../data-intensive-design/lost-updates.md) and [read-committed.md](../data-intensive-design/read-committed.md). Azure and the 2017 slides name three anomalies:

| Anomaly | Across-step shape |
|---|---|
| **Lost update** | Saga A writes; B writes the same row without reading A; A's later `Tj` or `Ci` clobbers B. |
| **Dirty read** | B reads a value A wrote in a compensatable step; A then compensates. |
| **Fuzzy / nonrepeatable read** | Two steps of the *same* saga read one key and get different results because another saga wrote between them. |

**Countermeasures** (Azure; same six on the 2017 slides):

1. **Semantic lock.** A compensatable step sets `PENDING` / a flag; others must not treat the row as committed (Richardson `Create Order`: `cancelOrder` only if `APPROVED`). Application-level. Needs a **timeout** or it deadlocks. AWS PG independently recommends it.
2. **Commutative updates.** Debit/credit so compensate is `+N` after `-N`.
3. **Pessimistic view.** Reorder so the risky write is retryable (never compensated).
4. **Reread values.** Before a later write, re-read; abort or restart if changed.
5. **Version files.** Append-only ops so create-then-cancel equals cancel-then-create (the 2017 slides note this "sounds like event sourcing" — [E12](../data-intensive-design/event-sourcing-cqrs.md), not this card).
6. **Risk-based concurrency.** Low-risk → saga; high-risk funds on one ledger → one DB or *database-internal* 2PC, not XA ([distributed-transactions.md](../data-intensive-design/distributed-transactions.md)).

## Execution log

The log *is* atomicity. Three durable shapes; pick one and do not dual-write around it.

| Approach | What is durable | If missing |
|---|---|---|
| **Outbox / CDC (B7, later)** | Local write + next message in **one** commit; a relay publishes | Crash between `COMMIT` and `producer.send` → saga never starts, or starts twice. |
| **Orchestrator journal** | Each forward step **and** its compensate (Azure's Cosmos example) | Crash after `Ti` commits, before the journal → `Ti` is invisible to compensate (**orphan `Ti`**). |
| **Engine history** | Temporal Event History / Step Functions execution history / Durable History table; replay skips completed RPCs | History-quota kill; non-deterministic workflow code; version skew — [durable-workflows.md](../data-intensive-design/durable-workflows.md). |

**Engine caps (dated examples, fetched 2026-09-13), not a vendor how-to.** Temporal Cloud + self-hosted defaults (server **v1.31.2**, 2026-07-08): **51 200 events or 50 MB** (warn 10 240 / 10 MB); payload **2 MB**; history txn **4 MB**; gRPC **4 MB**; no workflow time cap — escape with Continue-As-New. Step Functions **Standard**: **25 000** events (event 25 000 must be `ExecutionSucceeded` or the execution fails); **1 year**; history **90 days**; I/O **256 KiB**; 1 000 000 open executions / account / Region. **Express** is **5 min**, unlimited history, **at-least-once** — wrong for capture. Azure Durable Functions: `maxOrchestrationActions` **100 000** / cycle; Consumption activity `functionTimeout` **5 / 10** min; Flex / Premium / Dedicated **30** min default, unbounded max; HTTP trigger still **230 s** load-balancer idle.

Version in-flight definitions like an encoding. Replay still needs idempotent callees and deterministic workflow code.

## Timeout, retry, and the compensate branch

[C2](RetryBackoff.md) owns whether and how to retry a hop; [C7](TimeoutsDeadlines.md) owns how long and the remaining deadline; [C9](Idempotency.md) owns the key store. This card owns the **branch**:

1. **Transient / platform** (timeout, 502 / 503, worker crash) → retry the *same* step under the remaining saga deadline. Do **not** compensate yet.
2. **Business reject** (no credit, bad card, out of stock) → do not retry unchanged; compensate preceding compensatable steps, or take an alternative path.
3. **Timeout-unknown** (a capture whose 200 was lost) → "maybe succeeded." Safe only with a **C9 key** minted once per `(saga-id, step)` and reused on retry *and* compensate. Compensating a never-applied capture is a documented no-op; retrying an applied capture must not double-charge.
4. **Open circuit ([C1](CircuitBreaker.md))** → fail fast into the saga decision. Do not retry Open.
5. **Stacked retries** — orchestrator + SDK + broker redelivery is three layers. One retry owner per hop (usually the orchestrator / activity policy); callee fail-fast.

Choreography has no global timeout (AWS). A missing hop timeout leaves the saga `PENDING` and the **semantic lock never releases**.

## Configuration

There is no Resilience4j of sagas. These are **engine** defaults for the orchestrator variant (fetched 2026-09-13). Choreography inherits the [broker](PubSubQueues.md).

| Engine | Retry default | Timeouts | Saga reading |
|---|---|---|---|
| **Temporal** Activity Retry (server v1.31.2; Java SDK 1.31.0 agrees) | **On** (workflow retries **off**). `InitialInterval` **1 s**, `BackoffCoefficient` **2.0**, `MaximumInterval` **100 × Initial**, `MaximumAttempts` **0 = unlimited**, `NonRetryableErrorTypes` `[]` | `ScheduleToClose` **∞**; `StartToClose` inherits it if unset; `ScheduleToStart` **∞** and **non-retryable**. Heartbeat throttle `min(heartbeatTimeout × 0.8, max)`, default interval **30 s**, max **60 s**. Workflow execution timeout **unlimited** — history size is the real cap | Retry the *step*, not the saga. Bound unlimited attempts with `ScheduleToClose` or a business error retries forever. Put business rejects in `NonRetryableErrorTypes` so they fail into compensate. **Always set `StartToClose`** — the server detects worker crash only via it. Disable retries: `MaximumAttempts = 1`. |
| **Step Functions** Task + Retry | Unhandled error **fails the execution**. `Retry.IntervalSeconds` **1**, `MaxAttempts` **3**, `BackoffRate` **2.0**, `MaxDelaySeconds` unset = **no cap**, `JitterStrategy` **`NONE`** (`FULL` = `random(0, interval)`) | `TimeoutSeconds` / `HeartbeatSeconds` **99 999 999**. Unspecified Task **waits forever**. HTTP Task hard-cap **60 s** | `Catch` onto compensate. Mark business `ERROR` non-retryable so it can branch to `Revert*`. Turn `FULL` jitter on for a fleet of sagas ([C2](RetryBackoff.md)). Capture + compensate → **Standard**, not Express. Store ids, not cart blobs (256 KiB). Retries are billed state transitions; Redrive resets the counter (14-day Standard window). |
| **Azure Durable Functions** | **None** unless you pass `RetryPolicy`. Policy: you set max attempts (**1** = no retries); first interval required; backoff coefficient **1** (no growth); retry timeout **indefinite** | Consumption activity **5 / 10** min; Flex / Premium / Dedicated **30** min default. `maxConcurrentActivityFunctions` Consumption **10**, Dedicated / Premium **10 × processors**; `maxConcurrentOrchestratorFunctions` Consumption **5**, Dedicated / Premium **10 × processors**. Control / work-item visibility timeout **00:05:00**; `partitionCount` **4** (change = new hub) | Unhandled orchestrator exception → instance **`Failed`** and **cannot be retried** — compensate *inside* try / catch first. Long captures belong on Flex / Premium or webhook + external event. Keep `traceInputsAndOutputs` **false** on payments. |
| **Cadence** Java client 4.0.0 | `setRetryOptions` default **null = no retries**. `BackoffCoefficient` **2.0**; `MaximumInterval` **100 × Initial**; either `ExpirationInterval` or `MaximumAttempts` required (`0` = unlimited) | `ScheduleToClose` **or** both `ScheduleToStart` + `StartToClose`; all capped by workflow timeout | Temporal's predecessor: *opt-in* retries vs Temporal *opt-out*. Dated example, not a recommendation. |

## Observability

A saga without a join key is an un-debuggable distributed transaction. There is no official OpenTelemetry saga convention; treat the following as a design rule (Azure / AWS observability bullets + W3C Trace Context on the bus), not a vendor schema.

| Signal | What it tells you |
|---|---|
| Root `saga.id` / `saga.type` / `saga.outcome` (`completed` \| `compensated` \| `failed` \| `pending`) | Join key across choreography hops. |
| Per-step span (`name`, `number`, `status`) + compensate span (`for_step`) | Azure: correlate the original and the undo. |
| Attempt count + reason (`transient` \| `business` \| `timeout-unknown`) | Distinguishes a [C2](RetryBackoff.md) retry from compensate. |
| Semantic-lock age | Deadlock or a forgotten TTL. |
| History size (Temporal warn 10 240 / 10 MB; SFN → 25 000) | Quota-kill is a silent death. |
| Outbox lag (B7); compensate DLQ | Never-started saga, or compensate that failed. |

Temporal withholds `ActivityTaskStarted` until the activity completes or exhausts retries — use Describe for in-flight attempts. Step Functions: logging + `TracingEnabled` (AWS sample). Alert shapes (this note's, **not** vendor PromQL): `PENDING` longer than the lock TTL; compensate failure rate; history past 80% of cap; outbox age; orchestrator `Failed` with no compensate span.

## Tuning

| Knob | Too aggressive | Too timid | Starting point (sourced) |
|---|---|---|---|
| Style | Choreography of 8+ (AWS: "harder to track") | Orchestrator for emit-and-forget | Few independent participants → choreography; branching / compensate-heavy → orchestration. |
| Retry vs compensate | Compensate on first timeout | Retry a business reject 100× | Platform → retry; business → compensate; timeout-unknown → retry **with a C9 key**, then human / compensate. |
| Step timeout | Start-To-Close ≪ p99 (false timeout → double apply) | Default ∞ / 99 999 999 s (stuck `PENDING`) | Start-To-Close > max body; Schedule-To-Close = the step budget (Temporal: always set Start-To-Close). |
| Retry budget | Unlimited Temporal attempts on a payment | `MaxAttempts = 1` on a flaky RPC | Temporal: cap with Schedule-To-Close; SFN default 3 + Catch; mark business errors non-retryable. |
| Pivot | Charge first | Forever-compensatable "maybe" charge | First irreversible step, after validations (Azure). |
| Semantic-lock TTL | None (deadlock) | TTL ≪ remaining p99 | ≥ remaining downstream Schedule-To-Close + compensate budget. |
| History | One workflow, a year of retries | Continue-As-New every step | Stay under Temporal warn (10 240 / 10 MB) or SFN 25 000. |

## Where it lives

| Layer | Coordinates | Compensate / rollback |
|---|---|---|
| HTTP edge | Accept command; 202 + saga id (Richardson option 2) | Client polls; no 2PC. |
| Outbox in the first service (B7, later) | Durable *start* | Relay; at-least-once to the bus or orchestrator. |
| Choreography bus ([A2](PubSubQueues.md)) | Next `Ti` / `Ci` | Compensation events; DLQ → human (Azure Choreography). |
| Orchestrator / engine | Sequence, timeouts, retries, reverse `Ci` | Catch → compensate; journal / history is SoT. |
| Participant | Local ACID + idempotent handler | Semantic lock; local `Ci`. |

## Worked calibration — `CreateOrder`

Design drill (not a vendor SLA): Richardson Customers & Orders + the AWS PG three-participant diagram. 200 orders/s peak; credit p99 200 ms; inventory p99 80 ms; capture p99 1.2 s / p99.9 8 s; must roll back if capture fails; notifications are *not* atomic.

| Step | Choice | Why |
|---|---|---|
| Start | `POST /orders` → 202 + `orderId`; Order `PENDING` + outbox `ReserveCredit` in **one** TX (B7) | Richardson option 2; dual-write closed. |
| Style | Orchestrate credit → inventory → capture; choreograph email after `OrderApproved` | [ch08.md](../aws/ch08.md) hybrid. |
| Engine | SFN Standard *or* Temporal — not Express (5 min + at-least-once) | Capture must be exactly-once *workflow*. |
| T1 `ReserveCredit` | Compensatable; key `saga:{id}:credit`; Start-To-Close 2 s; Schedule-To-Close 15 s; `CreditLimitExceeded` **non-retryable** | `Ci` = commutative `+N`. |
| T2 `ReserveInventory` | Compensatable; key `saga:{id}:inv`; Start-To-Close 1 s; Schedule-To-Close 10 s; `OutOfStock` non-retryable; SKU `PENDING` reservation row | Semantic lock against oversell. |
| T3 `CapturePayment` | **Pivot**; key `saga:{id}:pay` ([C9](Idempotency.md), reused); Start-To-Close 15 s; Schedule-To-Close 60 s; heartbeat 10 s if 3-D Secure; SFN-like 3 attempts | Timeout-unknown is the double-charge case. Success → refund is a *new* saga, not `C3`. |
| T4 `ApproveOrder` | Retryable (`PENDING` → `APPROVED`) | Releases the lock. |
| T3 business fail | Compensate T2 then T1 (Azure allows parallel); order `REJECTED` | Commutative credit / inventory tolerate either order. |
| T3 timeout-unknown | Retry T3 with the **same** key; if Schedule-To-Close expires → **human** | Do not auto-compensate a maybe-captured charge. |
| Client | Poll `GET /orders/{id}` | Do not hold HTTP for capture p99.9. |
| Out of saga | Email, loyalty, search | Losing them must not compensate the capture. |

## Failure modes of the saga itself

- **Orphan compensations.** Two directions. **Orphan `Ci`:** timeout-unknown auto-compensate refunds a charge that never applied, or a `Ci` runs because the log thought `Ti` happened. **Orphan `Ti`:** `Ti` committed, the journal / outbox did not — compensate cannot see it, so inventory stays reserved and the order looks `PENDING`. The log *and* the C9 no-op contract are the fix; "compensate on any timeout" is how you mint orphans.
- **Semantic lock without a TTL.** Stuck `PENDING`; the reservation never releases; later sagas dirty-read it or deadlock waiting for it. The 2017 slides already name timeout as the deadlock detector.
- **Forgotten / failed compensate** (Azure: "might not always succeed") — journal + DLQ + human. An untested compensate path is a modal fallback, the same class of risk the [breaker](CircuitBreaker.md) research cites.
- **Snapshot-restore compensate** clobbers concurrent work (García-Molina airline: write back the old seat count).
- **Dirty read:** another saga shipped against a `PENDING` reservation that was later compensated.
- **Lost update on compensate:** two sagas `+credit` via read-modify-write instead of commutative `+N`.
- **Dual-write start** → zombie `PENDING` (B7).
- **Retry of a non-idempotent pivot** → double capture ([C9](Idempotency.md)).
- **Retry of a business reject** → credit-limit storm ([C2](RetryBackoff.md) classification).
- **History-quota kill** (Temporal 51 200 / 50 MB; SFN 25 000) mid-compensate.
- **Orchestrator SPOF** / SFN unspecified Task timeout waits forever.
- **Choreography cycles** / no global timeout (AWS).
- **Replay non-determinism / version skew** — [durable-workflows.md](../data-intensive-design/durable-workflows.md).

## When not to use

| Situation | Source | Prefer |
|---|---|---|
| One DB already owns the rows | Richardson: the force is Database-per-Service | Local ACID. |
| Tight coupling / cyclic dependencies | Azure Saga "might not be suitable" | Collapse services, or orchestrate *and* break the cycle. |
| Cannot tolerate intermediate reads | Azure Compensating Transaction; AWS eventual-consistency warning | Single-node TX or *internal* 2PC — not XA. |
| Retries alone suffice | Azure Compensating Transaction | [C2](RetryBackoff.md) only. |
| Compensate cannot restore a valid state | Azure Compensating Transaction | Don't start the irreversible step until you can finish. |
| High-risk funds on one ledger | Richardson 2017 "by value" | Internal 2PC or one service. |
| Must answer every POST synchronously | Richardson option 1 "reduced availability" | 202 + poll, or keep the work in one service. |

## Trade-offs

| Buy | Pay |
|---|---|
| Business atomicity across services without XA | ACD, not ACID — dirty reads and lost updates across the saga window |
| Availability: locks drop at each local commit | Semantic locks, commutative updates, and a lock TTL you have to operate |
| Choreography: no orchestrator SPOF | Scattered compensate; no global timeout; cycles |
| Orchestration / durable engine: central Catch → `Ci` | Engine HA, history caps, replay determinism, versioning |
| Continuation on platform failure, compensate on business failure | Timeout-unknown is neither; a C9 key and a human path are mandatory on the pivot |
| Explicit degraded path (alternative hotel, enqueue, human) | Compensate is a rarely exercised mode; orphans if the log lags the commit |

The saga decides **whether the business operation still holds**. [Retries](RetryBackoff.md) decide **whether to try the current step again**. [Timeouts](TimeoutsDeadlines.md) decide **how long that step may run**. [Idempotency keys](Idempotency.md) decide **whether trying again is safe**. The [breaker](CircuitBreaker.md) decides **whether to call that hop at all**. Coordinate all four; do not treat the saga as a complete consistency strategy.

## Sources

Verified 2026-09-13; the full URL list, per-claim provenance, and items deliberately left out are in the [external research note](../../docs/research/sysdesign/b5-saga-external-research.md). 2PC / XA and exactly-once inboxes stay in [distributed-transactions.md](../data-intensive-design/distributed-transactions.md); replay and versioning stay in [durable-workflows.md](../data-intensive-design/durable-workflows.md).

- Canon: García-Molina & Salem, *Sagas* (SIGMOD 1987); Richardson, *Pattern: Saga* and the 2017 QCon ACD / pivot slides; Azure *Saga*, *Compensating Transaction*, and *Choreography*; AWS Prescriptive Guidance saga overview / choreography / orchestration.
- Engines (dated examples): Temporal retry policies, event-history and Cloud limits (server v1.31.2); Step Functions error handling, Task timeouts, and service quotas; Azure Durable Task error handling, `host.json` `durableTask` defaults, and Functions scale; Cadence Java client 4.0.0 `RetryOptions`.
- Workspace: [aws/ch08.md](../aws/ch08.md); [distributed-transactions.md](../data-intensive-design/distributed-transactions.md); [durable-workflows.md](../data-intensive-design/durable-workflows.md); [lost-updates.md](../data-intensive-design/lost-updates.md).
