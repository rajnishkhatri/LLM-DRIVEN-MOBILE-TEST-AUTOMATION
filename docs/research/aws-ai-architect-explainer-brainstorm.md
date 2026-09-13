---
type: analysis
title: 'SDD Stage 1 — Brainstorm: AWS + Claude AI-architect explainer guide'
description: >-
  Premise audit, external-research currency delta, and six directions for an
  architect-level HTML explainer synthesized from the aws-claude and aws-ai
  bundles, in the o7-pipeline-story-v2 design language.
tags: [sdd, brainstorm, aws, bedrock, claude, explainer, agentcore]
---

# SDD Stage 1 — Brainstorm: AWS + Claude AI-architect explainer guide

**Stage:** SDD Stage 1 (brainstorm / ideation)
**Binding:** `.sdd/binding.toml` — constitution `.cursor/rules/architecture-principles.mdc`; spec home `docs/sdd/specs/`; `test_gate = <none>`; `check_gate` = skill-sync (repo root only)
**Status:** DIRECTION ACCEPTED 2026-08-27 — owner picked the **D1 + D4 + D5 composite** (D1 narrative spine; D4 decision map as a dedicated Part; D5 dual-plane as the diagram convention throughout), with the **D3 honesty-key currency marking** rider, placement in `docs/architecture/explainers/`, and the **D6-lite hygiene track executed at this stage** (seam + stale-flag entries appended to both bundle `log.md`s, `okf_lint` green). Advance → `sdd-spec`.
**Home:** `docs/research/aws-ai-architect-explainer-brainstorm.md`
**Research provenance:** 10-agent workflow, 2026-08-27 — 4 repo auditors (both source bundles read in full, o7-v2 design system, premise audit) + 6 external researchers (Bedrock platform, AgentCore/Strands, Anthropic guidance, Well-Architected/security, RAG/KB, evals/observability), all findings source-linked to primary AWS/Anthropic docs.

> Per `sdd-brainstorm`: restate the problem → premise audit against the working tree → ~6 directions → hypothesis validation for a lead → dependency map → **human gate**. No spec is written here.

---

## 0. Restated problem (not a solution)

Produce an **architect-level explainer guide** — a self-contained HTML page in the `o7-pipeline-story-v2` design language — that synthesizes:

1. **Primary content:** `cases/claude-architect-foundation/aws-claude/` — 10 distilled Concepts on Claude-on-Bedrock mechanics (Converse, tool use, MCP, caching, evals, prompt techniques, RAG, thinking/vision, agents, Claude Code). Provenance: a same-day split of one prompt-engineering course dump (`log.md`, 2026-08-27).
2. **Supplementary context:** `cases/aws-ai/` — 10 chapters on AWS AI agents (tools → memory → multi-agent → MCP/A2A → deployment → evals/governance → security → end-to-end → sustainability). Provenance: **two** source books (see premise audit).
3. **External research** (this stage, complete): the mid-2026 AWS/Claude landscape, to give the guide currency and depth the course-era notes lack.

The reader is an architect who wants the conceptual map of building AI systems on AWS with Claude — not a hands-on tutorial reader.

---

## 1. Constitution / subtree backdrop

Touched folders: `docs/research/` (this doc), later `docs/architecture/explainers/` or `docs/` (the guide), `docs/architecture/log.md` (catalog entry). No nested `CLAUDE.md` constitutions exist anywhere in the repo (audited; governance runs through `docs/CONVENTIONS.md`, `.okf/binding.toml`, `.sdd/binding.toml`).

**Constitution** (`.cursor/rules/architecture-principles.mdc`): no numbered invariant list; load-bearing principles here:

| Principle | Why it binds this change |
|---|---|
| **Single Responsibility** | Source bundles (knowledge plane) ≠ explainer (narrative artifact) ≠ host (surface). Fixing stale sources and authoring the guide are separate responsibilities. |
| **Trade-off analysis** | The guide's own content is trade-off tables (endpoint choice, RAG vs long-context, config vs code); the artifact must practice what it teaches. |
| **Coupling** | The explainer must not link to non-vendored paths (evidence segments stay uncommitted — `.okf/binding.toml` de-linking precedent, 2026-08-11). |
| **Simplest style that works** | A static self-contained HTML file, like every prior guide; no new runtime, dependency, or service. |

**De-facto invariants from precedent (must not silently break):**

- Self-containment: no CDN, no external `href`/`src`; works from `file://` (o7 explainers have zero external refs; prep-guide FR-1 precedent).
- Honesty-key semantics stay intact: teal `--det` = deterministic/trustworthy, amber `--llm` = model reasoning, slate `--human` = human decision, **dashed violet `--proposed` = never confused with real** (`docs/architecture/explainers/o7-pipeline-story-v2.html:14-22`).
- Surface discipline: repo file is the only surface by default; the public Pages origin is allowlist-only per ADR 0001 (`docs/architecture/log.md`, 2026-08-26 entry) — adding the guide there is a later spec + manifest row, never a side effect.
- Discovery = a hand-written newest-first entry in `docs/architecture/log.md` (house pattern names the file, the design language, and SDD provenance). HTML is outside `okf_lint` scope (`.okf/binding.toml` globs are `**/*.md` only).
- One sticky element: the page's own honesty-key legend at `top:0`; no second sticky chrome.

⚠️ **Ask-first items:** none for the default direction (repo-only HTML file — no new dep/service/abstraction). Pages allowlisting, if ever chosen, is the one ⚠️ item and lives behind its own spec/ADR.

---

## 2. Premise audit

| # | Premise | Status | Evidence |
|---|---|---|---|
| P1 | Both source folders exist and are complete (12 md each) | **verified** | `ls` both dirs: 10 Concepts + index + log (aws-claude, ~42KB); ch01–ch10 + index + log (aws-ai, ~675KB) |
| P2 | `o7-pipeline-story-v2.html` exists and is the latest design-language reference | **verified** | v1 + v2 exist, same title, v2 newer/larger; no v3; palette read directly (`o7-pipeline-story-v2.html:1-100`) |
| P3 | No AWS/Claude architect guide exists yet | **REFUTED** | `docs/claude-architect-m1-atlas.html:6` — `<title>Claude Architect Atlas</title>`, a Module-1 study atlas with 12 sections and heavy Bedrock coverage, committed (cf5a5c) and allowlisted on the public Pages origin. Re-posed framing in §2.1 below. |
| P4 | Primary source bundle is committed | **REFUTED (known)** | `git status`: `?? cases/claude-architect-foundation/` — untracked; its catalog wiring exists only as the uncommitted diffs to `.okf/binding.toml`, `docs/CONVENTIONS.md`, `docs/skills/okf-curator-instructions.md`. The explainer layers on an in-flight change. |
| P5 | SDD binding resolves | **verified** | `.sdd/binding.toml:11-12+`: constitution `.cursor/rules/architecture-principles.mdc`; spec home `docs/sdd/specs/` (13 spec precedents); brainstorm home precedent `docs/research/*-brainstorm.md` (4 priors) |
| P6 | The two bundles are one coherent corpus | **REFUTED** | `cases/aws-ai/` is stitched from **two books**: ch01–07 = Packt "AI Agents on AWS" (Strands/AgentCore, 2025–26 model ids); ch08–10 = "Using Amazon Bedrock" (renaldig repo, console-first, classic Bedrock Agents `create_agent` API, legacy model ids; ch09 even ships a Text-Completions body against a Messages-only model — cannot run as written). Neither `index.md` nor `log.md` records the seam. |
| P7 | The notes are current enough to teach from directly | **REFUTED** | Systematic course-era staleness confirmed by research (§3): the prefill+stop extraction pattern that four aws-claude notes lean on now returns HTTP 400 on all current Claude models; manual thinking budgets are rejected; "Bedrock Agents" ch08 secures a product closed to new customers 2026-07-30; the MCP transports named are superseded by the 2026-07-28 stateless spec. |
| P8 | Research claims about pricing/GA dates are all confirmable from primary docs | **unverifiable (partial)** | Bedrock's pricing page is JS-rendered; a handful of numbers (5-gen per-MTok on the AWS page, 1h-cache-write multiplier on Bedrock's bill, Managed-KB rates) are Anthropic-list or secondary-source figures. Tagged `needs-probe`; the guide must carry an as-of provenance footer and mark these. |

### 2.1 Re-posed framing (P3, P6, P7 corrected)

The corrected problem is **not** "write the first Claude-architect guide." It is:

> Write the **bundle-synthesis explainer** that the M1 atlas is not: the atlas is a certification-module study aid (committed, published); this guide narrates the *two case bundles* + the *mid-2026 delta* for an architect. It must (a) define its seam against the atlas instead of duplicating it, (b) not present the two source books as one coherent stack (P6), and (c) treat the notes' course-era claims as *teaching artifacts to be marked*, not facts to be repeated (P7). Silently retelling the notes would ship 2024-era guidance under a 2026 date — the exact failure the honesty key exists to prevent.

---

## 3. The currency delta (external research, condensed)

What changed between the course era captured in the notes and 2026-08-27. Each row is source-linked in the research dossiers; the guide's spec will carry the citations.

| # | Notes teach | Mid-2026 reality |
|---|---|---|
| 1 | Prefill + stop-sequence as THE structured-output extractor (4 notes rely on it) | **Assistant prefill returns 400** on Claude 4.6+/5-gen. Replacements: tool-schema extraction, structured outputs (not yet on Bedrock for Opus 5/Sonnet 5), system-prompt schemas + validated retry |
| 2 | Extended thinking = flag + `budget_tokens` (min 1024), eval-gated on/off | Manual budgets deprecated (4.6) / rejected (4.7+). **Adaptive thinking** + `output_config.effort` (low→max); always-on for Fable 5; evals now pick an *effort level*, not a toggle |
| 3 | Caching: 5-min TTL, 1024-token min, no pricing given | Per-model minimums (512/1024/4096), 5m **and 1h** TTLs, write 1.25×/2×, read 0.1×, cache reads quota-free, max 4 checkpoints, batch-incompatible |
| 4 | "Sonnet, Haiku and peers", dated model ids, 200K context | Claude 5 family (Opus 5 $5/$25, Sonnet 5 $2/$10, Fable 5 $10/$50), dateless ids, **1M context standard-priced**, 128K output, 4.7+ tokenizer emits ~30% more tokens |
| 5 | One API (Converse), one endpoint | Five API patterns on `bedrock-runtime` + new **`bedrock-mantle`** endpoint (first-party Messages API; no KB/Guardrails/Agents attach); Anthropic labels Converse-integration "legacy (≤ Opus 4.6)" |
| 6 | Inference profiles route cross-region at no premium | `global.` vs geo profiles; **regional = +10%** on Sonnet 4.5+; service tiers (Priority/Flex/Reserved); output-token quota burndown (10× for Opus 5/Sonnet 5) |
| 7 | ch08's "Bedrock Agents" (action groups) as the managed-agent path | **Bedrock Agents Classic: closed to new customers 2026-07-30, model catalog frozen.** AgentCore is the default: Runtime (+Instances GA 2026-08), Harness (GA 2026-06), Policy/Cedar (GA 2026-03), Evaluations (GA 2026-03), Gateway, Identity, Memory, Observability |
| 8 | MCP transports "stdio, HTTP, WebSockets"; sampling/roots as features | **Spec 2026-07-28**: stateless (no handshake/session), Streamable HTTP, MRTR replaces server-initiated requests, **Roots/Sampling/Logging deprecated**, OAuth 2.1 + CIMD, Linux Foundation governance |
| 9 | Hand-rolled RAG (Titan Embed V2, DIY BM25+RRF, LLM rerank) | Bedrock KB (classic + **Managed KB**, GA 2026-06, agentic retriever), S3 Vectors GA (~90% cheaper tier), GraphRAG/Neptune, Rerank API ($1–2/1k queries), hybrid-search store constraints; **"<~200k tokens → skip RAG, cache the corpus"** (Anthropic) |
| 10 | Guardrails = an app-level filter | A layered control plane: org-enforced guardrails (GA 2026-04, non-bypassable), Automated Reasoning checks (GA 2025-08, formal verification), `InvokeGuardrailChecks` for per-step agent loops (2026-06), Standard tier (cross-region dependency); plus **Cedar/AgentCore Policy: content vs action governance split** |
| 11 | Offline prompt evals (dataset → grade → average) | Two-tier practice: build-time (Strands Evals, pass^k, trajectory matchers, CI gates) + production online sampling (AgentCore Evaluations, 1–5%); Bedrock Evaluations GA w/ LLM-judge + BYOI; Anthropic "Demystifying evals" (task/trial/grader, pass@k vs pass^k) |
| 12 | Observability = CloudWatch logs exist | CloudWatch GenAI observability GA, OTel `gen_ai.*` conventions (adopted but pre-1.0), AgentCore Observability (incl. on-prem/multi-cloud), invocation logging OFF by default (governance gap to close), app inference profiles for chargeback, cache-hit-rate as FinOps KPI |
| 13 | "Providers never see customer data" | Now a **configurable policy surface**: data-retention modes (`none`/`default`/`provider_data_share`) with SCP condition key; Fable 5/Mythos 5 *require* provider_data_share (30-day retention); Opus 5 ships ZDR-by-default |
| 14 | MCP + A2A as the protocol story | Four layers: MCP (tools), A2A v1.0/LF (agents), **AG-UI** (frontend), x402/MPP (payments, preview); AgentCore Gateway as the managed choke point |

**Still-true spine (survives verification):** the tool loop (`stop_reason` contract) is unchanged and is now literally a managed service (AgentCore Harness); the MCP tools/resources/prompts control split still teaches correctly; "the eval decides" is now Anthropic's and AWS's official doctrine; "start simple, escalate on evidence" (single agent before multi-agent) is stated by both bundles and both vendors; the determinism-vs-probability split (Cedar/DAG/IAM vs model) matured from book theme into shipped product (Policy, Graph, org-enforced guardrails).

---

## 4. Independent axes (do not conflate)

1. **Narrative structure** — story vs atlas vs delta-organized vs decision-map (the direction pick).
2. **Currency treatment** — whether the guide *marks* course-era vs 2026-verified claims with the honesty key, or silently writes as-of-2026.
3. **Placement & surface** — `docs/architecture/explainers/` (design-language home) vs `docs/` root (recent guide precedent); repo-only now regardless; Pages later behind its own spec.
4. **Source-plane hygiene** — recording the P6 seam and P7 stale-pattern flags in the *bundles* is knowledge-plane truth-keeping, independent of any guide.

---

## 5. Candidate directions (~6)

### High-probability (follow existing repo patterns)

**D1 — "The Loop, Left Running": single narrative explainer** *(recommended lead)*
One story told once: a single stateless Converse call → the tool loop → the loop with a server (MCP) → the loop left running (agent) → many loops (multi-agent patterns) → the loop as infrastructure (AgentCore Runtime/Gateway/Policy/Evaluations) — with caching/RAG/evals/guardrails entering the story where the loop makes them necessary. The two bundles already layer this deliberately (the aws-claude audit found the tool loop told at three altitudes; the aws-ai arc is the same ladder at platform altitude).
*Pattern followed:* `o7-pipeline-story-v2.html` (masthead → sticky key → numbered sections in Parts → scorecard table → proposed zone → footer provenance) + spec-first flow (`docs/sdd/specs/ccar-p-prep-guide.spec.md` precedent).
*Trade-offs:* strongest pedagogy, clearest seam vs the M1 atlas (story vs reference); but weakest as a lookup artifact, and scope must be cut hard (the corpus is ~10× what one story can hold).
*What breaks if chosen:* nothing in-repo; the risk is page bloat (o7-v2 is 80KB; this corpus could triple that — the spec must set a size budget).
*Invariant stressed:* honesty key (needs a principled mapping for "course-era claim, superseded" — see D3 rider).

**D2 — Companion atlas volume ("Architect Atlas, Module 2")**
A sectioned reference atlas in the `claude-architect-m1-atlas.html` mold: ~10 lookup sections (platform map, model selection, API surfaces, caching, RAG/KB, agent topologies, AgentCore, security/governance, evals/observability, FinOps), each with decision tables. Sited in `docs/` next to the M1 atlas, spec'd like `platform-design-atlas.spec.md`.
*Pattern followed:* the M1 atlas + platform-design-atlas spec.
*Trade-offs:* best as a durable reference and cleanest continuation of the published study cluster; but highest duplication risk against M1 (whose 12 sections already cover Platform Map, RAG Pipeline Design, Reference Architectures) — the spec would need a section-by-section seam audit. A variant (extend M1 in place) was considered and rejected: it entangles a published, allowlisted artifact with uncommitted source bundles and mixes certification provenance with bundle synthesis.
*What breaks:* M1's positioning ("Module 1") implies a series; a sloppy M2 fragments rather than extends it.
*Invariant stressed:* surface discipline (sitting next to two Pages-allowlisted files invites "just allowlist it too" — that stays a separate spec).

**D3 — Currency-first explainer ("What the course couldn't tell you")**
Organize the guide around the delta table in §3: each section = the durable mechanism (still-true spine) + what 2026 changed, with the honesty key doing the epistemics — teal = verified-current (source-linked), amber = model-behavior/course-era teaching, dashed violet = superseded/changed. The research corrections become the guide's spine rather than its footnotes.
*Pattern followed:* the honesty-key ethos itself; the CCAR-P v3 integrity-pass precedent (claims carry their verification status).
*Trade-offs:* the most honest and the most differentiated from both the M1 atlas and the source bundles; ages the best (the delta frame expects future deltas). But it teaches *against* a baseline the reader may not share — weaker for a reader who never took the course.
*What breaks:* nothing; but it makes the guide depend visibly on research citations, so the unverifiable price/date rows (P8) must be marked `needs-probe` in-page.
*Invariant stressed:* honesty key (this direction is the key, generalized from "proposed vs real" to "verified vs course-era vs superseded").

### Exploratory (different abstraction / integration / shift)

**D4 — Decision-architecture map**
Not a walkthrough: ~9 architect decision points rendered as ADR-candidate cards with trade-off tables — endpoint (`bedrock-runtime` vs `bedrock-mantle`), global vs geo profiles (+10%/residency), RAG vs cached-long-context vs agentic retrieval, config vs code (Harness vs Strands), content vs action governance (Guardrails vs Cedar), eval two-tier, deployment quantum (Runtime/Instances/Lambda/ECS), data-retention mode, model selection (Haiku→Fable ladder). Integrates with the `aws-ai-assess`/`aws-ai-design` skill stages as their referenced decision map.
*Trade-offs:* highest architect utility per byte; a genuine join of the arch-* and aws-ai-* families. But it abandons the bundles' narrative content (most of the course material appears only as context), and it duplicates what the aws-ai skill briefs already encode — the seam vs the skill family needs defining.
*What breaks:* scope discipline — every decision card invites becoming a full atlas section.
*Invariant stressed:* Single Responsibility (guide vs skill-family briefs).

**D5 — Dual-plane guide ("the determinism envelope")**
Organize everything around the corpus's strongest architect-grade idea: a probabilistic model inside a deterministic envelope. Two visual lanes throughout — amber lane (model: prompting, thinking, tool choice, memory) and teal lane (envelope: IAM, Cedar, DAG routing, guardrails, quotas, evals-as-gates) — every topic placed by which lane owns it, every diagram two-laned.
*Trade-offs:* the most original architectural framing, and a perfect fit for the existing color semantics; risk is procrustean — some topics (RAG, caching, FinOps) straddle lanes awkwardly, and the frame is the author's, not the sources'.
*What breaks:* diagram effort roughly doubles (every figure needs both lanes).
*Invariant stressed:* honesty key (reuses det/llm exactly as designed — lowest semantic drift of all directions).

**D6 — Source-plane hygiene first, thin explainer second**
Fix the knowledge plane before narrating it: record the two-book seam in `cases/aws-ai/log.md` (+ index note), add currency-flag notes to the stale Concepts (prefill, thinking budgets, Agents-Classic, MCP transports), then author a thinner explainer over corrected sources.
*Trade-offs:* class-over-instance fix (the defect class is "un-flagged staleness in course-dump bundles" — it will recur with every future dump); everything downstream inherits the corrections. But bundle edits touch the owner's in-flight uncommitted change (P4) and are `okf-curator` territory — sequencing it *before* the guide costs calendar time on the main deliverable.
*What breaks:* nothing if scoped to log/flag entries; rewriting note *content* would be a different, bigger change (not proposed).
*Invariant stressed:* Single Responsibility (curation vs authoring) — which is why §7 proposes the log/flag subset as a **do-regardless track**, not a competing direction.

---

## 6. Leading direction — hypotheses (D1 + D3 rider)

D1 (narrative) with D3's currency marking as the honesty-key mapping. Validated against the working tree:

- **H1 — works because the honesty key generalizes to claim-epistemics.** The v2 palette defines the semantics in-file: `--det` "deterministic / machine / trustworthy", `--llm` "LLM / authoring / 'fuzzy' reasoning", `--proposed` "proposed enhancement — never confused with real", always dashed (`docs/architecture/explainers/o7-pipeline-story-v2.html:14-22`, read directly). Mapping verified-current→det, model-behavior/course-teaching→llm, superseded→proposed-dashed preserves each token's core meaning (trustworthy / fuzzy / not-real). The footer "Honesty note" pattern exists for exactly this disclosure.
- **H2 — safe because no gate governs HTML.** `.okf/binding.toml` knowledge_globs are markdown-only (verified in the working-tree diff audit); `okf_lint` never sees the file; the Pages origin serves only the `apps/html-site/manifest.toml` allowlist (ADR 0001, log entry 2026-08-26, read directly). Ship = 1 new HTML file + 1 hand-written `docs/architecture/log.md` line. `check_gate` (skill-sync) untouched — no skill surfaces change.
- **H3 — works because the material is sufficient and load-bearing overlaps are mapped.** Bundle audits (full-read, this stage) provide per-file core ideas, the four-notes-deep prefill dependency, the three-altitude tool-loop layering, and the two-book seam; six research dossiers provide primary-source citations for every §3 row. No `needs-probe` blocks authoring; the P8 rows are marked in-page instead.
- **H4 — feasibility check ("one page can hold it" is a hypothesis, not a fact).** The corpus is ~717KB of source + six dossiers; o7-v2 is 80KB. A comprehensive retelling does not fit one page at explainer quality — **the spec must cut scope** (candidate cut: the story spine carries Converse→loop→agent→AgentCore→governance; RAG/evals/FinOps compress to one decision figure + scorecard row each). Cost is engineering-time only; no calendar waits — research is done.
- **H5 — process follows precedent.** Spec-first: `docs/sdd/specs/` holds 13 specs including both prior guide specs; next stage is `sdd-spec` (EARS + clarify + plan/tasks), not direct authoring. Brainstorm home + gate status recorded here, matching `html-site-hosting-brainstorm.md`.

Rejected hypothesis (context-blindness check): "reuse the M1 atlas section skeleton" — the atlas's 12 sections are certification-module-shaped (exam domains), not bundle-shaped; grafting them would re-import the duplication D2 risks. The seam, not the skeleton, is what the spec needs from the atlas.

---

## 7. Dependency structure

- **Do-regardless (zero-risk hygiene, any direction):** record the two-book seam + stale-pattern flags in the bundles' `log.md`s (D6-lite; `okf_lint` must stay green; touches only files already in the owner's in-flight change-set, so it lands as part of that commit, not a new surface).
- **The pick (this gate):** D1 / D2 / D3 / D4 / D5 as the guide's structure. D1+D3 compose (recommended); D5 can be a diagram convention inside any pick; D4 can be one Part of D1/D2 rather than the whole.
- **Sequenced after the pick:** `sdd-spec` (scope cut, seam-vs-atlas definition, size budget, citation/as-of policy, EARS criteria) → tasks → authoring.
- **Deferred behind their own specs:** Pages allowlisting (ADR 0001 discipline); any companion markdown Concept (`type: overview`, index + lint); any rewrite of source-bundle *content* (okf-curator stage, owner's call).
- **Cost axes:** all engineering time; no external waits. The one calendar risk is P4 — if the owner reshapes the untracked bundle, the guide's citations into it move; the spec should cite bundle content by Concept title, not line number.

---

## 8. Human gate

Direction-level acceptance only. Questions posed with explicit ids:

1. **Structure:** D1 story (rec) / D2 atlas M2 / D3 delta-first / D4 decision map / D5 dual-plane?
2. **Currency treatment:** honesty-key delta marking (D3 rider, rec) / delta appendix only / write-as-of-2026 silently (not recommended — P7)?
3. **Placement:** `docs/architecture/explainers/` (design-language home, rec) / `docs/` root (study-cluster home) / defer to spec?
4. **Hygiene track:** D6-lite do-regardless (rec) / fold into the guide spec / skip?

On acceptance: update **Status** above, then advance → `sdd-spec` with the chosen direction + H1–H5.

**Gate outcome (2026-08-27):** Q1 = D1 **+ D4 as a Part + D5 as the diagram convention** (composite); Q2 = honesty-key marking; Q3 = `docs/architecture/explainers/`; Q4 = do-regardless, executed — seam entry appended to `cases/aws-ai/log.md`, stale-flag entry appended to `cases/claude-architect-foundation/aws-claude/log.md`, no content rewrites, lint green. Spec-time consequences of the composite: the size budget must cover a decision-map Part (~9 ADR-candidate cards) inside the story arc, and every figure adopts the two-lane (amber model / teal envelope) convention — H4's scope cut becomes the spec's first clarify question.
