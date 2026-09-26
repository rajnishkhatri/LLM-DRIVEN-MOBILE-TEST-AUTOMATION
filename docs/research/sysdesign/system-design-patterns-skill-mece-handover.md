---
type: analysis
title: 'Sysdesign skill family — MECE / pyramid / hypothesis handover'
description: >-
  Handover for an sdd-brainstorm agent: corrected MECE cuts, Minto pyramid,
  and an honest hypothesis tree for the system-design-patterns skill family.
  Supersedes the §9 G-gate in the sibling brainstorm as the live decision
  structure. Does not close the gate and does not write a spec.
tags: [sdd, brainstorm, system-design-patterns, mece, handover, skills]
---

# Sysdesign skill family — MECE / pyramid / hypothesis handover

**For:** the next `sdd-brainstorm` agent (and the human at the Stage 1 gate).
**Date:** 2026-09-13.
**Stage:** still SDD Stage 1. No direction has been accepted. Do **not** start `sdd-spec`.
**Sibling record:** [system-design-patterns-skill-brainstorm.md](system-design-patterns-skill-brainstorm.md) (premise audit, D1–D7, original §8 gate, §9 refresh). This file **supersedes §9 as the live gate**. §5–§9 stay as history.
**Catalog:** [system-design-patterns-catalog.md](system-design-patterns-catalog.md).
**Constitution:** `.cursor/rules/architecture-principles.mdc`.
**Binding:** `.sdd/binding.toml` — `test_gate = <none>`; `check_gate` = `python3 tooling/skill-sync/skill_sync.py check`.
**Amended:** 2026-09-13 — §12 amendments adopted by the owner after adversarial review; §8 below is the amended live gate.

> Read this file first. Re-verify any `file:line` you intend to quote. Do not regenerate six new directions that remix D1–D7. The failure mode to avoid is treating D1–D7 as a MECE set, or treating §9’s “D2 = groups A/B/C/D” as the same idea as original D2.

---

## 1. How to use this

1. Skim §2 (closed) and §3 (problem). Do not re-open closed owner calls unless the human withdraws them.
2. The **first live question** is **Q1 (scope: S1 vs S3)**, then **Q2 (topology, incl. `T2-defer`)** — order amended by §12. Pose these before G0–G6 from the old brainstorm.
3. If the human answers Q1–Q5 by id, record the ids in the brainstorm (new §11 or a status line) and advance to **sdd-spec** with those ids + the validated hypotheses in §7.
4. A bare “yes” / “go with the recommendation” is not consent. Require ids.
5. Do not write skills, a manifest family, cards, or a spec in the brainstorm chat.

---

## 2. Do not re-litigate (closed or obsolete)

| Id | Decision | Evidence / why closed |
|---|---|---|
| C1 | Broader catalog, owner-confirmed | Catalog of record; 43 topics all ✅ |
| C2 | [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md) / [RetryBackoff.md](../../../cases/SystemDesignPatterns/RetryBackoff.md) are the operational depth bar | Gold-standard Concepts |
| C3 | **New sibling family**, independent first, joinable later | Owner; not a patch to `arch-*` |
| C4 | Copilot projection deferred | Manifest has no Copilot target |
| C5 | Circuit-breaker deepening — done | Concept + research note exist |
| R4 | Style Concepts live in the **bundle** | 13 E-cards in `cases/SystemDesignPatterns/` |
| R5 | Catalog research closed | 41 catalog-wave notes under `docs/research/sysdesign/` |
| G3 | Wave planning | **Moot** — every topic is a Concept |
| P11 | No `sysdesign-*` skill exists yet | `ls .cursor/skills` — arch / aws-ai / sdd / okf only |
| W1 / W2 | “Just read Concepts” or “patch `arch-*`” as the *home* | Rejected by C3. `arch-*` still has no circuit/bulkhead/saga/outbox/idempotency/rate-limit hits (re-grep if you cite this). |

**Do-regardless hygiene** (not a direction pick): keep OKF lint and skill-sync green; when a family lands, add the `docs/skills/README.md` row and a manifest `[[family]]`.

---

## 3. Restated problem (from the brainstorm, still in force)

Coding agents have no skill here that reasons about **tactical** system-design patterns (breaker, retry budgets, bulkheads, cache, outbox, saga, …) with the discipline `arch-*` brings to characteristics / components / style / decide / risk / validate.

The family must:

1. **Work on its own** — an agent with *only this family* can diagnose → pick → apply knobs → verify. Independence means the **tactical loop**, not “all of system design.”
2. Later plug into `arch-*` / `aws-ai-*` / `sdd-*` without redesign.
3. Project to Cursor + Claude via `tooling/skill-sync/` now; Copilot later (C4).

**Explicitly not the problem** (brainstorm §0): choosing architecture *styles* (`arch-style`); curating the bundle (`okf-curator`); runtime tooling.

**Tension the last analysis buried:** R4 put 13 style Concepts in the same bundle; the catalog title calls that bundle the catalog “for the future skill family.” The *skill problem* still excludes styles. **Q2 (scope)** is “does the skill match §0 or the bundle?”, not “are styles important?”

**Measured content (2026-09-13, file-counted):** 43 catalog topics; **47 canonical Concepts** (34 tactical A/B/C/D + 13 style E) + 3 superseded first-pass cards (`WebSockets.md`, `ApiVersioning.md`, `Failover.md`). Tactical split: A6 + B12 + C11 + D5 = 34. Five per-group HTML explainers under `docs/architecture/explainers/system-design-patterns/`.

---

## 4. Why D1–D7 are not MECE

MECE (Minto / McKinsey; logic older) = buckets that **do not overlap** and **do not leave a hole**. D1–D7 sit on different questions:

| Direction | Actual question | Same-axis rivals |
|---|---|---|
| D1 stage family | How skills are cut (topology) | D2, D3 |
| D2 category family | Topology | D1, D3 |
| D3 single skill | Topology | D1, D2 |
| D4 generator | How cards are produced (pipeline) | P0, D4-lite, D7 |
| D5 clinic | How the agent starts (entry) | name-first, code-first |
| D6 fitness pack | How we prove it (quality — a **menu**, not XOR) | evals, lint |
| D7 pattern IR | Pipeline (stricter D4) + extra projections | nested under D4, not a sibling |

That is why the old lead had to be a **composite**. “Pick D2 or D5” is a false choice.

**Further trap (this is the load-bearing one):** original D2 was **job-shaped** (`-resilience`, `-messaging`, `-data`, `-traffic`, `-coordination`). Brainstorm §9 silently retargeted D2 to **catalog groups A/B/C/D**. Those are not the same cut. §9’s “D2 is strengthened because folders exist” proves *filing convenience*, not *trigger fitness*.

---

## 5. Pyramid (Minto)

The point above must be a summary of the points below. One idea per level.

```
The Stage-1 decision is: ship an independent tactical skill family,
cut the first skill by AGENT JOB (not by catalog folder),
entered as a clinic (name + code as bypasses),
reading a thin hand slice (Concepts or 3 cards),
proved by evals.

    ├── Independence = tactical loop only. Styles stay in the bundle
    │   and in arch-style. Skill scope follows brainstorm §0, not
    │   “the bundle is 47 files.”
    │
    ├── D1–D7 mixed four questions. Pick one option per question;
    │   do not pick a letter from the old list.
    │
    ├── Clinic wants COMBINATIONS (breaker + timeout + retry budget).
    │   Catalog groups A–D want HOMES. Whether they fight is UNTESTED
    │   (Ht2b is PLAUSIBLE; the worked C-only example cannot show it —
    │   the §7 killing tests decide; §12).
    │   Original D2 (job-shaped) matches the clinic; §9 D2 (A–D) matches
    │   index.md and the five explainers.
    │
    ├── Four stage SKILL.md files (D1) share one body of knowledge and
    │   have no per-stage gate here (unlike aws-ai credentials). Keep
    │   diagnose→select→apply→verify as SECTIONS, not as four skills.
    │
    └── test_gate is none. Without trigger+answer evals the family has
        no quality gate. Generator / IR wait until one card template
        has been used for real. Joins wait so arch-* and this family
        are not specified together.
```

If the human rejects the top sentence, do not keep the children as a “recommended slate.” Re-pose from Q1.

---

## 6. MECE cuts (one cut at a time)

Apply **one dimension per list**. A later option is a date, not a sibling. A stackable item is a **menu**, not XOR.

### Cut 0 — Where the capability lives (closed)

| Id | Option | Status |
|---|---|---|
| W1 | No skill — agents read Concepts / `okf-curator` | Closed (C3) |
| W2 | Put it in an **existing** family (`arch-*` / `aws-ai-*` / `sdd-*` / `okf-curator`) | Closed (C3). Old write-up said “patch arch-*” only — that was an instance, not the class. |
| W3 | New sibling family inside `skill-sync` | **Chosen (C3)** |
| W4 | Capability outside `skill-sync` (MCP-only, manual-only) | Not proposed; packaging ≠ home. aws-ai already ships a portable zip *and* is a family. |

Do not replay Cut 0 unless C3 is withdrawn.

### Cut 1 — What the first skill teaches (scope)

| Id | Option | Notes |
|---|---|---|
| **S1** | Tactical loop only (the 34 A/B/C/D Concepts as *source material*) | Matches §0. Bundle still keeps E (R4). |
| **S2** | Styles only | Dead — does not solve the problem. |
| **S3** | Skill also owns styles as a 5th category | Matches the bundle/catalog-of-record wording; competes with mounted `arch-style`. |
| *(not an option)* | “Tactical now, styles later” | **A date on S1 vs S3**, not a fourth scope. If they want this, record `S1` + `later: revisit S3`. |

### Cut 2 — How SKILL.md files are cut (topology)

| Id | Option | Notes |
|---|---|---|
| **T1** | Stage files (`-diagnose` / `-select` / `-apply` / `-verify`) | Weak. No per-stage gate. Useful protocol survives as **sections**. |
| **T2a** | Category files = **catalog groups A/B/C/D** | §9 default. Easy to file. Whether symptoms span letters is Ht2b’s untested claim (its own example stays in letter C) — killing tests decide (§12). |
| **T2b** | Category files = **agent job** (resilience / messaging / data / traffic / coordination) | Original D2. Matches combinations. Cross-links still needed for orphans. |
| **T2-defer** | Ship the shared first skill now (the seven owned cards T2a and T2b agree on); close the cut at skill #2 | Added by §12. Converts the bet into gated-on-data — the §7 killing tests run on real usage before the cut closes. Wave-1 router text stays cut-neutral. |
| **T3** | One catalog skill | Fast; 34-name trigger surface; `needs-probe` (frontmatter budgets). |

Thin slice = “router + first category now” is a **delivery sequence on T2a or T2b**, not a fifth topology. **T2-defer** (§12) is different in kind: it ships the slice while leaving the cut open.

### Cut 3 — How the agent starts (primary entry only)

| Id | Primary | Bypass (may stack) |
|---|---|---|
| **E1** | Symptom / clinic | D5 |
| **E2** | Pattern name (“saga”) | Required bypass if E1 is primary |
| **E3** | NFR / quality-attribute (“availability”) | Often the same utterance as E1 |
| **E4** | **Code / diff in hand** (“this client has no timeout”) | Omitted from the old brainstorm; likeliest for a *coding* agent |

Pick **one primary**. Record bypasses separately (`E1 + bypass E2, E4`).

### Cut 4 — What the agent reads (pipeline, *now*)

| Id | Option | Notes |
|---|---|---|
| **P0** | No distilled cards — SKILL.md protocol + Concepts in `cases/SystemDesignPatterns/` | Cheapest in-repo. Portability suffers (H3). Old tree omitted this. |
| **P1** | Hand-distill against a frozen template (3-card thin slice) | Old D4-lite / G4-a |
| **P2** | Generator from Concepts first | Old D4 / G4-b. Nested: D7 is P2 + a stricter schema + extra projections. |
| **P3** | Pattern IR first | Old D7 / G4-c. Not a sibling of P2 — a stricter P2. |

“Generator later” is **P1 then P2**, not a fifth box. IR is justified by Copilot *and* by MCP / card lint / stable evals — do not repeat “IR only exists for Copilot.”

### Cut 5 — What proves it (menu — pick a minimum bar; ids V1–V5, renamed from Q1–Q5 by §12)

| Id | Item | Role |
|---|---|---|
| **V1** | Trigger + answer evals at the thin slice | **Minimum bar.** `evals.json` precedent: `.cursor/skills/aws-ai-lifecycle/evals/evals.json`. Format compatibility `needs-probe`. |
| **V2** | Defer evals | Schedule risk, not a strategy |
| **V3** | Fitness recipes in each card; code only when this repo names a stack | Old D6. This repo is the design workspace, not spine/o1 Java. |
| **V4** | OKF lint + skill-sync | Floor, already true |
| **V5** | Card-template / schema lint | Appears once P1 or P2 exists |

### Cut 6 — When other families consume this (second session)

Do **not** put this in the same row as Cuts 1–5. Ask after Q1–Q5.

| Id | Option |
|---|---|
| **J1** | Seams only (reserve output shapes). Styles→`arch-style` is a **separate** track if anyone runs it. |
| **J2** | One named join this iteration (say which skill, which artifact). |
| **J3** | Full join to arch / aws-ai / sdd now | Contradicts C3; straw man — do not offer unless asked. |

**Join and scope are one fight if you are not careful:** “styles wire into `arch-style`” is a join, not a reason to own or not own style *cards*. Ask them separately.

### Outside the tree (hygiene)

- **Name:** `sysdesign-*` / router `sysdesign-patterns` vs `sdp-*` vs `patterns-*`. Collision fact: `sdp-*` is one character from `sdd-*`. Does not change behavior.
- **Binding:** optional `.<prefix>/binding.toml` vs portable-only (old H6). Decide at spec.
- **First thin-slice membership** (which Concepts sit in `-resilience`) is a spec list once T2b or T2a is picked — not a Stage-1 axis.

---

## 7. Hypothesis tree (honest verdicts)

**H0 (proposed lead — not accepted):**  
W3 + S1 + T2b + E1 (bypasses E2, E4) + P1 (P0 acceptable for week one) + Q1 + Q3-as-recipes. Joins and name are later.

H0 is a **bet**. It can lose. Do not present it as validated.

Verdicts: **validated** = file evidence for *that claim*; **plausible** = no contradiction; **needs-probe**; **rejected**; **weakened** = true but does not kill the rival.

```
H0
├── S  SCOPE
│   ├── Hs1  Skill independence means the tactical loop, not style selection.
│   │        Evidence: brainstorm §0 lines 26–32 (“not the problem: styles”).
│   │        Verdict: VALIDATED as a reading of the problem.
│   ├── Hs2  Therefore the skill must also teach styles, or a solo install
│   │        cannot “work on its own.”
│   │        Dies if: “on its own” = tactical loop (Hs1).
│   │        Do NOT reject Hs2 by saying “arch-style is already mounted” —
│   │        that answers a workspace-install question, not a solo-family
│   │        question. Reject it from §0, or accept S3 if the human wants
│   │        the skill to match the 47-Concept bundle.
│   │        Verdict: REJECTED given §0; REOPEN if they pick S3.
│   └── Hs3  The gap in arch-* is pattern mechanics, not style selection.
│            Evidence: grep of arch-*/SKILL.md and references for
│            circuit|bulkhead|saga|outbox|idempoten|rate limit → no hits
│            (re-run before you cite). Style Concepts already cite
│            arch-style/references/style-selection.md and say do not
│            re-run the four determinations.
│            Verdict: VALIDATED (gap) + VALIDATED (E-cards already wired
│            as citations). Does not by itself forbid S3.
│
├── T  TOPOLOGY
│   ├── Ht1  Four stage skills need a per-stage gate to be worth the files.
│   │        Evidence: aws-ai splits on credential / CDK / harness gates;
│   │        this family has test_gate = none.
│   │        Verdict: WEAKENED T1, not killed. Keep stages as sections.
│   ├── Ht2a Catalog A–D grouping exists, so T2a is easy.
│   │        Evidence: catalog groups; index.md sections; five explainers
│   │        a-communication.html … e-architectural-styles.html.
│   │        Verdict: VALIDATED as feasibility. NOT validated as the
│   │        right trigger cut.
│   ├── Ht2b Clinic combinations stay inside one job skill more often
│   │        than inside one catalog letter.
│   │        Example: breaker + timeout + retry + budget = C1+C7+C2,
│   │        sometimes + C10/C8. Saga is B5; gateway is C6; cache is B3.
│   │        Verdict: PLAUSIBLE. This is the claim the V1 trigger evals and the §7 killing tests must test.
│   └── Ht3  One skill can trigger on a 34-pattern surface.
│            Verdict: NEEDS-PROBE (old P12 / H5).
│
├── E  ENTRY
│   ├── He1  Class failure is pattern-dropping without a confirming metric.
│   │        Evidence: CircuitBreaker.md already teaches check raw error
│   │        rate before tuning; constitution requires trade-offs.
│   │        Verdict: PLAUSIBLE (doctrine + gold card; no eval yet).
│   ├── He2  Name-lookup must remain a bypass.
│   │        Verdict: PLAUSIBLE.
│   └── He4  Code/diff is a first-class entry for coding agents.
│            Verdict: PLAUSIBLE; omitted from old D5; put on the gate.
│
├── P  PIPELINE
│   ├── Hp0  In this workspace, Concepts can be the first read surface.
│   │        Verdict: PLAUSIBLE. Portability (H3) argues against P0 as
│   │        the *shipped* form if a portable zip is in scope.
│   ├── Hp1  A generator needs a stable schema; freeze a template on a
│   │        real thin slice first.
│   │        Old “two schemas” argument is WEAKER under S1 (the E/decision
│   │        schema goes away). Do not use E-cards to slow P2 if you
│   │        picked S1.
│   │        Verdict: PLAUSIBLE for P1-before-P2; do not over-claim.
│   ├── Hp2  Cards must stand alone if the family is shipped outside
│   │        this repo (aws-ai portable zip ships skill dirs only).
│   │        Verdict: VALIDATED as a constraint *if* portability is a
│   │        goal. Confirm at spec. Not a law of in-repo wave 1.
│   └── Hp3  IR-now is expensive while the card shape is unlearned.
│            Extra IR value (MCP, lint, evals) is real; still not a
│            reason to start there.
│            Verdict: PLAUSIBLE deferral.
│
├── Q  QUALITY
│   ├── Hq1  Without evals there is no family quality gate.
│   │        Evidence: test_gate none; skill-sync = drift; OKF = structure.
│   │        Verdict: VALIDATED → V1 (evals) is do-regardless.
│   └── Hq2  Executable fitness needs a named stack in *this* repo.
│            Verdict: VALIDATED → Q3 as recipes now.
│
└── J  JOIN (second session)
    ├── Hj1  House sibling join is a prose protocol (aws-ai → arch-decide).
    │        Verdict: VALIDATED as precedent, not as a proof we must wait.
    └── Hj2  Content-isn’t-ready is a DEAD reason to defer joins
             (34 tactical Concepts exist). Remaining reason is coupling
             (specify two families at once).
             Verdict: old G6-a rationale is STALE. Prefer J1 as a
             coupling preference, and say so.
```

### Killing tests (use these; do not invent new rhetoric)

| If this happens | Drop | Switch to |
|---|---|---|
| One worked clinic (“p99 walked upstream” / “client has no timeout”) needs cards from two job skills *and* would have stayed in one A–D skill | T2b | T2a |
| Same clinic stays inside one job skill and would have hopped A–D letters | T2a | T2b |
| Trigger eval: one description recalls saga + p99 + error budget | T2* | T3 |
| Human wants style *selection* without loading `arch-style` | S1 | S3 |
| Three hand cards extract mechanically into one schema | P1-forever | P2 as fast-follow |
| Portable zip is explicitly out of scope for v1 | must-have P1 | P0 is enough to start |

---

## 8. Live human gate (supersedes brainstorm §8 and §9)

Pick by id. Recommended slate if they want one line:

`S1 T2b E1+E2+E4 P1 V1 J1 N-a`

*(§12 divergence: the reviewer recommends `T2-defer` where this slate bets `T2b`.)*

### Q1 — Skill scope (ask this first — both topology option sets presuppose S1; §12)

- `S1` — tactical loop only; E stays in the bundle / `arch-style` (**recommended**; matches §0)
- `S3` — family also owns styles (topology then needs a styles bucket — name it at Q2)
- `S1` + `later:S3` — if they want a date, not a third box

### Q2 — Topology of the first skill

- `T2-defer` — ship the shared first skill now; close T2a-vs-T2b at skill #2 on §7 killing-test data (**review recommendation** — §12)
- `T2b` — job-shaped categories; first skill `-resilience` (**original bet** — commit now)
- `T2a` — catalog groups A/B/C/D; first skill = group C
- `T3` — single catalog skill
- `T1` — four stage skills (discouraged; say why if they pick it)

### Q3 — Primary entry + bypasses

- `E1` — clinic primary (**recommended**)
- Bypasses (multi-select): `E2` name · `E4` code/diff (**recommend both**) · `E3` NFR

### Q4 — Portable zip first, then what the agent reads now

§12 inverted this question: the gate previously asked the P-conclusion while parking its deciding premise (portable zip in v1 — old §9 task) to spec. Answer the premise:

- `Z-yes` — portable zip is in v1 scope → `P1` (hand-distill 3 cards against a frozen template)
- `Z-no` — in-repo only for v1 → `P0` (Concepts as the read surface; cards when portability enters scope)
- `Z-spec` — cannot answer yet → record `P0` to start + `P1` before any zip ships; carry Hp2 to spec

`P2` (generator first) and `P3` (IR first — discouraged now) stay pickable by id regardless.

### Q5 — Quality (menu; ids V1–V5, renamed from Q1–Q5 by §12)

- `V1` — evals at thin slice (**do-regardless**; not a taste pick)
- `V3` — fitness as recipes in the verify section (**recommend**)
- `V2` — defer evals (record as accepted risk)

### Q6 — Name (hygiene)

- `N-a` — `sysdesign-*`, router `sysdesign-patterns` (**recommended**)
- `N-b` — `sdp-*`
- `N-c` — `patterns-*`
- `N-d` — other

### Q7 — Joins (ask after Q1–Q5, or skip to spec as “seams”)

- `J1` — seams only this iteration (**recommended** as a coupling preference, not because content is missing)
- `J2` — one join now (name it)

### Proposed first `-resilience` membership (only if T2b — spec list, not a gate)

Draft, not accepted: [CircuitBreaker](../../../cases/SystemDesignPatterns/CircuitBreaker.md), [RetryBackoff](../../../cases/SystemDesignPatterns/RetryBackoff.md), [TimeoutsDeadlines](../../../cases/SystemDesignPatterns/TimeoutsDeadlines.md), [Bulkhead](../../../cases/SystemDesignPatterns/Bulkhead.md), [Idempotency](../../../cases/SystemDesignPatterns/Idempotency.md), [LoadShedding](../../../cases/SystemDesignPatterns/LoadShedding.md), [GracefulDegradation](../../../cases/SystemDesignPatterns/GracefulDegradation.md). Cross-link, do not own: [FailoverHealth](../../../cases/SystemDesignPatterns/FailoverHealth.md), [CachingStrategies](../../../cases/SystemDesignPatterns/CachingStrategies.md), [OutboxCdc](../../../cases/SystemDesignPatterns/OutboxCdc.md). Thin-slice cards to distill first: CircuitBreaker, RetryBackoff, TimeoutsDeadlines.

---

## 9. What to carry into sdd-spec (if the gate closes)

Validated enough to carry: Hs1, Hs3 (gap), Ht1 (as “stages = sections”), Hq1, Hq2, H1-from-old-brainstorm (manifest entry is generic — re-open `tooling/skill-sync/manifest.toml` and `skill_sync.py` before citing lines).

Carry as spec-time tasks:

- H5 / P12 — trigger eval on the *chosen* topology (T2-defer vs T2b vs T2a vs T3).
- Evals-format compatibility with `aws-ai-lifecycle/evals/evals.json`.
- Hp2 — portable zip in v1: asked at the gate since §12 (Q4 `Z-*`); if `Z-spec`, decide here.
- Freeze **one** operational card template from CircuitBreaker/RetryBackoff *after* the first three distillations, not before.
- Ask-first / ADR: new skill family + new manifest family are a new abstraction.

Do **not** carry: “D4 generator needs two schemas” if S1 was picked; “IR only for Copilot”; “joins wait because content isn’t ready”; “T2a is validated.”

---

## 10. Paths the next agent should open (not memorize)

| What | Path |
|---|---|
| This handover | `docs/research/sysdesign/system-design-patterns-skill-mece-handover.md` |
| Historical brainstorm | `docs/research/sysdesign/system-design-patterns-skill-brainstorm.md` |
| Catalog | `docs/research/sysdesign/system-design-patterns-catalog.md` |
| Bundle index | `cases/SystemDesignPatterns/index.md` |
| Depth bar | `cases/SystemDesignPatterns/CircuitBreaker.md`, `RetryBackoff.md` |
| Explainers | `docs/architecture/explainers/system-design-patterns/*.html` |
| Manifest | `tooling/skill-sync/manifest.toml` |
| Sibling-family shape | `.cursor/skills/aws-ai-lifecycle/SKILL.md` |
| Eval precedent | `.cursor/skills/aws-ai-lifecycle/evals/evals.json` |
| Style matrix E-cards cite | `.cursor/skills/arch-style/references/style-selection.md` |
| SDD brainstorm skill | `.claude/skills/sdd-brainstorm/SKILL.md` or `.cursor/skills/sdd-brainstorm/SKILL.md` |

---

## 11. What the previous analysis got wrong (so you do not repeat it)

1. Reverse-engineered six axes from G0–G6, then called the recommended slate “validated.”
2. Treated Quality as XOR and then said Q1+Q3 “can stack.”
3. Called “tactical now, styles later” a fourth scope while denying the same move on Pipeline.
4. Equated original D2 (job) with §9 D2 (A–D).
5. Rejected “own styles” by “arch-style is mounted” instead of by §0’s problem statement.
6. Said T1 “dies.” It is only expensive.
7. Said IR is only for Copilot.
8. Said joins wait because content is not ready. Content is ready. Coupling remains.
9. Put the conclusion in H0’s title and argued downward.

The useful remainder: one question at a time; T1-as-four-files is a bad deal; evals early; IR-now is the wrong first build; clinic + A/B/C/D may fight.

---

## 12. Amendments (2026-09-13, adopted post-review)

An adversarial review ran before the gate: five independent lenses filed 35 criticisms against this handover; 29 were refuted by paired accuracy/materiality refuters and 6 survived; 23 endorsements verified — all load-bearing facts held, and the §4 D2-retargeting trap, the E4/P0 holes, the date-not-a-box rule, and the G0-a wrong-ground rejection were all confirmed against the record (review run `wf_57a8628e-767`). The owner adopted these amendments; §8 above is already amended.

1. **Calibration.** Cut 2’s T2a note and the §5 pyramid asserted the clinic-vs-catalog conflict as fact while Ht2b is PLAUSIBLE and the only worked example (C1+C7+C2, +C10/C8) sits entirely in letter C — consistent with both cuts, discriminating neither. Both spots now mark the conflict untested; the §7 killing tests decide.
2. **Scope before topology.** T2a and T2b both enumerate tactical-only buckets, so the topology options presuppose S1 while Hs2 keeps S3 live (“REOPEN if they pick S3”). Scope is now Q1; topology is Q2.
3. **`T2-defer` added.** The two cuts’ first skills nearly coincide (seven owned cards, all group C; the delta is C3–C6), and the killing tests need usage evidence that exists only after the first skill ships. `T2-defer` ships the shared first skill now and closes the cut at skill #2; under it the §7 killing tests are the skill-#2 decision procedure. Reviewer divergence from the original slate: recommend `T2-defer`; `T2b` remains the commit-now bet.
4. **Q4 inverted.** The gate asked the P0-vs-P1 conclusion while its stated discriminator (portable zip in v1) was parked to spec (old §9 task). The gate now asks the premise (`Z-yes` / `Z-no` / `Z-spec`) and derives the P-pick.
5. **Id rename.** Quality-menu ids Q1–Q5 collided with gate-question ids Q1–Q7 (§8 Q5’s options were literally “Q1/Q3/Q2”; §7’s “the claim Q1 must test” was ambiguous). Quality items are now **V1–V5** everywhere in this file.

**Provenance caveat on §11 (recorded, not amended):** items 3, 4, 5, 7 verify against the sibling brainstorm; items 1, 2, 6, 8, 9 use vocabulary the brainstorm never contained (“dies”, “can stack”, a slate called “validated”, H0) — read those as lessons from a prior analysis pass, not as an audit of the brainstorm record.

---

## 13. Consumer / steering dimension (recorded 2026-09-13, owner request)

Added after exploring how other skills would use this content at human-in-the-loop gates.

**Reframe.** The family's long-run value is not only the standalone clinic; it is a **decision substrate other skills pull from at human-gated steps** to steer a choice. The demand is already latent in the tree — `arch-risk/SKILL.md:62` and `references/risk-storming.md:52` hand-write "backpressure queue → priority channel" mitigations with no card to cite.

**Consumer map** (each need is a projection of card sections the tactical cards already carry):

| Consumer | Human-in-loop gate | Shape it needs | Card section that feeds it |
|---|---|---|---|
| **arch-risk** | mitigation accept/reject (human owns cost) | pattern as a mitigation + cost/knobs | Failure modes · Configuration · Trade-offs |
| **arch-validate** | wiring fitness functions | metrics → checklist-for-computers | Observability |
| **arch-decide** | the ADR | option + trade-off | Trade-offs · When-not-to-use |
| **sdd-spec** | verify / acceptance list | knobs/defaults → assertions | Configuration · Tuning |
| **sdd-brainstorm** | the direction pick | what-breaks / obligation on a direction | Failure modes · When-not-to-use |
| **aws-ai-design** | agent tool-call design | retry/timeout/breaker/idempotency for LLM calls | LLM-provider angle (prospective — no hooks found yet) |

Seam is greenfield: no skill cites `SystemDesignPatterns` yet.

**Load-bearing insight.** Consumers reference the **card, not the skill grouping**. Topology (Cut 2) is therefore nearly invisible to consumers; the design weight sits on the **pipeline** (Cut 4 — cards must be addressable by a stable id and self-contained) and **joins** (Cut 6). This weakens "P0 forever" (a raw Concept cited by line is a fragile join) and gives the IR (P3) a second driver beyond Copilot: several families citing patterns programmatically.

**Design invariant (carry to spec).** Every card is addressable by a stable id, stands alone, and carries an explicit trade-off surface — the card, not the skill, is the unit other families consume. Per-consumer join output shapes (mitigation / fitness function / ADR option / verify task) are reserved as seams; **none built this iteration** (owner C3: independent first).

**Effect on the gate:** informs Cut 4 (favor a real addressable card layer over P0-forever) and Cut 6 / Q7 (the join shapes above). Does not change the topology pick.

---

## 14. Gate answers — GATE CLOSED 2026-09-13

Owner answered the §8 gate question by question (a bare yes was not accepted; each is an id pick). **Accepted slate:** `S1 · T2b · E1+E2+E4 · P1→P2 (Z-spec) · V1+V3+V5 · N-b (sdp-*) · J1`. Advance → **sdd-spec** via [system-design-patterns-skill-spec-handover.md](system-design-patterns-skill-spec-handover.md).

| Q | Decision | Note |
|---|---|---|
| **Q1 scope** | **S1** — tactical loop only; the 13 style cards stay in the bundle (R4) and feed `arch-style` | matches §0 / C3 |
| **Q2 topology** | **T2b** — job-shaped categories (resilience / messaging / data / traffic / coordination); commit now | Owner chose T2b over the review's `T2-defer` recommendation. **Carry to spec:** the job-cut's trigger fitness is still the untested bet (Ht2b PLAUSIBLE) — the §7 killing tests + the V1 trigger eval remain spec-time tasks; first skill `-resilience`, membership a spec list. Under S1 the five buckets are all tactical (no styles bucket). |
| **Q3 entry** | **E1** primary (symptom/clinic) + bypasses **E2** (name) & **E4** (code/diff in hand) | E3 (NFR) not opened — overlaps E1. E4 kept first-class for the coding-agent audience; cards already carry the config-shaped material it needs. |
| **Q4 pipeline** | **P1** now (hand-distilled cards vs a frozen template) → **P2** generator fast-follow → **P3** IR deferred-but-alive (consumer/MCP/Copilot drivers); **Z-spec** | Cards built standalone-friendly so a portable zip is cheap later; P0-forever ruled out by §13. P1 activates card-template lint (V5) for Q5. |
| **Q5 quality** | **V1** evals + **V3** fitness recipes + **V5** card-template lint (V4 lint/skill-sync floor always on) | V2 (defer evals) declined. V1 also serves T2b's untested trigger-fitness; V5 enforces the §13 addressable-card invariant. |
| **Q6 name** | **N-b** — `sdp-*` prefix; working router `sdp-patterns`, members `sdp-resilience`/`-messaging`/`-data`/`-traffic`/`-coordination` | Owner chose N-b over the review's N-a. **Carry to spec:** `sdp-*` is one character from `sdd-*` — disambiguate skill descriptions/triggers to avoid mis-invocation; router suffix (`-patterns` vs house `-lifecycle`) is a spec sub-detail. |
| **Q7 joins** | **J1** — seams only this iteration; no join built | Per C3 (independent-first) and because the family is greenfield — nothing to cite yet. **First join to build later = arch-risk** (only demonstrated demand: it already improvises backpressure/queue mitigations, `arch-risk/SKILL.md:62`). §13 reserves the six consumer output shapes. |
