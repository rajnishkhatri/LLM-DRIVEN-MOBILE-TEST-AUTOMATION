---
type: overview
title: 'Analyze Requirements for a Multilingual Financial Support Assistant'
description: 'Walk through AWS certification task 1.1: turn a regulated, multilingual customer-support brief into a Bedrock RAG architecture, a scoped POC, and reusable multi-Region components — with self-checks on FM approach, integration pattern, unused capability, and private Bedrock access.'
tags: [aws-skill, requirements, genai]
---

# Analyze Requirements for a Multilingual Financial Support Assistant

Walk through a sample solution for certification **task 1.1**: analyze a business brief, map drivers to AWS services, validate with a scoped proof of concept, then standardize the pieces that must be identical in every Region.

Requirement analysis is the design-time join between the business brief and the architecture. The exam (and real delivery) punish jumping to a model or a service before the drivers are named. This note is a worked example of that join, not a catalog of every AWS GenAI service.

## Scenario

A multinational financial-services company wants a generative AI assistant for customer support across **15 countries** and **eight languages**. The assistant must:

- Understand customer queries and answer from an extensive knowledge base.
- Integrate with existing customer-relationship management (CRM) systems.
- Comply with financial regulation and data-privacy rules.
- Provide a consistent experience across Regions.
- Cut response times by **70%**.

Those constraints — multilingual, domain-grounded, integrated, regulated, multi-Region, latency-sensitive — are the architectural drivers. Everything below is a response to them.

## Drivers before services

| Driver | Why it matters | Design implication |
|---|---|---|
| Multilingual (8 languages) | Answers must be correct *and* fluent, not just translated | Prefer an FM with strong multilingual reasoning; do not treat language as a post-process |
| Domain-specific financial knowledge | Hallucinated product or policy answers are a compliance failure | Ground generation in the company's own corpus (RAG), not a general-purpose chat model alone |
| CRM integration | Tickets must be created and updated without a new silo | Event-driven join to the existing system of record |
| Regulation and privacy | Data residency and access control are non-negotiable | Regional deployments, encryption, fine-grained IAM, auditable APIs |
| Consistent experience across Regions | Same quality in every jurisdiction | Standardized IaC, prompts, evals, and observability — not 15 one-off stacks |
| 70% faster responses | Current mean time is measured in hours | Near-real-time inference plus a POC that measures latency, not just accuracy |

Exam insight: on regulated-industry items, accuracy and compliance almost always outrank cost. Name the drivers first; the service list is a consequence.

## Mapping drivers to AWS

### Foundation model

Evaluate foundation models available through **Amazon Bedrock**. Select **Anthropic Claude 3.5 Sonnet** for multilingual performance and reasoning. Bedrock keeps the model behind a managed API so the rest of the architecture (RAG, IAM, Regional control) does not change if the model choice is revisited.

Trade-off: a smaller, cheaper model might suffice for FAQ retrieval, but this brief needs cross-language reasoning over financial policy. The cost of a wrong answer dominates token cost.

Match capabilities to the brief. Brand voice, factual accuracy, and faster *email* replies need prompt/filter controls, a knowledge base, and human review for sensitive mail. They do not need a multi-modal FM. Extra modality is extra coupling (ingestion, IAM, eval, cost) with no driver behind it.

#### Self-check: least-important component

**Scenario.** A customer-service department wants generative AI to draft email responses to customer inquiries. Requirements: maintain brand voice, ensure factual accuracy, and reduce response time.

Which architectural component would be **LEAST** important for meeting these requirements?

- A. A content filtering system to detect and prevent inappropriate responses
- B. A human-in-the-loop review process for complex or sensitive inquiries
- C. A knowledge base integration to provide up-to-date product information
- **D. (correct)** A multi-modal foundation model that can process images and text

**Why this is the answer.** The brief is *email drafts* — text in, text out. Brand voice, factual accuracy, and latency do not require vision. A multi-modal FM adds pipeline and cost without serving a named driver.

**Why the other options stay in the architecture.**

- **A** — content filters protect brand voice and stop off-policy drafts before they reach a customer.
- **B** — HITL is how factual accuracy is enforced on complex or sensitive mail without blocking the simple cases that deliver the latency win.
- **C** — a knowledge base is how product facts stay current; prompting alone cannot.

Exam insight: on **LEAST** items, underline the verbs and nouns in the stem first (`draft email`, `brand voice`, `factual`, `response time`). Drop anything that is a real AWS capability with no matching noun.

### Grounding (RAG)

Implement retrieval-augmented generation with **Amazon Bedrock Knowledge Bases**, pointing at financial documentation already stored in:

- **Amazon S3**
- Microsoft SharePoint
- Internal Confluence wiki

RAG is the right default when the corpus changes often (products, policies, regulations) and when answers must be attributable. Fine-tuning would bake a snapshot of policy into weights; it does not replace retrieval for this brief.

#### Self-check: foundation-model approach

**Scenario.** A financial services company wants a generative AI solution for summarizing lengthy financial documents and extracting key financial metrics. The solution must have high accuracy for financial terminology and maintain data privacy.

Which foundation model approach in Amazon Bedrock would be most appropriate?

- A. Use Claude 3 Sonnet with few-shot prompting for financial summarization
- B. Use Llama 3 with RAG (Retrieval-Augmented Generation) for document processing
- C. Fine-tune Titan Text on proprietary financial documents
- **D. (correct)** Use Amazon Bedrock Knowledge Bases with Anthropic Claude and company-specific financial data

**Why this is the answer.** Knowledge Bases keep proprietary documents in the company's AWS environment and retrieve them at inference time, so accuracy for financial terminology comes from the corpus, not from shipping that corpus into a training job. Claude is strong at long, structured summarization; the Knowledge Base supplies the company-specific metrics and terms. No fine-tuning cycle, and no extra copy of sensitive filings leaving the account.

**Why the distractors fail.**

- **A** — few-shot prompting can shape *format*, not load a private corpus. It will miss house terminology and unpublished metrics.
- **B** — Llama 3 plus a hand-rolled RAG path is the same *idea* as Knowledge Bases, but it is custom plumbing (chunking, indexes, IAM, citations) the exam is steering you away from when a managed Bedrock path exists.
- **C** — fine-tuning Titan on proprietary filings improves style at the cost of a training dataset of sensitive financial data, a frozen snapshot of policy, and operational overhead this brief does not need. Privacy is the disqualifier.

Exam insight: when the stem says "high accuracy for *our* terminology" *and* "data privacy," prefer retrieve-in-place (Knowledge Bases) over fine-tune-on-the-corpus.

### CRM join

Use **Amazon EventBridge** so ticket creation and updates are events, not a synchronous write from the assistant into the CRM. The assistant and the CRM stay loosely coupled: a failed CRM call should not take down answer generation, and the CRM can evolve without a new assistant release.

### Conversation orchestration

EventBridge is the *join* to the CRM. It is not the chatbot's control plane. A conversational assistant that must keep session context, pull CRM facts, and *decide* whether to escalate is an orchestrated workflow: **AWS Step Functions** plus RAG.

- Step Functions owns conversation state, branching (answer vs escalate), retries, and execution visibility.
- RAG (Knowledge Bases, or a retrieval step in the state machine) supplies CRM-grounded answers instead of a generic FM completion.
- EventBridge still fires when a ticket should land in the CRM — fire-and-forget, not the decision itself.

**Amazon Bedrock Flows** can chain model steps for multi-hop *generation*. They do not replace a workflow engine when the next action is "open a human ticket" or "wait on CRM data."

Trade-off: a single synchronous `InvokeModel` call is simpler until you have more than one system and a decision point. The moment the brief lists CRM + context + escalation, the coupling belongs in an orchestrator, not in the client.

#### Self-check: integration pattern

**Scenario.** Your company needs a customer-support chatbot that can handle routine inquiries and escalate complex issues to human agents. The chatbot should integrate with the existing CRM and maintain context throughout conversations.

Which integration pattern would be most appropriate?

- A. Synchronous API integration with direct calls to Amazon Bedrock
- B. Asynchronous batch processing using Amazon SQS and Lambda
- **C. (correct)** Orchestrated workflow using AWS Step Functions with retrieval-augmented generation
- D. Streaming integration using Amazon Kinesis and real-time analytics

**Why this is the answer.** Step Functions can orchestrate a workflow that keeps conversation state, calls retrieval against the CRM/knowledge base, and branches to a human agent when confidence or policy says so. RAG is how the bot answers from CRM-grounded facts rather than from the FM's prior. The state machine gives you retries, timeouts, and a visible execution history — the operational surface this brief needs.

**Why the distractors fail.**

- **A** — a direct Bedrock call has no durable conversation state, no CRM retrieval, and no escalation branch. Too few decision points for the stem.
- **B** — SQS + Lambda is a batch/decoupled *processing* pattern. Chat is request/response with session memory, not a queue of documents.
- **D** — Kinesis is continuous data movement and analytics. It is the wrong abstraction for a turn-taking conversation.

Exam insight: count the *systems* and the *decisions* in the stem. One FM call is enough only when both counts are one. CRM + context + escalate is an orchestrator + RAG item.

### API layer

Use **AWS AppSync** as the API. GraphQL's declarative fetch and AppSync's built-in auth controls fit a fleet of mobile and web clients across Regions better than a hand-rolled REST surface that every client must version independently.

Trade-off: REST via API Gateway is the more common exam default. AppSync is justified here by many clients, varying payload shapes, and a need for built-in security controls — not by GraphQL fashion.

### Multi-Region routing

Design a multi-Region deployment and put **AWS Global Accelerator** in front so traffic lands on the closest healthy Regional stack. That serves both latency and data-residency: a jurisdiction that must keep data in-Region still has a local deployment; users elsewhere are not forced through a single far-away endpoint.

## Prove it before you scale

Do not deploy eight languages and 15 countries on day one. Validate feasibility with a **technical proof of concept on Amazon Bedrock**:

- Three Regions with the highest customer volume.
- A subset of the most common queries.
- **Two** languages, not eight.

Connect Knowledge Bases to a *sample* of the financial corpus. The POC question is: can this stack produce accurate, compliant answers on company-specific information, at a latency that makes the 70% target believable?

### Prompts and multi-step work

- **Amazon Bedrock Prompt Management** — versioned templates per query type and language, so tests are systematic rather than one-off playground sessions.
- **Amazon Bedrock Flows** — chain steps for queries that need more than one reasoning hop.

### What the POC showed

| Signal | Result |
|---|---|
| Accuracy on financial queries | 92% |
| Response time | 24 hours → 4–5 seconds |
| Cost | 62% lower support spend at 3× query volume |

Those numbers are the business case for full-scale deployment. They are not a production SLO until the remaining languages, Regions, and corpus are under the same eval harness.

## Standardize what must be identical everywhere

Once the shape is proven, the remaining work is making every Region a clone, not a fork.

- **AWS Well-Architected Framework** and the **Well-Architected Generative AI Lens** as the review bar.
- Reusable infrastructure as code with **AWS CloudFormation**.
- GenAI Ops: **Amazon SageMaker Pipelines** for continuous evaluation — accuracy, bias, and financial-regulation checks across all supported languages.

### Security and governance (same components, every Region)

- Authentication: **Amazon Cognito**
- Encryption: **AWS Key Management Service (KMS)**
- Access: **AWS Identity and Access Management (IAM)**

### Network boundary

When internal documents must not leave the company network, put **Amazon Bedrock behind a VPC interface endpoint (AWS PrivateLink)** and encrypt in transit and at rest. Traffic stays on the AWS network; you still consume a managed FM. Self-hosting on **AWS Inferentia** is stricter isolation and much more operations — use it when the stem forbids AWS-hosted inference, not when it only forbids the *public internet*.

On the exam, "external services" in this pattern usually means public endpoints and third-party APIs, not Bedrock in your account via PrivateLink.

#### Self-check: deployment strategy

**Scenario.** Your company is developing a generative AI application that will process sensitive internal documents to answer employee questions. The application must remain within the company's network boundary and cannot send data to external services.

Which deployment strategy would best meet these requirements?

- **A. (correct)** Use Amazon Bedrock with a private VPC endpoint and data encryption
- B. Deploy foundation models on Amazon SageMaker with model parallelism
- C. Implement Amazon Bedrock Knowledge Bases with cross-region replication
- D. Use AWS Inferentia instances with locally deployed open-source models

**Why this is the answer.** A VPC endpoint keeps Bedrock traffic off the public internet. Encryption covers data in transit and at rest. You get managed FMs without standing up training or inference clusters, which is the usual balance of isolation vs. operational load for this stem.

**Why the distractors fail.**

- **B** — SageMaker *model parallelism* is a training/serving scale technique for large models. It does not answer "stay inside the network boundary." It is also more ops than the brief requires when Bedrock exists.
- **C** — Knowledge Bases plus cross-Region replication is availability and residency. It does not keep inference traffic off the public internet.
- **D** — Inferentia plus local open-source models *can* keep weights and data in your VPC, but the stem does not require you to own the model. It requires a network boundary. PrivateLink on Bedrock meets that with far less expertise in compilation, scaling, and patching.

Exam insight: "network boundary" + a managed-service option pointing at **VPC endpoint / PrivateLink** is almost always that option. Self-host wins only when the stem bans AWS-hosted models or requires on-prem/air-gap.

### Observability

- **Amazon CloudWatch** dashboards and alarms for accuracy, latency, and cost per Region.
- **AWS X-Ray** for distributed tracing when a request is slow.
- A reusable evaluation framework that samples answers across languages and query types so quality drift is visible before customers file tickets.

## Outcome (assumed post-deployment)

Deployed across 15 countries and eight languages. Reported within the first three months:

- 78% reduction in response times (the original target was 70%).
- 42% fewer escalations to human agents.
- 68% improvement in customer-satisfaction scores.

Knowledge Bases plus a standardized RAG path keep answers current as products and policies change. The same components are then reused by other business units — the usual payoff of treating the first Region as a *template*, not a snowflake.

## Architecture takeaway

Task 1.1 is not "pick Bedrock." It is: name the drivers, pick the *minimum* managed path that satisfies them (drop unused modalities; PrivateLink before self-host), prove it on a slice, then freeze the template (IaC, prompts, evals, IAM, observability) so expansion is copy-and-configure. The coupling to watch is the CRM join and the corpus: those are the systems of record; the FM is replaceable.
