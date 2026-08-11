# ASH-Capture - Component view — detail tables

> Zooms into the ASH-Capture container. The discovery loop, deterministic validator, DeviceSession abstraction, and the two committed artifacts (ScreenGraph, NavigationManifest). Every node here is PROPOSED (ADR 0014 in flight). The spine consumes only the committed manifest; none of these components run in the spine.

**Locator:** this view opens `ASH` from `02-container`. It is a **completeness reference** at this grain.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 1 | DISC | PROPOSED ADR 0014 LLM proposes <=K candidate next actions from screenshot + pruned tree budgets: <=15 actions, <=60s/step, <=3 no-progress strikes, 10-min session cap records every transition as a graph edge (side effect) concrete mocks: ASHCapture.discovery.{input.json,prompt.md,output.json} - HomeScreen -> AccountOverview scenario; see 05-discovery-loop for the step-by-step runtime cycle |
| 2 | VAL | PROPOSED ADR 0014 filters by locator cascade + confidence floor denylist (logout/transfer/pay/confirm) - defense-in-depth, not the safety guarantee safety is environmental: lower test env, resettable data |
| 3 | EXEC | PROPOSED ADR 0014 applies the surviving action via DeviceSession.act() re-dumps hierarchy, computes screen signature, checks arrival |
| 4 | SIG | PROPOSED ADR 0014 signature = (skeletonHash, titleAnchor) skeletonHash = hash of sorted (elementType, accessibilityId) tuples, excludes text titleAnchor = auto-discovered accessibility title element (no app-team ask) ANCHOR_LESS screens -> human escape hatch |
| 5 | DEV | PROPOSED ADR 0014 abstraction: login(), screenshot(), hierarchy(), act(), launchDeepLink() implementations: PerfectoSession, LocalIOSSession, LocalAndroidSession normalized hierarchy output; locator source field marks backend |
| 6 | DRIFT | PROPOSED ADR 0014 on release: edges flip UNVERIFIED, re-verify lazily on capture failure: mark edge BROKEN, scoped re-discovery from last good node graph versioned per appVersion; supersede-not-update (ADR 0012) concrete mock: ASHCapture.driftrepair.input.json; surfaces the signature re-keying defect (Replan R1 D1/S1) - reuses the discovery prompt unchanged |
| 7 | DEEP | PROPOSED ADR 0014 static parse (APK intent filters / iOS associated domains) + LLM-proposed routes + deterministic probe stores confirmed links as DEEP_LINK edges (cost 1), supplemental not replacing concrete mocks: ASHCapture.deeplink.{input.json,prompt.md,output.json}; known gap preserved: the probe has no URL denylist (Replan R1 D1) |
| 8 | HATCH | PROPOSED ADR 0014 triggered by discovery failure or ANCHOR_LESS screen (<10% target) human steers; system records action stream and commits manifest + edges provenance: MANUAL_CAPTURE |
| 9 | GRAPH | PROPOSED ADR 0014 nodes = screen signatures, edges = deterministic locator-actions snapshot per graph_version_sha; auditable-not-gated cost weights: DEEP_LINK=1 < SCROLL/TAP=2 < TYPE=3 |
| 10 | MAN | PROPOSED ADR 0014 per-screen deterministic path the spine replays rootMode FRESH_LOGIN or DEEP_LINK; always starts from a known root provenance: DISCOVERY | GRAPH_SEARCH | DEEP_LINK_PROBE | DRIFT_REPAIR | MANUAL_CAPTURE |

## Key

- rectangle = a grouping of code inside a container (C4 component)
- cylinder = a data store (used for datastores ONLY)
- solid arrow = synchronous call
- `[Type]` under a name = the element's C4 type (container/component)

