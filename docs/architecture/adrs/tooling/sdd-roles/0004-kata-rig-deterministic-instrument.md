---
type: architecture
title: 'ADR 4. The kata rig is a deterministic instrument; the pre-registration is pinned by a digest triangle'
description: 'Ship a deterministic kata rig as the instrument for role-kernel evals — placeholder workload, sealed fixtures, exit-code-only verdicts.'
tags: [architecture, adr]
---

# ADR 4. The kata rig is a deterministic instrument; the pre-registration is pinned by a digest triangle

## Status

Accepted
<!-- Accepted at the sdd-roles-kata build-gate close, 2026-08-08 (spec v2 after
review round 1; clarify C1–C4 owner-decided = placeholder workload, C5–C8
defaulted; F1–F4 ratified as drafted). Build gate: selftest 20/20 ×2
byte-identical at 1.4.0 / 0.6.0, acceptance PASS on a clean offline copy, tamper
trio verified (each flipping `kata` alone). Fourth ADR of the tooling/sdd-roles
series; governs build item 6 (the kata). Extends ADR 0001 (corpus-as-contract)
and ADR 0002 (golden-run conformance) to the study instrument; does not amend
ADR 0003. Discharges item-5 S6 ("model is an item-6 deployment parameter"):
`invocation.model` is now populated catalog data. -->

## Context

Build item 6 is "the kata" — the pre-registered §6 experiment that decides
whether the role conveyor earns six roles, three, or one. Two facts shape how
it can be built:

1. **Pre-registration is only meaningful if the analysis is fixed before the
   data exists.** The whole value of §6's criteria and kill-rule is that they
   were chosen without knowing the outcome. If the thresholds can be edited
   after observations are collected — even innocently, to "fix an obvious
   mistake" — the experiment degrades into post-hoc rationalization
   (p-hacking). The memo's own evidence spine (§2) is built on this discipline;
   the rig must enforce it mechanically, not by good intentions.

2. **The run itself is a multi-hour, multi-harness LLM study that cannot be
   executed in this environment** (only the `claude` CLI is present; a full
   A/B/C×12×5 run needs a live model budget and real Java toolchains with
   crap4java/mutate4java built). Building "the kata" as a single monolithic
   live orchestrator would couple the immutable analysis to the volatile
   execution and make nothing gate-testable now.

Alternatives considered:

- **Live orchestrator now** — needs absent CLIs and an LLM budget; and worse,
  puts the criteria code next to the data-collection loop where a "quick tweak"
  can silently move a bar. Rejected: violates fact 1 and blocked by fact 2.
- **Criteria as configuration read at analysis time** — lets the data supply
  its own thresholds; the exact p-hacking hole. Rejected.
- **Golden-tested criteria only** — a committed verdict golden catches
  *accidental* drift, but a coordinated same-commit edit of the threshold and
  its golden passes the gate. No cross-artifact bind. Rejected as insufficient
  for the scientific claim.

## Decision

**The kata rig is a deterministic instrument, split from its execution.** The
built half is three pure, clock-free, digest-stamped, all-or-nothing
subcommands of a new `kata` console script — `plan` (registry + workload + reps
→ a byte-stable `kata_plan`), `analyze` (plan + pre-registration + results → a
byte-stable `kata_verdict`), `report` (verdict → a Markdown scorecard, never
recomputing). All statistics are exact integer arithmetic (fixed-point scale
10000, `z²=9604/2500`, `math.isqrt` plus a perfect-square correction for a true
ceil-sqrt; both interval bounds use the *widened* half-width so the interval
never narrows versus the exact real interval — a floored lower bound would
narrow it and make a false C-win easier, the exact trap this pins shut) so the
goldens are byte-identical across machines; the one canonical Wilson expression
is frozen and must not be refactored after the golden is cut. The execution
half — driving real Java kata workspaces through the **existing, unchanged**
`gate-runner` conveyor with a live model, and the crap4java/mutate4java gate
implementations — is a documented seam (`kernel/docs/kata-seam.md`) whose only
obligation is to emit a schema-valid `kata_results` file; it is not built here.

**The pre-registration is pinned by a digest triangle.** The criteria
constants live frozen in analyzer code as `PREREG_CONSTANTS`;
`PREREG_DIGEST = sha256(canonical_dumps(PREREG_CONSTANTS))` is computed at
import (the clock-free stamp idiom). Three edges bind the corners: (1) the
`kata` selftest section asserts the committed `kata-preregistration.json`
canonical constants block byte-agrees with `PREREG_DIGEST` (code ↔ artifact);
(2) every `kata_results` file carries a `prereg_digest` the analyzer refuses to
process on mismatch, exit 2 (artifact ↔ data); (3) the digest is stamped into
the plan and every verdict (traceability). Moving a threshold therefore
requires changing the code constant *and* the committed artifact *and*
re-pinning every results file — a loud, atomic, git-dated **amendment**, never
a silent edit. A `+10pp → +5pp` change breaks the triangle and reds the gate.

The verdict encodes exactly §6's decision space
(`winner∈{A,B,C,none}` × `decision_reason∈{tamper-invalid, gates-not-roles,
six-roles-earned, three-roles, default-solo}`) via a frozen total precedence
order (`tamper → kill → C → B → default`); C−dbg is a non-decisional ablation.
The §6 result-level rule — "any tamper instance fails the run regardless of
gates" — is applied before any Wilson math and voids the data point.

## Consequences

- The analysis is provably immutable before any observation exists — the
  scientific point of pre-registration, enforced by the gate rather than by
  discipline. Post-hoc threshold edits are mechanically detectable.
- The rig is fully conformance-gated *now* (5 synthetic branch fixtures cover
  every decision path; a Wilson-exactness fixture pins the integer bounds)
  without any LLM run; when the real run happens, `kata analyze` over the
  observations IS the decision, and no one can move a bar to change it.
- The observations file is lossless (all 8 §6 metrics per cell), so the real
  run stays re-analyzable for secondary metrics; the analyzer aggregates
  internally without discarding data.
- Golden fragility of the frozen Wilson expression is a feature: any refactor
  that shifts an intermediate `isqrt` floor flips the goldens, which is the
  immutability guard. A "do not refactor after golden cut" comment marks it.
- `invocation.model` becomes catalog data (populated per role; resolved at plan
  time), completing the deployment binding item 5 deferred — this ADR records
  that item-5 S6's "model is an item-6 deployment parameter" is now discharged.
- The trust edge that remains: the analyzer checks `provenance=="tool_output"`
  and that `evidence_ref` is well-formed, but does not re-verify the evidence
  digest chains into the gate-runner ledger — that verification is a seam
  obligation at real-run time, out of scope for the built instrument.
- A residual, accepted limit: a coordinated amendment (code + artifact + all
  results, same commit) passes the gate. That is correct — it is a *visible,
  reviewable amendment*, not a silent tweak; the triangle's job is to force it
  into the open, not to make amendment impossible.

## Amendment 2026-08-10 (fourth session) — the architect stage sheds the `tests` gate

**The triangle worked exactly as designed** — it forced a real instrument flaw
into the open before the study spent money on it. The 3-cell pricing pass
(`docs/skills/sdd-roles/evals/evidence-pricing-pass-001/`) ran a greenfield ×
arm C cell live; it **died deterministically at the architect stage**. Cause,
confirmed from the ledger and gate reports:

- Arm C / C-dbg order the stages specifier → **architect** → coder → …; the
  **coder is the first stage that writes the test suite**.
- The architect declared gates `[build, tests]`. On a greenfield instance no
  suite exists yet, so `junit-runner` returns `tests: 0` and scores it **red**
  (`"no tests discovered (a vacuous pass is fail-open)"` — the deliberate
  anti-fail-open rule). The architect cannot fix this without doing the
  coder's job, so it failed 3× identically, exhausted `rework.max`, exit 2.
- This generalizes to **every greenfield and bugfix cell of arm C and C-dbg**
  — up to ~80 of the 240 cells — failing for a *structural* reason unrelated
  to role decomposition, the thing the study measures. Only legacy (green
  baseline suite) let the architect pass.

**Change (owner-approved):** the architect's gate set in
`kernel/catalog/role-registry.json` becomes `[build]` — a pre-implementation
stage is gated on "it still compiles", not on a passing suite it structurally
cannot produce. The architect still *writes* property tests (unchanged
`tests/` scope and invocation prompt); the coder, gated on `tests`, makes them
green. This is the intended architecture-first TDD flow: architect red → coder
green.

**Tax paid:** registry bytes changed, so the digest triangle moved as it must —
kata **restamp** (Appendix A of the kata-study plan): plan stamp
`kata:73fca8cae0f6` → **`kata:0628e6306595`**, with the exact-literal swap into
the 8 `results-*.json` + `failures/results-inconsistent/results.json`, all 8
verdict branches re-analyzed, scorecard re-rendered. `plan_digest` and
`prereg_digest` are **unchanged** (cells and the frozen constants did not
move — only `registry_digest` + stamp did), and the tamper branch still
resolves `winner none / decision_reason tamper-invalid`. Six-regen moved the
projection stamp `catalog:1d520797652a` → **`catalog:95747f71f9d8`**
(architect card now `gates: build`); workspaces rebuilt. Selftest 20/0 ×2
byte-identical; all four arm configs 29/0. The stale line in
`ir-gate-arm-role-ownership.md` ("exit gates stay build + tests") is corrected
to match.

**Standing lesson:** a role's declared gate set must be satisfiable *at that
role's position in its arm's sequence*, on every family the arm runs. A gate
that can only pass after a later stage is a structural defect, and only a live
run on the worst-case family surfaces it — which is precisely why the pricing
pass ran before the study, not after.

### Addendum, same day — F7: the hardener's write scope vs the Maven layout

The F6 acceptance re-run (greenfield-1 × arm C, r1) got four stages further
and then failed at the **hardener** on `CHK-SCOPE` — the *same class* of bug in
the scope dimension. The hardener's job is to strengthen tests, so it wrote to
`src/test/java/…` (Maven), but its `write_scopes` were `[tests/, specs/]`; the
retro scope lint flagged a *legitimate* write as out-of-scope. The roles that
already worked (maker3, checker3, coder, cleaner, qa, solo) all carry `src/`,
which covers `src/test/`; the hardener alone did not — and it must stay
tests-only (no `src/` production access).

**Static audit before the fix** (all nine roles, scope vs Maven paths each must
write): the hardener was the **only** uncovered case — so this is the last
structural role/workspace mismatch, not a whack-a-mole. **Change:** hardener
`write_scopes` → `[src/test/, tests/, specs/]` (adds the Maven test path, keeps
it tests-only). Same tax: kata stamp `kata:0628e6306595` →
**`kata:a6f56755e9b0`**, projection `catalog:95747f71f9d8` →
**`catalog:cabd69051aa2`**; `plan_digest`/`prereg_digest` unchanged; tamper
branch preserved; selftest 20/0 ×2; configs 29/0.

**Broadened lesson:** a role's declared *capabilities* — gates AND write
scopes — must match the *concrete workspace layout* it runs against. The role
registry was authored against a flat `tests/` layout; the kata workspaces are
Maven `src/test/`. Two roles (architect gate, hardener scope) encoded that
stale assumption, and only a live run on the family that exercises the full
sequence surfaced each. The static cross-check of every role against the layout
is now the cheap guard that should precede any future arm/role change.
