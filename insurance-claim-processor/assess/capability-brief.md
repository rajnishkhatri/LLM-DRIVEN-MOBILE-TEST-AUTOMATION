# Capability brief — insurance claim document processor

**VP-ready one-liner:** Fine-tuning teaches a model how to talk; RAG teaches it
what *this* policy says — and for claims, Textract/BDA (or a multimodal FM)
reads the packet, a capable FM extracts, a cheaper FM summarizes, and a
validator decides whether a human must look.

Design-time only. No AWS calls. `aws_profile` stays `<none>`. Binding:
`.aws-ai/binding.toml` (`[roots] claim-document-processor`). Characteristics:
`../worksheets/characteristics-worksheet.md`.

**Cost of being wrong:** high (incorrect payout, PII leak, unauditable
decision). This assess therefore treats integrity, privacy, and audit as
driving rows, not footnotes.

**GATE: PENDING HUMAN — confirm each axis separately:** capability class,
service, model/approach, cost ceiling. Not one bundled "yes."

---

## 1. Decision-readiness

| Input | State |
|---|---|
| Capability wanted | Understand claim documents, extract structured fields, generate a summary, ground against policy information |
| Data available | Claim packets to land in S3; a policy corpus for RAG. Formats (PDF vs text vs image), labeled gold set, residency: **`needs-input`** |
| Latency / throughput | Back-office processing assumed, not interactive chat. SLO / QPS: **`needs-input`** |
| Volume / shape | PoC = 2–3 docs. Production burst (catastrophe): **`needs-input`** |
| Budget ceiling | **`needs-input`**. PoC must stay on-demand (no provisioned throughput) |
| Compliance / residency | Insurance; PII in packets. Region default `us-east-1` until residency is set. Constitution: `<none>` |

Missing inputs do not block a *class* pick. They **do** block treating a
real-time claimant chatbot, a SageMaker real-time endpoint, or a fine-tune
as "the" architecture.

---

## 2. Capability class

**Generative document understanding + extraction + RAG-grounded summary** —
Bedrock branch (`cases/aws-ai/ch01.md:128-148`), with a **managed perception**
contender (Textract / Bedrock Data Automation) under ingest.

Walk the customization ladder (`cases/aws-ai/ch10.md:47-61`): prompt → **RAG**
→ PEFT → full fine-tune → train-from-scratch. **Stop at prompt + RAG.** The
gap is *knowledge* (what this policy says, what this packet contains), not
*behavior*. The brief has documents, not a labeled Q&A training set — that is
a **standalone knockout** for fine-tuning.

Rejected / live-contender branches:

| Branch | Role |
|---|---|
| Amazon Q Business | **Reject for the core path.** Purpose-built for internal employee Q&A with a ready UI — not a claims extraction pipeline that must emit schema-valid JSON into an ops workflow. Keep as a *later* "adjuster asks the policy KB" add-on, not the processor |
| SageMaker custom-model / fine-tune | **Reject for PoC.** No labels; policy changes; idle endpoint cost trap. Live only if a measured prompt+RAG gap is *behavior* (house style that prompt cannot hold) |
| Managed perception (Textract / BDA) | **Live contender under ingest**, not a replacement for the summarizer. Best when packets are scanned PDFs/forms; a multimodal FM (Nova / Claude document blocks) can skip a separate OCR hop for the PoC |
| AgentCore / multi-agent | **Overkill for PoC.** This is a fixed extract → ground → summarize path, not an unpredictable tool-using conversation. Graph/Step Functions later if HITL + core-system writes appear |

---

## 3. Service-selection matrix

Driving characteristics as rows. Scores: ● strong / ◐ mixed / ○ weak.
Fast-moving $ figures are **[re-verify]**.

| Characteristic | Bedrock FM + KB (on-demand) | SageMaker self-host FM | Strands + AgentCore Runtime | Amazon Q Business | Textract / BDA + Bedrock |
|---|---|---|---|---|---|
| Data integrity | ● structured Converse + validator you own | ● you own the head | ◐ agent path adds hops | ○ chat answers, not schema | ● BDA blueprints / Textract forms; still needs an FM for summary |
| Privacy | ● in-account, Guardrails PII | ● VPC, you operate it | ● Cedar at tools | ◐ Q's ACL model | ● in-account |
| Auditability | ● you record model id, prompt, chunks | ● | ◐ more moving parts | ○ less of the invoke you own | ● job ids + JSON |
| Reliability | ● serverless; throttle is the tax | ○ you run HA | ◐ Runtime + FM | ● AWS-managed | ● async jobs + SQS |
| Testability | ● Converse + Stubber | ◐ | ◐ | ○ | ◐ BDA job shapes |
| Configurability | ● `modelId` swap via Converse | ◐ | ● | ○ | ◐ blueprint + FM |
| Unit cost | ● per-token, no idle FM | ○ instance-hours 24×7 | ◐ per-token + Runtime | ◐ per-seat (wrong shape) | ● pay per page + tokens |
| Operational burden | ● | ○ | ◐ | ● | ◐ two services |
| Data gravity | ● corpus stays in S3/KB | ◐ | ● | ◐ Q's store | ● |

**Least-worst pick:** **Amazon Bedrock** (Converse + Knowledge Bases) for
extraction, RAG, and summary; **S3** as the document SoR; **in-process /
S3-backed policy RAG for the PoC**, promoting to a Bedrock Knowledge Base
when the corpus outgrows a handful of files. Add **Textract or Bedrock Data
Automation** when packets are scanned/multimodal — not on day 1 if samples
are text.

SageMaker loses on idle cost for a plain FM/RAG job (named antipattern:
*self-hosting a plain FM/RAG job*). Q Business loses on schema-valid
extraction and workflow control (named antipattern: *hand-assembling a chat
portal when you needed a pipeline* — here the inverse: do not buy a portal
when you needed a pipeline). AgentCore loses until there are tools a Cedar
policy must gate.

---

## 4. Approach and model

- **Rung:** prompt engineering + RAG. Fine-tune rejected (knowledge vs
  behavior; no labels; policy snapshot goes stale).
- **Generation API:** `bedrock-runtime.converse` — **never** the legacy
  `invoke_model` + `"prompt"` + `max_tokens_to_sample` +
  `response["completion"]` path in the exam snippet (`cases/aws-ai/ch09.md:686-712`).
  That format is a correctness bug against current-gen models. Converse is
  how we swap extract vs summarize models without rewriting parsers.
- **RAG:** `retrieve` + our Converse prompt (we own citations and the
  validator). `retrieve_and_generate` is the losing alternative: less
  control of schema and provenance. PoC: local policy corpus + embeddings
  *or* keyword retrieval so the offline harness does not need a live KB.
- **Embeddings (when the KB is promoted):** Titan Text v2
  (`amazon.titan-embed-text-v2:0`, example — **re-verify**) at 512 or 1024
  dims; record model+dims next to the index.
- **Vector store (when promoted):** S3 Vectors if idle cost dominates
  **[re-verify]**; OpenSearch Serverless if hybrid search + filters are the
  measured need. Metadata filters: `line_of_business`, `jurisdiction`,
  `policy_form`, `effective_date` — a Florida auto claim must not retrieve a
  California homeowners clause.

### Task → model family (examples to re-verify, never constants)

Resolve at runtime via `list_foundation_models` / `list_inference_profiles`.
Many current ids are **inference-profile-only** (`us.` / `global.` prefix).
Bare ids throw `ValidationException`. `anthropic.claude-v2` in the exam
snippet is retired for this design.

| Task | Family (exam + corpus) | Why this rung | Losing alternative |
|---|---|---|---|
| **Document understanding** | Amazon **Nova** multimodal *or* Claude with `document` content blocks; Textract/BDA if scanned forms dominate | Packets mix text, photos, PDFs (`cases/aws-c01/bedrock-models.md`, `multimodel.md`) | A text-only FM on a JPEG claim; a vision FM on already-plain-text PoC samples (unused modality) |
| **Information extraction** | Capable instruction-follower (Claude Sonnet-class *example*) at **temperature 0** / current-gen: `maxTokens` only | Structured JSON, low creativity; integrity is the driver | Instant/Haiku as the *only* extract model before eval says it holds fields |
| **Summary generation** | Cheaper/faster (Claude Haiku-class or Nova Lite *example*) | Short, grounded restatement; cost-efficiency row | Same frontier model as extract — pays reasoning tax twice |
| **Policy retrieval** | Titan Embeddings v2 *example* + KB, or keyword for PoC | Knowledge gap, not behavior | Fine-tune Titan on policy PDFs |

**Orchestration pattern:** **cascade**, not aggregation. Extract on the
capable model; if the validator fails schema, retry once or escalate;
summarize on the cheap model. Aggregation (vote three models) is for
high-stakes diagnosis, not a 2–3 doc PoC (`cases/aws-c01/bedrock-models.md`).

**Inference config:** extraction wants determinism (low temperature / omit
sampling on current-gen Claude). Summary may allow mild temperature.
Stop sequences / JSON-mode where the model supports structured output
**[re-verify]**.

---

## 5. Feasibility envelope

| Check | PoC reading | Production caveat |
|---|---|---|
| Token cost | 2–3 short text claims: cents. Order-of-magnitude: extract prompt ≈ document tokens + schema; summary ≈ extracted JSON + retrieved chunks **[re-verify rates]** | Catastrophe burst × frontier model × retries is the runaway. Cap cascade; measure $/claim |
| Latency | Batch: tens of seconds per claim is acceptable | Interactive adjuster UI would need streaming (`converse_stream`) — not in the brief |
| Quota | On-demand Bedrock TPM/RPM **[re-verify]** | `ThrottlingException` under burst → adaptive SDK retries (C2), then a queue, not a tight loop |
| Idle cost | Zero on Bedrock on-demand | SageMaker real-time endpoint bills 24×7 even at 0 QPS |

**AI-specific risks for arch-risk:**

1. **Throttling** — burst of claims after a storm. Needs C2 (adaptive retries,
   one layer) + C10 (queue / shed) + C11 (extract without summary).
2. **Model deprecation** — hard-coded `anthropic.claude-v2` is a scheduled
   `ValidationException`. Resolve ids; record the resolved id on every result.

---

## 6. Least-worst pick, losers, ADR candidates

| Axis | Recommendation | Human confirms separately |
|---|---|---|
| Capability class | Generative FM + RAG; optional managed OCR | |
| Service | Amazon Bedrock (Converse + later KB); S3 SoR | |
| Approach | Prompt + RAG; cascade extract→validate→summarize | |
| Cost ceiling | On-demand only for PoC; no provisioned throughput | **`needs-input`** |

**Losers and the characteristic that sank them:**

- SageMaker self-host — **cost-efficiency** (idle instance-hours).
- Amazon Q Business — **data integrity** (not a schema pipeline).
- Fine-tune / provisioned throughput — **feasibility** + missing labels.
- Legacy `invoke_model` completions — **correctness** (named antipattern).
- Multi-agent / AgentCore — **simplicity / testability** until tools exist.
- One frontier model for every step — **cost-efficiency**.

**ADR candidates (arch-decide):**

1. Bedrock vs SageMaker vs Q Business (always).
2. RAG store: PoC in-process vs Bedrock KB + S3 Vectors vs OpenSearch.
3. Document understanding: multimodal FM vs Textract/BDA.
4. Host: single Python modular monolith (PoC) vs Lambda vs Step Functions
   vs AgentCore Runtime.

Advance → **arch-decide** (record) → **aws-ai-design**.
