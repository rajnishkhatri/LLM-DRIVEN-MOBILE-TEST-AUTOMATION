# ADR index — insurance claim document processor

One file per decision. Status flow: Proposed → Accepted → Superseded by `<M>`.
Amend/supersede links go both ways. Template:
`.cursor/skills/arch-decide/references/adr-template.md`.

| ADR | Title | Status | Amends / extends / superseded |
|---|---|---|---|
| [0001](0001-use-bedrock-converse-on-demand.md) | Use Bedrock Converse on-demand | Proposed | — |
| [0002](0002-rag-not-finetune.md) | RAG, not fine-tune | Proposed | — |
| [0003](0003-modular-monolith-poc.md) | Modular monolith for the PoC | Proposed | amended by 0004 |
| [0004](0004-step-functions-orchestration.md) | Orchestrate with Step Functions (Standard) | Proposed | amends 0003 |
| [0005](0005-hitl-manual-token-resume.md) | HITL via manual token resume | Proposed | — |
| [0006](0006-document-understanding-vision-fm.md) | Document understanding via vision FM | Proposed | extended by 0014 |
| [0007](0007-rag-knowledge-base-s3-vectors.md) | RAG Knowledge Base on S3 Vectors | Proposed | — |
| [0008](0008-guardrails-on-converse-day-one.md) | Guardrails on Converse day one | Proposed | — |
| [0009](0009-least-privilege-iam-single-processing-role.md) | Least-privilege IAM, single processing role | Proposed | — |
| [0010](0010-appconfig-model-selection-and-flags.md) | Externalize model selection + flags to AppConfig | Accepted | — |
| [0011](0011-foundation-model-adapter.md) | Bedrock-family foundation-model adapter | Accepted | — |
| [0012](0012-circuit-breaker-measured-signal.md) | Measured circuit breaker in the workflow | Accepted | amends resilience-clinic C1 deferral |
| [0013](0013-ensemble-extraction-flag-gated.md) | Ensemble the extraction step, flag-gated | Accepted | reverses (bounded) capability-brief §4 |
| [0014](0014-graceful-degradation-tier-ladder.md) | Graceful-degradation tier ladder | Accepted | extends 0006 + C11 |
| [0015](0015-cloudwatch-emf-metrics-and-remediation.md) | CloudWatch EMF metrics + reversible remediation | Accepted | — |
| [0016](0016-data-preparation-plane-intake-state-machine.md) | Data-preparation plane = second orchestrated workflow inside the existing quantum (pre-cut seam) | Accepted 2026-09-23 | extends 0004 |
| [0017](0017-single-writer-zones-and-curated-bundle.md) | Single-writer S3 zones + self-contained versioned bundle; drop-zone ingestion; S3 lock with takeover | Accepted 2026-09-23 | — |
| [0018](0018-managed-perception-deterministic-first-fm-last.md) | Managed perception + deterministic code; FM reserved for judgment; sentiment context-only | Accepted 2026-09-23 | extends 0006 |
| [0019](0019-intake-quality-gates-from-one-rule-catalog.md) | Batch + row quality gates from one rule catalog (Glue DQ + Lambda) | Accepted 2026-09-23 | — |
| [0020](0020-pii-minimization-and-iam-separation-of-duties.md) | PII minimized before persistence; raw-PII readers ≠ Bedrock callers | Accepted 2026-09-23; LLD amendment accepted 2026-09-24 | extends 0008, 0009 |
| [0021](0021-model-input-formatting-contract.md) | Model-input formatting contract (intake owns data, v1 owns task); dialog templates | Accepted 2026-09-23 | extends 0001, 0011 |
| [0022](0022-human-approved-replay-proven-quality-proposals.md) | Human-approved, replay-proven DQ config proposals | Accepted 2026-09-23 | extends 0010, 0015 |

**Approval criteria** (R7q-a, 2026-09-23): [`approval-criteria.md`](approval-criteria.md).
It sets five triggers. A flagged ADR is approved on its own, then signed off by
a security / privacy reviewer before any real claim data.

**LLD baseline** = 0001–0009. **Model-resilience increment** = 0010–0015
(spec: `../specs/claim-processor-model-resilience.spec.md`; **Accepted
2026-09-21**, in sdd-implement).
**v2 data-preparation increment** = 0016–0022 (HLD summary:
`../design/hld-v2-data-prep.md`; spec `../specs/claim-processor-data-prep.spec.md`
ON HOLD until the LLD is done (owner sequence, 2026-09-23); **Accepted 2026-09-23** — ratified as recommended; amendments M1–M18 recorded per ADR).
