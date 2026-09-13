---
type: research
title: 'Load balancing techniques — external research (2026-09-13)'
description: >-
  Group C catalog evidence pass for C5: L4 vs L7, algorithms (RR, least-conn,
  Maglev/ring-hash, EWMA/P2C, weighted), session affinity, the HTTP/2
  connection-level trap, consistent hashing + virtual nodes, panic/fail-open,
  and outlier ejection as placement of C1 — Envoy/NGINX/HAProxy/ALB/NLB/gRPC
  defaults with versions and fetch dates.
tags: [research, system-design-patterns, C5, load-balancing]
---

# C5 Load balancing techniques — catalog research (2026-09-13)

> **What this is.** The catalog evidence pass for **C5**. It **links** the same-day first pass [load-balancing-external-research.md](load-balancing-external-research.md) (algorithm canon, Maglev paper, K8s topology-aware serving, DNS/anycast, Brooker M/M/c pool math) and **deepens** it to the Group C / [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md) bar: mechanics and variants, knobs with verified defaults, observability, tuning, a worked calibration, failure modes, sources. Discovery-then-balance is already named in [rest-rpc-dataflow.md](../../../cases/data-intensive-design/rest-rpc-dataflow.md); this note owns *how* a request is placed once the live set is known.
>
> **Method.** Primary pages fetched 2026-09-13. Numbers and option names reproduced exactly; everything else paraphrased. Facts marked **[→C5-1]** are in the first-pass note and not re-fetched here. Facts marked **[→breaker]** are in [circuit-breaker-external-research.md](circuit-breaker-external-research.md). Unverifiable items are in §10 and are **not** asserted as fact.

---

## 1. Scope and non-goals

**Owns.** L4 (connection / flow) vs L7 (request / stream) placement; the algorithm family (weighted RR, least-conn / least-request, Maglev vs ketama ring-hash, P2C, Peak EWMA, weighted); session affinity / sticky as an *override* of the algorithm; the gRPC/HTTP/2 trap (one connection, many streams — connection-level LB pins the herd); consistent hashing plus virtual nodes / table size; panic threshold and fail-open (when the healthy set is too small, spray or 503); outlier ejection as the **placement of C1** on the LB path (eject a host, do not fail-fast the caller). Verified Envoy / NGINX / HAProxy / ALB / NLB / gRPC defaults with versions or fetch dates.

**Does not own.** Active/passive probes and the healthy/unhealthy counters that *feed* the live set (**C3**). API gateway / BFF composition, auth, and edge product policy (**C6**). WebSocket sticky as a *protocol* concern — connections are inherently sticky; A3 owns resume vs reconnect (**A3**, cross-link only). Key → shard → node routing for a partitioned store (**B2** / [request-routing.md](../../../cases/data-intensive-design/request-routing.md)): a stateless app instance may sit behind any replica; a shard can serve a key only on a replica that owns it.

**Does not re-derive.** [rest-rpc-dataflow.md](../../../cases/data-intensive-design/rest-rpc-dataflow.md) (hardware LB / software LB / DNS / registry / mesh — “discover, balance, then version”). [hash-sharding.md](../../../cases/data-intensive-design/hash-sharding.md) (partition keys, not request placement). First-pass K8s `trafficDistribution` / topology-mode, Cloudflare anycast, Brooker M/M/c pool-size math **[→C5-1]**.

---

## 2. Lineage / vocabulary

| Term | Meaning | Named source |
|---|---|---|
| **L4 / connection LB** | Terminate TCP (or copy bytes) and pin the *connection* to one backend for its life. | gRPC LB blog 2017-06-15; NLB introduction |
| **L7 / request LB** | Parse HTTP/2 (or HTTP/1.1) and pick a backend *per stream / request*. | Same gRPC blog: “LB can distribute the streams from one client among multiple backends” |
| **Weighted RR** | Walk the set; a weight-*w* host appears *w* times in the rotation. | NGINX default; Envoy `ROUND_ROBIN` (DEFAULT); HAProxy `roundrobin` |
| **Least-conn / least-request** | Prefer the host with fewest in-flight connections or requests. | NGINX `least_conn`; HAProxy `leastconn`; Envoy `LEAST_REQUEST`; ALB `least_outstanding_requests` |
| **P2C** | Sample *d* random healthy hosts (default *d* = 2); pick the least loaded. | Mitzenmacher (via Envoy + Brooker 2012-01-17); HAProxy `random(<draws>)` default **2** |
| **Peak EWMA** | P2C on `Cost = RTT_peak_ewma × (active_requests + 1)`. | Envoy contrib `peak_ewma` (1.40.0-dev) |
| **Ring hash (ketama)** | Hash hosts onto a circle many times (virtual nodes); request hash → clockwise next. | Envoy RING_HASH; NGINX `hash … consistent`; Karger STOC 1997 **[→C5-1]** |
| **Maglev** | Fixed prime lookup table; faster build/lookup, more disruption on membership change than ring hash. | Maglev NSDI 2016 **[→C5-1]**; Envoy `table_size` **65537** |
| **Bounded-load CH** | Cap a host at *c* × average load; overflow walks / jumps. | arXiv:1608.01350 (Envoy cites it); HAProxy `hash-balance-factor` |
| **Sticky / affinity** | After the first pick, later requests of a session skip the algorithm. | ALB `AWSALB` cookie; NGINX `ip_hash` / `sticky`; Envoy stateful-session filter |
| **Panic / fail-open** | When healthy share (or count) is too low, ignore health and spray — or fail all. | Envoy `healthy_panic_threshold` **50%**; ALB/NLB routing failover |
| **Outlier ejection** | Passive host-level C1: remove one unlike host from the *LB set*. Caller still gets a pick. | Envoy outlier proto; CircuitBreaker.md placement table |

**Mitzenmacher / Brooker (P2C vs herd).** Brooker 2012-01-17 (fetched 2026-09-13): stale “pick the least loaded” **herds** every client onto the last quiet host; the host flips busy/quiet on each refresh. Best-of-2 “rejects herd behavior much more strongly” than best-of-all *and* than random — that is why Envoy equal-weight least-request, NGINX `random two`, and HAProxy `random()` default to two draws. Mitzenmacher (IEEE TPDS 2001, cited by Envoy and HAProxy, PDF **[→C5-1]**): *d* = 2 is an exponential improvement over *d* = 1; *d* = 3 is only a constant-factor gain over *d* = 2.

**Karger / ketama / Maglev.** Consistent hashing: a small membership change does not induce a total remap (vs `mod N`). Virtual nodes (many hashes per host) approximate weight and cut variance; they do **not** cap a hot key. Maglev (Google software LB since 2008 **[→C5-1]**) trades a little more disruption for even fill and O(1) lookup; Envoy: Maglev “not as stable as ring hash when upstream hosts change”; simulations ~2× the keys move. Bounded-load CH (Mirrokni et al.; Envoy `hash_balance_factor`, HAProxy `hash-balance-factor`) is the cap.

**gRPC 2017-06-15 + gRFC A9 (2017-01-27, Implemented).** Proxy vs thick-client vs lookaside. L3/L4 copies frames — **one connection, one backend**. L7 parses HTTP/2 and can spray streams. A9: L4 LBs “do not balance RPCs but instead TCP connections”; `MAX_CONNECTION_AGE` (default **infinite**) + **±10% jitter** is the server-side way to force reconnect so an L4 hop can rebalance. Client default LB policy is **`pick_first`** (grpc `doc/load-balancing.md`, fetched 2026-09-13) — no spreading until `round_robin` or xDS is selected.

**Nygard / Azure.** A mesh or LB that already routes around failure is on Azure’s “not suitable” list for an *application* breaker **[→breaker §1]** — that is this note’s placement claim: outlier + panic *are* C1 on the data path; they do not replace a caller-side fail-fast.

---

## 3. Mechanics

### 3.1 L4 vs L7

```
L4  client ──TCP──► LB ──TCP──► one backend for the life of the connection
L7  client ──H2──► LB parses streams ──► backend A / B / C per stream
```

| | **L4** | **L7** |
|---|---|---|
| Unit of placement | 5-tuple (or QUIC CID) | HTTP request or HTTP/2 stream |
| Cost | Cheap; no app parse | Terminates / re-encodes; sees cookies, headers, gRPC |
| Affinity | Free (the connection *is* the session) | Must be configured (cookie, header, hash) |
| Failure | RST / connect-fail; health from C3 | Per-request 5xx, timeout, outlier |
| Trap | HTTP/2 multiplex pins all RPCs | Extra hop + CPU |

**NLB (L4, fetched 2026-09-13).** TCP hash = protocol + src IP/port + dst IP/port **+ TCP sequence number**; “each individual TCP connection is routed to a single target for the life of the connection.” UDP is 5-tuple. QUIC uses Server ID in the Connection ID; initial packets without a Server ID use 5-tuple. Cross-zone default: each node stays in its AZ unless enabled. Clients that ignore DNS TTL keep hitting withdrawn AZ IPs.

**ALB (L7).** Algorithms below. Stickiness, if on, **bypasses** the algorithm after the first pick. HTTP/2→1.1 conversions are counted separately under `least_outstanding_requests`.

**When L4 is the right tool.** TLS passthrough, millions of new short TCP flows, protocol-agnostic front doors, QUIC CID pinning. **When L7 is required.** gRPC or any HTTP/2 multiplex; content-based routing; cookie affinity; per-request outlier. Putting NLB (or kube-proxy) in front of a long-lived gRPC channel is the trap in §3.4.

### 3.2 Algorithms

| Algorithm | Pick | Herd risk | Use when |
|---|---|---|---|
| **Weighted RR** | Next in rotation, weights honored | Low if work is homogeneous and short | Default of NGINX, Envoy `lb_policy`, HAProxy, ALB |
| **Least-conn** | Fewest *connections* (HAProxy also counts queued) | High if load signal is stale (Brooker) | Long sessions: LDAP/SQL — HAProxy says **not** short HTTP |
| **Least-request / LOR / P2C** | Fewest *in-flight requests*; equal weights → O(1) P2C | Low at *d* = 2 | Heterogeneous RPC duration; Istio’s preferred default |
| **Random / random(2)** | Uniform, or P2C on draws | Low | Membership churn; HAProxy: avoids RR/leastconn hammering |
| **Ring hash** | Hash(key) → clockwise host | N/A (key, not load) | Cache affinity, “same user → same pod” *soft* stickiness |
| **Maglev** | Hash(key) → fixed prime table | Same | Same job, faster rebuild; accept more remap on change |
| **Peak EWMA** | P2C on peak-EWMA RTT × (inflight+1) | Low; **fast-fail looks “fast”** | Latency-aware among *already-healthy* hosts (contrib) |
| **Client-side WRR (ORCA)** | Weight from upstream QPS / utilization | Needs fresh ORCA | Single-locality child of `WrrLocality` (Envoy) |

**Envoy least-request (1.40.0-dev proto).** Equal weights: `choice_count` default **2** (P2C). Unequal weights: `weight = load_balancing_weight / (active_requests + 1)^active_request_bias`; `active_request_bias` default **1.0**; **0.0** degenerates to RR. Slow start off unless `SlowStartConfig` is set.

**Envoy Peak EWMA (contrib, `v3alpha`, fetched 2026-09-13).** `decay_time` **10 s**, `aggregation_interval` **100 ms**, `max_samples_per_host` **1000**, `default_rtt` **10 ms**, `penalty_value` **1e6**. Requires the `envoy.filters.http.peak_ewma` HTTP filter or there is no RTT. Docs: it “does not handle unhealthy hosts or error responses”; a host that **fast-fails** looks cheap and attracts *more* traffic. Pair with C3 health checks and C1 outlier **before** Peak EWMA sees the set. Must be compiled into a contrib build.

**Weights.** NGINX `weight` default **1**; example 5-1-1 → 5 of every 7 requests. HAProxy `roundrobin` is dynamic (weights change live; **4095** active servers/backend cap); `static-rr` is not. Envoy locality overprovisioning factor default **1.4**: `availability = 140 × available / total`; effective weight does not decay until locality health drops below **~71%** (table: 70% still full share, 69% starts to spill).

### 3.3 Consistent hashing and virtual nodes

A hash of *N* hosts without virtual nodes remaps nearly everything on +1/−1. Ketama puts each host on the ring many times; add/remove moves ~1/*N* of keys *if* the ring is large enough that hashes are not clumped.

| Implementation | Virtual-node / table knob | Default | Bound |
|---|---|---|---|
| Envoy RING_HASH | `minimum_ring_size` / `maximum_ring_size` | **1024** / **8 M** | 8 M; hash **XX_HASH** |
| Envoy MAGLEV | `table_size` (must be prime) | **65537** | ≤ **5 000 011** |
| Istio `consistentHash.ringHash` | `minimumRingSize` | **1024** | — |
| Istio Maglev | `tableSize` | **65537** | prime **< 5 000 011** |
| NGINX `hash key consistent` | ketama; compatible with Cache::Memcached::Fast `ketama_points` **160** | (implicit) | — |
| NGINX `hash key` (no `consistent`) | Cache::Memcached-style; **most keys remap** on membership change | — | — |

Envoy: “multiply the number of hashes per host — for example 100 vs 200 — to better approximate the desired distribution”; watch `min_hashes_per_host` / `max_hashes_per_host` (ring) or `min_entries_per_host` / `max_entries_per_host` (Maglev). If hosts > Maglev table size, some hosts get **0** entries.

**Bounded load.** Envoy `CommonLbConfig.hash_balance_factor` (ring **and** Maglev): unset = **unbounded**; typical **120–200**; min **100**; example **150** ⇒ no host > 1.5× average; overflow is a **random jump** (arXiv:1908.08762), O(*N*). HAProxy `hash-balance-factor` default **0 (disabled)**; 150 = 1.5×; recommended **125–200**; also honored by `balance random`. HAProxy 3.2 `hash-preserve-affinity`: default **`always`** (hash even if saturated); `maxconn` / `maxqueue` skip a full server.

**Hot key.** Hashing balances *keys*, not *bytes*. Virtual nodes cut variance; they do not cap one viral `user_id`. Bounded-load CH or a separate shed is the fix. Shard routing of that key is **B2**.

### 3.4 gRPC / HTTP/2 — connection-level LB is a trap

gRPC `doc/load-balancing.md`: “Load-balancing within gRPC happens on a **per-call** basis, not a per-connection basis.” HTTP/2 multiplexes many streams on one TCP connection. An L4 hop (NLB, kube-proxy iptables/IPVS, HAProxy `mode tcp`) sees **one** flow and parks every RPC on one pod.

Kubernetes blog 2018-11-07 (Morgan / Buoyant): kube-proxy is connection-level — “no new connections = no opportunity for load balancing.” HTTP/1.1 naturally cycles connections (one request in flight per conn, idle expiry); HTTP/2 does not. Fixes named there: headless Service + client LB, or an L7 proxy/mesh.

**Client policies (grpc `load-balancing.md`).** No service-config policy → **`pick_first`**: try addresses in order; all RPCs go to the first READY address; on break → IDLE until the app pokes it. `round_robin` walks READY subchannels per RPC. `grpclb` is **deprecated** in favor of xDS.

**Rebalancing knobs.** A9: `MAX_CONNECTION_IDLE` / `MAX_CONNECTION_AGE` / `MAX_CONNECTION_AGE_GRACE` default **infinite**; `KEEPALIVE_TIME` **2 hours**, `KEEPALIVE_TIMEOUT` **20 s**; age jitter **±10%**. Envoy `HttpProtocolOptions.max_connection_duration` unset = **no max**; `max_connection_duration_jitter` unset = **no jitter**; `max_requests_per_connection` unset = **unlimited** (`1` disables keepalive; HTTP/2/3 limit is approximate). Istio `maxRequestsPerConnection` **0** **[→breaker]**. gRPC performance guide: a stream **cannot** be load-balanced once started; hitting `MAX_CONCURRENT_STREAMS` queues RPCs on that connection — open more channels (different channel args) or wait for grpc#21386.

### 3.5 Session affinity / sticky

Sticky is **not** an algorithm. It is a *constraint* that freezes the first pick.

| Mechanism | Key | Failover | Default |
|---|---|---|---|
| ALB duration cookie | `AWSALB`; duration **86400 s** (1 s–7 d); cookie object itself expires in **7 d** (non-configurable) | Next pick if target draining/unhealthy | `stickiness.enabled` **false** |
| ALB app cookie | App name + ALB wrapper; same duration default **86400 s** | Same | off |
| NLB | `source_ip` only; **false**; not for QUIC | — | off |
| NGINX `ip_hash` | First **three IPv4 octets** or whole IPv6 | Next server; mark removed servers `down` to keep the map | — |
| NGINX Plus `sticky cookie/route/learn` | Cookie / route / learned | Falls back to the configured algorithm | — |
| HAProxy `source` / cookie / `stick-table` | Client IP or app key | Hash changes when membership changes unless `hash-type consistent` | algorithm is `roundrobin` if unset |
| Envoy stateful-session | Cookie or header host pin | `strict: false` fallback vs `strict: true` **503** **[→C5-1]** | — |
| K8s `sessionAffinity: ClientIP` | Client IP | timeout **10800 s** **[→C5-1]** | `None` |

ALB: `weighted_random` **cannot** combine with stickiness or slow start; `least_outstanding_requests` **cannot** combine with slow start. After scale-out, cookies keep load on the *old* targets until expiry — shorten, or do not sticky POSTs that have an idempotency key.

WebSocket: the TCP connection *is* the affinity. A3 owns heartbeats / resume; this note only forbids treating WS sticky as a general HTTP design.

### 3.6 Panic threshold, fail-open, and outlier as placement of C1

Two different C1 placements share a data path:

```
caller ──► (optional app breaker: fail-fast) ──► LB pick among *eligible* hosts
                 ▲                                      │
                 │                                      ▼
            C1 library                         C1 outlier: eject host
            (C1 Concept)                       from the set; still pick
                                               │
                                               ▼
                                    panic / fail-open: set too small
                                    → all hosts  or  503 no upstream
```

**Outlier (Envoy 1.40.0-dev proto, fetched 2026-09-13).** Passive, per sidecar, per host — the mesh row in CircuitBreaker.md. Defaults: `consecutive_5xx` **5** (enforced **100%**), `consecutive_gateway_failure` **5** (enforced **0%** — off), `interval` **10 s**, `base_ejection_time` **30 s**, `max_ejection_time` **300 s**, `max_ejection_time_jitter` **0 s**, `max_ejection_percent` **10%**, success-rate `minimum_hosts` **5** / `request_volume` **100** / `stdev_factor` **1900** (mean − 1.9σ), failure-percentage threshold **85** enforced **0%**. Ejection time = base × consecutive ejections, capped; a passing active health check **unejects** by default (`successful_active_health_check_uneject_host` **true**) — C3 can undo C1 if the probe is not on the data plane. Ejected hosts are skipped **unless panic**.

**Panic (Envoy).** `healthy_panic_threshold` default **50%** (truncated to 1%). Below that, ignore health and balance across **all** hosts, or — if `fail_traffic_on_panic` — **no** hosts (503). Set threshold **0%** to disable panic (never fail-open; empty healthy set → 503). Zone-aware requires **both** clusters out of panic, `routing_enabled` **100%**, `min_cluster_size` **6**. Priorities: if normalized total availability stays 100%, panic is disregarded and spill goes down-priority; when it drops below 100%, each priority is tested against 50%. Istio `minHealthPercent` **0%** = panic surface **disabled** **[→breaker]**.

**ALB / NLB fail-open (target-group attributes, fetched 2026-09-13).** Routing failover: if healthy targets < `unhealthy_state_routing.minimum_healthy_targets.count` (default **1**) or below the percentage (default **`off`**), “send traffic to all targets, including unhealthy targets.” DNS failover: `dns_failover.minimum_healthy_targets.count` default **1**, percentage **`off`**. Health-check page: if *every* registered target is unhealthy, ALB “fails open” and the algorithm still runs on the full set. NLB: same count/percentage defaults; `target_health_state.unhealthy.connection_termination.enabled` default **true** (cut unhealthy TCP). ALB ATW: anomaly *detection* is on for every ALB (≥ **3** healthy targets; 5xx + connect errors vs peers; `normal` / `anomalous`); anomaly *mitigation* requires `weighted_random` and `load_balancing.algorithm.anomaly_mitigation` default **`off`**.

**NGINX / HAProxy (C3-adjacent, not C1).** NGINX `max_fails` **1**, `fail_timeout` **10 s** (window *and* penalty); ignored for a single-server upstream. HAProxy `observe` + `error-limit` **[→breaker]**. These are passive health, owned as *signals* by C3; C5 only consumes the resulting set.

Trade-off of fail-open: a bad deploy that fails every health check still receives production traffic (the 2001-style fallback **[→breaker]**). Trade-off of fail-closed: one shared probe bug 503s the fleet. Panic 50% is Envoy’s compromise; ALB’s default “at least one healthy” is the opposite extreme (fail-open only when the set is empty).

---

## 4. Verified defaults / standards (fetched 2026-09-13)

### 4.1 Envoy 1.40.0-dev

| Knob | Default | Notes |
|---|---|---|
| `lb_policy` | **ROUND_ROBIN** | `LEAST_REQUEST` / `RING_HASH` / `MAGLEV` / `RANDOM` |
| Least-request `choice_count` | **2** | P2C when weights equal |
| `active_request_bias` | **1.0** | 0.0 = RR |
| Ring `minimum_ring_size` / `maximum_ring_size` | **1024** / **8 M** | XX_HASH |
| Maglev `table_size` | **65537** | prime, ≤ 5 000 011 |
| `hash_balance_factor` | unset = **off** | 120–200 typical |
| `healthy_panic_threshold` | **50%** | 0% disables; `fail_traffic_on_panic` → 503 |
| Zone-aware `routing_enabled` / `min_cluster_size` | **100%** / **6** | Both clusters must be out of panic |
| Locality overprovision | **1.4** | Spill starts ~71% healthy |
| Outlier (see §3.6) | 5 / 10 s / 30 s / 10% | Gateway-failure enforcement **0%** |
| `max_connection_duration` | **unset** (unlimited) | Jitter unset = 0 |
| `max_requests_per_connection` | **unset** (unlimited) | `1` = no keepalive |
| Peak EWMA | contrib / v3alpha | Needs HTTP filter; see §3.2 |

### 4.2 NGINX `ngx_http_upstream_module`

Default method **weighted round-robin**; `weight` **1**. `least_conn` (weight-aware; ties by WRR). `least_time` (Plus). `random [two [method]]` — `two` default method **`least_conn`**. `ip_hash` as above. `hash key [consistent]` — without `consistent`, remaps most keys; with it, ketama / `ketama_points` **160**. `max_fails` **1**, `fail_timeout` **10 s**, `slow_start` **0** (incompatible with hash / ip_hash / random). Single-server group: max_fails / fail_timeout / slow_start **ignored**.

### 4.3 HAProxy 3.2 configuration manual

“The load balancing algorithm of a backend is set to **roundrobin** when no other algorithm, mode nor option have been set.” `leastconn`: lowest connections **plus queued**; recommended for long sessions, “not very well suited” for short HTTP. `random()` draws default **2** (P2C; cites Mitzenmacher handbook PDF). `hash-balance-factor` default **0**; `hash-preserve-affinity` default **`always`**. `roundrobin` cap **4095** dynamic servers.

### 4.4 AWS ALB / NLB

| Knob | ALB | NLB |
|---|---|---|
| Placement | L7 request | L4 flow (TCP seq in hash) |
| Algorithm | `round_robin` **default**; `least_outstanding_requests`; `weighted_random` | Flow hash (not configurable as RR/LOR) |
| Stickiness | off; cookie **86400 s**; types `lb_cookie` / `app_cookie` | off; `source_ip` |
| Slow start | **0** (off); 30–900 s if set | — |
| Drain | `deregistration_delay` **300 s** (0–3600) | **300 s**; QUIC always 300 |
| Conn terminate on drain | — | UDP/TCP_UDP new groups **true**; else **false** |
| Fail-open routing | healthy count default **1**; % **off** | same |
| DNS failover | count **1**; % **off** | same |
| ATW mitigation | **off**; needs `weighted_random` | n/a |
| Unhealthy conn kill | — | **true** |

### 4.5 gRPC / Istio

| Knob | Default | Page |
|---|---|---|
| Client LB policy | **`pick_first`** | grpc `doc/load-balancing.md` |
| Spreading | `round_robin` or xDS; `grpclb` deprecated | same |
| `MAX_CONNECTION_AGE` / IDLE / GRACE | **infinite** | gRFC A9 |
| Age jitter | **±10%** | A9 |
| Server keepalive | **2 h** / **20 s** | A9 |
| Istio `LoadBalancerSettings.simple` | **UNSPECIFIED** → “Istio will select an appropriate default” | DestinationRule, fetched 2026-09-13 |
| Istio 1.14 (2022-05-24) | default algorithm **ROUND_ROBIN → LEAST_REQUEST** | change notes; restore via `ENABLE_LEGACY_LB_ALGORITHM_DEFAULT=true` |
| Istio warmup | `minimumPercent` **10**, `aggression` **1.0**; RR / LEAST_REQUEST only | DestinationRule |
| Istio ring / Maglev | 1024 / 65537 | DestinationRule |

---

## 5. Knobs, observability, tuning

### 5.1 Knobs

| Knob | Role | Too low | Too high |
|---|---|---|---|
| Layer (L4 vs L7) | Unit of placement | L4 in front of gRPC → one-pod herd | L7 on TLS-passthrough / huge PPS |
| Algorithm | How the eligible set is walked | RR on heterogeneous RPC → tail on unlucky hosts | Least-loaded with stale stats → Brooker herd |
| `choice_count` / draws | P2C sample size | 1 = random | ≥3 ≈ global-least, herd-prone |
| Ring / Maglev size | Virtual nodes / table | Clumps; Maglev hosts with 0 slots | RAM; slower rebuild |
| `hash_balance_factor` | Cap CH hot spots | Many probes (Envoy O(*N*)) | Hot key still pins |
| Stickiness TTL | Session → host | Extra setup on every request | Scale-out ignored for days (ALB 86400 s) |
| Panic threshold | When to ignore health | 0% + probe bug = fleet 503 | 50%+ fail-open onto dying hosts |
| `max_ejection_percent` | Cap C1 on the LB | One bad host never isolated | Eject until panic, then fail-open anyway |
| `MAX_CONNECTION_AGE` | Force L4 rebalance | Reconnect storms (jitter or not) | Rolling deploy never sheds survivors |
| Slow start | Ramp cold hosts | Off + least-request = flood | Long ramp starves capacity |

**Placement.** Client (`pick_first` vs `round_robin` / xDS) → sidecar (Envoy/Istio algorithm + outlier + panic) → L7 LB (ALB) → L4 LB (NLB). The **coarsest** hop that still multiplexes HTTP/2 wins the imbalance. A gateway (**C6**) in front does not fix an L4 hop behind it.

### 5.2 Observability (feeds D4)

| Signal | Why |
|---|---|
| Per-host in-flight / active requests | Least-request input; P2C herd visible as one bar |
| Per-host RPS, p50/p99, 5xx | ATW “anomalous”; Peak EWMA vs outlier disagreement |
| `outlier_detection.ejections_active` + reason | C1-on-the-LB; consecutive_5xx vs success-rate |
| `lb_healthy_panic` / panic duration | Fail-open is on |
| Ring `min/max_hashes_per_host`, Maglev `min/max_entries_per_host` | Virtual-node collapse |
| Upstream cx / rq vs downstream streams | HTTP/2 pin: many streams, one `upstream_cx` |
| GOAWAY / `max_age` / connection age histogram | A9 ageing actually firing |
| Sticky share (requests with cookie vs without) | Scale-out skew |
| ALB `AnomalyDetectionResult` | ATW detection ≠ mitigation |

### 5.3 Tuning

1. Decide the **unit**: connection (L4) or request/stream (L7). gRPC/HTTP/2 → L7 or client-side per-call.
2. Start **P2C least-request** (Istio 1.14 lesson; Envoy `choice_count` 2). Use RR only when work is short and homogeneous.
3. CH only for *cache/session* keys; set ring ≥ 1024 and watch min hashes; add `hash_balance_factor` ~150 if one key can dominate.
4. Leave stickiness **off** unless the process holds unshareable state; prefer a backplane (A3) or idempotency keys (C1/C2).
5. Keep outlier at Envoy defaults until you have volume; never raise `max_ejection_percent` past (100 − panic) without deciding fail-open vs 503.
6. If any L4 hop remains, set `MAX_CONNECTION_AGE` (minutes, not infinite) with the mandated ±10% jitter; optionally Envoy `max_connection_duration` + jitter.
7. Slow-start new replicas when the algorithm is least-request; ALB slow start is **off** and incompatible with LOR / weighted_random.
8. Revisit after a rolling deploy: the signature of the trap is *old pods hot, new pods idle*.

---

## 6. Worked calibration — checkout → payment (8 pods)

Constraints are a **design drill**, not a vendor SLA. Method: Brooker P2C + Envoy panic/outlier defaults + A9 ageing + ALB fail-open.

Checkout 500 rps, payment 8 pods, ~80 ms p50 / 220 ms p99 capture (same AZ). Payment is gRPC. Idempotency key on `POST /capture` (C1/C2).

| Hop | Choice | Why |
|---|---|---|
| Edge | ALB, `round_robin`, stickiness **off** | Capture is not a session; cookie 86400 s would ignore scale-out. Fail-open stays at default count **1** (only when *zero* healthy — acceptable; a bad-probe fail-open onto 8 dead pods is the remaining risk). Drain **300 s**. |
| Mesh sidecar | Envoy `LEAST_REQUEST`, `choice_count` **2** | Heterogeneous issuer latency; P2C vs herd. Not Peak EWMA (contrib + fast-fail magnet). |
| Panic | **50%** default; `fail_traffic_on_panic` **false** | 8 pods: panic only if fewer than 4 healthy. Prefer spray over 503 while four pods can still capture. |
| Outlier (C1 here) | consecutive_5xx **5**, interval **10 s**, base **30 s**, max eject **10%** | 10% of 8 = 0 → Envoy still ejects **at least** one if `always_eject_one_host` or percent rounds; treat as “one pod” isolation. App-level breaker on checkout stays for *payment-as-a-dependency* fail-fast **[→breaker]**. |
| gRPC client | service config **`round_robin`**, not `pick_first` | Default pick_first + one channel = one pod. |
| L4 (if NLB exists) | `MAX_CONNECTION_AGE` **900 s** (±10% → 810–990 s) | Without age, a rolling deploy never moves the multiplexed channel. Envoy `max_connection_duration` 900 s + jitter if the sidecar owns the conn. |
| Cache of payment methods | Maglev **65537**, hash `user_id`, `hash_balance_factor` **150** | Soft affinity; cap the celebrity-user hot key. Not sticky cookies. |
| Warmup | Istio `warmup.duration` 30 s, `minimumPercent` 10, `aggression` 1.0 | Least-request otherwise slams a cold pod. ALB slow start left **0** (incompatible with LOR if we had switched the ALB). |

Inequality check: 10% eject + panic 50% ⇒ you can isolate one bad pod without fail-open. If a zone loses 5/8 pods, panic sprays the remaining (and the sick) — that is the deliberate fail-open, not a C3 bug. Do **not** sticky the capture; do **not** put NLB-only in front of a single gRPC channel.

---

## 7. Failure modes and when-not-to-use

1. **HTTP/2 / gRPC behind L4.** One channel, one backend. kube-proxy, NLB, HAProxy TCP. Symptom: one pod at 100% CPU. Fix: L7 or client `round_robin` + connection age.
2. **`pick_first` left on.** Official default. Looks “fine” in staging with one address.
3. **Stale least-loaded (Brooker herd).** Central “pick the quietest” with a cached load vector. Use P2C.
4. **Peak EWMA without outlier.** Fast 500s look like 3 ms RTT; traffic *increases*.
5. **Hot key under CH.** Virtual nodes do not cap; disable factor 0 on HAProxy by default.
6. **Maglev table < host count.** Some hosts get zero slots.
7. **Sticky after scale-out.** ALB 1-day cookie; NGINX `ip_hash` /24 buckets whole offices onto one pod.
8. **Panic fail-open of a bad deploy.** Every target 5xx, ALB still hashes onto them (count default 1 → open at zero healthy). Envoy 50% opens earlier.
9. **Panic fail-closed of a probe bug.** Threshold 0% + C3 false-unhealthy → 503. C3 owns the probe; C5 owns this interaction.
10. **`max_ejection_percent` + panic.** Eject 10%, then panic and put them *back*. Isolation was theatre.
11. **Active HC unejects a data-plane-dead host.** Default `successful_active_health_check_uneject_host` true **[→breaker]**.
12. **Slow-start off + least-request.** New replica has 0 in-flight → flood. ALB default slow start **0**; LOR/weighted_random cannot enable it.
13. **`MAX_CONNECTION_AGE` without jitter.** A9 exists so you do not recreate the herd on a timer.
14. **RR on long heterogeneous RPCs.** HAProxy: leastconn is for LDAP/SQL, not short HTTP — the inverse (RR on long RPC) is the other mistake.
15. **One breaker / one hash over shards.** Brooker / Azure resource differentiation **[→breaker]**; B2 owns the map.

**When not to use an L7 LB.** TLS passthrough; protocols the proxy cannot parse; pps where the parse is the budget. **When not to use sticky.** Shared session store exists; the verb is not session-scoped; you are about to autoscale. **When not to use CH.** No cache locality benefit — P2C is simpler and load-aware. **When not to use fail-open.** Failure is all-or-nothing (bad config, expired certs); then `fail_traffic_on_panic` / raise the ALB count. **When not to use outlier-as-C1 alone.** You need a *caller* fallback (queue, cached price) — ejection still sends the request somewhere; the app breaker fails fast **[→breaker]**.

---

## 8. Cross-links

| Id | Why |
|---|---|
| **C1** circuit breaker | Outlier + panic *are* C1 on the LB; app breaker is fail-fast. Do not confuse Envoy “circuit breaking” (concurrency limits) with outlier **[→breaker]** |
| **C2** retry | Retries re-enter the picker; a retry budget sits *above* a new pick |
| **C3** health | Probes populate the eligible set; timeouts/thresholds are not LB algorithms |
| **C6** API gateway / BFF | Edge product routing; not a substitute for per-call gRPC spreading |
| **C7** timeouts | Per-try vs outer; a 504 is an outlier signal |
| **C8** bulkhead | In-flight count *is* least-request’s signal |
| **A3** WebSocket | Inherent connection stickiness vs reconnect affinity — A3 owns the protocol |
| **B2** partition / routing | Key → shard → node; LB among *stateless* replicas is this note |
| First-pass C5 | [load-balancing-external-research.md](load-balancing-external-research.md) — Maglev paper, K8s topology, DNS/anycast, M/M/c |
| Cases | [rest-rpc-dataflow.md](../../../cases/data-intensive-design/rest-rpc-dataflow.md), [request-routing.md](../../../cases/data-intensive-design/request-routing.md), [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md) |

---

## 9. Sources

Fetched 2026-09-13 unless noted.

**Canon.** grpc.io/blog/grpc-load-balancing (2017-06-15) · github.com/grpc/grpc/blob/master/doc/load-balancing.md · github.com/grpc/proposal/blob/master/A9-server-side-conn-mgt.md (2017-01-27) · grpc.io/docs/guides/performance · kubernetes.io/blog/2018/11/07/grpc-load-balancing-on-kubernetes-without-tears · brooker.co.za/blog/2012/01/17/two-random.html · Mitzenmacher TPDS 2001 / Karger STOC 1997 / Maglev NSDI 2016 / arXiv:1608.01350 **[→C5-1]** · Nygard / Azure / Fowler **[→breaker §1]**.

**Envoy 1.40.0-dev.** envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/load_balancers · …/panic_threshold · …/outlier · …/zone_aware · …/locality_weight · …/api-v3/config/cluster/v3/cluster.proto (ROUND_ROBIN DEFAULT; ring 1024/8M; Maglev 65537; panic 50%; choice_count 2; hash_balance_factor) · …/outlier_detection.proto · …/config/core/v3/protocol.proto (`max_connection_duration` unset) · …/config/contrib/load_balancing_policies/peak_ewma/peak_ewma.html (v3alpha).

**NGINX / HAProxy / Istio.** nginx.org/en/docs/http/ngx_http_upstream_module.html · docs.haproxy.org/3.2/configuration.html (`balance` default roundrobin; `hash-balance-factor` 0; `random()` draws 2; `hash-preserve-affinity` always) · istio.io/latest/docs/reference/config/networking/destination-rule · istio.io/latest/news/releases/1.14.x/announcing-1.14/change-notes/ (2022-05-24).

**AWS.** docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html (TCP hash + sequence number) · …/application/load-balancer-target-groups.html · …/application/edit-target-group-attributes.html (ATW; fail-open; `AWSALB`) · …/application/target-group-health-checks.html (all-unhealthy fail-open) · …/network/load-balancer-target-groups.html · docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_TargetGroupAttribute.html.

**Cited forward.** [load-balancing-external-research.md](load-balancing-external-research.md) (ketama Last.fm; Maglev M = 65 537 / 655 373; K8s v1.37 topology / `PreferSameZone`; Envoy STRICT_DNS 5000 ms; Brooker 2020-08-06 M/M/c; Vimeo ~8× via Google blog) · [circuit-breaker-external-research.md](circuit-breaker-external-research.md) §§3–4 (Istio outlier, ALB HC 30 s / 5 s / 5 / 2, Envoy concurrency limits vs outlier).

---

## 10. Uncertain / left out

- Maglev paper §3.4 internals and the 10 Gbps / M = 655 373 evaluation: not re-read this pass **[→C5-1]**.
- Mitzenmacher 2001 PDF equilibrium formula 1/(1−λ): cited via Brooker + Envoy, not re-opened.
- ATW “re-adjusts every 5 s” from the first pass: **not** on the ALB attributes page this fetch — unasserted here.
- Envoy stateful-session `strict` 503: first-pass only **[→C5-1]**.
- K8s `sessionAffinity` timeout 10800 s and topology-mode vs `trafficDistribution` GA tension: first-pass **[→C5-1]**; not re-fetched.
- Istio *current* concrete default when `UNSPECIFIED`: docs still say “appropriate default”; 1.14 change notes say LEAST_REQUEST. No live istiod dump.
- Peak EWMA selection is documented as P2C / O(1); a configurable `choice_count` was **not** on the proto page.
- Envoy `fail_traffic_on_panic` protobuf default is implicit **false** (fail-open); the panic overview describes both modes without restating the bool default.
- NLB target-group-health HTML was thin this fetch; fail-open count/percentage taken from `load-balancer-target-groups.html`.
- HAProxy `error-limit` / `observe` defaults left on the breaker note.
- Linkerd EWMA claims in the 2018 K8s blog are product narrative, not a numeric default.
- grpc#21386 (multi-connection channel) still “plans” on the performance guide; not treated as shipped.
- First-pass Netflix / Vimeo 403s and Azar 1994 remain out **[→C5-1]**.
- Checkout table is a drill. PromQL names above are recommendations, not a vendor schema.
