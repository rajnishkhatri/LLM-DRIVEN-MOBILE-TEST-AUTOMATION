# Kata seam — running the real kata (the deferred, non-deterministic half)

Build item 6 ships the kata **rig** — the deterministic `plan → analyze → report`
instrument, gate-tested in `corpus/kata/`. This document specifies the other
half: the LLM-driven execution that produces a real `kata_results` file for
`kata analyze` to consume. It is **not built or gate-tested** (it needs a live
model, real Java kata workspaces, and the crap4java/mutate4java gate binaries),
but it is fully specified here so it is runnable later without redesign.

The seam's only contract: **emit a schema-valid `kata_results` whose `plan_stamp`
and `prereg_digest` match the plan, and whose `observations` biject the plan's
`cells` exactly.** Everything downstream of that file is deterministic and
already gated. The runner is a dumb executor of resolved plan bindings — it
makes no analysis decisions.

## Prerequisites (not present in this environment)

- The three harness CLIs the plan targets (`claude`, `agent`/cursor, `copilot`).
  Only `claude` is installed here; the memo §8 smoke tests (#1 SKILL.md cap, #2
  cursor headless reliability) gate the cursor/copilot legs and must pass first.
- ~~The gate binaries bound into each kata workspace~~ *(2026-08-09: BUILT —
  all four Java gate tools exist under `tools/<tool-id>/` on the
  ir-gate-checker template, each with its own fixture corpus and selftest;
  they are bound at run time via `--bind` tokens (`configs/o7/README.md`),
  not shipped inside the workspace. Uniform exit taxonomy 0 green / 2 red
  (report written, fail-closed) / 3 usage-or-environment error — this
  supersedes the pre-build sketch here that had `mutate4java` exiting 3 on
  a surviving mutant. Thresholds unchanged from canon: workspace CRAP≤6
  per method — a deliberate parameter, not the crap4j folklore default —
  and mutation score ≥ 0.85, decided on the integer scale.)*
- ~~The real 12-instance workload (C1–C4)~~ *(2026-08-09: DONE — the twelve
  `source_kata` values are real katas and each has a built workspace. Two
  corrections to the sketch above, recorded at the same edit: the workload
  input is **`kernel/corpus/kata/workload.json`**, not the
  `kernel/catalog/kata-workload.json` path this line used to name (likewise
  the prereg below lives at `kernel/corpus/kata/preregistration.json`); and
  regenerating the plan is not enough — the plan stamp is an input to every
  stamp-carrying golden, so the workload edit takes the full restamp
  procedure (plan regen → exact-literal stamp swap in the 8 `results-*.json`
  plus `failures/results-inconsistent/results.json`, leaving the doctored
  `failures/stamp-mismatch` fixture alone → 8 verdicts → scorecard). Chosen
  katas: Mars Rover / Bank OCR / Roman Numerals / Bowling Game (greenfield);
  Gilded Rose / Trivia / Tennis Refactoring / Yatzy (legacy); date-range
  overlap / RPN calculator / word wrap / shopping-cart discount
  (seeded-bugfix, `protected_tests: true` — the D7 leg). Workspaces,
  provenance and the per-family baseline gate states:
  `tooling/sdd-roles/kata-workspaces/README.md`.)*

## Procedure (per plan cell)

For each `cell` in `kata plan` output, in `cell_id` order:

1. **Isolate.** `git worktree add` a clean copy of the cell's kata workspace
   `kata-workspaces/<instance>`. For the `seeded-bugfix` family, mount the D7
   write-guard so `tests/` is write-protected (the guard is already built —
   `write-guard mount`).
2. **Run the arm, unchanged.** Invoke the existing `gate-runner run` conveyor
   with the registry filtered to the cell's arm roles, the arm's kernel-config
   (gate set + thresholds), and the harness binding. The cell's `bindings[]`
   carry the resolved `{role, model, prompt}` — the runner drives the live model
   behind each `prompt` (the `{args}` token is substituted here, at run time,
   not at plan time). No new orchestration: the seam only *feeds* the runner.
3. **Extract the eight metrics** from the run-dir + ledger into one
   `cell_result`:
   - `gates[].first_attempt_pass` / `final_pass` — the first and final gate
     outcomes recorded in the ledger's gate_run entries;
   - `mutation_score` — from the `mutation` gate's report (as an integer on
     [0,10000], e.g. 0.86 → 8600 — **no floats**, the rig is integer-only);
   - `crap` — `{max, mean, over_threshold_count, per_method}` from the `crap`
     gate report (`over_threshold_count` counts methods above the CRAP≤6
     workspace threshold, C8);
   - `tokens`, `wall_clock_ms` — from the harness transcript / run timing;
   - `handoff_schema_failures` — count of `contract-lint` failures on the
     stage handoffs recorded in the ledger;
   - `tamper_events` — count of `write-guard` block decisions in the ledger
     (a D7 tamper attempt); `tamper_instance = tamper_events > 0`;
   - `final_all_gates_pass` — true iff every `gates[].final_pass` is true (the
     analyzer re-checks this self-consistency and refuses a mismatch);
   - `provenance` — always `"tool_output"` (these are gate/tool measurements,
     never role-authored; the analyzer refuses any other value — the anti-BMAD
     rule);
   - `evidence_ref` — `{path, sha256}` of the ledger entry substantiating the
     pass, so the claim is traceable to the committed run.
4. **Append** the `cell_result` to `kata_results.observations`.

## Emit and analyze

Set `plan_stamp` and `prereg_digest` from the plan, then:

```
kata analyze --kernel kernel --plan <plan.json> \
             --prereg kernel/catalog/kata-preregistration.json \
             --results <kata_results.json> --out <verdict.json>
kata report  --kernel kernel --verdict <verdict.json> --out <scorecard.md>
```

`analyze` is fail-closed: any stamp/digest mismatch, missing or extra cell,
non-`tool_output` provenance, or `final_all_gates_pass` inconsistency exits 2
and writes nothing. When it exits 0, the verdict IS the pre-registered decision
— and because the criteria are frozen by the digest triangle, no threshold can
have moved between plan time and analysis time.

## Residual trust edge

`analyze` verifies `provenance == "tool_output"` and that `evidence_ref` is
present and well-formed, but does **not** re-verify that the `evidence_ref`
sha256 chains into the gate-runner ledger — that requires the real run-dir and
is a seam obligation checked at real-run time, not a built check (ADR 0004).
