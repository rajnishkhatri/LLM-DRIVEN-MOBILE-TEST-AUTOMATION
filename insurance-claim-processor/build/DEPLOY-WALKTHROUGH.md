# Deploy walkthrough — claim processor on AWS, by hand, with the reasoning

A first-time, manual deployment of the insurance-claim processor to a real AWS
account, written up from the session that did it (2026-09-22). It sits beside:

- `DEPLOY.md` — the terse expert runbook (*what*).
- `DEPLOY-LEDGER.md` — every name, ID and ARN this account ended up with.
- this file — *how* and *why*, step by step, for someone doing it for the first time.

Every step has four parts: **Console** (click path), **CLI** (copy-paste), a
**Browser check** (how to see it worked), and **Why** (the practice behind it).
Values shown are the ones this account used; substitute your own.

---

## 0. Ground rules that made the deploy safe

1. **You run every AWS command; nothing runs unattended.** Secrets (access keys)
   never leave your machine or enter a chat. A deployment is a sequence of
   reversible API calls you can read before you run them.
2. **Trust the API, suspect the view.** When the console and the CLI disagree, the
   CLI is right — the console is a cached web page over the same API. (S3
   "folders" appeared only after a refresh; AppConfig showed *Deploying* while
   the data plane already served the new version.)
3. **Read AWS errors literally.** `Application with Id APP_ID could not be found`
   means exactly that. `Could not find configuration … version 1` means the
   version does not exist. `Syntax errors in policy` on valid JSON means the
   *grammar* is wrong, not the JSON.
4. **ARNs embed IDs, not names.** Guardrails, AppConfig applications, and
   Step Functions executions are all addressed by system-generated IDs. A policy
   that matches on a name pattern silently matches nothing.
5. **Valid JSON is not a valid document.** Offline tests can check *contents*;
   only the real API checks the *schema*. Four of the eleven findings were
   schema/grammar problems (F4, F7, F9 plus the ID-vs-name pattern).
6. **Prove permissions with a denial.** A least-privilege policy is trustworthy
   only after you have watched it say *no* to the wrong thing.
7. **Keep a ledger.** Every ID gets used again two stages later. Write it down
   the moment it is printed.
8. **Set the spend alarm before creating anything.** Budgets warn; they do not
   stop spend. The stop button is deletion, and it is the last step of the deploy.

---

## Stage 0 — Account, identity, tooling

### 0.1 AWS CLI

**CLI**
```bash
aws --version
```
Any recent v1 or v2 works. On this machine `aws` resolved to the Anaconda v1.40
even after Homebrew installed v2 (PATH shadowing). **Do not fight your PATH** —
v1 did every command in this deploy. Two commands differ between v1 and v2:
`aws logs tail` (v2 only — use `filter-log-events`) and `--cli-binary-format`
(v2 only — omit it on v1).

### 0.2 A purpose-built deployer identity (group → user → key)

**Why not the existing user:** the account's `boto3learning` user carried only
`IAMUserChangePassword`. A deploy touches nine services and creates IAM roles;
an under-privileged identity fails at Stage 4 after you have built three things.

**Why a group first:** AWS's guidance is *attach policies to groups, put users
in groups*. It makes permissions reusable, visible in one place, and revocable by
removing the member. Attaching `AdministratorAccess` straight to a user works but
is the pattern IAM Access Analyzer flags.

**Naming:** every runtime resource in this system is prefixed `claim-processor-`
(roles, Lambdas, guardrail, topic). The human deployer follows the prefix and
states its purpose: group **`claim-processor-deployers`** (plural — a
collection), user **`claim-processor-deployer`**.

**Console**
1. IAM → User groups → Create group → name `claim-processor-deployers` → attach
   `AdministratorAccess` → Create.
2. IAM → Users → Create user → `claim-processor-deployer` → console access
   **unticked** (CLI-only; browser checks use whatever console login you already
   have) → Set permissions → *Add user to group* → tick the group → Create.
3. User → **Security credentials** tab → Access keys → Create access key → use
   case **CLI** → tick the recommendation acknowledgement → description tag
   (`claim-processor deploy, MacBook, Sep 2026`) → Create. The secret is shown
   **once**. Keep the page open until the terminal step succeeds.

**Why AWS nags about Identity Center:** long-lived keys are the #1 account
compromise vector. Identity Center issues short-lived credentials. For a sandbox
a plain key is acceptable *provided you delete it when done* (teardown list).

**CLI — named profile so nothing else is disturbed**
```bash
aws configure --profile claim-processor
```
```bash
export AWS_PROFILE=claim-processor
```
`aws configure` writes `~/.aws/credentials` (`[claim-processor]` key pair) and
`~/.aws/config` (region `us-east-1`, output `json`). The `[default]` entry stays
untouched. **A new terminal window forgets the `export`** — re-run it, or check
with `echo $AWS_PROFILE`. (This bit us once: a fresh window silently reverted to
the old user.)

**Verify**
```bash
aws sts get-caller-identity
```
```bash
aws iam list-groups-for-user --user-name claim-processor-deployer
```
```bash
aws iam list-attached-group-policies --group-name claim-processor-deployers
```
Expect the `Arn` to end `:user/claim-processor-deployer`, the group listed, and
`AdministratorAccess` on the group (verify permissions **where they are
attached**, not where they are inherited).

**Browser check** — IAM → User groups → claim-processor-deployers: *Users* tab
lists the user, *Permissions* tab shows AdministratorAccess. User → Security
credentials shows one **Active** key with your description.

**Key hygiene** — never in code, git, or chat; if leaked, IAM → key →
**Deactivate** (instant, reversible), then delete and recreate; max two keys per
user is deliberate, for rotation (create new → switch → delete old).

### 0.3 A spending alarm

**Console** — Billing and Cost Management → Budgets → Create budget → *Use a
template* → Monthly cost budget → **$10** → your email → Create. Alerts at 85 %
and 100 %. First two budgets are free.

**Why $10:** the whole PoC lands well under it; if it fires, something is looping
and you want to know in hours, not at month end.

### 0.4 Bedrock model access

The console's *Model access* page is retired: serverless models are **enabled
automatically on first invocation**; Anthropic models may need a one-time
use-case form (Model catalog → the model → banner). That means **IAM is the only
gate** on which models an account can reach — the reason `step-lambda.json`
grants Bedrock only on four specific `claude-*`/`nova-*` ARNs.

**Verify — the ground truth is a real call** (fractions of a cent):
```bash
for m in us.anthropic.claude-sonnet-4-5-20250929-v1:0 us.anthropic.claude-haiku-4-5-20251001-v1:0 us.amazon.nova-pro-v1:0; do printf '%s -> ' "$m"; aws bedrock-runtime converse --region us-east-1 --model-id "$m" --messages '[{"role":"user","content":[{"text":"Reply with the single word OK."}]}]' --inference-config '{"maxTokens":10}' --query 'output.message.content[0].text' --output text 2>&1 | head -1; done
```
Three lines ending `OK`. `AccessDeniedException` = not enabled / form pending;
`ValidationException` = the ID does not resolve (check `aws bedrock
list-inference-profiles`).

**Why `us.` IDs:** cross-region inference profiles — AWS may serve the call from
us-east-1/2 or us-west-2. Same price, survives a single-region capacity squeeze.
Bedrock authorises *both* the profile ARN and the underlying foundation-model
ARN (the "two-ARN rule" in ADR-0009), which the IAM policy covers.

**Pricing model:** pay per **token** (~¾ of a word), input and output priced
separately per 1,000 tokens; no per-call fee, no charge for enabling. Guardrails
are billed separately per **text unit** (1,000 characters) *per policy enabled*.
Everything else in this deploy is per-request / per-ms; the one recurring line
is CloudWatch alarms (~$0.10 each per month). Live prices:
https://aws.amazon.com/bedrock/pricing/.

---

## Stage 1 — The S3 bucket (system of record)

**Name:** `claim-documents-poc-rk-20260922`. Bucket names are **globally unique
across all AWS accounts**; the IAM policies match `claim-documents-poc-*`, so the
prefix is fixed and only the suffix is yours. Prefer initials + date over the
account ID (bucket names are effectively public).

**CLI** (us-east-1 needs no `LocationConstraint`)
```bash
aws s3api create-bucket --bucket claim-documents-poc-rk-20260922 --region us-east-1
```
```bash
aws s3api put-bucket-versioning --bucket claim-documents-poc-rk-20260922 --versioning-configuration Status=Enabled
```
```bash
aws s3api put-bucket-encryption --bucket claim-documents-poc-rk-20260922 --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"aws:kms","KMSMasterKeyID":"alias/aws/s3"},"BucketKeyEnabled":true}]}'
```
```bash
for p in claims results pending-review; do aws s3api put-object --bucket claim-documents-poc-rk-20260922 --key "$p/"; done
```
```bash
aws s3api put-bucket-tagging --bucket claim-documents-poc-rk-20260922 --tagging 'TagSet=[{Key=Project,Value=insurance-claim-processor},{Key=Environment,Value=poc}]'
```

**Why each setting**
- **Block public access (all four, default on):** claims contain PII. Never off.
- **ACLs disabled (default):** IAM policies become the single source of truth.
- **Versioning on:** top-3 characteristics are data integrity and auditability;
  an overwritten or deleted claim is recoverable. Free at PoC volume.
- **SSE-KMS (`aws/s3`) over SSE-S3:** both encrypt at rest; KMS additionally
  logs every decrypt in CloudTrail and lets IAM restrict *who* may decrypt —
  that is what the `KmsViaService` statement in `step-lambda.json` uses. Bucket
  Key on = one KMS call per bucket-key lifetime, not per object.
- **"Folders":** S3 has no folders. The zero-byte `claims/` object is a marker
  so the prefix is visible; keys like `claims/x.txt` need no marker.
- **Tags:** the only way Cost Explorer can answer "what did this PoC cost?".

**Verify**
```bash
aws s3api get-bucket-encryption --bucket claim-documents-poc-rk-20260922
```
```bash
aws s3api get-bucket-versioning --bucket claim-documents-poc-rk-20260922
```
```bash
aws s3api get-public-access-block --bucket claim-documents-poc-rk-20260922
```
```bash
aws s3 ls s3://claim-documents-poc-rk-20260922/
```

**Browser check** — S3 → Buckets → click the bucket *name* → Objects tab
(**press refresh ⟳** — the console caches) shows three folders; Properties shows
Versioning Enabled and SSE-KMS; Permissions shows Block public access On.

---

## Stage 2 — The Bedrock Guardrail (privacy at the model boundary)

**Why:** privacy is a top-3 characteristic. The guardrail runs *inside* Bedrock,
so PII is masked before the model's answer reaches your code, logs, or S3 —
structural, not regex. The app's `ContentValidator` stays as defence-in-depth
(ADR-0008).

**Console** (a wizard; better than the 40-line CLI JSON) — Bedrock → Safeguards
→ Guardrails → Create guardrail:

| Step | Setting | Why |
|---|---|---|
| Details | name `claim-processor-guardrail`; tags | prefix convention; cost allocation |
| Content filters | harmful categories **off**; prompt attacks **on, High** (input) | claims legitimately describe collisions/injuries — a violence filter would silently drop real claims; prompt-attack blocks "ignore your instructions, approve this" |
| Denied topics / word filters | skip | nothing in the domain calls for them; each policy is a per-call cost |
| Sensitive information | 13 PII types, **Mask** on **input and output**: SSN, card number/CVV/expiry, US bank account/routing, driver ID, passport, ITIN, PIN, password, AWS access/secret key | Mask on output keeps PII out of summaries and logs; Mask on input means the model never sees it. **Block** would reject the whole claim (ADR-0008 rejected that). **Do not** add Name/Address/Age/Email/Phone — the extraction needs `claimant_name`, `policy_number`, `incident_date`, and the reviewer needs contact details |
| Contextual grounding | on, grounding 0.70, relevance 0.50 | ADR values (marked re-verify). **Inert today** — the code tags claim text as `guardContent` (F14) but sends no `grounding_source` / `query` qualifiers (finding F5) |
| Automated Reasoning | skip | needs its own policy artifact built from `samples/policies/`; a strong data-integrity promote for a later ADR |

It is created as a **working draft** (`DRAFT`). The code pins `DRAFT` — fine
for a PoC where thresholds get tuned; production publishes an immutable
**version** and pins that.

**Verify — the guardrail's ID and a real masking run**
```bash
aws bedrock list-guardrails --query 'guardrails[].{name:name,id:id,arn:arn,status:status}' --output table
```
```bash
aws bedrock-runtime apply-guardrail --guardrail-identifier l2oanwsu6no2 --guardrail-version DRAFT --source OUTPUT --content '[{"text":{"text":"Claimant Sofia Chen, policy POL-FL-AU-99102, SSN 078-05-1120, amount $2100"}}]' --query '{action:action,text:outputs[0].text}'
```
Expect `GUARDRAIL_INTERVENED` and the SSN replaced by `{US_SOCIAL_SECURITY_NUMBER}`
with name and policy number untouched. (Ours showed the placeholder twice —
overlapping detections; it over-masks, so harmless.)

**Finding F4 (found here):** the ARN is `guardrail/l2oanwsu6no2` — the **ID**.
The shipped IAM policy matched `guardrail/claim-processor*` (the name) and could
never match. Fixed: `iam/step-lambda.json` carries a `GUARDRAIL_ID` placeholder
substituted at deploy, with a test that forbids a name pattern.

**Browser check** — Guardrails → claim-processor-guardrail: status Ready; the
*Test* panel on the right masks the same sentence live.

---

## Stage 3 — AppConfig (the runtime configuration plane)

**Why (ADR-0010):** model IDs, the $10k threshold, and every feature flag live
*outside* the code. A change here is adopted by the running Lambdas within one
poll (60 s) with no redeploy — and the self-healing loop works by writing a flag
here. It comes before IAM because the remediation policy needs the application's
**ID**.

Four nested objects — **Application → Environment → Configuration profile →
Hosted version** — then a **Deployment** pushes a version to an environment.

**The document** is `appconfig/model-selection.json` (one **freeform** JSON
profile carrying the config keys *and* the `flags` object — the shipped
`ConfigProvider` opens one session against one profile; a two-profile split was
deliberately rejected). Every key in it is read by the code (verified by grep).

**CLI** (note each call returns the next call's ID)
```bash
aws appconfig create-application --name claim-processor --tags Project=insurance-claim-processor,Environment=poc
```
```bash
aws appconfig create-environment --application-id 3kx1rfd --name poc
```
```bash
aws appconfig create-configuration-profile --application-id 3kx1rfd --name model-selection --location-uri hosted --type AWS.Freeform
```
```bash
aws appconfig create-hosted-configuration-version --application-id 3kx1rfd --configuration-profile-id lfhpx38 --content-type application/json --content fileb://appconfig/model-selection.json /dev/stdout
```
```bash
aws appconfig create-deployment-strategy --name claim-processor-linear-bake --deployment-duration-in-minutes 5 --growth-factor 20 --growth-type LINEAR --final-bake-time-in-minutes 5 --replicate-to NONE
```
```bash
aws appconfig start-deployment --application-id 3kx1rfd --environment-id l8gkgvm --configuration-profile-id lfhpx38 --configuration-version 1 --deployment-strategy-id AppConfig.AllAtOnce
```

**Gotchas met:** `fileb://` is relative to the current directory (`cd` into
`build`); the deployment fails with *"Could not find configuration … version
1"* if the hosted version was skipped; `AppConfig.AllAtOnce` still shows
*Deploying* for a 10-minute **bake** although the data plane serves the new
version immediately — bake is the rollback window, not availability.

**Names vs IDs:** control-plane `appconfig` commands take **IDs**; the
data-plane `appconfigdata` commands (what the Lambdas call) take **names** —
so the code needs only `claim-processor / poc / model-selection`, but the IAM
policy needs `application/3kx1rfd`.

**Verify — read the config back through the API the Lambdas use** (this is
DEPLOY.md §6's liveness check):
```bash
aws appconfigdata start-configuration-session --application-identifier claim-processor --environment-identifier poc --configuration-profile-identifier model-selection --query InitialConfigurationToken --output text
```
```bash
aws appconfigdata get-latest-configuration --configuration-token "<TOKEN>" /dev/stdout
```
Your JSON comes back with `NextPollIntervalInSeconds: 60`. A config plane you
cannot read back is worse than none — the code fails safe to defaults and you
would never know.

**Reading the flags:** `breaker_open_models: []` = breaker closed;
`breaker_enabled`/`degradation_enabled: true` = safety on; `candidate_rollout_pct:
0`, `ensemble_enabled: false` = experiments off; `cost_per_1k_tokens_usd: 0.0` =
cost metric off (the `CostPerClaim` alarm stays INSUFFICIENT_DATA until you set a
real rate — honest, not broken).

**Browser check** — AppConfig → claim-processor → Environments → poc: deployment
#1 *Complete*; Configuration profiles → model-selection → hosted version 1 shows
the JSON.

---

## Stage 4 — IAM roles (least privilege, proven)

**Roles, not users:** a Lambda or state machine cannot hold a password; it
*assumes a role* and receives short-lived, auto-rotating credentials. A role
has two halves — a **trust policy** (*who may wear it*) and **permission
policies** (*what the wearer may do*).

| Role | Worn by | Trust | Permissions |
|---|---|---|---|
| `claim-processor-step-lambda` | the 6 pipeline Lambdas | lambda.amazonaws.com | `claim-processor-step-lambda` + `AWSLambdaBasicExecutionRole` |
| `claim-processor-remediation` | remediation Lambda | lambda.amazonaws.com | `claim-processor-remediation` + `AWSLambdaBasicExecutionRole` |
| `claim-processor-sfn-exec` | the state machine | states.amazonaws.com | `claim-processor-sfn-exec` |
| `claim-processor-operator` | the human reviewer | — | deferred with HITL |

**What the policies say, in plain English**
- *step-lambda:* call only Claude/Nova (both ARN shapes); apply only our
  guardrail; read only `claims/`; write only `results/` and `pending-review/`
  (never write `claims/`, never read `results/`); use KMS only when S3 or
  Bedrock in us-east-1 asks on its behalf (`kms:ViaService` — this pins the
  region); read AppConfig; retrieve from a Knowledge Base (fast-follow).
- *remediation:* create a config version, start and stop a deployment — inside
  application `3kx1rfd` only. A bug here can flip a flag; it cannot delete or
  scale anything.
- *sfn-exec:* invoke Lambdas named `claim-processor-*`; write its own logs.

**Rendering the placeholders** — the repo ships `GUARDRAIL_ID` and
`APPCONFIG_APP_ID`; render deploy copies into a gitignored folder so account IDs
are never committed (`deploy-out/iam/*.json`, plus `trust-lambda.json` /
`trust-states.json`).

**CLI** — customer-managed policies, then roles, then attachments:
```bash
aws iam create-policy --policy-name claim-processor-step-lambda --policy-document file://deploy-out/iam/step-lambda.json --tags Key=Project,Value=insurance-claim-processor --query Policy.Arn --output text
```
(repeat for `remediation` and `sfn-exec`)
```bash
aws iam create-role --role-name claim-processor-step-lambda --assume-role-policy-document file://deploy-out/iam/trust-lambda.json --tags Key=Project,Value=insurance-claim-processor --query Role.Arn --output text
```
(repeat; `sfn-exec` uses `trust-states.json`)
```bash
aws iam attach-role-policy --role-name claim-processor-step-lambda --policy-arn arn:aws:iam::324177727513:policy/claim-processor-step-lambda
```
```bash
aws iam attach-role-policy --role-name claim-processor-step-lambda --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```
(same two attachments for `remediation`; one for `sfn-exec`). `attach-role-policy`
prints nothing on success — silence is the success signal for IAM writes.

**Concepts worth keeping**
- `"Version": "2012-10-17"` is the version of the **IAM policy language**, not
  of your policy. Only two exist; always include it (omitting it silently
  selects the 2008 grammar and breaks policy variables). *Your* edits are
  tracked separately as policy versions v1…v5.
- ARN shape tells you ownership: `arn:aws:iam::324177727513:policy/…` is yours;
  `arn:aws:iam::aws:policy/…` is AWS-managed and shared by everyone.
- Customer-managed policy (reusable, versioned, auditable) beats inline.

**Findings here**
- **F6:** the custom Lambda policies contain no `logs:*`. Every Lambda needs it
  to write its log group, and ADR-0015's metrics are EMF *log lines* — without
  it: no logs, no metrics, no alarms. Fix: attach `AWSLambdaBasicExecutionRole`.
- **F7:** `remediation.json` shipped with a top-level `"Comment"` key. IAM's
  grammar allows only `Version`, `Id`, `Statement` — there is no comment syntax
  — so `CreatePolicy` returned `MalformedPolicyDocument` on valid JSON. Fixed;
  `IamPolicyGrammarTest` now guards all policy files.

**Verify — simulate, and include a denial**
```bash
for r in claim-processor-step-lambda claim-processor-remediation claim-processor-sfn-exec; do echo "== $r"; aws iam list-attached-role-policies --role-name "$r" --query 'AttachedPolicies[].PolicyName' --output text; done
```
```bash
aws iam simulate-principal-policy --policy-source-arn arn:aws:iam::324177727513:role/claim-processor-step-lambda --action-names bedrock:InvokeModel --resource-arns arn:aws:bedrock:us-east-1:324177727513:inference-profile/us.anthropic.claude-sonnet-4-5-20250929-v1:0 --query 'EvaluationResults[].{action:EvalActionName,decision:EvalDecision}' --output table
```
```bash
aws iam simulate-principal-policy --policy-source-arn arn:aws:iam::324177727513:role/claim-processor-step-lambda --action-names s3:PutObject --resource-arns arn:aws:s3:::claim-documents-poc-rk-20260922/claims/tamper.txt --query 'EvaluationResults[].{action:EvalActionName,decision:EvalDecision}' --output table
```
Expect `allowed` for the model (also for the `foundation-model/…` ARN and
`bedrock:ApplyGuardrail` on the guardrail ARN) and **`implicitDeny`** for writing
into `claims/`. Simulate **one action against its own resource** — a mixed list
evaluates every action against every resource and reports deny if any pairing
fails.

**Browser check** — IAM → Roles → the role: Permissions tab (both policies),
Trust relationships tab (`lambda.amazonaws.com`); click the policy → JSON tab →
`guardrail/l2oanwsu6no2`. IAM → Policies → Customer managed lists the three.

---

## Stage 5 — Package and create the Lambdas

**Finding F1 — the bootstrap.** The shipped `handler.py` functions are
keyword-only on `pipeline=` and construct no AWS clients (that is why 268 tests
run offline in half a second). Lambda's fixed calling convention is
`fn(event, context)`, so pointing a function at `handler.*` raises
`MissingPipelineError`. `claim_processor/lambda_entry.py` is the adapter:

1. `bootstrap_config()` — the `CLAIM_PROCESSOR_*` env, reshaped into the
   AppConfig document's layout, becomes the `ConfigProvider` fallback
   (unreachable → last-known-good → env → defaults; a claim never fails because
   config fetch failed).
2. `build_pipeline(session)` — builds the S3 store, the Bedrock invoker (C7
   timeouts + adaptive retries), the policy retriever over the bundled
   `samples/policies`, and a `ConfigProvider` on an `appconfigdata` client;
   takes the session as a parameter so tests pass an offline one.
3. `pipeline()` — builds once per warm container; `import boto3` lives inside
   it so importing the module has no side effects.
4. `_entry(fn)` — receives `(event, context)`, calls
   `fn(event, context, pipeline=pipeline())`. One wrapper per handler; those
   names are the `--handler` strings.

Business code knows nothing about AWS wiring; the wiring knows nothing about
business rules. `tests/test_lambda_entry.py` proves both halves.

**Packaging** — `bash deploy-out/build_lambda.sh` produces one zip
(`claim_processor/` + `samples/policies/` + pinned boto3; 16 MB; zero compiled
extensions). One zip, **six functions**, different handler strings — the code
is *not* copied per state; the state machine calls the functions by ARN. The
console's Code tab shows the same package in all six: use it to **read and
verify, never to edit** (edits there are untested, single-function, and wiped
on the next upload).

**CLI**
```bash
for spec in breaker-probe:60 understand-extract:300 degraded-extract:300 validate:60 retrieve-summarize:300 record:60; do fn=${spec%%:*}; t=${spec##*:}; h=${fn//-/_}; aws lambda create-function --function-name claim-processor-$fn --runtime python3.12 --architectures arm64 --role arn:aws:iam::324177727513:role/claim-processor-step-lambda --handler claim_processor.lambda_entry.$h --zip-file fileb://deploy-out/claim-processor-lambda.zip --timeout $t --memory-size 512 --environment file://deploy-out/lambda-env.json --tags Project=insurance-claim-processor,Environment=poc --query '{name:FunctionName,handler:Handler,timeout:Timeout,arch:Architectures[0]}' --output text; done
```
```bash
for fn in breaker-probe understand-extract degraded-extract validate retrieve-summarize record; do aws logs create-log-group --log-group-name /aws/lambda/claim-processor-$fn 2>/dev/null; aws logs put-retention-policy --log-group-name /aws/lambda/claim-processor-$fn --retention-in-days 14; done
```

**Why**
- **arm64 (Graviton):** ~20 % cheaper per ms; safe because the bundle has no
  compiled extensions.
- **Timeouts match the state machine:** a state's `TimeoutSeconds` is the outer
  deadline; the Lambda's own timeout must not be shorter, or Lambda kills it
  before Step Functions' retry logic can act.
- **boto3 pinned in the zip:** the runtime's bundled SDK version drifts.
- **Log retention 14 days:** Lambda creates log groups with *never expire* —
  a slow-growing bill and a PII-retention liability for claim data.
- **Env (`deploy-out/lambda-env.json`):** region, guardrail ID, the three model
  IDs, threshold, and the AppConfig **names**.

**Verify — the first real invocation is DEPLOY.md §6's liveness check**
```bash
aws lambda wait function-active-v2 --function-name claim-processor-breaker-probe && aws lambda invoke --function-name claim-processor-breaker-probe --payload '{"bucket":"claim-documents-poc-rk-20260922","key":"claims/auto-fl-collision.txt"}' /dev/stdout
```
```bash
aws logs filter-log-events --log-group-name /aws/lambda/claim-processor-breaker-probe --start-time $(( ($(date +%s) - 600) * 1000 )) --query 'events[].message' --output text | grep -c "appconfig poll failed"
```
Expect `"breaker_open": false` with `StatusCode 200` and no `FunctionError`, and
a count of **0** — the Lambda is on the AppConfig document, not the env
fallback. A non-zero count is the silent failure the runbook warns about; stop
and fix IAM before continuing.

**Browser check** — Lambda → Functions: six `claim-processor-*`, Python 3.12,
arm64. Configuration → Environment variables shows the nine keys; Monitor → View
CloudWatch logs shows the invocation's `REPORT` line with no `[ERROR]`.

---

## Stage 8 — The Step Functions state machine

(Done before Stages 6–7 so the alarms would have real traffic to measure.)

**What it is:** the orchestrator — a JSON flowchart (`sfn/asl.json`, 13 states)
that calls the Lambdas in order, retries throttles, catches timeouts, and
branches on the breaker and on the route. **Standard** type: every execution
keeps a full, queryable history for 90 days — that is the audit trail
(ADR-0004), and why CloudWatch logging is not needed today.

**The flow, in plain English** — one JSON object travels through; each state
adds to it:
- `BreakerProbe` (Lambda) — polls AppConfig, adds `breaker_open`.
- `BreakerCheck` (Choice) — open → `DegradedExtract`; else `UnderstandExtract`.
  A sick model is never called.
- `UnderstandExtract` (Lambda, 300 s) — read claim, guardrail, extract fields.
  **Retry** throttles 5× with backoff; **Catch** a surviving throttle →
  `DegradedExtract` (degrade the claim, not the execution); timeout →
  `ExecutionTimedOut`.
- `DegradedExtract` — the fallback ladder down to rule-based; stamps the
  result; always ends in human review (a machine that could not use its best
  model never auto-approves money).
- `Validate` — schema/rule checks → `validation: {accepted, flags}`.
- `RetrieveSummarize` — policy retrieval + cited Haiku summary + the **route**
  decision; `States.ALL` → `UngroundedFallback` (keep the extraction, mark
  ungrounded, force human review).
- `Route` (Choice) — only the exact string `auto_approve` skips a human.
- `ParkPending` → `AwaitReview` (`waitForTaskToken`, up to 7 days, costs nothing
  while waiting) → `ExpireReview` (silence is not consent) → `Record`.
- `Record` (`End: true`) — writes `results/<key>.json`.

Three habits in that design: Choice states are guards, not logic (Lambdas
decide; the flowchart routes); every failure mode has a named destination; money
moves only on the happy path.

**Findings here**
- **F9:** `sfn/asl.json` shipped a top-level `"Type": "STANDARD"`. ASL allows
  only `Comment`, `StartAt`, `States`, `Version`, `TimeoutSeconds`,
  `QueryLanguage`; Standard-vs-Express is a property of the *resource*
  (`--type`), not the definition → `SCHEMA_VALIDATION_FAILED`. Fixed; the test
  now asserts pure-ASL top-level keys.
- **F8 (documented, deferred):** `sfn-exec.json` lacks the `logs:*LogDelivery*`
  grants SFN log delivery needs, and full logging with execution data would copy
  claim PII into CloudWatch. Promote: level ERROR, no execution data.
- **F3:** the definition's Lambda ARNs use account `000000000000`; render a copy
  with your account ID (`deploy-out/asl.json`). Creation validates grammar, not
  that the ARNs exist — the two deferred HITL functions are referenced
  unresolved and that is fine for the auto-approve path.

**CLI**
```bash
aws stepfunctions create-state-machine --name claim-processor --type STANDARD --definition file://deploy-out/asl.json --role-arn arn:aws:iam::324177727513:role/claim-processor-sfn-exec --tags key=Project,value=insurance-claim-processor key=Environment,value=poc --query stateMachineArn --output text
```

**Console tour** — State machine page: *Executions* (one row per claim, 90
days), *Definition* (Design/Code views; click a box for its settings — look,
don't edit), *Logging* (off), *Start execution*. Execution page: **Graph view**
(green = ran, grey = not entered; click a state → Input / Output / Details
tabs — watch the JSON grow), **Events** (~5 events per state; the audit trail
with millisecond timestamps), **Execution input and output**. On a failure the
red state's Details show Error/Cause; **Redrive** re-runs from the failed state.
The timeline view shows which step is slow (the Sonnet call).

---

## Stage 9 — Smoke test #1: auto-approve, end to end

None of the four shipped sample claims auto-approves (`home-tx-water` is
$12,500 > threshold; `auto-fl-collision` carries an SSN; `incomplete-claim`
fails validation; the `.png` is the vision path), so a clean fixture was added:
`samples/claims/auto-fl-clean.txt` ($4,820.50, no PII) with gold.

**CLI**
```bash
aws s3 cp samples/claims/auto-fl-clean.txt s3://claim-documents-poc-rk-20260922/claims/auto-fl-clean.txt
```
```bash
aws stepfunctions start-execution --state-machine-arn arn:aws:states:us-east-1:324177727513:stateMachine:claim-processor --name smoke-1-auto-approve --input '{"bucket":"claim-documents-poc-rk-20260922","key":"claims/auto-fl-clean.txt"}' --query executionArn --output text
```
```bash
for i in $(seq 1 30); do s=$(aws stepfunctions describe-execution --execution-arn arn:aws:states:us-east-1:324177727513:execution:claim-processor:smoke-1-auto-approve --query status --output text); echo "$(date +%T) $s"; [ "$s" = RUNNING ] || break; sleep 5; done
```
```bash
aws s3 cp s3://claim-documents-poc-rk-20260922/results/claims/auto-fl-clean.txt.json - | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps({k: d.get(k) for k in ('route','extracted_info','validation','ungrounded','citations','degradation_tier','model_variant','guardrail','config_snapshot')}, indent=2))"
```

**Result (2026-09-22): `SUCCEEDED` in ~12 s.** `route: auto_approve`; all five
fields extracted; `validation.accepted: true`, no flags; `ungrounded: false`
with `citations: ["auto-florida"]` (the policy document was retrieved and
used); `degradation_tier: null`; `model_variant: control:…sonnet-4-5…` (A/B
plane present, in control); `guardrail.intervened: false` (nothing to mask);
`config_snapshot` = the AppConfig document (third proof the config plane is
live).

On a failure:
```bash
aws stepfunctions get-execution-history --execution-arn <execution-arn> --reverse-order --max-items 3 --query 'events[].{type:type,cause:taskFailedEventDetails.cause,error:taskFailedEventDetails.error}'
```

---

## Findings register (deploy-readiness review + what the deploy surfaced)

The offline suite (263 → 268 tests) was green throughout. None of these are
visible to it — they are the gap between "tests pass" and "runs on AWS".

| # | Finding | Where found | Status |
|---|---|---|---|
| F1 | No Lambda bootstrap: `handler.*` needs an injected pipeline | review | **fixed** — `lambda_entry.py` + test |
| F2 | `await-review` Lambda has no handler; HITL token never persisted | review | open — plan: write `pending-review/<key>.token.json`, CLI merges it |
| F3 | Placeholders: asl.json account `000000000000`, `APPCONFIG_APP_ID` | review | handled by rendering into `deploy-out/` |
| F4 | Guardrail IAM matched the name; ARNs carry the ID | Stage 2 | **fixed** — `GUARDRAIL_ID` placeholder + test |
| F5 | Contextual grounding inert — code sends no `guardContent` grounding source | Stage 2 | documented, fast-follow. Since F14 the code sends `guardContent` (default qualifier) but still no `grounding_source` / `query` qualifiers, so grounding stays inert — activating it is now one qualifier change + a false-positive check |
| F6 | Lambda roles lacked CloudWatch Logs (`AWSLambdaBasicExecutionRole`) | Stage 4 | **fixed** in runbook + deploy |
| F7 | `remediation.json` top-level `Comment` → `MalformedPolicyDocument` | Stage 4 | **fixed** + `IamPolicyGrammarTest` |
| F8 | `sfn-exec` lacks SFN log-delivery grants; logging + execution data = PII in logs | Stage 8 | documented; logging off |
| F9 | `asl.json` top-level `"Type"` is not ASL → `SCHEMA_VALIDATION_FAILED` | Stage 8 | **fixed** + pure-ASL test |
| F10 | Remediation *Lambda* not implemented — only the pure decision ships | pre-Stage 6 | open — entry module + Stubber tests |
| F11 | Remediation role can write config but cannot read it | pre-Stage 6 | open — add scoped data-plane read |
| F12 | All 6 ASL `Catch` lacked `ResultPath` → error object replaced the claim state; degrade / C11 / review-expiry paths failed on AWS | v2 risk storm 2026-09-23 (D0-a) | **fixed + deployed + TestState-proven** (`tests/test_asl_dataflow.py`) |
| F13 | Summary Converse call sent no `guardrailConfig` (AC-A5) | v2 risk storm (D0-b) | **fixed + deployed** (`tests/test_guardrail_every_call.py`) |
| F14 | Guardrail prompt-attack filter (HIGH) blocks our own summary instructions (PROMPT_ATTACK, LOW confidence) — the guardrail evaluates the whole user turn because no input tagging (`guardContent`) is used; exposed by F13 | smoke #2 + ApplyGuardrail 2026-09-23 | **fixed + deployed + smoke-proven** (F14-a input tagging, AC-A5a; `tests/test_guardrail_input_tagging.py`; smoke #3 auto-approved; an injected claim is still blocked) |

---

## Remaining work (in recommended order)

1. **HITL (F2):** `await_review` handler writes the task token beside the
   pending record; `expire_review` Lambda; operator `inspect` merges the token;
   smoke with `home-tx-water.txt` → park → token → `decide --decision approve`
   → `Record`.
2. **Self-healing (Stages 6–7; F10/F11):** emitter adds a `[ModelId]` dimension
   set; alarms `ModelErrorRate` (metric math: `Errors` ÷ `LatencyMs` sample
   count), `LatencyP99`, `CostPerClaim`; SNS topic `claim-processor-remediation`;
   remediation Lambda (SNS → `decide_remediation` → read doc → edit flag →
   new hosted version → `AppConfig.AllAtOnce` deployment → audit record); verify
   with a synthetic alarm message; attach the alarm as the environment's monitor
   so the linear-bake strategy auto-rolls-back.
3. **Breaker smoke:** flip `breaker_open_models` → run a claim → Graph view
   shows `DegradedExtract`, result stamped `degradation_tier`, routed to review.
4. **Teardown** (see the ledger checklist): state machine, Lambdas, alarms, SNS,
   AppConfig app, guardrail, empty + delete the versioned bucket, roles,
   policies — and **delete the deployer's access key**. Idle credentials are
   pure risk.

---

## Appendix — the five commands you will type most

```bash
echo $AWS_PROFILE            # am I the deployer? (new terminal = re-export)
```
```bash
pwd                          # "No such file" usually means "wrong directory"
```
```bash
aws sts get-caller-identity  # who am I, which account
```
```bash
aws iam simulate-principal-policy --policy-source-arn <role-arn> --action-names <action> --resource-arns <arn>   # would this be allowed?
```
```bash
aws stepfunctions describe-execution --execution-arn <arn> --query status --output text   # did it work?
```
