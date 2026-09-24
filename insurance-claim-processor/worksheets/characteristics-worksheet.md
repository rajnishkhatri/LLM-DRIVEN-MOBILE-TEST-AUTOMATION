# Architecture characteristics — insurance claim document processor

**Mode:** kata (exam Skill 1.1.1–1.1.3 + eval). Premises come from the brief,
not a live insurer repo.

**Cost of being wrong:** high. A wrong extracted amount, policy number, or
policy-grounded summary can drive an incorrect payout, a privacy incident, or
an unauditable decision. Rigor on correctness, privacy, and auditability
outweighs token-cost optimization.

**GATE: PENDING HUMAN — recommendation below.** Confirm (a) the ≤7 driving
list, (b) the top 3 in any order, (c) demotions. Do not fully rank all seven.

Binding: `.arch/binding.toml` (`[roots] claim-document-processor`). Sibling: `../assess/capability-brief.md`.

---

## Domain ingest

| Field | From the brief |
|---|---|
| Description | Automate processing of insurance claim documents to reduce manual effort and improve consistency |
| Users (stated) | Not named. Implicit: claims operations (adjusters / examiners), plus whoever uploads the packet |
| Requirements | Document storage (S3); a processing workflow; foundation-model integration; response generation; document understanding, information extraction, summary generation; a simple RAG component over policy information |
| Additional | PoC first (upload + Bedrock + RAG + summary), then reusable prompt / invoker / validator components, then eval on 2–3 samples |
| Volume / latency / residency | **`needs-input`** — treat as back-office batch, not a public chat, until stated otherwise |

---

## Candidate extraction

### Explicit

| Candidate | Source language | Translation |
|---|---|---|
| Consistency of extraction / summary | "improve consistency" | **data integrity** of structured fields + repeatable prompts |
| Reduced manual effort | "reduce manual effort" | feasibility / automation; not itself a measurable -ility |
| Document ingest durability | S3 as the landing zone | recoverability of the artifact (implicitly also availability of storage) |
| Policy-grounded answers | "simple RAG component using policy information" | correctness via retrieval, not memorized policy |
| Model swap / comparison | "compare performance of different models" | configurability + testability |
| Reusable prompt / invoke / validate | Skill 1.1.3 | modularity (constituent of agility) |

### Implicit (insurance domain)

| Candidate | Domain fact | Why it is implicit |
|---|---|---|
| Privacy / PII | Claimant name, policy number, incident narrative | Unstated, load-bearing in insurance |
| Auditability / legal | Payouts are regulated decisions | Unstated; "consistency" is the hint |
| Reliability / fault tolerance | A failed invoke must not lose the claim packet | Unstated; S3 as SoR is the hint |
| Security (authz) | Only claims staff should see packets | Unstated |
| Availability | Ops still work if Bedrock throttles | Unstated; batch can queue |

---

## 3-part test

Each candidate must be (a) nondomain, (b) structurally supported, (c) critical.

| Candidate | (a) (b) (c) | Outcome |
|---|---|---|
| Data integrity / extraction correctness | yes / yes — validator, RAG citations, HITL gate, structured output / yes | **Driving** |
| Privacy | yes / yes — KMS, Guardrails PII, least-privilege IAM, PrivateLink later / yes | **Driving** |
| Auditability | yes / yes — prompt+model+chunk ids on every record; immutable S3 / yes | **Driving** |
| Reliability | yes / yes — timeouts, retries, DLQ, idempotent reprocess / yes | **Driving** |
| Configurability (prompts, model ids) | yes / yes — template manager + resolved model ids, not hardcoded / yes for a PoC that must compare models | **Driving** |
| Cost-efficiency | yes / yes — model routing, on-demand vs provisioned / important at scale, not day-1 | **Driving** (keep, but not top-3) |
| Feasibility / time-to-value | composite → **deployability + testability** | Decompose |
| Reduced manual effort | domain goal, not an -ility | Demoted — *handle via design* (automation is the product) |
| Scalability / elasticity | volume **`needs-input`** | Others considered unless volume is bursty |
| Real-time performance | not in the brief | Others considered — batch SLO is enough |
| User satisfaction | composite | Decompose; not driving |

**Demotion (step 3b):** "reduce manual effort" is the business outcome. Structure
serves it by making extraction + summary *checkable*, not by adding a
"productivity component."

---

## Composite decomposition

- **Agility / time-to-market** → deployability (PoC in one region, IaC later) +
  testability (offline Stubber harness + sample-doc eval) + modularity
  (prompt / invoker / validator as separate components).
- **User satisfaction** → correctness + reliability. Do not treat CSAT as a
  characteristic.
- **Consistency** is *not* a synonym of availability. Here it means
  **repeatable, schema-valid extraction** (data integrity), governed by
  templates and a validator.

---

## Driving characteristics (≤7)

| # | Characteristic | Objective definition | Measure (kind) | Caveat |
|---|---|---|---|---|
| 1 | **Data integrity** | Extracted fields (claimant, policy #, incident date, amount, description) match the source document; summaries cite retrieved policy chunks | Extraction field-match rate vs gold + citation coverage (operational) | Averages hide the 1% catastrophic miss (wrong amount) — report **max error on amount** alongside mean |
| 2 | **Privacy** | PII in prompts, logs, and generated text is minimized / redacted; packets stay in-account | Guardrail `GUARDRAIL_INTERVENED` rate on PII + no raw PII in application logs (operational + structural: log-shape test) | Coverage of "we have a guardrail" without assertions is gamed |
| 3 | **Auditability** | Every output can be replayed: model id, prompt template version, retrieved chunk ids, validator result | % of results with complete provenance tuple (operational) | Provenance without retention / access control is theater |
| 4 | **Reliability** | A transient Bedrock/S3 fault does not lose the packet or double-write a decision | Success + DLQ depth + duplicate-write rate under injected retry (operational) | Success % without a timeout bound is a hung-call lie |
| 5 | **Testability** | Pipeline can be proven without a real AWS account | Offline contract tests pass; eval set of ≥3 docs with model-comparison table (process) | 100% tests with no schema assertions is gamed |
| 6 | **Configurability** | Prompt templates and model ids are swapped without rewriting invoke shape | One-line modelId change via Converse; templates keyed by name (structural) | Hard-coded `anthropic.claude-v2` is a scheduled outage |
| 7 | **Cost-efficiency** | Token spend matches task difficulty (extract ≠ summarize ≠ understand) | $/claim + p50/p99 latency by model (operational) | Cheapest model that silently drops fields is not cheaper |

### Proposed top 3 (any order)

1. **Data integrity** — wrong fields are the expensive failure.
2. **Privacy** — insurance packets are PII by construction.
3. **Auditability** — a regulated decision without provenance cannot ship.

**Elimination probe:** cull **cost-efficiency** first. A PoC that is cheap and
wrong teaches the wrong lesson; token routing is a later fitness function.
Do **not** cull privacy or integrity — those are implicit supports of general
success in this domain.

---

## Tension pairs

- **Privacy ↔ auditability:** redacting PII from logs fights the desire to
  replay the exact prompt. Resolve: store encrypted full prompt in the audit
  object; log only template id + hashes in app logs.
- **Data integrity ↔ cost-efficiency:** a frontier model on every page wins
  accuracy and burns tokens. Resolve: route — understand/extract on a capable
  model; summarize on a cheaper one; cascade only when the validator fails.
- **Reliability ↔ cost-efficiency:** retries and a second model on validator
  failure amplify spend. Bound retries (C2) and cascade only on schema miss.
- **Configurability ↔ auditability:** swapping models freely is useless unless
  the *resolved* id is recorded on the result.

---

## Clusters (input to arch-style)

One coherent back-office set: integrity + privacy + audit + reliability.
No public-facing scale cluster is in the brief. **One quantum** unless a
claimant portal or a separate policy-admin system appears.

A later HITL review UI would be a second *actor class*, not automatically a
second quantum — keep it in the same processing quantum until review SLO and
ingest SLO diverge.

---

## Others considered

Scalability, elasticity, real-time performance, multilingual, accessibility,
learnability. Pull in **scalability** if claim volume or catastrophe-burst
(`needs-input`) is confirmed.

---

## Fitness-function seeds (for arch-validate)

- Schema-valid JSON on 100% of happy-path sample docs.
- Amount field numeric; max relative error vs gold = 0 on the eval set.
- Every summary has ≥1 policy citation **or** is explicitly flagged `ungrounded`.
- No `invoke_model` text-completions path (`max_tokens_to_sample` /
  `completion`) in the build.
- Bedrock client has connect + read timeouts set (C7).

---

## v2 addendum — data-preparation plane (2026-09-23)

**GATE: RATIFIED 2026-09-23 ("ratify as recommended" — design/hld-v2-data-prep.md §6; was PENDING HUMAN) — recommendation below** (provisional-gate batch run,
A2-a; ratify via the checklist in `../design/hld-v2-data-prep.md`).
**Mode:** review — v1 is live (`../build/DEPLOY-LEDGER.md` Stage 9). The
v2 domain input is the course assignment (validation · multimodal ·
FM formatting · quality enhancement) mapped to claims per C1-a
(`../specs/claim-processor-data-prep.spec.md` §1.3, **DRAFT — on hold per
A5-a**; its premise audit §1.1 is reused here as evidence).

**Cost of being wrong: higher than v1.**
- v2 pushes far more PII into the pipeline: call recordings with spoken
  SSNs and cards, police reports, free narratives.
- It adds **silent-corruption paths upstream of the approval gate**. Example:
  a partner date `11/03/2026` misparsed as 3 Nov instead of 11 Mar looks
  valid, so a naive design would auto-approve on a corrupted fact.
- A bad upstream export could flood human review with hundreds of claims.

### Domain ingest (v2)

| Field | v2 |
|---|---|
| Description | Validate, enrich, and format multimodal claim data before the v1 decision workflow; improve data quality over time from model responses |
| Users / actors | Intake ops (own quarantine) · adjusters (read bundle context) · data-quality owner (approves proposals) · SIU (special investigations; history flags) · auditors (lineage) · upstream systems (claims-admin / FNOL exports, partner TPAs — third-party administrators, call-recording store) |
| Requirements (explicit) | Glue DQ on structured data; Lambda checks on unstructured text; CloudWatch DQ metrics over time; Comprehend entities + sentiment; Textract on images; Transcribe on calls; tabular → natural-language summary; Claude-formatted, dialog, and multimodal requests; entity/theme extraction; text normalization; feedback loop |
| Additional | Synthetic data; reuse the live pipeline (no rebuild); "faster turnaround without compromising real-world depth" |
| Volume / latency | **`needs-input`** — batch intake assumed (minutes OK); catastrophe (CAT) surge volume unknown |

### Candidate extraction (v2 delta)

| Candidate | Source | Explicit / implicit | Translation |
|---|---|---|---|
| Input data quality | "data validation", "data quality enhancement" | explicit | **data integrity** extended upstream: completeness, validity, uniqueness, consistency, timeliness of *inputs* |
| DQ monitored over time | "CloudWatch metrics to monitor data quality over time" | explicit | **observability** of data quality (trend + attribution) |
| Multimodal ingest | text / image / audio / table | explicit | interoperability with source formats + extensibility per modality |
| Improves from model responses | "feedback loop" | explicit | configurability *governed by* auditability (a rule change is a controlled change) |
| Faster turnaround | user | explicit | testability + deployability (time to market decomposed) |
| Voice / documents are PII-dense | insurance + call-center fact | implicit | **privacy** (data minimization before the FM) |
| Which source said what | a disputed claim or regulator inquiry | implicit | **auditability → data lineage** |
| Partial multi-service failure | 4 services + 2 async jobs per claim; at-least-once events | implicit | **reliability** (no lost or duplicated claim) |
| Per-claim multi-service spend | Textract Queries, Transcribe minutes, Glue DPUs, image tokens | implicit | cost-efficiency |
| Sentiment on claimant language | Comprehend sentiment (assignment) | implicit | **fairness guard** — dialect bias must not reach decisions |
| CAT surge | insurance domain | implicit | scalability / elasticity — `needs-input` |

### 3-part test (v2)

| Candidate | (a) nondomain / (b) structural / (c) critical | Outcome |
|---|---|---|
| Data integrity (inputs + cross-source) | yes / yes — batch gate + row gate + reconciliation + quarantine zone / yes | **Driving** |
| Privacy | yes / yes — redaction *before* persistence and FM, separate raw vs processed zones, redaction at the source service / yes | **Driving** |
| Auditability (lineage + change governance) | yes / yes — lineage block per value, versioned S3, proposal→approval→config-version chain / yes | **Driving** |
| Reliability (partial failure) | yes / yes — per-branch failure isolation, idempotency keys, conservation accounting / yes | **Driving** |
| Testability | yes / yes — fakes + seeded corpus; injectable clients / yes (turnaround) | **Driving** |
| Observability of DQ | yes / yes — every stage emits bounded-dimension metrics into a shared plane / yes (explicit) | **Driving** |
| Cost-efficiency | yes / yes — which features run per claim (Queries, images to FM, Glue workers) / important, not day-1 | **Driving** (cull first) |
| Configurability | yes / *already structural in v1* (ADR 0010 config plane; `config_provider.py:58`) / yes | **Handle via design** — second AppConfig profile, no new structure |
| Interoperability (source formats) | yes / partly — a normalizer component + schema contracts, not an architecture-wide shape / yes | **Handle via design** |
| Fairness (sentiment) | borderline domain / yes — a **data-flow boundary** (sentiment never reaches routing or reconciliation) / yes | **Handle via design + structural fitness function** (static import/AST rule) |
| Extensibility (future modalities) | yes / yes — branch-per-modality / speculative today | **Others considered** |
| Scalability / elasticity (CAT surge) | yes / yes / `needs-input` | **Others considered** — pull in when volume is stated |
| Timeliness (acknowledgement latency) | yes / yes / `needs-input` (no SLO given) | **Others considered** |

### Composite decomposition (v2)

- **"Data quality"** is a composite. Decompose it into the classic dimensions
  (completeness, validity, uniqueness, consistency, timeliness, accuracy).
  Each maps to a rule family: DQDL `IsComplete`, `ColumnValues matches|in`,
  `IsUnique`, reconciliation, report-lag, and the FM-vs-source disagreement
  rate. Don't report one "quality score" as if it measured all six.
- **"Faster turnaround"** = testability (offline fakes + seeded corpus) +
  deployability (one extra package handler, runbook stages) + modularity
  (a bounded `dataprep` subpackage).
- **"Consistency"** here means *cross-source agreement* (reconciliation), not
  CAP consistency and not v1's "repeatable extraction".

### Driving characteristics (≤7) — v2 plane

| # | Characteristic | Objective definition | Measure (kind) | Caveat |
|---|---|---|---|---|
| 1 | **Data integrity (inputs)** | Every claim reaching v1 has (i) passed the blocking rules, (ii) canonical fields, and (iii) every cross-source disagreement surfaced as a flag. No known-defective record auto-approves. | Seeded-defect recall = 100 % (blocking → quarantined; warn/recon → flagged) and blocking flags on seeded-clean = 0 (process, offline corpus). DQ score per batch; FM-vs-source disagreement rate per field (operational). | Seeded defects test only the defect classes we *imagined*. The disagreement rate is the probe for unknown classes. Pair batch averages with a **zero-tolerance max**: silent misparse reaching `auto_approve` = 0. |
| 2 | **Privacy** | High-risk PII types (SSN, card, bank, PIN) never appear in processed artifacts, bundles, FM requests, logs or metrics. Transcripts are redacted by the source service. Names and dates are kept only because extraction needs them. | PII scan over every persisted synthetic output = 0 hits (structural); log-shape test (reuses `logging_safe.py:13`); redaction settings on 100 % of Transcribe jobs (config assertion). | No detector has 100 % recall: keep defense in depth (Comprehend + Transcribe redaction + the v1 Guardrail on FM input). Raw audio *is* PII, so control access to the `raw/` zone. |
| 3 | **Auditability (lineage)** | For any bundle value you can name its source object (key + S3 version), extractor (service, confidence) and config version. For any DQ config change you can name the evidence and the approver. | % of bundles with a complete lineage block = 100 % (structural test); % of proposals with evidence and approver = 100 %; S3 versioning ON (`DEPLOY-LEDGER.md:27`). | Lineage that points at a mutable object is theater, so record version ids, not just keys. |
| 4 | **Reliability (partial failure)** | Every intake row is accounted for exactly once (processed / quarantined / `claim_failed`), despite at-least-once events, async-job failures or a dead source. A failed source degrades the claim to review; it never fails the batch. | **Conservation**: rows_in = processed + quarantined + claim_failed, per batch (operational + test). Duplicate v1 executions per revision = 0 under replayed events (test). | "Execution succeeded" hides silent drops. Measure conservation, not success %. |
| 5 | **Testability** | The whole intake flow runs offline with no credentials, with deterministic fakes and a seeded corpus. Every AWS call site has a Stubber contract test. | Offline e2e green; % of new call sites under Stubber = 100 %; generator determinism (same seed → same bytes). | Fakes encode our assumptions about service output shapes. Only the `[gate]` smoke proves them (Transcribe output shape, Glue metrics). |
| 6 | **Observability (DQ over time)** | Each stage emits its quality outcome with bounded dimensions; the trend and its attribution (stage / source / channel) are visible without reading logs. | Metric-coverage test (each stage emits ≥ 1 vocabulary metric); `claim_id` is never a dimension (cardinality test); an alarm on the batch DQ score. | A dashboard with no alarm and no owner is wallpaper. Metrics improve nothing without the feedback loop. |
| 7 | **Cost-efficiency** | Data-prep spend per claim scales with the sources present; no always-on compute; costly features only where they buy integrity. | Estimated $/claim per service (usage units) and $/batch for Glue DQ; smoke ≤ the $10 budget (`DEPLOY-LEDGER.md:17`). | The cheapest path (skipping reconciliation, or using OCR without Queries) is not cheaper once one misparse pays out. |

### Proposed top 3 (any order)

1. **Data integrity (inputs)** — the reason the plane exists. A silent
   misparse upstream of the approval gate is the most expensive v2 failure.
2. **Privacy** — v2 multiplies the PII surface (voice, police reports).
3. **Auditability (lineage)** — a claim decision built from five sources is
   indefensible if you cannot say which source supplied each fact.

This is the **same top 3 as v1**, now applied upstream.

**Elimination probe:** cull **cost-efficiency** first (the PoC spend is cents;
see the tension pair below), then observability (its structure already exists
through ADR 0015). Never cull integrity or privacy.

### Tension pairs (v2)

- **Privacy ↔ data integrity:** redacting before the FM can remove facts the
  extraction needs. Resolve: redact only high-risk types; keep names and
  dates; reconcile against structured intake fields, which are not redacted.
- **Privacy ↔ auditability:** disputes need the raw audio and narrative, which
  are PII-dense. Resolve: a restricted, versioned `raw/` zone; `processed/`
  and bundles carry redacted text; lineage points at raw keys and versions,
  never copies content.
- **Data integrity ↔ cost:** Textract Queries cost more than plain text
  detection (DetectDocumentText), and sending images to Claude as well as OCR
  text costs more again. Resolve: Queries only on document types whose fields
  feed reconciliation; track $/claim; revisit at volume.
- **Reliability ↔ timeliness:** fail-closed batch quarantine also blocks the
  good rows in a bad batch. Resolve: a tunable threshold plus a resubmission
  path. The SLO is `needs-input`.
- **Configurability ↔ integrity / auditability:** a loop that retunes rules
  itself could silently widen acceptance. Resolve with C4-a: proposals only,
  replay evidence, human approval, and bake + rollback through AppConfig.
- **Data integrity ↔ fairness:** "more signals" (sentiment, language) looks
  like better data but imports bias. Resolve: sentiment is context only,
  enforced as a structural rule.

### Clusters (input to arch-style)

- **Shared governance cluster (v1 + v2):** integrity, privacy, auditability.
  **No counteracting clusters** (nothing public-facing, no scale cluster).
- **Operational-profile divergence** — not the Ch-7 "fatal flaw", but real:

  | Aspect | v2 intake | v1 decision |
  |---|---|---|
  | Unit of work | a batch (minutes; Glue DQ start-up ~1–2 min) | a claim (seconds to a 7-day HITL wait) |
  | Change cadence | DQ rules change often (feedback loop) | decision logic is stable and ADR-governed |
  | Main operational concern | cost and throughput | reliability of the decision |

  **arch-style must decide** whether this divergence alone justifies a second
  quantum. It is not assumed here, even though C2-a presupposed a separate
  state machine.

### Handle via design / Others considered (v2)

- **Handle via design:**
  - configurability — second AppConfig profile on the v1 plane (`config_provider.py:58`);
  - interoperability — normalizer + CSV / bundle contracts;
  - fairness — the sentiment-isolation rule plus a static fitness function;
  - "reduced manual effort" — the domain goal, carried over from v1.
- **Others considered:**
  - scalability / elasticity (CAT surge) and timeliness — `needs-input`;
  - extensibility to new modalities — speculative, but the branch-per-modality
    shape keeps it cheap;
  - multilingual — out: non-English → `language_unsupported` → review;
  - accessibility and learnability — no UI in scope.

### Fitness-function seeds (v2, for arch-validate)

- Seeded-defect recall = 100 %; blocking flags on seeded-clean claims = 0.
- Conservation per batch: rows_in = processed + quarantined + claim_failed.
- No high-risk PII in any persisted processed/bundle output (a scanner over
  the corpus run).
- Lineage completeness = 100 % of bundle fields.
- Sentiment never imported or read by routing or reconciliation (AST rule).
- No `time.sleep` in `dataprep/`; every async poll loop in the ASL has a
  budget.
- Payload ≤ 32 KB per intake step (claim-check).
- Metric vocabulary coverage, and no `claim_id` dimension.
- DQDL ↔ row-twin parity.

### Ubiquitous language (v2)

- **Validation** = rules at ingest (batch gate, row gate).
- **Reconciliation** = agreement across sources.
- **Feedback** = FM-vs-source disagreement plus reviewer corrections.
- **Quarantine** = held for intake ops, never deleted.
- **Bundle** = the per-claim, per-revision FM-ready package plus lineage.
- **Proposal** = a bounded config change with replay evidence, never
  self-applied.
