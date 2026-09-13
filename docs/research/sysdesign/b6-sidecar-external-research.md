---
type: research
title: 'Sidecar — external research (2026-09-13)'
description: >-
  Source-verified research backing catalog B6: sidecar as a colocated process
  sharing fate and namespace with the app; Kubernetes native sidecars; mesh
  placement (Envoy/Istio/Linkerd/Consul, App Mesh, ECS Service Connect);
  ambient vs sidecar; resource isolation, injection, ordering; verified
  defaults and when not to sidecar.
tags: [research, system-design-patterns, B6, sidecar]
---

# Sidecar — external research (2026-09-13)

> **What this is.** The evidence pass for catalog **B6** (Group B, full
> operational / CircuitBreaker depth bar). The Concept (when written) carries
> the distilled result; this note keeps verified facts, defaults, and URLs.
>
> **Method.** Primary pages fetched 2026-09-13. Paraphrase; numbers and
> identifiers reproduced exactly. Items that could not be verified are in
> **Uncertain / left out** and are **not** to be asserted in the Concept.
>
> **Existing notes in this tree** (cite; do not rewrite):
> [aws/ch08.md](../../../cases/aws/ch08.md)
> (one-paragraph Sidecar + Service mesh under *Other Cloud Architecture
> Patterns* / API routing),
> [ml-microservices-patterns.md](../../../cases/ml-solutions-arch/ml-microservices-patterns.md)
> (sidecar as the ops companion on an inference pod).

---

## 1. Scope and non-goals

**This note owns** *placement*: a helper process or container colocated with
an application instance, sharing its life cycle and (on Kubernetes) its
network and optional volume namespaces. Operational depth: variants
(logging / config / ambassador / mesh proxy / Dapr-class dependency
abstraction), Kubernetes native sidecar containers, injection, startup and
shutdown order, CPU/memory isolation, mesh-as-sidecar vs ambient /
node-proxy, per-pod cost, and when a library or a separately scaled service
is the better cut.

**Mesh as placement, not as resilience mechanics.** Istio, Linkerd, Consul
Connect, Envoy, AWS App Mesh, and ECS Service Connect appear here because
they *are* the dominant sidecar deployment. Breaker / retry / timeout /
bulkhead *behavior* that those proxies implement stays in C1 / C2 / C7 / C8.

**Stays in sibling catalog ids**

| Id | Why it is not this card |
|---|---|
| **C1 Circuit breaker** | Failure-trip and concurrency-limit *mechanics* that often *run in* the sidecar. This note only says the state lives per proxy. |
| **C2 Retry / budgets** | Retry knobs (Envoy `retry_budget`, Linkerd HTTPRoute retries, Service Connect's fixed 2 retries). |
| **C7 Timeouts / deadlines** | Per-request and idle timeouts (Service Connect `perRequestTimeout` 15 s, idle 5 min HTTP). |
| **C8 Bulkhead / cells** | Thread/connection-pool isolation and cell blast-radius. A sidecar is *not* a cell. |
| **C6 API gateway / BFF** | North-south façade. Envoy *front proxy* / Istio Gateway is C6; Envoy *colocated with the app* is B6. |
| **E2 Microservices** | The *style*. Sidecar is an implementation tactic that the style often uses. |
| **E13 Cellular** | Independent deployable cells (aws/ch08 cellular). Sidecar is per-instance, not per-cell. |
| **Ambassador (Burns / Azure)** | A *use* of a sidecar (egress proxy). Summarized as a variant; not a second card. |

**Non-goals.** Rewriting [aws/ch08.md](../../../cases/aws/ch08.md) or
[ml-microservices-patterns.md](../../../cases/ml-solutions-arch/ml-microservices-patterns.md);
scoring monolith-vs-microservices; a Dapr Concept; EnvoyFilter / WasmPlugin
catalogs.

---

## 2. Lineage / vocabulary

**Burns, Kubernetes blog (2015-06-29),**
https://kubernetes.io/blog/2015/06/the-distributed-system-toolkit-patterns/
— DockerCon 2015 toolkit. **Sidecar** containers "extend and enhance the
'main' container" without rewriting it. Worked example: Nginx + a git
synchronizer sharing a filesystem = modular push-to-deploy. Sibling
composites named in the same talk / ;login: article (Oct 2015):
**ambassador** (proxy that *presents* localhost to the app) and **adapter**
(normalize output, e.g. a metrics exporter). Requirements: shared
namespaces (network, optionally filesystem), **co-scheduling**, runtime
parameterization.

**Burns, *Designing Distributed Systems* (O'Reilly, February 2018),**
ch. 2 — sidecar as the first *single-node* pattern: two containers in an
atomic group (a Kubernetes Pod) that share hostname, network, and parts of
the filesystem. The sidecar "augment[s] and improve[s] the application
container, often without the application container's knowledge." Examples:
HTTPS termination in front of a legacy HTTP service; dynamic configuration
sync; the `topz` debugging container. Design rules: parameterized
containers, a documented container API, modularity so one sidecar image
serves many apps.

**Azure Architecture Center, *Sidecar Pattern*** (GitHub `ms.date`
2026-02-17; fetched 2026-09-13).
https://learn.microsoft.com/en-us/azure/architecture/patterns/sidecar
— motorcycle metaphor; also called **Sidekick**. Each application instance
gets its own sidecar instance that **shares its life cycle**. Advantages:
language independence, shared-resource access, low latency vs a remote
helper, extensibility for apps with no plugin API. Considerations: choose
IPC carefully (language-agnostic unless performance forbids it); evaluate
whether the work is a *library*, a *daemon*, or a *separate service* before
adding a sidecar; Kubernetes **native sidecar containers** start before the
app and terminate after it. Examples: Dapr (dependency abstraction), Istio
(mesh data plane), ambassador, protocol adapters, OpenTelemetry Collector
as a telemetry sidecar.

**Azure *Ambassador Pattern*** (fetched 2026-09-13).
https://learn.microsoft.com/en-us/azure/architecture/patterns/ambassador
— "an out-of-process proxy that's colocated with the client." Can be
deployed *as a sidecar* or as a host daemon shared by several processes.
Offloads TLS, routing, retries, breakers, metrics. "Not suitable" when
latency is critical, the client is a single language (prefer a library),
or the platform already ships a mesh. Ambassador *is* a sidecar use; B6
owns the colocated-process cut, not the resilience knobs.

**Envoy, *Service to service only*** (docs 1.40.0-dev, fetched 2026-09-13).
https://www.envoyproxy.io/docs/envoy/latest/intro/deployment_types/service_to_service
— Envoy "originated as a service mesh sidecar proxy"
(*Life of a Request*). Two listeners: **egress** (app → `localhost:9001`,
Host/`:authority` selects the remote cluster) and **ingress** (remote
Envoys → local Envoy → app). Default Envoy-to-Envoy is HTTP/2. The
**front-proxy** deployment (TLS termination, L7 edge) is the complementary
*non-colocated* cut — C6, not B6.

**Istio** (first release 2017; sidecar from day one). Data plane = Envoy
injected next to each workload. Ambient mode launched 2022; production-ready
for single-cluster as of **Istio 1.22**. Current release at fetch:
**Istio 1.31.0** (2026-08-31), supported on Kubernetes 1.32–1.36.

**Workspace one-liners (link only).**
[aws/ch08.md](../../../cases/aws/ch08.md): sidecar = extra container or
process for monitoring, logging, configuration, networking; language-
decoupled from the main container. Mesh = those concerns implemented by
sidecar proxies on *east-west* hops (gateway is north-south).
[ml-microservices-patterns.md](../../../cases/ml-solutions-arch/ml-microservices-patterns.md):
sidecar on the inference pod ships traces / mTLS so "the predictor stays a
predictor."

---

## 3. Mechanics (Group B depth)

### 3.1 What the pattern is

A **sidecar** is a second process that is *scheduled with* the application
instance and *dies with it*. On Kubernetes that is a second container in
the same Pod: shared network namespace (`localhost` is the IPC), optional
shared volumes, independent image / language / team, **not** independently
scaled. The application does not have to know the sidecar exists (mesh
iptables / eBPF redirect) or it talks to `localhost` (ambassador, Dapr,
log shipper tailing a shared file).

That is *placement*, not a runtime style. The destination of the helper's
work can be a logging backend, a control plane, or another service. The
sidecar does not make a monolith into microservices (E2) and does not
create a cell (E13).

### 3.2 Variants (what the colocated process *does*)

| Variant | Helper's job | Typical IPC | Trade-off |
|---|---|---|---|
| **Mesh proxy** (Istio / Linkerd / Consul Connect / App Mesh / ECS Service Connect) | Intercept inbound + outbound; mTLS, L7 route, telemetry | Transparent redirect, or app → localhost egress | App unchanged; per-replica CPU/RAM and an extra hop. Resilience knobs → C1/C2/C7/C8. |
| **Ambassador** (Burns / Azure) | Client-side egress proxy the *app calls* | localhost HTTP/gRPC | Explicit; no iptables. Extra hop on every outbound call. |
| **Adapter** (Burns 2015) | Normalize logs / metrics / protocol | shared volume or localhost scrape | One exporter image, many apps; must stay up for the scrape window. |
| **Dependency abstraction** (Dapr; Azure sidecar examples) | State, pub/sub, bindings, secrets via a sidecar API | localhost HTTP/gRPC | Language-agnostic platform API; another process in the blast radius. |
| **Log / config / cert shipper** | Tail files, sync ConfigMaps, rotate certs | shared `emptyDir` | Simple; startup order matters (shipper before writers; certs before listeners). |
| **Protocol / TLS wrapper** (Burns HTTPS-in-front-of-HTTP) | Speak the modern protocol to the world, legacy to localhost | localhost | Legacy app untouched; sidecar is now on the request path. |

These compose: a mesh sidecar *is* often an ambassador + adapter for
networking. Do not invent a second card for that overlap.

### 3.3 Kubernetes native sidecar containers (KEP-753)

Until 1.28 a "sidecar" was a convention: either an init container that
**exits** (wrong lifetime) or a regular container with **no startup order**
that can **block Job completion**.

| Milestone | What shipped | Source |
|---|---|---|
| **1.28** (2023-08-25 blog) | Alpha. `SidecarContainers` feature gate. `restartPolicy: Always` on an `initContainers[]` entry. Starts in init order; restarts on exit; does **not** keep the Pod alive after main containers exit. Resource managers / `kubectl describe node` were wrong in alpha. | https://kubernetes.io/blog/2023/08/25/native-sidecar-containers/ |
| **1.29** | Beta, **on by default**. | https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/ |
| **1.33** (2025-04-23, "Octarine") | **GA / stable.** Feature locked; setting the gate is ignored. Reverse-order shutdown after main containers stop. Sidecars may use startup / readiness / liveness probes; **OOM score aligned with primary containers**. KEP-753 (SIG Node). | https://kubernetes.io/blog/2025/04/23/kubernetes-v1-33-release/ |
| **1.36** | Feature **gate** removed (feature stays). | kubernetes#129731 release note; #137755 |

API shape (verified docs example): put the helper under `spec.initContainers`
with `restartPolicy: Always`. After that container's `started` status is
true (process running, or `startupProbe` success), the next init container
starts. On termination the kubelet **waits for main containers to stop**,
then SIGTERMs sidecars in **reverse declaration order**. If mains consume
the whole `terminationGracePeriodSeconds`, sidecars may get SIGTERM then
SIGKILL with **non-zero exit** — treat that as normal. Jobs: a native
sidecar **does not** prevent Job success after the main container finishes.

**Resource accounting (docs, fetched 2026-09-13).** Effective init
request/limit = the **highest** request/limit among init containers (a
missing limit is treated as the highest). Pod effective request/limit =
pod overhead + **max**(sum of non-init app+sidecar requests/limits,
effective init request/limit). Scheduler and cgroups use the effective
values. Pod QoS is computed across **all** init, sidecar, and app
containers — one BestEffort container can drag the Pod down.

**Legacy multi-container Pods** (no `restartPolicy` on init) remain valid
when you do not need ordering, or you must run on nodes older than 1.29.

### 3.4 Injection and traffic steal

| Platform | How the sidecar appears | Opt-in |
|---|---|---|
| **Istio** | Mutating webhook. Automatic: label namespace `istio-injection=enabled` (or `istio.io/rev=<rev>`). Manual: `istioctl kube-inject`. `istio-injection` on the namespace wins over `istio.io/rev`. Pod label `sidecar.istio.io/inject=true\|false`. If neither label is set, inject only when `.values.sidecarInjectorWebhook.enableNamespacesByDefault` is on (**off** by default). | https://istio.io/latest/docs/setup/additional-setup/sidecar-injection/ |
| **Linkerd** | Injector webhook or `linkerd inject`. Annotation `linkerd.io/inject`: `enabled` \| `disabled` \| `ingress`. | https://linkerd.io/docs/reference/proxy-configuration/ |
| **Consul Connect** | `consul-k8s` connect-inject webhook. Default **opt-in**: `consul.hashicorp.com/connect-inject: "true"` on the **Pod**. Helm `connectInject.default: true` injects unless annotated false. Namespace allow/deny lists. | https://developer.hashicorp.com/consul/docs/connect/k8s/inject |
| **ECS Service Connect** | ECS **adds** a sidecar at task start. It is **not** in the task definition and is not user-configurable. Reuse one task def across namespaces. | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect-concepts-deploy.html |
| **AWS App Mesh** (EOS **2026-09-30**) | User **declares** an `envoy` container in the task / pod; `proxyConfiguration.type=APPMESH`. | https://docs.aws.amazon.com/app-mesh/latest/userguide/getting-started-ecs.html |

Istio / Linkerd / Consul typically install an **init** (iptables / nft /
CNI) that redirects pod traffic through the proxy. Istio 1.27+ also
supports `values.global.nativeNftables=true`. Interception mode `NONE`
skips the init (Istio injection template).

### 3.5 Startup / shutdown ordering

| Mechanism | Start | Stop | Notes |
|---|---|---|---|
| **K8s native sidecar** | Declared order among `initContainers`; mains wait until sidecar `started` | Mains first, then sidecars reverse-order | `holdApplicationUntilProxyStarts` is a *legacy* workaround. Istio injection template: `$holdProxy := holdApplication… AND NOT $nativeSidecar` — native path adds `preStop: pilot-agent request POST drain`, not a `postStart` wait. |
| **Istio legacy** (`holdApplicationUntilProxyStarts: true`) | Injects sidecar first + `pilot-agent wait` postStart | `terminationDrainDuration` drain | Needed when proxy is a regular container. Global value or `proxy.istio.io/config`. |
| **Istio native** (`ENABLE_NATIVE_SIDECARS`) | K8s ordering | Drain via preStop, then SIGTERM after mains | 1.27 change notes: env **defaults to `true`**. Implementation (istio#57587, AKS docs): auto-enable only when **all nodes are ≥ 1.33** unless the env is set explicitly. Per-pod opt-out annotation name is inconsistent across pages (§8). AKS: default native from cluster **1.33** + add-on `asm-1-29`. |
| **Linkerd** | `config.linkerd.io/proxy-await`: `enabled` \| `disabled` — app containers wait until proxy ready | `proxy-wait-before-exit-seconds` (alpha annotation; **default 0**); `shutdown-grace-period` for open connections | Native sidecars: `config.linkerd.io/proxy-enable-native-sidecar` (alpha/beta aliases deprecated). |
| **Consul** | Init container (defaults §4) then Envoy | `enable-sidecar-proxy-lifecycle`, shutdown drain listeners, graceful port — Helm `connectInject.sidecarProxy.lifecycle.*` | |

**Job / batch** is the case native sidecars were built for (1.28 blog; Istio
dataplane-modes table: Jobs "Complicated by long life of sidecar" vs
ambient "Transparent").

### 3.6 Ambient vs sidecar (mesh placement)

Istio documents two data-plane modes
(https://istio.io/latest/docs/overview/dataplane-modes/, fetched 2026-09-13):

| | **Sidecar** | **Ambient** |
|---|---|---|
| Data plane | Envoy **per pod** (and VMs) | Per-node L4 **ztunnel**; optional per-namespace (or per-service) Envoy **waypoint** for L7 |
| Add a workload | Label + **restart pods** | Label; **no restart** |
| L7 steps on a request | 2 (source + dest sidecar) | 1 (dest waypoint) |
| Latency they publish (p90/p99) | **0.63–0.88 ms** | Ambient **0.16–0.20 ms**; waypoint **0.40–0.50 ms** |
| Resource model | Provision **worst-case per replica** | Waypoints autoscale; many replicas share one waypoint |
| Keys | Strongest: **per-workload** keys. Compromised app pod **has** mesh keys | Strong: node agent holds keys for pods **on that node**. Compromised app **does not** get mesh keys |
| Extensibility | Full, including `EnvoyFilter` | WasmPlugin on waypoint; **EnvoyFilter not supported** |
| Jobs | Sidecar lifetime fights completion | Transparent |
| Server-first protocols | Needs config | Yes |
| Support | Stable, **including multi-cluster** | Stable, **single-cluster only** (unsupported: sidecar↔waypoint interop, multi-network, VMs) |

Ambient is informally "sidecar-less mesh." Hybrid is allowed: pods with
`istio.io/dataplane-mode=ambient` coexist with sidecar pods. Migration
caveat (Istio migrate docs): **sidecar clients bypass waypoints**, so L7
policy on a waypoint is not enforced until the *source* is also ambient.
`VirtualService` in ambient is Alpha; HTTPRoute is the stable L7 path.

Linkerd remains a sidecar (or native-sidecar) data plane; it is not an
ambient mesh. Cilium / other eBPF node proxies are the same *placement*
idea as ztunnel (per-node, not per-pod) — cite as an alternative, do not
deep-dive CNI.

### 3.7 Placement table

| Layer | Fate shared with | Typical use | When it is the wrong layer |
|---|---|---|---|
| **In-process library** (Resilience4j, OTel SDK, mesh client) | Process | Single language; lowest latency | Polyglot fleet; you cannot change the app (C1/C2 still apply). |
| **Sidecar in the Pod / ECS task** | Replica | Mesh, log shipper, Dapr, TLS wrapper | Need independent scale; per-replica cost dominates; platform already does it. |
| **Node proxy / ztunnel / CNI** | Node | L4 mTLS + identity for every pod on the node | Need per-workload key isolation or L7 at every hop. |
| **Namespace / service waypoint** | A *set* of replicas | Shared L7 policy, retries, HTTPRoute | Need client-side L7 (retries from *this* pod) or EnvoyFilter. |
| **Front proxy / gateway (C6)** | None (shared fleet) | North-south TLS, composition, BFF | East-west identity hop-by-hop. |
| **Host daemon** (Azure ambassador alternative) | Host | Many processes, one proxy | Container orchestration already gives you a Pod. |

---

## 4. Verified defaults / standards (knobs)

Fetched 2026-09-13. Envoy itself has **no** CPU/memory product default — the
injector does.

### 4.1 Sidecar resource requests / limits

| Injector (source pin) | CPU request | Memory request | CPU limit | Memory limit |
|---|---|---|---|---|
| **Istio** `istio-discovery` chart `proxy.resources` (`master` raw, 2026-09-13; same numbers since the 1.4-era chart) | **100m** | **128Mi** | **2000m** | **1024Mi** |
| **Istio waypoint** (same file) | 100m | 128Mi | `"2"` | 1Gi |
| **Istio `proxy_init` / validation** (historical 1.4.5 chart; confirm per install) | 10m | 10Mi | 100m | 50Mi |
| **Linkerd** default Helm | **empty** (no request/limit). **1** runtime worker (`runtime.workers.minimum: 1`) | empty | empty | empty |
| **Linkerd HA** `values-ha.yaml` (`main`, 2026-09-13) | **100m** | **20Mi** | *(unset)* | **250Mi** |
| **Consul Connect** `connectInject.sidecarProxy.resources` | **null** (omitted). Comment **"Recommended default: 100m"** | null; recommended **100Mi** | null; recommended **100m** | null; recommended **100Mi** |
| **Consul Connect init** (chart default, not null) | **50m** | **25Mi** | **50m** | **150Mi** |
| **ECS Service Connect** (AWS *recommendation*, not a container `cpu` field — add to **task** size) | **+256** units (0.25 vCPU); **+512** if peak **> 500 rps** | **+64 MiB**; **+128 MiB** if namespace **> 100 services** or **> 2000 tasks** | n/a (task-level) | Fargate task memory floor **512 MiB** |
| **App Mesh Envoy** (docs; EOS 2026-09-30) | **512** units recommended | **≥ 64 MiB**; Fargate lowest settable **1024 MiB** | raise from Container Insights | Image pin at fetch: `aws-appmesh-envoy:v1.39.1.0-prod` |

**Istio annotation trap** (injection docs): if you set
`sidecar.istio.io/proxyCPU` you **must** also set
`sidecar.istio.io/proxyCPULimit` or the CPU **limit becomes unlimited**;
same pairing for memory. Setting only a subset of the four annotations
replaces the whole resources block (istio#35905). Override annotations
(`sidecar.istio.io/proxyCPU` / `proxyMemory` / `proxyCPULimit` /
`proxyMemoryLimit`) are **Alpha**. `LimitRange` can insert requests
*before* the injector runs.

**Linkerd concurrency.** Default kubelet CFS (`none` CPU manager): limit
is a quota. Static CPU manager: Guaranteed QoS (every container
request=limit) **and** proxy CPU request/limit are **integers ≥ 1**.
`maximumCPURatio` 1.0 = one worker per host CPU; 0.2 = one worker per
five cores; CPU **limit beats** the ratio. Annotation examples in the
docs: request `0.2` / limit `1`, memory request `128Mi` / limit `2Gi`.
`proxy-init` resources now **inherit the proxy's** values (linkerd#12741 /
#11320) so Guaranteed QoS is not broken by a leftover 100m init request.

### 4.2 Native-sidecar / injection knobs

| Knob | Verified default |
|---|---|
| K8s `SidecarContainers` | On by default **1.29+**; GA **1.33**; gate ignored / removed **1.36**. |
| Istio `ENABLE_NATIVE_SIDECARS` | 1.27.0 change notes (2025-08-11): **default true**. Runtime: auto-on when every node is **≥ 1.33**, else set the env yourself (istio#57587). |
| Istio `holdApplicationUntilProxyStarts` | Off unless set; **ignored** when native sidecar is on. |
| Istio startupProbe | Chart: `enabled: true`, `failureThreshold: 600` (10 min at 1 s). |
| Istio status port | `15020`. Prometheus merge scrape `:15020/stats/prometheus` (`meshConfig.enablePrometheusMerge` **on** by default). |
| Linkerd `proxy-await` | Documented as annotation `enabled`/`disabled`; HA/docs treat await as the production posture. |
| Linkerd wait-before-exit | **0** s. |
| Linkerd inbound / outbound connect timeout | **100 ms** / **1000 ms**. |
| Consul inject default | **false** (annotation required). |
| Service Connect retries / outlier / timeout | **2** retries; ≥ **5** failed connections in **30 s** → avoid **30–300 s**; `perRequestTimeout` **15 s**; idle HTTP **5 min**, TCP **1 h**. (*Mechanics owned by C1/C2/C7 — listed so placement cost is honest.*) |

### 4.3 Observability of the sidecar itself

A sidecar without **its own** signals is a silent tax. Emit at least:

| Signal | Why |
|---|---|
| **Container CPU / memory** of the proxy (`container_cpu_usage_seconds_total`, `container_memory_working_set_bytes` tagged `container="istio-proxy"` / `linkerd-proxy` / `envoy`) vs its request/limit | The 100m/128Mi defaults are scheduling hints, not a workload profile. OOMKill of the proxy takes the **whole Pod** (shared fate). |
| **Istio standard metrics** from the proxy: `istio_requests_total`, `istio_request_duration_milliseconds`, `istio_request_bytes`, `istio_response_bytes`; TCP: `istio_tcp_{sent,received}_bytes_total`, `istio_tcp_connections_{opened,closed}_total`. Label `reporter=source\|destination` — sidecar-to-sidecar traffic is counted **twice** if you sum both. | https://istio.io/latest/docs/reference/config/metrics/ |
| **Envoy cluster stats** (`envoy_cluster_upstream_cx_active`, `_rq_pending_overflow`, outlier / retry counters) | Placement health of *this* proxy; C1/C2 own the *meaning* of those counters. |
| **Injection / dataplane-mode** | Pods 1/1 vs 2/2; `istio.io/dataplane-mode`; missing webhook = apps running **unmeshed**. |
| **Startup / drain** | Time from Pod scheduled → proxy ready; preStop drain duration; Jobs that never complete (legacy sidecar). |
| **Waypoint vs sidecar mix** | During ambient migration, sidecar→waypoint bypass (Istio migrate docs). |

Alert shapes (own formulations on documented functions — **not** vendor
PromQL; see §8): *sidecar CPU > request for 15 m*; *sidecar OOMKills > 0*;
*proxy not ready while app is Ready* (legacy ordering); *injected replica
count ≠ Deployment replicas*.

OpenTelemetry: there is no sidecar-specific semantic convention. Put the
proxy's spans on the same trace as the app (`traceparent` hop) and tag
`container` / `dataplane_mode`. The Collector *as* a sidecar is the
adapter variant.

### 4.4 Tuning

| Knob | Too aggressive | Too timid | Starting point (sourced) |
|---|---|---|---|
| Sidecar CPU request | 2 cores on a 100 rps CRUD pod | 0 (BestEffort; eviction) | Istio 100m; Linkerd HA 100m; measure p50 then add headroom. |
| Sidecar memory limit | 128Mi on a large-mesh Envoy (config xDS blows it) | no limit (noisy neighbor) | Istio 1024Mi limit / 128Mi request; raise when `envoy_server_memory_*` or OOMKills appear. Pair CPU/mem annotations. |
| Mesh mode | Sidecar on every Job and every replica "for consistency" | Ambient without waypoints while you still need L7 auth | Ambient ztunnel for mTLS-only; waypoint where HTTPRoute / L7 auth lives; sidecar where you need EnvoyFilter, VMs, or multi-cluster (Istio table). |
| Native sidecar | Forced on mixed 1.28/1.33 nodes | Still using `holdApplicationUntilProxyStarts` on 1.33+ | K8s ≥ 1.33 + Istio ≥ 1.27 with env/auto-detect; Linkerd `proxy-enable-native-sidecar` for Jobs. |
| Injection default | Cluster-wide inject (Consul `default: true`, Istio `enableNamespacesByDefault`) | Manual inject only, drift | Namespace label (Istio / Linkerd); Consul stay opt-in until the platform owns it. |
| Task size (ECS SC) | 256 CPU task + SC (proxy eats the app) | Ignore +256/+64 | AWS: add 256 CPU + 64 MiB; 512 CPU if > 500 rps; 128 MiB extra at 100 services / 2000 tasks. |

### 4.5 Worked calibration — inference pod (50 replicas)

Design drill (not a vendor SLA), matching
[ml-microservices-patterns.md](../../../cases/ml-solutions-arch/ml-microservices-patterns.md)
"sidecar on the inference pod ships traces":

Constraints: 50 replicas; app **1 CPU / 2 Gi** request=limit (Guaranteed
if the sidecar matches); east-west mTLS required; L7 retries/timeouts on
the *feature-store* hop only (C2/C7); cluster is Kubernetes **1.33**.

| Step | Choice | Why |
|---|---|---|
| Need | mTLS + identity + L4 telemetry on all hops; L7 only to `feature-store` | Istio L4-vs-L7 table: do not pay two Envoys per request for encrypt-only. |
| Default sidecar bill | 50 × (100m CPU, 128Mi) = **5 CPU, 6.25 Gi** scheduled; limits 50 × (2 CPU, 1 Gi) = **100 CPU / 50 Gi** burst cap | Istio chart defaults. Worst-case limit is why Istio calls sidecar utilization "wasteful." |
| Ambient alternative | ztunnel on each node (say 10 nodes) + **one** waypoint Deployment for `feature-store` (autoscale) | L7 processing steps 1 not 2; published latency 0.16–0.50 ms vs 0.63–0.88 ms. No pod restart to enroll. |
| Keep sidecar when | You need `EnvoyFilter`, multi-cluster, or a VM predictor | Istio "unsupported in ambient" list. |
| If sidecar stays | Native sidecar (`restartPolicy: Always` on `istio-proxy`); set **all four** resource annotations after a load test; `proxyCPU=200m` + `proxyCPULimit=1` + matching memory if p99 proxy CPU > 100m | Avoid unlimited-limit trap; Jobs (batch eval) complete. |
| ECS analog | Same 50 tasks: task size += 256 CPU + 64 MiB (512 CPU if a task exceeds 500 rps) | Service Connect docs. App Mesh path is dying 2026-09-30 — do not start new work there. |
| Rollback | Namespace `istio-injection=disabled` + restart (sidecar); or remove `istio.io/dataplane-mode=ambient` (no restart) | Ambient incremental vs sidecar binary. |
| Do not | Put C1 breaker thresholds in this card; put model code in the sidecar; scale the OTel collector *with* replicas if a cluster collector would do | Azure "daemon or separate service" test. |

---

## 5. Failure modes and when-not-to-use

**Failure modes of the sidecar itself**

- **Shared fate.** Proxy OOM, crash-loop, or iptables init failure takes
  the replica (or makes it unready). Native sidecars restart independently
  but a down mesh proxy still black-holes redirected traffic.
- **Startup race (legacy).** App binds and serves before Envoy is LIVE —
  first requests fail or bypass policy. `holdApplicationUntilProxyStarts`
  / native ordering / Linkerd `proxy-await` exist because this is common
  (Istio "sidecar injection problems").
- **Shutdown race (legacy).** Proxy exits while the app still has in-flight
  RPCs; or a Job never completes because the proxy is a main container.
  Native reverse-order stop + Linkerd wait-before-exit + Istio drain.
- **Per-replica tax / eviction.** 100 pods × 128–256 Mi is 12–25 Gi of
  node memory that is not model weights. QoS: a sidecar without requests
  can make a Guaranteed app Burstable.
- **Config stampede / memory.** Envoy holds per-cluster xDS; large meshes
  without `Sidecar` scope (Istio) blow the 128Mi *request* and then the
  1Gi *limit*. Ambient's pitch: "works without custom configuration."
- **Injection drift.** Webhook down → new pods unmeshed (Istio inject
  logic step 3). `LimitRange` fights injector resource blocks.
- **Annotation partial apply.** Istio CPU request set, limit wiped
  (injection docs + #35905).
- **Ambient hybrid gap.** Sidecar source → ambient dest **skips** the
  waypoint; L7 AuthorizationPolicy silently not enforced (Istio migrate).
- **App Mesh clock.** EOS **2026-09-30**; leftover `envoy` containers are
  unmaintained placement.
- **Double hop vs front proxy.** Putting L7 policy in both a C6 gateway
  *and* every sidecar without a reason.
- **Keys on the app pod.** Istio sidecar column: compromised application
  **has** mesh keys. Ambient: no.

**When not to use (sourced)**

| Situation | Source | Prefer |
|---|---|---|
| **Optimize IPC / frequent chatter** | Azure sidecar "might not be suitable" | In-process library |
| **Small system; per-instance cost dominates** | Azure | Skip, or one node proxy |
| **Must scale the helper independently** | Azure | Separate Deployment (collector, waypoint, daemon) |
| **Platform already provides it** | Azure sidecar + Azure ambassador | Use the platform mesh / gateway |
| **Sidecar-less data plane meets the need** | Azure sidecar; Istio ambient table | Ambient ztunnel (± waypoint); Cilium-class node proxy |
| **Single language, you own the code** | Azure ambassador | Client library (C1/C2 in-process) |
| **North-south composition / BFF** | C6; Envoy front-proxy docs | Gateway, not a per-pod sidecar |
| **Jobs / batch, no native sidecars** | Istio dataplane-modes; K8s 1.28 blog | Ambient, or native sidecars on 1.29+ |
| **Need independent blast radius** | E13 / C8 | Cells, not a sidecar (sidecar *increases* coupling to the replica) |

---

## 6. Cross-links

- **Catalog:** B6 in
  [system-design-patterns-catalog.md](system-design-patterns-catalog.md).
- **Siblings:** C1 / C2 / C7 / C8 (mechanics that *run in* the proxy);
  C6 gateway / BFF / Envoy front proxy; E2 microservices style; E13 / C8
  cells (aws/ch08 cellular).
- **Existing mechanism notes (link, do not rewrite):**
  [aws/ch08.md](../../../cases/aws/ch08.md)
  (sidecar paragraph + service mesh vs API gateway);
  [ml-microservices-patterns.md](../../../cases/ml-solutions-arch/ml-microservices-patterns.md)
  (inference-pod sidecar).
- **Depth-bar examples (do not copy topics):**
  [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md),
  [RetryBackoff.md](../../../cases/SystemDesignPatterns/RetryBackoff.md).
- **Related Azure cards:** Ambassador (egress use of this pattern);
  Gateway Aggregation (C6).

---

## 7. Sources

Retrieved 2026-09-13.

**Canon.** kubernetes.io/blog/2015/06/the-distributed-system-toolkit-patterns
(2015-06-29) · usenix.org/system/files/login/articles/login_oct15_07_burns.pdf
· oreilly.com/library/view/designing-distributed-systems/9781491983638/ch02.html
(Burns, Feb 2018) ·
learn.microsoft.com/en-us/azure/architecture/patterns/sidecar
(`ms.date` 2026-02-17 on MicrosoftDocs/architecture-center) ·
learn.microsoft.com/en-us/azure/architecture/patterns/ambassador ·
learn.microsoft.com/en-us/azure/aks/istio-native-sidecar

**Kubernetes native sidecars.**
kubernetes.io/docs/concepts/workloads/pods/sidecar-containers ·
kubernetes.io/docs/tutorials/configuration/pod-sidecar-containers ·
kubernetes.io/blog/2023/08/25/native-sidecar-containers ·
kubernetes.io/blog/2025/04/23/kubernetes-v1-33-release ·
github.com/kubernetes/enhancements/blob/master/keps/sig-node/753-sidecar-containers/README.md
· github.com/kubernetes/kubernetes/pull/129731 ·
github.com/kubernetes/kubernetes/pull/137755 ·
kubernetes.io/blog/2025/04/22/multi-container-pods-overview

**Istio / Envoy placement.**
istio.io/latest/docs/overview/dataplane-modes ·
istio.io/latest/docs/ambient/overview ·
istio.io/latest/docs/ambient/migrate ·
istio.io/latest/docs/setup/additional-setup/sidecar-injection ·
istio.io/latest/docs/ops/deployment/architecture ·
istio.io/latest/docs/reference/config/annotations ·
istio.io/latest/docs/reference/config/metrics ·
istio.io/latest/docs/ops/integrations/prometheus ·
istio.io/latest/blog/2023/native-sidecars ·
istio.io/latest/news/releases/1.27.x/announcing-1.27/change-notes
(2025-08-11) ·
istio.io/latest/news/releases/1.31.x/announcing-1.31 (2026-08-31) ·
github.com/istio/istio/blob/master/manifests/charts/istio-control/istio-discovery/values.yaml
· github.com/istio/istio/issues/57587 · github.com/istio/istio/issues/35905
· github.com/istio/istio/discussions/53174 ·
envoyproxy.io/docs/envoy/latest/intro/life_of_a_request ·
envoyproxy.io/docs/envoy/latest/intro/deployment_types/service_to_service ·
envoyproxy.io/docs/envoy/latest/intro/deployment_types/front_proxy

**Linkerd / Consul.**
linkerd.io/docs/reference/proxy-configuration ·
linkerd.io/docs/tasks/configuring-proxy-concurrency ·
github.com/linkerd/linkerd2/blob/main/charts/linkerd-control-plane/values.yaml
· github.com/linkerd/linkerd2/blob/main/charts/linkerd-control-plane/values-ha.yaml
· github.com/linkerd/linkerd2/pull/12741 · github.com/linkerd/linkerd2/issues/9796
· developer.hashicorp.com/consul/docs/connect/k8s/inject ·
developer.hashicorp.com/consul/docs/reference/k8s/annotation-label ·
github.com/hashicorp/consul-helm/blob/master/values.yaml
(`sidecarProxy.resources` recommended 100m/100Mi, default null; init
50m/25Mi request, 50m/150Mi limit)

**AWS.**
docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect-concepts-deploy.html
· docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect-concepts.html
· docs.aws.amazon.com/app-mesh/latest/userguide/envoy.html
(v1.39.1.0-prod; 512 CPU / ≥64 MiB; EOS 2026-09-30) ·
docs.aws.amazon.com/app-mesh/latest/userguide/getting-started-ecs.html ·
aws.amazon.com/blogs/containers/migrating-from-aws-app-mesh-to-amazon-ecs-service-connect

**Workspace.** cases/aws/ch08.md ·
cases/ml-solutions-arch/ml-microservices-patterns.md ·
docs/research/sysdesign/system-design-patterns-catalog.md ·
docs/research/sysdesign/circuit-breaker-external-research.md (mesh *mechanics*)

---

## 8. Uncertain / left out (excluded from the Concept)

- Istio 1.27 change-note annotation `sidecar.istio.io/native-side` vs
  Kyma/SAP `sidecar.istio.io/nativeSidecar` vs injection-template
  `$nativeSidecar` — **which annotation string is authoritative** was not
  reconciled on istio.io this fetch. Concept should say "per-pod native
  opt-out exists" and cite the live annotation reference, not a guessed
  key.
- `ENABLE_NATIVE_SIDECARS` "default true" (1.27 notes) vs auto-detect
  **only on 1.33+ nodes** (istio#57587 maintainers). Treat the 1.33 gate
  as the operational fact; the release note is incomplete.
- Istio `proxy_init` resource numbers on **1.31** were not re-read from
  the current injection template; 10m/10Mi/100m/50Mi is the historical
  chart default.
- Linkerd `proxy-await` **chart** default (`true` vs annotation-only) —
  docs describe the annotation, not a numeric Helm default in the pages
  fetched.
- Envoy *product* has no sidecar CPU/memory default; any blog that
  states "Envoy defaults to 100m" is repeating Istio.
- johal.in / OneUptime posts claiming Istio 1.24 limits of 100m CPU —
  **contradict** the chart (limit **2000m**). Not used.
- Burns 2018 book body beyond the freely posted chapter summary and the
  2015 blog — not copied; no page-level quotes.
- Azure Learn HTML did not surface `ms.date`; **2026-02-17** is from the
  GitHub `sidecar.md`.
- Dapr sidecar resource defaults — not fetched (example only).
- Cilium service-mesh / node-proxy numeric defaults — not fetched.
- PromQL alert recipes — none found; §4.3 shapes are this note's.
- Service Connect: whether HTTP 5xx (not just failed connections) feeds
  outlier detection — already flagged in the C1 research note; not
  re-litigated.
- App Mesh EKS → VPC Lattice as the *EKS* successor — banner/blog only;
  no Lattice sidecar-equivalent fetched (Lattice is not a sidecar).
- Istio published ambient latency (0.16–0.88 ms) has **no** linked
  benchmark method on the dataplane-modes page; reproduce as "Istio
  states," not as a universal SLA.
- `GOMEMLIMIT` / `GOMAXPROCS` chart defaults added in 1.27 — control
  plane, not the sidecar; left out.
