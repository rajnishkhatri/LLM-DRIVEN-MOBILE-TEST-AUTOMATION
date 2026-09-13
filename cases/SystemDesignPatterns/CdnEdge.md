---
type: reference
title: 'CDN and edge'
description: 'The HTTP cache in front of an origin on the public path: cache-key variance, TTL vs s-maxage vs RFC 5861 stale windows, origin shield, purge, signed URLs, and dynamic acceleration as TCP+TLS proxying versus a cache hit. Complements application caches; serving stale on purpose is a product decision.'
tags: [system-design-patterns, performance, cdn]
---

# CDN and edge

**See also:** [caching (B3 research)](../../docs/research/sysdesign/b3-caching-external-research.md) · [load balancing](LoadBalancing.md) · [failover and health checks](FailoverHealth.md) · [graceful degradation](GracefulDegradation.md) · [circuit breaker](CircuitBreaker.md) · [performance](../data-intensive-design/performance.md) · [home-timeline case study](../data-intensive-design/home-timeline-case-study.md) · [CloudFront as an AWS entry point](../aws/ch09.md) · [Origin Shield in a video sketch](../aws/ch20.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/b8-cdn-edge-external-research.md)

A CDN point of presence (POP) stores an HTTP **response** keyed by a **cache key** derived from the request. A later request that hashes to the same key is a **hit** and never reaches the origin. A miss, or a revalidation, goes origin-ward — optionally through a mid-tier **shield** that collapses duplicate misses. That is the opposite of an application cache ([B3](../../docs/research/sysdesign/b3-caching-external-research.md)): the caller is an anonymous or cookied HTTP client, the store is shared and multi-tenant, and invalidation is a *fleet* problem (every POP, every variant).

Quality attributes: **performance** (bytes closer to the client), **scalability** of the origin (`origin_qps ≈ client_qps × (1 − hit_rate)`, then collapsed by the shield), and **availability** of the *caller* when `stale-if-error` is on. Costs: another fleet of independent stores to fill and purge, key-design as a correctness problem, and a capacity-cache flush that becomes a thundering herd on the origin.

[C11](GracefulDegradation.md) owns *whether* serving stale is acceptable as degradation. This card owns the HTTP and CDN *mechanism*.

## Lineage and vocabulary

- **RFC 9111** (STD 98, June 2022; obsoletes 7234) is HTTP caching. Shared vs private. `s-maxage` (shared only) overrides `max-age` / `Expires` inside a shared cache and **incorporates `proxy-revalidate`**: a shared cache MUST NOT reuse a stale `s-maxage` response until it has validated with the origin. `must-revalidate` / `no-cache` / applicable `s-maxage` or `proxy-revalidate` forbid generating a stale response. A cache MUST NOT serve stale unless disconnected **or** explicitly permitted (`max-stale`, RFC 5861 extensions, or an out-of-band contract). Shared caches MUST NOT reuse a response to a request with `Authorization` unless `must-revalidate`, `public`, or `s-maxage` is present.
- **RFC 5861** (May 2010, Informational, not Standards Track) is two independent extensions. `stale-while-revalidate=N`: MAY serve stale for N seconds while revalidating **without blocking**. Example: `max-age=600, stale-while-revalidate=30`. `stale-if-error=N`: MAY serve stale on 500 / 502 / 503 / 504 (or equivalent network/DNS failure) up to N seconds of staleness. Background revalidation SHOULD be request-triggered to avoid amplification.
- **Vendor cache-key canons** (fetched 2026-09-13). CloudFront: key = query / headers / cookies you *opt in*; those values are also forwarded (use an **origin request policy** to forward without varying). Fastly `vcl_hash` default: `req.url` (includes query) + `req.http.host` + `req.vcl.generation`; method and TLS-vs-HTTP are ignored; prefer `Vary` over stuffing the hash. Cloudflare default: scheme + host + URI **with query** + `Origin` + method-override and forwarded-host headers. Akamai: hostname + path always; query **on by default**. Cache is **per edge server**, not a monolithic store.

## Two products named "acceleration"

| Mode | What the POP does | Origin load |
|---|---|---|
| **Cache-hit** | Return bytes from the POP (or shield). | Zero for that request. |
| **Dynamic acceleration** | Proxy on a **kept-alive** origin TCP/TLS session (often a better path). | One origin request; handshake amortized. |

CloudFront states the dynamic case: persistent connections save the TCP + TLS handshake; keep-alive default **5 s** (1–300 s); connection timeout **10 s**, **3** attempts; response timeout **30 s** (1–120 s). Origin Shield treats PUT/POST/PATCH/DELETE and GET/HEAD with TTL < **3600 s** (or caching disabled) as dynamic — Shield is then *always* an extra hop. Cloudflare Argo Smart Routing minimizes origin TTFB by avoiding congested paths; it does **not** create a cache hit. Tiered Cache is the shield cousin.

WebSocket / SSE are usually uncacheable; you wanted [A3](WebSockets.md) / [A4](ServerSentEvents.md) plus an idle timeout (CloudFront WebSocket origin idle **10 min**), not a cache policy.

## Cache-key design (the variance problem)

The key is every request dimension you *choose* to vary on. Extra dimensions multiply stored objects and **cut hit rate**. An omitted dimension the origin actually uses is a **correctness** bug (wrong language, wrong tenant, cache poisoning via a forwarded host).

| Dimension | When to include | Failure if wrong |
|---|---|---|
| **Scheme** | When origin content differs on HTTP vs HTTPS. Cloudflare default uses *origin* scheme (Flexible → Full **busts** the key). Fastly default **ignores** TLS-vs-HTTP. CloudFront caches once even if viewers use both. | Poisoning, or a silent miss storm after an SSL-mode change. |
| **Host** | Always, unless you deliberately collapse aliases. | Serving tenant A for tenant B. |
| **Path** | Always (normalized). | — |
| **Query** | Only parameters the origin *uses to select bytes*. Drop `utm_*` and **signed-URL tokens**. CloudFront CachingOptimized includes **none**; Cloudflare / Fastly include the whole query; Akamai adds query **by default**. | All = shard on every tracker. None = one variant for every query. |
| **Cookie** | Only cookies that change the body (A/B, currency). Never session IDs if the body is public. CachingOptimized: **none**. Cloudflare default: cookies not in the key. | One cookie × N users = N objects. |
| **Header** | `Accept-Language`, normalized `Accept-Encoding`, CORS `Origin`, device class. Do **not** vary on `Authorization` unless the response is `public` / `s-maxage` / `must-revalidate` (RFC 9111 §3.5) *and* you intend per-credential objects. | Un-normalized `Accept-Encoding` = one object per browser string. |
| **Method** | GET/HEAD. Fastly default hash ignores method (non-GET typically passed). Cloudflare: non-GET not cached by default. CloudFront: only GET (max object **50 GB**). | Caching POST is a correctness incident. |

**Cache key vs origin request.** CloudFront's split is the design rule: everything in the cache policy is in the origin request; an **origin request policy** forwards extras *without* varying. Fastly: hash on normalized fields, `req.http.*` still goes to origin. Cloudflare custom keys that ignore query still *send* the query unless you rewrite it.

**Vary vs hash.** Fastly prefers `Vary` for language / location: one stored object with a vary list, rather than N hashes you must purge individually. CloudFront has no first-class `Vary` cache-key UI — you list headers instead.

## Freshness: TTL vs `s-maxage` vs RFC 5861

Three clocks, one object:

1. **Browser freshness** — `Cache-Control: max-age` / `Expires`. The CDN does not control this once the bytes left the POP.
2. **Shared-cache freshness** — `s-maxage` (RFC 9111 §5.2.2.10) or a surrogate (`Surrogate-Control: max-age` at Fastly; CloudFront Min/Default/Max TTL; Cloudflare Edge Cache TTL; Akamai `honorSMaxage`).
3. **Stale window** — RFC 5861 `stale-while-revalidate` (hide revalidation latency) and `stale-if-error` (hide origin failure; [C11](GracefulDegradation.md) decides *whether*).

`s-maxage` **is not** "CDN `max-age`." It also means `proxy-revalidate`. Cloudflare's operational consequence (page date 2026-06-26): if `s-maxage` (or `must-revalidate` / `proxy-revalidate` / `no-cache`) sits next to `stale-while-revalidate`, Cloudflare will **not** serve stale — status `EXPIRED` instead of `UPDATING`. Their documented workaround for "long edge TTL, short browser TTL, plus SWR": send `max-age` + `stale-while-revalidate`, then set Edge Cache TTL. Do **not** use `s-maxage` for that split on Cloudflare. CloudFront's SWR page shows examples with `max-age`, not `s-maxage`, and caps SWR/SIE by MaxTTL. Fastly parses both as separate windows and does **not** repeat Cloudflare's sentence — test the POP; do not claim a vendor-universal rule.

Fastly freshness preference: `Surrogate-Control: max-age` → `Cache-Control: s-maxage` → `max-age` → `Expires`. SWR / SIE default **0**. Implicit no-header TTLs differ by surface (2 min / 120 s / 3 600 s) — **set an explicit TTL**. Fastly strips `Surrogate-Control` before the client except when shielding, so the edge POP still sees it.

**Request collapsing** is the stampede control at this layer (B3 owns application-lock families). Cloudflare: a per-datacenter cache lock; only the first miss of a given asset goes to origin. CloudFront Origin Shield consolidates simultaneous requests for the same object to "as few as one" origin fetch.

## Origin shield / tiered cache

Shield is **not** a second CDN. It is a fan-in of *misses*.

| Vendor | Mechanism | Placement rule (sourced) |
|---|---|---|
| **CloudFront Origin Shield** | Extra regional cache; skip the hop if the request already landed in that Region. 13 Shield Regions listed. | Same Region as an in-Region origin; otherwise the pairing table. Multi-CDN: other CDNs use CloudFront as *their* origin so one Shield absorbs them. gRPC bypasses Shield. Log: `OriginShieldHit`. |
| **Fastly shielding** | One designated shield POP per backend. | Closest POP to the origin. Age is forwarded so the edge does not treat shield-stale as fresh — **except** soft-purge + SWR (see failure modes). |
| **Cloudflare Tiered Cache** | Lower-tier → upper-tier; only upper-tiers talk to origin. | Smart + Generic Global + Regional + Custom. Public-cloud anycast origins need a **cloud region hint** (`aws:us-east-1`, …; changelog 2026-04-17). [Load balancing](LoadBalancing.md): one upper-tier for the **whole pool**. Confirm with `CacheTieredFill`. |
| **Akamai** | Site Shield / Tiered Distribution: child → parent → origin. | `Miss from child, Hit from parent`. Site Shield also hides origin IPs. |

It helps just-in-time packaging and image transforms (CloudFront's named use cases) because those origins are expensive per miss. It hurts low-cacheability / rarely-requested objects: every miss pays an extra hop.

## Purge / invalidation

TTL bounds *staleness*; purge is the operator's "this byte is wrong *now*." A forgotten purge lasts the TTL; a purge without TTL still needs the next miss to refill.

| Vendor | Mechanism | Verified limits / gotchas |
|---|---|---|
| **CloudFront** | Path (and cache-tag) invalidation. Signed URLs: invalidate **only the path before `?`**. Cookie / header variants: one invalidation drops **all** variants. Query-forwarding: you **must** include the query. Directory: invalidate with *and* without trailing `/`. | **150** paths or tags / s; **1** wildcard / s; path max **4 000** chars. |
| **Fastly** | URL purge; surrogate-key; purge-all (increments `req.vcl.generation`). Soft purge marks stale (pairs with SWR). `Surrogate-Key` tokens ≤ **1 KB**, header ≤ **16 KB**. | Purge-all: up to **2 minutes**; incompatible with soft / bulk. Soft-purge + shielding can re-cache stale as fresh at the edge. |
| **Cloudflare** | Everything / URL / tag / hostname / prefix. Custom keys that include headers/cookies: dashboard single-file purge **will not** hit them — API must send the same headers. Missing header = empty value in the key. | Prefetch always uses the **default** key — mismatch with custom keys. |
| **Akamai Fast Purge** | **Invalidate** (default): next request is IMS; 304 keeps the object. **Delete**: drop the bytes; next request is a full GET. Invalidate can still serve stale if origin is down (when configured). Purge is not persistent. | Delete is the compliance / takedown tool; it costs more origin bandwidth. |

**Versioned URLs** (content-hash in the path) are the purge you do not have to issue — B3's generation-key idea at the edge. Trade-off: old hashes occupy cache until eviction; HTML that references them must change in lockstep.

## Signed URLs (auth in the query string)

A signed URL is an authorization *token*, not a cache-key dimension. If the signature, expiry, or key-id is in the key, every user gets a unique object and the CDN is a very expensive reverse proxy.

**Design rule (all four vendors, same shape):** validate the signature *before* cache lookup; strip or ignore signing parameters in the key; forward only what the origin needs.

| Vendor | Token shape | Cache-key interaction |
|---|---|---|
| **CloudFront** | Canned: `Expires` + `Signature` + `Key-Pair-Id`. Custom: `Policy` (base64 JSON) + `Signature` + `Key-Pair-Id`. RSA **2048** or ECDSA **256**. Application query params must be signed *with* the URL; adding them after signing → **403**. CloudFront **removes** the signing params before the origin. Expiry is checked at request time. | Invalidate the path, not the query. CachingOptimized already excludes QS. Do not name your own params `Expires` / `Signature` / `Key-Pair-Id` / `Policy`. |
| **Cloudflare** | WAF `is_timed_hmac_valid_v0` (example TTL **10 800 s**); Workers HMAC-SHA256. | Default key includes the whole query. Exclude `verify` or set a Worker `cf.cacheKey` to `host + pathname`. |
| **Fastly** | HMAC over `path + expiration`. Example lifetime in the token-functions repo: **1 209 600 s** — an *example*, not a platform default. | Drop the token from `req.url` before `vcl_hash`. |
| **Akamai** | Auth Token 2.0 in query, cookie, or header. AMD: `hdnts` / `hdntl`. Cookie-less HLS embeds the session token in the segment path. | Strip or Cache-ID-exclude the query token. Path-embedded session tokens are a new object per session unless you rewrite. |

## Edge compute vs cache — placement

These are **where** a byte is computed, not which vendor's image product to buy.

| Placement | What runs there | Cache-key / shield consequence |
|---|---|---|
| **Origin** | App or an image service in-region. | CDN caches the *output* if the key includes the transform params (`w`, `h`, `fm`). Shield collapses the first-of-each-variant miss. |
| **Shield / upper-tier** | Transform once per variant, then fan out. | CloudFront: Lambda@Edge *origin-request / origin-response* run in the **Origin Shield Region**. Right place for "one transform per object." |
| **Every edge POP** | Per-request rewrite, A/B, auth, HTML assembly. | CloudFront Functions: **10 KB** / **2 MB** memory. Fastly Compute / VCL `vcl_recv`. Cloudflare Workers. Akamai EdgeWorkers. Do **not** put a unique `Authorization` in the cache key here. |
| **Pass-through (no cache)** | Personalized HTML, POST, WebSocket. | Dynamic acceleration only. |

Image variants are a cache-key problem: `?w=800` and `?w=801` are two objects. Normalize allowed widths at the edge (allow-list) before the key is computed, or the transform origin becomes a zip-bomb.

## Configuration

| Knob | Role | Too low | Too high |
|---|---|---|---|
| **Cache-key variance** (QS / cookie / header) | Correctness vs hit rate | Wrong body served | Hit rate collapses; purge cannot enumerate variants |
| **MinTTL / Edge TTL override** | Floor against origin `no-store` | Origin directives ignored for N seconds (CloudFront CachingOptimized = 1 s) | Personalized / auth responses cached |
| **`s-maxage` vs `max-age`** | Shared vs browser TTL | Browsers hold stale as long as the CDN | CDN revalidates constantly; browsers hold nothing |
| **`stale-while-revalidate`** | Hide refresh latency | Every expiry is a blocking miss (or a stampede) | Users see stale past the product contract |
| **`stale-if-error`** | Hide origin failure (C11 decides *whether*) | Errors become user-visible at the first 5xx | Stale-as-truth during a long outage |
| **Shield / upper-tier** | Collapse origin fan-out | Every POP hits origin (N-to-1 miss storm) | Extra hop on already-dynamic traffic |
| **Keep-alive** (CloudFront default 5 s) | Dynamic-acceleration reuse | Handshake per request | Idle sockets held at origin / ALB (keep CloudFront < ALB idle) |
| **Purge granularity** | Freshness without waiting for TTL | Purge-all as a deploy step (Fastly ≤ 2 min) | Orphaned variants live until TTL |
| **Signed-URL lifetime** | Authorization window | Downloads fail mid-retry after expiry | Token sharing / hotlinking |

### Library / platform defaults (registry-verified, 2026-09-13)

RFC 9111 dated June 2022. RFC 5861 dated May 2010. RFC 5861 example windows: 600 s fresh + 30 s SWR; SIE example 600 s fresh + 1 200 s stale-on-error. Error class for SIE: 500, 502, 503, 504.

| CloudFront policy (ID) | Min / Default / Max TTL | Key contents |
|---|---|---|
| CachingOptimized (`658327ea-f89d-4fab-a63d-7e88639e58f6`) | **1 / 86 400 / 31 536 000** s | No QS, no cookies; normalized `Accept-Encoding` |
| CachingDisabled (`4135ea2d-6df8-44a3-9df3-4b5a84be39ad`) | **0 / 0 / 0** | None |
| UseOriginCacheControlHeaders (`83da9c7e-98b4-4e11-a168-04f0df8e2c65`) | **0 / 0 / 31 536 000** s | Host, Origin, X-HTTP-Method*, all cookies, no QS |
| Amplify (`2e54312d-136d-493c-8eb9-b001f22f67d2`) | **2 / 2 / 600** s | Authorization, CloudFront-Viewer-Country, Host, all cookies, all QS |

API `CachePolicyConfig` DefaultTTL field default: **86 400 s**. Legacy behavior without a cache policy: default TTL **24 h**. Viewer `Cache-Control` / `Pragma` on GET **do not** force a CloudFront origin fetch. Invalidation: **150** paths-or-tags/s, **1** wildcard/s. Max cacheable GET **50 GB**. Request URL **8 192** bytes. Functions **10 KB**. Origin Shield Regions: `us-east-2`, `us-east-1`, `us-west-2`, `ap-south-1`, `ap-northeast-2`, `ap-southeast-1`, `ap-southeast-2`, `ap-northeast-1`, `eu-central-1`, `eu-west-1`, `eu-west-2`, `sa-east-1`, `me-central-1`.

**Fastly.** Hash default: URL + Host + generation. Headerless cacheable statuses (`200, 203, 300, 301, 302, 404, 410`) → TTL **2 min**; SWR/SIE **0**. UI fallback vs custom-VCL implicit TTLs disagree — set an explicit TTL. Hit-for-pass stored **120–3 690 s**.

**Cloudflare.** HTML and JSON are **not** cached by default (extension list only). Default Edge TTL when no `Cache-Control`/`Expires`: **120 m** (200/206/301), **20 m** (302/303), **3 m** (404/410). Cacheable file size: **512 MB** (Free/Pro/Business), default **5 GB** (Enterprise). Origin Cache Control: **on by default** for Free/Pro/Business. Cache-key customization (per-header / per-cookie / per-query include) is **Enterprise**. Request collapsing: one origin fetch per asset per datacenter.

**Akamai.** Required key parts: hostname + path; query **on** by default. Enhanced RFC Support: `honorMaxAge`, `honorSMaxage`, `honorMustRevalidate`, `honorProxyRevalidate`. Fast Purge default method: **Invalidate**.

## Observability

| Signal | Why |
|---|---|
| **Hit / miss / expire / updating / shield-hit** | CloudFront: `x-edge-result-type` / `x-edge-detailed-result-type` (`Hit`, `OriginShieldHit`, …). Cloudflare: `cf-cache-status` (`HIT`, `MISS`, `EXPIRED`, `UPDATING`, …) + `CacheTieredFill`. Akamai: `TCP_HIT` / `TCP_MISS` / `TCP_REFRESH_*` / `HitStale`. Fastly: `Fastly-Debug: 1` returns `Surrogate-Key`. |
| **Origin QPS next to edge QPS** | `origin_qps ≈ client_qps × (1 − hit_rate)`, now *per POP*, then collapsed by the shield. A 90% edge hit rate with no shield is still N POPs × miss rate at origin. |
| **`cdn-upstream-connect` / TTFB to origin** | Distinguishes cache-hit (no origin) from dynamic acceleration (connect dur = 0 means reuse). Argo analytics is origin-TTFB, not hit rate. |
| **Purge lag** | Fastly purge-all ≤ 2 min; CloudFront "Deployed" for Shield is "a few minutes" (no SLA). A dashboard that assumes instant global consistency is lying. |
| **Variant cardinality** | Unique keys per path (or `Surrogate-Key` class). Unbounded cookie/header variance shows up here, not in mean hit rate. |
| **401/403 on signed URLs** | Signature / clock / param-after-sign. Do not "fix" by putting the token in the key. |

Alert shapes (own formulations on documented fields — **not** vendor PromQL): *origin QPS ≫ baseline at constant edge QPS* (hit-rate collapse or shield bypass); *`UPDATING`/`OriginShieldHit` missing while SWR is configured* (SWR disabled by `s-maxage`); *purge-all duration above the documented bound*; *signed-URL 403 rate*. No CDN-specific OpenTelemetry semantic convention was found — use HTTP spans on the **origin** plus the vendor's access-log fields.

## Tuning

- **Hashed static:** long surrogate/`s-maxage` (Fastly example: 1 year surrogate, 1 day browser); purge-by-key or never.
- **HTML / JSON:** Cloudflare does not cache them until a Cache Rule says so. CloudFront CachingOptimized *will* cache them 24 h if the origin sends no `Cache-Control` — send headers or use `UseOriginCacheControlHeaders` (DefaultTTL **0**).
- **SWR + split browser/edge TTL:** Cloudflare workaround (`max-age` + SWR + Edge TTL, no `s-maxage`). CloudFront: `s-maxage` + Min/Max TTL; SWR still capped by MaxTTL. Fastly: `Surrogate-Control` vs `Cache-Control`.
- **`Set-Cookie` / logged-in HTML:** Cloudflare and Fastly skip cache. CloudFront MinTTL > 0 can override `private` — do not put CachingOptimized on that behavior.
- **Multi-CDN + expensive origin:** one innermost shield (CloudFront's documented shape), not one per CDN.
- **Cloudflare Smart Tiered + anycast cloud origin:** set the 2026-04-17 region hint or upper-tier selection is wrong.

## Worked calibration — media + HTML storefront

Design drill (not a vendor SLA). Constraints borrowed from the workspace video notes ([aws/ch20.md](../aws/ch20.md)) plus a typical storefront: 20 000 rps globally, ~85% of bytes `/static/*` or `/media/*`, ~15% `/` and `/api/*`; origin is a single-region packager + app; rollback of a bad CSS deploy must be < one change window.

| Slice | Cache key | Freshness | Shield | Purge / sign |
|---|---|---|---|---|
| `/static/{contenthash}.*` | Host + path. **Ignore query.** No cookies. | `Cache-Control: public, max-age=31536000, immutable` (browser = CDN). | Yes. Hash-in-path means a miss is a new object, not a stampede on the old one. | No purge. New hash = new object. |
| `/media/{id}` (identical bytes per id) | Host + path. **Strip** signed-URL params; validate first. | `s-maxage=86400, max-age=3600` **without** SWR if you need RFC-strict shared revalidate; **or** `max-age=3600, stale-while-revalidate=60` + CDN Edge/`Surrogate-Control` 86400 (Cloudflare's documented split). | Yes — CloudFront's JIT / image-origin case. | Invalidate `/media/{id}` (CloudFront: path only). Tokens: CloudFront canned; Cloudflare exclude `verify`. |
| `/` HTML | Host + path. No QS unless A/B is in a **named** cookie you accept. | Short: Fastly-class `max-age=0, s-maxage=60, stale-while-revalidate=30` (or Cloudflare Edge 60 s + SWR, **no** `s-maxage` if you want SWR there). | Optional. Helps only if many POPs miss together (deploy). | Soft-purge (Fastly) or URL purge on deploy. Do not purge-all if hashed static shares the service. |
| `/api/*` | Usually **pass**. If a public GET is cacheable: host + path + the *one* filter query; no `Authorization` in the key. | `Cache-Control: private, no-store` unless the handler is a public catalog. CloudFront: **CachingDisabled**, not CachingOptimized. | No — CloudFront would still charge Shield as dynamic. | — |
| Image `?w=` | Allow-list widths at the edge; key = path + normalized `w`. | Same as `/media`. Transform at **shield** (Lambda@Edge origin trigger / equivalent), not at every POP. | **Required** if the transform is expensive. | Purge by tag / surrogate-key `img:{id}` so all widths die together. |

Origin-QPS napkin (B3 identity, now with a shield). 17 000 rps static at 99% edge hit and a working shield ≈ tens of origin QPS, not 170. 3 000 rps HTML at 50% hit with no shield ≈ 1 500 origin QPS × POP-fanout; turning on a shield collapses the fan-out to ~1 500. The 10× Bronson loop ([C1](CircuitBreaker.md) / B3) still applies if you flush the shield.

## Failure modes of the CDN itself

- **Key explosion.** Session cookies, raw `Accept-Encoding`, signed-URL query params, or unbounded `?w=` produce one object per user / per token. Hit rate falls; origin sees "dynamic" traffic; purge cannot enumerate variants (CloudFront: you *cannot* invalidate by cookie or header value).
- **Key collision / stale poison.** Omitting a dimension the origin uses (`Host`, `Origin`, language) serves the wrong body as if it were fresh. Cloudflare default includes `Origin` and forwarded-host headers for this reason; they warn that custom keys plus URL normalization without "Normalize URLs to origin" enable poisoning.
- **`s-maxage` silently disables SWR** (Cloudflare + RFC 9111). Symptom: you set both headers and still block on every expiry (`EXPIRED`, not `UPDATING`).
- **MinTTL overrides `no-store`.** CloudFront CachingOptimized / Amplify: personalized HTML cached for 1–2 s (or worse if you raise MinTTL). Their own warning.
- **Shield SWR / soft-purge loop (Fastly).** Shield serves stale to the edge; edge re-caches it as fresh for the remaining `max-age`. Documented mitigation: disable SWR on the shield POP; rely on `Age` for ordinary expiry.
- **Shield miss after origin move.** Cloudflare: changing origin IPs / switching to anycast without a region hint reassigns upper-tiers and spikes `MISS`.
- **Purge that misses the key.** Cloudflare dashboard purge vs custom keys; CloudFront invalidation that omits a forwarded query; Fastly `vcl_hash` customized without keeping `req.vcl.generation` (purge-all stops working).
- **Signed URL in the key, or param added after signing.** Unique objects or 403. CloudFront checks expiry at *request* start; Range-retry after expiry fails.
- **Thundering herd to origin (capacity-cache flush).** Same loop as B3/C1, now at the shield: lose the upper-tier and every POP refills at once. Pair with [C1](CircuitBreaker.md); do not "just hit the origin." Without a shield, a deploy-time miss storm is N POPs × the same object. Request collapsing and the shield are the controls; a purge-all of a hot path is how you schedule the herd.
- **Caching an error.** Cloudflare default-caches 404/410 for **3 m**. Fastly cacheable statuses include 404/410. A bad deploy's 404 becomes a fleet fact until purge or TTL.
- **WebSocket / SSE through a cache behavior.** Uncacheable; you wanted A3/A4 + an idle timeout, not a cache policy.

## When not to use (a CDN cache, specifically)

| Situation | Prefer |
|---|---|
| Per-user HTML or anything with `Set-Cookie` / `Authorization` as the body selector | Pass / CachingDisabled; dynamic acceleration only. B3 session store stays behind the origin. |
| Write-heavy POST / mutating APIs | Do not cache. [C5](LoadBalancing.md) + origin LB. |
| Origin already a **latency cache** (SRE ch. 22, on B3): it can take full client QPS | CDN is optional complexity; use it for TLS offload / WAF if you still want the path. |
| You need *immediate* global correctness (prices, inventory, legal takedown) | Short TTL **and** Delete-class purge (Akamai Delete; Fastly hard purge); or uncacheable. Invalidate-only + IMS is not a takedown. |
| Freshness contract is "never stale, even on 503" | No SIE; [C11](GracefulDegradation.md) if you later *choose* stale as degradation. `must-revalidate` + no RFC 5861. |
| gRPC | CloudFront: Origin Shield is skipped. Not this card. |
| Small internal service, one region, no public clients | B3 next to the origin is cheaper than an edge fleet. |

## Trade-offs

| Buy | Pay |
|---|---|
| Origin offload; bytes at the POP | Another fleet of independent stores to fill, key, and purge |
| Shield collapses N-POP miss storms | Extra hop on already-dynamic traffic; SWR-at-shield bugs |
| `s-maxage` / surrogate TTL split from the browser | `s-maxage` forbids stale on RFC-strict shared caches (Cloudflare: SWR off) |
| RFC 5861 SWR hides refresh; SIE hides origin 5xx | Stale past the product contract; C11 must accept the window |
| Signed URLs keep private bytes off a public cache | Token-in-key shards the cache; param-after-sign is 403 |
| Versioned URLs retire purge | Old hashes occupy cache; HTML must change in lockstep |
| Edge compute normalizes keys / transforms once at shield | Unique `Authorization` in the key, or transform-at-every-POP, undoes the cache |

The application cache ([B3](../../docs/research/sysdesign/b3-caching-external-research.md)) decides **what the origin remembers**. This card decides **what the public path remembers**, and for how long. [C5](LoadBalancing.md) places the origin request that still happens. [C3](FailoverHealth.md) decides when that origin is dead. [C11](GracefulDegradation.md) decides whether stale bytes are an acceptable answer. [C1](CircuitBreaker.md) is what you pair with a shield flush so the refill does not take the origin down.

## Sources

Verified 2026-09-13; the full URL list, per-claim provenance, and the items deliberately left out are in the [external research note](../../docs/research/sysdesign/b8-cdn-edge-external-research.md). Do not promote §8 of that note (unverified `s-maxage`+SWR on Fastly/CloudFront as a universal rule; Akamai SWR as a first-class Property Manager option; Fastly implicit-TTL which-one; image-product bake-offs; OTel CDN conventions; PromQL recipes) into this card.

- Canon: RFC 9111 (STD 98, June 2022); RFC 5861 (May 2010, Informational).
- Vendors (fetched 2026-09-13): CloudFront cache policy, expiration, Origin Shield, invalidation, signed URLs, origin timeouts; Fastly `vcl_hash`, freshness, stale, shielding, purging; Cloudflare cache keys, default behavior, revalidation, Tiered Cache, Argo, token auth; Akamai Property Manager caching, Fast Purge, Auth Token 2.0.
- Adjacent in this tree: [B3 research](../../docs/research/sysdesign/b3-caching-external-research.md); [CircuitBreaker.md](CircuitBreaker.md); [GracefulDegradation.md](GracefulDegradation.md); [aws/ch09.md](../aws/ch09.md); [aws/ch20.md](../aws/ch20.md).
