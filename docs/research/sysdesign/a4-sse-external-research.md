---
type: research
title: 'Server-sent events — external research (2026-09-13)'
description: >-
  Source-verified research for catalog A4: WHATWG EventSource wire format
  (text/event-stream, id/event/data/retry, Last-Event-ID, CORS,
  withCredentials), connection lifecycle, HTTP/1.1 vs HTTP/2 limits,
  proxy/LB buffering and idle timers, and SSE vs WebSocket vs long-polling.
tags: [research, system-design-patterns, a4, sse]
---

# Server-sent events — external research (2026-09-13)

> **What this is.** The evidence pass for catalog topic **A4** (Group A —
> Communication). It is not a Concept. Group A bar: wire semantics, connection
> lifecycle, scaling limits and fan-out, failure and reconnect, proxy/LB
> interactions, verified defaults, when-not-to-use.
>
> **Method.** Primary pages fetched 2026-09-13. WHATWG HTML §9.2 is the
> protocol SoT (living standard; the SSE chapter snapshot said "Last Updated
> 20 July 2026"). Browser numeric limits are taken from engine source or
> vendor docs, not from Stack Overflow restatements. Items that could not be
> pinned are in §8 and are **not** to be implied as fact.

---

## 1. Scope and non-goals

**Owns.** Browser and HTTP `EventSource` / `text/event-stream`: field grammar,
ready-state machine, automatic reconnect and `Last-Event-ID`, CORS /
`withCredentials`, the HTTP/1.1 per-origin socket interaction, HTTP/2 stream
concurrency, proxy buffering and idle teardown, and the comparison with
WebSocket and HTTP long-polling.

**Does not own.** Request–response semantics and REST/gRPC sync (A1). Broker
fan-out, competing consumers, DLQ (A2). WebSocket framing, ping/pong, sticky
sessions as a first-class topic (A3 — cited only for the comparison table).
Webhooks and callback signing (A5). LB algorithms (C5), gateway/BFF placement
(C6), and the general timeout/deadline catalogue (C7) — this note cites their
idle/read numbers only where they break SSE.

**Non-goals.** Inventing a universal "6 connections" as an HTML or HTTP
requirement. Writing exploits around the `Last-Event-ID` CORS hole. Library
SDKs beyond the few defaults needed to operate a stream.

---

## 2. Lineage / vocabulary

**WHATWG HTML Living Standard, §9.2 Server-sent events.** Canon for
`EventSource`, the `text/event-stream` ABNF, field processing, announce /
reestablish / fail, and the `Last-Event-ID` request header. Retrieved
2026-09-13 from `html.spec.whatwg.org/multipage/server-sent-events.html`.

**W3C Recommendation *Server-Sent Events*, 2015-02-03**
(`TR/2015/REC-eventsource-20150203`). Snapshot of the same design; the
current `https://www.w3.org/TR/eventsource/` page now redirects at the WHATWG
HTML document. Use WHATWG for normative behaviour; cite the Rec only for
lineage.

**WHATWG Fetch.** `EventSource` construction creates a potential-CORS request
(Anonymous, or Use Credentials when `withCredentials` is true), sets cache
mode "`no-store`", and may set `Accept: text/event-stream`. CORS-safelisted
request headers (fetched 2026-09-13) are `accept`, `accept-language`,
`content-language`, `content-type` under value constraints — **`Last-Event-ID`
is not on that list**. whatwg/fetch#1788 (2025) proposes adding it; it had
not landed in the living Fetch text fetched this day.

**RFC 9112 HTTP/1.1 §9.4 Concurrency (June 2022).** A client "ought to limit"
simultaneous connections to a given server. Earlier HTTP revisions gave a
numeric ceiling (RFC 2616's two); 9112 **mandates no number** and tells
clients to be conservative.

**RFC 9113 HTTP/2 §6.5.2 (June 2022).** `SETTINGS_MAX_CONCURRENT_STREAMS`
(0x03): initially there is **no limit**; it is recommended the value be no
smaller than **100**. MDN's "defaults to 100" is an implementation convention,
not the RFC initial value.

**RFC 6455 The WebSocket Protocol (December 2011)** and the WHATWG WebSockets
API: bidirectional framed messages; separate from SSE. Chromium keeps
WebSocket sockets in a different pool (255 per group vs 6 for ordinary HTTP).

**RFC 6202 (April 2011), informational.** *Known Issues and Best Practices
for the Use of Long Polling and Streaming in Bidirectional HTTP.* Distinguishes
short polling, long polling (server holds the request until an event or a
timeout), and HTTP streaming. §5.5: long-poll timeout ought to be high, but
too high yields 408/504; the document's then-current "browser default" of
300 s and the "generally 30 s is safer" advice are 2011 statements (see §8).

**MDN `EventSource` / "Using server-sent events".** Baseline-widely-available
since January 2020; IE never shipped it. Useful for examples (`X-Accel-Buffering:
no` in the PHP sample) and the HTTP/2 warning. The "6 connections / won't fix"
paragraph cites Stack Overflow — **do not treat that paragraph as the
measurement**. Engine sources below are.

---

## 3. Mechanics (Group A depth bar)

### 3.1 Wire semantics

The response MIME type **must** be `text/event-stream`. The stream is always
UTF-8; there is no encoding switch. Lines end in CRLF, LF, or CR. A leading
UTF-8 BOM is stripped.

An event is one or more `field` / `comment` lines terminated by a **blank
line**. End-of-stream without that blank line **discards** the incomplete
event. Field names are compared literally (no case folding). Unknown fields
are ignored.

| Field | Effect |
|---|---|
| `data` | Append value + LF to the data buffer. Multiple `data` lines concatenate with newlines; a trailing LF is stripped on dispatch. |
| `event` | Set the event-type buffer. Empty → dispatch as `message`. Named types require `addEventListener(name)`; `onmessage` does **not** see them. |
| `id` | If the value contains no U+0000, set the last-event-ID **buffer**. An `id` field with an empty value resets the last event ID to `""` (so the next reconnect sends **no** `Last-Event-ID`). |
| `retry` | If the value is only ASCII digits, set reconnection time (ms). Otherwise ignore. |
| `:` comment | Ignored. Used as a keep-alive (WHATWG authoring notes: every **15 seconds** or so against legacy proxies). |

Dispatch (browsers): copy last-event-ID buffer → event-source last event ID
(the buffer is **not** cleared, so later events without `id` still expose the
previous id on `MessageEvent.lastEventId`); if data is empty, reset data and
event-type buffers and return (comments-only blocks fire nothing); else fire
`MessageEvent` with `origin` = final URL origin after redirects.

`Last-Event-ID` is a request header on **reestablish** only, UTF-8, and
(WHATWG, issue #7363 still open) essentially any UTF-8 string except NUL / LF
/ CR. It is not sent when the last event ID string is empty.

Request shape from the constructor: GET-equivalent fetch, cache `no-store`,
optional `Accept: text/event-stream`. The IDL options dict has one member:
`withCredentials` (default `false` → credentials mode not `include`; Chromium
uses `same-origin` vs `include`). There is **no** spec hook for custom
headers or a method other than GET. Chromium's `EventSource::Connect`
hard-codes `GET`, `Accept: text/event-stream`, and
`CorsPreflightPolicy::kPreventPreflight`.

CORS: cross-origin streams need `Access-Control-Allow-Origin` on the **stream
response** (and on reconnects). `withCredentials: true` requires an explicit
origin (not `*`) plus `Access-Control-Allow-Credentials: true`. Default
`EventSource` is a simple GET; it generally does not preflight. Reconnects
that add `Last-Event-ID` also do not preflight in current Chromium
(`kPreventPreflight`). That is the hole whatwg/fetch#568 / #1788 are trying
to close by safelisting the header under the 128-byte / no-unsafe-byte rules.

### 3.2 Connection lifecycle

`readyState`: `CONNECTING` (0) at construction → `OPEN` (1) after announce →
`CLOSED` (2) after `close()`, a fatal fail, or document teardown.

Constructor: parse URL (else `SyntaxError`); build the potential-CORS
request; `fetch` with `processResponse` / `processResponseEndOfBody`.

`processResponse` (WHATWG):

1. Aborted network error → **fail** (CLOSED + `error`, no reconnect).
2. Other network error → **reestablish**, unless the UA knows it is futile.
3. Status **≠ 200** **or** `Content-Type` is not `text/event-stream` → **fail**.
4. Else announce (`open`) and parse the body line by line.

The non-normative intro states that **204 No Content** tells the client to
stop reconnecting. That follows from (3): 204 is not 200, so the connection
fails. Chromium additionally rejects a 200 whose MIME is not exactly
`text/event-stream`, and rejects a non-empty charset other than UTF-8.

`processResponseEndOfBody`: if the response is **not** a network error,
reestablish. A clean server close of a 200 stream therefore reconnects.

**Reestablish:** queue `error`, set `CONNECTING`, wait the reconnection time,
optionally wait more (spec permits exponential backoff or waiting for OS
connectivity — **optional**, not required), then fetch again, attaching
`Last-Event-ID` when the last event ID string is non-empty.

**Fail:** `CLOSED` + `error`; no further reconnect. `close()` aborts in-flight
fetch and sets `CLOSED`. Forcible close when the `Document` goes away.
Garbage-collection of an open `EventSource` must abort the fetch.

GC roots: strong reference from `Window`/`WorkerGlobalScope` while
`CONNECTING` (if `open`/`message`/`error` listeners exist) or `OPEN` (if
`message`/`error` listeners exist), and while a task is queued on the remote
event task source.

### 3.3 Scaling limits and fan-out

**Server cost.** Each subscriber is one long-lived HTTP request: one
file-descriptor / buffer / request context for the life of the stream. Fan-out
is connection-bound, not request-rate-bound. Horizontal scale needs a shared
publish path (broker or log) plus a writer on each connection. `Last-Event-ID`
resume across replicas additionally needs a **replayable log**, not
fire-and-forget pub/sub — otherwise a reconnect that lands on another instance
cannot honour the header. Sticky sessions are then a substitute, not a
requirement; they become required only when the event buffer is process-local
(same placement trade-off as A3 WebSocket). WHATWG authoring notes: do not
key identity on client IP (NATs and shared proxies).

**Client HTTP/1.1 sockets.** RFC 9112 gives no number. WHATWG authoring notes
only that "clients that support HTTP's per-server connection limitation"
starve when many pages each open an `EventSource` to the same host, and
suggest unique hostnames, a per-page disable, or a **shared worker** sharing
one `EventSource`.

Verified engine numbers (not a web-wide constant):

- **Chromium** `net/socket/client_socket_pool_manager.cc` (HEAD, fetched
  2026-09-13): `g_max_sockets_per_group` = **6** for `kNormal`, **255** for
  `kWebSocket`; comment: "Default to allow up to 6 connections per host"
  (crbug.com/12066). Soft cap per pool 256. Group id is origin-ish (scheme /
  host / port + privacy / NAK), not "tabs independently". An SSE stream
  occupies a `kNormal` slot for its lifetime, so six concurrent H1 streams to
  that group — across tabs in the same profile/network partition — queue.
- **Firefox:** Bugzilla 1954844 (2025) states the product still uses "the
  browser standard max **6** connections to a server for HTTP/1.1" via
  `network.http.max-persistent-connections-per-server`. An experiment raising
  6 → 12 produced "dozens of regressions". I did not re-read today's
  `StaticPrefList.yaml` value (§8).
- **WebKit curl backend:** `CURLMOPT_MAX_HOST_CONNECTIONS` set to **6**
  (changeset 279864, 2021). Apple's Network.framework path is a different
  code; treat Safari's current number as **unverified** (§8).

**HTTP/2 / HTTP/3.** SSE is ordinary HTTP; streams multiplex on one
connection. RFC 9113: no initial stream cap, recommend ≥ 100. This removes
the *client H1 socket* starvation, not the *server* one-stream-per-subscriber
cost. A proxy that downgrades upstream to HTTP/1.1 (`proxy_http_version 1.0`
and similar) re-imposes H1 limits on that hop. HTTP/2 PING does **not** reset
AWS ALB idle timeout (ALB docs, fetched 2026-09-13) — heartbeats must be
payload bytes.

**Auth at scale.** Cookie + `withCredentials` is the EventSource-native path.
Bearer tokens do not fit the constructor; common escapes are a short-lived
query token (leaks via logs/Referer) or `fetch()` + `ReadableStream` (custom
headers, but you own reconnect / `Last-Event-ID` / `retry`). Trade-off:
protocol automation vs header control.

### 3.4 Failure and reconnect

| Condition | WHATWG result |
|---|---|
| TCP/TLS drop, clean 200 close, most network errors | reestablish after reconnection time; `error` while `CONNECTING` |
| `close()`, abort, CORS/access-check fail (Chromium), wrong status/MIME | fail; `CLOSED`; no reconnect |
| HTTP 204 | fail (non-200) |
| 301 / 307 | intro: follow as normal HTTP; Chromium `DidFailRedirectCheck` aborts — treat redirect-on-stream as fragile (§8) |
| `retry: 5000` | reconnection time := 5000 ms |
| empty `id:` | last event ID := `""`; next reconnect omits the header |

Default reconnection time is **implementation-defined** ("probably a few
seconds"):

- Chromium / Blink: `kDefaultReconnectDelay = 3000` ms
  (`third_party/blink/renderer/modules/eventsource/event_source.cc`, HEAD).
- Gecko: `DEFAULT_RECONNECTION_TIME_VALUE 5000` ms, floor
  `MIN_RECONNECTION_TIME_VALUE 500` ms, pref
  `dom.server-events.default-reconnection-time`
  (`dom/base/EventSource.cpp`).

The spec *allows* extra backoff after a failed attempt; Chromium's
`ScheduleReconnect` uses the fixed `reconnect_delay_` with no extra jitter.
A fleet of browsers that drop together (LB idle, deploy) can therefore
re-issue in a 3 s or 5 s lockstep — pair with C2 retry-budget thinking on
the **server accept** path, not inside EventSource.

Resume is best-effort: the server must interpret `Last-Event-ID`. If events
were never given `id`s, the client cannot ask for a cursor. If the server
ignores the header, the client sees a gap or a full replay. At-least-once vs
at-most-once is an application contract on id uniqueness and replay.

### 3.5 Proxy / LB interactions

Two distinct failures: **buffering** (events arrive in a burst, or never,
until the response ends) and **idle teardown** (the hop closes a quiet
stream). Heartbeats fix the second, not the first.

**nginx `ngx_http_proxy_module`** (fetched 2026-09-13):

- `proxy_buffering` default **`on`**. Disabled per-location, or per-response
  by `X-Accel-Buffering: no` (ignored if listed in `proxy_ignore_headers`).
  Same header is documented for `fastcgi_buffering` / `uwsgi_buffering`.
- With buffering off, nginx still does not preserve chunk boundaries
  (nginx-devel, 2019-05): it forwards as received up to `proxy_buffer_size`,
  and may coalesce. SSE framing must be in the **body text**, not in HTTP
  chunk edges.
- `proxy_read_timeout` default **60s** — resets when *something* is read
  from upstream. A comment line is enough.
- `proxy_cache` default `off`. Still send `Cache-Control: no-cache` so a
  later cache layer does not store the stream (WHATWG cache mode is
  `no-store` on the request; intermediaries may not honour it).

**AWS ALB** (ELB Application attributes, fetched 2026-09-13):

- Connection idle timeout default **60 s**, range 1–4000 s
  (`idle_timeout.timeout_seconds`). "Send at least 1 byte of data before each
  idle timeout period elapses."
- HTTP/2 PING frames **do not** reset that idle timer.
- HTTP client keepalive default **3600 s** (60–604800): a *lifetime* cap,
  then `Connection: close` (H1) or `GOAWAY` (H2). An SSE stream that lives
  past this is torn down even if it is busy.

**Cloudflare** Fundamentals "Connection limits" (updated 2026-07-23, fetched
2026-09-13):

- Client↔CF: H1 keep-alive **400 s**, H2 idle **400 s**.
- CF↔origin: Proxy Read Timeout **125 s** → HTTP **524** (Enterprise-configurable);
  Proxy Idle Timeout **900 s** → 520; Proxy Write Timeout **30 s** → 524.
- Community posts often say "100 s". That number is **not** on this page;
  use 125 s for the official origin read limit (§8 for the 100 s claim).

**Azure Application Gateway.** Official SSE page (fetched 2026-09-13):
disable **response buffering**; set Backend Settings request timeout **above
the idle gap between events**. Recommended backend headers (not required by
App Gateway itself): `Content-Type: text/event-stream`, `Connection:
keep-alive`, `Transfer-Encoding: chunked`, `Cache-Control: no-cache`.
Request timeout default **20 s** (1–86400 private backend; 1–240 external) —
20 s will kill any quiet SSE stream. App Gateway for Containers: idle
timeout **5 minutes**; docs recommend `: keep-alive\n\n` and Gateway API
`timeouts.request: "0s"`.

**GCP Cloud Load Balancing** backend service timeout default **30 s**
(range 1–2,147,483,647). For HTTP(S) Application LBs this is a
request/response deadline (first request byte to last response byte), so an
SSE stream longer than 30 s is dropped unless the timeout is raised. That is
stricter than an idle timer.

**WHATWG authoring notes (non-normative):** comment every ~15 s; HTTP
chunking by an unaware layer can delay dispatch; disable chunking if that
hurts. MDN's PHP sample sets `X-Accel-Buffering: no`, `Cache-Control:
no-cache`, and `flush()` per event.

### 3.6 Comparison: SSE vs WebSocket vs long-polling

| | SSE (`EventSource`) | WebSocket (A3) | HTTP long-polling (RFC 6202) |
|---|---|---|---|
| **Direction** | Server → client on one HTTP response. Client→server is a *different* HTTP request (A1). | Bidirectional frames after an Upgrade / extended CONNECT. | Each cycle is request/response. Server holds the request until an event or a timeout; client immediately opens the next. |
| **Binary** | UTF-8 text. Binary must be encoded (e.g. Base64) inside `data`. | Native binary and text frames (RFC 6455). | HTTP body; typically JSON text, but any representation. |
| **Reconnect** | Automatic. `retry` sets the delay. `id` + `Last-Event-ID` is the resume cursor. | Application-defined. No standard last-event header. | Client re-issues. No standard resume header; the app must put a cursor in URL/body. |
| **HTTP/2 multiplexing** | Yes — it is an HTTP stream. H2 removes the *client H1* socket cap. | Optional: RFC 8441 bootstrapping via extended CONNECT. Many stacks still Upgrade on H1. Chromium uses a **separate** 255-socket WS pool. | Yes — ordinary HTTP requests. |
| **Auth** | Constructor: cookies / `withCredentials` only. No `Authorization` hook. `fetch()` streaming can send headers but loses automatic reconnect. | Browser `WebSocket()` also cannot set arbitrary headers; cookie, query, or first-frame token. | Full HTTP headers, including `Authorization`. Preflight rules apply if cross-origin + unsafe headers. |
| **Proxy fit** | Looks like a long HTTP GET. Breaks when hops buffer or idle-timeout. No protocol upgrade to allow-list. | Upgrade / 101 (or RFC 8441). Many L7 hops must explicitly support WS. Idle timers often differ from HTTP. | Every cycle is a complete HTTP response — works through almost any proxy. Higher request rate; RFC 6202 §5.5 timeout clash (408/504). |
| **When it wins** | Server-push of text events to browsers; auto-resume; stays on HTTP. | True duplex, binary, or client-initiated messages on the same socket. | Maximum compatibility; no long-lived stream state in the proxy. |

Trade-off summary: SSE is the least new protocol and the most reconnect-aware
browser API, at the cost of unidirectional text and header-poor auth. WS is
the duplex/binary tool and a different scaling/sticky problem (A3).
Long-polling is the compatibility fallback and the most request-amplifying
(C2/C7).

---

## 4. Verified defaults / standards

Fetched 2026-09-13 unless noted. Versions are page/source dates, not registry
releases.

| Knob | Value | Source |
|---|---|---|
| MIME / encoding | `text/event-stream`, UTF-8 only | WHATWG HTML §9.2.5–9.2.6 |
| Success status | 200 only; else fail | WHATWG `processResponse` |
| Stop reconnecting | non-200 (intro calls out 204) | WHATWG intro + fail rule |
| Cache mode | `no-store` | WHATWG constructor |
| `withCredentials` default | `false` | WHATWG |
| Reconnect default (Blink) | 3000 ms | Chromium `event_source.cc` |
| Reconnect default (Gecko) | 5000 ms (min 500) | Firefox `EventSource.cpp` |
| Authoring heartbeat | comment every ~15 s | WHATWG §9.2.7 |
| H1 client socket cap (Chromium) | 6 / group (`kNormal`); 255 (`kWebSocket`) | `client_socket_pool_manager.cc` |
| H1 concurrency (HTTP) | no mandated number | RFC 9112 §9.4 |
| H2 stream cap | initially unlimited; recommend ≥ 100 | RFC 9113 §6.5.2 |
| nginx `proxy_buffering` | `on` | nginx.org proxy module |
| nginx `X-Accel-Buffering` | `yes`/`no` overrides buffering | same |
| nginx `proxy_read_timeout` | 60 s | same |
| ALB idle timeout | 60 s (1–4000) | AWS ELB ALB attributes |
| ALB client keepalive | 3600 s (60–604800) | same |
| ALB H2 PING vs idle | PING does **not** reset idle | same |
| Cloudflare origin read | 125 s → 524 | CF connection-limits |
| Azure App Gateway request timeout | 20 s default | Azure Backend Settings |
| Azure App Gateway SSE | disable response buffers; timeout > idle gap | Azure SSE page |
| GCP backend service timeout | 30 s (request/response deadline on HTTP(S) ALB) | GCP backend-service docs |
| Spring `SseEmitter` timeout | unset → MVC async timeout → servlet container default | Spring Framework 7.0.7 Javadoc |
| RFC 6202 long-poll advice (2011) | 30 s "safer"; 120 s seen to work; browser XHR "300 s" then | RFC 6202 §5.5 |

`EventSource` itself has no library trip-threshold analogue. The operational
knobs are: `retry`, heartbeat interval, proxy read/idle, buffering off, and
whether `id`s are assigned.

---

## 5. Failure modes and when-not-to-use

**Failure modes of the mechanism.**

- **Buffered stream.** Default-on proxy buffering (`proxy_buffering on`,
  App Gateway response buffers, some CDN edges) holds events until a buffer
  fills or the response ends. Symptom: "SSE works on localhost, bursts in
  prod." Fix is hop-by-hop (`X-Accel-Buffering: no` *and* no
  `proxy_ignore_headers` eating it; App Gateway disable-buffering; no gzip
  that waits for EOS). Heartbeats do not fix this.
- **Idle cut.** ALB 60 s, nginx 60 s read, CF origin 125 s, Azure 20 s,
  GCP 30 s *total*. A quiet feed dies; EventSource reconnects and, without
  `id`s, repeats or skips. Comment heartbeats must be **payload bytes** (ALB
  ignores H2 PING).
- **H1 connection starvation.** Six Chromium `kNormal` sockets per group,
  shared across tabs. A seventh EventSource or a page that also needs XHR
  hangs. H2 end-to-end is the structural fix; a Shared Worker is the
  WHATWG-documented H1 workaround.
- **Fatal MIME/status.** A gateway error page (200 + `text/html`, or 502)
  **fails** the EventSource (no reconnect) if it is not 200 +
  `text/event-stream`. Operators see a single `error` and a dead widget.
- **Missing cursor.** No `id` → no `Last-Event-ID` → reconnect is a new
  subscription. Empty `id:` *clears* the cursor on purpose.
- **Reconnect stampede.** Fixed 3 s / 5 s delays, spec backoff optional,
  Blink does not add jitter. Pair with accept-side load shedding (C10) and
  C2 budgets.
- **Auth hole / log leak.** Query-string tokens appear in access logs and
  `Referer`. Cookie auth needs CORS credentials configured on every hop.
- **`Last-Event-ID` as an arbitrary request header.** A cooperating stream
  can plant an id and, on reconnect, redirect the next GET with that header
  (whatwg/html#689, whatwg/fetch#568). Do not treat the header as
  secret-bearing; do not trust it as an ACL.
- **Process-local fan-out.** Publish-in-memory plus a multi-instance LB
  without sticky routing or a replay log: reconnects miss events. Sticky
  hides the bug until a deploy drains the instance (C5/C3).
- **Serverless / request deadlines.** A 30 s LB deadline or a function
  max-duration is not an idle timer; the stream cannot outlive it.

**When not to use SSE.**

- The client must **send** messages on the same connection → A3 WebSocket
  (or WebTransport). Extra POSTs can fake duplex but lose ordering and
  head-of-line coupling.
- Native **binary** frames or a compact binary protocol → WebSocket.
- The browser must send **`Authorization`** (or any non-cookie header) and
  you will not implement `fetch()` streaming + your own reconnect → do not
  use `EventSource`.
- Server-to-server push with retries, signatures, and at-least-once delivery
  → A5 webhooks, not a held HTTP stream.
- A single request/response is enough → A1.
- Intermediaries cannot disable response buffering and cannot be bypassed
  (some locked-down corporate proxies / CDNs). Long-polling degrades more
  gracefully there (RFC 6202).
- Subscriber count × hold-time exceeds fd / thread / serverless concurrency
  and there is no plan for a shared log + connection-bearing tier.

---

## 6. Cross-links

**Catalog siblings.** A1 request–response (the client→server half, and
long-poll as repeated A1). A3 WebSocket (duplex, heartbeats, sticky, the
255 vs 6 Chromium pools). A5 webhooks (async server-to-server alternative).
C5 load balancing ([load-balancing-external-research.md](load-balancing-external-research.md)
— pinning, draining, H2). C6 gateway / BFF
([api-gateway-external-research.md](api-gateway-external-research.md) —
where to terminate the stream). C7 timeouts
([timeouts-deadlines-external-research.md](timeouts-deadlines-external-research.md)
— idle vs request vs total; ALB/nginx numbers here are the SSE-specific
slice).

**Existing `cases/` notes (main repo; do not re-derive).**
[rest-rpc-dataflow.md](../../../cases/data-intensive-design/rest-rpc-dataflow.md)
(HTTP as request/response).
[event-driven-dataflow.md](../../../cases/data-intensive-design/event-driven-dataflow.md)
(broker fan-out behind the SSE writer).
[timeouts-and-delays.md](../../../cases/data-intensive-design/timeouts-and-delays.md)
(timeouts are guesses; packet delay is unbounded).
Circuit breaker / retry Concepts are the accept-side complement to
EventSource's un-jittered reconnect
([CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md),
[RetryBackoff.md](../../../cases/SystemDesignPatterns/RetryBackoff.md)).

---

## 7. Sources

Retrieved 2026-09-13.

**Specs.** https://html.spec.whatwg.org/multipage/server-sent-events.html (WHATWG HTML §9.2; snapshot "Last Updated 20 July 2026") · https://html.spec.whatwg.org/dev/server-sent-events.html · https://www.w3.org/TR/2015/REC-eventsource-20150203/ · https://fetch.spec.whatwg.org/ (§ CORS-safelisted request-header) · https://www.rfc-editor.org/rfc/rfc9112.html#name-concurrency · https://www.rfc-editor.org/rfc/rfc9113.html (SETTINGS_MAX_CONCURRENT_STREAMS) · https://datatracker.ietf.org/doc/html/rfc6455 · https://www.rfc-editor.org/rfc/rfc6202.html

**Browsers.** https://developer.mozilla.org/en-US/docs/Web/API/EventSource · https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events · https://developer.mozilla.org/en-US/docs/Web/API/EventSource/withCredentials · https://chromium.googlesource.com/chromium/src/+/HEAD/third_party/blink/renderer/modules/eventsource/event_source.cc · https://chromium.googlesource.com/chromium/src/+/HEAD/net/socket/client_socket_pool_manager.cc · https://searchfox.org/firefox-main/source/dom/base/EventSource.cpp · https://github.com/mozilla-firefox/firefox/blob/dc6fa2e86c5a799a74cac11f7ffe639c41cbb142/dom/base/EventSource.cpp · https://bugzilla.mozilla.org/show_bug.cgi?id=1954844 · https://trac.webkit.org/changeset/279864/webkit · https://github.com/whatwg/fetch/issues/568 · https://github.com/whatwg/fetch/pull/1788 · https://github.com/whatwg/html/issues/7363

**Proxies / LBs.** https://nginx.org/en/docs/http/ngx_http_proxy_module.html · https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html · https://developers.cloudflare.com/fundamentals/reference/connection-limits/ · https://learn.microsoft.com/en-us/azure/application-gateway/use-server-sent-events · https://learn.microsoft.com/en-us/azure/application-gateway/configuration-http-settings · https://learn.microsoft.com/en-us/azure/application-gateway/for-containers/server-sent-events · https://docs.cloud.google.com/load-balancing/docs/backend-service · https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/web/servlet/mvc/method/annotation/SseEmitter.html

---

## 8. Uncertain / left out

- Safari / WebKit **Network.framework** per-host HTTP/1.1 cap today.
  `initializeMaximumHTTPConnectionCountPerHost()` was not read; only the curl
  backend's `CURLMOPT_MAX_HOST_CONNECTIONS = 6` is verified.
- Firefox `network.http.max-persistent-connections-per-server` **current
  StaticPrefList.yaml value**. 1954844 (2025) still describes it as 6; the
  file was too large to confirm a later flip.
- Whether every Chromium tab in a profile shares one `GroupId` for a given
  origin in all privacy / partition modes. The pool is per group, not
  "per browser" as MDN's SO paragraph says.
- MDN "issue marked Won't fix in Chrome and Firefox" — the specific bug IDs
  were not re-opened this pass.
- Blink/Gecko behaviour on **301/302/307** of an EventSource after the
  WHATWG intro's "301 and 307" sentence. Chromium `DidFailRedirectCheck`
  aborts; that may be stricter than the intro.
- Whether `Content-Type: text/event-stream; charset=utf-8` is accepted in
  **all** engines. Chromium accepts empty or UTF-8 charset; older Safari
  "suffix rejects" claims were not sourced to WebKit.
- Fetch PR #1788 landing date and whether any engine now preflights unsafe
  `Last-Event-ID` values on EventSource.
- Cloudflare **100 s** origin-read figure (community / secondary). Official
  table is **125 s** Proxy Read Timeout.
- RFC 6202's "browser default timeout is 300 seconds" as a **2026** fact.
  It is a 2011 informational statement; modern `fetch` / XHR defaults were
  not re-measured.
- HAProxy `timeout server` / `timeout tunnel` defaults; Envoy `idle_timeout`
  / `stream_idle_timeout` — left to C6/C7 rather than guessed.
- Node.js global `EventSource` (undici) reconnect default; `@microsoft/fetch-event-source`
  defaults. Not fetched.
- A controlled measurement of EventSource reconnect stampede amplitude.
- HTTP/3 SETTINGS analogue for concurrent streams as used by EventSource
  (SSE-over-H3 works as HTTP, but per-browser stream caps were not read).
- IANA `Last-Event-ID` registry row (W3C Rec §11.2 describes the
  registration; the live IANA page was not fetched).

---
