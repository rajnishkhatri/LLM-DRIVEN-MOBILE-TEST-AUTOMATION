---
type: reference
title: 'Webhooks and callbacks'
description: 'Outbound HTTP callbacks across a trust boundary: HMAC signing and timestamp replay windows, the 2xx-after-durable-enqueue contract, producer retry schedules as published, receiver dedupe keys (not C9 storage), fan-out caps, proxy/LB HMAC breakers, and when to prefer a broker, poll, or socket.'
tags: [system-design-patterns, communication, webhooks, callbacks, integration]
---

# Webhooks and callbacks

**See also:** [request–response](RequestResponse.md) · [pub/sub & queues](PubSubQueues.md) · [WebSocket](WebSockets.md) · [SSE](ServerSentEvents.md) · [retry](RetryBackoff.md) · [idempotency](Idempotency.md) · [timeouts](TimeoutsDeadlines.md) · [API gateway](ApiGateway.md) · [event-driven dataflow (DDIA)](../data-intensive-design/event-driven-dataflow.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/a5-webhooks-external-research.md)

A webhook is an event pushed **across a trust boundary** as a plain HTTP POST: the producer owns delivery and retries, the receiver owns an internet-facing endpoint and everything that implies. It is [pub/sub](PubSubQueues.md) with HTTP as the broker — ack becomes a status code, the DLQ becomes the producer's redelivery backlog, and authentication becomes cryptography because the caller is someone else's system. Quality attributes: **integration reach** (any HTTPS endpoint is a subscriber) and **latency** versus polling. Costs: at-least-once and unordered by contract, a public attack surface, and two parties who must each hold up their half.

## Lineage and vocabulary

**Webhook = HTTP callback / "reverse API".** Standard Webhooks **v1.0.0** (Apache-2.0) exists as a converging header set (`webhook-id`, `webhook-timestamp`, `webhook-signature`); Svix uses the same HMAC (`whsec_`, `webhook-` / `svix-` prefixes) plus optional `ed25519`. The producer calls *the consumer's* HTTP server. A traditional API is common, not required.

**Fowler 2017** (Event Notification vs Event-Carried State Transfer) is the thin-vs-snapshot split: thin events carry ids and force an [A1 GET](RequestResponse.md); snapshots carry state and are larger on every delivery. Stripe now ships both, chosen per destination.

**AWS Architecture Blog (Gerring 2021)** places the three async shapes: poll the created resource, webhook (server-to-server), [WebSocket](WebSockets.md) (browser). Nygard's Integration Points apply per destination: every callback has its own timeout and retry.

## Wire semantics

A delivery is one **HTTP POST**, `Content-Type: application/json` in the vendors fetched here. Authenticity lives in **headers**, not in a query secret.

| Producer | Auth headers | Signed content | Digest |
|---|---|---|---|
| **Stripe** | `Stripe-Signature: t=<unix>,v1=<hex>[,v0=…]` | `timestamp + '.' + raw JSON body` | HMAC-SHA256; ignore non-`v1` (downgrade) |
| **Standard Webhooks / Svix** | `webhook-id`, `webhook-timestamp`, `webhook-signature` (Svix default `svix-*`) | `msg_id + '.' + unix_ts + '.' + raw body` | HMAC-SHA256 → base64 `v1,<sig>` (space-delimited list for rotation); optional `ed25519` / `v1a` |
| **GitHub** | `X-Hub-Signature-256: sha256=<hex>` (legacy `X-Hub-Signature` SHA-1) | raw body only (no timestamp in the MAC) | HMAC-SHA256 hex |
| **Slack** | `X-Slack-Signature: v0=<hex>`, `X-Slack-Request-Timestamp` | `'v0:' + timestamp + ':' + raw body` | HMAC-SHA256 hex |
| **Shopify** | `X-Shopify-Hmac-SHA256` | raw body | HMAC-SHA256 → base64 |

**Raw body is load-bearing.** Stripe, GitHub, Slack, Shopify, and the spec all require the exact bytes the producer signed. Re-parsing JSON and re-serializing (whitespace, key order, Unicode) invalidates the MAC. Frameworks that run `express.json()` / body parsers *before* the webhook route are the documented failure mode.

**Receiver contract (status codes).**

- **Success = 2xx** (200–299). GitHub's own handler examples return **202**. Slack asks for `HTTP 200 OK` in prose but counts the 200-series.
- **Anything else is a failed delivery** for Stripe (any non-`2xx`), Shopify ("any response outside the 200 range, **including 3XX**"), and Slack (`http_error` unless it is one of the two allowed redirects).
- **Standard Webhooks recommended etiquette** (spec, not a vendor SLA): `2xx` success; `3xx` failure (do not follow redirects); `410 Gone` → producer **disables** the endpoint; `429` → throttle; `502`/`504` → throttle; honour `Retry-After` when present.
- **Slack** will follow **up to two** `301`/`302`s; more than two is `too_many_redirects`.
- **4xx vs 5xx is not a retry classifier at these producers.** Stripe, Shopify, and Slack retry on *any* non-success, including 400/401/403 from a buggy verifier. Return **2xx after durable enqueue**. Slack's `x-slack-no-retry: 1` on a *non-200* is the explicit escape hatch — it cancels **that event**, not the subscription.

## Connection lifecycle

There is **no reconnect protocol**. Each attempt is a new HTTP transaction: DNS resolve (re-resolve per attempt — SSRF below) → TCP connect → TLS 1.2+ handshake → HTTP/1.1 POST → verify raw body, enqueue, 2xx → idle close. The *event* identity (id header) ties attempts together, not a socket. No vendor fetched here requires HTTP/2. Shopify documents Keep-Alive reuse to the same host.

**Timeouts (verified).** GitHub.com / GHEC: **10 s** to a 2xx or the connection is terminated. Slack Events API: **3 s**. Shopify: **1 s** connect + **5 s** request. Standard Webhooks *recommendation*: **15–30 s** (spec, not a library default). Stripe official docs say "quickly" / "Timed out" as a delivery error; **no seconds figure on the primary page** — do not invent one.

Stripe requires TLS **v1.2 or v1.3** and validates the server certificate before sending. Slack classifies `ssl_error` separately and offers **mutual TLS**: the terminator requests a client cert under a DigiCert root; SAN or CN must be exactly `platform-tls-client.slack.com`; inject a header the app server trusts *only* from that terminator.

## Signing and replay windows

Three rules fall out of the table above.

1. **Verify on the raw bytes before any parsing.** Express json middleware, Next.js body parsing, and API Gateway mappings that parse first are the documented breakers. Stripe publishes an API Gateway + Lambda mapping template that must stash `$input.body` as `rawBody`.
2. **Compare in constant time.** GitHub's docs say it explicitly ("never use a plain ==").
3. **Enforce the timestamp window *and* dedupe ids** — they defend different replays.

| Producer | Replay window | What it does *not* cover |
|---|---|---|
| Stripe | **300 s** in official libraries (`DEFAULT_TOLERANCE` / `WebhookDefaultTolerance`); `0` **disables** the check | A replay inside the window; retries are re-signed with a fresh `t=` / `v1=` |
| Slack | \|now − timestamp\| > **300 s** → reject | A replay inside the window; dedupe on `event_id` |
| Standard Webhooks / Svix | Spec does **not** fix the window; Python reference uses 5 minutes | Same: window + `webhook-id` together |
| GitHub | **None** — the MAC has no timestamp | Replay defense is the delivery-GUID store only |
| Shopify | HMAC of raw body; no timestamp in the MAC | Use `X-Shopify-Triggered-At` (or a payload timestamp) for staleness |

mTLS and published egress IPs exist as additional layers; the signature remains the authentication. IP allowlists without signatures fail when a neighbor on the same NAT is malicious; signatures without allowlisting still hold if the secret holds.

**Secret rotation is a protocol feature.** Overlap windows with one signature per active secret (Stripe's multiple `v1`; Standard Webhooks' space-delimited list). Expiring the old secret before consumers deploy makes the retry window your outage budget.

## Acknowledge vs process; idempotent receivers

Every vendor fetched here: return 2xx *before* slow work. Stripe: "before updating a customer's invoice as paid." GitHub: 2xx within **10 s**, then a queue. Slack: 2xx within **3 s**; "avoid actually processing … in the same process." Shopify: 2xx quickly against a **5 s** request budget. The HTTP handler's unit of work is verify + persist + ack, not the business transaction.

**Persist-or-enqueue, then 2xx.** A 2xx sent before durable write is silent loss — the producer will not retry. That is the C9-shaped fix; how to *store* the key, conflict codes, and 24 h API-key retention live in [idempotency](Idempotency.md). This card only names the receiver keys that stay stable across retries:

| Producer | Dedupe key | Fine print |
|---|---|---|
| Stripe | `Event.id` (`evt_…`) | Already-processed → ignore + **2xx** (stops further automatic retries). Snapshots can arrive **out of order**; do not use `created` as a sequence number. |
| Standard Webhooks | `webhook-id` | Constant across retries; spec example stores ids ~5 minutes. |
| GitHub | `X-GitHub-Delivery` GUID | **The same** on manual redelivery. |
| Slack | envelope `event_id` | Retries add `x-slack-retry-num` `1\|2\|3` and `x-slack-retry-reason`. Dedupe on `event_id`, not the counter. |
| Shopify | `X-Shopify-Webhook-Id` per delivery; `X-Shopify-Event-Id` shared across subscriptions of the same merchant action | Retries keep the original payload (stale). |

Enrollment handshakes are not business events: Slack `url_verification` (echo `challenge` as text/plain, form, or JSON); GitHub `ping` (`X-GitHub-Event: ping`) — 2xx / 202, not repo activity. Exempt the route from CSRF (the signature is the CSRF token) and never rely on a secret URL path — it logs everywhere and authenticates nothing about the body.

## Fan-out and scaling

Fan-out on this channel is **N independent HTTPS POSTs**, one per registered destination — not a broker subscription. Cost and failure domains multiply with N.

| Producer | Fan-out / caps (fetched 2026-09-13) |
|---|---|
| **Stripe** | **16** webhook endpoints per account; HTTPS, publicly reachable. Same event can also go to Amazon EventBridge or Azure Event Grid. Thin vs snapshot payloads are **separate** destinations. |
| **Standard Webhooks** | Recommends multiple endpoints per customer (CRM + billing + chat). Payload **< 20 kB** recommended (no hard spec limit). |
| **GitHub** | Payload cap **25 MB** — oversize events are **not delivered**. Subscribe to the minimum event set. `GET /meta` → `hooks` CIDRs (values change; do not freeze a list). |
| **Slack** | One Events API request URL per app (HTTP mode) or Socket Mode (no public URL). **30 000** events / workspace / app / 60 minutes; overflow is an `app_rate_limited` callback every minute. Apps under 1 000 events/hour are not auto-disabled. |
| **Shopify** | HTTPS, or Google Pub/Sub / Amazon EventBridge (HMAC does not apply on the buses). Multiple subscriptions for one topic → one delivery each (different `Webhook-Id`, same `Event-Id`). |

Receiver scaling: ingress must stay inside the producer timeout (3–10 s typical). Burst absorption is a **queue behind the 2xx**. Horizontal scale of that handler is stateless if the dedupe store is shared ([C9](Idempotency.md)).

**Producer-side amplification.** One business event × N endpoints × retry attempts is open-loop load on the consumer. [C2](RetryBackoff.md)'s lesson applies on the *producer* worker pool: Full Jitter on the retry clock, a retry budget so a down consumer cannot dominate the sender, one retry layer. Do not stack client retries in front of Stripe/GitHub/Slack's already-scheduled retries. Per-endpoint isolation — cap concurrency and rate **per destination**, put retries on a lower-priority queue, circuit-break dead endpoints — is the [bulkhead](Bulkhead.md) applied to destinations.

## Failure and "reconnect" (producer retry schedules)

There is no reconnect. What exists is a **published retry schedule**. Jitter math, SRE ~10% budgets, and `4³=64` stacking live in [retry](RetryBackoff.md) — this card only records what each producer publishes.

| Producer | Automatic retries | Give-up / disable | Manual / reconcile |
|---|---|---|---|
| **Stripe** | Live: up to **three days**, exponential backoff. Sandbox: **three** attempts over a few hours. New `t=` / `v1=` on **every** attempt. | Disabled/deleted destination → no further retries. Re-enable before the next attempt → retries continue. | Dashboard resend ≤ **15** days; CLI `stripe events resend` ≤ **30** days. List API `delivery_success=false` to backfill. A manual 2xx does **not** cancel the automatic schedule. |
| **GitHub** | **None.** Timeout (10 s) or non-2xx = failed delivery, period. | n/a | Redeliver last **3** days (UI or `POST .../deliveries/{id}/attempts`). Script: list deliveries, skip GUIDs that already have `status=OK`. |
| **Slack** | **3** retries: nearly immediately, **1 min**, **5 min**. Reasons: `http_timeout`, `too_many_redirects`, `connection_failed`, `ssl_error`, `http_error`, `unknown_error`. | **> 95%** of attempts in any of {SSL fail, >3 s, >2 redirects, non-200-series} over **60 min** → subscription temporarily disabled (email). Optional **Delayed Events**: hourly retries for **24 h**; default will not deliver an event **> 2 h** late. | Re-enable in app settings. `x-slack-no-retry: 1` on a non-200 stops that event. |
| **Shopify** | **8** retries over **4 hours**, exponential backoff. Original payload; original subscription URL (address changes mid-cycle are ignored). | After 8 consecutive failures, Admin-API subscriptions are **deleted**; emergency-developer email. | Re-create the subscription; reconcile via Admin API. |
| **Standard Webhooks (example)** | Spec *example*: immediate, 5 s, 5 min, 30 min, 2 h, 5 h, 10 h, 14 h, 20 h, 24 h (elapsed 75 h 35 m 5 s). Recommends jitter ([C2](RetryBackoff.md)) and email + disable on persistent fail. | Recommendation only. | Visibility + manual replay called out as non-core but "immensely important." |

GitHub's lack of automatic retry is the architectural outlier: the consumer must poll the Deliveries API or accept loss outside the 3-day manual window. Stripe/Slack/Shopify assume the opposite. Reconciliation (list events / Admin API / deliveries API) is the closed loop when the retry window closes.

**Order and loss.** At-least-once, not in-order. Stripe snapshot events "can arrive out of order." Shopify retries the *original* payload (stale). Slack is "best-effort"; incidents can delay delivery. Fetch current state for anything order-sensitive; treat the payload as a hint.

## Proxy / load-balancer interactions

Signatures and timeouts fail at the edge more often than in handler code.

- **Body mutation.** Any proxy that buffers, pretty-prints, gzip-re-encodes, or JSON-rewrites the body breaks HMAC. GitHub: "if you use a proxy or load balancer, make sure [it] does not modify the payload or headers."
- **TLS termination vs mTLS.** Slack mTLS is decided at the terminator. If an LB strips client certs, the app never sees `platform-tls-client.slack.com`. Injected SAN headers are only safe if the terminator overwrites them (Slack: check the header was not already present).
- **Idle / request timeouts at the LB** shorter than the producer's wait ([C7](TimeoutsDeadlines.md)) turn a would-be 2xx into the producer's `timed out` / `http_timeout`. Shopify's 5 s budget is easy to blow with one extra hop.
- **Redirects.** Shopify treats 3xx as failure. Slack follows two. Standard Webhooks: do not follow; update the registered URL. An edge "HTTP→HTTPS 301" is a production outage for Shopify.
- **IP allowlists.** Complement, not a substitute, for signatures. Stripe: live list at docs.stripe.com/ips and `ips_webhooks.txt` (7-day notice via API-announce). GitHub: `GET https://api.github.com/meta` field `hooks`.
- **Keep-Alive reuse** (Shopify): sudden LB deregistration mid-reuse looks like `connection_failed` / RST, which *is* retried by Stripe/Slack/Shopify.

## Endpoint verification and SSRF (high-level)

**Consumer proves they own the URL.** Slack `url_verification` as above; GitHub `ping` on create; Stripe CLI `stripe listen` / Workbench "send test event"; live endpoints must already be public HTTPS.

**Producer must not fetch attacker URLs.** Standard Webhooks calls webhooks "especially vulnerable": consumers supply arbitrary URLs invoked from inside the producer's network. OWASP **API7:2023** names webhooks as a primary SSRF vehicle. When the destination set is unknown, allowlists are unavailable — combine scheme/port restrictions, block private/loopback/link-local ranges, disable or re-validate redirects. Spec controls (high-level only): egress all deliveries through an isolating proxy (the spec names Stripe's **smokescreen** as the idea); put webhook workers on a subnet that cannot reach internal services; re-resolve DNS immediately before *each* attempt, including retries hours later.

## Verified defaults

Fetched 2026-09-13. Library *tolerance constants* from published docs / source.

| Knob | Verified default |
|---|---|
| Stripe live retry horizon | 3 days, exponential backoff |
| Stripe sandbox retries | 3 attempts, few hours |
| Stripe endpoint cap | 16 HTTPS URLs |
| Stripe TLS | 1.2 or 1.3 |
| Stripe timestamp tolerance | **300 s**; `0` disables |
| Stripe signed payload | `t + '.' + raw body`; ignore non-v1 |
| GitHub response deadline | 10 s → 2xx |
| GitHub auto-retry | none |
| GitHub manual replay | 3 days |
| GitHub payload cap | 25 MB (otherwise no delivery) |
| Slack ack deadline | 3 s, HTTP 2xx |
| Slack retries | 3: immediate, 1 min, 5 min |
| Slack auto-disable | >95% failed attempts / 60 min (and ≥ 1 000 events/h) |
| Slack delivery cap | 30 000 events / workspace / app / 60 min |
| Slack replay window | 300 s |
| Slack Delayed Events | + hourly / 24 h; default drop if > 2 h late |
| Shopify timeouts | 1 s connect, 5 s request |
| Shopify retries | 8 over 4 h; Admin-API subscription deleted after 8 consecutive failures |
| Standard Webhooks | spec **1.0.0**; `msg_id.timestamp.payload`; `whsec_` 24–64 byte secrets; 15–30 s timeout *recommendation* |

**C2 defaults this card refuses to copy.** Brooker Full Jitter, SRE per-client retry ratio ~10%, and "do not retry permanent errors" belong in [RetryBackoff](RetryBackoff.md). Webhook *producers* should apply those to their outbound worker, not invent a second schedule on the receiver.

## Failure modes

- **Ack-before-persist.** 2xx then crash = silent loss. Persist/enqueue first.
- **Verifier bugs that 4xx valid traffic.** Treated as retryable failure; Slack/Shopify may disable or delete the subscription.
- **Signature over the parsed body.** Fails closed until someone "fixes" it by skipping verification.
- **Raw-body / clock skew.** Tolerance 5 min needs NTP; Stripe `0` disables replay protection. GitHub has **no** timestamp in the MAC.
- **Wrong granularity of disable.** One bad path (one event type, one tenant) can take the whole endpoint dark (Slack app-level 95%; Shopify subscription delete).
- **Fan-out amplification + no budget.** N endpoints × retries against a recovering consumer ([C2](RetryBackoff.md) / metastability).
- **SSRF on the producer** if customer URLs are fetched from a privileged network, especially the "send test request" flow.
- **Edge mutation / short LB timeouts / HTTP→HTTPS 301.**
- **IP allowlist rot** (GitHub and Stripe both tell you the list changes).
- **Out-of-order / stale retries** (Stripe snapshots; Shopify original payload).
- **GitHub: no automatic retry** — outage longer than ops noticing ≈ missed events outside 3-day redelivery.
- **The polite 500.** A catch-all returning 2xx on internal errors silently discards events; map internal failure to 5xx and let the retry schedule work.

## When not to use

| Situation | Prefer |
|---|---|
| Browser or mobile client, bidirectional, sub-second | [WebSocket](WebSockets.md). Slack's own alternative is Socket Mode. |
| Browser, one-way stream | [SSE](ServerSentEvents.md) |
| High-volume *internal* fan-out, ordering, competing consumers, DLQ | [Broker](PubSubQueues.md) / [event-driven dataflow](../data-intensive-design/event-driven-dataflow.md) |
| Client cannot host a public HTTPS endpoint | Poll the [A1](RequestResponse.md) resource, or a bus (Stripe EventBridge, Shopify Pub/Sub) |
| Need a query/audit log of every data access | Thin webhook + A1 GET — or skip push |
| Exactly-once / total order | Not this channel; [C9](Idempotency.md) + A2 still only give effectively-once |
| Receiver timeout budget is tighter than producer (3–5 s) and work is heavy | Still a webhook, but only as a trigger onto a queue — or don't take the HTTP callback |

**When it is the right channel.** Server-to-server, event rate modest relative to a 3–10 s ack, consumer can expose (or tunnel) HTTPS, at-least-once + idempotent apply is acceptable, producer already retries. Payments, CI, commerce, and chat platforms standardized on it for a reason: no persistent connection tax, reuses A1 HTTP/TLS/LB, and the consumer is already a server.

## Trade-offs

| Buy | Pay |
|---|---|
| Push latency without polling costs | An internet-facing endpoint with cryptographic hygiene |
| Provider-owned retries and backoff | Schedules vary from none (GitHub) to 3 days (Stripe) — reconciliation is still yours |
| Loose coupling across organizations | At-least-once, unordered, stale: three contracts to engineer around |
| Standard Webhooks converging the schemes | Two-party correctness: either side's shortcut breaks it |
| Thin events shrink leak surface and stay unversioned | Every handler must [GET current state](RequestResponse.md) |

A webhook is the receiver half of [pub/sub](PubSubQueues.md) worn across a trust boundary; the [idempotent inbox](Idempotency.md) is its load-bearing wall; the [retry](RetryBackoff.md) note owns the jitter and budget you apply when *you* are the producer.

## Sources

Verified 2026-09-13; full URLs and exclusions in the [external research note](../../docs/research/sysdesign/a5-webhooks-external-research.md). Key primaries: Standard Webhooks 1.0.0 and Svix verification docs; Fowler 2017 event-notification; AWS Architecture Blog (Gerring 2021); Stripe webhooks, signature, undelivered-events, and IP docs plus official-library `DEFAULT_TOLERANCE = 300s`; GitHub webhook validation, best-practices, failed-deliveries, redelivery (3 days), payload cap, and `/meta` `hooks`; Slack request verification, Events API (3 s, retries, 95%, 30k, Delayed Events), and `url_verification`; Shopify verify-deliveries (1 s / 5 s, 8 / 4 h); OWASP API7:2023 and SSRF Prevention Cheat Sheet (high-level). Jitter, budgets, and stacked-retry math cited via [C2](RetryBackoff.md); inbox storage and key retention via [C9](Idempotency.md). Left out of this card (research §8): Stripe's unpublished per-attempt timeout, unofficial backoff-step tables, and claimed auto-disable triggers; GHES-only timeout conditionals; OWASP's still-draft webhook cheat sheet.
