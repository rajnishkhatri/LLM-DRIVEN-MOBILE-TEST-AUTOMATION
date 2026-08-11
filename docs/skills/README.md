# Skills — human index

This folder is the **human** surface for skill manuals and the portable
diagram pack. Agent projections live under `.cursor/skills/` and
`.claude/skills/` (provisioned by `tooling/skill-sync/`). Do not maintain a
third divergent copy of arch/sdd skill trees here.

**First-time / clone setup:** [../SETUP.md](../SETUP.md)

## Instruments

| Family | What it does | Source of truth | How to invoke |
|---|---|---|---|
| **sdd-\*** (6) | Spec-driven development lifecycle | `tooling/sdd-skills-bundle/` | Chat: `sdd-lifecycle` / stage skills; **how-to:** [sdd-lifecycle-instructions.md](sdd-lifecycle-instructions.md); full manual: [sdd-usage-guide.md](sdd-usage-guide.md) |
| **arch-\*** (7) | Architecture workflow (characteristics → validate) | `.cursor/skills/arch-*/` | Chat: `arch-lifecycle`; **how-to:** [arch-lifecycle-instructions.md](arch-lifecycle-instructions.md); projected to `.claude/skills/` |
| **sdd-roles** | Role cards + conveyor kernel | `tooling/sdd-roles/` | Claude: `.claude/agents/`; kernel card `.claude/skills/sdd-roles/` |
| **coding-rules** | ADR-backed coding rules for the Java delivery repo | `tooling/coding-rules-skill/` | Install into spine/o1 per [coding-rules-skill/INSTALL.md](coding-rules-skill/INSTALL.md) — not mounted in this design repo |
| **diagrams** | C4 IR → D2 → linted SVG | `docs/skills/generating-architecture-diagrams/` | Chat or human: [generating-architecture-diagrams/SKILL.md](generating-architecture-diagrams/SKILL.md) |
| **okf-curator** | Knowledge-plane curation + lint | `.cursor/skills/okf-curator/` | Chat: okf-curator; lint via `.okf/binding.toml` |

## Workspace machinery

| Tool | Path | Role |
|---|---|---|
| **skill-sync** | `tooling/skill-sync/` | Provision projections + drift guard (`check_gate`) |

```bash
python3 tooling/skill-sync/skill_sync.py fix
python3 tooling/skill-sync/skill_sync.py check
```

## Operator manuals

| Doc | Use when |
|---|---|
| [sdd-lifecycle-instructions.md](sdd-lifecycle-instructions.md) | Running SDD **in this repo** — binding paths, gate tokens, copy-paste prompts |
| [arch-lifecycle-instructions.md](arch-lifecycle-instructions.md) | Running arch-\* **in this repo** — binding paths, gate tokens, copy-paste prompts |
| [sdd-usage-guide.md](sdd-usage-guide.md) | Full playbook across sdd / arch / roles / coding-rules |
