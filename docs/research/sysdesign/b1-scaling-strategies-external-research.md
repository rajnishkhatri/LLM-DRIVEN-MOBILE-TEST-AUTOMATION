---
type: research
title: 'Scaling strategies — external research (2026-09-13)'
description: >-
  Source-verified research for catalog B1: vertical vs horizontal scale-up
  limits, Little's law L = λW (Little 1961 / Kleinrock), M/M/1 and M/M/c
  queueing, and current autoscaling defaults (K8s HPA/VPA, KEDA 2.20.2,
  AWS ASG, Cloud Run, Azure Monitor, Cluster Autoscaler) as of 2026-09-13.
tags: [research, system-design-patterns, B1, scaling-strategies]
---

# B1 Scaling strategies — external research (2026-09-13)

> **What this is.** Evidence pass for catalog B1 (vertical/horizontal scaling, autoscaling, Little's law) at the Group B / CircuitBreaker depth bar. The Concept will carry the distilled result; this note keeps verified facts, defaults, and URLs. **Link, do not rewrite** [scalability.md](../../../cases/data-intensive-design/scalability.md).
>
> **Method.** Primary pages fetched 2026-09-13. Paraphrase; numbers reproduced exactly. **(cite-forward)** = already verified in sibling research notes this cycle. Unverified items live in §8 and are not facts.

---

## 1. Scope and non-goals

**Owns.** How to add *capacity* when load grows: scale-up vs scale-out, the queueing identity that sizes concurrency (`L = λW`), high-level M/M/1 and M/M/c behaviour, and the autoscaling loops that turn a metric into replicas (Kubernetes HPA / VPA / Cluster Autoscaler, KEDA, AWS EC2 Auto Scaling, Cloud Run, Azure Monitor autoscale). Worked calibration: given `λ` and `W`, compute in-flight concurrency and a replica count. Failure modes of the *scaler itself* (cold start, metric lag, thundering herd, flapping, downstream saturation).

**Does not own.** How data is split or copied — **B2** (do not re-derive sharding, rebalancing, or request routing). Cache hit-rate as a load reducer — **B3**. Spreading requests across already-running instances — **C5**. What to do when capacity cannot be added in time — **C10** (shed / backpressure) and **C8** (bulkhead the pool you already have). Style-level "how many services / cells / functions" — **E2 / E11 / E13**. Fleet instrumentation — Group D.

---

## 2. Lineage / vocabulary

**Kleppmann / this tree's scalability note** (link, do not rewrite). Scalability is the ability to cope with increased load — not a yes/no label. Name the load parameters first (RPS, bytes/day, concurrent users, read/write ratio, cache hit rate), then ask what happens if they grow with resources held constant, and how many resources it takes to hold performance constant. **Vertical scaling / scale-up** = a more powerful machine. **Shared-memory** parallelism on one box; cost typically grows *faster than linearly*, and bottlenecks mean twice the hardware rarely yields twice the load. **Shared-disk** = independent CPU/RAM, contended NAS/SAN. **Shared-nothing / horizontal / scale-out** = each node owns CPU, RAM, and disks; coordination is software over a conventional network — that *buys a distributed system* (explicit sharding is B2). Linear scalability is the happy case. Design for the next **10×**, not an imaginary 1000×; there is no generic "magic scaling sauce." If load is predictable, a manually scaled system may have fewer operational surprises than autoscaling.

**Azure Architecture Center, "Autoscaling Guidance"** (fetched 2026-09-13). **Vertical** = change the capacity of a resource — often a temporary outage while the system is redeployed; "less common to automate." **Horizontal** = add or remove instances — the application keeps running. Autoscaling "mostly applies to compute"; horizontally scaling a database or queue "usually involves data partitioning, which is generally not automated" (B2). Four components: instrumentation, decision logic, an *external* actuator (idle or overwhelmed code must not scale itself), and a tuning loop. Related patterns it names: Throttling (use *with* autoscaling when the burst outruns provision time — C10), Competing Consumers (A2).

**Little, "A Proof for the Queuing Formula: L = λW"** (*Operations Research* 9(3):383–387, published online 1961-06-01, DOI 10.1287/opre.9.3.383). If mean inter-arrival `1/λ`, mean population `L`, and mean sojourn `W` are finite, the processes are strictly stationary, and the arrival process is metrically transitive with nonzero mean, then **`L = λW`**. Distribution-independent: arrival process, service distribution, and discipline drop out. 50th-anniversary revisit: Little, *OR* 59:536–549 (2011). Stidham's generalisation: "A Last Word on L = λW", *OR* 22:417–421 (1974).

**Kleinrock, *Queueing Systems* Volume 1: Theory** (Wiley 1975, ISBN 0471491101). Standard OR treatment of Kendall-notation models. Wikipedia's M/M/1 article (fetched 2026-09-13) cites it for the CTMC construction (p. 77) and the busy-period / sojourn analysis (p. 215). M/M/c is the multi-server extension of the same birth–death chain.

**Google SRE book + workbook.** The SRE book never uses the words "Little's law." What it states, and what the concurrency-limit literature maps onto `L = λW`:

- Ch. 6 *Monitoring Distributed Systems* (https://sre.google/sre-book/monitoring-distributed-systems): golden signals; **saturation** is "how full your service is"; "many systems degrade in performance before they achieve 100% utilization, so having a utilization target is essential." Averages hide imbalance: "a web service with an average latency of 100 ms at 1,000 requests per second, 1% of requests might easily take 5 seconds."
- Ch. 4 *Service Level Objectives* (https://sre.google/sre-book/service-level-objectives): QPS and latency "might be connected behind the scenes: higher QPS often leads to larger latencies, and it's common for services to have a **performance cliff** beyond some load threshold." High-order percentiles; "long-tail behavior, an effect exacerbated at high load by **queuing effects**."
- Ch. 21 *Handling Overload* (cite-forward [circuit-breaker](circuit-breaker-external-research.md)): utilization (CPU reserved, sometimes memory) drives rejection by criticality; executor load = smoothed count of active/runnable threads vs processors.
- Workbook ch. 11 *Managing Load* (https://sre.google/workbook/managing-load): Pokémon GO launch at ~50× the optimistic load-test; after the GCLB migration, true client demand was 200% above previously observed; synchronized client retries produced **20×** previous global RPS peaks. Autoscaling section: scale-up is "more important and less risky" than scale-down; most implementations are "intentionally more sensitive to jumps in traffic than to drops"; set min/max bounds; ship a **kill switch**; do not average utilization over unhealthy instances; horizontal scale does not help a **stateful** session pinned to one backend (task-level routing is C5; vertical scale is only a short-hotspot buffer, and because the resize is typically *uniform*, low-traffic instances grow too).

**Netflix concurrency-limits** (README fetched 2026-09-13; library 0.5.4 on 2025-12-08 cite-forward from the circuit-breaker note). Think in concurrent requests, not a static RPS token bucket: **"This relationship is covered very nicely with Little's Law where `Limit = Average RPS * Average Latency`."** Vegas / Gradient2 / AIMD then *adapt* that limit from delay. Same identity sizes bulkhead permits in [C8](bulkhead-isolation-external-research.md) §7.

**This tree's performance note** (link, do not rewrite) [performance.md](../../../cases/data-intensive-design/performance.md): response time = service time + queueing delay; as throughput approaches hardware maximum, queueing delays increase sharply; an overloaded system can enter a retry-storm / metastable loop ([7][8][9] in [nfr-references.md](../../../cases/data-intensive-design/nfr-references.md)).

---

## 3. Mechanics

### 3.1 Vertical vs horizontal

| Axis | What you add | Stays the same | Typical automation | Cost / complexity |
|---|---|---|---|---|
| **Scale-up** | CPU, RAM, disk, NIC on one unit (VM size, Pod requests, instance class) | Process identity, in-memory state, local disk, connection table | Rarely automated (Azure: often a redeploy/outage). K8s VPA is the exception, and it *recreates* Pods by default. | Price/performance of a high-end machine is worse than two mid ones; NUMA, lock contention, GC, memory bandwidth, and single-thread ceilings bind before the invoice does. |
| **Scale-out** | More identical units behind a balancer or competing-consumer queue | Per-unit size | The default cloud autoscaler target | Buys a distributed system: session affinity, membership, and (for stateful data) B2 partitioning. |

**Scale-up limits (verified).** Individual CPU cores "are no longer getting significantly faster" ([scalability.md](../../../cases/data-intensive-design/scalability.md)); you buy *more* cores on one box, and they share RAM — lock, cache-coherence, and GC pauses do not scale with core count. Azure: a vertical change "often requires making the system temporarily unavailable while it's being redeployed." Cloud Run (https://docs.cloud.google.com/run/docs/about-concurrency, updated 2026-09-09): CPU-based autoscaling averages **across all vCPUs on the instance**. A single-threaded app on a multi-vCPU instance shows deceptively low average utilization ("vCPU hotspots") and will not scale out on CPU — drive scale from **concurrency** instead. HPA + VPA on the same CPU/memory metric fight: HPA wants more Pods when utilization is high; VPA wants bigger Pods, which *lowers* utilization and can stall HPA. Kubernetes treats them as alternatives for the same resource (or VPA `Off` / `Initial` as a recommender only).

Trade-off: scale-up preserves a single-node programming model until the box, the license, or the failure domain is the limit. Scale-out is what autoscalers actually automate. Mixing them is normal: a manually sized replica (VPA `Initial` or a reserved instance class) plus HPA/ASG/Cloud Run on replica count.

### 3.2 Little's law as a sizing identity

`L = λW` with consistent units. `λ` = long-run **effective** arrival rate (completions/sec in a stable system; if work is lost, throughput `X ≤ λ`). `W` = mean **sojourn** (queue + service), seconds. `L` = mean requests **in the system** — the concurrency the pool must hold.

| Need | Formula | Use |
|---|---|---|
| Concurrency / pool / in-flight | `L = λW` | Thread pools, connection pools, Cloud Run concurrency × instances, Envoy `max_requests` (C8 / C5). |
| Capacity given a latency SLO | `λ_max ≈ L_cap / W_slo` | Will not exceed `L_cap` in-flight and need `W ≤ W_slo`. |
| Utilization (1 server) | `ρ = λS` | `S` = mean *service* time, not sojourn. Stable iff `ρ < 1`. |
| Utilization (`c` servers) | `ρ = λS / c` | HPA/ASG "target utilization" is a proxy for keeping `ρ` off the cliff. |

The law does **not** say that raising `λ` leaves `W` unchanged. `W` is an observation. Near saturation, `W` grows (queueing), so `L` grows faster than `λ` — SRE's performance cliff. Netflix's `Limit = RPS × Latency` is Little applied to the *admission* cap: keep offered `L` at the onset of queueing, not at 100% CPU.

### 3.3 Queueing (M/M/1, M/M/c) — high-level

Kendall notation: `A/S/c` = arrival / service / server count. **M** = Markovian (Poisson arrivals or exponential service).

**M/M/1** (Kleinrock 1975; Wikipedia M/M/1, fetched 2026-09-13). Single server, infinite buffer, FCFS, Poisson `λ`, exponential `μ` (`S = 1/μ`). Stable only if `λ < μ`. Utilization `ρ = λ/μ`. Stationary `π_i = (1 − ρ) ρ^i`. Mean population `L = ρ / (1 − ρ)`. Mean sojourn via Little: **`W = 1 / (μ − λ)`**. Mean wait in queue `W_q = ρ / (μ − λ)`. As `ρ → 1`, both diverge: `ρ = 0.5 → L = 1`; `0.8 → 4`; `0.9 → 9`; `0.95 → 19`. That is why SRE wants a utilization *target* well below 100% and why Cloud Run defaults to 60% (§4). Kingman's heavy-traffic limit (1961): near `ρ = 1` the queue is approximately reflected Brownian motion — tails, not averages, dominate.

**M/M/c** (multi-server, one shared queue — the horizontal-scale cartoon). `c` exponential servers, same Poisson arrivals. Utilization `ρ = λ / (cμ)`; stable iff `ρ < 1`. Mean service time is still `1/μ`; what scale-out buys is a collapse of **queueing delay**, not of service time. Closed forms use the Erlang-C wait probability (Kleinrock Vol. 1); this note does not reproduce the series (§8). Operationally: `c` must satisfy `c > λS`, then extra servers are the headroom that keeps `ρ` on the flat part of `W(ρ)`. A single queue in front of `c` workers (competing consumers / one LB pool) beats `c` independent M/M/1s with random split — join-the-shortest-queue / P2C is C5.

**What the models are not.** Real services are G/G/c. M/M/* is a *lower bound* on how ugly queueing gets (exponential service is memoryless). Heavier tails make the same `ρ` worse. Use the models for order-of-magnitude and a utilization target, then measure.

### 3.4 Autoscaling as a delayed closed loop

Every managed scaler is the same loop with different sensors:

1. **Observe** a metric that *falls as you add instances* (CPU %, concurrent requests / max concurrency, queue depth **per replica**, ALB requests/target). Azure and AWS both warn: raw `RequestCount` or SQS `ApproximateNumberOfMessagesVisible` do **not** work — they do not change proportionally with fleet size.
2. **Recommend** `desired = f(current, target)` (HPA ratio; Cloud Run per-driver instance formula; ASG target tracking).
3. **Stabilize** so noise and cold-start CPU do not flap the fleet (HPA windows; ASG warmup; KEDA cooldown-to-zero; Cloud Run 1- and 15-minute idle shutdowns).
4. **Actuate** a replica count, then wait for Ready / `InService` / serving. That wait is why autoscaling loses to a burst (Azure: "autoscaling isn't an instantaneous process"; SRE: "creating new instances is never instant").
5. **Bound** with `minReplicas` / `maxReplicas`. Unbounded scale-out is a quota-exhaustion and backend-overload bug (SRE workbook "Setting Constraints"; Cloud Run "Autoscaling impact on backing services"; Azure "limit the maximum number of instances").

Cloud Run names two mechanisms every other scaler has an analogue of. **Metrics-based** — periodic, averaged, "keep `ρ` ≈ target." **On-demand / pending-queue** — a request arrived and no slot exists. Cloud Run's on-demand path is the *only* driver from zero; a request pends for `max(10 s, 3.5 × predicted cold-start)` before a new instance starts, and fails **429** if still pending (https://docs.cloud.google.com/run/docs/about-instance-autoscaling, updated 2026-09-09). KEDA splits the same idea across two controllers: KEDA polls triggers every `pollingInterval` **while at zero**; from 1→N the Kubernetes HPA takes over (default sync 15 s).

---

## 4. Verified defaults / standards (fetched 2026-09-13)

### 4.1 Kubernetes HPA (`autoscaling/v2`)

Primaries: https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/ and the v2 API reference.

| Knob | Default | Notes |
|---|---|---|
| Controller sync | `--horizontal-pod-autoscaler-sync-period` **15 s** | Not continuous. |
| Algorithm | `desiredReplicas = ceil(currentReplicas × currentMetric / desiredMetric)` | Largest recommendation wins if multiple metrics. |
| Tolerance | **0.1** (10%) via `--horizontal-pod-autoscaler-tolerance` | Skip if ratio is within 1.0 ± tolerance. Per-direction `behavior.*.tolerance` is **stable since v1.37** (`HPAConfigurableTolerance`; first in v1.33). |
| Default metric if `metrics` omitted | **80%** average CPU utilization | API reference. Walkthroughs often show 60%. |
| `minReplicas` | **1** | `0` allowed only with ≥ 1 Object or External metric. |
| Scale-up stabilization | **0 s** | Act on the first up recommendation. |
| Scale-down stabilization | **300 s** | Highest recommendation in the window (`--horizontal-pod-autoscaler-downscale-stabilization` default 5 min). |
| Scale-up velocity | **+100% or +4 Pods every 15 s**, `selectPolicy: Max` | Concepts "Default behavior" YAML. |
| Scale-down velocity | **−100% every 15 s** (down to `minReplicas` after stabilization) | |
| CPU init exclusion | `--horizontal-pod-autoscaler-cpu-initialization-period` **5 min**; `--horizontal-pod-autoscaler-initial-readiness-delay` **30 s** | New Pods' CPU ignored while unready / recently ready. |
| Missing metrics | Conservative: treat missing as 100% of target on scale-down, 0% on scale-up | Dampens both directions. |
| Scale-to-zero | `HPAScaleToZero` **beta, on by default in v1.37** (blog 2026-09-02) | Object/external metrics only — not CPU/memory. `ScaledToZero` condition vs manual `replicas: 0`. |

API-reference inconsistency (§8): `HorizontalPodAutoscalerBehavior.scaleUp` prose still says "4 pods per **60** seconds / double per **60** seconds"; `HPAScalingRules.policies` and the concepts default YAML both say **15 s**. This note uses the concepts YAML. HPA does not apply to DaemonSets. Binding HPA to a Deployment and leaving `spec.replicas` in the manifest causes apply-time fights (docs: remove `spec.replicas`; default 1 if you strip it carelessly).

### 4.2 Kubernetes VPA (`autoscaling.k8s.io/v1`, not in core API)

https://kubernetes.io/docs/concepts/workloads/autoscaling/vertical-pod-autoscale/ — Recommender (target / lower / upper from history + OOM), Updater (evict or in-place), Admission webhook (applies target on create). Requires Metrics Server.

| Knob | Default / current |
|---|---|
| `updateMode` if omitted | **`Recreate`** (evict when request diverges "significantly"; respects PDB) |
| `Auto` | **Deprecated since VPA 1.4.0**; alias of `Recreate` |
| `InPlaceOrRecreate` | In-place resize, fall back to eviction; needs `InPlacePodVerticalScaling` |
| `InPlace` | Alpha in **VPA 1.7.0**, Kubernetes **≥ 1.33**; never evicts |
| `controlledResources` | CPU and memory if unset |
| `controlledValues` | **`RequestsAndLimits`** (limits scale with the request/limit ratio) |
| LimitRange | Admission/updater clamp recommendations to Pod/Container LimitRanges |

### 4.3 KEDA ScaledObject (latest release **v2.20.2**, 2026-07-31; `/docs/latest/` fetched)

https://keda.sh/docs/latest/reference/scaledobject-spec/

| Knob | Default |
|---|---|
| `pollingInterval` | **30 s** (KEDA-owned while replicas = 0) |
| `cooldownPeriod` | **300 s** after last *active* trigger before scale **to 0** |
| `initialCooldownPeriod` | **0 s** |
| `minReplicaCount` | **0** (the YAML *example* writes `1`; the field default is 0) |
| `maxReplicaCount` | **100** |
| `idleReplicaCount` | ignored; only **0** is supported (HPA limitation) |
| `fallback.behavior` | `"static"` (section requires `failureThreshold` + `replicas`) |
| `restoreToOriginalReplicaCount` | **false** |
| Generated HPA name | `keda-hpa-{scaled-object-name}` |
| Trigger `metricType` | `AverageValue` (CPU/memory also allow `Utilization`) |
| `useCachedMetrics` | **false** |

1→N behaviour is whatever HPA default you did not override (`advanced.horizontalPodAutoscalerConfig.behavior`). KEDA's cooldown does **not** apply to 1→N.

### 4.4 AWS EC2 Auto Scaling

| Knob | Default | Source |
|---|---|---|
| `DefaultCooldown` | **300 s** | CFN / `CreateAutoScalingGroup`. **Only simple scaling policies** honour it. AWS now recommends *against* simple scaling + cooldowns. |
| Target tracking / step | **No cooldown.** Scale-out immediately; scale-in blocked while instances warm. | Cooldown + target-tracking guides |
| `DefaultInstanceWarmup` | **unset / null** ("not enabled or configured by default") | https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-default-instance-warmup.html — if null, target-tracking/step fall back to `DefaultCooldown` (300 s); instance refresh falls back to the health-check grace period; predictive scaling has **no** default warmup. Suggested starting value if unsure: **300 s**. |
| Health-check grace | **300 s in the console; 0 s via CLI / SDK / CloudFormation** (`0` = off) | https://docs.aws.amazon.com/autoscaling/ec2/userguide/health-check-grace-period.html |
| ELB deregistration delay | **300 s** (simple-scaling cooldown starts when deregistration *begins*, not when it finishes) | Cooldown guide |
| Target-tracking predefined metrics | `ASGAverageCPUUtilization`, `ASGAverageNetworkIn/Out`, `ALBRequestCountPerTarget` | Need `ResourceLabel` for ALB |
| EC2 metric period | **5 min** unless **detailed monitoring** (1 min) is enabled | Target-tracking "Choose metrics" — AWS *recommends* detailed monitoring for CPU |
| Multiple target-tracking policies | Scale **out** if *any* policy wants out; scale **in** only if *all* (with scale-in enabled) agree | Availability-first, same shape as Azure |
| `DisableScaleIn` | **false** | |
| `ALBRequestCountPerTarget` = 0 | Group **can** scale to 0 if `min` = 0 | |
| Unusable metrics for target tracking (verbatim) | LB `RequestCount`, LB `Latency`, SQS `ApproximateNumberOfMessagesVisible` | Need a *per-instance* custom metric for SQS |

### 4.5 Cloud Run (docs last-updated 2026-09-09 / 2026-09-10)

| Knob | Default |
|---|---|
| Min instances | **0** (scale to zero). Docs recommend **≥ 1** if the process uses CPU off-request; **≥ 3** as a high-availability *best-effort* floor (zone capacity, rebalancing, crash-loops, and quota can still drop below it). |
| Max instances | **100 per revision** |
| Max concurrency | Console: **80**. gcloud / Terraform **on first create only**: **80 × vCPUs**. Subsequent deploys do not reset it. Hard cap **1,000**. Set **1** if the process is not concurrency-safe. |
| CPU target / concurrency target | **60%** each (range 10–95% via scaling-controls *Preview*) |
| CPU window | Average CPU/s over **1 minute** / CPUs per instance / CPU target |
| Concurrency window | `max(1-minute avg, 10-minute avg)` concurrent requests / max concurrency / concurrency target |
| Scale-up | `max` of the two drivers. On-demand path from zero. Pending queue: `max(10 s, 3.5 × predicted cold start)` then start an instance; **429** if still pending. |
| Scale-down | Deprioritize unrecommended instances. Shut a group when 1-minute utilization **< 10%**. A second group stays until a **15-minute** idle timeout (10 minutes for GPUs). |
| Adaptive concurrency tuning (ACT) | If CPU over last **1 s > 90%**, lower that instance's max concurrency by 1. If at the cap and CPU **< 70%** for 1 s, raise by 1. Values **do not persist across deployments** and **are not observable**. |
| Memory as a scale driver | **Not supported** |
| Exceeding max instances | Allowed briefly (traffic spikes, replacements); grace typically **≤ 15 min** or the request timeout; extras "normally less than twice" the configured max. Traffic splits and new-revision warm-up can make *service* instance count exceed *per-revision* max. |

### 4.6 Azure Monitor autoscale (VMSS, App Service, …)

https://learn.microsoft.com/azure/architecture/best-practices/auto-scaling and https://learn.microsoft.com/azure/azure-monitor/autoscale/autoscale-best-practices (fetched 2026-09-13).

| Knob / rule | Verified text |
|---|---|
| Default aggregation window | **45 minutes** for Cloud Services and Virtual Machines; "periods of less than **25 minutes** might cause unpredictable results." App Service averaging is shorter — new instances "in about **five minutes**." |
| Scale-out vs scale-in, multiple rules | Out if **any** rule fires; in only if **all** in-rules fire. Conflicting profiles: largest increase wins; smallest decrease wins; out beats in. |
| Flapping guard | Engine computes post-scale-in load; skips an in-action that would immediately require out (worked 80%/60% / 2→3 instance example). Logs `Flapping` (aborted) or `FlappingOccurred` (scaled to a different count). |
| Safe `default` instance count | Used when the metric cannot be read: scale **out** to default if below it; **never** scale in toward it. |
| Manual scale | Temporary; next run clamps back into `[min, max]`. |

### 4.7 Cluster Autoscaler (node layer under HPA)

Constants from `sigs.k8s.io/cluster-autoscaler/pkg/config` and the AKS / EKS tables (fetched 2026-09-13): `scan-interval` **10 s**; `scale-down-unneeded-time` **10 min**; `scale-down-unready-time` **20 min**; `scale-down-delay-after-add` **10 min**; `scale-down-delay-after-failure` **3 min**; `scale-down-utilization-threshold` **0.5**. HPA can want Pods in seconds; those Pods stay `Pending` until CA provisions a node (EKS BP: an EC2 node often takes ~2 minutes). That gap is a first-class autoscaling failure mode (§5).

### Observability

Minimum dashboard (signals, not a vendor pack): `desiredReplicas` vs `currentReplicas` vs Ready/`InService` (lag and stuck-unready — SRE: averaging unhealthy instances freezes the scaler); scaling metric vs target (detect vCPU hotspot or SQS depth not divided by fleet); in-flight `L` (or `λ × W` reconstructed) vs pool size (if observed concurrency ≪ `λW`, you are losing work or mis-measuring `W`); admission rejects (429 / `UNAVAILABLE` / Envoy overflow — on-demand path or C10; Cloud Run pending-queue 429s); scale events + reason (HPA conditions, ASG activities, Azure activity log `Flapping`); cold-start / warmup P99 (sets HPA CPU-init period, ASG warmup, Cloud Run pending window); downstream saturation (DB connections, quota). HPA reports *unadjusted* average utilization in status even when it damped the decision for not-ready / missing pods — do not treat status CPU as the number the controller used.

### Tuning

| Symptom | First knob | Trade-off |
|---|---|---|
| Flapping / thrash | Widen HPA down-stabilization; Azure in/out threshold margin; ASG warmup | Leftover capacity vs oscillation |
| Burst overshoots SLO, then scaler moves | Wrong *metric* (CPU lags concurrency / queue depth); or scale-up stabilization > 0 when you needed 0 | Queue/concurrency overshoots more; CPU is smoother and later |
| New replicas cause *more* scale-out | Startup CPU in the average — raise HPA cpu-initialization-period / ASG warmup / Cloud Run min instances | Slower reaction to real CPU growth |
| Scale-to-zero, then a latency cliff | KEDA `pollingInterval` + cold start; Cloud Run pending window; set `minReplicaCount` / min instances | Idle cost |
| Scale-out does nothing | CA pending nodes; `maxReplicas`; quota; HPA missing CPU requests; ASG `INSUFFICIENT_DATA` | |
| Scale-out kills the database | Cap `maxReplicas` at `downstream_budget / per_replica_cost` (Cloud Run backing-services note; SRE "Avoiding Overloading Backends") | Compute availability vs data availability |
| Single-threaded multi-CPU | Lower Cloud Run concurrency; HPA on QPS / in-flight, not CPU | More instances, higher cost, actually moves |

Scheduled / predictive capacity (Azure scheduled profiles; AWS predictive scaling; KEDA cron / Elastic Forecast scaler in 2.20) is the correct answer to *known* peaks — SRE workbook and Azure both say combine schedule (be there before the peak) with reactive (catch the unforecast residual). Predictive AWS policies have **no** default warmup unless you set `DefaultInstanceWarmup`.

### Worked calibration

Units: seconds. Little's law first, then a replica count, then an M/M/1 warning.

**Given.** `λ = 200` requests/s, measured mean sojourn `W = 100 ms = 0.1 s` (stable period — not the incident tail).

1. **In-flight concurrency** `L = λW = 200 × 0.1 = 20`. That is the mean number of requests that must live in pools, threads, Cloud Run slots, or Envoy `max_requests`. Netflix `Limit ≈ 20`. C8's bulkhead note uses the same pair (200 req/s × 100 ms ≈ 20 permits).
2. **Replica count at a concurrency cap.** Cloud Run / HPA-on-concurrency: each instance advertises `C_max = 80` (console default) and the platform targets 60% of that. Required instances `≈ L / (0.60 × 80) = 20 / 48 ≈ 0.42` — one instance is enough *on the mean*, which is why you still set `min ≥ 1` (or 3) and size for the *tail* of `W`, not the mean. Using p99 sojourn `W_99 = 400 ms`: `L_99 ≈ 200 × 0.4 = 80`, `instances ≈ 80 / 48 ≈ 1.7 → 2` (plus min/max and a node).
3. **HPA CPU example (docs' own numbers).** 10 replicas, target 60% CPU, observed 72%: `desired = ceil(10 × 72/60) = 12`. Ratio `1.2` is outside the 10% tolerance, so the controller moves. A 63% reading (`ratio = 1.05`) would not.
4. **M/M/1 cliff, same `λ`.** One replica, exponential service `S = 4 ms` so `μ = 250 /s`: `ρ = 200/250 = 0.80`, `W = 1/(250 − 200) = 20 ms`, `L = 0.8/0.2 = 4`. Service slows to `S = 4.8 ms` (`μ = 208.3 /s`): `ρ = 0.96`, `W = 1/(208.3 − 200) ≈ 120 ms`, `L ≈ 24`. A 20% service-time regression turned a fine system into one that needs 6× the concurrency. Horizontal scale (M/M/c) buys `ρ` back: five replicas at the original `μ` give `ρ = 200/(5 × 250) = 0.16` — queueing delay nearly vanishes; sojourn collapses toward `S`. That is the whole point of HPA.
5. **Headroom vs utilization target.** Cloud Run / many HPA walkthroughs use 60%; SRE wants the service "far from key system bottlenecks." `c > λS / ρ_target`. For `λ = 200 /s`, `S = 4 ms`, `ρ_target = 0.6`: `c > 200 × 0.004 / 0.6 ≈ 1.33` → 2 replicas at that size, not 1.

Do not use this arithmetic on a *shard-local* hotspot and then add replicas that cannot see the hot key — that is B2.

---

## 5. Failure modes and when-not-to-use

**When autoscaling fails (even when the math is right).**

| Failure | Mechanism | What actually works |
|---|---|---|
| **Cold start** | On-demand from 0: image pull, JIT, connection cache, TLS. Cloud Run pending window then 429; KEDA waits up to a full `pollingInterval` (30 s) before it *notices* work. | `min instances` / `minReplicaCount ≥ 1`; warmup / CPU-init exclusion so the new replica is not immediately "hot" in the average. |
| **Thundering herd / dogpile** | Clients retry in sync (Pokémon GO 20× RPS; Nygard *Dogpile* / *Force Multiplier*). The scaler sees a false `λ` and overshoots, or the LB retries (GCLB retried GET on timeouts) amplify further. | Jittered backoff + retry budget (C2); shed (C10); **do not** let the scaler chase the retry spike to `maxReplicas`. |
| **Metric lag** | HPA 15 s sync + Metrics Server scrape; ASG 5-minute EC2 CPU unless detailed monitoring; Azure 45-minute aggregate on VMs; CA 10 s scan + minutes to a node. The burst is over, or the outage has cascaded, before `desired` moves. | Scale on a *leading* metric (queue depth, concurrent requests, pending); scheduled capacity for known peaks; C10 while the loop catches up. |
| **Wrong metric** | CPU on a blocked thread pool looks idle; SQS depth is not divided by fleet size; Cloud Run average-CPU on a 1-of-N vCPU hotspot. | Metric must fall as replicas rise. Prefer in-flight / queue-per-replica / ALB requests-per-target. |
| **Unhealthy-in-the-average** | SRE workbook: not-serving instances still in the utilization mean → scaler "simply won't occur." | Scale on LB-observed capacity; exclude warmup; autoheal with a long enough healthy-delay. |
| **Flapping** | In and out thresholds too close (Azure 80/60 on two instances); HPA down-stabilization 0. | Asymmetric thresholds; 300 s down window; Azure flapping detector. |
| **Downstream saturation** | Compute replicas × connections/replica > DB `max_connections` / API quota. Cloud Run and SRE both name this. | `maxReplicas` as a *safety* bound; pool bulkheads (C8); partition the data plane (B2). |
| **Stateful pin** | Session or shard affinity: more instances do not receive the hot session. | C5 routing / B2 re-shard; vertical only as a short buffer. |
| **Apply-time replica fight** | Deployment `spec.replicas` vs HPA. | Remove `spec.replicas` from the live manifest (HPA docs). |
| **Scale-to-zero split brain** | K8s < 1.37 / feature-gate skew: controller treats `replicas: 0` as a manual pause. KEDA `idleReplicaCount ≠ 0` does not work. | One controller owns zero; object/external metric required for HPA-to-zero. |
| **Modal / runaway scale-out** | Bug burns CPU → HPA/ASG adds replicas → more burned CPU (SRE "Setting Constraints"). A downed dependency holds every in-flight request (`W` explodes, `L` explodes, scaler adds fuel). | Hard `max`; kill switch; breaker / timeout on the dependency (C1, C7) so `W` cannot run away. |

**When not to autoscale.** Load is flat or known-periodic and the surprise-cost of a bad scaler exceeds the idle-cost of a fixed fleet (Kleppmann; Azure scheduled + reactive combo is the exception, not "always on"). The bottleneck is **data** (one hot key, one primary, one queue partition) — B2, not more stateless replicas. The bottleneck is **in-process** (unbounded pool, missing timeout) — C8 / C7; adding replicas multiplies the damage. You need an answer in less time than provision + warmup — C10 (Azure: "it might be better to throttle"). Vertical scale of a single-node store is still within one failure domain and one order of magnitude — stay there (scalability.md). DaemonSets, or any object without a scale subresource.

---

## 6. Cross-links

**Catalog siblings.** B2 partition/replicate (shared-nothing *data*; rebalancing, request routing). B3 cache (hit rate is a load parameter in scalability.md; stampede on fill is a herd, not a scaler). C5 load balancing ([research](load-balancing-external-research.md) — P2C / least-request compare the in-flight `L` Little predicts). C8 bulkhead ([research](bulkhead-isolation-external-research.md) §7 — same `L = λW` permit math). C10 load shedding (admission cap when the scaler has not caught up). E2 microservices / E11 serverless / E13 cells (quantum count and isolation; Cloud Run *is* E11's usual actuator; cells cap blast radius so a runaway HPA cannot take the fleet).

**Existing notes in this tree (link, do not rewrite).** [scalability.md](../../../cases/data-intensive-design/scalability.md) · [performance.md](../../../cases/data-intensive-design/performance.md) · [distributed vs single-node](../../../cases/data-intensive-design/distributed-vs-single-node.md) · [cloud vs self-hosting](../../../cases/data-intensive-design/cloud-vs-self-hosting.md#separation-of-storage-and-compute) · [timeouts and delays](../../../cases/data-intensive-design/timeouts-and-delays.md#latency-versus-utilization) · [home timeline](../../../cases/data-intensive-design/home-timeline-case-study.md) · [nfr-references](../../../cases/data-intensive-design/nfr-references.md) · [nfr-overview](../../../cases/data-intensive-design/nfr-overview.md). B2's existing notes when that card is written: sharding-overview, replication-overview, rebalancing, request-routing.

**Cite-forward.** Circuit-breaker note: Netflix concurrency-limits Little's-law limit, Envoy concurrency thresholds. Retry note: Pokémon GO retry amplification. Bulkhead note: 200 req/s × 100 ms = 20 permits. Load-balancing note: queueing math / least-request.

---

## 7. Sources

**Canon / queueing.** pubsonline.informs.org/doi/abs/10.1287/opre.9.3.383 (Little 1961, *OR* 9(3):383–387) · Little 2011 *OR* 59:536–549 · Stidham 1974 *OR* 22:417–421 · Kleinrock, *Queueing Systems* Vol. 1 (Wiley 1975, ISBN 0471491101) · en.wikipedia.org/wiki/M/M/1_queue (fetched 2026-09-13; Kleinrock pp. 77, 215; Kingman 1961 heavy traffic) · github.com/Netflix/concurrency-limits (README, `Limit = Average RPS * Average Latency`).

**SRE / industry.** sre.google/sre-book/monitoring-distributed-systems · sre.google/sre-book/service-level-objectives · sre.google/sre-book/handling-overload · sre.google/workbook/managing-load · learn.microsoft.com/azure/architecture/best-practices/auto-scaling · learn.microsoft.com/azure/azure-monitor/autoscale/autoscale-best-practices.

**Kubernetes / KEDA.** kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale · kubernetes.io/docs/reference/kubernetes-api/autoscaling/horizontal-pod-autoscaler-v2 · kubernetes.io/blog/2026/09/02/kubernetes-v1-37-hpa-scale-to-zero-beta · kubernetes.io/docs/concepts/workloads/autoscaling/vertical-pod-autoscale · github.com/kubernetes/autoscaler (VPA types / quickstart; CA `pkg/config` defaults) · keda.sh/docs/latest/reference/scaledobject-spec · github.com/kedacore/keda/releases/tag/v2.20.2 (2026-07-31).

**AWS / GCP / Azure / CA ops.** docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-scaling-cooldowns.html · docs.aws.amazon.com/autoscaling/ec2/userguide/as-scaling-target-tracking.html · docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-default-instance-warmup.html · docs.aws.amazon.com/autoscaling/ec2/userguide/health-check-grace-period.html · docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-autoscaling-autoscalinggroup.html · docs.cloud.google.com/run/docs/about-instance-autoscaling (2026-09-09) · docs.cloud.google.com/run/docs/about-concurrency (2026-09-09) · docs.cloud.google.com/run/docs/configuring/max-instances (2026-09-10) · docs.cloud.google.com/run/docs/configuring/min-instances · docs.cloud.google.com/run/docs/configuring/scaling-controls · docs.aws.amazon.com/eks/latest/best-practices/cas.html · learn.microsoft.com/azure/aks/cluster-autoscaler · pkg.go.dev/sigs.k8s.io/cluster-autoscaler/pkg/config.

**This tree.** cases/data-intensive-design/scalability.md (owner link) · performance.md · nfr-references.md [7][8][9] · docs/research/sysdesign/circuit-breaker-external-research.md · bulkhead-isolation-external-research.md · load-balancing-external-research.md · retry-backoff-external-research.md · docs/research/sysdesign/system-design-patterns-catalog.md (B1 row).

---

## 8. Uncertain / left out

- HPA v2 API `scaleUp` field description ("4 pods / double per **60** seconds") vs concepts default YAML and `HPAScalingRules.policies` ("every **15** seconds"). Used the concepts YAML.
- API `minReplicas` text still calls `HPAScaleToZero` **alpha**; the 2026-09-02 blog and the concepts page say **beta, default on** in 1.37. Used the blog + concepts page.
- KEDA **v2.21** docs exist on keda.sh but the page banner says they are not latest; latest *release* is **2.20.2** (2026-07-31). Defaults matched across `/docs/latest/` and 2.21 spec; 2.21-only `scalingModifiers` fallback behaviour not treated as released.
- Erlang-C / exact M/M/c sojourn formula not fetched this session (M/M/c Wikipedia timed out). Only the stability condition `λ < cμ` and the qualitative "queueing delay falls, service time does not" are asserted.
- AKF "Scale Cube" primary (akfpartners.com) returned HTTP 409; X/Y/Z axes not used. B2 remains the data-split owner.
- Universal Scalability Law (Gunther) and Amdahl serial-fraction numbers not re-derived; both are left out rather than quoted from memory.
- AWS target-tracking CloudWatch alarm periods (how many 1-minute samples, hysteresis) not fetched beyond "detailed monitoring = 1 min, default EC2 = 5 min."
- Metrics Server scrape interval not fetched (HPA 15 s sync is not the scrape).
- VPA recommender period, "significantly different" eviction threshold, and in-cluster default `updateMode` when the CR omits `updatePolicy` — docs call Recreate the default; not re-read from the current operator flags.
- Cloud Run ACT internals and the Preview scaling-controls *tolerance of 10%* (docs) — Preview, may move.
- Azure 45-minute default aggregation: taken from the current Autoscaling Guidance page; no `ms.date` in the fetched HTML.
- EC2 / GCE / Azure *largest* instance SKUs and current regional quotas — not fetched; do not invent a scale-up ceiling in cores.
- "The Tail at Scale" (Dean/Barroso) not re-fetched this session; SRE percentile + Kingman stand in.
- PromQL / CloudWatch alarm recipes are own formulations and are not in this note.
