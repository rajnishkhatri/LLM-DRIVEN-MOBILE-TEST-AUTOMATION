# Eval report — claim document processor (offline)

**Mode:** aws-ai-validate offline harness only. `aws_profile` stays `<none>`.
No `aws s3 mb`, no live `converse`. Real-AWS smoke is a **separate human
gate**.

Build: `../build/`.
Suite: `python3 -m unittest discover -s tests -v` → **17 passed** (2026-09-20).

---

## Sample documents

| Doc | Type | Gold (human) |
|---|---|---|
| `samples/claims/auto-fl-collision.txt` | FL personal auto, collision | Maria Elena Ruiz / POL-FL-AU-88421 / 2026-03-11 / 4820.50 |
| `samples/claims/home-tx-water.txt` | TX homeowners, water | James K. Patel / HO-TX-10993-B / 2026-04-02 / 12500 |
| `samples/claims/incomplete-claim.txt` | Missing amount/date/policy | A. Nguyen / unknowns / windshield chip |

Policy corpus: `auto-florida.md`, `homeowners-texas.md`.

---

## Offline pipeline results (`--fake`)

Fake Converse is deterministic so we can score **retrieval, schema, and
degradation**, not FM quality. Live model comparison is gated.

| Doc | Extraction | Citations | Ungrounded | Validator flags |
|---|---|---|---|---|
| auto-fl-collision | Matches gold; amount 4820.5 | `auto-florida` | no | none |
| home-tx-water | Matches gold; amount 12500.0 | `homeowners-texas` | no | none |
| incomplete-claim | Name + description only | (none) | **yes** | `empty_fields:policy_number,incident_date,claim_amount`, `ungrounded` |

SSN in the auto packet is **not** copied into the fake summary. The
validator still fails a summary that contains `078-05-1120` (`pii_ssn`).

---

## Finding: unfiltered keyword RAG is an integrity defect

First run (no metadata filter) cited **both** `homeowners-texas` and
`auto-florida` on the Texas water claim — a Florida auto clause on a
Texas HO-3 packet. That is the exact miss `aws-ai-design` names
(jurisdiction filter as a correctness lever).

**Fix applied:** fail closed when jurisdiction cannot be inferred;
otherwise filter `jurisdiction` + `line_of_business`. Incomplete
windshield claim is now `ungrounded` rather than randomly grounded.
Production must stamp those tags at **ingest**, not regex the query.

---

## Model comparison (exam Skill 1.1.2 / step 4)

`compare_models` runs the **same** extract prompt through Converse for
each id and records wall time, output length, validator accept/flags, and
token usage.

**Not executed against Bedrock in this run** (offline rule). When you
open the real-AWS gate, pass current inference-profile ids (re-verify;
do not use `anthropic.claude-v2` from the exam snippet):

| Role | Example family | What to score |
|---|---|---|
| Extract | Claude Sonnet-class vs Haiku-class vs Nova | field-match vs gold, especially **amount max error** |
| Summary | Haiku/Nova Lite vs Sonnet | citation faithfulness, length, $/claim |
| Understand | Nova multimodal vs text-only + Textract | only if samples are PDF/image |

Hypothesis (not a measurement): Haiku will win latency/cost on summary;
Sonnet will win extract schema on messy packets. **Confirm on these three
docs before standardizing.** Cascade: cheap extract first, escalate when
validator fails.

Contract already proven: Stubber `converse` uses `messages` +
`inferenceConfig.maxTokens`, not `prompt` / `max_tokens_to_sample` /
`completion`.

---

## Resilience fitness (cards)

| Card | Assertion | Result |
|---|---|---|
| C7 | Bedrock Config connect=10s, read=300s | pass |
| C2 | adaptive, max_attempts=5; no nested app retry | pass (config) |
| C9 | second process of same key overwrites one result | pass |
| C11 | unknown jurisdiction → ungrounded, extraction kept | pass (incomplete claim) |

C1 / C8 / C10 not applied — no live error-rate metric yet.

---

## Recommendations

1. Ratify characteristics top-3 (integrity, privacy, auditability) and
   Bedrock-on-demand Converse before any sandbox spend.
2. Promote policy files to a Knowledge Base **with the same metadata
   filters** the PoC just proved are load-bearing.
3. Put Bedrock Guardrails on Converse I/O (PII ANONYMIZE) so the regex
   validator is a backup, not the control.
4. Do not create `s3://claim-documents-poc-*` until this report's
   real-AWS gate is explicitly approved.
5. Re-verify model ids the day you invoke; record the resolved id on
   every result (auditability).
