# Tasks + Analyze — claim processor model resilience

**Stage:** sdd-spec (Stages 3–4) → **sdd-implement**. **Status:** APPROVED
2026-09-21 — implementing (see per-wave status log at the end). **Spec:**
`../specs/claim-processor-model-resilience.spec.md` · **Plan:**
`./claim-processor-model-resilience.plan.md` · **ADRs:** 0010–0015.
**Markers:** `[P]` parallelizable · `[off]` offline-verifiable · `[gate]`
real-AWS · `[sfn]` state-machine layer · `[infra]` runbook/deploy review.
Each task maps 1:1 to EARS criteria. Namespace **R-** (distinct from prior
T-/C-). Do **not** modify the frozen real-AWS spec or T-01…T-19 / C-01…C-08.

## Task list

### Wave 3a — foundation (config + adapter + contract)

| ID | File | Task | Deps | Verify → AC |
|---|---|---|---|---|
| R-01 `[P]` | `config_provider.py` (new) | `ConfigProvider` over injected `appconfigdata`; last-known-good cache; env/default fallback; reject malformed value + `config_rejected` | — | Stubber session → resolved config; killed stubber → env → default; malformed → last-known-good; unit → **K1,K2,K4** |
| R-02 `[P]` | `models.py` | extend `ProcessingResult`: `config_snapshot`, `model_variant`, `ensemble`, `degradation_tier`, `breaker_state`, `remediation` (optional/defaulted) | — | unit: new fields serialize; pre-increment record still serializes → **R4,K5,M3,N5,O4,P5** |
| R-03 | `adapter.py` (new), `invoker.py` | `ModelAdapter` iface + `BedrockConverseAdapter` (Claude/Nova); `AdapterError`; `CallOutcome` enum + `AdapterResult`; preserve C2/no-completions/guardrail/resolved-id | — | Stubber per family; bad shape → `AdapterError` (not `KeyError`); outcome enum; exactly one call; grep no completions → **L1–L5** |
| R-04 | `config.py` | `EscalationPolicy` gains `ensemble_models`, `degradation_tiers`, flag fields; `from_env` stays bootstrap; `ConfigProvider` produces the extended policy | R-01 | unit: defaults + env; provider → extended policy → **K2,K3** |

### Wave 3b — resilience behaviors (pure, unit-first)

| ID | File | Task | Deps | Verify → AC |
|---|---|---|---|---|
| R-05 `[P]` | `flags.py` (new) | flag eval: deterministic `claim_key` assignment, safe defaults, kill-switch | R-01 | unit: absent flag → safe default; same key → same variant; kill-switch forces off → **M1,M2,M5** |
| R-06 `[P]` | `breaker.py` (new) | **pure** breaker decision over injected signal/flag; open/half-open/closed; no in-process state | R-02 | unit: slow-success series → closed (N1); error-rate>threshold → open; recover → half-open → close → **N1,N3,N4,N5** |
| R-07 `[P]` | `degrade.py` (new) | tier-ladder walker + `RuleBasedExtractor` (regex/keyword 5-field) | R-03 | unit: advanced down → next tier → rule-based schema-valid; sub-advanced stamped + `human_review`; S3 hard unchanged → **P1–P5** |
| R-08 `[P]` | `ensemble.py` (new) | field-level majority + `agreement`; quorum fallback | R-03 | unit: agree → one result + high agreement; disagree → low-conf + `human_review`; sub-quorum → primary, never empty; summary untouched → **O1,O2,O3,O5** |
| R-09 | `routing.py` | extend predicate: degraded tier / ensemble split / rejected config / breaker-open → `human_review` (never auto) | R-06,R-07,R-08 | unit: each signal → review; clean still auto → **R3,O1,P3,K4** |

### Wave 3c — orchestration + observability

| ID | File | Task | Deps | Verify → AC |
|---|---|---|---|---|
| R-10 `[P]` | `metrics.py` (new) | EMF emitter **through `logging_safe`**; metric vocabulary; no `put_metric_data` | R-02 | unit: EMF-shaped JSON; PII context → no raw SSN/PAN (ties H1); grep no `put_metric_data` → **Q1,Q2** |
| R-11 `[P]` | `remediation.py` (new) | **pure** alarm-state → bounded-action mapping; destructive not representable | R-01 | unit: alarm → {open_breaker\|switch_model\|disable_ensemble\|rollback}; destructive absent from enum; action emitted → **Q4,Q5** |
| R-12 | `pipeline.py` | wire adapter+flags+ensemble+degradation into extract/summarize; A/B variant; record new fields; emit metrics; C9 preserved | R-03…R-10 | unit: flag off → single call; flag on → ensemble; advanced down → degrade; variant recorded; metrics emitted; dup key → one object → **K5,L,M2,M3,O,P,Q1,R4** |
| R-13 | `sfn/asl.json`, `handler.py` | add `BreakerCheck` `Choice` before model steps → degraded path; keep Retry/Catch/`waitForTaskToken`; thin handler I/O | R-06,R-12 | `[sfn]` SFN-Local: Choice on breaker state; open → degraded path, no model invoke; structure valid → **N2,N4** |

### Wave 3d — infra + gate

| ID | File | Task | Deps | Verify → AC |
|---|---|---|---|---|
| R-14 `[P]` | `iam/*.json`, `tests/test_iam_policy.py` | step-lambda `appconfigdata` read; **new** remediation role (AppConfig write on the app only); no `PutMetricData`; no FullAccess/bucket-wide `s3:*` | — | policy-lint: appconfig read scoped; remediation write scoped; no `cloudwatch:PutMetricData`; existing I1/I2 stay → **Q1, least-priv** |
| R-15 | `DEPLOY.md` | AppConfig app/env/profile + deployment strategy w/ bake alarm; CloudWatch alarms (error-rate/p99/$-per-claim); SNS → remediation Lambda; breaker flag | R-11,R-13,R-14 | `[infra]` doc-review checklist → **M4,Q3,Q4** |
| R-16 | `tests/` | offline sweep green (existing 100 + new); no new pip dep | all `[off]` | `python3 -m unittest discover -s tests`, no creds; grep no new dep → **R1** |
| R-17 | (run) | real-AWS smoke: live AppConfig change adopted no-deploy; alarm → flag flip; A/B variant split | R-12,R-13,R-15 | `[gate]` `CLAIM_PROCESSOR_REAL_AWS=1` → **K3,M4,Q3,Q4,R2** |
| R-18 `[P]` | `design/solution-design.md` | add **§8** model-resilience addendum linking ADRs 0010–0015 | — | doc-review: design ↔ ACs ↔ ADRs consistent → **traceability** |

## Coverage matrix (every AC → ≥1 task)

K1→R-01 · K2→R-01,R-04 · K3→R-04,R-17 · K4→R-01,R-09 · K5→R-02,R-12 ·
L1–L5→R-03 · M1→R-05 · M2→R-05,R-12 · M3→R-02,R-12 · M4→R-15,R-17 · M5→R-05 ·
N1→R-06 · N2→R-13 · N3→R-06 · N4→R-06,R-13 · N5→R-02,R-06 ·
O1→R-08,R-09 · O2→R-08,R-12 · O3→R-08 · O4→R-02,R-12 · O5→R-08 ·
P1→R-07 · P2→R-07 · P3→R-07,R-09 · P4→R-07 · P5→R-02,R-07 ·
Q1→R-10,R-14 · Q2→R-10 · Q3→R-15,R-17 · Q4→R-11,R-15,R-17 · Q5→R-11 ·
R1→R-16 · R2→R-16,R-17 · R3→R-09 · R4→R-02,R-12.
**All 39 criteria covered; every task maps to ≥1 criterion.**

## Analyze (Stage 4 — cross-artifact + grounding)

- **Coverage:** complete both ways (matrix above). No zero-coverage AC; no
  orphan task.
- **Constitution:** no invariant violation — DI preserved (`ConfigProvider`,
  `ModelAdapter`, breaker signal all injected; no import-time client), SRP
  (eight single-purpose modules; `pipeline` orchestrates only), DIP
  (`ModelAdapter` + `ConfigProvider` interfaces; `RetrieverProtocol`
  unchanged), simplest-thing (breaker reuses the metric, not DynamoDB; EMF not
  `PutMetricData`; adapter Bedrock-only; ensemble extraction-only + flag-off
  default). **Two** new abstractions justified (G1, plan): `ModelAdapter`,
  `ConfigProvider`.
- **Integrity invariant (AC-R3) cross-check:** every new path (ensemble split
  O1, degraded tier P3, rejected config K4, breaker-open N2) routes to
  `human_review`; **no new auto-approve path** — R-09 owns the assertion; the
  clean predicate AC-E1 stays the single gate.
- **Grounding:**
  - All touched module paths exist under `build/claim_processor/` and
    `build/{sfn,iam,tests}/` (probed: config/invoker/models/pipeline/routing/
    understand/review/rag/store/logging_safe/handler; `sfn/asl.json`;
    `iam/{sfn-exec,step-lambda,operator}.json`; `tests/test_iam_policy.py`).
    `DEPLOY.md` does not exist yet (prior T-15 + this R-15) — not CRITICAL.
  - **No new pip dependency:** `appconfigdata` is in botocore (Stubber-able);
    EMF is structured logging; alarms/SNS/AppConfig-deploy are `[infra]`. The
    prior Analyze's "do not add moto" holds — new AWS-client tests use Stubber.
  - New AWS APIs (re-verify at build): `appconfigdata`
    `StartConfigurationSession`/`GetLatestConfiguration`; AppConfig deployment
    strategy + `StartDeployment`/`StopDeployment`; CloudWatch EMF + alarms;
    SNS — all valid.
  - `[sfn]` (N2/N4) needs Step Functions Local for the live `BreakerCheck`
    Choice; step logic is covered by offline unit tests, so a missing SFN-Local
    blocks only the `[sfn]` assertions, not the build. `[infra]` (M4/Q3/Q4) is
    runbook/deploy-review, not unit-tested.
- **Baseline (observed 2026-09-21):** offline suite **127 tests OK
  (skipped=1)** (`python3 -m unittest discover -s tests` from `build/`) = the
  pre-implementation baseline for Wave 3. `check_gate`
  (`python3 tooling/skill-sync/skill_sync.py check`, repo root):
  `SUMMARY: 7 families, 0 drifted, 0 shadow -> exit 0`.
- **CRITICAL count: 0** (zero-coverage = 0; missing required files = 0 —
  `DEPLOY.md` is a task output, not a referenced-but-absent dependency).
- **Verdict:** no CRITICAL. **Ready → human plan/tasks gate → sdd-implement**
  (Wave 3a → 3b → 3c → 3d). Two ⚠️ decisions for the gate: breaker-state
  mechanism (ADR 0012) and the bounded ensembling reversal (ADR 0013).

## sdd-implement status log

### Wave 3a — foundation COMPLETE (2026-09-21)

Kata gate: `python3 -m unittest discover -s tests` from `build/` → **147 tests
OK (skipped=1)** (was 127). `check_gate` (repo root):
`SUMMARY: 7 families, 0 drifted, 0 shadow -> exit 0`. Red/green per task.

| Id | Status | Files |
|---|---|---|
| R-01 | **DONE** — `ConfigProvider` (AppConfig Data + last-known-good + fallback + `validate_config`); AC-K1,K2,K4 | `config_provider.py`, `tests/test_config_provider.py` |
| R-02 | **DONE** — `ProcessingResult` +6 provenance fields; AC-R4,K5,M3,N5,O4,P5 | `models.py`, `tests/test_models_resilience.py` |
| R-03 | **DONE** — `ModelAdapter`/`BedrockConverseAdapter` + `CallOutcome` + `AdapterError`; AC-L1–L5 | `adapter.py`, `tests/test_adapter.py` |
| R-04 | **DONE** — `EscalationPolicy` +ensemble/tiers/flags + `from_config`; AC-K2,K3 | `config.py`, `tests/test_config_resilience.py` |

### Wave 3b — resilience behaviors COMPLETE (2026-09-21)

Kata gate → **184 tests OK (skipped=1)** (was 147). `check_gate`:
`7 families, 0 drifted, 0 shadow -> exit 0`. Red/green per task.

| Id | Status | Files |
|---|---|---|
| R-05 | **DONE** — `flags` safe defaults + deterministic variant + kill-switch; AC-M1,M2,M5 | `flags.py`, `tests/test_flags.py` |
| R-06 | **DONE** — pure `decide_state` (slow-success never opens) + `breaker_open` shared-flag; AC-N1,N3,N4 | `breaker.py`, `tests/test_breaker.py` |
| R-07 | **DONE** — `walk_tiers` ladder + `RuleBasedExtractor` floor; AC-P1,P2,P5 | `degrade.py`, `tests/test_degrade.py` |
| R-08 | **DONE** — `combine` majority/agreement + `has_quorum`; AC-O1,O2,O4,O5 | `ensemble.py`, `tests/test_ensemble.py` |
| R-09 | **DONE** — routing integrity gates (degraded/split/breaker/config → review); AC-R3,O1,P3,K4 | `routing.py`, `tests/test_routing_resilience.py` |

### Wave 3c — orchestration + observability COMPLETE (2026-09-21)

Kata gate → **208 tests OK** (was 184). Red/green per task; one strike on R-10
(EMF Timestamp tripped the PAN regex → redact string leaves only, numbers
preserved). `check_gate`: `0 drifted, 0 shadow`.

| Id | Status | Files |
|---|---|---|
| R-10 | **DONE** — EMF via `logging_safe.redact` (strings), no `put_metric_data`; AC-Q1,Q2 | `metrics.py`, `tests/test_metrics.py` |
| R-11 | **DONE** — pure alarm→bounded-action map; destructive not representable; AC-Q4,Q5 | `remediation.py`, `tests/test_remediation.py` |
| R-12 | **DONE** — pipeline wires adapter+flags+ensemble+degradation+metrics; default path byte-identical (existing 15 pipeline tests green); AC-K5,L,M2,M3,O,P,Q1,R4 | `pipeline.py`, `adapter.py` (`from_invoker`), `tests/test_pipeline_resilience.py` |
| R-13 | **DONE** — ASL `BreakerCheck` Choice → `DegradedExtract`; `degraded_extract` handler; AC-N2,N4 `[sfn]` structure (SFN-Local absent) | `sfn/asl.json`, `handler.py`, `tests/test_asl_resilience.py`, `tests/test_handler_resilience.py` (+updated `test_asl.py` StartAt) |

### Wave 3d — infra + gate COMPLETE (2026-09-21)

Kata gate → **217 tests OK (skipped=1)** (was 184 at Wave 3a start; +90 for the
increment). `check_gate`: `SUMMARY: 7 families, 0 drifted, 0 shadow -> exit 0`.

| Id | Status | Files |
|---|---|---|
| R-14 | **DONE** — step-lambda scoped AppConfig read; new `remediation.json` (scoped, reversible); no `PutMetricData`; existing IAM lint green; AC-Q1, least-priv | `iam/step-lambda.json`, `iam/remediation.json`, `tests/test_iam_resilience.py` |
| R-15 | **DONE** `[infra]` — `DEPLOY.md`: AppConfig app/env/profiles + deploy strategy w/ bake alarm; alarms; SNS→remediation; breaker flag; AC-M4,Q3,Q4 | `DEPLOY.md` |
| R-16 | **DONE** — no-new-dep gate (AST import scan; requirements = boto3/botocore only); AC-R1 | `tests/test_no_new_deps.py` |
| R-17 | **ENV-GATED** `[gate]` — real-AWS smoke (AppConfig live change, alarm→flip, A/B split) documented in `DEPLOY.md §6`; not run offline (needs `CLAIM_PROCESSOR_REAL_AWS=1`); AC-K3,M4,Q3,Q4,R2 | `DEPLOY.md` |
| R-18 | **DONE** — solution-design **§8** model-resilience addendum linking ADRs 0010–0015 | `design/solution-design.md` |

## Stage sign-off (2026-09-21)

All offline (`[off]`) + `[sfn]`-structure + `[infra]` tasks landed; R-17 is the
only `[gate]` item, env-gated (real-AWS not run here). Kata gate:
`python3 -m unittest discover -s tests` from `build/` → **217 tests OK
(skipped=1)** (baseline was 127). `check_gate` (repo root):
`SUMMARY: 7 families, 0 drifted, 0 shadow -> exit 0`. ADRs 0010–0015 Accepted.
Every offline AC has a passing test; integrity invariant AC-R3 enforced in
`routing.py`. **Next:** Stage 7 review (code-review, fresh thread) then the
gated real-AWS smoke (R-17).

## Stage 5 replan — Stage-7 review remediation (2026-09-21, **APPROVED**)

**Trigger:** (c) review findings invalidate tasks. Stage-7 max-effort review
returned **15 findings, 0 refuted**; offline suite still 217 green — these are
coverage gaps, not test failures. **Scope verdict: the spec does NOT change** —
every finding is an implementation/wiring gap against an existing AC (R3, N2,
K3, K4, O1, O3, P4, Q-cost, M) — so no backward propagation to
`claim-processor-model-resilience.spec.md`; the frozen specs stay frozen.
Route on approval: **sdd-implement** with Wave 3e below (append-only; R-01…
R-18 history untouched).

**Findings → task map (clusters):**

- **A — SFN/production wiring** (the resilience control plane exists but is
  not wired into the deployed path): #1 handler `retrieve_summarize`
  (`handler.py:88–98`) rebuilds `ProcessingResult` without the six resilience
  fields, so the AC-R3 integrity gates never fire in the SFN runtime —
  **defeats the increment's central invariant, silently**; #3 `$.breaker_open`
  (`sfn/asl.json:11`) is never populated → `DegradedExtract` unreachable;
  #4 per-claim `_refresh_policy()` runs only in CLI `process()`; production
  never passes `config_provider=` → live AppConfig changes never adopted
  (AC-K3); #2 IAM `appconfigdata:` prefix (`iam/step-lambda.json:66–67`) is
  not a real IAM namespace (data-plane actions authorize under `appconfig:`,
  verified vs AWS service-authorization reference) → silent `AccessDenied`.
- **B — delivered logic bugs (offline):** #5 even-split 2-model ensemble not
  flagged → disagreement can auto-approve (AC-O1/O3); #9 `bool⊂int` quorum
  coercion; #6 `usage.update` under-reports cost N×; #7 throttle swallowed →
  bypasses the ASL retry tier; #8 sticky config merge across refreshes;
  #10 `config_rejected` never produced (AC-K4 gate dead); #11
  `degradation_enabled` flag dead.
- **C — verification gap:** #13 no test drives routing through the handler/SFN
  path (why #1 shipped green). #14 DEPLOY.md two-profile design vs
  single-profile `ConfigProvider` (PLAUSIBLE — doc/design mismatch).

**Task disposition:** R-01…R-18 stay DONE as history, but findings **reopen**
the verify claims of R-13 (#1,#3), R-14 (#2), R-12 (#6,#7,#8), R-08 (#5,#9),
R-01 (#10), R-05/R-07 (#11), R-15 (#14), R-16 (superseded by R-27).
**R-17 (real-AWS smoke) SLIPS** until Wave 3e is green — running it now would
burn the gate on known-broken wiring (#2/#3/#4 alone make it fail or, worse,
pass misleadingly). Nothing drops.

### Wave 3e — review remediation (append-only; TDD red/green per task)

| ID | File | Task | Deps | Fixes | Verify → AC |
|---|---|---|---|---|---|
| R-19 | `handler.py` | carry the six resilience fields (+`config_rejected`) from the merged event into the `ProcessingResult` built in `retrieve_summarize`; route on the full record | — | #1 | red: handler-level test — breaker-open/degraded/split event → `route=human_review`; clean → auto → **R3,N5,O4,P5** |
| R-20 `[P]` | `iam/step-lambda.json`, `tests/test_iam_resilience.py` | `appconfigdata:*` → `appconfig:StartConfigurationSession` / `appconfig:GetLatestConfiguration`; lint asserts the correct namespace and forbids `appconfigdata:` | — | #2 | policy-lint red→green → **least-priv, K3 (unblocks)** |
| R-21 | `pipeline.py`, `handler.py`, `sfn/asl.json` | production config wiring: handlers accept/refresh `ConfigProvider` per claim; populate `$.breaker_open` in step output so `BreakerCheck` is reachable | R-19 | #3,#4 | unit: stubbed provider change adopted between two handler calls; ASL test: breaker-open output → `DegradedExtract` path taken → **K3,N2** |
| R-22 `[P]` | `ensemble.py` | even-split (no majority) → low `agreement` + `human_review` signal, never silent primary win; quorum arithmetic excludes `bool` (`isinstance` guard) | — | #5,#9 | unit: 2-model disagreement → flagged; `True/False` inputs don't count toward quorum → **O1,O3,O5** |
| R-23 `[P]` | `pipeline.py`, `adapter.py` | accumulate usage across ensemble/degrade calls (no `dict.update` overwrite); re-raise throttle outcomes so the ASL Retry tier owns backoff | — | #6,#7 | unit: N calls → summed tokens/cost; throttle → raises (not swallowed) → **Q-cost, L4/N** |
| R-24 `[P]` | `config_provider.py`, `flags.py`, `degrade.py` | fresh merge per refresh (no sticky carry-over); produce `config_rejected` on malformed value into the result payload; honor `degradation_enabled` | — | #8,#10,#11 | unit: bad→good refresh leaves no stale keys; malformed → `config_rejected=True` reaches routing; flag off → ladder disabled → **K2,K4,M1,P** |
| R-25 `[P]` | `DEPLOY.md`, `design/solution-design.md §8` | align config-plane docs to the single-profile `ConfigProvider` (A1: doc follows code; two-profile split rejected as new surface w/o an AC) — or flip at the gate | R-24 | #14 | `[infra]` doc-review: DEPLOY steps runnable against the shipped provider → **M4,Q3** |
| R-26 | `tests/test_handler_routing_path.py` (new) | SFN-path regression suite: drive `understand_extract → retrieve_summarize → Route` field-flow offline for each integrity signal; guards #1 forever | R-19,R-21 | #13 | suite red pre-R-19 patch, green post; every AC-R3 signal covered **through the handler** → **R3,N2** |
| R-27 | (run) | re-gate: full offline sweep + `check_gate`; then **un-slip R-17** | R-19…R-26 | — | `python3 -m unittest discover -s tests` ≥217 OK, no new dep; `check_gate` 0 drift → **R1** |

**Order:** R-19 first (integrity invariant), then R-20/R-22/R-23/R-24 `[P]`,
then R-21 → R-26 → R-25 → R-27 → R-17 `[gate]`.

**Gate outcome (2026-09-21):** human approved Wave 3e as scoped, order as
proposed; #14 resolved as **align DEPLOY.md to the single-profile provider**
(A1 — doc follows code; two-profile split rejected: new surface without an
AC). Spec untouched. Routed → **sdd-implement** (Wave 3e).

### Wave 3e — review remediation COMPLETE (2026-09-21)

Kata gate → **247 tests OK (skipped=1)** (was 217; +30 for the wave — every
fix red-first). `check_gate` (repo root): `SUMMARY: 7 families, 0 drifted,
0 shadow -> exit 0`. `test_no_new_deps` green (still boto3/botocore only).

| Id | Status | Fix / evidence |
|---|---|---|
| R-19 | **DONE** — `ClaimPipeline.result_from_event` carries all resilience fields (+`config_rejected` flags) into the routed record; handler `retrieve_summarize` rebuilt on it; usage split `{extract, summary}` + guardrail merge preserved. Red: 4 auto-approve bypasses + usage error | `pipeline.py`, `handler.py`, `tests/test_handler_routing_path.py` |
| R-20 | **DONE** — `appconfigdata:` → `appconfig:` actions; lint now asserts the real namespace and forbids `appconfigdata:` in ALL policy files (the old lint asserted the bug) | `iam/step-lambda.json`, `tests/test_iam_resilience.py` |
| R-21 | **DONE** — new `BreakerProbe` StartAt Task (`handler.breaker_probe` → `$.breaker_open` producer); public `refresh_policy()` called per-invocation by `breaker_probe`/`understand_extract`/`degraded_extract`/`retrieve_summarize`; live flag flip adopted between executions (stub-provider test) | `sfn/asl.json`, `handler.py`, `pipeline.py`, `tests/test_asl{,_resilience}.py`, `tests/test_handler_resilience.py` |
| R-22 | **DONE** — strict-majority confidence in `combine` (2-model split / 2-2 tie now low-confidence); `resolve_quorum` guards `bool ⊂ int` (`ensemble_quorum: true` no longer a quorum of 1) | `ensemble.py`, `pipeline.py`, `tests/test_ensemble.py` |
| R-23 | **DONE** — `_accumulate_usage` sums token counts across ensemble/ladder calls (was last-call-wins, N× under-report); `ThrottlingException` re-raised from the invoke seam so the ASL Retry tier owns backoff (C2); ladder-trigger test moved to timeout | `pipeline.py`, `adapter.py`, `tests/test_pipeline_resilience.py` |
| R-24 | **DONE** — provider merges fresh from bootstrap each poll (removed key actually leaves; rejected key retains last GOOD value — K4 held); `ConfigResult.rejected` → `config_rejected:<key>` validation flags → routing gate live; `degradation_enabled` off = fail loud (`DegradationDisabledError`), never a silent ladder walk | `config_provider.py`, `pipeline.py`, `degrade.py`, `tests/test_config_provider.py`, `tests/test_pipeline_resilience.py` |
| R-25 | **DONE** `[infra]` — DEPLOY.md: single `model-selection` profile w/ full JSON shape (flags inline), `appconfig:` namespace note, `BreakerProbe` in §4/§5, `config_provider=` wiring requirement; design §8 rows updated | `DEPLOY.md`, `design/solution-design.md` |
| R-26 | **DONE** — full-chain suite: `breaker_probe → understand_extract → retrieve_summarize` with the real pipeline; clean→auto, degraded→review, breaker-open→probe true + review | `tests/test_handler_routing_path.py` (9 tests) |
| R-27 | **DONE** — re-gate green (247 OK, check_gate 0 drift). **R-17 un-slipped**: the gated real-AWS smoke is now unblocked and remains the next `[gate]` action | (run) |

**Wave 3e sign-off:** all 15 Stage-7 findings closed (#14 as doc-alignment per
gate). Next: re-run Stage-7 review on the remediation diff if desired, then the
gated real-AWS smoke **R-17** (`CLAIM_PROCESSOR_REAL_AWS=1`, DEPLOY.md §6).

### Stage-7 RE-review fixes (2026-09-21, direct-fix per owner — no replan)

Fresh-thread re-review of commit e3ac15a: Wave 3e held (no reintroduced AC-R3
bypass) but returned 8 new findings; owner chose "fix directly". All fixed
red-first except **#3 (throttle re-raise vs AC-O5/P1 — OPEN, needs an owner
spec decision:** bless orchestrator-owned throttle retries w/ execution failure
terminal, or re-catch throttles inside the ladder**)**. Gate → **260 tests OK
(skipped=1)** (was 247), `check_gate` 0 drift.

| # | Fix | Files |
|---|---|---|
| 1 | AppConfig ARNs: name-scoping was dead (ARNs embed generated IDs). Read grant → `application/*` data-plane wildcard; remediation writes → `APPCONFIG_APP_ID` placeholder + REQUIRED substitution step in DEPLOY §0; `StartDeployment` re-scoped off `deployment/*`; lint forbids name-scoped ARNs + asserts the placeholder + DEPLOY documents it | `iam/step-lambda.json`, `iam/remediation.json`, `tests/test_iam_resilience.py`, `DEPLOY.md` |
| 2 | `ConfigProvider` resets its session token on a failed poll (single-use/expiring tokens no longer brick warm Lambdas) + logs `appconfig poll failed` so fallback ≠ "no change"; §6 gains a config-plane-liveness check first | `config_provider.py`, `tests/test_config_provider.py`, `DEPLOY.md` |
| 4 | Routing gates on `guardrail.intervened` — the ensemble can no longer auto-approve a claim a member's guardrail fired on | `routing.py`, `tests/test_routing_resilience.py`, `tests/test_pipeline_resilience.py` |
| 5 | Missing AC-Q1/K4/N5 metrics emitted: `ConfigRejected` (on rejection), `Degradation`+`BreakerTransition` (at observation), `HumanReview`+`Ungrounded`+`CostUsd` (at route). `CostUsd` = usage totalTokens × `flags.cost_per_1k_tokens_usd` (>0 opt-in; absent, never fabricated-zero) — un-deadens the CostPerClaim→disable_ensemble loop | `pipeline.py`, `DEPLOY.md`, `tests/test_pipeline_resilience.py` |
| 6 | Breaker recovery (AC-N4): `ModelErrorRate` leaving ALARM (OK/INSUFFICIENT_DATA) → new `close_breaker` action; alarm-window = coarse half-open probe (bounded-probe = production promote); alarms wire OK transitions to SNS | `remediation.py`, `tests/test_remediation.py`, `DEPLOY.md` |
| 7 | `UngroundedFallback` Pass state carries the full Wave-3 provenance + usage/guardrail/model ids (audit contract on the RAG-down path) | `sfn/asl.json`, `tests/test_asl_resilience.py` |
| 8 | `ensemble_enabled` requires a real bool (`is True`) — `"false"` can no longer switch the expensive path ON | `flags.py`, `tests/test_flags.py` |

**R-17 remains next** once #3 is decided (as shipped, a sustained throttle
fails the execution after the ASL retry tier — the smoke's outage scenario
should be run with a timeout fault, or #3 resolved first).
