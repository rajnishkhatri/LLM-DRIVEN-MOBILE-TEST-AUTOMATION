---
type: research
title: 'Bulkhead & isolation — external research (2026-09-13)'
description: >-
  Source-verified research backing the Bulkhead Concept in
  cases/SystemDesignPatterns: Nygard/Azure canon, library bulkheads
  (Resilience4j, Polly v8 concurrency limiter, JDK virtual threads),
  connection pools as bulkheads (HikariCP, PgBouncer, Go, Node, Tomcat),
  pool-exhaustion math and deadlocks, Kubernetes requests/limits/QoS/OOM,
  shuffle sharding and cell-based architecture, and Little's-law sizing.
tags: [research, bulkhead, isolation, connection-pools, system-design-patterns]
---

# C8 Bulkhead & isolation — external research (2026-09-13)

**Method.** Every fact verified by fetching the named primary page this session (Browser rendering for the client-rendered AWS Builder Center article). **(cite-forward)** = already verified in [circuit-breaker-external-research.md](circuit-breaker-external-research.md): Hystrix thread-pool vs semaphore isolation and defaults; Netflix partitioned concurrency limiter and concurrency-limits Little's-law sizing; .NET standard handler's 1000-permit rate limiter; Envoy per-cluster concurrency thresholds; Eskildsen napkin math; Shopify tuning.

## 1. Canon

- **Nygard, *Release It!* 2nd ed.** (Jan 2018): Bulkheads is the third stability pattern (list cite-forward). Publisher extracts do not cover ch. 5; the prescription is triangulated from three secondaries (Wikipedia "Bulkhead pattern"; Holý 2015-03-17; juststeveking.com): contain a failure inside dedicated resources — partition capacity per dependency or client class. Granularities attributed to the book: physical redundancy, CPU binding, cluster sub-groups, bounded thread pools, dedicated app-server pools per function (airline example: flight-status lookups get their own servers so check-in survives). Lineage: 2007 1st ed. → Hystrix per-dependency pools (late 2012) → Resilience4j/Polly.
- **Azure Architecture Center, Bulkhead pattern** (ms.date **2026-03-19**): now states bulkhead is "also known as a *cell-based architecture*". Problem: one unresponsive service pins a consumer's shared pool until every service fails; one greedy client exhausts a provider for all. Solution: partition service instances by consumer class; per-dependency pools on the consumer side. Considerations (full list, paraphrased): partition around business/technical requirements; align with DDD bounded contexts; weigh isolation level vs cost/overhead; combine with Retry, Circuit Breaker, Throttling; consumer bulkheads from processes, thread pools, semaphores (resilience4j and Polly named); service bulkheads from VMs/containers/processes — containers a good balance; separate queues + dedicated handlers for async; choose granularity (one tenant vs several per partition); monitor each partition's SLA; prefer built-in platform controls (APIM rate limits, Cosmos RU isolation, AKS limits); **AI/inference workloads often need strict bulkheads due to deployment-level quotas — isolate model deployments per workload or tenant**. Use: isolate per dependency, shield critical consumers, stop cascades. Not suitable: when the efficiency loss or complexity is unjustified. Example: K8s pod with requests/limits.

## 2. Library bulkheads (exact defaults)

| Implementation | Option | Default (source-verified, R4j 2.4.0 era master) |
|---|---|---|
| Resilience4j SemaphoreBulkhead | `maxConcurrentCalls` | **25** |
| | `maxWaitDuration` | **0** (reject immediately) |
| | `fairCallHandlingStrategyEnabled` | **true** (source only) |
| | `writableStackTraceEnabled` | true |
| Resilience4j ThreadPoolBulkhead | `maxThreadPoolSize` | `availableProcessors()` |
| | `coreThreadPoolSize` | `availableProcessors() − 1` (floor 1) |
| | `queueCapacity` | **100** |
| | `keepAliveDuration` | **20 ms** |

Saturation throws `BulkheadFullException` ("Bulkhead 'X' is full and does not permit further calls"). Spring aspect order puts Bulkhead innermost (cite-forward). Docs recommend the semaphore form across threading models.

- **Polly v8**: v7 Bulkhead is gone; migration guide: "The new counterpart to bulkhead is `ConcurrencyLimiter`" — `Policy.Bulkhead(100, 50)` → `AddConcurrencyLimiter(permitLimit: 100, queueLimit: 50)` (Polly.RateLimiting over System.Threading.RateLimiting). Generic rate-limiter defaults: `PermitLimit` 1000, `QueueLimit` 0; rejection = `RateLimiterRejectedException` (optional RetryAfter). `ConcurrencyLimiterOptions`: `PermitLimit` must be set > 0 (no usable default); `QueueLimit` ≥ 0 (0 = reject); `QueueProcessingOrder`.
- **JDK virtual threads (JEP 444, JDK 21)**: "virtual threads are not expensive so there is never a need to pool them"; to cap concurrent access to a limited resource use constructs built for the purpose — **semaphores**. Carry-overs: avoid heavy thread-locals; replace long-I/O `synchronized` with `ReentrantLock` (pinning; softened by later JDKs, unverified here). On 21+: thread-pool bulkheads remain for platform threads/CPU work; semaphore bulkheads are the default isolation tool.

## 3. Connection pools as bulkheads

- **HikariCP** (README 7.1.0): `maximumPoolSize` **10**; exhausted `getConnection()` blocks up to `connectionTimeout` **30 000 ms** then SQLException; `minimumIdle` defaults to max (fixed-size pool recommended); `idleTimeout` 600 000 ms; `maxLifetime` **1 800 000 ms** (set seconds below infra limits); **`keepaliveTime` now 120 000 ms** (was "0 disabled" in 5.1.0 — stale-claim correction). Pool-sizing wiki: `connections = (core_count × 2) + effective_spindle_count`; Oracle RWP demo ~100 ms → ~2 ms by shrinking the pool; "You want a small pool, saturated with threads waiting for connections."; deadlock axiom `pool ≥ Tn × (Cm − 1) + 1`.
- **PgBouncer**: `pool_mode` default **session**; transaction/statement modes; `default_pool_size` **20** per user+db; `max_client_conn` **100**; `max_db_connections` 0. Transaction pooling breaks SET/RESET, LISTEN, WITH HOLD cursors, PREPARE-style statements, session advisory locks; `max_prepared_statements` default **200** rewrites protocol-level prepared statements across shared server connections.
- **PostgreSQL 18**: `max_connections` typically **100**; `superuser_reserved_connections` 3, `reserved_connections` 0 — the hard budget every pool across every replica shares.
- **Go net/http** (go1.27.1): `MaxIdleConnsPerHost` 0 → default **2**; `MaxConnsPerHost` **0 = no limit** (set → dials block); `MaxIdleConns` 0 = no limit. Derived: the default client is an unbounded bulkhead with a 2-connection keep-alive cache — bursts open unbounded connections then churn (TIME_WAIT) instead of queueing.
- **Node http.Agent** (v26.8.2): `maxSockets` **Infinity** per origin; `maxTotalSockets` Infinity; `maxFreeSockets` 256; global agent keepAlive true since **v19.0.0** (2022-10-18). No outbound bulkhead unless set.
- **Tomcat 11.0**: `maxThreads` **200** (−1 via JMX when an Executor is attached); `maxConnections` **8192**; `acceptCount` **100** (OS backlog once maxConnections reached); `minSpareThreads` 10. Three nested queues: backlog → connections → workers.

## 4. Pool exhaustion math and failure modes

- **ThreadPoolExecutor** (Java 21 javadoc): below core → new thread; at core → queue; queue full and below max → new thread; else reject. With an unbounded `LinkedBlockingQueue`, "no more than corePoolSize threads will ever be created" — max is dead config; "core 10 / max 200 / unbounded queue" is a 10-thread pool with an infinite invisible queue. Default rejection `AbortPolicy`; `CallerRunsPolicy` = crude backpressure; `DiscardOldestPolicy` rarely acceptable.
- **Queue-in-front-of-pool latency**: javadoc trade-off (large queues + small pools → "artificially low throughput"); Little's law (§7) converts: λ = 1,000 req/s at W = 50 ms needs L = 50 workers; unbounded queue converts overload into unbounded latency + memory instead of fast rejection.
- **Nested-acquisition deadlock**: HikariCP formula above; javadoc's `SynchronousQueue` rationale ("avoids lockups … requests that might have internal dependencies"). Same-pool re-entry is the one dependency structure a bulkhead cannot have; fix = separate pools per tier or the formula.
- **One slow dependency draining a shared pool** (cite-forward): Hystrix rationale; napkin math (5 s timeout ≈ 1/50 capacity; breaker alone recovers only ~50%). The bulkhead bounds damage while the breaker is still counting.

## 5. Kubernetes isolation

- **Requests vs limits**: requests inform scheduling; limits enforced at runtime — CPU by **throttling** (hard kernel ceiling), memory by **OOM kill** ("memory limits are enforced reactively"). CPU compressible (latency), memory not (kill).
- **CFS quota** (kernel sched-bwc): `cpu.cfs_period_us` default **100 ms**, `cfs_quota_us` −1, `cfs_burst_us` 0. Quota exhausted → throttled until next period: a 4-thread burst against a 1-CPU limit burns 100 ms in 25 ms then sleeps 75 ms.
- **QoS classes**: Guaranteed (all containers CPU+mem requests=limits), Burstable (some request/limit), BestEffort (none).
- **Eviction/OOM ordering** (node-pressure-eviction source md): kubelet ranks by (1) usage > requests, (2) pod priority, (3) usage relative to requests — not by QoS directly; kernel OOM uses pre-seeded `oom_score_adj`: Guaranteed **−997**, BestEffort **1000**, Burstable `min(max(2, 1000 − 1000×req/capacity), 999)`. Criticality = reservation; least-reserved dies first.

## 6. Shuffle sharding and cells

- **AWS Builders' Library, "Workload isolation using shuffle sharding"** (MacCárthaigh; Builder Center republication 2026-06-12): 8 workers unsharded → any poison request hits everyone. 4 shards of 2 → 25% blast radius. Shuffle shard of 2-of-8 → **28 combinations**, scope ~1/28 (7× better than 4 shards); any two customers share at most one worker, so retrying clients route around. **Route 53**: capacity as **2048 virtual name servers**, each domain a shuffle shard of **4** → "730 billion possible shuffle shards" (C(2048,4)); no two domains share more than two; DDoS'd domains movable to dedicated capacity. Recursive shuffle sharding; open-source Route 53 Infima. (2014 blog predecessor uses permutation counts — 56 for 2-of-8; note the convention difference.)
- **AWS Well-Architected cell-based architecture** (2023-09-20): cells = workload-level AZ/Region isolation; goal multi-tenant economics with single-tenant blast radius. **Sizing**: cap and standardize cell size; forces — big enough for the largest tenant and economies of scale, small enough to test at full scale and stay under quotas; 10 cells → 10% blast radius, 100 → 1%; a cell should have known maxima in TPS, tenants, storage. **Routing**: the router is the one shared component — keep it "as simple and horizontally scalable as possible", no business logic; cheap partition-key mapping (hash + modulo); hide the layout; keep serving healthy cells. Router options: Route 53 per cell, API Gateway, thin compute + S3/DynamoDB map. **Zonal vs regional cells**: single-AZ cells align with AZ boundaries (precise zonal evacuation; per-zone routers, AZ-scoped services, extra DR care); multi-AZ cells ride Regional services' resilience (less control over gray zonal failures).

## 7. Sizing

- **Little's law** (Little 1961, *Operations Research* 9(3):383–387): L = λW, distribution-independent. Applied: required concurrency = throughput × latency — 200 req/s × 100 ms ≈ 20 permits; size a margin above, let the wait timeout bound the queue. Same rule as Netflix concurrency-limits (cite-forward) and the shape behind HikariCP's small-pool formula.
- **Per-criticality partitioning** (cite-forward): Netflix partitioned limiter (user-initiated vs prefetch; > 99.4% availability through a 12× spike); Uber Cinnamon's 768 levels; Azure's high-priority consumer pools; K8s QoS as the kernel-enforced version.

## Sources

Canon: learn.microsoft.com/azure/architecture/patterns/bulkhead (2026-03-19) · pragprog.com/titles/mnee2 · en.wikipedia.org/wiki/Bulkhead_pattern · blog.jakubholy.net (2015-03-17) · juststeveking.com bulkhead article.
Libraries: resilience4j.readme.io/docs/bulkhead + master BulkheadConfig.java / ThreadPoolBulkheadConfig.java / BulkheadFullException.java · pollydocs.org rate-limiter + migration-v8 · learn.microsoft.com ConcurrencyLimiterOptions (2025-07-01) · openjdk.org/jeps/444.
Pools: github.com/brettwooldridge/HikariCP README 7.1.0 + tag 5.1.0 + About-Pool-Sizing wiki · pgbouncer.org/config.html + features.html · postgresql.org/docs/current/runtime-config-connection.html · pkg.go.dev/net/http (go1.27.1) · nodejs.org/api/http.html (v26.8.2) + node v19.0.0 release notes · tomcat.apache.org/tomcat-11.0-doc/config/http.html.
Exhaustion/runtime: docs.oracle.com Java 21 ThreadPoolExecutor · kubernetes.io manage-resources-containers + pod-qos + node-pressure-eviction (website source md) · docs.kernel.org/scheduler/sched-bwc.html.
Sharding/cells: builder.aws.com workload-isolation-using-shuffle-sharding (republished 2026-06-12) · aws.amazon.com/blogs/architecture shuffle-sharding (2014-04-14) · docs.aws.amazon.com/wellarchitected reducing-scope-of-impact-with-cell-based-architecture (2023-09-20; cell-sizing, cell-routing, single-az-cells, multi-az-cells).
Sizing: pubsonline.informs.org/doi/10.1287/opre.9.3.383 · cite-forward circuit-breaker note §§1–3.

## Uncertain / could not verify (excluded from the Concept)

- Nygard's exact ch. 5 text (secondaries triangulated; no verbatim phrasing).
- Shuffle-shard counting convention: 2014 blog counts permutations (56), current article combinations (28) — note the convention, don't mix.
- Original Builders' Library publication date (~2019) invisible; archive unreachable.
- PgBouncer docs version; `max_prepared_statements` introduction history.
- HikariCP keepaliveTime flip release not pinned; Oracle RWP pool numbers (2048→96) unconfirmed.
- `fairCallHandlingStrategyEnabled` and BulkheadFullException from source, not docs page.
- kubelet `cpuCFSQuotaPeriod` default not re-verified; K8s pages undated.
- JEP 491 (synchronized without pinning, JDK 24) not verified — excluded.
- Cell placement page known from a snippet only; Go churn consequence and queue-latency arithmetic are labeled derivations.
