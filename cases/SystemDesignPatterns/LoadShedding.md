---
type: reference
title: 'Load shedding and backpressure'
description: 'The server side of overload: drop by criticality so goodput plateaus (not throughput), or slow producers with credit-based backpressure. Distinct from rate limits (C4, 429 by policy) and degraded responses (C11). Covers Yanacek shed-early and health-check priority, CoDel and adaptive LIFO, adaptive concurrency, HTTP/2 windows, 503 + Retry-After, verified defaults, a checkout calibration, and queues-don’t-fix-overload.'
tags: [system-design-patterns, resilience, load-shedding, backpressure]
---

# Load shedding and backpressure

**See also:** [rate limiting](RateLimiting.md) · [graceful degradation](GracefulDegradation.md) · [circuit breaker](CircuitBreaker.md) · [retry, backoff, and retry budgets](RetryBackoff.md) · [bulkhead](Bulkhead.md) · [timeouts](TimeoutsDeadlines.md) · [failover](Failover.md) · [publisher–subscriber](PubSubQueues.md) · [performance](../data-intensive-design/performance.md) · [NFR references](../data-intensive-design/nfr-references.md) · [catalog research (2026-09-13)](../../docs/research/sysdesign/c10-load-shedding-external-research.md)

When offered load exceeds what a server can finish *usefully*, it has three honest moves: **shed** (drop some work, cheaply and by priority), **push back** (make producers slow down), or **degrade** (do less *per accepted request* — [C11](GracefulDegradation.md)). Everything else is a queue, and a queue only converts overload into latency, memory, and a later bigger failure.

This note owns the first two. [Rate limiting](RateLimiting.md) is admission by *declared policy* and answers **429** when *this caller* exceeded *its* allocation. Shedding is admission by *measured capacity* and answers **503** when the *service* is short for everyone. Degradation shrinks the *response*; shedding drops or delays the *request*. Quality attributes: **goodput under overload** (useful work completed inside the client's patience), **latency integrity** for what is accepted, and survival of the metastable zone ([7](../data-intensive-design/nfr-references.md), [8](../data-intensive-design/nfr-references.md), [9](../data-intensive-design/nfr-references.md)). Costs: dropped work by design, priority plumbing, and metrics that lie if rejections enter the success histogram.

## Lineage and vocabulary

- **Yanacek, *Using load shedding to avoid overload*** ([15](../data-intensive-design/nfr-references.md)): **goodput ≠ throughput**. Throughput is offered (or accepted) RPS, including work that will time out; goodput is the subset finished without error *and* inside a latency the client can still use. Max-connections as the only knob is too imprecise. Shed **early and cheaply**; measure **client-perceived** availability and latency; **do not fold reject latency into the success histogram** (60% shed can make p50 look excellent). **Prioritize the load-balancer ping** — a missed health check shrinks the fleet, the last thing a brownout wants. Then: humans over crawlers; in-quota over burst; `end()` over `start()`; page *N* over page 1. Drop doomed work (remaining deadline, queue *age*, LIFO when the protocol allows). Hidden queues (TCP buffers, executor queues, CLB surge queues) are everywhere. Shed on the same CPU target as autoscaling **starves the scale-out signal**. False-positive target: **zero**.
- **Google SRE ch. 21–22**: QPS is a poor capacity unit — provision on resources (usually CPU). Criticality `CRITICAL_PLUS` / `CRITICAL` (production default) / `SHEDDABLE_PLUS` / `SHEDDABLE`, **propagated automatically**. Preferred utilization signal: **executor load average** (decayed active threads), shed when it exceeds processors. Rejections still burn CPU — a backend can be overloaded doing nothing but rejecting, so push shedding **client-ward** (adaptive throttling, last **two minutes**, multiplier **K ≈ 2**). Queue length **≤ ~50% of the pool** for steady traffic; Gmail often uses **queueless** servers. FIFO → **LIFO or CoDel**. Deadline check **after dequeue**. The cheaper-ranker / smaller-index move is **C11**, not this note.
- **Facebook, "Fail at Scale" (Maurer 2015)** and **CoDel (RFC 8289)**: two tuning-free disciplines. **Controlled delay** — if the queue has not drained recently, new entries get only **M = 5 ms** of queue budget (**N = 100 ms** otherwise); accept slightly more than capacity so the worker never goes idle. **Adaptive LIFO** — a forming queue flips to newest-first (the oldest has likely been abandoned). They compose. RFC 8289 is the same idea at the packet layer: control **sojourn time** (TARGET **SHOULD be 5 ms**, INTERVAL **100 ms**), not queue length.
- **Nygard** ([12](../data-intensive-design/nfr-references.md)) lists *Shed Load* and *Create Back Pressure* among the Stability Patterns. **Sackman** ([16](../data-intensive-design/nfr-references.md)) and **Cvet** ([1](../data-intensive-design/nfr-references.md)) are the backpressure / fan-in vocabulary; do not re-derive them here.
- **Wire signal.** RFC 9110 §15.6.4: **503** = temporary overload or maintenance; the server **MAY** send `Retry-After` (§10.2.3, HTTP-date or delay-seconds) and **need not** use 503 — it may refuse the connection. **429** stays in [C4](RateLimiting.md).

## Goodput vs throughput

```
offered RPS ──► [admit / shed] ──► accepted ──► finish inside timeout? ──► goodput
                      │
                      └── cheap 503 / window-close / nack
```

Without a bound, utilization ρ → 1 and queueing delay explodes. Brooker (2021-08-05): M/M/1 occupancy `E[N] = ρ/(1−ρ)` is **1 at ρ = 0.5** and **99 at ρ = 0.99**; the same 1/(1−ρ) blow-up hits time-in-system, and **high percentiles go first** — tail latency is the leading indicator of overload, well before errors. [performance.md](../data-intensive-design/performance.md) already ties that knee to retries and metastable failure. Shedding is the cut: refuse work that would only finish after the client has gone.

Yanacek's load-test shape: goodput **plateaus** near full utilization and stays flat as offered load keeps rising. If availability falls toward zero, the service still needs a shedder. Little's law (`L = λW`) converts any latency target into the in-flight cap that a [bulkhead](Bulkhead.md) or adaptive limiter enforces.

Shed is **not free**. Amdahl still collects on the reject path; when reject cost ≈ serve cost, SRE's client-side throttle is the move — at K = 2 the backend sees about one rejected request per accepted one.

## Shed early; never shed the ping

| Layer | What it can drop cheaply | Visibility cost |
|---|---|---|
| WAF / API Gateway / iptables | Volume before the process | Almost none — you will not know *which* API |
| LB / Envoy overload manager | New connections / streams (503, GOAWAY, close) | Proxy stats; no app log |
| Sidecar admission / adaptive-concurrency | Per-cluster concurrency or success-rate | Proxy counters |
| In-process middleware (Cinnamon, concurrency-limits) | After headers, before the handler | App logs + priority |
| After dequeue | Doomed-by-deadline / over-age | You already paid the queue |

Yanacek's layering: the hop in front caps the extreme; the **server still takes some excess** so it can log client / operation / why. **Health checks sit outside the shed.** Verified:

- Yanacek: the LB ping is the *most important* request; proxy `max_connections` must stay **below** listener threads / FDs so the ping still fits. Then humans over crawlers.
- Envoy admission-control (1.40.0-dev): **"Health check traffic does not count towards any of the filter’s measurements."**
- Envoy adaptive-concurrency: put the filter **after** the healthcheck filter so pings are not sampled into minRTT.

A shedder that trips the LB unhealthy threshold **reduces capacity** — the opposite of protection. CLB **surge-queued** excess; ALB **rejects** it.

## Queue discipline: FIFO, LIFO, CoDel

| Discipline | When it wins | Source |
|---|---|---|
| **FIFO** | Fairness; protocols that cannot reorder (HTTP/1.1 pipelining) | Yanacek |
| **LIFO / adaptive LIFO** | Newest work is still inside the client timeout; oldest is abandoned | Yanacek; *Fail at Scale*; SRE ch. 22 |
| **CoDel** | Bound *sojourn time*, not length. TARGET 5 ms, INTERVAL 100 ms | RFC 8289; Facebook used the same pair |
| **Queue-age bound** | Dequeue, measure wait, drop if older than remaining deadline or a TTL | Yanacek; SRE ch. 22 |
| **Length bound** | Steady traffic: **≤ ~50% of pool size** | SRE ch. 22 |
| **No queue** | Fail over instead of waiting | Gmail (SRE ch. 22) |

Bound **time** as well as slots; assume a queue you have not found yet. Hébert, "Queues Don't Fix Overload" (2014-11-19): an unbounded buffer in front of a bottleneck buys time, then fails rarer-and-worse.

## Adaptive concurrency

A *static* in-flight cap is a [bulkhead](Bulkhead.md). Adaptive concurrency **moves** the cap from measured latency so the same binary works across hardware and diurnal mix. Limit ≈ RPS × latency (Little), steered by a delay/loss controller.

| System | Controller | Defaults / claims that matter | Reject |
|---|---|---|---|
| **Netflix concurrency-limits 0.5.4** (2025-12-08) | Server: **Vegas** (α = 3·log₁₀ L, β = 6·log₁₀ L). Also Gradient, Gradient2 (gradient clamped [0.5, 1.0]; default `queueSize` **4**, not the 2018 `√limit`), AIMD (+1 / ×0.9) | README: live **0.9** / batch **0.1**; unidentified traffic uses **excess only**. Netflix retired Hystrix in favour of this family | gRPC `UNAVAILABLE` |
| **Netflix PlayAPI (2024-06-25)** | Partitioned limiter on `X-Netflix.Request-Name`: **user-initiated = 1.0**, **pre-fetch = 0.0** (excess). Header-only — rejected requests never parse a body | 12× Android prefetch spike: prefetch availability **20%**, user-initiated **> 99.4%**, **> 50%** of requests throttled. Follow-on buckets CRITICAL / DEGRADED / BEST_EFFORT / BULK. CPU shed **after** autoscale (experiment: noncritical **60%**, critical **80%**, cluster that scales at **45%**) | filter class named; gRPC integration documents `UNAVAILABLE` |
| **Envoy adaptive-concurrency** (1.40.0-dev proto) | `gradient = (minRTT + B) / sampleRTT`, `B = minRTT × buffer_pct`; `limit_new = gradient × limit_old + √limit` | p50; `max_concurrency_limit` **1000**; `request_count` **50**; jitter **15%**; `min_concurrency` **3** (pinned during minRTT); buffer **25%**. Remeasure if the limit sits at minimum for **5 consecutive** windows. Filter must see **every** request | **503** (forced if configured < 400) |
| **Uber Cinnamon** (2023-11-22) | PID rejector on queue inflow/outflow + modified TCP-Vegas inflight + 6 tiers × 128 cohorts = **768** priorities via Jaeger | No config; queue timeout **~33%** of RPC timeout; empty-queue window **~10 s**. Claims: **~1 µs** overhead; **P50 +50% at 300% overload**. Vs QALM/CoDel, which oscillated and at 3 000 RPS held only **~40%** of capacity | page wording: "rate limiting error" |

Netflix names the two anti-patterns: **no shedding** (death spiral) and **congestive failure** (successful RPS *drops* after the limiter engages — the reject path ate the CPU).

## 503 vs 429 — and vs a degraded response

| Signal | Means | Owner |
|---|---|---|
| **503** (+ optional `Retry-After`) | *We* are short. Anyone may be rejected. | **This note** |
| **429** (+ optional `Retry-After`, RateLimit headers) | *You* exceeded *your* quota. Others may still pass. | [C4](RateLimiting.md) |
| gRPC `UNAVAILABLE` / `RESOURCE_EXHAUSTED` | Overload vs quota; classify before the [breaker](CircuitBreaker.md) | C1 + C10 |
| SRE "overloaded; don't retry" | Whole datacenter looks sick; bubble up | [C2](RetryBackoff.md) |
| Connection refuse / GOAWAY | Cheaper than a status line | edge |
| Smaller index / stale body / cheaper ranker | Request *accepted*; work *shrunk* | [C11](GracefulDegradation.md) |

Kubernetes APF `type: Reject` returns **429** + adaptive `Retry-After` (per-level dropped-request tracker; the KEP-era default of `1` was replaced — PR 117547). APF is **quota-shaped fairness** at the apiserver, not a public-API 503 template. A 503 without a hint is **not** a license to retry immediately — honour `Retry-After` when short, then the [C2](RetryBackoff.md) budget.

Provider 529 / 503 "overloaded" is this pattern (service short). Provider 429 with `retry-after` is [C4](RateLimiting.md) scoped to the key / tenant / model. Do not fold either into a degraded *answer* on the same request — that is [C11](GracefulDegradation.md).

## Backpressure vs shed

Backpressure issues *credit*; the producer may not exceed it. Shedding *drops*. Backpressure wins when the producer is yours and can wait (a pipeline, a consumer group). It is the **wrong** tool for a synchronous RPC whose caller will time out and retry: a bounded wait becomes a hidden queue, then a retry storm. For RPC, **shed**.

| Layer | Credit / pull | What "full" does |
|---|---|---|
| TCP (RFC 9293) | 16-bit receive window (scale via RFC 7323) | Sender stops; persist-timer probes |
| **HTTP/2 (RFC 9113)** | Stream **and** connection windows, both start **65 535**. Only DATA consumes. `SETTINGS_INITIAL_WINDOW_SIZE` changes stream windows only | DATA stalls. Flow control is **per hop** — a buffering proxy **re-issues credit** regardless of the real consumer. NGINX `proxy_buffering` default **on** (memory + up to `proxy_max_temp_file_size` **1024m** of disk per response) |
| Reactive Streams 1.0.4 | `request(n)` demand | `onNext` ≤ demand; `request(Long.MAX_VALUE)` is the documented opt-out back to push |
| Node streams (v26.8.2) | `highWaterMark` 16 objects / **64 KiB** (16 KiB Windows) | `write() === false` → wait for `'drain'`; ignore → "buffer … until maximum memory usage occurs" |
| Kafka 4.1 consumer | `max.poll.records` **500**; `fetch.max.bytes` **50 MiB** | Slow `poll()` → `max.poll.interval.ms` **300 s** → group rebalance |

## Verified defaults (2026-09-13)

| System | Mechanism | Defaults worth knowing | Reject |
|---|---|---|---|
| Envoy overload manager 1.40.0-dev | Resource monitor → action / load-shed point | **Off** until Bootstrap `overload_manager` is set. Docs example: disable keepalive at heap **0.92**, stop accepting at **0.95**. `global_downstream_max_connections` unset = **no global cap** | 503 / close / GOAWAY |
| Envoy admission-control **proto** | Per-worker success-rate shed | `sampling_window` **30 s**; `aggression` **1.0**; `sr_threshold` **95%**; `rps_threshold` **0**; `max_rejection_probability` **80%** (so the estimate can recover). HTTP success default **< 500**; health checks excluded. Docs *example* 60 s / rps 1 / max 95% is **not** the proto | 503 |
| Envoy cluster "circuit breaking" | Concurrency *limits*, not a trip | `max_pending_requests` **1024**, `max_requests` **1024** ([breaker](CircuitBreaker.md)) | 503 + `x-envoy-overloaded` |
| Kubernetes APF (GA 1.29) | Shuffle-shard + fair queue | `Reject` or `Queue`; seats = `--max-requests-inflight` + `--max-mutating-requests-inflight` | **429** + adaptive `Retry-After` |
| SRE ch. 21–22 | Criticality + queue bound | K = **2**, 2-minute window; queue **≤ ~50%** of pool | 503 / "don't retry" |

Istio `connectionPool` defaults remain **2³²−1** (effectively unlimited) — a sidecar is not a shedder until you set the cap.

## Observability

Emit **split by priority / partition**, and **never mix reject latency into the success histogram** (Yanacek):

| Signal | Why |
|---|---|
| Offered RPS vs **goodput** (success ∧ under SLO latency) | The plateau vs collapse shape |
| Shed count / rate by class | Who paid; congestive-failure check (success RPS must not fall) |
| In-flight vs current limit; Envoy `concurrency_limit`, `gradient`, `min_rtt_msecs` | Controller health |
| Queue depth **and** queue age (p50/p99) | Length-only hides a 10 s sojourn |
| Reject-path CPU / `rq_rejected` / `rq_blocked` | Amdahl on the shed itself |
| Client-perceived availability; health-check success vs data-plane shed | Server 200s after the caller timed out are not goodput; proof the ping is exempt |
| Autoscaling signal vs shed rate | Same-threshold deadlock |

Envoy: `http.<prefix>.admission_control.{rq_rejected,rq_success,rq_failure}`; `http.<prefix>.adaptive_concurrency.gradient_controller.{rq_blocked,concurrency_limit,gradient,min_rtt_msecs,sample_rtt_msecs,min_rtt_calculation_active}`. Alert on *goodput drop*, *shed-rate step-change*, and *health-check failure during a shed*.

## Tuning

| Knob | Too aggressive | Too lax | Starting point |
|---|---|---|---|
| In-flight / concurrency limit | False 503s starve autoscaling | Queue forms; goodput collapses | Adaptive (Vegas / Gradient2 / Envoy / Cinnamon); static caps belong to [C8](Bulkhead.md) |
| Queue length | Honest bursts rejected | SRE: 10× pool × 100 ms = +1 s before work starts | ≤ 50% of pool for steady RPC |
| Queue age / CoDel TARGET | Sheds healthy jitter | Serves answers nobody will read | 5 ms / 100 ms at the hop; looser at RPC (see calibration) |
| LIFO vs FIFO | LIFO starves the oldest (pagination / `end()`) | FIFO finishes abandoned work | Adaptive LIFO only when the queue *forms* |
| Priority / partition | Everything is critical = nothing is | Idle partitions waste capacity | Guarantee 1.0 to user-initiated / `CRITICAL`; 0.0 (excess) to prefetch / `BULK` |
| Admission `sr_threshold` / reject cap | Sheds on noise; estimate cannot recover | Never engages; overload leaks | Envoy proto 95% / **80%** cap |
| Health-check exemption | Missed ping shrinks capacity | Unhealthy hosts keep taking work ([C3](Failover.md)) | Filters *after* the healthcheck filter |
| CPU shed vs autoscale | Shed eats the scale-out signal | Metastable zone entered first | Shed *above* the scale target (Netflix 60/80 vs 45) |

Load-test **past** the plateau. If goodput *falls*, the reject path is too expensive — fix logging/socket work before tightening thresholds. Return **503 + `Retry-After`** (delay-seconds) on capacity sheds; 429 only for [C4](RateLimiting.md) quota.

## Where it lives

| Deployment | What it sheds | Trade-off |
|---|---|---|
| Edge WAF / API Gateway / CloudFront | Volume | Cheap; blind to criticality unless you tag at the edge |
| Envoy overload manager | Process-level memory / conn pressure | Must be turned on; 503 before filters |
| Envoy admission / adaptive-concurrency | Per-proxy, per-cluster | Uncoordinated across replicas; minRTT window injects 503s |
| In-process (concurrency-limits, Cinnamon) | Knows headers / priority | Per instance; fleet reaction is slow |
| Kafka pause / Reactive Streams / H2 window | Producer wait | Wrong for sync RPC |
| Client adaptive throttling (SRE) | Local reject | Needs enough traffic for a 2-minute view |

## Worked calibration — checkout API

Constraints are a **design drill**, not a vendor SLA. Method: Yanacek plateau-test [15] + SRE queue ≤ 50% + Netflix 1.0 / 0.0 + Envoy proto defaults + remaining deadline from [C7](TimeoutsDeadlines.md).

Measured on one warmed checkout instance, client-side (drill numbers): user-initiated `POST /pay` 400 rps, healthy p99 180 ms, SLO 99.5% ≤ 300 ms; prefetch `GET /pay/quote` 800 rps, p99 90 ms, best-effort; ALB health check 1 / 30 s — **never shed**. Instance goodput plateau (mixed) **~520 rps**. Handler threads **64**. Little: 520 × 0.18 s ≈ **94** in-flight at the pay p99 — the static cap must sit *above* that or we false-shed in the healthy region.

| Knob | Choice | Why |
|---|---|---|
| Adaptive limit | Envoy gradient or Gradient2; `max_concurrency_limit` **200**; `min_concurrency` **3** | 200 > 94 so the healthy mix is unhindered |
| Queue length | **32** (50% of 64) | Steady-traffic rule; 32 × 180 ms ≈ 5.8 s of FIFO wait already exceeds the 300 ms SLO — a *burst* cap, not a latency budget |
| Queue age | Drop at dequeue if wait > **50 ms** or remaining deadline < expected service (p99 180 ms) | Yanacek TTL; CoDel-class sojourn, loosened from 5 ms because this is an RPC, not a DC hop |
| Discipline | FIFO while depth < 8; **LIFO** above (HTTP/2 to the instance) | Facebook adaptive-LIFO; pay is not pipelined HTTP/1.1 |
| Partition | `user-initiated` **1.0**, `pre-fetch` **0.0** on `X-Request-Class` | PlayAPI shape: prefetch may fall to ~20% under a 12× spike; pay stays on the 99.5% SLO |
| Health | Admission/adaptive filters **after** the healthcheck filter | Yanacek + Envoy docs |
| Response | **503** + `Retry-After: 2` on capacity shed; **429** only if a *tenant* bucket ([C4](RateLimiting.md)) tripped first | RFC 9110 |
| Autoscaling | CPU target **45%**; progressive shed of prefetch from **60%**, pay from **80%** | Netflix experiment — shed *after* the scale signal |
| Retry | Honour `Retry-After`; [C2](RetryBackoff.md) 10% budget; no retry of `/pay` without an [idempotency](Idempotency.md) key | A 503 on capture is not a signal to double-charge |
| Deadline | Edge 3 s → remaining ~2.9 s; drop if remaining < 200 ms at dequeue | Doomed work is not goodput |

Load-test gate: raise offered prefetch to **6×** with scale-out *disabled*. Expect: pay goodput flat near 400 rps, pay p99 < 300 ms, prefetch collapsing, health checks **100%**, success-path p50 **not** improved by fast 503s (those series are separate). If pay goodput *falls*, the reject path is congestive — fix that before shipping.

## Testing and operating

- Load-test **past** the knee and verify: goodput plateaus (not collapses), sheds are tiered, accepted-request p99 holds, health checks stay green. A shedder proven only below capacity is unproven.
- Verify recovery: after the spike, rejection probability falls on its own (the 80% cap exists for this) and LIFO flips back to FIFO.
- Inject a slow consumer against every backpressured stream and assert bounded memory + upstream slowdown, not buffer growth.
- Confirm the shed path is cheap: profile CPU per rejection. An expensive 503 is a self-DoS at scale (Netflix congestive failure; SRE reject-CPU spiral).
- Envoy minRTT windows pin concurrency to 3 and 503 — expected; retry *other* hosts (`previous_hosts` predicate).

## Failure modes

1. **No shed → collapse.** Netflix anti-pattern 1; Yanacek "fails in the least desirable way."
2. **Congestive failure.** Reject path more expensive than serve. Successful RPS drops after the limiter engages.
3. **Shed hides latency.** Fast 503s dominate server p50. Measure goodput and *success-only* latency.
4. **Shed starves autoscaling.** Same CPU target on shed and scale-out.
5. **Health-check inversion.** Shedding pings ejects the instance and concentrates load on survivors.
6. **Wrong code: 429 vs 503.** A 429 on *capacity* trains clients to wait out *their* quota while the fleet is sick, and trains [breakers](CircuitBreaker.md) to trip per-caller.
7. **Retry inversion.** 503 without `Retry-After` + stacked retries → the sustaining loop in [7](../data-intensive-design/nfr-references.md)/[9](../data-intensive-design/nfr-references.md) and [C2](RetryBackoff.md). Honour "don't retry."
8. **FIFO on abandoned work.** A 10 s queued search (SRE ch. 22) — the user already refreshed.
9. **LIFO starvation.** Oldest pagination / `end()` never finishes (Yanacek's start/end and page-N priority fight LIFO).
10. **Unbounded buffer labelled "backpressure."** Node ignore-`drain`; RxJava `BUFFER`; NGINX 1 GB disk spool.
11. **CoDel oscillation.** QALM at deep overload rejected nearly everything — Cinnamon's reason to exist.
12. **Static max-connections as the only control.** Yanacek's opening failure.
13. **Proxy-buffered "backpressure."** HTTP/2 credit stops at each hop; a buffering intermediary silently absorbs the signal.
14. **Rebalance storms.** Kafka consumers that blow `max.poll.interval.ms` turn slowness into partition churn.

**When not to use shedding.** Tenant fairness and product quotas → [C4](RateLimiting.md) (429). A single dependency hanging your threads → [C1](CircuitBreaker.md) + [C7](TimeoutsDeadlines.md), not a global 503. A full compartment of *one* pool → [C8](Bulkhead.md). Optional features you can skip while still answering → [C11](GracefulDegradation.md). A producer that can wait on a credit window → backpressure / [A2](PubSubQueues.md). In-process function calls. Work that *must* finish after the client is gone (SRE's checkpointed catchup). A tight adaptive cap is the wrong tool for the first request on a cold instance (Envoy minRTT) and for mixed request costs on one limiter (SRE: QPS is a bad unit — partition or cost-weight).

## Trade-offs

| Buy | Pay |
|---|---|
| Goodput plateaus past the knee | Work is dropped on purpose — a product decision per tier |
| Accepted-request latency stays inside the SLO | Priority taxonomy to define, tag, and propagate |
| Tuning-free disciplines exist (CoDel, adaptive LIFO) | Controllers and caps to keep the shedder itself stable |
| Adaptive concurrency tracks hardware and mix | minRTT dips, uncoordinated replicas, mixed-cost blindness |
| Backpressure: lossless slowdown for elastic producers | Only works end-to-end; one buffer in the path breaks it |

The [limiter](RateLimiting.md) decides **how much a caller may ask**. The [bulkhead](Bulkhead.md) decides **how much may run at once**. Shedding and backpressure decide **what the server drops or slows when reality exceeds both**. [Degradation](GracefulDegradation.md) decides **how much smaller an accepted response may be**. The [breaker](CircuitBreaker.md) decides **whether the client should call at all**. Timeouts decide **how long to wait**; retries decide **whether to try again**. Coordinate all six.

## Sources

Verified 2026-09-13; the full URL list, per-claim provenance, and items deliberately left out are in the [catalog research note](../../docs/research/sysdesign/c10-load-shedding-external-research.md). Envoy action names, CoDel TARGET/INTERVAL, APF seat model, Reactive Streams rules, Node `highWaterMark`, and Kafka 4.1 pull defaults also live in the [first-pass note](../../docs/research/sysdesign/load-shedding-backpressure-external-research.md). Items already cited in this tree are referenced by their number in [nfr-references.md](../data-intensive-design/nfr-references.md).

- Canon: Yanacek [15]; SRE book ch. 21–22; RFC 9110 §10.2.3 / §15.6.4; RFC 6585 (429 — [C4](RateLimiting.md)); Brooker utilization (2021-08-05); Nygard [12]; Sackman [16]; Cvet [1]; [performance.md](../data-intensive-design/performance.md).
- Adaptive / prioritized: Netflix PlayAPI 2024-06-25; concurrency-limits 0.5.4 (Vegas / Gradient2 / AIMD; issue #189); Uber Cinnamon 2023-11-22; Netflix 2018 algorithms via the [breaker research](../../docs/research/sysdesign/circuit-breaker-external-research.md).
- Envoy / mesh: overload manager, admission-control proto (30 s / 95% / 80%), adaptive-concurrency proto (p50 / 1000 / 3 / 25%), cluster concurrency limits.
- Queues / AQM / APF / backpressure: RFC 8289; *Fail at Scale* (ACM Queue 2015, archive); Kubernetes APF GA 1.29 + PR 117547; Hébert 2014-11-19; RFC 9293; RFC 9113; NGINX proxy buffering; Reactive Streams 1.0.4; Node stream v26.8.2; Kafka 4.1.
- Complements: [RetryBackoff.md](RetryBackoff.md) (`Retry-After`, 10% budget, "don't retry"); [CircuitBreaker.md](CircuitBreaker.md) (accelerated open on 503); [Bulkhead.md](Bulkhead.md) (static occupancy); [GracefulDegradation.md](GracefulDegradation.md) (brownout / optional code); [TimeoutsDeadlines.md](TimeoutsDeadlines.md) (remaining deadline as the doomed-work predicate).
