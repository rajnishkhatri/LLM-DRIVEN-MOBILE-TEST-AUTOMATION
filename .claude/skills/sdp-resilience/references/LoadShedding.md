---
id: C10
title: 'Load shedding'
description: >-
  Clinic card for load shedding: when offered load exceeds usable capacity, shed
  cheaply by measured priority so goodput plateaus instead of collapsing, or push
  back with credit-based backpressure when the producer can wait. Diagnose the
  overload signal → prioritize → tune admission, queue discipline, and adaptive
  concurrency → verify goodput holds. Distinct from rate limiting (C4, quota-shaped
  429) and graceful degradation (C11, a smaller accepted response). Covers
  Yanacek shed-early and health-check priority, SRE criticality tiers, CoDel and
  adaptive LIFO, adaptive concurrency controllers, HTTP/2 flow control, verified
  defaults, a checkout calibration, and shedding around LLM provider APIs.
tags: [system-design-patterns, resilience, load-shedding, backpressure]
---

# Load shedding

**See also (non-load-bearing bonus — this card stands alone):** the source Concept [`LoadShedding.md`](../../../../cases/SystemDesignPatterns/LoadShedding.md) for full lineage, extra diagrams, and the external research notes behind these numbers. You do not need to open it to use this card.

When offered load exceeds what a server can finish *usefully*, it has three honest moves: **shed** (drop some work, cheaply and by priority), **push back** (make producers slow down), or **degrade** (do less *per accepted request* — C11, graceful degradation). Everything else is a queue, and a queue only converts overload into latency, memory, and a later, bigger failure. This card owns the first two. Rate limiting (C4) is admission by *declared policy* and answers **429** when *this caller* exceeded *its* allocation; shedding is admission by *measured capacity* and answers **503** when the *service* is short for everyone. Degradation shrinks the *response*; shedding drops or delays the *request*. Quality attributes in play: **goodput under overload** (useful work completed inside the client's patience), **latency integrity** for what is accepted, and survival of the metastable-failure zone. The costs: dropped work by design, priority plumbing to build and keep correct, and metrics that lie if rejections leak into the success histogram.

## Lineage and vocabulary

- **Yanacek, *Using load shedding to avoid overload*:** **goodput ≠ throughput**. Throughput is offered (or accepted) RPS, including work that will time out; goodput is the subset finished without error *and* inside a latency the client can still use. Max-connections as the only knob is too imprecise. Shed **early and cheaply**; measure **client-perceived** availability and latency; **do not fold reject latency into the success histogram** (60% shed can make p50 look excellent). **Prioritize the load-balancer ping** — a missed health check shrinks the fleet, the last thing a brownout wants. Then: humans over crawlers; in-quota over burst; `end()` over `start()`; page *N* over page 1. Drop doomed work (remaining deadline, queue *age*, LIFO when the protocol allows). Hidden queues (TCP buffers, executor queues, CLB surge queues) are everywhere. Shed on the same CPU target as autoscaling **starves the scale-out signal**. False-positive target: **zero**.
- **Google SRE ch. 21–22:** QPS is a poor capacity unit — provision on resources (usually CPU). Criticality `CRITICAL_PLUS` / `CRITICAL` (production default) / `SHEDDABLE_PLUS` / `SHEDDABLE`, **propagated automatically**. Preferred utilization signal: **executor load average** (decayed active threads), shed when it exceeds processors. Rejections still burn CPU — a backend can be overloaded doing nothing but rejecting, so push shedding **client-ward** (adaptive throttling, last **two minutes**, multiplier **K ≈ 2**). Queue length **≤ ~50% of the pool** for steady traffic; Gmail often uses **queueless** servers. FIFO → **LIFO or CoDel**. Deadline check **after dequeue**. The cheaper-ranker / smaller-index move is **C11**, not this card.
- **Facebook, "Fail at Scale" (Maurer 2015) and CoDel (RFC 8289):** two tuning-free disciplines. **Controlled delay** — if the queue has not drained recently, new entries get only **M = 5 ms** of queue budget (**N = 100 ms** otherwise); accept slightly more than capacity so the worker never goes idle. **Adaptive LIFO** — a forming queue flips to newest-first (the oldest has likely been abandoned). They compose. RFC 8289 is the same idea at the packet layer: control **sojourn time** (TARGET **SHOULD be 5 ms**, INTERVAL **100 ms**), not queue length.
- **Nygard** lists *Shed Load* and *Create Back Pressure* among the Stability Patterns. **Sackman** and **Cvet** supply the backpressure / fan-in vocabulary; this card does not re-derive them.
- **Wire signal.** RFC 9110 §15.6.4: **503** = temporary overload or maintenance; the server **MAY** send `Retry-After` (§10.2.3, HTTP-date or delay-seconds) and **need not** use 503 — it may refuse the connection. **429** stays with rate limiting (C4).

## Goodput vs throughput

```
offered RPS ──► [admit / shed] ──► accepted ──► finish inside timeout? ──► goodput
                      │
                      └── cheap 503 / window-close / nack
```

Without a bound, utilization ρ → 1 and queueing delay explodes. Brooker (2021-08-05): M/M/1 occupancy `E[N] = ρ/(1−ρ)` is **1 at ρ = 0.5** and **99 at ρ = 0.99**; the same 1/(1−ρ) blow-up hits time-in-system, and **high percentiles go first** — tail latency is the leading indicator of overload, well before errors. Shedding is the cut: refuse work that would only finish after the client has gone.

Yanacek's load-test shape: goodput **plateaus** near full utilization and stays flat as offered load keeps rising. If availability falls toward zero, the service still needs a shedder. Little's law (`L = λW`) converts any latency target into the in-flight cap that a bulkhead (C8) or adaptive limiter enforces.

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
- Envoy admission-control (1.40.0-dev): "Health check traffic does not count towards any of the filter's measurements."
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

A *static* in-flight cap is a bulkhead (C8). Adaptive concurrency **moves** the cap from measured latency so the same binary works across hardware and diurnal mix. Limit ≈ RPS × latency (Little), steered by a delay/loss controller. The verified controller shapes and their defaults are in *Configuration & verified defaults* below.

Netflix names the two anti-patterns: **no shedding** (death spiral) and **congestive failure** (successful RPS *drops* after the limiter engages — the reject path ate the CPU).

## 503 vs 429 — and vs a degraded response

| Signal | Means | Owner |
|---|---|---|
| **503** (+ optional `Retry-After`) | *We* are short. Anyone may be rejected. | **This card (C10)** |
| **429** (+ optional `Retry-After`, RateLimit headers) | *You* exceeded *your* quota. Others may still pass. | C4 |
| gRPC `UNAVAILABLE` / `RESOURCE_EXHAUSTED` | Overload vs quota; classify before the breaker | C1 + C10 |
| SRE "overloaded; don't retry" | Whole datacenter looks sick; bubble up | C2 |
| Connection refuse / GOAWAY | Cheaper than a status line | edge |
| Smaller index / stale body / cheaper ranker | Request *accepted*; work *shrunk* | C11 |

Kubernetes APF `type: Reject` returns **429** + adaptive `Retry-After` (per-level dropped-request tracker; the KEP-era default of `1` was replaced — PR 117547). APF is **quota-shaped fairness** at the apiserver, not a public-API 503 template. A 503 without a hint is **not** a license to retry immediately — honour `Retry-After` when short, then the C2 (retry & backoff) budget.

## Backpressure vs shed

Backpressure issues *credit*; the producer may not exceed it. Shedding *drops*. Backpressure wins when the producer is yours and can wait (a pipeline, a consumer group). It is the **wrong** tool for a synchronous RPC whose caller will time out and retry: a bounded wait becomes a hidden queue, then a retry storm. For RPC, **shed**.

| Layer | Credit / pull | What "full" does |
|---|---|---|
| TCP (RFC 9293) | 16-bit receive window (scale via RFC 7323) | Sender stops; persist-timer probes |
| **HTTP/2 (RFC 9113)** | Stream **and** connection windows, both start **65 535**. Only DATA consumes. `SETTINGS_INITIAL_WINDOW_SIZE` changes stream windows only | DATA stalls. Flow control is **per hop** — a buffering proxy **re-issues credit** regardless of the real consumer. NGINX `proxy_buffering` default **on** (memory + up to `proxy_max_temp_file_size` **1024m** of disk per response) |
| Reactive Streams 1.0.4 | `request(n)` demand | `onNext` ≤ demand; `request(Long.MAX_VALUE)` is the documented opt-out back to push |
| Node streams (v26.8.2) | `highWaterMark` 16 objects / **64 KiB** (16 KiB Windows) | `write() === false` → wait for `'drain'`; ignore → "buffer … until maximum memory usage occurs" |
| Kafka 4.1 consumer | `max.poll.records` **500**; `fetch.max.bytes` **50 MiB** | Slow `poll()` → `max.poll.interval.ms` **300 s** → group rebalance |

## Configuration & verified defaults

Verified 2026-09-13.

| System | Mechanism | Verified defaults | Reject |
|---|---|---|---|
| Envoy overload manager 1.40.0-dev | Resource monitor → action / load-shed point | **Off** until Bootstrap `overload_manager` is set. Docs example: disable keepalive at heap **0.92**, stop accepting at **0.95**. `global_downstream_max_connections` unset = **no global cap** | 503 / close / GOAWAY |
| Envoy admission-control **proto** | Per-worker success-rate shed | `sampling_window` **30 s**; `aggression` **1.0**; `sr_threshold` **95%**; `rps_threshold` **0**; `max_rejection_probability` **80%** (so the estimate can recover). HTTP success default **< 500**; health checks excluded. Docs *example* 60 s / rps 1 / max 95% is **not** the proto default | 503 |
| Envoy adaptive-concurrency **proto** | `gradient = (minRTT + B) / sampleRTT`, `B = minRTT × buffer_pct`; `limit_new = gradient × limit_old + √limit` | Sampled at p50; `max_concurrency_limit` **1000**; `request_count` **50**; jitter **15%**; `min_concurrency` **3** (pinned during minRTT); buffer **25%**. Remeasure if the limit sits at minimum for **5 consecutive** windows. Filter must see **every** request | **503** (forced if configured < 400) |
| Envoy cluster "circuit breaking" | Concurrency *limits*, not a trip | `max_pending_requests` **1024**, `max_requests` **1024** (C1 territory) | 503 + `x-envoy-overloaded` |
| Kubernetes APF (GA 1.29) | Shuffle-shard + fair queue | `Reject` or `Queue`; seats = `--max-requests-inflight` + `--max-mutating-requests-inflight` | **429** + adaptive `Retry-After` |
| Google SRE ch. 21–22 | Criticality + queue bound | K = **2**, 2-minute window; queue **≤ ~50%** of pool | 503 / "don't retry" |
| Istio `connectionPool` | Per-sidecar concurrency cap | Defaults remain **2³²−1** (effectively unlimited) — a sidecar is not a shedder until you set the cap | n/a |
| **Netflix concurrency-limits 0.5.4** (2025-12-08) | Server: **Vegas** (α = 3·log₁₀ L, β = 6·log₁₀ L). Also Gradient, Gradient2 (gradient clamped [0.5, 1.0]; default `queueSize` **4**, not the 2018 `√limit`), AIMD (+1 / ×0.9) | Live **0.9** / batch **0.1**; unidentified traffic uses **excess only**. Netflix retired Hystrix in favour of this family | gRPC `UNAVAILABLE` |
| **Netflix PlayAPI** (2024-06-25) | Partitioned limiter on `X-Netflix.Request-Name`: **user-initiated = 1.0**, **pre-fetch = 0.0** (excess). Header-only — rejected requests never parse a body | 12× Android prefetch spike: prefetch availability **20%**, user-initiated **> 99.4%**, **> 50%** of requests throttled. Follow-on buckets CRITICAL / DEGRADED / BEST_EFFORT / BULK. CPU shed **after** autoscale (experiment: noncritical **60%**, critical **80%**, cluster that scales at **45%**) | filter class named; gRPC integration documents `UNAVAILABLE` |
| **Uber Cinnamon** (2023-11-22) | PID rejector on queue inflow/outflow + modified TCP-Vegas inflight + 6 tiers × 128 cohorts = **768** priorities via Jaeger | No config; queue timeout **~33%** of RPC timeout; empty-queue window **~10 s**. Claims: **~1 µs** overhead; **P50 +50% at 300% overload**. Vs QALM/CoDel, which oscillated and at 3 000 RPS held only **~40%** of capacity | page wording: "rate limiting error" |

## Where it lives

| Deployment | What it sheds | Trade-off |
|---|---|---|
| Edge WAF / API Gateway / CloudFront | Volume | Cheap; blind to criticality unless you tag at the edge |
| Envoy overload manager | Process-level memory / conn pressure | Must be turned on; 503 before filters |
| Envoy admission / adaptive-concurrency | Per-proxy, per-cluster | Uncoordinated across replicas; minRTT window injects 503s |
| In-process (concurrency-limits, Cinnamon) | Knows headers / priority | Per instance; fleet reaction is slow |
| Kafka pause / Reactive Streams / H2 window | Producer wait | Wrong for sync RPC |
| Client adaptive throttling (SRE) | Local reject | Needs enough traffic for a 2-minute view |

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
| In-flight / concurrency limit | False 503s starve autoscaling | Queue forms; goodput collapses | Adaptive (Vegas / Gradient2 / Envoy / Cinnamon); static caps belong to C8 (bulkhead) |
| Queue length | Honest bursts rejected | SRE: 10× pool × 100 ms = +1 s before work starts | ≤ 50% of pool for steady RPC |
| Queue age / CoDel TARGET | Sheds healthy jitter | Serves answers nobody will read | 5 ms / 100 ms at the hop; looser at RPC (see calibration) |
| LIFO vs FIFO | LIFO starves the oldest (pagination / `end()`) | FIFO finishes abandoned work | Adaptive LIFO only when the queue *forms* |
| Priority / partition | Everything is critical = nothing is | Idle partitions waste capacity | Guarantee 1.0 to user-initiated / `CRITICAL`; 0.0 (excess) to prefetch / `BULK` |
| Admission `sr_threshold` / reject cap | Sheds on noise; estimate cannot recover | Never engages; overload leaks | Envoy proto 95% / **80%** cap |
| Health-check exemption | Missed ping shrinks capacity | Unhealthy hosts keep taking work (C3, failover/health) | Filters *after* the healthcheck filter |
| CPU shed vs autoscale | Shed eats the scale-out signal | Metastable zone entered first | Shed *above* the scale target (Netflix 60/80 vs 45) |

Load-test **past** the plateau. If goodput *falls*, the reject path is too expensive — fix logging/socket work before tightening thresholds. Return **503 + `Retry-After`** (delay-seconds) on capacity sheds; 429 only for C4 (rate limiting) quota.

## Alternatives that beat load shedding

The shedder is a service-boundary admission control. Several situations want a different control instead — this is the "when NOT to use it" table.

| Situation | Prefer | Why |
|---|---|---|
| Tenant fairness / product quotas | Rate limiting (C4) | 429 by declared policy, not measured capacity |
| A single dependency hanging your threads | Circuit breaker (C1) + timeouts & deadlines (C7) | Isolate the one bad dependency; do not 503 the whole service for it |
| A full compartment of *one* pool | Bulkhead (C8) | Compartmentalize before shedding globally |
| Optional features you can skip while still answering | Graceful degradation (C11) | Shrink the response; keep answering |
| A producer that can wait on a credit window | Backpressure (A2, pub/sub & queues) | The producer is yours and can slow down instead of losing work |
| In-process function calls | Neither — this pattern is admission at a service boundary | There is no client to shed against |
| Work that *must* finish after the client is gone | SRE's checkpointed catchup, not a shedder | Shedding assumes the client stops caring; some batch work does not |
| First request on a cold instance | Loosen the adaptive cap; do not shed | Envoy's minRTT problem — a tight cap with no baseline mistakes a cold cache for overload |
| Mixed request costs on one limiter | Partition or cost-weight the limiter | SRE: QPS is a bad capacity unit across heterogeneous requests |

## Worked calibration — checkout API

Constraints are a **design drill**, not a vendor SLA. Method: Yanacek's plateau-test method + SRE queue ≤ 50% + Netflix 1.0 / 0.0 + Envoy proto defaults + remaining deadline from C7 (timeouts & deadlines).

Measured on one warmed checkout instance, client-side (drill numbers): user-initiated `POST /pay` 400 rps, healthy p99 180 ms, SLO 99.5% ≤ 300 ms; prefetch `GET /pay/quote` 800 rps, p99 90 ms, best-effort; ALB health check 1 / 30 s — **never shed**. Instance goodput plateau (mixed) **~520 rps**. Handler threads **64**. Little: 520 × 0.18 s ≈ **94** in-flight at the pay p99 — the static cap must sit *above* that or we false-shed in the healthy region.

| Knob | Choice | Why |
|---|---|---|
| Adaptive limit | Envoy gradient or Gradient2; `max_concurrency_limit` **200**; `min_concurrency` **3** | 200 > 94 so the healthy mix is unhindered |
| Queue length | **32** (50% of 64) | Steady-traffic rule; 32 × 180 ms ≈ 5.8 s of FIFO wait already exceeds the 300 ms SLO — a *burst* cap, not a latency budget |
| Queue age | Drop at dequeue if wait > **50 ms** or remaining deadline < expected service (p99 180 ms) | Yanacek TTL; CoDel-class sojourn, loosened from 5 ms because this is an RPC, not a DC hop |
| Discipline | FIFO while depth < 8; **LIFO** above (HTTP/2 to the instance) | Facebook adaptive-LIFO; pay is not pipelined HTTP/1.1 |
| Partition | `user-initiated` **1.0**, `pre-fetch` **0.0** on `X-Request-Class` | PlayAPI shape: prefetch may fall to ~20% under a 12× spike; pay stays on the 99.5% SLO |
| Health | Admission/adaptive filters **after** the healthcheck filter | Yanacek + Envoy docs |
| Response | **503** + `Retry-After: 2` on capacity shed; **429** only if a *tenant* bucket (C4) tripped first | RFC 9110 |
| Autoscaling | CPU target **45%**; progressive shed of prefetch from **60%**, pay from **80%** | Netflix experiment — shed *after* the scale signal |
| Retry | Honour `Retry-After`; C2 (retry & backoff) 10% budget; no retry of `/pay` without an idempotency (C9) key | A 503 on capture is not a signal to double-charge |
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
6. **Wrong code: 429 vs 503.** A 429 on *capacity* trains clients to wait out *their* quota while the fleet is sick, and trains breakers (C1) to trip per-caller.
7. **Retry inversion.** 503 without `Retry-After` + stacked retries → the sustaining loop that C2 (retry & backoff) exists to prevent. Honour "don't retry."
8. **FIFO on abandoned work.** A 10 s queued search (SRE ch. 22) — the user already refreshed.
9. **LIFO starvation.** Oldest pagination / `end()` never finishes (Yanacek's start/end and page-N priority fight LIFO).
10. **Unbounded buffer labelled "backpressure."** Node ignore-`drain`; RxJava `BUFFER`; NGINX 1 GB disk spool.
11. **CoDel oscillation.** QALM at deep overload rejected nearly everything — Cinnamon's reason to exist.
12. **Static max-connections as the only control.** Yanacek's opening failure.
13. **Proxy-buffered "backpressure."** HTTP/2 credit stops at each hop; a buffering intermediary silently absorbs the signal.
14. **Rebalance storms.** Kafka consumers that blow `max.poll.interval.ms` turn slowness into partition churn.

## Load shedding around LLM provider APIs

Model endpoints are usually the most expensive, slowest calls a service makes, and both directions of this pattern show up. As a **caller**, the provider is doing its own shedding: a 529 / 503 "overloaded" response is the provider's admission control saying it is short for everyone — treat it as **this pattern's signal, one hop further out**, not as a C4 quota (429) or a C11 degraded answer folded into the same response. As the **operator of a service that fronts an LLM provider**, you are the one who has to shed: the call is slow enough (seconds, sometimes tens of seconds) that an unbounded queue in front of it is exactly the "queues don't fix overload" failure this card warns about, and the cost per accepted request is high enough that admitting doomed work is expensive twice over — once for your own capacity, once for the provider's.

| Signal | Treatment |
|---|---|
| Provider 529 / 503 "overloaded" | This pattern's signal. Do not retry into it immediately; honour `Retry-After` when present, then fall to the C2 budget. |
| Provider 429 with `retry-after` | C4 territory (quota for your key / tenant / model), not this pattern — do not fold it into a shed decision. |
| Your own request queue for a model call | Bound by **age**, not only length — a queued generation the user already abandoned is doomed work by the same TTL logic as the checkout calibration. |
| Interactive vs background generation | Partition like Netflix PlayAPI: user-facing chat = **1.0** (guaranteed), batch / pre-generation / eval = **0.0** (excess, shed first). |
| Health check / liveness probe to your own service | Never shed — the same exemption as any other backend; a hung model call must not take the probe down with it. |

**Knobs.** Put the admission decision in front of the token-generation call, not after it starts — the expensive part is the call itself, so a cheap 503 before dequeuing beats an expensive one after a partial generation. Size the in-flight cap from Little's law using the *provider's* p99 latency, not your own service's normal p99 — a 20 s model call inflates the in-flight count for the same RPS far past what a database-backed endpoint would need. Prioritize by product tier the same way the checkout calibration prioritizes `/pay` over `/pay/quote`: paid or interactive traffic at 1.0, speculative or batch generation at 0.0. Return 503 + `Retry-After` on your own shed, kept distinct from a passed-through provider 429.

## Trade-offs

| Buy | Pay |
|---|---|
| Goodput plateaus past the knee | Work is dropped on purpose — a product decision per tier |
| Accepted-request latency stays inside the SLO | Priority taxonomy to define, tag, and propagate |
| Tuning-free disciplines exist (CoDel, adaptive LIFO) | Controllers and caps to keep the shedder itself stable |
| Adaptive concurrency tracks hardware and mix | minRTT dips, uncoordinated replicas, mixed-cost blindness |
| Backpressure: lossless slowdown for elastic producers | Only works end-to-end; one buffer in the path breaks it |

The rate limiter (C4) decides **how much a caller may ask**. The bulkhead (C8) decides **how much may run at once**. Shedding and backpressure decide **what the server drops or slows when reality exceeds both**. Graceful degradation (C11) decides **how much smaller an accepted response may be**. The circuit breaker (C1) decides **whether the client should call at all**. Timeouts (C7) decide **how long to wait**; retries (C2) decide **whether to try again**. Coordinate all six.

## Sources

Verified 2026-09-13; numbers, defaults, and failure modes below are carried from the source Concept's verified research — do not soften them.

- **Canon:** Yanacek, *Using load shedding to avoid overload*; Google SRE book ch. 21–22; RFC 9110 §10.2.3 / §15.6.4; RFC 6585 (429 — rate limiting, C4); Brooker, utilization analysis (2021-08-05); Nygard, *Release It!*; Sackman; Cvet.
- **Adaptive / prioritized:** Netflix PlayAPI (2024-06-25); Netflix concurrency-limits 0.5.4 (Vegas / Gradient2 / AIMD; issue #189); Uber Cinnamon (2023-11-22); Netflix's 2018 limiter algorithms.
- **Envoy / mesh:** overload manager; admission-control proto (30 s / 95% / 80%); adaptive-concurrency proto (p50 / 1000 / 3 / 25%); cluster concurrency limits.
- **Queues / AQM / APF / backpressure:** RFC 8289 (CoDel); Facebook, *Fail at Scale* (ACM Queue, 2015); Kubernetes APF GA 1.29 + PR 117547; Hébert, *Queues Don't Fix Overload* (2014-11-19); RFC 9293 (TCP); RFC 9113 (HTTP/2); NGINX proxy-buffering docs; Reactive Streams 1.0.4; Node.js streams v26.8.2; Kafka 4.1 consumer docs.
- **Complements:** rate limiting (C4) for 429 / quota; circuit breaker (C1) for accelerated open on 503; bulkhead (C8) for static occupancy; graceful degradation (C11) for brownout / optional-code shedding; timeouts & deadlines (C7) for the remaining-deadline doomed-work predicate.
