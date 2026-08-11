# Mobile Test Automation LLM Pipeline - Container view (logical components) — detail tables

> This view opens the Mobile Test Automation LLM Pipeline system box from the Context view at logical-component grain: the sixteen components in three clusters, the shared screening library that is deliberately not a component, and the external systems they touch. Edges carry numbers; the numbered edge-detail table resolves each claim.

**Locator:** this view opens `SYS` from `01-context`. It is a **completeness reference** at this grain.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 1 | CC | Advances each conversion through its explicit state transitions within its retry budgets. Maximally unstable: CE = 11, CA = 0, I = 1.00 - the structural weak point, carried to Stage 4 as ADR-3 (central orchestration vs event-driven choreography). |
| 2 | ITS | Acquires manual-test payloads and their source references from Octane, ALM/QC, and Excel. One of three trust boundaries that invoke the screening library. |
| 3 | ITI | Produces schema-valid TestCaseIR, including control flow, and flags ambiguity rather than resolving it silently. Enriches with control flow and step dependencies - the defensible half of pass-1's 'Planner'. |
| 4 | AUE | Captures and prunes page-source and Object Spy evidence from a live Perfecto device. One implementation, two callers (human in Phase 1, service in Phase 2). One of three trust boundaries invoking the screening library. |
| 5 | RE | Ranks and validates locator candidates against captured evidence and the object repository. Owns the locator cascade - nothing else may know it. Watch item: if VLM grounding is adopted, extract Ground Visually (section 6). |
| 6 | RCA | Supplies the versioned prompts, house rules, and exemplars a conversion step requires. Stable; version identity is its whole job. CE = 1, CA = 4, I = 0.20. |
| 7 | GTC | Renders Page Objects and Appium Java/TestNG tests from approved IR and locators. Growth test: if house-style rework churns independently of code generation, extract Match House Style (section 5). |
| 8 | RL | Re-grounds locators for heal-eligible failures within a bounded repair budget. Budget: 3 static repairs, 3 device retries, then human queue (enforced by the coordinator). |
| 9 | IM | Mediates every model call with versioned prompts, fixed sampling policy, caching, and backoff. Single choke point. Stable and abstract: CE = 1, CA = 5, I = 0.17. Cache-key defect (must include model and provider version) carried to Stage 4 as ADR-2. One of three trust boundaries invoking the screening library. |
| 10 | RHD | Presents ambiguous and sub-threshold cases for decision and records the outcome attributably. Human/identity boundary; balanced CE = 1, CA = 1, I = 0.50. |
| 11 | VS | Rejects generated code that fails formatting, compilation, lint, or locator-manifest rules. Free, fast, deterministic; runs on every generation. One of the three components that 'LLM-free replay' now refers to (section 8). |
| 12 | ROD | Executes committed tests K times against pinned Perfecto capability sets. The system's dominant cost; inherently flaky; rate-limited by lab capacity. K=3 conversion, K=5 certification. |
| 13 | CRO | Assigns a rule-based failure class to each run and emits the ReplayReport. Must stay deterministic and rule-based; explicitly not LLM work. Owns the failure-class taxonomy enum. |
| 14 | CV | Grades assertion fidelity against the original manual expected result, applies the admission gates conjunctively, and issues the certification verdict. The one genuinely divergent component in pass 3: gate application is deterministic; fidelity grading is nondeterministic. CE = 4 (was 2), CA = 1, I = 0.80. Growth trigger: re-extract Judge Semantic Fidelity if recalibration decouples from gate-rule change. Carried to Stage 4 as ADR-4. |
| 15 | PCA | Writes certified locators and tests to the object repository and the exemplar corpus under single-writer discipline. Both writes must succeed or neither is visible; balanced CE = 1, CA = 1, I = 0.50. |
| 16 | PP | Maintains the append-only lineage linking source asset, IR, prompt and model version, code commit, run artifacts, and human decisions - and exposes a read model over that lineage for conversion, quality, and cost metrics. Maximally stable and the most-depended-on contract: CE = 0, CA = 13, I = 0.00. The pass-3 read model is versioned separately so a metrics change cannot churn the write contract. Also owns the read-only auditor export (ADR 0008). |
| 17 | LIB | Shared screening library - injection screening plus secret/PII redaction - invoked at all three trust boundaries. Demoted from a component at the pass-3 gate; the duplication rule is still satisfied but the boundary is no longer structural, so its three call sites must be asserted by a fitness function (section 4, section 9). |
| 18 | SRC | External manual-test source systems, drawn as EXT1 in the section 10 component diagram. |
| 19 | PERF | External device lab, drawn as EXT2; touched by Acquire UI Evidence and Replay on Devices. |
| 20 | GATEWAY | External model provider, drawn as EXT3; reached only through Invoke Models. |
| 21 | OBJREPO | External store, drawn as EXT4; read by Resolve Elements, written by Publish Certified Assets. |
| 22 | GITCORP | External store, drawn as EXT5; read by Retrieve Conversion Assets, grown by Publish Certified Assets. |
| 23 | HUMAN_EXT | The human actor from the Context view, drawn as EXT6 in the section 10 component diagram; the endpoint of Route Human Decisions. |

## Edge detail

| # | Edge | Mode | Claim |
|---|------|------|-------|
| 1 | CC → ITS | sync | Coordinate Conversion drives Ingest Test Sources (orchestrator fan-out, CE = 11). |
| 2 | CC → ITI | sync | Coordinate Conversion drives Interpret Test Intent. |
| 3 | CC → AUE | sync | Coordinate Conversion drives Acquire UI Evidence. |
| 4 | CC → RE | sync | Coordinate Conversion drives Resolve Elements. |
| 5 | CC → GTC | sync | Coordinate Conversion drives Generate Test Code. |
| 6 | CC → VS | sync | Coordinate Conversion drives Verify Statically. |
| 7 | CC → ROD | sync | Coordinate Conversion drives Replay on Devices. |
| 8 | CC → CRO | sync | Coordinate Conversion drives Classify Replay Outcome. |
| 9 | CC → RL | sync | Coordinate Conversion drives Repair Locators. |
| 10 | CC → CV | sync | Coordinate Conversion drives Certify Conversion. |
| 11 | CC → RHD | async | Coordinate Conversion routes to Route Human Decisions - the asynchronous edge in the middle of the state machine (section 6). |
| 12 | ITI → IM | sync | Interpret Test Intent calls Invoke Models for messy free text. |
| 13 | RE → IM | sync | Resolve Elements calls Invoke Models. |
| 14 | GTC → IM | sync | Generate Test Code calls Invoke Models. |
| 15 | RL → IM | sync | Repair Locators calls Invoke Models for bounded re-grounding. |
| 16 | ITI → RCA | sync | Interpret Test Intent retrieves conversion assets. |
| 17 | RE → RCA | sync | Resolve Elements retrieves conversion assets. |
| 18 | GTC → RCA | sync | Generate Test Code retrieves conversion assets (exemplars, skeletons). |
| 19 | RL → RE | sync | Repair Locators reuses Resolve Elements - the reuse that justified withdrawing pass-1's Fix Proposer (section 8). |
| 20 | CV → PCA | sync | Certify Conversion hands a passed verdict to Publish Certified Assets. |
| 21 | CV → RCA | sync | Certify Conversion retrieves conversion assets - new efferent edge in pass 3. |
| 22 | CV → IM | entangled | entanglement: cluster B calls cluster A. Certify Conversion calls Invoke Models to grade fidelity - Dynamic Quantum Entanglement, the one edge crossing from cluster B back into cluster A (section 1a, section 10). Carried to Stage 4 as ADR-4. |
| 23 | ITS → LIB | sync | Ingest Test Sources invokes the screening library at its trust boundary (drawn as a dashed boundary edge in the section 10 source; rendered solid here because the source does not assert asynchrony and dashed is reserved for async). |
| 24 | AUE → LIB | sync | Acquire UI Evidence invokes the screening library at its trust boundary. |
| 25 | IM → LIB | sync | Invoke Models invokes the screening library at its trust boundary. |
| 26 | ITS → PP | sync | Ingest Test Sources writes to the append-only provenance contract (all 13 write edges into Preserve Provenance carry the same lineage-append semantics). |
| 27 | ITI → PP | sync | Interpret Test Intent writes lineage to Preserve Provenance. |
| 28 | AUE → PP | sync | Acquire UI Evidence writes lineage to Preserve Provenance. |
| 29 | RE → PP | sync | Resolve Elements writes lineage to Preserve Provenance. |
| 30 | GTC → PP | sync | Generate Test Code writes lineage to Preserve Provenance. |
| 31 | RL → PP | sync | Repair Locators writes lineage to Preserve Provenance. |
| 32 | IM → PP | sync | Invoke Models writes lineage to Preserve Provenance. |
| 33 | VS → PP | sync | Verify Statically writes lineage to Preserve Provenance. |
| 34 | ROD → PP | sync | Replay on Devices writes lineage to Preserve Provenance. |
| 35 | CRO → PP | sync | Classify Replay Outcome writes lineage to Preserve Provenance. |
| 36 | CV → PP | sync | Certify Conversion writes lineage to Preserve Provenance. |
| 37 | PCA → PP | sync | Publish Certified Assets writes lineage to Preserve Provenance. |
| 38 | RHD → PP | sync | Route Human Decisions writes human corrections as preference pairs to Preserve Provenance - flywheel input. |
| 39 | ITS → SRC | sync | Ingest Test Sources reads from Octane / ALM-QC / Excel (EXT1). |
| 40 | AUE → PERF | sync | Acquire UI Evidence captures evidence from the Perfecto device lab (EXT2). |
| 41 | ROD → PERF | sync | Replay on Devices runs K replays against the Perfecto device lab (EXT2). |
| 42 | IM → GATEWAY | sync | Invoke Models reaches the Orchestrator AI gateway (EXT3) - the single model-call seam. |
| 43 | RE → OBJREPO | sync | Resolve Elements looks up known elements in the object repository (EXT4). |
| 44 | PCA → OBJREPO | sync | Publish Certified Assets writes certified locators/tests back to the object repository (EXT4). |
| 45 | RCA → GITCORP | sync | Retrieve Conversion Assets reads versioned prompts/exemplars from the Git corpus (EXT5). |
| 46 | PCA → GITCORP | sync | Publish Certified Assets grows the exemplar/golden set in the Git corpus (EXT5). |
| 47 | RHD → HUMAN_EXT | sync | Route Human Decisions presents cases to QA engineers and reviewers (EXT6). |

