---
type: research
title: 'Bulkhead & isolation — external research (2026-09-13)'
description: >-
  Group C catalog evidence pass for C8: Nygard bulkheads, Hystrix thread-pool
  vs semaphore, per-dependency connection pools, Resilience4j/Envoy/Istio
  concurrency limits (not C1 failure-trip), shuffle sharding, cells as a
  blast-radius tactic, and Little's-law pool-vs-timeout calibration.
tags: [research, system-design-patterns, C8, bulkhead]
---

# C8 Bulkhead & isolation — catalog research (2026-09-13)

> **What this is.** The catalog evidence pass for **C8**. It **links** the same-day first pass [bulkhead-isolation-external-research.md](bulkhead-isolation-external-research.md) (Nygard/Azure canon, HikariCP/PgBouncer/Go/Node/Tomcat pools, ThreadPoolExecutor queue traps, Kubernetes QoS, Little's-law permit math) and **deepens** it to the Group C / [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md) bar: mechanics and variants, knobs with verified defaults, observability, tuning, a worked pool-size-vs-timeout calibration, failure modes, sources. The breaker (C1) stops *new* calls once failure is proven; this note owns the partitions that bound damage **while the breaker is still counting**.
>
> **Method.** Primary pages fetched 2026-09-13. Numbers and option names reproduced exactly; everything else paraphrased. Facts marked **[→C8-1]** are in the first-pass note and not re-fetched here. Facts marked **[→breaker]** / **[→C7]** / **[→B1]** are in the sibling research notes. Unverifiable items are in §10 and are **not** asserted as fact.

---

## 1. Scope and non-goals

**Owns.** Nygard bulkheads as dedicated capacity per dependency or client class; thread-pool vs semaphore isolation (the Hystrix lesson and what Resilience4j kept); connection-pool isolation *per dependency*; Envoy concurrency circuit-breaking (`max_connections` / `max_pending_requests` / `max_requests` / `max_retries`) distinguished from C1 failure-trip breakers; Istio `DestinationRule.connectionPool`; shuffle sharding as combinatorial blast-radius reduction; **cells as a tactic** (cap the fraction of the fleet a poison request or bad deploy can hit). Verified library/mesh defaults with versions or fetch dates; observability; a worked Little's-law calibration of pool size against the C7 timeout.

**Does not own.** What errors trip a breaker, half-open design, or outlier detection (**C1**). Which traffic to drop when the system is already overloaded (**C10** — a full bulkhead is a reject, not a priority policy). Cell-based *architecture* as a style: quantum count, router options as a platform, zonal vs regional cells as a deploy model (**E13**). Where the sidecar sits and what else it intercepts (**B6**). How `L = λW` is proved and how autoscalers use it (**B1** — this note only *applies* the identity to a permit pool). Jitter / retry-budget math (**C2**). How the timeout number is chosen (**C7** — this note only uses it as hold-time).

**Does not re-derive.** [Bulkhead.md](../../../cases/SystemDesignPatterns/Bulkhead.md) (existing Concept; links the first-pass). HikariCP/PgBouncer/Tomcat/Go/Node defaults, Kubernetes requests/limits/QoS, ThreadPoolExecutor unbounded-queue trap **[→C8-1]**.

---

## 2. Lineage / vocabulary

| Term | Meaning | Named source |
|---|---|---|
| **Bulkhead** | Dedicated capacity so one dependency, tenant, or request class can exhaust only its own share. | Nygard *Release It!*; Azure Bulkhead pattern |
| **Semaphore isolation** | A counter on the *calling* thread. Cheap. **No walk-away timeout** — a latent call holds the caller until the I/O timeout. | Hystrix wiki How-it-Works / Configuration |
| **Thread-pool isolation** | A bounded pool *per dependency*. Caller can time out and leave; the pool thread may still run. | Same; Netflix API: 40+ pools, most size 10 |
| **Connection-pool isolation** | A separate outbound (or DB) pool per dependency / host. Shared pool = shared fate. | Azure Bulkhead; HikariCP **[→C8-1]** |
| **Concurrency circuit-breaking** | Envoy/Istio *limits* (connections, pending, in-flight, retries). Overflow → reject. Not a failure-rate automaton. | Envoy arch overview + proto (1.40.0-dev) |
| **Shuffle shard** | Per-customer virtual shard drawn as a combination/permutation of workers; client retries across members. | MacCárthaigh 2014-04-14; Builders' Library **[→C8-1]** |
| **Cell (tactic)** | A blast-radius partition: *N* cells → ~1/*N* of tenants/requests if one cell dies. | AWS WA *What is a cell-based architecture?* |

**Nygard, *Release It!*** (2nd ed. 2018) lists **Bulkheads** as the third of the twelve Stability Patterns — after Timeouts and Circuit Breaker **[→breaker §1]**. Publisher extracts do not cover ch. 5; the prescription is triangulated from Azure + secondaries **[→C8-1]**: contain a failure inside dedicated resources at every granularity (thread pools, per-dependency pools, app-server groups per client class). Lineage: 2007 1st ed. → Hystrix per-dependency pools (2012) → Resilience4j / Polly concurrency limiter.

**Azure Architecture Center, Bulkhead pattern** (ms.date **2026-03-19**, page fetched 2026-09-13). Now states bulkhead is "also known as a *cell-based architecture*" — that equation is Azure's; **this note keeps the tactic and leaves the style to E13**. Problem: one unresponsive service pins a consumer's shared pool until every service fails; one greedy client exhausts a provider for all. Solution: partition instances by consumer class; **per-dependency connection pools on the consumer**. Combine with Retry, Circuit Breaker, Throttling; consumer bulkheads from processes / thread pools / semaphores (resilience4j and Polly named); service bulkheads from VMs/containers/processes; separate queues for async; prefer platform controls (APIM, Cosmos RU, AKS limits); **AI/inference often needs strict bulkheads because deployments carry their own quotas**. Not suitable when the efficiency loss or complexity is unjustified.

**Hystrix How-it-Works** (wiki fetched 2026-09-13). Isolation is the reason the library existed: "latency on the underlying executions will saturate the available threads only in that pool." Thread isolation lets the caller *walk away*. Semaphore isolation "does not allow for timing out and walking away"; "if a dependency is isolated with a semaphore and then becomes latent, the parent threads will remain blocked until the underlying network calls timeout." Netflix API: **10+ billion** command executions/day, **40+** thread-pools per instance, **5–20** threads each (most set to **10**). Semaphore reserved for "very low-latency" / "hundreds per second" in-process calls where thread overhead is too high — wiki example: 5000 rps in-memory lookups on a semaphore of **2**; default is still **10**.

---

## 3. Mechanics

### 3.1 Two isolation strategies (Hystrix lesson)

```
THREAD:     caller ──queue──► dep-pool threads ──I/O──► dependency
            timeout fires on caller; pool thread may keep running
SEMAPHORE:  caller ──permit──► same caller thread ──I/O──► dependency
            reject at permit==0; no walk-away; I/O timeout is the only bound
```

| | **Thread-pool isolation** | **Semaphore isolation** |
|---|---|---|
| Who runs the call | A thread from *this dependency's* pool | The caller (Tomcat / event-loop / VT) |
| Saturation | Pool + queue full → reject / fallback | Permit count hit → reject |
| Timeout | Yes (Hystrix default **1000 ms**, interrupt-on-timeout **true**) | **No** — Hystrix timeout on semaphore is a *separate timer thread* that cannot free the caller **[How-it-Works]** |
| Cost | Queueing + context switch (Netflix still preferred it at 10B/day) | A counter |
| Failure mode | Pool threads ignore `InterruptedException` (most Java HTTP clients) → pool stays full after the caller left | Latent dependency pins *caller* threads; the container pool *is* the blast radius |
| When | Untrusted / network clients | Trusted, sub-ms, in-process; or virtual threads + a cap (JEP 444 **[→C8-1]**) |

Hystrix `HystrixCommand` default **THREAD**; `HystrixObservableCommand` default **SEMAPHORE**. Resilience4j inverted the recommendation: docs say `SemaphoreBulkhead` "should work well across a variety of threading and I/O models" and, unlike Hystrix, "does not provide a 'shadow' thread pool"; "it is up to the client to ensure correct thread pool sizing that will be consistent with bulkhead configuration." `ThreadPoolBulkhead` is the opt-in shadow pool (bounded queue + fixed pool). **The lesson that survived:** a semaphore is not a timeout. Pair it with C7 or the caller still holds the slot for the I/O bound.

Polly v8 retired `Policy.Bulkhead`; the counterpart is `AddConcurrencyLimiter(permitLimit, queueLimit)` over `System.Threading.RateLimiting` — a semaphore with an optional queue, not a thread pool.

### 3.2 Connection-pool isolation per dependency

Azure's first diagram is the consumer-side rule: Workload 2 has **one pool for Service B and one for Service C**; Service A dying cannot take B/C. A single shared HikariCP / `http.Transport` / `http.Agent` for "all outbound" is the anti-pattern the pattern exists to stop.

| Shared pool | Isolated pools |
|---|---|
| One slow dependency occupies every connection; checkout cannot reach catalog | Payment can fill only *its* pool; catalog/recs keep theirs |
| One `connectionTimeout` (HikariCP **30 s** **[→C8-1]**) pins waiters for all deps | Waiters queue only on the sick dep |
| Sizing is a compromise that is wrong for everyone | Size each pool with `L = λW` for *that* hop (B1) |

Outbound HTTP defaults that are **not** bulkheads unless set: Go `MaxConnsPerHost` **0 = no limit**; Node `maxSockets` **Infinity** **[→C8-1]**. Envoy's per-cluster limits (§3.3) are the mesh form of the same rule. Nested acquisition of the *same* pool deadlocks — HikariCP `pool ≥ Tn × (Cm − 1) + 1` **[→C8-1]**. Fix = separate pools per tier, not a bigger shared one.

### 3.3 Envoy concurrency circuit-breaking ≠ C1 failure-trip

CircuitBreaker.md: "Two different mechanisms share the name." This note owns the **limit**; C1 owns the **automaton**.

Envoy (docs `latest` = **1.40.0-dev**, fetched 2026-09-13) enforces five *fully distributed, not coordinated* limits **per upstream cluster and per priority**. Overflow increments a counter and the router sets **`x-envoy-overloaded`**. Defaults from `circuit_breaker.proto`:

| Knob | Default | Overflow counter | What it isolates |
|---|---|---|---|
| `max_connections` | **1024** | `upstream_cx_overflow` | TCP/HTTP1 connections to the *cluster* (active + draining). Envoy still guarantees ≥1 connection to a selected host → `upstream_cx_active` can exceed the limit by up to `(endpoints) × (connection pools)` |
| `max_pending_requests` | **1024** | `upstream_rq_pending_overflow` | Requests waiting for a ready connection. HTTP/2 with unconfigured max streams multiplexes on one connection — this trips mainly when **no** connection exists yet |
| `max_requests` | **1024** | `upstream_rq_active_overflow` | Outstanding requests to the cluster (HTTP only). Runtime `skip_pending_overflow_count_on_active_rq` (default **true**) stops double-counting on the legacy pending counter |
| `max_retries` | **3** | `upstream_rq_retry_overflow` | Concurrent retries. Docs: "aggressively circuit break retries"; prefer a **retry budget** |
| `max_connection_pools` | **unlimited** | `upstream_cx_pool_overflow` | Instantiated pools (Original-Src can create unbounded pools). Pools do not time out; connections do |

`retry_budget` (optional) **overrides** `max_retries`: default **20%** of (active + pending) with `min_retry_concurrency` **3**, `budget_interval` **0 ms** (presently in-flight only). C2 owns the budget math; the knob lives here because it is a *concurrency* cap.

**Not these:** Envoy *outlier detection* (`consecutive_5xx` 5, ejection 30 s × n, …) is a C1 failure-trip **[→breaker]**. A cluster at 200 rps with 1024 `max_requests` will not overflow and will not look "open" on `rq_open` — that is not a healthy breaker; it is an unused limit.

Workers share limits (eventually consistent; races can exceed). `track_remaining` default **false** — remaining gauges are off until flipped. Disable by setting thresholds to the type max.

### 3.4 Istio `DestinationRule.connectionPool`

Istio maps the same Envoy limits, then **removes the modest defaults**. DestinationRule reference (istio.io latest, fetched 2026-09-13):

| Field | Envoy analog | Istio default |
|---|---|---|
| `tcp.maxConnections` | `max_connections` | **2³²−1** |
| `http.http1MaxPendingRequests` | `max_pending_requests` | **2³²−1** (docs: applies to HTTP/1.1 *and* HTTP/2) |
| `http.http2MaxRequests` | `max_requests` | **2³²−1** (same caveat) |
| `http.maxRetries` | `max_retries` | **2³²−1** (not Envoy's 3) |
| `http.maxRequestsPerConnection` | — | **0** = unlimited, up to 2²⁹; **1** disables keepalive |
| `tcp.connectTimeout` | `connect_timeout` | **10 s** (Envoy cluster default is **5 s** **[→C7]**) |
| `tcp.idleTimeout` / `http.idleTimeout` | idle | **1 hour** if unset; `0s` disables TCP idle |
| `http.maxConcurrentStreams` | H2 streams | **2³¹−1** |

An Istio mesh with no `connectionPool` stanza is **not** running Envoy's 1024/1024/1024/3 bulkhead. It is unlimited concurrency plus whatever the app set. The published task (httpbin, `maxConnections: 1`, `http1MaxPendingRequests: 1`, `maxRequestsPerConnection: 1`): fortio `-c 2 -n 20` → **85% 200 / 15% 503**; `-c 3 -n 30` → **36.7% / 63.3%**; proof is the *client* sidecar `upstream_rq_pending_overflow` (task dump: **21**). `outlierDetection` on the same DestinationRule is C1 — do not tune it to "fix" overflow 503s.

### 3.5 Shuffle sharding

Traditional shard of 8 workers into 4×2: poison customer → **25%** blast radius (2014-04-14 Architecture Blog, fetched 2026-09-13). Shuffle shard of **2-of-8**: the 2014 post counts **56** *permutations* and, with client retries across both members, constrains real impact to **~1/56**. Four members (3 retries) → **1/1680**. The current Builders' Library article counts **combinations** (**28** for 2-of-8) and Route 53 as **2048** virtual name servers × shard of **4** → "730 billion" `C(2048,4)` **[→C8-1]** — do not mix 56 with 28. The *mechanism* is the same: overlapping virtual shards + **client retry across members**. Without the retry, shared workers couple the shards and the gain collapses.

Infima (2014): stateless hash shards vs stateful search that caps overlap (e.g. 4-of-20, no two shards share more than two). Also: shuffle-shard *in-memory* queues and rate-limiters, not only hosts.

### 3.6 Cells as a tactic (E13 owns the style)

AWS WA (fetched 2026-09-13): a cell is a complete, independent replica serving a subset of the partition key. **10 cells → ~10% blast radius; 100 → ~1%.** That percentage is the *tactic* — cap the fraction a bad deploy, poison pill, or noisy tenant can hit. The router is the **one shared component** and "cannot follow the same compartmentalization strategy"; keep it "as simple and horizontally scalable as possible", no business logic, hash+modulo mapping, keep serving healthy cells even when one is unreachable. Sizing forces: big enough for the largest tenant and economies of scale; small enough to test at full scale and stay under account/quotas; a cell should have known maxima in TPS, tenants, storage. **E13** owns whether the system *is* cell-based (quantum count, zonal vs regional, control-plane). This note only uses cells as another bulkhead granularity above pools.

---

## 4. Verified defaults / standards (fetched 2026-09-13)

### 4.1 Libraries

| Implementation | Version / page | Isolation | Default caps | At saturation |
|---|---|---|---|---|
| Hystrix `HystrixCommand` | wiki + `HystrixCommandProperties` / `HystrixThreadPoolProperties` (1.5.x line; maintenance since 2018 **[→breaker]**) | **THREAD** | pool `coreSize`/`maximumSize` **10**, `maxQueueSize` **−1** (SynchronousQueue), `queueSizeRejectionThreshold` **5** (inert at −1), timeout **1000 ms**, interrupt-on-timeout **true** | Reject → fallback |
| Hystrix semaphore | same | **SEMAPHORE** (also fallback semaphore) | `execution` **10**, `fallback` **10** | Reject; caller already blocked if in-flight |
| Resilience4j `SemaphoreBulkhead` | docs + master `BulkheadConfig` (2.4.0-era constants; tag blob empty this fetch) | Semaphore | `maxConcurrentCalls` **25**, `maxWaitDuration` **0**, `fairCallHandlingStrategyEnabled` **true** (source) | Immediate `BulkheadFullException` |
| Resilience4j `ThreadPoolBulkhead` | docs + `ThreadPoolBulkheadConfig` | Shadow pool | max = `availableProcessors()`, core = processors−1 (floor 1), `queueCapacity` **100**, `keepAliveDuration` **20 ms**, reject `AbortPolicy` | Queue, then reject. `queueCapacity == 0` → `SynchronousQueue` |
| Polly v8 `AddConcurrencyLimiter` | pollydocs.org rate-limiter | Semaphore + queue | Strategy `DefaultRateLimiterOptions`: `PermitLimit` **1000**, `QueueLimit` **0**. `ConcurrencyLimiterOptions.PermitLimit` itself has **no usable default** (must be > 0) | `RateLimiterRejectedException` (+ optional `RetryAfter`) |
| .NET standard resilience handler | **[→breaker]** | Concurrency limiter outermost | **1000** permits, queue **0** | Reject before retry/breaker |
| JDK 21+ virtual threads | JEP 444 **[→C8-1]** | — | Do **not** pool VTs; cap the *resource* with a semaphore | — |

Spring AOP nest (Retry outermost … Bulkhead innermost) **[→retry-library-defaults]**: the permit is taken *around the call*, after retry and breaker decided to invoke. A retry therefore re-takes the permit (good); an Open breaker never should.

### 4.2 Mesh / proxy

| System | Version / page | Connections | Pending | Requests | Retries | Notes |
|---|---|---|---|---|---|---|
| Envoy | 1.40.0-dev proto + arch | **1024** | **1024** | **1024** | **3** | Per cluster × priority; `x-envoy-overloaded`; retry_budget 20%/min 3 overrides retries |
| Istio `connectionPool` | DestinationRule latest | **2³²−1** | **2³²−1** | **2³²−1** | **2³²−1** | Must set to isolate; task uses 1/1/1 |
| Istio `outlierDetection` | same CR | — | — | — | — | **C1**, not a pool |

---

## 5. Knobs, observability, tuning

### 5.1 Knobs

| Knob | Role | Too low | Too high |
|---|---|---|---|
| Semaphore / `maxConcurrentCalls` / `max_requests` | Cap in-flight = `L` | Healthy tail rejected; under-utilized dep | Unused limit; one dep can still take the process |
| `maxWaitDuration` / `QueueLimit` / `max_pending_requests` | Bound the *queue in front of* the cap | Burst → 503 | Invisible latency; memory; B1 cliff |
| Thread-pool size / Hikari `maximumPoolSize` | Cap *workers* or *connections* for one dep | Same as semaphore too-low | Idle capacity; or (unbounded queue) a fake max **[→C8-1]** |
| Per-attempt timeout (C7) | How long a slot is held when the dep hangs | False-timeout + retry storm **[→C7]** | Eskildsen: 5 s on a 100 ms worker ≈ 1/50 capacity **[→breaker]** |
| Shuffle-shard cardinality / cell count | Blast-radius fraction | 4 shards → 25% | More cells/shards to operate; router is shared |
| Envoy `max_retries` / retry_budget | Concurrent retry cap | Genuine blips cannot retry | Retry storm *through* the bulkhead (C2) |

Placement: **library** (typed reject, per-dep permit) → **connection pool** (per-dep sockets) → **sidecar** (Envoy 1024 vs Istio unlimited — B6 owns *that it is a sidecar*) → **cell / shuffle shard** (tenant blast radius). The tightest *occupied* cap on the path is the real isolation; an unset Istio pool plus `maxSockets: Infinity` is no bulkhead.

### 5.2 Observability (feeds D4)

Emit **per dependency / cluster / shard**, not a process total:

| Signal | Why |
|---|---|
| Available permits vs max (`resilience4j.bulkhead.available.concurrent.calls` / `.max.allowed.concurrent.calls`) | Saturation vs unused limit |
| ThreadPoolBulkhead `queue.depth` vs `queue.capacity`, `thread.pool.size` vs core/max | Queue hiding overload |
| Reject count (`BulkheadFullException` / `OnRateLimiterRejected` / Envoy `upstream_rq_*_overflow`) | Admission, not "5xx" |
| Envoy `circuit_breakers.<priority>.{cx,rq_pending,rq,rq_retry}_open` (0/1) | Which *limit* is at cap — not C1 Open |
| `remaining_*` (only if `track_remaining: true`) | Headroom until overflow |
| Hold-time histogram with the C7 timeout drawn | Slots stuck at T |
| `x-envoy-overloaded` / 503 vs C1 503 from ejection | Overflow ≠ host unhealthy |
| Per-shard / per-cell error rate | Shuffle/cell working (blast radius) vs shared-pool (everyone) |

Alert shapes: *reject rate > X for 5 min* (cap too small or dep hung at T); *queue depth pinned at capacity* (pending is a second queue); *`rq_open == 0` forever on a critical cluster* (limit never sized — not "healthy").

### 5.3 Tuning

1. Measure caller-side `λ` and sojourn `W` **per dependency** (include queueing).
2. Set `L_cap ≈ λ × W_healthy × margin` (B1). Margin covers p95, not the timeout.
3. Set C7 per-attempt timeout **independently**; then compute timeout-held capacity `λ_hang = L_cap / T` (§6). If `λ_hang` is far below offered `λ`, shrink `T` or raise `L_cap` — or shed (C10).
4. Wait/queue **0** (R4j / Polly / .NET standard) unless a measured burst is shorter than T. Envoy 1024 pending is a *queue*, not isolation.
5. One pool / one semaphore / one Envoy cluster **per dependency** (and per tenant/class if they contend). Shopify Semian: host-wide *bulkhead*, per-worker *breaker* **[→breaker]**.
6. Istio: write `connectionPool` or you inherited 2³²−1.
7. Revisit after a week of permit and overflow series; a bulkhead that never rejects is as uninformative as a breaker that never trips.

---

## 6. Worked calibration — checkout → payment (Little's law × C7 timeout)

Constraints are a **design drill**, not a vendor SLA. Identity from **[→B1]**: `L = λW`. Timeout from **[→C7]** checkout Brooker table. Eskildsen napkin **[→breaker]**.

Measured caller-side `POST /capture`, same AZ, warmed connections, **200 rps** (B1's pair):

| Percentile | Latency |
|---|---|
| p50 | 80 ms |
| p95 | 160 ms |
| p99.9 | 420 ms |

`L_mean = 200 × 0.080 = 16`. `L_p95 = 200 × 0.160 = 32`. Start `SemaphoreBulkhead.maxConcurrentCalls` / Envoy `max_requests` at **24** (1.5× mean) with `maxWaitDuration` / pending **0**. That admits the mean and a short burst; p95 sojourn already wants 32 — if p95 is *queueing* you caused, do not size to it (B1: keep offered L at the onset of queueing).

C7 per-attempt **T = 500 ms**. Timeout/healthy = 500/80 = **6.25×** (same class as Eskildsen 5 s / 100 ms = 50×). A hung call occupies ~6 healthy slots.

| Hang fraction | Extra L = f × 200 × 0.5 | Slots left of 24 | Healthy remainder `λ × 0.08` | Fits? |
|---|---|---|---|---|
| 0% | 0 | 24 | 16 | yes |
| 5% | 5 | 19 | 15.2 | yes |
| 20% | 20 | 4 | 12.8 | **no — healthy traffic shed** |
| 100% | — | `λ_cap = 24/0.5 = 48 rps` | — | pool is a 48 rps cap, not 200 |

If 20% hang is plausible (dep slow, not down — C1 slow-call / C7 too-long T), either cut T toward p99.9 (420 ms → still ~5×) or raise L to `16 + 20 = 36` *and* accept 36 concurrent payment calls on this instance. A **shared** 24-slot pool with catalog+recs makes the 20% case take 20/24 of *all* outbound capacity.

Connection pool: outbound HTTP to payment ≥ 24 (or Envoy `max_connections` if HTTP/1.1; H2 multiplexes so `max_requests` is the real cap). **Do not** copy HikariCP's small-pool doctrine (max **10**, "saturated with threads waiting") onto this hop — that formula is for a disk/CPU-bound *database* **[→C8-1]**. Istio: set `http2MaxRequests: 24` (or 32) and `http1MaxPendingRequests: 0–8`; leaving defaults is 2³²−1.

Retries: Envoy `max_retries` 3 is concurrent, not per-request. Worst-case in-flight if every call retries = 24 × (1+retries) unless a retry budget (20%) is set — C2. Hedge is forbidden on `POST /capture` **[→C7]**.

Cells/shuffle (tactic only): if payment tenants are shuffle-sharded 2-of-8, a poison tenant hits 2 workers (~1/28 combinations **[→C8-1]**, or 1/56 permutations on the 2014 count). That does **not** replace the per-instance 24-permit cap.

---

## 7. Failure modes and when-not-to-use

1. **Shared pool.** One hung dep = process-wide hang. Azure's problem statement.
2. **Semaphore without a timeout.** Hystrix How-it-Works: parent threads stay blocked until the *network* timeout. C7 missing → TCP floor **[→C7]**.
3. **Thread-pool timeout that does not stop work.** Hystrix: `InterruptedException` ignored by typical HTTP clients → pool stays full after the caller left.
4. **Queue-as-bulkhead.** R4j `queueCapacity` 100, Envoy pending 1024, `ThreadPoolExecutor` unbounded queue **[→C8-1]**: overload becomes RAM and latency. Little: `W` grows, so `L` grows faster than `λ` **[→B1]**.
5. **Timeout holds the slot.** Breaker stops *new* calls; threads/permits already parked stay parked **[→breaker]** Azure *inappropriate time-outs*. §6 20% hang table.
6. **Istio unlimited mistaken for Envoy 1024.** No stanza → 2³²−1; `maxRetries` also unlimited (retry storm).
7. **Envoy 1024 treated as a C1 breaker.** `rq_open == 0` because you never approached 1024. Outlier detection is the other knob.
8. **Same-pool re-entry deadlock.** HikariCP formula **[→C8-1]**.
9. **Bulkhead = whole container pool.** Hystrix: semaphore must be a *small percentage* of Tomcat threads or it isolates nothing.
10. **Shuffle shard without client retry.** Shared workers couple shards; blast radius returns to "whoever shares a host."
11. **Mixing 28 and 56.** Combinations vs permutations for 2-of-8.
12. **Cells without a boring router.** Router is shared; business logic there is a fleet-wide blast radius (E13).
13. **Virtual-thread *pools*.** JEP 444: never pool VTs; semaphore-cap the dependency **[→C8-1]**.
14. **Nested retry × permit.** Retry outside bulkhead re-takes a permit (intended); retry storms still fill *this* dep's pool (C2 budget).
15. **AI deployment quotas.** Azure 2026 note: isolate model deployments per workload/tenant or one tenant burns the org quota — still a bulkhead, not a breaker.

**When a bulkhead is the wrong tool.** The efficiency loss is unjustified (Azure). You need a *priority* decision about whom to fail (**C10**). The dependency is hard-down and you want fail-fast + fallback (**C1**), not a full queue. In-process CPU work on platform threads already isolated by the FJP. Health probes (**C3**). You are designing cell *architecture* (routing, control plane, zonal cells) — **E13**.

**When-not-to-use a *tight* cap.** Unknown `λW` (measure first); multi-tenant *shared* pools you have not partitioned; first request on a cold connection (Brooker **[→C7]**); work that legitimately fans out above `L_mean`.

---

## 8. Cross-links

| Id | Why |
|---|---|
| **C1** circuit breaker | Failure-rate / outlier automaton; Envoy *outlier detection*; "two mechanisms share the name"; threads already blocked |
| **C2** retry | `max_retries` / retry_budget are concurrency caps on retries; do not rewrite jitter |
| **C7** timeouts | Slot hold-time; pair every semaphore with a bound; Brooker T used in §6 |
| **C10** shedding | Bulkhead reject is admission; *which* class to keep is shedding |
| **B1** scaling | `L = λW` identity; M/M/1 cliff if you queue in front of the pool |
| **B6** sidecar | Placement of Envoy/Istio isolation, not the knobs |
| **E13** cell-based architecture | Style / quanta / zonal-regional; this note only uses the 1/*N* tactic |
| **D4** tracing | Record bulkhead name, available permits, reject vs timeout class on the span |
| First-pass C8 | [bulkhead-isolation-external-research.md](bulkhead-isolation-external-research.md) — pools, K8s QoS, HikariCP, Route 53 C(2048,4) |
| Cases | [Bulkhead.md](../../../cases/SystemDesignPatterns/Bulkhead.md), [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md), [scalability.md](../../../cases/data-intensive-design/scalability.md) |

---

## 9. Sources

Fetched 2026-09-13 unless noted.

**Canon.** learn.microsoft.com/azure/architecture/patterns/bulkhead (ms.date 2026-03-19; GitHub `MicrosoftDocs/architecture-center` `docs/patterns/bulkhead.md`) · Nygard *Release It!* 2nd ed. **[→breaker §1]** · github.com/Netflix/Hystrix/wiki/How-it-Works · github.com/Netflix/Hystrix/wiki/Configuration · `HystrixCommandProperties.java` (`default_executionTimeoutInMilliseconds` 1000, semaphore 10/10, strategy THREAD) · `HystrixThreadPoolProperties.java` (core/max 10, maxQueueSize −1, queueSizeRejectionThreshold 5).

**Libraries.** resilience4j.readme.io/docs/bulkhead · resilience4j.readme.io/docs/micrometer · github.com/resilience4j/resilience4j `BulkheadConfig.java` / `ThreadPoolBulkheadConfig.java` (master; v2.4.0 HTML blob empty this fetch) · pollydocs.org/strategies/rate-limiter (`PermitLimit` 1000 / `QueueLimit` 0; `AddConcurrencyLimiter`) · openjdk.org/jeps/444 **[→C8-1]** · Spring nest **[→retry-library-defaults]** getting-started-3.

**Mesh.** envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking (1.40.0-dev) · …/api-v3/config/cluster/v3/circuit_breaker.proto (1024/1024/1024/3; retry_budget 20%/min 3) · …/configuration/upstream/cluster_manager/cluster_stats (`cx_open` … `remaining_*`; `track_remaining` default off) · istio.io/latest/docs/reference/config/networking/destination-rule (`connectionPool` 2³²−1; connectTimeout 10 s; idle 1 h) · istio.io/latest/docs/tasks/traffic-management/circuit-breaking (85%/15% and 36.7%/63.3%; `upstream_rq_pending_overflow`).

**Shuffle / cells.** aws.amazon.com/blogs/architecture/shuffle-sharding-massive-and-magical-fault-isolation (2014-04-14; 56 permutations; 1/1680 at 4-of-8) · Builders' Library combinations / Route 53 2048 **[→C8-1]** (live HTML 409 / builder.aws.com timeout this session) · docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/what-is-a-cell-based-architecture.html · …/cell-sizing.html (10% / 1%) · …/cell-routing.html (router is shared; no business logic).

**Cited forward.** [bulkhead-isolation-external-research.md](bulkhead-isolation-external-research.md) (HikariCP 7.1.0 max 10 / 30 s; PgBouncer; Go/Node; Tomcat; K8s QoS; Little 1961) · [b1-scaling-strategies-external-research.md](b1-scaling-strategies-external-research.md) §3.2 · [c7-timeouts-external-research.md](c7-timeouts-external-research.md) §6 · [circuit-breaker-external-research.md](circuit-breaker-external-research.md) (Envoy vs outlier; Semian; Eskildsen; .NET 1000).

---

## 10. Uncertain / left out

- Nygard's exact ch. 5 prose — secondaries only; no verbatim **[→C8-1]**.
- Live Builders' Library / builder.aws.com shuffle-sharding: 409 and timeout this session. Route 53 **2048 / C(2048,4) / 28 combinations** stay **[→C8-1]**; 2014 **56 / 1/1680** re-fetched.
- Resilience4j **v2.4.0** tag `BulkheadConfig.java` GitHub HTML was empty; defaults asserted from the live docs table + master constants (same as first-pass). Release date of 2.4.0 not re-checked here.
- `fairCallHandlingStrategyEnabled` default **true** is source-only (not on the docs table).
- Whether every Istio 1.2x still writes Envoy thresholds as 2³²−1 when the stanza is omitted was not dumped from a live control plane — docs say those defaults.
- Envoy `max_connections` "at least one per selected host" overflow bound: formula from the arch page; not re-measured.
- Istio task 85%/15% and 36.7%/63.3% are the *documented* fortio run, not a re-run.
- Polly `ConcurrencyLimiterOptions` without wrapping `RateLimiterStrategyOptions`: only "PermitLimit must be > 0" is asserted; no hidden default found.
- HikariCP keepalive flip release, Oracle RWP 2048→96, PgBouncer docs version **[→C8-1]**.
- JEP 491 (pinning, JDK 24) not verified **[→C8-1]**.
- Semian SysV details beyond "host-wide bulkhead" **[→breaker]**.
- §6 table is a drill; Brooker 0.1% / p99.9 is an Amazon *example* **[→C7]**.
- PromQL names above are the Resilience4j/Envoy documented series, not a required dashboard schema.
- Azure's "bulkhead = cell-based architecture" wording is theirs; E13 decides if the style applies.
