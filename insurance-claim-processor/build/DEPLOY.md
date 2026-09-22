# DEPLOY — claim processor (manual runbook)

Manual, console/CLI runbook (no CDK — ADR scope). Covers the base runtime and
the **model-resilience** additions (ADRs 0010–0015). `[infra]` steps are
verified by this checklist, not unit tests. Region pin: **us-east-1**
(`CLAIM_PROCESSOR_REGION` other than us-east-1 is unsupported for IAM — see
IAM ViaService).

## 0. Prerequisites

- S3 bucket `claim-documents-poc-<suffix>` with prefixes `claims/`,
  `results/`, `pending-review/`; default SSE-KMS.
- Bedrock Guardrail named `claim-processor*` (PII ANONYMIZE + contextual
  grounding + prompt-attack) — ADR 0008.
- Three base IAM roles from `iam/` (`sfn-exec.json`, `step-lambda.json`,
  `operator.json`) + the new **`remediation.json`** role (below).
- **REQUIRED substitution before creating the remediation role:** AppConfig
  ARNs embed the system-generated application **ID**, never the name. After
  creating the application (§1), fetch its ID and substitute the
  `APPCONFIG_APP_ID` placeholder in `iam/remediation.json`:

  ```
  aws appconfig list-applications --query "Items[?Name=='claim-processor'].Id"
  sed -i '' "s/APPCONFIG_APP_ID/<that-id>/g" iam/remediation.json
  ```

  (`step-lambda.json` needs no substitution — its data-plane read wildcards
  the application segment.) A role created with the placeholder left in place
  gets AccessDenied on every AppConfig write, and the failure is **silent**.

## 1. AppConfig — config + feature-flag plane (ADR 0010)

1. **Application:** `claim-processor`.
2. **Environment:** `poc`.
3. **Configuration profile** — a **single** freeform-JSON profile
   `model-selection` (the shipped `ConfigProvider` opens one session against
   one profile; a two-profile split is deliberately NOT used — replan
   2026-09-21, review #14). One document carries both the config keys and the
   flags under a `"flags"` object, matching `EscalationPolicy.from_config`:

   ```json
   {
     "extract_model_id": "...", "summary_model_id": "...",
     "understand_model_id": "...", "amount_threshold": 10000,
     "force_review_flags": [], "ensemble_models": [],
     "degradation_tiers": [],
     "flags": {
       "candidate_rollout_pct": 0, "candidate_model_id": null,
       "ensemble_enabled": false, "ensemble_quorum": 2,
       "breaker_enabled": true, "breaker_open_models": [],
       "degradation_enabled": true,
       "kill_switch_candidate": false, "kill_switch_ensemble": false,
       "cost_per_1k_tokens_usd": 0.0
     }
   }
   ```
4. **Bootstrap fallback:** the step Lambdas keep the `CLAIM_PROCESSOR_*` env
   vars set (defaults in `config.py`); if AppConfig is unreachable the last
   known good, then env, then dataclass defaults apply (AC-K1).
5. **Deployment strategy (AC-M4):** create a strategy with a **bake window**
   (e.g. `Deployment: Linear20PercentEvery1Minute`, `FinalBakeTime: 5m`) and
   attach the **CloudWatch alarm** `ModelErrorRate` (below). AppConfig
   **auto-rolls-back** the deployment if the alarm fires during bake.

`step-lambda` role grants scoped `appconfig:StartConfigurationSession` +
`appconfig:GetLatestConfiguration` (see `iam/step-lambda.json`). The IAM
namespace is `appconfig:`, **not** `appconfigdata:` — `appconfigdata` is only
the API/client name and grants nothing as an action prefix (review #2).

## 2. CloudWatch metrics + alarms (ADR 0015)

- Metrics arrive as **EMF** on the Lambda log streams (namespace
  `ClaimProcessor`) — no `PutMetricData`, no extra IAM (AC-Q1). Enable EMF
  metric extraction on the log group if not automatic.
- **Alarms (AC-Q3):**
  - `ModelErrorRate` — `Errors / calls` per `ModelId` over threshold.
  - `LatencyP99` — p99 `LatencyMs` over threshold.
  - `CostPerClaim` — `CostUsd` over threshold. `CostUsd` is emitted **only
    when** `flags.cost_per_1k_tokens_usd` is set `> 0` in the AppConfig
    document (blended $-per-1k-token rate for the deployed models); left at 0
    the metric is absent and this alarm stays INSUFFICIENT_DATA — set the rate
    or the cost-remediation loop is inert.
- Wire each alarm’s **ALARM and OK/INSUFFICIENT_DATA** transitions to the
  **SNS topic** `claim-processor-remediation` (recovery notifications drive
  the breaker close — §3/§4).

## 3. SNS → remediation Lambda (ADR 0015, AC-Q4)

1. SNS topic `claim-processor-remediation`.
2. Lambda `claim-processor-remediation` subscribed to it, using the
   **`remediation.json`** role (scoped, reversible AppConfig writes only — no
   `Resource: "*"`, no destructive actions).
3. The Lambda maps `alarm → action` via `remediation.decide_remediation`:
   - `ModelErrorRate → open_breaker` (add the model to `breaker_open_models`).
   - `LatencyP99 → switch_model` (set `candidate_model_id` / rollout).
   - `CostPerClaim → disable_ensemble` (`kill_switch_ensemble = true`).
   - `DeploymentBake → rollback_deployment` (`StopDeployment`).
   - **Recovery (AC-N4):** `ModelErrorRate` leaving ALARM (state OK, or
     INSUFFICIENT_DATA — an open breaker starves the alarm of samples) →
     `close_breaker` (remove the model from `breaker_open_models`). If the
     fault persists, the next real traffic re-fires ALARM and re-opens: the
     alarm's evaluation window is the coarse half-open probe budget; a
     bounded-probe-count half-open is a production promote.
   Every action is a flag flip or an AppConfig deployment rollback — reversible
   and audited (`remediation_record`).

## 4. Circuit breaker (ADR 0012)

- **Sustained throttle** (the common Bedrock brownout): the Retry tier on
  `UnderstandExtract` absorbs short spikes (5 backed-off attempts); a
  `ThrottlingException` that survives it is caught → `DegradedExtract`, which
  walks throttled tiers down to the rule-based floor — the claim degrades to
  human review instead of the execution failing (AC-P1, option B 2026-09-22).
  Meanwhile the throttle-driven `Errors` metric trips `ModelErrorRate` → the
  breaker opens → subsequent claims skip the sick model entirely.
- The breaker signal is the `ModelErrorRate` alarm; the shared state is the
  `breaker_open_models` flag. The state machine starts at the **`BreakerProbe`**
  Task (Lambda `claim-processor-breaker-probe`, `handler.breaker_probe`), which
  adopts the live AppConfig flags and writes `$.breaker_open`; the
  `BreakerCheck` Choice then routes an open-model claim to `DegradedExtract` —
  the failing model is never invoked (AC-N2). Recovery half-opens then closes
  (AC-N4).

## 5. Deploy the workflow

1. Package the step Lambdas (`handler.py` entry points incl. `breaker_probe`
   and `degraded_extract`). Construct each `ClaimPipeline` **with
   `config_provider=`** (an `appconfigdata` client session against the
   profile above) — without it the handlers run on bootstrap env config
   forever and AC-K3 cannot hold (review #4).
2. Import `sfn/asl.json` as a **Standard** state machine; set the Lambda ARNs.
3. Smoke: run an auto-approve claim, a flagged claim (HITL), and — with
   `breaker_open_models` set — confirm `DegradedExtract` runs and the result is
   `degradation_tier`-stamped and routed to review.

## 6. Gated real-AWS checks (R-17, `[gate]`)

Behind `CLAIM_PROCESSOR_REAL_AWS=1` (AC-R2):
- **First, verify the config plane is actually live** (the provider fails
  safe, so a broken IAM grant or wrong profile is otherwise invisible): call
  `aws appconfigdata start-configuration-session` as the step-Lambda role and
  confirm it succeeds; then confirm the Lambda logs show **no**
  `appconfig poll failed` warnings and a claim's `config_snapshot` reflects
  the deployed AppConfig document (not the env bootstrap).
- Change a value in AppConfig → the running Lambda adopts it within one poll
  interval, no redeploy (AC-K3).
- Trip `ModelErrorRate` → remediation flips `breaker_open_models` → next
  execution takes `DegradedExtract` (AC-Q4/N2).
- Enable an A/B flag → variants split deterministically by `claim_key` and the
  `model_variant` shows up on results (AC-M2/M3).
