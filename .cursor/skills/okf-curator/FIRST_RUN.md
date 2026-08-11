---
type: runbook
title: OKF curator first run — bind the skill to your workspace
description: >-
  The inspect → propose → confirm → persist flow that adapts the portable
  okf-curator skill (and its bundled lint engine) to a new workspace.
tags: [okf, binding, portability]
---

# First run in a new workspace — bind the OKF curator to your ecosystem

The `okf-curator` skill is **workspace-neutral**: its body uses `{{placeholder}}`
tokens instead of any one repo's paths, and its bundled scripts — including the
**OKF lint engine** — read the same values from a per-workspace binding. Before
the skill can run here, those placeholders need your workspace's real values.

## Resolution order (what the skill and scripts check, in order)

1. `--binding PATH` — an explicit flag on any bundled script wins.
2. **`.okf/binding.toml`** at your repo root — the resolved binding for this
   workspace. If present and filled, used directly.
3. A committed **reference** binding shipped with the skill's home repo
   (`docs/skills/_okf/binding.reference.toml`) — only relevant inside that repo.
4. **None present → first-run auto-adapt** (below). The lint engine **hard-exits**
   with a pointer to this file rather than lint a guessed bundle set —
   undecidable → ask, never fabricate.

## First-run auto-adapt — inspect → propose → confirm → persist

When no binding is found, the skill does **not** guess and run. It:

1. **Inspects your ecosystem** for markers of each binding key:
   - `conventions_doc` → an existing conventions/knowledge-format doc; if none,
     propose creating one from the skill's `references/conventions.md`.
   - `docs_home` / `recipes_home` → `docs/`, `wiki/`, an existing recipe or
     runbook dir.
   - `authored_research_home` / `evidence_home` → a research/notes dir vs a
     generated-outputs dir, or `<none>` if the workspace doesn't split them.
   - `context_mention_prefix` → `@`-mention conventions in `AGENTS.md` /
     `CLAUDE.md` / `.cursorrules`, else `<none>`.
   - `[lint].declared_bundles` → **start with one bundle** — the dir the user
     most wants curated; grow the list as dirs are promoted.
   - `[drift].code_prefixes` → the top-level source dirs (`src/`, `lib/`,
     package dirs).
2. **Proposes** a filled `binding.toml` — every key with its detected value (or
   `<none>`), shown to you.
3. **Requires your confirmation.** You edit or approve. The lint engine never
   runs against a guessed bundle list, and no `<none>` is silently invented.
4. **Persists** the confirmed binding to `.okf/binding.toml`. Subsequent runs
   skip straight to step 2 of the resolution order.

## Graceful degradation

A key set to `<none>` means that rule has no workspace analog — the skill
**skips** it and says so in output (e.g. no `evidence_home` → the
authored-vs-evidence filing rule collapses to the authored home; no
`context_mention_prefix` → the move-safety @-mention rewrite is a no-op).
An empty `declared_bundles` lints zero bundles and prints exactly that —
honest output, never fabricated coverage.

## Files in this bundle

- `binding.schema.md` — the 15-key vocabulary + fill-prompts (the contract).
- `binding.template.toml` — copy to `.okf/binding.toml` and fill (or let
  first-run fill it).
- `binding.reference.toml` — the home repo's own values (a worked example;
  not shipped in the portable archive).
