---
type: architecture
title: 'ADR 5. `ir-gate` is first-class kernel gate vocabulary, pinned to one checker tool'
description: 'Add first-class kernel gate id ir-gate so o7''s IR gate is declarable in role stage exits without folding into build/tests.'
tags: [architecture, adr]
---

# ADR 5. `ir-gate` is first-class kernel gate vocabulary, pinned to one checker tool

## Status

Accepted
<!-- Accepted 2026-08-09 on owner direction ("complete the adoption") after the
ir-gate ownership review. The guide's registry sketch had been applied ahead of
kernel vocabulary (registry-first); the review measured the half-applied state
(selftest 18/2; all four arms refusing preflight; 39 stale projection paths;
kata plan golden diverged) and this ADR completes the change atomically:
registry declarations (already applied) + doctrine bodies + regenerated
projections + kata instrument restamp. Build gate: selftest 20/20 ×2
byte-stable at 1.4.0 / 0.6.0. Fifth ADR of the tooling/sdd-roles series;
ratifies docs/architecture/adrs/tooling/sdd-roles/ir-gate-arm-role-ownership.md
and closes the battle-test's highest-value design finding.
Checker build item landed 2026-08-09 (same day, later session): tool
tooling/sdd-roles/tools/ir-gate-checker/ at 1.0.0 (8-case fixture corpus,
own selftest green x2) + CHK-IRGATE-PIN in the validator (27th invalid
family; validator 0.7.0). Gate re-confirmed: selftest 20/20 x2 byte-stable
at 1.4.0 / 0.7.0. -->

## Context

The battle-test's highest-value finding: o7's IR gate is a first-class "MUST
run first" gate that no role in the kernel vocabulary declared — the gate vocab
was closed at `{build, tests, crap, mutation}`, and an Arm C run could go green
on all four while never crossing o7's real trust boundary before device spend.

The ownership guide (`ir-gate-arm-role-ownership.md`) proposed the split:
specifier writes the law, architect records the boundary, makers build and
declare the checker, checkers re-prove it, and the kernel — not prose — makes
"done" impossible without it. Its registry sketch was applied to the live
catalog on 2026-08-09 ahead of the kernel work. The review of that state
established two mechanical facts that shape this decision:

1. **Declarations are retro-lint law immediately.** CHK-EVIDENCE is
   gate-id-agnostic: any run whose registry declares `ir-gate` cannot mark a
   stage `complete` without a green, hash-intact `ir-gate` outcome. No
   validator change is needed for enforcement-after-the-fact.
2. **Declarations without a bound tool refuse to start, fail-closed.** The
   gate-runner preflights every declared gate id against KernelConfig
   `gates[]`, a named threshold, and the tool allowlist; probes confirmed all
   four arms refuse (`gate 'ir-gate' has no KernelConfig gates[] row`) and a
   discrimination control (declarations stripped) passes preflight. A third
   probe showed the hole this ADR must close by law: a config row binding
   `ir-gate` to *any* allowlisted tool passes preflight — the config-level
   version of "map the IR gate to `tests`".

Alternatives considered:

- **Fold into `build`** — o7 deliberately replaced compile/Checkstyle with a
  pre-device, zero-compilation gate; mapping it to `build` lies about the
  architecture. Rejected.
- **Fold into `tests`** — loses the "MUST run first, before device" semantics;
  unit-green is not enqueue-permission. Rejected.
- **Hardener-only ownership** — pre-enqueue law is a pipeline gate; mutation
  proves the suite, `ir-gate` proves the sealed map. Rejected.
- **Prose-only doctrine in role bodies** — unenforceable by the gate-runner;
  the exact anti-pattern the guide names. Rejected.
- **Gate id without a pinned tool** — measured alias hole above; the path of
  least resistance under schedule pressure would be aliasing `ir-gate` to an
  existing tool. Rejected.

## Decision

**1. `ir-gate` is kernel gate vocabulary.** The registry declarations are
frozen as applied: **coder, qa, maker3, checker3, solo declare it; specifier,
architect, cleaner, hardener do not.** Specifier has no stage-exit gates;
architect owns the boundary ADR, not the night watch; cleaner is
structure-preserving with re-proof owed by coder and qa. **Hardener's "no" is
the ADR-recorded pick** the guide required: hardener keeps `tests` +
`mutation`; if hardening ever changes gate behavior, adding `ir-gate` to
hardener is an amendment to this table, not a silent registry edit.

**2. One backing tool, pinned.** A KernelConfig `gates[]` row for `ir-gate`
MUST bind `tool: "ir-gate-checker"`, and `ir-gate-checker` must appear in
`gate_tool_allowlist`. Binding `ir-gate` to any other tool id violates this
ADR. Mechanical enforcement (a validator check plus a corpus invalid-family
case that reds an aliased binding) ships with the checker build item — the
check needs the tool's report contract to assert against; until then the pin
is ADR law, held by review. **Landed 2026-08-09:** `CHK-IRGATE-PIN`
(validator 0.7.0) reds an aliased binding at both layers — a KernelConfig
`gates[]` row and a gate outcome — with corpus cases `aliased-config` and
`aliased-outcome`.

**3. Threshold.** The row names threshold `ir_gate_violations_max` with value
`0`: the gate rejects on any failed check among the seven (`schemaValid`,
`opcodeClosed`, `boundedWaits`, `locatorManifest`, `noLiteralCreds`,
`ambiguityClear`, `dryRun`); the report enumerates per-check outcomes. The
runner requires a named threshold for every gate row — this is `ir-gate`'s.

**4. Checker contract (specified here, not built).** Pre-execution,
zero-compilation, zero-device-cost; consumes the sealed IR and locator
manifest; exit 0 green / 2 red / 3 usage, with descriptor exit-code maps
carrying the 2 and 3 translations; the report JSON must carry `tool_version`
(the runner refuses reportless or versionless outcomes). Building the checker
is maker work under the guide's role split; the battle-test's [D] risks stay
open until it is real.

**5. Catalog scope.** The catalog registry is **o7-first**. Non-o7 conveyor
runs pin their own registry copy via `--registry` (runs are self-contained).
The kata study consumes the catalog registry by design, so registry edits
restamp the kata instrument: this ADR performs that restamp as a visible
ADR-0004 **amendment** — plan, the eight results files' `plan_stamp`, the
eight verdict goldens, the scorecard, and the `results-inconsistent` failure
fixture. `PREREG_CONSTANTS` are untouched; the digest triangle holds.

**6. Doctrine agrees with contract.** The five declaring roles' bodies name
`ir-gate` in their stage-exit law (solo: five gates, not "all four"), and the
projections are regenerated in the same change, so no emitted card ships with
its Contract and Doctrine sections disagreeing about what "done" means.

## Consequences

- **All four arms refuse to start** until a productive KernelConfig binds
  `ir-gate` → `ir-gate-checker`. That is intended backpressure, not an
  outage: claiming "done" without o7's trust boundary is now mechanically
  impossible, which is the point — and nothing runnable was lost today,
  since crap4java/mutate4java are equally absent (R-KATA-STUDY). *(2026-08-09,
  checker landed: the tool now exists at
  `tooling/sdd-roles/tools/ir-gate-checker/`; the remaining condition is the
  per-run KernelConfig binding row.)*
- CHK-EVIDENCE enforces the declarations on any run carrying this registry
  from now on; complete-without-green-`ir-gate` is a red finding today.
- ~~The alias hole remains mechanically open until the checker's validator
  check lands; it is a named residual, mitigated by the tool-id pin above.~~
  Closed 2026-08-09: `CHK-IRGATE-PIN` reds aliased bindings mechanically at
  the config-row and gate-outcome layers.
- Every future gate-vocabulary change pays the kata restamp cost, because the
  plan pins the registry bytes. Lesson recorded: **ship vocabulary changes
  atomically with their tools** — the registry-first sequencing reviewed here
  red-flagged the kernel's own gate for a session and is not the pattern.
- Related but separate future gate ids stay separate (do not overload
  `ir-gate`): `ir-conformance` (C3 corpus release gate), `fitness`/ArchUnit
  (no per-test generated code, no model on the replay path), `device-walk`
  (the real Perfecto week-gate).
