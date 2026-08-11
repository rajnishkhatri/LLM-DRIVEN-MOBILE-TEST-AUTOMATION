# Locator Resolution - Cascade + LLM fallback — detail tables

> Zooms into the Locator resolution step from the pipeline flow. This stage is DECIDED (base O1 spine, blueprint-revision-v2). The cascade tries three deterministic sources in order; only when all fall below the confidence floor does it fall to the VLM and LLM-guess sources - both genuine model calls, routed through the Gateway, screened as a decided-spine egress. Output is the shared LocatorCandidate.manifest.json that the static gate's no-orphan-locator rule enforces against.

**Locator:** this view opens `LOC` from `04-pipeline-flow`. It is a **completeness reference** at this grain.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 1 | REPO | source 1 of 5 in the cascade - the object repository (existing resolved locators, single-writer discipline) deterministic: no model call |
| 2 | PAGESRC | source 2 of 5 - the live Appium getPageSource() dump for the current screen (LoginScreen.pageSource.xml) deterministic: no model call |
| 3 | SPY | source 3 of 5 - Perfecto's Object Spy smart-locator candidates (LoginScreen.objectSpy.json) deterministic: no model call |
| 4 | VLM | source 4 of 5 - a vision-language model confirms the element is visually present and tappable from a screenshot THIS IS A GENUINE MODEL CALL, routed through the Gateway (ADR 0013); part of the decided spine, not a proposal awaiting an ADR screening call-site: adr-0009:locator-fallback-egress |
| 5 | LLMGUESS | source 5 of 5, last resort - proposes a locator strategy from the pruned tree text alone, no screenshot THIS IS A GENUINE MODEL CALL, routed through the Gateway (ADR 0013); part of the decided spine, not a proposal awaiting an ADR concrete mock: LocatorResolution.fallback.{input.json,prompt.md,output.json} - resolves 'the Forgot Password link' -> forgotPasswordButton (ACCESSIBILITY_ID, 0.91) does NOT invent elements outside the pruned tree (returns NO_MATCH instead); does NOT execute anything on a device |
| 6 | MANIFEST | every candidate carries a confidence and a source (OBJECT_REPO | PAGE_SOURCE | OBJECT_SPY | VLM | LLM-guess) concrete mock: LocatorCandidate.manifest.json (ACC-1042 scenario - 4 ACCESSIBILITY_ID candidates, all source OBJECT_REPO in the happy-path case) committed as the resolved locator set for this IR version |
| 7 | SG | THE SPINE BEGINS - LLM-free from here (same node as in 04-pipeline-flow) no-orphan-locator rule: every locator used in the committed Java must appear in this manifest or the object repository concrete mock: StaticGate.report.json - locatorManifest check PASS, 4/4 locators found, 0 orphans |

## Key

- cylinder = a data store (used for datastores ONLY)
- dash-bordered rectangle = a runtime process, not a deployable
- module-a colour = the same module tracked by colour across every view
- solid arrow = synchronous call

