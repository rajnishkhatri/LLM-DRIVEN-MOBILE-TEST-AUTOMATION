---
type: reference
title: 'Failover mechanisms and health checks'
description: 'Detect that a destination is dead, take it out of rotation, and replace it: probe kinds, fail-open vs fail-closed, active/passive vs active/active, RTO/RPO and the four AWS DR tiers, verified K8s / Route 53 / ALB knobs, DNS as hidden failover latency, and split-brain as a failover failure mode.'
tags: [system-design-patterns, availability, failover, health-checks]
---

# Failover mechanisms and health checks

**See also:** [circuit breaker](CircuitBreaker.md) · [retry, backoff, and retry budgets](RetryBackoff.md) · [load balancing](LoadBalancing.md) · [timeouts and deadline propagation](TimeoutsDeadlines.md) · [graceful degradation](GracefulDegradation.md) · [quorums and fencing](../data-intensive-design/quorums-and-fencing.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/c3-failover-health-external-research.md)

The [circuit breaker](CircuitBreaker.md) decides **whether to call**. [Retries](RetryBackoff.md) decide **whether to try again**. Both assume a destination still exists. This pattern owns the complementary question: **when is that destination declared dead, taken out of rotation, and replaced?** Failover is detect-then-move — a health check names unhealth; a routing or promotion action points traffic at a survivor. Automatic where the blast radius is one host; deliberate where it is a region.

Quality attributes in play: **availability** of the service (traffic still lands somewhere), **recoverability** (RTO — how long until service is restored), and **durability** of recent writes (RPO — how much time of data you accept losing). The costs are standby capacity paid every day, a detection-vs-false-positive trade, a hidden DNS/cache term in every user-visible RTO, and the worst failure mode of automatic failover — **split-brain**.

## Lineage and vocabulary

- **Yanacek, *Implementing health checks*** (AWS Builders' Library, fetched 2026-09-13) is the taxonomy. Opening incident: a render fleet served blank error pages; the process still answered load-balancer pings, failed *fast*, and a least-requests balancer sent it a disproportionate share. Ten servers, one black hole → availability ≤ 90%. Four check depths: **liveness** (connectivity + process present), **local / shallow** (on-box resources not shared with peers), **dependency / deep** (can this instance talk to neighbours — catches expired credentials; false-positives when the *dependency* is the problem; turns a soft dependency hard), **anomaly** (fleet-relative: clock skew, old code, too-fast 400s — the instance cannot see this about itself). Placement: the work producer (LB, queue poller) does liveness + local; a *central* actor with rate limits does dependency + anomaly. Amazon is "skeptical of things we can't fully reason about."
- **Kubernetes probes** (docs fetched 2026-09-13; page last modified 2026-04-17): **startup** gates the other two and succeeds once; **liveness** → kubelet restart; **readiness** → drop from EndpointSlices, process stays up. Liveness "should be used with caution"; incorrect implementations "can lead to cascading failures"; backing-service dependencies belong in readiness. Common pattern: the same cheap endpoint, higher liveness `failureThreshold`.
- **REL13-BP02 + AWS DR whitepaper** (fetched 2026-09-13): **RTO** is maximum acceptable delay from interruption to restored service; **RPO** is maximum acceptable time since the last recovery point. Four regional strategies, cost/complexity up, RTO/RPO down. Automatic failover on alarms "should be used with caution"; push-button automation of a *manual* decision is the common pattern. Recovery must use the **data plane** (REL11-BP04): health-checked Route 53 records and ARC routing-control health checks are data-plane on/off switches; changing Route 53 weights is control-plane.
- **Weiss & Furr, *Static stability using availability zones***: keep working when a dependency is impaired; no control-plane action on the recovery path. Three AZs → overprovision **50%**, each AZ at **66%** of load-tested capacity.
- **GitHub, 2018-10-21** (github.blog 2018-10-30): a 43 s optical partition; Orchestrator+Raft quorum in West + East-cloud promoted West primaries; East held unreplicated writes (busiest cluster **954 writes**); **24 h 11 m** degraded; integrity over availability; remediation = do not promote primaries across regional boundaries. Split-brain is a *failure mode of automatic failover*, not a separate pattern. Fencing tokens, leases, Chubby sequencers, Kafka epochs, Raft terms live in [quorums and fencing](../data-intensive-design/quorums-and-fencing.md).

## What the check is asking

Five questions share the name "health check." Mixing them is how a soft dependency becomes a hard one.

| Kind | Asks | Safe automated reaction | Unsafe automated reaction |
|---|---|---|---|
| **Liveness** | Can I reach a process on the port? | Remove one host | Restart a deadlock from a ping that cannot see it |
| **Local / K8s liveness** | Is *this* box independently broken (disk, deadlock, sibling process)? | LB eject; kubelet restart | A neighbour on this path (fleet restart) |
| **K8s startup** | Has init finished? | Hold liveness/readiness until success; then retire | Stuffing the startup budget into a loose liveness |
| **Readiness / local-for-traffic** | Should *new* work land here? | Drop from EndpointSlices / target group; process stays up | Failing readiness on a shared dependency without fail-open |
| **Dependency / anomaly** | Can I use my neighbours? Am I an outlier vs peers? | Central monitor, rate-limited replace, page a human | LB or liveness (soft dep → hard dep; clock-skew needs a fleet view) |

A queue poller has **no** load balancer to fail it out — an unhealthy consumer still eats messages. Active probes (the platform initiates them) are this card. Envoy/Istio **outlier detection** is passive (request failures) and is the [breaker](CircuitBreaker.md). Do not configure both as if they were one knob.

gRPC Health (`grpc.health.v1`): unary `Check` for central monitors ("does not scale" for a client fleet); streaming `Watch` for clients. Empty `service` = whole server. Client `healthCheckConfig.serviceName`: requests **held** until `SERVING`; `NOT_SERVING` or call failure → subchannel `TRANSIENT_FAILURE` so the balancer picks another (fail-closed per subchannel). `UNIMPLEMENTED` disables client health checking. `pick_first` may disable the feature.

## Fail-open vs fail-closed

| System | All-bad / missing-signal behavior | Default |
|---|---|---|
| Route 53 record group | "If no record is healthy, all records are healthy" | Fail-open |
| Route 53 failover pair | Both unhealthy → **primary**; a secondary without a check is healthy whenever the primary is unhealthy | Fail-open toward primary |
| Route 53 new / Disabled / CALCULATED `HealthThreshold` 0 | New checks healthy until data (invert → unhealthy until data); Disabled = always healthy; threshold 0 = always healthy | Fail-open |
| ALB target group | Only-unhealthy registered targets → route to **all**, all enabled AZs | Fail-open |
| NLB target group | All-unhealthy **or empty** → fail open; an AZ with zero healthy targets is **removed from DNS** until then | Fail-open + zonal DNS |
| Envoy `HealthStatus.UNKNOWN` | Interpreted as `HEALTHY` | Fail-open-ish |
| Kubernetes readiness | Failed → removed from EndpointSlices | **Fail-closed** |
| gRPC client health checking | Hold until healthy; unhealthy → `TRANSIENT_FAILURE` | Fail-closed per subchannel |
| K8s liveness | Failure → restart | Fail-closed with restart risk |

Blast-radius layers (DNS, LB) fail open because an all-fail signal is often a check bug or a shared-dependency blip; per-endpoint gates fail closed because a sibling can absorb the traffic. Test *partial* dependency failure — flapping around the fail-open threshold is worse than a clean all-down.

## Active/passive, active/active, and the four DR tiers

Route 53 (dns-failover-types, fetched 2026-09-13):

- **Active-active** = any non-failover policy (weighted, latency, …). Healthy records stay in answers; unhealthy dropped. Zero-weight weighted records are a standby used only when every nonzero-weight record is unhealthy — and the last healthy nonzero-weight target can be crushed.
- **Active-passive** = failover routing policy. Primary while healthy; secondary when primary is unhealthy. A multi-resource primary is healthy if **any** associated resource is.

REL13-BP02 (fetched 2026-09-13), regional, cost/complexity ↑, RTO/RPO ↓. These are **tier labels**, not SLAs:

| Strategy | RPO | RTO | Live in the recovery site | Recovery action |
|---|---|---|---|---|
| Backup & restore | hours (PITR can be ~**5 min**) | **≤ 24 h** | Backups | Deploy infra + code + restore (control plane) |
| Pilot light | minutes | tens of minutes | Data + core infra; app servers **off** | Provision compute, promote DB, shift traffic |
| Warm standby | seconds | minutes | Scaled-down **functional** stack | Scale up. Fully scaled = **hot standby** |
| Multi-site active/active | ~0 | potentially 0 | Full stack serving | Evacuate a Region. Write conflicts are *your* problem. Corruption still needs PITR. |

Pilot light cannot process requests without additional action; warm standby can, at reduced capacity. Do not pick a stricter tier than the business RTO/RPO — you pay for it every day. Prefer data-plane traffic shift. Global Accelerator traffic dials are control-plane; CloudFront origin failover is **per-request** and does not stay failed over.

Aurora Global (DR procedure page, fetched 2026-09-13): typical cross-Region lag **under a second**, up to **10** secondary Regions; **switchover** (planned) waits for sync → **RPO 0**; **failover** (unplanned) → RPO typically **seconds** (the lag at cut); RTO "on the order of minutes." Static stability is the *intra-Region* counterpart of warm/hot standby: AZ loss needs **no scale-up**.

## Detection, DNS, and user-visible RTO

```
t_detect  ≥  (failureThreshold − 1) × interval  +  timeout
t_user    ≥  t_detect  +  t_failover_action  +  t_DNS/cache  +  t_reconnect/warmup
```

| Checker | Default interval | Timeout | Unhealthy / healthy | Worst-case eject (approx.) |
|---|---|---|---|---|
| K8s probe | **10 s** | **1 s** | fail **3** / success **1** (liveness+startup success **must** be 1) | ~**31 s** then restart or unready |
| ALB (instance/ip) | **30 s** (5–300) | **5 s** (2–120; lambda timeout **30 s**, interval **35 s**) | unhealthy **2**, healthy **5** | ~**65 s** out; ~**155 s** back in |
| NLB | **30 s** | HTTP **6 s** / TCP+HTTPS **10 s** | **2** / **5**; matcher **200–399** (ALB default matcher is **200**) | ~**70 s** TCP |
| Route 53 | **30 s** (or **10 s** fast; **immutable**) | HTTP: TCP ≤ **4 s** + 2xx/3xx ≤ **2 s**; TCP ≤ **10 s** | `FailureThreshold` **3** (1–10); healthy iff **> 18%** of checkers agree | ~**90 s** + consensus; checkers **uncoordinated** |
| Envoy active | **required** (no default) | **required** | both **required**; startup: **one** success | — |
| Patroni leader lock | `loop_wait` **10 s** | `retry_timeout` **10 s** | `ttl` **30 s**; `loop_wait + 2×retry_timeout ≤ ttl` | lock expiry ~**30 s**; crash-with-`primary_start_timeout` **300 s** → worst `2×loop_wait + 300` = **320 s** |

DNS is a second timer nobody put in the RTO spreadsheet:

- Route 53: health-checked records, specify a TTL of **60 seconds or less**.
- RDS Multi-AZ instance **and** cluster: failover **flips DNS**; JVM `networkaddress.cache.ttl` recommended **≤ 60 s**; "some Java configurations… **never refresh** until the JVM is restarted."
- RDS Proxy "bypasses DNS caches to reduce failover times by up to **66%**" (Aurora HA page — a vendor reduction claim, not a measured distribution).
- Global Accelerator is the whitepaper's alternative when resolver caches make Route 53 look like it "didn't fail over."

A 30 s Route 53 fast check + 60 s TTL + a sticky JVM cache is an RTO measured in **minutes** before the engine failover (35–120 s) is even visible.

## Verified knobs (fetched 2026-09-13)

**Kubernetes probes.** `initialDelaySeconds` **0**; `periodSeconds` **10** (min 1); `timeoutSeconds` **1** (min 1); `successThreshold` **1** (**must** be 1 for liveness and startup); `failureThreshold` **3** (min 1); `terminationGracePeriodSeconds` inherits Pod **30 s** (probe-level override stable v1.28; **illegal on readiness**). httpGet success = status **200–399**; body cap **10 KiB**; same-host redirects followed, cross-host redirect counted *success* + `ProbeWarning`; ≥ 11 redirects also "success" + warning; HTTPS skips cert verify. exec forks per probe. gRPC probe stable **v1.27**; numeric port only; `service` distinguishes liveness vs readiness on one port. Docs worked example: startup `failureThreshold` 30 × period 10 s = **300 s** startup budget, then a tight liveness.

**Route 53 `HealthCheckConfig`.** `RequestInterval` default **30**, allowed **10 or 30**, **immutable**. `FailureThreshold` default **3**, range 1–10. `Regions` min **3**, max 64. CALCULATED: `ChildHealthChecks` max **256**; `HealthThreshold` 0–256; **0 = always healthy**. HTTPS **does not validate** certificates. String match in first **5,120** bytes.

**ALB vs NLB.** ALB: HTTP(S) GET; interval **30 s**; timeout **5 s**; healthy **5**; unhealthy **2**; matcher default **200**; gRPC path default `/AWS.ALB/healthcheck`, matcher default **12**; first success after register → `Healthy`; WebSockets not supported for health checks. NLB: protocol default **TCP**; targets see *more* checks than `interval` suggests (no published multiplier); HTTPS checks fail if the target is **TLS 1.3-only**.

**Envoy active** (`core.v3.HealthCheck`, docs `latest` = 1.40.0-dev). **Required (no defaults):** `timeout`, `interval`, `unhealthy_threshold`, `healthy_threshold`. Startup: **one** success. `reuse_connection` default **true**. `no_traffic_interval` default **60 s**. `HttpHealthCheck.path` required; `expected_statuses` default **200 only**. Non-expected, non-retriable HTTP → **immediately** unhealthy (threshold ignored). `DRAINING` and `TIMEOUT` → `UNHEALTHY`.

**Database failover timings** (re-fetched 2026-09-13):

| System | What flips | Documented time |
|---|---|---|
| RDS Multi-AZ **instance** | DNS to the standby (standby is **not** readable) | typically **60–120 s**; large tx / recovery can exceed |
| RDS Multi-AZ **cluster** | Promote a readable standby (two readers, 3 AZs) | typically **under 35 s**; completes when **both** readers applied outstanding tx |
| Aurora replica promotion | Cluster endpoint → new writer | typically **< 60 s**, often **< 30 s**. Priority tier **0–15** (0 highest); same tier → largest; after **five** unsuccessful attempts, tiers ignored. No replica → typically **< 10 min** to recreate the writer. Restart same instance is *faster* than failover. |
| Aurora Global switchover / failover | Planned role swap vs unplanned promote | Switchover: RPO **0**. Failover: RPO = lag (seconds); RTO typically a few minutes. Watch `AuroraGlobalDBRPOLag`. |
| Patroni (dynamic config) | DCS leader lock | `ttl` **30** (min 20), `loop_wait` **10**, `retry_timeout` **10**, `primary_start_timeout` **300**, `failsafe_mode` default **false**, `synchronous_mode` `off`/`on`/`quorum` |

Patroni `synchronous_mode` trades lost-tx on async failover for write unavailability when durability cannot be guaranteed — an RPO knob, not a health check. `maximum_lag_on_failover` is documented **without** a default on the 2026-09-13 fetch.

## Observability

Emit per target **and** per checker layer (they disagree):

| Signal | Why |
|---|---|
| Probe **class** (liveness / readiness / startup / LB / DNS / client) | "Unhealthy" is not a diagnosis |
| Reason code (`Target.Timeout` vs `ResponseCodeMismatch` vs kubelet `ProbeWarning`) | 10 KiB close vs real 5xx vs redirect-counted-success |
| `t_detect` vs `t_failover` vs `t_DNS` vs `t_reconnect` | RTO budget attribution |
| Healthy-host count **and** whether fail-open is active | All-unhealthy ALB/NLB still has 200s |
| Checker consensus (Route 53 % healthy, NLB extra probes) | Isolation vs true down |
| Replica lag / `AuroraGlobalDBRPOLag` at cut | Actual RPO, not the brochure |
| Version / generation on the health response | Yanacek zombies |
| Split-brain detector: two writers, epoch mismatch, rows in both DCs | GitHub 954-write window |

Do not page only on instance liveness — Yanacek's blank-page fleet could not self-report. ALB access logs / client error rate are the backstop.

## Tuning

| Knob | Too low | Too high | Starting point |
|---|---|---|---|
| Interval × unhealthy threshold | Flap; load on the probe path | User-visible hole bigger than the engine failover | Write user RTO, subtract DNS/cache and reconnect; remainder is what probes and the engine may spend |
| Probe timeout | Healthy GC / pause looks dead ([process pauses](../data-intensive-design/process-pauses.md)) | Overloaded box still "passes" and becomes a black hole | Just above p99 of a *cheap local* probe under load |
| Healthy vs unhealthy thresholds | Flap | Recovery delayed | Asymmetric (ALB 2 down / 5 up; Envoy startup one-success) — recover slower than eject |
| Check depth | Black holes stay in rotation | Soft dep becomes hard; fleet fail-closed | Liveness + local on the LB/kubelet path; dependency/anomaly on a central actor with a rate limit |
| DNS TTL + JVM/`nscd` cache | Resolver load | Failover happened; clients still have the corpse | TTL ≤ 60 s; set `networkaddress.cache.ttl` **before** the first connect |
| Fail-open threshold | Empty-fleet 5xx (K8s) | Check bug ejects everyone | Know which layer you are on before the day it matters |
| RTO/RPO tier | Paying for active/active you never exercise | Backup/restore against a minutes RTO | Match the business number; intra-Region vs regional are different budgets |
| Patroni `ttl` vs `loop_wait+2×retry` | False demotions on DCS blips | Split-brain window grows | Keep the inequality; `primary_start_timeout` 300 s vs a one-minute RTO is a miss |
| Promote-across-region | Cross-region split-brain (GitHub) | Regional DR cannot be automatic | Policy fence; push-button data-plane (ARC) |

Prioritize the ping under overload: extra workers beyond proxy max-connections, or a background `isHealthy` flag plus a dead-man on that thread (Yanacek). If that thread dies, the flag freezes. Exercise the failover **on purpose** — untested topology assumptions (promote-across-region) *are* the incident.

## Where it lives

| Layer | What it isolates | Scope | Trade-off |
|---|---|---|---|
| **Process liveness** (kubelet, systemd) | Deadlock / stuck PID | Per container | Restarts; cascade if the check is a dependency |
| **Readiness / EndpointSlice** | This Pod as a backend | Per Service | Fail-closed; all-unready = no endpoints |
| **Sidecar active check** (Envoy) | This host in *this* proxy's cluster | Per sidecar | Required knobs; `UNKNOWN`=`HEALTHY`; not fleet-coordinated |
| **LB active check** (ALB/NLB) | This target in the TG | Per LB node | Coarse; **fail-open**; NLB also drops an AZ from DNS |
| **Mesh outlier detection** | Bad host via *request* errors | Per sidecar | **[C1](CircuitBreaker.md)**, not this card |
| **DNS health** (Route 53) | This record in answers | Global checkers, **>18%** | TTL + stub resolvers dominate; fail-open group rule |
| **Client health** (gRPC Watch) | This subchannel | Per channel | Fail-closed; `pick_first` may ignore it |
| **DCS lock** (Patroni ttl) | Who is primary | Cluster | Timeout **is** the split-brain window unless storage fences |
| **Central monitor + rate limit** | Dependency / anomaly | Fleet | Slow; safe; needs a human threshold |
| **Policy fence** (no cross-region promote) | Topology the app cannot survive | Operator config | GitHub's actual fix |

## Worked calibration — checkout → payment

Constraints are a **design drill**, not a vendor SLA. Business: checkout accept **RTO 120 s**, payment capture **RPO 5 s**. Stack: three-AZ checkout (ALB → K8s); payments on **Aurora** (writer + two readers) in one Region; regional DR is **pilot light** (out of the 120 s budget).

| Decision | Choice | Why |
|---|---|---|
| AZ capacity | 3 AZ, +50% (each AZ ≤ 66% load-tested) | Static stability; AZ loss must not call the ASG control plane |
| K8s liveness | httpGet `/live` — process + disk; period 10, timeout 1, fail 3 | Local only. ~31 s to restart a deadlock. Not the payment DB. |
| K8s readiness | `/ready` — listen socket + in-process caches; period 5, fail 3 | Traffic gate. Aurora **not** on this path. |
| K8s startup | same as `/live`, fail 30 × 10 s = 300 s | Slow image vs tight liveness |
| ALB TG | interval **10 s**, timeout **3 s**, unhealthy **2**, healthy **5**, matcher 200 | `t_detect` ≈ 13–23 s. Default 30/5/2 spends **65 s** before Aurora has even failed over. |
| Check depth on ALB | `/ready` (local) | A deep `/ready` that `SELECT 1`s payments turns Aurora latency into a fleet-wide ALB fail-open flap |
| Aurora | Multi-AZ readers; cluster endpoint + RDS Proxy | Published promote **< 60 s / often < 30 s**; Proxy's "66%" only helps the DNS term |
| DNS / JVM | Route 53 TTL **60**; `networkaddress.cache.ttl=5` at process start | Hidden term. Without it, 120 s is already gone |
| Regional DR | Pilot light, **push-button** (ARC), not health-check automatic | REL13 caution; 120 s RTO is **intra-Region** only |
| RPO 5 s | In-Region Aurora storage covers AZ loss | Do not advertise 5 s RPO across a Region cut without measuring `AuroraGlobalDBRPOLag` at drill |

Budget: ALB detect ~20 s + Aurora promote ~30 s + DNS/Proxy ~10 s + reconnect ~10 s ≈ **70 s** typical, **< 120 s** if the JVM cache is not infinite. Default ALB 65 s + Aurora 60 s + TTL 60 s + JVM-never = **an RTO you did not choose**.

Hedging/retry of `POST /capture` is [C2](RetryBackoff.md). Brownout of the checkout page is [C11](GracefulDegradation.md). Outlier ejection of one payment replica is [C1](CircuitBreaker.md). Least-requests amplification of a black hole is [C5](LoadBalancing.md). Probe timeout as a *timer kind* is [C7](TimeoutsDeadlines.md).

## Failure modes

1. **Shallow check, fast-fail black hole.** Yanacek blank pages; least-requests amplifies. Local check must see *correct* responses, not just a 200 from the proxy.
2. **Deep check on the LB path.** Shared-dep blip ejects the fleet; fail-open may not trigger if only a *fraction* fail. Soft dep becomes hard.
3. **Liveness that checks a neighbour.** K8s documented cascade: restart under load → less capacity → more restarts.
4. **Startup budget stuffed into liveness.** Deadlocks wait out a 300 s window; or slow starters get killed every 30 s. Split the probes.
5. **httpGet success on a cross-host redirect / 11+ redirects / 10 KiB close.** Probe green, app logs look like a network fault.
6. **Fail-open you did not know you had.** ALB/NLB all-unhealthy; NLB empty TG; Route 53 group rule; Disabled check = always healthy; Envoy `UNKNOWN`. Dashboards show 200s to dead targets.
7. **Fail-closed at the wrong layer.** All Pods unready because the one DB is slow → ClusterIP has no endpoints while the LB above is still green (or vice versa).
8. **DNS/JVM cache longer than the failover.** Engine flipped; clients still write the corpse.
9. **Automatic failover on a gray health signal.** False failover costs RPO. Prefer push-button data-plane (ARC).
10. **Control plane on the recovery path.** ASG scale-out, weight edits, "launch more in the good AZ."
11. **Pilot light advertised as warm standby.** Cannot take traffic until you provision.
12. **Active/active writes without a conflict story.** Last-writer-wins / partitioned writes / "avoid or handle." Corruption still needs backups.
13. **Split-brain.** Timeout declared death; the zombie still writes. GitHub: 43 s / 954 writes / 24 h 11 m. A node cannot trust "I am alive"; majority decides death; a lease without a fencing token is split-brain; STONITH does not stop a packet already in flight ([quorums and fencing](../data-intensive-design/quorums-and-fencing.md)). Name **what fences the zombie** — DCS lock (Patroni `ttl`), storage epoch, or an explicit "we will not promote across this boundary." This is a failure mode of automatic failover, not a fencing card.
14. **Patroni inequality broken**, or `primary_start_timeout=300` vs an RTO of a minute.
15. **TLS 1.3-only NLB HTTPS checks**; Route 53 HTTPS without cert validation (expired cert still "healthy"); ALB matcher 200 vs a 204 endpoint.
16. **Zombie after partition.** Old code, old schema. Put version on the health response; refuse re-admit.
17. **Health checks not prioritized under overload.** Timeouts fire, fleet shrinks, downward spiral. [C11](GracefulDegradation.md) owns the brownout *response*; this card owns not ejecting yourself.

## When not to use

A health check is the wrong tool for: deciding *whether to call* a dependency ([breaker](CircuitBreaker.md)); bounding *how long* to wait ([timeouts](TimeoutsDeadlines.md)); shedding load ([load shedding](LoadShedding.md)); serving stale ([degradation](GracefulDegradation.md)); choosing among already-healthy backends ([load balancing](LoadBalancing.md)); fencing a zombie writer ([quorums and fencing](../data-intensive-design/quorums-and-fencing.md)); in-process resources.

Automatic failover is the wrong tool for: cross-region promote when the app cannot bear the RTT (GitHub); gray failures; any path whose fence is "we will reconstruct from backups" — that is restore, not failover; an RTO smaller than `t_detect + TTL`.

## Trade-offs

| Buy | Pay |
|---|---|
| Bounded RTO/RPO instead of open-ended outage | Standby capacity and replication cost, every day |
| Automated host/AZ self-healing | False positives become self-inflicted outages; gray signals become split-brain |
| Fail-open at DNS/LB | A real fleet-down keeps routing into the fire; dashboards still show 200s |
| Fail-closed at readiness / gRPC | All-unready = no endpoints while the layer above is still green |
| Deep checks catch gray failures | Soft dependencies become hard; correlated fleet ejection |
| Data-plane traffic shift | Control-plane recovery (scale-out, weight edits) is off the path — you must have pre-provisioned |
| Policy fence against cross-region promote | Regional DR cannot be a health-check reflex |

Health checks decide **who is eligible**. [Load balancing](LoadBalancing.md) spreads across the eligible. The [breaker](CircuitBreaker.md) is the per-client view of the same dependency. [Timeouts](TimeoutsDeadlines.md) bound the probe and the call. [Retries](RetryBackoff.md) must not chase an endpoint the LB just failed away from. [Degradation](GracefulDegradation.md) is what the survivors do with the load. [Quorums and fencing](../data-intensive-design/quorums-and-fencing.md) is what stops the zombie writing.

## Sources

Verified 2026-09-13; the full URL list, per-claim provenance, and items deliberately left out are in the [external research note](../../docs/research/sysdesign/c3-failover-health-external-research.md). Combined first-pass (C3+C11): [failover-degradation-external-research.md](../../docs/research/sysdesign/failover-degradation-external-research.md).

- Canon: Yanacek, *Implementing health checks* (Builders' Library); Weiss & Furr, *Static stability using availability zones* (50% / 66%); REL13-BP02 and the AWS DR whitepaper; Kubernetes probe docs (and v1.36 snapshot); GitHub 2018-10-21 post-incident analysis.
- DNS / LB / RPC: Route 53 determining-health, choosing-records, dns-failover-types, `HealthCheckConfig` API; ALB and NLB target-group health checks; Envoy `core.v3.HealthCheck` proto 1.40.0-dev; gRPC health-checking guide.
- Databases: RDS Multi-AZ instance (60–120 s; JVM TTL) and cluster (< 35 s); Aurora HA (< 60 / often < 30; < 10 min; Proxy 66%); Aurora Global DR (RTO minutes; switchover RPO 0; failover RPO seconds); Patroni dynamic configuration.
- Safety: [quorums-and-fencing.md](../data-intensive-design/quorums-and-fencing.md). Outlier detection / panic / `minimum_healthy_targets`: [circuit breaker](CircuitBreaker.md).
