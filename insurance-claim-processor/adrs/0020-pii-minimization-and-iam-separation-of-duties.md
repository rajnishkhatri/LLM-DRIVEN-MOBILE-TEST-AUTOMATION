# ADR 0020. Minimize PII before persistence, and separate raw-PII readers from Bedrock callers

## Status
Accepted — 2026-09-23 (ratified as recommended; amendments below). Formerly: Proposed. Extends ADR 0008 (Guardrails stay at the FM boundary) and ADR 0009
(new least-privilege roles). Related: 0017 (zones, SD-4), 0018.

## Context
v2 multiplies the PII surface:
- spoken SSNs and card numbers in call audio;
- names, addresses and licence numbers on police reports;
- free narratives.

v1's controls act at the **FM boundary** (the Guardrail on Converse, ADR 0008)
and on **outputs** (the validator regex, `../build/claim_processor/validator.py:10-11`).
Neither prevents raw PII from being *persisted* into new processed artifacts,
bundles, transcripts or logs. Privacy is a v2 top-3 characteristic
(`../worksheets/characteristics-worksheet.md` v2).

IAM facts (spec P-k, AWS service-reference JSON): Comprehend Detect*,
Textract AnalyzeDocument and Transcribe StartTranscriptionJob have **no
resource type**, so `Resource:"*"` is unavoidable for them.

Alternatives:
- **Where to minimize:**
  - (a) the Guardrail only, at the FM boundary (v1 as-is);
  - (b) **typed redaction before persistence** (Comprehend `DetectPiiEntities`
    with offsets) + source redaction (Transcribe) + the Guardrail + the
    validator;
  - (c) redact everything, including names and dates (starves extraction).
- **Roles:**
  - (i) extend v1's single step-Lambda role with the new grants;
  - (ii) **separate roles by data sensitivity**.

## Decision
We will **minimize PII before anything persists**. And we will **separate
duties so that no role can both read raw PII and call Bedrock**.

**Four layers:**
1. **Transcribe `ContentRedaction`** at the source: redacted output only, for
   SSN, card number / CVV / expiry, bank account / routing, PIN.
2. **Typed redaction** (`[SSN]`, …) of narratives and OCR text via Comprehend
   `DetectPiiEntities` offsets, before `processed/` or `bundles/`. Names,
   addresses and dates are kept, because extraction needs them.
3. **The Bedrock Guardrail on every Converse call** (unchanged, ADR 0008).
4. **The v1 validator** on outputs → human review.

Plus the redacting logger and metric emitter for every intake log line and
metric.

**Roles:**
- `claim-processor-intake-lambda` reads the raw zone and calls the perception
  services. It has **no Bedrock** grant.
- v1's `claim-processor-step-lambda` calls Bedrock and gains **only**
  `s3:GetObject` on `bundles/*` (curated, redacted text + copied images,
  ADR 0017).
- The other new roles are narrow: `-intake-sfn` (invoke the intake Lambda);
  `-glue-dq` (read intake CSVs, write DQ results, namespace-conditioned
  metrics); `-intake-events` (start the intake machine).
- `Resource:"*"` only on the no-resource-type actions (plus `PutMetricData`
  with a namespace condition). Everything else is scoped:
  - `GetTranscriptionJob` → `transcription-job/clm-*`;
  - Glue DQ → `dataQualityRuleset/claims-intake*`;
  - `iam:PassRole` → the Glue role, with `iam:PassedToService`;
  - `StartExecution` → the v1 machine.

Justification:
- **Technical:**
  - Defense in depth, because no detector has 100 % recall.
  - Persistence is where PII becomes *breach-able*, so minimization must
    precede it.
  - Separation of duties makes the *raw zones* unreadable to the
    model-calling role by IAM.
    **Corrected by the risk storm (C-3):** that is not an "IAM impossibility"
    for everything Bedrock sees.
    - Text written into `bundles/` by the raw-reading role is trusted by
      **code convention** (redaction + the scanner test), not IAM.
    - **Document images carry PII into `bundles/` and Bedrock by design**
      until **M6(c)** (images only when OCR confidence is insufficient) is
      accepted.
    - The breach-notification identifiers (driver's licence, passport) need
      **M6(a)**.
    - AI-services content use needs the **M7** opt-out.

    All were accepted at ratification (`../risk/risk-storm-v2-data-prep.md` §5).
    M7 was decided as R8c-a; the owner performs it.
- **Business:** a smaller breach radius and a simpler privacy review. The
  regulator story holds only in its qualified form: "the model-calling role
  cannot read raw zones; what it reads is redacted text plus, when needed,
  document images."

**Residual risk, accepted and flagged:** PII inside **document images**
reaches Bedrock unredacted (in-account). Comprehend cannot redact pixels, and
Guardrail PII filters are text-oriented **[re-verify image support]**.
This guardrail checks no image content at all today: its prompt-attack filter is
TEXT-only and its harmful-content filters are off (verified 2026-09-23). v2
sends images as untagged blocks (H-F14-a, ADR 0021).
Mitigations:
- send only the document types reconciliation needs;
- the **M6 image rule** (accepted 2026-09-23; it supersedes the image-drop
  knob): an image reaches the FM only when OCR confidence is insufficient and
  no PII was found in that document;
- no image persisted outside `bundles/`.

→ arch-risk.

## Consequences
**Good:**
- Redacted artifacts everywhere downstream of intake.
- An IAM-enforced boundary between raw PII and the model.
- Every PII event is countable (`PiiRedacted{Type}`).

**Bad / accepted:**
- One extra Comprehend call per text source (cost is cents).
- Redaction can remove something extraction needed. Mitigation: redact only
  high-risk types, and reconcile against the unredacted structured intake
  fields.
- Four roles to maintain and lint.

**Losers:**
- (a) Guardrail-only: PII persists in `processed/`, bundles and transcripts.
- (c) Redact everything: breaks extraction (integrity).
- (i) One shared role: any code path could send raw PII to Bedrock; the
  boundary would be conventional, not enforced.

## Compliance
Offline fitness:
- **IAM policy-lint** (extends AC-I1/I2):
  - `*` only on the allowlisted actions;
  - v1 role has no `raw/*` and no Transcribe, Comprehend or Textract grants;
  - intake role has no `bedrock:*`;
  - PassRole is conditioned.
- **PII scanner** over every persisted artifact of the seeded corpus run:
  zero high-risk hits.
- **Stubber:** Transcribe requests carry `ContentRedaction` with the
  `redacted` output; only `RedactedTranscriptFileUri` is read.
- **Log-shape test** extended to the intake steps.

`[gate]`: simulate-principal-policy denies `bedrock:InvokeModel` for the
intake role and `s3:GetObject raw/claims/*` for the v1 role.

## Amendments ratified 2026-09-23 (risk storm, `../risk/risk-storm-v2-data-prep.md` §5)
- **M6** PII: + `DRIVER_ID`/`PASSPORT_NUMBER` (and peers); transcripts and OCR text redacted (not verified) + stdlib scrub of ≥4-digit runs in transcripts; images to the FM only when OCR confidence is insufficient **and** no PII was found in that document. OCR insufficient but PII found → blocking `image_withheld:pii`. OCR sufficient → no image, no flag (clarified 2026-09-23); explicit **Deny `raw/*`** on v1's step-lambda role.
- **M7** AWS Organizations AI-services opt-out. **R8c-a (owner, 2026-09-23):** opt out of **all** AI services at the organization root.
  - The owner performs it; **action pending until verified** with `describe-effective-policy`. Until then, synthetic data only.
  - Re-verified against the AWS Organizations docs (2026-09-23): AI services "may use and store customer content for service improvement", possibly in another Region, unless opted out.
  - The supported list includes Comprehend, Textract, Transcribe and Glue; Bedrock is not on it. Opting out deletes content already stored for that purpose.
- **M8** tighten v1 wildcards (`sfn-exec.json` explicit ARNs; `remediation.json` → `model-selection` profile only) + lint rule: no v1 grant matches a v2 resource — except SD-4's designed `s3:GetObject` on `bundles/*` (clarified 2026-09-23).

Detailed EARS criteria land in the spec revision (R10).

## Amendment (ACCEPTED 2026-09-24) — the LLD's IAM and PII detail
**Status: Accepted (2026-09-24).** Flagged under approval criteria 1 and 2,
and approved on its own in three parts (`../design/lld-v2-data-prep.md`
Appendix B):
- B6-6-a (`ask` runs as v1's `operator` role) and B4-5-a (transcript
  encryption, below), each on its own;
- the IAM diff in its corrected form ("IAM ok"), after the two independent
  reviews of LLD Waves B and C changed it. The diff is LLD §6.13, and the
  JSON is LLD Appendix C.

Before any real claim data, a named security / privacy reviewer who is not
the author signs this amendment off (`approval-criteria.md`).

What the LLD adds to this ADR's decision:
- **Five v2 identities, not four.** The four above, plus
  `claim-processor-dq-owner`. The owner assumes that role from the deployer
  user to run `python -m claim_processor.dataprep dq …`. It reads the pinned
  configs, the quality records, three processed files and the bundle JSON
  (never the image copies). It reads the intake CSV **only by VersionId**, for
  replay (the only `s3:GetObjectVersion` in the design). It writes only
  `quality/proposals/*`. It has no AppConfig grant. Like every v2 identity, it
  carries an explicit `Deny bedrock:*`: it reads raw PII, so it must not call
  Bedrock (LLD IAM-48 – IAM-54).
- **Two resource policies.** A function policy lets the feedback and watchdog
  rules invoke `claim-processor-intake-step`, each pinned to its rule's ARN.
  A queue policy lets only the trigger rule send to the dead-letter queue
  (LLD IAM-38 – IAM-43).
- **L4 (M14).** The intake machine's own role may start and describe its own
  Distributed Map children and read the row-gate worklist. There is no
  `StopExecution`, no `ResultWriter` and no redrive (LLD IAM-27 – IAM-31).
- **No `*` for Glue.** Every Glue DQ action has a `dataQualityRuleset` form.
  The closed `Resource: "*"` list is Comprehend, Textract, Transcribe start,
  the Glue role's namespace-conditioned `PutMetricData`, and v1's HITL
  resume (LLD §6.11).
- **No managed policies on v2 roles.** Logs are a scoped grant on each
  function's own log group (LLD IAM-04, IAM-24).
- **v1 narrowing beyond M8.** Every v1 S3 resource names the exact bucket,
  including the write grant and `operator`'s read. The explicit Deny covers
  `history/*` too (LLD IAM-57 – IAM-65).
- **Layer 2's type lists.** 24 high-risk types are replaced at any score;
  `NAME`, `ADDRESS`, `DATE_TIME` and nine other types are kept. A test fails
  when AWS adds a type nobody has decided (LLD CMP-06, CMP-07; B4-3-a,
  decided 2026-09-24). Layer 1 stays this ADR's seven Transcribe types (LLD
  TRN-03).
- **Transcript encryption (B4-5-a, approved 2026-09-24).** Transcribe writes
  its output with the caller's permissions, and with SSE-S3 when no key is
  given [re-verify whether the bucket's default SSE-KMS applies instead]. That
  is accepted for the PoC. The first smoke records which encryption applies,
  and the go-live reviewer decides before any real data (LLD IAM-46, IAM-47).
- **`ask` (SD-3; B6-6-a, approved 2026-09-24).** v1's `operator` role gains
  `s3:GetObject` on `bundles/*`, `bedrock:ApplyGuardrail` on the one
  guardrail, and the same Deny on the raw and v2 zones as the step Lambdas.
  v1 deferred creating the role with HITL, so v2 creates it, trusted only by
  the deployer user. Its unchanged `HitlResume` on `*` goes live with it; no
  task token exists until F2 ships (LLD IAM-91, IAM-92).
- **Review corrections (2026-09-24).** The intake Lambda loses two unused
  grants: `GetObject` and `ListBucket` on `quality/dq-results/*`. It gains one
  list prefix, `quality/pins/*`, so a self-retry finds its own pin (LLD
  REC-14). Three reads the draft could not make are designed away without a
  grant: `claim_check` derives the v1 name, `feedback` decides "first" from
  the v1 record, and `themes` lists first (LLD ASL-19, REC-27, CMP-19). The
  Distributed Map describe grant stays the documented `execution:<name>:*`
  (docs re-read 2026-09-24); the 51-row batch B0003 probes it (LLD IAM-29).

Approval criteria: flagged (1, 2).
Approved by / date: Rajnish Khatri / 2026-09-24 — B6-6-a and B4-5-a, each on
its own; the corrected IAM diff (LLD §6.13) on its own ("IAM ok").
Reviewed by / date: _(before real data: the go-live security / privacy
reviewer)_

## Notes
Author: arch-decide (v2 HLD, provisional batch A2-a)
Approved by / date: Rajnish Khatri / 2026-09-23 ("ratify as recommended")
Superseded date:
Last modified: 2026-09-24 / LLD amendment accepted ("IAM ok")
