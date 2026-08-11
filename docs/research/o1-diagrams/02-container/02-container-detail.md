# O1 Test-Automation Pipeline - Container view — detail tables

> Shows the O1 pipeline as a readable stage flow above the four stores that own its committed artifacts, operational state, locator knowledge, and immutable evidence. The spine (replay + certification) is LLM-free; the authoring arm (ingestion + ASH-Capture + conversion) is LLM-bounded. ASH-Capture (ADR 0014 Accepted 2026-07-31).

**Locator:** this view opens `Pipeline` from `01-context`. It is a **completeness reference** at this grain.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 1 | ING | A0 Normalizer (LLM) - PROPOSED this session A1 Parser (deterministic, structure only) A2 Semantic Interpreter (deterministic-first, LLM fallback) emits committed TestCaseIR.json concrete mocks: NormalizedIntent.{input.txt,prompt.md,json} (A0) -> TestCaseIR.skeleton.json (A1) -> TestCaseIR.json (A2) |
| 2 | ASH | ADR 0014 Accepted 2026-07-31 automates state-aware hierarchy capture (replaces manual hierarchy-tool run) hybrid: LLM proposes + deterministic validator shortlists commits NavigationManifest to Git; writes ScreenGraph edges to PostgreSQL (opened in the Component view) concrete mocks: ASHCapture.discovery.*, ASHCapture.deeplink.*, ASHCapture.driftrepair.input.json (see the Component view + 05-discovery-loop for the internal runtime cycle) |
| 3 | CVT | Phase 1: Copilot workspace + prompt library Phase 2: generation service via Orchestrator AI structured output via BeanOutputConverter against IR + manifest schemas emits committed Appium Java (the audit pin) concrete mock: LoginTest.java (the committed audit pin for scenario ACC-1042) |
| 4 | RPL | Stage 1 static gate: format, mvn compile, Checkstyle, Error Prone, locator-manifest rule Stage 2 device gate: K runs on Perfecto (K=1 signed-off baseline; raising K = CF6 recorded decision), flakiness derivable once K>1 Stage 3 verdict: ReplayReport pins codeCommit SHA LLM output never touches it; consumes only committed code concrete mocks: StaticGate.report.json (stage 1), ReplayReport.json (stage 3 verdict) |
| 5 | CER | applies gates: compile, K/K device passes, semantic fidelity, locator confidence floor publishes metrics; feeds the flywheel on accept |
| 6 | PG | single primary store (ADR 0006) TestCaseIR, ReplayReport, lineage chain (ADR 0012) ScreenGraph tables (ADR 0014); NavigationManifest lineage rows |
| 7 | OBJ | resolved locators, single-writer discipline enriched by the flywheel on accept |
| 8 | EVID | immutable, S3-port-backed (ADR 0011) anchors lineage chain heads + graph version JSON |
| 9 | GITD | TestCaseIR.json, LoginTest.java, NavigationManifest |

## Edge detail

| # | Edge | Mode | Claim |
|---|------|------|-------|
| 1 | ING → ASH | sync | passes committed TestCaseIR |
| 2 | ASH → CVT | sync | provides manifest + UI evidence |
| 3 | CVT → RPL | sync | hands off committed Appium Java |
| 4 | RPL → CER | sync | produces ReplayReport |

## Key

- rectangle = an application or data store (C4 container)
- cylinder = a data store (used for datastores ONLY)
- module-a colour = the same module tracked by colour across every view
- module-b colour = the same module tracked by colour across every view
- solid arrow = synchronous call
- `[Type]` under a name = the element's C4 type (container/component)

