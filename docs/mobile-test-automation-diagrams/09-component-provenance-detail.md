# C3c — Component overlay: provenance & pinning — detail tables

> Who writes lineage, carrying what? A subset of C3a — the thirteen lineage writers, Preserve Provenance, and the two store edges. The thirteen edges are directed and unlabeled; they share the one meaning fixed in the key (§0).

**Locator:** this view opens `APP` from `07-component`. It is a **subset** of `07-component` — not the complete edge set.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 14 | PRESERVE_PROVENANCE | Append-only hash-chained lineage, CA=13 (ADR 0012); + metrics read model + auditor export (ADR 0008, CF11) |
| 15 | POSTGRESQL | WORKING ASSUMPTION (spine C3); lineage schema append-only: app role INSERT/SELECT only, per-conversion hash chain, supersede-not-update — ADR 0012 |
| 16 | OBJECT_STORAGE | Evidence object storage behind an S3-compatible port (ADR 0011). Lineage chain anchors (ADR 0012) |

## Edge detail

| Edge | Detail the short label hides |
|------|------------------------------|
| INGEST_TEST_SOURCES → PRESERVE_PROVENANCE | writes its lineage row in the same local transaction as its state change (ADR 0007), carrying the pinning fields (F6), the authenticated principal (M37), the per-conversion chain link (ADR 0012), the corpus class (M19), the retention class (M39), and the writer's build identity (M32) |
| INTERPRET_TEST_INTENT → PRESERVE_PROVENANCE | writes its lineage row in the same local transaction as its state change (ADR 0007), carrying the pinning fields (F6), the authenticated principal (M37), the per-conversion chain link (ADR 0012), the corpus class (M19), the retention class (M39), and the writer's build identity (M32) |
| ACQUIRE_UI_EVIDENCE → PRESERVE_PROVENANCE | writes its lineage row in the same local transaction as its state change (ADR 0007), carrying the pinning fields (F6), the authenticated principal (M37), the per-conversion chain link (ADR 0012), the corpus class (M19), the retention class (M39), and the writer's build identity (M32) |
| RESOLVE_ELEMENTS → PRESERVE_PROVENANCE | writes its lineage row in the same local transaction as its state change (ADR 0007), carrying the pinning fields (F6), the authenticated principal (M37), the per-conversion chain link (ADR 0012), the corpus class (M19), the retention class (M39), and the writer's build identity (M32) |
| GENERATE_TEST_CODE → PRESERVE_PROVENANCE | writes its lineage row in the same local transaction as its state change (ADR 0007), carrying the pinning fields (F6), the authenticated principal (M37), the per-conversion chain link (ADR 0012), the corpus class (M19), the retention class (M39), and the writer's build identity (M32) |
| REPAIR_LOCATORS → PRESERVE_PROVENANCE | writes its lineage row in the same local transaction as its state change (ADR 0007), carrying the pinning fields (F6), the authenticated principal (M37), the per-conversion chain link (ADR 0012), the corpus class (M19), the retention class (M39), and the writer's build identity (M32) |
| INVOKE_MODELS → PRESERVE_PROVENANCE | writes its lineage row in the same local transaction as its state change (ADR 0007), carrying the pinning fields (F6), the authenticated principal (M37), the per-conversion chain link (ADR 0012), the corpus class (M19), the retention class (M39), and the writer's build identity (M32) |
| VERIFY_STATICALLY → PRESERVE_PROVENANCE | writes its lineage row in the same local transaction as its state change (ADR 0007), carrying the pinning fields (F6), the authenticated principal (M37), the per-conversion chain link (ADR 0012), the corpus class (M19), the retention class (M39), and the writer's build identity (M32) |
| REPLAY_ON_DEVICES → PRESERVE_PROVENANCE | writes its lineage row in the same local transaction as its state change (ADR 0007), carrying the pinning fields (F6), the authenticated principal (M37), the per-conversion chain link (ADR 0012), the corpus class (M19), the retention class (M39), and the writer's build identity (M32) |
| CLASSIFY_REPLAY_OUTCOME → PRESERVE_PROVENANCE | writes its lineage row in the same local transaction as its state change (ADR 0007), carrying the pinning fields (F6), the authenticated principal (M37), the per-conversion chain link (ADR 0012), the corpus class (M19), the retention class (M39), and the writer's build identity (M32) |
| CERTIFY_CONVERSION → PRESERVE_PROVENANCE | writes its lineage row in the same local transaction as its state change (ADR 0007), carrying the pinning fields (F6), the authenticated principal (M37), the per-conversion chain link (ADR 0012), the corpus class (M19), the retention class (M39), and the writer's build identity (M32) |
| PUBLISH_CERTIFIED_ASSETS → PRESERVE_PROVENANCE | writes its lineage row in the same local transaction as its state change (ADR 0007), carrying the pinning fields (F6), the authenticated principal (M37), the per-conversion chain link (ADR 0012), the corpus class (M19), the retention class (M39), and the writer's build identity (M32) |
| ROUTE_HUMAN_DECISIONS → PRESERVE_PROVENANCE | writes its lineage row in the same local transaction as its state change (ADR 0007), carrying the pinning fields (F6), the authenticated principal (M37), the per-conversion chain link (ADR 0012), the corpus class (M19), the retention class (M39), and the writer's build identity (M32) |

## Key

- rectangle = a grouping of code inside a container (C4 component)
- cylinder = a data store (used for datastores ONLY)
- module-a colour = the same module tracked by colour across every view
- module-b colour = the same module tracked by colour across every view
- module-c colour = the same module tracked by colour across every view
- solid arrow = synchronous call
- `[Type]` under a name = the element's C4 type (container/component)

