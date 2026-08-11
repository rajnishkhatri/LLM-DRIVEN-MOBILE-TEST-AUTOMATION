# Agent guidance for this workspace

Portable, tool-neutral pointers for any coding agent working in this repo.

This repository is the **design workspace** for LLM-driven mobile test
automation: the O7 pipeline, the spine ecosystem, and related ADRs / SDD
artifacts. It is not the Java delivery (spine / o1) code repo.

## Architecture diagrams

To draw, redraw, or render a system's **C4-flavored architecture diagrams**
(context / container / component), or to produce a presentation-grade diagram
set, use the skill at:

**`docs/skills/generating-architecture-diagrams/SKILL.md`**

It gives you a fact-frozen IR, a reserved shape vocabulary, verbatim labels,
honesty tags (never invent SLAs / vendors / regions / counts), a deterministic
D2 render (`scripts/render.sh`), and a deterministic linter
(`scripts/lint_diagram.py`) that must pass before a diagram is considered done.
Install/usage details are in the skill's `INSTALL.md`.

## Architecture workflow (design, not just drawing)

For the broader software-architect workflow — deriving characteristics,
component design, style/quanta selection, ADRs, risk storming, validation — see
the `arch-*` skill family under `.cursor/skills/` (router: `arch-lifecycle`).
Workspace how-to (prompts, gates, paths):
`docs/skills/arch-lifecycle-instructions.md`. Delivery-project artifacts for
`mobile-test-automation` root under `docs/architecture/` (see
`.arch/binding.toml` `[roots]`).

## Spec-driven development

For the 10-stage SDD lifecycle, see `sdd-lifecycle` (SoT:
`tooling/sdd-skills-bundle/`). Workspace how-to (prompts, gates, paths):
`docs/skills/sdd-lifecycle-instructions.md`. Full operator manual:
`docs/skills/sdd-usage-guide.md`. Bindings: `.sdd/binding.toml`.

## Spine repo root files (staged data)

`docs/sdd/plans/spine-repo/{AGENTS.md,CLAUDE.md}` are **staged copies for the
future spine code repository**, not instructions for *this* workspace. Do not
treat them as governing this repo until they are landed in that code repo.

## Skill surfaces

| Surface | Where |
|---|---|
| Cursor | `.cursor/skills/` |
| Claude Code | `.claude/skills/` + `.claude/agents/` |
| Human manuals | `docs/skills/` |

Re-provision / drift-check: `python3 tooling/skill-sync/skill_sync.py fix` then
`check` (from repo root).
