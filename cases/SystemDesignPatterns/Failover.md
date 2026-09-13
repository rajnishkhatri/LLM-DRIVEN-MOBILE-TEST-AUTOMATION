---
type: reference
title: 'Failover and health checks'
description: 'Detect unhealth and move traffic to a survivor: probe taxonomy from liveness to anomaly detection, verified K8s/Envoy/Route 53 defaults, RTO/RPO and the four DR strategies, DNS TTL and database failover timings, static stability and the data-plane rule, the fail-open/fail-closed matrix, and the GitHub 2018 split-brain post-mortem.'
tags: [system-design-patterns, availability, failover, health-checks, dr]
---

# Failover and health checks

**See also:** [circuit breaker](CircuitBreaker.md) · [load balancing](LoadBalancing.md) · [graceful degradation](GracefulDegradation.md) · [quorums and fencing (DDIA)](../data-intensive-design/quorums-and-fencing.md) · [replication (DDIA)](../data-intensive-design/replication-overview.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/failover-degradation-external-research.md)

Failover is the pattern pair: **detect** that a replica, zone, or site is unhealthy, then **move traffic** to a survivor — automatically where the blast radius is small, deliberately where it is not. Health checks are the detection half, and they are harder than they look: the classic incident is a server failing *fast* with blank pages while passing every responsiveness probe, thereby attracting *more* traffic (the black-hole effect). Quality attributes: **availability** and **recoverability** (RTO), bounded **data loss** (RPO). Costs: standby capacity, detection latency vs false-positive trade-offs, and the worst failure mode in distributed systems — split-brain.

## Lineage and vocabulary

- **The health-check taxonomy** (AWS Builders' Library): **liveness** (process up, port open) → **local** (disk writable, support processes) → **dependency** (peers, credentials) → **anomaly detection** (this server disagrees with its fleet: clock skew, old code). The deeper the check, the more it knows — and the more correlated its failures.
- **The cardinal rule**: a dependency wired into a routing health check turns a soft dependency into a hard one and can fail the whole fleet at once. Kubernetes says the same thing from the other side: liveness probes "should be used with caution"; incorrect ones "can lead to cascading failures" — backing-service checks belong in **readiness**, which removes the pod from endpoints, not in liveness, which kills it.
- **RTO/RPO** (AWS DR whitepaper): maximum acceptable delay to restoration; maximum acceptable window of lost data. Every failover design is a point on that plane.
- **Static stability**: the system keeps working when a dependency is impaired, *without any change* — and recovery must not depend on the **control plane** (more moving parts than the data plane, statistically more likely to be down with it). Pre-provision: three zones at ~66% each absorb a zone loss with no scale-up, no API call.

## Health checking (verified defaults)

| Layer | Defaults | Behavior |
|---|---|---|
| Kubernetes probes | period 10 s, timeout **1 s**, failure 3, success 1 (liveness/startup must be 1) | Startup gates the others; readiness → removed from EndpointSlices; liveness → restart. Slow starters: a startup probe with a high threshold, never a loose liveness |
| Envoy active checks | interval/timeout/thresholds **required, no defaults**; no-traffic interval 60 s | One success marks healthy at startup; pairs with passive outlier ejection ([breaker](CircuitBreaker.md)) |
| Route 53 | interval 30 s (or 10 s), failure threshold 3; ≥ 3 checker regions, healthy iff **> 18%** agree | HTTPS checks do **not** validate certificates; string match in the first 5,120 bytes; new checks are healthy until data |
| ALB/NLB | 30 s interval, 5 healthy / 2 unhealthy | **Fails open** when all targets are unhealthy (see the matrix) |
| gRPC | grpc.health.v1 Check/Watch; per-service names | Client-side health checking holds requests until healthy — fail-closed per subchannel |

Design the probe pair: liveness = "am I broken beyond restart?" (cheap, no dependencies); readiness = "can I serve right now?" (may consult dependencies); same endpoint with a higher liveness threshold is the documented pattern.

## Failover mechanics

- **Topologies**: active-passive (failover routing; standby idles at some scale) vs active-active (every healthy replica answers; unhealthy ones drop out of answers). The DR ladder with AWS's own tiers: backup & restore (RPO hours, RTO ≤ 24 h) → pilot light (minutes / tens of minutes; data live, compute off) → warm standby (seconds / minutes; scaled-down but functional) → multi-site active-active (≈ zero / ≈ zero; corruption still needs backups). The more scaled the standby, the less the failover depends on control-plane actions — the static-stability rule again.
- **Automation posture** (AWS's caution): fully *automatic* failover on alarms "should be used with caution" — a false alarm buys real downtime and data loss. The common production stance is **manually initiated, fully automated**: one deliberate push of a data-plane switch (Route 53 ARC's health checks are literally on/off toggles).
- **DNS failover**: keep health-checked record TTLs ≤ 60 s; the resolver cache *is* your failover latency. JVMs can cache lookups indefinitely — RDS documents the class, and RDS Proxy exists partly to bypass DNS caching (up to 66% faster failover).
- **Database failover timings** (documented): RDS Multi-AZ instance 60–120 s (a DNS flip); Multi-AZ cluster typically < 35 s (semisync, promotes the freshest reader); Aurora replica promotion usually < 30–60 s, but **no replica → ~10 minutes** to build a new writer; Patroni's clock: leader-lock `ttl` 30 s, `loop_wait` 10 s, `retry_timeout` 10 s, with the invariant `loop_wait + 2 × retry_timeout ≤ ttl`, and a 1 MiB default lag ceiling for election eligibility.
- **Split-brain control**: an unresponsive node cannot be assumed dead; without **fencing** (STONITH — power or fabric), promoting elsewhere risks two writers. Fencing tokens are the storage-side version ([quorums and fencing](../data-intensive-design/quorums-and-fencing.md)).

## Fail-open or fail-closed

The single most consequential default in the stack — verified rows:

| Layer | When all signals are bad | Default |
|---|---|---|
| Route 53 record selection | "If no record is healthy, all records are healthy" | **Open** |
| Route 53 failover pair | Both unhealthy → primary is returned | Open toward primary |
| ALB/NLB target groups | Route to all targets anyway | **Open** (tunable) |
| Envoy | Ejections capped at 10%; panic below 50% healthy spreads to all | Open guardrails |
| Kubernetes readiness | No ready endpoints → nothing to route to | **Closed** (opt-out: publishNotReadyAddresses) |
| gRPC client health checking | Hold requests until healthy | Closed per subchannel |
| K8s liveness | Restart | Closed, with restart-storm risk |

The documented rationale: fleet-blast-radius layers (DNS, LB) fail open because an all-unhealthy signal is more often a broken check or a blipped dependency than a dead fleet; per-endpoint gates fail closed because a healthy sibling absorbs the traffic. Know which side each layer of *your* stack is on before the day it matters.

## Observability

- Per target: health-state transitions with reasons (which check, which threshold) — flapping targets are a tuning signal, not noise.
- Fleet: healthy-fraction per zone/site; time-in-unhealthy; fail-open engagements (panic mode, all-unhealthy routing) as first-class alarms.
- Failover drills produce the two numbers that matter: measured RTO (detection + decision + propagation, including DNS TTL) and measured RPO (replication lag at cutover). Dashboards of *configured* values are not evidence.
- Watch replication lag continuously: it is your live RPO.

## Tuning

| Knob | Too aggressive | Too lax | Starting point |
|---|---|---|---|
| Probe interval × threshold | Flapping; restart storms | Minutes of black-hole traffic | Detection budget = interval × threshold; set it from the SLO's error budget |
| Probe timeout | Healthy-but-busy marked dead (K8s default 1 s bites) | Slow detection | ≥ p99 of the probe endpoint under load |
| Probe depth | Correlated fleet-wide failure | Blank-page servers pass | Liveness shallow; readiness as deep as *uncorrelated* dependencies allow |
| DNS TTL | Resolver load | Failover latency = TTL | ≤ 60 s on health-checked records |
| Election TTLs (Patroni-class) | Spurious failovers on GC pauses | Long write outages | Respect `loop_wait + 2 × retry ≤ ttl`; measure your pause distribution first ([process pauses](../data-intensive-design/process-pauses.md)) |
| Automation | False-alarm failovers (split-brain risk) | 3 a.m. human latency | Automatic within a zone; button-press across regions |

## Worked calibration — regional web service, RTO 5 min / RPO 30 s

| Decision | Choice | Why |
|---|---|---|
| Strategy | Warm standby in region B at 30% | RTO minutes without control-plane scale-up on the critical path; 100% pre-provision would be static-stability gold but the budget says 30% + shed |
| Data | Async replication, lag alarmed at 15 s | Half the RPO as the paging threshold |
| Detection | Synthetic checks from ≥ 3 regions on the user journey, 10 s fast checks, threshold 3 | 30 s detection; > 18% aggregation resists checker isolation |
| Decision | Human-initiated ARC toggle (data plane) | Cross-region failover is a business decision; the toggle is rehearsed monthly |
| Traffic | Route 53 failover records, TTL 30 s | Worst-case propagation ≈ TTL + resolver behavior; measured, not assumed |
| Fencing | Old primary's writes fenced before promotion (token/STONITH) | The GitHub lesson: 43 seconds of split writes cost 24 hours |
| Degrade | Region B at 30% sheds by criticality on arrival | [Load shedding](LoadShedding.md) and [degradation](GracefulDegradation.md) are what make a warm standby honest |

## Testing and operating

- Game-day the actual failover, including the *failback* (often the harder half); measure RTO/RPO each time. Untested failover is the fallback-code problem in its most expensive form.
- Kill checks in both directions: verify a genuinely dead target is ejected within budget, and that a check-bug (all targets "unhealthy") triggers the intended fail-open, not a blackout.
- Chaos at the dependency layer: break a *soft* dependency and assert the fleet stays healthy — this catches dependency-check creep in liveness probes.
- Rehearse under a control-plane brownout: can you fail over using only data-plane actions?

## Failure modes

- **The black hole**: fast-failing servers pass shallow checks and attract traffic. Fix with response-validating checks plus fleet anomaly comparison.
- **Correlated deep checks**: one dependency blip marks the whole fleet unhealthy; fail-open saves you (and should alarm), but the check design was the bug.
- **Restart storms**: dependency-aware liveness under load — kill, shift, kill. Readiness for dependencies; liveness for deadlocks.
- **Split-brain**: GitHub 2018-10-21 — 43 s of lost cross-country connectivity, an automatic cross-region promotion, 954 unreplicated writes on the old side, integrity chosen over availability, 24 h 11 m degraded; remediation: never promote primaries across regional boundaries automatically.
- **DNS-cached clients** sailing past your failover for their cache lifetime.
- **Standby rot**: warm standbys that never take traffic drift (config, data, capacity) until the day they must — continuously exercised failover (active-active for reads, periodic live drills) is the antidote.
- **Control-plane coupling**: recovery that needs instance launches or config pushes during the very outage that impaired them.

## Trade-offs

| Buy | Pay |
|---|---|
| Bounded RTO/RPO instead of open-ended outage | Standby capacity and replication cost, forever |
| Automated zone-level self-healing | False positives become self-inflicted outages |
| Fail-open guards against check bugs | Fail-open under a real fleet-down routes traffic into the fire |
| Deep checks catch gray failures | Deep checks correlate; anomaly detection is the safer depth |

Health checks decide **who is eligible**; [load balancing](LoadBalancing.md) spreads across the eligible; the [breaker](CircuitBreaker.md) is the per-client view of the same signal; [degradation](GracefulDegradation.md) is what the survivors do with the load.

## Sources

Verified 2026-09-13; full URLs and exclusions in the [external research note](../../docs/research/sysdesign/failover-degradation-external-research.md). Key primaries: Kubernetes probe docs; gRPC health protocol; Envoy health-check proto; Builders' Library health-checks and static-stability articles; AWS DR whitepaper + REL13/REL11; Route 53 health-check API and record-selection docs; RDS/Aurora failover docs; Patroni configuration; Pacemaker fencing docs; GitHub's 2018-10-21 post-incident analysis. ALB fail-open, Envoy panic, and incident set cited via the [circuit-breaker note](../../docs/research/sysdesign/circuit-breaker-external-research.md).
