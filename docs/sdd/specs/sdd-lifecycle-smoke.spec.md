# Spec: SDD lifecycle smoke (throwaway)

**Status:** **signed-off (2026-08-11)** — **THROWAWAY** lifecycle smoke complete (D1)  
**Direction:** D1 (brainstorm 2026-08-11, `docs/research/sdd-lifecycle-smoke-brainstorm.md`)  
**Change class:** throwaway / exploratory — light-spec carve-out  
**Ask-first / ADR:** none expected (markdown-only; no new dependency, service, or abstraction)

## Problem

An operator who provisioned this design workspace needs a **disposable, named**
change that proves the SDD conveyor is live: binding resolves, artifacts land
under bound homes, Stage-8 `check_gate` stays green — without mutating spine /
O7 / ash product specs.

## Goals

1. Exercise Stages 2–10 lightly on a throwaway triplet
   (`*.spec.md` / `*.plan.md` / `*.tasks.md`).
2. Produce a single smoke **receipt** (evidence of green `check_gate` + path
   checks) as the only “implementation” deliverable.
3. Keep product specs and tooling sources untouched.

## Non-goals

- Changing `tooling/skill-sync/`, `.sdd/binding.toml`, or skill projections
- Touching `mobile-test-automation-*.spec.md` or other product law
- Adding Python/automation (that was D6)
- Fresh cold-session skill-discovery probe (deferred; usage guide Part 0.4)
- Production sign-off of a durable feature

## Functional requirements

- **FR-1 Spec/plan/tasks triplet.** This change keeps a light EARS spec under
  `docs/sdd/specs/sdd-lifecycle-smoke.spec.md` and matching plan + tasks under
  `docs/sdd/plans/` with the same basename.
- **FR-2 Receipt.** Implementation produces one markdown receipt at
  `docs/research/sdd-lifecycle-smoke-receipt.md` containing: date, direction id,
  pasted `check_gate` SUMMARY line, and a short path checklist (binding keys,
  skill SKILL.md paths, triplet paths).
- **FR-3 Product quarantine.** No edits to product specs
  (`mobile-test-automation-*.spec.md`), `tooling/**` (except none), or
  `.cursor/skills/**` / `.claude/skills/**` sources/projections.
- **FR-4 Labeling.** Spec, plan, tasks, and receipt each state **THROWAWAY**
  in the title or status line so they are not mistaken for product law.
- **FR-5 Gate.** Before sign-off, `python3 tooling/skill-sync/skill_sync.py check`
  from repo root exits 0 with zero drift (this workspace’s Stage-8 bar;
  `test_gate` is `<none>`).

## Acceptance criteria (EARS — failure paths first)

- **AC-1** IF any of `docs/sdd/specs/sdd-lifecycle-smoke.spec.md`,
  `docs/sdd/plans/sdd-lifecycle-smoke.plan.md`, or
  `docs/sdd/plans/sdd-lifecycle-smoke.tasks.md` is missing at the end of
  Stage 3 THEN the smoke has failed (triplet incomplete).
- **AC-2** IF the receipt path `docs/research/sdd-lifecycle-smoke-receipt.md`
  is missing after implementation THEN the smoke has failed.
- **AC-3** IF `check_gate` exits non-zero OR the SUMMARY line reports drift
  THEN Stage-8 fails and Stage-10 sign-off MUST NOT pass.
- **AC-4** IF a diff for this change edits a product spec
  (`docs/sdd/specs/mobile-test-automation-*.spec.md`) OR any path under
  `tooling/` OR skill projection trees THEN the change violates FR-3 and
  MUST be replanned or reverted before sign-off.
- **AC-5** WHEN the receipt exists, it MUST contain the literal substring
  `THROWAWAY` and a pasted `SUMMARY:` line from a real `check_gate` run.
- **AC-6** Ubiquitous: the spec header marks the change as throwaway /
  exploratory; it MUST NOT claim product or spine/O7 delivery status.
- **AC-7** WHEN Stage-10 is run, throwaway artifacts (spec, plan, tasks,
  receipt; brainstorm optional) remain in-tree, each marked **THROWAWAY**
  (clarify C1 = leave; do not require delete).
- **AC-8** WHEN Stages 9–10 run, the change follows the **clean path**:
  classify finds no `missing`/`partial`/`contradicts`/`unrequested` gaps;
  no Phase-N tasks are required; human may sign off after green `check_gate`
  (clarify C2).
- **AC-9** WHEN Stage 7 runs, a **lightweight same-thread** FR/AC checklist
  against the triplet + receipt is sufficient; a fresh-thread code-review is
  not required for this throwaway (clarify C3).

## Out of scope

D2/D3/D4/D5/D6 directions · role-card / coding-rules install · ADR filing ·
architecture kata · cold-session discovery probe · intentional gap / Phase-N
converge loop (rejected at C2) · mandatory fresh-thread Stage-7 (rejected at C3).

## Clarify log

| ID | Question | Decision |
|----|----------|----------|
| C1 | Stage-10 disposition of throwaway artifacts? | **A — leave marked THROWAWAY** (2026-08-11) |
| C2 | Converge path depth? | **A — clean path** (no intentional gap / Phase-N) (2026-08-11) |
| C3 | Stage-7 review depth for this markdown-only smoke? | **A — lightweight same-thread checklist** (2026-08-11) |
