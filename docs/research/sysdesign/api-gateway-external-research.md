---
type: research
title: 'API gateway patterns — external research (2026-09-13)'
description: >-
  Source-verified research backing the API gateway Concept in
  cases/SystemDesignPatterns: Richardson/Newman/Azure canon (routing,
  aggregation, offloading, BFF), gateway vs proxy vs LB vs mesh boundaries,
  Kubernetes Gateway API state through v1.5, anti-patterns, verified AWS API
  Gateway / Kong / Apigee numbers, edge responsibilities (JWT, transcoding,
  caching, canary, WAF), GraphQL federation and demand control, and the
  SoundCloud and Uber production lessons.
tags: [research, api-gateway, bff, edge, system-design-patterns]
---

# C6 API gateway patterns — external research (2026-09-13)

**Method.** Facts verified against the cited primary page 2026-09-13; paraphrase; identifiers exact. Forward citations: [circuit-breaker-external-research.md](circuit-breaker-external-research.md) (CB note: APIM backend breaker + pools, Kong/Traefik/NGINX passive breakers, LLM gateways, 429/Retry-After) and [mesh-proxy-retry-external-research.md](mesh-proxy-retry-external-research.md) (retry note: API Gateway does not retry; Envoy/Istio per-try timeout defaults; APIM retry policy bounds).

## 1. Pattern canon

- **microservices.io "API Gateway / Backends for Frontends"** (Richardson, © 2026): problem — clients must otherwise call many fine-grained APIs per user request. Variants: single gateway (sole entry point, proxy or fan-out, optional per-client adapters) vs **BFF** (one gateway per client kind). Benefits: insulates clients from partitioning and discovery; per-client APIs; fewer round trips; simpler clients; protocol translation. Drawbacks: another HA component to build and run; extra hop (called typically insignificant). Related: discovery patterns, Access Token, Circuit Breaker, API Composition.
- **Azure Architecture Center — three pattern pages.** *Gateway Routing* (updated 2025-12-09): one endpoint, L7 rules to services/instances/versions (blue-green, incremental, config-change revert); considerations — SPoF/bottleneck, load-test against cascades, L7 inputs, global vs regional (Front Door vs App Gateway), lock down direct backend access; not for one-or-two-service apps. *Gateway Aggregation* (ms.date **2026-06-02**): gateway decomposes one request into several backend calls and combines; considerations — don't introduce cross-backend coupling; place near backends; bulkheads/breakers/retries/timeouts inside the gateway; a slow branch may return **partial data** — design it explicitly; async I/O; correlation IDs; monitor response sizes; cache as failover; **consider a dedicated aggregation service behind the gateway** (different resource profile than routing). Not suitable to reduce calls to a single service (add a batch op) or when the client is near the backends. *Gateway Offloading* (updated 2025-12-09): move cross-cutting features to the gateway (certs, authn, TLS termination, monitoring, protocol translation, throttling); benefits — simpler services, specialist ownership, a logging floor; considerations — HA/scaling, offload only whole-app features, **"Business logic should never be offloaded to the gateway"**, correlation IDs.
- **Sam Newman, BFF** (samnewman.io, 2015-11-18): term from Phil Calçado's team at SoundCloud (one general API could not serve desktop and mobile). Rules: **one BFF per user experience** (accepts SoundCloud's single BFF for iOS+Android because one team owns both); **the UI team owns its BFF**. Duplication tolerated until ~3 occurrences, then extract a domain service (not a shared library), or push aggregation downstream. BFFs fan out in parallel and degrade gracefully (wishlist without stock levels). Critique: a general-purpose API backend for many UIs becomes a bloated bottleneck owned by nobody.

## 2. Boundaries and the Kubernetes Gateway API

- **CNCF glossary**: API gateway = one entry point applying cross-cutting API controls (authn/z, rate limiting, metrics, policy) uniformly; load balancer = spreads requests across instances; service mesh = uniform reliability/observability/security for **service-to-service** traffic (sidecar or eBPF). Working distinction: gateway = reverse proxy with API-management semantics at the **north-south** edge; mesh = same per-request controls **east-west**.
- **Gateway API** (`gateway.networking.k8s.io`): **v1.0 GA 2023-10-31** (Gateway, GatewayClass, HTTPRoute → v1 Standard; CEL validation replacing the webhook). Two channels: Standard and Experimental. **Ingress is frozen** — official docs recommend Gateway API; Ingress stays GA, "no further changes". **GAMMA**: a Route with a **Service as parentRef** configures east-west (mesh) traffic; mesh support + GRPCRoute → Standard in **v1.1 (2024-05-09)**. **v1.4 (2025-10-06)**: BackendTLSPolicy, supportedFeatures, named Route rules → Standard; experimental Mesh resource, default gateways, externalAuth filter. **v1.5 (2026-02-27)**: ListenerSet, TLSRoute, HTTPRoute CORS filter, client cert validation, TLS-origination cert selection, ReferenceGrant → Standard; 4-month release train. HTTPRoute retries (GEP-1731) absent from both Standard lists (inference; see Uncertain).

## 3. Anti-patterns

- **"Overambitious API gateways"** (ThoughtWorks Radar, **Hold**; appearances Nov 2015 → May 2018): gateways marketed to run business logic (orchestration, transformation, rules) put domain smarts into transport middleware — single points of scaling/control, hard to test and deploy; keep the gateway to generic edge concerns.
- **Gateway as a new monolith**: Newman's bottleneck; SoundCloud saw both directions (one API forcing compromises; then BFF sprawl re-creating duplication). Remedy: thin gateway, heavyweight composition in a service behind it (Azure aggregation).
- **Business logic in the gateway**: Azure states it absolutely; aggregation page routes complex composition to a dedicated service; the Radar blip is the industry version.
- **Chatty aggregation / fan-out budgeting**: Azure requires explicit partial-vs-fail behavior with per-request timeouts, breakers, async I/O; SoundCloud documents recursive pagination in BFFs causing timeouts and failures. Budget: client deadline > gateway total > branch total > branch per-try (Envoy `per_try_timeout` defaults to the route timeout — a timed-out attempt eats the whole budget and a 504 is not retried under retry_on 5xx; Istio same; retry note), with SRE deadline propagation (CB note).

## 4. Platform facts (verified numbers)

- **AWS API Gateway, REST vs HTTP APIs**: REST-only — API keys + usage plans, per-client throttling, request validation, WAF, edge-optimized + private endpoints, resource policies, caching, canary deployments, request **body** transformation, custom gateway responses, X-Ray, response streaming, mock integrations. HTTP-only — built-in **JWT authorizers**, automatic deployments, Cloud Map private integrations. Pricing (US East): HTTP $1.00/M first 300 M then $0.90; REST $3.50/M first 333 M, $2.80 next 667 M, $2.38 beyond; caching hourly by size.
- **Quotas**: account throttle **10,000 RPS/Region, 5,000 burst** (13 newer Regions 2,500/1,250); payload **10 MB not increasable**; REST integration timeout "50 ms – 29 s", **raisable above 29 s for Regional and private REST APIs** (Service Quotas L-E5AE38E3; shipped **2024-06-04**, motivated by LLM workloads; may cost Region-level throttle) and **not** for edge-optimized; HTTP APIs max integration timeout **30 s not increasable**; REST 300 resources / 10 stages; caching TTL default 300 s (0–3600); HTTP APIs 300 routes, 10 authorizers, JWKS timeout 1,500 ms; Lambda-authorizer response timeout 10,000 ms. No integration retries (retry note). Raw-Markdown fetch trick: AWS docs pages are fetchable as `.md`.
- **ALB vs API Gateway** (AWS Prescriptive Guidance): API Gateway = managed API management (authorizers, per-client throttling + quotas, caching, transformation); ALB = load-balanced web backends (rich routing inputs, health checks, stickiness; fixed-response only; rate limiting only via WAF). Since **2025-11-21** REST APIs integrate directly with internal ALBs (previously NLB hop).
- **Kong**: plugin phases (certificate, rewrite, access, response, header/body_filter, log); within a phase **static numeric priority, highest first** (blog examples: rate-limiting 910, key-auth 1250); **dynamic plugin ordering** in Gateway Enterprise 3.0 (2022-10-04); 12 scope-precedence levels (consumer+route+service … global). Request size limiting off by default (`nginx_http_client_max_body_size = 0`); `request-size-limiting` plugin defaults 128 MB, `require_content_length` false.
- **Apigee**: buffered request/response **30 MB enforced** (streamed: 10 MB listed, not enforced); target connection timeout 300 s ("Planned" enforcement); 1,000 target endpoints/proxy. APIM breaker/pool and retry-policy facts cite forward.

## 5. Edge responsibilities (one source each)

- **JWT at the edge** (AWS HTTP API JWT authorizer): reads token from identitySource; verifies signature via issuer `jwks_uri` (RSA only; keys cacheable ≤ 2 h), then `kid`, `iss`, `aud`/`client_id`, `exp`, `nbf`, `iat`, scopes vs `authorizationScopes`; claims passed to the integration. **OWASP API Security Top 10 2023**: API2 broken authentication (centralize at edge); API4 unrestricted resource consumption (timeouts, max upload, per-client rate limits, pagination caps, third-party spend caps — the gateway's list); API1 BOLA is per-object authorization the gateway generally cannot own (SoundCloud's scattered-authorization lesson).
- **Transformation**: REST = params + body; HTTP APIs = parameter mapping only; ALB = fixed response only. Keep transformations generic (Radar).
- **Protocol translation**: grpc-gateway (protoc plugin, RESTful JSON → gRPC per `google.api.http`; no bidi streaming); Envoy `grpc_json_transcoder` (needs proto descriptor set; rewrites to `POST /<pkg>.<svc>/<method>`; streams as JSON arrays; `google.api.HttpBody`; preserves x-envoy-original-path).
- **Caching**: REST stage/method cache TTL 300 s default (0–3600), billed hourly; absent from HTTP APIs/ALB; cache-as-failover (Azure).
- **Rate limiting**: usage plans per client; 10 k RPS account backstop; 429/Retry-After and LLM-gateway variants cite forward.
- **Canary**: REST canary deployments — same stage, preconfigured percentage of randomly selected traffic, then promote or disable; Azure routing covers blue-green generically.
- **WAF**: attaches to REST (not HTTP APIs); on ALB, WAF rate-based rules are the rate-limit story; Azure offloading centralizes WAF/TLS.

## 6. GraphQL at the edge

- **Apollo Federation**: subgraphs composed into a supergraph; the **router** is the single entry point that plans and executes across only the needed subgraphs — gateway aggregation with a schema-aware planner; Connectors front REST sources. v2.0 April 2022; **v2.15 (LTS) July 2026** (router ≥ 2.16.0).
- **Persisted queries**: GraphOS persisted query lists (build-time manifests via Rover; router polls; modes allow/audit/**safelist**/IDs-only; wire shape shared with APQ — but APQ is a latency cache with **no security value**; PQL safelisting is Enterprise).
- **Demand control** (Apollo Router, IBM GraphQL Cost Directive spec): mutation base cost **10**, query/subscription 0; object/interface/union 1, scalar/enum 0; lists via assumed size; `demand_control.enabled`, `mode: measure | enforce`, `strategy.static_estimated.max` (e.g. 1000), `list_size`; overrides `@cost(weight)`, `@listSize(assumedSize | slicingArguments)`.

## 7. Production lessons

- **SoundCloud** (developers.soundcloud.com, Part 1 2021-07-29, Part 2 2021-08-20): BFF pioneered ~2013 after one public API could not serve mobile and web; by 2021, **dozens of BFFs** at hundreds of millions of requests/hour, each doing gatekeeping (rate limiting, authn, header sanitization, cache control). Failures: authorization/integration logic **replicated across BFFs and drifting** (correctness + security); new BFFs spun up for narrow uses (sprawl); client logic migrating in ("extension of the client") → recursive pagination → timeouts. Correction: a **Value-Added Services layer** between BFFs and foundation services owning entity aggregates and authorization; BFFs shrink to client-specific formatting — aggregation moved behind the gateway.
- **Uber** ("The Architecture of Uber's API Gateway", 2021-05-19): single self-built entry point — routing, protocol conversion (JSON/Thrift/Protobuf), rate limiting, load shedding, header enrichment, security auditing; ~**500K QPS**, **1,500+ APIs** migrated off the legacy Node edge. Per-endpoint generated stack: Protocol manager → Middleware (authn/z, rate limits) → Endpoint handler (validation, transformation) → generated Client. Lessons: centralized cross-cutting features pay for every onboarded team; implementation choices dominate performance at scale.

## Sources

Canon: microservices.io/patterns/apigateway.html · samnewman.io/patterns/architectural/bff (2015-11-18) · learn.microsoft.com gateway-routing (upd. 2025-12-09) / gateway-aggregation (2026-06-02) / gateway-offloading (upd. 2025-12-09).
Boundaries: glossary.cncf.io api-gateway / service-mesh / load-balancer · kubernetes.io blog gateway-api-ga (2023-10-31), v1-1 (2024-05-09), v1-4 (2025-10-06), v1-5 (2026-02-27) · gateway-api.sigs.k8s.io gamma + versioning · kubernetes.io ingress docs (frozen note).
Anti-patterns: thoughtworks.com/radar overambitious-api-gateways (Hold, 2015–2018) · Azure pages · SoundCloud Part 1 · retry note (per-try timeouts).
Platforms: docs.aws.amazon.com apigateway limits + execution-service-limits-table + http-api-quotas (raw .md) · aws.amazon.com whats-new 2024-06 integration-timeout · http-api-vs-rest · api-gateway pricing · prescriptive-guidance services-comparison · whats-new 2025-11 REST↔ALB · developer.konghq.com plugin entity + request-size-limiting · konghq.com blog dynamic-plugin-ordering (2022-10-04) · Kong kong.conf.default · docs.cloud.google.com apigee limits.
Edge: AWS http-api-jwt-authorizer (raw .md) · api-security.owasp.org 2023 (API1, API2, API4) · github.com/grpc-ecosystem/grpc-gateway · envoyproxy.io grpc_json_transcoder_filter · AWS canary-release (raw .md) · CB note §§3–5.
GraphQL: apollographql.com federation + federation versions + persisted-queries + demand-control.
Lessons: developers.soundcloud.com service-architecture-1 (2021-07-29), -2 (2021-08-20) · uber.com/blog/architecture-api-gateway (2021-05-19).

## Uncertain / could not verify (excluded from the Concept)

- Radar blip 2015 verbatim text (paraphrase only; ring + dates from the current page).
- GEP-1731 retries "below Standard as of v1.5" is inferred from promotion-list absence.
- Kong priorities 910/1250 from the 2022 blog; no current versioned table located.
- Apollo demand-control plan gating mixed in docs; safelisting = Enterprise is stated.
- API Gateway prices are US-East as rendered; the old "71% cheaper" claim not asserted.
- Newman page has no changelog; may have been revised since 2015.
- microservices.io page undated (© 2026 only).
- Uber's earlier edge-generation posts not fetched.
- OWASP one-liners are paraphrases (fetch truncation; no quotes).
- Whether the >29 s timeout raise is purely self-service is not described in the announcement.
