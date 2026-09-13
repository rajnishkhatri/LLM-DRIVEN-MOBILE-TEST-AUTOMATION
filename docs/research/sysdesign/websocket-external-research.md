---
type: research
title: 'WebSocket communication — external research (2026-09-13)'
description: >-
  Source-verified research backing the WebSocket Concept (A3): RFC 6455 wire
  mechanics (handshake, masking rationale, control frames, close codes),
  RFC 8441/9220 status and nginx's refusal, heartbeat numbers (socket.io
  25 s/20 s), scaling with pub/sub backplanes and verified managed-service
  quotas (API Gateway 10 min/2 h/32 KB/128 KB; Azure 1,000 conn/unit),
  bufferedAmount backpressure and permessage-deflate memory caveats, browser
  auth patterns incl. the Kubernetes subprotocol token, and when not to use it.
tags: [research, websocket, realtime, system-design-patterns]
---

# A3 WebSocket communication — external research (2026-09-13)

**Method.** Facts verified against primaries 2026-09-13; paraphrase; ≤ 1 short quote per source. **[→timeouts] [→lb]** cite forward to [timeouts-deadlines-external-research.md](timeouts-deadlines-external-research.md) and [load-balancing-external-research.md](load-balancing-external-research.md) (ALB idle 60 s + 502 rule; NGINX 60 s between-reads; TCP keepalive floor; connection pinning + MAX_CONNECTION_AGE jitter; L4 pinning).

## 1. RFC 6455 wire mechanics

- **Handshake**: HTTP/1.1 GET with Upgrade/Connection, `Sec-WebSocket-Key` (16 random bytes b64), version 13 → **101** + `Sec-WebSocket-Accept` = b64(SHA-1(key ∥ 258EAFA5-E914-47DA-95CA-C5AB0DC85B11)); the GUID round-trip proves a real WebSocket endpoint.
- **Opcodes**: 0x1 text (UTF-8), 0x2 binary, 0x8 Close, 0x9 Ping, 0xA Pong; lengths 7-bit / 16-bit (126) / 64-bit (127).
- **Masking**: client MUST mask every frame (fresh 32-bit XOR key); server MUST NOT; violations close the connection. §10.3 rationale: unmasked script-chosen bytes could impersonate HTTP to intermediaries (cache poisoning) — an infrastructure defense, not confidentiality.
- **Control frames**: ≤ **125 bytes**, never fragmented, may interleave within a fragmented message — that keeps heartbeats alive during large transfers. Pong echoes the Ping payload; unsolicited Pong = one-way heartbeat.
- **Close codes**: 1000 normal; 1001 going away; 1002 protocol error; 1008 policy; 1009 too big; 1011 internal error. **1005/1006/1015 MUST NOT be sent** — 1006 is the locally reported "died without a Close frame" code (what you see when an LB kills the TCP). 1012 Service Restart / 1013 Try Again Later are IANA-registered (hybi), not in 6455. 4000–4999 = private/application use.
- **Fragmentation**: FIN + continuation frames; two data messages may not interleave.

## 2. Over HTTP/2 and HTTP/3

- **RFC 8441**: server advertises SETTINGS_ENABLE_CONNECT_PROTOCOL; client sends Extended CONNECT with `:protocol: websocket`; success is **2xx not 101**; the socket rides one h2 stream (END_STREAM orderly, RST_STREAM abrupt). **RFC 9220**: same setting over h3; FIN orderly, H3_REQUEST_CANCELLED abrupt.
- **Support**: Chrome default since **M91** (secure sockets on an already-open h2 connection that advertised the setting; else fresh h1 handshake). Firefox landed in 65, currently default-on (`network.http.http2.websockets: true`). **nginx does not implement RFC 8441** (ticket #1992 open; Dounin 2020: translating extended CONNECT to Upgrade "doesn't look like a good solution"). Behind nginx, browser sockets run h1 — one TCP connection per socket.

## 3. Keepalive and dead-connection detection

- The app layer must heartbeat: TCP alone detects a dead idle peer in ≈ 2 h 11 m at best, unacked writes hang 13–30 min **[→timeouts]**. RFC 6455 provides Ping/Pong, mandates no interval.
- **socket.io v4**: server ping every **25 000 ms**, dead if no pong in **20 000 ms** (client symmetric at 45 s); history 60 s → 5 s → 20 s shows the too-small/too-large trade. `maxHttpBufferSize` 1 MB/message.
- **NGINX**: tunnel closes on 60 s of upstream silence (`proxy_read_timeout`) — its own docs suggest raising it or sending Pings; the timer watches the *upstream* direction. **ALB**: 60 s idle applies **[→timeouts]**. Hence the de-facto **20–30 s** heartbeat: under the near-universal 60 s idle default. Detection latency ≈ interval + timeout; heartbeat cost scales with connection count (25 s × 1 M conns = 40 k frames/s).

## 4. Scaling and fan-out

- **Stickiness is only needed for multi-request session state**: socket.io requires it for HTTP long-polling (multiple requests must hit the session's node) but "no longer required" for WebSocket-only transport — the connection itself is sticky at L4 **[→lb]**. What needs engineering is the **broadcast path** to sockets on other nodes.
- **Pub/sub backplane** (socket.io Redis adapter): local delivery + publish to Redis; every node forwards to its own room members; sharded adapter for Redis 7 cluster. Reference shape: connection registry local, routing global.
- Post-deploy rebalancing carries over: age connections out (server closes 1001/1012; clients reconnect with jittered backoff) **[→lb]**.
- **Verified capacity numbers**: AWS API Gateway WebSocket — new connections **500/s per account/Region** (increasable), no enforced concurrent cap (worked example: 3.6 M concurrent at 500/s for 2 h). Azure Web PubSub / SignalR: **1,000 concurrent connections per unit** (Standard/Premium; Free 20), up to 100+ units — "a unit ≈ 1,000 sockets" is the Azure currency.

## 5. Managed services (API Gateway WebSocket)

- Routes `$connect` (auth here; Lambda authorizers), `$disconnect`, `$default`, custom via `routeSelectionExpression` on a JSON field.
- **Quotas (not increasable)**: idle timeout **10 min**; max connection duration **2 h**; frame **32 KB**; message **128 KB** (larger messages must arrive as ≤ 32 KB frames; violations close with **1009**). Closures map to registry codes: 1001 on idle/lifetime, 1008 throttling, 1012 restart — clients must expect 1001 every ≤ 2 h and reconnect; heartbeats defer the 10-min idle but nothing defers the 2-h cap.
- **Callback pattern**: connection terminates at the edge; backend pushes via the `@connections` management API (POST to send, GET status, DELETE force-disconnect; SigV4; `GoneException` for dead ids); $connect/$disconnect maintain your connection registry. Azure Web PubSub is the same shape.

## 6. Backpressure, size, compression

- **Browser**: `send()` never blocks; poll `bufferedAmount` (bytes queued, drains to 0) before producing more; no receive-side backpressure in the classic API. **WebSocketStream** (Streams-based, automatic backpressure) is MDN-flagged non-standard/experimental (Chromium only).
- **Node ws**: same bufferedAmount; `send()` callback = the server-side backpressure hook; `pause()`/`resume()` for receive relief; `maxPayload` default **100 MiB** — tune down.
- **permessage-deflate (RFC 7692)**: negotiated via Sec-WebSocket-Extensions; RSV1 marks compressed messages. Memory story = context takeover: each direction retains its LZ77 window per connection by default; `*_no_context_takeover` drops it (less memory, worse ratio); `*_max_window_bits` 2^8–2^15. **ws disables it by default** — "significant overhead in terms of performance and memory consumption"; Node zlib under concurrency can fragment memory catastrophically; `threshold` and `concurrencyLimit` contain it. Per-connection zlib × 100 k connections is the real memory budget.

## 7. Authentication

- The browser constructor takes only url + protocols — no headers (Heroku: "you cannot customize WebSocket headers from JavaScript"). Options:
1. **Cookies**: automatic — and attached to any origin's handshake = Cross-Site WebSocket Hijacking; OWASP: validate `Origin` against an allowlist (browsers only — non-browser clients forge it).
2. **Token in query string**: works, but logs leak it (OWASP: redact; prefer message-based).
3. **Ticket auth** (Heroku's reference flow): short-lived single-use ticket over HTTPS (user, IP, expiry), presented on connect; institutionalized by API Gateway's `$connect` authorizer.
4. **Token in the subprotocol** — the one header you can set: Kubernetes apiserver accepts `base64url.bearer.authorization.k8s.io.<b64url-token>` as a subprotocol (verified from source; client must offer one real subprotocol too, since the server must echo a selection).
- Always `wss://` (OWASP).

## 8. When NOT WebSocket

- Unidirectional push → SSE (A4 owns the comparison): auto-reconnect + Last-Event-ID, plain HTTP; the h1 6-connections-per-origin cap is the sharp edge (MDN; ~100 h2 streams).
- **Request-response over WS is an anti-pattern**: Ably — "WebSockets do not support caching", no status codes/acks out of the box; you reinvent correlation ids, timeouts, retries inside a schema invisible to proxies/CDNs/observability. Stable shape: REST for the transactional surface + one socket or SSE for push.

## Sources

RFC 6455 · IANA close-code registry · RFC 8441 · RFC 9220 · RFC 7692 · Chrome Platform Status (h2 WebSockets, M91) · Bugzilla 1434137 + Firefox StaticPrefList.yaml · nginx websocket page + trac #1992 · socket.io server-options / redis-adapter / using-multiple-nodes · AWS API GW websocket overview + websocket-limits + @connections docs · Azure subscription limits (Web PubSub/SignalR) · MDN bufferedAmount / WebSocketStream / SSE · WHATWG WebSockets Standard · ws README + doc/ws.md · kubernetes apiserver websocket protocol.go + PR #47740 · Heroku websocket-security · OWASP WebSocket cheat sheet · Ably websockets-vs-http. Cited forward: timeouts-deadlines-, load-balancing-external-research.md.

## Uncertain / could not verify (excluded from the Concept)

- RFC 9220 (h3) real-world deployment: asserted only as "specified, sparse".
- Safari RFC 8441 status: no signal verified.
- Firefox re-enable release after bug 1523978 not identified.
- OWASP phrasing summarizer-extracted.
- socket.io maxHttpBufferSize vs ws maxPayload interaction unverified.
- Azure Web PubSub max message size not in the fetched table.
- 1014 rarely implemented; registry fact only.
