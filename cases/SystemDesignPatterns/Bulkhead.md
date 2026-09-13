---
type: reference
title: 'Bulkhead and isolation'
description: 'Partition capacity — thread pools, semaphores, connection pools, shuffle shards, cells as a blast-radius tactic — so one dependency, tenant, or request class can sink only its own share. Distinguishes Envoy concurrency limits from C1 failure-trip breakers. Covers Hystrix isolation, verified library and mesh defaults, Little’s-law pool-vs-timeout sizing, observability, and the shared-pool failure modes.'
tags: [system-design-patterns, resilience, bulkhead, isolation]
---

# Bulkhead and isolation

**See also:** [circuit breaker](CircuitBreaker.md) · [retry, backoff, and retry budgets](RetryBackoff.md) · [timeouts and deadline propagation](TimeoutsDeadlines.md) · [load shedding & backpressure](LoadShedding.md) · [rate limiting](RateLimiting.md) · [reliability](../data-intensive-design/reliability.md) · [scalability](../data-intensive-design/scalability.md) · [NFR references](../data-intensive-design/nfr-references.md) · [cloud failure-tolerant patterns](../aws/ch08.md) · [catalog research (2026-09-13)](../../docs/research/sysdesign/c8-bulkhead-external-research.md)

A bulkhead partitions capacity — threads, connections, memory, whole servers — so that one dependency, tenant, or request class can exhaust only **its own share**. The ship metaphor is Nygard's: compartments so a hull breach floods one section, not the vessel. It is the *structural* member of the resilience set. The [timeout](TimeoutsDeadlines.md) bounds how long a unit is held. The [breaker](CircuitBreaker.md) stops *new* calls once failure is proven. The bulkhead bounds the damage **while the breaker is still counting**. Quality attributes: **fault isolation**, **blast-radius control**, differentiated **QoS**. Costs: capacity fragmentation (reserved-but-idle), more pools to size and watch, and a new deadlock class.

The breaker decides **whether to call**. Timeouts decide **how long a slot is held**. Retries and their budget decide **whether to try again**. The bulkhead decides **how much may run at once, per compartment**.

## Lineage and vocabulary

- **Nygard, *Release It!*** ([12](../data-intensive-design/nfr-references.md)) lists Bulkheads as the third stability pattern — after Timeouts and Circuit Breaker. Dedicated resources per function at every granularity: bounded thread pools, per-dependency pools, app-server groups per client class (the airline drill: flight-status lookups get their own servers so check-in survives their death).
- **Hystrix** made it mainstream (2012): a bounded thread pool per dependency with a timeout, versus semaphore isolation (a counter, **no walk-away timeout** — a latent dependency then blocks caller threads). Netflix API: **10+ billion** command executions/day, **40+** thread-pools per instance, **5–20** threads each (most set to **10**). Its successors kept the semaphore form as the default.
- **Azure Architecture Center** (ms.date 2026-03-19) now equates bulkhead with **cell-based architecture**. That equation is Azure's; **this note keeps the tactic and leaves the style to E13**. Its rules: partition along bounded contexts; combine with retry, breaker, throttling; consumer-side bulkheads from processes, thread pools, semaphores; service-side from VMs and containers; separate queues per async consumer; prefer built-in platform limits. A current addendum: AI/inference workloads need strict bulkheads because model deployments carry their own quotas — isolate deployments per workload or tenant.
- Vocabulary: *bulkhead* (per-dependency capacity), *semaphore isolation* (a counter on the calling thread), *thread-pool isolation* (a bounded pool per dependency; the caller can time out and leave), *connection-pool isolation* (a separate outbound or DB pool per hop), *concurrency circuit-breaking* (Envoy/Istio **limits**, not a failure-rate automaton), *shuffle shard* (a per-customer virtual cell drawn combinatorially), *cell as tactic* (cap the fraction of the fleet a poison request or bad deploy can hit).

## Thread-pool vs semaphore isolation

The Hystrix lesson that survived every rewrite: **a semaphore is not a timeout**.

```
THREAD:     caller ──queue──► dep-pool threads ──I/O──► dependency
            timeout fires on the caller; the pool thread may keep running
SEMAPHORE:  caller ──permit──► same caller thread ──I/O──► dependency
            reject at permit == 0; no walk-away; the I/O timeout is the only bound
```

| | **Thread-pool isolation** | **Semaphore isolation** |
|---|---|---|
| Who runs the call | A thread from *this dependency's* pool | The caller (Tomcat / event-loop / virtual thread) |
| Saturation | Pool + queue full → reject / fallback | Permit count hit → reject |
| Timeout | Yes (Hystrix default **1000 ms**, interrupt-on-timeout **true**) | **No** — a Hystrix timer thread cannot free the caller |
| Cost | Queueing + context switch (Netflix still preferred it at 10B/day) | A counter |
| Failure mode | Pool threads ignore `InterruptedException` (most Java HTTP clients) → the pool stays full after the caller left | A latent dependency pins *caller* threads; the container pool *is* the blast radius |
| When | Untrusted / network clients | Trusted, sub-ms, in-process; or virtual threads + a cap (JEP 444) |

Hystrix `HystrixCommand` defaulted to **THREAD**; `HystrixObservableCommand` to **SEMAPHORE**. Resilience4j inverted the recommendation: `SemaphoreBulkhead` "should work well across a variety of threading and I/O models" and does not ship a shadow pool; `ThreadPoolBulkhead` is the opt-in. Pair every semaphore with a [C7 timeout](TimeoutsDeadlines.md) or the caller still holds the slot for the I/O bound. JDK 21+ virtual threads: never pool them (JEP 444) — cap the *resource* with a semaphore. Polly v8 retired `Policy.Bulkhead`; the counterpart is `AddConcurrencyLimiter(permitLimit, queueLimit)` — a semaphore with an optional queue, not a thread pool.

Spring aspect order puts Bulkhead **innermost**: the permit is taken around the call, after retry and breaker decided to invoke. A retry re-takes the permit (good). An Open breaker never should.

## Connection-pool isolation

Azure's first diagram is the consumer-side rule: one pool for Service B and one for Service C, so A dying cannot take B/C. A single shared HikariCP / `http.Transport` / `http.Agent` for "all outbound" is the anti-pattern the pattern exists to stop.

| Pool | Defaults (verified 2026-09-13) | The catch |
|---|---|---|
| HikariCP 7.1.0 | max **10**, fixed-size recommended, `connectionTimeout` 30 s, `maxLifetime` 30 min, keepalive 120 s | Small-pool doctrine: "a small pool, saturated with threads waiting for connections"; sizing `cores × 2 + effective spindles`; the Oracle demo cut ~100 ms to ~2 ms by *shrinking* the pool. That formula is for a disk/CPU-bound *database* — do not copy it onto a payment HTTP hop. |
| PgBouncer | `pool_mode` session, `default_pool_size` **20** per user+db, `max_client_conn` 100 | Transaction pooling breaks SET/LISTEN/prepared statements/advisory locks; `max_prepared_statements` 200 is the modern escape hatch |
| PostgreSQL | `max_connections` ~**100** (3 reserved) | The hard budget every pool on every replica shares — pools multiply, the server does not |
| Go `http.Transport` | `MaxIdleConnsPerHost` **2**, `MaxConnsPerHost` **0 = unlimited** | The default client is an *unbounded* bulkhead with a 2-connection cache |
| Node `http.Agent` | `maxSockets` **Infinity** | Same shape: no outbound bulkhead unless you set one |
| Tomcat 11 | `maxThreads` **200**, `maxConnections` 8192, backlog 100 | Three nested queues; everything behind the 200 workers waits invisibly |

**Same-pool re-entry deadlock.** A task holding one connection while acquiring a second from the same exhausted pool waits forever. HikariCP: `pool ≥ Tn × (Cm − 1) + 1`. The structural fix is separate pools per tier — a bulkhead of bulkheads. Same-pool re-entry is the one dependency shape a bulkhead cannot tolerate.

**The unbounded-queue trap** (ThreadPoolExecutor): with an unbounded `LinkedBlockingQueue`, no more than `corePoolSize` threads are ever created — "core 10 / max 200 / unbounded queue" is a 10-thread pool with an infinite, invisible queue. Bound the queue; rejection is information.

## Envoy concurrency limits are not C1 breakers

Two different mechanisms share the name "circuit breaking." The [breaker](CircuitBreaker.md) owns the **failure-trip automaton** (Closed / Open / Half-Open, and mesh *outlier detection*). This pattern owns the **limit**. Overflow increments a counter and the router sets `x-envoy-overloaded`. A cluster at 200 rps with 1024 `max_requests` will not overflow and will not look "open" on `rq_open` — that is not a healthy breaker; it is an unused limit.

Envoy 1.40.0-dev enforces five *fully distributed, not coordinated* limits **per upstream cluster and per priority**. Defaults from `circuit_breaker.proto`:

| Knob | Default | Overflow counter | What it isolates |
|---|---|---|---|
| `max_connections` | **1024** | `upstream_cx_overflow` | TCP/HTTP1 connections to the cluster. Envoy still guarantees ≥1 connection to a selected host, so `upstream_cx_active` can exceed the limit by up to `(endpoints) × (connection pools)` |
| `max_pending_requests` | **1024** | `upstream_rq_pending_overflow` | Requests waiting for a ready connection. HTTP/2 with unconfigured max streams multiplexes on one connection — this trips mainly when **no** connection exists yet |
| `max_requests` | **1024** | `upstream_rq_active_overflow` | Outstanding requests to the cluster (HTTP only) |
| `max_retries` | **3** | `upstream_rq_retry_overflow` | Concurrent retries. Prefer a [retry budget](RetryBackoff.md) (20% of active + pending, `min_retry_concurrency` 3) — it **overrides** `max_retries` |
| `max_connection_pools` | **unlimited** | `upstream_cx_pool_overflow` | Instantiated pools (Original-Src can create unbounded pools) |

`track_remaining` defaults **false**. Workers share limits eventually-consistently; races can exceed. Outlier detection (`consecutive_5xx` 5, ejection 30 s × n) is **C1**, not a pool.

**Istio removes the modest defaults.** A DestinationRule with no `connectionPool` stanza is **not** running Envoy's 1024/1024/1024/3. `tcp.maxConnections`, `http.http1MaxPendingRequests`, `http.http2MaxRequests`, and `http.maxRetries` all default to **2³²−1**. The published task (`maxConnections: 1`, `http1MaxPendingRequests: 1`, `maxRequestsPerConnection: 1`): fortio `-c 2` → **85% 200 / 15% 503**; `-c 3` → **36.7% / 63.3%**; proof is the *client* sidecar `upstream_rq_pending_overflow`. `outlierDetection` on the same DestinationRule is C1 — do not tune it to "fix" overflow 503s.

## Shuffle sharding

Traditional shard of 8 workers into 4×2: a poison customer → **25%** blast radius. A per-customer *shuffle shard* of 2-of-8 draws a virtual cell combinatorially; client retries across members route around a victim's outage.

Do **not** mix the two published counts. The 2014 Architecture Blog counts **56 permutations** and, with retries across both members, constrains real impact to **~1/56** (four members → **1/1680**). The Builders' Library counts **28 combinations** for the same 2-of-8. **Route 53 in production**: 2048 virtual name servers, 4 per domain — C(2048,4) ≈ 730 billion shards, no two domains sharing more than two servers. Without the client retry, shared workers couple the shards and the gain collapses. Infima (2014) also shuffle-shards *in-memory* queues and rate-limiters, not only hosts.

## Cells as a tactic (E13 owns the style)

A cell is a complete, independent replica serving a subset of the partition key. **10 cells → ~10% blast radius; 100 → ~1%.** That percentage is the *tactic* — cap the fraction a bad deploy, poison pill, or noisy tenant can hit. The **router is the one shared component** and cannot follow the same compartmentalization strategy: keep it thin, no business logic, cheap hash+modulo mapping, keep serving healthy cells even when one is unreachable. Sizing forces: big enough for the largest tenant and economies of scale; small enough to test at full scale and stay under quotas; a cell should have known maxima in TPS, tenants, storage.

**E13** owns whether the system *is* cell-based — quantum count, zonal vs regional cells, control-plane and router options as a platform. This note only uses cells as another bulkhead granularity *above* pools. Azure's "bulkhead = cell-based architecture" wording is theirs; do not treat a semaphore as a cell architecture.

## Library and mesh defaults (verified 2026-09-13)

| Implementation | Isolation | Default caps | At saturation |
|---|---|---|---|
| Hystrix `HystrixCommand` | **THREAD** | pool core/max **10**, `maxQueueSize` **−1** (SynchronousQueue), timeout **1000 ms** | Reject → fallback |
| Hystrix semaphore | **SEMAPHORE** | execution **10**, fallback **10** | Reject; caller already blocked if in-flight |
| Resilience4j `SemaphoreBulkhead` 2.4.0 | Semaphore | `maxConcurrentCalls` **25**, `maxWaitDuration` **0** | Immediate `BulkheadFullException` |
| Resilience4j `ThreadPoolBulkhead` | Shadow pool | max = processors, core = processors−1, queue **100**, `keepAliveDuration` 20 ms | Queue, then reject |
| Polly v8 `AddConcurrencyLimiter` | Semaphore + queue | Strategy `PermitLimit` **1000**, `QueueLimit` **0** | `RateLimiterRejectedException` |
| .NET standard resilience handler | Concurrency limiter **outermost** | **1000** permits, queue **0** | Reject before retry/breaker |
| Envoy 1.40 | Per-cluster limits | **1024 / 1024 / 1024 / 3** | 503 + `x-envoy-overloaded` |
| Istio `connectionPool` | Same Envoy knobs | **2³²−1** unless set | Unlimited concurrency |

## Little's law: pool size versus timeout

Little (1961): `L = λW`, distribution-independent. Required concurrency = throughput × hold-time. A 200 r/s hop at 100 ms needs **20** permits at the mean; size a margin above healthy sojourn, **not** above the timeout. The [timeout](TimeoutsDeadlines.md) is an independent knob that sets how long a *hung* call occupies a slot.

Eskildsen's napkin (via the [breaker](CircuitBreaker.md) note): a 5 s timeout on a 100 ms worker turns one worker into ~1/50 of capacity. The breaker stops *new* calls; permits already parked stay parked (Azure's *inappropriate time-outs*). A pool sized to healthy `λW` and paired with a too-long T becomes a much smaller cap the moment hang starts.

| Hang fraction (T = 500 ms, L_cap = 24, λ = 200 rps, W = 80 ms) | Extra L | Slots left | Healthy remainder | Fits? |
|---|---|---|---|---|
| 0% | 0 | 24 | 16 | yes |
| 5% | 5 | 19 | 15.2 | yes |
| 20% | 20 | 4 | 12.8 | **no — healthy traffic shed** |
| 100% | — | `λ_cap = 24 / 0.5 = 48 rps` | — | the pool is a 48 rps cap, not 200 |

If 20% hang is plausible (dep slow, not down), either cut T toward p99.9 or raise L — or [shed](LoadShedding.md). A **shared** 24-slot pool with catalog + recs makes the 20% case take 20/24 of *all* outbound capacity. Kubernetes is the kernel-enforced cousin: requests drive scheduling, limits throttle CPU (CFS: a 4-thread burst against a 1-CPU limit burns a 100 ms period in 25 ms and sleeps 75 ms) and OOM-kill memory. QoS ranks by reservation — Guaranteed / Burstable / BestEffort — so the least-reserved partition dies first.

## Observability

Emit **per dependency / cluster / shard**, not a process total. Aggregate dashboards hide exactly what bulkheads reveal.

| Signal | Why |
|---|---|
| Available permits vs max (`resilience4j.bulkhead.available.concurrent.calls`) | Saturation vs unused limit |
| ThreadPoolBulkhead `queue.depth` vs `queue.capacity` | Queue hiding overload |
| Reject count (`BulkheadFullException` / `OnRateLimiterRejected` / Envoy `upstream_rq_*_overflow`) | Admission, not "5xx" |
| Envoy `circuit_breakers.<priority>.{cx,rq_pending,rq,rq_retry}_open` (0/1) | Which *limit* is at cap — **not** C1 Open |
| Hold-time histogram with the C7 timeout drawn | Slots stuck at T |
| `x-envoy-overloaded` / overflow 503 vs C1 ejection 503 | Overflow ≠ host unhealthy |
| Per-shard / per-cell error rate | Shuffle/cell working vs shared-pool (everyone) |

Alert shapes: *reject rate > X for 5 min* (cap too small or dep hung at T); *queue depth pinned at capacity*; *`rq_open == 0` forever on a critical cluster* (limit never sized — not "healthy").

## Tuning

| Knob | Too small | Too large | Starting point |
|---|---|---|---|
| Semaphore / `maxConcurrentCalls` / `max_requests` | Healthy tail rejected | Unused limit; one dep can still take the process | `L ≈ λ × W_healthy × margin` (margin covers p95, not T) |
| `maxWaitDuration` / `QueueLimit` / pending | Burst → 503 | Invisible latency and memory | **0** unless a measured burst is shorter than T. Envoy 1024 pending is a *queue*, not isolation |
| Thread-pool / Hikari size | Same as semaphore too-low | Idle capacity; or (unbounded queue) a fake max | Per-dep `λW`; budget DB pools from `max_connections` *down* |
| Per-attempt timeout (C7) | False-timeout + retry storm | Eskildsen 5 s / 100 ms ≈ 1/50 capacity | Independent of L; then compute `λ_hang = L_cap / T` |
| Shuffle-shard / cell count | 4 shards → 25% | More partitions to operate; router is shared | Combinatorial shards + client retry; cells for deploy/tenant blast radius |
| Envoy `max_retries` / retry budget | Genuine blips cannot retry | Retry storm *through* the bulkhead | Budget 20% of in-flight if the mesh owns retries |

Placement, tightest occupied cap wins: **library** (typed reject) → **connection pool** (per-dep sockets) → **sidecar** (Envoy 1024 vs Istio unlimited) → **cell / shuffle shard** (tenant blast radius). An unset Istio pool plus `maxSockets: Infinity` is no bulkhead. Shopify Semian: host-wide *bulkhead*, per-worker *breaker*.

## Worked calibration — checkout → payment

Constraints are a **design drill**, not a vendor SLA. Measured caller-side `POST /capture`, same AZ, warmed connections, **200 rps**: p50 **80 ms**, p95 **160 ms**, p99.9 **420 ms**.

| Knob | Choice | Why |
|---|---|---|
| `L_mean` / `L_p95` | 200 × 0.080 = **16**; 200 × 0.160 = **32** | Identity, not a guess |
| Semaphore / Envoy `max_requests` | **24** (1.5× mean), wait/pending **0** | Admits the mean and a short burst. If p95 is *queueing you caused*, do not size to it |
| Per-attempt T | **500 ms** | Timeout/healthy = 6.25× (same class as Eskildsen 50×). A hung call occupies ~6 healthy slots — see the hang table above |
| Outbound HTTP / H2 | connections ≥ 24, or `max_requests` as the real cap under multiplex | Do **not** copy HikariCP's max-10 doctrine onto this hop |
| Istio | `http2MaxRequests: 24` (or 32), `http1MaxPendingRequests: 0–8` | Leaving defaults is 2³²−1 |
| Hikari (shared Postgres, 3 replicas) | **10** fixed per instance | 3 × 10 = 30 of ~97 usable server connections |
| Retries | Envoy `max_retries` 3 is *concurrent*, not per-request | Worst-case in-flight = 24 × (1+retries) unless a 20% budget is set. Hedge is forbidden on capture |
| Cells / shuffle | Tactic only: 2-of-8 → ~1/28 combinations (or 1/56 permutations) | Does **not** replace the per-instance 24-permit cap |
| Criticality | user-initiated vs batch reconciliation pools | Batch can starve; users cannot — reservation is the policy |

The deadlock check: no handler acquires two connections; if one ever does, `10 ≥ Tn × (2−1) + 1` caps handler concurrency at 9.

## Testing and operating

- Saturate one dependency with Toxiproxy latency and assert: its pool rejects, siblings' latency is flat, the process survives. That **flat-sibling** assertion *is* the bulkhead test.
- Unit-test rejection paths (`BulkheadFullException` / `RateLimiterRejectedException`) — rejection is a designed outcome, not an error branch.
- Istio's circuit-breaking task is a ready-made overflow drill; the proof is `upstream_rq_pending_overflow`, not the server's logs. Do not confuse those 503s with C1 ejection.
- In Kubernetes, watch `container_cpu_cfs_throttled_periods_total` — a "healthy" pod with throttle spikes is an undersized CPU bulkhead.
- Game-day a cell: drain one and confirm the router keeps siblings serving and per-cell dashboards isolate the event. Force a library bulkhead full to rehearse the reject path at peak, not at 3 a.m.

## Failure modes

- **Shared pool.** One hung dep = process-wide hang. Azure's problem statement.
- **Semaphore without a timeout.** Parent threads stay blocked until the *network* timeout — often the TCP floor.
- **Thread-pool timeout that does not stop work.** `InterruptedException` ignored → pool stays full after the caller left.
- **Queue-as-bulkhead.** R4j `queueCapacity` 100, Envoy pending 1024, unbounded `LinkedBlockingQueue`: overload becomes RAM and latency. Little: `W` grows, so `L` grows faster than `λ`.
- **Timeout holds the slot.** Breaker stops new calls; parked permits stay parked. The 20% hang row above.
- **Istio unlimited mistaken for Envoy 1024.** No stanza → 2³²−1; `maxRetries` also unlimited (retry storm).
- **Envoy 1024 treated as a C1 breaker.** `rq_open == 0` because you never approached 1024.
- **Same-pool re-entry** under load: works in test (pool never full), deadlocks in production.
- **Bulkhead = whole container pool.** A semaphore that is not a *small percentage* of Tomcat threads isolates nothing.
- **Shuffle shard without client retry.** Shared workers couple shards; blast radius returns.
- **Mixing 28 and 56.** Combinations vs permutations for 2-of-8.
- **Cells without a boring router.** Business logic on the shared router is a fleet-wide blast radius (E13).
- **Virtual-thread *pools*.** JEP 444: semaphore-cap the dependency.
- **AI deployment quotas.** Isolate model deployments per workload/tenant or one tenant burns the org quota — still a bulkhead, not a breaker.
- **Shared fate by the back door.** Five "isolated" pools in front of one database, one lock, or one GC heap. The bulkhead is only as real as the deepest shared resource — cells exist because in-process bulkheads all share the host.

**When a bulkhead is the wrong tool.** The efficiency loss is unjustified (Azure). You need a *priority* decision about whom to fail (**C10**). The dependency is hard-down and you want fail-fast + fallback (**C1**), not a full queue. You are designing cell *architecture* — **E13**.

## Trade-offs

| Buy | Pay |
|---|---|
| One failure floods one compartment | Reserved capacity idles; total efficiency drops |
| Damage bounded while the breaker is still counting | More pools to size, watch, and re-size |
| Differentiated QoS by reservation | A new deadlock class (nested acquisition) |
| Envoy 1024 / library semaphores: transparent or typed reject | Istio defaults erase Envoy's caps; overflow 503s look like C1 |
| Shuffle shards / cells: blast radius by arithmetic | A retry across members, a thin router, per-partition ops |
| Little's-law sizing from measured `λW` | A too-long timeout turns the pool into a much smaller cap |

The bulkhead decides **how much may run at once, per compartment**. The [limiter](RateLimiting.md) decides how much may be *asked*. The [timeout](TimeoutsDeadlines.md) decides how long each unit is held. The [breaker](CircuitBreaker.md) decides whether to keep calling at all. [Shedding](LoadShedding.md) decides *which* class to keep when a compartment is already full.

## Sources

Verified 2026-09-13; full URLs, per-claim provenance, and items deliberately left out are in the [catalog research note](../../docs/research/sysdesign/c8-bulkhead-external-research.md). Pool, Kubernetes, and first-pass HikariCP/Go/Node numbers are in [bulkhead-isolation-external-research.md](../../docs/research/sysdesign/bulkhead-isolation-external-research.md). Items already cited in this tree are referenced by their number in [nfr-references.md](../data-intensive-design/nfr-references.md).

- Canon: Nygard, *Release It!* 2nd ed. [12]; Azure Architecture Center, *Bulkhead pattern* (ms.date 2026-03-19); Hystrix wiki How-it-Works / Configuration and `HystrixCommandProperties` / `HystrixThreadPoolProperties`.
- Libraries: Resilience4j 2.4.0 bulkhead docs and `BulkheadConfig` / `ThreadPoolBulkheadConfig`; Polly v8 rate-limiter migration; JEP 444; Spring aspect nest via the [retry defaults](../../docs/research/sysdesign/retry-library-defaults.md).
- Pools and runtime: HikariCP 7.1.0 README and pool-sizing wiki; PgBouncer and Postgres docs; Go `http.Transport`, Node `http.Agent`, Tomcat 11; Java ThreadPoolExecutor javadoc; Kubernetes resources/QoS/eviction and kernel CFS.
- Mesh: Envoy 1.40 circuit-breaking arch + `circuit_breaker.proto` (1024/1024/1024/3); Istio DestinationRule `connectionPool` (2³²−1) and circuit-breaking task (85%/15%, 36.7%/63.3%).
- Shuffle / cells: MacCárthaigh 2014-04-14 (56 permutations; 1/1680 at 4-of-8); Builders' Library combinations / Route 53 2048; AWS Well-Architected cell-based architecture (cell-sizing 10%/1%, cell-routing — router is shared).
- Sizing: Little (1961); Eskildsen napkin and Semian via the [breaker research](../../docs/research/sysdesign/circuit-breaker-external-research.md); checkout T from the [C7 research](../../docs/research/sysdesign/c7-timeouts-external-research.md).
