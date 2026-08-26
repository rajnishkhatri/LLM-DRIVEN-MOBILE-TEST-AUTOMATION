# Plan: Claude Architect Module-1 Interactive Atlas

**Spec:** `docs/sdd/specs/platform-design-atlas.spec.md` (SPEC-OK 2026-08-23,
C1–C5 locked). **Status:** awaiting PLAN-OK.
**Change class:** documentation deliverable; no new dependency; no ⚠️ Ask-first
trigger → no ADR; decision-log entry at registration (FR-10).

## A1 — simplest machinery statement

One hand-authored HTML file with one small vanilla-JS map engine reading one
embedded JSON block. Rejected as over-machinery: any JS framework or graph
library (new dep → ADR), a build step (repo has none), hand-plotted SVG
coordinates for 26 nodes (error-prone; a ~60-line deterministic layout
function is less total machinery than 26×2 hand-tuned coordinates), and a
generator for future modules (D6, deferred at brainstorm).

## Architecture of the deliverable

`docs/claude-architect-m1-atlas.html` (C1), structured top to bottom:

1. **Head + CSS tokens.** House token pattern from
   `docs/mobile-test-automation-six-way-comparison.html` (`--ground/--panel/
   --ink/--rule/--accent…`), extended with four node-kind hues and four
   journey-decision hues. Theme wiring uses the artifact-compatible superset —
   light on bare `:root`, dark under
   `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) }`
   AND `:root[data-theme="dark"]` — valid standalone (AC-13) and correct if
   the same content is later published as an Artifact (C2). System font stack;
   zero external requests (AC-2).
2. **Header** — title, one-paragraph orientation, view controls (edges toggle,
   journey toggle: plain `<button aria-pressed>`), legend.
3. **Map container** — `<figure>` with its own `overflow:auto` (AC-3); the SVG
   is JS-rendered at load from the data block. `<noscript>` note: "map needs
   JS — the cards below are the same content in course order" (AC-1: the map
   is navigation; content lives in cards).
4. **Data block** — one `<script type="application/json" id="atlas-data">`:
   nodes (id, label, kind, section, journey-decision, one-line description),
   33 edges (from, to, why), glossary (81 terms). Derived offline from
   `scratchpad/atlas-content-map.json`; the HTML embeds only the final data.
5. **Concept cards** — one `<section class="card" id="<node-id>" data-kind=…>`
   per Concept, grouped under 12 module-section headings, document order =
   course order (AC-1 linear readability). Each card: title, kind chip,
   ~150–300-word plain-English distillation (C3), one inline `<svg>` visual
   (from the inventory's `visual_idea`), a "memorable specifics" strip, a
   "for the exam" pointer, glossary terms as
   `<span class="dfn" data-term="…">` (tooltip via CSS/JS; term still plain
   text without JS — AC-1). Stub cards add the C5 badge. Self-tests are native
   `<details><summary>` — click-to-reveal with **zero JS** (AC-1/AC-11), quiz
   items paraphrased from the content map (AC-5).
6. **Glossary section** — the merged 81-term glossary rendered as a browsable
   card (also the no-JS fallback for tooltips).
7. **Footer** — FR-9 unofficial-study-aid note + pointer to Anthropic docs;
   provenance line naming the bundle.

## Map engine design (~150 lines vanilla JS)

- **Layout:** deterministic radial "clock" — 12 sections arranged 01→12
  around a center hub ("Module 1"), each section's nodes fanned on a second
  ring within the section's angular slice. Pure arithmetic at load; no
  physics, no animation loops (reduced-motion trivially respected — the only
  animations are CSS transitions, disabled under
  `prefers-reduced-motion: reduce`).
- **Node kinds:** concept (filled circle), watch-out (warning triangle),
  checkpoint (ring/target), reconstructed stub (dashed outline) — shape +
  hue so kinds survive both themes and color-blindness (AC-6).
- **Interaction:** nodes are `<a href="#<card-id>">` inside SVG — click AND
  keyboard focus/Enter navigate natively (FR-11, AC-7); JS adds
  `:target`-plus-class card highlight and hover/focus tooltip with the node
  description. Edges render as quadratic Béziers only while the edge toggle
  is on; hover/focus on an edge shows its "why" (AC-8).
- **Journey toggle:** each node carries `data-journey`; toggling swaps the
  fill attribute source and the legend — same nodes, recolored/regrouped
  visually by the four decisions; off restores section coloring (AC-9).

## Content pipeline (the real work)

Cards are authored (not generated) from two sources per concept: the
inventory in `scratchpad/atlas-content-map.json` + the source .md itself for
fidelity spot-checks. Originality rule AC-5 enforced by construction (authors
write from key_points, never copy) and verified by shingle check (below).
Stub recovery per spec Scope: platform-map ← entrypoint-governance tables +
checkpoint-platform; flexibility-nondeterminism ← its description +
pattern-selection; rag-pipeline ← its description + CCAR-P study guide
§"Core concept 2" (extracted at `scratchpad/ccarp-study-guide.txt`).

Implementation loads `artifact-design` + `artifact-diagramming` skills before
writing the page (harness requirement for Artifact-published HTML; also the
right design calibration for the 19 mini-diagrams).

## Verification harness (AC → check)

`scratchpad/verify_atlas.py` (stdlib-only, not committed — a converge tool,
not a repo gate):
- AC-2: scan for `http(s)://` in src/href/url() of loaded resources (footer
  informational links to anthropic.com allowed as plain `<a>` navigation —
  they are not fetched resources).
- AC-5: 15-word shingle overlap between every bundle .md body and the HTML
  text (exclusion list for kept specifics).
- AC-12: count `<section class="card">` == 19 == count of concept nodes in
  the data block; every bundle Concept basename appears exactly once.
- AC-13: file size < 1 MB; every CSS custom property defined on bare `:root`;
  body background uses a token.
- AC-6/10/11 (static half): node-kind count, `data-term` spans all resolve
  against the glossary JSON, ≥1 `<details>` self-test for each of the quiz
  sources named in spec Scope.
Browser checks (Browser pane): AC-1 (JS disabled via
`javascript_tool`-free load is not possible in-pane — instead: verify cards +
`<details>` + `<noscript>` in DOM and reason from native-element behavior),
AC-3 (375 px, no body h-scroll), AC-7/8/9 interactions, both themes
(`resize_window` colorScheme), reduced-motion by CSS audit.

## File-level touchpoints

| Path | Action |
|---|---|
| `docs/claude-architect-m1-atlas.html` | **create** (the deliverable) |
| `cases/claude-certification/platform-design/log.md` | append one dated pointer line (FR-10) |
| `docs/architecture/log.md` | append 2–4 line decision-log entry (FR-10) |
| `scratchpad/atlas-data.json`, `scratchpad/verify_atlas.py` | working assets, not committed |
| everything else | untouched — no skill surfaces, no `tooling/`, no `src/` |

## Risks

- **Verbatim leakage** (AC-5): mitigated by authoring from inventories +
  shingle check.
- **Card-authoring drift across batches** (voice/format inconsistency):
  mitigated by a card template + example card written first (T4) and named
  the style anchor for all batches.
- **Coverage drop during fan-out authoring** — exactly the watch-fan-out
  failure: mitigated by AC-12 reconciliation in the verifier, run after every
  batch merge, counts asserted not assumed.
- **Size creep from 19 inline SVGs**: budget ~2–6 KB each; verifier enforces
  the 1 MB ceiling (expected total ~250–400 KB).
