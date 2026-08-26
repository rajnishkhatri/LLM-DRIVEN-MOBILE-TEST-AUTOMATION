# Tasks: CCAR-P Exam Prep Guide

**Spec:** `docs/sdd/specs/ccar-p-prep-guide.spec.md` (SPEC-OK 2026-08-25) ·
**Plan:** `docs/sdd/plans/ccar-p-prep-guide.plan.md` (PLAN-OK 2026-08-25) ·
**Status:** TASKS-OK recorded 2026-08-25 · **T0–T17 complete 2026-08-25**
(verifier GREEN, browser checks passed, gate exit 0; next: Stage-7 review).
Markers: `[deps: …]` must-finish-first · `[par]` parallelizable with siblings.

**Checklist ("unit tests for English"):** every AC in the spec is measurable —
AC-2/4/5/6/7/8/12 and the static half of AC-9/10 by script; AC-1/3 and the
dynamic half of AC-9/10 by DOM/browser inspection (AC-1's end-to-end
observation via a script-stripped copy); AC-11 by script — each part's
`data-covers` slugs reconciled against the plan's mapping table. Two judgment-shaped phrases are
concretized here: AC-9's "names the trap" = the adversarial option's rationale
contains an explicit trap-naming sentence (review item, per-option node
present is the script half); "pitched above the practice bank" (FR-8) =
stem ≥120 words, no surface-eliminable option, ≥1 adversarial option — the
plan's hardening operationalization. No unmeasurable criteria remain.

- **T0 — Donor extraction + meaning-token map.** Re-read the token/component
  block of `docs/architecture/explainers/o7-pipeline-story-v2.html`; fix the
  four meaning tokens (deterministic-teal / model-amber / human-slate /
  risk-red) and their washes for both themes; record the mapping as a comment
  at the top of the new file's CSS.
  Pass: token comment present; every meaning token has light + dark values.
- **T1 — Chassis.** [deps: T0] Full skeleton at `docs/ccar-p-prep-guide.html`:
  head + token CSS (triple-guard theme wiring, explicit body background,
  survey-grid ground, reduced-motion guard), masthead (eyebrow/serif h1/dek/
  byline incl. verify-policy note), sticky semantic key, front-matter shell,
  seven part shells (rule-orn + numbered h2 + weight chip, D1–D7 order),
  gauntlet section shells **including the `article.qitem` markup contract and
  one fully-worked specimen item** (options with `data-role`, per-option
  rationale nodes, `<details>` answer block), annex shell, FR-5 footer with
  relative atlas link.
  Pass: opens from `file://`; both themes sane; zero external resource URLs
  (AC-2); no body h-scroll at 375 px for the shell (AC-3 half); weight chips
  present and summing to 100 (AC-6 half); specimen item readable with JS off
  (AC-1 pattern proven).
- **T2 — Front matter content.** [deps: T1] [par] How-to-use; exam facts
  panel (63 items · 120 min · 720/1000 · seven weights, flagged
  verify-before-sitting); master lens (four properties + through-lines,
  whitelabeled); option-triage method (diagnosis-before-remedy,
  category-error-first, silent-success signatures, adversarial-option
  spotting).
  Pass: facts match the blueprint snapshot recorded in the plan (63 items ·
  120 min · 720/1000 · weights 17/13/19/16/14/14/7); no shingle overlap with
  capture files (AC-4 spot).
- **T3 — Part D1 (style anchor).** [deps: T1] Teaching prose + ≥2 fig-card
  SVGs (decomposition ownership triangle; five-factor sequence with the
  input-vs-path trap) + rules panel + 1–2 checkpoints, per the plan's D1 row.
  **This part is the named voice/format/diagram anchor for T4–T9.**
  Pass: ≥2 fig-cards using only key colors (AC-7); ≥1 native-`<details>`
  checkpoint (AC-8); prose authored from rules, shingle-clean (AC-4);
  section `data-covers` slugs match the plan's D1 row (AC-11 anchor).
- **T4 — Part D2.** [deps: T3] [par] Per the plan's D2 row, complete: four
  properties in depth; tier default + eval-gated swaps; context strategies;
  caching prefix mechanics diagram; RAG decision diagram.
  Pass: anchor standard (AC-4/7/8) + `data-covers` slugs match the D2 row.
- **T5 — Part D3.** [deps: T3] [par] Per the plan's D3 row, complete:
  entry-point trade-off table; constraint matrix (compliance eliminates
  first) diagram; identity/data-minimization path diagram;
  multi-entry-point responsibility map.
  Pass: anchor standard + `data-covers` slugs match the D3 row.
- **T6 — Part D4.** [deps: T3] [par] Per the plan's D4 row, complete: evals
  as acceptance criteria; grading ladder + judge calibration; golden-dataset
  currency; POC→production four dimensions diagram; reliability controls;
  A/B-vs-shadow decision diagram; failure taxonomy + change attribution;
  drift-pairing lesson.
  Pass: anchor standard + `data-covers` slugs match the D4 row.
- **T7 — Part D5.** [deps: T3] [par] Per the plan's D5 row, complete:
  four-layer stack + three control points diagram (fail-closed); injection
  vectors + risk catalog; fairness injection points + decision logging
  diagram; routing-by-stakes; register (control/owner/evidence); skill
  supply-chain audit.
  Pass: anchor standard + `data-covers` slugs match the D5 row.
- **T8 — Part D6.** [deps: T3] [par] Per the plan's D6 row, complete:
  discovery four buckets + translation table; tradeoff three-element frame
  diagram; feedback-loop-above-observability diagram + scheduled regulated
  checkpoints; three-reader documentation + completeness test; outcome six
  fields.
  Pass: anchor standard + `data-covers` slugs match the D6 row.
- **T9 — Part D7.** [deps: T3] [par] Per the plan's D7 row, complete: four
  team-setup decisions; champion-and-batch diagram; four distribution
  mechanisms diagram; spend posture; inside-vs-beside; checklist-as-practice;
  symptom→cause runbooks.
  Pass: anchor standard + `data-covers` slugs match the D7 row.
- **T10 — Gauntlet A authoring.** [deps: T1] [par with T3–T9] 15 static items
  per the plan's re-skin table — lesson invariant, setting replaced; specimen
  contract followed; every item `data-domain`-tagged.
  Pass: 15 `article.qitem`; zero grep hits for source-setting markers
  (AC-5); lesson column reconciles 1:1 against the table.
- **T11 — Gauntlet B authoring.** [deps: T1] [par with T10] 15 static items
  from the session seeds (M2–M4 coverage), upgraded to the specimen contract.
  Pass: 15 items, domains tagged, seeds' 15 topics all present.
- **T12 — Hardening pass.** [deps: T10, T11] Across all 30 items: 5 options
  each; ≥1 `data-role="adversarial"` + ≥2 `data-role="distractor"` per item;
  5–7 items converted to multi-select (`data-multi`) where the lesson
  naturally splits; stems ≥120 words; no surface-eliminable option; every
  rationale addresses all five options and names the adversarial trap.
  Pass: static counts all green (AC-9/AC-10 static half); spot review of 5
  random items against the difficulty operationalization.
- **T13 — Quiz engine.** [deps: T12] ~150–180-line vanilla-JS enhancement per
  the plan: selection affordances (real buttons, `aria-pressed`),
  single-select grade-on-choice / multi-select confirm, per-option verdict +
  rationale reveal, per-gauntlet summary (n/15 + per-domain tally from tags),
  reload-to-reset note; CSS-only motion under reduced-motion guard.
  Pass: AC-9/AC-10 dynamic behavior demonstrable; static form untouched when
  JS is off (AC-1).
- **T14 — Quick-revision annex.** [deps: T3–T9] [par with T10–T13] Per-domain
  decision-rule grid, whitelabeled. Pass: all seven domains present;
  shingle-clean (AC-4).
- **T15 — Verifier + full static pass.** [deps: T2, T13, T14]
  Write + run `verify_prep_guide.py` (session scratchpad, outside the repo;
  plan §Verification): AC-2 resource scan · AC-4 15-word shingle vs all
  bundle .md bodies with terminology exclusion list · AC-5 source-marker
  grep · AC-6 part order + weight sum · AC-7 fig-card count + SVG color
  audit · AC-8 checkpoint count · AC-9/10 static counts (15+15 items, 5
  options, role tags, 5–7 multi, rationale nodes non-empty) · **AC-11
  `data-covers` reconciliation against the script-held mapping-table slug
  list** · FR-11 atlas-link presence in the footer · AC-12 size ≤1 MB +
  token/theme audit.
  Pass: all checks green, exit 0.
- **T16 — Browser verification.** [deps: T15] Browser pane via `atlas-docs`:
  both themes, 375 px + desktop (AC-3), checkpoint reveals, one full
  keyboard-only item walk, single- and multi-select grading, summary + domain
  tally, screenshot evidence; **AC-1 end-to-end pass**: generate a
  script-stripped copy (all `<script>` blocks removed) into the session
  scratchpad, serve it, and walk the whole document for document-order
  readability — teaching prose, checkpoint answers, all 30 items with
  answers and rationales. Pass: AC-1/3 observed (AC-1 via the stripped
  copy); AC-9/10 dynamic halves observed.
- **T17 — Registration + gate baseline.** [deps: T16] Append one dated
  pointer line to `cases/claude-certification/log.md`; 2–4 line entry in
  `docs/architecture/log.md`; run `python3 tooling/skill-sync/skill_sync.py
  check` from the repo root. Pass: gate exit 0; both log lines present
  (FR-11). *(No Artifact task — C4 rejected publication.)*

**AC → task coverage:** AC-1 T1/T13/T16 · AC-2 T1/T15 · AC-3 T1/T16 · AC-4
T2–T9/T14/T15 · AC-5 T10/T15 · AC-6 T1/T15 · AC-7 T3–T9/T15 · AC-8 T3–T9/T15
· AC-9 T12/T13/T15/T16 · AC-10 T12/T13/T15/T16 · AC-11 T3–T9/T15
(`data-covers` script reconciliation against the mapping table) · AC-12
T1/T15. No
zero-coverage criteria; no task without a criterion.
