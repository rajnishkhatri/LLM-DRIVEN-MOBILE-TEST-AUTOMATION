# ADR 0002. Ground summaries with RAG; do not fine-tune on policies

## Status
Proposed

## Context
Summaries must reflect *this* insurer's policy language. Alternatives:
prompt-only, RAG over the policy corpus, PEFT/fine-tune, train from
scratch. The brief supplies documents, not a labeled instruction set.

## Decision
We will retrieve policy chunks (PoC: in-process files; production:
Bedrock Knowledge Base with metadata filters) and pass them into the
summary prompt. We will not fine-tune on policy PDFs for this system.

Justification:

- The gap is **knowledge**, not behavior (`cases/aws-ai/ch10.md:47-61`).
- Fine-tuning needs labels we do not have (standalone knockout).
- Policies change; weights would snapshot stale clauses.
- Citations make integrity checkable; an un-cited summary is flagged
  `ungrounded`.

## Consequences
Good: policy updates are ingest, not a training job; privacy stays
in-account.
Bad: retrieval quality (wrong jurisdiction) becomes a correctness
failure — metadata filters are mandatory in production. `retrieve` means
we own the prompt (more code) vs `retrieve_and_generate` (less control).

## Compliance
Eval: every summary on the gold set has ≥1 citation **or** explicit
`ungrounded`. No training job in the deploy graph.

## Notes
Author: arch-decide (provisional kata run)
Approved by / date:
Last modified: 2026-09-20
