---
type: reference
title: 'Request–response (REST / gRPC sync)'
description: 'Synchronous request–response as a style of exchange: REST over HTTP/1.1, HTTP/2 and HTTP/3, and gRPC unary. Wire semantics (safe/idempotent, trailers, TCP HOL), connection lifecycle (reuse, GOAWAY, coalescing/421), scaling and fan-out caps, failure and reconnect, proxy/LB idle clocks with verified defaults, and when a held connection is the wrong shape.'
tags: [system-design-patterns, communication, rest, grpc, http]
---

# Request–response (REST / gRPC sync)

**See also:** [REST, RPC, and service dataflow (DDIA)](../data-intensive-design/rest-rpc-dataflow.md) · [timeouts](TimeoutsDeadlines.md) · [retry](RetryBackoff.md) · [idempotency](Idempotency.md) · [load balancing](LoadBalancing.md) · [circuit breaker](CircuitBreaker.md) · [pub/sub & queues](PubSubQueues.md) · [WebSocket](WebSockets.md) · [SSE](ServerSentEvents.md) · [webhooks](Webhooks.md) · [API versioning](ApiVersioning.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/a1-request-response-external-research.md)

Request–response is the synchronous exchange: one caller, one callee, one reply (or a classified failure) that the caller waits for. That covers REST over any HTTP version and **gRPC unary**. Every other communication pattern in this group is a deviation — a broker, a long-lived push socket, a callback. Quality attributes: **simplicity** (no broker; correlation is the connection or stream) and **consistency** (the answer reflects the state the caller just caused). Costs: caller and callee coupled in time; every idle, route, and deadline timer on the path is part of the contract; a timeout leaves the outcome unknown.

A network call is not a local call. [REST, RPC, and service dataflow](../data-intensive-design/rest-rpc-dataflow.md) already owns location transparency, IDL choice (OpenAPI vs protobuf), discovery / load-balancer / mesh *placement*, and request/response compatibility when servers upgrade first. This Concept does not rewrite that argument. It owns the **wire**: how HTTP and gRPC unary actually move, how connections live and die, what the proxies do to them, and when holding the caller is the wrong shape.

What stays on a sibling, so it is not re-derived here:

| Sibling | What stays there |
|---|---|
| [Pub/sub](PubSubQueues.md) | Brokers, competing consumers, async fan-out, long work |
| [WebSocket](WebSockets.md) / [SSE](ServerSentEvents.md) | Long-lived push, heartbeats, resume cursors, sticky sessions |
| [Webhooks](Webhooks.md) | Inverted request–response; the receiver is the idempotent one |
| [API versioning](ApiVersioning.md) | OpenAPI / protobuf / GraphQL evolution |
| [Load balancing](LoadBalancing.md) | Algorithms (least-conn, Maglev, consistent hash), panic/ejection |
| [API gateway](ApiGateway.md) | Product placement, BFF, aggregation |
| [Timeouts](TimeoutsDeadlines.md) | Timeout *policy* and deadline-propagation playbooks |
| [Idempotency](Idempotency.md) | Keys and dedup stores — required before retrying POST or unmarked gRPC |

## Lineage and vocabulary

- **Birrell & Nelson (1984)** ([38](../data-intensive-design/encoding-references.md)) made a network request look like a local procedure. **Waldo et al. (1994)** ([39](../data-intensive-design/encoding-references.md)) and **Vinoski (2008)** ([40](../data-intensive-design/encoding-references.md)) named why that is the bug, not the feature: latency, memory access, partial failure, and concurrency are qualitatively different on a network. REST's appeal, as the workspace note puts it, is that it treats state transfer as a different thing from a function call.
- **Fielding (2000 / 2008)** ([31](../data-intensive-design/encoding-references.md), [32](../data-intensive-design/encoding-references.md)) defines REST over HTTP's existing verbs, URIs, and representations — not "JSON over POST."
- **June 2022 rewrite** split the old RFC 7230–7235 / 7540 stack: **9110** (STD 97) is HTTP *semantics* (methods, status, safe/idempotent, `Retry-After`, 408, 421); **9112** is HTTP/1.1 *messaging* (persistence, pipelining, `Connection: close`); **9113** is the HTTP/2 mapping (streams, SETTINGS, GOAWAY); **9114** maps HTTP onto QUIC.
- **gRPC unary** (core concepts): the client sends one request and gets one response, "just like a normal function call." Transport is HTTP/2. Application status is a `(code, message)` pair in **trailers**, not the HTTP status line.

Vocabulary used below. An **exchange** is one REST request/response or one unary RPC. A **connection** is TCP (HTTP/1.1, HTTP/2) or QUIC (HTTP/3). A **stream** is an HTTP/2 or HTTP/3 request–response pair multiplexed on one connection — HTTP/1.1 has none; Envoy still maps each HTTP/1.1 request onto an internal stream for timeouts. A **deadline** is an absolute time; a **timeout** is a duration. gRPC converts a deadline to remaining `grpc-timeout` so clock skew does not accumulate. An **idle timeout** is no *application* activity — distinct from TCP keepalive and from HTTP/2 PING.

## Wire semantics

HTTP is **stateless at the message layer** (RFC 9110 §3.3): each request's semantics are understandable in isolation; connection reuse must not change interpretation. Correlation of request to response is version-dependent: HTTP/1.1 uses implicit order on the connection; HTTP/2 and HTTP/3 use an explicit stream identifier.

**Safe vs idempotent (RFC 9110 §9.2).** Safe: GET, HEAD, OPTIONS, TRACE — the client does not request a state change. Idempotent: PUT, DELETE, and all safe methods — *N* identical requests have the same *intended* effect as one. POST and PATCH are neither. A client **SHOULD NOT** automatically retry a non-idempotent method unless it has another way to know the semantics are actually idempotent ([idempotency](Idempotency.md)). A **proxy MUST NOT** automatically retry non-idempotent requests. Treating POST as retryable buys availability and loses exactly-once; the RFC calls out the "idle persistent connection closed before any response" guess as the riskier path.

| Mapping | How an exchange travels | What you buy | What you pay |
|---|---|---|---|
| **HTTP/1.1** (RFC 9112 §9.3) | Persistent connections are the default. A client that does not support them must send `Connection: close` on every request; a server that does not must send `Connection: close` on every non-1xx response. One in-flight request per connection unless pipelining (MAY send several; MUST respond in order). Pipelining is still in the spec; browsers do not use it (HOL plus decades of broken intermediaries). Practical HTTP/1.1 is **stop-and-wait per connection**. | Simple; one failure is one request | Six sockets per host in Chromium; HOL at the application layer |
| **HTTP/2** (RFC 9113) | Binary framing, HPACK, concurrent streams on one TCP connection. Client streams odd-numbered; stream 0 is control. | Far fewer sockets; header compression | **TCP HOL remains**: a lost packet stalls every multiplexed stream |
| **HTTP/3** (RFC 9114) | One QUIC stream per exchange; per-stream loss recovery. Each endpoint declares an **idle timeout in the handshake**; if no packets arrive for that duration the peer assumes the connection is gone. Clients SHOULD open a new connection as the idle timeout approaches. Servers SHOULD NOT actively keep connections open. | No TCP HOL; connection migration; 0-RTT | UDP-path middlebox hostility; a negotiated idle timeout PINGs cannot always extend |
| **REST sync** | One method + target URI + optional body → one status + representation. Caching is a first-class semantic (GET/HEAD; POST is theoretically cacheable and almost never is). `Retry-After` on 503 / 3xx and 408 (incomplete request) are HTTP features, not conventions. | Cache/CDN estate; every client speaks it | Hop-local timers; no standard remaining-budget header |
| **gRPC unary** | Always `:method POST`, `:path /Service/Method`, `content-type` beginning `application/grpc`, required `te: trailers`. HTTP `:status` on a well-formed RPC is **200** even when `grpc-status` is non-OK. Trailers carry `grpc-status` (decimal, no leading zeros) and optional percent-encoded `grpc-message`. **Trailers-Only** (headers + trailers, no DATA) is legal for immediate errors. Length-prefixed messages: 1-byte compressed flag + 4-byte big-endian length + payload; DATA frame boundaries are **not** message boundaries. Suggested header-size default: **8 KiB**. | Contracts, trailer status, `grpc-timeout` | Trailer-faithful HTTP/2 end to end; opaque to HTTP tooling that only sees `:status 200` |

HTTP/2 SETTINGS the RFC actually numbers (initial values; peers MAY lower them):

| Setting | Initial | Why it matters |
|---|---|---|
| `SETTINGS_MAX_CONCURRENT_STREAMS` | unlimited; RFC recommends ≥ 100 | The real fan-out cap once HTTP/2 collapses the 6-socket pool |
| `SETTINGS_HEADER_TABLE_SIZE` | 4,096 | HPACK dynamic table |
| `SETTINGS_INITIAL_WINDOW_SIZE` | 65,535 octets | Per-stream flow control; Envoy now starts at 16 MiB (below) |
| `SETTINGS_MAX_FRAME_SIZE` | 16,384 | Frame size, not message size |
| `SETTINGS_MAX_HEADER_LIST_SIZE` | unlimited | gRPC's suggested request-header default is a separate **8 KiB** |

If `content-type` does not begin `application/grpc`, servers SHOULD answer HTTP **415** so ordinary HTTP/2 clients do not treat an HTTP 200 + `grpc-status` trailer as success. gRPC calls are **not assumed idempotent** unless marked: unstarted calls may be retried; the protocol has no duplicate-suppression.

**gRPC status codes** (0–16). Library-generated: CANCELLED, UNKNOWN, DEADLINE_EXCEEDED, PERMISSION_DENIED, RESOURCE_EXHAUSTED, UNIMPLEMENTED, INTERNAL, UNAVAILABLE, UNAUTHENTICATED (and OK). **Never generated by the library, only by user code:** INVALID_ARGUMENT, NOT_FOUND, ALREADY_EXISTS, FAILED_PRECONDITION, ABORTED, OUT_OF_RANGE, DATA_LOSS. Decision rule for 9 / 10 / 14: **UNAVAILABLE** if the client can retry just this call; **ABORTED** if the client should retry a higher-level sequence; **FAILED_PRECONDITION** if the client must not retry until state is fixed. UNAVAILABLE "is most likely a transient condition" — "not always safe to retry non-idempotent operations." DEADLINE_EXCEEDED "may be returned even if the operation has completed successfully" (the response arrived after the deadline). No data transmitted before the deadline → DEADLINE_EXCEEDED; some data (e.g. request metadata written) then connection break → UNAVAILABLE. RST_STREAM: REFUSED_STREAM → UNAVAILABLE (retry, possibly elsewhere); CANCEL from server → CANCELLED; ENHANCE_YOUR_CALM → RESOURCE_EXHAUSTED; INADEQUATE_SECURITY → PERMISSION_DENIED; most other RST codes → INTERNAL.

## Connection lifecycle

```
HTTP/1.1:  TCP(+TLS) → request → response → idle until close or next request
HTTP/2:    TCP(+TLS) → SETTINGS both ways → N concurrent streams → GOAWAY → drain → TCP close
HTTP/3:    QUIC/TLS1.3 → SETTINGS → N QUIC streams → GOAWAY → idle-timeout or CONNECTION_CLOSE
gRPC:      channel (HTTP/2 session) → unary stream (HEADERS + DATA + trailers) → stream ends; channel reused
```

**HTTP/2 persistence (RFC 9113 §9.1).** Connections are persistent. Clients SHOULD NOT open more than one HTTP/2 connection to a given host+port (unless replacing a connection near stream-id exhaustion, refreshing TLS keys, recovering from a connection error, or using a different SNI / client cert). Servers are encouraged to keep connections open as long as possible but MAY close idle ones. The closer SHOULD send GOAWAY first. Stream identifiers cannot be reused; exhausting the 31-bit space forces a new connection.

**Coalescing (RFC 9113 §9.1.1).** A connection MAY carry requests for **multiple URI authorities** if the server is authoritative — same resolved IP for cleartext; for `https`, the certificate MUST also be valid for the new host. RFC 9110 §4.3.4 adds: DNS for the new origin contains the connection's IP, unless the server sends an ORIGIN frame (RFC 8336). The failure mode the RFC names: TLS terminates on a middlebox that routes by SNI; the client then sends a coalesced `:authority` the backend is not configured for. The server answers **421 Misdirected Request**. The client MAY retry on a *different* connection, **whether or not the method is idempotent**. A proxy MUST NOT generate 421. Coalescing cuts handshakes; it also pins many origins to one VIP and one certificate, and it breaks SNI-based routing unless every coalesced name is configured on that listener (Envoy issue #6767 is the mesh-shaped instance).

**gRPC GOAWAY / lame-duck.** Server GOAWAY includes the last accepted stream id. Clients MUST treat later streams as UNAVAILABLE and retry elsewhere; already-accepted streams run to completion. PING: peer must echo. If a **server-initiated** PING times out, the server closes outstanding calls with CANCELLED; if a **client-initiated** PING times out, the client closes all calls with UNAVAILABLE. Detectable client connection failure → all calls UNAVAILABLE; server-side → open calls CANCELLED. Cancellation is not a rollback.

**ALB: two clocks, not one.** **Connection idle timeout** (default **60 s**, range 1–4000): no bytes in either direction. HTTP/2 PING does **not** reset it. **HTTP client keepalive duration** (default **3600 s**, range 60–604800): max age from *establishment*; it does not reset on traffic. At expiry ALB accepts one more request then closes (`Connection: close` on HTTP/1.x, GOAWAY on HTTP/2). AWS recommends the *application's* idle timeout be **larger** than the ALB's, otherwise the target closes first and ALB returns **502** on the next request. A short keepalive (used with zonal shift) drains impaired AZs faster; a long one saves handshakes and holds clients on a dying AZ.

## Scaling and fan-out

**HTTP/1.1 browser pool.** Chromium HEAD `client_socket_pool_manager.cc` (2026-09-13): `g_max_sockets_per_group` = **6** for the normal pool, **255** for WebSockets; process-wide soft cap **256**; unused-idle socket timeout **60 s**. A seventh concurrent HTTP/1.1 request to the same host queues. HTTP/2 collapses that to one connection, so the 6-slot limit is not the fan-out bound — `SETTINGS_MAX_CONCURRENT_STREAMS` is. Chromium's 6 is the HTTP/1.1 *socket* pool, not the H2 stream cap (browser-advertised H2 SETTINGS were not fetched).

| Product | Concurrent-stream default |
|---|---|
| RFC 9113 | unlimited initially; recommend ≥ 100 |
| NGINX `http2_max_concurrent_streams` | **128** (`http`/`server`) |
| AWS ALB HTTPS listener / `HTTP2` target group | **128** parallel requests per client HTTP/2 connection; server push not supported |
| Envoy `Http2ProtocolOptions.max_concurrent_streams` | **1024** "for safety" (changed from 2,147,483,647 in **1.36.0, 2025-10-14**); range 1–2³¹−1. H2 initial stream window now **16 MiB** (was 256 MiB); connection window **24 MiB**. Revert guard: `envoy.reloadable_features.safe_http2_options` |

A unary or REST handler that itself issues *N* synchronous downstream calls holds the inbound stream, thread, and deadline for `max(downstream_i)` plus local work. Sync request–response does **not** provide a broker, a retry budget, or a competing-consumer partition; *N* callers × *M* serial dependencies is *N·M* held connections. The programming model is a function call; the capacity model is Little's law on the held resource (thread, stream, FD). That amplification is why [retries](RetryBackoff.md) and [timeouts](TimeoutsDeadlines.md) are policy, not optional polish — and why many-consumer fan-out belongs on [pub/sub](PubSubQueues.md), not here.

**HTTP/2 at a proxy is not HTTP/2 to the backend.** ALB: "Because HTTP/2 uses front-end connections more efficiently, you might notice fewer connections between clients and the load balancer." The target-group default is still **HTTP/1.1**. HTTP/2 client → HTTP/1.1 target works (ALB demuxes); HTTP/1.1 client → HTTP/2 target is an **error**; gRPC requires an HTTPS listener + `GRPC` or `HTTP2` protocol version, a custom `/package.service/method` health check, and no Lambda targets; HTTP/2 client → `GRPC` target succeeds only for POST. Desync mitigation default is **defensive**. ALB listener pages list HTTP and HTTPS only — **no HTTP/3 listener**.

**Upstream keep-alive is a cache, not a cap.** NGINX `keepalive` (upstream, since **1.29.7** default `32 local`): max *idle* connections cached **per worker**; it "does not limit the total number of connections to upstream servers." Set it small enough that upstreams can still accept new connections. `proxy_http_version` is **1.1** since 1.29.7 (was 1.0); 1.1 or 2 is required for upstream keepalive.

## Failure and reconnect

| Event | HTTP/1.1 | HTTP/2 / gRPC | HTTP/3 |
|---|---|---|---|
| Idle close | Peer sends FIN / `Connection: close`; next request needs a new TCP(+TLS) | Idle timeout → drain + GOAWAY (Envoy) or FIN; in-flight streams finish if the drain allows | QUIC idle timeout; client SHOULD reconnect before it fires |
| Graceful server stop | `Connection: close` on the next response | GOAWAY(last-stream-id); new streams UNAVAILABLE / retry elsewhere | GOAWAY with stream/push id; clients MAY open a new connection |
| Mid-request TCP reset | Outcome unknown; retry only if idempotent (RFC 9110 §9.2.2) | Stream RST; gRPC maps REFUSED_STREAM → UNAVAILABLE (retry), others → INTERNAL / CANCELLED | QUIC RESET_STREAM / CONNECTION_CLOSE; same application uncertainty |
| Deadline first | Client gives up; server may still finish (orphaned work) | Client: DEADLINE_EXCEEDED; server auto-cancels the RPC (`CANCELLED`); the **application** must poll cancellation and stop spawned work | Same deadline mapping if the stack is gRPC; raw HTTP/3 has no `grpc-timeout` |
| Coalesced wrong origin | N/A (one Host per connection typical) | **421**; client MAY retry on a fresh connection even for POST | Same 421 rule (HTTP semantics) |
| 503 + `Retry-After` | Wait the indicated HTTP-date or delay-seconds (RFC 9110 §10.2.3) | Same header; gRPC apps usually see UNAVAILABLE unless a gateway mapped it | Same |

**gRPC deadlines vs HTTP timeouts.** Default: **no deadline** — a client can wait forever. Always set one. Client past deadline → `DEADLINE_EXCEEDED`. Server whose client deadline has passed → call cancelled (`CANCELLED`). Propagation: some languages (Java, Go) do it by default; C++ must enable it. The wire form is a **remaining duration** (`grpc-timeout` = at most 8 ASCII digits plus a unit `H`, `M`, `S`, `m`, `u`, or `n`); "If Timeout is omitted a server should assume an infinite timeout." Spec example: `grpc-timeout = 1S`.

| Clock | What it is | Propagates? |
|---|---|---|
| gRPC **deadline** | An instant. Converted to remaining `grpc-timeout` on the wire so clock skew does not accumulate | Yes, in Java and Go by default; C++ must enable it. 0.5 s already spent on a 2 s budget → 1.5 s forwarded |
| HTTP / Envoy / NGINX **timeout** | A duration local to that hop. Restarts or sits idle-based depending on the knob | No, unless something copies it (Envoy `MaxStreamDuration` "fixed time offset on grpc-timeout headers", a custom header) |
| ALB / Envoy HTTP **idle** | Silence at the connection — HTTP/2 PING does **not** reset it | No |

A 15 s Envoy route timeout and a 2 s gRPC deadline are *different clocks* — the tighter one wins, and the looser one hides nothing. [Timeouts](TimeoutsDeadlines.md) owns the policy; this Concept owns the fact that REST-over-HTTP has **no standard remaining-budget header**. The two timer *classes* (between-byte vs end-to-end) that make `proxy_read_timeout` misleading live there too.

**Reconnect is not session resume.** HTTP request–response has no session to resume ([WebSocket](WebSockets.md) and [SSE](ServerSentEvents.md) do). After GOAWAY or idle close the client opens a new connection and retries only what RFC 9110 / gRPC retry rules allow. gRPC channel state (`connected` / `idle`) and how you close a channel are language-dependent.

## Proxy and load-balancer clocks

The production bug is a **timeout sandwich**: client timeout *T*, proxy idle/route timeout *t < T*, backend work in *(t, T]*. The proxy cuts the stream; the client [retries](RetryBackoff.md); the backend still finishes the first attempt ([idempotency](Idempotency.md)). Invert it (*t > T*) and the proxy holds a connection the client has already abandoned.

| Envoy knob (docs banner `1.40.0-dev`) | Default | What it actually measures |
|---|---|---|
| HTTP protocol `idle_timeout` | **1 hour** | No active requests/streams at the HTTP layer. Independent of TCP keepalive. HTTP/2 PING does **not** keep it alive. HTTP/2 downstream: start drain. Set 0 to disable (leak warning). |
| `max_connection_duration` | **0 (unlimited)** | Age from connect; then drain. Optional jitter against a reconnect stampede. |
| HCM `drain_timeout` | **5 s** | Between first HTTP/2 GOAWAY and final GOAWAY. New streams still accepted in the grace window. Never force-kills active streams. |
| HCM `stream_idle_timeout` | **5 minutes** | No upstream/downstream activity on that stream. Recommended for *all* requests, not only streaming. Route `idle_timeout` overrides. |
| HCM `request_timeout` / `request_headers_timeout` | **disabled** | Whole request stream from the client / headers-only wait. Incompatible with never-ending streams. |
| Route `timeout` | **15 seconds** | Wait for a *complete* upstream response **after** the downstream request is fully received. Disable (0) for streaming. Does not start on a streaming request. |
| Cluster `connect_timeout` | **5 seconds** | Includes upstream TLS handshake. |
| TCP proxy `idle_timeout` / TCP pool `idle_timeout` | **1 hour** / **10 minutes** | Proxy idle vs unused upstream connection. |

| NGINX directive | Default | What bites |
|---|---|---|
| `keepalive_timeout` (core) | **75 s** | Idle client keep-alive. 0 disables. Docs: MSIE closes on its own in ~60 s. |
| `keepalive_requests` | **1000** (was **100** before 1.19.10) | Then close. |
| `keepalive_time` | **1 h** (since 1.19.10) | Max lifetime; close after the next request. |
| `client_header_timeout` / `client_body_timeout` / `send_timeout` | **60 s** | |
| `proxy_connect_timeout` / `proxy_read_timeout` / `proxy_send_timeout` | **60 s** | Read/send timeouts are *between successive* I/O ops, **not** total response time. A backend that dribbles a byte every 59 s never hits 60 s and can run for minutes. |
| `http2_max_concurrent_streams` | **128** | `http2` itself is **off** per-server since 1.25.1. |
| `upstream keepalive` / `keepalive_timeout` | **32 local** since 1.29.7 / **60 s** | Idle cache per worker, not a total connection cap. |

**HAProxy 3.0.** Default connection mode is keep-alive. `timeout client` / `timeout server` / `timeout connect`: **unspecified = infinite**, with a startup warning ("accumulation of expired sessions"). The manual's own example uses `timeout connect 5000ms`, `timeout client 50000ms`, `timeout server 50000ms` — those 5 s / 50 s figures are **example text, not compiled defaults**. For the request-read phase they recommend `timeout http-request` against Slowloris.

**Envoy coalescing / 421.** Browsers coalesce on wildcard certs + overlapping IPs; Envoy latches a connection to one listener/filter chain. Names that live on another chain get the first chain's route table. Mitigations named in envoy#6767: send 421 for unknown authorities; advertise RFC 8336 ORIGIN (sparse client support — not re-surveyed). Algorithm choice and panic/ejection live in [load balancing](LoadBalancing.md); this Concept only covers how H2 coalescing and keepalive pools change what the balancer *sees*.

## Verified defaults (2026-09-13)

| Thing | Value |
|---|---|
| RFC 9110 safe / idempotent | GET, HEAD, OPTIONS, TRACE / those plus PUT, DELETE |
| HTTP/1.1 persistence | on by default |
| H2 `SETTINGS_HEADER_TABLE_SIZE` / `MAX_HEADER_LIST_SIZE` initial | 4,096 / unlimited |
| H2 connections per host+port | SHOULD NOT > 1 |
| gRPC default deadline / omitted `grpc-timeout` | **none (infinite)** / server assumes infinite |
| gRPC unary HTTP method / success path | POST / HTTP 200 + trailer `grpc-status` |
| Chromium HTTP/1.1 sockets per host / unused idle | **6** / **60 s** |
| Envoy HTTP idle / stream idle / route / connect / drain / H2 max streams | **1 h** / **5 min** / **15 s** / **5 s** / **5 s** / **1024** |
| NGINX client keepalive / proxy read-send-connect / H2 streams / upstream keepalive | **75 s** / **60 s** / **128** / **32 local** (1.29.7) |
| ALB idle / client keepalive / H2 parallelism / target protocol default | **60 s** (1–4000) / **3600 s** (60–604800) / **128** / **HTTP1** |
| HAProxy unset timeouts | **infinite** + warning |

gRPC retry at the *protocol* (not [C2](RetryBackoff.md) policy): only calls that cannot be proven to have started, or that are marked idempotent, may be sent more than once. Application retry-code choice is explicitly *not* a fixed list — the library can emit the same code for different causes. Language keepalive defaults (`keepalive_time`, `permit_without_calls`) and channel reconnect backoff were **not** fetched; do not invent them.

## Failure modes of the style itself

1. **Unknown outcome on timeout.** RFC 9110 and gRPC both state it: DEADLINE_EXCEEDED / a closed connection can happen *after* the server applied the write. Retry without [idempotency](Idempotency.md) duplicates work. "Fail fast" frees the caller and creates orphans.
2. **Timeout sandwich.** Client 30 s, Envoy route 15 s, NGINX `proxy_read_timeout` 60 s (between reads), ALB idle 60 s, gRPC deadline unset (infinite). The first timer that fires is the truth; the others only add 502/504/UNAVAILABLE noise.
3. **HTTP/2 HOL / one-bad-stream.** One stalled window or one lossy TCP connection delays every multiplexed RPC on that channel. HTTP/3 fixes TCP HOL; it does not fix a server that stops reading.
4. **Coalescing → wrong backend.** Wildcard cert + shared VIP + SNI-selected filter chain. Symptom: 421, or worse, 200 from the *other* app. 421 is retryable even for POST — another duplicate-risk if the first hop did apply the request.
5. **Idle-close race.** ALB 60 s vs app 60 s; NGINX 75 s vs Chromium 60 s unused-idle; Envoy 1 h vs ALB 60 s in front of it. The shorter closer wins; the longer one sees a half-closed socket and 502s. HTTP/2 PING will not save you on ALB or Envoy HTTP idle.
6. **Status-code split brain.** REST clients key off HTTP 4xx/5xx. gRPC clients key off trailers. A proxy that only sees `:status 200` will not trip outlier detection on `grpc-status: 14` unless it understands gRPC. Trailers-only errors are easy to drop on HTTP/1.1 hop-by-hop conversions (`te: trailers` is how gRPC detects incompatible proxies).
7. **Sync fan-out amplification.** One inbound exchange × *N* outbound unary calls × retries × no deadline = thread/stream exhaustion. That case should have been a [queue](PubSubQueues.md) or a workflow, not a held request.

## When not to use synchronous request–response

| Situation | Why this is wrong | Go to |
|---|---|---|
| Caller should not wait (minutes of work, human-time batch, report generation) | Every hop's idle/route timeout will lie; you hold a connection for business time | [Pub/sub](PubSubQueues.md), durable workflow |
| Many independent consumers need the same event | Sync fan-out is *N* RPCs and *N* failure domains | [Pub/sub](PubSubQueues.md) |
| Server wants to push after the caller has gone | No connection left; polling is a bad A1 | [Webhooks](Webhooks.md), [SSE](ServerSentEvents.md), [WebSocket](WebSockets.md) |
| Interactive bidirectional stream (editor, game, agent tool loop) | Unary/REST is one shot; streaming gRPC is not this pattern either | [WebSocket](WebSockets.md), or gRPC bidi (out of A1) |
| Client is a browser tab that must stay updated | Request–response requires polling; proxies buffer or time out long polls | [SSE](ServerSentEvents.md) (one-way) or [WebSocket](WebSockets.md) (two-way) |
| Cross-org "fire and forget" integration | You cannot keep their HTTP request open; they cannot keep yours | [Webhooks](Webhooks.md) |
| Work is naturally idempotent *and* delayed | The useful contract is "deliver at least once with a key", not "wait for 200" | [Pub/sub](PubSubQueues.md) + [idempotency](Idempotency.md) |
| You only needed a function call in-process | Network RPC is not a local call ([rest-rpc-dataflow](../data-intensive-design/rest-rpc-dataflow.md)) | in-process |

**When it is the right default.** Ask/answer fits in a budget you can write down (and that budget is tighter than every proxy on the path). The callee's effect is small enough to bound. The caller needs the result to continue. GET-shaped reads want the HTTP cache semantics REST already has. Public APIs and browsers speak HTTP; gRPC unary is the internal analogue when you own both stubs and want deadlines + trailer status. Versus a queue: simpler ops, harder tail latency. Versus a socket or SSE: no heartbeat tax, no sticky-session tax, no half-open connection inventory.

## Trade-offs

| Buy | Pay |
|---|---|
| Simplest mental model; answer reflects caused state | Caller and callee coupled in time; the slowest hop is the contract |
| HTTP semantics: caching, status codes, ubiquity | Hop-local timers; no remaining-budget header; POST is not retryable |
| HTTP/2 multiplexing, fewer sockets | TCP HOL; coalescing/421; one bad connection delays every stream |
| HTTP/3 per-stream loss recovery | UDP-path hostility; handshake-negotiated idle timeout |
| gRPC: contracts, trailer status, shrinking `grpc-timeout` | HTTP 200 + trailers; default deadline is infinite; proxies must understand gRPC |
| Connection reuse (ALB 3600 s keepalive, Envoy 1 h idle) | Idle-close races and 502s when any hop's clock is shorter |

[Timeouts](TimeoutsDeadlines.md) decide **how long to wait**. [Retries](RetryBackoff.md) decide **whether to try again**. [Idempotency](Idempotency.md) decides **whether a retry is safe**. This pattern decides **whether the caller holds the line**. Do not stretch that hold past the shortest timer on the path.

## Sources

Verified 2026-09-13; the full URL list, per-claim provenance, and items deliberately left out (language keepalive defaults, browser H2 SETTINGS, NLB QUIC idle, CloudFront / GCP / Azure App Gateway idle) are in the [external research note](../../docs/research/sysdesign/a1-request-response-external-research.md). Location transparency, IDL, discovery/mesh placement, and compatibility stay in [rest-rpc-dataflow.md](../data-intensive-design/rest-rpc-dataflow.md); citations [31]–[44] live in [encoding-references.md](../data-intensive-design/encoding-references.md).

- Canon: RFC 9110 / 9112 / 9113 / 9114; RFC 8336 (ORIGIN); RFC 9000 §10.1 (QUIC idle); Fielding 2000/2008 [31][32]; Birrell & Nelson 1984 [38]; Waldo et al. 1994 [39]; Vinoski 2008 [40].
- gRPC: core concepts, status-codes, deadlines, error handling; `PROTOCOL-HTTP2.md` and `statuscodes.md` on `grpc/grpc` master.
- Proxies: Envoy latest timeout FAQ + `protocol.proto` (`1.40.0-dev`) and 1.36.0 changelog (2025-10-14); envoy#6767; NGINX core / proxy / upstream / v2 modules; AWS ALB attributes, listeners, target groups; HAProxy 3.0 configuration manual.
- Clients: Chromium HEAD `client_socket_pool_manager.cc` (6 / 255 / 60 s).
