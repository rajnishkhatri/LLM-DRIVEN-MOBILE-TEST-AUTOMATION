---
type: research
title: 'Failover, health checks, graceful degradation & kill switches — external research (2026-09-13)'
description: >-
  Source-verified research backing the Failover and Graceful degradation
  Concepts (C3/C11): Kubernetes probe defaults, gRPC health protocol, Envoy
  active checks, the Builders' Library health-check taxonomy, RTO/RPO and the
  four AWS DR strategies, Route 53 health-check mechanics and fail-open rules,
  RDS/Aurora/Patroni failover timings, static stability, RFC 5861 stale
  serving, SRE degradation, brownout, OpenFeature, kill-switch flags, and the
  GitHub 2018 split-brain post-mortem.
tags: [research, failover, health-checks, graceful-degradation, kill-switch, system-design-patterns]
---

# C3/C11 Failover & health checks · Graceful degradation & kill switches — external research (2026-09-13)

**Method.** Facts verified against primary pages 2026-09-13 (Kubernetes additionally from the website source markdown). **[already verified]** = cited forward from [circuit-breaker-external-research.md](circuit-breaker-external-research.md) / [retry-backoff-external-research.md](retry-backoff-external-research.md): ALB/NLB health-check defaults + fail-open tuning, Envoy outlier detection + panic 50%, Istio minHealthPercent 0, ECS Service Connect, Cloudflare 2026 deployment breaker, Slack 2022 / GitHub 2025-08 / DynamoDB 2015 / Kinesis 2020 incidents, Resilience4j/Polly kill-switch states.

## 1. Health checking

- **Kubernetes probes**: startupProbe gates liveness/readiness ("do not begin until the startup probe has succeeded"); liveness failure → restart; readiness failure → Pod IP removed from EndpointSlices (container keeps running). Defaults: `initialDelaySeconds` 0; `periodSeconds` **10 s**; `timeoutSeconds` **1 s**; `successThreshold` **1** ("Must be 1 for liveness and startup"); `failureThreshold` **3**; probe-level terminationGracePeriodSeconds inherits pod 30 s. Mechanisms: exec (forks per probe — CPU overhead), httpGet (success 200–399; body read capped 10 KiB), tcpSocket, grpc (stable v1.27; numeric port only; `service` = health service name). Slow starters: startup probe with a high failureThreshold instead of loosening liveness. Documented cautions: liveness "should be used with caution", must indicate unrecoverable failure (deadlock); "Incorrect implementation of liveness probes can lead to cascading failures"; backing-service dependencies belong in **readiness**, not liveness; common pattern — same endpoint, higher liveness failureThreshold.
- **gRPC Health Checking Protocol** (grpc.health.v1): unary Check, streaming Watch; `service: ""` = overall health; ServingStatus UNKNOWN/SERVING/NOT_SERVING/SERVICE_UNKNOWN (Watch; Check returns NOT_FOUND). Watch sends current status immediately then on change. Guide: polling Check "does not scale"; client-side health checking via service config `healthCheckConfig{serviceName}` — requests held until healthy; unhealthy subchannel → TRANSIENT_FAILURE so the balancer picks another (fail-closed per subchannel).
- **Envoy active health check** (`core.v3.HealthCheck`): `timeout`, `interval`, `unhealthy_threshold`, `healthy_threshold` all **required** (no defaults); startup: one success suffices; `no_traffic_interval` default **60 s**; `reuse_connection` true; jitter options; HttpHealthCheck.path required, expected_statuses default 200 only.
- **AWS Builders' Library "Implementing health checks"** (Yanacek; verified via the aws.amazon.com/jp mirror): opening incident — servers returning blank error pages still passed LB responsiveness checks and, failing *fast*, drew a disproportionate share ("black hole"). Taxonomy: **liveness** (connectivity/process), **local** (disk writable, support processes), **dependency** (credentials, peers, bad state), **anomaly detection** (vs fleet: clock skew, old code). Fail-open: all-unhealthy → NLB/ALB route to all; Route 53 analogous. Risk: a dependency check turns a soft dependency hard and can fail the fleet simultaneously — deep checks belong in external monitoring, not the LB routing decision.
- **Anti-pattern (cross-source)**: dependency-checking health checks → correlated fleet-wide unhealthiness and cascading restarts (kubernetes.io liveness caution; Yanacek fail-open + external monitors).

## 2. Failover

- **Active-active vs active-passive** (Route 53 guide): active-passive = failover routing policy (secondary only when primary unhealthy); active-active = any non-failover policy, unhealthy records dropped from answers. DR whitepaper: passive site serves nothing until failover; fully scaled passive = hot standby.
- **RTO/RPO** (DR whitepaper): RTO = "the maximum acceptable delay between the interruption of service and restoration of service"; RPO = "the maximum acceptable amount of time since the last data recovery point".
- **Four AWS DR strategies** (REL13-BP02 tiers): backup & restore (RPO hours / RTO ≤ 24 h; PITR to ~5 min RPO); pilot light (RPO minutes / RTO tens of minutes; data live, app servers off — "cannot process requests without additional action"); warm standby (RPO seconds / RTO minutes; scaled-down but functional; more scale = lower RTO and less control-plane reliance); multi-site active/active (RPO ~0 / RTO ~0; corruption recovery still needs backups). Write strategies: global (Aurora Global Database — promote secondary "in less than one minute", replication < 1 s), local (DynamoDB global tables, last-writer-wins), partitioned (bi-directional S3). Caution: automatic failover on alarms "should be used with caution" — manually initiated, fully automated ("push of a button") is common; Route 53 ARC health checks "act as on/off switches" over a highly available **data-plane** API.
- **Route 53 health checks**: `RequestInterval` default **30 s** (or 10 s fast; immutable); `FailureThreshold` default **3** (1–10). ≥ 3 checker regions, uncoordinated (bursts). Healthy iff **> 18%** of checkers say healthy. HTTP: TCP connect ≤ 4 s then 2xx/3xx ≤ 2 s (HTTPS certs NOT validated); TCP connect ≤ 10 s; string match in first **5,120 bytes**. CALCULATED (≤ 256 children; HealthThreshold 0 = always healthy); `Disabled` = always healthy; `Inverted`; new checks healthy until data; CloudWatch-alarm checks: InsufficientDataHealthStatus Healthy|Unhealthy|LastKnownStatus.
- **All-unhealthy behavior**: records without a health check are always healthy. Failover pair: both unhealthy → **primary** returned; secondary without check = healthy whenever primary unhealthy. Group rule verbatim: "If no record is healthy, all records are healthy" (documented fail-open). Zero-weighted standby only used when all nonzero-weight records are unhealthy.
- **DNS TTL pitfalls**: health-checked records "specify a TTL of 60 seconds or less"; RDS/Aurora failover flips DNS, so JVM `networkaddress.cache.ttl` matters ("some Java configurations" never refresh); RDS Proxy "bypasses DNS caches to reduce failover times by up to 66%".
- **Database failover times** (docs): RDS Multi-AZ instance "typically 60–120 seconds" (DNS flip; triggers include patching, unhealthy primary, storage failure, reboot-with-failover). Multi-AZ DB cluster (two readable standbys, semisync) "typically under 35 seconds". Aurora replica promotion "typically … less than 60 seconds, and often less than 30"; priorities tier 0–15; no replica → new instance "typically takes less than 10 minutes".
- **Patroni** (4.1.x dynamic config): `ttl` **30 s** (min 20), `loop_wait` **10 s**, `retry_timeout` **10 s**, rule **`loop_wait + 2 × retry_timeout ≤ ttl`**; `maximum_lag_on_failover` **1 MiB**; `primary_start_timeout` 300 s; `synchronous_mode` off; `failsafe_mode` false.
- **Split-brain / fencing (ops)** (Pacemaker 2.1 docs): fencing = making a node unable to run resources even when unresponsive; **STONITH**; without fencing, recovering resources elsewhere risks split-brain corruption; power fencing vs fabric fencing. (Fencing tokens covered in-repo.)

## 3. Static stability; control plane vs data plane

**AWS Builders' Library "Static stability using Availability Zones"** (Weiss & Furr): a statically stable system "keeps working even when a dependency becomes impaired" — no changes/deploys/config during the outage; don't depend on the **control plane** during recovery (more moving parts than the data plane, statistically more likely impaired); zonal deployment calendars; zone-local architectures; **pre-provisioning**: three AZs → overprovision 50%, each AZ at ~66%, an AZ loss absorbed with no scale-up. Corroborated: DR whitepaper ("use only data plane operations as part of your failover"); REL13-BP02 anti-pattern "Dependency on control plane operations during recovery" (Auto Scaling is control-plane); REL11-BP04 "Rely on the data plane and not the control plane during recovery"; ARC toggles are data-plane, changing record weights is control-plane.

## 4. Graceful degradation

- **RFC 5861** (2010, Informational): `stale-while-revalidate=N` (serve stale up to N s past freshness while revalidating in the background); `stale-if-error=N` (request or response directive; serve stale ≤ N s stale on errors = anything producing **500/502/503/504**; past the limit, pass the error).
- **SRE ch. 22 "Load Shedding and Graceful Degradation"**: degradation reduces work per response (small in-memory candidate index vs full disk index; cheaper ranking; omit auxiliary content). Decide the trigger metric (CPU, latency, queue length, threads), the actions, the layer. Warnings: monitor/alert when active; **exercise the emergency path regularly** or it won't work; keep trigger logic simple against feedback loops.
- **Netflix degraded/fallback taxonomy** (Hystrix wiki "How To Use"): Fail Fast; Fail Silent (empty/removed); Fallback Static (in-code defaults); Fallback Stubbed (partly from request state); Fallback Cache-via-Network (stale from memcached — itself a network call: wrap in its own command); Primary + Secondary with Fallback (façade choosing path).
- **Brownout** (Klein et al., ICSE 2014, DOI 10.1145/2568225.2568227): mark code **optional**; a control-theoretic controller dynamically deactivates it; apps "robustly withstand unpredictable runtime variations, without over-provisioning"; RUBiS/RUBBoS retrofits < 170 LOC each.

## 5. Kill switches and flags

- **OpenFeature** (openfeature.dev; CNCF **Incubating** — accepted 2022-06-17, incubating 2023-11-21): vendor-agnostic feature-flag API standard — Evaluation API, evaluation context, providers, hooks, events; server + client SDKs.
- **Kill-switch flags** (LaunchDarkly docs): "permanent boolean flags" (Enabled/Disabled), for shutting off non-core functionality or third-party integrations in emergencies; deliberately simple targeting; can be wired to observability for automated shutoff (flag triggers).
- **"Big red button"** (Google SRE "Twenty years of SRE lessons learned", lesson #4): a simple, easy-to-trigger safety action reverting the risky change; identify buttons *before* the risky action. Companions: #2 recovery mechanisms tested before the emergency; #7 intentionally degrade performance modes; #9 automate mitigations. Infra counterparts: Route 53 ARC on/off controls; breaker FORCED_OPEN/DISABLED/Isolate **[already verified]**.

## 6. Failover gone wrong — GitHub 2018-10-21 (official post-incident analysis)

- 22:52 UTC: routine optical-equipment replacement → **43 seconds** of lost connectivity between the East Coast hub and the primary East Coast data center.
- Orchestrator (MySQL HA) promoted primaries in the **West Coast** DC and directed writes there.
- Split-brain: East Coast held writes never replicated west (busiest cluster: **954 writes** in the window) while West accumulated new writes — "both data centers now contained writes that were not present in the other".
- GitHub chose integrity over availability: webhooks and Pages paused 23:19; restore-from-backup + resync took hours; **24 h 11 m** degraded.
- Remediation: Orchestrator reconfigured "to prevent the promotion of database primaries across regional boundaries" (~60 ms cross-country latency made single-primary topology untenable).

## 7. Fail-open vs fail-closed — verified rows

| System / knob | All-bad / missing signals behavior | Default |
|---|---|---|
| Route 53 record selection | "If no record is healthy, all records are healthy" | Fail-open |
| Route 53 failover pair | Both unhealthy → primary; secondary w/o check healthy when primary unhealthy | Fail-open toward primary |
| Route 53 check status | New checks healthy until data; Disabled = always healthy; CALCULATED threshold 0 = always healthy | Fail-open |
| ALB/NLB target groups | All unhealthy → route to all; tunable minimum_healthy_targets | Fail-open **[already verified]** |
| Envoy outlier detection | max_ejection_percent 10%; panic < 50% healthy → spread or fail-all | Fail-open guardrails **[already verified]** |
| Istio outlierDetection | minHealthPercent 0% (panic surface off) | Panic off **[already verified]** |
| Kubernetes readiness | Failed → removed from EndpointSlices; all unready → no ready endpoints | **Fail-closed** |
| K8s publishNotReadyAddresses | All endpoints "considered 'ready' even if the Pods themselves are not" (headless/StatefulSet discovery) | Opt-in fail-open |
| K8s traffic policy Local | No node-local endpoints → dropped by kube-proxy; terminating-endpoint fallback only when all local are terminating | Fail-closed per node |
| gRPC client health checking | Requests held until healthy status; unhealthy → TRANSIENT_FAILURE | Fail-closed per subchannel |
| K8s liveness | Failure → restart; cascading-failure caution | Fail-closed with restart risk |

Rationale for the split (Yanacek): fleet-blast-radius layers (DNS, LB) fail open because an all-fail signal is often a check bug or dependency blip; per-endpoint gates fail closed because a healthy sibling absorbs the traffic.

## Sources

Kubernetes probes + lifecycle + virtual-ips + Service API (docs + website source md) · grpc/grpc doc/health-checking.md + grpc.io health guide · envoyproxy.io core/v3/health_check.proto · aws.amazon.com/builders-library implementing-health-checks (jp mirror) + static-stability-using-availability-zones · AWS DR whitepaper (BCP + options pages) · wellarchitected REL13-BP02 (REL11-BP04 by reference) · Route 53 API_HealthCheckConfig + developer guide (failover types, choosing records, endpoint health, failover record values) · RDS Multi-AZ instance + cluster + Aurora high availability pages · patroni.readthedocs.io dynamic_configuration (4.1.x) · clusterlabs.org Pacemaker 2.1 fencing · rfc-editor.org/rfc/rfc5861 · sre.google/sre-book/addressing-cascading-failures · Netflix/Hystrix wiki How-To-Use · dl.acm.org/doi/10.1145/2568225.2568227 (+ Lund portal) · openfeature.dev + cncf.io/projects/openfeature · launchdarkly.com/docs killswitch flags · sre.google twenty-years-of-sre-lessons-learned · github.blog/2018-10-30-oct21-post-incident-analysis.

## Uncertain / could not verify (excluded from Concepts)

- Yanacek article: exact English phrasing via the jp mirror; "gray failure" as literal vocabulary unverified (concept present as anomaly detection).
- Static-stability figures (50%/66%) via a summarizer pass — high confidence, not raw-quoted; article publication date not shown.
- "Twenty years" page undated (2023 anniversary); the 2016 Calendar-outage origin claim not asserted.
- No documented statement that a ClusterIP Service with zero ready endpoints actively *rejects* connections — excluded from the matrix.
- Patroni maximum_lag_on_failover default: medium-high confidence (readthedocs via search).
- Netflix 2012 tech-blog post Medium-blocked; taxonomy from the Hystrix wiki.
- Brownout PDF not extractable; abstract-level only; "dimmer" is paper-body vocabulary — not asserted.
- GitHub 2018: only the §6 numbers verified; secondary accounts' extra details not.
- Route 53 health-checks-values.html failed to render; API reference used.
- DR whitepaper last-updated date not displayed.
