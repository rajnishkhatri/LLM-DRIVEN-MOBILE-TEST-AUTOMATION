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

**LLD baseline** = 0001–0009. **Model-resilience increment** = 0010–0015
(spec: `../specs/claim-processor-model-resilience.spec.md`; **Accepted
2026-09-21**, in sdd-implement).
