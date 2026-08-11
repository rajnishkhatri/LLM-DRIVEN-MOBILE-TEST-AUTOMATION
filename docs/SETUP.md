---
type: runbook
title: Skill setup — LLM-DRIVEN-MOBILE-TEST-AUTOMATION
description: >-
  One-time and fresh-clone setup for all skill surfaces (Cursor, Claude Code,
  human docs) in this design workspace.
tags: [skills, setup, skill-sync]
---

# Skill setup — this workspace

Use this after cloning
`LLM-DRIVEN-MOBILE-TEST-AUTOMATION`. Skills are already committed; you
**re-provision projections** and verify bindings — you do not reinstall from
Architect.

Human index: [skills/README.md](skills/README.md)  
SDD how-to (this workspace): [skills/sdd-lifecycle-instructions.md](skills/sdd-lifecycle-instructions.md)  
Arch how-to (this workspace): [skills/arch-lifecycle-instructions.md](skills/arch-lifecycle-instructions.md)  
Operator manual (all families): [skills/sdd-usage-guide.md](skills/sdd-usage-guide.md)

---

## 1. Prerequisites (machine)

| Need | Why |
|---|---|
| Python 3.8+ | skill-sync, okf-curator lint, diagram scripts |
| `d2`, `rsvg-convert` (`brew install d2 librsvg`) | architecture diagram render |
| Pillow (`python3 -m pip install Pillow`) | diagram grayscale proof |

Optional later (spine/o1 Java delivery repo only): JDK 17+, Maven/Gradle — for
coding-rules CI seeds. Not required in this design workspace.

---

## 2. Clone and open

```bash
git clone git@github.com:rajnishkhatri/LLM-DRIVEN-MOBILE-TEST-AUTOMATION.git
cd LLM-DRIVEN-MOBILE-TEST-AUTOMATION
```

Open **this folder** as the Cursor / Claude Code workspace root (not a parent).

---

## 3. Provision agent projections (required)

From the **repo root**:

```bash
python3 tooling/skill-sync/skill_sync.py fix
python3 tooling/skill-sync/skill_sync.py check
```

Expected: `SUMMARY: 5 families, 0 drifted, 0 shadow -> exit 0`.

What `fix` syncs (see `tooling/skill-sync/manifest.toml`):

| Family | Source of truth | Projections |
|---|---|---|
| sdd-\* (6) | `tooling/sdd-skills-bundle/` | `.cursor/skills/`, `.claude/skills/` |
| arch-\* (7) | `.cursor/skills/arch-*/` | `.claude/skills/` |
| role cards | `tooling/sdd-roles/kernel/corpus/catalog-projections/claude-code/agents/` | `.claude/agents/` |
| sdd-roles card | `.../claude-code/skills/sdd-roles/` | `.claude/skills/sdd-roles/` |
| coding-rules dist | `tooling/coding-rules-skill/references/` | `tooling/coding-rules-skill/dist/...` (catalog mirror only) |

**Do not** copy Claude conveyor `hooks.json` into `.claude/settings.json` — it
blocks interactive work.

---

## 4. Skills that are already in place (no extra install)

| Skill | Cursor | Claude | Human docs |
|---|---|---|---|
| sdd-\* | `.cursor/skills/sdd-*` | `.claude/skills/sdd-*` | [skills/sdd-usage-guide.md](skills/sdd-usage-guide.md) |
| arch-\* | `.cursor/skills/arch-*` | `.claude/skills/arch-*` | [skills/arch-lifecycle-instructions.md](skills/arch-lifecycle-instructions.md) · SoT under `.cursor/skills/arch-*/` |
| sdd-roles | — | `.claude/agents/` + `.claude/skills/sdd-roles/` | SoT `tooling/sdd-roles/` |
| okf-curator | `.cursor/skills/okf-curator/` | — (use Cursor or run lint CLI) | skill `INSTALL.md` / `FIRST_RUN.md` |
| diagrams | use `docs/skills/generating-architecture-diagrams/` (AGENTS.md points here) | same path / optional copy into agent skills | [skills/generating-architecture-diagrams/SKILL.md](skills/generating-architecture-diagrams/SKILL.md) |

Bindings (already resolved; do not blank them):

- `.sdd/binding.toml` — sdd-\*
- `.arch/binding.toml` — arch-\* (`mobile-test-automation` → `docs/architecture/`)
- `.okf/binding.toml` — okf-curator

---

## 5. Fresh session (required after provision)

Skills register at **session start**. After `fix` / `check`:

1. Quit the current agent chat / window.
2. Re-open this repo in a new Cursor or Claude Code session.
3. Smoke-probe, e.g.:
   - “Load `sdd-lifecycle` and summarize Stage 0.”
   - “Load `arch-lifecycle` and list the six stages.”
   - (Claude) “Use the `specifier` agent — what may you write?”
   - “Point at `docs/skills/generating-architecture-diagrams/SKILL.md`.”

For day-to-day SDD prompts and gate tokens after setup, use
[skills/sdd-lifecycle-instructions.md](skills/sdd-lifecycle-instructions.md).
For arch-\* prompts and gate tokens, use
[skills/arch-lifecycle-instructions.md](skills/arch-lifecycle-instructions.md).

---

## 6. Diagram skill (optional machine tools)

Prereqs in §1. Usage: follow
[skills/generating-architecture-diagrams/INSTALL.md](skills/generating-architecture-diagrams/INSTALL.md)
and `SKILL.md`. This repo keeps the pack under `docs/skills/`; agents should
follow `AGENTS.md` rather than requiring a second copy under `.cursor/skills/`.

---

## 7. coding-rules — not installed here

coding-rules targets the **spine/o1 Java delivery repo**, not this design
workspace. When that repo exists:

```bash
# follow tooling/coding-rules-skill/INSTALL.md (or docs/skills/coding-rules-skill/INSTALL.md)
```

Until then, leave coding-rules off Cursor/Claude in this repo.

---

## 8. okf-curator smoke (optional)

```bash
python .cursor/skills/okf-curator/scripts/okf_lint.py
```

Conventions: [CONVENTIONS.md](CONVENTIONS.md). Binding: `.okf/binding.toml`.

---

## 9. Ongoing hygiene

| When | Command |
|---|---|
| Fresh clone / after pulling skill SoT changes | `python3 tooling/skill-sync/skill_sync.py fix && check` |
| Bound `check_gate` (sdd) | same `check` from repo root |
| Drift reported | `fix`, then new session |
| `SHADOW <name>` advisory | user-scoped `~/.claude/skills` collides; rename/remove user copy if confusing |

---

## 10. Quick map

```
tooling/sdd-skills-bundle/     → sdd-* SoT
.cursor/skills/arch-*/         → arch-* SoT (+ Claude projection)
tooling/sdd-roles/             → roles / conveyor SoT
.cursor/skills/okf-curator/    → OKF SoT
docs/skills/generating-architecture-diagrams/  → diagram SoT
tooling/coding-rules-skill/    → install into spine/o1 later
tooling/skill-sync/            → provision + drift guard
docs/skills/                   → human manuals
docs/SETUP.md                  → this runbook
```
