# v2 HLD consistency pass — fold map (2026-09-23)

The single source of wording for the consistency pass. It lists every
ratified change and the HLD artifacts that must carry it. Sources of truth:
- `../risk/risk-storm-v2-data-prep.md` §5 (M1–M18);
- the "Amendments ratified 2026-09-23" sections of ADRs 0016–0022;
- the owner decisions below.

This is not a new design.

## Owner decisions (all 2026-09-23)

| Id | Decision |
|---|---|
| Ratification | The HLD was ratified as recommended. ADRs **0016–0022 are Accepted**. All mitigation packages are accepted: must-have M1 M2 M3 M4 M6 M7 M12 M13; should-have M5 M10 M14 M15 M16 M17 M18; hygiene M8 M9. **M11 goes to v1 re-entry.** |
| **R7q-a** | ADR approval criteria are adopted. Record: `../adrs/approval-criteria.md`. |
| **R8c-a** | Opt out of **all** AWS AI services' content use through an AWS Organizations AI-services opt-out policy. The **owner performs it** (an account-level security setting); status: *owner action pending* until verified. Verify with `aws organizations describe-effective-policy --policy-type AISERVICES_OPT_OUT_POLICY --target-id <account>`. The AWS-supported list includes Amazon Comprehend, Amazon Textract, Amazon Transcribe and AWS Glue. **Amazon Bedrock is not on it**, because Bedrock does not use content for service improvement. Until verified: synthetic data only. |
| **H-F14-a** | The v2 formatting contract uses Converse **input tagging**. See "Canonical wording for H-F14-a" below. |
| **D-a** | Keep the live v1 state (R0 + F14, deployed by the agent). **All future deploys are manual and owner-run**, as in v1. |
| Stage order | Finalize the HLD → **LLD** → spec (the implementation plan) → build → the owner's manual deploy. |
| F14 (live v1) | Input tagging in v1 (v1 AC-A5a, ADR 0008 amendment). **D0 is closed.** |

## Canonical wording for H-F14-a (use verbatim or near-verbatim)

- Every context section that contains claim-derived values travels inside Converse `guardContent`. That covers the intake record values, the claimant narrative, the OCR document text, the call transcript, the loss history and the reconciliation notes.
- Instructions, the output schema and policy excerpts travel as plain `text`.
- Images travel as plain `image` blocks and are **not guardrail-checked**. This loses nothing today: the guardrail's prompt-attack filter is TEXT-only and its harmful-content filters are off (verified with `get-guardrail`, 2026-09-23).
- Integrity against image-borne (visual) prompt injection rests on **M1** (the pre-routing check against canonical values) + routing on the canonical amount + deterministic routing.
- M10 escaping applies inside the guarded text.
- Contextual grounding stays inert (v1 finding F5: no `grounding_source` / `query` qualifiers).
- Revisit if image content filters are ever enabled. Whether the prompt-attack filter supports images at all is **[re-verify]**.

## Canonical names (do not invent others)

- **No new logical components.** M14's watchdog is a **second entry into
  Account Batch Outcome**: an intake execution FAILED / TIMED_OUT / ABORTED
  event → a `batch_failed` summary + the metric **`BatchFailed{Status}`**.
- The other amendments land in these components:
  - M1 lands in v1 **Validate Extracted Content** (and **Route Claim** for
    the threshold).
  - M15 / M16 land in v1 retrieval / degradation for bundle keys.
  - M18 lands in v1 **Route Claim** / **Record Processing Result**.
- Physical, container level:
  - M14's watchdog is an EventBridge rule on intake-execution status-change
    events, targeting the intake step function.
  - The intake trigger gets a dead-letter queue, **"Trigger dead-letter queue"
    [Amazon SQS]**.
  - Step Functions emits the status-change events itself.
- Flags (exact spellings): `bundle:fm_source_mismatch:<field>`, `dq_warn:ambiguous_date`, `invalid_schema`, `recon_unverifiable:<field>`, `source_disabled:<src>`, `history_failed`, `history_unavailable`, `image_withheld:pii`, `batch_failed`.
- Keys: `intake/v=1/…`, `raw/claims/<claim_id>/…`, `bundles/<claim_id>/r<rev>`, `processed/claims/<claim_id>/r<rev>/…`.

## Per-mitigation fold

| Id | Canonical content | Components | Diagrams | Design §9 | Clinic | Validation (new G-row) |
|---|---|---|---|---|---|---|
| M1 | Pre-routing check of FM output against canonical intake values (`claim_amount` within tolerance, `incident_date`, `policy_number`) → blocking `bundle:fm_source_mismatch:<field>`; the threshold routes on the **canonical** amount. Resolves correction C-1. | v1 Validate Extracted Content, Route Claim | 02 DSTEP detail | §9.4.1, §9.9 | — | yes |
| M2 | Ambiguity-aware canonicalizer: a date with day ≤ 12 that is valid both ways → blocking `dq_warn:ambiguous_date` unless independently corroborated; date order keyed by source / issuer, not channel | Canonicalize Values | 03 CAN | §9.8 | — | yes |
| M3 | Catalog hardening + key contract: completeness renders as non-empty; header exact-match → `invalid_schema`; report_date ≥ loss_date; exactly one CSV per partition; attachments confined to `raw/claims/<claim_id>/`; `intake/v=1/…` path | Intake Rule Catalog, Admit Intake Batch | 03 RCAT, ADM; 02 S3 | §9.8 | — | yes |
| M4 | Unverifiable is not clean: blocking `recon_unverifiable:<field>` (a low-confidence sole source), `source_disabled:<src>`, `history_failed`, `history_unavailable`; the loss-run join and dates go through Canonicalize Values | Reconcile Claim Facts, Summarize Loss History | 03 RCF | §9.9 | — | yes |
| M5 | Revision and replay governance: resubmitting a decided claim → human review only (unless it is a DQ-owner-tagged proposal re-run); replay over the whole channel / partner scope reports fixed / broken / unchanged, and any break blocks; scope keyed by partner id; the measuring prompt hides the intake record; degraded results are excluded | Propose Quality Rule Change, Measure Extraction Agreement, Dispatch Claim Decision | 03 MEA, DSP | §9.9 | — | yes |
| M6 | PII: + `DRIVER_ID` / `PASSPORT_NUMBER` and peers; transcripts and OCR text are **redacted** (not "verified") + a stdlib scrub of runs of ≥ 4 digits in transcripts; images go to the FM **only** when OCR confidence is insufficient **and** no PII was found in that document; OCR insufficient **but** PII found → the image is withheld, blocking `image_withheld:pii`; OCR sufficient → no image and no flag (clarified 2026-09-23; the OCR-sufficiency threshold is an LLD item); pixel redaction deferred; an explicit **Deny `raw/*`** on v1's step-lambda role | Redact Sensitive Data, Format Model Context | 03 RSD, FMC; 02 DSTEP | §9.5, §9.6 | — | yes |
| M7 | AI-services opt-out = **R8c-a** (above) | — (account-level) | 01 CMP / TXT / TRS / GDQ detail | §9.5 | — | yes (manual check) |
| M8 | Tighten v1 wildcards: `sfn-exec.json` → explicit function ARNs; `remediation.json` → the `model-selection` profile only; lint: no v1 grant may match a v2 resource — except SD-4's designed `s3:GetObject` on `bundles/*` (clarified 2026-09-23) | — (IAM) | — | §9.6 | — | yes |
| M9 | Quarantine and feedback records hold **no values** (row index + rule ids + object version); `dq propose` runs S3-side only | Account Batch Outcome, Measure Extraction Agreement, Propose Quality Rule Change | 03 ACC | §9.8 | — | yes |
| M10 | Escape `<` and `>` in claimant-derived text inside the context tags (+ a formatter test) | Format Model Context | 03 FMC | §9.4 | — | yes |
| M11 | **v1 re-entry** (pin a numbered guardrail version) | — | — | v1 re-entry list only | — | — |
| M12 | Revision-scoped keys (`bundles/<id>/r<rev>`, `processed/claims/<id>/r<rev>/…`); v1 result / pending keys follow the bundle key; the S3 **VersionId** travels in the v1 input and the lineage; feedback pairs by revision | Assemble Claim Bundle, Dispatch Claim Decision, v1 Record Processing Result | 02 S3 + dispatch edge; 03 ASM, DSP | §9.8 | — | yes |
| M13 | Lock correctness: holder ARN == `$$.Execution.Id` → a self-retry proceeds; `states:DescribeExecution` on intake executions (takeover); `CreatePartition` `AlreadyExistsException` counts as success | Admit Intake Batch | 03 ADM | §9.6, §9.9 | C9 row | yes |
| M14 | Watchdog + limits: an EventBridge rule on intake execution FAILED / TIMED_OUT / ABORTED → `batch_failed` summary + `BatchFailed{Status}`; an alarm on intake `ExecutionsFailed`; a DLQ on the trigger (Amazon SQS); intake-Lambda reserved concurrency ≥ 20; inline Map ≤ **50** claims; **Distributed Map (a Standard child execution per claim)** for 51–200; > 200 rows quarantined at admission (ADR 0019); trim iteration outputs (`ResultSelector`) | Account Batch Outcome (second entry) | 02 IWF detail + IWF→EB, EB→ISTEP, EB→DLQ edges + DLQ node; 03 EB→ACC edge | §9.7, §9.9 | knobs + metric | yes |
| M15 | For bundle keys, RAG scope = the canonical intake jurisdiction and line of business | v1 retrieval | 02 DSTEP (optional) | §9.3 / §9.9 | — | yes |
| M16 | For bundle keys, the rule-based degrade floor = the canonical intake fields (deterministic; still routes to review) | v1 degradation | — | §9.9 | C11 row | yes |
| M17 | Pin the DQ config per batch at Admit; `config_source=fallback` → quarantine (fail closed); the catalog hash is stamped into the Glue ruleset description and compared | Admit Intake Batch, Gate Batch Quality | 03 ADM, GBQ | §9.9 | — | yes |
| M18 | Fail closed on missing flags: a `bundles/` key whose state lacks `bundle_flags` → review; Record re-checks routing for dict payloads; runbook: publish Lambda versions and switch alias-qualified ARNs together (the alias part can wait for IaC) | v1 Route Claim, Record Processing Result | — | §9.9 | — | yes |
| H-F14-a | See the canonical wording above | Format Model Context | 03 FMC; 02 DSTEP / BR | §9.4, §9.5 | — | yes (sentinel formatter test) |

## Also fix everywhere in the v2 addenda

- Honesty tags `(PROPOSED ADR 00xx)` become `(ADR 00xx)`.
- "Pending your approval", "proposed" or "pending R8b" wording about
  decisions that are now ratified becomes the ratified wording.
- **Do not touch the v1 sections.** Stale v1 items go to the v1 re-entry list,
  not into edits: v1 top-of-file "GATE: PENDING HUMAN" markers, ADRs 0001–0009
  still reading "Proposed", the v1 component-table drift, the stale v1 style
  text, the v1 5 × 5 retry amplification, M11, F2, F5.
