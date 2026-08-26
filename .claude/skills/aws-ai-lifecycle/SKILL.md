---
name: aws-ai-lifecycle
type: skill
description: >-
  Router for the AWS-AI capability workflow family (aws-ai-*) that supplements
  the arch-* architect family. Use whenever the work involves building,
  deploying, or reasoning about AWS AI/ML — Amazon Bedrock, Amazon SageMaker,
  Bedrock AgentCore, Strands agents, RAG/Knowledge Bases, guardrails, or
  shipping an agent / AI pipeline to AWS with boto3 + CDK (Python). Routes to:
  aws-ai-assess (frame the need + pick the service), aws-ai-design (agent
  topology, RAG, memory, guardrail & IAM boundaries), aws-ai-build (boto3 +
  Converse + Strands/AgentCore + SageMaker code), aws-ai-deploy (CDK-Python
  delivery), aws-ai-validate (offline Stubber/moto harness → gated real-AWS).
  Trigger even when the user says "add a Bedrock agent", "deploy this to
  SageMaker", "build a RAG pipeline on AWS", or "which AWS AI service should
  we use" without naming a stage. Do NOT use for a single stage the user
  already named — invoke that stage skill directly. Not for the architecture
  workflow itself (arch-lifecycle) or knowledge curation (okf-curator).
---

# AWS-AI Capability Workflow — Lifecycle

> **Workspace binding.** Resolve each `{{placeholder}}` from `.aws-ai/binding.toml`
> at the repo root, else first-run auto-adapt (see `FIRST_RUN.md` in this skill;
> schema in `binding.schema.md`). All aws-ai-* siblings share this one binding —
> they do not carry their own copies.

This family is the AWS AI/ML **capability arm** of the `arch-*` architect family:
it lets the architect workflow reason about Bedrock/SageMaker as concrete options
**and** actually ship the resulting agents and AI pipelines. Primary language is
**Python** (`{{primary_language}}`); the deploy surface is **boto3 + AWS CDK**
(`{{iac_tool}}`).

Knowledge source: `{{methodology_source}}` (the modern *AI Agents on AWS* corpus,
Strands + Bedrock AgentCore) with `{{methodology_secondary}}` as system-design
backdrop, and external research in `{{research_home}}`. Every stage skill cites
its chapters by `file.md:line` and defers fast-moving facts to
`references/research-2026.md`.

## The two modes

- **Design-time mode** (supplement, default when reached from `arch-*`): the
  family *informs* an architecture decision — which AWS AI capability fits, its
  feasibility, and its trade-offs — without touching AWS. Output is an
  assessment/design that flows back into `arch-style`/`arch-decide`. No
  credentials, no calls.
- **Deploy-time mode** (delivery): actually build and ship the agent / AI
  pipeline. The offline harness (`botocore` Stubber + `moto`) runs always; a
  **real AWS account is touched only at the gated `aws-ai-validate` step**, with
  throwaway sandbox creds, and nothing that incurs cost happens without explicit
  human approval.

## The pipeline

Assessment and design are the design-time join with `arch-*`; build → deploy →
validate is the delivery run. Stages may re-enter freely (AI systems are
iterative — models, costs, and APIs move).

| # | Stage | Skill | Output artifact (home) |
|---|---|---|---|
| 1 | Frame the AI/ML need + select the AWS service | **aws-ai-assess** | capability brief in `{{assess_home}}` |
| 2 | Design the solution (topology, RAG, memory, guardrail/IAM boundaries) | **aws-ai-design** | solution design in `{{design_home}}` |
| 3 | Build it in Python (boto3, Converse, Strands/AgentCore, SageMaker) | **aws-ai-build** | implementation in `{{build_home}}` |
| 4 | Deploy to AWS (CDK-Python) | **aws-ai-deploy** | CDK app + `cdk synth` in `{{deploy_home}}` |
| 5 | Validate — offline harness → gated real-AWS | **aws-ai-validate** | test/eval report in `{{validate_home}}` |

Routing rules:

- **Frame the stakes before routing — "what's the cost of being wrong?"** A
  low-stakes internal helper and a regulated/insurer-facing decision demand very
  different rigor; this triage question sets how hard `aws-ai-assess` and
  `aws-ai-validate` push.
- Reached from `arch-*` / "which AWS AI service should we use?" → **aws-ai-assess**
  first; never jump to build/deploy before a capability decision exists (that is
  the Accidental Architecture antipattern in AWS clothing).
- "Ship this agent / pipeline to AWS" with a design on file → **aws-ai-build** →
  **aws-ai-deploy** → **aws-ai-validate**.
- "Is this AI design production-ready / does it hold up?" → **aws-ai-validate**
  (its eval + cost + security + guardrail checklist is the criteria menu).
- Post-deploy **evaluation and monitoring** — a held-out test set, cost/latency
  tracking, model-invocation logging, budget alerts — live in **aws-ai-validate**,
  not the router.
- Any real AWS call outside the gated `aws-ai-validate` real-path is a defect —
  offline Stubber/moto is the default everywhere else.
- A stage's human gate failing loops back to that stage, not to stage 1.

## Handoff with the arch-* family (loose coupling)

The AI arm is referenced from the architect stages where AI/ML surfaces — it does
not edit their skill bodies beyond a pointer line:

- **arch-style** — AWS AI capabilities as style options (Bedrock-managed vs
  SageMaker-self-hosted vs AgentCore-Runtime) enter through **aws-ai-assess**.
- **arch-decide** — ADRs (Bedrock vs SageMaker, RAG store choice, Lambda vs
  AgentCore) are informed by the assess/design briefs.
- **arch-validate** — the Well-Architected **GenAI + ML Lenses** become the
  GenAI-intersection checklist, supplied by **aws-ai-validate**.
- **arch-risk** — AI-specific risks (hallucination, excessive agency, cost
  runaway, throttling, model deprecation) feed the risk matrix.

## Shared references

Cross-cutting AWS topic depth lives here (not in the skill names); stage skills
cite the relevant file rather than inlining it.

- `references/research-2026.md` — externally verified 2025–2026 evidence
  (Bedrock, SageMaker, agents, CDK deploy, offline testing), confidence-labeled,
  pointing at the `{{research_home}}` OKF Concepts. Re-research before treating
  its version-specific facts as constants.
- `references/corpus-map.md` — what the two seed bundles contain and what to cite
  where, including the **two-lineage warning** (modern `cases/aws-ai` ch01–07 vs
  the grafted legacy ch08–10).
- `references/bedrock.md` — Converse API + tool-use loop, Knowledge Bases/RAG,
  Guardrails, embeddings, inference profiles, model-ID resolution.
- `references/sagemaker.md` — train → pipeline → endpoint → registry, JumpStart,
  the SDK V2/V3 split (HyperPod is a pointer, not a stage).
- `references/agents.md` — Strands (tools, Swarm/Graph, A2A), AgentCore
  (Runtime/Memory/Gateway/Identity/Observability/Policy/Evaluations), MCP.
- `references/boto3-foundations.md` — boto3 sessions/`Config`/retries/pagination,
  IAM least-privilege, VPC endpoints, cost, and the offline test strategy.

## Constraints

- **Offline-first, credentials-gated.** No real AWS call until the gated
  `aws-ai-validate` real-path; nothing that costs money without explicit human
  approval. The always-on default is `botocore` Stubber (the only pure-unit path
  for `bedrock-runtime`, which `moto` cannot mock) + `moto` for supporting infra
  and the SageMaker control plane. LocalStack is opt-in (needs Docker up).
  *Carve-out for human exploration:* a person hand-poking the Bedrock **console
  playground** to get a feel for a model early on is fine and encouraged — that is
  manual, ad-hoc, and outside any automated/CI path. The gate is on *automated*
  real-AWS calls and anything the agent runs, not on a human's manual console spike.
- **Don't hardcode fast-moving facts.** Resolve model IDs via
  `list_foundation_models` / inference profiles; note the SageMaker SDK **V2/V3**
  split and the **two conflicting `agentcore` CLIs**; CDK Bedrock L2 constructs
  are still unstable → L1/`AwsCustomResource` fallback. Defer specifics to
  `references/research-2026.md` and re-verify.
- **Trade-offs, not advocacy** (inherits arch-*'s first law). Managed (Bedrock)
  vs self-hosted (SageMaker) vs framework (Strands/AgentCore) is a spectrum with
  cost/latency/control trade-offs — present positions, let the human place the
  cursor.
- **Cite, don't paraphrase.** Modern patterns come from `cases/aws-ai` ch01–07;
  the legacy lineage (ch08–10) is flagged and corrected, never copied verbatim
  (e.g. its `\n\nHuman:` completion format and classic `create_agent` path). The
  concept-only `cases/aws` bundle is backdrop, not implementation.
- **Fill the real gaps with executed code, not prose.** SageMaker
  (train→pipeline→endpoint), CDK-Python deploy, the native `bedrock-runtime`
  Converse tool-use loop, and the test harness are absent from the corpus — the
  family supplies them as code it actually runs (the `aws-ai-validate` harness is
  the proof).
