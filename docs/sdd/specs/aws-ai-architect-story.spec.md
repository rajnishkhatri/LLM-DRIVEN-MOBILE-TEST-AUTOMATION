# Spec: AWS + Claude AI-Architect Explainer — "The Loop, Left Running" (aws-ai-architect-story)

**Status:** **SPEC-OK (2026-08-27)** — owner approved at the gate after
answering C1–C4 in session (C1 upgraded to spine + evals Part; C2 cap
loosened to 250 KB; C3/C4 as recommended). Advance → plan.
**IMPLEMENTED (2026-08-27)** — see the tasks-file build record; deliverable
at `docs/architecture/explainers/aws-ai-architect-story.html`, registered in
`docs/architecture/log.md`, private Artifact published per C4.
**REPLAN R1 (2026-08-28) — status back to IN PROGRESS.** Stage-5 replan
triggered by (a) the Stage-7 review
(`docs/research/aws-ai-architect-story-review.md`: 2 High · 5 Medium ·
3 Low) and (b) an owner scope change: the **temporal labeling grammar is
removed in full** — no claim badges ("verified 2026" / "course-era" /
"superseded"), no was/now `.delta-pair` blocks, no badge legend or footer
badge semantics. Readers have no context for the course-vs-2026 history; the
page states **current best practice only**, in **plain-English immersive
long-form narration**. The `.unverified` figure markers and as-of provenance
**stay** (owner-confirmed). Sections revised below carry the **(R1)** marker;
regenerated task list in `aws-ai-architect-story.tasks.md` §Replan R1.
**R1 IMPLEMENTED (2026-08-28)** — see the tasks-file §Replan R1 build
record; verifier `docs/architecture/explainers/verify_aws_ai_story.py`
green (30/30, exit 0); awaiting Stage-7 re-review.
**Direction:** accepted at the Stage-1 gate
([brainstorm](../../research/aws-ai-architect-explainer-brainstorm.md),
DIRECTION ACCEPTED 2026-08-27) — **D1 + D4 + D5 composite** with the **D3
honesty-key currency rider**: D1 narrative spine ("the loop, left running"),
D4 decision map as a dedicated Part (~9 ADR-candidate cards), D5 dual-plane
(amber model lane / teal envelope lane) as the diagram convention throughout,
honesty-key marking of verified-2026 vs course-era vs superseded claims.
**(R1: the honesty-key badge grammar is removed — currency honesty is now
carried by current-practice-only prose, the retained `.unverified` figure
markers, and the as-of provenance block.)**
Placement `docs/architecture/explainers/`. The D6-lite hygiene track (bundle
`log.md` seam + stale-flag entries) was executed at Stage 1.
**Change class:** documentation deliverable (one HTML file + one decision-log
pointer line); no code paths, no new dependency, no ⚠️ Ask-first trigger →
decision-log entry, no ADR. `check_gate` (skill-sync) untouched by
construction — no skill surfaces are written. `test_gate = <none>`.

## Clarify decisions

| ID | Question | Recommendation | Decision |
|----|----------|----------------|----------|
| C1 | Scope cut (H4): which topics ride the spine at full depth vs compress? | Loop-ladder spine only (six Parts); everything else compresses to envelope beats + decision cards | **Spine + evals Part** (owner-selected 2026-08-27): the six ladder Parts **plus a dedicated full-depth Part VII "The eval decides"**; RAG, caching, guardrails, observability/FinOps, data-retention compress to envelope beats + their decision card |
| C2 | Deliverable path/name + size budget | `docs/architecture/explainers/aws-ai-architect-story.html`, cap 180 KB | **Same path, roomier cap** (owner-selected 2026-08-27): `docs/architecture/explainers/aws-ai-architect-story.html`; hard cap **≤ 250 KB**, target ~155–160 KB — the cap is head-room, not a target; the C1 scope cut still governs |
| C3 | Citation / as-of policy for currency claims (incl. P8 `needs-probe` rows) | **Strict zero external `href`/`src`** (o7 precedent, full `file://` parity): citations rendered as plain-text source names (e.g. "AWS Bedrock pricing page, as of 2026-08-27"), a footer provenance block listing primary sources, and inline "unverified — check the current page" markers on the P8 figures | **locked as recommended** |
| C4 | Artifact publication at converge? | **Yes** — publish a private claude.ai Artifact after the repo file lands; the repo file stays canonical (M1-atlas C2 precedent) | **locked as recommended** |

**Open questions:** none beyond C1–C4.

## Problem

The corrected Stage-1 framing (brainstorm §2.1, premises P3/P6/P7 refuted):
this is **not** the first Claude-architect guide — `docs/claude-architect-m1-atlas.html`
already exists, is committed, and is Pages-allowlisted. The missing artifact is
the **bundle-synthesis explainer** the atlas is not: a narrative that reads the
two case bundles (`cases/claude-architect-foundation/aws-claude/`,
`cases/aws-ai/`) *through* the mid-2026 platform delta, for an architect
reader. Three constraints are load-bearing:

1. **Seam vs the atlas** — the atlas is a certification-module study aid; this
   guide is a story + decision map over the bundles. It must define that seam,
   not duplicate atlas sections.
2. **Seam inside the sources** — `cases/aws-ai/` is stitched from two books
   (ch01–07 Strands/AgentCore vs ch08–10 console-era classic Bedrock Agents);
   the guide must not present them as one coherent stack without translation.
3. **Currency honesty** — the notes are systematically course-era (prefill
   extraction now returns 400; manual thinking budgets rejected; Bedrock
   Agents Classic closed to new customers 2026-07-30; MCP transports
   superseded by the 2026-07-28 stateless spec). Silently retelling them would
   ship 2024-era guidance under a 2026 date — the honesty key exists to
   prevent exactly this. **(R1: the same honesty is now achieved by
   publishing only the translated, current-state guidance — the reader never
   sees a labeled stale layer, and no stale claim ships because none is
   retold.)**

## Scope — source material

| Source | Role |
|---|---|
| `cases/claude-architect-foundation/aws-claude/` (10 Concepts) | primary teaching content — Claude-on-Bedrock mechanics (Converse, tool loop, MCP, caching, evals, RAG, thinking/vision, agents, Claude Code) |
| `cases/aws-ai/` (ch01–ch10) | supplementary platform arc — tools → memory → multi-agent → MCP/A2A → deployment → evals/governance → security; **two-book seam per its `log.md` 2026-08-27 entry** |
| [brainstorm §3 currency-delta table](../../research/aws-ai-architect-explainer-brainstorm.md) (14 rows + still-true spine) | the mid-2026 delta the guide narrates; the in-repo distillation of the 10-agent research pass (2026-08-27) — the guide's currency claims trace here |
| `docs/architecture/explainers/o7-pipeline-story-v2.html:14-22` | design language: palette tokens + semantics (`--det` teal deterministic/trustworthy, `--llm` amber model reasoning, `--human` slate, `--proposed` dashed violet never-confused-with-real), masthead → sticky key → Parts → scorecard → footer Honesty note |
| `docs/claude-architect-m1-atlas.html` | seam reference only — named, not duplicated |
| `docs/architecture/log.md` | registration surface (FR-11) |

Bundle citations are by **Concept/chapter title, not line number** — the
primary bundle is untracked and in-flight (P4); line-level cites would rot.

## Deliverable structure (the accepted composite)

Masthead ("The Loop, Left Running" working title + seam statement) → sticky
**lane legend (R1)** (`top:0`, the page's only sticky element: amber model
lane / teal envelope lane / the `.unverified` chip — no claim badges) → seven
spine Parts (D1 + C1's evals Part) → the decision-map Part (D4) → scorecard
table → footer (About / Honesty note / provenance + as-of date).

**The spine (D1, C1-decided)** — one story told once, each Part ending with an
**envelope beat** (D5: what the deterministic plane must own before the next
escalation):

| Part | Story step | Core content (delta rows it carries) |
|---|---|---|
| I | **One call** | a single stateless Converse/Messages call; model ladder Haiku 4.5 → Sonnet 5 → Opus 5 → Fable 5; endpoints `bedrock-runtime` vs `bedrock-mantle`; adaptive thinking/effort (rows 1, 2, 4, 5) |
| II | **The loop** | tool use, the `stop_reason` contract; structured extraction via tool schemas (rows 1, 3-lite) |
| III | **The loop with servers** | MCP: tools/resources/prompts control split; the stateless transport spec as current practice (row 8) |
| IV | **The loop left running** | agent = loop + state; memory; Strands as the code-first frame (rows 7-lite, 11-lite) |
| V | **Many loops** | multi-agent patterns, A2A v1.0, the protocol stack MCP/A2A/AG-UI/x402 (row 14); "start simple, escalate on evidence" (still-true) |
| VI | **The loop as infrastructure** | AgentCore: Runtime/Instances, Harness (the tool loop as a managed service), Gateway, Identity, Memory, Policy, Evaluations, Observability; one plain-prose fact that Bedrock Agents Classic is closed to new customers and AgentCore is the platform (rows 7, 10-lite, 12-lite) |
| VII | **The eval decides** (C1) | the doctrine Part: build-time evals (Strands Evals, pass@k vs pass^k, trajectory matchers, CI gates) vs production sampling (AgentCore Evaluations, 1–5%); Bedrock Evaluations LLM-judge/BYOI; Anthropic task/trial/grader framing; evals as the envelope's gates — incl. effort-level selection replacing the on/off thinking toggle (rows 2-lite, 11, 12-lite) |
| VIII | **The decision map** (D4) | the nine cards below (rows 3, 6, 9, 10, 12, 13 land here; the eval-tier card distills Part VII) |

**The nine decision cards (D4, VIII):** endpoint (`bedrock-runtime` vs
`bedrock-mantle`) · routing (global vs geo profiles, +10% regional, service
tiers) · model selection (the ladder × cost × retention coupling) · context
strategy (RAG vs cached long-context vs agentic retrieval; the "<~200k tokens
skip RAG" rule; caching economics) · orchestration (config vs code: Harness
vs Strands vs raw loop) · governance split (content: Guardrails/org-enforced/
Automated Reasoning vs action: Cedar/AgentCore Policy) · eval tiers
(build-time Strands Evals pass^k vs production AgentCore Evaluations
sampling) · deployment quantum (AgentCore Runtime vs Lambda vs ECS) ·
data-retention mode (`none`/`default`/`provider_data_share`; Fable 5 requires
share, Opus 5 ships ZDR). Each card: the decision, a trade-off table, a
**default + when-to-deviate** line.

**One visual grammar (R1):** the palette tokens serve the figures only —
every architecture diagram has an amber **model lane** (probabilistic:
prompting, thinking, tool choice) and a teal **envelope lane** (deterministic:
IAM, Cedar, DAG routing, guardrails, quotas, evals-as-gates), as labeled area
fills; slate stays reserved for human-decision accents in figures. The
claim-badge grammar (verified-2026 / course-era / superseded chips, the
was/now `.delta-pair` construct) is **removed**. The only prose chip that
remains is the `.unverified` figure marker (FR-8) — it must wrap normally
(no `nowrap`) so it can never force body horizontal scroll (AC-3).

## Functional requirements

- **FR-1 Single self-contained file** at the C2 path. Zero external requests:
  no CDN, no web fonts, all CSS/JS inline, all diagrams inline SVG using
  `var(--token)` colors. Works from `file://` offline.
- **FR-2 Narrative spine.** The seven spine Parts in the order above, each
  readable top-to-bottom as prose, each closing with an envelope beat. The
  story is fresh distillation of the bundles + delta — not a
  chapter-by-chapter retell.
- **FR-3 Two-lane figures.** Every architecture figure renders both lanes
  (amber model / teal envelope) per the D5 convention; single-lane figures are
  allowed only for non-architecture illustrations (e.g. a pricing table
  visual), and the plan enumerates any such exceptions.
- **FR-4 Decision-map Part.** The nine cards above, each with a trade-off
  table and a default + when-to-deviate line; cards cross-link (plain anchors)
  to the spine Part that motivates them.
- **FR-5 Current-practice-only prose (R1, replaces honesty-key marking).**
  The page states current (as-of-2026-08) recommended practice, plainly, with
  no temporal labeling taxonomy: no claim badges, no was/now pairing blocks,
  and none of the vocabulary "verified 2026", "course-era", "superseded" in
  reader-visible text. A retired mechanism may be named in at most one plain
  sentence where the reader could otherwise walk into it (e.g. Bedrock Agents
  Classic is closed to new customers; AgentCore is the platform) — stated as
  fact, never as a labeled historical layer.
- **FR-6 Delta coverage (R1-revised).** All 14 rows of the brainstorm §3
  table land on the page **as their current-state guidance** (spine Part or
  decision card per the structure table above), carried by the invisible
  `data-delta="1…14"` anchors for coverage bookkeeping. The history behind a
  row is not narrated (FR-5); the anchors are for verification only.
- **FR-7 Seam statements.** The masthead (or an early aside) names the seam vs
  the M1 atlas (study aid vs bundle-synthesis story) in ≤3 sentences; the
  About footer records the two-book provenance of `cases/aws-ai/` and points
  at both bundle `log.md`s.
- **FR-8 As-of provenance + needs-probe marking.** A footer as-of line
  (research date 2026-08-27); every P8-unverified figure (5-gen per-MTok
  prices, 1h-cache-write multiplier, Managed-KB rates) carries an inline
  "unverified — check the current pricing page" marker per C3.
- **FR-9 Originality.** All prose fresh; no verbatim bundle/course sentence
  >15 consecutive identical words (kept exact: numbers, product names, API
  field names, rules of thumb). Footer states the guide is an independent
  synthesis of the author's notes, pointing to AWS/Anthropic docs as
  authority.
- **FR-10 Theming.** Light/dark via CSS custom tokens; the three-block
  dark-mode pattern (bare `:root` light palette; `prefers-color-scheme: dark`
  guarded `:root:not([data-theme="light"])`; `:root[data-theme="dark"]`);
  explicit body background token.
- **FR-11 Registration + converge.** One hand-written newest-first entry in
  `docs/architecture/log.md` naming the file, the design language
  (o7-v2), and SDD provenance (brainstorm + this spec). No `index.md` entry —
  HTML is outside `okf_lint` scope by design. At converge (per C4): publish
  the finished file as a private claude.ai Artifact; the repo file stays
  canonical.
- **FR-12 Responsive + accessible baseline (R1-extended).** No horizontal
  body scroll at ≤375 px (wide figures/tables scroll inside their own
  `overflow-x` containers); interactive reveals (if any) keyboard-operable;
  `prefers-reduced-motion` respected; content never gated on JS. Hash-jump
  targets (`#d-*`, `h2`) carry `scroll-margin-top` clearing the sticky
  legend; links/targets have a `:focus-visible` style; data tables use
  `<thead>` with no empty header cells (or a `<caption>`/`scope` where the
  first column is a row-header axis).
- **FR-13 Plain-English immersive narration (R1, new).** Long-form-article
  voice: plain, simple English; every technical term or acronym introduced in
  ordinary words at first use; each Part opens with a concrete hook or scene
  an architect recognizes and carries the running "loop, left running"
  thread (second person welcome, envelope beats as recurring cadence).
  Engagement never invents facts: every claim stays grounded in the sources,
  with the `.unverified` markers and as-of provenance as the honesty valves.
- **FR-14 Standard document shell (R1, new).** The file opens with
  `<!DOCTYPE html>`, `<html lang="en">`, and a `<head>` containing
  `<meta charset="utf-8">` plus the viewport meta — so the page renders in
  standards mode with correct UTF-8 over HTTP, not just `file://`.
- **FR-15 Verifier checked in (R1, new).** The static verifier lives in the
  repo next to the deliverable
  (`docs/architecture/explainers/verify_aws_ai_story.py`, stdlib-only) so
  future edits can re-run the AC gate; it is a converge tool, not a CI gate.

## Acceptance criteria (EARS — failure paths first)

- **AC-1** IF JavaScript is disabled or fails, THEN every Part, card,
  figure, and badge remains readable in document order — interactivity is
  progressive enhancement, never a content gate.
- **AC-2** IF the file is opened from `file://` with networking blocked, THEN
  the page renders identically to the online case — verifiable: zero
  `http(s)://` in `src`/`href` attributes (C3 strict policy).
- **AC-3** IF a viewer is at ≤375 px width, THEN the body has no horizontal
  scroll; wide figures and tables pan inside their own containers.
- **AC-4 (R1, replaced)** IF the page is grepped for the removed temporal
  grammar, THEN zero matches remain: no `.b-verified` / `.b-course` /
  `.b-superseded` / `.b-human` chip classes, no `.delta-pair` / `.was` /
  `.now` constructs, and none of the strings "verified 2026", "course-era",
  "superseded" in reader-visible text.
- **AC-5 (R1-tightened)** IF a figure or rate is one of the P8-unverified
  values, THEN **every occurrence** of it (prose, decision cards, scorecard)
  carries the inline unverified marker and the footer as-of date covers it —
  no occurrence ships bare.
- **AC-6** IF any prose span reproduces >15 consecutive identical words from
  either bundle, THEN the build fails review — spot-checkable by grepping
  distinctive source phrases against the HTML.
- **AC-7 (R1, rewritten)** WHEN the page loads, the sticky legend (the only
  sticky element, `top:0`) defines the two lanes (amber model / teal
  envelope) and the `.unverified` chip — nothing else — legible in both
  light and dark themes.
- **AC-8** WHEN any architecture figure is viewed, both lanes are present and
  labeled, colored via `var(--llm)` / `var(--det)` (no hard-coded hex in
  figure fills); plan-enumerated exceptions only.
- **AC-9** WHEN the decision-map Part is read, all nine cards are present,
  each with a trade-off table and a default + when-to-deviate line, each
  anchor-linked from/to its motivating spine Part.
- **AC-10** Ubiquitous: all 14 delta rows are covered per the structure
  table's row mapping, reconciled by a row-by-row checklist in the tasks file
  (coverage verified, not assumed).
- **AC-11 (R1-trimmed)** Ubiquitous: the seven spine Parts appear in the
  structure-table order, each closing with an envelope beat.
- **AC-12** Ubiquitous: theme sanity in both `prefers-color-scheme` modes
  (explicit body background; no token defined in only one theme); total file
  size ≤ 250 KB (C2).
- **AC-13** Ubiquitous: the seam statement (atlas) and the two-book
  provenance note (aws-ai) are present per FR-7.
- **AC-14** Ubiquitous: the `docs/architecture/log.md` entry exists, is
  newest-first, and names file + design language + SDD provenance; no other
  registration surface is touched.
- **AC-15 (R1, new)** WHEN the file is served over HTTP, the browser reports
  UTF-8 and standards mode (`characterSet: "UTF-8"`,
  `compatMode: "CSS1Compat"`) and no mojibake appears in the masthead,
  figure titles, or footer.
- **AC-16 (R1, new)** WHEN any Part is read, it reads as plain-English
  narrative per FR-13: a concrete opening hook, no unexplained acronym at
  first use, no taxonomy vocabulary (FR-5). Human-judged by targeted read at
  the converge gate — deliberately not machine-checkable.

## Verification method (how each AC is checked)

- **Grep/script probes (the checked-in verifier, FR-15):** AC-2 (no external
  `src`/`href`), AC-4 (zero residue of the removed grammar: chip classes,
  `.delta-pair`/`.was`/`.now`, label strings), AC-5 (every occurrence of a
  P8 figure carries the marker — value-keyed, not just a class count), AC-6
  (distinctive-phrase sweep), AC-8 (no hex fills in SVG outside the token
  block), AC-12 (file size; token defined in all three theme blocks), AC-10
  (`data-delta` 1–14 each present at its structure-table location), AC-15
  static half (doctype/`html lang`/charset present in the first bytes),
  plus the static halves of AC-9/11.
- **Targeted reads:** AC-7/9/11/13 (legend block, nine cards, Part order +
  envelope beats, seam statements) and AC-16 (voice pass, human-judged).
- **Browser checks:** AC-1 (JS off), AC-3 (≤375 px viewport, and a 300 px
  probe of `document.documentElement.scrollWidth`), AC-12 (dark mode), AC-15
  (served over `python3 -m http.server`: `characterSet`/`compatMode`) via the
  in-app browser pane.
- Baseline before implementation: `check_gate`
  (`python3 tooling/skill-sync/skill_sync.py check` from repo root) green;
  `test_gate = <none>`.

## Out of scope / deferred

Pages allowlisting (`apps/html-site/manifest.toml` — its own spec + ADR 0001
discipline, never a side effect) · any rewrite of source-bundle *content*
(okf-curator territory; the D6-lite log entries already landed at Stage 1) ·
a companion markdown Concept (`type: overview`) in either bundle · quiz /
self-test / progress layers (M1-atlas territory) · the `aws-ai-*` skill-family
briefs (the decision map may later be referenced by them; no skill surface
changes here) · localStorage or any persistence · any edit to `tooling/`,
`src/`, or skill surfaces.
