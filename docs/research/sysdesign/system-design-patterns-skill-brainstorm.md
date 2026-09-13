---
type: analysis
title: 'SDD Stage 1 — Brainstorm: system-design-patterns skill family'
description: >-
  Premise audit, content-inventory delta, seven directions, and a validated
  lead for a new skill family that turns the cases/SystemDesignPatterns OKF
  bundle into system-design skills for coding agents (Cursor + Claude now,
  Copilot later), standalone first and joinable to arch-*, aws-ai-*, sdd-* later.
tags: [sdd, brainstorm, system-design-patterns, skills, arch, skill-sync]
---

# SDD Stage 1 — Brainstorm: system-design-patterns skill family

**Stage:** SDD Stage 1 (brainstorm / ideation)
**Binding:** `.sdd/binding.toml` — constitution `.cursor/rules/architecture-principles.mdc`; spec home `docs/sdd/specs/`; `test_gate = <none>`; `check_gate` = `python3 tooling/skill-sync/skill_sync.py check` (repo root only)
**Status:** PARTIALLY GATED 2026-09-13 — owner answered the scope half: catalog confirmed and extended per group (superseding §3; see the [catalog of record](system-design-patterns-catalog.md)), group-appropriate depth bars, one group per research cycle, styles live in the bundle. The direction ids (G1, G2, G4, G5, G6) stay open until the catalog research completes (owner R5).
**Home:** `docs/research/sysdesign/system-design-patterns-skill-brainstorm.md`
**Owner framing confirmed 2026-09-13:** C1 broader system-design catalog (patterns to be recommended here and confirmed); C2 the deepened [Circuit breaker](../../../cases/SystemDesignPatterns/CircuitBreaker.md) is the depth bar for every pattern; C3 a **new sibling family** that works independently first and supports arch-* / aws-ai-* / sdd-* later; C4 Copilot is a later projection; C5 finish the Circuit breaker deepening in parallel.

> Per `sdd-brainstorm`: restate the problem → premise audit against the working tree → ~6 directions → hypothesis validation for a lead → dependency map → **human gate**. No spec is written here.

---

## 0. Restated problem (not a solution)

Coding agents (Cursor, Claude Code, later Copilot) have no skill in this workspace that lets them reason about **tactical system-design patterns** — circuit breaker, retry budgets, bulkheads, caching, outbox, saga, sharding, and the rest — with the same discipline the `arch-*` family brings to characteristics, components, style, decisions, risk and validation. The raw material is being sourced pattern by pattern into the `cases/SystemDesignPatterns/` OKF bundle at a fixed depth bar (mechanics, configuration, observability, tuning, placement, a worked calibration, trade-offs, cited sources). The problem is to turn that material into a skill family that:

1. works on its own — an agent with only this family installed can diagnose a symptom, pick a pattern, apply it with sane knobs, and verify it;
2. later plugs into `arch-*` (style / decide / risk / validate), `aws-ai-*` (agent tool-call resilience), and `sdd-*` (spec and converge gates) without redesign;
3. is projected to Cursor and Claude now through `tooling/skill-sync/`, with a Copilot projection deferred.

Not the problem: choosing architecture *styles* (that is `arch-style`), curating the bundle itself (that is `okf-curator`), or building runtime tooling.

---

## 1. Constitution / subtree backdrop

**Touched folders:** `cases/SystemDesignPatterns/` (content), `.cursor/skills/` (source of truth for a new family), `.claude/skills/` (projection), `tooling/skill-sync/manifest.toml` (family registration), `docs/skills/` (README row + instructions manual), `docs/research/` (this document). The 2026-08-27 brainstorm audited the tree for nested `CLAUDE.md` constitutions and found none; the same folders are touched here — re-verify at spec time.

**Constitution** (`.cursor/rules/architecture-principles.mdc`, `alwaysApply: true`): its scope names design patterns, architectural styles and system design explicitly, and its response guidelines are effectively the **pattern-card contract**: a concise definition, the motivation, a practical example or diagram; trade-off analysis on every decision; language-agnostic unless a stack is named; references to well-known sources. Any direction below that produces pattern content without trade-offs or sources violates the constitution.

**Gates:** `check_gate` is the skill-sync drift guard (currently `6 families, 0 drifted, 0 shadow -> exit 0`); `test_gate` is `<none>`, so the family's quality bar must come from somewhere else (see H4). The bundle itself is governed by the OKF lint gate (`python .cursor/skills/okf-curator/scripts/okf_lint.py`, currently exit 0 with two pre-existing warnings outside this bundle).

---

## 2. Premise audit

| # | Premise (as posed) | Status | Evidence |
|---|---|---|---|
| P1 | `cases/SystemDesignPatterns/` is an OKF bundle holding the sourced content | **verified** | `index.md`, `log.md`, `CircuitBreaker.md` present; declared in `.okf/binding.toml:31`; home listed in `docs/CONVENTIONS.md:77` |
| P2 | An `arch-*` family exists (7 skills), Cursor source → Claude projection | **verified** | `tooling/skill-sync/manifest.toml:15-18`; `docs/skills/README.md:15` |
| P3 | A "sibling family supplementing arch-*" already has a worked shape | **verified** | aws-ai: `manifest.toml:26-29`; router `.cursor/skills/aws-ai-lifecycle/SKILL.md:5` ("supplements the arch-* architect family"), `:23-25` (one shared binding `.aws-ai/binding.toml`), `:42` (design-time vs build-time modes); stage skills cite bundle content by line (`aws-ai-assess/SKILL.md:76-80` → `cases/aws-ai/ch01.md:128-148`); packaging workshop `tooling/aws-ai-skill/README.md` |
| P4 | Targets are Cursor, Claude **and Copilot** | **partly refuted → re-posed** | `.github/` holds only `workflows/`; the manifest has no Copilot projection. Copilot is net-new projection work with an unverified consumption format. Owner re-posed it as a later projection (C4). |
| P5 | "Give the patterns to the arch skills" | **verified as a gap** | `grep -i 'circuit\|bulkhead\|saga\|CQRS\|outbox\|idempoten\|backpressure\|rate limit'` across every `arch-*/SKILL.md` and `arch-*/references/*.md` returns **nothing**. The join seam is empty; aws-ai shows the join is a prose protocol (outputs flow to `arch-style`/`arch-decide`), not code. |
| P6 | The broader catalog is greenfield content | **refuted → re-posed** | Mechanism-level notes already exist: `cases/data-intensive-design/` (single/multi-leader/leaderless replication, hash/key-range sharding, rebalancing, request routing, quorums-and-fencing, event-sourcing-cqrs, distributed-transactions, timeouts-and-delays, conflict-resolution, durable-workflows, sharding-multitenancy, secondary-indexes …); `cases/aws/ch08.md` (CQRS, Saga, circuit breaker, retry with backoff, rate limiter, API gateway, service mesh, anticorruption layer, strangler fig, transactional outbox, sidecar, BFF, cellular architecture); `cases/ml-solutions-arch/ml-microservices-patterns.md`; `cases/claude-certification/enterprise-integration-production/poc-to-production.md` (retries / fallbacks / breakers for LLM apps). **Re-posed:** the new bundle owns the *pattern-card framing at the depth bar* and cross-links to these mechanism notes instead of re-deriving them. This changes which patterns to source first (§3). |
| P7 | The deepened Circuit breaker Concept is the depth bar | **verified** | Sections today: states, configuration, observability, tuning, retry+breaker, placement, worked calibration, trade-offs; external-research deepening in flight this session (four verified research tracks) |
| P8 | Gates: no test gate; skill-sync is the check gate | **verified** | `.sdd/binding.toml:14-15`; `skill_sync.py check` exit 0 |
| P9 | Skill evals have a precedent in this workspace | **verified** | `.cursor/skills/aws-ai-lifecycle/evals/evals.json`; `docs/research/aws-ai-eval-iteration-1/{benchmark.json,benchmark.md,feedback-iteration-1.json,iteration-2-plan.md}` |
| P10 | A "content → generated projection" precedent exists | **verified** | `manifest.toml:42-44` (`coding-rules-dist`: `tooling/coding-rules-skill/references` → `dist/.../references`); `manifest.toml:32-39` (sdd-roles kernel corpus → catalog projections) |
| P11 | No system-design / patterns skill exists yet | **verified** | `ls .cursor/skills .claude/skills` — arch-*, aws-ai-*, sdd-*, okf-curator, sdd-roles only |
| P12 | Skill frontmatter budgets (description length, trigger precision) constrain a broad catalog | **unverifiable here** | Needs a probe at spec time (the in-session `skill-creator` skill documents the limits and runs trigger evals). Directions that hinge on it are tagged `needs-probe`. |

No live system with an open defect is involved, so there is no blocking D0. Hygiene to do regardless of the pick: finish P01 (Circuit breaker) at the depth bar; keep the OKF lint and skill-sync gates green; add the family row to `docs/skills/README.md` when it lands.

---

## 3. Content-inventory delta → recommended catalog (owner asked for a recommendation, C1)

Rule from P6: **source first the patterns whose operational depth does not exist anywhere in the tree**, and wrap existing mechanism notes into pattern cards later. Wave 1 is the resilience-and-traffic cluster the Circuit breaker Concept already cross-references, plus the three integration patterns that every distributed write path needs.

| Id | Pattern (card scope) | Existing notes to link, not redo | Why this wave |
|---|---|---|---|
| P01 | Circuit breaker | — (this is the bar) | in flight |
| P02 | Timeouts & deadline propagation | `data-intensive-design/timeouts-and-delays.md`, `unreliable-networks.md` | the breaker's third knob; SRE deadline budgets; no operational note exists |
| P03 | Retry with backoff, jitter, and retry budgets | `aws/ch08.md` (paragraph), `data-intensive-design/nfr-references.md` [10][11][14] | retry storms are the top metastable-failure cause; token-bucket budgets absent from the tree |
| P04 | Bulkhead & isolation (thread/connection pools, cells) | `aws/ch08.md` cellular architecture | Hystrix-era isolation → cell-based; no note |
| P05 | Rate limiting (token/leaky bucket, sliding window; client vs server; per-tenant) | `aws/ch08.md` (paragraph) | pairs with 429 / Retry-After semantics in P01 |
| P06 | Load shedding & backpressure (priority tiers, adaptive concurrency) | `data-intensive-design/performance.md` (mitigation list), `nfr-references.md` [15][16] | the alternative-to-breaker family; Netflix/Uber/Google material verified this session |
| P07 | Idempotency & deduplication (idempotency keys, idempotent consumers) | `data-intensive-design/lost-updates.md`, `detecting-concurrent-writes.md` | prerequisite for safe retry + breaker + async fallback |
| P08 | Caching (cache-aside / read-through / write-behind, invalidation, stampede & thundering herd) | `data-intensive-design/home-timeline-case-study.md`, `replication-lag.md` | breaker fallbacks lean on caches; metastable cache-loss loop |
| P09 | Transactional outbox & CDC | `aws/ch08.md` (section), `data-intensive-design/event-driven-dataflow.md`, `replication-logs.md` | dual-write problem; no depth note |
| P10 | Saga (orchestration vs choreography, compensation) | `aws/ch08.md`, `ml-microservices-patterns.md`, `data-intensive-design/distributed-transactions.md`, `durable-workflows.md` | most-requested integration pattern; mechanism notes exist, operational card does not |
| P11 | Queues & pub/sub with DLQ, poison messages, ordering, competing consumers | `data-intensive-design/event-driven-dataflow.md` | Kafka pause/resume and DLQ facts verified this session |
| P12 | Health checks, heartbeats & graceful degradation (fail-open vs fail-closed; "avoid fallback") | `claude-certification/.../poc-to-production.md`, `responsible-ai/guardrails.md` | ALB fail-open, Envoy panic threshold, AWS fallback caution — all verified |

**Wave 2 (data & coordination — mostly cards over existing DDIA notes):** sharding & consistent hashing; replication & quorum reads/writes; leader election, locks, leases & fencing tokens; CQRS & event sourcing; API gateway / BFF; service discovery & mesh / sidecar; strangler fig & anticorruption layer; multi-region active-active & CDN/edge.
**Wave 3 (operational & delivery):** feature flags & kill switches; progressive delivery (canary / blue-green); chaos engineering & fault injection; distributed tracing & correlation IDs; autoscaling & capacity (Little's law); multi-tenancy isolation; search & secondary indexing.
**Out of scope for the family:** architecture styles (monolith vs microservices, hexagonal, event-driven as a *style*) — those stay in `arch-style`; security patterns — separate family if ever.

---

## 4. Independent axes (do not conflate)

| Axis | Choices | Note |
|---|---|---|
| A1 Family shape | stage family (router + diagnose/select/apply/verify) · **category family** (router + resilience / messaging / data / traffic / coordination) · single catalog skill | drives trigger precision and file count |
| A2 Content pipeline | hand-distilled cards citing Concepts (aws-ai style) · cards generated from Concepts (coding-rules-dist style) · machine-readable pattern IR → all projections | decide before card #2 to avoid rework |
| A3 Entry model | symptom-first ("p99 walks upstream") · name lookup ("saga") · quality-attribute lookup ("availability") | the router can offer all three; which is *primary* shapes SKILL.md |
| A4 Verification | trigger + answer evals (evals.json precedent) · OKF lint on Concepts · skill-sync check · executable pattern fitness checks | `test_gate` is `<none>`, so this is the family's only quality gate |
| A5 Join seams | none now · prose protocol later (arch-style options, arch-decide ADR candidates, arch-risk mitigations, arch-validate fitness functions, aws-ai-design tool-call resilience, sdd-spec verify tasks) | owner: independent first |
| A6 Naming | `sysdesign-*` · `sdp-*` · `patterns-*` | `sdp-*` is one keystroke from `sdd-*`; `patterns-*` collides with generic user-scope skills; `design` is already a session skill name |

---

## 5. Candidate directions

### High-probability (follow existing repo patterns)

**D1 — Stage family, aws-ai shape.** `<prefix>-lifecycle` router + `-diagnose` (symptom / NFR gap → candidate patterns and the metric that confirms the diagnosis) + `-select` (trade-off matrix → choice + ADR candidate) + `-apply` (checklist, knobs with defaults, calibration worksheet, anti-stacking rules) + `-verify` (metrics, alerts, fault-injection recipe). Shared `.<prefix>/binding.toml`, `FIRST_RUN.md`, `binding.schema.md`, instructions manual, manifest entry, packaging workshop. *Follows:* `.cursor/skills/aws-ai-*` (`manifest.toml:26-29`), `tooling/aws-ai-skill/`. *Trade-offs:* mirrors the workspace idiom exactly and the joins to `arch-*` stages are one-to-one; but the four stages share the same knowledge, so it multiplies SKILL.md files without distinct gates (aws-ai splits stages because build/deploy/validate have a credential gate — nothing comparable exists here). *What breaks if chosen:* every pattern card is referenced from four skills; drift between stage skills is the day-two cost. *Invariant stressed:* skill-sync drift guard (more files, same content).

**D2 — Category family.** `<prefix>-patterns` router + one skill per catalog category (`-resilience`, `-messaging`, `-data`, `-traffic`, `-coordination`), each carrying its cards under `references/` and embedding the same four-step protocol (diagnose → select → apply → verify) as sections of its SKILL.md. Wave 1 launches with router + `-resilience` + `-messaging` (+ `-data` for caching); later waves add skills, never restructure. *Follows:* per-skill `references/` in every `arch-*` skill; router + siblings with one shared binding (`aws-ai-lifecycle/SKILL.md:23-25`); manifest family entry (`manifest.toml:15-18`). *Trade-offs:* precise triggering (each description names its symptoms and patterns), each skill useful alone, joins can target one category; cost is a router that must route by symptom across categories. *What breaks:* a pattern that spans categories (idempotency, timeouts) needs one home and cross-links. *Invariant stressed:* constitution's "trade-offs always" — every card must carry a "use when / avoid when" table or the protocol collapses into a lookup.

**D3 — Single catalog skill.** One skill (`<prefix>-patterns`) whose SKILL.md is the router-by-symptom and protocol, with `references/catalog.md` (index table) and `references/patterns/<slug>.md` (cards) plus a `scripts/` card linter. *Follows:* `okf-curator-portable` (SKILL + references + scripts), `arch-characteristics/references/characteristics-catalog.md`. *Trade-offs:* fastest to ship and trivially portable; but one description must trigger on a 30-pattern surface (`needs-probe`, P12) and the file grows without a natural seam for joins. *What breaks:* trigger recall on symptom phrasing; a future split into categories is a rename of every reference. *Invariant stressed:* progressive disclosure (SKILL.md must stay short while the catalog grows).

**D4 — Cards generated from Concepts (content pipeline).** The bundle Concept stays the single source of truth at full depth; each gains a normalized card block (or sidecar frontmatter: intent, forces, knobs, metrics, anti-patterns, relations, sources); `tooling/<prefix>-skill/build_cards.py` extracts cards into the skill's `references/`; a skill-sync family pairs source → projections; OKF lint keeps Concepts sound. *Follows:* `coding-rules-dist` (`manifest.toml:42-44`), `make_bundle.py`'s frontmatter-driven generation. *Trade-offs:* zero drift between bundle and skill, one place to edit; cost is a generator and a card schema decided before the depth bar is fully learned. *What breaks:* hand-written nuance in cards (e.g., LLM-provider specifics) needs a place in the schema or it is lost. *Invariant stressed:* skill-sync's "source of truth per family" rule — the generated cards are a projection and must never be hand-edited.

### Exploratory (different abstraction / integration / shift)

**D5 — Symptom-first "design clinic" as the primary interface (demand-side lens).** The entry is not a catalog but a diagnostic protocol: elicit the failure signature or NFR gap and which metrics exist; map to a pattern *combination* (breaker + timeout + retry budget; cache + invalidation + stampede guard; outbox + idempotent consumer); refuse to recommend when the confirming metric is absent and prescribe the measurement first (the Circuit breaker Concept already teaches "check the raw error rate before tuning"). *Shift:* from "pattern encyclopedia" to "clinic" — stops agents pattern-dropping ("add a circuit breaker") without evidence, which is the class-level failure behind most misapplied patterns (Brooker's partial→total failure, Yandex's flapping breaker, Amazon's fallback caution — all sourced this session). *Trade-offs:* higher value per invocation; needs a symptom taxonomy and is harder to eval. *What breaks:* users who just want the saga card get a questionnaire — the router must offer a name-lookup bypass. *Invariant stressed:* constitution's "surface the trade-offs" — the clinic must show the rejected alternatives.

**D6 — Verify / fitness pack per pattern.** Each card ships executable-where-possible checks: config lints ("every outbound call has a timeout", "retry has jitter and a budget", "breaker emits state metrics"), architecture-test templates, fault-injection recipes (Toxiproxy toxics, Istio fault injection, WireMock faults), alert rules. *Shift:* knowledge → checks; joins `arch-validate` governance and `sdd-converge` gates later. *Trade-offs:* the highest leverage for coding agents; but language- and stack-specific, and unbounded. *What breaks:* scope — start with recipes and checklists, promote to code only where the workspace has a stack. *Invariant stressed:* `test_gate = <none>` — this direction would create the family's first real test surface.

**D7 — Pattern IR + multi-harness projections.** A YAML schema per pattern (intent, forces, mechanics, knobs + defaults, failure modes, metrics, relations, sources) generating markdown cards for Cursor/Claude now and Copilot later, optionally an MCP tool `find_pattern(symptom)` usable from any harness. *Follows:* sdd-roles kernel corpus → catalog projections (`manifest.toml:32-39`). *Trade-offs:* the only direction that makes the Copilot projection (C4) a build step instead of a rewrite; cost is schema design before the content exists and schema churn while the first wave is being learned. *What breaks:* over-engineering; a 12-pattern catalog does not yet justify an IR. *Invariant stressed:* single source of truth (IR vs Concept — pick one).

---

## 6. Leading direction — hypotheses (D2 + D5 spine + D4-lite)

Recommended composite: **D2** category family; **D5** as the protocol every SKILL.md embeds (with a name-lookup bypass); **D4-lite** — Concepts remain the source of truth and cards are hand-distilled against a fixed card template now, with the generator (D4 proper) and the IR (D7) deferred until ≥ 8 patterns exist. D1's stages become sections, not skills. D6 starts as recipes inside the "verify" section of every card.

| # | Hypothesis | Validation against the tree | Verdict |
|---|---|---|---|
| H1 | Registering the family is a manifest entry, no code | `skill_sync.py:56-69` reads generic `members`; `run_fix` (`:188-209`) projects each member directory; arch is registered exactly so (`manifest.toml:15-18`) | **validated** |
| H2 | Per-skill `references/` progressive disclosure is the house pattern | every `arch-*` skill carries `references/*.md`; `aws-ai-lifecycle/references/` holds six files incl. `research-2026.md` and `corpus-map.md` | **validated** |
| H3 | Cards may cite bundle Concepts by `file:line` yet must stand alone | `aws-ai-assess/SKILL.md:76-80` cites `cases/aws-ai/ch01.md:128-148`; `tooling/aws-ai-skill/README.md` ships only the skill dirs in the portable zip — so outside this workspace the Concept link is dead and the card is all the agent has | **validated (design constraint: cards self-sufficient, Concept link is a bonus)** |
| H4 | The family's quality gate is an eval set, not a test suite | `.sdd/binding.toml:15` (`test_gate = <none>`); precedent `.cursor/skills/aws-ai-lifecycle/evals/evals.json` and `docs/research/aws-ai-eval-iteration-1/benchmark.json`; in-session `skill-creator` runs trigger/answer evals | **validated; format compatibility `needs-probe`** |
| H5 | A category split triggers more precisely than one broad description | depends on frontmatter budgets (P12) | **`needs-probe`** — build router + one category skill, run a trigger eval before adding the rest |
| H6 | The family works independently without a workspace binding for wave 1 | aws-ai needs region / IaC / credentials (`.aws-ai/binding.toml`); a patterns family needs only optional homes (ADR series, metrics stack) — `FIRST_RUN.md` can be optional | **plausible; decide at spec** |
| H7 | Content velocity is about one pattern per research cycle at the depth bar | measured on P01 this session: four parallel research agents, 18–24 min wall-clock each, ~1.16 M subagent tokens total, synthesis in progress | **validated for research; synthesis cost still to measure** |

**Feasibility adjectives checked:** "just a manifest entry" holds (H1); "portable" holds only if cards are self-sufficient (H3); "these categories are parallel" holds for research but not for the card template — the template must be frozen after P01 and before P02 (§7).

---

## 7. Dependency structure

- **Sequenced:** card template (frozen from the P01 depth bar) → wave-1 Concepts → cards → `-resilience` + `-messaging` skills → router → manifest + `docs/skills/README.md` row + instructions manual → evals → (later) joins → (later) Copilot projection.
- **Independent-parallel:** research per pattern (the P01 four-track split is reusable as a workflow per pattern or per wave); category skills after the template is fixed.
- **Do regardless of the pick:** finish P01; freeze the card template; keep OKF lint and skill-sync green; add the family with router + `-resilience` as soon as three cards exist (thin slice) so evals can start early.
- **Deferred behind volume:** D4 generator and D7 IR after ≥ 8 patterns; D6 executable checks after the workspace names a stack.
- **Cost axes:** engineering time is small (skills are markdown + one manifest entry); **calendar time is the research and synthesis per pattern** — wave 1 is twelve P01-sized cycles.
- **Ask-first items (need an ADR at spec time):** a new skill family and a new manifest family are "new abstraction / new node" class changes; the naming prefix is a decision to record.

---

## 8. Human gate

Pick by id; a bare "yes" is not multi-option consent.

- **G1 Direction.** `G1-a` D2 + D5 + D4-lite composite (recommended) · `G1-b` D1 stage family · `G1-c` D3 single skill · `G1-d` other (say which mix).
- **G2 Naming prefix.** `G2-a` `sysdesign-*` with router `sysdesign-patterns` (recommended: unambiguous, no collision) · `G2-b` `sdp-*` · `G2-c` `patterns-*` · `G2-d` other.
- **G3 Catalog wave 1.** `G3-a` P01–P12 as listed in §3 · `G3-b` P01–P12 minus these ids: … · `G3-c` add these: … (wave 2/3 lists are proposals, not commitments).
- **G4 Content pipeline now.** `G4-a` hand-distilled cards against a frozen template, generator later (recommended) · `G4-b` build the generator first (D4) · `G4-c` IR first (D7).
- **G5 Quality gate.** `G5-a` adopt the `evals.json` precedent: a trigger + answer eval set per category skill, started at the thin slice (recommended, do-regardless) · `G5-b` defer evals until wave 1 is complete.
- **G6 Joins.** `G6-a` confirm: no arch-*/aws-ai/sdd joins in this iteration; only leave the seams (router boundary statements, ADR-candidate output shape) · `G6-b` include one join now (say which).

Advance → **sdd-spec** with the chosen ids + validated hypotheses H1–H4, carrying H5 and the evals-format probe as spec-time tasks.
