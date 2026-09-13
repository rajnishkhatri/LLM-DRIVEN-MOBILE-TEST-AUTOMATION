---
type: reference
title: 'Graceful degradation and kill switches'
description: 'Do less per request so the core function survives a soft-dependency or overload failure: omit, static, stub, already-held stale (RFC 5861 → B8), or a cheaper algorithm. Kill switches are the product lever; C1 FORCED_OPEN is only the actuator. Covers PE vs GD, hard vs soft deps, Hodgson ops toggles, Hystrix fallback kinds, Gabrielson’s untested-fallback bugs, verified CDN and flag-SDK defaults, a homepage ladder, and drills.'
tags: [system-design-patterns, resilience, graceful-degradation, kill-switch, feature-flags]
---

# Graceful degradation and kill switches

**See also:** [load shedding](LoadShedding.md) · [circuit breaker](CircuitBreaker.md) · [failover](Failover.md) · [retry](RetryBackoff.md) · [API gateway / BFF](ApiGateway.md) · [timeouts](TimeoutsDeadlines.md) · [bulkhead](Bulkhead.md) · [idempotency](Idempotency.md) · [guardrail failure posture](../claude-certification/responsible-ai/guardrails.md) · [POC-to-production controls](../claude-certification/enterprise-integration-production/poc-to-production.md) · [reliability](../data-intensive-design/reliability.md) · [NFR references](../data-intensive-design/nfr-references.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/c11-graceful-degradation-external-research.md)

[Shedding](LoadShedding.md) drops whole requests. This pattern **shrinks the work per request** so the named core function still returns: hide a rail, serve last-good HTML, rank against a smaller index, queue a write. A kill switch is the operator interface — a long-lived ops toggle that turns a capability off *on purpose* before the system does it chaotically. Quality attributes: **availability of the core function** under partial failure, **operator agency**. Costs: every degraded mode is a second path with Gabrielson’s fallback problem — latent bugs, a product argument about “good enough,” and rot unless the path is exercised.

This card owns the **product decision** (what the user gets, which deps are soft, how stale is sellable, who may flip which switch). [C1](CircuitBreaker.md) `FORCED_OPEN` / Polly `Isolate` / Hystrix `forceOpen` are **actuators** that stop *calling* one dependency. [C3](Failover.md) owns probes, survivors, RTO/RPO, and split-brain — do not treat a flag flip as a replica promotion.

## Lineage and vocabulary

- **Progressive enhancement vs graceful degradation (web).** MDN: PE starts from a baseline every client can use and adds richness after a capability check; GD “is often seen as going in the opposite direction” — ship the full modern experience, then fall back to a still-usable essential. They complement. The *runtime* analogue is the same pair: PE = checkout never needed recommendations; GD = the homepage shipped with them and learns to hide them. New surfaces should be PE; GD is the retrofit.
- **Runtime degradation (SRE ch. 22).** Load shedding *drops traffic* (C10). Degradation “takes the concept of load shedding one step further” by reducing work: in-memory subset vs full disk index, less-accurate ranking, omit auxiliaries. Decide the **trigger** (CPU, latency, queue, threads; auto vs manual), the **actions**, and the **layer**. It “shouldn’t trigger very often”; “the code path you never use is the code path that (often) doesn’t work” — exercise by running a small subset of servers near overload; alert when too many enter the mode; keep the trigger simple against feedback loops. Store the off-switch in a watched config (their example: Chubby) *and* accept the synchronized-failure risk of that store.
- **Hard vs soft dependency (REL05-BP01).** Hard = no substitute; the caller’s availability is the product of its own and the dependency’s. Soft = the caller still performs its **core function** when the dependency is unhealthy. Ranking that split is a business decision (payments often keep consistency; a real-time app often keeps availability; a customer site follows customer expectation). Ecommerce landing page: recommendations, ranked products, and order status come from different systems — “when one upstream system fails, it still makes sense to display everything else instead of showing an error page.” Parameter store: bake defaults into the image and keep them in the test suite. Monitoring: still execute business functions if logs/metrics cannot be shipped (with a compliance caveat). Writes: buffer so the request is accepted. Anti-patterns: serving *no* data when a partial result exists; emptying local state after a failed refresh; fabricating a transaction. Failure modes of components should be treated as **normal operation**.
- **Fallback vs retry vs failover.** A fallback is a *different mechanism* for the same result. A [retry](RetryBackoff.md) is the same mechanism again. [Failover](Failover.md) is the same mechanism on a different replica (C3). REL05-BP01 closes with Gabrielson’s sentence: “Generally, fallback strategies should be avoided” — the forbidden move is an *untested second mechanism* that dumps load onto a weaker path (cache-miss → database), not omit or already-held stale.
- **Gabrielson, *Avoiding fallback in distributed systems*** (Builders’ Library; cited via the [breaker](CircuitBreaker.md) research, not re-fetched here). A “query the database if the cache is down” fallback turned a partial cache outage into a total one (the 2001 retail story). Fallbacks carry latent bugs because they run only when things are already breaking. Prefer making the primary reliable, pushing data proactively, or converting the fallback into a *continuously exercised* path. **C1 owns the breaker-modal reading; this card owns the product implication** — omit or serve bytes you already hold; do not invent a hotter path.
- **Brownout (Klein et al., ICSE 2014).** Formalizes optional-code: mark work optional and let a controller deactivate it dynamically; their RUBiS/RUBBoS retrofits cost under 170 lines. The keepable idea is the peacetime inventory of what is optional — not an unowned closed loop (the paper’s controller is not re-derived here).
- **Hodgson / Fowler, *Feature Toggles* (2017).** Four boxes: Release, Experiment, Ops, Permissioning (longevity × dynamism). Ops toggles “control operational aspects”; a small number of long-lived **kill switches** degrade “non-vital system functionality” under load — his example is disabling an expensive Recommendations panel. They “need to be re-configured extremely quickly”; shipping a release to flip one will not make operations happy. A retailer he consulted disabled many non-critical features in the purchasing flow just before a high-demand launch.
- **HTTP already has the stale primitive (RFC 5861 → [B8 CDN & edge](../../docs/research/sysdesign/system-design-patterns-catalog.md)).** `stale-while-revalidate` hides latency; `stale-if-error` hides origin 500/502/503/504. This card owns *stale-as-degradation*. B8 will own cache keys, edge acceleration, and CDN topology.
- **Hystrix fallback taxonomy** (wiki “How To Use”): **Fail Fast** (no fallback); **Fail Silent** (`null` / empty); **Static**; **Stubbed** (request-scope fields); **Cache via Network** (memcached — *itself a network call*: wrap in its own command on a **separate** [bulkhead](Bulkhead.md), else a saturated primary pool blocks the fallback); **Primary + Secondary** (façade, `DynamicBooleanProperty`, each side isolated — do not treat a routinely used secondary as a primary failure). `getFallback()` runs on `run()` failure, timeout, rejection, *and* short-circuit.
- **Emergency lever / big red button.** REL05-BP07: a rapid, *tested* process that disables, throttles, or changes a component; desired outcome is graceful continuation of business-critical functions — “do LESS, not more.” SRE twenty-years lesson #4: identify a simple revert *before* the risky change. #2: test recovery before the emergency. #7: intentionally degrade performance modes. #9: automate when the signal is clear.

## Two directions, one contract

```
PE (capability):   core HTML/checkout  ──feature detect──►  recommendations, live stock, 3-D
GD (failure):      full homepage       ──dependency fail──►  hide recs / serve stale / static merch
```

The contract is the same: **name the core function**, then list what may disappear. REL05-BP01 makes that ranking a product decision, not an SRE default. A kill switch that 500s the page has only moved the failure earlier (Unleash 2026-08-13).

Retries are not this pattern. A [retry](RetryBackoff.md) is the same mechanism again and is the usual metastable loop; Gabrielson’s last warning is retries-as-accidental-fallback. Timeouts ([C7](TimeoutsDeadlines.md)) bound the soft dependency so omit/stale can run; the Brooker pick stays there. The [breaker](CircuitBreaker.md) decides *whether to call*; fallback — what the user gets while Open — is orchestration, not a state inside the automaton.

## What you serve instead

Name the **core function** first. Everything else is eligible to omit or stale.

| Action | Caller gets | Right tool when | Hidden cost |
|---|---|---|---|
| **Fail silent / omit** | Empty list, missing widget | Additive UI (recs, reviews, related) | Clients that treat empty as “user has none” |
| **Fail fast** | Immediate error, no substitute | The result *is* the core (auth, capture, inventory decrement) | User-visible 5xx unless a higher layer degrades |
| **Static / stubbed** | In-code default or request-scope stub | Bounded, reviewable substitute | Stale *policy* (`getFallback()` returning `true` for a permission) |
| **Cached stale** | Last good response, `Age` past freshness | Read-mostly, already cached | A lie past the SIE window; masks origin death |
| **Cheaper algorithm** | Smaller index, faster rank (SRE ch. 22) | CPU/latency trigger, same schema | Accuracy SLO vs availability SLO |
| **Queue the write** | 202 / accepted | Writes that tolerate delay (REL05-BP01) | Backlog; [C10](LoadShedding.md) / [C9](Idempotency.md) own the drain |
| **Primary + secondary façade** | Secondary as a *normal* path | Secondary is exercised continuously (Gabrielson “convert fallback to failover”) | Dual-mode ops; “cry wolf” if the secondary trips the primary’s breaker |

Reads degrade more comfortably than writes. A stale read is a product decision; a lost write is an incident. Writes degrade by **deferral** (queue + key), never by fabrication. A static “charged” stub on a consistency core is fraud, not degradation (REL05-BP01 payments example).

The last two rows are where C11 and Gabrielson meet. A cache-via-network fallback is the shipping-speed story unless the cache path is **capacity-capped and continuously hit** — Hystrix is explicit that the cache command lives on a **separate thread pool**, and that the cache command’s own fallback is fail-silent `null`. Prefer serving bytes *already in the edge* (RFC 5861) over opening a new dependency when the first one is on fire. A primary + secondary façade is allowed only when the secondary is a *normal* path; treating a routinely used secondary as a primary failure trips breakers and pages (“cry wolf”).

## Kill switches: product flag, ops toggle, library isolate

Same `if` in the binary; different owner, lifetime, targeting, and failure default.

| | Product / release flag | Ops kill switch | Library force-open / isolate |
|---|---|---|---|
| **Job** | Who sees a feature | Turn a behaviour off in an incident | Stop *calling* one dependency |
| **Hodgson box** | Release / Experiment / Permissioning | Long-lived Ops Toggle (“manually-managed Circuit Breaker”) | Fowler’s operator trip/reset — the [C1](CircuitBreaker.md) actuator |
| **LaunchDarkly** | Release / experiment templates | “Kill switch”: permanent boolean, Enabled/Disabled; typically no complex targeting; may wire APM flag triggers | — |
| **Unleash** (v3.5+ types) | `Release`/`Experiment` 40 d, `Operational` 7 d, `Permission` permanent, `Sunset` 90 d | `Kill switch` — “Gracefully degrade system functionality,” **Permanent**. Type is metadata | — |
| **Default polarity** | Feature-on is usually `true` | Unleash (2026-08-13): **invert** — name `disable-recommendations`, default `false`; enabling turns the feature *off*. A `new-recs-enabled=true` flag goes dark if the SDK/cache/default is wrong | `forceOpen` / `FORCED_OPEN` / `IsolateAsync` default **off** |
| **Propagation** | Product cadence | Incident seconds | In-process, immediate |

LaunchDarkly and Unleash **disagree on polarity**. LD’s template is “Enabled when targeting on.” Unleash’s guidance is inverted so a flag-system failure leaves the feature running. Pick one convention per fleet; do not mix them on one page. An ops kill switch is **not** failover (C3) and **not** a shed of *other* URLs (C10). Isolating a Polly circuit does not hide the widget — the product path still has to omit, or the BFF 500s.

Do not evaluate the kill switch on the dependency it is supposed to kill (Unleash: backend SDKs evaluate **locally** from an in-memory repo). Do not make the flag control plane a hard dependency of checkout. OpenFeature (CNCF incubating) standardizes the evaluation API vendor-neutrally: a client **MUST NOT** throw; abnormal execution **MUST** return the supplied default. Fail-open vs fail-closed **is the default you pass**, not a global. OpenFeature does *not* mandate last-known-config; `PROVIDER_STALE` means a provider *may* keep serving cached rules. Unleash’s last-known behaviour is a vendor SDK property.

## Stale serving (RFC 5861 → B8)

This is Gabrielson-compatible: the origin is not asked for a *new* kind of work. The cache returns bytes it already has. The HotOS cache-loss loop ([breaker](CircuitBreaker.md)) is the opposite — a look-aside miss that *amplifies* origin load.

RFC 5861 (Informational, May 2010):

- `stale-while-revalidate=N` — MAY serve stale up to N seconds past freshness; SHOULD revalidate without blocking. Example: `max-age=600, stale-while-revalidate=30` → fresh 600 s, then 30 s of async stale; after that the next request blocks. Combined lifetime the origin must tolerate = max-age + SWR.
- `stale-if-error=N` — on error, MAY serve stale up to N seconds of staleness. Error = any situation that would produce **500, 502, 503, or 504**. Example: `max-age=600, stale-if-error=1200` — at Age 900 a 500 is replaced by the cached 200; past Age 1800 the error is written through.
- Stale responses SHOULD still look stale (`Age` > 0 and a warning). SWR security note: predicate background revalidation on an incoming request to avoid amplification.

RFC 9111 §4.2.4: a cache **MUST NOT** generate a stale response when `must-revalidate`, `proxy-revalidate`, `no-cache`, or an applicable `s-maxage` forbids it. `s-maxage` implies `proxy-revalidate` — **do not pair `s-maxage` with SWR** (Cloudflare documents this explicitly). Prefer already-held stale over a Hystrix cache-via-network hop on the miss path.

## Placement

| Layer | Mechanism | Typical action |
|---|---|---|
| **CDN / reverse proxy** | RFC 5861 SWR / SIE; Varnish grace; Fastly `beresp.stale_*` | Serve last HTML/JSON. B8 owns the rest of the edge. |
| **BFF / gateway aggregation** | Newman: fan-out, omit the failed backend ([ApiGateway.md](ApiGateway.md) “wishlist without stock”) | Partial page, not a 5xx |
| **Per-dependency command** | Hystrix `getFallback()` / Resilience4j / Polly fallback | Silent / static / stub |
| **Fleet flag** | OpenFeature → LaunchDarkly / Unleash / in-house | Hide widget; skip RPC |
| **Library isolate** | Hystrix `forceOpen`; Resilience4j `FORCED_OPEN`; Polly `IsolateAsync` | Fail every call to *that* dependency — then hide the feature so the caller does not 500 |
| **Emergency lever** | REL05-BP07 procedure (manual or automated) | Compose C11 hide + C10 shed; do not scale up through a sick control plane |

## Verified defaults (2026-09-13)

| Knob | Default / verified value | Trade-off |
|---|---|---|
| RFC 5861 SWR / SIE | **No numeric default** — origin sets `delta-seconds`. RFC examples: SWR 30, SIE 1200, max-age 600 | Too-small SWR → requests miss and block; too-large SIE → a day-old price |
| Fastly “Serve stale” UI | **Off** by default. UI default TTL **43 200 s (12 h)** | 12 h of silent origin death; purge-all *overrides* SIE and can stampede the origin |
| Fastly VCL example | `beresp.stale_if_error = 86400s`; `beresp.stale_while_revalidate = 60s`. **SWR overrides SIE** while SWR is open. `beresp.grace` ≡ SIE; a VCL `grace` **overrides** origin SIE headers | Example 86400 s ≠ UI 43200 s — pick one |
| Varnish `default_grace` | **10 s** (v8.0.1) — deliver after TTL expiry “provided another thread is attempting to get a new copy” | SWR-shaped, not a day-long SIE |
| Cloudflare CDN SIE | Origin **500/502/503/504** only (404 is *not* an error). Example `max-age=3600, stale-if-error=60`. Ignored if Always Online or `must-revalidate` / `proxy-revalidate` / `s-maxage` / `no-cache` / `no-store`. `stale-if-error=0` opts out | OCC-disabled: `must-revalidate` is *ignored and stale is served* |
| Cloudflare Workers cache | If SIE **unset** and no `s-maxage`/`must-revalidate`/`proxy-revalidate`: serve stale on Worker error **indefinitely** until purge | Masks Worker 5xx from monitors |
| Hystrix `forceOpen` / `forceClosed` | Both **`false`**. `forceOpen` **takes precedence**; `forceClosed` ignores error % | In-process only; `forceClosed` hides a real outage |
| Resilience4j `FORCED_OPEN` | Always deny; **no events** (except the transition) and **no metrics**. Exit via `transitionTo*` / `reset()` | Blind isolate — pair with an external state gauge |
| Polly v8 `ManualControl` | Default `null`. `IsolateAsync()` holds Isolated until `CloseAsync()`; `IsolatedCircuitException` | Isolate ≠ Open (Open still half-opens) |
| OpenFeature evaluation | MUST return the supplied **default**; no provider → no-op provider | Fail-open vs fail-closed is that default |
| LaunchDarkly Java server SDK 7.15.0 | Streaming **default**; polling opt-in, `DEFAULT_POLL_INTERVAL` **30 s** (also the minimum) | Stream ≈ seconds |
| LaunchDarkly JS client | `waitForInitialization` default **5 s**; streaming **off** unless `streaming: true` or a `change` listener; js-core poll **300 s** | A *browser-only* kill switch can lag minutes |
| Unleash Node SDK | `refreshInterval` **15 000 ms**; unreachable server → **last known** | ≤ 15 s fleet lag; cold start with empty repo needs bootstrap |

## Observability

A 200 is not a diagnosis. Emit per feature / dependency / hop:

| Signal | Why |
|---|---|
| **Degraded-mode gauge** (full / stale / omitted / isolated) | SRE ch. 22: alert when too many servers enter the mode |
| **Action taken** (`omit` / `static` / `stale` / `cheaper` / `force_open`) | Distinguishes “available” from “available because we lied” |
| **Flag key, type, polarity, evaluation reason** | OpenFeature reason + provider status (`STALE` vs `ERROR`) |
| **Cache `Age` and CDN stale status** | SIE vs SWR vs origin 5xx |
| **Fallback invocations vs primary successes** | A rising fallback *is* the incident |
| **Flag-SDK freshness** (last successful refresh age) | Unleash 15 s / LD stream gap / LD JS 300 s poll |
| **Error-budget class** | D5: is this 200 *good* for availability and *bad* for freshness? |

Do not let `FORCED_OPEN` go dark: Resilience4j records **no metrics** in that state — scrape `resilience4j.circuitbreaker.state`. Do not let SIE 200s hide origin death from the burn-rate alert — scrape `Age` and the mode gauge. Business KPIs per mode: “sell anyway” is only defensible if conversion-under-degradation is a measured number.

## Tuning

| Knob | Too eager | Too reluctant | Starting point |
|---|---|---|---|
| Trigger | Users see degraded UX on blips | Degradation arrives after the outage | Same family as the [shed trigger](LoadShedding.md): tail latency or saturation, one notch earlier; SRE: keep it simple |
| Staleness bound (SIE) | Meaningfully wrong data | Errors shown while good-enough sat in cache | Per data class. RFC 1 200 s and Fastly’s 12 h are *examples*, not a standard. Prices: hours. Balances / buyable SKUs: never |
| Flag polarity + default | Cold-start empty repo disables checkout | Flag service outage cannot hide a burning widget | Invert ops switches (Unleash) *or* default “feature on” + last-known. Never default a kill switch to “feature off” on a core path |
| Propagation | Browser 300 s poll as the only lever | — | Streaming server-side SDK for incident switches; Unleash 15 s is usually enough |
| Mode count | Combinatorial state space | One giant switch | Few, named, independently testable; one switch per blast radius (Unleash: resist one global parent) |
| Kill-switch hygiene | Cleanup sweeper deletes the lever | Flag sprawl | Exempt `Permanent` / LD “usually permanent”; owner + review date |

Nine rules, compressed: write the core-function list first; prefer PE for new work; prefer already-held stale over a new fallback RPC; cap SIE to a business-tolerable lie; invert ops switches *or* fail the SDK default to “feature on”; put incident switches on a streaming server-side SDK, not a 300 s JS poll; exercise the path; pair with a shed, don’t impersonate one; exempt kill switches from leftover-flag cleanup. When the remaining core still overloads the box, [C10](LoadShedding.md) drops requests; C11 has already dropped work.

## Worked calibration — ecommerce homepage

Constraints are a **design drill**, not a vendor SLA. Method: REL05-BP01 landing-page split + Hodgson recommendations toggle + RFC 5861 examples + Unleash/LD propagation + SRE ch. 22 layering.

**Core (hard).** Search box, product URL, cart, `POST /checkout` capture. Fail fast; no stale prices on SKUs that can be bought; no inverted flag that can disable capture on a flag-service blip.

**Soft (eligible).** Personalized recommendations, “customers also bought,” reviews teaser, live order-status chip.

Measured recs-service caller-side latency (drill): p50 40 ms, p95 90 ms, p99.9 250 ms.

**Ladder** (cheapest / most-exercised first):

1. **Edge stale (always-on PE).** Origin: `Cache-Control: public, max-age=600, stale-while-revalidate=30, stale-if-error=1200` (RFC 5861 §3.1 / §4.1 examples). Recs fragment is cacheable GET. Cloudflare: do **not** add `s-maxage`. Fastly: do **not** also enable the 43 200 s UI switch on the same service. Varnish `default_grace` 10 s is *in addition* only if you are not sending SWR.
2. **Per-command omit (automatic GD).** Recs command: timeout 300 ms (above p99.9; [C7](TimeoutsDeadlines.md) owns the Brooker pick). Fallback = Fail Silent empty fragment. **No** cache-via-network hop to memcached on the miss path unless memcached is the *primary* store and is hit on the success path too.
3. **Ops kill switch.** Unleash type `Kill switch`, key `disable-homepage-recs`, inverted: `false` → render; `true` → omit. Node SDK 15 s worst-case fleet lag. Alternative: LD kill-switch template, Java server SDK streaming, polarity documented as “targeting off = Disabled = widget gone.” One switch per blast radius.
4. **Isolate the RPC (C1 actuator).** If recs is also poisoning the BFF thread pool: Polly `IsolateAsync` / Resilience4j `transitionToForcedOpenState` / Hystrix `forceOpen=true` on that command only. Immediate, in-process; still hide the widget (step 3) so the BFF does not 500.
5. **Shed (C10), not here.** If homepage HTML itself cannot be produced, drop *requests* at the edge.

**Checkout.** No SIE on `POST /capture`. No kill switch whose default-off disables payment. A *release* flag for a new capture path may exist; its fail-safe is “old path,” continuously exercised (Hystrix primary/secondary façade), not a static “payment accepted” stub. Mint the [idempotency](Idempotency.md) key once; reuse it on the queue replay.

**Error budget (D5).** Homepage availability SLI counts a 200 with recs omitted as **good**. A separate freshness / personalization SLI counts SIE hits as **bad**.

**Exercise.** Weekly: force recs 500s in one canary (SRE “small subset near overload”); flip `disable-homepage-recs` in prod for five minutes off-peak; confirm omit, flat 5xx, and restore. An untested kill switch is a guess.

## Testing and operating

- **Drill on a schedule.** Force each mode in production (flags make this cheap) and verify rendering, alerts, KPIs. SRE’s rule is the whole game — an undrilled degraded mode is the 2001 fallback story queued up. Twenty-years #2 / Unleash: flip in staging, then in a low-traffic prod window.
- **Game-day the levers.** Who may flip which, from where, under a control-plane brownout; measure flip-to-effect latency. A JS-only switch that polls every 300 s is not a big red button.
- **Chaos.** Fail each optional dependency (Toxiproxy, fault injection) and assert the core path’s SLO holds with the rail gone. Deterministic tests: force `FORCED_OPEN` / `Isolate` and assert omit, not 5xx.
- **Keep degraded modes in the normal test matrix.** They are features with a weird activation condition. Parameter-store defaults belong in the test suite (REL05-BP01).
- **Watch recovery, not just activation.** Time-in-mode, `Age` distribution, fallback rate vs primary, flag-SDK freshness, and the freshness SLI.

## Failure modes

- **Untested fallback becomes the outage.** Gabrielson; SRE “code path you never use.” Cache-down → database is the canonical story.
- **Fallback that is a hotter path.** Hystrix cache-via-network on the failure path; look-aside miss amplification (HotOS, via [C1](CircuitBreaker.md)).
- **SIE as silent origin death.** Fastly 12 h UI; Cloudflare Workers indefinite default; OCC-disabled Cloudflare ignoring `must-revalidate`. Monitors see 200.
- **`s-maxage` + SWR.** RFC 9111 / Cloudflare: SWR disabled. Config that *looks* like stale-on-error is fail-closed.
- **Flag-system hard dependency.** `new-recs-enabled` default `false` + empty SDK repo on cold start = homepage without recs *or* without checkout if someone reused the pattern. Invert + bootstrap.
- **Polarity mix-up.** LD Enabled-when-on vs Unleash disable-when-on. On-call flips the wrong way.
- **Kill switch on the client only.** LD JS 300 s poll → the lever takes minutes.
- **`FORCED_OPEN` without a gauge.** Resilience4j stops events and metrics. **`forceClosed` / DISABLED as a “fix”** admits doomed calls.
- **Complex targeting on an incident switch.** A percentage rollout is a release flag, not a lever. Parent/child graphs: Unleash warns that one global parent is easy to misconfigure.
- **Cleanup job deletes the lever.** Permanent vs 40-day release sweeper.
- **Degraded 200 spends no budget.** Freshness SLI must exist or SIE is free.
- **Bimodal recovery.** REL05-BP07 / REL11-BP05: the lever must not require a control-plane scale-up (C3 static stability). “Do LESS, not more.”
- **GD used as a substitute for PE.** New surfaces should be PE; GD is the cheaper retrofit and the worse long-term maintenance.
- **Consistency core treated as soft.** Fabricated acknowledgments are data loss. [Guardrails](../claude-certification/responsible-ai/guardrails.md) that degrade by *passing traffic through* are the same fork wearing a safety costume — decide fail-closed in peacetime.
- **Mode explosion.** Five independent binary modes = 32 states; name the few that are allowed.
- **Brownout controller as an unowned closed loop.** Optional-code inventory is the pattern; an unowned PID is not.

**When degradation is the wrong tool.** The dependency *is* the product (authn, capture, durable write you cannot buffer). You have no already-held bytes and the only fallback is a weaker datastore. You need a replica promotion (C3) or a shed (C10). Message-driven flows that already dead-letter.

**When a kill switch is the wrong tool.** A one-off release you will delete next week (release flag). A per-user experiment. A permission/entitlement (different owner). A health-check fail-open (C3).

## Trade-offs

| Buy | Pay |
|---|---|
| Core function survives partial failure and overload | A second code path per mode, with the fallback hazard |
| Operators get levers instead of outages | Owners, polarity convention, audits, and drills |
| Smooth quality dial (brownout / omit / stale) between “all” and “down” | Product must define the quality floor, per surface |
| Stale-serving is nearly free at the cache tier | Staleness is a correctness budget; SIE 200s hide origin death |
| Invert + local eval keeps the flag plane soft | A cold-start empty repo still needs bootstrap defaults |
| C1 isolate is immediate and in-process | It does not hide the widget; Resilience4j `FORCED_OPEN` goes dark |

[Shedding](LoadShedding.md) does fewer requests; degradation does less per request; the [breaker](CircuitBreaker.md) decides whether to call and exposes the isolate actuator; this card decides **what the user gets**. Coordinate all four; do not treat a flag flip as failover.

## Sources

Verified 2026-09-13; the full URL list, per-claim provenance, and items deliberately left out (live Gabrielson HTML, W3C-wiki body, Brownout PDF, REL05-BP07 2022 snapshot bullets) are in the [C11 research note](../../docs/research/sysdesign/c11-graceful-degradation-external-research.md). First-pass C3/C11 vocabulary: [failover-degradation-external-research.md](../../docs/research/sysdesign/failover-degradation-external-research.md). Items already cited in this tree are referenced by their number in [nfr-references.md](../data-intensive-design/nfr-references.md).

- Canon: MDN Progressive enhancement / Graceful degradation; Hodgson, *Feature Toggles* (2017-10-09); REL05-BP01 and REL05-BP07; SRE book ch. 22 and “Twenty years of SRE lessons learned”; RFC 5861; RFC 9111 §4.2.4; Hystrix wiki How-To-Use and Configuration; Klein et al., *Brownout*, ICSE 2014 (abstract-level).
- Flags: LaunchDarkly kill-switch template, Java server SDK 7.15.0, JS client defaults; Unleash flag types, Node SDK, 2026-08-13 invert guidance; OpenFeature spec §01 (CNCF incubating).
- Cache / CDN: Fastly serve-stale (UI 43 200 s, VCL examples); Varnish 8.0.1 `default_grace` 10 s; Cloudflare cache-control (2026-06-30) and Workers cache configuration.
- Actuators and fallback caution: Resilience4j 2.4.0 `FORCED_OPEN`; Polly 8.7 `ManualControl` / `IsolateAsync`; Hystrix `forceOpen` / `forceClosed`; Gabrielson and the 2001 cache story via the [circuit-breaker research](../../docs/research/sysdesign/circuit-breaker-external-research.md).
