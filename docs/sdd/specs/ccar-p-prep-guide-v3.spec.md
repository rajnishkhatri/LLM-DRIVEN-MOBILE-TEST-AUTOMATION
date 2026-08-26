# Spec: CCAR-P Prep Guide — v3 review-fix pass (ccar-p-prep-guide-v3)

**Status:** **DRAFT (2026-08-26)** — awaiting owner SPEC-OK gate.
**Predecessor:** [`ccar-p-prep-guide.spec.md`](ccar-p-prep-guide.spec.md)
(SPEC-OK 2026-08-25) — built `docs/ccar-p-prep-guide.html` (v1) →
`docs/ccar-p-prep-guide-v2.html` (v2). **This spec is a revision delta on
v2, not a re-spec.** Every v1/v2 acceptance criterion (AC-1…AC-12) is
inherited unchanged and must not regress (see AC-V3-11).
**Direction:** confirmed in-session 2026-08-26 — fix an external review of
v2 in three tiers (integrity → pedagogy → style), emit a new
`docs/ccar-p-prep-guide-v3.html`, leave v2 on disk, repoint the catalog to
v3 as current.
**Change class:** documentation deliverable (one HTML file + catalog/log
pointer lines); no code paths, no new dependency, no ⚠️ Ask-first trigger →
decision-log entry only, no ADR. `check_gate` (skill-sync) untouched by
construction — no skill surfaces written.

## Clarify decisions

| ID | Question | Decision |
|----|----------|----------|
| V1 | Are the exam-facts figures (63 items / 120 min / 720 on 100–1000 / domain weights) real-and-citable, or illustrative? | **Illustrative — label unverified.** They trace to a private practice-bank capture, not a citable official page; treat them the same as every other invented figure and bring them inside the disclaimer's scope. (Owner-selected 2026-08-26.) |
| V2 | Monotonic answer key — add new items, or rewrite existing? | **Full fix: rewrite.** Convert 2–3 existing graded items so the tuning/pragmatic answer is genuinely correct, **and** audit all 30 gauntlet items for the length/completeness giveaway. (Owner-selected 2026-08-26.) |
| V3 | Style pass depth? | **Full pass.** ~40–45% cut of antithesis + em-dashes across all seven rooms; thin the atmospheric tics; excise the strained metaphors. Substance and (except the V2 items) the answer key unchanged. (Owner-selected 2026-08-26.) |
| V4 | v2 disposition once v3 ships? | **Locked default (reversible):** v3 is a new file; v2 is retained on disk (review provenance) but the `cases/claude-certification/log.md` and `docs/architecture/log.md` pointers move to v3 as current, with a one-line "supersedes v2 — see v3 review-fix pass" note. |

**Open questions:** none.

## Problem

An external backpressure/anti-slop review of
[`docs/ccar-p-prep-guide-v2.html`](../../ccar-p-prep-guide-v2.html) surfaced
six defects. Reproduced against v2 at spec time (all counts confirmed):

1. **Monotonic answer key (highest-value pedagogical defect).** Across the 30
   gauntlet items + 14 checkpoints + decision-table rows, the correct answer
   is *always* the enforcement-layer / deterministic-gate / upstream-
   minimization / ownership-mechanism choice; the "tune the parameter / tighten
   the prompt / add a reviewer" option is **never once correct**. The guide
   warns against pattern-matching while its own answer distribution *trains*
   the reflex "when in doubt, pick the mechanism answer" — self-undermining.
2. **Length/completeness giveaway.** Measured: **26 of 30** gauntlet items make
   the correct option the single **longest** option; **7 of 30** phrase the
   correct option as "do X **and** make it standing practice." A test-wise
   reader picks by length/comprehensiveness without diagnosing.
3. **Flattened engineering tradeoffs presented as law.** (a) *Fail-closed as
   absolute* — stated as the always-right answer; fail-open is correct where
   blocking legitimate traffic is the greater harm (critical-alert / medical
   paths). (b) *"Stale checks riskier than no checks at all"* — a rhetorical
   overreach asserted, not argued.
4. **Disclaimer scope gap.** The honesty clause disclaims only "scenarios,
   organizations, and figures **in the teaching text and gauntlets**" — which
   silently **excludes** the exam-facts table, the one place invented precision
   does real harm (a candidate anchoring on a fake passing score).
5. **Unfalsifiable self-authority.** "harder than the real exam" and the
   recurring "the exam's favorite / the exam loves" (9 instances) assert
   privileged knowledge of an exam the guide also says it cannot verify.
6. **Uniform slop rhythm.** Measured tics: em-dashes **797**, "X, not Y"
   antithesis **158**, silent/quiet family **44**, "load-bearing" **14**,
   "the exam loves/favorite" **9**, "most expensive [X]" **6**. Not empty
   prose — *relentlessly the same move*; the emphasis machinery self-cancels.
   Plus strained metaphors ("curating a corpse," "gates dress for meetings,"
   "governance demoted … to hope").
7. **Minor overstatement.** "a *different* model judging than the one being
   judged" stated as a hard rule; same-family self-eval is not categorically
   invalid.

## Scope — surfaces touched

| Surface | Role |
|---|---|
| `docs/ccar-p-prep-guide-v2.html` | **source** — copied to v3, then edited. Read-only baseline retained. |
| `docs/ccar-p-prep-guide-v3.html` | **deliverable** — the fixed guide. |
| `cases/claude-certification/log.md`, `docs/architecture/log.md` | pointer lines repoint to v3 (FR-V3-7). |
| Review findings (this session's `/sdd-spec` argument) | the defect list driving FR-V3-1…6. |

**Not touched:** the seven-domain spine, semantic color key, diagram set,
domain weights, quiz engine JS, and every answer-key entry **except** the 2–3
items deliberately converted under FR-V3-2. v2 is not deleted.

## Functional requirements

- **FR-V3-1 Answer-key de-monotonization.** Convert **2–3** existing graded
  items (gauntlet and/or checkpoint) so the correct answer is a
  tuning/pragmatic remedy (tune a parameter, tighten a prompt, adjust a
  threshold, add a targeted reviewer), and the architectural/mechanism/upstream
  option is demoted to a distractor or adversarial option whose rationale
  explains why the heavier move is the **wrong diagnosis / over-engineering
  here**. Items enumerated in the plan; each converted correct option carries a
  machine-checkable marker (`data-remedy="tuning"`). Distractor/adversarial
  role counts, the per-domain tag, the single-correct/multi-select shape, and
  the 15-items-per-gauntlet invariant are preserved for every converted item.
- **FR-V3-2 Giveaway audit (all 30 gauntlet items).** Even option lengths so
  the correct option is **not the single longest** — primarily by trimming
  verbose correct options, secondarily by tightening over-long distractors —
  and reword correct options that win by comprehensiveness ("… **and** make it
  standing practice") so completeness is not the discriminator. Every option
  retains its rationale (AC-9 preserved).
- **FR-V3-3 Tradeoff honesty.** In the fail-closed passage, add a clause: fail-
  **open** is correct where blocking legitimate traffic is the greater harm
  (name a critical-alert / medical-path example); fail-closed stays the
  **default**, not the law. In the stale-suite passage, replace "riskier than
  no checks at all" with the defensible "manufactures false confidence" (a
  stale green measures the previous system wearing the current one's name); no
  "riskier than nothing" claim survives.
- **FR-V3-4 Disclaimer scope + facts label.** Extend the footer honesty clause
  so its illustrative-unverified scope **explicitly includes the exam-facts
  figures** (item count, time, passing score, domain weights). Add an inline
  "illustrative — verify current policy on the official page" label **on the
  exam-facts panel itself**, not only in the far-away footer.
- **FR-V3-5 Calibrate self-authority.** Remove or recast the unverifiable
  superiority claims: no assertion that the guide is "harder than the real
  exam" as fact; the anthropomorphized "the exam loves / the exam's favorite
  trap" recast to calibrated language (e.g. "a classic trap," "commonly
  mis-answered") — target ≤2 residual instances. Soften "a *different* model
  judging" from a hard rule to a strong best practice that acknowledges
  same-family self-eval is weaker, not invalid.
- **FR-V3-6 Style / anti-slop pass (all seven rooms).** Break the uniform
  `setup — em-dash aside — antithetical punchline` cadence into plain
  declaratives where it repeats, per the measurable targets in AC-V3-9. Cut the
  three flagged strained metaphors (and comparable ones) to sparse. Meaning,
  correct answers (except FR-V3-1 items), diagrams, and weights unchanged.
- **FR-V3-7 Registration.** Repoint the `cases/claude-certification/log.md` and
  `docs/architecture/log.md` entries to v3 as current with a one-line
  "supersedes v2" note; keep the relative M1-atlas link; do not edit v2.

## Acceptance criteria (EARS — failure paths first)

**Integrity (tier A)**
- **AC-V3-1** IF the footer honesty clause is read, THEN its illustrative-and-
  unverified scope explicitly names the exam-facts figures (item count / time /
  passing score / domain weights), AND the exam-facts panel itself carries an
  inline "illustrative — verify on the official page" label. *(Fails if the
  clause still reads "in the teaching text and gauntlets" only.)*
- **AC-V3-2** IF the guardrail fail-closed passage is read, THEN the same
  passage states fail-open is correct where blocking legitimate traffic is the
  greater harm, with fail-closed framed as the default not an absolute.
- **AC-V3-3** IF the stale-evaluation passage is read, THEN it contains no claim
  that stale checks are "riskier than no checks"; the risk is expressed as
  manufactured/false confidence.
- **AC-V3-4** Ubiquitous: the "different model judging" guidance reads as a
  strong best practice (weaker-not-invalid), not a categorical must/never; and
  anthropomorphized "the exam loves/favorite" instances number ≤2 (from 9), with
  no factual "harder than the real exam" superiority claim.

**Pedagogy (tier B)**
- **AC-V3-5** WHEN the full graded set (30 gauntlet + 14 checkpoints) is
  considered, THEN **≥2 (target 3)** items have a correct answer that is a
  tuning/pragmatic remedy, each marked `data-remedy="tuning"`, with the
  mechanism/upstream option present as a distractor or adversarial whose
  rationale names why the heavier move is wrong here. *(Fails if zero
  tuning-correct items exist — the v2 state.)*
- **AC-V3-6** IF any of the 30 gauntlet items is measured on option text
  (rationale excluded), THEN its correct option is not the single longest;
  across all 30, correct-is-longest count ≤ 6 (from 26), and none of the
  FR-V3-1 converted items is the longest.
- **AC-V3-7** IF a correct option is measured, THEN the "do X **and** make it
  standing/always/permanent practice" completeness pattern appears in ≤2
  correct options (from 7).
- **AC-V3-8** Ubiquitous (no-regression on the engine): every option still
  shows a rationale and each adversarial option's rationale names its trap
  (AC-9); each gauntlet still has exactly 15 items with a consistent per-domain
  tally and 5–7 multi-select items total (AC-10); the seven domain weights
  still sum to 100 (AC-6).

**Style (tier C)**
- **AC-V3-9** Ubiquitous (measurable, verified by grep on v3):
  em-dashes ≤ **438** (≥45% cut from 797); "X, not Y"/antithesis ≤ **95**
  (≥40% from 158); silent/quiet family ≤ **26** (≥40% from 44);
  "load-bearing" ≤ **5** (from 14); "most expensive [X]" ≤ **2** (from 6);
  "the exam loves/favorite" ≤ **2** (from 9). The three named strained
  metaphors are gone.
- **AC-V3-10** Ubiquitous (no-regression on substance): the answer-key role
  diff vs v2 is limited to the FR-V3-1 items; the semantic color key, diagram
  set, and domain weights are byte-stable in meaning (no diagram/weight edits);
  the whitelabel >15-consecutive-word rule (AC-4) still holds.

**Chassis (inherited)**
- **AC-V3-11** Ubiquitous: v3 satisfies every v1/v2 criterion AC-1…AC-12 —
  JS-off readability of all items + answers + rationales, zero external fetches
  / `file://` parity, no horizontal scroll ≤375px, ≥2 inline-SVG fig-cards per
  domain part with all meaning-colors in the sticky key, light/dark theme
  sanity, and total file size ≤ 1 MB.

## Verification method (how each AC is checked)

- Structural/count ACs (V3-1 scope string, V3-3 absent phrase, V3-4/9 tic
  counts, V3-5 `data-remedy` count, V3-6/7 option-length + pattern scan):
  the spec-time grep/Python probes, re-run against v3 — pass = the stated
  thresholds. The audit script lives in the tasks file.
- Prose ACs (V3-2 fail-open clause, V3-4 phrasing, V3-5 rationale-names-trap):
  targeted read of the named passage.
- Chassis ACs (V3-11): re-run v2's checks (no `http(s)://` in loaded refs,
  ≤375px reflow, theme tokens, ≤1 MB) against v3.

## Out of scope / deferred

Deleting or rewriting v2 · re-authoring the whole item bank · changing the
seven-domain spine, weights, diagrams, or quiz engine · adding score
persistence or a timed mock · Artifact publication (still repo-file-only per
predecessor C4) · any edit to `cases/…/*.md`, `tooling/`, `src/`, or skill
surfaces · sourcing the exam figures from an official page (decision V1:
they are labeled illustrative, not cited).
