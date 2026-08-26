# External research — AWS AI capability, 2025–2026

Deep-research run 2026-08-12 for the `aws-ai-*` family (five parallel agents,
cross-checked against official AWS sources: `docs.aws.amazon.com`,
boto3/botocore reference, `github.com/awslabs`, `github.com/strands-agents`,
`docs.getmoto.org`, `docs.localstack.cloud`; current through August 2026).
This file is the **condensed, confidence-labeled digest** — the fast-moving
traps the whole family must not bake in as constants. The authoritative,
example-rich source is `{{research_home}}/aws-ai-bedrock-sagemaker-research.md`;
open it for the actual request/response shapes. Confidence labels reflect how
official the evidence is **and** how fast it decays.

> **Re-research before treating numbers as constants.** Model IDs, AgentCore
> CLI verbs, and CDK L2 graduation move monthly. Everything below tagged
> *volatile* is a snapshot, not a law — resolve it at runtime or re-verify at
> authoring time. Dates and version numbers here are load-bearing precisely
> because they will be wrong soon.

## The stable spine (safe to build on)

1. **Converse is the default model-access API** [high; AWS Bedrock userguide].
   `bedrock-runtime.converse` / `converse_stream` is provider-agnostic —
   `modelId` swaps across Claude, Nova, Llama, Mistral, Cohere without
   rewriting request/response parsing. `invoke_model` is reserved for
   embeddings, image generation, and model-specific fields. The family
   standardizes on Converse; `invoke_model` is the exception, never the default.
2. **The control/runtime client split is strict** [high; boto3 reference].
   Six Bedrock clients (`bedrock`, `bedrock-runtime`, `bedrock-agent`,
   `bedrock-agent-runtime`, `bedrock-agentcore-control`, `bedrock-agentcore`).
   Guardrail *creation* is on `bedrock`; standalone *apply* is on
   `bedrock-runtime`. Mixing planes is the #1 beginner error — the full table
   is §1.1 of the authoritative doc.
3. **The tool-use loop is contract, not style** [high; Bedrock tool-use docs].
   Send `toolConfig` → model returns `stopReason="tool_use"` → echo the
   assistant's `toolUse` turn back **verbatim first**, then append a user turn
   whose `toolResult.content` is a **list of blocks** (`{"json":...}`), never a
   bare string → loop until `stopReason="end_turn"`. Getting the ordering or
   the block-list shape wrong is a validation error, not a soft failure.
4. **Strands authors, AgentCore deploys** [high; strandsagents.com + AgentCore
   devguide]. These are orthogonal: Strands (`@tool`, `Agent`, `BedrockModel`,
   `strands.multiagent` Swarm/Graph, A2A) is the authoring spine; Bedrock
   AgentCore is the hosting/operating platform. This matches the modern corpus
   lineage (`cases/aws-ai` ch01–07) and AWS's own strategic direction.

## The moving parts (resolve dynamically — do not hard-code)

5. **Model-ID drift** [high, *volatile*; `list_foundation_models` /
   `list_inference_profiles`]. IDs churn and the corpus proves it — ch02/ch05
   use Sonnet 4, ch03 Haiku 4.5, ch04 Sonnet 4.5. Resolve at runtime; treat any
   literal id in an example as re-verify-me. Two live traps: (a) many newer
   models are **inference-profile-only** — a bare model id returns
   `ValidationException` ("on-demand not supported… use an inference profile");
   (b) profile prefixes are region-scoped (`us.`/`eu.`/`apac.`/*new* `global.`).
   Never present a model id as permanent.
6. **SageMaker SDK V2 vs V3 split** [high, *volatile*; sagemaker-python-sdk
   CHANGELOG]. **V3.0.0 shipped 2025-11-19, hard backward-incompatible** —
   `Estimator`/`Model`/`Predictor` and all framework subclasses were *removed*,
   replaced by `ModelTrainer` (`sagemaker.train`) and `ModelBuilder`
   (`sagemaker.serve`). No compat shim. Author against a V2-stable baseline with
   a clearly flagged V3 section, and **version-pin every example**
   (`pip install "sagemaker<3"` vs `>=3`). Also note the product rename: the
   build/train/deploy service is now **"SageMaker AI"**; plain "SageMaker" is
   the umbrella data platform.
7. **Two conflicting `agentcore` CLIs** [high, *volatile*; github.com/aws].
   The pip `bedrock-agentcore-starter-toolkit` (`agentcore configure/launch/
   invoke`) is now **legacy**; the npm **`@aws/agentcore`** (`agentcore
   create/dev/deploy/invoke`) is the forward path. Both register the same
   `agentcore` command and their verbs drifted (`launch` ↔ `deploy`) —
   uninstall the pip one first, pin the version, and check `--help` rather than
   trusting memory. AgentCore Runtime requires **ARM64/Graviton**.
8. **Bedrock CDK L2 constructs are still unstable** [high, *volatile*;
   aws/aws-cdk#36592]. `aws-cdk-lib.aws_bedrock` (stable) is **L1 only**
   (`CfnKnowledgeBase`, `CfnAgent`, `CfnGuardrail`); the `aws-bedrock-alpha`
   L2s for **KB + DataSource are still in progress (Aug 2026)**;
   `generative-ai-cdk-constructs` has the richest KB/Agent L2s but its Bedrock
   submodule is **deprecated**. Guidance for `{{iac_tool}}`: AgentCore infra →
   native `aws_bedrockagentcore` L2s (import is `from aws_cdk import
   aws_bedrockagentcore`, *not* `aws_bedrock_agent_core`); Bedrock KB/Agents →
   L1 `Cfn*` **or** `custom_resources.AwsCustomResource` calling boto3
   `bedrock-agent`. Do not assume a clean L2 exists — verify graduation first.
9. **AgentCore is new and fast-expanding** [high, *volatile*; AgentCore release
   notes]. **GA 2025-10-13.** GA services: Runtime, Memory, Gateway, Identity,
   Observability, Built-in Tools (Code Interpreter, Browser). Adjacent-new and
   still moving: Policy (Cedar), Evaluations (13 evaluators, GA Mar 2026),
   Managed Knowledge Base (June 2026), Payments (preview), Agent Registry.
   Feature availability is a moving target — check the service's own status
   before designing around it.

## Corrections the family applies to the seed corpus

10. **The legacy completion-format is a real bug, not a pattern** [high;
    verified at `cases/aws-ai/ch09.md:686-712`]. The grafted legacy lineage
    (`cases/aws-ai` ch08–10) invokes a Sonnet-4 model id
    (`anthropic.claude-sonnet-4-20250514-v1:0`) with the deprecated
    `\n\nHuman:`/`\n\nAssistant:` + `max_tokens_to_sample` +
    `response["completion"]` text-completions shape. That format was retired
    with the Messages/Converse era — against a Sonnet-4 id it is a correctness
    defect. Cite it only as the thing to *correct*, never to copy. Same lineage
    ships deprecated `create_agent`/`create_guardrail` via
    `botocore.session.Session()` (ch08) — flag, don't emulate.
11. **The Bedrock IAM role needs both resource ARN families** [high; verified at
    `cases/aws-ai/ch06.md:72-80`]. An execution role that allows
    `bedrock:InvokeModel` on only `foundation-model/*` gets `AccessDenied` the
    moment a `us.`-prefixed (inference-profile) id is used — you must also allow
    `inference-profile/*`. The foundation-model ARN carries **no account id**;
    the inference-profile ARN does. Cross-region profiles need
    `foundation-model/*` allowed in **every** region the profile spans.

## Offline-testing facts (they drive the harness, `{{test_stack}}`)

12. **`moto` cannot mock `bedrock-runtime`** [high; docs.getmoto.org coverage].
    `invoke_model`/`converse`/`converse_stream` are not implemented in `moto`
    (~5.1). Therefore **botocore `Stubber` is the only pure-unit path for
    Bedrock inference** — it validates responses against the service model (a
    genuine contract test) and can inject `ThrottlingException` etc. `moto`
    *does* cover the Bedrock control plane, the **SageMaker control plane**
    (`create_training_job`, `create_pipeline`, endpoints, tuning) and
    `sagemaker-runtime.invoke_endpoint`. Layered default: Stubber (Bedrock /
    SM-runtime contract) → `moto` (infra + SM control plane) → LocalStack
    Ultimate (integration, opt-in) → real AWS (smoke, gated).
13. **LocalStack changed its packaging** [medium, *volatile*;
    docs.localstack.cloud 2026]. Bedrock + SageMaker are **Ultimate-tier only**
    (Bedrock via Ollama; SageMaker custom-image endpoints only — no training, no
    Pipelines) and need Docker. The free **Community** image was discontinued
    2026-03-23; the free **Hobby** tier ≈ old Community (Lambda/S3/DDB/SQS/SNS/
    IAM/SecretsMgr). This is why LocalStack stays opt-in and the pure-Python
    Stubber+`moto` stack is the always-on default.
14. **Static IaC checks run fully offline** [high; cdk / cfn-lint / cdk-nag
    docs]. `cdk synth` (runs Aspects/cdk-nag) → `cfn-lint` → `cdk-nag`
    (`AwsSolutions-IAM5` wildcard finds, encryption, public exposure) — no AWS
    account touched. Pair with `mypy` + `boto3-stubs[bedrock-runtime,sagemaker,
    sagemaker-runtime]` to catch wrong params/keys/return-shapes before runtime.

## Governance source for the arch-* handoff

15. **Both Well-Architected AI lenses were revised 2025-11-19** [high; AWS
    Well-Architected]. The **Generative AI Lens** (6 GenAI pillars incl.
    excessive-agency security, RAG performance, prompt cost-engineering) covers
    Bedrock/RAG/agents; the **Machine Learning Lens** covers custom-trained
    SageMaker models (drift/retraining). These are the natural
    fitness-function / checklist source `aws-ai-validate` supplies to
    `arch-validate`'s GenAI intersection.

## Explicitly NOT settled (re-research when it matters)

- **Exact GA dates and feature tiers** for AgentCore sub-services (Evaluations,
  Managed KB, Payments, Policy) are the fastest-moving facts in this file — the
  dates above are Aug-2026 snapshots. Confirm against release notes before a
  design depends on a specific capability being GA.
- **CDK L2 graduation** for Bedrock KB/DataSource: assume L1/`AwsCustomResource`
  until you have verified an L2 exists in the pinned `aws-cdk-lib` version.
- **The two agentcore CLIs' verb surface** will keep drifting as the npm CLI
  matures and the pip toolkit is retired — `--help` is ground truth, not this
  file.

## Time sensitivity

The version-specific facts here (SDK V3 on 2025-11-19, AgentCore GA 2025-10-13,
LocalStack Community EOL 2026-03-23, the model ids, the CDK L2 status) are the
first things to go stale — the field moves monthly. Re-run the research and
re-open `{{research_home}}/aws-ai-bedrock-sagemaker-research.md` before treating
any of them as constants; the stable spine (Converse default, client-plane
split, tool-use contract, Stubber-for-runtime) is what to lean on between
refreshes.
