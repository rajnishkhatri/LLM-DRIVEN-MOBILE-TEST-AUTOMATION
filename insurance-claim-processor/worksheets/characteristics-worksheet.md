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
