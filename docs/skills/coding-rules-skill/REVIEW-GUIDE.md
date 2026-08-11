---
type: validation-walkthrough
title: 'Coding-Rules Skill — Eval Reviewer Walkthrough & Rubric'
description: >-
  Reviewer walkthrough and 7-dimension scoring rubric for human review of the
  coding-rules skill's eval runs (iteration 1): per-run guidance, seeded
  ground-truth tables, and a CR-01..CR-18 crib sheet for spot-checking rule
  citations. Canonical copy; the eval outputs live in the evidence-excluded
  tooling/coding-rules-skill-workspace/.
tags: [rubric, coding-rules, skill-eval, walkthrough]
---

# Reviewer Walkthrough — coding-rules skill, iteration 1

Companion to the eval viewer at **http://127.0.0.1:3117**. Six runs: 3 test
cases × (with-skill / baseline). The automated grading already verified the
*mechanical* facts (25/25 with-skill, 23/25 baseline, all verdicts
independently re-checked). **Your job is what grep can't score:** quality,
precision, proportionality, and whether you'd actually want these outputs in
the o1 workspace.

## How to work

1. For each test case, read the **with_skill** output first, then
   **without_skill**, then ask: *"as the o1 tech lead, which one would I
   want on my desk — and what's missing from both?"*
2. Type feedback in the box (auto-saves). Put your substantive feedback on
   the **with_skill** runs — that's what drives iteration 2. Comment on a
   baseline run only when it did something the skill version should copy.
3. Score each with-skill run on the rubric below; paste the scores into the
   feedback box (a one-liner like `R:5 P:3 S:4 A:4 F:5 Prop:2 Read:3 — see
   notes` is enough).
4. When done, click **Submit All Reviews**, then tell me in chat.

**Do not grade:** wall-clock time (the two review runs were interrupted by
an API error and resumed); compilation (fixture can't compile on JDK 11 —
known environment limit); the baseline's lack of CR-xx IDs (by design).

---

## The rubric (score 1–5 per dimension)

| # | Dimension | 5 looks like | 3 looks like | 1 looks like |
|---|---|---|---|---|
| R | **Rule correctness** | Every spot-checked CR citation matches what the catalog rule actually says | Citations right in spirit, occasionally stretched to fit | IDs decorative or misattributed |
| P | **Precision (signal/noise)** | Every finding beyond the 10 seeds is real and worth fixing; no book-purism that an ADR overrides | A few debatable extras, clearly labeled | Manufactured violations; would breed alert fatigue |
| S | **Severity calibration** | Security findings marked security; triage order matches real risk | Ordering roughly right, some inflation | Everything is High; or a security issue rated cosmetic |
| A | **Actionability** | Fixes name the concrete mechanism in *this* repo (the port, the config class, the schema) | Fixes correct but generic | "Refactor for cleanliness" hand-waving |
| F | **Process fidelity** | Skill protocol visibly followed: binding resolved, missing-gate double findings, security framing, report-only where required | Protocol partially followed | Skill read but ignored |
| Prop | **Proportionality** *(implement run only)* | Diff sized to the task; every extra class earns its keep via a rule | Somewhat ceremonious but defensible | Gold-plating in the rules' name |
| Read | **Readability** | Summary-first; a teammate could act without rereading; length matched to purpose | Complete but heavy | Wall of text; key findings buried |

**Interpreting totals:** any dimension ≤ 2 → name it explicitly in feedback
(it becomes the iteration-2 focus). All ≥ 4 → the skill front-end likely
needs no change for that mode; we iterate on the eval instead.

---

## Test case 1 — Review mode (`eval-0-review-seeded-violations`)

**Asked:** review the repo, write findings.md (file / problem / why /
severity / fix). **Ground truth — 10 seeded violations:**

| File | Seeded violation | Rule |
|---|---|---|
| `conversion/replay/FailureTriage.java` | direct `ChatClient` model call | CR-05 |
| `conversion/replay/ReplayService.java` | async post-commit provenance write | CR-14 |
| `conversion/capture/ActionExecutor.java` | executes on model confidence > 0.8 | CR-16 (security) |
| `evidence/storage/ArtifactSaver.java` | evidence written to `/tmp` | CR-07 |
| `certification/domain/CertificationPolicy.java` | `@Service` + `@Autowired` field in domain | CR-11 |
| `com.bank.o1.services` / `.util` packages | layer-named packages | CR-03 |
| `certification/web/CertificationController.java` | returns JPA entity over HTTP | CR-12 |
| `conversion/ingestion/IngestionCoordinator.java` | reach-in past `evidence.api` | CR-01 |
| `replay` ↔ `capture` | package cycle | CR-02 |
| `certification/web/ReviewController.java` | certification thresholds inline | CR-13 |

**with_skill (17 findings, ~30 KB):** both configs found all 10 seeds, so
focus on what only judgment can rate:

- **Spot-check 2–3 CR citations** against the crib sheet below (dimension R).
  A wrong ID in a real workspace routes a fix to the wrong ADR.
- **The 7 extra findings** (crossing-type vocabulary, no composition root,
  seed-gap notes, etc.) — real value or padding? (P)
- **Would you triage in its order?** Two Criticals first, then the gates? (S)
- **Length:** is ~30 KB right for a repo audit, or do you want a one-page
  summary + appendix? This directly shapes the front-end's output guidance. (Read)

**without_skill (20 findings):** notice it found *more* raw findings
(including genuine ones like the S3 adapter never calling S3, path
traversal in ArtifactSaver). Two questions: is the extra breadth something
the skill *suppressed* (bad) or out-of-scope opportunism (fine)? And does
the Medium rating on ActionExecutor confirm that severity calibration is
real skill value?

## Test case 2 — Implement mode (`eval-1-implement-stabilization-hint`)

**Asked:** on FLAKY replay outcome, get a model-proposed stabilization hint
(3-value set), validate, record; wire into ReplayService; small diff.

**with_skill (5 files):** port interface + enum + gate class + adapter
bridge + ReplayService change, with pinning fields and a
`STABILIZATION_HINT_REJECTED` event. **The central question is Prop:**
read `outputs/change.diff` as a PR — does each extra class earn its keep
via a rule (the consumer-owned-port/cycle argument, the versioned gate), or
is this gold-plating a 2-file task into 5? Would *you* merge it?

**without_skill (2 files):** enum with parser + ReplayService change,
straight through `InvokeModels`. Cleaner — but note what it skipped: no
pinning fields, no rejection event, silent drop on invalid proposals.
**Which diff would you actually merge into o1, and why?** Write that in
feedback — it's the single most useful sentence you can give me for
iteration 2.

## Test case 3 — Converge mode (`eval-2-converge-gap-classification`)

**Asked:** classify gaps between a spec excerpt and a teammate's diff.
**Ground truth — 4 seeded gaps:** direct `ChatClient` (violates criterion
1 / CR-05), confidence threshold instead of enum validation (contradicts
criterion 2 / CR-16), persistence+lineage never implemented (missing
criterion 3), debug endpoint (explicitly out of scope).

- **Routing test (F):** from each report, could sdd-converge mechanically
  decide fix-task vs replan vs de-scope? The spec's taxonomy is
  missing/partial/contradicts/unrequested; the with-skill report used
  Missing/Divergent/Out-of-scope, the baseline MISSING/DIVERGENT/SCOPE/
  DEFECT/STANDARDS. Equivalent — or should the skill *force* the exact
  sdd-converge vocabulary? Your call here changes the front-end.
- Does the with-skill report's extra finding (missing ArchUnit gate, G1b)
  and security framing of the confidence gate justify its existence over
  the strong baseline? (P, S)
- Both reports correctly attributed pre-existing fixture violations as
  not-the-teammate's. Check the tone: fair to the hypothetical teammate,
  or blame-y? (Read)

---

## Crib sheet — the 18 rules (for spot-checking citations)

A. Structure — **CR-01** module access only via `api` packages · **CR-02**
no cycles · **CR-03** domain-named packages, never layers · **CR-04**
package-private by default.
B. Seams — **CR-05** all model calls via Invoke Models seam (load-bearing)
· **CR-06** only committed vocabulary crosses it · **CR-07** evidence only
via storage port · **CR-08** Strategy-shaped seams, no registries/backchannels
· **CR-09** no provider conditionals in core · **CR-10** narrow
consumer-owned ports.
C. Core purity — **CR-11** framework-free core, wiring at composition root
· **CR-12** DTOs cross boundaries, never entities/rows · **CR-13** humble
controllers/CLIs.
D. Data & flow — **CR-14** lineage in-transaction, lineage schema only ·
**CR-15** async only at the two decided seams (outbox) · **CR-16** model
proposes, determinism disposes (security).
E. Tests & metrics — **CR-17** test the API, not the structure · **CR-18**
CC ≤ 10 / Distance < 0.3 as ratchets.

Full text with trade-offs: `tooling/coding-rules-skill/references/rules-catalog.md`.

---

## Already queued for iteration 2 (no need to re-report these)

1. ArchUnit seed **D-2** misses `CompletableFuture.runAsync`; **B-3**
   misses `java.nio.file` writes — found by the skill itself, will fix.
2. The implement eval discriminated nothing (7/7 both configs) — fixture
   hints will be stripped and/or assertions added for pinning, rejection
   routing, and gate versioning.
3. Review-run timing is not comparable (API interruption + resume).
