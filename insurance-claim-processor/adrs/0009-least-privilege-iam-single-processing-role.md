# ADR 0009. Least-privilege IAM: three roles, one shared step-Lambda role

## Status
Proposed — depends on ADR 0004, 0007, 0008

## Context
The Step Functions runtime (ADR 0004) plus Guardrails (ADR 0008) and the KB
fast-follow (ADR 0007) need IAM. Insurance and the auditability characteristic
demand least-privilege and a small, explicit set of principals. The load-bearing
footgun is the Bedrock **two-ARN trap**: a modern `us.`/`global.` model id is an
inference-profile id, so a role needs **both** a `foundation-model/` ARN **and**
an `inference-profile/` ARN or it gets an intermittent `AccessDenied`
(`cases/aws-ai/ch06.md:72-81`). Wave 1 review (F1/F3/F4b) added three further
forces: (1) `states:SendTaskSuccess` / `SendTaskFailure` have empty Resource
types — a `stateMachine:` ARN is `AccessDenied`, so HITL cannot be
resource-scoped; (2) spike defaults include Nova
(`UNDERSTAND_MODEL_EXAMPLE = us.amazon.nova-pro-v1:0`) as well as Claude, so a
Claude-only pattern fails the image path; (3) static IAM cannot follow
`CLAIM_PROCESSOR_REGION`, and this ADR never names a CMK.

## Decision
**Three roles**, none carrying `AmazonBedrockFullAccess` or bucket-wide `s3:*`:

1. **SFN execution role** — `lambda:InvokeFunction` on the step Lambdas +
   CloudWatch Logs (execution history). Nothing else.
2. **Step Lambda role — single, shared:**
   - `bedrock:InvokeModel` + `InvokeModelWithResponseStream` on **both** a
     `foundation-model/` ARN and an `inference-profile/` ARN; the model-id
     segment is a **resolved pattern** covering the spike models
     (`inference-profile/us.anthropic.claude-*` and
     `inference-profile/us.amazon.nova-*`, plus the matching
     `foundation-model/` patterns), marked *pattern, not a pinned
     constant* and not a bare `*`.
   - `bedrock:ApplyGuardrail` on the guardrail arn (ADR 0008).
   - `s3:GetObject` on `claims/*`; `s3:PutObject` on `results/*` +
     `pending-review/*`.
   - `kms:Decrypt` / `GenerateDataKey` scoped by `kms:ViaService`
     `s3.us-east-1.amazonaws.com` + `bedrock.us-east-1.amazonaws.com`;
     Resource `arn:aws:kms:*:*:key/*` (ViaService, not a named CMK). PoC IAM
     is **us-east-1 only** — other `CLAIM_PROCESSOR_REGION` values are
     unsupported for IAM until T-15.
   - *(fast-follow)* `bedrock:Retrieve` on the `knowledge-base/*` arn.
3. **Operator / CLI role** — `states:SendTaskSuccess` / `SendTaskFailure`
   with `Resource: "*"` (HITL resume; AWS empty Resource types for those
   actions — not scoped to a `stateMachine:` ARN). Identity compensation:
   these actions live only on the operator role. Optional conditions
   (`aws:SourceAccount`, `aws:RequestedRegion`) may be added; they do not
   replace `*`. Also `s3:GetObject` on `pending-review/*`;
   `bedrock:InvokeModel` for the feasibility spike (same Claude+Nova
   patterns).

KMS: bucket default encryption + `kms:ViaService` key policy. PrivateLink /
`aws:sourceVpce`: **not in the PoC** (noted for production residency).

Rejected: **split-by-trust roles** for the PoC (a Bedrock-only role vs a
write-capable role) — over-split for coarse states + a manual deploy; named as
**production hardening** when the pipeline splits into per-component Lambdas.
Rejected: any `bedrock:*` / `AmazonBedrockFullAccess` wildcard.
Rejected: Claude-only `us.anthropic.claude-*` (Nova understand path would
`AccessDenied`). Rejected: templating `${Region}` in static JSON (PoC has one
region; revisit at T-15). Rejected: pin `alias/claim-processor` (invents a
key this ADR does not evidence).

Justification: least-privilege at the action/resource level without a role
explosion; the two-ARN + named-pattern rule prevents the classic intermittent
outage *and* the image-path Nova miss; HITL `*` is the only IAM-legal shape
for SendTask*; a small, explicit principal set is what an auditor reads.

## Consequences
Good: few, auditable principals; the two-ARN + Claude+Nova pattern rule
pre-empts the "works in console, `AccessDenied` in Lambda" failure and the
vision-FM miss; HITL resume is actually grantable.
Bad: one shared step-Lambda role means a compromised extract step could write
results (accepted for the PoC; production splits by trust); deferring
PrivateLink means traffic uses AWS network edges (in-account) — revisit under a
residency requirement; SendTask* `*` is wider than a state-machine ARN (accepted
because AWS will not evaluate one — compensate with operator-only identity and
optional account/region conditions); a second region requires a T-15 IAM
revisit, not a silent env-var follow.

## Compliance
Fitness: no role carries `AmazonBedrockFullAccess` or bucket-wide `s3:*`;
every Bedrock invoke names both a `foundation-model/` and an
`inference-profile/` ARN whose model-id segment is the Claude+Nova
pattern (not a bare `*`, not a pinned constant); operator HITL
`SendTaskSuccess`/`SendTaskFailure` is `Resource: "*"` and no other
PoC statement uses `*`; KMS is `key/*` + ViaService
`s3.us-east-1` / `bedrock.us-east-1` (PoC region pin).

## Notes
Author: aws-ai-design (provisional kata run)
Approved by / date:
Last modified: 2026-09-21 (bounded amend: F1 SendTask* cannot be
resource-scoped; F3 Claude+Nova invoke patterns; F4b us-east-1 ViaService,
`key/*` not a named CMK)
