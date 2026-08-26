---
type: analysis
title: AWS AI seed-corpus inventory — cases/aws + cases/aws-ai coverage map
description: >-
  Chapter-level coverage map of the two seed-corpus OKF bundles (cases/aws
  "System Design on AWS" and cases/aws-ai "AI Agents on AWS") that back the
  aws-ai-* skill family. Records what each chapter actually supplies (runnable
  code vs concept-only), the two-lineage split inside cases/aws-ai (modern
  Strands+AgentCore vs legacy classic-Bedrock), the real gaps the corpus does
  NOT cover, and how the material maps onto the proposed skill pillars.
tags: [aws, bedrock, sagemaker, agentcore, strands, corpus, inventory, analysis, aws-ai-skill]
---

# AWS AI seed-corpus inventory

**Provenance.** Corpus re-review run 2026-08-12 for the `aws-ai-*` skill family
(supplements the `arch-*` architect family). Four parallel reader agents over the
two seed bundles as they now stand (both freshly re-imported as OKF bundles with
`index.md`/`log.md`). Companion to
[aws-ai-bedrock-sagemaker-research.md](aws-ai-bedrock-sagemaker-research.md) — the
research doc is the external best-practice picture; this doc is the *internal
corpus* picture: what we already have on disk to cite, and where the real gaps are.

This is a **decision-framework corpus, not a copy-paste corpus.** Where code exists
it is inventoried by line range so the skill author can lift it; where it is
concept-only that is stated so the skill author knows to supply fresh executed code.

## The two bundles at a glance

| Bundle | Book | Chapters | Stack / altitude | Runnable AWS code |
|---|---|---|---|---|
| `cases/aws-ai/` | "AI Agents on AWS" (+ a grafted legacy book) | ch01–ch10 | **Two lineages** (see below) | Yes in ch01–07; partial/console in ch08–10 |
| `cases/aws/` | "System Design on AWS" | ch01–ch16, ch19–ch21 | Conceptual / decision-framework | **None** (5 curly-quote snippets total, no boto3/CDK/CLI) |

## `cases/aws-ai/` — "AI Agents on AWS" (the AI/ML corpus)

**⚠️ Critical structural finding: this bundle is two different books stitched
together, on two incompatible API generations.** The skill family must treat them
as distinct lineages, not one continuum.

- **ch01–ch07 → modern lineage** (`PacktPublishing/AI-Agents-on-AWS`): **Strands
  Agents SDK + Bedrock AgentCore**, Claude Sonnet 4 / Haiku 4.5 inference profiles,
  code-rich and IaC-quality. This is the spine the `aws-ai-agents` skill should
  follow.
- **ch08–ch10 → legacy lineage** (`renaldig/Using-Amazon-Bedrock`): **classic
  "Agents for Amazon Bedrock" + raw `botocore` + AWS-Console click-through.** No
  Strands, no AgentCore, no Cedar. Valuable for IAM/KMS JSON and security
  frameworks; hazardous as a code model (deprecated `create_agent`/`create_guardrail`,
  `\n\nHuman:`/`max_tokens_to_sample` completion format against a Sonnet-4 id).

### ch01–ch05 — agent fundamentals (modern lineage)

The hands-on/tutorial half of the modern book. Code density rises across the five
(runnable completeness roughly **ch05 > ch02 > ch03 > ch04 > ch01**); ch01 is a
near-code-free primer, ch02–05 own the reusable agent-authoring snippets while
ch06–07 own runtime/deploy/observability. The **`@tool` decorator contract**
(function + type hints + docstring → agent tool, ch02 L89–104) is the atomic
building block that recurs in every chapter — the family should standardize on it.

- **ch01 — Understanding AI Agents** → `aws-ai-foundations`. Conceptual: RAG-vs-agents,
  the AWS Agentic Stack, a **Bedrock-vs-SageMaker decision table (L128–148)**, MCP/A2A
  intro. Only runnable bit is a zero-config `Agent()` (L433–438). Low code value;
  strong for the stack taxonomy the foundations skill needs.
- **ch02 — Building Agents With Tools** → `aws-ai-agents` (core). Rich, runnable:
  `@tool` decorator (L89–104); multi-tool agent (L126–140); `strands_tools` prebuilts
  (`calculator`, `http_request`, `use_aws`); **`use_aws` S3/DynamoDB/Lambda bridge
  (L384–416)**; class-based shared-connection tools (L516–532); async parallel tool
  (L556–572). Model `us.anthropic.claude-sonnet-4-20250514-v1:0`. Canonical
  tool-authoring reference — richer on tool internals than ch06–07.
- **ch03 — Agent Memory** → `aws-ai-bedrock` + `aws-ai-agents`. CoALA memory theory;
  **AgentCore Memory** `MemoryClient.create_memory` (L637) + namespaces/strategies
  (L553–589); Mem0 personalized agent (L302–370); **LangGraph checkpointing**
  `AgentCoreMemorySaver` (L649) + `init_chat_model(model_provider="bedrock_converse")`
  (L655) — the one place the **Converse API** surfaces (via LangChain). Model
  `global.anthropic.claude-haiku-4-5-20251001-v1:0`. Adds AgentCore-Memory material
  not in ch06–07.
- **ch04 — Advanced Agent Architecture Patterns** → `aws-ai-agents`. Multi-agent:
  supervisor-worker + agent-as-tool (`.as_tool()`, L100–214); **`strands.multiagent`
  `Swarm`** with handoff (L384–477); **`GraphBuilder`** DAG nodes/conditional edges
  (L528–557); a pattern-selection table (L562–604) and explicit "when NOT to go
  multi-agent." Model `us.anthropic.claude-sonnet-4-5-20250929-v1:0`. Some snippets are
  `...` placeholders. Net-new orchestration APIs.
- **ch05 — Agent Communication (MCP + A2A)** → `aws-ai-agents` + `aws-ai-deploy`.
  Most complete runnable chapter: **FastMCP server** tool/resource/prompt (L443–478);
  async MCP client session (L485–546); prebuilt `awslabs.aws-documentation-mcp-server`
  via `uvx` (L367–381); **A2A** servers with agent cards (L774–868) + orchestrator
  client (L875–917); 3-terminal run (L928–939). `a2a-sdk` + `strands-agents[a2a]`
  (`A2AServer`, `A2AAgent`). MCP-server-authoring + A2A material absent from ch06–07.
- **Model-ID drift confirmed:** ch02/ch05 use Sonnet 4, ch03 Haiku 4.5, ch04
  Sonnet 4.5 — reinforces resolving model IDs dynamically
  (`list_foundation_models` / inference profiles) rather than hard-coding.

### ch06 — Production Deployment & Enterprise Integration (modern)
- **Feeds:** `aws-ai-deploy` (primary), `aws-ai-agents`.
- **Stack/services:** Lambda + SAM, ECS/Fargate, EKS, **Bedrock AgentCore**
  (Runtime, Gateway, Identity, Policy, Memory, Observability, Evaluations, Browser,
  Code Interpreter), ECR, DynamoDB, EventBridge, SQS/DLQ, Secrets Manager, KMS.
  `BedrockModel(model_id="us.anthropic.claude-sonnet-4-20250514-v1:0")`.
- **Runnable code (partial → yes):** Lambda init-outside-handler (L55–64); SAM IAM
  policy with **both** `foundation-model/*` and `inference-profile/*` ARNs — the
  classic access-denied trap (L72–80); ECS FastAPI agent server (L130–138);
  **AgentCore Runtime entrypoint** `BedrockAgentCoreApp` + `@app.entrypoint` +
  `app.run()` (L243–262); starter-toolkit `Runtime.configure/launch/invoke`,
  **ARM64/Graviton required** (L288–305); Gateway via
  `boto3.client('bedrock-agentcore-control').create_gateway(...)` (L402–424).
- **Hazards:** none — clean modern stack.

### ch07 — Evaluation, Observability & AI Governance (modern)  ★ most reusable
- **Feeds:** `aws-ai-agents` (eval/observability), `aws-ai-deploy`, governance
  cross-cut for `arch-validate`.
- **Stack/services:** AgentCore Evaluations, AgentCore Observability, CloudWatch
  GenAI Observability, **OpenTelemetry/ADOT**, Jaeger, **Langfuse** (self-host on
  ECS+RDS+ALB; CDK/Terraform samples referenced), LangSmith, Strands telemetry,
  **Bedrock Guardrails**, **AgentCore Policy / Cedar**.
- **Runnable code (yes):** Strands OTel setup `StrandsTelemetry().setup_otlp_exporter()`
  (L510–524); AgentCore eval passes `eval_client.run(evaluators=[...])` at
  session/trace/custom-judge level (L313–422); Guardrails on Strands
  `BedrockModel(..., guardrail_id=..., guardrail_trace="enabled")` (L764–780); three
  runnable **Cedar** policy blocks (L797–841); OTel Collector fan-out YAML (L668–690).
- **Hazards:** none — modern, internally consistent.

### ch08 — Security & Privacy for GenAI on AWS  ⚠️ LEGACY lineage
- **Feeds:** `aws-ai-foundations` (IAM/security pillar) — JSON only, not the Python.
- **Stack/services:** Bedrock (classic), **KMS**, **IAM** (identity-based, ABAC,
  condition keys, STS AssumeRole, service roles, SCPs, permission boundaries),
  CloudTrail, **GuardDuty**, **Macie**, **Inspector**, PrivateLink/VPC endpoints,
  STRIDE threat modeling, GenAI Security Scoping Matrix (5 scopes).
- **Reusable (partial):** KMS key policy JSON scoped by `kms:ViaService` (L49–79);
  a suite of six IAM policy JSON patterns (L304–420); Bedrock-agent least-privilege
  IAM (L427–466); contextual-grounding guardrail tags (L545–600). **These JSON
  artifacts are version-agnostic and directly citable.**
- **Hazards (flagged):** classic `create_guardrail`/`create_agent` via
  `botocore.session.Session()` (L605–676) — the deprecated path. Treat as a
  *separate legacy lineage*, not a continuation of ch07's governance story.

### ch09 — Building End-to-End GenAI Applications  ⚠️ LEGACY lineage
- **Feeds:** `aws-ai-bedrock` (RAG/KB), `aws-ai-deploy` (data pipelines).
- **New material not elsewhere:** **RAG from scratch** (Bedrock Knowledge Base +
  OpenSearch vector store + `retrieve_and_generate`, L656–683); self-correcting
  **text-to-SQL** engine (Glue Data Catalog + Athena poll loop + model retry-on-error,
  L715–846); **IoT ingestion** (IoT Core/MQTT → DynamoDB → Lambda → Bedrock →
  API Gateway/S3).
- **Hazards (flagged):** mixes modern Messages API with the **deprecated
  `\n\nHuman:`/`\n\nAssistant:` + `max_tokens_to_sample` + `response["completion"]`
  text-completions format against a `claude-sonnet-4` model id (L686–712)** — a
  genuine correctness bug. Console-first, minimal IaC. Classic
  `bedrock-agent`/`bedrock-agent-runtime`, not AgentCore.

### ch10 — Sustainability & Scalability with Bedrock  ⚠️ LEGACY lineage
- **Feeds:** `aws-ai-sagemaker` (first real SageMaker usage), `aws-ai-foundations`
  (cost/sustainability), `aws-ai-bedrock` (batch inference).
- **New material:** SageMaker Studio notebook + `redshift-data` API → Titan
  `invoke_model` (L314–419) — the **only runnable SageMaker code in either bundle**;
  **zero-ETL** Aurora↔Redshift (console + SQL); **Bedrock Batch Inference** (50%
  discount, console-only); Titan Image Generator + watermark detection (console-only);
  sustainability/cost ladder (Trainium, pruning/distillation/quantization, S3
  Intelligent-Tiering, AWS Batch).
- **Hazards (flagged):** Titan Text Large (`amazon.titan-tg1-large`) + Claude 3.5
  Sonnet, no Sonnet 4, no inference profiles; legacy Titan `inputText`/`outputText`
  schema. Console-first.

## `cases/aws/` — "System Design on AWS" (the platform corpus)

Conceptual / decision-framework book; **explicitly disclaims setup steps**. Every
chapter is `type: overview`. Across all read chapters there are only **5 code blocks
total** (a Dockerfile, a DocumentDB JSON doc, an ECS task-def JSON, a Step Functions
ASL JSON, and an IAM policy JSON) — **and all use typographic curly quotes, so none
run as-is.** No boto3, no CLI, no Terraform, no CDK anywhere. Treat as vocabulary and
decision-criteria, not implementation.

### Service chapters (fully inventoried)
- **ch12 — Messaging, Orchestration, Monitoring & IAM  ★ highest citation density.**
  Feeds `aws-ai-foundations` (IAM/security) **and** `aws-ai-deploy` (orchestration).
  Has the two most citable artifacts in the bundle: a **Step Functions ASL** state
  machine JSON (L327–337) and a canonical **IAM policy JSON** (`Version 2012-10-17`,
  s3 ListBucket/GetObject, L566–582). Full taxonomy: MSK/Kinesis/SQS/SNS, Step
  Functions (standard vs express), MWAA/Airflow, CloudWatch alarms, EventBridge, IAM
  user/group/role/policy, Cognito, AppSync.
- **ch13 — Big Data, Analytics & ML  ★ sole SageMaker source (concept-only).**
  Feeds `aws-ai-sagemaker`. Gives the **four inference/deploy modes** (real-time /
  serverless / async ≤1 GB / batch-transform) and the SageMaker feature map (Data
  Wrangler, Studio, Clarify, Debugger, Pipelines, AMT, Ground Truth) plus
  Trainium/Inferentia cost story — but **zero runnable code.** **Bedrock / GenAI
  foundation models are not mentioned anywhere in this bundle.**
- **ch11 — Compute** (EC2/Lambda/ECS/EKS; ECS Fargate task-def JSON L226–251; Fargate
  "no GPU" constraint; Lambda cold-start/provisioned-concurrency) → `aws-ai-deploy`.
- **ch09 — Network** (VPC/subnets/SG-vs-NACL/NAT/PrivateLink/Route53/ELB/API GW/
  CloudFront) → `aws-ai-foundations` (networking; PrivateLink for private
  Bedrock/SageMaker traffic).
- **ch10 — Storage** (EBS/EFS/FSx/S3 storage-classes+encryption/DynamoDB capacity
  modes/RDS/Aurora/DAX/OpenSearch) → `aws-ai-foundations` (storage; S3 as the
  SageMaker data substrate).
- **ch07 — Containers** (Docker/K8s/deployment strategies; one real Dockerfile
  L64–83) → `aws-ai-deploy` background.

### Concept + case-study chapters (index-level coverage)
ch01–ch06, ch08, ch14–ch16, ch19–ch21 — system-design fundamentals (basics, storage
types, non-relational stores, caching, load balancing, protocols, architectural
patterns) and worked case studies (URL shortener, web crawler/search, social
newsfeed, chat app, video pipeline, stock-trading platform). **Background concept
only** — no AI/ML, no AWS AI services, no runnable AWS code (per the book's own
altitude). Useful as architecture-decision vocabulary the `arch-*` family already
covers; low direct-citation value for `aws-ai-*`.

## Pillar → source map (what to cite where)

| Proposed skill | Strong in-corpus sources | Nature |
|---|---|---|
| `aws-ai-foundations` (AWS/boto3/IAM/security/cost) | aws-ai ch08 (IAM/KMS JSON, STRIDE, scoping matrix); aws ch12 (IAM policy JSON), ch09 (network), ch10 (storage) | JSON + concept |
| `aws-ai-bedrock` (Converse/RAG/guardrails/embeddings) | aws-ai ch09 (KB/RAG `retrieve_and_generate`), ch07 (Guardrails), ch10 (batch inference) | partial code (legacy) |
| `aws-ai-agents` (Strands/AgentCore/MCP/multi-agent) | aws-ai ch01–07 (modern stack, code-rich) | **runnable, modern** |
| `aws-ai-sagemaker` (train/pipeline/endpoint) | aws-ai ch10 (redshift-data→Titan, only SM code); aws ch13 (deploy-mode taxonomy, concept-only) | **thin — real gap** |
| `aws-ai-deploy` (CDK-Python + harness) | aws-ai ch06 (Lambda/ECS/AgentCore deploy), ch07 (Langfuse infra); aws ch11 (compute), ch12 (Step Functions ASL) | SAM/toolkit; **CDK absent** |

## The real gaps — where the skill family must supply fresh executed code

The corpus is **strong on modern agents and on security/IAM JSON**, and
**conceptual on everything else**. These are the genuine holes the `aws-ai-*` family
must fill with its own executed, verified code (not doc paraphrase):

1. **SageMaker train → pipeline → endpoint** — the corpus has one Titan-via-notebook
   snippet (ch10) and a concept-only taxonomy (aws ch13). No `ModelTrainer`,
   `sagemaker.workflow.*`, registry, or endpoint deploy code. **Biggest gap.**
2. **AWS CDK-Python deployment** — essentially absent from both bundles (only a
   passing reference to a Langfuse CDK sample). The chosen deploy stack (boto3 + CDK)
   has no in-corpus model.
3. **Native Converse API model access** — the corpus reaches Bedrock either through
   raw `invoke_model` (ch09/ch10, incl. one legacy completion-format bug) or behind
   framework abstractions (Strands `BedrockModel`; LangChain
   `init_chat_model(model_provider="bedrock_converse")` in ch03). The **native boto3
   `bedrock-runtime.converse()` / `converse_stream()` call** — the research doc's
   recommended default, with its hand-rolled tool-use loop and Converse-native
   guardrails — never appears directly. That, plus current embeddings (Titan v2 /
   Cohere v3–v4), is fresh code the `aws-ai-bedrock` skill must supply.
4. **Offline test harness** — no `botocore` Stubber / `moto` tests anywhere. The
   family's verification harness is net-new.

## Implications for family shape

- The **`aws-ai-agents`** pillar is well-supported and should follow ch01–07's
  modern Strands+AgentCore spine; classic Bedrock Agents (ch08) are secondary and
  explicitly flagged as legacy.
- **`aws-ai-sagemaker`** and **`aws-ai-deploy`** are the pillars that carry the most
  net-new executed code — they are where the "actually run it" bar is met, not where
  the corpus is paraphrased.
- **`aws-ai-bedrock`** must modernize the corpus (Converse over `invoke_model`) and
  reuse ch09's RAG shape while correcting its completion-format bug.
- **`aws-ai-foundations`** can lean on the corpus's genuinely reusable IAM/KMS JSON
  (aws-ai ch08, aws ch12) and the network/storage concepts (aws ch09/ch10).
