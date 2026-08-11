# Skills — human index

This folder is the **human** surface for skill manuals and the portable
diagram pack. Agent projections live under `.cursor/skills/` and
`.claude/skills/` (provisioned by `tooling/skill-sync/`). Do not maintain a
third divergent copy of arch/sdd skill trees here.

## Instruments

| Family | What it does | Source of truth | How to invoke |
|---|---|---|---|
| **sdd-\*** (6) | Spec-driven development lifecycle | `tooling/sdd-skills-bundle/` | Chat: `sdd-lifecycle` / stage skills; manual: [sdd-usage-guide.md](sdd-usage-guide.md) |
| **arch-\*** (7) | Architecture workflow (characteristics → validate) | `.cursor/skills/arch-*/` | Chat: `arch-lifecycle`; projected to `.claude/skills/` |
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

## Operator manual

[sdd-usage-guide.md](sdd-usage-guide.md) — when to play which instrument across the lifecycle.
