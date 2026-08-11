# Mobile Test Automation LLM Pipeline - Container view (logical components) — external-boundary overlay — detail tables

> This view is a subset of `02-container` opening `SYS` — only the edges that cross the system's external boundary. Edge numbers match the primary; see `02-container` for the complete edge set.

**Locator:** this view opens `SYS` from `02-container`. It is a **subset** of `02-container` — not the complete edge set.

## Node detail (keyed by node ID)

| Node | Detail the short label hides |
|------|------------------------------|
| ITS | Acquires manual-test payloads and their source references from Octane, ALM/QC, and Excel. One of three trust boundaries that invoke the screening library. |
| SRC | External manual-test source systems, drawn as EXT1 in the section 10 component diagram. |
| AUE | Captures and prunes page-source and Object Spy evidence from a live Perfecto device. One implementation, two callers (human in Phase 1, service in Phase 2). One of three trust boundaries invoking the screening library. |
| PERF | External device lab, drawn as EXT2; touched by Acquire UI Evidence and Replay on Devices. |
| ROD | Executes committed tests K times against pinned Perfecto capability sets. The system's dominant cost; inherently flaky; rate-limited by lab capacity. K=3 conversion, K=5 certification. |
| IM | Mediates every model call with versioned prompts, fixed sampling policy, caching, and backoff. Single choke point. Stable and abstract: CE = 1, CA = 5, I = 0.17. Cache-key defect (must include model and provider version) carried to Stage 4 as ADR-2. One of three trust boundaries invoking the screening library. |
| GATEWAY | External model provider, drawn as EXT3; reached only through Invoke Models. |
| RE | Ranks and validates locator candidates against captured evidence and the object repository. Owns the locator cascade - nothing else may know it. Watch item: if VLM grounding is adopted, extract Ground Visually (section 6). |
| OBJREPO | External store, drawn as EXT4; read by Resolve Elements, written by Publish Certified Assets. |
| PCA | Writes certified locators and tests to the object repository and the exemplar corpus under single-writer discipline. Both writes must succeed or neither is visible; balanced CE = 1, CA = 1, I = 0.50. |
| RCA | Supplies the versioned prompts, house rules, and exemplars a conversion step requires. Stable; version identity is its whole job. CE = 1, CA = 4, I = 0.20. |
| GITCORP | External store, drawn as EXT5; read by Retrieve Conversion Assets, grown by Publish Certified Assets. |
| RHD | Presents ambiguous and sub-threshold cases for decision and records the outcome attributably. Human/identity boundary; balanced CE = 1, CA = 1, I = 0.50. |
| HUMAN_EXT | The human actor from the Context view, drawn as EXT6 in the section 10 component diagram; the endpoint of Route Human Decisions. |

## Edge detail

| # | Edge | Mode | Claim |
|---|------|------|-------|
| 39 | ITS → SRC | sync | Ingest Test Sources reads from Octane / ALM-QC / Excel (EXT1). |
| 40 | AUE → PERF | sync | Acquire UI Evidence captures evidence from the Perfecto device lab (EXT2). |
| 41 | ROD → PERF | sync | Replay on Devices runs K replays against the Perfecto device lab (EXT2). |
| 42 | IM → GATEWAY | sync | Invoke Models reaches the Orchestrator AI gateway (EXT3) - the single model-call seam. |
| 43 | RE → OBJREPO | sync | Resolve Elements looks up known elements in the object repository (EXT4). |
| 44 | PCA → OBJREPO | sync | Publish Certified Assets writes certified locators/tests back to the object repository (EXT4). |
| 45 | RCA → GITCORP | sync | Retrieve Conversion Assets reads versioned prompts/exemplars from the Git corpus (EXT5). |
| 46 | PCA → GITCORP | sync | Publish Certified Assets grows the exemplar/golden set in the Git corpus (EXT5). |
| 47 | RHD → HUMAN_EXT | sync | Route Human Decisions presents cases to QA engineers and reviewers (EXT6). |

