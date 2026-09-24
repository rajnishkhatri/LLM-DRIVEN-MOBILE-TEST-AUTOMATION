# Spec — claim processor v2: data-preparation plane (validate · multimodal · format for Claude · quality feedback)

> **ON HOLD (owner sequence, 2026-09-23):** finalize the HLD
> (`../design/hld-v2-data-prep.md`), then the LLD, then revise this spec from
> the LLD. The draft below predates the HLD ratification. It does not yet carry
> SD-1…SD-6, the accepted risk-storm amendments or H-F14-a. Do not build from it.

**Stage:** sdd-spec (Stages 2–4), compact per decision **C7-a**: brainstorm
record + spec + plan + tasks in ONE file, one ADR (**0016**). **Status:**
DRAFT 2026-09-23 — awaiting the single human gate (§8). **New increment
(v2).** The prior specs stay **FROZEN** and additive-only:
`./claim-processor-real-aws.spec.md` (A–J), `./claim-processor-model-resilience.spec.md` (K–R).
This file owns **S–Z**.
**Binding:** `.sdd` `[roots] claim-document-processor = insurance-claim-processor/`.
**Design:** ADR [0016](../adrs/0016-data-preparation-plane-intake-state-machine.md);
`../design/solution-design.md` gets a §9 addendum in DP-23.
**Constitution:** `.cursor/rules/architecture-principles.mdc` (principles, no
numbered invariants) + the frozen kata invariants A–R above.
**Test gate:** offline `unittest` in `../build/` (no creds); real AWS behind
`CLAIM_PROCESSOR_REAL_AWS=1` + the interactive one-step-per-turn deploy.

**Verification tags:** `[off]` offline (Stubber/unit/grep); `[gate]` real-AWS
gate; `[sfn]` state-machine layer (definition test + deploy check); `[infra]`
runbook/config review, not unit tests.

---

## 0. Decisions in force (confirmed by the human, 2026-09-23)

| Id | Decision |
|---|---|
| C1-a | Map the assignment's customer-feedback domain onto claims (table §1.3). |
| C2-a | A **separate** intake state machine produces a per-claim **bundle**; the live claim workflow (v1) consumes it. |
| C3-a | Glue Data Catalog + Glue Data Quality, Comprehend, Textract, Transcribe, Lambda for the tabular summary. **No** SageMaker, **no** Rekognition. |
| C4-a | Feedback loop **proposes**; a human approves; nothing auto-applies. Reuses the remediation discipline (ADR 0015). |
| C5-a | Offline suite + synthetic data generator, then real-AWS deploy + smoke in acct `324177727513` / `us-east-1`. |
| C6-a | v1 open items (F2 HITL, F10/F11, teardown) stay a separate track. |
| C7-a | This compact spec + ADR 0016, then build in waves. |

## 1. Brainstorm record (Stage 1, compressed)

### 1.1 Premise audit

| # | Premise | Status | Evidence |
|---|---|---|---|
| P-a | v1 is live on real AWS (auto-approve path) | verified | `build/DEPLOY-LEDGER.md` Stage 9: `smoke-1-auto-approve` SUCCEEDED |
| P-b | v1 already formats multimodal Converse requests | **partly refuted** | `understand.py` `to_content_blocks` builds ONE block (text *or* one image). The only image sample `samples/claims/auto-fl-photo.png` is a **1×1 px, 70-byte placeholder**. v1 has never read a real image. v2 must supply real document images and a multi-block request. |
| P-c | v1's ingest image cap is safe for Converse | **refuted** | `understand.py:9` `MAX_IMAGE_BYTES = 5_242_880` (5 MiB). Converse allows **≤ 20 images, each ≤ 3.75 MB / 8000 px**; images only in the `user` role (botocore `bedrock-runtime` `Message.content` doc). A 3.75–5 MiB image passes v1's cap and then fails at Bedrock. → hygiene **H1** (do regardless). |
| P-d | The assignment's Glue DQ Python API | **refuted** | `awsglue.data_quality.DataQualityRule` is not a boto3 API. `glue.CreateDataQualityRuleset.Ruleset` is a **DQDL string** (≤ 65,536 chars). |
| P-e | The assignment's S3 → Lambda `create-event-source-mapping` | **refuted** | Event-source mappings accept only Kinesis, DynamoDB Streams, SQS, MSK, MQ and DocumentDB (botocore `lambda` `CreateEventSourceMapping.EventSourceArn`). v2 uses S3 → **EventBridge** → Step Functions. |
| P-f | The assignment's Transcribe Lambda waits in a `while/sleep` loop | **refuted as a pattern** | The Lambda is billed while it sleeps and has a 15-minute cap. v2 polls from a Step Functions Wait → Get → Choice loop with a poll budget. |
| P-g | The assignment drops low-quality reviews (`quality_score < 0.7 → return`) | **refuted for claims** | A claim cannot be silently dropped. Low quality → human review with reasons (T2). |
| P-h | Comprehend size limits | verified | DetectSentiment 5 KB; BatchDetectSentiment ≤ 25 docs × 5 KB; Detect{Entities,KeyPhrases,PiiEntities,DominantLanguage} 100 KB (botocore `comprehend` docs). → chunking (U1). |
| P-i | Glue DQ can evaluate one batch partition | verified | `GlueTable.AdditionalOptions` supports `pushDownPredicate`. Run `Status` ∈ {STARTING…SUCCEEDED, FAILED, TIMEOUT}. The result has `Score` + `RuleResults[{Name, Result, EvaluationMessage…}]`. `AdditionalRunOptions{CloudWatchMetricsEnabled, ResultsS3Prefix}`. `NumberOfWorkers` defaults to 5 (G.1X). |
| P-j | Idempotent batch lock without DynamoDB | verified (API) / `[gate]` (behaviour) | S3 `PutObject.IfNoneMatch` returns 412 when the key already exists. |
| P-k | IAM resource scoping for the new services | verified | AWS service-reference JSON, fetched 2026-09-23. **No resource type** (so `Resource:"*"` is required): `transcribe:StartTranscriptionJob`, `comprehend:Detect{KeyPhrases,Sentiment,PiiEntities,DominantLanguage}`, `comprehend:BatchDetectSentiment`, `textract:AnalyzeDocument`, `textract:DetectDocumentText`. `comprehend:DetectEntities` can only be scoped to *custom* endpoints, so the built-in model needs `*`. **Scopable:** `transcribe:GetTranscriptionJob` → `transcription-job/${JobName}`; Glue DQ run/result actions → `dataQualityRuleset/${RulesetName}`; Glue catalog actions → `database/`/`table/` ARNs; `states:StartExecution` → the state-machine ARN. |
| P-l | Synthetic data needs no new dependency | verified (probe) | A stdlib-written one-page PDF renders to a 612×792 PNG via `sips`. `say --data-format=LEI16@16000` produces 16 kHz mono PCM WAV (Transcribe `MediaFormat=wav`). The generator is macOS-only; its outputs are committed, so tests never need `say` or `sips`. |
| P-m | v1 open items | verified open | Walkthrough findings register: F2, F10, F11 open. **Consequence:** on real AWS, v2 human-review claims stop at `AwaitReview` exactly as v1's do. The HITL-correction feedback signal (X3) is offline-only until F2 lands. |
| P-n | The test gate allows new stdlib modules | **refuted** | `tests/test_no_new_deps.py` has a fixed `_STDLIB` allowlist and scans `claim_processor/*.py` top-level only. v2 must extend the allowlist (stdlib only) and scan subpackages (`rglob`). |
| P-o | Deploy coordinates | verified | acct `324177727513`, `us-east-1`, bucket `claim-documents-poc-rk-20260922`, AppConfig app `claim-processor` (ledger Stages 0–3). |

### 1.2 Directions

| Id | Direction | Verdict |
|---|---|---|
| D-A | **Separate intake state machine → bundle → v1** (follows v1's orchestration pattern, ADR 0004; claim-check via S3 as in `store.py`) | **Chosen (C2-a)** |
| D-B | New states inside the v1 state machine | Rejected. It couples batch-scoped DQ (minutes, one per batch) with the per-claim decision workflow (AC-G1 one execution per claim). It would also redeploy the live machine for every intake change. |
| D-C | S3-triggered Lambda chain with key rewriting (the assignment's shape) | Rejected: P-e, P-f; no orchestration audit trail; brittle `key.replace(...)`. |
| D-D | Bedrock Data Automation as one multimodal extractor | Deferred. The assignment names Textract, Transcribe and Comprehend, and v1 lists BDA as out of scope. Recorded as a future option. |
| D-E | *Demand-side:* skip FM extraction when intake, OCR and narrative already reconcile | Deferred. It changes what the approval gate is based on (AC-E1 assumes an FM extraction), so it needs its own ADR. The reconciliation block (V1) is the substrate it would need. |
| D-F | *Under-used signal:* FM-vs-source disagreement plus reviewer `field_changes` drive the quality loop | **Adopted** as §X (C4-a). |

### 1.3 Domain mapping (C1-a)

| Assignment | v2 on claims | Section |
|---|---|---|
| Glue DQ on structured feedback | Glue DQ (DQDL) on **claim-intake batches** (CSV) | S |
| Lambda validation of text reviews | Lambda validation of **claimant narratives** | T |
| CloudWatch quality metrics | EMF metrics + dashboard + alarms | Y |
| Comprehend entities / sentiment | Narratives + call transcripts | U |
| Textract on product images | **Police-report / repair-estimate images** with Textract Queries | U |
| Transcribe service calls | **First-notice-of-loss (FNOL) call recordings**, PII-redacted | U |
| Survey table → natural-language summary | **Policy loss-run (prior-claims) table** → deterministic summary (recommended; S1) | U |
| Format for Claude / conversation templates / multimodal requests | Bundle `fm_request` + dialog template + multi-image request | V, W |
| Comprehend themes · normalization · feedback loop | Batch themes · normalizer · proposal loop | U12, T, X |

---

## 2. Scope

**In:** S intake + Glue DQ gate · T narrative validation + normalization · U
Comprehend / Textract / Transcribe / loss-run summaries + themes · V bundle
(reconcile, score, format for Claude) · W v1 consumes the bundle · X
human-approved feedback loop · Y metrics, dashboard, alarms · Z orchestration,
idempotency, IAM, privacy, offline-first, cost. Plus hygiene **H1**.

**Out:** SageMaker Processing, Rekognition, Comprehend topic-modeling jobs or
custom classifiers, Transcribe Call Analytics, BDA, Distributed Map (batches >
200 rows), a crawler on the hot path, CDK/IaC, auto-applied feedback, a
reviewer UI or HITL (F2), non-English text, generated damage photos (Claude
sees document images only), and the assignment's model-selection step (a
different lab — v1 ADR 0010 already owns model selection).

---

## S. Structured intake + Glue Data Quality (Part 1.1)

- **AC-S1** `[off]` IF a batch's Glue DQ ruleset score is below
  `dq.batch_min_score` (default 0.80), THEN the system SHALL quarantine the
  **whole batch**, process none of its claims, write
  `quality/quarantine/<batch_id>/summary.json`, and emit `BatchQuarantined`. A
  systemic upstream defect SHALL NOT fan out into per-claim human review.
- **AC-S2** `[off]` IF a row fails a **blocking** rule, THEN the system SHALL
  quarantine that row with its failed rule ids, SHALL NOT preprocess it, and
  SHALL continue with the rest of the batch. Blocking rules: `claim_id` missing,
  malformed or duplicated within the batch (every copy is quarantined);
  `policy_number` missing, or not canonical after normalization; `loss_date`
  missing or unparseable with the configured formats; `claim_amount` missing,
  non-numeric or negative; `line_of_business` or `jurisdiction` outside the
  allowed set.
- **AC-S3** `[off]` IF a row passes the blocking rules but trips a **warning**
  rule, THEN the claim SHALL proceed carrying `dq_warn:<rule>`, which routes it
  to human review (W3). Warning rules: report lag > `dq.report_lag_warn_days`
  (30); `loss_date` in the future; currency ≠ USD. A raw value that is not
  canonical but normalizes cleanly is **info**, not a warning
  (`normalized:<field>`). Format variety is the normalizer's job. A wrong
  normalization is caught per claim by reconciliation (V1) and per batch by
  the DQDL format-threshold rules (score + trend).
- **AC-S4** `[off]` The ruleset SHALL be DQDL in ONE file
  (`build/glue/claims_intake.dqdl`). Every DQDL rule SHALL have a row-level twin
  in `dataprep/intake_rules.py`, keyed by (rule type, column). A parity test
  SHALL fail when a rule has no twin or a twin has no rule. *(fitness:
  class-level drift guard between the batch gate and the row gate)*
- **AC-S5** `[gate]` WHEN a batch lands, the system SHALL register its
  partition `batch_id=<id>` on an **explicit** catalog table
  (`claim_processor_dq.claims_intake`: all-string columns, OpenCSVSerde,
  header skipped). It SHALL then evaluate the ruleset on that partition only
  (`pushDownPredicate`) with `NumberOfWorkers=2`, `Timeout=10`,
  `CloudWatchMetricsEnabled=true` and `ResultsS3Prefix=quality/dq-results/`.
- **AC-S6** `[off]` The DQ run SHALL be polled by the state machine (Wait 15 s →
  Get → Choice) within a poll budget (default 40). IF the run ends `FAILED`,
  `TIMEOUT` or `STOPPED`, or the budget is exhausted, THEN the batch SHALL be
  quarantined with reason `dq_run_failed`. It is never processed unvalidated
  *(fail closed)*.
- **AC-S7** `[off]` The batch outcome (score, per-rule result, quarantined rows
  with rule ids, row counts) SHALL be written to
  `quality/dq-results/<batch_id>/summary.json`.
- **AC-S8** `[off]` IF a batch has more than `dq.max_batch_rows` (200) rows or
  its key does not match `intake/batch_id=<id>/<name>.csv`, THEN it SHALL be
  quarantined (`batch_too_large` / `invalid_batch_key`). Inline-Map scale is
  bounded explicitly.

## T. Narrative validation + normalization (Parts 1.2, 4.2)

- **AC-T1** `[off]` IF a narrative is missing, empty, not UTF-8, or over
  `narrative.max_bytes` (100,000 — the Comprehend 100 KB cap), THEN the system
  SHALL record `narrative_invalid:<reason>` and still assemble the bundle from
  the other sources. The claim is never dropped.
- **AC-T2** `[off]` The system SHALL score each narrative with deterministic
  checks:
  - length ≥ `narrative.min_chars` (80);
  - describes a loss (loss lexicon);
  - contains a date reference;
  - is not placeholder text (`n/a`, `test`, `lorem`, …);
  - mentions the intake claimant surname or policy number;
  - is English-dominant (Comprehend `DetectDominantLanguage` = `en`, score ≥ 0.8 `[gate]`; heuristic in the fake).

  `quality_score = passed / total`. IF the score is < `narrative.min_quality`
  (0.7), THEN flag `narrative_quality_low`. Checks and score are recorded.
- **AC-T3** `[off]` Before any service call, the system SHALL normalize text:
  Unicode NFKC, smart quotes and dashes → ASCII, control characters stripped,
  whitespace collapsed. Normalization SHALL be **idempotent**
  (`n(n(x)) == n(x)`, property-tested over the synthetic corpus).
- **AC-T4** `[off]` One shared normalizer SHALL canonicalize structured tokens
  across every source:
  - dates → ISO-8601, using `normalization.date_formats` and a per-channel `normalization.date_order` (`MDY`/`DMY`) to resolve `dd/mm` vs `mm/dd`;
  - amounts → decimal (currency symbols and thousands separators stripped);
  - policy numbers → canonical `POL-<ST>-<AU|HO>-<5 digits>`;
  - VINs → 17 upper-case characters, rejecting I/O/Q;
  - domain abbreviations expanded from `normalization.lexicon`.
- **AC-T5** `[off]` Normalization and threshold configuration SHALL be read
  through the existing `ConfigProvider` from a **second AppConfig profile
  `data-quality`**, with a bundled default document. If the config is
  unreachable, the provider falls back to last-known-good, then to the bundled
  default *(AC-K1 parity)*.
- **AC-T6** `[off]` IF a high-risk PII entity (SSN, CREDIT_DEBIT_NUMBER / CVV /
  EXPIRY, BANK_ACCOUNT_NUMBER / ROUTING, PIN) is detected in a narrative
  (Comprehend `DetectPiiEntities` `[gate]`; regex in the fake), THEN the system
  SHALL replace it with `[<TYPE>]` before the text is analysed further, stored
  under `processed/`, or placed in any FM request. It records
  `pii_redacted:<TYPE>` (type only, never the value). Names, addresses and dates
  are kept because extraction needs them. *(data minimization; ties AC-H1)*

## U. Multimodal extraction (Parts 2.1–2.4, 4.1)

- **AC-U1** `[off]` IF text exceeds a Comprehend per-call limit (P-h), THEN the
  system SHALL split it at sentence boundaries into chunks within the limit.
  Sentiment goes through `BatchDetectSentiment` (≤ 25 chunks per call) and is
  aggregated as byte-weighted mean scores with the label = argmax. It SHALL
  NEVER send an over-limit request or truncate silently.
- **AC-U2** `[off]` WHEN a narrative passes T1, the system SHALL extract:
  - entities (type, text, score ≥ `comprehend.min_entity_score` 0.80);
  - the top `comprehend.top_key_phrases` (15) key phrases;
  - sentiment.

  It writes `processed/claims/<claim_id>/narrative.json` (normalized, redacted
  text + checks + insights).
- **AC-U3** `[off]` Sentiment (narrative and call) SHALL be **context only**. It
  SHALL NOT feed routing, auto-approve, or any priority or fraud score: sentiment
  models carry dialect bias, and an upset claimant is not a riskier claim. A test
  asserts that no routing or reconciliation function reads sentiment.
  *(bias guard)*
- **AC-U4** `[off]` IF a document image is not PNG/JPEG/PDF/TIFF by magic bytes,
  exceeds `images.max_image_bytes` (3,750,000 — the Converse limit, H1), or
  Textract errors, THEN the system SHALL record
  `document_failed:<doc_type>:<reason>` and continue (→ human review).
- **AC-U5** `[off]` WHEN a police report or repair estimate is present, the
  system SHALL call Textract `AnalyzeDocument` with `FeatureTypes=["QUERIES"]`
  and the doc-type query set:
  - police report: report number, incident date, incident location;
  - repair estimate: total amount, VIN, estimate date.

  It keeps LINE text in reading order and each answer with its confidence. An
  answer below `textract.min_confidence` (80) is kept, marked `low_confidence`,
  and SHALL NOT be used as a reconciliation source.
- **AC-U6** `[off]` Textract output SHALL be written to
  `processed/claims/<claim_id>/documents.json` (per document: type, key,
  lines[], answers{alias: {text, confidence, low_confidence}}).
- **AC-U7** `[off]` IF a transcription job fails or its poll budget (40 × 15 s)
  is exhausted, THEN the claim SHALL continue with `call_failed:<reason>`. No
  Lambda SHALL sleep waiting for a job.
- **AC-U8** `[off]` WHEN a call recording is present, the system SHALL start ONE
  Transcribe job per claim revision:
  - name `clm-<claim_id>-r<revision>`. A `ConflictException` resolves to polling the existing job (idempotent);
  - `ShowSpeakerLabels`, `MaxSpeakerLabels=2`;
  - `ContentRedaction{RedactionType: PII, RedactionOutput: redacted, PiiEntityTypes: [SSN, CREDIT_DEBIT_NUMBER, CREDIT_DEBIT_CVV, CREDIT_DEBIT_EXPIRY, BANK_ACCOUNT_NUMBER, BANK_ROUTING, PIN]}`;
  - output `transcripts/<claim_id>/` in the same bucket.
- **AC-U9** `[off]` WHEN the job completes, the system SHALL read ONLY
  `Transcript.RedactedTranscriptFileUri` and build ordered speaker turns
  (`agent | caller`; the first speaker is `agent`). It uses
  `results.audio_segments` when present and falls back to
  `results.items[].speaker_label`; the real output shape is confirmed at the
  `[gate]`. It adds per-speaker sentiment (context only, U3) and writes
  `processed/claims/<claim_id>/call.json`.
- **AC-U10** `[off]` IF a policy has no loss-run rows in the lookback window,
  THEN the history summary SHALL say so explicitly ("No prior claims on record
  for policy POL-… in the last 36 months"). It never omits the section or
  invents content.
- **AC-U11** `[off]` WHEN loss-run rows exist, the system SHALL produce a
  **deterministic** natural-language summary (no FM) over
  `history.lookback_months` (36): count, perils, total paid, open claims, most
  recent loss. It flags `history_frequency_high` when the count within
  `history.frequency_window_months` (12) is ≥ `history.frequency_threshold` (3).
  The same input gives a byte-identical summary.
- **AC-U12** `[off]` WHEN a batch's claims settle, the system SHALL aggregate
  key phrases and entity types across the batch into ranked themes (normalized
  phrase → count, claim ids) at `quality/themes/<batch_id>.json`, and emit the
  top-N counts.

## V. Bundle: reconcile, score, format for Claude (Parts 3.1–3.3, 4.1)

- **AC-V1** `[off]` IF two or more sources disagree on a reconcilable field,
  THEN the bundle SHALL carry `recon_mismatch:<field>` with every source's
  value (→ human review). Fields and sources:
  - `loss_date`: intake, narrative, police report;
  - `claim_amount`: intake vs repair-estimate total, tolerance `recon.amount_tolerance_pct` (2 %);
  - `policy_number`: intake vs narrative;
  - `vin`: narrative vs estimate.

  Low-confidence OCR answers (U5) and sentiment (U3) are never sources.
- **AC-V2** `[off]` The bundle SHALL carry a `quality` block:
  - per-source status (`intake|narrative|documents|call|history` = `ok|missing|failed`);
  - `flags` (blocking) and `info` (non-blocking), kept separate;
  - `bundle_quality_score` ∈ [0, 1] (narrative score, source completeness, reconciliation agreement).

  The score is **informational**: routing uses flags only.
- **AC-V3** `[off]` The bundle SHALL carry `fm_request.context_blocks`, which is
  Converse user-role content made of:
  - labelled text sections in a fixed order (INTAKE RECORD · CLAIMANT NARRATIVE · DOCUMENT TEXT · CALL TRANSCRIPT · LOSS HISTORY · RECONCILIATION NOTES);
  - then image blocks by **S3 reference** (`{"image": {"format", "s3_key"}}`).

  Image bytes are never stored in the bundle. The intake plane owns **data
  formatting**; v1 owns the **task prompt** (W2).
- **AC-V4** `[off]` Image content SHALL respect the Converse limits: ≤
  `images.max_images` (20) per request, each ≤ 3,750,000 bytes, user role only.
  An over-limit image is left out with `image_skipped:<reason>` (blocking).
- **AC-V5** `[off]` The call transcript SHALL be rendered through a
  **conversation template** as turn-ordered, redacted dialog
  (`Agent: … / Caller: …`). The prompt registry SHALL add a multi-turn
  `adjuster_dialog` template that renders a Converse `messages` list: the bundle
  context as turn 1, then alternating user/assistant turns for follow-up
  questions. It is exercised by `python -m claim_processor ask` (fake offline,
  `[gate]` live). Template versions are recorded.
- **AC-V6** `[off]` The bundle (`schema_version "2.0"`) SHALL be written to
  `bundles/<claim_id>` only after every source branch has settled. Each
  revision overwrites it completely *(C9)*.

## W. v1 consumes the bundle (integration + integrity)

- **AC-W1** `[off]` IF a v1 key is under `bundles/` and the object is missing,
  unparseable or not `schema_version 2.x`, THEN the extract step SHALL raise a
  typed `BundleError`. The execution fails visibly; this is a producer defect,
  not a data defect.
- **AC-W2** `[off]` WHEN a v1 key is under `bundles/`:
  - extraction SHALL send `[extract_info_bundle prompt] + context_blocks`, with image S3 keys resolved to bytes at invoke time and V4 re-checked;
  - it keeps the frozen five-field schema (AC-B3) and all resilience behavior (adapter, flags, ensemble, ladder — K–P);
  - `document_text` (rule-based floor + RAG scope) = the concatenated text sections;
  - the summary step SHALL use `generate_summary_bundle`, which adds the loss-history summary and reconciliation notes to v1's inputs and never sentiment (U3).
- **AC-W3** `[off]` Every blocking bundle flag SHALL be merged into
  `validation.flags` as `bundle:<flag>`, and `route_claim` SHALL send any
  `bundle:` flag to human review. Informational items (sentiment, themes,
  `pii_redacted:*`, `bundle_quality_score`, low-confidence OCR) SHALL NOT affect
  routing. *(integrity: extends AC-R3 — no v2 path widens auto-approve)*
- **AC-W4** `[off]` A key NOT under `bundles/` SHALL take the v1 path unchanged.
  The legacy `claims/*` samples and all 268 existing tests keep passing, v1
  templates are unchanged, and the new templates are additive.
- **AC-W5** `[off]` The result SHALL carry
  `bundle: {key, schema_version, revision, quality_score, sources, flags}`. The
  field is optional and defaulted, so pre-v2 results still serialize
  *(AC-R4 parity)*.
- **AC-W6** `[sfn]` The v1 definition SHALL change only in the
  `UngroundedFallback` Pass: it passes `bundle` and `bundle_flags` through.
  Every extract path emits both keys (null / `[]` for non-bundle keys), so the
  JSONPath never misses.
- **AC-W7** `[off]` The v1 Lambda role SHALL gain `s3:GetObject` on `bundles/*`
  and `raw/claims/*` only (W2's image resolution), and nothing else.

## X. Quality feedback loop (Part 4.3; C4-a)

- **AC-X1** `[off]` The loop SHALL NEVER apply a change. It SHALL only write
  proposals to `quality/proposals/<ts>.json`, drawn from a **bounded** set:
  `set_date_order{channel, order}`, `add_date_format{format}` (from a fixed
  candidate list), `adjust_threshold{key, value}`. A free-form or destructive
  change cannot be represented. A human applies a proposal by deploying a new
  `data-quality` AppConfig version through the existing linear-bake strategy,
  which is rollback-able. *(ADR 0015 discipline)*
- **AC-X2** `[off]` WHEN a v1 record for a bundle lands (`pending-review/bundles/*`
  or `results/bundles/*` → EventBridge), the system SHALL compare the
  FM-extracted fields with the bundle's source values. It writes
  `quality/feedback/<claim_id>-r<rev>.json` (per field: agree/disagree, which
  source, raw + normalized source values; names are stored as a boolean match
  only) and emits `FieldDisagreement` by field and channel. Human-review claims
  are included, because they are where the signal is.
- **AC-X3** `[off]` WHEN a record carries a reviewer decision with
  `field_changes`, those values SHALL be the highest-precedence signal (ground
  truth for the field). Live only after F2 (P-m).
- **AC-X4** `[off]` WHEN the proposal job runs (`python -m claim_processor dq
  propose`, local or S3), it SHALL emit a proposal only when a pattern has ≥
  `feedback.min_support` (3) supporting claims AND replay shows it fixes ≥
  `feedback.min_fix_rate` (80 %) of them. Each proposal carries its evidence
  (claim ids, counts, before/after). The inputs are feedback records plus
  quarantine records (a DMY date that was unparseable is evidence too).
- **AC-X5** `[off]` Replay SHALL re-run the normalizer and row rules under the
  proposed config over the stored records: deterministic, offline, no FM calls.
- **AC-X6** `[off]` Reprocessing after an accepted change SHALL go through a
  **resubmission batch** (same claim ids, `revision + 1`) on the normal intake
  path. The v1 execution name `claim-<claim_id>-r<revision>` keeps a separate
  audit trail for each revision.

## Y. Observability (Part 1.3)

- **AC-Y1** `[off]` The system SHALL emit EMF metrics in namespace
  `ClaimProcessor/DataQuality`, through the redacting emitter *(AC-Q2 parity)*:
  - `DQRulesetScore`, `RowsQuarantined`, `BatchQuarantined`;
  - `NarrativeQualityScore`, `BundleQualityScore`;
  - `SourceFailed` (Source), `ReconMismatch` (Field), `PiiRedacted` (Type), `FieldDisagreement` (Field, Channel);
  - `ProposalsWritten`.

  Each metric has ≤ 2 dimension keys, and `claim_id` is **never** a dimension
  (cardinality).
- **AC-Y2** `[off]` `build/dashboards/data-quality.json` SHALL chart every Y1
  metric (1-hour and 1-day periods) plus the Glue-published DQ metrics. A test
  asserts that it parses and references only vocabulary metrics. `[infra]`
  `put-dashboard`.
- **AC-Y3** `[infra]` Alarms `DQRulesetScoreLow` (< `dq.batch_min_score`) and
  `ReconMismatchHigh` → the SNS topic from v1 Stages 6–7. They notify only and
  trigger **no** automated config change (C4-a).

## Z. Orchestration, idempotency, IAM, privacy, offline-first, cost

- **AC-Z1** `[sfn]` Intake SHALL run on a new Standard state machine,
  `claim-processor-intake`, with one execution per batch. EventBridge triggers
  it on `Object Created` for keys matching `intake/*.csv`. Per claim, a `Map`
  (MaxConcurrency 4) runs a `Parallel` of the source branches, then
  AssembleBundle, then StartClaim (the v1 execution). The run ends with
  BatchSummary.
- **AC-Z2** `[off]` IF the same batch object triggers more than once
  (EventBridge is at-least-once), THEN only the first execution SHALL process
  it. The first state takes the lock `quality/locks/<batch_id>` with
  `IfNoneMatch="*"`. A 412 ends the duplicate as `duplicate_batch` with no side
  effects.
- **AC-Z3** `[off]` The v1 execution SHALL be started with name
  `claim-<claim_id>-r<revision>` (≤ 80 chars). `ExecutionAlreadyExists` is
  recorded as `already_started`, so no revision gets a second decision workflow
  *(C9)*.
- **AC-Z4** `[off]` Each source branch SHALL catch its own failure and turn it
  into a `failed` source status, so one bad source never fails the claim. A
  claim-level failure (bundle write or start) is retried twice with backoff,
  then recorded as `claim_failed` in the batch summary. The batch never fails
  as a whole because of one claim.
- **AC-Z5** `[off]` State payloads SHALL carry S3 references, not content
  (claim-check): every intake step returns ≤ 32 KB. Transcripts, OCR lines and
  insights live under `processed/`.
- **AC-Z6** `[off]` IAM policy-lint *(extends AC-I1/I2)* covers the new roles
  `claim-processor-intake-lambda`, `-intake-sfn`, `-glue-dq` and
  `-intake-events`:
  - `Resource:"*"` is allowed ONLY on the P-k no-resource-type actions, plus `cloudwatch:PutMetricData` with a `cloudwatch:namespace` condition. Any other `*` fails the lint;
  - `transcribe:GetTranscriptionJob` is scoped to `transcription-job/clm-*`;
  - Glue DQ actions to `dataQualityRuleset/claims-intake*`;
  - catalog actions to the one database and table;
  - `iam:PassRole` only for the Glue DQ role, with `iam:PassedToService=glue.amazonaws.com`;
  - `states:StartExecution` only on the v1 state machine;
  - S3 by prefix, never bucket-wide.
- **AC-Z7** `[off]` No raw PII SHALL appear in logs or metrics *(AC-H1/Q2
  parity)*. Service payloads (entities, OCR lines, transcripts) are never
  logged; only counts and types are.
- **AC-Z8** `[off]` Offline-first: `python -m claim_processor intake --fake
  --batch <csv>` SHALL run the whole flow locally, with deterministic fakes for
  Glue DQ, Comprehend, Textract and Transcribe, and v1's fake pipeline on each
  bundle. It needs **no new pip dependency**; the no-new-deps test scans
  subpackages. Real AWS stays behind `CLAIM_PROCESSOR_REAL_AWS=1`.
- **AC-Z9** `[off]` `tools/gen_synthetic.py --seed 23` SHALL deterministically
  generate the corpus, with seeded defects labelled in
  `samples/v2/manifest.json`. The offline suite SHALL assert:
  - 100 % of seeded blocking defects are quarantined;
  - 100 % of seeded warn / narrative / recon / source defects are flagged;
  - 0 **blocking** flags on the seeded-clean claims;
  - ≥ 3 clean claims end `auto_approve`;
  - batch B0001 passes the batch gate with a score the manifest pins (the fake Glue DQ evaluates the DQDL twins);
  - the seeded DMY-date pattern yields exactly one `set_date_order{partner, DMY}` proposal whose replay fixes all its supporting claims.
- **AC-Z10** `[gate]` The smoke SHALL stay inside the existing $10 budget:
  ≤ 16 rows (≤ 11 processed claims), ≤ 3 recordings ≤ 60 s each, ≤ 8 document
  images, ≤ 2 batches (initial + resubmission). The runbook estimates the cost
  before any upload.

## H1. Hygiene — do regardless

- **AC-H1v2** `[off]` `understand.MAX_IMAGE_BYTES` SHALL be 3,750,000 (the
  Converse per-image limit, P-c), shared by the ingest cap (AC-D3) and V4. A
  4 MB image now fails fast at ingest instead of at Bedrock. Tighter is safer.

---

## 3. Contracts (Wave 0)

**S3 zones** (bucket `claim-documents-poc-rk-20260922`):

| Prefix | Writer | Content |
|---|---|---|
| `intake/batch_id=<id>/claims.csv` | upstream / operator | structured intake (partitioned; Glue table location `intake/`) — **uploaded last** (commit marker) |
| `raw/claims/<claim_id>/` | upstream | `narrative.txt`, `police_report.png`, `repair_estimate.png`, `fnol_call.wav` |
| `history/loss_runs.csv` | upstream | policy loss runs (reference data) |
| `transcripts/<claim_id>/` | Transcribe | redacted transcript JSON |
| `processed/claims/<claim_id>/` | intake | `narrative.json`, `documents.json`, `call.json`, `history.json` |
| `bundles/<claim_id>` | intake | bundle v2.0 = v1 input key |
| `quality/{locks,dq-results,quarantine,themes,feedback,proposals}/` | intake / operator | DQ plane |
| `results/bundles/<claim_id>.json`, `pending-review/bundles/<claim_id>.json` | v1 (unchanged code path) | decisions |

**Intake CSV** (header required; every value a string in the raw zone):
`claim_id,revision,policy_number,claimant_name,line_of_business,jurisdiction,loss_date,report_date,claim_amount,currency,channel,narrative_key,document_keys,call_key`.
`document_keys` is `;`-separated. `channel` ∈ {agent, web, phone, partner}.
`line_of_business` ∈ {auto, homeowners}; `jurisdiction` ∈ {FL, TX} (the
states that have policy documents for RAG).

**Loss runs:** `policy_number,prior_claim_id,loss_date,peril,paid_amount,status`.

**Bundle v2.0** (top-level keys): `schema_version, claim_id, revision,
batch_id, intake{raw, normalized, dq{warnings[]}}, narrative{status, key,
text, quality{score, checks}, insights{entities, key_phrases, sentiment},
pii_redacted[]}, documents[{key, doc_type, status, lines_key, answers}],
call{status, key, job_name, turns_key, sentiment}, history{status, summary,
stats}, reconciliation{fields{<f>: {values{src: v}, agree}}, reconciled{}},
quality{sources{}, flags[], info[], bundle_quality_score},
fm_request{context_blocks[], context_text, format_version},
provenance{created_at, intake_execution_arn, data_quality_config_version}`.
Large arrays (OCR lines, turns) go by `*_key` reference (Z5). `context_text`
carries what the FM needs.

**Flag vocabulary** (`dataprep/contracts.py`). **Blocking**: `dq_warn:*`,
`narrative_invalid:*`, `narrative_quality_low`, `language_unsupported`,
`document_failed:*`, `call_failed:*`, `recon_mismatch:*`,
`history_frequency_high` (S5 — confirm at gate), `image_skipped:*`.
**Info**: `pii_redacted:*`, `low_confidence_ocr:*`, `normalized:*`. Any flag
not in the vocabulary is a test failure.

**Dispatcher event:** `{"step": "<name>", ...}` → one Lambda,
`claim-processor-intake-step` (handler
`claim_processor.lambda_entry.intake_step`). Steps: `acquire_lock`,
`register_partition`, `start_dq_run`, `get_dq_run`, `evaluate_batch`,
`split_rows`, `narrative`, `documents`, `start_transcription`,
`get_transcription`, `process_transcript`, `history`, `assemble_bundle`,
`start_claim`, `batch_summary`, `feedback` (the EventBridge input transformer
adds `step`).

**`data-quality` AppConfig document:** `build/appconfig/data-quality.json`
(keys `dq`, `narrative`, `normalization{date_formats, date_order{default,
<channel>}, lexicon}`, `comprehend`, `textract`, `recon`, `history`,
`feedback`, `images`; defaults as quoted in the ACs).

**Synthetic corpus** (`samples/v2/`; `s3/` mirrors the bucket, and `truth/`
holds the fakes' sidecars and gold values, never uploaded). Batch `B0001`,
16 rows:

| claim | scenario | expected |
|---|---|---|
| 101 | FL auto, clean, all 4 sources | auto_approve |
| 102 | TX home, clean, narrative + estimate | auto_approve |
| 103 | FL auto, clean, narrative only | auto_approve |
| 104 | TX home, $18,400 > threshold | human_review (v1 threshold) |
| 105, 106 | partner channel, DMY date with day ≤ 12 (silent misparse); the narrative and police report state the date unambiguously ("11 March 2026") | `recon_mismatch:loss_date` → human_review; feedback evidence |
| 107 | intake $2,400 vs estimate $9,850 | `recon_mismatch:claim_amount` |
| 108 | narrative "car damaged. n/a" | `narrative_quality_low` |
| 109 | SSN inside narrative, otherwise clean | `pii_redacted:SSN` (info) → auto_approve |
| 110 | policy_number missing | row quarantined |
| 111 ×2 | duplicate claim_id | both rows quarantined |
| 112 | claim_amount `N/A` | row quarantined |
| 113 | partner DMY with day > 12 → unparseable under default config | row quarantined; proposal evidence |
| 114 | 3 prior claims in 12 months | `history_frequency_high` |
| 115 | corrupt WAV (header only) | `call_failed:*` |

Resubmission batch `B0002` (`samples/v2/resubmission/`): 105, 106 and 113 at
`revision 2`, run after the proposal is applied. Expected: 105 and 106 lose
their mismatch; 113 processes.

---

## 4. Plan

```
S3 intake/batch_id=B/claims.csv ─EventBridge─▶ SFN claim-processor-intake (Standard, 1 exec/batch)
 AcquireLock(IfNoneMatch) → RegisterPartition → StartDQRun → [Wait15 → GetDQRun → Choice]≤40 → EvaluateBatch
   ├─ score<min | run failed | too large → QuarantineBatch → End
   └─ SplitRows(row gate, quarantine rows) → Map(claims, MaxConcurrency 4):
        Parallel[ Narrative(validate·normalize·PII·Comprehend) | Documents(Textract QUERIES)
                | Call(StartTranscribe → [Wait15 → GetTranscribe → Choice]≤40 → ProcessTranscript) | History ]
        (each branch Catch → failed status)
        → AssembleBundle(reconcile·score·format·write bundles/<id>) → StartClaim(v1, claim-<id>-r<rev>)
   → BatchSummary(themes·metrics·summary.json) → End
v1 claim-processor (definition unchanged but for W6): UnderstandExtract reads bundles/<id> → … → Record
pending-review|results/bundles/* ─EventBridge─▶ intake-step(feedback) → quality/feedback/* + FieldDisagreement
operator: dq propose → quality/proposals/* → human → AppConfig data-quality vN (linear-bake) → resubmission batch
```

**Module layout** — new subpackage `build/claim_processor/dataprep/`
(bounded context: *data preparation*; v1 modules = *claim decisioning*):
`contracts.py` (bundle / flags / source status), `intake_rules.py` (row
twins + DQDL parser), `normalize.py`, `narrative.py`, `comprehend_step.py`,
`textract_step.py`, `transcribe_step.py`, `history.py`, `reconcile.py`,
`bundle.py` (assemble / score / `fm_request` / dialog render), `glue_dq.py`,
`themes.py`, `feedback.py` (compare / propose / replay), `dq_config.py`,
`steps.py` (dispatcher), `fakes.py`.

**Touched v1 files:** `understand.py` (H1), `models.py` (`bundle` field),
`pipeline.py` (bundle branch in `understand_extract`, summary template,
bundle-flag merge in `process` / `result_from_event`), `routing.py`
(`bundle:` rule), `prompts.py` (+3 templates, additive), `handler.py`
(pass-through), `lambda_entry.py` (`intake_step` + builder), `__main__.py`
(`intake`, `dq propose`, `ask`), `sfn/asl.json` (W6 only),
`iam/step-lambda.json` (W7), `tests/test_no_new_deps.py` (rglob + stdlib
allowlist: `csv`, `unicodedata`, `math`, `statistics`, `string`), and
`tests/test_iam_policy.py` (new files + `*` allowlist).

**New deploy assets:** `sfn/intake-asl.json`, `glue/claims_intake.dqdl`,
`glue/claims_intake_table.json`, `appconfig/data-quality.json`,
`dashboards/data-quality.json`, `iam/{intake-lambda,intake-sfn-exec,glue-dq,intake-events}.json`,
`events/{intake-rule,feedback-rule}.json`, `tools/gen_synthetic.py`,
`samples/v2/**`, `DEPLOY-V2.md` (stages 10–15).

**G1 (new abstractions, and what each buys):**

| Abstraction | What it buys | Simpler option rejected |
|---|---|---|
| The **bundle** contract | One reviewable, replayable artifact per claim revision: FM input + provenance + flags | Flattening everything into a text packet under `claims/`, which loses images, structure and flags (S3) |
| The **dispatcher Lambda** | One function to deploy, not 16; the role is shared anyway | Per-step functions, v1's style (S4) |
| The **`data-quality` profile** | Reuses `ConfigProvider` plus the linear-bake rollback | A JSON file in S3 with no rollout safety |

## 5. Tasks (waves; `[P]` = parallel within the wave)

| Task | Wave | Deliverable (file-level) | ACs | Verify |
|---|---|---|---|---|
| DP-00 | H | `understand.py` cap 3.75 MB + test | H1v2 | unit |
| DP-01 | 0 | `dataprep/contracts.py` (bundle v2.0, flag vocabulary, statuses) | V2, V6, W3, W5 | unit |
| DP-02 | 0 | `glue/claims_intake.dqdl` + `dataprep/intake_rules.py` + parity test | S2–S4 | unit + parity |
| DP-03 | 0 | `tools/gen_synthetic.py` + committed `samples/v2/**` + manifest | Z9 (data) | determinism test |
| DP-04 | 0 | `test_no_new_deps.py` rglob + allowlist | Z8 | unit |
| DP-05 | 1 [P] | `normalize.py` (NFKC, dates / amounts / policy / VIN, lexicon) | T3, T4 | unit + idempotence property |
| DP-06 | 1 [P] | `narrative.py` (checks, score, PII redaction) | T1, T2, T6 | Stubber |
| DP-07 | 1 [P] | `dq_config.py` + `appconfig/data-quality.json` | T5 | unit (fallback chain) |
| DP-08 | 1 [P] | `glue_dq.py` (register partition, start / get run, evaluate, quarantine, summary) | S1, S5–S8 | Stubber |
| DP-09 | 2 [P] | `comprehend_step.py` (chunking, batch sentiment, aggregation) | U1–U3 | Stubber + bias-guard test |
| DP-10 | 2 [P] | `textract_step.py` (QUERIES, parse, confidence) | U4–U6 | Stubber |
| DP-11 | 2 [P] | `transcribe_step.py` (idempotent start, poll, redacted turns) | U7–U9 | Stubber |
| DP-12 | 2 [P] | `history.py` (deterministic loss-run summary) | U10, U11 | unit (golden text) |
| DP-13 | 3 | `reconcile.py` | V1 | unit |
| DP-14 | 3 | `bundle.py` (assemble, score, `fm_request`, dialog template) + `prompts.py` templates | V2–V6 | unit |
| DP-15 | 3 | v1 integration (`pipeline` / `handler` / `routing` / `models`, W6 in `asl.json`) | W1–W6 | unit + ASL test + all 268 legacy tests |
| DP-16 | 3 [P] | IAM docs (4 new + step-lambda delta) + lint extension | W7, Z6 | policy-lint |
| DP-17 | 4 | `steps.py` dispatcher + `lambda_entry.intake_step` + `fakes.py` | Z4, Z5, Z7 | unit (payload ≤ 32 KB) |
| DP-18 | 4 | `sfn/intake-asl.json` + structural tests (lock, poll caps, branch Catch, Map, names) | Z1–Z3, S6, U7 | ASL test |
| DP-19 | 4 [P] | `themes.py` + batch summary | U12 | unit |
| DP-20 | 4 [P] | `feedback.py` + CLI `dq propose` | X1–X6 | unit + replay |
| DP-21 | 4 [P] | metric vocabulary + `dashboards/data-quality.json` + alarms spec | Y1–Y3 | unit |
| DP-22 | 4 | CLI `intake --fake` end-to-end + the Z9 seeded-defect assertions + `ask` | Z8, Z9, V5 | e2e offline |
| DP-23 | 5 | `DEPLOY-V2.md` + ledger sections + solution-design §9 addendum | infra | review |
| DP-24 | 5 `[gate]` | Interactive deploy + smoke: B0001 → bundles → v1 runs → feedback → proposal → human applies → B0002 | S5, U*, Z10 | live evidence in ledger |
| DP-25 | 5 | Teardown additions (Glue db / table / ruleset, 2nd state machine, rules, roles) | infra | checklist |

Dependencies: Wave 0 → Waves 1 ∥ 2 → Wave 3 → Wave 4 → Wave 5. DP-16 can run
alongside Wave 3. DP-03's corpus feeds the fakes (DP-17) and the e2e test
(DP-22). Engineering critical path: DP-01 → DP-05 → DP-13 → DP-14 → DP-15 →
DP-17 → DP-22. The calendar cost sits in Wave 5 (interactive deploy).

## 6. Analyze (Stage 4 cross-check)

- **Coverage:** every AC S1–S8, T1–T6, U1–U12, V1–V6, W1–W7, X1–X6, Y1–Y3,
  Z1–Z10 and H1v2 maps to ≥ 1 task (§5). No task lacks an AC.
- **Frozen invariants preserved:**
  - A1 (no legacy completions contract): the bundle path uses the same adapter.
  - A3/C2 (no nested app retries): new service calls use SDK retries; the state machine owns Retry.
  - A5 (`guardrailConfig` passthrough): unchanged.
  - B3 (five-field schema): kept (W2).
  - E1/F3 (single approval predicate): W3 adds human-review routes only.
  - F2 (idempotent result): bundle overwrite + execution names (Z3).
  - G1 (one v1 execution per claim): Z3.
  - H1 (no PII in logs): T6, Z7.
  - I1/I2 (IAM lint): extended by Z6.
  - J1/J2, R1 (offline, no new deps): Z8.
  - R3: W3.
- **Grounding:** every existing file named in §4 was read this session. Every
  AWS API and limit is cited in P-c…P-k. The only open items are `[gate]`
  probes: Transcribe output shape (U9), Glue-published metric names (Y2), and
  the minimal Glue DQ role set (DQ role policy verified by the first run, as in
  the v1 ledger).
- **Baseline (2026-09-23):** `python3 -m unittest discover -s tests` → 268 OK
  (1 skipped). `python3 tooling/skill-sync/skill_sync.py check` → exit 0.
- **Risks:**
  - R1: Glue DQ Spark start adds ~1–2 min per batch. Acceptable for batch intake.
  - R2: Transcribe PII redaction here is `en-US` only.
  - R3: Synthetic realism (TTS audio, rendered PDFs) proves the plumbing, not model accuracy.
  - R4: Enabling EventBridge on the bucket emits events for every prefix; the rules filter them, at negligible cost.
  - R5: Inline-Map history is capped at 25,000 events, hence the 200-row cap (S8).
  - R6: F2 is open, so live human-review claims park at `AwaitReview` (P-m).

## 7. Clarify pass — recommended defaults (confirm or override by id)

- **S1** Tabular source for "survey → summary": **policy loss runs** (feeds
  the adjuster and fraud context) *(recommended)*. Alternative: a post-claim
  satisfaction survey, which never influences a claim decision.
- **S2** Glue catalog: an **explicit all-string table + partition registration
  per batch** *(recommended)*. A crawler infers types from exactly the dirty
  data the gate exists to catch, and adds 1–2 min per batch. Alternative: a
  crawler per batch (the assignment's shape).
- **S3** v1 contract: v1 consumes **`bundles/<claim_id>`**, with Lambda code, W6
  and W7 as the only v1 changes *(recommended)*. Alternative: a flat text
  packet under `claims/`, which needs no v1 code but loses images, structure
  and flags.
- **S4** **One dispatcher Lambda** for the intake steps *(recommended)*.
  Alternative: one function per step (v1's style; about 16 functions to create
  by hand).
- **S5** `history_frequency_high` **forces human review** (like a referral to
  a special investigations unit) *(recommended)*. Alternative: informational
  only.

## 8. Human gate

Approve = accept S1–S5 as recommended and start **DP-00 → Wave 0**. Or change
any item by id. Until approval, no code, no data and no AWS calls. Waves 0–4
are offline. Wave 5 continues the interactive, one-step-per-turn deploy.
