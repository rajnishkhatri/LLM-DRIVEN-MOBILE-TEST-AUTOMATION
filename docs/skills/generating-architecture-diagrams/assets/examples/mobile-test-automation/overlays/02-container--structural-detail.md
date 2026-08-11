# Mobile Test Automation LLM Pipeline - Container view (logical components) — structural overlay — detail tables

> This view is a subset of `02-container` opening `SYS` — only the structural topology — orchestration fan-out, handoffs, and the marked entanglement edge. Edge numbers match the primary; see `02-container` for the complete edge set.

**Locator:** this view opens `SYS` from `02-container`. It is a **subset** of `02-container` — not the complete edge set.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 1 | CC | Advances each conversion through its explicit state transitions within its retry budgets. Maximally unstable: CE = 11, CA = 0, I = 1.00 - the structural weak point, carried to Stage 4 as ADR-3 (central orchestration vs event-driven choreography). |
| 2 | ITS | Acquires manual-test payloads and their source references from Octane, ALM/QC, and Excel. One of three trust boundaries that invoke the screening library. |
| 3 | ITI | Produces schema-valid TestCaseIR, including control flow, and flags ambiguity rather than resolving it silently. Enriches with control flow and step dependencies - the defensible half of pass-1's 'Planner'. |
| 4 | AUE | Captures and prunes page-source and Object Spy evidence from a live Perfecto device. One implementation, two callers (human in Phase 1, service in Phase 2). One of three trust boundaries invoking the screening library. |
| 5 | RE | Ranks and validates locator candidates against captured evidence and the object repository. Owns the locator cascade - nothing else may know it. Watch item: if VLM grounding is adopted, extract Ground Visually (section 6). |
| 6 | GTC | Renders Page Objects and Appium Java/TestNG tests from approved IR and locators. Growth test: if house-style rework churns independently of code generation, extract Match House Style (section 5). |
| 7 | VS | Rejects generated code that fails formatting, compilation, lint, or locator-manifest rules. Free, fast, deterministic; runs on every generation. One of the three components that 'LLM-free replay' now refers to (section 8). |
| 8 | ROD | Executes committed tests K times against pinned Perfecto capability sets. The system's dominant cost; inherently flaky; rate-limited by lab capacity. K=3 conversion, K=5 certification. |
| 9 | CRO | Assigns a rule-based failure class to each run and emits the ReplayReport. Must stay deterministic and rule-based; explicitly not LLM work. Owns the failure-class taxonomy enum. |
| 10 | RL | Re-grounds locators for heal-eligible failures within a bounded repair budget. Budget: 3 static repairs, 3 device retries, then human queue (enforced by the coordinator). |
| 11 | CV | Grades assertion fidelity against the original manual expected result, applies the admission gates conjunctively, and issues the certification verdict. The one genuinely divergent component in pass 3: gate application is deterministic; fidelity grading is nondeterministic. CE = 4 (was 2), CA = 1, I = 0.80. Growth trigger: re-extract Judge Semantic Fidelity if recalibration decouples from gate-rule change. Carried to Stage 4 as ADR-4. |
| 12 | RHD | Presents ambiguous and sub-threshold cases for decision and records the outcome attributably. Human/identity boundary; balanced CE = 1, CA = 1, I = 0.50. |
| 13 | RCA | Supplies the versioned prompts, house rules, and exemplars a conversion step requires. Stable; version identity is its whole job. CE = 1, CA = 4, I = 0.20. |
| 14 | PCA | Writes certified locators and tests to the object repository and the exemplar corpus under single-writer discipline. Both writes must succeed or neither is visible; balanced CE = 1, CA = 1, I = 0.50. |
| 15 | IM | Mediates every model call with versioned prompts, fixed sampling policy, caching, and backoff. Single choke point. Stable and abstract: CE = 1, CA = 5, I = 0.17. Cache-key defect (must include model and provider version) carried to Stage 4 as ADR-2. One of three trust boundaries invoking the screening library. |
| 16 | LIB | Shared screening library - injection screening plus secret/PII redaction - invoked at all three trust boundaries. Demoted from a component at the pass-3 gate; the duplication rule is still satisfied but the boundary is no longer structural, so its three call sites must be asserted by a fitness function (section 4, section 9). |

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
| 16 | ITI → RCA | sync | Interpret Test Intent retrieves conversion assets. |
| 17 | RE → RCA | sync | Resolve Elements retrieves conversion assets. |
| 18 | GTC → RCA | sync | Generate Test Code retrieves conversion assets (exemplars, skeletons). |
| 19 | RL → RE | sync | Repair Locators reuses Resolve Elements - the reuse that justified withdrawing pass-1's Fix Proposer (section 8). |
| 20 | CV → PCA | sync | Certify Conversion hands a passed verdict to Publish Certified Assets. |
| 21 | CV → RCA | sync | Certify Conversion retrieves conversion assets - new efferent edge in pass 3. |
| 22 | CV → IM | entangled | entanglement: cluster B calls cluster A. Certify Conversion calls Invoke Models to grade fidelity - Dynamic Quantum Entanglement, the one edge crossing from cluster B back into cluster A (section 1a, section 10). Carried to Stage 4 as ADR-4. |
| 23 | ITS → LIB | sync | Ingest Test Sources invokes the screening library at its trust boundary (drawn as a dashed boundary edge in the section 10 source; rendered solid here because the source does not assert asynchrony and dashed is reserved for async). |
| 24 | AUE → LIB | sync | Acquire UI Evidence invokes the screening library at its trust boundary. |

