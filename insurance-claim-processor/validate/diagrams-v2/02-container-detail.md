# Insurance claim processor v2 - Container view — detail tables

> Opens the Claim processing system box from the Context view. Two Step Functions workflows share one package, one bucket and one AppConfig application (one quantum). The intake workflow hands each claim revision to the decision workflow asynchronously; decision records flow back as events. A watchdog turns any failed intake execution into a `batch_failed` summary and metric (M14). Edges carry numbers resolved in the edge-detail table.

**Locator:** this view opens `SYS` from `01-context`. It is a **completeness reference** at this grain.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 1 | UPS | claims-admin and FNOL exports, partner TPAs, call-recording store |
| 5 | EB | rules: intake CSV objects; decision-record objects; failed intake executions (M14) at-least-once delivery; consumers dedupe (ADR 0017) |
| 6 | IWF | one execution per batch; Map over claims, Parallel over sources inline Map ≤ 50 claims; Distributed Map (a Standard child execution per claim) for 51–200 (M14) batches > 200 rows are quarantined at admission (ADR 0019) one orchestrator retry layer with full jitter (ADR 0016) |
| 7 | ISTEP | dataprep subpackage, one handler dispatching on step role reads raw PII and cannot call Bedrock (ADR 0020) |
| 8 | DWF | v1, live; one execution per claim revision definition changes by one pass-through only |
| 9 | DSTEP | v1 pipeline; reads `bundles/*` only, with an explicit Deny on `raw/*` (M6) checks FM output against canonical intake values before routing; threshold on the canonical amount (M1) calls Bedrock with a guardrail on every request; only claim-derived text is guardrail-checked input (H-F14-a) |
| 10 | CLI | dq propose, ask, decide |
| 11 | S3 | Amazon S3 bucket, versioned, SSE-KMS single-writer zones: intake, raw, processed, bundles, quality, results (ADR 0017) revision-scoped keys `bundles/<claim_id>/r<rev>` and `processed/claims/<claim_id>/r<rev>/…` (M12) intake contract version path `intake/v=1/…` (M3) |
| 12 | CAT | AWS Glue Data Catalog: all-string claims_intake table, one partition per batch (ADR 0019) |
| 13 | CFG | AWS AppConfig: model-selection and data-quality profiles linear-bake deployments with rollback (ADR 0010, ADR 0022) |
| 14 | BR | Converse + Guardrails |
| 15 | CMP | sync Detect APIs, chunked to documented limits |
| 16 | TXT | AnalyzeDocument QUERIES |
| 17 | TRS | batch jobs, redacted output only |
| 18 | GDQ | ruleset evaluation runs |
| 19 | DLQ | holds intake start events Event routing could not deliver (M14) |

## Edge detail

| # | Edge | Mode | Claim |
|---|------|------|-------|
| 1 | UPS → S3 | sync | Upstream claim sources write raw claim artifacts first, then the intake CSV last (manifest-last commit). |
| 2 | S3 → EB | async | The claim data store emits Object Created events for intake CSVs and for decision records. |
| 3 | EB → IWF | async | Event routing starts one intake execution per batch CSV. |
| 4 | IWF → ISTEP | sync | The intake workflow invokes each intake step: admit, gates, sources, reconcile, bundle, dispatch, account. |
| 5 | ISTEP → S3 | sync | The intake step function reads the raw, intake and history zones and writes the processed, bundles and quality zones. |
| 6 | ISTEP → CAT | sync | The intake step function registers each batch partition in the intake catalog. |
| 7 | ISTEP → GDQ | async | The intake step function starts and polls the batch ruleset run (budgeted poll, cancel on exhaustion). |
| 8 | GDQ → S3 | sync | Glue Data Quality reads the batch partition and writes DQ results to the quality zone. |
| 9 | ISTEP → CMP | sync | The intake step function detects PII, entities, key phrases and sentiment through Comprehend. |
| 10 | ISTEP → TXT | sync | The intake step function analyzes police-report and estimate images through Textract QUERIES. |
| 11 | ISTEP → TRS | async | The intake step function starts and polls redacted transcription jobs. |
| 12 | TRS → S3 | async | Transcribe writes redacted transcripts to the transcripts zone. |
| 13 | ISTEP → CFG | sync | The intake step function reads the data-quality configuration (last-known-good on failure). |
| 14 | ISTEP → DWF | async | The intake step function starts one decision execution per claim revision, named `claim-<id>-r<rev>`, passing the bundle key plus its S3 VersionId (M12), and does not wait for it. |
| 15 | DWF → DSTEP | sync | The decision workflow invokes each decision step. |
| 16 | DSTEP → S3 | sync | The decision step functions read bundles and write results and pending-review records. |
| 17 | DSTEP → BR | sync | The decision step functions extract and summarize through Converse with a guardrail. |
| 18 | DSTEP → CFG | sync | The decision step functions read model-selection configuration and flags. |
| 19 | EB → ISTEP | async | Event routing delivers decision-record events to the intake feedback step. |
| 20 | DQO → CLI | sync | The data-quality owner runs dq propose in the operator CLI. |
| 21 | CLI → S3 | sync | The operator CLI reads feedback records and writes proposals to the quality zone. |
| 22 | DQO → CFG | sync | The data-quality owner deploys an approved data-quality configuration version. |
| 23 | OPS → S3 | sync | Intake operations review quarantine records in the quality zone. |
| 24 | ADJ → CLI | sync | The claims adjuster asks questions about a claim bundle through the operator CLI. |
| 25 | CLI → BR | sync | The operator CLI answers adjuster questions through multi-turn Converse with a guardrail. |
| 26 | IWF → EB | async | Step Functions emits the intake workflow's execution status-change events to Event routing (M14). |
| 27 | EB → ISTEP | async | Event routing routes FAILED, TIMED_OUT and ABORTED intake executions to the intake step function for failed-batch accounting: a `batch_failed` summary plus the `BatchFailed{Status}` metric (M14). |
| 28 | EB → DLQ | async | Event routing sends intake start events it could not deliver to the trigger dead-letter queue (M14). |

## Not shown for brevity

- **Amazon CloudWatch** — every container emits EMF metrics and logs to CloudWatch; the data-quality dashboard and alarms read them

## Key

- stadium/pill = a person or role (actor)
- rectangle = an application or data store (C4 container)
- double-bordered rectangle, `EXT:` = an external system we don't own
- cylinder = a data store (used for datastores ONLY)
- solid arrow = synchronous call
- dashed arrow = asynchronous message/event
- `[Type]` under a name = the element's C4 type (container/component)

