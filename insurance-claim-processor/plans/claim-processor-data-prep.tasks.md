# Tasks + Plan — claim processor v2: data-preparation plane

**Stage:** sdd-spec (Stages 3–4) → **sdd-implement** (a fresh session).
**Status:** **APPROVED 2026-09-24** (`TASKS-OK`, the owner; LY-b kept) —
ready for **sdd-implement** in a fresh session.
**Spec:** `../specs/claim-processor-data-prep.spec.md` (APPROVED 2026-09-24,
`SPEC-OK`; criteria AC-S9…AC-Z37). **Design:**
`../design/lld-v2-data-prep.md` (FINAL) — the LLD is the detailed plan
(module layout §1.1–§1.4, contracts §2, ASL §3, tests §10, runbook §11);
this file adds only execution logistics: waves, worktrees, the merge
protocol, and the task list.
**Markers:** `[P]` parallelizable within its wave · `[owner]` performed by
the owner (CL3-a: blocks only its dependents) · `[off]`/`[sfn]`/`[gate]`/
`[infra]` as in the spec.
**Namespace:** **DP-30+**. The 2026-09-23 draft's DP-00–DP-25 are **void**
(superseded with their ACs; spec §3). Do not modify the frozen specs or the
R-/T-/C- task lists.

---

## 1. Plan (WV-a · PW-a · DW-a)

### 1.1 Waves

Waves are sequential checkpoints; parallelism lives **inside** a wave.

```
Wave 0  contracts & scaffolding      DP-30 … DP-43
Wave 1  batch level                  DP-44 … DP-48
Wave 2  per-claim sources → bundle   DP-49 … DP-57
Wave 3  the v1 side and the loop     DP-58 … DP-65
Wave 4  corpus, e2e, deploy assets   DP-66 … DP-71
Wave 5  the owner's manual deploy    DP-72 … DP-75   (not agent work)
```

### 1.2 Worktree protocol (PW-a)

- **One worktree per parallel track** within a wave
  (`git worktree add ../wt-<track> v2/<track>`), branched from the
  integration branch (`cursor/skill-family-instructions` today; the build
  session may cut `v2/integration` from it). Short-lived: a track merges
  back as soon as its tasks pass, then the worktree is removed.
- **File ownership.** A parallel track writes **only** the files its task
  rows name — its leaf module(s) and its own test file(s). The eight support
  modules (`__main__`, `contracts`, `keys`, `steps`, `clients`, `dq_config`,
  `fakes`, `telemetry`), `sfn/intake-asl.json` and every v1 file are
  **single-owner**: they are written only in Wave 0 or in serial tasks on
  the integration branch (Wave 3's DP-58/DP-59 run serially for this
  reason). A track that discovers it needs a support-module change stops and
  records it as a seam item; the change lands as a serial commit on the
  integration branch before dependent tracks continue. Fakes are written
  **completely in Wave 0** (DP-35): LLD §4.8 fixes every shape, so later
  tracks only consume them; a fake deviation is a seam item, not a track
  edit.
- **Merge gate (CL4-a).** Every merge back runs
  `bash build/tools/pre-commit.sh` (DP-42): the offline suite
  (`cd build && python3 -m unittest discover -s tests -t .`) — which
  contains the lints (IAM, ASL, DQDL golden, no-new-deps) — plus
  `python3 tooling/skill-sync/skill_sync.py check` from the repo root.
  Non-green merges do not land. Wave *N*+1 branches only from a fully
  merged, green Wave *N*.
- **Merge order** within a wave is given per wave below; tracks with no
  ordering constraint merge as they finish.
- Commits happen only when the owner asks; worktrees still commit locally on
  their own branches so merges are clean (those commits are folded when the
  owner asks for the real commit).

### 1.3 Owner steps inside the build (CL3-a)

| Step | When | Blocks only |
|---|---|---|
| DP-43 install the pre-commit hook | after DP-42, any time in Wave 0 | nothing (merges run the script directly until installed) |
| DP-67 render + commit the two call WAVs (`build/tools/render_calls.py`, macOS `say`; C10-1-a) | during Wave 4, after DP-66 authors the script | DP-66's call fixtures/manifest hashes; DP-69's call-path e2e |
| All of Wave 5 | after Wave 4 merges green | — |

### 1.4 Deploy (DW-a)

Wave 5 is owner-run, one step per turn, against `build/DEPLOY-V2.md` —
written by DP-71 from LLD §11 at **v1-walkthrough depth**
(`DEPLOY-WALKTHROUGH.md` style): per stage the exact console/CLI action, the
expected result, a verification check, the reasoning, and its
`DEPLOY-LEDGER.md` "v2" entry. The agent prepares commands and announced
read-only checks only (RUN-01); rollback = disable the trigger first.

### 1.5 Abstractions (G1 slop check)

The tasks introduce **no abstraction beyond the LLD's design** (the LLD's
own G1 cases — the catalog, the step dispatcher, the pin — were justified
and approved there). The only new artifact this plan adds is
`build/tools/pre-commit.sh` (CL4-a), a shell wrapper over the existing gate
commands; the simpler thing (remembering to run them) is what intersection
#4 flagged.

---

## 2. Task list

Columns: **Files** are the deliverables (paths under
`insurance-claim-processor/build/` unless rooted); **Verify → AC** names the
pass/fail check and the criteria the task proves; **G** lists the governance
rows (CL1-a) whose evidence the task builds.

### Wave 0 — contracts & scaffolding

Tracks: **0A** support modules (serial, integration branch) · **0B** gates
and IAM `[P]` · **0C** ASL and static assets `[P]`. Merge order: DP-30 →
DP-31/DP-32 → the rest of 0A; 0B and 0C merge after DP-32 (their tests
import `steps.STEP_CONTRACT` and the shell constants).

| ID | Trk | Files | Task | Deps | Verify → AC | G |
|---|---|---|---|---|---|---|
| DP-30 | 0A | `claim_processor/dataprep/{__init__,contracts}.py`, `tests/test_dataprep_contracts.py` | Bundle 2.0 types + tolerant `read_bundle`, the closed flag vocabulary (19 blocking families, info items), views (`view_sections`, `view_images`; extraction excludes `intake_record`/`loss_history`/`reconciliation_notes`), `parse_intake_key`, bundle-key builders, `CallStartResult` | — | unit: BUN-02 paths, unknown major → `BundleError`; vocabulary closed; views per BUN-05 → **V9, V10 (views), V17, S9 (parse)** | 44 (vocab) |
| DP-31 | 0A | `dataprep/keys.py`, `tests/test_dataprep_keys.py` | Every internal S3 key builder (KEY-01–KEY-07), execution/job/token names (EVT-01–EVT-04), `_invalid/<hash16>` | DP-30 | unit: keys-1…7; canonical serialization; name formats → **S15 (KEY-05), Z34 (names)** | 31 |
| DP-32 | 0A | `dataprep/steps.py`, `tests/test_dataprep_steps.py` | `handler` (Deps once per container, dispatch on `step`, event-driven pair, `UnknownStepError`), `STEP_CONTRACT`, STP-06's eight-env-var cold-start check, the six fault classes | DP-30, DP-31 | unit: unknown step → `DeployDefectError`; env-var matrix; contract keys; ≤ 32 KB → **Z11 (dispatch), Z18, S16 (STP-03/07)** | 24, 47 |
| DP-33 | 0A | `dataprep/clients.py`, `tests/test_dataprep_clients.py` | `build_clients` (closed 7-service set, per-service timeouts, keepalive, **`total_max_attempts: 1`** on the built client), `check_deadline`, `classify_error` (one Stubber case per §4.2 row), SVC-12 list-first reads, no-content exceptions | DP-30 | Stubber per error row; config asserts → **Z14 (clients), Z20, Y6 (SVC-07)** | 17, 45 |
| DP-34 | 0A | `dataprep/telemetry.py`, `tests/test_dataprep_telemetry.py` | Vocabulary (24 metrics, closed enums, ≤ 137 series), EMF + step loggers, result→metric mappers, emit-after-write; F3–F10, tel-1…9 | DP-30 | unit: F6/F8/F9/F10; series budget; no OBS-07 key → **Y4, Y5, Y6 (logs)** | 16, 18, 33, 43 |
| DP-35 | 0A | `dataprep/fakes.py`, `tests/test_dataprep_fakes.py` | The complete fake surface (§4.8): FakeS3 (versioned, 412/409), FakeStepFunctions, FakeAppConfigData, Fake Glue DQ/Comprehend/Textract/Transcribe, sidecar-driven, deterministic; fake responses pass Stubber validation | DP-33 | unit: SVC-14/15, TST-15 → **Z35 (fakes)** | — |
| DP-36 | 0A | `dataprep/dq_config.py`, `appconfig/data-quality.{json,schema.json}`, `tests/{draft04,test_dataprep_dq_config}.py` | Draft-04 schema + `validate` (one good/bad table, conf-1…5), fresh-session fetch, pin write/read, bounds table with widening directions | DP-32 | unit: two layers agree; fresh session; no fallback → **S16 (config), S17** | 15, 36, 48 |
| DP-37 | 0A | `dataprep/` 19 leaf-module shells (constants + frozen signatures), `dataprep/__main__.py`, `claim_processor/adjuster.py` (shell), `tests/test_dataprep_structure.py` | The §1.1 package tree with §1.3's public names; import-seam rules (MOD-01–MOD-08, KEY-02, SVC-02, SVC-04, OBS-02) as `ast` tests; CLI skeleton `intake --fake · dq propose|decide|deployed` | DP-30…DP-36 | structure test green over the shells → **Z19, Z28 (style)** | 2, 3, 6, 11, 17, 43 |
| DP-38 | 0B `[P]` | `tests/test_no_new_deps.py` | `rglob` both walks; stdlib allowlist grows by exactly `csv, unicodedata, decimal, math, statistics, urllib`; banned list; `tools/*.py` scanned | — | unit: TST-31 → **Z28 (deps)** | — |
| DP-39 | 0B `[P]` | `iam/{intake-lambda,intake-sfn,glue-dq,intake-events,dq-owner}.json`, `iam/trust/*.json` (incl. `operator.json`), `iam/resource/*.json`, v1 deltas (`iam/step-lambda.json`, `sfn-exec.json`, `remediation.json`, `operator.json`), `tests/test_iam_policy.py` | The approved §6/Appendix C JSON verbatim (IAM ok, 2026-09-24) + the grown lint (IAM-69–IAM-88: effect-aware, wildcard semantics, writers/readers tables, allowlists, no-unused-grant `ast` scan) | DP-37 (scan) | policy-lint green → **Z21–Z26, W15 (files)** | 4, 5, 6, 26 (Deny), 28, 32 |
| DP-40 | 0C `[P]` | `sfn/intake-asl.json`, `tests/test_intake_asl.py` | The §3.10 skeleton verbatim + the 33 `[sfn]` tests (structure, retriers, timeouts, Maps, catchers, verdicts, STEP_CONTRACT parity, GDQ-03 budget) | DP-32 | all 33 tests green → **Z17, Z12, Z11 (ASL-52), Z14 (retriers), Z15 (budgets), Z16 (Maps), S10 (poll), U19 (call loop)** | 1, 33 |
| DP-41 | 0C `[P]` | `events/{intake-trigger,intake-feedback,intake-watchdog}.json`, `glue/claims_intake_table.json`, `tests/test_dataprep_assets.py` (events + table half) | The EventBridge rule patterns (EVT-06–EVT-08), the DLQ wiring facts, the Glue table SD (CAT-12) | DP-30 | asset tests: keys-3, patterns, table columns → **Z13 (rules), S14 (table)** | 33 (rules) |
| DP-42 | 0B `[P]` | `tools/pre-commit.sh` | The CI hook (CL4-a): offline suite + skill-sync check, non-zero exit on failure; doubles as the PW-a merge gate | — | run it: green on Wave 0 → **Z37** | (runs all offline G rows) |
| DP-43 | `[owner]` | `.git/hooks/pre-commit` | Install DP-42's script as the git pre-commit hook | DP-42 | `git commit` runs it → **Z37** | — |

### Wave 1 — batch level

Tracks (one worktree each): **1A** catalog `[P]` · **1B** canonicalize `[P]`
· then **1C** admit `[P]` · **1D** batch gate `[P]` · **1E** row gate `[P]`.
Merge order: DP-44 and DP-45 first; DP-46/DP-47/DP-48 branch after both land.

| ID | Trk | Files | Task | Deps | Verify → AC | G |
|---|---|---|---|---|---|---|
| DP-44 | 1A | `dataprep/rule_catalog.py`, `glue/claims_intake.dqdl`, `tests/test_dataprep_catalog.py` | The catalog (header, rules, thresholds), deterministic `render_dqdl` == committed golden, `catalog_sha256`, `row_checks`, `batch_eval` (fake/tests only); rule-01…30; CSV-01–06 checks | Wave 0 | golden render; rule cases; header byte-equality → **S13, S9 (header/caps), S11 (CAT-11/15), S15 (CSV)** | 8, 23 |
| DP-45 | 1B | `dataprep/canonicalize.py`, `tests/test_dataprep_canonicalize.py` | `text` (FMT-07 pipeline, fixed point), `date` (issuer order, ambiguity + alternate), `amount`, `policy_number`, `vin`, `find_mentions`; date-4/5/12 | Wave 0 | unit + property (idempotence): → **T9 (canonicalize), V13 (fixed point)** | 22 (parsers) |
| DP-46 | 1C `[P]` | `dataprep/admit.py`, `tests/test_dataprep_admit.py` | The 13 admission checks in order, lock/self-retry/takeover/duplicate (REC-06–REC-09), pin (REC-14), `GetDataQualityRuleset` + `CreatePartition` (GDQ-09/10), lock-1…8, out-1…8 | DP-44, DP-45 | fakes/Stubber: every admission outcome with zero AI calls; 412 matrix → **S9, S12 (admit), S16 (pin), S14 (partition)** | 16, 23, 32, 36, 41, 46 |
| DP-47 | 1D `[P]` | `dataprep/batch_gate.py`, `tests/test_dataprep_batch_gate.py` | `start_run` (GDQ-01 request, ClientToken), `poll_run`/`cancel_run` (fail-closed states), `decide` (CAT-08–CAT-10 mapping, score, row-count check); batch-1…3/8, out-9/10 | DP-44 | Stubber/fake: verdict matrix fail-closed → **S10, S14 (run)** | 39, 41 |
| DP-48 | 1E `[P]` | `dataprep/row_gate.py`, `tests/test_dataprep_row_gate.py` | Row verdicts, systemic-warning quarantine (CAT-14), create-only revision markers **then** listing (REC-11/REC-12, SEQ-04), worklist for 51–200 (`INLINE_MAP_MAX`), quarantine/row-gate records; mark-1…7, batch-4…7, dmap-1 | DP-44, DP-45 | fakes: marker races, `revision.not_reused`, `resubmission_review` → **S11, X10 (markers), Z16 (worklist)** | 16 (markers), 25, 39, 40 |

### Wave 2 — per-claim sources → bundle

Tracks: **2A** redact `[P]` first-merge · **2B**–**2F** sources `[P]` · then
**2G** reconcile · **2H** formatter · **2I** bundle `[P]` after 2B–2F.
Merge order: DP-49 → (DP-50…DP-54) → (DP-55, DP-56, DP-57).

| ID | Trk | Files | Task | Deps | Verify → AC | G |
|---|---|---|---|---|---|---|
| DP-49 | 2A | `dataprep/redact.py`, `tests/test_dataprep_redact.py` | `chunk_text` (deterministic, overlap), `redact_segments`/`redact_text` (span widening, dual offset readings, packing), `scrub_digit_runs`, the 24/12 type split + botocore-enum test, fail-closed CMP-09 | Wave 1 | unit + Stubber: CMP-02…09; flag-18 → **T8, T10, T11** | 26, 42 |
| DP-50 | 2B `[P]` | `dataprep/narrative_quality.py` + `narrative` step body, `tests/test_dataprep_narrative.py` | Quality checks + score, `narrative_invalid:*` reasons, the CMP-10 call order, kill switch | DP-49 | unit: T-checks, order, flag-4/5 → **T7, T13, T8 (order), U24 (narrative)** | 42 |
| DP-51 | 2C `[P]` | `dataprep/language.py`, `tests/test_dataprep_language.py` | `analyze` (language gate, entities, key phrases, sentiment aggregation, theme eligibility), `turn_sentiment`; REC-04 containment | DP-49 | unit: CMP-11…16, 18–20; flag-6 → **T12, T14, U21 (sentiment), U23 (eligibility)** | 11 (data) |
| DP-52 | 2D `[P]` | `dataprep/documents.py`, `tests/test_dataprep_documents.py` | Pre-checks (PNG/JPEG only), QUERY_SETS, answers + confidence, lines, normalize→redact, L1 image decision (TXT-09/10/11), record shape, kill switch | DP-49 | Stubber/fake: TXT-01…12; flag-7/19 → **U13–U16, U24 (documents)** | 26 (images) |
| DP-53 | 2E `[P]` | `dataprep/transcribe.py`, `tests/test_dataprep_transcribe.py` | WAV-only pre-checks (16-bit PCM ≤ 600 s), fixed job request, lifecycle + `ConflictException`, output trust (TRN-07–TRN-09), turn build, Layer-1 counting, lineage, kill switch; grep tests TRN-03/08 | DP-49 | Stubber/fake: TRN-01…12; keys-6, flag-8 → **U17–U21, U24 (call)** | 42 |
| DP-54 | 2F `[P]` | `dataprep/loss_history.py`, `tests/test_dataprep_history.py` | Deterministic golden summaries, window at both TST-05 ends, `history_*` flags, canonicalized join keys; kill switch | Wave 1 | golden text; flag-12/13 → **U22, U24 (history)** | 24 (history) |
| DP-55 | 2G | `dataprep/reconcile.py`, `tests/test_dataprep_reconcile.py` | The four fields, corroboration-only, ambiguity handling (REC-05), B4-10; date-1…3/6…11, flag-14/15 | DP-45, DP-50…DP-54 | unit: verdicts; nothing flips → **V7, T9 (reconcile)** | 22, 24 |
| DP-56 | 2H | `dataprep/model_context.py`, `tests/test_dataprep_model_context.py` | The formatter: vocabulary/sections/views (FMT-01–17), caps + markers (FMT-18–23), the M6 image table I1–I8/I3a, `FormatError` no-op check, fitness FMT-43…47, 49–51, 53 | DP-55 | fitness suite: sentinels, vectors, caps, image rows → **V10 (FMT-49), V11 (table), V12–V16** | 12, 21 (view), 26, 30, 42, 49 |
| DP-57 | 2I | `dataprep/bundle.py`, `tests/test_dataprep_bundle.py` | Assemble: vetted-version image copies (BUN-10), images-first/bundle-last (KEY-04), lineage (BUN-08), one key per revision | DP-56 | Stubber/fake: copy version checks; commit order → **V8, V11 (copy)** | 49 |

### Wave 3 — the v1 side and the loop

Tracks: **3A → 3B → 3C serial on the integration branch** (single-owner v1
files) · **3D**–**3H** `[P]` in worktrees. Merge order: DP-58 → DP-59 →
DP-60; DP-61…DP-65 branch off after Wave 2 and merge as they finish.

| ID | Trk | Files | Task | Deps | Verify → AC | G |
|---|---|---|---|---|---|---|
| DP-58 | 3A | `claim_processor/{store,models,validator,understand,invoker,prompts}.py`, `tests/{test_store,test_models,test_validator_bundle,test_understand,test_invoker,test_prompts}.py` | `get_bytes_versioned`; `ProcessingResult.bundle`; `fm_source_mismatches` + `bundle_validation_flags` (V1-16/20/21); `MAX_IMAGE_BYTES` 3,750,000 (H1v2); `converse(messages=)`; the three templates + `TEMPLATE_VERSIONS` + hash golden | Wave 2 | fm-1…5; template hashes; legacy `prompt_versions` byte-identical → **W8 (read), W9 (validator), W11 (templates), W14 (models), W16** | 13, 21, 30 |
| DP-59 | 3B | `claim_processor/{pipeline,handler,routing,rag,degrade}.py`, `sfn/asl.json` (V1-11 only), `tests/{test_pipeline_bundle,test_bundle_routing,test_handler_routing_path,test_rag,test_degrade,test_asl_resilience,test_guardrail_bundle_tagging}.py` | The bundle branch (V1-02/17/18), request assembly (FMT-27–34), routing gate (V1-06/07/19), Record re-check (V1-08), RAG scope + degrade floor (V1-09/10), the whitelist keys; fm-6…12 | DP-58 | handler-path tests; H-F14-a sentinel; legacy smoke tests unchanged → **W8–W12, W14 (ASL), W16** | 14, 21, 31 (v1), 34, 35, 37, 38, 49 |
| DP-60 | 3C | `claim_processor/adjuster.py`, `claim_processor/__main__.py` (`ask`), `tests/test_adjuster.py` | The dialog: stateless turns, cache point, guardrail-required, provenance lines, bounded history (FMT-35–38); reads bundles via `dataprep.contracts` only | DP-59 | dialog request FMT-52; MOD-02 | **W13 (offline)** | 11 (ask) |
| DP-61 | 3D `[P]` | `dataprep/themes.py`, `tests/test_dataprep_language.py` (themes cases) | `aggregate` over outcome claims; no claim ids (M9); processed batches only | Wave 2 | unit: CMP-19/20 → **U23** | 29 (themes) |
| DP-62 | 3E `[P]` | `dataprep/dispatch.py`, `tests/test_dataprep_dispatch.py` | `claim_check` (marker listing, no body read) + `dispatch` (fence → StartExecution → marker; `ExecutionAlreadyExists`; ASL-39 recovery); fence-1, mark-8/9, fate-2/4 | Wave 2 | Stubber/fake: fates matrix → **Z34, S12 (fence)** | 16, 40 |
| DP-63 | 3F `[P]` | `dataprep/batch_outcome.py`, `tests/test_dataprep_batch_outcome.py` | `account` (join record, fate reconciliation ASL-15, conservation gap, fence) + `account_failed` (watchdog entry, create-only, no lock read); out-12, fate-3/5, fence-2 | Wave 2 | fakes: records, gap 0, dedupe → **S11 (records), S12, Z13 (watchdog), Z16 (fates)** | 10, 29, 33 (record), 40, 41 |
| DP-64 | 3G `[P]` | `dataprep/agreement.py`, `tests/test_dataprep_feedback.py` | The feedback step: stage records create-only, labels only, exclusions (REC-21), REC-27 first-record rule, F2-era behavior (REC-22 null) | Wave 2 | fakes: dedupe, labels, excluded → **X7, W17 (offline)** | 16, 29 |
| DP-65 | 3H `[P]` | `dataprep/proposals.py`, `dataprep/__main__.py` (dq subcommands), `tests/test_dataprep_proposals.py` | Candidates (REC-29), replay (REC-24/28), thresholds + break-blocking (REC-23), the three create-only files, `decide`/`deployed` record-only; replay-1…9 | Wave 2 | unit: proposal matrix; per-partner blocking → **X8, X9, X10 (loop)** | 15, 25 (replay), 29 |

### Wave 4 — corpus, e2e, deploy assets

Tracks: **4A** corpus `[P]` · **4B** scan helpers `[P]` · **4D** asset files
`[P]` · **4E** walkthrough `[P]` · then **4C** e2e + coverage (integration
branch, after all merges). DP-67 `[owner]` sits inside 4A.

| ID | Trk | Files | Task | Deps | Verify → AC | G |
|---|---|---|---|---|---|---|
| DP-66 | 4A | `tools/gen_synthetic.py`, `tools/render_calls.py`, `samples/v2/**` (s3 + truth trees), the manifest, `tests/test_dataprep_corpus.py` | The seeded corpus: B0001 (16 rows, pinned totals), B0002 (3), B0003 (51, `CLM-000301`–`CLM-000351`); seed 23 byte-identical; validity window; budget sum (TST-12); seeds + canaries | Wave 3 | regeneration SHA-256s; manifest oracle; window ends → **Z29, Z31 (corpus)** | 9 (data) |
| DP-67 | `[owner]` | `samples/v2/**` (two WAVs) | Render the two scripted calls once with `render_calls.py` (macOS `say`, two voices, 16 kHz mono 16-bit WAV) and commit; hashes go into the manifest | DP-66 (script) | generator hash check passes → **Z29 (C10-1-a)** | — |
| DP-68 | 4B `[P]` | `tests/pii_scan.py`, `tests/corpus_expect.py` | The high-risk scanner (TST-29 shapes, positive controls) and the shared record-comparison helper the smoke reuses (TST-30) | Wave 3 | scanner finds all seeds in raw, 0 in processed → **Z30 (helpers)** | 7 (scanner) |
| DP-69 | 4C | `tests/test_dataprep_e2e.py`, `tests/test_dataprep_coverage.py` | The e2e (§10.8 order: B0001 → v1 chain → feedback → propose/decide/deployed → B0002 → B0003) asserting TST-28's eleven checks; the G-row map as data (TST-03) + vocabulary reachability (TST-25) | DP-66, DP-67, DP-68 | e2e green; coverage table live → **Z30, Z36, Z28 (TST-03), X10 (B0002), Z31 (expectations), Z35 (driver parity)** | 7, 9, 10, 25, 42, 43, 44, 47 |
| DP-70 | 4D `[P]` | `alarms/intake.json`, `dashboards/data-quality.json`, `tests/test_dataprep_assets.py` (growth) | The twelve alarms A1–A12 (notify-only, FILL, 300 s/1-of-1/notBreaching) and widgets D1–D17; F7 checks | Wave 3 | asset tests parse + vocabulary-only → **Y7, Y8** | 18, 33 (alarms) |
| DP-71 | 4E `[P]` | `DEPLOY-V2.md`, `DEPLOY-LEDGER.md` ("v2" skeleton) | The DW-a walkthrough from LLD §11: stages P0–T1 and smokes 1–9, one step per turn, each with action, expected result, check, reasoning, ledger row; RUN-01–RUN-08 verbatim | Wave 3 | doc review against §11 (every stage + closing check present) → **Z33, Y9 (infra facts)** | 27 (Stage A), 37 (runbook) |

### Wave 5 — the owner's manual deploy (`[owner]`, one step per turn)

Not agent work (RUN-01). The agent prepares commands and announced read-only
checks; every result lands in the ledger.

| ID | Stages (per `DEPLOY-V2.md`) | Closes | Verify → AC | G |
|---|---|---|---|---|
| DP-72 | **P0** preconditions (Stage A or synthetic-only; baselines; ledger) · **V1a–V1d** v1 code, ASL, IAM, the **operator role** | v1 side live before any bundle key (V1-22); IAM-89 simulations for V1c/V1d | legacy smoke unchanged; simulations pass → **W15 (gate), W16 (order), Z21 (roles), Z27 (part), Z33** | 20, 27, 37 |
| DP-73 | **G1–G2** Glue · **C1** AppConfig · **I1** intake IAM · **L1** Lambda · **S1** machine · **O1** alarms · **E1–E2** EventBridge, trigger **last** | every v2 resource; I1 simulations; STP-06 invoke checks | closing checks per stage table → **S14 (gate), Y9, Z21 (creation), Z24 (policies), Z27 (part)** | 8 (ruleset), 36 (label) |
| DP-74 | **K1** smokes 1–9 (B0001 happy + AC-W17's 7 `AwaitReview` failures; duplicate; B0003 watchdog E1→E3; feedback; proposal loop + B0002's 2; Glue mapping; IAM simulations; first-run probes incl. transcript SSE; operator dialog) | TST-30/32/33; F11/F12; FMT-54; ASL-49/50 p99.9; IAM-90; EVT-06 tightening | `corpus_expect` matches; ledger findings flagged → **Z32, Z15 (gate), Z16 (B0003), Z13 (gate), Z24 (gate), Z27, Y10, W13 (gate), W17 (gate), S10/S14 (gate)** | 7, 9, 10, 16, 20, 25, 33, 36, 39, 41 (gates) |
| DP-75 | **R1** rollback rehearsal noted · **T1** teardown additions to the ledger | the teardown checklist covers every v2 resource | ledger review → **Z33 (rollback/teardown)** | — |

---

## 3. Coverage matrix (every AC → ≥ 1 task; every task → ≥ 1 AC)

S9→DP-30,44,46 · S10→DP-40,47 · S11→DP-44,48,63 · S12→DP-46,62,63 ·
S13→DP-44 · S14→DP-41,46,47,73,74 · S15→DP-31,44 · S16→DP-32,36,46 ·
S17→DP-36 ·
T7→DP-50 · T8→DP-49,50 · T9→DP-45,55 · T10→DP-49 · T11→DP-49 · T12→DP-51 ·
T13→DP-50 · T14→DP-51 ·
U13→DP-52 · U14→DP-52 · U15→DP-52 · U16→DP-52 · U17→DP-53 · U18→DP-53 ·
U19→DP-40,53 · U20→DP-53 · U21→DP-49,51,53 · U22→DP-54 · U23→DP-51,61 ·
U24→DP-50,52,53,54 ·
V7→DP-55 · V8→DP-57 · V9→DP-30 · V10→DP-30,56 · V11→DP-56,57 · V12→DP-56 ·
V13→DP-45,56 · V14→DP-56 · V15→DP-56 · V16→DP-56 · V17→DP-30 ·
W8→DP-58,59 · W9→DP-58,59 · W10→DP-59 · W11→DP-58,59 · W12→DP-59 ·
W13→DP-60,74 · W14→DP-58,59 · W15→DP-39,72 · W16→DP-58,59,72 ·
W17→DP-64,74 ·
X7→DP-64 · X8→DP-65 · X9→DP-65 · X10→DP-48,65,69 ·
Y4→DP-34 · Y5→DP-34 · Y6→DP-33,34 · Y7→DP-70 · Y8→DP-70 · Y9→DP-71,73 ·
Y10→DP-74 ·
Z11→DP-32,40 · Z12→DP-40 · Z13→DP-40,41,63,74 · Z14→DP-33,40 ·
Z15→DP-40,74 · Z16→DP-40,48,63,74 · Z17→DP-40 · Z18→DP-32 · Z19→DP-37 ·
Z20→DP-33 · Z21→DP-39,72,73 · Z22→DP-39 · Z23→DP-39 · Z24→DP-39,73,74 ·
Z25→DP-39 · Z26→DP-39 · Z27→DP-72,73,74 · Z28→DP-37,38,69 · Z29→DP-66,67 ·
Z30→DP-68,69 · Z31→DP-66,69 · Z32→DP-74 · Z33→DP-71,72,73,74,75 ·
Z34→DP-31,62 · Z35→DP-35,69 · Z36→DP-69 · Z37→DP-42,43.

**All 88 criteria covered; every task DP-30…DP-75 maps to ≥ 1 criterion.**

## 4. G-row map (CL1-a)

Per-task rows are in §2's **G** column; the roll-up (every G row → task(s)
whose tests are its evidence; `[gate]` halves land in DP-72…DP-74):

G1→DP-40 · G2, G3→DP-37 · G4, G5→DP-39 · G6→DP-37, DP-39 ·
G7→DP-68, DP-69 (+DP-74) · G8→DP-44 (+DP-73, DP-74) · G9→DP-66, DP-69
(+DP-74) · G10→DP-63, DP-69 (+DP-74) · G11→DP-37, DP-51, DP-60 ·
G12→DP-56 · G13→DP-58 · G14→DP-59 · G15→DP-36, DP-65 ·
G16→DP-34, DP-46, DP-62, DP-64 (+DP-74) · G17→DP-33, DP-37 ·
G18→DP-34, DP-70 (+DP-74 F11/F12) · **G19→standing evidence**
(`lint_diagram.py` over the unchanged v2 diagrams; no new task — DP-69's
TST-03 table cites it) · G20→DP-72, DP-74 · G21→DP-56, DP-58, DP-59 ·
G22→DP-45, DP-55 · G23→DP-44, DP-46 · G24→DP-32, DP-54, DP-55 ·
G25→DP-48, DP-65, DP-69 (+DP-74 smoke 5) · G26→DP-39, DP-49, DP-52, DP-56 ·
G27→DP-72 (Stage A, `[infra]`, owner) · G28→DP-39 (+DP-74 smoke 7) ·
G29→DP-61, DP-63, DP-64, DP-65 · G30→DP-56, DP-58 · G31→DP-31, DP-59 ·
G32→DP-39, DP-46 · G33→DP-34, DP-40, DP-63, DP-70 (+DP-74 smoke 3) ·
G34→DP-59 · G35→DP-59 · G36→DP-36, DP-46 (+DP-74 smoke 6) ·
G37→DP-59 (+DP-72 runbook V1a) · G38→DP-56, DP-59 ·
G39→DP-47, DP-48 (+DP-74 smoke 6) · G40→DP-48, DP-62, DP-63 ·
G41→DP-46, DP-47 (+DP-74) · G42→DP-49, DP-50, DP-53, DP-56, DP-69 ·
G43→DP-34, DP-37, DP-69 (+DP-74) · G44→DP-30, DP-69 · G45→DP-33 ·
G46→DP-46 · G47→DP-32, DP-69 · G48→DP-36 · G49→DP-56, DP-57, DP-59.

**All 49 rows mapped**; DP-69's TST-03 test holds this table as data, so a
row losing its evidence fails the suite.

## 5. Analyze (Stage 4 — cross-artifact + grounding)

- **Coverage, both ways:** §3 maps all 88 criteria; no orphan task. The
  §9.10 failure rows reach tasks through the spec's §5.2 (each row's
  criteria appear in §3). G rows: §4, all 49.
- **Constitution** (`.cursor/rules/architecture-principles.mdc`): DI holds —
  every AWS call goes through `Deps`/injected clients (SVC-01, DP-33), no
  import-time client (structure test, DP-37); SRP — one leaf module per
  component (MOD-01); simplest-thing — no abstraction beyond the LLD (§1.5);
  spec-before-code by construction (this file precedes the build).
- **Frozen v1 invariants A–R** (CL5-a, spot-checked against the criteria):
  A1/L (no completions contract; adapter untouched) — bundle requests go
  through the same `ModelInvoker`/adapter (AC-W11, AC-W13); C2/A3 (one retry
  layer) — intake clients `total_max_attempts: 1`, the state machine owns
  Retry (AC-Z14), v1's layer unchanged; B3 (five-field schema) — kept;
  extraction template still yields the five keys (AC-W11); E1/F3/R3 (single
  approval predicate; nothing widens auto-approve) — every new path adds
  review-only flags (AC-W9, AC-V17); the config bounds table marks widening
  directions (AC-S17); F2/G1 (idempotent result, one execution per claim) —
  revision-scoped names + markers (AC-Z34, AC-X10); H1/Q2 (no PII in logs) —
  AC-Y6 extends it; I1/I2 (IAM lint) — AC-Z26; J1/J2/R1 (offline-first, no
  new deps) — AC-Z28; K–R behaviors untouched by legacy keys (AC-W16).
- **Grounding:**
  - v1 files named by DP-58/DP-59/DP-60 all exist under
    `build/claim_processor/` and `build/tests/` (checked 2026-09-24):
    `store.py`, `models.py`, `validator.py`, `understand.py`, `invoker.py`,
    `prompts.py`, `pipeline.py`, `handler.py`, `routing.py`, `rag.py`,
    `degrade.py`, `sfn/asl.json`, `iam/{step-lambda,sfn-exec,remediation,operator}.json`,
    and the named test files.
  - New paths (`dataprep/`, `build/glue/`, `build/events/`,
    `build/iam/trust/`, `build/iam/resource/`, `build/alarms/`,
    `build/dashboards/`, `tools/`, `samples/v2/`) do not exist yet —
    created by their tasks; no task references a file no task creates.
  - Every AWS API named comes from the LLD's §4/§6 (whose `[re-verify]`
    marks stay `[gate]`, checked in DP-74); **no new pip dependency**
    anywhere (AC-Z28; `requirements.txt` stays `boto3, botocore`).
- **Baselines (2026-09-24, after the spec revision):** offline suite 288 OK
  (1 skipped); `python3 tooling/skill-sync/skill_sync.py check` exit 0.

## 6. Human gate

**`TASKS-OK`** approves the wave/worktree plan (§1) and the task list (§2)
as the build contract. Then **sdd-implement runs in a fresh session**, wave
by wave per the kickoff in the spec's §7 and this plan; Wave 5 belongs to
the owner. Until `TASKS-OK`: no code, no worktrees, no AWS calls.

### Status log

| Date | Event |
|---|---|
| 2026-09-24 | Spec APPROVED (`SPEC-OK`). This file drafted per LY-b/WV-a/PW-a/DW-a and CL1–CL5. |
| 2026-09-24 | **`TASKS-OK`** given ("keep LY-b, TASKS-OK"). Stage 2–4 complete. Next: sdd-implement (fresh session), Wave 0 → DP-30; Wave 5 is the owner's. |
