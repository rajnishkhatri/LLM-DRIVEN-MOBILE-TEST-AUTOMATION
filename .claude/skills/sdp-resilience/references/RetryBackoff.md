---
id: C2
title: 'Retry & backoff'
description: >-
  Retry only transient, idempotent failures — exponential backoff + full jitter,
  at one layer, under a ~10% budget. Complements the circuit breaker (C1);
  stacked retries are the usual metastable-failure loop. Self-contained clinic
  card: classify → select strategy → apply knobs → verify, with verified library
  and mesh defaults, hedging, LLM-provider retries, and failure modes.
tags: [system-design-patterns, resilience, retry, backoff]
---

# Retry & backoff

**See also (non-load-bearing bonus):** the source Concept [Retry, backoff, and retry budgets](../../../../cases/SystemDesignPatterns/RetryBackoff.md) carries the full per-claim provenance. This card stands alone — you do not need to open it to diagnose, select, tune, or verify.

The circuit breaker (card C1) decides **whether to call**. Retry answers the complementary question: once you call and the attempt fails, **whether, when, and how often to try again**. It is the controlled alternative to giving up immediately *and* to retrying recklessly. Done well, retries absorb transient faults invisibly; done badly, they are the single most common *sustaining effect* in metastable outages. The quality attributes in play are **reliability** (a blip does not become a user-visible error) and **availability of the caller**. The costs: extra load on an already-sick callee, extra tail latency, and a new way to turn a partial outage into a total one. Brooker's framing is the one to keep in mind — retries are **selfish**: each client helps itself at the fleet's expense. GitHub's August 2025 search incident is the shape in miniature — retry logic masked a fault until the retry queues overwhelmed the load balancers.

## Lineage and vocabulary

- **Nygard, *Release It!*** treats Timeouts as the first stability pattern; retries without a bound are how Integration Points become Cascading Failures. The companion patterns are the breaker, bulkheads, and load shedding — retries are not a complete strategy on their own.
- **Brooker, "Exponential Backoff And Jitter" (2015)** is the jitter canon. Capped exponential backoff *alone* still produces synchronized waves (the thundering herd). Three jittered variants, implemented in the `aws-arch-backoff-simulator` (`ExpoBackoffFullJitter` / `EqualJitter` / `Decorr`): **Full**, **Equal**, **Decorrelated**. Full does the least *work*; Equal is the loser of the jittered set (more work *and* much more time); Full vs Decorrelated is a work-vs-time trade — Full uses slightly *more* time than Decorrelated, not less. ("Full jitter is fastest" is a common misconception.)
- **Brooker, "What Is Backoff For?" (2022):** backoff helps closed-loop systems and short spikes, not sustained open-loop overload. If the callee is still over capacity, waiting and hitting it again is how you stay there.
- **Brooker / AWS Builders' Library**, "Timeouts, retries and backoff with jitter" and "Fixing retries with token buckets": pick timeouts from the latency distribution (p99.9 for a 0.1% false-timeout budget); a **five-deep** stack with **three tries** per layer is **3⁵ = 243×** database load (© 2019 — *tries*, so 3 per layer, not "3 retries = 4 attempts"); Amazon's preferred control is a **local retry token bucket** (in the AWS SDK since 2016), because a breaker on the *primary* path is modal. A breaker applied *only to retries* (first attempts always pass) caps retry load without making the happy path modal.
- **Google SRE book ch. 21–22** and the **Workbook**: per-request cap of **three attempts**; per-client **retry budget of ~10%** of requests (fleet load grows to "just below 3×" without it, "~1.1×" with it); retry **only at the layer immediately above** the rejector; backends can answer **"overloaded, don't retry"**; server-wide budget example of **60 retries/min/process**; Pokémon GO launch produced **20×** peaks from synchronized client retries — fix = jitter + truncated exponential backoff + admin rate limits.
- **Azure Architecture Center** Retry pattern + **Retry Storm** antipattern: classify transient vs permanent; **do not nest** retry policies (the inner one should fail fast); the breaker is prescribed specifically against retry storms.
- **Dean & Barroso, "The Tail at Scale" (2013):** a **hedged** request sends a backup *before* failure, after waiting past expected p95 (~5% extra load). Bigtable: hedging after 10 ms cut the 99.9th percentile from **1 800 ms → 74 ms** at **+2%** requests. Hedging is not a retry.

## What is worth retrying

The first branch is classification. Retrying a permanent failure wastes capacity and delays surfacing the real error. Inspect the status or exception *before* backing off — a library that retries "any exception" will retry `IllegalArgumentException` until the budget is gone.

| Outcome | Retry? | Why |
|---|---|---|
| Connection refused / reset, DNS or TLS failure, TCP reset | **Yes** | The path failed; the request likely never ran. |
| Timeout, gRPC `DEADLINE_EXCEEDED` | **Yes, once, under the remaining deadline** | The attempt may have succeeded; only safe if idempotent. Bound the attempt so the retry still fits the outer deadline. |
| HTTP 408, 409, 429 with `Retry-After`, 502 / 503 / 504, gRPC `UNAVAILABLE` | **Yes** | Transient or overload. Honour `Retry-After` when present and short. |
| HTTP 500 / 529, gRPC `INTERNAL` / `UNKNOWN` | **Yes, bounded** | Server-side fault. Still subject to the budget. |
| 429 / 503 that names a delay | **Wait that long, then one retry** | Do not spin. |
| 400 / 404 / 413 / 422, validation, gRPC `INVALID_ARGUMENT` / `NOT_FOUND` / `FAILED_PRECONDITION` | **No** | The request is wrong. SRE: do not retry permanent errors or malformed requests. |
| 401 / 403, gRPC `UNAUTHENTICATED` / `PERMISSION_DENIED` | **No — alert** | Configuration. Retrying hides it. |
| Spend-cap / quota 429 (no `Retry-After`, or billing exhausted) | **No** | Access will not resume on a timer. Page a human. |
| Caller cancellation | **No** | Polly excludes `OperationCanceledException` for exactly this reason. |
| Circuit **Open** | **No** | Fail into the fallback. Retrying an Open circuit delays the degraded path. |
| Half-open **probe** | **No** | The probe must be a single attempt; retries falsify recovery. |
| HTTP 200 with an app-level refusal or truncated context window | **No** (same model) | Not an HTTP error. See the LLM section. |

## Backoff and jitter

Retrying immediately floods a recovering service. A fixed delay helps one client but synchronizes a fleet. Capped exponential backoff grows the wait:

```
expo(n) = min(cap, base · 2ⁿ)
```

Without jitter, every client computes the *same* schedule, so a shared blip becomes a **thundering herd** at 1 s, 2 s, 4 s, 8 s. Jitter randomizes the sleep to desynchronize clients:

| Strategy | Sleep formula | Work (callee load) | Time-to-finish | Use |
|---|---|---|---|---|
| None (immediate) | 0 | Highest | Fast on rare blips | Almost never in production |
| Fixed interval | constant | Moderate | Predictable | Simple systems; still herds |
| Exponential, no jitter | `expo(n)` | High (synchronized waves) | Slowest of the exponential set | Brooker: the clear loser |
| **Full jitter** | `random(0, expo(n))` | **Lowest** | Slightly slower than Decorrelated | **Default for most distributed callers** |
| Equal jitter | `expo(n)/2 + random(0, expo(n)/2)` | Slightly more than Full | Much slower than Full | Guarantees a minimum wait; not worth it |
| Decorrelated jitter | `min(cap, random(base, sleep_prev · 3))` | Higher than Full | Slightly faster than Full | When completion time matters more than callee work |

**Full jitter is the recommended default** because it minimizes callee work; the slight p99 cost is the trade for not dogpiling. `Math.random()` (or the language equivalent) is enough to desynchronize clients that failed in the same millisecond — do **not** seed from the clock at second resolution.

## Retry budgets

Backoff spaces *one client's* retries. A **budget** caps *fleet* retry traffic. Enforce it where you can see **aggregate** traffic — infrastructure (Envoy, gRPC service config, AWS SDK) — not only inside one process. When the budget is exhausted, **do not retry**; fail or fall back.

| Mechanism | Rule | Source |
|---|---|---|
| Per-request attempt cap | At most **three attempts** (original + 2), then bubble up | SRE ch. 21 |
| Per-client retry ratio | Retry while retries are **< ~10%** of that client's requests | SRE ch. 21; Yandex 2024 kept a 10% local token bucket |
| Server-wide cap | e.g. **60 retries/min/process**, then fail | SRE ch. 22 |
| Token bucket (client) | Tokens refill on success; a retry spends a token; empty = no retry | AWS SDK since 2016; Brooker 2022; gRPC `retryThrottling`. Cross-SDK 2026 table (capacity **500**, transient cost **14**, throttling cost **5**) is **opt-in** (`AWS_NEW_RETRIES_2026=true`); Java 2.x default is still **Legacy** |
| Envoy retry budget | When set, **20%** of active + pending requests, `min_retry_concurrency` **3**; **overrides** `max_retries` | Envoy cluster circuit-breaking |
| gRPC `retryThrottling` | With a configured `retryPolicy`: `{maxTokens ∈ (0,1000], tokenRatio}` (−1 per failure, +`tokenRatio` per success; retries suppressed at ≤ `maxTokens/2`); gRFC A6 caps `maxAttempts` at **5**. There is **no default** retry policy — only transparent retries | gRFC A6 |

SRE's headline: without the 10% budget, load can grow to just under **3×**; with it, about **1.1×**.

## Amplification and the one-layer rule

Retries multiply down a call chain. **Memorize SRE's arithmetic:** three layers each issuing **3 retries (4 attempts)** produce **4³ = 64** attempts on the database (not 27 — that under-counts by treating "3 retries" as 3 attempts). Extra leaf attempts under SRE: **63**. The Builders' Library's five-deep stack with three *tries* per layer is **3⁵ = 243×**. Papers count attempts vs retries differently; the invariant is **the product of per-layer attempt counts**.

So: **retry at one layer**, typically the one immediately above the failure, and never both in the application *and* in the mesh. Azure's Retry pattern is explicit: **do not nest** retry policies (the inner should fail fast). If Envoy owns retries, the app must not wrap the same call. Auditing overlapping policies is the first step when moving retries into a sidecar — stacked policies are a classic source of production retry storms.

Napkin estimate (not SRE): a 10% failure rate where every failure takes 3 extra attempts adds ~30% traffic to a service that is *already* failing. That is how degradation becomes outage.

## Idempotency

A transient failure is necessary but not sufficient. Retrying is only safe if doing the work twice has the same effect as doing it once.

- HTTP **GET** is safe and idempotent. **PUT** and **DELETE** are idempotent and *unsafe*. **POST** that creates an order is neither. RFC 9110 §9.2.2: a client **SHOULD NOT** automatically retry a non-idempotent method unless it knows the semantics are actually idempotent or that the original never applied; a **proxy MUST NOT** automatically retry non-idempotent requests; a client **SHOULD NOT** automatically retry a *failed automatic retry*.
- Mint an **idempotency key once** per business operation and reuse it across retries, queue replays, and the fallback path. Stripe stores the first status and body per key for **at least 24 hours** (including 500s) and errors if the payload differs; do not send the key on GET or DELETE. The IETF `Idempotency-Key` draft-07 (2025-10-15, expired 2026-04-18, **not** an RFC) specifies **400** if the key is missing when required, **422** if reused with a different payload, **409** if the original is still in flight.
- `.NET`'s `DisableForUnsafeHttpMethods()` turns retries off for POST, PATCH, PUT, DELETE, CONNECT. That is **safety** (RFC 7231 §4.2.1), *not* idempotency — it also disables PUT/DELETE, which *are* idempotent. The standard resilience handler retries every method unless you call it.
- A timeout on a payment capture is the classic double-charge: the first attempt succeeded, the caller never saw the 200, the retry charges again. **The key, not the HTTP method, is the control.**

## Timeouts, deadlines, and the breaker

Retries only behave if their timeouts and the breaker are coordinated. A hung call that never fails never increments anything — bound every outbound call.

| Knob | Role | Rule |
|---|---|---|
| **Per-attempt timeout** | How long one try may run | Must be **shorter than** the breaker's detection window *and* shorter than the remaining outer deadline. A try that can outlast the window is invisible to the breaker. |
| **Total / outer timeout** | How long the *logical* request may run, retries included | Envoy's route timeout **includes all retries**. A 3 s outer with a 2.7 s first try leaves 0.3 s for the retry *and* its backoff. |
| **Deadline remaining** | What you propagate downstream | gRPC converts the deadline to remaining time (2 s deadline, 0.5 s spent → 1.5 s downstream). Enabled by default in Java and Go. |
| **Breaker state** | Whether to call at all | Open → no retry. Half-open → one probe, no retry. Closed → retries feed the failure counter, so an aggressive loop can trip a healthy-enough dependency. |
| **Pipeline order** | What the breaker sees | .NET standard handler: rate limiter → **total timeout 30 s** → **retry (3, exponential + jitter, 2 s base)** → circuit breaker → **attempt timeout 10 s**. Resilience4j Spring aspects nest **Retry outermost** around CircuitBreaker, RateLimiter, TimeLimiter, Bulkhead. Retry *outside* the breaker can be refused by an Open circuit (good). |

## Strategy comparison

| Strategy | Delay | Downstream load | Best for | Risk |
|---|---|---|---|---|
| Immediate retry | None | Very high | Ultra-low-latency paths with *rare* transient blips | Retry storms |
| Fixed interval | Constant (e.g. 2 s) | Moderate | Simple systems with predictable recovery | Thundering herd |
| Exponential, no jitter | 1 s, 2 s, 4 s, 8 s | Lower, but peaked | — | Synchronized waves; Brooker's loser |
| Exponential + **full jitter** | `random(0, expo)` | **Lowest** | Production microservices at scale | Slightly higher p99 |
| Hedged request | Backup sent after a latency threshold, not after failure | ~5% extra if delayed to p95 | Tail-latency-sensitive reads | Double work when both succeed; must cancel the loser |
| No retry (fail fast) | n/a | None | Non-idempotent writes without a key; Open breaker; spend-cap | Missed transient recovery |

For most production RPC, **exponential backoff + full jitter + a 10% budget + one layer** is the balance. Hedging is the read-path alternative when the problem is a *slow* replica, not a failed one.

## Configuration & verified defaults

Verified 2026-09-13. Attempt-count vocabulary is inconsistent — **read the column.** Resilience4j's `maxAttempts` *includes* the original call; Polly's `MaxRetryAttempts` is *in addition to* it.

| Library | Attempts | Backoff | Jitter | Retries what | Does not retry | Budget |
|---|---|---|---|---|---|---|
| **Resilience4j Retry** | `maxAttempts` **3** (= original + 2); `waitDuration` **500 ms** fixed | `intervalFunction` default = constant; `ofExponentialBackoff()` available | `ofRandomized()` available; off by default | `retryExceptionPredicate` default `true`; `retryOnResult` default `false` | `ignoreExceptions` (empty); business exceptions you list | none |
| **Polly v8 Retry** | `MaxRetryAttempts` **3** (+ original = **4**); `Delay` **2 s**; `BackoffType` **Constant**; `UseJitter` **false** | Constant / Linear / Exponential | ±25% of Delay, except Exponential uses `DecorrelatedJitterBackoffV2` | Any exception except `OperationCanceledException` | Cancellation; whatever `ShouldHandle` excludes | none (compose a rate limiter) |
| **.NET standard HTTP handler** | **3 retries**, exponential + jitter, **2 s** base | Exponential | On | HTTP ≥ 500, 408, 429, `HttpRequestException`, `TimeoutRejectedException` | Nothing until `DisableForUnsafeHttpMethods()` | rate limiter in front (1000 permits) |
| **.NET hedging handler** | min 1 / max **10** hedge attempts, delay **2 s**; total timeout **30 s**, attempt **10 s** | Hedge delay, not retry backoff | — | Same failure set as the standard handler | — | — |
| **Anthropic SDK** (Python 1.5.0 / TS 0.125.0, 2026-09-10) | `max_retries` **2**; timeout **10 min** (TS scales to 60 min for large non-streaming) | `min(0.5 · 2ⁿ, 8)` s | × `[0.75, 1.0]` (minus up to 25%; **not** ±25%) | Connection errors, 408, 409, 429, ≥ 500 (covers 504, 529) | `x-should-retry: false`. Python honours `retry-after` only if `0 < v ≤ 60` s; **TS is uncapped** | none |
| **OpenAI Python SDK** 3.13.0 | `max_retries` **2**; timeout **600 s** | 0.5 s → 8 s cap | same Stainless shape | Connection, 408, 409, 429, ≥ 500 | Spend / quota 429s do not restore access; `retry-after` **> 120 s → do not retry** | none |
| **Tenacity** 9.1.4 | **Forever**; wait **none** | none | off | `Exception` | success; non-`Exception` `BaseException` | none — override before production |
| **p-retry** 8.0.1 | **10 extra**; 1 s × 2ⁿ | Exponential | off | Promise rejections | `AbortError`; most `TypeError` | `maxRetryTime` default ∞ |
| **Failsafe** 3.3.2 | **3 total**; delay **0** | none | off | failed execution | `abort*` | optional max duration |
| **spring-retry** 2.0.13 | **3 total**; fixed **1 s** | Fixed | off | all exceptions | `noRetryFor` empty | none |
| **Hystrix** 1.5.18 | **1** (no retry module) | — | — | — | — | Retries lived in Feign / Ribbon / Spring Retry, not Hystrix |
| **Envoy router** 1.40 | **Off** unless configured; policy present → `num_retries` **1**. Concurrent CB `max_retries` **3** | Fully jittered exponential, base **25 ms**, cap **10×** (250 ms): 1st 0–24 ms, 2nd 0–74 ms, 3rd 0–174 ms. Rate-limited path: `Retry-After` then `X-RateLimit-Reset`, jitter `random(interval, interval·1.5)`, cap **300 s** | Full jitter built in | Only what `retry_on` / `retry_grpc_on` lists | Outer route timeout (504) is **not** retried unless a *per-try* timeout is set; `x-envoy-ratelimited` only if that policy is on | `retry_budget` **20%** of active+pending, `min_retry_concurrency` **3** (overrides `max_retries` when set) |
| **gRPC client** | **No default `retryPolicy`.** Transparent retries only (never-seen-by-server; one if it reached the server library). Configured A6: `maxAttempts` cap **5** | Service-config backoff | Per config | Configured retryable statuses | Everything else; transparent retries do **not** count toward `maxAttempts` | Optional `retryThrottling`; guide example 10 / 0.1 is **not** a default |

**Metrics exposed.** Resilience4j: one gauge `resilience4j.retry.calls` tagged `successful_without_retry` / `successful_with_retry` / `failed_with_retry` / `failed_without_retry` (logical outcomes, not per-attempt). Polly meter `Polly`: `resilience.polly.strategy.events` (`OnRetry`), `.attempt.duration` (`attempt.number` 0-based). Envoy: `upstream_rq_retry`, `_retry_success`, `_retry_overflow` (circuit breaking *or* budget), `_retry_limit_exceeded`, `_retry_backoff_exponential`, `_retry_backoff_ratelimited`.

## Where it lives

Placement is a layering decision. The invariant is **one owner** — never stack a client retry on a layer that already retries.

| Layer | What it retries | Trade-off |
|---|---|---|
| **In-process library** (Resilience4j, Polly, Failsafe, language SDKs) | Typed exceptions, result predicates, easy idempotency-key reuse | Blind to fleet-wide retry rate unless you add a shared bucket |
| **HTTP / gRPC client SDK** (AWS, Anthropic, OpenAI) | Transport + a fixed status list | Convenient; often *on by default*. Two retries × a 10-minute timeout is a 30-minute hang. Turn it down or off when a mesh or app policy already retries. |
| **Sidecar / mesh** | Envoy: off until configured, then `num_retries` **1**. Istio VirtualService / MeshConfig default `attempts: 2` (`1 + attempts` total). Linkerd HTTPRoute `retry.linkerd.io/limit` default **1** since 2.16, opt-in, bodies > **64 KiB** not retried | Transparent; Envoy can pick another host. Istio `retryOn` default is connect/reset/unavailable/cancelled. |
| **Cloud LB / gateway** | **ALB: no retry policy.** API Gateway **does not retry integration timeouts** (50 ms–29 s). ECS Service Connect: **2** connection retries, `perRequestTimeout` **15 s**. App Mesh default **2** (EOS 2026-09-30). Azure APIM: no implicit retry; `count` 1–50 required | Do not assume the edge retries for you — and do not stack a client retry on a gateway that already does |
| **Reverse proxy** | Kong Service `retries` default **5**, **transport only** (not 5xx/429). Traefik `attempts` **required**, stops on any status. NGINX `proxy_next_upstream_tries` default **0 = unlimited**; ingress-nginx default **3** | Unlimited NGINX tries is a storm waiting for a config. Kong will not save you from application 5xx |
| **Message consumer** (Spring Kafka `DefaultErrorHandler` `FixedBackOff(0, 9)` = ten deliveries, then log; DLQ via `DeadLetterPublishingRecoverer`) | Redelivery, not an RPC retry | Pause/resume and DLQ are the complementary controls |

Istio's own fault-injection task is the object lesson in mismatched budgets: `productpage`→`reviews` timeout **3 s + 1 retry = 6 s** against `reviews`→`ratings` **10 s** hard-coded — a 7 s injected delay surfaces the mismatch.

## Observability

A retry without metrics is how retry storms hide inside "elevated latency." Emit at least:

| Metric | What it tells you |
|---|---|
| **Retry rate** (retries / original requests) | Against the 10% budget. A sustained rise is the early signal. |
| **Retry exhaustion / `failed_with_retry` / `_retry_limit_exceeded`** | The dependency is past transient. Page on a spike. |
| **`_retry_overflow`** | The budget or the retry breaker did its job — or is too tight. |
| **Retry-induced latency** (attempt-duration histogram, `attempt.number`) | Whether backoff is eating the SLO. |
| **Per-attempt outcome** | Ground truth for the retry predicate. |

Log every attempt with correlation ID, attempt number, delay applied, and the triggering error. No vendor publishes a PromQL recipe for these; alert on *exhaustion rate* and *retry rate vs 10%*, not a copied query.

## Tuning

| Parameter | Too low | Too high | Starting point |
|---|---|---|---|
| Max attempts | Miss real transients | Amplification; SLO miss | **2 extra** (SRE's three-attempt cap) on idempotent reads; **0–1** on writes even with a key |
| Base delay | Herd; no breathing room | Recovery delayed; outer timeout consumed by sleeping | Tens to hundreds of ms for RPCs; honour `Retry-After` when shorter than your cap |
| Cap | Exponential grows into the outer timeout | Callee never sees a gap | Fit *worst-case* `attempts × (per-try timeout + cap)` inside the SLO |
| Jitter | Synchronized waves | — | **Full jitter** unless you measured Decorrelated finishing faster *and* can afford the extra work |
| Per-try timeout | False timeouts, extra retries | Threads pinned; breaker blind | From the latency distribution (p99.9 if you can afford 0.1% false timeouts), always < remaining deadline |
| Retry budget | Gives up on recoverable blips | Storm | **10%** per client; Envoy 20% of *in-flight* if the mesh owns it |
| Layer count | — | 64× / 243× amplification | **One** |

## Alternatives that beat a retry

When *not* to retry — the situations where another control is strictly better:

| Situation | Prefer | Why |
|---|---|---|
| The replica is *slow*, not down | **Hedging** (Dean/Barroso; Polly hedging; Envoy `x-envoy-hedge-on-per-try-timeout`) | Cut tail latency without waiting for a failure. Cancel the loser. |
| The callee is overloaded | **Don't retry** + "overloaded" signal + load shed / adaptive concurrency | Backoff does not help open-loop overload — it prolongs it. |
| Many small clients, poor local estimates | Client-side adaptive throttling (SRE ch. 21: last **two minutes** of `requests` vs `accepts`, multiplier **K ≈ 2**) or a token bucket | Degrades smoothly; no per-client threshold to get wrong. |
| The dependency is hard-down | **Breaker + fallback** (card C1) | Fail fast; stop paying the per-try timeout. |
| Non-idempotent write, no key | Fail and surface; or enqueue with a key | A retry is a duplicate. |
| Work outlives the caller's patience | Deadline propagation and cancellation | Stop spending capacity on answers nobody will read. |

## Worked calibration — order service, 3 s SLO

Constraints from the source exercise (a design drill, not a vendor SLA):

- Order service: **3 s** end-to-end.
- Inventory: **200 ms** average, **2%** transient failures.
- Payment gateway: **800 ms** average, **0.5%** transient failures.
- Sequential: inventory then payment.

| Knob | Inventory | Payment | Why |
|---|---|---|---|
| Retry? | Yes, **1** extra attempt | **No** RPC retry | Inventory is a read/reserve that can be keyed. Payment capture is the double-charge path; one 1 500 ms retry already breaks the SLO (1 500 + backoff + 1 500 > 3 000). Enqueue on transient payment failure. |
| Per-try timeout | **400 ms** | **1 500 ms** | Well above the mean; no p99.9 available. Payment's 1 500 ms is the entire remaining budget after inventory's worst case. |
| Backoff | Full jitter, base **50 ms**, cap **100 ms** | n/a | Must fit in the leftover 3 000 − 800 − 1 500. |
| Worst-case latency | 400 + 100 + 400 = **900 ms** | **1 500 ms** | Sum **2 400 ms** < 3 000 ms. Adding a payment retry (3 100 ms) **misses** the SLO. |
| Jitter | Full | — | 2% inventory errors at checkout RPS is enough to herd without it. |
| Layer | Application (needs the idempotency / reservation key) | None, or Envoy `connect-failure` / `reset-before-request` **only** | Never `5xx` on a capture that may have succeeded. Never both app and mesh. |
| Budget | 10% client-side | n/a | Inventory's 2% healthy-transient rate sits under the budget; a real outage hits the cap and we fail that reserve. |
| Breaker | Yes; no retry when Open; half-open probe is one attempt | Yes; Open → enqueue | Per-try timeout < the breaker's window on each path. |
| Idempotency | Reservation key reused on the retry | Key minted once, reused on the *queue* replay | Timeout ≠ failure. |

Revisit after a week of `retry.calls` / `upstream_rq_retry` and the raw downstream error rate. If inventory retries are exhausting, the 2% is not transient.

## Testing and operating

- **Fault injection.** Toxiproxy (`reset_peer`, `timeout`, `latency` with jitter); WireMock `CONNECTION_RESET_BY_PEER` / scenario 500-then-200; Istio `fault.delay` / `fault.abort` (the 7 s vs 3 s+retry mismatch above).
- **Deterministic tests.** Resilience4j: mock the callee, assert `times(3)` against default `maxAttempts`. Polly v8: `ResiliencePipelineBuilder.TimeProvider` + `FakeTimeProvider` (v7's `SystemClock` is static and not parallel-safe).
- **Kill the retry.** Envoy runtime `upstream.use_retry` is a fleet-wide percent; SDKs take `max_retries=0`. Practice the fail-fast path, not only the happy retry.
- **Watch recovery.** Exhaustion rate, retry rate vs the 10% budget, and attempt-duration by `attempt.number` tell you whether backoff is eating the SLO.

## Failure modes

- **Retry storm / metastable loop.** Huang et al. (OSDI 2022): retry policy is the sustaining effect in **more than 50%** of 21/22 studied incidents (11 named). Bronson et al. (HotOS 2021): a 300 QPS-capable DB with one 1 s retry is vulnerable above **150 QPS**; after a 10 s blip at 280 QPS the retry holds the client at **560 QPS**. Slack 2022-02-22: cache-miss amplification plus client retries; recovery by a client-boot throttle raised in small steps. GitHub 2025-08-12: retry queues overwhelmed the load balancers. DynamoDB 2015: membership retries kept load high until metadata requests were **paused**.
- **Amplification across layers.** 64× / 243×. The fix is one layer, not a smaller delay.
- **Double execution.** Timeout + retry + queue replay around a capture. The idempotency key is the fix; HTTP method is not.
- **Herd despite exponential backoff.** No jitter. Pokémon GO 20×.
- **Backoff into the outer timeout.** Envoy will not start a retry that cannot finish. An app library often will — and then the breaker never sees a failure.
- **Retrying overload.** Backoff does not create capacity. Honour "don't retry" / `Retry-After` / spend-cap 429s.
- **SDK defaults you did not know were on.** Two retries × a 10-minute Anthropic timeout is a 30-minute thread. Set an explicit per-attempt timeout on time-to-first-token.

## Retries around LLM provider APIs

Model endpoints break the usual assumptions: many "failures" are capacity signals, latency is tens of seconds, and some failures arrive as HTTP 200.

| Signal | Retry? |
|---|---|
| Connection failure, 408, 409, 500 / 502 / 504 / 529, 503 overloaded | **Yes**, honour `retry-after` when ≤ the SDK cap (Anthropic **Python ≤ 60 s**; Anthropic **TS uncapped**; OpenAI **≤ 120 s** else do not retry; Portkey fails immediately if a single `Retry-After` > 60 s). |
| 429 rate limit **with** `retry-after` | **Yes**, wait that long. Scope to the key / tenant / model, not the provider. |
| 429 `slow_down` (OpenAI) | **Yes**, slower ramp (their rule of thumb: after 1 M input TPM, increase ≤ 50% every 15 min). |
| 429 spend-cap / `enforced_spend_limit_reached` / credit or org spend exhausted | **No.** Anthropic: no `retry-after`; retrying (including the SDKs' automatic retries) fails until access resumes. OpenAI: retrying billing / spend / quota errors won't restore API access. |
| 400 validation / context-length, 401 / 402 / 403, 413 | **No.** LiteLLM routes context-window and content-policy errors to **dedicated fallbacks**, not the generic retry path. |
| HTTP 200 `stop_reason: "refusal"` | **Do not retry unchanged on the same model** (Anthropic: usually earns another refusal). Fall back to another model or reset context. |
| HTTP 200 `model_context_window_exceeded` | Not an error. Do not treat as transient. |
| Mid-stream `error` event after a 200 | Retryable only as a **new** request, not as an HTTP retry of the same stream. |

**Knobs.** Stream so time-to-first-token is visible; set a per-attempt TTFT timeout *and* a total deadline (the 10-minute SDK default will hide every other knob); keep `max_retries` at the SDK **or** the gateway, not both; put model-tier fallback in orchestration *after* retries exhaust (LiteLLM: `num_retries` on the same `model_name`, then `fallbacks`). Portkey: up to 5 retries on `[429, 500, 502, 503, 504, 529]` at 1/2/4/8/16 s, 60 s cumulative wait cap. Cloudflare AI Gateway: `cf-aig-max-attempts` advertised as a maximum of 5 (treat as a cap of five, not a recommendation).

## Trade-offs

| Buy | Pay |
|---|---|
| Absorb transient faults; higher caller success | Extra load on a sick callee; extra p99 |
| Full jitter desynchronizes a fleet | Slightly slower completion than Decorrelated |
| 10% budget / token bucket caps the storm | Recoverable blips are dropped once the bucket is empty |
| One layer, coordinated with the breaker | Requires an audit; easy to stack with an SDK default |
| Hedging cuts read-path tail latency | Double work; must cancel; useless on non-idempotent writes |
| SDK retries on by default | Hidden 2 × 10 min hangs; spend-cap 429s retried until you turn them off |

The breaker decides **whether to call** (card C1). Timeouts decide **how long to wait** (card C7). Retries and their budget decide **whether to try again**. Fallbacks decide **what the user gets**. Coordinate all four.

## Sources

Verified 2026-09-13. Numbers, defaults, and failure modes carried from the source Concept's verified research; do not soften them.

- **Canon:** Brooker, "Exponential Backoff And Jitter" (2015) and the `aws-arch-backoff-simulator`; Brooker, "What Is Backoff For?" (2022) and "Fixing retries with token buckets"; AWS Builders' Library, "Timeouts, retries and backoff with jitter"; Google SRE book ch. 21–22 and SRE Workbook ch. 11; Azure Architecture Center Retry pattern + Retry Storm antipattern; Nygard, *Release It!*; Dean & Barroso, *The Tail at Scale* (2013).
- **Metastability / incidents:** Bronson et al. (HotOS 2021); Huang et al. (OSDI 2022); Slack 2022-02-22; GitHub August 2025; DynamoDB 2015; Yandex, *Good Retry, Bad Retry* (2024).
- **Idempotency:** Stripe idempotent requests; IETF `Idempotency-Key` draft-07 (2025-10-15, expired 2026-04-18); RFC 9110 §9.2.2; RFC 7231 §4.2.1 (via .NET's citation).
- **Libraries and clients:** Resilience4j 2.4.0, Polly 8.7.0, .NET standard/hedging resilience handlers, Tenacity 9.1.4, p-retry 8.0.1, Failsafe 3.3.2, spring-retry 2.0.13, Hystrix 1.5.18 (no retry module), AWS SDK retry modes, Anthropic SDK (Python 1.5.0 / TS 0.125.0), OpenAI Python SDK 3.13.0.
- **Infrastructure:** Envoy 1.40 router + cluster circuit-breaking; Istio 1.31 (`attempts: 2`); Linkerd 2.16; Kong / NGINX / ingress-nginx / Traefik / ALB / API Gateway / ECS Service Connect / App Mesh / Azure APIM; gRPC gRFC A6.
- **LLM:** Anthropic errors / rate-limits / refusals; OpenAI error-codes; LiteLLM fallbacks; Portkey automatic retries; Cloudflare AI Gateway request-handling.
