---
type: research
title: 'Client-side monitoring (RUM, web vitals, crash/error, mobile) — external research (2026-09-13)'
description: >-
  Source-verified D2 note: RUM vs CrUX vs lab, current Google Core Web Vitals
  (LCP/INP/CLS) definitions and p75 thresholds, JS/mobile crash and ANR
  semantics, crash-free sessions, and what OpenTelemetry JS / browser / Android
  SDKs actually emit.
tags: [research, system-design-patterns, D2, client, monitoring, rum]
---

# Client-side monitoring — external research (2026-09-13)

> Evidence pass for catalog **D2** (`d2-client-monitoring`). Not a Concept.
> **D1 owns taxonomy** — this note does not re-define “metric,” RED, USE, or
> the four golden signals. Primary pages and registries fetched 2026-09-13;
> unverified claims stay in §8. Do not re-cite latency [21]–[26], percentile
> construction [31]–[36], Hidalgo [28], Mogul/Wilkes [29], Hauer [30] from
> main-repo `cases/data-intensive-design/nfr-references.md`; “never average
> percentiles” is in `performance.md`; demo-median ≠ production p95 is in
> `cases/claude-certification/enterprise-integration-production/poc-to-production.md`.

---

## 1. Scope and non-goals

**Owns.** Browser/mobile RUM: session / page-view / navigation units; Core
Web Vitals (LCP, INP, CLS) as Google defines them on 2026-09-13; FCP /
TTFB / TBT-as-lab-proxy; JS `error` / `unhandledrejection`; mobile crash,
ANR / hang, crash-free users / sessions; OTel JS / browser / Android
versions and **what they emit**; client alerting peculiarities; failure
modes of the monitor itself.

**Does not own.** Taxonomy and golden-metric *frameworks as frameworks*
(D1). Server golden signals (D3). Trace propagation and session↔trace
joins (D4) — this note only records `session.id` and outbound fetch/XHR
spans. SLO / burn-rate math (D5). Vendor RUM pricing, session replay,
synthetic scripts. Client numbers below are *instances* of D1’s types,
not a second taxonomy.

---

## 2. Lineage / vocabulary

**RUM vs lab vs CrUX.** Google’s Web Vitals program (Walton, 2020-05-04;
vitals overview last updated 2024-10-31) splits measurement into **lab**
(Lighthouse, DevTools, WebPageTest — no real user, so **INP is not
measurable**; TBT is the documented proxy) and **field**. Field has two
populations that must not be treated as interchangeable:

| Source | Population | Window | What it can tell you |
|---|---|---|---|
| **CrUX** | Eligible *Chrome* users who opted into usage statistics; origin/page must be publicly discoverable and “sufficiently popular” | Rolling **28 days**, API ~2 days behind, PST, no DST adjustment | Whether a public URL/origin passes CWV at p75. **Not** *why*. |
| **First-party RUM** | Whoever your snippet reaches (minus consent / blockers / sampling) | Whatever you store | Attribution: which element, which interaction, which navigation, which session |
| **Lab** | Scripted device + network | One load | Regressions before ship; cannot stand in for field INP or lifespan CLS |

CrUX is “the Google dataset of the Web Vitals program” and feeds Search;
Google “strongly recommend[s]” first-party RUM for diagnosis. Trade-off:
CrUX is free and unbiased *within Chrome-consenting users*, blind to
Safari/Firefox and low-traffic URLs. RUM sees those and is biased by
whoever did not load the script.

**CWV lifecycle.** Experimental → pending (≥ 6 months) → stable. Vitals
page 2024-10-31: LCP, CLS, INP are **stable**. INP replaced FID
**2024-03-12**; Chrome dropped FID **2024-09-09**. `web-vitals` v5
removed `onFID`.

**Session — three incompatible units.** Crashlytics (2026-09-11): cold
start or foreground after ≥ **30 min** background; user = one install.
OTel browser-sdk 0.4.0 example: `maxDuration` **4 h**,
`inactivityTimeout` **30 min**, `LocalStorage`, stamps `session.id`.
Android vitals (2026-08-26): usage in a **24 h** window from midnight
**PT**. Play’s own clash: one user, three plays, one crash → vitals
**100%** (DAU) vs Crashlytics **33%** (session). Denominator join is D5;
the fact is D2.

**Error classes (client).** Fatal process death (crash / native signal);
ANR / hang (UI thread unresponsive, process often still alive); non-fatal
caught exception / JS `error` / `unhandledrejection`. Crash-free *metrics*
in Crashlytics count **only fatals** (plus Unity/Flutter uncaught-as-fatal).
Filtering the console to ANR or non-fatal **blanks** the crash-free charts.

---

## 3. Mechanics (Group D depth bar)

### 3.1 Signals and semantics — Core Web Vitals (verified 2026-09-13)

Official Search Central and web.dev still publish the same “good” targets
that have been stable since INP’s promotion. **No official 2026 threshold
change was found on Google properties** (a third-party claim of LCP ≤ 2.0 s
from March 2026 is §8).

| Vital | Facet | Good | Needs improvement | Poor | Aggregation |
|---|---|---|---|---|---|
| **LCP** | Loading | ≤ 2.5 s | ≤ 4 s | > 4 s | p75 of page loads, **mobile and desktop separately** |
| **INP** | Interactivity | ≤ 200 ms | ≤ 500 ms | > 500 ms | same |
| **CLS** | Visual stability | ≤ 0.1 | ≤ 0.25 | > 0.25 | same |

A page/origin **passes** CWV only if **all three** meet “good” at p75
(vitals article; Search Console Help table). Thresholds are **not** split
by device even though reporting is — achievability was set from mobile
(defining-thresholds article, updated 2025-05-07). p75 was chosen as the
compromise between “most visits” (3 of 4) and outlier-resistance (25 of 100
samples must be extreme before p75 moves; p95 moves after 5).

**LCP** (Walton/Pollard, 2025-09-04). Render time of the largest viewport
image / text / video vs navigation start (prerender: `activationStart`).
Candidates: `<img>`, `<image>` in `<svg>`, `<video>` (poster or first
frame, earlier wins), `background-image: url()`, block text. Chromium
excludes opacity 0, full-viewport backgrounds, low-entropy placeholders.
Size = visible intersection; images min(visible, intrinsic); no CSS
box. Successive `largest-contentful-paint` entries — **report the last**;
stops on tap/scroll/key. **Includes unload, connect, redirect, TTFB**
(lab-vs-field gap). API≠metric: drop background-tab loads; treat bfcache
as a new visit; include iframe LCP (JS cannot see cross-origin iframes —
CrUX can). Chrome **133** exposes coarsened render time without
`Timing-Allow-Origin`.

**INP** (Wagner/Pollard, 2025-09-02). Replaced FID. Click / tap / key only
(not hover, zoom, or scroll). Latency = input delay + handlers +
presentation delay → **next paint**. Page value = longest interaction,
**ignoring one highest per 50**. Event Timing default threshold **104 ms**
(floor 16 ms); also observe `first-input`. Finalize on
`visibilitychange`. A page may have **no INP** (scroll-only, bots).

**CLS** (session-window definition, current on fetch). **Not** the old
lifetime sum. A window is unexpected `layout-shift`s with **< 1 s**
between shifts and **≤ 5 s** total; CLS = **worst** window.
`score = impact fraction × distance fraction`. Discrete input within
**500 ms** sets `hadRecentInput` (excluded); scroll/drag/pinch do not.
`transform` does not shift; `top`/`width` can. Lab CLS is load-only and
under-reports field CLS.

**Soft navs / transport.** `web-vitals` **6.2.1** (npm 2026-08-26): Chrome
**151+**, `reportSoftNavs: true` (interaction + URL change + a paint).
After a soft nav: TTFB = **0**; FCP/LCP ignore leftover un-repainted
elements; INP/CLS reset. CrUX still scores hard navigations — enabling
the flag **diverges** first-party RUM. Google’s snippet:
`sendBeacon` with `fetch(..., {keepalive: true})` fallback.

### 3.2 Signals and semantics — JS errors

Browser: `window` `error` (uncaught sync) and `unhandledrejection`. OTel
`ErrorsInstrumentation` (browser-instrumentation 0.8.1) emits an
**`exception` event** with `exception.type` / `.message` / `.stacktrace`
(type and stack omitted when the thrown value is a string). This is
**not** a crash: the tab usually survives. Do not fold JS exceptions into
a crash-free-session denominator.

### 3.3 Signals and semantics — mobile crash, ANR, hang

**Android ANR** (2026-08-18). Triggers: input dispatch **5 s** (the only
type Play calls **user-perceived**); service create/start/bind “a few
seconds”; `startForeground` not called within **5 s**; broadcast overtime
(**5 s** if an activity is foreground); JobService overtime (silent
targetSdk ≤ 33, explicit on 34+). Play rates are **% of daily active
users**. Bad-behavior floors (vitals 2026-08-26): user-perceived ANR
**0.47% overall / 8% per phone / 5% per watch**; user-perceived crash
**1.09% / 8% / 4%**. Window = **28 days**; “emerging” if a device-level
problem lasts **> 7 days**. 3P SDKs cannot report ANRs on Android **≤10**;
Crashlytics uses `getHistoricalProcessExitReasons` (**11+** only) and
sends **on next start** — why Play and Crashlytics ANR counts disagree.

**Crashlytics crash-free** (docs updated 2026-09-11). Minimum SDKs: Apple
**10.8.0+**, Android **18.6.0+** (BoM **32.6.0+**), Flutter **3.4.5+**,
Unity **11.7.0+**.

```
CRASH_FREE_USERS    = 1 − (CRASHED_USERS    / ALL_USERS)
CRASH_FREE_SESSIONS = 1 − (CRASHED_SESSIONS / ALL_SESSIONS)
```

Aggregation over the selected window, **not** an average of daily
percentages. Crash-free **users** shrink as the window lengthens (same
user more likely to have crashed sometime). Crashlytics says explicitly:
**do not compare crash-free users across different time periods.**
Opt-in-only collection and `sendUnsentReports` (crashes without session
pings) make the charts **optimistic or ~0** — a monitoring failure mode,
not an app-quality signal.

**iOS counterpart.** Not called ANR. MetricKit / Xcode Organizer: **hang
rate** = seconds/hour the app is unresponsive, counting periods **> 250
ms**; hang *reports* (stack samples) when the main thread is unresponsive
**≥ 1 s**. Watchdog terminations (`0x8badf00d`) are **crashes**, not
hangs; Apple’s scene-create example allowance is **19.97 s** (an example
in the crash report, not a published universal constant — §8). WWDC26
session 222 claims iOS **27** MetricKit diagnostics (crash/hang) are
delivered **immediately** to the app; older guidance was ~24 h delay.

### 3.4 Golden-metric frameworks (client instances, D1 owns the frameworks)

Do not invent a fourth framework. Map client signals onto D1’s existing
ones:

| D1 framework | Client instantiation |
|---|---|
| Four golden signals / RED | **Traffic** = navigations / sessions / soft-navs; **Errors** = JS `exception` rate, fatal crash rate, user-perceived ANR rate; **Duration** = LCP / INP / TTFB (distributions, not averages — `performance.md`) |
| USE | Device CPU / memory / slow+frozen frames (`app.jank`), wake locks — mostly Play vitals / MetricKit, not first-party RUM |
| Google Web Vitals | The **page-experience** golden set: LCP + INP + CLS at p75 |
| Android vitals | The **store-visibility** golden set: user-perceived crash + user-perceived ANR (+ battery / memory; memory thresholds gain Play visibility impact **February 2027**) |

Trade-off: Web Vitals and Android vitals are *externally enforced* (Search
/ Play). They are excellent **symptoms** and poor **causes**. First-party
RUM exists to attribute the symptom.

### 3.5 OpenTelemetry — versions and what they actually emit

Two JS stacks coexist and **do not emit the same signals**.

**Legacy web traces** (`opentelemetry-js` / `js-contrib`, npm 2026-09-13):
`@opentelemetry/sdk-trace-web` **2.10.0** (2026-07-21); 
`instrumentation-document-load` **0.66.0** (2026-07-23) emits
`documentLoad` / `documentFetch` / `resourceFetch` **spans** (stable
semconv v1.23.0+ since 0.65.0); `auto-instrumentations-web` **0.66.0**
bundles those plus fetch, user-interaction, and XHR spans. **No CWV, no
JS exceptions, no sessions.** Pre-2024 tutorials wrapping `onFID` as
spans are not this stack.

**New browser SDK** (`opentelemetry-browser`): `browser-sdk` **0.4.0**
and `browser-instrumentation` **0.8.1** (both npm 2026-09-09; latter
depends on `web-vitals` ^6.2.1). README: logs + traces;
**“Metrics are out of the scope for now.”** Experimental. Default OTLP
`http://localhost:4318`. 0.8.1 emits: `browser.navigation` (hard load +
`pushState`/`replaceState`/`popstate`/hash; attrs `url.full`,
`browser.navigation.{same_document,hash_change,type}` =
`push|replace|reload|traverse`); **`browser.web_vital`** log records
(semconv Development) with required
`browser.web_vital.{name,value,delta,id}`, recommended
`{navigation_type,rating}`; well-known names `cls|fcp|inp|lcp|ttfb`
(**no `fid`** on today’s spec page); `includeRawAttribution` default
**false**; `exception` (uncaught `error` + `unhandledrejection`);
`browser.console`; fetch/XHR **spans**
(`http.request.method`, `url.full`, `http.response.status_code`,
`error.type`; CORS `traceparent` via `propagateTraceHeaderCorsUrls` —
D4). Session helper: 4 h max / 30 min idle; processors **before**
exporters so `session.id` is set.

**Android** GitHub **v1.7.0** (2026-09-04); docs BOM
`opentelemetry-android-bom:1.7.0`. Java Instrumentation **2.31.1** /
Java **1.65.0**. Agent API stable since 1.0.0; **instrumentation remains
alpha**. v1.3.0 raised min API **21 → 23** (docs page still says 21 —
§8). Example session: `backgroundInactivityTimeout = 15.minutes`,
`maxLifetime = 4.days` (not Crashlytics 30 min). Offline disk buffer
on. Slow frames **> 16 ms**, frozen **> 700 ms**. Emits: **`app.crash`**
event (was `device.crash` until 1.5.0) with
`exception.{message,stacktrace,type}`, `thread.{id,name}`, stacks
truncated **1 000** lines, flush-before-previous-handler in 1.7.0;
opt-in **native** `app.crash` on **next launch** (1.6.0); **`device.anr`**
event (README — **not** a span): poll UI thread every **1 s**, emit
after **5** consecutive misses, foreground only, ERROR,
`exception.stacktrace` = main-thread dump; `app.jank`; Compose
`app.navigation.complete` (1.7.0); `app.screen.click` /
`app.widget.click`. Semconv allows a later process to report a prior
crash from tombstones; then `os.name` / `os.version` /
`service.version` / `app.build_id` are conditionally required.
`session.id` Recommended. Dedup is **not** required.

**iOS / Swift.** Releases search shows **2.5.1**; crash/hang emit list
**not verified** from a README (§8). Use Apple MetricKit.

### 3.6 Alerting policy (client-shaped; burn-rate math is D5)

Alert on **field p75** or Play’s **28-day DAU** rate — never a single
pageview or a Lighthouse score (lab INP does not exist). Symptoms first:
CWV fail, Play crash/ANR crossing **1.09% / 0.47%**, Crashlytics
crash-free **sessions** on a *fixed* post-release window — then slice by
URL / LCP element / INP target / device. Do not alert crash-free
*users* across unequal windows (Crashlytics explicit) or mix DAU with
session rates. JS `exception` volume is not availability. Consent and
sample-rate changes are deploys. A RUM-volume drop with stable server
traffic is a **monitor** outage. Trade-off vs D3: client series are
sparse, consent-biased, and finalized late — tight “N of M minutes”
burns mis-fire. Use Play/CrUX 28-day courts for external risk; first-party
RUM for attribution.

### 3.7 Tool-neutral defaults (not vendor SLAs)

`web-vitals` **6.2.1** (`onLCP`/`onINP`/`onCLS`; attribution +~1.5 kB
brotli; `reportAllChanges` **false** in production). Soft navs **off**
unless opted in (Chrome 151+; diverges from CrUX). Beacon =
`sendBeacon` / `fetch`+`keepalive`. New browser OTel for vitals+errors
as **events**; legacy auto-web 0.66.0 for **spans only**; no OTLP
metrics on browser-sdk 0.4.0. Session idle **30 min** (Crashlytics +
browser-sdk example). Android BOM **1.7.0**, ANR/crash on, sample if
battery hurts. OTel ANR = 1 s × 5 foreground poll ≠ Play input-dispatch.
Crash-free **sessions** for release health, **users** for habit-forming
apps. Play 1.09% / 0.47% are **discoverability** floors, not UX targets.

---

## 4. Verified defaults / standards (versions + fetch dates)

All fetched **2026-09-13**. CWV articles: vitals 2024-10-31, LCP 2025-09-04, INP 2025-09-02, thresholds 2025-05-07; Search Central still LCP 2.5 s / INP 200 ms / CLS 0.1; INP replaced FID **2024-03-12**; Chrome dropped FID **2024-09-09**. Libraries: `web-vitals` **6.2.1** (2026-08-26); `@opentelemetry/sdk-trace-web` **2.10.0** (2026-07-21); `auto-instrumentations-web` **0.66.0** (2026-07-23); `browser-sdk` **0.4.0** and `browser-instrumentation` **0.8.1** (both 2026-09-09); Android agent **1.7.0** (2026-09-04). Crashlytics crash-free docs **2026-09-11**; Android ANR **2026-08-18**; Android vitals **2026-08-26**. Semconv `browser.web_vital` / `app.crash` / `app.jank` are **Development**. CrUX API: 28-day rolling, ~2-day lag, PST.

---

## 5. Failure modes and when-not-to-use

**Failure modes of the monitor itself.** Population bias (CrUX = Chrome +
consent + popularity; RUM = script survivors; Crashlytics opt-in =
optimistic crash-free; Play = certified + Play-installed + consent +
k-anonymized). Denominator clash (Play DAU vs Crashlytics 30 min vs OTel
15 min / 4 h / 4 day — Play’s own 100% vs 33% example). Finalization
delay (INP/CLS need `visibilitychange`; mobile often skips unload).
Beacon loss (process kill, radio, CSP, ad blockers on `/analytics` and
OTLP `/v1/logs`) — volume drop ≠ quality. Iframe gap (CrUX includes
cross-origin iframes; in-page JS cannot). Background-tab LCP / forgotten
bfcache reset. Soft-nav flag diverges from CrUX. ANR holes (no 3P ANR on
Android ≤10; Crashlytics 11+ next-start only; OTel is a foreground
1 s × 5 poll, not Play input-dispatch). Next-process crash reports steal
the survivor’s resource unless `session.id` / `app.build_id` are copied
(1.7.0 native fix). Self-instrumentation (console hook, fetch wrap, ANR
poll) consumes the main thread it measures. Cardinality of raw
`url.full`. Stale names (FID, `device.crash`, “ANR spans”). Collector
429/R8-stripped agent looks like a perfect day — pair RUM volume with
server traffic (D3).

**When not to use.** Lighthouse/TBT as a production INP SLO. Crash-free
*users* as a week-over-week KPI. JS exceptions as crashes, ANRs as
crashes. A RUM vendor to *define* CWV (`web-vitals` already matches
Google). `auto-instrumentations-web` for LCP/INP/CLS (it does not emit
them). `browser-sdk` 0.4.0 for OTLP **metrics** (out of scope). Skipping
first-party RUM because CrUX is green (no attribution; low-traffic URLs
absent). Lab is enough only for pre-merge LCP/CLS/TBT on a known
template.

---

## 6. Cross-links

| Id | Relation |
|---|---|
| **D1** | Taxonomy owner. RED/USE/golden-signals definitions live there; §3.4 only instantiates them on the client. |
| **D3** | Server golden signals. Pair RUM volume vs server request rate as a monitor-liveness check. Do not double-count fetch spans here and HTTP RED there without a join key. |
| **D4** | Session/trace correlation. This note records `session.id` processors and fetch/XHR `traceparent`; D4 owns propagation, tail sampling, and the join. |
| **D5** | SLOs for user-facing. p75 CWV and Play 28-day DAU rates are *candidate SLIs*; burn-rate, error budget, and paging policy are D5. |
| Catalog | [`system-design-patterns-catalog.md`](system-design-patterns-catalog.md) Group D. |
| Main repo | [`nfr-references.md`](/Users/rajnishkhatri/Code/LLM-DRIVEN-MOBILE-TEST-AUTOMATION/cases/data-intensive-design/nfr-references.md) [21]–[36], [28]–[30]; [`performance.md`](/Users/rajnishkhatri/Code/LLM-DRIVEN-MOBILE-TEST-AUTOMATION/cases/data-intensive-design/performance.md) (percentiles, tail amplification [27]); [`poc-to-production.md`](/Users/rajnishkhatri/Code/LLM-DRIVEN-MOBILE-TEST-AUTOMATION/cases/claude-certification/enterprise-integration-production/poc-to-production.md) (demo median ≠ production p95; reliability controls belong in the stack before the first incident). |

---

## 7. Sources

**Web Vitals / Search.** web.dev/articles/{vitals (2024-10-31), lcp
(2025-09-04), inp (2025-09-02), cls, defining-core-web-vitals-thresholds
(2025-05-07)} · developers.google.com/search/docs/appearance/core-web-vitals ·
support.google.com/webmasters/answer/9205520 ·
developers.google.com/search/blog/2023/05/introducing-inp (INP
2024-03-12) · web.dev/blog/{inp-cwv-launch, fid (2024-09-09)} ·
npmjs.com/package/web-vitals (6.2.1) ·
developer.chrome.com/docs/crux{/methodology,/api}

**Mobile.** developer.android.com/topic/performance/vitals{/anr}
(2026-08) · support.google.com/googleplay/android-developer/answer/9844486 ·
firebase.google.com/docs/crashlytics/{crash-free-metrics (2026-09-11),
troubleshooting, debug-anr-errors} ·
developer.apple.com/documentation/{xcode/addressing-watchdog-terminations,
metrickit/mxhangdiagnostic} · developer.apple.com/videos/play/wwdc2026/222

**OpenTelemetry.** opentelemetry.io/docs/languages/js/getting-started/browser ·
npmjs.com/package/@opentelemetry/{sdk-trace-web (2.10.0),
instrumentation-document-load (0.66.0), auto-instrumentations-web
(0.66.0), browser-sdk (0.4.0), browser-instrumentation (0.8.1)} ·
opentelemetry.io/docs/specs/semconv/{browser/browser-events,
app/app-events} · opentelemetry.io/docs/platforms/client-apps/android ·
github.com/open-telemetry/opentelemetry-android/{releases (v1.7.0),
tree/main/instrumentation/{anr,crash}}

**Existing tree.** nfr-references.md [21]–[36], [28]–[30] · performance.md ·
poc-to-production.md · system-design-patterns-catalog.md Group D

---

## 8. Uncertain / left out

1. **LCP “good” = 2.0 s from March 2026** — third-party SEO post;
   contradicted by Search Central / Search Console / web.dev fetched
   today (still 2.5 s / 4 s). Not used.
2. Official `opentelemetry.io` Android landing still says ANR **spans**
   and min SDK **21**; instrumentation README + Releases say **events**
   and min SDK **23** since 1.3.0. This note follows README + Releases.
3. Whether `device.anr` was renamed under the 1.5.0 experimental-semconv
   flag (crash → `app.crash`) — not confirmed; name kept as `device.anr`.
4. npm `browser-sdk` jumped 0.1.0 → 0.3.0 → 0.4.0; GitHub tagged 0.2.0
   (2026-07-29) but npm has no 0.2.0.
5. `browser.web_vital` **body map vs attributes** — today’s spec page
   lists attributes; older YAML used a map body. 0.8.1 emits attributes
   (`includeRawAttribution` sets body). Semconv is Development.
6. `web-vitals` 6.x `includeProcessedEventEntries` default — secondary
   article only; not asserted.
7. iOS OTel Swift **2.5.1** seen in Releases search; **crash/hang emit
   list not verified** from a README. Issue #990 is research, not a ship
   note. MetricKit is the cited iOS source.
8. Watchdog **19.97 s** / **15 s** are crash-report *examples*, not a
   published default table.
9. CrUX “sufficiently popular” numeric cutoff — not on the methodology
   page fetched.
10. Play memory / DEX visibility impact **February 2027** — on the vitals
    page; recorded as a date, not a D2 default.
11. No vendor PromQL / RUM-alert cookbook treated as a standard.
12. W3C Reporting API / Crash Reporting support matrix — not fetched.
13. Session-replay and GDPR implementation — out of scope; consent is
    noted only as denominator bias.
