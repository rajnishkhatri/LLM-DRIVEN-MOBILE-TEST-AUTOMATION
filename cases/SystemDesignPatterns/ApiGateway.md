---
type: reference
title: 'API gateway and backend-for-frontend'
description: >-
  North-south edge façade for routing, offloading, and optional aggregation —
  one gateway vs BFF vs mesh ingress — with C4/C7/C1 placed at the edge vs
  in-mesh, aggregation pitfalls, and verified AWS/Kong/Apigee/Envoy Gateway
  /Spring Cloud Gateway defaults. Business logic never lives in the gateway;
  B4 owns strangler cutover; C5 owns host selection; A6 owns version contracts.
tags: [system-design-patterns, api-gateway, bff, edge]
---

# API gateway and backend-for-frontend

**See also:** [rate limiting](RateLimiting.md) · [timeouts](TimeoutsDeadlines.md) · [circuit breaker](CircuitBreaker.md) · [load balancing](LoadBalancing.md) · [API contracts and versioning](ApiVersioning.md) · [retry, backoff, and retry budgets](RetryBackoff.md) · [cloud patterns: gateway, mesh, BFF, strangler](../aws/ch08.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/c6-api-gateway-external-research.md)

An API gateway is a **north–south edge façade**: a reverse proxy with API-management semantics — TLS, authn, routing, optional aggregation, protocol translation, and the cross-cutting offloads Azure names (certs, throttling, a logging floor) — so clients and services do not each reimplement them. A **BFF** is the same hop, one per user experience, owned by the UI team. A **service mesh** applies per-request controls **east–west**; a [load balancer](LoadBalancing.md) only spreads. Quality attributes: **security** (one enforced front door), **client simplicity** (fewer round trips, per-client shaping), **evolvability** (backends re-partition behind a stable URL). Costs: one more highly available hop, a bottleneck-and-SPOF candidate, and a standing temptation to put business logic where it does not belong.

```
client ──TLS──► gateway (authn/z · route · optional aggregate · translate)
                    │
                    ├── C4 admit / 429
                    ├── C7 outer / remaining
                    └── C1 concurrency or failure-trip (product-dependent)
                         │
                         ▼
              backends / mesh (C7 per-try · C2 retry · C1 outlier)
```

## Lineage and vocabulary

- **Richardson (microservices.io)**: clients otherwise call many fine-grained APIs per user action. Variants: one gateway (proxy or fan-out, optional per-client adapters) vs **one BFF per client kind**. Benefits: hide partitioning and discovery; fewer round trips; protocol translation. Cost: another HA component; an extra hop (called typically insignificant). Related: Access Token, Circuit Breaker, API Composition.
- **Azure Architecture Center splits the pattern in three.** *Gateway Routing* — one endpoint, L7 rules, blue-green by config change; lock down direct backend access; not for one-or-two-service apps. *Gateway Aggregation* — one client call fans out and combines; design the partial-failure answer explicitly; put heavyweight composition in a **dedicated service behind the gateway**. *Gateway Offloading* — certs, TLS, authn, throttling at the edge, with the absolute rule: **"Business logic should never be offloaded to the gateway."**
- **Newman (2015, from SoundCloud / Calçado)**: **one BFF per user experience**, owned by the team that owns the UI; tolerate duplication until ~3 occurrences, then extract a *domain service*, not a shared library; BFFs fan out in parallel and degrade (wishlist without stock). A general-purpose API for many UIs becomes a bloated bottleneck owned by nobody.
- **ThoughtWorks Radar** put "overambitious API gateways" on **Hold** (2015–2018): orchestration, transformation and rules in transport middleware create a single point of scaling and control that product teams cannot test or deploy.
- **[aws/ch08.md](../aws/ch08.md)** (workspace; do not rewrite): gateway = unified client interface, routing + composition + protocol translation + centralized access control; mesh = east-west sidecars, mTLS, discovery; BFF = per-client backends to cut over/under-fetch; strangler fig + ACL sit one section later — **B4** owns the cutover; this card only supplies the façade.

## Façade vs BFF vs mesh ingress

The same hop can be owned three ways. That is a topology decision, not a different pattern.

| Topology | Who owns it | Traffic | Trade-off |
|---|---|---|---|
| **One gateway** | Platform | All north–south | Cheap consistency (TLS, JWT, [C4](RateLimiting.md)). Becomes Newman's nobody-owned blob as client kinds grow. Uber 2021 is this extreme: one self-built gateway, ~500K QPS, 1,500+ APIs, generated per-endpoint stacks. |
| **BFF per experience** | UI team | That client's north–south | Right-shaped payloads; duplicated gatekeeping. SoundCloud 2021: **dozens** of BFFs at hundreds of millions of req/h, then a Value-Added Services layer *behind* them. |
| **Mesh ingress** (Envoy Gateway / Istio Gateway / Gateway API) | Platform + service owners via `HTTPRoute` | North–south into the cluster | Same Envoy knobs as the sidecar, **without** claiming east–west. GAMMA Service-as-parent is mesh, not this card. Kubernetes **Ingress is frozen**; Gateway API is the successor (v1.0 GA 2023-10; v1.5 Standard 2026-02). |
| **Gateway + mesh** | Split | NS at gateway, EW in mesh | Usual production: C4 / JWT / WAF at the edge; C7 remaining-time + C1 outlier + C2 retry **in-mesh or in-process**. |
| **Strangler façade** | Migration | Same URL, path or weight flip | The gateway is the usual physical seam. Incremental cutover, shadow, dual-write, rollback, and ACL field-mapping belong to **B4** (Concept pending; see [ch08](../aws/ch08.md)). Do not put the anticorruption layer in the gateway. |

A single thin façade in front of per-experience BFFs is a legal combination: the façade holds the public URL and edge policy; each BFF owns payload shape. Header or URI version match at that façade is [contract selection](ApiVersioning.md), not a gateway pattern. Weighted host selection among healthy backends is [load balancing](LoadBalancing.md).

## What the hop is for (and is not)

| Offload | Why at the edge | Why *not* only at the edge |
|---|---|---|
| **TLS terminate** | One cert plane; backends stay private. | Mesh still needs **mTLS** east–west. Passthrough if the app owns client-cert identity. |
| **Authn** | JWT / API-key / Lambda authorizer once. AWS HTTP JWT: `jwks_uri` (RSA), `kid`/`iss`/`aud`/`exp`/`nbf`/`iat`, scopes; JWKS timeout **1 500 ms**; keys cached ≤ 2 h. | **BOLA / object authz** is per-resource (OWASP API1). The gateway cannot know who may touch order 4711; SoundCloud's scattered-authorization drift is the cautionary tale. |
| **Routing** | Host / path / header. Canary `%` is a *proxy* canary, not an extract (**B4**). | Version headers are **A6**. Host pick among healthy replicas is **C5**. |
| **Aggregation** | Hide chatty mobile/WAN. | Azure: different CPU/IO profile than routing; domain-heavy composition *behind* the gateway. |
| **Protocol translation** | grpc-gateway / Envoy `grpc_json_transcoder`. APIM `forward-request http-version="2or1"` (v2 **downgrades inbound HTTP/2 → HTTP/1** before the backend). | Wire semantics stay [A1](RequestResponse.md) / [C7](TimeoutsDeadlines.md). |
| **Resource limits** | Rate limits, size caps, pagination caps (OWASP API4). | Per-tenant *business* quotas stay in services. |

Every extra offload makes the gateway the scaling and blast-radius unit Azure and the Radar warn about. Thin façade, specialist policy, domain work in a service.

## Where C4, C7 and C1 sit

The gateway is a *placement* for sibling controls, not a second copy of their algorithms. Stacking the same control at edge and sidecar without a shared budget is how amplification starts.

| Control | At the **gateway** | **In-mesh / in-process** | Do not |
|---|---|---|---|
| **[C4](RateLimiting.md) rate limit** | Per API key / JWT / IP / usage plan. AWS: usage plan → stage method → **account 10 000 RPS / 5 000 burst** (14 newer Regions **2 500 / 1 250**; RPS adjustable, burst **not**). Kong `limit_by` default **consumer**. | Per-service / per-tenant fairness the edge cannot see. | Double-count the same token bucket at edge *and* sidecar. Fail-open defaults (Envoy `failure_mode_deny` false, Kong `fault_tolerant` true) vanish under store failure. |
| **[C7](TimeoutsDeadlines.md) timeout** | **Outer** user-facing bound + remaining-time stamp if the product can (`x-envoy-expected-rq-timeout-ms`). | **Per-try** + connect, excluding TLS from a tight request timer. | Copy a 29 s / 60 s / 300 s product default as if it were an SLO. Idle ≠ request (Kong `read_timeout` is *between successive reads*). |
| **[C1](CircuitBreaker.md) breaker** | Gateway-scoped: APIM backend breaker; Kong **passive** (trip only); Envoy Gateway **concurrency** 1024 (not a failure detector — same confusion as Envoy "circuit breaking"); Spring Cloud Gateway wraps Resilience4j. | Host **outlier detection** / library breaker per dependency. | One gateway breaker over many shards (Azure *resource differentiation*). Retry an **Open** circuit. |
| **[C2](RetryBackoff.md) retry** | Only if the product actually retries, and only for **idempotent** methods, **one layer**. AWS API Gateway **does not retry** integration timeouts — "clients must implement their own retries." | Preferred: the hop *just above* the failing service, under a budget. | Stack gateway retries + mesh retries + SDK retries (SRE / Brooker 243×). |

Two coherent designs for the timeout+retry inequality (`client deadline > gateway outer > max(branches) [or Σ if sequential] > per-try`):

| Design | Outer (gateway) | Inner | Retry |
|---|---|---|---|
| **Envoy / Envoy Gateway** | `timeouts.request` (Envoy default **15 s** if unset) | `timeouts.backendRequest` ≤ request; EG `perRetry.timeout` | EG `numRetries` default **2** *when* a retry policy exists. HTTPRoute Retries (GEP-1731) beat `BackendTrafficPolicy` from EG **v1.3**. Unconfigured: `/status/500` returns **immediately**. |
| **.NET-style** | Total 30 s | Attempt 10 s | Retry *inside* total, *outside* attempt. |

A 504 on the *outer* is not retried by Envoy unless `per_try_timeout` fired. AWS integration timeout **50 ms–29 s** (REL05-BP05) is a *placement* fact: the managed edge is the outer bound; retry lives downstream or in the client, not both.

## Aggregation pitfalls

Aggregation is where gateways fail in production. Azure (Learn page, 2026-06-02): one client request → N backends in **parallel async I/O**; **partial vs fail-all** is a product decision encoded in the aggregator; correlation IDs across branches; monitor **response size**; cache-as-failover is allowed; coupling backends through the gateway is not; if composition is domain-heavy, **move it behind**.

**Chatty-fan-out failure.** A BFF or GraphQL router that walks an entity graph issues *O(fields × depth)* RPCs. SoundCloud: client logic migrated in ("extensions of the client") until recursive pagination caused BFF timeouts — the fix was a **Value-Added Services layer** behind the BFFs owning aggregates and authorization, shrinking BFFs back to formatting. Apollo Federation's router is supposed to plan *only needed* subgraphs; **demand control** (mutation base cost **10**, object **1**, `max` example **1000**) is the cap; persisted-query *safelisting* is a security control (automatic persisted queries are a latency cache with **no security value**). Apigee API-product GraphQL operations cap: **50** (enforced). None of these replace a per-branch **C7** timeout.

Envoy's per-try timeout defaults to the whole route timeout, so one slow branch eats the budget. APIM `send-request` is the documented shape: per-request timeouts, conditional errors, circuit breakers.

## Platform defaults (verified 2026-09-13)

Product defaults are **not** SLOs. Unset, they pin workers for tens of seconds on a 200 ms p99 hop.

| Product | Unset timeout | Unset retry | Effect on a 200 ms p99 payment |
|---|---|---|---|
| **AWS REST** | **29 s** (50 ms floor; Regional/private raisable since 2024-06, LLM-motivated, may cut account RPS; edge-optimized **not**). Payload **10 MB**, not increasable. Cache TTL default **300 s**. Idle connection **310 s**. | **None** | Pins a gateway execution + backend thread 29 s. Client *must* retry 504s. |
| **AWS HTTP** | **30 s**, **not** increasable | **None** | Same, plus no REST canary / WAF / cache. Built-in JWT; JWKS **1 500 ms**. |
| **Kong Service** | connect/read/write **60 000 ms** (idle-between-I/O). Connect fail → **502**; read/write idle → **504**. | **5** transport retries (0–32 767). **5xx and 429 are not retried.** POST after the upstream received the body is not retried unless `proxy_next_upstream non_idempotent`. | 60 s stall; GET retried 5× on connect/timeout. |
| **Apigee** | `connect.timeout.millis` **3 000**; `io.timeout.millis` **55 000**; `api.timeout` unset → Ingress **300 s**; `keepalive.timeout.millis` **60 000**. Buffered payload **30 MB** enforced. | Connect may be retried **up to three times** | 55 s read stall; 300 s if you never set `api.timeout`. Limits-row "Target connection timeout **300 s**" is **Planned** enforcement. |
| **Azure APIM** | `forward-request timeout` **300 s** — waits for **response headers**; values **> 240 s** "may not be honored" | **No** retry unless you add `<retry>` (`buffer-request-body` must be **true**) | 5-minute header wait. A trickling SSE/body can outlive `timeout` while `buffer-response` default **true** chunks 8 KB — set `buffer-response="false"` for SSE. |
| **Spring Cloud Gateway** | `httpclient.connect-timeout` **30 s**; `response-timeout` **unset** | Retry filter *if enabled*: **3**, **5XX**, **GET** only, backoff **off**, timeout **unlimited**. Retries **all filters after it**. | Connect bounded; body can run forever. Enabling Retry on POST caches the body. CircuitBreaker filter needs Resilience4j (failure-rate **50%**, TimeLimiter **1 s**). |
| **Envoy Gateway** | Envoy route **15 s** (`0s` disables; Gateway API says implementation-specific) | none until HTTPRoute / BTP; then `numRetries` **2** | Closest to a sane outer. Concurrency breaker **1024** / **1024** / **1024** per `BackendReference` — overflow is **503**, not a Fowler trip. Not synced across Envoy processes. |

AWS account throttle is a *shared* backstop across all APIs in the Region. REST-only capabilities: API keys + usage plans, WAF, caching, canary, body transformation, X-Ray, edge-optimized + private endpoints. HTTP-only: built-in JWT authorizers, automatic deployments, Cloud Map. REST canary (`percentTraffic` 0–100) versions the *proxy*. Direct REST → internal ALB since 2025-11. ALB is not a gateway: rich routing and health checks, rate limiting only via WAF.

Kong plugins run per phase (certificate, rewrite, access, response, header/body_filter, log) by **static priority, highest first**; scope precedence across 12 levels. Request-size limiting is **off** until the plugin is added (`nginx_http_client_max_body_size = 0`; plugin default 128 MB). Passive health checks (not retries) mark targets unhealthy via `healthchecks.passive.unhealthy.http_statuses` — see the [breaker's gateway row](CircuitBreaker.md).

## Observability

Emit at least:

| Signal | What it tells you |
|---|---|
| Gateway **class** of 504 (integration / io / connect / stream-idle) | AWS 504 ≠ Kong idle-read 504 ≠ APIM header-wait 504. |
| Per-backend latency + error, tagged `route` / `integration` | Aggregation hides which branch died. |
| Remaining deadline at ingress vs at each backend | Copied 29 s vs remaining ([C7](TimeoutsDeadlines.md)). |
| Retry count **by hop** | Catch stacked retries (`envoy_cluster_upstream_rq_retry`; Kong `X-Kong-Upstream-Latency`). |
| Authn fail vs backend fail | 401/403 must **not** trip C1. |
| Rate-limit 429 vs backend 429 | Edge quota vs provider quota. |
| Partial-aggregation rate | How often users got the degraded aggregate — Azure's "design it explicitly." |
| Config-change audit | The gateway is a single point of control; canary the gateway itself. |

Kong `X-Kong-Proxy-Latency` / `X-Kong-Upstream-Latency` are computed in `header_filter` — **before** a slow body finishes. Prefer a metrics plugin for the full cycle. Correlation IDs are minted or propagated at the edge (Azure lists this under both routing and offloading).

## Tuning

| Knob | Too tight / off | Too loose / on | Starting point |
|---|---|---|---|
| Gateway **outer** timeout | False 504s; truncates inner retries | APIM 300 s / Kong 60 s / AWS 29 s pins workers | Brooker percentile of *this* hop + pad; must be **<** any idle LB in front (ALB **60 s**) |
| `backendRequest` / per-try | Healthy tail looks down | Outer never fires first | < outer; cover one attempt only |
| Gateway retries | 0 on a fleet of flaky connects | Kong **5** × mesh **2** × SDK **2** | **0** at AWS; **0** on POST; at most **1** layer |
| Edge C4 | UX 429s on launch | Account 10 k RPS is the only backstop | Usage-plan per client; keep account headroom |
| EG / Envoy concurrency 1024 | 503s under legitimate fan-out | Never overflow; slow backend holds 1024 | Set `maxParallelRequests` to what the *callee* can do |
| Aggregation placement | Partial data surprises | Sequential N× latency; gateway becomes the monolith | Parallel + explicit partial; composition with domain meaning → service behind the gateway |
| BFF count | One general-purpose backend = bottleneck nobody owns | BFF sprawl = duplicated authz drift | One per experience, owned by that UI team |

Write the remaining-time inequality first ([C7](TimeoutsDeadlines.md)), then pick the product whose *default* is closest and **override it**. Put C4 at the edge (identity you already terminated). Put C2 **one** hop above the failure. Put failure-trip C1 on the *dependency*, concurrency C1 on the *proxy*. Revisit when the histogram walks; a gateway timeout that never fires is the APIM-300 / AWS-29 trap.

## Testing and operating

A gateway is an operational mode that is easy to configure and hard to rehearse: the first time a 29 s default, a stacked retry, or a BFF fan-out meets production traffic is the worst time.

- **Override every product default in staging and prove it.** Hit a 200 ms backend through AWS REST, Kong, EG, Apigee, APIM and SCG with the *unset* timeout and with the calibrated one; the proof is the 504 class and the worker-hold time, not a dashboard that says "healthy."
- **Fault-inject a slow branch.** Toxiproxy latency / Istio `fault.delay` on one of N backends; assert the aggregator returns the documented partial (or fails all) *and* that siblings still finish inside the outer. Envoy Gateway's own retry task is the object lesson: unconfigured, `/status/500` returns immediately — a policy you thought was on is not.
- **Kill the edge retry.** AWS has none to kill. Kong `retries 0` on the capture Service; EG omit BTP / HTTPRoute retries on POST; SCG do not attach Retry. Practice the client-504 path and the checkout-service retry path separately.
- **Force-open a backend breaker** (APIM / Resilience4j / Kong passive) and confirm the BFF degrades the optional rail rather than 504ing the screen.
- **Canary the gateway config itself.** A usage-plan, timeout, or route change is a fleet-wide blast radius; treat it like a service deploy. Strangler weight flips are **B4** — do not canary *all* URLs because the gateway can.

## Worked calibration — checkout → payment (timeout + retry at the gateway vs down)

Constraints are a **design drill**, not a vendor SLA. Same histogram as the [C7](TimeoutsDeadlines.md) checkout: p50 **80 ms**, p99.9 **420 ms** on `POST /capture`. User-facing budget **3 s**. Per-attempt **500 ms**. C2 policy (cited, not redesigned): 2 retries, full jitter, 200 ms base → worst-case sleeps ≈ 600 ms. `3.0 ≥ 3×0.5 + 0.6` → **2.1 s** used, **0.9 s** slack.

| Layer | Choice | Why |
|---|---|---|
| **Client** | One retry on **504/503** only, budget 1, honour `Retry-After` | AWS: *clients* retry. Do not also retry 400s. |
| **Edge gateway** | AWS REST integration timeout **2.5 s** (inside 3 s, above 2.1 s). **Retries = 0**. C4: usage-plan ~ checkout RPS × 1.2. JWT/API-key here. | Outer bound. 29 s default would pin the 99.9% path. Canary of the *proxy* is **B4**, not this SLO. |
| If the edge is **Kong** | `connect_timeout` **5 000**; `read_timeout` **2 500**; `retries` **0** on the capture Service | Default 60 s / 5 retries is a Brooker 243× starter kit. Kong will not retry that POST after the body was received (good) but *will* retry GET status 5×. |
| If the edge is **Envoy Gateway** | `timeouts.request: 2.5s`, `backendRequest: 500ms`; **no** BTP retry on `POST /capture`; concurrency sized to the payment pool | 15 s default is closer than 29/60/300 but still 5× the budget. |
| If the edge is **Apigee** | `api.timeout` **2500**; `io.timeout.millis` **500** on the payment TargetEndpoint; leave `connect.timeout.millis` **3000** (connect ≠ request) | Unset `api.timeout` = **300 s** Ingress. |
| If the edge is **APIM** | `<forward-request timeout="3"/>` **and** a backend breaker per payment shard; **no** `<retry>` around capture | Default **300 s** header wait. |
| If the edge is **SCG** | `connect-timeout` 1000; `response-timeout` **2.5s**; **do not** attach Retry to POST; CircuitBreaker name per issuer, TimeLimiter **500 ms** not 1 s | Align the TimeLimiter with the attempt, not the library default. |
| **Checkout service** | Remaining ~2.4 s after 50–80 ms gateway+auth. Retry **here** (idempotency key), breaker per payment authority | One retry layer, just above the rejector (SRE). |
| **Payment** | Per-attempt 500 ms; outgoing to issuer capped **1.0 s** | Do not inherit 2.4 s onto issuer threads. |
| **Hedging** | **Off** on capture | Side effect. Status GET may hedge at p95. |

If checkout is a **BFF** that also fetches cart + recommendations: those branches get their **own** 400–800 ms budgets and a documented partial (Azure). Do not hang the capture path on the wishlist. Token validated at the gateway; **object checks in each service**. BFF formats; any cross-entity logic goes to a composition service (SoundCloud's correction, pre-applied).

## Failure modes

- **Product default as SLO.** AWS 29 s, HTTP 30 s, Kong 60 s, Apigee 55 s / 300 s, APIM 300 s, SCG response unset, EG 15 s. The unnamed min on the path still wins (CloudFront / ALB idle).
- **Stacked retries.** Kong 5 + EG 2 + SDK 2 on GET; SCG Retry retries *downstream filters*. See [retry amplification](RetryBackoff.md).
- **Gateway retries a POST.** SCG will if you enable Retry and add POST; Kong will only on pre-receive connect fail — unless someone set `non_idempotent`. Double capture without [idempotency](Idempotency.md).
- **AWS 504, client retries, payment succeeded.** Integration timeout does not cancel work the way gRPC `CANCELLED` does. The idempotency key is required.
- **Chatty aggregation / GraphQL N+1.** SoundCloud pagination; Azure SPoF/bottleneck; Apollo cost cap bypassed if `enforce` is off.
- **Business logic in the façade.** Radar Hold; Azure offloading; B4 ACL-in-gateway.
- **BFF sprawl and drift.** Authz implementations disagree — a correctness *and* security failure (SoundCloud). Newman's unowned general API is the other pole.
- **One C1 over many backends.** Azure resource differentiation; EG counters are per `BackendReference` (good) but one APIM backend pool is not.
- **Concurrency limit mistaken for a breaker.** EG/Envoy 1024 never "trips Open"; it 503s. See the [breaker's two-mechanism warning](CircuitBreaker.md).
- **C4 only at the account cap.** 10 k RPS shared across *all* APIs; one noisy neighbor.
- **Raising AWS REST > 29 s.** LLM-shaped; eats Region throttle; HTTP APIs and edge-optimized cannot follow.
- **JWKS 1.5 s / Lambda authorizer 10 s** folded into a 500 ms attempt.
- **Idle used as request timeout.** Kong `read_timeout`, Apigee `io.timeout.millis` (no *data*), AWS idle connection **310 s**.
- **SPOF / bottleneck.** Under-provisioned gateway melts first under load it was supposed to police — load-test it like a service.

**When a gateway is the wrong tool.** One or two services (Azure routing). Client already next to backends (Azure aggregation). You need object-level authz only the service can do. You were about to put orchestration in the proxy (Radar; put a service behind). Greenfield with no edge policy need — start with a mesh ingress *or* nothing, not APIM-300.

**When a *single* gateway is wrong.** Multiple UX surfaces with different payload/auth shapes (Newman BFF), *or* a strangler that needs path extract (**B4**) plus a stable public URL (keep one thin façade, BFFs behind it).

**When a BFF is wrong.** One team cannot own it; duplication has already been extracted three times (Newman → domain service); the BFF is paginating a foundation API (SoundCloud).

## Trade-offs

| Buy | Pay |
|---|---|
| One enforced front door for TLS, JWT, C4, WAF | One more HA component, hop, and config blast radius |
| Clients decoupled from service partitioning | The edge team becomes a dependency for every API change |
| Per-client shaping (BFF) | Per-client backends to own and keep from drifting |
| Central canary / strangler seam | Cutover mechanics are **B4**; ACL-in-gateway is the Radar failure |
| Platform reuse (AWS / Kong / EG / APIM / SCG) | Defaults will pin workers; tuning is ongoing operations |

The gateway owns the **edge**. Per-object authorization and domain composition stay behind it. [C4](RateLimiting.md) decides **whether to admit**. [C7](TimeoutsDeadlines.md) decides **how long the outer hop may run**. [C1](CircuitBreaker.md) decides **whether to call a sick backend**. [C2](RetryBackoff.md) decides **whether to try again** — at one layer, not this one if AWS already bound the integration. Coordinate all four; do not treat the gateway as a complete resilience strategy.

## Sources

Verified 2026-09-13; full URLs, per-claim provenance, and items deliberately left out are in the [catalog research note](../../docs/research/sysdesign/c6-api-gateway-external-research.md). First-pass GraphQL / Gateway API / JWT / SoundCloud-Uber tables it links: [api-gateway-external-research.md](../../docs/research/sysdesign/api-gateway-external-research.md). Workspace one-liners: [aws/ch08.md](../aws/ch08.md). Sibling facts cited forward, not re-derived: [breaker](CircuitBreaker.md), [retry](RetryBackoff.md), [timeouts](TimeoutsDeadlines.md), [rate limiting](RateLimiting.md), [load balancing](LoadBalancing.md), [versioning](ApiVersioning.md).

- Canon: Richardson microservices.io API-gateway/BFF; Newman, *BFF* (2015-11-18); Azure gateway routing / aggregation (2026-06-02) / offloading; ThoughtWorks Radar blip (Hold, 2015–2018).
- Platforms: AWS API Gateway quotas + REL05-BP05 + 2024-06 timeout announcement + REST-vs-HTTP + 2025-11 REST↔ALB; Kong Service schema + proxying (60 s / 5 retries / no 5xx); Apigee endpoint properties + limits (updated 2026-09-11); Envoy Gateway HTTP timeouts (v1.9.1), retry (`numRetries` 2), circuit breakers (1024); Gateway API GEP-1731; Spring Cloud Gateway timeouts / Retry / CircuitBreaker / configprops; Azure APIM `forward-request` (300 s header wait) + retry policy.
- Lessons: SoundCloud service-architecture parts 1–2 (2021); Uber gateway architecture (2021); OWASP API Security Top 10 (2023); Apollo Federation, persisted queries, demand control.
