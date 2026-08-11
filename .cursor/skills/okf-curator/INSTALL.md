---
type: runbook
title: Portable okf-curator skill — install into any workspace
description: >-
  How to install the workspace-neutral OKF knowledge-plane curator (with its
  bundled lint engine) into any repo and any coding agent.
tags: [okf, binding, portability]
---

# Portable `okf-curator` skill — install into any workspace

One skill that keeps a repo's written knowledge plane **true and extractable**:
document shipped work as recipes, file research where it stays findable, check
docs for staleness against recent code, move docs with full reference
rewriting, and hold the whole tree to a structural lint gate. The gate is
**bundled** — `scripts/okf_lint.py` inside the skill is a pure-stdlib engine
driven by your binding, so an adopting workspace needs **nothing pre-existing**.

## What's in the archive

```
okf-curator/
├── SKILL.md                  ← the methodology (placeholder-ized, portable)
├── binding.template.toml     ← copy to .okf/binding.toml and fill
├── binding.schema.md         ← the 15-key vocabulary + fill-prompts
├── FIRST_RUN.md              ← the inspect→propose→confirm→persist flow
├── references/               ← conventions model, recipe template, gotchas log
└── scripts/
    ├── okf_lint.py           ← the bundled OKF lint engine (the gate)
    ├── _binding.py           ← shared binding loader (--binding / .okf/ discovery)
    ├── add_frontmatter.py    ← typed-frontmatter prepender
    ├── make_bundle.py        ← index.md + log.md generator
    ├── drift_report.py       ← changed-code → mentioning-docs report
    └── relocate.py           ← git mv + full reference rewrite
```

## Install (pick your coding agent)

### Claude Code
```bash
# project-scoped (checked into the repo) …
cp -r okf-curator <your-repo>/.claude/skills/
# … or user-scoped (all your projects)
cp -r okf-curator ~/.claude/skills/
```

### Cursor
```bash
cp -r okf-curator <your-repo>/.cursor/skills/
```

### GitHub Copilot
```bash
mkdir -p <your-repo>/docs/skills <your-repo>/.github/instructions
cp -r okf-curator <your-repo>/docs/skills/
printf -- '---\napplyTo: "**"\n---\n\nSee `docs/skills/okf-curator/SKILL.md` for the okf-curator skill.\n' \
    > <your-repo>/.github/instructions/okf-curator.instructions.md
```

### Any other agent
The skill is plain Markdown + stdlib Python. Put `okf-curator/` wherever your
agent reads instructions from; the scripts run with any Python ≥3.11
(`tomllib`) and no third-party dependency.

## First run — bind to your workspace (one time)

The body's `{{placeholder}}` tokens and the scripts' config resolve from
`.okf/binding.toml` at your repo root. Either let first-run auto-adapt propose
one (see `FIRST_RUN.md` — inspect → propose → **your confirmation** → persist),
or fill it yourself:

```bash
mkdir -p <your-repo>/.okf
cp binding.template.toml <your-repo>/.okf/binding.toml
# edit: replace every <fill>; "<none>" for what your workspace doesn't have.
```

Minimal viable binding — the three that matter most:

```toml
[binding]
conventions_doc = "docs/CONVENTIONS.md"   # your knowledge-format rules doc
docs_home       = "docs/"
lint_gate       = "python .claude/skills/okf-curator/scripts/okf_lint.py"

[lint]
declared_bundles = ["docs/notes"]         # start with ONE bundle; grow it
```

**Safety property:** with no binding at all, the lint engine **hard-exits**
pointing at `FIRST_RUN.md` — it never lints a guessed bundle set.

## Verify it took

```bash
python <skills-path>/okf-curator/scripts/okf_lint.py --root <your-repo>
```

Exit 0 with a `N bundle(s), … 0 failure(s)` summary = bound and working. Then
ask your agent to "document what we just shipped" — the skill routes it through
Routine 1 (recipe) and ends by running this same gate.
