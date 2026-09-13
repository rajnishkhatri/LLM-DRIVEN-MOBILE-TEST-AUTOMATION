---
type: research
title: 'Timeouts & deadline propagation — external research (2026-09-13)'
description: >-
  Source-verified research backing the Timeouts and deadline propagation
  Concept in cases/SystemDesignPatterns: the no-default-timeout trap table
  across clients, server/proxy defaults (NGINX, ALB, CloudFront, gunicorn,
  Node), deadline-propagation wire mechanics (grpc-timeout, Envoy headers, Go
  context, .NET tokens), timeout-hierarchy math, the TCP-layer floor, and
  documented failure modes. Facts already verified in the circuit-breaker and
  retry notes are cited forward, not re-fetched.
tags: [research, timeouts, deadlines, resilience, system-design-patterns]
---

# C7 Timeouts & deadline propagation — external research (2026-09-13)

**Method.** Every fact was fetched from the primary page on 2026-09-13 (source-file facts from the project's master branch, retrieved and grepped). Paraphrase throughout; numbers and option names reproduced exactly. Facts marked **[→retry]** / **[→breaker]** are cited forward from [retry-backoff-external-research.md](retry-backoff-external-research.md) and [circuit-breaker-external-research.md](circuit-breaker-external-research.md) (verified there 2026-09-13; not re-verified). Unverifiable items are in "Uncertain" and are not asserted in the Concept.

**Cited forward, not re-verified:** Brooker's pick-timeout-at-p99.9 rule and "retries are selfish" **[→breaker §1]**; SRE deadline propagation 30 s → 23 s → 19 s **[→breaker §1]**; per-attempt vs total timeout and Envoy "route timeout includes all retries" **[→retry §3]** (reconfirmed on the route proto, §3); gRPC deadlines — no default, remaining-time forwarding, propagation default-on in Java/Go **[→retry §3]**; Anthropic/OpenAI SDK 10-minute defaults, TS scaling to 60 min, TTFT guidance **[→breaker §5]**; Azure "inappropriate time-outs" **[→breaker §1]**; Eskildsen napkin math (5 s timeout ≈ 1/50 capacity) **[→breaker §1]**.

## 1. The "no default timeout" trap table

| Client | Option | Default | Meaning |
|---|---|---|---|
| Go `http.Client` | `Timeout` | **0** | "A Timeout of zero means no timeout." Covers connect, redirects, and body read (pkg.go.dev/net/http, Go 1.27.1) |
| Go `http.DefaultTransport` | dialer `Timeout`/`KeepAlive` 30 s; `TLSHandshakeTimeout` 10 s; `IdleConnTimeout` 90 s; `ExpectContinueTimeout` 1 s; `MaxIdleConns` 100 | as listed | but `ResponseHeaderTimeout` **0 = no timeout** — nothing bounds a server that connects and then stalls before headers (`transport.go`, master) |
| Go `http.Server` | `ReadTimeout`, `WriteTimeout` | **0** = no timeout | `ReadHeaderTimeout` 0 falls back to `ReadTimeout`; `IdleTimeout` 0 falls back to `ReadTimeout`; all three zero → unbounded (`server.go`, master) |
| Python `requests` | `timeout=` | **None** | "Failure to do so can cause your program to hang indefinitely"; read timeout = seconds with no bytes on the socket, not whole-download; `(connect, read)` tuple form; connect timeout applies **per IP attempt** (v4+v6 → perceived timeout doubles) |
| `urllib3` | `Timeout(total=None)` | **None** = infinite | read/total "only measure the time between read operations on the socket" |
| Node.js `http.Server` (v22 LTS) | `requestTimeout` | **300 000 ms**, 408 then close | v18.0.0 changed the default from no timeout to 300 s; `headersTimeout` = min(`requestTimeout`, 60 000) since v18.14.0; `server.timeout` **0** (v13 changed from 120 s); `keepAliveTimeout` **5000 ms** |
| Node.js `http.request` (client) | — | **none** | the `timeout` option only emits `'timeout'`; "The request must be destroyed manually." |
| undici / Node `fetch` | `headersTimeout` **300 000 ms**; `bodyTimeout` **300 000 ms** (time **between body chunks**, not total); `connectTimeout` 10 000; `keepAliveTimeout` 4 000 | as listed | 0 disables (undici `docs/api/Client.md`, main) |
| axios | `timeout` | **0** | README v1.x: default 0 = no timeout; no separate connect timeout |
| Java `java.net.http.HttpClient` | request timeout | **none** | not setting one is "the same as setting an infinite Duration"; `connectTimeout` unset → empty `Optional`, no default documented (JDK 21) |
| .NET `HttpClient` | `Timeout` | **100 s** | the one mainstream client with a real total default; per-request `CancellationTokenSource` races it, shorter wins (ms.date 2025-07-01) |
| OkHttp | `connectTimeout`/`readTimeout`/`writeTimeout` **10 s each**; `callTimeout` **0** | call timeout off | "The call timeout spans the entire call" — DNS, connect, request body, server processing, response body; redirects and retries share one period (`OkHttpClient.kt`, master) |
| curl / libcurl | `--max-time` / `CURLOPT_TIMEOUT` | **0** — never times out during transfer | `--connect-timeout` default **300 s** |
| PgJDBC | `socketTimeout` | **0 = disabled** | reads can block forever; `connectTimeout` 10 s, `cancelSignalTimeout` 10 s |
| PostgreSQL server | `statement_timeout` | **0 = disabled** | also `lock_timeout` 0, `idle_in_transaction_session_timeout` 0; setting `statement_timeout` globally in postgresql.conf is "not recommended" — set per role/session |

**Slowloris context.** Cloudflare, "The complete guide to Go net/http timeouts" (2016-06-29; the Go field docs above are the current source of truth): package-level `http.Get` has no timeouts; `http.ListenAndServe` with zero-value timeouts leaks descriptors to slow clients until `accept4: too many open files`.

**Pattern:** connect timeouts usually have sane defaults (Go dialer 30 s, OkHttp 10 s, undici 10 s, PgJDBC 10 s, curl 300 s); it is the **total/read** budget that defaults to infinity almost everywhere. .NET (100 s) and Node's server side (since 18) are the exceptions.

## 2. Server / proxy side

- **NGINX** (`ngx_http_proxy_module`): `proxy_connect_timeout` **60s** ("cannot usually exceed 75 seconds"), `proxy_read_timeout` **60s** — "only between two successive read operations", not the whole response — `proxy_send_timeout` **60s**, `proxy_next_upstream_timeout` **0**. NGINX's 60 s is an *idle* bound: a trickling upstream can stream for hours.
- **AWS ALB** (attributes page): idle timeout default **60 s** (1–4000). Documented rule: the *target's* idle timeout must be **larger than** the load balancer's, otherwise the target closes the TCP connection while the ALB still considers it open, the ALB forwards a request into it, and the client gets **HTTP 502**. ALB does not use HTTP/2 PING as idle reset; HTTP client keepalive duration default **3600 s** (cannot be disabled).
- **CloudFront**: **response timeout default 30 s** — a *per-wait* timer (time to first packet AND between packets); the **response completion timeout** is the actual total cap and is **unenforced by default**, so a trickling origin can stream indefinitely. Origin keep-alive timeout default **5 s**; connection timeout **10 s × 3 attempts**. On response timeout GET/HEAD are retried per connection attempts; POST/PUT/PATCH/DELETE/OPTIONS are not.
- **gunicorn** (master `config.py`; docs site 404'd this fetch): `timeout` **30** — workers silent longer are killed and restarted; sync workers: bounds request handling; async workers: liveness heartbeat only. `graceful_timeout` **30**; `keepalive` **2 s**, with gunicorn's own advice to raise it behind a load balancer.
- **uWSGI**: `harakiri` has no default listed — no worker-kill timeout unless set.

## 3. Deadline propagation mechanics

- **Wire format** (grpc/grpc `doc/PROTOCOL-HTTP2.md`): the deadline travels as the `grpc-timeout` request header — ASCII integer of **at most 8 digits** plus one unit from `H M S m u n`. "If Timeout is omitted a server should assume an infinite timeout." The wire carries a *relative* timeout; each sender recomputes remaining time from its absolute deadline.
- **Inheritance**: no default deadline; an intermediary that received 2 s and spent 0.5 s forwards ~1.5 s; automatic in Java and Go when the incoming context is used for outbound calls **[→retry §3]**.
- **Why absolute deadlines compose** (gRPC blog "gRPC and Deadlines", 2018-02-26): without a deadline, resources are held for all in-flight requests up to the maximum timeout. APIs split between *deadline* (a point in time: C++ `set_deadline`) and *timeout* (a duration: Go `context.WithTimeout`, Java `withDeadlineAfter`); servers check `IsCancelled()` / `ctx.Err()`. A duration restarts at every hop and silently extends the end-to-end budget; a point in time survives any number of hops.
- **Envoy headers** (router filter, 1.40.0-dev): `x-envoy-upstream-rq-timeout-ms` overrides the route timeout; Envoy stamps `x-envoy-expected-rq-timeout-ms` onto the upstream request — the time it expects completion in — so the upstream can make deadline-aware decisions; `x-envoy-upstream-rq-per-try-timeout-ms` must be less than the global route timeout or it is ignored. Route API (`route_components.proto`): `timeout` **default 15 s**, "includes all retries", 0 disables; separate `idle_timeout` bounds stream inactivity.
- **Go idiom** (pkg.go.dev/context): "WithTimeout returns WithDeadline(parent, time.Now().Add(timeout))"; "If the parent's deadline is already earlier than d, WithDeadline(parent, d) is semantically equivalent to parent" — a child can shorten but never extend. Expiry yields `context.DeadlineExceeded`; `context.Cause` (1.20+) recovers the reason.
- **.NET** (cancellation docs, ms.date 2026-03-17): cooperative cancellation; `CancellationTokenSource.CancelAfter` for deadline-as-timeout (later calls reset the delay); `CreateLinkedTokenSource` composes an external caller token with an internal timeout token — the .NET analog of context inheritance; nothing crosses the process boundary automatically; `HttpClient.Timeout` and a per-request token race, shorter wins.

## 4. Timeout hierarchy math

**The inequality.** For `A` attempts with per-try timeout `T` and backoff sleeps `bᵢ`: `outer ≥ Σᵢ(Tᵢ) + Σᵢ(bᵢ)` — otherwise the outer deadline truncates later attempts. Envoy documents the failure mode: a 3 s route timeout including retries, a 2.7 s first try, 0.3 s left for backoff plus retry **[→retry §3]**; a per-try larger than the route timeout is ignored. The .NET standard pipeline deliberately inverts it in the safe direction: total 30 s outside retry (3 × exponential from 2 s) outside a 10 s attempt timeout **[→breaker §2]** — worst-case inner exceeds outer, so the total is the binding budget. Both designs are coherent; the incoherent one is an inner budget exceeding the outer without anyone noticing.

**Phase decomposition** (libcurl timing infos, cumulative from start): `NAMELOOKUP_TIME` → `CONNECT_TIME` → `APPCONNECT_TIME` (TLS) → `PRETRANSFER_TIME` → `STARTTRANSFER_TIME` (TTFB) → `TOTAL_TIME`.

| Phase | Knobs (verified above) |
|---|---|
| connect | curl 300 s; Go dialer 30 s; OkHttp 10 s; undici 10 s; PgJDBC 10 s; CloudFront 10 s×3; NGINX 60 s |
| TLS | Go `TLSHandshakeTimeout` 10 s |
| TTFB / headers | Go `ResponseHeaderTimeout` (0!); Node server `headersTimeout` 60 s; undici `headersTimeout` 300 s; Cloudflare AI Gateway TTFB-based timeout **[→retry §5]** |
| read / between-bytes | requests/urllib3 read; NGINX `proxy_read_timeout` 60 s; CloudFront response timeout 30 s; undici `bodyTimeout` 300 s; OkHttp `readTimeout` 10 s; ALB idle 60 s; PgJDBC `socketTimeout` |
| total | Go `Client.Timeout`; curl `--max-time`; axios; OkHttp `callTimeout`; .NET 100 s; Java `HttpRequest.timeout`; Envoy route 15 s; CloudFront response completion timeout; Postgres `statement_timeout` |

**Setting values.** Total/per-try from the measured latency distribution at the percentile matching the false-timeout budget (p99.9 ≈ 0.1%) **[→breaker §1]**. Connect timeouts from network physics — the requests docs' rule: slightly above a multiple of 3 seconds, the default TCP retransmission window. Read/idle timeouts bound *stall*, not duration — right for streams where total time is legitimately unbounded but silence is not. Preserve the distinction: NGINX / CloudFront / undici-body / requests-read are **between-byte** timers; Envoy route / OkHttp call / .NET / Go client are **end-to-end** timers; a slow trickle defeats the first class entirely.

## 5. TCP layer (`tcp(7)`, `connect(2)`, man7.org)

- `tcp_keepalive_time` **7200 s**, `tcp_keepalive_intvl` **75 s**, `tcp_keepalive_probes` **9** — probes sent only with `SO_KEEPALIVE` enabled. An idle connection to a dead peer, without app timeouts, is detected after **≈ 2 h 11 m** at best, never by default.
- `tcp_syn_retries` **6** — "retrying for up to approximately 127 seconds": the effective OS connect timeout every no-connect-timeout client inherits.
- `tcp_retries2` **15** — unacknowledged data on an established connection gives up after roughly **13 to 30 minutes**. That is how long a write to a silently dead peer can hang without a socket timeout.
- RST vs silent drop: a peer that answers with a reset fails fast (ECONNREFUSED); a blackholed peer gives no signal and burns the full SYN-retry budget to ETIMEDOUT.

## 6. Failure modes

1. **Missing timeout pins a worker pool.** A present-but-long timeout collapses capacity (5 s ≈ 1/50 of a 100 ms fleet **[→breaker §1]**); with §1 defaults the pin is not 5 s but TCP's 13–30 minutes (§5). Azure's "inappropriate time-outs" names the mechanism **[→breaker §1]**.
2. **Keepalive mismatch → intermittent 502s.** ALB documents the rule (target idle > LB idle 60 s). gunicorn ships the mismatch by default: `keepalive` 2 s < ALB 60 s; its own docs advise raising it behind an LB. CloudFront's 5 s origin keep-alive constrains origins the same way.
3. **Race-to-the-slowest at the edge.** CloudFront 30 s vs ALB 60 s vs NGINX 60 s vs gunicorn 30 s vs Node 300 s: the shortest timer on the path defines the real SLA, usually one nobody chose (cf. Istio's 3 s-outer vs 10 s-inner drill **[→retry §3]**).
4. **Long-tail LLM calls hide behind 10-minute client defaults**, retried — wall-clock up to timeout × (retries + 1) **[→breaker §5]**; a 10-minute SDK budget is unreachable through an ALB (60 s idle) or CloudFront (30 s per-wait) unless streaming keeps bytes flowing.
5. **GC pauses and clock trouble corrupt deadline math.** Covered in-repo: link `cases/data-intensive-design/process-pauses.md`.
6. **Slowloris by default.** Go's zero-value server; Node before v18 (no request timeout until the 300 s default).

## Sources

Clients: pkg.go.dev/net/http (Go 1.27.1) · golang/go master `server.go`, `transport.go` · blog.cloudflare.com/the-complete-guide-to-golang-net-http-timeouts (2016-06-29) · requests.readthedocs.io (quickstart, advanced) · urllib3.readthedocs.io util reference · nodejs.org/docs/latest-v22.x/api/http.html (cross-checked v26.8.2) · nodejs/undici `docs/docs/api/Client.md` · axios README v1.x · JDK 21 `java.net.http` API · learn.microsoft.com HttpClient.Timeout (2025-07-01) · square/okhttp master `OkHttpClient.kt` · curl.se CURLOPT_TIMEOUT / CURLOPT_CONNECTTIMEOUT / curl_easy_getinfo · jdbc.postgresql.org/documentation/use · postgresql.org runtime-config-client.
Servers/proxies: nginx.org ngx_http_proxy_module · AWS ALB edit-load-balancer-attributes · CloudFront RequestAndResponseBehaviorCustomOrigin + DownloadDistValuesOrigin · benoitc/gunicorn master `config.py` · uwsgi-docs Options.
Propagation: grpc/grpc `doc/PROTOCOL-HTTP2.md` · grpc.io/blog/deadlines (2018-02-26) · envoyproxy.io router filter + route_components.proto · pkg.go.dev/context · learn.microsoft.com cancellation-in-managed-threads (2026-03-17).
TCP: man7.org tcp(7), connect(2).
Cited forward: [circuit-breaker-external-research.md](circuit-breaker-external-research.md) §§1, 2, 5 · [retry-backoff-external-research.md](retry-backoff-external-research.md) §§3, 5.

## Uncertain / could not verify (excluded from the Concept)

- AWS Builders' Library "Timeouts": live pages client-rendered and archive unreachable this session; only cited-forward facts used.
- uWSGI harakiri "off by default" is inferred from the option listing no default.
- Java HttpClient connect behavior when unset ("falls to OS TCP limits") is an inference.
- CloudFront response-timeout configurable range not on the fetched pages; only 30 s / 5 s / 10 s×3 defaults asserted. NLB HTTP/2 PING behavior unchecked.
- Node requestTimeout motivation (smuggling/slowloris hardening) not stated on the docs page.
- gunicorn defaults from master source; docs-site rendering unreachable.
- urllib3 v2 `Timeout.DEFAULT_TIMEOUT` sentinel semantics; assert only None = infinite.
- axios-http.com redirects to an unfamiliar host; README used instead.
- Envoy route default 15 s is on the route proto page only.
- RST wording kept at the man-page level (no literal "RST" in connect(2)).
- OkHttp versioned doc-site pages 404'd; master source + KDoc used.
