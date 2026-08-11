---
type: plan
title: sdd-roles / o7 — live-leg completion + kata study plan (post ADR 0006)
description: >-
  Cold-session-executable plan for the work remaining after the 2026-08-09
  ADR 0006 landing and the first fully-green live conveyor run: the live
  write-guard (hooks) leg, the 12 real kata workspaces, the workload swap +
  kata restamp, a budget-gated pilot, the kata LLM study itself, and the
  event/environment-driven seams (T05, future gate ids, copilot/cursor
  legs). Supersedes next-items-plan.md for open work; that file remains the
  record of items 0–2.
date: 2026-08-09
status: open
supersedes: next-items-plan.md
adr_0005: ../../../architecture/adrs/tooling/sdd-roles/0005-ir-gate-first-class-gate-vocabulary.md
adr_0006: ../../../architecture/adrs/tooling/sdd-roles/0006-live-invocation-runner-contract-channel.md
probe_report: ../evals/live-leg-probe-report.md
battle_test: ../evals/battle-test-report.md
tags: [sdd-roles, o7, plan, kata, live-leg, hooks, seams]
---

# Live-leg completion + kata study plan (written 2026-08-09, end of second session)

> ## ⛔ SUPERSEDED for open work — start at [kata-study-execution-plan.md](kata-study-execution-plan.md)
>
> Items 0–4 of this plan are **DONE** (status block below is the record).
> Everything still open — the two blocking owner decisions, the per-arm
> config prerequisite, and the kata study itself — moved to
> [kata-study-execution-plan.md](kata-study-execution-plan.md), which is
> cold-session executable and carries the current stamps. Read this file only
> for the history of items 0–4.

> **Execution status — updated 2026-08-09, third session.**
> **Item 0** green (selftest 20/0 ×2, ir-gate 8/8, o7 validate 29/0, validator
> 0.7.2, stamp `kata:26b8f03465ba` at session start).
> **Item 1 DONE with a blocker found** — hooks mounted, scripted probe 12/13,
> and the **first live in-flight block** against a live model (protected test
> left byte-identical). Recorded as probe-report **Part 3** + evidence bundle
> `../evals/evidence-live-hooks-001/`. The 13th probe case is the blocker:
> ADR 0006 *requires* every role to write `<run_dir>/handoff.draft`, and the
> D7 guard law (`writer-only-run-dir`) *forbids* any role write into the run
> dir — so a hook-mounted run cannot complete a single stage. **Owner
> decision required** (see §D1 below); it blocks the `seeded-bugfix` family
> and item 5's D7 leg only.
> **Item 2 DONE** — 12 workspaces at `tooling/sdd-roles/kata-workspaces/`,
> generated + layout-linted, and all 24 build/tests baselines verified with
> the REAL gate tools. Choices, provenance and baselines: that dir's README.
> **Item 3 DONE** — real `source_kata` values swapped in; plan restamped
> `kata:26b8f03465ba` → **`kata:73fca8cae0f6`**; 9 results files swapped, 8
> verdicts + scorecard regenerated, tamper verdict still `winner none /
> tamper-invalid`, `PREREG_CONSTANTS` untouched, selftest 20/0 ×2. The stale
> `kernel/docs/kata-seam.md` path is fixed as a dated note.
> **Item E3** re-probed: `copilot`, `cursor`/`agent`/`cursor-agent` still
> absent → both legs stay open on CLI absence alone. `claude` 2.1.185.
> **Item 4 DONE — the pilot cell went fully green.** greenfield-1 (Mars
> Rover) × arm B × 1 rep: runner exit 0, **7/7 gate executions green on
> attempt 1, zero rework**, `mutation_score 1.0`, 1587 s wall clock
> (specifier 339 s / maker3 292 s / checker3 955 s). Evidence:
> `../evals/evidence-pilot-greenfield-1/`; narrative: probe report Part 4.
> **Budget (measured, not estimated):** 472 input / 174,397 output /
> 4,039,265 cache-read / 258,868 cache-write tokens per cell — cache reads
> are 96.1% of input-side tokens. Per cell $4.80 on Sonnet 4.6 (what ran),
> $8.00 on Opus 5 → **60 cells $288 / $480; 240 cells $1,152 / $1,920**;
> 26.4 h / 105.8 h serial. Floor, not a mean — this cell needed no rework.
> En route the ADR 0006 decision clause needed a third correction (item
> types, not just container shape); descriptor fixed, six-regen run,
> projection stamp `catalog:b2b1edd94ec0` → **`catalog:1d520797652a`**,
> selftest 20/0 ×2, ADR 0006 amended.
> **Item 5 remains owner-gated** on §D1 and §D2 below plus the budget.
>
> ### §D2 — second open owner decision (from item 4)
> **The study model is not pinned.** The pilot ran on `claude-sonnet-4-6`
> only because the operator's CLI is set to `opusplan`; the plan is
> generated `--default-model UNBOUND` and the descriptor carries no
> `--model` flag, so the model silently follows an unrelated local setting
> and is not recorded in the run. For an arm-comparison study that is a
> validity threat. Fix before item 5: add a `--model {model}` token to the
> descriptor row (the plan's `bindings[]` already carry a per-cell model),
> regenerate the plan with a real `--default-model`, and record the resolved
> model in each `cell_result` — a descriptor change (six-regen + selftest
> ×2) plus a kata restamp.
>
> ### §D1 — open owner decision (from item 1)
> Resolving the contradiction means amending the guard so the current stage
> role may write exactly `<run_dir>/handoff.draft` and nothing else in the
> run dir. That is an ADR-level change to the D7 floor carrying the full
> invariant-2 tax (guard corpus cases, dated ADR amendment, selftest
> re-green) — deliberately NOT taken on implementer initiative. A second,
> smaller decision rides with it: `gate-wrap` captures the guard's stdout, so
> a blocked model never sees the real block code (`TESTS_PROTECTED`,
> `PROTECTED`, `SCOPE`, `WRITER_ONLY`) — see probe report §3.5.

Everything below assumes **no memory of prior sessions**. §1 is the
world-state; §2 the invariants (including the ones this day's live runs
taught); §3 the items in execution order; the appendices hold the proven
procedures and the live-run rig parameters.

---

## 1. State snapshot (verified 2026-08-09, end of second session)

All paths relative to `tooling/sdd-roles/` unless rooted.

| Surface | State |
|---|---|
| Kernel / validator | schema 1.4.0 / validator **0.7.2**; `contract-lint selftest` **20/0 ×2 byte-identical**; catalog projection stamp `b2b1edd94ec0`; kata plan stamp `kata:26b8f03465ba` (UNCHANGED all day — instrument intact) |
| Gate tools | **all five built and row-proven**: `tools/{ir-gate-checker,javac-build,junit-runner,crap4java,mutate4java}/` — ir-gate-checker template (fixtures + selftest ×2 green each; exits 0/2/3 fail-closed; canon thresholds echoed). Engines: mvn compile diagnostics; surefire XML (zero tests = red); JaCoCo 0.8.12 per-method CRAP ≤ 6; PIT 1.16.1 integer-scaled ≥ 8500 |
| Live invocation | **[ADR 0006](../../../architecture/adrs/tooling/sdd-roles/0006-live-invocation-runner-contract-channel.md) Accepted + landed**: runner contract (task `{args}` — required bind, `{run_dir}`, `{next_role}`, exact handoff.draft shape incl. the decision law) rides a quoted composite prompt token in all three live descriptor rows; `_invoke_role` exposes `next_role` (final stage → arm entry); token regex accepts digits (0.7.2 fix — `{crap4java}`/`{mutate4java}` were unfillable before) |
| Live proofs | **First live green stage AND first fully-green live conveyor run** (`live-full-001`: arm B specifier→maker3→checker3, exit 0, 7 gate executions green incl. live PIT scaled 10000). Evidence + digests: `../evals/evidence-live-full-001/`; narrative: probe report Part 2. En route, D7 test-write protection and `chk_decisions_v1` each refused a live model's overreach — guards proven in anger |
| Harness CLIs | `claude` 2.1.185 present (`--agents` takes inline JSON — bind a JSON object, not a path). `copilot`, `cursor`/`agent` **absent** → R-COPILOT-LIVE / R-CURSOR-LEG open on CLI absence alone (their descriptor rows already carry the ADR 0006 contract) |
| Hooks (write-guard live leg) | **NOT yet mounted in any live run** — deterministically proven only (battle-test). The live runs so far ran hook-less workspaces; this is item 1 |
| Kata rig | frozen + restamp-proven; `kernel/corpus/kata/workload.json` holds **12 PLACEHOLDER instances** — 4× `greenfield-tdd`, 4× `legacy-refactor`, 4× `seeded-bugfix` (`protected_tests: true`). (`kernel/docs/kata-seam.md` names a stale path `kernel/catalog/kata-workload.json` — the real input is `kernel/corpus/kata/workload.json`, per Appendix A's proven command) |
| o7 location fact | per the accepted 2026-08-09 AGENTS.md research: **o7 is a module in the spine repo, not a greenfield repo** — item E1's trigger phrasing reflects this. o7 spec sign-off gate still OPEN; ADR 0016 still Proposed (owner actions) |
| Live rig | preserved at `../evals/live-rig-2026-08-09.py` — the exact script that produced `live-full-001` (workspace builder, projection-derived agents JSON, babysitter with ledger tail + timeout). Fresh sessions adapt it; do not rebuild from scratch |
| Version control | **no git in this workspace** — before editing any kernel/validator file, copy it to the session scratchpad first (that was the only rollback path all day) |

Session-start baseline (run from `tooling/sdd-roles/`; all must be green
before any change):

```bash
.venv/bin/contract-lint selftest --kernel kernel          # exit 0, 20/0
python3 tools/ir-gate-checker/ir_gate_checker.py selftest # 8 cases, pass
.venv/bin/contract-lint validate configs/o7 --kernel kernel  # exit 0
.venv/bin/pip show sdd-roles-validator | grep Version     # 0.7.2
python3 -c "import json; print(json.load(open('kernel/corpus/kata/plan.json'))['stamp'])"
#   -> must print: sdd-roles 1.4.0 kata:26b8f03465ba  (until item 3 restamps it)
```

## 2. Discipline invariants

Invariants 1–8 of [next-items-plan.md](next-items-plan.md) §2 carry over
verbatim (green-after ×2; atomic vocabulary changes; registry bytes pinned
by the kata plan; catalog changes regenerate projections; kernel
neutrality; equipment outside the kernel; corpus tax for new checks; dated
ADR amendments). Today added four:

9. **Probe fidelity:** any probe claiming to be "runner-faithful" must
   byte-match the runner's mechanics (regexes, fill, cwd, direct-exec).
   The Appendix C probe passed with a wider token regex than the runner's
   and masked a real bug for half a day.
10. **Contract text = validator law, verbatim.** Text delivered to live
    roles (descriptor composite, task binds) must state the checks'
    actual rules — every approximation costs one full live attempt
    (empty `rejected_alternatives`, then an empty `decisions` array).
11. **Descriptor edits regenerate stamps.** The projection stamp hashes
    the descriptor ROW — any `command_template` change requires the
    six-regen procedure (Appendix B) + selftest ×2. Iterating contract
    text is cheap but never free.
12. **Live evidence is committed evidence.** Every live run worth
    mentioning gets its ledger + handoffs + key artifacts copied into
    `docs/skills/sdd-roles/evals/` with sha256 digests before the
    scratchpad vanishes. Scratchpad-only proof is no proof.

## 3. The items

Recommended order: **0 → 1 → 2 → 3 → 4 → STOP (owner budget gate) → 5**,
with E1/E2 event-driven and E3 environment-driven. Items 1 and 2 are
independent and can run as parallel sessions; item 3 must follow 2 in the
same session it lands (restamp discipline).

### Item 0 — session baseline (10 min, every session)

Run the §1 baseline block. Any red → stop and fix before proceeding (the
2026-08-09 sessions began green twice; keep the streak).

### Item 1 — live write-guard leg (mount hooks, prove a live block)

**Context.** The conveyor's D7 protection fired live via BETWEEN-RUN
validation (CHK-SCOPE caught maker3 modifying a protected test — after
the fact). The PRE-WRITE hook layer (`write-guard decide` behind
`gate-wrap`, mounted per the descriptor `hooks` row at
`.claude/settings.json`) has never intercepted a live model. The mount
machinery exists: `write-guard mount` (see the kernel skill card's console
scripts) and `mounts.py` fill the hook `command_template` per role.

**Work.**
1. Extend the rig's workspace builder: after building the workspace, run
   `write-guard mount` for the claude-code harness so the PreToolUse hook
   lands in `.claude/settings.json` (absolute paths for `gate-wrap`
   /`write-guard` via `.venv/bin/…` — the CLI subprocess inherits no venv).
2. Verify the mounted hook fires at all: a scripted (non-LLM) probe that
   invokes the hook command with a protected-path payload and asserts the
   descriptor exit map (allow → 0, block → 2).
3. Live adversarial stage: arm B on a scratch workspace, task
   deliberately instructing maker3 to "fix" an existing test file (the
   exact overreach D7 caught post-hoc on 2026-08-09). Expect: the hook
   BLOCKS the write in-flight, the model adapts or reports, the stage
   completes without the tamper, and the run validates.
4. Record as probe-report **Part 3** with evidence (ledger, the block
   decision, hook config digest). Close the "live hook mounting" open
   thread only if the block actually fired live.

**Acceptance:** a live in-flight block decision on a protected path,
recorded with evidence; run remains valid; selftest 20/0 ×2 (no kernel
bytes change in this item — it is workspace enablement + rig work).

### Item 2 — build the 12 real kata workspaces

**Context.** `kernel/corpus/kata/workload.json` fixes the shape: 4×
greenfield-tdd, 4× legacy-refactor, 4× seeded-bugfix (protected). The
seam doc names the canon sources: Mars Rover and Bank OCR (greenfield);
Gilded Rose and Trivia (legacy); the builder session picks the remaining
2+2 classics and the 4 seeded-defect instances, and records the choices.

**Layout.** `tooling/sdd-roles/kata-workspaces/<instance_id>/` (equipment
land, outside `kernel/`). EVERY workspace carries the full
`configs/o7/README.md` layout — the parts that are easy to forget:
- `ir/testcase-ir.json` + `ir/locator-manifest.json` **sealed**
  (`ir_gate_checker.py seal`) — maker3/checker3/coder/qa/solo declare
  `ir-gate`, so every gated run needs them;
- `.specify/memory/constitution.md`, `specs/`, `.sdd-roles/ledger/`;
- `.claude/skills/sdd-roles/SKILL.md` (projection copy) +
  `.claude/settings.json` permissions (the rig shows both);
- family-appropriate `src/**` + `src/test/**` (greenfield: compiling
  skeleton, no/empty suite — the CONVEYOR writes the tests; legacy:
  the kata's full tangled source + its characterization suite;
  seeded-bugfix: a green module with a deliberately seeded defect and
  the suite that SHOULD catch it, `tests` write-protected);
- Maven pom on the proven fixture template (release 11, surefire 3.2.5,
  JUnit 4.13.2 — see any `tools/*/fixtures/green/workspace/pom.xml`).

**Baseline gate states per family must be documented** in a README next
to the workspaces (e.g. greenfield: build green, tests vacuous-red by
design until the conveyor writes them; legacy: build+tests green, crap
red-by-design where the kata is famously CRAP-heavy; seeded-bugfix:
build green, tests red on the seeded defect). These baselines are what
the study's `first_attempt_pass` metrics mean — write them down before
any live run.

**Acceptance:** 12 workspace dirs; each passes a scripted layout lint
(all required paths present, IR seal verifies, pom compiles where the
family says it must); baselines README committed; no kernel bytes
touched; selftest 20/0 ×2.

### Item 3 — workload swap + kata restamp (same session as item 2's finish)

Replace the 12 `PLACEHOLDER-*` `source_kata` values with the real kata
ids (family structure and instance ids stay EXACTLY as-is), then run the
**extended Appendix A restamp** — the workload is a `kata plan` input, so
the plan stamp changes and every stamp-carrying golden follows. Also fix
the stale path line in `kernel/docs/kata-seam.md`
(`kernel/catalog/kata-workload.json` → `kernel/corpus/kata/workload.json`)
as a dated note, same edit.

**Acceptance:** `kata plan` regenerated; stamp literal swapped in the 8
results files + `failures/results-inconsistent/results.json` (tamper
fixture stays doctored at `kata:000000000000`); 8 verdicts + scorecard
regenerated; tamper verdict still `winner none / tamper-invalid`;
`PREREG_CONSTANTS` untouched; selftest 20/0 ×2.

### Item 4 — pilot cell + budget estimate (HARD STOP for owner approval)

**One cell, live:** greenfield-1 × arm B × 1 rep through the rig (adapted
to the kata workspace). This validates workspaces + workload + rig
end-to-end before any real spend, and produces the numbers the budget
decision needs:
- wall-clock per stage from the ledger `ts` deltas (2026-08-09 reference:
  specifier ~110 s, maker3 ~190 s incl. four gates; full arm ~7–8 min);
- tokens per stage from the harness transcript files (the headless CLI
  writes them under the harness's own project dir) — parse usage, do NOT
  touch the descriptor to add output flags;
- retry/rework overhead observed (contract-debug attempts averaged 3
  extra runs on day one; steady-state should be near zero — measure it).

Extrapolate to the 60-cell single-arm acceptance target AND the full
240-cell §6 experiment. **Present both to the owner and STOP.** Item 5
runs only on an explicit budget go.

### Item 5 — the kata study (owner-gated by item 4's budget approval)

Execute per `kernel/docs/kata-seam.md`, with one recorded deviation: no
git in this workspace, so cell isolation is **copy-per-cell** (fresh copy
of the kata workspace per cell into scratch, like the rig does) instead
of `git worktree add`. For `seeded-bugfix` cells, mount the write-guard
(item 1's product) so `tests/` is protected — that family's D7 leg is
the point.

Hard rules restated: metrics extracted ONLY from run-dir + ledger
(`provenance: "tool_output"`, `evidence_ref` with sha256 into the
committed run); mutation score as integer [0,10000]; `plan_stamp` +
`prereg_digest` from the (restamped) plan; `kata analyze` over the
observations IS the decision; `PREREG_CONSTANTS` never touched; a cell
that fails to complete is recorded as its gate outcomes say, never
hand-patched.

**Acceptance:** schema-valid `kata_results` for ≥ 1 full arm (60 cells)
from real runs; `kata analyze` exit 0 and its verdict committed to the
evals bundle; scorecard rendered; honest ledger of any skipped/failed
cells.

### Item E1 (event-driven) — T05 schema reconciliation

**Trigger (updated for the accepted o7-location research):** the o7
module exists **in the spine repo** with its T05-regenerated `TestCaseIR`
JSON Schema. Upstream owner actions, do not self-trigger: o7 spec
sign-off (gate OPEN), ADR 0016 (Proposed). Work when triggered: diff the
tool's `o7-spec-derived.1` contract against T05; every divergence is a
dated ADR 0005 amendment; bump the tool contract string, reseal fixtures,
regenerate goldens, tool selftest ×2.

### Item E2 (event-driven) — future gate ids

`ir-conformance` / `fitness` / `device-walk` stay separate ids (ADR 0005)
and each follows the full invariant-2 playbook with its own ADR.
`ir-conformance` spec-side corpus authoring starts **after the o7 spec is
signed off** (deliberately not before — a conformance corpus derived from
draft law would inherit its churn). `fitness` needs the o7 module;
`device-walk` needs the device pool.

### Item E3 (environment-driven) — copilot / cursor live legs

Each session, re-probe: `which copilot`, `which agent cursor-agent
cursor`, `gh copilot --version`. The descriptor rows already carry the
ADR 0006 contract. When a CLI appears: verify its flag semantics against
the row (the claude-code `--agents`-takes-JSON lesson), drive ONE live
stage via the rig, record in the probe report, and only then close that
leg's [D] risk. Until then the legs stay open on CLI absence — nothing
is substituted.

## Appendix A — kata restamp, workload-change variant (extends the old plan's Appendix A)

Same session as the workload (or any registry) edit, no exceptions:

```bash
cd tooling/sdd-roles
K=kernel/corpus/kata
OLD=$(python3 -c "import json; print(json.load(open('$K/plan.json'))['stamp'])")
.venv/bin/kata plan --kernel kernel --registry kernel/catalog/role-registry.json \
  --prereg $K/preregistration.json --workload $K/workload.json \
  --reps 5 --default-model UNBOUND --out $K/plan.json
NEW=$(python3 -c "import json; print(json.load(open('$K/plan.json'))['stamp'])")
# exact-literal swap OLD->NEW in: the 8 results-*.json AND
# failures/results-inconsistent/results.json (each contains it exactly once);
# failures/stamp-mismatch is doctored (kata:000000000000) — must NOT be touched.
for b in six-roles three-roles gates-not-roles tamper solo btok-fail conj-ia-only conj-margin-fail; do
  .venv/bin/kata analyze --kernel kernel --plan $K/plan.json --prereg $K/preregistration.json \
    --results $K/results-$b.json --out $K/verdict-$b.json
done
.venv/bin/kata report --kernel kernel --verdict $K/verdict-six-roles.json --out $K/scorecard.md
```

Confirm after: tamper verdict still `winner none / tamper-invalid`;
`PREREG_CONSTANTS` untouched; selftest 20/0 ×2.

## Appendix B — the six-regen procedure (after ANY descriptor or catalog edit)

The projection stamp hashes registry + bodies + the descriptor row, so a
descriptor edit regenerates BOTH golden sets (proven 2026-08-09, three
times):

```bash
cd tooling/sdd-roles
for h in claude-code copilot cursor; do
  .venv/bin/role-emit project --kernel kernel \
    --descriptors kernel/descriptors/invocation-descriptors.json --harness $h \
    --registry kernel/corpus/emitter/common/role-registry.json \
    --bodies kernel/corpus/emitter/common/bodies \
    --out kernel/corpus/emitter/$h
  .venv/bin/role-emit project --kernel kernel \
    --descriptors kernel/descriptors/invocation-descriptors.json --harness $h \
    --registry kernel/catalog/role-registry.json --bodies kernel/catalog/bodies \
    --out kernel/corpus/catalog-projections/$h
done
# then: contract-lint selftest x2, byte-identical, 20/0
```

## Appendix C — the live rig (proven parameters of live-full-001)

Script: `../evals/live-rig-2026-08-09.py` (copy into the session
scratchpad, adapt, run — do not edit the committed copy; it is the record
of the green run). What it encodes:

- **Workspace builder:** specs/, `.sdd-roles/ledger/`, `.specify` +
  constitution, green Maven module + sealed IR pair, kernel skill card at
  `.claude/skills/sdd-roles/SKILL.md`, `.claude/settings.json` with
  `permissions.allow: [Read, Write, Edit, Glob, Grep]`.
- **Agents bind:** `--agents` gets inline JSON built verbatim from the
  committed projection cards (description from front matter, body as
  prompt) for ALL arm roles — the bind is static per-run.
- **Binds:** `python`, `sdd_roles_root`, the four Java tool paths,
  `agents_file`, and `args` (REQUIRED — the stage task; state validator
  laws verbatim in any instruction that touches decisions/writes).
- **Babysitter:** Popen with `start_new_session=True`, 2 s ledger tail,
  per-event prints, timeout (900 s full-arm), SIGTERM on scope limit;
  ledger is append-only and resume-safe at any kill point.
- **Observed timings (green run):** specifier passed t≈114 s; maker3
  passed t≈304 s (four gates); full arm exit 0 in ≈ 7–8 min.
- **Failure modes already seen (do not re-diagnose from scratch):**
  literal `{token}` in argv → bind missing or (pre-0.7.2) digit-token
  bug; CHK-SCOPE red → model modified a protected test (D7 — adds
  exempt, mods refused); CHK-DECISIONS red → decision law text imprecise
  (≥1 decision per completed handoff; non-empty `rejected_alternatives`
  or the `alternatives_considered: none` sentinel + rationale).
