---
type: research
title: 'Graceful degradation & kill switches — external research (2026-09-13)'
description: >-
  Group C catalog evidence pass for C11: progressive enhancement vs graceful
  degradation, fallback taxonomies, cached-stale serving, feature flags vs ops
  kill switches, and verified library/CDN/flag-SDK defaults — not failover.
tags: [research, system-design-patterns, C11, c11-graceful-degradation]
---

# C11 Graceful degradation & kill switches — catalog research (2026-09-13)

> **What this is.** The catalog evidence pass for **C11**. It **links** the same-day first pass [failover-degradation-external-research.md](failover-degradation-external-research.md) (RFC 5861 sketch, SRE ch. 22, Hystrix fallback names, OpenFeature, LaunchDarkly kill-switch, SRE “big red button”) and **deepens** it to the Group C / [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md) bar: mechanics and variants, knobs with verified defaults, observability, tuning, a worked homepage calibration, failure modes, sources. **C3 owns failover / health / RTO / RPO / split-brain.** This note owns *what the survivors serve* when a feature or a soft dependency is impaired: quality drop, fallback, and the operator switch that turns the feature off.
>
> **Method.** Primary pages fetched 2026-09-13. Numbers and option names reproduced exactly; everything else paraphrased. Facts marked **[→C3-1]** are in the first-pass note and not re-derived here. Facts marked **[→breaker]** are in [circuit-breaker-external-research.md](circuit-breaker-external-research.md). Unverifiable items are in §10 and are **not** asserted as fact.

---

## 1. Scope and non-goals

**Owns.** Progressive enhancement vs graceful degradation (web lineage + the runtime analogue); hard vs soft dependencies (REL05-BP01); fallback kinds (omit / static / stub / stale cache / cheaper algorithm); kill switches as *long-lived ops toggles* vs product feature flags; library force-open / isolate as in-process switches; cached-stale as a first-class degradation (RFC 5861 + CDN knobs); flag-system failure defaults (OpenFeature, Unleash last-known, LaunchDarkly wait timeout); observability, tuning, and a worked calibration.

**Does not own.** Active/passive failover, probe taxonomy, RTO/RPO, DNS/LB fail-open, database promotion, fencing, split-brain (**C3** — do not rewrite [Failover.md](../../../cases/SystemDesignPatterns/Failover.md) or the first-pass note’s health/DR sections). What errors trip a breaker or how half-open works (**C1**); this note only uses the breaker’s *manual* states as a kill-switch surface and cites Gabrielson’s “avoiding fallback” caution from **[→breaker]**. Dropping *requests* to protect capacity (**C10**); this note drops *work per request*. Error-budget math and burn-rate windows (**D5**); this note only says how a degraded 200 must be classified in the SLI.

**Does not re-derive.** [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md) operational states (`FORCED_OPEN` / `Isolated` / `forceOpen`). [ApiGateway.md](../../../cases/SystemDesignPatterns/ApiGateway.md) Newman BFF “wishlist without stock levels.” First-pass C3/C11 §4–5 vocabulary **[→C3-1]**.

---

## 2. Lineage / vocabulary

| Term | Meaning | Named source |
|---|---|---|
| **Progressive enhancement (PE)** | Start from a baseline every client can use; add richness only after a capability check. | MDN Glossary “Progressive enhancement” (page last modified 2025-07-18) |
| **Graceful degradation (web)** | Build the full modern experience first; fall back to a still-usable essential when a capability is missing. MDN: “often seen as going in the opposite direction” to PE; both “can often complement one another.” | MDN Glossary “Graceful degradation” |
| **Graceful degradation (runtime)** | Reduce *work per response* so the core function survives a soft-dependency or overload failure. SRE: cheaper index / cheaper rank / omit auxiliaries. AWS: serve “slightly stale data, alternate data, or even no data.” | SRE book ch. 22; REL05-BP01 |
| **Hard vs soft dependency** | Hard = no substitute; the caller’s availability is the product of its own and the dependency’s. Soft = the caller still performs its core function when the dependency is unhealthy. | REL05-BP01; REL13 auto-recovery page (hard/soft split) |
| **Fallback** | A *different mechanism* for the same result. Distinct from retry (same mechanism again) and failover (same mechanism, different replica — **C3**). | Gabrielson via **[→breaker]**; REL05-BP01 “Generally, fallback strategies should be avoided.” |
| **Kill switch / ops toggle** | A runtime control whose job is to turn a production behaviour off without a deploy. Hodgson: long-lived ops toggles “could be seen as a manually-managed Circuit Breaker.” | Hodgson, *Feature Toggles* (2017-10-09); LaunchDarkly “Kill switch flags”; Unleash flag type `Kill switch` |
| **Emergency lever** | A rapid, *tested* process that disables, throttles, or changes a component using a known mechanism. Desired outcome: the workload “should degrade gracefully and continue to perform its business-critical functions.” | REL05-BP07 |
| **Big red button** | “A simple, easy-to-trigger action that reverts whatever triggered the undesirable state.” Identify it *before* the risky change. | Google “Twenty years of SRE lessons learned,” lesson #4 |
| **Cached stale** | Serve a response past freshness: `stale-while-revalidate` hides latency; `stale-if-error` hides origin 500/502/503/504 (RFC 5861). | RFC 5861 (Informational, May 2010, M. Nottingham) |

**MDN (fetched 2026-09-13).** PE “provides a baseline of essential content and functionality to as many users as possible, while delivering the best possible experience only to users of the most modern browsers.” GD “centers around trying to build a modern website/application that will work in the newest browsers, but falls back to an experience that while not as good still delivers essential content and functionality in older browsers.” The *direction* is the design difference: PE looks forward from a working core; GD looks back from the full product. The *runtime* analogue is the same pair: PE = the checkout path never needed recommendations; GD = the homepage shipped with recommendations and learns to hide them.

**Hodgson / Fowler, *Feature Toggles (aka Feature Flags)* (2017-10-09).** Four categories: **Release**, **Experiment**, **Ops**, **Permissioning**, plotted on longevity × dynamism. Ops toggles “control operational aspects”; most are short-lived; “a small number of long-lived ‘Kill Switches’” degrade “non-vital system functionality” under high load — his example is disabling an expensive Recommendations panel. A retailer he consulted disabled “many non-critical features in their website’s main purchasing flow just prior to a high-demand product launch.” Ops toggles “need to be re-configured extremely quickly — needing to roll out a new release in order to flip an Ops Toggle is unlikely to make an Operations person happy.”

**REL05-BP01 (reliability-pillar, fetched 2026-09-13).** Desired outcome: “Failure modes of components should be seen as normal operation.” Ecommerce landing page: recommendations, ranked products, and order status come from different systems — “when one upstream system fails, it still makes sense to display everything else instead of showing an error page.” Parameter store: bake defaults into the image; keep them in the test suite. Monitoring: still execute business functions if logs/metrics cannot be shipped (with a compliance caveat). Writes: buffer in a queue so the customer request is accepted while the primary writer is down. Anti-patterns: serving *no* data when a partial result exists; emptying local state after a failed refresh; creating an inconsistent transaction. Closing caution: “the pathways taken in case of component failure need to be tested and should be significantly simpler than the primary pathway. Generally, fallback strategies should be avoided.” That last sentence is Gabrielson, not a contradiction of stale/omit: the forbidden move is an *untested second mechanism* that dumps load onto a weaker path (cache-miss → database).

**Gabrielson, *Avoiding fallback in distributed systems*** (Amazon Builders’ Library; live HTML JS-empty / 409 this session — facts from **[→breaker]** archived copies + REL05-BP01’s citation + Gabrielson’s own 2019 note that the article descends from a 2006 internal “Modes Considered Harmful”). The caution: a fallback that “query the database if the cache is down” turned a partial cache outage into a total one; fallbacks carry latent bugs because they run only when things are already breaking; prefer making the primary reliable, pushing data proactively, or converting the fallback into a *continuously exercised* failover. **C1 owns the breaker-modal reading**; C11 owns the product implication — *omit or serve already-held stale*, do not invent a hotter path.

**SRE book ch. 22 (fetched 2026-09-13).** Load shedding *drops traffic* (C10). Graceful degradation “takes the concept of load shedding one step further by reducing the amount of work that needs to be performed” — in-memory subset vs full disk index; less-accurate ranking. Decide the trigger metric (CPU, latency, queue length, threads; auto vs manual), the actions, and the layer. Warnings: it “shouldn’t trigger very often”; “the code path you never use is the code path that (often) doesn’t work” — exercise by running “a small subset of servers near overload”; monitor/alert when too many servers enter the mode; keep the trigger simple against feedback loops; store the off-switch in a watched config (their example: Chubby) *and* accept the synchronized-failure risk of that store.

**SRE “Twenty years” (fetched 2026-09-13; page undated).** Lesson #2: test recovery before the emergency. #4: big red button. #7: “Intentionally degrade performance modes” — availability is not binary; “Services should degrade gracefully and continue to function under exceptional circumstances.” #9: automate mitigations when the signal is clear.

---

## 3. Mechanics

### 3.1 Two directions, one contract

```
PE (capability):   core HTML/checkout  ──feature detect──►  recommendations, live stock, 3-D
GD (failure):      full homepage       ──dependency fail──►  hide recs / serve stale / static merch
```

The contract is the same: **name the core function**, then list what may disappear. REL05-BP01 makes the ranking a business decision (payments often keep consistency; a real-time app often keeps availability; a customer site follows customer expectation). A kill switch that 500s the page has only moved the failure earlier (Unleash 2026-08-13 guidance).

### 3.2 Degradation actions (what you serve instead)

| Action | What the caller gets | When it is the right tool | Hidden cost |
|---|---|---|---|
| **Fail silent / omit** | Empty list, missing widget, `null` | Additive UI (recs, reviews, related) | Clients that treat empty as “user has none” |
| **Fail fast** | Immediate error, no fallback | The result *is* the core function (auth, capture, inventory decrement) | User-visible 5xx unless a higher layer degrades |
| **Static / stubbed** | In-code default or request-scope stub (geo cookie → country) | Bounded, reviewable substitute | Stale *policy* (Hystrix `getFallback()` returning `true` for a permission) |
| **Cached stale** | Last good response, `Age` > freshness | Read-mostly, already cached | Serves a lie past the SIE window; masks origin death |
| **Cheaper algorithm** | Smaller index, faster rank (SRE ch. 22) | CPU/latency trigger, same schema | Accuracy SLO vs availability SLO |
| **Queue the write** | 202 / accepted | Writes that tolerate delay (REL05-BP01) | Backlog; C10/C9 own the drain |
| **Primary + secondary façade** | Secondary as a *normal* path | Secondary is exercised continuously (Hystrix; Gabrielson “convert fallback to failover”) | Dual-mode ops; “cry wolf” if the secondary trips the primary’s breaker |

**Hystrix wiki “How To Use” (fetched 2026-09-13; Hystrix 1.5.18 final 2018-11-16 [→breaker]).** Named patterns: **Fail Fast** (no `getFallback()`, exception); **Fail Silent** (`null` / empty collection); **Fallback: Static**; **Fallback: Stubbed** (request-scope fields); **Fallback: Cache via Network** (memcached — *itself a network call*: wrap in its own `HystrixCommand` on a **separate thread pool**, else a saturated primary pool blocks the fallback; the cache command’s own fallback is fail-silent `null`); **Primary + Secondary with Fallback** (façade, semaphore-isolated, chooses path via `DynamicBooleanProperty "primarySecondary.usePrimary"` default `true`; each side thread-isolated and individually tuned; do *not* treat a routinely used secondary as a failure of the primary — that trips breakers and pages). `getFallback()` runs on `run()` failure, timeout, pool/semaphore rejection, *and* circuit short-circuit. `HystrixBadRequestException` does not count.

That last row is where C11 and Gabrielson meet: a cache-via-network fallback is the shipping-speed story unless the cache path is **capacity-capped and continuously hit**. Prefer serving bytes *already in the edge* (RFC 5861) over opening a new dependency when the first one is on fire.

### 3.3 Feature flag vs ops kill switch vs library isolate

Same `if` in the binary; different owner, lifetime, targeting, and failure default.

| | Product / release flag | Ops kill switch | Library force-open / isolate |
|---|---|---|---|
| **Job** | Who sees a feature | Turn a behaviour off in an incident | Stop *calling* one dependency |
| **Hodgson box** | Release / Experiment / Permissioning | Long-lived Ops Toggle | Fowler’s “operators should be able to trip or reset” **[→breaker]** |
| **LaunchDarkly** | Release / experiment templates | “Kill switch” template: permanent boolean, variations Enabled/Disabled; “typically do not use complex targeting”; serve Enabled when targeting on, Disabled when off; may wire APM “flag triggers” | — |
| **Unleash** (v3.5+ types; docs fetched 2026-09-13) | `Release` 40 d, `Experiment` 40 d, `Operational` 7 d, `Permission` permanent, `Sunset` 90 d | `Kill switch` — “Gracefully degrade system functionality,” **Permanent**. Type is metadata (does not change evaluation). Parent dependency “Parent feature is disabled” is the documented inverted-parent pattern | — |
| **Default polarity** | Feature-on is usually `true` | Unleash blog 2026-08-13: **invert** — name `disable-recommendations`, default `false`; enabling the flag turns the feature *off*. A `new-recommendations-enabled=true` flag goes dark if the flag service / cache / default is wrong | `forceOpen` / `FORCED_OPEN` / `IsolateAsync` default **off** |
| **Propagation** | Product cadence | Incident seconds (see §4) | In-process, immediate |

LaunchDarkly and Unleash **disagree on polarity**. LD’s template is “Enabled when targeting on.” Unleash’s kill-switch *guidance* is inverted so a flag-system failure leaves the feature running. Pick one convention per fleet and put it in the runbook; do not mix them on one page.

An **ops kill switch is not a failover**. Flipping `disable-recommendations` does not promote a replica (C3). Isolating a Polly circuit does not shed *other* URLs (C10). The switch only changes *this* behaviour.

### 3.4 Cached stale as degradation (not as a new backend)

RFC 5861 (Informational, May 2010; httpwg.org fetch 2026-09-13):

- `stale-while-revalidate=N` — MAY serve stale up to N seconds past freshness; SHOULD revalidate without blocking. Example: `Cache-Control: max-age=600, stale-while-revalidate=30` → fresh 600 s, then 30 s of async stale; after that the next request blocks. Combined lifetime the origin must tolerate = max-age + SWR (example: both 600 → 20 minutes).
- `stale-if-error=N` — on error, MAY serve stale up to N seconds of staleness. Error = any situation that would produce **500, 502, 503, or 504**. Example: `max-age=600, stale-if-error=1200` — at Age 900 a 500 is replaced by the cached 200 (`Age: 900`); past Age 1800 the error is written through.
- Stale responses SHOULD still look stale (`Age` > 0 and a warning). SWR security note: predicate background revalidation on an incoming request to avoid amplification.

RFC 9111 §4.2.4 (fetched 2026-09-13): a cache **MUST NOT** generate a stale response when `must-revalidate`, `proxy-revalidate`, `no-cache`, or an applicable `s-maxage` forbids it. `s-maxage` implies `proxy-revalidate` — **do not pair `s-maxage` with SWR** (Cloudflare documents this explicitly).

This is Gabrielson-compatible: the origin is not asked for a *new* kind of work. The cache returns bytes it already has. The HotOS cache-loss loop **[→breaker]** is the opposite failure — a look-aside miss that *amplifies* origin load.

### 3.5 Placement

| Layer | Mechanism | Typical action |
|---|---|---|
| **CDN / reverse proxy** | RFC 5861 SWR / SIE, Varnish grace, Fastly `beresp.stale_*` | Serve last HTML/JSON |
| **BFF / gateway aggregation** | Newman: fan-out, omit the failed backend **[ApiGateway.md]** | Wishlist without stock |
| **Per-dependency command** | Hystrix `getFallback()` / Resilience4j fallback / Polly fallback | Silent / static / stub |
| **Fleet flag** | OpenFeature client → LaunchDarkly / Unleash / in-house | Hide widget; skip RPC |
| **Library isolate** | Hystrix `forceOpen`; Resilience4j `FORCED_OPEN`; Polly `IsolateAsync` | Fail every call to that dependency |
| **Emergency lever** | REL05-BP07 procedure (manual or automated) | “Do LESS, not more”; may compose C10 shed + C11 hide |

Do not put the kill-switch evaluation on the dependency it is supposed to kill (Unleash: backend SDKs evaluate **locally** from an in-memory repo). Do not make the flag control plane a hard dependency of checkout.

---

## 4. Verified defaults / standards

Fetched 2026-09-13. Library rows that only repeat **[→breaker]** are marked.

| Knob | Default / verified value | Version or fetch | Trade-off |
|---|---|---|---|
| RFC 5861 SWR / SIE | **No numeric default** — origin sets `delta-seconds`. Worked examples: SWR 30, SIE 1200, max-age 600 | RFC 5861 | Too-small SWR → requests miss the window and block; too-large SIE → serve a day-old price |
| Fastly “Serve stale” UI | **Not enabled by default.** UI default TTL **43 200 s (12 h)** | fastly.com serving-stale-content | 12 h of silent origin death; purge-all *overrides* SIE and can stampede the origin |
| Fastly VCL example | `beresp.stale_if_error = 86400s`; `beresp.stale_while_revalidate = 60s`. **SWR overrides SIE** while the SWR window is open | Same page (examples, not platform defaults) | Example 86400 s ≠ UI 43200 s — pick one |
| Fastly `beresp.grace` | Equivalent to `stale_if_error`; a VCL `grace` **overrides** origin SIE headers | Same | Header vs VCL split-brain |
| Varnish `default_grace` | **10 s** (v8.0.1 `varnishd` params). Deliver after TTL expiry “provided another thread is attempting to get a new copy” | varnish-cache.org/docs/8.0/reference/varnishd.html | 10 s is SWR-shaped, not a day-long SIE |
| Cloudflare CDN SIE | Triggers on origin **500/502/503/504** only (404 is *not* an error). Example `max-age=3600, stale-if-error=60`. Ignored if Always Online or `must-revalidate` / `proxy-revalidate` / `s-maxage` / `no-cache` / `no-store`. Set `stale-if-error=0` to opt out | developers.cloudflare.com/cache/concepts/cache-control (updated 2026-06-30) | OCC-disabled: `must-revalidate` is *ignored and stale is served* — a foot-gun |
| Cloudflare Workers cache | If SIE **unset** and no `s-maxage`/`must-revalidate`/`proxy-revalidate`: serve stale on Worker error **indefinitely** until purge. Docs: set `stale-if-error=0` to surface errors | developers.cloudflare.com/workers/cache/configuration | Masks Worker 5xx from monitors |
| Hystrix `circuitBreaker.forceOpen` | **`false`**. If `true`, reject all; **takes precedence over `forceClosed`**. Property `hystrix.command.default.circuitBreaker.forceOpen` | github.com/Netflix/Hystrix/wiki/Configuration | In-process only; not a fleet flag |
| Hystrix `forceClosed` | **`false`**. Ignores error %; `forceOpen` wins | Same | Hides a real outage |
| Resilience4j `FORCED_OPEN` | Always deny; **no events** (except the transition) and **no metrics**. Exit only via `transitionTo*` / `reset()` | resilience4j.readme.io; 2.4.0 2026-03-14 **[→breaker]** | Blind isolate — pair with an external gauge |
| Polly v8 `ManualControl` | Default `null`. `IsolateAsync()` holds Isolated until `CloseAsync()`; callers get `IsolatedCircuitException` | pollydocs.org/strategies/circuit-breaker; Polly 8.7.0 2026-06-10 **[→breaker]** | Isolate ≠ Open (Open still half-opens) |
| OpenFeature evaluation | Client **MUST NOT** throw; abnormal execution **MUST** return the supplied **default value**. No provider → no-op provider returns that default. Statuses: `NOT_READY` / `READY` / `STALE` / `ERROR` / `FATAL` | openfeature.dev spec §01; CNCF accepted 2022-06-17, incubating 2023-11-21 (cncf.io/projects/openfeature) | Fail-open vs fail-closed **is the default you pass**, not a global |
| LaunchDarkly Java server SDK | Streaming is the **default** data source. Polling is opt-in; `DEFAULT_POLL_INTERVAL` **30 s** (also the minimum) | launchdarkly-java-server-sdk **7.15.0** (GitHub release 2026-07-21) | Stream ≈ seconds; poll ≥ 30 s to every instance |
| LaunchDarkly JS client | `waitForInitialization` default timeout **5 s**; docs recommend ≤ 5 s. Streaming **off** unless `streaming: true` or a `change` listener. Poll interval in js-core **300 s** | launchdarkly.com/docs/sdk/client-side/javascript; `@launchdarkly/js-client-sdk-common` 1.30.2 javadoc | A kill switch on the **browser** can lag minutes if no stream |
| Unleash Node SDK | `refreshInterval` default **15 000 ms**; `metricsInterval` **60 000 ms**. Evaluation is local; unreachable server → **last known** config | docs.getunleash.io/sdks/node | ≤ 15 s fleet lag; cold start with empty repo needs bootstrap/defaults |
| Unleash flag-type lifetimes | Kill switch **Permanent**; Operational **7 days**; Release/Experiment **40 days** | docs.getunleash.io/concepts/feature-flags | Cleanup jobs must exempt kill switches |

OpenFeature does **not** mandate last-known-config; `PROVIDER_STALE` means a provider *may* keep serving cached rules. Unleash’s last-known behaviour is a **vendor SDK** property, not the spec.

---

## 5. Observability, knobs, tuning

### 5.1 Signals (emit per feature / dependency / hop)

| Signal | Why |
|---|---|
| **Degraded-mode gauge** (0/1 or enum: full / stale / omitted / isolated) | SRE ch. 22: alert when too many servers enter the mode |
| **Action taken** (`omit` / `static` / `stale` / `cheaper` / `force_open`) | “200 OK” is not a diagnosis |
| **Flag key, type, polarity, evaluation reason** | OpenFeature reason + provider status (`STALE` vs `ERROR`) |
| **Cache `Age` and `Cf-Cache-Status` / Fastly stale** | SIE vs SWR vs origin 5xx |
| **Fallback invocations vs primary successes** | Hystrix `getFallback()` rate; a rising fallback *is* the incident |
| **Flag-SDK freshness** (last successful refresh age) | Unleash 15 s / LD stream gap / LD JS 300 s poll |
| **Error-budget class of the response** | D5: is this 200 *good* for availability and *bad* for freshness? |

Do not let `FORCED_OPEN` go dark: Resilience4j records **no metrics** in that state — scrape the state gauge (`resilience4j.circuitbreaker.state`) or you have a silent isolate **[→breaker]**.

### 5.2 Tuning

1. **Write the core-function list first** (REL05-BP01). Everything else is eligible to omit or stale.
2. **Prefer PE for new work**: ship the widget off; enhance when the dependency is healthy. GD is the retrofit for a page that already assumes the widget.
3. **Prefer already-held stale over a new fallback RPC** (Gabrielson **[→breaker]**; Hystrix cache-via-network warning).
4. **Cap SIE to a business-tolerable lie.** RFC example 1 200 s is a *document example*, not a standard. Fastly UI 12 h is a *vendor convenience*.
5. **Invert ops switches** (Unleash 2026-08-13) *or* fail the SDK default to “feature on” and accept last-known. Never default a kill switch to “feature off” on a cold start unless the feature is non-core *and* you have tested the empty page.
6. **Propagation budget.** Streaming LD server-side for incident switches; Unleash 15 s is usually enough (their words). Do not put a homepage kill switch only in a JS client that polls every 300 s.
7. **Exercise the path** (SRE ch. 22; Twenty-years #2; Unleash: flip in staging, then in a low-traffic prod window, on a schedule). An untested `getFallback()` is Gabrielson’s latent bug.
8. **Pair with a shed, don’t impersonate one.** When the remaining core still overloads the box, C10 drops requests; C11 has already dropped work.
9. **Exempt kill switches from leftover-flag cleanup** (Unleash type Permanent; LD “usually permanent”) and give them an owner + review date.

---

## 6. Worked calibration — ecommerce homepage

Constraints are a **design drill**, not a vendor SLA. Method: REL05-BP01 landing-page split + Hodgson recommendations toggle + RFC 5861 examples + Unleash/LD propagation + SRE ch. 22 layering. Numbers that are RFC/vendor examples are tagged.

**Core (hard).** Search box, product URL, cart, `POST /checkout` capture. Fail fast; no stale prices on SKUs that can be bought; no inverted flag that can disable capture on a flag-service blip.

**Soft (eligible).** Personalized recommendations, “customers also bought,” reviews teaser, live order-status chip on the logged-in hero.

Measured recs-service caller-side latency (same AZ, 14 days) — drill, not a published Amazon figure:

| Percentile | Latency |
|---|---|
| p50 | 40 ms |
| p95 | 90 ms |
| p99.9 | 250 ms |

**Ladder** (cheapest / most-exercised first):

1. **Edge stale (always-on PE).** Origin: `Cache-Control: public, max-age=600, stale-while-revalidate=30, stale-if-error=1200` (RFC 5861 §3.1 / §4.1 examples). Recs HTML fragment is cacheable GET. Cloudflare: do **not** add `s-maxage` (disables SWR). Fastly: do **not** also enable the 43 200 s UI switch on the same service — two SIE windows. Varnish `default_grace` 10 s is *in addition* only if you are not sending SWR.
2. **Per-command omit (automatic GD).** Recs command: timeout 300 ms (above p99.9; C7 owns the Brooker pick). Fallback = Fail Silent empty fragment (Hystrix). **No** cache-via-network hop to memcached on the miss path — that is the Gabrielson anti-pattern unless memcached is the *primary* store and is hit on the success path too.
3. **Ops kill switch (manual / APM).** Unleash type `Kill switch`, key `disable-homepage-recs`, inverted: flag `false` → render recs; flag `true` → omit. Node SDK 15 s worst-case fleet lag. Alternative: LD kill-switch template, Java server SDK streaming, polarity documented as “targeting off = Disabled = widget gone.” Parent-flag fan-in: Unleash warns that one global parent over many children is easy to misconfigure — prefer one switch per blast-radius.
4. **Isolate the RPC.** If recs is also poisoning the BFF thread pool: Polly `IsolateAsync` / Resilience4j `transitionToForcedOpenState` / Hystrix `forceOpen=true` on that command only. Immediate, in-process; still hide the widget (step 3) so the BFF does not 500.
5. **Shed (C10), not here.** If homepage HTML itself cannot be produced, drop *requests* at the edge. C11 has already removed recs work.

**Checkout.** No SIE on `POST /capture`. No kill switch whose default-off disables payment. A *release* flag for a new capture path may exist; its fail-safe is “old path,” continuously exercised (Hystrix primary/secondary façade), not a static “payment accepted” stub.

**Error budget (D5).** Homepage availability SLI counts a 200 with recs omitted as **good**. A separate *freshness* or *personalization* SLI counts SIE hits as **bad**. Do not let SIE 200s hide an origin outage from the burn-rate alert — scrape `Age` and degraded-mode.

**Exercise.** Weekly: force recs 500s in one canary (SRE “small subset near overload”); flip `disable-homepage-recs` in prod for 5 minutes off-peak; confirm omit, flat 5xx, and restore. Twenty-years #2 / Unleash “an untested kill switch is a guess.”

---

## 7. Failure modes and when-not-to-use

1. **Untested fallback becomes the outage.** Gabrielson **[→breaker]**; SRE “code path you never use.” Cache-down → database is the canonical story.
2. **Fallback that is a hotter path.** Hystrix cache-via-network on the failure path; look-aside miss amplification (HotOS **[→breaker]**).
3. **SIE as a silent origin death.** Fastly 12 h UI; Cloudflare Workers indefinite default; OCC-disabled Cloudflare ignoring `must-revalidate`. Monitors see 200.
4. **`s-maxage` + SWR.** RFC 9111 / Cloudflare: SWR disabled. Config that *looks* like stale-on-error is fail-closed.
5. **Flag-system hard dependency.** `new-recs-enabled` default `false` + empty SDK repo on cold start = homepage without recs *or* without checkout if someone reused the pattern. Unleash invert + bootstrap file.
6. **Polarity mix-up.** LD Enabled-when-on vs Unleash disable-when-on. On-call flips the wrong way.
7. **Kill switch on the client only.** LD JS 300 s poll / no stream → the “big red button” takes minutes.
8. **`FORCED_OPEN` without a gauge.** Resilience4j stops events and metrics.
9. **`forceClosed` / DISABLED as a “fix.”** Admits doomed calls; hides the outage (Hystrix docs: forceClosed allows all regardless of error %).
10. **Complex targeting on an incident switch.** LD: kill switches “typically do not use complex targeting.” A percentage rollout is a release flag, not a lever.
11. **Parent/child flag graphs.** Unleash: resist one global parent; inverted parent is supported but easy to get wrong.
12. **Cleanup job deletes the lever.** Unleash Permanent vs 40-day release sweeper.
13. **Degraded 200 spends no budget.** D5: freshness SLI must exist or SIE is free.
14. **Bimodal recovery.** REL05-BP07 / REL11-BP05: the lever must not require a control-plane scale-up to survive (C3 static stability). “Do LESS, not more.”
15. **GD used as a substitute for PE.** W3C-wiki (search-indexed; live fetch bot-walled — see §10): GD is the cheaper retrofit and the worse long-term maintenance. New surfaces should be PE.
16. **Consistency core treated as soft.** REL05-BP01 payments example: a static “charged” stub is fraud, not degradation.
17. **Brownout controller as an unowned closed loop.** Klein et al. ICSE 2014 (optional-code + controller) **[→C3-1]** — abstract only this session; do not copy a PID from memory.

**When degradation is the wrong tool.** The dependency *is* the product (authn, capture, durable write you cannot buffer). You have no already-held bytes and the only fallback is a weaker datastore (Gabrielson). You need a replica promotion (C3) or a shed (C10). Message-driven flows that already dead-letter (Azure breaker “not suitable” **[→breaker]**).

**When a kill switch is the wrong tool.** A one-off release you will delete next week (use a release flag and retire it). A per-user experiment (experiment flag). A permission/entitlement (permission flag — Unleash Permanent, different owner). A health-check fail-open (C3).

---

## 8. Cross-links

| Id | Why |
|---|---|
| **C3** health / failover | Survivors and probes; this note does not rewrite RTO/RPO, Route 53, or GitHub 2018. First pass: [failover-degradation-external-research.md](failover-degradation-external-research.md) |
| **C1** breaker | `FORCED_OPEN` / `forceOpen` / `Isolate`; Gabrielson “avoiding fallback” **[→breaker]**; fallback is what you do *while Open* |
| **C10** shedding | Drop *requests*; C11 drops *work per request* (SRE ch. 22 split) |
| **C2** retry | A retry is not a fallback; retries-as-accidental-fallback is Gabrielson’s last warning |
| **C7** timeouts | Bound the dependency so omit/stale can run; Brooker pick stays in C7 |
| **C8** bulkhead | Hystrix separate pool for cache-via-network; isolate one widget’s threads |
| **D5** error budgets | Classify omitted/stale in the SLI; burn-rate must still see origin death |
| **D1 / D3** | Emit the gauges; this note does not write PromQL |
| Cases | [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md) (ops states as kill switches); [Failover.md](../../../cases/SystemDesignPatterns/Failover.md) (points at degradation; C3); [ApiGateway.md](../../../cases/SystemDesignPatterns/ApiGateway.md) (BFF partial fan-out); [poc-to-production.md](../../../cases/claude-certification/enterprise-integration-production/poc-to-production.md) (POC with no fallback) |

---

## 9. Sources

Fetched 2026-09-13 unless noted.

**Canon.** developer.mozilla.org/en-US/docs/Glossary/Progressive_Enhancement (2025-07-18) · developer.mozilla.org/en-US/docs/Glossary/Graceful_degradation · martinfowler.com/articles/feature-toggles.html (Hodgson, 2017-10-09) · docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_graceful_degradation.html (REL05-BP01) · docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_emergency_levers.html (REL05-BP07) · sre.google/sre-book/addressing-cascading-failures (ch. 22) · sre.google/resources/practices-and-processes/twenty-years-of-sre-lessons-learned · httpwg.org/specs/rfc5861.html (RFC 5861, May 2010) · rfc-editor.org/rfc/rfc9111.html §4.2.4 · github.com/Netflix/Hystrix/wiki/How-To-Use · github.com/Netflix/Hystrix/wiki/Configuration.

**Flags / kill switches.** launchdarkly.com/docs/home/flags/killswitch · launchdarkly.com/docs/guides/flags/creating-flags · launchdarkly.com/blog/launched-automatic-kill-switches-using-flag-triggers · launchdarkly.com/docs/sdk/server-side/java · launchdarkly.com/docs/sdk/client-side/javascript · launchdarkly.github.io/java-core/lib/sdk/server (7.15.0, 2026-07-21) · docs.getunleash.io/concepts/feature-flags · docs.getunleash.io/sdks/node · getunleash.io/blog/how-should-i-implement-a-kill-switch-for-a-critical-production-feature (2026-08-13) · openfeature.dev/specification/sections/flag-evaluation · github.com/open-feature/spec/blob/main/specification/sections/01-flag-evaluation.md · cncf.io/projects/openfeature · cncf.io/blog/2023/12/19/openfeature-becomes-a-cncf-incubating-project.

**Cache / CDN.** fastly.com/documentation/guides/full-site-delivery/performance/serving-stale-content · fastly.com/documentation/guides/concepts/cache/stale · varnish-cache.org/docs/8.0/reference/varnishd.html (`default_grace` 10 s) · developers.cloudflare.com/cache/concepts/cache-control (2026-06-30) · developers.cloudflare.com/workers/cache/configuration · developers.cloudflare.com/cache/concepts/cdn-cache-control.

**Libraries (kill-switch surface).** resilience4j.readme.io/docs/circuitbreaker · pollydocs.org/strategies/circuit-breaker · pollydocs.org/api/Polly.CircuitBreaker.CircuitBreakerManualControl.html · **[→breaker]** Resilience4j 2.4.0 / Polly 8.7.0 / Hystrix 1.5.18 version pins.

**Cited forward.** [circuit-breaker-external-research.md](circuit-breaker-external-research.md) §1 Gabrielson / Brooker (archived Builders’ Library) · [failover-degradation-external-research.md](failover-degradation-external-research.md) §§4–5 · a-nickels-worth.dev/posts/avoiding-fallback-in-distributed-systems (2019-12-20; 2006 “Modes Considered Harmful” origin) · aws.amazon.com/blogs/architecture/reinvent-2019-introducing-the-amazon-builders-library-part-ii (whiteboard analogy) · aws.amazon.com/builders-library/caching-challenges-and-strategies (cache-down → origin spike; prefer in-memory + shed).

---

## 10. Uncertain / left out

- Live `aws.amazon.com/builders-library/avoiding-fallback-in-distributed-systems` and `builder.aws.com` article body: JS-empty / cookie wall / archive fetch timeout this session. Shipping-speed / ~2001 cache story and the word-level “we almost never use them” claim stay on **[→breaker]** archived copies; not re-quoted here.
- W3C wiki “Graceful degradation versus progressive enhancement”: live fetch bot-walled (Cloudflare challenge). Directional PE-vs-GD contrast taken from MDN (verified). Extra W3C sentences (“looking back / looking forward,” “GD is a patch”) **not** asserted from a primary extract.
- REL05-BP07 “Block all robot traffic / serve static pages / reduce call frequency” examples appear on the **2022-03-31** framework snapshot; the 2026 reliability-pillar page fetched here states the lever definition without those four bullets — examples not asserted as current.
- LaunchDarkly “flag triggers” blog describes unguessable URLs that toggle a flag; per-vendor webhook latency to the SDK stream was not measured.
- Unleash Node `refreshInterval` 15 000 ms is from current docs, not a pinned SDK semver this session.
- LD JS poll **300 s** is from js-core `DEFAULT_POLLING_INTERVAL = 60 * 5` at commit `8dfef4a`; not re-read on every 1.30.x tag.
- Cloudflare CDN default SIE when the directive is *absent* (Workers “indefinite” is documented; CDN-without-Workers is “set `stale-if-error=0` to avoid” — whether the CDN default is also indefinite is **not** asserted).
- Fastly control-panel 43 200 s vs VCL example 86 400 s: both documented; which a new service gets if *both* are configured was not labbed.
- Brownout (Klein et al., ICSE 2014) PDF not extracted; “dimmer” body vocabulary not asserted **[→C3-1]**.
- Nygard *Release It!* mapping of degradation to a named stability pattern was not fetchable **[→breaker §7]**.
- Homepage latency table and 5-minute exercise window are a drill.
- PromQL / OTel attribute names above are recommendations, not a vendor schema.
- OpenFeature provider last-known-config is provider-specific; only the default-value MUST is spec-level.
- Wikipedia PE history (Champeon / Shea) not used as a primary.
- Route 53 ARC “on/off switches” stay in **C3**.
