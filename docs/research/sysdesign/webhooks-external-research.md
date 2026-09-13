---
type: research
title: 'Webhooks & callbacks — external research (2026-09-13)'
description: >-
  Source-verified research backing the Webhooks Concept (A5): the
  at-least-once unordered delivery contract, exact signing schemes (Stripe,
  GitHub, Slack, Standard Webhooks), replay windows and raw-body verification,
  verified retry schedules per provider, the receiver checklist, provider-side
  dispatch design (per-endpoint isolation, thin vs snapshot payloads), and
  failure modes including ack-before-enqueue loss and SSRF.
tags: [research, webhooks, callbacks, signing, system-design-patterns]
---

# A5 Webhooks & callbacks — external research (2026-09-13)

**Method.** Facts verified against primaries 2026-09-13; paraphrase; ≤ 1 short quote per source. **Cited forward** from [idempotency-dedup-external-research.md](idempotency-dedup-external-research.md) (inbox/idempotent receiver, at-least-once vocabulary) and [retry-backoff-external-research.md](retry-backoff-external-research.md) (jitter canon, budgets, RFC 9110, metastability); not re-verified.

## 1. Delivery contract: at-least-once, unordered

- **Stripe**: does not guarantee event order (subscription creation emits several events in any arrival order); `created` timestamps are second-granular — never order or dedupe by them; track **event IDs** and fetch missing objects via the API. "Handle duplicate events": endpoints may receive the same event more than once; log processed ids and skip. Sometimes two *distinct* events describe one occurrence — dedupe by (`data.object` id + type).
- **Svix**: exponential-backoff retries give at-least-once (FAQ); regular endpoints deliver independently, order best-effort.
- **OpenAI**: duplicates possible; use the `webhook-id` header as the dedup key.
- Receiver mechanics = the inbox pattern **[cited forward]**.

## 2. Signing schemes (exact formats)

| Provider | Header(s) | Signed string | MAC/encoding | Notes |
|---|---|---|---|---|
| Stripe | `Stripe-Signature: t=<ts>,v1=<sig>[,v1=…][,v0=…]` | `t + "." + raw_body` | HMAC-SHA256 hex | Only v1 is live (v0 is a fake test scheme — ignore, downgrade defense); multiple v1 during secret rolls; library default tolerance **5 min** (0 disables — forbidden); constant-time compare; **each retry gets a fresh timestamp+signature** |
| GitHub | `X-Hub-Signature-256: sha256=<hex>` | raw body | HMAC-SHA256 hex | "Never use a plain `==`" — constant-time; SHA-1 header legacy-only; no timestamp — replay defense is `X-GitHub-Delivery` dedup |
| Slack | `X-Slack-Signature: v0=<hex>` + `X-Slack-Request-Timestamp` | `v0:<timestamp>:<raw body>` | HMAC-SHA256 hex | Reject > **5 min** skew (replay); verify on the raw body before deserialization |
| Standard Webhooks | `webhook-id`, `webhook-timestamp` (unix s), `webhook-signature` | `id + "." + ts + "." + payload` | HMAC-SHA256 **base64**, entries `v1,<b64>`, space-delimited list | Spec **1.0.0**; `v1a` = ed25519 (whsk_/whpk_ keys); list format exists for rotation; Svix `svix-*` headers are aliases; key = base64-decoded part after `whsec_` |

Standard Webhooks TSC: Zapier, Twilio, Lob, Mux, ngrok, Supabase, Svix, Kong; **OpenAI adoption independently verified** from its own docs.

## 3. Replay protection and transport

- Timestamp windows: Stripe (signed-in timestamp; 5-min library default), Slack (5-min, checked by you), Standard Webhooks (mandated check, no number). GitHub: id-dedup only (detects repeats, doesn't bound age).
- **Raw-body verification is the gotcha**: frameworks that parse/re-serialize break signatures — Stripe names Express `express.json()` before the route, Next.js bodyParser, API Gateway needing rawBody mapping; Svix: the signature "is sensitive to even the slightest changes". Rule: **verify before parse, on the bytes**.
- mTLS variant: DocuSign Connect documents mutual TLS (listener validates DocuSign's client cert; newer mTLS+OAuth chaining).
- Static egress IPs: Stripe publishes webhook IP lists (machine-readable, 7-day change notice) and says use IP allowlisting **and** signatures — defense in depth, not auth. GitHub exposes hook IPs via `GET /meta`.

## 4. Retry schedules (verified 2026-09)

| Provider | Schedule | After exhaustion |
|---|---|---|
| Stripe | Live: up to **3 days** exponential; sandbox: 3 retries over hours; manual resend ≤ 15 d (Dashboard) / 30 d (CLI) | Marked undelivered; recover via `GET /v1/events?delivery_success=false` (30-day retention); failing-endpoint **emails** |
| GitHub | **No automatic retries**; 10-s response deadline | Manual redelivery (UI/REST); docs recommend a periodic list-and-redeliver script |
| Slack Events | 3 retries: ~immediate, 1 min, 5 min; `x-slack-retry-num/-reason` headers; 2xx stops; `x-slack-no-retry: 1` refuses redelivery on an error | > 95% failures in 60 min → subscriptions temporarily disabled (< 1,000 events/h exempt) |
| Svix | 8 attempts: now, 5 s, 5 m, 30 m, 2 h, 5 h, 10 h, 10 h (~32 h) | `message.attempt.exhausted` op-webhook; endpoint auto-disabled after all-fail 5 days (≥ 12 h span in 24 h to start the clock) |
| OpenAI | Up to **72 h** exponential | Dedup on webhook-id |

## 5. Receiver discipline (each line sourced)

1. **Ack fast, process async**: Stripe (2xx before complex logic; queue — renewal spikes overwhelm); Slack (2xx within **3 s**); GitHub (within 10 s); Microsoft Graph (2xx/202 within 3 s; **persist to a queue, then ack**).
2. Verify signature on the raw body; constant-time; reject stale timestamps; ignore non-v1 schemes.
3. Dedupe by event id (Stripe id; GitHub `X-GitHub-Delivery` — redeliveries reuse it; `webhook-id` "an idempotency key") via the inbox **[cited forward]**.
4. Tolerate out-of-order by **fetching current state** (Stripe: retrieve the referenced objects; snapshots can be stale; thin events make fetch-current mandatory).
5. The signature is the auth (Stripe threat model: fake events → fulfillment/access); exempt the route from CSRF (documented); IP lists are extra.
6. Challenge flows: Slack `url_verification` (echo `challenge`); Microsoft Graph `validationToken` (10 s, 200, text/plain, escaped echo).
7. Stay healthy or lose data: Graph throttling — > 10% slow in 10 min ⇒ 10-min delivery delay; > 15% over limit ⇒ **drop state, "Dropped notifications can't be recovered"**; Slack disables at 95%. Reconciliation polling is the universal backstop.

## 6. Provider-side design (emitting)

- **Queue-backed dispatch, per-endpoint isolation** (Svix scalability guide): write once, expand per endpoint in workers; retries on a separate lower-priority queue so first attempts leave on time; aggressive delivery timeouts; **per-endpoint concurrency caps and rate limits; circuit-break dead endpoints** — "a single customer's bad deploy can look like an outage in your own system". Bulkhead-per-destination.
- Disable policies: Svix 5-day all-fail + op-event; Slack 95%/60-min; Stripe verified emails + retry-window stop (auto-disable not on current pages).
- **Thin vs snapshot payloads** (Stripe event destinations): snapshot = full object, API-versioned, "can be stale"; thin = id+type pointer, **unversioned**, typed SDK fetch helpers; v2 destinations choose per endpoint.
- Ordering disclaimers are the default; Svix FIFO endpoints show why (strict FIFO = head-of-line blocking, throughput via batching only).
- Managed fan-out overlap: SNS HTTP/S delivery policy (phases; defaults numRetries 3, min/max delay 20 s, linear; retryable = 5xx + 429; total HTTP/S retry ≤ **3,600 s**; DLQ on exhaustion; `maxReceivesPerSecond` throttle) — deeper fan-out is A2 territory.

## 7. Failure modes

1. **200-then-crash**: provider counts 2xx as delivered (Graph explicit) — ack before durable enqueue = unrecoverable loss; inbox-first, then ack.
2. **Signature over parsed body**: fails closed (endless verification failures) or tempts skipping verification — exposing the fake-event threat.
3. **Replay beyond tolerance**: enforce the window + id dedup; Stripe re-signs retries, so windows don't fight legitimate retries.
4. **Secret rotation without overlap**: Stripe keeps the old secret up to 24 h and sends one signature per active secret; Standard Webhooks' list format exists for this; expiring early makes the retry window your outage budget.
5. **Thundering redelivery after recovery**: Graph flushes missed notifications up to 4 h; Svix bulk resend; process via queue + shed or fall over again.
6. **SSRF (provider side)**: OWASP names webhook callback URLs a canonical SSRF vector — https-only, resolve-and-block internal ranges (169.254.169.254, 127/8, RFC1918), no blind redirects, allowlists.
7. **Catch-all 2xx** on internal errors silently discards events everywhere (2xx-is-success semantics are per-provider documented; framing is analysis).

## Sources

docs.stripe.com/webhooks (+ /webhooks/signature, /process-undelivered-events, /handle-irrecoverable-events, /event-destinations, /billing/subscriptions/webhooks, /ips) · docs.github.com validating-webhook-deliveries + best-practices + handling-failed-deliveries · docs.slack.dev verifying-requests + events-api + using-http-request-urls · standard-webhooks spec 1.0.0 + standardwebhooks.com · developers.openai.com webhooks guide · docs.svix.com retries + verifying-payloads + faq + fifo-endpoints · svix.com webhook-scalability guide · DocuSign mTLS blog + platform docs · learn.microsoft.com graph change-notifications-delivery-webhooks (2025-01-15) · docs.aws.amazon.com sns-message-delivery-retries · OWASP SSRF cheat sheet. Cited forward: idempotency-dedup-, retry-backoff-external-research.md.

## Uncertain / could not verify (excluded from the Concept)

- Stripe **auto-disable** after N days: only emails + retry-stop are on current pages — don't assert auto-disable.
- Standard Webhooks "40+ adopters incl. Anthropic/Gemini": site-claimed; only OpenAI independently verified.
- GitHub delivery-record retention period unstated.
- Slack docs pages undated.
- DocuSign docs page JS-rendered; mechanism from their blog.
- Svix "why unordered" causal wording is analysis.
- Flags: auth-in-URL anti-pattern reasoning, thin-events-blast-radius, recovery shed framing, catch-all-2xx framing = synthesis.
- SNS "100,015 attempts/23 days" applies to AWS-managed endpoints (Lambda/SQS), **not** HTTP/S — never quote it for webhooks.
