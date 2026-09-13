---
type: reference
title: 'Server-sent events'
description: 'One-way server push as a plain HTTP response: the text/event-stream wire format, EventSource reconnect (3 s Blink / 5 s Gecko) and the Last-Event-ID cursor, the 200-only announce and 204 stop rules, GET-only client limits versus fetch-parse, H1 six-socket starvation versus H2 multiplexing, proxy buffering versus idle teardown with verified nginx/ALB/CF/Azure/GCP knobs, and the SSE / WebSocket / long-polling decision table.'
tags: [system-design-patterns, communication, sse, streaming]
---

# Server-sent events

**See also:** [WebSocket](WebSockets.md) · [request–response](RequestResponse.md) · [timeouts](TimeoutsDeadlines.md) · [pub/sub & queues](PubSubQueues.md) · [load balancing](LoadBalancing.md) · [retry](RetryBackoff.md) · [webhooks](Webhooks.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/a4-sse-external-research.md)

Server-sent events are server push as an ordinary HTTP response that does not end: `Content-Type: text/event-stream`, then UTF-8 lines. Because it is *just HTTP*, auth cookies, routing, load balancers, and tracing keep working; because the browser client has reconnection and a resume cursor **built in**, SSE ships with the reliability plumbing [WebSocket](WebSockets.md) makes you write. The constraint is honest: one direction, text only. Quality attributes: **simplicity** (no Upgrade, no new protocol) and **resumability** (`Last-Event-ID`). Costs: unidirectional; UTF-8 only; one file-descriptor per subscriber; and the buffering and idle-timer hazards of any long-lived response.

## Lineage

- **WHATWG HTML §9.2** is the protocol source of truth (`EventSource`, the `text/event-stream` grammar, announce / reestablish / fail, `Last-Event-ID`). The 2015 W3C Recommendation is a snapshot of the same design; the live TR page redirects at WHATWG.
- **WHATWG Fetch** builds the constructor request as potential-CORS, cache mode `no-store`, optional `Accept: text/event-stream`. CORS-safelisted request headers do **not** include `Last-Event-ID` (whatwg/fetch#1788 proposed adding it; it had not landed as of 2026-09-13).
- **RFC 9112 §9.4** tells clients to limit concurrent HTTP/1.1 connections but **mandates no number**. RFC 2616's "two" is gone. Engine pools, not the RFC, set the six-socket figure below.
- **RFC 9113 §6.5.2**: `SETTINGS_MAX_CONCURRENT_STREAMS` starts **unlimited**; implementations are recommended to advertise no fewer than **100**.
- **RFC 6202** (informational, 2011) names the three HTTP push shapes — short poll, long poll, HTTP streaming — and warns that intermediaries may legally buffer a whole response.

## Wire semantics

The MIME type **must** be `text/event-stream`. Encoding is UTF-8 with no switch; a leading BOM is stripped. Lines end in CRLF, LF, or CR. An event is one or more field or comment lines terminated by a **blank line**. End-of-stream without that blank line **discards** the incomplete event. Field names are compared literally (no case folding). Unknown fields are ignored, so the format is forward-compatible by construction.

| Field | Effect |
|---|---|
| `data` | Append value + LF to the data buffer. Consecutive `data` lines join with newlines; a trailing LF is stripped on dispatch. |
| `event` | Set the event-type buffer. Empty → dispatch as `message`. Named types require `addEventListener(name)`; `onmessage` does **not** see them. |
| `id` | If the value contains no U+0000, set the last-event-ID **buffer**. An empty `id:` resets that buffer to `""`, so the next reconnect sends **no** `Last-Event-ID`. |
| `retry` | ASCII digits only → reconnection time in milliseconds. Anything else is ignored. |
| `:` comment | Ignored. This is the keepalive primitive (WHATWG authoring notes: about every **15 seconds** against legacy proxies). |

On dispatch the browser copies the last-event-ID buffer onto `MessageEvent.lastEventId` and **does not clear the buffer** — later events without `id` still expose the previous cursor. A comments-only block with empty data fires nothing. `Last-Event-ID` is a request header on **reestablish** only, and only when the last event ID string is non-empty.

A stream that a dashboard and an LLM-style token feeder both speak:

```
: keepalive

event: tick
id: 42
data: {"t": 1}

data: hello
data: world

id:
data: reset-cursor
```

The first block is a heartbeat (no dispatch). The second fires a named `tick` with `lastEventId = "42"`. The third fires `message` with data `hello\nworld` and *still* exposes `"42"`. The fourth fires `message` and clears the cursor, so the next reconnect omits `Last-Event-ID`.

## Connection lifecycle

`readyState`: `CONNECTING` (0) at construction → `OPEN` (1) after announce → `CLOSED` (2) after `close()`, a fatal fail, or document teardown.

WHATWG `processResponse`:

1. Aborted network error → **fail** (`CLOSED` + `error`, no reconnect).
2. Other network error → **reestablish**, unless the UA knows it is futile.
3. Status **≠ 200** **or** `Content-Type` is not `text/event-stream` → **fail**.
4. Else announce (`open`) and parse the body line by line.

The non-normative intro calls out **204 No Content** as "stop reconnecting." That is just rule (3): 204 is not 200, so the connection fails. Chromium additionally rejects a 200 whose MIME is not exactly `text/event-stream`, and rejects a non-empty charset other than UTF-8. A gateway error page that is `200` + `text/html`, or a `502`, therefore kills the widget permanently — one `error`, no retry.

`processResponseEndOfBody`: if the response is **not** a network error, reestablish. A clean server close of a 200 stream therefore reconnects. `close()` aborts the in-flight fetch and sets `CLOSED`. The `Document` going away does the same. An open `EventSource` that is garbage-collected must abort the fetch. The spec keeps a strong reference from `Window` / `WorkerGlobalScope` while `CONNECTING` (if `open` / `message` / `error` listeners exist) or `OPEN` (if `message` / `error` listeners exist), and while a task is queued on the remote event task source — drop the listeners if you want the connection to die with the page.

Redirects are fragile: the WHATWG intro says follow 301/307 as normal HTTP; Chromium's `DidFailRedirectCheck` aborts. Do not rely on a stream redirect.

## Reconnect and Last-Event-ID

Reestablish queues `error`, sets `CONNECTING`, waits the reconnection time (the spec permits waiting longer — exponential backoff or "wait for connectivity" — but that extra wait is **optional**), then fetches again, attaching `Last-Event-ID` when the cursor is non-empty.

Default reconnection time is implementation-defined ("probably a few seconds"):

| Engine | Default | Notes |
|---|---|---|
| Chromium / Blink | **3000 ms** (`kDefaultReconnectDelay`) | `ScheduleReconnect` uses the fixed delay; **no extra jitter** |
| Gecko | **5000 ms** (`DEFAULT_RECONNECTION_TIME_VALUE`) | Floor **500 ms**; pref `dom.server-events.default-reconnection-time` |

A fleet that drops together (LB idle, deploy) therefore re-issues in 3 s or 5 s lockstep. Pair that with accept-side [retry budgets](RetryBackoff.md) and [load shedding](LoadShedding.md) on the **server**, not inside `EventSource`. `retry:` resets the client's delay; it is a floor, not a jittered policy.

Resume is a **two-sided** contract. The client's half is automatic: remember `id:`, replay it as `Last-Event-ID`. The server's half is a design task:

- If events were never given `id`s, the client cannot ask for a cursor. Reconnect is a new subscription.
- If the server ignores the header, the client sees a gap or a full replay and does not know which.
- Empty `id:` **clears** the cursor on purpose — use it when the stream's identity changes, not by accident.
- Done right, delivery is **at-least-once with dedupe-by-id possible**. That is more than [WebSocket](WebSockets.md) (no protocol resume) and less than a [queue](PubSubQueues.md) (no durability once the retention window closes).
- Resume across replicas needs a **replayable log**, not fire-and-forget pub/sub. Sticky sessions are a substitute when the event buffer is process-local — they hide the bug until a deploy drains the instance ([load balancing](LoadBalancing.md)). The placement choice is the same one [WebSocket](WebSockets.md) makes for connection state: registry local, routing global, nodes replaceable — except SSE's cursor makes the *log* the registry.
- Do not treat `Last-Event-ID` as secret-bearing or as an ACL. It is an arbitrary UTF-8 cursor the client will echo; WHATWG/Fetch issues (#689, #568) exist because a planted id becomes a request header on the next GET.

## The client API and its escape hatch

`EventSource` is deliberately tiny: a URL plus `withCredentials` (default `false`). The constructor issues a GET-equivalent fetch, cache `no-store`. There is **no** spec hook for custom headers, a method other than GET, or a request body. Chromium hard-codes `GET`, `Accept: text/event-stream`, and `CorsPreflightPolicy::kPreventPreflight`. Cross-origin streams need `Access-Control-Allow-Origin` on the stream response (and on reconnects); `withCredentials: true` needs an explicit origin (not `*`) plus `Access-Control-Allow-Credentials: true`.

That GET-and-cookies surface disqualifies any API that takes a POST with an `Authorization` header. The workaround is to keep the *protocol* and drop the *client*: `fetch()` with any method, headers, and body, then parse `text/event-stream` off the response `ReadableStream`. You then own reconnect, `retry`, and `Last-Event-ID` yourself. Cookie + `withCredentials` is the EventSource-native path; a short-lived query token leaks via logs and `Referer`.

CORS is load-bearing on every hop, not just the first GET. Default `EventSource` is a simple GET and generally does not preflight. Reconnects that add `Last-Event-ID` also do not preflight in current Chromium (`kPreventPreflight`) — that is the hole whatwg/fetch#568 / #1788 are trying to close by safelisting the header under the 128-byte / no-unsafe-byte rules. Until that lands, treat the header as an untrusted cursor, never as a capability token.

## Scaling limits and fan-out

Each subscriber is one long-lived HTTP request: one file-descriptor, buffer, and request context for the life of the stream. Fan-out is connection-bound, not request-rate-bound. Horizontal scale needs a shared publish path ([pub/sub](PubSubQueues.md) or a log) plus a writer on each connection. WHATWG authoring notes: do not key identity on client IP (NATs and shared proxies).

**HTTP/1.1 sockets** are the client-side trap. RFC 9112 gives no number. Verified engine pools (not a web-wide constant):

- **Chromium** `g_max_sockets_per_group` = **6** for `kNormal`, **255** for `kWebSocket`. An SSE stream occupies a `kNormal` slot for its lifetime. Group id is origin-ish (scheme / host / port + privacy partition), shared across tabs in the same profile — six concurrent H1 streams to that group queue the seventh.
- **Firefox**: still "the browser standard max **6**" (`network.http.max-persistent-connections-per-server`); a 2025 experiment raising 6 → 12 produced dozens of regressions.
- **WebKit curl** backend: `CURLMOPT_MAX_HOST_CONNECTIONS` = **6**. Safari's Network.framework path is unverified.

WHATWG's own workaround list: unique hostnames, a per-page disable, or a **shared worker** sharing one `EventSource`.

**HTTP/2 and HTTP/3** multiplex SSE as an ordinary HTTP stream, which removes the *client H1* cap (RFC 9113: initially unlimited, recommend ≥ 100). They do not remove the *server* one-stream-per-subscriber cost. A proxy that downgrades upstream to HTTP/1.1 re-imposes H1 limits on that hop. HTTP/2 PING does **not** reset AWS ALB idle timeout — heartbeats must be payload bytes.

## Proxy buffering and idle teardown

Two distinct failures. **Buffering** holds events until a buffer fills or the response ends ("works on localhost, bursts in prod"). **Idle teardown** closes a quiet stream. Heartbeats fix the second, not the first.

| Hop | Default that kills SSE | Fix |
|---|---|---|
| **nginx** `proxy_buffering` | **on** | Per-location `off`, or per-response `X-Accel-Buffering: no` (ignored if listed in `proxy_ignore_headers`). Same header for FastCGI/uwsgi. |
| nginx `proxy_read_timeout` | **60 s** between upstream reads | A comment line is enough. Even unbuffered, nginx may coalesce up to `proxy_buffer_size` — framing lives in the **body text**, not in chunk edges. |
| **AWS ALB** idle | **60 s** (1–4000) | Send ≥ 1 byte of data before each idle period. H2 PING does **not** count. |
| ALB client keepalive | **3600 s** (60–604800) lifetime, then `Connection: close` / `GOAWAY` | A busy stream still dies at the lifetime cap. |
| **Cloudflare** origin read | **125 s** → HTTP 524 | Official table; the community "100 s" figure is not on the page. Client↔CF H1/H2 idle **400 s**. Origin idle 900 s → 520; write 30 s → 524. |
| **Azure Application Gateway** request timeout | **20 s** (1–86400 private; 1–240 external) | Disable **response buffering**; set the timeout above the idle gap. Recommended backend headers: `Content-Type: text/event-stream`, `Connection: keep-alive`, `Transfer-Encoding: chunked`, `Cache-Control: no-cache`. Containers SKU: idle **5 minutes**; docs recommend comment keepalives and Gateway API `timeouts.request: "0s"`. |
| **GCP** backend service timeout | **30 s** | On HTTP(S) Application LBs this is a **request/response deadline** (first request byte to last response byte), not an idle timer. A stream longer than 30 s dies unless the timeout is raised. |

Also send `Cache-Control: no-cache`: WHATWG's request cache mode is `no-store`, but intermediaries may not honour it, and nginx `proxy_cache` being off today does not bind a later cache layer. Compression middleware that waits for end-of-stream is another silent buffer — flush per event or skip compression on the stream path. Serverless and function max-durations are request deadlines, not idle timers; the stream cannot outlive them.

## SSE vs WebSocket vs long-polling

| | **SSE** (`EventSource`) | [WebSocket](WebSockets.md) | HTTP long-polling (RFC 6202) |
|---|---|---|---|
| Direction | Server → client on one HTTP response. Client→server is a *different* [request](RequestResponse.md). | Bidirectional frames after Upgrade / extended CONNECT. | Each cycle is request/response. Server holds until an event or a timeout; client opens the next immediately. |
| Binary | UTF-8 text. Binary must be encoded inside `data`. | Native binary and text frames. | HTTP body; any representation. |
| Reconnect + resume | **Built in**: auto-retry + `Last-Event-ID`. | Application-defined. No standard cursor. | The next poll. App puts a cursor in URL or body. |
| HTTP/2 | Yes — it is an HTTP stream. H2 removes the *client H1* socket cap. | Optional (RFC 8441). Many stacks still Upgrade on H1. Chromium uses a **separate** 255-socket WS pool. | Yes — ordinary HTTP requests. |
| Auth | Constructor: cookies / `withCredentials` only. `fetch()` streaming sends headers but loses automatic reconnect. | Browser `WebSocket()` also cannot set arbitrary headers. | Full HTTP headers, including `Authorization`. |
| Proxy fit | Looks like a long GET. Breaks when hops buffer or idle-timeout. No upgrade to allow-list. | Upgrade / 101 (or RFC 8441). Many L7 hops must explicitly support WS. | Every cycle is a complete response — works through almost any proxy. Highest request rate; RFC 6202 §5.5 timeout clash (408/504). 2011 advice: ~30 s is safer than a 300 s hold. |
| When it wins | Server-push of text events to browsers; auto-resume; stays on HTTP. | True duplex, binary, or client-initiated messages on the same socket. | Maximum compatibility; no long-lived stream state in the proxy. |

Rule of thumb: two-way interactivity → WebSocket; one-way feed → SSE; lowest-common-denominator intermediaries → long-polling with a hold under the shortest 408/504 on the path.

## Verified defaults

Fetched 2026-09-13. `EventSource` has no library trip-threshold analogue. The operational knobs are `retry`, heartbeat interval, proxy read/idle, buffering off, and whether `id`s are assigned.

| Knob | Value | Source |
|---|---|---|
| MIME / encoding | `text/event-stream`, UTF-8 only | WHATWG HTML §9.2 |
| Success status | 200 only; else fail | WHATWG `processResponse` |
| Stop reconnecting | non-200 (intro calls out 204) | WHATWG intro + fail rule |
| Cache mode / `withCredentials` | `no-store` / `false` | WHATWG constructor |
| Reconnect (Blink / Gecko) | 3000 ms / 5000 ms (min 500) | `event_source.cc` / `EventSource.cpp` |
| Authoring heartbeat | comment every ~15 s | WHATWG §9.2.7 |
| H1 client socket cap (Chromium) | 6 / group (`kNormal`); 255 (`kWebSocket`) | `client_socket_pool_manager.cc` |
| H2 stream cap | initially unlimited; recommend ≥ 100 | RFC 9113 §6.5.2 |
| nginx buffering / read timeout | `proxy_buffering on`; `proxy_read_timeout` 60 s | nginx proxy module |
| ALB idle / keepalive / H2 PING | 60 s / 3600 s / PING does not reset idle | AWS ELB ALB attributes |
| Cloudflare origin read | 125 s → 524 | CF connection-limits |
| Azure App Gateway request timeout | 20 s default; disable response buffers for SSE | Azure Backend Settings + SSE page |
| GCP backend service timeout | 30 s (request/response deadline on HTTP(S) ALB) | GCP backend-service docs |
| Spring `SseEmitter` timeout | unset → MVC async timeout → servlet container default | Spring Framework 7.0.7 Javadoc |

## Failure modes

- **The silent buffer.** Default-on proxy buffering, App Gateway response buffers, gzip that waits for EOS. Heartbeats do not fix this. Put `X-Accel-Buffering: no` (and do not list it in `proxy_ignore_headers`) in the handler, not the runbook.
- **Death by idle timer — or by total deadline.** ALB/nginx 60 s idle, CF origin 125 s, Azure 20 s, GCP 30 s *total*. Comment heartbeats must be **payload bytes**. A function max-duration is not an idle timer.
- **Cursor theater.** Sending `id:` without server-side replay gives clients a resume header the server ignores — at-least-once quietly becomes at-most-once on every blip. Empty `id:` clears the cursor.
- **H1 connection starvation.** Six Chromium `kNormal` sockets per group, shared across tabs. A seventh `EventSource` or a page that also needs XHR hangs. H2 end-to-end is the structural fix; a Shared Worker is the WHATWG-documented H1 workaround.
- **Fatal MIME/status.** A 200 HTML error page or a 502 **fails** the `EventSource`. Operators see a single `error` and a dead widget.
- **Reconnect stampede.** Fixed 3 s / 5 s delays, spec backoff optional, Blink adds no jitter.
- **Process-local fan-out.** In-memory publish plus a multi-instance LB without sticky routing or a replay log: reconnects miss events. Sticky hides it until drain.
- **Auth hole / log leak.** Query-string tokens appear in access logs and `Referer`. Cookie auth needs CORS credentials on every hop.

## When not to use SSE

- The client must **send** messages on the same connection → [WebSocket](WebSockets.md) (or WebTransport). Extra POSTs can fake duplex but lose ordering and head-of-line coupling.
- Native **binary** frames or a compact binary protocol → WebSocket.
- The browser must send **`Authorization`** (or any non-cookie header) and you will not implement `fetch()` streaming plus your own reconnect → do not use `EventSource`.
- Server-to-server push with retries, signatures, and at-least-once delivery → [webhooks](Webhooks.md), not a held HTTP stream.
- A single request/response is enough → [request–response](RequestResponse.md).
- Intermediaries cannot disable response buffering and cannot be bypassed (locked-down corporate proxies / some CDNs). Long-polling degrades more gracefully there (RFC 6202).
- Subscriber count × hold-time exceeds file-descriptor / thread / serverless concurrency and there is no plan for a shared log plus a connection-bearing tier.
- Missed events must survive an absent consumer → that is a [queue](PubSubQueues.md), not a stream.

## Trade-offs

| Buy | Pay |
|---|---|
| Plain HTTP: cookies, routing, LBs, tracing all free | One direction only; client-to-server goes back over HTTP |
| Built-in reconnect + resume cursor | The server must implement the replay half (and a log, to honour it across replicas) |
| Forward-compatible framing, trivial to emit | UTF-8 only; base64 for anything binary |
| No protocol upgrade to allow-list | Buffering and idle (and *total*) timers must be engineered away hop by hop |
| Least new protocol of the three push shapes | GET-only `EventSource`; header-rich APIs own their own reconnect |

SSE is the right default for feeds, progress, and one-way text streams. The moment the client must *talk back* on the same channel, it is a [WebSocket](WebSockets.md). The moment missed events must survive an absent consumer, it is a [queue](PubSubQueues.md). The moment the path cannot be talked out of buffering, it is long-polling.

## Sources

Verified 2026-09-13; full URLs, per-claim provenance, and items deliberately left out (Safari Network.framework cap, live Firefox `StaticPrefList.yaml`, Fetch PR #1788 landing, CF "100 s" claim, RFC 6202's 2011 "300 s browser default" as a 2026 fact, HAProxy/Envoy idle left to the gateway and [timeouts](TimeoutsDeadlines.md) notes) are in the [external research note](../../docs/research/sysdesign/a4-sse-external-research.md).

- Canon: WHATWG HTML §9.2 (snapshot "Last Updated 20 July 2026"); W3C Rec *Server-Sent Events* (2015-02-03); WHATWG Fetch (CORS-safelisted headers; #568 / #1788); RFC 9112 §9.4; RFC 9113 §6.5.2; RFC 6202; RFC 6455 (comparison only).
- Browsers: MDN `EventSource` / "Using server-sent events"; Chromium `event_source.cc` and `client_socket_pool_manager.cc`; Gecko `EventSource.cpp`; Bugzilla 1954844; WebKit changeset 279864.
- Proxies / LBs: nginx `ngx_http_proxy_module`; AWS ELB Application attributes; Cloudflare connection-limits (updated 2026-07-23); Azure Application Gateway SSE and Backend Settings; Azure Application Gateway for Containers SSE; GCP backend-service; Spring `SseEmitter` 7.0.7 Javadoc.
- Idle vs request vs total timers cited via the [timeouts note](../../docs/research/sysdesign/timeouts-deadlines-external-research.md); pinning and drain via the [load-balancing note](../../docs/research/sysdesign/load-balancing-external-research.md).
