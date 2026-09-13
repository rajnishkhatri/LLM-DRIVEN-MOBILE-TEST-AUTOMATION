# Plan: AWS + Claude AI-Architect Explainer — "The Loop, Left Running"

**Spec:** `docs/sdd/specs/aws-ai-architect-story.spec.md` (SPEC-OK 2026-08-27,
C1–C4 locked). **Status:** **PLAN-OK (2026-08-27)** — owner approved at the
gate; tasks decomposed → `aws-ai-architect-story.tasks.md`.
**REPLAN R1 (2026-08-28):** spec revised at Stage 5 (Stage-7 review intake +
owner scope change) — the claim-badge/delta-pair temporal grammar is removed
in full; plain-English immersive narration added (FR-13); document shell
(FR-14) and checked-in verifier (FR-15) added. Sections below marked **(R1)**
are revised; superseded plan text is edited in place. New tasks in the tasks
file §Replan R1.
**Change class:** documentation deliverable; no new dependency; no ⚠️ Ask-first
trigger → no ADR; decision-log entry at registration (FR-11).

## A1 — simplest machinery statement

One hand-authored HTML file with **zero required JavaScript**: the page is a
linear narrative — anchors, `<details>` where anything folds, pure-CSS badges
and lanes. Rejected as over-machinery: any framework or chart library (new
dep → ADR), a build step (repo has none), a JS figure engine (the atlas
needed one for a 26-node interactive map; this page's ~10 figures are static
two-lane SVGs, cheaper hand-authored), and a data-driven card generator for
nine cards (a template + hand-authoring is less total machinery).

**G1 note (R1-revised):** the claim-badge + supersession-block convention
originally introduced here was **removed at Replan R1** — readers have no
context for the course-vs-2026 history it encoded, so the page now states
current practice only (spec FR-5). What survives as machine-checkable
convention: the invisible `data-delta="1…14"` coverage anchors (AC-10) and
the `.unverified` figure chip (AC-5). AC-4 inverts from "every superseded
claim is paired" to "zero residue of the removed grammar".

## Architecture of the deliverable

`docs/architecture/explainers/aws-ai-architect-story.html` (C2), top to
bottom:

1. **Document shell + head + CSS tokens (R1).** `<!DOCTYPE html>`,
   `<html lang="en">`, `<head>` with `<meta charset="utf-8">` + viewport
   (FR-14/AC-15). The o7-v2 palette verbatim (`--det` teal, `--llm`
   amber, `--human` slate, `--proposed` violet, plus ground/panel/ink/rule),
   system font stack, three-block theme pattern (FR-10): light on bare
   `:root`; dark under `@media (prefers-color-scheme: dark)
   { :root:not([data-theme="light"]) }` AND `:root[data-theme="dark"]` —
   valid standalone and correct when republished as an Artifact (C4).
   Explicit `body { background: var(--ground) }`. Zero external requests
   (C3/AC-2). Hash targets get `scroll-margin-top` clearing the sticky
   legend; a `:focus-visible` rule ships (FR-12).
2. **Masthead.** Title ("The Loop, Left Running — an architect's story of
   Claude on AWS, mid-2026"), one-paragraph orientation, and the FR-7 seam
   statement (≤3 sentences: the M1 atlas is the certification study aid;
   this page narrates the two case bundles through the mid-2026 delta).
3. **Sticky lane legend (R1)** (`top:0`, the page's only sticky element),
   one compact block (AC-7): amber = the model's probabilistic plane; teal =
   the deterministic envelope (rendered as labeled low-opacity `var(--token)`
   band fills in every architecture SVG); plus the `.unverified` chip
   ("unverified — check the current page"). No claim badges — the badge key
   is removed with the badge grammar (FR-5).
4. **No supersession construct (R1).** The `.delta-pair`/`.was`/`.now`
   markup is removed; superseded course-era claims are simply not retold.
   The former `.now` content merges into the surrounding narrative prose
   (with its plain-text citation). AC-4's grep check inverts: zero matches
   for the removed classes and label strings.
5. **Delta-row anchors:** every place a brainstorm-§3 row lands carries
   `data-delta="<n>"` (n = 1–14; a row may appear at several depths — the
   full treatment carries the attribute). AC-10's check: all 14 values
   present at least once.
6. **Parts I–VII (R1)** — `<section class="part" id="part-1…7">` per the
   spec structure table, each: plain-English narrative prose (FR-13 voice: a
   concrete opening hook, terms introduced at first use, the running
   "loop, left running" thread), 1–2 figures, and a closing
   `<aside class="envelope-beat">` (teal-ruled: what the deterministic plane
   must own before the next escalation). No badges anywhere in prose.
7. **Part VIII — the decision map.** Nine
   `<article class="decision-card" id="d-endpoint|d-routing|d-model|
   d-context|d-orchestration|d-governance|d-evals|d-deploy|d-retention">`,
   each: the decision in one sentence, a trade-off `<table>` (inside an
   `overflow-x` wrapper, AC-3), a `.default-line` ("default … deviate
   when …"), and plain-anchor cross-links to/from its motivating Part
   (AC-9).
8. **Scorecard table (R1).** One row per compressed topic (RAG/KB, caching,
   guardrails, observability/FinOps, data retention — protocol stack is
   dropped from this table: it has full-depth Part V, and its former routing
   to the orchestration card was wrong, per review M2/M4): what it is in one
   line × which lane owns it × its decision card anchor × its delta row(s).
   No currency-badge column. Observability/FinOps routes to its governing
   card (deploy/governance), not evals. P8 figures repeated here carry the
   `.unverified` chip per occurrence (AC-5).
9. **Footer (R1).** About (two-book provenance of `cases/aws-ai/`,
   plain-text pointers to both bundle `log.md`s), Honesty note (what the
   `.unverified` chip means, the FR-9 independent-synthesis statement,
   AWS/Anthropic docs as authority — no badge semantics), provenance block
   (research pass 2026-08-27; primary sources as plain-text names per C3),
   the as-of line, and the P8 unverified-figures list (each such figure
   in-page also carries the inline `.unverified` marker at every occurrence,
   FR-8/AC-5).

## Figure inventory (D5 two-lane convention; exceptions enumerated per FR-3)

| # | Part | Figure | Lanes |
|---|---|---|---|
| F1 | I | Anatomy of one call: request → envelope (IAM, endpoint choice, quotas) → model → response | two-lane |
| F2 | I | Model ladder × endpoints (Haiku 4.5 → Sonnet 5 → Opus 5 → Fable 5; `bedrock-runtime` vs `bedrock-mantle`) | **exception: single-lane** (a comparative ladder visual, not an architecture); R1: no lane-semantic washes on model chips — neutral panel fills only, so the ladder can't be misread through the lane grammar |
| F3 | II | The tool loop: `stop_reason` contract; model proposes (amber) / envelope executes + validates (teal) | two-lane |
| F4 | III | MCP host–client–server + tools/resources/prompts control split; the stateless transport shown as the current wire contract (R1: no delta inset) | two-lane |
| F5 | IV | Agent = the loop left running: state, memory tiers, Strands frame | two-lane |
| F6 | V | Many loops: topologies + the protocol stack (MCP / A2A / AG-UI / x402) | two-lane |
| F7 | VI | AgentCore platform map (Runtime·Instances, Harness, Gateway, Identity, Memory, Policy, Evaluations, Observability) — R1: the dashed-violet Bedrock Agents Classic retired lane is removed; Classic survives only as the one-sentence plain-prose fact in Part VI | two-lane |
| F8 | VII | The two-tier eval funnel: build-time gates (Strands Evals, pass^k) → production sampling (AgentCore Evaluations) | two-lane |
| F9 | VIII | The nine decisions plotted on the two-lane map (each dot anchors to its card) | two-lane |

Budget ~2–6 KB each inline SVG, `var(--token)` fills only (AC-8).

## Content pipeline (the real work)

Prose is authored (not generated) from three layers per Part: the bundle
Concepts/chapters (cited by title, never line — spec Scope rule), the
brainstorm §3 delta table (the currency skeleton; each row's landing spot is
fixed by the spec structure table), and the ten research dossiers at
`<scratchpad>/tasks/sections/*.json` (working assets, not committed — they
carry the primary-source names the C3 text citations use). Authoring order:
tokens/legend/CSS chassis first, then Parts in story order (Part II written
second but styled as the template Part — it carries the richest badge mix),
then cards, scorecard, footer. The implementation loads `artifact-design` +
`artifact-diagramming` before writing the page (C4 publishes an Artifact;
also the right calibration for nine SVG figures).

## Verification harness (AC → check)

`docs/architecture/explainers/verify_aws_ai_story.py` (**R1: checked in next
to the deliverable per FR-15** — review M5 showed the scratchpad copy let
regressions through; stdlib-only, a converge tool, not a repo gate):
- **AC-2:** no `http(s)://` in `src`/`href`/`url()` anywhere (C3 is strict —
  no external navigation links either; source names are plain text).
- **AC-4 (R1, inverted):** zero matches for `.b-verified`/`.b-course`/
  `.b-superseded`/`.b-human`/`.delta-pair`/`.was`/`.now` classes and for the
  reader-visible strings "verified 2026", "course-era", "superseded".
- **AC-5 (R1, value-keyed):** every occurrence of each P8 figure value
  (prices, cache-write multipliers, KB rates) sits inside an element carrying
  `.unverified` — per occurrence, not a global count; footer as-of line
  present.
- **AC-15 (static half):** file begins `<!DOCTYPE html>`; `<html lang=` and
  `<meta charset="utf-8">` present in the head.
- **AC-3 (static assist):** no `white-space: nowrap` on `.unverified` or
  other prose chips.
- **AC-6:** 15-word shingle overlap between every source-bundle `.md` body
  and the page text (exclusion list: numbers, product names, API fields).
- **AC-8:** no hex colors inside `<svg>` fill/stroke attributes (tokens
  only); F2 whitelisted as the enumerated exception.
- **AC-10:** `data-delta` values cover 1–14.
- **AC-12:** file size ≤ 250 KB; every token defined in all three theme
  blocks; body background is a token.
- **AC-9/11 (static half):** nine `#d-*` cards each containing a `<table>`
  and a `.default-line`; seven `.part` sections in order each ending with an
  `.envelope-beat`.
Browser checks (Browser pane, **served over HTTP** — R1: `file://` masked the
charset failure): AC-1 (no-JS reasoning — the page ships no required JS;
verify `<details>` fallbacks), AC-3 (375 px and a 300 px
`document.documentElement.scrollWidth` probe, no body h-scroll), AC-7 (legend
both themes via `resize_window` colorScheme), AC-13 (masthead seam + footer
provenance read), AC-15 (`characterSet: "UTF-8"`, `compatMode:
"CSS1Compat"`, no mojibake). AC-16 (voice) is a targeted human read at
converge.

## File-level touchpoints

| Path | Action |
|---|---|
| `docs/architecture/explainers/aws-ai-architect-story.html` | **create** (the deliverable) |
| `docs/architecture/log.md` | append one newest-first decision-log entry (FR-11); R1 adds a replan line |
| `docs/architecture/explainers/verify_aws_ai_story.py` | **create + commit (R1, FR-15)** — the static verifier, next to the deliverable |
| section drafts | working assets, not committed |
| claude.ai Artifact (private) | publish at converge (C4); repo file canonical |
| everything else | untouched — no bundle edits (D6-lite already landed), no skill surfaces, no `tooling/`, no `src/`, no `apps/html-site/manifest.toml` |

## Risks

- **Size creep** (nine SVGs + nine cards + seven Parts): target ~155–160 KB
  against the 250 KB cap; verifier enforces; the C1 scope cut, not the cap,
  is the working constraint — compressed topics stay compressed.
- **Two-grammar confusion** — dissolved at R1: the claim-badge grammar is
  removed, so only the lane grammar remains. Residual risk is stale badge
  markup surviving the strip; the inverted AC-4 grep is the ratchet.
- **Voice flattening (R1):** rewriting for plain English can sand off the
  facts — every number, product name, and API field survives the rewrite
  verbatim (FR-13 grounds engagement in the sources; AC-6 shingle check
  still applies).
- **Verbatim leakage** (AC-6): authored from distillations + shingle check.
- **Citation rot into the untracked bundle** (P4): all bundle citations by
  Concept/chapter title only.
- **Unverified-figure drift** (P8): the `.unverified` marker + as-of footer
  are the honesty valve; no bare price ships as fact.
- **Figure effort doubling** (D5 known cost): capped at 9 figures; per-card
  mini-diagrams explicitly out — cards are tables.
