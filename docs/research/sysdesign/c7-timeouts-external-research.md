---
type: research
title: 'Timeouts & deadline propagation — external research (2026-09-13)'
description: >-
  Group C catalog evidence pass for C7: timeout kinds, remaining-time budgets,
  gRPC grpc-timeout, Brooker p99.9 calibration, library/proxy defaults,
  cancellation, and hedging vs retry — breaker and retry assume this.
tags: [research, system-design-patterns, C7, c7-timeouts]
---

# C7 Timeouts & deadline propagation — catalog research (2026-09-13)

> **What this is.** The catalog evidence pass for **C7**. It **links** the same-day first pass [timeouts-deadlines-external-research.md](timeouts-deadlines-external-research.md) (the no-default trap table, NGINX/ALB/CloudFront idle-vs-total distinction, TCP floor) and **deepens** it to the Group C / [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md) bar: mechanics and variants, knobs with verified defaults, observability, tuning, a worked Brooker calibration, failure modes, sources. Breaker (C1) and retry (C2) already assume a bound exists; this note owns how that bound is chosen, split, propagated, and cancelled.
>
> **Method.** Primary pages fetched 2026-09-13. Numbers and option names reproduced exactly; everything else paraphrased. Facts marked **[→C7-1]** are in the first-pass note and not re-fetched here. Facts marked **[→breaker]** / **[→retry]** are in [circuit-breaker-external-research.md](circuit-breaker-external-research.md) / [retry-backoff-external-research.md](retry-backoff-external-research.md). Unverifiable items are in §8 and are **not** asserted as fact.

---

## 1. Scope and non-goals

**Owns.** Connect vs request vs idle vs between-byte vs end-to-end timers; deadline vs timeout; remaining-time budgets across hops; the `grpc-timeout` wire header; cancellation that actually stops work; hedging as a *latency* tool vs retry as a *failure* tool; Brooker’s percentile method for picking the number; verified library / proxy / LB defaults with versions or fetch dates; observability and a worked calibration.

**Does not own.** Jitter algorithms and retry-budget math (**C2** — do not rewrite jitter). What errors trip a breaker (**C1**); this note only supplies the timeout *as a failure signal*. Active/passive health probes and their timeouts (**C3**). Thread/connection-pool isolation (**C8**). Trace-context headers and span graphs (**D4**); this note only names the deadline as a piece of request context that a tracer should record.

**Does not re-derive.** [timeouts-and-delays.md](../../../cases/data-intensive-design/timeouts-and-delays.md) (no correct constant; queueing is why delay varies; Φ accrual). [unreliable-networks.md](../../../cases/data-intensive-design/unreliable-networks.md) (silence is not a boolean; TCP ack ≠ application ack). [process-pauses.md](../../../cases/data-intensive-design/process-pauses.md) (GC / steal / SIGSTOP corrupt deadline math).

---

## 2. Lineage / vocabulary

| Term | Meaning | Named source |
|---|---|---|
| **Timeout** | A *duration*. Restarts if a hop copies it instead of subtracting elapsed time. | gRPC Deadlines guide; gRPC blog 2018-02-26 |
| **Deadline** | A *point in time*. Converted to remaining duration on the wire so clock skew does not extend the budget. | Same; SRE book ch. 22 |
| **Connect timeout** | Bound on DNS + TCP (+ TLS, when the client includes it). | Brooker Builders’ Library; curl `CURLOPT_CONNECTTIMEOUT`; Envoy `connect_timeout` |
| **Request / call timeout** | End-to-end bound on one attempt or one logical call. | Brooker; OkHttp `callTimeout`; Go `Client.Timeout` |
| **Idle / keepalive timeout** | Bound on *silence*, not on total duration. A trickle defeats it. | NGINX `proxy_read_timeout`; ALB idle; Envoy `stream_idle_timeout` |
| **Per-try vs outer** | Inner attempt bound vs the budget that includes retries/hedges. Outer must cover `Σ attempts + Σ backoffs`. | Envoy router; .NET standard handler |
| **Cancellation** | Cooperative stop of in-flight work once the waiter is gone. Distinct from the timer firing. | gRPC `CANCELLED` vs `DEADLINE_EXCEEDED`; Polly token wrapping |
| **Hedging** | Send a *duplicate* before the first fails, then cancel losers. XOR retry on the same gRPC method. | Dean & Barroso 2013; gRPC A6; Envoy `hedge_on_per_try_timeout` |

**Nygard, *Release It!*** (2nd ed. 2018) lists **Timeouts** as the first of the twelve Stability Patterns — before Circuit Breaker and Bulkheads — as the answer to *Blocked Threads* and *Slow Responses*. A breaker that never sees a failure because the call never returns is not a breaker **[→breaker §1]**.

**Brooker, *Timeouts, retries, and backoff with jitter*** (Amazon Builders’ Library; PDF fetched 2026-09-13). Set **both** a connection timeout and a request timeout on every remote call, including same-box IPC. Pick the request timeout from the downstream latency distribution at the percentile matching an acceptable **false-timeout rate** (example: 0.1% → **p99.9**). Pitfalls he names: internet clients need worst-case network padding; when p99.9 ≈ p50, add padding or small latency bumps become mass timeouts; Linux `SO_RCVTIMEO` is a poor end-to-end timer; homemade timers often miss DNS/TLS; a 20 ms timeout that included connection setup failed only after deploys (new TLS handshake > 20 ms) — fix was pre-establish connections, then raise the timeout for the setup path. Retries are “selfish”; five layers × three retries = **243×** database load.

**Google SRE book ch. 22** (fetched 2026-09-13). Deadlines exist so a frontend does not hold resources “until the server restarts.” Servers must **check remaining time before each stage**; work after the client has given up is uncredited. **Deadline propagation** example: A sets 30 s, spends 7 s, B gets 23 s; B spends 4 s, C gets 19 s. Subtract “a few hundred milliseconds” for transit and post-processing; optionally cap outgoing deadlines to non-critical backends. Without it, B invents a 20 s deadline to C while A already has 2 s left — C does useless work. Pair with LIFO/CoDel so queued requests that will miss are dropped. Worked collapse: 50 QPS of 100 s-deadline blackholes on a 1 000-thread frontend → **5 000** threads consumed → **80.4%** error rate; “deadlines several orders of magnitude longer than the mean” is the usual setup for that trap.

**Azure Architecture Center** names the same capacity failure as *inappropriate time-outs*: a long dependency timeout pins threads before the breaker learns anything **[→breaker §1]**. Eskildsen: a 5 s timeout on a 100 ms worker is ~1/50 capacity **[→breaker §1]**.

**Dean & Barroso, “The Tail at Scale”** (CACM Feb 2013, fetched 2026-09-13). Hedge after the class’s **p95** expected latency (~5% extra load). Google BigTable benchmark: hedge after **10 ms** dropped p99.9 of a 1 000-key / 100-server read from **1 800 ms → 74 ms** at **+2%** requests. Cancellation of losers is what keeps the extra work from becoming another overload.

---

## 3. Mechanics

### 3.1 Five timers that share a name

| Kind | Starts | Fires when | Defeated by | Typical knob |
|---|---|---|---|---|
| **Connect** | Dial | TCP/TLS not up | Blackholed SYN (OS `tcp_syn_retries` ≈ 127 s) | curl 300 s; Go dialer 30 s; OkHttp 10 s; Envoy 5 s |
| **Request / call** | First byte of the attempt (or the logical call) | Whole attempt/call exceeds T | Nothing if it is truly end-to-end | Go `Client.Timeout`; OkHttp `callTimeout` (default **off**); .NET `HttpClient.Timeout` 100 s; Envoy route **15 s** |
| **Idle / stream-idle** | Last byte in either direction | Silence ≥ T | A 1-byte trickle | ALB **60 s**; Envoy stream idle **5 min**; NGINX `proxy_read_timeout` **60 s** |
| **Between-byte / read** | Last socket read | No bytes for T | Slow streaming that never goes silent | requests `timeout`; CloudFront *response timeout* **30 s**; undici `bodyTimeout` **[→C7-1]** |
| **Connection lifetime** | Accept / connect | Age ≥ T, even if busy | — | ALB client keepalive **3600 s**; Envoy `max_connection_duration` default **0** (unlimited); Envoy HTTP protocol idle **1 h** |

Brooker’s “set a connection timeout **and** a request timeout” is the minimum pair. A connect bound without a request bound leaves a connected-then-stalled server unbounded (Go `ResponseHeaderTimeout` default **0**). A request bound that *includes* connect will false-timeout on cold TLS (Brooker’s 20 ms deploy). Idle and between-byte timers are the right tool for streams whose total time is legitimately unbounded; they are the **wrong** tool for “this RPC must finish.”

### 3.2 Remaining-time budgets

A duration copied hop-to-hop **extends** the end-to-end wait. An absolute deadline converted to remaining time **preserves** it.

```
edge  30.0s  ──spend 7.0s──►  hop-B  23.0s  ──spend 4.0s──►  hop-C  19.0s
                              minus ~0.2s transit                    (SRE ch. 22)
```

**gRPC wire.** `grpc-timeout` is a request header: ASCII integer of **at most 8 digits** plus one unit `H | M | S | m | u | n` (example `grpc-timeout: 1S`). “If Timeout is omitted a server should assume an infinite timeout.” The value is **relative remaining time**, recomputed at each sender from its local absolute deadline — that is how gRPC avoids clock skew (Deadlines guide). Propagation of the incoming context onto outbound RPCs is **default-on in Java and Go**, **opt-in in C++**. Client expiry → `DEADLINE_EXCEEDED`. Server-side, the runtime **cancels** the call (`CANCELLED`); the handler must poll `Context` / `IsCancelled()` and stop spawned work — the runtime will not kill application threads.

**Envoy (docs `latest` = 1.40.0-dev, fetched 2026-09-13).** Route `timeout` default **15 s**, “includes all retries”, `0` disables; starts only after the **entire** downstream request is received (streaming requests never start this timer — disable it and use `idle_timeout` / `max_stream_duration`). `per_try_timeout` must be **<** the route timeout or it is ignored. Documented explosion: 3 s route, 2.7 s first try → **0.3 s** left for backoff + retry. Headers: `x-envoy-upstream-rq-timeout-ms` overrides route/`grpc-timeout`; `x-envoy-upstream-rq-per-try-timeout-ms` is the inner bound; Envoy stamps **`x-envoy-expected-rq-timeout-ms`** on the upstream request so the callee can exit early. `grpc-timeout` is honoured only if `max_grpc_timeout` / `max_stream_duration.grpc_timeout_header_max` is set; `grpc_timeout_header_offset` subtracts Envoy’s own budget so Envoy, not the client, is more likely to fire first. `connect_timeout` default **5 s** (includes upstream TLS). HTTP protocol idle default **1 hour**; `stream_idle_timeout` default **5 minutes**; `drain_timeout` default **5 s**; TCP-proxy idle default **1 hour**; TCP pool idle default **10 minutes**.

**Istio** VirtualService `timeout` default is **disabled** (docs: “default is disabled”; the request-timeouts task repeats it). That is **not** Envoy’s 15 s: Istio historically writes `timeout: 0s` into Envoy, which also makes `perTryTimeout` inert unless a route timeout is set. Per-request override: `x-envoy-upstream-rq-timeout-ms`. Product-page vs reviews 3 s application timeout vs a looser Istio timeout: the **stricter** bound wins.

**Go `context`.** `WithTimeout` = `WithDeadline(parent, now+timeout)`. A child can only shorten. Expiry is `context.DeadlineExceeded`. **.NET:** `CancellationTokenSource.CancelAfter` + `CreateLinkedTokenSource` is the in-process analog; nothing crosses the process boundary unless the app writes a header. `HttpClient.Timeout` (default **100 s**) races a per-request token — shorter wins. DNS “may take up to 15 seconds,” so a Timeout < 15 s can still wait 15 s.

**Hierarchy inequality.** For `A` attempts with per-try `T` and backoffs `bᵢ`: `outer ≥ Σ Tᵢ + Σ bᵢ`. Envoy enforces this by including retries in the route timeout. The .NET **standard resilience handler** inverts it safely: total **30 s** outside retry (3 retries, exponential + jitter, 2 s base) outside attempt **10 s** — worst-case inner exceeds outer, so the **total is the binding budget**. Both designs are coherent; the incoherent one is an inner bound larger than the outer that nobody notices.

### 3.3 Cancellation

A timeout that does not cancel leaves the callee working for an answer nobody will read (SRE: “you don’t get credit for late assignments”). Layers:

| Layer | Signal | Cooperative? |
|---|---|---|
| gRPC | Client stops; server sees `CANCELLED`; HTTP/2 `RST_STREAM` | Yes, if the handler polls context |
| Envoy | 504 on outer timeout; no retry on outer-timeout 504 — use per-try to retry slowness | Proxy-side; upstream sees reset |
| Polly v8 | Wraps the incoming token; timeout → `TimeoutRejectedException`; caller cancel is **not** a timeout | **Yes — and it waits for the callback to observe the token** before throwing. Ignore the token and the timeout is late. |
| Resilience4j `TimeLimiter` | Default `timeoutDuration` **1 s**, `cancelRunningFuture` **true** | Cancels the `Future`; does not magically stop unmanaged threads |
| HTTP/1.1 | Closing the socket | Server may not notice until the next write |
| TCP | `SO_KEEPALIVE` off → silent dead peer for **tcp_retries2** ≈ **13–30 min** | Not an application cancel |

Do **not** count caller cancellation as a breaker failure (Polly excludes `OperationCanceledException` **[→breaker §2]**). Do count `DEADLINE_EXCEEDED` / 504 / `TimeoutRejectedException`.

### 3.4 Hedging vs retry (do not rewrite jitter)

| | **Retry** | **Hedging** |
|---|---|---|
| Trigger | A failure (or a per-try timeout that is classified as failure) | Time elapsed *without* a success |
| Concurrency | Sequential (after backoff) | Parallel; first success wins; losers **cancelled** |
| Extra load | 1 + retries, after the failure | Up to `maxAttempts` in flight *before* any failure |
| Idempotency | Required for unsafe methods | Required — the server may execute the RPC twice |
| Deadline | Applies to the whole chain | Same — “once the deadline has passed, the operation fails regardless of in-flight RPCs” (gRPC hedging guide) |

**gRPC A6 / hedging guide** (fetched 2026-09-13). A method may have `retryPolicy` **or** `hedgingPolicy`, not both. `maxAttempts` includes the original; client-side cap **5** (channel arg can raise it). Unspecified `hedgingDelay` → all attempts at once. `nonFatalStatusCodes`: a fatal code cancels siblings; a non-fatal code fires the next hedge immediately. Server pushback header `grpc-retry-pushback-ms` (negative / unparseable = do not hedge further). `retryThrottling` (`maxTokens`, `tokenRatio`) gates *subsequent* hedges at `maxTokens/2`. **Go hedging: “Not yet supported”** on the official guide’s language table this fetch. No extra retries after every hedge fails.

**Envoy `HedgePolicy`.** The implemented knob is `hedge_on_per_try_timeout` (default **false**): on per-try expiry, issue a retry **without** resetting the original; first success wins. Requires a `RetryPolicy` with remaining retries. `initial_requests` / `additional_request_chance` are proto fields tagged **`#not-implemented-hide:`** (Envoy issue #20036, still unimplemented on the fetched proto). Do not configure them expecting Dean-style fan-out.

**.NET** `AddStandardHedgingHandler`: total **30 s** → hedge (min 1 / max **10** / delay **2 s**) → per-endpoint limiter + breaker → attempt **10 s**. Endpoint key default = URL authority. This is a *different* default max than gRPC’s 5.

**When to hedge rather than retry.** Tail latency caused by *interference* (queueing on one replica), idempotent reads, and a hedge delay at ~p95 (Dean) or a per-try timeout (Envoy). **When to retry rather than hedge.** Transient 503/UNAVAILABLE after a definite failure; you cannot afford 2× in-flight; the method is not idempotent. **C2** owns the backoff/jitter/budget; this note only forbids stacking hedge + retry on one gRPC method and requires the outer deadline to cover the hedge chain.

---

## 4. Verified defaults / standards (fetched 2026-09-13)

### 4.1 HTTP / RPC clients

| Client | Version / page | Connect | Request / call | Idle / other | Notes |
|---|---|---|---|---|---|
| Go `http.Client` | pkg.go.dev 2026-09-01 | dialer **30 s** via `DefaultTransport` | `Timeout` **0** = none (connect + redirects + body) | `TLSHandshakeTimeout` **10 s**; `IdleConnTimeout` **90 s**; `ExpectContinueTimeout` **1 s**; `ResponseHeaderTimeout` **0** | Server `ReadTimeout`/`WriteTimeout` **0** = none **[→C7-1]** |
| Java `java.net.http` | JDK 21 | `connectTimeout` unset → empty Optional | `HttpRequest.Builder.timeout` unset = **infinite Duration** (“block forever”) | — | `HttpTimeoutException` only if set |
| .NET `HttpClient` | learn.microsoft.com | (DNS may take **15 s**) | **100 s**; `InfiniteTimeSpan` disables | — | Races per-request token, shorter wins |
| OkHttp | 5.x docs + master | **10 s** | `callTimeout` **0** (DNS+connect+body+redirects+retries share one period if set) | read/write **10 s** each | Phase timers on, total off |
| curl / libcurl | curl.se | `CURLOPT_CONNECTTIMEOUT` default **300 s** (0 = that default) | `CURLOPT_TIMEOUT` default **0** = never during transfer | — | Connect is **included** in total when both set |
| Python requests | 2.34.2 | per-IP if tuple form **[→C7-1]** | `timeout` unset = **no timeout** | read = **seconds with no bytes**, not whole download | “Nearly all production code should use this parameter” |
| Resilience4j `TimeLimiter` | source `TimeLimiterConfig.java` (defaults unchanged in 2.4.0 line) | — | **1 s** | `cancelRunningFuture` **true** | Far below typical RPC SLOs |
| Polly v8 timeout | pollydocs.org | — | **30 s** (`TimeoutGenerator` overrides) | — | Cooperative; `Timeout` range 10 ms–24 h |
| .NET standard resilience | learn.microsoft.com 2026-09-13 | — | total **30 s**, attempt **10 s** | — | Retry **inside** total, **outside** attempt |
| .NET standard hedging | same | — | total **30 s**, attempt **10 s**, hedge delay **2 s**, max **10** | — | XOR the standard *retry* handler — do not stack |
| gRPC | grpc.io Deadlines + A6 | — | **no default deadline** | — | Hedge `maxAttempts` cap **5**; retry XOR hedge |

Pattern (same as **[→C7-1]**, reconfirmed): connect often has a default; **total/read usually does not**. Exceptions with a real total default: .NET 100 s, Polly 30 s, Resilience4j TimeLimiter 1 s, Envoy route 15 s.

### 4.2 Proxies, meshes, LBs

| System | Version / page | Connect | Request / route | Idle / keepalive | Deadline propagation |
|---|---|---|---|---|---|
| Envoy | 1.40.0-dev FAQ + router + route proto | **5 s** (TLS included upstream) | route **15 s** (all retries); `0` disables | stream idle **5 min**; HTTP idle **1 h**; TCP proxy idle **1 h**; pool idle **10 min** | `x-envoy-expected-rq-timeout-ms`; optional `grpc-timeout` via `grpc_timeout_header_max` |
| Istio VirtualService | istio.io latest | (Envoy) | **disabled** unless set | (Envoy HCM) | `x-envoy-upstream-rq-timeout-ms` per request |
| Linkerd | 2.16+ / 2-edge features page | — | `timeout.linkerd.io/request` / HTTPRoute `timeouts.request`; unspecified or 0 = **not enforced** | `timeout.linkerd.io/response` | Outbound only; `l5d-timeout` header if `--allow-l5d-request-headers` |
| AWS ALB | attributes page | — | (no per-request timeout; slow target → idle) | idle **60 s** (1–4000); client keepalive **3600 s** (60–604800); **no HTTP/2 PING** as idle reset | Target idle **must be >** ALB idle or ALB → **HTTP 502** |
| CloudFront | DownloadDistValuesOrigin | **10 s × 3** attempts (30 s wall) | *response timeout* default **30 s** (TTFB **and** between packets); *response completion timeout* **unenforced** if unset | origin keep-alive default **5 s** | GET/HEAD retried on response timeout; POST/PUT/PATCH/DELETE/OPTIONS not |
| NGINX `proxy_*` | ngx_http_proxy_module | `proxy_connect_timeout` **60 s** (“cannot usually exceed 75 seconds”) | none (whole-response) | `proxy_read_timeout` / `proxy_send_timeout` **60 s**, **between successive** I/O | A trickle streams for hours |

### 4.3 TCP floor (man7.org `tcp(7)`, fetched 2026-09-13)

- `tcp_keepalive_time` **7200 s**, probes **9**, interval **75 s** (from the keepalive_time text: ~11 extra minutes). Probes only with `SO_KEEPALIVE`. Idle + dead peer, no app timeout: **≈ 2 h 11 m**.
- `tcp_syn_retries` **6** ≈ **127 s** connect to a blackhole (the inherited OS connect timeout).
- `tcp_retries2` **15** ≈ **13–30 min** on an established connection with unacked data.

RST/ECONNREFUSED is fast; silence burns these budgets. This is why [unreliable-networks.md](../../../cases/data-intensive-design/unreliable-networks.md) treats “no reply” as six undistinguishable cases.

---

## 5. Knobs, observability, tuning

### 5.1 Knobs

| Knob | Role | Too low | Too high |
|---|---|---|---|
| Connect timeout | Bound setup, **exclude** from a tight request timer | False timeouts on cold TLS / new IP (Brooker 20 ms) | SYN-blackhole holds a worker ~127 s |
| Per-attempt request timeout | Brooker percentile of *this hop’s* latency | Retry/hedge storm; healthy tail looks down | Pins the pool; breaker never sees a failure |
| Outer / total deadline | User-facing remaining budget | Truncates retries/hedges (Envoy 2.7 + 0.3) | SRE 100 s-vs-100 ms collapse |
| Idle / between-byte | Stall detector for streams | Cuts legitimate quiet periods | Never detects a wedged stream |
| Hedge delay | When to send the duplicate | Extra load ≈ all requests × (N−1) | Hedge never fires (delay > outer) |
| Transit trim | SRE “few hundred ms” | Next hop starts already expired | Last hop overruns the edge |

Placement: **library** (typed cancel, remaining time in process) → **sidecar** (Envoy stamps expected timeout; Istio default-off) → **LB/CDN** (idle, not RPC deadline) → **gateway**. The shortest timer on the path is the real SLO, usually one nobody chose **[→C7-1]**.

### 5.2 Observability (feeds D4)

Emit, per dependency and hop:

| Signal | Why |
|---|---|
| Timeout **class** (connect / headers / request / idle / cancelled) | “504” is not a diagnosis |
| Timeout rate vs raw error rate | Brooker false-timeout vs real failure |
| Latency histogram with the timeout line drawn | Recalibrate when p99.9 walks |
| Remaining deadline at ingress of each hop | Propagation bugs show up as *increasing* remaining time, or as 0 on hop 1 |
| `DEADLINE_EXCEEDED` vs `CANCELLED` vs 499 vs 504 | Who fired — client, server runtime, or proxy |
| Server work **after** client cancel | Wasted capacity (SRE) |
| Hedge / retry attempt index vs deadline left | Envoy 0.3 s leftover |

OpenTelemetry (D4) carries **trace** context (`traceparent` / `grpc-trace-bin`, gRFC A72), not `grpc-timeout`. Record remaining-ms and timeout class as **span attributes**; do not assume a tracer will cancel work. Java-agent OTel can accidentally propagate a gRPC deadline into an executor that was *not* supposed to inherit it (opentelemetry-java-instrumentation #4169) — fork the context for work that must outlive the RPC.

### 5.3 Tuning

1. Measure the **downstream** latency distribution at the caller (include queueing, not just handler time).
2. Choose a false-timeout budget (Brooker’s 0.1% is a starting *example*, not a standard).
3. Set per-attempt ≈ that percentile; pad if p99.9 ≈ p50 or if clients are off-box.
4. Set outer ≥ attempts + backoffs + hedge delays; then **propagate remaining**, don’t reset.
5. Split connect out of the request timer; pre-warm pools so deploys don’t look like outages.
6. Streams: route/call timeout **0**, idle set to “silence I will not tolerate.”
7. Revisit after the histogram has a week of shape; a timeout that never fires is as wrong as one that fires at p50.

---

## 6. Worked calibration — checkout → payment (Brooker method)

Constraints are a **design drill**, not a vendor SLA. Method cited: Brooker Builders’ Library (PDF 2026-09-13) + SRE ch. 22 remaining-time + Dean p95 hedge rule.

Measured caller-side latency to `POST /capture` over 14 days, same AZ, warmed connections (so the timer is *request*, not connect):

| Percentile | Latency |
|---|---|
| p50 | 80 ms |
| p95 | 160 ms |
| p99 | 220 ms |
| p99.9 | 420 ms |
| p99.99 | 2.1 s |

False-timeout budget **0.1%** → Brooker start point **p99.9 = 420 ms**. p99.9 / p50 = 5.25 (not “close”), so the tight-bound padding rule does not dominate; still add ~80 ms for a rare TLS-miss / AZ blip (Brooker deploy story) → **per-attempt T = 500 ms**.

User-facing checkout budget **3 s**. C2 retry policy (cited, not redesigned): 2 retries, exponential + full jitter, 200 ms base, cap 1 s. Worst-case sleeps ≈ 200 + 400 = 600 ms. Inequality: `3.0 ≥ 3×0.5 + 0.6` → **2.1 s < 3 s**, slack 0.9 s for gateway overhead. Envoy route timeout **3 s**, `per_try_timeout` **500 ms** (must be < 3 s). .NET-style stack would be total 3 s outside retry outside 500 ms attempt.

Propagation: edge 3.0 s → API gateway spends 50 ms → checkout 2.95 s → checkout spends 80 ms → payment **2.87 s** remaining (`grpc-timeout` recomputed). Payment → issuer: cap outgoing at **1.0 s** (SRE “upper bound for noncritical / typically-fast backends” — issuer p99.9 is 300 ms; a 2.87 s inherited deadline would pin issuer threads on a blackhole). Transit trim 20 ms.

Hedging: **not** on `POST /capture` (side effect). On idempotent `GET /capture/{id}` status: hedge delay **160 ms** (p95), `maxAttempts` 2, under a retry throttle. Dean’s 10 ms / 1 800→74 ms number is a BigTable fan-out benchmark, not this SLO.

Connect: Envoy/client **5 s** (or OkHttp 10 s) **separate** from the 500 ms attempt. Pre-warm the payment pool on process start so a deploy does not fold connect into T.

If the 0.1% false-timeout line is too expensive (each timeout retries), move to p99.99 only after measuring retry amplification; do not jump to 2.1 s because one plot looked scary — that is the SRE “orders of magnitude vs mean” trap.

---

## 7. Failure modes and when-not-to-use

1. **Missing timeout → TCP floor.** 13–30 min writes, 127 s connects, 2 h keepalive. Worker pool gone. The first-pass trap table **[→C7-1]** is the usual cause.
2. **Present-but-long timeout.** Azure *inappropriate time-outs*; Eskildsen 5 s ≈ 1/50; SRE 100 s × 5% blackholes.
3. **Too-short timeout.** Brooker: extra retries, then “all requests start being retried” → outage. Especially when the timer includes connect after a deploy.
4. **Duration copied, not remaining.** Last hop still has a full 30 s after the edge expired. C does work A will never read.
5. **Race-to-the-shortest.** CloudFront 30 s between-packet vs ALB 60 s idle vs Envoy 15 s total vs gunicorn 30 s **[→C7-1]** vs Istio-disabled vs app 3 s. The unnamed min wins.
6. **Idle/between-byte used as a request timeout.** NGINX/CloudFront/requests: a trickle never fires; a quiet-but-healthy stream does.
7. **Keepalive mismatch → 502.** ALB documents it; target idle must exceed 60 s. CloudFront origin keep-alive 5 s is the same class toward origins. gunicorn `keepalive` 2 s **[→C7-1]**.
8. **Outer < Σ attempts.** Envoy 2.7 + 0.3; Istio `perTryTimeout` ignored when route timeout is 0.
9. **Timeout without cancel.** Server finishes after `DEADLINE_EXCEEDED`; capacity burned. Handler that ignores context.
10. **Hedging a non-idempotent call.** Double capture. gRPC and .NET both warn; Envoy hedge is a retry in disguise and inherits retry-on rules.
11. **Hedging + retry on one gRPC method.** Forbidden by A6.
12. **Envoy `initial_requests`.** Not implemented. Config that looks like Dean fan-out is a no-op.
13. **GC / pause / clock.** [process-pauses.md](../../../cases/data-intensive-design/process-pauses.md): a 15 s stop-the-world makes a live node look dead; leases and deadlines are the same math.
14. **LLM 10-minute SDK defaults** retried, wall-clock × (retries+1), dying on ALB 60 s idle unless streamed **[→breaker §5]**.
15. **Breaker never trips.** Hung calls never increment the counter — C1’s first dependency.

**When a timeout is the wrong tool.** Long-lived streams and notifications (use idle + `max_stream_duration`). In-process function calls. Work that *must* finish after the client is gone (checkpointed catchup — SRE’s explicit exception; check the deadline *after* the checkpoint). Pure tail-latency on idempotent fan-out (hedge, then still keep a deadline). Health probing (**C3**) — a probe timeout is a liveness guess, not an RPC budget. Do not use a timeout as a load-shedder when you have an explicit shed (**C10**); the timeout is the backstop, not the policy.

**When-not-to-use a *tight* timeout.** p99.9 ≈ p50 without padding; multi-region callers measured against in-AZ histograms; first request on a cold connection; anything whose legitimate work exceeds the percentile (large payloads, reports).

---

## 8. Cross-links

| Id | Why |
|---|---|
| **C1** circuit breaker | Timeout / `DEADLINE_EXCEEDED` **is** a failure; Azure inappropriate-timeouts; slow-call rate is a timeout in disguise |
| **C2** retry | Per-try vs outer; Envoy “route timeout includes all retries”; do not rewrite jitter; hedge XOR retry |
| **C3** health | Probe interval/timeout ≠ RPC deadline; ALB 5 s probe timeout is a different knob |
| **C8** bulkhead | Timeout sets how long a bulkhead slot is held; a 30 s timeout on a 10-slot pool is 10 hung callers |
| **D4** tracing | Deadline is request context; OTel does not carry `grpc-timeout`; record remaining-ms on the span |
| First-pass C7 | [timeouts-deadlines-external-research.md](timeouts-deadlines-external-research.md) — trap table, CloudFront/ALB/NGINX, TCP, .NET tokens |
| Cases | [timeouts-and-delays.md](../../../cases/data-intensive-design/timeouts-and-delays.md), [unreliable-networks.md](../../../cases/data-intensive-design/unreliable-networks.md), [process-pauses.md](../../../cases/data-intensive-design/process-pauses.md) |

---

## 9. Sources

Fetched 2026-09-13 unless noted.

**Canon.** d1.awsstatic.com/builderslibrary/pdfs/timeouts-retries-and-backoff-with-jitter.pdf (Brooker; live `aws.amazon.com/builders-library/...` returned HTTP 409 this session) · sre.google/sre-book/addressing-cascading-failures · cacm.acm.org/research/the-tail-at-scale (Dean & Barroso, Feb 2013) · grpc.io/docs/guides/deadlines · grpc.io/blog/deadlines (2018-02-26) · github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md · grpc.io/docs/guides/request-hedging · github.com/grpc/proposal/blob/master/A6-client-retries.md · learn.microsoft.com/azure/architecture/patterns/circuit-breaker **[→breaker]** · Nygard *Release It!* 2nd ed. **[→breaker §1]**.

**Clients / libraries.** pkg.go.dev/net/http · github.com/golang/go `src/net/http/transport.go` · docs.oracle.com/en/java/javase/21/.../HttpRequest.Builder.html (`timeout` = infinite if unset) · learn.microsoft.com/dotnet/api/system.net.http.httpclient.timeout (100 s) · learn.microsoft.com/dotnet/core/resilience/http-resilience (30 s / 10 s; hedge max 10 / 2 s) · square.github.io/okhttp/5.x/... and github.com/square/okhttp `OkHttpClient.kt` · curl.se/libcurl/c/CURLOPT_TIMEOUT.html · curl.se/libcurl/c/CURLOPT_CONNECTTIMEOUT.html · requests.readthedocs.io/en/latest/user/quickstart/#timeouts (2.34.2) · resilience4j `TimeLimiterConfig.java` · pollydocs.org/strategies/timeout · github.com/grpc/proposal/A72-open-telemetry-tracing.md.

**Proxies / LB / mesh.** envoyproxy.io/docs/envoy/latest/faq/configuration/timeouts · .../configuration/http/http_filters/router_filter · .../api-v3/config/route/v3/route_components.proto (1.40.0-dev) · istio.io/latest/docs/reference/config/networking/virtual-service · istio.io/latest/docs/tasks/traffic-management/request-timeouts · linkerd.io/2-edge/features/retries-and-timeouts · docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html · docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesOrigin.html · nginx.org/en/docs/http/ngx_http_proxy_module.html · man7.org/linux/man-pages/man7/tcp.7.html.

**Cited forward.** [timeouts-deadlines-external-research.md](timeouts-deadlines-external-research.md) (Node 22 `requestTimeout` 300 s — nodejs.org 409 this session; undici; axios; urllib3; PgJDBC; Postgres `statement_timeout`; gunicorn; uWSGI) · [circuit-breaker-external-research.md](circuit-breaker-external-research.md) §§1, 2, 5 · [retry-backoff-external-research.md](retry-backoff-external-research.md) §3 · [mesh-proxy-retry-external-research.md](mesh-proxy-retry-external-research.md) (Linkerd HTTPRoute timeout 0 = off; API Gateway 50 ms–29 s via REL05-BP05).

---

## 10. Uncertain / left out

- Live Builders’ Library HTML 409; Brooker numbers are from the official PDF, not the JS-rendered page.
- Exact Go toolchain minor on pkg.go.dev this fetch (page published 2026-09-01; `DefaultTransport` fields confirmed in master `transport.go`).
- `PROTOCOL-HTTP2.md` GitHub HTML blob was empty this fetch; grammar (`≤8` digits + `H|M|S|m|u|n`, omit = infinite) taken from search-indexed master text and matches **[→C7-1]**.
- Node.js v22 `requestTimeout` / undici / axios / PgJDBC / gunicorn / uWSGI not re-fetched (409 or already in first pass).
- CloudFront *response timeout* configurable range / quota-increase path: only the **30 s** default and “completion timeout unenforced if unset” are asserted.
- Istio current-version behavior when VS timeout is omitted: docs say “disabled”; old issues show Envoy `timeout: 0s`. Whether every Istio 1.2x still writes 0 s was not re-dumped from a live control plane.
- Linkerd numeric default when annotations are absent: treated as **not enforced**, not as Envoy 15 s.
- API Gateway integration timeout **29 s** not on the quotas page this fetch; cited only via the mesh-retry note / REL05-BP05.
- Envoy `initial_requests` still `#not-implemented-hide:` as of the 1.40.0-dev proto; no newer implementation commit verified.
- gRPC-Go hedging remains “Not yet supported” on the guide; a later grpc-go release enabling it was not checked in source.
- Java `HttpClient` connect-timeout-unset → OS TCP limits is an inference; only “empty Optional” is documented.
- Brooker 0.1% / p99.9 is an Amazon *example*, not an industry standard. The checkout table is a drill.
- PromQL / OTel attribute names above are recommendations, not a vendor schema.
- Φ accrual detector details stay in the DDIA case; not re-derived.
- Nygard’s per-pattern prose mapping Timeouts → antipatterns was not fetchable **[→breaker §7]**.
