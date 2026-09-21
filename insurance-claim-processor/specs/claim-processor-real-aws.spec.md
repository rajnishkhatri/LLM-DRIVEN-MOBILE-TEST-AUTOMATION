# Spec — claim processor on real AWS (Step Functions + HITL)

**Stage:** sdd-spec (Stages 2–4). **Status:** CLARIFIED — bounded IAM amendment
2026-09-21 (F1/F3/F4b/F9; F8 dropped). **Do not rewrite** the rest of this
spec.
**Binding:** `.sdd` `[roots] claim-document-processor = insurance-claim-processor/`.
**Design:** `../design/solution-design.md` §1–§7, ADRs 0004–0009,
`../validate/architecture-validation.md`.
**Test gate:** offline `unittest` suite in `../build/` (no creds, `aws_profile`
`<none>`); real AWS behind `CLAIM_PROCESSOR_REAL_AWS=1` + a separate human gate.

**Verification tags:** `[off]` provable offline (Stubber/moto/unit/grep);
`[gate]` requires the real-AWS gate; `[sfn]` proven at the state-machine layer
(Step Functions Local / deploy check).

## Scope

**In:** promote the offline PoC to the real-AWS target — (Step A) a CLI
feasibility spike against real Bedrock, then (Step B) a Step Functions Standard
runtime with routing + HITL, vision-FM image reading, Guardrails day-1,
least-privilege IAM, and the extended result contract. KB on S3 Vectors is
specified as a **fast-follow** (contract captured; PoC first smoke stays on
keyword RAG).
**Out:** CDK automation (manual runbook only), reviewer UI / A2I, Verified
Permissions authz, PrivateLink, a relational DB / DynamoDB worklist, Textract/BDA.

---

## A. Foundation-model invocation

- **AC-A1** `[off]` IF code emits the legacy completions contract
  (`prompt` / `max_tokens_to_sample` / `["completion"]`), THEN the build fails —
  grep + contract test forbid it. *(fitness: ADR-0001)*
- **AC-A2** `[off]` The Bedrock client SHALL set connect=10 s, read=300 s and
  adaptive retries `max_attempts=5`. *(C7/C2)*
- **AC-A3** `[off]` IF Bedrock returns `ThrottlingException`, THEN the system
  SHALL rely on SDK adaptive retry and SHALL NOT add a nested application retry
  loop (exactly one app-level call). *(C2)*
- **AC-A4** The system SHALL invoke `converse` with `messages` +
  `inferenceConfig`, and SHALL resolve model ids at runtime `[gate]` and record
  the resolved id on every result `[off]`. *(ADR-0001)*
- **AC-A5** `[off]` WHERE Guardrails are enabled, every `converse` call SHALL
  include `guardrailConfig`. *(ADR-0008)*

## B. Extraction + validation (integrity)

- **AC-B1** `[off]` IF an extraction is not schema-valid or a required field is
  empty, THEN the system SHALL flag it (`empty_fields:…`) and route to human
  review.
- **AC-B2** `[off]` IF PII (e.g. an SSN) appears in the generated summary, THEN
  the system SHALL flag `pii_*` and route to human review — never auto-approve.
- **AC-B3** `[off]` WHEN a packet is processed, the system SHALL extract the
  five fields as schema-valid JSON; `claim_amount` SHALL be numeric with max
  relative error vs gold = 0 on the eval set. *(fitness: worksheet)*

## C. RAG grounding

- **AC-C1** `[off]` IF the jurisdiction cannot be inferred, THEN the system
  SHALL retrieve nothing and mark the summary `ungrounded` (fail closed).
- **AC-C2** `[off]` WHEN composing a summary, the system SHALL include ≥1 policy
  citation OR flag it `ungrounded`. *(ADR-0002)*
- **AC-C3** `[off]` The audited path SHALL use `retrieve` + our Converse prompt,
  never `retrieve_and_generate`.
- **AC-C4** `[gate]` WHERE the KB is live, retrieval SHALL filter on
  jurisdiction + line_of_business; each chunk SHALL carry the four metadata tags
  (jurisdiction, line_of_business, policy_form, effective_date); embeddings
  model + dims SHALL be recorded next to the index. *(ADR-0007, fast-follow)*

## D. Image understanding

- **AC-D1** `[off]` IF a packet is an image, THEN extraction SHALL still produce
  the schema-valid five-field JSON (eval covers ≥1 image sample).
- **AC-D2** The system SHALL read images via a vision FM (image content block)
  `[gate]` and record the resolved multimodal model id `[off]`. *(ADR-0006)*
- **AC-D3** `[off]` Image size SHALL be bounded at ingest.

## E. Routing + HITL

- **AC-E1** `[off]` WHEN validation completes, the system SHALL auto-approve
  **only if** schema-valid AND all required fields present AND grounded AND
  `claim_amount` ≤ `amount_threshold` AND no PII flag; otherwise route to human
  review. The predicate is a pure, unit-tested function.
- **AC-E1b** `[off]` The escalation policy SHALL be **configuration, not
  hardcoded** — `amount_threshold` (default **$10,000**) and the force-review
  flag set are supplied via config/env. *(configurability)*
- **AC-E2** `[sfn]` WHEN a claim routes to human review, the system SHALL pause
  on a `waitForTaskToken` state and write `pending-review/<key>.json`.
- **AC-E3** `[off]` WHEN a reviewer resumes the token, the system SHALL record
  `review:{decision, reviewer_id, timestamp, field_changes[]}`; on `correct` the
  reviewer's values become the **final recorded result with no
  re-summarize/re-validate** in the PoC.
- **AC-E4** `[sfn]` IF no decision arrives within 7 days, THEN the system SHALL
  mark the claim `review-expired` and escalate.
- **AC-E5** `[off]` A token SHALL be single-use — a duplicate resume SHALL NOT
  double-record. *(C9)*

## F. Recording + idempotency + audit

- **AC-F1** `[off]` WHEN a claim is recorded, `results/<key>.json` SHALL contain
  the full provenance tuple (§7 contract: extracted, summary, citations,
  ungrounded, validation, route, review?, guardrail, resolved model ids,
  prompt_versions, usage, sfn_execution_arn).
- **AC-F2** `[off]` WHEN the same key is processed twice, the system SHALL
  overwrite one result object (idempotent). *(C9)*
- **AC-F3** `[off]` No auto-approved result SHALL be recorded without the clean
  predicate (AC-E1) or a human `approve`. *(ADR-0005)*

## G. Orchestration (Step Functions)

- **AC-G1** `[sfn]` The workflow SHALL run on a Step Functions **Standard**
  workflow (not Express); each claim SHALL produce exactly one execution.
  *(ADR-0004)*
- **AC-G2** `[sfn]` Per-state Retry/Catch SHALL implement C2 (throttle), C7
  (timeout), C11 (RAG-down → ungrounded branch).

## H. Privacy / logging

- **AC-H1** `[off]` The system SHALL NOT write raw PII (e.g. an SSN) to
  application logs — log-shape test. *(fitness flagged by arch-validate)*
- **AC-H2** `[gate]` WHERE Guardrails enabled, PII in FM output SHALL be
  ANONYMIZED and `GUARDRAIL_INTERVENED` recorded. *(ADR-0008)*

## I. IAM (least privilege)

- **AC-I1** `[off]` IF any of the three PoC roles carries
  `AmazonBedrockFullAccess` or bucket-wide `s3:*`, THEN policy-lint SHALL fail.
  WHERE the operator role grants `states:SendTaskSuccess` /
  `states:SendTaskFailure`, IF those actions are scoped to a `stateMachine:`
  or `execution:` ARN, THEN HITL resume is `AccessDenied` (AWS documents
  empty Resource types for those actions) and policy-lint SHALL fail. Those
  two actions SHALL use `Resource: "*"` only, on the operator role only;
  optional `aws:SourceAccount` / `aws:RequestedRegion` MAY ride on top of
  `*`, not instead. No other statement in the three PoC roles SHALL use
  `Resource: "*"`. *(fitness flagged; ADR-0009)*
- **AC-I2** `[off]` Every Bedrock **invoke** statement SHALL name BOTH a
  `foundation-model/` ARN and an `inference-profile/` ARN. The model-id
  segment SHALL be a named pattern covering the spike models actually used
  (`anthropic.claude-*` and `amazon.nova-*`), not a pinned constant and not
  a bare `*`. *(ADR-0009)*

## J. Offline-first gate

- **AC-J1** `[off]` The offline suite SHALL pass with no AWS credentials;
  `aws_profile` stays `<none>`.
- **AC-J2** `[off]` Real-AWS execution SHALL require `CLAIM_PROCESSOR_REAL_AWS=1`.

---

## Clarify pass — RESOLVED (2026-09-21)

1. HITL **"correct"** → corrected values are **final**, no re-summarize (AC-E3).
2. **Auto-approve** clean claims per AC-E1 (humans see only flagged/risky).
3. **Amount threshold** = **$10,000**, and **configurable** (AC-E1b).
4. **KB/S3-Vectors** stays IN as fast-follow `[gate]` (AC-C4).
5. **F1 HITL IAM** — `SendTaskSuccess` / `SendTaskFailure` use `Resource: "*"`
   only (operator role). A `stateMachine:` ARN is `AccessDenied`. Optional
   account/region conditions may ride on `*`, not instead.
6. **F3 Bedrock invoke** — named Claude + Nova patterns (not
   `foundation-model/*`). Nova is required: `UNDERSTAND_MODEL_EXAMPLE` is
   `us.amazon.nova-pro-v1:0`.
7. **F4b ViaService** — PoC IAM pinned `us-east-1`; other
   `CLAIM_PROCESSOR_REGION` unsupported for IAM until T-15. `key/*` stays.
   `from_env` may still read the var.
8. **F8 CRLF** — dropped this iteration; H1 stays raw-PII only. No new AC.
9. **F9 test paths** — freeze §18 records landed `test_iam_policy.py` /
   `test_store_pending.py`. No code rename.
