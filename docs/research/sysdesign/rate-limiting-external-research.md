---
type: research
title: 'Rate limiting & throttling — external research (2026-09-13)'
description: >-
  Source-verified research backing the Rate limiting Concept in
  cases/SystemDesignPatterns: algorithm math (token/leaky bucket, windows,
  GCRA), distributed enforcement and fail-open defaults, the IETF RateLimit
  header draft and real-world header conventions, infrastructure defaults
  (Envoy, NGINX, HAProxy, Kong, AWS API Gateway, Cloudflare), design
  dimensions, failure modes, and LLM-provider token-based limiting.
tags: [research, rate-limiting, throttling, resilience, system-design-patterns]
---

# C4 Rate limiting & throttling — external research (2026-09-13)

**Method.** Every fact verified against the named primary page on 2026-09-13; paraphrase throughout; numbers exact. **Cited forward, not re-verified** (already in [circuit-breaker-external-research.md](circuit-breaker-external-research.md) / [retry-backoff-external-research.md](retry-backoff-external-research.md)): RFC 6585 (429) and RFC 9110 Retry-After; Stripe's four limiters and its fail-open Redis token bucket; SRE ch. 21 adaptive throttling; Anthropic/OpenAI 429 semantics, spend-cap 429 without retry-after, header families, SDK retry defaults; Envoy retry budgets.

## 1. Algorithms — math and trade-offs

- **Token bucket.** Capacity *b* (burst) + refill rate *r*; admits at most *b + r·t* over any interval *t*. Named as the algorithm by AWS API Gateway (burst = bucket capacity) and Anthropic (capacity "continuously replenished", contrasted with fixed-interval resets). Envoy `type.v3.TokenBucket`: `max_tokens` required (= initial fill); `tokens_per_fill` default **1**; `fill_interval` required (≥ 50 ms in the local filter).
- **Leaky bucket — two algorithms share the name.** *Meter form*: counter drained at constant rate — per Wikipedia (attribution Turner 1986) exactly equivalent to a mirror-image token bucket. *Queue form*: FIFO drained at fixed rate — a shaper that removes burstiness and adds queueing delay. NGINX `limit_req` documents itself as leaky bucket: drain = `rate`, queue = `burst`. "Token vs leaky" is only a real trade-off in the queue form.
- **Fixed window.** O(1), one INCR per key per aligned window; boundary weakness: full limit at the end of one window plus start of the next → worst case ~2× inside a sub-window interval (arithmetic; Cloudflare describes the reset-burst mechanism). GitHub's hourly limit is fixed-window with an epoch reset.
- **Sliding window log.** Timestamp per request (sorted set); exact but O(requests) memory; Cloudflare rejected it for memory/processing at long periods.
- **Sliding window counter (Cloudflare, 2017-06).** Keep previous + current counters; `rate = prev × (window − elapsed)/window + curr`. Example at 50 req/min: 42 prev, 18 in first 15 s → 42×0.75+18 = 49.5 → allowed. Measured over 400 M requests / 270 k sources: 0.003% wrongly allowed or limited; mean 6% rate difference; zero false positives. Two numbers per counter, single INCR.
- **GCRA** (brandur.org, 2015-09-18). One stored value per key: the theoretical arrival time (TAT); emission interval T = period ÷ count; burst tolerance τ; allow iff `TAT − (τ + T) ≤ now`, then TAT += T. Rolling, no drip, no log. **redis-cell**: `CL.THROTTLE <key> <max_burst> <count per period> <period> [<quantity>]` → `[limited, limit = max_burst+1, remaining, retry_after_s, reset_s]`, atomic in Redis. GCRA is the ATM-standardized meter-form leaky bucket (ITU-T I.371 per Wikipedia).

## 2. Distributed enforcement

- **Redis official pattern** (redis.io INCR docs): `ip:unixtime` fixed window, or single counter + EXPIRE — with a documented **race**: client dies between INCR and EXPIRE → key leaked with no TTL, throttled forever; fix = 3-line Lua (`incr`, `expire` iff 1) via EVAL.
- **Centralized**: Envoy global filter calls an external rate-limit service (RLS) over gRPC per request (20 ms default budget) — consistent, adds an RPC + shared dependency. **Local-first with async sync**: Kong `sync_rate` (−1 default = synchronous; ≥ 0 batches to Redis at that interval).
- **Fleet options** (Yanacek, AWS Builders' Library "Fairness in multi-tenant systems", © 2020): (a) divide quota by server count — valid only under uniform request balancing; (b) consistent-hash throttle keys to a tracker fleet (hot key → hot tracker node); (c) async sharing of observed rates — approximate. Cloudflare keeps counters **per data center** — no global counters (2026-04-16 doc).
- **Store down → fail-open is the documented default**: Envoy `failure_mode_deny` default **false** (RLS error ⇒ allowed, counted in `failure_mode_allowed`; true ⇒ 500); Kong `fault_tolerant` default **true** (store down ⇒ proxied unlimited; false ⇒ 500); Stripe fail-open cited forward. envoyproxy/ratelimit's memcache backend increments asynchronously (brief over-admission).

## 3. Standards and header conventions

- **IETF draft-ietf-httpapi-ratelimit-headers-11** (2026-05-23, expires 2026-11-24; still not an RFC). Two RFC 9651 Structured Fields, Lists of policy-named Items: `RateLimit-Policy` params `q` (quota, required), `qu` (unit, default "requests"), `w` (window s), `pk` (partition key); `RateLimit` params `r` (remaining, required), `t` (seconds to reset), `pk`. Examples: `RateLimit-Policy: "burst";q=100;w=60,"daily";q=1000;w=86400` · `RateLimit: "default";r=50;t=30`. `t` is delta-seconds (clock-sync rationale); Retry-After MUST take precedence on conflict; quota is advisory, MUST NOT be treated as SLA. Registers problem types quota-exceeded (429), temporary-reduced-capacity (503), abnormal-usage-detected (429). Pre-2024 `RateLimit-Limit/-Remaining/-Reset` separate fields are an older draft syntax; Envoy's `DRAFT_VERSION_03` option emits that older X-RateLimit family.
- **GitHub REST**: 60/hr unauthenticated; 5,000/hr user (15,000 Enterprise Cloud); Apps 5,000 + 50/repo above 20 capped 12,500; Actions GITHUB_TOKEN 1,000/hr/repo. Headers `x-ratelimit-limit/-remaining/-used/-reset` (**UTC epoch**), `-resource`. Over-limit = 403 or 429. Secondary: ≤ 100 concurrent; 900 points/min/endpoint; 90 s CPU per 60 s; 80 content-generating/min, 500/hr. Guidance: obey retry-after, else wait to reset, else ≥ 1 min exponential.
- **Stripe** (docs.stripe.com/rate-limits): 100 req/s live (25 sandbox) global; endpoints 25 r/s unless noted; Files 20+20; Payouts 15 creates/s, 30 concurrent; Search 20 r/s; PaymentIntents 1,000 updates/object/hr. 429s carry **`Stripe-Rate-Limited-Reason`**: global-rate, endpoint-rate, global-concurrency, endpoint-concurrency, resource-specific; a 429 without it is not a rate limit. Long-window quota: reads ≤ 500 × transactions rolling 30 days, min 10,000/month. Advice: backoff + jitter + client-side token bucket.

## 4. Infrastructure defaults (exact fields)

- **Envoy local rate limit** (`local_ratelimit.v3.LocalRateLimit`): `token_bucket {max_tokens, tokens_per_fill (1), fill_interval (≥ 50 ms)}`; `status` default **429** (< 400 coerced); **`filter_enabled` and `filter_enforced` default 0%** — inert until both raised; `always_consume_default_token_bucket` true; `local_rate_limit_per_downstream_connection` false (bucket per **process**); `enable_x_ratelimit_headers` off (option DRAFT_VERSION_03); sets `x-envoy-ratelimited`; stats enabled/ok/rate_limited/enforced.
- **Envoy global filter + envoyproxy/ratelimit**: required `domain`; RLS gRPC per request; `timeout` **20 ms**; `failure_mode_deny` false; over-limit **429**; `enable_retry_after_header` from RLS duration_until_reset. Descriptors from route actions (source_cluster, destination_cluster, request_headers, remote_address, generic_key, header_value_match). Reference RLS: YAML domain + nested descriptors with `rate_limit {unit: second|minute|hour|day, requests_per_unit}`; **fixed-window** counters (atomic increment + TTL); `shadow_mode` per descriptor; freecache local cache of already-over-limit keys; stats total_hits/over_limit/near_limit (80–100%).
- **NGINX** (`ngx_http_limit_req_module`): `limit_req_zone key zone=name:size rate=Nr/s|m` (1 MB ≈ 16 k states 32-bit / 8 k 128-byte 64-bit; LRU eviction on exhaustion); `limit_req zone=… [burst=N (0)] [nodelay | delay=M]` — leaky bucket: excess ≤ burst queued and delayed to rate; `nodelay` admits burst immediately consuming slots; beyond burst → `limit_req_status` default **503**; `limit_req_dry_run off`.
- **HAProxy** (vendor blog 2018-09-21): `stick-table type ip size 1m expire 10s store http_req_rate(10s)`; `http-request track-sc0 src`; `http-request deny deny_status 429 if { sc_http_req_rate(0) gt 20 }`; three sticky counters sc0–sc2; expire ≥ longest period. Peers replicate but **overwrite, don't sum** rates (Enterprise adds an aggregator).
- **Kong rate-limiting plugin**: windows second…year (no defaults; ≥ 1 required); `limit_by` default **consumer** (credential, ip, service, header, path, consumer-group); `policy` default **local** (per node — diverges as nodes scale), `cluster` (accurate, costly, not in hybrid/Konnect), `redis`; `sync_rate` −1; `fault_tolerant` true; `error_code` 429 "API rate limit exceeded"; emits X-RateLimit-Limit-{Unit}/Remaining + RateLimit-Limit/Remaining/Reset + Retry-After; redis timeout 2000 ms.
- **AWS API Gateway**: account default **10,000 RPS per Region with 5,000-token burst bucket** across HTTP/REST/WebSocket (RPS increasable via L-8A5B8E43; burst not customer-adjustable; 13 newer Regions 2,500/1,250). Order: per-client usage plan → per-method stage → account per-Region → AWS Regional; throttled ⇒ 429; usage plans set rate + burst per method plus day/week/month quota; targets are best-effort.
- **Cloudflare rate limiting rules** (2026-08-25 / parameters 2026-04-29): rule = expression + characteristics (IP; IP-with-NAT; headers/cookies/query/host/path/ASN/country/JA3-JA4; JSON body fields Enterprise Advanced) + period (10–3600 s; Enterprise to 65,535) + requests_per_period (or score_per_period) + mitigation_timeout (0–86400) + action (block, managed_challenge, js_challenge, challenge, log). mitigation_timeout > 0 ⇒ action for the whole duration; 0 ⇒ throttle only the excess. Block default 429, customizable 400–499 + ≤ 30 KB body. `counting_expression` can count by **response** fields (e.g. only 401/403s). Counters per data center.

## 5. Design dimensions

- **Key choice**: Kong limit_by / Cloudflare characteristics are the menus; Envoy descriptors compose keys. Providers: GitHub per user/app; Stripe per account; Anthropic/OpenAI per organization (OpenAI also per project); Azure OpenAI per deployment; Bedrock per account-region-model. IP is the weakest tenant proxy (NAT).
- **Global vs per-instance**: divide-by-N works only under uniform balancing (Yanacek); per-colo (Cloudflare), per-node (Kong local), per-process (Envoy local) are deliberate accuracy/latency/blast-radius dials.
- **Quota vs rate vs concurrency**: Google Cloud formalizes rate quotas (reset) vs allocation quotas (held resources, no reset) (2026-09-03). Stripe runs all three (100 r/s + concurrency limiters + 30-day read allocation). GitHub: hourly quota + per-minute points + 100 concurrent.
- **Hierarchical / fair-share** (Yanacek): per-tenant quotas shed only the unplanned part of a spike; **soft allocation** lets tenants burst into unused capacity with in-quota traffic prioritized; **compose token buckets in sequence** (low-rate/high-burst → high-rate/low-burst) for "high burst, bounded burst rate"; cost-aware variants debit true cost after completion. Anthropic: per-workspace caps under an org limit; workspace caps may sum above it, org limit always applies.
- **Server signals**: split 429 (client exceeded its allocation) from 503/529 (server out of capacity); Yanacek notes 429 only entered HTTP in 2012 and SQS still returns 503 for rate-exceeded; NGINX defaults 503 while Envoy/Kong/Cloudflare/API-GW default 429. Cooperation ladder: Retry-After → pacing off remaining/reset headers → client token bucket → SRE adaptive throttling → AWS SDK STANDARD mode.
- **Admission vs shaping**: reject fast (shed) vs queue/delay (NGINX burst without nodelay; Cloudflare timeout-0 throttling only the excess). Yanacek: async systems absorb and slow; sync systems shed early.

## 6. Failure modes

- **Hot keys**: one over-limit key dominating the store — envoyproxy/ratelimit's local over-limit cache; consistent-hash tracker hot-spots; unbounded key cardinality needs bounded-memory sketches (heavy hitters, counting Bloom filters) (Yanacek).
- **Clock skew**: draft-11 chose delta-seconds for this; GitHub's epoch reset inherits the exposure; HAProxy peers overwrite; GCRA pins each key to one store clock.
- **Window-edge herds**: fixed windows synchronize the wake (everyone waits for the same reset instant); Stripe prescribes jitter; token-bucket replenishment is Anthropic's documented alternative.
- **Store outage**: fail-open defaults mean protection disappears under load (watch Envoy `failure_mode_allowed`); fail-closed turns the limiter into a SPOF.
- **Guessed limits**: log key + limit per request, compute true/false positive rates; deploy in evaluation mode first (Envoy shadow_mode, NGINX dry-run, Envoy enabled-vs-enforced split); sandbox load tests mislead (Stripe); Azure pooled deployments get temporary limit reductions under regional pressure (visible in headers).
- **Per-instance multiplication**: Kong local counters diverge — N nodes ⇒ up to N× the intended limit; same arithmetic for Envoy local buckets and NGINX zones.

## 7. LLM-provider angle

- **Token-based, not request-based.** Anthropic: RPM + ITPM + OTPM per model class; cache-aware ITPM — `cache_read_input_tokens` do **not** count (except Haiku 3.5); ITPM estimated at request start, adjusted to actuals; **OTPM counts only generated tokens — max_tokens does not factor in**. OpenAI: RPM/RPD/TPM/TPD/IPM; throttling estimate = max(max_tokens, char-count estimate) — oversized max_tokens burns limit. Azure OpenAI: TPM quota with RPM coupled by capacity ratios (older chat 6 RPM : 1,000 TPM; o3 1:1,000; o3-mini 1:10,000); estimate counts prompt + max_tokens + best_of; **RPM enforced over 1 s/10 s sub-windows** (600 RPM ⇒ > 10 in any second throttles); 429 carries `retry-after-ms` (2026-05-04). Bedrock: TPM/TPD per model-Region (TPD = TPM × 1440 default) with **burndown rates**: Claude ≤ 4.7 5×, Sonnet 5/Opus 5/Fable 5.1 10×, Claude 4.8 15× output-token conversion; deduction staged (input + max_tokens up front → adjusted → unused replenished); cache reads don't count. Gemini: RPM/TPM/RPD (+ IPM/TPD); any dimension 429s; **spend-based rolling 10-minute windows** ($10/$50/$200 by tier) (2026-09-02).
- **Concurrency caps**: GitHub 100; Stripe concurrency 429 reasons; Gemini Batch 100 concurrent; Anthropic/OpenAI document no sync-inference concurrency cap (absence is a finding).
- **Batch queue quotas**: Anthropic 200k/300k/500k queued requests by tier (100k per batch); OpenAI caps enqueued input tokens per model.
- **Acceleration/ramp limits**: Anthropic documents 429s on sharp org-level increases ("ramp up gradually"); Azure pooled reductions; Gemini spend windows; tier graduation (OpenAI $5→$1,000 cumulative; Gemini spend + days; Anthropic usage history, Evaluation tier).

## Sources

Algorithms: blog.cloudflare.com/counting-things-a-lot-of-different-things (2017-06) · brandur.org/rate-limiting (2015-09-18) · github.com/brandur/redis-cell · en.wikipedia.org/wiki/Leaky_bucket · envoyproxy.io type/v3/token_bucket.proto.
Enforcement: redis.io/docs/latest/commands/incr · d1.awsstatic.com/builderslibrary/pdfs/fainess-in-multi-tenant-systems-david-yanacek.pdf (© 2020) · developers.cloudflare.com/waf/rate-limiting-rules/request-rate (2026-04-16) · github.com/envoyproxy/ratelimit.
Standards: ietf.org draft-ietf-httpapi-ratelimit-headers-11 (2026-05-23) · docs.github.com REST rate limits · docs.stripe.com/rate-limits.
Infrastructure: envoyproxy.io local_rate_limit + rate_limit filters (+ protos) · nginx.org ngx_http_limit_req_module · haproxy.com stick-tables intro (2018-09-21) · developer.konghq.com rate-limiting plugin + reference · docs.aws.amazon.com apigateway request-throttling + limits · developers.cloudflare.com waf rate-limiting-rules (2026-08-25) + parameters (2026-04-29).
Design: docs.cloud.google.com/docs/quotas/overview (2026-09-03).
LLM: platform.claude.com/docs/en/api/rate-limits · developers.openai.com rate-limits · learn.microsoft.com azure ai-foundry openai quota (2026-05-04) · docs.aws.amazon.com/bedrock quotas + quotas-token-burndown · ai.google.dev/gemini-api/docs/rate-limits (2026-09-02).
Cited forward: RFC 6585 · RFC 9110 · stripe.com/blog/rate-limiters · sre.google handling-overload · platform.claude.com errors · Envoy retry budgets.

## Uncertain / could not verify (excluded from the Concept)

- Cloudflare post exact day (2017-06-07 single-sourced; use "2017-06").
- Leaky ≡ token equivalence verified via Wikipedia only (ITU-T I.371 not fetched).
- AWS fairness article fail-open stance: not stated on the pages read — do not assert; fail-open evidence rests on Stripe/Envoy/Kong.
- Google Cloud "rate-limiting strategies" page now redirects; dropped as a source.
- Kong: fixed-vs-sliding window unstated; `sync_rate` > 0 semantics only as sync frequency; cluster-policy deprecation status unconfirmed.
- envoyproxy/ratelimit units beyond second|minute|hour|day unconfirmed.
- NGINX cross-worker sharing follows from shared-memory-zone semantics, not a doc sentence.
- IETF draft intended status "(None)" on datatracker.
- Cloudflare error-1015 page vs default 429 interplay unverified.
- HAProxy syntax from the 2018 blog — re-check against the current manual before quoting config.
- No documented sync-inference concurrency cap for Anthropic/OpenAI/Bedrock text models (absence, not proof).
- Fixed-window "2×" is arithmetic; Cloudflare documents the mechanism, not the figure.
