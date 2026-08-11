---
name: coding-rules
description: >-
  REQUIRED before touching Java/Spring Boot code in the o1 pipeline repo —
  code written, placed, or reviewed without it will violate the repo's 18
  binding coding rules (CR-01–CR-18). Load it FIRST, before answering,
  whenever the user is: implementing or sanity-checking anything in o1
  (adapters, seams, modules, transactional outbox, lineage/checkpoint
  writes, model gateway, replay logic); asking what a CR-xx rule requires;
  deciding where new classes or packages belong; reviewing a commit, diff,
  or PR for cleanliness; classifying gaps between a spec and the built
  code; or turning sdd-converge findings into fix tasks. If the request
  involves writing, placing, reviewing, or reconciling o1 code in any way,
  invoke this skill even when the user never says "coding rules". Not for
  general architecture education or book summaries, build/dependency
  failures, spec or acceptance-criteria authoring, or pre-spec
  brainstorming.
---

# o1 Coding Rules — front-end (Claude)

**The rules live in one place:** `{{rules_home}}/rules-catalog.md`
(default `docs/coding-rules/rules-catalog.md`). ArchUnit/PMD/migration
seeds: `{{rules_home}}/archunit-seeds.md`. Binding keys: `[coding-rules]`
in `.sdd/binding.toml`. If the workspace install is absent (no
`docs/coding-rules/` and no binding), fall back to the `references/`
directory bundled beside this SKILL.md, and treat module/package
placeholders as unresolved (ask, don't guess). This file is a pointer —
never restate or fork rule content here.

## Protocol

1. **Resolve the binding**, then read the catalog's header (how-to-apply +
   override table) and the rule groups the task touches:
   - any new class/package → **A** (structure)
   - model / storage / external-system calls → **B** (seams)
   - `domain`/`usecase` code → **C** (core purity)
   - state, lineage, queues, LLM output → **D** (data & flow)
   - tests, metrics → **E**
2. **Implementing** (with sdd-implement): rules constrain the shape of the
   green code; red/green and small-diff discipline stay with sdd-implement.
   If a rule forces a design the task list didn't anticipate, that's a
   legitimate re-plan trigger, not a reason to waive the rule.
3. **Reviewing / converging** (with code-review or sdd-converge): tag every
   violation finding with its rule ID (`CR-05`). A mechanical-rule violation
   found by eye = two findings: the violation + the missing/disabled
   ArchUnit gate. CR-16 violations are security findings. Verify behavior,
   not just shape (catalog: "Shape is necessary, not sufficient") — a
   well-shaped no-op adapter, hardcoded pinning literals, or a silent stub
   on an audit path is a finding even when the placement is compliant.
   Review reports open with a top-3 triage frame; converge reports use the
   canonical labels missing/partial/contradicts/unrequested with a
   structured `Type: <label> (ACn). Severity: <sev>.` header per finding
   (DEFECT/STANDARDS as secondary tags).
4. **Precedence:** ADR > catalog > book. Never "fix" code toward the book
   against a decided ADR (the catalog's override table lists the five known
   conflicts). Proposing a new rule or threshold change → route to an ADR /
   catalog PR, don't improvise per-diff.
