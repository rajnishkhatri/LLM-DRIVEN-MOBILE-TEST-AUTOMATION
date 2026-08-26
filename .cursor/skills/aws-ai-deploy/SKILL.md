---
name: aws-ai-deploy
type: skill
description: >-
  AWS-AI capability workflow stage 4: deliver a built agent or AI pipeline to
  AWS as CDK-Python infrastructure-as-code, validated offline with cdk synth →
  cfn-lint → cdk-nag. Use when the user says "deploy this to AWS", "write the
  CDK app / stack", "cdk synth", "ship the agent to Lambda / ECS / AgentCore
  Runtime", "deploy the SageMaker endpoint or pipeline", "package the agent
  container for ECR", "wire the Step Functions AI pipeline", or hands over a
  built implementation that now needs an IaC deploy surface. Bundles a worked,
  offline-synthesizable CDK app (scripts/sample_cdk_app/) that encodes the
  two-ARN Bedrock IAM trap. Do NOT use to pick the AWS service (aws-ai-assess),
  design topology/RAG/IAM boundaries (aws-ai-design), write the boto3/Strands
  agent code (aws-ai-build), or run the offline harness / the gated real
  deploy (aws-ai-validate) — a real `cdk deploy` never happens in this stage.
---

# Stage 4 — Deploy (CDK-Python)

> Binding: `.aws-ai/binding.toml` (see aws-ai-lifecycle). IaC surface:
> `{{iac_tool}}`; region `{{region_default}}`; primary language
> `{{primary_language}}`. Methodology: `{{methodology_source}}` ch06 (the three
> deploy paths, the two-ARN trap, ARM64/Graviton) + `{{methodology_secondary}}`
> ch11–12 (compute selection, Step Functions ASL). Reference:
> `../aws-ai-lifecycle/references/boto3-foundations.md` §3–5 (IAM, cost, static
> IaC gates). Worked example bundled here: `scripts/sample_cdk_app/` — a
> Lambda "Bedrock agent" that renders with `cdk synth` offline, no Docker, no
> account.

Micro-loop: **pick the target → author the CDK app → `cdk synth` offline →
human gate before any real deploy.** Everything in this stage runs with
`{{aws_profile}}` unset — synth, lint, and nag need no credentials and cost
nothing. The real `cdk deploy` is a separate, human-approved act that belongs to
aws-ai-validate's gated real-path, not here.

## Agent work

1. **Choose the deploy target — workload shape decides, not fashion.** The four
   candidates are a **Lambda function**, an **ECS/Fargate service**, **AgentCore
   Runtime**, and a **SageMaker endpoint**; the corpus lays the first three side
   by side in Table 6.1 (`{{methodology_source}}/ch06.md:309-377`), and the last
   two rows — who owns auth/observability/policy, and how much infra control you
   keep — are where the call actually gets made (`ch06.md:377`). Map by session
   model: a stateless single-shot request → **Lambda**, but respect its
   **15-minute ceiling** (`ch06.md:337`, `{{methodology_secondary}}/ch11.md:140`);
   a long-lived, continuous, no-distinct-session workload → **ECS/Fargate**
   (`ch06.md:526`); multi-turn, per-user isolated sessions → **AgentCore
   Runtime** (`ch06.md:513`, `ch06.md:539`); self-hosted or custom-trained model
   inference → a **SageMaker endpoint** (its type — real-time / serverless /
   async / batch — was chosen back in aws-ai-design). Fundamentals behind the
   pick live in `{{methodology_secondary}}/ch11.md`: Lambda's 250 MB zip limit
   (`ch11.md:151`), and Fargate's serverless convenience at the cost of **no GPU
   and no EBS** (`ch11.md:281`) — disqualifying for GPU inference. Output: the
   chosen target with its reason and the losing options named, so the trade-off
   is on the record rather than assumed.

2. **Author the CDK app — and get the execution role's TWO ARNs right.** Use
   `aws-cdk-lib` (`{{iac_tool}}`), one `Stack` per deployable quantum. The single
   most common Bedrock deploy defect is granting `bedrock:InvokeModel` on the
   `foundation-model/*` ARN alone: any modern model id starts `us.` / `eu.` /
   `apac.` / `global.`, which is a **cross-region inference profile**, so the
   role also needs an `inference-profile/*` ARN or invocation fails with an
   `AccessDenied` that never names the missing permission — the corpus states it
   outright in its SAM policy (`{{methodology_source}}/ch06.md:76-80`) under the
   warning "Two resource types, not one" (`ch06.md:81`). Two asymmetries to
   encode faithfully: the `foundation-model` ARN has an **empty account segment**
   (`arn:aws:bedrock:<region>::foundation-model/*`) because models are AWS-owned,
   while the `inference-profile` ARN carries your account id; and a cross-region
   profile must allow `foundation-model/*` in **every** region it can route to.
   `scripts/sample_cdk_app/app.py` is the reference implementation — its
   `PolicyStatement` (app.py:114-127) encodes exactly this trap in CDK, scoped to
   `InvokeModel` + `InvokeModelWithResponseStream` on both resources, never `*`.
   **Default to the tighter scope — name the specific inference-profile id and its
   member foundation-model id, not a `/*`; with no wildcard there is no
   `AwsSolutions-IAM5` finding to suppress.** Discover the member foundation-model
   ARNs with `aws bedrock get-inference-profile --inference-profile-identifier
   <profile-id>` and read `models[].modelArn` (a cross-region profile lists one per
   routed region — grant them all). Only *if you rotate models often*, use the
   variant: an `anthropic.*` family wildcard paired with an active, reasoned
   `NagSuppressions` for the IAM5 finding it then raises (app.py sketches both).
   Lazy shortcut (not recommended): `resources=["*"]` — prefer the least-privilege
   two-ARN grant.
   The wider least-privilege discipline (no `*FullAccess`; the SageMaker
   `iam:PassRole` gated by `iam:PassedToService=sagemaker.amazonaws.com`) is in
   `../aws-ai-lifecycle/references/boto3-foundations.md` §3. Construct choice is
   fast-moving: Bedrock **L2s are still unstable** (KB/agent), so prefer native
   `aws_bedrockagentcore` for AgentCore infra and fall back to L1 `Cfn*` or an
   `AwsCustomResource` calling boto3 `bedrock-agent` for KB/Agents — re-verify
   against `../aws-ai-lifecycle/references/research-2026.md` before committing.

3. **Pipeline deploys — Step Functions or a SageMaker pipeline.** An AI pipeline
   (ingest → train → eval → register, or an orchestration of Bedrock/Lambda
   steps) is IaC too. A **Step Functions** state machine is declared in Amazon
   States Language, whose canonical JSON shape — `StartAt`, `States`, a `Task`
   with a `Resource` ARN — is at `{{methodology_secondary}}/ch12.md:325-337`. In
   CDK, build the chain and pass `definition_body=DefinitionBody.from_chainable(...)`
   (the older `definition=` kwarg is deprecated); SageMaker Pipelines have **no
   dedicated SFN task**, so trigger them with `CallAwsService` calling
   `startPipelineExecution`. Pick **Standard vs Express** by execution
   duration/volume (`ch12.md:374`). The pipeline/execution role needs
   `sagemaker:Create*`, scoped S3/ECR/logs/KMS, **and** `iam:PassRole` on the
   exact exec-role ARN with the `iam:PassedToService` condition — the passed-role
   trap that silently blocks runs (boto3-foundations.md §3). A SageMaker pipeline
   itself is authored in aws-ai-build; here you emit the CDK that schedules and
   permissions it.

4. **Packaging — container via ECR, ARM64/Graviton for AgentCore Runtime.** A
   real Strands/AgentCore agent's dependencies exceed Lambda's 250 MB zip ceiling
   (`{{methodology_secondary}}/ch11.md:151`), so ship it as a container image
   (`DockerImageFunction`, up to 10 GB) pushed to **ECR** rather than a zip — the
   container variant needs `from aws_cdk import aws_ecr_assets as ecr_assets` at
   the top alongside `aws_lambda`, an easy import to drop that turns a copied
   sketch into a `NameError`.
   **AgentCore Runtime requires ARM64/Graviton images**
   (`{{methodology_source}}/ch06.md:307`) — a non-negotiable, easy-to-miss
   constraint; build ARM64 wheels and match the architecture end to end. The
   starter-toolkit `configure` step generates the Dockerfile, creates the exec
   role, and provisions the ECR repo (`ch06.md:303`), then `launch` builds and
   pushes it; either way the container serves `/invocations` + `/ping` on :8080
   via `BedrockAgentCoreApp` + `@app.entrypoint` (`ch06.md:257`, `ch06.md:265`).
   The bundled sample deliberately uses **inline** Lambda code (not a container)
   solely to keep `cdk synth` offline — see `scripts/sample_cdk_app/README.md`
   for why it is not production-shaped. **Sampling params are removed on
   current-generation Claude models (VERIFIED against the authoritative Claude API
   reference, 2026-08).** In the handler's Converse call do NOT set
   `inferenceConfig.temperature`, `topP`, or `topK` for a current-gen Claude id:
   Opus 4.7+/Opus 5 and Fable 5 remove them (sending any returns a 400) and Sonnet 5
   rejects a non-default value with a 400 — omit `inferenceConfig` or pass only
   `maxTokens`. They stay valid on older models (Sonnet 4.5 / Opus 4.5 and earlier),
   so the guard is model-generation-specific: drop the sampling params when the
   resolved id is a current-gen Claude. Treat it as a deprecated-parameter trap
   symmetric with the legacy `\n\nHuman:` / `max_tokens_to_sample` completion
   format — both silently break against current Claude models, and the skill warns
   against both the same way. Note the two conflicting `agentcore` CLIs
   (legacy pip starter-toolkit vs forward npm `@aws/agentcore`) — pin the version
   and re-verify verbs against research-2026.md.

5. **Offline synth validation — the only thing that runs here.** With no
   credentials: `cdk synth` → `cfn-lint` → `cdk-nag`. `cdk synth` renders the
   full CloudFormation template completely offline (the sample's inline code
   means nothing is bundled and no Docker is needed) and runs any `cdk-nag`
   Aspects you attach; `cfn-lint` validates the synthesized
   `cdk.out/*.template.json`; **`cdk-nag AwsSolutionsChecks`** flags IAM
   wildcards — `AwsSolutions-IAM5` is the direct guard against the step-2 policy
   decaying into a `*` grant — plus unencrypted resources and public exposure.
   Suppress only genuinely-justified findings with `NagSuppressions`, which
   leaves an audit trail instead of hiding the risk. Reproduce it on the sample:
   `pip install -r requirements.txt && cdk synth` (`scripts/sample_cdk_app/README.md`).
   Write the CDK app **and** the synthesized template to `{{deploy_home}}`; the
   full static-IaC + types contract (cfn-lint severities, `boto3-stubs` + mypy)
   is `../aws-ai-lifecycle/references/boto3-foundations.md` §5–6.

## Human gate

A real `cdk deploy` (and `cdk bootstrap`) provisions real resources in a real
account and can start standing cost — **it does not happen in this stage.** This
stage ends at a synthesized, `cfn-lint`-clean, `cdk-nag`-reviewed template on
disk in `{{deploy_home}}`. Confirm three things **separately**, not as one
bundled "yes": the deploy-target choice, the two-ARN execution policy, and the
packaging/architecture (container + ARM64 where AgentCore Runtime is the target).
Consult `{{constitution}}` (model-access policy, cost ceilings, data-residency)
before advancing. The actual deploy is requested at **aws-ai-validate**'s gated
real-path — with `{{aws_profile}}` set to throwaway sandbox credentials and
explicit human approval — never here. Advance → **aws-ai-validate**.

## Constraints

- **Offline synth/lint/nag is the whole of this stage.** `{{aws_profile}}` stays
  `<none>`; `cdk synth`, `cfn-lint`, and `cdk-nag` need no account and cost
  nothing. Any real AWS call — including `cdk bootstrap`/`cdk deploy` — outside
  aws-ai-validate's gated real-path is a defect, not a shortcut.
- **The two-ARN trap is non-negotiable.** Both `foundation-model/*` and
  `inference-profile/*`, scoped to the specific invoke actions, or the role is
  broken for every `us.`/`eu.`/`global.` model id (`ch06.md:81`). `cdk-nag`'s
  `AwsSolutions-IAM5` is there to stop the "fix" from becoming a `*`.
- **Nothing incurs standing cost silently.** Always-on SageMaker endpoints,
  provisioned throughput, and NAT gateways are flagged as cost in the synth
  review so the human owns the trade-off (boto3-foundations.md §5); prefer
  scale-to-zero / serverless / async and delete-idle by default.
- **Don't hardcode fast-moving facts.** Resolve model ids dynamically
  (`list_foundation_models` / `list_inference_profiles`); treat Bedrock CDK L2s
  as unstable (L1 `Cfn*` / `AwsCustomResource` fallback); use
  `definition_body` over the deprecated `definition=`; watch the two `agentcore`
  CLIs. Defer specifics to `../aws-ai-lifecycle/references/research-2026.md` and
  re-verify at author time.
- **Trade-offs, not advocacy** (inherits the family's first law). Lambda vs
  ECS/Fargate vs AgentCore Runtime vs SageMaker endpoint is a spectrum of
  control-for-convenience and session-model fit — present the cursor position,
  let the human place it.
