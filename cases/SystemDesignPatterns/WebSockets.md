---
type: reference
title: 'WebSocket communication'
description: 'Full-duplex messaging over one long-lived connection: RFC 6455 mechanics (masking rationale, control frames, the close-code map), h2/h3 status and nginx’s refusal, the 20-to-30-second heartbeat rule, stateless scaling with pub/sub backplanes, verified managed quotas (API Gateway 10 min/2 h/32 KB/128 KB), bufferedAmount backpressure, deflate memory costs, browser auth patterns, and when a socket is the wrong tool.'
tags: [system-design-patterns, communication, websocket, realtime]
---

# WebSocket communication

**See also:** [server-sent events](ServerSentEvents.md) · [timeouts](TimeoutsDeadlines.md) · [load balancing](LoadBalancing.md) · [pub/sub & queues](PubSubQueues.md) · [idempotency](Idempotency.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/websocket-external-research.md)

A WebSocket turns one HTTP request into a **full-duplex, long-lived connection**: after the 101 upgrade, both sides send frames whenever they like. That buys true bidirectional push at minimal per-message cost, and it buys every long-lived-connection problem at once — heartbeats, reconnect logic, sticky load, proxy hostility, and a browser API with no headers. Quality attributes: **interactivity** (client-to-server and server-to-client without polling) and per-message **efficiency**. Costs: statefulness in a fleet designed for stateless requests, and an ecosystem — caches, gateways, [balancers](LoadBalancing.md) — built for the request-response shape you just left.

## Wire mechanics that matter (RFC 6455)

- **Handshake**: GET + Upgrade + a random key; the server proves protocol awareness by hashing the key with a fixed GUID into `Sec-WebSocket-Accept`. After 101, it is not HTTP anymore.
- **Masking**: clients MUST mask every frame (servers must not). The reason is infrastructure, not secrecy: unmasked script-chosen bytes could impersonate HTTP requests to naive intermediaries and poison caches.
- **Control frames** (Close, Ping, Pong) are ≤ 125 bytes, never fragmented, and may interleave *inside* a fragmented message — which is why heartbeats keep working during a large transfer. A Pong echoes its Ping's payload; unsolicited Pongs are legal one-way heartbeats.
- **Close codes you will actually see**: 1000 normal; 1001 going away (deploys, tab closed — expect and handle it routinely); 1008 policy; 1009 message too big; 1011 server error; 1012/1013 restart / try later (registry additions). **1006 is never on the wire** — it is the local report for "the TCP died with no Close frame", i.e. the signature of an idle-timeout kill by a proxy or LB.
- App-defined codes live in 4000–4999.

## HTTP/2 and HTTP/3 reality

RFC 8441 (h2) and RFC 9220 (h3) tunnel WebSockets through Extended CONNECT so sockets share a multiplexed connection. Support is uneven where it counts: Chrome has it (on an already-open h2 connection that advertised the setting), Firefox has it, and **nginx has declined to implement it** (the maintainer's position: translating extended CONNECT to Upgrade is not a good solution). Practical consequence: behind the most common proxy, every browser socket is an HTTP/1.1 connection of its own. Design for h1 sockets; treat h2/h3 coalescing as a bonus.

## Heartbeats: the 20 to 30 second rule

TCP alone detects a dead idle peer in about two hours at best, and an unacked write can hang up to half an hour ([timeouts](TimeoutsDeadlines.md)). The protocol gives you Ping/Pong and no interval; the infrastructure sets it for you:

| Timer on the path | Default |
|---|---|
| NGINX tunnel (`proxy_read_timeout`, upstream direction) | 60 s |
| ALB idle | 60 s |
| socket.io ping / pong-timeout | 25 s / 20 s |
| API Gateway idle | 10 min |

Heartbeat **under the shortest idle timer on the path** — hence the de-facto 20–30 s. Detection latency ≈ interval + timeout (45 s at socket.io defaults). Cost scales with fleet size: 25 s pings across a million sockets is 40 thousand frames per second of pure liveness. Note NGINX's timer watches the *upstream* direction — a chatty client alone does not keep the tunnel alive; the server must speak.

## Scaling: stateless nodes, shared broadcast

- **Stickiness is narrower than folklore says**: it is required only when *multi-request* session state lives on a node (socket.io needs it for long-polling; for WebSocket-only transport it documents that sticky sessions are no longer required). The connection itself is already pinned at L4 ([load balancing](LoadBalancing.md)).
- The real engineering is the **broadcast path**: a message for room X must reach sockets on every node. The reference shape is a pub/sub backplane (socket.io's Redis adapter: deliver locally, publish globally, every node forwards to its own members) — connection registry local, routing global, nodes replaceable.
- **Deploys are the enemy of long-lived connections**: survivors keep the herd ([the pinning problem](LoadBalancing.md)). Age connections out deliberately — server-initiated 1001/1012 closes on a jittered schedule, clients reconnecting with jittered backoff — and remember managed platforms do it for you whether you like it or not (API Gateway closes every socket at 2 hours).
- **Verified capacity anchors**: API Gateway WebSocket — 500 new connections/s per account/Region, no concurrent cap (3.6 M by arithmetic); Azure Web PubSub/SignalR — 1,000 concurrent connections per unit.

## Managed sockets: the callback pattern

API Gateway WebSocket APIs terminate the socket at the edge: your backend gets invoked per message (`$connect` for auth, `$disconnect` for cleanup, routes by a JSON field) and pushes by calling a management API with the connection id (a gone connection raises an exception — your registry learns of deaths lazily). Hard quotas to design against: **idle 10 min, lifetime 2 h, frame 32 KB, message 128 KB**, none increasable; oversized traffic closes with 1009. The shape generalizes to Azure Web PubSub: the service owns the socket, you own a connection registry and a push API — statelessness restored at the price of per-message invocation.

## Backpressure and compression

- `send()` never blocks anywhere. The browser exposes only `bufferedAmount` to poll before producing more; Node's ws adds a per-send callback (the real server-side hook) plus `pause()`/`resume()`; the Streams-based WebSocketStream API with genuine backpressure is still non-standard. Rule: treat every socket as an unbounded buffer unless you check — the [queues-don't-fix-overload](LoadShedding.md) trap with a friendlier API.
- ws server defaults deserve two edits on day one: `maxPayload` is **100 MiB** (tune down), and permessage-deflate is **off for a reason** — per-connection zlib contexts (context takeover) make compression × connection-count the real memory budget, and the ws maintainers document severe fragmentation under concurrency. Enable it narrowly (threshold, no-context-takeover, bounded windows) or not at all.

## Auth without headers

The browser constructor takes a URL and subprotocols — nothing else. The worked options:

1. **Cookies**: automatic, and attached to *any* origin's handshake — Cross-Site WebSocket Hijacking. Origin-allowlist checks constrain browsers only (non-browser clients forge Origin freely).
2. **Query-string token**: universal and logged everywhere; treat as last resort and redact.
3. **Ticket auth** (the documented reference flow): fetch a short-lived single-use ticket over authenticated HTTPS, present it on connect, validate source and expiry server-side. This is what API Gateway's `$connect` authorizer institutionalizes.
4. **Token in the subprotocol** — the one header you can set: Kubernetes' apiserver accepts a base64url bearer token as a `Sec-WebSocket-Protocol` entry (offer one real subprotocol too, since the server must echo a selection).

Always `wss://`.

## Failure modes

- **The 1006 epidemic**: idle timers killing quiet sockets (heartbeat under the shortest timer; expect 1001/1006 as routine, reconnect with jittered backoff and resubscribe logic — the protocol has **no resume**; missed messages are an application problem, which is where [SSE's](ServerSentEvents.md) built-in cursor or a [queue](PubSubQueues.md) earns its place).
- **Herd-on-reconnect**: a deploy or LB flip closes thousands of sockets at once; un-jittered clients reconnect as one wave into cold nodes ([cold-start hammering](LoadBalancing.md)).
- **Broadcast backplane as SPOF**: every node's fan-out rides the Redis/pub-sub channel; size and monitor it like the tier-one dependency it becomes.
- **Memory by a thousand sockets**: deflate contexts, per-connection buffers, unbounded `bufferedAmount` to slow clients — the [bulkhead](Bulkhead.md) discipline applies per connection class.
- **Request-response tunneled through the socket**: reinventing status codes, correlation ids, timeouts, and retries inside a schema invisible to every proxy, cache, and tracing tool — while paying stickiness and heartbeat tax. Keep the transactional surface on HTTP ([request-response](RequestResponse.md)); use the socket for the push surface.

## Trade-offs

| Buy | Pay |
|---|---|
| True bidirectional push, minimal per-message overhead | Long-lived state in a stateless-by-design fleet |
| One handshake, then frames | Heartbeats, reconnect, resubscribe — all yours; no protocol resume |
| Binary frames, subprotocols | Browser API: no headers, polling-only backpressure |
| Managed offerings restore statelessness | Their quotas (10 min/2 h/128 KB) become your protocol |

If the data flows one way, [SSE](ServerSentEvents.md) buys reconnect, resume, and plain-HTTP infrastructure for free; if the data must survive the receiver being away, that is a [queue](PubSubQueues.md), not a socket.

## Sources

Verified 2026-09-13; full URLs and exclusions in the [external research note](../../docs/research/sysdesign/websocket-external-research.md). Key primaries: RFC 6455, the IANA close-code registry, RFC 8441/9220 with Chrome/Firefox status and nginx ticket #1992; socket.io server-options and Redis-adapter docs; AWS API Gateway WebSocket docs and quota tables; Azure limits; MDN and the WHATWG standard; ws documentation; RFC 7692; the Kubernetes apiserver subprotocol source; Heroku's ticket-auth article; the OWASP WebSocket cheat sheet; Ably's WS-vs-HTTP comparison. Idle timers and pinning cited via the [timeouts](../../docs/research/sysdesign/timeouts-deadlines-external-research.md) and [load-balancing](../../docs/research/sysdesign/load-balancing-external-research.md) notes.
