---
type: record
title: sdd-roles / o7 — fourth session record (item 0 + item P1 landed; four new findings)
description: >-
  What the fourth session actually did: ran the item-0 baseline green, landed
  item P1 (per-arm kernel configs), and investigated the D1/D2/D3 owner
  decisions against source. Four findings that are NOT in the execution plan,
  one of them a blocker on the plan's own cheap option. No owner decision was
  taken — all four remain open. No kernel, validator, registry, descriptor or
  corpus file was modified; no live runs; no spend.
date: 2026-08-10
status: open
amends: kata-study-execution-plan.md
adr_0004: ../../../architecture/adrs/tooling/sdd-roles/0004-kata-rig-deterministic-instrument.md
adr_0006: ../../../architecture/adrs/tooling/sdd-roles/0006-live-invocation-runner-contract-channel.md
tags: [sdd-roles, o7, record, kata, study, owner-decision, findings]
---

# Fourth session record

Reading order for a cold session: this file first (it is current), then
[kata-study-execution-plan.md](kata-study-execution-plan.md) for the items
it does not supersede. §3 below contains findings that **change** that plan —
apply them before executing items D1, D2 or 5.

---

## 1. What landed

### Item 0 — session baseline: **GREEN**

All six checks, run from `tooling/sdd-roles/`:

| Check | Result |
|---|---|
| `contract-lint selftest --kernel kernel` | exit 0, **20 pass / 0 fail** |
| `ir-gate-checker selftest` | 8 cases, pass, exit 0 |
| `contract-lint validate configs/o7 --kernel kernel` | exit 0, **29 / 0** |
| `lint_workspaces.py` | `lint: clean`, 12/12 instances |
| validator version | 0.7.2 |
| kata plan stamp | `sdd-roles 1.4.0 kata:73fca8cae0f6` |
| projection stamp | `sdd-roles 1.4.0 catalog:1d520797652a` |

Selftest summary counters unmoved: `guard_cases 23`, `kata_cells 240`,
`flipped_cases 12`, `emitter_trees 4`, `catalog_trees 3`, `deferred_entries 0`.

### Item P1 — per-arm kernel configs: **DONE** (self-verified)

Created three sibling config directories, each a byte-copy of `configs/o7`
with the single `"arm"` field changed:

| Directory | `arm` | Resolved role sequence |
|---|---|---|
| `configs/o7` (unchanged) | `B` | specifier → maker3 → checker3 |
| `configs/o7-arm-a` | `A` | solo |
| `configs/o7-arm-c` | `C` | specifier → architect → coder → cleaner → hardener → qa |
| `configs/o7-arm-c-dbg` | `C-dbg` | specifier → architect → coder → cleaner → hardener |

Each directory also carries `speckit-mapping.json` (sha256
`162cb24b2831c3cb3620880ec0763c2eff171abbda46099840a4f4b2a4f308ed`,
byte-identical to the `o7` original — the runner copies both into the run dir
at genesis) and a new `README.md` recording provenance and the re-derivation
procedure.

**Acceptance, both limbs met:**

1. `diff configs/o7/kernel-config.json <each>` → exactly one changed line
   (`"arm"`), confirmed for all three.
2. `contract-lint validate <dir> --kernel kernel` → exit 0, 29/0 on all four
   directories.
3. Dry `Runner` construction (read-only, `validator/src` on `sys.path`, no
   stage executed) resolved the four sequences in the table above. The Runner
   constructor is the right probe: it performs the arm lookup **and** validates
   that every role's declared gates have a KernelConfig row, a declared
   threshold, and an allowlisted tool.
4. `contract-lint selftest` still 20/0 afterwards.

**Caveat:** this is my own verification. The independent audit of P1 was a
casualty of the failed workflow (§4), so P1 has not had a second pair of eyes.

### Item D1 — guard vs ADR 0006 carve-out: **DONE** (owner-approved, unit-verified)

Owner approved the narrow fix (2026-08-10). Implemented with the F3 correction
applied — the exemption sits **before** the containment check, not before the
`WRITER_ONLY` raise. `validator/src/sdd_roles_validator/guard.py`: factored the
symlink-hardened canonicalization out of `_contained_rel` into `_canonical_abs`,
then in `_evaluate` the current stage role may **create or modify exactly
`<run_dir>/handoff.draft`** — checked ahead of containment so the outside-the-
workspace run dir (`REPO_SCOPE`) no longer pre-empts it. Properties, all
corpus-proven:

- **one filename wide** — every other run-dir path still blocks;
- **create/modify only** — `delete` stays blocked (runner owns the unlink);
- **symlink-safe** — candidate is symlink-resolved and compared to the
  *lexical* draft path, so a `handoff.draft` symlink onto a protected test
  resolves away, misses the exemption, and is caught `TESTS_PROTECTED`.

Corpus tax: five new guard decision cases (`handoff-draft-allow`,
`-allow-inside`, `-delete-block`, `run-dir-other-block`,
`handoff-draft-symlink-block`) + one `handoff-symlink-escape` selftest setup;
`GUARD_DECISION_CASES` 23 → **28**. Validator **0.7.2 → 0.7.3** (bumped in
`pyproject.toml` + `__init__.py`, reinstalled editable). ADR 0006 carries a
dated amendment (2026-08-10) recording the reconciliation.

Verified: selftest **20/0 ×2 byte-identical**, validator 0.7.3, guard_cases 28;
a 6-variant adversarial probe via the console script confirmed the **live
shape** (absolute path to `<run_dir>/handoff.draft`, create → `allow`) and the
**absolute symlink-laundering attack** (→ `TESTS_PROTECTED`); ir-gate 8/8;
`validate` 29/0 on all four arm configs; workspace lint clean; both stamps
unmoved (`kata:73fca8cae0f6`, `catalog:1d520797652a`).

**Live acceptance: GREEN.** The guarded bugfix cell of the pricing pass below
completed (runner exit 0) with the write-guard mounted: 6 hook fires, **all
`allow`, 0 block** — the handoff.draft writes went through, no legitimate write
was obstructed, and the model fixed the code without touching the protected
tests. D1 is now proven live, not just in unit cases.

### Pricing pass (3 live cells, Sonnet): **DONE** — evidence-pricing-pass-001/

Owner chose "proceed but price first". Three real cells to replace the soft
$4.80 floor. All on Sonnet (operator CLI = `opusplan`), so comparable to the
pilot. Total spend **$12.51**.

| Cell | Completed | Wall | Cost | Note |
|---|---|---|---|---|
| greenfield-1 × **arm C** (6 roles) | **NO** (exit 2) | 1614 s | $4.14 (partial) | died at the architect stage — see F6 |
| legacy-1 × arm B | yes | 1271 s | $4.92 | crap green (tangle decomposed), mutation ≥ .85 |
| bugfix-1 × arm B **guarded** | yes | 610 s | $3.45 | defect fixed, tests green; **D1 live acceptance** |

**What the money bought:**
- **Arm-B cost across all three families is now measured:** greenfield $4.80
  (pilot), legacy $4.92, bugfix **$3.45**. Tighter than feared, and the
  seeded-bugfix family is the *cheapest* — the one-line fix is quick. Arm-B
  floor is ~$3.45–$4.92, call it ~$4.4 mean.
- **The 6-role arm cost is STILL unmeasured** — the cell that would have given
  it (greenfield × arm C) died at a structural blocker (F6) after only 2 of 6
  stages, so its $4.14 is a partial, not an arm-C cost. Arm C and C-dbg are
  half the study's cells and their cost remains unknown.
- The greenfield arm-C **specifier alone took 975 s** (~16 min) of pure model
  time (specifier has no gates) — a slow-stage cost data point.

---

## 2. What was investigated

D1, D2a, D2b, D3 and a completeness sweep for decisions the plan does not
list. First attempted as a 14-agent workflow, which failed totally (§4); then
done inline against source. Everything in §3 carries a file:line citation and
was read directly, not inferred.

---

## 3. Findings — these amend the execution plan

### F1 (BLOCKER) — the plan's "60 cells / 1 arm" option produces no verdict

The execution plan's budget table offers *60 cells (1 arm)* at $288/$480 as
the cheap option. It is not a study:

- `_check_bijection`
  ([kata.py:253-265](../../../../tooling/sdd-roles/validator/src/sdd_roles_validator/kata.py))
  raises `RenderFailure` when **any** plan cell is absent from `observations`.
  `kernel/corpus/kata/plan.json` holds **240 cells — 60 per arm across all
  four arms** (`A`, `B`, `C`, `C-dbg`; 12 instances × 5 reps each). A 60-cell
  single-arm results file is missing 180 plan cells → `analyze` exits 2 and
  writes nothing.
- Independently of the bijection, every pre-registered criterion in
  `kernel/corpus/kata/preregistration.json` is a **cross-arm** comparison:
  `b_over_a_pp: 5`, `c_over_a_pp: 10`, `c_over_b_pp: 5`,
  `kill_a_within_c_pp: 5`, `c_over_a_intervals: "non-overlapping"`,
  `kill_a_token_num/den`. With one arm there is nothing to compare against.

**Consequence:** the minimum analyzable run is **all 240 cells at reps 5** —
$1,152 (Sonnet, at the plan's unverified $4.80/cell) or $1,920 (Opus 5). The
budget gate is therefore roughly **4× what the plan's cheapest row implies**.

**The one cheaper analyzable shape:** regenerate the plan with `--reps 1` →
48 cells (4 arms × 12 instances × 1 rep), all arms present, bijection
satisfiable, ≈$230/$384. This deviates from the pre-registered `reps: 5` and
must be declared as a deviation in the scorecard by hand — see F2 for why
nothing will catch it for you.

### F2 — `analyze` does not cross-check `reps` against the pre-registration

`analyze`
([kata.py:285-300](../../../../tooling/sdd-roles/validator/src/sdd_roles_validator/kata.py))
verifies exactly three things before evaluating: `_assert_prereg_pinned(prereg)`,
`results.prereg_digest == PREREG_DIGEST`, and
`results.plan_stamp == plan.stamp`. It never compares `plan_doc["reps"]`
against `prereg["reps"]`.

The plan's `reps` **is** inside the stamp — `stamp_src = canonical_dumps(registry)
+ canonical_dumps(workload) + str(reps) + default_model`
([kata.py:190-194](../../../../tooling/sdd-roles/validator/src/sdd_roles_validator/kata.py))
— so a reps change is *visible* in the stamp, but no check *rejects* it. A
plan regenerated at `--reps 1` analyzes clean against a pre-registration that
says `reps: 5`.

This is a hole in an otherwise fail-closed analyzer. It is worth closing on its
own merits (a `reps` equality check plus the corpus tax under invariant 7),
and it is a precondition for trusting any reduced-reps run.

### F3 — D1's prescribed fix is aimed one line too low

The plan's D1 step 2 says to *"permit the single exempt path before the
`WRITER_ONLY` raise"*. That alone changes nothing for the study as it is
actually run:

- `pilot_cell.py:133-135` sets `ws, run_dir = SCRATCH / "workspace", SCRATCH /
  "run"` — the run dir is a **sibling of the workspace, not inside it**.
- `_evaluate`
  ([guard.py:230-241](../../../../tooling/sdd-roles/validator/src/sdd_roles_validator/guard.py))
  calls `_contained_rel(workspace, raw_path)` **first** (line 231); for a path
  outside the workspace that returns `None` and raises `Block("REPO_SCOPE", …)`
  at line 233. `WRITER_ONLY` at line 241 is never reached.

**The exemption must therefore precede the containment check, not the
`WRITER_ONLY` raise.** (The plan does note that `_contained_rel` "must also
stop rejecting it" — the correction here is that this is the *primary* site,
not a secondary one.)

**Two facts that make the carve-out narrower than it looks:**

- The runner reads the draft **after** the gates, then **deletes it**:
  `draft_path.unlink()`
  ([runner.py:488-500](../../../../tooling/sdd-roles/validator/src/sdd_roles_validator/runner.py)).
  The durable artifact is `handoff-<run_id>-NNN.json`, written by the runner
  and still fully blocked. The exempt surface is one transient filename that
  does not survive its own stage — a role cannot read or clobber a prior
  stage's draft because there isn't one.
- Therefore the exemption should be **create/modify only, never delete** (the
  runner owns the unlink), and must be **path equality after normalization**.
  A prefix test would let `<run_dir>/handoff.draft/../<run_id>.ndjson` through
  — and because the exemption sits *ahead* of `_contained_rel`, it cannot
  borrow that function's normalization; it must normalize itself.

**Corpus tax, confirmed:** `kernel/corpus/guard/decisions/` holds 23 case
directories today; `GUARD_DECISION_CASES = 23`
([selftest.py:81](../../../../tooling/sdd-roles/validator/src/sdd_roles_validator/selftest.py),
asserted at line 1313). The two new cases the plan names take it to **25**.

### F4 — D2a's load-bearing claim is CONFIRMED

The plan argues that pinning `invocation.model` in the catalog registry makes
the digest triangle encode the model. Verified:

- `stamp_src` includes `canonical_dumps(registry)` **and** `default_model`
  ([kata.py:190-194](../../../../tooling/sdd-roles/validator/src/sdd_roles_validator/kata.py)),
  so both the per-role pin and the planner default reach the stamp.
- `render_plan`'s `binding()` writes `"model": inv.get("model") or
  default_model` (line 158) into every cell's `bindings[]`
  ([kata.py:148-163](../../../../tooling/sdd-roles/validator/src/sdd_roles_validator/kata.py)).
- The schema accepts any non-empty string: `$defs/invocation` in
  `kernel/schemas/role-registry.schema.json` declares
  `model: {type: string, minLength: 1}` with no enum. A real model id
  validates; nothing needs widening.
- `"UNBOUND"` carries **no** special meaning anywhere — the only live
  reference is `kata.py:243`'s `flags.get("default-model", "UNBOUND")` default;
  every other hit is a corpus fixture or README text. No check keys off it.

Option (a) is mechanically sound as written. The plan's warning about
`--bind model=…` being silently overridden by the registry value stands.

### F5 — D3's mechanism is confirmed; its premise is UNVERIFIED

Confirmed:

- The guard emits `block <CODE> <path>` on **stdout** and the human detail on
  **stderr**, exit 2
  ([guard.py:158-160](../../../../tooling/sdd-roles/validator/src/sdd_roles_validator/guard.py)).
  So a real, useful reason string *is* produced today.
- `gate-wrap` runs the tool with `capture_output=True`
  ([gate_wrap.py:67](../../../../tooling/sdd-roles/validator/src/sdd_roles_validator/gate_wrap.py))
  and writes only `entry["decision_output"]` to stdout (line 82) — the code and
  detail are discarded exactly as the plan says.
- `gate-wrap` already uses stderr for its own usage errors (line 17), so
  forwarding would not open a new channel.
- But stderr is **not** part of the declared descriptor contract: the
  claude-code row's `exit_code_map` maps `tool_exit → decision_output` /
  `wrapper_exit` only. Under invariant 13, forwarding stderr means the contract
  text must say so.

**Not confirmed:** that Claude Code surfaces a PreToolUse hook's stderr to the
model as the blocking reason. The agent assigned to check this against the hook
documentation died with the workflow. **The entire value of D3 rests on this
premise** — verify it before doing the work, and record the answer either way.

---

### F6 (BLOCKER, found by the pricing pass) — arm C / C-dbg cannot complete greenfield (and likely bugfix) — **RESOLVED 2026-08-10**

> **Resolution (owner-approved):** the architect's gate set became `[build]`
> (was `[build, tests]`). ADR 0004 amended 2026-08-10; the ownership guide's
> stale line corrected. Registry restamp + six-regen done: kata stamp
> `kata:73fca8cae0f6` → **`kata:0628e6306595`**, projection
> `catalog:1d520797652a` → **`catalog:95747f71f9d8`**; `plan_digest` /
> `prereg_digest` unchanged, tamper verdict preserved, selftest 20/0 ×2, all
> four configs 29/0. **Re-run confirmed live (r1):** the architect PASSED
> (`build` only) and the run went four stages further — specifier → architect →
> coder → cleaner all green — then failed at the hardener on a *different*
> blocker, **F7** (below). F6 itself is proven fixed. The r1 cell cost **$8.41**
> for 5 of 6 stages → a full arm-C cell ≈ **$9–10** (~2× arm B). Evidence:
> `evidence-pricing-pass-001/f6-acceptance-rerun.json` + `report-…-r1.json`.

### F7 (BLOCKER, found by the F6 re-run) — the hardener's write scope vs the Maven layout — **RESOLVED 2026-08-10**

> **Resolution (owner-approved):** hardener `write_scopes` `[tests/, specs/]` →
> `[src/test/, tests/, specs/]`. ADR 0004 addendum 2026-08-10; registry restamp
> + six-regen: kata `kata:0628e6306595` → **`kata:a6f56755e9b0`**, projection
> `catalog:95747f71f9d8` → **`catalog:cabd69051aa2`**; selftest 20/0 ×2, configs
> 29/0, tamper verdict preserved.

Same class of bug as F6, one dimension over. The hardener strengthens tests, so
it writes `src/test/java/…` (Maven), but its scope was `[tests/, specs/]` — no
`src/test/` coverage — so the retro `CHK-SCOPE` lint blocked a **legitimate**
write and the stage failed. Every other test-writing role (maker3, checker3,
coder, cleaner, qa, solo) carries `src/`, which covers `src/test/`; the hardener
must stay tests-only, so it gets `src/test/` directly, not `src/`.

**A static audit of all nine roles' scopes vs the Maven paths each must write
found the hardener was the ONLY uncovered case** — F6 (gate) and F7 (scope) are
the *only* two role/workspace mismatches, both now fixed. The audit
(scope-vs-layout, plus the F6-style gate-satisfiability-at-position check) is
the cheap guard that should precede any future arm/role change — running the
worst-case family live is what surfaces these, at ~$8–10 a cell.


The greenfield × arm C cell died at the **architect** stage, not on time or
model quality. Mechanism, confirmed from the ledger and gate reports
(evidence-pricing-pass-001/ledger-greenfield-1-armC-r0.ndjson):

- Arm C's sequence is specifier → **architect** → coder → cleaner → hardener →
  qa. The **coder is the first stage that writes the test suite**; nothing
  before it does.
- The architect declares gates `[build, tests]` (registry). On a greenfield
  instance the workspace ships **no suite at all**, so `junit-runner` returns
  `tests: 0` and — by deliberate design — scores it **red**
  (`"not_evaluable": "no tests discovered (a vacuous pass is fail-open)"`).
- The architect cannot fix this: writing production code is not its role, and
  it precedes the coder. It failed the `tests` gate **3× identically** (same
  report hash each attempt), exhausted `rework.max`, and the runner exited 2.

This is deterministic, not a model fluke — a retry produces the same result.
It generalizes:

- **greenfield × {arm C, C-dbg}** — certain failure (no tests exist before the
  coder). 4 instances × 2 arms × 5 reps = **40 cells**.
- **bugfix × {arm C, C-dbg}** — the suite exists but is **red** (seeded
  defect), which the architect also may not fix without doing the coder's job;
  so the same gate is unsatisfiable, OR a model that fixes the bug at the
  architect stage corrupts the arm-C measurement. Either way problematic. 4 ×
  2 × 5 = **40 cells**.
- **legacy × {arm C, C-dbg}** is fine — the characterization suite is green at
  baseline, so the architect's `tests` gate passes.

So **up to ~80 of the 240 cells** (a third of the study) would fail or be
invalid for a *structural* reason unrelated to role decomposition — the thing
the study measures. This was NOT reconciled in `kernel/docs/kata-seam.md`.

**This is an owner decision and a hard prerequisite for any arm-C/C-dbg run.**
Sketch of the options (each has a tax, none taken):
1. Drop `tests` (keep `build`) from the **architect** gate set in the registry
   — a pre-implementation stage arguably should not be gated on a passing
   suite. Registry change → kata restamp + six-regen. Cleanest, but changes
   what the architect stage verifies.
2. Teach `junit-runner` / the runner to treat "no tests yet" as a pass for
   pre-coder stages. Kernel/tool change; messier; risks re-opening the
   vacuous-pass fail-open hole the current red deliberately closes.
3. Accept it as a real result (arm C fails greenfield/bugfix). Bad science —
   measures a config artifact, not roles.
4. Scope arm C / C-dbg to the legacy family only. Breaks the pre-registered
   4-arms × 12-instances design.

**Until this is resolved, only arm A and arm B are safely runnable across all
families.** Arm B is fully priced and unblocked; arm A (solo) is untested here
but writes its own tests like a maker, so it is not expected to hit F6.

## 4. Operational note — the 14-agent workflow failed totally

A workflow was launched to research D1/D2/D3 in parallel (6 investigations →
adversarial refutation of each → independent P1 audit → synthesis). It ran
**2.5 hours, started 36 agents, and produced zero results** — not one agent
ever reached its `StructuredOutput` call. Failure signature from the run
journal and per-agent transcripts:

- 14 agents ended on `API Error: Connection closed mid-response`
  (`server_error`); 34 carry `[Request interrupted by user]`.
- Deaths arrived in **synchronized cohorts** — 3 to 5 agents sharing an
  identical death timestamp — which is one fatal API error taking down the
  whole in-flight batch, followed by a retry into the same wall.
- All six stage-1 keys exhausted their retries and returned null, so the
  pipeline yielded nothing and the synthesis would have been built on six
  empty inputs. The run was killed rather than allowed to emit that.

**Candidate invariant 16:** *a fan-out is only as good as its smallest
survivable unit.* Heavy prompts (a long plan plus many files to read) at high
effort gave each agent a 10–20 minute runway it never survived, and the cohort
coupling meant one failure cost the whole batch. Scope agents to minutes, not
tens of minutes, and check the run journal for `completed` records early —
36 `started` records with no `completed` is visible within the first few
minutes and is the signal to abort.

The investigation was subsequently done inline in a fraction of the time. For
work of this shape — reading a known set of files and citing them — inline was
strictly better.

---

## 5. What is open

Decisions taken: (1) go/no-go → **proceed but price first**; (2) guard → **narrow
fix approved (done, live-proven)**; (3) pricing shape → **3 cells (done)**.

| # | Open item | State / blocked on |
|---|---|---|
| **F6** | Arm C/C-dbg architect-gate blocker → architect gate `[build]` | ✅ **FIXED + LIVE-CONFIRMED 2026-08-10** (architect passes; run reached stage 5) |
| **F7** | Arm C/C-dbg hardener scope blocker → hardener scope `+src/test/` | ✅ **FIXED 2026-08-10** (registry+restamp+regen, ADR 0004 addendum). Static audit: last structural mismatch. Full arm-C completion not yet re-confirmed live |
| 1 | **Study scope** — real floor is 240 cells / reps 5 ($1,152–$1,920); 60-cell option is unanalyzable (F1) | owner; also gated by F6 for arm-C/C-dbg |
| 2 | **F2 reps hole** — add a plan-vs-prereg `reps` check to `analyze` + corpus tax | owner (independent; worth doing regardless) |
| 3 | **D1** — guard carve-out | ✅ **DONE + LIVE-PROVEN 2026-08-10** (guarded bugfix cell exit 0, 6 hooks all allow) |
| 4 | **D2a** — registry pin (verified sound, F4) vs run-time bind | owner |
| 5 | **D2b** — which model; arm-B ~$3.45–$4.92/cell, **arm-C ≈ $9–10/cell** (~2× arm B, from the F6 re-run) | owner |
| 6 | **D3** — verify the F5 premise before deciding | anyone; cheap |
| 7 | **Item 5** — the study itself | F6 + items 1–5 |
| 8 | E1 / E2 / E3 | unchanged: event- and environment-driven |

**State of the tree (end of session 4):**
- **Changed (D1):** `validator/src/.../guard.py` + `selftest.py`, 5 new
  `kernel/corpus/guard/decisions/` cases, validator 0.7.2 → **0.7.3**,
  ADR 0006 amended.
- **Changed (F6 + F7):** `kernel/catalog/role-registry.json` (architect gates
  `[build,tests]`→`[build]`; hardener scope `[tests/,specs/]`→
  `[src/test/,tests/,specs/]`) → **two restamp + six-regen cycles**. Net stamps:
  kata `kata:73fca8cae0f6` → **`kata:a6f56755e9b0`**, projection
  `catalog:1d520797652a` → **`catalog:cabd69051aa2`** (intermediate F6 stamps
  `0628e6306595`/`95747f71f9d8` superseded). Kata corpus restamped, projections
  regenerated, workspaces rebuilt; ADR 0004 amended + addendum; ownership guide
  corrected. `plan_digest` / `prereg_digest` unchanged both times.
- **Also:** three `configs/o7-arm-*` dirs (P1), this record, the
  `evidence-pricing-pass-001/` bundle (incl. the r1 re-run).
- **Unchanged:** descriptors, workload, emitter corpus, `PREREG_CONSTANTS`.
- **Spend:** **$20.92** ($12.51 pricing pass + $8.41 F6 re-run, all Sonnet).
  Selftest 20/0 ×2 after every change.
