# Spec — claim processor v2: data-preparation plane (validate · multimodal · format for Claude · quality feedback)

> **REVISED FROM THE LLD (owner sequence).** The LLD
> (`../design/lld-v2-data-prep.md`) is **FINAL**, signed off 2026-09-24. This
> revision replaces the 2026-09-23 on-hold draft's acceptance criteria, plan
> and tasks; the draft's §0 decisions, §1 brainstorm record and §2 scope are
> kept as the historical record. **The LLD is the source of truth**: this spec
> restates *what must hold* and cites the LLD rule ids; it does not redesign.

**Stage:** sdd-spec (Stages 2–4) — **complete**. **Status:** **APPROVED
2026-09-24** (`SPEC-OK`; the tasks file got `TASKS-OK` the same day) → next
stage is **sdd-implement** (§8). **Layout LY-b (owner, 2026-09-24):** this file carries the
EARS criteria → `SPEC-OK`; `../plans/claim-processor-data-prep.tasks.md`
carries the plan (waves, worktrees, merge protocol) and the task list →
`TASKS-OK`. **EARS granularity EA-a:** criteria by reference — each criterion
names the LLD rule ids it covers ("Covers:"), and the LLD stays the detailed
source. **Waves WV-a**, parallel build in git worktrees (**PW-a**), manual
deploy with a full walkthrough (**DW-a**).
**Clarify decisions (owner, 2026-09-24):** CL1-a (G rows live in the tasks
file + TST-03's coverage test), CL2-a (retired draft ACs kept, marked
superseded — §3), CL3-a (`[owner]` tasks block only their dependents), CL4-a
(a repo pre-commit script, owner-installed, is the CI hook and the worktree
merge gate), CL5-a (the v1 specs stay frozen; every v2 change to a v1 file is
specified in family W only).

**New increment (v2).** The prior specs stay **FROZEN** and additive-only:
`./claim-processor-real-aws.spec.md` (A–J),
`./claim-processor-model-resilience.spec.md` (K–R). This file owns **S–Z**
and **H1v2**.
**Binding:** `.sdd` `[roots] claim-document-processor = insurance-claim-processor/`.
**Design:** `../design/lld-v2-data-prep.md` (FINAL 2026-09-24) ←
`../design/hld-v2-data-prep.md` (FINAL 2026-09-23), ADRs
[0016](../adrs/0016-data-preparation-plane-intake-state-machine.md)–[0022](../adrs/0022-human-approved-replay-proven-quality-proposals.md)
with their ratified amendments, `../adrs/approval-criteria.md`,
`../validate/architecture-validation.md` (G1–G49).
**Constitution:** `.cursor/rules/architecture-principles.mdc` (principles, no
numbered invariants) + the frozen kata invariants A–R above (checked in the
Stage-4 analyze; CL5-a).
**Test gate:** offline `unittest` in `../build/`
(`cd build && python3 -m unittest discover -s tests -t .`; baseline 288 OK,
1 skipped, 2026-09-24). Real AWS is Wave 5, owner-run, one step per turn; the
agent never runs a mutating AWS command.

**Verification tags** (the LLD's, unchanged): `[off]` offline unit, Stubber
or grep; `[sfn]` state-machine definition test; `[gate]` real-AWS smoke,
owner-run; `[infra]` runbook or config review. `[re-verify]` facts stay
`[gate]` criteria — they are not resolved in this spec.

---

## 0. Decisions in force

**From the 2026-09-23 draft (confirmed, unchanged):** C1-a…C7-a — the
claims domain mapping, the separate intake state machine and bundle, the
service set (Glue DQ + Comprehend + Textract + Transcribe; no SageMaker, no
Rekognition), the human-approved proposal loop, offline-first then gated
real AWS, v1 open items on a separate track. C7-a's one-file layout is
superseded by **LY-b** (owner, 2026-09-24): two files, two approvals.

**From the HLD and LLD (decided — do not reopen):**
- HLD: A1-a…A5-a, R1–R9, SD-1…SD-6, D0 closed, H-F14-a, R7q-a, R8c-a, D-a,
  and the stage order (HLD → LLD → spec → build → owner's manual deploy).
- LLD framing: S-a · L-a · R-a · F-a · W-a (2026-09-23).
- Checkpoint 1: Q1-a **tightened** (ADR 0021 amendment), Q2-a…Q7-a, **Q8-b**
  (ADR 0022 amendment), Q9-a, **Q10-a** (ADR 0019 amendment).
- Checkpoint 2 (2026-09-24): **IAM ok** (ADR 0020 amendment, the corrected
  §6.13 diff), B6-6-a (the `operator` role for `ask`), B4-5-a, B3.1-a,
  B4-1-a (PNG and JPEG only), B4-2-a, B4-3-a, B5-1-a, C10-1-a (owner-rendered
  WAVs), C10-2-a (batch B0003); defaults B4-4, B5-2–B5-5, B6-1 = b (no intake
  machine logging), B6-2–B6-4, B7-2, B7-4 (`ProposalsWritten` dropped), S9-1;
  B.5: B4-6–B4-10, B7-5.
- **LLD signed off** 2026-09-24. Any gap or contradiction found during the
  build is raised as an LLD erratum with the owner's OK — never diverged from
  silently.

## 1. Brainstorm record (Stage 1, compressed — historical)

> Kept verbatim from the 2026-09-23 draft as the Stage-1 record. Where a
> premise or probe conflicts with the LLD, **the LLD governs** (e.g. the
> accepted document formats, the Transcribe output reading, the poll
> budgets — see §3).

### 1.1 Premise audit

| # | Premise | Status | Evidence |
|---|---|---|---|
| P-a | v1 is live on real AWS (auto-approve path) | verified | `build/DEPLOY-LEDGER.md` Stage 9: `smoke-1-auto-approve` SUCCEEDED |
| P-b | v1 already formats multimodal Converse requests | **partly refuted** | `understand.py` `to_content_blocks` builds ONE block (text *or* one image). The only image sample `samples/claims/auto-fl-photo.png` is a **1×1 px, 70-byte placeholder**. v1 has never read a real image. v2 must supply real document images and a multi-block request. |
| P-c | v1's ingest image cap is safe for Converse | **refuted** | `understand.py:9` `MAX_IMAGE_BYTES = 5_242_880` (5 MiB). Converse allows **≤ 20 images, each ≤ 3.75 MB / 8000 px**; images only in the `user` role (botocore `bedrock-runtime` `Message.content` doc). A 3.75–5 MiB image passes v1's cap and then fails at Bedrock. → hygiene **H1** (do regardless). |
| P-d | The assignment's Glue DQ Python API | **refuted** | `awsglue.data_quality.DataQualityRule` is not a boto3 API. `glue.CreateDataQualityRuleset.Ruleset` is a **DQDL string** (≤ 65,536 chars). |
| P-e | The assignment's S3 → Lambda `create-event-source-mapping` | **refuted** | Event-source mappings accept only Kinesis, DynamoDB Streams, SQS, MSK, MQ and DocumentDB (botocore `lambda` `CreateEventSourceMapping.EventSourceArn`). v2 uses S3 → **EventBridge** → Step Functions. |
| P-f | The assignment's Transcribe Lambda waits in a `while/sleep` loop | **refuted as a pattern** | The Lambda is billed while it sleeps and has a 15-minute cap. v2 polls from a Step Functions Wait → Get → Choice loop with a poll budget. |
| P-g | The assignment drops low-quality reviews (`quality_score < 0.7 → return`) | **refuted for claims** | A claim cannot be silently dropped. Low quality → human review with reasons. |
| P-h | Comprehend size limits | verified | DetectSentiment 5 KB; BatchDetectSentiment ≤ 25 docs × 5 KB; Detect{Entities,KeyPhrases,PiiEntities,DominantLanguage} 100 KB (botocore `comprehend` docs). → chunking. |
| P-i | Glue DQ can evaluate one batch partition | verified | `GlueTable.AdditionalOptions` supports `pushDownPredicate`. Run `Status` ∈ {STARTING…SUCCEEDED, FAILED, TIMEOUT}. The result has `Score` + `RuleResults[{Name, Result, EvaluationMessage…}]`. `AdditionalRunOptions{CloudWatchMetricsEnabled, ResultsS3Prefix}`. `NumberOfWorkers` defaults to 5 (G.1X). |
| P-j | Idempotent batch lock without DynamoDB | verified (API) / `[gate]` (behaviour) | S3 `PutObject.IfNoneMatch` returns 412 when the key already exists. |
| P-k | IAM resource scoping for the new services | verified | AWS service-reference JSON, fetched 2026-09-23. **No resource type** (so `Resource:"*"` is required): `transcribe:StartTranscriptionJob`, `comprehend:Detect{KeyPhrases,Sentiment,PiiEntities,DominantLanguage}`, `comprehend:BatchDetectSentiment`, `textract:AnalyzeDocument`, `textract:DetectDocumentText`. `comprehend:DetectEntities` can only be scoped to *custom* endpoints, so the built-in model needs `*`. **Scopable:** `transcribe:GetTranscriptionJob` → `transcription-job/${JobName}`; Glue DQ run/result actions → `dataQualityRuleset/${RulesetName}`; Glue catalog actions → `database/`/`table/` ARNs; `states:StartExecution` → the state-machine ARN. |
| P-l | Synthetic data needs no new dependency | verified (probe) | A stdlib-written one-page PDF renders to a 612×792 PNG via `sips`. `say --data-format=LEI16@16000` produces 16 kHz mono PCM WAV (Transcribe `MediaFormat=wav`). The generator is macOS-only; its outputs are committed, so tests never need `say` or `sips`. |
| P-m | v1 open items | verified open | Walkthrough findings register: F2, F10, F11 open. **Consequence:** on real AWS, v2 human-review claims stop at `AwaitReview` exactly as v1's do (now criterion **AC-W17**). |
| P-n | The test gate allows new stdlib modules | **refuted** | `tests/test_no_new_deps.py` has a fixed `_STDLIB` allowlist and scans `claim_processor/*.py` top-level only. v2 must extend the allowlist (stdlib only) and scan subpackages (`rglob`). |
| P-o | Deploy coordinates | verified | acct `324177727513`, `us-east-1`, bucket `claim-documents-poc-rk-20260922`, AppConfig app `claim-processor` (ledger Stages 0–3). |

### 1.2 Directions

| Id | Direction | Verdict |
|---|---|---|
| D-A | **Separate intake state machine → bundle → v1** (follows v1's orchestration pattern, ADR 0004; claim-check via S3 as in `store.py`) | **Chosen (C2-a)** |
| D-B | New states inside the v1 state machine | Rejected. It couples batch-scoped DQ (minutes, one per batch) with the per-claim decision workflow (AC-G1 one execution per claim). It would also redeploy the live machine for every intake change. |
| D-C | S3-triggered Lambda chain with key rewriting (the assignment's shape) | Rejected: P-e, P-f; no orchestration audit trail; brittle `key.replace(...)`. |
| D-D | Bedrock Data Automation as one multimodal extractor | Deferred. The assignment names Textract, Transcribe and Comprehend, and v1 lists BDA as out of scope. Recorded as a future option. |
| D-E | *Demand-side:* skip FM extraction when intake, OCR and narrative already reconcile | Deferred. It changes what the approval gate is based on (AC-E1 assumes an FM extraction), so it needs its own ADR. |
| D-F | *Under-used signal:* FM-vs-source disagreement plus reviewer `field_changes` drive the quality loop | **Adopted** as §X (C4-a). |

### 1.3 Domain mapping (C1-a)

| Assignment | v2 on claims | Family |
|---|---|---|
| Glue DQ on structured feedback | Glue DQ (DQDL) on **claim-intake batches** (CSV) | S |
| Lambda validation of text reviews | Lambda validation of **claimant narratives** | T |
| CloudWatch quality metrics | EMF metrics + dashboard + alarms | Y |
| Comprehend entities / sentiment | Narratives + call transcripts | T, U |
| Textract on product images | **Police-report / repair-estimate images** with Textract Queries | U |
| Transcribe service calls | **First-notice-of-loss (FNOL) call recordings**, PII-redacted | U |
| Survey table → natural-language summary | **Policy loss-run (prior-claims) table** → deterministic summary | U |
| Format for Claude / conversation templates / multimodal requests | Bundle `fm_request` + dialog template + multi-image request | V, W |
| Comprehend themes · normalization · feedback loop | Batch themes · normalizer · proposal loop | U, T, X |

---

## 2. Scope

**In:** S batch admission + rule catalog + Glue DQ gates · T narrative
validation, normalization, redaction · U per-claim sources (Textract,
Transcribe, loss-run summaries, themes) · V reconcile + bundle + model-context
formatting · W the v1 side (V1-01 – V1-23: bundle reader, M1 gate, templates,
`ask` and its dialog, IAM narrowing) · X the human-approved feedback loop
(`dq propose | decide | deployed`) · Y observability (EMF vocabulary, alarms
A1–A12, dashboard) · Z orchestration (the intake ASL, both Maps including the
**Distributed Map for 51–200 rows**), the step dispatcher, module layout,
error classification, IAM (five new roles + the lint), the offline corpus
(B0001, B0002, **B0003**) and e2e, the runbook outline. Plus hygiene **H1v2**
and the **CI hook** (CL4-a). v2 also **creates v1's `operator` role** for
`ask` (B6-6-a; Stage V1d, smoke 9).

**Out** (handover §8): the v1 re-entry list (LLD §12, L6) — F2, F5, F10/F11,
M11, the 5 × 6 retry amplification, the `AwaitReview` heartbeat, v1's EMF
lines, a v1 `ExecutionsFailed` alarm, the five v1 states without
`Retry`/`Catch`, the `guardrail_id: null` pass-through, the unused redacting
logger, `AWSLambdaBasicExecutionRole`, v1's trust files — **noted where v2
depends on one (AC-W17), never fixed here**. Also out: real claim data
(synthetic only until Stage A and the flagged-ADR sign-offs), pricing (the
owner prices the custom-metric series, LLD §7.8), CDK/IaC, SageMaker
Processing, Rekognition, Comprehend topic-modeling jobs or custom
classifiers, Transcribe Call Analytics, BDA, batches > 200 rows (quarantined
at admission), a crawler on the hot path, auto-applied feedback, a reviewer
UI or HITL (F2), non-English text, and hosted CI (CL4-a is a repo pre-commit
script).

---

## 3. Disposition of the 2026-09-23 draft ACs (CL2-a)

The draft's ACs predate the LLD. Each is kept here with a one-line pointer,
in the frozen specs' additive style; the new criteria continue each family's
numbering (S9+, T7+, U13+, V7+, W8+, X7+, Y4+, Z11+). **Re-derived** = the
substance survives, restated from the LLD rules named. **Superseded** = the
LLD changed the substance; the pointer names what replaced it.

| Old AC | Gist | Disposition |
|---|---|---|
| AC-S1 | score < min → quarantine whole batch | Re-derived → AC-S10 (CAT-10: the score is now one of three fail-closed verdicts; alarm A7 replaces the old score alarm) |
| AC-S2 | blocking row rules → row quarantined | Re-derived → AC-S11 (CAT-11; the rule set now comes from the catalog, §2.4) |
| AC-S3 | warning rows proceed flagged | Re-derived → AC-S11 (CAT-11; `normalized:<field>` stays info) |
| AC-S4 | DQDL one file + row twins + parity test | Re-derived → AC-S13 (CAT-01, CAT-05: one catalog renders the DQDL, the row checks and the header; parity by construction, golden render) |
| AC-S5 | catalog table + partition + run params | Re-derived → AC-S14 (CAT-12, GDQ-01, GDQ-02; `ResultsS3Prefix` now per batch, `Timeout` = `DQ_RUN_TIMEOUT_MINUTES`) |
| AC-S6 | DQ poll budget 40 × 15 s | **Superseded by ASL-27/ASL-28: 48 × 15 s, the run's own timeout ends first** → AC-S10, AC-Z15 |
| AC-S7 | outcome to `quality/dq-results/<batch>/summary.json` | **Superseded by REC-16 (A.3 row 9): the outcome record lives in `quality/batches/`; Glue alone writes `quality/dq-results/`** → AC-S11 |
| AC-S8 | max rows + key check | Re-derived → AC-S9 (CSV-02, KEY-06; the key is now `intake/v=1/batch_id=<id>/claims.csv`, M3) |
| AC-T1 | narrative_invalid reasons | Re-derived → AC-T7 (REC-01, SVC-11) |
| AC-T2 | narrative quality checks + score | Re-derived → AC-T13 (the English check is now its own flag, `language_unsupported`, CMP-11) |
| AC-T3 | NFKC normalization, idempotent | Re-derived → AC-T9 (FMT-07 pipeline; idempotence is now the fixed-point check, FMT-45) |
| AC-T4 | shared canonicalizer (dates, amounts, policy, VIN) | Re-derived → AC-T9 (REC-05: the issuer key is `partner_id`, never `channel`; strict order) |
| AC-T5 | `ConfigProvider` + `data-quality` profile + fallback chain | **Superseded by Q4-a / CFG-04–CFG-06: a fresh AppConfig session per batch, no cache, NO fallback; fail closed** → AC-S16, AC-S17 |
| AC-T6 | high-risk PII redaction | Re-derived → AC-T10 (CMP-06/CMP-07: 24 redacted types, 12 kept, enum-complete) |
| AC-U1 | Comprehend chunking | Re-derived → AC-T11 (CMP-03–CMP-05) |
| AC-U2 | entities, key phrases, sentiment | Re-derived → AC-T14 (CMP-13–CMP-15) |
| AC-U3 | sentiment context only | Re-derived → AC-T14 (REC-04, BUN-07, FMT-17: never in `fm_request`, routing, reconcile) |
| AC-U4 | PNG/JPEG/PDF/TIFF accepted | **Superseded by TXT-02, B4-1-a: PNG and JPEG only; PDF/TIFF → `document_failed:<doc_type>:bad_format` → review** → AC-U13 |
| AC-U5 | query sets incl. report number, location, estimate date | **Superseded by TXT-04: exactly three queries (incident date, estimate total, VIN)** → AC-U14 |
| AC-U6 | `documents.json` shape | Re-derived → AC-U15 (TXT-12's schema) |
| AC-U7 | Transcribe poll budget 40 × 15 s | **Superseded by ASL-29: 20 × 30 s, job abandoned on a spent budget** → AC-U19 |
| AC-U8 | one job per revision, redaction config | Re-derived → AC-U18 (TRN-02: output key now `transcripts/<claim_id>/r<rev>/…`) |
| AC-U9 | read `audio_segments`, fall back to items | **Superseded by TRN-09 (A.3 row 32): the documented `items[]` + `speaker_labels`; `audio_segments` unused** → AC-U20, AC-U21 |
| AC-U10 | no-history summary explicit | Re-derived → AC-U22 |
| AC-U11 | deterministic loss-run summary | Re-derived → AC-U22 |
| AC-U12 | themes with claim ids | **Superseded by CMP-20 (M9): the themes record holds no claim ids** → AC-U23 |
| AC-V1 | reconcile fields and sources | Re-derived → AC-V7 (§4.10; B4-10: narrative amounts never count for `recon_mismatch:claim_amount`; M4 corroboration-only) |
| AC-V2 | bundle quality block + score | Re-derived → AC-V8, AC-V17 (FLG-02: score informational) |
| AC-V3 | `fm_request.context_blocks` | **Superseded by §2.7 (A.3 row 20): `sections` + `images` + `views` + `images_in`** → AC-V10, AC-V12 |
| AC-V4 | Converse image limits | Re-derived → AC-V11 (FMT-25; adds the 8,000-px side cap, B5-2) |
| AC-V5 | dialog template + `ask` | Re-derived → AC-W13 (FMT-35–FMT-39; `ask` stays on v1's CLI, runs as the `operator` role, B6-6-a) |
| AC-V6 | bundle written after branches settle | Re-derived → AC-V8 (BUN-01; the key is now `bundles/<claim_id>/r<rev>`, KEY-03/M12 — one key per revision, not overwritten across revisions) |
| AC-W1 | `BundleError` on a bad bundle | Re-derived → AC-W8 (BUN-02) |
| AC-W2 | extraction request from context_blocks | Partly **superseded by Q1-a tightened / BUN-05: the extraction view hides the intake record, loss history and reconciliation notes** → AC-W11, AC-V10 |
| AC-W3 | `bundle:` flags → review | Re-derived → AC-W9 (V1-07) |
| AC-W4 | legacy path unchanged, all tests pass | Re-derived → AC-W16 (A.3 row 18: **deliberate** test updates are listed in LLD §1.5/§10.7.2; everything else unchanged) |
| AC-W5 | result `bundle` field | Re-derived → AC-W14 (V1-05's richer schema) |
| AC-W6 | ASL change: UngroundedFallback passthrough | Re-derived → AC-W14 (V1-11: three keys — `version_id`, `bundle`, `bundle_flags`) |
| AC-W7 | v1 role gains `bundles/*` **and `raw/claims/*`** | **Superseded by SD-4 + the M6 Deny (A.3 row 8, HLD hand-off): v1 reads `bundles/*` only and is explicitly denied `raw/*` and every other v2 zone; images are pre-copied beside the bundle** → AC-W15 |
| AC-X1 | bounded proposal set, never auto-applied | Re-derived → AC-X8, AC-X9 (CFG-09: `set_date_order{partner_id, order}`, not `{channel, order}`; one folder per proposal, REC-25) |
| AC-X2 | feedback record with raw + normalized values | **Superseded by M9 / REC-20: labels only, never a value; key `quality/feedback/<claim_id>/r<rev>/<stage>.json`** → AC-X7 |
| AC-X3 | reviewer `field_changes` precedence | Re-derived → AC-X7 (REC-22; null until F2) |
| AC-X4 | propose thresholds (support, fix rate) | Re-derived → AC-X8 (REC-23 adds: the replay must break nothing) |
| AC-X5 | replay deterministic, offline | Re-derived → AC-X8 (REC-24, REC-28) |
| AC-X6 | resubmission batch, revision + 1 | Re-derived → AC-X10 (SEQ-24, Q8-b: every resubmission goes to review, no exception) |
| AC-Y1 | metric list incl. `ProposalsWritten` | Partly **superseded by B7-4 (`ProposalsWritten` dropped) and OBS-06's closed vocabulary** → AC-Y4 |
| AC-Y2 | dashboard | Re-derived → AC-Y8 (OBS-28, widgets D1–D17) |
| AC-Y3 | alarms `DQRulesetScoreLow`, `ReconMismatchHigh` | **Superseded by §7.5: the twelve alarms A1–A12; `ReconMismatch` is deliberately not alarmed (OBS-27)** → AC-Y7 |
| AC-Z1 | intake state machine shape | Re-derived → AC-Z16, AC-Z17 (§3's richer skeleton) |
| AC-Z2 | lock + duplicate | Re-derived → AC-S12 (REC-06/REC-07: holder inspection, takeover, self-retry) |
| AC-Z3 | v1 execution name | Re-derived → AC-Z34 (EVT-01/EVT-02) |
| AC-Z4 | branch Catch + claim retry ×2 | **Superseded by ASL-21 (retrier T: 4 retries, jittered) + ASL-16/ASL-17** → AC-Z12, AC-Z14 |
| AC-Z5 | payload ≤ 32 KB | Re-derived → AC-Z18 (STP-02, ASL-35) |
| AC-Z6 | IAM lint | Re-derived → AC-Z26 (IAM-69–IAM-88; five v2 roles now, incl. `dq-owner`) |
| AC-Z7 | no PII in logs | Re-derived → AC-Y6 (OBS-14–OBS-21) |
| AC-Z8 | offline CLI, no new deps | Re-derived → AC-Z28, AC-Z35 (MOD-08: the CLI is `python -m claim_processor.dataprep`; TST-31 `rglob`) |
| AC-Z9 | seeded-corpus assertions | Re-derived → AC-Z30, AC-Z31 (TST-28's eleven assertions) |
| AC-Z10 | smoke budget, ≤ 2 batches | **Superseded by C10-2-a: three batches — B0003 (51 rows) proves the Distributed Map** → AC-Z31 (TST-12) |
| AC-H1v2 | `MAX_IMAGE_BYTES` = 3,750,000 | **Carried forward unchanged** — now also V1-03; covered by AC-W16 |

---

## 4. Acceptance criteria (EA-a: by reference)

Each criterion is one testable claim and names the LLD rule ids it covers
("Covers:"); the LLD's rule text is the detailed source. **Failure paths come
first** inside every family, per LLD §9.10; the failure-flow rows (FB, FC,
FF, FV, FA) are mapped to criteria in §5.2. Constants quoted here are the
LLD's; where the two ever disagree, that is an LLD erratum to raise, not a
spec fact.

### S. Batch admission, rule catalog, Glue DQ gates

- **AC-S9** `[off]` IF a batch fails an admission check — the key is not
  `intake/v=1/batch_id=<id>/claims.csv` with exactly one object in its
  partition, the `batch_id`/`claim_id`/`revision`/`partner_id` format is
  broken, the CSV's first line is not byte-equal to the 17-column header
  (after BOM/line-ending removal), the batch has more than 200 data rows
  (`row_gate.MAX_BATCH_ROWS`, checked before any AppConfig or Glue call) or
  more than the pinned `dq.max_batch_rows`, the CSV version changed under the
  lock, AppConfig stays unavailable after retrier C, the config document
  breaks a bound or lacks a `VersionLabel`, or the ruleset is missing or its
  description differs from the catalog hash — THEN the batch SHALL be
  quarantined with its named reason (`invalid_batch_key`, `invalid_schema`,
  `batch_too_large`, `batch_id_reused`, `dq_config_unavailable`,
  `dq_config_invalid`, `dq_catalog_mismatch`), writing the join record and
  the quarantine record, with **zero** Comprehend, Textract or Transcribe
  calls and no v1 start. An invalid key takes no lock and records under batch
  id `_invalid/<hash16>`. *Covers: KEY-01, KEY-06, CSV-01, CSV-02, REC-08,
  REC-18, CFG-05, CFG-06, CAT-07, GDQ-09, ASL-45, ASL-46, ASL-47; FB-3–FB-11.*
- **AC-S10** `[off]` The batch verdict SHALL fail closed: any batch-form rule
  failing (`t_block` = 0.80, `t_warn` = 0.50) → `dq_rule_failed`; score <
  `dq.batch_min_score` → `dq_score_low`; a DQ run ending FAILED/STOPPED/
  TIMEOUT, a spent poll budget (48 × 15 s, then a best-effort cancel), a
  gate-step fault after retries, a `SUCCEEDED` run without exactly one
  result, an unmatched rule result or a result `ERROR` →
  `dq_run_failed` / `dq_catalog_mismatch`; an evaluated row count ≠ Admit's
  `rows_in` (or none reported) → `dq_row_count_mismatch`. Batches under 10
  rows (`MIN_ROWS_BATCH_VERDICT`) skip the rule and score verdicts; the row
  gate still applies. A batch is never processed unvalidated. *Covers:
  CAT-08, CAT-09, CAT-10, CAT-13, GDQ-05, GDQ-06, GDQ-07, GDQ-08, ASL-27,
  ASL-28; FB-12–FB-16.*
- **AC-S11** `[off]` Row fates: a row failing a blocking rule SHALL be
  quarantined with its rule ids and never preprocessed; a failed warning rule
  lets the claim continue carrying blocking `dq_warn:<name>` (→ review); a
  raw value that normalizes cleanly is info `normalized:<field>`. One
  row-only warning on more than half of a batch of ≥ 10 rows SHALL
  quarantine the whole batch as `dq_warn_systemic` before any per-claim
  spend. A blank value fails only its `non_blank` rule; a rule whose input
  did not parse is not evaluated. Quarantined rows appear as `row_index` +
  `rule_ids` (no values, no claim ids) in the quarantine record; a batch
  whose every row is quarantined still ends `processed` with `claims[]`
  empty and gap 0. The outcome record (`batch-outcome/1`, in
  `quality/batches/`, single writer) and quarantine record (`quarantine/1`)
  follow REC-16/REC-17's schemas. *Covers: CAT-11, CAT-14, CAT-15, REC-15,
  REC-16, REC-17, SEQ-04, SEQ-08, SEQ-10, SEQ-11; FB-17, FB-19; FC-8.*
- **AC-S12** `[off]` The batch lock SHALL make delivery-at-least-once safe:
  Admit creates `quality/locks/<batch_id>` with `IfNoneMatch="*"` before any
  other side effect; on 412 it decides in order — a different CSV version →
  `batch_id_reused` (never taken over); its own holder → self-retry with the
  same `attempt`; a RUNNING/SUCCEEDED/PENDING_REDRIVE holder →
  `duplicate_batch` (metric only, no record, no side effect); a
  FAILED/TIMED_OUT/ABORTED holder → takeover with `IfMatch=<ETag>`,
  `attempt + 1` and `takeover_of`; a racing takeover's 412 →
  `duplicate_batch`. `dispatch` and `batch_outcome` re-read the lock and
  return `superseded` writing nothing when the holder changed; the fence
  applies only to executions that held the lock. A batch id is used once:
  crashed executions are re-run by the owner with the same input (Admit takes
  over; never `RedriveExecution`); transient-cause quarantines are
  resubmitted under a new id. *Covers: REC-06, REC-07.1–REC-07.4, REC-09,
  REC-10, EVT-04, EVT-10, ASL-38, ASL-40, SEQ-09, SEQ-18, SEQ-19, SEQ-20;
  FB-1, FB-2.*
- **AC-S13** `[off]` The Intake Rule Catalog SHALL define once — the
  17-column header, every rule (id, columns, kind, severity, threshold,
  warning flag) — and the Glue table columns, Admit's header check and the
  DQDL SHALL all derive from it. `render_dqdl()` is deterministic and its
  output equals the committed `glue/claims_intake.dqdl` byte for byte
  (golden); the ruleset is named `claims-intake-<sha12>` and described
  `catalog_sha256=<64 hex>`; a new catalog is a new ruleset beside the old.
  DQDL rendering keeps the portable subset: completeness as non-blank (never
  `IsComplete`), anchored portable regexes; rules needing canonical values,
  config, two columns or an S3 lookup are row-only. *Covers: CAT-01–CAT-06.*
- **AC-S14** `[gate]`&`[off]` The DQ run SHALL be started with the fixed
  request — the `claim_processor_dq.claims_intake` table with
  `pushDownPredicate "batch_id='<batch_id>'"`, the Glue DQ role,
  `NumberOfWorkers` 2, `Timeout` = `DQ_RUN_TIMEOUT_MINUTES` (10: the largest
  whole minutes with `Timeout × 60 + 15 + 60 ≤` the poll budget's 720 s),
  `ClientToken "<batch_id>-dq-a<attempt>"`, the pinned ruleset name,
  `CloudWatchMetricsEnabled`, `ResultsS3Prefix …/quality/dq-results/<batch_id>/`
  — and Admit SHALL register the partition with the committed
  `StorageDescriptor` (`AlreadyExistsException` = success; no crawler). The
  Glue table definition (17 all-string columns in header order, partition key
  `batch_id`, OpenCSVSerde, `skip.header.line.count` 1) is `[infra]` at
  deploy. *Covers: GDQ-01–GDQ-04, GDQ-10, CAT-12; GDQ-11 is design-only
  (cost note).*
- **AC-S15** `[off]` CSV semantics: every raw value is a string (types
  applied only by Canonicalize Values); `partner_id` — never `channel` — is
  the key for per-issuer policy; document types come from the column
  (`police_report_file` → `police_report`), never the file name; row numbers
  are 1-based data rows. An attachment file name resolves only to
  `raw/claims/<claim_id>/<file>` with `<file>` matching
  `^[A-Za-z0-9._-]{1,64}$` (no `..`); anything else is a blocking row
  defect. *Covers: CSV-03–CSV-06, KEY-05.*
- **AC-S16** `[off]` Admit SHALL read the `data-quality` document once per
  batch through a **fresh** AppConfig session (no cache, no fallback
  document, `config_source=fallback` cannot occur), validate it, and write
  the pin create-only before the DQ run; a self-retry reuses its own pin.
  Every later step of the execution reads the pin, never AppConfig; `as_of`
  is the pin's `pinned_at` date, so one execution judges on one day and
  replay uses the pin's `as_of`. The pin holds the whole document; every
  bundle's lineage and the batch outcome cite it. A batch rejected before
  the pin carries `config: null`. *Covers: CFG-04, CFG-07, CFG-08, REC-14,
  STP-03, STP-07, ASL-47.*
- **AC-S17** `[off]` Config validation SHALL run in two agreeing layers —
  the draft-04 JSON Schema attached to the profile and
  `dq_config.validate` in stdlib code — tested over one shared good/bad
  table; the code adds the one cross-key rule
  (`history.frequency_window_months` ≤ `history.lookback_months`). Bounds
  apply to every change, hand-made or proposal; the bounds table records per
  key which direction widens auto-approve. *Covers: CFG-01–CFG-03.*

### T. Narrative, normalization, redaction, language

- **AC-T7** `[off]` IF the narrative is absent, empty, not UTF-8, over
  `narrative.max_bytes` (100,000), missing at read time, or unreadable to
  Comprehend, THEN the claim SHALL carry blocking
  `narrative_invalid:<reason>` (reasons closed: `missing`, `empty`,
  `not_utf8`, `too_large`, `not_found`, `unreadable`) and continue; the
  claim is never dropped. Source status is `ok | missing | failed |
  disabled`; a record is written for every status except `missing`; a
  missing *optional* source raises no flag. *Covers: REC-01, SVC-11
  (narrative family); FF-3 (narrative row).*
- **AC-T8** `[off]` Every text SHALL be normalized (`canonicalize.text`)
  **before** redaction, never after; every text field of a processed record
  is normalized then redacted before the record is written; if any
  `DetectPiiEntities` call of a source fails, none of that source's text is
  persisted (no partial redaction). The formatter later re-normalizes and
  requires a no-op (AC-V13). *Covers: CMP-09, CMP-10, REC-02; G42.*
- **AC-T9** `[off]` One canonicalizer SHALL serve every source:
  `canonicalize.text` (newline unification, NFKC, control/format-character
  removal in the LLD's exact order) and the structured parsers — dates to
  ISO with the issuer's order from `normalization.date_order.by_partner`
  (else `default`), strict for every numeric date; amounts to two-decimal
  numbers; policy numbers to `POL-<ST>-<AU|HO>-<5 digits>`; VINs to 17
  characters. A numeric date with both leading parts ≤ 12 and differing is
  ambiguous: the issuer's order picks the reading, the other is kept as
  `alternate`, and Reconcile raises blocking `dq_warn:ambiguous_date` unless
  a non-claimant source states the date unambiguously at ≥
  `textract.min_confidence`; corroboration never flips the canonical value;
  narrative dates never corroborate. `find_mentions` extracts
  dates/amounts/policy numbers/VINs from redacted text with pure stdlib
  regexes. *Covers: FMT-07, REC-05, CMP-17, CSV-03; G22.*
- **AC-T10** `[off]` PII policy: the 24 `REDACT_PII_TYPES` SHALL be replaced
  as `[<TYPE>]` verbatim at any score; the 12 `KEEP_PII_TYPES` are kept; a
  test reads botocore's `PiiEntityType` enum and requires every value except
  `ALL` to be in exactly one list, so a new AWS type fails the suite. Info
  items `pii_redacted:<TYPE>` appear once per type; counts only — no value,
  offset or score is written anywhere. `redact.scrub_digit_runs` masks every
  run of ≥ 4 digits in transcript turns as `[DIGITS]` before `call.json` is
  first written. *Covers: CMP-06, CMP-07, CMP-08, REC-03; G26.*
- **AC-T11** `[off]` Chunking SHALL fail toward more redaction: deterministic
  sentence-boundary chunks within each Comprehend limit, entity/PII/key-
  phrase calls overlapped by `PII_OVERLAP_CHARS` (200) with spans widened to
  whole tokens and applied under both code-point and byte readings;
  cross-boundary spans clipped and both parts replaced; sentiment chunked
  without overlap so each byte counts once. Segment packing
  (`redact_segments`) maps spans back per segment, within CMP-01's closed
  API surface and limits. *Covers: CMP-01, CMP-02, CMP-03, CMP-04, CMP-05.*
- **AC-T12** `[off]` WHEN the redacted narrative is under
  `MIN_LANGUAGE_CHARS` (20), detects no language, is not `en`-dominant, or
  scores under `comprehend.min_language_score`, THEN the claim SHALL carry
  blocking `language_unsupported`; no entity, key-phrase or sentiment call is
  made; the redacted text is still written (redaction always runs as `en`).
  *Covers: CMP-11, CMP-12; FF-7 (language row).*
- **AC-T13** `[off]` Narrative quality SHALL be scored with deterministic
  checks (length ≥ `narrative.min_chars` 80, loss lexicon, date reference,
  placeholder text, claimant/policy mention); a score below
  `narrative.min_quality` (0.7) SHALL raise blocking
  `narrative_quality_low`; checks and score are recorded in
  `narrative.json`. *Covers: CMP-10 (order), the `narrative_quality` module
  (MOD-01); FF-7.*
- **AC-T14** `[off]` Insights: entities kept at `Score ≥
  comprehend.min_entity_score`, the top `comprehend.top_key_phrases` key
  phrases, and byte-weighted mean sentiment with argmax label (batch errors
  fail the whole step retryably — no partial sentiment; B4-7). Sentiment is
  **context only**: it appears only in `narrative.json`, `call.json` and the
  bundle's `sources.*.sentiment`, and `routing.py`, `reconcile.py` and
  `model_context.py` never reference it. *Covers: CMP-13, CMP-14, CMP-15,
  CMP-16, REC-04; G11.*

### U. Per-claim sources: documents, calls, history, themes

- **AC-U13** `[off]` Document pre-checks SHALL run in order, each failure
  costing no Textract call: listing (absent → `not_found`; size over
  `TEXTRACT_MAX_BYTES` = 5,000,000 → `too_large`); magic bytes — **PNG and
  JPEG only** (B4-1-a), decided from bytes never the file name, else
  `bad_format`; header dimensions — unreadable → `bad_format`, a side over
  10,000 px → `too_large`. Each failure records blocking
  `document_failed:<doc_type>:<reason>` and the claim continues (→ review).
  *Covers: TXT-02, TXT-03, SVC-12; FF-3 (document row).*
- **AC-U14** `[off]` Textract SHALL be called once per document —
  `AnalyzeDocument`, `FeatureTypes=["QUERIES"]`, bytes input (no S3 access,
  no async) — with the code-constant `QUERY_SETS` (police report:
  incident date, required; repair estimate: estimate total, required; VIN,
  optional). Answers resolve via `Relationships[ANSWER]` → highest
  confidence; a missing answer leaves its alias absent. An answer under
  `textract.min_confidence` (80) is kept, marked `low_confidence`, raises
  info `low_confidence_ocr:<doc_type>:<alias>`, and is **never** a
  reconciliation source. *Covers: TXT-01, TXT-04, TXT-05, TXT-06.*
- **AC-U15** `[off]` The document record SHALL keep `LINE` text in response
  order joined by `\n`, `ocr_confidence{min, mean}`, and TXT-12's fields;
  `lines_text` and every answer are normalized then redacted in one
  `redact_segments` call per document before the record is written. Textract
  query answers are never rendered into the model context (B5-5); the OCR
  lines carry the text. *Covers: TXT-07, TXT-08, TXT-12; FMT-13.*
- **AC-U16** `[off]` L1 — OCR is sufficient when all three hold: ≥ 1 line,
  `ocr_confidence.mean` ≥ `images.ocr_sufficient_min_confidence` (default
  90, bounds 50–100; lowering it widens auto-approve), and every required
  query answered at ≥ `textract.min_confidence`. The image decision is
  `image{eligible, reason}`: `ocr_sufficient` → not eligible; `pii_found`
  (Layer 2 replaced at least one entity in that document, B4-2-a) → not
  eligible; `ocr_insufficient` with no PII → eligible. A non-`ok` document
  has `image: null`. *Covers: TXT-09, TXT-10, TXT-11.*
- **AC-U17** `[off]` Call pre-checks SHALL accept **only 16-bit PCM WAV, at
  most 600 s by the header** (`MAX_CALL_SECONDS`; B4-6): listing (absent →
  `not_found`; over `MAX_CALL_BYTES` 20,000,000 → `too_large`; under 44
  bytes → `bad_format`); one ranged read (8 KiB) recording the VersionId;
  magic bytes `RIFF…WAVE` only — flac/ogg/mp3/m4a/mp4/webm/amr →
  `bad_format`; a non-PCM, non-16-bit, inconsistent or truncated header →
  `bad_format`; duration over 600 s → `too_large`. Every failure is blocking
  `call_failed:<reason>` and the claim continues. *Covers: TRN-01; FF-3
  (call row).*
- **AC-U18** `[off]` The Transcribe job SHALL be fixed and idempotent per
  revision: name `clm-<claim_id>-r<rev>`, `en-US`, `wav`, output
  `transcripts/<claim_id>/r<rev>/…` in the intake bucket,
  `ShowSpeakerLabels` with `MaxSpeakerLabels` 2, `ContentRedaction` with
  `RedactionOutput "redacted"` and the seven `TRANSCRIBE_PII_TYPES` (never
  `redacted_and_unredacted`); `ConflictException` → poll the existing job; a
  job already FAILED under that name → `call_failed:job_failed`, no second
  job. *Covers: TRN-02, TRN-03, TRN-04, TRN-06, EVT-03.*
- **AC-U19** `[off]` Job lifecycle: QUEUED/IN_PROGRESS → keep polling within
  the state machine's budget (20 × 30 s); FAILED → `call_failed:job_failed`;
  still running when the budget is spent → `call_failed:poll_budget`, the
  job abandoned (no stop API) and late output ignored; an unstarted call
  (`missing`, `disabled`, or a failed pre-check) reaches `call_finish`
  directly, which makes no service call and writes the record with the
  start's status (no record for `missing`). *Covers: TRN-05, TRN-12,
  ASL-29; FF-4.*
- **AC-U20** `[off]` `call_finish` SHALL trust nothing it did not ask for:
  the job's `ContentRedaction` must match, `Media.MediaFileUri` must be this
  claim's recording, `CreationTime` ≥ the recording's `LastModified`; it
  reads **only** `Transcript.RedactedTranscriptFileUri` (https on the intake
  bucket, key under `transcripts/<claim_id>/r<rev>/`), requires top-level
  `isRedacted` true, and builds turns from the documented `results.items[]`
  + `speaker_labels` (first speaker `agent`; `audio_segments` unused). Any
  mismatch, invalid JSON, or an unrequested redaction type →
  `call_failed:bad_output` (B4-8), the output never used. *Covers: TRN-07,
  TRN-08, TRN-09; FA-9 (call part).*
- **AC-U21** `[off]` Before `call.json` is first written, every turn SHALL go
  through, in order: `canonicalize.text`, Layer 2 `redact_segments` over all
  turns, the digit-run scrub, then per-speaker sentiment; `pii.types` counts
  Layer 1 redactions, Layer 2 types and `DIGIT_RUN`. The record's lineage
  names the recording's and the transcript's key + VersionId. *Covers:
  TRN-10, TRN-11, CMP-16; G42 (call part).*
- **AC-U22** `[off]` The loss-run summary SHALL be deterministic (no FM, no
  AI call): the same input gives a byte-identical summary over
  `history.lookback_months` (36); no rows in the window → an explicit
  "no prior claims" summary, never an omitted section; ≥
  `history.frequency_threshold` (3) claims within
  `history.frequency_window_months` (12) → blocking
  `history_frequency_high` (Q7); an unreadable or stale loss-run source →
  blocking `history_failed` / `history_unavailable` — unverifiable is not
  clean (M4), and history is never `missing`. Join keys and dates go through
  Canonicalize Values. *Covers: REC-01 (history), the `loss_history` module,
  M4 flags; FF-8; G24 (history part).*
- **AC-U23** `[off]` Themes SHALL aggregate only status-`ok` narratives of
  the batch's outcome claims, using only phrases marked theme-eligible (no
  overlap with any `PERSON`/`LOCATION` span, no placeholder, digit or `@`);
  normalized, listed only at ≥ `THEMES_MIN_CLAIMS` (2) claims, capped at
  `THEMES_MAX` (50), deterministic order. The themes record holds **no claim
  ids and no row indexes** (M9) and themes make no AWS AI call; themes runs
  only for a processed batch. *Covers: CMP-18, CMP-19, CMP-20.*
- **AC-U24** `[off]` WHILE `sources.disable-<src>` is true in the batch's
  pin, that source's step SHALL return `disabled` with blocking
  `source_disabled:<src>`, reading no raw object and making no service
  call, for every claim of that batch and no other (the pin scopes kill
  switches per batch). *Covers: SVC-13, SEQ-14; FF-6.*

### V. Reconcile, bundle, model-context formatting

- **AC-V7** `[off]` Reconcile SHALL compare exactly four fields —
  `loss_date` (intake vs police report and narrative), `claim_amount`
  (intake vs the repair-estimate total **only**; narrative amounts never
  count, B4-10), `policy_number` (narrative), `vin` (estimate and
  narrative) — with corroboration that only confirms, never flips; a
  disagreement raises blocking `recon_mismatch:<field>`, a sole unusable
  cross-check raises blocking `recon_unverifiable:<field>`; low-confidence
  answers, transcripts and sentiment are never sources; the amount tolerance
  is `recon.amount_tolerance_pct` (2 %). *Covers: REC-05 (reconcile part),
  §4.10, the `reconcile` module; FF-9; G24.*
- **AC-V8** `[off]` The bundle (`schema_version` 2.x) SHALL be written only
  after every source branch settles, image copies first
  (`bundles/<claim_id>/r<rev>-img-<n>.<ext>`) and the bundle object last as
  the commit marker — v1 can never read a bundle whose images are missing.
  One key per revision; a same-execution retry writes new versions of the
  same keys and dispatches the version it wrote. The bundle's lineage names
  an S3 VersionId for every input (CSV, attachments, processed records,
  image copies, the config pin); canonical `claim_amount` is a two-decimal
  JSON number, dates ISO strings. *Covers: BUN-01, BUN-08, BUN-09, KEY-03,
  KEY-04; G31 (bundle side).*
- **AC-V9** `[off]` `contracts.read_bundle` SHALL be a tolerant reader:
  accept `^2\.[0-9]+$` ignoring unknown keys; an unknown major version,
  invalid JSON or missing required path raises `BundleError` naming the
  path. Writers never remove or rename a 2.x field; new optional fields bump
  the minor; `fm_request.format_version` versions the tag vocabulary and v1
  raises `BundleError` on an unknown one. *Covers: BUN-02, BUN-03.*
- **AC-V10** `[off]` Views SHALL contain what they may show: the
  **extraction view never contains a canonical intake value** — it excludes
  `intake_record`, `loss_history` and `reconciliation_notes` (Q1-a
  tightened; proven by the AC's sentinel test); the summary view adds
  `loss_history` + `reconciliation_notes` to v1's inputs; the dialog view
  may hold every section; `images_in` is `["extraction","dialog"]` — the
  summary never carries images. Sentiment appears in no view (BUN-07, FMT-17).
  *Covers: BUN-05, BUN-07, FMT-05, FMT-17; FMT-49; G21 (view side).*
- **AC-V11** `[off]` The M6 image rule SHALL be the decision table and only
  its `sent` row produces an image: a non-`ok` document sends nothing (its
  own flag); `ocr_sufficient` → `not_needed`; `pii_found` → blocking
  `image_withheld:pii`; changed after vetting → blocking
  `image_skipped:changed` (Assemble copies an image **only** from the
  version Read Document Text vetted, checking `CopySourceVersionId`);
  wrong format / over 3,750,000 bytes / a side over 8,000 px / beyond
  `images.max_images` → blocking `image_skipped:<reason>`. Every blocked
  image means the claim cannot auto-approve without it. Images are
  referenced by bundle key (never embedded), `user` role only. *Covers:
  BUN-06, BUN-10, FMT-24, FMT-25, FMT-26, rows I1–I8/I3a; FF-10; FA-9;
  G26, G49 (producer side).*
- **AC-V12** `[off]` The formatter SHALL render exactly the format-version-2
  vocabulary: the seven sections in fixed order, the closed attribute set
  (source, version_id, revision, confidences, image, redacted — never a file
  name, S3 key, claim id or claim value), each `rendered` string complete,
  tagged, redacted, escaped and never blank; section bodies per source as
  the LLD fixes them (intake record lines from `intake.normalized`;
  narrative text; OCR lines; `Agent:`/`Caller:` turns; the history summary;
  one reconciliation line per field with verdicts); byte-identical output
  for the same inputs. *Covers: FMT-01, FMT-02, FMT-03, FMT-04, FMT-06,
  FMT-11–FMT-16, BUN-04; FMT-43; G12.*
- **AC-V13** `[off]` IF a processed text reaching the formatter is not a
  fixed point of `canonicalize.text`, THEN the formatter SHALL raise
  `FormatError` (never retried) and the claim ends `claim_failed` visibly —
  vectors N1/N2. *Covers: FMT-08, N1, N2; G42 (formatter side).*
- **AC-V14** `[off]` Escaping SHALL make every `<` in a rendered section a
  tag our code wrote: `&` first, then `<`, `>`, and `"` in attributes;
  redaction placeholders pass byte for byte; unescape(escape(x)) returns the
  normalized input (property-tested). *Covers: FMT-09, FMT-10; FMT-44,
  FMT-45, FMT-47; G30.*
- **AC-V15** `[off]` Truncation SHALL be bounded and marked: per-section caps
  (`SECTION_MAX_CHARS`; transcript cap `format.max_transcript_chars` 6,000,
  bounds 1,000–20,000, B5-1-a), head/tail keeping whole units with `elided`
  markers, first and last unit always kept, no cut splitting an escape
  entity; every cut adds info `truncated:<section_id>` (never routing); the
  worst-case dialog view stays ≤ 61,000 chars and extraction ≤ 56,000 (at
  the 20,000 cap). *Covers: FMT-18–FMT-23; FMT-51.*
- **AC-V16** `[off]` The formatter fitness suite SHALL exist as the LLD
  names it — order/names, tag integrity, vectors, no-sentiment, placeholder
  survival, the H-F14-a and BUN-05 sentinels, the image table, caps, request
  validation, determinism goldens and template hashes. *Covers: FMT-43–FMT-53
  (each also cited by its substantive criterion); G38 (offline half).*
- **AC-V17** `[off]` The flag vocabulary SHALL be closed in `contracts.py`
  (family + suffix pattern; a flag outside it fails the suite); blocking
  flags and info items live in separate lists; routing reads only
  `quality.flags`; a suffix names a field, type, source or reason — never a
  value; `bundle_quality_score` is informational. *Covers: FLG-01, FLG-02,
  FLG-03; G44 (vocabulary side).*

### W. The v1 side (CL5-a: every v2 change to a v1 file is specified here)

- **AC-W8** `[off]` The v1 bundle read path SHALL be versioned end to end:
  `store.get_bytes_versioned` returns the VersionId; the read bundle's
  VersionId must equal the input's `version_id` and each image's its
  `images[].version_id` — a bundle mismatch raises blocking
  `bundle:version_mismatch` (→ review), a mismatched image is not sent (same
  flag); an image at the right version over the cap or with wrong magic
  bytes raises `BundleError` (producer defect — the execution fails
  visibly), as does an unreadable bundle; `retrieve_summarize` re-reads and
  re-checks the bundle (a mismatch there ends in `UngroundedFallback` →
  review); `understand_extract`/`degraded_extract` pass `version_id` into
  the pipeline. *Covers: V1-01, V1-02, V1-17, V1-18; FV-1–FV-4, FV-10,
  FV-11; G49 (consumer side); FMT-31.*
- **AC-W9** `[off]` The M1 gate (Q1-a tightened) SHALL hold at validation
  **and** routing, through the handler path: for a bundle key the decision
  uses the canonical intake values of the three M1 fields; an FM value
  present and different (amount outside max($1.00, 2 %) — a code constant;
  a non-ISO date; policy numbers compared uppercased without spaces/hyphens)
  → blocking `bundle:fm_source_mismatch:<field>`; one absent M1 field →
  `bundle.fm_absent[]`, no flag; two or three absent → blocking
  `bundle:fm_evidence_missing`; a state without `bundle_flags` → blocking
  `bundle:flags_missing`; any bundle flag → review; the amount threshold
  routes on `bundle.canonical.claim_amount`, never the FM value;
  `extracted_info` keeps the FM output verbatim. *Covers: V1-06, V1-07,
  V1-16, V1-20, V1-21; FV-7, FV-8; G14, G21, G37 (flags half).*
- **AC-W10** `[off]` WHEN Record receives a dict payload routed
  `auto_approve`, it SHALL re-run `route_claim` under the state's
  `config_snapshot` (which now records `force_review_flags`); a disagreement
  is written to `pending-review/` with `record_recheck_failed` as an
  operator item. *Covers: V1-08, V1-19; FV-9; G37 (re-check half).*
- **AC-W11** `[off]` v1 SHALL build bundle requests without parsing rendered
  sections: one `guardContent` block per view section in order (plain
  `text` when no guardrail is configured), then the view's images as plain
  `image` blocks, then the template blocks; bundle requests are **always**
  tagged (H-F14-a; the legacy image-claim exemption does not apply); no
  `qualifiers` key; the adapter `prompt` string joins every block and is
  never logged; `{extracted_info}` in the summary template stays guarded and
  is JSON-escaped. The three new templates (`extract_info_bundle`,
  `generate_summary_bundle`, `adjuster_dialog`) declare `_UNTRUSTED_FIELDS`,
  carry no claim values, accept `format_version` "2" only, and are versioned
  with SHA-256-pinned texts; a legacy key's `prompt_versions` stays
  byte-identical. *Covers: V1-04, FMT-27–FMT-30, FMT-33, FMT-34,
  FMT-40–FMT-42; FMT-48; G38.*
- **AC-W12** `[off]` Degradation and RAG for a bundle key SHALL use canonical
  values only: the RAG scope maps canonical jurisdiction/line codes to the
  retriever vocabulary (no keyword inference); the rule-based floor takes
  the canonical intake fields (plus the redacted narrative head), never the
  claim id as a policy number, still sets `RULE_BASED` and routes to review;
  an empty extraction view makes **no model call** and takes that floor.
  *Covers: V1-09, V1-10, FMT-32; FV-5, FV-6; G34, G35.*
- **AC-W13** `[off]`&`[gate]` The `ask` dialog SHALL run on v1's CLI as the
  **`operator` role that v2 creates** (B6-6-a; Stage V1d, smoke 9, IAM-91,
  IAM-92): stateless multi-turn Converse re-sending `messages[0]` byte for
  byte (dialog view + images + one default-TTL `cachePoint` for listed
  models only), at most `DIALOG_MAX_TURNS` (10) questions of ≤ 2,000 chars,
  `maxTokens` 500, a guardrail on every call (on real AWS `ask` refuses to
  start without one; an intervention on turn 1 ends the session), one
  provenance line per turn (bundle key + VersionId, template versions,
  model id, usage incl. cache tokens, guardrail outcome);
  `ModelInvoker.converse` gains the `messages=` argument keeping the one
  retry layer; `adjuster.py` lives on the v1 side and reads bundles through
  `dataprep.contracts` only. *Covers: FMT-35–FMT-39, V1-23, MOD-02; FMT-54
  `[gate]`.*
- **AC-W14** `[sfn]`&`[off]` v1's definition SHALL change only in the
  `UngroundedFallback` whitelist — the three keys `version_id`, `bundle`,
  `bundle_flags`, emitted by every extract path — and
  `ProcessingResult.bundle` (V1-05's schema) is optional and emitted only
  when set, so pre-v2 results still serialize. *Covers: V1-05, V1-11, KEY-07.*
- **AC-W15** `[off]`&`[gate]` v1's IAM SHALL be narrowed, never widened
  (the AC-W7 fix): the step-Lambda role gains **only** `s3:GetObject` on
  `bundles/*`; every v1 S3 resource is pinned to the exact bucket; an
  explicit Deny covers `raw/*` and every v2 zone (`intake/*`, `history/*`,
  `transcripts/*`, `processed/*`, `quality/*`); `sfn-exec` names the eight
  exact function ARNs and the exact v1 log group; `remediation` reaches the
  `model-selection` profile only (the stated IAM-64 residual accepted);
  `operator`'s pending-review read is bucket-pinned and it gains only the
  B6-6-a grants. The owner's `simulate-principal-policy` checks (IAM-89) are
  the `[gate]`. *Covers: V1-12, V1-13, IAM-57–IAM-65, IAM-91; G20, G28.*
- **AC-W16** `[off]` The legacy path SHALL stay byte-compatible: a key not
  under `bundles/` behaves exactly as today; `MAX_IMAGE_BYTES` = 3,750,000
  for every key (H1v2); the intake plane reuses v1's `emit_metric` and
  `logging_safe` without changing v1 code; the **deliberate** v1 test
  updates are exactly LLD §1.5/§10.7.2's list, and every other v1 test
  passes unchanged; the deploy order (V1-22, `[infra]`) puts every v1 change
  live and checked before the intake trigger is enabled. *Covers: V1-03,
  V1-14, V1-15, V1-22, AC-H1v2.*
- **AC-W17** `[off]`&`[gate]` **F2 dependency (v1 re-entry; not fixed
  here):** until the `claim-processor-await-review` Lambda ships, a
  review-bound v1 execution writes its `pending-review/bundles/…` record and
  then fails at `AwaitReview` (`Lambda.ResourceNotFoundException`); reviewer
  `field_changes` stay null (REC-22). The smokes SHALL expect exactly this —
  **7 such failures in B0001 and 2 in B0002**, distinguished from a bundle
  failure by the failing state (`AwaitReview`, not `UnderstandExtract`).
  *Covers: FV-12, REC-22, LLD §12 (F-a).*

### X. The feedback loop and proposals

- **AC-X7** `[off]` Feedback records SHALL be create-only, deduplicated and
  value-free: one record per (claim, revision, stage) at
  `quality/feedback/<claim_id>/r<rev>/<stage>.json` (a 412 means no rewrite
  and no second metric); labels only (`agree`/`disagree`/`absent`/`n/a`),
  names as booleans; results with a degradation tier, open breaker, no FM
  output, or a changed bundle VersionId are recorded `excluded` and never
  count as evidence; which record is first is decided from the record the
  step reads, never a lookup; reviewer `field_changes`, when F2 ships, take
  precedence as names only. *Covers: REC-19, REC-20, REC-21, REC-22, REC-27,
  SEQ-26; FA-3, FA-4; G29 (feedback half).*
- **AC-X8** `[off]` A proposal SHALL be written only when all three hold:
  support ≥ `feedback.min_support` (3), fix rate ≥ `feedback.min_fix_rate`
  (0.80), and a deterministic, offline replay (no FM, no AWS AI call,
  stored inputs by lineage VersionIds) over **every claim the change can
  affect** (that partner for `set_date_order`, every partner otherwise)
  breaks nothing; outcomes are re-derived twice (base vs changed config)
  into fixed/broken/unchanged per partner. Candidates are drawn as REC-29
  fixes them; the proposal types are a closed enum (`set_date_order`,
  `add_date_format`, `adjust_threshold`) whose params cannot express any
  other change, and no proposal can leave the config bounds. *Covers:
  REC-23, REC-24, REC-28, REC-29, CFG-09, CFG-10, SEQ-27; G15, G25 (replay
  half), G48 (proposal half).*
- **AC-X9** `[off]` The proposal lifecycle SHALL be three create-only files
  per proposal (`P-<yyyymmdd>-<nnn>`): the proposal with its evidence (claim
  ids and counts, never values), `decision.json` from `dq decide`,
  `deployed.json` from `dq deployed` recording the AppConfig version label
  — run **only after** the deployment completes. Neither command deploys
  anything: the owner creates and bakes the labelled hosted version as the
  deployer; the CLI runs as `claim-processor-dq-owner` (no Bedrock, no
  AppConfig grant, S3-side only, `python -m claim_processor.dataprep`).
  *Covers: REC-25, REC-26, MOD-08, SEQ-28, SEQ-29; G15, G29 (CLI half).*
- **AC-X10** `[off]` Resubmission SHALL always mean review (Q8-b): a marker
  for **any other** revision — earlier or later, decided or in flight —
  raises blocking `resubmission_review` with no exception
  (`rerun_proposal_id` is lineage only); markers are create-only at Gate
  Claim Rows, before any per-claim spend, only for passing rows; a revision
  is used once (`revision.not_reused` across batches, `claim_id.unique`
  within one); a `claim_failed` claim returns only as revision + 1 in a new
  batch (S9-1). The loop's effect shows as **cleared flags on the re-run,
  not auto-approval** — except a claim whose r1 was row-quarantined (no
  marker), which may auto-approve. *Covers: REC-11, REC-12, REC-13 (marker
  half), SEQ-16, SEQ-24, SEQ-25, SEQ-30; FA-10; FF-2; G25, G40 (marker
  half).*

### Y. Observability

- **AC-Y4** `[off]` Metrics SHALL take one path: EMF via v1's `emit_metric`
  with namespace `ClaimProcessor/DataQuality` and intake's own bare-stdout
  INFO logger, through `telemetry.py` alone (no other dataprep module
  imports logging/metrics; no `PutMetricData`); the vocabulary is the LLD's
  closed table (24 metrics; `ProposalsWritten` deliberately absent, B7-4),
  ≤ 2 dimension keys from closed enums, an out-of-enum value emitted as
  `other` and failing F6; never an id, `partner_id`, key or free text as a
  dimension; ≤ 137 series (test fails above 140); one line per invocation
  with only `step` and `request_id` as properties. *Covers: OBS-01, OBS-02,
  OBS-06–OBS-12; F6, F9; G43.*
- **AC-Y5** `[off]` Records SHALL stay the truth: no decision reads a
  metric; a step emits metrics and its log line **after** its S3 writes
  succeed (a failed write emits no outcome metric; a 412 on create-only
  emits nothing); `RowsIn`/`RowsQuarantined` are emitted only for batches
  the row gate processed (B7-5), so A12's ratio is well-defined. *Covers:
  OBS-03, OBS-04; F10; FA-11.*
- **AC-Y6** `[off]` Logs SHALL carry no values: exactly one structured step
  line per invocation with closed keys and per-step outcome enums; claim
  ids only on per-claim lines whose ids passed the row gate; never a claim
  value, raw event, S3 key/VersionId, file name, `partner_id`, exception
  message/traceback or config document — in logs, exceptions (`error{class,
  code}` only, raised `from None`) or state payloads; no dataprep code
  changes root/boto3/botocore log levels; the redacting logger is the
  backstop. *Covers: OBS-14–OBS-19, OBS-21, SVC-07; F2, F8; G7 (offline
  half), G47 (privacy half).*
- **AC-Y7** `[off]`&`[infra]` The twelve alarms A1–A12 SHALL exist as data
  (`build/alarms/intake.json`), every one notify-only to
  `claim-processor-intake-alerts` (never v1's remediation topic), 300 s / 1
  of 1 / `notBreaching`, FILL-wrapped math; the deliberately un-alarmed list
  (`SourceFailed`, transcribe budget, `ReconMismatch`, `DuplicateBatch`,
  `FieldDisagreement`, v1's own failures) stays un-alarmed; A1+A3 pair on a
  dead batch. *Covers: OBS-24–OBS-27; F7 `[off]`, F12 `[infra]`.*
- **AC-Y8** `[off]` The dashboard (`build/dashboards/data-quality.json`,
  widgets D1–D17) SHALL parse, reference only vocabulary metrics and
  allow-listed AWS namespaces, and chart what the LLD fixes. *Covers:
  OBS-28; F7.*
- **AC-Y9** `[infra]` Platform observability settings: the intake log group
  is pre-created with 14-day retention; X-Ray stays off; **the intake state
  machine does not log** (B6-1 = b); the trigger DLQ keeps messages 14 days
  (envelopes, not claim values). *Covers: OBS-05, OBS-20, OBS-22, OBS-23.*
- **AC-Y10** `[gate]` After the smoke the metrics SHALL exist in CloudWatch
  (`list-metrics` shows the namespace; `RowsIn` sums to the batch's
  `rows_in`) — the only proof OBS-10's EMF lines parse. *Covers: OBS-13;
  F11.*

### Z. Orchestration, dispatcher, modules, IAM, tests, runbook

- **AC-Z11** `[off]`&`[sfn]` A deploy defect SHALL fail the execution and
  **never become a flag** (B4-4): a missing grant or resource, a rejected
  request, an unknown `step`, or a missing/malformed value among STP-06's
  **eight environment variables** (checked once per cold start; a leftover
  upper-case token counts) raises `DeployDefectError` — never retried, never
  caught into a fate; the only Fail states are the two deploy-defect ones;
  the watchdog records `batch_failed`, the owner fixes and re-runs, and the
  takeover keeps the batch id. Steps signal expected outcomes in `status`,
  never by raising; the raisable classes are exactly STP-04's six. *Covers:
  STP-01, STP-04, STP-06, SVC-10, ASL-04, ASL-52, SEQ-17; FA-7; G45 (defect
  half).*
- **AC-Z12** `[off]`&`[sfn]` Per-claim failures SHALL be contained: every
  iteration Task catches `DeployDefectError` first, then
  `States.DataLimitExceeded`, then `States.ALL` (each Catch
  `ResultPath "$.error"`) into `ClaimFailed`; each source branch catches
  into its own `<Source>Failed` Pass with blocking `source_failed:<src>` and
  the error name only (the `Cause` never leaves the iteration); a
  self-detected source failure returns `failed` with its family flag and is
  not retried; a faulted claim ends fate `claim_failed` while its siblings
  finish and the batch ends `processed`; `already_started` and `superseded`
  are ordinary fates; a Lambda throttle or timeout follows the same
  catchers. *Covers: ASL-16–ASL-20, SEQ-12, SEQ-13, SEQ-15; FC-4, FC-6,
  FC-7; FA-5, FA-6; FF-5.*
- **AC-Z13** `[off]`&`[gate]` Crashes and lost events SHALL be visible and
  recoverable: the watchdog fires on the parent's FAILED/TIMED_OUT/ABORTED
  only (child events under the Map label are ignored), writes exactly one
  create-only `….watchdog.json` without reading the lock, and emits one
  `BatchFailed{Status}`; `Admit` (but for config errors), `GateRows` and
  `BatchOutcome` have no Catch — if their dependencies are down the batch
  crashes and the watchdog records it; the batch-gate steps instead fail
  closed to `dq_run_failed`; a lost start event lands in the trigger DLQ
  (default retry policy; queue policy pinned to the rule's ARN) for the
  owner to replay as an execution input; join and watchdog records never
  collide. *Covers: ASL-41–ASL-44, EVT-07, EVT-08, EVT-09, REC-16 (watchdog
  entry), SEQ-21, SEQ-22, SEQ-23; FB-18; FA-1, FA-2, FA-8; G33.*
- **AC-Z14** `[off]`&`[sfn]` Retries SHALL have one owner, the state
  machine: every Task carries retrier T (the exact transient error list,
  `IntervalSeconds` 2, `BackoffRate` 2.0, `MaxAttempts` 4, `MaxDelaySeconds`
  30, FULL jitter); only `Admit` adds retrier C for `ConfigUnavailableError`;
  no retrier lists a permanent error (`States.ALL`, `States.TaskFailed`,
  `States.Timeout`, runtime failures, `DeployDefectError`, `FormatError`);
  every retried step is idempotent via its key/token/marker. The intake
  boto3 clients are built once per container from an injected session, the
  closed seven-service set with pinned region, per-service timeouts,
  keepalive and **`retries={"mode": "standard", "total_max_attempts": 1}`**
  asserted on the built client (`max_attempts: 1` would mean two attempts);
  no `time.sleep` in `dataprep/`; a call that cannot finish inside the
  Lambda deadline raises retryable without calling. *Covers: ASL-21–ASL-25,
  SVC-01–SVC-06; G17.*
- **AC-Z15** `[sfn]`&`[gate]` Deadlines SHALL nest: client (5 s connect,
  ≤ 30 s read) < Lambda 90 s (`STEP_LAMBDA_TIMEOUT_S`) < Task 120 s < poll
  budgets (DQ 48 × 15 s with the Glue run's own `Timeout` firing first;
  calls 20 × 30 s) < execution 10,800 s (B3.1-a). At the smoke every step's
  p99.9 must stay ≤ 55 s, else the timeout family is raised together.
  *Covers: ASL-26–ASL-29, ASL-31, GDQ-03; ASL-49, ASL-50 `[gate]`.*
- **AC-Z16** `[sfn]`&`[off]` The two Maps SHALL share one iteration
  (deep-equal states), `MaxConcurrency` 4, and the six-key envelope from
  `$.admit` (no `$$.Execution` inside the iteration): inline for ≤ 50 claims
  (`INLINE_MAP_MAX`; history budget ≤ 60 % of 25,000 events), the
  Distributed Map (STANDARD children, `ToleratedFailurePercentage` 0, Label
  `claims`, no ResultWriter, the S3 item reader on the row-gate worklist)
  for 51–200; fates are reconciled against the row-gate claims — a passed
  claim with no fate counts `claim_failed`/`no_fate` and the conservation
  gap must be 0; reserved concurrency ≥ 20 bulkheads the account (one batch
  at a time, RUN-04). *Covers: ASL-09–ASL-15, ASL-30, ASL-32, ASL-37,
  REC-15; FC-5; FA-12; G10 (offline half).*
- **AC-Z17** `[sfn]` The intake ASL SHALL pass the LLD's 33 definition
  tests: pure-ASL STANDARD JSONPath machine starting at `Admit` reading the
  raw event; every Task the one step-Lambda ARN with a §1.4 step name and a
  `ResultSelector` (except `DqCancel`); every Choice with a safe Default;
  every path into `BatchOutcome` through exactly one of the six verdict
  Passes; `batch_outcome` reading the whole top-level state; every Task's
  `Parameters` carrying `retry_count` and I/O matching `steps.STEP_CONTRACT`;
  step outputs ≤ 32 KB and the top-level state bounded. *Covers: ASL-01–
  ASL-03, ASL-05–ASL-08, ASL-33–ASL-36, ASL-48, ASL-51; §3.11 tests 1–33;
  G1.*
- **AC-Z18** `[off]` The step dispatcher SHALL enforce the step contract:
  `steps.handler` builds `Deps` once per container and dispatches on
  `event["step"]` (absent → the event-driven pair `feedback`/`batch_failed`
  by source, else `UnknownStepError`); every step returns every key its
  `STEP_CONTRACT` row names (null/[] when not applicable) and ≤ 32 KB; state
  carries keys, never content. *Covers: STP-01 (dispatch half), STP-02,
  STP-05; ASL-08, ASL-35; G47 (size half).*
- **AC-Z19** `[off]` The module layout SHALL match the component table: one
  leaf module per intake component plus exactly the eight support modules;
  `contracts.py` imports stdlib only; v1 imports only `dataprep.contracts`;
  `dataprep` imports from v1 only `metrics` and `logging_safe`, and only in
  `telemetry.py`; the seven pure modules import no boto3/botocore/clients;
  `adjuster.py` lives on the v1 side; every S3 key is built in
  `contracts.py`/`keys.py` (v1 never imports `keys`); no `bedrock` service
  name appears under `dataprep/`; the CLI is
  `python -m claim_processor.dataprep`. *Covers: MOD-01–MOD-06, MOD-08,
  KEY-02, SVC-02; G2, G3, G6 (code half).*
- **AC-Z20** `[off]` Error classification SHALL be total and singular: one
  pure `clients.classify_error` maps every exception per the LLD's §4.2
  table (retryable / expected reason code / success / deploy defect;
  specific rows win; unknown 4xx → deploy defect — an unknown error never
  becomes a flag); the reason codes are the closed SVC-11 table, each with
  one `ReasonClass`; one Stubber case per table row. *Covers: SVC-08,
  SVC-09, SVC-11; G45.*
- **AC-Z21** `[off]` The IAM surface SHALL be exactly the LLD's: five v2
  identity policies + five trust policies + two resource policies, all pure
  IAM documents with Sids, literal stable names and only the closed token
  list; no managed policy on any v2 role; **every v2 policy carries
  `DenyBedrock`**; the DQ owner is a role assumed from the deployer (no
  long-lived key), Bedrock-denied, with no AppConfig grant; each trust
  policy admits one principal; v2 commits its trust files; **v2 creates
  `claim-processor-operator`** (trust: the deployer user) at Stage V1d.
  *Covers: IAM-01–IAM-05, IAM-48, IAM-49, IAM-53, IAM-55, IAM-56, IAM-92;
  G6 (IAM half).*
- **AC-Z22** `[off]` The S3 grant matrix SHALL hold: only
  Get/Put/List(+`GetObjectVersion` for dq-owner on the intake CSV alone) —
  no delete, ACL, tagging or multipart; every `ListBucket` prefix-
  conditioned; existence checked by listing (a 403 on a granted key is a
  deploy defect); one writer per prefix **between roles** (intake →
  `transcripts/`, `processed/claims/`, `bundles/`, the `quality/` prefixes;
  glue-dq → `quality/dq-results/`; dq-owner → `quality/proposals/`; v1 →
  `results/`, `pending-review/`); dq-owner reads bundles minus the image
  copies; `states:RedriveExecution` nowhere. *Covers: IAM-06–IAM-15,
  IAM-33, IAM-50–IAM-52, IAM-84; G4.*
- **AC-Z23** `[off]` Non-S3 grants SHALL be exactly scoped: Glue by ruleset
  name/database/table (+`iam:PassRole` only for the Glue DQ role to
  `glue.amazonaws.com`); Comprehend/Textract/Transcribe-start on `*` only
  because the actions take no resource, with `GetTranscriptionJob` pinned
  to `transcription-job/clm-*`; AppConfig reads pinned per profile
  (intake → `data-quality`, v1 → `model-selection`); logs scoped to the one
  pre-created group; KMS only via-S3; the machine role's L4 trio
  (StartExecution on itself, DescribeExecution on parent-form executions,
  GetObject on the worklist) and `lambda:InvokeFunction` on the exact
  function ARN. *Covers: IAM-12, IAM-16–IAM-32, IAM-34–IAM-36, IAM-83
  (grant side).*
- **AC-Z24** `[off]`&`[gate]` Event plumbing SHALL be pinned: the events
  role's only Allow is StartExecution on the intake machine; the feedback
  and watchdog rules reach the Lambda through function-policy statements
  pinned to each rule's exact ARN; the DLQ policy admits only
  `events.amazonaws.com` for the trigger rule; SSE-SQS; no role reads the
  queue. Transcribe reads media and writes transcripts with the caller's
  permissions (no `DataAccessRoleArn`; the intake role never trusts
  `transcribe.amazonaws.com` — a contrary smoke finding forces a separate,
  flagged data-access role); the transcript's `ServerSideEncryption` is
  recorded at the smoke (B4-5-a). *Covers: IAM-38–IAM-42, IAM-44–IAM-46;
  IAM-43, IAM-47 `[gate]`.*
- **AC-Z25** `[off]` Wildcard discipline: the `Resource:"*"` Allow list is
  the closed W-01–W-06 set — a new `*` fails the lint until added with its
  reason as a **flagged** IAM change; partial wildcards are the listed,
  literal-prefixed forms only. *Covers: IAM-67, IAM-68, IAM-81.*
- **AC-Z26** `[off]` The IAM lint (`tests/test_iam_policy.py`) SHALL grow to
  the LLD's twenty rules: rglob file walking, Effect-aware checks, IAM
  wildcard semantics (product-automaton, `*` crosses `/`), no v1 Allow
  reaching a v2 resource with exactly the two SD-4 bundle-read exceptions,
  the writers/readers tables, no Bedrock in v2 / no perception in v1, the
  services allowlist, scoped-action counts, the closed `*` list, the
  no-unused-grant `ast` scan, condition checks, bucket pinning, and the
  managed-policy table (v1's `AWSLambdaBasicExecutionRole` the one known
  exception). *Covers: IAM-69–IAM-88, V1-15; G4, G5, G6, G28.*
- **AC-Z27** `[gate]` The owner's IAM gates SHALL run as the runbook stages
  fix them: the `simulate-principal-policy` matrix (IAM-89) at V1c/V1d/I1;
  the deployed function/queue policies compared statement-by-statement with
  the committed files (IAM-43); the first real runs as probes — B0003 for
  the Distributed Map grants, one Glue DQ run, one call claim, one feedback
  event, one aborted execution — each `AccessDenied` a one-line **flagged**
  ledger finding (IAM-37, IAM-90). *Covers: IAM-37, IAM-43, IAM-47, IAM-89,
  IAM-90; G20; TST-32 (IAM part).*
- **AC-Z28** `[off]` Suite discipline: one gate command (`cd build &&
  python3 -m unittest discover -s tests -t .`), no AWS and no moto (Stubber
  and fakes only; `requirements.txt` stays `boto3, botocore`);
  `test_no_new_deps.py` walks with `rglob` and grows the stdlib allowlist by
  exactly `csv`, `unicodedata`, `decimal`, `math`, `statistics`, `urllib`;
  the G-row map is data (TST-03: every G row names live evidence or the
  suite fails — CL1-a's backstop); every §10.6 case id is a test citing its
  rule id; vocabulary reachability holds (every flag family, reason code,
  info item, outcome and fate produced at least once or on the reviewed
  defensive list); new tests follow v1's style. *Covers: TST-01–TST-03,
  TST-24–TST-26, TST-31, MOD-07; G44.*
- **AC-Z29** `[off]` The corpus SHALL be deterministic and windowed: an
  injected clock (`as_of` = the pin's date; no `datetime.now()` in rules);
  the manifest pins `as_of` 2026-09-23 and `valid_until` 2027-03-01 with
  clock-dependent expectations tested at both ends; `gen_synthetic.py
  --seed 23` regenerates byte-identical files (SHA-256s in the manifest);
  the manifest is the hand-written oracle (one labelled exception: the
  pinned batch score, checked against real Glue in smoke 6); two trees —
  `s3/` uploaded, `truth/` never; synthetic values only; one seeded cause
  per row; documents are generator-drawn PNGs; the two call WAVs are
  rendered **once by the owner** with `build/tools/render_calls.py`
  (macOS `say`; C10-1-a) and committed with checked hashes — the suite
  never calls `say`. *Covers: TST-04–TST-10, TST-13, TST-14, TST-17.*
- **AC-Z30** `[off]` The e2e (`intake --fake` through v1's fake pipeline,
  feedback, propose/decide/deployed, B0002, B0003) SHALL assert TST-28's
  eleven checks — exact per-row results, 100 % per-rule recall, 0 blocking
  flags on seeded-clean claims, ≥ 3 auto-approvals in B0001, the pinned
  score, exactly one proposal, B0002's flag clearing, conservation
  everywhere, the PII scan (positive controls first, canaries nowhere
  forbidden), canonical fixed points and payload caps with lineage, and
  B0003's 51-dispatch worklist run — with the fake model reading only
  evidence (a canonical intake value never appears unless the evidence
  repeats it). *Covers: TST-11, TST-23, TST-27, TST-28, TST-29; G7 (offline),
  G9, G10.*
- **AC-Z31** `[off]`&`[gate]` The smoke corpus SHALL be exactly three
  batches inside the budget (TST-12): **B0001, 16 rows** (5 quarantined, 11
  dispatched, 4 auto-approve, 7 review; totals pinned), **B0002, 3 rows**
  (105/106 r2 review with `resubmission_review` only, 113 r2 auto-approves),
  and **B0003, 51 narrative-only rows `CLM-000301`–`CLM-000351`** — the
  Distributed Map probe (0 quarantined, 51 dispatched, all auto-approve with
  `fm_absent: [policy_number]`), run through smoke 3's stop-and-takeover
  sequence; ≤ 3 recordings of ≤ 60 s, ≤ 8 document files; a test sums the
  manifest against the budget. *Covers: TST-12, TST-18–TST-22, TST-34;
  SEQ-05.*
- **AC-Z32** `[gate]` The nine smokes SHALL run as §11 fixes them, with
  synthetic data only, comparing records through the same manifest
  (`tests/corpus_expect.py`, TST-30) and covering what only real AWS can
  show (TST-32): the happy batch (with **AC-W17's expected `AwaitReview`
  failures**), duplicate delivery, the B0003 watchdog sequence, feedback,
  the proposal loop, the Glue mapping, the IAM simulations, the first-run
  probes, and the operator dialog (smoke 9); every offline twin pins the
  current `[re-verify]` reading and names the smoke that checks it
  (TST-33). *Covers: TST-30, TST-32, TST-33; FMT-54; OBS-13.*
- **AC-Z33** `[infra]` The runbook SHALL keep the owner's rules: the agent
  never runs a mutating AWS command (RUN-01); every stage recorded in the
  ledger (RUN-02); synthetic data only until Stage A is verified (RUN-03);
  **one batch at a time** (RUN-04); token substitution with a grep check
  (RUN-05); owner-deleted `clm-*` jobs before a corpus re-run (RUN-06); DLQ
  replay and takeover re-runs, never `RedriveExecution` (RUN-07); uploads
  with `aws s3 cp` to the full key, raw files first, CSV last — **never a
  console folder** (RUN-08); the stage order V1a→…→E2 with the trigger
  last and V1-22's precondition; rollback = disable the trigger first.
  `build/DEPLOY-V2.md` is written from §11 **at v1-walkthrough depth**
  (DW-a): per stage the exact action, expected result, verification check,
  reasoning, and a ledger entry. *Covers: RUN-01–RUN-08, §11's stage and
  smoke tables, V1-22.*
- **AC-Z34** `[off]` Hand-off names SHALL be idempotent: the v1 input is
  the canonically-serialized `{bucket, key, version_id}`; the v1 execution
  name `claim-<claim_id>-r<rev>` (`ExecutionAlreadyExists` → fate
  `already_started`; a takeover never re-dispatches); the dispatch marker is
  written create-only after the start, and `claim_check` skips a marked
  revision with no AI call; intake executions are named by EventBridge, and
  Admit and the watchdog share `contracts.parse_intake_key` so the loose
  trigger pattern admits nothing KEY-06 rejects (tightened after the first
  real event). *Covers: EVT-01, EVT-02, EVT-05, EVT-06, REC-13, ASL-39; FC-1–FC-3, FC-6
  (recovery half); G16, G31 (naming half), G40 (dispatch half).*
- **AC-Z35** `[off]` The fakes SHALL run the production path: one fake per
  service with boto3 method names, request params and response shapes,
  raising real `ClientError` codes through `classify_error`; deterministic
  (no clock, no randomness; triggers live in the synthetic data); the fake
  driver walks the ASL's states, Parameters, ResultSelectors and Catch
  outputs, proven by a parity test against `sfn/intake-asl.json`; Stubber
  tests pin every request shape per the LLD's table. *Covers: SVC-14,
  SVC-15, SVC-16, TST-15, TST-16.*
- **AC-Z36** `[off]` The happy path SHALL leave exactly the LLD's artifact
  set: every execution ends as `DuplicateBatch`, `Done` (join record
  written), or a watchdog-recorded crash; B0001 under fakes produces exactly
  one lock, one pin, one partition, one DQ run, 11 markers, the per-claim
  records/bundles/dispatch markers, 11 v1 starts, one join record (gap 0),
  one quarantine record, one themes record; the per-claim order is fixed
  (`ClaimCheck` → `Sources` → `Assemble` → `Dispatch`); intake never waits
  for v1; uploads are manifest-last. *Covers: SEQ-01–SEQ-03, SEQ-05–SEQ-07;
  FC-1.*
- **AC-Z37** `[off]`&`[infra]` **The CI hook (CL4-a, validation
  intersection #4):** the repo SHALL carry `build/tools/pre-commit.sh`
  running the offline suite and the lints (IAM, ASL, DQDL golden,
  no-new-deps) with a non-zero exit on any failure; the owner installs it as
  the git pre-commit hook (`[owner]` task; no hosted CI, no Claude hook
  config); the build's worktree merge protocol invokes the same script as
  the merge gate. *Covers: the HLD hand-off's CI-hook item; G1–G49's
  "manual runs only" gap.*

---

## 5. Coverage ledger

### 5.1 Rule families → criteria

Every LLD rule id is covered by at least one criterion below, or listed as
design-only in §5.3. The per-rule detail is each criterion's "Covers:" line;
this table is the roll-up the Stage-4 analyze checks.

| Family (count) | Criteria |
|---|---|
| MOD 1–8 | Z19; W13 (MOD-02), Z28 (MOD-07) |
| STP 1–7 | Z11, Z18; S16 (STP-03, STP-07) |
| V1 1–23 | W8–W16 |
| KEY 1–7 | S9 (01, 06), S15 (05), Z19 (02), V8 (03, 04), W14 (07) |
| CSV 1–6 | S9 (01, 02), S15 (03–06) |
| CAT 1–15 | S13 (01–06), S9 (07), S10 (08–10, 13), S11 (11, 14, 15), S14 (12) |
| FLG 1–3 | V17 |
| REC 1–29 | T7/U22 (01), T8 (02), T10 (03), T14 (04), T9/V7 (05), S12 (06–10), X10/Z34 (11–13), S16 (14), S11/Z16 (15), S11/Z13 (16), S11 (17), S9 (18), X7 (19–22, 27), X8/X9 (23–26, 28, 29) |
| BUN 1–10 | V8 (01, 08, 09), V9 (02, 03), V12/W11 (04), V10 (05, 07), V11 (06, 10) |
| EVT 1–10 | Z34 (01, 02, 05, 06), U18 (03), S12 (04, 10), Z13 (07–09) |
| ASL 1–52 | Z17 (01–03, 05–08, 33–36, 48, 51), Z11 (04, 52), Z16 (09–15, 30, 32, 37), Z12 (16–20), Z14 (21–25), Z15 (26–29, 31, 49, 50), S12 (38, 40), Z34 (39), Z13 (41–44), S9 (45–47) |
| SVC 1–16 | Z14 (01–06), Y6 (07), Z20 (08, 09, 11), Z11 (10), U13 (12), U24 (13), Z35 (14–16) |
| CMP 1–20 | T11 (01–05), T10 (06–08), T8 (09, 10), T12 (11, 12), T14 (13–16), T9 (17), U23 (18–20) |
| TXT 1–12 | U13 (02, 03), U14 (01, 04–06), U15 (07, 08, 12), U16 (09–11) |
| TRN 1–12 | U17 (01), U18 (02–04, 06), U19 (05, 12), U20 (07–09), U21 (10, 11) |
| GDQ 1–11 | S14 (01–04, 10), S10 (05–08), S9 (09); GDQ-11 design-only |
| FMT 1–54 | V12 (01–04, 06, 11–17), V10 (05, 17), T9 (07), V13 (08), V14 (09, 10), V15 (18–23), V11 (24–26), W11 (27–30, 33, 34, 40–42), W8 (31), W12 (32), W13 (35–39), V16 (43–53), Z32 (54) |
| IAM 1–92 | Z21 (01–05, 48, 49, 53, 55, 56, 92), Z22 (06–15, 33, 50–52, 84), Z23 (12, 16–32, 34–36, 83), Z24 (38–47), Z25 (67, 68, 81), Z26 (66, 69–88), Z27 (37, 43, 47, 89, 90), W15 (57–65, 91); IAM-54 design-only |
| OBS 1–28 | Y4 (01, 02, 06–12), Y5 (03, 04), Y6 (14–19, 21), Y9 (05, 20, 22, 23), Y7 (24–27), Y8 (28), Y10 (13) |
| CFG 1–10 | S17 (01–03), S16 (04, 07, 08), S9 (05, 06), X8 (09, 10) |
| SEQ 1–30 | Z36 (01–03, 05–07), S11 (04, 08, 10, 11), S12 (09, 18–20), Z12 (12, 13, 15), U24 (14), X10 (16, 24, 25, 30), Z11 (17), Z13 (21–23), X7 (26), X8 (27), X9 (28, 29) |
| TST 1–34 | Z28 (01–03, 24–26, 31), Z29 (04–10, 13, 14, 17), Z30 (11, 23, 27–29), Z31 (12, 18–22, 34), Z32 (30, 32, 33), Z35 (15, 16) |
| RUN 1–8 | Z33 |
| Image rows I1–I8/I3a, vectors N1/N2 | V11, V13 |

### 5.2 Failure-flow rows (LLD §9.10) → criteria

| Table | Rows → criteria |
|---|---|
| FB (batch) | S12 (1, 2), S9 (3–11), S10 (12–16), S11 (17, 19), Z13 (18) |
| FC (claim) | Z34 (1–3, 6), Z12 (4, 7), Z16 (5), S11 (8), X10 (9) |
| FF (flags) | S11 (1), X10 (2), T7/U13/U17 (3), U19 (4), Z12 (5), U24 (6), T12/T13 (7), U22 (8), V7 (9), V11 (10) |
| FV (v1) | W8 (1–4, 10, 11), W12 (5, 6), W9 (7, 8), W10 (9), **W17 (12)** |
| FA (async) | Z13 (1, 2, 8), X7 (3, 4), Z12 (5, 6), Z11 (7), U20/V11 (9), X10 (10), Y5 (11), Z16 (12) |

### 5.3 Design-only rules (no criterion; reason)

| Rule | Why design-only |
|---|---|
| GDQ-11 `[infra]` | A cost note: workers × timeout cap the DPU bill; the owner prices it (no prices in the LLD or here). |
| IAM-54 `[off]` | A go-live governance statement: where the DQ-owner CLI may run is the named reviewer's decision before real data, not a testable build fact. Its IAM half is covered by Z21/Z22. |
| LLD §3.13, §6.13, §6.14, §9.12, A.*, B.* | Owner-decision records and rationale, not rules. |

### 5.4 G rows (CL1-a)

G1–G49 map to tasks, not to spec criteria: the tasks file carries a per-task
"G rows" column, and AC-Z28's TST-03 coverage test enforces the map at run
time. Criteria above cite a G row only where they restate it directly.

## 6. Facts carried verbatim (handover §5 — easy to lose)

| Fact | Where it binds |
|---|---|
| Intake clients: `total_max_attempts: 1` (`max_attempts: 1` means two attempts) | AC-Z14 |
| Documents: PNG and JPEG only | AC-U13 |
| Calls: 16-bit PCM WAV only, ≤ 600 s by the header | AC-U17 |
| Smoke batches: B0001 (16 rows), B0002 (3), B0003 (51 narrative-only, `CLM-000301`–`CLM-000351`, the Distributed Map probe via smoke 3's stop-and-takeover) | AC-Z31, AC-Z32 |
| v2 creates v1's `operator` role for `ask` (Stage V1d, smoke 9, IAM-91, IAM-92) | AC-W13, AC-Z21 |
| STP-06's eight environment variables checked at cold start | AC-Z11 |
| A deploy defect fails the execution and never becomes a flag — including an unknown `step` | AC-Z11 |
| One batch at a time (RUN-04); no logging from the intake state machine (B6-1 = b); never create folders in the S3 console (RUN-08) | AC-Z33, AC-Y9 |
| Until F2 ships, review-bound v1 executions fail at `AwaitReview`: the smokes expect 7 in B0001 and 2 in B0002 | AC-W17, AC-Z32 |

## 7. Hand-off to the tasks file (LY-b)

Approved criteria flow into `../plans/claim-processor-data-prep.tasks.md`,
which owns (→ `TASKS-OK`):

- the **WV-a waves** (0 contracts/scaffolding · 1 batch level · 2 per-claim
  sources · 3 the v1 side and the loop · 4 corpus/e2e/deploy assets · 5 the
  owner's manual deploy);
- the **PW-a worktree plan**: one worktree per parallel track within a wave,
  each track file-disjoint (named branch, owned tasks, writable files,
  dependencies, its slice of the suite), with the merge-back protocol —
  merge order, the gate green at every merge (the full offline suite + the
  lints via AC-Z37's script), the next wave branching only from a fully
  merged, green integration branch;
- the **1:1 map**: every criterion above → at least one task's pass/fail
  check; every task → its criteria; the **G-rows column** (CL1-a) with
  TST-03 as the backstop;
- the **`[owner]` tasks** (CL3-a): rendering the two WAVs (AC-Z29),
  installing the pre-commit hook (AC-Z37), and all of Wave 5 — each blocking
  only its dependents;
- the **DW-a walkthrough task**: `build/DEPLOY-V2.md` written from LLD §11
  at v1-walkthrough depth (AC-Z33), plus the ledger's v2 section.

## 8. Human gate

- **`SPEC-OK`** approves §§0–6 as the acceptance contract. Until it is
  given: no tasks file, no code, no data, no AWS calls.
- After `SPEC-OK`, the tasks file is drafted per §7 and waits for
  **`TASKS-OK`**.
- The Stage-4 analyze (spec ↔ tasks ↔ constitution ↔ the frozen A–R
  invariants; grounding of every path and API; no new dependency; both
  baselines green) runs before `TASKS-OK` is requested.
- Records on approval: this banner's status flips to APPROVED, and
  `../adrs/log.md` gets the approval entry. No ADR changes are proposed by
  this revision; any build-time gap becomes an LLD erratum with its own OK.

### Status log

| Date | Event |
|---|---|
| 2026-09-23 | Draft spec written (pre-LLD); put ON HOLD by the owner's sequence (HLD → LLD → spec). |
| 2026-09-24 | LLD FINAL, signed off. Framing confirmed: LY-b, EA-a, WV-a, PW-a, DW-a. Clarify pass: CL1-a, CL2-a, CL3-a, CL4-a, CL5-a. |
| 2026-09-24 | This revision: criteria re-derived from the LLD (88 new criteria S9–Z37, §3 disposition of the 59 draft ACs). |
| 2026-09-24 | **`SPEC-OK`** given by the owner. Tasks file (`../plans/claim-processor-data-prep.tasks.md`) drafted per §7. |
| 2026-09-24 | **`TASKS-OK`** given (LY-b kept). Stages 2–4 complete; the build (sdd-implement, waves DP-30…DP-75) runs in a fresh session. |

