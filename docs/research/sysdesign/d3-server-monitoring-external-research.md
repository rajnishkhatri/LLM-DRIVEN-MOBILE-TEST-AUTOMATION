---
type: research
title: 'Server-side monitoring (golden signals, alerting) — external research (2026-09-13)'
description: >-
  Source-verified research for catalog id D3: host/process/runtime golden
  signals in production, scrape vs push, RED on servers, saturation, alerting
  implementation (not SLO policy), OpenTelemetry and Prometheus defaults, and
  failure modes of monitoring itself.
tags: [research, system-design-patterns, D3, server, monitoring]
---

# Server-side monitoring (golden signals, alerting) — external research (2026-09-13)

> **What this is.** Evidence pass for catalog id **D3**. D1 owns the signal
> taxonomy (what a metric / log / trace *is*, and the RED/USE *frameworks* as
> vocabulary). This note applies those frameworks to **servers in production**:
> host, process, and runtime golden signals; scrape vs push; RED on inbound
> request paths; saturation; and how alerts are *implemented*. D5 owns SLO /
> error-budget *policy*. Primary pages fetched 2026-09-13. Paraphrase; numbers
> and identifiers reproduced exactly. Items that could not be verified are in
> §8 and are **not** asserted as fact.
>
> **Existing citations in this tree** (do not duplicate): Hidalgo SLOs [28],
> Mogul & Wilkes “Nines Are Not Enough” [29], Hauer et al. *Meaningful
> Availability* [30], HdrHistogram [31], t-digest [32], Brooker on the mean
> [19], Schwartz on percentiles [36], Dean & Barroso *The Tail at Scale* [27]
> in [nfr-references.md](../../../cases/data-intensive-design/nfr-references.md).
> Circuit-breaker metric *names* were first verified in
> [circuit-breaker-external-research.md](circuit-breaker-external-research.md);
> this note treats that observability section as a **consumer** of server
> metrics, not a second home. Health-check defaults live in
> [failover-degradation-external-research.md](failover-degradation-external-research.md)
> (C3).

---

## 1. Scope and non-goals

**This note owns.** Host / process / runtime golden signals as they appear on
a production server (or replica, container, JVM/Go runtime). How those signals
are *collected* (Prometheus-style scrape vs OTLP/SDK push). RED applied to
*inbound* server request paths. Saturation as the fourth golden signal and as
USE-method resource queues. Alerting *implementation*: scrape-health (`up`),
pending/`for`, grouping, inhibition, and the mechanical shape of burn-rate
rules. Failure modes of the monitoring path itself: missing scrapes, stale
series, cardinality bombs, alert storms.

**Non-goals (sibling owners).**

| Id | Stays there |
|---|---|
| **D1** | Signal taxonomy. Do not re-define “metric”. RED/USE as *framework names* are D1’s; D3 applies them to servers. |
| **D2** | Client-side RUM, web vitals, crash / error reporting, mobile. A browser p75 is not a server p99. |
| **D4** | Distributed traces and correlation IDs. Server histograms may carry exemplars; the trace graph is D4. |
| **D5** | SLO / SLI / error-budget *policy*: which ratio is the SLI, what the objective is, how much budget a page is allowed to spend. D3 may cite workbook *mechanics* so an implementer can wire rules; the policy decision is D5. |
| **C1** | Circuit-breaker state machine. The breaker *emits* server-side series (see §6); it does not define golden signals. |
| **C3** | Health checks, probes, LB fail-open, failover. **Health ≠ monitoring.** A probe is a binary routing / restart decision; a golden-signal pipeline is continuous quantitative telemetry plus paging. Deep dependency checks belong in *external monitoring*, not in the LB health path (Yanacek, cited in C3 research). |

**Tool-neutrality.** Names below are from Prometheus, OpenTelemetry, and the
SRE books because those are the documents that publish numeric defaults. The
mechanics (pull vs push, histograms vs means, page-on-symptoms) do not require
those vendors.

---

## 2. Lineage / vocabulary

**SRE book ch. 6 *Monitoring Distributed Systems*** (Ewaschuk, 2016)
https://sre.google/sre-book/monitoring-distributed-systems/ — fetched
2026-09-13. White-box = internals (`/metrics`, JVM, logs). Black-box =
externally visible behaviour. An **alert** is a human-directed notification
(ticket / email / page). Page only when the event is urgent, actionable,
requires intelligence, and is novel. First cut: symptom (“what’s broken”)
vs cause (“why”).

**Four golden signals** (same chapter): latency, traffic, errors,
saturation — “If you can only measure four metrics of your user-facing
system, focus on these four.” Split success vs failure latency (a fast
HTTP 500 pulls the mean down). Traffic is demand in a system-specific unit
(HTTP RPS; concurrent sessions; KV transactions/s). Errors are explicit
(HTTP 500), implicit (HTTP 200, wrong content), or by policy (1.2 s against
a 1 s commitment). Saturation = how full the *most constrained* resource
is, plus prediction (“disk full in 4 hours”). p99 over a one-minute window
is the chapter’s leading-indicator example.

**SRE Workbook ch. 4 *Monitoring*** (Frame et al.)
https://sre.google/workbook/monitoring/ — fetched 2026-09-13. Metrics for
pages/dashboards (near-real-time); logs for root cause and more accurate
offline reports. Data more than **four to five minutes** stale “might
significantly impact” incident response. Prefer monotonic counters.
Monitoring config as code. 2018 open standards named: statsd and
Prometheus (then becoming OpenMetrics). Saturation includes hard limits
(RAM, disk, CPU quota) *and* soft ones (fds, thread-pool occupancy, queue
wait, log volume); Java heap/metaspace/GC; Go goroutine count. Instrument
the RPC client library once so new dependencies are free.

**Workbook ch. 5 *Alerting on SLOs***
https://sre.google/workbook/alerting-on-slos/ — fetched 2026-09-13. **D5
owns policy.** Cited here only for implementation shape: Table 5-8,
multi-window `AND`, short window ≈ 1/12 of long. They do **not** recommend
Prometheus `for:` as a substitute for a long SLO window (a 100% outage then
waits as long as a 0.2% drip; a flicker resets the timer).

**Gregg, USE Method** — https://www.brendangregg.com/usemethod.html —
fetched 2026-09-13. “For every resource, check utilization, saturation, and
errors.” Utilization = busy-time average; saturation = extra work that
cannot be serviced (queue length / queued time); errors = event counts.
Any non-zero saturation can add latency. Five-minute CPU averages ≤ 80%
can hide 100% bursts that already saturate the run-queue. Software
resources and resource controls are in scope.

**Wilkie, RED Method** (2015; Grafana write-up 2018-08-03)
https://grafana.com/blog/the-red-method-how-to-instrument-your-services/ —
fetched 2026-09-13. For every *service*: Rate, Errors, Duration. Wilkie:
USE is machines, RED is users; complementary. Golden signals = “RED +
saturation.”

**Prometheus pull / Pushgateway**
https://prometheus.io/docs/practices/pushing/ ·
https://prometheus.io/docs/introduction/faq/ — fetched 2026-09-13. Default
collection is scrape-over-HTTP. Pushgateway only for **service-level batch
jobs** that cannot be scraped (no machine/`instance` label). Blind use as
a push bus: SPOF / bottleneck; no `up`; **never forgets** series unless
deleted via its API. FAQ: pull is “slightly better,” not a deciding
feature.

---

## 3. Mechanics (group D depth bar)

### 3.1 Three stacked views of one server

Treat a production instance as three layers that each get a golden-signal
set. Mixing the layers on one chart is how teams page on CPU while users
are fine, or the reverse.

| Layer | Framework | What “traffic / rate” is | What “saturation” is | Typical exporters |
|---|---|---|---|---|
| **Host** | USE | interrupt / packet / I/O rate | run-queue, paging, disk wait, NIC drops | node_exporter; OTel `hostmetrics` (`system.*`) |
| **Process** | USE | CPU-seconds, context switches, I/O | thread / fd / handle exhaustion; RSS vs limit | Prometheus `process_*`; OTel `process.*` |
| **Runtime** | USE + workbook “purposeful metrics” | allocations, GC work, goroutine create | heap / metaspace, GC pause, goroutine count | Micrometer / OTel `jvm.*` (renamed from `process.runtime.jvm.*` in semconv 1.22) |
| **Inbound RPC / HTTP** | RED = golden latency/traffic/errors | requests/s by method × route-template × status | in-flight / queue / pool occupancy; p99 as leading indicator | OTel `http.server.request.duration`; Prometheus `http_request_duration_seconds` |

**RED on servers** is the inbound histogram (or counter + histogram pair),
not the host CPU. Wilkie’s GrafanaCon queries (slides, 2018; same shape in
the 2018-08-03 post’s Prometheus example) all read one histogram family:

```
sum(rate(request_duration_seconds_count{job="…"}[1m]))
sum(rate(request_duration_seconds_count{job="…",status_code!~"2.."}[1m]))
histogram_quantile(0.99, sum(rate(request_duration_seconds_bucket{job="…"}[1m])) by (le))
```

Trade-off: a single histogram gives Rate, Errors, and Duration with one
instrument, but **status as a label on the duration histogram** multiplies
buckets × codes × routes. Prefer a low-cardinality route *template*
(`/users/:id`, never the raw path) — OTel marks `http.route` conditionally
required “if and only if it’s available” and warns it MUST be
low-cardinality.

**Saturation is not utilization.** SRE: systems degrade before 100%
utilization, so a *target* below the hard limit is required. Gregg: any
queued extra work is already a problem; utilization averaged over minutes
can look healthy while the run-queue is not. Workbook: watch the resource
that will actually cap the service (thread pool, fds, queue wait), not
only the metric that is easy. Prediction (“disk full in 4 hours”) is part
of the golden-signal definition, not a bonus dashboard.

**Latency instrumentation.** SRE ch. 6: do not alert or capacity-plan on
the mean of latency; collect counts in exponentially spaced buckets
(their example spacing is factors of ~3). A 100 ms mean at 1 000 RPS can
hide 1% of requests at 5 s, and that p99 becomes the *median* of a
fan-in frontend. Percentile sketch literature and why averages mislead
are already in [nfr-references.md](../../../cases/data-intensive-design/nfr-references.md)
([19], [27], [31]–[36]); do not re-derive them here. Split success and
error latency or a flood of instant 500s makes the service look faster
while it is down.

### 3.2 Scrape vs push

Two control loops, not two religions.

**Pull / scrape.** The collector (Prometheus server, OTel Collector
`prometheusreceiver`, Grafana Alloy `prometheus.scrape`) schedules HTTP
GETs against `/metrics`. The scheduler owns the interval; a failed GET
is itself a time series (`up=0`). When a target disappears, its series
are marked stale (Prometheus inserts a stale NaN; lookback then drops
them). You can hit the same endpoint in a browser. Extra scrapers
(laptop, second HA Prometheus) do not require the app to know about
them.

**Push.** The process *exports* on a timer (OTel
`PeriodicMetricReader` → OTLP) or writes to an intermediary
(Pushgateway, statsd). The app owns the interval. There is no automatic
`up`. If the exporter dies, the last samples persist until lookback /
cache expiry — or, on Pushgateway, **forever**.

**When push is the right default.** Short-lived batch / cron that exits
before the next scrape (Prometheus: Pushgateway, and only as a
*service-level* job without an `instance` label). Processes behind NAT
that cannot be scraped. Sidecar / Collector topologies where many
processes OTLP-push to one Collector, and the Collector is what Prometheus
scrapes (push at the edge, pull at the store — the common OTel shape).

**When scrape is the right default.** Long-running servers. Anything you
need an `up` signal for. Anything whose lifecycle should match series
lifecycle (scale-in should make series disappear).

Trade-off: scrape couples discovery to the collector (you must find
targets); push couples availability to the app’s exporter and to the
receiver’s backlog. Neither removes the need to monitor the monitor
(§5).

### 3.3 Alerting *implementation* (policy stays in D5)

A production alerting path has four mechanical stages. D5 decides *what
ratio* is the SLI; this section is how the path behaves once that ratio
exists.

1. **Scrape / export health.** Prometheus writes, on every scrape:
   `up{job,instance}` (1 reachable, 0 failed),
   `scrape_duration_seconds`,
   `scrape_samples_scraped`,
   `scrape_samples_post_metric_relabeling`,
   `scrape_series_added` (since v2.10).
   A missing golden-signal graph is often `up=0` or a cardinality drop,
   not an application regression. The docs’ own example rule pages
   `up == 0` with `for: 5m`.
2. **Rule evaluation.** `evaluation_interval` default **1m**. Alert
   `for:` default **0s** (fires on first true evaluation).
   `keep_firing_for` default **0s**. A zero `for` on a noisy gauge is how
   alert storms start.
3. **Notification grouping.** Alertmanager route defaults (fetched
   2026-09-13 from https://prometheus.io/docs/alerting/latest/configuration/):
   `group_wait` **30s**, `group_interval` **5m**, `repeat_interval` **4h**.
   `repeat_interval` is rounded up to a multiple of `group_interval`.
   Group-by and inhibit so one saturated dependency is one page, not N.
4. **Burn-rate *shape*** (workbook Table 5-8, 99.9% / 30-day example —
   **thresholds are D5’s to accept or reject**): page at 14.4× over
   **1 h AND 5 m** (2% budget) or 6× over **6 h AND 30 m** (5%); ticket
   at 1× over **3 d AND 6 h** (10%). Short window ≈ 1/12 of long, so the
   alert resets when burn *stops*, not when the long window drains.
   The same chapter’s example `expr` also shows a 3× / 24 h / 2 h ticket
   pair that Table 5-8 omits (§8).

SRE ch. 6 paging questions that belong on the *implementation* side
(independent of which SLO D5 picked): does this detect something
urgent, actionable, and user-visible (or imminently so, including N+0
and “nearly full”)? Will I learn to ignore it? Are users actually
affected (filter drained / test traffic)? Can the action be automated?
Is someone else already paged for the same incident?

Cause-oriented pages (CPU high, disk full) are debugging aids;
symptom-oriented pages (error ratio, latency, `up`) are what should
wake a human. Saturation is the exception SRE carves out: page when a
signal is *nearly* problematic, because black-box users have not
broken yet.

### 3.4 Health checks are not this pipeline

C3’s probe (kube `periodSeconds` 10 s, ALB 30 s, Route 53 30 s) answers
“should this instance receive traffic / be restarted?” Monitoring
answers “what is the distribution of user-visible work, and is a human
needed?” Crossing them produces the two classic failures already
documented in C3: (a) a shallow TCP check that black-holes traffic onto
a process serving empty 200s; (b) a deep dependency check in the LB
path that takes the whole fleet out when one shared backend blinks.
Yanacek’s rule, already in the C3 note: deep checks belong in
*external monitoring*. `up` is scrape reachability, not application
correctness; a process can export `up=1` while every request is 500.

---

## 4. Verified defaults / standards (fetched 2026-09-13)

**The 15 s question.** Prometheus’s *software* default is **not** 15 s.
https://prometheus.io/docs/prometheus/latest/configuration/configuration/
documents:

| Knob | Default |
|---|---|
| `global.scrape_interval` | **1m** |
| `global.scrape_timeout` | **10s** (must be ≤ interval) |
| `global.evaluation_interval` | **1m** |
| `global.rule_query_offset` | **0s** |
| `scrape_configs[].metrics_path` | `/metrics` |
| `sample_limit` / `body_size_limit` / `target_limit` | **0** = unlimited |

The getting-started tutorial *sets* `scrape_interval: 15s` and comments
“By default, scrape targets every 15 seconds.” That comment describes
the *tutorial file*, not the binary default. Treat 15 s as a common
*chosen* resolution, not a vendor default.

**OTel Collector `prometheusreceiver`.** Contrib README (fetched
2026-09-13): embedded Prometheus scrape YAML; “any field you omit picks
up the default documented there” → **1m / 10s** unless the job
overrides. README examples use `scrape_interval: 5s` for the
Collector’s *own* `:8888` telemetry — an example, not the receiver
default. `scrape_on_shutdown` default **false**.

**OTel Collector `hostmetricsreceiver`.**
`collection_interval` default **1m**; `initial_delay` default **1s**.
Run two receiver instances if CPU should be sampled faster than disk.

**OTel SDK PeriodicMetricReader**
(https://opentelemetry.io/docs/specs/otel/metrics/sdk and
https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/
): `exportIntervalMillis` **60000**; `exportTimeoutMillis` **30000**.
Env: `OTEL_METRIC_EXPORT_INTERVAL=60000`,
`OTEL_METRIC_EXPORT_TIMEOUT=30000`. This is the **push** cadence from
the process to a Collector / backend.

**OTel HTTP server semantic conventions**
(https://opentelemetry.io/docs/specs/semconv/http/http-metrics/):
`http.server.request.duration` — Histogram, unit `s`, **stable**,
recommended. Advisory buckets
`[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10]`.
Required attrs: `http.request.method`, `url.scheme`. Conditionally
required: `http.response.status_code`, `http.route` (template only),
`error.type`. `server.address` / `server.port` are **Opt-In** because
they are high-cardinality if taken from request headers (migration
note, v1.23). Companion: `http.server.active_requests` (in-flight —
a saturation gauge). Renames: `http.server.duration` (ms) →
`http.server.request.duration` (s) at v1.23.1.

**Prometheus classic histogram `DefBuckets`** (`client_golang`
`histogram.go`):
`[]float64{.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10}` plus
implicit `+Inf`. Tailored to “response time (in seconds) of a network
service”; the comment says you will most likely need custom buckets.
**OTel HTTP adds 0.075, 0.75, 7.5** that Prometheus DefBuckets omit —
do not assume they match. Native histograms are preferred in current
Prometheus histogram docs; `scrape_native_histograms` default in the
config schema fetched today is **false**.

**Alertmanager** (https://prometheus.io/docs/alerting/latest/configuration/):
`group_wait` 30s, `group_interval` 5m, `repeat_interval` 4h.

**Prometheus alerting rules**
(https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/
and recording-rules syntax): `for` **0s**, `keep_firing_for` **0s**,
group `limit` **0** (no cap on series/alerts produced). Docs example:
`up == 0` for 5m; latency example `for: 10m`.

**Staleness / lookback.**
https://prometheus.io/docs/prometheus/latest/querying/basics/ — lookback
period **5 minutes** default (`--query.lookback-delta`). Failed scrape
marks previously exposed series stale; subsequent failed scrapes ingest
only `up` and friends. Instant selectors honor stale markers immediately;
series with *explicit* timestamps without `track_timestamps_staleness`
linger for the lookback. A secondary blog claims Prometheus 3 changed
the default lookback to the scrape interval; the docs page fetched
today still says 5m (§8).

**Cardinality guidance (Prometheus, not a hard server limit).**
Naming: https://prometheus.io/docs/practices/naming/ — never put user
IDs, emails, or other unbounded sets on labels; every label-set is a
series. Instrumentation: https://prometheus.io/docs/practices/instrumentation/
— “try to keep the cardinality of your metrics below 10”; for those
that exceed it, “a handful across your whole system”; “vast majority
… should have no labels”; cardinality **over 100** (or the potential
to grow there) → reduce dimensions or move the analysis off the
metrics TSDB. Their worked example: `node_filesystem_avail` in the
tens of series/node × 10 000 nodes ≈ 100 000 series is “fine”;
per-user quota on that metric is not.

**Naming vs OTel.** Prometheus SHOULD suffix units (`_seconds`,
`_bytes`, `_total`). OTel puts the unit in metadata and uses
`http.server.request.duration` without a suffix. Prometheus’s own
naming page now explains why it disagrees (YAML-in-incident UX;
`process_cpu` seconds vs milliseconds collisions). A Collector
translation step is required if both names must coexist; do not
assume they are the same series.

---

## 5. Failure modes and when-not-to-use

**Missing scrapes / silent dashboards.** `up=0` is the first alert, not
a footnote. A scrape timeout (default 10 s) on a huge `/metrics` looks
like an application outage. `sample_limit` / `body_size_limit` default
off: a cardinality bomb is ingested until the TSDB OOMs, then
*everything* pages. After a failed scrape Prometheus marks the *previous*
application series stale — graphs go blank, not flat, which is easy to
misread as “load disappeared.” Pushgateway and un-timestamped push
caches do the opposite: they lie that the job is still healthy.

**Cardinality bombs.** Unbounded labels (user id, request id, raw URL,
email, build SHA, exception message) multiply: buckets × status ×
route × instance. Classic histograms make this worse (`le` is already
a dimension). The failure mode of monitoring itself is that the
collector falls over *during* the incident the metrics were meant to
explain. Mitigations with sources: drop at scrape
(`metric_relabel_configs`); `sample_limit` as a scrape circuit-breaker
(config exists; default 0 = off); keep identifiers on logs/traces
(D4), not series; OTel’s demotion of `server.address` to Opt-In is
exactly this class of bug.

**Alert storms.** `for: 0s` + 1 m evaluation + one rule per instance ×
endpoint turns one saturated database into thousands of pages. SRE ch. 6:
too-frequent pages are skimmed, including the real one. Workbook:
severity classes; inhibit children when the dependency is already
firing; one global error-rate page, not one per node. Alertmanager
30 s / 5 m / 4 h is useless if `group_by` is the full label set.
Bigtable SRE (ch. 6): mean SLO + email-and-page volume; they loosened
to p75, disabled email, fixed the tail. Gmail: paging per de-scheduled
task (thousands of tasks, each a fraction of a percent of users) was
unmaintainable — rote pages should have been automated.

**Too-clever monitors.** SRE ch. 6: limited success with deep
dependency hierarchies and “magic” anomaly detectors; paging rules
must be readable by the whole team. Unused series (no dashboard, no
alert) are removal candidates. Combining monitoring with profiling /
crash-dump / traffic inspection in one binary is called out as
fragile.

**Wrong layer / health-check substitution.** CPU pages without RED:
users may be fine or already down. RED-only: you miss “disk full in 4
hours.” Wilkie: run both. Using the LB probe as the only server monitor
(or 5xx rate as the only readiness signal) collapses C3 and D3 — §3.4.

**When not to use this style.** Single-process tool, one operator, no
paging rotation (SRE: do not create a “stare at a screen” job).
Low-traffic: workbook ch. 5, one failure in 10 req/h = 10% hourly =
1 000× burn on a 99.9% SLO — do not page that blindly (synthetic
traffic / combine services / change the product are D5-adjacent).
Batch/cron: scrape a long job *and* push a completion gauge; HTTP RED
does not apply. Narrow security audits — ch. 6 sets those outside
“something seems a bit weird” paging.

Trade-off: symptom pages hide causes, so you still need USE series and
(D4) traces *after* the page. Collecting both at 15 s / high
cardinality is how the monitor becomes the outage.

---

## 6. Cross-links

| Target | Why |
|---|---|
| **D1** | Taxonomy owner. RED/USE *as frameworks* live there; this note only applies them to servers. |
| **D2** | Client-perceived latency / crash reporting. Do not substitute server p99 for RUM. |
| **D4** | Traces, correlation, exemplars hanging off `http.server.request.duration`. |
| **D5** | SLO, error budget, and *which* burn-rate table to adopt. Table 5-8 is quoted as implementation shape only. |
| **C1** [CircuitBreaker.md § Observability](../../../cases/SystemDesignPatterns/CircuitBreaker.md) | Example *consumer* of server metrics: breaker state, trip rate, MTTR-open, not-permitted / fallback rate, downstream error and slow-call rates (Resilience4j / Polly / Envoy names). Link; do not copy. Research home: [circuit-breaker-external-research.md](circuit-breaker-external-research.md). |
| **C3** [failover-degradation-external-research.md](failover-degradation-external-research.md) | Health checks, probes, fail-open. Health ≠ monitoring. Yanacek: deep checks → external monitoring. |
| [nfr-references.md](../../../cases/data-intensive-design/nfr-references.md) | SLOs [28], nines [29], meaningful availability [30], histograms / sketches [31]–[35], percentile pitfalls [19][36], tail [27]. |
| [nfr-overview.md](../../../cases/data-intensive-design/nfr-overview.md) / [performance.md](../../../cases/data-intensive-design/performance.md) | Reliability as “continuing to meet the SLO”; percentile SLOs. Do not re-derive. |
| Catalog | [system-design-patterns-catalog.md](system-design-patterns-catalog.md) id D3. |

---

## 7. Sources

**Canon / frameworks.**
sre.google/sre-book/monitoring-distributed-systems (2016, Ewaschuk) ·
sre.google/workbook/monitoring (Frame et al.) ·
sre.google/workbook/alerting-on-slos (Thurgood et al.; Table 5-8) ·
brendangregg.com/usemethod.html ·
grafana.com/blog/the-red-method-how-to-instrument-your-services (2018-08-03;
Wilkie 2015) ·
grafana.com/files/grafanacon_eu_2018/Tom_Wilkie_GrafanaCon_EU_2018.pdf

**Prometheus / Alertmanager (defaults).**
prometheus.io/docs/prometheus/latest/configuration/configuration
(`scrape_interval` 1m, `scrape_timeout` 10s, `evaluation_interval` 1m) ·
prometheus.io/docs/prometheus/latest/getting_started (tutorial 15 s) ·
prometheus.io/docs/prometheus/latest/configuration/alerting_rules
(`for` 0s; `up == 0` for 5m example) ·
prometheus.io/docs/prometheus/latest/configuration/recording_rules ·
prometheus.io/docs/alerting/latest/configuration
(`group_wait` 30s, `group_interval` 5m, `repeat_interval` 4h) ·
prometheus.io/docs/concepts/jobs_instances (`up` and scrape series) ·
prometheus.io/docs/prometheus/latest/querying/basics (lookback 5m; staleness) ·
prometheus.io/docs/practices/pushing ·
prometheus.io/docs/introduction/faq (pull vs push) ·
prometheus.io/docs/practices/instrumentation (cardinality < 10 / investigate > 100) ·
prometheus.io/docs/practices/naming (no user-id labels; unit suffixes) ·
prometheus.io/docs/practices/histograms ·
github.com/prometheus/client_golang `prometheus/histogram.go` `DefBuckets`

**OpenTelemetry.**
opentelemetry.io/docs/specs/otel/metrics/sdk (`exportIntervalMillis` 60000) ·
opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables
(`OTEL_METRIC_EXPORT_INTERVAL`) ·
opentelemetry.io/docs/specs/semconv/http/http-metrics
(`http.server.request.duration` buckets) ·
opentelemetry.io/docs/specs/semconv/non-normative/http-migration ·
opentelemetry.io/docs/specs/semconv/system/process-metrics ·
github.com/open-telemetry/opentelemetry-collector-contrib
`receiver/prometheusreceiver/README.md` ·
`receiver/hostmetricsreceiver/README.md` (`collection_interval` 1m)

**In-tree.**
cases/data-intensive-design/nfr-references.md ·
cases/SystemDesignPatterns/CircuitBreaker.md § Observability ·
docs/research/sysdesign/circuit-breaker-external-research.md ·
docs/research/sysdesign/failover-degradation-external-research.md (C3; health ≠ monitoring)

---

## 8. Uncertain / left out

- **“Prometheus defaults to a 15 s scrape.”** Contradicted by the
  configuration schema (1m). The getting-started comment is tutorial
  prose. Not asserted as a software default.
- **kube-prometheus / kube-prometheus-stack / Grafana Alloy chart
  scrape intervals** (commonly 15 s or 30 s in secondary write-ups).
  Not fetched from those Helm values this pass.
- **Prometheus 3 lookback-delta.** A 2026 secondary post claims the
  default changed from 5m to the scrape interval. The official querying
  basics page fetched 2026-09-13 still says 5 minutes. Unresolved;
  cite the docs page, not the blog.
- **Workbook Table 5-8 vs the example `expr`.** The table lists three
  rows (14.4× 1h/5m, 6× 6h/30m, 1× 3d/6h). The immediately preceding
  example also has a 3× / 24 h / 2 h ticket pair (and Table 5-6’s
  “10% in three days” ticket). D5 should treat Table 5-8 as the
  labelled recommendation and the extra pair as an example, not invent
  a fourth official row.
- **`for:` on SLO burn-rate rules.** Workbook iteration 3 argues
  against `for` as a *window substitute*. SoundCloud’s 2018 post (not
  re-fetched as primary) adds `for: 2m/15m/1h` on top of multi-window
  rules. That addition is not in Table 5-8.
- **Gregg USE first-publication date** (page is living; PDF
  “Communications of the ACM, 2013-ish” not confirmed this pass).
- **Wilkie 2015** is Wilkie’s own date in the 2018 Grafana post; no
  2015 primary URL fetched.
- **OTel Collector contrib version pin** as of 2026-09-13 (READMEs
  fetched from `main` / current docs). Defaults above are from those
  pages, not a release tarball.
- **`scrape_native_histograms` default false** is from the
  configuration schema fetched today; a future Prometheus 3.x flip
  would change ingestion, not the 1m scrape interval.
- **PromQL “golden signal” alert recipes** beyond the docs’
  `up == 0` for 5m and the workbook burn-rate `expr` are own
  formulations and are **not** included above.
- **Node-exporter / process-collector default metric lists** and
  kube-state-metrics CPU-quota saturation (Wilkie’s verbal example)
  were not dumped metric-by-metric this pass.
- **Statsd** is named as a peer standard in workbook ch. 4; no
  statsd flush-interval default fetched.
- **Security-monitoring and business-analytics** uses of the same
  pipelines — SRE ch. 6 explicitly out of scope.

Everything in this section stays out of any later Concept.
