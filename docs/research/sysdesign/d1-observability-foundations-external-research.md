---
type: research
title: 'Monitoring & observability foundations — external research (2026-09-13)'
description: >-
  Catalog-owned taxonomy of metric / log / trace / profile / exemplar / baggage;
  Google four golden signals, RED, and USE; current OpenTelemetry signal model;
  tool-neutral defaults; alerting policy foundations; failure modes of the
  telemetry pipeline itself.
tags: [research, system-design-patterns, D1, observability, monitoring]
---

# Monitoring & observability foundations — external research (2026-09-13)

> **What this is.** The Group D taxonomy note. D1 defines the signal vocabulary
> and the golden-metric frameworks. D2 (client), D3 (server), D4 (tracing), and
> D5 (SLOs) consume these definitions; they must not re-define **metric**,
> **log**, **trace**, or **profile**. C1 breaker observability is *placement*
> of those signals on a breaker, not a second taxonomy.
>
> **Method.** Primary pages fetched 2026-09-13. Numbers and identifiers are
> reproduced exactly. Paraphrase elsewhere. Items that could not be verified
> sit in §8 and are not implied as fact.

---

## 1. Scope and non-goals

**This note owns**

- The catalog definitions of **metric**, **log**, **trace**, **profile**, and
  (where the spec is stable) **exemplar** and **baggage**.
- The three golden-metric frameworks and how they compose: Google four golden
  signals (Rob Ewaschuk, SRE book ch. 6, 2016); RED (Tom Wilkie / Weaveworks,
  2015); USE (Brendan Gregg, 2012).
- The OpenTelemetry *signal* model at the current specification version, plus
  the pillars-versus-signals debate (Cindy Sridharan; Charity Majors).
- Cardinality as a first-class cost and correctness constraint.
- Alerting *policy foundations* (symptom vs cause; page vs ticket vs
  dashboard; when a page is justified). Burn-rate math, error budgets, and
  SLO documents are **D5**.
- Tool-neutral defaults a later Concept can quote without picking a vendor.
- Failure modes of monitoring itself: the telemetry pipeline as a dependency.

**Explicit non-goals (sibling owners)**

| Sibling | Owns | Must not do |
|---|---|---|
| **D2** | RUM, web vitals, crash/error reporting, mobile client telemetry | Re-define “metric.” Apply D1’s metric/log/trace to the client. |
| **D3** | Server-side dashboards, scrape/export topology, host/process collectors | Re-define “metric” or re-derive RED/USE/golden signals. Place them. |
| **D4** | Trace graphs, sampling, W3C Trace Context, correlation IDs | Re-define “trace.” D1 states what a trace *is*; D4 states how it *propagates*. |
| **D5** | SLIs / SLOs / error budgets, multiwindow burn-rate alerts | Re-derive “what to measure.” D1 names the signals; D5 names the contract. |
| **C1** | Breaker state, trip rate, not-permitted calls | Invent a fourth signal type. C1 is placement on a breaker. |

Existing `cases/` notes already cover percentiles, metastable failure, and
the POC-to-production reliability stack. Cite them; do not re-derive them.

---

## 2. Lineage / vocabulary

**Monitoring vs observability.** Ewaschuk’s SRE ch. 6 (April 2016) defines
**monitoring** as collecting, processing, aggregating, and displaying
real-time quantitative data (query counts, error counts, processing times,
server lifetimes). **White-box** inspects internals (metrics endpoints, logs,
JVM profiling interfaces). **Black-box** tests externally visible behaviour
as a user would see it. The SRE Workbook ch. 4 (Frame, Lenton, Thurgood,
Tolchanov, Trdin; 2018) adds that monitoring data also includes text logging,
structured event logging, distributed tracing, and event introspection, and
that metrics plus structured logs are what SRE uses most for paging and
dashboards. The financial-architecture notes in this tree already paraphrase
the industry shift: monitoring evolved from reactive checks to
**observability** — inferring internal behaviour from external outputs — and
call it a data-management problem first
([monitoring-observability.md](../../../cases/fincancial-data-architecture/monitoring-observability.md)).

Sridharan, *Distributed Systems Observability* (O’Reilly, first edition May
2018 / first release 2018-05-11), ch. 4: logs, metrics, and traces are
“often known as the three pillars of observability,” and *having* the three
does not by itself make a system observable. Her earlier essay “Logs and
Metrics” (Medium / copyconstruct) treats logs and metrics as complementary
white-box techniques that, with distributed request tracing, form those
three pillars. Charity Majors (paraphrase, not quote): **“pillar” is a
marketing term; “signal” is a technical term** (“How many pillars…”,
2025-10-30). She treats siloed per-signal stores as Observability 1.0 and
wide structured events in one store as Observability 2.0 (“Is It Time To
Version Observability?”, 2024-08-07). OTel’s own docs use **signal**, not
pillar.

**Four golden signals — Rob Ewaschuk, SRE book ch. 6 (2016).** If you can
only measure four metrics of a user-facing system, measure **latency,
traffic, errors, saturation**. Page a human when one is problematic, or,
for saturation, *nearly* problematic.

| Signal | Ewaschuk’s definition (paraphrase; identifiers exact) |
|---|---|
| **Latency** | Time to service a request. Split successful vs failed: a fast HTTP 500 from a dropped database connection must not pull the success latency down; a slow error is worse than a fast error, so track error latency too. |
| **Traffic** | Demand, in a system-specific high-level unit. HTTP: requests/s, optionally static vs dynamic. Audio: network I/O or concurrent sessions. KV store: transactions and retrievals/s. |
| **Errors** | Failed-request rate, **explicit** (HTTP 500s), **implicit** (HTTP 200 with the wrong content), or **by policy** (a one-second commitment makes a 1.2 s success an error). Load-balancer 5xx catch total failures; only end-to-end tests catch wrong content. |
| **Saturation** | How full the service is, on the *most constrained* resource. Many systems degrade before 100% utilization — a utilization *target* is essential. Latency, especially p99 over a short window (his example: one minute), is often a leading indicator. Saturation also includes prediction: “the database will fill its disk in 4 hours.” |

**RED — Tom Wilkie, Weaveworks, 2015** (GrafanaCon EU talk recap,
grafana.com, 2018-08-03; GrafanaCon EU 2018 slides). For every *service*,
monitor request **Rate** (requests/s), **Errors** (failing requests),
**Duration** (how long those requests take). Wilkie’s own framing: USE
applies to hardware; RED is the microservices-oriented counterpart;
consistency across services lets you put people on call for code they did
not write. RED is a proxy for user happiness and therefore for SLAs. He
treats the four golden signals as **RED + saturation**. Attribution trap:
Ewaschuk wrote the golden signals, not RED. Wilkie created RED at Weave
after a new hire asked for his monitoring philosophy.

**USE — Brendan Gregg.** First public checklists March 2012 (Linux
2012-03-07, Solaris 2012-03-01 on dtrace.org). Formal write-up: ACM Queue
vol. 10 no. 12, published 2012-12-10, doi:10.1145/2405116.2413037;
republished CACM 56(2), February 2013. One sentence: **for every resource,
check utilization, saturation, and errors.**

| Term | Gregg |
|---|---|
| **Resource** | Physical server functional components (CPUs, disks, busses, …) and software resources treated the same way (locks, thread pools, file-descriptor tables). |
| **Utilization** | Average time the resource was busy servicing work. For capacity resources (main memory) it is fraction of capacity used, not busy-time. Example: “one disk is running at 90% utilization.” |
| **Saturation** | Extra work the resource cannot service, often queued. Example: “the CPUs have an average run queue length of four.” Any non-zero saturation can be a problem. |
| **Errors** | Count of error events, including recovered ones (retried I/O, a failed device in a redundant pool). Non-zero and still-increasing counters while performance is poor are worth investigating. |

Interpretation rules from the same paper: ~100% utilization is usually a
bottleneck (confirm with saturation); any saturation can be a problem;
errors that are still climbing during a slowdown are a lead. USE is an
early-investigation *checklist*, not a complete methodology.

**Composition (tool-neutral).** RED (or golden-signal latency / traffic /
errors) answers “are users having a bad time?” USE answers “which resource
is the bottleneck?” Golden-signal **saturation** is the join: a
service-level fullness measure that USE would have found per resource.
Wilkie: RED is about how happy the users are; USE is about how happy the
machines are; they are complementary views of the same system. D3 places
RED on request-driven services and USE on hosts, runtimes, and pools. D2
places RED-shaped signals on user-visible navigations and USE-shaped
signals on device resources.

---

## 3. Mechanics

### 3.1 Catalog taxonomy (owned here)

These are the catalog definitions. D2 and D3 **must not** re-define
“metric.” D4 **must not** re-define “trace.”

**Metric.** A measurement of a service captured at runtime. An OpenTelemetry
**metric event** is the measurement plus the time it was captured plus
associated metadata (OTel concepts, fetched 2026-09-13). Metrics are
intended to provide *statistical information in aggregate*, not a request
lifecycle. Instrument kinds (OTel Metrics API): **Counter** (monotonic
up), **Asynchronous Counter**, **UpDownCounter**, **Asynchronous
UpDownCounter**, **Gauge** (current value; synchronous), **Asynchronous
Gauge**, **Histogram** (client-side aggregation of a distribution). The
OTLP data model ships **Sum**, **Gauge**, **Histogram**,
**ExponentialHistogram**, and **Summary** streams. The SRE Workbook: a
metric is a numerical measurement of attributes and events, typically
harvested as many data points at regular intervals; prefer monotonically
incrementing counters so the backend can compute windowed rates.

**Log.** A timestamped text record, structured (recommended) or
unstructured, with optional metadata (OTel Logs concepts). OTel: a **log
record** has named top-level fields — Timestamp, ObservedTimestamp,
TraceId, SpanId, TraceFlags, SeverityText, SeverityNumber, Body, Resource,
InstrumentationScope, Attributes, EventName — plus arbitrary resource and
attribute maps. **Events** are a specific type of log; not all logs are
events, but all events are logs. The Logs Bridge API is for logging-library
authors, not application code. Structured means a *stable schema*, not
merely valid JSON. The SRE Workbook: logs are an append-only record of
events; structured logs enable rich query; there is inherent delay between
event and visibility; logs are more accurate than metrics when reporting
is not time-sensitive, and are what you use to find a root cause a metric
cannot name.

**Trace.** The path of a request through an application. A **span** is a
unit of work: name, parent span ID (empty for the root), start and end
timestamps, span context (trace ID, span ID, trace flags, trace state),
attributes, events, links, status (`Unset` / `Error` / `Ok`). Span kinds:
`Client`, `Server`, `Internal`, `Producer`, `Consumer`. Context
propagation is what assembles spans from different processes into one
trace. OTel’s own teaching sentence: a span looks like a structured log
because it is one, with correlation, hierarchy, and causality baked in.
D4 owns sampling, W3C Trace Context on the wire, and correlation
operations.

**Profile.** A recording of resource usage at the code level (OTel Signals
concepts). The Profiles data format (spec, development) encodes aggregated
stack traces and metadata, based on Google **pprof**, so pprof maps
unambiguously in and, where the target format has equivalent capability,
back out. Unlike other signals, profiles share a top-level
`ProfilesDictionary` (strings, stacks, locations, mappings, functions,
attributes, links) because the payload is highly repetitive. Status as of
the spec status page fetched 2026-09-13: **Protocol: development**. OTLP
ships profiles at `/v1development/profiles`.

**Exemplar (verified, stable in the metrics data model).** A recorded
measurement that associates OpenTelemetry context with a metric event
inside an aggregated Metric. One use: link a Trace to a Metric. An
exemplar carries optional `trace_id` / `span_id`, `time_unix_nano`,
`value`, and `filtered_attributes`. For histograms the exemplar’s value
already participates in `bucket_counts`, `count`, and `sum`; for sums it
is already in the sum. Exemplars are sampled via `ExemplarFilter`
(`AlwaysOn` / `AlwaysOff` / `TraceBased`) and stored in an
`ExemplarReservoir`. They are **not** a sixth signal.

**Baggage (verified, API and SDK stable; Protocol N/A).** Contextual
key-value data that rides next to context and can be read downstream to
annotate traces, metrics, or logs. OTel status page, verbatim intent:
**“Baggage is not an observability tool”** — there is no OTLP or Collector
component for it. It is *not* automatically copied onto span/metric/log
attributes; a processor must promote it. W3C *Propagation format for
distributed context: Baggage* is a Candidate Recommendation Snapshot,
2024-05-30 (not a Recommendation as of this fetch). Security: automatic
instrumentation puts baggage in most outbound HTTP headers; there is no
integrity check on inbound keys; do not put credentials or unfiltered PII
in it.

**What a “signal” is, in OTel.** “System outputs that describe the
underlying activity of the operating system and applications.” Current
supported signals: traces, metrics, logs, baggage. Under development or
proposal: events (a log subtype), profiles. Each signal is built on
**context propagation**. Status (spec status page, 2026-09-13): Tracing
API/SDK/Protocol **stable**; Metrics API **stable**, SDK **mixed**,
Protocol **stable**; Logging Bridge API/SDK/Protocol **stable**; Baggage
API/SDK **stable**; Profiles Protocol **development**.

Sridharan’s complementary-costs argument (paraphrase): metrics are cheap to
alert on because an in-memory time-series query is cheap; logs keep the
long-tail context averages hide; traces reconstruct a request across
process boundaries. Majors’ counter (paraphrase): once each signal lives
in its own store you hop metrics → logs → traces matching timestamps
(“bunny products”); the missing property is *context preserved across
zoom*, not a fourth pillar. This note takes OTel’s word **signal** as
canon and treats “three pillars” as a historical / vendor phrase.

### 3.2 Cardinality

**Cardinality** of a metric is the number of unique attribute (label)
combinations. OTel Metrics concepts: the SDK keeps a separate aggregation
state per combination, so cost scales with distinct combinations, not with
request volume. High-cardinality attributes (user IDs, raw URL paths)
cause unbounded memory growth.

**Verified default.** Metrics SDK spec, Cardinality limits (Stable): if no
View and no MetricReader override is set, the default aggregation
cardinality limit **SHOULD be 2000**. Enforcement happens *after*
attribute filtering. Overflow measurements are **not dropped**: they fold
into one overflow point tagged `otel.metric.overflow=true`. Totals stay
correct; any query that groups or filters by an attribute undercounts,
because overflow *replaces the entire attribute combination*. Worked
failure from the concepts page: a counter labelled `{url.path, success}`
overflows; `{url.path=/checkout, success=false}` folds into
`{otel.metric.overflow=true}` and an error-rate alert on `success=false`
goes silent while the total still looks healthy. The limit does **not**
apply to Resource attributes (`service.name`, `service.instance.id`) or
instrumentation-scope attributes. Delta temporality resets state each
cycle (the limit bounds one cycle); cumulative temporality retains state
until process restart.

Majors (paraphrase, 2024-08-07): in metrics-backed products, cost tracks
cardinality; “custom metrics” is often a euphemism for unique series;
metrics discard context at write time and do not support high (or even
medium) cardinality. Wide structured events keep those dimensions and
answer unknown-unknowns; the trade-off is you cannot store every event
about every hop, so you sample (her “Live Your Best Life With Structured
Events”). Hidalgo, *Implementing Service Level Objectives* (O’Reilly 2020,
ISBN 9781492076813) and Mogul & Wilkes, “Nines Are Not Enough” (HotOS
2019) — already cited as [28] and [29] in
[nfr-references.md](../../../cases/data-intensive-design/nfr-references.md)
— are the D5-adjacent literature on why a percentile / nines number is
not a metric definition. Percentile *mechanics* (do not average
percentiles; histograms vs t-digest vs DDSketch) already live in
[performance.md](../../../cases/data-intensive-design/performance.md)
([31]–[36] of the same references file).

**Tool-neutral rule.** Put user ID, request ID, raw path, and build SHA on
logs and traces (or on exemplars), not on metric attributes. On metrics,
use *bounded* dimensions: method, *route template*, status class, service,
instance. OTel HTTP semconv 1.44.0 makes this concrete: `http.route` is
conditionally required and “MUST be low-cardinality” with static segments
kept and parameters templated (`/users/:userId`); `server.address` /
`server.port` were demoted to Opt-In specifically because they are
header-derived and high-cardinality.

### 3.3 Alerting policy foundations (D5 owns the SLO contract)

Ewaschuk’s paging philosophy, used as the D1 default:

- A page detects an otherwise undetected condition that is **urgent,
  actionable, and actively or imminently user-visible**. N+0 (no
  redundancy) and “nearly full” count as imminent.
- Every page is actionable and requires intelligence. A robotic response
  should not be a page — automate it.
- Pages are about a novel problem. If you can ignore an alert knowing it
  is benign, the rule is wrong.
- Symptom over cause for paging. “What’s broken” vs “why.” Causes belong
  on dashboards and in debug traces. One person’s symptom is the next
  layer’s cause (slow database reads).
- Black-box paging forces discipline: the problem is already happening and
  users see it. White-box is what catches imminent saturation and failures
  masked by retries.
- Email alerts are “alert spam” — rarely read. Prefer a dashboard of
  subcritical problems plus a log for historical correlation.
- Keep the paging path simple. Google reports limited success with complex
  dependency hierarchies and with “magic” systems that learn thresholds.

Workbook ch. 4: classify alerts so the response is proportional (ticket a
low error rate that lasts more than an hour; page a 100% error rate).
Suppress: one global-error-rate page instead of one page per node; suppress
a service’s error-rate page when a dependency already has a firing alert.
Workbook ch. 5 starting numbers — **owned in detail by D5**, recorded here
so D1 does not invent different ones — for a typical 30-day SLO: page at
**2% budget in 1 hour** (burn rate 14.4) and **5% in 6 hours** (burn rate
6); ticket at **10% in 3 days** (burn rate 1). Multiwindow, multi-burn-rate
is the workbook’s recommended end state. Low-traffic services break the
math (10 requests/hour, one failure = 10% hourly errors).

The existing stakeholder note already states the layer above this stack: a
**feedback loop** maps each signal to a trigger, owner, and action;
observability without that table is a dashboard that replaced the loop
([feedback-loop.md](../../../cases/claude-certification/stakeholder-engagement/feedback-loop.md),
[observability-replaced-loop.md](../../../cases/claude-certification/stakeholder-engagement/observability-replaced-loop.md)).

### 3.4 Monitoring as a dependency

The telemetry pipeline is a production dependency with its own saturation,
errors, and fail-open/fail-closed choice.

**Collector (verified defaults, exporterhelper README / `NewDefaultQueueConfig`,
fetched 2026-09-13; resiliency page).** `sending_queue.enabled` default
**true**; `queue_size` **1000** (unit = `sizer`, default **requests**, not
spans); `num_consumers` **10**; `block_on_overflow` **false** (reject when
full — data is dropped); `retry_on_failure.enabled` **true**;
`initial_interval` **5 s**; `max_interval` **30 s**; `max_elapsed_time`
**300 s**; `multiplier` **1.5**. In-memory queue: Collector crash loses
the buffer. `file_storage` WAL survives process death, not disk-full.
Kafka (or equivalent) between Agent and Gateway is the documented
highest-durability hop; it moves the failure to the queue cluster.

Documented loss modes (resiliency page): endpoint down longer than
`max_elapsed_time`; queue overflow; crash with no WAL; disk failure;
message-queue failure; misconfiguration; resilience explicitly disabled.
Internal telemetry (Collector docs): default Prometheus scrape of the
Collector itself at **127.0.0.1:8888**; watch
`otelcol_receiver_accepted_*` vs `otelcol_exporter_sent_*`,
`otelcol_receiver_refused_*`, `otelcol_exporter_send_failed_*`,
`otelcol_exporter_enqueue_failed_*`, `otelcol_exporter_queue_size` /
`_capacity`. Refused/failed counters do not by themselves prove loss
(retries exist); sustained refused *does* mean the client was told no.
`Dropping data because sending_queue is full` is the log line.

**Watchdog / dead man’s switch.** kube-prometheus `Watchdog` rule:
`expr: vector(1)` — an alert that is *always* firing, routed to an
*external* heartbeat (PagerDuty Dead Man’s Snitch is the runbook’s
example). Absence of the Watchdog is the only reliable signal that
Prometheus, Alertmanager, or the notification path has died. The watcher
must not share fate with the stack it watches.

**Self-observability of the SDK.** The OTel spec has a Self-Observability
section (listed on the 1.60.0 spec index). Treat SDK exporters the same
way as the Collector: bounded queues, visible drops, no silent
best-effort.

**Guardrail analogy (existing note, do not re-derive).** An
operator-built control that errors and still passes traffic is fail-open;
the default of surrounding code is almost always to keep requests flowing
([guardrails.md](../../../cases/claude-certification/responsible-ai/guardrails.md)).
A Collector that drops on overflow is fail-closed *for telemetry* and
fail-open *for the product* — the user request succeeds, the record of it
does not. Decide that explicitly.

---

## 4. Verified defaults / standards

Fetched 2026-09-13. Library versions are cited only where a numeric default
is taken from that artefact.

| Item | Value | Source |
|---|---|---|
| OpenTelemetry Specification | **1.60.0**, released 2026-08-07 | opentelemetry.io/docs/specs/otel/ ; GitHub release |
| OTLP | **1.11.0**. Stable for traces, metrics, logs. Development for profiles. Paths `/v1/traces`, `/v1/metrics`, `/v1/logs`, `/v1development/profiles` | opentelemetry.io/docs/specs/otlp/ |
| Semantic Conventions | **1.44.0** | opentelemetry.io/docs/specs/semconv/ |
| Metrics cardinality default | **2000** unique combinations per instrument per collection cycle; overflow → `otel.metric.overflow=true` | spec `metrics/sdk.md` Cardinality limits (Stable) |
| HTTP server duration metric | `http.server.request.duration`, Histogram, unit `s`, **Stable**. Required attrs: `http.request.method`, `url.scheme` | semconv HTTP metrics |
| HTTP duration buckets (advisory) | `[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10]` seconds | same; `ExplicitBucketBoundaries` |
| Prometheus `DefBuckets` | `[.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10]` seconds; `+Inf` implicit | prometheus/client_golang `histogram.go` (current master, same values as v1.6.0) |
| Prometheus `scrape_interval` | default **1m**; `scrape_timeout` default **10s** | prometheus.io configuration |
| Collector sending queue | 1000 requests, 10 consumers, non-blocking overflow (= drop) | exporterhelper `NewDefaultQueueConfig` |
| Collector retry | 5 s → 30 s cap, 1.5×, 300 s max elapsed | exporterhelper README |
| Collector self-metrics | Prometheus on `127.0.0.1:8888` | Collector internal-telemetry docs |
| W3C Baggage | CR Snapshot **2024-05-30**, not Recommendation | w3.org/TR/baggage/ |
| SRE book | First edition April 2016, O’Reilly, ISBN 9781491929117. Ch. 6 Ewaschuk / Beyer | oreilly.com / research.google |
| USE paper | ACM Queue 10(12), 2012-12-10, doi:10.1145/2405116.2413037 | dl.acm.org |
| RED | Wilkie, Weaveworks 2015; Grafana recap 2018-08-03 | grafana.com/blog/the-red-method-… |
| Workbook burn-rate starting points | page 2%/1 h @ 14.4× and 5%/6 h @ 6×; ticket 10%/3 d @ 1× | sre.google/workbook/alerting-on-slos (D5 detail) |

**Histogram vs mean (Ewaschuk, do not re-derive the percentile math).** Do
not design a new monitoring system around the mean of latency. His
teaching example: average 100 ms at 1,000 QPS can hide 1% of requests at
5 seconds; that 99th percentile of one backend becomes the *median* of a
frontend that fans out. Collect counts *bucketed by latency* with
approximately exponential boundaries (his worked set: 0–10 ms, 10–30,
30–100, 100–300, … — factors of roughly 3). [performance.md] already
separates response time, service time, queueing delay, and network
latency, and forbids averaging percentiles.

**Resolution (Ewaschuk).** CPU over a one-minute average hides spikes that
drive tail latency. For a 99.9% annual target (~9 hours downtime/year),
probing success more than once or twice a minute is probably unnecessary;
disk-full checks more than once every 1–2 minutes likewise. Per-second
CPU *can* be sampled internally and exported as a 5%-wide histogram every
minute.

**Instrumentation shape Wilkie actually wrote down** (GrafanaCon slides):
one `request_duration_seconds` histogram, labels `method`, `route`,
`status_code`, buckets = `prometheus.DefBuckets`. Queries: Rate =
`sum(rate(..._count[1m]))`; Errors =
`sum(rate(..._count{status_code!~"2.."}[1m]))`; Duration =
`histogram_quantile(0.99, sum(rate(..._bucket[1m])) by (le))`. Trade-off:
`status_code!~"2.."` counts every non-2xx as an error, which folds 4xx
(caller / validation) into the error rate — the same classification
problem CircuitBreaker.md already owns for trip criteria. Prefer status
*class* or an explicit error predicate; do not put the raw path in
`route`.

**Google staffing observation, not a default to copy:** an SRE team of
10–12 typically had one (sometimes two) people whose primary job was the
monitoring system; that number fell as infrastructure was centralized, but
every team still had a “monitoring person.” Staring at a screen to watch
for problems is explicitly rejected.

---

## 5. Failure modes and when-not-to-use

**Failure modes of the telemetry system itself**

1. **Cardinality overflow hides the page.** Totals stay correct;
   `success=false` (or any filtered label) undercounts. Symptom: error
   ratio on the dashboard falls while users scream. Detect
   `otel.metric.overflow=true` as its own alert.
2. **Raw URL / user ID on a metric.** Unbounded series, OOM in the SDK,
   Prometheus scrape failure, or a vendor bill that tracks “custom
   metrics.” Put those dimensions on logs/traces.
3. **Mean latency / unsplit success+error latency.** Fast 500s make the
   service look faster as it gets worse (Ewaschuk).
4. **Implicit and policy errors invisible to the load balancer.** HTTP 200
   + wrong body; SLO-late successes. Only synthetics / end-to-end tests
   catch them. A 5xx-only RED panel is a false green.
5. **Histogram interpolation around the SLO threshold.**
   `histogram_quantile` interpolates; if no bucket sits on the SLO
   threshold the estimate lies. Semconv and Prometheus both expect you to
   *choose* buckets; DefBuckets top out at 10 s — useless as-is for
   10-minute LLM calls ([poc-to-production.md](../../../cases/claude-certification/enterprise-integration-production/poc-to-production.md)
   already flags p95 vs median under load).
6. **Alert fatigue.** Bigtable SRE (Ewaschuk): SLO on synthetic-client
   *mean* performance, email as the SLO approached and pages when it
   broke, volume so high the team missed the user-visible failures. Remedy
   was temporarily relaxing the target (75th percentile), disabling email,
   and spending the quiet on the real fix — a short-term availability hit
   for a long-term one. Gmail: paging on every de-scheduled task when each
   task was a fraction of a percent of users; the durable fix was
   automating the rote poke, not living with the pages.
7. **Magic detectors and deep dependency trees.** Google: limited success;
   paging rules that catch real incidents must stay simple. Rarely
   exercised collection is a candidate for deletion.
8. **Pipeline drop = silent product success.** Default Collector queue
   drops at 1000 in-flight *requests* with `block_on_overflow=false`. The
   user request is fail-open; the record is fail-closed. No Watchdog →
   you will not be paged when Prometheus itself dies. Collector internal
   metrics scraped only on localhost never reach the same Prometheus that
   pages you — a circular-dependency footgun.
9. **Baggage leakage.** User IDs and origin IPs in headers to third-party
   APIs; untrusted inbound keys written into attributes.
10. **Three-pillar hop without correlation IDs.** A metric with no exemplar
    / trace_id, a log with no span_id, a trace with no matching logs.
    Sridharan and Majors disagree on storage; both require connective
    tissue. D4 owns how to stitch it.
11. **Sampling the tail away.** Structured-event stores require sampling
    (Majors). Head-based sampling biases against the rare failure you
    needed. D4 owns the sampler; D1 only records that a 100% metrics
    series plus a 1% trace sample is a *deliberate* fidelity split.
12. **Observability that replaced the feedback loop.** Signals without
    trigger / owner / action. Already documented; do not rebuild it here.
13. **Monitoring the wrong layer of an LLM call.** POC-to-production:
    retries sit next to the API call, breakers at the service boundary,
    fallbacks in orchestration; p95 under concurrency is not demo median;
    token distributions are skewed. Guardrails that fail open look
    healthy. None of that changes the signal definitions.

**When-not-to-use (the frameworks, not “don’t monitor”)**

- **USE alone on a request-driven service.** Utilization of a pod is not
  user happiness; Wilkie’s reason for inventing RED. Saturation of memory
  and “what is a memory error on Linux?” are the examples he calls
  awkward.
- **RED alone on a resource.** Rate/Errors/Duration of a disk are the
  wrong questions; use USE.
- **RED `status_code!~"2.."` as the error definition.** Counts 401/404/422
  as service failures. Classify first (CircuitBreaker.md already has the
  table).
- **Four golden signals on a batch / queue worker without translation.**
  Traffic becomes messages/s or lag; latency becomes age-of-oldest;
  saturation is consumer-lag or disk. The *names* still work; the units
  change. D3 must pick units, not redefine the signals.
- **Paging on every cause.** You will page on every crashed replica behind
  a healthy load balancer.
- **Requiring all OTel signals before the first dashboard.** Each signal
  is independently usable (OTel; Majors quotes Austin Parker on this).
  Start with RED histograms + USE on the bottleneck resource + a Watchdog.
- **High-cardinality metrics as a substitute for traces.** That is how
  you buy a metrics outage.
- **Treating the Collector health endpoint as sufficient.** Legacy
  `check_collector_pipeline` is documented as not working as expected
  (healthcheck / healthcheckv2 READMEs). Use accepted-vs-sent, queue
  utilisation, and an external Watchdog.

---

## 6. Cross-links

**Siblings.** D2 applies this taxonomy to RUM / vitals / crash reporting.
D3 places golden signals, RED, and USE on servers and writes the
dashboards and scrape topology. D4 owns trace propagation, sampling, and
correlation — it consumes §3.1’s trace/span/baggage definitions. D5 owns
SLI/SLO/error-budget math and the workbook burn-rate tables; it consumes
§3.3. C1 ([CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md)
Observability section) places state / trip rate / MTTR / not-permitted /
downstream error and slow-call rates on a breaker; those are metrics as
defined here.

**Existing notes (main-repo `cases/`, do not rewrite).**

- [nfr-references.md](../../../cases/data-intensive-design/nfr-references.md)
  — Hidalgo SLO book [28], Mogul & Wilkes [29], Hauer *Meaningful
  Availability* [30], percentile sketches [31]–[36], Brooker / Nygard /
  metastable [7]–[15]. Dump ends at [41]; [42]–[100] are pointers, not
  invented here.
- [performance.md](../../../cases/data-intensive-design/performance.md) —
  response time vs service time vs queueing; do not average percentiles;
  retry storms and metastable failure.
- [nfr-overview.md](../../../cases/data-intensive-design/nfr-overview.md) —
  reliability = meeting the SLO when parts fail; fault vs failure.
- [distributed-vs-single-node.md](../../../cases/data-intensive-design/distributed-vs-single-node.md)
  — observability as querying high-level metrics *and* individual events;
  OTel / Zipkin / Jaeger as tracing examples.
- [poc-to-production.md](../../../cases/claude-certification/enterprise-integration-production/poc-to-production.md)
  — p95 ≠ demo median; retries / fallbacks / breakers by layer; RAG
  retrieval precision/recall as *system* metrics; shared trace ID across
  orchestrator-workers.
- [guardrails.md](../../../cases/claude-certification/responsible-ai/guardrails.md)
  — fail-open vs fail-closed when a control errors; log every blocked or
  failed gate.
- [feedback-loop.md](../../../cases/claude-certification/stakeholder-engagement/feedback-loop.md)
  / [observability-replaced-loop.md](../../../cases/claude-certification/stakeholder-engagement/observability-replaced-loop.md)
  — governance table above the stack.
- [monitoring-observability.md](../../../cases/fincancial-data-architecture/monitoring-observability.md)
  — metrics / events / logs / traces as a data-management problem; budget
  the store like a market-data store.

---

## 7. Sources

Retrieved 2026-09-13.

**Golden-metric frameworks.** sre.google/sre-book/monitoring-distributed-systems (Ewaschuk / Beyer, SRE book ch. 6) · sre.google/workbook/monitoring · sre.google/workbook/alerting-on-slos · sre.google/workbook/on-call · oreilly.com/library/view/site-reliability-engineering/9781491929117 (April 2016) · research.google/pubs/monitoring-distributed-systems · brendangregg.com/usemethod.html · brendangregg.com/USEmethod/use-linux.html · dl.acm.org/doi/10.1145/2405116.2413037 (Queue 2012-12-10) · cacm.acm.org/practice/thinking-methodically-about-performance (CACM 2013-02) · grafana.com/blog/the-red-method-how-to-instrument-your-services (2018-08-03) · grafana.com/files/grafanacon_eu_2018/Tom_Wilkie_GrafanaCon_EU_2018.pdf · suse.com/c/rancher_blog/red-method-for-prometheus-3-key-metrics-for-monitoring (Weave/Rancher webinar write-up).

**Signals, pillars, cardinality.** opentelemetry.io/docs/concepts/signals · /metrics · /traces · /logs · /baggage · opentelemetry.io/docs/specs/otel (Specification 1.60.0) · opentelemetry.io/docs/specs/status · opentelemetry.io/docs/specs/otlp (OTLP 1.11.0) · opentelemetry.io/docs/specs/semconv (1.44.0) · opentelemetry.io/docs/specs/semconv/http/http-metrics · opentelemetry.io/docs/specs/otel/metrics/data-model (Exemplars, Stable) · opentelemetry.io/docs/specs/otel/metrics/sdk (cardinality 2000; ExemplarFilter) · opentelemetry.io/docs/specs/otel/profiles/data-format · github.com/open-telemetry/opentelemetry-specification/releases (v1.60.0, 2026-08-07) · copyconstruct.medium.com/logs-and-metrics-6d34d3026e38 · copyconstruct.medium.com/monitoring-in-the-time-of-cloud-native-c87c7a5bfa3e · oreilly.com/library/view/distributed-systems-observability/9781492033431 (Sridharan, May 2018) · charity.wtf/p/the-pillar-is-a-lie (2025-10-30) · charity.wtf/p/is-it-time-to-version-observability-signs-point-to-yes (2024-08-07) · charity.wtf/p/live-your-best-life-with-structured-events · charity.wtf/p/observability-is-a-many-splendored-thing · w3.org/TR/baggage (CR 2024-05-30) · w3.org/standards/history/baggage.

**Pipeline as a dependency.** opentelemetry.io/docs/collector/internal-telemetry · opentelemetry.io/docs/collector/resiliency · github.com/open-telemetry/opentelemetry-collector/blob/main/exporter/exporterhelper/README.md · exporterhelper/internal/queue_sender.go (`NewDefaultQueueConfig`) · github.com/open-telemetry/opentelemetry-collector-contrib healthcheck / healthcheckv2 READMEs · runbooks.prometheus-operator.dev/runbooks/general/watchdog · prometheus.io/docs/prometheus/latest/configuration/configuration (scrape_interval 1m) · github.com/prometheus/client_golang/blob/master/prometheus/histogram.go (`DefBuckets`).

**In-tree.** cases/data-intensive-design/{nfr-references,nfr-overview,performance,distributed-vs-single-node}.md · cases/claude-certification/enterprise-integration-production/poc-to-production.md · cases/claude-certification/responsible-ai/guardrails.md · cases/claude-certification/stakeholder-engagement/{feedback-loop,observability-replaced-loop}.md · cases/fincancial-data-architecture/monitoring-observability.md · cases/SystemDesignPatterns/CircuitBreaker.md (C1 placement).

---

## 8. Uncertain / left out

- Original Weaveworks HTML post *“The RED Method: key metrics for
  microservices architecture”* and the 2015 London Prometheus-meetup
  slides were not fetchable as live pages. 2015 authorship is taken from
  Wilkie’s 2018 Grafana recap (first-party) and the GrafanaCon PDF. Do
  not cite a dead weave.works URL as verified.
- Exact calendar day of the SRE book’s print run beyond “April 2016” /
  O’Reilly first edition was not independently re-verified against a
  colophon scan.
- Metrics SDK status page still says SDK “mixed” and “Metrics is currently
  under active development” while also marking the API and protocol
  stable — wording looks stale relative to language-table “Stable” rows
  on the concepts page. Treat API + protocol + data model as stable;
  per-language SDK status as the language table.
- OTLP *proto* GitHub latest *release tag* observed as v1.10.0
  (2026-03-09) while the spec site titles “OTLP Specification 1.11.0”.
  The site title is what this note uses; the tag skew is unverified.
- Collector `NewDefaultQueueConfig` on `main` also defaulted a nested
  batch (`FlushTimeout` 200 ms, `MinSize` 8192 items). Whether every
  released exporter helper version ships that nested default was not
  cross-checked against a release tarball; queue_size 1000 / 10
  consumers / retry 5–30–300 are in the released README (v0.148.0).
- Healthcheck v2 `/status?pipeline=` behaviour was read from the README,
  not exercised.
- Peter Bourgon 2018 “three pillars” post and Ben Sigelman “just
  telemetry” talk were cited by Majors; the originals were not re-fetched
  here.
- No controlled measurement of “how often overflow silently kills an
  error-rate alert in production” was found. The OTel worked example is
  a specification illustration, not an incident report.
- PromQL Watchdog `vector(1)` and the kube-prometheus runbook are
  ecosystem conventions, not a Prometheus project RFC.
- LLM-specific token/span semantic conventions have moved to a separate
  GenAI semconv repository (semconv 1.44.0 index). Not expanded here.
- Skill-frontmatter budgets, vendor SLAs, and per-vendor “custom metric”
  prices — out of scope; no prices asserted.
