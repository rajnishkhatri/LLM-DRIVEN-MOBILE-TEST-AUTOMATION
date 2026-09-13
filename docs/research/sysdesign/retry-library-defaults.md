---
type: research
title: 'Retry library defaults — source-verified (2026-09-13)'
description: >-
  Primary-doc and registry-verified retry defaults for Resilience4j, Polly v8,
  Microsoft.Extensions.Http.Resilience, Hystrix (none), Tenacity, p-retry, AWS
  SDKs, Anthropic/OpenAI official SDKs, Failsafe, Spring Retry, gRPC service
  config, and selected Go libraries. Facts and URLs only. No invented numbers.
tags: [research, retry, backoff, resilience, system-design-patterns]
---

# Retry library defaults — source-verified (2026-09-13)

Fetched 2026-09-13. Numbers copied from primary docs or current source on the tagged/default branch. Registry versions recorded from Maven Central / NuGet / PyPI / npm / GitHub Releases / Go module proxy. Attempt-count semantics differ across libraries (total attempts vs extra retries) — reproduced as the source states them.

Column key for every row: **max attempts** | **backoff type** | **base delay** | **max delay** | **jitter** | **retried** | **not retried** | **budget/throttle** | **metrics** | **composition**.

---

## 1. Resilience4j Retry (2.x)

**Version / date.** GitHub Releases `v2.4.0` published 2026-03-14. Artifact `io.github.resilience4j:resilience4j-retry:2.4.0` present on Maven Central (`repo1.maven.org/.../2.4.0/resilience4j-retry-2.4.0.pom`). Maven Central Solr `latestVersion` still reported `2.3.0` (stale index; see § Unverified).

**Primary URLs.**
- Docs table: https://resilience4j.readme.io/v2.0.0/docs/retry
- `RetryConfig.java` (master, fetched 2026-09-13): https://raw.githubusercontent.com/resilience4j/resilience4j/master/resilience4j-retry/src/main/java/io/github/resilience4j/retry/RetryConfig.java
- `IntervalFunction.java`: https://raw.githubusercontent.com/resilience4j/resilience4j/master/resilience4j-core/src/main/java/io/github/resilience4j/core/IntervalFunction.java
- Spring aspect order: https://resilience4j.readme.io/docs/getting-started-3
- Micrometer: https://resilience4j.readme.io/docs/micrometer
- Release: https://github.com/resilience4j/resilience4j/releases/tag/v2.4.0

**`RetryConfig` constants (source).** `DEFAULT_MAX_ATTEMPTS = 3`. `DEFAULT_WAIT_DURATION = 500` (ms). `failAfterMaxAttempts = false`. `writableStackTraceEnabled = true`. `retryExceptions` / `ignoreExceptions` empty arrays. Default exception predicate `throwable -> true`. Default result predicate is unset (`retryOnResultPredicate` null; docs table: `result -> false`). Ignore has priority over retry. `intervalFunction` + `intervalBiFunction` together throws `IllegalStateException`. `maxAttempts` is **total attempts including the initial call** (docs: “including the initial call as the first attempt”).

**`IntervalFunction` constants (source).** `DEFAULT_INITIAL_INTERVAL = 500`. `DEFAULT_MULTIPLIER = 1.5`. `DEFAULT_RANDOMIZATION_FACTOR = 0.5`. `ofDefaults()` = fixed 500 ms. `ofExponentialBackoff()` = 500 ms × 1.5 per attempt; **no max** unless an overload with `maxIntervalMillis` is used. `ofRandomized()` = 500 ms ± 50%. `ofExponentialRandomBackoff()` = exponential then `randomize(interval, 0.5)`. `randomize`: `[current − f·current, current + f·current]`, then `Math.max(1.0, randomizedValue)`.

| Field | Default |
|---|---|
| max attempts | **3 total** (initial + 2 retries) |
| backoff type | **fixed** (`numOfAttempts -> waitDuration`) unless an `IntervalFunction` is set |
| base delay | **500 ms** |
| max delay | **none** on the default path; exponential overloads can take `maxIntervalMillis` |
| jitter | **off** by default; `ofRandomized` / `ofExponentialRandomBackoff` use factor **0.5** |
| retried | every `Throwable` (`throwable -> true`); optional `retryExceptions` / `retryOnException` / `retryOnResult` |
| not retried | `ignoreExceptions` (empty); ignore wins |
| budget/throttle | none in the Retry module |
| metrics | gauge `resilience4j.retry.calls` with `kind` = `successful_without_retry` / `successful_with_retry` / `failed_with_retry` / `failed_without_retry` (Prometheus sample uses underscores; docs table also writes dotted `successful.without.retry`) |
| composition | Spring AOP default nest: `Retry ( CircuitBreaker ( RateLimiter ( TimeLimiter ( Bulkhead ( Function ) ) ) ) )` — Retry outermost. Override via `resilience4j.retry.retryAspectOrder` vs `resilience4j.circuitbreaker.circuitBreakerAspectOrder` (higher value = higher priority) |

`failAfterMaxAttempts=true` throws `MaxRetriesExceededException` only when max attempts are reached **and** the result still fails `retryOnResultPredicate`.

---

## 2. Polly v8 Retry / Hedging + Microsoft.Extensions.Http.Resilience

**Version / date.** NuGet `Polly` **8.7.0**, last updated **2026-06-10**. `Microsoft.Extensions.Http.Resilience` **10.10.0**, last updated **2026-09-09**.

**Primary URLs.**
- Retry strategy: https://www.pollydocs.org/strategies/retry
- Retry options API: https://www.pollydocs.org/api/Polly.Retry.RetryStrategyOptions-1.html
- Hedging: https://www.pollydocs.org/strategies/hedging
- Pipelines (add-order = outer→inner): https://www.pollydocs.org/pipelines
- Http resilience: https://learn.microsoft.com/en-us/dotnet/core/resilience/http-resilience
- NuGet Polly: https://www.nuget.org/packages/Polly
- NuGet Http.Resilience: https://www.nuget.org/packages/Microsoft.Extensions.Http.Resilience/10.10.0

### Polly `RetryStrategyOptions` defaults (docs + API)

| Field | Default |
|---|---|
| max attempts | **`MaxRetryAttempts` = 3, in addition to the original call** (4 total if all fail). `int.MaxValue` = retry forever |
| backoff type | **`DelayBackoffType.Constant`** |
| base delay | **`Delay` = 2 seconds** |
| max delay | **`MaxDelay` = null** (uncapped) |
| jitter | **`UseJitter` = false**. If true: Constant/Linear = ±25% of calculated delay; Exponential = `DecorrelatedJitterBackoffV2` (Polly.Contrib.WaitAndRetry) |
| retried | **`ShouldHandle`**: any exception other than `OperationCanceledException` |
| not retried | `OperationCanceledException`; results unless a `HandleResult` predicate is added |
| budget/throttle | none in the retry strategy itself |
| metrics | telemetry events `ExecutionAttempt` (Information / Warning / Error) and `OnRetry` (Warning). `OnRetry` only if a retry actually runs |
| composition | `ResiliencePipelineBuilder` add order: first added is **outer**. No built-in Retry+CB pairing; caller composes |

Exponential without jitter (source `RetryHelper.GetRetryDelayCore`): `baseDelay × 2^attempt`. Linear without jitter: `(attempt + 1) × baseDelay`. Constant: `baseDelay`.

### Polly `HedgingStrategyOptions` defaults

| Field | Default |
|---|---|
| max attempts | **`MaxHedgedAttempts` = 1** (plus the original) |
| backoff type | latency-mode delay, not exponential retry |
| base delay | **`Delay` = 2 seconds** before spawning the next hedged action |
| max delay | n/a (`DelayGenerator` optional) |
| jitter | none documented on the default delay |
| retried / hedged | any exception other than `OperationCanceledException` |
| special Delay values | `0` = spawn all `MaxHedgedAttempts` immediately; `-1 ms` = no concurrent hedge (wait for previous to finish) |
| metrics | `ExecutionAttempt`, `OnHedging` |

### `AddStandardResilienceHandler` defaults (Http.Resilience docs)

Outer → inner:

| Order | Strategy | Defaults |
|---|---|---|
| 1 | Rate limiter | Queue **0**, Permit **1000** |
| 2 | Total timeout | **30 s** |
| 3 | Retry | **Max retries 3**, **Exponential**, **Use jitter true**, **Delay 2 s** |
| 4 | Circuit breaker | Failure ratio **10%**, min throughput **100**, sampling **30 s**, break **5 s** |
| 5 | Attempt timeout | **10 s** |

Retry/CB handle: HTTP **≥ 500**, **408**, **429**, `HttpRequestException`, `TimeoutRejectedException`.

**Default retries all HTTP methods.** `DisableFor(HttpMethod…)` and `DisableForUnsafeHttpMethods()` (`POST`, `PATCH`, `PUT`, `DELETE`, `CONNECT`) are **opt-in**.

### `AddStandardHedgingHandler` defaults (same page)

Outer → inner: total timeout **30 s** → hedging (**Min attempts 1**, **Max attempts 10**, **Delay 2 s**) → per-endpoint rate limiter (queue 0 / 1000) → per-endpoint CB (10% / 100 / 30 s / 5 s) → attempt timeout **10 s**. Endpoint selection default: URL authority (scheme + host + port).

---

## 3. Netflix Hystrix — no retry module

**Version / date.** Hystrix **1.5.18**, final, **2018-11-16**. Maintenance since README commit 2018-11-19.

**Primary URLs.**
- https://github.com/Netflix/Hystrix
- https://github.com/netflix/hystrix/blob/master/README.md

Hystrix is isolation + circuit breaker + fallback + collapsing. README lists no retry policy, no max-attempts, no backoff. A Hystrix command runs **once**; retries (when present in Netflix/Spring stacks) lived in **Feign Retryer**, **Ribbon**, or **Spring Retry**, not inside Hystrix. Spring Cloud Netflix issue #1998: with Hystrix enabled, Feign’s Retryer does not run as expected; maintainers centralized on Spring Retry.

**Successor (README, verbatim intent).** For new work Netflix points at **Resilience4j** and **adaptive concurrency limits** (https://medium.com/@NetflixTechBlog/performance-under-load-3e6fa9a60581). `Netflix/concurrency-limits` is the named adaptive-limit library (not a retry library).

| Field | Default |
|---|---|
| max attempts | **1** (no Hystrix retry) |
| backoff / jitter / budget | none |
| retried | n/a |
| metrics | Hystrix command metrics only; no retry metric names |
| composition | if something else retries, Hystrix wrapping that retry is a stacking choice outside this library |

---

## 4. Tenacity (Python)

**Version / date.** PyPI **tenacity 9.1.4**, wheel upload **2026-02-07T10:45:32Z**.

**Primary URLs.**
- Docs: https://tenacity.readthedocs.io/en/stable/
- API: https://tenacity.readthedocs.io/en/stable/api.html
- Source `__init__.py`: https://raw.githubusercontent.com/jd/tenacity/master/tenacity/__init__.py
- `retry.py` tag 9.1.4: https://raw.githubusercontent.com/jd/tenacity/9.1.4/tenacity/retry.py
- PyPI: https://pypi.org/pypi/tenacity/json

Docs sentence: “the default behavior is to retry forever without waiting when an exception is raised.”

Source defaults on `BaseRetrying` / `@retry`:

| Field | Default |
|---|---|
| max attempts | **`stop=stop_never`** (unbounded) |
| backoff type | **none** (`wait=wait_none()`) |
| base / max delay | **0** |
| jitter | none unless a wait strategy adds it |
| retried | **`retry=retry_if_exception_type()`** → `exception_types=Exception` (not `BaseException`) |
| not retried | successful return; non-`Exception` BaseExceptions (e.g. `KeyboardInterrupt` / `SystemExit`) |
| budget/throttle | none |
| metrics | none built in (`statistics` dict on the wrapped function is the hook) |
| composition | none |

`reraise` default `False`. No circuit-breaker module.

---

## 5. p-retry (npm)

**Version / date.** npm **p-retry 8.0.1**, package `time` **2026-09-01T13:15:38.647Z**. Homepage https://github.com/sindresorhus/p-retry.

**Primary URL.** https://registry.npmjs.org/p-retry/latest (README reproduced by the registry).

| Field | Default |
|---|---|
| max attempts | **`retries` = 10** (additional retries; first call + 10) |
| backoff type | **exponential** (`minTimeout × factor^n`) |
| base delay | **`minTimeout` = 1000** ms |
| max delay | **`maxTimeout` = Infinity** |
| jitter | **`randomize` = false**; if true, multiply timeout by a factor in **[1, 2]** |
| retried | rejected promises, except as below |
| not retried | `AbortError`; most `TypeError`s except network errors (best-effort); `shouldRetry` / exhausted `retries` / `maxRetryTime` |
| extra | `maxRetryTime` = Infinity (monotonic `performance.now()`); `unref` = false; `shouldConsumeRetry` can skip decrementing the budget |
| budget/throttle | per-call `retries` + `maxRetryTime` only |
| metrics | none |
| composition | none; HTTP status is **not** classified — caller must throw |

---

## 6. AWS SDK retry modes (Java / Python / JS)

Three overlapping documents. They **disagree** on some defaults. Recorded separately; do not merge.

### 6a. Cross-SDK reference (opt-in 2026 behaviour)

**URL.** https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html

Page banner: behaviour on this page **requires `AWS_NEW_RETRIES_2026=true` until it becomes the default**. Without the flag, “pre-2026 retry behavior” applies (different backoff, quota costs, service-specific defaults).

Under the flag, the page states:

| Setting | Default |
|---|---|
| `retry_mode` / `AWS_RETRY_MODE` | **standard** |
| `max_attempts` / `AWS_MAX_ATTEMPTS` | **3 total** (1 initial + 2 retries). `1` disables retries |
| DynamoDB / DynamoDB Streams | **4** max attempts; transient base **25 ms** (others **50 ms**) |
| transient base | **50 ms** |
| throttling base | **1 000 ms** |
| backoff | `delay = random(0, 1) × min(20 000 ms, base_delay × 2^retry)` ; `retry` starts at 0; **full jitter**; cap **20 s** |
| `x-amz-retry-after` | used, clamped to [computed, computed+5 000 ms]; no extra jitter; effective max **25 s** |
| token bucket | capacity **500**; transient retry cost **14**; throttling retry cost **5**; success-after-retry restores that cost; first-try success restores **1** |
| retried (transient) | `RequestTimeout`, `RequestTimeoutException`, `InternalError`, `IDPCommunicationError`, I/O failure, HTTP **500/502/503/504** without a recognized code |
| retried (throttling) | `Throttling`, `ThrottlingException`, `ThrottledException`, `RequestThrottledException`, `TooManyRequestsException`, `ProvisionedThroughputExceededException`, `TransactionInProgressException`, `LimitExceededException`, `PriorRequestNotComplete`, `RequestThrottled`, `EC2ThrottledException`, `RequestLimitExceeded`, `SlowDown`, `BandwidthLimitExceeded` |
| not retried | e.g. `AccessDeniedException`, `ValidationException`, `ResourceNotFoundException` |
| adaptive | standard + client-side rate limiter that **can delay the initial request** |

Support table on that page: Java 2.x, Boto3, .NET 4.x, JS 3.x, PHP, Kotlin, Rust = Yes. Go V2 / C++ / CLI / Swift / Ruby = “See tracking issue”.

### 6b. AWS SDK for Java 2.x (current developer guide, no 2026 flag)

**URL.** https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/retry-strategy.html

**Legacy is the default** when the caller does not specify a strategy. Standard is “recommended”. Retry-strategy API since **2.26.0**.

| Strategy | Max attempts | Base non-throttling | Base throttling | Token bucket | Cost non-throttling | Cost throttling |
|---|---|---|---|---|---|---|
| **Standard** | **3** | **100 ms** | **1000 ms** | **500** | **5** | **5** |
| **Legacy** (default) | **4** | **100 ms** | **500 ms** | **500** | **5** | **0** |
| **Adaptive** | **3** | **100 ms** | **100 ms** | **500** | **5** | **5** |

Standard/Adaptive: max delay **20 s** (`BackoffStrategy#exponentialDelay`). DynamoDB clients: default maximum retry count **8** for all strategies (this page). Adaptive assumes one resource per client. `RetryMode.ADAPTIVE_V2` (2.26.0) delays the first attempt after prior throttling; env/profile `adaptive` now gets V2.

### 6c. Boto3 (page title: Boto3 1.43.93)

**URL.** https://docs.aws.amazon.com/boto3/latest/guide/retries.html

| Field | Default |
|---|---|
| mode | **`legacy`** |
| max attempts | **5 total** (including initial) when unset |
| legacy retried | `ConnectionError`, `ConnectionClosedError`, `ReadTimeoutError`, `EndpointConnectionError`; `Throttling` / `ThrottlingException` / `ThrottledException` / `RequestThrottledException` / `ProvisionedThroughputExceededException`; HTTP **429, 500, 502, 503, 504, 509** |
| legacy backoff | “exponential backoff by a base factor of **2**” (no base-ms / cap numbers on this page) |
| standard max attempts | **3 total** |
| standard extras | circuit-breaking; expanded error list; HTTP **500, 502, 503, 504**; exponential backoff factor 2, **max 20 s** |
| adaptive | experimental; standard + client token-bucket rate limiter |
| Config `max_attempts` | **retries only** (excludes initial) |
| env / `~/.aws/config` `max_attempts` | **total including initial** |
| `total_max_attempts` | Config-only; always total including initial |

### 6d. AWS SDK for JavaScript v3

https://docs.aws.amazon.com/sdk-for-javascript/v3/developer-guide/retry.html returned no usable body. Smithy `StandardRetryStrategy.ts` 404 at the guessed path. **JS numeric defaults not verified here.** Cross-SDK page lists JS 3.x as supporting the 2026 behaviour when opted in. JS has **no legacy mode** on the cross-SDK table.

---

## 7. Anthropic official SDKs (Python + TypeScript)

### Python

**Version / date.** PyPI **anthropic 1.5.0**, wheel **2026-09-10T17:45:34Z**.

**Primary URLs.**
- https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/src/anthropic/_constants.py
- https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/src/anthropic/_base_client.py
- Docs (retries section): https://platform.claude.com/docs (Python SDK retries; Korean mirror fetched: platform.claude.com/docs/ko/cli-sdks-libraries/sdks/python)

`_constants.py`:

```
DEFAULT_TIMEOUT = httpx2.Timeout(timeout=10 * 60, connect=5.0)   # 10 minutes
DEFAULT_MAX_RETRIES = 2
INITIAL_RETRY_DELAY = 0.5
MAX_RETRY_DELAY = 8.0
```

`_calculate_retry_timeout` (source):
1. Parse `retry-after-ms`, then `retry-after` (seconds or HTTP-date).
2. If `0 < retry_after <= 60`, **return that value** (seconds).
3. Else `sleep_seconds = min(0.5 * 2^nb_retries, 8.0)` then `jitter = 1 - 0.25 * random()`; return `sleep_seconds * jitter`.
4. `nb_retries = min(max_retries - remaining_retries, 1000)`.

`_should_retry`: honour `x-should-retry: true|false`; else retry **408, 409, 429, status >= 500**. Connection / timeout exceptions are also retried (`APIConnectionError`, `APITimeoutError`, `RetryableError`). **529 is >= 500 → retried.**

| Field | Default |
|---|---|
| max attempts | **`max_retries=2`** → 3 total |
| backoff | exponential `0.5 * 2^n`, cap **8 s**, × **[0.75, 1.0]** jitter |
| retry-after | honoured if **(0, 60] s** |
| timeout | **600 s** request, **5 s** connect |
| not retried | other 4xx (400/401/403/404/413/…); `x-should-retry: false` |

### TypeScript

**Version / date.** npm **@anthropic-ai/sdk 0.125.0**, `time` **2026-09-10T17:55:20.750Z**.

**Primary URLs.**
- https://github.com/anthropics/anthropic-sdk-typescript/blob/main/src/client.ts
- https://registry.npmjs.org/@anthropic-ai/sdk/latest

`maxRetries` default **2** (`options.maxRetries ?? 2`). `timeout` default **10 minutes** (`BaseAnthropic.DEFAULT_TIMEOUT`).

`calculateDefaultRetryTimeoutMillis`: `initialRetryDelay = 0.5`, `maxRetryDelay = 8.0`, `sleepSeconds = min(0.5 * 2^numRetries, 8.0)`, `jitter = 1 - Math.random() * 0.25`.

`shouldRetry`: extra path — **401** with token-cache + unused refresh → retry once (invalidate cache). Then `x-should-retry`, then **408, 409, 429, status >= 500**.

`retryRequest`: if `retry-after-ms` or `retry-after` parses, **use it with no 60 s cap** (unlike Python). Else the exponential formula.

---

## 8. OpenAI official Python SDK

**Version / date.** PyPI **openai 3.13.0**, wheel **2026-09-10T19:38:25Z**.

**Primary URLs.**
- https://raw.githubusercontent.com/openai/openai-python/main/src/openai/_constants.py
- https://raw.githubusercontent.com/openai/openai-python/main/src/openai/_base_client.py

`_constants.py`:

```
DEFAULT_TIMEOUT = httpx2.Timeout(timeout=600, connect=5.0)
DEFAULT_MAX_RETRIES = 2
INITIAL_RETRY_DELAY = 0.5
MAX_RETRY_DELAY = 8.0
MAX_RETRY_AFTER_DELAY = 2 * 60    # 120 s
```

Backoff formula **same as Anthropic Python**: `min(0.5 * 2^nb_retries, 8.0) * (1 - 0.25 * random())`.

Retry-After:
- Honoured when `0 < retry_after <= 120`.
- If `retry_after > 120`, **`_should_retry` returns False** (do not retry). This gate does **not** exist in Anthropic Python.

Status codes: `x-should-retry`, then **408, 409, 429, >= 500**. Also `retry-after-ms`.

| Field | Default |
|---|---|
| max attempts | **2 retries / 3 total** |
| timeout | **600 s**, connect **5 s** |
| retry-after | honoured up to **120 s**; longer → no retry |

---

## 9. Failsafe (Java)

**Version / date.** Maven Central `dev.failsafe:failsafe` latest directory **3.3.2**, **2023-06-24**. GitHub Releases `/latest` 404 (no latest-release tag API).

**Primary URLs.**
- https://failsafe.dev/retry/
- https://github.com/failsafe-lib/failsafe/blob/master/core/src/main/java/dev/failsafe/RetryPolicy.java
- Javadoc: https://failsafe.dev/javadoc/core/dev/failsafe/RetryPolicyConfig.html
- Maven: https://repo1.maven.org/maven2/dev/failsafe/failsafe/

`RetryPolicy.ofDefaults()` / `builder()`: **3 execution attempts max, no delay.**

| Field | Default |
|---|---|
| max attempts | **3 total** (`withMaxAttempts`; `-1` = unlimited). `getMaxRetries()` javadoc default **2** (same 3-attempt budget) |
| backoff type | **none** |
| base / max delay | **`Duration.ZERO`** / backoff max **null** until `withBackoff` / `withDelay` |
| jitter | off; `withJitter(.1)` or `withJitter(Duration)` optional |
| retried | failed executions (exceptions). `handle(...)` / `handleResult(...)` narrow |
| abort | `abortOn` / `abortWhen` / `abortIf` |
| budget/throttle | `withMaxDuration` optional; no token bucket |
| metrics | event listeners (`onFailedAttempt`, `onRetry`, `onRetriesExceeded`, `onAbort`) — not Micrometer names |
| composition | compose with Fallback / CircuitBreaker / Timeout around the RetryPolicy |

Backoff example in docs: `withBackoff(1, 30, ChronoUnit.SECONDS)` (1 s → 30 s). Default backoff **factor not restated as a constant on the retry page**; javadoc `getDelayFactor` exists.

---

## 10. Spring Retry + Spring Framework 7 retry

### spring-retry 2.0.13

**Version / date.** Maven Central `org.springframework.retry:spring-retry` **2.0.13**, **2026-06-08**.

**Primary URLs.**
- https://repo1.maven.org/maven2/org/springframework/retry/spring-retry/
- https://raw.githubusercontent.com/spring-projects/spring-retry/v2.0.13/src/main/java/org/springframework/retry/annotation/Retryable.java
- https://raw.githubusercontent.com/spring-projects/spring-retry/v2.0.13/src/main/java/org/springframework/retry/annotation/Backoff.java
- https://raw.githubusercontent.com/spring-projects/spring-retry/v2.0.13/src/main/java/org/springframework/retry/backoff/ExponentialBackOffPolicy.java

`@Retryable`:
- `maxAttempts` default **3** (**including the first failure**).
- `retryFor` / `noRetryFor` empty → **all exceptions retried**.
- `backoff` default `@Backoff()`.

`@Backoff`:
- `delay` / `value` default **1000** ms (fixed).
- `maxDelay` default **0** (ignored). If set **less than delay**, `ExponentialBackOffPolicy.DEFAULT_MAX_INTERVAL` is applied.
- `multiplier` default **0** (ignored → not exponential).
- `random` default **false**.

`ExponentialBackOffPolicy` (used only when multiplier > 1): `DEFAULT_INITIAL_INTERVAL = 100` ms, `DEFAULT_MULTIPLIER = 2`, `DEFAULT_MAX_INTERVAL = 30000` ms.

| Field | Default (`@Retryable`) |
|---|---|
| max attempts | **3 total** |
| backoff | **fixed 1000 ms** |
| max delay / jitter | unused unless `@Backoff` sets multiplier / random |
| retried | **all exceptions** |
| not retried | empty `noRetryFor`; `notRecoverable` empty |
| metrics | `label()` for statistics; no Micrometer names in the annotation |
| composition | `@Recover`; no breaker in this library |

Current `/docs/current/apidocs/.../Retryable.html` **404** (old current-javadoc URL).

### Spring Framework 7 core retry (still relevant)

**URL.** https://docs.spring.io/spring/reference/7.0-SNAPSHOT/core/resilience.html (fetched as 7.0-SNAPSHOT).

`org.springframework.resilience.annotation.Retryable`: **`maxRetries = 3` after the initial failure** → **4 total attempts**. Delay **1 second**. Retries **any exception**. Formula stated: `total attempts = 1 + maxRetries`. Requires `@EnableResilientMethods`. **Not the same semantics as spring-retry `@Retryable.maxAttempts=3`.** Released GA version of Framework 7 not pinned in this pass.

---

## 11. gRPC client retry (service config)

**Primary URLs.**
- https://grpc.io/docs/guides/retry/
- gRFC A6: https://raw.githubusercontent.com/grpc/proposal/master/A6-client-retries.md
- Hedging: https://grpc.io/docs/guides/request-hedging/
- Core arg: https://www.grpc.io/grpc/core/group__grpc__arg__keys.html (`GRPC_ARG_ENABLE_RETRIES` defaults **true**)

**There is no default retry policy.** Retries-the-feature are on (transparent retries only) unless the channel disables them. Without a service-config `retryPolicy`, gRPC retries only when it is certain the server app never saw the RPC (transparent retry: unlimited while the RPC never left the client; **one** transparent retry if it reached the server library but not app logic). Transparent retries **do not count** toward `maxAttempts`.

When a `retryPolicy` **is** configured (A6 validation):

| Field | Rule / example |
|---|---|
| max attempts | **required**, integer **> 1**. **Values > 5 are treated as 5** (client-side cap; raisable via channel args). Docs example: **4** |
| backoff | required `initialBackoff`, `maxBackoff`, `backoffMultiplier`. Example: **0.1 s**, **1 s**, **2** |
| jitter | **± 20%** on the backoff (guide: 100 ms → **[80 ms, 120 ms]** after first attempt) |
| retryable status codes | **required, non-empty**. Example: **`["UNAVAILABLE"]`**. No implicit default set |
| not retried | any status not in that list; RPC **committed** once response headers arrive |
| `retryThrottling` | **not defaulted**. If present: `maxTokens` in **(0, 1000]**, `tokenRatio` > 0 (3 decimal places). Example: **`maxTokens` 10, `tokenRatio` 0.1**. Start at `maxTokens`; fail **−1**, success **+ tokenRatio**; retries pause at **`token_count <= maxTokens/2`** |
| server pushback | metadata can force delay or forbid retry |
| metrics (OTel, guide) | `grpc.client.attempt.started`, `.duration`, `.sent_total_compressed_message_size`, `.rcvd_total_compressed_message_size`; call-level `grpc.client.call.duration` |

Hedging `maxAttempts` uses the **same cap of 5**. A method may have retry **or** hedge, not both (A6).

---

## 12. Go libraries (fetched)

### hashicorp/go-retryablehttp v0.7.8

**Date.** Go proxy `Time`: **2025-06-18T14:25:10Z**. Latest listed tag **v0.7.8**.

**URLs.**
- https://github.com/hashicorp/go-retryablehttp/blob/v0.7.8/client.go
- https://proxy.golang.org/github.com/hashicorp/go-retryablehttp/@v/v0.7.8.info
- README: https://github.com/hashicorp/go-retryablehttp

Source constants: `defaultRetryWaitMin = 1s`, `defaultRetryWaitMax = 30s`, `defaultRetryMax = 4`.

`DefaultBackoff`: `min × 2^attemptNum`, cap `max`. If status **429 or 503** and `Retry-After` parses, **use that** (no extra jitter).

`DefaultRetryPolicy` (source): retry on client/connection errors; **429**; status **0** or **>= 500 except 501**.

| Field | Default |
|---|---|
| max attempts | **`RetryMax` = 4 retries** (plus the first request) |
| backoff | exponential, min **1 s**, max **30 s** |
| jitter | **off** (`LinearJitterBackoff` exists, not default) |
| retried | connection errors, **429**, **5xx except 501** |
| not retried | 4xx other than 429; **501** |
| budget | none |

### cenkalti/backoff v5.0.3

**Date.** Go proxy **2025-07-23T16:23:35Z**.

**URLs.**
- https://raw.githubusercontent.com/cenkalti/backoff/v5/exponential.go
- https://raw.githubusercontent.com/cenkalti/backoff/v5/retry.go
- https://proxy.golang.org/github.com/cenkalti/backoff/v5/@latest

`Retry` defaults: `NewExponentialBackOff()`, `MaxElapsedTime = 15 * time.Minute`, `MaxTries` unset (**0 = unlimited tries** until elapsed/context/Stop).

`ExponentialBackOff` defaults: `InitialInterval = 500ms`, `RandomizationFactor = 0.5`, `Multiplier = 1.5`, `MaxInterval = 60s`. Next interval = current × (1 ± 0.5). `MaxInterval` caps **RetryInterval**, not the randomized sample.

| Field | Default |
|---|---|
| max attempts | **unlimited** (`MaxTries` 0) |
| budget | **15 min** elapsed |
| jitter | **0.5** randomization factor |
| retried | any error except `Permanent` |
| not retried | `backoff.Permanent(...)` |

This is a backoff primitive, not an HTTP classifier.

### avast/retry-go v4.7.0

**Date.** Go proxy **2025-10-14T18:38:31Z**. Source fetched from `master` `options.go` (defaults match pkg.go.dev text).

**URLs.**
- https://raw.githubusercontent.com/avast/retry-go/master/options.go
- https://proxy.golang.org/github.com/avast/retry-go/v4/@latest
- https://pkg.go.dev/github.com/avast/retry-go

`newRetrieerCore` defaults: `attempts = 10`, `delay = 100ms`, `maxJitter = 100ms`, `delayType = CombineDelay(BackOffDelay, RandomDelay)`, `retryIf = IsRecoverable`, `maxDelay` unset (**does not apply by default**).

`BackOffDelay`: `delay << (n-1)` (binary exponential). `RandomDelay`: uniform `[0, maxJitter)`. Combined = sum.

| Field | Default |
|---|---|
| max attempts | **10** (`Attempts(0)` = until success) |
| backoff | exponential + random jitter |
| base delay | **100 ms** |
| max delay | **none** unless `MaxDelay` set |
| jitter | **+ [0, 100 ms]** |
| retried | any recoverable error |
| not retried | `retry.Unrecoverable(...)` |

---

## Comparison table (defaults only)

Attempt-count column uses each library’s own noun.

| Library (ver, date) | max attempts | backoff | base | max | jitter | retried | not retried | budget | metrics | composition |
|---|---|---|---|---|---|---|---|---|---|---|
| Resilience4j 2.4.0 (2026-03-14) | 3 **total** | fixed | 500 ms | none | off (opt. 0.5) | all Throwables | `ignoreExceptions` | none | `resilience4j.retry.calls` | Retry **outside** CB (Spring AOP) |
| Polly 8.7.0 (2026-06-10) Retry | 3 **extra** | Constant | 2 s | none | off | all except cancel | `OperationCanceledException` | none | `ExecutionAttempt`, `OnRetry` | add-order = outer→inner |
| Polly Hedging | 1 extra hedge | delay-to-hedge | 2 s | — | — | same as retry | cancel | none | `ExecutionAttempt`, `OnHedging` | — |
| Http.Resilience 10.10.0 (2026-09-09) std | 3 extra | Exponential | 2 s | — | **on** | ≥500, 408, 429, HttpReqEx, TimeoutRejected | other HTTP; unsafe methods only if disabled | rate limiter 1000/0 | Polly meter | RL → 30s → **Retry** → **CB** → 10s |
| Hystrix 1.5.18 (2018-11-16) | 1 | — | — | — | — | — | — | — | command metrics | no retry; successor R4j / concurrency-limits |
| Tenacity 9.1.4 (2026-02-07) | forever | none | 0 | 0 | off | `Exception` | success; non-Exception BaseException | none | `statistics` | none |
| p-retry 8.0.1 (2026-09-01) | 10 extra | exp ×2 | 1 s | ∞ | off ([1,2] if on) | rejections | AbortError; most TypeError | `maxRetryTime` ∞ | none | none |
| AWS Java 2.x Legacy (default) | 4 total | exp | 100 ms / 500 ms thr | 20 s | (strategy) | retryable SDK exceptions | non-retryable | bucket 500; thr cost **0** | — | — |
| AWS Java 2.x Standard | 3 total | exp | 100 ms / 1000 ms thr | 20 s | (strategy) | same family | non-retryable | 500; cost 5/5 | — | — |
| Boto3 legacy (default) | 5 total | exp ×2 | — | — | — | listed + 429/5xx/509 | others | none (legacy) | log lines | — |
| Boto3 standard | 3 total | exp ×2 | — | 20 s | — | expanded list + 500–504 | others | circuit-break / quota | log lines | — |
| AWS cross-SDK 2026 (opt-in) | 3 total | full jitter exp | 50 ms / 1000 ms | 20 s | full | listed | validation/auth/not-found | 500; cost 14 / 5 | — | DynamoDB 4 / 25 ms |
| Anthropic py 1.5.0 (2026-09-10) | 2 extra | 0.5×2^n | 0.5 s | 8 s | ×[0.75,1] | 408/409/429/≥500 + conn | other 4xx | none | — | honour Retry-After ≤60 s |
| Anthropic TS 0.125.0 (2026-09-10) | 2 extra | same | 0.5 s | 8 s | ×[0.75,1] | same + 401 cache refresh | other 4xx | none | — | Retry-After **uncapped** |
| OpenAI py 3.13.0 (2026-09-10) | 2 extra | same | 0.5 s | 8 s | ×[0.75,1] | 408/409/429/≥500 + conn | other 4xx; Retry-After >120 s | none | — | honour Retry-After ≤120 s |
| Failsafe 3.3.2 (2023-06-24) | 3 total | none | 0 | none | off | failed exec | `abort*` | optional max duration | listeners | compose CB/Timeout/Fallback |
| spring-retry 2.0.13 (2026-06-08) | 3 total | fixed 1 s | 1000 ms | unused | off | all exceptions | `noRetryFor` empty | none | `label` | `@Recover` |
| Spring Framework 7 `@Retryable` (7.0-SNAPSHOT) | 3 **extra** (4 total) | 1 s | 1 s | — | — | any exception | — | none | — | `@EnableResilientMethods` |
| gRPC (no policy) | transparent only | — | — | — | — | never-seen-by-server races | everything else | — | attempt/call OTel | — |
| gRPC (if configured; A6) | ≤**5** total | exp | example 0.1 s | example 1 s | ±20% | configured codes only | others; after headers | optional 10 / 0.1 example | same | hedge XOR retry |
| go-retryablehttp v0.7.8 (2025-06-18) | 4 extra | exp | 1 s | 30 s | off | conn, 429, 5xx≠501 | other 4xx, 501 | none | none | Retry-After on 429/503 |
| cenkalti/backoff v5.0.3 (2025-07-23) | unlimited | exp | 500 ms | 60 s | ±0.5 | any err | Permanent | 15 min elapsed | none | primitive |
| avast/retry-go v4.7.0 (2025-10-14) | 10 | exp + random | 100 ms | none | +0–100 ms | recoverable | Unrecoverable | none | none | primitive |

---

## URLs (registry + primary)

| What | URL |
|---|---|
| R4j Retry docs | https://resilience4j.readme.io/v2.0.0/docs/retry |
| R4j 2.4.0 POM | https://repo1.maven.org/maven2/io/github/resilience4j/resilience4j-retry/2.4.0/resilience4j-retry-2.4.0.pom |
| R4j 2.4.0 release | https://github.com/resilience4j/resilience4j/releases/tag/v2.4.0 |
| Polly retry | https://www.pollydocs.org/strategies/retry |
| Polly hedging | https://www.pollydocs.org/strategies/hedging |
| Http.Resilience | https://learn.microsoft.com/en-us/dotnet/core/resilience/http-resilience |
| NuGet Polly 8.7.0 | https://www.nuget.org/packages/Polly/8.7.0 |
| NuGet Http.Resilience 10.10.0 | https://www.nuget.org/packages/Microsoft.Extensions.Http.Resilience/10.10.0 |
| Hystrix README | https://github.com/Netflix/Hystrix |
| Tenacity 9.1.4 | https://pypi.org/pypi/tenacity/9.1.4 |
| p-retry 8.0.1 | https://www.npmjs.com/package/p-retry |
| AWS retry (cross-SDK) | https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html |
| AWS Java retry | https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/retry-strategy.html |
| Boto3 retries | https://docs.aws.amazon.com/boto3/latest/guide/retries.html |
| Anthropic `_constants.py` | https://github.com/anthropics/anthropic-sdk-python/blob/main/src/anthropic/_constants.py |
| Anthropic `_base_client.py` | https://github.com/anthropics/anthropic-sdk-python/blob/main/src/anthropic/_base_client.py |
| Anthropic TS `client.ts` | https://github.com/anthropics/anthropic-sdk-typescript/blob/main/src/client.ts |
| OpenAI `_constants.py` | https://github.com/openai/openai-python/blob/main/src/openai/_constants.py |
| Failsafe retry | https://failsafe.dev/retry/ |
| spring-retry 2.0.13 | https://repo1.maven.org/maven2/org/springframework/retry/spring-retry/2.0.13/ |
| Framework 7 resilience | https://docs.spring.io/spring/reference/7.0-SNAPSHOT/core/resilience.html |
| gRPC retry | https://grpc.io/docs/guides/retry/ |
| gRFC A6 | https://github.com/grpc/proposal/blob/master/A6-client-retries.md |
| go-retryablehttp v0.7.8 | https://github.com/hashicorp/go-retryablehttp/tree/v0.7.8 |
| cenkalti/backoff v5.0.3 | https://github.com/cenkalti/backoff/tree/v5.0.3 |
| avast/retry-go v4.7.0 | https://github.com/avast/retry-go/tree/v4.7.0 |

---

## § Unverified

These were **not** confirmed from a fetched primary page or current source. Do not assert them.

1. **Maven Central Solr** `latestVersion` for `resilience4j-retry` = `2.3.0` (timestamp ~2025-01). Contradicted by GitHub `v2.4.0` (2026-03-14) and a live `2.4.0` POM on repo1. Solr is stale.
2. **Resilience4j Spring Boot property defaults** for `enableExponentialBackoff` / `exponentialBackoffMultiplier` / `enableRandomizedWait` — examples in getting-started YAML are **not** stated as library defaults.
3. **Exact `RetryMetricNames` Java constants** vs docs table (`successful.without.retry` vs Prometheus `successful_without_retry`). Both appear; which string Micrometer emits as the tag value was not re-read from `RetryMetricNames.java`.
4. **Polly `DecorrelatedJitterBackoffV2` numeric formula** — docs name the algorithm and the WaitAndRetry origin; coefficients not copied from `RetryHelper.cs` in this pass.
5. **Http.Resilience C# source constants** (`HttpStandardResilienceOptions`) — numbers taken from learn.microsoft.com tables, not the 10.10.0 source file. Hedging “Min attempts 1 / Max attempts 10” not cross-checked against `HedgingStrategyOptions.MaxHedgedAttempts` default of 1.
6. **Hystrix wiki / Javadoc** exhaustive search for a hidden retry knob. README + public surface have none; a buried experimental flag was not hunted in 1.5.18 source.
7. **AWS SDK for JavaScript v3 shipped defaults** (maxAttempts, base delay, token costs) — JS developer-guide page body empty; Smithy `StandardRetryStrategy.ts` 404 at the path tried. Cross-SDK 2026 numbers apply only with `AWS_NEW_RETRIES_2026=true`.
8. **Whether `AWS_NEW_RETRIES_2026` is already default in any released SDK** as of 2026-09-13 — page still says opt-in.
9. **Java DynamoDB attempt count conflict**: Java 2.x guide = **8**; cross-SDK 2026 page = **4** and 25 ms transient base. Both cannot be the live default simultaneously; which build you have matters.
10. **Boto3 / botocore exact package versions on PyPI** (docs title said 1.43.93). Legacy “base factor of 2” **base milliseconds** not on the Boto3 page.
11. **Anthropic Python 529** is implied by `status >= 500`, not named in `_should_retry`. Official API docs for 529 were not re-fetched in this pass.
12. **Anthropic TS `DEFAULT_TIMEOUT` millisecond literal** — comments say 10 minutes; constant body not copied.
13. **OpenAI TypeScript SDK** — not fetched (user asked Python).
14. **Failsafe `RetryPolicyBuilder` default `handle` set and default backoff factor** — `v3.3.2` raw builder 404; docs/javadoc used instead. GitHub Releases latest API 404.
15. **Spring Retry `RetryTemplate` builder defaults** vs `@Retryable` — only the annotation + `ExponentialBackOffPolicy` constants were read. `SimpleRetryPolicy` default max-attempts if constructed without `@Retryable` not re-read.
16. **Spring Framework 7 GA version + date** — only the 7.0-SNAPSHOT reference page.
17. **gRPC language implementations** that ignore A6’s cap of 5, or default `retryThrottling` in any shipped client. Guide examples are **not** defaults.
18. **gRPC retry-specific metric names** from gRFC A45 (guide says A6’s original retry stats are obsolete).
19. **go-retryablehttp `DefaultRetryPolicy` full error list** — 429 / 5xx≠501 / connection errors verified; redirect/TLS edge cases not copied in full.
20. **avast/retry-go v4.7.0 tag** `options.go` vs `master` — defaults read from master; proxy says v4.7.0 is latest. Drift possible if master moved after the tag.
21. **Envoy / Istio retry defaults** — out of the requested library list; not fetched here.
22. **Micrometer meter name `Polly`** for Http.Resilience — mentioned in the circuit-breaker note; not re-fetched as a retry-specific name list this pass.
