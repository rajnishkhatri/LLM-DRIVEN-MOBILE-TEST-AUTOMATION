---
type: research
title: 'Request–response (REST / gRPC) — external research (2026-09-13)'
description: >-
  Source-verified research backing the Request–response Concept (A1): RFC 9110
  status-code selection (202/204/206/303/409/412/422/425) and negotiation,
  async request-reply and AIP-151 long-running operations, gRPC unary wire
  anatomy (framing, trailers, channel states, fail-fast default, 4 MB limits,
  keepalive enforcement), gRPC-vs-REST selection, AIP-158/157 pagination and
  field masks, W3C Trace Context vs X-Request-ID, and mid-response/HOL/proxy
  failure modes.
tags: [research, request-response, rest, grpc, http, system-design-patterns]
---

# A1 Request–response (REST / gRPC synchronous semantics) — external research (2026-09-13)

**Method.** Facts verified against primaries 2026-09-13; paraphrase; identifiers exact. **[→timeouts] [→retry] [→apigw] [→shedding] [→idem] [→mesh-retry]** cite forward to the sibling notes in this directory (verified there; not re-fetched). *(analysis)* marks synthesis with no single primary.

## 1. HTTP semantics beyond methods (RFC 9110)

- **Resource vs representation** (§3): the request targets a *resource*; what travels is a *representation* of its state. Status codes describe the outcome against the resource; two GETs may lawfully return different representations.
- **Status codes a designer chooses between**: **202** accepted for processing, "the processing has not been completed" — intent, not success; no HTTP mechanism pushes the final status later, hence the status-endpoint contract (§2). **204** success, nothing to send. **206** only for Range requests, with Content-Range. **303** — retrieve the result **with GET** at another URI regardless of original method; the correct terminal redirect after POST (302 does not guarantee the method change; some clients replay the POST — Azure states this). **409** conflict with *current state* (edit conflict, duplicate create); the one 4xx that can be transient — Envoy's `retriable-4xx` class covers only 409 **[→retry]**; the Idempotency-Key draft uses it for an in-flight duplicate **[→retry]**. **412** a *client-supplied* precondition failed (If-Match optimistic concurrency **[→idem]**). **422** well-formed but semantically invalid (vs 400 malformed); the draft's "same key, different payload". **425 Too Early** (RFC 8470): TLS 1.3 0-RTT replay refusal; the client retries after the handshake, not in early data; only *safe* methods belong in early data.
- **Content negotiation** (§12): q-values 0–1, default 1, q=0 = not acceptable; server may send 406 or serve a default (paraphrase-level); every negotiated axis multiplies cache keys via Vary. *(analysis)* Machine-to-machine APIs pin one media type because negotiation buys nothing between contract-sharing clients and costs Vary-fragmented caches.

## 2. Long-running requests

- **Azure async request-reply** (ms.date 2026-03-30): validate then **202** + `Location` (status endpoint) + `Retry-After`; status endpoint returns **200 + status body** (status vocabulary Pending/Running/Succeeded/Failed/Canceled; createdAt; lastUpdatedAt; percentComplete; RFC 9457 error) while running; **303 See Other** to the result on completion (chosen to force GET); failures persisted at the result URL as 4xx + Problem Details. Considerations: dedicated status endpoint beats poll-target-until-not-404; retention + `Expires` on status resources; DELETE for cancellation (may need compensation); **require an idempotency key on submission** so a retried POST returns the existing status resource **[→idem]**; façade for legacy sync clients. Not for: real notification channels, streaming responses, broker-shaped workloads, persistent connections.
- **Google AIP-151** (2025-02-04): methods taking ~10 s+ return `Operation{name, metadata, done, error|response}`; `operation_info` declares types; poll via GetOperation (AIP-131: GET by name). Start-blocking errors return immediately; mid-flight failures land in `Operation.error`; conflicting parallels: `ABORTED` or queue.
- **When to switch**: mechanical against the edge ceilings — API Gateway REST 29 s (raisable Regional/private since 2024-06; edge no; HTTP APIs 30 s hard; no integration retries) **[→apigw][→mesh-retry]**; CloudFront 30 s per-wait; ALB 60 s idle **[→timeouts]**. p99 near the shortest ceiling ⇒ 202 + status resource, not raised timers everywhere.

## 3. gRPC unary anatomy

- **Framing** (PROTOCOL-HTTP2.md): 5-byte prefix (1B compressed flag + 4B big-endian length) per message; `:status` is always 200 and the outcome rides in **trailers** ("Status must be sent in Trailers even if the status code is OK"; `grpc-status` + percent-encoded `grpc-message`); Trailers-Only for early errors; `grpc-timeout` carries the deadline **[→timeouts]**. Rationale: only trailers can report an outcome computed after streaming the body.
- **Why trailers break the browser path**: browsers do not expose HTTP/2 framing (PROTOCOL-WEB's stated justification), so gRPC-Web re-encodes the trailer block inside the body (MSB-flagged frame). Intermediaries that fail to forward trailers destroy status reporting *(generalization beyond browsers: analysis)*.
- **Lifecycle** (Core concepts): client and server make independent local success determinations that can disagree (server OK after client deadline); either side may cancel; "changes made before a cancellation are not rolled back."
- **Channel states**: IDLE (entered after IDLE_TIMEOUT, given as 300 s) → CONNECTING → READY; TRANSIENT_FAILURE with exponential backoff; SHUTDOWN terminal.
- **Fail-fast is the default** (Wait-for-Ready guide): a failed channel fails RPCs immediately; wait-for-ready queues until READY, deadline still applies.
- **Message size**: grpc-go client/server receive default **4 MB**, send MaxInt32 (source constants); grpc-java `maxInboundMessageSize` **4 MiB** (javadoc, advisory). Cross-language contract: 4 MB receive both ends, effectively unlimited send — the *receiver* fails, raising is two-sided.
- **Keepalive** (keepalive.md): client PING **off by default** (`KEEPALIVE_TIME_MS` INT_MAX; server 2 h); `KEEPALIVE_TIMEOUT_MS` 20 s; `PERMIT_WITHOUT_CALLS` false; server enforcement `MIN_RECV_PING_INTERVAL_WITHOUT_DATA_MS` **5 min**; violations → **GOAWAY `ENHANCE_YOUR_CALM` / `too_many_pings`**. Turning client keepalive on to survive a 60 s LB idle **[→timeouts]** must be coordinated with server permits or it becomes periodic connection kills.

## 4. gRPC vs REST selection

- grpc.io FAQ: good fits — low-latency scalable distributed systems, mobile-to-cloud, new language-independent protocols, layered designs needing pluggable auth/LB/logging; deliberately swaps HTTP status/URI conventions for its own model; gRPC-Web GA.
- Microsoft comparison (2024-07-31): contract required (.proto) vs optional; HTTP/2; protobuf small/binary vs JSON; streaming client+server+bidi; **browser support: no (gRPC-Web required)**; codegen first-class. Recommended: microservices, real-time point-to-point, polyglot, constrained networks, IPC. Weaknesses: no direct browser calls; binary not human-readable; no broadcast concept.
- *(analysis, anchored)* REST's structural win: GET is safe **[→retry]**, so the HTTP cache/CDN estate accelerates it for free; gRPC's 200-always + trailers is opaque to that machinery.
- **gRPC-Web today** (README): unary + server-streaming only (server-streaming only in `grpcwebtext` base64 mode); "Client-side and Bi-directional streaming is not currently supported"; a proxy (Envoy grpc-web filter default) is required.

## 5. Pagination and partial responses

- **AIP-158**: `page_size` optional (0 → default; above max → **coerce down**; negative → INVALID_ARGUMENT); `page_token` "must be opaque (but URL-safe)", never parseable, never carries authorization (each page re-authorized); changing other args between pages → INVALID_ARGUMENT; **empty `next_page_token` is the only end signal** (never infer from a short page); token expiry allowed, ~3 days rule of thumb; `total_size` may be an estimate. Opacity rationale: evolution.
- **Stripe**: cursors are object ids (`starting_after`/`ending_before`, mutually exclusive); `limit` default 10, 1–100; `has_more`; auto-pagination in libraries. *(analysis)* Offset skips/duplicates under mutation and costs O(offset) — reasoning, not a cited sentence.
- **AIP-157**: read masks as *system parameters* (request-field read masks deprecated) or View enums (List defaults BASIC); absent mask = full resource.

## 6. Correlation and tracing

- **W3C Trace Context** (REC 2021-11-23): `traceparent = version-traceid-parentid-flags` (2+32+16+2 hex; all-zero ids forbidden; only the sampled flag defined); forwarding vendors MUST set parent-id to their own span — the header mutates per hop while trace-id persists; `tracestate` carries vendor pairs.
- **X-Request-ID is convention only**: NGINX defines just `$request_id` (16 random bytes hex; operators wire the header themselves); Heroku generates per request, honors client values 20–200 chars (letters/digits/+/=-), logs as `request_id`. No RFC. Use it for log correlation; use traceparent for tracing.

## 7. Failure modes

- **Mid-response failure after the status line** (RFC 9112 §8): chunked body incomplete without the zero chunk; short Content-Length = incomplete; close-delimited completion is indistinguishable from cut-off — never design unframed responses. Trailers are a weak failure channel in plain HTTP (client must send `TE: trailers`; recipients must not merge). HTTP/2 makes truncation explicit (END_STREAM vs RST_STREAM). *(analysis)* JSON-API detection ladder: framing violation first, parse failure last.
- **HOL blocking h1 → h2 → h3**: RFC 9113 — h2 removes application-layer HOL, "TCP head-of-line blocking is not addressed"; RFC 9114 — one lost TCP segment stalls all h2 streams; QUIC gives per-stream reliability; QPACK replaces HPACK because HPACK needs in-order delivery. Multiplexing changes *which* failures correlate.
- **Proxy buffering moves the clock** (NGINX, verified): `proxy_request_buffering on` reads the whole request body before the upstream sees it (upstream timers don't run during slow uploads; off → no failover after body bytes sent); `proxy_buffering on` frees the upstream fast and spools to disk **[→shedding]**; every buffering hop restarts "whose timeout is running" — budget unbuffered (SSE/gRPC) paths separately **[→timeouts]**.

## Sources

RFC 9110 · RFC 8470 · RFC 9112 · RFC 9113 · RFC 9114 · Azure async-request-reply (2026-03-30) · AIP-151 (2025-02-04), AIP-131, AIP-157 (2025-10-03), AIP-158 (2025-07-08) · grpc/grpc PROTOCOL-HTTP2.md, PROTOCOL-WEB.md, connectivity-semantics-and-api.md, keepalive.md · grpc.io core concepts, wait-for-ready, keepalive, FAQ · grpc-go v1.83.2 + server.go · grpc-java 1.84.0 javadoc · grpc-web README · learn.microsoft.com grpc/comparison (2024-07-31) · w3.org/TR/trace-context (2021-11-23) · nginx core + proxy modules · Heroku http-request-id (2026-01-28) · docs.stripe.com/api/pagination. Cited forward: timeouts-deadlines-, retry-backoff-, api-gateway-, mesh-proxy-retry-, load-shedding-backpressure-, idempotency-dedup-external-research.md.

## Uncertain / could not verify (excluded from the Concept)

- RFC 9110 verbatim sentences for 202's noncommittal wording and §12.1's 406-or-default (paraphrase only; do not quote).
- q-value three-decimal ABNF (state the range only).
- RFC 9113 Content-Length/DATA mismatch rule (omitted).
- grpc-java over-limit status (javadoc names none).
- grpc-go server defaults from master source constants.
- IDLE_TIMEOUT 300 s per-language variance unsurveyed.
- "Proxies drop trailers" generality; PROTOCOL-WEB trailer-specific wording (inference).
- gRPC status-code table not re-verified this pass.
- Media-type pinning and offset-pagination anomalies are analysis.
- Google Cloud API design guide not fetched.
- nginx proxy_http_version default change "since 1.29.7" not changelog-checked.
