# Capability brief — multi-tenant portfolio summarizer

**VP-ready one-liner:** Fine-tuning teaches a model how to talk; RAG teaches it
what *this* client's portfolio says — and for a financial multi-tenant app the
retrieval plane, not the model, is the isolation boundary.

Design-time only. No AWS calls. `aws_profile` stays `<none>`. Binding:
`.aws-ai/binding.toml` (confirmed 2026-08-13).

**Cost of being wrong:** high. A cross-tenant hit on semantic search is a
portfolio leak — client confidentiality, regulatory exposure, and loss of the
engagement. This assess therefore treats isolation as a driving characteristic,
not a retrieval-config footnote.

---

## 1. Decision-readiness

| Input | State |
|---|---|
| Capability wanted | Summarize a corporate customer's portfolio from their own documents via Amazon Bedrock |
| Data available | Per-tenant portfolio corpus (statements, holdings, IPS). Location / residency / existing S3 layout: **`needs-input`** |
| Latency / throughput | Interactive summarization assumed. SLO / QPS: **`needs-input`** |
| Volume / shape | Spiky analyst use, not 24×7 inference. **Tenant count is load-bearing** for silo vs pool cost: **`needs-input`** |
| Budget ceiling | **`needs-input`**. Isolation cost (per-tenant store idle) will dominate token cost if tenant count is large |
| Compliance / residency | Financial multi-tenant; absolute isolation between corporate customers. Region default `us-east-1` until residency is set. Constitution: `<none>` |

Missing inputs are tagged on the candidates they affect. They do not block a
service pick; they *do* block treating a pooled vector index as "absolute."

---

## 2. Capability class

**Generative RAG over a private corpus** — Bedrock / AgentCore branch
(`cases/aws-ai/ch01.md:128-148`). The gap is *knowledge* (what this tenant's
portfolio contains), not *behavior*. Walk the customization ladder
(`cases/aws-ai/ch10.md:47-61`): prompt → **RAG** → PEFT → full fine-tune →
train-from-scratch. Stop at RAG.

Rejected branches:

| Branch | Why it loses |
|---|---|
| SageMaker custom-model / fine-tune | No labeled Q&A set; portfolios change; fine-tune does not teach fresh holdings. Knockout: documents, not a training set |
| Amazon Q Business | Purpose-built for *internal* employee Q&A with document ACLs — not a client-facing multi-tenant financial product that must *guarantee* isolation you can audit |
| Managed perception (Textract-only) | OCR may sit *under* ingest; it is not the summarizer |

Live contender, not a foregone conclusion: **how much agent surface** — a
retrieve-then-Converse path vs a Strands agent with a retrieve tool. Both stay
on Bedrock. Topology is a design-stage call.

---

## 3. Service-selection matrix

Driving characteristics as rows. Scores are relative (● strong / ◐ mixed / ○
weak). Fast-moving $ figures are **[re-verify]**.

| Characteristic | Bedrock managed FM + KB | SageMaker self-host FM | Strands + AgentCore Runtime | Amazon Q Business |
|---|---|---|---|---|
| Unit cost | ● per-token, no idle FM | ○ instance-hours 24×7 | ◐ per-token + Runtime | ◐ per-seat (wrong shape) |
| Latency | ● serverless | ◐ you size it | ● | ● |
| Control / isolation depth | ◐ KB + IAM + metadata; silo is on you | ● full, you operate it | ● Cedar at the tool boundary | ○ ACL model you do not own |
| Operational burden | ● | ○ | ◐ | ● |
| Data gravity | ● corpus stays in-account | ◐ endpoints + your store | ● | ◐ Q's store |

**Least-worst pick:** Amazon Bedrock (Converse + Knowledge Bases) for generation
and managed ingest; **Strands on AgentCore Runtime** as the host so Cedar can
sit on the retrieve tool (`cases/aws-ai/ch07.md:830-841`). SageMaker loses on
idle cost for a plain FM/RAG job (named antipattern). Q Business loses on
control of the isolation boundary.

---

## 4. Approach and model

- **Rung:** RAG. Fine-tune rejected (knowledge vs behavior; no labels; stale the
  day a holding changes).
- **Generation:** `bedrock-runtime.converse` — never the legacy
  `\n\nHuman:` / `max_tokens_to_sample` path (`cases/aws-ai/ch09.md:686-712`).
- **Retrieval API:** `retrieve` (you own the prompt and the fail-closed tenant
  check), not `retrieve_and_generate` as the isolation path
  (`../aws-ai-lifecycle/references/bedrock.md` §5).
- **Embeddings:** Titan Text Embeddings V2 (`amazon.titan-embed-text-v2:0`,
  dims 256/512/1024) — example to **resolve dynamically**; keep index and query
  dims identical (`bedrock.md` §7).
- **Vector store (assess-level):** **siloed OpenSearch Serverless collection
  per tenant** as the isolation default; S3 Vectors as the cost-down alternative
  when tenant count makes the OSS OCU floor unbearable
  (`docs/research/aws-ai-bedrock-sagemaker-research.md` §1.6 — idle ~$345/mo
  2-OCU / S3 Vectors ~90% under that, **[re-verify]**). Pinecone is a named
  losing alternative for "absolute" isolation (third-party trust boundary;
  namespaces are logical). Detail in the design.

Model IDs are examples. Resolve via `list_foundation_models` /
`list_inference_profiles`. Grant **both** `foundation-model/*` and
`inference-profile/*` ARNs.

---

## 5. Feasibility envelope

- **Token cost:** interactive summarization, per-token. Order-of-magnitude
  depends on volume (**`needs-input`**).
- **Store idle:** per-tenant OSS collection inherits the serverless OCU floor
  **[re-verify]**. At tens of tenants this is the isolation tax; at hundreds,
  S3 Vectors or a hybrid (hot tenants siloed, long-tail more carefully pooled)
  must be re-opened — pooling is never "absolute."
- **Latency:** retrieve + Converse is reachable for interactive use; multi-agent
  would roughly triple it (`cases/aws-ai/ch04.md:610-612`).
- **Risks for arch-risk:** (1) **throttling** on burst (`ThrottlingException` →
  adaptive retries / provisioned throughput); (2) **model deprecation** if an id
  is hard-coded; (3) **cross-tenant retrieval** if isolation is only a metadata
  filter.

---

## 6. ADR candidates → `arch-decide`

1. **Bedrock vs SageMaker** — Bedrock (this brief).
2. **RAG store + tenancy model** — siloed OSS vs S3 Vectors vs pooled+filter vs
   Pinecone (design expands).
3. **`retrieve` vs `retrieve_and_generate`** — `retrieve` for isolation control.
4. **Host** — AgentCore Runtime (Cedar native) vs Lambda + Amazon Verified
   Permissions (same Cedar language).

Losing alternatives and the characteristic that sank each: SageMaker (idle
cost), Q Business (isolation you cannot audit), fine-tune (wrong rung), shared
Pinecone index (trust boundary + logical-only partition).

---

## Human gate (assess) — confirm separately

1. **Capability class** — generative RAG, not fine-tune / classic ML.
2. **Service** — Bedrock + Strands/AgentCore, not SageMaker, not Q Business.
3. **Model / approach** — RAG via `retrieve` + Converse; embeddings resolved at
   build; no hard-coded model id.
4. **Cost ceiling** — accept per-tenant store idle as the isolation tax, or
   name a ceiling that forces us off "absolute" silo.

A single "go" hides which axis you agreed to.
