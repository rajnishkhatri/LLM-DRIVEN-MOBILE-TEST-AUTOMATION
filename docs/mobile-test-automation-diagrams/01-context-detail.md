# C1 — Context view: the system in its world — detail tables

> Who and what does the system touch? The whole conversion-and-certification pipeline, its four actor classes, and its external dependencies. The single system box drawn here is opened in C2a.

## Node detail (keyed by node ID)

| Node | Detail the short label hides |
|------|------------------------------|
| QA | IDE + 2 CLIs. In P1 the conversion reasoning happens in THIS actor's IDE (Copilot, ADR 0001); the system receives only committed artifacts |
| REVIEWER | HITL queue; responds in hours–days |
| AUDITOR | Must reconstruct verdicts from stored evidence alone, without access to the running system (ADR 0008) |
| LEAD | Read-only metrics |
| SYS | ACCEPTED: Spring Boot modular monolith, ONE architecture quantum (ADR 0005). Runs inside the bank's validated internal network (E3). Opened in C2a |
| PERFECTO | INCUMBENT vendor — MSA on file, unread against this system's needs (E1). Flows run on mock/synthetic data (E2); artifacts produced OFF-PREM. NOT covered by E3. SLA: UNKNOWN (pending — probe = read the MSA, M1) |
| GATEWAY | Internal gateway; model providers hosted INSIDE the bank — prompts never leave (E4). Version-report contract UNVERIFIED (M5 probe held). SLA: UNKNOWN (pending — M4 consolidated inquiry) |
| OCTANE | At BOTH ends of the pipeline (E5): ingest source (REST, API-key) AND certified-asset publish target. Asset-versioning capability UNVERIFIED (M7 probe held). SLA: UNKNOWN (pending) |
| XLS | Excel workbooks + ALM-QC later (additive — C1). File input originating from bank teams inside the network (E3/S9). "The least deterministic input" — M16 real-workbook corpus is the probe |

## Edge detail

| Edge | Detail the short label hides |
|------|------------------------------|
| QA → SYS | Ingestion CLI + hierarchy-tool CLI, sync |
| REVIEWER → SYS | Review of ambiguous / sub-threshold cases; async, hours–days |
| AUDITOR → SYS | Read-only versioned export — no access to the running system (ADR 0008); the export is itself an attributable lineage event (CF11) |
| LEAD → SYS | Metrics dashboard, sync, read-only |
| SYS → PERFECTO | Device runs on pinned pools (sync); single-run session tokens (ADR 0013) |
| SYS → GATEWAY | Model calls via the Invoke Models seam, P2 (sync) |
| SYS → OCTANE | Manual-test ingest, sync, REST |
| SYS → OCTANE | Publish certified assets — async, retryable, idempotent projection, never a verdict precondition (CF3; weeks 3–8) |
| SYS → XLS | Workbook file input |

## Key

- stadium/pill = a person or role (actor)
- heavy-stroke rectangle = the software system in focus
- double-bordered rectangle, `EXT:` = an external system we don't own
- solid arrow = synchronous call
- dashed arrow = asynchronous message/event

