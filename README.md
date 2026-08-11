# LLM-Driven Mobile Test Automation

Design workspace for the **mobile-test-automation / spine / O7** ecosystem:
ADRs, architecture worksheets, research, SDD specs/plans, and the agent skill
surfaces used to evolve that design.

## What lives here

- `docs/architecture/` — MTA ADRs, components, worksheets, presentations, risk, O7 explainers
- `docs/sdd/` — specs and plans (MTA/spine/O7 plus sdd-roles / skill-sync tooling history)
- `docs/research/` — pipeline options (o1–o7), spine studies, mocks
- `cases/coding-rules/` — OKF bundle (includes junior-clean-architecture)
- `tooling/` — skill sources of truth (sdd-*, sdd-roles, coding-rules, skill-sync)
- `.cursor/` / `.claude/` — Cursor and Claude Code skill projections

## How to use the skills

Start with the human operator manual:

**[`docs/skills/sdd-usage-guide.md`](docs/skills/sdd-usage-guide.md)**

Skill index: [`docs/skills/README.md`](docs/skills/README.md)

On a fresh clone, provision projections:

```bash
python3 tooling/skill-sync/skill_sync.py fix
python3 tooling/skill-sync/skill_sync.py check
```

Then open a **fresh** Cursor or Claude Code session (skills register at session start).

## Cutover note

Content was copied from the Architect study workspace on 2026-08-11. **This
repo is the canonical home** for MTA / spine / O7 design going forward;
Architect copies of these paths should be treated as stale after that date.

## Staged spine root files

`docs/sdd/plans/spine-repo/` holds `AGENTS.md` / `CLAUDE.md` ready to copy into
the future spine **code** repository. They do not govern this design workspace.
