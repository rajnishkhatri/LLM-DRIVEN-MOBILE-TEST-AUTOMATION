---
type: runbook
title: SDD lifecycle — how to use in this workspace
description: >-
  Workspace-resolved instructions for driving the sdd-* skills in
  LLM-DRIVEN-MOBILE-TEST-AUTOMATION (design repo for MTA / spine / O7).
tags: [sdd, lifecycle, instructions, cursor]
---

# SDD lifecycle — instructions for this workspace

Use this when you want to run a **spec-driven change** in
`LLM-DRIVEN-MOBILE-TEST-AUTOMATION`. It is the short, path-resolved playbook.

| Need | Doc |
|---|---|
| Clone / provision skills | [../SETUP.md](../SETUP.md) |
| Full operator manual (all four families) | [sdd-usage-guide.md](sdd-usage-guide.md) |
| Agent pointers | [../../AGENTS.md](../../AGENTS.md) |

**This repo is the design workspace** (specs, plans, ADRs). It is **not** the
Java spine/o1 delivery repo — `coding-rules` and Java `test_gate` are not
mounted here.

---

## 0. Before you start

1. Open **this folder** as the Cursor / Claude Code workspace root.
2. From repo root, confirm the gate (re-run `fix` only if drifted):

```bash
python3 tooling/skill-sync/skill_sync.py check
```

Expected: `SUMMARY: 5 families, 0 drifted, 0 shadow -> exit 0`.

3. Prefer a **fresh chat** after provisioning (skills register at session start).
4. Tell the agent to **load the skill** for the stage you are in (see below).
   Do **not** say “run the whole lifecycle” in one shot — you hold every gate.

### Binding (already set — `.sdd/binding.toml`)

| Key | This workspace |
|---|---|
| constitution | `.cursor/rules/architecture-principles.mdc` |
| check_gate | `python3 tooling/skill-sync/skill_sync.py check` |
| test_gate | `<none>` |
| spec_home | `docs/sdd/specs/` |
| plan_home | `docs/sdd/plans/` |
| adr_home (MTA) | `docs/architecture/adrs/application/mobile-test-automation/` |
| adr_home (sdd-roles tooling) | `docs/architecture/adrs/tooling/sdd-roles/` |
| adr_template | `.cursor/skills/arch-decide/references/adr-template.md` |
| decision_log | `docs/architecture/log.md` |

Skill bodies: `.cursor/skills/sdd-*` (Cursor) and `.claude/skills/sdd-*`
(Claude). Canonical source: `tooling/sdd-skills-bundle/`.

---

## 1. Which skill owns which stage

| Stage | Skill | You are here when… |
|---|---|---|
| Router / “what stage?” | `sdd-lifecycle` | Starting a non-trivial change or lost |
| 1 Brainstorm | `sdd-brainstorm` | Problem open; no direction yet |
| 2–4 Spec → plan → tasks → analyze | `sdd-spec` | Direction chosen; no code yet |
| 5 Replan | `sdd-replan` | Blocked, scope change, or task invalidated |
| 6 Implement | `sdd-implement` | Task list approved |
| 7 Review | code-review (fresh thread) | Diff done; not the implementer chat |
| 8 Test / check | `check_gate` above | After implement / before sign-off |
| 9–10 Converge · sign-off | `sdd-converge` | Gaps vs spec, or ready for production |

**Skip the lifecycle** for typos / one-liners; **never skip** `check_gate` /
constitution. Anything that needs a new dep, service, or abstraction → full
lifecycle + ADR.

---

## 2. Golden rules (short)

1. **One stage per turn** — agent works → **you** gatekeep → advance or loop.
2. **You own gates** — agent must not self-approve SPEC-OK / PLAN-OK / SIGN-OFF.
3. **Label multi-option picks** — reply `D1`, `SPEC-OK`, `A`/`B`; bare “yes” is invalid when several options exist.
4. **Evidence** — `file:line` for repo claims; paste failing then passing gate output.
5. **Three strikes → `sdd-replan`** — do not invent a fourth broken approach.
6. **Durable state in files** — plans/tasks under `docs/sdd/plans/`, not only chat.

---

## 3. Copy-paste prompts (Cursor)

Paste one block at a time. Replace `<…>` placeholders.

### Router

```text
Load sdd-lifecycle. Using .sdd/binding.toml (not placeholders), say which
stage we are in for: <one-line problem or link to existing spec/plan>.
Name the owning skill and the human gate before we advance.
```

### Stage 1 — Brainstorm

```text
Load sdd-brainstorm. Problem (not solution): <problem>.
Audit premises against this repo, generate ~6 directions (3 patterned + 3
exploratory), validate hypotheses with file:line evidence, then STOP for my
direction pick by id.
```

Your reply: `D1` (or other id) — not bare “yes”.

### Stages 2–4 — Spec (stop after spec)

```text
Load sdd-spec. Direction <id> from <brainstorm path or summary>.
Write a light EARS spec under docs/sdd/specs/<name>.spec.md, run clarify
(≤5 questions, one at a time, each with a recommended answer), and STOP for
SPEC-OK before writing the plan.
```

Your replies: answer each clarify `A`/`B`, then `SPEC-OK`.

### Plan + tasks (after SPEC-OK)

```text
SPEC-OK. Derive docs/sdd/plans/<name>.plan.md and STOP for PLAN-OK.
```

```text
PLAN-OK. Write docs/sdd/plans/<name>.tasks.md with file-level tasks,
deps/parallel markers, and 1:1 EARS→pass/fail. Run Stage-4 analyze
(ground paths, check_gate baseline). STOP for TASKS-OK.
```

Your replies: `PLAN-OK`, then `TASKS-OK`.

### Stage 5 — Replan (only if needed)

```text
Load sdd-replan. What changed: <block / scope / finding>.
Update the plan/tasks docs (state lives there). Propose stay/slip/split/drop
per task. STOP for my approval, then route (back to sdd-spec if scope, else
tasks rewrite, else sdd-implement).
```

### Stage 6 — Implement

```text
Load sdd-implement. TASKS-OK on docs/sdd/plans/<name>.tasks.md.
Execute the next unblocked task with red-then-green evidence. Stop if blocked
(route to sdd-replan). After each task, keep check_gate green from repo root.
```

### Stage 7 — Review

Open a **fresh** chat (production changes). Throwaway markdown smokes may use
a same-thread FR/AC checklist if the spec carved that out.

```text
Code-review the diff for <change name> against
docs/sdd/specs/<name>.spec.md. List findings only; do not fix.
```

### Stage 8 — Gate

```bash
python3 tooling/skill-sync/skill_sync.py check
```

Paste the real SUMMARY line into the change record / receipt. `test_gate` is
`<none>` here.

### Stages 9–10 — Converge · sign-off

```text
Load sdd-converge. Classify every gap vs docs/sdd/specs/<name>.spec.md
(missing / partial / contradicts / unrequested). Append Phase-N tasks only;
do not fix in this stage. Then run the Stage-10 sign-off checklist and STOP
for my SIGN-OFF.
```

Your reply: `SIGN-OFF` (or name a gap). Commit only if you ask for a commit.

---

## 4. Artifact naming

| Kind | Path pattern |
|---|---|
| Spec | `docs/sdd/specs/<name>.spec.md` |
| Plan | `docs/sdd/plans/<name>.plan.md` |
| Tasks | `docs/sdd/plans/<name>.tasks.md` |
| Early research / brainstorm | `docs/research/<name>-brainstorm.md` (optional) |

Use one basename across the triplet (e.g. `skill-sync`).

Ask-first / new abstraction → ADR under the binding `adr_home` (or
`adr_home_sdd_roles` if the change touches `tooling/sdd-roles/`), using the
`arch-decide` template. Spec = *what*; ADR = *why*.

---

## 5. Gate tokens you type

| Token | Meaning |
|---|---|
| `D<n>` | Accept brainstorm direction |
| `SPEC-OK` | Approve spec; unlock plan |
| `PLAN-OK` | Approve plan; unlock tasks |
| `TASKS-OK` | Approve tasks/analyze; unlock implement |
| `SIGN-OFF` | Stage-10 production/acceptance (or throwaway complete) |

---

## 6. Smoke / sanity

To prove SDD is ready after setup (no new change):

```text
Load sdd-lifecycle. Confirm binding + skill paths for this repo, run
check_gate, and summarize whether SDD is ready — do not start a new change.
```

Or from the repo root:

```bash
python3 tooling/skill-sync/skill_sync.py check
```

---

## 7. What not to do here

- Do not install **coding-rules** into this design repo (spine/o1 later).
- Do not mount Claude conveyor `hooks.json` into interactive `.claude/settings.json`.
- Do not run `check_gate` from a subdirectory (fails loud; not silently green).
- Do not treat `docs/sdd/plans/spine-repo/{AGENTS,CLAUDE}.md` as governing
  *this* workspace — they are staged for the future code repo.
