# Insurance claim processor v2 - Context view — detail tables

> The whole. The claim processing system (v1 decision workflow plus the v2 data-preparation workflow), the people who operate it, the upstream sources that feed it, and the managed AWS AI services it depends on. The system box is opened in the Container view.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 1 | UPS | claims-admin and FNOL exports, partner TPAs, call-recording store drop zone: attachments first, intake CSV last (ADR 0017) |
| 2 | OPS | own quarantined batches and rows |
| 3 | DQO | approves bounded DQ proposals (ADR 0022) |
| 4 | ADJ | asks questions over a claim bundle (CLI today) HITL review UI deferred with F2 - PROVISIONAL |
| 5 | SYS | v1 decision workflow + v2 data-preparation workflow ONE architecture quantum, pre-cut seam (ADR 0016) (opened in the Container view) |
| 6 | BR | Converse + Guardrails (ADR 0001, ADR 0008) model ids resolved at runtime, never hard-coded |
| 7 | CMP | PII, entities, key phrases, sentiment (ADR 0018) content-use opt-out via an AWS Organizations AI-services opt-out policy: owner action pending (R8c-a) |
| 8 | TXT | AnalyzeDocument with QUERIES (ADR 0018) content-use opt-out via an AWS Organizations AI-services opt-out policy: owner action pending (R8c-a) |
| 9 | TRS | batch jobs with PII redaction at source (ADR 0020) content-use opt-out via an AWS Organizations AI-services opt-out policy: owner action pending (R8c-a) |
| 10 | GDQ | DQDL ruleset per batch partition (ADR 0019) content-use opt-out via an AWS Organizations AI-services opt-out policy: owner action pending (R8c-a) |

## Key

- stadium/pill = a person or role (actor)
- heavy-stroke rectangle = the software system in focus
- double-bordered rectangle, `EXT:` = an external system we don't own
- solid arrow = synchronous call
- dashed arrow = asynchronous message/event

