# Risk storm — v2 data-preparation plane (2026-09-23)

**GATE: RATIFIED 2026-09-23 ("ratify as recommended" — design/hld-v2-data-prep.md §6; was PENDING HUMAN)** (provisional batch, A2-a). You play two roles here:
- **arbiter** in phase 2: your domain knowledge can overrule any consensus
  cell;
- **business stakeholder** in phase 3: accept, reject, or ask for a cheaper
  version of each priced mitigation.

**Outcome (2026-09-23):**
- Medians kept (dissents noted).
- **All mitigation packages accepted** (must-have + should-have + hygiene;
  M11 → v1).
- **D0 executed first** and is closed, including F14 (see the §0 outcome).
- **L-1 re-verified** against current AWS docs and stays at 9 until the
  opt-out is in place. M7 was decided as **R8c-a**: opt out of all AI services;
  the owner performs it.
- New from F14 (**H-F14-a**): v2 images are not guardrail-checked. No change
  from today, since the guardrail checks no images. M1 carries integrity.

**Input diagrams:** `../validate/diagrams-v2/02-container.svg` +
`03-component-intake.svg` (linted), plus the v2 addenda and ADRs 0016–0022.
**Mode:** review, design-time for v2. The **live v1** code and ASL were
examined where v2 depends on them, which surfaced the **D0** items (§0).

## 0. BLOCKING — live v1 defects (D0: they outrank all v2 work)

The storm found two defects in the **deployed** v1 system (ledger Stage 9,
2026-09-22). The facilitator verified both against the repo. Both fail
**safe**: nothing auto-approves wrongly. But claims on these paths end
**undecided**, and one privacy control is missing.

| Id | Defect (verified) | Effect on real AWS | I × L | Fix | Effort |
|---|---|---|---|---|---|
| **D0-a** | **None of the 6 `Catch` blocks in `../build/sfn/asl.json` sets `ResultPath`.** In ASL a Catcher without `ResultPath` defaults to `$`, so the error object `{Error, Cause}` replaces the whole state input. Affected: UnderstandExtract→DegradedExtract, RetrieveSummarize→UngroundedFallback, AwaitReview→ExpireReview, and 3 × → ExecutionTimedOut. | **Throttle brownout:** DegradedExtract gets no `bucket`/`key` → `KeyError` at `handler.py:73` → the execution fails, so AC-P1's "degrade, don't fail" is broken. **Policy lookup (RAG) failure:** UngroundedFallback's `$.bucket` does not resolve → `States.Runtime`, so the C11 path (AC-G2) is broken. **HITL timeout:** ExpireReview → Record `KeyError` at `handler.py:136`, so AC-E4 is broken. Only the auto-approve path has run live, so this is untested. The offline tests check each Catch *target*, never the data flow (`tests/test_asl.py`, `test_asl_resilience.py`). | 3 × 3 = **9** | Add `"ResultPath": "$.error"` to every Catcher. Add an offline ASL **data-flow** test: any Catcher whose next state reads `$.` paths must set a non-root `ResultPath`, and every `Parameters` path must exist on the incoming shape. Redeploy the definition (one `update-state-machine`). | ~0.25 d + 1 interactive deploy step |
| **D0-b** | **The summary Converse call passes no `guardrailConfig`** (`../build/claim_processor/pipeline.py:423-428`; only the extract path sets it, `:185,200`). That violates v1 AC-A5 ("every converse call SHALL include guardrailConfig"). | Summary output is not guardrail-masked. The validator regex still sends dashed SSNs and card numbers in the summary to review, but other PII types pass. | 3 × 2 = **6** | Pass `guardrail_config` on the summary call. Add a regression test: every `converse` call carries `guardrailConfig` when a guardrail id is set. Redeploy the Lambda code. | ~0.25 d + redeploy |

**§0 outcome (2026-09-23, `../build/DEPLOY-LEDGER.md` "Hotfix R0"):** D0-a **fixed, deployed, and TestState-proven on real AWS**. D0-b **fixed and deployed** — which exposed **F14**: the guardrail's prompt-attack filter (HIGH) blocks our own summary instructions (ApplyGuardrail: PROMPT_ATTACK, LOW confidence, BLOCKED), so clean claims now route to review (fail-safe). **F14 fixed the same day** (option F14-a, input tagging: only claim-derived text is guarded input; ADR 0008 amendment, v1 AC-A5a). Smoke #3 auto-approved on real AWS, and an injected claim is still blocked (`../build/DEPLOY-LEDGER.md` "Fix F14"). **D0 is closed.**

These are **v1 fixes**, routed to the v1 owner, and they should land **before
v2 work starts**. v2 would send *more* claims down exactly these degraded and
review paths.

## 1. Frame

- **Contexts:**
  - **X1** admission & quality gates;
  - **X2** source extraction;
  - **X3** reconcile, format & bundle;
  - **X4** decision integration (v1 side);
  - **X5** feedback & governance.
- **Passes stormed (one criterion each):** **P1 data integrity (inputs)** and
  **P2 privacy**.
- **Queued passes:** P3 auditability, P4 reliability (partly surfaced anyway,
  §3 C-7), P5 cost.
- **Participants.** All wrote blind; the facilitator's sheet was written to a
  scratch file before any lens output was read:
  - **F**, facilitator / architect;
  - **DQ**, data engineering;
  - **SEC**, security & data protection;
  - **OPS**, operations / SRE;
  - **FM**, implementation & model behavior.
- **Honesty note.** The lenses are the same model with different lens
  prompts: **coverage of different risk dimensions, not independent votes**.
  Agent consensus is not evidence; you arbitrate.

## 2. Matrix (median of 5 sheets; per-lens products visible)

Scale: 1–2 low, 3–4 medium, 6–9 **high**. Direction: **new** (the first v2
assessment). Sheet order: F / DQ / SEC / OPS / FM.

| Criterion \ context | X1 gates | X2 sources | X3 reconcile/format/bundle | X4 v1 integration | X5 feedback | **Row sum** |
|---|---|---|---|---|---|---|
| **P1 integrity** | **6** (6/6/6/6/6) | **6** (F4→6/6/6/6/6) | **6** (F6→9/9/6/4/6) | **6** (6/6/6/6/9) | **6** (F3→6/6/6/6/6) | **30** |
| **P2 privacy** | 4 (F2→4/6/4/2/3) | **6** (6/6/6/6/6) | **6** (6/6/6/6/6) | 3 (F2→3/3/3/6/4) | 2 (2/4/2/2/2) | **21** |
| **Column sum** | 10 | 12 | 12 | 9 | 8 | |

**Ranking:**
- Criteria: integrity (30) ≫ privacy (21).
- Contexts: X2 = X3 (12) > X1 (10) > X4 (9) > X5 (8).
- **Every** integrity context is HIGH: v2's reason to exist is also its
  thinnest area.

**Dissents for your arbitration:**
- **P1-X3:** F and DQ argue **9**. Single-source dates are the norm in real
  claim files, and every source runs through one parser keyed on the claim
  channel.
- **P1-X4:** FM argues **9**. There is no control at all between FM output and
  routing.
- **P2-X4:** OPS argues **6**. The v1 role still reads `claims/*` (the legacy
  path) and the spec's AC-W7 grants `raw/claims/*`, so the IAM separation is a
  convention.

## 3. Consensus log (phase 2)

**Facilitator movement** (initial → final; evidence-cited, so no anchoring and
no instant collapse; the lenses were one-shot):

| Cell | F initial → final | What moved it |
|---|---|---|
| P1-X2 | 4 → 6 | SEC: a low-confidence OCR total drops the only third-party amount check, with only an info flag. DQ / FM: loss-run lookups bypass the canonicalizer, so a mismatch renders as "No prior claims" and silently suppresses `history_frequency_high`. |
| P1-X3 | 6 → 9 | DQ: every source goes through one parser keyed on the channel, so errors are correlated. Single-source fields raise no flag, and the corpus never exercises the failure. |
| P1-X5 | 3 → 6 | SEC: `revision` is controlled upstream, so a claim can be re-rolled. DQ / OPS / FM: replay scores only the supporting claims; `channel` ≠ partner. |
| P2-X1 | 2 → 4 | DQ / SEC: structured rows bypass every redaction layer; quarantine records keep raw values. |
| P2-X4 | 2 → 3 | SEC / DQ / OPS: spec AC-W7 contradicts SD-4; v1's `sfn-exec.json:8` wildcard covers the new Lambda. |

**Convergent finds (several lenses independently; the strongest evidence here):**

- **C-1 (P1-X4): routing trusts the FM, not the canonical intake.** Found by
  **4 of 5** lenses (DQ, SEC, OPS lone #3, FM).
  - `routing.py:57-59` gates on the FM-extracted `claim_amount`. Nothing
    compares FM output with `intake.normalized` before routing.
    Reconciliation runs **before** the model; agreement is measured only
    **after** the record is written.
  - FM adds: RAG scope for a bundle is a substring guess over the concatenated
    text (`rag.py:99-106`), not the canonical jurisdiction / line of business.
  - → The "manipulated field → `recon_mismatch`" defense was **monitoring
    mistaken for a gate**. Corrected in ADR 0021 and design §9.4.1 (needs M1).
- **C-2 (P1-X1): gate evaluation differs.** Found by F, DQ, FM.
  OpenCSVSerde yields `''`, not NULL (`IsComplete` passes it); Spark maps by
  position and skips the header unchecked; the twin maps by name. A day ≤ 12
  date that parses under the channel order counts only as `normalized:*` info.
  - → "Semantically equal by construction" holds for rule *definitions* only.
- **C-3 (P2-X3): document images carry PII into `bundles/` and Bedrock.** All
  5 lenses. OPS: the image is sent even when Layer 2 has just found an SSN in
  *that document's* OCR text.
  - → Corrected in ADR 0020: "IAM impossibility" is false for images.
- **C-4 (P1-X5 / audit): keys are per claim, not per revision.** Found by OPS
  lone #1, FM lone #2, SEC.
  - `bundles/<id>`, `processed/claims/<id>/*`, `results/bundles/<id>.json` and
    `pending-review/bundles/<id>.json` are all per claim (`pipeline.py:40-42`,
    `store.py:16-18`), and v1's input carries no S3 VersionId.
  - Revision *r*'s late review (up to 7 days) overwrites revision *r+1*'s
    decision, and feedback pairs *r*'s FM output with *r+1*'s bundle.
- **C-5 (P1-X2): a disabled or failed source is silent.** Found by OPS, SEC,
  DQ. A kill-switched source, a failed history lookup or low-confidence OCR
  produces **no blocking flag** (there is no `source_disabled:*` or
  `history_failed`; `low_confidence_ocr` is info), so the claim loses its only
  cross-check and can still auto-approve.
- **C-6 (X1 reliability): the lock cannot tell its own retry from a
  duplicate.** Found by FM lone #3, OPS.
  - A lock write that succeeded but lost its response is retried, hits 412 on
    its *own* lock, and ends as `duplicate_batch` with no summary.
  - Takeover needs `states:DescribeExecution`, which is not granted.
  - `CreatePartition` is not idempotent (`AlreadyExistsException`).
- **C-7 (reliability, outside P1/P2): the batch's health report is written by
  the execution it reports on.** OPS lone #2:
  - `States.Runtime` and `States.DataLimitExceeded` are uncaught.
  - The 25,000-event inline-Map history limit vs Transcribe polling (~9 events
    per iteration) caps a 200-row batch at ~9 polls per claim.
  - **Reserved concurrency 10 < 16** concurrent branch invocations (4 claims ×
    4 sources) — **a facilitator knob error, now corrected in the clinic**.
  - No DLQ on the EventBridge target; no alarm on intake execution failure.
  - The 16-row smoke cannot reveal any of it.
- **C-8 (X1 integrity): three manual channels, no version pin.** OPS. The
  Glue ruleset, the zip and the `data-quality` AppConfig version ship
  separately. A ConfigProvider fallback to the bundled default silently
  **reverts an approved fix** (for example DMY for a partner).

**Lone identifications (one lens each):**

| Id | Lens | Risk | I × L |
|---|---|---|---|
| L-1 | SEC | **AI-services content use.** Comprehend, Textract and Transcribe may store and use content to improve the service unless an AWS Organizations **AI-services opt-out policy** exists (no Organization in the ledger). Bedrock is not affected. **[re-verify current Service Terms]** | 3 × 3 = **9** |
| L-2 | SEC | **v1 wildcards reach v2.** `sfn-exec.json:8` can invoke `claim-processor-intake-step`. `remediation.json:5-19` lets the *automated* remediation Lambda deploy **any** AppConfig profile, including `data-quality`, which breaks C4-a as an IAM fact. | 3 × 1 = 3 |
| L-3 | SEC | The high-risk PII list is narrower than breach-notification scope (driver's licence, passport). | folded into P2-X2 / X3 |
| L-4 | DQ | The feedback loop grades itself: the measuring model sees the intake record and the reconciliation notes. | folded into P1-X5 |
| L-5 | FM | For bundles, the rule-based degrade floor would read `CLM-000101` from `<intake_record>` as the policy number (`degrade.py:30-32`), and degraded results are not excluded from agreement scoring. | folded into P1-X5 |
| L-6 | OPS | Deploy skew: six `$LATEST` functions updated one at a time. Old code can read a bundle key as plain text, with no `bundle_flags`. `Record` re-checks routing only for `ProcessingResult`, not dict payloads (`pipeline.py:531-533`). | folded into P1-X4 |

## 4. Stakeholder view — HIGH only

- **0. D0-a (9, LIVE v1)** — `Catch` without `ResultPath`, so the degraded,
  C11 and review-expiry paths fail on real AWS.
- **0. D0-b (6, LIVE v1)** — the summary call has no guardrail.
1. **L-1 (9)** — AI-services content opt-out missing **[re-verify]**.
2. **P1-X4 (6; FM 9)** — routing trusts the FM's amount (C-1), plus deploy
   skew (L-6).
3. **P1-X3 (6; F / DQ 9)** — correlated parser; single-source fields; revision
   keys (C-4).
4. **P1-X1 (6)** — gates check format, not meaning (C-2); unpinned config
   (C-8); self-lock (C-6).
5. **P1-X2 (6)** — silent disabled or unverifiable sources (C-5); loss-run
   bypass.
6. **P1-X5 (6)** — revision re-roll; replay blind to collateral breakage.
7. **P2-X2 (6)** — redaction gaps on derived text (spoken digit runs, OCR,
   narrow type list).
8. **P2-X3 (6)** — image PII reaches bundles and Bedrock (C-3).

## 5. Phase 3 — mitigations (priced; **all accepted 2026-09-23**, M7 as R8c-a, M11 → v1)

Effort is in builder-days (one builder). "Target" = the expected residual
score.

| Id | Mitigation | Cells | Effort | Target |
|---|---|---|---|---|
| **D0-a** | Catcher `ResultPath: "$.error"` ×6 + an ASL data-flow test + redeploy the definition | live v1 | 0.25 d + deploy | 1 |
| **D0-b** | `guardrail_config` on the summary call + an AC-A5 regression test + redeploy | live v1 | 0.25 d + deploy | 2 |
| **M1** | **A pre-routing check of FM output against canonical values** (`claim_amount` with tolerance, `incident_date`, `policy_number`) → blocking `bundle:fm_source_mismatch:<field>`. Route the threshold on the **canonical** amount. | P1-X4 | 0.5 d | 3 |
| **M2** | **An ambiguity-aware canonicalizer.** A date valid both ways with day ≤ 12 returns both readings → blocking `dq_warn:ambiguous_date` unless independently corroborated. Date order keyed by **source / issuer**, not channel. | P1-X3, X1 | 1 d | 3 |
| **M3** | **Catalog hardening:** completeness renders as non-empty; header exact-match → `invalid_schema`; report_date ≥ loss_date; exactly one CSV per partition; attachment keys confined to `raw/claims/<claim_id>/`; `intake/v=1/…` contract version | P1-X1 | 1 d | 3 |
| **M4** | **Unverifiable is not clean:** blocking `recon_unverifiable:<field>` (low-confidence sole source), `source_disabled:<src>`, `history_failed`, `history_unavailable` (stale or missing loss runs). The loss-run join and dates go through Canonicalize Values. | P1-X2 (C-5) | 0.75 d | 3 |
| **M5** | **Revision and replay governance:** a resubmission of a decided claim → human review only (unless it is a DQ-owner-tagged proposal re-run); replay over the **whole** channel / partner scope reporting fixed / broken / unchanged, where any break blocks the proposal; proposal scope keyed by partner id; the measuring prompt hides the intake record (L-4); degraded results are excluded (L-5). | P1-X5 | 1 d | 3 |
| **M6** | **PII:** (a) add `DRIVER_ID` / `PASSPORT_NUMBER` and similar types; (b) transcripts and OCR text are **redacted**, not "verified", and a stdlib scrub masks every run of ≥ 4 digits in transcripts (context only, so over-masking is harmless); (c) images go to the FM **only** when OCR confidence is insufficient **and** Layer 2 found no PII in that document; if OCR is insufficient but PII was found, `image_withheld:pii` (blocking); if OCR is sufficient, no image and no flag (*clarified 2026-09-23*: a literal "otherwise" would have flagged every confidently read document); (d) *deferred:* pixel redaction (an image library conflicts with R1); (e) an explicit **Deny `raw/*`** on v1's step-lambda role | P2-X2, X3, X4 (C-3) | 1.25 d | 3 |
| **M7** | An AWS Organizations **AI-services opt-out** policy (Comprehend, Textract, Transcribe) **[re-verify]** | L-1 | ~1 h + your account decision | 1 |
| **M8** | Tighten v1 wildcards: `sfn-exec.json` → explicit function ARNs; `remediation.json` → the `model-selection` profile only. Lint rule: no v1 grant may match a v2 resource — except SD-4's designed `s3:GetObject` on `bundles/*` (clarified 2026-09-23). | L-2 | 0.5 d | 1 |
| **M9** | Quarantine and feedback records hold **no values** (row index + rule ids + object version); `dq propose` runs S3-side only | P2-X1, X5 | 0.5 d | 2 / 1 |
| **M10** | Escape `<` and `>` in claimant-derived text inside the context tags, plus a formatter test | P1-X3 / X4 (injection) | 0.25 d | — |
| **M11** | v1 re-entry: pin a numbered Guardrail version instead of `DRAFT` | P2-X4 | v1 | — |
| **M12** | **Revision-scoped keys:** `bundles/<id>/r<rev>`, `processed/claims/<id>/r<rev>/…`; v1 result and pending keys follow the bundle key; the S3 **VersionId** travels in the v1 input and lineage; feedback pairs by revision | C-4 | 0.5 d | 3 |
| **M13** | **Lock correctness:** holder ARN == `$$.Execution.Id` → self-retry proceeds; grant `states:DescribeExecution` on intake executions (for takeover); `CreatePartition` `AlreadyExistsException` counts as success | C-6 | 0.25 d | 2 |
| **M14** | **Execution-level watchdog + limits:** an EventBridge rule on intake execution FAILED / TIMED_OUT / ABORTED → a `batch_failed` summary + metric; an alarm on intake `ExecutionsFailed`; a DLQ on the trigger; reserved concurrency **≥ 20** (knob corrected); inline-Map cap **50 rows**, with **Distributed Map (Standard child per claim)** named as the > 50 path; trim iteration outputs (`ResultSelector`) | C-7 | 1 d | 3 |
| **M15** | For bundle keys, RAG scope = the canonical intake jurisdiction and line of business | P1-X4 | 0.25 d | — |
| **M16** | For bundle keys, the rule-based degrade floor = the canonical intake fields (deterministic; still routes to review) | L-5 | 0.25 d | — |
| **M17** | **Pin the DQ config per batch at Admit.** `config_source=fallback` → quarantine the batch (fail closed); stamp the catalog hash into the Glue ruleset description and compare | C-8 | 0.5 d | 3 |
| **M18** | **Fail closed on missing flags:** a `bundles/` key whose state lacks `bundle_flags` → review; `Record` re-checks routing for dict payloads. Runbook: publish Lambda versions + alias-qualified ARNs switched together (the alias part can wait for IaC). | L-6 | 0.5 d | 3 |

**Packages** (≈ 11 builder-days in total, excluding D0):

| Package | Contents | Effort |
|---|---|---|
| **D0 first** (live v1) | D0-a + D0-b | ~0.5 d + one interactive redeploy |
| **v2 must-have** | M1 · M2 · M3 · M4 · M6 · M7 · M12 · M13 | ~5.5 d |
| **v2 should-have** | M5 · M10 · M14 · M15 · M16 · M17 · M18 | ~3.75 d |
| **Hygiene** | M8 · M9 | ~1 d |

M11 goes to v1 re-entry.

## 6. Queued passes

- **P3 auditability:** lineage with VersionIds (M12 interacts); proposal
  evidence retention.
- **P4 reliability:** a formal storm after M13 / M14. Most reliability risk has
  already surfaced as C-6 / C-7.
- **P5 cost:** image tokens (M6c lowers them); Textract Queries; metric
  cardinality.

Cadence: re-storm after the spec revision and after the first real-AWS smoke.
