---
type: research
title: 'SLOs, error budgets & alerting policy — external research (2026-09-13)'
description: >-
  Source-verified research on SLI/SLO/SLA distinctions, error budgets,
  burn-rate alerting (SRE Workbook ch. 5), availability nines, OpenTelemetry
  SLI raw material, OpenSLO, and when not to set an SLO.
tags: [research, system-design-patterns, D5, slos, error-budgets, alerting]
---

# SLOs, error budgets & alerting policy — external research (2026-09-13)

> **What this is.** Evidence pass for catalog **D5** (Group D). Not a Concept.
> Primary pages fetched 2026-09-13. Paraphrase; numbers exact. Unverified
> claims live in §8 and must not be implied as fact.
>
> **Siblings.** **D1** owns signal taxonomy (RED / USE / golden-signal
> *definitions*). **D3** owns how alerts are *implemented* (PromQL, routing).
> This note owns the **policy layer**: SLI/SLO/SLA, error-budget math,
> sourced burn-rate windows. C1/C2 own breaker/retry mechanics; cited only
> for event classification (429, refusal). Existing in-tree citations — do
> not duplicate: Hidalgo [28], Mogul & Wilkes [29], Hauer et al. [30] in
> [nfr-references.md](../../../cases/data-intensive-design/nfr-references.md).

---

## 1. Scope and non-goals

**Owns.** SLI vs SLO vs SLA; error-budget math and freeze policy;
multi-window multi-burn-rate alerting (verify, do not invent); nines and
time-based vs request-yield availability; when *not* to set an SLO;
tool-neutral defaults (OpenSLO; OTel as SLI raw material); failure modes
of the SLO/alerting layer; eval / guardrail SLOs.

**Does not own.** Emitting RED/USE/golden-signal metrics (D1). Wiring
Prometheus / Cloud Monitoring (D3). RUM collection (D2). Trace–exemplar
join as a tracing topic (D4). Circuit-breaker / retry algorithms (C1/C2).

**Non-goals.** Invented SLAs. Copying Hidalgo / Mogul / Hauer prose.
Starting a skill family or writing a Concept.

---

## 2. Lineage / vocabulary

**SRE book ch. 4 *Service Level Objectives*** (Jones, Wilkes, Murphy,
Smith). https://sre.google/sre-book/service-level-objectives/ — fetched
2026-09-13. “SLA” is overloaded; the chapter splits three terms.

| Term | Definition (paraphrase) | Test |
|---|---|---|
| **SLI** | Carefully defined quantitative measure of a service aspect. Common: latency, error rate, throughput (QPS), availability as *yield* (well-formed requests that succeed), durability. | Computable from events? |
| **SLO** | Target or range for an SLI: `SLI ≤ target` or `lo ≤ SLI ≤ hi`. Chapter example: average Shakespeare search < 100 ms (100 ms labelled arbitrary). | What do we *aim* to hit? |
| **SLA** | Contract with **consequences** of meeting or missing the contained SLOs (rebate, penalty, other). | What *happens* on a miss? If nothing → SLO. |

Footnote 16: most people mean SLO when they say “SLA”; a real SLA breach
might be a court case. Google Search has no public SLA and still needs
SLIs/SLOs (reputation, ads). SRE does not typically draft SLAs.

**SRE book ch. 3 *Embracing Risk*** (Alvidrez; budget section Roth /
Quinito). https://sre.google/sre-book/embracing-risk/ — 100% is the wrong
target: a user on a 99% smartphone cannot tell 99.99% from 99.999%; each
extra nine is nonlinear (redundant compute + opportunity cost). The
availability target is both a **minimum and a maximum**. Error budget =
remaining unreliability vs the SLO; while it remains, releases proceed.

**Workbook ch. 2 *Implementing SLOs*** (Thurgood, Ferguson, with Hidalgo
and Beyer). https://sre.google/workbook/implementing-slos/ — preferred SLI
shape: **good events / total events** (0–100%). Error budget = 100% −
SLO. Example: 99.9% SLO, 3 000 000 requests / four weeks → **3 000**
allowed errors; one 1 500-error outage spends **50%**. Distinguishes
**SLI specification** (user outcome, measurement-independent) from **SLI
implementation** (logs vs probers vs in-page JS — quality / coverage /
cost differ). Start with **five or fewer** SLI *types*. General-purpose
window: **four-week rolling** (integral weeks so weekend count is
stable); weekly summaries + quarterly planning. Calendar windows match
planning but force mid-period traffic speculation.

**Workbook ch. 5 *Alerting on SLOs*** (Thurgood et al.).
https://sre.google/workbook/alerting-on-slos/ — fetched in full
2026-09-13. Primary source for burn-rate numbers. Prometheus syntax is
illustrative; the approach is framework-agnostic.

**Workbook Appendix B *Example Error Budget Policy*** (Thurgood,
2018-02-19 / approved 2018-02-20).
https://sre.google/workbook/error-budget-policy/ — budget = 1 − SLO;
99.9% → 0.1%; 1 000 000 requests / four weeks → **1 000** errors.
Changes are “roughly **70%** of our outages.” Exceeded four-week budget
→ halt all changes except P0 / security until back in SLO. One incident
**> 20%** of four-week budget → postmortem with a P0 action; one *class*
of outage > 20% over a quarter → P0 on the next quarterly plan.
May-continue-features: company-wide network, another team’s frozen dep,
out-of-scope load/pen testers, miscategorized errors with no user impact.

**SRE book Appendix A.** https://sre.google/sre-book/availability-table/
— time-based downtime, no planned downtime. Selected rows:

| Availability | / year | / month | / day |
|---|---|---|---|
| 90% | 36.5 days | 3 days | 2.4 hours |
| 99% | 3.65 days | 7.2 hours | 14.4 minutes |
| 99.9% | 8.76 hours | 43.2 minutes | 1.44 minutes |
| 99.95% | 4.38 hours | 21.6 minutes | 43.2 seconds |
| 99.99% | 52.6 minutes | 4.32 minutes | 8.64 seconds |
| 99.999% | 5.26 minutes | 25.9 seconds | 0.87 seconds |

Prefers aggregate unavailability (“X% of operations failed”) when the
service is partially up or load varies. Embracing Risk restates 99.99%
as **52.56 minutes**/year and 2.5 M req/day → **250** errors. Calculus
(below) rounds a 365-day year to **53 minutes**. Do not collapse the
three figures.

**Treynor, Dahlin, Rau, Beyer, “The Calculus of Service Availability,”**
*ACM Queue* 15(2) 2017. Google PDF fetched 2026-09-13:
https://sre.google/static/pdf/calculus_of.pdf (ACM HTML blocked).
Availability = MTTF / (MTTF + MTTR), duration as users experience it.
**Rule of the extra 9:** a service cannot outrun the intersection of its
*unique* critical dependencies; Google thumb-rule = one extra nine
(99.99% service → 99.999% deps). Count each unique dep **once**, any
depth — do not add a nine per hop. Typical **5–10** critical deps.
Worked 99.99% year: 0.01% of 525 600 min = **53 min**; five 99.999% deps
= **26 min**; **27 min** left for the service. Three complete 20-min
outages = 60 min → already over. Workbook ch. 2 independently: multiplying
independent-zone nines is deceptive (shared fate).

**Hidalgo 2020** [28], **Mogul & Wilkes HotOS 2019** [29], **Hauer et al.
NSDI 2020** [30] — already in nfr-references / cited from
[performance.md](../../../cases/data-intensive-design/performance.md).
Not re-quoted; PDFs of [29]/[30] not re-fetched (§8).

**OpenSLO v1.** https://github.com/OpenSLO/OpenSLO — `apiVersion:
openslo/v1`; kinds DataSource, SLO, SLI, AlertPolicy, AlertCondition,
AlertNotificationTarget, Service. `budgetingMethod`: **Occurrences**
(good/total counts), **Timeslices** (good slices / total slices),
**RatioTimeslices** (mean of per-slice ratios). Objective `target` ∈
`[0.0, 1.0)` (cannot be 1.0). `AlertCondition.kind` defaults to
`burnrate` (`op`, `threshold`, `lookbackWindow`, `alertAfter` default
`0m`). v2alpha is WIP. Issue #218: v1 AlertPolicy allows **one**
condition — cannot express Workbook §6 AND/OR without an extension.

---

## 3. Mechanics (Group D depth bar)

### 3.1 Signals and semantics

Workbook ratio examples: successful HTTP / total; gRPC < 100 ms / total;
undegraded / total (quality). Pipeline: freshness (records newer than a
watermark / records *accessed*); correctness (injected known-good);
coverage (processed / should-have-processed). Storage: durability =
written records later readable — the user-wanted slice may be a tiny
unavailable subset of a decade of bytes.

SRE book ch. 4 categories: serving → availability, latency, throughput;
storage → latency, availability, durability; pipelines → throughput +
e2e latency; **all** → correctness (often a data property, not an infra
SLO).

**Aggregation.** Averages hide tails. Ch. 4: typical ~50 ms, **5% of
requests 20× slower**; mean alerting is flat while p99 moves. Prefer
percentiles; do not assume normality. **Never average percentiles** —
merge histograms ([performance.md](../../../cases/data-intensive-design/performance.md)
[36]). Histogram `le` buckets approximate a latency SLI; counting slow
requests at configured thresholds is more accurate but harder to change
retroactively (Workbook).

**Denominator.** Well-formed requests only (yield). Count as *bad*:
connect fail, timeout, HTTP 5xx, gRPC UNAVAILABLE / DEADLINE_EXCEEDED
(C1 classifier). Do not count as availability failures: 4xx validation,
401/403, caller cancel. Workbook example: non-5xx = success. **Policy
errors:** golden-signals chapter allows “over the latency SLO ⇒ an
error” — that is a latency SLI as a ratio, not a second availability
SLI. **429:** Sloth getting-started (2026-09-13) uses
`code=~"(5..|429)"` — a product choice, not a Workbook MUST; C1/C2 treat
429 + `Retry-After` as accelerated-open. **LLM refusals:** HTTP 200 +
`stop_reason: "refusal"` are not availability errors (C2); they are a
quality / safety SLI candidate.

**Spec vs implementation (Workbook).** Same “homepage < 100 ms” spec:
server logs miss never-arrived requests; browser probers catch
network-path failures, miss subset-only bugs; in-page JS is closest to
the user *and* gives the telemetry service its own reliability
requirement. Move toward the user to raise quality; raise coverage to
capture more of the population.

**Golden signals (D1 owns the taxonomy).** SRE book ch. 6
https://sre.google/sre-book/monitoring-distributed-systems/ — latency,
traffic, errors, saturation. An SLO is a *target on an SLI built from
those*, not a fifth signal. Traffic/QPS is **not** an SLO you choose
(ch. 4). Saturation is usually a *leading* page (ch. 6: page when nearly
problematic), not a user-facing SLO. Separate successful-request latency
from error latency: a fast 500 must not improve a latency SLI.

### 3.2 Error-budget mechanics

`budget = (1 − SLO) × eligible events` (GCP + Workbook). Burn rate 1 =
pace that hits exactly 0 at window end. Workbook Table 5-4 (99.9% /
30-day):

| Burn rate | Error rate | Time to exhaust |
|---|---|---|
| 1 | 0.1% | 30 days |
| 2 | 0.2% | 15 days |
| 10 | 1% | 3 days |
| 1 000 | 100% | **43 minutes** |

Google prefers **yield** (successes / total) over uptime clocks for
globally distributed, partially-available services (Embracing Risk).
Consequence (Workbook footnote 8): a four-hour hole, four one-hour
holes, and a constant 0.5% drip can spend the *same* event budget and
produce different happiness. Calculus: mature SLO > 99.99% often resets
**quarterly**.

**Policy is the teeth.** Without an approved freeze policy the SLO is
“another KPI” (Workbook). Appendix B is the sourced four-week / 20% /
P0 text. Dependency-caused misses: two schools (do not freeze / freeze
anyway); Appendix B lists shared-fate exceptions. Write one down.

**Workbook Table 2-5** (SLO met/missed × toil × satisfaction): met +
low toil + high sat → raise velocity *or* step back; met + low sat →
**tighten**; missed + high sat → **loosen**; missed + high toil + low
sat → offload toil and fix the product. That is how you learn the number
is wrong — not a vendor preset.

### 3.3 Burn-rate alerting (Workbook ch. 5 — verified)

Evaluate on **precision, recall, detection time, reset time**. Iterations
1–3 are teaching failures; **6 is recommended**.

1. **Recent rate ≥ SLO (~10 min).** 99.9% → alert if 10-min rate ≥ 0.1%.
   Total-outage detection ~0.6 s; a 0.1% × 10 min spend is **0.02%** of
   the monthly budget; up to **144 alerts/day** while still meeting the
   SLO.
2. **36 h window** (= 5% of 30-day budget at 0.1%). Better precision;
   ~36 h reset after a 100% outage; expensive to compute.
3. **`for:` duration** (1 m rate > 0.1% `for: 1h`). **Not recommended.**
   A 100% outage pages after one hour — same detection as a 0.2% leak —
   and spends **140%** of the 30-day budget. A 5-min 100% spike every
   10 min never trips a 10-min `for`, yet spends **35%**. Any momentary
   in-SLO scrape resets the timer.
4. **Single burn-rate.** Example: 5% of 30-day budget in 1 h → burn
   **36**. A **35×** burn never pages but exhausts the month in
   **20.5 hours**. HTML detection-time “equations” are broken operators
   — **tables and PromQL are authoritative** (§8).
5. **Multiple burn rates.** Starting spends: **2% in 1 h** and **5% in
   6 h** page; **10% in 3 days** ticket. Table 5-6:

   | Spend | Window | Burn rate | Notify |
   |---|---|---|---|
   | 2% | 1 hour | **14.4** | Page |
   | 5% | 6 hours | **6** | Page |
   | 10% | 3 days | **1** | Ticket |

   **Arithmetic (do not invent):** 30-day = 720 h. `14.4 × 1/720 = 0.02`.
   `6 × 6/720 = 0.05`. `1 × 72/720 = 0.10`. Matches Table 5-6.

6. **Multi-window, multi-burn-rate.** AND a short window so the alert
   clears when spend *stops*. Guideline: short = **1/12** of long
   (1 h → 5 m; 6 h → 30 m; 3 d → 6 h; PromQL ticket pair 24 h → 2 h).
   Table 5-8 (starting point for a **99.9%** SLO):

   | Severity | Long | Short | Burn | Budget consumed |
   |---|---|---|---|---|
   | Page | 1 hour | 5 minutes | **14.4** | 2% |
   | Page | 6 hours | 30 minutes | **6** | 5% |
   | Ticket | 3 days | 6 hours | **1** | 10% |

   The chapter PromQL *also* tickets **3×** over 24 h AND 2 h
   (`3 × 24/720 = 10%`). Sloth emits **both** ticket pairs. Suppress
   duplicates: a 10% spend in five minutes satisfies slower windows too.

**Low traffic.** 10 req/h, one failure → 10% hourly rate = **1 000×**
burn vs 99.9% and **13.9%** of the 30-day budget; seven failures exhaust
the month. Sourced options: synthetic traffic (hides paths synthetics
miss); combine related services (hides a 100% single-binary outage);
change the product (C2 retries; store-and-forward); **lower the SLO**
(99.9% → 99%) if one ephemeral error should not page.

**Extreme SLOs.** 90% availability: Table 5-8’s “2% of budget in one
hour” **cannot fire** — a 100% outage spends only **1.4%** of a 30-day
90% budget in that hour. 99.999% monthly: 100% outage exhausts the
budget in **26 seconds**, below many scrape intervals and SMS/email.
Defending five nines is a **design** problem (canary to 1% of users →
**43 minutes** of budget at 1% burn), not a paging problem.

**Alerting at scale.** Do not invent per-microservice windows. Bucket
request classes (Table 5-10 — **examples**, not universal SLOs):

| Class | Availability | Latency @ 90% | Latency @ 99% |
|---|---|---|---|
| `CRITICAL` | 99.99% | 100 ms | 200 ms |
| `HIGH_FAST` | 99.9% | 100 ms | 200 ms |
| `HIGH_SLOW` | 99.9% | 1 000 ms | 5 000 ms |
| `LOW` | 99% | None | None |
| `NO_SLO` | None | None | None |

`NO_SLO` is sourced: dark launches and explicitly-out-of-SLO alpha.
Pages and tickets are the only valid ways to get a human (ch. 5 fn. 2).

### 3.4 Availability math and dependency SLOs

Time-based: `MTTF / (MTTF + MTTR)` (Calculus). Event-based:
`successes / total` (Embracing Risk). Nines are leftover after you decide
how unhappy users may be (Workbook: above the SLO almost all are happy;
below it they complain or leave). Calculus: most Google user-facing
services aim **99.99% internally**; some cloud services **99.999%**; many
contracts publish a *lower* external number and keep a tighter internal
SLO (ch. 4 safety margin).

**Do not overachieve.** Users build on observed reality. Chubby: SRE
synthesizes a controlled outage in any quarter that has not naturally
spent the budget (ch. 4).

**Dependencies.** Workbook: a critical dep’s SLO should be *at least* the
journey’s SLO; if not, cache / store-and-forward / degrade rather than
multiply nines. Calculus extra-9 is the Google thumb-rule for *critical*
deps; design non-critical deps *out* of the critical set.

### 3.5 When not to set an SLO

Sourced:

- **100%** — impossible; freezes change; reactive-only (Workbook).
  Calculus exceptions: antilock brakes, pacemakers — not a web SLO.
- **Copied from current performance** without a review loop (ch. 4).
  Workbook nuance: current performance is an acceptable *first* number if
  you iterate; users will come to expect whatever you actually deliver.
- **QPS / traffic as an SLO** — you do not choose incoming demand (ch. 4).
- **“User delight”** and other non-SLI attributes (ch. 4).
- **An SLO you cannot win a priority argument with** (ch. 4). Fn. 17: if
  you cannot win *any* SLO conversation, you may not need SRE for the
  product.
- **Too many.** “A handful” of indicators (ch. 4); five or fewer *types*
  (Workbook); bucket, don’t one-SLO-per-RPC (ch. 5).
- **Absolutes** (“always”, “infinite scale”) (ch. 4).
- **`NO_SLO` work** — dark launch, alpha, invisible polling (Table 5-10).
- **Paging to defend five nines** — budget is gone before the page (ch. 5).
- **Low-traffic 99.9% that pages on one ephemeral error** (ch. 5).
- **Wilkes**
  (https://sre.google/resources/practices-and-processes/measuring-reliability/):
  start from the reliability *question* (and cost of a wrong answer).
  Not every question is an SLO.

### 3.6 Eval SLOs and guardrails

Existing notes, not re-derived:

- [poc-to-production.md](../../../cases/claude-certification/enterprise-integration-production/poc-to-production.md)
  — a POC has no production latency distribution. **p95**, not the median,
  is the design target. Retry / fallback / breaker miss-rate is what an
  availability SLI will see.
- [feedback-loop.md](../../../cases/claude-certification/stakeholder-engagement/feedback-loop.md)
  — SLA = measure / breach / consequence. Thresholds trace to **UX,
  criticality, or evals**. Eval-score breach → diagnose prompt / data /
  model drift. Regulated checkpoints fire **on a schedule**, not only at
  a threshold — they are not burn-rate pages.
- [guardrails.md](../../../cases/claude-certification/responsible-ai/guardrails.md)
  — fail-open screening still *looks* healthy. Fail-closed is the sourced
  default for operator-built guardrails and **couples two SLOs**:
  guardrail availability vs product availability. Fail-closed burns the
  *product* budget on purpose; fail-open burns a **safety / quality**
  budget while availability stays green. Instrument both. Anthropic
  built-in safety is not operator-fail-open.

Eval SLI shape (Workbook applied, not a vendor MUST): good eval outcomes
/ eval runs (or sampled production traces). Do not fold a synchronous
judge into the user latency SLO unless it is on the path. Do not count
HTTP-200 refusals as availability errors. RAG retrieval precision/recall
are quality SLIs (poc-to-production).

---

## 4. Verified defaults / standards (fetch dates 2026-09-13)

The SLO is a **policy object**. OpenTelemetry is **instrumentation**.
Neither is the other.

**OpenTelemetry HTTP metrics**
(https://opentelemetry.io/docs/specs/semconv/http/http-metrics/, Status
**Mixed**). No SLO / error-budget resource. `http.server.request.duration`
Histogram, unit `s`. Advisory `ExplicitBucketBoundaries`:
`[ 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10 ]`.
Required: `http.request.method`, `url.scheme`. Conditionally required:
`http.response.status_code`, `error.type`, `http.route` (template only).
Opt-in `user_agent.synthetic.type` ∈ {`bot`, `test`} — label probes;
Workbook warns successful synthetics can *hide* real-user failures.
**Cardinality:** opting in to header-derived `server.address` /
`server.port` “may allow an attacker to trigger cardinality limits.”
Instrumentations on ≤ **v1.20.0** of this document SHOULD NOT flip
defaults until HTTP conventions are marked stable;
`OTEL_SEMCONV_STABILITY_OPT_IN=http|http/dup`. Same duration SHOULD
match the HTTP server span (D4 exemplars). A 200 ms latency SLO needs a
0.2 s boundary — **0.2 is not in the advisory list** (0.1 / 0.25 are).
Override buckets to fit the SLO, or accept 250 ms as the measurable
threshold (comparability vs fit). GenAI conventions: not fetched (§8).

**OpenSLO v1.** `target` ∈ `[0.0, 1.0)` — cannot encode 100% (matches
Workbook). Occurrences ≡ good/total; Timeslices ≡ time-based
availability. Exactly one `timeWindow` (rolling `4w` or calendar `1Q` +
IANA zone). Burn-rate `threshold` is whatever *you* put in — **14.4 / 6
are not in the spec**. `alertAfter` default `0m` — do not use it as
Workbook’s rejected `for:`. Multi-window AND is **not** in v1 (#218).
Duration-shorthand `M`/`Q`/`Y` is implementation-defined.

**Sloth** (https://sloth.dev/introduction/). Example `objective: 99.9`,
30-day metadata. Generated page alert (identifiers exact):

```
slo:sli_error:ratio_rate5m  > (14.4 * 0.0009999999999999432)  and
slo:sli_error:ratio_rate1h  > (14.4 * 0.0009999999999999432)
or
slo:sli_error:ratio_rate30m > (6 * 0.0009999999999999432)     and
slo:sli_error:ratio_rate6h  > (6 * 0.0009999999999999432)
```

Ticket: `3×` on 2 h / 1 d **or** `1×` on 6 h / 3 d. The
`0.0009999999999999432` factor is `1 − 0.999` in IEEE float — same 0.1%
budget as Table 5-8. Generated `sloth_version` label was `dev`; **no
release version claimed**. Example error query counts `5xx|429`.

**Google Cloud Monitoring** (updated **2026-09-09** UTC).
https://cloud.google.com/stackdriver/docs/solutions/slo-monitoring/alerting-on-budget-burn-rate
— `select_slo_burn_rate(SLO, LOOKBACK)`; burn 1 = sustainable rate that
exactly meets the SLO. **Different starting defaults than Table 5-8:**
fast-burn **10×** / 1–2 h lookback; slow-burn **2×** / 24 h. Cannot
alert on a compliance period **> 24 h**; approximate a 28-/30-day SLO
with a < 24 h lookback. Do not report 14.4 as “the GCP default.”

**Prometheus alerting practices.**
https://prometheus.io/docs/practices/alerting/ — page on user-visible
latency and errors as high in the stack as possible; **one** latency
page point per stack. Batch: page if not succeeded recently enough to
hurt users, generally ≥ **two full runs** (example: 4 h period, 1 h
runtime → **10 hours**). **Metamonitoring:** prefer an end-to-end
“alert was delivered” black-box over per-component causes. CamelCase
alert names. Ewaschuk “My Philosophy on Alerting” linked; body not
fetched (§8).

| Knob | Sourced starting point | Trade-off |
|---|---|---|
| SLI shape | good / total (Workbook) | 0–100% scale; awkward for gauges |
| Classes | ≤ 5 SLI types; request-class buckets | Coarse vs toil |
| Window | 4-week rolling; quarterly if SLO > 99.99% | User memory vs planning |
| Target | < 100%; not copied from current without review | Tight → freeze culture; loose → silent pain |
| Page burns (99.9% / ~30 d) | 14.4 × (1 h ∧ 5 m) and 6 × (6 h ∧ 30 m) | GCP ships 10× / 2×; retune for 90% or five-nines |
| Ticket burns | 1 × (3 d ∧ 6 h) and/or 3 × (24 h ∧ 2 h) | Long reset if you omit the short window |
| `for:` / `alertAfter` | Avoid as the SLO gate | Cheap; misses inter-window spikes |
| HTTP duration buckets | OTel advisory list (seconds) | 200 ms SLO is not on a boundary |
| 5xx vs 429 | Workbook example = 5xx; Sloth example = 5xx\|429 | 429 as availability vs overload |
| Freeze | 4-week budget exhausted → halt non-P0 (App. B) | Punishes shared-fate deps unless excepted |

---

## 5. Failure modes and when-not-to-use

**The monitoring / SLO layer can lie:**

- **Wrong SLI implementation.** Logs miss never-arrived requests;
  synthetics hide real-user paths; LB 5xx miss HTTP-200 wrong content
  (golden-signals implicit errors). SLI precision/recall ≠ alert
  precision/recall (Workbook fn. 7).
- **Event-ratio blindness to outage shape.** Same spend, different pain
  (fn. 8). [30] exists because of this.
- **Nines arithmetic on correlated deps.** Shared control planes.
  Extra-9 is a thumb-rule, not a proof.
- **Duration-clause alerts** (iteration 3) / OpenSLO `alertAfter` used
  the same way: reset on one good scrape; miss regular 100% blips.
- **Iteration-1 threshold-on-SLO:** 144 pages/day, still in SLO. Trains
  ignore (Prometheus: no page with nothing to do).
- **Low-traffic false pages / five-nines un-pageable events.**
- **Combining services** to fix low traffic: a 100% small-binary outage
  may never look “significant.”
- **Calendar reset** as a happiness discontinuity.
- **Histogram / percentile misuse.** Advisory buckets miss the SLO
  threshold; averaging percentiles [36].
- **Cardinality explosion** (OTel `server.address`; raw URI as route).
- **Shared fate of the monitor.** Metrics pipeline as a critical dep
  without an extra nine + metamonitoring → you learn from Twitter.
- **GCP 24 h lookback cap** vs a 30-day SLO: night-time over-page (GCP
  caveat).
- **OpenSLO v1 single-condition AlertPolicy** cannot express MWMB AND;
  `threshold: 14.4` without the short window reproduces iteration 4’s
  ~58-min reset.
- **Guardrail fail-open.** Availability stays green; safety should have
  burned.
- **Over-achievement / Chubby.** An unpublished extra nine becomes an
  ungoverned de-facto SLO.
- **Heroic 100%.** The last nine is lost in the laptop / Wi-Fi / ISP
  path (Calculus + Workbook).

**When not to use this machinery.** No stakeholder will enforce a freeze
(Workbook: iterate until they will, or don’t call it an error-budget
culture). No events to count (one batch run per window — use freshness /
“last success age”; page on two missed runs, not 14.4). Safety-critical
“must not fail” loops that are not request yields (Calculus exceptions).
Questions the SLI/SLO model cannot answer (Wilkes). Dark launch /
`NO_SLO`.

---

## 6. Cross-links

**Catalog.**
[system-design-patterns-catalog.md](system-design-patterns-catalog.md)
Group D: **D1** foundations / RED / USE / golden-signal *taxonomy*;
**D2** client-side / RUM as the higher-quality SLI implementation;
**D3** server-side golden signals and PromQL / Alertmanager
*implementation* of Table 5-8; **D4** traces / exemplars that explain a
burned budget. Group C: **C1**
[CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md)
· [circuit-breaker-external-research.md](circuit-breaker-external-research.md);
**C2**
[RetryBackoff.md](../../../cases/SystemDesignPatterns/RetryBackoff.md) ·
[retry-backoff-external-research.md](retry-backoff-external-research.md).

**Existing cases (cite, do not rewrite).**
[nfr-references.md](../../../cases/data-intensive-design/nfr-references.md)
[28][29][30];
[performance.md](../../../cases/data-intensive-design/performance.md)
(percentiles as SLO/SLA language);
[reliability.md](../../../cases/data-intensive-design/reliability.md)
(reliability = meeting the SLO when a *fault* is not yet a *failure*);
[nfr-overview.md](../../../cases/data-intensive-design/nfr-overview.md);
[poc-to-production.md](../../../cases/claude-certification/enterprise-integration-production/poc-to-production.md);
[feedback-loop.md](../../../cases/claude-certification/stakeholder-engagement/feedback-loop.md);
[guardrails.md](../../../cases/claude-certification/responsible-ai/guardrails.md).

---

## 7. Sources

Retrieved 2026-09-13 unless noted.

**SRE (primary).** sre.google/sre-book/service-level-objectives ·
sre.google/sre-book/embracing-risk ·
sre.google/sre-book/availability-table ·
sre.google/sre-book/monitoring-distributed-systems ·
sre.google/workbook/implementing-slos ·
sre.google/workbook/alerting-on-slos ·
sre.google/workbook/error-budget-policy ·
sre.google/static/pdf/calculus_of.pdf ·
sre.google/resources/practices-and-processes/measuring-reliability

**In-tree (do not duplicate).** nfr-references.md [28][29][30][36] ·
performance.md · reliability.md · nfr-overview.md

**Instrumentation / policy objects.**
opentelemetry.io/docs/specs/semconv/http/http-metrics ·
github.com/OpenSLO/OpenSLO (openslo/v1; issue #218) ·
sloth.dev/introduction ·
cloud.google.com/stackdriver/docs/solutions/slo-monitoring/alerting-on-budget-burn-rate
(updated 2026-09-09) · prometheus.io/docs/practices/alerting

**AI / eval notes.** poc-to-production.md · feedback-loop.md ·
guardrails.md · circuit-breaker-external-research.md ·
retry-backoff-external-research.md (429 / refusal classification)

---

## 8. Uncertain / left out

- Hidalgo 2020 chapter-level claims / numeric defaults — book not
  re-fetched; keep [28] as the pointer.
- Mogul & Wilkes [29] and Hauer et al. [30] **findings** — cited from
  existing NFR notes; PDFs not re-fetched. Do not invent their formulas.
- ACM Queue HTML of Calculus (Cloudflare block); numbers above are from
  the Google-hosted PDF only.
- Workbook ch. 5 HTML detection-time “equations” are concatenated /
  broken operators. **Tables 5-4, 5-6, 5-8 and the PromQL are
  authoritative.** Do not reconstruct a closed-form detection-time
  formula.
- 52.56 min (Embracing Risk) vs 52.6 min (Appendix A) vs 53 min
  (Calculus, 365-day 525 600 min). Same 99.99% idea; do not pick one as
  “the” minute count.
- GCE “three and a half nines / 99.95%” in SRE book ch. 4 is a
  contemporaneous published target — not checked against current GCP
  SLA pages.
- ISP background error rate “0.01% to 1%” (Embracing Risk) — as stated
  in the book; not re-measured.
- OpenSLO duration-shorthand (`M` / `Q` / `Y`) is
  implementation-defined. v2alpha contents not read.
- Sloth *release* version: page generated `sloth_version: dev`. Pyrra /
  operator defaults not fetched.
- Rob Ewaschuk “My Philosophy on Alerting” Google Doc — linked from
  Prometheus; body not fetched.
- OTel GenAI metric names / stability — not fetched; not SLO defaults.
- Whether `http.server.request.duration` is Stable after this fetch —
  page said **Mixed**.
- GCP create-policy API examples use threshold **2**, not 14.4 —
  consistent with GCP’s 2×/10× guidance, not a Workbook conflict.
- Eval-SLO numeric thresholds (e.g. “score ≥ 0.85”) — **none sourced**;
  feedback-loop.md says they come from the suite.
- PromQL in §4 is Sloth’s generated example, not a Google-published
  rule file.

Everything in this section is excluded from any future Concept.
