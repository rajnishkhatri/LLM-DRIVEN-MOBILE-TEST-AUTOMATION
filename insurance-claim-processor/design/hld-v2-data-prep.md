# High-level design — claim processor v2: data-preparation plane

**Read this first.** It summarizes the v2 HLD pass (2026-09-23): the arch-*,
aws-ai-* and sdp-* skills, run as a **provisional batch** (decision A2-a).
It was **ratified as recommended** the same day. **Status: FINAL
(2026-09-23)** after the consistency pass (§5). The LLD starts from here:
[`lld-v2-handover.md`](lld-v2-handover.md).

Decisions in force: C1-a…C7-a (v2 framing) and A1-a…A5-a (this pass).
**Stage order (owner, 2026-09-23):**
1. finalize this HLD;
2. **LLD**;
3. spec (the implementation plan);
4. build;
5. **manual** deploy, run by the owner step by step as in v1.

The draft spec `../specs/claim-processor-data-prep.spec.md` stays **on hold**
until the LLD is done.

## 1. The design in one paragraph

A second **Step Functions Standard workflow**, `claim-processor-intake`, runs
**inside the existing quantum**: the same package, bucket and AppConfig app,
with the seam pre-cut. It fires once per intake batch.

1. It admits the batch exactly once (S3 conditional-put lock, with a
   controlled takeover of a failed holder, M13). It pins the batch's DQ config
   and fails closed on fallback (M17).
2. It gates quality at **batch grain** (Glue Data Quality) and at **row grain**
   (Lambda), both driven by **one rule catalog**.
3. Per claim, in parallel, it reads four sources:
   - the narrative (quality checks + typed PII redaction + Comprehend);
   - the police report / estimate (Textract QUERIES);
   - the FNOL call (Transcribe, redacted at source);
   - the loss runs (a deterministic summary).

   Up to 50 claims run in an inline Map. 51–200 run as a Distributed Map, one
   child execution per claim. Larger batches are quarantined (M14, ADR 0019).
4. It reconciles facts across sources, formats **tagged,
   lineage-attributed Converse context**, and writes a **self-contained,
   revision-scoped bundle** (M12).
   - Only claim-derived text is guardrail-checked input (H-F14-a).
   - Images go only when OCR is insufficient and no PII was found (M6).
5. It starts the **v1 decision workflow** asynchronously, once per claim
   revision, passing the bundle key + S3 VersionId (M12). v1 changes only where
   it reads bundles:
   - an FM-vs-canonical check before routing, with the threshold on the
     canonical amount (M1);
   - fail-closed flags (M18);
   - canonical RAG scope and degrade floor (M15, M16).

A watchdog turns any failed intake execution into a `batch_failed` summary and
metric (M14).

v1's decision records flow back through EventBridge into a **feedback loop**.
It only *proposes* bounded, replay-proven configuration changes; a human
deploys them through AppConfig.

**Principle: deterministic-first, FM-last.** Managed services read, code checks
the facts, and the model judges only what is left. It never decides approval.

## 2. Diagrams (D2, linted — all PASS)

| View | File | What it answers |
|---|---|---|
| Context | [`../validate/diagrams-v2/01-context.view.md`](../validate/diagrams-v2/01-context.view.md) | Who uses the system; which AWS AI services it depends on |
| Container | [`../validate/diagrams-v2/02-container.view.md`](../validate/diagrams-v2/02-container.view.md) | Two workflows, one quantum; the async hand-off (edge 14) and the feedback events (edge 19) |
| Component (intake) | [`../validate/diagrams-v2/03-component-intake.view.md`](../validate/diagrams-v2/03-component-intake.view.md) | The 18 intake components and the per-claim data flow |

The diagram IRs encode C3-a as lint rules: `SageMaker`, `Rekognition` and
`DynamoDB` fail the build if they ever appear.

## 3. Stage artifacts (each a dated v2 section in the v1 living document)

| # | Stage (skill) | Artifact | Headline |
|---|---|---|---|
| 1 | Characteristics (arch-characteristics) | [`../worksheets/characteristics-worksheet.md`](../worksheets/characteristics-worksheet.md) § v2 | Top 3 = **data integrity (inputs), privacy, auditability (lineage)** — same as v1, now upstream. 7 driving characteristics; cost culled first. |
| 2 | Components (arch-components) | [`../components/logical-components.md`](../components/logical-components.md) § v2 | 20 components. Characteristic splits CS-1…CS-5. **SD-1:** one Intake Rule Catalog renders the DQDL (removes the drift class). **v1 drift found:** 9 intended vs 25 actual components. |
| 3 | Service choice (aws-ai-assess) | [`../assess/capability-brief.md`](../assess/capability-brief.md) § v2 | Comprehend (not FM-NLP) for privacy; Textract QUERIES **and** images to Claude; Transcribe standard + redaction; deterministic loss-run summary; smoke ≈ $1–2 **[re-verify]** |
| 4 | Style / quanta (arch-style) | [`../worksheets/style-decision.md`](../worksheets/style-decision.md) § v2 | **One quantum, two workflows**, pre-cut seam + split triggers. **Orchestrated pipeline** (beats choreography and Glue ETL). Async hand-off (avoids HITL-latency entanglement). **SD-4:** v1 reads only the curated bundle zone. |
| 5 | Solution design (aws-ai-design) | [`solution-design.md`](solution-design.md) §9 | Not an agent; formatting contract (data → images → instruction, XML-style tags); 4-layer PII; IAM separation of duties (**qualified** by the risk storm) |
| 6 | Resilience clinic (sdp-resilience) | [`../risk/resilience-clinic.md`](../risk/resilience-clinic.md) § v2 | C7 + C2 (one layer, owned by SFN, full jitter) + C9 (lock with takeover) + C11 (soft sources, fail-closed batch gate) + C8 + C10 at admission; C1 not applied. **v1 finding:** retry amplification 5 × 5. Reserved sdp categories named. |
| 7 | Decisions (arch-decide) | [`../adrs/index.md`](../adrs/index.md) | **0016 revised** + **0017–0022**, all Accepted 2026-09-23 (LLD amendments: 0019, 0021, 0022; 0020 Proposed). Every hand-off item Written / Merged / Deferred ([`../adrs/log.md`](../adrs/log.md)). |
| 8 | Risk storm (arch-risk) | [`../risk/risk-storm-v2-data-prep.md`](../risk/risk-storm-v2-data-prep.md) | **5 blind lenses.** Found **2 LIVE v1 defects (D0, blocking)**. Integrity is HIGH in **every** context (row sum 30); privacy row sum 21. Convergent finds C-1…C-8, of which C-1 (routing trusts the FM's amount) came from 4 of 5 lenses. Mitigations D0 + M1–M18 priced (v2 must-have ≈ 5.5 d). |
| 9 | Validation (arch-validate) | [`../validate/architecture-validation.md`](../validate/architecture-validation.md) § v2 | Nine-intersection verdicts (engineering practices and systems integration partially misaligned; infrastructure and enterprise unknown); governance G1–G49 (G39–G49 added by the LLD); checklists; open items by owner |

## 4. What the risk storm changed

**BLOCKING (D0): two defects in the LIVE v1 system, verified against the repo:**
- **D0-a:** none of the 6 `Catch` blocks in `../build/sfn/asl.json` sets
  `ResultPath`, so on a catch the claim data is replaced by the error object.
  The throttle-degrade path (AC-P1), the policy-lookup / RAG fallback (C11 /
  AC-G2) and the 7-day review expiry (AC-E4) therefore fail on real AWS. They
  fail safe (no wrong approval), but the claims end undecided.
- **D0-b:** the summary Converse call sends no `guardrailConfig`
  (`../build/claim_processor/pipeline.py:423-428`), against v1 AC-A5.
- Fix both first: about half a day plus one interactive redeploy. v2 would
  send *more* claims down these paths.

**False claims, corrected in place:**
- **C-1:** "reconciliation catches a manipulated field" (ADR 0021,
  design §9.4.1). It is monitoring, not a gate, until **M1**, a pre-routing
  check of FM output against the canonical values.
- **C-3:** "raw PII reaching Bedrock is an IAM impossibility" (ADR 0020). It is
  false for images, and holds only by convention for text, until **M6**.
- **Clinic knob error:** reserved concurrency 10 < 16 concurrent invocations,
  now corrected to 20 (C-7).

**Structural changes** (accepted at R8b; drawn in the v2 diagrams since the consistency pass):
- **M12:** revision-scoped keys plus S3 VersionId hand-off (C-4).
- **M14:** inline-Map cap 50 rows, with Distributed Map (a Standard child per
  claim) above that, plus an execution-failure watchdog (C-7).
- **M17:** pin the DQ config per batch; fail closed on fallback (C-8).

The spec (on hold) also contradicts SD-4 (AC-W7). It is fixed at the A5-a
revision.

## 5. Status — FINAL (2026-09-23)

- **Ratified as recommended** (R1–R9). ADRs 0016–0022 are **Accepted**, with
  the risk-storm amendments recorded per ADR.
- **Owner decisions:**
  - **R7q-a:** approval criteria, recorded in `../adrs/approval-criteria.md`.
  - **R8c-a:** opt out of all AI services. The owner performs it
    (`../build/DEPLOY-LEDGER.md` "Stage A"); synthetic data only until verified.
  - **H-F14-a:** input tagging in the v2 formatting contract (ADR 0021).
  - **D-a:** keep the live v1 state.
- **R0 / D0 closed.** D0-a is fixed and TestState-proven. D0-b is fixed, and
  the F14 it exposed is fixed with input tagging (ADR 0008 amendment, v1
  AC-A5a). Smoke #3 auto-approved on real AWS, and an injected claim is still
  blocked. The agent deployed these via the CLI. From now on **every deploy is
  manual and owner-run**.
- **Consistency pass done.** It folded M1–M10 and M12–M18, H-F14-a and R8c-a
  into every HLD artifact. The worklist is
  [`hld-v2-fold-map.md`](hld-v2-fold-map.md).
  - Diagrams were re-rendered and re-linted: 3/3 PASS.
  - The components were re-checked: no new components; the M14 watchdog is a
    second entry into Account Batch Outcome.
  - Design §9, the clinic, style, capability brief and validation are updated
    (governance **G21–G38**). The v1 sections are untouched.
- **Two clarifications made during the pass** (wording, not new decisions;
  the owner may object):
  - **M6 image rule:** OCR sufficient → no image and no flag. OCR
    insufficient + no PII → the image is sent. OCR insufficient + PII →
    blocking `image_withheld:pii`. A literal "otherwise" would have flagged
    every confidently read document.
  - **M8 lint:** "no v1 grant matches a v2 resource" has one designed
    exception: SD-4's `s3:GetObject` on `bundles/*`.
- **R10 (spec revision)** was started early and stopped with no changes. Per
  the owner's sequence, the spec is revised **after the LLD**.
- **Next: LLD.** See [`lld-v2-handover.md`](lld-v2-handover.md) and §5a.

## 5a. LLD inputs (left open by the HLD on purpose)

These are low-level choices the ratified HLD does not settle. The LLD settles
each one; none is a new HLD decision.

| # | Open point | From |
|---|---|---|
| L1 | The OCR-sufficiency threshold behind the M6 image rule. The rule itself was clarified on 2026-09-23: OCR sufficient → no image, no flag. | M6 |
| L2 | Where copied images live per revision (e.g. beside `bundles/<claim_id>/r<rev>`) | M12 |
| L3 | What a catalog-hash mismatch does (fail-closed reading: quarantine the batch) | M17 |
| L4 | The IAM that M14 implies: Distributed Map child executions, the watchdog rule's target, the dead-letter-queue policy. Adds IAM, so it is flagged under the approval criteria. | M14 |
| L5 | Which component runs the transcript digit-run scrub: Transcribe Call or Redact Sensitive Data. The component diagram states it in node detail only. | M6 |
| L6 | v1 re-entry items the LLD must respect but not fix: F2 (the await-review Lambda; review-bound claims stop there), F5 (grounding inert), M11 (pin a guardrail version). | fold map |

## 6. Ratification checklist (answer by id — one reply can cover all)

| Id | Gate (stage) | Decide | Recommendation |
|---|---|---|---|
| **R0** | **BLOCKING: live v1** | Fix **D0-a** (Catch `ResultPath` + an ASL data-flow test) and **D0-b** (summary guardrail + an AC-A5 test) now, then redeploy the state-machine definition + Lambda code, one interactive step at a time as in the v1 runbook | **fix first** |
| **R1** | Characteristics | (a) the 7 driving characteristics; (b) the top 3; (c) the demotions | as drafted |
| **R2** | Components | the component set; splits CS-1…CS-5; SD-1 / SD-2 / SD-3 | accept all |
| **R3** | Service choice | **separately:** capability class · services · approach · cost ceiling (PoC = the existing $10 budget; production `needs-input`) | as drafted |
| **R4** | Style | **separately:** D1 one quantum, pre-cut seam · D2 single-writer zones + SD-4 · D3 async hand-off + choreographed feedback · style A (orchestrated pipeline) | as drafted |
| **R5** | Solution design | **separately:** topology · memory · PII placement · IAM separation (qualified, C-3) | as drafted + M6 |
| **R6** | Resilience | the pack + knobs (reserved concurrency now 20); SD-6 metrics; the v1 5 × 5 retry finding → v1 re-entry | as drafted |
| **R7** | ADRs | Accept / revise / defer: **0016 · 0017 · 0018 · 0019 · 0020 · 0021 · 0022** | accept ✔ (M-series recorded per ADR; folded into the HLD artifacts by the consistency pass) |
| **R7q** | *Queued duty* (first-use approval criteria) | **Proposed:** owner approval suffices, **except** an ADR that widens IAM, changes where PII flows, adds an AWS service, or adds > $50/month. Those get a separate security/privacy review before Accepted. Recorded in `../adrs/approval-criteria.md` once agreed. | **R7q-a ✔** (2026-09-23): the four triggers + "widens what can auto-approve"; solo-PoC reading; [`../adrs/approval-criteria.md`](../adrs/approval-criteria.md) |
| **R8a** | Risk arbitration | dissents: P1-X3 (F / DQ say 9), P1-X4 (FM says 9), P2-X4 (OPS says 6); L-1 = 9 pending re-verification | keep the medians; L-1 yes |
| **R8b** | Risk mitigations | accept / reject / cheaper for each item, or by package: **v2 must-have** (M1 · M2 · M3 · M4 · M6 · M7 · M12 · M13 ≈ 5.5 d) · **should-have** (M5 · M10 · M14 · M15 · M16 · M17 · M18 ≈ 3.75 d) · **hygiene** (M8 · M9 ≈ 1 d); M11 → v1 | must-have + should-have + hygiene |
| **R8c** | Account-level | **M7** makes the account an AWS Organizations management account for the AI-services opt-out policy | **R8c-a ✔** (2026-09-23): opt out of all AI services; **owner performs it** (`../build/DEPLOY-LEDGER.md` "Stage A"); synthetic data only until verified |
| **R9** | Validation | per-intersection sign-off 1–9. Exceptions: #4 (no CI → a CI-hook task), #6 (header rule + intake version path). Unknowns #2 / #7 resolve at the smoke / by you. | sign off with exceptions |
| **R10** | Spec (A5-a) | After R0–R9: revise the spec (SD-1…SD-6, the accepted D0 / M-series, the header / version rule, the CI hook, G1–G49 as tasks, the AC-W7 fix). Then one approval, then build. **Re-sequenced by the owner (2026-09-23): LLD first, then the spec.** | proceed, after the LLD |

| **H-F14** | Formatting contract (ADR 0021), raised by live-v1 F14 | Carry input tagging into v2: every claim-derived context section goes in `guardContent`; instructions, schema and policy excerpts stay plain text. **Images:** (a) plain image blocks, not guardrail-checked. The guardrail checks no images today: prompt-attack is TEXT-only (verified) and the harmful-content filters are off. M1 + canonical routing hold integrity against visual injection. (b) Guardrail image blocks inside `guardContent` **[re-verify** model visibility and filter support**]**. (c) No tagging: F14's false positives return. | **H-F14-a ✔** (2026-09-23): ADR 0021 amendment |

**Fastest path:** reply "**ratify as recommended**". That covers R0 (fix live
v1 first) through R10, and leaves **R7q** (approval criteria) and **R8c** (the
account-level opt-out) for you to state explicitly.
