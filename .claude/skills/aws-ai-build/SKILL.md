---
name: aws-ai-build
type: skill
description: >-
  AWS-AI capability workflow stage 3: implement the agreed design in Python —
  boto3 client wiring, the native Bedrock Converse tool-use loop, Strands /
  AgentCore agents, RAG / Knowledge Base retrieval, and SageMaker
  train→pipeline→endpoint code — with every boto3 client dependency-injected so
  the offline Stubber/moto harness can bind. Use when the user says "build the
  agent", "write the boto3 code", "implement the Converse loop", "wire up
  retrieve_and_generate", "code the Strands tools", "add the AgentCore
  entrypoint", "train and register the SageMaker model", or hands over an
  aws-ai-design solution to make real. Do NOT use to pick the service or shape
  the topology (aws-ai-assess / aws-ai-design own that), to emit CDK / deploy
  IaC (aws-ai-deploy), or to run the test harness and gate the real-AWS call
  (aws-ai-validate).
---

# Stage 3 — Build (Python)

> Binding: `.aws-ai/binding.toml` (see aws-ai-lifecycle). Language:
> `{{primary_language}}`. Input: the solution design in `{{design_home}}`.
> Output: implementation in `{{build_home}}`. References (cited, not inlined):
> `../aws-ai-lifecycle/references/bedrock.md` (Converse + tool-use + RAG),
> `../aws-ai-lifecycle/references/agents.md` (Strands / AgentCore),
> `../aws-ai-lifecycle/references/sagemaker.md` (train→pipeline→endpoint),
> `../aws-ai-lifecycle/references/boto3-foundations.md` §1–2 (client/session/DI).
> Region for examples: `{{region_default}}`; the code must satisfy `{{test_stack}}`.

Micro-loop: agent scaffolds from the design → implements the model / agent / RAG /
SageMaker code against **dependency-injected** boto3 clients → hands clean,
Stubber/moto-bindable seams and a run note to aws-ai-validate. Nothing here touches
a real AWS account — that is a gated aws-ai-validate step.

## Agent work

1. **Scaffold from the design.** Read the solution design in `{{design_home}}`
   (topology, RAG shape, guardrail/IAM boundaries, model choice) — build realizes
   it, it does not re-decide it. Lay out a package under `{{build_home}}` in
   `{{primary_language}}` with a pinned `requirements.txt`. The load-bearing move:
   **dependency-inject the boto3 clients.** A module that calls
   `boto3.client("bedrock-runtime")` at import time cannot be exercised offline;
   accept the client (or a `Session`/factory) as a constructor argument so the
   harness can later hand it a Stubber-wrapped or moto-backed client — this is the
   single thing that makes aws-ai-validate possible
   (`../aws-ai-lifecycle/references/boto3-foundations.md` §1–2). Reuse clients
   (thread-safe, pooled); Bedrock/SageMaker/STS are client-only, no resource.
   `{{region_default}}` for region; `{{aws_profile}}` stays `<none>` until validate.

2. **Model access — the native Converse tool-use loop.** Default to
   `bedrock-runtime` `converse` / `converse_stream`: it is provider-agnostic, so a
   `modelId` swap across Claude/Nova/Llama/Mistral needs no request/response rewrite
   (`../aws-ai-lifecycle/references/bedrock.md`). Keep the shape honest — `system`
   is a **separate top-level param, not a message role**; `toolConfig` carries an
   `inputSchema` wrapped under the literal key `json`; `toolChoice` is
   `auto`/`any`/`tool`. Run the loop: send `toolConfig`; when `stopReason ==
   "tool_use"`, append the assistant turn back **verbatim first**, then a user turn
   whose `toolResult` echoes the `toolUseId` with `content` as a **list of blocks**
   (`{"json": ...}`, never a bare string); loop until `stopReason == "end_turn"`; a
   turn may carry several `toolUse` blocks → one `toolResult` per `toolUseId`.
   Explicitly do **not** emit the legacy `\n\nHuman:/\n\nAssistant:` +
   `max_tokens_to_sample` + `response["completion"]` completion format — if you lift
   the RAG/text-to-SQL flow from `cases/aws-ai/ch09.md`, its `invoke_claude`
   (`cases/aws-ai/ch09.md:686-712`) is a genuine bug fired at a Sonnet-4 id; replace
   it with `converse`. Symmetric deprecated-param trap: a Converse call against a
   **current-generation Claude** model must **omit `temperature`/`top_p`/`top_k`** —
   pass only `maxTokens` (or no `inferenceConfig`); current-gen Claude removes/rejects
   sampling params with a 400 (`../aws-ai-lifecycle/references/bedrock.md`). Resolve
   `modelId` dynamically (`list_foundation_models` / `list_inference_profiles`) and
   treat any literal id as a **current-generation** example to re-verify — many newer
   ids are inference-profile-only (`us.`/`global.` prefix) and a bare id raises
   `ValidationException`, and a current-gen example id is exactly what makes the
   sampling-param omission mandatory, not precautionary.

3. **Agents — Strands + AgentCore.** The atomic unit is the `@tool` decorator:
   function + type hints + docstring → an agent-callable schema
   (`cases/aws-ai/ch02.md:89`). Compose several single-purpose tools into one
   `Agent` with a `BedrockModel` (`cases/aws-ai/ch02.md:126`) rather than a
   mega-tool — smaller tools reason and reuse better. Escalate to multi-agent only
   when the design demands it: `strands.multiagent.Swarm` for unpredictable
   peer-handoff collaboration, with the ping-pong guards (`max_handoffs`,
   `repetitive_handoff_detection_window`) set (`cases/aws-ai/ch04.md:384`); a
   `GraphBuilder` DAG when certain checks must always run in a fixed, auditable order
   (`cases/aws-ai/ch04.md:528`). For a hosted agent, wrap it with
   `BedrockAgentCoreApp` + `@app.entrypoint` + `app.run()` — only four lines change
   from local code, and the SDK serves `/invocations` + `/ping` on `:8080`
   (`cases/aws-ai/ch06.md:243`). Validate that the entrypoint's `prompt` is a
   `str`: a `toolUse` block smuggled in as the prompt bypasses guardrails. See
   `../aws-ai-lifecycle/references/agents.md`; leave ARM64/Graviton and the two
   conflicting `agentcore` CLIs for aws-ai-deploy to resolve.

4. **RAG / KB wiring.** Retrieve with `bedrock-agent-runtime`
   `retrieve_and_generate` (`type: KNOWLEDGE_BASE`, or `EXTERNAL_SOURCES` for
   inline docs); walk `response["citations"] → retrievedReferences →
   content.text` to keep the grounding trail, and thread `sessionId` for multi-turn
   (`cases/aws-ai/ch09.md:656`). **Keep the citations** — dropping them removes the
   audit trail that makes the answer defensible. Attach the guardrail via
   `generationConfiguration.guardrailConfiguration` (contextual grounding is the
   anti-hallucination check for RAG); any standalone generation around the retrieval
   goes through `converse`, never the ch09 completion format
   (`../aws-ai-lifecycle/references/bedrock.md`).

5. **SageMaker code — only if the design's fork picked self-hosted (CORE depth).**
   When assess/design chose SageMaker over Bedrock-managed, supply the
   train→pipeline→endpoint code as fresh, executed code — this is a real corpus gap,
   not something to paraphrase. Train with `ModelTrainer` (SDK V3) or `Estimator`
   (V2) and **pin the SDK** (`pip install "sagemaker<3"` vs `>=3`): V3 (2025-11-19)
   removed `Estimator`/`Model`/`Predictor` with no shim. Assemble a
   `sagemaker.workflow` `Pipeline` (Processing → Training → eval `ConditionStep` →
   metric-gated `ModelStep` register) and prefer idempotent `pipeline.upsert`. Pick
   the endpoint type from the four (real-time / serverless / async / batch transform)
   the design named. Keep the `sagemaker` control-plane calls behind an injected
   client so moto can bind them (`../aws-ai-lifecycle/references/sagemaker.md`).

6. **Leave clean seams + a run note.** Every AWS call must sit behind an injectable
   client so the harness binds Stubber (the only pure-unit path for
   `bedrock-runtime` — moto **cannot** mock it) and moto (S3/IAM/Step Functions +
   the SageMaker control plane) without editing your code. Write a short run note to
   `{{build_home}}` — entrypoints, which client each module needs, env vars (e.g.
   the model id), how to invoke locally — so aws-ai-validate can wire tests and
   aws-ai-deploy can package. Write the implementation to `{{build_home}}`.

## Human gate

Human reviews the implementation against the design in `{{design_home}}`: does the
code realize the agreed topology, RAG shape, guardrail/IAM boundaries, and model
choice — and is every AWS call behind an injectable seam so the offline harness can
reach it? If `{{constitution}}` is set, check its model-access and cost provisions
here. A gap loops back to build, or to aws-ai-design when the design itself is
wrong — never forward with a real call. Advance → **aws-ai-deploy**.

## Constraints

- **Offline-exercisable before any real call.** Every module must run green under
  `{{test_stack}}` with zero credentials; a client constructed at import defeats
  that, so inject it. The real AWS account is aws-ai-validate's gated job alone —
  nothing with cost happens here.
- **Resolve model IDs dynamically.** `list_foundation_models` /
  `list_inference_profiles`; label any literal id as an example to re-verify and
  expect inference-profile-only (`us.`/`global.`) ids — never hard-code as if
  permanent.
- **Cite the modern lineage** (`cases/aws-ai` ch01–07). The legacy ch08–10 is
  corrected, never copied — above all never the `\n\nHuman:` completion format
  (`cases/aws-ai/ch09.md:686-712`); native Converse is the model-access default.
- **Trade-offs, not advocacy** (inherits the family's first law). Strands vs raw
  boto3 vs AgentCore, Bedrock-managed vs SageMaker-self-hosted — the design placed
  that cursor; build implements the pick, it does not relitigate it.
