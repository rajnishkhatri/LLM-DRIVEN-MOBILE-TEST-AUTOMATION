# Spec: CCAR-P Exam Prep Guide (ccar-p-prep-guide)

**Status:** **SPEC-OK (2026-08-25)** — owner locked C1–C3 as recommended;
C4 overridden to **repo file only** (no Artifact publication).
**Direction:** confirmed 2026-08-25 in-session: v2 editorial chassis
(`docs/architecture/explainers/o7-pipeline-story-v2.html` design language) +
**7-exam-domain spine** (per the CCAR-P blueprint) + **whitelabeled scenarios**
(course captures are private; stories re-invented) + **adversarial-hardened
practice layer** (owner has sat the exam; the real test is harder than the
practice bank) + **visual-first explanations** (inline SVG diagrams).
**Change class:** documentation deliverable (one HTML file + catalog pointer
lines); no code paths, no new dependency, no ⚠️ Ask-first trigger →
decision-log entry, no ADR. `check_gate` (skill-sync) untouched by
construction — no skill surfaces are written.

**Clarify decisions:**
| ID | Question | Recommendation | Decision |
|----|----------|----------------|----------|
| C1 | Deliverable path/name | `docs/ccar-p-prep-guide.html` (beside the M1 atlas, served by the `atlas-docs` launch config) | **locked as recommended** |
| C2 | Whitelabel boundary | Exam-relevant terminology and frameworks stay exact (they are what the exam tests); every scenario, organization, actor, and metric-story is invented fresh; no >15-consecutive-word verbatim run from any course capture | **locked as recommended** |
| C3 | Gauntlet design | Two 15-item interactive quizzes; 5 options per item (1 correct, ≥2 technique-wrong-diagnosis distractors, ≥1 adversarial option); ~20% multi-select; difficulty pitched above the practice bank | **locked as recommended** |
| C4 | Publication & linkage | Publish as a private claude.ai Artifact at converge; no `file://` links to the practice bank; relative link to the M1 atlas allowed | **overridden: repo file only** — no Artifact; no `file://` links to the practice bank; relative atlas link kept |

**Open questions:** none beyond C1–C4.

## Problem

The five-module bundle (`cases/claude-certification/`) is complete enough to
study from, but it is the wrong shape for the exam and the wrong sensitivity
for sharing. Four gaps:

1. **Wrong axis.** Content is organized by the five course modules; the CCAR-P
   exam is organized by seven blueprint domains with fixed weights. The
   crosswalk currently lives in nobody's head but the owner's.
2. **Private substance.** The bundle's scenarios and failure traces are
   captures of Anthropic's course screens. A shareable prep guide cannot
   reproduce them; the *lessons* must survive while the *stories* are
   re-invented.
3. **Difficulty undershoot.** The existing practice bank
   (`CCAR-P_Practice_Bank_Set2_1.html`, 120 items) sits below the real exam's
   difficulty (owner's firsthand report). Its items rarely carry adversarial
   options — options engineered to punish pattern-matching rather than merely
   occupy space.
4. **Prose-only teaching.** The bundle and revision sheet are text; the
   decision rules (control placement, failure asymmetry, caching mechanics)
   are inherently diagrammatic and are currently taught without a single
   picture.

## Scope — source material

| Source | Role |
|---|---|
| Five module bundles under `cases/claude-certification/` | teaching substance: frameworks, decision rules, failure-*lessons* (concepts kept; stories re-invented per FR-5) |
| `cases/claude-certification/revision-all-modules.md` | condensed decision rules + cross-module through-lines — each domain part's "rules" panel |
| `cases/claude-certification/quiz-mixed-platform-team-enablement.md` | 15 recorded items: format precedent + re-skin source for Gauntlet A |
| Session-drafted M2–M4 coverage map (this session, 2026-08-25) | Gauntlet B basis (fresh authorship) |
| `docs/architecture/explainers/o7-pipeline-story-v2.html` | design-language donor: tokens, components, semantic color key, fig-card SVG idiom |
| `~/Downloads/CCAR-P_Practice_Bank_Set2_1.html` | exam blueprint authority: 7 domains + weights (D1 17 / D2 13 / D3 19 / D4 16 / D5 14 / D6 14 / D7 7), 63-item / 120-min / 720-of-1000 facts; difficulty floor; quiz-engine interaction precedent |
| `docs/claude-architect-m1-atlas.html` | house precedent for a self-contained interactive HTML deliverable |

## Functional requirements

- **FR-1 Single self-contained file.** One HTML file at the C1 path. Zero
  external requests: no CDN, no web fonts (system serif/sans/mono stacks as in
  the v2 donor), all CSS/JS inline, all diagrams inline SVG. Works from
  `file://` offline.
- **FR-2 v2 design language.** The guide is built from the donor's component
  vocabulary: masthead (eyebrow / serif display h1 / italic dek / mono
  byline), **sticky semantic color key**, numbered `h2` sections with PART
  dividers (`rule-orn`), measured text column, `fig-card` SVG figure bands
  with mono figcaptions, callouts, pull quotes, tables with pills, mono
  footer, light/dark theming (`prefers-color-scheme` + explicit
  `data-theme` override winning both directions), `prefers-reduced-motion`
  respected.
- **FR-3 Semantic color system.** Colors carry meaning consistently across
  every diagram and panel in the guide (e.g., deterministic-control /
  model-probabilistic / human-decision / risk-failure), declared once in the
  sticky key. No diagram uses a meaning-color decoratively.
- **FR-4 Seven-domain spine.** Front matter (how to use the guide + exam facts
  panel + the cross-module "master lens" section), then Parts D1–D7 in
  blueprint order, each labeled with its official weight, then the practice
  gauntlets, then a quick-revision annex. Module→domain mapping is recorded in
  the plan and drives each part's content.
- **FR-5 Whitelabel originality.** Exam-relevant terminology, framework names,
  and decision rules are kept exact. Every scenario, company, actor, industry
  pairing, and numeric story is freshly invented. No >15-consecutive-word
  verbatim run from any course-capture file. No course screen's structure is
  mirrored. Footer states the guide is independent and unofficial, with a
  pointer to Anthropic's official pages as the authority on current exam
  policy, models, and pricing.
- **FR-6 Visual-first teaching.** Each domain part carries ≥2 inline-SVG
  diagrams in the fig-card idiom, each showing a *mechanism* (a request path,
  a failure asymmetry, a cache prefix, a control placement) rather than
  decorating. Every load-bearing decision rule in a part appears in at least
  one diagram or structured panel (table/callout), not only in running prose.
- **FR-7 Inline checkpoints.** 1–2 per domain part: a short scenario prompt
  with click-to-reveal answer + why-the-tempting-option-fails rationale.
  Readable without JavaScript (native `<details>` or equivalent).
- **FR-8 Practice gauntlets.** Two 15-item interactive quizzes at C3 design:
  - **Gauntlet A** — re-skinned from the recorded M1+M5 session (new
    industries/actors/numbers per FR-5; same lessons).
  - **Gauntlet B** — fresh items over the M2–M4 coverage map.
  - Every item: a verbose scenario stem, 5 options, exactly one correct set
    (single-select, or multi-select marked as such at ~20% of items overall),
    ≥2 distractors that pair a *real technique with the wrong diagnosis*, and
    ≥1 **adversarial option** — an option that reaches a right-sounding
    conclusion through flawed reasoning, or that would be correct in an
    adjacent scenario, engineered to punish pattern-matching.
  - Every item is tagged to one of the 7 domains.
  - Difficulty pitched above the practice bank (longer stems, closer calls,
    no giveaway options).
- **FR-9 Quiz engine.** Select → grade → per-option verdict with a rationale
  line for *every* option (the adversarial option's rationale names the trap).
  Running progress, end-of-gauntlet summary with total score and per-domain
  tally from item tags. No persistence; a reload resets. With JavaScript
  disabled, items and their answers/rationales remain readable in document
  order (progressive enhancement, never a content gate).
- **FR-10 Exam logistics & strategy.** A facts panel (63 items, 120 minutes,
  720/1000 cut, domain weights — flagged "verify current policy on the
  official page"), time-budget arithmetic, and an option-triage method
  (diagnosis-before-remedy, category-error-first, silent-success signatures,
  adversarial-option spotting) — the cross-cutting lessons from the quiz
  records, whitelabeled.
- **FR-11 Registration.** One pointer line in
  `cases/claude-certification/log.md`, a 2–4 line entry in
  `docs/architecture/log.md`, and a relative link from the guide to the M1
  atlas (one-way; the shipped atlas file is not edited).
- **FR-12 Responsive + accessible baseline.** No horizontal body scroll at
  ≤375 px (wide SVGs scroll inside their own container); checkpoints and quiz
  controls keyboard-operable with visible focus; `prefers-reduced-motion`
  disables animation.

## Acceptance criteria (EARS — failure paths first)

- **AC-1** IF JavaScript is disabled or fails, THEN all teaching prose,
  diagrams, checkpoint answers, and gauntlet items *including* their correct
  answers and rationales are readable in document order — interactivity is
  progressive enhancement, never a content gate.
- **AC-2** IF the file is opened from `file://` with networking blocked, THEN
  the page renders identically to the online case (zero external fetches —
  verifiable: no `http(s)://` in `src`/`href` of loaded resources).
- **AC-3** IF a viewer is at ≤375 px width, THEN the body has no horizontal
  scroll; wide figures scroll inside their own containers.
- **AC-4** IF any prose run of >15 consecutive words is identical to a
  course-capture file (framework terminology being taught excluded), THEN
  review fails — spot-checkable by grepping distinctive source phrases
  against the HTML.
- **AC-5** IF a Gauntlet A item's scenario shares its source item's industry +
  actor pairing, THEN the re-skin is incomplete and review fails (whitelabel
  check at the quiz layer).
- **AC-6** WHEN the page loads, THEN the masthead, sticky semantic key, and
  Parts D1–D7 render in blueprint order, each part labeled with its weight,
  and the seven weights sum to 100.
- **AC-7** WHEN any domain part is read, THEN it contains ≥2 inline-SVG
  fig-cards, and every meaning-color used in any diagram appears in the sticky
  key.
- **AC-8** WHEN a checkpoint's reveal is activated, THEN the answer and its
  why-wrong-options-fail rationale appear; every domain part has ≥1
  checkpoint.
- **AC-9** WHEN a gauntlet item is graded, THEN every option shows a rationale
  line and the adversarial option's rationale names the trap it sets.
- **AC-10** WHEN a gauntlet is completed, THEN the summary shows the total
  score and a per-domain tally consistent with the item tags; each gauntlet
  has exactly 15 items; 5–7 of the 30 items are multi-select.
- **AC-11** Ubiquitous: each of the 7 blueprint domains is covered by a part
  whose content traces to ≥1 module-bundle source named in the plan's mapping
  table — coverage verified, not assumed.
- **AC-12** Ubiquitous: theme sanity holds in light and dark (tokens defined
  on bare `:root`, dark via media query guarded against `data-theme="light"`,
  explicit `data-theme` overrides winning both directions; body background
  explicit), and total file size stays ≤ 1 MB.

## Out of scope / deferred

Any modification of the bundle's `.md` files · duplicating the practice
bank's 120 items (it remains the drilling tool) · score persistence /
localStorage · timed-mock simulation of the 63-item exam · multi-page
splitting or a generator for future exams · changes to skill surfaces,
`tooling/`, or `src/` · Artifact publication (rejected at C4 — the repo
file is the only surface; viewed locally via the `atlas-docs` server or
`file://`).
