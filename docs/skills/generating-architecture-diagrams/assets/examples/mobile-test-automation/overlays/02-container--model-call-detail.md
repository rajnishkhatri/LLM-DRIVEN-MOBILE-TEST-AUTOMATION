# Mobile Test Automation LLM Pipeline - Container view (logical components) — model-call overlay — detail tables

> This view is a subset of `02-container` opening `SYS` — only the model-call seam and its gateway. Edge numbers match the primary; see `02-container` for the complete edge set.

**Locator:** this view opens `SYS` from `02-container`. It is a **subset** of `02-container` — not the complete edge set.

## Node detail (keyed by node ID)

| Node | Detail the short label hides |
|------|------------------------------|
| ITI | Produces schema-valid TestCaseIR, including control flow, and flags ambiguity rather than resolving it silently. Enriches with control flow and step dependencies - the defensible half of pass-1's 'Planner'. |
| IM | Mediates every model call with versioned prompts, fixed sampling policy, caching, and backoff. Single choke point. Stable and abstract: CE = 1, CA = 5, I = 0.17. Cache-key defect (must include model and provider version) carried to Stage 4 as ADR-2. One of three trust boundaries invoking the screening library. |
| RE | Ranks and validates locator candidates against captured evidence and the object repository. Owns the locator cascade - nothing else may know it. Watch item: if VLM grounding is adopted, extract Ground Visually (section 6). |
| GTC | Renders Page Objects and Appium Java/TestNG tests from approved IR and locators. Growth test: if house-style rework churns independently of code generation, extract Match House Style (section 5). |
| RL | Re-grounds locators for heal-eligible failures within a bounded repair budget. Budget: 3 static repairs, 3 device retries, then human queue (enforced by the coordinator). |
| LIB | Shared screening library - injection screening plus secret/PII redaction - invoked at all three trust boundaries. Demoted from a component at the pass-3 gate; the duplication rule is still satisfied but the boundary is no longer structural, so its three call sites must be asserted by a fitness function (section 4, section 9). |

## Edge detail

| # | Edge | Mode | Claim |
|---|------|------|-------|
| 12 | ITI → IM | sync | Interpret Test Intent calls Invoke Models for messy free text. |
| 13 | RE → IM | sync | Resolve Elements calls Invoke Models. |
| 14 | GTC → IM | sync | Generate Test Code calls Invoke Models. |
| 15 | RL → IM | sync | Repair Locators calls Invoke Models for bounded re-grounding. |
| 25 | IM → LIB | sync | Invoke Models invokes the screening library at its trust boundary. |

