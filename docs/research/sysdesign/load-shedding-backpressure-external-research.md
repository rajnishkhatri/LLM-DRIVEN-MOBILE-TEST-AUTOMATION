---
type: research
title: 'Load shedding & backpressure — external research (2026-09-13)'
description: >-
  Source-verified research backing the Load shedding Concept (C10): Envoy
  overload manager and admission-control filter defaults, CoDel RFC 8289 and
  Facebook's adaptive-LIFO/controlled-delay, Kubernetes API Priority and
  Fairness, per-layer backpressure (TCP rwnd, HTTP/2 windows, Reactive
  Streams, Node streams, Kafka pull), queueing math, shed placement and
  criticality, brownout, and the queues-don't-fix-overload failure mode.
tags: [research, load-shedding, backpressure, overload, system-design-patterns]
---

# C10 Load shedding & backpressure — external research (2026-09-13)

**Method.** Facts verified against primaries 2026-09-13 (paywalled ACM read from an Internet Archive capture). **[cited forward]** = verified in [circuit-breaker-external-research.md](circuit-breaker-external-research.md): Yanacek load shedding; SRE ch. 21 adaptive throttling + ch. 22 retry amplification + queue ≤ 50%; Netflix 2018 adaptive concurrency + 2024 prioritized shedding; Uber Cinnamon PID/Vegas/768 priorities; Stripe shedders; Envoy adaptive-concurrency filter + breaker thresholds; concurrency-limits; Kafka pause/resume.

## 1. Envoy overload manager and admission control

- **Overload manager** (1.40.0-dev): **off until the Bootstrap `overload_manager` field is configured.** Resource monitors: fixed_heap, global_downstream_max_connections, cgroup_memory, cpu_utilization. Actions (exact names): `stop_accepting_requests` (immediate **503**), `disable_http_keepalive` (GOAWAY h2/h3, close idle h1), `stop_accepting_connections`, `reject_incoming_connections`, `shrink_heap`, `reduce_timeouts`, `reset_high_memory_stream` (singular), `close_idle_http_connections`. Triggers: `threshold` (binary) or `scaled` (linear ramp between scaling and saturation thresholds). Worked example: disable keepalive at heap 0.92, stop accepting at 0.95. Load-shed points fire deep in the path (tcp_listener_accept, http_connection_manager_decode_headers, …).
- **Admission control filter** (`envoy.filters.http.admission_control`; defaults from the raw proto, authoritative): per-thread success-rate shedder; rejection probability grows as `((total − successes/threshold)/(total+1))^(1/aggression)`. Defaults: enabled if unspecified; `sampling_window` **30 s**; `aggression` **1.0** (< 1 clamped); `sr_threshold` **95%**; `rps_threshold` **0**; `max_rejection_probability` **80%** (so the estimate can recover). Success defaults: HTTP **< 500**; gRPC OK/Cancelled/Unknown/InvalidArgument/NotFound/AlreadyExists/Unauthenticated/FailedPrecondition/OutOfRange/PermissionDenied/Unimplemented. Rejection = **503** (source line verified).

## 2. Queue disciplines

- **CoDel (RFC 8289, Jan 2018, Experimental)**: controls **sojourn time**, not length; "TARGET SHOULD be set to 5 ms", INTERVAL **100 ms** (RTTs 10 ms–1 s); drop when the *minimum* sojourn exceeds TARGET for a full INTERVAL; while dropping, next drop at `t + INTERVAL/√count`; goal parameterless AQM; Appendix A extends to data-center servers.
- **Facebook "Fail at Scale"** (Maurer, ACM Queue 13(8), 2015-10-27; archive capture): three amplifiers — rapid config changes, hard core dependencies, latency/resource exhaustion. Mechanisms: **controlled delay** — if the queue hasn't drained in the last N, entries get only M ms of queue budget; "5 milliseconds for M and 100 ms for N" needs no per-service tuning; accepts slightly more than capacity "so it never goes idle" (Wangle/Thrift). **Adaptive LIFO** — FIFO normally; queue forming → LIFO (oldest likely abandoned; newest most likely to matter); composes with CoDel (HHVM). **Client-side concurrency cap** per service as a stopgap.

## 3. Kubernetes API Priority and Fairness

Gate alpha 1.18 / beta 1.20 / **GA 1.29**; on by default (`--enable-priority-and-fairness=false` to opt out); flowcontrol.apiserver.k8s.io/**v1** since 1.29. Model: FlowSchema → PriorityLevelConfiguration; per-level concurrency; flows separated by **shuffle sharding** + fair queuing; total = max-requests-inflight + max-mutating (distinction dropped). **Seats**: LIST charged by estimated objects; watches charged for the initial burst; writes charged for notification fan-out; `nominalConcurrencyShares` with lend/borrow. Defaults: mandatory `exempt` + `catch-all`, suggested node-high / system / leader-election / workload-high / workload-low / global-default. Shedding: `type: Reject` → **429** with an **adaptive Retry-After** (per-level, from a dropped-requests tracker — apiserver source verified); `type: Queue` per queues/queueLengthLimit/handSize.

## 4. Backpressure per layer

- **TCP (RFC 9293, STD 7)**: 16-bit Window = octets the receiver will accept — a continuously re-issued byte credit; zero window → sender stops and probes (persist timer); > 65,535 needs window scale (RFC 7323).
- **HTTP/2 (RFC 9113)**: credit at **stream and connection** level, both starting **65,535**; SETTINGS_INITIAL_WINDOW_SIZE changes stream windows only (connection only via WINDOW_UPDATE); only DATA consumes. §5.2.1: flow control is **per hop** — an intermediary that buffers re-issues credit regardless of the downstream. Concrete: NGINX `proxy_buffering` default **on** (memory + up to `proxy_max_temp_file_size` **1024m** of disk per response); `proxy_request_buffering` on.
- **Reactive Streams 1.0.4**: demand via `request(n)` (rule 2.1); onNext count ≤ demand (1.1); serial signals (1.3); request(≤ 0) error (3.9); cumulative ≥ Long.MAX_VALUE = "effectively unbounded" (3.17) — the opt-out. Reactor: onBackpressureBuffer (bounded form takes an overflow strategy) / Drop / Latest / Error. RxJava BackpressureStrategy: BUFFER ("Buffers all onNext values" — unbounded), ERROR (MissingBackpressureException), DROP, LATEST, MISSING.
- **Node streams** (v26.8.2): getDefaultHighWaterMark — **16** objects; bytes **64 KiB non-Windows / 16 KiB Windows** (bumped in v22.0.0); `write()` false → wait for `'drain'`; ignoring it: "Node.js will buffer all written chunks until maximum memory usage occurs" then aborts; highWaterMark is a threshold, not a limit; pipe()/pipeline() manage it.
- **Kafka consumer = pull backpressure** (4.1): `max.poll.records` **500**; `fetch.max.bytes` **50 MiB** (first-batch exception); `max.partition.fetch.bytes` **1 MiB**; `fetch.min.bytes` 1 / `fetch.max.wait.ms` 500; **`max.poll.interval.ms` 300 000** — the tripwire: slower processing → consumer considered failed, group rebalances.

## 5. Queueing math

- **Brooker "Latency Sneaks Up On You" (2021-08-05)**: M/M/1 `E[N] = ρ/(1−ρ)` — 1 at ρ=0.5, 99 at ρ=0.99; same 1/(1−ρ) blow-up for time in system; high percentiles blow up first → **percentile latency is the leading indicator of overload**; efficiency wins mask fragility.
- **Little's law** (Little 1961, DOI 10.1287/opre.9.3.383): concurrency ≈ rate × latency [cited forward for the limit rule].
- **Bounded queues**: SRE queue ≤ ~50% of pool [cited forward]; Fail-at-Scale's alternative — bound queue *time* (M = 5 ms once not draining), tuning-free; RFC 8289 is the same idea a layer down.

## 6. Where to shed; what first

- Edge/LB: Envoy overload manager 503 before upstream work; load-shed points at accept. Sidecar: admission-control filter; adaptive concurrency [cited forward]. In-app middleware: Cinnamon (RPC middleware; priorities propagated via Jaeger; PID rejection ratio + Vegas inflight limit) [placement verified; internals cited forward]; concurrency-limits interceptors (429). Client: SRE adaptive throttling [cited forward]; Fail-at-Scale per-service outstanding cap.
- **What first — SRE ch. 21 (verified)**: criticality CRITICAL_PLUS / CRITICAL (default for production jobs) / SHEDDABLE_PLUS / SHEDDABLE, **propagated automatically** by the RPC system. Utilization signals: CPU rate, memory, and the preferred **executor load average** (active threads, exponentially decayed; shed above processors available). Rejections still burn CPU — a backend can be overloaded doing nothing but rejecting → push shedding client-ward.

## 7. Brownout

Klein et al., ICSE 2014: mark code **optional**; a control-theoretic controller deactivates it dynamically; withstands flash crowds/failures without over-provisioning; RUBiS/RUBBoS < 170 LOC. Third lever next to shedding (drop requests) and backpressure (slow producers): shrink work per request.

## 8. Failure modes

- **Shedding hides latency**: fast rejections dominate server metrics; measure goodput + client latency [cited forward]; Brooker's twin trap — mean utilization hides the knee percentiles reveal.
- **Over-shedding / collapse**: static limits mis-set [cited forward]; SRE rejection-cost spiral (verified); Uber's earlier CoDel-based QALM rejected nearly everything under deep overload, oscillating — Cinnamon's PID was built to fix that.
- **Retry priority inversion** (synthesis; grounded facts verified): retries inherit the original criticality (automatic propagation; default CRITICAL) while multiplying load; mitigations — 10% budgets, "overloaded; don't retry", one-layer retries, APF's adaptive Retry-After.
- **Unbounded buffering → OOM**: Hébert, "Queues Don't Fix Overload" (ferd.ca, 2014-11-19) — a queue before a bottleneck buys time, then fails rarer-but-worse; fix = backpressure or shedding at the true bottleneck. Same trap in official docs: Node buffer-until-abort; RxJava BUFFER; Reactor unbounded buffer; NGINX spooling 1 GB to disk per response by default.

## Sources

Envoy overload_manager config page + admission_control filter + raw proto + admission_control.cc (main) · RFC 8289 · queue.acm.org 2839461 via Internet Archive ("Fail at Scale") · kubernetes.io flow-control (stable v1.29) + feature-gates-removed + apiserver priority-and-fairness.go · RFC 9293 · RFC 9113 · nginx.org ngx_http_proxy_module · reactive-streams-jvm README 1.0.4 · projectreactor.io 3.8.7 operator appendix · RxJava 3.x BackpressureStrategy.java · nodejs.org stream (v26.8.2) + node main doc/api/stream.md · kafka.apache.org/41 consumer config · brooker.co.za utilization (2021-08-05) · Little 1961 DOI · sre.google handling-overload · uber.com Cinnamon post · Lund portal Brownout (ICSE 2014) · ferd.ca queues-don-t-fix-overload (2014-11-19).

## Uncertain / could not verify (excluded from the Concept)

- "Cold-start after drains" is not in Fail at Scale; the verified adjacent claim is accepting slightly more than capacity to never go idle.
- Envoy admission-control overview-page extraction disagreed with the proto; proto values (30 s / 0 / 80% / < 500) are authoritative.
- Retry priority inversion is synthesis — label as analysis.
- APF gate-removal release ambiguous (1.30 vs 1.31).
- Brownout "dimmer" is paper-body vocabulary — not asserted.
- Little 1961 volume/pages inferred from DOI, INFORMS blocked.
- Netflix 2020 priority-bucket post unverified (Medium block); rely on the 2024 post.
- Live ACM pages 403; archive capture used.
