# C2b — Container drill-down: module wiring — unclustered overlay — detail tables

> This view is a subset of `03-container-module-wiring` opening `APP` — only the edges owned by `unclustered`. Edge numbers match the primary; see `03-container-module-wiring` for the complete edge set.

**Locator:** this view opens `APP` from `03-container-module-wiring`. It is a **subset** of `03-container-module-wiring` — not the complete edge set.

## Node detail (keyed by node ID)

| Node | Detail the short label hides |
|------|------------------------------|
| APP | Module boundaries are the three clusters, NOT the blueprint's five pipeline stages (ADR 0005). Drawn opaque in C2a; opened at module grain in C2b and at component grain in C3a |
| WEB | One authenticated internal API, no BFF (ADR 0008). SSO against the bank IdP is a HARD requirement, not a nice-to-have (M37). The ONLY UI in Phase 1 |
| TEST_EXECUTION | Test-execution process, spawned per device run. Separate OS process — shape committed NOW, sandbox technology weeks 3–8 (ADR 0013). NO long-lived credentials; single-run device session token; NEVER the gateway credential. Static capability rules gate entry (supplement, not the control) |
| PERFECTO | Same standing as the C1 node-detail table (E1/E2). INCUMBENT vendor — MSA on file, unread (E1); flows run on mock/synthetic data (E2); NOT covered by E3 |

## Edge detail

| # | Edge | Mode | Claim |
|---|------|------|-------|
| 1 | QA → APP | sync | 2 CLIs (ingestion + hierarchy-tool), no BFF (ADR 0008) |
| 2 | REVIEWER → WEB | async | Review queue; human latency, hours–days |
| 3 | LEAD → WEB | sync | Read-only metrics dashboard |
| 4 | WEB → APP | sync | One authenticated internal API; SSO against bank IdP (M37) |
| 17 | TEST_EXECUTION → PERFECTO | sync | Single-run device session token; expires with the run (ADR 0013) |

## Key

- stadium/pill = a person or role (actor)
- rectangle = an application or data store (C4 container)
- double-bordered rectangle, `EXT:` = an external system we don't own
- dash-bordered rectangle = a runtime process, not a deployable
- solid arrow = synchronous call
- dashed arrow = asynchronous message/event
- `[Type]` under a name = the element's C4 type (container/component)

