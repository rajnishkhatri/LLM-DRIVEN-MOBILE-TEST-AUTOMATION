# Brainstorm: SDD lifecycle smoke (throwaway)

**Status:** Stage 1 complete — **D1 accepted**; full D1 smoke **signed-off 2026-08-11** (THROWAWAY)  
**Date:** 2026-08-11  
**Change class:** throwaway / exploratory — light-spec carve-out if chosen  
**Constitution:** `.cursor/rules/architecture-principles.mdc`  
**Binding:** `.sdd/binding.toml` (`check_gate` = skill-sync; `test_gate` = `<none>`)

## Problem (posed as problem, not solution)

An operator who just provisioned this design workspace cannot **prove in one short disposable change** that the SDD skill family is live end-to-end (binding resolves, Stage skills load, artifacts can land under bound homes, Stage-8 `check_gate` stays green) **without** mutating spine / O7 product specs or inventing delivery-repo work.

## Premise audit

| ID | Premise | Status | Evidence |
|----|---------|--------|----------|
| P1 | `.sdd/binding.toml` exists and points `spec_home`/`plan_home` at `docs/sdd/{specs,plans}/` | **verified** | `.sdd/binding.toml:15-16` |
| P2 | `check_gate` is `python3 tooling/skill-sync/skill_sync.py check` and is green today | **verified** | binding L13; live run 2026-08-11: `SUMMARY: 5 families, 0 drifted, 0 shadow -> exit 0` |
| P3 | Cursor projections for all six `sdd-*` skills exist under `.cursor/skills/` | **verified** | `skill_sync.py check` OK sdd (48 file-pairs / 2 projections); SKILL.md present for lifecycle/brainstorm/spec |
| P4 | This workspace has no executable `test_gate` | **verified** | `.sdd/binding.toml:14` `test_gate = "<none>"` |
| P5 | A prior full lifecycle already exercised skill-sync itself | **verified** | `docs/sdd/specs/skill-sync.spec.md:1-11` (signed-off 2026-08-10) |
| P6 | Product specs (spine/O7/ash) are the right place for a smoke marker | **refuted** | Those specs are durable product law; a smoke must not hitch-hike there. Corrected framing: smoke artifacts must be clearly named throwaway and outside product scope. |
| P7 | Skills will auto-discover mid-session after provision | **unverifiable** here without a cold session | Usage guide Part 0.4 (`docs/skills/sdd-usage-guide.md:101-103`) warns registry freeze; this session already loaded skills — treat as `needs-probe` for a *fresh* chat, not blocking this in-thread smoke. |

**Corrected framing (P6):** Prove the conveyor with a **named throwaway** change whose artifacts are deletable and never claim product status.

## Directions (~6)

### High-probability (follow repo patterns)

**D1 — Light-spec throwaway triplet (skill-sync pattern, minimal)**  
Land `docs/sdd/specs/sdd-lifecycle-smoke.spec.md` + matching `.plan.md` / `.tasks.md` under `docs/sdd/plans/`, with EARS criteria that are *repo-evidence checks* (binding keys present, `check_gate` exit 0, skills loadable by path). Implement = write a tiny marker file under `docs/research/` or a `## Smoke evidence` section, then converge + delete or leave marked THROWAWAY.  
- Follows: `skill-sync.spec.md` / `.plan.md` / `.tasks.md` naming.  
- Tradeoff: adds three docs you must remember to delete.  
- Breaks if: someone treats smoke as product law.  
- Ask-first: none if no new dep/abstraction.

**D2 — Research-only brainstorm + light one-file “receipt”**  
Keep ideation in `docs/research/*-brainstorm.md` (this file); skip full plan/tasks; one receipt markdown under `docs/research/` listing Stage 0–1 evidence.  
- Follows: `docs/research/mobile-test-automation-*-brainstorm.md`.  
- Tradeoff: does **not** exercise `sdd-spec` / implement / converge artifact paths.  
- Breaks if: goal is “full conveyor smoke.”

**D3 — Checklist in usage guide only**  
Add a Part 0.x “lifecycle smoke” subsection to `docs/skills/sdd-usage-guide.md` with copy-paste prompts; no new spec/plan.  
- Follows: operator-manual ownership in usage guide.  
- Tradeoff: documents probes; does not *run* Stages 2–10.  
- Breaks if: we need proof the agent can write under `spec_home`.

### Exploratory

**D4 — Demand-side: do not create a change**  
Treat green `skill_sync.py check` + successful skill loads in this chat as sufficient proof; delete this brainstorm; no further stages.  
- Demand-side: the expensive “full lifecycle” does not happen.  
- Tradeoff: weak proof of Stages 2–10.  
- Breaks if: user wants implement/converge exercised.

**D5 — Class-level: reusable “lifecycle smoke” template**  
Add a reusable template under `docs/sdd/specs/` (or `docs/skills/_sdd/`) for future smokes, plus one filled instance.  
- Class over instance vs one-off D1.  
- Tradeoff: new template = mild abstraction → call out G1 / possible decision-log note.  
- Breaks if: overbuilt for a one-time verify.

**D6 — Automated probe script**  
Small stdlib script that asserts binding keys + skill paths + runs `check_gate` (skill-sync shape).  
- Exploratory ops automation.  
- Tradeoff: new tooling surface; may trigger Ask-first if treated as a new service.  
- Breaks if: smoke was meant to be docs-only and disposable.

## Leading recommendation

**D1** — exercises the same artifact homes and gates a real change uses, stays clearly throwaway, matches the 2026-08-10 skill-sync lifecycle test-drive precedent, needs no ADR if kept to markdown + existing `check_gate`.

### Hypotheses (D1)

| H | Claim | Validation |
|---|--------|------------|
| H1 | Works *because* bound homes already exist and accept markdown | **supported** — `docs/sdd/specs/` and `docs/sdd/plans/` populated (e.g. skill-sync triplet) |
| H2 | Safe *because* no Ask-first seam if we add no dep/abstraction and do not touch product specs | **supported** — constitution Ask-first list is for deps/services/new abstractions; smoke marker is disposable docs |
| H3 | Stage-8 proof is `check_gate` alone here | **supported** — `test_gate = "<none>"` |
| H4 | “Zero code” means zero Python — still calendar-cheap | **supported** if D1 stays markdown-only; **reject** if D6 chosen |

## Dependency map

| Track | Items |
|-------|--------|
| **Do regardless** | Keep `check_gate` green; do not edit product specs (spine/O7/ash) for smoke |
| **Pick the priority** | Depth of conveyor exercised: D4 (Stage 0 only) vs D2 (1) vs D1 (2–10 light) vs D6 (tooling) |
| **Deferred** | Fresh-session discovery probe (P7) — separate cold-chat check from usage guide 0.4 |
| **Sequenced if D1** | brainstorm (done) → light spec → plan/tasks → implement marker → check_gate → converge/sign-off → optional delete |

## Human gate — pick a direction

Reply with one id (or a combination with explicit scope):

- **D1** — Light-spec throwaway triplet (recommended for “skills installed properly”)
- **D2** — Research brainstorm + receipt only
- **D3** — Usage-guide checklist only
- **D4** — Stop; green check_gate + this brainstorm is enough
- **D5** — Reusable smoke template + instance
- **D6** — Automated probe script

Not valid: bare “yes” / “go ahead” without an id.
