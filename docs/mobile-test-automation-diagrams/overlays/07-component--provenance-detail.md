# C3a — Component view: module flow — provenance overlay — detail tables

> This view is a subset of `07-component` opening `APP` — only the provenance/lineage writes into the append-only store. Edge numbers match the primary; see `07-component` for the complete edge set.

**Locator:** this view opens `APP` from `07-component`. It is a **subset** of `07-component` — not the complete edge set.

## Node detail (keyed by node ID)

| Node | Detail the short label hides |
|------|------------------------------|
| AUDITOR | Must reconstruct verdicts from stored evidence alone, without access to the running system (ADR 0008) |
| PRESERVE_PROVENANCE | Append-only hash-chained lineage, CA=13 (ADR 0012); + metrics read model + auditor export (ADR 0008, CF11) |
| LEAD | Read-only metrics |

## Edge detail

| # | Edge | Mode | Claim |
|---|------|------|-------|
| 4 | AUDITOR → PRESERVE_PROVENANCE | sync | versioned export |
| 5 | LEAD → PRESERVE_PROVENANCE | sync | metrics |

## Key

- stadium/pill = a person or role (actor)
- rectangle = a grouping of code inside a container (C4 component)
- module-c colour = the same module tracked by colour across every view
- solid arrow = synchronous call
- `[Type]` under a name = the element's C4 type (container/component)

