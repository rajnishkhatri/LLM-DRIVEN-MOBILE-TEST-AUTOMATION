---
type: research
title: 'Mesh / proxy retry configuration — external research (2026-09-13)'
description: >-
  Source-verified infrastructure retry defaults for Envoy, Istio, Linkerd, AWS
  ALB / API Gateway / App Mesh / ECS Service Connect, Azure API Management,
  Kong, Traefik, NGINX, Kubernetes Ingress, Gateway API, and Spring Kafka
  DefaultErrorHandler. Numbers reproduced from current official docs. Unverified
  items listed at the end.
tags: [research, retry, backoff, mesh, proxy, envoy, istio, linkerd]
---

# Mesh / proxy retry configuration — external research (2026-09-13)

Fetched 2026-09-13. Official docs only. Numbers and identifiers reproduced exactly. Items not on the cited pages are in **§ Unverified**.

---

## Per-system table

| System | Default attempts | Retry-on | Per-try timeout | Backoff | Budget | Header controls | Version / date |
|---|---|---|---|---|---|---|---|
| **Envoy router** | `num_retries` default **1**. No retries unless a retry policy or `x-envoy-retry-on` / `x-envoy-retry-grpc-on` is set. Circuit-breaker `max_retries` (concurrent retries) default **3**. | HTTP: `5xx`, `gateway-error`, `reset`, `reset-before-request`, `connect-failure`, `envoy-ratelimited`, `retriable-4xx` (**409 only**), `refused-stream`, `retriable-status-codes`, `retriable-headers`, `http3-post-connect-failure`. gRPC headers: `cancelled` (1), `deadline-exceeded` (4), `internal` (13), `resource-exhausted` (8), `unavailable` (14). `5xx` includes connect-failure and refused-stream; `5xx` does **not** retry when the **outer** `x-envoy-upstream-rq-timeout-ms` is exceeded (504). | `per_try_timeout` optional; if unspecified, uses the global route timeout (so a 5xx timeout will not retry — total budget exhausted). Also `per_try_idle_timeout` (absent = none). Header: `x-envoy-upstream-rq-per-try-timeout-ms` (ignored if ≥ global route timeout). | Fully jittered exponential: default base **25ms** (`upstream.base_retry_backoff_ms`); first retry delay in `[0, (2^N-1)B)` — first 0–24ms, 2nd 0–74ms, 3rd 0–174ms; max interval default **10×** base (**250ms**). `retry_back_off.base_interval` required if set; values &lt; 1 ms rounded to 1 ms; `max_interval` default 10× base. `rate_limited_retry_back_off`: match `Retry-After` (SECONDS, form `120`) then `X-RateLimit-Reset` (UNIX_TIMESTAMP); jitter `random(interval, interval * 1.5)`; `max_interval` default **300 seconds**. Configuring rate-limited backoff does **not** by itself cause retries. | `retry_budget.budget_percent` default **20%** of (active + pending requests). `min_retry_concurrency` default **3**. `budget_interval` default **0ms** (presently active/pending only). If `retry_budget` is set, it **overrides** the `max_retries` circuit breaker. | `x-envoy-retry-on`, `x-envoy-retry-grpc-on`, `x-envoy-max-retries` (overrides policy), `x-envoy-retriable-status-codes`, `x-envoy-retriable-header-names` (internal clients only), `x-envoy-upstream-rq-timeout-ms`, `x-envoy-upstream-rq-per-try-timeout-ms`, `x-envoy-hedge-on-per-try-timeout`. Downstream: `x-envoy-overloaded` if dropped for maintenance mode or circuit breaking. Upstream attempt: `x-envoy-attempt-count` (“1” on first). Runtime `upstream.use_retry` = % eligible. | Latest Envoy docs banner: **envoy 1.40.0-dev-1dc43a**. URLs below. |
| **Istio VirtualService** | Cluster-wide default if unspecified: `attempts: 2`. `attempts` = retries, not total requests; max requests = `1 + attempts`. `attempts: 0` disables. MeshConfig `defaultHttpRetryPolicy`: default attempts **2**; setting attempts to 0 disables globally. `perTryTimeout` **cannot** be set globally via MeshConfig. | VirtualService `retryOn` if unspecified: `connect-failure,refused-stream,unavailable,cancelled`. MeshConfig default string: `connect-failure,refused-stream,unavailable,cancelled,retriable-status-codes`. May also list HTTP codes (`retryOn: "503,reset"`). Codes match the **destination** response, not Istio’s translated 503 on reset. Example in HTTPRetry prose also mentions 503. | `perTryTimeout`: MUST be ≥1ms. Default = HTTP route `timeout`, “which means no timeout.” Route `timeout` default is disabled. | Interval “determined automatically (25ms+)”. `backoff` = min duration between attempts; unset → **25ms** base for “exponetial” backoff. Example: `attempts` 3, `backoff` 2s, `timeout` 3s → retried only once. | Not documented on VirtualService HTTPRetry. | None documented on VirtualService (Envoy headers still apply at the sidecar). | Fetched `istio.io/latest` 2026-09-13. Latest release announced: **Istio 1.31.0** (2026-08-31). HTTPRetry + MeshConfig pages as fetched. |
| **Linkerd HTTPRoute / GRPCRoute** | `retry.linkerd.io/limit` default **1** if unspecified. Retries are **opt-in** (`retry.linkerd.io/http` or `/grpc` must be set). Body &gt; **64KiB** is not retried. | HTTP (`retry.linkerd.io/http`): single code `"504"`, range `500-504`, `gateway-error` (**502–504**), `5xx`. gRPC (`retry.linkerd.io/grpc`): `cancelled`, `deadline-exceeded`, `internal`, `resource-exhausted`, `unavailable`. | `retry.linkerd.io/timeout`: unspecified = **no** retry timeout. Units required (`5s`, `200ms`; not `5`). HTTPRoute `timeouts.request` / `timeouts.backendRequest`: unspecified or 0 = not enforced; MUST be ≥1ms if set. Each retry starts a new `backendRequest`; all count against `request`. | Not documented on HTTPRoute annotations. | HTTPRoute counted retries: **no** budget field. Legacy ServiceProfile `retryBudget`: `retryRatio`, `minRetriesPerSecond`, `ttl` — current reference does **not** state numeric defaults. 2019 Linkerd 2.2 design post example: `retryRatio: 0.2`, `minRetriesPerSecond: 10`, `ttl: 10s`. | If `--allow-l5d-request-headers`: `l5d-retry-http`, `l5d-retry-grpc`, `l5d-retry-limit`, `l5d-retry-timeout`, `l5d-timeout`, `l5d-response-timeout`. | HTTPRoute/GRPCRoute annotations since **Linkerd 2.16** (announce 2024-08-13). Current docs: linkerd.io/docs. ServiceProfiles still supported; if a ServiceProfile exists, annotation retries are **ignored**. |
| **AWS ALB** | No retry-policy field found on ALB / target-group attribute pages fetched. | — | — | — | — | — | ALB troubleshooting / attributes / target-group attributes fetched 2026-09-13. **No retry configuration documented.** |
| **AWS API Gateway** | Does **not** retry integration timeouts. Clients must retry. | — | Integration timeout **50 ms–29 s**. | — | — | — | REL05-BP05 (Well-Architected). Quotas page fetched; no retry policy there. |
| **AWS App Mesh** | Default Envoy route (not visible in App Mesh API): **Max retries `2`**. User `HttpRetryPolicy.maxRetries` required if you set a policy (min 0). Best practice: “at least two”. EOS **2026-09-30**. | Default: HTTP `503`; gRPC `UNAVAILABLE`; TCP `connect-failure` and `refused-stream`; Reset (disconnect/reset/read timeout). Configurable `httpRetryEvents`: `server-error` (500, 501, 502, 503, 504, 505, 506, 507, 508, 510, 511), `gateway-error` (502, 503, 504), `client-error` (409), `stream-error` (refused stream). `tcpRetryEvents`: `connection-error`. `server-error` and `gateway-error` include Envoy `reset`. Best-practice recommended events: TCP `connection-error`; HTTP/HTTP2 `stream-error` + `gateway-error`; gRPC `cancelled` + `unavailable`. | `perRetryTimeout` **required** on a user policy. Timeout includes the initial attempt. | Not specified as exponential on the API page. | Circuit-breaker `max_retries` defaulted to **2147483647** (effectively disabled). | — | App Mesh userguide `envoy-defaults.html` + `API_HttpRetryPolicy.html` + best-practices. |
| **ECS Service Connect** | **Number of retries: 2**. Second attempt avoids the previous host. | “retry connection that pass through the proxy and fail” — connection failures. Outlier detection (separate): 5+ failed connections in last 30 s → avoid host 30–300 s. | `perRequestTimeout` default **15 seconds** (0 disables). `idleTimeout` HTTP/HTTP2/GRPC **5 minutes**; TCP **1 hour**. | — | — | — | `service-connect-concepts-deploy.html` fetched 2026-09-13. Retry count **not** user-configurable on that page. |
| **Azure API Management** | No implicit default. `count` **required**, range **1–50**. Policy runs children **once**, then retries until `condition` is false or `count` exhausted. | `condition` expression (required). Examples: `context.Response.StatusCode == 500`; `>= 500`; `== 429`. | Not a per-try timeout field. Child `forward-request` / `send-request` carry their own timeouts. | `interval` only → **fixed**. `interval` + `delta` → linear: `interval + (count - 1)*delta`. `interval` + `max-interval` + `delta` → exponential: `interval + (2^(count - 1)) * random(delta * 0.8, delta * 1.2)`, cap `max-interval`. `first-fast-retry` default **`false`**. | — | — | https://learn.microsoft.com/en-us/azure/api-management/retry-policy — All tiers. `ms.date` not in rendered page. Fetched 2026-09-13. |
| **Kong Gateway Service** | `retries` default **5** (schema min 0, max 32767). | Transport-level only, Nginx default `proxy_next_upstream` = error/timeout while connecting, sending request, or reading **response headers**. **Does not** retry upstream 5xx or 429. Does not retry after response body streaming starts. Idempotent methods (`GET`, `HEAD`, `PUT`, `DELETE`, `OPTIONS`, `TRACE`) retried; non-idempotent (`POST`, `PATCH`, …) only if TCP failed **before** upstream received the request, unless `proxy_next_upstream non_idempotent`. | `connect_timeout` / `write_timeout` / `read_timeout` default **60000** ms. Connect failure → 502 + retries. Read/write timeout → 504; retry depends on method. | Immediate next-upstream (Nginx). No Kong backoff field. | — | — | https://developer.konghq.com/gateway/entities/service/ + https://developer.konghq.com/gateway/traffic-control/proxying/ fetched 2026-09-13. |
| **Traefik Retry middleware** | `attempts` **required**; no default. | Default: retry if server **does not reply**. Stops as soon as the server answers, **regardless of status**. `status` default `[]`. Network-error retries on unless `disableRetryOnNetworkError` (default **false**). `retryNonIdempotentMethod` default **false** (`POST`, `LOCK`, `PATCH`). If `disableRetryOnNetworkError` is true, `status` is required. | `timeout` default **0**. | `initialInterval` default **0** (immediate). If set, exponential; max interval = **2×** `initialInterval`. | — | — | https://doc.traefik.io/traefik/reference/routing-configuration/http/middlewares/retry/ fetched 2026-09-13. `maxRequestBodyBytes` default **2MB**. |
| **NGINX `proxy_next_upstream`** | `proxy_next_upstream_tries` default **0** = unlimited. `proxy_next_upstream_timeout` default **0** = unlimited. | Default: `error timeout`. Optional: `denied`, `invalid_header`, `http_500`, `http_502`, `http_503`, `http_504`, `http_403`, `http_404`, `http_429`, `non_idempotent`, `off`. Only if nothing yet sent to client. `error`/`timeout`/`denied`/`invalid_header` always count as unsuccessful attempts; HTTP 5xx/429 only if listed; `http_403`/`http_404` never unsuccessful. Non-idempotent (`POST`, `LOCK`, `PATCH`) not retried after request sent unless `non_idempotent` (since 1.9.13). | No per-try timeout field. | None (immediate next server). | — | — | https://nginx.org/en/docs/http/ngx_http_proxy_module.html fetched 2026-09-13. |
| **ingress-nginx** | ConfigMap `proxy-next-upstream-tries` default **3**. Timeout default **0**. | ConfigMap `proxy-next-upstream` default `"error timeout"`. Annotations: `nginx.ingress.kubernetes.io/proxy-next-upstream`, `-timeout`, `-tries`. `service-upstream` annotation: `proxy_next_upstream` has **no effect**. | Same as NGINX + connect/send/read timeout annotations. | None. | — | — | https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/configmap/ fetched 2026-09-13. |
| **Kubernetes native / Gateway API** | Core Service / Endpoints / Ingress API: **no** retry object. Gateway API **GEP-1731** proposes `HTTPRoute.rules[].retry` (`codes`, attempts, `backoff`). Future goal: retry budget. | Implementation-defined until GEP is adopted by a given controller. | Interaction with HTTPRoute timeouts is a GEP goal. | GEP: min backoff; exponential/jitter/cap are **non-goals**. | Budget is a **future** GEP goal. | — | https://gateway-api.sigs.k8s.io/geps/gep-1731/ fetched 2026-09-13. GEP status banner was not a dated Standard/GA label in the fetch. |
| **Spring Kafka `DefaultErrorHandler`** | Default `FixedBackOff(0L, 9)` → **9 retries**, **10** delivery attempts, **0** delay. After ten failures, default recoverer **logs** at ERROR. Example: `FixedBackOff(1000L, 2L)` = 2 retries / 3 attempts / 1 s. `FixedBackOff.UNLIMITED_ATTEMPTS` = infinite. | Listener exceptions (not HTTP). | — | `FixedBackOff(intervalMs, maxRetries)`. Also `ExponentialBackOffWithMaxRetries` since 2.7.3. | — | — | https://docs.spring.io/spring-kafka/reference/kafka/annotation-error-handling.html + API 4.1.x. DLQ: `DeadLetterPublishingRecoverer` after backoff STOP; framework does not auto-create the DLT topic. |

---

## 1. Envoy router retries

**Docs (latest, banner `envoy 1.40.0-dev-1dc43a`, fetched 2026-09-13):**

- Router filter / headers: https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/router_filter
- Route `RetryPolicy` proto: https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/route/v3/route_components.proto
- Circuit breakers / `RetryBudget` proto: https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/cluster/v3/circuit_breaker.proto
- HTTP routing / retry semantics: https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/http/http_routing
- Transient-failures FAQ: https://www.envoyproxy.io/docs/envoy/latest/faq/load_balancing/transient_failures.html

**`retry_on` (from `x-envoy-retry-on`):**

- `5xx` — any 5xx, or no response (disconnect/reset/read timeout). Includes `connect-failure` and `refused-stream`. Does **not** retry when the request exceeds `x-envoy-upstream-rq-timeout-ms` (504). Use per-try timeout to retry slow attempts. Outer timeout includes all retries.
- `gateway-error` — 502, 503, 504, or no response (disconnect/reset/read timeout).
- `reset` — no response (disconnect/reset/read timeout).
- `reset-before-request` — reset, only if headers have not been sent upstream.
- `connect-failure` — TCP connect failure/timeout. Included in `5xx`. Not upstream request timeouts.
- `envoy-ratelimited` — header `x-envoy-ratelimited` present.
- `retriable-4xx` — currently **only 409**. Docs warn: 409 can mean optimistic-lock conflict; retrying then always fails with another 409.
- `refused-stream` — upstream reset with `REFUSED_STREAM` (safe to retry). Included in `5xx`.
- `retriable-status-codes` — codes in the retry policy **or** `x-envoy-retriable-status-codes`.
- `retriable-headers` — response headers matching the policy **or** `x-envoy-retriable-header-names`.
- `http3-post-connect-failure` — HTTP/3 post-connect failure.

**Defaults:** `num_retries` optional, defaults to **1**. “By default, Envoy will not perform retries unless you’ve configured them.” `host_selection_retry_max_attempts` unspecified → “retrying once.”

**Host selection:** `retry_host_predicate` extensions include `envoy.retry_host_predicates.previous_hosts`, `omit_canary_hosts`, `omit_host_metadata`. FAQ example uses `previous_hosts` + `host_selection_retry_max_attempts: "5"`.

**`x-envoy-overloaded`:** set on the **downstream** response when the request was dropped due to maintenance mode or upstream circuit breaking. HTTP routing page also: “Envoy retries requests when x-envoy-overloaded is present” and recommends retry budgets (preferred) or `max_retries` to avoid retry storms.

**Retry budget RECONFIRMED** from current proto: `budget_percent` defaults to **20%**; `min_retry_concurrency` defaults to **3**.

---

## 2. Istio VirtualService retries

**Docs (`istio.io/latest`, fetched 2026-09-13):**

- VirtualService / HTTPRetry: https://istio.io/latest/docs/reference/config/networking/virtual-service/
- MeshConfig `defaultHttpRetryPolicy`: https://istio.io/latest/docs/reference/config/istio.mesh.v1alpha1/
- Latest release: Istio **1.31.0** announced 2026-08-31 — https://istio.io/latest/news/releases/1.31.x/announcing-1.31/

**Documented discrepancy (do not collapse):**

| Source | Default `retryOn` string |
|---|---|
| HTTPRoute `retries` note + HTTPRetry `retryOn` field | `connect-failure,refused-stream,unavailable,cancelled` |
| MeshConfig `defaultHttpRetryPolicy` | `connect-failure,refused-stream,unavailable,cancelled,retriable-status-codes` |

HTTPRetry example prose says a retry occurs on connect-failure, refused_stream, or upstream **503**. `retryRemoteLocalities` is a BoolValue; “see the retry plugin configuration.” `retryIgnorePreviousHosts` defaults to **true**.

---

## 3. Linkerd HTTPRoute / GRPCRoute

**Docs (fetched 2026-09-13):**

- Retries: https://linkerd.io/docs/reference/retries/
- Retries and timeouts: https://linkerd.io/docs/features/retries-and-timeouts/
- HTTPRoute timeouts: https://linkerd.io/docs/reference/httproute/
- 2.16 announce (retries on Gateway API resources): https://linkerd.io/2024/08/13/announcing-linkerd-2.16/
- ServiceProfiles (legacy): https://linkerd.io/2/reference/service-profiles/
- ServiceProfile budget example (2019-02-22): https://linkerd.io/2019/02/22/how-we-designed-retries-in-linkerd-2-2/

**Since:** Linkerd **2.16** (2024-08-13): “retry and timeout configuration to these same Gateway API resources.” Before 2.16, retries/timeouts were ServiceProfiles. ServiceProfiles remain supported; a ServiceProfile on the Service **overrides** HTTPRoute/GRPCRoute annotations.

Timeout annotations named on the features page: `timeout.linkerd.io/request`, `timeout.linkerd.io/response`. HTTPRoute spec timeouts: `request`, `backendRequest`.

---

## 4. AWS ALB / API Gateway / App Mesh / ECS Service Connect

**ALB** — https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-troubleshooting.html · https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html · https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html — no retry-policy attribute on the fetched pages.

**API Gateway** — REL05-BP05: https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_mitigate_interaction_failure_client_timeouts.html — “API Gateway clients must implement their own retries when handling timeouts. API Gateway supports a 50 millisecond to 29 second integration timeout for downstream integrations and does not retry when integration requests timeout.” Quotas: https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html (no retry policy).

**App Mesh** (EOS 2026-09-30) — https://docs.aws.amazon.com/app-mesh/latest/userguide/envoy-defaults.html · https://docs.aws.amazon.com/app-mesh/latest/APIReference/API_HttpRetryPolicy.html · https://docs.aws.amazon.com/app-mesh/latest/userguide/best-practices.html · routes: https://docs.aws.amazon.com/app-mesh/latest/userguide/routes.html

**ECS Service Connect** — https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect-concepts-deploy.html — “Number of retries: 2”; `perRequestTimeout` default 15 seconds.

---

## 5. Azure API Management

https://learn.microsoft.com/en-us/azure/api-management/retry-policy — `count` 1–50 required; `interval` required; `first-fast-retry` default `false`; sections inbound/outbound/backend/on-error; all gateway types listed.

---

## 6. Kong / Traefik / NGINX

- Kong Service schema `retries` default 5: https://developer.konghq.com/gateway/entities/service/
- Kong proxy retries: https://developer.konghq.com/gateway/traffic-control/proxying/
- Traefik Retry: https://doc.traefik.io/traefik/reference/routing-configuration/http/middlewares/retry/
- NGINX: https://nginx.org/en/docs/http/ngx_http_proxy_module.html (`proxy_next_upstream` default `error timeout`; `proxy_next_upstream_tries` default 0)

---

## 7. Kubernetes native

No retry field on core `Service`, `Endpoints`, or `Ingress`. Retries exist only on controllers:

- ingress-nginx ConfigMap defaults `proxy-next-upstream: "error timeout"`, `proxy-next-upstream-tries: 3`, `proxy-next-upstream-timeout: 0` — https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/configmap/
- Gateway API GEP-1731 HTTPRoute retries — https://gateway-api.sigs.k8s.io/geps/gep-1731/

---

## 8. Kafka / Spring Kafka (complementary)

https://docs.spring.io/spring-kafka/reference/kafka/annotation-error-handling.html — default `FixedBackOff(0L, 9)`; ten failures then log; `DeadLetterPublishingRecoverer` publishes after backoff STOP. API: https://docs.spring.io/spring-kafka/docs/4.1.x/api/org/springframework/kafka/listener/DefaultErrorHandler.html — “default back off (9 retries, no delay).”

---

## 9. One-layer / stacking warnings (official)

| Source | Statement |
|---|---|
| Google SRE book ch. 22 | “avoid amplifying retries by issuing retries at multiple levels: a single request at the highest layer may produce a number of attempts as large as the product of the number of attempts at each layer… If the database can’t service requests because it’s overloaded, and the backend, frontend, and JavaScript layers all issue 3 retries (4 attempts), then a single user action may create 64 attempts (4^3) on the database.” Also: randomized exponential backoff; overloaded backends should return a specific code so clients **do not retry**. https://sre.google/sre-book/addressing-cascading-failures/ |
| Envoy HTTP routing | Retry budgets “to prevent their contribution to large increases in traffic volume.” “It is recommended to either configure retry budgets (preferred) or set maximum active retries circuit breaker… to avoid retry storms.” Circuit-breaking overview: `max_retries` should “aggressively circuit break retries” so “the overall retry volume cannot explode.” https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/http/http_routing · https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking.html |
| Linkerd | “retries by definition will increase the load on your system. A set of services that have requests being constantly retried could potentially get taken down by the retries.” Retries only on idempotent methods. https://linkerd.io/docs/features/retries-and-timeouts/ |
| AWS REL05-BP05 | Timeouts too low “can generate increased traffic on the backend… In some cases, this can lead to complete outages because all requests are being retried.” Points to Builders’ Library *Timeouts, retries, and backoff with jitter*. https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_mitigate_interaction_failure_client_timeouts.html |

**Not found on official Istio / Envoy pages fetched:** an explicit sentence “do not enable application retries and mesh retries at the same time.” The SRE product-of-attempts rule is the official one-layer statement.

---

## § Unverified

- Envoy **stable** (non-`dev`) version number corresponding to the `latest` docs banner `1.40.0-dev-1dc43a` on 2026-09-13.
- Whether Istio’s **implemented** default still injects `retriable-status-codes` + HTTP 503 (MeshConfig / older source) vs VirtualService text that omits them. Docs disagree; source not re-read for 1.31.
- Istio `retryRemoteLocalities` default (field exists; default value not on the HTTPRetry table).
- Current Linkerd ServiceProfile **numeric** `retryBudget` defaults (0.2 / 10 / 10s appear in the 2019 design post as the customization example; current reference lists fields only). Whether HTTPRoute counted retries still apply a ServiceProfile-style budget: **not** stated on the current retries page.
- Exact Linkerd version when `timeout.linkerd.io/*` annotations landed vs 2.16 (retries+timeouts announced together for Gateway API).
- AWS ALB: **absence** of an undocumented internal retry. Official attribute pages fetched do not define one.
- API Gateway HTTP API vs REST vs WebSocket: only the Well-Architected “does not retry when integration requests timeout” sentence was used; no per-API-type retry policy page found.
- App Mesh default-policy account-cutoff text (meshes created before 2020-07-29) — older userguide wording; current `envoy-defaults.html` fetch states the default is created for all HTTP/HTTP2/gRPC routes without that cutoff paragraph.
- Azure APIM `ms.date` / product version (not in rendered markdown).
- Kong Gateway product version of the schema page (default `retries: 5` is on the current schema).
- Traefik product version of the Retry page.
- Whether Gateway API GEP-1731 `HTTPRoute.retry` is Standard, Experimental, or unimplemented in a given controller as of 2026-09-13.
- Kubernetes core API: negative proof is “no field on Service/Ingress”; a future CRD was not exhaustively searched beyond Ingress and Gateway API.
- Spring Kafka **current** GA module version on the live site vs the 4.1.x API URL; behavior quote is from the current reference page.
- HAProxy `retry_on` / `retries` (mentioned in GEP-1731 background; **not** fetched from haproxy.org for this note).
- GCP load balancer / Cloud Endpoints / Cloud Service Mesh retry settings (not in the ask).
- An official Istio or Envoy sentence that names “application + sidecar” stacking by those words.
