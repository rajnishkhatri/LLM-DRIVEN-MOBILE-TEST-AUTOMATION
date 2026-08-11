# Architecture artifacts — delivery projects

Stage artifacts produced by the `arch-*` skill family for **delivery projects**, kept
here in the published `docs/` tree rather than in `.arch/`.

## Why the split

`.arch/` holds the practice katas (`silicon-sandwiches`, `going-going-gone`) and review
records. Those are finished study artifacts and should stay put. A live project's
artifacts get revised repeatedly and ship alongside the rest of `docs/`, so they are
decoupled into this tree. The decoupling is declared in `.arch/binding.toml`:

```toml
[roots]
mobile-test-automation = "docs/architecture/"
```

Any target listed under `[roots]` resolves every `{{*_home}}` beneath that root.
Targets not listed keep the `.arch/` homes. `.arch/binding.toml` itself stays where the
skills look for it — only artifacts move.

## Layout

The folder structure mirrors `.arch/` exactly, so nothing about the skills' namespacing
changes:

| Binding key | Path here | Stage |
|---|---|---|
| `worksheet_home` | `worksheets/<target>/` | 1 (characteristics), 3 (style decision) |
| `component_home` | `components/<target>/` | 2 (logical components), 6 (diagram set) |
| `adr_home` | `adrs/<scope>/<target>/` | 4 (ADRs; `scope` = `common`/`application`/`integration`/`enterprise`) |
| `risk_home` | `risk/<target>/` | 5 (risk report) |

Directories are created as their stage first produces an artifact.

## OKF shape

This directory is a declared OKF bundle (`[lint].declared_bundles` in
`.okf/binding.toml`). Concepts are nested under the artifact homes above rather than
sitting flat, so the catalog is generated recursively:

```bash
python .cursor/skills/okf-curator/scripts/make_bundle.py docs/architecture \
    --title "Architecture artifacts — delivery projects" --recurse-index \
    --note "<what changed>"
python .cursor/skills/okf-curator/scripts/okf_lint.py   # gate: exit 0
```

Two things to know before regenerating: the generated catalog is plain alphabetical,
so re-group [index.md](index.md) by target and stage afterwards; and `make_bundle.py`
re-seeds `log.md` from `--note`, so preserve the existing entries by hand.

Every new stage artifact needs `type` frontmatter (`type: architecture`, plus `title`,
`description`, `tags`) or the gate warns.

## Current targets

The per-target catalog lives in [index.md](index.md). Upstream research premises for
`mobile-test-automation` live in `docs/research/`.
