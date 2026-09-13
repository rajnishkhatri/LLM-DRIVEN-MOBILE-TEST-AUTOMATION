---
type: research
title: 'Load balancing techniques — external research (2026-09-13)'
description: >-
  Source-verified research backing the Load balancing Concept (C5): algorithm
  canon (WRR, least-connections, P2C from Mitzenmacher, consistent hashing
  from Karger/ketama, Maglev, bounded-load CH), Envoy/Istio specifics, L4 vs
  L7 and ALB/NLB behavior incl. ATW and draining, gRPC/HTTP/2 pinning and
  connection-age rebalancing, DNS and anycast, Kubernetes topology-aware
  serving, operational failure modes, and queueing math.
tags: [research, load-balancing, consistent-hashing, p2c, system-design-patterns]
---

# C5 Load balancing techniques — external research (2026-09-13)

**Method.** Facts verified against primaries 2026-09-13 (papers read as PDFs; Envoy banner 1.40.0-dev; Kubernetes docs v1.37). **Cited forward**: Envoy outlier ejection/panic/slow start, ALB health checks + fail-open, Istio connectionPool, Netflix concurrency-limits ([circuit-breaker note](circuit-breaker-external-research.md)); Envoy `num_retries` 1 + retry budget, Istio `attempts: 2`, Linkerd retries ([mesh-proxy note](mesh-proxy-retry-external-research.md)).

## 1. Algorithms with canon

- **Round robin / weighted RR**: NGINX default is weighted RR (`weight=1` default; 5-1-1 example). Envoy `LbPolicy` default ROUND_ROBIN. HAProxy roundrobin per weight.
- **Least connections**: NGINX `least_conn` (weight-aware, ties by WRR); HAProxy `leastconn` (counts queued too; recommended for long sessions — LDAP/SQL — not short HTTP); IPVS lc/wlc.
- **Least request + P2C**: Envoy weighted least request — equal weights ⇒ O(1) P2C with `choice_count` default **2**; unequal weights ⇒ dynamic WRR with `weight = lb_weight / (active_requests + 1)^active_request_bias`, bias default **1.0**.
- **P2C canon** (Mitzenmacher, IEEE TPDS 12(10), 2001): supermarket model; "Having d = 2 choices leads to exponential improvements" in expected time vs d = 1; d = 3 only a constant factor over d = 2. d = 1 equilibrium expected time 1/(1−λ). Two choices ≈ close to global-knowledge balancing.
- **Random**: Envoy RANDOM; NGINX `random [two [least_conn]]`; HAProxy `random(<draws>)` through consistent hashing (two draws avoid the most-loaded).
- **IP/flow hash**: NGINX `ip_hash` (first three IPv4 octets; mark removed servers `down` to preserve mapping); K8s `sessionAffinity: ClientIP` (default None; timeout 10800 s).
- **Consistent hashing** (Karger et al., STOC 1997): "a small change in the bucket set does not induce a total remapping" (vs mod-p moving nearly everything); properties balance, monotonicity, spread, load. **ketama** (Last.fm): 100–200 points per server on a continuum; key → next-larger point.
- **Ring hash vs Maglev**: Envoy RING_HASH is ketama-style — `minimum_ring_size` default **1024**, `maximum_ring_size` **8M**, xxHash. **Maglev** (NSDI 2016): Google's software network LB "serving Google's traffic since 2008"; ECMP across machines; 10 Gbps small-packet per machine; prime lookup table via per-backend permutations; evaluated M = 65,537 and 655,373; optimizes even load, accepts slightly more disruption, connection tracking protects established flows. Envoy `MaglevLbConfig.table_size` default **65537** (prime, ≤ 5,000,011); Envoy docs: Maglev "not as stable as ring hash when upstream hosts change".
- **Bounded-load CH** (Mirrokni/Thorup/Zadimoghaddam, arXiv:1608.01350): c = 1+ε; no bin exceeds ⌈c·m/n⌉; overflow walks clockwise; O(1/ε²) expected moves. Vimeo/HAProxy production: cache bandwidth "decrease … by a factor of almost 8" (Google Research blog 2017-04-03). **HAProxy `hash-balance-factor`** default **0 (disabled)**; with `hash-type consistent`, 150 caps a server at 1.5× average concurrent; recommended 125–200; also honored by `balance random`. HAProxy 3.2 adds `hash-preserve-affinity always|maxconn|maxqueue`.

## 2. Envoy / Istio specifics

- Envoy: default ROUND_ROBIN; ring 1024/8M; maglev 65537; **zone-aware routing**: both clusters out of panic mode, `routing_enabled` default 100%, `min_cluster_size` default **6**; residual spills cross-zone. **Locality weighted LB** mutually exclusive with zone-aware; overprovisioning factor 140 → effective_weight degrades below ~71% availability. **Stateful sessions** filter: cookie or header host pinning; `strict: false` fallback vs `strict: true` 503.
- Istio (1.31): `loadBalancer.simple` UNSPECIFIED default ("Istio will select an appropriate default"); **1.14 changed the default from ROUND_ROBIN to LEAST_REQUEST**; consistentHash keys header/cookie/sourceIp/queryParam; ringHash.minimumRingSize 1024; maglev.tableSize 65537; slow start = `warmup` (minimumPercent 10, aggression 1.0).

## 3. Layer 4 vs layer 7 (AWS)

- **grpc.io framing**: L4 copies bytes, one connection → one backend; L7 parses the protocol — "With HTTP/2, LB can distribute the streams from one client among multiple backends".
- **NLB flow hash**: TCP hashes protocol, src IP/port, dst IP/port **and TCP sequence number** — each connection pinned for life; UDP 5-tuple; QUIC by Connection ID. DNS-caching hazard: TTL-ignoring clients keep hitting removed IPs.
- **ALB algorithms** (`load_balancing.algorithm.type`): `round_robin` **default**; `least_outstanding_requests` (in-progress requests; HTTP/2→1.1 conversions counted separately; **cannot combine with slow start**); `weighted_random` (cannot combine with slow start or stickiness). Stickiness bypasses the algorithm after first pick.
- **Automatic Target Weights**: anomaly *detection* always on (≥ 3 healthy targets; 5xx + connection failures vs peers; `normal`/`anomalous` via DescribeTargetHealth); anomaly *mitigation* requires `weighted_random`, re-adjusts every 5 s, gradual return; `load_balancing.algorithm.anomaly_mitigation` default **off**.
- **Draining / slow start**: `deregistration_delay.timeout_seconds` default **300 s** (0–3600); draining targets get no new requests; sticky-but-draining rerouted. NLB adds connection_termination (default true only for new UDP groups). ALB `slow_start.duration_seconds` default **0** (30–900 s linear); pre-existing healthy targets never enter slow start.

## 4. gRPC / HTTP/2 pinning and rebalancing

- All RPCs of a channel multiplex one HTTP/2 connection → connection-level balancing pins everything to one backend. K8s blog (2018-11-07): kube-proxy is connection-level — "no new connections = no opportunity for load balancing"; fixes = headless Service + client LB, or L7 proxy/mesh.
- **grpc.io LB blog** (2017-06-15): proxy (untrusted clients; hop + throughput cost) vs thick client (best perf; per-language complexity) vs lookaside. gRPC client default with no service-config policy is **pick_first** (no spreading); `round_robin`; xDS supersedes grpclb.
- **Rebalancing knobs**: gRFC A9 — server GOAWAY at `MAX_CONNECTION_AGE` (**default infinite**) + GRACE, mandated **±10% jitter**; `MAX_CONNECTION_IDLE`. Envoy `max_connection_duration` unset (no limit); `max_requests_per_connection` unset = unlimited (1 disables keep-alive); Istio `maxRequestsPerConnection` default 0 (cited forward).

## 5. Client-side and DNS

- Envoy discovery: `STRICT_DNS` (continuous re-resolution, `dns_refresh_rate` default 5000 ms unless `respect_dns_ttl`) vs `LOGICAL_DNS` (first IP at connection time; recommended for large DNS-RR names). Rotation only rebalances **new** connections; gRPC re-resolves on connection loss or GOAWAY.
- **Anycast** (Cloudflare primer, 2011, mod. 2026-07-15): one IP, routers deliver to the closest machine; failover by route withdrawal; DDoS diffusion. GCP: global external LBs front a single anycast IP (GFE/Envoy); passthrough Network LB runs on **Maglev**.

## 6. Kubernetes topology-aware serving (v1.37)

- kube-proxy modes: iptables (**default**; future default nftables), ipvs (**deprecated v1.35**, off by default v1.40, removal ~v1.43), nftables (**stable v1.33**), kernelspace (Windows).
- **Topology Aware Routing** (annotation `service.kubernetes.io/topology-mode: Auto`): per-zone hints proportional to allocatable CPU; safeguards disable hints (fewer endpoints than zones, unbalanceable allocation, missing zone labels…); advise ≥ 3 endpoints/zone; incompatible with internalTrafficPolicy Local. Docs banner beta v1.23 vs v1.33 blog "GA (KEP-2433/4444)" — treat `trafficDistribution` as the GA surface.
- **`spec.trafficDistribution`**: `PreferClose` GA v1.33, deprecated as alias in v1.34 for **`PreferSameZone`** and **`PreferSameNode`** (node → zone → cluster; beta on-by-default v1.34). Unset = even cluster-wide. Precedence: topology-mode annotation > trafficDistribution; `Local` policy overrides both.
- **externalTrafficPolicy**: Cluster (spreads; hides client IP; extra hop) vs Local (source IP kept; nodes without local endpoints forward **nothing**; `healthCheckNodePort` allocated so the cloud LB can probe). For Cluster, point LB checks at kube-proxy `${NODE_IP}:10256/healthz` (503 during node deletion = draining); ProxyTerminatingEndpoints stable v1.28.

## 7. Operational failure modes

- **Hot key under CH**: hashing balances keys, not load (Karger's own motivation); ketama's virtual points reduce variance, cap nothing; bounded-load CH is the fix (HAProxy factor 150; Vimeo ~8×).
- **Long-lived-connection imbalance after a rolling deploy**: connection-oriented balancing rebalances only at setup — survivors keep the herd. Fixes: MAX_CONNECTION_AGE + jitter (A9), Envoy max_connection_duration / max_requests_per_connection, per-request L7 balancing.
- **Cold-target hammering**: ALB slow start default **off** and incompatible with LOR/weighted_random; least-loaded policies attract floods to cold/fast-failing hosts without warm-up (Envoy slow start cited forward; Istio warmup).
- **Load-feedback herding** (Brooker 2012-01-17): with stale load data, "pick the least loaded" herds every client onto the same quiet host — oscillation; best-of-2 "rejects herd behavior much more strongly" — why Envoy/NGINX/HAProxy implement least-loaded as P2C. Damping in managed LBs: ATW 5 s adjustments + gradual return; Envoy active_request_bias < 1.0.
- **Sticky skew**: after scale-out, stickiness keeps load on old targets (ALB: expire/shorten cookie; `AWSALB`, duration default 86400 s, 1 s–7 d).

## 8. Queueing math

- Little's law: limit ≈ RPS × latency (concurrency-limits README, cited forward) — the quantity least-request/LOR compare.
- Brooker "Surprising Economics of Load-Balanced Systems" (2020-08-06): M/M/c — at equal utilization, 13% of requests queue at c = 5 vs 3.6% at c = 10; bigger balanced pools run hotter for the same latency.

## Sources

Papers: Mitzenmacher TPDS 2001 (eecs.harvard.edu PDF) · Karger et al. STOC 1997 (princeton PDF) · Maglev NSDI 2016 (research.google PDF) · arXiv:1608.01350 (v3 2017-07-27).
Envoy 1.40.0-dev: load_balancers + zone_aware + locality_weight overviews · cluster.proto · protocol.proto · stateful_session filter · service_discovery.
Istio: destination-rule reference · 1.14 change notes.
AWS: NLB introduction · ALB edit-target-group-attributes · ELBv2 API TargetGroupAttribute.
gRPC: grpc.io/blog/grpc-load-balancing (2017-06-15) · grpc doc/load-balancing.md · gRFC A9.
HAProxy 3.2 configuration manual · nginx.org upstream module · github.com/RJ/ketama.
Kubernetes v1.37: virtual-ips · topology-aware-routing · service · create-external-load-balancer · blog 2018-11-07 · v1.33 blog (2025-04-23) · v1.34 blog (2025-08-27).
Write-ups: research.google/blog consistent-hashing-with-bounded-loads (2017-04-03) · brooker.co.za two-random (2012-01-17) + erlang (2020-08-06) · blog.cloudflare.com a-brief-anycast-primer (2011-10-21) · GCP load-balancing overview.

## Uncertain / could not verify (excluded from the Concept)

- Netflix edge-LB post (Medium 403): choice-of-2 + utilization confirmed via snippets only; probation/load-banding NOT verified.
- Vimeo post 403; ~8× figure from the Google blog.
- Little 1961 paywalled; L = λW via concurrency-limits README.
- IPVS default scheduler unstated in the fetched config API.
- Topology Aware Routing beta-banner vs GA-blog tension.
- Istio's concrete default rests on 1.14 change notes ("appropriate default" in docs).
- No GCP first-party MAX_CONNECTION_AGE guidance found.
- Azar 1994 / Mitzenmacher thesis not fetched.
- Cloudflare DNS-RR learning page 403.
- HAProxy default balance algorithm when omitted: unasserted.
- Maglev §3.4 internals via summarizer; page-1 facts directly read.
- ALB anomaly *mitigation* default off per API reference (console wording differs).
