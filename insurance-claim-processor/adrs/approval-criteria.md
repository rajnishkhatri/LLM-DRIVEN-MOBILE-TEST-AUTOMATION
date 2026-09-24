# ADR approval criteria — insurance claim document processor

**Agreed:** 2026-09-23 by Rajnish Khatri (**R7q-a**, the first-use duty of
arch-decide). **Applies to:** every ADR and every ADR amendment in this folder.

## Default

The owner may accept an ADR in-session. The agent drafts and stress-tests
ADRs, but never marks one Accepted without the owner's explicit yes.

## Triggers — an ADR or amendment that does any of these is *flagged*

1. **Widens IAM:** a new action, a new resource, or any `*`.
2. **Changes where PII flows or is stored:** a new place PII is sent,
   persisted, logged or displayed, or a change in what a PII control checks.
3. **Adds an AWS service.**
4. **Adds more than $50 / month** at the stated volume **[re-verify the
   prices used]**.
5. **Widens what can auto-approve:** the amount threshold, the clean
   predicate, a flag that stops blocking, or a mechanism that can relax
   acceptance rules.

## What a flagged ADR needs

- **Now (PoC, one owner):** its own approval, never inside a bundled
  approval such as "ratify as recommended". The change is shown next to the
  decision: the IAM diff, the data-flow diff, the cost, or the routing diff.
- **Before any real (non-synthetic) claim data:** a named security / privacy
  reviewer who is not the author signs off every flagged ADR. The sign-off is
  recorded in the ADR's Notes as "Reviewed by / date".

## How it is applied

arch-decide checks each new ADR or amendment against the triggers. It writes
the result in the ADR's Notes, for example "Approval criteria: flagged (1, 3)"
or "not flagged". Then it asks for approval in the form the result requires.

## Go-live review list (triggers applied retroactively, 2026-09-23)

These were accepted before the criteria existed. The reviewer signs them off
before any real claim data. Triggers are in brackets.

| ADR | Why flagged |
|---|---|
| 0001 | Bedrock added; claim text goes to the FM [2, 3] |
| 0004 | Step Functions added; claim data sits in execution history [2, 3] |
| 0005 | pending-review records hold claim data; sets the auto-approve defaults [2, 5] |
| 0006 | claim images go to a vision FM [2] |
| 0007 | Bedrock Knowledge Base + S3 Vectors (fast-follow, not built) [3] |
| 0008 | guardrail PII masking; the F14 amendment narrowed what the guardrail checks [2] |
| 0009 | IAM roles and grants [1] |
| 0010 | AppConfig added; config can change the amount threshold [3, 5] |
| 0015 | CloudWatch alarms, SNS and a remediation role that can deploy config [1, 3] |
| 0016 | M14 adds Amazon SQS (the trigger dead-letter queue) [3] |
| 0017 | EventBridge added; raw PII zones; images copied into bundles [2, 3] |
| 0018 | Comprehend, Textract and Transcribe added; claim content goes to them [2, 3] |
| 0019 | Glue Data Quality and its role [1, 3] |
| 0020 | four new roles; PII minimization layers [1, 2] |
| 0021 | images reach Bedrock; H-F14-a input tagging (images are not guardrail-checked) [2] |
| 0022 | data-quality proposals can relax acceptance rules (human-approved) [5] |

Not flagged: 0002, 0003, 0011, 0012, 0013 (watch its cost at volume), 0014.

**Note.** v1's 0001–0009 still read "Proposed" although v1 is built and live
on synthetic data. Setting their true status is a v1 re-entry item.
