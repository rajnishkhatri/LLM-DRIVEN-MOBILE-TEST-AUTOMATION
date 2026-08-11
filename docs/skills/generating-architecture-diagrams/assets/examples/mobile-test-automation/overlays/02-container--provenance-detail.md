# Mobile Test Automation LLM Pipeline - Container view (logical components) — provenance overlay — detail tables

> This view is a subset of `02-container` opening `SYS` — only the provenance/lineage writes into the append-only store. Edge numbers match the primary; see `02-container` for the complete edge set.

**Locator:** this view opens `SYS` from `02-container`. It is a **subset** of `02-container` — not the complete edge set.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 1 | ITS | Acquires manual-test payloads and their source references from Octane, ALM/QC, and Excel. One of three trust boundaries that invoke the screening library. |
| 2 | PP | Maintains the append-only lineage linking source asset, IR, prompt and model version, code commit, run artifacts, and human decisions - and exposes a read model over that lineage for conversion, quality, and cost metrics. Maximally stable and the most-depended-on contract: CE = 0, CA = 13, I = 0.00. The pass-3 read model is versioned separately so a metrics change cannot churn the write contract. Also owns the read-only auditor export (ADR 0008). |
| 3 | ITI | Produces schema-valid TestCaseIR, including control flow, and flags ambiguity rather than resolving it silently. Enriches with control flow and step dependencies - the defensible half of pass-1's 'Planner'. |
| 4 | AUE | Captures and prunes page-source and Object Spy evidence from a live Perfecto device. One implementation, two callers (human in Phase 1, service in Phase 2). One of three trust boundaries invoking the screening library. |
| 5 | RE | Ranks and validates locator candidates against captured evidence and the object repository. Owns the locator cascade - nothing else may know it. Watch item: if VLM grounding is adopted, extract Ground Visually (section 6). |
| 6 | GTC | Renders Page Objects and Appium Java/TestNG tests from approved IR and locators. Growth test: if house-style rework churns independently of code generation, extract Match House Style (section 5). |
| 7 | RL | Re-grounds locators for heal-eligible failures within a bounded repair budget. Budget: 3 static repairs, 3 device retries, then human queue (enforced by the coordinator). |
| 8 | IM | Mediates every model call with versioned prompts, fixed sampling policy, caching, and backoff. Single choke point. Stable and abstract: CE = 1, CA = 5, I = 0.17. Cache-key defect (must include model and provider version) carried to Stage 4 as ADR-2. One of three trust boundaries invoking the screening library. |
| 9 | VS | Rejects generated code that fails formatting, compilation, lint, or locator-manifest rules. Free, fast, deterministic; runs on every generation. One of the three components that 'LLM-free replay' now refers to (section 8). |
| 10 | ROD | Executes committed tests K times against pinned Perfecto capability sets. The system's dominant cost; inherently flaky; rate-limited by lab capacity. K=3 conversion, K=5 certification. |
| 11 | CRO | Assigns a rule-based failure class to each run and emits the ReplayReport. Must stay deterministic and rule-based; explicitly not LLM work. Owns the failure-class taxonomy enum. |
| 12 | CV | Grades assertion fidelity against the original manual expected result, applies the admission gates conjunctively, and issues the certification verdict. The one genuinely divergent component in pass 3: gate application is deterministic; fidelity grading is nondeterministic. CE = 4 (was 2), CA = 1, I = 0.80. Growth trigger: re-extract Judge Semantic Fidelity if recalibration decouples from gate-rule change. Carried to Stage 4 as ADR-4. |
| 13 | PCA | Writes certified locators and tests to the object repository and the exemplar corpus under single-writer discipline. Both writes must succeed or neither is visible; balanced CE = 1, CA = 1, I = 0.50. |
| 14 | RHD | Presents ambiguous and sub-threshold cases for decision and records the outcome attributably. Human/identity boundary; balanced CE = 1, CA = 1, I = 0.50. |

## Edge detail

| # | Edge | Mode | Claim |
|---|------|------|-------|
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

