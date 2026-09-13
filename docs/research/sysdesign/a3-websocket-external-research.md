---
type: research
title: 'WebSocket — external research (2026-09-13)'
description: >-
  Source-verified research for catalog A3: RFC 6455 handshake/frames/close
  codes, ping/pong heartbeats, HTTP/2 and HTTP/3 bootstrapping, scaling
  (sticky sessions, Redis pub/sub backplane), AWS API Gateway vs ALB vs NLB
  vs CloudFront idle timeouts, reconnect without Last-Event-ID, proxy
  buffering, and when not to use WebSocket.
tags: [research, system-design-patterns, A3, websocket]
---

# WebSocket — external research (2026-09-13)

> **What this is.** The evidence pass behind catalog topic **A3** (WebSocket
> lifecycle, heartbeats, scaling, sticky sessions). No Concept is written
> here. Primary pages fetched 2026-09-13. Paraphrase; numbers and identifiers
> reproduced exactly. Items that could not be verified are in §8 and are
> **not** to be asserted in a later Concept.
>
> **Method.** Wire/protocol (RFC 6455, RFC 8441, RFC 9220, IANA close-code
> registry, WHATWG WebSockets Standard); AWS idle-timeout and stickiness
> pages (API Gateway, ALB, NLB, CloudFront); proxy/LB (nginx, HAProxy,
> Cloudflare, Socket.IO); backplane (Redis `PUBLISH`, Socket.IO Redis
> adapter). Existing chat/WS comparison in
> [cases/aws/ch19.md](../../../cases/aws/ch19.md) is **linked, not rewritten**.

---

## 1. Scope and non-goals

**Owns.** Bidirectional WebSocket as a communication mechanism: HTTP/1.1
Upgrade handshake and RFC 6455 framing; ping/pong heartbeats; close codes;
connection lifecycle; HTTP/2 (RFC 8441) and HTTP/3 (RFC 9220) bootstrapping;
horizontal scale (per-connection memory/FD, fan-out via a pub/sub backplane,
sticky sessions vs connection-local affinity); failure and reconnect (no
`Last-Event-ID`; application-level resume); proxy and load-balancer idle
timeouts and Upgrade handling; verified vendor defaults; when not to use WS.

**Does not own.** Request–response HTTP/gRPC semantics (**A1**). One-way
server push, EventSource auto-reconnect, and `Last-Event-ID` (**A4**).
Signed outbound callbacks (**A5**). Cookie/IP stickiness algorithms as a
general LB topic (**C5**). API-gateway product patterns and BFF (**C6**).
Deadline propagation and generic timeout policy (**C7**). Health-check /
active-passive failover (**C3**). Chat-application Day-0/Day-N AWS design
and the API Gateway / IoT Core / ELB comparison table — that comparison
already lives in [ch19.md](../../../cases/aws/ch19.md) Table 19-1; this
note only verifies the timeout and quota numbers that table points at.

---

## 2. Lineage / vocabulary

**RFC 6455, *The WebSocket Protocol*** (IETF Standards Track, December 2011).
Independent TCP-based protocol whose *only* relationship to HTTP is that the
opening handshake is an HTTP Upgrade so one port can serve both. Two parts:
handshake, then framed full-duplex data. Six frame types in this version
(ten opcodes reserved). Client-to-server frames **must** be masked; servers
**must not** mask. Closing handshake is a Close control frame (opcode 0x8)
exchanged both ways so intermediaries that drop TCP FINs do not silently
lose data.

**RFC 8441, *Bootstrapping WebSockets with HTTP/2*** (September 2018).
HTTP/2 forbids connection-wide `Upgrade` / `Connection` and status 101.
Extended CONNECT: server advertises `SETTINGS_ENABLE_CONNECT_PROTOCOL = 1`;
client sends `:method = CONNECT`, `:protocol = websocket`, plus `:scheme`,
`:path`, `:authority`. Success is HTTP **200**, not 101. `Connection` and
`Upgrade` **MUST NOT** appear. `Sec-WebSocket-Key` / `Sec-WebSocket-Accept`
processing is **superseded** by `:protocol`. `Origin`,
`Sec-WebSocket-Version`, `Sec-WebSocket-Protocol`, and
`Sec-WebSocket-Extensions` still apply (HTTP/2 names are lowercase). After
the handshake the peers run RFC 6455 on that HTTP/2 stream as if it were
the TCP connection; state is OPEN (RFC 6455 §4.1). Stream `END_STREAM` ≅
orderly TCP close; `RST_STREAM` + `CANCEL` ≅ RST.

**RFC 9220, *Bootstrapping WebSockets with HTTP/3*** (June 2022). Same
Extended CONNECT semantics; `SETTINGS_ENABLE_CONNECT_PROTOCOL` value
**0x08**, default **0**. Unknown `:protocol` → 501. Orderly close = FIN on
the HTTP/3 stream; abort = `H3_REQUEST_CANCELLED`.

**WHATWG WebSockets Standard** (Living Standard; fetched 2026-09-13).
Browser API: `WebSocket(url[, protocols])`, `readyState` CONNECTING /
OPEN / CLOSING / CLOSED, `send`, `close([code][, reason])`, events
`open` / `message` / `error` / `close`. **Ping and Pong frames are not
exposed.** User agents may send pings or unsolicited pongs for NAT
keepalive or latency display; they **must not** use them to aid the
server. There is **no automatic reconnect** and no `Last-Event-ID`
(that header is EventSource / **A4**). `MessageEvent.lastEventId` is
defined for SSE; it is empty for WebSocket messages.

**IANA WebSocket Close Code Number Registry.** RFC 6455 codes plus later
registrations 1012 Service Restart, 1013 Try Again Later, 1014 Bad Gateway
(HTTP-502 analogue). Range 4000–4999 private use.

**Socket.IO v4** (library layered *on* WS + HTTP long-polling). Not the
protocol. Its Engine.IO heartbeat and Redis adapter are the most-cited
operational defaults for “WS at more than one node.” `connectionStateRecovery`
(v4.6.0+) is an *application* resume mechanism, not an RFC feature.

---

## 3. Mechanics

### 3.1 Wire semantics (RFC 6455)

**Opening handshake (HTTP/1.1).** Client:

```
GET /chat HTTP/1.1
Host: server.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Origin: http://example.com
Sec-WebSocket-Protocol: chat, superchat
Sec-WebSocket-Version: 13
```

Server proves receipt: concatenate the key (trimmed) with GUID
`258EAFA5-E914-47DA-95CA-C5AB0DC85B11`, SHA-1, Base64 →
`Sec-WebSocket-Accept`. For the example key the Accept value is
`s3pPLMBiTxaQ9kYGzzhZRbK+xOo=`. Any status other than **101 Switching
Protocols** means the handshake failed and HTTP semantics still apply.
`Sec-WebSocket-Protocol` is the server’s chosen subprotocol (one or none).
`Origin` is the browser CSRF/cross-origin check; the server may reject
with an HTTP error before upgrading.

**Frame header.** FIN | RSV1-3 | opcode (4) | MASK | 7-bit length
(0–125 direct; 126 → 16-bit; 127 → 64-bit) | optional 32-bit masking key
| payload. Opcodes: `0x0` continuation, `0x1` text (UTF-8), `0x2` binary,
`0x8` Close, `0x9` Ping, `0xA` Pong. A *message* is one or more frames;
control frames **MUST** have payload ≤ **125 bytes** and **MUST NOT** be
fragmented; they MAY be interjected in the middle of a fragmented data
message. Client frames MUST be masked (XOR with a fresh unpredictable
32-bit key); a client that sees a masked server frame closes with 1002.

**Closing handshake.** Either peer sends Close (optional 2-byte status +
UTF-8 reason). The receiver MUST reply with Close if it has not already
sent one, then both close TCP (server immediately; client SHOULD wait
for the server FIN). Simultaneous Close is legal. After sending Close,
no further data frames. After receiving Close, further data is discarded.

**Close codes (RFC 6455 §7.4.1 + IANA).** Sent on the wire: 1000 Normal,
1001 Going Away, 1002 Protocol Error, 1003 Unsupported Data, 1007 Invalid
payload (non-UTF-8 in a text message), 1008 Policy Violation, 1009 Message
Too Big, 1010 Mandatory Extension (client only; server can fail the
handshake instead), 1011 Internal Error. **MUST NOT be sent:** 1004
Reserved, **1005** No Status Rcvd, **1006** Abnormal Closure, **1015**
TLS handshake failure. IANA later: **1012** Service Restart, **1013** Try
Again Later, **1014** Bad Gateway. 0–999 unused; 1000–2999 standards /
specification required; 3000–3999 first-come (libraries); 4000–4999
private use.

### 3.2 Connection lifecycle

Conceptual states (RFC 6455 §4 / §7 + WHATWG `readyState`): CONNECTING
(handshake in flight) → OPEN (frames) → CLOSING (Close sent or received)
→ CLOSED (TCP torn down, or never opened). Browser `close` event carries
`wasClean`, `code`, `reason`. Abnormal drops surface as **1006** in the
API even though 1006 is never on the wire.

Auth happens at handshake time. AWS API Gateway documents this
explicitly: `AuthN`/`AuthZ` run only on `$connect`; a failed authorizer
returns HTTP **401/403** and the socket is never established. `$connect`
integration (optional) can persist `connectionId` (variable-length;
format may change), domain, and stage. `$disconnect` runs **after** the
socket is already closed and is **best-effort** — delivery is not
guaranteed. Backend-initiated close uses the `@connections` API.

### 3.3 Heartbeats (ping/pong vs application)

RFC 6455 Ping (0x9) MAY carry application data. Receiver MUST Pong (0xA)
with identical application data unless a Close was already received;
MAY collapse outstanding Pings to the most recent. Unsolicited Pong is a
unidirectional heartbeat; no reply is expected. Ping is both keepalive
and liveness probe.

**Browser gap.** The WHATWG API does not expose ping/pong. A JS client
cannot send a protocol Ping. Server-originated Pings still work if the
user agent answers them (it must, at the protocol layer). To probe
*from the browser*, send an application data frame (e.g. `{"type":"ping"}`)
and require a data-frame pong. That also resets proxy idle timers that
only count bytes, not “TCP is up.”

**Library heartbeat (Socket.IO / Engine.IO v4, fetched 2026-09-13).**
`pingInterval` **25000** ms; `pingTimeout` **20000** ms (v4.0.0 changed
the timeout from 5000). Server sends a ping packet every interval; no
pong within timeout → disconnect reason `ping timeout`. Client treats
the link dead if it sees no ping within `pingInterval + pingTimeout`
(**45 s**). nginx’s default `proxy_read_timeout` is **60 s**; Socket.IO
docs require it to be **greater than** `pingInterval + pingTimeout`
or the proxy closes first (`transport close`). `perMessageDeflate`
default **false** since Socket.IO v3 (CPU/memory cost).
`maxHttpBufferSize` **1e6** (1 MB). `connectTimeout` **45000** ms.
`connectionStateRecovery.maxDisconnectionDuration` example **120000** ms
when the feature is enabled (v4.6.0+; default of the option itself is
`undefined` / off).

### 3.4 HTTP/2 and HTTP/3 vs HTTP/1.1 Upgrade

Trade-off: RFC 8441 multiplexes WS onto an existing h2 connection
(shared congestion window, no extra TCP/TLS handshake) but every hop
must implement Extended CONNECT. CloudFront **only supports WebSocket
over HTTP/1.1** (AWS, fetched 2026-09-13). ALB documents native WS as
an HTTP/1.1 Upgrade that turns the client-to-LB and LB-to-target TCP
connections into a persistent tunnel; the same listener page documents
HTTP/2 (up to **128** concurrent requests on one h2 connection) as a
*separate* feature and says HTTP/2 PING frames **do not** reset the
ALB idle timeout. ASP.NET Core docs (view=aspnetcore-10.0): Chrome,
Edge, and Firefox **128+** have HTTP/2 WebSockets enabled by default
(`network.http.http2.websockets` in Firefox). A server that advertises
h2 but does not handle `:protocol = websocket` will fail Chrome/Firefox
handshakes with **1006** while Safari (HTTP/1.1 Upgrade) still works —
observed in Mattermost #30285; treat browser-matrix details beyond the
Microsoft sentence as §8.

### 3.5 Scaling limits and fan-out

A WebSocket is one long-lived TCP (or one h2/h3 stream) **plus** server
process state (subscriptions, presence). Horizontal scale therefore has
two distinct problems:

1. **Accept and hold connections.** First ceilings are OS file
   descriptors, per-connection buffers, and TLS session memory — not
   request rate. No vendor-neutral “N connections per box” is asserted
   here (see §8). API Gateway does **not** quota concurrent connections;
   the implied ceiling is `new connections per second × 2 h duration`.
   Default **500** new connections/s/account/Region (increasable) ×
   7 200 s = **3 600 000** concurrent if clients connect at the cap for
   two hours (AWS example, not a guarantee). Frame size **32 KB**,
   message payload **128 KB** (must split above 32 KB; oversize →
   close **1009**). Integration timeout **50 ms–29 s** (not increasable)
   — that is the *backend invocation* window, not the socket lifetime.

2. **Fan-out to the right sockets.** After upgrade, a message for user B
   must reach the process that owns B’s socket. Options:
   - **Sticky + in-process map** — cheap, dies with the instance
     (C5 / C3).
   - **Registry** (user → `{node, connectionId}`) in Redis/DynamoDB plus
     node-to-node send — what [ch19.md](../../../cases/aws/ch19.md)
     describes for chat; do not re-derive it.
   - **Pub/sub backplane.** Publisher does not know subscribers. Redis
     `PUBLISH` complexity **O(N+M)** (N = subscribers on the channel,
     M = all pattern subscriptions). Delivery is **at-most-once**; a
     subscriber that is down misses the message forever. In Redis
     Cluster, classic `PUBLISH` is forwarded across nodes; Redis **7.0**
     sharded pub/sub (`SPUBLISH` / `SSUBSCRIBE`) keeps propagation
     inside the owning shard. Socket.IO Redis adapter: each node
     publishes the packet; every other node broadcasts to *its local*
     sockets. **Three Redis subscriptions per namespace** (broadcast,
     request, response). Default channel prefix `socket.io`;
     `requestsTimeout` **5000** ms. The adapter **does not** remove the
     need for sticky sessions when HTTP long-polling is enabled
     (polling is many sequential HTTP requests that must hit the same
     Engine.IO session). **WebSocket-only** (`transports: ["websocket"]`)
     makes stickiness unnecessary for the *live* connection because
     there is a single TCP session; reconnects still land randomly
     unless you pin them or keep session state off-box.

**Autoscaling interaction.** New targets take *new* handshakes. Existing
WS stay on the target that returned 101. Adding capacity does not drain
old sockets. ALB deregistration delay default **300 s** (range 0–3600);
after it elapses the target may be terminated and the ALB **closes the
client side** — it does not fail the socket over to another target
(AWS re:Post, consistent with the stickiness page).

### 3.6 Failure and reconnect (no Last-Event-ID)

RFC 6455 has no resume token. CloudFront: “If the WebSocket connection
is disconnected … client applications are expected to re-initiate the
connection.” WHATWG: implement reconnect in `onclose`; the new object is
a new handshake (new `Sec-WebSocket-Key`, new API Gateway
`connectionId`).

**Contrast with A4.** EventSource on reconnect sends `Last-Event-ID`
automatically. WebSocket `message` events do not. Resume is
**application-level**: monotonic event IDs in payloads, a replay
request after `onopen` (`{type:"replay", afterEventId}`), or a library
feature such as Socket.IO `connectionStateRecovery` (in-memory backup
for a bounded `maxDisconnectionDuration`). Missed messages during the
gap are gone unless the app persisted them (offline store in ch19).

**Reconnect policy by close code (operational, not RFC-normative).**
1000: usually do not retry. 1001 / 1012: retry with jitter (1012’s
IANA note: randomized **5–30 s** if the client chooses to reconnect —
from the hybi registration mail, not RFC 6455). 1006: retry; the close
was unclean. 1002 / 1003 / 1007 / 1010: do not retry unchanged. 1013:
back off longer (overload). API Gateway idle/max-lifetime → **1001**;
oversize → **1009**; binary → **1003** (binary is unsupported);
internal → **1011**; service restart → **1012**; unexpected TCP drop →
**1006**. `$disconnect` may not fire; clients must detect via heartbeat
timeout, not only `onclose` (API Gateway re:Post: some clients miss
`OnClosed` on gateway-initiated idle/2 h close).

**Dogpile.** Coordinated 2-hour API Gateway lifetime or a fleet bounce
produces a reconnect stampede. Jitter the retry (C2); 1012’s 5–30 s
range is the registered hint. First-attempt traffic should still pass
(C2 token-bucket lesson); do not pause *all* connects behind a shared
breaker (C1).

### 3.7 Proxy / load-balancer interactions

`Upgrade` and `Connection` are **hop-by-hop**. A reverse proxy that
strips them never delivers a WS handshake. nginx since **1.3.13**
tunnels after a proxied **101** if the client asked for Upgrade; the
official recipe re-injects the headers (`map $http_upgrade
$connection_upgrade`) because they are not forwarded by default.
Default `proxy_read_timeout` **60 s** (between successive upstream
reads, not the whole response). Official alternatives: raise
`proxy_read_timeout`, **or** have the upstream send WebSocket ping
frames. Same 60 s default applies to `proxy_send_timeout`.
`proxy_http_version 1.1` is required for Upgrade (HTTP/1.0 cannot).

**HAProxy 3.4** (configuration manual, fetched 2026-09-13). After 101,
the connection is a tunnel; `timeout tunnel` “supersedes both the
client and server timeouts.” Documented example: `timeout tunnel 1h`
with `timeout client/server 30s`. There is **no implicit numeric
default** for `timeout tunnel`; if unset, client/server idle timers
apply (example defaults in the same manual: `timeout client 50000ms`,
`timeout server 50000ms`). `timeout client-fin` / `server-fin` exist
because half-closed WS/RDP otherwise sit in FIN_WAIT.

**AWS ALB** (docs 2026-09-13). Native WS on HTTP and HTTPS listeners.
Idle timeout default **60 s**, range **1–4000 s**
(`idle_timeout.timeout_seconds`). Send ≥ 1 byte before each idle
period. Application idle should be **longer** than the LB idle or the
target’s ungraceful close yields client **HTTP 502**. HTTP/2 PING does
**not** reset idle. HTTP client keepalive (separate knob) default
**3600 s**, range **60–604800 s** — this is the max time ALB keeps a
*persistent HTTP* client connection; after expiry, HTTP/1.x gets
`Connection: close`, HTTP/2 gets `GOAWAY`. Whether keepalive also caps
an already-upgraded WS is **not** stated on that page (§8).
**Stickiness:** “WebSocket connections are inherently sticky. … the
target that returns an HTTP 101 … is the target used … After the
WebSockets upgrade is complete, cookie-based stickiness is not used.”
AWS Prescriptive Guidance: if the workload *is* WebSockets, “there is
no need to use any [stickiness] strategy” *for the live socket*.
Cookie stickiness (`stickiness.enabled` default **false**;
`lb_cookie` / `app_cookie`; cookie duration default **86400 s**, max
**604800 s**) still matters for **reconnects** and for any HTTP
handshake that must return to in-memory session state. WS is **not**
supported on target groups with target optimizer enabled. Deregistration
delay default **300 s**.

**AWS NLB** (docs 2026-09-13). Layer-4 passthrough; WS is just TCP.
`tcp.idle_timeout.seconds` default **350**, range **60–6000**. **TLS
listeners: 350 s, not configurable.** If TCP idle is set **above 350 s**,
the target ENI `TcpEstablishedTimeout` must be ≥ the NLB value; Nitro
V6+ default connection-tracking timeout is **350 s** — mismatch → the
ENI silently drops state while NLB still thinks the flow is alive.

**AWS API Gateway WebSocket** (quotas page + overview, 2026-09-13).
Idle **10 minutes**, max duration **2 hours**, both **not increasable**.
Idle or max-lifetime close code **1001**. Routes: `$connect`,
`$disconnect`, `$default`, plus custom keys from
`routeSelectionExpression` (JSON; non-JSON → `$default`). Outbound:
route response, or `@connections` POST. Account throttle on
`@connections` is documented on the general limits page as increasable
(do not invent the rps figure here; see §8). Binary media **1003**.

**Amazon CloudFront** (websockets + quotas, 2026-09-13). WS enabled on
every distribution. Forward **all** viewer headers (`AllViewer`) **or**
at least `Sec-WebSocket-Key` and `Sec-WebSocket-Version`. Recommended
also: `Sec-WebSocket-Protocol`, `Sec-WebSocket-Accept`,
`Sec-WebSocket-Extensions` (compression surprises). **HTTP/1.1 only.**
WebSocket idle quota: origin response timeout **10 minutes** — “If
CloudFront hasn't detected any bytes sent **from the origin to the
client** within the past 10 minutes, the connection is assumed idle and
is closed.” Directionality is origin→client in that sentence (§8).

**Cloudflare** (Network WebSockets, updated 2026-08-14, fetched
2026-09-13). Proxied WS on all plans; toggle on Network. WAF inspects
the **initial 101 only**. Argo is **incompatible**. “When Cloudflare
releases new code … we may restart servers, which terminates WebSockets.”
Idle: closed after “a period of time” with no data either way;
Enterprise can set a custom idle timeout. **No numeric default is
published on that page** (§8). Load-balanced origins need session
affinity so a reconnect does not land on a node without the session.

**Stacking timeouts.** The effective idle is the **minimum** hop that
sees no bytes: browser/OS, NAT, CDN, LB, proxy `read_timeout`, app
heartbeat. A 25 s Socket.IO ping clears nginx 60 s and ALB 60 s; it
does **not** extend API Gateway’s 2 h lifetime. Protocol Pings reset
hops that parse WS frames; some L7 devices only reset on application
data — verify the hop (API Gateway idle vs protocol ping is §8).

---

## 4. Verified defaults / standards

Fetched 2026-09-13. Versions/dates are those on the cited page.

| Knob | Value | Increasable? | Source |
|---|---|---|---|
| RFC 6455 version | 13 (`Sec-WebSocket-Version`) | — | RFC 6455 |
| Accept GUID | `258EAFA5-E914-47DA-95CA-C5AB0DC85B11` | — | RFC 6455 |
| Control-frame payload | ≤ 125 B, no fragmentation | — | RFC 6455 §5.5 |
| HTTP/2 WS success status | 200 (not 101) | — | RFC 8441 |
| `SETTINGS_ENABLE_CONNECT_PROTOCOL` | 0x08, default 0 | — | RFC 8441 / 9220 |
| API GW new connections/s | 500 / account / Region | Yes | API GW WS quotas |
| API GW concurrent connections | none (implied 500×7200 = 3.6 M) | n/a | same |
| API GW frame / message | 32 KB / 128 KB | No | same |
| API GW idle / max duration | 10 min / 2 h | No | same |
| API GW integration timeout | 50 ms–29 s | No | same |
| API GW idle/max close code | 1001 | — | API GW overview |
| ALB idle | 60 s default; 1–4000 s | Yes | ALB attributes |
| ALB HTTP client keepalive | 3600 s default; 60–604800 s | Yes | ALB attributes |
| ALB stickiness enabled | false | Yes | ALB target groups |
| ALB stickiness cookie TTL | 86400 s default; max 604800 s | Yes | same |
| ALB deregistration delay | 300 s; 0–3600 s | Yes | same |
| NLB TCP idle | 350 s default; 60–6000 s | Yes (TCP only) | NLB idle-timeout |
| NLB TLS idle | 350 s | No | same |
| Nitro V6+ ENI TCP established | 350 s | OS sysctl | NLB idle-timeout |
| CloudFront WS idle | 10 min | No | CloudFront quotas |
| CloudFront WS HTTP version | HTTP/1.1 only | — | CloudFront WS page |
| nginx `proxy_read_timeout` | 60 s | Yes | nginx.org websocket + proxy module |
| HAProxy `timeout tunnel` | no implicit default; example 1 h | Yes | HAProxy 3.4 manual |
| Socket.IO `pingInterval` / `pingTimeout` | 25 000 / 20 000 ms | Yes | socket.io v4 server-options |
| Socket.IO `maxHttpBufferSize` | 1e6 | Yes | same |
| Socket.IO `perMessageDeflate` | false (since v3) | Yes | same |
| Redis `PUBLISH` | O(N+M), at-most-once | — | redis.io PUBLISH + pubsub |
| Redis sharded pub/sub | 7.0+ `SPUBLISH`/`SSUBSCRIBE` | — | redis.io pubsub |
| Socket.IO Redis `requestsTimeout` | 5 000 ms | Yes | redis-adapter README |

**ALB vs NLB vs API Gateway (timeouts only; product choice stays in ch19).**
API Gateway: managed routes + `$connect` auth + `@connections` callbacks;
hard **10 min / 2 h**; 29 s integration; no binary. ALB: L7 routing, WAF,
native 101, idle up to **4000 s**, inherent per-socket stickiness, you
run the WS process. NLB: L4, idle up to **6000 s** (TCP), TLS idle stuck
at **350 s**, no HTTP routing. CloudFront in front of any of them adds a
**10 min** origin→client idle and **forces HTTP/1.1** WS.

---

## 5. Failure modes and when-not-to-use

**Failure modes of the mechanism itself.**

- **Silent half-open.** NAT or a proxy drops the flow; the peer still
  thinks OPEN until the next write or a heartbeat timeout. Browser
  `onclose` may not fire (API Gateway 2 h / idle reports).
- **Idle-timeout mismatch.** App heartbeat > proxy idle → 1006 at 60 s
  (nginx/ALB) or 1001 at 10 min (API GW / CloudFront). Inverse: idle
  raised to hours without app heartbeats → zombie FDs.
- **Reconnect storm.** Synchronized 2 h lifetime, deploy drain, or
  Cloudflare edge restart. No protocol-level jitter.
- **Lost fan-out.** Redis pub/sub at-most-once; a node that blips misses
  broadcasts. In-memory subscription maps die with the instance; ALB
  will not move the socket.
- **Sticky vs backplane confusion.** Redis adapter + polling without
  affinity → Engine.IO session errors. WS-only + in-memory state +
  random reconnect → “logged in on the other box.”
- **HTTP/2 downgrade bugs.** Hop advertises h2 without RFC 8441 →
  Chrome/Firefox CONNECT fails; Safari Upgrade works.
- **Hop-by-hop Upgrade stripped** → handshake never completes (400 or
  silent drop).
- **API Gateway `$disconnect` miss** → stale `connectionId` in DynamoDB;
  `@connections` POST fails; must TTL the row.
- **Message-size close.** API GW 32 KB frame / 128 KB message → 1009.
- **Binary on API GW** → 1003.
- **Half-open drain.** Deregistration delay < in-flight WS lifetime →
  hard cut; delay >> deploy SLO → capacity stuck on draining nodes.
- **NLB > 350 s vs ENI 350 s** → black-hole (LB holds, target already
  forgot).
- **Compression.** `permessage-deflate` (RFC 7692) is expensive; Socket.IO
  leaves it off. CloudFront warns to forward extension headers or
  negotiate surprises.

**When not to use WebSocket.**

- **One-way server → client stream** (notifications, logs, progress):
  **A4 SSE**. EventSource reconnects and sends `Last-Event-ID`; it is
  HTTP and survives more proxies; browsers do the resume. WS buys
  client→server frames you do not need, plus sticky/backplane cost.
- **Request–response, idempotent, cacheable, or CRUD:** **A1** REST or
  multiplexed gRPC. A WS that only wraps RPC still pays connection
  tax, defeats HTTP caching/CDNs, and makes load shedding (C10) and
  timeouts (C7) ad hoc.
- **Server-to-server callbacks, webhooks:** **A5**. Short HTTP POSTs
  with signatures and retries; no socket inventory.
- **You cannot control idle hops** (corporate proxies, unknown NAT) and
  cannot ship a heartbeat shorter than the smallest hop.
- **You need CloudFront + HTTP/2 multiplexing for the same socket.**
  CloudFront WS is HTTP/1.1 only.
- **Binary payloads through API Gateway WS.** Unsupported (1003).
- **Fan-out that must be durable.** Redis pub/sub will drop; use a log
  (A2) and have sockets subscribe to a consumer, or persist then push.
- **Auth that must be re-checked per message** without app work. API GW
  authorizes only at `$connect`.

**When WS is the fit.** Both directions need low-latency frames on an
already-open session (chat typing + send, collaborative editing,
multiplayer, device telemetry with commands). Then: heartbeat < min hop
idle; persist connection identity; backplane or registry for fan-out;
client resume IDs; jittered reconnect; drain ≥ typical session or accept
forced reconnect on deploy.

---

## 6. Cross-links

| Id | Why it borders A3 |
|---|---|
| **A1** | Default for request–response; WS is the exception when the call pattern is not RPC. [rest-rpc-dataflow](../../../cases/data-intensive-design/rest-rpc-dataflow.md). |
| **A4** | SSE: auto-reconnect + `Last-Event-ID`; prefer for one-way push. |
| **A5** | Webhooks: outbound HTTP, not a long socket. |
| **C5** | Sticky sessions as a general LB technique; A3 only needs the WS-inherent-stickiness vs reconnect-affinity distinction. |
| **C6** | API Gateway as a product pattern; A3 owns WS-specific `$connect` / quotas / 10 min / 2 h. |
| **C7** | Timeouts and deadline propagation; hop idle table here, policy there. [timeouts-and-delays](../../../cases/data-intensive-design/timeouts-and-delays.md). |
| **C3** | Failover: ALB/NLB do not migrate a live WS; client reconnect *is* the failover. |
| **C1 / C2** | Reconnect storms: jitter + retry budget; do not trip a shared breaker on first-connect. |
| **ch19** | Chat architecture; Table 19-1 API GW vs IoT Core vs ELB — **link only**. |

---

## 7. Sources

**Protocol.** https://www.rfc-editor.org/rfc/rfc6455.html (Dec 2011) ·
https://www.rfc-editor.org/rfc/rfc8441.html (Sep 2018) ·
https://www.rfc-editor.org/rfc/rfc9220.html (Jun 2022) ·
https://www.iana.org/assignments/websocket/websocket.xml (Close Code
Number Registry) · https://websockets.spec.whatwg.org/ ·
https://html.spec.whatwg.org/multipage/server-sent-events.html
(`Last-Event-ID`, EventSource reconnect) ·
https://developer.mozilla.org/en-US/docs/Web/API/CloseEvent/code ·
https://learn.microsoft.com/en-us/aspnet/core/fundamentals/websockets?view=aspnetcore-10.0
(HTTP/2 WS browser defaults).

**AWS (fetched 2026-09-13).**
https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-execution-service-websocket-limits-table.html ·
https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api-overview.html ·
https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api-route-keys-connect-disconnect.html ·
https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html ·
https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-listeners.html ·
https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html ·
https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html ·
https://docs.aws.amazon.com/prescriptive-guidance/latest/load-balancer-stickiness/options.html ·
https://docs.aws.amazon.com/elasticloadbalancing/latest/network/update-idle-timeout.html ·
https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-listeners.html ·
https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-working-with.websockets.html ·
https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cloudfront-limits.html ·
https://aws.amazon.com/about-aws/whats-new/2024/09/aws-network-load-balancer-tcp-idle-timeout/ ·
https://repost.aws/questions/QUFbNpkJJvTySYuHA7uHQAeQ/extend-websocket-idle-connection-timeout ·
https://repost.aws/questions/QUwS2EfQ7eR_WQGxmXSs1fBg/websockets-behaviour-with-alb.

**Proxies / libraries / backplane.**
https://nginx.org/en/docs/http/websocket.html ·
https://nginx.org/en/docs/http/ngx_http_proxy_module.html (`proxy_read_timeout 60s`) ·
https://docs.haproxy.org/3.4/configuration.html ·
https://developers.cloudflare.com/network/websockets/ ·
https://socket.io/docs/v4/using-multiple-nodes/ ·
https://socket.io/docs/v4/server-options/ ·
https://socket.io/docs/v4/how-it-works/ ·
https://github.com/socketio/socket.io-redis-adapter ·
https://redis.io/docs/latest/commands/publish/ ·
https://redis.io/docs/latest/develop/pubsub/.

**Existing workspace note (do not duplicate).**
[cases/aws/ch19.md](../../../cases/aws/ch19.md)
(chat; WS / API GW / IoT Core / ELB comparison).

---

## 8. Uncertain / left out

- **Cloudflare idle timeout in seconds.** Official page says only “a
  period of time”; Enterprise can customize. Secondary write-ups claim
  100 s. **Not asserted.**
- **Whether API Gateway treats RFC 6455 Ping/Pong as activity** against
  the 10-minute idle timer. Official quotas/overview do not say;
  practitioner notes recommend application heartbeats. **Not asserted.**
- **Whether ALB `client_keep_alive.seconds` (default 3600) forcibly
  ends an upgraded WebSocket.** The page describes HTTP/1.x
  `Connection: close` and HTTP/2 `GOAWAY` after keepalive; WS is not
  mentioned. Idle timeout (60–4000 s) is the verified WS-relevant knob.
- **CloudFront idle direction.** Quotas text measures bytes
  origin→client only. Whether client→origin traffic alone resets the
  10-minute timer is unstated.
- **API Gateway `@connections` account-level rps / burst.** A
  third-party skill quotes 10 000 rps / 5 000 burst; not re-fetched
  from the current general limits table in this pass.
- **Browser RFC 8441 matrix.** Microsoft: Chrome/Edge/Firefox 128+
  default on. websocket.org table still marks Firefox Extended CONNECT
  as unsupported. Safari primary page not fetched. Mattermost #30285 is
  an incident report, not a spec.
- **Per-host connection counts** (C10K, “1 M sockets / box”, Ejabberd
  “> 2 million” in ch19). Implementation- and kernel-specific; ch19 is
  linked, not re-measured.
- **Cellular / home-NAT idle (30–120 s / 60–300 s).** Common operator
  folklore; no primary citation in this pass.
- **HAProxy `timeout tunnel` default when omitted.** Manual gives an
  example (1 h) and says tunnel supersedes client/server; it does not
  publish a built-in number.
- **RFC 7692 `permessage-deflate` library defaults** beyond Socket.IO’s
  `false`. Not a full extension survey.
- **AppSync WS quotas.** ch19 claims no hard concurrent-connection
  limit; not independently re-verified here.
- **1012 reconnect 5–30 s.** IANA registration mail / Netty comment,
  not RFC 6455. Treat as a registered hint, not a protocol MUST.

---
