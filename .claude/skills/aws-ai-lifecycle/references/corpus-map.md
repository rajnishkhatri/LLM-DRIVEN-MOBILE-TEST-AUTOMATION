# Seed-corpus map — what to cite where

Navigation aid over the two seed bundles the `aws-ai-*` family cites. The full,
line-ranged inventory is `{{research_home}}/aws-ai-corpus-inventory.md`
(corpus re-review 2026-08-12, four reader agents); this is the condensed pointer
version — enough to know which chapter to open, not a re-derivation. Line refs
below were spot-verified against the chapters; open the chapter and confirm the
exact line before writing a new citation, and correct it if the corpus has since
moved.

> **The one warning that governs everything.** `cases/aws-ai` is **two books
> stitched together on two incompatible API generations.** ch01–07 are the
> modern lineage (Strands + Bedrock AgentCore, Converse-era); ch08–10 are a
> grafted **legacy** lineage (classic "Agents for Amazon Bedrock", raw
> `botocore`, console click-through). Cite the modern half as the pattern; cite
> the legacy half only for its version-agnostic IAM/KMS JSON and only as the
> thing to *correct* for its Python. Never treat them as one continuum.

## The two bundles at a glance

| Bundle (`{{…}}`) | Book | Chapters | Altitude | Runnable AWS code |
|---|---|---|---|---|
| `{{methodology_source}}` = `cases/aws-ai` | "AI Agents on AWS" (+ grafted legacy book) | ch01–ch10 | **Two lineages** | Yes in ch01–07; partial/console in ch08–10 |
| `{{methodology_secondary}}` = `cases/aws` | "System Design on AWS" | ch01–ch16, ch19–ch21 | Concept / decision-framework | **None** (5 curly-quote snippets, none run) |

## `cases/aws-ai` — modern lineage (ch01–07): the spine to follow

Code density rises roughly **ch05 > ch02 > ch03 > ch04 > ch01**; ch01 is a
near-code-free primer, ch02–05 own the agent-authoring snippets, ch06–07 own
runtime/deploy/observability. The **`@tool` contract** (function + type hints +
docstring → agent tool, `cases/aws-ai/ch02.md:89-104`) is the atom that recurs
in every chapter — standardize on it.

- **ch01 — Understanding AI Agents.** Conceptual: RAG-vs-agents, the AWS Agentic
  Stack, the **Bedrock-vs-SageMaker decision table** (`ch01.md:128-148`),
  MCP/A2A intro. Only runnable bit is a zero-config `Agent()` (`ch01.md:433-438`).
  Cite for the stack taxonomy and the service-choice framing (feeds
  **aws-ai-assess**), not for code.
- **ch02 — Building Agents With Tools.** Richest tool-authoring chapter: `@tool`
  (`ch02.md:89-104`), multi-tool agent (`126-140`), `strands_tools` prebuilts
  (`calculator`/`http_request`/`use_aws`), the **`use_aws` S3/DynamoDB/Lambda
  bridge** (`384-416`), class-based shared-connection tools (`516-532`), async
  parallel tool (`556-572`). Canonical for tool internals.
- **ch03 — Agent Memory.** CoALA memory theory; **AgentCore Memory**
  `create_memory` (`ch03.md:637`) + namespaces/strategies (`553-589`); Mem0
  agent (`302-370`); **LangGraph checkpointing** `AgentCoreMemorySaver`
  (`649`) + `init_chat_model(model_provider="bedrock_converse")` (`655`) — the
  one place Converse surfaces in the corpus, and only via LangChain.
- **ch04 — Advanced Agent Architecture Patterns.** Multi-agent: supervisor-worker
  + agent-as-tool `.as_tool()` (`ch04.md:100-214`); **`strands.multiagent`
  `Swarm`** with handoff (`384-477`); **`GraphBuilder`** DAG (`528-557`); a
  pattern-selection table + "when NOT to go multi-agent" (`562-604`). Some
  snippets are `...` placeholders.
- **ch05 — Agent Communication (MCP + A2A).** Most complete runnable chapter:
  **FastMCP server** (`ch05.md:443-478`), async MCP client (`485-546`), prebuilt
  `awslabs.aws-documentation-mcp-server` via `uvx` (`367-381`), **A2A** servers
  with agent cards (`774-868`) + orchestrator client (`875-917`), 3-terminal run
  (`928-939`).
- **ch06 — Production Deployment.** ★ deploy source. Lambda init-outside-handler
  (`ch06.md:55-64`); **the SAM IAM policy with BOTH `foundation-model/*` and
  `inference-profile/*` ARNs** — the access-denied trap (`72-80`); ECS FastAPI
  server (`130-138`); **AgentCore Runtime entrypoint** `BedrockAgentCoreApp` +
  `@app.entrypoint` + `app.run()` (`243-262`); starter-toolkit
  configure/launch/invoke, **ARM64/Graviton required** (`288-305`); Gateway via
  `create_gateway` (`402-424`). Clean modern stack — but note the starter
  toolkit it uses is now the *legacy* CLI (see research-2026 §7).
- **ch07 — Evaluation, Observability & Governance.** ★ most reusable, and the
  governance feed to `arch-validate`. Strands OTel setup (`ch07.md:510-524`);
  AgentCore eval passes `eval_client.run(evaluators=[...])` (`313-422`);
  Guardrails on Strands `BedrockModel(..., guardrail_id=...)` (`764-780`); three
  runnable **Cedar** policy blocks (`797-841`); OTel Collector fan-out YAML
  (`668-690`).

## `cases/aws-ai` — legacy lineage (ch08–10): ⚠️ cite with correction

- **ch08 — Security & Privacy.** Genuinely reusable **version-agnostic JSON**:
  KMS key policy scoped by `kms:ViaService` (`ch08.md:49-79`), six IAM policy
  patterns (`304-420`), Bedrock-agent least-privilege IAM (`427-466`),
  contextual-grounding guardrail config (`545-600`). Also STRIDE + the GenAI
  Security Scoping Matrix. **Hazard:** classic `create_guardrail`/`create_agent`
  via `botocore.session.Session()` (`605-676`) — deprecated path, cite JSON not
  Python.
- **ch09 — End-to-End GenAI Applications.** New material: **RAG from scratch**
  (Bedrock KB + OpenSearch + `retrieve_and_generate`, `ch09.md:656-683`),
  self-correcting **text-to-SQL** (Glue + Athena poll loop, `715-846`), IoT
  ingestion. **Hazard:** the **legacy completion-format bug** —
  `\n\nHuman:`/`\n\nAssistant:` + `max_tokens_to_sample` +
  `response["completion"]` against a Sonnet-4 id (`686-712`). Reuse the RAG
  *shape*; rebuild the model call on Converse.
- **ch10 — Sustainability & Scalability.** The **only runnable SageMaker code in
  either bundle**: SageMaker Studio notebook + `redshift-data` API → Bedrock
  `invoke_model` (`ch10.md:314-419`). Also zero-ETL Aurora↔Redshift, Bedrock
  Batch Inference (console-only), Titan Image Generator. **Hazard:** Titan Text
  Large + Claude 3.5, **no Sonnet 4, no inference profiles**, legacy Titan
  `inputText`/`outputText` schema.

## `cases/aws` — concept-only backdrop (not implementation)

Decision-framework book; every chapter is `type: overview`; **5 code blocks
total, all with typographic curly quotes → none run as-is.** Cite for vocabulary
and decision criteria only.

- **ch12 — Messaging, Orchestration, Monitoring & IAM.** ★ highest citation
  density: a **Step Functions ASL** state machine JSON (`cases/aws/ch12.md:327-337`)
  and a canonical **IAM policy JSON** (`566-582`, curly-quoted). Full
  messaging/orchestration/IAM taxonomy.
- **ch13 — Big Data, Analytics & ML.** ★ sole SageMaker source, concept-only:
  the **four inference/deploy modes** — real-time / serverless / async ≤1 GB /
  batch-transform (`cases/aws/ch13.md:313`) — plus the SageMaker feature map. No
  runnable code; **Bedrock/GenAI FMs are never mentioned in this bundle.**
- **ch11 — Compute** (EC2/Lambda/ECS/EKS; Fargate task-def JSON `ch11.md:226-251`;
  Fargate "no GPU"). **ch09 — Network** (VPC/PrivateLink for private
  Bedrock/SageMaker traffic). **ch10 — Storage** (S3 as the SageMaker data
  substrate). **ch07 — Containers** (one real Dockerfile `ch07.md:64-83`).
- **ch01–06, ch08, ch14–16, ch19–21** — system-design fundamentals + worked case
  studies. Background vocabulary the `arch-*` family already owns; low
  direct-citation value here.

## Where the material lands (topic depth → reference → citing stage)

Topic depth lives in the shared references, not in skill names; the stages cite
the reference and the corpus chapter together.

| Reference (topic depth) | Cited chiefly by | Strong in-corpus sources | Nature |
|---|---|---|---|
| `references/boto3-foundations.md` (boto3/IAM/security/cost) | aws-ai-assess, aws-ai-design, aws-ai-deploy | aws-ai ch08 (IAM/KMS JSON, STRIDE, scoping matrix); aws ch12 (IAM JSON `566-582`), ch09 (network), ch10 (storage) | JSON + concept |
| `references/bedrock.md` (Converse/RAG/guardrails/embeddings) | aws-ai-build | aws-ai ch09 (KB/RAG `656-683`), ch07 (Guardrails `764-780`), ch10 (batch) | partial code, **legacy — modernize** |
| `references/agents.md` (Strands/AgentCore/MCP/multi-agent) | aws-ai-build, aws-ai-deploy | aws-ai ch01–07 (code-rich, modern) | **runnable, modern** |
| `references/sagemaker.md` (train→pipeline→endpoint) | aws-ai-build, aws-ai-deploy | aws-ai ch10 (`314-419`, only SM code); aws ch13 (`313`, taxonomy) | **thin — real gap** |
| `references/research-2026.md` + deploy know-how | aws-ai-deploy | aws-ai ch06 (Lambda/ECS/AgentCore), ch07 (Langfuse infra); aws ch11 (compute), ch12 (SFN ASL `327-337`) | SAM/toolkit; **CDK absent — real gap** |

## The real gaps — fill with executed code, not paraphrase

The corpus is strong on modern agents and on security/IAM JSON, and conceptual on
everything else. These holes are the family's "actually run it" bar — supply
verified code, proven by the `aws-ai-validate` harness:

1. **SageMaker train → pipeline → endpoint** — one Titan-via-notebook snippet
   (`cases/aws-ai/ch10.md:314-419`) and a concept-only taxonomy (`cases/aws/ch13.md`)
   are all the corpus has. No `ModelTrainer`, `sagemaker.workflow.*`, registry,
   or endpoint-deploy code. **Biggest gap.**
2. **AWS CDK-Python deployment** — essentially absent from both bundles (a single
   passing Langfuse-CDK reference). The chosen deploy surface `{{iac_tool}}` has
   no in-corpus model.
3. **Native Converse model access** — the corpus reaches Bedrock only via raw
   `invoke_model` (ch09/ch10, incl. the completion-format bug) or behind
   framework abstractions (Strands `BedrockModel`; LangChain `bedrock_converse`
   in ch03). The native `bedrock-runtime.converse()`/`converse_stream()` call —
   with its hand-rolled tool-use loop and Converse-native guardrails — plus
   current embeddings (Titan v2 / Cohere v3–v4), is fresh code.
4. **Offline test harness** — no `botocore` Stubber / `moto` tests anywhere in
   the corpus. The verification spine (`{{test_stack}}`) is net-new.
