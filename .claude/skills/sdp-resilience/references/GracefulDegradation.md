---
id: C11
title: 'Graceful degradation'
description: 'Diagnose which dependencies are soft, select the cheapest fallback that still tells the truth (omit, static, stub, or already-held stale), tune kill-switch polarity and propagation, and verify the degraded path is drilled. Covers hard vs soft dependencies (REL05-BP01), the Hodgson kill-switch box, the Hystrix fallback taxonomy, RFC 5861 stale serving, verified CDN and flag-SDK defaults, a homepage ladder, and drills.'
tags: [system-design-patterns, resilience, graceful-degradation, kill-switch, feature-flags]
---

# Graceful degradation

**See also (non-load-bearing bonus):** the source Concept [Graceful degradation and kill switches](../../../../cases/SystemDesignPatterns/GracefulDegradation.md) carries the full per-claim provenance. This card stands alone — you do not need to open it to diagnose, select, tune, or verify.

Load shedding (C10) drops whole requests. Graceful degradation **shrinks the work per request** so the named core function still returns: hide a rail, serve last-good HTML, rank against a smaller index, queue a write. A **kill switch** is the operator interface — a long-lived ops toggle that turns a capability off *on purpose* before the system does it chaotically. Quality attributes in play: **availability of the core function** under partial failure, and **operator agency**. The costs: every degraded mode is a second code path with the fallback hazard — latent bugs, a product argument about "good enough," and rot unless the path is exercised.

This card owns the **product decision**: what the user gets, which dependencies are soft, how stale is sellable, and who may flip which switch. The circuit breaker's (C1) `FORCED_OPEN` / Polly `Isolate` / Hystrix `forceOpen` are **actuators** that stop *calling* one dependency — they are not this card's decision about what the caller serves instead. Failover (C3) owns probes, survivors, RTO/RPO, and split-brain; do not treat a flag flip as a replica promotion.

## Lineage and vocabulary

- **Progressive enhancement vs graceful degradation (web).** MDN: PE starts from a baseline every client can use and adds richness after a capability check; GD "is often seen as going in the opposite direction" — ship the full modern experience, then fall back to a still-usable essential. They complement. The *runtime* analogue is the same pair: PE = checkout never needed recommendations; GD = the homepage shipped with them and learns to hide them. New surfaces should be PE; GD is the retrofit.
- **Runtime degradation (SRE ch. 22).** Load shedding drops traffic (C10). Degradation "takes the concept of load shedding one step further" by reducing work: in-memory subset vs full disk index, less-accurate ranking, omit auxiliaries. Decide the **trigger** (CPU, latency, queue, threads; auto vs manual), the **actions**, and the **layer**. It "shouldn't trigger very often"; "the code path you never use is the code path that (often) doesn't work" — exercise by running a small subset of servers near overload; alert when too many enter the mode; keep the trigger simple against feedback loops. Store the off-switch in a watched config (their example: Chubby) *and* accept the synchronized-failure risk of that store.
- **Hard vs soft dependency (REL05-BP01).** Hard = no substitute; the caller's availability is the product of its own and the dependency's. Soft = the caller still performs its **core function** when the dependency is unhealthy. Ranking that split is a business decision (payments often keep consistency; a real-time app often keeps availability; a customer site follows customer expectation). Ecommerce landing page: recommendations, ranked products, and order status come from different systems — "when one upstream system fails, it still makes sense to display everything else instead of showing an error page." Parameter store: bake defaults into the image and keep them in the test suite. Monitoring: still execute business functions if logs/metrics cannot be shipped (with a compliance caveat). Writes: buffer so the request is accepted. Anti-patterns: serving *no* data when a partial result exists; emptying local state after a failed refresh; fabricating a transaction. Failure modes of components should be treated as **normal operation**.
- **Fallback vs retry vs failover.** A fallback is a *different mechanism* for the same result. A retry (C2) is the same mechanism again. Failover (C3) is the same mechanism on a different replica. REL05-BP01 closes with Gabrielson's sentence: "Generally, fallback strategies should be avoided" — the forbidden move is an *untested second mechanism* that dumps load onto a weaker path (cache-miss → database), not omit or already-held stale.
- **Gabrielson, *Avoiding fallback in distributed systems*** (Builders' Library; cited via the circuit-breaker (C1) research, not re-fetched here). A "query the database if the cache is down" fallback turned a partial cache outage into a total one (the 2001 retail story). Fallbacks carry latent bugs because they run only when things are already breaking. Prefer making the primary reliable, pushing data proactively, or converting the fallback into a *continuously exercised* path. C1 owns the breaker-modal reading; this card owns the product implication — omit or serve bytes you already hold; do not invent a hotter path.
- **Brownout (Klein et al., ICSE 2014).** Formalizes optional-code: mark work optional and let a controller deactivate it dynamically; their RUBiS/RUBBoS retrofits cost under 170 lines. The keepable idea is the peacetime inventory of what is optional — not an unowned closed loop (the paper's controller is not re-derived here).
- **Hodgson / Fowler, *Feature Toggles* (2017).** Four boxes: Release, Experiment, Ops, Permissioning (longevity × dynamism). Ops toggles "control operational aspects"; a small number of long-lived **kill switches** degrade "non-vital system functionality" under load — his example is disabling an expensive Recommendations panel. They "need to be re-configured extremely quickly"; shipping a release to flip one will not make operations happy. A retailer he consulted disabled many non-critical features in the purchasing flow just before a high-demand launch.
- **HTTP already has the stale primitive (RFC 5861).** `stale-while-revalidate` hides latency; `stale-if-error` hides origin 500/502/503/504. This card owns *stale-as-degradation*; CDN/edge topology (catalog id B8) owns cache keys, edge acceleration, and CDN placement.
- **Hystrix fallback taxonomy** (wiki "How To Use"): **Fail Fast** (no fallback); **Fail Silent** (`null` / empty); **Static**; **Stubbed** (request-scope fields); **Cache via Network** (memcached — *itself a network call*: wrap in its own command on a **separate** bulkhead (C8), else a saturated primary pool blocks the fallback); **Primary + Secondary** (façade, `DynamicBooleanProperty`, each side isolated — do not treat a routinely used secondary as a primary failure). `getFallback()` runs on `run()` failure, timeout, rejection, *and* short-circuit.
- **Emergency lever / big red button.** REL05-BP07: a rapid, *tested* process that disables, throttles, or changes a component; desired outcome is graceful continuation of business-critical functions — "do LESS, not more." SRE twenty-years lesson #4: identify a simple revert *before* the risky change. #2: test recovery before the emergency. #7: intentionally degrade performance modes. #9: automate when the signal is clear.

## Two directions, one contract

```
PE (capability):   core HTML/checkout  ──feature detect──►  recommendations, live stock, 3-D
GD (failure):      full homepage       ──dependency fail──►  hide recs / serve stale / static merch
```

The contract is the same: **name the core function**, then list what may disappear. REL05-BP01 makes that ranking a product decision, not an SRE default. A kill switch that 500s the page has only moved the failure earlier (Unleash, 2026-08-13).

Retries are not this pattern. A retry (C2) is the same mechanism again and is the usual metastable loop; Gabrielson's last warning is retries-as-accidental-fallback. Timeouts (C7) bound the soft dependency so omit/stale can run; the Brooker pick stays there. The circuit breaker (C1) decides *whether to call*; fallback — what the user gets while Open — is orchestration, not a state inside the automaton.

## What you serve instead

Name the **core function** first. Everything else is eligible to omit or stale.

| Action | Caller gets | Right tool when | Hidden cost |
|---|---|---|---|
| **Fail silent / omit** | Empty list, missing widget | Additive UI (recs, reviews, related) | Clients that treat empty as "user has none" |
| **Fail fast** | Immediate error, no substitute | The result *is* the core (auth, capture, inventory decrement) | User-visible 5xx unless a higher layer degrades |
| **Static / stubbed** | In-code default or request-scope stub | Bounded, reviewable substitute | Stale *policy* (`getFallback()` returning `true` for a permission) |
| **Cached stale** | Last good response, `Age` past freshness | Read-mostly, already cached | A lie past the SIE window; masks origin death |
| **Cheaper algorithm** | Smaller index, faster rank (SRE ch. 22) | CPU/latency trigger, same schema | Accuracy SLO vs availability SLO |
| **Queue the write** | 202 / accepted | Writes that tolerate delay (REL05-BP01) | Backlog; load shedding (C10) / idempotency (C9) own the drain |
| **Primary + secondary façade** | Secondary as a *normal* path | Secondary is exercised continuously (Gabrielson "convert fallback to failover") | Dual-mode ops; "cry wolf" if the secondary trips the primary's breaker |

Reads degrade more comfortably than writes. A stale read is a product decision; a lost write is an incident. Writes degrade by **deferral** (queue + key), never by fabrication. A static "charged" stub on a consistency core is fraud, not degradation (REL05-BP01 payments example).

The last two rows are where this card and Gabrielson meet. A cache-via-network fallback is the shipping-speed story unless the cache path is **capacity-capped and continuously hit** — Hystrix is explicit that the cache command lives on a **separate thread pool**, and that the cache command's own fallback is fail-silent `null`. Prefer serving bytes *already in the edge* (RFC 5861) over opening a new dependency when the first one is on fire. A primary + secondary façade is allowed only when the secondary is a *normal* path; treating a routinely used secondary as a primary failure trips breakers and pages ("cry wolf").

## Kill switches: product flag, ops toggle, library isolate

Same `if` in the binary; different owner, lifetime, targeting, and failure default.

| | Product / release flag | Ops kill switch | Library force-open / isolate |
|---|---|---|---|
| **Job** | Who sees a feature | Turn a behaviour off in an incident | Stop *calling* one dependency |
| **Hodgson box** | Release / Experiment / Permissioning | Long-lived Ops Toggle ("manually-managed Circuit Breaker") | Fowler's operator trip/reset — the circuit breaker (C1) actuator |
| **LaunchDarkly** | Release / experiment templates | "Kill switch": permanent boolean, Enabled/Disabled; typically no complex targeting; may wire APM flag triggers | — |
| **Unleash** (v3.5+ types) | `Release`/`Experiment` 40 d, `Operational` 7 d, `Permission` permanent, `Sunset` 90 d | `Kill switch` — "Gracefully degrade system functionality," **Permanent**. Type is metadata | — |
| **Default polarity** | Feature-on is usually `true` | Unleash (2026-08-13): **invert** — name `disable-recommendations`, default `false`; enabling turns the feature *off*. A `new-recs-enabled=true` flag goes dark if the SDK/cache/default is wrong | `forceOpen` / `FORCED_OPEN` / `IsolateAsync` default **off** |
| **Propagation** | Product cadence | Incident seconds | In-process, immediate |

LaunchDarkly and Unleash **disagree on polarity**. LD's template is "Enabled when targeting on." Unleash's guidance is inverted so a flag-system failure leaves the feature running. Pick one convention per fleet; do not mix them on one page. An ops kill switch is **not** failover (C3) and **not** a shed of *other* URLs (C10). Isolating a Polly circuit does not hide the widget — the product path still has to omit, or the BFF 500s.

Do not evaluate the kill switch on the dependency it is supposed to kill (Unleash: backend SDKs evaluate **locally** from an in-memory repo). Do not make the flag control plane a hard dependency of checkout. OpenFeature (CNCF incubating) standardizes the evaluation API vendor-neutrally: a client **MUST NOT** throw; abnormal execution **MUST** return the supplied default. Fail-open vs fail-closed **is the default you pass**, not a global. OpenFeature does *not* mandate last-known-config; `PROVIDER_STALE` means a provider *may* keep serving cached rules. Unleash's last-known behaviour is a vendor SDK property.

## Stale serving (RFC 5861)

This is Gabrielson-compatible: the origin is not asked for a *new* kind of work. The cache returns bytes it already has. The HotOS cache-loss loop (circuit-breaker research, C1) is the opposite — a look-aside miss that *amplifies* origin load.

RFC 5861 (Informational, May 2010):

- `stale-while-revalidate=N` — MAY serve stale up to N seconds past freshness; SHOULD revalidate without blocking. Example: `max-age=600, stale-while-revalidate=30` → fresh 600 s, then 30 s of async stale; after that the next request blocks. Combined lifetime the origin must tolerate = max-age + SWR.
- `stale-if-error=N` — on error, MAY serve stale up to N seconds of staleness. Error = any situation that would produce **500, 502, 503, or 504**. Example: `max-age=600, stale-if-error=1200` — at Age 900 a 500 is replaced by the cached 200; past Age 1800 the error is written through.
- Stale responses SHOULD still look stale (`Age` > 0 and a warning). SWR security note: predicate background revalidation on an incoming request to avoid amplification.

RFC 9111 §4.2.4: a cache **MUST NOT** generate a stale response when `must-revalidate`, `proxy-revalidate`, `no-cache`, or an applicable `s-maxage` forbids it. `s-maxage` implies `proxy-revalidate` — **do not pair `s-maxage` with SWR** (Cloudflare documents this explicitly). Prefer already-held stale over a Hystrix cache-via-network hop on the miss path.

## Configuration & verified defaults

Verified 2026-09-13.

| Knob | Default / verified value | Trade-off |
|---|---|---|
| RFC 5861 SWR / SIE | **No numeric default** — origin sets `delta-seconds`. RFC examples: SWR 30, SIE 1200, max-age 600 | Too-small SWR → requests miss and block; too-large SIE → a day-old price |
| Fastly "Serve stale" UI | **Off** by default. UI default TTL **43 200 s (12 h)** | 12 h of silent origin death; purge-all *overrides* SIE and can stampede the origin |
| Fastly VCL example | `beresp.stale_if_error = 86400s`; `beresp.stale_while_revalidate = 60s`. **SWR overrides SIE** while SWR is open. `beresp.grace` ≡ SIE; a VCL `grace` **overrides** origin SIE headers | Example 86400 s ≠ UI 43200 s — pick one |
| Varnish `default_grace` | **10 s** (v8.0.1) — deliver after TTL expiry "provided another thread is attempting to get a new copy" | SWR-shaped, not a day-long SIE |
| Cloudflare CDN SIE | Origin **500/502/503/504** only (404 is *not* an error). Example `max-age=3600, stale-if-error=60`. Ignored if Always Online or `must-revalidate` / `proxy-revalidate` / `s-maxage` / `no-cache` / `no-store`. `stale-if-error=0` opts out | OCC-disabled: `must-revalidate` is *ignored and stale is served* |
| Cloudflare Workers cache | If SIE **unset** and no `s-maxage`/`must-revalidate`/`proxy-revalidate`: serve stale on Worker error **indefinitely** until purge | Masks Worker 5xx from monitors |
| Hystrix `forceOpen` / `forceClosed` | Both **`false`**. `forceOpen` **takes precedence**; `forceClosed` ignores error % | In-process only; `forceClosed` hides a real outage |
| Resilience4j `FORCED_OPEN` | Always deny; **no events** (except the transition) and **no metrics**. Exit via `transitionTo*` / `reset()` | Blind isolate — pair with an external state gauge |
| Polly v8 `ManualControl` | Default `null`. `IsolateAsync()` holds Isolated until `CloseAsync()`; `IsolatedCircuitException` | Isolate ≠ Open (Open still half-opens) |
| OpenFeature evaluation | MUST return the supplied **default**; no provider → no-op provider | Fail-open vs fail-closed is that default |
| LaunchDarkly Java server SDK 7.15.0 | Streaming **default**; polling opt-in, `DEFAULT_POLL_INTERVAL` **30 s** (also the minimum) | Stream ≈ seconds |
| LaunchDarkly JS client | `waitForInitialization` default **5 s**; streaming **off** unless `streaming: true` or a `change` listener; js-core poll **300 s** | A *browser-only* kill switch can lag minutes |
| Unleash Node SDK | `refreshInterval` **15 000 ms**; unreachable server → **last known** | ≤ 15 s fleet lag; cold start with empty repo needs bootstrap |

## Where it lives

| Layer | Mechanism | Typical action |
|---|---|---|
| **CDN / reverse proxy** | RFC 5861 SWR / SIE; Varnish grace; Fastly `beresp.stale_*` | Serve last HTML/JSON. CDN/edge topology (B8) owns the rest of the edge. |
| **BFF / gateway aggregation** | Newman: fan-out, omit the failed backend (API gateway / BFF, C6 — "wishlist without stock") | Partial page, not a 5xx |
| **Per-dependency command** | Hystrix `getFallback()` / Resilience4j / Polly fallback | Silent / static / stub |
| **Fleet flag** | OpenFeature → LaunchDarkly / Unleash / in-house | Hide widget; skip RPC |
| **Library isolate** | Hystrix `forceOpen`; Resilience4j `FORCED_OPEN`; Polly `IsolateAsync` | Fail every call to *that* dependency — then hide the feature so the caller does not 500 |
| **Emergency lever** | REL05-BP07 procedure (manual or automated) | Compose hide (this card) + shed (C10); do not scale up through a sick control plane |

## Observability

A 200 is not a diagnosis. Emit per feature / dependency / hop:

| Signal | Why |
|---|---|
| **Degraded-mode gauge** (full / stale / omitted / isolated) | SRE ch. 22: alert when too many servers enter the mode |
| **Action taken** (`omit` / `static` / `stale` / `cheaper` / `force_open`) | Distinguishes "available" from "available because we lied" |
| **Flag key, type, polarity, evaluation reason** | OpenFeature reason + provider status (`STALE` vs `ERROR`) |
| **Cache `Age` and CDN stale status** | SIE vs SWR vs origin 5xx |
| **Fallback invocations vs primary successes** | A rising fallback *is* the incident |
| **Flag-SDK freshness** (last successful refresh age) | Unleash 15 s / LD stream gap / LD JS 300 s poll |
| **Error-budget class** | Is this 200 *good* for availability and *bad* for freshness? |

Do not let `FORCED_OPEN` go dark: Resilience4j records **no metrics** in that state — scrape `resilience4j.circuitbreaker.state`. Do not let SIE 200s hide origin death from the burn-rate alert — scrape `Age` and the mode gauge. Business KPIs per mode: "sell anyway" is only defensible if conversion-under-degradation is a measured number.

## Tuning

| Knob | Too eager | Too reluctant | Starting point |
|---|---|---|---|
| Trigger | Users see degraded UX on blips | Degradation arrives after the outage | Same family as the load-shedding trigger (C10): tail latency or saturation, one notch earlier; SRE: keep it simple |
| Staleness bound (SIE) | Meaningfully wrong data | Errors shown while good-enough sat in cache | Per data class. RFC 1 200 s and Fastly's 12 h are *examples*, not a standard. Prices: hours. Balances / buyable SKUs: never |
| Flag polarity + default | Cold-start empty repo disables checkout | Flag service outage cannot hide a burning widget | Invert ops switches (Unleash) *or* default "feature on" + last-known. Never default a kill switch to "feature off" on a core path |
| Propagation | Browser 300 s poll as the only lever | — | Streaming server-side SDK for incident switches; Unleash 15 s is usually enough |
| Mode count | Combinatorial state space | One giant switch | Few, named, independently testable; one switch per blast radius (Unleash: resist one global parent) |
| Kill-switch hygiene | Cleanup sweeper deletes the lever | Flag sprawl | Exempt `Permanent` / LD "usually permanent"; owner + review date |

Nine rules, compressed: write the core-function list first; prefer PE for new work; prefer already-held stale over a new fallback RPC; cap SIE to a business-tolerable lie; invert ops switches *or* fail the SDK default to "feature on"; put incident switches on a streaming server-side SDK, not a 300 s JS poll; exercise the path; pair with a shed, don't impersonate one; exempt kill switches from leftover-flag cleanup. When the remaining core still overloads the box, load shedding (C10) drops requests; this card has already dropped work.

## Alternatives that beat graceful degradation

The degraded path is not always the right tool. This is the "when NOT to use it" table.

| Situation | Prefer | Why |
|---|---|---|
| The dependency *is* the product (authn, capture, a durable write you cannot buffer) | Replica promotion / failover (C3), or load shedding (C10) | No already-held bytes exist to serve; a fallback here is fabrication, not degradation |
| You have no already-held bytes and the only fallback is a weaker datastore | Failover (C3) | A stale/weaker read is a worse product decision than an honest failure |
| Message-driven flows that already dead-letter | Let the queue's own retry/DLQ handle it | Degrading the consumer path duplicates a mechanism that already exists |
| A one-off release you will delete next week | A release flag (Hodgson box), not a kill switch | Different lifetime; kill switches are Permanent and exempt from the release sweeper |
| A per-user experiment | An experiment flag | Different owner and targeting model than an incident lever |
| A permission or entitlement check | A permission flag | Different owner (security/product), not operations |
| A health-check that should fail-open | Probe design / failover (C3) | A flag flip is not a replica promotion |

## Worked calibration — ecommerce homepage

Constraints are a **design drill**, not a vendor SLA. Method: REL05-BP01 landing-page split + Hodgson recommendations toggle + RFC 5861 examples + Unleash/LD propagation + SRE ch. 22 layering.

**Core (hard).** Search box, product URL, cart, `POST /checkout` capture. Fail fast; no stale prices on SKUs that can be bought; no inverted flag that can disable capture on a flag-service blip.

**Soft (eligible).** Personalized recommendations, "customers also bought," reviews teaser, live order-status chip.

Measured recs-service caller-side latency (drill): p50 40 ms, p95 90 ms, p99.9 250 ms.

**Ladder** (cheapest / most-exercised first):

1. **Edge stale (always-on PE).** Origin: `Cache-Control: public, max-age=600, stale-while-revalidate=30, stale-if-error=1200` (RFC 5861 §3.1 / §4.1 examples). Recs fragment is cacheable GET. Cloudflare: do **not** add `s-maxage`. Fastly: do **not** also enable the 43 200 s UI switch on the same service. Varnish `default_grace` 10 s is *in addition* only if you are not sending SWR.
2. **Per-command omit (automatic GD).** Recs command: timeout 300 ms (above p99.9; timeouts, C7, own the Brooker pick). Fallback = Fail Silent empty fragment. **No** cache-via-network hop to memcached on the miss path unless memcached is the *primary* store and is hit on the success path too.
3. **Ops kill switch.** Unleash type `Kill switch`, key `disable-homepage-recs`, inverted: `false` → render; `true` → omit. Node SDK 15 s worst-case fleet lag. Alternative: LD kill-switch template, Java server SDK streaming, polarity documented as "targeting off = Disabled = widget gone." One switch per blast radius.
4. **Isolate the RPC (circuit-breaker actuator, C1).** If recs is also poisoning the BFF thread pool: Polly `IsolateAsync` / Resilience4j `transitionToForcedOpenState` / Hystrix `forceOpen=true` on that command only. Immediate, in-process; still hide the widget (step 3) so the BFF does not 500.
5. **Shed (C10), not here.** If homepage HTML itself cannot be produced, drop *requests* at the edge.

**Checkout.** No SIE on `POST /capture`. No kill switch whose default-off disables payment. A *release* flag for a new capture path may exist; its fail-safe is "old path," continuously exercised (Hystrix primary/secondary façade), not a static "payment accepted" stub. Mint the idempotency (C9) key once; reuse it on the queue replay.

**Error budget.** Homepage availability SLI counts a 200 with recs omitted as **good**. A separate freshness / personalization SLI counts SIE hits as **bad**.

**Exercise.** Weekly: force recs 500s in one canary (SRE "small subset near overload"); flip `disable-homepage-recs` in prod for five minutes off-peak; confirm omit, flat 5xx, and restore. An untested kill switch is a guess.

## Testing and operating

- **Drill on a schedule.** Force each mode in production (flags make this cheap) and verify rendering, alerts, KPIs. SRE's rule is the whole game — an undrilled degraded mode is the 2001 fallback story queued up. Twenty-years #2 / Unleash: flip in staging, then in a low-traffic prod window.
- **Game-day the levers.** Who may flip which, from where, under a control-plane brownout; measure flip-to-effect latency. A JS-only switch that polls every 300 s is not a big red button.
- **Chaos.** Fail each optional dependency (Toxiproxy, fault injection) and assert the core path's SLO holds with the rail gone. Deterministic tests: force `FORCED_OPEN` / `Isolate` and assert omit, not 5xx.
- **Keep degraded modes in the normal test matrix.** They are features with a weird activation condition. Parameter-store defaults belong in the test suite (REL05-BP01).
- **Watch recovery, not just activation.** Time-in-mode, `Age` distribution, fallback rate vs primary, flag-SDK freshness, and the freshness SLI.

## Failure modes

- **Untested fallback becomes the outage.** Gabrielson; SRE "code path you never use." Cache-down → database is the canonical story.
- **Fallback that is a hotter path.** Hystrix cache-via-network on the failure path; look-aside miss amplification (HotOS, via the circuit-breaker research, C1).
- **SIE as silent origin death.** Fastly 12 h UI; Cloudflare Workers indefinite default; OCC-disabled Cloudflare ignoring `must-revalidate`. Monitors see 200.
- **`s-maxage` + SWR.** RFC 9111 / Cloudflare: SWR disabled. Config that *looks* like stale-on-error is fail-closed.
- **Flag-system hard dependency.** `new-recs-enabled` default `false` + empty SDK repo on cold start = homepage without recs *or* without checkout if someone reused the pattern. Invert + bootstrap.
- **Polarity mix-up.** LD Enabled-when-on vs Unleash disable-when-on. On-call flips the wrong way.
- **Kill switch on the client only.** LD JS 300 s poll → the lever takes minutes.
- **`FORCED_OPEN` without a gauge.** Resilience4j stops events and metrics. **`forceClosed` / DISABLED as a "fix"** admits doomed calls.
- **Complex targeting on an incident switch.** A percentage rollout is a release flag, not a lever. Parent/child graphs: Unleash warns that one global parent is easy to misconfigure.
- **Cleanup job deletes the lever.** Permanent vs 40-day release sweeper.
- **Degraded 200 spends no budget.** Freshness SLI must exist or SIE is free.
- **Bimodal recovery.** REL05-BP07 / REL11-BP05: the lever must not require a control-plane scale-up (failover's static stability, C3). "Do LESS, not more."
- **GD used as a substitute for PE.** New surfaces should be PE; GD is the cheaper retrofit and the worse long-term maintenance.
- **Consistency core treated as soft.** Fabricated acknowledgments are data loss. A guardrail that degrades by *passing traffic through* is the same fork wearing a safety costume — decide fail-closed in peacetime.
- **Mode explosion.** Five independent binary modes = 32 states; name the few that are allowed.
- **Brownout controller as an unowned closed loop.** Optional-code inventory is the pattern; an unowned PID is not.

## Graceful degradation around LLM provider APIs

The circuit breaker (C1) decides whether to keep calling a model endpoint; retry/backoff (C2) decides whether to try the call again; timeouts (C7) bound how long an attempt may take. This card owns what the caller gets while a model call is Open, exhausted, or simply too slow to sit in the critical path — and the one place graceful degradation must refuse to improvise: the answer's content.

- **Classify the dependency first.** A model call behind an "AI summary" widget, a "customers also ask" panel, or a suggested-reply chip is soft — omit it (Fail Silent) and the surrounding page or thread still works. A model call that *is* the product's core function — a support bot with no human fallback, an agentic action that executes a side effect — is hard; fail fast or route to a human, the same REL05-BP01 test used above for the ecommerce homepage.
- **Do not stub a completion.** REL05-BP01's forbidden move is fabricating a transaction; the LLM-shaped version is a "Static / stubbed" fallback (Hystrix taxonomy) that returns *prose which looks like a real answer*. A stub is legitimate only when the caller can tell it is one — a fixed "assistant is temporarily unavailable" string, never a plausible-sounding guess standing in for the model.
- **Cheaper algorithm, not a cheaper truth.** The SRE ch. 22 "smaller index / less-accurate ranking" move maps onto a smaller or faster model tier, a non-LLM heuristic (keyword match instead of semantic search), or a cached prior answer for the *same* prompt — never the same-tier model asked to guess with less grounding than it had.
- **Stale serving has a shorter shelf life here.** RFC 5861 `stale-if-error` on a cached completion is defensible only for content that ages slowly (an FAQ answer, a generated product blurb); on anything time-sensitive or personalized it is the same REL05-BP01 fraud as a stale price on a buyable SKU.
- **The kill switch is the safety lever, not the quality lever.** An ops kill switch (Hodgson box) that disables an AI feature belongs on the same streaming, locally-evaluated flag plane as the homepage recs switch — propagation in seconds, not a client-side poll — because the trigger is usually a cost or safety incident, not a UX preference.
- **A guardrail is not a fallback.** The failure mode above applies directly: a moderation, hallucination, or policy check that "degrades gracefully" by *passing the model's output through ungated* when the checker is slow or down is a fork wearing a safety costume. Decide the guardrail's fail-open/fail-closed posture in peacetime — a consistency-critical guardrail is a hard dependency and fails closed (block, or queue for review), not an optional rail that quietly omits itself.

This card does not restate the breaker's per-signal treatment of 429/529/refusal (C1) or the time-to-first-token timers that bound an attempt (C7) — see those cards for the trip and timing criteria. What this card adds is the product answer to "the model call just failed or is Open — what does the user see," and the answer is never a fabricated one.

## Trade-offs

| Buy | Pay |
|---|---|
| Core function survives partial failure and overload | A second code path per mode, with the fallback hazard |
| Operators get levers instead of outages | Owners, polarity convention, audits, and drills |
| Smooth quality dial (brownout / omit / stale) between "all" and "down" | Product must define the quality floor, per surface |
| Stale-serving is nearly free at the cache tier | Staleness is a correctness budget; SIE 200s hide origin death |
| Invert + local eval keeps the flag plane soft | A cold-start empty repo still needs bootstrap defaults |
| The breaker's isolate (C1) is immediate and in-process | It does not hide the widget; Resilience4j `FORCED_OPEN` goes dark |

Load shedding (C10) does fewer requests; degradation does less per request; the circuit breaker (C1) decides whether to call and exposes the isolate actuator; this card decides **what the user gets**. Coordinate all four; do not treat a flag flip as failover.

## Sources

Verified 2026-09-13. The full URL list, per-claim provenance, and items deliberately left out (live Gabrielson HTML, W3C-wiki body, Brownout PDF, REL05-BP07 2022 snapshot bullets) live in the source Concept's external research notes (non-load-bearing).

- **Canon:** MDN Progressive enhancement / Graceful degradation; Hodgson, *Feature Toggles* (2017-10-09); REL05-BP01 and REL05-BP07; SRE book ch. 22 and "Twenty years of SRE lessons learned"; RFC 5861; RFC 9111 §4.2.4; Hystrix wiki How-To-Use and Configuration; Klein et al., *Brownout*, ICSE 2014 (abstract-level).
- **Flags:** LaunchDarkly kill-switch template, Java server SDK 7.15.0, JS client defaults; Unleash flag types, Node SDK, 2026-08-13 invert guidance; OpenFeature spec §01 (CNCF incubating).
- **Cache / CDN:** Fastly serve-stale (UI 43 200 s, VCL examples); Varnish 8.0.1 `default_grace` 10 s; Cloudflare cache-control (2026-06-30) and Workers cache configuration.
- **Actuators and fallback caution:** Resilience4j 2.4.0 `FORCED_OPEN`; Polly 8.7 `ManualControl` / `IsolateAsync`; Hystrix `forceOpen` / `forceClosed`; Gabrielson and the 2001 cache story via the circuit-breaker research note.
