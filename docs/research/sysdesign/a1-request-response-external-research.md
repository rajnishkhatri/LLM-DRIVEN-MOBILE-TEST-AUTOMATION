---
type: research
title: 'Request–response (REST / gRPC sync) — external research (2026-09-13)'
description: >-
  Source-verified research on synchronous request–response: HTTP/1.1 vs
  HTTP/2 vs HTTP/3 wire semantics, REST vs gRPC unary, connection reuse and
  multiplexing, LB/proxy idle timeouts, gRPC deadlines, and when sync RPC
  is the wrong style.
tags: [research, system-design-patterns, A1, request-response, rest, grpc]
---

# Request–response (REST / gRPC sync) — external research (2026-09-13)

> **What this is.** The evidence pass for catalog id **A1** (Group A — Communication). The Concept (not written here) should stay readable; this note keeps fetched facts, defaults, and URLs. Everything below is paraphrase; numbers and identifiers are reproduced exactly. Items that could not be verified are in §8 and are **not** asserted as fact.
>
> **Method.** Primary pages fetched 2026-09-13: RFC 9110 / 9112 / 9113 / 9114 (rfc-editor.org `.txt`); gRPC status, deadlines, core concepts, error handling, and `PROTOCOL-HTTP2.md`; Envoy latest timeout FAQ + `protocol.proto` (docs banner `1.40.0-dev`); NGINX `ngx_http_core_module`, `ngx_http_proxy_module`, `ngx_http_upstream_module`, `ngx_http_v2_module`; AWS ALB attributes, listeners, target groups; HAProxy 3.0 configuration manual; Chromium `client_socket_pool_manager.cc` HEAD. Existing workspace note [rest-rpc-dataflow.md](../../../cases/data-intensive-design/rest-rpc-dataflow.md) (main repo) is linked, not re-derived.

---

## 1. Scope and non-goals

**Owns.** Synchronous request–response as a *style of exchange*: one caller, one callee, one reply (or a classified failure) that the caller waits for. That includes REST over HTTP (any version) and **gRPC unary** RPCs. Wire semantics, connection lifecycle, keep-alive and multiplexing, scaling / fan-out limits, reconnect after GOAWAY / idle close / RST, proxy and load-balancer timeout interactions, verified protocol and proxy defaults, and when this style is the wrong one.

**Does not own.**

| Sibling | What stays there |
|---|---|
| **A2** | Pub/sub, queues, streams, competing consumers, async fan-out |
| **A3** | WebSocket lifecycle, heartbeats, sticky sessions |
| **A4** | SSE reconnect, `Last-Event-ID`, proxy buffering vs long-poll |
| **A5** | Webhooks / callbacks, signing, receiver retries |
| **A6** | API contracts and versioning (OpenAPI / protobuf / GraphQL evolution) |
| **C5** | Load-balancing *algorithms* (least-conn, Maglev, consistent hash) |
| **C6** | API gateway / BFF product patterns |
| **C7** | Timeout *policy* and deadline-propagation playbooks |
| **C9** | Idempotency keys and dedup stores |
| **E5** | Client–server as an architectural *style* (quanta, migration) |

Existing [REST, RPC, and service dataflow](../../../cases/data-intensive-design/rest-rpc-dataflow.md) already covers location-transparency fallacies, IDL choice (OpenAPI vs protobuf), discovery/LB/mesh *placement*, and request/response compatibility when servers upgrade first. This note does not repeat that argument; it supplies the wire and proxy facts the Concept will need.

---

## 2. Lineage / vocabulary

**RPC (1984).** Birrell & Nelson, *Implementing Remote Procedure Calls* (ACM TOCS 2(1), Feb 1984) — the original “make a network call look like a local procedure.” Cited as [38] in [encoding-references.md](../../../cases/data-intensive-design/encoding-references.md).

**Location transparency is the bug, not the feature (1994).** Waldo, Wyant, Wollrath, Kendall, *A Note on Distributed Computing* (Sun SMLI TR-94-29, Nov 1994) [39]: latency, memory access, partial failure, and concurrency are *qualitatively* different on a network. Vinoski, *Convenience over Correctness* (IEEE Internet Computing, Jul 2008) [40] restates the same for modern RPC stacks.

**REST (2000 / 2008).** Fielding’s dissertation (UC Irvine, 2000) [31] defines REST as an architectural style over HTTP’s existing verbs, URIs, and representations — not “JSON over POST.” Fielding, *REST APIs Must Be Hypertext-Driven* (2008-10) [32] rejects RPC-shaped “REST” that ignores hypermedia. The workspace note’s takeaway stands: REST treats state transfer as a different thing from a function call.

**HTTP semantics vs mapping (2022-06).** The June 2022 rewrite split the old RFC 7230–7235 / 7540 stack:

| RFC | Role | Supersedes |
|---|---|---|
| **9110** (STD 97) | HTTP *semantics*: methods, status codes, safe/idempotent, `Retry-After`, 408, 421 | RFC 7230–7235 semantics |
| **9112** | HTTP/1.1 *messaging*: persistent connections, pipelining, `Connection: close` | RFC 7230 messaging |
| **9113** | HTTP/2 mapping: streams, SETTINGS, GOAWAY, connection reuse | RFC 7540 |
| **9114** | HTTP/3 mapping onto QUIC | (new) |

Fetched as `rfc-editor.org/rfc/rfc911{0,3,4}.txt` and datatracker RFC 9112 on 2026-09-13.

**gRPC unary (living spec).** [gRPC core concepts](https://grpc.io/docs/what-is-grpc/core-concepts/) (fetched 2026-09-13): four method kinds; **unary** is “the client sends a single request to the server and gets a single response back, just like a normal function call.” Transport is HTTP/2 (and, in some stacks, HTTP/3 — not fetched as a separate protocol doc). Status is a `(code, message)` pair, **not** the HTTP status line. `PROTOCOL-HTTP2.md` on `grpc/grpc` master (fetched 2026-09-13) is the wire mapping.

**Vocabulary used below.**

- **Exchange:** one request message + one response message (REST) or one unary RPC (gRPC). Streaming RPCs are out of A1 except where they share the connection.
- **Connection:** TCP (HTTP/1.1, HTTP/2) or QUIC (HTTP/3).
- **Stream:** HTTP/2 / HTTP/3 request–response pair multiplexed on one connection. HTTP/1.1 has no streams; Envoy maps each HTTP/1.1 request onto an internal stream for timeout purposes.
- **Deadline:** an absolute time; **timeout:** a duration. gRPC converts a deadline to a remaining `grpc-timeout` on the wire so clock skew does not accumulate (deadlines guide).
- **Idle timeout:** no *application* activity. Distinct from TCP keepalive and from HTTP/2 PING.

---

## 3. Mechanics (Group A depth bar)

### 3.1 Wire semantics

**HTTP is stateless at the message layer** (RFC 9110 §3.3): each request’s semantics are understandable in isolation; connection reuse must not change interpretation. Correlation of request to response is version-dependent: HTTP/1.1 uses implicit order on the connection; HTTP/2 and HTTP/3 use an explicit stream identifier (RFC 9110 §7.5).

**Safe vs idempotent (RFC 9110 §9.2).** Safe: GET, HEAD, OPTIONS, TRACE — the client does not request a state change. Idempotent: PUT, DELETE, and all safe methods — *N* identical requests have the same *intended* effect as one. POST and PATCH are neither. A client **SHOULD NOT** automatically retry a non-idempotent method unless it has another way to know the semantics are actually idempotent (C9). A **proxy MUST NOT** automatically retry non-idempotent requests. Trade-off: treating POST as retryable buys availability and loses exactly-once; the RFC explicitly calls out the “idle persistent connection closed before any response” guess as the riskier path.

**HTTP/1.1 (RFC 9112 §9.3).** Persistent connections are the default. A client that does not support them must send `Connection: close` on every request; a server that does not must send `Connection: close` on every non-1xx response. One in-flight request per connection unless **pipelining** is used: a client MAY send several requests without waiting; the server MUST respond in order. Pipelining is still in the spec; browsers do not use it (head-of-line blocking plus decades of broken intermediaries). Practical HTTP/1.1 request–response is therefore **stop-and-wait per connection**.

**HTTP/2 (RFC 9113).** Binary framing, HPACK, concurrent streams on one TCP connection. Client-initiated streams are odd-numbered; stream 0 is connection control. `SETTINGS_MAX_CONCURRENT_STREAMS` is directional; the **initial value is unlimited**; the RFC *recommends* no smaller than 100 so parallelism is not needlessly capped. Initial flow-control window `SETTINGS_INITIAL_WINDOW_SIZE` = 65,535 octets; `SETTINGS_MAX_FRAME_SIZE` initial = 16,384. HTTP/2 removes *HTTP-layer* HOL blocking; **TCP HOL remains** (RFC 9113 intro): a lost packet stalls every multiplexed stream on that connection. Trade-off vs HTTP/1.1: far fewer sockets and better header compression, at the cost of coupling all streams to one congestion window and one loss recovery.

**HTTP/3 (RFC 9114).** HTTP semantics over QUIC. Each request–response pair consumes one QUIC stream; QUIC provides per-stream loss recovery, so a lost packet does not stall sibling streams. SETTINGS still exist (first frame after the handshake). Connection close: each QUIC endpoint declares an **idle timeout during the handshake**; if no packets arrive for that duration the peer assumes the connection is gone (RFC 9114 §5.1, pointing at RFC 9000 §10.1). Clients SHOULD open a new connection if the existing one is approaching that idle timeout. Servers SHOULD NOT actively keep connections open. Trade-off vs HTTP/2: no TCP HOL, connection migration, 0-RTT — at the cost of UDP-path middlebox hostility, a new congestion controller, and a negotiated idle timeout that application PINGs cannot always extend the way operators expect.

**REST sync.** A REST exchange is one HTTP method + target URI + optional body, one status + representation. Caching is a first-class semantic (GET/HEAD; RFC 9110 §9.2.3 notes POST is theoretically cacheable and almost never is). Content negotiation, `Retry-After` on 503 / 3xx (RFC 9110 §10.2.3), and 408 when the server did not receive a complete request in time (§15.5.9) are HTTP features, not application conventions.

**gRPC unary.** Always `:method POST`, `:path /Service/Method`, `content-type` beginning `application/grpc` (`+proto` / `+json` / custom), required `te: trailers`. If `content-type` does not begin `application/grpc`, servers SHOULD answer HTTP 415 so ordinary HTTP/2 clients do not treat an HTTP 200 + `grpc-status` trailer as success (`PROTOCOL-HTTP2.md`). The application status lives in trailers: `grpc-status` (decimal, no leading zeros) and optional `grpc-message` (percent-encoded UTF-8). HTTP `:status` on a well-formed RPC is **200** even when `grpc-status` is non-OK. A **Trailers-Only** response (headers + trailers, no DATA) is legal for immediate errors. Length-prefixed messages: 1-byte compressed flag + 4-byte big-endian length + payload; DATA frame boundaries are **not** message boundaries. Suggested header-size default: 8 KiB computed like `SETTINGS_MAX_HEADER_LIST_SIZE`. gRPC calls are **not assumed idempotent** unless marked: unstarted calls may be retried; there is no duplicate-suppression mechanism in the protocol.

**gRPC status codes** ([status-codes guide](https://grpc.io/docs/guides/status-codes/), fetched 2026-09-13). Codes 0–16. Library-generated on client or server: CANCELLED, UNKNOWN, DEADLINE_EXCEEDED, PERMISSION_DENIED, RESOURCE_EXHAUSTED, UNIMPLEMENTED, INTERNAL, UNAVAILABLE, UNAUTHENTICATED (and OK). **Never generated by the library, only by user code:** INVALID_ARGUMENT, NOT_FOUND, ALREADY_EXISTS, FAILED_PRECONDITION, ABORTED, OUT_OF_RANGE, DATA_LOSS. Decision rule for 9 / 10 / 14: UNAVAILABLE if the client can retry just this call; ABORTED if the client should retry a higher-level sequence; FAILED_PRECONDITION if the client must not retry until state is fixed. UNAVAILABLE “is most likely a transient condition, which can be corrected by retrying with a backoff. Note that it is not always safe to retry non-idempotent operations.” DEADLINE_EXCEEDED “may be returned even if the operation has completed successfully” (the response arrived after the deadline). [Error handling](https://grpc.io/docs/guides/error/): no data transmitted before deadline → DEADLINE_EXCEEDED; some data (e.g. request metadata written) then connection break → UNAVAILABLE. RST_STREAM mapping (`PROTOCOL-HTTP2.md`): REFUSED_STREAM → UNAVAILABLE (retry, possibly elsewhere); CANCEL from server → CANCELLED; ENHANCE_YOUR_CALM → RESOURCE_EXHAUSTED; INADEQUATE_SECURITY → PERMISSION_DENIED; most other RST codes → INTERNAL.

### 3.2 Connection lifecycle

```
HTTP/1.1:  TCP(+TLS) → request → response → idle until close or next request
HTTP/2:    TCP(+TLS) → SETTINGS both ways → N concurrent streams → GOAWAY → drain → TCP close
HTTP/3:    QUIC/TLS1.3 → SETTINGS → N QUIC streams → GOAWAY → idle-timeout or CONNECTION_CLOSE
gRPC:      channel (HTTP/2 session) → unary stream (HEADERS + DATA + trailers) → stream ends; channel reused
```

**HTTP/2 persistence (RFC 9113 §9.1).** Connections are persistent. Clients SHOULD NOT open more than one HTTP/2 connection to a given host+port (unless replacing a connection near stream-id exhaustion, refreshing TLS keys, recovering from a connection error, or using a different SNI / client cert). Servers are encouraged to keep connections open as long as possible but MAY close idle ones. The closer SHOULD send GOAWAY first. Stream identifiers cannot be reused; exhausting the 31-bit space forces a new connection.

**HTTP/2 connection reuse / coalescing (RFC 9113 §9.1.1).** A connection MAY carry requests for **multiple URI authorities** if the server is authoritative. For cleartext TCP, that means the host resolved to the same IP. For `https`, the certificate MUST also be valid for the new host (SAN / wildcard). RFC 9110 §4.3.4 adds the practical client check: DNS for the new origin contains the connection’s IP, unless the server sends an ORIGIN frame (RFC 8336). **The failure mode the RFC names:** TLS is terminated on a middlebox that routes by SNI; the client then sends a coalesced `:authority` the backend is not configured for. The server answers **421 Misdirected Request** (RFC 9110 §15.5.20). The client MAY retry on a *different* connection, **whether or not the method is idempotent**. A proxy MUST NOT generate 421. Trade-off: coalescing cuts handshakes and sockets; it also pins many origins to one VIP and one certificate, and it breaks SNI-based routing unless every coalesced name is configured on that listener (Envoy issue #6767 is the mesh-shaped instance of the same bug).

**gRPC gateway / lame-duck.** Server GOAWAY includes the last accepted stream id. Clients MUST treat later streams as UNAVAILABLE and retry elsewhere; already-accepted streams run to completion (`PROTOCOL-HTTP2.md` Connection Management). PING: peer must echo. If a **server-initiated** PING times out, the server closes outstanding calls with CANCELLED; if a **client-initiated** PING times out, the client closes all calls with UNAVAILABLE. Detectable client connection failure → all calls UNAVAILABLE; server-side → open calls CANCELLED. Cancellation is not a rollback.

**ALB client keepalive vs idle.** Two different clocks (attributes page, fetched 2026-09-13). **Connection idle timeout** (default 60 s, range 1–4000): no bytes in either direction. HTTP/2 PING does **not** reset it. **HTTP client keepalive duration** (default 3600 s, range 60–604800): max age of the client HTTP connection from *establishment*; it does not reset on traffic. At expiry ALB accepts one more request then closes: `Connection: close` on HTTP/1.x, GOAWAY on HTTP/2. AWS recommends the *application’s* idle timeout be **larger** than the ALB’s, otherwise the target can close first and ALB returns **502** on the next request. Trade-off: a short keepalive (used with zonal shift) drains impaired AZs faster; a long one saves handshakes and holds clients on a dying AZ.

### 3.3 Scaling limits and fan-out

**HTTP/1.1 browser pool.** Chromium HEAD `net/socket/client_socket_pool_manager.cc` (fetched 2026-09-13): `g_max_sockets_per_group` = **6** for the normal pool (“Default to allow up to 6 connections per host”; crbug.com/12066), **255** for WebSockets; process-wide soft cap **256**; unused-idle socket timeout **60 s**. A seventh concurrent HTTP/1.1 request to the same host queues. HTTP/2 collapses that to one connection (RFC 9113 §9.1 SHOULD NOT open more than one), so the 6-slot limit is not the fan-out bound — `SETTINGS_MAX_CONCURRENT_STREAMS` is.

**Documented stream caps (not RFC minima).**

| Product (fetched 2026-09-13) | Concurrent streams default |
|---|---|
| RFC 9113 | unlimited initially; recommend ≥ 100 |
| NGINX `http2_max_concurrent_streams` | **128** (`http`/`server`) |
| AWS ALB HTTPS listener | “up to **128** requests in parallel using one HTTP/2 connection”; server push not supported |
| AWS ALB target group `HTTP2` | “maximum number of streams per client HTTP/2 connection is **128**” |
| Envoy `Http2ProtocolOptions.max_concurrent_streams` | **1024** “for safety” (changed from 2,147,483,647 in **1.36.0, 2025-10-14**); range 1–2³¹−1 |

**gRPC / REST fan-out.** A unary or REST handler that itself issues *N* synchronous downstream calls holds the inbound stream/thread/deadline for `max(downstream_i)` plus local work. That is the amplification the workspace RPC note already flags as “retry is normal” and that C2/C7 own as policy. Sync request–response does **not** provide a broker, a retry budget, or a competing-consumer partition; *N* callers × *M* serial dependencies is *N·M* held connections. Trade-off: the programming model is a function call; the capacity model is Little’s law on the held resource (thread, stream, FD).

**HTTP/2 vs HTTP/1.1 at a proxy.** ALB: “Because HTTP/2 uses front-end connections more efficiently, you might notice fewer connections between clients and the load balancer.” The target-group default is still **HTTP/1.1**; HTTP/2 on the front does not imply HTTP/2 to the backend. Combination table (target-groups page): HTTP/2 client → HTTP/1.1 target works (ALB demuxes); HTTP/1.1 client → HTTP/2 target is an **error**; gRPC requires HTTPS listener + `GRPC` or `HTTP2` protocol version; HTTP/2 client → `GRPC` target succeeds only for POST.

**Upstream keep-alive is a cache, not a cap.** NGINX `keepalive` (upstream, since **1.29.7** default `32 local`): max *idle* connections cached **per worker**; it “does not limit the total number of connections to upstream servers.” Set it small enough that upstreams can still accept new connections.

### 3.4 Failure and reconnect

| Event | HTTP/1.1 | HTTP/2 / gRPC | HTTP/3 |
|---|---|---|---|
| Idle close | Peer sends FIN / `Connection: close`; next request needs a new TCP(+TLS) | Idle timeout → drain + GOAWAY (Envoy) or FIN; in-flight streams finish if the drain allows | QUIC idle timeout; client SHOULD reconnect before it fires |
| Graceful server stop | `Connection: close` on the next response | GOAWAY(last-stream-id); new streams UNAVAILABLE / retry elsewhere | GOAWAY with stream/push id; clients MAY open a new connection |
| Mid-request TCP reset | Request outcome unknown; retry only if idempotent (RFC 9110 §9.2.2) | Stream RST; gRPC maps REFUSED_STREAM → UNAVAILABLE (retry), others → INTERNAL / CANCELLED | QUIC RESET_STREAM / CONNECTION_CLOSE; same application uncertainty |
| Deadline first | Client gives up; server may still finish (orphaned work) | Client: DEADLINE_EXCEEDED; server auto-cancels the RPC (`CANCELLED`); app must poll cancellation and stop spawned work | Same deadline mapping if the stack is gRPC; raw HTTP/3 has no `grpc-timeout` |
| Coalesced wrong origin | N/A (one Host per connection typical) | 421; client MAY retry on a fresh connection even for POST | Same 421 rule (HTTP semantics) |
| 503 + `Retry-After` | Wait the indicated HTTP-date or delay-seconds (RFC 9110 §10.2.3) | Same header; gRPC apps usually see UNAVAILABLE instead unless a gateway mapped it | Same |

**gRPC deadlines vs HTTP timeouts** ([deadlines guide](https://grpc.io/docs/guides/deadlines/), fetched 2026-09-13). **Default: no deadline** — a client can wait forever. Always set one. Client past deadline → `DEADLINE_EXCEEDED`. Server whose client deadline has passed → call cancelled (`CANCELLED`); the **application** must stop work it spawned. Propagation: some languages (Java, Go) do it by default; C++ must enable it. The wire form is a **remaining duration** (`grpc-timeout` = ≤8 digit ASCII + unit `H|M|S|m|u|n`); “If Timeout is omitted a server should assume an infinite timeout.” Example in the spec: `grpc-timeout = 1S`. Trade-off vs a single HTTP client timeout: a deadline is an instant that shrinks as it hops (0.5 s already spent → 1.5 s forwarded on a 2 s budget), so a 15 s Envoy route timeout and a 2 s gRPC deadline are *different clocks* — the tighter one wins, and the looser one hides nothing.

**HTTP timeouts are hop-local.** A browser, a sidecar, and a route each have their own timer. They do not propagate unless something copies them (gRPC `grpc-timeout`, Envoy `MaxStreamDuration` “fixed time offset on grpc-timeout headers”, custom headers). C7 owns the policy; A1 owns the fact that REST-over-HTTP has **no standard remaining-budget header**.

**Reconnect is not session resume.** HTTP request–response has no session to resume (A3/A4 do). After GOAWAY or idle close the client opens a new connection and retries only what RFC 9110 / gRPC retry rules allow. gRPC channel state (`connected` / `idle`) is language-dependent; closing a channel is language-dependent (core concepts).

### 3.5 Proxy / LB interactions

**Timeout mismatch is the production bug.** The dangerous pattern: client timeout *T*, proxy idle/route timeout *t < T*, backend work in *(t, T]*. The proxy cuts the stream; the client retries (C2); the backend still finishes the first attempt (C9). Invert it (*t > T*) and the proxy holds a connection the client has already abandoned.

**Envoy (latest docs, banner `1.40.0-dev`, fetched 2026-09-13).**

| Knob | Default | Notes |
|---|---|---|
| HTTP protocol `idle_timeout` | **1 hour** | No active requests/streams at the HTTP layer. Independent of TCP keepalive. HTTP/2 PING does **not** keep it alive. HTTP/2 downstream: start drain (`drain_timeout`). Set 0 to disable (leak warning). |
| `max_connection_duration` | **0 (unlimited)** | Age from connect; then drain. Optional jitter to avoid reconnect stampede. |
| HCM `drain_timeout` | **5 s** | Time between first HTTP/2 GOAWAY and final GOAWAY. New streams still accepted in the grace window. Never force-kills active streams. |
| HCM `stream_idle_timeout` | **5 minutes** | No upstream/downstream activity on that stream. Recommended for *all* requests, not only streaming. Route `idle_timeout` overrides. |
| HCM `request_timeout` | **disabled** | Whole request stream from the client; incompatible with never-ending streams. |
| HCM `request_headers_timeout` | **disabled** | Headers-only wait. |
| Route `timeout` | **15 seconds** | Wait for a *complete* upstream response **after** the downstream request is fully received. Disable (0) for streaming. Does not start on a streaming request. |
| Cluster `connect_timeout` | **5 seconds** | Includes upstream TLS handshake. |
| TCP proxy `idle_timeout` | **1 hour** | |
| TCP pool `idle_timeout` | **10 minutes** | Upstream connection not associated with a downstream. |
| H2 `max_concurrent_streams` | **1024** (since 1.36.0) | Was 2³¹−1. H2 initial stream window default now **16 MiB** (was 256 MiB); connection window **24 MiB** (was 256 MiB). Revert guard: `envoy.reloadable_features.safe_http2_options`. |

**NGINX (nginx.org module docs, fetched 2026-09-13).**

| Directive | Default | Notes |
|---|---|---|
| `keepalive_timeout` (core) | **75 s** | Idle client keep-alive. 0 disables. Optional second arg writes `Keep-Alive: timeout=`. Docs: MSIE closes on its own in ~60 s. |
| `keepalive_requests` | **1000** (was **100** before 1.19.10) | Then close. |
| `keepalive_time` | **1 h** (since 1.19.10) | Max lifetime; close after the next request. |
| `client_header_timeout` / `client_body_timeout` / `send_timeout` | **60 s** | |
| `proxy_connect_timeout` / `proxy_read_timeout` / `proxy_send_timeout` | **60 s** | Read/send timeouts are *between successive* I/O ops, **not** total response time. |
| `proxy_http_version` | **1.1** since **1.29.7** (was 1.0) | 1.1 or 2 required for upstream keepalive. |
| `upstream keepalive` | **32 local** since **1.29.7** | Idle cache per worker; `local` = not shared across locations. |
| `upstream keepalive_timeout` | **60 s** | Idle upstream keep-alive. |
| `http2_max_concurrent_streams` | **128** | Still documented; several neighbouring `http2_*` knobs obsolete since 1.19.7 / 1.25.1 in favour of `keepalive_*` / `large_client_header_buffers`. |
| `http2` | **off** | Per-server enable since 1.25.1. |

**AWS ALB (ELB Application User Guide, fetched 2026-09-13).** Idle **60 s** (1–4000); client keepalive **3600 s** (60–604800); desync mitigation default **defensive**; HTTP/2 only on HTTPS listeners; **128** parallel streams; no HTTP/2 PING credit; default target protocol **HTTP1**; gRPC needs HTTPS + `GRPC` protocol version, custom `/package.service/method` health check, no Lambda targets. Listener page lists HTTP and HTTPS only — **no HTTP/3 listener**. (NLB API lists QUIC / TCP_QUIC; full NLB QUIC idle defaults not fetched, §8.)

**HAProxy 3.0 configuration manual (docs.haproxy.org/3.0 and download/3.0 `configuration.txt`, fetched 2026-09-13).** Default connection mode is **keep-alive** (fits HTTP/2 and HTTP/3). `timeout client` / `timeout server` / `timeout connect`: **unspecified = infinite**, with a startup warning (“accumulation of expired sessions”). The manual’s own example uses `timeout connect 5000ms`, `timeout client 50000ms`, `timeout server 50000ms`. Those 5 s / 50 s figures are **example text, not compiled defaults**. `timeout client` is inactivity while the client should ack or send; for the request-read phase they recommend `timeout http-request` against Slowloris.

**Envoy coalescing / 421.** GitHub envoy#6767 (still the canonical write-up): browsers coalesce on wildcard certs + overlapping IPs; Envoy latches a connection to one listener/filter chain. Names that live on another chain get the first chain’s route table. Mitigations named there: send 421 for unknown authorities; advertise RFC 8336 ORIGIN (sparse client support — not re-verified, §8).

---

## 4. Verified defaults / standards

All rows fetched **2026-09-13**. Versions are what the page itself showed.

| Thing | Value | Version / page |
|---|---|---|
| RFC 9110 safe methods | GET, HEAD, OPTIONS, TRACE | RFC 9110 §9.2.1 (2022-06) |
| RFC 9110 idempotent methods | PUT, DELETE + safe | §9.2.2 |
| HTTP/1.1 persistence | on by default | RFC 9112 §9.3 |
| H2 `SETTINGS_MAX_CONCURRENT_STREAMS` initial | unlimited; recommend ≥ 100 | RFC 9113 §6.5.2 |
| H2 `SETTINGS_HEADER_TABLE_SIZE` initial | 4,096 | RFC 9113 §6.5.2 |
| H2 `SETTINGS_INITIAL_WINDOW_SIZE` initial | 65,535 | RFC 9113 §6.5.2 |
| H2 `SETTINGS_MAX_FRAME_SIZE` initial | 16,384 | RFC 9113 §6.5.2 |
| H2 `SETTINGS_MAX_HEADER_LIST_SIZE` initial | unlimited | RFC 9113 §6.5.2 |
| H2 connections per host+port | SHOULD NOT > 1 | RFC 9113 §9.1 |
| gRPC default deadline | **none (infinite)** | grpc.io/docs/guides/deadlines |
| gRPC `grpc-timeout` omitted | server assumes infinite | PROTOCOL-HTTP2.md |
| gRPC suggested max request headers | 8 KiB | PROTOCOL-HTTP2.md |
| gRPC unary HTTP method | POST | PROTOCOL-HTTP2.md |
| gRPC status on success path | HTTP 200 + trailer `grpc-status` | PROTOCOL-HTTP2.md |
| Chromium HTTP/1.1 sockets per host | **6** | chromium HEAD `client_socket_pool_manager.cc` |
| Chromium unused idle socket | **60 s** | same |
| Envoy HTTP idle | **1 h** | envoy latest timeout FAQ |
| Envoy stream idle | **5 min** | same |
| Envoy route timeout | **15 s** | same |
| Envoy connect | **5 s** | same |
| Envoy drain | **5 s** | same |
| Envoy H2 max streams | **1024** | protocol.proto latest; 1.36.0 (2025-10-14) changelog |
| NGINX client `keepalive_timeout` | **75 s** | ngx_http_core_module |
| NGINX `keepalive_requests` | **1000** | same; was 100 before 1.19.10 |
| NGINX proxy read/send/connect | **60 s** | ngx_http_proxy_module |
| NGINX H2 max streams | **128** | ngx_http_v2_module |
| NGINX upstream keepalive | **32 local** since 1.29.7 | ngx_http_upstream_module |
| ALB idle | **60 s** (1–4000) | edit-load-balancer-attributes |
| ALB client keepalive | **3600 s** (60–604800) | same |
| ALB H2 parallelism | **128** | load-balancer-listeners / target-groups |
| ALB target protocol default | **HTTP1** | target-groups |
| HAProxy unset timeouts | **infinite** + warning | HAProxy 3.0 manual |

**gRPC retry (protocol, not C2 policy).** `PROTOCOL-HTTP2.md` “Idempotency and Retries”: calls are not assumed idempotent; only calls that cannot be proven to have started, or that are marked idempotent, may be sent more than once. Application retry-code choice is explicitly *not* a fixed list ([statuscodes.md](https://github.com/grpc/grpc/blob/master/doc/statuscodes.md)): the library can emit the same code for different causes.

---

## 5. Failure modes and when-not-to-use

**Failure modes of the style itself**

1. **Unknown outcome on timeout.** RFC 9110 and gRPC both state it: DEADLINE_EXCEEDED / a closed connection can happen *after* the server applied the write. Retry without C9 duplicates work. Trade-off of “fail fast”: you free the caller and you create orphans.
2. **Timeout sandwich.** Client 30 s, Envoy route 15 s, NGINX `proxy_read_timeout` 60 s (between reads!), ALB idle 60 s, gRPC deadline unset (infinite). The first timer that fires is the truth; the others only add 502/504/UNAVAILABLE noise. `proxy_read_timeout` is especially misleading: a backend that dribbles bytes every 59 s never hits 60 s and can run for minutes.
3. **HTTP/2 HOL / one-bad-stream.** One stalled window or one lossy TCP connection delays every multiplexed RPC on that channel. HTTP/3 fixes TCP HOL; it does not fix a server that stops reading.
4. **Coalescing → wrong backend.** Wildcard cert + shared VIP + SNI-selected filter chain. Symptom: 421, or worse, 200 from the *other* app. 421 is retryable even for POST (RFC 9110) — another duplicate-risk if the first hop did apply the request.
5. **Idle-close race.** ALB 60 s vs app 60 s; NGINX 75 s vs Chromium 60 s unused-idle; Envoy 1 h vs ALB 60 s in front of it. The shorter closer wins; the longer one sees a half-closed socket and 502s. HTTP/2 PING will not save you on ALB or Envoy HTTP idle.
6. **Status-code split brain.** REST clients key off HTTP 4xx/5xx. gRPC clients key off trailers. A proxy that only sees `:status 200` will not trip outlier detection on `grpc-status: 14` unless it understands gRPC (Envoy does map some codes; that mapping lives with C1/C5). Trailers-only errors are easy to drop on HTTP/1.1 hop-by-hop conversions (`te: trailers` is how gRPC detects incompatible proxies).
7. **Sync fan-out amplification.** One inbound exchange × *N* outbound unary calls × retries (C2) × no deadline (this section) = thread/stream exhaustion. This is the case that should have been A2 or a workflow, not A1.

**When not to use synchronous request–response**

| Situation | Why A1 is wrong | Go to |
|---|---|---|
| Caller should not wait (minutes of work, human-time batch, report generation) | Every hop’s idle/route timeout will lie; you hold a connection for business time | **A2** (queue + worker), durable workflow |
| Many independent consumers need the same event | Sync fan-out is *N* RPCs and *N* failure domains | **A2** |
| Server wants to push after the caller has gone | No connection left; polling is a bad A1 | **A5** webhooks, **A4** SSE, **A3** WebSocket |
| Interactive bidirectional stream (editor, game, agent tool loop) | Unary/REST is one shot; streaming gRPC is not A1 either | **A3**, or gRPC bidi (out of A1) |
| Client is a browser tab that must stay updated | Request–response requires polling; proxies buffer or time out long polls | **A4** (one-way) or **A3** (two-way) |
| Cross-org “fire and forget” integration | You cannot keep their HTTP request open; they cannot keep yours | **A5** |
| Work is naturally idempotent *and* delayed | The useful contract is “deliver at least once with a key”, not “wait for 200” | **A2** + **C9** |
| You only needed a function call in-process | Network RPC is not a local call ([rest-rpc-dataflow.md](../../../cases/data-intensive-design/rest-rpc-dataflow.md)) | in-process, or E5 if you truly want a network boundary |

**When A1 is the right default.** Ask/answer fits in a budget you can write down (and that budget is tighter than every proxy on the path). The callee’s effect is small enough to bound. The caller needs the result to continue. GET-shaped reads want HTTP cache semantics REST already has. Public APIs and browsers speak HTTP; gRPC unary is the internal analogue when you own both stubs and want deadlines + trailer status. Trade-off vs A2: simpler ops, harder tail latency; vs A3/A4: no heartbeat tax, no sticky-session tax, no half-open connection inventory.

---

## 6. Cross-links

- Existing note (do not rewrite): [REST, RPC, and service dataflow](../../../cases/data-intensive-design/rest-rpc-dataflow.md) · citations [31]–[44] in [encoding-references.md](../../../cases/data-intensive-design/encoding-references.md).
- **A2** pub/sub, queues, streams — async fan-out and long work.
- **A3** WebSocket — upgraded HTTP/1.1 connection; ALB documents native `ws`/`wss` upgrade on the same idle-timeout knobs.
- **A4** SSE — long-lived HTTP response; disable Envoy route timeout (default 15 s) and NGINX-style successive-read timeouts.
- **A5** webhooks — inverted request–response; receiver must be the idempotent one (C9).
- **A6** contracts — OpenAPI vs protobuf, URL vs `Accept` versioning (workspace note already).
- **C5** load balancing — algorithms and panic/ejection; this note only covers how H2 coalescing and keepalive pools change what the balancer *sees*.
- **C6** API gateway — product placement; this note only covers hop timeouts and gRPC-awareness.
- **C7** timeouts & deadline propagation — policy; this note only records that REST has no standard remaining-budget header and gRPC does (`grpc-timeout`).
- **C9** idempotency — required before retrying POST or unmarked gRPC.
- **E5** client–server style — one quantum vs many; A1 is the usual *exchange* inside that style.
- Resilience already in-tree: [CircuitBreaker](../../../cases/SystemDesignPatterns/CircuitBreaker.md) (what to count: 502/503/504, gRPC UNAVAILABLE / DEADLINE_EXCEEDED) · [RetryBackoff](../../../cases/SystemDesignPatterns/RetryBackoff.md).

---

## 7. Sources

Retrieved **2026-09-13**.

**RFCs.** rfc-editor.org/rfc/rfc9110.txt (HTTP Semantics, June 2022) · datatracker.ietf.org/doc/html/rfc9112 (HTTP/1.1) · rfc-editor.org/rfc/rfc9113.txt (HTTP/2) · rfc-editor.org/rfc/rfc9114.txt (HTTP/3) · RFC 8336 (ORIGIN frame; cited by 9110, not re-fetched as a full read) · RFC 9000 §10.1 (QUIC idle timeout; cited by 9114).

**REST / RPC lineage (already in-tree).** Fielding 2000 dissertation [31] · Fielding 2008 [32] · Birrell & Nelson 1984 [38] · Waldo et al. 1994 [39] · Vinoski 2008 [40] · [rest-rpc-dataflow.md](../../../cases/data-intensive-design/rest-rpc-dataflow.md) · [encoding-references.md](../../../cases/data-intensive-design/encoding-references.md).

**gRPC.** grpc.io/docs/what-is-grpc/core-concepts/ · grpc.io/docs/guides/status-codes/ · grpc.io/docs/guides/deadlines/ · grpc.io/docs/guides/error/ · github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md (raw, master) · github.com/grpc/grpc/blob/master/doc/statuscodes.md.

**Envoy.** envoyproxy.io/docs/envoy/latest/faq/configuration/timeouts (banner `1.40.0-dev-1dc43a`) · envoyproxy.io/docs/envoy/latest/api-v3/config/core/v3/protocol.proto (`idle_timeout` 1 h; H2 `max_concurrent_streams` 1024) · envoyproxy.io/docs/envoy/latest/version_history/v1.36/v1.36.0 (2025-10-14: streams 2³¹−1 → 1024; windows 256 MiB → 16 / 24 MiB) · github.com/envoyproxy/envoy/issues/6767 (H2 coalescing / 421).

**NGINX.** nginx.org/en/docs/http/ngx_http_core_module.html · nginx.org/en/docs/http/ngx_http_proxy_module.html · nginx.org/en/docs/http/ngx_http_upstream_module.html · nginx.org/en/docs/http/ngx_http_v2_module.html.

**AWS ALB.** docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html · …/load-balancer-listeners.html · …/load-balancer-target-groups.html · docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_LoadBalancerAttribute.html · API_CreateTargetGroup.html (ProtocolVersion default `HTTP1`; NLB QUIC/TCP_QUIC listed).

**HAProxy.** docs.haproxy.org/3.0/configuration.html (3.0.26 banner) · haproxy.org/download/3.0/doc/configuration.txt (`timeout client` infinite-if-unset; example 5 s / 50 s / 50 s).

**Clients.** chromium.googlesource.com/chromium/src/+/HEAD/net/socket/client_socket_pool_manager.cc (`g_max_sockets_per_group` 6 / 255; unused idle 60 s).

**Secondary (coalescing narrative, not used for numbers).** daniel.haxx.se/blog/2016/08/18/http2-connection-coalescing/ (Haxx on RFC 7540 §9.1.1, term “coalescing”).

---

## 8. Uncertain / left out

- RFC HTML fetches (`rfc-editor.org/rfc/rfc9110.html` etc.) returned HTTP 409 in this session; text editions were used. Section numbers were checked against those `.txt` files.
- Exact calendar day of the June 2022 RFC 9110–9114 series (month+year only).
- Whether a numbered **Envoy 1.40.0** exists; pages said `1.40.0-dev`. 1.36.0 date 2025-10-14 is from the version-history page.
- Current NGINX *stable/mainline version number* on 2026-09-13 (module docs are unversioned; version gates 1.19.7 / 1.19.10 / 1.25.1 / 1.29.7 are from those pages).
- HAProxy 3.0.26 patch date; 3.0 is the series fetched.
- NLB **QUIC / TCP_QUIC** idle-timeout defaults and whether they terminate HTTP/3 (API lists the listener protocols; user-guide page not fully fetched). ALB-has-no-HTTP/3-listener is from the ALB listener page.
- Browser-advertised HTTP/2 `SETTINGS_MAX_CONCURRENT_STREAMS` (Chrome / Firefox / Safari). Chromium’s **6** is the HTTP/1.1 *socket* pool, not the H2 stream cap.
- Firefox / Safari HTTP/1.1 per-host limits (Chromium comment mentions Firefox **WebSocket** 200 only).
- gRPC-Go / gRPC-Java / grpc-core **keepalive** defaults (`keepalive_time`, `keepalive_timeout`, `permit_without_calls`) and channel reconnect backoff. Not fetched; do not invent.
- Language-specific gRPC default deadlines other than the published “none.” Some language APIs “may or may not have a default deadline” (core concepts) — no numbers fetched.
- RFC 8336 ORIGIN-frame client support matrix (Envoy #6767 claims “a few clients”; not re-surveyed).
- HTTP/3 0-RTT replay / anti-replay operational guidance (RFC 9001); out of scope unless a later pass.
- CloudFront / GCP URL map / Azure App Gateway idle defaults (not in the fetch list).
- Istio `DestinationRule` `idleTimeout` default (often inherited from Envoy 1 h — not independently fetched).
- Whether ALB coalesces wildcard-SAN names the way browsers do (not stated on the ALB pages fetched).
- Java `HttpClient`, Go `http.Transport`, and .NET `SocketsHttpHandler` idle-timeout defaults.
- gRPC-over-HTTP/3 specification status per language (core concepts still describe HTTP/2 framing).
- PromQL / SLO recipes — out of scope (Group D).
