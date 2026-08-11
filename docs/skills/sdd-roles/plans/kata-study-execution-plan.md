---
type: plan
title: sdd-roles / o7 — kata study execution plan (post pilot-cell green)
description: >-
  Cold-session-executable plan for everything still open after the 2026-08-09
  third session, which closed items 0–4 of the live-leg plan (live write-guard
  block, 12 kata workspaces, workload restamp, and a fully-green pilot kata
  cell). What remains: two blocking owner decisions (D1 guard-vs-ADR-0006,
  D2 unpinned study model), one optional fidelity fix (D3), one mechanical
  prerequisite (P1 per-arm configs), the kata study itself (item 5, budget
  gated), and the unchanged event/environment-driven seams. Supersedes
  live-leg-and-kata-study-plan.md for open work; that file remains the record
  of items 0–4.
date: 2026-08-09
status: open
supersedes: live-leg-and-kata-study-plan.md
adr_0005: ../../../architecture/adrs/tooling/sdd-roles/0005-ir-gate-first-class-gate-vocabulary.md
adr_0006: ../../../architecture/adrs/tooling/sdd-roles/0006-live-invocation-runner-contract-channel.md
probe_report: ../evals/live-leg-probe-report.md
seam_doc: ../../../../tooling/sdd-roles/kernel/docs/kata-seam.md
tags: [sdd-roles, o7, plan, kata, study, owner-decision, budget]
---

# Kata study execution plan (written 2026-08-09, end of third session)

Everything below assumes **no memory of prior sessions**. §1 is the
world-state; §2 the invariants; §3 the items in execution order; the
appendices hold the proven procedures, the rigs, and the metric-extraction
map item 5 needs.

**The short version:** the machine works end to end. A real kata cell ran
green with zero rework. What is left is not engineering discovery — it is
two decisions the owner must make, one mechanical prerequisite, and then
spending the budget.

---

## 1. State snapshot (verified 2026-08-09, end of third session)

All paths relative to `tooling/sdd-roles/` unless rooted.

| Surface | State |
|---|---|
| Kernel / validator | schema 1.4.0 / validator **0.7.2**; `contract-lint selftest` **20/0 ×2 byte-identical**; `contract-lint validate configs/o7` **29/0** |
| Stamps (both moved this session) | kata plan **`kata:73fca8cae0f6`** (was `26b8f03465ba` — real workload landed); projection **`catalog:1d520797652a`** (was `b2b1edd94ec0` — ADR 0006 clause fix) |
| Gate tools | all five built and **row-proven live**: `tools/{ir-gate-checker,javac-build,junit-runner,crap4java,mutate4java}/`. All seven gate executions of the pilot cell green on attempt 1 |
| Kata workspaces | **BUILT** — `kata-workspaces/` holds all 12 instances, generated (not hand-maintained) by `build_workspaces.py` from `_sources_{greenfield,legacy,bugfix}.py`; `lint_workspaces.py` is the layout gate, `--gates` additionally runs the real build/tests tools. All 24 baselines verified. Provenance + per-family baseline table: `kata-workspaces/README.md` |
| Workload | **REAL** — `kernel/corpus/kata/workload.json` carries the 12 real `source_kata` ids (mars-rover, bank-ocr, roman-numerals, bowling-game / gilded-rose, trivia, tennis-refactoring, yatzy / date-range-overlap, rpn-calculator, word-wrap, shopping-cart-discount). Family structure, ids and `protected_tests` unchanged from the pre-registered placeholder |
| Live conveyor | **proven twice**: `live-full-001` (synthetic module) and `pilot-greenfield-1-armB-r1` (real kata workspace, exit 0, 7/7 gates attempt 1, `mutation_score 1.0`, 1587 s) |
| Live write-guard | mount + adapter + **first live in-flight block** proven (`live-hooks-001`). **But hook-mounted runs cannot complete a stage** — see item D1 |
| Harness CLIs | `claude` 2.1.185 present. `copilot`, `cursor`/`agent`/`cursor-agent` **absent** → R-COPILOT-LIVE / R-CURSOR-LEG open on CLI absence alone |
| Measured cost | **$4.80/cell** (Sonnet 4.6, what ran) / **$8.00/cell** (Opus 5). 60 cells $288/$480 · 240 cells $1,152/$1,920. 26.4 h / 105.8 h serial |
| Evidence bundles | `../evals/evidence-live-hooks-001/` (hooks leg + all four rig scripts), `../evals/evidence-pilot-greenfield-1/` (pilot ledger, handoffs, 7 gate reports, spec, final src, `pilot_cell.py`, `budget.py`), `../evals/evidence-live-full-001/` (earlier). Each has `SHA256SUMS.txt` |
| Version control | **no git in this workspace** — before editing any kernel/validator file, copy it to the session scratchpad first. The kata workspaces are regenerable instead (that IS their rollback path) |

Session-start baseline (run from `tooling/sdd-roles/`; all must be green
before any change):

```bash
.venv/bin/contract-lint selftest --kernel kernel          # exit 0, 20/0
python3 tools/ir-gate-checker/ir_gate_checker.py selftest # 8 cases, pass
.venv/bin/contract-lint validate configs/o7 --kernel kernel  # exit 0, 29/0
python3 kata-workspaces/lint_workspaces.py                # lint: clean
.venv/bin/pip show sdd-roles-validator | grep Version     # 0.7.2
python3 -c "import json; print(json.load(open('kernel/corpus/kata/plan.json'))['stamp'])"
#   -> sdd-roles 1.4.0 kata:73fca8cae0f6   (until D2 restamps it)
grep -m1 'stamp:' kernel/corpus/catalog-projections/claude-code/agents/specifier.md
#   -> sdd-roles 1.4.0 catalog:1d520797652a  (until D1/D2 regenerate it)
```

## 2. Discipline invariants

Invariants 1–12 of [live-leg-and-kata-study-plan.md](live-leg-and-kata-study-plan.md)
§2 carry over verbatim (green-after ×2; atomic vocabulary changes; registry
bytes pinned by the kata plan; catalog changes regenerate projections; kernel
neutrality; equipment outside the kernel; corpus tax for new checks; dated ADR
amendments; probe fidelity; contract text = validator law verbatim; descriptor
edits regenerate stamps; live evidence is committed evidence). This session
added three:

13. **Contract text must state the law at the granularity it is enforced
    at** — including *element types*, not just container shapes. Three data
    points now: which decisions are required, when, and (this session) that
    `rejected_alternatives` items are plain strings. Each approximation costs
    exactly one live attempt.
14. **Baselines are measured, never asserted.** The 12 workspace baselines
    are green only because `lint_workspaces.py --gates` ran the real
    `javac-build` and `junit-runner` against every instance. A documented
    baseline that has not been executed is a claim, not a baseline. (It
    caught a genuine error: two wrong assertions in the Yatzy suite.)
15. **A watcher must not match itself.** `until ! pgrep -f "foo.py"` never
    terminates when the watcher's own command line contains `foo.py` — three
    such loops span for the rest of the session and suppressed the very
    notifications they existed to deliver. Use `pgrep -f "[f]oo.py"`, or
    watch for the artifact the job produces rather than its process name.

## 3. The items

Recommended order: **0 → D1 → D2 → (D3) → P1 → STOP (owner budget gate) → 5**,
with E1/E2 event-driven and E3 environment-driven. D1 and D2 are independent
of each other and can run as parallel sessions; both must land before item 5.

### Item 0 — session baseline (10 min, every session)

Run the §1 baseline block. Any red → stop and fix before proceeding.

---

### Item D1 — OWNER DECISION: the guard forbids the handoff ADR 0006 requires

**The contradiction.** Two accepted laws are in direct conflict:

- **ADR 0006 / the runner contract** (in every descriptor row's composite
  prompt, enforced at `runner.py:487`): every role must write
  `<run_dir>/handoff.draft` or its stage fails.
- **The D7 guard law**, pinned by guard corpus case
  `kernel/corpus/guard/decisions/writer-only-run-dir/`: any role write into
  the run directory is `block WRITER_ONLY` ("only the gate-runner writes the
  run directory and ledger"). When the run dir sits outside the workspace,
  `REPO_SCOPE` fires first — same outcome.

Proven both on the bench (scripted probe case 13) and live (`live-hooks-001`:
the write was blocked at t=106 s and the run died with "wrote no handoff
draft"). It was invisible until now because the retro `chk_scope` lint
resolves writes from the runner's **workspace** scan, and the run dir is not
in the workspace — so retro enforcement never saw the draft at all, while
live enforcement intercepts by path and does.

**Consequence:** mounting the write-guard kills every stage of every run at
stage one. That blocks the `seeded-bugfix` family (4 of 12 instances, which
the seam doc specifies must mount the guard) and item 5's whole D7 leg.

**Recommended resolution.** Amend the guard so the **current stage role may
create or modify exactly `<run_dir>/handoff.draft` and nothing else in the
run directory**. Narrowest possible carve-out: one filename, one directory,
still blocking the ledger, reports, and every other run-dir path.

**Work, if the owner approves:**
1. Dated ADR amendment — on ADR 0006 (it introduced the obligation without
   reconciling the guard) or a new ADR; the owner's call which.
2. `validator/src/sdd_roles_validator/guard.py`: in `_evaluate`, permit the
   single exempt path before the `WRITER_ONLY` raise; `_contained_rel` must
   also stop rejecting it when the run dir is outside the workspace.
3. **Corpus tax** (invariant 7): add guard decision cases under
   `kernel/corpus/guard/decisions/` — at minimum `handoff-draft-allow` (the
   exempt write) and `run-dir-other-block` (a *different* run-dir path still
   blocked), and bump `GUARD_DECISION_CASES` in `selftest.py` from 23.
4. Selftest 20/0 ×2 byte-identical.
5. Re-run the item-1 rig end to end (Appendix C) and confirm a hook-mounted
   arm-B run now completes — that is the acceptance, not the unit cases.

**Acceptance:** a hook-mounted live run reaches `passed` on every stage with
the guard still blocking protected tests; selftest 20/0 ×2; ADR amended.

**Do not proceed without the owner.** This widens the D7 floor, which is the
project's core safety property.

---

### Item D2 — OWNER DECISION: the study model is not pinned

**The problem.** The pilot ran on `claude-sonnet-4-6`. Nothing in the kernel
chose that: the catalog registry sets `invocation.model: "UNBOUND"`, the
plan is generated `--default-model UNBOUND`, the claude-code descriptor row
carries **no model flag at all**, so the harness fell back to the operator's
CLI setting (`opusplan` → Sonnet for execution). The resolved model is not
recorded anywhere in the run.

For an arm-comparison study this is a validity threat: two cells run on
different machines or days are not comparable, and nothing in the record
would reveal it. The ledger's `harness` object pins the *agent definition*
digest, not the model.

**Two mechanisms — recommend (a).**

**(a) Pin it in the registry (recommended).** Set `invocation.model` to a
real model id for all 9 roles in `kernel/catalog/role-registry.json`, and add
`--model {model}` to the claude-code `command_template`. The runner already
resolves `{model}` from `role.invocation` (`_invoke_role` merges
`role["invocation"]` into the fill map), and `render_plan` already copies
`invocation.model` into every cell's `bindings[]`. So the model lands in the
plan, in the stamp, and in the command — the digest triangle then encodes it,
which is what a pre-registered study wants.

*Tax:* registry bytes change → **kata restamp** (Appendix A) **and**
six-regen (Appendix B), plus `kata plan --default-model <the same id>`.
Both stamps move. Roughly one focused session.

**(b) Bind it at run time (lighter, weaker).** Add a *new* token (e.g.
`--model {run_model}`) to the descriptor and bind `--bind run_model=…` per
run. Descriptor change → six-regen only, no registry change, no restamp.
But the model then lives outside the pinned record and must be captured
per-cell in evidence instead.

> ⚠️ Do **not** try to bind the existing `{model}` token via `--bind`:
> `_fill` does `fill = dict(self.binds); fill.update(extra)`, and `extra`
> carries `invocation.model`, so the registry value **overrides** any
> `--bind model=…`. Silent, and exactly the kind of thing that produces a
> wrong study.

**Also decide which model the study runs on.** The budget differs by 1.67×
(Sonnet vs Opus 5). This is a scientific choice as much as a cost one —
whichever is chosen, every cell must use it.

**Acceptance:** every cell's resolved model is visible in `plan.json`
`bindings[].model` and in the live command line; a one-stage live smoke
confirms the flag is accepted by the CLI; selftest 20/0 ×2; restamp
verified per Appendix A.

---

### Item D3 (optional) — a blocked model is told nothing useful

`gate-wrap` runs the guard with `capture_output=True` (`gate_wrap.py:67`) and
emits only the mapped decision word, so the guard's actual block **code**
(`TESTS_PROTECTED`, `PROTECTED`, `SCOPE`, `WRITER_ONLY`) and detail never
reach the harness. Claude Code surfaces a PreToolUse hook's **stderr** to the
model as the blocking reason — so the model is refused with no reason.

The item-1 adapter papers over this with a generic, clearly adapter-authored
reason. Forwarding the guard's real stderr means changing `gate-wrap`, which
owns a selftest corpus section (`gatewrap-corpus`) — hence a separate item.

**Judgement:** cosmetic for correctness (the block fires either way), but it
directly shapes what a live model does *after* a refusal, which the study
measures via `tamper_events`. Worth doing before item 5 if D1 is being done
anyway; skippable otherwise. Record the decision either way.

---

### Item P1 — per-arm kernel configs (mechanical prerequisite for item 5)

`Runner` selects the stage sequence from `config["arm"]`
(`runner.py:131-135`), and `configs/o7/kernel-config.json` is **arm B only**.
The study needs all four arms: `A` (solo), `B` (specifier→maker3→checker3),
`C` (6 roles), `C-dbg` (5 roles, diagnostic-debug ablation).

**Work.** Create `configs/o7-arm-a/`, `configs/o7-arm-c/`,
`configs/o7-arm-c-dbg/` (or a single directory with four config files —
either is fine, it is equipment). Each is a byte-copy of
`configs/o7/kernel-config.json` with the one `"arm"` field changed; the
sibling `speckit-mapping.json` travels with each (the runner copies both into
the run dir at genesis). The gate rows already cover every arm — their gate
unions are identical, which is why only that one field moves.

**Acceptance:** `contract-lint validate <each config dir> --kernel kernel`
exits 0; a dry `gate-runner run` on a throwaway workspace resolves the right
role sequence for each arm.

---

### Item 4-STOP — the budget gate (owner)

Numbers are measured and in hand (§1 and probe report Part 4). **Item 5 runs
only on an explicit owner go**, and only after D1 + D2 land. Re-present:

| Model | $/cell | 60 cells (1 arm) | 240 cells (full §6) |
|---|---:|---:|---:|
| Sonnet 4.6 / Sonnet 5 std | 4.80 | 288 | 1,152 |
| Sonnet 5 (intro, to 2026-08-31) | 3.20 | 192 | 768 |
| Opus 5 | 8.00 | 480 | 1,920 |

Wall clock 26.4 h / 105.8 h serial; cells are independent so this
parallelises. **Floor, not a mean** — the pilot cell needed zero rework;
legacy (CRAP-red by design) and seeded-bugfix (tests red + guard mounted)
families will cost more, and any cell that burns retries costs more again.

---

### Item 5 — the kata study (owner-gated on the budget above)

Execute per [`kernel/docs/kata-seam.md`](../../../../tooling/sdd-roles/kernel/docs/kata-seam.md),
with two recorded deviations:

- **Cell isolation is copy-per-cell**, not `git worktree add` — no git in
  this workspace. `pilot_cell.py` already does exactly this
  (`shutil.copytree` of `kata-workspaces/<instance>` into scratch).
- **The write-guard is mounted only for `seeded-bugfix` cells** (that
  family's D7 leg is the point) — and only once D1 has landed.

**Procedure per cell**, in `cell_id` order from `plan.json`:

1. Copy `kata-workspaces/<instance>` to a fresh scratch dir.
2. Run `gate-runner run` with the arm's config (item P1), the committed
   registry/descriptors, `--harness claude-code`, the six gate binds, and
   `--bind args=<the task text for that instance>`.
3. Extract the eight metrics into one `cell_result` — **Appendix D** is the
   field-by-field map.
4. Append to `kata_results.observations`.

Then:

```bash
K=kernel/corpus/kata
.venv/bin/kata analyze --kernel kernel --plan $K/plan.json \
  --prereg $K/preregistration.json --results <kata_results.json> --out <verdict.json>
.venv/bin/kata report --kernel kernel --verdict <verdict.json> --out <scorecard.md>
```

**Hard rules restated:** metrics come ONLY from run-dir + ledger
(`provenance: "tool_output"` — the analyzer refuses any other value);
`mutation_score` and every rate are integers on [0,10000] (**no floats**);
`plan_stamp` + `prereg_digest` copied from the plan; `observations` must
biject the plan's `cells` exactly; `PREREG_CONSTANTS` is never touched; a
cell that fails to complete is recorded as its gate outcomes say, **never
hand-patched**. `analyze` is fail-closed — any stamp/digest mismatch,
missing or extra cell, or `final_all_gates_pass` inconsistency exits 2 and
writes nothing.

**Residual trust edge (ADR 0004, unchanged):** `analyze` verifies
`provenance` and that `evidence_ref` is well-formed, but does **not**
re-verify that the `evidence_ref` sha256 chains into the ledger. That is a
seam obligation checked at real-run time — do it, and say so in the report.

**Acceptance:** schema-valid `kata_results` for ≥ 1 full arm (60 cells) from
real runs; `kata analyze` exit 0 with the verdict committed to the evals
bundle; scorecard rendered; an honest ledger of any skipped or failed cells.

---

### Item E1 (event-driven) — T05 schema reconciliation

**Trigger:** the o7 module exists **in the spine repo** with its
T05-regenerated `TestCaseIR` JSON Schema. Upstream owner actions, do not
self-trigger: o7 spec sign-off (gate OPEN), ADR 0016 (Proposed). Work when
triggered: diff the tool's `o7-spec-derived.1` contract against T05; every
divergence is a dated ADR 0005 amendment; bump the tool contract string,
reseal fixtures, regenerate goldens, tool selftest ×2. **Note:** all 12 kata
workspaces carry the same sealed IR pair as a deliberate constant — a
contract bump means regenerating all 12 (`build_workspaces.py`, then
`lint_workspaces.py`).

### Item E2 (event-driven) — future gate ids

`ir-conformance` / `fitness` / `device-walk` stay separate ids (ADR 0005) and
each follows the full invariant-2 playbook with its own ADR.
`ir-conformance` corpus authoring starts **after** the o7 spec is signed off;
`fitness` needs the o7 module; `device-walk` needs the device pool.

### Item E3 (environment-driven) — copilot / cursor live legs

Each session re-probe: `which copilot`, `which agent cursor-agent cursor`,
`gh copilot --version`. Re-probed 2026-08-09: **all still absent**. The rows
already carry the ADR 0006 contract. When a CLI appears: verify its flag
semantics against the row (the claude-code `--agents`-takes-JSON lesson),
drive ONE live stage via the rig, record in the probe report, and only then
close that leg's [D] risk.

---

## Appendix A — kata restamp (run in the same session as any registry or workload edit)

```bash
cd tooling/sdd-roles
K=kernel/corpus/kata
OLD=$(python3 -c "import json; print(json.load(open('$K/plan.json'))['stamp'])")
.venv/bin/kata plan --kernel kernel --registry kernel/catalog/role-registry.json \
  --prereg $K/preregistration.json --workload $K/workload.json \
  --reps 5 --default-model <MODEL> --out $K/plan.json
NEW=$(python3 -c "import json; print(json.load(open('$K/plan.json'))['stamp'])")
# exact-literal swap OLD->NEW in the 8 results-*.json AND
# failures/results-inconsistent/results.json (each contains it exactly once).
# failures/stamp-mismatch is DOCTORED (kata:000000000000) — must NOT be touched.
for b in six-roles three-roles gates-not-roles tamper solo btok-fail conj-ia-only conj-margin-fail; do
  .venv/bin/kata analyze --kernel kernel --plan $K/plan.json --prereg $K/preregistration.json \
    --results $K/results-$b.json --out $K/verdict-$b.json
done
.venv/bin/kata report --kernel kernel --verdict $K/verdict-six-roles.json --out $K/scorecard.md
```

Confirm after: tamper verdict still `winner none / tamper-invalid`;
`PREREG_CONSTANTS` untouched; `prereg_digest` unchanged; selftest 20/0 ×2.
(Proven twice — 2026-08-09 items 3 and D2's rehearsal.)

## Appendix B — the six-regen (after ANY descriptor or catalog edit)

The projection stamp hashes registry + bodies + the descriptor row, so either
kind of edit regenerates BOTH golden sets:

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
# then: contract-lint selftest x2 byte-identical, 20/0
python3 kata-workspaces/build_workspaces.py   # workspaces carry the skill card — restamp them
python3 kata-workspaces/lint_workspaces.py
```

**Do not hand-edit `invocation-descriptors.json` with a full-file rewrite** —
edit the three `command_template` strings only and diff against a backup to
confirm exactly three lines moved.

## Appendix C — the rigs (all committed, all proven)

Copy into the session scratchpad, adapt, run. Do not edit the committed
copies; they are the record of green runs.

| Script | In | What it does |
|---|---|---|
| `pilot_cell.py` | `../evals/evidence-pilot-greenfield-1/` | Copy-per-cell isolation + full arm-B run on a real kata workspace + per-stage timing and token extraction. **The item-5 cell runner starts here.** |
| `budget.py` | same | Per-model token/cost rollup from the harness transcripts, with the 60/240-cell extrapolation |
| `live_rig_hooks.py` | `../evals/evidence-live-hooks-001/` | Arm-B run with the write-guard mounted; babysitter kills after one stage |
| `hook_enablement.py` + `dispatch.py` | same | The mount adapter — stages the kernel artifact under `harness-settings/` (a `harness_enablement` protected root), binds machine tokens, resolves the current role from the ledger, projects onto claude-code's native `.claude/settings.json` |
| `probe_hook_mount.py` | same | 13-case scripted probe of the mounted hook against the descriptor exit map |
| `build_ws.py` | same | Synthetic-workspace builder (the pre-kata fixture module) |

**Observed timings (green pilot):** specifier 339 s, maker3 292 s (four
gates), checker3 955 s (mutation dominates), total 1587 s.

**Failure modes already seen — do not re-diagnose from scratch:**

- literal `{token}` in argv → bind missing (or, pre-0.7.2, the digit-token bug)
- `CHK-SCOPE` red → a role modified a protected test (D7; adds are exempt)
- `CHK-DECISIONS` red → decision-law text imprecise
- `CHK-SCHEMA` on `rejected_alternatives` → contract text omitted the item type
- role blocked writing `handoff.draft` → item D1, not a bug in the rig
- a `pgrep -f`-based watcher that never fires → invariant 15

## Appendix D — `cell_result` extraction map (item 5)

`kata_results` requires `schema_version`, `artifact_type`, `plan_stamp`,
`prereg_digest`, `observations`. Every `cell_result` requires **all** of:

| Field | Source | Notes |
|---|---|---|
| `cell_id`, `arm`, `instance`, `rep` | `plan.json` `cells[]` | copy verbatim; bijection is checked |
| `gates[]` | ledger `gate_run` entries | `{gate_id, first_attempt_pass, final_pass}` — first vs final attempt outcomes |
| `mutation_score` | `mutation` gate report | **integer [0,10000]** (0.86 → 8600). Pilot returned 1.0 → `10000` |
| `crap` | `crap` gate report | `{max, mean, over_threshold_count, per_method}` — all integers; `over_threshold_count` counts methods above CRAP ≤ 6 |
| `tokens` | harness transcripts | see `budget.py`; filter sessions by `first_ts >= run start` — the workspace path is reused across runs and stale sessions WILL be picked up otherwise |
| `wall_clock_ms` | ledger `ts` deltas | first to last entry |
| `handoff_schema_failures` | `contract-lint` on the stage handoffs | count |
| `tamper_events` | `write-guard` block decisions | count; `tamper_instance = tamper_events > 0`. Only meaningful once D1 lands and the guard is actually mounted |
| `final_all_gates_pass` | derived | true iff every `gates[].final_pass` — the analyzer re-checks this and refuses a mismatch |
| `provenance` | constant | always `"tool_output"` |
| `evidence_ref` | `{path, sha256}` | into the committed run; chain-verify it yourself (ADR 0004 residual edge) |

## Appendix E — operational notes for a fresh session

- **Live runs are slow and that is expected.** One arm-B cell is ~26 min of
  wall clock. Start it in the background, set **one** watcher, and do other
  work. Do not poll the output file repeatedly — it produces nothing and
  burns the session.
- **Watchers must not self-match** (invariant 15). Prefer waiting on the
  artifact: `until [ -f <run_dir>/handoff-*-011.json ]; do sleep 30; done`.
- **Maven is slow too.** `lint_workspaces.py --gates` is a build+test cycle
  across 12 workspaces (several minutes). The fast layout-only lint is the
  default and is what most changes need.
- **The harness model is whatever the operator's CLI says** until D2 lands —
  check `~/.claude/settings.json` `model` before trusting any live result.
