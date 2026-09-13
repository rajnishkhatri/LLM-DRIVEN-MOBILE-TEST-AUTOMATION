---
type: reference
title: 'Client-side monitoring (RUM, web vitals, crash & error reporting, mobile)'
description: 'Observe what happens on the user device: RUM and Core Web Vitals, JS exceptions, mobile crash / ANR / hang. Distinct from D1 taxonomy, D3 server golden signals, D4 trace joins, and D5 burn-rate math. Covers CrUX vs first-party RUM vs lab, session-unit clash, verified CWV and Play floors, what OTel JS / browser / Android actually emit, client alerting, and failure modes of the monitor itself.'
tags: [system-design-patterns, observability, rum, web-vitals, crash-reporting]
---

# Client-side monitoring

**See also:** [describing performance](../data-intensive-design/performance.md) · [reliability](../data-intensive-design/reliability.md) · [NFR references](../data-intensive-design/nfr-references.md) · [POC-to-production reliability](../claude-certification/enterprise-integration-production/poc-to-production.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/d2-client-monitoring-external-research.md)

Server metrics tell you the *backend* survived. Client-side monitoring tells you whether the *user device* did: the page painted, the tap painted, the process stayed alive. A 200 from checkout and a frozen main thread are compatible facts. This pattern is first-party observation of browser and mobile experience — RUM, Core Web Vitals, JavaScript exceptions, crash, ANR, hang — so a release that is green on the server can still be red where the user sits.

It is **not** a capacity control. A RUM snippet does not shed load ([C10](LoadShedding.md)), trip a breaker ([C1](CircuitBreaker.md)), isolate a pool ([C8](Bulkhead.md)), or flip a kill switch ([C11](GracefulDegradation.md)). Those *act*. This card *sees*. Quality attributes: **observability of user-perceived experience**, **detectability** of faults that never become a server 5xx, and **release-health comparability** when the denominator is honest. The costs are population bias, late-finalizing signals, and a monitor that can look healthy while it is the thing that is down.

Sibling ownership (catalog Group D): **D1** owns the taxonomy (metric, RED, USE, four golden signals) — this note only *instantiates* those types on the client. **D3** owns server golden signals; pair RUM *volume* with server request rate as a monitor-liveness check, and do not double-count fetch spans here and HTTP RED there without a join key. **D4** owns session↔trace correlation; this note only records that `session.id` and outbound `traceparent` exist. **D5** owns SLO / burn-rate / paging math; p75 CWV and Play 28-day DAU rates are *candidate SLIs*, not a paging policy.

## Lineage and vocabulary

- **Walton / Google Web Vitals (2020-05-04; vitals overview 2024-10-31)** split measurement into **lab** (Lighthouse, DevTools, WebPageTest — no real user, so **INP is not measurable**; TBT is the documented proxy) and **field**. Field has two populations that must not be treated as interchangeable.

| Source | Population | Window | What it can tell you |
|---|---|---|---|
| **CrUX** | Eligible *Chrome* users who opted into usage statistics; origin/page must be publicly discoverable and “sufficiently popular” | Rolling **28 days**, API ~2 days behind, PST, no DST adjustment | Whether a public URL/origin **passes** CWV at p75. **Not** *why*. |
| **First-party RUM** | Whoever your snippet reaches (minus consent / blockers / sampling) | Whatever you store | Attribution: which element, which interaction, which navigation, which session |
| **Lab** | Scripted device + network | One load | Regressions before ship; cannot stand in for field INP or lifespan CLS |

CrUX is the Google dataset of the Web Vitals program and feeds Search. Google “strongly recommend[s]” first-party RUM for diagnosis. Trade-off: CrUX is free and unbiased *within Chrome-consenting users*, blind to Safari/Firefox and low-traffic URLs. RUM sees those and is biased by whoever did not load the script.

- **CWV lifecycle.** Experimental → pending (≥ 6 months) → stable. As of the 2024-10-31 vitals page, LCP, CLS, and INP are **stable**. INP replaced FID **2024-03-12**; Chrome dropped FID **2024-09-09**. `web-vitals` v5 removed `onFID`.
- **Session — three incompatible units.** Crashlytics (2026-09-11): cold start or foreground after ≥ **30 min** background; user = one install. OTel browser-sdk 0.4.0 example: `maxDuration` **4 h**, `inactivityTimeout` **30 min**, `LocalStorage`, stamps `session.id`. Android vitals (2026-08-26): usage in a **24 h** window from midnight **PT**. Play’s own clash: one user, three plays, one crash → vitals **100%** (DAU) vs Crashlytics **33%** (session). Denominator join is D5; the fact is D2.
- **Error classes (client).** Fatal process death (crash / native signal); ANR / hang (UI thread unresponsive, process often still alive); non-fatal caught exception / JS `error` / `unhandledrejection`. Crashlytics crash-free metrics count **only fatals** (plus Unity/Flutter uncaught-as-fatal). Filtering the console to ANR or non-fatal **blanks** the crash-free charts.

Percentile construction stays in [performance.md](../data-intensive-design/performance.md) — never average p75s. Demo-median ≠ production p95 stays in [poc-to-production](../claude-certification/enterprise-integration-production/poc-to-production.md).

## Core Web Vitals

Official Search Central and web.dev still publish the same “good” targets that have been stable since INP’s promotion. **No official 2026 threshold change** was found on Google properties (a third-party “LCP ≤ 2.0 s from March 2026” claim is left out of the [research note](../../docs/research/sysdesign/d2-client-monitoring-external-research.md) §8).

| Vital | Facet | Good | Needs improvement | Poor | Aggregation |
|---|---|---|---|---|---|
| **LCP** | Loading | ≤ 2.5 s | ≤ 4 s | > 4 s | p75 of page loads, **mobile and desktop separately** |
| **INP** | Interactivity | ≤ 200 ms | ≤ 500 ms | > 500 ms | same |
| **CLS** | Visual stability | ≤ 0.1 | ≤ 0.25 | > 0.25 | same |

A page/origin **passes** CWV only if **all three** meet “good” at p75. Thresholds are **not** split by device even though reporting is — achievability was set from mobile. p75 is the compromise between “most visits” (3 of 4) and outlier-resistance (25 of 100 samples must be extreme before p75 moves; p95 moves after 5).

**LCP.** Render time of the largest viewport image / text / video vs navigation start (prerender: `activationStart`). Candidates: `<img>`, `<image>` in `<svg>`, `<video>` (poster or first frame, earlier wins), `background-image: url()`, block text. Chromium excludes opacity 0, full-viewport backgrounds, low-entropy placeholders. Size = visible intersection; images min(visible, intrinsic). Successive `largest-contentful-paint` entries — **report the last**; stops on tap/scroll/key. **Includes unload, connect, redirect, TTFB** (the usual lab-vs-field gap). API ≠ metric: drop background-tab loads; treat bfcache as a new visit; include iframe LCP (in-page JS cannot see cross-origin iframes — CrUX can). Chrome **133** exposes coarsened render time without `Timing-Allow-Origin`.

**INP.** Replaced FID. Click / tap / key only (not hover, zoom, or scroll). Latency = input delay + handlers + presentation delay → **next paint**. Page value = longest interaction, **ignoring one highest per 50**. Event Timing default threshold **104 ms** (floor 16 ms). Finalize on `visibilitychange`. A page may have **no INP** (scroll-only, bots).

**CLS** is the **worst session window**, not a lifetime sum: unexpected `layout-shift`s with **< 1 s** between shifts and **≤ 5 s** total. `score = impact fraction × distance fraction`. Discrete input within **500 ms** sets `hadRecentInput` (excluded); scroll/drag/pinch do not. `transform` does not shift; `top`/`width` can. Lab CLS is load-only and under-reports field CLS.

**Supporting lab/field signals (not CWV).** FCP is first paint of content — useful for “did anything appear,” not a pass/fail court. TTFB is in LCP’s critical path (unload + connect + redirect + first byte) and is the usual reason lab LCP looks faster than field. TBT is the **lab proxy for INP**; it is not measurable as INP in Lighthouse, and it must not be the production SLI. A page may have **no INP** at all (scroll-only, bots) — do not treat a missing INP as a perfect score.

**Soft navs / transport.** `web-vitals` **6.2.1** (npm 2026-08-26): Chrome **151+**, `reportSoftNavs: true` (interaction + URL change + a paint). After a soft nav: TTFB = **0**; FCP/LCP ignore leftover un-repainted elements; INP/CLS reset. CrUX still scores hard navigations — enabling the flag **diverges** first-party RUM from Search. Google’s snippet: `sendBeacon` with `fetch(..., {keepalive: true})` fallback. Finalize INP/CLS on `visibilitychange`; mobile often skips unload, so a keepalive beacon is the transport, not a `beforeunload` XHR.

## JavaScript errors are not crashes

Browser: `window` `error` (uncaught sync) and `unhandledrejection`. OTel `ErrorsInstrumentation` (browser-instrumentation 0.8.1) emits an **`exception` event** with `exception.type` / `.message` / `.stacktrace` (type and stack omitted when the thrown value is a string). The tab usually survives. Do not fold JS exceptions into a crash-free-session denominator. JS `exception` volume is not availability.

## Mobile crash, ANR, hang

**Android ANR** (docs 2026-08-18). Triggers: input dispatch **5 s** (the only type Play calls **user-perceived**); service create/start/bind “a few seconds”; `startForeground` not called within **5 s**; broadcast overtime (**5 s** if an activity is foreground); JobService overtime (silent targetSdk ≤ 33, explicit on 34+). Play rates are **% of daily active users**. Bad-behavior floors (vitals 2026-08-26): user-perceived ANR **0.47% overall / 8% per phone / 5% per watch**; user-perceived crash **1.09% / 8% / 4%**. Window = **28 days**; “emerging” if a device-level problem lasts **> 7 days**. These are **Play discoverability floors**, not UX targets. 3P SDKs cannot report ANRs on Android **≤10**; Crashlytics uses `getHistoricalProcessExitReasons` (**11+** only) and sends **on next start** — why Play and Crashlytics ANR counts disagree.

**Crashlytics crash-free** (docs 2026-09-11). Minimum SDKs: Apple **10.8.0+**, Android **18.6.0+** (BoM **32.6.0+**), Flutter **3.4.5+**, Unity **11.7.0+**.

```
CRASH_FREE_USERS    = 1 − (CRASHED_USERS    / ALL_USERS)
CRASH_FREE_SESSIONS = 1 − (CRASHED_SESSIONS / ALL_SESSIONS)
```

Aggregation is over the selected window, **not** an average of daily percentages. Crash-free **users** shrink as the window lengthens (the same user is more likely to have crashed sometime). Crashlytics is explicit: **do not compare crash-free users across different time periods.** Opt-in-only collection and `sendUnsentReports` (crashes without session pings) make the charts **optimistic or ~0** — a monitoring failure mode, not an app-quality signal. Prefer crash-free **sessions** for release health; **users** for habit-forming apps, on a *fixed* window.

**iOS counterpart** is not called ANR. MetricKit / Xcode Organizer: **hang rate** = seconds/hour the app is unresponsive, counting periods **> 250 ms**; hang *reports* (stack samples) when the main thread is unresponsive **≥ 1 s**. Watchdog terminations (`0x8badf00d`) are **crashes**, not hangs. Scene-create time allowances printed in crash reports are examples, not a published universal constant — do not promote them to a fleet SLO. WWDC26 session 222 claims iOS **27** MetricKit diagnostics (crash/hang) are delivered **immediately**; older guidance was ~24 h delay. iOS OpenTelemetry Swift **2.5.1** was seen in a Releases search; the crash/hang emit list was **not verified** from a README. Use MetricKit.

Three series, never one:

| Class | Process | Counts toward crash-free? | Typical delay |
|---|---|---|---|
| Fatal crash / native signal / watchdog | Dead | Yes (Crashlytics fatals) | Next launch (native); MetricKit was ~24 h, claimed immediate on iOS 27 |
| ANR / hang | Often still alive | **No** — filtering to ANR blanks the crash-free charts | Play vs Crashlytics disagree; OTel ANR is a different detector |
| JS `exception` / caught non-fatal | Tab/app usually survives | **No** | Immediate if the beacon lands |

## Golden-metric frameworks (client instances)

Do not invent a fourth framework. Map client signals onto D1’s existing ones:

| D1 framework | Client instantiation |
|---|---|
| Four golden signals / RED | **Traffic** = navigations / sessions / soft-navs; **Errors** = JS `exception` rate, fatal crash rate, user-perceived ANR rate; **Duration** = LCP / INP / TTFB (distributions, not averages) |
| USE | Device CPU / memory / slow+frozen frames (`app.jank`), wake locks — mostly Play vitals / MetricKit, not first-party RUM |
| Google Web Vitals | The **page-experience** golden set: LCP + INP + CLS at p75 |
| Android vitals | The **store-visibility** golden set: user-perceived crash + user-perceived ANR |

Web Vitals and Android vitals are *externally enforced* (Search / Play). They are excellent **symptoms** and poor **causes**. First-party RUM exists to attribute the symptom.

## OpenTelemetry — two JS stacks, one Android agent

Two JS stacks coexist and **do not emit the same signals**. Versions fetched 2026-09-13.

**Legacy web traces** (`opentelemetry-js` / `js-contrib`): `@opentelemetry/sdk-trace-web` **2.10.0** (2026-07-21); `instrumentation-document-load` **0.66.0** (2026-07-23) emits `documentLoad` / `documentFetch` / `resourceFetch` **spans** (stable semconv v1.23.0+ since 0.65.0); `auto-instrumentations-web` **0.66.0** bundles those plus fetch, user-interaction, and XHR spans. **No CWV, no JS exceptions, no sessions.** Pre-2024 tutorials wrapping `onFID` as spans are not this stack.

**New browser SDK** (`opentelemetry-browser`): `browser-sdk` **0.4.0** and `browser-instrumentation` **0.8.1** (both npm 2026-09-09; latter depends on `web-vitals` ^6.2.1). Logs + traces; **“Metrics are out of the scope for now.”** Experimental. Default OTLP `http://localhost:4318`. 0.8.1 emits: `browser.navigation` (hard load + `pushState` / `replaceState` / `popstate` / hash); **`browser.web_vital`** log records (semconv Development) with required `browser.web_vital.{name,value,delta,id}`, recommended `{navigation_type,rating}`; well-known names `cls|fcp|inp|lcp|ttfb` (**no `fid`**); `includeRawAttribution` default **false**; `exception` (uncaught `error` + `unhandledrejection`); `browser.console`; fetch/XHR **spans** (`http.request.method`, `url.full`, `http.response.status_code`, `error.type`; CORS `traceparent` via `propagateTraceHeaderCorsUrls` — D4). Session helper: 4 h max / 30 min idle; processors **before** exporters so `session.id` is set.

**Android** GitHub **v1.7.0** (2026-09-04); BOM `opentelemetry-android-bom:1.7.0`. Agent API stable since 1.0.0; **instrumentation remains alpha**. v1.3.0 raised min API **21 → 23** (the docs landing page still says 21 — follow README + Releases). Example session: `backgroundInactivityTimeout = 15.minutes`, `maxLifetime = 4.days` (not Crashlytics 30 min). Offline disk buffer on. Slow frames **> 16 ms**, frozen **> 700 ms**. Emits: **`app.crash`** event (was `device.crash` until 1.5.0) with `exception.{message,stacktrace,type}`, `thread.{id,name}`, stacks truncated **1 000** lines, flush-before-previous-handler in 1.7.0; opt-in **native** `app.crash` on **next launch** (1.6.0); **`device.anr` event** (not a span): poll UI thread every **1 s**, emit after **5** consecutive misses, foreground only — this is **not** Play’s input-dispatch ANR. Also `app.jank`; Compose `app.navigation.complete` (1.7.0); `app.screen.click` / `app.widget.click`. Semconv allows a later process to report a prior crash from tombstones; then `os.name` / `os.version` / `service.version` / `app.build_id` are conditionally required. `session.id` Recommended. Dedup is **not** required.

## Verified knobs and defaults

Tool-neutral starting points from the research pass — **not** vendor SLAs.

| Knob | Verified default / court | Do not |
|---|---|---|
| CWV “good” at p75 | LCP ≤ **2.5 s**, INP ≤ **200 ms**, CLS ≤ **0.1**; all three to pass | Treat a Lighthouse score as field INP; invent a 2026 LCP retune |
| `web-vitals` | **6.2.1**: `onLCP` / `onINP` / `onCLS`; attribution +~1.5 kB brotli; `reportAllChanges` **false** in production | Let a RUM vendor *define* CWV — this library already matches Google |
| Soft navs | **Off** unless opted in (Chrome 151+); diverges from CrUX | Compare soft-nav RUM p75 to Search Console |
| Transport | `sendBeacon` / `fetch`+`keepalive` | Assume unload always fires (mobile often skips it) |
| Browser OTel | New stack for vitals+errors as **events**; legacy auto-web **0.66.0** for **spans only**; no OTLP **metrics** on browser-sdk **0.4.0** | Use `auto-instrumentations-web` for LCP/INP/CLS (it does not emit them) |
| Session idle | **30 min** (Crashlytics + browser-sdk example) | Join Crashlytics 30 min, Play 24 h PT, and OTel 15 min / 4 h / 4 day as one series |
| Android OTel | BOM **1.7.0**; ANR/crash on; sample if battery hurts | Equate OTel’s 1 s × 5 foreground poll with Play input-dispatch |
| Crash-free | **Sessions** for release health, **users** for habit, *fixed* post-release window | Week-over-week crash-free *users* across unequal windows |
| Play floors | Crash **1.09%** / ANR **0.47%** of 28-day DAU | Treat them as UX SLOs; mix DAU rates with session rates |

## Where it lives

Placement is a layering decision. The invariant is **one definition per signal**, not one vendor.

| Layer | What it sees | Trade-off |
|---|---|---|
| **`web-vitals` snippet** | LCP / INP / CLS / FCP / TTFB as Google defines them | Small; matches Search. No crash, no session store |
| **First-party RUM collector** | Same vitals plus attribution, URL, device, consent | Population = script survivors; cardinality of `url.full` |
| **CrUX / Search Console** | Origin/page p75 over 28 days, Chrome-consenting, popular URLs | Free court; no *why*; Safari/Firefox and long-tail URLs absent |
| **Legacy OTel web (auto-web 0.66.0)** | documentLoad / fetch / XHR / user-interaction **spans** | No CWV, no JS exceptions, no sessions |
| **New OTel browser-sdk 0.4.0** | `browser.web_vital` + `exception` **events**, fetch spans, `session.id` | Experimental; metrics out of scope; default OTLP localhost |
| **Crashlytics** | Fatals; crash-free users/sessions; ANR on Android 11+ next start | Session ≠ Play DAU; opt-in charts lie |
| **Play vitals / MetricKit** | Store-visibility crash/ANR (Play) and hang rate (iOS) | 28-day DAU (Play); hang ≠ crash; delayed delivery |
| **OTel Android 1.7.0** | `app.crash`, `device.anr` event, `app.jank` | Alpha instrumentation; ANR poll ≠ Play input-dispatch |

Do not run two CWV implementations and average them. Do not treat CrUX green as a reason to skip first-party RUM.

## Observability

A client monitor without volume and denominator series is how a blocked beacon looks like a perfect day. Emit at least:

| Series | What it tells you |
|---|---|
| **Beacon / RUM event volume** vs **server request rate** (D3) | Volume drop + stable server traffic = monitor outage (blocker, CSP, 429, stripped agent) |
| **p75 LCP / INP / CLS** by URL template, mobile vs desktop | The CWV court; slice to the element / interaction, not a site-wide average of p75s |
| **Share of loads with no INP** | Scroll-only and bot traffic; a missing INP is not “good” |
| **JS `exception` rate** (not folded into crash-free) | Application defects that leave the tab alive |
| **Fatal crash rate** and **crash-free sessions** on a *fixed* window | Release health. Users-over-unequal-windows is the Crashlytics trap |
| **User-perceived ANR / hang** as its own series | Play 0.47% floor; never the crash-free denominator |
| **Consent / sample-rate** | Denominator deploys. A sample-rate change is a deploy, not a quality jump |
| **`session.id` presence** on crash and vital events | Survivor-process reports otherwise steal the next launch’s resource keys |

No vendor PromQL cookbook is a standard. Alert shapes with precedent: *field p75 fails CWV*, *Play 28-day DAU crosses 1.09% / 0.47%*, *RUM volume drops while server RED is flat*, *crash-free sessions drop on a fixed post-release window*.

## Alerting (client-shaped)

Alert on **field p75** or Play’s **28-day DAU** rate — never a single pageview or a Lighthouse score (lab INP does not exist). Symptoms first: CWV fail, Play crash/ANR crossing **1.09% / 0.47%**, Crashlytics crash-free **sessions** on a *fixed* post-release window — then slice by URL / LCP element / INP target / device. Do not alert crash-free *users* across unequal windows. Consent and sample-rate changes are deploys: they move the denominator. A RUM-volume drop with stable server traffic (D3) is a **monitor** outage, not a quality win.

Trade-off vs D3: client series are sparse, consent-biased, and finalized late (INP/CLS wait on `visibilitychange`; mobile crash often arrives on next start). Tight “N of M minutes” burns mis-fire. Use Play/CrUX 28-day courts for external risk; first-party RUM for attribution. Burn-rate and paging policy are D5.

## Worked calibration — checkout web + Android app

Constraints from published courts (a design drill, **not** a vendor SLA this workspace invented):

- Web checkout must **pass CWV** at p75 (all three “good”) on mobile and desktop separately.
- Android checkout must stay under Play’s user-perceived floors: crash **1.09%** and ANR **0.47%** of 28-day DAU.
- Attribution has to answer *which* LCP element, *which* INP target, *which* release.

| Knob | Choice | Why |
|---|---|---|
| CWV source of record | `web-vitals` **6.2.1** in the checkout bundle; CrUX as the Search court | Vendor RUM must not redefine LCP/INP/CLS. CrUX will not explain a regression |
| Soft navs | **Off** for the Search-facing comparison; on only for an SPA-attribution stream labelled as such | Checkout is a hard navigation today; the flag diverges from CrUX |
| Aggregation | p75 by URL *template*, mobile vs desktop, **never** an average of daily p75s | [performance.md](../data-intensive-design/performance.md); p75 was chosen so 25 of 100 samples must move before the court moves |
| JS errors | Separate `exception` rate; not in crash-free | A validation throw is not a process death |
| Android crash | Crashlytics crash-free **sessions** on a *fixed* post-release window; Play 28-day DAU as the store court | Users-over-widening-windows shrink by construction (Crashlytics explicit). Play vs Crashlytics denominators stay unjoined here (D5) |
| Android ANR | Play user-perceived (input-dispatch 5 s) as the floor; OTel `device.anr` as a *faster* foreground hint only | 1 s × 5 poll ≠ Play. Android ≤10 has no 3P ANR |
| Transport | `sendBeacon` / `fetch`+`keepalive`; pair volume with checkout request rate | Mobile skips unload; a silent collector 429 looks like a perfect release |
| Session | Crashlytics 30 min idle for crash-free; do not join to Play’s 24 h PT DAU | Play’s 100% vs 33% example is the trap |
| Trace join | Stamp `session.id`; leave propagation and tail sampling to D4 | Fetch spans here and HTTP RED on D3 need a join key before they are the same request |

Revisit after a week of field p75 and the raw Play window — not after one Lighthouse run on a laptop.

## Failure modes of the monitor itself

- **Population bias.** CrUX = Chrome + consent + popularity. RUM = script survivors. Crashlytics opt-in = optimistic crash-free. Play = certified + Play-installed + consent + k-anonymized.
- **Denominator clash.** Play DAU vs Crashlytics 30 min vs OTel 15 min / 4 h / 4 day — Play’s own 100% vs 33% example. Mixing them is a false trend.
- **Finalization delay.** INP/CLS need `visibilitychange`; mobile often skips unload; Crashlytics ANR/native crash send on next start.
- **Beacon loss.** Process kill, radio, CSP, ad blockers on `/analytics` and OTLP `/v1/logs`. Volume drop ≠ quality. Pair RUM volume with server traffic.
- **Iframe gap.** CrUX includes cross-origin iframes; in-page JS cannot.
- **Wrong navigation model.** Background-tab LCP; forgotten bfcache reset; soft-nav flag diverges from CrUX.
- **ANR holes.** No 3P ANR on Android ≤10; Crashlytics 11+ next-start only; OTel is a foreground 1 s × 5 poll, not Play input-dispatch.
- **Survivor attribution.** Next-process crash reports steal the survivor’s resource unless `session.id` / `app.build_id` are copied (Android agent 1.7.0 native fix).
- **Self-instrumentation.** Console hook, fetch wrap, ANR poll consume the main thread they measure.
- **Cardinality.** Raw `url.full` explodes series.
- **Stale names.** FID, `device.crash`, “ANR spans.” Collector 429 or an R8-stripped agent looks like a perfect day.

## When not to use

| Temptation | Prefer |
|---|---|
| Lighthouse / TBT as a production INP SLO | Field INP at p75; TBT only in lab |
| Crash-free *users* as a week-over-week KPI | Crash-free **sessions** on a fixed window |
| JS exceptions as crashes; ANRs as crashes | Three separate series; crash-free counts fatals only |
| A RUM vendor to *define* CWV | `web-vitals` 6.2.1 |
| `auto-instrumentations-web` for LCP/INP/CLS | browser-instrumentation 0.8.1 (events) or `web-vitals` directly |
| `browser-sdk` 0.4.0 for OTLP **metrics** | It does not emit them |
| Skipping first-party RUM because CrUX is green | CrUX has no attribution; low-traffic URLs are absent |
| Lab alone in production | Lab is enough only for pre-merge LCP/CLS/TBT on a known template |
| Joining Play DAU to Crashlytics sessions to OTel 4-day max | Keep three series; D5 owns any SLO that needs a single denominator |

## Trade-offs

| Buy | Pay |
|---|---|
| User-perceived truth the server cannot see | Consent, blockers, and sampling bias the population |
| CrUX / Play as free external courts | Chrome-only / Play-installed; 28-day lag; no *why* |
| First-party RUM attribution | Script cost on the main thread; beacon loss; cardinality |
| Crash-free sessions as release health | Fatals only; opt-in charts lie; next-start ANR holes |
| OTel browser events for vitals + exceptions | Experimental; no metrics; two JS stacks that do not substitute |
| OTel Android `app.crash` / `device.anr` | Alpha instrumentation; ANR poll ≠ Play definition; session units differ |

D1 names the signal types. This card says what the **client** instance of each type *means*, which library actually emits it, and how the monitor fails. D3 is the server twin; D4 joins session to trace; D5 turns p75 and 28-day DAU into an error budget.

## Sources

Verified 2026-09-13; the full URL list, per-claim provenance, and items deliberately left out (LCP-2.0s rumor, iOS OTel emit list, watchdog example seconds, CrUX popularity cutoff, vendor PromQL cookbooks, W3C Reporting API, session-replay/GDPR implementation) are in the [external research note](../../docs/research/sysdesign/d2-client-monitoring-external-research.md). Items already cited in this tree: [performance.md](../data-intensive-design/performance.md) (percentiles); [nfr-references.md](../data-intensive-design/nfr-references.md) [21]–[36], [28]–[30]; [poc-to-production.md](../claude-certification/enterprise-integration-production/poc-to-production.md).

- Canon: web.dev Web Vitals / LCP / INP / CLS / defining-thresholds; Search Central CWV; CrUX methodology and API; INP launch 2024-03-12; FID retirement 2024-09-09; `web-vitals` 6.2.1.
- Mobile: Android vitals and ANR; Play Console vitals help; Crashlytics crash-free metrics (2026-09-11); Apple MetricKit hang diagnostics and watchdog terminations; WWDC26 session 222.
- OpenTelemetry: `sdk-trace-web` 2.10.0, `auto-instrumentations-web` 0.66.0, `browser-sdk` 0.4.0, `browser-instrumentation` 0.8.1; semconv `browser.web_vital` / `app.crash` / `app.jank` (Development); Android agent 1.7.0.
