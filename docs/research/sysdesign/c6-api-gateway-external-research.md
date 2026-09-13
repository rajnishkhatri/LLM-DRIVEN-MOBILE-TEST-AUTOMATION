---
type: research
title: 'API gateway patterns — external research (2026-09-13)'
description: >-
  Group C catalog evidence pass for C6: gateway as edge façade, BFF vs single
  gateway vs mesh ingress, GraphQL/BFF fan-out, placement of C4/C7/C1, and
  verified AWS / Kong / Apigee / Envoy Gateway / Spring Cloud Gateway knobs
  — with a timeout+retry calibration at the gateway vs downstream.
tags: [research, system-design-patterns, C6, api-gateway, bff]
---

# C6 API gateway patterns (+ BFF) — catalog research (2026-09-13)

> **What this is.** The catalog evidence pass for **C6**. It **links** the same-day first pass [api-gateway-external-research.md](api-gateway-external-research.md) (Richardson/Newman/Azure canon, Gateway API through v1.5, ThoughtWorks Hold, SoundCloud/Uber, JWT/transcoding/canary/WAF, Apollo demand control) and **deepens** it to the Group C / [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md) bar: mechanics and variants, knobs with verified defaults, observability, tuning, a worked timeout+retry calibration, failure modes, sources.
>
> **Method.** Primary pages fetched 2026-09-13. Numbers and option names reproduced exactly; everything else paraphrased. Facts marked **[→C6-1]** are in the first-pass note and not re-fetched here. Facts marked **[→C7]** / **[→breaker]** / **[→retry]** / **[→C4]** / **[→B4]** live in those sibling notes. Unverifiable items are in §10 and are **not** asserted as fact.

---

## 1. Scope and non-goals

**Owns.** The gateway as a **north-south edge façade**: TLS termination, authn/z, routing, aggregation, protocol translation, and the cross-cutting offloads Azure names (certs, throttling, a logging floor). Topology choice: **one gateway vs BFF vs mesh ingress**. GraphQL / BFF **chatty fan-out**. Where **C4 / C7 / C1** belong at the edge versus in-mesh. Verified knobs on AWS API Gateway, Kong, Apigee, Envoy Gateway, Spring Cloud Gateway (plus Azure APIM where it is the only documented *header-wait* default). Worked calibration: timeout and retry at the gateway versus one hop down.

**Does not own.** Load-balancing *algorithms* (**C5**). Incremental strangler cutover, shadow, dual-write, rollback of the façade (**B4** — this note only names the gateway as the usual physical seam). Sidecar lifecycle and east-west data-plane (**B6**). Contract / schema versioning (**A6**). REST vs gRPC *wire* semantics (**A1**). Jitter / retry-budget math (**C2** — do not rewrite). What errors trip a breaker (**C1**). Deadline kinds and Brooker percentile method (**C7** — this note only *places* the bound). Rate-limit *algorithms* and header drafts (**C4**).

**Does not re-derive.** [aws/ch08.md](../../../cases/aws/ch08.md) one-paragraph API gateway / service mesh / BFF / strangler-fig. First-pass GraphQL federation / persisted-query / demand-control tables **[→C6-1]**.

---

## 2. Lineage / vocabulary

| Term | Meaning | Named source |
|---|---|---|
| **API gateway** | Single north-south entry applying API-management semantics (authn/z, routing, composition, protocol translation, policy). | Richardson microservices.io; [aws/ch08.md](../../../cases/aws/ch08.md) *API routing*; CNCF glossary **[→C6-1]** |
| **BFF** | One backend *per user experience*, owned by the UI team. | Newman 2015-11-18 (term from Calçado / SoundCloud); [aws/ch08.md](../../../cases/aws/ch08.md) *Backend for frontend* |
| **Offloading** | Move *whole-app* cross-cuts (TLS, authn, throttling, WAF) to the edge. **“Business logic should never be offloaded to the gateway.”** | Azure *Gateway Offloading* (upd. 2025-12-09) **[→C6-1]** |
| **Aggregation** | One client call → N backend calls, combined. Different resource profile than routing. | Azure *Gateway Aggregation* (ms.date **2026-06-02**) |
| **Mesh ingress** | Gateway API `Gateway` + `HTTPRoute` as the cluster edge; east-west is a Route with a **Service** `parentRef` (GAMMA). | Gateway API v1.1+ **[→C6-1]**; [aws/ch08.md](../../../cases/aws/ch08.md) mesh vs gateway |
| **Strangler façade** | The *use* of a gateway as the incremental-cutover seam. | Fowler; Azure / AWS PG; **[→B4]** |

**Richardson, *API Gateway / BFF*** (microservices.io, © 2026) **[→C6-1]**. Clients otherwise call many fine-grained APIs per user action. Variants: one gateway (proxy or fan-out, optional per-client adapters) vs one BFF per client kind. Benefits: hide partitioning/discovery; fewer round trips; protocol translation. Cost: another HA component; extra hop (called typically insignificant). Related: Access Token, Circuit Breaker, API Composition.

**Newman, BFF** (2015-11-18) **[→C6-1]**. One BFF per *experience* (SoundCloud’s single iOS+Android BFF is accepted because one team owns both). UI team owns the BFF. Duplicate until ~3 occurrences, then extract a *domain service* (not a shared library). Fan-out in parallel; degrade (wishlist without stock). A general-purpose API for many UIs becomes a bloated bottleneck owned by nobody.

**Azure three pages** **[→C6-1]**. *Routing*: L7 rules, SPoF/bottleneck, lock down direct backend access; not for one-or-two-service apps. *Aggregation*: no cross-backend coupling; place near backends; bulkheads / breakers / retries / timeouts *inside* the aggregator; a slow branch may return **partial data** — design it; consider a **dedicated aggregation service behind** the gateway. *Offloading*: never business logic.

**ThoughtWorks Radar, “Overambitious API gateways”** (Hold, 2015–2018) **[→C6-1]**. Domain orchestration in transport middleware.

**[aws/ch08.md](../../../cases/aws/ch08.md)** (workspace; do not rewrite). Gateway = unified client interface, routing + composition + protocol translation + centralized access control. Mesh = east-west sidecars, mTLS, discovery. BFF = per-client backends to cut over/under-fetch. Strangler fig + ACL sit one section later — **B4** owns the cutover; this note only supplies the façade.

---

## 3. Mechanics

### 3.1 Edge façade (what the hop is for)

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

| Offload | Why at the edge | Why *not* only at the edge |
|---|---|---|
| **TLS terminate** | One cert plane; backends stay private. | Mesh still needs **mTLS** east-west (**B6**). Passthrough if the app owns client-cert identity. |
| **Authn** | JWT / API-key / Lambda authorizer once. AWS HTTP JWT: `jwks_uri` (RSA), `kid`/`iss`/`aud`/`exp`/`nbf`/`iat`, scopes; JWKS timeout **1 500 ms** **[→C6-1]**. | **BOLA / object authz** is per-resource (OWASP API1) — SoundCloud’s scattered-auth lesson **[→C6-1]**. |
| **Routing** | Host / path / header (ch08). Canary % is a *proxy* canary, not an extract (**B4**). | Header versioning is **A6**. Weighted LB among healthy hosts is **C5**. |
| **Aggregation** | Hide chatty mobile/WAN. | Azure: different CPU/IO profile than routing; put heavy composition *behind* the gateway. |
| **Protocol translation** | grpc-gateway / Envoy `grpc_json_transcoder` **[→C6-1]**. APIM `forward-request http-version="2or1"` (self-hosted + v2 preview; v2 **downgrades inbound HTTP/2 → HTTP/1** before the backend). | Wire semantics (deadlines, streaming, status mapping) stay **A1** / **C7**. |

Trade-off: every extra offload makes the gateway the scaling and blast-radius unit Azure and the Radar warn about. Thin façade, specialist policy, domain work in a service.

### 3.2 Single gateway vs BFF vs mesh ingress

| Topology | Who owns it | Traffic | Trade-off |
|---|---|---|---|
| **One gateway** | Platform | All north-south | Cheap consistency (auth, TLS, C4). Becomes Newman’s nobody-owned blob as client kinds grow. |
| **BFF per experience** | UI team | That client’s north-south | Right-shaped payloads; duplicated gatekeeping. SoundCloud 2021: **dozens** of BFFs at hundreds of millions of req/h, then a Value-Added Services layer *behind* them **[→C6-1]**. |
| **Mesh ingress** (Envoy Gateway / Istio Gateway / Gateway API) | Platform + service owners via `HTTPRoute` | North-south into the cluster | Same Envoy knobs as the sidecar, **without** claiming east-west. GAMMA Service-as-parent is mesh, not this card. |
| **Gateway + mesh** | Split | NS at gateway, EW in mesh | Usual production: C4/JWT/WAF at the edge; C7 remaining-time + C1 outlier + C2 retry **in-mesh or in-process**. |
| **Strangler façade** | Migration | Same URL, path/weight flip | **[→B4]**. Do not put ACL field-mapping in the gateway (Radar + Azure offloading). |

Uber’s 2021 post (~**500K QPS**, **1 500+** APIs) is the *single* self-built gateway at the other extreme: generated per-endpoint stacks, not BFF sprawl **[→C6-1]**.

### 3.3 Aggregation and GraphQL fan-out

Azure aggregation (Learn page, fetched 2026-09-13) plus the 2026-06-02 considerations **[→C6-1]**:

1. One client request → N backends in **parallel async I/O**.
2. **Partial vs fail-all** is a product decision, encoded in the aggregator (APIM `send-request` example: per-request timeouts, conditional errors, circuit breakers).
3. Correlation IDs across branches; monitor **response size**.
4. Cache-as-failover is allowed; coupling backends through the gateway is not.
5. If composition is domain-heavy, **move it behind** the gateway.

**Chatty-fan-out failure.** A BFF or GraphQL router that walks an entity graph issues *O(fields × depth)* RPCs. SoundCloud: client logic migrated in → recursive pagination → BFF timeouts **[→C6-1]**. Apollo Federation’s router is supposed to plan *only needed* subgraphs; **demand control** (mutation base cost **10**, object **1**, `max` example **1000**) is the cap **[→C6-1]**. Apigee API-product GraphQL operations cap: **50** (enforced). None of these replace a per-branch **C7** timeout.

Budget inequality (same as **[→C7]** / first-pass):

`client deadline > gateway outer > max(branches)  [or Σ if sequential] > per-try`

A 504 on the *outer* is not retried by Envoy unless `per_try_timeout` fired **[→retry]** / **[→C7]**.

### 3.4 Placement — C4 / C7 / C1

| Control | At the **gateway** | **In-mesh / in-process** | Do not |
|---|---|---|---|
| **C4** rate limit | Per API key / JWT / IP / usage plan. AWS: usage plan → stage method → **account 10 000 RPS / 5 000 burst** (14 newer Regions **2 500 / 1 250**; RPS adjustable, burst **not**) **[→C4]**. Kong plugin `limit_by` default **consumer**. | Per-service / per-tenant fairness the edge cannot see. | Double-count the same token bucket at edge *and* sidecar without a shared budget. Fail-open defaults (Envoy `failure_mode_deny` false, Kong `fault_tolerant` true) **[→C4]**. |
| **C7** timeout | **Outer** user-facing bound + remaining-time stamp if the product can (`x-envoy-expected-rq-timeout-ms` **[→C7]**). | **Per-try** + connect, excluding TLS from a tight request timer. | Copy a 29 s / 60 s / 300 s product default as if it were an SLO. Idle ≠ request (Kong `read_timeout` is *between successive reads*). |
| **C1** breaker | Gateway-scoped: APIM backend breaker; Kong **passive** (trip only); Envoy Gateway **concurrency** 1024 (not a failure detector — same confusion as Envoy “circuit breaking” **[→breaker]**); SCG wraps Resilience4j. | Host **outlier detection** / library breaker per dependency. | One gateway breaker over many shards (Azure *resource differentiation*). Retry an **Open** circuit. |
| **C2** retry | Only if the product actually retries, and only for **idempotent** methods, **one layer**. | Preferred: the hop *just above* the failing service, under a budget. | Stack gateway retries + mesh retries + SDK retries (SRE / Brooker 243× **[→retry]**). |

AWS API Gateway **does not retry** integration timeouts — “clients must implement their own retries”; integration timeout **50 ms–29 s** (REL05-BP05, fetched 2026-09-13). That is a *placement fact*, not a defect: the managed edge is the outer bound; retry lives downstream or in the client, not both.

### 3.5 Timeout + retry: gateway vs downstream

Two coherent designs (same inequality as **[→C7]**):

| Design | Outer (gateway) | Inner | Retry |
|---|---|---|---|
| **Envoy / Envoy Gateway** | `timeouts.request` (Envoy default **15 s** if unset) | `timeouts.backendRequest` ≤ request; EG `perRetry.timeout` | EG `numRetries` default **2** *when* a retry policy exists. HTTPRoute Retries (GEP-1731) beat `BackendTrafficPolicy` from EG **v1.3**. Unconfigured: `/status/500` returns **immediately** (EG retry task). |
| **.NET-style** | Total 30 s | Attempt 10 s | Retry *inside* total, *outside* attempt **[→C7]** |

Incoherent (what the defaults produce if you never set them):

| Product | Unset timeout | Unset retry | Effect on a 200 ms p99 payment |
|---|---|---|---|
| AWS REST | **29 s** (50 ms floor; Regional/private raisable, may cut account RPS; edge-optimized **not**) | **None** | Pins a gateway execution + backend thread 29 s. Client *must* retry 504s. |
| AWS HTTP | **30 s**, **not** increasable | **None** | Same, plus no REST canary / WAF / cache **[→C6-1]**. |
| Kong Service | connect/read/write **60 000 ms** (idle-between-I/O) | **5** transport retries | 60 s stall; GET retried 5× on connect/timeout; **5xx/429 not retried**; POST after the upstream received the body **not** retried. |
| Apigee | `connect.timeout.millis` **3 000**; `io.timeout.millis` **55 000**; `api.timeout` unset → Ingress **300 s**; `keepalive.timeout.millis` **60 000** | Connect may be retried **up to three times** (total can exceed 3 s) | 55 s read stall; 300 s if you never set `api.timeout`. Limit row “Target connection timeout **300 s**” is **Planned** enforcement (limits page, updated 2026-09-11). |
| Azure APIM | `forward-request timeout` **300 s** — waits for **response headers**; values **> 240 s** “may not be honored” | **No** retry unless you add `<retry>` | 5-minute header wait. `buffer-request-body` default **false** — retries need it **true**. |
| Spring Cloud Gateway | `httpclient.connect-timeout` default **30 s**; `response-timeout` **unset** (configprops: no default) | Retry filter *if enabled*: **3**, **5XX**, **GET** only, backoff **off**, timeout **unlimited** | Connect bounded; body can run forever. Enabling Retry on POST caches the body (`CACHED_REQUEST_BODY_ATTR`). |
| Envoy Gateway | Envoy route **15 s** | (none until HTTPRoute / BTP) | Closest to a sane outer. Concurrency breaker **1024** / **1024** / **1024** — overflow is 503, not a failure-trip. |

---

## 4. Verified defaults / standards (fetched 2026-09-13)

### 4.1 AWS API Gateway

| Knob | REST | HTTP API | Notes |
|---|---|---|---|
| Integration timeout | **50 ms–29 s**; Service Quotas “Maximum integration timeout in milliseconds” default **29 000**; raisable for **Regional and private** only (announcement **2024-06-04**, LLM-motivated; may reduce Region throttle). Edge-optimized **not** raisable. | **30 s**, **not** increasable | 504 on expiry. **No integration retry** (REL05-BP05). |
| Account throttle | **10 000 RPS**, burst **5 000** (other Regions); 14 newer Regions **2 500 / 1 250**. RPS yes, burst **no**. | Shared account bucket | Usage plan → method → account → AWS Regional **[→C4]**. |
| Payload | **10 MB**, not increasable | **10 MB**, no | Combined headers REST public **20 480 B**, private **8 000 B**; HTTP request-line+headers **10 240 B**. |
| Cache TTL | default **300 s** (0–3600); cached object **1 048 576 B** | **No** cache | Hourly by size **[→C6-1]**. |
| Idle connection (integration) | **310 s**, not increasable | — | Not a request timeout. |
| JWT / authorizers | Lambda + Cognito; **10** / API | Built-in JWT; JWKS **1 500 ms** / **150 000 B**; OIDC discovery **1 500 ms**; Lambda authorizer **10 000 ms**; **10** authorizers | RSA-only JWT **[→C6-1]**. |
| Canary | `percentTraffic` **0–100** **[→B4]** | **No** | Version of the *proxy*. |
| Resources / stages | 300 / 10 | 300 routes / 10 stages | `#foreach` cap **1 000**; mapping template **300 KB**. |

REST-only vs HTTP-only capability split (keys, WAF, X-Ray, body transform, Cloud Map, …) stays **[→C6-1]**. Direct REST → internal ALB since **2025-11-21** **[→C6-1]**.

### 4.2 Kong Gateway (Service schema + proxying page)

- `connect_timeout` / `read_timeout` / `write_timeout` default **60 000 ms** (1–2 147 483 646). Connect fail → **502** + retry. Read/write idle → **504**.
- `retries` default **5** (0–32 767). Nginx `proxy_next_upstream` defaults: error/timeout while connecting, sending, or reading **headers**. **5xx and 429 are not retried.** Mid-body failure is not retried (bytes already streamed).
- Idempotent methods (`GET HEAD PUT DELETE OPTIONS TRACE`) retry up to `retries`. Non-idempotent (`POST PATCH` …) only if the TCP connect failed *before* the upstream received the request, unless `proxy_next_upstream non_idempotent`.
- Listeners default **8000 / 8443** (`proxy_listen`); Admin **8001**. Plugin phases and 128 MB `request-size-limiting` default **[→C6-1]**.
- Passive health checks (not retries) mark targets unhealthy via `healthchecks.passive.unhealthy.http_statuses` **[→breaker]**.

### 4.3 Apigee (endpoint properties + limits, both “Last updated 2026-09-11”)

| Property / limit | Default | Enforcement |
|---|---|---|
| `connect.timeout.millis` | **3 000** → HTTP **503** (sometimes **504** with LoadBalancer) | Documented; auto-retry connect **≤ 3** |
| `io.timeout.millis` | **55 000** (no data to read / socket not writable) | Ingress timeout while reading client → **408**; target read/write → **504** |
| `api.timeout` | unset → Ingress **300 s** (not configurable); must be **< 300 s** if set | After each policy, MP computes `api.timeout − elapsed`; `< 0` → **504**. Next hop `io.timeout` = min(remaining, `io.timeout.millis`) |
| `keepalive.timeout.millis` | **60 000** | Pool idle |
| Buffered payload | limits table **30 MB** enforced; parse.limit default **10M** (min 10M, max 30M) | Streamed listed **10 MB**, **not** enforced |
| Target endpoints / proxy | **1 000** | Yes |
| Target connection timeout (limits row) | **300 s** | **Planned** |
| SpikeArrest `Rate` | 4 000 / s, 240 000 / min | **Planned** |

### 4.4 Envoy Gateway

Fetched: HTTP Timeouts task (Helm pin **v1.9.1**), Circuit Breakers task (**v1.8.4**), Retry task (`/latest`, “might not be stable”).

- HTTPRoute `timeouts.request` / `timeouts.backendRequest`; `request >= backendRequest`; `0s` disables (Gateway API). Unspecified → **implementation-specific**; EG documents Envoy’s **15 s** request default. Miss → **504** `upstream request timeout`.
- `BackendTrafficPolicy.retry.numRetries` default **2**. `perRetry.backOff` / `timeout`. `retryOn.triggers` + `httpStatusCodes`. GEP-1731 HTTPRoute retries **override** BTP (since **v1.3**).
- Circuit breakers are Envoy **concurrency** limits: default threshold **1024** (“may be too strict for high-throughput”). Distinct counters **per `BackendReference`**, even if BTP targets the Gateway. Overflow → **503**. Distributed: **not** synced across Envoy processes.

### 4.5 Spring Cloud Gateway (WebFlux reference + `configprops`)

- `spring.cloud.gateway.server.webflux.httpclient.connect-timeout` — “the default is **30s**” (millis field).
- `…httpclient.response-timeout` — listed, **no default**. Per-route `response-timeout: -1` disables a global value. YAML examples of `1000` / `5s` are **examples**, not defaults.
- `Retry` filter, *if enabled*: retries **3**, series **5XX**, methods **GET**, exceptions `IOException` + `TimeoutException`, backoff/jitter **disabled**, retry timeout **unlimited**. Retries **all filters after it**. Body-bearing methods cache the body.
- `CircuitBreaker` filter needs `spring-cloud-starter-circuitbreaker-reactor-resilience4j`. Delegates to Resilience4j (failure-rate **50%**, TimeLimiter **1 s** **[→breaker]** / **[→C7]**). Optional `fallbackUri` (`forward:` only); `statusCodes` can trip on HTTP; `resumeWithoutError` still returns **504** / **503** for timeout and `CallNotPermittedException`.

---

## 5. Knobs, observability, tuning

### 5.1 Knobs

| Knob | Too low | Too high | Starting point (sourced) |
|---|---|---|---|
| Gateway **outer** timeout | False 504s; truncates inner retries (Envoy leftover) **[→C7]** | APIM 300 s / Kong 60 s / AWS 29 s pins workers | Brooker percentile of *this* hop + pad; must be **<** any idle LB in front (ALB **60 s** **[→C7]**) |
| `backendRequest` / per-try | Healthy tail looks down | Outer never fires first | < outer; cover one attempt only |
| Gateway retries | 0 on a fleet of flaky connects | Kong **5** × mesh **2** × SDK **2** | **0** at AWS; **0** on POST; at most **1** layer (SRE) |
| Edge C4 | UX 429s on launch | Account 10 k RPS is the only backstop | Usage-plan per client; keep account headroom **[→C4]** |
| EG / Envoy concurrency 1024 | 503s under legitimate fan-out | Never overflow; slow backend holds 1024 | Set `maxParallelRequests` to what the *callee* can do (EG task: 10 + pending 0 to fail fast) |
| Aggregation fan-out | Partial data surprises | Sequential N× latency | Parallel + explicit partial; cap GraphQL cost **[→C6-1]** |

### 5.2 Observability (feeds D4)

| Signal | Why |
|---|---|
| Gateway **class** of 504 (integration / io / connect / stream-idle) | AWS 504 ≠ Kong idle-read 504 ≠ APIM header-wait 504 |
| Per-backend latency + error, tagged `route` / `integration` | Aggregation hides which branch died |
| Remaining deadline at ingress vs at each backend | Copied 29 s vs remaining **[→C7]** |
| Retry count **by hop** (`envoy_cluster_upstream_rq_retry`, Kong `X-Kong-Upstream-Latency`) | Catch stacked retries |
| Authn fail vs backend fail | 401/403 must **not** trip C1 **[→breaker]** |
| Rate-limit 429 vs backend 429 | Edge quota vs provider quota |
| Partial-aggregation rate | Azure “design it explicitly” |

Kong `X-Kong-Proxy-Latency` / `X-Kong-Upstream-Latency` are computed in `header_filter` — **before** a slow body finishes (docs warning). Prefer a metrics plugin for the full cycle.

### 5.3 Tuning

1. Write the remaining-time inequality first (**C7**), then pick the product whose *default* is closest and **override it**.
2. Put C4 at the edge (identity you already terminated). Put C2 **one** hop above the failure, never on AWS integrations, never on non-idempotent POSTs at Kong/SCG.
3. Put failure-trip C1 on the *dependency*, concurrency C1 on the *proxy*. Do not read EG “circuit breaker” as Fowler’s automaton.
4. Aggregation: measure branch p99; set per-branch timeout to that; outer ≥ slowest branch + compose; document partial.
5. Revisit when the histogram walks; a gateway timeout that never fires is the APIM-300 / AWS-29 trap.

---

## 6. Worked calibration — checkout → payment (timeout + retry at gateway vs down)

Constraints are a **design drill**, not a vendor SLA. Method: Brooker p99.9 + SRE remaining-time **[→C7]** + REL05-BP05 (API Gateway does not retry) + Kong/EG/SCG defaults above. Same checkout histogram as C7: p50 **80 ms**, p99.9 **420 ms** on `POST /capture`.

User-facing checkout budget **3 s**. Per-attempt **500 ms**. C2 policy (cited, not redesigned): 2 retries, full jitter, 200 ms base → worst-case sleeps ≈ 600 ms. `3.0 ≥ 3×0.5 + 0.6` → **2.1 s** used, **0.9 s** slack.

| Layer | Choice | Why |
|---|---|---|
| **Client** | One retry on **504/503** only, budget 1, honour `Retry-After` | AWS: *clients* retry. Do not also retry 400s. |
| **Edge gateway** | AWS REST integration timeout **2.5 s** (inside 3 s, above 2.1 s). **Retries = 0** (not available anyway). C4: usage-plan ~ checkout RPS × 1.2, burst for page-load. JWT/API-key here. | Outer bound. 29 s default would pin the 99.9% path. Canary of the *proxy* is **B4**, not this SLO. |
| If the edge is **Kong** | `connect_timeout` **5 000**; `read_timeout` **2 500**; `retries` **0** on the capture Service | Default 60 s / 5 retries is a Brooker 243× starter kit on a POST that timed out after the body was received — Kong *won’t* retry that POST (good) but *will* retry GET status 5× (set retries explicitly). |
| If the edge is **Envoy Gateway** | `timeouts.request: 2.5s`, `backendRequest: 500ms`; **no** BTP retry on `POST /capture`; concurrency `maxParallelRequests` sized to payment pool | 15 s default is closer than 29/60/300 but still 5× the budget. |
| If the edge is **Apigee** | `api.timeout` **2500**; `io.timeout.millis` **500** on the payment TargetEndpoint; `connect.timeout.millis` **3000** left (connect ≠ request) | Unset `api.timeout` = **300 s** Ingress. |
| If the edge is **APIM** | `<forward-request timeout="3" timeout-ms="…"/>` **and** a backend circuit breaker per payment shard; **no** `<retry>` around capture | Default **300 s** header wait. |
| If the edge is **SCG** | `connect-timeout` 1000; `response-timeout` **2.5s**; **do not** attach Retry to POST; CircuitBreaker name per issuer, TimeLimiter **500 ms** not 1 s | 1 s TimeLimiter default is *tight* vs 500 ms attempt — align them. |
| **Checkout service** | Remaining ~2.4 s after 50–80 ms gateway+auth. Retry **here** (idempotency key), breaker per payment authority **[→breaker]** | One retry layer, just above the rejector (SRE). |
| **Payment** | Per-attempt 500 ms; outgoing to issuer capped **1.0 s** **[→C7]** | Do not inherit 2.4 s onto issuer threads. |
| **Hedging** | **Off** on capture | Side effect. Status GET may hedge at p95 **[→C7]**. |

If checkout is a **BFF** that also fetches cart + recommendations: those branches get their **own** 400–800 ms budgets and a documented partial (Azure). Do not hang the capture path on the wishlist.

---

## 7. Failure modes and when-not-to-use

1. **Product default as SLO.** AWS 29 s, HTTP 30 s, Kong 60 s, Apigee 55 s / 300 s, APIM 300 s, SCG response unset, EG 15 s. The unnamed min on the path still wins (**[→C7]** CloudFront/ALB).
2. **Stacked retries.** Kong 5 + EG 2 + SDK 2 on GET; SCG Retry retries *downstream filters*. Brooker / SRE amplification **[→retry]**.
3. **Gateway retries a POST.** SCG will if you enable Retry and add POST; Kong will only on pre-receive connect fail — unless someone set `non_idempotent`. Double capture without **C9**.
4. **AWS 504, client retries, payment succeeded.** Integration timeout does not cancel work the way gRPC `CANCELLED` does **[→C7]**. Idempotency key required.
5. **Chatty aggregation / GraphQL N+1.** SoundCloud pagination; Azure SPoF/bottleneck; Apollo cost cap bypassed if `enforce` is off **[→C6-1]**.
6. **Business logic in the façade.** Radar Hold; Azure offloading; **[→B4]** ACL-in-gateway.
7. **BFF sprawl.** Authz drift; Newman’s unowned general API; SoundCloud VAS correction **[→C6-1]**.
8. **One C1 over many backends.** Azure resource differentiation; EG counters are per `BackendReference` — good — but one APIM backend pool is not.
9. **Concurrency limit mistaken for a breaker.** EG/Envoy 1024 never “trips Open”; it 503s. **[→breaker]** two-mechanism warning.
10. **C4 only at the account cap.** 10 k RPS shared across *all* APIs; one noisy neighbor.
11. **APIM timeout is headers, not body.** A trickling SSE/body can outlive `timeout` while `buffer-response` default **true** chunks 8 KB. Set `buffer-response="false"` for SSE (docs).
12. **Raising AWS REST > 29 s.** LLM-shaped; eats Region throttle; HTTP APIs cannot follow; edge-optimized cannot follow.
13. **JWKS 1.5 s / Lambda authorizer 10 s** folded into a 500 ms attempt.
14. **Strangler canary of *all* URLs.** **[→B4]** — the gateway can, the new service cannot.
15. **Idle used as request timeout.** Kong `read_timeout`, Apigee `io.timeout.millis` (no *data*), AWS idle connection **310 s**.

**When a gateway is the wrong tool.** One or two services (Azure routing). Client already next to backends (Azure aggregation). You need object-level authz only the service can do. You were about to put orchestration in the proxy (Radar; put a service behind). Greenfield with no edge policy need — start with a mesh ingress *or* nothing, not APIM-300.

**When a *single* gateway is wrong.** Multiple UX surfaces with different payload/auth shapes (Newman BFF) *or* a strangler that needs path extract (**B4**) plus a stable public URL (keep one thin façade, BFFs behind it).

**When a BFF is wrong.** One team cannot own it; duplication has already been extracted three times (Newman → domain service); the BFF is paginating a foundation API (SoundCloud).

---

## 8. Cross-links

| Id | Why |
|---|---|
| **C1** | Gateway vs mesh breaker; EG concurrency ≠ Fowler trip; APIM / Kong passive **[→breaker]** |
| **C2** | One retry layer; AWS does not retry; Kong 5 / SCG 3 / EG 2 defaults |
| **C4** | Edge usage-plan / consumer limit; account 10 k RPS; do not restack algorithms |
| **C5** | Host selection *behind* the route — not this card |
| **C7** | Outer vs per-try vs idle; remaining-time; Brooker percentile |
| **C8** | Aggregation bulkheads; EG pending-queue |
| **C9** | POST / capture idempotency when any hop retries |
| **C10** | Uber edge load-shedding **[→C6-1]**; timeout is the backstop, not the shed |
| **B4** | Gateway as strangler façade; canary / `URI_PATH` / ACL-not-in-gateway |
| **B6** | Sidecar / east-west; mTLS after the edge terminates TLS |
| **A1** | REST/gRPC wire; transcoding is only the façade |
| **A6** | Version routing / sunset — header match is not a gateway pattern card |
| First-pass | [api-gateway-external-research.md](api-gateway-external-research.md) |
| Workspace | [aws/ch08.md](../../../cases/aws/ch08.md) (gateway / mesh / BFF / strangler one-liners) |

---

## 9. Sources

Fetched 2026-09-13 unless noted.

**Canon / workspace.** microservices.io/patterns/apigateway.html **[→C6-1]** · samnewman.io/patterns/architectural/bff (2015-11-18) **[→C6-1]** · learn.microsoft.com/azure/architecture/patterns/gateway-aggregation (example + APIM `send-request`; considerations also **[→C6-1]** 2026-06-02) · learn.microsoft.com/…/gateway-routing · learn.microsoft.com/…/gateway-offloading **[→C6-1]** · thoughtworks.com/radar overambitious-api-gateways **[→C6-1]** · [aws/ch08.md](../../../cases/aws/ch08.md) · [b4-strangler-fig-external-research.md](b4-strangler-fig-external-research.md).

**AWS.** docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html · …/http-api-quotas.html · docs.aws.amazon.com/general/latest/gr/apigateway.html (29 000 ms; 10 000 / 5 000; 14 Regions 2 500 / 1 250) · aws.amazon.com/about-aws/whats-new/2024/06/amazon-api-gateway-integration-timeout-limit-29-seconds/ · docs.aws.amazon.com/wellarchitected/latest/framework/rel_mitigate_interaction_failure_client_timeouts.html (REL05-BP05) · REST vs HTTP / JWT / canary / ALB **[→C6-1]**.

**Kong.** developer.konghq.com/gateway/entities/service/ (schema defaults) · developer.konghq.com/gateway/traffic-control/proxying/ (60 s / 5 retries / no 5xx retry / POST rule).

**Apigee.** cloud.google.com/apigee/docs/api-platform/reference/endpoint-properties-reference (`connect` 3000, `io` 55000, `api.timeout` vs 300 s Ingress) · …/reference/limits (30 MB / 1000 targets / 300 s Planned; GraphQL ops **50**; updated 2026-09-11).

**Envoy Gateway.** gateway.envoyproxy.io/docs/tasks/traffic/http-timeouts/ (v1.9.1, Envoy 15 s) · gateway.envoyproxy.io/latest/tasks/traffic/retry/ (`numRetries` 2; no default 500 retry) · gateway.envoyproxy.io/v1.8/tasks/traffic/circuit-breaker/ (1024) · gateway-api.sigs.k8s.io/geps/gep-1731/.

**Spring Cloud Gateway.** docs.spring.io/spring-cloud-gateway/reference/spring-cloud-gateway-server-webflux/http-timeouts-configuration.html · …/gatewayfilter-factories/retry-factory.html · …/circuitbreaker-filter-factory.html · docs.spring.io/spring-cloud-gateway/reference/configprops.html (connect **30 s**; response unset).

**Azure APIM.** learn.microsoft.com/azure/api-management/forward-request-policy (`timeout` **300**, >240 s caveat) · learn.microsoft.com/azure/api-management/retry-policy · APIM backend breaker **[→breaker]**.

**Cited forward.** [c7-timeouts-external-research.md](c7-timeouts-external-research.md) · [circuit-breaker-external-research.md](circuit-breaker-external-research.md) · [retry-backoff-external-research.md](retry-backoff-external-research.md) · [mesh-proxy-retry-external-research.md](mesh-proxy-retry-external-research.md) · [rate-limiting-external-research.md](rate-limiting-external-research.md) · SoundCloud / Uber / Apollo / Gateway API version train **[→C6-1]**.

---

## 10. Uncertain / left out

- Envoy Gateway `/latest` retry page vs v1.9.1 timeouts vs v1.8.4 circuit-breaker — `numRetries` default **2** asserted from `/latest`; not re-dumped from a v1.9 CRD.
- Whether every EG install still inherits Envoy **15 s** when HTTPRoute `timeouts` is omitted: docs say Envoy default; Gateway API says implementation-specific.
- GEP-1731 Standard-channel status as of Gateway API v1.5 was inferred absent in **[→C6-1]**; EG v1.3+ implements the API regardless.
- Spring `connect-timeout` “default is 30s” is from configprops; Netty’s own idle is not separately asserted. `1000`/`5s` on the timeouts page are examples.
- Resilience4j TimeLimiter **1 s** inside SCG CircuitBreaker: library default **[→C7]**, not re-read from SCG source this pass.
- Apigee “automatically retry the connection up to three times” — whether that is connect-only (text) or includes read was not traced in MP source.
- Limits “Target connection timeout 300 seconds / Planned” vs property `connect.timeout.millis` **3 s** — both asserted; the 300 s row is a *product cap*, not the default.
- AWS newer-Region count: **14** listed on the quotas page this fetch (first pass said 13). Burst still non-adjustable.
- Whether raising REST > 29 s is purely self-service after Service Quotas approval: re:Post describes the request; “Case opened” if over max — max value not published here.
- APIM `timeout` > 240 s “may not be honored” — no published infrastructure idle number.
- Kong plugin priority 910/1250 **[→C6-1]** not re-verified.
- Uber 500K QPS / SoundCloud “hundreds of millions per hour” not re-fetched.
- PromQL names above are recommendations, not a vendor schema.
- Pricing (AWS HTTP $1/M vs REST $3.50/M) stays **[→C6-1]**; not used in the calibration.
- Nygard / Fowler breaker prose is **[→breaker]**; not re-derived.
