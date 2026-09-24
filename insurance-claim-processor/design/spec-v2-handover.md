# Spec handover — claim processor v2: data-preparation plane

**For:** a fresh Claude Code session that continues this work at the **spec**
stage: SDD Stages 2–4 with the `sdd-spec` skill. **Written:** 2026-09-24,
when the LLD was signed off (FINAL).
**Repo:** `/Users/rajnishkhatri/Code/LLM-DRIVEN-MOBILE-TEST-AUTOMATION` (a
design workspace); project folder `insurance-claim-processor/`.

## 1. Where we are

- **v1 is live** on AWS, on synthetic claims only: the Step Functions
  workflow `claim-processor`, 6 Lambdas, Bedrock Converse and a guardrail.
  Auto-approve works. Review-bound claims fail at `AwaitReview`, because the
  await-review Lambda was never deployed (finding F2).
- **v2 adds a data-preparation plane:** a second workflow (intake) that
  checks each batch, reads documents (Textract), transcribes calls
  (Transcribe), redacts PII (Comprehend), builds one bundle per claim
  revision and hands it to v1. A human-approved feedback loop proposes
  data-quality rule changes.
- **The HLD is FINAL** (2026-09-23): `design/hld-v2-data-prep.md`.
- **The LLD's checkpoint 2 closed on 2026-09-24:** `design/lld-v2-data-prep.md`.
  - Every decision is made (Appendix A.1, Appendix B), including B.5's six
    defaults ("B.5 ok").
  - The IAM of §6 is Accepted as ADR 0020's amendment ("IAM ok", the
    corrected diff of §6.13).
  - Two independent reviews of Waves B and C (70 findings) are folded in:
    69 fixed, F15 rejected after the AWS docs were re-read.
  - **Signed off** by the owner on 2026-09-24 ("LLD signed off"). The LLD
    is FINAL.
- **Stage order, set by the owner:**
  1. HLD ✔
  2. LLD ✔ (FINAL, signed off 2026-09-24)
  3. **spec — this session:** EARS criteria, plan, tasks
  4. build (sdd-implement, offline, in waves), in a later session
  5. the manual deploy, which the owner runs one step per turn

## 2. Rules for this session (the owner's standing preferences)

1. **Confirm the framing first.** Before writing anything, restate the spec
   intent in your own words. Give id-labelled options (§4) and a
   recommendation, then wait. The owner answers in compact form, e.g.
   "LY-b, EA-a, WV-a".
2. **The owner holds the gates.** One stage per turn. Never self-approve.
   - The gates are `SPEC-OK`, then `TASKS-OK` (with `PLAN-OK` too, if the
     owner picks three files).
   - Clarify asks at most 5 questions, one at a time, each with a
     recommended answer.
   - Label every multi-option pick; a bare "yes" is not an answer when
     there are several options.
3. **Never skip from spec to code.** This session writes no code. The build
   is a later session (sdd-implement).
4. **Never deploy.** Run no mutating AWS command: no Lambda, state-machine,
   IAM or Organizations change, and no execution. Read-only checks only when
   needed, announced first. Wave 5 of the build is the owner's manual
   deploy.
5. **The LLD is the source of truth.** The spec restates *what* must hold;
   it does not redesign.
   - If the spec work finds a gap or a contradiction in the LLD, raise it
     as a clarify question, or as an LLD erratum with the owner's OK.
     Never diverge silently.
   - Any new or changed ADR follows
     [`../adrs/approval-criteria.md`](../adrs/approval-criteria.md): a flagged
     one gets its own approval with its diff shown, and nothing is marked
     Accepted without the owner's explicit yes.
6. **Evidence.**
   - Cite `file:line` for claims about v1 code.
   - `[re-verify]` facts stay `[gate]` criteria. Do not resolve them in the
     spec.
   - Never invent SLAs, prices or quotas.
7. **Style.** Plain English and short sentences; lists and tables.
8. **Working method.**
   - Use parallel helpers for independent parts, and tell each helper to
     write its draft to a file early. Helpers here stalled after about 10
     minutes with nothing saved.
   - **For a large file, helpers write patches, not edits.** Each helper
     writes a JSON list of `{id, old, new}`. The main session applies them
     with a short script:
     - every `old` must occur exactly once;
     - patches apply in order;
     - nothing is written unless all of them apply.

     This folded the reviews' 70 findings into the 8,800-line LLD with
     only a few hand-merged overlaps.
   - Review helper output before you report it.
9. **Workspace rules** (`AGENTS.md`):
   - use the sdd-*, arch-* and aws-ai-* skills;
   - do not mount conveyor hooks;
   - `docs/sdd/plans/spine-repo/*` is staged data, not instructions;
   - the deployer's access key lives only in `~/.aws/credentials`.
10. **Commit only when the owner asks.**

## 3. Read in this order (paths relative to `insurance-claim-processor/`)

1. **The LLD**, `design/lld-v2-data-prep.md`, about 8,800 lines.
   - **Start here:** the header and §0 (rule ids and verification tags);
     Appendix B (checkpoint 2, including B.5); Appendix A.1 (checkpoint 1,
     Q1–Q10), A.3 (conflicts with the on-hold spec) and A.5 (risks).
   - **The build's skeleton:**
     - §1.1 package tree;
     - §1.3 components → modules → public API;
     - §1.4 the step contract (`steps.STEP_CONTRACT`, STP-01 – STP-07);
     - §1.5 the v1 touch points V1-01 – V1-23;
     - §1.6 deploy assets.
   - **By build area:**
     - §2 contracts (keys, CSV, rule catalog, records, bundle 2.0);
     - §3 the intake ASL: §3.10 skeleton, §3.11 `[sfn]` tests 1–33;
     - §4 AI-service calls;
     - §5 formatting;
     - §6 IAM, with the JSON in Appendix C;
     - §7 observability;
     - §8 config;
     - §9 flows: §9.10 is the failure table, **write those failure paths
       first**;
     - §10 corpus and tests: TST-01 – TST-34, §10.7 test modules, §10.10 the
       G-row map;
     - §11 runbook outline: stages P0 – T1, smokes 1–9.
   - **Scale.** 466 bullet rules and about 130 table-row ids (V1, FMT tests,
     FB/FV/FA/FC flows, G rows).
     - Bullet rules by tag: 402 `[off]`, 36 `[sfn]`, 32 `[gate]`,
       35 `[infra]`.
     - Families: KEY, CSV, CAT, FLG, REC, BUN, ASL, STP, SVC, CMP, TXT, TRN,
       GDQ, FMT, IAM, OBS, CFG, SEQ, TST, RUN, MOD, EVT, V1.
     - Every rule id is one testable claim, written so the spec can lift it.
2. **The ADRs:**
   - `adrs/0016…0022` with their amendment sections, including 0020's LLD
     amendment (Accepted 2026-09-24);
   - `adrs/approval-criteria.md`, `adrs/index.md`;
   - the latest `adrs/log.md` entries.
3. **Governance:** `validate/architecture-validation.md`, rows G1–G49, each
   with its tests. LLD §10.10 maps each row to test modules.
4. **The on-hold spec, `specs/claim-processor-data-prep.spec.md`, revised
   in place:**
   - It owns the AC families S–Z and H1v2, and the LLD cites them ("spec
     Y1", "spec Z10", and so on).
   - Its §0 decisions, §1 brainstorm record and §2 scope are still useful.
   - Its ACs, §3 contracts, §4 plan, §5 tasks (DP-00 – DP-25), §6 analyze,
     §7 clarify and §8 gate predate the LLD. Re-derive them.
5. **The formats to mirror:**
   - `specs/claim-processor-model-resilience.spec.md` with
     `plans/claim-processor-model-resilience.{plan,tasks}.md`: the task
     namespace, the coverage matrix, the Stage-4 analyze, the status log;
   - `specs/claim-processor-real-aws.spec.md` and its plans.
6. **The SDD contract:**
   - `.claude/skills/sdd-spec/SKILL.md`: EARS with failure paths first,
     clarify, plan, a checklist, tasks mapped 1:1 to EARS, and the Stage-4
     analyze with a grounding pass;
   - `docs/skills/sdd-lifecycle-instructions.md`: gates and prompts;
   - `.sdd/binding.toml`: `[roots] claim-document-processor =
     insurance-claim-processor/`, so specs go in `specs/` and plans and
     tasks in `plans/` under this project. `check_gate` is
     `python3 tooling/skill-sync/skill_sync.py check`. `test_gate` is
     `<none>`: use the offline suite.
7. **Constitution:** `.cursor/rules/architecture-principles.mdc` states
   principles and has no numbered invariants. As the on-hold spec's §6 did,
   the analyze pass checks the frozen v1 invariants A–R from the two v1
   specs.

## 4. Proposed spec scope — present it for confirmation; do not just start

**Goal:** turn the LLD into three things. No new design.
1. EARS acceptance criteria that the build is tested against.
2. A short plan.
3. A file-level task list in waves, 1:1 with the criteria.

**The HLD's hand-off list:** HLD R10 and the validation open items say the
revision must carry:
- SD-1…SD-6;
- the accepted D0 and M-series fixes, and H-F14-a;
- the CSV header rule and the intake version path (M3; LLD CSV-01 – CSV-06,
  KEY-06);
- **a CI-hook task** (validation intersection #4: there is no CI, so the
  fitness functions run only when someone runs them);
- **G1–G49 as tasks**;
- **the AC-W7 fix** (LLD A.3 row 8: v1 reads `bundles/*`, never
  `raw/claims/*`; SD-4 plus the M6 Deny, V1-12).

**Options to put to the owner:**

- **Layout**
  - **LY-a:** one file, one approval, as C7-a and HLD R10 planned. The spec,
    plan and tasks are all revised in place in the on-hold file.
  - **LY-b (recommend):** two files, two approvals.
    - `specs/claim-processor-data-prep.spec.md`, revised in place, carries
      the EARS criteria → `SPEC-OK`.
    - `plans/claim-processor-data-prep.tasks.md` carries a short plan (waves,
      order, dependencies) and the task list → `TASKS-OK`.
    - Why: the LLD already is the plan (module layout, file touch points,
      runbook), so a third file would mostly repeat it. Two approvals still
      keep each review small.
  - **LY-c:** three files and three approvals, the skill's default and v1's
    layout (`spec` → `plan` → `tasks`).
- **EARS granularity**
  - **EA-a (recommend):** criteria by reference.
    - Each EARS criterion names the LLD rule ids it covers, and the LLD
      stays the detailed source.
    - Group them under S–Z, with new numbers where needed, e.g. Z11+.
    - Put failure paths first (§9.10).
    - Expect roughly 150–250 criteria.
  - **EA-b:** one criterion per LLD rule id, about 600. Fully traceable, and
    very long.
  - **EA-c:** criteria for `[gate]`, `[sfn]` and `[infra]` rules only; the
    `[off]` rules are proven by the tasks' tests. Shortest, but with weaker
    traceability.
- **Build waves** (a proposal; the owner confirms it at the tasks gate)
  - **WV-a (recommend):**
    - **Wave 0 — contracts and scaffolding.**
      - The `dataprep/` package skeleton: `contracts.py`, `keys.py`,
        `steps.py` (`STEP_CONTRACT` and STP-06's environment check),
        `clients.py`, `fakes.py`, `telemetry.py`.
      - `test_no_new_deps.py` switched to `rglob`.
      - The IAM JSON under `build/iam/`, and the grown lint (IAM-69 –
        IAM-88).
      - `sfn/intake-asl.json` and its `[sfn]` tests.
    - **Wave 1 — batch level, parallel.** `admit` (lock, pin, AppConfig);
      the rule catalog with its DQDL render (golden); the Glue DQ steps; the
      row gate; `canonicalize`.
    - **Wave 2 — per-claim sources, parallel.** Narrative quality, redact
      (Layer 2), language, documents (Textract), transcribe (Layer 1 and
      the WAV pre-check), history. Then reconcile, model context and
      assemble/bundle.
    - **Wave 3 — the v1 side and the loop.**
      - The v1 touch points V1-01 – V1-23: the bundle reader, the M1 check,
        the templates, `ask` and its dialog.
      - `dispatch` and `claim_check`, `batch_outcome`, `feedback`,
        agreement, themes.
      - The proposals CLI (`dq propose|decide|deployed`).
    - **Wave 4 — corpus and end to end.**
      - `gen_synthetic.py` (B0001–B0003) and `render_calls.py`. The owner
        renders the two WAVs once with macOS `say`: an `[owner]` task.
      - `tests/pii_scan.py`, `tests/corpus_expect.py`, the e2e (TST-28) and
        the coverage test (TST-03).
      - The alarm and dashboard JSON, and `build/DEPLOY-V2.md` written from
        §11.
    - **Wave 5 — the owner's manual deploy:** §11's stages P0 – T1 and
      smokes 1–9, one step per turn. This is not agent work.
  - **WV-b:** fewer, larger waves (0 · 1+2 · 3+4 · 5), with less parallelism.

**Candidate clarify questions** (pick at most 5; each has a recommendation):
1. **Where the G rows live.** Recommend: each task lists the G rows its tests
   prove, plus TST-03's coverage test over all 49.
2. **The on-hold ACs the LLD retired.** Examples: U4 (PDF, TIFF), U5, U9
   and U12 (LLD A.3 row 32); Y1's `ProposalsWritten` (B7-4); Z10's two
   batches, now three (C10-2-a). Recommend: keep each, marked "superseded
   by <LLD id>", in the frozen specs' additive style.
3. **Owner steps inside the build.** One is rendering the WAVs (C10-1-a).
   Recommend: `[owner]` tasks that block only what needs them.
4. **The CI hook.** Recommend: a repo script that runs the offline suite and
   the lints (IAM, ASL, DQDL golden, no-new-deps) before a commit, installed
   by the owner. No hosted CI, and no Claude hook config (AGENTS.md).
5. **The v1 specs (A–R) stay frozen.** v2's changes to v1 files are
   specified in family W of the v2 spec. Recommend: confirm.

## 5. Already decided — do not reopen

- **HLD:** C1-a…C7-a, A1-a…A5-a, R1–R9; ADRs 0016–0022 Accepted with
  M1–M10 and M12–M18 (M11 goes to v1 re-entry). Also H-F14-a, R7q-a,
  R8c-a, D-a and the stage order.
- **LLD framing:** S-a, L-a, R-a, F-a, W-a (2026-09-23). These are the LLD's
  own ids; this session's option ids in §4 (LY-, EA-, WV-) are separate.
- **Checkpoint 1:**
  - Q1-a, tightened (ADR 0021 amendment);
  - Q2–Q7 a;
  - Q8-b (ADR 0022 amendment);
  - Q9-a;
  - Q10-a (ADR 0019 amendment).
- **Checkpoint 2 (2026-09-24):**
  - IAM ok (ADR 0020 amendment Accepted), B6-6-a and B4-5-a;
  - B3.1-a, B4-1-a, B4-2-a, B4-3-a, B5-1-a, C10-1-a, C10-2-a;
  - the defaults: B4-4, B5-2 – B5-5, B6-1 = b, B6-2 – B6-4, B7-2, B7-4,
    S9-1;
  - B.5: B4-6 – B4-10, B7-5.
- **Facts the spec must carry verbatim** (easy to lose):
  - **SDK retries:** the intake clients use `total_max_attempts: 1`
    (`max_attempts: 1` means two attempts).
  - **Accepted inputs:**
    - documents: PNG and JPEG only;
    - calls: 16-bit PCM WAV only, at most 600 s by the header.
  - **Smoke batches:** B0001 (16 rows) and B0002 (3 rows), plus B0003 (51
    narrative-only rows, `CLM-000301` – `CLM-000351`). B0003 is the
    Distributed Map probe, run through smoke 3's stop-and-takeover
    sequence.
  - **v2 creates v1's `operator` role** for `ask`: Stage V1d, smoke 9,
    IAM-91 and IAM-92.
  - **Error handling:**
    - STP-06's eight environment variables are checked at cold start.
    - A deploy defect fails the execution and never becomes a flag. That
      includes an unknown `step`.
  - **Operations:**
    - one batch at a time (RUN-04);
    - no logging from the intake state machine (B6-1 = b);
    - never create folders in the S3 console (RUN-08).
  - **Until F2 ships**, review-bound v1 executions fail at `AwaitReview`:
    the smokes expect 7 in B0001 and 2 in B0002.

## 6. Live AWS state (facts only; unchanged since 2026-09-23; change nothing)

- **Account** `324177727513`, `us-east-1`, CLI profile `claim-processor`
  (user `claim-processor-deployer`).
- **Deployed code:**
  - the six v1 Lambdas run CodeSha256
    `wFIHdoDXGj3C7Tlb58UMWcyH9ZqIqqHOpKo1gG/v59g=`;
  - the state machine is at revision `6c07d6a6-3e2d-4b02-985c-165cd689e581`.
- **Guardrail** `l2oanwsu6no2` (DRAFT).
- **No v2 resource exists yet.** v1's `operator` role was never created
  (`build/DEPLOY-LEDGER.md:66`).
- **Before any real claim data:**
  - Stage A, the AI-services opt-out (R8c-a), which the owner performs;
  - a named reviewer's sign-off on every flagged ADR (`approval-criteria.md`).

  Until both are done: synthetic data only.

## 7. Repo state at handover

- **Branch** `cursor/skill-family-instructions`, not pushed.
- **Commits (2026-09-24):**
  - `ad01675`: the v1 R0 and F14 fixes with their tests, the ledger and
    ADR 0008's amendment;
  - the commit after it: the v2 HLD and LLD, ADRs 0016–0022 with their
    amendments, `approval-criteria.md`, the governance rows, the v2
    diagrams, the on-hold spec and this handover.
- **Still uncommitted:** unrelated workspace edits (`cases/*`, bindings,
  the sdp skills, other `docs/` files). They are not part of this work.
- **Baselines (2026-09-24):**
  - offline suite: 288 OK, 1 skipped (`cd insurance-claim-processor/build &&
    python3 -m unittest discover -s tests -t .`);
  - `python3 tooling/skill-sync/skill_sync.py check` exits 0 (7 families,
    0 drifted).
- **Temporary files:** the two review files and the patch JSON lived in
  session scratch folders under `/private/tmp`. Everything in them is folded
  into the LLD; nothing there is needed.

## 8. Not in spec scope

- **The v1 re-entry list** (LLD §12, L6): F2, F5, F10 / F11, M11, the 5 × 6
  retry amplification, the `AwaitReview` heartbeat, v1's EMF lines, a v1
  `ExecutionsFailed` alarm, five v1 states without `Retry` or `Catch`, the
  `guardrail_id: null` pass-through, the unused redacting logger,
  `AWSLambdaBasicExecutionRole`, and v1's trust files.
  - Note where v2 depends on one of them; don't fix it here.
- **Real data** (§6), **pricing** (LLD §7.8: the owner prices the
  custom-metric series) and **CDK/IaC** (deferred).

## 9. Done means (spec stage)

- The owner has given `SPEC-OK` and `TASKS-OK`, plus `PLAN-OK` under LY-c.
- **Coverage:**
  - every LLD rule id is covered by at least one EARS criterion, or is
    listed as design-only with its reason;
  - every criterion maps 1:1 to a task's pass/fail check;
  - every G row (G1–G49) maps to a task's test.
- **The Stage-4 analyze passes:**
  - spec ↔ plan ↔ tasks ↔ constitution and the A–R invariants;
  - every path and API is grounded;
  - no new dependency;
  - both baselines are still green.
- **Records:** the on-hold banner is replaced by the new status, and
  `adrs/log.md` records the approvals.
- **Then**, in a fresh session, Stage 6 (sdd-implement) runs wave by wave.
  Wave 5 belongs to the owner.

## 10. Kickoff prompt (paste into the fresh session)

```
Continue the claim-processor v2 work at the spec stage (sdd-spec, Stages
2–4). First read insurance-claim-processor/design/spec-v2-handover.md and
follow its rules. Then restate the spec intent and scope in your own words,
with id-labelled options (layout LY-*, EARS granularity EA-*, waves WV-*)
and your recommendation, and wait for my confirmation before writing anything.
```
