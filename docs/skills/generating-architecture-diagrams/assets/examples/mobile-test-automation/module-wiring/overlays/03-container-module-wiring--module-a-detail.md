# C2b - Container drill-down: module wiring — module-a overlay — detail tables

> This view is a subset of `03-container-module-wiring` opening `APP` — only the edges owned by `module-a`. Edge numbers match the primary; see `03-container-module-wiring` for the complete edge set.

**Locator:** this view opens `APP` from `03-container-module-wiring`. It is a **subset** of `03-container-module-wiring` — not the complete edge set.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 1 | MA | Conversion (cluster A) - 10 components incl. the Invoke Models seam. Only MA holds the gateway credential; drawn properly in C2d. |
| 2 | PG | WORKING ASSUMPTION (spine C3); dev/CI embedded or containerized, ephemeral-only (D1, M40). Schemas: conversion-state; lineage (append-only: app role INSERT/SELECT only, per-conversion hash chain, supersede-not-update - ADR 0012); outbox+queue (bounded retries, dead-letter quarantine - M21); judge-response cache (M27, CF7). No cross-lifecycle foreign keys (F4, ADR 0006). |
| 3 | OBJ | Evidence object storage behind an S3-compatible port (ADR 0011). Dev/CI: containerized MinIO; production BINDING PROBE-PENDING (week-0 platform probe; default = self-operated MinIO). Write-once / object-lock REQUIRED - ADR 0012's precondition, deployment-checked. Holds: classified artifacts + retention classes (M39); canonicalized source snapshots (M15); lineage chain anchors (ADR 0012). Envelope encryption + crypto-shredding before the first audit-retained artifact (ADR 0011 as amended). |
| 4 | SEC | Interim: CI secret store; the vault is named by the M33 controls-baseline read - PENDING. All credentials resolved by injected reference, never literals (M34/CF8). |
| 5 | GIT | Prompts / exemplars / golden set / test code; version identity is free. |
| 6 | GW | Same standing as the C1 node-detail table (E4). Model providers hosted INSIDE the bank - prompts never leave (E4); version-report contract UNVERIFIED (M5 held). |
| 7 | OCT | Same standing as the C1 node-detail table (E5). At BOTH ends of the pipeline (E5): ingest source AND publish target; asset-versioning UNVERIFIED (M7 held). |
| 8 | XLS | Same standing as the C1 node-detail table (E3/S9). File input originating from bank teams inside the network (E3/S9). |

## Edge detail

| # | Edge | Mode | Claim |
|---|------|------|-------|
| 6 | MA → PG | sync | State + lineage, same local transaction (ADR 0007) |
| 9 | MA → OBJ | sync | Canonicalized source snapshots (M15) |
| 12 | MA → SEC | sync | Gateway credential, by injected reference (M34) |
| 14 | MA → GIT | sync | Versioned assets (prompts / exemplars / golden set / test code) |
| 19 | MA → GW | sync | Model calls (P2) via the Invoke Models seam |
| 21 | MA → OCT | sync | Manual-test ingest, API-key; hash-at-ingest (M15) |
| 23 | MA → XLS | sync | Workbook file input; raw workbooks never enter Git (M35) |

