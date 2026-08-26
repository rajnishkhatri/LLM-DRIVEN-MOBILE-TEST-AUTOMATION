---
name: aws-ai-design
type: skill
description: >-
  AWS-AI capability workflow stage 2: design the AI/ML solution once a service
  is chosen — agent topology (single vs multi-agent, supervisor / agent-as-tool
  / Swarm / Graph), RAG/Knowledge-Base and vector-store shape, conversation
  memory, and the guardrail / Cedar / IAM boundaries. Use when the user says
  "design the agent", "single agent or multiple", "where do the guardrails go",
  "what RAG/vector store should we use", "how should memory work", "draw the
  solution architecture", or "what are the IAM boundaries for this Bedrock
  agent". Produces a solution design + diagram + ADR candidates that flow to
  aws-ai-build. Do NOT use to frame the need or pick the service (aws-ai-assess
  first), to write the implementation code (aws-ai-build), to record the ADR
  itself (arch-decide owns that), or to run any AWS call (aws-ai-validate).
---

# Stage 2 — Solution Design

> Binding: `.aws-ai/binding.toml` (see aws-ai-lifecycle). Methodology:
> `{{methodology_source}}` ch03–09. References:
> `../aws-ai-lifecycle/references/agents.md` (topology, memory, MCP/A2A),
> `../aws-ai-lifecycle/references/bedrock.md` (RAG, guardrails), and
> `../aws-ai-lifecycle/references/boto3-foundations.md` (IAM, KMS, PrivateLink).
> Design-time only: no AWS calls, `{{aws_profile}}` stays `<none>`.

Micro-loop: agent drafts the topology and the four safety/data boundaries from
the assess brief → human confirms each boundary → the design flows to
aws-ai-build, with its significant choices spun out as ADR candidates for
arch-decide.

## Agent work

1. **Agent topology — single vs multi-agent, and *why not one*.** Start from the
   capability brief in `{{assess_home}}`. The first determination is the corpus's
   blunt default: a single agent with good tools beats a poorly designed
   multi-agent system, and rebuilding a working single agent as five coordinating
   ones typically triples latency and multiplies failure points
   (`cases/aws-ai/ch04.md:610-612`). So "why not one agent?" is a *required*
   justification before any topology is drawn — the corpus admits only three
   genuine walls: a context window that truly overflows, a real need for
   parallelism, and expertise that provably will not fit one prompt
   (`cases/aws-ai/ch04.md:614-618`). If multi-agent survives that test, pick the
   pattern by **who decides the path** (Table 4.1, `cases/aws-ai/ch04.md:562-604`):
   supervisor–worker for centralized synthesis (`Agent.as_tool()`,
   `cases/aws-ai/ch04.md:100-140`), agent-as-tool for reuse across systems
   (`cases/aws-ai/ch04.md:185-214`), Swarm for autonomous handoffs on an
   unpredictable path (`cases/aws-ai/ch04.md:384-441`), Graph (DAG) when the path
   must be fixed and auditable — compliance, approval chains
   (`cases/aws-ai/ch04.md:528-557`). Depth in
   `../aws-ai-lifecycle/references/agents.md` §2. Emit the topology: nodes,
   who-decides-the-path per edge, and sync-vs-async communication.

2. **Knowledge & memory — two orthogonal questions.** (a) *Retrieval:* does the
   agent need grounding in a corpus? Shape it as a Bedrock Knowledge Base and
   choose who owns generation — `retrieve` returns ranked chunks you feed into
   your own Converse prompt (full control), `retrieve_and_generate` is one managed
   call that answers with citations (`cases/aws-ai/ch09.md:656-683`). Always plan
   to surface citations: an un-cited RAG answer is indistinguishable from a
   hallucination. **Metadata filtering is a first-class correctness lever, not a
   retrieval-config footnote** — for regulated/insurance corpora it is the single
   biggest lever you have. Tag every chunk with domain metadata (`line_of_business`,
   `state`/jurisdiction, `policy_form`, `plan_version`, `effective_date`/
   `expiration_date`) and filter retrieval on it, so a jurisdiction- or
   version-wrong chunk can never surface (a Florida auto policyholder must never
   pull a California homeowners clause). Design the tags and the filter here, not at
   build time. Place the vector-store choice *here* too, as a cost/scale trade-off,
   not at build time: **S3 Vectors** (idle-cheap, ~90% under OpenSearch's OCU floor
   — re-verify the figure against `{{research_home}}`) vs **OpenSearch Serverless**
   (mature, higher idle cost) vs **Aurora pgvector** (co-located with relational
   data) — details in
   `../aws-ai-lifecycle/references/bedrock.md` §5 and research §1.6. (b) *Memory:*
   if the agent must remember across turns or sessions, design AgentCore Memory
   **namespaces** and **strategies** now. Namespaces partition memory so the agent
   does not blur unrelated facts — global `/`, strategy `/strategy/{id}`, actor
   `/actor/{id}`, session `/session/{id}` (`cases/aws-ai/ch03.md:553-562`);
   strategies decide what is extracted into long-term store (built-in /
   built-in-override / self-managed), and "if no strategy is configured, long-term
   memory is not extracted" — an easy silent gap (`cases/aws-ai/ch03.md:563-572`).
   See `../aws-ai-lifecycle/references/agents.md` §4.3.

3. **Tool & integration surface — the seams.** The atomic contract is the `@tool`
   function: type hints + a docstring, where the docstring is the model's
   *selection prompt*, not decoration — so design focused, single-purpose tools
   and give the agent several rather than one mega-tool
   (`../aws-ai-lifecycle/references/agents.md` §1.1). Then decide each seam: a
   local `@tool` when the capability is yours; an **MCP** server when tools must be
   shared across clients or hosted independently (FastMCP exposes tools,
   read-only resources, and prompt templates, `cases/aws-ai/ch05.md:443-478`);
   **A2A** when the peer is a first-class independent agent that publishes its own
   card at `/.well-known/agent-card.json` (`cases/aws-ai/ch05.md:629-631`). Flag
   `use_aws` explicitly as a **design-time trust decision**: it translates natural
   language into AWS CLI calls under the caller's configured credentials
   (`cases/aws-ai/ch02.md:384-416`), so it inherits whatever the execution role
   allows — scoping that role is a boundary item for step 5, never a default grant.
   Agent-communication depth in `../aws-ai-lifecycle/references/agents.md` §3.

4. **Guardrail & safety placement — two controls, two layers.** The design must
   put each in the request path deliberately. **Bedrock Guardrails** filter *text*
   — toxicity, PII, denied topics, RAG grounding — on model input and output, and
   they never see a tool call: "if your agent decides to call a refund tool with
   amount=$50,000, the guardrail doesn't see that decision"
   (`cases/aws-ai/ch07.md:753-758`). **AgentCore Policy (Cedar)** governs *actions*
   — it intercepts every tool call *before* it executes and returns a deterministic
   permit/deny regardless of prompt phrasing (`cases/aws-ai/ch07.md:787-810`), and
   because Cedar reads the authenticated user's attributes it expresses
   context-dependent rules guardrails cannot ("only a physician in the same
   department may read a patient record", `cases/aws-ai/ch07.md:814-820`). **The
   Cedar enforcement point follows the host (from assess):** on **AgentCore
   Runtime** it is **AgentCore Policy**; on a **Lambda- or ECS-hosted** agent it is
   **Amazon Verified Permissions** — the same Cedar language, evaluated in your code
   via an `is_authorized` call before each tool dispatch. Lead with the one that
   matches the chosen host, not with AgentCore Policy by default. Place
   Guardrails at the model boundary (Converse-native `guardrailConfig`, or Strands
   `guardrail_id` evaluating both input and output, `cases/aws-ai/ch07.md:764-781`;
   standalone `apply_guardrail` for text Bedrock did not generate) and Cedar at the
   tool boundary; add a contextual-grounding threshold on any RAG path. See
   `../aws-ai-lifecycle/references/bedrock.md` §6 and `agents.md` §4.7.

5. **IAM & security boundaries — least privilege, designed now.** The load-bearing
   trap: a Bedrock execution role needs **both** the `foundation-model/*` **and**
   the `inference-profile/*` resource ARNs — "Two resource types, not one" —
   because any modern `us.`/`global.` model id is an inference-profile id; omit the
   second and you get an `AccessDenied` whose message never says what is missing
   (`cases/aws-ai/ch06.md:72-81`). The recognizable symptom: *it works in the
   console but the Lambda gets `AccessDenied`*, and the failure is intermittent — it
   succeeds whenever the profile happens to route to a region you allowed and fails
   otherwise. When the policy's resource ARN names a model id, write that segment as
   a startup-resolved pattern/wildcard (e.g. `inference-profile/us.anthropic.claude-*`,
   an example to re-verify) with a comment marking it *a pattern, not a pinned
   constant* — so the policy does not contradict the never-hard-code-a-model-id rule
   the rest of the design follows. Enumerate only the actions a principal needs —
   never `AmazonBedrockFullAccess` (`cases/aws-ai/ch08.md:425`), e.g. an agent
   scoped to `PrepareAgent` + `InvokeAgent` (`cases/aws-ai/ch08.md:427-440`) — and
   split roles by trust level (a read-only finance agent vs a write-capable ops
   agent, `cases/aws-ai/ch08.md:443`). Add KMS with a `kms:ViaService`-scoped key
   policy for at-rest encryption of agents and knowledge bases
   (`cases/aws-ai/ch08.md:49-79`), and, for private traffic, PrivateLink interface
   endpoints paired with an `aws:sourceVpce` IAM condition so calls are *rejected*
   unless they arrive through your endpoint (`cases/aws-ai/ch08.md:82`,
   `cases/aws-ai/ch08.md:422`). The SageMaker specifics — a pipeline role's
   `iam:PassRole` gate, an invoker limited to `sagemaker:InvokeEndpoint` — live in
   `../aws-ai-lifecycle/references/boto3-foundations.md` §3–4.

6. **Emit the design + diagram + ADR candidates.** Write the solution design to
   `{{design_home}}<target>/solution-design.md`, and **open it with a short TL;DR /
   recommendation** — the chosen topology, vector store, guardrail/Cedar split, and
   IAM stance in a few lines — before the detailed sections; a recommendation-first
   structure serves the reader better than prose-then-detail. Then the full
   sections: topology, knowledge/memory shape,
   tool and integration seams, guardrail + Cedar placement, and IAM/KMS/PrivateLink
   boundaries — each with its least-worst pick *and* the losing alternatives named.
   Draw a `{{diagram_notation}}` diagram of the request path (guardrail → agent →
   Cedar → tools) showing where memory and the KB attach and where the trust
   boundaries fall. List the ADR candidates — any choice carrying a significant
   trade-off: single-vs-multi-agent, vector store, managed-vs-self-owned RAG
   generation, and the guardrail/Cedar split — for hand-off to arch-decide. If
   `{{constitution}}` is set, consult it (model-access policy, data residency,
   cost ceilings) before proposing anything that touches those limits, and flag any
   conflict rather than silently designing around it.

## Human gate

The human confirms four boundaries **separately** — topology (especially any
jump to multi-agent), knowledge/memory shape, guardrail + Cedar placement, and
the IAM boundary — not one bundled "yes" (the conflated-axes rule inherited from
arch-style). A multi-agent topology that fails the "why not one agent?" test is
surfaced as a named antipattern with its latency and failure-point cost, then
deferred: it is the human's call, recorded with its consequences in the ADR.
Advance → **aws-ai-build**; the ADR candidates → **arch-decide**.

## Constraints

- **Design-time only.** No AWS calls, no credentials — `{{aws_profile}}` stays
  `<none>`. This stage *draws* the boundaries; it does not test them (that is the
  gated aws-ai-validate harness).
- **Least-worst, not best** (inherits arch-*'s first law). Managed Bedrock vs
  self-hosted SageMaker vs the Strands/AgentCore framework is a cost/latency/control
  spectrum — present the cursor position, let the human place it.
- **Modern spine is the default.** Design on Strands + Bedrock AgentCore + the
  native Converse path. The legacy classic-agent lineage (`cases/aws-ai` ch08–09 —
  `create_agent`, the `\n\nHuman:`/`max_tokens_to_sample` completion format) is
  recognized so you don't inherit it, never chosen; cite it only for its
  version-agnostic IAM/KMS JSON.
- **Don't freeze drift into the design.** Model ids, vector-store pricing, and
  AgentCore service GA dates move monthly — mark them as choices to re-verify
  against `{{research_home}}` and resolve dynamically, not constants baked into the
  topology.
