# Tasks + Analyze — claim processor on real AWS

**Stage:** sdd-spec (Stages 3–4). **Status:** READY for sdd-implement.
**Spec:** `../specs/claim-processor-real-aws.spec.md` · **Plan:**
`./claim-processor-real-aws.plan.md`.
**Markers:** `[P]` parallelizable · `[off]` offline-verifiable · `[gate]`
real-AWS · `[sfn]` state-machine layer. Each task maps 1:1 to EARS criteria.

**Wave 0 (contract freeze):** names, signatures, defaults, and paths are
frozen in [`./claim-processor-real-aws.wave0-contracts.md`](./claim-processor-real-aws.wave0-contracts.md).
Later waves fork from that document. Do not start product modules until Wave 1.

## Task list

### Step A — feasibility spike

| ID | File | Task | Deps | Verify → AC |
|---|---|---|---|---|
| T-01 `[P]` | `config.py` (new) | `EscalationPolicy` (configurable `amount_threshold`=10000), region, model/guardrail/kb ids from env | — | unit: threshold from env/default, no constant → **E1b, A4** |
| T-02 | `invoker.py` | `converse` accepts text+image blocks + optional `guardrailConfig`; return intervention; retain timeouts/adaptive; record resolved id | T-01 | Stubber: messages/inferenceConfig, guardrailConfig present, image block ok, **no** completions contract → **A1–A5, D2, H2** |
| T-03 `[P]` | `understand.py` (new) | detect image vs text → content blocks; bound by byte size | — | unit: image→block, text→text, oversize rejected → **D1–D3** |
| T-04 `[P]` | `models.py` | extend `ProcessingResult` (route, review, guardrail, sfn_execution_arn, schema_version, understand_model_id, embeddings) | — | unit: serializes new fields → **F1, A4** |
| T-05 | `samples/`, `fake.py` | add ≥1 image sample + gold; fake covers image path | T-03,T-04 | eval: image sample → schema-valid 5 fields (offline) → **D1, B3** |
| T-06 | (run) | spike via `--real` on 3 text + 1 image; capture accuracy/grounding/PII/$/latency | T-01…T-05 | `[gate]` `CLAIM_PROCESSOR_REAL_AWS=1`; resolved ids recorded → **A4, H2, J2** |

### Step B — Step Functions + HITL + hardening

| ID | File | Task | Deps | Verify → AC |
|---|---|---|---|---|
| T-07 | `routing.py` (new) | pure `route_claim(...)` predicate (uses config threshold) | T-01,T-04 | unit: clean→auto; missing/PII/>threshold/ungrounded→review; threshold configurable → **E1, E1b, B1, B2, C1** |
| T-08 | `review.py` (new) | apply decision; `field_changes` diff; correct→final (no re-summarize); `review-expired` | T-04 | unit: correct records diff + final values; expired path → **E3, E4, F3** |
| T-10 `[P]` | `store.py` | add `pending-review/` get/put | — | unit: pending-review/<key>.json roundtrip → **E2, F** |
| T-09 | `pipeline.py` | split into step units; record after route(auto)/review(human); idempotent | T-02,T-03,T-04,T-07,T-08,T-10 | unit: auto path records; flagged→pending+route; dup key→one object → **E, F1, F2, F3, C2** |
| T-11 | `__main__.py` | `decide` subcmd (`SendTaskSuccess` + reviewer_id) + pending inspect; keep `--real` gate | T-08,T-10 | unit: decide payload (stubbed); gate guards → **E3, J2** |
| T-12 `[P]` | `logging_safe.py` (new) | redacting logger — no raw PII | — | log-shape: SSN packet → no SSN in captured logs → **H1** |
| T-13 | `sfn/asl.json`, `handler.py` (new) | Standard SM: Understand/Extract→Validate→Retrieve/Summarize→Route(Choice)→[AwaitReview `waitForTaskToken`]→Record; Retry/Catch (C2/C7/C11) | T-08,T-09 | `[sfn]` SFN-Local: Standard type, states + Retry/Catch, waitForTaskToken, 1 exec/claim → **E2, E4, E5, G1, G2** |
| T-14 `[P]` | `iam/*.json` (new) | 3 least-privilege roles + policy-lint | — | policy-lint: no FullAccess/bucket-wide s3:*; both ARNs; model-id pattern; operator scoped → **I1, I2** |
| T-15 | `DEPLOY.md` (new) | manual runbook: bucket+prefixes, KMS(ViaService), Guardrail(PII ANONYMIZE+grounding+prompt-attack), 3 roles, deploy Lambda(s)+SM, run+decide | T-13,T-14 | doc-review checklist → infra (**G, H2, I**) |
| T-16 | `tests/` | offline sweep green (existing 17 + new) | all `[off]` | `python3 -m unittest discover -s tests`, no creds → **J1** |

### Fast-follow (gated) — KB on S3 Vectors

| ID | File | Task | Deps | Verify → AC |
|---|---|---|---|---|
| T-17 `[P]` | `rag.py` | extract `RetrieverProtocol`; keyword retriever implements it; pipeline depends on protocol | T-09 | unit: pipeline via protocol (keyword) → **C (agnostic)** |
| T-18 | `kb.py` (new) | KB `retrieve` + metadata filter; embeddings model+dims recorded; fail-closed | T-17 | `[gate]` real KB; `[off]` retrieve-shape contract → **C3, C4** |
| T-19 | `scripts/tag_ingest.py` | ingest tagging: stamp 4 metadata tags | T-18 | `[off]` tags applied; `[gate]` real ingest → **C4** |

## Coverage matrix (every AC → ≥1 task)

A1–A5→T-02(,T-06) · B1,B2→T-07 · B3→T-05 · C1→T-07,T-09 · C2→T-09 · C3,C4→T-18,T-19 ·
D1→T-03,T-05 · D2→T-02,T-03 · D3→T-03 · E1,E1b→T-07(,T-01) · E2→T-10,T-13 ·
E3→T-08,T-11 · E4→T-08,T-13 · E5→T-13,T-09 · F1→T-04,T-09 · F2→T-09 · F3→T-07,T-08,T-09 ·
G1,G2→T-13 · H1→T-12 · H2→T-02,T-06,T-15 · I1,I2→T-14 · J1→T-16 · J2→T-06,T-11.
**All 32 criteria covered; every task maps to ≥1 criterion.**

## Analyze (Stage 4 — cross-artifact + grounding)

- **Coverage:** complete both ways (matrix above). No zero-coverage AC; no
  orphan task.
- **Constitution:** no invariant violation — DI preserved (handlers call
  modules; no import-time client), SRP (new modules single-purpose), DIP
  (`RetrieverProtocol`), simplest-thing (coarse SM, one processing role, keyword
  RAG first). One new abstraction justified (G1, plan).
- **Grounding:**
  - All touched module paths exist under `build/claim_processor/` (verified:
    models/store/prompts/invoker/rag/validator/pipeline/compare/fake/__main__).
  - **FINDING — `moto` is NOT in `requirements.txt` (only boto3/botocore).**
    The existing 17-test suite uses botocore **Stubber** (ships with botocore).
    Resolution: **do not add moto** — new AWS-client tests use Stubber +
    `LocalDocumentStore` (no new pip dependency; simplest-thing). The aws-ai
    binding's `test_stack = stubber+moto` is aspirational; the kata gate is
    Stubber-only.
  - `[sfn]` criteria (E2/E4/E5/G1/G2) need **Step Functions Local** (test
    infra, not a pip dep); step *logic* is still covered by offline unit tests,
    so a missing SFN-Local blocks only the `[sfn]` assertions, not the build.
  - Real APIs referenced (waitForTaskToken, SendTaskSuccess, SFN Standard,
    guardrailConfig, list_foundation_models/list_inference_profiles,
    bedrock:Retrieve) are all valid — resolve ids/pricing at build (re-verify).
- **Baseline:** offline suite currently **17 green** = the pre-implementation
  baseline. `check_gate` (skill-sync) is workspace-level, run from repo root;
  not kata-specific.
- **Verdict:** no CRITICAL. Ready → **sdd-implement**.

## Phase 1 — Convergence

**Stage:** sdd-converge (Stages 9–10). **Date:** 2026-09-21.
**Input:** Wave 1 code review of T-01, T-03, T-04, T-10, T-12, T-14
(working tree; 47 tests OK). **Stage 9 does not implement.**
Do not rewrite T-01…T-19. Do not spawn C-* for unimplemented Wave 2+
(T-02, T-05, T-07, T-08, T-09, T-11, T-13, T-15…T-19) — those rows
already exist.

### Classification (finding → gap-type → route)

| Finding | Evidence | gap-type | Route |
|---|---|---|---|
| **F1** High — operator `SendTaskSuccess`/`SendTaskFailure` scoped to `stateMachine:` ARN | Freeze §13: “on the SM”. ADR 0009 Decision §3: “on the state machine (HITL resume)”. Spec **I1/I2** do not name an SFN resource shape; I1 forbids FullAccess / bucket-wide `s3:*` only. Landed `operator.json` + `test_iam_policy.py` require `stateMachine:` (or `execution:`). AWS service-auth: those two actions have **empty Resource types** — IAM supports only `Resource: "*"`. HITL resume will `AccessDenied`. Silent `*` would violate freeze + lint. | `contradicts` (freeze/ADR vs AWS) | **sdd-replan** — do not implement `*` |
| **F2** High — H1 redaction is message-only | Spec **H1** / ADR 0008 Compliance: no raw PII in application logs. Freeze §13: logger “emits only redacted messages”. `logging_safe.py` redacts `getMessage()` and clears `args`. `exc_info`, `extra`, and the exception path are not redacted. Tests cover SSN in `info("%s", packet)` only. | `partial` (H1 unmet off the message path) | **C-01** → sdd-implement |
| **F3** Medium — IAM lint pins `foundation-model/*` and `inference-profile/*` | Freeze §13 + spec **I2**: both ARNs, model-id segment “as a pattern”. Lint requires those exact `*` ARNs. ADR 0009 Decision: resolved pattern `inference-profile/us.anthropic.claude-*`. Freeze-compliant lint vs ADR fitness cannot both be true. | `contradicts` (freeze/I2 vs ADR 0009) | **sdd-replan** — do not change the lint/JSON |
| **F4a** Medium — `ApplyGuardrail` on `guardrail/*` | Freeze §13 / ADR 0009: `ApplyGuardrail` on **the** guardrail arn. Landed `step-lambda.json` uses `arn:aws:bedrock:*:*:guardrail/*`. Action is present; resource is a class wildcard, not “the” guardrail. Named pattern is implementable (`guardrail/claim-processor*`, same style as other Wave 1 names). | `partial` | **C-04** → sdd-implement |
| **F4b** Medium — KMS `key/*` + `ViaService` pinned `us-east-1` | Freeze §4: `CLAIM_PROCESSOR_REGION` may be `eu-west-1`. Freeze §13 / ADR 0009: `kms:Decrypt`/`GenerateDataKey` with `kms:ViaService` (no named key, no region list). Landed condition is `s3.us-east-1.amazonaws.com` + `bedrock.us-east-1.amazonaws.com`. Static IAM cannot follow env. **Any-key** (`key/*`) is not an I1/I2 miss (those ACs do not name KMS); resolve named-key vs `key/*` in the same replan. | `contradicts` (configurable region vs pinned ViaService) | **sdd-replan** — do not pin or widen in code |
| **F5** Medium — T-03 oversize test uses caller `max_bytes=len-1`; never asserts frozen 5 MiB; non-image bytes `decode("utf-8")` strict | Freeze §7 / ADR 0006: `MAX_IMAGE_BYTES = 5_242_880`; oversize image raises; text not capped. `test_oversize_image_rejected` never hits the default. Non-image bytes take `payload.decode("utf-8")` → `UnicodeDecodeError` (not `OversizeDocumentError`, not a text block). Spec **D3** “bounded at ingest” is implemented for images, default/cap + binary-text path unmet. | `partial` (+ `missing` tests for the frozen default) | **C-02** → sdd-implement |
| **F6** Medium — T-12 / T-14 / T-01 miss EARS edges | T-12: no PAN, no `exc_info`/`extra` (folds into **C-01**). T-14: no assert that step-lambda S3 Get is `claims/*` only and Put is `results/*`+`pending-review/*` (**C-03**). T-14 ViaService assertion would lock F4b’s `us-east-1` — **do not spawn**; rides F4b replan. T-01: `_env("")` already falls back to `10000.0`; no test for empty threshold (**C-05**). | `missing` (tests) | **C-01**, **C-03**, **C-05** → sdd-implement |
| **F7** Low — `pending_review_key` has no S3 Stubber `expected-params` | T-10 landed Local roundtrip + key-shape in `test_store_pending.py`. Existing `test_store.py` Stubber covers `get_text`/`put_json` only, not the pending prefix. | `missing` (test) | **Deferred** (low; not blocking Wave 1 H1/I) |
| **F8** Low — CRLF in redacted log lines (log injection) | Spec **H1** is raw PII (SSN example), not injection. Folding CRLF into C-01 would silently widen H1. | `unrequested` | **sdd-replan** — de-scope or add an AC |
| **F9** Freeze path drift | Freeze §18: T-14 → `tests/test_iam.py`; T-10 → append `tests/test_store.py`. Landed `test_iam_policy.py` + `test_store_pending.py` (collision-avoidance vs Wave 0 extracted files / §1 “do not append to a shared monolith”). Same ACs, different paths. | `unrequested` | **sdd-replan** — amend freeze §18 to landed names (or rename later). Do not rewrite T-01…T-19 |

### sdd-replan items (not C-* implement tasks)

These must be decided in **sdd-replan** before any IAM *product* fix that
touches them. Do **not** silently implement `Resource: "*"`,
`us.anthropic.claude-*`, or a ViaService region list.

1. **F1 / I1–I2 / ADR 0009 / freeze §13** — operator HITL resume:
   allow `Resource: "*"` for `states:SendTaskSuccess`/`SendTaskFailure`
   only (AWS has no resource type), and rewrite the lint + freeze + ADR
   0009 so they agree. Optional extra scoping (tags/conditions) is a
   replan choice, not a Wave 1 silent `*`.
2. **F3 / I2 / ADR 0009** — model-id segment: keep freeze `*` (current
   lint), or adopt ADR’s `us.anthropic.claude-*`, or a third pattern.
   Pick one; amend spec/freeze/ADR/lint together.
3. **F4b / freeze §4 + §13** — `CLAIM_PROCESSOR_REGION` vs static
   `kms:ViaService`. Pin PoC IAM to `us-east-1`, template the region, or
   drop ViaService region literals. Same pass: named KMS key vs `key/*`.
   **Do not add a ViaService unit test that freezes `us-east-1` until this
   lands.**
4. **F8** — log-injection / CRLF: de-scope (H1 stays PII-only) or add an
   AC and a later C-* .
5. **F9** — freeze §18 test paths: record `test_iam_policy.py` and
   `test_store_pending.py` as the Wave 1 homes (collision-avoidance), or
   schedule a rename. Not a product defect.

**Blocked until 1–3 replan:** any change to `operator.json` HITL
Resource, Bedrock invoke ARN model-id segment, or KMS ViaService/key
ARN. **Not blocked:** C-01, C-02, C-03 (S3 prefix *tests* only), C-04
(ApplyGuardrail named pattern), C-05.

### New tasks (`missing` / `partial` only)

| Id | Files | Task | source-ref | gap-type | Pass/fail |
|---|---|---|---|---|---|
| **C-01** | `build/claim_processor/logging_safe.py`, `build/tests/test_logging_safe.py` | Redact PII on every emit path the stdlib logger can carry: formatted message, `exc_info` / exception text, and `extra`. Cover PAN as well as SSN. Do **not** add CRLF/injection behavior (that is F8 / replan). | F2 + F6 (T-12); **AC-H1**; ADR 0008 Compliance | `partial` | Captured records from `logger.info` / `exception` / `extra=` contain no raw SSN (`078-05-1120`) and no raw PAN stand-in; existing SSN packet test stays green |
| **C-02** | `build/claim_processor/understand.py`, `build/tests/test_understand.py` | Assert the frozen ingest cap; reject an image that exceeds the **default** 5 MiB (not only a caller `max_bytes=len-1`). Non-image / non-UTF-8 bytes must not raise `UnicodeDecodeError` (text block or a typed reject — pick one and test it). | F5; **AC-D3**; freeze §7; ADR 0006 | `partial` | `MAX_IMAGE_BYTES == 5_242_880`; image of `MAX_IMAGE_BYTES + 1` raises `OversizeDocumentError` with default kwargs; a non-image binary payload does not `UnicodeDecodeError` |
| **C-03** | `build/tests/test_iam_policy.py` | Policy-lint: step-lambda `s3:GetObject` is `claims/*` only; `s3:PutObject` is `results/*` + `pending-review/*` only; operator Get stays `pending-review/*`. Tests only — do not retarget ViaService or model-id ARNs. | F6 (T-14 S3 prefix); **AC-I1** | `missing` | New asserts fail if those prefixes are swapped or widened; existing I1/I2 lint stays |
| **C-04** | `build/iam/step-lambda.json`, `build/tests/test_iam_policy.py` | Scope `bedrock:ApplyGuardrail` to a **named** guardrail ARN pattern (e.g. `arn:aws:bedrock:*:*:guardrail/claim-processor*`), not `guardrail/*`. | F4a; freeze §13; ADR 0009 | `partial` | Lint requires a named guardrail resource (not `guardrail/*` alone); `ApplyGuardrail` remains present; no FullAccess / no bucket-wide `s3:*` |
| **C-05** | `build/tests/test_config.py` | Empty / whitespace `CLAIM_PROCESSOR_AMOUNT_THRESHOLD` falls back to `10000.0` (today’s `_env` already does this; it is untested). | F6 (T-01 empty threshold); **AC-E1b**; freeze §4 | `missing` | `from_env()` with `CLAIM_PROCESSOR_AMOUNT_THRESHOLD=""` (and whitespace) equals default `10000.0` |

### Deferred

- **F7** — S3 Stubber `expected-params` for `pending_review_key` /
  `put_pending_review` / `get_pending_review`. Low; Local roundtrip
  already covers E2 key shape. Durable home: plan **Convergence →
  Deferred**. Do not rewrite T-10.

### Stage 10 — sign-off (NOT MET)

This change is **not** fully implemented (Wave 2+ T-02, T-05, T-07… still
pending). **Do not claim sign-off.** Binding resolved 2026-09-21:

| Placeholder | Value |
|---|---|
| `{{constitution}}` | `.cursor/rules/architecture-principles.mdc` (no TDD Always-rules section) |
| `{{check_gate}}` | `python3 tooling/skill-sync/skill_sync.py check` (repo root) |
| `{{test_gate}}` | workspace `<none>`; kata gate = `python3 -m unittest discover -s tests` from `insurance-claim-processor/build/` |
| `{{methodology_source}}` | `<none>` |
| `{{gate_catalog}}` | `<none>` |
| `{{adr_home}}` | workspace `docs/architecture/adrs/application/mobile-test-automation/`; this kata files ADRs under `insurance-claim-processor/adrs/` |
| `{{examples.eval_capture_rule}}` | binding has no `[examples]`; schema reference is `eval_capture.record()` with `user_id`+`task_id` |

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Converged: every EARS AC has a passing test; no `missing`/`partial`/`contradicts` remain | **NOT MET** | Wave 2+ ACs unbuilt (A1–A5, D2, E, F, G, H2, C3–C4, J2, …). Phase 1 still has C-01…C-05 plus F1/F3/F4b contradicts. |
| 2 | `{{check_gate}}` green AND `{{test_gate}}` green — paste actual output | **NOT MET** as sign-off | Gates are green *today* but the change is incomplete, so this item cannot be signed. `check_gate` (repo root, 2026-09-21): `SUMMARY: 7 families, 0 drifted, 0 shadow -> exit 0`. Kata gate: `Ran 47 tests in 0.209s` / `OK`. Workspace `test_gate` is `<none>`. |
| 3 | Every ADR trigger has a filed `{{adr_home}}` record (+ index/log) | **NOT MET** | Kata ADRs 0004–0009 exist as **Proposed** under `insurance-claim-processor/adrs/`; that folder has no `index.md`/`log.md`. Workspace `adr_home` was not used. F1/F3 mean ADR 0009 is itself in contradiction with AWS / freeze. |
| 4 | G1/G3/G4/G7/G8/G9 answered by the human in their own words | **NOT MET** | `{{gate_catalog}}` is `<none>` (no G-series wordings in-repo). No human answers are recorded. This row does **not** invent them. Constitution Always-rules: the bound file has none (freeze §17). |
| 5 | Eval-capture rule | **NOT MET** | No `eval_capture.record()` (or equivalent) in this kata. T-06 (accuracy/grounding/PII/$/latency capture) is not done. Binding has no `[examples].eval_capture_rule`. |
| 6 | Blast-radius cleanup (what THIS change added that can now be deleted) | **NOT MET** | Wave 1 only; Wave 2+ still pending. Stage 9/10 this pass does not delete product/test code. No sweep performed. |

**max_iterations:** not agreed. Phase 1 is the first converge pass. Not
converged → **sdd-replan** for F1/F3/F4b/F8/F9, then **sdd-implement**
for C-01…C-05 (C-01/C-02/C-03/C-05 unblocked; C-04 unblocked; IAM
Resource/`*` / model-id / ViaService remain blocked on replan).

### Replan routing (2026-09-21, append-only)

Stage 5 proposal is in
[`claim-processor-real-aws.plan.md`](./claim-processor-real-aws.plan.md)
**`## Replan (Stage 5)`** — PROPOSED, human gate open. Do not rewrite
C-01…C-05 or T-01…T-19.

- **sdd-implement now (no spec wait):** C-01, C-02, C-03, C-04, C-05.
- **Human yes → sdd-spec first:** F1, F3, F4b, F9. Product IAM
  (`Resource: "*"`, model-id pattern, ViaService pin) stays blocked
  until that amend. Placeholders C-06/C-07/C-08 exist only in the
  plan Replan section; they are not tasks yet.
- **Drop / stay:** F8 de-scope; F7 Deferred; T-06 after T-09+T-11;
  T-17 still after T-09.

## Spec amendment landed — C-06 / C-07 / C-08 (2026-09-21)

Recommended set **APPROVED** (no alternatives named). Spec I1/I2,
freeze §4/§13/§18, ADR 0009 amended. `contradicts` F1/F3/F4b and
`unrequested` F9 are **resolved by spec amend**. F8 stays dropped
(no AC). T-01…T-19 and C-01…C-05 rows are unchanged.

### New tasks (`contradicts` resolved — implement after C-01…C-05)

Write-set overlap with C-03/C-04: `build/iam/operator.json`,
`build/iam/step-lambda.json`, `build/tests/test_iam_policy.py`.
**C-06…C-08 depend on C-03 and C-04.** Do not race those files.
Recommend: **C-01…C-05 first**, then **C-06 → C-07 → C-08**, then
Wave 2.

| Id | Files | Task | source-ref | gap-type | Deps | Pass/fail |
|---|---|---|---|---|---|---|
| **C-06** | `build/iam/operator.json`, `build/tests/test_iam_policy.py` | Operator HITL: `Resource: "*"` for `states:SendTaskSuccess` / `SendTaskFailure` only; update lint that currently requires `stateMachine:`/`execution:`. Optional `aws:SourceAccount` / `aws:RequestedRegion` MAY ride on `*`, not instead. No other PoC statement uses `*`. | F1; **AC-I1**; ADR 0009 Decision §3 | `contradicts` (resolved by spec amend) | C-03, C-04 | Lint fails if SendTask* is a `stateMachine:`/`execution:` ARN; operator HitlResume is `"*"`; FullAccess / bucket-wide `s3:*` still forbidden |
| **C-07** | `build/iam/step-lambda.json`, `build/iam/operator.json`, `build/tests/test_iam_policy.py` | Bedrock invoke ARNs → Claude + Nova named patterns on step-lambda + operator spike; lint asserts the model-id segment is not a lone `*`. | F3; **AC-I2**; freeze §13; ADR 0009 | `contradicts` (resolved by spec amend) | C-03, C-04, C-06 | Both roles name `foundation-model/anthropic.claude-*` + `amazon.nova-*` and `inference-profile/us.anthropic.claude-*` + `us.amazon.nova-*`; lint fails on a lone `*` segment |
| **C-08** | `build/iam/step-lambda.json`, `build/tests/test_iam_policy.py`; T-15 `DEPLOY.md` when it exists | Document/pin ViaService `s3.us-east-1.amazonaws.com` + `bedrock.us-east-1.amazonaws.com`; lint those strings; freeze that other `CLAIM_PROCESSOR_REGION` is unsupported for IAM until T-15. `key/*` stays. | F4b; freeze §4/§13; ADR 0009 | `contradicts` (resolved by spec amend) | C-03, C-04, C-07 | Lint requires those two ViaService literals and `arn:aws:kms:*:*:key/*`; no named CMK; region pin documented |

### Analyze (Stage 4 — 2026-09-21 bounded IAM amendment)

- **spec ↔ plan ↔ tasks:** I1 HITL `*` → C-06; I2 Claude+Nova → C-07;
  ViaService/`key/*` pin (freeze/ADR, no new AC) → C-08; F9 is freeze
  §18 only; F8 has no AC and no C-*. T-01…T-19 and C-01…C-05 untouched.
  Coverage: no zero-coverage new criterion; no orphan C-06…C-08.
- **Constitution:** bound file
  (`.cursor/rules/architecture-principles.mdc`) has **no** numbered
  8-invariants / Always-rules section. Alignment holds: least
  machinery (A1 — static JSON + lint, no templating/CDK), DI/testability
  unchanged (no `build/` product this pass), trade-off in ADR 0009
  (SendTask* `*` vs AWS empty Resource types).
- **Grounding:** cited paths exist (see probe this pass):
  `build/iam/operator.json`, `build/iam/step-lambda.json`,
  `build/iam/sfn-exec.json`, `build/tests/test_iam_policy.py`,
  `build/tests/test_store_pending.py`, `build/claim_processor/config.py`,
  `build/claim_processor/models.py` (`EXTRACT`/`SUMMARY`/`UNDERSTAND`
  examples). `DEPLOY.md` does **not** exist yet (T-15) — C-08 notes
  “when it exists”; not CRITICAL.
- **No CRITICAL** (zero-coverage = 0; missing required files = 0).
- **Baseline (this pass, no `build/` change):** `check_gate` (repo root)
  `SUMMARY: 7 families, 0 drifted, 0 shadow -> exit 0`. Kata gate
  (`python3 -m unittest discover -s tests` from
  `insurance-claim-processor/build/`): `Ran 47 tests in 0.204s` / `OK`.
- **CRITICAL count: 0.**
- **Verdict:** Ready → **sdd-implement** C-01…C-05 first, then
  C-06…C-08. Stage 10 not signed off.

## sdd-implement — C-01…C-08 complete (2026-09-21)

All eight convergence tasks landed. Kata gate:
`python3 -m unittest discover -s tests` from `build/` → **60 tests OK**.
`check_gate` (repo root): `SUMMARY: 7 families, 0 drifted, 0 shadow -> exit 0`.
Workspace `test_gate` is `<none>`. Wave 2 (T-02, T-05, …) not started.

| Id | Status |
|---|---|
| C-01 | **DONE** — extra / exc_info / PAN redacted (AC-H1) |
| C-02 | **DONE** — default 5 MiB cap + non-UTF-8 text block (AC-D3) |
| C-03 | **DONE** — S3 prefix-split lint (AC-I1) |
| C-04 | **DONE** — ApplyGuardrail `guardrail/claim-processor*` |
| C-05 | **DONE** — empty/whitespace threshold → `10000.0` (AC-E1b) |
| C-06 | **DONE** — operator HITL `Resource: "*"` (AC-I1) |
| C-07 | **DONE** — Claude+Nova named invoke ARNs (AC-I2) |
| C-08 | **DONE** — ViaService `s3.us-east-1` + `bedrock.us-east-1`; `key/*` stays |

## sdd-implement — Wave 2 complete (2026-09-21)

Wave 2 from plan Replan § "Then Wave 2: T-02, T-07, T-08" (and
`Wave 2 (T-02, T-07, T-08)` routing table). Kata gate:
`python3 -m unittest discover -s tests` from `build/` → **89 tests OK**
(was 60). `check_gate` (repo root):
`SUMMARY: 7 families, 0 drifted, 0 shadow -> exit 0`.
T-09 hub and later T-* not started.

| Id | Status |
|---|---|
| T-02 | **DONE** — converse `content` + `guardrail_config`; intervention recorded; no completions / no app retry (AC-A1–A5, D2, H2) |
| T-07 | **DONE** — `route_claim` clean→auto; missing/PII/>threshold/ungrounded/force-flags→review; threshold from policy (AC-E1, E1b, B1, B2, C1) |
| T-08 | **DONE** — `apply_decision` correct diffs + final values; expired never auto-approves (AC-E3, E4, F3) |

## sdd-implement — T-09 hub complete (2026-09-21)

T-09 sequential hub after Wave 2. Kata gate:
`python3 -m unittest discover -s tests` from `build/` → **100 tests OK**
(was 89). `check_gate` (repo root):
`SUMMARY: 7 families, 0 drifted, 0 shadow -> exit 0`.
T-05, T-11, T-06, T-13, T-15+ not started.

| Id | Status |
|---|---|
| T-09 | **DONE** — `ClaimPipeline` step units; auto→`results/`; flagged→`pending-review/`+route; dup key overwrite; record after human review (AC-E, F1, F2, F3, C2) |

## sdd-implement — T-05 + T-11 complete (2026-09-21)

T-05 (image sample + fake) and T-11 (`decide` CLI) after T-09 hub.
Kata gate: `python3 -m unittest discover -s tests` from `build/`.
T-06, T-13, T-15+ not started.

| Id | Status |
|---|---|
| T-05 | **DONE** — image sample + gold; fake image path → schema-valid 5 fields, amount rel-error 0 (AC-D1, B3) |
| T-11 | **DONE** — `decide` SendTaskSuccess payload (stubbed) + pending `inspect`; `--real`/`--s3`/decide gated (AC-E3, J2) |

## sdd-implement — T-17 RetrieverProtocol (2026-09-21)

T-17 after T-09 hub. Keyword retriever unchanged; pipeline annotation
widened to `RetrieverProtocol` (AC-C agnostic).

| Id | Status |
|---|---|
| T-17 | **DONE** — `RetrieverProtocol` extracted; `PolicyRetriever` implements it; pipeline depends on protocol (AC-C agnostic) |

## sdd-implement — T-13 ASL + handler (2026-09-21)

T-13 after T-08/T-09. Offline ASL structure + handler I/O (SFN-Local
not in this environment; Analyze: missing SFN-Local blocks only live
`[sfn]` exec, not the build).

| Id | Status |
|---|---|
| T-13 | **DONE** — Standard ASL UnderstandExtract→Validate→RetrieveSummarize→Route→AwaitReview(waitForTaskToken)→Record; Retry/Catch C2/C7/C11; handler thin adapter (AC-E2, E4, E5, G1, G2) |

## sdd-implement — T-06 gated spike (2026-09-21)

T-06 after T-09 + T-11. Offline gate + injected 3-text + 1-image
capture. Live Bedrock spike is `env-gated:` (not run here).

| Id | Status |
|---|---|
| T-06 | **DONE** — `--real --spike` refuses without `CLAIM_PROCESSOR_REAL_AWS=1`; injected path captures accuracy/grounding/PII/$/latency + resolved ids (AC-A4, H2, J2) |
