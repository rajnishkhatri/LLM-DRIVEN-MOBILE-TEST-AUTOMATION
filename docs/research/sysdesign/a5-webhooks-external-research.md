---
type: research
title: 'Webhooks & callbacks — external research (2026-09-13)'
description: >-
  Source-verified Group A research on outbound HTTP webhooks: wire semantics,
  HMAC signing (Stripe, GitHub, Slack, Standard Webhooks), replay windows,
  vendor retry schedules, 2xx/4xx/5xx receiver contract, idempotent receivers,
  SSRF and endpoint verification, and webhook vs polling vs WebSocket.
tags: [research, system-design-patterns, a5, webhooks, callbacks]
---

# Webhooks & callbacks — external research (2026-09-13)

> **What this is.** Evidence pass for catalog **A5** (Group A). Not a
> Concept. Primary pages fetched 2026-09-13. Paraphrase; numbers exact.
> Unverified claims stay in §8. Retry formulas and idempotency-key
> semantics are **not** re-derived — [C2](retry-backoff-external-research.md)
> and sibling **C9**.

---

## 1. Scope and non-goals

**Owns.** Outbound HTTP callbacks (producer `POST` to a consumer-registered
HTTPS URL): wire semantics; connection lifecycle (no session to reconnect);
HMAC + timestamp replay windows; 2xx/4xx/5xx contract; producer retry
*schedules as published* (not jitter math); fan-out / scaling; proxy/LB
effects; endpoint ownership checks; producer-side SSRF *controls*
(high-level); webhook vs polling vs WebSocket.

**Does not own.** **A1** ordinary REST/gRPC. **A2** brokers / DLQ / ordered
streams. **A3/A4** WebSocket heartbeats and SSE `Last-Event-ID`. **C2**
Brooker jitter / SRE ~10% budgets / `4³=64` — cite only. **C9**
idempotency-key headers and Stripe's 24 h API-key store — this note only
names receiver duplicate keys. **C7** deadline propagation. **C4**
token-bucket math (Slack's 30k/h is a delivery cap only). No exploit
steps.

---

## 2. Lineage / vocabulary

**Webhook = HTTP callback / "reverse API".** Standard Webhooks spec
**v1.0.0** exists (Apache-2.0; github.com/standard-webhooks/standard-webhooks
`spec/standard-webhooks.md`, www.standardwebhooks.com). Producer calls
*the consumer's* HTTP server. A traditional API is common, not required.
Svix (Stripe-originated) uses the same HMAC (`whsec_`, `webhook-` /
`svix-` headers) plus optional `ed25519`.

**Fowler 2017-01-20** (martinfowler.com/articles/201701-event-driven.html):
Event Notification vs Event-Carried State Transfer = the spec's thin
(ids → A1 GET) vs full (snapshot, larger every delivery).

**AWS Architecture Blog, Gerring 2021-05-11:** polling the created
resource vs webhook (server-to-server) vs WebSocket (browser). §5.

**Signing practice (2026-09-13).** Stripe `t=`/`v1=` HMAC-SHA256; GitHub
`sha256=` hex; Slack `v0:timestamp:body` + 5 min window; Shopify
base64 HMAC-SHA256 of raw body. Nygard Integration Points (via C1/C2):
every callback has its own timeout and retry.

---

## 3. Mechanics (Group A depth bar)

### 3.1 Wire semantics

A delivery is one **HTTP POST** (occasionally documented as "the
request"), `Content-Type: application/json` in the vendors fetched
here, body = event payload, authenticity in **headers**, not in a
query secret.

| Producer | Auth headers | Signed content | Digest |
|---|---|---|---|
| **Stripe** | `Stripe-Signature: t=<unix>,v1=<hex>[,v0=…]` | `timestamp + '.' + raw JSON body` | HMAC-SHA256; ignore non-`v1` (downgrade) |
| **Standard Webhooks / Svix** | `webhook-id`, `webhook-timestamp`, `webhook-signature` (Svix default `svix-*`; white-label `webhook-*`) | `msg_id + '.' + unix_ts + '.' + raw body` | HMAC-SHA256 → base64 `v1,<sig>` (space-delimited list for rotation); optional `ed25519` / `v1a` |
| **GitHub** | `X-Hub-Signature-256: sha256=<hex>` (legacy `X-Hub-Signature` SHA-1) | raw body only (no timestamp in the MAC) | HMAC-SHA256 hex; UTF-8 |
| **Slack** | `X-Slack-Signature: v0=<hex>`, `X-Slack-Request-Timestamp` | `'v0:' + timestamp + ':' + raw body` | HMAC-SHA256 hex |
| **Shopify** | `X-Shopify-Hmac-SHA256` | raw body | HMAC-SHA256 → base64 |

**Raw body is load-bearing.** Stripe, GitHub, Slack, Shopify, and the
spec all require the exact bytes the producer signed. Re-parsing JSON
and re-serializing (whitespace, key order, Unicode) invalidates the
MAC. Frameworks that run `express.json()` / body parsers *before* the
webhook route are the documented failure mode (Stripe signature-
troubleshooting page; Shopify "raw body parsing"; Slack Flask
`request.get_data()`).

**Receiver contract (status codes).**

- **Success = 2xx** (200–299). Stripe, GitHub, Slack, Shopify, and
  Standard Webhooks agree. GitHub's own handler examples return
  **202**. Slack asks for `HTTP 200 OK` in prose but counts the
  200-series.
- **Anything else is a failed delivery** for Stripe (any non-`2xx`),
  Shopify ("any response outside the 200 range, **including 3XX**"),
  and Slack (`http_error` unless it is one of the two allowed
  redirects).
- **Standard Webhooks recommended etiquette** (spec, not a vendor
  SLA): `2xx` success; `3xx` failure (do not follow redirects — extra
  load); `410 Gone` → producer **disables** the endpoint; `429` →
  throttle; `502`/`504` → throttle (callee under load); honour
  `Retry-After` when present; remaining codes = failure.
- **Slack** will follow **up to two** `301`/`302`s in search of a
  200-series; more than two is `too_many_redirects`.
- **4xx vs 5xx is not a retry classifier at these producers.** Stripe,
  Shopify, and Slack retry on *any* non-success (including 400/401/403
  from a buggy verifier). A receiver that 401s a *valid* signed event
  because of a clock or raw-body bug will be retried and may trip
  auto-disable. Return **2xx after durable enqueue**; reserve 4xx for
  "this request must not be retried" only when the producer documents
  that (Slack's `x-slack-no-retry: 1` on a *non-200* response is the
  explicit escape hatch — it cancels **that event**, not the
  subscription).

**Acknowledge vs process.** Every vendor fetched here: return 2xx
*before* slow work. Stripe: "before updating a customer's invoice as
paid." GitHub: 2xx within **10 s**, then a queue (Resque / RQ /
RabbitMQ named). Slack: 2xx within **3 s**; "avoid actually processing
… in the same process." Shopify: 2xx quickly; **1 s** connect timeout,
**5 s** entire-request timeout; Keep-Alive enabled. If the 2xx is
sent before persist, a crash loses the event *and* the producer will
not retry — the C9-shaped fix is "persist-or-enqueue, then 2xx," not
"2xx then maybe write."

**Idempotent receivers (pointer, not C9).** At-least-once is the
delivery contract. Dedupe keys that stay stable across retries:

- Stripe: `Event.id` (`evt_…`); official undelivered-events guide:
  already-processed → ignore + **2xx** (stops further automatic
  retries). Snapshot events can arrive **out of order**; do not use
  `created` as a sequence number.
- Standard Webhooks: `webhook-id` is constant across retries; spec
  recommends treating it as the idempotency key (example: store ids
  ~5 minutes).
- GitHub: `X-GitHub-Delivery` GUID is **the same** on manual
  redelivery (docs: use it against replay; redelivery reuses it).
- Slack: envelope `event_id` (globally unique); retries add
  `x-slack-retry-num` `1|2|3` and `x-slack-retry-reason`. Dedupe on
  `event_id`, not the retry counter.
- Shopify: `X-Shopify-Webhook-Id` per delivery; `X-Shopify-Event-Id`
  shared across subscriptions of the same merchant action. Retries
  keep the original payload; use `X-Shopify-Triggered-At` (or a
  payload timestamp) to detect staleness.

How to *store* that key, conflict codes, and 24 h retention live in
**C9**.

### 3.2 Connection lifecycle

There is **no reconnect protocol**. Each attempt is a new HTTP
transaction:

1. Producer resolves DNS (re-resolve per attempt — SSRF §3.6).
2. TCP connect (Shopify: **1 s** connect timeout).
3. TLS 1.2+ handshake. Stripe requires TLS **v1.2 or v1.3** and
   validates the server certificate before sending. Slack classifies
   `ssl_error` separately. Slack also offers **mutual TLS**: the
   TLS-terminator requests a client cert under a DigiCert root; SAN
   or CN must be exactly `platform-tls-client.slack.com`; inject a
   header the app server trusts *only* from that terminator.
4. HTTP/1.1 POST. Shopify documents **Keep-Alive** reuse to the same
   host (receiver must enable it). No vendor fetched here requires
   HTTP/2.
5. Receiver reads the **raw** body, verifies, enqueues, 2xx.
6. Idle close. Next retry is a new connect; the *event* identity
   (id header) is what ties attempts together, not a socket.

**Timeouts (verified).** GitHub.com / GHEC: **10 s** to a 2xx or the
connection is terminated (`timed out`; GHES source text uses 30 s —
not re-verified on a GHES host). Slack Events API: **3 s**. Shopify:
**1 s** connect + **5 s** request. Standard Webhooks *recommendation*:
**15–30 s** (spec; not a library default). Stripe official docs: "quickly"
/ "Timed out" as a delivery error; **no seconds figure on the primary
page** (§8).

### 3.3 Scaling limits and fan-out

Fan-out on this channel is **N independent HTTPS POSTs**, one per
registered destination — not a broker subscription. Cost and
failure domains multiply with N.

| Producer | Fan-out / caps (fetched 2026-09-13) |
|---|---|
| **Stripe** | **16** webhook endpoints per account; HTTPS, publicly reachable. Same event can also go to Amazon EventBridge or Azure Event Grid (avoids HTTP fan-out). Thin vs snapshot payloads are **separate** destinations. |
| **Standard Webhooks** | Recommends multiple endpoints per customer (CRM + billing + chat). Payload **< 20 kB** recommended (no hard spec limit). |
| **GitHub** | Payload cap **25 MB** — oversize events are **not delivered**. Subscribe to the minimum event set. `GET /meta` → `hooks` CIDRs for allowlisting (values change; do not freeze a list). |
| **Slack** | One Events API request URL per app (HTTP mode) or Socket Mode (no public URL). **30 000** events / workspace / app / 60 minutes; overflow is an `app_rate_limited` callback every minute. Apps under 1 000 events/hour are not auto-disabled. |
| **Shopify** | HTTPS, or Google Pub/Sub / Amazon EventBridge (HMAC does not apply on the buses). Multiple subscriptions for one topic → one delivery each (different `Webhook-Id`, same `Event-Id`). |

**Receiver scaling.** Ingress must stay inside the producer timeout
(3–10 s typical). Burst absorption is a **queue behind the 2xx**
(Shopify: "queue webhooks to handle traffic bursts"; Slack: implement
a queue). The HTTP handler's unit of work is verify + persist + ack,
not the business transaction. Horizontal scale of that handler is
stateless if the dedupe store is shared (C9).

**Producer-side amplification.** One business event × N endpoints ×
retry attempts is open-loop load on the consumer. C2's lesson applies
on the *producer* worker pool: Full Jitter on the retry clock, a
retry budget so a down consumer cannot dominate the sender, one retry
layer. Do not stack client retries in front of Stripe/GitHub/Slack's
already-scheduled retries.

### 3.4 Failure and "reconnect" behavior

| Producer | Automatic retries | Give-up / disable | Manual / reconcile |
|---|---|---|---|
| **Stripe** | Live: up to **three days**, exponential backoff. Sandbox: **three** attempts over a few hours. New `t=` / `v1=` on **every** attempt. | Disabled/deleted destination → no further retries. Re-enable before the next attempt → retries continue. | Dashboard resend ≤ **15** days; CLI `stripe events resend` ≤ **30** days. List API `delivery_success=false` to backfill. Manual 2xx does **not** cancel the automatic schedule — receiver must 2xx the automatic retry too. |
| **GitHub** | **None.** Timeout (10 s) or non-2xx = failed delivery, period. | n/a | Redeliver last **3** days (UI or `POST .../deliveries/{id}/attempts`). Script: list deliveries, skip GUIDs that already have `status=OK`. |
| **Slack** | **3** retries: nearly immediately, **1 min**, **5 min**. Reasons: `http_timeout`, `too_many_redirects`, `connection_failed`, `ssl_error`, `http_error`, `unknown_error`. | **> 95%** of attempts in any of {SSL fail, >3 s, >2 redirects, non-200-series} over **60 min** → subscription temporarily disabled (email). Optional **Delayed Events**: hourly retries for **24 h**; default will not deliver an event **> 2 h** late. | Re-enable in app settings. `x-slack-no-retry: 1` on a non-200 stops that event. |
| **Shopify** | **8** retries over **4 hours**, exponential backoff. Original payload; original subscription URL (address changes mid-cycle are ignored). | After 8 consecutive failures, Admin-API subscriptions are **deleted**; emergency-developer email. | Re-create the subscription; reconcile via Admin API. |
| **Standard Webhooks (example schedule)** | Spec example: immediate, 5 s, 5 min, 30 min, 2 h, 5 h, 10 h, 14 h, 20 h, 24 h (elapsed 75 h 35 m 5 s). Recommends jitter (C2) and email + disable on persistent fail. | Recommendation only. | Visibility + manual replay called out as non-core but "immensely important." |

GitHub's lack of automatic retry is the architectural outlier: the
consumer must poll the Deliveries API or accept loss outside the
3-day manual window. Stripe/Slack/Shopify assume the opposite.

**Order and loss.** At-least-once, not in-order. Stripe snapshot
events "can arrive out of order." Shopify retries the *original*
payload (stale). Slack is "best-effort"; incidents can delay
delivery. Reconciliation (list events / Admin API / deliveries API)
is the closed loop when the retry window closes.

### 3.5 Proxy / load-balancer interactions

Signatures and timeouts fail at the edge more often than in handler
code.

- **Body mutation.** Any proxy that buffers, pretty-prints, gzip-
  re-encodes, or JSON-rewrites the body breaks HMAC. GitHub:
  "if you use a proxy or load balancer, make sure [it] does not
  modify the payload or headers." Stripe publishes an **API Gateway
  + Lambda** mapping template that must stash `$input.body` as
  `rawBody` (`$util.escapeJavaScript`) because the default JSON
  integration parses first.
- **TLS termination vs mTLS.** Slack mTLS is decided at the
  terminator. If an LB strips client certs, the app never sees
  `platform-tls-client.slack.com`. Injected SAN headers are only
  safe if the terminator overwrites them (Slack: check the header
  was not already present).
- **Idle / request timeouts at the LB** that are *shorter* than the
  producer's wait (ALB / NGINX / Envoy defaults — C7) turn a
  would-be 2xx into the producer's `timed out` / `http_timeout`.
  Shopify's 5 s budget is easy to blow with one extra hop.
- **Redirects.** Shopify treats 3xx as failure. Slack follows two.
  Standard Webhooks: do not follow; update the registered URL.
  An edge "HTTP→HTTPS 301" is a production outage for Shopify.
- **IP allowlists.** Complement, not a substitute, for signatures
  (IPs move). Stripe: live list at
  https://docs.stripe.com/ips and
  https://stripe.com/files/ips/ips_webhooks.txt (7-day notice via
  API-announce for IP changes). GitHub: `GET https://api.github.com/meta`
  field `hooks`. Allowlisting without signature verification fails
  when a neighbor on the same NAT is malicious; signatures without
  allowlisting still hold if the secret holds.
- **Keep-Alive and connection reuse** (Shopify): a pool of producer
  connections sits on the receiver. Sudden LB deregistration
  mid-reuse looks like `connection_failed` / RST, which *is*
  retried by Stripe/Slack/Shopify.

### 3.6 Endpoint verification and SSRF (high-level)

**Consumer proves they own the URL.**

- Slack `url_verification`: POST `{type, challenge, token}`; respond
  **200** with the `challenge` as text/plain, form, or JSON. Token
  field is deprecated; still verify the signing secret. SSL is
  checked as part of the handshake.
- GitHub `ping` (`X-GitHub-Event: ping`) on create; examples return
  2xx / 202 and do not treat it as repo activity.
- Stripe: CLI `stripe listen` / Workbench "send test event"; live
  endpoints must already be public HTTPS.

**Producer must not fetch attacker URLs (SSRF).** Standard Webhooks
calls webhooks "especially vulnerable": consumers supply arbitrary
URLs invoked from inside the producer's network. OWASP **API7:2023
Server Side Request Forgery**
(https://owasp.org/API-Security/editions/2023/en/0xa7-server-side-request-forgery/)
names webhooks as a primary SSRF vehicle; the published example is a
"test request" to a customer URL that can be pointed at cloud
metadata. OWASP SSRF Prevention Cheat Sheet: when the destination
set is unknown (the webhook case), allowlists are unavailable —
combine scheme/port restrictions, block private/loopback/link-local
ranges, disable or re-validate redirects. Spec controls (high-level
only): (1) egress all deliveries through an isolating proxy
(spec names Stripe's **smokescreen** as the idea, not a required
dependency); (2) put webhook workers on a subnet that cannot reach
internal services. Re-resolve DNS immediately before *each*
attempt (including retries hours later). No exploit steps here.

---

## 4. Verified defaults / standards

Fetched 2026-09-13. Library *tolerance constants* from published
docs / source, not from a registry crawl of every SDK version.

| Knob | Verified default | Source |
|---|---|---|
| Stripe live retry horizon | 3 days, exponential backoff | docs.stripe.com/webhooks |
| Stripe sandbox retries | 3 attempts, few hours | same |
| Stripe endpoint cap | 16 HTTPS URLs | same |
| Stripe TLS | 1.2 or 1.3 | same |
| Stripe timestamp tolerance | **300 s** (5 min) in official libraries (`DEFAULT_TOLERANCE` / `WebhookDefaultTolerance`); `0` **disables** the check | docs + stripe-go / stripe-ruby / stripe-java / stripe-node |
| Stripe signed payload | `t + '.' + raw body`; header `t=,v1=`; ignore non-v1 | docs.stripe.com/webhooks |
| GitHub response deadline | 10 s → 2xx | docs.github.com best-practices + handling-failed |
| GitHub auto-retry | none | handling-failed-webhook-deliveries |
| GitHub manual replay | 3 days | redelivering-webhooks |
| GitHub payload cap | 25 MB (otherwise no delivery) | webhook-events-and-payloads |
| GitHub MAC | HMAC-SHA256 `sha256=<hex>` of raw body; compare constant-time; SHA-1 header legacy | validating-webhook-deliveries |
| Slack ack deadline | 3 s, HTTP 2xx | docs.slack.dev/apis/events-api |
| Slack retries | 3: immediate, 1 min, 5 min | same |
| Slack auto-disable | >95% failed attempts / 60 min (and ≥ 1 000 events/h) | same |
| Slack delivery cap | 30 000 events / workspace / app / 60 min | same |
| Slack replay window | \|now − timestamp\| > **300 s** → reject (docs + python-slack-sdk `60 * 5`) | verifying-requests-from-slack |
| Slack Delayed Events | + hourly / 24 h; default drop if > 2 h late | Events API |
| Shopify timeouts | 1 s connect, 5 s request | shopify.dev verify-deliveries |
| Shopify retries | 8 over 4 h, exponential backoff; Admin-API subscription deleted after 8 consecutive failures | verify-deliveries (live); changelog 2024-09-10 (search-visible) |
| Shopify HMAC | base64 HMAC-SHA256(raw body, client secret); Pub/Sub & EventBridge skip HMAC | verify-deliveries |
| Standard Webhooks | spec **1.0.0**; `msg_id.timestamp.payload`; `whsec_` 24–64 byte secrets; example multi-day retry table; 15–30 s timeout *recommendation*; HTTPS advised | spec |
| Svix / SW libraries | 5-minute timestamp tolerance in the Python reference (`timedelta(minutes=5)`); docs last-updated 2026-08-28 | standard-webhooks Python lib; docs.svix.com |
| Stripe webhook source IPs | published list + `ips_webhooks.txt` / `.json` | docs.stripe.com/ips |

**C2 defaults this note refuses to copy.** Brooker Full Jitter
`sleep = random(0, min(cap, base·2^n))` is the least-*work* default;
SRE per-client retry ratio ~10% (~1.1× vs ~3×); do not retry
permanent errors. Webhook *producers* should apply those to their
outbound worker, not invent a second schedule on the receiver.

---

## 5. Failure modes and when-not-to-use

**Failure modes of the webhook itself.**

- **Ack-before-persist.** 2xx then crash = silent loss (producer
  thinks success). Persist/enqueue first.
- **Verifier bugs that 4xx valid traffic.** Treated as retryable
  failure; Slack/Shopify may disable or delete the subscription.
- **Raw-body / clock skew.** Tolerance 5 min needs NTP; Stripe `0`
  disables replay protection. GitHub has **no** timestamp in the
  MAC — replay protection is the delivery GUID store, not a window.
- **Wrong granularity of disable.** One bad path (one event type,
  one tenant) can take the whole endpoint dark (Slack app-level
  95%; Shopify subscription delete).
- **Fan-out amplification + no budget.** N endpoints × retries
  against a recovering consumer (C2 / metastability).
- **SSRF on the producer** if customer URLs are fetched from a
  privileged network, especially the "send test request and echo
  the body" flow (OWASP API7).
- **Edge mutation / short LB timeouts / HTTP→HTTPS 301.**
- **IP allowlist rot** (GitHub and Stripe both tell you the list
  changes).
- **Out-of-order / stale retries** (Stripe snapshots; Shopify
  original payload).
- **GitHub: no automatic retry** — outage longer than ops
  noticing ≈ missed events outside 3-day redelivery.

**When not to use (prefer the sibling).**

| Situation | Prefer |
|---|---|
| Browser or mobile client, bidirectional, sub-second | **A3** WebSocket (AWS blog; RFC 6455). Slack's own alternative is Socket Mode. |
| Browser, one-way stream | **A4** SSE |
| High-volume *internal* fan-out, ordering, competing consumers, DLQ | **A2** broker (event-driven-dataflow: buffer, redeliver, don't name the consumer) |
| Client cannot host a public HTTPS endpoint | Poll the A1 resource (AWS blog polling row) or a bus (Stripe EventBridge, Shopify Pub/Sub) |
| Need a query/audit log of every data access | Thin webhook + A1 GET (Standard Webhooks rationale) — or skip push |
| Exactly-once / total order | Not this channel; C9 + A2 still only give effectively-once |
| Receiver timeout budget is tighter than producer (3–5 s) and work is heavy | Still a webhook, but only as a trigger onto a queue — or don't take the HTTP callback |

**When it is the right channel.** Server-to-server, event rate
modest relative to 3–10 s ack, consumer can expose (or tunnel)
HTTPS, at-least-once + idempotent apply is acceptable, producer
already retries. Payments, CI, commerce, and chat platforms
standardized on it for a reason: no persistent connection tax,
reuses A1 HTTP/TLS/LB, and the consumer is already a server.

---

## 6. Cross-links

- **A1** Request–response — [rest-rpc-dataflow](../../../cases/data-intensive-design/rest-rpc-dataflow.md)
  (main repo). Thin webhooks are "Notification then GET."
- **A2** Pub-sub / queues / streams —
  [event-driven-dataflow](../../../cases/data-intensive-design/event-driven-dataflow.md).
  Broker when you need buffer, fan-out without N HTTPS, DLQ.
- **C2** Retry, backoff, budgets —
  [retry-backoff-external-research.md](retry-backoff-external-research.md)
  and [RetryBackoff.md](../../../cases/SystemDesignPatterns/RetryBackoff.md).
  Use Full Jitter and a ~10% budget on *your* outbound webhook
  workers; do not stack another retry loop in front of Stripe /
  Slack / Shopify schedules.
- **C9** Idempotency & deduplication (sibling card; not written
  here). Receiver keys above; Stripe API `Idempotency-Key` 24 h
  store is already in the C2 note.
- **C7** Timeouts & deadlines — producer 3–10 s vs LB idle;
  [timeouts-and-delays](../../../cases/data-intensive-design/timeouts-and-delays.md).
- **C4** Rate limiting —
  [rate-limiting-external-research.md](rate-limiting-external-research.md).
  Slack 30k/h and `app_rate_limited`; Standard Webhooks `429` +
  `Retry-After`.
- **C1** Circuit breaker — [circuit-breaker-external-research.md](circuit-breaker-external-research.md)
  if *you* are the producer and the consumer is down (open the
  *destination*, not the whole fleet).
- Catalog: [system-design-patterns-catalog.md](system-design-patterns-catalog.md) ⊕A5.

---

## 7. Sources

Retrieved 2026-09-13.

**Standard / canon.** github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md (v1.0.0) · www.standardwebhooks.com · docs.svix.com/receiving/verifying-payloads/how-manual (updated 2026-08-28) · martinfowler.com/articles/201701-event-driven.html (2017-01-20) · aws.amazon.com/blogs/architecture/managing-asynchronous-workflows-with-a-rest-api/ (2021-05-11) · tools.ietf.org / rfc-editor.org RFC 6455 (WebSocket contrast only).

**Stripe.** docs.stripe.com/webhooks · docs.stripe.com/webhooks/signature · docs.stripe.com/webhooks/process-undelivered-events · docs.stripe.com/ips · stripe.com/files/ips/ips_webhooks.txt · github.com/stripe/stripe-go `WebhookDefaultTolerance = 300s` · stripe-ruby / stripe-java / stripe-node `DEFAULT_TOLERANCE = 300`.

**GitHub.** docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries · …/handling-failed-webhook-deliveries · …/best-practices-for-using-webhooks · …/handling-webhook-deliveries (`ping`, 202) · …/webhook-events-and-payloads (25 MB, headers) · docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/redelivering-webhooks (3 days) · docs.github.com/en/rest/meta/meta (`hooks`).

**Slack.** docs.slack.dev/authentication/verifying-requests-from-slack · docs.slack.dev/apis/events-api (3 s, retries, 95%, 30k, Delayed Events) · docs.slack.dev/reference/events/url_verification · docs.slack.dev/tools/python-slack-sdk/reference/signature (`60 * 5`).

**Shopify.** shopify.dev/docs/apps/build/webhooks/verify-deliveries · shopify.dev/docs/apps/build/webhooks/troubleshoot · shopify.dev/changelog/updates-to-webhook-retry-mechanism (2024-09-10; search-indexed, fetch of that URL returned 404 this pass).

**SSRF (high-level).** owasp.org/API-Security/editions/2023/en/0xa7-server-side-request-forgery/ · cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html · github.com/stripe/smokescreen (named by the spec).

**C2 / C9 already in-tree.** docs.research/retry-backoff-external-research.md · cases/SystemDesignPatterns/RetryBackoff.md · docs.stripe.com/api/idempotent_requests (via C2).

---

## 8. Uncertain / left out

- **Stripe per-attempt timeout in seconds** is not on
  docs.stripe.com/webhooks. A 2022 Stack Overflow answer claims
  Support said 20 s. Not asserted.
- **Stripe's exact backoff steps** (immediate / 5 min / 30 min /
  2 h / … / 12 h) appear on secondary pages (Hookdeck, etc.), not
  on the official retry paragraph ("exponential back off" / three
  days). The similar table in Standard Webhooks is an *example*,
  not Stripe's published schedule.
- **Stripe auto-disable after N days of non-2xx** is widely claimed
  (Hookdeck "3 days then disable"). Official text says retries
  stop if the destination *is* disabled/deleted; the disable
  *trigger* was not on the fetched page.
- **Shopify changelog URL** `shopify.dev/changelog/updates-to-webhook-retry-mechanism`
  404'd on fetch; search still returns the 2024-09-10 body. Live
  verify-deliveries (8 / 4 h) is the asserted source. Troubleshoot
  metrics text mentioning "24-hour period" for removal was **not**
  reconciled with "4 hours" — left unused.
- **Standard Webhooks spec** does not fix the replay window at
  5 minutes; that is library practice (Python 5 min; JS constant
  not re-read from a non-empty blob this pass).
- **GitHub.com per-event-type hook cap** (docs source liquid:
  20 vs GHES 250) was not confirmed on a rendered "creating
  webhooks" page this pass.
- **GitHub GHES 30 s timeout** is in docs source conditionals, not
  re-verified against a GHES instance.
- Slack Bolt-JS `verify-request.ts` rejects only *stale* (past)
  timestamps; official prose uses absolute 5 min. Not treated as
  a contradiction in the Concept.
- OWASP Webhook Security Cheat Sheet is still under
  `cheatsheets_draft/` — not cited as published.
- No controlled measurement of webhook-retry dogpiles vs Full
  Jitter was found; C2 remains the authority.
- API Gateway default body-size / timeout numbers are C6/C7, not
  re-fetched here (only Stripe's raw-body mapping note).
- Skill-family / Concept write-up — out of scope.
