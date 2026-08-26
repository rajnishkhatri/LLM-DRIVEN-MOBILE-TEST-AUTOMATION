---
name: aws-ai-assess
type: skill
description: >-
  Stage 1 of the AWS-AI capability workflow (aws-ai-*): frame the AI/ML need
  and SELECT the AWS service before anything is built — the design-time join
  with the arch-* architect family. Runs the decision-readiness,
  need-classification, and service-selection determinations, then presents a
  scored managed-vs-self-hosted-vs-framework matrix and writes a capability
  brief that flows to arch-decide as ADR candidates. Use when the user asks
  "which AWS AI service should we use", "Bedrock or SageMaker", "do we need an
  agent or a fine-tuned model", "RAG vs fine-tune vs prompt", "is this feasible
  on AWS AI", or reaches here from arch-style/arch-decide needing an AWS AI
  option assessed — and whenever a Bedrock/SageMaker/AgentCore build is about to
  start with no capability decision on file (jumping past this is the Accidental
  Architecture antipattern in AWS clothing). Do NOT use to design the chosen
  solution's topology (aws-ai-design), to write code (aws-ai-build), to deploy
  (aws-ai-deploy), or to make any AWS API call — this stage touches no
  credentials.
---

# Stage 1 — Assess & Select the AWS AI Capability

> Binding: `.aws-ai/binding.toml` (see aws-ai-lifecycle). Methodology:
> `{{methodology_source}}` ch01 (the Bedrock-vs-SageMaker table) + ch10 (the
> energy/cost customization ladder); `{{methodology_secondary}}` ch13 (the
> SageMaker deploy-mode taxonomy). References: `../aws-ai-lifecycle/references/`
> `bedrock.md`, `sagemaker.md`, `agents.md` for the three positions on the
> service spectrum; `boto3-foundations.md` for cost/quota/IAM framing;
> `research-2026.md` for fast-moving facts (model IDs, inference profiles).
> Principles: `{{constitution}}` (model-access policy, data-residency, cost
> ceilings) — consulted before the human gate, `<none>` skips it.

Micro-loop: the agent runs the six determinations and presents a scored
service-selection matrix (managed Bedrock ↔ self-hosted SageMaker ↔ framework
Strands/AgentCore) → the human picks capability class, service, model/approach,
and cost ceiling *separately* → the pick flows to **arch-decide** as ADR
candidates, then to **aws-ai-design**. No AWS calls in this stage.

## Agent work

1. **Confirm decision-readiness.** You cannot pick a service without the inputs
   that discriminate between them, so name each one and its state: capability
   wanted (what the system must do, in the user's words), data available (own
   corpus? labeled? where does it live, and under what residency rule?),
   latency/throughput target, request volume/shape (steady vs spiky vs batch),
   budget ceiling, and compliance/data-residency constraints. A missing input is
   *named as a `needs-input` tag on the candidates it affects* — never silently
   assumed, because the assumption is exactly what later collapses the choice
   (spiky volume assumed steady picks a real-time endpoint that then bills 24×7).
   Consult `{{constitution}}` for any hard model-access, residency, or cost rules
   that pre-eliminate options before the matrix is even built.
2. **Classify the need — which branch of the AWS Agentic Stack.** Generative or
   agentic (reason over language, call tools, RAG) → **Bedrock / AgentCore**;
   custom-model, fine-tuning, or classic ML (tabular, forecasting, CV training) →
   **SageMaker AI**; off-the-shelf perception/NLP (OCR, transcription, entity
   extraction, image labels) → a **managed AI service** (Textract/Transcribe/
   Comprehend/Rekognition — breadth beyond this family's deep references, so
   re-verify current API surface against AWS docs rather than citing here). **A
   turnkey internal Q&A assistant over your own documents** (an employee portal;
   IT/HR/policy self-service) → **Amazon Q Business** — a purpose-built,
   permission-aware managed assistant with built-in connectors, retrieval, and a
   ready UI, priced per user. For that exact shape it is often the *best default*:
   it delivers what a hand-assembled Bedrock Knowledge Base + RAG + custom UI
   would, without the build. Reach for DIY Bedrock RAG instead only when you need
   custom orchestration, tool use, or per-token economics at high volume
   (re-verify Q Business's current quotas/pricing against AWS docs — it moves fast
   and is beyond this family's deep references). **When Q Business is the
   recommended path, address *its own* trust/safety controls — built-in admin and
   content/topic controls, response guardrails, document-level ACLs
   (permission-aware retrieval), and grounding/citations — not only the Bedrock-DIY
   Guardrails path;** in a regulated context (insurer, health, finance) name those
   controls explicitly or flag their absence as a real gap, because the recommended
   path's own trust/safety controls are the load-bearing question. The
   book frames the same split: the Bedrock-vs-SageMaker decision table
   (`cases/aws-ai/ch01.md:128-148`) — Bedrock for rapid managed FM/agent work,
   SageMaker AI for deep training/hosting control — sitting inside the three-tier
   stack (managed Bedrock → AgentCore runtime → do-it-yourself SageMaker,
   `cases/aws-ai/ch01.md:121-124`). For the classic-ML branch, the SageMaker
   capability taxonomy is `cases/aws/ch13.md:313` (concept-only in the corpus).
   Output: the capability class, plus any branch that is a live contender rather
   than a foregone conclusion.
3. **Build the service-selection matrix.** Treat managed (Bedrock) ↔ self-hosted
   (SageMaker) ↔ framework (Strands/AgentCore) as a **spectrum, not three boxes**,
   and score it the way arch-style scores styles: the **driving characteristics
   are the rows** — unit cost, latency, control/customization depth, operational
   burden, and data-gravity (how much your data must move to reach the model) —
   and each candidate is a column. Pull the per-position facts from the
   references, not memory: `bedrock.md` (serverless per-token, Converse default,
   Knowledge Bases/RAG, guardrails), `sagemaker.md` (endpoint instance-hour
   billing, the four deploy modes, scale-to-zero, the SDK V2/V3 split), and
   `agents.md` (Strands authors / AgentCore hosts — orthogonal, and AgentCore
   Runtime needs ARM64/Graviton). Note where a row is a genuine trade rather than
   a winner (Bedrock trades control for zero ops; SageMaker trades ops burden for
   cost/latency control at steady high volume). When determination 2 flagged a
   turnkey internal assistant, add **Amazon Q Business** as a fourth column: it
   typically wins the operational-burden and time-to-value rows and loses the
   control/customization and per-token-economics rows — make that trade explicit
   rather than silently defaulting to a DIY Bedrock-RAG build.
4. **Select the approach and model — cheapest rung that clears the bar.** For a
   generative need, walk the customization ladder from the corpus, whose rungs
   escalate in energy *and* cost *and* build-complexity together: prompt
   engineering → RAG → parameter-efficient tuning → full fine-tune → train from
   scratch (`cases/aws-ai/ch10.md:47-61`). Pick the lowest rung that meets the
   requirement — RAG over fine-tuning whenever the gap is knowledge rather than
   behavior — and record why the cheaper rung was rejected if you climb. Treat
   **"you have documents, not a labeled Q&A training set"** as a *standalone*
   knockout for fine-tuning, not a line item buried in build cost: fine-tuning
   needs labeled training data the corpus doesn't contain, so a "just fine-tune the
   PDFs" plan fails on missing inputs before economics even enter — the easiest
   rebuttal is that their plan needs data they don't have. If RAG
   is in scope, name the embeddings model and vector store as sub-decisions
   (Titan Text v2 / Cohere v3–v4; OpenSearch Serverless vs the cheaper S3 Vectors
   vs pgvector — see `bedrock.md`). **Resolve model IDs dynamically, never
   hard-code them**: they are examples to re-verify via `list_foundation_models`
   / `list_inference_profiles`, many newer models are *inference-profile-only*
   (a bare id throws `ValidationException`), and the `us.`/`eu.`/`global.`
   profile prefix is part of the id (`research-2026.md`).
5. **Draw the feasibility envelope.** Turn the pick into a cost/latency/quota
   sanity check the human can veto on: order-of-magnitude token or instance-hour
   cost at the stated volume, whether the latency target is reachable on the
   chosen path, and whether default service quotas cover the throughput
   (`boto3-foundations.md` for the cost and IAM framing). When a managed assistant
   (Amazon Q Business) and a Bedrock DIY build are both in play, give their costs
   as **two shapes, not one blended band** — managed is **per-user** (scales with
   headcount), DIY is **per-token** (scales with query volume); the pricing *shape*
   is the decision axis, not a single number. State the **crossover** explicitly
   (the user-count/query-volume where the per-token bill overtakes the per-seat
   bill), and note the managed-path win below it rests on **build/ops/permissions
   amortization, not per-query math** — DIY only wins once it absorbs its build and
   operations cost. Surface two AI-specific
   risks explicitly for **arch-risk** to carry: **throttling** (`ThrottlingException`
   under burst — needs adaptive retries or provisioned throughput, a cost lever)
   and **model deprecation** (IDs drift release-to-release, so a hard-coded model
   is a scheduled outage). Flag the idle-endpoint cost trap here if SageMaker
   self-hosting is a contender — a real-time endpoint bills per instance-hour
   whether or not it serves a request.
6. **Name the least-worst pick, its losing alternatives, and the ADR candidates.**
   Output = chosen capability class + service + approach/model (all as *examples
   to re-verify*, not constants), the scored matrix, the rejected alternatives
   with the one characteristic that sank each, and the explicit list of decisions
   that need ADRs: **Bedrock vs SageMaker** (always), **RAG store choice** if RAG
   is selected, and **managed vs self-host / Lambda vs AgentCore Runtime** where
   the trade-off is significant. Close with a **VP-ready one-liner** the
   recommendation survives being repeated up the chain by — e.g. *"fine-tuning
   teaches a model how to talk; RAG teaches it what our policies say."* Write the
   capability brief to `{{assess_home}}<target>/capability-brief.md`.

## Human gate

The human confirms **each axis separately — capability class, service,
model/approach, and cost ceiling — not one bundled "yes"** (conflated-axes rule:
a single approval hides which axis they actually agreed to). Before presenting,
re-read `{{constitution}}` and flag any pick that violates a stated model-access,
residency, or cost rule. If the human's choice contradicts a determination,
surface it as a **named antipattern with its cost**, then defer — it is their
call, recorded with consequences in the ADR:

- **Self-hosting a plain FM/RAG job on SageMaker** → paying instance-hours 24×7
  for what Bedrock serves per-token with zero idle cost.
- **Hand-assembling Bedrock KB + RAG + a custom UI for a plain internal-document
  Q&A portal** → rebuilding what **Amazon Q Business** already delivers as a
  purpose-built managed service; justify the DIY only by a real need for custom
  orchestration, tool use, or per-token economics at high volume.
- **Fine-tuning (or provisioned throughput) for low/spiky volume** → build cost
  and committed capacity that the traffic never amortizes; the RAG or prompt rung
  was left on the table (`cases/aws-ai/ch10.md:47-61`).
- **The legacy Bedrock completion path** (`invoke_model` with the
  `\n\nHuman:`/`\n\nAssistant:` + `max_tokens_to_sample` + `response["completion"]`
  format, `cases/aws-ai/ch09.md:686-712`) → a real correctness bug against a
  Converse-era model; the default is `bedrock-runtime.converse`.
- **A hard-coded model id treated as permanent** → a scheduled
  `ValidationException`/model-not-found when the id is deprecated or is
  inference-profile-only.

Advance → **arch-decide** (record the chosen decisions as ADRs) → **aws-ai-design**.
A failing gate loops back here, not around it.

## Constraints

- **Trade-offs, not advocacy** (inherits the family's first law). Managed
  (Bedrock) vs self-hosted (SageMaker) vs framework (Strands/AgentCore) is a
  spectrum with cost/latency/control/ops/data-gravity trade-offs — present the
  positions and let the human place the cursor; never lead with a favored
  service.
- **No AWS calls in this stage.** Assessment is design-time and credential-free;
  quotas, prices, and model availability are *reasoned from the references and
  re-verified*, not fetched. The first real call is the gated `aws-ai-validate`
  step.
- **Don't hard-code fast-moving facts.** Model IDs, inference-profile prefixes,
  and the SageMaker SDK V2/V3 boundary move monthly — label every id and version
  as an example to resolve dynamically (`list_foundation_models` /
  `list_inference_profiles`) and defer specifics to `research-2026.md`. The same
  discipline binds fast-moving **quantitative** claims — vector-store idle costs,
  "%-cheaper" figures, tier/per-seat prices, GA dates, PrivateLink/VPC-parity
  statements — each carries a re-verify marker exactly like model rates; flagging
  model prices while stating a "~90% cheaper" or "idle ~$X/mo" figure as settled
  fact is the inconsistency to avoid.
- **Cite the modern lineage; correct the legacy one.** The Bedrock-vs-SageMaker
  framing and the customization ladder come from the modern half of
  `{{methodology_source}}`; the ch08–10 legacy lineage is cited only to *reject*
  its patterns (the completion-format bug above), never to select them.
