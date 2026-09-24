# Resilience clinic — claim document processor

Clinic loop for the Bedrock/S3 path. Cards cited by id. **Recommend, then
the operator decides.** Confirming metrics are named *before* knobs.

**Symptom (anticipated, not yet measured):** a slow or throttled Bedrock
call hangs the CLI; a naive retry loop turns a regional blip into a token
storm; a retried summarize double-writes a result; a dead policy KB
either 500s the whole claim or silently hallucinates coverage.

---

## 1. Diagnose → candidates

| Failure | Card |
|---|---|
| Hung Converse / no bound | **TimeoutsDeadlines (C7)** |
| `ThrottlingException` / blip | **RetryBackoff (C2)** |
| Retry of Record after a timeout | **Idempotency (C9)** |
| Policy retrieve down, extract already succeeded | **GracefulDegradation (C11)** |
| Storm of claims, Bedrock TPM exceeded | **LoadShedding (C10)** — production queue |
| Bedrock error rate high, retries still firing | **CircuitBreaker (C1)** — only after a metric exists |
| Extract vs summary sharing one thread pool under load | **Bulkhead (C8)** — production concurrency |

Style (monolith vs queue) is **not** this clinic — see
`../worksheets/style-decision.md`.

---

## 2. Confirm the metric first

Do **not** drop a breaker on Bedrock because "LLMs fail." Measure:

- Raw Bedrock error rate split by code (`ThrottlingException` vs 4xx vs
  timeout).
- p50 / p99 / p99.9 of Converse (extract vs summary separately).
- Duplicate result objects per `s3_key` (C9).
- Fraction of summaries with `ungrounded=true` (C11).

A breaker whose "failures" are actually **slow successes** converts a
slowdown into an outage (C1 doctrine). For the PoC, the only honest
metrics are the Stubber-injected cases + wall time of compare_models.

---

## 3. Select the combination (control loop)

PoC pack: **C7 + C2 (SDK layer only) + C9 + C11**.

- C7 defines failure-fast so C2 has something to retry.
- C2: botocore `retries.mode=adaptive`, `max_attempts=5`. **No**
  application `for model in models: retry` around that — nested retries
  are the 243× amplification story.
- C9: result key = `results/{claim_key}.json`; put is overwrite of the
  same object (naturally idempotent for this PoC). Production: include
  template version in the key or a condition.
- C11: RAG is **soft** — extract still records; summary either cites or
  is flagged. S3 is **hard** — no packet, no claim.
- C1 / C8 / C10: named, **not applied** until the metrics above exist
  (PoC volume cannot fill a breaker window honestly).

---

## 4. Apply knobs (defaults, not policy)

| Card | Starting knobs | Bound to this kata |
|---|---|---|
| C7 | connect 10s, read 300s on Bedrock; connect 10s, read 60s on S3 | Batch docs; 300s is the streaming/agent floor from boto3-foundations — extract of a short text claim should finish far sooner; **recalibrate from p99.9 once measured** |
| C2 | adaptive, max_attempts 5; honour `Retry-After`; do not retry 4xx / `AccessDenied` | One layer = the SDK |
| C9 | one key per `bucket/key` | Re-running the CLI replaces the result, does not append |
| C11 | omit policy grounding; never fabricate a coverage decision | Core function = **durable extraction**; summary is additive |

---

## 5. Verify (fitness)

| Card | Metric → assertion |
|---|---|
| C7 | Stubber hang is not possible in unit tests; Config carries connect/read timeouts — assert on the client Config |
| C2 | Inject `ThrottlingException` then success; exactly one app-level call, SDK retries internally; no second nested loop |
| C9 | Process the same key twice → one result object |
| C11 | Empty retrieve → `ungrounded=true`, extraction still present |
| C1 | Not in PoC; production: trip rate vs raw error rate dashboard |

Regression: removing timeouts or adding `for _ in range(3): converse()`
around the SDK fails the C2 assertion.

---

## v2 addendum — intake plane clinic (2026-09-23)

Consistency pass 2026-09-23: folds the ratified amendments (M1–M10, M12–M18), H-F14-a and R8c-a — see `../design/hld-v2-fold-map.md`.

**Mode:** design-review clinic. There is **no incident yet**; the symptoms
below are anticipated. Cards are cited by id. **Recommend, then the
operator decides.** Confirming metrics are named before any knob.
**GATE: RATIFIED 2026-09-23 ("ratify as recommended" — design/hld-v2-data-prep.md §6; was PENDING HUMAN)** (provisional batch, A2-a).
Style and quantum questions are not this clinic (`../worksheets/style-decision.md`
v2).

### 1. Diagnose → candidates

| Anticipated symptom | Failure mechanism | Card |
|---|---|---|
| Glue DQ run or Transcribe job never finishes; the batch hangs | Unbounded wait on async work | **TimeoutsDeadlines C7** (poll budgets + service timeouts + cancel) |
| Textract / Comprehend `ThrottlingException` under Map fan-out, then synchronized retries | Retry storm; lock-step retries across Map iterations | **RetryBackoff C2** (one layer, full jitter, budget) |
| S3 → EventBridge delivers the batch event twice | At-least-once redelivery (EventBridge target retries up to **24 h / 185 attempts** — Idempotency C9 verified table) | **Idempotency C9** (batch lock) |
| The same claim revision starts two v1 decisions | Retry of `StartExecution` | **Idempotency C9** (execution name = key) |
| One dead source (e.g. Textract) sinks the claim or the whole batch | Error propagation through Parallel / Map | **GracefulDegradation C11** (soft sources) + **Bulkhead C8** (per-branch isolation) |
| A broken upstream export floods human review with 200 flagged claims | Demand of bad work over reviewer capacity | **LoadShedding C10** (shed at admission: batch gate, row cap) |
| One slow Transcribe job delays the batch summary | Temporal coupling at the join | **C7** (per-claim budget) + **C8** (Map concurrency so slow claims do not starve others) |
| An intake burst turns into a Bedrock spike in v1 | Load propagated through the async hand-off | **C8** (Map `MaxConcurrency` + intake-Lambda reserved concurrency pace v1 starts); v1's **C1** / C11 already guard Bedrock |
| A failed intake execution leaves the lock held, so the batch can never re-run | Idempotency without a recovery path | **C9** (key lifecycle: failed first attempt → a controlled takeover; the holder is read with `states:DescribeExecution`, M13) |
| A lock write succeeds but its response is lost; the retry hits 412 on its own lock and ends as `duplicate_batch` with no summary | The lock cannot tell its own retry from a duplicate (risk-storm C-6) | **C9** (holder ARN == `$$.Execution.Id` → a self-retry proceeds, M13) |
| The intake execution itself dies (an uncaught `States.Runtime` or `States.DataLimitExceeded`; the inline-Map history limit), so no batch summary is written | The batch's health report is written by the execution it reports on (risk-storm C-7) | **C11** (the M14 watchdog keeps the summary) + **C8** (inline Map ≤ 50 claims, Distributed Map above, M14) |

### 2. Confirm the metric first

Nothing is tuned blind. None of these exist yet; each becomes a named metric
(**spec delta SD-6**, added to the `ClaimProcessor/DataQuality` vocabulary):

| Metric | Why (the decision it gates) |
|---|---|
| `SourceFailed{Source}` / claims (already in spec Y1) | Whether a per-source kill switch or breaker is ever warranted (C1 doctrine: raw failure rate first) |
| **`ClaimSettleMs`** (Map iteration start → dispatch), p50 / p99 / p99.9 | Calibrates per-claim budgets (C7 uses p99.9, not the mean) |
| **`TranscribeJobSeconds`**, **`DQRunSeconds`** | Calibrates the two poll budgets |
| **`RetryAttempts{Step}`** (emitted by the step on SFN retry count, read from `$$.State.RetryCount`) | Confirms that the one-layer rule and the jitter work, and exposes amplification |
| **`DuplicateBatch`**, **`AlreadyStarted`** | Evidence that C9 is exercised, not theoretical |
| **`ConservationGap`** (rows_in − processed − quarantined − claim_failed) | Must be **0**. Any non-zero value is a lost claim. |
| **`BatchFailed{Status}`** (the M14 watchdog: one per intake execution `FAILED` / `TIMED_OUT` / `ABORTED`, with its `batch_failed` summary) | A batch whose own execution died still gets a summary. Read it beside the alarm on intake `ExecutionsFailed` (M14). |
| Service-published throttle metrics (Textract / Comprehend in their `AWS/*` namespaces) | Distinguishes our fan-out from regional pressure **[re-verify metric names per service]** |

Honest PoC position: in the PoC these are **Stubber fault injections** plus
**one smoke run's** numbers. The smoke is too small to calibrate p99.9, so
every knob below stays a default until real volume exists (`needs-input`).

### 3. Select the combination (control loop)

**Intake pack: C7 + C2 (one layer) + C9 + C11 + C8. C10 at admission. C1
named, not applied.**

**C7 — define "done or given up" everywhere, with nested deadlines:**
client read < Lambda timeout < Task `TimeoutSeconds` < poll budget <
execution `TimeoutSeconds`. An inner timer must fire before its outer one,
or the waiter walks away while the worker keeps burning money.
- **Cancel work the waiter will never read:**
  - Glue has `CancelDataQualityRulesetEvaluationRun` (verified in botocore),
    so budget exhaustion cancels the run. The run's own `Timeout` (10 min) is
    aligned to the poll budget.
  - Transcribe has **no stop API** for standard jobs (verified: only
    `Delete*`). On budget exhaustion the job is abandoned; its cost is bounded
    by the ≤ 60 s audio, and the late transcript is ignored.

**C2 — one retry layer, owned by Step Functions:**
- State `Retry` with `JitterStrategy: FULL` and `MaxDelaySeconds` (full
  jitter is the card's default).
- Intake SDK clients use `retries={"mode": "standard", "max_attempts": 1}`, so
  retries do not multiply.
- Why the orchestrator layer: its retries are visible in execution history,
  jittered across Map iterations, and **free while waiting**. SDK backoff
  inside a Lambda bills Lambda-milliseconds for sleeping.
- Trade-off: a transient connection reset now re-runs the whole (idempotent)
  step instead of a ms-level SDK retry. That is accepted at this volume.

**C9 — idempotency keys minted once per business operation:**

| Operation | Key | Mechanism |
|---|---|---|
| Admit a batch | `batch_id` from the object key | `quality/locks/<batch_id>` via `PutObject IfNoneMatch="*"`. The lock body = `{execution_arn, started_at}`. A 412 whose holder ARN == `$$.Execution.Id` is this execution's own retry, so it proceeds (M13). |
| Register the batch partition | the batch partition | `CreatePartition`: `AlreadyExistsException` counts as success (M13) |
| Start the DQ run | `ClientToken = <batch_id>-dq` | Glue idempotency token (verified in the `StartDataQualityRulesetEvaluationRun` shape) |
| Transcribe | `clm-<claim_id>-r<rev>` | `ConflictException` → poll the existing job |
| v1 decision | `claim-<claim_id>-r<rev>` | `ExecutionAlreadyExists` → `already_started` |
| Processed records, bundle, image copies | Deterministic keys | Overwrite = idempotent |
| Feedback metric emission | `quality/feedback/<id>-r<rev>-<stage>` | `IfNoneMatch` on the first write. A 412 on redelivery skips re-emitting `FieldDisagreement`; the record content may still be refreshed. |

- **Recovery path** (key lifecycle): a duplicate reads the lock holder's
  status with `states:DescribeExecution` (granted on intake executions, M13).
  One that finds the holder `FAILED`, `TIMED_OUT` or `ABORTED` may **take
  over**, using `PutObject IfMatch=<lock ETag>` (verified in botocore). Two
  racing takeovers cannot both win. A holder that is `RUNNING` or `SUCCEEDED`
  ends the duplicate, unless the holder is the execution itself (M13
  self-retry, above).
- **Dedup-window rule** (C9): the lock retention (S3, no expiry) outlives
  EventBridge's 24 h redelivery.

**C11 — name the core function: "every admitted row reaches exactly one fate
(decision workflow, quarantine, or `claim_failed`) with honest flags."**

| Dependency | Treatment |
|---|---|
| Comprehend, Textract, Transcribe, history | **Soft** → `failed` status + flag → human review |
| S3, Step Functions, the v1 start | **Hard** → retry, then `claim_failed` (conservation holds) |
| Glue DQ (the batch gate) | **Fail closed** (quarantine the batch). Option spectrum below. |
| The `data-quality` config | **Fail closed** (M17): pinned per batch at Admit; `config_source=fallback` → quarantine the batch; the catalog hash is stamped into the Glue ruleset description and compared |
| v1 extraction on a bundle key (v1's own C11 degrade path) | **Soft**: the rule-based degrade floor = the canonical intake fields (deterministic; still routes to review) (M16) |
| The intake execution itself | **Watchdog** (M14): an EventBridge rule on intake execution `FAILED` / `TIMED_OUT` / `ABORTED` → a second entry into Account Batch Outcome → a `batch_failed` summary + `BatchFailed{Status}`; an alarm on intake `ExecutionsFailed`. The start event gets a dead-letter queue on the trigger |

- **Per-source kill switches** (ops toggles in the `data-quality` profile,
  polarity per the card: `disable-documents`, `disable-call`, …, default
  `false`). They let an operator skip a source that is down for every claim
  without a deploy. Flags evaluate from the ConfigProvider's local cache,
  never from the dependency they kill.
- **Glue DQ outage options (C11 spectrum):**
  - (a) **fail closed** — quarantine and re-run later. **PoC pick**: simplest
    and safest.
  - (b) a **deterministic fallback gate**. With SD-1, the Intake Rule Catalog
    can evaluate the same rules and aggregates in Lambda for ≤ 200 rows. The
    batch is marked `gate_engine: fallback` with a `DQGateFallback` metric.
    Deferred until a batch SLO exists, because it adds a second evaluation
    path to keep semantically equal.

**C8 — partitions:**
- Per-branch `Catch` inside `Parallel`: a source cannot fail its siblings.
- Iterator-level catch: a claim cannot fail the Map.
- `Map MaxConcurrency` 4: caps downstream TPS and paces v1 starts.
- **Map shape (M14):** inline Map ≤ **50** claims; **Distributed Map** (a
  Standard child execution per claim) for 51–200, so one execution's history
  limit cannot cap Transcribe polling (C-7). Iteration outputs are trimmed
  with `ResultSelector`.
- **Reserved concurrency on `claim-processor-intake-step`** (start at **20**, ratified as ≥ 20 by M14; *corrected 2026-09-23 by risk-storm C-7: 10 was below the 16 concurrent invocations of 4 claims × 4 sources, so the plane would throttle itself*): the
  intake plane cannot starve v1's Lambdas of account concurrency.
- Two separate state machines: an intake bug cannot fail a decision in
  flight.

**C10 — shed at admission, before per-claim cost.**
- `batch_too_large` (> 200 rows) and a low batch DQ score quarantine the
  **whole batch**. They are rejected before any Comprehend, Textract or
  Transcribe spend, and before the review queue grows.
- **Never shed the batch summary and quarantine record** (the conservation
  "ping"): they are written even on quarantine.

**C1 — named, not applied.** A breaker on Textract or Comprehend needs a
measured `SourceFailed` rate first. Until then, C2's bounded retries plus
C11's soft degradation are the whole loop. A breaker whose "failures" are
throttles under our own fan-out would turn a pacing problem into an outage.

### 4. Apply knobs (defaults, not policy — recalibrate from §2 metrics)

| Card | Knob | Start value | Calibrate from |
|---|---|---|---|
| C7 | Comprehend / Textract client connect / read | 5 s / 30 s | p99.9 of call latency |
| C7 | intake-step Lambda timeout / Task `TimeoutSeconds` | 90 s / 120 s (Task > Lambda) | step duration p99.9 |
| C7 | Glue DQ: API `Timeout` / poll | 10 min / 40 × 15 s | `DQRunSeconds` |
| C7 | Transcribe poll | 40 × 15 s (≈ 10× the headroom for ≤ 60 s audio **[re-verify turnaround]**) | `TranscribeJobSeconds` p99.9 |
| C7 | Intake execution `TimeoutSeconds` | 3600 s | batch duration |
| C2 | State `Retry` on throttling / 5xx | `IntervalSeconds` 2, `BackoffRate` 2, `MaxAttempts` 4, `MaxDelaySeconds` 30, `JitterStrategy` FULL | `RetryAttempts` + throttle counts |
| C2 | SDK retries (intake clients) | `standard`, `max_attempts` 1 | — (the one-layer rule) |
| C9 | Lock / feedback keys | as §3 | `DuplicateBatch`, `AlreadyStarted` |
| C8 | Map `MaxConcurrency` / Lambda reserved concurrency | 4 / **20** (≥ claims × sources + headroom; was 10 — C-7; ratified as ≥ 20 by M14) | throttle counts vs `ClaimSettleMs` |
| C8 | Map shape (M14) | inline Map ≤ **50** claims; **Distributed Map** (a Standard child execution per claim) for 51–200; > 200 rows quarantined at admission (C10, ADR 0019) | history events per claim vs the 25,000-event execution history limit (C-7) **[re-verify]** |
| C8 | Iteration outputs (M14) | trimmed with `ResultSelector` | state payload size (`States.DataLimitExceeded`, C-7) |
| C10 | `dq.max_batch_rows` / `dq.batch_min_score` | 200 / 0.80 | quarantine rate vs rows |
| C11 | Source kill switches | all `false` | `SourceFailed{Source}` |
| C11 | Execution watchdog + trigger DLQ (M14) | an EventBridge rule on intake execution `FAILED` / `TIMED_OUT` / `ABORTED` → a `batch_failed` summary + `BatchFailed{Status}`; an alarm on intake `ExecutionsFailed`; "Trigger dead-letter queue" [Amazon SQS] on the intake trigger | `BatchFailed{Status}`, `ConservationGap` |

> **LLD update (2026-09-24).** Three knobs above changed at LLD depth
> (`../design/lld-v2-data-prep.md`): SDK clients use `total_max_attempts: 1`,
> because botocore's `max_attempts: 1` means one retry (SVC-04); the DQ poll is
> 48 × 15 s, so the Glue run's own 10-minute timeout fires first (ASL-28); the
> Transcribe poll is 20 × 30 s (ASL-29). The execution timeout is 10,800 s
> (ASL-31; B3.1-a, decided 2026-09-24).

### 5. Verify (fitness)

| Card | Metric → assertion (offline unless marked) |
|---|---|
| C7 | ASL test: every `Task` has `TimeoutSeconds`, and each Task > its Lambda timeout; every poll loop has a counter and a budget Choice; the execution has `TimeoutSeconds`. Grep: no `time.sleep` in `dataprep/`. Stubber: DQ budget exhausted → the cancel call is issued. |
| C2 | ASL test: every `Retry` has `JitterStrategy: FULL` + `MaxDelaySeconds`. Unit: intake clients are built with `total_max_attempts == 1` (LLD SVC-04). Stubber: throttle → the step raises once (no in-Lambda retry loop). |
| C9 | Stubber: the lock returns 412, held by another `RUNNING` execution → `duplicate_batch`, zero downstream calls. Holder `FAILED` → takeover with `IfMatch`; a racing takeover gets 412. `ExecutionAlreadyExists` → `already_started`. Replaying one batch twice → one bundle per claim revision, one v1 start. |
| C11 | Fake: each source failing alone → the claim still dispatches with `<source>_failed` + human review. A kill switch set → zero calls to that service. |
| C8 | Fake: one claim's source raising → the other claims in the batch are unaffected; the Map completes. |
| C10 | A 201-row batch → quarantined with zero service calls; a low DQ score → quarantined with zero per-claim calls. |
| C9 (M13) | Stubber: the lock returns 412 and the holder ARN == `$$.Execution.Id` → the execution proceeds (no `duplicate_batch`). A takeover reads the holder through `states:DescribeExecution` first. `CreatePartition` raising `AlreadyExistsException` → success. IAM lint: the intake role has `states:DescribeExecution` on intake executions. |
| C8 / C11 (M14) | ASL test: the inline Map is capped at 50 claims, and 51–200 run as a Distributed Map (a Standard child execution per claim); every iteration output passes a `ResultSelector`. Fake: an intake execution `FAILED` / `TIMED_OUT` / `ABORTED` event → a `batch_failed` summary + `BatchFailed{Status}`. `[gate]`: the trigger has the dead-letter queue, the alarm on intake `ExecutionsFailed` exists, and the intake-step reserved concurrency is ≥ 20. |
| C11 (M17) | Fake: `config_source=fallback` at Admit → the batch is quarantined with zero per-claim calls (fail closed). Unit: the DQ config is pinned once per batch at Admit; the rendered Glue ruleset description carries the catalog hash, and Admit compares it. |
| Conservation | For every seeded batch: `ConservationGap == 0` (spec AC-Z9 corpus). `[gate]`: the same on the smoke. |

**Regressions caught:**
- Adding SDK retries to intake clients breaks the C2 client-config assertion.
- Removing a budget Choice breaks the C7 ASL test.
- Letting a branch exception escape breaks the C8 / C11 fake tests.

### 6. Review finding — v1 retry amplification (routed to v1 re-entry, not changed by v2)

- `invoker.py:11-16` configures Bedrock with `retries={"mode": "adaptive",
  "max_attempts": 5}` ("One retry layer — do not wrap this").
- The v1 ASL still wraps `UnderstandExtract` / `RetrieveSummarize` in `Retry`
  on `ThrottlingException` with `MaxAttempts` 5 (`../build/sfn/asl.json`).
  That was a deliberate choice (re-review #3, option B).

Worst case: **5 × 5 = 25 Converse attempts per step** before degradation
(more with ensemble members). Adaptive mode's client-side rate limiter
softens this, but it is still two layers under RetryBackoff C2's one-layer
rule. Options for the v1 owner:
- lower one layer to `max_attempts` 1–2;
- or make the state Retry the only layer, which is what v2 does.

Needs a metric first: the Bedrock throttle count vs the retry count.

### 7. Reserved-category gaps (honest — not forced into resilience)

| Pattern used by v2 | Category | Status |
|---|---|---|
| **Claim-check** (S3 refs in state payloads, ≤ 32 KB) | messaging | `sdp-messaging` **reserved** — no card; cited from the style fallacy "bandwidth is infinite" |
| **Choreography** (S3 → EventBridge → feedback; upstream → intake) | messaging | `sdp-messaging` **reserved** |
| **Manifest-last commit** (attachments first, CSV last) | data / coordination | `sdp-data` / `sdp-coordination` **reserved** |
| **Single writer per prefix + data zones** | data | `sdp-data` **reserved** |
| **Distributed lock with lease / takeover** (S3 conditional put) | coordination | `sdp-coordination` **reserved** (C9 covers only its idempotency half) |

These gaps are input for the sdp family's next waves (memory: later category
waves).
