---
type: research
title: 'Failover & health checks — external research (2026-09-13)'
description: >-
  Group C catalog evidence pass for C3: health-check kinds (liveness / local /
  dependency / anomaly + K8s startup/readiness), fail-open vs fail-closed,
  active/passive vs active/active, RTO/RPO and the four AWS DR tiers, DNS TTL
  + LB failover, verified DB timings, and split-brain as a failover failure
  mode — breaker and retry assume a live endpoint exists.
tags: [research, system-design-patterns, C3, failover, health-checks]
---

# C3 Failover mechanisms & health checks — catalog research (2026-09-13)

> **What this is.** The catalog evidence pass for **C3**. It **links** the same-day first pass [failover-degradation-external-research.md](failover-degradation-external-research.md) (C3+C11 combined) and **deepens the C3 half only** to the Group C / [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md) bar: mechanics and variants, knobs with verified defaults, observability, tuning, a worked calibration, failure modes, sources. Breaker (C1) and retry (C2) already assume there is a destination; this note owns how that destination is declared dead, taken out of rotation, and replaced.
>
> **Method.** Primary pages fetched 2026-09-13. Numbers and option names reproduced exactly; everything else paraphrased. Facts marked **[→C3-1]** are in the first-pass note and not re-fetched here. Facts marked **[→breaker]** are in [circuit-breaker-external-research.md](circuit-breaker-external-research.md). Unverifiable items are in §10 and are **not** asserted as fact.

---

## 1. Scope and non-goals

**Owns.** Liveness vs local vs dependency vs anomaly health checks (Yanacek); Kubernetes startup / liveness / readiness as the container-runtime mapping of those kinds; fail-open vs fail-closed at each layer; active/passive vs active/active; RTO/RPO and the four AWS DR strategy tiers; DNS TTL + resolver caches as the hidden term in user-visible failover; LB active health checks (ALB/NLB/Envoy) as the *routing* decision, not a breaker; verified database failover timings (RDS Multi-AZ instance/cluster, Aurora, Aurora Global, Patroni knobs); split-brain **as a failover failure mode** (GitHub 2018) with a recommended card split.

**Does not own.** Graceful degradation, stale-while-revalidate, brownout, kill-switch flags (**C11** — the first-pass §§4–5 stay there; do not duplicate). What errors trip a breaker, and mesh *outlier detection* (**C1** — passive ejection is a breaker, not a health check). Load-balancing algorithms and least-requests black holes as *routing math* (**C5** — Yanacek’s black-hole story is cited here only as a health-check motivation). Probe timeouts as a *timer kind* (**C7** — this note only uses the timeout as a health-check knob). Fencing tokens, leases, Chubby sequencers, Kafka epochs, Raft terms, etcd revision+lease — [quorums-and-fencing.md](../../../cases/data-intensive-design/quorums-and-fencing.md). STONITH that does not stop an in-flight packet is that case’s point; this note only names power/fabric fencing as the *ops* counterpart.

**Does not re-derive.** [process-pauses.md](../../../cases/data-intensive-design/process-pauses.md) (a live node looks dead). [unreliable-networks.md](../../../cases/data-intensive-design/unreliable-networks.md) (silence is not a boolean). [single-leader-replication.md](../../../cases/data-intensive-design/single-leader-replication.md) (leader failover). [timeouts-and-delays.md](../../../cases/data-intensive-design/timeouts-and-delays.md) (no correct constant; Φ accrual).

---

## 2. Lineage / vocabulary

| Term | Meaning | Named source |
|---|---|---|
| **Liveness check** | Connectivity + process present. Unaware of application correctness. | Yanacek, Builders’ Library (builder.aws.com, fetched 2026-09-13) |
| **Local / shallow check** | On-box resources not shared with peers (disk, sibling process, support daemon). Unlikely to fail the fleet at once. | Same; N&CD “shallow vs deep” |
| **Dependency / deep check** | Can this instance talk to adjacent systems? Catches expired credentials; false-positives when the *dependency* is the problem. Turns a soft dependency hard. | Yanacek |
| **Anomaly detection** | Fleet-relative: clock skew, old code, too-fast 400s, too-slow 200s. The instance cannot see this about itself. | Yanacek |
| **Startup / liveness / readiness** | K8s mapping: startup gates the other two; liveness → restart; readiness → drop from EndpointSlices (process keeps running). | kubernetes.io probes (fetched 2026-09-13; page last modified 2026-04-17) |
| **Fail-open** | All-unhealthy (or no signal) → treat everyone as healthy and keep routing. | Route 53 “If no record is healthy, all records are healthy”; ALB/NLB all-unhealthy; Envoy `UNKNOWN` → `HEALTHY` |
| **Fail-closed** | No healthy target → drop / hold / restart. | K8s readiness; gRPC client health checking |
| **Active-passive** | Secondary used only when primary is unhealthy. Route 53 *failover* policy. | Route 53 dns-failover-types |
| **Active-active** | Any healthy record of the same name/type/policy may be answered. Unhealthy dropped. | Same |
| **RTO** | Maximum acceptable delay from interruption to restored service (downtime). | REL13-BP02; Aurora Global DR page |
| **RPO** | Maximum acceptable time since the last recovery point (data loss, measured in time). | Same |
| **Static stability** | Keep working when a dependency is impaired; no control-plane action on the recovery path. Three AZs → overprovision **50%**, each AZ at **66%** of load-tested capacity. | Weiss & Furr, Builders’ Library (fetched 2026-09-13) |
| **Split-brain** | Two primaries accept writes that the other never saw. A *failure mode of automatic failover*, not a separate pattern. | GitHub 2018-10-21; [quorums-and-fencing.md](../../../cases/data-intensive-design/quorums-and-fencing.md) |

**Yanacek, *Implementing health checks*** (Builders’ Library; fetched 2026-09-13 from `builder.aws.com`). Opening incident: a render-fleet bug served blank error pages; the process still answered LB pings, failed *fast*, and a least-requests balancer sent it a disproportionate share (“black hole”). Ten-server fleet, one black hole → availability **≤ 90%**. Taxonomy above. Fail-open at NLB/ALB/Route 53 is what makes a *dependency* check on the LB path survivable — and Amazon is “skeptical of things we can’t fully reason about”: teams still prefer **liveness + local on the LB**, dependency/anomaly on a *central* actor with rate limits. A health-check thread that updates an `isHealthy` flag keeps the ping fast under overload; if that thread dies, the flag freezes. Soft dependency on the health path becomes a hard dependency and a cascade.

**Kubernetes probes** (docs current + v1.36 snapshot, fetched 2026-09-13). Startup succeeds once, then never again. Liveness “should be used with caution”; “Incorrect implementation of liveness probes can lead to cascading failures”; backing-service dependencies belong in **readiness**, not liveness. Common pattern: same cheap endpoint, **higher liveness `failureThreshold`**. httpGet success = status **200–399**; body read capped **10 KiB**; same-host redirects followed, cross-host redirect counted *success* + `ProbeWarning`; ≥ 11 redirects also “success” + warning. exec forks per probe (CPU tax at density). gRPC probe stable **v1.27**; numeric port only; `service` distinguishes liveness vs readiness on one port.

**REL13-BP02 + DR whitepaper** (fetched 2026-09-13). Four regional strategies, cost/complexity up, RTO/RPO down. Automatic failover on alarms “should be used with caution”; push-button automation of a *manual* decision is the common pattern. Recovery must use the **data plane** (REL11-BP04); changing Route 53 weights is control-plane; ARC routing-control health checks are data-plane on/off switches.

**GitHub, 2018-10-21** (github.blog 2018-10-30, fetched 2026-09-13). 43 s optical partition; Orchestrator+Raft quorum in West + East-cloud promoted West primaries; East held unreplicated writes (busiest cluster **954 writes**); **24 h 11 m** degraded; integrity over availability; remediation = do not promote primaries across regional boundaries.

---

## 3. Mechanics

### 3.1 Five questions that share the name “health check”

| Kind | Asks | Safe automated reaction | Unsafe automated reaction |
|---|---|---|---|
| **Liveness** | Can I reach a process on the port? | Remove one host; EC2 status checks | None — too shallow to restart a deadlock |
| **Local / K8s liveness** | Is *this* box independently broken (disk, deadlock, sibling process)? | LB eject; kubelet restart | Dependency on this path (fleet restart) |
| **K8s startup** | Has init finished? | Hold liveness/readiness until success; then retire | Using a loose liveness instead (deadlocks wait out the long window forever) |
| **Readiness / local-for-traffic** | Should *new* work land here? | Drop from EndpointSlices / target group; process stays up | Failing readiness on a shared dependency without fail-open |
| **Dependency / anomaly** | Can I use my neighbours? Am I an outlier vs peers? | Central monitor, rate-limited replace, page a human | LB or liveness (soft dep → hard dep; clock-skew / old-code needs a *fleet* view) |

Yanacek’s placement rule: the work producer (LB, queue poller) does liveness + local. External monitoring does dependency + anomaly. K8s maps “take me out of rotation but keep me alive” to readiness and “I am unrecoverably stuck” to liveness. A queue poller has **no** LB to fail it out — a disk-full worker still consumes messages; SQS visibility timeout is the compensating factor, not a probe **[→C3-1]**.

gRPC Health (`grpc.health.v1`, guide fetched 2026-09-13). Unary `Check` for central monitors (“does not scale” for a client fleet). Streaming `Watch` for clients. Empty `service` = whole server. Client `healthCheckConfig.serviceName`: requests **held** until `SERVING`; `NOT_SERVING` or call failure → subchannel `TRANSIENT_FAILURE` so the balancer picks another (fail-closed per subchannel). `UNIMPLEMENTED` disables client health checking. `pick_first` may disable the feature. Envoy gRPC health check sends the same `service_name`.

Active vs passive: this note’s *active* check is a probe the platform initiates. Envoy/Istio **outlier detection** is passive (request failures) and is **C1** **[→breaker]**. Do not configure both as if they were one knob.

### 3.2 Fail-open vs fail-closed

| System / knob | All-bad / missing-signal behavior | Default | Fetch |
|---|---|---|---|
| Route 53 record group | “If no record is healthy, all records are healthy” | Fail-open | choosing-records, 2026-09-13 |
| Route 53 failover pair | Both unhealthy → **primary**; secondary without a check = healthy whenever primary is unhealthy | Fail-open toward primary | same |
| Route 53 new / Disabled / CALCULATED `HealthThreshold` 0 | New checks healthy until data (invert → unhealthy until data); Disabled = always healthy; threshold 0 = always healthy | Fail-open | API + determining-health |
| ALB target group | Only-unhealthy registered targets → route to **all**, all enabled AZs | Fail-open | ALB health-checks page |
| NLB target group | All-unhealthy **or empty** → fail open; an AZ with zero healthy targets is **removed from DNS** until then | Fail-open + zonal DNS | NLB health-checks page |
| Envoy `HealthStatus.UNKNOWN` | Interpreted as `HEALTHY` | Fail-open-ish | proto 1.40.0-dev |
| Envoy outlier / panic / ALB `minimum_healthy_targets` | Panic and fail-open *tuning* | **[→breaker]** | do not re-derive |
| Kubernetes readiness | Failed → removed from EndpointSlices | **Fail-closed** | probes page |
| K8s `publishNotReadyAddresses` / Local traffic policy | Headless fail-open opt-in; Local with no node-local endpoints drops | **[→C3-1]** | |
| gRPC client health checking | Hold until healthy; unhealthy → `TRANSIENT_FAILURE` | Fail-closed per subchannel | grpc.io guide |
| K8s liveness | Failure → restart | Fail-closed with restart risk | probes caution |

Yanacek’s rationale (paraphrase): blast-radius layers (DNS, LB) fail open because an all-fail signal is often a check bug or a shared-dependency blip; per-endpoint gates fail closed because a sibling can absorb the traffic. Test *partial* dependency failure — flapping around the fail-open threshold is worse than a clean all-down.

### 3.3 Active/passive vs active/active, and the four DR tiers

Route 53 (dns-failover-types, fetched 2026-09-13):

- **Active-active** = any non-failover policy (weighted, latency, …). Healthy records stay in answers; unhealthy dropped.
- **Active-passive** = failover routing policy. Primary while healthy; secondary when primary is unhealthy. Multi-resource primary is healthy if **any** associated resource is. Zero-weight weighted records are a standby that is used only when every nonzero-weight record is unhealthy — and the last healthy nonzero-weight target can be crushed.

REL13-BP02 (fetched 2026-09-13), regional, cost/complexity ↑, RTO/RPO ↓:

| Strategy | RPO | RTO | What is live in the recovery site | Recovery action |
|---|---|---|---|---|
| Backup & restore | hours (PITR can be ~**5 min**) | **≤ 24 h** | Backups | Deploy infra + code + restore (control plane) |
| Pilot light | minutes | tens of minutes | Data + core infra; app servers **off** / undeployed | Provision compute, promote DB, shift traffic |
| Warm standby | seconds | minutes | Scaled-down **functional** stack | Scale up. Fully scaled = **hot standby** (less control-plane reliance) |
| Multi-site active/active | ~0 | potentially 0 | Full stack serving | Evacuate a Region. Write conflicts are *your* problem. Corruption still needs PITR. |

Pilot light cannot process requests without additional action; warm standby can, at reduced capacity. REL13: do not pick a stricter tier than the business RTO/RPO — you pay for it every day. DR whitepaper (fetched 2026-09-13): passive site serves nothing until failover; **use only data-plane operations as part of failover**; Route 53 health-checked DNS failover is data-plane; flipping weighted records is not; Global Accelerator traffic dials are control-plane; CloudFront origin failover is **per-request** and does not stay failed over.

Aurora Global (DR page + overview, fetched 2026-09-13) is the concrete DB mapping: typical cross-Region lag **under a second**, up to **10** secondary Regions; **switchover** (planned, previously “managed planned failover”) waits for sync → **RPO 0**; **failover** (unplanned) → RPO typically **seconds** (the lag at cut); RTO “on the order of minutes”. Dedicated replication infrastructure; promote-secondary marketing line “in less than one minute” is on the Aurora FAQ / DRS comparison pages — the DR procedure page itself says the chosen secondary “typically… within a few minutes.” Put the one-minute figure only on the FAQ/compare pages, not on the procedure.

Static stability (Weiss & Furr, fetched 2026-09-13) is the *intra-Region* counterpart of warm/hot standby: three AZs, overprovision **50%**, each AZ **66%** of load-tested capacity, so an AZ loss needs **no scale-up**. The ALB itself is provisioned to survive an AZ without growing. Control plane (launch, ASG, register) stays off the recovery path.

### 3.4 Detection, DNS TTL, and user-visible RTO

Worst-case **probe** detection, independent of C7’s timer taxonomy:

```
t_detect  ≥  (failureThreshold − 1) × interval  +  timeout     (consecutive-fail model)
t_user    ≥  t_detect  +  t_failover_action  +  t_DNS/cache  +  t_reconnect/warmup
```

| Checker | Default interval | Timeout | Unhealthy / healthy thresholds | Worst-case eject (approx.) |
|---|---|---|---|---|
| K8s probe | **10 s** | **1 s** | fail **3** / success **1** (liveness+startup success **must** be 1) | ~**31 s** then restart or unready |
| ALB (instance/ip) | **30 s** (5–300) | **5 s** (2–120; lambda timeout **30 s**, interval **35 s**) | unhealthy **2**, healthy **5** | ~**65 s** out; ~**155 s** back in |
| NLB | **30 s** | HTTP **6 s** / TCP+HTTPS **10 s** | **2** / **5**; matcher **200–399** (ALB default matcher is **200**) | ~**70 s** TCP |
| Route 53 | **30 s** (or **10 s** fast; **immutable**) | HTTP: TCP ≤ **4 s** + 2xx/3xx ≤ **2 s**; TCP ≤ **10 s** | `FailureThreshold` **3** (1–10); healthy iff **> 18%** of checkers agree | ~**90 s** + consensus; checkers **uncoordinated** (bursts) |
| Envoy active | **required** (no default) | **required** | both **required**; startup: **one** success | — |
| Patroni leader lock | `loop_wait` **10 s** | `retry_timeout` **10 s** | `ttl` **30 s**; rule `loop_wait + 2×retry_timeout ≤ ttl` | lock expiry ~**30 s**; crash-with-`primary_start_timeout` **300 s** → worst `2×loop_wait + 300` = **320 s** |

DNS is a second timer nobody put in the RTO spreadsheet:

- Route 53: health-checked records “specify a TTL of **60 seconds or less**” **[→C3-1]** (failover-record-values; first pass).
- RDS Multi-AZ instance **and** Multi-AZ cluster pages (fetched 2026-09-13): failover **flips DNS**; JVM `networkaddress.cache.ttl` recommended **≤ 60 s**; “some Java configurations… **never refresh** until the JVM is restarted.”
- RDS Proxy “bypasses DNS caches to reduce failover times by up to **66%**” (Aurora HA page, fetched 2026-09-13).
- Global Accelerator is the whitepaper’s explicit alternative when resolver caches make Route 53 look like it “didn’t fail over.”

A 30 s Route 53 fast check + 60 s TTL + a sticky JVM cache is an RTO measured in **minutes** before the engine failover (35–120 s) is even visible.

### 3.5 Database failover timings (re-fetched 2026-09-13)

| System | What flips | Documented time | Notes |
|---|---|---|---|
| RDS Multi-AZ **instance** | DNS to the standby (standby is **not** readable) | typically **60–120 s**; large tx / recovery can exceed | Triggers: OS patch, unhealthy primary, network loss, storage failure, reboot-with-failover, customer modify, primary “busy and unresponsive” |
| RDS Multi-AZ **cluster** | Promote a readable standby (two readers, 3 AZs) | typically **under 35 s**; completes when **both** readers applied outstanding tx | Manual failover: terminate writer, monitor promotes. Semisync / flow-control details **[→C3-1]** |
| Aurora replica promotion | Cluster endpoint → new writer | typically **< 60 s**, often **< 30 s** | Priority tier **0–15** (0 highest); same tier → largest; then arbitrary. After **five** unsuccessful attempts, tiers ignored. Restart same instance is *faster* than failover. Aurora MySQL: non-target readers stay up. |
| Aurora, **no** replica | Recreate writer in same AZ | typically **< 10 min** | |
| Aurora Global switchover | Planned role swap, sync first | RPO **0**; unavailable “a short time” | Same major/minor (patch rules vary) |
| Aurora Global failover | Unplanned promote | RPO = lag (seconds); “typically… a few minutes” | `AuroraGlobalDBRPOLag` / `AuroraGlobalDBReplicationLag` (ms) |
| RDS Proxy | Preserve app connections; skip DNS cache | “up to **66%**” vs DNS-only | Marketing reduction, not a substitute for `t_detect` |
| Patroni (dynamic config, latest docs) | DCS leader lock | `ttl` **30** (min 20), `loop_wait` **10** (min 1), `retry_timeout` **10** (min 3) | `primary_start_timeout` **300**; `synchronous_mode` `off`/`on`/`quorum`; `failsafe_mode` default **false**; `maximum_lag_on_failover` documented **without** a default on this fetch |

Patroni `synchronous_mode` trades lost-tx on async failover for write unavailability when durability cannot be guaranteed. That is an RPO knob, not a health check.

### 3.6 Split-brain as a failover failure mode

Automatic failover is “declare the primary dead, promote a standby.” The declaration is a timeout plus a quorum or a single observer. Wrong declaration → two writers.

GitHub 2018 (re-fetched) is the operational exhibit: a **43 s** partition was enough for Orchestrator (Raft) to form a quorum that **did not include** the East primary’s DC, promote West, and leave **954** East writes unreplicated. Cross-country latency then made “fail forward” the integrity-preserving choice and a **24 h 11 m** brownout (C11 owns the *degradation*; C3 owns the *split*). Remediation was a **policy fence** (do not promote across regions) — not a storage token.

[quorums-and-fencing.md](../../../cases/data-intensive-design/quorums-and-fencing.md) owns the *safety* side: a node cannot trust “I am alive”; majority decides death; a lease without a fencing token is split-brain; STONITH does not stop a packet already in flight; storage must reject a stale token (Chubby sequencer, Kafka epoch, Raft term, etcd revision+lease). This note only requires that any automatic failover name **what fences the zombie** — DCS lock (Patroni `ttl`), storage epoch, or an explicit “we will not promote across this boundary.” Pacemaker STONITH as the HA-cluster *ops* fence stays **[→C3-1]** / the DDIA case.

---

## 4. Verified defaults / standards (fetched 2026-09-13)

### 4.1 Kubernetes probes

| Knob | Default | Constraint |
|---|---|---|
| `initialDelaySeconds` | **0** | Startup success delays the others’ clocks |
| `periodSeconds` | **10** (min 1) | Unready readiness may run *faster* than period (“make the Pod ready faster”) |
| `timeoutSeconds` | **1** (min 1) | C7 owns this as a timer; here it is a probe knob |
| `successThreshold` | **1** | **Must be 1** for liveness and startup |
| `failureThreshold` | **3** (min 1) | |
| `terminationGracePeriodSeconds` | inherit Pod **30 s** | Probe-level override stable v1.28; **illegal on readiness** |
| httpGet | 200–399; UA `kube-probe/<ver>`; 10 KiB body cap | HTTPS skips cert verify |
| grpc | stable v1.27; `SERVING` = success | Port number only |

Docs worked example: startup `failureThreshold` 30 × period 10 s = **300 s** startup budget, then a tight liveness.

### 4.2 Envoy active health check (`core.v3.HealthCheck`, docs `latest` = 1.40.0-dev)

**Required (no defaults):** `timeout`, `interval`, `unhealthy_threshold`, `healthy_threshold`. Startup: **one** success. `reuse_connection` default **true**. `no_traffic_interval` default **60 s** (unused cluster). `HttpHealthCheck.path` required; `expected_statuses` default **200 only** (must list 200 explicitly if you replace the set). Non-expected, non-retriable HTTP → **immediately** unhealthy (threshold ignored). `DRAINING` and `TIMEOUT` → `UNHEALTHY`; `UNKNOWN` → `HEALTHY`. Jitter: `initial_jitter`, `interval_jitter`, `interval_jitter_percent` (both jitter knobs add if both set).

### 4.3 Route 53 `HealthCheckConfig` (API, fetched 2026-09-13)

`RequestInterval` default **30**, allowed **10 or 30**, **immutable**. `FailureThreshold` default **3**, range 1–10. `Regions` min **3**, max 64 (enumerated eight classic checker regions). CALCULATED: `ChildHealthChecks` max **256** items; `HealthThreshold` 0–256; **0 = always healthy**. HTTPS **does not validate** certificates (determining-health page). String match in first **5,120** bytes. Types: HTTP / HTTPS / `*_STR_MATCH` / TCP / `CLOUDWATCH_METRIC` / `CALCULATED` / `RECOVERY_CONTROL`.

### 4.4 ALB vs NLB (re-fetched; ALB numbers also **[→breaker]**)

ALB: HTTP(S) GET; interval **30 s**; timeout **5 s**; healthy **5**; unhealthy **2**; matcher default **200**; gRPC path default `/AWS.ALB/healthcheck`, matcher default **12**. First success after register → `Healthy`. WebSockets not supported for health checks.

NLB: protocol default **TCP**; HTTP timeout **6 s**, TCP/HTTPS **10 s**; matcher **200–399**; consensus (targets see *more* checks than `interval` suggests); HTTPS checks fail if the target is **TLS 1.3-only**.

---

## 5. Knobs, observability, tuning, placement

### 5.1 Knobs

| Knob | Role | Too low | Too high |
|---|---|---|---|
| Probe interval × unhealthy threshold | `t_detect` | Flap; load on the probe path | User-visible hole bigger than the engine failover |
| Probe timeout | Stall vs slow | Healthy GC / pause looks dead ([process-pauses.md](../../../cases/data-intensive-design/process-pauses.md)) | Overloaded box still “passes” and becomes a black hole |
| Healthy vs unhealthy thresholds | Hysteresis | Flap | Recovery delayed after the box is fine |
| Check depth (liveness / local / dep) | What “unhealthy” *means* | Black holes stay in rotation (Yanacek) | Soft dep becomes hard; fleet fail-closed |
| DNS TTL + JVM/`nscd` cache | Hidden RTO term | Resolver load | Failover happened; clients still have the corpse |
| Fail-open threshold | All-down behavior | Empty-fleet 5xx (K8s) | Check bug or shared-dep outage takes the site down by *ejecting everyone* |
| RTO/RPO tier | Cost vs loss | Paying for active/active you never exercise | Backup/restore against a minutes RTO |
| Patroni `ttl` vs `loop_wait+2×retry` | When the lock is allowed to expire | False demotions on DCS blips | Split-brain window grows |
| `primary_start_timeout` / `synchronous_mode` | Crash recovery vs lost tx | Immediate failover, possible RPO hit | **320 s** worst-case with defaults |
| Promote-across-region | Policy fence | Cross-region split-brain (GitHub) | Regional DR cannot be automatic |

### 5.2 Observability (feeds D3/D4)

Emit, per target **and** per checker layer (they disagree):

| Signal | Why |
|---|---|
| Probe **class** (liveness / readiness / startup / LB / DNS / client) | “Unhealthy” is not a diagnosis |
| Reason code (`Target.Timeout` vs `ResponseCodeMismatch` vs kubelet `ProbeWarning`) | 10 KiB close vs real 5xx vs redirect-counted-success |
| `t_detect` vs `t_failover` vs `t_DNS` vs `t_reconnect` | RTO budget attribution |
| Healthy-host count **and** whether fail-open is active | All-unhealthy ALB/NLB still has 200s |
| Checker consensus (Route 53 % healthy, NLB extra probes) | Isolation vs true down |
| Replica lag / `AuroraGlobalDBRPOLag` at cut | Actual RPO, not the brochure |
| Version / generation on the health response | Yanacek zombies |
| Split-brain detector: two writers, epoch mismatch, rows in both DCs | GitHub 954-write window |

Do not page only on instance liveness — Yanacek’s blank-page fleet could not self-report. ALB access logs / client error rate are the backstop.

### 5.3 Tuning

1. Write the RTO/RPO in **user** units, then subtract DNS/cache and reconnect — the remainder is what the engine and probes may spend.
2. LB/kubelet path: **liveness + local only**. Put dependency checks on a central actor with a rate limit and a human threshold (Yanacek; DynamoDB/S3/RDS teams).
3. Asymmetric thresholds (ALB 2 down / 5 up; Envoy startup one-success) so recovery is slower than eject — the opposite of a flappy breaker **[→breaker]**.
4. Prioritize the ping under overload: extra workers beyond proxy max-connections; or a background flag plus a dead-man on that thread (Yanacek).
5. Set DNS TTL ≤ 60 s on anything you fail over; set JVM `networkaddress.cache.ttl` **before** the first connect; prefer a proxy that ignores OS/JVM caches if RTO < 60 s.
6. Prefer data-plane traffic shift (Route 53 health-checked records, ARC routing controls) over control-plane weight edits.
7. Exercise the failover **on purpose**. REL13 and GitHub’s own write-up: untested topology assumptions (promote-across-region) are the incident.
8. Revisit after a week of `t_detect` / fail-open / lag histograms. A probe that never fails is as wrong as one that fails at p50.

### 5.4 Placement

| Layer | What it isolates | State / scope | Trade-off |
|---|---|---|---|
| **Process liveness** (kubelet, systemd) | Deadlock / stuck PID | Per container | Restarts; cascade if the check is a dependency |
| **Readiness / EndpointSlice** | This Pod as a backend | Per Service | Fail-closed; all-unready = no endpoints |
| **Sidecar active check** (Envoy) | This host in *this* proxy’s cluster | Per sidecar | Required knobs; `UNKNOWN`=`HEALTHY`; not fleet-coordinated |
| **LB active check** (ALB/NLB) | This target in the TG | Per LB node | Coarse; **fail-open**; NLB also drops an AZ from DNS |
| **Mesh outlier detection** | Bad host via *request* errors | Per sidecar | **C1**, not this card |
| **DNS health** (Route 53) | This record in answers | Global checkers, **>18%** | TTL + stub resolvers dominate; fail-open group rule |
| **Client health** (gRPC Watch) | This subchannel | Per channel | Fail-closed; `pick_first` may ignore it |
| **DCS lock** (Patroni ttl, Orchestrator) | Who is primary | Cluster | Timeout **is** the split-brain window unless storage fences |
| **Central monitor + rate limit** | Dependency / anomaly | Fleet | Slow; safe; needs a human threshold |
| **Policy fence** (no cross-region promote) | Topology the app cannot survive | Operator config | GitHub’s actual fix |

---

## 6. Worked calibration — checkout → payment (design drill)

Constraints are a **design drill**, not a vendor SLA. Method: Yanacek placement + REL13 RTO/RPO subtraction + the detection inequality in §3.4 + Aurora/RDS published ranges (fetched 2026-09-13).

Business: checkout accept **RTO 120 s**, payment capture **RPO 5 s**. Stack: three-AZ checkout (ALB → K8s), payments on **Aurora** (writer + two readers, two AZs minimum) in one Region; regional DR is **pilot light** (out of the 120 s budget — do not pretend otherwise).

| Decision | Choice | Why |
|---|---|---|
| AZ capacity | 3 AZ, +50% (each AZ ≤ 66% load-tested) | Static stability; AZ loss must not call the ASG control plane |
| K8s liveness | httpGet `/live` — process + disk; period 10, timeout 1, fail 3 | Local only. ~31 s to restart a deadlock. Not the payment DB. |
| K8s readiness | `/ready` — listen socket + in-process caches; period 5, fail 3 | Traffic gate. Dependency (Aurora) **not** on this path. |
| K8s startup | same as `/live`, fail 30 × 10 s = 300 s | Slow image vs tight liveness |
| ALB TG | interval **10 s**, timeout **3 s**, unhealthy **2**, healthy **5**, matcher 200 | `t_detect` ≈ 13–23 s, inside the 120 s budget. Default 30/5/2 would spend **65 s** before Aurora has even failed over. |
| Check depth on ALB | `/ready` (local) | Deep `/ready` that SELECTs 1 from payments turns Aurora latency into a fleet-wide ALB fail-open flap |
| Aurora | Multi-AZ readers; connect via **cluster endpoint** + RDS Proxy | Published promote **< 60 s / often < 30 s**; Proxy’s “66%” only helps the DNS term |
| DNS / JVM | Route 53 TTL **60**; `networkaddress.cache.ttl=5` at process start | Hidden term. Without it, 120 s is already gone |
| Regional DR | Pilot light, **push-button** (ARC), not health-check automatic | REL13 caution; 120 s RTO is **intra-Region** only |
| RPO 5 s | Aurora in-Region storage (six copies) covers AZ loss; Global Database is a *different* (regional) RPO, typical **< 1 s** lag if we later add it | Do not advertise 5 s RPO across a Region cut without measuring `AuroraGlobalDBRPOLag` at drill |

Budget: ALB detect ~20 s + Aurora promote ~30 s + DNS/Proxy ~10 s + reconnect ~10 s ≈ **70 s** typical, **< 120 s** if JVM cache is not infinite. Default ALB 65 s + Aurora 60 s + TTL 60 s + JVM-never = **an RTO you did not choose**.

Hedging/retry of `POST /capture` is **C2** (idempotency). Brownout of the checkout page is **C11**. Outlier ejection of one payment replica is **C1**.

---

## 7. Failure modes and when-not-to-use

1. **Shallow check, fast-fail black hole.** Yanacek blank pages; least-requests (C5) amplifies. Local check must see *correct* responses, not just a 200 from the proxy.
2. **Deep check on the LB path.** Shared-dep blip ejects the fleet; fail-open may not trigger if only a *fraction* fail (Yanacek flap). Soft dep becomes hard.
3. **Liveness that checks a neighbour.** K8s documented cascade: restart under load → less capacity → more restarts.
4. **Startup budget stuffed into liveness.** Deadlocks wait out a 300 s window; or slow starters get killed every 30 s. Split the probes.
5. **httpGet success on a cross-host redirect / 11+ redirects / 10 KiB close.** Probe green, app logs look like a network fault.
6. **Fail-open you did not know you had.** ALB/NLB all-unhealthy; NLB empty TG; Route 53 group rule; Disabled check = always healthy; Envoy `UNKNOWN`. Dashboards show 200s to dead targets.
7. **Fail-closed at the wrong layer.** All Pods unready because the one DB is slow → ClusterIP has no endpoints while the LB above is still green (or vice versa).
8. **DNS/JVM cache longer than the failover.** Engine flipped; clients still write the corpse. GitHub-scale version: apps *did* flip, to the wrong coast.
9. **Automatic failover on a gray health signal.** REL13 / DR whitepaper: false failover costs RPO. Prefer push-button data-plane (ARC).
10. **Control plane on the recovery path.** ASG scale-out, weight edits, “launch more in the good AZ.” Static-stability miss.
11. **Pilot light advertised as warm standby.** Cannot take traffic until you provision. REL13’s own distinction.
12. **Active/active writes without a conflict story.** REL13: last-writer-wins / partitioned writes / “avoid or handle.” Corruption still needs backups.
13. **Split-brain.** Timeout declared death; zombie still writes. GitHub 43 s / 954 writes. Fence with a token ([quorums-and-fencing.md](../../../cases/data-intensive-design/quorums-and-fencing.md)) or a topology policy, not hope.
14. **Patroni inequality broken**, or `primary_start_timeout=300` vs an RTO of a minute.
15. **TLS 1.3-only NLB HTTPS checks**, Route 53 HTTPS without cert validation (expired cert still “healthy”), ALB matcher 200 vs a 204 endpoint.
16. **Queue workers without a work-producer check.** Unhealthy consumer still pollutes the queue **[→C3-1]**.
17. **Zombie after partition.** Old code, old schema. Yanacek: put version on the health response; refuse re-admit.
18. **Health checks not prioritized under overload.** Timeouts fire, fleet shrinks, downward spiral (Yanacek). C11 owns the brownout *response*; C3 owns not ejecting yourself.

**When a health check is the wrong tool.** Deciding *whether to call* a dependency (breaker, **C1**). Bounding *how long* to wait (**C7**). Shedding load (**C10**). Serving stale (**C11**). Choosing among healthy backends (**C5**). Fencing a zombie writer (the DDIA case). In-process resources (Azure’s “not suitable” for breakers applies here too **[→breaker]**).

**When automatic failover is the wrong tool.** Cross-region promote when the app cannot bear the RTT (GitHub). Gray failures. Any path whose fence is “we will reconstruct from backups” — that is restore, not failover. RTO that is smaller than `t_detect + TTL`.

---

## 8. Cross-links

| Id | Why |
|---|---|
| **C1** circuit breaker | Outlier detection / panic / ALB fail-open *tuning* live there; a health check is not a breaker |
| **C2** retry | Do not retry an endpoint the LB just failed over away from without a budget |
| **C5** load balancing | Least-requests black hole; this note only motivates a *correctness* check |
| **C7** timeouts | Probe `timeoutSeconds` / ALB 5 s are knobs, not timer kinds |
| **C8** bulkhead | A failed-open LB dumps everyone into one remaining AZ |
| **C10** load shedding | Prioritize the ping; do not use “fail the probe” as a shed |
| **C11** degradation / kill switches | First-pass §§4–5; GitHub paused webhooks/Pages as *degradation*, not as failover |
| **D3 / D4** | Reason codes, consensus %, remaining RTO terms |
| First-pass C3+C11 | [failover-degradation-external-research.md](failover-degradation-external-research.md) |
| Cases | [quorums-and-fencing.md](../../../cases/data-intensive-design/quorums-and-fencing.md), [process-pauses.md](../../../cases/data-intensive-design/process-pauses.md), [unreliable-networks.md](../../../cases/data-intensive-design/unreliable-networks.md), [single-leader-replication.md](../../../cases/data-intensive-design/single-leader-replication.md), [timeouts-and-delays.md](../../../cases/data-intensive-design/timeouts-and-delays.md) |

### Recommended split

**Keep on C3 (this card):** health-check taxonomy and K8s mapping; fail-open vs fail-closed; active/passive vs active/active; RTO/RPO + DR tiers; DNS TTL + LB failover; verified engine timings; split-brain **as the failure mode** (GitHub 2018 + “name the fence”).

**Do not duplicate on C3:** fencing tokens, leases, sequencers/epochs/terms — already a complete case in [quorums-and-fencing.md](../../../cases/data-intensive-design/quorums-and-fencing.md).

**Future card (only if a Concept cannot stay near CircuitBreaker length):** “Fencing & HA-cluster failover” covering Pacemaker/STONITH *ops*, Patroni DCS-lock races, Orchestrator/Raft promote policy, and the GitHub topology fence — still *citing* the DDIA case, not re-deriving tokens. **Do not split yet.** The first C3 Concept should keep split-brain in Failure modes and link the case. C11 stays its own card (already paired in the first pass).

---

## 9. Sources

Fetched 2026-09-13 unless noted.

**Canon.** builder.aws.com/content/3Ev53O39izHCtWLzp4XU6t8PC1O/implementing-health-checks (Yanacek; live `aws.amazon.com/builders-library` HTML was not used this pass) · aws.amazon.com/builders-library/static-stability-using-availability-zones (Weiss & Furr; 50% / 66%) · docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_disaster_recovery.html (REL13-BP02) · docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html · github.blog/2018-10-30-oct21-post-incident-analysis · kubernetes.io/docs/concepts/workloads/pods/probes (and v1-36 snapshot).

**DNS / LB / mesh / RPC.** docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-determining-health-of-endpoints.html · …/health-checks-how-route-53-chooses-records.html · …/dns-failover-types.html · docs.aws.amazon.com/Route53/latest/APIReference/API_HealthCheckConfig.html · docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html · …/network/target-group-health-checks.html · envoyproxy.io/docs/envoy/latest/api-v3/config/core/v3/health_check.proto (1.40.0-dev) · grpc.io/docs/guides/health-checking · aws.amazon.com/blogs/networking-and-content-delivery/choosing-the-right-health-check-with-elastic-load-balancing-and-ec2-auto-scaling (shallow/deep vocabulary).

**Databases.** docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.Failover.html (60–120 s; JVM TTL) · …/multi-az-db-clusters-concepts-failover.html (< 35 s) · docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Concepts.AuroraHighAvailability.html (< 60 / often < 30; < 10 min; Proxy 66%) · …/aurora-global-database.html · …/aurora-global-database-disaster-recovery.html (RTO minutes; switchover RPO 0; failover RPO seconds; ≤ 10 secondaries; typical < 1 s lag) · patroni.readthedocs.io/en/latest/dynamic_configuration.html.

**Cited forward.** [failover-degradation-external-research.md](failover-degradation-external-research.md) (gRPC protocol Watch `SERVICE_UNKNOWN` / Check `NOT_FOUND`; K8s `publishNotReadyAddresses` / Local traffic policy; Pacemaker 2.1 STONITH; Envoy outlier / Istio `minHealthPercent` / ALB `minimum_healthy_targets` **[→breaker]**) · [circuit-breaker-external-research.md](circuit-breaker-external-research.md) · [quorums-and-fencing.md](../../../cases/data-intensive-design/quorums-and-fencing.md).

---

## 10. Uncertain / left out

- Live `aws.amazon.com/builders-library/implementing-health-checks` HTML not used; Yanacek quotes are from the Builder Center copy. Publication date of the original Library article not shown.
- Route 53 developer-guide “up to **255** child health checks” vs API `ChildHealthChecks` max **256** items / `HealthThreshold` max 256. This note asserts the API maxima; the 255 wording is not reconciled.
- Patroni `maximum_lag_on_failover` **default**: official dynamic-config page lists the knob without a number. First-pass **1 MiB** remains **unasserted**. `failsafe_mode` / `synchronous_mode` defaults are from that page (`false` / documented values `off|on|quorum`; implied off unless set).
- Aurora FAQ “promote secondary in under a minute” vs DR page “typically a few minutes.” Only the DR-page wording is used for procedure time; FAQ line is not treated as an SLO.
- RDS Proxy “up to 66%” is a vendor reduction claim, not a measured distribution.
- REL13 “RTO in 24 hours or less” / “RPO in hours” are **tier labels**, not SLAs. The checkout table is a drill.
- K8s ClusterIP with zero ready endpoints: first pass could not verify an active *reject*; still not asserted.
- `publishNotReadyAddresses`, Local traffic policy, Pacemaker fencing details, gRPC `SERVICE_UNKNOWN` / Check `NOT_FOUND`: **[→C3-1]**, not re-fetched.
- Envoy `no_traffic_healthy_interval` vs `no_traffic_interval` interaction beyond the proto comments: not labbed.
- NLB “targets receive more than the configured number of health checks”: no multiplier published; not invented.
- JVM default TTL “varies by version and security manager” — only the RDS warning and the ≤ 60 s recommendation are asserted.
- Azure / GCP / HAProxy / Consul / Spring Actuator probe defaults: not in scope this pass (would be the next deepen if a multi-cloud Concept needs them).
- Φ accrual, lease-vs-timeout math: stay in the DDIA cases.
- C11 material (RFC 5861, brownout, OpenFeature, kill switches, SRE ch. 22 degradation): first pass only.
