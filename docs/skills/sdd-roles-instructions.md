---
type: runbook
title: SDD roles — how to use in this workspace
description: >-
  Workspace-resolved instructions for interactive sdd-roles (Claude agents +
  kernel card) in LLM-DRIVEN-MOBILE-TEST-AUTOMATION (design repo for MTA /
  spine / O7).
tags: [sdd, roles, conveyor, instructions, claude]
---

# SDD roles — instructions for this workspace

Use this when you want a **named role persona** (specifier, architect, coder,
…) with a write-scope + gate contract, instead of (or beside) a stage skill.
It is the short, path-resolved playbook for **interactive** use.

| Need | Doc |
|---|---|
| Clone / provision skills | [../SETUP.md](../SETUP.md) |
| SDD stage how-to | [sdd-lifecycle-instructions.md](sdd-lifecycle-instructions.md) |
| Full operator manual (pairings + conveyor) | [sdd-usage-guide.md](sdd-usage-guide.md) § Part 3 + Appendix A |
| Agent pointers | [../../AGENTS.md](../../AGENTS.md) |

**This repo is the design workspace.** Role cards are projected for Claude
Code; most maker/checker gates (build, tests, mutation, …) only bite in the
future spine/o1 Java delivery repo. Here, **you** are the write-guard and gate.

---

## 0. Before you start

1. Open **this folder** as the Cursor / Claude Code workspace root.
2. From repo root, confirm skill-sync:

```bash
python3 tooling/skill-sync/skill_sync.py check
```

Expected: `SUMMARY: 5 families, 0 drifted, 0 shadow -> exit 0`.

3. Prefer a **fresh Claude Code session** after provisioning (agents register
   at session start).
4. Invoke **one role per turn** for one stage of work. Do not ask a role to
   “run the whole conveyor” interactively.

### Surfaces (already provisioned by skill-sync)

| Surface | This workspace |
|---|---|
| Role agent cards | `.claude/agents/*.md` (9 roles) |
| Kernel skill card (constitution) | `.claude/skills/sdd-roles/SKILL.md` |
| Canonical SoT | `tooling/sdd-roles/` |
| Claude projection SoT (emit source) | `tooling/sdd-roles/kernel/corpus/catalog-projections/claude-code/` |
| ADR seam for kernel/tooling work | `docs/architecture/adrs/tooling/sdd-roles/` (see `.sdd/binding.toml` `adr_home_sdd_roles`) |
| Conveyor configs (headless) | `tooling/sdd-roles/configs/` |

**Cursor:** there is no committed `.cursor/agents/` tree for roles in this
repo. Use Claude Code subagents, or paste a card’s invocation + doctrine from
SoT (Path B below).

### Warning — do not mount conveyor hooks

Do **not** copy
`tooling/sdd-roles/kernel/corpus/catalog-projections/claude-code/hooks/hooks.json`
into `.claude/settings.json`. That file is the conveyor’s fail-closed
write-guard; mounting it blocks normal interactive work. Interactive mode
relies on **you** enforcing scopes (see §2).

---

## 1. The nine roles (kernel catalog)

| Role | Tag | Gates (catalog) | Writes (catalog) | Fit in *this* design repo |
|---|---|---|---|---|
| `specifier` | maker | none | `specs/` | High — map to `docs/sdd/specs/` (and scenario law under plans when you say so) |
| `architect` | maker | build | `src/`, `tests/`, `docs/adr/` | Design via arch-\*; structural honor-pattern later in spine/o1 |
| `coder` | maker | build, tests, ir-gate | `src/`, `tests/` | Deferred — Java delivery repo |
| `cleaner` | maker | build, tests, crap | `src/` | Deferred |
| `hardener` | checker | tests, mutation | `src/test/`, `tests/`, `specs/` | Deferred |
| `qa` | checker | build, tests, crap, ir-gate | `src/`, `tests/` | Light use as diagnostic / review lens |
| `solo` | maker | build, tests, crap, mutation, ir-gate | `src/`, `tests/`, `specs/` | Rare; prefer stage skills here |
| `maker3` | maker | build, tests, crap, ir-gate | `src/`, `tests/` | Deferred |
| `checker3` | checker | tests, mutation, ir-gate | `src/`, `tests/` | Light use as diagnostic / review lens |

Stamp / catalog live on the kernel card: `.claude/skills/sdd-roles/SKILL.md`.

---

## 2. Golden rules (interactive)

1. **Kernel first** — role reads `.claude/skills/sdd-roles/SKILL.md` before acting.
2. **You enforce write scopes** — no write-guard hook in interactive mode. Check
   the diff against the role’s scopes (adapted to this repo’s paths — say the
   mapping in the prompt).
3. **Law permanence** — scenario / EARS law files are amended only by you; makers
   must not “fix the test to go green.”
4. **Add-only tests** — makers may add tests; they must not modify or delete
   existing ones (when that applies).
5. **One stage + sparse handoff** — end with decisions, what moved, what stays
   red — not a process diary.
6. **Roles ≠ stage skills** — `sdd-spec` authors documents; `specifier` turns
   approved criteria into executable scenario law. `arch-*` decides; `architect`
   honors ratified ADRs (see [sdd-usage-guide.md](sdd-usage-guide.md) §3.1–3.2).

---

## 3. Copy-paste prompts (Claude Code)

### Path A — installed subagent

```text
Use the <role> subagent. Read the kernel skill card
(.claude/skills/sdd-roles/SKILL.md) first. Adapt write scopes:
specs/ → docs/sdd/specs/; docs/adr/ → the binding adr_home for this change.
Task: <one stage of work>. End with a sparse handoff. Do not leave your scopes.
```

### Path B — no subagent / Cursor paste

Open
`tooling/sdd-roles/kernel/corpus/catalog-projections/claude-code/agents/<role>.md`,
paste **Invocation** + **Doctrine**, then your task.

### Specifier (design-repo shaped)

```text
Use the specifier subagent. Read the kernel skill card first. Your specs/
write scope is docs/sdd/specs/ in this workspace. Convert the approved tasks
at docs/sdd/plans/<name>.tasks.md into scenario law (Given/When/Then + entry
command + example tables). Never write production code. Sparse handoff only.
```

### Architect — honor pattern (after arch-* ratification)

```text
Use the architect subagent. Read the kernel skill card first. Input: ratified
ADRs at <paths>. Honor them — do not re-decide. In THIS design repo, limit
writes to docs under the binding adr homes / architecture tree; do not invent
src/ layout here. Sparse handoff: what was honored, what is deferred to spine/o1.
```

### Smoke (Claude)

```text
Use the specifier agent — what may you write? Name your gates and the kernel
card path in this repo. Do not author files.
```

---

## 4. Gate tokens / human ratification

Roles do not use `SPEC-OK` / `PLAN-OK` tokens. Those belong to **sdd-\*** stage
skills. For roles, you ratify by:

| You say / do | Meaning |
|---|---|
| Accept the sparse handoff | Role stage complete; law/structure is durable |
| Reject + send gaps back | Especially to specifier when law is incomplete |
| Run `check_gate` yourself | `python3 tooling/skill-sync/skill_sync.py check` from repo root |
| Spine/o1 only | Run the role’s catalog gates (build, tests, …) yourself |

---

## 5. Headless conveyor (advanced — usually not here)

`gate-runner` + write-guard + ledger live under `tooling/sdd-roles/`. Full
commands and bind flags: [sdd-usage-guide.md](sdd-usage-guide.md) Appendix A
and `tooling/sdd-roles/validator/README.md`. Default for this design workspace
is **interactive roles + human guard**, not a headless arm.

---

## 6. What not to do here

- Do not mount conveyor `hooks.json` into interactive `.claude/settings.json`.
- Do not treat role cards as a substitute for `sdd-lifecycle` / `arch-lifecycle`
  when you need staged human gates on specs or architecture decisions.
- Do not expect Java gates (CRAP, mutation, ir-gate tools) to exist in this repo.
- Do not install **coding-rules** here (spine/o1 later) — see
  [coding-rules-instructions.md](coding-rules-instructions.md).
- Work that changes `tooling/sdd-roles/` itself files ADRs under
  `adr_home_sdd_roles`, not the MTA application ADR series.
