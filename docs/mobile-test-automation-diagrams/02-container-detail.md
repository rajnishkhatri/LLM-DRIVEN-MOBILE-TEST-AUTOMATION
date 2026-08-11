# C2a — Container view: deployment topology (high level) — detail tables

> What containers exist, and what talks to what? This view opens the single box SYS from C1. Structure and synchronous data flow only, at container grain — the monolith is one opaque box here. Which module owns each edge is C2b; evidence flows are C2c; credentials are C2d; async edges are C2e. Canvas carries numbered edge refs only (1–16); the full claim lives in the edge-detail table keyed by number.

**Locator:** this view opens `SYS` from `01-context`. It is a **completeness reference** at this grain.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 5 | WEB | One authenticated internal API, no BFF (ADR 0008). SSO against the bank IdP is a HARD requirement, not a nice-to-have (M37). The ONLY UI in Phase 1 |
| 6 | APP | Deployment boundary: bank internal network — on-premises, bank validated internal network — no external party has access (ADR 0006; E3). Perfecto, the gateway, Octane, and workbook sources sit outside it Architecture quantum 1 of 1 — one deployable + one primary datastore = the single architecture quantum (ADR 0005). Object storage, Git, and the secrets store are on-premises but outside the quantum: they have their own lifecycles Module boundaries are the three clusters, NOT the blueprint's five pipeline stages (ADR 0005). Drawn opaque in C2a; opened at module grain in C2b and at component grain in C3a |
| 7 | POSTGRESQL | WORKING ASSUMPTION (spine C3); dev/CI embedded or containerized, ephemeral-only (D1, M40). Schemas: conversion-state · lineage (append-only: app role INSERT/SELECT only, per-conversion hash chain, supersede-not-update — ADR 0012) · outbox+queue (bounded retries, dead-letter quarantine — M21) · judge-response cache (M27, CF7). No cross-lifecycle foreign keys (F4, ADR 0006) |
| 8 | TEST_EXECUTION | Test-execution process, spawned per device run. Separate OS process — shape committed NOW, sandbox technology weeks 3–8 (ADR 0013). NO long-lived credentials; single-run device session token; NEVER the gateway credential. Static capability rules gate entry (supplement, not the control) |
| 9 | SECRETS_STORE | Interim: CI secret store; the vault is named by the M33 controls-baseline read — PENDING. All credentials resolved by injected reference, never literals (M34/CF8) |
| 10 | OBJECT_STORAGE | Evidence object storage behind an S3-compatible port (ADR 0011). Dev/CI: containerized MinIO; production BINDING PROBE-PENDING (week-0 platform probe; default = self-operated MinIO). Write-once / object-lock REQUIRED — ADR 0012's precondition, deployment-checked. Holds: classified artifacts + retention classes (M39) · canonicalized source snapshots (M15) · lineage chain anchors (ADR 0012). Envelope encryption + crypto-shredding before the first audit-retained artifact (ADR 0011 as amended) |
| 11 | GIT | Prompts / exemplars / golden set / test code; version identity is free |
| 12 | PERFECTO | Same standing as the C1 node-detail table (E1/E2, E4, E5, E3/S9). INCUMBENT vendor — MSA on file, unread (E1); flows run on mock/synthetic data (E2); NOT covered by E3 |
| 13 | GATEWAY | Same standing as the C1 node-detail table (E1/E2, E4, E5, E3/S9). Internal gateway; model providers hosted INSIDE the bank — prompts never leave (E4); version-report contract UNVERIFIED (M5 held) |
| 14 | OCTANE | Same standing as the C1 node-detail table (E1/E2, E4, E5, E3/S9). At BOTH ends of the pipeline (E5): ingest source AND publish target; asset-versioning UNVERIFIED (M7 held) |
| 15 | XLS | Same standing as the C1 node-detail table (E1/E2, E4, E5, E3/S9). File input originating from bank teams inside the network (E3/S9) |

## Edge detail

| # | Edge | Mode | Claim |
|---|------|------|-------|
| 1 | QA → APP | sync | 2 CLIs (ingestion + hierarchy-tool), no BFF (ADR 0008) |
| 2 | REVIEWER → WEB | async | Review queue; human latency, hours–days |
| 3 | LEAD → WEB | sync | Read-only metrics dashboard |
| 4 | WEB → APP | sync | One authenticated internal API; SSO against bank IdP (M37) |
| 5 | AUDITOR → APP | sync | Versioned export; targets the evidence module at module grain (C2b). Itself an attributable lineage event (CF11) |
| 6 | APP → POSTGRESQL | sync | State + lineage, same local transaction (ADR 0007) — rolled up from MA/MB/MC in C2b |
| 7 | APP → OBJECT_STORAGE | sync | Snapshots + classified artifacts + chain anchors (rolled up from MA/MB/MC in C2b) |
| 8 | APP → SECRETS_STORE | sync | All credentials resolved by injected reference, never literals (M34/CF8) |
| 9 | APP → GIT | sync | Versioned assets (prompts / exemplars / golden set / test code) |
| 10 | APP → TEST_EXECUTION | sync | Spawn per device run (ADR 0013) |
| 11 | TEST_EXECUTION → PERFECTO | sync | Single-run device session token (ADR 0013) |
| 12 | APP → PERFECTO | sync | Pool + artifact pull; dominant cost (MB-owned — C2b) |
| 13 | APP → GATEWAY | sync | Model calls (P2) + fidelity grade (ADR 0004) — MA/MB-owned (C2b) |
| 14 | APP → OCTANE | sync | Manual-test ingest, API-key (MA-owned — C2b) |
| 15 | APP → OCTANE | async | A3: publish certified assets — idempotent projection (CF3); never a verdict precondition |
| 16 | APP → XLS | sync | Workbook file input (MA-owned — C2b) |

## Key

- stadium/pill = a person or role (actor)
- rectangle = an application or data store (C4 container)
- double-bordered rectangle, `EXT:` = an external system we don't own
- cylinder = a data store (used for datastores ONLY)
- dash-bordered rectangle = a runtime process, not a deployable
- solid arrow = synchronous call
- dashed arrow = asynchronous message/event
- `[Type]` under a name = the element's C4 type (container/component)

