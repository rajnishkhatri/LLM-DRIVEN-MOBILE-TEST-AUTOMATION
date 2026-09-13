---
type: research
title: 'Server-sent events — external research (2026-09-13)'
description: >-
  Source-verified research backing the SSE Concept (A4): the WHATWG
  text/event-stream protocol (fields, UTF-8, reconnection with browser-source
  defaults 3 s/5 s, the 204 stop rule, Last-Event-ID), EventSource constraints
  and the fetch-parse alternative, the h1 six-connection cap vs h2 streams,
  proxy buffering and heartbeat fixes, resumability semantics, the
  WS/SSE/long-polling comparison, and SSE as the LLM streaming transport
  including Anthropic/OpenAI event taxonomies and MCP's resumability retreat.
tags: [research, sse, server-sent-events, streaming, llm, system-design-patterns]
---

# A4 Server-sent events — external research (2026-09-13)

**Method.** Facts verified against primaries 2026-09-13; paraphrase; ≤ 1 quote per source. **[→timeouts]** cites forward to [timeouts-deadlines-external-research.md](timeouts-deadlines-external-research.md).

## 1. Wire protocol (WHATWG HTML, server-sent events section)

- `text/event-stream`; line-based: blank line dispatches; a line starting with `:` is a comment (the keepalive primitive); fields `data:` (joined with LF across consecutive lines), `event:` (named events vs onmessage), `id:` (sets the last-event-ID buffer; ignored if it contains NULL; a bare `id:` **resets** it), `retry:` (ASCII digits = reconnection time in ms); unknown fields ignored (forward-compatible). **UTF-8 only** — no other encoding.
- **Reconnection**: spec says implementation-defined "a few seconds"; browser sources: Chromium `kDefaultReconnectDelay = 3000`, Firefox `DEFAULT_RECONNECTION_TIME_VALUE 5000` (min clamp 500). The spec blesses waiting longer after failures (backoff allowed; `retry:` is a floor).
- **Last-Event-ID**: sent on reconnect when the buffer is non-empty.
- **Stop rule**: reconnection stops on **HTTP 204** (also: non-200 status or wrong Content-Type fails the connection → CLOSED, no retry; server-closed connections reestablish). Redirects followed.
- readyState: CONNECTING (0) / OPEN (1) / CLOSED (2).

## 2. EventSource constraints and the fetch alternative

- Constructor surface = URL + `withCredentials`; cache no-store. Constraints (fetch-event-source README): **GET only, no custom headers, no body**; no retry control. UTF-8 only ⇒ no binary.
- The workaround everyone uses: `fetch()` + incremental parse of `response.body` — any method/headers/body, response validation before parsing, custom retry, Last-Event-ID preserved. `@microsoft/fetch-event-source` is the reference (repo alive, last npm release 2.0.1 of 2021 — dormant). LLM SDKs implement this pattern because provider APIs are POST (§7).

## 3. HTTP-version interaction

- The HTML spec itself warns about per-server connection limits with multiple tabs (suggests unique domains or a SharedWorker). MDN quantifies: **not over HTTP/2 the limit is 6 per browser+domain** (Chrome/Firefox won't-fix); over h2 the negotiated stream limit defaults ~100 (RFC 9113: initially unlimited, "no smaller than 100" recommended). One hanging SSE eats one of ~6 h1 connections — dashboards deadlock tabs; over h2/h3 it is one stream of 100+.

## 4. Proxy and infrastructure pitfalls (each with its knob)

- RFC 6202: intermediaries may legally buffer entire responses — streaming dies there.
- **NGINX**: `proxy_buffering` default on; fix per-location (`proxy_buffering off`) or per-response with the **`X-Accel-Buffering: no`** response header (verified); even unbuffered, `proxy_read_timeout` 60 s is a between-reads timer **[→timeouts]**.
- **Compression middleware buffers**: expressjs/compression documents SSE breakage and `res.flush()` per event.
- Edge timers cite forward: CloudFront 30 s per-wait; ALB 60 s idle; undici bodyTimeout 300 s between chunks **[→timeouts]**.
- **Heartbeats**: the spec's authoring note — proxies drop idle connections; send a comment line about every **15 seconds**. MCP (2026-07-28) encodes both fixes: servers SHOULD send `X-Accel-Buffering: no` and are encouraged to send comment keepalives. Rule: the heartbeat must beat the shortest idle timer on the path (hence 15–30 s vs the 30–60 s edge timers — synthesis).

## 5. Resumability

- Client side is spec'd: the UA remembers `id:` across reconnects and replays it as Last-Event-ID; the value is opaque. Server side is yours: treat it as a cursor, buffer or re-derive events-since-id. MCP's Streamable HTTP (2025-06-18) is the cleanest statement: ids unique per session, cursor within one stream, replay only on the disconnected stream. Yield = **at-least-once** with dedupe-by-id possible (synthesis). Server-controlled edges: NULL-containing id ignored; bare `id:` clears the cursor. Contrast WebSocket: no protocol reconnect/resume at all (RFC 6455 only advises client backoff).

## 6. WS vs SSE vs long-polling

| | WebSocket | SSE | Long-polling |
|---|---|---|---|
| Direction | Two-way | Server→client | Server→client via held response |
| Transport | Own protocol after Upgrade; needs RFC 8441/9220 for h2/h3 | Plain HTTP body — h1/h2/h3 unchanged; h1 costs one of ~6 connections | Plain request/response |
| Reconnect/resume | None in protocol; app rebuilds | **Built in**: auto-retry (3 s/5 s, `retry:`) + Last-Event-ID cursor | The next poll is the mechanism; app cursors |
| Headers/auth/body | No headers from the browser API | EventSource GET-only/no headers; fetch-parse frees it | Full freedom |
| Proxies | Upgrade/CONNECT can be blocked | Buffering + idle timers must be handled | Most compatible; per-request overhead |
| Binary | Native | None (UTF-8) | Any |
| Cost | Handshake once, minimal framing | One request then bytes; ~15 s comments | Full RTT + headers per message; ≥ 3 transits worst case (RFC 6202) |

Long-polling (RFC 6202): hold the request until update or timeout; ~**30 s** is the safe timeout (intermediaries kill longer); weaknesses = header overhead, 3-transit worst case, one held connection per client.

## 7. SSE as the LLM streaming transport

- **Anthropic**: named events — message_start → per block content_block_start / content_block_delta (text_delta, input_json_delta, thinking_delta, signature_delta) / content_block_stop → message_delta (stop_reason, usage) → message_stop; interspersed **ping** events; **in-band `event: error`** (e.g. overloaded_error) after the 200; "handle unknown event types gracefully"; SDKs require streaming for large max_tokens **[→timeouts]**.
- **OpenAI**: Chat Completions chunks over SSE ending with the **`data: [DONE]`** sentinel (verified in the SDK source and Azure transcripts); `stream_options.include_usage` for the final usage chunk; SDK raises on in-band `error` events; the Responses API moves to typed semantic events (response.created / output_text.delta / completed / error) — converging on named events.
- Both APIs are POST ⇒ SDKs are fetch-parse SSE, not EventSource.
- **Why SSE won** (labeled synthesis): token generation is one-way small text deltas; a 200-with-long-body inherits HTTP auth/routing/observability; flowing deltas feed the between-byte timers, pings cover silences; in-band error events solve already-sent-200. Resume cursors are not documented by the big APIs — a dropped stream is a new request and re-billed tokens.
- **MCP**: Streamable HTTP replaced HTTP+SSE (2025-03-26); 2025-06-18 had GET listening streams, sessions, and Last-Event-ID resumability; the **2026-07-28 revision removes them — "Resumable SSE streams via Last-Event-ID are not supported"** — SSE remains as per-request response streams + subscriptions/listen; spec recommends X-Accel-Buffering: no + comment keepalives. Arc: full resumability adopted, then walked back within ~16 months.

## Sources

WHATWG HTML server-sent-events · MDN EventSource + Using SSE · Chromium event_source.cc (3000) · Firefox EventSource.cpp (5000/500) · nginx proxy module (X-Accel-Buffering) · RFC 9113 · RFC 6202 · RFC 6455 §7.2.3 · RFC 9220 · @microsoft/fetch-event-source (repo + npm) · expressjs/compression README · platform.claude.com streaming docs · developers.openai.com streaming reference + guide + openai-python _streaming.py · Azure OpenAI content-streaming (2026-09-08) · modelcontextprotocol.io transports 2025-06-18 + 2026-07-28 + versioning. Cited forward: timeouts-deadlines-external-research.md.

## Uncertain / could not verify (excluded from the Concept)

- "GET" is by Fetch default, not a literal spec word.
- Browser WS header limitation not re-verified here (see the WebSocket note).
- fetch-event-source: dormant, not archived.
- Heartbeat 15–30 s band is synthesis over the spec's ~15 s + edge timers.
- "h2 defaults to 100 streams" is MDN's characterization; RFC recommends ≥ 100.
- OpenAI first-party [DONE] prose unfetchable; verified via SDK + Azure.
- Whether Anthropic error events terminate the HTTP stream is unstated (SDKs stop).
