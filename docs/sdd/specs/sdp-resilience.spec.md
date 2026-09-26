# Spec: `sdp-*` system-design-patterns family — wave 1 (`sdp-lifecycle` router + `sdp-resilience`)

**Status:** **DRAFT — awaiting SPEC-OK (owner gate).** Stage 2 of SDD. No plan,
no tasks, no implementation until this is signed off.
**Direction:** Stage-1 (sdd-brainstorm) gate **CLOSED 2026-09-13**. Accepted slate
`S1 · T2b · E1+E2+E4 · P1→P2 (Z-spec) · V1+V3+V5 · N-b (sdp-*) · J1`.
Bridge: [system-design-patterns-skill-spec-handover.md](../../research/sysdesign/system-design-patterns-skill-spec-handover.md);
live gate + §13 consumer dimension: […-mece-handover.md](../../research/sysdesign/system-design-patterns-skill-mece-handover.md) §8/§13/§14.
**Change class:** **⚠️ Ask-first — new skill family + new skill-sync manifest node**
("new abstraction / new node"). Raises **ADR** `docs/architecture/adrs/tooling/sdp/0001-*`
(new seam) + a `docs/architecture/log.md` entry. **Ask-first source note:** this
trigger comes from the **SDD ask-first convention** (`sdd-spec/SKILL.md:37-38`,
`sdd-brainstorm/SKILL.md:115-116`) **and the handover §2 ruling** (`spec-handover:45-49`)
— **not** from the bound constitution, which contains no ask-first list (see the
Clarify note on C-const below). Contrast the no-ADR carve-out used for pure
doc/skill deliverables (`platform-design-atlas.spec.md:9`): the `sdp-*` family is
deliberately outside it because it adds an abstraction and a manifest node.

## Clarify decisions (locked 2026-09-13)

| ID | Question | Decision |
|----|----------|----------|
| **C1** | Router skill name | **`sdp-lifecycle`** — house router convention (`arch-lifecycle`/`aws-ai-lifecycle`/`sdd-lifecycle`), chosen over the working name `sdp-patterns`. Owner call at the framing gate. |
| **C2** | Portable zip in wave-1 (the deferred **Z-spec**) | **Deferred** — no zip artifact ships in wave-1. **But AC-4 mandates card self-containment now** (the Concept link is a non-load-bearing "See also"), so a later zip is a packaging step, not a rewrite. |
| **C3** | Wave-1 done-boundary | **All 7 owned resilience cards authored in wave-1** (C1/C2/C7/C8/C9/C10/C11). The template is still **frozen after the first three** (C1/C2/C7) per AC-11, then applied to the remaining four. |
| **C4** | `sdp-*` ↔ `sdd-*` disambiguation | Spec **mandate** (FR-11 / AC-5): each skill `description` carries a negative boundary that excludes the SDD lifecycle; the one-character prefix distance must not cause mis-invocation. |
| **C5** | ADR home | **New seam** `docs/architecture/adrs/tooling/sdp/` (parallel to the existing `tooling/sdd-roles/` seam). Neither `adr_home` (`application/mobile-test-automation/`) nor `adr_home_sdd_roles` fits a skills-family change. |
| **C6** | Eval file format | **Mirror** `.cursor/skills/aws-ai-lifecycle/evals/evals.json` (`skill_name` · `note` · `evals[]{id,name,target_skill,prompt,expected_output,expectations[]}`; `with_skill` run starts at the router and follows routing, baseline answers from general knowledge). |
| **C7** | `.sdp/binding.toml`? | **No binding file in wave-1.** The family is a content clinic, not an SDD/arch workflow family — it has no spec/plan/ADR homes or gates of its own. Skills reference the constitution by its repo path directly (`.cursor/rules/architecture-principles.mdc`, repo-root-relative, valid from both projection surfaces). Revisit only if/when the portable zip (C2) ships. Least machinery (A1). |
| **C-const** | The `{{constitution}}` "8 invariants" | **Recorded discrepancy (not a choice).** The bound constitution `.cursor/rules/architecture-principles.mdc` is a 29-line `alwaysApply` rule with **no numbered invariant list and no ask-first list**. It **does** impose the 5-part card contract (`:24` definition+motivation+example/diagram; `:27` trade-offs on every decision; `:28` cite well-known sources). This spec cites that real contract (AC-17) and does **not** invoke a nonexistent "8 invariants". Flagged so Stage-4 Analyze does not chase it. |

**Open questions:** none blocking. (Split-vs-single ADR and the V5-lint host location are
recorded as plan-time sub-decisions under FR-9/FR-13, with recommendations.)

---

## Problem

Coding agents have a mounted architect discipline (`arch-*`: characteristics →
components → style → decide → risk → validate) but **no skill that reasons about
tactical, intra-service system-design patterns** — circuit breakers, retry
budgets, timeouts/deadlines, bulkheads, idempotency, load shedding, graceful
degradation. The gap is verified: a grep of `arch-*` SKILL/reference bodies for
`circuit|bulkhead|saga|outbox|idempoten|rate limit` returns no hits (mece Hs3).

The knowledge exists as 47 canonical Concepts in the `cases/SystemDesignPatterns/`
bundle, but it is **not skill-addressable and not self-contained**: a consumer
cannot cite a pattern's trade-off surface as a unit. The latent demand is already
visible — `arch-risk` hand-writes "backpressure queue → priority channel"
mitigations with no card to cite (`arch-risk/SKILL.md:62`).

Wave 1 stands up the family and its first category so that an agent with **only
this family** can run the tactical loop **diagnose → select → apply knobs →
verify** for resilience/availability symptoms, hand off out-of-scope *style*
questions to `arch-style`, and leave clean seams for later consumers.

---

## Scope — wave 1

**In scope (this spec governs; implementation is Stage 3):**

1. **Family router `sdp-lifecycle`** — births the `sdp-*` family; routes a symptom
   to the right category skill; carries the E2 (name) + E4 (code/diff) bypasses
   and the `arch-style` handoff. Wave-1 authors **only** `sdp-resilience`; the
   other four categories (`-messaging`/`-data`/`-traffic`/`-coordination`) are
   **named as reserved**, not authored.
2. **Category skill `sdp-resilience`** — **owns 7 cards**: CircuitBreaker (**C1**),
   RetryBackoff (**C2**), TimeoutsDeadlines (**C7**), Bulkhead (**C8**),
   Idempotency (**C9**), LoadShedding (**C10**), GracefulDegradation (**C11**).
   **Cross-links, does not own**: FailoverHealth (**C3**), CachingStrategies
   (**B3**), OutboxCdc (**B7**).
3. **Entry** — E1 clinic/symptom primary; E2 name-lookup and E4 code/diff-in-hand
   as bypasses; trade-offs surfaced **before** any recommendation.
4. **arch-style handoff** — the S1 boundary made operational (FR-4).
5. **One frozen card template** (P1) — derived from the C1/C2/C7 depth bar,
   **frozen after the first three distillations** (AC-11), adds a stable `id`
   field, then applied to the remaining four owned cards.
6. **Quality** — **V1** family eval set (trigger + answer, including the T2b
   trigger killing-test), **V3** fitness recipes in each card, **V5**
   card-template lint.
7. **Manifest** — a new `[[family]] id = "sdp"` node in
   `tooling/skill-sync/manifest.toml`; `check_gate` stays exit 0.
8. **J1 seams** — the six consumer output shapes reserved as template anchors;
   **none built**. First future join = `arch-risk`.

**Out of scope / deferred:**

- The other four category skills (`-messaging`/`-data`/`-traffic`/`-coordination`)
  — later waves.
- **P2** generator (fast-follow, once the template is proven on 7 real cards);
  **P3** pattern IR (deferred-but-alive: consumer/MCP/Copilot drivers).
- **The portable zip artifact** (C2) — deferred; self-containment (AC-4) is built
  in now so the zip is cheap later.
- **Any built join** (J1) — seams reserved only.
- **Style ownership** — S1: the 13 style Concepts stay in the bundle and feed
  `arch-style`; this family never owns or re-scores them.
- **`.sdp/binding.toml`** (C7) and NFR entry E3.

---

## The card template (shape derived from the C1/C2/C7 depth bar — normative; **frozen at implement-time per AC-11, not here**)

Per the handover ("freeze ONE template **after** the first three distillations,
not before"), this section fixes the **shape** the freeze must take, derived from
the three gold Concepts (`CircuitBreaker.md`, `RetryBackoff.md`,
`TimeoutsDeadlines.md`). The intersection is 11 sections; the mechanics band is
pattern-specific.

**Frontmatter:** existing `type` / `title` / `description` / `tags` **plus a new
`id` field** carrying the catalog id (e.g. `id: C1`) — the addressable handle
§13 requires and the source Concepts lack.

**Body order:**

1. `# <Pattern>` (H1) + a `See also:` line linking the bundle Concept as a
   **non-load-bearing** reference (AC-4).
2. **Intro** = definition + motivation + quality-attributes/cost (no heading;
   satisfies the constitution's definition+motivation clause).
3. `## Lineage and vocabulary` *(intersection)*
4. `## <Mechanics …>` — **variable**, 1–N pattern-specific sections (e.g. CB: the
   three states / what counts as a failure / half-open probe; RB: what is worth
   retrying / backoff & jitter / retry budgets / one-layer rule; TD: five timers /
   remaining-time budgets / cancellation).
5. `## Configuration & verified defaults` — **canonical name** for the
   config/knobs band (unifies CB's "Configuration"+"Library defaults", RB's
   "Library defaults", TD's "Defaults are not a policy"+"OS floor").
6. `## Where it lives` *(intersection)*
7. `## Observability` *(intersection — feeds the V3 fitness recipe and the
   arch-validate consumer shape)*
8. `## Tuning` *(intersection)*
9. `## Alternatives that beat a <pattern>` *(intersection — **carries
   when-not-to-use**, which no card gives a dedicated heading)*
10. `## Worked calibration — <scenario>` *(intersection — the worked example)*
11. `## Testing and operating` *(intersection)*
12. `## Failure modes` *(intersection — feeds the sdd-brainstorm what-breaks
    consumer shape)*
13. `## <Pattern> around LLM provider APIs` *(intersection — feeds the
    aws-ai-design tool-call-resilience consumer shape)*
14. `## Trade-offs` *(intersection — **required**; its absence fails V5)*
15. `## Sources` *(intersection — **required**; its absence fails V5)*

**Consumer-seam anchors (J1, reserved — FR-12):** each of the six shapes is a
projection of sections above, not a new section — mitigation → Failure modes +
Configuration + Trade-offs; fitness-function → Observability; ADR-option →
Trade-offs + Alternatives; verify-task → Configuration + Tuning; what-breaks →
Failure modes + Alternatives; tool-call-resilience → the LLM-provider section.

---

## Functional requirements

- **FR-1 — Router `sdp-lifecycle`.** A router `SKILL.md` (frontmatter = the three
  keys only: `name`, `type: skill`, `description`). The `description` routes
  symptom → category with a `Routes to: sdp-resilience (breakers/retries/timeouts/
  bulkhead/idempotency/load-shedding/degradation), sdp-messaging (…reserved…), …`
  enumeration, carries E2/E4 bypass triggers, and a negative boundary naming both
  `arch-style` (style selection) and `sdd-*` (the lifecycle). Body: clinic loop →
  category map → routing rules → **`## Handoff with the arch-* family`** →
  constraints. The four un-authored categories appear as reserved rows.
- **FR-2 — Skill `sdp-resilience`.** A member `SKILL.md` (three-key frontmatter).
  Owns the 7 cards; cross-links (does not own) C3/B3/B7. Body: `## Agent work`
  (diagnose symptom → confirm the metric exists → select the combination → apply
  knobs → verify) → `## Human gate` → `## Constraints`. The `description` carries
  resilience trigger utterances and the arch-style / sdd negative boundary.
- **FR-3 — Entry E1 + E2 + E4.** Clinic/symptom primary; pattern-name lookup and
  code/diff-in-hand as bypasses. In all three modes the skill **surfaces
  trade-offs before recommending** and, for breaker/retry advice, prompts to
  confirm the raw failure/error-rate metric first (CircuitBreaker doctrine).
- **FR-4 — arch-style handoff (S1 boundary operational).** When a symptom is an
  architecture-style / quantum / topology question (any `arch-style` trigger
  utterance: "monolith or distributed", "how many quanta", "which architecture
  style", "sync or async between services"), the skill **does not answer and does
  not run arch-style's four determinations**; it routes to `arch-style`, and where
  a style fact is needed it **cites `arch-style/references/style-selection.md` as
  FACT** (the discipline the style E-cards already follow, e.g. `Monolith.md:61`).
- **FR-5 — Frozen card template (P1).** Exactly one operational template (shape
  above), frozen from the first three distilled cards (C1/C2/C7) and then applied
  unchanged to C8/C9/C10/C11. The template adds the `id` frontmatter field.
- **FR-6 — §13 card invariant.** Every card is (a) **addressable** by a stable
  catalog id in frontmatter, (b) **self-contained** — the Concept link is not
  load-bearing, and (c) **carries an explicit trade-off surface** (`## Trade-offs`
  + when-not-to-use via `## Alternatives…` + `## Sources`).
- **FR-7 — V1 family eval set** at `sdp-lifecycle/evals/evals.json` (C6 format),
  covering the required cases enumerated below, **including the T2b trigger
  killing-test** (does a resilience symptom cluster in the resilience bucket or
  hop buckets?).
- **FR-8 — V3 fitness recipes.** Each card expresses verification as a fitness
  **recipe** (metric → assertion, in prose), **not** executable test code — this
  repo names no runnable app stack (Hq2). Fed by the card's Observability/Tuning.
- **FR-9 — V5 card-template lint.** A deterministic, stdlib-Python, read-only lint
  (precedent: `okf_lint.py`, `skill_sync.py`) that asserts every
  `sdp-*/references/*.md` card conforms to the frozen template. *Plan-time
  sub-decision:* host at `tooling/sdp-card-lint/` (recommended, parallel to
  `tooling/skill-sync/`) vs. inside the skill dir.
- **FR-10 — Manifest family node.** Add `[[family]] id = "sdp"`,
  `source = ".cursor/skills"`, `members = ["sdp-lifecycle", "sdp-resilience"]`,
  `projections = [".claude/skills"]` to `tooling/skill-sync/manifest.toml`
  (same shape as the `arch`/`aws-ai` families). `check_gate` stays exit 0.
- **FR-11 — `sdp` ↔ `sdd` disambiguation.** Router and member `description`s must
  not mis-fire on SDD-lifecycle utterances; each carries an explicit "Not for the
  SDD lifecycle (sdd-*)" boundary (C4).
- **FR-12 — J1 consumer seams (reserved, none built).** The template provides the
  six consumer-shape anchors as projections of existing sections; **no live join
  is built** this wave. First future join = `arch-risk`.
- **FR-13 — ADR + decision log.** Raise ADR `docs/architecture/adrs/tooling/sdp/
  0001-…` (Proposed) for the new family + manifest node + projection model, and a
  `docs/architecture/log.md` entry. *Plan-time sub-decision:* one ADR covering
  family+node+topology (recommended, least machinery) vs. splitting the T2b
  topology bet into its own ADR.

---

## Acceptance criteria (EARS — **failure paths first**)

Each collapses to one testable claim; mapping to FRs in the Traceability table.

**Failure / boundary (IF-THEN):**

- **AC-1** IF a presented symptom is an architecture-style / quantum / topology
  question THEN `sdp-resilience` hands off to `arch-style`, does **not** run the
  four determinations, and does **not** offer a tactical pattern as the answer.
  *Amendment 2026-09-14 (owner decision at benchmark iteration 2; `log.md`):*
  "hands off" means the agent **names or loads `arch-style`** and does not answer
  the style question *as the sdp agent*; once handed off, `arch-style` may run in
  the same session (chain-in — the owner kept this behaviour). V1 eval 4 measures
  exactly that: answering the style question from general knowledge without
  naming/loading `arch-style` fails, proceeding via `arch-style`'s method passes.
- **AC-2** IF the agent is asked to recommend a pattern THEN it surfaces that
  pattern's trade-offs (and, for breaker/retry, prompts to confirm the raw
  failure-rate metric) **before** the recommendation — never a bare pattern-drop.
- **AC-3** IF a card lacks the `id` field, OR a `## Trade-offs` section, OR a
  `## Sources` section THEN the V5 lint exits non-zero and names the card and the
  missing element.
- **AC-4** IF a card's mechanism cannot be understood without following its
  Concept link THEN it violates the self-containment invariant — the card must
  carry the mechanism itself; the link is a `See also` only.
- **AC-5** IF an utterance targets the SDD lifecycle ("spec this", "run the sdd
  lifecycle", "replan the tasks") THEN neither `sdp-lifecycle` nor `sdp-resilience`
  claims it.
- **AC-6** IF a symptom names a pattern the skill cross-links but does not own
  (FailoverHealth/CachingStrategies/OutboxCdc) THEN the skill cross-links to it
  rather than silently owning or dropping it.
- **AC-7** IF a projected `sdp-*` file drifts from its `.cursor/skills` source
  THEN `check_gate` exits 2 (the new family is under the drift guard).

**Event (WHEN):**

- **AC-8 (T2b killing-test)** WHEN a V1 trigger eval presents a resilience symptom
  ("p99 is walking upstream and taking the pool with it", "this client has no
  timeout", "retries are hammering a sick dependency") THEN it routes to
  `sdp-resilience` AND every card it pulls sits **within** the resilience bucket;
  the eval records in-bucket vs. bucket-hop so the T2b bet is measured, not assumed.
- **AC-9** WHEN a user names a pattern ("circuit breaker", "bulkhead") THEN the
  skill returns that pattern's card (E2 bypass).
- **AC-10** WHEN a user presents code/diff exhibiting a missing or mis-set pattern
  ("this HTTP client sets no timeout") THEN the skill identifies the pattern and
  surfaces its card (E4 bypass).
- **AC-11** WHEN the first three cards (C1/C2/C7) are distilled THEN the template
  is frozen from them AND the remaining four owned cards (C8/C9/C10/C11) conform to
  the frozen template with no further template edits.
- **AC-12** WHEN this spec is approved THEN the ADR(s) under
  `docs/architecture/adrs/tooling/sdp/` exist in **Proposed** status and a
  `docs/architecture/log.md` entry is added.

**State / feature (WHERE):**

- **AC-13** WHERE the six consumer output shapes are concerned, the card template
  provides an addressable anchor for each as a projection of existing sections AND
  none is built as a live join this wave (J1).
- **AC-14** WHERE a card specifies verification, it does so as a fitness **recipe**
  (metric → assertion in prose), not executable test code.

**Ubiquitous:**

- **AC-15** The router and member each carry **only** the three frontmatter keys
  (`name`, `type: skill`, `description`) and encode all triggering and negative
  boundaries in the `description` prose (matching every sibling skill; no
  `triggers`/`tools`/`when-to-use` fields exist to lean on).
- **AC-16** `check_gate` (`python3 tooling/skill-sync/skill_sync.py check`) exits 0
  and OKF lint exits 0 on the wave-1 tree.
- **AC-17** Every card satisfies the constitution card contract
  (`architecture-principles.mdc:24,27,28`): definition, motivation, an
  example-or-diagram, explicit trade-offs on every decision, and cited well-known
  sources.

---

## V1 eval set — required cases (FR-7; authored in Stage 3)

Mirrors `aws-ai-lifecycle/evals/evals.json`. The `with_skill` run starts at
`sdp-lifecycle` and follows routing; the baseline answers from general knowledge.
Minimum cases:

1. **trigger / in-bucket (T2b):** a resilience symptom → routes to
   `sdp-resilience`; expectations assert it does **not** route to a non-resilience
   bucket and the cards cited are all resilience cards (AC-8).
2. **answer / trade-offs-first:** "should I add a circuit breaker here?" →
   surfaces the raw-error-rate check and trade-offs before recommending (AC-2),
   cites C1.
3. **E2 name lookup:** "explain the bulkhead pattern" → returns C8 (AC-9).
4. **E4 code/diff:** a snippet with a timeout-less client → names TimeoutsDeadlines
   (C7) and the fix (AC-10).
5. **arch-style handoff:** "should this be a monolith or microservices?" → hands
   off to `arch-style`, does not recommend a tactical pattern (AC-1).
6. **sdp↔sdd disambiguation:** "run the sdd lifecycle / spec this feature" → not
   claimed by `sdp-*` (AC-5).
7. **router:** "my service keeps falling over under load, where do I start?" →
   routes into the clinic loop, not to code or a single named pattern.

*Status 2026-09-14:* all seven cases are live in `sdp-lifecycle/evals/evals.json`
(case 3 is eval 7 `bulkhead-name-lookup-e2`, added once C8 existed — wave 1 had
temporarily pointed the name-lookup case at C1). Tightened after benchmark
iteration 2 (owner decision **c1**): grounding expectations require the card to
be **named by id** in the answer — which is why `sdp-resilience` and
`sdp-lifecycle` now carry a "name the card by id" constraint — and each
expectation is tagged **GUARD** (pins an AC; expected to pass in both benchmark
configurations) or left as a discriminator (measures the clinic's discipline).
*Second tightening 2026-09-14 (owner decision N1, after benchmark iteration 3, no re-run):*
case 1's in-bucket guard now lists all seven owned ids and tests *necessity* of a
sibling-bucket card (C3/B3/B7 allowed as onward pointers); case 4's timeout fix
passes a labelled placeholder with the derivation stated; case 5 requires
`arch-style` to be **named** in the answer (loading is invisible to a reader).

---

## Consumer seams (J1 — reserved, none built)

| Consumer | Human-in-loop gate | Shape reserved | Fed by card section |
|---|---|---|---|
| **arch-risk** *(first future join)* | mitigation accept/reject | pattern-as-mitigation + cost/knobs | Failure modes · Configuration · Trade-offs |
| arch-validate | wiring fitness functions | metrics → checklist | Observability |
| arch-decide | the ADR | option + trade-off | Trade-offs · Alternatives |
| sdd-spec | verify / acceptance list | knobs/defaults → assertions | Configuration · Tuning |
| sdd-brainstorm | the direction pick | what-breaks on a direction | Failure modes · Alternatives |
| aws-ai-design | agent tool-call design | retry/timeout/breaker/idempotency for LLM calls | LLM-provider section |

---

## Verification / gates

- **check_gate:** `python3 tooling/skill-sync/skill_sync.py check` → exit 0
  (family added to the manifest and byte-clean across projections).
- **OKF lint:** `python .cursor/skills/okf-curator/scripts/okf_lint.py` → exit 0
  (2 known non-bundle warnings; the bundle is unaffected — cards are skill
  reference files, not new Concepts).
- **V5 card lint:** every `sdp-*/references/*.md` conforms to the frozen template
  (FR-9 / AC-3).
- **V1 evals:** the required cases above pass on the `with_skill` run.
- **test_gate:** `<none>` — the V1 eval set is this family's behavioral quality gate.

---

## Traceability (AC ↔ FR)

| FR | ACs |
|---|---|
| FR-1 router | AC-15, AC-16 |
| FR-2 skill / membership | AC-6, AC-15 |
| FR-3 entry E1/E2/E4 | AC-2, AC-9, AC-10 |
| FR-4 arch-style handoff | AC-1 |
| FR-5 frozen template | AC-11 |
| FR-6 §13 invariant | AC-3, AC-4, AC-17 |
| FR-7 V1 evals | AC-8, AC-9, AC-10 |
| FR-8 V3 recipes | AC-14 |
| FR-9 V5 lint | AC-3 |
| FR-10 manifest node | AC-7, AC-16 |
| FR-11 sdp↔sdd | AC-5 |
| FR-12 J1 seams | AC-13 |
| FR-13 ADR + log | AC-12 |

---

## ADR pointer

`docs/architecture/adrs/tooling/sdp/0001-stand-up-the-sdp-tactical-patterns-skill-family.md`
(Proposed, drafted with this spec) — records the new family, its manifest node,
the `.cursor → .claude` projection model, and the T2b job-shaped topology bet with
the V1 trigger eval (AC-8) named as its killing-test in Compliance.
