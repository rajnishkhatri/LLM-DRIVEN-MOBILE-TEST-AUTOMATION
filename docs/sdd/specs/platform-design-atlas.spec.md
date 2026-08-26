# Spec: Claude Architect Module-1 Interactive Atlas (platform-design-atlas)

**Status:** **SPEC-OK (2026-08-23)** — owner accepted all clarify
recommendations verbatim ("spec-ok"); C1–C5 locked as recommended below.
**Direction:** D1 chassis + D4-lite study layer + D5 explainer-side gap fill,
with D3's four-decisions journey folded in as a map grouping toggle
(brainstorm 2026-08-23, gate answer "recommendation").
**Change class:** documentation deliverable (one HTML file + catalog pointer
lines); no code paths, no new dependency, no ⚠️ Ask-first trigger → decision-log
entry, no ADR. `check_gate` (skill-sync) untouched by construction — no skill
surfaces are written.

**Clarify decisions:**
| ID | Question | Recommendation | Decision |
|----|----------|----------------|----------|
| C1 | Deliverable path/name | `docs/claude-architect-m1-atlas.html` (sits beside the two existing HTML deliverables) | **locked as recommended** |
| C2 | Also publish as a claude.ai Artifact (private link, shareable) after commit? | Yes — publish at converge; the repo file stays canonical | **locked as recommended** |
| C3 | Concept-card depth | ~150–300 words + one visual per card ("get the concept in a minute") | **locked as recommended** |
| C4 | D4-lite boundary | Self-tests for every captured quiz set, click-to-reveal only; **no** localStorage progress tracking | **locked as recommended** |
| C5 | Stub honesty marker | The 3 recovered cards carry a small "reconstructed — course screen not captured" badge naming their sources | **locked as recommended** |

**Open questions:** none beyond C1–C5.

## Problem

The platform-design bundle (`cases/claude-certification/platform-design/`,
19 OKF Concepts) captures ~29 of the 34 screens of Anthropic's Claude Certified
Architect Foundations Module 1 as flowing prose with screen-navigation debris.
It is complete enough to study from but hard to study *with*: no headings, no
visuals, no cross-links between concepts, three empty stubs, quizzes and a
glossary buried inside larger captures. Anyone preparing for the certification
(the audience) has no way to see the module's whole territory at a glance or to
drill into one concept quickly.

## Scope — source material

| Source | Role |
|---|---|
| 16 non-stub Concepts in the bundle | primary teaching content (per-file inventory via `atlas-content-inventory` workflow) |
| `entrypoint-governance.md:8-80` | canonical 12-section / 34-screen module ToC — the map skeleton |
| `entrypoint-governance.md` entry-point / build-interface / delivery-route tables | recovery source for the `platform-map` stub |
| `pattern-selection.md` + stub frontmatter description | recovery source for the `flexibility-nondeterminism` stub |
| `rag-pipeline.md` frontmatter + `docs/research/certification/CCAR-P_Study_Guide.docx` ("Core concept 2 — RAG pipeline design") | recovery source for the `rag-pipeline` stub |
| `assembly.md` glossary screen | glossary hover-definition data |
| Captured checkpoints/quizzes (checkpoint-platform, primitive-checkpoint, decomposition-chkpt, watch-fan-out quiz, entrypoint-governance scenario MCQs) | self-test layer data (paraphrased) |
| `orientation.md:15-26` four decisions | journey-grouping toggle data |

## Functional requirements

- **FR-1 Single self-contained file.** One HTML file at the C1 path. Zero
  external requests: no CDN, no web fonts (system font stack), all CSS/JS
  inline, all diagrams inline SVG. Works from `file://` offline.
- **FR-2 Mind map.** An SVG map rendering the 12 module sections and all 19
  Concepts (plus embedded checkpoints surfaced by the inventory) as nodes.
  Node kinds visually distinct: concept / watch-out / checkpoint / reconstructed
  stub. Clicking a node opens/scrolls to its concept card. Hovering shows the
  node's one-line description.
- **FR-3 Authored edges.** 20–35 cross-section edges from the inventory
  synthesis, each with a one-line "why" shown on hover; edges toggleable so the
  map can be read clean.
- **FR-4 Journey toggle.** A control that regroups/recolors the map by the four
  design decisions (what Claude owns → shape of work → reference architecture →
  model/context/entry point) instead of the 12-section ToC.
- **FR-5 Concept cards.** One card per Concept: original plain-English
  distillation at C3 depth, the concept's memorable specifics, one inline-SVG
  visual chosen for that concept, and a "for the exam" pointer. Cards are
  readable top-to-bottom as a linear study document even ignoring the map.
- **FR-6 Study layer (D4-lite).** Glossary terms in card prose get hover/tap
  definitions from the merged glossary. Every captured quiz set becomes a
  paraphrased click-to-reveal self-test on (or beside) its card, per C4.
- **FR-7 Stub recovery.** The three stub Concepts get full cards authored from
  the recovery sources in Scope, marked per C5.
- **FR-8 Theming.** Light/dark via CSS custom tokens + `prefers-color-scheme`,
  explicit body background (house precedent:
  `docs/mobile-test-automation-six-way-comparison.html`).
- **FR-9 Originality.** All prose is fresh distillation. No verbatim re-hosting
  of course screens; quiz items paraphrased; concrete specifics (numbers,
  product names, rules of thumb) may be kept exact. A short footer states the
  atlas is an independent, unofficial study aid derived from the author's course
  notes, pointing to Anthropic docs as the authority.
- **FR-10 Registration.** One pointer line in the bundle's `log.md` (and its
  `index.md` if conventions require non-Concept pointers there — curator call),
  plus a 2–4 line entry in `docs/architecture/log.md` (decision log).
- **FR-11 Responsive + accessible baseline.** No horizontal body scroll at
  mobile widths (wide map scrolls inside its own container); map nodes
  keyboard-focusable and activatable; `prefers-reduced-motion` respected;
  self-test reveals work without a pointer device.

## Acceptance criteria (EARS — failure paths first)

- **AC-1** IF JavaScript is disabled or fails, THEN every concept card's full
  content (prose, visuals, quiz questions AND their answers) is still readable
  in document order — interactivity is progressive enhancement, never a
  content gate.
- **AC-2** IF the file is opened from `file://` with networking blocked, THEN
  the page renders identically to the online case (zero external fetches —
  verifiable: no `http(s)://` in `src`/`href` attributes of loaded resources).
- **AC-3** IF a viewer is at ≤375 px width, THEN the body has no horizontal
  scroll; the map pans/scrolls inside its own container.
- **AC-4** IF a concept is one of the three reconstructed stubs, THEN its card
  displays the C5 marker naming its recovery sources.
- **AC-5** IF any card prose reproduces a course screen sentence verbatim
  (>15 consecutive identical words, excluding kept specifics per FR-9), the
  build fails review — spot-checkable by grepping distinctive source phrases
  against the HTML.
- **AC-6** WHEN the page loads, the map shows all 12 sections and ≥19 concept
  nodes with the four node kinds visually distinguishable in both light and
  dark themes.
- **AC-7** WHEN a map node is clicked (or focused + Enter), the viewport
  navigates to that concept's card and the card is visibly highlighted.
- **AC-8** WHEN edges are toggled on and one is hovered/focused, its one-line
  "why" is shown; toggled off, no edge lines render.
- **AC-9** WHEN the journey toggle is active, the same nodes regroup/recolor by
  the four decisions with a visible legend; toggling back restores the
  12-section view.
- **AC-10** WHEN a glossary term in card prose is hovered/tapped, its plain-
  English definition appears; every merged-glossary term used in prose is
  wired.
- **AC-11** WHEN a self-test's reveal control is activated, the paraphrased
  answer + rationale appears; each captured quiz set in Scope has ≥1
  corresponding self-test.
- **AC-12** Ubiquitous: every one of the 19 bundle Concepts maps to exactly one
  card; card count and node count reconcile against the bundle index (the
  fan-out lesson applied to ourselves: coverage verified, not assumed).
- **AC-13** Ubiquitous: the file passes theme sanity in both `light` and `dark`
  `prefers-color-scheme` (body background explicit, no token used only in one
  theme), and total size stays under 1 MB.

## Out of scope / deferred

Bundle-side backfill of the three stub .md files (separate okf-curator task if
wanted) · localStorage progress tracking (D4-full) · multi-module
generator/template (D6 — deferred until a second module bundle matures;
implementation keeps CSS/JS cleanly sectioned so the shell is liftable) ·
hub-and-spoke pagination (D2, rejected at gate) · any change to skill
surfaces, `tooling/`, or `src/`.
