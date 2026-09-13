# Tasks: AWS + Claude AI-Architect Explainer — "The Loop, Left Running"

**Spec:** `docs/sdd/specs/aws-ai-architect-story.spec.md` · **Plan:**
`docs/sdd/plans/aws-ai-architect-story.plan.md` · **Status:** **IMPLEMENTED
(2026-08-27)** — all tasks T0–T12 green in one `sdd-implement` session.
Deliverable at `docs/architecture/explainers/aws-ai-architect-story.html`
(111.7 KB); static verifier (`verify_story.py`, scratchpad) green: exit 0 on
AC-2/4/5/6/8/9-static/10/11-static/12; browser pass observed AC-1/3/7/13 in
both themes at 375 px + desktop; `check_gate` exit 0 after the
`docs/architecture/log.md` registration (AC-14); private Artifact published
per C4 (repo file canonical). Implementation notes: the sticky-legend badge
chips are a named AC-4 exception in the verifier (a definition is not a
claim); F2 is the enumerated single-lane exception and ships price-free —
P8 price figures live in prose/cards with inline `.unverified` markers
(5 markers ≥ 3 P8 classes, reconciled in the footer). Next: Stage-7 review
(`code-review`, fresh thread).
Prior gate record: TASKS-OK (2026-08-27) — owner approved; Stage-4 analyze
green (check_gate exit 0, grounding pass clean).
**REPLAN R1 (2026-08-28): status → IN PROGRESS.** Stage-7 review
(`docs/research/aws-ai-architect-story-review.md`) found 2 High · 5 Medium ·
3 Low, and the owner directed a scope change (temporal labeling grammar
removed in full; plain-English immersive narration added). Spec + plan
revised first (sections marked R1). The T0–T12 record above stands as
history; live work is **§Replan R1** below.
Markers: `[deps: …]` must-finish-first · `[par]` parallelizable with siblings.

**Checklist ("unit tests for English"):** every AC is measurable — AC-2/4/5/
6/8/10/12 and the static halves of AC-9/11 by the stdlib verifier; AC-7/13 by
targeted read; AC-1/3 (+ theme half of 7/12) by browser check; AC-14 by file
inspection. Vague words made concrete at spec/plan time: "adjacent" (AC-4) =
the `.delta-pair` construct; "fresh distillation" = the 15-word shingle scan
(AC-6); "covered" (AC-10) = `data-delta` anchors 1–14. No unmeasurable
criteria remain.

- **T0 — Design-skill load + style anchor.** Load `artifact-design` +
  `artifact-diagramming`; re-read the o7-v2 token block, sticky-legend, and
  footer Honesty-note patterns (`docs/architecture/explainers/
  o7-pipeline-story-v2.html`).
  Pass: both skills loaded in-session before any HTML is written.
- **T1 — Content map derivation.** [deps: T0] From the ten research dossiers
  (`<scratchpad>/tasks/sections/*.json`), the brainstorm §3 table, and the
  bundle audits, derive `<scratchpad>/story-content-map.json`: per-Part
  claim outlines (each claim: badge class, `data-delta` assignment per the
  spec structure table, plain-text citation), envelope-beat text ×7, the
  nine cards' trade-off-table data + default-lines, scorecard rows, the P8
  unverified-figure list.
  Pass: python sanity — delta rows 1–14 all assigned to their spec-table
  locations; 9 cards; ≥6 scorecard rows; P8 list non-empty; every
  `.was` claim has a paired `.now` replacement in the map.
- **T2 — Chassis.** [deps: T1] Skeleton at
  `docs/architecture/explainers/aws-ai-architect-story.html`: head + tokens
  (three-block theme wiring, explicit body background), masthead + FR-7 seam
  statement, sticky two-grammar legend, empty `.part` shells I–VIII,
  scorecard shell, footer shells (About / Honesty note / provenance /
  as-of / P8 list).
  Pass: opens from `file://`; both themes sane; zero external resource URLs;
  no body h-scroll at 375 px; the legend is the only sticky element.
- **T3 — Part II "The loop" (style anchor).** [deps: T2] The richest badge
  mix: still-true double badge on the `stop_reason` contract, the prefill
  `.delta-pair` (course-era extraction → tool-schema/structured
  replacement), figure F3, closing envelope beat. **This Part is the named
  voice/format anchor for T4–T7.**
  Pass: shingle-clean vs both bundles; `.delta-pair` well-formed; F3 shows
  both labeled lanes with token fills; `data-delta` 1 and 3 present.
- **T4 — Parts I + III.** [deps: T3] [par] Part I (one call: model ladder,
  endpoints, adaptive thinking/effort; F1 + F2-exception; rows 1, 2, 4, 5;
  P8 price figures carry `.unverified`) and Part III (MCP control split
  still-true + 2026-07-28 stateless `.delta-pair`; F4; row 8).
  Pass: anchor standard (voice, badges, beat); rows present; `.unverified`
  markers on every P8 figure used.
- **T5 — Parts IV + V.** [deps: T3] [par] Part IV (agent = loop + state,
  memory, Strands; F5; rows 7-lite, 11-lite) and Part V (topologies, A2A,
  protocol stack, start-simple still-true; F6; row 14).
  Pass: anchor standard; rows present.
- **T6 — Parts VI + VII.** [deps: T3] [par] Part VI (AgentCore platform map
  F7 with Bedrock Agents Classic as the dashed-violet retired lane; rows 7,
  10-lite, 12-lite) and Part VII (the eval doctrine: two-tier funnel F8,
  pass@k vs pass^k, effort-selection tie-back; rows 2-lite, 11, 12-lite).
  Pass: anchor standard; Classic renders dashed-violet inside a
  `.delta-pair` naming AgentCore as the `.now`; rows present.
- **T7 — Part VIII decision map.** [deps: T3] [par] Nine `#d-*` cards
  (endpoint, routing, model, context, orchestration, governance, evals,
  deploy, retention): one-sentence decision, trade-off `<table>` in an
  `overflow-x` wrapper, `.default-line`, cross-anchors to/from motivating
  Parts; figure F9; rows 3, 6, 9, 10, 12, 13.
  Pass: all nine present with table + default-line; anchors resolve both
  directions; rows present.
- **T8 — Scorecard + footer completion.** [deps: T4, T5, T6, T7] Scorecard
  rows (RAG/KB, caching, guardrails, observability/FinOps, data retention,
  protocol stack) wired to card anchors + delta rows + badges; footer About
  (two-book provenance, bundle-log pointers), Honesty note (badge semantics,
  FR-9 statement), provenance block + as-of line; footer P8 list reconciled
  against in-page `.unverified` markers.
  Pass: every scorecard anchor resolves; footer P8 list = in-page marker
  set.
- **T9 — Verifier + full static pass.** [deps: T8] Write + run
  `<scratchpad>/verify_story.py` (plan §Verification): external-URL scan,
  `.delta-pair` pairing, `.unverified` counts, shingle scan vs all bundle
  bodies, SVG token-fill audit (F2 whitelisted), `data-delta` 1–14, size ≤
  250 KB + three-block token audit, structure counts (seven spine `.part`
  sections in order each ending with an `.envelope-beat`, plus the
  decision-map section with its nine `#d-*` cards — the beat requirement is
  spine-only, per AC-11).
  Pass: all checks green, exit 0.
- **T10 — Browser verification.** [deps: T9] Browser pane on the `file://`
  page: both themes (`resize_window` colorScheme), 375 px + desktop, legend/
  seam/footer targeted reads, screenshot evidence.
  Pass: AC-1 (content complete with zero required JS; any `<details>`
  native), AC-3, AC-7, AC-13 observed.
- **T11 — Registration + gate baseline.** [deps: T10] Append the
  newest-first entry to `docs/architecture/log.md` (file, design language,
  SDD provenance); run `python3 tooling/skill-sync/skill_sync.py check` from
  the repo root.
  Pass: gate exit 0; entry present (AC-14).
- **T12 — Artifact publish (C4).** [deps: T11] Publish the finished page as
  a private claude.ai Artifact (stable favicon; repo file canonical); hand
  the user the repo path + private link.
  Pass: artifact renders in both viewer themes; link delivered.

**AC → task coverage (T0–T12 era):** AC-1 T2/T10 · AC-2 T2/T9 · AC-3
T2/T7/T10 · AC-4 T3–T7/T9 · AC-5 T4/T8/T9 · AC-6 T3/T9 · AC-7 T2/T10 · AC-8
T3–T7/T9 · AC-9 T7/T9 · AC-10 T1/T9 · AC-11 T3–T6/T9 · AC-12 T2/T9 · AC-13
T2/T10 · AC-14 T11. No zero-coverage criteria; no task without a criterion.

---

## Replan R1 (2026-08-28) — review fixes + de-labeling + voice pass

**Status: R1 IMPLEMENTED (2026-08-28)** — R1-T1…T8 green in one
`sdd-implement` session. Evidence: red-first —
`docs/architecture/explainers/verify_aws_ai_story.py` written before the
fixes failed 16/30 against the pre-R1 page (charset, residue, nowrap,
scroll-margin, thead, F2 wash, part-5 link, scorecard 1.25× unmarked), then
30/30 / exit 0 after them; `check_gate` exit 0; browser pass over
`python3 -m http.server` (not `file://`): `characterSet: "UTF-8"`,
`compatMode: "CSS1Compat"`, `scrollWidth` 300@300px and 375@375px (was 406
at 300px), hash-jump lands below the sticky key, both themes screenshotted;
0 badge/delta-pair elements and 8 `.unverified` markers in the live DOM;
10/10 tables have `<thead>`; page 114.4 → 104.8 KB. T2+T3 were applied as
one editing sweep per section (T3's dependency on T2 respected; both pass
criteria checked separately). Artifact republished to the existing URL
(C4; repo file canonical). Next: Stage-7 re-review (`code-review`, fresh
thread).

**Inputs:** Stage-7 review `docs/research/aws-ai-architect-story-review.md`
(H1–H2, M1–M5, L1–L3); owner scope decisions (2026-08-28): full removal of
the temporal grammar; `.unverified` markers stay; plain-English immersive
long-form narration. Spec revisions: FR-5/6 rewritten, FR-13/14/15 and
AC-15/16 added, AC-4 inverted, AC-5 tightened, AC-7/11 trimmed.

**Finding disposition** (every review finding routed, none dropped
silently):

| Finding | Disposition |
|---|---|
| H1 charset/doctype | **Fix** → R1-T1 (now FR-14/AC-15) |
| H2 nowrap chip overflow | **Fix** → R1-T5 (chips wrap; AC-3) |
| M1 scorecard 2× unmarked | **Transformed**: the verified-2026 badge is gone; the AC-5 half remains — every P8 occurrence marked → R1-T4 |
| M2 scorecard count/misroutes | **Fix** → R1-T4 (drop protocol-stack row; reroute observability/FinOps) |
| M3 `data-delta="3"` mis-tag | **Fix** → R1-T4 (anchors kept as invisible bookkeeping) |
| M4 Part V unbound | **Fix** → R1-T4 (Part V ↔ orchestration-card backref; no invented protocol-stack card) |
| M5 verifier not in repo | **Fix** → R1-T6 (FR-15; rewritten for the R1 grammar) |
| L1 scroll-margin / focus-visible | **Fix** → R1-T5 |
| L2 false F2 caption | **Fix** → R1-T4 |
| L3 D1 header cell / F2 Sonnet wash | **Fix** → R1-T5 |

**Dissolved by scope change** (no task): the old AC-4 pairing rule, badge
legend semantics, still-true double badges, the F7 retired lane — all
removed wholesale by R1-T2 rather than repaired.

### R1 task list

- **R1-T1 — Document shell.** Prepend `<!DOCTYPE html>`, `<html lang="en">`,
  `<head>` + `<meta charset="utf-8">` (keep the existing viewport meta);
  close the shell correctly.
  Pass: served via `python3 -m http.server`, browser reports
  `characterSet: "UTF-8"`, `compatMode: "CSS1Compat"`; masthead/figures/
  footer free of mojibake (AC-15).
- **R1-T2 — De-labeling strip.** [deps: R1-T1] Remove the claim-badge
  grammar page-wide: legend badge block (legend → lanes + `.unverified` chip
  only), all `.b-*` chips, every `.delta-pair` (delete `.was` halves; merge
  `.now` content into surrounding prose with its citation), the F7
  dashed-violet Classic lane (→ one plain-prose sentence in Part VI), the
  scorecard badge column, footer badge semantics; purge the now-dead CSS
  rules.
  Pass: grep zero for `b-verified|b-course|b-superseded|b-human|delta-pair|
  class="was"|class="now"` and for reader-visible "verified 2026" /
  "course-era" / "superseded" (AC-4-R1); every merged claim kept its
  citation; page still covers `data-delta` 1–14.
- **R1-T3 — Voice pass (FR-13).** [deps: R1-T2] Rewrite Parts I–VIII prose
  as plain-English immersive long-form narration: concrete opening hook per
  Part, terms introduced in ordinary words at first use, the running
  "loop, left running" thread, envelope beats as the recurring cadence.
  Numbers, product names, API fields survive verbatim; nothing invented.
  Pass: per-Part targeted read against FR-13; AC-6 shingle check still
  clean; `.unverified` markers preserved through the rewrite (AC-16 final
  judgment is the owner's at converge).
- **R1-T4 — Content corrections.** [deps: R1-T2] [par with R1-T3 by
  section] Scorecard: drop the protocol-stack row (full-depth Part V
  exists), reroute observability/FinOps off the evals card, fix the
  five-vs-six count line; mark the cache-write 2× (and any other P8 repeat)
  `.unverified` at every occurrence (M1/AC-5); move `data-delta="3"` off the
  prefill passage onto the caching treatment (M3/AC-10); add the Part V ↔
  `#d-orchestration` backref pair (M4/AC-9); correct the F2 figcaption so it
  matches where prices actually appear (L2).
  Pass: scorecard rows = topics counted, all anchors resolve both ways;
  verifier AC-5/AC-9/AC-10 checks green.
- **R1-T5 — Responsive + a11y fixes.** [deps: R1-T2] [par] Let `.unverified`
  chips wrap (drop `nowrap`; audit `code` spans) (H2/AC-3);
  `scroll-margin-top` on `#d-*`/`h2` clearing the sticky legend +
  `:focus-visible` rule (L1/FR-12); D1 table gets a `<thead>` with no empty
  header cell (L3); F2 Sonnet tile loses the envelope wash — neutral panel
  fill (L3/FR-3-exception discipline).
  Pass: 300 px probe `document.documentElement.scrollWidth` ≤ viewport;
  hash-jump lands clear of the legend; D1 headers announced; F2 uses no
  lane-semantic fill.
- **R1-T6 — Verifier rewrite + check-in (FR-15).** [deps: R1-T2, R1-T4,
  R1-T5] Write `docs/architecture/explainers/verify_aws_ai_story.py`
  (stdlib-only) per the plan's R1 harness: AC-2 external-URL scan · AC-4-R1
  residue grep · AC-5 value-keyed per-occurrence marker check · AC-6
  shingle scan · AC-8 SVG token-fill audit (F2 whitelisted) · AC-10
  `data-delta` 1–14 · AC-12 size + three-block tokens · AC-15 static shell
  check · AC-3 static nowrap assist · AC-9/11 static structure counts.
  Pass: committed next to the HTML; exit 0 on the fixed page; deliberately
  fails when run against the pre-R1 page (proves the ratchet bites).
- **R1-T7 — Browser re-verification.** [deps: R1-T6] HTTP-served pass (not
  `file://`): both themes, 375 px + 300 px + desktop, charset/compat probe,
  hash-jump, legend/seam/footer targeted reads, screenshot evidence.
  Pass: AC-1/3/7/13/15 observed; no regressions vs the review's §2 table.
- **R1-T8 — Registration + republish.** [deps: R1-T7] Append the R1 line to
  the `docs/architecture/log.md` entry (replan provenance: review + scope
  change); run `check_gate`; republish the private Artifact **to the same
  URL** (C4; repo file canonical).
  Pass: gate exit 0; log newest-first intact (AC-14); artifact link
  unchanged, renders in both viewer themes.

**AC → R1 task coverage:** AC-3 T5/T7 · AC-4-R1 T2/T6 · AC-5 T4/T6 · AC-6
T3/T6 · AC-7 T2/T7 · AC-9 T4/T6 · AC-10 T4/T6 · AC-11 T6 (unchanged
structure) · AC-12 T6 · AC-14 T8 · AC-15 T1/T6/T7 · AC-16 T3 (+ owner read
at converge). AC-1/2/8/13 unaffected by R1 edits, re-confirmed by T6/T7.
Gate: owner approval of this replan → route to `sdd-implement` (Stage 6) on
this list.
