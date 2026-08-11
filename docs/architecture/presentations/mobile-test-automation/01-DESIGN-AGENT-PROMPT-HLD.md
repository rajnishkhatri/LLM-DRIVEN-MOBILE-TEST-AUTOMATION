---
type: design-agent-prompt
title: Shared Spine HLD — Three-Audience PPTX Presentation Prompt
description: Design-agent prompt that instructs an agent to produce a three-audience PowerPoint presentation of the Mobile Test Automation Weeks 0–3 Shared Spine high-level design. Content is handed over as an artifact folder (deck markdown + four rendered diagrams + detail tables); the agent reads the files and never re-decides or invents facts.
tags: [design-agent, mobile-test-automation, spine, hld, pptx, chief-architect, delivery-manager, developers, anti-slop]
source: docs/architecture/presentations/mobile-test-automation/ (spine-design-pack.md + P1–P4 renders + view/detail files)
---

# Design-Agent Prompt — Shared Spine HLD Three-Audience PPTX Presentation

## What you're building

One PowerPoint file — `Shared Spine HLD — Three-Audience Presentation.pptx`
— that presents the **Mobile Test Automation Weeks 0–3 Shared Spine
high-level design** to three audiences simultaneously: **Chief Architect**
(the shape, the decisions, the enforcement), **Delivery Manager** (scope
fence, roadmap, week-0 asks), and **Developer** (the repo, the rules of the
road). The three-audience framing lives in the **speaker notes** of every
slide — one notes panel with three labeled sections, so a presenter reads
the room and uses the right frame.

It is a buy-in deck for a ~45-minute stakeholder walkthrough — not a spec,
not a training manual. The design is **already decided and gated**; the deck
markets a done decision set and asks each audience for one concrete action.
The deliverable is the `.pptx` itself; how you produce it (python-pptx,
Node, manual XML, whatever) is your choice. The constraints below govern
the deck, not the toolchain.

> **Terminology rule.** Never surface internal process identifiers on slide
> titles, body text, or speaker notes: `EARS`, `SDD`, `SKILL.md`, stage
> numbers of the authoring workflow ("stage-2 component analysis" → "the
> component analysis"), approval tokens (`PLAN-OK`, `TASKS-OK` → "plan
> approved 2026-07-28", "task-list approval"), bare carry-forward codes
> (`CF1–CF11` → "the eleven carry-forward rules"), and bare mitigation
> codes (`M16` → "the real-workbook corpus request"). Translate each into
> plain language.
>
> **Allowed verbatim** (they appear on the diagram canvases or are the
> system's real vocabulary): module names (`spine-contracts`, `screening`,
> `conversion`, `validation-certification`, `evidence`), record names
> (`TestCaseIR`, `LocatorCandidate`, `ReplayReport`), fitness-function IDs
> F1–F4, work packages WP0–WP7, ADR numbers (spell out "architecture
> decision record" on first use), vendor/product names (Perfecto, ALM
> Octane, Excel, PostgreSQL, MinIO, Spring Boot, Maven, Appium),
> `REAL_INGESTED`, `NOT_APPLICABLE`, `Thread.sleep`.

## Constraints

1. **One `.pptx` file.** Opens cleanly in PowerPoint, Keynote, and Google
   Slides. No external dependencies to view it — the four diagram PNGs are
   embedded in the file, not linked.
2. **16:9 aspect ratio.** Slide dimensions 13.33" × 7.5" (or the equivalent
   EMU value your toolchain uses). Do not default to 4:3.
3. **Action title on every slide — section headers included.** A complete
   sentence that states a conclusion (has a subject and a verb; states a
   claim, not a category). Example of failure: "The Architecture". Example
   of pass: "One deployable with three cluster modules and exactly two
   async seams is the whole architecture." Section-header titles carry
   their section's mini-Complication — the tension the section resolves —
   so each section opens a fresh attention cycle. Sole exception: Slide 1's
   deck title may be a name.
4. **Titles Test (preflight).** Before building any slide, draft all 18
   titles as an ordered list and verify they convey the complete argument
   on their own. Only once the titles pass the test do you build the
   slides. The titles list is the first artifact; emit it as `TITLES.md`
   alongside the `.pptx`.
5. **Speaker notes format** on every slide (three-section, labeled):
   ```
   [Chief Architect] <framing for the chief architect>

   [Delivery Manager] <framing for the delivery manager>

   [Developer] <framing for developers>
   ```
6. **Clean design.** Define a `PALETTE` (in your toolchain or as a comment
   in `COVERAGE.md`): Chief Architect `#F59E0B` (amber), Delivery Manager
   `#10B981` (green), Developer `#3B82F6` (blue). Warning color: `#EF4444`
   (red) for risk/gate-slip content. Neutral background: `#F8FAFC`. Table
   header rows use a dark neutral fill with white text; body rows alternate
   neutral and white. Do not scatter hex codes — centralize the palette.
   Do NOT restyle or recolor the diagram PNGs — they carry their own
   deliberate visual system.
7. **Slide-number footer** on every content slide (not section headers,
   not the title slide): bottom-right, 9pt, neutral color.
8. **No duplication.** If your toolchain is code-based, define helpers for
   repeated slide shapes (image slide, table builder, notes formatter). Do
   not inline the same shape-drawing logic more than once (5-line clone
   tripwire).
9. **Circuit breaker.** If a slide cannot be built from the handover
   artifacts without fabricating a fact, emit a placeholder slide titled
   `TODO: <what's missing>` and flag it in `COVERAGE.md`. Three failed
   attempts at the same slide = placeholder + flag, not a fourth
   variation. Never fill a gap from memory or general knowledge — the
   handover folder is the only source of truth.
10. **PDF-export safe.** The deck must export cleanly to PDF via
    PowerPoint's File → Export — no content cut off, no missing glyphs.
    Avoid emoji as semantic markers (rendering varies by OS); prefer filled
    shapes or unicode symbols with broad font coverage.

================================================================
== HANDOVER — THE ARTIFACT FOLDER                             ==
================================================================

Everything you need is in **one folder**:

```
docs/architecture/presentations/mobile-test-automation/
```

You read files; you never re-derive, re-decide, or supplement from memory.
The design was gated upstream (spec signed off 2026-07-27, plan approved
2026-07-28, thirteen architecture decision records); this deck is a
communication artifact of that baseline, and so is your `.pptx`.

### What each artifact is authoritative for

| Artifact | Role in your build |
|---|---|
| `spine-design-pack.md` | **The sole content source.** A 14-page deck-style walkthrough; every fact on every slide traces to a page of this file. Page numbers cited in the slide structure below refer to its `## N ·` headings. |
| `p1-spine-context@2x.png` | Slide image — the spine in one picture (context view). Place as-is. |
| `p2-module-map@2x.png` | Slide image — six Maven modules, one deployable (module map). Place as-is. |
| `p3-replay-flow@2x.png` | Slide image — a committed test's journey to the week-3 gate (replay flow). Place as-is. |
| `p4-delivery-roadmap@2x.png` | Slide image — eight work packages to the gate (delivery flow, not an architecture view). Place as-is. |
| `p1/p2/p3-*.view.md` | Numbered node/edge tables matching the `[n]` markers on each canvas, plus honesty flags (UNKNOWN SLAs, working assumptions). **Speaker-note depth only — never slide body.** |
| `p1/p2/p3-*-detail.md` | Extended captions per view. Speaker-note depth only. |
| `SELF-AUDIT.md` | Diagram provenance and lint results. Background reading; not slide content. |

**Ignore entirely:** `00-DESIGN-AGENT-PROMPT.md` (a different deck's
prompt), `spine-design-pack-standalone.md` (a generated duplicate of the
deck), `ir/`, `proofs/`, `*.d2`, `*.svg`, `build_standalone.py` (diagram
toolchain internals).

### Rules for using the artifacts

- **Images go on slides unmodified.** The `@2x` PNGs are render-final:
  crisp at full-slide width, deliberate palette, grayscale-safe. Scale
  proportionally to the largest size that fits under the title; never
  crop, recolor, annotate over, or redraw them.
- **Honesty tags must travel.** Each `view.md` carries an export caveat:
  off-canvas honesty flags (e.g. Perfecto SLA UNKNOWN, PostgreSQL as a
  working assumption, object storage probe-pending) do not travel with a
  bare image. On every slide that places a PNG, copy the relevant honesty
  flags from that view's `view.md` into the speaker notes. The open-items
  table (deck page 7) additionally surfaces them on a slide body — that
  slide is mandatory.
- **Facts are verbatim.** Numbers (43 tasks, eight work packages, thirteen
  ADRs, three promises, four fitness functions, two gate clauses, five
  week-0 asks) come from `spine-design-pack.md` exactly. If you cannot
  find a number there, it does not go on a slide.
- **The deck re-decides nothing, and neither do you.** If two artifacts
  seem to disagree, `spine-design-pack.md` wins for slide content; flag
  the discrepancy in `COVERAGE.md` instead of resolving it yourself.

================================================================
== SLIDE DECK STRUCTURE (18 slides)                           ==
================================================================

> **Attention-cycle structure.** Section 1 (Slides 3–6) models the full
> Mini-Situation → Mini-Complication → macro Question → Mini-Answer cycle
> explicitly. Sections 2–4 each open a fresh cycle through their section
> header: the header title states the section's mini-Complication (the
> tension), and the section's content slides deliver the mini-Answers
> (claim titles) with evidence after each answer, never before. A section
> whose header fails to state a tension is flat-lined and must be
> re-titled.

Each entry maps to one slide. `layout` is a hint (Title Slide / Section
Header / Title and Content / Picture with Caption / Title Only + shapes);
use whatever your toolchain provides that fits. `source` names the
`spine-design-pack.md` page(s) the body content comes from.

### Section 0 — Title

**Slide 1** (layout: Title Slide)
- Title: `The Shared Spine — Mobile Test Automation, Weeks 0–3`
- Subtitle: `One Deployable, Three Promises, a Two-Clause Gate — Rails Built Before Any Train Runs on Them`
- Source: page 1 (cover) and page 2's one-sentence keeper.
- Notes:
  [Chief Architect] You leave confirming this pack faithfully represents the gated baseline — nothing here re-decides anything.
  [Delivery Manager] You leave with five week-0 asks — the only thing between this plan and its gate.
  [Developer] You leave knowing the repo you'll live in and the rules the build enforces from commit one.

---

### Section 1 — Why this exists (everyone)

**Slide 2** (layout: Section Header)
- Title: `Everything after week 3 depends on a spine that does not exist yet.`
- Source: page 2.
- Notes:
  [Chief Architect] The next four slides state the premise, the picture, the finish line, and the three promises — the shared ground before your section.
  [Delivery Manager] The next four slides define what "done by week 3" means — the gate your calendar serves.
  [Developer] The next four slides are the context for every rule in your section — why the rails come before any train.

**Slide 3** (layout: Title and Content) — Mini-S + Mini-C
- Title: `Both delivery phases consume the same four foundations — so the spine must be right from the first commit.`
- Body (from page 2):
  - Phase 1 (weeks 3–8) converts manual tests with AI assistance; Phase 2
    swaps the reasoning engine. Both consume the same four things: the
    schema contracts, an ingestion path, a device-evidence tool, and a
    deterministic replay pipeline.
  - The load-bearing premise: Phase 1 is not a throwaway prototype — it is
    the asset factory and data flywheel for Phase 2. That holds only if
    the spine is built with the decided architecture from the first commit.
  - So weeks 0–3 build the spine, and only the spine — in a new Spring
    Boot repository, with module boundaries, append-only provenance, and
    fitness functions in place from commit one.
- Closing line (visually distinct — larger, centered, below the bullets;
  the one sentence the deck asks everyone to keep): *We are building the
  rails before any train — human or AI — runs on them.*
- Notes:
  [Chief Architect] The premise is architectural: if the spine ships without the decided boundaries, Phase 2's engine swap becomes a rewrite, not a config change.
  [Delivery Manager] Three weeks of spine is what makes weeks 3–8 an asset factory instead of a prototype you later pay to replace.
  [Developer] "Only the spine" is a scope promise to you too — no LLM integration, no UI, no healing loops in this window.

**Slide 4** (layout: Picture with Caption) — P1, the spine in one picture
- Title: `One system turns manual tests and device evidence into auditable verdicts — with no LLM call anywhere.`
- Body: `p1-spine-context@2x.png` at maximum proportional size. One caption
  line below (from page 3): manual tests arrive from Excel workbooks and
  ALM Octane; device evidence from the Perfecto lab; everything leaves a
  lineage row (PostgreSQL) and hashed evidence (object storage).
- Callout (small, distinct fill): **"No LLM call anywhere" is a design
  fact enforced by a CI rule — not an aspiration.**
- Source: page 3; honesty flags from `p1-spine-context.view.md`.
- Notes:
  [Chief Architect] The numbered markers have engineer-grade backing — every node and edge on this canvas traces to a decision record. Honesty flags carried from the source view: Perfecto and Octane SLAs are UNKNOWN pending probes; PostgreSQL is a working assumption; object storage is probe-pending with a MinIO default.
  [Delivery Manager] Two external dependencies on this picture — Perfecto and Octane — are exactly the access asks in your section.
  [Developer] The system box is one Spring Boot deployable; you'll see its internal module map in your section.

**Slide 5** (layout: Picture with Caption) — P3, the week-3 gate
- Title: `The finish line is two binding clauses: a real test replayed end to end, and real source material ingested.`
- Body: two short clause statements above or beside `p3-replay-flow@2x.png`
  (from page 4, verbatim in substance):
  - **(a)** One hand-written Appium test flows end to end — static gate,
    real Perfecto device, classification — yielding a `ReplayReport` that
    validates against the committed schema with a complete pinning set.
  - **(b)** The ingestion CLI has produced schema-valid, screened IR from
    real source material — recorded `REAL_INGESTED` in lineage.
    Fixture-only green does not count.
- Caption line: static gate first — seconds, zero device cost — then the
  queued device gate, then rule-based classification; every hop writes
  append-only lineage.
- Source: page 4; honesty flags from `p3-replay-flow.view.md`.
- Notes:
  [Chief Architect] The gate exercises a hand-written test deliberately — the pipeline is proven before any generated code reaches it. Honesty flags from the source view travel here: device SLA and gateway contract remain probe-pending.
  [Delivery Manager] Clause (b)'s floor is set when the real-workbook corpus returns — blocked honestly, never guessed. That corpus request is one of your five asks.
  [Developer] The static gate runs in seconds at zero device cost — your fastest feedback loop lives there, not on the device.

**Slide 6** (layout: Title and Content) — The three promises
- Title: `Every structural choice serves three promises: reproducibility, security and privacy, and verifiability.`
- Body: the 3-row table from page 5, verbatim
  (Promise | What it means here | How the spine keeps it):
  reproducibility (everything pinned; `NOT_APPLICABLE` explicit, null
  never valid) · security & privacy (one screening library at all three
  egress points; credentials by injected reference; raw workbooks never
  enter Git) · verifiability (append-only hash-chained lineage anchored in
  immutable storage; evidence hashed at landing; attributable principals).
- Closing line: these three survived five risk-storming passes — this deck
  shows the **post-mitigation** design.
- Source: page 5.
- Notes:
  [Chief Architect] This is the locked top-3 from the characteristics worksheet — the yardstick for every trade-off in your section.
  [Delivery Manager] "Post-mitigation" means the risk work is already inside this design, not a follow-up backlog.
  [Developer] Each promise turns into build-enforced rules in your section — pinning fields, screening calls, append-only lineage.

---

### Section 2 — Architect view

**Slide 7** (layout: Section Header)
- Title: `A modular monolith buys one quantum of simplicity — but its boundaries survive only if something enforces them.`
- Notes:
  [Chief Architect] The next three slides are your section: the shape and its stated trade-off, the thirteen decisions with what's honestly open, and the enforcement that stops rot.
  [Delivery Manager] One deployable means one thing to operate, version, and roll back in this window.
  [Developer] The enforcement slide is the origin of every "the build will stop you" rule in your section.

**Slide 8** (layout: Title and Content) — The shape
- Title: `One deployable with three cluster modules and exactly two async seams is the whole architecture.`
- Body (from page 6):
  - Three cluster modules — `conversion`, `validation-certification`,
    `evidence` — from the component analysis (16 components, 3 clusters),
    not the blueprint's five pipeline stages (those survive as packages).
  - The microkernel hybridization was declined at the style gate —
    recorded as the losing alternative, not forgotten.
  - Exactly two async seams (ADR 0007): the device-replay queue and human
    decisions — both via transactional outbox + idempotent consumers,
    never a distributed transaction. The queue starts as PostgreSQL
    tables; a broker is a later swap behind the same schema.
  - Only three abstractions beyond the spec, each with its
    simpler-rejected-thing recorded: the `spine-contracts` kernel, the
    `screening` library, and the object-storage port.
- Callout (distinct fill — the trade-off stated plainly): the monolith
  gives up independently deployable units for one quantum's operational
  simplicity — and the boundaries that would have been structural are now
  protected **only by fitness functions**.
- Source: page 6.
- Notes:
  [Chief Architect] The trade-off is stated, not hidden: boundary protection moved from structure to rules. The next-but-one slide shows the rules are CI-blocking, which is what makes this acceptable.
  [Delivery Manager] "Declined, recorded" is the pattern — losing alternatives are kept as decision records so nobody relitigates them mid-delivery.
  [Developer] Abstraction count is deliberately three — you will not meet a framework zoo in this repo.

**Slide 9** (layout: Title and Content) — Decisions made, honestly open
- Title: `Thirteen gated decisions close the design; four items stay honestly open as flagged probes, not guesses.`
- Body (from page 7): a compact two-part layout —
  - Top: the three decision groups as short labeled rows (Seams & shape ·
    Data & evidence · Security), each listing its ADR numbers and
    one-phrase gists, verbatim from page 7.
  - Bottom: the "honestly open" 4-row table verbatim (production
    object-storage platform — ADR 0011 Proposed, MinIO default ·
    PostgreSQL — working assumption pending bank-catalog confirmation ·
    Perfecto MSA / gateway contract / Octane asset versioning — probes
    open · real-input floor for gate clause (b) — set when the workbook
    corpus returns).
- Closing line (warning accent): either of the first two resolving against
  us is a **replan event, not a silent patch**.
- Source: page 7.
- Notes:
  [Chief Architect] Nothing on this slide is up for re-decision today — the ask is confirmation that the pack represents the baseline faithfully.
  [Delivery Manager] The open items are exactly the probe asks in your section — this slide is why they exist.
  [Developer] The open items don't block code: adapters and ports isolate every unresolved choice behind an interface you build against now.

**Slide 10** (layout: Title and Content) — How it can't rot
- Title: `Four CI-blocking fitness functions are wired before any feature commit — a boundary violation fails the build.`
- Body (from page 8): the four rules as bullets, each ending in
  "**build fails**":
  - **F1** — any type outside the model-boundary adapter referencing a
    provider SDK or AI-assistant construct → build fails. The model seam
    cannot erode before it is even used.
  - **F2** — any source-system type (POI, Octane DTO) escaping its
    adapter → build fails. The IR is the only thing that leaves ingestion.
  - **F3** — ingestion egress without a screening call → build fails
    (static half) *and* the payload is rejected at runtime (runtime half).
  - **F4** — any foreign key from lineage into conversion state → build
    fails. Retention deletion stays safe.
- Callout: **task zero** wires all four CI-blocking before any feature
  commit, and proves in CI that the database refuses `UPDATE`/`DELETE` on
  lineage from the application role. Weakening any fitness function is a
  recorded decision, never just a commit.
- Source: page 8.
- Notes:
  [Chief Architect] This is the answer to the monolith's stated trade-off: the boundaries live in rules, and the rules are mechanical, not conventions.
  [Delivery Manager] Task zero is strictly first on the roadmap because of this slide — a build without the fitness functions is not a valid baseline.
  [Developer] These four are most of your "rules of the road" — the build stops you, tells you which F-rule fired, and why.

---

### Section 3 — Delivery view

**Slide 11** (layout: Section Header)
- Title: `The engineering has no open questions — the calendar risk is external access.`
- Notes:
  [Chief Architect] The next three slides show the scope fence holding your decisions, and the external risks flagged in the spec itself.
  [Delivery Manager] The next three slides are your section: the fence, the roadmap, and the five asks only you can fire.
  [Developer] The start-anyway rule in this section is why you begin regardless of what access arrives late.

**Slide 12** (layout: Title and Content) — The scope fence
- Title: `Weeks 0–3 build the spine and only the spine — everything deferred has a recorded reason it is safe to defer.`
- Body (from page 9):
  - **In:** the three schema contracts · Excel + Octane ingestion behind
    one adapter contract · the screening library · the hierarchy tool ·
    the queued replay pipeline (static gate → device gate → classification
    → report) · append-only provenance · fitness functions from commit one.
  - **Out (with reasons):** the 5-row deferral table verbatim from page 9
    (LLM calls/prompts · review-queue UI · K-run certification policy ·
    locator healing · encryption + crypto-shredding — each with its
    "why it's safe to defer").
- Closing line: eleven carry-forward rules bind the weeks 3–8 spec to
  import this contract — dropping one is a recorded decision, not an
  omission.
- Source: page 9.
- Notes:
  [Chief Architect] Every deferral names the seam or record shape that makes it safe — deferred, not forgotten.
  [Delivery Manager] The fence is your scope-creep defense: anything crossing it mid-window is a replan conversation by construction.
  [Developer] "Out" items still shape your code — the quarantine record already matches the future review-record shape, so you build it once.

**Slide 13** (layout: Picture with Caption) — P4, the roadmap
- Title: `Eight work packages reach the week-3 gate, with three parallel streams after week one.`
- Body: `p4-delivery-roadmap@2x.png` at maximum proportional size. Caption
  line (from page 10): solid arrow = "must complete before"; colours track
  the module map — yellow conversion, green validation-certification, blue
  evidence, orange hexagon the screening library. This is a delivery flow,
  not an architecture view.
- Two bullets (from page 10): task zero is strictly first — no feature
  code before scaffold, fitness functions, lineage grants, and CI checks
  exist · WP4 ∥ WP5 ∥ WP6 run in parallel; only WP7 hard-requires external
  access.
- Source: page 10. (43 tasks total — say it in notes, keep the slide
  clean.)
- Notes:
  [Chief Architect] Dependencies are verbatim from the approved plan's work-package table — the diagram invents nothing.
  [Delivery Manager] Eight work packages, 43 tasks, three parallel streams after week 1; the only hard external dependency is WP7 at the gate.
  [Developer] Your stream assignment comes from this picture — conversion, validation, and evidence streams run in parallel from week 1.

**Slide 14** (layout: Title and Content) — Gate risks + week-0 asks
- Title: `Five week-0 asks stand between this plan and its gate — and none of them stops the team starting.`
- Body: the 5-row table from page 11 verbatim
  (Risk | Consequence if late | Week-0 ask): Perfecto credentials + pinned
  pool · Octane API key · the real-workbook corpus (10–20 workbooks) ·
  PostgreSQL catalog confirmation · the object-storage platform probe.
  Use the warning accent for the "consequence if late" column header.
- Callout (distinct fill — the start-anyway rule): none of these gate
  WP0/WP1/WP3 — the team starts regardless, and WP4–WP6 code proceeds
  against recorded fixtures. If the corpus slips past week 2, that is a
  **replan conversation, not a quiet slip**.
- Source: page 11.
- Notes:
  [Chief Architect] These risks are named in the spec itself as known break risks — surfacing them here is fidelity, not pessimism.
  [Delivery Manager] This is your action slide: fire all five asks this week; the corpus request goes to the feeding teams before the Excel adapter is written.
  [Developer] The start-anyway rule is your instruction too — recorded fixtures are the default substrate until real access lands.

---

### Section 4 — Developer view

**Slide 15** (layout: Section Header)
- Title: `The rules of the road are enforced by the build and the schema — not by memory.`
- Notes:
  [Chief Architect] The next two slides show your boundary decisions as developers will actually meet them: module walls and build failures.
  [Delivery Manager] Enforcement by CI means onboarding does not depend on tribal knowledge — the build teaches the rules.
  [Developer] The next two slides are your section: the repo you'll live in, and the eight things that stop the build.

**Slide 16** (layout: Picture with Caption) — P2, the repo
- Title: `Six Maven modules, one deployable — an illegal import is a build failure, not a review comment.`
- Body: `p2-module-map@2x.png` at maximum proportional size. Bullets
  (from page 12):
  - `spine-contracts` is the vocabulary: `TestCaseIR`, `LocatorCandidate`,
    `ReplayReport` as Java records; JSON Schema committed, drift fails CI.
  - Cluster modules depend on `spine-contracts` only — the module-boundary
    rule is CI-blocking.
  - `screening` is a shared library (deliberately not a pipeline
    component): one-line, in-process API at three call sites.
  - Stack: Java 21 · Maven reactor · Spring Boot · PostgreSQL 16 + Flyway ·
    Testcontainers (Postgres, MinIO) · ArchUnit · TestNG + pinned Appium.
- Source: page 12; honesty flags from `p2-module-map.view.md`.
- Notes:
  [Chief Architect] The hexagon is a deliberate shape choice — screening is a library, not a pipeline stage, and the diagram refuses to let it be misread. Honesty flags from the source view travel here.
  [Delivery Manager] One deployable and six modules is the whole operational surface for this window.
  [Developer] Memorize one edge rule: cluster modules import `spine-contracts` and nothing else across the wall — ArchUnit enforces it on every build.

**Slide 17** (layout: Title and Content) — Rules of the road
- Title: `Eight day-one rules stop the build — the pattern is quarantine loud, never default quietly.`
- Body (from page 13): the eight "the build will stop you if…" rules as a
  compact two-column bullet layout, verbatim in substance: source-system
  type escaping its adapter (F2) · egress without a screening call (F3) ·
  `Thread.sleep` in test code · locator not in the committed
  `LocatorCandidate` manifest · literal credential (schema rejects in
  data; gitleaks flags in code) · `UPDATE`/`DELETE` on a lineage row
  (database refuses; corrections are superseding appends) · missing
  pinning field (null never valid; `NOT_APPLICABLE` spelled out) ·
  real-derived fixture without its screening-version marker.
- Closing line (visually distinct): the pattern to internalize —
  **quarantine loud, never default quietly**: unknown classification
  quarantines, substituted devices quarantine, flagged payloads quarantine
  with a recorded override path.
- Source: page 13.
- Notes:
  [Chief Architect] Each rule is a promise from the three-promises slide made mechanical — reproducibility is the pinning rules, security is the screening and credential rules, verifiability is the lineage rule.
  [Delivery Manager] These fire on day one, not after a hardening phase — quality is not a later work package.
  [Developer] None of these depends on you remembering them — CI or the schema stops you and names the rule. The one habit to build: when something is unknown, quarantine it loudly.

---

### Section 5 — Closing

**Slide 18** (layout: Title Slide) — The ask
- Title: `Nothing in this deck is up for re-decision — each audience leaves with one concrete action.`
- Subtitle (three lines, one per audience; render each line's leading
  audience label in that audience's accent color from the PALETTE — this
  is the one place the audience accents appear on a slide surface; from
  page 14):
  - Chief Architect: Confirm this pack faithfully represents the gated baseline; flag anything it doesn't.
  - Delivery Manager: Fire the five week-0 asks — they are the only thing between this plan and its gate.
  - Developer: The task list awaits approval; on approval, task zero starts.
- Closing line (small, centered, from page 14): *Every fact on these pages
  traces to a signed-off artifact. Where something is unknown, it says so
  — that is the standard the system itself is being built to.*
- Notes:
  [Chief Architect] The confirmation you give here is the last gate before task zero — silence is not confirmation.
  [Delivery Manager] The asks are drafted and named; the action is firing them this week, not composing them.
  [Developer] Task zero is fully specified down to pass/fail — the moment the task list is approved, the rails start going down.

================================================================
== END SLIDE STRUCTURE                                         ==
================================================================

## Invariants

- No internal process identifiers (`EARS`, `SDD`, approval tokens, bare
  carry-forward or mitigation codes) appear in slide titles, body text, or
  speaker notes at any point — see the terminology rule for the allowed
  verbatim vocabulary.
- Action title on every slide, section headers included (verb + claim;
  never a topic label; Slide 1's deck title exempt). Section-header titles
  state the section's mini-Complication.
- Speaker notes on every slide in the three-section labeled format
  ([Chief Architect] / [Delivery Manager] / [Developer]).
- No fabricated facts or numbers — everything traces to
  `spine-design-pack.md`; view/detail files feed speaker notes only.
- The four diagram PNGs appear unmodified — never cropped, recolored,
  redrawn, or annotated over.
- Honesty tags travel: every image slide's speaker notes carry the
  relevant UNKNOWN/working-assumption flags from its `view.md`, and the
  open-items table (deck page 7) appears on a slide body.
- No duplication: helper functions (or equivalent reuse) for repeated
  patterns; no 5-line clone.
- `TITLES.md` emitted alongside the deck — the 18 titles in order, so the
  argument is readable from titles alone without opening the `.pptx`.
- Circuit breaker: placeholder slide + `TODO:` title rather than invented
  content; flagged in `COVERAGE.md`.
- Do not collapse the three audiences into one label — the differentiated
  framing is the core value the speaker notes deliver.

## Deliverables

1. `Shared Spine HLD — Three-Audience Presentation.pptx` — the deck.
2. `TITLES.md` — the 18 slide titles in order (the Titles Test artifact).
3. `COVERAGE.md` — a coverage table listing every `spine-design-pack.md`
   page (2–14), the slide(s) it appears on, and whether it is fully
   covered, partially covered, or a placeholder; plus any flagged
   discrepancies between handover artifacts. This is the review entry
   point: a reviewer reads `TITLES.md` first (does the argument hold?),
   then `COVERAGE.md` (is every source page surfaced?), then samples the
   `.pptx`.

## What "done" means

A reviewer who reads `TITLES.md`, reads `COVERAGE.md`, and opens the
`.pptx` walks away confirming: (a) the titles alone tell the complete
argument; (b) every slide has a three-section speaker notes panel; (c) all
four diagram PNGs are present, unmodified, and legible at presentation
size; (d) the three-promises table (Slide 6), the honestly-open table
(Slide 9), and the week-0 asks table (Slide 14) are present with their
verbatim rows; (e) every image slide's notes carry the honesty flags from
its source view; (f) no internal process identifiers appear anywhere in
the deck; (g) the deck exports cleanly to PDF with no content cut off and
no missing glyphs.

If any of those seven is missing, the deck has failed.
