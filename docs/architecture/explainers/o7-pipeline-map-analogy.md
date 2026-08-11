# The o7 pipeline as a map: source, directions, destination — and who does each job

> **Explainer** — narrates the full o7 mobile-test-automation pipeline end to end
> through the "test as a journey" map analogy, showing the division of labor between
> LLM reasoning and deterministic algorithms/infrastructure at every stage.
>
> Grounded in: the o7 interpreter SDD spec, the o7-spine mock artifacts
> (`TestCaseIR.json`, `IRGate.report.json`, `LocatorCandidate.manifest.json`,
> `ReplayReport.json`, `ExecutionPlan.acc-2087.md`), the o1 discovery-loop and
> locator-cascade diagrams, the logical-components doc, and the ASH-Capture spec +
> deep-link sub-loop mocks (ADR 0014).

A test is a **journey**: you start somewhere (source), you follow directions to get
where you're going (navigation), and when you arrive you check whether the place matches
what you expected (destination-check). o7 takes that same three-part shape and stretches
it across the *whole* pipeline. The single most important thing to hold in your head is
this:

> **o7 splits the journey into map-*making* and map-*driving*, and it puts the LLM
> entirely on the map-making side. By the time a test is executed, the map is sealed and
> the driver is a machine that never improvises.**

That one split explains almost every design decision below.

---

## The big picture: two arms, one seam

o7 has an **authoring arm** (make the map) and a **replay arm** (drive the sealed map).
Between them sits a hard, tamper-evident seam — the moment the map is **committed** and
gets a content fingerprint (`irDigest`).

- **Authoring arm** = surveyors drawing the map. This is where world-knowledge lives,
  where things are fuzzy, where the LLM earns its keep.
- **The commit seam** = sealing the finished map into an envelope. From here the map
  *is* the executable — there's no separate "compile the directions" step, because in o7
  the map itself is what gets driven.
- **Replay arm** = a machine driver following the sealed map turn-by-turn. **Zero LLM.
  Zero improvisation. Zero self-heal.** If a landmark doesn't match, the trip hard-fails
  — the driver does not invent a detour.

Here's the whole pipeline, in order, with the map role of each stage:

| # | Stage (real o7 name) | Map role | Who drives it |
|---|---|---|---|
| 1 | **Ingest Test Sources** | Read the list of trips people want to take (Excel, Octane) | Deterministic adapters |
| 2 | **Interpret Test Intent** (normalizer) | Turn a vague note into a precise itinerary | **LLM** |
| 3 | **ASH-Capture discovery** | Survey the actual roads, draw the map (ScreenGraph) | **LLM proposes**, deterministic executor drives |
| 4 | **Resolve Elements** (locator cascade) | Write down how to recognize each landmark | Deterministic first, **LLM fallback** |
| 5 | **Commit** (`irDigest`) | Seal the map into a fingerprinted envelope | Deterministic (auto-commit) |
| 6 | **IR gate** (7 checks) | Pre-departure checklist against the sealed map | Deterministic |
| 7 | **Enqueue** (outbox) | Drop the trip order in dispatch, exactly once | Deterministic |
| 8 | **Interpreter execution** | Machine driver follows the sealed itinerary | **Deterministic, LLM-free** |
| 9 | **Classify outcome** | Stamp a standard reason-code on the result | Deterministic lookup |
| 10 | **ReplayReport + execution-plan** | File the official trip record | Deterministic |
| 11 | **Certification verdict** | A human inspector signs off, after the fact | **Human** (LLM barred here) |

---

## Where the LLM does the heavy lifting (the authoring arm)

### Stage 2 — Reading the destination out of a vague note

A manual test says something like *"send $25 to a saved Zelle recipient and see the
confirmation."* That's a hand-written note, not an itinerary. The **normalizer** uses the
LLM exactly the way world-knowledge should be used: it knows banking apps are closed
systems, that Zelle lives under a payments/transfers area, that you confirm on a final
screen. It turns the note into a **structured itinerary** — an ordered `TestCaseIR` with
control flow and step dependencies.

Crucially, when it's *unsure* (which recipient? which account?), it doesn't guess
silently — **it flags the ambiguity as an explicit field** and routes it to a human.
That's the design principle throughout: *the LLM reasons under uncertainty, but
uncertainty is made visible, never hidden.*

### Stage 3 — Surveying the roads (the greedy discovery loop)

This is the "discover in-between locations while navigating" idea. In o7 it's
**ASH-Capture**, and it's a clean division of labor:

- **`svc-ash-proposer` (LLM)** looks at the current screen (an ObservationPacket) and
  **proposes up to K=3 candidate next actions, ranked by confidence.** This is the LLM's
  world-knowledge saying *"to reach the account balance, tap the thing that looks like
  'Accounts'."* The LLM **proposes navigation — it never touches the device and never
  writes to the map.**
- **`svc-ash-executor` (deterministic)** is the only thing that actually drives the
  device and the **only writer** to the map. It captures the screen, validates the
  proposed action against allowlists, and records what it found.

That's the **greedy loop**: `DUMP → PROPOSE → VALIDATE → EXECUTE → CHECK`. It's greedy in
the precise algorithmic sense — it takes the single best-confidence survivor at each
step, **doesn't backtrack**, and stops when it exhausts a budget (3 no-progress strikes,
≤15 actions, ≤60s/step, 10-minute cap) into a **human escape hatch**. The map it builds
is the **ScreenGraph** — screens as nodes, transitions as edges — persisted in Postgres
and **reused across tests**. This is the database that grows toward the ">90% coverage"
hypothesis: LLM world-knowledge seeds it, user-provided manual steps feed it, and greedy
discovery fills the gaps.

#### Deep links — the shortcut/teleport in the map

Not every screen has to be reached by tapping through the app. Many banking apps expose
**deep links** — special URLs like `erica://zelle/send` that jump straight to a screen. In
map terms a deep link is a **teleport**: it lands you on the destination without the
turn-by-turn drive. When one exists it's the cheapest way to arrive, so the ScreenGraph
records it as the cheapest edge: **`DEEP_LINK=1 < SCROLL/TAP=2 < TYPE=3`**.

Two disciplines keep this safe:

- **Discovered, never invented.** o7 only ever finds deep links the app *already*
  supports. An LLM may *propose* candidate URLs **within the app's real scheme**, but a
  deterministic probe must confirm each one actually lands on the target screen (full
  arrival table, strict thresholds) before it's saved as a `DEEP_LINK` edge with
  `provenance=DEEP_LINK_PROBE`. It never guesses a new scheme.
- **Deny-by-default allowlist, re-checked three times.** A proposed URL must exactly
  match a committed allowlist entry — no query strings, no pattern syntax. It's checked
  at proposal time (validator rejects → `REJECTED_URL`), again by the executor before
  `launchDeepLink()` (independent re-check → quarantine, **F11**), and again by the graph
  loader against the *current* allowlist version (load-time quarantine). Nothing outside
  the sanctioned list can fire.

**Honesty split (this is important):**

- ✅ **Accepted (ADR 0014):** the *cost model* (deep link = cheapest edge) and the
  *deny-by-default allowlist* safety design. The earlier known gap (probe had no URL
  denylist) is **closed** by that allowlist.
- 🟡 **Proposed / unratified sub-loop (ADR 0014):** the *discover → propose → probe* loop
  that actually finds new deep links. The mock prompt header literally says *"This is an
  unratified design."*
- ⛔ **Not in o7 today:** deep links in the **sealed replay run**. The o7 interpreter
  spec has **zero** deep-link references; the `NAVIGATE` opcode is whitelisted but unused
  in the Zelle test. The machine driver never teleports during a run — deep links live
  entirely in **map-making**.
- 🔮 **Deferred future work:** *parameterized* deep-link templates (links with
  parameters) — explicitly the "single sanctioned growth path," decided later.

Because deep links are *why* some edges cost 1 and others cost 2–3, they're directly tied
to the shortest-path (Dijkstra) proposal below: an optimal router would automatically
prefer the cost-1 teleport over a long tap-by-tap route.

### Stage 4 — Writing down how to recognize each landmark (the locator cascade)

For every stop, o7 records **how the driver will later recognize the landmark** — and
here the LLM is deliberately kept as a *last resort*. The cascade tries sources in a
**fixed priority order**:

1. `OBJECT_REPO` — known good locator (deterministic)
2. `PAGE_SOURCE` — Appium's `getPageSource()` dump (deterministic)
3. `OBJECT_SPY` — Perfecto element inspection (deterministic)
4. `VLM` — a vision model confirms the element is visually there (**LLM**)
5. `LLM-guess` — a model proposes a strategy from the tree text (**LLM**)

The model calls (4–5) are reached **only when every deterministic source falls below a
confidence floor (0.85)**. And even the LLM-guess is disciplined: it returns `NO_MATCH`
rather than inventing an element that isn't there.

This is the general pattern of the whole authoring arm: **deterministic where you can,
LLM where you must, confidence-gated so the model is the exception, not the default.**

---

## The seam: sealing the map (Stage 5)

Everything above is fuzzy and revisable. Then comes the **commit** — the fork boundary.
The `TestCaseIR` plus its `LocatorCandidate` manifest get **auto-committed** by a service
principal (`svc:conversion-pipeline`) and stamped with **`irDigest` = a SHA hash of the
canonical map.**

Two things make this the pivot of the whole design:

- **The committed map *is* the executable.** There's no code generation, no
  `LoginTest.java`. o7 deleted the codegen stage. The sealed JSON map is what runs. (This
  is the o7-vs-o1 fork: o1 generated Java; o7 interprets committed data.)
- **From here, nothing is fuzzy again.** The fingerprint means the exact map that was
  reviewed is the exact map that runs, byte-for-byte, and any later report can be
  re-derived and re-run at that SHA.

---

## Where deterministic algorithms and infrastructure take over (the replay arm)

Now the map is sealed, and the reason to hand off to deterministic machinery is simple:
**anything that must be correct, cheap, and repeatable should never depend on a model's
live output.** o7 is almost fanatical about this.

### Stage 6 — The pre-departure checklist (IR gate)

Before *any* device is acquired — zero device cost, zero compilation — a **deterministic
gate runs seven checks** on the sealed map:

1. `schemaValid` — the itinerary parses
2. `opcodeClosed` — only legal moves (`TAP, TYPE, SWIPE, WAIT, ASSERT, LAUNCH, NAVIGATE`)
   and legal checks (`TEXT_EQUALS, ELEMENT_PRESENT, VALUE_CHECK`)
3. `boundedWaits` — every stop carries a finite `timeoutMs` (no infinite waits)
4. `locatorManifest` — every landmark referenced is on the recognition sheet (no orphans)
5. `noLiteralCreds` — no secrets scribbled in the margin (vault references only)
6. `ambiguityClear` — no ambiguous stop survived
7. `dryRun` — a no-device paper walk of the whole route succeeds

This is deterministic *because it has to be*: it's the correctness substrate that makes
it *safe* to have removed the human pre-commit review. A checklist you can trust is one
that gives the same answer every time.

### Stage 7 — Dispatch exactly once (transactional outbox)

The approved trip goes into a queue via a **transactional outbox** with an **idempotent
consumer** — so even if the order is handed to dispatch twice, **exactly one car is
dispatched** and you never double-spend device minutes. Pure infrastructure correctness;
no room for a model here.

### Stage 8 — The machine driver (the interpreter — the core of o7)

The **version-pinned interpreter** (a Spring Boot module, its own Git SHA as
`interpreterVersion`) acquires a real device from a pinned Perfecto pool and **walks the
sealed itinerary step-by-step over Appium (`java-client 10.x`).** For each stop it:

- tries the committed locator cascade **in the committed order** (primary
  `ACCESSIBILITY_ID`, then the one committed fallback like an XCUITest `XPATH`),
- honors that stop's `timeoutMs` and `syncAfter` (e.g. wait-for-idle after a tap),
- and **never searches for, generates, or adapts a locator** — `healPolicy` is fixed to
  `NONE`.

If the committed cascade is exhausted with no match, that's a **hard fail**
(`LOCATOR_NOT_FOUND`), a red build. **The driver does not improvise.** o7 even goes a
step further and forces `cloudAdaptivityDisabled=true` per session — because modern
Perfecto/BrowserStack inject their *own* cloud-AI self-heal into Appium runs, and o7
attests it OFF or quarantines the session. The whole point of sealing the map was to make
the drive deterministic; letting the cloud silently "fix" a locator would break that
guarantee.

**This is the deepest expression of the map analogy:** the directions were figured out
(with LLM help) at map-making time; at drive time, following them must be mechanical, or
the test isn't measuring what you think it's measuring.

### The destination-check, made deterministic (a thread through stages 3 & 8)

The third map part — "is the criterion present at the destination?" — shows up twice, and
both times it's **deterministic**:

- **Did we arrive on the right *screen*?** o7 compares a **signature triad** against the
  stored signature: `titleAnchor` (the screen's accessibility title), `skeletonHash` (a
  hash of sorted `(elementType, accessibilityId)` tuples — deliberately *excluding* text
  so dynamic content doesn't break identity), and `DES` = `accessibilityId` overlap,
  thresholded (τ=0.6/0.8). Two settle-dumps ≥1s apart avoid mistaking a still-loading
  screen for arrival. **This is a pure function** — same inputs, same verdict, every time.
- **Did the *test criterion* pass?** The `ASSERT` steps — e.g.
  `TEXT_EQUALS "$25.00 sent to Alex Rivera"` on the confirmation banner — are exact
  deterministic checks.

No model decides whether you arrived. Arrival is math.

### Stages 9–11 — Reason-code, record, and the human stamp

- **Classify (9):** a **rule-based lookup** maps Appium exceptions and Perfecto failures
  into a fixed **seven-class taxonomy** (`LOCATOR_NOT_FOUND, STALE_ELEMENT, TIMEOUT_SYNC,
  ASSERTION_MISMATCH, APP_CRASH, DATA_PRECONDITION, ENV_INFRA`). No learned classifier —
  a pre-printed list of seven boxes. Infra failures re-queue with bounded backoff; they
  never count against the test.
- **ReplayReport (10):** the official record, pinned with `irDigest` +
  `interpreterVersion`, plus a human-readable execution plan **rendered deterministically
  from the fingerprint** — evidence only, never the authoritative record.
- **Certification (11):** the machine PASS is only a *precondition*. An **accountable
  human** signs the verdict, post-run. Fully-autonomous certification is **barred** — the
  one place a model is *forbidden* by design.

---

## The scorecard: LLM vs deterministic, and *why* each got its job

| Concern | Owner | Why it's assigned there |
|---|---|---|
| Turn messy free text into an itinerary | **LLM** | Needs world knowledge & language understanding — irreducibly fuzzy |
| Propose the next screen to explore | **LLM** | World knowledge of how apps are structured; the 60–70% base coverage |
| Locator fallback grounding (VLM / guess) | **LLM** | Only when deterministic sources fail — reasoning about unseen UI |
| Deterministic locators (repo/page-source/spy) | **Deterministic** | Exact, cheap, repeatable — no reason to ask a model |
| Screen-arrival check | **Deterministic** | Must be identical every run — a pure signature function |
| Sealing the map (commit + `irDigest`) | **Deterministic** | Integrity/audit — hashing, not judgment |
| IR gate (7 checks) | **Deterministic** | Correctness substrate; must be trustworthy and free |
| Dispatch exactly once | **Deterministic** | Transactional guarantee; models can't provide one |
| **Driving the sealed map on-device** | **Deterministic** | The core bet: repeatable execution ≠ live model output |
| Runtime self-heal | **Excluded** | Structurally barred — would break determinism |
| Failure classification | **Deterministic** | Fixed taxonomy lookup — same rules as the old TestNG runner |
| Final certification | **Human** | Accountability; autonomous sign-off is barred |

The rule underneath the whole table: **the LLM is confined to the map-making arm,
upstream of the seal. Downstream, everything is deterministic, pinned, and re-runnable.**
That's what lets o7 claim its correctness properties — you can re-run any report at its
exact SHAs and get the same answer, precisely because no model is in the replay loop.

---

## What the classical algorithms actually are here — and what could be added

Separating *present* from *proposed* honestly: **o7 today uses several deterministic
algorithms, but the graph-*search* family (Dijkstra/A*/BFS/DP) is not actually
implemented — the ScreenGraph has weighted edges but nothing computes optimal paths over
them yet.**

### Present in o7 today

- **Greedy search** — the discovery loop (Stage 3): best-confidence candidate, no
  backtracking, budget-bounded.
- **Fixed-order ranked fallback** — the locator cascade. The order is *frozen at commit*,
  so at runtime it's a deterministic sequence, **not** a live search.
- **Deterministic signature-match predicate** — the arrival/destination check.
- **Content-addressed hashing + hash-chaining** — `irDigest`, lineage integrity,
  hash-at-pull.
- **Optimistic concurrency (advisory lock + CAS rebase)** — for safe ScreenGraph commits.
- **Idempotent-consumer / exactly-once** — over the outbox.
- **Rule-based table lookup** — failure classification.

### Proposed (grounded, but not currently there)

All strictly in the authoring/replan arm, **never in the replay walk**:

- **Dijkstra / weighted shortest-path over the ScreenGraph.** The graph *already has* edge
  cost weights (`DEEP_LINK=1 < TAP/SCROLL=2 < TYPE=3`) and a verified-preferred rule — but
  no algorithm consumes them. A real shortest-path search at authoring time would turn
  those weights into an *optimal* committed navigation path: shorter, cheaper, more robust
  maps, chosen deterministically. **This is the single highest-value add** because the
  substrate is already in place.
- **The deep-link discovery sub-loop (ADR 0014, unratified).** The loop that *finds* new
  shortcuts: an LLM proposes candidate deep-link URLs within the app's real scheme, a
  deterministic probe confirms arrival, and only confirmed links are committed as cost-1
  `DEEP_LINK` edges. The safety design around it (discovered-not-invented; deny-by-default
  allowlist re-checked 3×) is settled; the loop has an accepted design but is **not yet
  ratified**. Adds shortcuts to the map only — never launches one in the sealed run.
- **Prefer shortcuts when routing.** Once shortest-path routing and the deep-link sub-loop
  both exist, the router would automatically favour a cost-1 deep-link teleport over a
  long tap-by-tap path — shorter, less fragile committed routes. Stacks on the two ideas
  above, so it's the furthest from decided.
- **A\*** — the same path-planning with a heuristic (e.g. signature-similarity between
  current and target screen) to prune search on large apps. Weaker grounding (no heuristic
  is defined yet), but a natural extension of Dijkstra.
- **Dynamic programming / memoized path cache.** The ScreenGraph already acts as a
  *de-facto* cache (the "~90% take the graph-search happy path" claim). Making the
  memoization explicit — best-known sub-path per `(root, target)` — turns "cache-hit vs
  re-discover" into a principled decision with optimal substructure.
- **BFS/DFS systematic traversal** for *coverage-guaranteed* discovery, as a complement to
  greedy. Greedy drains its budget into the human hatch on hard screens; a systematic
  frontier gives completeness guarantees. Trades LLM flexibility for exhaustiveness —
  worth it for a coverage push toward the >90% goal.
- **Topological sort of IR steps inside `dryRun`.** Right now `dryRun` is "a structural
  walk"; modeling step dependencies as a DAG and topologically validating it would give
  the gate a *precise* property — no cyclic/unsatisfiable ordering ever reaches a device.
- **Deterministic critic + bounded repair** (from the earlier POC brainstorm) — at
  authoring time only, to fix mechanical IR defects (missing `timeoutMs`, orphan locator)
  *before* commit, reducing gate rejections. **Hard constraint:** it must live upstream of
  the seal; the replay path structurally forbids repair (`healPolicy NONE`).

The load-bearing caveat on every proposal: **the replay arm is a linear walk of committed
data with no search, by design. All of these graph/search/repair ideas belong to
map-*making*, never map-*driving*.** That boundary is the thing that makes o7 o7.

---

## Grounding notes / open items to verify

This is built from reading the actual o7 spec, the o7-spine mock artifacts (the
`$25`-to-Alex-Rivera Zelle test runs through it), the discovery-loop and locator-cascade
diagrams, the logical-components doc, and the TestCaseIR/ReplayReport/IRGate JSON. A few
things flagged as **verify-before-publishing**:

- **`irVersion` naming:** the mock IR carries a field literally named `irVersion` (whose
  value *is* the `irDigest`), but the re-based F6 rule says o7 rows must carry *neither*
  `codeCommit` *nor* `irVersion`. Either the schema forbids the *name* (mock is
  non-conformant) or only forbids a *separate* pin. Worth resolving against the re-based
  schema.
- **Locator count:** the gate reports "10/10 locators, 0 orphans," but the manifest lists
  11 candidate objects (the step-7 XPATH fallback is the 11th). Likely "10 logical
  locators, one with a 2-entry cascade" — but confirm.
- **"Appium" is never written in the spec prose** — the driver layer is vendor-neutral
  (`DeviceSession.act()`, `pageSource`, Object Spy) with Perfecto as the cloud; only the
  mock names `XCUITest 9.4.0` / `Appium 2.19`, while the spec's target table says
  `java-client 10.x`. Minor version-line mismatch to nail down.
- **TechStack.md has zero mobile-automation content** — the Appium/iOS/Android grounding
  comes entirely from the specs and mocks, not the platforms doc.

---

*Next step (planned): render this as a visual artifact — the "map-making vs map-driving,
LLM vs deterministic" split as an annotated pipeline diagram.*
