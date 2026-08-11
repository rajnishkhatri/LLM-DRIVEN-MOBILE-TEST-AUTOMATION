---
type: architecture
title: 'P2 — The repo you''ll live in: six Maven modules, one deployable — detail tables'
description: 'Locator: this view opens SYS from p1-spine-context.'
tags: [architecture, presentation]
---

# P2 — The repo you'll live in: six Maven modules, one deployable — detail tables

> How is the new repository shaped? Six Maven modules, one bootable jar (ADR 0005, five-module reading ratified at PLAN-OK). Cluster modules may depend on spine-contracts only — the module-boundary rule wired CI-blocking in task zero; screening is a shared library, not a pipeline component. Opens SYS from P1.

**Locator:** this view opens `SYS` from `p1-spine-context`. It is a **completeness reference** at this grain.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 1 | APP | Thin assembly; wiring only. The single deployable — mvn package yields exactly one bootable jar (ADR 0005) |
| 2 | CONV | Packages: ingestion (Excel/POI + Octane REST adapters behind one contract — C1, with deterministic canonicalization + snapshot digest — M15), hierarchytool (capture, prune, pool identity — M24) Ambiguous steps are flagged in the IR rather than silently resolved |
| 3 | VC | Packages: staticgate, devicegate (worker — holds no gateway credential, ADR 0013), classification (fixed 7-class taxonomy), replayreport, objectrepo (port + read-only stub — C5) |
| 4 | EVID | Packages: lineage (append-only writes, principal, hash chain, supersede reads — ADR 0012), outbox+queue (ADR 0007), objectstorage (S3 port + MinIO adapter — ADR 0011), anchoring (job + verification), retention |
| 5 | CONTRACTS | The three schema contracts as Java records with Jackson: TestCaseIR, LocatorCandidate, ReplayReport JSON Schema exported via victools and committed; drift between record and schema fails CI PinnedValue marker enum {REAL, NOT_APPLICABLE, UNPINNABLE_PHASE1(reserved)} (C4/M12); corpusClass (M19); retentionClass (M39) |
| 6 | SCREEN | Shared library, not a pipeline component (ADR 0009): injection screening + secret/PII redaction; one-line in-process API, no network; versioned; red-team corpus + regression report (count / source mix / last addition / bypass rate — M36) Flagged payloads quarantine for review; release is a recorded, attributable override (M35/M18) |

## Edge detail

| Edge | Detail the short label hides |
|------|------------------------------|
| APP → CONV | Spring wiring; the cluster module ships inside the single bootable jar (ADR 0005) |
| APP → VC | Spring wiring; the cluster module ships inside the single bootable jar (ADR 0005) |
| APP → EVID | Spring wiring; the cluster module ships inside the single bootable jar (ADR 0005) |
| CONV → CONTRACTS | Cluster deps → spine-contracts only (module-boundary rule, task zero); the IR is the only thing that leaves ingestion (F2) |
| VC → CONTRACTS | Cluster deps → spine-contracts only (module-boundary rule, task zero) |
| EVID → CONTRACTS | Cluster deps → spine-contracts only (module-boundary rule, task zero); records living in producer modules was rejected — it would invert the dependency direction (plan G1) |
| CONV → SCREEN | Call sites 1 and 2 of three: ingestion boundary + hierarchy-capture output, before it is written (ADR 0009 as amended, M35); F3 static half fails CI, runtime half rejects the payload |
| VC → SCREEN | Call site 3 of three: the device-gate artifact pull at landing (ADR 0009 as amended, M35) |

## Not shown for brevity

- **architecture-tests** — ArchUnit fitness functions F1–F4 + module-boundary + no-gateway-credential rules, CI-blocking from task zero (M18) — a build artifact, not a runtime module (not shown for brevity)
- **db/migration + ci/** — Flyway V1 (lineage core + grants) and pipeline-as-code (runner pinned by digest — M28) land in task zero (not shown for brevity)

## Key

- rectangle = an application or data store (C4 container)
- hexagon = an element deliberately NOT modelled as a component
- module-a colour = the same module tracked by colour across every view
- module-b colour = the same module tracked by colour across every view
- module-c colour = the same module tracked by colour across every view
- solid arrow = synchronous call
- `[Type]` under a name = the element's C4 type (container/component)

