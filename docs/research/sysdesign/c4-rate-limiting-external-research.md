---
type: research
title: 'Rate limiting & throttling — external research (2026-09-13)'
description: >-
  Group C catalog evidence pass for C4: algorithm family, client/gateway/service/mesh
  placement, 429 + Retry-After, Redis and Envoy RLS, tenant fairness, verified
  library/proxy defaults, and interaction with C2 retry storms and C10 shedding.
tags: [research, system-design-patterns, C4, rate-limiting]
---

# C4 Rate limiting & throttling — catalog research (2026-09-13)

> **What this is.** The catalog evidence pass for **C4**. It **links** the same-day first pass [rate-limiting-external-research.md](rate-limiting-external-research.md) (algorithm math, IETF draft-11 field grammar, Kong/HAProxy/Cloudflare-WAF/Stripe/GitHub/LLM-provider tables) and **deepens** it to the Group C / [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md) bar: mechanics and variants, knobs with verified defaults, observability, tuning, a worked calibration, failure modes, sources. The limiter decides *how much a caller may ask*; the breaker decides *whether to call*; shedding (**C10**) decides *what to drop when already overloaded*.
>
> **Method.** Primary pages fetched 2026-09-13. Numbers and option names reproduced exactly; everything else paraphrased. Facts marked **[→C4-1]** are in the first-pass note and not re-fetched here. Facts marked **[→breaker]** / **[→retry]** are in [circuit-breaker-external-research.md](circuit-breaker-external-research.md) / [retry-backoff-external-research.md](retry-backoff-external-research.md). Unverifiable items are in §10 and are **not** asserted as fact.

---

## 1. Scope and non-goals

**Owns.** Token bucket vs leaky bucket vs fixed/sliding window vs GCRA; client vs gateway vs service vs mesh *placement of a limiter*; HTTP 429 + `Retry-After` and the RateLimit header drafts; distributed counters (Redis `INCR` race, redis-cell `CL.THROTTLE`, Envoy global filter + envoyproxy/ratelimit); fairness and tenant keys; interaction with **C2** retry storms and **C10** shedding; verified library / proxy / cloud defaults with versions or fetch dates; observability and a worked calibration.

**Does not own.** Retry-budget math, jitter algorithms, or what status codes are retryable (**C2** — do not rewrite Brooker jitter or the SRE 10% budget). What to drop when the *server* is already past capacity, queues, LIFO/CoDel, or goodput-over-throughput (**C10**). The API gateway as an architectural *place* to hang a limiter, BFF, or routing (**C6** — this note only treats the gateway as one enforcement hop). Circuit-breaker trip criteria and half-open design (**C1**); this note only supplies 429/`Retry-After` as a *signal* the breaker may accelerate on. Thread/connection-pool isolation (**C8**). Trace graphs (**D4**).

**Does not re-derive.** [ch08.md](../../../cases/aws/ch08.md) § Failure-Tolerant Patterns names Rate Limiter as the third of three (with Circuit Breaker and Retry with Backoff): “per user, per service, or globally”; no algorithm, no status code, no numeric default — link, do not expand. LLM-provider RPM/TPM/OTPM tables stay in **[→C4-1]** except where they change 429 scoping.

---

## 2. Lineage / vocabulary

| Term | Meaning | Named source |
|---|---|---|
| **Rate limit / throttle** | Policy-based admission: bound how much a *named key* may submit per unit time *before* the work is done. | RFC 6585 §4; AWS API Gateway throttling page |
| **Quota** | Long-window allocation (resets), distinct from a short-window rate and from in-flight concurrency. | GCP Cloud Quotas (2026-09-03): allocation / rate / concurrent |
| **Token bucket** | Capacity *b* (burst) + refill *r*; admits ≤ *b* + *r·t* over any *t*. | Envoy `type.v3.TokenBucket`; API Gateway (burst = bucket) |
| **Leaky bucket (meter)** | Counter drained at constant rate; mirror-image of token bucket. | brandur.org 2015-09-18; **[→C4-1]** Turner 1986 |
| **Leaky bucket (queue)** | FIFO shaped to a constant output rate; adds delay. | NGINX `limit_req` (drain = `rate`, queue = `burst`) |
| **Fixed window** | One counter per aligned interval; boundary can admit ~2× inside a straddle. | Redis `INCR` pattern 1; Cloudflare 2017-06-07 |
| **Sliding window counter** | `rate = prev × (window − elapsed)/window + curr`. | Cloudflare 2017-06-07 |
| **GCRA** | One TAT per key; allow iff `TAT − (τ + T) ≤ now`, then TAT += T. No drip. | brandur.org 2015-09-18; redis-cell |
| **429 vs 503** | 429 = *this key* exceeded *its* allocation. 503 / `temporary-reduced-capacity` = the *service* is short. | RFC 6585; draft-11 §5; **[→C4-1]** SQS still 503s rate-exceeded |
| **Fail-open / fail-closed** | Store or RLS down → admit (open) or reject (closed). | Envoy `failure_mode_deny`; Stripe **[→C4-1]** |

**Nygard, *Release It!*** lists **Shed Load**, **Create Back Pressure**, and **Governor** as Stability Patterns — the server-side family. The *client-facing* rate limiter is the complementary policy: refuse early so shedding is the backstop, not the first line **[→breaker §1]**.

**RFC 6585 §4** (fetched datatracker 2026-09-13; rfc-editor.org 409 this session). `429 Too Many Requests`: the user sent too many requests in a given time. Response SHOULD explain; MAY carry `Retry-After`. **MUST NOT** be stored by a cache. The RFC does **not** define how the server identifies the user or counts. §7.2: under attack, answering every request with 429 still costs resources — “it may be more appropriate to just drop connections.”

**RFC 9110 `Retry-After`** cited **[→retry]** (rfc-editor.org 409 this session): delay-seconds or HTTP-date; used on 503 as “server out of capacity, come back later.” Keep 429 (you) and 503 (everyone) distinct.

**IETF `draft-ietf-httpapi-ratelimit-headers-11`** (2026-05-23, expires 2026-11-24, Standards Track, **not an RFC**). Two RFC 9651 Structured Fields: `RateLimit-Policy` (stable; params `q` required, `qu` default `"requests"`, `w` window seconds, `pk` partition key) and `RateLimit` (may change per response; `r` remaining required, `t` seconds to reset, `pk`). Examples: `RateLimit-Policy: "burst";q=100;w=60,"daily";q=1000;w=86400` · `RateLimit: "default";r=50;t=30`. `t` is **delta-seconds** (clock-sync). If both `Retry-After` and `RateLimit` are present, **`Retry-After` MUST take precedence**. Quota is advisory: clients **MUST NOT** treat remaining as an SLA. Problem types: `quota-exceeded` (example 429), `temporary-reduced-capacity` (example 503), `abnormal-usage-detected` (example 429). Pre-2024 `RateLimit-Limit/-Remaining/-Reset` and Envoy `DRAFT_VERSION_03` emit the older `X-RateLimit-*` family.

**Brooker / AWS SDK retry token bucket** is a *retry budget*, not an admission limiter — **C2** owns it **[→retry]**.

**Yanacek, *Fairness in multi-tenant systems*** (Builders’ Library, © 2020) **[→C4-1]**: divide-quota-by-N only under uniform balancing; consistent-hash keys to a tracker fleet (hot key → hot tracker); async sharing of observed rates. Soft allocation + composed buckets. Not re-fetched this pass.

---

## 3. Mechanics

### 3.1 Five algorithms that share a job

| Algorithm | State | Burst behaviour | Distributed cost | When it is the tool |
|---|---|---|---|---|
| **Token bucket** | 1 counter + last-fill time | Burst up to `max_tokens`, then *r* | One number per key | Edge / mesh local (Envoy, API Gateway) |
| **Leaky bucket (meter)** | 1 counter | Same math as token, inverted | Same | Interchangeable with token *as a meter* |
| **Leaky bucket (queue)** | FIFO + drain rate | Smooths; **adds latency** | Shared zone (NGINX) | Sync HTTP you are willing to *delay* |
| **Fixed window** | 1 counter + TTL | Full limit at *t=0* of every window; edge can admit ~2× | `INCR`+TTL; cheap | Quotas (hourly GitHub-style) **[→C4-1]** |
| **Sliding window log** | Timestamp per request | Exact | O(requests) memory | Cloudflare rejected it at long periods (2017-06-07) |
| **Sliding window counter** | prev + curr | Approximation | Two numbers, one `INCR` | Distributed accuracy-per-byte |
| **GCRA** | 1 TAT | Rolling burst τ; no drip process | One value; clock must be the store’s | Per-tenant Redis (redis-cell) |

**Cloudflare 2017-06-07** (fetched). Worked example at 50 req/min: 42 in the previous minute, 18 in the first 15 s of the current → `42 × (45/60) + 18 = 49.5` → one more request trips. Over 400 M requests / 270 k sources: **0.003%** wrongly allowed or limited; mean **6%** rate difference; **zero false positives**; three false negatives, each < 15% over. Increments run **asynchronously** so the request path only checks a “mitigation started” bit, cached in the server until the known end time — that is how they survived 400 k rps to one domain.

**Token vs leaky is only a real trade-off in the queue form.** Meter-form leaky ≡ token **[→C4-1]**. NGINX `limit_req` *is* the queue form: excess ≤ `burst` are delayed to `rate`; `nodelay` admits the burst immediately (consumes slots); beyond burst → `limit_req_status` default **503**.

**GCRA / redis-cell** (README fetched 2026-09-13; “best effort” maintenance). `CL.THROTTLE <key> <max_burst> <count per period> <period> [<quantity>]`. Example `CL.THROTTLE user123 15 30 60` = 30 tokens / 60 s, max burst 15. Response: `[limited (0\|1), limit = max_burst+1, remaining, retry_after_s (−1 if allowed), reset_s]`. Informal benchmark: ~2× a `SET`, “very roughly 0.1 ms” from a client. Clock: brandur — use the store’s `TIME` if callers are multi-host.

**Resilience4j RateLimiter** is **none of the above by name**: it partitions epoch nanoseconds into cycles of `limitRefreshPeriod` and resets permissions to `limitForPeriod` at each cycle start (`AtomicRateLimiter`; also `SemaphoreBasedRateLimiter`). That is a **fixed window whose period you choose**. Defaults (docs + `RateLimiterConfig.java`, 2.4.0): `timeoutDuration` **5 s**, `limitRefreshPeriod` **500 ns**, `limitForPeriod` **50**. 50 permits / 500 ns ≈ **10⁸ permits/s** if left untouched — a default that does not limit. `timeoutDuration` is a *wait* (shaping), not a fast reject; expiry → `RequestNotPermitted`. `changeLimitForPeriod` applies only from the next cycle.

### 3.2 429, Retry-After, and headers

Cooperation ladder (this note owns the *server* side; **C2** owns the client retry):

1. Emit **429** for *this key’s* allocation, **503** for *everyone’s* capacity. draft-11 maps those onto `quota-exceeded` vs `temporary-reduced-capacity`.
2. Put **`Retry-After`** in delay-seconds (Envoy clamps ≥ 1 s). draft-11: if both headers exist, **`Retry-After` wins**.
3. Also emit remaining/reset (`RateLimit` / `X-RateLimit-*` / vendor `x-ratelimit-*`) so healthy clients can *pace* instead of bouncing.
4. **Do not** treat a 429 as a breaker failure of the *whole provider* — Azure accelerated breaking + Polly `RetryAfter` scope the trip to the quota that was hit **[→breaker]**.
5. **C2**: retry a 429 only after the advertised delay, under the retry budget, with jitter. A fleet that retries 429s immediately *is* a retry storm. Spend-cap / quota-exhausted 429s (no `retry-after`) are **not** retryable **[→retry]**.

Envoy (both filters, 1.40.0-dev docs, fetched 2026-09-13): `enable_retry_after_header` default **false**. When true: global filter uses the largest RLS `duration_until_reset` among over-limit descriptors, delay-seconds, ≥ 1 s, does not overwrite an RLS-supplied `Retry-After`; local filter uses seconds until the next token, ≥ 1 s, does not overwrite `response_headers_to_add`. Header is **not** emitted for upstream-generated 429s, when not enforced, or when status ≠ 429. `x-envoy-ratelimited` is set unless `disable_x_envoy_ratelimited_header` — Envoy retries that header only if the retry policy lists it **[→retry]**.

RFC 6585 §7.2 is the escape hatch when 429s themselves are the load: drop the connection (**C10** territory).

### 3.3 Placement — client / gateway / service / mesh

The same algorithm at four hops is four different products. **C6** owns “should we have a gateway”; this table owns “if a limiter lives here, what does it isolate.”

| Hop | What it isolates | State scope | Trade-off |
|---|---|---|---|
| **Client library** (Resilience4j, Polly, .NET standard handler) | *This process’s* outbound (or inbound) rate / concurrency | Per process; Polly can partition by a context key | Typed reject; invisible to the fleet. .NET/Polly default is a **concurrency** limiter (1 000 permits, queue 0), *not* a token bucket. |
| **In-service / app** (redis-cell, Redis `INCR`, Stripe-style bucket **[→C4-1]**) | Tenant or key the *business* understands | Shared store | Accurate fairness; store is a dependency on the request path. |
| **Sidecar / mesh** (Envoy local or global+RLS) | Cluster / route / descriptor | Local = **per Envoy process** (default) or per downstream connection; `local_cluster_rate_limit` shares one bucket across the local cluster so N sidecars do **not** become N×. Global = one RLS. | Transparent; local is inert until `filter_enabled`/`filter_enforced` are raised from **0%**. Global adds a 20 ms RPC. |
| **Gateway / edge** (API Gateway, Cloud Armor, NGINX, Cloudflare **[→C4-1]**) | Account / API key / IP / WAF characteristics | Per region, per colo, or per node — *deliberately approximate* | Cheap reject before origin; **C6**’s hop. Cloud Armor and API Gateway both document “targets, not ceilings.” |

Stacking all four without a single owner multiplies: a client 1 000-permit limiter in front of a gateway 10 k RPS account cap in front of ten Envoys each at 100 r/s is not “the” limit. Pick **one fairness owner** (usually the store or RLS, keyed by tenant) and treat the others as coarse backstops.

### 3.4 Distributed enforcement

**Redis official pattern** (redis.io `INCR`, fetched 2026-09-13). Pattern 1: `ip:unixtime` + `MULTI`/`INCR`/`EXPIRE`/`EXEC` (10 s TTL in their example of 10 req/s). Pattern 2: single counter, `INCR` then `EXPIRE` iff the value is 1 — documented **race**: client dies between `INCR` and `EXPIRE` → key leaked, **throttled forever**. Fix: 3-line Lua via `EVAL` (`incr`, `expire` iff 1). List/`RPUSHX` variant: race only *misses* an admit, still bounds the rate.

**Envoy global filter + envoyproxy/ratelimit** (docs `latest` = 1.40.0-dev; RLS README + `settings.go` fetched 2026-09-13). Filter: required `domain`; gRPC to RLS per matching descriptor; `timeout` default **20 ms** (0 = infinite); `failure_mode_deny` unset = **false** (protobuf; fail-open; counted in `failure_mode_allowed`); over-limit **429** (`rate_limited_status` < 400 coerced to 429); `filter_enabled`/`filter_enforced` default **100%** via runtime keys (the opposite of local). Descriptors from route actions (source_cluster, destination_cluster, request_headers, remote_address, generic_key, header_value_match, extensions). RLS: YAML `domain` + nested descriptors; `rate_limit {unit: second\|minute\|hour\|day, requests_per_unit}` — **fixed-window** counters; `shadow_mode` per descriptor or `SHADOW_MODE` global (default false); `BACKEND_TYPE` default **redis**; `NEAR_LIMIT_RATIO` default **0.8**; `LOCAL_CACHE_SIZE_IN_BYTES` default **0** (over-limit freecache is **off** until sized); `EXPIRATION_JITTER_MAX_SECONDS` default **300** (spreads Redis TTLs — a window-edge herd control); `STOP_CACHE_KEY_INCREMENT_WHEN_OVERLIMIT` default **false**. Stats: `total_hits` / `over_limit` / `near_limit` / `within_limit` / `shadow_mode`.

**Local-first.** Envoy local token bucket: `fill_interval` **≥ 50 ms**; `always_consume_default_token_bucket` default **true**; `local_rate_limit_per_downstream_connection` default **false** (bucket per **process**); `max_dynamic_descriptors` default **20**. **`local_cluster_rate_limit`**: if set, N Envoys in the local cluster share one logical bucket so the gateway’s limit stays X, not N·X — the documented fix for per-instance multiplication. Must not be combined with per-connection buckets.

**Fail-open is the documented default** wherever a store is involved: Envoy `failure_mode_deny` false; Kong `fault_tolerant` true **[→C4-1]**; Stripe **[→C4-1]**. Fail-closed (`failure_mode_deny` true → 500, or `status_on_error` default 500) turns the limiter into a SPOF. `failure_mode_deny_percent` can split the fleet (example: 50% closed / 50% open).

### 3.5 Fairness / tenant keys

A limiter without a key is a global governor. A limiter keyed on **IP** is a NAT lottery. Prefer the identifier the *quota is sold on*: API key, account, tenant, org, workspace, model.

| Source | Key menu (verified this pass or **[→C4-1]**) |
|---|---|
| Envoy descriptors | Compose `remote_address` × header × `generic_key` × cluster; unmatched → default bucket (local, if `always_consume_default` is true) |
| Cloud Armor (2026-09-03) | `ALL`, `IP`, `XFF_IP`, `HTTP_HEADER` / `HTTP_COOKIE` (first 128 B), `HTTP_PATH`, `SNI`, `REGION_CODE`, `TLS_JA3` / `TLS_JA4`, `USER_IP`, `ASN`; up to **three** keys. Header/cookie/SNI missing → `ALL` (one shared bucket — a fairness foot-gun) |
| Kong `limit_by` **[→C4-1]** | Default **consumer**; also credential, ip, service, header, path, consumer-group |
| GCP Cloud Quotas (2026-09-03) | Project / folder / org; some user-level. Rate quotas reset (per-day at midnight **Pacific Time**; per-minute “one minute after the first request in a rolling window”) |
| Providers **[→C4-1]** | GitHub user/app; Stripe account; Anthropic org (+ workspace caps); OpenAI org/project |

**Hierarchy.** Per-tenant limit sheds only that tenant. A global backstop still needed for the “all tenants at once” case (that is **C10** if the sum of in-quota traffic exceeds capacity). Yanacek **[→C4-1]**: *soft allocation* lets a tenant burst into unused capacity with in-quota traffic prioritized; compose buckets in sequence (low-rate/high-burst then high-rate/low-burst) for “high burst, bounded burst *rate*”; cost-aware debit after completion. Anthropic workspace caps may *sum above* the org cap; the org cap always binds **[→C4-1]**.

**Cloud Armor region multiply.** Thresholds are enforced **independently in each region** where the backend is deployed: two regions × 5 000 = 10 000 possible. IP keys are “reasonable” to treat as one region (anycast). Docs: use for **abuse / availability, not strict quota or licensing** — enforced rates are approximate; rare extra-region enforcement.

### 3.6 Interaction with C2 (retry storms) and C10 (shedding)

```
admit (C4) ──429 + Retry-After──► client paces / C2 retries under budget
     │
     ├─ admitted ──► work
     │                  └─ still overloaded? ──► C10 shed (drop by priority / goodput)
     └─ store down + fail-open ──► C4 is gone; C10 is the only brake
```

- **C4 then C2.** A correct 429 with `Retry-After` + jitter is *admission control*. A 429 retried immediately, retried at every hop, or counted as a 5xx into a fleet-wide breaker, is a **retry storm**. Envoy’s rate-limited retry path already jitter-waits `random(interval, interval·1.5)` capped at 300 s **[→retry]** — but only if `retry_on` includes the rate-limit condition. Default Envoy retries are **off**.
- **C2 then C4.** Client-side token buckets (AWS SDK since 2016, gRPC `retryThrottling`) cap *retries*, not first attempts. They do not replace a server limiter. Stacking a client retry on a gateway that already 429s without honouring `Retry-After` is Azure’s Retry Storm antipattern **[→retry]**.
- **C4 is not C10.** C4 is *declared policy* (this tenant may have 10 r/s). C10 is *measured capacity* (this process has 50 ms of queue and will drop prefetch first). In-quota traffic can still overload the fleet — that is when shedding fires. Netflix partitioned limiter / Uber Cinnamon / Stripe’s fleet-usage and worker-utilization shedders live in **C10** **[→breaker alternatives]**.
- **Window-edge herd.** Fixed-window reset + every client waking at `t` is a synchronized retry wave (Pokémon GO 20× is the C2 cousin **[→retry]**). Mitigations with precedent: GCRA / token-bucket *continuous* replenishment; RLS `EXPIRATION_JITTER_MAX_SECONDS` 300; Stripe “backoff + jitter + client-side token bucket” **[→C4-1]**; draft-11 `t` as delta-seconds so clocks do not align on an epoch.

---

## 4. Verified defaults / standards (fetched 2026-09-13)

### 4.1 Libraries

| Library | Version / page | Algorithm | Defaults | Notes |
|---|---|---|---|---|
| **Resilience4j RateLimiter** | 2.4.0 (GitHub 2026-03-14); readme.io + `RateLimiterConfig.java` | Fixed cycle | `timeoutDuration` **5 s**; `limitRefreshPeriod` **500 ns**; `limitForPeriod` **50**; `drainPermissionsOnResult` `any → false` | Default rate is ~10⁸/s. Wait-then-`RequestNotPermitted`. Spring aspect: Retry( CB( **RateLimiter**( TimeLimiter( Bulkhead )))) **[→breaker]** |
| **Polly v8 RateLimiter** | pollydocs.org `strategies/rate-limiter` | Thin wrap of `System.Threading.RateLimiting` | `DefaultRateLimiterOptions`: `PermitLimit` **1000**, `QueueLimit` **0** — a **concurrency** limiter | `RateLimiterRejectedException.RetryAfter` optional. Telemetry: `OnRateLimiterRejected` (Error). Package is `Polly.RateLimiting`, not `Polly.Core` |
| **.NET standard resilience** | learn.microsoft.com http-resilience (fetched 2026-09-13) | Same concurrency limiter, **outermost** | Queue **0**, Permit **1 000** | Then total timeout 30 s → retry → breaker → attempt 10 s. Hedging handler: per-endpoint limiter, same 1000/0 |
| **redis-cell** | brandur/redis-cell README | GCRA | No implicit limit — args on every call | Maintenance-mode warning. Response maps onto Limit/Remaining/Retry-After/Reset |

Resilience4j Micrometer (readme.io/docs/micrometer, 2.4.0 line): gauges `resilience4j.ratelimiter.available.permissions` and `.waiting.threads` tagged `name`. Events: `onSuccess` / `onFailure` (FAILED_ACQUIRE).

### 4.2 Proxies, meshes, clouds

| System | Version / page | Model | Admit / reject defaults | Fail / shadow |
|---|---|---|---|---|
| **Envoy local** | 1.40.0-dev local filter + proto | Token bucket / process | Status **429**; `filter_enabled`/`filter_enforced` **0%** (inert); `fill_interval` ≥ **50 ms**; `tokens_per_fill` default **1**; `Retry-After` **off**; `X-RateLimit` **off** (`DRAFT_VERSION_03` opt-in) | No RLS; stats `enabled`/`ok`/`rate_limited`/`enforced` |
| **Envoy global** | 1.40.0-dev rate_limit filter + proto | Descriptor → RLS | Status **429**; RLS timeout **20 ms**; enabled/enforced **100%**; `Retry-After` **off**; `X-RateLimit` **off** | `failure_mode_deny` false; `failure_mode_allowed` counter; `status_on_error` **500** |
| **envoyproxy/ratelimit** | master README + `settings.go` | Fixed window in Redis | `unit` second\|minute\|hour\|day; `NEAR_LIMIT_RATIO` **0.8** | `shadow_mode`; local cache size **0**; TTL jitter **300 s** |
| **NGINX `limit_req`** | ngx_http_limit_req_module | Leaky-bucket queue | `burst` **0**; `limit_req_status` **503**; `delay` default 0 (all excess delayed); 1 MB ≈ 16 k / 8 k states (32/64-bit, 64/128 B); LRU then error | `limit_req_dry_run` **off**; `$limit_req_status` PASSED/DELAYED/REJECTED(+_DRY_RUN) |
| **AWS API Gateway** | limits.html + request-throttling.html | Token bucket, **best-effort** | Account/Region: **10 000 RPS + 5 000 burst** (RPS increasable; burst **not** customer-adjustable). 13 newer Regions: **2 500 / 1 250**. Throttled → **429**. Order: usage-plan per-client/method → stage method → account → AWS Regional | “Targets rather than guaranteed ceilings.” Burst = “target maximum concurrent submissions” |
| **GCP Cloud Armor** | rate-limiting-overview, updated **2026-09-03** | Throttle or `rate_based_ban` | Default security policy at LB create: **500 req / 60 s**. `interval_sec` ∈ {10, 30, 60, …, 3600}. `exceed_action` deny 403/404/**429**/502 or redirect; docs **recommend 429**. Throttle count 1–1 000 000; ban count 1–10 000. `ban_duration_sec` ∈ {60 … 3600} | Preview mode. Per-backend **and** per-region. **Approximate — not for licensing** |
| **GCP Cloud Quotas** | quotas/overview, updated **2026-09-03** | Allocation / rate / concurrent | No universal numeric default; per-product. Project isolation | Rate reset: day = midnight PT; minute = rolling from first request |
| **GCP API Gateway quotas** | quotas-overview **[→C4-1]** | Config-defined | Empty until `x-google-quota`; apply to the *API*, not one config. Stale rename → **500** `Failed to call Service Control Quota` | Consumer project / API key |

Kong, HAProxy stick-tables, Cloudflare WAF rules (period 10–3600 s, per-colo counters): **[→C4-1]** — not re-fetched.

---

## 5. Knobs, observability, tuning

### 5.1 Knobs

| Knob | Role | Too low | Too high |
|---|---|---|---|
| Sustained rate *r* | Policy vs measured tenant p99 | Honest clients 429; support load | Callee saturates while C4 says “in quota” → **C10** |
| Burst *b* / `max_tokens` / NGINX `burst` | Absorb legitimate spikes | Bursty-but-honest fail | Window-edge or deploy spike hurts |
| Window / `limitRefreshPeriod` / Armor `interval_sec` | How fast the policy forgets | Boundary herds (fixed) | Memory (log) or stale fairness |
| Key | Who shares a bucket | One noisy tenant hides in `ALL` / IP / NAT | Cardinality explodes the store |
| Enforcement scope | Local vs RLS vs store | N× after scale-out (unless `local_cluster_rate_limit`) | 20 ms RLS on every request; store SPOF |
| `timeoutDuration` / NGINX delay | Shape vs reject | Fast 429, more retries (**C2**) | Threads wait; looks like a hang to **C7** |
| Fail-open vs closed | Store/RLS down | Fail-open: protection vanishes under load | Fail-closed: limiter *is* the outage |
| `NEAR_LIMIT_RATIO` / enabled-vs-enforced | Warning vs trip | Alert never fires | Shadow never becomes enforce |

### 5.2 Observability (feeds D4)

Emit per rule *and* per key where cardinality allows:

| Signal | Why |
|---|---|
| Allowed / limited / **near-limit** (RLS 80%) | Capacity conversation vs incident |
| `failure_mode_allowed` / store errors | How often C4 was *off* |
| `enabled` vs `enforced` vs `rate_limited` (Envoy local) | Shadow gap |
| `$limit_req_status` DELAYED vs REJECTED | Shaping vs shed |
| 429 vs 503 vs 529 vs `x-envoy-ratelimited` | Who fired, which semantic |
| `Retry-After` histogram | Clients that ignore it show up as retry storms (**C2**) |
| Resilience4j `available.permissions` / `waiting.threads` | Default 500 ns cycle will sit at 50 forever if unused |
| Key + applied limit on every request (log) | Offline true/false-positive rate (Yanacek / Stripe **[→C4-1]**) |

Alert: *sustained near-limit* (raise the quota or the capacity) and *fail-open engagement* (protection off). Do not page on a single 429.

### 5.3 Tuning

1. Measure per-tenant request *and* cost (tokens, CPU) at the enforcement hop — not sandbox **[→C4-1]**.
2. Set tenant *r* from p99 usage + headroom, **below** the fleet shed point (**C10**).
3. Set burst to a few seconds of *r* (token/GCRA) or an explicit `burst` (NGINX).
4. Key by tenant (or tenant × route if costs differ). Never ship `ALL` / IP as the only key on a multi-tenant API.
5. Shadow first: Envoy `shadow_mode` / local 100% enabled 0% enforced / NGINX `limit_req_dry_run` / Armor preview. Compare would-be 429s to incidents for a week.
6. Fail-open the *central* store, alarm it; keep a **local** process backstop that cannot fail open.
7. Emit `Retry-After` (Envoy flag is off until you set it) and teach clients (**C2**) to honour it with jitter.
8. Revisit after a scale-out: N new nodes × local bucket = N× limit unless `local_cluster_rate_limit` or RLS.

---

## 6. Worked calibration — multi-tenant checkout API, 1 000 RPS fleet

Constraints are a **design drill**, not a vendor SLA. Method: Cloudflare sliding-window / GCRA for the tenant key; Envoy local as a loose backstop; API Gateway as the C6 hop; C2 honouring `Retry-After`; C10 as the last brake.

Measured (14 days, production-shaped, not sandbox): 80 tenants, p99 concurrent *active* = 20; per-active-tenant p99 = 8 r/s; p99.9 = 22 r/s (brief bursts); fleet healthy capacity ≈ 1 000 r/s before p99 latency walks; 10 mesh pods.

| Knob | Choice | Why |
|---|---|---|
| Tenant algorithm | GCRA via redis-cell: `CL.THROTTLE tenant:{id} 30 10 1` (10 r/s, burst 30) | Continuous replenishment; atomic; returns `retry_after_s` for the header. 10 r/s × 20 actives = 200 r/s typical; 80 × 10 = 800 r/s if everyone is busy — under 1 000. |
| Tenant key | `tenant_id` from auth, **not** IP | NAT / mobile CGNAT would couple strangers. |
| Global / fairness owner | RLS or redis-cell (one store) | One owner. Descriptors: `(tenant_id)` + `(tenant_id, route)` for `/capture` at 2 r/s. |
| Mesh local backstop | Envoy local token bucket **12 r/s/pod** (`max_tokens` 24, `tokens_per_fill` 12, `fill_interval` 1 s) **or** `local_cluster_rate_limit` at 1 000 | 10 × 12 = 120 r/s if you forget cluster-share — *too low* as a global, *fine* as a per-pod safety. Prefer `local_cluster_rate_limit` at ~1 200 (1.2× capacity) so divide-by-N is not required. |
| Gateway (C6 hop) | API Gateway usage-plan 50 r/s / burst 25 *per API key* if keys = tenants; account 10 k RPS is not the design limit | Best-effort; do not treat 10 k as headroom you sold. |
| Response | **429** + `Retry-After` (Envoy `enable_retry_after_header: true`) + `RateLimit: "tenant";r=…;t=…` | draft-11: `Retry-After` wins on conflict. NGINX stay at 503 only if you *mean* “server full” — that is C10. |
| C2 | Honour `Retry-After`; full jitter; **one** layer; 10% retry budget | Do not retry 429 from the mesh *and* the SDK. Scope any breaker open to `tenant × route`, not the payment provider **[→breaker]**. |
| C10 | Shed prefetch / batch when pod CPU or queue says overloaded, *even if* the tenant is in quota | 80 × 10 r/s = 800 is in-policy and still near the wall. Shedding is the residual. |
| Store-down | RLS/Redis **fail-open**, page on `failure_mode_allowed`; local Envoy bucket stays up | Central fairness disappears; local backstop + C10 remain. |
| Rollout | One week `shadow_mode` / dry-run; log key + would-be verdict; then raise `filter_enforced` | Stripe/Yanacek: guessed limits are the usual outage. |

`POST /capture` is non-idempotent — a 429 must **not** be retried without the idempotency key (**C9** / **[→retry]**). Status GETs may retry after `Retry-After`.

If 0.1% false-limit is too expensive (each 429 retries), loosen burst before raising *r*; raising *r* until 429s vanish is how C4 stops being a limiter.

---

## 7. Failure modes and when-not-to-use

1. **Per-instance multiplication.** Kong local / Envoy local / NGINX zone / Armor per-region: N hops ⇒ up to N×. `local_cluster_rate_limit` is the Envoy-documented fix; RLS/Redis is the general one.
2. **Hot key.** One over-limit tenant dominates the store. RLS local cache helps only if `LOCAL_CACHE_SIZE_IN_BYTES` > 0 (default **0**). Consistent-hash trackers get a hot node (Yanacek **[→C4-1]**).
3. **Window-edge herd.** Fixed-window reset + synchronized `Retry-After` = C2 storm. Prefer GCRA/token; jitter Redis TTLs (RLS 300 s); clients jitter.
4. **Store outage + fail-open.** Protection vanishes under the load you bought the limiter for. Watch `failure_mode_allowed`.
5. **Store outage + fail-closed.** The limiter *is* the SEV.
6. **Redis `INCR`/`EXPIRE` race.** Permanent throttle of a key. Use Lua or redis-cell.
7. **Clock skew.** draft-11 chose delta-seconds for this; GitHub epoch reset inherits it **[→C4-1]**; GCRA must pin to one store clock.
8. **Guessed limits.** Sandbox and pooled Azure reductions lie **[→C4-1]**. Shadow first.
9. **429 handled as failure.** Counted into a fleet breaker or retried without `Retry-After` → outage amplifier (**C1**/**C2**).
10. **429 as the only shed.** RFC 6585 §7.2: answering every attacker with 429 is still work. Drop (**C10**).
11. **IP / `ALL` key.** NAT couples tenants; missing Armor header falls back to `ALL`.
12. **Default-on libraries that do not limit.** Resilience4j 50 / 500 ns; Envoy local 0% enforced (shipped config that looks like a limiter and is not).
13. **Default-on concurrency mistaken for rate.** Polly / .NET 1000 permits is *in-flight*, not r/s. Ten 60 s LLM calls consume 10 permits at ~0.16 r/s.
14. **Cloud “targets.”** API Gateway and Cloud Armor will over-admit. Do not sell them as licensing counters.
15. **Stale GCP API Gateway quota config.** Rename/remove a metric → **500**, not 429.
16. **LLM `max_tokens` pre-charge / sub-windows** **[→C4-1]** — a 600 RPM Azure limit still 429s at > 10 req in one second.

**When a rate limiter is the wrong tool.** In-process function calls. Strict licence metering on an approximate edge (Armor’s own warning). Already-overloaded servers (use **C10**). Health probes (**C3**) — do not share the tenant bucket with `/healthz`. Pure concurrency (bulkhead **C8** / Polly `AddConcurrencyLimiter`). Retry amplification (budget **C2**). A dependency that is *down* (breaker **C1**).

**When-not-to-use a *tight* limit.** First-request after a deploy (cold TLS, Brooker **[→C7]**); multi-region callers measured against one-region histograms; anything whose legitimate burst is the product (webhooks, game day, market open).

---

## 8. Cross-links

| Id | Why |
|---|---|
| **C1** circuit breaker | 429 + `Retry-After` → accelerated, *scoped* trip; do not blend tenants |
| **C2** retry | Honour `Retry-After`; jitter; one layer; 429 is retryable only when it names a delay; do not rewrite budgets |
| **C6** API gateway | Gateway is a *place*; ch08 + this note’s hop table. C6 owns BFF/routing |
| **C7** timeouts | Shaping (`timeoutDuration`, NGINX delay) holds a worker; bound it |
| **C8** bulkhead | Concurrency ≠ rate; .NET 1000-permit limiter is closer to C8 |
| **C9** idempotency | 429 + retry on `POST /capture` |
| **C10** load shedding | Residual when in-quota traffic still exceeds capacity; RFC 6585 drop-connections |
| **D4** tracing | Record limit key, remaining, `Retry-After` as span attributes |
| First-pass C4 | [rate-limiting-external-research.md](rate-limiting-external-research.md) — Kong/HAProxy/Cloudflare WAF, Stripe/GitHub numbers, LLM TPM tables, Yanacek PDF |
| Cases | [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md), [RetryBackoff.md](../../../cases/SystemDesignPatterns/RetryBackoff.md), [ch08.md](../../../cases/aws/ch08.md) (Rate Limiter paragraph only) |

---

## 9. Sources

Fetched 2026-09-13 unless noted.

**Canon / standards.** datatracker.ietf.org/doc/html/rfc6585 (§4, §7.2) · ietf.org/archive/id/draft-ietf-httpapi-ratelimit-headers-11.html (2026-05-23) · RFC 9110 `Retry-After` **[→retry]** · brandur.org/rate-limiting (2015-09-18) · blog.cloudflare.com/counting-things-a-lot-of-different-things (2017-06-07) · Nygard *Release It!* 2nd ed. **[→breaker §1]** · Yanacek fairness PDF **[→C4-1]**.

**Libraries.** resilience4j.readme.io/docs/ratelimiter + /docs/micrometer · github.com/resilience4j/resilience4j `RateLimiterConfig.java` · GitHub release v2.4.0 (2026-03-14) · pollydocs.org/strategies/rate-limiter · learn.microsoft.com/dotnet/core/resilience/http-resilience · github.com/brandur/redis-cell README (`CL.THROTTLE`).

**Redis / RLS / mesh.** redis.io/docs/latest/commands/incr · github.com/envoyproxy/ratelimit README + `src/settings/settings.go` · envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/rate_limit_filter.html · …/local_rate_limit_filter · …/api-v3/extensions/filters/http/ratelimit/v3/rate_limit.proto · …/local_ratelimit/v3/local_rate_limit.proto · …/api-v3/type/v3/token_bucket.proto (1.40.0-dev).

**Proxies / cloud.** nginx.org/en/docs/http/ngx_http_limit_req_module.html · docs.aws.amazon.com/apigateway/latest/developerguide/limits.html · …/api-gateway-request-throttling.html · docs.cloud.google.com/armor/docs/rate-limiting-overview (2026-09-03) · docs.cloud.google.com/docs/quotas/overview (2026-09-03).

**Cited forward.** [rate-limiting-external-research.md](rate-limiting-external-research.md) (Kong, HAProxy 2018 stick-tables, Cloudflare WAF 2026-08-25, Stripe/GitHub numbers, LLM providers, ITU-T I.371) · [circuit-breaker-external-research.md](circuit-breaker-external-research.md) · [retry-backoff-external-research.md](retry-backoff-external-research.md) · [ch08.md](../../../cases/aws/ch08.md) Rate Limiter paragraph.

---

## 10. Uncertain / left out

- rfc-editor.org returned HTTP 409 for RFC 6585 and RFC 9110 this session; 6585 text is from datatracker. RFC 9110 `Retry-After` semantics cited only via **[→retry]**.
- Envoy `failure_mode_deny` “default false” is the protobuf-unset value; the proto page does not print the word “default.”
- envoyproxy/ratelimit memcache backend “async increment / brief over-admission” **[→C4-1]** was not re-read in `settings.go` this pass.
- redis-cell “~0.1 ms” is the README’s informal figure, not a benchmark I ran.
- Resilience4j 2.4.0 is the latest GitHub release this fetch; no 2.4.x patch was checked for RateLimiterConfig drift (defaults match current master snippets).
- Cloud Armor “500 / 60 s” is the *default security policy created with the load balancer*, not a global Armor default on every policy.
- API Gateway “13 newer Regions” list is copied from limits.html this fetch; Service Quotas console values can disagree with the console throttle pane in those Regions (re:Post threads; not re-verified live).
- GCP API Gateway 500-on-stale-quota: first-pass; not re-fetched.
- Kong / HAProxy / Cloudflare WAF numeric tables: **[→C4-1]** only.
- Yanacek PDF and Stripe four-limiter post: **[→C4-1]** / **[→breaker]**; fail-open is *not* asserted from Yanacek.
- ITU-T I.371 / “GCRA ≡ ATM leaky bucket” via Wikipedia in **[→C4-1]** — not fetched.
- IETF draft intended-status on datatracker vs the archive copy saying “Standards Track”: archive HTML used; datatracker status widget not re-checked.
- PromQL names above are recommendations, not a vendor schema.
- The 1 000 RPS checkout table is a drill.
- LLM RPM/TPM/burndown / spend-cap tables not restated **[→C4-1]**.
