# ADR 0021. Format model input as tagged, lineage-attributed context owned by intake; keep task prompts in v1

## Status
Accepted — 2026-09-23 (ratified as recommended; amendments below). Formerly: Proposed. Extends ADR 0001 (Converse) and ADR 0011 (adapter content blocks).
Related: 0017, 0018, 0020.

## Context
Part 3 of the assignment asks for three things: format processed data for
Claude, add conversation templates for dialog-based analysis, and format
multimodal requests. v1 builds ONE content block (text *or* one image,
`../build/claim_processor/understand.py:38`). Its only image sample is a 1×1
placeholder (spec P-b).

Converse limits (botocore `Message.content`): ≤ 20 images, each ≤ 3.75 MB /
8000 px; ≤ 5 documents of ≤ 4.5 MB; images and documents only in the `user`
role. v1's ingest cap is 5 MiB (P-c, hygiene H1).

Forces:
- **Integrity:** the model must know which source said what.
- **Privacy:** only redacted text, per ADR 0020.
- **Auditability:** the exact request must be replayable.
- **Cost:** multi-turn dialog resends the whole context.
- **Security:** narratives, OCR text and transcripts are claimant-controlled
  text, so prompt injection is a realistic attack.

Alternatives:
- **Ownership:** (a) intake renders the whole prompt, task included; (b)
  **intake owns the data blocks, v1 owns the task prompt**; (c) v1 reads
  per-source records and formats them itself.
- **Structure:** a plain concatenation vs **tag-delimited sections with
  source attributes**.
- **Documents:** PNG image blocks vs Converse `document` (PDF) blocks.
- **Dialog state:** server-side memory (AgentCore Memory) vs **a stateless
  client resend** with a prompt-cache point.

## Decision
We will split ownership at the data/task line:
- **Intake owns the data.** Assemble / Format Model Context writes
  `fm_request.context_blocks` into the bundle.
- **v1 owns the task.** Templates live in `PromptTemplateManager`; they are
  versioned, and the versions are recorded on the result.

The request order is **data → images → instruction**.

Context rules:
- Sections are wrapped in source-attributed tags: `<intake_record>`,
  `<claimant_narrative source=… version=…>`,
  `<document_text source=… confidence_min=…>`, `<call_transcript redacted="true">`,
  `<loss_history>`, `<reconciliation_notes>`.
- Images follow as `user`-role blocks, referenced by bundle key and resolved to
  bytes at invoke time. There are at most 20, each ≤ 3.75 MB; an over-limit
  image becomes `image_skipped` (blocking).
- The task prompt and frozen five-field schema come last.
- Sentiment is never rendered into these prompts (ADR 0018).

**Conversation templates:**
- *Transcript dialog:* turn-ordered `Agent:` / `Caller:` lines inside
  `<call_transcript>`, bounded by `format.max_transcript_chars` (first and
  last turns kept, with an elision marker).
- *`adjuster_dialog`:* a stateless multi-turn Converse call.
  - System: answer only from the bundle, name the tag used, say "not in the
    claim file", never reconstruct a redacted value.
  - Turn 1: context + images + the question, then a `cachePoint`
    **[re-verify model support]**.
  - Then alternating turns, with the Guardrail on every call.
  - No server-side memory.

This ADR also records **hygiene H1**: `MAX_IMAGE_BYTES` = 3,750,000 (the
Converse limit), shared by the v1 ingest cap and the formatter.

Justification:
- **Technical:**
  - The data/task split lets intake evolve formatting without touching v1's
    versioned prompts, and lets v1 change task wording without re-running
    intake.
  - Source-attributed tags give the model and the auditor the same
    provenance.
  - "Data first, instruction last" and "images before the text that
    references them" follow current long-context and vision prompting
    guidance **[re-verify]**.
  - Tag delimiting plus the Guardrail prompt-attack filter plus
    **deterministic routing** means an injected instruction cannot *directly*
    approve a claim.
    **Corrected by the risk storm (C-1):** a corrupted *extracted* field is
    **not** caught by reconciliation, which runs before the model call. The
    claim holds only with **M1**, a pre-routing check of FM output against
    `intake.normalized` plus routing on the canonical amount. It also needs
    **M10**: escape `<` and `>` in claimant text inside tags. Both were
    accepted at ratification (`../risk/risk-storm-v2-data-prep.md` §5).
- **Business:**
  - Adjusters get a Q&A surface over one claim file without a new service.
  - Prompt caching keeps multi-turn cost near single-turn cost for the large,
    stable context **[re-verify]**.

## Consequences
**Good:**
- A replayable request per bundle revision.
- Multimodal extraction finally exercised with real images.
- Injection cannot reach the approval decision.
- The dialog has no server state to leak across claimants.

**Bad / accepted:**
- Two owners must agree on the tag vocabulary. It is part of the bundle
  contract (`format_version`).
- Image tokens raise per-claim FM cost (the knob is in ADR 0020).
- Prompt-cache support varies by model **[re-verify]**.
- A stateless dialog resends history each turn (bounded by the transcript cap
  and the cache).

**Losers:**
- (a) Intake renders the whole prompt: v1's prompt versions become
  meaningless; two teams edit one prompt.
- (c) v1 formats: v1 becomes coupled to every source record and loses the
  claim-check simplicity.
- Plain concatenation: provenance is invisible to the model; injection is
  easier.
- PDF document blocks: Textract and Claude would read *different* artifacts
  (lineage). Kept as an alternative.
- AgentCore Memory: cross-claimant blur risk, and no need yet.

## Compliance
Offline fitness:
- **Formatter unit tests:** fixed section order and tag names; images ≤ 20 and
  ≤ 3.75 MB, `user` role only; no sentiment keys in rendered text; redaction
  placeholders preserved; transcript cap honored.
- **v1:** a bundle key yields `[context blocks + resolved images + task]` in
  that order, and the five-field schema is unchanged (AC-B3).
- **`adjuster_dialog`:** renders alternating roles, a `cachePoint` after the
  context, and `guardrailConfig` present.
- **H1:** a 3.8 MB image fails at ingest.

`[gate]`: the smoke's extraction over a bundle with real images returns
schema-valid JSON.

## Amendments ratified 2026-09-23 (risk storm, `../risk/risk-storm-v2-data-prep.md` §5)
- **M1** pre-routing FM-vs-canonical check (`claim_amount` with tolerance, `incident_date`, `policy_number`) → blocking `bundle:fm_source_mismatch:<field>`; threshold routed on the canonical amount.
- **M10** escape `<`/`>` in claimant-derived text inside context tags (+ formatter test).
- **M15** bundle RAG scope = canonical intake jurisdiction / line of business.
- **M16** bundle rule-based degrade floor = canonical intake fields (deterministic; still review).
- **H-F14-a** (owner, 2026-09-23; raised by live-v1 finding F14): **input tagging**.
  - Every context section containing claim-derived values travels inside Converse
    `guardContent`: intake record values, narrative, OCR text, transcript, loss
    history, reconciliation notes.
  - Instructions, the output schema and policy excerpts are plain `text`.
  - Without tagging, the guardrail checks the whole turn and its prompt-attack
    filter blocks our own instructions. v1 hit exactly this.
  - **Images are plain `image` blocks and are not guardrail-checked.** That loses
    nothing today: this guardrail's prompt-attack filter is TEXT-only and its
    harmful-content filters are off (verified with `get-guardrail`, 2026-09-23).
  - Integrity against image-borne injection rests on **M1** + routing on the
    canonical amount.
  - M10 escaping applies inside the guarded text. Contextual grounding stays
    inert (F5).
  - Fitness: with a guardrail configured, a claim-derived sentinel never appears
    in a plain `text` block.
  - Revisit if image filters are enabled; image support in the prompt-attack
    filter is **[re-verify]**.

Detailed EARS criteria land in the spec revision (R10).

## Amendment 2026-09-23 — extraction sees evidence only; the decision uses the canonical intake values (LLD Q1-a)
Found at the LLD (Wave A): M5 says the measuring prompt hides the intake
record, but design §9.4.1 put `<intake_record>` in the extraction request.
With the record in view, the FM can copy the intake values. M1 and the
feedback loop would then compare intake with intake and never see a real
disagreement.

We now split what the FM sees by purpose (bundle `fm_request.views`,
`../design/lld-v2-data-prep.md` §2.7):
- **Extraction sees evidence only:** the narrative, the OCR text and the
  transcript. No section in the extraction view shows a canonical intake
  value, so it excludes `intake_record`, `reconciliation_notes` and
  `loss_history` (which names the policy number) (LLD BUN-05). The summary
  and dialog views are unchanged.
- **For a bundle key, the decision uses the canonical intake values of the
  three M1 fields:** `policy_number`, `incident_date` (= canonical
  `loss_date`) and `claim_amount` (LLD V1-20, V1-21):
  - FM value present and different → blocking
    `bundle:fm_source_mismatch:<field>` (M1, unchanged). The FM's date must be
    ISO `YYYY-MM-DD`; any other form counts as different.
  - One M1 field absent → recorded in `bundle.fm_absent[]`; it does not block
    on its own.
  - Two or three absent → blocking `bundle:fm_evidence_missing`, so an
    injected "return nulls" cannot silence M1.
  - `claimant_name` and `incident_description` stay FM fields: empty →
    `empty_fields:` → review, as today.
  - `extracted_info` keeps the FM output verbatim. The canonical values live
    only in `bundle.canonical`.
- v1 (non-bundle) keys are unchanged.

**Routing diff** (bundle keys only):

| | Before (design §9.4.1 + M1) | After (Q1-a) |
|---|---|---|
| What the FM sees when extracting | intake record + evidence + reconciliation notes | evidence only; `loss_history` hidden too |
| Fields decided from intake | none (M1 moved only the threshold) | policy number, date, amount |
| FM leaves one M1 field empty | review (`empty_fields`) | recorded in `bundle.fm_absent[]`; does not block |
| FM leaves two or three empty | review | review (`bundle:fm_evidence_missing`) |
| FM value differs | review (M1) | review (M1); a non-ISO date counts as different |
| FM output in the record | kept | kept verbatim; canonical values only in `bundle.canonical` |

- *Why this over the alternatives:* keeping the intake record in extraction
  (the HLD drawing) leaves M1 and the feedback loop blind to copying. Hiding
  the record but keeping all five fields FM-decided sends every claim whose
  evidence never restates its policy number to review.
- *Trade-off accepted (widens auto-approve):* a bundle claim whose evidence
  does not restate one of the three M1 fields can still auto-approve, on the
  validated canonical value. That value has already passed the row gate's
  blocking rules, and every value the FM does return is still checked by M1.
- *Risk (LLD Appendix A.5):* an amount that legitimately differs from the
  evidence by more than the M1 tolerance (a deductible, a partial claim) goes
  to review.
- *PII (criterion 2):* narrows only. The intake record, which holds the
  claimant name, is no longer sent to the FM for extraction.

Approval criteria: flagged (5).
Approved by / date: Rajnish Khatri / 2026-09-23 ("Q1-a approved"; the
tightened diff above: "Q1 tightened ok")

## Notes
Author: arch-decide (v2 HLD, provisional batch A2-a)
Approved by / date: Rajnish Khatri / 2026-09-23 ("ratify as recommended")
Superseded date:
Last modified: 2026-09-23 / Q1-a amendment (LLD)
