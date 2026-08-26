---
type: research
title: AWS AI capability research — Bedrock, SageMaker, agents, boto3, deploy (2025–2026)
description: >-
  External research synthesis backing the aws-ai-* skill family: current Amazon
  Bedrock (Converse API, AgentCore, Knowledge Bases/RAG, Guardrails, embeddings),
  Amazon SageMaker AI (SDK V2/V3, Pipelines, endpoints), agent frameworks
  (Strands / AgentCore / MCP), AWS CDK-Python deployment, and the offline boto3
  testing strategy (botocore Stubber / moto / LocalStack). Feeds the aws-ai-*
  skill family that supplements arch-*.
tags: [aws, bedrock, sagemaker, agentcore, strands, boto3, cdk, moto, research, aws-ai-skill]
---

# AWS AI capability research (2025–2026)

**Provenance.** Deep-research run 2026-08-12 for the `aws-ai-*` skill family
(supplements the `arch-*` architect family). Five parallel research agents,
cross-checked against official AWS sources (`docs.aws.amazon.com`, boto3/botocore
reference, `aws.amazon.com/blogs`, `github.com/awslabs`, `github.com/strands-agents`,
`docs.getmoto.org`, `docs.localstack.cloud`), current through **August 2026**.
`⚠️` marks things that changed recently and are easy to get wrong.

> **Time sensitivity.** Model IDs, AgentCore CLI verbs, and CDK L2 graduation move
> monthly. Prefer dynamic resolution (`list_foundation_models`,
> `list_inference_profiles`) and version pins over hardcoded constants. Re-verify
> fast-moving items at authoring time.

## Contents
1. [Amazon Bedrock](#1-amazon-bedrock)
2. [Amazon SageMaker AI](#2-amazon-sagemaker-ai)
3. [Agent frameworks + CDK-Python deployment](#3-agent-frameworks--cdk-python-deployment)
4. [boto3, offline testing, security & cost](#4-boto3-offline-testing-security--cost)
5. [Design implications for the aws-ai-* family](#5-design-implications-for-the-aws-ai-family)
6. [Sources](#6-sources)

---

## 1. Amazon Bedrock

### 1.1 The six boto3 clients (control vs runtime split is strict — the #1 beginner error)

| `boto3.client(...)` | Plane | Owns |
|---|---|---|
| `bedrock` | control | `list_foundation_models`, model access, **guardrails** (`create_guardrail`, `create_guardrail_version`), provisioned throughput, inference profiles (`list_inference_profiles`, `create_inference_profile`), customization/fine-tuning jobs, **batch** (`create_model_invocation_job`), eval jobs |
| `bedrock-runtime` | inference | `converse`, `converse_stream`, `invoke_model`, `invoke_model_with_response_stream`, **`apply_guardrail`** (creation is on `bedrock`; standalone apply is here), `start_async_invoke`/`get_async_invoke` |
| `bedrock-agent` | control | **classic** Agents (`create_agent`, `create_agent_action_group`, `prepare_agent`, `create_agent_alias`), **Knowledge Bases** (`create_knowledge_base`, `create_data_source`, `start_ingestion_job`), Flows, Prompt Management |
| `bedrock-agent-runtime` | runtime | `invoke_agent`, `invoke_inline_agent`, **KB retrieval** (`retrieve`, `retrieve_and_generate`, `retrieve_and_generate_stream`), `invoke_flow`, `rerank`, agent memory/sessions |
| `bedrock-agentcore-control` ⚠️ NEW | control | AgentCore CRUD: `create_agent_runtime`, `create_memory`, `create_gateway`, `create_gateway_target`, `create_workload_identity`, `create_code_interpreter`, `create_browser` |
| `bedrock-agentcore` ⚠️ NEW | data plane | `invoke_agent_runtime`, `invoke_code_interpreter`, `start_browser_session`, Memory events (`create_event`, `retrieve_memory_records`), `get_workload_access_token` |

`bedrock-mantle` ⚠️ NEW is an OpenAI-compatible `/v1/chat/completions` **endpoint**
(exposes non-native models like GPT-5.x on Bedrock), not a boto3 client.

### 1.2 Model invocation — Converse API is the default

Use **Converse** (`converse`/`converse_stream`) as the default: it's provider-agnostic,
so `modelId` swaps across Claude, Nova, Llama, Mistral, Cohere without rewriting
request/response parsing. Use `invoke_model` only for **embeddings**, **image
generation**, or model-specific params (via `additionalModelRequestFields`).

```python
import boto3
client = boto3.client("bedrock-runtime", region_name="us-east-1")
resp = client.converse(
    modelId="us.anthropic.claude-sonnet-4-5-20250929-v1:0",  # id | inference-profile id | ARN
    messages=[{"role": "user", "content": [{"text": "Hello"}]}],  # roles: user | assistant
    system=[{"text": "You are concise."}],                         # SEPARATE top-level param — NOT a message role
    inferenceConfig={"maxTokens": 1024, "temperature": 0.2, "topP": 0.9},
)
text = resp["output"]["message"]["content"][0]["text"]
# resp["stopReason"] ∈ end_turn | tool_use | max_tokens | stop_sequence | guardrail_intervened | content_filtered
# resp["usage"] = {inputTokens, outputTokens, totalTokens}; resp["metrics"] = {latencyMs}
```

Content block types (one key per block): `text`, `image`, `document`, `video`,
`toolUse`, `toolResult`, `guardContent`, `cachePoint`, `reasoningContent`.
⚠️ NEW: `cachePoint` (prompt caching, ttl `"5m"`|`"1h"`), `performanceConfig={"latency":"optimized"}`,
`serviceTier` (`standard|priority|flex|reserved`), `outputConfig.textFormat.type="json_schema"`
(structured outputs), `promptVariables`.

**Streaming** — iterate `converse_stream(...)["stream"]`: events `messageStart`,
`contentBlockDelta` (`delta.text`), `contentBlockStop`, `messageStop` (`stopReason`),
`metadata` (usage/metrics).

### 1.3 Tool use / function calling via Converse — the gotchas are load-bearing

```python
tool_config = {
  "tools": [{"toolSpec": {
      "name": "get_weather", "description": "Get weather for a city.",
      "inputSchema": {"json": {  # JSON Schema wrapped under literal key "json"
          "type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}}],
  "toolChoice": {"auto": {}}}   # or {"any": {}} or {"tool": {"name": "get_weather"}}

messages = [{"role": "user", "content": [{"text": "Weather in Paris?"}]}]
resp = client.converse(modelId=MODEL, messages=messages, toolConfig=tool_config)
if resp["stopReason"] == "tool_use":
    assistant_msg = resp["output"]["message"]     # role == assistant, has toolUse block(s)
    messages.append(assistant_msg)                # 1) echo assistant turn back VERBATIM first
    req = next(b["toolUse"] for b in assistant_msg["content"] if "toolUse" in b)
    messages.append({"role": "user", "content": [{"toolResult": {
        "toolUseId": req["toolUseId"],
        "content": [{"json": {"tempC": 18}}],     # 2) content is a LIST of blocks: {"json":...}|{"text":...}
        "status": "success"}}]})                  #    a bare string is INVALID
    final = client.converse(modelId=MODEL, messages=messages, toolConfig=tool_config)
```
- `toolResult.content` **must be a list of blocks**; `toolUse.input` is already a parsed dict (no `json.loads`).
- Append the assistant's `toolUse` turn **before** the user `toolResult` turn or validation fails.
- Loop until `stopReason == "end_turn"`; a turn may carry multiple `toolUse` blocks → one `toolResult` per `toolUseId`.

### 1.4 Classic Bedrock Agents (legacy path)

`create_agent(agentName, foundationModel, agentResourceRoleArn, instruction)` →
`create_agent_action_group(agentId, agentVersion="DRAFT", actionGroupExecutor={"lambda":arn} | {"customControl":"RETURN_CONTROL"}, apiSchema | functionSchema)` →
`[associate_agent_knowledge_base]` → `prepare_agent` (recompile DRAFT after **every** change) →
`create_agent_alias` → runtime `invoke_agent(agentId, agentAliasId, sessionId, inputText)` (streams `completion` chunks).
`invoke_inline_agent` needs no pre-created resource.

### 1.5 Amazon Bedrock AgentCore ⚠️ NEW (GA 2025-10-13) — the strategic direction

Framework/model-agnostic **production agent platform** (Strands, LangGraph, CrewAI,
LlamaIndex, Google ADK, OpenAI Agents SDK, Claude Agent SDK). Classic Agents =
managed Bedrock-model agent + action groups; **AgentCore = infra to host/operate
*any* agent code** (up to 8h, Instances up to 14-day sessions) plus modular services.

Services (GA): **Runtime** (serverless microVM, session isolation; deploy via
container, Direct Code Deploy `.zip`, or Instances compute; AG-UI, WebSocket
streaming, A2A), **Memory** (short/long-term; semantic/summary/episodic),
**Gateway** (APIs/Lambda/OpenAPI/**MCP** → agent tools; IAM/OAuth; guardrails at
gateway), **Identity** (OAuth2/API-key vault, `@requires_access_token`),
**Observability** (CloudWatch + OTEL/ADOT), **Built-in Tools** (Code Interpreter,
Browser). Adjacent NEW: **Policy** (Cedar), **Evaluations** (13 evaluators, GA
Mar 2026), **Harness**, **Managed Knowledge Base** (June 2026), **Payments** (preview),
**Agent Registry**.

```python
# pip install bedrock-agentcore
from bedrock_agentcore.runtime import BedrockAgentCoreApp
app = BedrockAgentCoreApp()
@app.entrypoint
async def handler(request):
    prompt = request.get("prompt")
    if not isinstance(prompt, str):   # ⚠️ SECURITY: a toolUse block sneaked in as prompt bypasses guardrails
        raise ValueError("prompt must be a string")
    async for event in MyAgent().stream_async(prompt):
        yield event
app.run()                             # serves POST /invocations + GET /ping on :8080
```
Invoke: `boto3.client("bedrock-agentcore").invoke_agent_runtime(agentRuntimeArn, runtimeSessionId=<uuid ≥33 chars>, payload=json.encode, qualifier="DEFAULT")`.
⚠️ With OAuth inbound auth you **cannot** use the SDK — make a raw HTTPS request.
`RetryableConflictException` (409) is auto-retried.

⚠️ **Two conflicting `agentcore` CLIs** — the pip `bedrock-agentcore-starter-toolkit`
(`agentcore configure/launch/invoke`) is now **legacy**; the npm **`@aws/agentcore`**
(`github.com/aws/agentcore-cli`; `agentcore create/dev/deploy/invoke/add memory|identity|gateway`)
is the forward path. Both register the `agentcore` command → uninstall the pip one first.

### 1.6 Knowledge Bases (RAG)

Authoring (`bedrock-agent`): `create_knowledge_base(name, roleArn, knowledgeBaseConfiguration={"type":"VECTOR","vectorKnowledgeBaseConfiguration":{"embeddingModelArn":...}}, storageConfiguration={...})`
→ `create_data_source(..., vectorIngestionConfiguration={"chunkingConfiguration":{...}})` → `start_ingestion_job`.

- Vector stores: `OPENSEARCH_SERVERLESS`, ⚠️ **`S3_VECTORS`** (GA Dec 2025, ~90% cheaper than OSS's ~$345/mo idle 2-OCU minimum), `RDS` (Aurora **pgvector**), `PINECONE`, `MONGO_DB_ATLAS`, `REDIS_ENTERPRISE_CLOUD`, `NEPTUNE_ANALYTICS` (GraphRAG).
- Chunking: `FIXED_SIZE`, `HIERARCHICAL`, `SEMANTIC`, `NONE`, custom-Lambda.

```python
rt = boto3.client("bedrock-agent-runtime")
res = rt.retrieve(knowledgeBaseId=KB, retrievalQuery={"text": q},
    retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 5, "overrideSearchType": "HYBRID"}})
out = rt.retrieve_and_generate(input={"text": q},
    retrieveAndGenerateConfiguration={"type": "KNOWLEDGE_BASE",   # or EXTERNAL_SOURCES (docs inline, no KB)
        "knowledgeBaseConfiguration": {"knowledgeBaseId": KB, "modelArn": MODEL_ARN,
            "generationConfiguration": {"guardrailConfiguration": {"guardrailId": GID, "guardrailVersion": "1"}}}})
# out["output"]["text"], out["citations"]; pass out["sessionId"] for multi-turn
```
Also `retrieve_and_generate_stream`. `promptTemplate.textPromptTemplate` must include `$search_results$`.
AgentCore's **Managed Knowledge Base** (June 2026) is a separate, newer fully-managed RAG offering.

### 1.7 Guardrails

`create_guardrail(...)` (on `bedrock`) → `guardrailId` (DRAFT); `create_guardrail_version` publishes immutable.
- Content filters: `HATE|INSULTS|SEXUAL|VIOLENCE|MISCONDUCT|PROMPT_ATTACK` × `NONE|LOW|MEDIUM|HIGH`.
- Denied topics (`DENY`), word filters, **PII** (`piiEntitiesConfig`: `EMAIL|PHONE|US_SSN|CREDIT_DEBIT_CARD_NUMBER|NAME`, action `BLOCK|ANONYMIZE` + `regexesConfig`), **contextual grounding** (`GROUNDING` + `RELEVANCE` thresholds — the anti-hallucination check for RAG).
- Apply: (1) inline `guardrailConfig={guardrailIdentifier, guardrailVersion, trace:"enabled"}` on `converse`/`invoke_model`; (2) standalone **`apply_guardrail`** (`bedrock-runtime`) to screen any system's I/O:
```python
r = boto3.client("bedrock-runtime").apply_guardrail(
    guardrailIdentifier=GID, guardrailVersion="1", source="INPUT",   # INPUT | OUTPUT
    content=[{"text": {"text": user_text, "qualifiers": ["query"]}}], outputScope="FULL")
# r["action"] ∈ NONE | GUARDRAIL_INTERVENED | ANONYMIZED
```
Billed per ~1000-char text unit per policy.

### 1.8 Embeddings (`invoke_model` only; no streaming)

- **Titan Text Embeddings V2** `amazon.titan-embed-text-v2:0`: dims 256/512/**1024** (default), `body={"inputText","dimensions","normalize","embeddingTypes":["float"|"binary"]}`. In-region only (no cross-region profile).
- **Cohere Embed** v3 (`cohere.embed-english-v3` / `-multilingual-v3`, 1024); ⚠️ **v4** `cohere.embed-v4:0` (Oct 2025) multimodal, dims 256–1536. `body={"texts","input_type": REQUIRED "search_document"|"search_query"|..., "embedding_types","truncate"}`. Gotcha: `input_type` mismatch degrades retrieval.

### 1.9 Operational

- **Model access**: opt-in per region, or ⚠️ NEW **Bedrock API keys** (`AWS_BEARER_TOKEN_BEDROCK`). No access → `AccessDeniedException`.
- **Cross-region inference profiles**: invoke a profile id (prefixes `us.`/`eu.`/`apac.`/⚠️`global.`), not a bare model id, for ~2× throughput. ⚠️ **Many newer models are inference-profile-only** — a bare id returns `ValidationException` ("on-demand not supported… use an inference profile").
- **Provisioned throughput** (committed capacity) vs on-demand; **batch inference** ~50% cheaper; **prompt caching** ⚠️ 1-hour TTL (Jan 2026), ~90% off cached input.
- **Exceptions**: `AccessDeniedException` (fix access, not retryable), `ThrottlingException` (429, retryable w/ backoff — `Config(retries={"mode":"adaptive"})`), `ValidationException` (bad request, not retryable), `ModelStreamErrorException`/`ModelTimeoutException` (may retry), `ServiceQuotaExceededException`, `ModelNotReadyException`.
- Limits (Converse): images ≤20/msg (≤3.75 MB), documents ≤5/msg (≤4.5 MB), user turns only.

---

## 2. Amazon SageMaker AI

### 2.1 Two big flags

- ⚠️ **Rebrand**: the classic build/train/deploy product is now **"Amazon SageMaker AI"** (`docs.aws.amazon.com/sagemaker/latest/dg/`). "Amazon SageMaker" (no *AI*) is the umbrella data+analytics+AI platform (Unified Studio + Lakehouse + governance). The skill scopes to **SageMaker AI**; treat Unified Studio/Lakehouse as the surrounding data plane.
- ⚠️ **SDK V2 vs V3 split**: SageMaker Python SDK **V3.0.0 shipped 2025-11-19**, hard backward-incompatible. `Estimator`/`Model`/`Predictor` + all framework subclasses **removed** → replaced by `ModelTrainer` (`sagemaker.train`) and `ModelBuilder` (`sagemaker.serve`). No compat shim. **Recommendation: author against V2-stable baseline with a clearly-flagged V3 section; version-pin examples (`pip install "sagemaker<3"` vs `>=3`).**

### 2.2 Training

- **V2**: `sagemaker.estimator.Estimator` (BYO/built-in); framework estimators `sagemaker.pytorch.PyTorch`, `.huggingface.HuggingFace`, `.sklearn.SKLearn`, `.xgboost.XGBoost`, `.tensorflow.TensorFlow`. `estimator.fit({"train": "s3://..."})`. Distributed via `distribution=`.
- **V3**: `sagemaker.train.ModelTrainer` (one universal class) + config objects (`sagemaker.train.configs.InputData`).
- boto3: `sagemaker` client `create_training_job` / `describe_training_job`.

### 2.3 Pipelines (the ML-pipeline backbone) — `sagemaker.workflow.*`

`Pipeline(name, parameters, steps, sagemaker_session)`. Parameters:
`ParameterString/Integer/Float/Boolean`. Steps: `ProcessingStep`, `TrainingStep`,
`TransformStep`, `TuningStep`, `ModelStep` (modern replacement for `CreateModelStep`/`RegisterModel`),
`ConditionStep`, `FailStep`, plus `LambdaStep`, `CallbackStep`, `EMRStep`, `AutoMLStep`,
`QualityCheckStep`, `ClarifyCheckStep`. Data deps via property refs
(`step_train.properties.ModelArtifacts.S3ModelArtifacts`); `PropertyFile` + `JsonGet` for
metric-gated conditions. Lifecycle: `pipeline.upsert(role_arn=...)` (idempotent, preferred),
`pipeline.start(parameters=...)`, `pipeline.definition()`. Idiom: `step_args=processor.run(...)`.
boto3: `create_pipeline`, `start_pipeline_execution`. ⚠️ Gotcha: a step in a `ConditionStep`'s
if/else must **not** also appear in top-level `Pipeline(steps=...)`.

### 2.4 Model registry & MLOps

`model.register(model_package_group_name=..., inference_instances=[...], transform_instances=[...], approval_status="PendingManualApproval")` — ⚠️ `inference_instances`/`transform_instances` effectively required.
Approval: `PendingManualApproval | Approved | Rejected` (`update_model_package`). Common pattern:
Processing → Training → Eval → `ConditionStep`(metric) → `ModelStep(register, gated)`. Lineage auto-tracked;
MLflow on SageMaker now serverless. SageMaker Projects = MLOps CI/CD templates.

### 2.5 Inference / endpoints — four types

| Type | Use when | Limits |
|---|---|---|
| Real-time | interactive, steady, low-latency | persistent; **scale-to-zero** via inference components; 60s, 6 MB |
| Serverless | spiky, tolerate cold start | pay-per-use, no idle charge; 1–6 GB mem, ~6 MB |
| Asynchronous | large payload / long processing | up to 1 GB payload, 1 h; S3 in/out; scale to zero |
| Batch transform | score whole dataset offline | no endpoint; results to S3 |

Deploy (V2): `model.deploy(instance_type=..., serverless_inference_config=ServerlessInferenceConfig(), async_inference_config=AsyncInferenceConfig(...), endpoint_type=EndpointType.INFERENCE_COMPONENT_BASED)`.
`ModelBuilder` (`sagemaker.serve`) is the AWS-recommended modern path (only path in V3).
Runtime (`sagemaker-runtime`): `invoke_endpoint(EndpointName, Body, ContentType, InferenceComponentName=)`,
`invoke_endpoint_with_response_stream(...)`, `invoke_endpoint_async(InputLocation=<s3>)`.
**Inference components** = multiple models per endpoint, independently scalable; **scale-to-zero**
(GA 2025) only with inference-component-based endpoints.

### 2.6 JumpStart

`sagemaker.jumpstart.model.JumpStartModel(model_id=..., instance_type=...).deploy(accept_eula=True)`;
`JumpStartEstimator` for fine-tune. **Bedrock vs SageMaker/JumpStart** (AWS decision guide):
Bedrock = serverless per-token, API-only, fast FM/RAG/agents, has Claude/Nova; SageMaker = self-hosted
endpoints, full cost/latency control, custom training. Progressive path: Bedrock → SageMaker serverless
customization → training/HyperPod. Custom SageMaker models can be **imported into Bedrock**.

### 2.7 Deprecations / new (2025–2026)

Studio Classic EOL 2024-12-31 (kernels off 2025-02-01) → new Studio (JupyterLab 4). SDK V2→V3.
SageMaker→SageMaker AI rename. K8s Operators v1 EOS. New: scale-to-zero (GA), serverless MLflow,
**HyperPod** (checkpointless/elastic training, task governance, KV caching), serverless model
customization (SFT/DPO/RLVR/RLAIF), Nova Forge.

---

## 3. Agent frameworks + CDK-Python deployment

### 3.1 Strands Agents SDK (AWS open-sourced May 2025; 1.0 GA 2025)

```bash
pip install strands-agents strands-agents-tools
```
```python
from strands import Agent, tool
agent = Agent()                    # defaults to Amazon Bedrock
print(agent("What is AWS Lambda?").message)
```
- **Model-driven loop** (LLM drives each iteration) vs graph-first (LangGraph). `@tool` decorator: docstring + type hints → schema; `@tool(context=True)` → `tool_context.invocation_state`.
- Providers (`strands.models`): `BedrockModel(model_id=<inference-profile-id>)` default; Anthropic/OpenAI/Gemini/LiteLLM/Ollama/Mistral.
- **Multi-agent** (`strands.multiagent`): **Swarm** (peer handoffs), **Graph** (deterministic DAG), Agents-as-Tools (wrap child `Agent` in `@tool`), **Workflow** tool, A2A.
- **MCP**: `from strands.tools.mcp import MCPClient; MCPClient(lambda: stdio_client(StdioServerParameters(command="uvx", args=["awslabs.aws-documentation-mcp-server@latest"])))`. Also `streamablehttp_client`/`sse_client`; `tool_filters`, `prefix` namespacing.
- **Strands authors; AgentCore deploys** — orthogonal choices.

### 3.2 AgentCore deploy paths

- **Path A (SDK + starter toolkit)**: wrap in `BedrockAgentCoreApp` `@app.entrypoint`; `agentcore configure -e agent.py; agentcore launch; agentcore invoke '{"prompt":...}'`. Starter toolkit is **legacy** → new `agentcore-cli` (`create/dev/deploy/invoke`); verbs drifted (`launch`↔`deploy`) → pin version, check `--help`.
- **Path B (BYO container + boto3)**: ARM64 image serving `/invocations`+`/ping` on 8080 → ECR → `bedrock-agentcore-control.create_agent_runtime(agentRuntimeArtifact.containerConfiguration.containerUri, networkConfiguration, roleArn)` → data-plane `invoke_agent_runtime`. Observability: `pip install aws-opentelemetry-distro`, run under `opentelemetry-instrument`.

### 3.3 MCP on AWS

`awslabs/mcp` (`uvx awslabs.<name>@latest`): `aws-documentation-mcp-server`, AWS Knowledge, AWS IaC
(CFN+CDK), AWS Serverless (SAM), `lambda-mcp-server` (expose Lambdas as tools), AgentCore MCP server,
DB servers. Two distinct Lambda projects: **`run-mcp-servers-with-aws-lambda`** (host a stdio MCP server
in Lambda) vs **`lambda-tool-mcp-server`** (bridge MCP clients to your Lambdas). Protocol: Streamable HTTP
(replaced HTTP+SSE 2025-03), OAuth 2.1 resource-binding (2025-06). AgentCore Gateway = managed
MCP-ification of Lambda/OpenAPI. LangGraph/CrewAI/LlamaIndex are first-class on AgentCore.

### 3.4 CDK v2 (Python) essentials

`aws-cdk-lib` (v2 single package), Python ≥3.10. CLI (`npm i -g aws-cdk`): `cdk init app --language python`,
`cdk bootstrap`, `cdk synth`, `cdk deploy`, `cdk diff`, `cdk destroy`. Layout: `app.py`, `cdk.json`,
`requirements.txt`, `.venv/`, `<proj>/<proj>_stack.py`. Idioms: `import aws_cdk as cdk`;
`import aws_cdk.aws_s3 as s3`; ⚠️ **`import aws_cdk.aws_lambda as lambda_`** (`lambda` is a keyword);
`from constructs import Construct`. Alpha modules = separate `aws-cdk.aws-<svc>-alpha` packages.

### 3.5 Lambda-based agent (CDK)

```python
from aws_cdk import Stack, Duration, aws_lambda as lambda_, aws_iam as iam
fn = lambda_.DockerImageFunction(self, "AgentFn",
    code=lambda_.DockerImageCode.from_image_asset("agent"),  # dir with Dockerfile; up to 10 GB
    architecture=lambda_.Architecture.ARM_64, memory_size=1024, timeout=Duration.minutes(5),
    environment={"BEDROCK_MODEL_ID": "us.anthropic.claude-sonnet-4-5-..."})
fn.add_to_role_policy(iam.PolicyStatement(
    actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
    resources=[f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-*",
               f"arn:aws:bedrock:{self.region}:{self.account}:inference-profile/us.anthropic.claude-*"]))
fn.add_function_url(auth_type=lambda_.FunctionUrlAuthType.AWS_IAM)
```
Zip = 250 MB limit (boto3 preinstalled); container = 10 GB (agent frameworks usually exceed zip → container).
⚠️ Cross-region inference profiles need `foundation-model/*` allowed in **every** region the profile spans.
Long loops → `timeout` max 15 min; longer → AgentCore Runtime, not Lambda.

### 3.6 Bedrock CDK constructs — changed a lot (flag prominently)

- `aws-cdk-lib.aws_bedrock` (stable): **L1 only** — `CfnKnowledgeBase`, `CfnDataSource`, `CfnAgent`, `CfnGuardrail`.
- `@aws-cdk/aws-bedrock-alpha` (`aws-cdk.aws-bedrock-alpha`): experimental L2s; ⚠️ **KB + DataSource L2s still in progress Aug 2026** (aws/aws-cdk#36592).
- `aws-cdk-lib.aws_bedrockagentcore` (native, mostly stable): L2 `Runtime`, `Gateway`/`GatewayTarget`, `Memory`, `BrowserCustom`, `CodeInterpreterCustom`, credential providers. Policy submodule alpha. ⚠️ **Verify import: `from aws_cdk import aws_bedrockagentcore`** (not `aws_bedrock_agent_core`).
- `awslabs/generative-ai-cdk-constructs` (`cdklabs.generative_ai_cdk_constructs`): richest KB/Agent L2 today but ⚠️ **Bedrock submodule deprecated**, migrating to `aws-bedrock-alpha`.
- **Guidance:** AgentCore infra → native `aws_bedrockagentcore`; Bedrock KB/Agents → `generative-ai-cdk-constructs` (deprecated) **or** L1 `Cfn*` **or** `custom_resources.AwsCustomResource` calling boto3 `bedrock-agent`.

### 3.7 AI pipelines: Step Functions (CDK)

`aws_stepfunctions` (`sfn`) + `aws_stepfunctions_tasks` (`tasks`). Tasks: `SageMakerCreateTrainingJob/TransformJob/ProcessingJob/Model/Endpoint`, `BedrockInvokeModel`, `LambdaInvoke`, and ⚠️ **`CallAwsService`** for SageMaker Pipelines `startPipelineExecution` (no dedicated task). `IntegrationPattern`: `REQUEST_RESPONSE`, `RUN_JOB` (`.sync`), `WAIT_FOR_TASK_TOKEN`. ⚠️ **`StateMachine(definition=)` deprecated → `definition_body=DefinitionBody.from_chainable(chain)`**. Trigger via `events.Rule(schedule=Schedule.cron(...), targets=[targets.SfnStateMachine(machine)])`.

### 3.8 Packaging heavy Python for Lambda

boto3/botocore preinstalled (don't bundle). Layers ≤5/fn, 250 MB unzipped ceiling.
`PythonFunction` (`aws-cdk.aws-lambda-python-alpha`) auto-bundles from `requirements.txt` but **requires
Docker at synth**. Container image (10 GB) = the answer for ML stacks. SnapStart (Python 3.12+, GA Nov
2024) = zip only, not container. Build wheels `manylinux`/AL2; prefer ARM64.

---

## 4. boto3, offline testing, security & cost

### 4.1 boto3 best practices

- Prefer explicit `session = boto3.Session(profile_name=, region_name=)` then `session.client(...)`. Clients thread-safe (reuse for pooling); resources are not.
- `botocore.config.Config(region_name, retries={"mode":"adaptive"|"standard"|"legacy"(default), "max_attempts":5}, connect_timeout(60), read_timeout(60 — ⚠️ RAISE to 300+ for Bedrock streaming), max_pool_connections(10 — raise for concurrency), tcp_keepalive=True)`. `adaptive` = standard + client-side rate limiting (good for Bedrock throttling; don't stack with your own retry loop).
- **Credential chain** (high→low): explicit client args → `Session` args → env vars → assume-role (config `role_arn`+`source_profile`, auto-refreshing — prefer over manual `sts.assume_role`) → web-identity (IRSA) → SSO → shared creds → config → container creds → IMDS. `AWS_PROFILE` selects a profile.
- Pagination: `client.get_paginator("op").paginate(...)`. Waiters: `client.get_waiter("endpoint_in_service").wait(...)`. Bedrock/SageMaker/STS = **client only** (no resource). Errors: `except ClientError as e: e.response["Error"]["Code"]`.

### 4.2 Offline-testing coverage matrix (the crown jewel — drives the harness design)

| Capability | moto `@mock_aws` (~5.1) | LocalStack (2026.03) | botocore `Stubber` |
|---|---|---|---|
| `bedrock` control plane | ✅ | ✅ Ultimate | ✅ |
| `bedrock-runtime` `invoke_model` | ❌ | ✅ Ultimate (via Ollama) | ✅ |
| `bedrock-runtime` `converse`/`converse_stream` | ❌ | ✅ Converse (Ultimate) | ✅ (`converse`; stream hard) |
| `sagemaker` control (endpoints, models, **training**, **pipelines**, tuning, processing) | ✅ broad | ⚠️ partial (no training, no Pipelines) | ✅ |
| `sagemaker-runtime` `invoke_endpoint` | ✅ | ✅ | ✅ |
| Supporting infra (S3/IAM/Lambda/StepFunctions/SNS/SQS/DynamoDB/KMS/STS/SecretsMgr/ECR/CloudWatch) | ✅ strong | ✅ (core free "Hobby") | ✅ (use moto instead) |

- ⚠️ **`moto` cannot mock `bedrock-runtime`** (`invoke_model`/`converse`) → **botocore `Stubber` is the only pure-unit option** for Bedrock inference. `moto` covers bedrock control-plane + sagemaker control-plane (incl. `create_pipeline`, `create_training_job`) + `sagemaker-runtime.invoke_endpoint`.
- `moto` v5 unified: `from moto import mock_aws; @mock_aws`. Set dummy creds + region.
- **LocalStack**: Bedrock + SageMaker = **Ultimate tier only**, needs Docker; Bedrock via **Ollama**; SageMaker custom-image endpoints only (no training/Pipelines). ⚠️ Community image discontinued 2026-03-23; free **Hobby** ≈ old Community (Lambda/S3/DDB/SQS/SNS/IAM/SecretsMgr). Wire `endpoint_url` only in test config, never prod.
- **botocore `Stubber`** = fallback for Bedrock/SageMaker-runtime contract tests; validates response against the service model (a good *contract* test):
```python
from botocore.stub import Stubber, ANY
with Stubber(client) as s:
    s.add_response("converse", {"output": {"message": {"role": "assistant", "content": [{"text": "Hi"}]}},
        "stopReason": "end_turn", "usage": {"inputTokens": 12, "outputTokens": 3, "totalTokens": 15},
        "metrics": {"latencyMs": 100}}, expected_params={"modelId": ANY, "messages": ANY})
    ...  # exercise code
    s.assert_no_pending_responses()
# error injection: s.add_client_error("converse", service_error_code="ThrottlingException", http_status_code=429)
```
- **Layered strategy**: Stubber (Bedrock/SM-runtime contract) → moto (infra + SM control plane) → LocalStack Ultimate (integration) → real AWS (smoke, gated).

### 4.3 Static validation without AWS

`cdk synth` (offline; runs Aspects/cdk-nag). `cfn-lint template.yaml` (E=error/W=warn/I=info; validates SAM too).
`cdk-nag` (`pip install cdk-nag`; `AwsSolutionsChecks`/HIPAA/NIST/PCI Aspects; `AwsSolutions-IAM5` wildcards,
unencrypted, public exposure; suppress via `NagSuppressions`). Type-check: `pip install 'boto3-stubs[bedrock-runtime,sagemaker,sagemaker-runtime,s3]'` + `mypy`/`pyright` catches wrong params/keys/return-shapes before runtime.

### 4.4 Security & cost

- **IAM invoke Bedrock**: `Allow bedrock:InvokeModel/InvokeModelWithResponseStream` on specific `foundation-model` + `inference-profile` ARNs (not `*`). ⚠️ foundation-model ARN has **no account id**; provisioned/custom/inference-profile ARNs do. Condition `bedrock:GuardrailIdentifier` (2025-04-09) forces a guardrail.
- **IAM SageMaker pipeline role**: `sagemaker:Create*`, scoped `s3:GetObject/PutObject`, `ecr` read, `logs`, `kms` Decrypt/GenerateDataKey, and ⚠️ **`iam:PassRole` on the exact exec-role ARN (`Condition iam:PassedToService sagemaker.amazonaws.com`)**. Runtime invoker: just `sagemaker:InvokeEndpoint` on the specific endpoint ARN. Avoid `AmazonSageMakerFullAccess`.
- **VPC/PrivateLink**: bedrock interface endpoints `com.amazonaws.<region>.bedrock{,-runtime,-agent,-agent-runtime}`; sagemaker `.api`/`.runtime`. Combine with `aws:sourceVpce` IAM conditions.
- **Cost**: Bedrock on-demand vs provisioned (break-even at sustained high volume); batch 50% off; prompt caching ~90% off cached input; cost allocation by IAM principal + inference-profile tags → Budgets per team. SageMaker real-time endpoints bill per instance-hour (main trap) → scale-to-zero (`ManagedInstanceScaling.MinInstanceCount=0`, needs inference components), prefer serverless/async, delete idle endpoints.
- **AWS Well-Architected** — both lenses **revised 2025-11-19**: **Generative AI Lens** (6 GenAI-specialized pillars incl. excessive-agency security, RAG perf, prompt cost-engineering; covers Bedrock + SageMaker + Q) and **Machine Learning Lens** (traditional ML lifecycle on SageMaker AI; data drift/retraining). Use the GenAI Lens for FM/RAG/agents, the ML Lens for custom-trained models — these are the natural fitness-function / checklist source for `arch-validate`.

---

## 5. Design implications for the aws-ai-* family

1. **Strands + AgentCore is the modern agent spine** (matches the `cases/aws-ai` corpus and AWS's strategic direction). Classic `bedrock-agent` Agents = secondary/legacy. `bedrock-runtime` Converse = default model access.
2. **Real gaps the skill must fill with fresh, executed code** (corpus has prose/references only): SageMaker (train→pipeline→endpoint), CDK-Python deploy (Lambda agent, Step Functions AI pipeline, AgentCore), Bedrock KB/RAG via boto3, the Converse tool-use loop, Guardrails apply.
3. **Verification spine = botocore `Stubber` (Bedrock/SM-runtime contract) + `moto` (infra + SM control plane) + `cdk synth`/`cfn-lint`/`cdk-nag` (IaC static) + `mypy`/`boto3-stubs`.** LocalStack = opt-in (Docker + Ultimate). Matches the container reality (Docker daemon down; `moto`/`cdk`/`cfn-lint` installable via pip/npm).
4. **Fast-moving → resolve dynamically & pin**: model IDs (`list_foundation_models`/`list_inference_profiles`), the two conflicting `agentcore` CLIs, CDK L2 graduation, SageMaker SDK V2 vs V3.

*(The corpus coverage map — an inventory of `cases/aws-ai` and `cases/aws` — is maintained separately and refreshed after each corpus reorg; see the companion inventory.)*

---

## 6. Sources

**Bedrock** — boto3 bedrock-runtime / bedrock-agent / bedrock-agentcore reference; Converse & tool-use (`docs.aws.amazon.com/bedrock/latest/userguide/tool-use-*`); KB (`knowledge-base-create`, `retrieve_and_generate`); Guardrails (`apply_guardrail`, `create_guardrail`); Titan/Cohere embeddings model cards; cross-region inference; AgentCore devguide + release notes; `github.com/aws/bedrock-agentcore-sdk-python`, `github.com/aws/agentcore-cli`, `github.com/awslabs/amazon-bedrock-agentcore-samples`.

**SageMaker AI** — `docs.aws.amazon.com/sagemaker/latest/dg/` (whatis, pipelines, model-registry, realtime/serverless/async endpoints, inference-components, endpoint-auto-scaling, scale-to-zero, jumpstart, studio-migrate); `sagemaker.readthedocs.io` (V3 ModelTrainer/ModelBuilder; V2 estimators/pipelines); `github.com/aws/sagemaker-python-sdk` (V3 breaking changes, CHANGELOG); Bedrock-or-SageMaker decision guide.

**Agent frameworks + CDK** — `strandsagents.com` (quickstart, multi-agent, mcp-tools, deploy); AWS ML/OSS blogs (Strands deep dive, Strands 1.0); `docs.aws.amazon.com/bedrock-agentcore` (what-is, starter-toolkit, runtime); `github.com/awslabs/mcp`; `docs.aws.amazon.com/cdk/v2/guide` (python, getting-started); CDK API ref (`aws_lambda`, `aws_bedrock`, `aws_bedrockagentcore`, `aws_stepfunctions_tasks`); `github.com/aws/aws-cdk/issues/36592`; `github.com/awslabs/generative-ai-cdk-constructs`; Lambda layers/SnapStart docs.

**boto3 / testing / security** — boto3 retries & credentials guides; `botocore` Config & Stubber reference; `docs.getmoto.org` (bedrock, sagemaker, sagemaker-runtime coverage) + `IMPLEMENTATION_COVERAGE.md`; `docs.localstack.cloud` (bedrock, sagemaker) + 2026 pricing/packaging; `github.com/cdklabs/cdk-nag`; `cfn-lint` rules; `boto3-stubs`/`mypy-boto3`; Bedrock IAM policy examples + least-privilege blog; Bedrock VPC/PrivateLink; SageMaker scale-to-zero & autoscaling IAM; AWS Well-Architected **Generative AI Lens** and **Machine Learning Lens** (both revised 2025-11-19).

*Full URL list retained in the working research notes; re-verify fast-moving items (model IDs, CLI verbs, CDK L2 status) at authoring time.*
