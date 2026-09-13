---
type: research
title: 'Load shedding & backpressure — external research (2026-09-13)'
description: >-
  Group C catalog evidence pass for C10: goodput vs throughput, shed-early
  and health-check priority, LIFO vs FIFO and queue bounds, Netflix/Uber
  adaptive concurrency, 503 + Retry-After, and a worked calibration.
tags: [research, system-design-patterns, C10, c10-load-shedding]
---

# C10 Load shedding & backpressure — catalog research (2026-09-13)

> **What this is.** The catalog evidence pass for **C10**. It **links** the
> same-day first pass [load-shedding-backpressure-external-research.md](load-shedding-backpressure-external-research.md)
> (Envoy overload manager + admission-control proto defaults, CoDel RFC 8289,
> Facebook adaptive-LIFO, Kubernetes APF, TCP/H2/Reactive-Streams/Node/Kafka
> backpressure, Brooker M/M/1, brownout, Hébert) and **deepens** the policy
> to the Group C / [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md)
> bar: mechanics and variants, knobs with verified defaults, observability,
> tuning, a worked calibration, failure modes, sources. Yanacek and Brooker
> are **cited**, not re-derived — [nfr-references.md](../../../cases/data-intensive-design/nfr-references.md)
> [15], [16], [1], [8], [11], [14]; queueing already lives in
> [performance.md](../../../cases/data-intensive-design/performance.md).
>
> **Method.** Primary pages fetched 2026-09-13. Numbers and option names
> reproduced exactly; everything else paraphrased. Facts marked **[→C10-1]**
> are in the first-pass note and not re-fetched here. Facts marked
> **[→breaker]** / **[→C2]** / **[→C7]** / **[→C4]** / **[→C8]** / **[→A2]**
> are in the sibling notes named in §8. Unverifiable items are in §10 and
> are **not** asserted as fact.

---

## 1. Scope and non-goals

**Owns.** What a *server* (or the hop immediately in front of it) does when
offered load exceeds the work it can finish *usefully*: drop or slow
producers so **goodput** plateaus instead of collapsing. Variants: static
concurrency / queue-time bounds; adaptive concurrency (Netflix
concurrency-limits, Envoy gradient filter, Uber Cinnamon); prioritized /
partitioned shedding; success-rate admission control; protocol
backpressure (TCP rwnd, HTTP/2 windows, Reactive Streams `request(n)`,
Kafka pull). Wire signal: **HTTP 503 + `Retry-After`**. Knobs, placement,
observability, a worked calibration.

**Does not own.**

| Sibling | Why it stays there |
|---|---|
| **C4** | *Quota vs shed.* 429 = *this caller* exceeded *its* allocation. 503 = the *service* is short for everyone. Token/leaky/GCRA, RateLimit headers, fail-open stores. |
| **C1** | Client-side trip on a *failing callee*. This note is the callee protecting *itself*. |
| **C2** | Whether / how to retry a 503. Honour `Retry-After`; do not rewrite jitter or the 10% budget. |
| **C8** | A full bulkhead *rejects when its compartment is full*. The shedder *chooses what to drop* once some compartment (or the host) is full. |
| **C11** | Shrink work per accepted request (brownout, optional features). C10 drops or delays the request. |
| **C7** | How the deadline is chosen and propagated. C10 uses the remaining deadline to drop doomed work. |
| **A2** | Broker flow-control knobs (`basic.qos`, `max.poll.records`, pause/resume). Policy — what “full” means and what to refuse — lives here. |
| **C3** | Probe interval / timeout / fail-open. This note only requires that **health checks are never shed**. |

**Does not re-derive.** Yanacek [15]; Sackman *Pushing Back* [16]; Cvet
Twitter fan-in [1]; Brooker metastability / backoff / token-bucket
[8][11][14]; Nygard *Shed Load* / *Create Back Pressure* [12]; the
queueing + retry-storm paragraph in
[performance.md](../../../cases/data-intensive-design/performance.md).
Envoy overload-manager action names, CoDel TARGET/INTERVAL, APF seat
model, Reactive Streams 1.0.4 rules, Node `highWaterMark`, Kafka 4.1
pull defaults: **[→C10-1]**.

---

## 2. Lineage / vocabulary

| Term | Meaning | Named source |
|---|---|---|
| **Throughput** | Offered (or accepted) requests per second, including work that will time out. | Yanacek [15] |
| **Goodput** | The subset of throughput finished **without error** and **inside a latency the client can still use**. | Yanacek [15] |
| **Load shedding** | Reject excess so accepted work stays inside the client’s patience. Goal: goodput *plateaus*. | Yanacek [15]; Nygard *Shed Load* [12] |
| **Backpressure** | Ask the *producer* to slow down (window, credit, pull, `request(n)`). Complementary to drop. | Sackman [16]; Cvet [1]; Nygard *Create Back Pressure* [12] |
| **Adaptive concurrency** | Little’s-law limit ≈ RPS × latency, steered by a delay/loss controller (Vegas / Gradient / AIMD / PID). | Netflix 2018 **[→breaker]**; Envoy gradient proto; Cinnamon |
| **Criticality / partition** | Ordered classes; lower classes shed first. Propagated with the request. | SRE ch. 21; Netflix 2024; Cinnamon 6×128 |
| **503 + Retry-After** | Temporary overload or maintenance; optional wait hint (HTTP-date or delay-seconds). | RFC 9110 §15.6.4, §10.2.3 |
| **429** | *This client* exceeded *its* quota. Sibling of 503, not a synonym. | RFC 6585 §4; **C4** |

**Yanacek, *Using load shedding to avoid overload*** (Amazon Builders’
Library; live `builder.aws.com` 2026-09-13; archived as
perma.cc/9SAW-68MP in [15]). Do **not** re-derive the article. The
claims this catalog needs, verified on the live page this fetch:

- Max-connections as the *only* knob is too imprecise (too low cuts
  unused capacity; too high browns out; “just right” drifts).
- **Goodput ≠ throughput.** Throughput is offered RPS; goodput is the
  useful subset. Without shedding, median latency crossing the client
  timeout turns a latency problem into ~50% availability.
- Overload is a **positive feedback loop**: late work is wasted; clients
  retry; deep graphs amplify **[→C2]**.
- Ideal load-test shape: goodput **plateaus** near full utilization and
  stays flat as offered load keeps rising. If availability falls to zero,
  the service still needs a shedder.
- Shed **early and cheaply**; measure **client-perceived** availability
  and latency; **do not fold reject latency into the success histogram**
  (60% shed can make p50 look excellent).
- **Prioritize the load-balancer ping.** A missed health check shrinks
  the fleet — the last thing a brownout wants. Then: humans over
  crawlers; in-quota over burst; `end()` over `start()`; page *N* over
  page 1.
- Drop doomed work: propagate **remaining deadline**; bound **queue
  age**, not only queue length; **LIFO** if the protocol allows
  (HTTP/1.1 pipelining does not; HTTP/2 generally does).
- CLB **surge-queued**; ALB **rejects** excess. Hidden queues (TCP
  buffers, executor queues) are everywhere.
- Layered protection: WAF / API Gateway / ALB cheap drop in front;
  the server still logs what *it* drops. False-positive rate target:
  **zero**. Shedding on the same CPU target as autoscaling **starves
  the scale-out signal**.

**Google SRE book ch. 21 *Handling Overload*** (fetched 2026-09-13).
QPS is a poor capacity unit; provision on **resources** (usually CPU).
Per-customer quotas. Client-side **adaptive throttling** over a
**two-minute** window, default multiplier **K = 2**, so backends are not
busy only generating rejections. Criticality
`CRITICAL_PLUS` / `CRITICAL` (production default) / `SHEDDABLE_PLUS` /
`SHEDDABLE`, **propagated automatically** by the RPC system; backends
reject lower criticalities first. Utilization signal of choice:
**executor load average** (active threads, exponentially decayed; shed
when it exceeds processors). Per-request retry cap **3**; per-client
retry budget **~10%**; overloaded backends may answer
**“overloaded; don’t retry”**. Retry **only at the layer immediately
above** the rejector **[→C2]**.

**SRE ch. 22 *Addressing Cascading Failures*** (fetched 2026-09-13).
For steady traffic, queue length **≤ ~50% of the thread-pool size** so
the server rejects *early*; Gmail often uses **queueless** servers and
fails over. HTTP **503** when in-flight work exceeds a bound. **FIFO →
LIFO or CoDel** so work the user has already abandoned is not finished.
Deadline check **after dequeue**. Graceful degradation (search a cache
subset, cheaper ranker) is **C11**, not this note — ch. 22 names it as
the next lever after shedding.

**Nygard *Release It!* 2nd ed.** [12] lists *Shed Load* and *Create Back
Pressure* among the twelve Stability Patterns (added vs 1st ed.)
**[→breaker §1]**.

---

## 3. Mechanics

### 3.1 Goodput plateau vs throughput collapse

```
offered RPS ──► [admit / shed] ──► accepted ──► finish inside timeout? ──► goodput
                      │
                      └── cheap 503 / window-close / nack
```

Without a bound, utilization ρ → 1 and queueing delay explodes
(Brooker 2021-08-05, M/M/1: `E[N] = ρ/(1−ρ)` is **1 at ρ = 0.5** and
**99 at ρ = 0.99** — cite, do not re-derive; high-percentile latency is
the **leading indicator** of overload, a bad efficiency metric).
[performance.md](../../../cases/data-intensive-design/performance.md)
already ties that knee to retries and **metastable failure**
[7][8][9]. Shedding is the cut: refuse work that would only finish
after the client has gone, so accepted work stays on the useful side of
the timeout.

Shed **is not free**. Yanacek: Amdahl still collects; a server can
drown in reject-path CPU. SRE ch. 21: when reject cost ≈ serve cost,
push the shed **client-ward** (adaptive throttling) so the backend sees
~1 rejected request per accepted one at K = 2.

### 3.2 Shed early; never shed the ping

| Layer | What it can drop cheaply | Visibility cost |
|---|---|---|
| WAF / API Gateway / iptables | Volume before the process | Almost none — you will not know *which* API |
| LB / Envoy overload manager | New conns / new streams (503, GOAWAY, close) | Proxy stats; no app log |
| Sidecar admission / adaptive-concurrency | Per-cluster concurrency or success-rate | Proxy counters |
| In-process middleware (Cinnamon, concurrency-limits) | After headers, before the handler | App logs + priority |
| After dequeue | Doomed-by-deadline / over-age | You already paid the queue |

Yanacek’s layering rule: the **server** must still take *some* excess so
it can log client / operation / why; the hop in front must cap the
extreme. **Health checks sit outside the shed.** Verified:

- Yanacek: the LB ping is the *most important* request; max-connections
  on the proxy must stay **below** listener threads / FDs so the ping
  still fits.
- Envoy admission-control docs (1.40.0-dev, 2026-09-13): **“Health check
  traffic does not count towards any of the filter’s measurements.”**
- Envoy adaptive-concurrency docs: put the filter **after** the
  healthcheck filter so pings are not sampled into minRTT.

A shedder that trips the LB unhealthy threshold **reduces capacity**,
which is the opposite of protection.

### 3.3 Queue discipline: FIFO, LIFO, CoDel, bounds

| Discipline | When it wins | Source |
|---|---|---|
| **FIFO** | Fairness; protocols that cannot reorder (HTTP/1.1 pipeline) | Yanacek |
| **LIFO / adaptive LIFO** | Newest work is still inside the client timeout; oldest is abandoned | Yanacek; Facebook *Fail at Scale* (Maurer 2015) **[→C10-1]**; SRE ch. 22 |
| **CoDel** | Bound *sojourn time*, not length. TARGET **SHOULD be 5 ms**, INTERVAL **100 ms** (RTTs 10 ms–1 s) | RFC 8289 (Experimental, Jan 2018) **[→C10-1]**; Facebook used the same 5 ms / 100 ms pair |
| **Queue-age bound** | Dequeue, measure wait, drop if older than remaining deadline or a TTL | Yanacek; SRE ch. 22 dequeue-then-check |
| **Length bound** | Steady traffic: **≤ ~50% of pool size**; bursty traffic sized from threads × service time × burst | SRE ch. 22 |
| **No queue** | Fail over instead of waiting | Gmail (SRE ch. 22) |

**Hidden queues.** Yanacek: OS socket buffers, framework executors, CLB
surge queues. Bound **time** as well as slots; assume a queue you have
not found yet. Hébert, “Queues Don’t Fix Overload” (2014-11-19)
**[→C10-1]**: an unbounded buffer in front of a bottleneck buys time,
then fails rarer-and-worse.

**Little’s law** (concurrency ≈ rate × latency) is the limit *rule*
behind every adaptive concurrency controller **[→breaker]**; C8 uses
the same occupancy math for pool sizing **[→C8]**.

### 3.4 Adaptive concurrency (Netflix, Envoy, Uber)

A *static* in-flight cap is a bulkhead (**C8**). Adaptive concurrency
*moves* the cap from measured latency so the same binary works across
hardware and diurnal mix.

**Netflix concurrency-limits 0.5.4** (GitHub release + Maven Central
`concurrency-limits-core`, **2025-12-08**). README (fetched 2026-09-13):
server-side prefer a delay-based limiter (**VegasLimit**); client-side
AIMD or combined; gRPC excess → `Status.UNAVAILABLE`. Partition example:
live **0.9** / batch **0.1**; unidentified traffic uses **excess only**.
Algorithms first verified **[→breaker]**: Vegas (α = 3·log10 L,
β = 6·log10 L); Gradient `gradient = tolerance × rttNoLoad / rtt`;
Gradient2 long-window EMA, gradient clamped **[0.5, 1.0]**; AIMD
(+1 / ×0.9). Issue #189 (2023-09-12, maintainer): Gradient2 default
`queueSize` is **fixed 4**, not the 2018 article’s `√limit` — the √
form remains opt-in. *Performance Under Load* (2018-03-23) was Medium-
blocked this pass; numbers above are from the library + **[→breaker]**.

**Netflix PlayAPI, 2024-06-25**
(`netflixtechblog.com/enhancing-netflix-reliability-with-service-level-prioritized-load-shedding-e735e6ce8f7d`).
`ServletLimiterBuilder` partitions on `X-Netflix.Request-Name`:
**user-initiated = 1.0**, **pre-fetch = 0.0** (excess only). Header-only
so rejected requests never parse a body. Steady state: no throttle.
FIT: +2 s latency on prefetch (healthy p99 < 200 ms) → baseline shed
*both* classes; canary kept **user-initiated at 100%**. Production:
12× Android prefetch spike after an outage; prefetch availability
down to **20%**, user-initiated **> 99.4%**, **> 50%** of all requests
throttled. Internal follow-on: four Linux-`tc-prio`-inspired buckets
**CRITICAL / DEGRADED / BEST_EFFORT / BULK**. CPU shed starts **after**
the autoscaling target (experiment: noncritical after **60%**, critical
after **80%**, cluster that autoscales at **45%**). Anti-patterns they
name: **no shedding** (death spiral) and **congestive failure**
(successful RPS *drops* after the limiter engages — the reject path
ate the CPU).

**Envoy adaptive-concurrency filter** (docs + proto, 1.40.0-dev,
2026-09-13).

```
gradient = (minRTT + B) / sampleRTT     B = minRTT × buffer_pct   (default 25%)
limit_new = gradient × limit_old + √limit
```

Proto defaults: `sample_aggregate_percentile` **p50**;
`max_concurrency_limit` **1000**; `request_count` **50**; jitter
**15%** of the minRTT interval; `min_concurrency` **3** (pinned during
minRTT); `buffer` **25%**; reject status **503** (forced if configured
< 400). minRTT remeasure also triggers if the limit sits at the
configured minimum for **5 consecutive** windows. Docs example (not
defaults): update **0.1 s**, p90, `min_concurrency` **50**,
`min_concurrency_limit` **25**, interval **60 s**, jitter **10%**.
Limitation: the filter must see **every** request to the cluster.
Recommend `previous_hosts` retry predicate around the minRTT window
(concurrency pinned low → a burst of 503s).

**Uber Cinnamon** (2023-11-22, fetched 2026-09-13). RPC middleware;
priority from the edge via **Jaeger**. **6 tiers × 128 cohorts = 768**
priorities (WeChat-inspired; cohort 0 is highest; cohorts rotate so the
same users are not always first). Pipeline: default priority →
**rejector** (PID on queue inflow/outflow) → priority queue →
**scheduler** (inflight cap) → **queue timeout typically 33% of the
request timeout**. Overload detector: queue has not been empty for
**~10 s** (Facebook-inspired). Auto-tuner: modified TCP-Vegas on
endpoint latency. Claims on the page: **~1 µs** overhead; **P50 +50%
at 300% overload**; **no configuration**; vs QALM/CoDel, which
oscillated and at 3 000 RPS held only **~40%** of capacity (552 / 1 300)
while Cinnamon held near the 1 300 plateau. Experiment service: ~120 ms
unloaded, 1 s timeout, two backends ≈ **650 RPS each**.

### 3.5 503 + Retry-After (and when 429 is the wrong code)

**RFC 9110 §15.6.4** (txt fetched 2026-09-13): 503 means the server
cannot handle the request because of **temporary overload or scheduled
maintenance**, likely to clear after some delay. The server **MAY**
send `Retry-After` (§10.2.3) to suggest how long to wait. Note: a
server **need not** use 503 — it may **refuse the connection**.

**RFC 9110 §10.2.3**: with 503, `Retry-After` is how long the service
is **expected to be unavailable**. Value = `HTTP-date / delay-seconds`
(`delay-seconds = 1*DIGIT`). Examples on the RFC: `Fri, 31 Dec 1999
23:59:59 GMT` and `120` (2 minutes).

| Signal | Means | Owner |
|---|---|---|
| **503** (+ optional `Retry-After`) | *We* are short. Anyone may be rejected. | **C10** |
| **429** (+ optional `Retry-After`, RateLimit headers) | *You* exceeded *your* quota. Others may still pass. | **C4** |
| gRPC `UNAVAILABLE` / `RESOURCE_EXHAUSTED` | Overload vs quota; classify before the breaker **[→breaker]** | C1 + C10 |
| SRE “overloaded; don’t retry” | Whole datacenter looks sick; bubble up | **C2** |
| Connection refuse / GOAWAY | Cheaper than a status line (RFC 9110 note; Envoy disable-keepalive) | edge |

Verified emitters: Envoy `stop_accepting_requests` → **503**; Envoy
adaptive concurrency default **503**; Envoy admission-control rejection
= **503** **[→C10-1]** (source line). Kubernetes APF `type: Reject` →
**429** + `Retry-After` from a per-priority-level dropped-request
tracker (apiserver `priority-and-fairness.go`; KEP-era default of `1`
was replaced by a dynamic value — PR 117547). APF is **quota-shaped
fairness** at the apiserver, not a 503 shed — do not copy the 429
into a generic user-facing API unless the reject is *per tenant*.

Clients: honour `Retry-After` when short; then the **C2** budget. A
503 without a hint is **not** a license to retry immediately.

### 3.6 Backpressure (slow the producer) vs shed (drop)

| Layer | Credit / pull | What “full” does | First-pass |
|---|---|---|---|
| TCP | 16-bit Window; scale via RFC 7323 | Sender stops; persist-timer probes | **[→C10-1]** RFC 9293 |
| HTTP/2 | Stream **and** connection windows, both start **65 535** | DATA stalls; hop-by-hop (intermediary re-issues credit) | **[→C10-1]** RFC 9113 |
| Reactive Streams 1.0.4 | `request(n)` | `onNext` ≤ demand; `Long.MAX_VALUE` = unbounded opt-out | **[→C10-1]** |
| Node streams (v26.8.2) | `highWaterMark` 16 objects / 64 KiB (16 KiB Windows) | `write()` false → wait `'drain'`; ignore → buffer until OOM | **[→C10-1]** |
| Kafka 4.1 consumer | `max.poll.records` **500**; `fetch.max.bytes` **50 MiB** | Slow `poll()` → `max.poll.interval.ms` **300 s** → rebalance | **[→C10-1]** / **[→A2]** |

Backpressure is the right tool when the producer can *wait* (async
pipelines, pull consumers). It is the **wrong** tool for a synchronous
RPC whose caller will time out and retry: a bounded wait becomes a
hidden queue, then a retry storm **[→C2]**. For RPC, **shed**.

---

## 4. Verified defaults / standards (fetched 2026-09-13)

| System (version / page) | Mechanism | Defaults worth knowing | Reject |
|---|---|---|---|
| RFC 9110 | 503 + `Retry-After` | `Retry-After` optional; HTTP-date or delay-seconds; server may refuse the TCP conn instead | 503 |
| Envoy overload manager 1.40.0-dev | Resource monitor → action / load-shed point | **Off** until Bootstrap `overload_manager` is set. Docs example: disable keepalive at heap **0.92**, stop accepting / TCP-accept-shed at **0.95**. `refresh_interval` example 250 ms. `shrink_heap` timer **10 s**, retain **100 MB**. `global_downstream_max_connections` unset = **no global cap** (startup warning). | 503 / close / GOAWAY |
| Envoy admission-control **proto** | SRE-style success-rate shed, per worker | `sampling_window` **30 s**; `aggression` **1.0** (< 1 clamped); `sr_threshold` **95%**; `rps_threshold` **0**; `max_rejection_probability` **80%**. HTTP success default **< 500**; health checks excluded. Docs *example* uses 60 s / rps 1 / max 95% — **not** the proto defaults. | 503 |
| Envoy adaptive concurrency **proto** | Gradient + √headroom | p50; max limit **1000**; minRTT samples **50**; jitter **15%**; pin **3**; buffer **25%**; reject **503** | 503 |
| Envoy cluster “circuit breaking” | Concurrency *limits*, not a trip | `max_pending_requests` **1024**, `max_requests` **1024** **[→breaker]** | 503 + `x-envoy-overloaded` |
| Netflix concurrency-limits **0.5.4** (2025-12-08) | Vegas / Gradient2 / AIMD + partitions | README: Vegas on server; live/batch 0.9/0.1 example; Gradient2 `queueSize` default **4** | gRPC `UNAVAILABLE` |
| Uber Cinnamon (2023-11-22 page) | PID + Vegas + 768-priority queue | No config; queue timeout **~33%** of RPC timeout; empty-queue window **~10 s** | “rate limiting error” (page wording) |
| Kubernetes APF (docs, GA **1.29**, `flowcontrol.apiserver.k8s.io/v1`) | Shuffle-shard + fair queue | `Reject` or `Queue`; total seats = `--max-requests-inflight` + `--max-mutating-requests-inflight` | **429** + adaptive `Retry-After` |
| SRE ch. 21–22 | Criticality + queue bound + 503 | K = **2**, 2-minute window; queue **≤ ~50%** of pool; 503 when in-flight exceeds bound | 503 / “don’t retry” |
| ALB vs CLB | Excess at the LB | CLB surged; ALB **rejects** (Yanacek) | ALB spillover |

Istio `connectionPool` defaults remain **2³²−1** (effectively unlimited)
**[→breaker]** — a sidecar is not a shedder until you set the cap.

---

## 5. Knobs, observability, tuning, placement

### 5.1 Knobs

| Knob | Role | Too low | Too high |
|---|---|---|---|
| In-flight / concurrency limit | Little’s-law cap | Under-utilizes; false 503s starve autoscaling (Yanacek) | Queue forms; goodput collapses |
| Queue *length* | Burst absorber | Rejects honest bursts | SRE 10× pool × 100 ms = +1 s before work starts |
| Queue *age* / CoDel TARGET | Drop doomed work | Sheds healthy jitter | Serves answers nobody will read |
| LIFO vs FIFO | Which waiting request runs | LIFO starves the oldest (bad for fairness/pagination) | FIFO finishes abandoned work |
| Priority / partition shares | Who keeps capacity | Critical traffic shares fate with prefetch (Netflix baseline) | Idle partitions waste capacity |
| Admission `sr_threshold` / aggression | When success-rate shedding starts | Sheds on noise | Never engages |
| `Retry-After` | Pace returning clients | Herd (everyone retries in 1 s — old APF) | Clients wait past recovery |
| Health-check exemption | Keep the fleet in rotation | Missed ping shrinks capacity | Unhealthy hosts keep taking work (**C3**) |

### 5.2 Observability

Emit, **split by priority / partition**, and **never mix reject latency
into the success histogram** (Yanacek):

| Signal | Why |
|---|---|
| Offered RPS vs **goodput** (success ∧ under SLO latency) | The plateau vs collapse shape |
| Shed count / rate by class | Who paid; congestive-failure check (success RPS must not fall) |
| In-flight vs current limit; Envoy `concurrency_limit`, `gradient`, `min_rtt_msecs` | Controller health |
| Queue depth **and** queue age (p50/p99) | Length-only hides a 10 s sojourn |
| Reject-path CPU / `rq_rejected` / `rq_blocked` | Amdahl on the shed itself |
| Client-perceived availability | Server 200s after the caller timed out are not goodput |
| Health-check success vs data-plane shed | Proof the ping is exempt |
| Autoscaling signal vs shed rate | Same-threshold deadlock |

Envoy: `http.<prefix>.admission_control.{rq_rejected,rq_success,rq_failure}`;
`http.<prefix>.adaptive_concurrency.gradient_controller.{rq_blocked,concurrency_limit,gradient,min_rtt_msecs,sample_rtt_msecs,min_rtt_calculation_active}`.
No vendor PromQL recipes found — alert on *goodput drop*, *shed rate
step-change*, and *health-check failure during a shed*, not a copied
query.

### 5.3 Tuning

1. Load-test **past** the plateau and far beyond (Yanacek). If goodput
   falls, the reject path is too expensive — fix logging/socket work
   before tuning thresholds.
2. Measure client-side success ∧ latency. Set the concurrency /
   queue-age bound so accepted p99 stays inside the caller timeout
   **[→C7]**.
3. Exempt health checks; keep proxy `max_connections` below server
   threads/FDs.
4. Partition: guarantee 1.0 to user-initiated / `CRITICAL`; 0.0
   (excess) to prefetch / `BULK`. Start CPU-based progressive shed
   **above** the autoscale target (Netflix 60/80 vs 45).
5. Prefer adaptive (Vegas / Gradient2 / Envoy / Cinnamon) over a
   guessed static RPS. Static caps belong to **C8** as isolation, not
   as the overload policy.
6. Bound queue **time** (CoDel 5 ms / 100 ms or a deadline check at
   dequeue) *and* length (≤ 50% of pool for steady RPC).
7. Return **503 + `Retry-After`** (seconds, not a clock date) on
   capacity sheds; 429 only for **C4** quota. Honour the hint in **C2**.
8. Revisit after a week of goodput / shed-by-class / queue-age. A
   limiter that never fires is untested mode (Netflix anti-pattern 1).

### 5.4 Placement

| Deployment | What it sheds | Trade-off |
|---|---|---|
| Edge WAF / API Gateway / CloudFront | Volume | Cheap; blind to criticality unless you tag at the edge (Cinnamon does) |
| Envoy overload manager | Process-level memory / conn pressure | Must be turned on; 503 before filters |
| Envoy admission / adaptive-concurrency | Per-proxy, per-cluster | Uncoordinated across replicas; minRTT window injects 503s |
| In-process (concurrency-limits, Cinnamon, Resilience4j bulkhead-as-cap) | Knows headers / priority | Per instance; fleet reaction is slow |
| Kafka pause / Reactive Streams / H2 window | Producer wait | Wrong for sync RPC |
| Client adaptive throttling (SRE) | Local reject | Needs enough traffic for a 2-minute view |

---

## 6. Worked calibration — checkout API (design drill)

Constraints are a **drill**, not a vendor SLA. Method: Yanacek
plateau-test [15] + SRE queue ≤ 50% + Netflix partition 1.0 / 0.0 +
Envoy proto defaults + C7 remaining-deadline **[→C7]**.

Measured on one warmed checkout instance, client-side, 14 days:

| Class | Offered | Healthy p99 | SLO |
|---|---|---|---|
| User-initiated `POST /pay` | 400 rps | 180 ms | 99.5% ≤ 300 ms |
| Prefetch `GET /pay/quote` | 800 rps | 90 ms | best-effort |
| ALB health check | 1 / 30 s | — | **never shed** |

Instance goodput plateau (load test, prefetch + pay mixed) **~520 rps**.
Handler threads **64**. Little: 520 rps × 0.18 s ≈ **94** in-flight at
the pay p99 — the static cap must sit *above* that or we false-shed
in the healthy region.

| Knob | Choice | Why |
|---|---|---|
| Adaptive limit | Envoy gradient or concurrency-limits Gradient2; `max_concurrency_limit` **200**; `min_concurrency` **3** (proto) / Netflix Vegas on the servlet | 200 > 94 so the healthy mix is unhindered; 200 << 64 × (300 ms / 18 ms) worst-case pin |
| Queue length | **32** (50% of 64) | SRE steady-traffic rule; 32 × 180 ms ≈ 5.8 s of FIFO wait is already > the 300 ms SLO — so this is a *burst* cap, not a latency budget |
| Queue age | Drop at dequeue if wait > **50 ms** or remaining deadline < expected service (p99 180 ms) | Yanacek TTL; CoDel-class sojourn, loosened from 5 ms because this is an RPC not a DC hop |
| Discipline | FIFO while depth < 8; **LIFO** above (HTTP/2 to the instance) | Facebook adaptive-LIFO; pay is not pipelined HTTP/1.1 |
| Partition | `user-initiated` **1.0**, `pre-fetch` **0.0** on `X-Request-Class` | Netflix PlayAPI; prefetch may fall to ~20% availability under a 12× prefetch spike and pay stays on the 99.5% SLO |
| Health | Admission/adaptive filters **after** the healthcheck filter; ping not in the partition key | Yanacek + Envoy docs |
| Response | **503** + `Retry-After: 2` (delay-seconds) on capacity shed; **429** only if a *tenant* token bucket (C4) tripped first | RFC 9110; C4 vs C10 |
| Autoscaling | CPU target **45%**; progressive shed of prefetch from **60%**, pay from **80%** | Netflix experiment shape — shed *after* the scale signal |
| Retry | Clients honour `Retry-After`; **C2** 10% budget; no retry of `/pay` without an idempotency key **[→C2]** | A 503 on capture is not a signal to double-charge |
| Deadline | Edge 3 s → checkout remaining ~2.9 s **[→C7]**; drop if remaining < 200 ms at dequeue | Doomed work is not goodput |

Load-test gate: raise offered prefetch to **6×** autoscale volume with
scale-out *disabled*. Expect: pay goodput flat near 400 rps, pay p99
< 300 ms, prefetch availability collapsing, health checks **100%**,
success-path p50 **not** improved by fast 503s (those series are
separate). If pay goodput *falls*, the reject path is congestive —
fix that before shipping.

---

## 7. Failure modes and when-not-to-use

1. **No shed → collapse.** Netflix anti-pattern 1; Yanacek “fails in
   the least desirable way”; baseline in the Cinnamon graphs dies above
   3 000 RPS.
2. **Congestive failure.** Reject path more expensive than serve
   (Yanacek log/socket footguns; Netflix anti-pattern 2; SRE reject-CPU
   spiral). Successful RPS drops after the limiter engages.
3. **Shed hides latency.** Fast 503s dominate server p50. Measure
   goodput and *success-only* latency (Yanacek).
4. **Shed starves autoscaling.** Same CPU target on shed and scale-out
   (Yanacek). Netflix’s fix: shed *above* the autoscale target.
5. **Health-check inversion.** Shedding pings ejects the instance and
   concentrates load on survivors.
6. **Wrong code: 429 vs 503.** A 429 on *capacity* trains well-behaved
   clients to wait out *their* quota while the fleet is actually sick
   (and trains breakers to trip per-caller **[→C1]**). APF’s 429 is for
   apiserver fairness, not a public API template.
7. **Retry inversion.** 503 without `Retry-After` + stacked retries →
   the sustaining loop in [7][9] and **C2**. Honour “don’t retry”.
8. **FIFO on abandoned work.** 10 s queued search (SRE ch. 22) — the
   user already refreshed.
9. **LIFO starvation.** Oldest pagination/`end()` never finishes
   (Yanacek’s start/end and page-N priority fights LIFO).
10. **Unbounded buffer labelled “backpressure.”** Node ignore-`drain`;
    RxJava `BUFFER`; NGINX `proxy_max_temp_file_size` **1024m**
    **[→C10-1]**.
11. **CoDel oscillation.** QALM at deep overload rejected nearly
    everything (Cinnamon’s reason to exist).
12. **minRTT measurement dip.** Envoy pins concurrency to 3 (default)
    and 503s during the window — expected; retry *other* hosts.
13. **AZ / headroom lie.** Shedding holds CPU below the metric that
    provisioned AZ redundancy (Yanacek).
14. **Static max-connections as the only control.** Yanacek’s opening
    failure.

**When-not-to-use shedding (use the sibling).** Tenant fairness and
product quotas → **C4** (429). A single dependency hanging your threads
→ **C1** + **C7**, not a global 503. A full compartment of *one* pool
→ **C8**. Optional features you can skip while still answering →
**C11**. A producer that can wait on a credit window → backpressure /
**A2**, not a 503. In-process function calls. Work that *must* finish
after the client is gone (SRE’s checkpointed catchup).

**When-not-to-use a tight adaptive cap.** First request on a cold
instance (Envoy minRTT / Brooker TLS story **[→C7]**); mixed request
costs on one limiter (SRE: QPS is a bad unit — partition or cost-weight);
clients so sparse the 2-minute adaptive-throttling window is empty.

---

## 8. Cross-links

| Id | Why |
|---|---|
| **C4** | Quota (429) vs capacity (503). Stripe’s four limiters: the two *shedders* (fleet-usage, worker-utilization) belong here; the two *limiters* stay in C4. |
| **C1** | Breaker is the *caller’s* defense. Accelerated open on 503 + `Retry-After` **[→breaker]**. |
| **C2** | Honour `Retry-After`; 10% budget; “don’t retry”; one layer. |
| **C7** | Remaining deadline is the doomed-work predicate; timeout is the backstop, not the shed policy. |
| **C8** | Occupancy cap vs *which* request occupies it. |
| **C11** | Brownout / optional code (Klein ICSE 2014 **[→C10-1]**; SRE ch. 22 cheaper ranker). |
| **C3** | Probe vs data-plane; fail-open when all targets are unhealthy (ALB) is the opposite of a shed. |
| **A2** | Pull/credit knobs; this note owns the refuse/slow policy. |
| Cases | [performance.md](../../../cases/data-intensive-design/performance.md) (throughput, queueing, mitigations); [nfr-references.md](../../../cases/data-intensive-design/nfr-references.md) [1][7][8][9][11][12][14][15][16] |
| First-pass | [load-shedding-backpressure-external-research.md](load-shedding-backpressure-external-research.md) |

---

## 9. Sources

Fetched 2026-09-13 unless noted.

**Canon.** builder.aws.com/content/3Eun1EEyX6p2e3VYNyRLSJzLuMV/using-load-shedding-to-avoid-overload (Yanacek; [15]) · sre.google/sre-book/handling-overload · sre.google/sre-book/addressing-cascading-failures · rfc-editor.org/rfc/rfc9110.txt §10.2.3, §15.6.4 · rfc-editor.org/rfc/rfc6585 (429; **[→C4]**) · brooker.co.za/blog/2021/08/05/utilization.html · Nygard [12] **[→breaker §1]** · Sackman [16] / Cvet [1] cited via nfr-references, not re-fetched.

**Adaptive / prioritized.** netflixtechblog.com/enhancing-netflix-reliability-with-service-level-prioritized-load-shedding-e735e6ce8f7d (2024-06-25) · github.com/Netflix/concurrency-limits (README; Gradient2Limit.java; issue #189; release v0.5.4 2025-12-08) · central.sonatype.com `com.netflix.concurrency-limits:concurrency-limits-core:0.5.4` · uber.com/us/en/blog/cinnamon-using-century-old-tech-to-build-a-mean-load-shedder (2023-11-22) · uber.com/ci/en/blog/cinnamon-auto-tuner-adaptive-concurrency-in-the-wild · Performance Under Load (2018) **[→breaker]** (Medium-blocked this pass).

**Envoy / mesh.** envoyproxy.io/docs/envoy/latest/configuration/operations/overload_manager/overload_manager (1.40.0-dev) · …/http_filters/admission_control_filter · …/api-v3/extensions/filters/http/admission_control/v3/admission_control.proto · …/http_filters/adaptive_concurrency_filter · …/api-v3/extensions/filters/http/adaptive_concurrency/v3/adaptive_concurrency.proto · cluster circuit-breaking **[→breaker]**.

**Queues / AQM / APF / backpressure.** RFC 8289 **[→C10-1]** · queue.acm.org 2839461 via Internet Archive (*Fail at Scale*) **[→C10-1]** · kubernetes.io/docs/concepts/cluster-administration/flow-control · github.com/kubernetes/apiserver `priority-and-fairness.go` · kubernetes/kubernetes#117547 · ferd.ca/queues-don-t-fix-overload.html **[→C10-1]** · RFC 9293 / RFC 9113 / Reactive Streams 1.0.4 / Node stream / Kafka 4.1 **[→C10-1]** **[→A2]**.

**Cited forward.** [circuit-breaker-external-research.md](circuit-breaker-external-research.md) (Netflix 2018 algorithms; Envoy CB 1024/1024/3; Stripe shedders) · [retry-backoff-external-research.md](retry-backoff-external-research.md) · [c7-timeouts-external-research.md](c7-timeouts-external-research.md) · [c8-bulkhead-external-research.md](c8-bulkhead-external-research.md) · [a2-pubsub-queues-external-research.md](a2-pubsub-queues-external-research.md).

---

## 10. Uncertain / left out

- Yanacek live HTML is the Builder Center render; [15] is the archived
  Builders’ Library copy. Substance matched; no extra numeric defaults
  (no “shed at X% CPU”) appear on the live page.
- Netflix 2018 *Performance Under Load* Medium page blocked; Gradient /
  Vegas / AIMD coefficients from library source + **[→breaker]**.
- PlayAPI production **HTTP status** on reject is not in the 2024 post
  (filter class named; gRPC integration documents `UNAVAILABLE`).
- Envoy admission-control **docs example** (60 s / rps 1 / max 95%) ≠
  **proto defaults** (30 s / 0 / 80%). Proto is authoritative here.
- Cinnamon PID gains (secondary post mentions Kp/Ki) **not** re-fetched;
  only the 2023-11-22 overview numbers are asserted.
- APF feature-gate removal release (1.30 vs 1.31) **[→C10-1]**.
- Live ACM Queue *Fail at Scale* 403; archive used in the first pass.
- Sackman [16] and Cvet [1] not re-fetched this pass.
- Stripe worker-utilization / fleet-usage shedder thresholds: **[→C4]** /
  **[→breaker]**, not re-measured.
- PromQL / OTel attribute names above are recommendations, not a vendor
  schema.
- Checkout table is a drill. Brooker 0.1% / p99.9 is an Amazon *timeout*
  example **[→C7]**, not a shed threshold.
- “Retry priority inversion” remains analysis **[→C10-1]**, not a
  vendor finding.
- Nygard per-pattern prose mapping Shed Load → antipatterns was not
  fetchable **[→breaker §7]**.
