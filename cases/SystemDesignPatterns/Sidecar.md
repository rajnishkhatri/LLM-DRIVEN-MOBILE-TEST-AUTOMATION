---
type: reference
title: 'Sidecar'
description: >-
  A colocated helper process that shares fate and namespace with the app —
  placement, not a runtime style. Distinguishes Burns/Azure sidecar from
  hexagonal adapters and microkernel plugins. Covers native Kubernetes
  sidecars, mesh data-plane vs control-plane, ambient vs sidecar, verified
  injector defaults, shared-fate and version-skew failure modes, and when a
  library or node proxy is the better cut.
tags: [system-design-patterns, deployment, sidecar]
---

# Sidecar

**See also:** [circuit breaker](CircuitBreaker.md) (mesh *policy*, not this placement) · [API gateway and BFF](ApiGateway.md) · [bulkhead and isolation](Bulkhead.md) · [retry, backoff, and retry budgets](RetryBackoff.md) · [timeouts and deadline propagation](TimeoutsDeadlines.md) · [cloud patterns: sidecar + mesh vs gateway](../aws/ch08.md) · [ML inference-pod sidecar](../ml-solutions-arch/ml-microservices-patterns.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/b6-sidecar-external-research.md)

A sidecar is a **second process scheduled with the application instance and dying with it**. On Kubernetes that is a second container in the same Pod: shared network namespace (`localhost` is the IPC), optional shared volumes, independent image / language / team, **not** independently scaled. The app may not know the helper exists (iptables / eBPF redirect) or it talks to `localhost` (ambassador, Dapr-class API, a log shipper tailing a shared file).

That is *placement*, not a style. A sidecar does not turn a monolith into microservices (E2) and does not create a cell ([bulkhead](Bulkhead.md) / E13). The [breaker](CircuitBreaker.md), [retry](RetryBackoff.md), [timeout](TimeoutsDeadlines.md), and concurrency limit that often *run inside* a mesh proxy stay on those cards; this one owns where the helper lives and what that costs.

Quality attributes: **modularity** (infra concerns out of the app), **language independence**, **operability** (one data-plane image for mTLS / telemetry / policy). Costs: per-replica CPU/RAM, an extra hop, **shared fate** (the helper's crash isolates the app), and a new version-skew surface between control plane and data plane.

## Not hexagonal, not a microkernel

Same words, three different cuts. Do not collapse them.

| Cut | What is composed | Process / language | Scale unit |
|---|---|---|---|
| **Sidecar (this card)** | App *process* + helper *process*, co-scheduled | Out-of-process; any language; no plugin API required | The replica. Helper scales with the app. |
| **Hexagonal / ports-and-adapters (E8)** | Domain at the center; *ports* as interfaces; *adapters* as in-process I/O | Same process. Cockburn's adapter is a **code module** (HTTP, DB, bus), not a container. | The deployable that contains the domain. |
| **Microkernel / plug-in (E7)** | Core + plugins the core loads | Typically same runtime and address space; the app *has* a plugin API | The host process. Plugins do not get their own replica. |

Burns's 2015 **adapter** sidecar *normalizes a container's output* (metrics exporter, log shape). Cockburn's adapter *implements a port*. Azure's reason to sidecar is the case E7 cannot cover: **extensibility for apps with no plugin API**. A hexagonal rewrite and a sidecar can coexist — one is how the code is structured, the other is how a helper is deployed.

## Lineage and vocabulary

- **Burns, Kubernetes blog (2015-06-29) / DockerCon toolkit.** Sidecar containers "extend and enhance the 'main' container" without rewriting it. Worked example: Nginx + a git synchronizer sharing a filesystem. Sibling composites in the same talk: **ambassador** (proxy that *presents* localhost to the app) and **adapter** (normalize output). Requirements: shared namespaces, **co-scheduling**, runtime parameterization.
- **Burns, *Designing Distributed Systems* (2018), ch. 2.** First *single-node* pattern: two containers in an atomic group (a Pod) sharing hostname, network, and parts of the filesystem. The sidecar "augment[s] and improve[s] the application container, often without the application container's knowledge." HTTPS in front of legacy HTTP; config sync; a `topz` debug container. Design rules: parameterized images, a documented container API, one sidecar image serving many apps.
- **Azure Architecture Center, *Sidecar Pattern*** (`ms.date` 2026-02-17). Motorcycle metaphor; also **Sidekick**. Each app instance gets its own sidecar that **shares its life cycle**. Advantages: language independence, shared-resource access, low latency vs a remote helper. Considerations: choose IPC carefully; decide *library vs daemon vs separate service* before adding a sidecar; Kubernetes **native sidecar containers** start before the app and terminate after it. Examples: Dapr (dependency abstraction — no resource defaults fetched), Istio, ambassador, protocol adapters, OpenTelemetry Collector as telemetry sidecar.
- **Azure *Ambassador Pattern*.** An out-of-process egress proxy colocated with the client — deployable *as a sidecar* or as a **host daemon**. Offloads TLS, routing, retries, breakers, metrics. Not suitable when latency is critical, the client is a single language (prefer a library), or the platform already ships a mesh. Ambassador is a *use* of B6; C1/C2 own the knobs.
- **Envoy *Service to service only*** (docs 1.40.0-dev). Envoy "originated as a service mesh sidecar proxy." Two listeners: **egress** (app → `localhost`, Host/`:authority` selects the remote cluster) and **ingress** (remote Envoys → local Envoy → app). Default Envoy-to-Envoy is HTTP/2. The **front-proxy** deployment is the complementary *non-colocated* cut — that is [C6](ApiGateway.md), not this card.
- **Istio** (2017; sidecar from day one). Data plane = Envoy next to each workload. Ambient launched 2022; production-ready for **single-cluster** as of Istio 1.22. Current release at research fetch: **Istio 1.31.0** (2026-08-31), Kubernetes 1.32–1.36.
- **Workspace one-liners (link only).** [aws/ch08.md](../aws/ch08.md): sidecar = extra container for monitoring, logging, configuration, networking; mesh = those concerns on *east-west* hops (gateway is north-south). [ml-microservices-patterns.md](../ml-solutions-arch/ml-microservices-patterns.md): sidecar on the inference pod ships traces / mTLS so "the predictor stays a predictor."

## Variants

| Variant | Helper's job | Typical IPC | Trade-off |
|---|---|---|---|
| **Mesh proxy** (Istio / Linkerd / Consul Connect / App Mesh / ECS Service Connect) | Intercept inbound + outbound; mTLS, L7 route, telemetry | Transparent redirect, or app → localhost egress | App unchanged; per-replica CPU/RAM and an extra hop. Policy knobs → C1/C2/C7/C8. |
| **Ambassador** (Burns / Azure) | Client-side egress proxy the *app calls* | localhost HTTP/gRPC | Explicit; no iptables. Extra hop on every outbound call. |
| **Adapter** (Burns 2015) | Normalize logs / metrics / protocol | shared volume or localhost scrape | One exporter image, many apps; must stay up for the scrape window. |
| **Dependency abstraction** (Dapr; Azure examples) | State, pub/sub, bindings, secrets via a sidecar API | localhost HTTP/gRPC | Language-agnostic platform API; another process in the blast radius. **No Dapr resource defaults** in the research pass. |
| **Log / config / cert shipper** | Tail files, sync ConfigMaps, rotate certs | shared `emptyDir` | Simple; startup order matters. |
| **Protocol / TLS wrapper** | Modern protocol to the world, legacy to localhost | localhost | Legacy app untouched; sidecar is now on the request path. |

These compose: a mesh sidecar is often ambassador + adapter for networking. Do not invent a second card for the overlap.

## Data plane vs control plane

```
  control plane (istiod / Linkerd dest / Consul / ECS SC)     admission webhook
           │ xDS / identity                                              │ inject
           ▼                                                             ▼
  ┌──────────────────────── Pod / ECS task ─────────────────────────┐
  │  app  ←localhost / redirect→  data-plane proxy (Envoy / …)     │
  └─────────────────────────────────────────────────────────────────┘
```

The **data plane** is the colocated process on the request path. The **control plane** is not in the Pod: it pushes config (xDS), issues identity, and (at admission) the injector mutates the spec. Envoy itself has **no** product CPU/memory default — the *injector* does. Mixing them is the usual version-skew: a live control-plane revision talking to leftover data-plane images, or new Pods that never got injected.

ECS Service Connect **adds** the sidecar at task start; it is not in the task definition and is not user-configurable. AWS App Mesh (EOS **2026-09-30**) is the opposite: the user *declares* an `envoy` container (`proxyConfiguration.type=APPMESH`). Do not start new work on App Mesh.

## Kubernetes native sidecars (KEP-753)

Until 1.28 a "sidecar" was a convention: an init that **exits** (wrong lifetime) or a regular container with **no startup order** that can **block Job completion**.

| Milestone | What shipped |
|---|---|
| **1.28** (2023-08-25) | Alpha. `restartPolicy: Always` on an `initContainers[]` entry. Starts in init order; restarts on exit; does **not** keep the Pod alive after mains exit. |
| **1.29** | Beta, **on by default**. |
| **1.33** ("Octarine", 2025-04-23) | **GA.** Reverse-order shutdown after mains stop. Sidecars may use startup / readiness / liveness probes; **OOM score aligned with primaries**. |
| **1.36** | Feature **gate** removed (the feature stays). |

API: helper under `spec.initContainers` with `restartPolicy: Always`. After that container's `started` is true, the next init starts. On termination the kubelet **waits for mains**, then SIGTERMs sidecars in **reverse declaration order**. If mains consume the whole `terminationGracePeriodSeconds`, sidecars may get SIGTERM then SIGKILL with **non-zero exit** — treat that as normal. A native sidecar **does not** prevent Job success.

**Resource accounting.** Effective init request/limit = the **highest** among init containers (a missing limit is treated as the highest). Pod effective request/limit = pod overhead + **max**(sum of non-init app+sidecar, effective init). QoS is computed across **all** init, sidecar, and app containers — one BestEffort container can drag the Pod down.

Istio's native path (operational fact: auto-on when **every node is ≥ 1.33**, else set `ENABLE_NATIVE_SIDECARS` yourself; istio#57587) adds a `preStop` drain, not a `postStart` wait. The legacy `holdApplicationUntilProxyStarts` workaround is **ignored** when native is on. Per-pod native opt-out exists; the annotation *string* was not reconciled this fetch — look up the live Istio annotation reference, do not guess a key. Linkerd: `config.linkerd.io/proxy-enable-native-sidecar`; `proxy-await` makes the app wait until the proxy is ready; `proxy-wait-before-exit-seconds` **defaults to 0**.

Legacy multi-container Pods (no `restartPolicy` on init) remain valid when you do not need ordering, or you must run on nodes older than 1.29.

## Injection and traffic steal

| Platform | How the sidecar appears | Opt-in |
|---|---|---|
| **Istio** | Mutating webhook. Namespace `istio-injection=enabled` (or `istio.io/rev=<rev>` — namespace injection **wins** over rev). Pod `sidecar.istio.io/inject=true\|false`. Inject-by-default is **off**. | Manual: `istioctl kube-inject`. |
| **Linkerd** | Injector webhook or `linkerd inject`. | Annotation `linkerd.io/inject`: `enabled` \| `disabled` \| `ingress`. |
| **Consul Connect** | `consul-k8s` connect-inject webhook. | Default **opt-in**: `consul.hashicorp.com/connect-inject: "true"` on the **Pod**. Helm `connectInject.default: true` flips it. |
| **ECS Service Connect** | ECS adds a sidecar at task start. | Not in the task def; reuse one def across namespaces. |
| **App Mesh** (EOS 2026-09-30) | User-declared `envoy` container. | `proxyConfiguration.type=APPMESH`. |

Istio / Linkerd / Consul typically install an init (iptables / nft / CNI) that redirects pod traffic through the proxy. Istio interception mode `NONE` skips the init. A down webhook is not a no-op: **new Pods come up unmeshed**.

## Ambient vs sidecar

Istio documents two data-plane modes (fetched 2026-09-13). Ambient is informally "sidecar-less mesh." Hybrid is allowed. Linkerd remains a sidecar data plane. Cilium-class eBPF node proxies are the same *placement* idea as ztunnel (per-node, not per-pod) — an alternative, not a deep-dive here.

| | **Sidecar** | **Ambient** |
|---|---|---|
| Data plane | Envoy **per pod** (and VMs) | Per-node L4 **ztunnel**; optional per-namespace (or per-service) Envoy **waypoint** for L7 |
| Add a workload | Label + **restart pods** | Label; **no restart** |
| L7 steps on a request | 2 (source + dest sidecar) | 1 (dest waypoint) |
| Latency Istio *states* (p90/p99) | **0.63–0.88 ms** | Ambient **0.16–0.20 ms**; waypoint **0.40–0.50 ms**. Istio's numbers, **not** a universal SLA — no benchmark method on the page. |
| Resource model | Provision **worst-case per replica** | Waypoints autoscale; many replicas share one waypoint |
| Keys | **Per-workload**. Compromised app pod **has** mesh keys | Node agent holds keys for pods **on that node**. Compromised app **does not** get mesh keys |
| Extensibility | Full, including `EnvoyFilter` | WasmPlugin on waypoint; **EnvoyFilter not supported** |
| Jobs | Sidecar lifetime fights completion | Transparent |
| Support | Stable, **including multi-cluster** | Stable, **single-cluster only** (unsupported: sidecar↔waypoint interop, multi-network, VMs) |

Migration caveat (Istio migrate docs): **sidecar clients bypass waypoints**, so L7 policy on a waypoint is not enforced until the *source* is also ambient. `VirtualService` in ambient is Alpha; HTTPRoute is the stable L7 path.

## Placement

| Layer | Fate shared with | Typical use | When it is the wrong layer |
|---|---|---|---|
| **In-process library** (Resilience4j, OTel SDK, mesh client) | Process | Single language; lowest latency | Polyglot fleet; you cannot change the app. |
| **Sidecar in the Pod / ECS task** | Replica | Mesh, log shipper, Dapr, TLS wrapper | Need independent scale; per-replica cost dominates; platform already does it. |
| **Node proxy / ztunnel / CNI** | Node | L4 mTLS + identity for every pod on the node | Need per-workload key isolation or L7 at every hop. |
| **Namespace / service waypoint** | A *set* of replicas | Shared L7 policy, retries, HTTPRoute | Need client-side L7 from *this* pod, or EnvoyFilter. |
| **Front proxy / gateway ([C6](ApiGateway.md))** | None (shared fleet) | North-south TLS, composition, BFF | East-west identity hop-by-hop. |
| **Host daemon** (Azure ambassador alternative) | Host | Many processes, one proxy | Orchestration already gives you a Pod. |

A sidecar is **not** a [bulkhead](Bulkhead.md). It *increases* coupling to the replica. Cells (E13) are an independent blast-radius cut.

## Verified defaults (2026-09-13)

Envoy the product has **no** sidecar CPU/memory default. Blogs that say "Envoy defaults to 100m" are repeating Istio.

| Injector | CPU request | Memory request | CPU limit | Memory limit |
|---|---|---|---|---|
| **Istio** `proxy.resources` (chart, same numbers since the 1.4-era file) | **100m** | **128Mi** | **2000m** | **1024Mi** |
| **Istio waypoint** (same file) | 100m | 128Mi | `"2"` | 1Gi |
| **Linkerd** default Helm | **empty** | empty | empty | empty. **1** runtime worker |
| **Linkerd HA** `values-ha.yaml` | **100m** | **20Mi** | *(unset)* | **250Mi** |
| **Consul Connect** `sidecarProxy.resources` | **null** (chart comment: recommended **100m**) | null; recommended **100Mi** | null; recommended **100m** | null; recommended **100Mi** |
| **Consul Connect init** (chart default, not null) | **50m** | **25Mi** | **50m** | **150Mi** |
| **ECS Service Connect** (AWS *recommendation* — add to **task** size) | **+256** units; **+512** if peak **> 500 rps** | **+64 MiB**; **+128 MiB** if namespace **> 100 services** or **> 2000 tasks** | n/a (task-level) | Fargate task memory floor **512 MiB** |
| **App Mesh Envoy** (docs; EOS 2026-09-30) | **512** units recommended | **≥ 64 MiB**; Fargate lowest settable **1024 MiB** | raise from Container Insights | Image pin at fetch: `aws-appmesh-envoy:v1.39.1.0-prod` |

**Istio annotation trap (verified):** if you set `sidecar.istio.io/proxyCPU` you **must** also set `sidecar.istio.io/proxyCPULimit` or the CPU **limit becomes unlimited**; same pairing for memory. Setting only a subset of the four annotations replaces the whole resources block (istio#35905). Those four override annotations are **Alpha**. `LimitRange` can insert requests *before* the injector runs.

Linkerd concurrency: default kubelet CFS, a CPU *limit* is a quota. Static CPU manager: Guaranteed QoS **and** proxy request/limit are **integers ≥ 1**. `maximumCPURatio` 1.0 = one worker per host CPU; 0.2 = one per five cores; the CPU **limit beats** the ratio. `proxy-init` resources now **inherit the proxy's** values so Guaranteed QoS is not broken by a leftover init request.

| Knob | Verified default |
|---|---|
| K8s `SidecarContainers` | On by default **1.29+**; GA **1.33**; gate gone **1.36**. |
| Istio native sidecars | Auto-on when every node is **≥ 1.33**; otherwise set the env yourself. |
| Istio `holdApplicationUntilProxyStarts` | Off unless set; **ignored** when native is on. |
| Istio startupProbe | Chart: `enabled: true`, `failureThreshold: 600` (10 min at 1 s). |
| Istio status port | `15020`. Prometheus merge scrape `:15020/stats/prometheus` (`enablePrometheusMerge` **on**). |
| Linkerd wait-before-exit | **0** s. |
| Linkerd inbound / outbound connect timeout | **100 ms** / **1000 ms**. |
| Consul inject default | **false** (annotation required). |
| Service Connect retries / outlier / timeout | **2** retries; ≥ **5** failed connections in **30 s** → avoid **30–300 s**; `perRequestTimeout` **15 s**; idle HTTP **5 min**, TCP **1 h**. *Mechanics owned by C1/C2/C7 — listed so placement cost is honest.* |

## Observability of the sidecar itself

A sidecar without **its own** signals is a silent tax.

| Signal | Why |
|---|---|
| **Container CPU / memory** of the proxy vs its request/limit | 100m/128Mi are scheduling hints, not a workload profile. OOMKill of the proxy takes the **whole Pod**. |
| **Istio standard metrics** (`istio_requests_total`, duration, bytes; TCP open/close/bytes). Label `reporter=source\|destination` — sidecar-to-sidecar is counted **twice** if you sum both. | Data-plane health of *this* hop. |
| **Envoy cluster stats** (`upstream_cx_active`, `_rq_pending_overflow`, outlier / retry counters) | Placement health of *this* proxy; C1/C2 own the *meaning*. |
| **Injection / dataplane-mode** | Pods 1/1 vs 2/2; `istio.io/dataplane-mode`; missing webhook = apps running **unmeshed**. |
| **Startup / drain** | Scheduled → proxy ready; preStop drain; Jobs that never complete (legacy sidecar). |
| **Waypoint vs sidecar mix** | During ambient migration, sidecar→waypoint bypass. |

Alert shapes (this note's, **not** vendor PromQL): *sidecar CPU > request for 15 m*; *sidecar OOMKills > 0*; *proxy not ready while app is Ready*; *injected replica count ≠ Deployment replicas*. OpenTelemetry has no sidecar-specific semantic convention: put the proxy's spans on the same trace (`traceparent` hop) and tag `container` / `dataplane_mode`. The Collector *as* a sidecar is the adapter variant.

## Tuning

| Knob | Too aggressive | Too timid | Starting point (sourced) |
|---|---|---|---|
| Sidecar CPU request | 2 cores on a 100 rps CRUD pod | 0 (BestEffort; eviction) | Istio 100m; Linkerd HA 100m; measure p50 then add headroom. |
| Sidecar memory limit | 128Mi on a large-mesh Envoy (xDS blows it) | no limit (noisy neighbor) | Istio 1024Mi limit / 128Mi request; raise on `envoy_server_memory_*` or OOMKills. Pair all four annotations. |
| Mesh mode | Sidecar on every Job and every replica "for consistency" | Ambient without waypoints while you still need L7 auth | Ambient ztunnel for mTLS-only; waypoint where HTTPRoute / L7 auth lives; sidecar for EnvoyFilter, VMs, or multi-cluster. |
| Native sidecar | Forced on mixed 1.28/1.33 nodes | Still using `holdApplicationUntilProxyStarts` on 1.33+ | K8s ≥ 1.33; Linkerd `proxy-enable-native-sidecar` for Jobs. |
| Injection default | Cluster-wide inject (Consul `default: true`, Istio `enableNamespacesByDefault`) | Manual inject only, drift | Namespace label (Istio / Linkerd); Consul stay opt-in until the platform owns it. |
| Task size (ECS SC) | 256 CPU task + SC (proxy eats the app) | Ignore +256/+64 | AWS: add 256 CPU + 64 MiB; 512 CPU if > 500 rps; 128 MiB extra at 100 services / 2000 tasks. |

## Worked calibration — inference pod (50 replicas)

Design drill (not a vendor SLA), matching [ml-microservices-patterns.md](../ml-solutions-arch/ml-microservices-patterns.md) "sidecar on the inference pod ships traces."

Constraints: 50 replicas; app **1 CPU / 2 Gi** request=limit (Guaranteed if the sidecar matches); east-west mTLS required; L7 retries/timeouts on the *feature-store* hop only; cluster is Kubernetes **1.33**.

| Step | Choice | Why |
|---|---|---|
| Need | mTLS + identity + L4 telemetry on all hops; L7 only to `feature-store` | Do not pay two Envoys per request for encrypt-only. |
| Default sidecar bill | 50 × (100m CPU, 128Mi) = **5 CPU, 6.25 Gi** scheduled; limits 50 × (2 CPU, 1 Gi) = **100 CPU / 50 Gi** burst cap | Istio chart defaults. Worst-case limit is why Istio calls sidecar utilization "wasteful." |
| Ambient alternative | ztunnel on each node (say 10 nodes) + **one** waypoint Deployment for `feature-store` (autoscale) | L7 steps 1 not 2; Istio-stated latency 0.16–0.50 ms vs 0.63–0.88 ms. No pod restart to enroll. |
| Keep sidecar when | You need `EnvoyFilter`, multi-cluster, or a VM predictor | Istio "unsupported in ambient" list. |
| If sidecar stays | Native sidecar (`restartPolicy: Always`); set **all four** resource annotations after a load test | Avoid the unlimited-limit trap; batch-eval Jobs complete. |
| ECS analog | Same 50 tasks: task size += 256 CPU + 64 MiB (512 CPU if a task exceeds 500 rps) | Service Connect docs. App Mesh is dying 2026-09-30. |
| Rollback | Namespace `istio-injection=disabled` + restart (sidecar); or remove `istio.io/dataplane-mode=ambient` (no restart) | Ambient incremental vs sidecar binary. |
| Do not | Put C1 thresholds in this card; put model code in the sidecar; scale an OTel collector *with* replicas if a cluster collector would do | Azure "daemon or separate service" test. |

## Failure modes of the sidecar itself

- **Shared fate / app isolation.** Proxy OOM, crash-loop, or iptables init failure takes the replica — or, with traffic steal, a live app behind a dead proxy is **network-isolated**: redirected packets black-hole. Native sidecars restart independently; that does not restore the hop while the proxy is down. This is the opposite of a [bulkhead](Bulkhead.md).
- **Version skew.** Control-plane revision (`istio.io/rev`) vs leftover data-plane images; webhook down → new Pods **unmeshed** while old ones still carry policy; ambient hybrid where sidecar sources **skip** the waypoint and L7 AuthorizationPolicy is silently not enforced; leftover App Mesh `envoy` containers after EOS **2026-09-30**. The fleet then has two (or three) data-plane generations and no single policy truth.
- **Startup race (legacy).** App binds and serves before the proxy is LIVE — first requests fail or bypass policy. Native ordering / `holdApplicationUntilProxyStarts` / Linkerd `proxy-await` exist because this is common.
- **Shutdown race (legacy).** Proxy exits while in-flight RPCs remain; or a Job never completes because the proxy is a main container. Native reverse-order stop + Istio drain + Linkerd wait-before-exit.
- **Per-replica tax / eviction.** 100 pods × 128–256 Mi is 12–25 Gi of node memory that is not model weights. A sidecar without requests can make a Guaranteed app Burstable.
- **Config stampede / memory.** Envoy holds per-cluster xDS; large meshes without Istio `Sidecar` scope blow the 128Mi *request* and then the 1Gi *limit*.
- **Annotation partial apply.** Istio CPU request set, limit wiped (#35905).
- **Double hop vs front proxy.** L7 policy in both a [C6](ApiGateway.md) gateway *and* every sidecar without a reason.
- **Keys on the app pod.** Istio sidecar: compromised application **has** mesh keys. Ambient: no.

## When not to use

| Situation | Prefer |
|---|---|
| Optimize IPC / frequent chatter (Azure: "might not be suitable") | In-process library |
| Small system; per-instance cost dominates | Skip, or one node proxy |
| Must scale the helper independently | Separate Deployment (collector, waypoint, daemon) |
| Platform already provides it | The platform mesh / gateway |
| Sidecar-less data plane meets the need | Ambient ztunnel (± waypoint); Cilium-class node proxy |
| Single language, you own the code (Azure ambassador) | Client library (C1/C2 in-process) |
| North-south composition / BFF | [Gateway](ApiGateway.md), not a per-pod sidecar |
| Jobs / batch, no native sidecars | Ambient, or native sidecars on 1.29+ |
| Need independent blast radius | Cells (E13 / C8) — a sidecar *increases* coupling to the replica |
| The "adapter" you want is a domain port | Hexagonal (E8), in-process |
| The app already has a plugin API and one language | Microkernel (E7), not a second process |

## Trade-offs

| Buy | Pay |
|---|---|
| Language-decoupled infra next to any app; no plugin API required | Per-replica CPU/RAM; extra hop; helper scales only with the replica |
| Uniform mTLS / telemetry / policy without rewriting the app | Shared fate: proxy crash isolates the app; keys sit on the app pod (sidecar mode) |
| Native sidecars fix Job completion and startup order | Requires Kubernetes 1.29+ (GA 1.33); mixed-node clusters need an explicit env |
| Ambient drops per-pod Envoy for L4 and shares L7 waypoints | Single-cluster; no EnvoyFilter; sidecar clients bypass waypoints until migrated |
| Injector-owned defaults (Istio 100m/128Mi, Service Connect +256/+64) | Defaults are scheduling hints; unpaired Istio annotations wipe limits; Linkerd ships empty |

The sidecar decides **where the helper runs**. The [gateway](ApiGateway.md) decides **the north-south façade**. The [breaker](CircuitBreaker.md) decides **whether to call**. The [bulkhead](Bulkhead.md) decides **how much may run at once**. Hexagonal and microkernel decide **how the code is composed**. Do not use one cut to do another cut's job.

## Sources

Verified 2026-09-13; full URLs, per-claim provenance, and items deliberately left out (Istio native-sidecar annotation string, Dapr resource defaults, Envoy-as-product CPU defaults, PromQL recipes, ambient latency method) are in the [external research note](../../docs/research/sysdesign/b6-sidecar-external-research.md).

- Canon: Burns, Kubernetes blog 2015-06-29 and ;login: Oct 2015; Burns, *Designing Distributed Systems* ch. 2 (2018); Azure *Sidecar* (`ms.date` 2026-02-17) and *Ambassador*.
- Kubernetes native sidecars: KEP-753; 1.28 / 1.33 blogs; sidecar-containers concept page; gate removal in 1.36.
- Mesh placement: Istio dataplane-modes, ambient overview/migrate, sidecar-injection, 1.31.0 (2026-08-31), 1.27 change notes, istio#57587 / #35905; Envoy *Life of a Request* and service-to-service vs front-proxy; Linkerd proxy-configuration and HA values; Consul connect-inject; ECS Service Connect; App Mesh Envoy (EOS 2026-09-30).
- Workspace: [aws/ch08.md](../aws/ch08.md); [ml-microservices-patterns.md](../ml-solutions-arch/ml-microservices-patterns.md).
