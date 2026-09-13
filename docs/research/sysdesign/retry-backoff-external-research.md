---
type: research
title: 'Retry, backoff, and retry budgets — external research (2026-09-13)'
description: >-
  Source-verified research backing the RetryBackoff Concept: Brooker jitter
  formulas, SRE budgets and amplification math, library and mesh defaults,
  idempotency, metastability, hedging, and LLM-provider retry semantics.
tags: [research, retry, backoff, resilience, system-design-patterns]
---

# Retry, backoff, and retry budgets — external research (2026-09-13)

> **What this is.** The evidence pass behind
> [RetryBackoff.md](../../../cases/SystemDesignPatterns/RetryBackoff.md), at the
> Circuit breaker depth bar (owner decision C2). The Concept carries the
> distilled result; this note keeps verified facts, defaults, and URLs.
>
> **Method.** Four tracks (canon; libraries; infrastructure; operations + LLM
> APIs). Primary pages fetched 2026-09-13. Paraphrase; numbers reproduced
> exactly. Items that could not be verified are in §7 and are **not** asserted
> in the Concept.
>
> **Existing citations in this tree** (do not duplicate): Bronson HotOS 2021
> [7], Brooker metastability [8], Huang OSDI 2022 [9], Brooker jitter [10],
> Brooker backoff [11], Nygard [12], Brooker token buckets [14] in
> [nfr-references.md](../../../cases/data-intensive-design/nfr-references.md).
> Envoy retry-budget 20% / `min_retry_concurrency` 3 and gRPC
> `retryThrottling` were first verified in
> [circuit-breaker-external-research.md](circuit-breaker-external-research.md)
> §3; the mesh track **reconfirmed** the budget on the current proto.
> Track dumps (do not treat as a second home for the Concept):
> [retry-library-defaults.md](retry-library-defaults.md),
> [mesh-proxy-retry-external-research.md](mesh-proxy-retry-external-research.md).

---

## 1. Canon and definitions

**Brooker, "Exponential Backoff And Jitter" (2015-03-04).**
https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter — May
2023 update notes most AWS SDKs now ship this in standard/adaptive retry
modes. Simulation of OCC under contention: no-backoff work grows with N²;
capped exponential backoff still clusters. Jitter formulas from
https://github.com/awslabs/aws-arch-backoff-simulator `src/backoff_simulator.py`:

```
expo(n) = min(cap, base * 2**n)
Full:         random.uniform(0, expo(n))
Equal:        expo(n)/2 + random.uniform(0, expo(n)/2)
Decorrelated: sleep = min(cap, random.uniform(base, sleep * 3))  # sleep starts at base
```

Results in the post: Full and Equal cut work substantially vs no-jitter;
Decorrelated does *more* work than Full; Equal is the jittered loser (slightly
more work than Full, much more time); Full uses less work but slightly more
time than Decorrelated. **The course dump's "full jitter is fastest" is
false.** Full is the least-*work* default.

**Brooker, "What Is Backoff For?" (2022-08-11).**
https://brooker.co.za/blog/2022/08/11/backoff.html — backoff helps closed-loop
systems and short spikes, not sustained open-loop overload. Cited as [11].

**Brooker, "Fixing retries with token buckets and circuit breakers"
(2022-02-28).** https://brooker.co.za/blog/2022/02/28/retries.html — cited as
[14]. 100-client simulation; a breaker applied only to *retries* (first
attempts always pass) controls load but is modal per client. AWS SDK local
token bucket since 2016 (Builders' Library; live pages are client-rendered,
verified from the circuit-breaker research archives).

**Google SRE book ch. 21 *Handling Overload*.**
https://sre.google/sre-book/handling-overload — per-request cap of three
attempts; per-client retry ratio ~10%; without it growth "just below 3X", with
it "~1.1x"; retry only at the layer immediately above the rejector; backends
may return "overloaded, don't retry"; adaptive throttling
`max(0, (requests − K·accepts) / (requests + 1))`, K = 2 default.

**Google SRE book ch. 22 *Addressing Cascading Failures*.**
https://sre.google/sre-book/addressing-cascading-failures — exact sentence:
"If the database can't service requests because it's overloaded, and the
backend, frontend, and JavaScript layers all issue 3 retries (4 attempts),
then a single user action may create 64 attempts (4^3) on the database."
Always use randomized exponential backoff (cites Bro15). Server-wide budget
example: 60 retries/min/process. Do not retry permanent errors or malformed
requests. Return a specific overloaded status. Brooker five-layers × three
retries = 243× is from the Builders' Library, not this chapter.

**SRE Workbook *Managing Load*.** https://sre.google/workbook/managing-load —
Pokémon GO ~50× forecast; synchronized client retries → 20× peaks; fix =
jitter + truncated exponential backoff + admin rate limits.

**Azure Retry pattern + Retry Storm antipattern.**
https://learn.microsoft.com/azure/architecture/patterns/retry and
https://learn.microsoft.com/azure/architecture/antipatterns/retry-storm —
classify transient vs permanent; breaker prescribed against storms
(ms.date 2025-07-16 on the storm page, from the breaker research).

**Dean & Barroso, "The Tail at Scale," CACM 56 (2013).**
https://cacm.acm.org/research/the-tail-at-scale/ — hedged request: send
secondary after expected p95 (~5% extra load). Bigtable: 1 000 keys, 100
servers, hedge after 10 ms → 99.9th percentile 1 800 ms → 74 ms, +2%
requests. Chubby-specific hedge numbers: **not in the fetched section**.

**Stripe idempotency.** https://docs.stripe.com/api/idempotent_requests —
keys pruned after **at least 24 hours**; ≤ 255 chars; stores first status +
body including 500s; errors on payload mismatch; all POST; do not send on GET
or DELETE.

**IETF `Idempotency-Key` draft-07** (2025-10-15, expires 2026-04-18, expired
& archived this fetch, not an RFC).
https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/
— 400 missing, 422 reused with different payload, 409 in-flight.

**.NET `DisableForUnsafeHttpMethods`.**
https://learn.microsoft.com/dotnet/core/resilience/http-resilience — disables
POST, PATCH, PUT, DELETE, CONNECT; cites RFC 7231 §4.2.1 *safety*, not
idempotency. Standard handler retries all methods unless called.

**Yandex, "Good Retry, Bad Retry" (2024-08-09).** 9× load at the callee vs
3× at its caller; 10% local token-bucket retry budget. Verified in the
breaker research; not re-fetched this pass.

---

## 2. Library implementations and defaults

| Library | Attempts | Backoff / delay | Jitter | Retries | Excludes |
|---|---|---|---|---|---|
| Resilience4j Retry (docs 2026-09-13) | `maxAttempts` **3 includes initial**; `waitDuration` **500 ms** | default interval = constant wait; `IntervalFunction.ofExponentialBackoff()` | `ofRandomized()` optional | `retryExceptionPredicate` default true | `ignoreExceptions` empty; `failAfterMaxAttempts` false |
| Polly v8 Retry | `MaxRetryAttempts` **3 in addition** (= 4 total); `Delay` **2 s**; `BackoffType` Constant | Constant / Linear / Exponential | `UseJitter` **false**; when on, ±25% except Exponential → `DecorrelatedJitterBackoffV2` | any exception except `OperationCanceledException` | cancellation |
| .NET standard HTTP handler (`Microsoft.Extensions.Http.Resilience`) | **3 retries**, exponential + jitter, **2 s** base | Exponential | on | HTTP ≥ 500, 408, 429, `HttpRequestException`, `TimeoutRejectedException` | unsafe methods only after `DisableForUnsafeHttpMethods()` |
| .NET hedging handler | hedge min 1 / max **10**, delay **2 s**; total 30 s, attempt 10 s | hedge delay | — | same failure set | — |
| Polly hedging | `MaxHedgedAttempts` **1**, `Delay` **2 s**; `Delay = 0` fires all at once; `−1 ms` waits for completion | — | — | — | — |
| Anthropic SDK Python `main` `_constants.py` | `DEFAULT_MAX_RETRIES = 2`; timeout 10 min | `min(0.5 * 2^n, 8.0)` s | `1 - 0.25 * random()` → **[0.75, 1.0]** (not ±25%; source comment "plus-or-minus half a second" does not match) | 408, 409, 429, ≥ 500; `x-should-retry` override; `retry-after` honoured iff `0 < v ≤ 60` s | — |
| OpenAI Python SDK | `DEFAULT_MAX_RETRIES = 2`; timeout 600 s; 0.5 → 8.0 s | same Stainless family | same shape | connection, 408, 409, 429, ≥ 500 | spend/quota 429s do not restore access |

Resilience4j: https://resilience4j.readme.io/docs/retry — `maxAttempts`
description is explicit: "including the initial call as the first attempt."
Spring aspect order (from breaker research): Retry outermost.

Resilience4j metrics: https://resilience4j.readme.io/docs/micrometer —
`resilience4j.retry.calls` gauge, kinds `successful_without_retry` /
`successful_with_retry` / `failed_with_retry` / `failed_without_retry`
(logical outcomes, #1600).

Polly: https://www.pollydocs.org/strategies/retry#defaults and
https://www.pollydocs.org/advanced/telemetry — meter `Polly`;
`resilience.polly.strategy.events` (`OnRetry`);
`.attempt.duration` (`attempt.number` 0-based). TimeProvider for tests:
https://www.pollydocs.org/api/Polly.ResiliencePipelineBuilderBase.html

Tenacity 9.1.4, p-retry 8.0.1, Failsafe 3.3.2, spring-retry 2.0.13, Hystrix
(no retry): see [retry-library-defaults.md](retry-library-defaults.md).

---

## 3. Infrastructure-level retries

**Envoy router (docs 1.40.0-dev, 2026-09-13).**
https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/router_filter

- No retries unless a retry policy (route / vhost) or HTTP/3 early-data 425
  path is configured. With a policy, default retries = **1**
  (`x-envoy-max-retries` overrides).
- Fully jittered exponential backoff, base **25 ms**, cap **10×** (250 ms).
  Given base B and retry N, sleep in `[0, (2^N − 1)B)`: 1st 0–24 ms, 2nd
  0–74 ms, 3rd 0–174 ms. Runtime `upstream.base_retry_backoff_ms`.
- Route timeout **includes all retries**.
- `retry_on`: `5xx`, `gateway-error` (502/503/504), `reset`,
  `reset-before-request`, `connect-failure`, `envoy-ratelimited`,
  `retriable-4xx` (**409 only** — OCC warning in the docs), `refused-stream`,
  `retriable-status-codes`, `retriable-headers`, `http3-post-connect-failure`.
  A request that exceeds `x-envoy-upstream-rq-timeout-ms` (504) is **not**
  retried; use per-try timeout to retry slow attempts.
- gRPC `retry_grpc_on`: cancelled, deadline-exceeded, internal,
  resource-exhausted, unavailable. Trailers do not trigger retry.
- Hedging: `x-envoy-hedge-on-per-try-timeout` issues a retry *without*
  resetting the original.
- Stats: `upstream_rq_retry`, `_retry_success`, `_retry_overflow` (circuit
  breaking **or** retry budget), `_retry_limit_exceeded`,
  `_retry_backoff_exponential`, `_retry_backoff_ratelimited`.
- Runtime `upstream.use_retry` = percent eligible (fleet kill switch).
- Cluster `max_retries` default 3 and optional `retry_budget` 20% /
  `min_retry_concurrency` 3: see breaker research §3. Retry budget, when
  set, **overrides** `max_retries`.

**Istio fault injection.**
https://istio.io/latest/docs/tasks/traffic-management/fault-injection/ —
Bookinfo: `productpage`→`reviews` timeout 3 s + 1 retry = 6 s vs
`reviews`→`ratings` 10 s; 7 s delay surfaces the mismatch.

**Linkerd retries** since 2.16 (2024-08-13): HTTPRoute/GRPCRoute
`retry.linkerd.io/limit` default 1 (breaker research §3). Not re-fetched.

**gRPC deadlines.** https://grpc.io/docs/guides/deadlines — no default
deadline; remaining-time propagation (2 s − 0.5 s = 1.5 s). Default on in
Java and Go.

**Spring Kafka** (breaker research): `DefaultErrorHandler` `FixedBackOff(0, 9)`
= ten deliveries then recoverer / DLQ.

---

## 4. Operational depth

**Metastability.** Huang et al. OSDI 2022 PDF
https://www.usenix.org/system/files/osdi22-huang-lexiang.pdf — abstract says
**22** incidents / 11 orgs; §2 says **21** (Table 1). Retry is the most
common sustaining effect, "**more than 50%**", and names 11 IDs (11/21 ≈ 52%).
Bronson et al. HotOS 2021: DB good to 300 QPS; one 1 s retry; 280 QPS + 10 s
blip → 560 QPS; stable below 150 QPS.

**Incidents.** GitHub 2025-08-12
https://github.blog/news-insights/company-news/github-availability-report-august-2025/
(published 2025-09-11): retry queues overwhelmed the load balancers; up to
75% of search queries failed. Slack 2022-02-22
https://slack.engineering/slacks-incident-on-2-22-22/ : cache-miss loop;
"Client retries are often a contributor… this scenario was no exception"
despite exponential backoff + jitter; recovery by client-boot throttle in
small steps. DynamoDB 2015-09-20: official `aws.amazon.com/message/5467D2/`
returned **403** this fetch; postmortem.io reprint used — membership retries
kept load high until metadata requests were paused at 5:06am PDT. Kinesis
2020-11-25 https://aws.amazon.com/message/11201/ : thread-limit trigger;
retry-adjacent fact is the **thundering-herd restart**, not a client storm.

**Amplification math.** SRE 4³ = 64 (total leaf attempts, original included).
Course "3 × 3 = 27" is not SRE. Extra = 63. Napkin "10% × 3 extra ≈ +30%" is
arithmetic, not a vendor quote.

**When not to retry (sourced).** Permanent / malformed (SRE ch. 22); auth
(provider error pages); spend-cap / quota 429 (Anthropic rate-limits, OpenAI
error-codes); context-length 400; same-model refusal (Anthropic); Open
circuit / half-open probe (design rule, complementary to the breaker Concept
— no single vendor MUST found on a retry page); non-idempotent POST without
a key (Stripe + IETF); `x-should-retry: false`.

**Testing.** Toxiproxy toxics including `reset_peer`. WireMock faults
(`CONNECTION_RESET_BY_PEER` "only seems to work properly on *nix"). Istio
fault injection as above. Resilience4j: mock + `times(3)` against default
`maxAttempts`. Polly: `TimeProvider` / `FakeTimeProvider`. No official
Resilience4j test-clock injection found. No vendor PromQL alert recipes
found.

---

## 5. Retries around LLM provider APIs

**Anthropic.** https://platform.claude.com/docs/en/api/errors — 408/409/429/5xx
retried by SDKs twice with exponential backoff, honouring `retry-after`.
529 `overloaded_error`; 504 `timeout_error`; mid-stream `error` events after
HTTP 200. Spend-cap 429 (`enforced_spend_limit_reached`) has **no**
`retry-after`; "Retrying, including the SDKs’ automatic retries, fails until
access resumes" (rate-limits page). User-set spend limit is HTTP 400.
`stop_reason: "refusal"` is HTTP 200: "Re-sending a refused request to the
same model usually earns another refusal."
https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback

**OpenAI.** https://platform.openai.com/docs/guides/error-codes — retry 429
rate-limit (follow `Retry-After`), 429 `slow_down` (≤ 50% increase / 15 min
after 1 M input TPM), 500, 503 `server_is_overloaded`. Do not retry
`credit_balance_exhausted` / org or project spend or usage limits.

**LiteLLM.** https://docs.litellm.ai/docs/proxy/reliability — example
`num_retries: 3` on each `model_name`, then `fallbacks`; separate
`context_window_fallbacks` / `content_policy_fallbacks`. `allowed_fails: 3`
vs comment "fails > 1 call in a minute" — contradiction, not used as a
number. Cooldown ≠ retry.

**Portkey.** https://portkey.ai/docs/product/ai-gateway/automatic-retries —
up to 5 retries; default codes `[429, 500, 502, 503, 504, 529]`; waits
1/2/4/8/16 s; cumulative wait cap 60 s; single `Retry-After` > 60 s → fail
immediately.

**Cloudflare AI Gateway.**
https://developers.cloudflare.com/ai-gateway/configuration/request-handling/
(updated 2026-06-15) — `cf-aig-max-attempts`, `cf-aig-retry-delay` max
5 000 ms, `cf-aig-backoff` constant|linear|exponential. Same page says both
"maximum of five retry attempts" and "maximum of 5 tries". TTFB timeout
`cf-aig-request-timeout`. Final retry waits until completion.

---

## 6. How this feeds the Concept

New sections in
[RetryBackoff.md](../../../cases/SystemDesignPatterns/RetryBackoff.md): lineage
(Brooker / SRE / Azure / Dean–Barroso); what is worth retrying; idempotency;
jitter formulas with the course-dump correction; budgets; amplification
(4³=64, not 27); timeout/deadline/breaker coordination; strategy table
including hedging; verified library and Envoy defaults; placement / one-layer;
observability; tuning; alternatives; worked 3 s order-service calibration;
testing; failure modes / metastability; LLM retries; trade-offs; sources.
Everything in §7 is excluded from the Concept.

---

## 7. Uncertain / not verified (excluded from the Concept)

- Course "full jitter is fastest" — contradicted by Brooker; excluded.
- Course "3 layers × 3 retries = 27" — not SRE; Concept states both and
  uses 4³=64. Builders' Library 243× is **3⁵ tries**, not 4⁵.
- AWS SDK JavaScript v3 shipped numeric defaults (page body empty). The
  2026 cross-SDK table is opt-in (`AWS_NEW_RETRIES_2026`); Java 2.x default
  remains Legacy — Concept states that caveat, not the 2026 numbers as
  current defaults.
- SRE ch. 21 adaptive-throttling **equation** — official HTML is a figure;
  secondary formulas conflict. Concept names the knobs (2-minute window,
  K≈2), not an equation.
- RFC 9110 HTML — 409; used `.txt`.
- Official DynamoDB 2015 HTML (403); Concept uses the pause-metadata fact
  from the reprint + breaker-research archive.
- Huang 21 vs 22 incidents — both in the same PDF.
- "Never retry while Open / never retry the half-open probe" as a library
  MUST — practiced; no single retry-page quote.
- Vendor PromQL alert recipes — none found.
- Resilience4j official test-clock injection — not found.
- Chubby hedging numbers — Tail at Scale example is Bigtable.
- LiteLLM `allowed_fails` comment vs key; cooldown-on-429-immediately not
  re-confirmed on the fallbacks page.
- Cloudflare `cf-aig-max-attempts`: tries vs retries wording conflict.
- Anthropic source comment "± half a second" vs code `[0.75, 1.0]`.
- Which Istio `retryOn` string is actually injected (VS text vs MeshConfig).
- Linkerd ServiceProfile budget numbers on current pages (0.2 / 10 / 10s
  only in a 2019 post).
- GEP-1731 Standard vs Experimental vs shipped.
- ALB undocumented internal retry (attribute pages show none).

---

## 8. Sources

**Canon.** aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter
(2015-03-04, updated 2023-05) · github.com/awslabs/aws-arch-backoff-simulator
· brooker.co.za/blog/2022/08/11/backoff.html ·
brooker.co.za/blog/2022/02/28/retries.html ·
sre.google/sre-book/handling-overload ·
sre.google/sre-book/addressing-cascading-failures ·
sre.google/workbook/managing-load ·
learn.microsoft.com/azure/architecture/patterns/retry ·
learn.microsoft.com/azure/architecture/antipatterns/retry-storm ·
cacm.acm.org/research/the-tail-at-scale ·
docs.stripe.com/api/idempotent_requests ·
datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/ ·
learn.microsoft.com/dotnet/core/resilience/http-resilience

**Metastability and incidents.**
usenix.org/system/files/osdi22-huang-lexiang.pdf ·
sigops.org/s/conferences/hotos/2021/papers/hotos21-s11-bronson.pdf ·
github.blog/news-insights/company-news/github-availability-report-august-2025
· slack.engineering/slacks-incident-on-2-22-22 ·
aws.amazon.com/message/11201 · postmortem.io reprint of DynamoDB 2015 ·
medium.com/yandex/good-retry-bad-retry-an-incident-story-648072d3cee6

**Libraries.** resilience4j.readme.io/docs/retry ·
resilience4j.readme.io/docs/micrometer · pollydocs.org/strategies/retry ·
pollydocs.org/strategies/hedging · pollydocs.org/advanced/telemetry ·
learn.microsoft.com/dotnet/core/resilience/http-resilience ·
github.com/anthropics/anthropic-sdk-python (`_constants.py`, `_base_client.py`)
· platform.openai.com/docs/guides/error-codes

**Infrastructure.** envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/router_filter
· istio.io/latest/docs/tasks/traffic-management/fault-injection ·
grpc.io/docs/guides/deadlines ·
circuit-breaker-external-research.md §3 (retry_budget, gRPC retryThrottling,
Linkerd)

**LLM.** platform.claude.com/docs/en/api/errors ·
platform.claude.com/docs/en/api/rate-limits ·
platform.claude.com/docs/en/build-with-claude/refusals-and-fallback ·
docs.litellm.ai/docs/proxy/reliability ·
portkey.ai/docs/product/ai-gateway/automatic-retries ·
developers.cloudflare.com/ai-gateway/configuration/request-handling
