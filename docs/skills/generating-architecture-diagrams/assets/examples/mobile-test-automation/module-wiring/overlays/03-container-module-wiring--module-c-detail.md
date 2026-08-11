# C2b - Container drill-down: module wiring — module-c overlay — detail tables

> This view is a subset of `03-container-module-wiring` opening `APP` — only the edges owned by `module-c`. Edge numbers match the primary; see `03-container-module-wiring` for the complete edge set.

**Locator:** this view opens `APP` from `03-container-module-wiring`. It is a **subset** of `03-container-module-wiring` — not the complete edge set.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 2 | MC | Evidence (cluster C) - Preserve Provenance + metrics read model + auditor export. Only MC anchors the lineage chain. |
| 3 | PG | WORKING ASSUMPTION (spine C3); dev/CI embedded or containerized, ephemeral-only (D1, M40). Schemas: conversion-state; lineage (append-only: app role INSERT/SELECT only, per-conversion hash chain, supersede-not-update - ADR 0012); outbox+queue (bounded retries, dead-letter quarantine - M21); judge-response cache (M27, CF7). No cross-lifecycle foreign keys (F4, ADR 0006). |
| 4 | OBJ | Evidence object storage behind an S3-compatible port (ADR 0011). Dev/CI: containerized MinIO; production BINDING PROBE-PENDING (week-0 platform probe; default = self-operated MinIO). Write-once / object-lock REQUIRED - ADR 0012's precondition, deployment-checked. Holds: classified artifacts + retention classes (M39); canonicalized source snapshots (M15); lineage chain anchors (ADR 0012). Envelope encryption + crypto-shredding before the first audit-retained artifact (ADR 0011 as amended). |

## Edge detail

| # | Edge | Mode | Claim |
|---|------|------|-------|
| 5 | AUD → MC | sync | Versioned export; itself an attributable lineage event (CF11) |
| 8 | MC → PG | sync | Append-only lineage writes + read-model reads |
| 11 | MC → OBJ | sync | Chain-head anchors at interval; a stale anchor is an alert (ADR 0012) |

