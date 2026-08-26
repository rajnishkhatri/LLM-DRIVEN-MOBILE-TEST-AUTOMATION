# boto3 foundations — client, IAM/security/cost, offline test strategy

The shared boto3 + security + verification substrate for the whole aws-ai-*
family. Every stage cites it; **aws-ai-build** leans on §1–2, **aws-ai-deploy**
on §3–5, and **aws-ai-validate** treats §6 as its harness spec. The external
authority for every fast-moving fact here is
`{{research_home}}/aws-ai-bedrock-sagemaker-research.md` **§4** (boto3, offline
testing, security & cost); the sibling digest `research-2026.md` distills it.
Corpus (`{{methodology_source}}` = `cases/aws-ai`, `{{methodology_secondary}}` =
`cases/aws`) supplies the reusable IAM JSON; everything Bedrock-runtime-native and
every test is code the family runs itself, because the corpus never wrote it.

> **Re-verify before trusting a constant.** Retry-mode names, endpoint-service
> DNS names, moto's coverage table, and CDK-nag rule ids all move. Prefer dynamic
> resolution (`list_foundation_models`, `list_inference_profiles`, a `Stubber`
> validated against the live service model) over pasted values, and re-open §4 of
> the research doc when a number looks load-bearing.

## Contents
1. [Session, client, resource, Config, credential chain](#1-session-client-resource-config-credential-chain)
2. [Pagination, waiters, error handling](#2-pagination-waiters-error-handling)
3. [IAM least-privilege — the two-ARN Bedrock trap](#3-iam-least-privilege--the-two-arn-bedrock-trap)
4. [VPC endpoints / PrivateLink](#4-vpc-endpoints--privatelink)
5. [Cost guardrails](#5-cost-guardrails)
6. [The offline test strategy (load-bearing for aws-ai-validate)](#6-the-offline-test-strategy-load-bearing-for-aws-ai-validate)

---

## 1. Session, client, resource, Config, credential chain

**Prefer an explicit `Session`, reuse clients, never share resources across
threads.** A `boto3.Session(profile_name=..., region_name=...)` pins credentials
and region in one object so a process can hold more than one identity without
mutating global state; `session.client("bedrock-runtime")` then reads from it.
Clients are thread-safe and hold the connection pool, so **build one per service
and reuse it** — re-creating clients per call throws the pool away and re-walks
the credential chain each time. Resources (`boto3.resource(...)`) are *not*
thread-safe, and the AI services you care about — `bedrock*`, `sagemaker`,
`sagemaker-runtime`, `sts` — are **client-only** (no resource interface exists),
so the resource/client question rarely arises here.

**`botocore.config.Config` is where you tune retries and timeouts — set it
deliberately, do not inherit the defaults for Bedrock.** The defaults assume a
short request/response; agent and streaming calls are neither.

```python
import boto3
from botocore.config import Config

cfg = Config(
    region_name="{{region_default}}",
    retries={"mode": "adaptive", "max_attempts": 5},  # default mode is "legacy"
    connect_timeout=10,     # default 60s — TCP handshake; fail fast on a dead endpoint
    read_timeout=300,       # default 60s — RAISE for Bedrock streaming / long agents
    max_pool_connections=20,  # default 10 — raise under concurrency or you serialize
    tcp_keepalive=True,
)
session = boto3.Session(profile_name="{{aws_profile}}", region_name="{{region_default}}")
brt = session.client("bedrock-runtime", config=cfg)
```

- **`retries.mode`:** `legacy` (the default) retries a small fixed set of errors;
  `standard` broadens the retryable set (adds throttling/timeout codes) and is the
  modern baseline; **`adaptive` = `standard` plus a client-side rate limiter** that
  backs the whole client off when it sees throttling. `adaptive` is the right
  default against Bedrock's `ThrottlingException`, but **do not also wrap calls in
  your own retry loop** — the two limiters fight and you lose the backoff signal.
- **Timeouts:** `read_timeout=60` will sever a legitimate `converse_stream` or a
  multi-minute agent turn mid-flight; treat 300s+ as the floor for anything
  streaming or agentic. Keep `connect_timeout` short so an unreachable endpoint
  surfaces immediately instead of hanging for a minute.

**The credential provider chain, highest priority first** — botocore stops at the
first source that resolves:

1. Explicit `aws_access_key_id`/`aws_secret_access_key` passed to `client()`
2. `Session(...)` constructor args
3. Environment (`AWS_ACCESS_KEY_ID`, …; `AWS_PROFILE` selects a named profile)
4. **Assume-role** in config (`role_arn` + `source_profile`) — botocore
   auto-refreshes these; **prefer this over a hand-rolled `sts.assume_role`** loop,
   which you then have to re-refresh yourself
5. Web-identity / IRSA (`AWS_WEB_IDENTITY_TOKEN_FILE`) — the EKS pod path
6. SSO → shared credentials file → config file → container credentials (ECS) →
   IMDS (EC2 instance role)

For this family the chain matters most as a *discipline*: design and build run
with `{{aws_profile}}` unset (`<none>`) so nothing can reach a real account by
accident; a profile or assumed role only appears at the gated **aws-ai-validate**
real-path.

## 2. Pagination, waiters, error handling

**Never trust a single list response to be complete.** Most `list_*`/`describe_*`
operations truncate and hand back a `NextToken`; the manual token loop is a
recurring bug source. Use the paginator — it hides the token and yields every
page:

```python
sm = session.client("sagemaker", config=cfg)
for page in sm.get_paginator("list_endpoints").paginate(StatusEquals="InService"):
    for ep in page["Endpoints"]:
        ...  # every endpoint, not just the first page
```

The same applies to `bedrock.list_foundation_models` /
`list_inference_profiles` — the model-ID resolution the family insists on (never
hard-code an id) is a paginated call.

**Waiters replace poll loops for state transitions.** SageMaker control-plane
operations are async: `create_endpoint` returns before the endpoint is live.
`client.get_waiter("endpoint_in_service").wait(EndpointName=...)` polls
`describe_endpoint` on the service-defined interval and raises `WaiterError` on
terminal failure — clearer and less brittle than a hand-written `while` loop with
your own `sleep`. (Bedrock inference is synchronous and has no waiters; its
control-plane jobs — batch, customization — do.)

**Error handling is `ClientError` + the error code, not the string.** Message
text is not a contract; `response["Error"]["Code"]` is. Branch on the code and let
retryable classes be retried by `Config`, not by catching-and-swallowing:

```python
from botocore.exceptions import ClientError

try:
    resp = brt.converse(modelId=MODEL, messages=msgs)
except ClientError as e:
    code = e.response["Error"]["Code"]
    if code == "AccessDeniedException":
        raise            # model access / IAM — NOT retryable; fix the grant
    if code == "ThrottlingException":
        raise            # 429 — let adaptive retries handle it; don't hand-loop
    if code == "ValidationException":
        raise            # malformed request (bad modelId, wrong content shape)
    raise
```

The Bedrock-runtime codes worth knowing (research §1.9): `AccessDeniedException`
and `ValidationException` are **not** retryable — fix the cause;
`ThrottlingException` (429) is retryable with backoff and is exactly what
`adaptive` mode is for; `ModelTimeoutException` / `ModelStreamErrorException` may
be retried; `ServiceQuotaExceededException` and `ModelNotReadyException` signal
capacity, not a code bug. A bare model id that returns `ValidationException`
("on-demand not supported… use an inference profile") is the common newer-model
trap — resolve to an inference-profile id, don't retry.

## 3. IAM least-privilege — the two-ARN Bedrock trap

**The single most common Bedrock IAM defect: granting `bedrock:InvokeModel` on
the foundation-model ARN alone.** Any modern model id you actually use starts
`us.` / `eu.` / `apac.` / `global.` — those are **cross-region inference-profile
ids**, and invoking one needs a *second* resource ARN. The corpus states it
plainly in the SAM policy at `cases/aws-ai/ch06.md:72-80`, with the warning
"Two resource types, not one" at `cases/aws-ai/ch06.md:81`:

```json
{
  "Effect": "Allow",
  "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
  "Resource": [
    "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
    "arn:aws:bedrock:*:123456789012:inference-profile/us.anthropic.claude-*"
  ]
}
```

Omit the `inference-profile/*` ARN and you get an `AccessDeniedException` whose
message does **not** say which permission is missing — hours lost to a policy that
"looks complete." Two structural details make it easy to get wrong:

- **The `foundation-model` ARN has no account id** (models are AWS-owned) — note
  the empty `::` segment. Inference-profile, provisioned-throughput, and custom-
  model ARNs *do* carry your account id.
- A cross-region profile spans several regions; **`foundation-model/*` must be
  allowed in every region the profile can route to**, not only your home region
  (research §3.5, §4.4). Scoping `Resource` to a single region silently breaks
  failover.

**The wider least-privilege discipline.** The generic policy shape — the
`Version`/`Effect`/`Action`/`Resource` skeleton scoped to a specific ARN rather
than `*` — is the reusable template at `cases/aws/ch12.md:566-582`. The
Bedrock-specific identity-policy suite (`ListFoundationModels`/`CreateAgent`
broad; then narrowed to a specific agent ARN; then gated by condition keys; then
ABAC by tag; then STS temporary credentials; then a service-role trust policy)
runs across `cases/aws-ai/ch08.md:304-420`. Its explicit rule — **do not attach
`AmazonBedrockFullAccess`; enumerate only the actions the principal needs** — is
at `cases/aws-ai/ch08.md:425`, illustrated by an agent limited to
`PrepareAgent` + `InvokeAgent` at `cases/aws-ai/ch08.md:427-440`. Two SageMaker
specifics the corpus does not cover but the deploy stage needs (research §4.4):

- A **pipeline/execution role** needs `sagemaker:Create*`, tightly scoped
  `s3:GetObject`/`PutObject`, ECR read, CloudWatch `logs`, KMS
  `Decrypt`/`GenerateDataKey`, **and `iam:PassRole` on the exact exec-role ARN
  gated by `Condition {"StringEquals": {"iam:PassedToService":
  "sagemaker.amazonaws.com"}}`** — the passed-role trap that blocks pipeline runs.
- A **runtime invoker** needs only `sagemaker:InvokeEndpoint` on the specific
  endpoint ARN — never `AmazonSageMakerFullAccess`.

The `bedrock:GuardrailIdentifier` condition key (2025-04-09) lets a policy *force*
a guardrail on every invoke — a cheap governance lever worth adding when a
guardrail exists.

## 4. VPC endpoints / PrivateLink

**Keep Bedrock and SageMaker traffic off the public internet with interface VPC
endpoints (PrivateLink).** The corpus frames PrivateLink as the private
alternative to VPC peering at `cases/aws/ch09.md:447`; the concrete endpoint
service names are current-fact material from research §4.4, not the (concept-only)
corpus:

- **Bedrock:** `com.amazonaws.<region>.bedrock`,
  `…bedrock-runtime`, `…bedrock-agent`, `…bedrock-agent-runtime` — one interface
  endpoint per plane you call (control vs runtime vs agent).
- **SageMaker:** `com.amazonaws.<region>.sagemaker.api` (control plane) and
  `…sagemaker.runtime` (`invoke_endpoint`).

The endpoint alone only provides a private *route*; pair it with an IAM
**`aws:sourceVpce`** condition so calls are *rejected* unless they arrive through
your endpoint. The corpus already recommends exactly this — restricting Bedrock
API calls to a specific VPC endpoint via `aws:SourceVpce` — at
`cases/aws-ai/ch08.md:422`. Route + condition together turn "private-capable" into
"private-enforced." Set `endpoint_url` on the client only when you must target a
custom endpoint in test config (see §6); production resolves the endpoint from the
region, and pinning it in prod code is a smell.

## 5. Cost guardrails

AI spend is dominated by two runaway modes — always-on inference capacity and
per-token volume — and both have concrete brakes.

- **Provisioned vs on-demand throughput (Bedrock).** On-demand bills per token
  with no floor; provisioned throughput buys committed model units and only wins
  past a **sustained high-volume break-even** (research §4.4). Default to
  on-demand; move to provisioned only with measured, steady traffic — the reverse
  is a classic over-commit.
- **Batch inference is ~50% cheaper** than on-demand for work that tolerates
  delay — stated outright in the corpus:
  "charged at a 50 percent discount compared to … on-demand usage"
  (`cases/aws-ai/ch10.md:430`). Route bulk, non-interactive jobs (catalog
  summaries, backfills, evals) through `create_model_invocation_job`, not the
  synchronous path.
- **Prompt caching** returns ~90% off cached input tokens (ttl `5m`/`1h`) — high
  leverage for long, stable system prompts and RAG context (research §1.9).
- **SageMaker real-time endpoints bill per instance-hour whether or not they serve
  a request** — the number-one SageMaker cost trap. Mitigate with **scale-to-zero**
  (`ManagedInstanceScaling.MinInstanceCount=0`, which requires inference-component-
  based endpoints), prefer **serverless** or **async** for spiky/large workloads,
  and **delete idle endpoints** (research §2.5, §4.4).
- **Quotas & throttling are a cost/reliability control, not just an error.**
  Bedrock throughput is quota-bounded; exceeding it yields `ThrottlingException`
  (429, absorb with `adaptive` retries) or `ServiceQuotaExceededException` (raise
  via Service Quotas). Tag spend by IAM principal + inference-profile so AWS
  Budgets can alarm **per team** before the invoice does.

None of these are free lunches — provisioned vs on-demand, batch vs real-time, and
serverless vs always-on are trade-offs (latency for cost, or commitment for rate).
Present the cursor position; the human owns the cost call.

## 6. The offline test strategy (load-bearing for aws-ai-validate)

This section **is** the aws-ai-validate harness contract. The default
`{{test_stack}}` is `stubber+moto`: pure-Python, no Docker, no credentials, always
runnable. **`{{localstack}}` is `off` by default** (it needs Docker up, and its
Bedrock/SageMaker support is Ultimate-tier only). Nothing here touches a real
account.

### The coverage matrix — which tool mocks what

| Capability | botocore `Stubber` | moto `@mock_aws` (~5.x) | LocalStack (opt-in) |
|---|---|---|---|
| `bedrock-runtime` `converse` / `invoke_model` | ✅ **only pure-unit path** | ❌ **cannot mock** | ✅ Ultimate (via Ollama) |
| `bedrock-runtime` `converse_stream` | ⚠️ hard (event stream) | ❌ | ✅ Ultimate |
| `bedrock` control plane (guardrails, profiles, batch) | ✅ | ✅ | ✅ Ultimate |
| `sagemaker-runtime` `invoke_endpoint` | ✅ | ✅ | ✅ |
| `sagemaker` control (endpoints, models, **training**, **pipelines**) | ✅ | ✅ broad | ⚠️ partial (no training/Pipelines) |
| S3 / IAM / Lambda / Step Functions / SQS / SNS / DynamoDB / KMS / STS | ✅ (use moto) | ✅ **strong — default here** | ✅ (core "Hobby") |

**The one hard fact that shapes the whole harness:
`moto` cannot mock `bedrock-runtime`** (neither `invoke_model` nor `converse`).
So **botocore `Stubber` is the *only* pure-unit path for Bedrock inference** —
there is no `@mock_aws` shortcut for the Converse call. moto owns everything
around it: the Bedrock control plane, the SageMaker control plane (including
`create_pipeline` and `create_training_job`), `sagemaker-runtime.invoke_endpoint`,
and all supporting infra (research §4.2).

### Stubber — the Bedrock/SageMaker-runtime contract test

`Stubber` queues canned responses onto a real client and validates each response
against the live service model, so a passing stub is also a *contract* check that
your response-parsing matches the API shape. The signature is
`add_response(operation_name, service_response, expected_params)`:

```python
from botocore.stub import Stubber, ANY

with Stubber(brt) as stub:
    stub.add_response(
        "converse",                                    # operation_name
        {                                              # service_response (model-validated)
            "output": {"message": {"role": "assistant",
                                   "content": [{"text": "Hi"}]}},
            "stopReason": "end_turn",
            "usage": {"inputTokens": 12, "outputTokens": 3, "totalTokens": 15},
            "metrics": {"latencyMs": 100},
        },
        expected_params={"modelId": ANY, "messages": ANY},  # asserts the request shape
    )
    result = my_agent_turn(brt)          # exercise the code under test
    stub.assert_no_pending_responses()   # fails if the call never happened

# inject failures to test error paths:
# stub.add_client_error("converse",
#     service_error_code="ThrottlingException", http_status_code=429)
```

`expected_params` is the request-side contract: a wrong `modelId` key or a
malformed `messages`/`toolConfig` block fails the stub before any network call,
which is exactly how you unit-test the Converse tool-use loop offline.
`converse_stream` is the sharp edge — its event-stream response is hard to stub
faithfully; assert on the assembled turn, and cover true streaming at the
LocalStack/real tier.

### moto — infra + the SageMaker control plane

```python
from moto import mock_aws
import boto3

@mock_aws
def test_pipeline_upserts():
    sm = boto3.client("sagemaker", region_name="{{region_default}}")
    sm.create_pipeline(PipelineName="p", RoleArn="arn:aws:iam::123456789012:role/x",
                       PipelineDefinition="{...}")
    assert sm.list_pipelines()["PipelineSummaries"]
```

moto v5 unified everything under `@mock_aws` — set dummy creds + a region so the
credential chain resolves to nothing real. This is the default for S3/IAM/Lambda/
Step Functions plumbing and for the SageMaker control plane; **reach for it first**
and fall back to `Stubber` only where moto can't reach (Bedrock inference,
runtime contract detail).

### LocalStack — opt-in integration tier

Flip `{{localstack}}` to `on` only when you need cross-service integration with
real request routing. Bedrock and SageMaker live in **Ultimate tier**, need Docker,
and back Bedrock with **Ollama**; SageMaker supports custom-image endpoints but
**not** training or Pipelines. Wire `endpoint_url` to LocalStack **in test config
only, never in production code** (research §4.2).

### Static IaC + types — verification that needs no mock at all

Two layers catch defects before any service, real or mocked, is involved:

- **`{{iac_tool}}` static checks:** `cdk synth` renders the template fully offline
  (and runs cdk-nag Aspects); `cfn-lint` validates the synthesized template (and
  SAM); **`cdk-nag`** (`AwsSolutionsChecks`) flags IAM wildcards
  (**`AwsSolutions-IAM5`** — the direct guard against the §3 over-grant),
  unencrypted resources, and public exposure. Legitimate findings are suppressed
  explicitly via `NagSuppressions`, which leaves an audit trail rather than hiding
  the risk.
- **Types:** `pip install 'boto3-stubs[bedrock-runtime,sagemaker,sagemaker-runtime,s3]'`
  plus `mypy`/`pyright` catches wrong parameter names, misspelled response keys,
  and wrong return shapes at author time — the Converse/tool-use dicts are deep and
  easy to shape wrong, and this is where that surfaces.

### The layered order

Run cheapest-and-narrowest first: **Stubber** (Bedrock / SageMaker-runtime
contract) → **moto** (infra + SageMaker control plane) → **static IaC + types**
→ **LocalStack Ultimate** (integration, opt-in) → **real AWS** (smoke only, gated
at aws-ai-validate). The first four run anywhere with no account and no cost;
crossing into the fifth is a deliberate, human-approved step, and any real AWS
call outside it is a defect. Reports land in `{{validate_home}}`.
