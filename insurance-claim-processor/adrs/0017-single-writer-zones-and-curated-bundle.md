# ADR 0017. Keep claim data in single-writer S3 zones and hand v1 a self-contained, versioned bundle

## Status
Accepted — 2026-09-23 (ratified as recommended; amendments below). Formerly: Proposed. Related: 0016 (placement), 0020 (IAM / PII).

## Context
v2 adds several things to the one versioned SSE-KMS bucket
(`../build/DEPLOY-LEDGER.md` Stage 1):
- raw, PII-dense artifacts (narratives, call audio, police reports);
- a Glue-catalogued intake table;
- per-source processed records;
- a DQ plane (locks, results, quarantine, feedback, proposals);
- the FM-ready package v1 must read.

The flow is still document-in, document-out, so the "one relational DB"
default is challenged again (`../worksheets/style-decision.md` v2 D2).

Forces:
- **Auditability:** lineage must point at immutable versions.
- **Privacy:** the Bedrock-calling role should not be able to read raw PII
  (ADR 0020).
- **Reliability:** EventBridge delivers at least once, with target retries for
  up to 24 h (Idempotency C9 verified table).
- **Evolvability:** the v2 → v1 contract must survive a future quantum split
  (ADR 0016).

Alternatives:
- **Store:** S3 zones vs a relational database vs DynamoDB for state.
- **v1 image access:** (i) v1 reads images from `raw/claims/*`; (ii) a
  suffix-scoped IAM pattern `raw/claims/*.png`; (iii) **copy the needed images
  into the bundle zone**.
- **Batch dedup:** a DynamoDB conditional write vs an **S3 conditional put**
  (`IfNoneMatch` / `IfMatch`, both verified in botocore).
- **Ingestion:** an S3 drop zone vs an upload API (presigned URLs) vs SFTP.

## Decision
We will organize claim data as **single-writer S3 zones**: every prefix has
exactly one writing component, and readers use only published contracts. v1
receives a **self-contained, versioned bundle** at `bundles/<claim_id>`
(`schema_version 2.x`). The images the FM needs are copied beside it
(`bundles/<claim_id>/img-N.<ext>`), so v1 reads the curated zone and nothing
else.

Justification first:
- **Technical:**
  - Single-writer ownership removes write–write coupling.
  - A self-contained bundle is a claim-check the decision plane can replay
    alone.
  - Lineage records S3 version ids, not just keys.
  - Copying images (a tiny `CopyObject`) is what lets v1's role lose all access
    to raw PII (ADR 0020). It also keeps v1 independent of raw-zone naming.
- **Business:** audit defensibility (every fact → source version), and a
  cheaper future split: moving the bundle zone to its own bucket changes one
  IAM statement.

Zones (writer → readers):
- `intake/batch_id=<id>/` (upstream → intake; Glue table
  `claim_processor_dq.claims_intake`);
- `raw/claims/<id>/` (upstream → intake only);
- `history/` (upstream → intake);
- `transcripts/` (Transcribe → intake);
- `processed/claims/<id>/` (the owning source component → Assemble);
- `bundles/` (Assemble → v1, adjuster Q&A);
- `results/`, `pending-review/` (v1 → the feedback component, via the §7
  contract);
- `quality/{locks,dq-results,quarantine,themes,feedback,proposals}/` (one
  intake component per prefix → intake ops, DQ owner).

This ADR also records:
- **Ingestion contract (PoC):** an S3 **drop zone with manifest-last commit**.
  Attachments are written first, the intake CSV last; the CSV's
  `Object Created` event is the only trigger (EventBridge wildcard
  `intake/*.csv`).
- **Batch lock with takeover:** `quality/locks/<batch_id>` via `PutObject
  IfNoneMatch="*"`, with the body `{execution_arn, started_at}`. A duplicate
  that finds the holder FAILED, TIMED_OUT or ABORTED takes over with `IfMatch`
  on the lock's ETag. Lock objects never expire; that outlives EventBridge's
  24 h redelivery.
- **Contract versioning:** the bundle carries `schema_version`. v1 is a
  tolerant reader of `2.x`; an unknown major raises `BundleError` and the
  execution fails visibly.

**Deferred** (each with its unlock):
- A production upload API or SFTP for partners — unlock: partner onboarding
  requirements.
- Retention periods for raw audio and narratives vs claim records (S3
  lifecycle, legal hold) — unlock: records-retention policy (`needs-input`).
  This is the likeliest ADR 0016 split trigger.
- Athena over `quality/` for intake-ops queries — unlock: quarantine volume
  that S3 listing cannot serve.

## Consequences
**Good:**
- A clear, reviewable IAM scope per role; v1 cannot read raw PII.
- Bundles are replayable in isolation.
- Duplicates are harmless (lock, overwrite keys).
- No database to operate.

**Bad / accepted:**
- Image bytes are duplicated per bundle revision (small; versioned bucket
  history grows).
- Querying quarantine or proposals needs S3 listing until Athena.
- Manifest-last is a *convention* upstream must follow. An out-of-order upload
  surfaces as `document_failed` / `narrative_invalid` flags, not silent data
  loss.

**Losers:**
- A relational database: operations and schema for no query need.
- DynamoDB locks: a second service where S3 conditional puts suffice.
- Raw-zone reads by v1: violates the privacy separation.
- A suffix-scoped raw pattern: cheaper, but the zone boundary stays implicit
  and v1 stays coupled to raw naming.

## Compliance
Offline fitness:
- **IAM lint:** v1's role has `s3:GetObject` on `bundles/*` only among the new
  prefixes; no role writes a prefix owned by another component (a
  prefix-ownership table in the test).
- **Bundle:** every source entry carries an S3 version id in `lineage`, and a
  schema-version test covers the tolerant reader.
- **Stubber:** lock 412 → `duplicate_batch`; a FAILED holder → takeover; a
  racing takeover gets 412.

`[gate]`: the smoke shows v1's role denied on `raw/claims/*`
(simulate-principal-policy), as in the v1 ledger's Stage 4 practice.

## Amendments ratified 2026-09-23 (risk storm, `../risk/risk-storm-v2-data-prep.md` §5)
- **M3 (keys/contract)** attachment keys confined to `raw/claims/<claim_id>/`; intake contract version in the key path (`intake/v=1/…`).
- **M9** quarantine and feedback records hold no values (row index + rule ids + object version); `dq propose` runs S3-side only.
- **M12** revision-scoped keys (`bundles/<id>/r<rev>`, `processed/claims/<id>/r<rev>/…`); v1 result/pending keys follow the bundle key; S3 VersionId travels in the v1 input and lineage.
- **M13** lock correctness: holder ARN == `$$.Execution.Id` → self-retry proceeds; `states:DescribeExecution` on intake executions; `CreatePartition` AlreadyExists = success.

Detailed EARS criteria land in the spec revision (R10).

## Notes
Author: arch-decide (v2 HLD, provisional batch A2-a)
Approved by / date: Rajnish Khatri / 2026-09-23 ("ratify as recommended")
Superseded date:
Last modified: 2026-09-23 / new
