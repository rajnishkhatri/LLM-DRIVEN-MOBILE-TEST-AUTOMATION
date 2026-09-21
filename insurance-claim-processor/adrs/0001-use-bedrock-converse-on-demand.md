# ADR 0001. Use Amazon Bedrock on-demand Converse for claim FMs

## Status
Proposed

## Context
The PoC must call foundation models for document understanding, field
extraction, and summary generation. Alternatives: Amazon Bedrock
(managed, per-token), SageMaker self-hosted endpoints (instance-hours),
Amazon Q Business (per-seat assistant), and the exam snippet's
`invoke_model` text-completions contract (`max_tokens_to_sample` /
`completion`).

## Decision
We will invoke Amazon Bedrock on-demand through `bedrock-runtime.converse`
(or `converse_stream` later), resolving model ids at runtime via
`list_foundation_models` / `list_inference_profiles`. We will not
self-host a plain FM on SageMaker for this job, will not use Q Business as
the processor, and will not emit the legacy completions contract.

Justification:

- **Integrity / configurability:** Converse is provider-agnostic; extract
  and summary can use different `modelId`s without parser rewrites.
- **Cost / time to market:** per-token, zero idle; a SageMaker real-time
  endpoint bills 24×7 at PoC volume.
- **Correctness:** the completions format is a known bug against
  current-gen ids (`cases/aws-ai/ch09.md:686-712`).
- **Strategic:** Bedrock Guardrails and Knowledge Bases attach to this
  path later without changing the invoke envelope.

## Consequences
Good: swap models in eval; Stubber can contract-test Converse.
Bad: on-demand throttling (`ThrottlingException`) is our problem — pair
with C2 adaptive retries and a queue, not nested loops. Q Business's
ready UI is forfeited (wrong shape). Current-gen Claude may reject
`temperature` — pass `maxTokens` only when that is the case **[re-verify]**.

## Compliance
Fitness: repo grep / unit test forbids `max_tokens_to_sample` and
`["completion"]` parsing. CI runs the Stubber suite with no AWS creds.

## Notes
Author: arch-decide (provisional kata run)
Approved by / date:
Last modified: 2026-09-20 / proposed from aws-ai-assess
