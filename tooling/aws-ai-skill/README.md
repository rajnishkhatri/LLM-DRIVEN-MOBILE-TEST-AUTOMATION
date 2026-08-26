# aws-ai-* skill — packaging workshop

This directory is **not a live skill surface**. It is the workshop that builds
the portable, distributable form of the `aws-ai-*` family. Nothing here is
auto-discovered or executed by Claude Code or Cursor.

## Where the family actually lives

| Surface | Path | Who reads it |
|---|---|---|
| Source of truth | `.cursor/skills/aws-ai-*/` | Cursor (and skill-sync) |
| Projection | `.claude/skills/aws-ai-*/` | Claude Code |
| Human how-to | `docs/skills/aws-ai-lifecycle-instructions.md` | you |
| **Portable bundle (here)** | `tooling/aws-ai-skill/dist/` | installs elsewhere |

The in-repo surfaces are provisioned + drift-guarded by
`tooling/skill-sync/` (`python3 tooling/skill-sync/skill_sync.py check`). Edit
the **Cursor source**, then `skill_sync.py fix` re-projects to Claude. This
workshop only rebuilds the distributable — it never edits the source.

## Build

```bash
tooling/aws-ai-skill/package.sh
```

Produces, under `dist/`:

- `aws-ai-family.zip` — all six skill dirs as **siblings**; the one-shot portable
  install. (Covered by the repo's `*.zip` gitignore — it is a build convenience,
  always regenerable from source.)
- `aws-ai-<member>.skill` × 6 — one single-skill zip each (top-level `<name>/` +
  `SKILL.md`), matching this repo's `.skill` format (cf.
  `tooling/coding-rules-skill/dist/coding-rules.skill`), for the claude.ai
  "add skill" / profile-install flow. These are the committed distributables.

**Rebuild after any skill edit** (and after `skill_sync.py fix`) so the bundle
never drifts from source.

## Why the family travels together

The five stage skills resolve the router's shared knowledge via **relative
sibling paths** — e.g. `aws-ai-assess/SKILL.md` cites
`../aws-ai-lifecycle/references/bedrock.md`. So the six dirs MUST install as
siblings under one `skills/` parent. A lone stage skill has dangling references.
Installation details: [INSTALL.md](INSTALL.md).

## What's in / out of the bundle

- **In:** each `SKILL.md`; the router's `FIRST_RUN.md`, `binding.template.toml`,
  `binding.schema.md`, and all six `references/*.md`; the bundled runnable
  `scripts/` (deploy CDK app, validate offline harness) that the skill bodies
  reference.
- **Out:** `evals/` (dev-only benchmark rubric), `__pycache__`, `.pytest_cache`,
  `*.pyc`, `.DS_Store`.
