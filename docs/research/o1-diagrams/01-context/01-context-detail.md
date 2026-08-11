# O1 Test-Automation Pipeline - Context view — detail tables

> The whole. The O1 pipeline (LLM-free deterministic replay of committed code), its two human roles, and its external dependencies. The single system box drawn here is opened in the Container view.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 1 | QA | runs ingestion CLI, reviews and commits generated artifacts |
| 2 | Auditor | audits verdicts and tamper-evident lineage |
| 3 | Pipeline | ACCEPTED: LLM-free deterministic replay of committed code (blueprint-revision-v2) north-star production posture; O3 hybrid is the proposed POC (opened in the Container view) 22 concrete mock artifacts (ingestion -> capture -> resolution -> codegen -> gates -> verdict, incl. all 4 LLM call sites) live under docs/research/mocks/o1-spine/ - see the Mock Artifact Index |
| 4 | Octane | manual test script sources free-form English or structured steps |
| 5 | Gateway | all LLM calls route through one ChatModel interface (blueprint-revision-v2) no direct model vendor SDKs anywhere |
| 6 | Perfecto | pinned device pool, Appium 2, Smart Reporting |
| 7 | LocalDevices | xctools (iOS sim) and adb (Android) for local capture/replay |
| 8 | VAULT | short-lived single-run session tokens (ADR 0013) no long-lived creds held by workers |
| 9 | GIT | system of record for committed IR / Java / manifests / graph |

## Key

- stadium/pill = a person or role (actor)
- heavy-stroke rectangle = the software system in focus
- double-bordered rectangle, `EXT:` = an external system we don't own
- solid arrow = synchronous call

