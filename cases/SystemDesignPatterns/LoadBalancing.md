---
type: reference
title: 'Load balancing techniques'
description: 'Place each request or connection on one host from a live set: L4 vs L7, algorithm family, the gRPC/HTTP/2 pinning trap, consistent hashing with virtual nodes, panic/fail-open, and outlier ejection as C1 on the LB path. Complements health checks; a gateway in front does not fix an L4 hop behind it.'
tags: [system-design-patterns, availability, load-balancing, consistent-hashing]
---

# Load balancing techniques

**See also:** [failover and health checks](Failover.md) · [API gateway](ApiGateway.md) · [WebSockets](WebSockets.md) · [request routing (DDIA)](../data-intensive-design/request-routing.md) · [circuit breaker](CircuitBreaker.md) · [retry, backoff, and retry budgets](RetryBackoff.md) · [catalog research (2026-09-13)](../../docs/research/sysdesign/c5-load-balancing-external-research.md)

Load balancing is **placement**. Once [health checks](Failover.md) have named a live set, pick one host for this *connection*, *request*, or *stream*. Discovery is already owned elsewhere ([REST/RPC dataflow](../data-intensive-design/rest-rpc-dataflow.md)); this note owns the pick. A [gateway](ApiGateway.md) in front is product routing, not a substitute for per-call spreading. Key → shard → node for a partitioned store is [request routing](../data-intensive-design/request-routing.md) (B2): a stateless replica may sit behind any peer; a shard can serve a key only on a replica that owns it.

Quality attributes: **scalability** (spread work), **availability** of the *caller* (route around a bad host without failing the request), and **tail latency** (avoid the unlucky replica). Costs: an extra hop or a fatter client, stale-signal herds, and affinity that fights scale-out.

## Lineage and vocabulary

- **Mitzenmacher (TPDS 2001) / Brooker (2012).** Sampling *d* = 2 hosts and picking the less loaded is an *exponential* improvement over random; *d* = 3 adds only a constant. Brooker’s point: a stale “pick the quietest” **herds** every client onto the last quiet host, which then flips busy/quiet each refresh. That is why Envoy equal-weight least-request, NGINX `random two`, and HAProxy `random()` default to two draws.
- **Karger (STOC 1997) / ketama / Maglev (NSDI 2016).** Consistent hashing: a small membership change must not remap everything (`mod N` does). Virtual nodes (many hashes per host) approximate weight and cut variance; they do **not** cap a hot key. Maglev trades a little more disruption for even fill and O(1) lookup — Envoy: “not as stable as ring hash when upstream hosts change”; simulations ~2× the keys move. Bounded-load CH (Mirrokni et al.; Envoy `hash_balance_factor`, HAProxy `hash-balance-factor`) is the cap.
- **gRPC blog (2017-06-15) and gRFC A9.** L4 copies frames — one connection, one backend. L7 parses HTTP/2 and can spray streams. A9: L4 balancers “do not balance RPCs but instead TCP connections”; `MAX_CONNECTION_AGE` (default **infinite**) plus **±10% jitter** is the server-side way to force reconnect so an L4 hop can rebalance. Client default policy is **`pick_first`** — no spreading until `round_robin` or xDS is selected.
- **Nygard / Azure.** A mesh or LB that already routes around failure is on Azure’s “not suitable” list for an *application* breaker. Outlier + panic *are* C1 on the data path; they do not replace a caller-side fail-fast.

## L4 vs L7

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

**NLB (L4).** TCP hash = protocol + src IP/port + dst IP/port **+ TCP sequence number**; each TCP connection is pinned for life. UDP is 5-tuple. QUIC uses Server ID in the Connection ID. **ALB (L7)** picks per request; stickiness, if on, **bypasses** the algorithm after the first pick.

Use L4 for TLS passthrough, millions of short TCP flows, protocol-agnostic front doors, QUIC CID pinning. Use L7 for gRPC or any HTTP/2 multiplex, content-based routing, cookie affinity, per-request outlier. Putting NLB (or kube-proxy) in front of a long-lived gRPC channel is the trap below. The **coarsest** hop that still multiplexes HTTP/2 wins the imbalance: a gateway in front does not fix an L4 hop behind it.

## Algorithms

| Algorithm | Pick | Herd risk | Use when |
|---|---|---|---|
| **Weighted RR** | Next in rotation; weight-*w* appears *w* times | Low if work is short and homogeneous | Default of NGINX, Envoy `lb_policy`, HAProxy, ALB |
| **Least-conn** | Fewest *connections* (HAProxy also counts queued) | High if the load signal is stale (Brooker) | Long sessions: LDAP/SQL — HAProxy says **not** short HTTP |
| **Least-request / LOR / P2C** | Fewest *in-flight requests*; equal weights → O(1) P2C | Low at *d* = 2 | Heterogeneous RPC duration; Istio’s preferred default since 1.14 |
| **Random / random(2)** | Uniform, or P2C on draws | Low | Membership churn; HAProxy: avoids RR/leastconn hammering |
| **Ring hash** | Hash(key) → clockwise host | N/A (key, not load) | Cache affinity, *soft* “same user → same pod” |
| **Maglev** | Hash(key) → fixed prime table | Same | Same job, faster rebuild; accept more remap on change |
| **Peak EWMA** | P2C on peak-EWMA RTT × (inflight+1) | Low; **fast-fail looks “fast”** | Latency-aware among *already-healthy* hosts (Envoy contrib) |
| **Sticky / affinity** | Freeze the first pick | N/A — it *is* the constraint | Unshareable per-process state; not an algorithm |

Envoy least-request (1.40.0-dev): equal weights use `choice_count` default **2**. Unequal weights: `weight = load_balancing_weight / (active_requests + 1)^active_request_bias`; bias default **1.0**; **0.0** degenerates to RR. Peak EWMA is contrib/`v3alpha` and “does not handle unhealthy hosts or error responses” — a host that **fast-fails** looks cheap and attracts *more* traffic. Pair it with C3 health and C1 outlier **before** it sees the set.

Weights: NGINX `weight` default **1**. HAProxy `roundrobin` is dynamic (weights change live; **4095** active servers/backend). Envoy locality overprovisioning default **1.4**: effective weight does not decay until locality health drops below **~71%**.

## Consistent hashing and virtual nodes

A hash of *N* hosts without virtual nodes remaps nearly everything on +1/−1. Ketama puts each host on the ring many times; add/remove moves ~1/*N* of keys *if* the ring is large enough that hashes are not clumped.

| Implementation | Knob | Default |
|---|---|---|
| Envoy RING_HASH | `minimum_ring_size` / `maximum_ring_size` | **1024** / **8 M** (XX_HASH) |
| Envoy MAGLEV | `table_size` (must be prime) | **65537** (≤ **5 000 011**) |
| Istio ring / Maglev | `minimumRingSize` / `tableSize` | **1024** / **65537** |
| NGINX `hash key consistent` | ketama; `ketama_points` | **160** |
| NGINX `hash key` (no `consistent`) | Cache::Memcached-style | **most keys remap** |

If hosts exceed the Maglev table, some hosts get **0** entries. Envoy `hash_balance_factor` (ring **and** Maglev) is unset = **unbounded**; typical **120–200**, min **100**; example **150** ⇒ no host > 1.5× average; overflow is a random jump, O(*N*). HAProxy `hash-balance-factor` default **0 (disabled)**; recommended **125–200**.

Hashing balances *keys*, not *bytes*. Virtual nodes cut variance; they do not cap one viral `user_id`. Bounded-load CH or a separate shed is the fix. The map of that key onto a shard is **B2**.

## The gRPC / HTTP/2 pinning trap

gRPC balances **per call**, not per connection. HTTP/2 multiplexes many streams on one TCP connection. An L4 hop (NLB, kube-proxy iptables/IPVS, HAProxy `mode tcp`) sees **one** flow and parks every RPC on one pod. Kubernetes (Morgan / Buoyant, 2018): kube-proxy is connection-level — “no new connections = no opportunity for load balancing.” HTTP/1.1 naturally cycles connections; HTTP/2 does not.

**Client policies.** No service-config policy → **`pick_first`**: all RPCs go to the first READY address. `round_robin` walks READY subchannels per RPC. `grpclb` is deprecated in favor of xDS. Staging with one address hides `pick_first`.

**Rebalancing knobs.** A9: `MAX_CONNECTION_IDLE` / `MAX_CONNECTION_AGE` / `MAX_CONNECTION_AGE_GRACE` default **infinite**; age jitter **±10%**; server keepalive **2 h** / **20 s**. Envoy `max_connection_duration` and `max_requests_per_connection` unset = **unlimited**. Istio `maxRequestsPerConnection` **0**. A stream **cannot** be rebalanced once started; hitting `MAX_CONCURRENT_STREAMS` queues RPCs on that connection.

Fixes: L7 proxy or mesh; headless Service + client `round_robin`; and if any L4 hop remains, set `MAX_CONNECTION_AGE` (minutes, not infinite) with the mandated jitter. Signature after a rolling deploy: *old pods hot, new pods idle*.

## Session affinity

Sticky is **not** an algorithm. It freezes the first pick.

| Mechanism | Key | Default |
|---|---|---|
| ALB duration cookie | `AWSALB`; duration **86400 s** (1 s–7 d) | `stickiness.enabled` **false** |
| NLB | `source_ip` only; not for QUIC | off |
| NGINX `ip_hash` | First **three IPv4 octets** or whole IPv6 | — |
| HAProxy cookie / `stick-table` / `source` | Client IP or app key | algorithm is `roundrobin` if unset |
| Envoy stateful-session | Cookie or header host pin | `strict: false` fallback vs `strict: true` **503** |
| K8s `sessionAffinity: ClientIP` | Client IP; timeout **10800 s** | `None` |

ALB `weighted_random` **cannot** combine with stickiness or slow start; `least_outstanding_requests` **cannot** combine with slow start. After scale-out, cookies keep load on the *old* targets until expiry. WebSocket: the TCP connection *is* the affinity — [A3](WebSockets.md) owns heartbeats and resume; do not treat WS sticky as a general HTTP design. Prefer a shared session store (A3 backplane) or an [idempotency key](Idempotency.md) over process-local stickiness.

## Panic, fail-open, and outlier as C1

Two different C1 placements share a data path:

```
caller ──► (optional app breaker: fail-fast) ──► LB pick among *eligible* hosts
                 ▲                                      │
                 │                                      ▼
            C1 library                         C1 outlier: eject host
            ([Circuit breaker](CircuitBreaker.md))      from the set; still pick
                                               │
                                               ▼
                                    panic / fail-open: set too small
                                    → all hosts  or  503 no upstream
```

**Outlier** (Envoy 1.40.0-dev) is passive, per sidecar, per host — the mesh row in the [breaker](CircuitBreaker.md) placement table. Defaults: `consecutive_5xx` **5** (enforced **100%**), `consecutive_gateway_failure` **5** (enforced **0%** — off), `interval` **10 s**, `base_ejection_time` **30 s**, `max_ejection_time` **300 s**, `max_ejection_percent` **10%**. Ejection time = base × consecutive ejections, capped. A passing **active** health check unejects by default (`successful_active_health_check_uneject_host` **true**) — C3 can undo C1 if the probe is not on the data plane. Ejected hosts are skipped **unless panic**. Do not confuse this with Envoy’s *“circuit breaking”* settings, which are concurrency limits.

**Panic** (Envoy). `healthy_panic_threshold` default **50%**. Below that, ignore health and balance across **all** hosts, or — if `fail_traffic_on_panic` — **no** hosts (503). Set threshold **0%** to disable panic (empty healthy set → 503). Zone-aware requires **both** clusters out of panic, `min_cluster_size` **6**. Istio `minHealthPercent` **0%** = panic surface **disabled**.

**ALB / NLB fail-open.** If healthy targets < `unhealthy_state_routing.minimum_healthy_targets.count` (default **1**) or below the percentage (default **`off`**), send traffic to all targets, including unhealthy. If *every* registered target is unhealthy, ALB “fails open” and the algorithm still runs on the full set.

NGINX `max_fails` **1** / `fail_timeout` **10 s** and HAProxy `observe` + `error-limit` are passive health — **C3** owns those signals; C5 only consumes the resulting set.

Trade-off of fail-open: a bad deploy that fails every health check still receives production traffic. Trade-off of fail-closed: one shared probe bug 503s the fleet. Panic 50% is Envoy’s compromise; ALB’s default “at least one healthy” fails open only when the set is empty.

## Defaults (verified 2026-09-13)

| Stack | Placement default | Load-bearing knobs |
|---|---|---|
| **Envoy 1.40.0-dev** | `lb_policy` **ROUND_ROBIN**; least-request `choice_count` **2** | Ring 1024/8 M; Maglev 65537; panic **50%**; locality overprovision **1.4**; outlier 5 / 10 s / 30 s / 10%; connection duration **unlimited** |
| **NGINX upstream** | Weighted RR, `weight` **1** | `random two` default method `least_conn`; `max_fails` 1 / `fail_timeout` 10 s (ignored for a single-server group); `slow_start` **0** |
| **HAProxy 3.2** | `roundrobin` if unset | `leastconn` for long sessions; `random()` draws **2**; `hash-balance-factor` **0**; `hash-preserve-affinity` **`always`** |
| **ALB / NLB** | ALB `round_robin`; NLB flow hash | ALB stickiness off, cookie **86400 s**; slow start **0**; drain **300 s**; fail-open count **1**; ATW *detection* on (≥ 3 healthy), *mitigation* **off** (needs `weighted_random`) |
| **gRPC / Istio** | Client **`pick_first`**; Istio `simple` **UNSPECIFIED** (“appropriate default”) | A9 age **infinite**, jitter ±10%; Istio 1.14 changed RR → **LEAST_REQUEST**; warmup `minimumPercent` **10**, `aggression` **1.0** (RR / LEAST_REQUEST only) |

## Observability

| Signal | Why |
|---|---|
| Per-host in-flight / active requests | Least-request input; P2C herd visible as one bar |
| Per-host RPS, p50/p99, 5xx | Peak EWMA vs outlier disagreement |
| `outlier_detection.ejections_active` + reason | C1-on-the-LB; consecutive_5xx vs success-rate |
| `lb_healthy_panic` / panic duration | Fail-open is on |
| Ring `min/max_hashes_per_host`, Maglev `min/max_entries_per_host` | Virtual-node collapse; Maglev hosts with 0 slots |
| Upstream connections vs downstream streams | HTTP/2 pin: many streams, one `upstream_cx` |
| GOAWAY / connection-age histogram | A9 ageing actually firing |
| Sticky share (cookie vs not) | Scale-out skew |

Spread *across* backends is the metric. A widening spread is the imbalance alarm.

## Tuning

| Knob | Too low | Too high | Starting point |
|---|---|---|---|
| Layer (L4 vs L7) | L4 in front of gRPC → one-pod herd | L7 on TLS-passthrough / huge PPS | gRPC/HTTP/2 → L7 or client-side per-call |
| Algorithm | RR on heterogeneous RPC → tail on unlucky hosts | Global-least with stale stats → Brooker herd | **P2C least-request**, `choice_count` **2** |
| Ring / Maglev size | Clumps; Maglev hosts with 0 slots | RAM; slower rebuild | Ring ≥ 1024; Maglev 65537; watch min hashes |
| `hash_balance_factor` | Many probes (Envoy O(*N*)) | Hot key still pins | **~150** if one key can dominate; else leave off |
| Stickiness TTL | Extra setup on every request | Scale-out ignored for days (ALB 86400 s) | **Off** unless the process holds unshareable state |
| Panic threshold | 0% + probe bug = fleet 503 | 50%+ fail-open onto dying hosts | Envoy **50%**; decide fail-open vs 503 before raising `max_ejection_percent` past (100 − panic) |
| `MAX_CONNECTION_AGE` | Reconnect storms | Rolling deploy never sheds survivors | Minutes, **±10% jitter** |
| Slow start | Off + least-request = flood the new replica | Long ramp starves capacity | Istio warmup when JIT/caches matter; ALB slow start is **off** and incompatible with LOR |

## Worked calibration — checkout → payment (8 pods)

Constraints are a **design drill**, not a vendor SLA. Checkout 500 rps, payment 8 pods, ~80 ms p50 / 220 ms p99 capture, same AZ. Payment is gRPC. Idempotency key on `POST /capture`.

| Hop | Choice | Why |
|---|---|---|
| Edge | ALB, `round_robin`, stickiness **off** | Capture is not a session; cookie 86400 s would ignore scale-out. Fail-open stays at default count **1**. Drain **300 s**. |
| Mesh sidecar | Envoy `LEAST_REQUEST`, `choice_count` **2** | Heterogeneous issuer latency; P2C vs herd. Not Peak EWMA (contrib + fast-fail magnet). |
| Panic | **50%**; `fail_traffic_on_panic` **false** | 8 pods: panic only if fewer than 4 healthy. Prefer spray over 503 while four pods can still capture. |
| Outlier (C1 here) | consecutive_5xx **5**, interval **10 s**, base **30 s**, max eject **10%** | Isolate one pod. The app-level [breaker](CircuitBreaker.md) on checkout stays for *payment-as-a-dependency* fail-fast. |
| gRPC client | service config **`round_robin`**, not `pick_first` | Default pick_first + one channel = one pod. |
| L4 (if NLB exists) | `MAX_CONNECTION_AGE` **900 s** (±10% → 810–990 s) | Without age, a rolling deploy never moves the multiplexed channel. |
| Cache of payment methods | Maglev **65537**, hash `user_id`, `hash_balance_factor` **150** | Soft affinity; cap the celebrity-user hot key. Not sticky cookies. |
| Warmup | Istio warmup 30 s, `minimumPercent` 10, `aggression` 1.0 | Least-request otherwise slams a cold pod. |

Inequality: 10% eject + panic 50% ⇒ isolate one bad pod without fail-open. If a zone loses 5/8 pods, panic sprays the remaining (and the sick) — deliberate fail-open, not a C3 bug. Do **not** sticky the capture; do **not** put NLB-only in front of a single gRPC channel. [Retries](RetryBackoff.md) re-enter the picker; keep the retry budget *above* a new pick.

## Testing and operating

- **Rolling deploy.** The trap’s signature is old pods hot, new pods idle. Assert connection-age histograms move and that new replicas take traffic within `MAX_CONNECTION_AGE` (plus warmup).
- **Kill one pod’s data plane, leave the probe green.** Outlier should eject; if active HC unejects it, the probe is lying — that is a C3 bug C5 will amplify.
- **Fail every health check.** Confirm the intended fail-open (ALB count 1, Envoy 50%) or fail-closed (`fail_traffic_on_panic`) actually fires, and that it pages. Untested panic is the 2001 fallback story on the LB path.
- **`pick_first` audit.** A staging cluster with one address will not show it. Force two READY backends and watch whether all RPCs pin.

## Failure modes

1. **HTTP/2 / gRPC behind L4.** One channel, one backend. Symptom: one pod at 100% CPU. Fix: L7 or client `round_robin` + connection age.
2. **`pick_first` left on.** Official default. Looks fine in staging with one address.
3. **Stale least-loaded (Brooker herd).** Central “pick the quietest” with a cached load vector. Use P2C.
4. **Peak EWMA without outlier.** Fast 500s look like 3 ms RTT; traffic *increases*.
5. **Hot key under CH.** Virtual nodes do not cap; HAProxy factor defaults to 0.
6. **Maglev table < host count.** Some hosts get zero slots.
7. **Sticky after scale-out.** ALB 1-day cookie; NGINX `ip_hash` /24 buckets whole offices onto one pod.
8. **Panic fail-open of a bad deploy.** Every target 5xx, ALB still hashes onto them. Envoy 50% opens earlier.
9. **Panic fail-closed of a probe bug.** Threshold 0% + C3 false-unhealthy → 503. C3 owns the probe; C5 owns this interaction.
10. **`max_ejection_percent` + panic.** Eject 10%, then panic and put them *back*. Isolation was theatre.
11. **Active HC unejects a data-plane-dead host.** Default uneject-on-active-HC is **true**.
12. **Slow-start off + least-request.** New replica has 0 in-flight → flood.
13. **`MAX_CONNECTION_AGE` without jitter.** A9 exists so you do not recreate the herd on a timer.
14. **RR on long heterogeneous RPCs.** The inverse of HAProxy’s “leastconn is for LDAP, not short HTTP.”
15. **One hash / one breaker over shards.** Brooker / Azure *resource differentiation*; B2 owns the map.

**When not to use an L7 LB.** TLS passthrough; protocols the proxy cannot parse; pps where the parse is the budget. **When not to use sticky.** A shared session store exists; the verb is not session-scoped; you are about to autoscale. **When not to use CH.** No cache locality — P2C is simpler and load-aware. **When not to use fail-open.** Failure is all-or-nothing (bad config, expired certs); then `fail_traffic_on_panic` / raise the ALB count. **When not to use outlier-as-C1 alone.** You need a *caller* fallback (queue, cached price) — ejection still sends the request somewhere; the app breaker fails fast.

## Trade-offs

| Buy | Pay |
|---|---|
| Horizontal scale; route around a bad host without failing the caller | Extra hop (proxy) or a fatter client (client-side) |
| P2C: near-optimal spreading with two samples | Live-load signals invite herding when used as global-least |
| Hash affinity: cache locality, session warmth | Hot keys, remap-on-change, stickiness vs elasticity |
| L7: per-request balancing, HTTP/2-correct | Protocol parse cost; TLS termination placement |
| Outlier + panic: C1 on the LB without a caller fallback | Fail-open onto a bad deploy; fail-closed on a probe bug; ejection is not fail-fast |

Health checks decide **who is eligible**. This pattern decides **who gets the next request**. The [breaker](CircuitBreaker.md) is fail-fast at the caller; outlier is fail-*over* at the LB. [Retries](RetryBackoff.md) re-enter the picker. What happens when capacity is simply insufficient is [load shedding](LoadShedding.md).

## Sources

Verified 2026-09-13; the full URL list, per-claim provenance, and items deliberately left out are in the [catalog research](../../docs/research/sysdesign/c5-load-balancing-external-research.md). First-pass Maglev paper internals, K8s topology-aware serving, DNS/anycast, and Brooker M/M/c pool math stay in [load-balancing-external-research.md](../../docs/research/sysdesign/load-balancing-external-research.md). Breaker/outlier cross-claims are in the [circuit-breaker research](../../docs/research/sysdesign/circuit-breaker-external-research.md).

- Canon: Mitzenmacher TPDS 2001; Brooker, *two random* (2012-01-17); Karger et al. STOC 1997; Maglev NSDI 2016; bounded-load CH arXiv:1608.01350; grpc.io LB blog (2017-06-15), `doc/load-balancing.md`, gRFC A9; Kubernetes *gRPC load balancing without tears* (2018-11-07); Nygard / Azure / Fowler via the breaker note.
- Infrastructure: Envoy 1.40.0-dev LB / panic / outlier / zone-aware / locality-weight / Peak EWMA (contrib v3alpha); NGINX `ngx_http_upstream_module`; HAProxy 3.2 `balance`; Istio DestinationRule + 1.14 change notes (RR → LEAST_REQUEST); AWS ALB/NLB target-group attributes (flow hash + TCP sequence; `AWSALB`; fail-open count 1).
- Adjacent: [rest-rpc-dataflow.md](../data-intensive-design/rest-rpc-dataflow.md) (discover, then balance); [request-routing.md](../data-intensive-design/request-routing.md) (key → shard); [CircuitBreaker.md](CircuitBreaker.md) (outlier vs concurrency limits vs app fail-fast).
