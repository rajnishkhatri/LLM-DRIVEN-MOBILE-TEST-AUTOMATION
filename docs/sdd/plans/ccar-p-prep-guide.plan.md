# Plan: CCAR-P Exam Prep Guide

**Spec:** `docs/sdd/specs/ccar-p-prep-guide.spec.md` (SPEC-OK 2026-08-25,
C1–C3 locked as recommended, C4 overridden to repo-file-only).
**Status:** PLAN-OK recorded 2026-08-25.
**Change class:** documentation deliverable; no new dependency; no ⚠️
Ask-first trigger → no ADR; decision-log entry at registration (FR-11).

## A1 — simplest machinery statement

One hand-authored HTML file: the v2 donor's CSS component vocabulary plus one
small vanilla-JS quiz-enhancement script that upgrades statically authored
quiz markup in place. Rejected as over-machinery: any JS framework or quiz
library (new dep → ADR), a build step (repo has none), porting the practice
bank's SPA shell (screens/timer/scaled scoring — a mode-switching app, wrong
shape for a long-read document and more code than the content needs), a
second data representation for quiz items (JSON + rendered DOM would duplicate
truth; the DOM *is* the data, tagged with `data-*` attributes), and a
multi-exam generator (same D6 deferral as the atlas).

## Architecture of the deliverable

`docs/ccar-p-prep-guide.html` (C1), top to bottom:

1. **Head + CSS tokens.** The v2 donor's token system (paper/ink neutrals,
   serif display + mono labels + sans body, survey-grid ground, fig-card,
   callout, pull quote, rule-orn, owner-pill, scorecard table) carried over
   and trimmed to what the guide uses. Meaning colors re-keyed for exam
   content: **deterministic control** (teal), **model / probabilistic**
   (amber), **human decision** (slate), **failure / risk** (red-brown) — the
   four semantics every module's diagrams actually need. Theme wiring uses
   the house superset — light on bare `:root`, dark under
   `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) }`
   AND `:root[data-theme="dark"]` (AC-12). System fonts; zero external
   requests (AC-2).
2. **Masthead** — eyebrow (`CCAR-P · UNOFFICIAL PREP`), serif working title
   (authoring call at T-time; candidate: "Seven Rooms" — the exam as a
   territory of seven weighted rooms), italic dek, mono byline (audience /
   reading time / status / "verify current exam policy on the official
   page").
3. **Sticky semantic key** — the four meaning colors, one legend, always in
   view (FR-3).
4. **Front matter part** — how to use the guide; exam facts panel (63 items ·
   120 min · 720/1000 · 7 domains with weights; flagged as
   verify-before-sitting); the **master lens** (four properties + the
   cross-module through-lines, whitelabeled); the **option-triage method**
   (diagnosis-before-remedy, category-error-first, silent-success signatures,
   and how to spot an adversarial option) (FR-10).
5. **Parts D1–D7** — rule-orn divider + numbered serif h2 + weight chip; each
   part: teaching prose in the measure column, ≥2 fig-card SVG mechanism
   diagrams (FR-6), a "rules that decide questions" panel (scorecard table or
   callout), 1–2 native-`<details>` checkpoints (FR-7). Content per the
   mapping table below; each part's `<section>` carries a `data-covers`
   attribute listing slugs for its mapping-row items — the machine anchor
   that makes AC-11 a scripted reconciliation instead of an assumption.
6. **The Gauntlets part** — two 15-item quizzes (FR-8). Items are authored as
   **static semantic HTML** — one `<article class="qitem" data-domain="D#"
   data-multi>` per item; options as list entries carrying
   `data-role="correct|distractor|adversarial"` and a per-option rationale
   element; the full rationale block sits inside a native `<details>` (no-JS
   fallback = readable answers, AC-1). The engine enhances this markup:
   selection UI, grading, per-option verdicts, per-gauntlet summary.
7. **Quick-revision annex** — the per-domain decision rules distilled to one
   compact grid (whitelabeled descendant of the revision sheet).
8. **Footer** — independent/unofficial note; Anthropic official pages as the
   authority for exam policy, models, pricing; provenance line naming the
   study-notes bundle; relative link to the M1 atlas. Direction call: the
   guide links **to** the atlas; the shipped atlas file is not edited
   (touching a shipped deliverable to add a backlink is scope creep — FR-11's
   cross-link is satisfied one-way plus the bundle log pointer).

## Module → domain mapping (drives AC-11)

| Part | Weight | Sourced from (bundle) | Load-bearing content |
|---|---|---|---|
| D1 Solution Design & Architecture | 17% | platform-design | decomposition (Claude/systems/humans); pattern = autonomy granted, five factors in sequence, input-vs-path variability; reference architectures + retrieval-vs-live-state; multi-agent failure asymmetry; entry-point governance (constraints eliminate) |
| D2 Models, Prompting & Context | 13% | platform-design | four properties in depth; tier default + eval-gated swaps; context strategies; prompt-caching prefix mechanics; RAG chunk/index/fusion decisions |
| D3 Integration | 19% | enterprise-integration-production + platform-design + stakeholder-engagement | five entry points and their trade-offs; compliance constraint matrix (HIPAA/GDPR/FedRAMP/privilege/residency) eliminating routes first; server-side identity; minimum-necessary data; multi-entry-point responsibility map |
| D4 Evaluation, Testing & Optimization | 16% | enterprise-integration-production (+ deterministic-drift lesson from platform-design) | evals as acceptance criteria; grading ladder + judge calibration; golden-dataset currency; POC→production four dimensions; reliability controls; A/B vs shadow; failure taxonomy + change attribution |
| D5 Governance, Safety & Risk | 14% | responsible-ai | safety stack (four layers, silent-gap failure); three control points + fail closed; indirect injection; risk catalog; fairness injection points + decision logging; review routing by stakes; compliance register (control/owner/evidence); skill supply-chain audit |
| D6 Stakeholder Comms & Lifecycle | 14% | stakeholder-engagement | discovery four buckets + translation table; tradeoff = gain/give-up/reversal cost; feedback loop above observability + scheduled checkpoints; documentation three readers + completeness test; outcome document six fields |
| D7 Developer Productivity & Enablement | 7% | team-enablement | team setup four decisions; champion-and-batch as learning system; skills distribution four mechanisms = governance postures; spend posture; inside-vs-beside workflows; verification checklist as practice; symptom→cause runbooks |

## Gauntlet content design

**Gauntlet A** (re-skin of the recorded M1+M5 session — lesson kept, story
replaced; AC-5 checks the industry+actor pairing changed):

| # | Lesson (kept) | Source setting → new setting |
|---|---|---|
| 1 | retrieval vs live transactional state | telecom call center → energy retailer's tariff/balance assistant |
| 2 | three enablement layers, not one root cause | fintech 340-dev rollout → insurance carrier 280-dev rollout |
| 3 | five factors; input ≠ path variability | prior-auth processing → municipal permit processing |
| 4 | symptom → architecture cause at 2 a.m. | freight tracking → parcel-locker network |
| 5 | prefix caching, static-first ordering | contract review → audit-policy Q&A desk |
| 6 | skills distribution = governance postures | insurer 2,000 eng → retail bank 1,400 eng |
| 7 | orchestrator vs subagent failure asymmetry | competitive-landscape reports → market-entry research |
| 8 | checklist as ritual vs practice | generic PR audit → medical-device firmware PRs |
| 9 | constraints eliminate entry points | wealth management → broker-dealer research desk |
| 10 | inside vs beside the workflow | backend guild → data-platform guild |
| 11 | decomposition across Claude/systems/humans | airline IROPS → hotel-chain overbooking recovery |
| 12 | champion-and-batch = learning system | healthcare CTO → telco CTO, 450 engineers |
| 13 | chunking by structure + hybrid indexing | pharma archive → aerospace maintenance manuals (AD citations) |
| 14 | four properties, three symptoms, one lens | hospital drug interactions → veterinary pharmacy interactions |
| 15 | deterministic gates drift-blind without sampling | product descriptions → real-estate listing generation |

**Gauntlet B** — fresh items over the M2–M4 coverage map drafted this session
(evals golden dataset · safety stack boundary · discovery elicitation · POC
cost/reliability · three control points + indirect injection · tradeoff
reversal cost · sizing verdicts + boundary conditions · fairness injection
points · feedback loop + scheduled checkpoints · identity + data
minimization · routing by stakes · documentation completeness test · A/B vs
shadow · compliance register evidence · outcome document). Scenarios were
invented in-session (not course captures) and are used as authoring seeds;
each is upgraded from 4 to 5 options.

**Hardening pass (both gauntlets, per C3):** every item gets a 5th option
where needed; ≥1 option tagged `adversarial` (right-sounding conclusion via
flawed reasoning, or correct-in-an-adjacent-scenario); 5–7 of the 30 items
converted to multi-select where the lesson naturally splits ("select the two
controls that must exist"); no option eliminable by surface reading alone;
rationale text addresses all five options and names the adversarial trap
(AC-5/AC-9).

## Quiz engine design (~150–180 lines vanilla JS)

- **Enhancement, not rendering:** on load, for each `article.qitem` the
  engine hides the static rationale `<details>`, decorates options with
  selection affordances (options become buttons; multi-select items get a
  confirm control), and wires grading. No JS → the untouched static form
  remains fully readable (AC-1).
- **Grading:** single-select grades on choice; multi-select on confirm.
  Per-option verdict chips + the per-option rationale lines revealed;
  item stamped correct/incorrect.
- **Summary:** per-gauntlet score block (n/15) + per-domain tally computed
  from `data-domain` tags (AC-10); reset = reload (documented inline).
- **Accessibility:** options are real `<button>`s (keyboard for free),
  `aria-pressed` selection state, focus-visible styles from the donor;
  animations are CSS-only and disabled under `prefers-reduced-motion`.

## Content pipeline (the real work)

Teaching prose is authored fresh from the revision sheet + module reads (all
five bundles already inventoried this session); the whitelabel rule (C2) is
enforced by construction — write from decision rules, never from capture
prose — and verified by shingle check. Diagrams are designed per part against
FR-6's mechanism test: each shows a path, an asymmetry, an ordering, or a
placement that the neighboring prose argues. No artifact-design skill load is
required (C4: no Artifact publication; the v2 donor is the design system).

## Verification harness (AC → check)

`verify_prep_guide.py` in the **session scratchpad** (outside the repo;
stdlib-only converge tool, never committed):
- AC-2: scan `src`/`href`/`url()` of loaded resources for `http(s)://`
  (plain informational `<a>` links to anthropic.com allowed — navigation, not
  fetched resources).
- AC-4: 15-word shingle overlap between every
  `cases/claude-certification/**/*.md` body and the HTML text, with a
  terminology exclusion list (framework names being taught).
- AC-5: grep the HTML for Gauntlet A source-setting markers ("telecom",
  "IROPS", "900-agent", "wealth-management", …) — zero hits expected; the
  re-skin table above is the review record.
- AC-6: parts D1–D7 present in order; weight chips parse and sum to 100.
- AC-7: ≥2 `fig-card` figures per part; every fill/stroke in inline SVGs
  resolves to a declared token (no ad-hoc meaning colors).
- AC-8: ≥1 checkpoint `<details>` per part.
- AC-11: every part's `data-covers` slugs reconcile 1:1 against the
  script-held slug list derived from the mapping table above — missing or
  extra slugs fail.
- FR-11: the relative atlas link (`claude-architect-m1-atlas.html`) present
  in the footer.
- AC-9/AC-10 (static half): exactly 15 `article.qitem` per gauntlet; 5
  options each; per item ≥1 `data-role="adversarial"` and ≥2
  `data-role="distractor"`; valid `data-domain`; 5–7 `data-multi` items
  across 30; every option has a non-empty rationale node.
- AC-12: file ≤ 1 MB; tokens defined on bare `:root`; body background uses a
  token; dark overrides guarded per the house pattern.
Browser checks (Browser pane, via the `atlas-docs` server): AC-3 (375 px, no
body h-scroll), grading interactions + summary (AC-9/10 dynamic half), both
themes via `resize_window` colorScheme, keyboard walk of one full item, and
the AC-1 end-to-end observation — a script-stripped copy of the page (all
`<script>` blocks removed, generated into the session scratchpad and served)
walked for document-order readability of prose, checkpoint answers, and all
30 items with answers/rationales.

## File-level touchpoints

| Path | Action |
|---|---|
| `docs/ccar-p-prep-guide.html` | **create** (the deliverable) |
| `cases/claude-certification/log.md` | append one dated pointer line (FR-11) |
| `docs/architecture/log.md` | append 2–4 line decision-log entry (FR-11) |
| `verify_prep_guide.py` (session scratchpad) | working asset, outside the repo |
| `docs/claude-architect-m1-atlas.html` | **untouched** (one-way link from the guide) |
| everything else | untouched — no skill surfaces, no `tooling/`, no `src/` |

## Risks

- **Verbatim leakage** (AC-4): highest on D5–D7 where module phrasing is
  distinctive; mitigated by authoring-from-rules + shingle check with a
  reviewed exclusion list.
- **Difficulty calibration is subjective** ("harder than the bank"):
  operationalized per item — stem ≥120 words, no surface-eliminable option,
  adversarial option present, closest-call margin reviewed in the hardening
  pass; the hardening pass is a separate task, not folded into first
  authoring.
- **Re-skin drift** (Gauntlet A): a new story can silently change the lesson;
  the mapping table's lesson column is the invariant checked at review.
- **Fan-out coverage loss** across 7 parts + 30 items + ~16 diagrams:
  verifier reconciles counts after every authoring batch — asserted, not
  assumed.
- **Size creep** (~16 SVGs + 30 long items): budget 2–6 KB per SVG, expected
  total 450–650 KB against the 1 MB ceiling; verifier enforces.
