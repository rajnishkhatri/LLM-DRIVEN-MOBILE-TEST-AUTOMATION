---
type: plan
title: sdd-roles / o7 — next-items plan (post ir-gate landing)
description: >-
  Cold-session-executable plan for the remaining seams after the 2026-08-09
  ir-gate landing: the four Java gate tools, the live LLM harness leg, the
  kata study, T05 schema reconciliation, and the three future gate ids.
  Carries the full state snapshot, discipline invariants, proven commands,
  and the kata-restamp procedure.
date: 2026-08-09
status: superseded
superseded_by: live-leg-and-kata-study-plan.md
tags: [sdd-roles, o7, plan, ir-gate, kata, seams]
adr: ../../../architecture/adrs/tooling/sdd-roles/0005-ir-gate-first-class-gate-vocabulary.md
battle_test: sdd-roles battle-test report (Architect workspace eval artifact; not vendored here)
---

# Next-items plan — sdd-roles / o7 (written 2026-08-09)

> **SUPERSEDED (same day):** items 0–2 are done (see the two addenda
> below); all open work now lives in
> [live-leg-and-kata-study-plan.md](live-leg-and-kata-study-plan.md).
> This file remains the record of what was executed and how.

Everything below assumes **no memory of prior sessions**. Section 1 is the
world-state; section 2 the rules that must survive every change; section 3
the items; the appendix holds procedures that were hard-won and WILL be
needed again.

> **2026-08-09 addendum (later session, same day):** items 0–2 executed.
> **Item 1 DONE** — all four Java gate tools live under `tools/<tool-id>/`
> on the ir-gate-checker template (own fixture corpus + selftest ×2 green
> each; Appendix C row probes 8/8 OK; `configs/o7` byte-unchanged; kernel
> selftest 20/0 ×2 after). **Item 2 EXECUTED** — recorded in
> [`../evals/live-leg-probe-report.md`](../evals/live-leg-probe-report.md):
> first-ever live CLI drive THROUGH `gate-runner run` (claude-code 2.1.185;
> invocation + write-scope legs live and held), stage blocked at the
> handoff leg by a pinned gap — live command templates carry no `{run_dir}`
> channel (stub descriptors do), no doctrine body states the
> `handoff.draft` obligation, `{args}` is never substituted live, and
> `--agents` takes inline JSON on this CLI version. copilot/cursor CLIs
> still absent. **R-COPILOT-LIVE / R-CURSOR-LEG / the live-stage
> acceptance stay OPEN** pending a seam decision (one atomic
> invariant-2-shaped change: descriptor `command_template` amendment +
> doctrine line + projections regen, with a dated ADR 0005-style record).
> Item 5 is now gated on that seam decision, the missing harness CLIs, and
> the 12 kata workspaces — the equipment leg is no longer the blocker.

> **2026-08-09 addendum 2 (owner-directed, same day):** the seam decision
> EXECUTED as
> [ADR 0006](../../../architecture/adrs/tooling/sdd-roles/0006-live-invocation-runner-contract-channel.md)
> — the runner contract rides the live command templates; `{next_role}`
> fill key (validator 0.7.1) + token-regex digit fix (0.7.2, a latent
> runner bug found live: `{crap4java}`/`{mutate4java}` were unfillable);
> emitter + catalog goldens regenerated (stamp `b2b1edd94ec0`); selftest
> 20/0 ×2 at every step; registry bytes and the kata instrument untouched.
> **Item 2 acceptance MET** (one live stage green on claude-code) and
> exceeded: **first fully-green live conveyor run** — arm B end-to-end,
> exit 0, all seven gate executions green including live PIT mutation
> (run `live-full-001`; probe report Part 2 +
> `../evals/evidence-live-full-001/`). Along the way the D7
> test-write-protection and the decision law each refused a live model's
> overreach — the guards work in anger. Still open: R-COPILOT-LIVE /
> R-CURSOR-LEG (CLI absence only), live hook mounting, and item 5's
> remaining inputs (12 kata workspaces + model budget) — the kata study is
> otherwise unblocked.

---

## 1. State snapshot (verified 2026-08-09, end of session)

All paths relative to `tooling/sdd-roles/` unless rooted.

| Surface | State |
|---|---|
| Kernel / validator | schema 1.4.0 / validator **0.7.0**; `contract-lint selftest` **20 pass / 0 fail ×2 byte-identical**; **27** invalid families (newest: `CHK-IRGATE-PIN`) |
| ir-gate law | [ADR 0005](../../../architecture/adrs/tooling/sdd-roles/0005-ir-gate-first-class-gate-vocabulary.md) Accepted: gate id `ir-gate`; tool pinned to `ir-gate-checker`; threshold `ir_gate_violations_max: 0`; declarations coder/qa/maker3/checker3/solo (hardener recorded "no") |
| Checker tool | `tools/ir-gate-checker/ir_gate_checker.py` **1.0.0**, contract `o7-spec-derived.1`, stdlib-only; subcommands check/seal/selftest; exits 0/2/3; 8-case fixture corpus, own selftest 8/8; seven checks always run, fail-closed |
| Alias enforcement | `CHK-IRGATE-PIN` (validator `checks/config_registry.py`) reds any `ir-gate` binding whose tool ≠ `ir-gate-checker`, at KernelConfig-row AND gate-outcome layers; corpus cases `aliased-config`, `aliased-outcome` |
| Productive config | `configs/o7/kernel-config.json` (arm **B**; all five gate rows; machine paths as `--bind` tokens) + sibling `speckit-mapping.json` + README. Validates green; **all four arms pass gate-runner preflight** with it; the ir-gate row executes runner-style (green fixture → exit 0, red → exit 2) |
| Catalog / skills | registry declares ir-gate (5 roles); 5 doctrine bodies name it in stage-exit law; projections regenerated ×3 harnesses (claude-code 12, copilot 19, cursor 11 files) — Contract and Doctrine agree |
| Kata instrument | restamped as ADR-0004 amendment; plan stamp `sdd-roles 1.4.0 kata:26b8f03465ba`; 8 results + 8 verdicts + scorecard consistent; `PREREG_CONSTANTS` untouched; tamper branch still `winner none / tamper-invalid` |
| o7 spec | `docs/sdd/specs/mobile-test-automation-o7-interpreter.spec.md` — **DRAFT, sign-off gate OPEN** (owner action); ADR 0016 still Proposed. o7's Spring Boot repo (implementation home) does not exist in this workspace |

Proven session-start baseline commands (run from `tooling/sdd-roles/`):

```bash
.venv/bin/contract-lint selftest --kernel kernel          # expect exit 0, 20/0
python3 tools/ir-gate-checker/ir_gate_checker.py selftest # expect 8 cases, pass
.venv/bin/contract-lint validate configs/o7 --kernel kernel  # expect exit 0
```

## 2. Discipline invariants (non-negotiable, learned the hard way)

1. **Green-after:** every change ends with `contract-lint selftest` 20/0,
   run **twice**, summaries identical. A red gate means the change is
   half-applied — finish it or revert it, never leave it.
2. **Atomic vocabulary changes:** a new gate id ships as ONE change — ADR +
   registry declarations + tool + config row + corpus pin + doctrine bodies +
   projections regen + kata restamp. The registry-first sequencing reviewed
   in ADR 0005's context is the anti-pattern.
3. **Registry bytes are pinned by the kata plan.** ANY edit to
   `kernel/catalog/role-registry.json` invalidates the kata instrument —
   follow Appendix A, same session, or don't touch the registry.
4. **Catalog changes regenerate projections.** Registry or body edits change
   the catalog digest → all 42 projection files drift → run `role-emit
   project` ×3 (command in Appendix B) or the selftest `catalog` section
   goes red.
5. **Neutrality:** nothing under `kernel/` may contain the tokens
   `claude`, `cursor`, `copilot`, `anthropic` (see `kernel/neutral_tokens.json`).
   Plans/docs that must name harnesses (like this one) live OUTSIDE
   `kernel/` — this is why this file is here.
6. **Equipment stays outside the kernel.** Gate tools live in `tools/`
   (own fixtures + own selftest, ir-gate-checker is the template); they are
   NOT contract-lint sections and NOT console scripts of the validator.
7. **New validator checks pay the corpus tax:** CHECKS row + invalid family
   dir (bijection) + `expect.json` case(s) isolated to exactly that check +
   selftest arithmetic constant bump + validator version bump.
8. **ADR amendments are dated notes, never silent edits.** Fabricating
   nothing; deferred risks (battle-test [D]) stay open until the live thing
   actually ran.

## 3. The items

Recommended order: **0 → 1 ∥ 2 → 5**, with 3 and 4 event-driven. Items 1 and
2 are independent surfaces and can run as parallel sessions.

### Item 0 — session baseline + venv hygiene (10 min, do first every session)

Run the three baseline commands above. Also refresh the editable install's
stale metadata (source is live-read so behavior is already 0.7.0, but the
venv dist-info still says 0.6.0):

```bash
.venv/bin/pip install -e validator --no-build-isolation --no-deps
```

Acceptance: baselines green; `pip show sdd-roles-validator` reports 0.7.0.

### Item 1 — the four Java gate tools (R-KATA-STUDY equipment seam) — **DONE 2026-08-09**

**Context.** The `build`/`tests`/`crap`/`mutation` legs have canonical tool
ids (`javac-build`, `junit-runner`, `crap4java`, `mutate4java` — fixed in the
canon allowlist and `configs/o7`) but **no implementations**. Bind tokens
`{javac_build}` `{junit_runner}` `{crap4java}` `{mutate4java}` are reserved
in `configs/o7/kernel-config.json`. `kernel/docs/kata-seam.md` documents the
seam's obligations.

**Contract each tool must meet** (the runner refuses anything less):
- Writes a JSON report at `{report}` carrying a non-empty `tool_version`.
- Exit 0 green / non-zero red; report written on red too (fail-closed).
- Deterministic: same workspace bytes → same verdict; no clocks in output.
- Thresholds (from canon): `build_errors_max 0`, `tests_failures_max 0`,
  `crap_composite 6`, `mutation_score_min 0.85` — echo name+value in the
  report like ir-gate-checker does.

**Approach.** One directory per tool under `tools/`, following the
ir-gate-checker template exactly (single entry file, fixtures/, own
selftest, README with the binding row). Realistic engines: wrap
`mvn -q compile` (javac-build), `mvn -q test` + surefire XML parse
(junit-runner), JaCoCo coverage + cyclomatic complexity → CRAP score
(crap4java), PIT mutation testing → kill rate (mutate4java). Java toolchain
presence is an environment precondition — probe and fail with a clear exit-3
message when absent, never fake a report.

**Acceptance.**
- Each tool: own selftest green ×2 against committed fixtures (a tiny Java
  fixture project per tool; green + red case minimum).
- A `_run_gate`-style row execution per tool (Appendix C pattern) green and
  red.
- `configs/o7` unchanged (rows already bind these ids); contract-lint
  selftest still 20/0 (equipment adds nothing kernel-side).

### Item 2 — live LLM harness leg (R-COPILOT-LIVE / R-CURSOR-LEG) — **ACCEPTANCE MET 2026-08-09 (ADR 0006; first live green stage + first green conveyor run; copilot/cursor legs still open on CLI absence)**

**Context.** The battle-test proved card fidelity (copilot byte-parity) but
NO live LLM execution has ever run through the gate-runner — that is the
deferred [D] seam. `kernel/descriptors/invocation-descriptors.json` carries
rows for `claude-code`, `copilot`, `cursor` with projections and exit maps;
the `command_template` values have never driven a real CLI.

**Work.**
1. Read the descriptor rows; verify each `command_template` against the
   real headless CLI (claude-code headless exists; copilot CLI and cursor
   headless were missing at battle-test time — re-probe availability, and
   record what is still absent rather than substituting).
2. Toy workspace smoke: drive ONE stage live through `gate-runner run` —
   specifier is the right role (no gates, writes only `specs/`, and the
   battle-test's live probe (4/4 boundaries held) is the precedent). Use
   `configs/o7` with a scratch workspace carrying the layout from
   `configs/o7/README.md`.
3. If a full stage completes: record the first-ever live conveyor stage in
   the evals bundle (new file next to the battle-test report) with the run
   dir's validation report. Do NOT close R-COPILOT-LIVE/R-CURSOR-LEG unless
   that harness's leg actually ran.

**Acceptance:** one live stage green end-to-end (invocation + handoff +
between-run validation) on at least one harness; honest [D]-risk ledger
updated (closed only what ran); selftest 20/0.

### Item 3 — T05 schema reconciliation (event-driven; blocked externally)

**Trigger:** the o7 Spring Boot repo exists with the T05-regenerated
`TestCaseIR` JSON Schema. Upstream of that: the o7 spec's sign-off gate is
OPEN and ADR 0016 is Proposed — **owner actions, do not self-trigger**.

**Work when triggered:** diff the tool's `o7-spec-derived.1` contract
(README table + `ir_gate_checker.py` constants) against T05's schema; every
divergence is a seam decision recorded as a dated ADR 0005 amendment; bump
the tool contract string, reseal fixtures (`seal` subcommand), regenerate
goldens, tool selftest ×2.

### Item 4 — future gate ids (spec-first; do NOT overload `ir-gate`)

Three ids ADR 0005 explicitly keeps separate. Each follows the full
invariant-2 playbook (its own ADR deciding declarations, tool, threshold,
corpus pin — the ADR 0005 shape is the template):

| Gate id | What it proves | Readiness |
|---|---|---|
| `ir-conformance` | the C3 release gate: the committed IR-conformance corpus (one case per opcode + assertion kind + cascade-miss hard-fail + each taxonomy trigger) passes before any `interpreterVersion` pin | spec-side authoring can start now (o7 spec C3 defines the case list); checker needs the interpreter to exist |
| `fitness` | ArchUnit F-B: no per-test generated Java, no model call on the replay path (o7 T02) | needs the Spring Boot repo |
| `device-walk` | the real Perfecto week-gate clause (a) | farthest out: device pool + credentials + interpreter |

### Item 5 — the kata LLM study (needs items 1 + 2)

**Context.** The pre-registered §6 experiment (ADR 0004): 4 arms × 12 Java
katas × 5 reps = 240 cells. The instrument is frozen and freshly restamped
(plan `kata:26b8f03465ba`); `kata plan/analyze/report` are deterministic and
gate-pinned. Missing: the Java gate tools (item 1), a live harness (item 2),
12 kata workspaces, and a model budget.

**Hard rules:** the analysis is immutable — thresholds live in
`PREREG_CONSTANTS` behind the digest triangle; results files must carry the
frozen `prereg_digest` and the current plan stamp; `kata analyze` over the
observations IS the decision. No metric may be hand-assembled: `kata_results`
comes from tool output (`provenance == "tool_output"`, anti-BMAD).

**Acceptance:** a schema-valid `kata_results` for at least one full arm
produced by real runs; `kata analyze` verdict committed; no constant
touched.

## Appendix A — kata restamp procedure (after ANY registry byte change)

Same session as the registry edit, no exceptions:

```bash
cd tooling/sdd-roles
K=kernel/corpus/kata
OLD=$(python3 -c "import json; print(json.load(open('$K/plan.json'))['stamp'])")
.venv/bin/kata plan --kernel kernel --registry kernel/catalog/role-registry.json \
  --prereg $K/preregistration.json --workload $K/workload.json \
  --reps 5 --default-model UNBOUND --out $K/plan.json
NEW=$(python3 -c "import json; print(json.load(open('$K/plan.json'))['stamp'])")
# exact-literal swap OLD→NEW in: the 8 results-*.json AND
# failures/results-inconsistent/results.json (each contains it exactly once);
# failures/stamp-mismatch is doctored (kata:000000000000) — must NOT be touched.
# then regenerate all 8 verdicts + the scorecard:
for b in six-roles three-roles gates-not-roles tamper solo btok-fail conj-ia-only conj-margin-fail; do
  .venv/bin/kata analyze --kernel kernel --plan $K/plan.json --prereg $K/preregistration.json \
    --results $K/results-$b.json --out $K/verdict-$b.json
done
.venv/bin/kata report --kernel kernel --verdict $K/verdict-six-roles.json --out $K/scorecard.md
```

Then confirm: tamper verdict still `winner none / tamper-invalid`; selftest
20/0 ×2. `PREREG_CONSTANTS` are NEVER touched by a restamp.

## Appendix B — projections regeneration (after catalog registry/body edits)

```bash
cd tooling/sdd-roles
for h in claude-code copilot cursor; do
  .venv/bin/role-emit project --kernel kernel \
    --descriptors kernel/descriptors/invocation-descriptors.json --harness $h \
    --registry kernel/catalog/role-registry.json --bodies kernel/catalog/bodies \
    --out kernel/corpus/catalog-projections/$h
done
```

## Appendix C — gate-row execution probe (per-tool smoke, runner-faithful)

Fill a `configs/o7` gate row's argv exactly as the runner would (`{python}`,
`{sdd_roles_root}`, `{workspace}`, `{report}` + the tool's bind token),
run it against a scratch workspace, and assert: report exists at `{report}`,
carries `tool_version`, exit 0 on the green fixture and non-zero on the red
one. The 2026-08-09 session ran this for the ir-gate row (green → 0,
red → 2); reuse the pattern for each Java tool.
