# C3a — Component view: module flow — structural overlay — detail tables

> This view is a subset of `07-component` opening `APP` — only the structural topology — orchestration fan-out, handoffs, and the marked entanglement edge. Edge numbers match the primary; see `07-component` for the complete edge set.

**Locator:** this view opens `APP` from `07-component`. It is a **subset** of `07-component` — not the complete edge set.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 1 | QA | IDE + 2 CLIs. In P1 the conversion reasoning happens in THIS actor's IDE (Copilot, ADR 0001); the system receives only committed artifacts |
| 2 | INGEST_TEST_SOURCES | Adapters: Excel + Octane now, ALM/QC later (C1). Hash-at-ingest snapshot digest (M15) |
| 3 | ACQUIRE_UI_EVIDENCE | Hierarchy tool: page source, Object Spy, pruned tree. Records device + pool identity; off-pool captures flagged (M24) |
| 4 | REVIEWER | HITL queue; responds in hours–days |
| 5 | ROUTE_HUMAN_DECISIONS | Authenticated; every decision attributed to an individual principal (M37) |
| 6 | COORDINATE_CONVERSION | State machine + retry budgets; CE=11, CA=0 (ADR 0003). Repair budgets: 3 static, 3 device |
| 7 | INTERPRET_TEST_INTENT | Emits TestCaseIR; flags ambiguity |
| 8 | RESOLVE_ELEMENTS | Owns the locator cascade. Octane locator lookup STUBBED IN SPINE (C5) |
| 9 | GENERATE_TEST_CODE | Page Objects + Appium Java/TestNG |
| 10 | VERIFY_STATICALLY | Free, fast, deterministic. Capability rules gate generated code (ADR 0013) |
| 11 | CLASSIFY_REPLAY_OUTCOME | Rule-based taxonomy; unmapped outcome quarantines, never defaults (M10a) |
| 12 | REPAIR_LOCATORS | Bounded re-grounding |
| 13 | CERTIFY_CONVERSION | Grades fidelity + applies gates conjunctively; grade is ADVISORY to a human certifier (CF9). Custody-before-certify: every reference must resolve locally first (CF1) |
| 14 | REPLAY_ON_DEVICES | K runs, pinned pools; dominant cost. Spawns the separate execution process, single-run token, NO gateway credential (ADR 0013). Records ACTUAL context beside requested; pinned-facet mismatch quarantines (M24) |
| 15 | RETRIEVE_CONVERSION_ASSETS | Versioned prompts, house rules, exemplars |
| 16 | INVOKE_MODELS | THE model seam (ADR 0001): P1 Copilot impl / P2 gateway impl, config-selected. Cache key incl. model+provider version (ADR 0002). P2 edge tags = runtime call exists in Phase 2 only; the seam and its callers exist from the first commit (F1) |
| 17 | PUBLISH_CERTIFIED_ASSETS | Single-writer; certify-locally, publish-async (CF3) |
| 18 | GIT | Drawn faded for location only; detail lives in the C2 tables. Prompts / exemplars / golden set / test code; version identity is free |

## Edge detail

| # | Edge | Mode | Claim |
|---|------|------|-------|
| 1 | QA → INGEST_TEST_SOURCES | sync | ingestion CLI |
| 2 | QA → ACQUIRE_UI_EVIDENCE | sync | hierarchy-tool CLI |
| 3 | REVIEWER → ROUTE_HUMAN_DECISIONS | async | review-queue UI |
| 6 | COORDINATE_CONVERSION → INGEST_TEST_SOURCES | sync | acquire source |
| 7 | COORDINATE_CONVERSION → INTERPRET_TEST_INTENT | sync | interpret |
| 8 | COORDINATE_CONVERSION → ACQUIRE_UI_EVIDENCE | sync | capture evidence |
| 9 | COORDINATE_CONVERSION → RESOLVE_ELEMENTS | sync | resolve locators |
| 10 | COORDINATE_CONVERSION → GENERATE_TEST_CODE | sync | generate |
| 11 | COORDINATE_CONVERSION → VERIFY_STATICALLY | sync | static gate |
| 12 | COORDINATE_CONVERSION → CLASSIFY_REPLAY_OUTCOME | sync | classify |
| 13 | COORDINATE_CONVERSION → REPAIR_LOCATORS | sync | repair (bounded) |
| 14 | COORDINATE_CONVERSION → CERTIFY_CONVERSION | sync | certify |
| 15 | COORDINATE_CONVERSION → REPLAY_ON_DEVICES | async | A1: replay request |
| 16 | COORDINATE_CONVERSION → ROUTE_HUMAN_DECISIONS | async | A2: escalate |
| 21 | INTERPRET_TEST_INTENT → RETRIEVE_CONVERSION_ASSETS | sync | retrieves conversion assets |
| 22 | RESOLVE_ELEMENTS → RETRIEVE_CONVERSION_ASSETS | sync | retrieves conversion assets |
| 23 | GENERATE_TEST_CODE → RETRIEVE_CONVERSION_ASSETS | sync | retrieves conversion assets |
| 24 | REPAIR_LOCATORS → RESOLVE_ELEMENTS | sync | re-run cascade |
| 25 | CERTIFY_CONVERSION → INVOKE_MODELS | entangled | ENTANGLEMENT: fidelity grade (ADR 0004) |
| 26 | CERTIFY_CONVERSION → RETRIEVE_CONVERSION_ASSETS | sync | retrieves conversion assets |
| 27 | CERTIFY_CONVERSION → PUBLISH_CERTIFIED_ASSETS | sync | publish on PASS |
| 34 | RETRIEVE_CONVERSION_ASSETS → GIT | sync | versioned assets |
| 35 | PUBLISH_CERTIFIED_ASSETS → GIT | sync | grow exemplar + golden set |

## Key

- stadium/pill = a person or role (actor)
- rectangle = a grouping of code inside a container (C4 component)
- cylinder = a data store (used for datastores ONLY)
- module-a colour = the same module tracked by colour across every view
- module-b colour = the same module tracked by colour across every view
- solid arrow = synchronous call
- dashed arrow = asynchronous message/event
- thick arrow = a deliberately-marked entanglement edge
- `[Type]` under a name = the element's C4 type (container/component)

