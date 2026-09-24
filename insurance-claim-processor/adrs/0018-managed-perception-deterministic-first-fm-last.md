# ADR 0018. Read claims with managed AI services, check facts with deterministic code, reserve the FM for judgment

## Status
Accepted — 2026-09-23 (ratified as recommended; amendments below). Formerly: Proposed. Extends ADR 0006 (it realizes the Textract "production promote" for
documents; vision-FM-direct stays for images). Related: 0019, 0020, 0021.

## Context
v2 needs:
- entities, key phrases, sentiment, PII and language on narratives;
- OCR plus key fields on police reports and repair estimates;
- transcription of first-notice-of-loss (FNOL) calls;
- a loss-run table → text;
- batch themes.

C3-a fixes the service family: Glue DQ, Comprehend, Textract, Transcribe,
Lambda — no SageMaker, no Rekognition. Custom models (Comprehend custom
entities, Textract adapters, Transcribe custom language models) need **labeled
training data we do not have**. That is the same standalone knockout as
fine-tuning (`../assess/capability-brief.md` v2 §2).

The scored matrices are in capability-brief v2 §3–§4:
- **N2 NLP:** Comprehend vs Claude-in-the-extraction-call vs the Guardrail PII
  filter.
- **N3 documents:** Textract QUERIES (+ images to Claude) vs Claude vision only
  vs Bedrock Data Automation vs Textract AnalyzeExpense.
- **N4 calls:** Transcribe standard + redaction vs Call Analytics.
- **N5 table → text:** deterministic template vs FM summary.
- **N7 themes:** aggregation vs topic modeling vs FM clustering.

## Decision
We will follow a **deterministic-first, FM-last** principle:
1. Managed services *read*.
2. Deterministic code *checks and summarizes numbers*.
3. The foundation model is reserved for *judgment over the resulting
   evidence*: multimodal extraction, the adjuster-facing summary and the
   dialog.

Service picks:
- **Comprehend** sync APIs (`DetectPiiEntities`, `DetectEntities`,
  `DetectKeyPhrases`, `BatchDetectSentiment`, `DetectDominantLanguage`),
  chunked to the documented limits (5 KB sentiment, 100 KB others).
- **Textract `AnalyzeDocument` with QUERIES** for both document types. Answers
  carry confidence; below 80 they are never a reconciliation source.
  **AND** the page images go to Claude. OCR gives confidence-gated facts;
  vision gives holistic reading.
- **Transcribe standard batch** with `ContentRedaction` (redacted output only).
- A **deterministic Lambda template** for the loss-run summary.
- **Aggregation** of Comprehend output for batch themes.
- **Glue DQ** for the batch gate (ADR 0019).

This ADR also records two rules:
- **Sentiment is context, never a decision input.** No routing,
  reconciliation or priority function reads it; it is not rendered into
  extraction or summary prompts. It is kept only in the bundle record, for
  adjuster empathy. Why: dialect bias in sentiment models, and an upset
  claimant is not a riskier claim.
- **The transcript is context, not a reconciliation source.** ASR errors on
  accents or noise must not create mismatches.

Justification:
- **Technical:**
  - **Privacy.** NLP inside the FM would show raw PII to the model before
    anything could redact it.
  - **Auditability.** Calibrated scores and confidences are recordable; "the
    model said so" is not.
  - **Integrity.** Numbers in an SIU-relevant summary must come from code, not
    generation.
  - **Testability.** Every call site is Stubber-able.
- **Business:** per-unit pricing that scales with the sources present
  (**[re-verify]** all figures); no idle compute; the named services match the
  assignment's learning goals.

## Consequences
**Good:**
- Each fact carries its source, confidence and service.
- The FM sees redacted text plus images.
- Deterministic outputs are golden-testable.
- Each service is replaceable behind its reader component.

**Bad / accepted:**
- Four services' quotas to watch. Textract's default TPS is the tightest
  **[re-verify per region]**, which is why Map concurrency is 4 and retries are
  jittered (ADR 0016).
- Two reads of each document (OCR + vision) cost more than one. The lever is
  now the M6 image rule (ADR 0020): an image is sent only when OCR confidence
  is insufficient.
- Comprehend's fixed entity types miss domain IDs (VIN, policy number). The
  canonicalizer handles those.

**Losers:**
- *FM-for-everything:* privacy + auditability.
- *Bedrock Data Automation:* not a named service. Deferred as a future
  consolidation ADR (D-D) that could replace three services.
- *Call Analytics:* cost for the PoC **[re-verify]**. It is the upgrade path
  (native turn sentiment and issues).
- *FM loss-run summary:* integrity (hallucinated counts).
- *Topic modeling:* feasibility at 16 rows.
- *SageMaker Processing / Rekognition:* excluded by C3-a (idle cost and
  redundancy).

## Compliance
Offline fitness:
- Stubber contract tests per call site, including chunking at 5 KB / 100 KB
  and the 25-document batch limit.
- **Bias guard** (AST rule): `routing.py`, `reconcile.py` and the prompt
  renderers never reference `sentiment`.
- Golden-text test for the loss-run summary (same input → byte-identical).
- The transcript is not in reconciliation's source list (unit).
- Low-confidence OCR answers are excluded from reconciliation (unit).

`[gate]`: the smoke records per-service usage, feeding the cost envelope
(spec AC-Z10).

## Amendments ratified 2026-09-23 (risk storm, `../risk/risk-storm-v2-data-prep.md` §5)
- **M4** unverifiable is not clean: blocking `recon_unverifiable:<field>`, `source_disabled:<src>`, `history_failed`, `history_unavailable`; loss-run join keys and dates through Canonicalize Values.

Detailed EARS criteria land in the spec revision (R10).

## Notes
Author: arch-decide (v2 HLD, provisional batch A2-a)
Approved by / date: Rajnish Khatri / 2026-09-23 ("ratify as recommended")
Superseded date:
Last modified: 2026-09-23 / new
