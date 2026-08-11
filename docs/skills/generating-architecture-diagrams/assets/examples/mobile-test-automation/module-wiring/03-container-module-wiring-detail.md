# C2b - Container drill-down: module wiring — detail tables

> Which module owns which store/external edge? This view opens the APP box from C2a into its three modules; every rolled-up C2a edge reappears here at module grain. Canvas carries numbered edge refs only (1-23); the full claim lives in the edge-detail table keyed by number. This is the completeness reference for module-granular edges - the C2c-e overlays each repeat a subset of it.

**Locator:** this view opens `APP` from `C2a`. It is a **completeness reference** at this grain.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 5 | APP | Module boundaries are the three clusters, NOT the blueprint's five pipeline stages (ADR 0005). Drawn opaque in C2a; opened at module grain in C2b and at component grain in C3a. |
| 6 | MA | Conversion (cluster A) - 10 components incl. the Invoke Models seam. Only MA holds the gateway credential; drawn properly in C2d. |
| 7 | MB | Validation-certification (cluster B) - 5 components; static gate to device gate to classify to certify. Device-gate worker holds NO gateway credential (ADR 0013). |
| 8 | MC | Evidence (cluster C) - Preserve Provenance + metrics read model + auditor export. Only MC anchors the lineage chain. |
| 9 | WEB | One authenticated internal API, no BFF (ADR 0008). SSO against the bank IdP is a HARD requirement, not a nice-to-have (M37). The ONLY UI in Phase 1. |
| 10 | PG | WORKING ASSUMPTION (spine C3); dev/CI embedded or containerized, ephemeral-only (D1, M40). Schemas: conversion-state; lineage (append-only: app role INSERT/SELECT only, per-conversion hash chain, supersede-not-update - ADR 0012); outbox+queue (bounded retries, dead-letter quarantine - M21); judge-response cache (M27, CF7). No cross-lifecycle foreign keys (F4, ADR 0006). |
| 11 | EXEC | Test-execution process, spawned per device run. Separate OS process - shape committed NOW, sandbox technology weeks 3-8 (ADR 0013). NO long-lived credentials; single-run device session token; NEVER the gateway credential. Static capability rules gate entry (supplement, not the control). |
| 12 | SEC | Interim: CI secret store; the vault is named by the M33 controls-baseline read - PENDING. All credentials resolved by injected reference, never literals (M34/CF8). |
| 13 | OBJ | Evidence object storage behind an S3-compatible port (ADR 0011). Dev/CI: containerized MinIO; production BINDING PROBE-PENDING (week-0 platform probe; default = self-operated MinIO). Write-once / object-lock REQUIRED - ADR 0012's precondition, deployment-checked. Holds: classified artifacts + retention classes (M39); canonicalized source snapshots (M15); lineage chain anchors (ADR 0012). Envelope encryption + crypto-shredding before the first audit-retained artifact (ADR 0011 as amended). |
| 14 | GIT | Prompts / exemplars / golden set / test code; version identity is free. |
| 15 | PERF | Same standing as the C1 node-detail table (E1/E2). INCUMBENT vendor - MSA on file, unread (E1); flows run on mock/synthetic data (E2); NOT covered by E3. |
| 16 | GW | Same standing as the C1 node-detail table (E4). Model providers hosted INSIDE the bank - prompts never leave (E4); version-report contract UNVERIFIED (M5 held). |
| 17 | OCT | Same standing as the C1 node-detail table (E5). At BOTH ends of the pipeline (E5): ingest source AND publish target; asset-versioning UNVERIFIED (M7 held). |
| 18 | XLS | Same standing as the C1 node-detail table (E3/S9). File input originating from bank teams inside the network (E3/S9). |

## Edge detail

| # | Edge | Mode | Claim |
|---|------|------|-------|
| 1 | QA → APP | sync | 2 CLIs (ingestion + hierarchy-tool), no BFF (ADR 0008) |
| 2 | REV → WEB | async | Review queue; human latency, hours-days |
| 3 | LEAD → WEB | sync | Read-only metrics dashboard |
| 4 | WEB → APP | sync | One authenticated internal API; SSO against bank IdP (M37) |
| 5 | AUD → MC | sync | Versioned export; itself an attributable lineage event (CF11) |
| 6 | MA → PG | sync | State + lineage, same local transaction (ADR 0007) |
| 7 | MB → PG | sync | State + lineage, same local transaction (ADR 0007) |
| 8 | MC → PG | sync | Append-only lineage writes + read-model reads |
| 9 | MA → OBJ | sync | Canonicalized source snapshots (M15) |
| 10 | MB → OBJ | sync | Classified artifacts + retention class (ADR 0006, M39) |
| 11 | MC → OBJ | sync | Chain-head anchors at interval; a stale anchor is an alert (ADR 0012) |
| 12 | MA → SEC | sync | Gateway credential, by injected reference (M34) |
| 13 | MB → SEC | sync | Perfecto + test-account credentials, by injected reference (M34) |
| 14 | MA → GIT | sync | Versioned assets (prompts / exemplars / golden set / test code) |
| 15 | MB → GIT | sync | Grow exemplar + golden set |
| 16 | MB → EXEC | sync | Spawn per device run (ADR 0013) |
| 17 | EXEC → PERF | sync | Single-run device session token; expires with the run (ADR 0013) |
| 18 | MB → PERF | sync | Pool + artifact pull; dominant cost |
| 19 | MA → GW | sync | Model calls (P2) via the Invoke Models seam |
| 20 | MB → GW | sync | Fidelity grade (ADR 0004); from day one |
| 21 | MA → OCT | sync | Manual-test ingest, API-key; hash-at-ingest (M15) |
| 22 | MB → OCT | async | A3: publish certified assets (CF3); never a verdict precondition |
| 23 | MA → XLS | sync | Workbook file input; raw workbooks never enter Git (M35) |

