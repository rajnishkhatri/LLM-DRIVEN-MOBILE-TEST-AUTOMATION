# Spec: Insurance Claim Processor Explainer — "The Workflow the Model Never Controls" (claim-processor-story)

**Status:** **SPEC-OK (2026-09-23)** — owner approved at the gate; all
five clarify questions C1–C5 answered **as recommended** in session.
Advance → plan (`docs/sdd/plans/claim-processor-story.plan.md`).
**IMPLEMENTED (2026-09-23)** — see the tasks-file build record;
deliverable at `docs/architecture/explainers/insurance-claim-processor-story.html`,
verifier green (153 checks), registered in `docs/architecture/log.md`,
private Artifact published per FR-12. Awaiting owner converge checks
(AC-15 flip test, AC-16 hybrid-rule read) + Stage-7 review.
**Direction:** accepted in session (2026-09-23, three confirm rounds):
a **hybrid visual-first explainer** of the insurance claim document
processor in the design system of
`docs/architecture/explainers/aws-ai-architect-story.html` ("The Loop,
Left Running"), with owner-selected options **O1a** (full real-deploy
story + findings), **O2** (`docs/architecture/explainers/` placement),
**O3** (checked-in verifier), **O4** (reference scale, ~14 figures).
Owner's governing rider (the hybrid rule): **diagrams lead wherever a
mechanism can be shown; where a concept genuinely needs words (a why, a
trade-off, a reversal, a finding), a short plain-English text explainer
carries it instead — the medium is chosen per concept by "which explains
this faster", never by word-count quota.** A figures-only reader must
still grasp the complete mechanism (the flip test); prose adds the
reasoning; neither half may be weak.
**Change class:** documentation deliverable (one HTML file + one
stdlib-only verifier script + one decision-log pointer line); no code
paths, no new dependency, no ⚠️ Ask-first trigger → decision-log entry, no
ADR. `check_gate` (skill-sync) untouched by construction — no skill
surfaces are written. `test_gate = <none>` (the kata's unittest suite is
not in scope: nothing under `insurance-claim-processor/build/` changes).

## Clarify decisions

| ID | Question | Recommendation | Decision |
|----|----------|----------------|----------|
| C1 | Findings F1–F11: verbatim register vs summarized? | Condensed one-liners pinned on the deploy-timeline figure (F13); the three deploy-blocking findings (bootstrap, HITL handler, placeholders) each get a short text-explainer beat; the walkthrough stays the deep link | **locked as recommended** (owner, 2026-09-23) |
| C2 | AWS icon fidelity: official asset SVGs vs simplified original glyphs? | Simplified original glyphs in AWS category colors, drawn once as `<symbol>`s, always text-labeled; no downloaded assets (keeps the file self-contained, avoids asset-license bookkeeping and byte bloat) | **locked as recommended** (owner, 2026-09-23) |
| C3 | How is the flip test verified? | Split: the verifier machine-checks structural proxies (every figure carries an in-SVG plain-English title sentence, flow figures have numbered step arrows, every icon use has a visible text label, caption + citation present); the flip test itself is human-judged at the converge gate via a figures-only scroll | **locked as recommended** (owner, 2026-09-23) |
| C4 | Live-status honesty: the system is partly deployed (auto-approve path live 2026-09-22; HITL, alarms/remediation, ensemble not yet). Present as timeless design or as-built? | As-built honesty: a `designed — not yet deployed` chip (same visual grammar as `.unverified`) on every element that is not live in account 324177727513, plus a footer status line dated 2026-09-23 | **locked as recommended** (owner, 2026-09-23) |
| C5 | Size budget (icon symbols + ~14 figures will outweigh the 105 KB reference) | Hard cap **≤ 350 KB**, target ~200–250 KB; cap is head-room, not a target | **locked as recommended** (owner, 2026-09-23) |

## Problem

The claim processor is the workspace's most complete worked example — a
full arch-* + aws-ai-* + SDD lifecycle from capability brief to a real
AWS deploy that succeeded on 2026-09-22 — but its story is scattered
across ~20 artifacts (design, worksheets, ADRs 0001–0015, specs, plans,
eval report, resilience clinic, deploy walkthrough/ledger). No single
artifact lets an architect or senior engineer absorb the system
end-to-end. The missing piece is the **synthesis explainer**: one page
that tells the whole arc — problem → not-an-agent decision →
characteristics → pipeline → human gate → safety/IAM envelope →
grounding → model-resilience layer → offline proof → real deploy and
what it surfaced — in the workspace's established explainer design
language, but **diagram-led**, so the mechanism survives even a
zero-prose read.

Three constraints are load-bearing:

1. **The hybrid rule** (owner rider above) — per-concept medium choice;
   the flip test for mechanism; text explainers reserved for reasoning
   that a diagram would distort (reversed decisions, trade-offs, findings).
2. **Nothing invented** — every fact on the page traces to a named
   in-repo source (table below). No invented SLAs, costs, team facts, or
   AWS behavior. Facts the sources themselves flag for re-verification
   (e.g. grounding threshold ~0.70) carry the `.unverified` marker.
3. **As-built honesty** — the deploy is partial (per C4); the page must
   not present designed-but-undeployed elements (HITL wait, alarms,
   remediation, ensemble flag) as live.

## Scope — source material

| Source (all under `insurance-claim-processor/` unless noted) | Role |
|---|---|
| `design/solution-design.md` | primary — topology, HITL, knowledge/memory, guardrails, IAM, resilience knobs, result contract, sequence + failure flows, resilience-increment map |
| `assess/capability-brief.md` | why an FM at all; service-selection matrix; cascade choice later reversed by ADR 0013 |
| `worksheets/characteristics-worksheet.md` | driving characteristics, top-3, tension pairs |
| `worksheets/style-decision.md` | quanta, sync/async, style scoring |
| `components/logical-components.md` | the 7 logical components, roles, coupling |
| `adrs/` (0001–0015 + index) | the decision trail incl. both supersessions (0003→0004; C1-deferral→0012; brief-§4→0013) |
| `specs/claim-processor-real-aws.spec.md`, `specs/claim-processor-model-resilience.spec.md` | EARS ground truth for pipeline + resilience behavior |
| `risk/resilience-clinic.md` | cards C1–C11: which are live vs named-not-applied |
| `validate/architecture-validation.md`, `validate/eval-report.md` | C4 diagram set precedent, nine-intersections verdict, offline eval results, RAG-integrity finding |
| `build/DEPLOY-WALKTHROUGH.md`, `build/DEPLOY-LEDGER.md` | the real-deploy narrative, stages 0–9, findings register F1–F11, remaining work |
| `build/README.md`, `build/claim_processor/` module names | offline-first run modes, gate flag, module ↔ component mapping (names only — no code retell) |
| `docs/architecture/explainers/aws-ai-architect-story.html` | design language: palette tokens, three-block theming, masthead → sticky key → Parts → decision cards → scorecard → footer, envelope beats, `.unverified` grammar |
| `docs/sdd/specs/aws-ai-architect-story.spec.md` | precedent spec — FR/AC/verifier conventions inherited below |
| `docs/architecture/log.md` | registration surface (FR-12) |

Citations are by **file path + section name, not line number** (paths are
stable; lines rot). Deploy findings keep their F1–F11 ids verbatim.

## Deliverable structure

Masthead (title + seam statement: how this page differs from the source
artifacts — synthesis story, not a replacement for the design doc or
walkthrough) → sticky **legend** (`top:0`, the page's only sticky
element: amber model lane / teal envelope lane / human slate /
`.unverified` chip / the C4 status chip) → **icon key strip**
(each AWS-glyph symbol shown once with its name, immediately under the
masthead or fused into the legend) → nine spine Parts → decision-card
Part → scorecard → footer (About / Honesty note / live-status line /
provenance + as-of date).

**The spine** — each Part opens with its hero figure, prose beneath it in
plain English, each Part closing with an **envelope beat** (what the
deterministic plane owns before the next escalation), with back-links to
decision cards:

| Part | Story step | Hero figure(s) | Text-explainer beats (hybrid rule) |
|---|---|---|---|
| I | **One claim, two doors** — what goes in, the provenance-tuple result, auto-approve vs human review | F1 claim in → two doors; F2 agent (crossed out) vs fixed workflow (chosen) | why the three multi-agent walls don't apply; the losing-alternatives table |
| II | **What it must be good at** | F3 top-3 characteristics pinned to the 7 components | tension pairs in one short paragraph |
| III | **The pipeline** | F4 (hero of the page): S3 → Step Functions → Lambdas → Bedrock(+Guardrail) → S3 on AWS glyphs, amber/teal lanes | none planned — this Part is the flip-test anchor |
| IV | **The human gate** | F5 routing funnel (four red gates → one human gate); F6 `waitForTaskToken` wait + token resume + 7-day timer | reviewer contract (approve/correct/reject), why the token is single-use |
| V | **The safety and trust envelope** | F7 two safety nets (Guardrail wraps the model call, validator wraps the result); F8 three IAM keys and their doors | the two-ARN trap; why Cedar waits for tools |
| VI | **Grounding** | F9 retrieve-then-cite; unknown jurisdiction → retrieve nothing + flag | `retrieve` vs `retrieve_and_generate`; the no-memory decision; S3 Vectors promote |
| VII | **When the model has a bad day** | F10 the seven-layer resilience stack; F11 breaker-open → degraded path → human review | the integrity invariant (no resilience path auto-approves); the two reversed decisions as a "decisions age" beat |
| VIII | **Proof** | F12 offline pyramid (263 tests → gate flag → real smoke); F13 deploy-stage timeline with findings pinned | what the tests couldn't see (the C1-decided finding beats); remaining work |
| IX | **The decision map** | F14 decision dots on the two-lane map, each linking to its card | the cards themselves |

**Decision cards (~10):** workflow host (Lambda vs Step Functions
Standard vs Express — ADR 0003/0004) · HITL mechanism (ADR 0005) ·
guardrail placement (day-1 Guardrails + validator defense-in-depth — ADR
0008) · IAM shape (single processing role, two-ARN pattern — ADR 0009) ·
RAG store (keyword PoC → KB on S3 Vectors — ADR 0007) · document
understanding (vision FM now, Textract/BDA promote — ADR 0006) · config
plane (AppConfig — ADR 0010) · breaker (measured signal — ADR 0012) ·
ensemble (flag-gated, bounded reversal — ADR 0013) · degradation ladder
(ADR 0014). Each card: the question, a compact trade-off table, a
**default + when-to-deviate** line, ADR id, anchors to/from its Part.

**Visual grammar:** the reference's two lanes (amber `--llm` model /
teal `--det` envelope / slate `--human`) **combined with** an AWS-glyph
symbol library: simplified service icons (per C2) defined once as SVG
`<symbol>` and placed with `<use>` — S3, Lambda, Step Functions, Bedrock,
Guardrails, IAM, KMS, AppConfig, CloudWatch, plus person/document/token
glyphs. The lane says *who decides*; the icon says *which service does
it*; every icon placement carries a visible text label.

## Functional requirements

- **FR-1 Single self-contained file** at
  `docs/architecture/explainers/insurance-claim-processor-story.html`.
  Zero external requests: no CDN, no web fonts, all CSS/JS inline, all
  figures inline SVG using `var(--token)` colors. Works from `file://`
  offline. Size per C5.
- **FR-2 Diagram-led spine.** The nine Parts in the order above; each
  Part's hero figure appears before its prose; the fourteen figures
  F1–F14 all present, numbered, in Part order.
- **FR-3 The flip test (mechanism-complete figures).** Read in sequence
  with all prose skipped, F1–F14 convey: input → two outcomes; code-owns-
  the-path; the pipeline hop-by-hop with model vs envelope steps; the
  four escalation gates; the durable human wait; the two safety layers;
  the least-privilege keys; fail-closed grounding; the resilience stack;
  the degraded path ending in human review; the proof ladder; the deploy
  timeline with findings; the decision map. Each figure carries one
  in-SVG plain-English title sentence; flow figures use numbered step
  arrows (①②③); machine proxies per C3, human flip-test at converge.
- **FR-4 Hybrid rule (owner rider).** Text explainers appear exactly
  where the structure table plans them (or where implementation finds a
  diagram would distort); each stays short (≈ ≤4 sentences per beat);
  no Part's prose retells what its figure already shows; no figure is
  forced where reasoning (why / trade-off / reversal) is the content.
- **FR-5 Two-lane + icon grammar.** Every architecture figure renders
  both lanes labeled, colored via `var(--llm)` / `var(--det)` (no
  hard-coded lane hex); AWS glyphs only via `<symbol>`/`<use>` (defined
  once, reused); every `<use>` placement has an adjacent visible text
  label; single-lane figures allowed only for non-architecture visuals
  (comparatives, timelines), enumerated in the plan. Category-color hex
  inside the symbol definitions is permitted (icons keep AWS identity in
  both themes) but must pass contrast in both palettes.
- **FR-6 Fact traceability.** Every figure and every prose claim traces
  to a source-table artifact; each figure's `figcaption` ends with its
  source citation ("`design/solution-design.md` §6, as of 2026-09-23"
  style). Facts the sources flag as tune/re-verify (grounding ~0.70,
  $10k threshold as a default) carry the `.unverified`-style marker at
  **every** occurrence. Findings keep ids F1–F11 verbatim, but — Stage-4
  analyze finding A1 — they collide with the figure numbering (also
  F1–F14), so on-page every finding reference is written "finding F2",
  never bare "F2", and the verifier keys figures on `data-fig`
  attributes, never on text. Depth per C1.
- **FR-7 As-built honesty (per C4).** Every not-yet-live element carries
  the status chip in figures and cards; the footer carries a dated
  what's-live line (auto-approve smoke succeeded 2026-09-22; HITL,
  alarms/remediation, ensemble pending). No undeployed element ships
  looking live.
- **FR-8 Plain-English narration.** Long-form-article voice; every
  technical term or acronym introduced in ordinary words at first use;
  no unexplained jargon inside figures (in-SVG text uses plain words +
  service names). The two supersessions are narrated as "decisions age"
  — plainly, without a temporal badge taxonomy (the R1 lesson from the
  precedent spec: no was/now grammar).
- **FR-9 Originality.** All prose fresh; no verbatim source sentence
  >15 consecutive identical words (kept exact: figures' ids, field
  names, ARNs patterns, thresholds, command names). The footer states
  the page is a synthesis of the named repo artifacts.
- **FR-10 Theming.** Light/dark via CSS custom tokens; the three-block
  dark-mode pattern (bare `:root`; `prefers-color-scheme: dark` guarded
  `:root:not([data-theme="light"])`; `:root[data-theme="dark"]`);
  explicit body background token; icon symbols legible in both themes.
- **FR-11 Responsive + accessible baseline.** No horizontal body scroll
  at ≤375 px (wide figures pan inside their own `overflow-x`
  containers); every figure `<svg>` has `role="img"` + `aria-label`
  describing the mechanism; hash targets carry `scroll-margin-top`;
  `:focus-visible` styles; `prefers-reduced-motion` respected; content
  never gated on JS; standard document shell (`<!DOCTYPE html>`,
  `lang="en"`, charset + viewport metas).
- **FR-12 Registration + converge.** One newest-first entry in
  `docs/architecture/log.md` naming the file, design language
  (aws-ai-architect-story lineage + AWS-glyph extension), and SDD
  provenance (this spec). No `index.md` entry (HTML outside `okf_lint`
  scope). At converge: publish the finished file as a private claude.ai
  Artifact; the repo file stays canonical (precedent C4).
- **FR-13 Verifier checked in.** Stdlib-only
  `docs/architecture/explainers/verify_claim_processor_story.py`, run as
  the AC gate at converge and re-runnable on future edits; checks
  enumerated under Verification below.

## Acceptance criteria (EARS — failure paths first)

- **AC-1** IF JavaScript is disabled, THEN every Part, figure, card, and
  chip remains readable in document order.
- **AC-2** IF the file is opened from `file://` with networking blocked,
  THEN it renders identically — verifiable: zero `http(s)://` in
  `src`/`href` attributes (in-repo relative links and plain-text source
  names only).
- **AC-3** IF the viewport is ≤375 px, THEN the body has no horizontal
  scroll; wide figures pan inside their own containers.
- **AC-4** IF a figure places an AWS glyph, THEN it does so via `<use>`
  of a `<defs>`-block `<symbol>` with an adjacent visible text label —
  zero inline-duplicated icon paths, zero unlabeled icon placements.
- **AC-5** IF a fact is one of the flagged-tunable values (grounding
  threshold, payout threshold as default), THEN every occurrence carries
  the unverified-style marker; IF an element is not live per C4, THEN
  every figure/card occurrence carries the status chip.
- **AC-6** IF any prose span reproduces >15 consecutive identical words
  from a source artifact, THEN the build fails review (distinctive-
  phrase sweep).
- **AC-7** IF a figure's `figcaption` lacks a source citation, or a
  figure lacks an in-SVG plain-English title sentence, THEN the verifier
  fails.
- **AC-8** WHEN any architecture figure is viewed, both lanes are
  present and labeled via `var(--llm)`/`var(--det)`; plan-enumerated
  single-lane exceptions only; no lane-color hard hex in figure fills.
- **AC-9** WHEN the decision Part is read, all ~10 cards are present,
  each with a trade-off table, a default + when-to-deviate line, its ADR
  id, and working anchors to/from its motivating Part; the two
  supersessions are visible on their cards.
- **AC-10** Ubiquitous: figures F1–F14 all present in Part order per the
  structure table; the nine Parts each close with an envelope beat.
- **AC-11** Ubiquitous: every `figcaption` citation names a real file
  from the source table (verifier cross-checks paths against the repo).
- **AC-12** Ubiquitous: theme sanity in both modes (every token defined
  in all three theme blocks; explicit body background); file size within
  the C5 cap.
- **AC-13** Ubiquitous: the masthead seam statement, the footer
  live-status line (C4), the honesty note, and the as-of date are
  present; the `docs/architecture/log.md` entry exists, newest-first.
- **AC-14** WHEN served over HTTP, the browser reports UTF-8 and
  standards mode; no mojibake in masthead, figure titles, or footer.
- **AC-15** WHEN the figures are read in sequence with prose skipped,
  the mechanism story of FR-3 is complete — human-judged flip test at
  the converge gate (deliberately not machine-checkable beyond the C3
  proxies).
- **AC-16** WHEN any Part is read in full, the hybrid rule holds: no
  prose paragraph retells its figure; every planned text-explainer beat
  is present and carries reasoning a figure could not — human-judged
  targeted read at converge.

## Verification method

- **Verifier probes (FR-13):** AC-2 (no external `src`/`href`), AC-4
  (`<use>`-only icons, symbol defined once, label adjacency), AC-5
  (value-keyed marker check + status-chip census against a C4-derived
  list), AC-6 (distinctive-phrase sweep), AC-7 (per-`figure` caption +
  citation + in-SVG title), AC-8 (no lane hex in fills outside the token
  block), AC-10 (F1–F14 ids + Part order + envelope-beat count), AC-11
  (citation paths exist on disk), AC-12 (token × three theme blocks;
  size cap), AC-14 static half (shell bytes).
- **Targeted reads:** AC-9 (cards), AC-13 (seam/footer/log), AC-15
  (flip test), AC-16 (hybrid rule).
- **Browser checks (in-app pane):** AC-1 (JS off), AC-3 (≤375 px +
  scrollWidth probe), AC-12 (dark mode), AC-14 (`python3 -m
  http.server`: `characterSet`/`compatMode`), plus a both-themes visual
  pass of the icon strip.
- Baseline before implementation: `check_gate` (`python3
  tooling/skill-sync/skill_sync.py check` from repo root) green;
  `test_gate = <none>`.

## Out of scope / deferred

Any edit under `insurance-claim-processor/` (the source artifacts are
read-only inputs) · Pages allowlisting (`apps/html-site/manifest.toml`
is its own spec discipline) · a markdown Concept twin of this page ·
quiz/self-test layers · localStorage or persistence · skill-surface,
`tooling/`, or `src/` changes · re-running or extending the deploy
(the page reports state as of 2026-09-23; deploy work continues under
its own SDD thread).

## Amendments

- **2026-09-23 (Stage-7 review):** figure set extended to **F1–F15**:
  a new F14 ("The whole machine, as deployed" — the end-to-end state
  machine with every catch, smoke-#1 path numbered, not-yet-exercised
  states dashed, HITL chain pinned to finding F2) was added to Part
  VIII at the owner's request, and the Part-IX decision map became
  F15. AC-10's id list reads F1–F15 accordingly. A new **AC-8b** is
  added: no SVG `<text>` may extend past its figure's viewBox
  (approximate glyph-advance lint in the verifier) — introduced after
  the review found six clipped labels the original AC set could not
  catch. All other ACs unchanged.
