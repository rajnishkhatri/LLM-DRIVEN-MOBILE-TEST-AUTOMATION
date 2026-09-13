---
type: reference
title: 'Server-side monitoring (golden signals, alerting)'
description: >-
  Continuous golden-signal telemetry on a production server — host, process,
  runtime, and inbound RED — plus the mechanical alerting path (scrape health,
  pending/for, grouping, inhibition, burn-rate shape). Complements health
  checks; is not SLO policy. Covers scrape vs push, verified Prometheus and
  OpenTelemetry defaults, cardinality and staleness, and failure modes of
  monitoring itself.
tags: [system-design-patterns, reliability, monitoring, golden-signals, alerting]
---

# Server-side monitoring (golden signals, alerting)

**See also:** [circuit breaker](CircuitBreaker.md) · [failover and health checks](FailoverHealth.md) · [load shedding and backpressure](LoadShedding.md) · [reliability](../data-intensive-design/reliability.md) · [performance](../data-intensive-design/performance.md) · [NFR overview](../data-intensive-design/nfr-overview.md) · [NFR references](../data-intensive-design/nfr-references.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/d3-server-monitoring-external-research.md)

The [circuit breaker](CircuitBreaker.md) decides **whether to call**. [Failover](FailoverHealth.md) decides **whether this instance still receives traffic**. Both *consume* numbers. This pattern owns the complementary question: **what is the distribution of user-visible work on a production server, and is a human needed?** Server-side monitoring is a continuous quantitative pipeline — host, process, runtime, and inbound RPC — plus the mechanical alerting path that turns those series into a page or a ticket.

A probe is a binary routing or restart decision. A golden-signal pipeline is histograms, counters, saturation, and paging. Crossing them produces the two classic failures already on the [health-check](FailoverHealth.md) card: a shallow TCP check that black-holes traffic onto a process serving empty 200s, and a deep dependency check in the load-balancer path that takes the fleet out when one shared backend blinks.

Quality attributes in play: **observability** (the fleet is explainable from the outside) and **reliability** of *operations* (you learn about an SLO threat before users file it). The costs are a second distributed system that can itself page, go silent, or fall over during the incident it was meant to explain.

Sibling owners stay off this card. Catalog **D1** owns the signal taxonomy and RED/USE as *framework names*; this card only applies them to servers. **D2** owns client-perceived RUM and crash reporting — a browser p75 is not a server p99. **D4** owns the trace graph; server histograms may carry exemplars. **D5** owns SLO / error-budget *policy* (which ratio is the SLI, what the objective is, how much budget a page may spend). This card may cite workbook *mechanics* so an implementer can wire rules; it does not pick the objective.

## Lineage and vocabulary

- **SRE book ch. 6, *Monitoring Distributed Systems*** (Ewaschuk, 2016). White-box = internals (`/metrics`, JVM, logs). Black-box = externally visible behaviour. An **alert** is a human-directed notification. Page only when the event is urgent, actionable, requires intelligence, and is novel. First cut: symptom (“what’s broken”) vs cause (“why”). **Four golden signals** — latency, traffic, errors, saturation — “If you can only measure four metrics of your user-facing system, focus on these four.” Split success vs failure latency (a fast HTTP 500 pulls the mean down). Traffic is demand in a system-specific unit (HTTP RPS; concurrent sessions; KV transactions/s). Errors are explicit (HTTP 500), implicit (HTTP 200, wrong content), or by policy (1.2 s against a 1 s commitment). Saturation = how full the *most constrained* resource is, plus prediction (“disk full in 4 hours”). p99 over a one-minute window is the chapter’s leading-indicator example.
- **SRE Workbook ch. 4, *Monitoring*** (Frame et al.). Metrics for pages and dashboards (near-real-time); logs for root cause and more accurate offline reports. Data more than **four to five minutes** stale “might significantly impact” incident response. Prefer monotonic counters. Monitoring config as code. Saturation includes hard limits (RAM, disk, CPU quota) *and* soft ones (fds, thread-pool occupancy, queue wait, log volume); Java heap / metaspace / GC; Go goroutine count. Instrument the RPC client library once so new dependencies are free.
- **Workbook ch. 5, *Alerting on SLOs*** — **D5 owns policy.** Cited here only for implementation shape: Table 5-8, multi-window `AND`, short window ≈ 1/12 of long. They do **not** recommend Prometheus `for:` as a substitute for a long SLO window (a 100% outage then waits as long as a 0.2% drip; a flicker resets the timer).
- **Gregg, USE Method.** For every *resource*: utilization, saturation, and errors. Utilization = busy-time average; saturation = extra work that cannot be serviced (queue length / queued time); errors = event counts. Any non-zero saturation can add latency. Five-minute CPU averages ≤ 80% can hide 100% bursts that already saturate the run-queue.
- **Wilkie, RED Method** (2015; Grafana write-up 2018). For every *service*: Rate, Errors, Duration. Wilkie: USE is machines, RED is users; complementary. Golden signals = “RED + saturation.”
- **Prometheus pull / Pushgateway.** Default collection is scrape-over-HTTP. Pushgateway only for **service-level batch jobs** that cannot be scraped (no machine/`instance` label). Blind use as a push bus: SPOF / bottleneck; no `up`; **never forgets** series unless deleted via its API. FAQ: pull is “slightly better,” not a deciding feature.

Names below come from Prometheus, OpenTelemetry, and the SRE books because those documents publish numeric defaults. The mechanics — pull vs push, histograms vs means, page-on-symptoms — do not require those vendors.

## Three stacked views of one server

Treat a production instance as layers that each get a golden-signal set. Mixing the layers on one chart is how teams page on CPU while users are fine, or the reverse.

| Layer | Framework | What “traffic / rate” is | What “saturation” is | Typical exporters |
|---|---|---|---|---|
| **Host** | USE | interrupt / packet / I/O rate | run-queue, paging, disk wait, NIC drops | node_exporter; OTel `hostmetrics` (`system.*`) |
| **Process** | USE | CPU-seconds, context switches, I/O | thread / fd / handle exhaustion; RSS vs limit | Prometheus `process_*`; OTel `process.*` |
| **Runtime** | USE + workbook “purposeful metrics” | allocations, GC work, goroutine create | heap / metaspace, GC pause, goroutine count | Micrometer / OTel `jvm.*` (renamed from `process.runtime.jvm.*` in semconv 1.22) |
| **Inbound RPC / HTTP** | RED = golden latency / traffic / errors | requests/s by method × route-template × status | in-flight / queue / pool occupancy; p99 as leading indicator | OTel `http.server.request.duration`; Prometheus `http_request_duration_seconds` |

**RED on servers** is the inbound histogram (or counter + histogram pair), not the host CPU. Wilkie’s GrafanaCon queries all read one histogram family:

```
sum(rate(request_duration_seconds_count{job="…"}[1m]))
sum(rate(request_duration_seconds_count{job="…",status_code!~"2.."}[1m]))
histogram_quantile(0.99, sum(rate(request_duration_seconds_bucket{job="…"}[1m])) by (le))
```

A single histogram gives Rate, Errors, and Duration with one instrument, but **status as a label on the duration histogram** multiplies buckets × codes × routes. Prefer a low-cardinality route *template* (`/users/:id`, never the raw path). OTel marks `http.route` conditionally required “if and only if it’s available” and warns it MUST be low-cardinality.

**Saturation is not utilization.** SRE: systems degrade before 100% utilization, so a *target* below the hard limit is required. Gregg: any queued extra work is already a problem; utilization averaged over minutes can look healthy while the run-queue is not. Workbook: watch the resource that will actually cap the service (thread pool, fds, queue wait), not only the metric that is easy. Prediction (“disk full in 4 hours”) is part of the golden-signal definition, not a bonus dashboard. [Load shedding](LoadShedding.md) is what you *do* once saturation is real; this card is how you see it coming.

**Latency instrumentation.** SRE ch. 6: do not alert or capacity-plan on the mean of latency; collect counts in exponentially spaced buckets (their example spacing is factors of ~3). A 100 ms mean at 1 000 RPS can hide 1% of requests at 5 s, and that p99 becomes the *median* of a fan-in frontend. Percentile-sketch literature and why averages mislead already live in [nfr-references.md](../data-intensive-design/nfr-references.md) ([19], [27], [31]–[36]); do not re-derive them here. Split success and error latency or a flood of instant 500s makes the service look faster while it is down.

## Scrape vs push

Two control loops, not two religions.

```mermaid
flowchart LR
    Target["Process /metrics or OTLP"] --> Collect["Collector"]
    Collect --> Store["TSDB"]
    Store --> Rules["Rule evaluation"]
    Rules --> AM["Group / inhibit"]
    AM --> Human["Page or ticket"]
```

**Pull / scrape.** The collector (Prometheus server, OTel Collector `prometheusreceiver`, Grafana Alloy `prometheus.scrape`) schedules HTTP GETs against `/metrics`. The scheduler owns the interval; a failed GET is itself a time series (`up=0`). When a target disappears, its series are marked stale (Prometheus inserts a stale NaN; lookback then drops them). Extra scrapers (laptop, second HA Prometheus) do not require the app to know about them.

**Push.** The process *exports* on a timer (OTel `PeriodicMetricReader` → OTLP) or writes to an intermediary (Pushgateway, statsd). The app owns the interval. There is no automatic `up`. If the exporter dies, the last samples persist until lookback / cache expiry — or, on Pushgateway, **forever**.

| Situation | Prefer | Why |
|---|---|---|
| Long-running server; you need `up`; scale-in should drop series | **Scrape** | Lifecycle of the process matches lifecycle of the series |
| Short-lived batch / cron that exits before the next scrape | **Pushgateway**, service-level job, **no** `instance` label | Prometheus’s documented exception, not a push bus |
| Processes behind NAT that cannot be scraped | **Push** (OTLP to a Collector) | The Collector is then what Prometheus scrapes |
| Many processes → one Collector → one store | Push at the edge, **pull at the store** | The common OTel shape |

Trade-off: scrape couples discovery to the collector (you must find targets); push couples availability to the app’s exporter and to the receiver’s backlog. Neither removes the need to monitor the monitor.

## Alerting implementation (policy stays in D5)

A production alerting path has four mechanical stages. D5 decides *what ratio* is the SLI; this section is how the path behaves once that ratio exists.

1. **Scrape / export health.** Prometheus writes, on every scrape: `up{job,instance}` (1 reachable, 0 failed), `scrape_duration_seconds`, `scrape_samples_scraped`, `scrape_samples_post_metric_relabeling`, `scrape_series_added` (since v2.10). A missing golden-signal graph is often `up=0` or a cardinality drop, not an application regression. The docs’ own example rule pages `up == 0` with `for: 5m`.
2. **Rule evaluation.** `evaluation_interval` default **1m**. Alert `for:` default **0s** (fires on first true evaluation). `keep_firing_for` default **0s**. A zero `for` on a noisy gauge is how alert storms start.
3. **Notification grouping.** Alertmanager route defaults: `group_wait` **30s**, `group_interval` **5m**, `repeat_interval` **4h**. `repeat_interval` is rounded up to a multiple of `group_interval`. Group-by and inhibit so one saturated dependency is one page, not N.
4. **Burn-rate *shape*** (workbook Table 5-8, 99.9% / 30-day example — **thresholds are D5’s to accept or reject**): page at 14.4× over **1 h AND 5 m** (2% budget) or 6× over **6 h AND 30 m** (5%); ticket at 1× over **3 d AND 6 h** (10%). Short window ≈ 1/12 of long, so the alert resets when burn *stops*, not when the long window drains.

SRE ch. 6 paging questions that belong on the *implementation* side (independent of which SLO D5 picked): does this detect something urgent, actionable, and user-visible (or imminently so, including N+0 and “nearly full”)? Will I learn to ignore it? Are users actually affected (filter drained / test traffic)? Can the action be automated? Is someone else already paged for the same incident?

Cause-oriented pages (CPU high, disk full) are debugging aids; symptom-oriented pages (error ratio, latency, `up`) are what should wake a human. Saturation is the exception SRE carves out: page when a signal is *nearly* problematic, because black-box users have not broken yet.

`up` is scrape reachability, not application correctness; a process can export `up=1` while every request is 500. Deep dependency checks belong in *external monitoring*, not in the LB health path (Yanacek, already on the [C3](FailoverHealth.md) card).

## Configuration

Library and collector defaults are generic. Override scrape cadence to the resolution the page actually needs; override histogram buckets to the latency the SLO actually cares about.

| Knob | Role |
|---|---|
| Scrape / export interval | How often a sample exists. Sets the floor on detection *and* on cardinality × write volume. |
| Scrape / export timeout | Must be ≤ the interval. A timeout on a huge `/metrics` looks like an application outage. |
| `for:` / multi-window `AND` | How long a condition must hold before a human is notified. Zero `for` is first-evaluation fire. |
| Group / inhibit / repeat | How many pages one incident becomes, and how often it re-pages. |
| Histogram buckets | Where the quantile is accurate. Defaults are a network-service starting point, not your p99. |
| Label set | Every unique combination is a series. Unbounded labels are a cardinality bomb. |
| `sample_limit` / `body_size_limit` | Scrape-side circuit breaker. Default unlimited. |

### Verified defaults (fetched 2026-09-13)

**Prometheus’s software default is not 15 s.** The configuration schema documents `global.scrape_interval` **1m**. The getting-started tutorial *sets* `scrape_interval: 15s` and comments “By default, scrape targets every 15 seconds” — that comment describes the *tutorial file*. Treat 15 s as a common *chosen* resolution, not a vendor default.

| Knob | Default | Source |
|---|---|---|
| `global.scrape_interval` | **1m** | Prometheus config |
| `global.scrape_timeout` | **10s** (must be ≤ interval) | Prometheus config |
| `global.evaluation_interval` | **1m** | Prometheus config |
| `scrape_configs[].metrics_path` | `/metrics` | Prometheus config |
| `sample_limit` / `body_size_limit` / `target_limit` | **0** = unlimited | Prometheus config |
| Alert `for` / `keep_firing_for` | **0s** | Prometheus alerting rules |
| Docs example: `up == 0` | `for: 5m` | Prometheus alerting rules |
| Docs example: latency | `for: 10m` | Prometheus alerting rules |
| Alertmanager `group_wait` | **30s** | Alertmanager config |
| Alertmanager `group_interval` | **5m** | Alertmanager config |
| Alertmanager `repeat_interval` | **4h** (rounded up to a multiple of `group_interval`) | Alertmanager config |
| Query lookback (`--query.lookback-delta`) | **5 minutes** | Prometheus querying basics |
| OTel Collector `prometheusreceiver` omitted fields | **1m / 10s** (embedded Prometheus scrape YAML) | contrib README |
| OTel `hostmetricsreceiver` `collection_interval` | **1m** (`initial_delay` **1s**) | contrib README |
| OTel SDK `PeriodicMetricReader` | `exportIntervalMillis` **60000**; `exportTimeoutMillis` **30000** | OTel metrics SDK + env vars |
| Env overrides | `OTEL_METRIC_EXPORT_INTERVAL=60000`, `OTEL_METRIC_EXPORT_TIMEOUT=30000` | OTel SDK env vars |

**OTel HTTP server semantic conventions** (`http.server.request.duration`): Histogram, unit `s`, **stable**, recommended. Advisory buckets `[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10]`. Required attrs: `http.request.method`, `url.scheme`. Conditionally required: `http.response.status_code`, `http.route` (template only), `error.type`. `server.address` / `server.port` are **Opt-In** because they are high-cardinality if taken from request headers (migration note, v1.23). Companion saturation gauge: `http.server.active_requests`. Rename: `http.server.duration` (ms) → `http.server.request.duration` (s) at v1.23.1.

**Prometheus classic `DefBuckets`** (`client_golang` `histogram.go`): `{.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10}` plus implicit `+Inf`. Tailored to “response time (in seconds) of a network service”; the comment says you will most likely need custom buckets. **OTel HTTP adds 0.075, 0.75, 7.5** that Prometheus `DefBuckets` omit — do not assume they match. Native histograms are preferred in current Prometheus histogram docs; `scrape_native_histograms` default in the schema fetched 2026-09-13 is **false**.

**Staleness.** Failed scrape marks previously exposed series stale; subsequent failed scrapes ingest only `up` and friends. Instant selectors honor stale markers immediately; series with *explicit* timestamps without `track_timestamps_staleness` linger for the lookback. Graphs go **blank**, not flat — easy to misread as “load disappeared.”

**Cardinality guidance (Prometheus practice, not a hard server limit).** Never put user IDs, emails, or other unbounded sets on labels; every label-set is a series. “Try to keep the cardinality of your metrics below 10”; for those that exceed it, “a handful across your whole system”; “vast majority … should have no labels”; cardinality **over 100** (or the potential to grow there) → reduce dimensions or move the analysis off the metrics TSDB. Their worked example: `node_filesystem_avail` in the tens of series/node × 10 000 nodes ≈ 100 000 series is “fine”; per-user quota on that metric is not.

**Naming vs OTel.** Prometheus SHOULD suffix units (`_seconds`, `_bytes`, `_total`). OTel puts the unit in metadata and uses `http.server.request.duration` without a suffix. A Collector translation step is required if both names must coexist; do not assume they are the same series.

Breaker *metric names* (Resilience4j / Polly / Envoy) live on the [circuit breaker](CircuitBreaker.md) observability section. That card is a **consumer** of this pipeline, not a second home for golden signals.

## What to emit, and what pages

A server without these series is flying blind; a server that emits them and pages on CPU is still flying blind.

| Series | Layer | What it tells you | Page on it? |
|---|---|---|---|
| Inbound request rate, error ratio, duration histogram (RED) | RPC / HTTP | User-visible demand and failure | **Yes** — symptom. One global error-rate / latency page, not one per node. |
| `http.server.active_requests` / pool / queue occupancy | RPC saturation | How full the request path is before 100% CPU | **Yes, when nearly full** — SRE’s saturation exception |
| `up`, `scrape_duration_seconds`, samples scraped | Collector | Whether the graph is missing because the *monitor* died | **Yes** — docs example `up == 0` for 5m |
| Host USE (run-queue, disk wait, NIC drops) | Host | Why RED moved | No — debugging after the symptom page; inhibit when the dependency is already firing |
| Process / runtime USE (fds, heap, GC, goroutines) | Process / runtime | Soft limits that cap the service | Ticket or inhibit; page only when the constrained resource is *nearly* problematic |
| Breaker state, trip rate, not-permitted, fallback rate | Integration (C1) | Silent degradation of one dependency | Open longer than recovery, or flapping — see [CircuitBreaker](CircuitBreaker.md) § Observability |
| Exemplars on the duration histogram | D4 | Which trace to open | Never a page by itself |

Log volume and traces stay on the side of *root cause*. Workbook ch. 4: metrics for the page; logs for why. Do not combine monitoring with profiling, crash-dump, and traffic inspection in one binary (SRE ch. 6: fragile).

## Tuning

Defaults are a starting point, not a calibration. The three inputs are the detection floor you can afford, the cardinality the TSDB can hold, and the page rate a human will not learn to ignore.

| Knob | Too low / too tight | Too high / too loose | Starting point |
|---|---|---|---|
| Scrape / export interval | Write amplification; collector load becomes the outage | Detection floor misses the incident (workbook: > 4–5 min stale hurts response) | Software default **1m** / OTLP **60s**. Choose 15 s only if a dashboard or page *needs* that resolution — it is not the binary default. |
| Scrape timeout | False `up=0` on a slow `/metrics` | Hung scrape overlaps the next interval | **10s**, and keep `/metrics` cheap enough to beat it |
| Histogram buckets | Quantile jumps between coarse `le`s; p99 is fiction | Extra `le` × status × route series | OTel HTTP advisory set, then *cut* buckets that your SLO will never use |
| Label dimensions | — | Cardinality bomb; TSDB OOM during the incident | Route *template*, not raw path; no user id / request id / email; investigate before cardinality 100 |
| `for:` on a gauge | `0s` → first-evaluation fire → storm | A 100% outage waits as long as a drip | Docs: `up == 0` for **5m**; latency example **10m**. Do **not** use `for:` as a substitute for a long SLO window (workbook ch. 5). |
| Group-by / inhibit | Full label set → one incident, N pages | Over-inhibit hides a second fault | Group on the shared dependency; inhibit children when the parent is firing |
| `sample_limit` | Drops the series you needed | Default **0** = unlimited, bomb ingested | Set as a scrape circuit-breaker *before* the first unbounded label ships |
| Host vs RED pages | CPU page while users are fine | RED-only, miss “disk full in 4 hours” | Page on RED + `up` + near-saturation; keep USE on the debug dashboard |

Revisit after a week of page volume and `scrape_samples_scraped`. A breaker that trips often is usually a threshold; a monitor that pages often is usually `for: 0s` or `group_by` too wide.

## Failure modes of monitoring itself

- **Missing scrapes / silent dashboards.** `up=0` is the first alert, not a footnote. A scrape timeout (default 10 s) on a huge `/metrics` looks like an application outage. `sample_limit` / `body_size_limit` default off: a cardinality bomb is ingested until the TSDB OOMs, then *everything* pages. After a failed scrape, application series go stale — blank, not flat. Pushgateway and un-timestamped push caches do the opposite: they lie that the job is still healthy.
- **Cardinality bombs.** Unbounded labels (user id, request id, raw URL, email, build SHA, exception message) multiply: buckets × status × route × instance. Classic histograms make this worse (`le` is already a dimension). The failure mode of monitoring itself is that the collector falls over *during* the incident the metrics were meant to explain. Mitigations with sources: drop at scrape (`metric_relabel_configs`); `sample_limit` as a scrape circuit-breaker (exists; default 0 = off); keep identifiers on logs/traces (D4), not series; OTel’s demotion of `server.address` to Opt-In is exactly this class of bug.
- **Alert storms.** `for: 0s` + 1 m evaluation + one rule per instance × endpoint turns one saturated database into thousands of pages. SRE ch. 6: too-frequent pages are skimmed, including the real one. Workbook: severity classes; inhibit children when the dependency is already firing; one global error-rate page, not one per node. Alertmanager 30 s / 5 m / 4 h is useless if `group_by` is the full label set. Bigtable SRE (ch. 6): mean SLO + email-and-page volume; they loosened to p75, disabled email, fixed the tail. Gmail: paging per de-scheduled task (thousands of tasks, each a fraction of a percent of users) was unmaintainable — rote pages should have been automated.
- **Too-clever monitors.** SRE ch. 6: limited success with deep dependency hierarchies and “magic” anomaly detectors; paging rules must be readable by the whole team. Unused series (no dashboard, no alert) are removal candidates. Combining monitoring with profiling / crash-dump / traffic inspection in one binary is called out as fragile.
- **Wrong layer / health-check substitution.** CPU pages without RED: users may be fine or already down. RED-only: you miss “disk full in 4 hours.” Wilkie: run both. Using the LB probe as the only server monitor (or 5xx rate as the only readiness signal) collapses C3 and D3.

## When not to use this style

- Single-process tool, one operator, no paging rotation (SRE: do not create a “stare at a screen” job).
- Low traffic: workbook ch. 5, one failure in 10 req/h = 10% hourly = 1 000× burn on a 99.9% SLO — do not page that blindly. Synthetic traffic / combining services / changing the product are D5-adjacent.
- Batch / cron: scrape a long job *and* push a completion gauge; HTTP RED does not apply.
- Narrow security audits — ch. 6 sets those outside “something seems a bit weird” paging.
- Client-perceived quality (web vitals, mobile crashes) — that is **D2**. Substituting server p99 for RUM hides the user’s path.
- SLO *policy* (which ratio, which objective, how much budget a page may spend) — that is **D5**. Wiring Table 5-8’s shape without accepting its thresholds is unfinished work, not a default.

Symptom pages hide causes, so you still need USE series and (D4) traces *after* the page. Collecting both at 15 s / high cardinality is how the monitor becomes the outage.

## Trade-offs

| Buy | Pay |
|---|---|
| Symptom pages (error ratio, latency, `up`) wake a human on user-visible failure | Causes still need USE series and traces after the page |
| Four golden signals bound what must exist on day one | Saturation is a different layer than RED; measuring only one hides the other |
| Scrape gives `up` and series lifecycle matching the process | Couples discovery to the collector; a timed-out scrape looks like an app outage |
| Push fits batch, NAT, and the OTel edge | No automatic `up`; Pushgateway never forgets; last samples lie |
| Multi-window burn-rate shape resets when burn stops | Thresholds and which SLO they attach to are D5’s; `for:` is not a window substitute |
| Default 1 m scrape / 60 s OTLP export is cheap to run | Detection floor is a minute; 15 s is a *choice*, paid in write volume |
| Histograms make p99 computable | Bucket × status × route cardinality; means still mislead if you alert on them |
| Alertmanager 30 s / 5 m / 4 h plus inhibit | Useless if `group_by` is the full label set or `for` is 0 s on a noisy gauge |

Health checks decide **whether this instance receives work**. Golden signals decide **whether a human is needed**. SLOs decide **how much error is allowed**. Traces decide **which hop**. Do not collapse the four.

## Sources

Verified 2026-09-13; the full URL list, per-claim provenance, and items deliberately left out (including the “Prometheus defaults to 15 s” tutorial comment, kube-prometheus chart intervals, and an unresolved Prometheus 3 lookback claim) are in the [external research note](../../docs/research/sysdesign/d3-server-monitoring-external-research.md). Items already cited in this tree are referenced by their number in [nfr-references.md](../data-intensive-design/nfr-references.md).

- Canon: SRE book ch. 6 (Ewaschuk); SRE Workbook ch. 4 (Frame et al.) and ch. 5 Table 5-8 (Thurgood et al.; implementation shape only); Gregg USE; Wilkie RED (2015 / Grafana 2018).
- Collectors: Prometheus configuration, alerting rules, querying basics, push practices, instrumentation/naming/histogram practices; Alertmanager configuration; `client_golang` `DefBuckets`; OTel metrics SDK and env vars; OTel HTTP semconv; Collector contrib `prometheusreceiver` and `hostmetricsreceiver`.
- In-tree consumers: [CircuitBreaker.md](CircuitBreaker.md) § Observability; [FailoverHealth.md](FailoverHealth.md) (health ≠ monitoring); [nfr-references.md](../data-intensive-design/nfr-references.md) SLOs [28], nines [29], meaningful availability [30], histograms / sketches [31]–[35], percentile pitfalls [19][36], tail [27].
