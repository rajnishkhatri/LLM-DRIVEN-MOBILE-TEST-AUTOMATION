# ADR 0004. Orchestrate the pipeline with Step Functions (Standard)

## Status
Proposed — **amends ADR 0003** (which deferred Step Functions)

## Context
The processor must run on real AWS, be triggered manually/on-demand, and add
**human-in-the-loop (HITL)** review of flagged claims. Two new forces have
landed since ADR 0003:

- **Auditability is a hard requirement** — insurance decisions are
  audit-governed; a regulator must be able to replay each step of a claim.
- **HITL requires a durable wait** — a flagged claim may pause for hours or
  days awaiting a human decision.

ADR 0003 chose a modular monolith and deferred Step Functions on a single
ground: "three sample docs do not amortize a state machine." That reasoning
weighed only build-time cost. The audit requirement and the HITL wait are the
exact conditions ADR 0003 and `../worksheets/style-decision.md` (Determination
5) named as the trigger to revisit it.

MECE trade-off (single Lambda vs Step Functions) is recorded in
`../design/solution-design.md` §1. Cost is **not** a differentiator: Bedrock
tokens dominate both runtimes; Step Functions Standard adds ~$0.0002/claim
(≈8 state transitions) **[re-verify]**.

## Decision
We will host the fixed extract → validate → retrieve → summarize → route →
(review) → record pipeline on **AWS Step Functions, Standard workflow**,
reached in two steps to keep throwaway near zero:

1. **Feasibility spike (first):** prove the *AI* hypothesis with the existing
   `claim_processor` CLI against real Bedrock (`CLAIM_PROCESSOR_REAL_AWS=1`) —
   extraction accuracy, RAG grounding, PII redaction, $/claim, resolved model
   ids. No new hosting code; the runtime shape does not change whether the AI
   works.
2. **Adopt Step Functions:** wrap the **same** component modules
   (`invoker`/`validator`/`rag`/`prompts`/`store`, unchanged) as states. HITL
   is a `waitForTaskToken` state (see ADR 0005).

Rejected: **single-Lambda production host** (dominated — cannot hold a
multi-day HITL wait; audit trail depends on hand-written logging); **Step
Functions Express** (no execution history — defeats the audit requirement);
**hand-rolled pause via Lambda + DynamoDB** (rebuilds `waitForTaskToken`,
adds throwaway). State **granularity** (~5–6 coarse states vs one Lambda per
component vs SFN direct S3/Bedrock integrations) is a build-time knob, not
fixed here.

Justification:

- **Auditability:** the Standard execution history records every state's
  input, output, timestamp, retry, and the path taken — a regulator-ready
  artifact, structural rather than logging-discipline-dependent.
- **HITL:** `waitForTaskToken` is the native durable-wait primitive (up to
  1 year); a single function cannot express it.
- **Production fidelity / minimal throwaway:** the state machine *is* the
  production topology; SQS ingest and extra review paths are added as
  triggers/states later, not a rewrite. Component logic is written once and
  reused across the spike, the state machine, and production.
- **Reliability:** per-state Retry/Catch turns resilience cards C7/C2/C9/C11
  from in-process code into declarative, auditable configuration.

## Consequences
Good: regulator-ready audit trail; HITL is native; per-state retry without
re-paying Bedrock tokens on partial failure; the offline component tests stay
green because logic lives in modules, not the ASL.
Bad: more resources to stand up by hand (mitigate with coarse states + SFN
direct integrations); a state-machine test surface beyond unit tests (mitigate
by keeping the ASL thin); SFN Standard per-transition cost (negligible vs
Bedrock).

## Compliance
Fitness: every processed claim produces one Step Functions execution history
record; the audited path uses **Standard**, never Express; the offline
`unittest` suite stays green; the CLI feasibility spike is the only real-AWS
step before the gated `aws-ai-validate` smoke; each step Lambda's role carries
**both** `foundation-model/*` and `inference-profile/*` ARNs (ADR 0001 /
design §5).

## Notes
Author: aws-ai-design (provisional kata run)
Approved by / date:
Last modified: 2026-09-21 / amends ADR 0003
