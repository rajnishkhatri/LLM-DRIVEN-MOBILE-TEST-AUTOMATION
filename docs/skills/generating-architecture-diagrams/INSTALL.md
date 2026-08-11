---
type: runbook
title: Portable generating-architecture-diagrams skill — install into any agent
description: >-
  How to install the workspace-neutral C4 diagram-generation skill (with its
  bundled D2 renderer + deterministic linter) into any repo and any coding agent.
tags: [diagrams, c4, d2, portability]
---

# Portable `generating-architecture-diagrams` skill — install anywhere

One skill that turns an architecture spec into a C4-flavored diagram set and
**proves its own correctness**: fact-frozen IR → deterministic D2 render →
grayscale proof → deterministic linter → self-audit. The renderer and the
linter are **bundled** — `scripts/` is plain stdlib Python plus the `d2` CLI, so
an adopting workspace needs nothing pre-existing beyond the three tools below.

## What's in the folder

```
generating-architecture-diagrams/
├── SKILL.md                        ← the methodology + the driver (man page)
├── INSTALL.md                      ← this file
├── references/                     ← shape-vocabulary, line-semantics,
│                                     honesty-tags, ir-schema, readability,
│                                     acceptance-checklist, d2-classes.d2
├── scripts/
│   ├── ir_to_d2.py                 ← IR → D2 (classes) + combined view.md
│   ├── decompose.py                ← density-triggered primary + overlays
│   ├── render.sh                   ← driver: IR → D2 → SVG → @2x PNG → gray
│   │                                 proof → view.md; decomposes dense views,
│   │                                 renders overlays, runs the set-level lint
│   ├── grayscale_proof.py          ← Pillow desaturate
│   ├── lint_diagram.py             ← the deterministic gate (per-view + set)
│   └── test_c4_signals.py          ← C4-Book signal tests (22 asserts)
├── evals/evals.json                ← the eval prompts (dev-only; safe to omit)
└── assets/
    ├── self-audit-template.md
    └── examples/
        ├── silicon-sandwiches/     ← worked Context-view slice + SELF-AUDIT.md
        └── mobile-test-automation/ ← decomposition example (primary + overlays)
```

## Prerequisites (one time, per machine)

```bash
brew install d2 librsvg          # macOS; d2 + rsvg-convert
python3 -m pip install Pillow    # any OS
```

Linux: install `d2` from https://d2lang.com, `rsvg-convert` via
`apt-get install librsvg2-bin`, and `Pillow` via pip.

## Install (pick your coding agent)

### Claude Code
```bash
# project-scoped (checked into the repo) …
cp -r generating-architecture-diagrams <your-repo>/.claude/skills/
# … or user-scoped (all your projects)
cp -r generating-architecture-diagrams ~/.claude/skills/
```

### Cursor
```bash
cp -r generating-architecture-diagrams <your-repo>/.cursor/skills/
```

### GitHub Copilot
```bash
mkdir -p <your-repo>/docs/skills <your-repo>/.github/instructions
cp -r generating-architecture-diagrams <your-repo>/docs/skills/
printf -- '---\napplyTo: "**"\n---\n\nSee `docs/skills/generating-architecture-diagrams/SKILL.md` for the architecture-diagram skill.\n' \
    > <your-repo>/.github/instructions/generating-architecture-diagrams.instructions.md
```

### Any other agent
The skill is plain Markdown + stdlib Python + the `d2` CLI. Put the folder
wherever your agent reads instructions from and point it at `SKILL.md`. The
scripts run with any Python ≥3.8 and Pillow; no other third-party dependency.

## Verify it took

```bash
cd <skills-path>/generating-architecture-diagrams
bash scripts/render.sh assets/examples/silicon-sandwiches/ir.json assets/examples/silicon-sandwiches
python3 scripts/lint_diagram.py \
  --ir assets/examples/silicon-sandwiches/ir.json \
  --svg assets/examples/silicon-sandwiches/01-context.svg \
  --d2 assets/examples/silicon-sandwiches/01-context.d2 \
  --proof assets/examples/silicon-sandwiches/proofs/01-context-gray.png \
  --detail assets/examples/silicon-sandwiches/01-context-detail.md
```

The `--detail` flag is required: the linter's key check fails without it (any
non-trivial view must carry a key). A clean run prints

```
PASS  01-context: 35/35 canvas labels verbatim, 0 relocated facts, 21 <text> elements, 0 failure(s)
```

and exits 0 = installed and working. Then ask your agent to "diagram this
architecture" and it routes through the IR → render → lint → self-audit loop.
