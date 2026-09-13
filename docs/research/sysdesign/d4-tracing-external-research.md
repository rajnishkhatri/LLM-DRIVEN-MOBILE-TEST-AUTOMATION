---
type: research
title: 'Distributed tracing & correlation — external research (2026-09-13)'
description: >-
  Source-verified research for catalog D4: W3C Trace Context and Baggage,
  the OpenTelemetry span and sampling model, context propagation across
  HTTP/gRPC/queues, log correlation via trace_id, and tail-based sampling
  collectors — with versions, 2026-09-13 fetch dates, and the failure
  modes of tracing itself.
tags: [research, system-design-patterns, D4, tracing, opentelemetry]
---

# Distributed tracing & correlation — external research (2026-09-13)

> **What this is.** Evidence pass for catalog **D4**
> ([catalog of record](system-design-patterns-catalog.md)). The future
> Concept stays readable; this note keeps protocol limits, sampler
> defaults, and URLs.
>
> **Method.** Primary pages fetched 2026-09-13. Paraphrase; numbers
> reproduced exactly. Unverified items live in §8 and are **not**
> asserted as fact.
>
> **Existing citations in this tree** (do not duplicate): Dapper
> (Sigelman et al., 2010) [48] in
> [references.md](../../../cases/data-intensive-design/references.md);
> *The Tail at Scale* [27], Hidalgo SLOs [28], Brooker / SRE
> metastability in
> [nfr-references.md](../../../cases/data-intensive-design/nfr-references.md).
> Signal taxonomy (metrics / events / logs / traces, RED/USE) is
> **D1** — cited, not re-derived. SLO / error-budget / burn-rate
> policy is **D5** — not rewritten here.

---

## 1. Scope and non-goals

**Owns.** Identifying and following one request across process, protocol, and vendor boundaries: W3C `traceparent` / `tracestate`, W3C `baggage`, the OpenTelemetry span model, sampling (head / parent-based / tail — current spec names), HTTP / gRPC / queue propagation, log↔trace correlation (`trace_id` / `span_id` / `trace_flags`), collector tail-sampling, tool-neutral defaults, and the failure modes of *tracing itself*.

**Does not own.**

| Sibling | Stays there |
|---|---|
| **D1** | Signal taxonomy; RED/USE as golden-metric *frameworks*. This note only says how traces feed them. |
| **D2** | RUM, web vitals, crash reporting, mobile client traces. |
| **D3** | Server-side golden-signal dashboards and page-level alerting. |
| **D5** | SLOs, error budgets, burn-rate policy. Traces diagnose a page; they are not the SLO. |
| **C7** | Timeout/deadline *as a reliability control*. This note only records the remaining budget as a span attribute and cites [timeouts-and-delays.md](../../../cases/data-intensive-design/timeouts-and-delays.md). |
| **A1 / A2** | REST/gRPC wire semantics and queue/stream mechanics. |

---

## 2. Lineage / vocabulary

**Dapper (April 2010).** Google technical report dapper-2010-1 (Sigelman, Barroso, Burrows, Stephenson, Plakal, Beaver, Jaspan, Shanbhag) — [48]. A *trace* is a tree of *spans* (name, span id, parent id, shared trace id). Roots have no parent. Dapper ids were probabilistically unique **64-bit** integers; W3C/OTel `trace-id` is **128-bit** / 16 bytes, `span-id` stays 64-bit / 8 bytes. Instrumentation was restricted to threading, control-flow, and RPC libraries. Goals: low overhead, application-level transparency, ubiquitous deployment, analysis ideally within a minute. Sampling was treated as necessary: "just one out of thousands of requests" still yielded useful information; a §4 sensitivity table includes rates down to **1/1024**. Root-span create/destroy averaged **204 ns**, non-root **176 ns** (2.2 GHz x86). Payloads were deliberately not logged. 70% of spans and 90% of traces carried at least one application annotation. Median collection latency **< 15 s**. Prior systems named: Magpie, X-Trace, Pinpoint. Cite [48]; do not copy the paper.

**Open-source line.** Zipkin (Twitter, 2012) popularized B3 headers. Jaeger (Uber, 2015) added remote sampling. OpenCensus + OpenTracing merged into **OpenTelemetry** (2019); tracing clients hit **1.0.0** in 2021. Live spec this fetch: **v1.60.0** (GitHub 2026-08-07). Semantic conventions **v1.44.0** (2026-08-04).

**W3C Distributed Tracing WG.** Trace Context Rec (2021-11-23): vendor-specific headers break traces at SaaS, mesh, and cloud boundaries. Portable fix = fixed-length `traceparent` + extensible `tracestate`. Application-defined request properties are a *separate* header, `baggage` — independent of whether a trace exists.

| Term | Meaning (sourced) |
|---|---|
| **Trace** | Forest of spans sharing one `trace-id`. |
| **Span** | One unit of work: name, `SpanContext`, parent, kind, start/end, attributes, events, links, status. |
| **SpanContext** | On-the-wire identity: `trace-id`, `span-id`, `trace-flags`, `tracestate`. Immutable once created. |
| **Sampled flag** | LSB of `trace-flags`. A *recommendation*, not a mandate (trust, bugs, load). |
| **Head sampling** | Decision at span start from data present at creation. In a fleet, usually parent-based children following a root decision. |
| **Parent-based** | Child matches the parent's `SampledFlag`. OTel `ParentBased` decorator. |
| **Tail sampling** | Decision after spans are assembled downstream. Not an SDK sampler; a collector policy. |
| **Baggage** | Application-defined request key/values. Not span attributes; not identity. |
| **Correlation** | Joining logs / metrics / traces on `trace_id` (and optionally `span_id`). |

Cindy Sridharan, *Distributed Systems Observability* (2018) [46] and Charity Majors' 2019 retrospective [47] treat traces as one observability signal. The four-signal table already in-tree is [monitoring-observability.md](../../../cases/fincancial-data-architecture/monitoring-observability.md). **D1 owns the taxonomy.**

---

## 3. Mechanics (Group D depth bar)

### 3.1 Signals and semantics (traces, not D1)

A trace is the **causal graph** of one request. Metrics tell you *that* p99 moved; a sampled trace tells you *which* hop. RED (rate, errors, duration) can be *derived* from SERVER/CLIENT spans (Collector `spanmetrics` is one implementation) only if names/attributes stay low-cardinality and sampling is 100% or consistently weighted. USE stays on resource metrics. **Cite D1** for the frameworks.

Span **status** is `UNSET` (default), `OK`, or `ERROR`. A description is ignored unless the code is `ERROR`. HTTP/RPC conventions map timeouts to `error.type=timeout` and gRPC `DEADLINE_EXCEEDED` — they do **not** define a standard attribute for the *deadline value* (verified against semconv v1.44.0 HTTP and RPC pages, 2026-09-13). Record remaining deadline as a **custom low-cardinality duration** (ms left, or the configured budget), not an absolute timestamp: clocks are unbounded guesses ([timeouts-and-delays.md](../../../cases/data-intensive-design/timeouts-and-delays.md)). An absolute deadline as a span attribute is high-cardinality *and* wrong under skew.

### 3.2 W3C Trace Context — `traceparent` / `tracestate`

**Level 1 Recommendation** 2021-11-23: `https://www.w3.org/TR/2021/REC-trace-context-1-20211123/` (latest published `https://www.w3.org/TR/trace-context-1/`). Fetched 2026-09-13. This is the interoperable default.

**Level 2** Candidate Recommendation Draft 2024-03-28: `https://www.w3.org/TR/2024/CRD-trace-context-2-20240328/`. **Not** a Recommendation this fetch. Adds the **random-trace-id** flag (bit 1, `0x02`): when set, the right-most **7 bytes (56 bits)** of `trace-id` MUST be uniform over `[0 .. 2^56−1]`. Sampled remains bit 0 (`0x01`). Test bits independently: `01` and `03` are both sampled; `02` and `03` both claim randomness. OTel `ProbabilitySampler` depends on this flag (or explicit `ot=rv:…`) for consistent thresholds.

**`traceparent` version `00`.** Fixed length, lowercase hex:

```
version(2)-trace-id(32)-parent-id(16)-trace-flags(2)
00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01
```

`version` `ff` is invalid. All-zero `trace-id` or `parent-id` is invalid — vendors MUST ignore the header. Header name SHOULD be sent lowercase, MUST be accepted in any case. Higher-version headers shorter than **55** characters: restart the trace; otherwise parse the three known fields and emit version `00`. Two compliance levels: **forward** (MUST pass both headers unbroken) vs **participate** (rewrite `parent-id`, update own `tracestate` entry, left-most).

**`tracestate`.** Vendor key/value companion. Max **32** list-members. Simple keys: lowercase / digits / `_` `-` `*` `/`. Multi-tenant: `tenant-id@system-id`. Value: up to **256** printable ASCII except `,` and `=`. One entry per key; on re-entry the vendor overwrites and moves left. SHOULD propagate at least **512** characters. Truncate **whole** entries: drop **> 128** char entries first, then from the **end**. Failed `traceparent` parse ⇒ MUST NOT parse `tracestate`; the converse is false. The sampled flag is explicitly not a strict rule (trust/abuse, buggy caller, callee downsampling).

### 3.3 W3C Baggage (independent of tracing)

**CR Snapshot 2024-05-30**, `https://www.w3.org/TR/2024/CR-baggage-20240530/`. Fetched 2026-09-13. History page shows no later publication. Browsers / user-agents are out of scope. Header `baggage`; UTF-8 encoded but restricted to `baggage-octet`; other code points MUST be percent-encoded. Multiple headers combine per RFC 7230.

**Minimum platform limits (MUST propagate when both hold):** resulting string has **≤ 64** list-members **and** **≤ 8192** bytes. If either fails, MAY drop whole members (selection unspecified) and MUST NOT propagate a *partial* member. Implementers MAY define higher limits. W3C ABNF does not require unique keys; producers SHOULD avoid duplicates.

**Privacy (normative consideration).** The header "can contain user-identifiable data"; no key has semantic meaning. Systems MUST assess header-abuse risk. Strip or refuse at trust boundaries. The spec's own `userId=alice` example is the anti-pattern for a public hop.

**OTel Baggage API** (stable, `https://opentelemetry.io/docs/specs/otel/baggage/api/`): stricter than W3C — each name maps to **exactly one** value; names/values case-sensitive UTF-8; container immutable; API MUST work with no SDK; a W3C `TextMapPropagator` is required. Name conflict: new pair wins. MUST be able to **clear all baggage** before an untrusted process. Default composite propagator: `OTEL_PROPAGATORS=tracecontext,baggage`.

Trade-off: baggage is the only standard way to carry tenant / debug / canary bits to every hop without putting them on every span; it is also a PII and header-amplification channel. Prefer a short allow-list; never user identifiers.

### 3.4 OpenTelemetry span model

Fetched `https://opentelemetry.io/docs/specs/otel/trace/api/` and `…/trace/sdk/` on 2026-09-13 (live pages; spec **1.60.0**, 2026-08-07). A `Span` has name; immutable `SpanContext`; parent (`Span`, `SpanContext`, or null); `SpanKind`; start/end (ms min / ns max); attributes; links; timestamped events; status. After end time is set, name / attributes / events / status MUST NOT change. Attributes present **at creation** are the only ones a sampler is guaranteed to see.

**`SpanKind`** (default `INTERNAL`): `CLIENT` outgoing request/response (usually parent of a remote `SERVER`); `SERVER` incoming request/response; `PRODUCER` outgoing deferred (enqueue); `CONSUMER` incoming deferred (process); `INTERNAL` in-process.

**HTTP span names** (semconv HTTP, fetched 2026-09-13): SHOULD be `{method} {target}` when `{target}` is low-cardinality (`http.route` on servers, `url.template` on clients); otherwise `{method}`. Instrumentation **MUST NOT** default to the raw URI path. `http.route` MUST be a template (placeholders for dynamic segments) and MUST NOT be filled from the URI path just to have a value.

**Messaging** (semconv — **Status: Development** as of v1.44.0): a producer SHOULD attach a **message creation context** to each message, preferably immutable by intermediaries. Without it, consumer traces cannot correlate with the producer. Default when processing happens under another ambient span: `CONSUMER`/`process` is a **child of the ambient span** and **links** to the message creation context. Using the message context as parent is opt-in and NOT RECOMMENDED by default when an ambient span exists. Operations: create / send / receive / process / settle. Existing instrumentations on ≤ v1.24.0 of the messaging document SHOULD NOT flip defaults until messaging is marked stable (`OTEL_SEMCONV_STABILITY_OPT_IN=messaging` / `messaging/dup`).

### 3.5 Sampling — current spec (2026-09-13)

The SDK page is explicit that **"head"** is overloaded (decision-at-start *or* a fleet using parent-based children) and **"tail"** means a downstream, usually whole-trace, decision. There is **no** SDK `TailSampler`. Tail sampling is a collector processor.

**Default sampler:** `ParentBased(root=AlwaysOn)` = `OTEL_TRACES_SAMPLER=parentbased_always_on`.

| Sampler | Behavior | Spec note |
|---|---|---|
| `AlwaysOn` / `AlwaysOff` | Record all / none | Stable |
| `ParentBased` | Decorator: root / remote-sampled / remote-not / local-sampled / local-not. Defaults: AlwaysOn, AlwaysOn, **AlwaysOff**, AlwaysOn, **AlwaysOff** | Stable. This *is* parent-based sampling. |
| `TraceIdRatioBased` | Ratio on the trace-id. **Ignores** parent `SampledFlag` unless wrapped in `ParentBased` | **Deprecated** for `ProbabilitySampler`. MUST NOT be removed or behaviour-changed until **at least 2027-01-01**. Algorithm was never specified; different SDKs may disagree on the same id. Recommended **only for roots** (with `ParentBased`). |
| `ProbabilitySampler` | Consistent probability using W3C L2 56-bit randomness; writes threshold `th` (and optional `rv`) into the `ot` `tracestate` key | Current replacement. Also ignores parent `SampledFlag` — wrap in `ParentBased` / `CompositeSampler`. Min ratio `2^-56`, max `1.0`. |
| `CompositeSampler` + composable AlwaysOn/Off, ParentThreshold, Probability, RuleBased | Standard-compliant threshold propagation | Current spec; language SDKs landing through 2026. |
| `JaegerRemoteSampler` | Poll a remote API; may vary by span name (`/product` 10%, `/admin` 100%, `/metrics` never) | Optional |

`OTEL_TRACES_SAMPLER_ARG` for `traceidratio` / `parentbased_traceidratio`: probability in `[0, 1]`, **default 1.0** if unset. Invalid args MUST be logged and ignored.

**Head vs tail.** Head (parent-based ratio) is cheap: unsampled requests pay a thread-local check; traces are complete or absent; Dapper's 1/1024 rationale still holds. It is **biased against the traces you want** (rare 5xx, tail latency) because the decision is made at start, before status exists. Tail keeps the needles and drops the hay, at the cost of buffering every span, sticky routing by `trace_id`, and a decision delay (`decision_wait` default **30 s**). Design recommendation (not a vendor SLA): parent-based probability at the SDK *plus* a collector tail policy for `status_code=ERROR` and high latency, with a small residual probabilistic keep.

**Biased sampling** is a failure of the signal itself. Mixed `TraceIdRatioBased` SDKs produce partial traces. Head-sampling 1% of requests then alerting on "error rate from spans" undercounts errors unless every error is force-recorded or the backend uses `th` adjusted counts. Tail policies that keep only errors make the stored corpus look like the system is always on fire. Health-check and `/metrics` roots should be `AlwaysOff`; otherwise they dominate volume.

### 3.6 Context propagation — HTTP, gRPC, queues

**HTTP.** Inject/extract W3C `traceparent` + `tracestate` (and `baggage` if enabled) on every hop. Proxies that drop unknown headers restart the forest. Level-1 intermediaries that zero the random flag silently disable consistent probability sampling (OTel SDK warning). Default OTel list: `tracecontext,baggage`. Also recognized: `b3`, `b3multi`, `xray`; `jaeger` and `ottrace` are **Deprecated**.

**gRPC.** Two formats coexist. Historical gRPC / OpenCensus uses binary metadata `grpc-trace-bin` (gRFC A72, fetched 2026-09-13). OTel's default `TextMapPropagator` is W3C. During mixed rollouts, A72's `GrpcTraceBinPropagator` (`GrpcTraceBinContextPropagator` in grpc-java 1.83.0 javadoc, `@ExperimentalApi` this fetch) lets both sides keep `grpc-trace-bin`. A fleet that only configures W3C **drops context** at an OC peer. gRPC deadlines are a timeout *control* (C7; [grpc.io/docs/guides/deadlines](https://grpc.io/docs/guides/deadlines) — no default deadline; remaining time is propagated, on by default in Java and Go). Record `rpc.response.status_code=DEADLINE_EXCEEDED` and the remaining budget as a span attribute; do not invent an OTel standard name.

**Queues.** Inject the message creation context into message headers (same W3C fields, or the broker's native equivalent). A broker that traces *transport* hops still does not correlate producer with consumer unless the creation context rides on the message. Fan-out: one `PRODUCER` context, many `CONSUMER` process spans. Batching needs a create-span (or equivalent) **per message** because a span has one parent. Missing queue context is the usual "the trace ends at the publisher" bug.

### 3.7 Correlation with logs

OTel log data model (stable): optional `TraceId`, `SpanId`, `TraceFlags` on the `LogRecord`, populated from the resolved `Context` at emit. Compatibility spec for **non-OTLP** formats (stable, fetched 2026-09-13): `trace_id` lowercase hex (32 chars), `span_id` lowercase hex (16 chars), `trace_flags` W3C (e.g. `01`). JSON: top-level fields. Syslog RFC 5424: SD-ID `OpenTelemetry`. All three optional; if `SpanId` is present, `TraceId` SHOULD be too.

Logs SDK: if a logger is `trace_based=true`, records with a valid `SpanId` whose sampled bit is **unset** MUST be dropped. Records with no trace context are unaffected. That is a silent hole: debug logs on unsampled requests vanish. Exemplars: `OTEL_METRICS_EXEMPLAR_FILTER` default `trace_based`.

### 3.8 Tail-based sampling collectors

**Component:** `tailsamplingprocessor` in `opentelemetry-collector-contrib`. Stability **beta** (traces). Distributions: `contrib`, `k8s`. Latest contrib this fetch: **v0.160.0** (2026-09-02). README defaults (`main`, 2026-09-13):

| Knob | Default | Role |
|---|---|---|
| `policies` | *required, no default* | Decision rules |
| `sampling_strategy` | `trace-complete` | Timer-path, accumulated tree. Alt: `span-ingest` (per-batch; rejects stateful policies) |
| `decision_wait` | **30 s** | Wait before timer decision / pending cleanup |
| `decision_wait_after_root_received` | **0 s** | Optional earlier decision after root arrives |
| `num_traces` | **50 000** | In-memory trace cap |
| `expected_new_traces_per_sec` | **0** | Allocation hint |
| `decision_cache.*_cache_size` | **0** (off) | LRU of keep/drop for late spans |
| `num_shards` | **1** (max 256) | Hash-by-`trace_id` event loops |
| `maximum_trace_size_bytes` | unset | Immediate drop of oversized traces |

Policy types: `always_sample`, `latency`, `probabilistic`, `status_code`, attribute matchers, `trace_state`, `trace_flags`, `rate_limiting`, `bytes_limiting`, `span_count`, `ottl_condition`, combinators `and` / `not` / `drop` / `composite`. Final decision: any `drop` wins; else any `sample` keeps; else **not sampled**.

**Official statefulness warning.** All spans of a trace MUST reach the **same collector instance**. Scale with a load-balancing exporter (hash on `trace_id`) then a tail-sampler tier. The processor re-batches and drops original context — place it *after* `k8sattributes`. Memory cost = 30 s wait × in-flight traces. `num_traces` eviction + unset caches ⇒ late spans decided without the tree. Combine with SDK AlwaysOn (or a high head ratio) so the collector *sees* errors; head-sampled-away errors never reach the tail policy. Collector `otel.sdk.processor.span.processed` (clarified in semconv 1.44.0) counts hand-off to the exporter, not persist success.

### 3.9 Alerting policy (D4 boundary; D5 owns SLOs)

Traces are a **diagnostic** signal. Page from D3/D5 (golden-signal or burn-rate), then jump to a trace. Do not page on "trace count dropped 20%" — that is usually a sampler, collector, or exporter failure, not a user-facing outage (failure mode of monitoring). If you derive RED from spans, treat it as a *sampled estimate*: require `th` adjusted counts or run an unsampled spanmetrics path for SLO-critical attributes only. Cardinality explosion in `spanmetrics` is a documented class (names such as `GET /user/123`; official mitigation is `set_semconv_span_name` in the transform processor before the connector). Tool-neutral rule: **alert on metrics; attach a trace**.

---

## 4. Verified defaults / standards

Fetched 2026-09-13 unless noted.

| Item | Value | Source |
|---|---|---|
| W3C Trace Context L1 | Rec 2021-11-23; `traceparent` v `00`; sampled `0x01` | w3.org/TR/trace-context-1 |
| W3C Trace Context L2 | CR Draft 2024-03-28; random flag `0x02`; 56-bit randomness | w3.org/TR/trace-context-2 |
| `tracestate` | 32 members; SHOULD propagate ≥ 512 chars; drop >128-char entries first | L1 §3.3.1.5 |
| W3C Baggage | CR Snapshot 2024-05-30; ≤64 members **and** ≤8192 B | w3.org/TR/baggage |
| OTel spec | **v1.60.0** (2026-08-07) | GitHub releases/latest |
| OTel semconv | **v1.44.0** (2026-08-04) | GitHub |
| Default sampler | `ParentBased(root=AlwaysOn)` / `parentbased_always_on` | SDK + env spec |
| Default propagators | `tracecontext,baggage` | env spec |
| Default traces exporter | `otlp` | env spec |
| `TraceIdRatioBased` floor | do not remove before **2027-01-01** | SDK spec |
| Span / event / link / attr-per-event / attr-per-link limits | **128** each; value length unlimited | `OTEL_SPAN_*` |
| Global attribute count / value length / depth | 128 / ∞ / **64** | common spec |
| Batch span processor | delay **5000** ms; export timeout **30 000** ms; queue **2048**; batch **512** | env spec |
| Log batch processor | delay **1000** ms; same timeout / queue / batch | env spec |
| Collector contrib | **v0.160.0** (2026-09-02) | GitHub |
| Tail sampler | beta; `decision_wait` **30 s**; `num_traces` **50 000**; same-instance required | tailsamplingprocessor README |
| Log correlation fields | `trace_id`, `span_id`, `trace_flags` | logging_trace_context (stable) |
| gRPC legacy header | `grpc-trace-bin` (A72) vs W3C default | gRFC A72 |
| HTTP span name | `{method} {low-card target}` or `{method}`; MUST NOT use raw path | semconv HTTP |

**Tool-neutral defaults** (not vendor SLAs): W3C `traceparent`+`tracestate` on every hop that can carry headers; W3C baggage only for a short allow-list; `ParentBased` + `ProbabilitySampler` (not bare `TraceIdRatioBased`) at roots; AlwaysOff for health/metrics routes; inject context on every queue message; put `trace_id`/`span_id` on every log line; record remaining deadline as a duration attribute; run tail sampling only behind trace-id-sticky collectors, with decision caches for late spans; never put user ids, tokens, or payloads in baggage or span attributes.

Trade-off on the 128-attribute default: it stops unbounded auto-instrumentation, but discard is silent aside from one SDK log line per span. High-cardinality is a *value* problem, not a *count* problem — 20 attributes that include `user.id` and a query-string `url` still explode a metrics backend.

---

## 5. Failure modes and when-not-to-use

**Missing context.** A proxy, trigger, or broker that does not forward `traceparent` (or `grpc-trace-bin`, or message headers) restarts the forest. Symptom: one-span traces at every hop. Fix is propagation, not a new backend. Pass-through services MUST forward even if they do not participate.

**Biased / inconsistent sampling.** Mixed `TraceIdRatioBased` implementations; head-sampled metrics treated as complete; tail policies that keep only errors; health-check floods; sampled-flag ignored by a downstream AlwaysOn/AlwaysOff. `ProbabilitySampler` without the L2 random flag (or `rv`) SHOULD log a compatibility warning and may sample inconsistently.

**PII in baggage (and span attributes).** W3C §5: the header can carry user-identifiable data across every hop, including vendors. Dapper refused RPC payloads for the same reason. Tokens in opt-in `http.request.header.*` and `url.full` with credentials (semconv: MUST NOT contain `https://user:pass@…`) are the same class. Clear baggage at trust boundaries.

**High-cardinality names and attributes.** Raw URI paths as span names; unparameterized SQL; query strings; unbounded `error.type`; per-user attributes used as metric dimensions. Semconv HTTP is explicit: MUST NOT default to URI path; `http.route` MUST be a template. The 128-attribute *count* limit does not fix this. `spanmetrics` + a high-card name is a backend outage waiting for a deploy.

**Failure modes of the tracing pipeline itself.**

- Tail sampler OOM / `num_traces` eviction → dropped or partial-decision traces during the incident you wanted.
- No sticky `trace_id` routing → each replica sees a fragment and independently drops.
- Late spans after cache-less eviction → orphaned spans or contradictory keep/drop.
- `trace_based` log filter → debug logs vanish on the unsampled majority.
- Default `parentbased_always_on` at high QPS → backend saturation, then operators disable tracing (Dapper's original fear).
- Collector export success ≠ backend persist; alerting on `span.processed` misses sink failure.
- Clock skew makes span timelines lie ([timeouts-and-delays.md](../../../cases/data-intensive-design/timeouts-and-delays.md)). Deadlines must travel as remaining time — gRPC already converts deadline → timeout for this reason.

**When not to use distributed tracing.** A single process with local logs; a batch job whose unit of work is not a request; hops that cannot carry headers and will not be changed; a compliance boundary that forbids request-scoped identifiers from leaving a trust zone. Then D1 metrics + D3 logs are enough. Do not install AlwaysOn + tail sampling "just in case" on a latency-critical path without a budget: Dapper measured material degradation at 1/1 sampling on a sensitive service.

---

## 6. Cross-links

| Id / note | Why |
|---|---|
| **D1** Monitoring & observability foundations | Signal taxonomy; RED/USE. Cite, do not rewrite. |
| **D2** Client-side monitoring | RUM / mobile traces attach via the same `traceparent`. |
| **D3** Server-side monitoring | Golden-signal dashboards; spanmetrics is an input, not a replacement. |
| **D5** SLOs, error budgets, alerting policy | Page from burn rate; jump to a trace. Do not redefine SLOs. |
| **C7** Timeouts & deadline propagation | Control; this note only records the budget on the span. |
| [nfr-references.md](../../../cases/data-intensive-design/nfr-references.md) | Hidalgo [28], Tail at Scale [27], Brooker / SRE. |
| [timeouts-and-delays.md](../../../cases/data-intensive-design/timeouts-and-delays.md) | Timeout is a guess; record remaining deadline as a duration attribute. |
| [references.md](../../../cases/data-intensive-design/references.md) [48] | Dapper. |
| [nfr-overview.md](../../../cases/data-intensive-design/nfr-overview.md) | Reliability = continue to meet the SLO when parts fail. |
| [monitoring-observability.md](../../../cases/fincancial-data-architecture/monitoring-observability.md) | Four instrumentation types already in-tree. |
| [performance.md](../../../cases/data-intensive-design/performance.md) | Percentiles / tail latency — why tail sampling exists. |

---

## 7. Sources

All retrieved **2026-09-13**.

**Canon / lineage.** static.googleusercontent.com/media/research.google.com/en/us/pubs/archive/36356.pdf (Dapper, April 2010) · research.google/pubs/dapper-a-large-scale-distributed-systems-tracing-infrastructure · cases/data-intensive-design/references.md [48] · cacm.acm.org/research/the-tail-at-scale (Dean & Barroso, 2013) [27].

**W3C.** w3.org/TR/trace-context-1/ (Rec 2021-11-23) · w3.org/TR/2021/REC-trace-context-1-20211123/ · w3.org/TR/trace-context-2/ (CR Draft 2024-03-28) · w3.org/TR/2024/CRD-trace-context-2-20240328/ · w3.org/standards/history/trace-context-2/ · w3.org/TR/baggage/ (CR Snapshot 2024-05-30) · w3.org/TR/2024/CR-baggage-20240530/ · w3.org/standards/history/baggage/.

**OpenTelemetry specification.** github.com/open-telemetry/opentelemetry-specification/releases/tag/v1.60.0 (2026-08-07) · opentelemetry.io/docs/specs/otel/trace/api/ · opentelemetry.io/docs/specs/otel/trace/sdk/ · opentelemetry.io/docs/specs/otel/trace/tracestate-probability-sampling/ · opentelemetry.io/docs/specs/otel/baggage/api/ · opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/ · opentelemetry.io/docs/specs/otel/logs/sdk/ · opentelemetry.io/docs/specs/otel/compatibility/logging_trace_context/ · opentelemetry.io/docs/specs/otel/logs/data-model.

**Semantic conventions.** github.com/open-telemetry/semantic-conventions/releases/tag/v1.44.0 (2026-08-04) · opentelemetry.io/docs/specs/semconv/http/http-spans/ · opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/ · github.com/open-telemetry/semantic-conventions/blob/main/docs/rpc/grpc.md · opentelemetry.io/docs/specs/semconv/non-normative/rpc-migration/.

**Collector / tail sampling.** github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/processor/tailsamplingprocessor/README.md · github.com/open-telemetry/opentelemetry-collector-contrib/releases/tag/v0.160.0 (2026-09-02) · github.com/open-telemetry/opentelemetry-collector-contrib/releases/tag/v0.157.0 (2026-07-21; pkg.go.dev still listed 0.157.0 as a module version) · opentelemetry.io/blog/2022/tail-sampling/ (historical walkthrough; 2022 example numbers are not current README defaults).

**gRPC.** github.com/grpc/proposal/blob/master/A72-open-telemetry-tracing.md · grpc.io/docs/guides/deadlines · grpc.github.io/grpc-java/javadoc/io/grpc/opentelemetry/GrpcTraceBinContextPropagator.html.

**In-tree.** docs/research/sysdesign/system-design-patterns-catalog.md · docs/research/sysdesign/circuit-breaker-external-research.md (method) · docs/research/sysdesign/retry-backoff-external-research.md (gRPC deadline propagation already verified for Java/Go).

---

## 8. Uncertain / left out

- Dapper §4 table cells other than the 1/1024 mention: PDF extract was column-scrambled; only the prose ("one out of thousands") and the 1/1024 rate are used. Exact percent-degradation numbers at each rate are **not** asserted.
- Whether W3C Trace Context Level 2 has advanced past the 2024-03-28 CR Draft: history page this fetch shows no later snapshot.
- Whether W3C Baggage has advanced past the 2024-05-30 CR Snapshot: history page this fetch shows no later snapshot.
- A standard OTel attribute name for "deadline" or "timeout budget": **not found** in HTTP or RPC semconv v1.44.0. Recording remaining duration is this note's recommendation, not an OTel MUST.
- Messaging semconv is **Development**; create/send/process structure may still change. Do not freeze it in a Concept as stable.
- `ProbabilitySampler` / `CompositeSampler` language-SDK completeness as of 2026-09-13: Go has experimental `sdk/trace/x`; JS ships `@opentelemetry/sampler-composite`. A cross-language GA matrix was not built.
- Collector contrib moves ~every two weeks; README defaults were taken from `main` on 2026-09-13 and may drift after v0.160.0. `pkg.go.dev` still highlighted v0.157.0 — treat module-index lag as possible.
- Envoy / Istio / Linkerd default propagation header sets were **not** re-fetched this pass. Do not claim a mesh default.
- Vendor-specific field names (Datadog / Elastic / Honeycomb / Tempo) beyond the OTel `trace_id` compatibility document — out of scope.
- Adjusted-count / `th` backend support matrix (who actually extrapolates rates) — Elastic published a 2026 how-to; a full vendor matrix was not verified.
- PromQL / TraceQL "alert on missing traces" recipes — none found that are vendor-official; excluded (same stance as C1/C2).
- Course-dump folklore ("always sample 100% in production", "baggage is just tracestate") — contradicted by the sources above.
