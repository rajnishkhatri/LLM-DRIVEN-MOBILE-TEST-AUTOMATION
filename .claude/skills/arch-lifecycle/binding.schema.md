# `.arch/binding.toml` schema

One shared binding for the whole arch-* family, at the repo root. All keys are
strings; `<none>` disables the seam and dependent steps are skipped.

| Key | Meaning | Default |
|---|---|---|
| `methodology_source` | Path to the Fundamentals of Software Architecture notes bundle (or equivalent methodology docs) that stage skills cite. | `cases/ArchitectureBook` |
| `constitution` | Workspace architecture principles file consulted before every human gate. | `<none>` |
| `worksheet_home` | Directory for characteristics worksheets, quantum maps, and style decisions. | `.arch/worksheets/` |
| `component_home` | Directory for logical-architecture artifacts (component tables + diagrams). | `.arch/components/` |
| `adr_home` | Directory for Architecture Decision Records. Layout: `common/`, `application/<app>/`, `integration/`, `enterprise/` (`arch-decisions.md:227-248`). | `.arch/adrs/` |
| `risk_home` | Directory for risk assessments and risk-storming session records. | `.arch/risk/` |
| `diagram_notation` | Notation for emitted diagrams (`mermaid` recommended; C4-flavored). | `mermaid` |
| `breadth_read_tool` | Read-only exploration tool used for review-mode evidence sweeps. | `explore subagent` |

First-run resolution order: `.arch/binding.toml` → propose from this schema's
defaults → human confirms → persist with a `# confirmed <date>` header.
