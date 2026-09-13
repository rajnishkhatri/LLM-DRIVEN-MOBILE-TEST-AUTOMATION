---
type: reference
title: 'Rate limiting and throttling'
description: 'Admission control by policy: bound how much a named key may submit per unit time before the work is done. Complements the breaker (whether to call) and shedding (what to drop when already overloaded). Covers token/leaky/window/GCRA algorithms, 429 + Retry-After, client/gateway/service/mesh placement, distributed limiters, tenant keys, verified library and proxy defaults, failure modes, and when not to use a limiter.'
tags: [system-design-patterns, availability, rate-limiting]
---

# Rate limiting and throttling

**See also:** [retry, backoff, and retry budgets](RetryBackoff.md) · [API gateway](ApiGateway.md) · [load shedding and backpressure](LoadShedding.md) · [circuit breaker](CircuitBreaker.md) · [bulkhead](Bulkhead.md) · [timeouts](TimeoutsDeadlines.md) · [idempotency](Idempotency.md) · [reliability](../data-intensive-design/reliability.md) · [cloud failure-tolerant patterns](../aws/ch08.md) · [catalog research (2026-09-13)](../../docs/research/sysdesign/c4-rate-limiting-external-research.md)

A rate limiter is **admission control by policy**: it bounds how much a *named key* may submit per unit time *before* the work is done. The [breaker](CircuitBreaker.md) decides **whether to call**. This pattern decides **how much a caller may ask**. [Shedding](LoadShedding.md) decides **what to drop when the server is already overloaded**. [ch08](../aws/ch08.md) names Rate Limiter as the third of three failure-tolerant patterns (with breaker and retry) — “per user, per service, or globally” — and stops there; this note owns the algorithms, the hop, and the headers.

Quality attributes: **availability** under abuse and spikes, **fairness** across tenants, and **cost control**. The costs are another distributed-state component, a policy that must track real capacity, 429s that clients must handle well, and a fail-open dilemma: the store that enforces fairness is itself a dependency on the request path.

## Lineage and vocabulary

- **RFC 6585 §4** (2012) added `429 Too Many Requests`: the user sent too many requests in a given time. The response SHOULD explain, MAY carry `Retry-After`, and **MUST NOT** be stored by a cache. The RFC does **not** define how the server identifies the user or counts. §7.2: under attack, answering every request with 429 still costs resources — “it may be more appropriate to just drop connections” ([shedding](LoadShedding.md)).
- **RFC 9110 `Retry-After`** (delay-seconds or HTTP-date) is also used on 503 as “server out of capacity, come back later.” Keep **429** (*this key* exceeded *its* allocation) distinct from **503** / draft-11 `temporary-reduced-capacity` (the *service* is short). Older AWS services (SQS) still 503 for rate-exceeded; NGINX rejects with 503 unless told otherwise; Envoy, Kong, Cloudflare and API Gateway default to 429.
- **IETF `draft-ietf-httpapi-ratelimit-headers-11`** (2026-05-23, expires 2026-11-24, **not an RFC**). Two RFC 9651 Structured Fields: `RateLimit-Policy` (stable; `q` required, `qu` default `"requests"`, `w` window seconds, `pk` partition key) and `RateLimit` (may change per response; `r` remaining required, `t` seconds to reset). Example: `RateLimit-Policy: "burst";q=100;w=60` · `RateLimit: "default";r=50;t=30`. `t` is **delta-seconds** (clock-sync). If both `Retry-After` and `RateLimit` are present, **`Retry-After` MUST take precedence**. Quota is advisory: clients **MUST NOT** treat remaining as an SLA. Pre-2024 `RateLimit-Limit/-Remaining/-Reset` and Envoy `DRAFT_VERSION_03` emit the older `X-RateLimit-*` family.
- **Nygard, *Release It!*** ([12](../data-intensive-design/nfr-references.md)) lists Shed Load, Create Back Pressure and Governor as Stability Patterns — the server-side family. The client-facing limiter is the complementary policy: refuse early so shedding is the backstop, not the first line.
- **Yanacek, *Fairness in multi-tenant systems*** (Builders’ Library, © 2020): divide-quota-by-N only under uniform balancing; consistent-hash keys to a tracker fleet (hot key → hot tracker); async sharing of observed rates; soft allocation + composed buckets.
- **Stripe's four limiters** (2017) stack request-rate, concurrent-request, fleet-usage shedder and worker-utilization shedder — the last two are [C10](LoadShedding.md). The Redis token bucket **fails open**; every new rule dark-launches.
- **Brooker / AWS SDK retry token bucket** is a *retry budget*, not an admission limiter — [C2](RetryBackoff.md) owns it.

**Quota** is a long-window allocation (resets). **Rate** is a short-window bound. **Concurrency** is in-flight. GCP Cloud Quotas (2026-09-03) names all three; mature APIs run all three. A Polly / .NET “rate limiter” that is 1 000 in-flight permits is closer to a [bulkhead](Bulkhead.md).

## Algorithms

Five families share the job. Token vs leaky is only a real trade-off in the *queue* form — meter-form leaky is the mirror image of token (Turner 1986).

| Algorithm | State | Burst behaviour | Distributed cost | When it is the tool |
|---|---|---|---|---|
| **Token bucket** | 1 counter + last-fill time | Burst up to `max_tokens`, then *r*. Admits ≤ *b* + *r·t* over any *t* | One number per key | Edge / mesh local (Envoy `type.v3.TokenBucket`, API Gateway burst = bucket) |
| **Leaky bucket (meter)** | 1 counter | Same math as token, inverted | Same | Interchangeable with token *as a meter* |
| **Leaky bucket (queue)** | FIFO + drain rate | Smooths; **adds latency** | Shared zone (NGINX) | Sync HTTP you are willing to *delay* |
| **Fixed window** | 1 counter + TTL | Full limit at *t=0* of every window; a straddle can admit ~2× | `INCR`+TTL; cheap | Quotas (GitHub-style hourly / epoch reset) |
| **Sliding window log** | Timestamp per request | Exact | O(requests) memory | Cloudflare rejected it at long periods (2017-06) |
| **Sliding window counter** | prev + curr | `rate = prev × (window − elapsed)/window + curr` | Two numbers, one `INCR` | Distributed accuracy-per-byte |
| **GCRA** | 1 TAT | Rolling burst τ; no drip process. Allow iff `TAT − (τ + T) ≤ now`, then TAT += T | One value; clock must be the store’s | Per-tenant Redis (redis-cell) |

Cloudflare (2017-06): 50 req/min, 42 in the previous minute, 18 in the first 15 s of the current → `42 × (45/60) + 18 = 49.5` → one more request trips. Over 400 M requests / 270 k sources: **0.003%** wrongly allowed or limited; mean **6%** rate difference; **zero false positives**. Increments ran **asynchronously** so the request path only checked a cached “mitigation started” bit.

**GCRA / redis-cell** (`CL.THROTTLE`): example `CL.THROTTLE user123 15 30 60` = 30 tokens / 60 s, max burst 15. Response: `[limited (0\|1), limit = max_burst+1, remaining, retry_after_s (−1 if allowed), reset_s]`. Pin GCRA to the store’s `TIME` if callers are multi-host. README is “best effort” maintenance.

**Resilience4j RateLimiter is none of the above by name.** It partitions epoch nanoseconds into cycles of `limitRefreshPeriod` and resets permissions to `limitForPeriod` at each cycle start — a **fixed window whose period you choose**. Defaults (2.4.0): `timeoutDuration` **5 s**, `limitRefreshPeriod` **500 ns**, `limitForPeriod` **50**. 50 permits / 500 ns ≈ **10⁸ permits/s** if left untouched — a default that does not limit. `timeoutDuration` is a *wait* (shaping), not a fast reject.

NGINX `limit_req` *is* the queue form: excess ≤ `burst` are delayed to `rate`; `nodelay` admits the burst immediately (consumes slots); beyond burst → `limit_req_status` default **503**.

## 429, Retry-After, and headers

Cooperation ladder (this note owns the *server* side; [C2](RetryBackoff.md) owns the client retry):

1. Emit **429** for *this key’s* allocation, **503** for *everyone’s* capacity. draft-11 maps those onto `quota-exceeded` vs `temporary-reduced-capacity`.
2. Put **`Retry-After`** in delay-seconds (Envoy clamps ≥ 1 s). draft-11: if both headers exist, **`Retry-After` wins**.
3. Also emit remaining/reset (`RateLimit` / `X-RateLimit-*` / vendor `x-ratelimit-*`) so healthy clients can *pace* instead of bouncing. GitHub sends `x-ratelimit-remaining` with an **epoch** reset; Stripe marks real rate-limit 429s with `Stripe-Rate-Limited-Reason` (a 429 without it is something else).
4. **Do not** treat a 429 as a breaker failure of the *whole provider* — Azure accelerated breaking + Polly `RetryAfter` scope the trip to the quota that was hit ([C1](CircuitBreaker.md)).
5. Retry a 429 only after the advertised delay, under the retry budget, with jitter. A fleet that retries 429s immediately *is* a retry storm. Spend-cap / quota-exhausted 429s (no `retry-after`) are **not** retryable.

Envoy (local and global, 1.40.0-dev): `enable_retry_after_header` default **false**. When true: global uses the largest RLS `duration_until_reset` among over-limit descriptors; local uses seconds until the next token; neither overwrites an already-present `Retry-After`. The header is **not** emitted for upstream-generated 429s. `x-envoy-ratelimited` is set unless disabled — Envoy retries that header only if the retry policy lists it.

RFC 6585 §7.2 is the escape hatch when 429s themselves are the load: drop the connection.

## Where it lives

The same algorithm at four hops is four different products. [C6](ApiGateway.md) owns “should we have a gateway”; this table owns “if a limiter lives here, what does it isolate.”

| Hop | What it isolates | State scope | Trade-off |
|---|---|---|---|
| **Client library** (Resilience4j, Polly, .NET standard handler) | *This process’s* outbound (or inbound) rate / concurrency | Per process; Polly can partition by a context key | Typed reject; invisible to the fleet. .NET/Polly default is a **concurrency** limiter (1 000 permits, queue 0), *not* a token bucket. |
| **In-service / app** (redis-cell, Redis `INCR`, Stripe-style bucket) | Tenant or key the *business* understands | Shared store | Accurate fairness; store is a dependency on the request path. |
| **Sidecar / mesh** (Envoy local or global+RLS) | Cluster / route / descriptor | Local = **per Envoy process** (default) or per downstream connection; `local_cluster_rate_limit` shares one bucket across the local cluster so N sidecars do **not** become N×. Global = one RLS. | Transparent; local is inert until `filter_enabled`/`filter_enforced` are raised from **0%**. Global adds a 20 ms RPC. |
| **Gateway / edge** (API Gateway, Cloud Armor, NGINX, Cloudflare) | Account / API key / IP / WAF characteristics | Per region, per colo, or per node — *deliberately approximate* | Cheap reject before origin; [C6](ApiGateway.md)’s hop. Cloud Armor and API Gateway both document “targets, not ceilings.” |

Stacking all four without a single owner multiplies: a client 1 000-permit limiter in front of a gateway 10 k RPS account cap in front of ten Envoys each at 100 r/s is not “the” limit. Pick **one fairness owner** (usually the store or RLS, keyed by tenant) and treat the others as coarse backstops.

## Distributed enforcement

**Redis official pattern** (redis.io `INCR`). Pattern 1: `ip:unixtime` + `MULTI`/`INCR`/`EXPIRE`/`EXEC`. Pattern 2: single counter, `INCR` then `EXPIRE` iff the value is 1 — documented **race**: client dies between `INCR` and `EXPIRE` → key leaked, **throttled forever**. Fix: 3-line Lua via `EVAL` (`incr`, `expire` iff 1).

**Envoy global filter + envoyproxy/ratelimit** (1.40.0-dev). Filter: required `domain`; gRPC to RLS per matching descriptor; `timeout` default **20 ms** (0 = infinite); `failure_mode_deny` unset = **false** (fail-open; counted in `failure_mode_allowed`); over-limit **429**; `filter_enabled`/`filter_enforced` default **100%** (the opposite of local). RLS: YAML `domain` + nested descriptors; `rate_limit {unit: second\|minute\|hour\|day, requests_per_unit}` — **fixed-window** counters; `BACKEND_TYPE` default **redis**; `NEAR_LIMIT_RATIO` default **0.8**; `LOCAL_CACHE_SIZE_IN_BYTES` default **0** (over-limit freecache is **off** until sized); `EXPIRATION_JITTER_MAX_SECONDS` default **300** (spreads Redis TTLs — a window-edge herd control); `shadow_mode` per descriptor.

**Local-first.** Envoy local token bucket: `fill_interval` **≥ 50 ms**; `tokens_per_fill` default **1**; `always_consume_default_token_bucket` default **true**; `local_rate_limit_per_downstream_connection` default **false** (bucket per **process**); `max_dynamic_descriptors` default **20**. **`local_cluster_rate_limit`**: if set, N Envoys in the local cluster share one logical bucket so the gateway’s limit stays X, not N·X — the documented fix for per-instance multiplication. Must not be combined with per-connection buckets.

**Fail-open is the documented default** wherever a store is involved: Envoy `failure_mode_deny` false; Kong `fault_tolerant` true; Stripe. Fail-closed (`failure_mode_deny` true → 500) turns the limiter into a SPOF. `failure_mode_deny_percent` can split the fleet.

Yanacek’s fleet options: divide quota by N only under uniform balancing; consistent-hash keys to a tracker fleet; or share observed rates asynchronously. Cloudflare keeps counters **per data center**. HAProxy peers replicate stick-table rates but **overwrite, never sum**.

## Tenant keys and fairness

A limiter without a key is a global governor. A limiter keyed on **IP** is a NAT lottery. Prefer the identifier the *quota is sold on*: API key, account, tenant, org, workspace, model.

| Source | Key menu (verified 2026-09-13 or first-pass) |
|---|---|
| Envoy descriptors | Compose `remote_address` × header × `generic_key` × cluster; unmatched → default bucket (local, if `always_consume_default` is true) |
| Cloud Armor (2026-09-03) | `ALL`, `IP`, `XFF_IP`, `HTTP_HEADER` / `HTTP_COOKIE` (first 128 B), `HTTP_PATH`, `SNI`, `REGION_CODE`, `TLS_JA3` / `TLS_JA4`, `USER_IP`, `ASN`; up to **three** keys. Header/cookie/SNI missing → `ALL` (one shared bucket — a fairness foot-gun) |
| Kong `limit_by` | Default **consumer**; also credential, ip, service, header, path, consumer-group |
| GCP Cloud Quotas | Project / folder / org; some user-level. Per-day rate quotas reset at midnight **Pacific Time** |
| Providers | GitHub user/app; Stripe account; Anthropic org (+ workspace caps); OpenAI org/project |

**Hierarchy.** Per-tenant limit sheds only that tenant. A global backstop is still needed for the “all tenants at once” case — that is [C10](LoadShedding.md) if the sum of in-quota traffic exceeds capacity. Yanacek: *soft allocation* lets a tenant burst into unused capacity with in-quota traffic prioritized; compose buckets in sequence (low-rate/high-burst then high-rate/low-burst) for “high burst, bounded burst *rate*”; cost-aware debit after completion. Anthropic workspace caps may *sum above* the org cap; the org cap always binds.

**Cloud Armor region multiply.** Thresholds are enforced **independently in each region** where the backend is deployed: two regions × 5 000 = 10 000 possible. Docs: use for **abuse / availability, not strict quota or licensing** — enforced rates are approximate.

## Library defaults (registry-verified, 2026-09-13)

| Library | Algorithm | Defaults | Notes |
|---|---|---|---|
| **Resilience4j RateLimiter 2.4.0** | Fixed cycle | `timeoutDuration` **5 s**; `limitRefreshPeriod` **500 ns**; `limitForPeriod` **50**; `drainPermissionsOnResult` off | Default rate is ~10⁸/s. Wait-then-`RequestNotPermitted`. Spring aspect: Retry( CB( **RateLimiter**( TimeLimiter( Bulkhead )))) |
| **Polly v8 RateLimiter** | Thin wrap of `System.Threading.RateLimiting` | `PermitLimit` **1000**, `QueueLimit` **0** — a **concurrency** limiter | `RateLimiterRejectedException.RetryAfter` optional. Package is `Polly.RateLimiting` |
| **.NET standard resilience handler** | Same concurrency limiter, **outermost** | Queue **0**, Permit **1 000** | Then total timeout 30 s → retry → breaker → attempt 10 s |
| **redis-cell** | GCRA | No implicit limit — args on every call | Maintenance-mode warning. Response maps onto Limit/Remaining/Retry-After/Reset |

Resilience4j Micrometer: gauges `resilience4j.ratelimiter.available.permissions` and `.waiting.threads` tagged `name`. Events: `onSuccess` / `onFailure` (FAILED_ACQUIRE). Ten 60 s LLM calls consume 10 of Polly’s 1 000 permits at ~0.16 r/s — concurrency mistaken for rate.

## Proxy, mesh and cloud defaults (verified 2026-09-13)

| System | Model | Admit / reject defaults | Fail / shadow |
|---|---|---|---|
| **Envoy local** 1.40.0-dev | Token bucket / process | Status **429**; `filter_enabled`/`filter_enforced` **0%** (inert); `fill_interval` ≥ **50 ms**; `tokens_per_fill` **1**; `Retry-After` **off**; `X-RateLimit` **off** | No RLS; stats `enabled`/`ok`/`rate_limited`/`enforced` |
| **Envoy global** 1.40.0-dev | Descriptor → RLS | Status **429**; RLS timeout **20 ms**; enabled/enforced **100%**; `Retry-After` **off** | `failure_mode_deny` false; `status_on_error` **500** |
| **envoyproxy/ratelimit** | Fixed window in Redis | `unit` second\|minute\|hour\|day; `NEAR_LIMIT_RATIO` **0.8** | `shadow_mode`; local cache size **0**; TTL jitter **300 s** |
| **NGINX `limit_req`** | Leaky-bucket queue | `burst` **0**; `limit_req_status` **503**; 1 MB ≈ 16 k / 8 k states (32/64-bit) | `limit_req_dry_run` **off**; `$limit_req_status` PASSED/DELAYED/REJECTED |
| **Kong plugin** | Windows per `limit_by` | `policy` **local** (diverges as nodes scale); `error_code` **429**; emits X-RateLimit-* + Retry-After | `fault_tolerant` **true**; `cluster` not in hybrid/Konnect |
| **HAProxy** stick-tables | `http_req_rate(period)` per key | Example deny 429; peers **overwrite, never sum** | Enterprise adds an aggregator |
| **AWS API Gateway** | Token bucket, **best-effort** | Account/Region: **10 000 RPS + 5 000 burst** (burst **not** customer-adjustable). 13 newer Regions: **2 500 / 1 250**. Throttled → **429**. Order: usage-plan → stage method → account → AWS Regional | “Targets rather than guaranteed ceilings.” |
| **GCP Cloud Armor** (2026-09-03) | Throttle or `rate_based_ban` | Default security policy at LB create: **500 req / 60 s**. `exceed_action` deny 403/404/**429**/502; docs **recommend 429**. Per-backend **and** per-region | Preview mode. **Approximate — not for licensing** |
| **Cloudflare WAF rules** | Expression + characteristics | Period 10–3600 s; `mitigation_timeout > 0` blocks for the duration, `0` throttles only the excess; default 429; **per-colo** counters | Can count by **response** fields (only 401/403s) |

Read the table as a design space, not a recommendation. Two traps hide in the defaults: Envoy local looks configured and is **inert**; Resilience4j looks configured and does **not limit**.

## Interaction with retry storms and shedding

```
admit (C4) ──429 + Retry-After──► client paces / C2 retries under budget
     │
     ├─ admitted ──► work
     │                  └─ still overloaded? ──► C10 shed (drop by priority / goodput)
     └─ store down + fail-open ──► C4 is gone; C10 is the only brake
```

- **C4 then C2.** A correct 429 with `Retry-After` + jitter is *admission control*. A 429 retried immediately, retried at every hop, or counted as a 5xx into a fleet-wide breaker, is a **retry storm**. Envoy’s rate-limited retry path already jitter-waits `random(interval, interval·1.5)` capped at 300 s — but only if `retry_on` includes the rate-limit condition. Default Envoy retries are **off**.
- **C2 then C4.** Client-side token buckets (AWS SDK since 2016, gRPC `retryThrottling`) cap *retries*, not first attempts. They do not replace a server limiter.
- **C4 is not C10.** C4 is *declared policy* (this tenant may have 10 r/s). C10 is *measured capacity* (this process has 50 ms of queue and will drop prefetch first). In-quota traffic can still overload the fleet — that is when shedding fires.
- **Window-edge herd.** Fixed-window reset + every client waking at `t` is a synchronized retry wave (Pokémon GO 20× is the [C2](RetryBackoff.md) cousin). Mitigations with precedent: GCRA / token-bucket *continuous* replenishment; RLS `EXPIRATION_JITTER_MAX_SECONDS` 300; Stripe “backoff + jitter + client-side token bucket”; draft-11 `t` as delta-seconds so clocks do not align on an epoch.

## Observability

Emit per rule *and* per key where cardinality allows:

| Signal | Why |
|---|---|
| Allowed / limited / **near-limit** (RLS 80%) | Capacity conversation vs incident |
| `failure_mode_allowed` / store errors | How often C4 was *off* |
| `enabled` vs `enforced` vs `rate_limited` (Envoy local) | Shadow gap |
| `$limit_req_status` DELAYED vs REJECTED | Shaping vs shed |
| 429 vs 503 vs 529 vs `x-envoy-ratelimited` | Who fired, which semantic |
| `Retry-After` histogram | Clients that ignore it show up as retry storms ([C2](RetryBackoff.md)) |
| Resilience4j `available.permissions` / `waiting.threads` | Default 500 ns cycle will sit at 50 forever if unused |
| Key + applied limit on every request (log) | Offline true/false-positive rate (Yanacek / Stripe) |

Alert: *sustained near-limit* (raise the quota or the capacity) and *fail-open engagement* (protection off). Do not page on a single 429.

## Tuning

| Knob | Too low | Too high | Starting point |
|---|---|---|---|
| Sustained rate *r* | Honest clients 429; support load | Callee saturates while C4 says “in quota” → [C10](LoadShedding.md) | Per-tenant p99 usage + headroom, **below** the fleet shed point |
| Burst *b* / `max_tokens` / NGINX `burst` | Bursty-but-honest fail | Window-edge or deploy spike hurts | A few seconds of *r* (token/GCRA) or an explicit `burst` |
| Window / `limitRefreshPeriod` / Armor `interval_sec` | Boundary herds (fixed) | Memory (log) or stale fairness | Sliding counter or GCRA for distributed; token bucket at the edge |
| Key | One noisy tenant hides in `ALL` / IP / NAT | Cardinality explodes the store | Tenant first; tenant × route where costs differ |
| Enforcement scope | N× after scale-out (unless `local_cluster_rate_limit`) | 20 ms RLS on every request; store SPOF | One fairness owner + a local process backstop |
| `timeoutDuration` / NGINX delay | Fast 429, more retries ([C2](RetryBackoff.md)) | Threads wait; looks like a hang to [C7](TimeoutsDeadlines.md) | Shape async work; reject sync HTTP |
| Fail-open vs closed | Fail-open: protection vanishes under load | Fail-closed: limiter *is* the outage | Fail-open the *central* store, alarm it; keep a local backstop that cannot fail open |

Shadow first: Envoy `shadow_mode` / local 100% enabled 0% enforced / NGINX `limit_req_dry_run` / Armor preview. Compare would-be 429s to incidents for a week. Revisit after a scale-out: N new nodes × local bucket = N× limit unless `local_cluster_rate_limit` or RLS. Emit `Retry-After` (Envoy’s flag is off until you set it).

## Worked calibration — multi-tenant checkout API, 1 000 RPS fleet

Constraints are a **design drill**, not a vendor SLA. Method: GCRA for the tenant key; Envoy local as a loose backstop; API Gateway as the [C6](ApiGateway.md) hop; [C2](RetryBackoff.md) honouring `Retry-After`; [C10](LoadShedding.md) as the last brake.

Measured (14 days, production-shaped, not sandbox): 80 tenants, p99 concurrent *active* = 20; per-active-tenant p99 = 8 r/s; p99.9 = 22 r/s (brief bursts); fleet healthy capacity ≈ 1 000 r/s before p99 latency walks; 10 mesh pods.

| Knob | Choice | Why |
|---|---|---|
| Tenant algorithm | GCRA via redis-cell: `CL.THROTTLE tenant:{id} 30 10 1` (10 r/s, burst 30) | Continuous replenishment; atomic; returns `retry_after_s`. 10 r/s × 20 actives = 200 r/s typical; 80 × 10 = 800 r/s if everyone is busy — under 1 000. |
| Tenant key | `tenant_id` from auth, **not** IP | NAT / mobile CGNAT would couple strangers. |
| Global / fairness owner | RLS or redis-cell (one store) | One owner. Descriptors: `(tenant_id)` + `(tenant_id, route)` for `/capture` at 2 r/s. |
| Mesh local backstop | Envoy `local_cluster_rate_limit` at ~1 200 (1.2× capacity) | 10 × 12 r/s/pod = 120 r/s if you forget cluster-share — *too low* as a global, *fine* as a per-pod safety. Prefer cluster-share so divide-by-N is not required. |
| Gateway ([C6](ApiGateway.md) hop) | API Gateway usage-plan 50 r/s / burst 25 *per API key* if keys = tenants; account 10 k RPS is not the design limit | Best-effort; do not treat 10 k as headroom you sold. |
| Response | **429** + `Retry-After` (`enable_retry_after_header: true`) + `RateLimit: "tenant";r=…;t=…` | draft-11: `Retry-After` wins. NGINX stay at 503 only if you *mean* “server full” — that is C10. |
| C2 | Honour `Retry-After`; full jitter; **one** layer; 10% retry budget | Do not retry 429 from the mesh *and* the SDK. Scope any breaker open to `tenant × route`, not the payment provider. |
| C10 | Shed prefetch / batch when pod CPU or queue says overloaded, *even if* the tenant is in quota | 80 × 10 r/s = 800 is in-policy and still near the wall. |
| Store-down | RLS/Redis **fail-open**, page on `failure_mode_allowed`; local Envoy bucket stays up | Central fairness disappears; local backstop + C10 remain. |
| Rollout | One week `shadow_mode` / dry-run; log key + would-be verdict; then raise `filter_enforced` | Guessed limits are the usual outage. |

`POST /capture` is non-idempotent — a 429 must **not** be retried without the [idempotency](Idempotency.md) key. Status GETs may retry after `Retry-After`. If 0.1% false-limit is too expensive (each 429 retries), loosen burst before raising *r*; raising *r* until 429s vanish is how C4 stops being a limiter.

## Failure modes

1. **Per-instance multiplication.** Kong local / Envoy local / NGINX zone / Armor per-region: N hops ⇒ up to N×. `local_cluster_rate_limit` is the Envoy-documented fix; RLS/Redis is the general one.
2. **Hot key.** One over-limit tenant dominates the store. RLS local cache helps only if `LOCAL_CACHE_SIZE_IN_BYTES` > 0 (default **0**). Consistent-hash trackers get a hot node.
3. **Window-edge herd.** Fixed-window reset + synchronized `Retry-After` = [C2](RetryBackoff.md) storm. Prefer GCRA/token; jitter Redis TTLs (RLS 300 s); clients jitter.
4. **Store outage + fail-open.** Protection vanishes under the load you bought the limiter for. Watch `failure_mode_allowed`.
5. **Store outage + fail-closed.** The limiter *is* the SEV.
6. **Redis `INCR`/`EXPIRE` race.** Permanent throttle of a key. Use Lua or redis-cell.
7. **Clock skew.** draft-11 chose delta-seconds for this; GitHub epoch reset inherits it; GCRA must pin to one store clock.
8. **Guessed limits.** Sandbox and pooled Azure reductions lie. Shadow first.
9. **429 handled as failure.** Counted into a fleet breaker or retried without `Retry-After` → outage amplifier ([C1](CircuitBreaker.md) / [C2](RetryBackoff.md)).
10. **429 as the only shed.** RFC 6585 §7.2: answering every attacker with 429 is still work. Drop ([C10](LoadShedding.md)).
11. **IP / `ALL` key.** NAT couples tenants; missing Armor header falls back to `ALL`.
12. **Default-on libraries that do not limit.** Resilience4j 50 / 500 ns; Envoy local 0% enforced (shipped config that looks like a limiter and is not).
13. **Default-on concurrency mistaken for rate.** Polly / .NET 1 000 permits is *in-flight*, not r/s.
14. **Cloud “targets.”** API Gateway and Cloud Armor will over-admit. Do not sell them as licensing counters.
15. **Stale GCP API Gateway quota config.** Rename/remove a metric → **500**, not 429.
16. **LLM `max_tokens` pre-charge / sub-windows.** A 600 RPM Azure limit still 429s at > 10 req in one second.

## When not to use

A rate limiter is the **wrong tool** for: in-process function calls; strict licence metering on an approximate edge (Armor’s own warning); already-overloaded servers (use [C10](LoadShedding.md)); health probes ([C3](Failover.md)) — do not share the tenant bucket with `/healthz`; pure concurrency ([bulkhead](Bulkhead.md) / Polly `AddConcurrencyLimiter`); retry amplification (budget [C2](RetryBackoff.md)); a dependency that is *down* ([breaker](CircuitBreaker.md)).

A **tight** limit is the wrong tool for: the first request after a deploy (cold TLS); multi-region callers measured against one-region histograms; anything whose legitimate burst *is* the product (webhooks, game day, market open).

## Limiters around LLM provider APIs

Model endpoints are token-based, not request-based, and the accounting details change designs. Full RPM/TPM/OTPM tables stay in the [first-pass research](../../docs/research/sysdesign/rate-limiting-external-research.md); what belongs here is **429 scoping**.

| Signal | Limiter / client treatment |
|---|---|
| 429 rate limit **with** `retry-after` / `retry-after-ms` | Honour the delay; scope to the key / tenant / model that hit the limit, **not** the provider. |
| 429 spend-cap / quota exhausted (no `retry-after`) | Open with **no timer** and page a human; probing will not help ([C1](CircuitBreaker.md) LLM table). |
| 529 / 503 overloaded | *Service* short — 503 semantics, not this tenant’s quota. |
| Anthropic OTPM | Counts only **generated** tokens — `max_tokens` does **not** pre-charge. Cache reads do not count toward ITPM (except Haiku 3.5). Workspace caps nest under the org limit. |
| OpenAI throttling estimate | `max(max_tokens`, size estimate) — an oversized `max_tokens` **burns rate limit** even if the answer is short. |
| Azure OpenAI | TPM with RPM coupled by ratio, enforced over **1 s / 10 s sub-windows**; 429s carry `retry-after-ms`. |
| Bedrock | Output tokens burn down quota at model-specific multipliers (5× to 15×); deduction is staged (input + `max_tokens` up front, unused replenished at completion). |

Client side, the cooperation ladder is the same: honor `Retry-After` → pace off remaining/reset headers → local token bucket → adaptive throttling. Keep SDK retries **or** gateway retries, not both.

## Trade-offs

| Buy | Pay |
|---|---|
| Overload prevented before work is done; tenant fairness | Policy must track real capacity or it lies in both directions |
| Cheap rejections (vs doing the work) | Rejections still cost CPU at scale — shedding remains the backstop |
| Machine-readable pacing (headers) | Another stateful, distributed component with a fail-open dilemma |
| Per-tenant blast-radius control | Key and scope choices are product decisions, revisited as tenants grow |
| Library, sidecar or gateway reuse | Defaults will be wrong (inert Envoy local; 10⁸/s Resilience4j; concurrency-as-rate) |

The limiter decides **how much a caller may ask**. Timeouts decide **how long to wait**. Retries and their budget decide **whether to try again**. The [bulkhead](Bulkhead.md) decides **how much may run at once**. [Shedding](LoadShedding.md) decides **what the server drops when policy was wrong**. The [breaker](CircuitBreaker.md) decides **whether the client should call at all**. Coordinate all five.

## Sources

Verified 2026-09-13; the full URL list, per-claim provenance and the items deliberately left out are in the [catalog research note](../../docs/research/sysdesign/c4-rate-limiting-external-research.md). Kong / HAProxy / Cloudflare WAF numeric tables, Stripe/GitHub published limits, and LLM RPM/TPM/burndown tables live in the [first-pass note](../../docs/research/sysdesign/rate-limiting-external-research.md). Items already cited in this tree are referenced by their number in [nfr-references.md](../data-intensive-design/nfr-references.md).

- Canon: RFC 6585 §4 / §7.2; RFC 9110 `Retry-After`; IETF ratelimit-headers draft-11 (2026-05-23); Nygard [12]; Yanacek fairness (© 2020); brandur.org GCRA (2015-09-18) and redis-cell; Cloudflare sliding-window (2017-06); Stripe four-limiter post.
- Libraries: Resilience4j 2.4.0 RateLimiter + Micrometer; Polly v8 RateLimiter; .NET standard HTTP resilience handler; redis-cell `CL.THROTTLE`.
- Infrastructure: Envoy 1.40.0-dev local/global filters and `TokenBucket` proto; envoyproxy/ratelimit README + `settings.go`; redis.io `INCR`; NGINX `limit_req`; Kong plugin; HAProxy stick-tables (2018); AWS API Gateway throttling + limits; GCP Cloud Armor (2026-09-03) and Cloud Quotas (2026-09-03); Cloudflare WAF rules.
- Clients and storms: [RetryBackoff.md](RetryBackoff.md) and [retry-backoff-external-research.md](../../docs/research/sysdesign/retry-backoff-external-research.md) (Brooker jitter, SRE 10% budget, Envoy rate-limited retry path). Breaker scoping of 429: [CircuitBreaker.md](CircuitBreaker.md).
- LLM: Anthropic / OpenAI / Azure / Bedrock / Gemini rate-limit docs in the first-pass note — restated here only where they change 429 scoping or `max_tokens` accounting.
