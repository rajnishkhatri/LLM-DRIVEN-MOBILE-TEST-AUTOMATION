---
type: reference
title: OKF workspace-binding schema
description: >-
  The contract that makes the okf-curator skill portable: the placeholder
  vocabulary, each key's purpose, this repo's reference value, and the prompt a
  foreign workspace answers on first run.
tags: [okf, binding, portability]
---

# OKF workspace-binding schema

> The **contract** that makes the `okf-curator` skill portable. The skill body
> uses `{{placeholder}}` tokens instead of this-repo-specific strings, and the
> bundled scripts (including the OKF lint engine) read the same keys from a
> per-workspace binding at runtime. This file is the single source of the
> vocabulary. Design rationale lives in the skill's home repo as ADR-0039
> (mirroring its `_sdd` predecessor, ADR-0032) — named, not linked: this file
> ships inside the `.skill` archive, where a repo-relative link would dangle.

## Resolution order (how the skill and scripts fill these at runtime)

1. `--binding PATH` (scripts only — explicit flag wins).
2. `.okf/binding.toml` at the workspace root (a foreign repo, once confirmed;
   discovered by walking upward from cwd).
3. `docs/skills/_okf/binding.reference.toml` (THIS repo's committed reference).
4. None present → **first-run auto-adapt** (see [FIRST_RUN.md](FIRST_RUN.md)):
   inspect the ecosystem, propose values, **require human confirmation**, persist
   to `.okf/binding.toml`. The lint engine hard-exits rather than lint a guessed
   bundle set (AP-6: undecidable → ask, never fabricate).

## The vocabulary — `[binding]` (8 keys)

| Key (`{{placeholder}}`) | Abstracts | This-repo reference value | First-run fill-prompt |
|---|---|---|---|
| `conventions_doc` | The OKF convention rules-of-record doc. | `docs/CONVENTIONS_OKF.md` | "Which file pins your knowledge-plane conventions? (create one from the skill's `references/conventions.md` if none)" |
| `lint_gate` | The command humans/agents run as the structural gate. | `python scripts/okf_lint.py` | "What command should run the OKF lint gate? (default: invoke the skill's bundled `scripts/okf_lint.py`)" |
| `docs_home` | The knowledge-plane root directory. | `docs/` | "Which directory is your knowledge-plane root? (e.g. `docs/`, `wiki/`)" |
| `recipes_home` | The parent directory for topic recipe sub-bundles. | `docs/recipes/` | "Where should feature recipes live? `<none>` to file recipes directly in topic bundles." |
| `authored_research_home` | The bundle for authored facts-to-rely-on research. | `research/` | "Where does authored design research live? `<none>` if unused." |
| `evidence_home` | The excluded records-of-what-happened tree. | `docs/research/` | "Where do generated evidence/run artifacts go (excluded from OKF)? `<none>` if you don't split authored vs evidence." |
| `context_mention_prefix` | The load-bearing @-mention form agent context files use. | `@docs/` | "Do your agent context files @-mention docs (e.g. `@docs/…`)? `<none>` if not." |
| `knowledge_globs` | Where the drift check scans for authored knowledge (array). | `["docs/**/*.md", "research/**/*.md"]` | "Which globs cover your authored knowledge files?" |

## The `[lint]` table (5 keys — read by the bundled lint engine)

| Key | Abstracts | This-repo reference value | First-run fill-prompt |
|---|---|---|---|
| `declared_bundles` | The OKF-conformant bundle set (array of dirs). | the 27 declared paths | "Which directories are managed knowledge bundles? (start with one)" |
| `evidence_segments` | Path segments marking generated artifacts to skip. | `["outputs"]` | "Any dir names that mark generated (non-authored) content?" |
| `evidence_suffixes` | Dir-name suffixes marking generated trees to skip. | `["-workspace"]` | "Any dir-name suffixes that mark generated trees?" |
| `run_dir_pattern` | Regex for run-artifact dirs to skip. | `"^run-\\d+$"` | "A regex for run-artifact dir names, if any." |
| `reserved` | Filenames exempt from `type` frontmatter. | `["index.md", "log.md", "README.md"]` | "Which filenames are structural (no frontmatter required)? (default fine)" |

> **`declared_bundles` is REQUIRED.** If the key is absent — including via a
> typo'd table (`[lints]`) or key — the engine exits 2 naming the key and the
> binding file. It does **not** lint zero bundles and report success: that
> would assert a clean tree the binding never declared (AP-6). An explicit
> `declared_bundles = []` is a legal mid-adoption state and prints a
> "no bundles declared" marker. The other four keys default as shown.
>
> **Path values are validated, not trusted.** `declared_bundles` (and
> `[binding].knowledge_globs`) must be a **list of strings** whose entries stay
> **inside the workspace root** — no absolute paths, no `..` segments. A binding
> is discovered by walking upward from cwd and can therefore arrive inside a
> repo you cloned, so it is input, not local configuration. Forgetting the TOML
> brackets (`declared_bundles = "docs/skills"`) is the common typo: a bare
> string is iterable, so it would otherwise split into single characters — one
> of which is `/`, resolving to the filesystem root.

## The `[drift]` table (2 keys — read by the drift report)

| Key | Abstracts | This-repo reference value | First-run fill-prompt |
|---|---|---|---|
| `code_prefixes` | Which changed paths count as *code* worth correlating to docs. | the 12 layer/package prefixes | "Which top-level paths hold the code your docs describe?" |
| `exclude_segments` | Changed-path noise filter for the drift scan. | the 8 evidence segments | "Any path segments the drift scan should ignore?" |

> **`code_prefixes` and `[binding].knowledge_globs` are REQUIRED by the drift
> report** (exit 2 when absent, same rule as above — without them the scan
> matches nothing and would report "no code changed" / "no docs reference the
> changed paths"). Passing `--paths` supplies the code scope directly and
> substitutes for `code_prefixes`. `exclude_segments` is optional.

## Optional `[examples]` section

Workspace-specific illustrations the portable body references generically —
absent in a foreign workspace, the skill uses the generic phrasing with no
concrete instance (same mechanism as the `_sdd` contract).

| `[examples]` key | Reference value (this repo) |
|---|---|
| `topic_bundles` | `gcp, governance, guardrails, goaljudge, memory_extractor` |
| `cross_cutting_recipes` | recipes 11–15 (fixes spanning several subsystems) — the flat-root exception |
| `depth_worked_values` | depth-to-root 2 for a `docs/recipes/<topic>/` bundle; 1 for root `research/` |
| `drift_scope_pair` | `services/ orchestration/` as a `--paths` subsystem-scoping example |
| `recipe_walkthrough` | Recipe 4 — an end-to-end telemetry-pipeline validation runbook (governance topic) |
