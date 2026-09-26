# Plan: Insurance Claim Processor Explainer — "The Workflow the Model Never Controls"

**Spec:** `docs/sdd/specs/claim-processor-story.spec.md` (SPEC-OK
2026-09-23, C1–C5 locked as recommended).
**Status:** **PLAN-OK (2026-09-23)** — owner approved at the gate; tasks
decomposed → `claim-processor-story.tasks.md`.
**Change class:** documentation deliverable; no new dependency; no
⚠️ Ask-first trigger → no ADR; decision-log entry at registration
(FR-12).

## A1 — simplest machinery statement

One hand-authored HTML file with **zero required JavaScript**: linear
narrative, anchors, pure-CSS chips and lanes, static inline SVG figures.
Rejected as over-machinery: frameworks/chart libraries (new dep → ADR),
a build step (repo has none), a JS figure engine (14 static figures are
cheaper hand-authored), downloaded AWS icon assets (C2 rejected them),
and a data-driven card generator (~10 cards hand-authored from one
template is less total machinery).

**G1 note — the one new convention:** an **SVG `<symbol>` icon library**
(defined once in a `<defs>` block, placed via `<use>`). What it buys:
single-source icon geometry across ~14 figures (edit once, correct
everywhere), a hard byte saving versus repeated paths, and a
machine-checkable rule (AC-4: `<use>`-only placements, each with a
visible label). The simpler thing rejected: drawing each icon inline per
figure — cheaper for one figure, strictly worse for fourteen.

## Architecture of the deliverable

`docs/architecture/explainers/insurance-claim-processor-story.html`,
top to bottom:

1. **Document shell + head + CSS tokens.** Standard shell (FR-11). The
   aws-ai-architect-story palette verbatim (`--det` teal envelope,
   `--llm` amber model, `--human` slate, paper/ink/rule/wash tokens,
   serif/sans/mono stacks, 66ch measure), three-block theme pattern
   (FR-10), explicit `body { background: var(--paper) }`. Two additions:
   `--status` (the C4 `designed — not yet deployed` chip color — reuse
   `--human` slate family, dashed border, so it reads "planned" without
   inventing a new hue) and the **AWS category hex constants inside the
   symbol defs only** (FR-5 carve-out): Compute `#ED7100`, Storage
   `#7AA116`, ML `#01A88D`, App Integration `#E7157B`, Security
   `#DD344C`, Mgmt/Governance `#E7157B` family — each glyph on a
   `var(--paper)` plate so contrast holds in both themes.
2. **SVG symbol library** — one hidden `<svg><defs>` block right after
   `<body>`: `sym-s3` (green bucket), `sym-lambda` (orange λ),
   `sym-sfn` (pink state-machine), `sym-bedrock` (ML-green model chip),
   `sym-guardrail` (ML-green shield), `sym-iam` (red key), `sym-kms`
   (red lock), `sym-appconfig` (mgmt-pink sliders), `sym-cloudwatch`
   (mgmt-pink gauge), `sym-sns` (pink bell), plus neutral glyphs:
   `sym-doc` (claim document), `sym-person` (reviewer), `sym-token`
   (task token), `sym-gate` (decision gate). Simplified original
   geometry (C2) — evocative of the AWS iconography, not traced from the
   official assets. Every `<use>` placement carries an adjacent visible
   `<text>` label (AC-4).
3. **Masthead.** Title + dek, the FR-6-style seam statement (≤3
   sentences: the design doc, ADRs, and walkthrough are the sources of
   record; this page is the synthesis you read first), byline (audience
   / reading time / as-of 2026-09-23 / status: partially deployed —
   see footer).
4. **Sticky legend** (`top:0`, the page's only sticky element): amber
   model lane / teal envelope lane / slate human accents / the
   `.unverified` chip / the `.status` chip ("dashed = designed, not yet
   deployed"). Kept to one wrapping row (AC-3).
5. **Icon key strip** — a non-sticky one-row figure directly under the
   masthead showing each symbol once with its service name. Doubles as
   the symbol-library smoke test in both themes.
6. **Parts I–IX** — `<section class="part" id="part-1…9">` per the spec
   structure table. Each Part: kicker + h2, **hero figure first**, then
   plain-English prose (FR-8 voice), planned text-explainer beats
   (FR-4), closing `<aside class="envelope-beat">` with card back-links.
7. **Part IX — decision map + cards.** F14 map figure, then ~10
   `<article class="decision-card" id="d-host|d-hitl|d-guardrail|d-iam|
   d-rag|d-docunderstand|d-config|d-breaker|d-ensemble|d-degrade">`,
   each: the question, trade-off `<table>` in an `overflow-x` wrapper,
   `.default-line` ("default … deviate when …"), ADR id, anchors both
   ways. The two supersessions (0003→0004; clinic-C1→0012 + brief-§4→
   0013) rendered as a plain "this reversed an earlier call, and why"
   line on their cards (FR-8 — no temporal badge grammar).
8. **Scorecard table.** One row per compressed topic (result contract /
   provenance, resilience knobs C2/C7/C9/C11, no-memory decision, eval
   findings, style/quanta decision, remaining work): one-line what ×
   owning lane × decision-card anchor × source. Status chips per
   occurrence (AC-5).
9. **Footer.** About (synthesis statement + the source-artifact list as
   in-repo relative links), Honesty note (`.unverified` + status-chip
   semantics), **live-status line (C4):** what ran on real AWS
   2026-09-22 (auto-approve smoke, account 324177727513, us-east-1) vs
   what is designed/built-but-not-deployed (HITL resume, alarms → SNS →
   remediation, ensemble flag, KB on S3 Vectors, Textract/BDA, Cedar),
   provenance + as-of date.

## Figure inventory (F1–F14; lanes per FR-5, exceptions enumerated here)

| # | Part | Figure (in-SVG plain-English title) | Lanes | Icons | Steps ①… |
|---|---|---|---|---|---|
| F1 | I | "A claim goes in. Either the rules approve it, or a person does." | two-lane | doc, s3, person | yes |
| F2 | I | "An agent picks its own path (not here). Our code owns the path (chosen)." | **exception: single-lane comparative** — the contrast *is* the content; chosen side carries teal wash, rejected side neutral + crossed | bedrock, sfn | no |
| F3 | II | "Three things this system must be, pinned to the seven parts that make it." | **exception: single-lane map** (characteristics → components, no runtime flow) | none (component boxes) | no |
| F4 | III | **Hero.** "One claim's journey: S3 in, Step Functions drives, Bedrock reads and writes, S3 out." | two-lane | s3, sfn, lambda, bedrock, guardrail, doc | yes ①–⑦ |
| F5 | IV | "Four red gates. Every one of them leads to the same human." | two-lane | gate ×4, person | yes |
| F6 | IV | "The workflow waits — up to 7 days — until a person answers with the token." | two-lane | sfn, token, person, s3 | yes |
| F7 | V | "Two safety nets: one wraps the model, one wraps the result." | two-lane | guardrail, bedrock, lambda | yes |
| F8 | V | "Three keys. Each opens only the doors its job needs." | two-lane | iam ×3, kms, s3, bedrock, sfn | no (matrix-style) |
| F9 | VI | "Cite the policy or say so: no citation means flagged, never guessed." | two-lane | doc (policy), bedrock, gate | yes |
| F10 | VII | "Seven layers between a bad model day and a wrong decision." | two-lane | appconfig, cloudwatch, bedrock, gate | no (ladder) |
| F11 | VII | "When the breaker opens: degrade, keep going, and let a person decide." | two-lane | sfn, gate, person, cloudwatch | yes |
| F12 | VIII | "Proved offline first: 263 tests, one gate flag, then real AWS." | **exception: single-lane pyramid/timeline** (proof ladder, not runtime) | lambda, s3(smoke) | yes |
| F13 | VIII | "The deploy, stage by stage — and what only the real cloud revealed." | **exception: single-lane timeline** with findings F1–F11 pinned (C1) | s3, guardrail, appconfig, iam, lambda, sfn | yes (stages) |
| F14 | IX | "Ten decisions, placed where they live: model lane or envelope lane." | two-lane (the map's axes) | none (dots → cards) | no |

Status chips (C4) appear inside F4 (none — all live), F6 (HITL wait:
chip), F10 (alarms/remediation layer: chip; ensemble layer: chip), F11
(remediation hook: chip), F13 (pending stages), and the matching cards.
The authoritative live/not-live census is derived from
`build/DEPLOY-LEDGER.md` + `build/DEPLOY-WALKTHROUGH.md` §Remaining
work at authoring time and recorded as a list in the tasks file — the
verifier checks the page against that census.

Budget ~2–7 KB per figure; lane fills `var(--llm)`/`var(--det)` only
(AC-8); AWS category hex confined to the `<defs>` symbol block.

## Content pipeline (the real work)

All sources are committed in-repo (spec Scope table) — no research pass
needed. Authoring order: **chassis first** (tokens, legend, icon
library, icon strip) → **F4 the hero** (it fixes the visual grammar:
lane heights, icon plate size, step-number style — every later figure
inherits) → Parts in story order → cards → scorecard → footer →
verifier → browser passes. Before writing the page: load
`artifact-design` + `artifact-diagramming` (14 SVG figures; a private
Artifact publishes at converge per FR-12). Mid-build checkpoint after
Part IV: a figures-only scroll (flip-test rehearsal) before investing
in Parts V–IX — catches grammar drift while it is still cheap.

Each figure is drafted from its source section (e.g. F4 ← solution-
design §1 mermaid + §7 sequence; F5 ← §1a escalation table; F8 ← §5 +
ADR 0009; F10 ← §8 table; F13 ← walkthrough stages + findings register)
and its `figcaption` cites exactly that section (AC-11).

## Verification harness (AC → check)

`docs/architecture/explainers/verify_claim_processor_story.py`
(stdlib-only, checked in beside the deliverable, converge tool not CI
gate — precedent FR-15):
- **AC-2:** zero `http(s)://` in `src`/`href`/`url()`; relative in-repo
  links allowed.
- **AC-4:** every icon placement is `<use href="#sym-*">`; each symbol
  id defined exactly once in the `<defs>` block; every `<use>` has a
  sibling/nearby visible `<text>` label (proximity check within the same
  group); zero duplicated icon path geometry outside `<defs>`.
- **AC-5 (value-keyed + census):** every occurrence of the flagged
  tunables (grounding ~0.70, $10k default) sits in an `.unverified`
  element; every census-listed not-live element name co-occurs with a
  `.status` chip in each figure/card where it appears; footer status
  line present and dated.
- **AC-6:** 15-word shingle overlap between each source `.md` and the
  page text (exclusion list: ids F1–F11, ARN patterns, field names,
  commands, thresholds).
- **AC-7:** every `<figure>` has a `figcaption` containing a source
  citation, and its `<svg>` contains a title-class `<text>` line; flow
  figures (per the inventory's Steps column, encoded as
  `data-steps="yes"`) contain circled-number glyphs.
- **AC-8:** no lane hex in SVG fills/strokes outside the `<defs>`
  block; single-lane exceptions whitelisted: F2, F3, F12, F13.
- **AC-10:** figures carry `data-fig="F1…F14"` in Part order; nine
  `.part` sections each end with an `.envelope-beat`.
- **AC-11:** every cited path in figcaptions exists on disk (resolved
  against repo root).
- **AC-12:** size ≤ 350 KB (C5); every token defined in all three theme
  blocks; body background is a token.
- **AC-9 (static half):** ten `#d-*` cards each containing a `<table>`,
  a `.default-line`, and an ADR id string.
- **AC-14 (static half):** shell bytes (doctype, `lang`, charset).

Browser checks (in-app pane, served over HTTP — `file://` masked the
charset failure last time): AC-1 (no required JS), AC-3 (375 px +
300 px `scrollWidth` probe), AC-12 (dark mode via `resize_window`
colorScheme; icon strip legibility both themes), AC-14
(`characterSet`/`compatMode`). Human at converge: AC-15 (figures-only
flip test), AC-16 (hybrid-rule read), AC-9/13 targeted reads.

Baseline before implementation: `python3
tooling/skill-sync/skill_sync.py check` green from repo root;
`test_gate = <none>`.

## File-level touchpoints

| Path | Action |
|---|---|
| `docs/architecture/explainers/insurance-claim-processor-story.html` | **create** (the deliverable) |
| `docs/architecture/explainers/verify_claim_processor_story.py` | **create** (the verifier) |
| `docs/architecture/log.md` | append one newest-first entry (FR-12) |
| `docs/sdd/plans/claim-processor-story.tasks.md` | create at Stage 3 |
| claude.ai Artifact (private) | publish at converge (FR-12); repo file canonical |
| everything else | untouched — nothing under `insurance-claim-processor/`, no skill surfaces, no `tooling/`, no `apps/` |

## Risks

- **Flip-test failure discovered late** — mitigated by hero-first
  authoring + the Part-IV figures-only checkpoint; the C3 proxies catch
  structural drift continuously.
- **Icon ambiguity** (simplified glyphs misread): every placement
  labeled (AC-4); the icon key strip teaches the vocabulary before any
  figure uses it.
- **Size creep** (14 figures + library): symbol reuse is the main
  brake; 350 KB cap verifier-enforced; target 200–250 KB.
- **Status-census drift** — the deploy continues in a parallel thread;
  the page is dated as-of 2026-09-23 and the census is frozen in the
  tasks file at authoring time; future deploys re-run the verifier
  after editing the census + chips.
- **Hybrid-rule erosion** (prose creeping into figure-retelling):
  AC-16 targeted read at converge; each Part's planned beats are
  enumerated in the spec structure table — anything beyond them needs a
  reason at review.
- **Verbatim leakage / citation rot:** shingle check (AC-6) + on-disk
  path check (AC-11).
- **Category-hex contrast in dark mode:** icons sit on `var(--paper)`
  plates; the icon-strip browser pass in both themes is the check.
