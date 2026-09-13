---
type: research
title: 'CDN & edge — external research (2026-09-13)'
description: >-
  Source-verified Group B research for B8: HTTP cache-key variance at the
  edge, TTL vs s-maxage vs RFC 5861 stale-while-revalidate, origin shield,
  purge/invalidation, signed URLs, and dynamic acceleration as TCP+TLS
  proxying versus a cache hit. Vendor defaults fetched 2026-09-13.
tags: [research, system-design-patterns, B8, cdn, edge]
---

# CDN & edge — external research (2026-09-13)

> **What this is.** The evidence pass for catalog id **B8** (slug `b8-cdn-edge`),
> at the CircuitBreaker.md operational depth bar. This note is research, not a
> Concept. Primary pages fetched **2026-09-13**. Paraphrase; numbers and
> identifiers reproduced exactly. Items that could not be verified are in §8
> and are **not** to be asserted as fact later.
>
> **Owns.** HTTP edge cache keys (host / path / query / cookie / header
> variance); freshness (`max-age`, `s-maxage`, RFC 9111 vs RFC 5861 SWR/SIE);
> origin shield / tiered cache; purge and invalidation; signed URLs as a
> cache-key problem; dynamic acceleration as connection reuse vs cache-hit;
> image transform and edge compute as *placement*.
>
> **Does not own.** Application aside / through / behind caches (**B3** —
> cite, do not rewrite). Load balancing (**C5**). Serving stale as a
> *degradation* / kill-switch mode (**C11**). WebSocket / SSE (usually
> uncacheable; **A3** / **A4**).

---

## 1. Scope and non-goals

**This note owns** the cache that sits *in front of* an origin on the public
HTTP path: how an edge POP decides that two requests are the same object,
how long that object stays fresh, how a mid-tier *shield* collapses origin
fan-out, how operators evict it, how a signed URL must not explode the key,
and what a CDN still does when the object is uncacheable (TCP + TLS
proxying on a persistent origin connection).

**Non-goals (sibling ids)**

| Id | What they own; do not re-derive here |
|---|---|
| **B3** | Application / data-plane caches: aside, through, behind; Redis / Memcached eviction; stampede locks / XFetch / leases. RFC 9111 / 5861 are cited there only as the HTTP *boundary*. This note is that boundary. |
| **C5** | Load-balancing algorithms, health-check fail-open, anycast vs DNS. A CDN *uses* an LB at the origin; it is not the LB card. |
| **C11** | Deliberately serving stale while the origin is unhealthy as a *product degradation* / kill switch. RFC 5861 `stale-if-error` is the HTTP *mechanism*; C11 owns when the business accepts it. |
| **A3 / A4** | WebSocket lifecycle and SSE reconnect. Both are usually uncacheable; CloudFront's WebSocket idle timeout (10 min) is cited only as a quota. |
| **A1** | REST / gRPC request–response wire semantics. `Cache-Control` rides on A1 responses. |
| **C1** | Circuit breaker. The cache-down → origin flood loop (Gabrielson; Bronson 10×; Slack 2022-02-22) stays on C1 / B3. |

**Existing notes to link, not rewrite:**
[B3 caching research](b3-caching-external-research.md);
[CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md);
[aws/ch09.md](../../../cases/aws/ch09.md) (CloudFront as an AWS entry
point); [aws/ch20.md](../../../cases/aws/ch20.md) (Origin Shield in a
video-distribution sketch).

---

## 2. Lineage / vocabulary

Named sources (all fetched 2026-09-13). Mechanics in §3 reuse these facts.

| Source | Vocabulary / claim that matters |
|---|---|
| **RFC 9111** (STD 98, June 2022; obsoletes 7234) | HTTP caching. Shared vs private cache. Freshness: `s-maxage` (shared only) overrides `max-age` / `Expires` inside a shared cache and **incorporates `proxy-revalidate`** — a shared cache MUST NOT reuse a stale `s-maxage` response until it has validated with the origin. `must-revalidate` / `no-cache` / applicable `s-maxage` or `proxy-revalidate` forbid generating a stale response. A cache MUST NOT serve stale unless disconnected **or** explicitly permitted (`max-stale`, RFC 5861 extensions, or an out-of-band contract). Shared caches MUST NOT reuse a response to a request with `Authorization` unless `must-revalidate`, `public`, or `s-maxage` is present. https://www.rfc-editor.org/rfc/rfc9111.html |
| **RFC 5861** (May 2010, **Informational**, not Standards Track) | Two independent extensions. `stale-while-revalidate=N`: MAY serve stale for N seconds while revalidating **without blocking**; if N passes without revalidation, SHOULD NOT continue. Example: `max-age=600, stale-while-revalidate=30`. `stale-if-error=N`: MAY serve stale on 500 / 502 / 503 / 504 (or equivalent network/DNS failure) up to N seconds of staleness. Security: background revalidation SHOULD be request-triggered to avoid amplification. https://httpwg.org/specs/rfc5861.html |
| **CloudFront cache policy + expiration** | Cache key = query strings + headers + cookies you *opt in*; those values are also forwarded to origin (use an **origin request policy** to forward without varying). Managed **CachingOptimized**: MinTTL **1 s**, DefaultTTL **86 400 s**, MaxTTL **31 536 000 s** (365 d); no QS, no cookies; normalized `Accept-Encoding` only. **CachingDisabled**: all TTLs **0**. MinTTL > 0 **overrides** origin `no-cache` / `no-store` / `private`. SWR and SIE supported; each is capped by MaxTTL. https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-managed-cache-policies.html · https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Expiration.html |
| **CloudFront Origin Shield** | Extra regional cache in front of the origin. All RECs go through one chosen Region (list of 13 Regions in the page). GET/HEAD with TTL < **3600 s**, or caching disabled, count as **dynamic** (always an incremental Shield hop). gRPC bypasses Shield. Log token: `OriginShieldHit` in `x-edge-detailed-result-type` (a REC-as-Shield hit is logged as `Hit`). https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/origin-shield.html |
| **Fastly `vcl_hash` + freshness** | Default hash: `req.url` (includes query) + `req.http.host` + `req.vcl.generation` (purge-all generation). Method and TLS-vs-HTTP are ignored. Prefer `Vary` over stuffing the hash. TTL preference: `Surrogate-Control: max-age` → `Cache-Control: s-maxage` → `max-age` → `Expires`; **default 2 min** when none present. SWR / SIE default **0**. Soft purge + SWR at a shield can re-cache stale as fresh at the edge. https://www.fastly.com/documentation/reference/vcl/subroutines/hash · https://www.fastly.com/documentation/guides/concepts/cache/cache-freshness/ |
| **Cloudflare cache key + default TTL** | Default key: scheme + host + URI **with query** + `Origin` + `x-http-method-override` / `x-http-method` / `x-method-override` + several forwarded-host / rewrite headers. HTML and JSON are **not** cached by default (extension list only). Default Edge TTL when no `Cache-Control`/`Expires`: **120 m** (200/206/301), **20 m** (302/303), **3 m** (404/410). SWR is origin-header-driven; `s-maxage` / `must-revalidate` / `proxy-revalidate` / `no-cache` disable SWR (RFC 9111 §4.2.4). Page last-updated **2026-09-03** (default behavior) / **2026-08-28** (cache keys). https://developers.cloudflare.com/cache/how-to/cache-keys/ · https://developers.cloudflare.com/cache/concepts/default-cache-behavior/ · https://developers.cloudflare.com/cache/concepts/revalidation/ |
| **Akamai Property Manager** | Cache key always includes hostname (incoming `Host` or origin hostname) and path; query strings optional **but added by default**; headers / cookies / variables optional via **Cache ID Modification**. Cache is **per edge server**, not a monolithic store. Caching behavior honors `s-maxage` under **Enhanced RFC Support** (cited as RFC 7234 on the page). Fast Purge: **Invalidate** (conditional GET / IMS; default) vs **Delete**. https://techdocs.akamai.com/property-mgr/docs/know-caching · https://techdocs.akamai.com/purge-cache/docs/purge-methods |

---

## 3. Mechanics (Group B depth)

### 3.1 What an edge cache is (and is not)

A CDN POP stores an HTTP **response** keyed by a **cache key** derived from
the request. A later request that hashes to the same key is a **hit** and
never reaches the origin. A miss (or a revalidation) goes origin-ward,
optionally through a **shield / upper-tier** that collapses duplicate
misses. That is the opposite of B3's application cache: the caller is an
anonymous (or cookied) HTTP client, the store is shared and multi-tenant,
and invalidation is a *fleet* problem (every POP, every variant).

Two different products share the word "acceleration":

| Mode | What the POP does | Origin load |
|---|---|---|
| **Cache-hit** | Return bytes from the POP (or shield). | Zero for that request. |
| **Dynamic acceleration** | Proxy the request on a **kept-alive** origin TCP/TLS session (and often a better path to the origin). | One origin request; handshake cost is amortized. |

CloudFront states the dynamic case explicitly: persistent connections
"save the time required to re-establish the TCP connection and perform
another TLS handshake"; keep-alive default **5 s** (range 1–300 s);
connection timeout default **10 s**, **3** attempts (up to 30 s before
failover / error); response timeout default **30 s** (range 1–120 s).
`cdn-upstream-connect;dur=0` in Server-Timing means the origin connection
was reused. Origin Shield treats PUT/POST/PATCH/DELETE and GET/HEAD with
TTL < 3600 s as dynamic — Shield is then *always* an extra hop.

Cloudflare **Argo Smart Routing** (now packaged under Smart Shield; docs
updated 2026-08-25 / 2026-04-16) is the path-optimization cousin: it
minimizes origin TTFB by avoiding congested Internet paths. It does **not**
create a cache hit. **Tiered Cache** is the shield cousin.

### 3.2 Cache-key design (the variance problem)

The key is the product of every request dimension you *choose* to vary on.
Every extra dimension multiplies stored objects and **cuts hit rate**.
Every omitted dimension that the origin actually uses is a **correctness**
bug (wrong language, wrong auth, cache poisoning via a forwarded host
header).

| Dimension | When to include | Failure if wrong |
|---|---|---|
| **Scheme** | When origin content differs on HTTP vs HTTPS. Cloudflare default key uses *origin* scheme; changing Flexible → Full **busts** the default key. Fastly default **ignores** TLS-vs-HTTP. CloudFront caches once even if viewers use both (match-viewer). | Poisoning or a silent cache miss storm after an SSL-mode change. |
| **Host** | Always, unless you deliberately collapse aliases. Fastly and Akamai default-include it. Cloudflare Host setting: original vs resolved (Origin Rule). | Serving tenant A's site for tenant B. |
| **Path** | Always (normalized). | — |
| **Query string** | Only parameters the origin *uses to select bytes*. Drop `utm_*`, cache-busters you do not honor, and **signed-URL tokens** (see §3.6). CloudFront **CachingOptimized** includes **none**; Cloudflare default includes **all**; Fastly includes the whole `req.url`; Akamai adds query **by default**. | Including all = shard the cache on every tracker. Including none = serve one variant to every query. |
| **Cookie** | Only cookies that change the body (A/B, currency). Never session IDs if the body is public. CloudFront CachingOptimized: **none**. Cloudflare default: cookies are *not* in the key (Enterprise custom keys can add them; `__cf*` cookies cannot). | One cookie in the key × N users = N objects. |
| **Header** | `Accept-Language`, `Accept-Encoding` (normalize), CORS `Origin`, device class. Do **not** vary on `Authorization` unless the response is `public` / `s-maxage` / `must-revalidate` (RFC 9111 §3.5) *and* you intend per-credential objects. Cloudflare default already includes `Origin` and method-override headers (CORS / cache-poisoning defense). CloudFront normalizes `Accept-Encoding` to `br,gzip` / `gzip` / omitted. | `Accept-Encoding` un-normalized = one object per browser string. |
| **Method** | GET/HEAD are the cacheable methods. Fastly default hash ignores method because non-GET is typically passed. Cloudflare: anything other than GET is not cached by default. CloudFront: only GET responses are cached (max object **50 GB**). | Caching POST is a correctness incident. |

**Cache key vs origin request.** CloudFront's split is the cleanest
statement of the design rule: everything in the cache policy is in the
origin request; an **origin request policy** forwards extra headers /
cookies / query strings *without* varying. Fastly equivalent: hash on
normalized fields, `req.http.*` still goes to origin. Cloudflare custom
keys that ignore query still *send* the query unless you rewrite it.

**Vary vs hash.** Fastly's `vcl_hash` page prefers `Vary` for language /
location: one stored object with a vary list, rather than N hashes you
must purge individually. The trade-off is implementation complexity at
the POP; CloudFront has no first-class `Vary` cache-key UI — you list
headers instead.

### 3.3 Freshness: TTL vs `s-maxage` vs RFC 5861

Three clocks, one object:

1. **Browser freshness** — `Cache-Control: max-age` / `Expires`. The CDN
   does not control this once the bytes left the POP (B3's "HTTP
   cache-busting query string" is the same idea at this layer).
2. **Shared-cache freshness** — `s-maxage` (RFC 9111 §5.2.2.10) or a
   CDN-specific surrogate (`Surrogate-Control: max-age` at Fastly;
   CloudFront Min/Default/Max TTL; Cloudflare Edge Cache TTL; Akamai
   property TTL / `honorSMaxage`).
3. **Stale window** — RFC 5861 `stale-while-revalidate` (hide
   revalidation latency) and `stale-if-error` (hide origin failure).

RFC 9111's `s-maxage` **is not** "CDN `max-age`." It also means
`proxy-revalidate`: a shared cache must not serve that object stale.
Cloudflare's revalidation page (fetched 2026-09-13; page date 2026-06-26)
states the operational consequence: if `s-maxage` (or
`must-revalidate` / `proxy-revalidate` / `no-cache`) sits next to
`stale-while-revalidate`, Cloudflare will **not** serve stale — status
`EXPIRED` instead of `UPDATING`. Their documented workaround for "long
edge TTL, short browser TTL, plus SWR": send `max-age` +
`stale-while-revalidate`, then set Edge Cache TTL in Cache Rules. Do
**not** use `s-maxage` for that split.

CloudFront's SWR example (`max-age=3600, stale-while-revalidate=600`)
serves stale up to 10 minutes **or MaxTTL, whichever is less**. SIE
example (`stale-if-error=86400`) is likewise capped by MaxTTL. Combining
both: SWR covers the first 600 s of background refresh; SIE covers up to
24 h if the origin errors during that refresh.

Fastly's documented recipe:
`Cache-Control: max-age=300, stale-while-revalidate=60, stale-if-error=86400`
(or the same on `Surrogate-Control`, which Fastly prefers and **strips
before the client** — except when shielding, so the edge POP still sees
it). SWR and SIE windows **start together** at freshness expiry. Default
SWR/SIE TTL is **0** (off) until a header or VCL sets them.
`req.hash_always_miss` / `req.hash_ignore_busy` disable SWR/SIE for that
request.

**Request collapsing** is the stampede control at this layer (B3 owns the
application-lock family). Cloudflare: a per-datacenter cache lock; only
the first miss of a given asset goes to origin; waiters are streamed the
same response. Fastly clustering / shielding is the same shape across
POPs. CloudFront Origin Shield "consolidates" simultaneous requests for
the same object to "as few as one" origin fetch.

### 3.4 Origin shield / tiered cache

| Vendor | Mechanism | Placement rule (sourced) |
|---|---|---|
| **CloudFront Origin Shield** | One extra REC in a chosen Region; skip the hop if the request already landed in that Region. | Same Region as an in-Region origin; otherwise the pairing table (e.g. `us-west-1` → `us-west-2`). Multi-CDN: other CDNs use CloudFront as *their* origin so one Shield absorbs them. Failover: secondary Shield Region via active error tracking. |
| **Fastly shielding** | One designated shield POP per backend (`amsterdam-nl` is the shield id for AMS). | Choose the POP closest to the origin. Clustering disabled by `Fastly-No-Shield: 1`, `return(pass)`, restart, or a delivery-node hit. Age is forwarded so the edge does not treat shield-stale as fresh — **except** soft-purge + SWR (see §5). |
| **Cloudflare Tiered Cache** | Lower-tier → upper-tier; only upper-tiers talk to origin. Smart topology picks one closest upper-tier from latency data. | Smart + Generic Global + Regional + Custom. Public-cloud anycast origins need a **cloud region hint** (`aws:us-east-1`, …) — changelog **2026-04-17**, all plan types. Load Balancing: one upper-tier for the **whole pool**. Confirm with `CacheTieredFill` in logs. |
| **Akamai** | Site Shield / Tiered Distribution: child POP → parent → origin. | `Miss from child, Hit from parent` on Return Cache Status. Site Shield also hides origin IPs (security product; not a cache-key). |

Shield is **not** a second CDN. It is a fan-in of *misses*. It helps
just-in-time packaging and image transforms (CloudFront's named use
cases) because those origins are expensive per miss. It hurts
low-cacheability / rarely-requested objects (CloudFront: "may not be a
good fit") because every miss pays an extra hop.

### 3.5 Purge / invalidation

TTL bounds *staleness*; purge is the operator's "this byte is wrong
*now*." The two compose: a forgotten purge lasts the TTL; a purge without
TTL still needs the next miss to refill.

| Vendor | Mechanism | Verified limits / gotchas |
|---|---|---|
| **CloudFront** | Path invalidation (and cache-tag invalidation). Signed URLs: invalidate **only the path before `?`**. Cookie / header variants: one invalidation drops **all** variants; you cannot select. Query-forwarding: you **must** include the query in the path. Directory: invalidate with *and* without trailing `/`. Path max **4 000** characters. | **150** paths or tags / s; **1** wildcard invalidation / s. No cap on files per wildcard or per tag. |
| **Fastly** | URL purge; surrogate-key purge; purge-all (increments `req.vcl.generation`, objects become unreachable and age out). Soft purge marks stale (pairs with SWR). `Surrogate-Key` tokens ≤ **1 KB**, header ≤ **16 KB**; Fastly strips the header unless `Fastly-Debug`. Purge-all: up to **2 minutes**; incompatible with soft / bulk purge. | Soft-purge + shielding can re-cache stale as fresh at the edge (§5). |
| **Cloudflare** | Purge everything; by URL; by tag; by hostname; by prefix. Custom cache keys that include headers/cookies: dashboard single-file purge **will not** hit them — API must send the same headers (incl. `CF-Device-Type`, `CF-IPCountry`, `Accept-Language`). Missing header = empty value in the key. | Prefetch always uses the **default** key — mismatch with custom keys. |
| **Akamai Fast Purge** | **Invalidate** (default): next request is IMS / `If-Modified-Since`; 304 keeps the object. **Delete**: drop the bytes; next request is a full GET. Invalidate can still serve stale if origin is down (when configured). ECCU enhanced purge is invalidate-only. Purge is not persistent — the edge executes and forgets. | Delete is the compliance tool; it costs more origin bandwidth. |

**Versioned URLs** (content-hash in the path) are the purge you do not
have to issue. They are B3's generation-key idea at the edge. Trade-off:
old hashes occupy cache until eviction; HTML that references them must
change in lockstep.

### 3.6 Signed URLs (auth in the query string)

A signed URL is an authorization *token*, not a cache-key dimension. If
the signature, expiry, or key-id is in the key, every user gets a unique
object and the CDN is a very expensive reverse proxy.

**Design rule (all four vendors, same shape):** validate the signature
*before* cache lookup; strip or ignore signing parameters in the key;
forward only what the origin needs.

| Vendor | Token shape (fetched) | Cache-key interaction |
|---|---|---|
| **CloudFront** | Canned: `Expires` (Unix UTC seconds) + `Signature` + `Key-Pair-Id`. Custom: `Policy` (base64 JSON: `DateLessThan` / optional `DateGreaterThan` / optional IP) + `Signature` + `Key-Pair-Id`. RSA **2048** or ECDSA **256**. Application query params must be signed *with* the URL; adding them after signing → **403**. CloudFront **removes** `Expires` / `Key-Pair-Id` / `Policy` / `Signature` before the origin. Expiry is checked at request time; an in-flight download may finish, a restart after expiry fails. | Invalidate the path, not the query. Do not name your own params `Expires` / `Signature` / `Key-Pair-Id` / `Policy` / `Hash-Algorithm`. CachingOptimized already excludes QS — good for signed media if the object is otherwise identical. |
| **Cloudflare** | WAF `is_timed_hmac_valid_v0(secret, http.request.uri, ttl, timestamp, sep_len)` (example TTL **10 800 s** = 3 h; `verify=timestamp-mac`). Workers HMAC-SHA256 example. | Default key includes the whole query → every token is a unique object. Exclude `verify` (Enterprise query include/exclude) or set a Worker `cf.cacheKey` to `host + pathname`. |
| **Fastly** | HMAC token over `path + expiration` (official `token-functions` / "Enabling URL token validation"). Example lifetime in that repo: **1 209 600 s** (2 weeks) — an *example*, not a platform default. | Drop the token from `req.url` before `vcl_hash`, or every token shards the cache. |
| **Akamai** | Auth Token 2.0: token in query, cookie, or header; HMAC over delimited fields. AMD: access token `hdnts`, session token `hdntl`. Cookie-less HLS embeds the session token in the segment path. | If the token is in the query and query is in the default key, strip or Cache-ID-exclude it. Session tokens in the *path* are a new object per session unless you rewrite. |

### 3.7 Image transform and edge compute — placement, not a product review

These are **where** a byte is computed, not which vendor's image product
to buy.

| Placement | What runs there | Cache-key / shield consequence |
|---|---|---|
| **Origin** | App or an image service in-region. | CDN caches the *output* if the key includes the transform params (`w`, `h`, `fm`). Shield collapses the first-of-each-variant miss. |
| **Shield / upper-tier** | Transform once per variant, then fan out to edges. | CloudFront: Lambda@Edge *origin-request / origin-response* run in the **Origin Shield Region** (and fail over with it). This is the right place for "one transform per object." |
| **Every edge POP** | Per-request rewrite, A/B, auth, HTML assembly. | CloudFront Functions: **10 KB** / **2 MB** memory (quota page). Fastly Compute / VCL `vcl_recv`. Cloudflare Workers. Akamai EdgeWorkers. Do **not** put a unique `Authorization` in the cache key here. |
| **Pass-through (no cache)** | Personalized HTML, POST, WebSocket. | Dynamic acceleration only. CloudFront WebSocket origin idle timeout: **10 minutes**. That quota lives on **A3**. |

Image variants are a cache-key problem: `?w=800` and `?w=801` are two
objects. Normalize allowed widths at the edge (allow-list) before the
key is computed, or the transform origin becomes a zip-bomb.

### 3.8 Knobs

| Knob | Role | Too low | Too high |
|---|---|---|---|
| **Cache-key variance** (QS / cookie / header) | Correctness vs hit rate | Wrong body served | Hit rate collapses; purge cannot enumerate variants |
| **MinTTL / Edge TTL override** | Floor against origin `no-store` | Origin directives ignored for N seconds (CloudFront CachingOptimized = 1 s) | Personalized / auth responses cached |
| **`s-maxage` vs `max-age`** | Shared vs browser TTL | Browsers hold stale as long as the CDN | CDN revalidates constantly; browsers hold nothing |
| **`stale-while-revalidate`** | Hide refresh latency | Every expiry is a blocking miss (or a stampede) | Users see stale past the product contract |
| **`stale-if-error`** | Hide origin failure (C11 decides *whether*) | Errors become user-visible at the first 5xx | Stale-as-truth during a long outage |
| **Shield / upper-tier** | Collapse origin fan-out | Every POP hits origin (N-to-1 miss storm) | Extra hop on already-dynamic traffic |
| **Keep-alive** (CloudFront default 5 s) | Dynamic-acceleration reuse | Handshake per request | Idle sockets held at origin / ALB (keep CloudFront < ALB idle) |
| **Purge granularity** | Freshness without waiting for TTL | Purge-all (generation bump; Fastly ≤ 2 min) as a deploy step | Orphaned variants live until TTL |
| **Signed-URL lifetime** | Authorization window | Downloads fail mid-retry after expiry | Token sharing / hotlinking |

### 3.9 Observability

| Signal | Why |
|---|---|
| **Hit / miss / expire / updating / shield-hit** | CloudFront: `x-edge-result-type` / `x-edge-detailed-result-type` (`Hit`, `OriginShieldHit`, …). Cloudflare: `cf-cache-status` (`HIT`, `MISS`, `EXPIRED`, `UPDATING`, …) + `CacheTieredFill`. Akamai: `TCP_HIT` / `TCP_MISS` / `TCP_REFRESH_*` / `HitStale` via Pragma `akamai-x-check-cacheable` / `akamai-x-get-cache-key`. Fastly: `Fastly-Debug: 1` returns `Surrogate-Key`. |
| **Origin QPS next to edge QPS** | B3's identity still holds: `origin_qps ≈ client_qps × (1 − hit_rate)`, now *per POP*, then collapsed by the shield. A 90% edge hit rate with no shield is still N POPs × miss rate at origin. |
| **`cdn-upstream-connect` / TTFB to origin** | Distinguishes cache-hit (no origin) from dynamic acceleration (connect dur = 0 means reuse). Argo analytics is origin-TTFB, not hit rate. |
| **Purge lag** | Fastly purge-all ≤ 2 min; CloudFront "Deployed" for Shield is "a few minutes" (no SLA). A dashboard that assumes instant global consistency is lying. |
| **Variant cardinality** | Count unique keys per path (or `Surrogate-Key` class). Unbounded cookie/header variance shows up here, not in mean hit rate. |
| **401/403 on signed URLs** | Signature / clock / param-after-sign. Do not "fix" by putting the token in the key. |

Alert shapes (own formulations on documented fields — **not** vendor
PromQL; see §8): *origin QPS ≫ baseline at constant edge QPS* (hit-rate
collapse or shield bypass); *`UPDATING`/`OriginShieldHit` missing while
SWR is configured* (SWR disabled by `s-maxage`); *purge-all duration
above the documented bound*; *signed-URL 403 rate*.

OpenTelemetry: no CDN-specific semantic convention was found. Use HTTP
server/client spans on the **origin** plus the vendor's access-log
fields as the edge signal. Cloudflare cache spans are not a stable OTel
convention (B3 already recorded the negative result for application
cache).

### 3.10 Tuning

- **Hashed static:** long surrogate/`s-maxage` (Fastly example: 1 year
  surrogate, 1 day browser); purge-by-key or never.
- **HTML / JSON:** Cloudflare does not cache them until a Cache Rule
  says so. CloudFront CachingOptimized *will* cache them 24 h if the
  origin sends no `Cache-Control` — send headers or use
  `UseOriginCacheControlHeaders` (DefaultTTL **0**).
- **SWR + split browser/edge TTL:** Cloudflare workaround (`max-age` +
  SWR + Edge TTL, no `s-maxage`). CloudFront: `s-maxage` + Min/Max TTL;
  SWR still capped by MaxTTL. Fastly: `Surrogate-Control` vs
  `Cache-Control`.
- **`Set-Cookie` / logged-in HTML:** Cloudflare and Fastly skip cache.
  CloudFront MinTTL > 0 can override `private` — do not put
  CachingOptimized on that behavior.
- **Multi-CDN + expensive origin:** one innermost shield (CloudFront's
  documented shape), not one per CDN.
- **Cloudflare Smart Tiered + anycast cloud origin:** set the 2026-04-17
  region hint or upper-tier selection is wrong.

### 3.11 Worked calibration — media + HTML storefront

Design drill (not a vendor SLA). Constraints borrowed from the workspace
video notes ([aws/ch20.md](../../../cases/aws/ch20.md)) plus a typical
storefront: 20 000 rps globally, ~85% of bytes are `/static/*` or
`/media/*`, ~15% is `/` and `/api/*`; origin is a single-region
packager + app; rollback of a bad CSS deploy must be < one change
window.

| Slice | Cache key | Freshness | Shield | Purge / sign |
|---|---|---|---|---|
| `/static/{contenthash}.*` | Host + path. **Ignore query.** No cookies. | `Cache-Control: public, max-age=31536000, immutable` (browser = CDN). CloudFront CachingOptimized is acceptable (DefaultTTL 24 h is a floor if headers are missing — still send the header). | Yes. Hash-in-path means a miss is a new object, not a stampede on the old one. | No purge. New hash = new object. |
| `/media/{id}` (identical bytes per id) | Host + path. **Strip** signed-URL params from the key; validate first. | `s-maxage=86400, max-age=3600` **without** SWR if you need RFC-strict shared revalidate; **or** `max-age=3600, stale-while-revalidate=60` + CDN Edge/`Surrogate-Control` 86400 (Cloudflare's documented split). | Yes — this is CloudFront's JIT / image-origin case. | Invalidate `/media/{id}` (CloudFront: path only). Tokens: CloudFront canned `Expires`+`Signature`+`Key-Pair-Id`; Cloudflare exclude `verify`. |
| `/` HTML | Host + path. No QS unless A/B is in a **named** cookie you accept. | Short: Fastly-class `max-age=0, s-maxage=60, stale-while-revalidate=30` (or Cloudflare Edge 60 s + SWR, **no** `s-maxage` if you want SWR there). | Optional. HTML miss rate is already high; shield helps only if many POPs miss together (deploy). | Soft-purge (Fastly) or URL purge on deploy. Do not purge-all if hashed static shares the service (Fastly: omit the `all` surrogate key on `immutable` objects). |
| `/api/*` | Usually **pass**. If a public GET is cacheable: key = host + path + the *one* filter query; no `Authorization` in the key. | `Cache-Control: private, no-store` unless the handler is a public catalog. CloudFront: attach **CachingDisabled** (all TTLs 0), not CachingOptimized. | No — CloudFront would still charge Shield as dynamic. | — |
| Image `?w=` | Allow-list widths at the edge; key = path + normalized `w`. | Same as `/media`. Transform at **shield** (Lambda@Edge origin trigger / equivalent), not at every POP. | **Required** if the transform is expensive. | Purge by tag / surrogate-key `img:{id}` so all widths die together. |

Origin-QPS napkin (B3 identity, now with a shield). 17 000 rps static at
99% edge hit and a working shield ≈ tens of origin QPS, not 170. 3 000
rps HTML at 50% hit with no shield ≈ 1 500 origin QPS × POP-fanout;
turning on a shield collapses the fan-out to ~1 500. The 10× Bronson
loop (C1 / B3) still applies if you flush the shield.

### 3.12 Placement

| Layer | Typical mechanism | State scope | Trade-off |
|---|---|---|---|
| **Browser / private cache** | `max-age`, `private` | Per user | You cannot purge it. Version the URL. |
| **Edge POP** | Vendor cache key + TTL | Per POP (Akamai: per *server*) | Closest bytes; N independent stores to fill and purge. |
| **Regional / shield / upper-tier** | Origin Shield, Fastly shield POP, Cloudflare upper-tier, Akamai parent | One (or few) locations | Origin offload; extra hop; SWR-at-shield bugs. |
| **Origin** | App, packager, B3 Redis | Your DC | Source of truth. Size it for miss QPS at worst hit rate, or treat the CDN as a **capacity cache** (SRE ch. 22, already on B3). |
| **Edge compute** | Functions / Workers / VCL / EdgeWorkers | Per request at that POP | Auth, rewrite, normalize keys. Not a second origin of record. |

---

## 4. Verified defaults / standards (fetched 2026-09-13)

**RFC.** RFC 9111 dated June 2022 (STD 98). RFC 5861 dated May 2010
(Informational). RFC 5861 example windows: 600 s fresh + 30 s SWR; SIE
example 600 s fresh + 1 200 s stale-on-error. Error class for SIE: 500,
502, 503, 504.

**CloudFront managed cache policies**

| Policy (ID) | Min / Default / Max TTL | Key contents |
|---|---|---|
| CachingOptimized (`658327ea-f89d-4fab-a63d-7e88639e58f6`) | **1 / 86 400 / 31 536 000** s | No QS, no cookies; normalized `Accept-Encoding` |
| CachingOptimizedForUncompressedObjects (`b2884449-e4de-46a7-ac36-70bc7f1ddd6d`) | 1 / 86 400 / 31 536 000 s | Same, compression off |
| CachingDisabled (`4135ea2d-6df8-44a3-9df3-4b5a84be39ad`) | **0 / 0 / 0** | None |
| UseOriginCacheControlHeaders (`83da9c7e-98b4-4e11-a168-04f0df8e2c65`) | **0 / 0 / 31 536 000** s | Host, Origin, X-HTTP-Method*, all cookies, no QS |
| UseOriginCacheControlHeaders-QueryStrings (`4cc15a8a-d715-48a4-82b8-cc0b614638fe`) | 0 / 0 / 31 536 000 s | Same + all QS |
| Amplify (`2e54312d-136d-493c-8eb9-b001f22f67d2`) | **2 / 2 / 600** s | Authorization, CloudFront-Viewer-Country, Host, all cookies, all QS |
| Elemental-MediaPackage (`08627262-05a9-4f76-9ded-b50ca2e3a84f`) | 0 / 86 400 / 31 536 000 s | Origin; QS `aws.manifestfilter`, `start`, `end`, `m` |

API `CachePolicyConfig` DefaultTTL field default: **86 400 s** (or MinTTL
if MinTTL > 86 400). Legacy behavior without a cache policy: default TTL
**24 h**. `max-age` supported range: **0 s – 100 years**. Viewer
`Cache-Control` / `Pragma` on GET **do not** force a CloudFront origin
fetch.

**CloudFront origin / Shield / quotas.** Keep-alive **5 s** default
(1–300). Connection timeout **10 s** (1–10), attempts **3**. Response
timeout **30 s** (1–120). Invalidation: **150** paths-or-tags/s, **1**
wildcard/s, path **4 000** chars. Max cacheable GET **50 GB**. Request
URL **8 192** bytes. Functions **10 KB**. WebSocket origin idle **10
min**. Origin Shield Regions: `us-east-2`, `us-east-1`, `us-west-2`,
`ap-south-1`, `ap-northeast-2`, `ap-southeast-1`, `ap-southeast-2`,
`ap-northeast-1`, `eu-central-1`, `eu-west-1`, `eu-west-2`, `sa-east-1`,
`me-central-1`. Dynamic = mutating methods, or GET/HEAD with TTL <
**3600 s** or caching disabled.

**Fastly.** Hash default: URL + Host + generation. Freshness preference
as §2; headerless cacheable status (`200, 203, 300, 301, 302, 404, 410`)
→ TTL **2 min**; SWR/SIE **0**. UI fallback TTL when no headers and no
custom VCL: **3 600 s**; custom VCL / Fiddle boilerplate: **120 s**
(Fastly "Controlling caching" page). Hit-for-pass stored **120–3 690 s**.
`Surrogate-Key`: 1 KB / 16 KB. Purge-all ≤ **2 min**.

**Cloudflare.** Default Edge TTL 120 m / 20 m / 3 m by status (above).
Cacheable file size: **512 MB** (Free/Pro/Business), default **5 GB**
(Enterprise). Upload limits 100 / 100 / 200 MB / up to 5 GB by plan.
Request collapsing: one origin fetch per asset per datacenter. Origin
Cache Control: **on by default** for Free/Pro/Business. Cache-key
customization (per-header / per-cookie / per-query include) is
**Enterprise**; Ignore / Sort query string and device-type are on all
plans. Smart Tiered Cache + cloud region hints: all plans, changelog
**2026-04-17**.

**Akamai.** Required key parts: hostname + path; query **on** by default.
Enhanced RFC Support: `honorMaxAge`, `honorSMaxage`,
`honorMustRevalidate`, `honorProxyRevalidate`. `mustRevalidate` on the
caching behavior: if enabled, only the re-fetched object may be served
after expiry; if disabled, may serve stale when origin is down. Fast
Purge default method: **Invalidate**.

---

## 5. Failure modes and when-not-to-use

**Failure modes of the CDN itself**

- **Key explosion.** Session cookies, raw `Accept-Encoding`, signed-URL
  query params, or unbounded `?w=` produce one object per user / per
  token. Hit rate falls; origin sees "dynamic" traffic; purge cannot
  enumerate variants (CloudFront: you *cannot* invalidate by cookie or
  header value).
- **Key collision / poisoning.** Omitting a dimension the origin uses
  (`Host`, `Origin`, language). Cloudflare default includes `Origin` and
  forwarded-host headers for this reason; they warn that custom keys plus
  URL normalization without "Normalize URLs to origin" enable poisoning.
- **`s-maxage` silently disables SWR.** RFC 9111 + Cloudflare
  revalidation page. Symptom: you set both headers and still block on
  every expiry (`EXPIRED`, not `UPDATING`).
- **MinTTL overrides `no-store`.** CloudFront CachingOptimized /
  Amplify: personalized HTML cached for 1–2 s (or worse if you raise
  MinTTL). Their own warning.
- **Shield SWR / soft-purge loop (Fastly).** Shield serves stale to the
  edge; edge re-caches it as fresh for the remaining `max-age`. Documented
  mitigations: disable SWR on the shield POP (`stale_while_revalidate = 0`
  when `fastly.ff.visits_this_service == 0` is *not* the shield — see
  their stale page); rely on `Age` for ordinary expiry.
- **Shield miss after origin move.** Cloudflare: changing origin IPs /
  switching to anycast without a region hint reassigns upper-tiers and
  spikes `MISS`.
- **Purge that misses the key.** Cloudflare dashboard purge vs custom
  keys; CloudFront invalidation that omits a forwarded query; Fastly
  `vcl_hash` customized without keeping `req.vcl.generation` (purge-all
  stops working).
- **Signed URL in the key, or param added after signing.** Unique objects
  or 403. CloudFront checks expiry at *request* start; Range-retry after
  expiry fails.
- **Capacity-cache flush.** Same loop as B3/C1, now at the shield: lose
  the upper-tier and every POP refills at once. Pair with C1; do not
  "just hit the origin."
- **Caching an error.** Cloudflare default-caches 404/410 for **3 m**.
  Fastly cacheable statuses include 404/410. A bad deploy's 404 becomes
  a fleet fact until purge or TTL.
- **WebSocket / SSE through a cache behavior.** Uncacheable; you wanted
  A3/A4 + an idle timeout (CloudFront 10 min), not a cache policy.

**When not to use (a CDN cache, specifically)**

| Situation | Prefer |
|---|---|
| Per-user HTML or anything with `Set-Cookie` / `Authorization` as the body selector | Pass / CachingDisabled; dynamic acceleration only. B3 session store stays behind the origin. |
| Write-heavy POST / mutating APIs | Do not cache. C5 + origin LB. |
| Origin already a **latency cache** (SRE ch. 22, on B3): it can take full client QPS | CDN is optional complexity; use it for TLS offload / WAF if you still want the path. |
| You need *immediate* global correctness (prices, inventory, legal takedown) | Short TTL **and** Delete-class purge (Akamai Delete; Fastly hard purge); or uncacheable. Invalidate-only + IMS is not a takedown. |
| Freshness contract is "never stale, even on 503" | No SIE; C11 if you later *choose* stale as degradation. `must-revalidate` + no RFC 5861. |
| gRPC | CloudFront: Origin Shield is skipped. Not this card. |
| Small internal service, one region, no public clients | B3 next to the origin is cheaper than an edge fleet. |

---

## 6. Cross-links

| Target | Why |
|---|---|
| **B3** [b3-caching-external-research.md](b3-caching-external-research.md) | Aside/through/behind, Redis/Memcached defaults, stampede families, hit-rate × origin-QPS identity. This note starts where B3 stops (RFC 9111 / 5861 as a *related* layer). |
| **C11** | Serving stale *on purpose* as degradation / kill switch. `stale-if-error` is the HTTP knob. |
| **C1** [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md) | Cache/CDN-down fallback, half-open stampede, metastability. |
| **C5** | Origin load balancing; anycast. Cloudflare Smart Tiered Cache × Load Balancing pool = one upper-tier. |
| **A1** [a1-request-response-external-research.md](a1-request-response-external-research.md) | `Cache-Control` on the wire. |
| **A3 / A4** | WS / SSE; CloudFront WS idle 10 min. |
| **aws/ch09.md**, **aws/ch20.md** | CloudFront / Origin Shield in the existing AWS notes — link, do not rewrite. |
| **Catalog** | B8 in [system-design-patterns-catalog.md](system-design-patterns-catalog.md). |
| **Depth-bar examples** | [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md), [RetryBackoff.md](../../../cases/SystemDesignPatterns/RetryBackoff.md). |

---

## 7. Sources

Retrieved 2026-09-13.

**RFCs.** rfc-editor.org/rfc/rfc9111.html · httpwg.org/specs/rfc5861.html
(rfc-editor.org/rfc/rfc5861.html returned **409** this fetch).

**CloudFront** (docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide).
cache-key-understand-cache-policy · using-managed-cache-policies ·
Expiration · origin-shield · controlling-origin-requests ·
understanding-how-origin-request-policies-and-cache-policies-work-together
· QueryStringParameters · invalidation-specifying-objects ·
cloudfront-limits · private-content-signed-urls ·
private-content-creating-signed-url-canned-policy ·
private-content-creating-signed-url-custom-policy ·
RequestAndResponseBehaviorCustomOrigin · DownloadDistValuesOrigin ·
cloudfront/latest/APIReference/API_CachePolicyConfig ·
API_CustomOriginConfig

**Fastly** (fastly.com/documentation). reference/vcl/subroutines/hash ·
guides/full-site-delivery/caching/manipulating-the-cache-key ·
guides/concepts/cache/cache-freshness · guides/concepts/cache/stale ·
guides/full-site-delivery/caching/controlling-caching ·
reference/http/http-headers/Surrogate-Control ·
guides/concepts/shielding · guides/getting-started/hosts/shielding ·
guides/concepts/cache/purging

**Cloudflare** (developers.cloudflare.com). cache/how-to/cache-keys ·
cache/concepts/default-cache-behavior · cache/concepts/revalidation ·
cache/concepts/retention-vs-freshness · cache/how-to/cache-rules/settings
· cache/how-to/purge-cache/purge-by-single-file ·
cache/how-to/tiered-cache · smart-shield/configuration/smart-tiered-cache
· smart-shield/configuration/argo · argo-smart-routing ·
changelog/post/2026-04-17-smart-tiered-cache-for-public-cloud ·
waf/custom-rules/use-cases/configure-token-authentication ·
ruleset-engine/rules-language/functions

**Akamai** (techdocs.akamai.com). property-mgr/docs/know-caching ·
cache-id-modification · reference/latest-caching · reference/ga-caching ·
docs/return-cache-status · edge-diagnostics/docs/pragma-headers ·
purge-cache/docs/purge-methods · purge-cache/docs/welcome-purge ·
property-mgr/docs/auth-token-2-0-ver ·
adaptive-media-delivery/docs/add-token-auth

**Workspace.** cases/aws/ch09.md · cases/aws/ch20.md ·
docs/research/sysdesign/b3-caching-external-research.md ·
cases/SystemDesignPatterns/CircuitBreaker.md

---

## 8. Uncertain / left out (excluded from the Concept)

- **RFC 5861 html at rfc-editor.org** returned HTTP 409 this fetch;
  text taken from httpwg.org/specs/rfc5861.html (same RFC).
- **`s-maxage` + SWR interaction on CloudFront and Fastly** — Cloudflare
  documents the RFC 9111 conflict explicitly. CloudFront's SWR page
  shows examples with `max-age`, not `s-maxage`. Fastly parses both
  `s-maxage` (as TTL) and `stale-while-revalidate` (as a separate
  window) and does **not** repeat Cloudflare's "SWR off when s-maxage
  present" sentence. Do not claim a single vendor-universal rule;
  test the POP.
- **Akamai `stale-while-revalidate` as a first-class Property Manager
  option.** Enhanced RFC Support lists max-age / s-maxage /
  must-revalidate / proxy-revalidate. SWR/SIE are **not** named on the
  fetched `latest-caching` / `ga-caching` pages. Secondary articles
  claim Akamai honors RFC 5861; **not asserted**.
- **Fastly UI 3 600 s vs readthrough 2 min vs custom-VCL 120 s.** All
  three appear on official pages for slightly different "no header"
  cases. Concept should say "set an explicit TTL" rather than pick one
  implicit default.
- **Fastly bulk surrogate-key batch size (256)** appeared only in a
  search snippet, not in the fetched purging page. Not asserted.
- **CloudFront "first 1 000 invalidation paths free per month"** is
  pricing, not fetched from the quotas page. Out of scope.
- **CloudFront HTTP/3 "up to 10% latency" blog claim** — marketing, not
  a default. Not used.
- **CloudFront Server-Timing `cdn-upstream-connect`** described on the
  Networking blog and implied by the Developer Guide's persistent-
  connection text; the exact enablement default (off vs on) was not
  pinned on a fetched Developer Guide page.
- **Akamai Site Shield map counts / IP-allowlist refresh interval** —
  not fetched. Site Shield is cited only as parent-cache + origin-IP
  hiding.
- **Cloudflare purge rate limits per plan** — the purge API schema was
  fetched; numeric rate quotas were not on the pages used. Not asserted.
- **Google Cloud CDN / Azure Front Door / Nginx/Varnish-as-CDN** —
  out of the four-vendor fetch list.
- **Image product defaults** (CloudFront image optimization TTLs,
  Cloudflare Image Resizing, Akamai Image Manager, Fastly IO) — placement
  only; no product bake-off.
- **OpenTelemetry CDN semantic conventions** — none found.
- **PromQL alert recipes** — none found; §3.9 shapes are this note's.
- **Nygard Dogpile / SRE cache-warming** — already on C1 / B3; not
  re-derived.
- **Netflix Open Connect / embedded PoP storage (128 TB, 70 Gbps)** in
  aws/ch20.md — book figures, not re-verified this pass.
