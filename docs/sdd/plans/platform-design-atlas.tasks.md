# Tasks: Claude Architect Module-1 Interactive Atlas

**Spec:** `docs/sdd/specs/platform-design-atlas.spec.md` · **Plan:**
`docs/sdd/plans/platform-design-atlas.plan.md` · **Status:** awaiting TASKS-OK.
Markers: `[deps: …]` must-finish-first · `[par]` parallelizable with siblings.

**Checklist ("unit tests for English"):** every AC in the spec is measurable —
AC-1/2/3/5/12/13 by script or DOM inspection, AC-4/6/7/8/9/10/11 by browser
check against enumerable elements. No unmeasurable criteria found; AC-5's
"distinctive phrase" spot-check is made concrete as the 15-word shingle scan.

- **T0 — Design-skill load + style anchor.** Load `artifact-design` +
  `artifact-diagramming`; re-read house token block in
  `docs/mobile-test-automation-six-way-comparison.html`.
  Pass: both skills loaded in-session before any HTML is written.
- **T1 — Data derivation.** [deps: T0] From `scratchpad/atlas-content-map.json`
  derive `scratchpad/atlas-data.json`: 26 nodes (id/label/kind/section/
  journey/description), 33 edges (from/to/why), 81-term glossary, quiz-source
  manifest. Node ids = bundle basenames (AC-12 keys). Every node carries a
  journey-decision assignment (AC-9 data).
  Pass: python json sanity — 12 sections, 19 concept-card nodes, 4 kinds
  present, all edge endpoints resolve, journey values ∈ {1,2,3,4}.
- **T2 — Scaffold + tokens + chrome.** [deps: T1] Full HTML skeleton at
  `docs/claude-architect-m1-atlas.html`: head, token CSS (triple-guard theme
  wiring, explicit body background), header + controls + legend, empty map
  figure with `<noscript>`, section headings ×12, glossary section shell,
  FR-9 footer. Embed the data block.
  Pass: opens from `file://`; both themes sane (AC-13 half); zero external
  resource URLs (AC-2); body h-scroll absent at 375 px for the shell (AC-3
  half).
- **T3 — Map engine.** [deps: T2] Radial clock layout, kind shapes, SVG-native
  `<a href="#…">` nodes, hover/focus description tooltip, card highlight on
  arrival, edge toggle + Bézier edges + hover "why", journey toggle + legend
  swap, CSS-transition-only motion under `prefers-reduced-motion` guard.
  Pass: AC-6, AC-7, AC-8, AC-9 all demonstrable in the Browser pane;
  keyboard-only walk reaches and activates ≥3 nodes (FR-11).
- **T4 — Card template + §01–02 (style anchor).** [deps: T2]
  `orientation`, `claude-behave` cards: template markup, C3 depth, one inline
  SVG each, memorable-specifics strip, "for the exam" line, dfn spans.
  **This card pair is the named voice/format anchor for T5–T10.**
  Pass: both cards read plain-English in ≤1 min each; AC-5 shingle scan clean
  for these two files.
- **T5 — §03 Platform Map & Primitives.** [deps: T4] [par] Cards:
  `platform-map` (stub badge, C5), `ai-primitive`, `checkpoint-platform` +
  `primitive-checkpoint` (as `<details>` self-tests). Pass: 4 cards to anchor
  standard; stub badge names sources (AC-4); self-tests reveal without JS.
- **T6 — §04 Decomposition.** [deps: T4] [par] Cards: `decomposition`,
  `deterministic-drift` (watch-out styling), `decomposition-chkpt`
  (self-test). Pass: anchor standard; watch-out kind visually distinct.
- **T7 — §05 Pattern Selection.** [deps: T4] [par] Cards: `pattern-selection`,
  `flexibility-nondeterminism` (stub badge), `multi-agent`, `watch-fan-out`
  (+ its embedded critique quiz as self-test). Pass: anchor standard; AC-4 on
  the stub.
- **T8 — §06–07 Reference Architectures + RAG.** [deps: T4] [par] Cards:
  `reference-architecture` (incl. retrieval-vs-live-state watch-out content +
  its checkpoint self-test), `rag-pipeline` (stub badge; CCAR-P §Core-concept-2
  + description skeleton). Pass: anchor standard; AC-4 on the stub.
- **T9 — §08–10 Model/Prompting/Entry points.** [deps: T4] [par] Cards:
  `model-context-strategy`, `prompting-architecture` (its 4 exercise items as
  self-tests), `entrypoint-governance` (6 scenario MCQs paraphrased as
  self-tests). Pass: anchor standard; AC-11 count for these quiz sources.
- **T10 — §11 Assembly + glossary wiring.** [deps: T5–T9] `assembly` card
  (four-architectures comparison visual + its 2 self-tests); render the
  81-term glossary section; wire every `data-term` span page-wide; tooltip
  CSS/JS. Pass: AC-10 — every span resolves, spot-check tooltips in browser.
- **T11 — Verifier + full static pass.** [deps: T10] Write + run
  `scratchpad/verify_atlas.py` (plan §Verification): AC-2 resource scan, AC-5
  shingle scan vs all 16 source bodies, AC-12 reconciliation (19 = cards =
  concept nodes; every basename once), AC-13 size + token audit, AC-6/10/11
  static counts. Pass: all checks green, exit 0.
- **T12 — Browser verification.** [deps: T11] Browser pane: both themes,
  375 px + desktop, node click/keyboard nav, edge + journey toggles, tooltip
  and self-test interactions, screenshot evidence. Pass: AC-1 (DOM: content
  complete outside JS-built map; `<details>` native), AC-3, AC-7/8/9 observed.
- **T13 — Registration + gate baseline.** [deps: T12] Append pointer line to
  `cases/claude-certification/platform-design/log.md`; 2–4 line entry in
  `docs/architecture/log.md`; run `python3 tooling/skill-sync/skill_sync.py
  check` from repo root. Pass: gate exit 0; both log lines present (FR-10).
- **T14 — Artifact publish (C2).** [deps: T13] Body-only variant with
  `<title>`, publish via Artifact tool (stable favicon), hand the user the
  repo path + private link. Pass: artifact renders identically in both
  viewer themes; link delivered.

**AC → task coverage:** AC-1 T2/T12 · AC-2 T2/T11 · AC-3 T2/T12 · AC-4 T5/T7/
T8 · AC-5 T4/T11 · AC-6 T3/T11 · AC-7 T3/T12 · AC-8 T3/T12 · AC-9 T3/T12 ·
AC-10 T10/T11 · AC-11 T5–T10/T11 · AC-12 T11 · AC-13 T2/T11. No zero-coverage
criteria; no task without a criterion.
