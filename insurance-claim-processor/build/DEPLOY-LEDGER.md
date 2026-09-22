# Deploy ledger — claim processor (manual deploy, started 2026-09-22)

Every name / ID / ARN created during the manual deploy, in the order the
runbook (`DEPLOY.md`) needs them. Nothing here is a secret (no keys) — but the
access key for the deployer lives ONLY in `~/.aws/credentials`, never here.

## Stage 0 — account & identity  ✅ 2026-09-22

| Item | Value |
|---|---|
| AWS account | `324177727513` |
| Region (pinned — KMS ViaService) | `us-east-1` |
| Deployer group | `claim-processor-deployers` (AdministratorAccess) |
| Deployer user | `claim-processor-deployer` (CLI only, 1 access key) |
| CLI profile | `claim-processor` → `export AWS_PROFILE=claim-processor` per terminal |
| AWS CLI in use | Anaconda v1.40.44 (Homebrew v2 installed but PATH-shadowed; fine) |
| Budget | Monthly cost budget, $10, email alert |
| Bedrock models verified via `converse` | `us.anthropic.claude-sonnet-4-5-20250929-v1:0`, `us.anthropic.claude-haiku-4-5-20251001-v1:0`, `us.amazon.nova-pro-v1:0` |

## Stage 1 — S3 bucket  ✅ 2026-09-22

| Item | Value |
|---|---|
| Bucket | `claim-documents-poc-rk-20260922` (`arn:aws:s3:::claim-documents-poc-rk-20260922`) |
| Prefixes | `claims/`, `results/`, `pending-review/` (marker objects created) |
| Encryption | SSE-KMS, AWS-managed key `alias/aws/s3` = `arn:aws:kms:us-east-1:324177727513:key/aea6d346-5022-44cf-9d16-4d6b38af7920`, Bucket Key on |
| Versioning | Enabled |
| Block public access | all 4 on |
| Tags | Project=insurance-claim-processor, Environment=poc |

## Stage 2 — Bedrock Guardrail  ✅ 2026-09-22

| Item | Value |
|---|---|
| Name | `claim-processor-guardrail` |
| **ID** (→ `GUARDRAIL_ID` in `iam/step-lambda.json`, and `CLAIM_PROCESSOR_GUARDRAIL_ID` env) | `l2oanwsu6no2` |
| ARN | `arn:aws:bedrock:us-east-1:324177727513:guardrail/l2oanwsu6no2` |
| Version the code pins | `DRAFT` (publish + pin a numbered version for prod) |
| Config | prompt-attack HIGH (input); 13 PII types Mask on input+output (SSN, cards, bank, driver ID, passport, ITIN, PIN, password, AWS keys); harmful-category filters OFF (domain false positives); contextual grounding 0.70/0.50 — **inert until code sends `guardContent` grounding source (F5)** |
| Candidate promote | Automated Reasoning checks over `samples/policies/` (own ADR) |

**F4 (found here):** guardrail ARN carries the ID, not the name → patched
`iam/step-lambda.json` to a `GUARDRAIL_ID` placeholder + test + DEPLOY §0.

## Stage 3 — AppConfig  ✅ 2026-09-22 (deployment #1 AllAtOnce; data-plane read-back verified, poll 60s; strategy `claim-processor-linear-bake` = `3qgbyet`)
| Item | Value |
|---|---|
| Application `claim-processor` | **ID `3kx1rfd`** → substitute for `APPCONFIG_APP_ID` in `iam/remediation.json` |
| Environment `poc` | **ID `l8gkgvm`** |
| Profile `model-selection` (freeform JSON, hosted) | **ID `lfhpx38`** |
| Hosted version | 1 = `appconfig/model-selection.json` |
| Strategies | `AppConfig.AllAtOnce` (bootstrap), `claim-processor-linear-bake` (20%/1min, bake 5min — attach `ModelErrorRate` monitor to env in Stage 6) |
| Guardrail note | apply-guardrail masks SSN twice (`{…}{…}`) — overlapping detections, over-masks only; cosmetic |

## Stage 4 — IAM roles  ✅ 2026-09-22 — role ARNs `arn:aws:iam::324177727513:role/claim-processor-{step-lambda,remediation,sfn-exec}`; simulate-principal-policy: InvokeModel allowed on both ARN shapes, ApplyGuardrail allowed, PutObject claims/ implicitDeny

Rendered policies with real IDs live in `deploy-out/iam/` (gitignored):
`step-lambda.json` (GUARDRAIL_ID→l2oanwsu6no2), `remediation.json`
(APPCONFIG_APP_ID→3kx1rfd), `sfn-exec.json`, `trust-lambda.json`, `trust-states.json`.

| Role | Trust | Policies |
|---|---|---|
| `claim-processor-step-lambda` | lambda.amazonaws.com | `claim-processor-step-lambda` + `AWSLambdaBasicExecutionRole` |
| `claim-processor-remediation` | lambda.amazonaws.com | `claim-processor-remediation` + `AWSLambdaBasicExecutionRole` |
| `claim-processor-sfn-exec` | states.amazonaws.com | `claim-processor-sfn-exec` |
| `claim-processor-operator` | (deferred with HITL) | — |

**F6:** custom Lambda policies carry no `logs:*` → attach `AWSLambdaBasicExecutionRole` (DEPLOY §0 updated).
**F7:** `iam/remediation.json` shipped with a top-level `"Comment"` key → IAM `MalformedPolicyDocument`; removed, grammar test added (`IamPolicyGrammarTest`).

## Stage 5 — Lambdas (6 for the auto-approve path)  ✅ 2026-09-22 — breaker-probe invoked: `breaker_open: false`, 0 `appconfig poll failed` (config plane LIVE = DEPLOY §6 check #1); log retention 14d

**F1 resolved:** `claim_processor/lambda_entry.py` (bootstrap; `tests/test_lambda_entry.py`).
Artifact: `deploy-out/build_lambda.sh` → `deploy-out/claim-processor-lambda.zip` (16 MB, boto3 1.43.99 vendored, 0 .so).
Env: `deploy-out/lambda-env.json`. Runtime python3.12 / arm64 / 512 MB / role `claim-processor-step-lambda`.

| Function | Handler | Timeout |
|---|---|---|
| `claim-processor-breaker-probe` | `claim_processor.lambda_entry.breaker_probe` | 60 |
| `claim-processor-understand-extract` | `…lambda_entry.understand_extract` | 300 |
| `claim-processor-degraded-extract` | `…lambda_entry.degraded_extract` | 300 |
| `claim-processor-validate` | `…lambda_entry.validate` | 60 |
| `claim-processor-retrieve-summarize` | `…lambda_entry.retrieve_summarize` | 300 |
| `claim-processor-record` | `…lambda_entry.record` | 60 |
| _(deferred: `await-review` F2, `expire-review`)_ | | |

## Stage 9 — Smoke  ✅ #1 auto-approve 2026-09-22

| Execution | Result |
|---|---|
| `smoke-1-auto-approve` (`claims/auto-fl-clean.txt`) | **SUCCEEDED in ~12 s** → `results/claims/auto-fl-clean.txt.json`: `route: auto_approve`, accepted, grounded (`auto-florida`), $4,820.50, `model_variant: control:sonnet-4-5`, guardrail not intervened, `config_snapshot` = AppConfig doc (proof #3 the config plane is live) |
| _(pending)_ breaker-open → `DegradedExtract` (set `breaker_open_models`) | after Stage 6–7 |
| _(pending)_ HITL flagged claim | after F2 (await-review handler) |

## Stage 6–7 — Alarms, SNS, remediation
_(pending — next)_

## Stage 8 — Step Functions  ✅ 2026-09-22 (done BEFORE stages 6–7 so the alarms have traffic)

| Item | Value |
|---|---|
| Definition | `deploy-out/asl.json` = `sfn/asl.json` with `000000000000` → `324177727513` (13 states, STANDARD, StartAt BreakerProbe) |
| State machine | `claim-processor` → `arn:aws:states:us-east-1:324177727513:stateMachine:claim-processor` |
| Role | `claim-processor-sfn-exec` |
| CloudWatch logging | **not configured** — execution history in SFN is the audit trail (ADR-0004); **F8:** `iam/sfn-exec.json` lacks the `logs:*LogDelivery*` / `PutResourcePolicy` grants SFN log delivery needs, and level ALL + execution data would copy claim PII into logs. Promote: level ERROR, no execution data, + grants. |
| **F9** | `sfn/asl.json` shipped a top-level `"Type": "STANDARD"` (not ASL) → `SCHEMA_VALIDATION_FAILED`; removed, test now asserts pure-ASL top-level keys |
| Smoke claim (auto-approve) | `samples/claims/auto-fl-clean.txt` (collision claim minus the SSN; $4,820.50 < $10k) → `results/claims/auto-fl-clean.txt.json` |
| Flagged claims (HITL — deferred) | `home-tx-water.txt` ($12,500 > threshold), `auto-fl-collision.txt` (SSN) → stop at `AwaitReview` until F2 |

## Teardown checklist (do at the end)
- [ ] Delete state machine, Lambdas, alarms, SNS topic, AppConfig app, guardrail
- [ ] Empty + delete bucket (versioned → delete all versions)
- [ ] Delete IAM roles
- [ ] **Delete the deployer's access key** (or the user)
