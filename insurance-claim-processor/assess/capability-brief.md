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

---

## v2 addendum — data-preparation plane (2026-09-23)

**VP-ready one-liner:** *Managed AI services read the claim, code checks the
facts, and the foundation model only judges what is left. Nothing it sees
carries a raw SSN.*

Design-time only; no AWS calls; `aws_profile` stays `<none>`.
**GATE: RATIFIED 2026-09-23 ("ratify as recommended" — design/hld-v2-data-prep.md §6; was PENDING HUMAN)** (provisional batch, A2-a). R3 ratified
each axis as drafted: capability class per need, service per need,
approach/model, cost ceiling. Notes on the ratified amendments: §8.
**Fixed input C3-a:** Glue Data Quality, Comprehend, Textract, Transcribe,
Lambda. **No** SageMaker, **no** Rekognition.
This addendum records *why*, the feasibility envelope, and the losers; it
does not reopen C3-a.
**Stakes:** high. The data feeds an insurer's payout decision, and the new
inputs (voice, police reports) are PII-dense.
**Constitution:** the workspace AI constitution is `<none>`, so no model-access
or residency rule pre-eliminates an option. `us-east-1` stays pinned
(ledger).

### 1. Decision-readiness (v2)

| Input | State |
|---|---|
| Capability wanted | Validate structured intake batches; get entities, key phrases, sentiment and PII from narratives; OCR + key fields from police reports and repair estimates; transcribe FNOL calls with PII redaction; loss-run table → text; format all of it for Claude; improve DQ from model disagreement |
| Data available | **Synthetic only** (spec §3): CSV batches, narratives, one-page document PNGs (stdlib PDF → `sips`), 16 kHz WAV calls (`say`), a loss-run CSV. No labeled training set for any custom model. |
| Latency / throughput | Back-office **batch**; minutes per batch acceptable. SLO **`needs-input`**. |
| Volume / shape | PoC: 16 rows, ≤ 11 processed claims, ≤ 3 calls, ≤ 8 images. Production volume and CAT burst: **`needs-input`**. |
| Budget ceiling | PoC: the existing **$10/month** account budget (`../build/DEPLOY-LEDGER.md:17`) covers v1 + v2. Production: **`needs-input`**. |
| Compliance / residency | PII-dense. Transcribe redaction is configured for `en-US`; Comprehend PII detection for English. Residency: **`needs-input`** (us-east-1 pinned). AI-services content opt-out: **R8c-a**, owner action pending (§8). |

`needs-input` items block *production sizing* (Textract TPS quota,
Transcribe concurrency, batch size). They do not block the service choices,
which are driven by capability, integrity and privacy.

### 2. Capability classification (per need)

| Need | Class | Live contenders |
|---|---|---|
| N1 Batch structural validation | **Not AI** — data engineering (rule evaluation over a table) | Glue DQ · Lambda-only rules · Deequ / Great Expectations |
| N2 Narrative NLP (entities, phrases, sentiment, PII, language) | **Managed NLP service** | Comprehend · FM (Claude) doing NLP in the extraction call · Bedrock Guardrails sensitive-info filter (PII only) |
| N3 Document OCR + key fields | **Managed perception** | Textract (AnalyzeDocument QUERIES / AnalyzeExpense) · Claude vision alone (image blocks) · Bedrock Data Automation |
| N4 Call transcription + PII redaction | **Managed speech** | Transcribe standard batch + ContentRedaction · Transcribe Call Analytics |
| N5 Loss-run table → text | **Not AI** — deterministic template | Lambda template · FM summarization · SageMaker Processing (**excluded, C3-a**) |
| N6 Formatting for Claude + dialog | **Generative FM interface** (unchanged v1 branch) | Converse image blocks · Converse `document` blocks (PDF) |
| N7 Themes across a batch | **Aggregation of N2 output** | Key-phrase / entity aggregation · Comprehend topic modeling (async) · FM clustering |
| N8 Feedback proposals | **Not AI** — deterministic pattern + replay | Bounded proposal set · FM-generated rules (**rejected: unbounded**) |

The customization ladder (`cases/aws-ai/ch10.md:47-61`) **stays at the
prompt rung**. Custom Comprehend entity recognition, Textract adapters and
Transcribe custom language models each need **labeled training data we do not
have**. That is the same standalone knockout as fine-tuning in §2. Structured
IDs (policy number, VIN) are handled by the deterministic canonicalizer
instead.

### 3. Service-selection matrices (contested needs)

Rows = v2 driving characteristics (+ operational burden, data gravity).
● strong / ◐ mixed / ○ weak. All $ are **[re-verify]**.

**N2 — narrative NLP**

| Characteristic | **Comprehend** (sync Detect*) | Claude (NLP inside the extraction call) | Guardrails sensitive-info filter (PII only) |
|---|---|---|---|
| Data integrity | ● fixed types + calibrated scores; deterministic enough to reconcile | ◐ flexible domain entities (VIN, peril), but no calibrated confidence; output varies run to run | n/a (PII only) |
| Privacy | ● `DetectPiiEntities` returns **offsets + types**, so redaction uses typed placeholders *before* persistence | ○ the FM sees the raw PII first — the step we are trying to precede | ◐ masks at the FM boundary (already on in v1); can run standalone via ApplyGuardrail; less offset detail **[re-verify]** |
| Auditability | ● per-entity score and offsets recorded | ◐ prompt/response logged; no per-field score | ◐ intervention record |
| Reliability | ◐ 5 KB sentiment cap forces chunking (P-h); throttling under fan-out | ◐ one more FM call; throttling shared with extraction | ● |
| Testability | ● Stubber per API | ● Stubber | ● |
| Observability | ● per-type counts | ◐ | ◐ |
| Cost | ● per 100-char unit, cheap at narrative sizes **[re-verify]** | ○ tokens × every claim, plus a reasoning tax | ◐ per text unit **[re-verify]** |
| Operational burden | ● serverless | ● | ● |

→ **Comprehend** for NLP signals and PII detection. Claude keeps the
five-field extraction (v1). The Guardrail stays as **defense in depth** at
the FM boundary.
The loser was sunk by **privacy**: NLP inside the FM means the model sees
raw PII before anything can redact it.

**N3 — documents (police report, repair estimate)**

| Characteristic | **Textract AnalyzeDocument QUERIES** (+ images to Claude) | Claude vision only | Bedrock Data Automation (blueprints) | Textract AnalyzeExpense (estimates) |
|---|---|---|---|---|
| Data integrity | ● per-answer **confidence** gates reconciliation (U5); lines give deterministic OCR | ◐ holistic reading; no confidence, so it cannot gate reconciliation | ● blueprint fields + confidence | ● invoice-native TOTAL / line items |
| Privacy | ◐ OCR text persisted → must pass Redact Sensitive Data | ◐ no OCR text persisted, but the image goes to the FM | ◐ | ◐ |
| Auditability | ● answer + confidence + page | ○ "the model said so" | ● | ● |
| Reliability | ◐ sync API; low default TPS in some regions → throttle risk **[re-verify quotas]** | ◐ shares FM throttle | ◐ async jobs | ◐ |
| Testability | ● Stubber | ● | ◐ job shapes | ● |
| Cost | ◐ Queries are priced above plain text detection **[re-verify]** | ● image tokens only (~w×h/750 per image for Claude **[re-verify]**) | ◐ per page/asset **[re-verify]** | ◐ **[re-verify]** |
| Scope fit (C3-a) | ● named service | ● (v1 ADR 0006 path) | ○ **not a named service** (deferred, D-D) | ● named service |

→ **Textract AnalyzeDocument QUERIES for both document types, AND images to
Claude.** They are complementary, not redundant:
- Textract supplies confidence-gated facts for deterministic reconciliation
  (integrity, audit).
- Claude reads the page holistically for extraction.

Knobs:
- *Upgrade:* use **AnalyzeExpense** for repair estimates with line items
  (a second parser; deferred until estimates are real invoices).
- *Cost lever* → now a rule (**M6**): an image goes to the FM only when OCR
  confidence is insufficient **and** no PII was found in that document;
  otherwise the blocking flag `image_withheld:pii`. This narrows "images to
  Claude" above and lowers image-token cost (§8).
- *Alternative:* Converse `document` blocks (PDF ≤ 4.5 MB, ≤ 5 per request —
  P-c) instead of PNG image blocks. Rejected for now because Textract and
  Claude should read the *same* artifact (lineage).

### 4. Other needs — pick and the characteristic that sank each loser

| Need | Pick | Losers → sinking characteristic |
|---|---|---|
| N1 Batch validation | **Glue DQ (DQDL) as the batch gate + Lambda row gate**, one rule catalog (SD-1) | *Lambda-only* → **observability** (no DQ result history, no managed ruleset evaluation, no published DQ metrics). *Great Expectations / PyDeequ* → **testability / R1** (a new pip dependency or Spark ops). *Crawler per batch* → **integrity** (it infers types from dirty data) + ~1–2 min latency. *Glue DQ rule recommendations* → keep as an **optional one-time bootstrap** that profiles the synthetic batch, never on the hot path. |
| N4 Calls | **Transcribe standard batch + ContentRedaction (redacted output only)** | *Call Analytics* → **cost** for the PoC **[re-verify]**; it is the upgrade path (native turn sentiment, issue detection) that would replace Comprehend-on-turns. *Claude* → no audio input on Converse (Nova Sonic is speech-to-speech, not batch transcription) **[re-verify]**. *Whisper on SageMaker* → excluded, C3-a (idle-endpoint trap). |
| N5 Loss runs → text | **Deterministic Lambda template** | *FM summary* → **integrity**: a hallucinated count or amount in an SIU-relevant summary is a defect. Numbers come from code, prose from templates. *SageMaker Processing* → excluded, C3-a (ml.m5.xlarge for kilobytes). |
| N6 Formatting | **Converse** (v1 ADR 0001 / 0011): text sections + image blocks (≤ 20 × ≤ 3.75 MB, user role — P-c); `adjuster_dialog` multi-turn | *Legacy `invoke_model` completions* → correctness (named antipattern). Knob: **Bedrock prompt caching** on the repeated bundle context in multi-turn dialog **[re-verify model support]**. |
| N7 Themes | **Aggregate Comprehend key phrases / entity types** | *Topic modeling* → **cost + feasibility** (async job; a 16-row corpus is far below useful size). *FM clustering* → **auditability** (non-reproducible themes). |
| N8 Proposals | **Bounded proposal set + deterministic replay** (C4-a) | *FM-generated rules / regex* → **auditability + integrity** (unbounded change surface). |

### 5. Approach and model (v2)

- **FM usage stays two-legged** (v1): extraction on a capable model, summary
  on a cheaper one (examples in §4 of the v1 brief; **resolve ids with
  `list_inference_profiles`**, never hard-code them).
- New FM uses:
  - multimodal extraction over the bundle (same extraction model, now with
    image blocks);
  - `adjuster_dialog` (the cheaper model is enough; prompt-caching knob).
- **Deterministic-first:** N1, N5, N7 and N8 use no FM at all. The FM is
  reserved for judgment over conflicting or unstructured evidence.
- **Service API choices** (examples to re-verify; the API surfaces were
  verified in botocore this session — spec P-h, P-i, P-k):
  - Comprehend `DetectPiiEntities`, `DetectEntities`, `DetectKeyPhrases`,
    `BatchDetectSentiment`, `DetectDominantLanguage`;
  - Textract `AnalyzeDocument(FeatureTypes=["QUERIES"])`;
  - Transcribe `StartTranscriptionJob(ContentRedaction=…)`;
  - Glue `StartDataQualityRulesetEvaluationRun` with `pushDownPredicate`.

### 6. Feasibility envelope (PoC; every figure **[re-verify]** at DP-24 before upload — spec AC-Z10)

Per smoke run (≤ 11 processed claims, 3 calls ≤ 60 s, ≤ 8 images, 2 batches):

| Service | Order of magnitude | Driver |
|---|---|---|
| Glue DQ | cents per run | ~2 G.1X workers × a few minutes incl. Spark start-up; per-second billing with a minimum **[re-verify]** |
| Comprehend | ~1 cent per claim | ≈ 5 APIs × tens of 100-char units, 3-unit minimum per request **[re-verify]** |
| Textract Queries | ~1–2 cents per page | 8 pages **[re-verify]** |
| Transcribe | ~2–3 cents per minute | 3 minutes **[re-verify]** |
| Bedrock | ~2–4 cents per claim | 3–6 k input tokens + ~650 tokens per page image, plus the summary **[re-verify]** |
| Lambda / SFN / S3 / EventBridge | fractions of a cent | a few hundred state transitions |
| CloudWatch custom metrics (EMF) | cents for the smoke, **cardinality-driven** | Billed per unique name × dimension set (prorated) **[re-verify]**. The ≤ 2-dimension rule with no `claim_id` (spec AC-Y1) is the cost control. |

**Total ≈ $1–2 per full smoke, including margin.** That is well inside the
$10 budget, and the budget alarm exists. Production $/claim (excluding the FM)
is dominated by Textract pages and Transcribe minutes; including the FM, image
tokens dominate. This is sized once volume is stated (`needs-input`).

Latency: the batch gate adds ~1–3 min (Spark start-up). A claim with a call
takes about its audio duration plus queueing **[re-verify]**; a claim without
one takes seconds. Fine for batch; an interactive FNOL SLO would need
revisiting.

**AI-specific risks handed to arch-risk:**
1. **Throttling under Map fan-out.** Textract's default TPS is the tightest
   quota **[re-verify per region]**. Comprehend is shared across narratives
   and turns.
2. **Detector recall.** PII the detectors miss would be persisted. Keep
   defense in depth (Comprehend + Transcribe redaction + Guardrail).
3. **ASR errors** on accents or noisy calls. That is why the transcript is
   **context, not a reconciliation source** (deliberate).
4. **The FM "resolves" conflicts silently** when the bundle carries
   disagreeing values. Reconciliation flags force review.
5. **Model / id deprecation** — carried over from v1.

### 7. Least-worst picks, per axis (ratified as drafted, R3)

| Axis | Recommendation |
|---|---|
| Capability class | **Managed perception + NLP services + deterministic code**. The FM only for multimodal extraction, summary and dialog. |
| Services | Glue DQ · Comprehend · Textract (QUERIES) · Transcribe (standard + redaction) · Lambda · Bedrock Converse (v1) |
| Approach | Prompt rung (no custom models: no labels); deterministic-first; confidence-gated reconciliation; defense-in-depth PII |
| Cost ceiling | PoC: the existing $10/month budget (v1 + v2). Production: **`needs-input`** |

**ADR candidates (arch-decide)** — now recorded in ADRs 0016–0022, Accepted
2026-09-23:
1. The v2 service set and "deterministic-first, FM-last" principle (the
   service half of ADR 0016).
2. Batch DQ engine: Glue DQ + Lambda row gate + single rule catalog vs
   Lambda-only.
3. Document path: Textract QUERIES **and** images to Claude vs Claude vision
   only vs BDA.
4. PII minimization point: typed redaction before persistence (Comprehend) vs
   the Guardrail at the FM boundary only.
5. Transcription tier: standard + redaction vs Call Analytics.

Advance → **arch-style** (quantum / sync-async), then **arch-decide**.

### 8. Notes on the ratified amendments (2026-09-23)

Folded from `../design/hld-v2-fold-map.md`. No axis in §7 changes.

- **R8c-a (M7): AI-services content opt-out.** Opt out of content use for
  **all** AWS AI services through an AWS Organizations AI-services opt-out
  policy. AWS's supported list includes Comprehend, Textract, Transcribe and
  Glue. **Bedrock is not on it**, because Bedrock does not use content for
  service improvement. Both facts were checked against the AWS Organizations
  docs on 2026-09-23 (ADR 0020) **[re-verify]**. The owner performs the
  opt-out: **owner action pending** until verified with
  `aws organizations describe-effective-policy --policy-type AISERVICES_OPT_OUT_POLICY --target-id <account>`
  (`../build/DEPLOY-LEDGER.md` "Stage A"). Until then: synthetic data only.
- **H-F14-a: images are not guardrail-checked.** Claim-derived text travels in
  Converse `guardContent`; images travel as plain `image` blocks. That loses
  nothing today: the guardrail's prompt-attack filter is TEXT-only and its
  harmful-content filters are off (verified with `get-guardrail`,
  2026-09-23). Integrity against image-borne prompt injection comes from
  **M1** (the pre-routing check against canonical values) + routing on the
  canonical amount + deterministic routing. The Guardrail's "defense in
  depth" (N2; §6 risk 2) therefore covers text, not images. Whether the
  prompt-attack filter supports images at all is **[re-verify]**.
- **M6 lowers image-token cost.** An image reaches the FM only when OCR
  confidence is insufficient and no PII was found in that document (the N3
  cost lever). Image tokens dominate $/claim once the FM is included (§6).
- **M14 adds Amazon SQS** (the trigger dead-letter queue), a new AWS service.
  It adds no AI service, so C3-a stands. Under the approval criteria
  (**R7q-a**, `../adrs/approval-criteria.md`), adding a service is trigger 3,
  so ADR 0016 is on the go-live review list: a named security / privacy
  reviewer signs it off before any real claim data.
