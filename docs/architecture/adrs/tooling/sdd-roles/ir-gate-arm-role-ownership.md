---
type: guide
title: IR-gate arm/role ownership — new gate id vs ADR vs checkers
description: >-
  Ownership guide for closing the battle-test finding that o7's IR gate is a
  first-class "MUST run first" gate no role in the sdd-roles kernel can declare.
  Separates kernel gate vocabulary from role work (specifier law, architect ADR,
  maker implementation, hardener/qa verification) and maps Arms A/B/C/C-dbg.
tags: [sdd-roles, o7, ir-gate, guide, roles, arms, ownership]
status: ratified-by-adr-0005
supersedes: none
adr: ./0005-ir-gate-first-class-gate-vocabulary.md
sourced_from: sdd-roles battle-test report (Architect workspace eval artifact; not vendored here)
---

# IR-gate arm/role ownership guide

**Status:** ratified by
[ADR 0005](./0005-ir-gate-first-class-gate-vocabulary.md) (2026-08-09), which
freezes the gate id, the `ir-gate-checker` tool pin, the
`ir_gate_violations_max: 0` threshold, and the declaration table below.
Originally a proposed guide capturing the ownership decision shape after the
sdd-roles battle-test on the o7 IR-gate slice.
**Date:** 2026-08-09. **Kernel:** sdd-roles 1.4.0 (gate vocab now
`{build, tests, crap, mutation, ir-gate}` per ADR 0005; the checker tool is
**built** at `tooling/sdd-roles/tools/ir-gate-checker/` (1.0.0), with
`CHK-IRGATE-PIN` (validator 0.7.0) redding any aliased binding; productive
runs additionally need the per-run KernelConfig `ir-gate` →
`ir-gate-checker` binding row).

**One-line claim:** IR gate must become a **new first-class gate id** in the
kernel. Roles **author law, decide structure, implement, and verify** it —
prose in a role body is not enough.

---

## Why this guide exists

The battle-test's highest-value design finding:

> o7's IR gate is a first-class "MUST run first" gate that no role in the
> current kernel vocabulary declares.

o7 already requires (ubiquitous): the IR gate runs **first**, pre-device, with
**zero device cost and zero compilation**, rejecting on any of its seven checks
(`schemaValid`, `opcodeClosed`, `boundedWaits`, `locatorManifest`,
`noLiteralCreds`, `ambiguityClear`, `dryRun`) — then enqueue → interpreter
(`docs/sdd/specs/mobile-test-automation-o7-interpreter.spec.md`). Grep across
`tooling/sdd-roles/kernel/` + `validator/src/` for those check names was **0
hits** at battle-test time.

Without a gate id, an Arm C run can go green on `build` / `tests` / `crap` /
`mutation` while never requiring o7's real trust boundary before Perfecto spend.

---

## Split three things people mix up

| Thing | What it is | Who owns it |
|-------|------------|-------------|
| **Gate id `ir-gate`** | Machine exit check the runner can require | **Kernel / KernelConfig** (vocabulary + allowlisted tool) |
| **IR-gate checker (code)** | The program that runs the seven checks | **Makers** (coder / maker3 / solo) under `src/` |
| **Law that says it MUST run first** | Specifier scenarios + o7 EARS | **Specifier** (humans amend the law) |

Do **not** fold IR gate into `tests` or `build`. o7 deliberately replaced
compile/Checkstyle with a **pre-device, no-compile** gate. Mapping it to `build`
lies about the architecture; mapping it only to `tests` loses the "MUST run
first before device" semantics.

---

## Who does what (by role)

### Specifier — owns the exam, not the checker

- Writes scenarios: bad opcode / missing locator / literal cred / ambiguity →
  IR gate fails, outbox empty; good sealed IR (e.g. Alex Rivera Zelle shape) →
  gate passes, enqueue allowed.
- Supplies example tables hardener can mutate.
- Keeps `gates: []` — specifier does not declare stage-exit gates and does not
  write `src/`.

### Architect — owns the boundary decision (ADR), not the night watch

- Records: gate module ≠ interpreter ≠ outbox; dependency rule (interpreter
  must not import authoring/LLM paths); `healPolicy: NONE` is a determinism
  control, not a style preference.
- Exit gate is `build` only (**amended 2026-08-10, ADR 0004**: the architect
  precedes the coder who writes the suite, so a `tests` gate here is
  structurally unsatisfiable on greenfield/bugfix — it shed `tests`). Do not
  add `ir-gate` to architect either (usually **no** — architect shapes; makers
  implement; checkers prove).
- Related fitness (ArchUnit: no per-test generated Java / no model on replay)
  is a **separate** future gate id — do not overload `ir-gate`.

### Coder / Cleaner (or Maker3) — own building and tidying the checker

- Coder: implement the seven checks; wire "gate pass → outbox".
- Cleaner: structure-preserving decrap of the gate module.
- After vocabulary lands: **coder / maker3 declare `ir-gate`** so the stage
  cannot hand off "I wrote a gate" without the gate tool going green on
  fixtures.

### Hardener — owns strengthening proof that the gate means something

- Mutate the checker and example tables; kill always-pass mutants
  (e.g. `noLiteralCreds` short-circuit).
- Does **not** replace `ir-gate` with `mutation` — mutation proves the suite;
  `ir-gate` proves the sealed map.
- Optional: also declare `ir-gate` if hardening can change gate behavior.
  Default preference: hardener keeps `tests` + `mutation`; a later checker
  re-runs `ir-gate`. Pick one and record it in the ADR.

### QA / Checker3 — own independent verification of the pipeline path

- Drive sealed fixtures through IR gate; confirm no device acquire on red.
- Confirm enqueue respects the gate (green report ignored by outbox is a
  wiring defect, not a soft pass).
- Should declare **`ir-gate`**. Device week-gate / Perfecto walk is a **later**
  harness (`device-walk`), not the same gate.

### Solo

- Declares **all** gates including the new `ir-gate` (same pattern as today's
  four).

---

## By arm (same o7 IR-gate job)

### Arm A — Solo

Solo writes law, builds checker, runs `ir-gate` + other gates, verifies the
path.

| Gain | Cost |
|------|------|
| Fast | Same brain authored "MUST run first" and grades it |
| Mechanical `ir-gate` still fail-closes | Softening temptation remains |

### Arm B — Specifier → Maker3 → Checker3 (practical default)

```
specifier          maker3                         checker3
  law         build checker + tidy           mutation + path verify
              gates: build, tests, crap,     gates: tests, mutation,
                     ir-gate                        ir-gate
```

- Maker3 cannot finish without `ir-gate` green on fixtures.
- Checker3 re-runs `ir-gate` and verifies enqueue / no-heal path.
- No separate architect stage — still write the seal/outbox ADR by hand if the
  boundary is new.

### Arm C — Full line (closest to o7's philosophy)

```
specifier → architect → coder → cleaner → hardener → qa
   law        ADR         implement  tidy     strengthen   independent path
                         + ir-gate*           mutation      + ir-gate
```

\*Put **`ir-gate` on coder (and/or cleaner) and on qa**.

- Coder: checker exists and passes fixtures.
- QA: still passes when an independent operator drives the sealed path.
- Hardener: focus on `mutation`; optional `ir-gate` after test changes.

### Arm C-dbg — Arm C without QA

Same as C through hardener. **`ir-gate` on coder still required.**

Without QA you lose independent "did enqueue actually honor the gate?"
C-dbg measures whether QA was load-bearing for wiring lies (green gate
report, ignored outbox).

---

## Recommended `ir-gate` declarations (draft registry sketch)

**Applied** to live catalog
`tooling/sdd-roles/kernel/catalog/role-registry.json` on 2026-08-09
(defaults below) and frozen by
[ADR 0005](./0005-ir-gate-first-class-gate-vocabulary.md): a KernelConfig
`gates[]` row for `ir-gate` MUST bind `tool: "ir-gate-checker"` with threshold
`ir_gate_violations_max: 0`. The checker tool is not yet built — productive
runs refuse at gate-runner preflight, fail-closed, until it exists.

| Role | Declare `ir-gate`? | Rationale |
|------|--------------------|-----------|
| specifier | no | No stage-exit gates |
| architect | no (default) | ADR owner, not gate runner |
| coder | **yes** | Built the checker; stage exit |
| cleaner | no | Tidies only; re-prove left to coder/qa |
| hardener | no | Mutation focus; optional later via ADR |
| qa | **yes** | Independent path verify |
| maker3 | **yes** | Arm B implement+tidy exit |
| checker3 | **yes** | Arm B harden+verify exit |
| solo | **yes** | Carries every stage's evidence |

---

## Decision tree (what to do first)

1. **Kernel:** add gate id `ir-gate` + allowlisted backing tool (new vocabulary —
   battle-test highest-value finding).
2. **Specifier:** scenarios that only `ir-gate` can satisfy.
3. **Architect:** ADR — gate before outbox; `healPolicy: NONE` is determinism
   law; reject folding into `build`/`tests`.
4. **Coder / Maker3:** implement checker; stage exit includes `ir-gate`.
5. **QA / Checker3:** re-run `ir-gate` + path verify.

**Related but separate later gate ids** (do not overload `ir-gate`):

| Future gate | Why separate |
|-------------|--------------|
| `ir-conformance` (C3) | Corpus before pinning `interpreterVersion` |
| `fitness` / ArchUnit | No per-test generated Java / no model on replay path |
| `device-walk` | Real Perfecto week-gate clause (a) |

---

## Anti-patterns

| Anti-pattern | Why it fails |
|--------------|--------------|
| Only add prose to `qa.md` / `hardener.md` | Doctrine without a gate id is unenforceable by `gate-runner` |
| Map IR gate → `build` | o7 path has **zero compilation** |
| Map IR gate → `tests` only | Unit green ≠ "MUST run first before device" |
| Give IR gate only to hardener | Pre-enqueue law is a pipeline gate, not only mutation |
| Specifier "owns" the gate tool | Specifier has no gates and must not write `src/` |

---

## Practical pick

| If you want… | Do this |
|--------------|---------|
| Fastest honest adoption | **Arm B** + `ir-gate` on **maker3** and **checker3** |
| Closest to o7's philosophy | **Arm C** + `ir-gate` on **coder** and **qa**, ADR from **architect**, law from **specifier** |
| Measure QA's value | Ship Arm C, compare to **C-dbg** with `ir-gate` still on coder |

**Bottom line:** ownership is **shared by stage**; authority is the **new gate
id**. Specifier writes that it must run first; makers build the checker;
checkers prove it; the **kernel** is what makes "done" impossible without it.

---

## Follow-ons (out of this guide's scope)

- ~~Draft / Accept a numbered ADR in this series (likely 0005) that freezes the
  gate-id name, role declaration table, and reject-alternatives above.~~ Done:
  [ADR 0005](./0005-ir-gate-first-class-gate-vocabulary.md) (2026-08-09), which
  also updated the five declaring roles' doctrine bodies, regenerated the
  projections, and restamped the kata instrument (ADR-0004 amendment).
- Spec + plan the checker tool and KernelConfig allowlist entry.
- Do not claim battle-test [D] risks closed until Copilot live / kata tooling /
  cursor headless seams are real (battle-test report §5).
