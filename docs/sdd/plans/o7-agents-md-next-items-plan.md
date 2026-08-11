---
type: plan
title: o7 / spine AGENTS.md — next-items plan (post 2026-08-09 research + seeds)
description: >-
  Cold-session-executable plan for the work remaining after the 2026-08-09
  AGENTS.md external research, the three ArchUnit seeds (F-1..F-3), and the
  spine T01 amendment A1. Covers the dangling coding-rules reference, the
  unresolved binding, the no-registry enforcement decision, the open stack
  dimensions, the three o7 field-shape conflicts, and the two external
  dependencies. This is a WORK-HANDOFF plan, not an SDD spec-to-plan artifact
  — it derives no tasks for o7 and closes no gate.
date: 2026-08-09
updated: 2026-08-09
status: complete for now — 8 of 9 closed, I6 parked by owner; AGENTS.md final at v1.0.0
progress: I1-I5 + I7-I9 ✅ CLOSED (amendments A2-A5; ADR 0016 residual-risk + D7). I6 ⏸ PARKED by owner 2026-08-09 — safe only while o7 is out of scope; UNPARK BEFORE THE o7 GATE CLOSES or the first run quarantines. AGENTS.md content FINAL at v1.0.0 / 247 lines. Sole remaining owner input: #6 attribution-trailer policy.
research_report: ../../research/o7-agents-md-external-research.md
agents_md_draft: mobile-test-automation-spine.AGENTS.md
spine_tasks: mobile-test-automation-spine.tasks.md
spine_plan: mobile-test-automation-spine.plan.md
o7_spec: ../specs/mobile-test-automation-o7-interpreter.spec.md
archunit_seeds: ../../../tooling/coding-rules-skill/references/archunit-seeds.md
---

# o7 / spine AGENTS.md — next items

## 0. Read this first (state of the world, 2026-08-09)

**Nothing is implemented.** There is no spine repository, no Java source, no POM,
no schema, no IR gate, no DB migration. Everything below is documents and
decisions. If you find yourself writing Java, stop — you have misread the state.

**Two gates are open.** Neither closes by any item in this plan:

| Gate | State |
|---|---|
| Spine task board | **awaiting TASKS-OK** (`spine.tasks.md:149`). The *plan* has PLAN-OK 2026-07-28; the *tasks* do not. |
| o7 Stage-2 sign-off | **open**, **two** signatures pending — owner, plus the designated security owner for ADR 0017 |

**ADR statuses, verified 2026-08-09:** 0016 **Proposed**; 0017 **Proposed**
(2026-08-05, same gate as 0016); 0011 **Proposed** — acceptance blocked on the
week-0 platform probe. 14 of 17 mobile-test-automation ADRs are Accepted.

**Two standing assumptions that are not facts.** PostgreSQL is a working
assumption pending bank-catalog confirmation; ADR 0011 object storage is
PROBE-PENDING with a MinIO default. Either resolving against us is an **sdd-replan
event, not a silent patch** (`spine.plan.md:7`).

## 1. What was produced 2026-08-09 (do not redo)

| Artifact | Path | State |
|---|---|---|
| External research report | `docs/research/o7-agents-md-external-research.md` | 418 lines, 10 sections. All 28 completeness-critic corrections applied **in the body**, not as errata. §5 carries a correction box; §9 Q1/Q2/Q3 are marked ANSWERED. |
| AGENTS.md — **FINAL v1.0.0** | `docs/sdd/plans/spine-repo/AGENTS.md` | **247 lines / 14.1 KB**, a literal file (211/11.4 delivered → 218 after I1+I3 → 237 after I4 → 247 final). Copied verbatim by T01 with `spine-repo/CLAUDE.md`. The `---8<---` marker convention is **retired** (A6); `mobile-test-automation-spine.AGENTS.md` now holds provenance + change log only. Content final; board still awaits TASKS-OK, so **not yet landed**. |
| ArchUnit seeds F-1…F-3 | `tooling/coding-rules-skill/references/archunit-seeds.md` §F | New section + F-1b/F-3b/F-3c. Frontmatter retitled to cover o1 **and** o7. Two blind spots recorded in the review channel. |
| Spine board amendments | `docs/sdd/plans/mobile-test-automation-spine.tasks.md` | **A1–A5**, all 2026-08-09, all pending TASKS-OK. A1 `AGENTS.md`+`CLAUDE.md` (T01) · A2 coding-rules bundle install (T01) · A3 B-5 no-registry (T02) · A4 resolved binding replaces the template (T01) · A5 stack pins for the POM (T01). Each has its own visible amendment section; none closes a gate. |

**Operational note.** `tooling/coding-rules-skill/dist/coding-rules/references/`
is a byte-identical manual mirror of `references/`, and `dist/coding-rules.skill`
is a plain zip of `dist/coding-rules/`. There is **no build script**. After any
`references/` edit, copy into the **`references/` subdirectory** — the mirror is
*not* flat, and `cp … dist/coding-rules/` silently adds a fifth stray file
(observed 2026-08-09):

```bash
cp references/<file> dist/coding-rules/references/
cd dist && rm -f coding-rules.skill && zip -rqD coding-rules.skill coding-rules -x '.DS_Store' -x '*/.DS_Store'
```

The `-D` matters — it reproduces the original 4-file, no-directory-entry archive
shape. Verify with `unzip -l dist/coding-rules.skill`: **4 files, no directory
entries.** A 5-file listing means the copy landed in the wrong place.

## 2. Items

Ordered by dependency, not importance. Each says what blocks it.

### I1 — Close the dangling coding-rules reference (T01 amendment A2) — ✅ DONE 2026-08-09

> **Executed.** Amendment **A2** landed in `spine.tasks.md` (T01 row tagged
> `[A2 2026-08-09]`, verify column extended, amendment section written in the A1
> style). Steps 3–5 of `INSTALL.md` were deliberately **excluded** — per-agent
> front-ends (`.claude/skills/`, `.cursor/skills/`, `.github/instructions/`) would
> recreate the competing-instruction-file condition T01 asserts against, and
> `AGENTS.md` is the spine's single instruction file per A1. Step 6 is T02's.
> `AGENTS.md` §Reading was corrected in the same pass: the "first three missing =
> bundle not installed, ask" fallback now reads as a scaffold-incomplete signal
> rather than the expected path, and states that unresolved `[coding-rules]`
> placeholders are intended at T01 (I2 resolves them).

**Defect.** `AGENTS.md` names the CR-xx catalog as authority #3 and its pointer
table sends agents to `docs/coding-rules/rules-catalog.md` and
`docs/coding-rules/archunit-seeds.md`. **Nothing in T01 installs them.** This is
the exact failure microsoft/apm#695 documents — instructions pointing at a file
that does not exist. The draft carries a fallback ("first three missing = bundle
not installed; ask") but that is mitigation, not a fix.

**Do.** Amend T01 to add steps 1–2 of `tooling/coding-rules-skill/INSTALL.md`:
copy `rules-catalog.md` + `archunit-seeds.md` into `$SPINE/docs/coding-rules/`,
and append `binding.template.toml` into `$SPINE/.sdd/binding.toml`. Record it as
**Amendment A2** in the same visible style as A1 — do not edit the row silently.
*(Superseded in part by **A4**: T01 installs the resolved
`mobile-test-automation-spine.binding.toml`, **not** the template — see I2.)*

**Verify.** T01 verify column gains: `docs/coding-rules/{rules-catalog,
archunit-seeds}.md` present at repo root; `.sdd/binding.toml` contains a
`[coding-rules]` section.

**Blocked by.** Nothing. Two-line change plus an amendment note.
**Recommendation: DO IT.** It is the only defect in the delivered set that makes
`AGENTS.md` actively misleading rather than merely incomplete.

### I2 — Resolve the `[coding-rules]` binding — ✅ DONE 2026-08-09

> **Executed.** Owner supplied `base_package = "com.bank.spine"`; every remaining
> value was derivable from the approved plan §2 tree + ADRs, so the binding is
> resolved, not placeholder-filled. Landed as
> `mobile-test-automation-spine.binding.toml` (this directory) and Amendment
> **A4** — T01 now installs **that**, not `binding.template.toml`, whose defaults
> were wrong for the spine in four places (three modules not six;
> `evidence.storage` not `objectstorage`; an `ingestion.adapter.internal` package
> the approved tree does not have; async seams naming neither spine package).
>
> **Three latent seed defects surfaced only once a binding was resolved against
> them** — the argument for doing this before T01, not during it:
> 1. `" | "`-joined multi-glob strings match no package, and in `noClasses()`
>    *exclusion* position that **widens** D-2/B-2 to the whole build, so the
>    legitimate seam code fails first and looks like a false positive.
>    Multi-glob keys are now TOML arrays + plural ArchUnit predicates.
> 2. B-1 referenced `{{provider_sdk_packages}}`, matching **no binding key**,
>    while hardcoding a parallel copy of the same list. It worked by accident;
>    adding the Phase-2 gateway SDK to the binding would silently not have been
>    enforced — on F1, load-bearing.
> 3. Those values were bare roots with no trailing `..`, inert until (2) was
>    fixed, then silently under-banning.
>
> All fixed in `archunit-seeds.md` **and** `binding.template.toml` (so the o1 arm
> benefits), dist mirror + `.skill` rebuilt. **No re-check needed: owner confirms
> no o1 workspace exists yet**, so all three were caught before first install.
>
> **Three values stay CHANGE-ME by design**, each naming what to ask:
> `invoke_models_adapter` (reserved/empty — the spine makes no model call, so B-1
> correctly reads as "no provider SDK anywhere" today), the second
> `async_seam_packages` entry (ADR 0007's human-review seam is out of spine
> scope), and the Phase-2 gateway SDK.

### I2 (original text) — Resolve the `[coding-rules]` binding

**State.** The workspace `.sdd/binding.toml` has **no** `[coding-rules]` section
(verified: zero matches). So `{{base_package}}`, `{{rules_home}}` and every seam
glob are unresolved — which is why seeds F-1…F-3 carry placeholders and why
`AGENTS.md` marks package paths UNRESOLVED.

**The gap is narrower than it looks.** Package *names* are decided —
`ADR 0005:69-75` retains `ingestion`, `hierarchy-tool`, `conversion`, `replay`,
`certification`. What is missing is the **base package** and the **seam globs**.

**Do.** Get the base package from the owner (no value for it exists anywhere in
the repo — do not invent one; the skill's own rule is "ask, don't guess"). Then
fill the template's table: `seams.invoke_models_adapter`,
`seams.storage_port_adapter`, `seams.source_adapter_packages` (+ `_internal_`),
`seams.async_seam_packages`, `seams.provider_sdks.packages`. Leave
`thresholds.*` at defaults — changing one is an ADR-level decision.

**Blocked by.** Owner (base package). Also I1/T01 in practice — the binding lives
in the spine repo, which does not exist.

### I3 — Decide where the no-registry rule lives — ✅ DONE 2026-08-09 (owner chose (a))

> **Executed as option (a).** Landed as Amendment **A3** on the T02 row
> (`spine.tasks.md`), on `plan:14` authority with **no dependency on ADR 0017**.
> Consequential edits: `archunit-seeds.md` gains **B-5** in the o1/spine class
> (three CR-08 seams — source adapters, Invoke Models, storage port); seed F-1 is
> narrowed to `{{seam.driver_adapter_packages}}` alone and renamed
> `driver_seam_bound_by_spring_di_not_by_a_registry`; a split note in §F forbids
> re-merging them; review-channel item 1 now records that F-1b's name heuristic is
> **driver-seam only**, so the spine arm's blind spot is wider. `AGENTS.md` Never
> block: enforcer `**none today**` → ArchUnit B-5 / T02, and the DoD step-2 line
> now reads `F1–F4 + module boundaries + B-5`. `dist/` mirror + `.skill` zip
> rebuilt (4 files, verified). **`Enforcer: none` entries drop from three to two**
> — the fitness-function guard and the hash-before-read ordering rule remain.

**The tension.** Seed **F-1** (no plug-in registry at the seams) currently sits in
the **o7** section of `archunit-seeds.md`, sourced from ADR 0017 — which is
Proposed. But `spine.plan.md:14` states the same principle at **spine** level and
is **approved**: *"No registry, no plug-in machinery. Source adapters are
Spring-selected implementations of one interface."*

Checking that line closely sharpens the point: it says *"F1/F2 ArchUnit rules are
the boundary"* — but F1 and F2 guard **what crosses a seam**, not **how an
implementation is bound to it**. A `ServiceLoader`-based registry passes both.
**So nothing enforces this today**, and `AGENTS.md` currently says so.

**Options.** (a) Promote a spine-scoped no-registry rule into **T02** now,
justified by plan:14 alone with no dependency on ADR 0017. (b) Leave it a review
obligation until the o7 gate closes.

**Recommendation: (a).** The principle is already approved at plan level; the
enforcement gap is real today, not on gate closure; and it removes one of only
three `Enforcer: none` entries in the Never block. If taken, update the F-1
citation in the AGENTS.md draft from `**none today**` to name T02, and move a
spine-scoped copy of the seed out of the o7-gated §F.

**Blocked by.** Nothing. Owner call on scope.

### I4 — Settle the open stack dimensions before T01 writes the POM — ✅ DONE 2026-08-09

> **Executed as Amendment A5** on T01, plus the AGENTS.md Stack table (which no
> longer carries a stack `UNRESOLVED` block — only the attribution trailer remains).
>
> | Dimension | Decision |
> |---|---|
> | JDK distribution | **Temurin 21.0.8+**, explicitly **not Oracle JDK** |
> | Framework | **Spring Boot 4.1** — line now, exact patch pinned when T01 runs |
> | Formatter | Spotless + **palantir-java-format 2.97.0** |
> | Static analysis | **Error Prone 2.50.0 + NullAway 0.13.8 + Checkstyle** |
> | Null safety | **JSpecify** + `@NullMarked`; NullAway `ERROR` |
> | Architecture tests | **ArchUnit 1.5.0**, artifact **`archunit-junit6`** |
>
> **Two things this item got wrong, corrected on execution:**
>
> 1. **"Static-analysis set" was not fully open.** plan:69 and **T30** already
>    name Spotless + Checkstyle + Error Prone + custom Checkstyle checks, and the
>    `Thread.sleep` ban (**FP7**, a Never-block rule) *is* one of those custom
>    checks. **Checkstyle was already approved and load-bearing** — report §5's
>    "skip Checkstyle" was written before the plans directory was read, the same
>    gap that produced its Java 25 baseline. The real question was only whether it
>    also gates the spine's own source. It does; SpotBugs and PMD stay out.
> 2. **The Java 21 re-check found a decision this item did not list.** NullAway's
>    JSpecify mode targets Java 25; the Java 21 fallback needs JDK 21.0.8+ **except
>    Oracle JDK**, plus `-XDaddTypeAnnotationsToSymbol=true`. The plan pins "Java
>    21" with **no distribution**, so the vendor became a real decision — on Oracle
>    JDK the null-safety row is simply unavailable. If bank policy later mandates
>    Oracle, that is an **sdd-replan trigger for that row**, not a silent drop.
>
> **Deferred with reasons, per this item's own recommendation:** SBOM, dependency
> locking/checksums, reproducible builds and Sonar are additive and block nothing.
> **PIT is deferred on a blocker, not on cost** — whether `pitest-junit5-plugin`
> works against JUnit Jupiter 6 is unverified (§5 flags it), and gating the
> scaffold's first green run on an unverified pairing is a coin flip.
>
> **A bundle defect fixed at source.** `INSTALL.md` step 6 specified
> `archunit-junit5:1.3.0` in **Gradle** syntax; under Boot 4.1's JUnit 6 BOM the
> artifact must be **`archunit-junit6`** and the spine is Maven. **This one fails
> silently** — the wrong engine suffix discovers no `@ArchTest`, so the suite
> reports success having run nothing. INSTALL.md now carries a JUnit-version →
> artifact table, a Maven snippet, and says so explicitly.

**Decided already** (`spine.plan.md:64-73`, approved — do not relitigate):
Java 21, Maven, PostgreSQL 16 + JSONB + Flyway, Postgres outbox with
`FOR UPDATE SKIP LOCKED` (no broker), ArchUnit, Testcontainers.

**Still open:** Spring Boot version; formatter (Spotless + which formatter);
static-analysis set; null-safety annotations; mutation testing; SBOM; dependency
locking / checksum verification; reproducible-build settings.

**⚠ Re-check the research against Java 21 before using it.** Report §5 was written
recommending **Java 25**; the plan pins **21**. Most rows survive, but at least one
does not cleanly: NullAway's JSpecify mode wants Java 25, with a documented
fallback on "most JDK 21.0.8+ distributions (**except Oracle JDK**)" plus
`-XDaddTypeAnnotationsToSymbol=true`. Verify each version claim against Java 21
rather than lifting §5 wholesale.

**Recommendation.** Decide **formatter + static-analysis set** before T01 (they
shape the POM and the definition-of-done step 5, currently marked UNRESOLVED).
Defer SBOM, dependency locking and reproducible builds to a later task — they are
additive and none blocks the scaffold. Prefer a *small* analyser set; §5's
evidence is that listing five invites an agent to add all five and produce an
unrunnable build.

**Blocked by.** Owner.

### I5 — Resolve the three o7 field-shape conflicts — ✅ DONE 2026-08-09

> **Executed; all three owner-decided.** Landed as a visible **pre-gate amendment
> section** in the o7 spec (the spec is unsigned, so this corrects it *before*
> signature rather than patching an approved artifact), plus ADR 0016 and both
> o7 mocks.
> 1. **Cloud adaptivity → structured tri-state.** `cloudAdaptivity:
>    {selfHealing, perfectoAI}`, each `DISABLED` | `ENABLED` | `UNKNOWN`. The
>    split was total — spec used the boolean 9×/structured 0×, ADR 0016 the
>    reverse (3×), mock sided with the ADR. ADR wins: 0016:339-341 quarantines a
>    run "without both attestations, **or with either enabled**" — three states a
>    boolean cannot carry. `UNKNOWN` will be a *real* value, since no provider
>    offers per-session cryptographic attestation (I7). All 9 spec sites rewritten.
> 2. **`dryRun` → seventh entry inside `checks`.** Spec :33/:82/:119 + ADR
>    0016:328-329 + `ReplayReport.irGate` all say seven; `IRGate.report.json` was
>    the sole outlier and is corrected. Decisive beyond the count: outside
>    `checks`, an "all checks PASS" loop over `checks{}` silently skips it —
>    fail-open on what spec:95 calls the substrate making removal of pre-commit
>    engineer review safe.
> 3. **`gateVersion` → onto `ReplayReport.irGate`, NOT into F6.** ⚠ **This item
>    was mis-framed below.** It is not a spec-vs-mock conflict: `gateVersion` is
>    an established gate-report convention (o1 `StaticGate.report.json:6`, same
>    auditPin), and F6 governs `ReplayReport` — a different artifact. The real gap
>    was that `irGate` recorded seven verdicts while dropping the pin their
>    reproducibility rests on. Kept out of F6 because F6 has complete-or-invalid
>    teeth and is scoped to *execution* pins.
>
> **Still open, deliberately:** the attestation *posture* (I7). Decision 1 fixes
> how the answer is recorded, not how strong the evidence is.

### I5 (original text) — Resolve the three o7 field-shape conflicts

These are spec-vs-mock contradictions that determine **what validates**. They look
editorial; they are not. From report §7.5 item 6:

1. `cloudAdaptivityDisabled` (boolean, spec prose) vs
   `cloudAdaptivity: {selfHealing, perfectoAI}` (ADR 0016 + `ReplayReport.json:28`)
2. `dryRun` **inside** vs **outside** the `checks` object — `IRGate.report.json`
   has six checks in `checks` with `dryRun` a sibling at `:16`, while
   `ReplayReport.json:6-14` lists all seven flat
3. `gateVersion` (`IRGate.report.json:6`) — present in the mocks, **absent** from
   the spec's F6 set

**Recommendation.** Resolve these **before** the o7 gate closes, not after. They
are internal inconsistencies in the artifact being signed off; closing the gate
over them means ratifying a contradiction. A schema author must pick one shape
each regardless.

**Blocked by.** Owner. Not blocked by the gate — this is pre-gate hygiene.

### I6 — Confirm Perfecto Appium 3 on real devices (external) — ⏸ PARKED 2026-08-09 (owner)

> **Parked by owner decision, not closed.** Both questions stay open; nothing
> waits on them. What that means concretely:
> - **Q1 (Appium 3 real devices)** — `AGENTS.md` now carries the consequence as a
>   standing rule: **do not commit to an Appium 3 pin**, and do not infer support
>   from a session that happens to start. Costs nothing while parked.
> - **Q2 (Scriptless self-healing on code-path sessions)** — ⚠ **still gates every
>   o7 run.** `cloudAdaptivity.perfectoAI` resolves to `UNKNOWN`, which
>   quarantines, until a **written** vendor confirmation makes `NOT_APPLICABLE`
>   valid. Parking is safe **only because o7 is not yet in scope** — the Stage-2
>   gate is open and no o7 run can happen. **Unpark this before the o7 gate
>   closes**, or the first real run quarantines and records no verdict.
>
> Nothing else in the plan depends on either answer.

Report §6: Perfecto documents Appium 3 on **emulators/simulators only** (Release
25.10); real-device support is **unconfirmed and possibly blocking** for the
pinning strategy. Needs direct vendor confirmation — no amount of desk research
settles it.

**Do.** Raise with Perfecto. Until answered, do not commit to any Appium 3 pin.
**Blocked by.** Vendor. **Start now** — it is the longest-lead item here.

> **[2026-08-09] This contact now carries TWO questions — one channel.** I7 added
> the second, and it is the more urgent of the pair because it blocks *runs*, not
> just a version pin:
>
> 1. **Appium 3 on real devices** — supported, or emulator/simulator only
>    (Release 25.10)? Blocks the pinning strategy.
> 2. **Does Scriptless self-healing touch code-path Appium sessions?** A written
>    "no" is the *only* thing that makes `cloudAdaptivity.perfectoAI =
>    NOT_APPLICABLE` valid. Without it every o7 run quarantines and records no
>    verdict (ADR 0016, *Accepted residual risk*). Get it **in writing** —
>    absence of a statement is not a guarantee, which is exactly the trap
>    report §6 names.

### I7 — Record the attestation residual risk — ✅ DONE 2026-08-09

> **Executed. Posture: (b) post-run assertion, with (c) named as the escalation.**
> Recorded in **ADR 0016** (the determinism ADR) as a new *Accepted residual risk*
> section, and mirrored into the o7 spec's pre-gate amendment block.
>
> **(b)** asserts per run, from the run's own evidence (`healsApplied: NONE` + no
> healed-locator markers in the session log), that no cloud healing occurred —
> recorded explicitly as **evidence of absence, not a signed guarantee**, and
> defeasible by a vendor that heals silently. **(c) self-hosted Appium** is named
> as the escalation but not adopted: it would give up the Perfecto lab the specs
> name, making it an **sdd-replan event**. **(a) capability echo** was rejected —
> Perfecto exposes no toggle to echo.
>
> **A blocker surfaced and was resolved.** Perfecto documents self-healing as a
> Scriptless product feature with **no code-path AI toggle and no way to attest
> one**, so under I5's rule `perfectoAI` could never reach `DISABLED` and **every
> run would quarantine** — a gate that never opens, not a risk accepted. Resolved
> by a fourth state, **`NOT_APPLICABLE`**, reusing the spine's existing
> `PinnedValue` vocabulary rather than inventing one. Valid **only** with a written
> vendor confirmation on file and referenced from the report; unreferenced it is a
> schema violation, never a default and never an engineer's call.
>
> **Still open, and it gates real runs:** that confirmation does not exist. Until
> Perfecto states in writing that Scriptless self-healing does not touch code-path
> Appium sessions, `perfectoAI = UNKNOWN` and runs quarantine. **Folded into I6.**
>
> Scope note: interpreter-side self-heal was never at risk — `healPolicy: NONE`
> and hard-fail on cascade exhaustion are structural (o7 spec:98, :135), not
> attested. H10 is **not** satisfied; the ADR now records how far short the
> evidence falls and that D7's in-toto signed attestation is the closure path.

Report §6: neither Perfecto nor BrowserStack offers per-session cryptographic
attestation that AI/self-healing was disabled. Options: (a) capability echo from
session creation — weak evidence; (b) post-run assertion that the healing report
is empty — evidence of absence, not a signed guarantee; (c) self-hosted Appium —
**the only option that satisfies a hard requirement**.

Note BrowserStack is **out of scope** — the specs name Perfecto only
(`cloudAdaptivity.perfectoAI`, the C5 Perfecto epoch rule). Keep it as comparative
research.

**Do.** Pick one and record it as an accepted residual risk in the determinism
ADR. Do not leave it implied — H10 requires per-session attestation, and (a)/(b)
do not actually deliver it. **Blocked by.** Owner.

### I8 — in-toto attestation (defer, but record) — ✅ DONE 2026-08-09 (recorded as deferred)

> **Executed: deferral reaffirmed on evidence and recorded in ADR 0016's D7
> follow-on note**, which already existed but said only "not built now". It now
> carries enough to be picked up cold, so the next reader re-derives nothing:
> - **Predicate choice is genuinely open** — `test-result` is vetted but **dormant
>   since 2023-05-25**; `runtime-trace` is arguably the better fit for attesting
>   *how a run executed*; both at **v0.1**, and **no verifier tooling surfaced**,
>   so an emitter alone would produce signatures nothing checks.
> - **⚠ Guardrail recorded explicitly: SLSA v1.2 has Build and Source tracks only
>   — there is no test track.** A `ReplayReport` attestation is not a SLSA artifact
>   and must never be described as one. This is the failure mode most likely to
>   happen by accident, since "supply-chain attestation" reads as SLSA to most
>   people.
> - **What would flip the decision** is now written down: either predicate reaching
>   v1 with verifier tooling, or a hard external per-session attestation
>   requirement — and the second is *already live as unmet* (I7), with D7 named as
>   its closure path.
> - Scoped honestly as **not-found**, not proof of absence.
>
> Nothing is scoped into o7 by this. The item's own recommendation was "record as a
> known gap rather than scoping it in", and that is exactly what happened.

`test-result` predicate is vetted but **dormant since 2023-05-25**; `runtime-trace`
is arguably the better fit for "how did this run execute"; both sit at v0.1 and no
verifier tooling surfaced. SLSA v1.2 defines Build and Source tracks only — **do
not claim SLSA compliance for test runs.**

**Recommendation. Defer.** o7 would be an early adopter building both emitter and
verification policy. Record as a known gap rather than scoping it in.

### I9 — AGENTS.md length (optional) — ✅ DONE 2026-08-09 (237 accepted)

> **Executed: 237 lines accepted, no trimming.** The <200 figure is a soft
> guideline justified by token cost and review burden — **not a model limit**. The
> only ceiling that actually truncates is Codex's 32 KiB, and 13.4 KB is far under
> it.
>
> The growth is defensible line by line: I1+I3 added the numbering-scheme note and
> the B-5 enforcer citation (+7); **I4 added the largest share by replacing an
> `UNRESOLVED` ask-the-owner block with the actual pins** — which is the file doing
> its job, not bloat. A file that says "ask" costs a round trip every time an agent
> reads it; a file that says "Temurin 21.0.8+, not Oracle" costs nothing.
>
> The `Common changes` table remains the cheapest ~11 lines if a future owner wants
> it shorter — but report §3 rated that pattern **the single most transferable one
> found in real repos**, so cutting it would trade the most-proven section for a
> guideline the file is not violating in any way that matters.

**247 lines / 14.1 KB** final (v1.0.0) (211/11.4 as delivered → 218/11.9 after
I1+I3 → 237/13.4 after I4 resolved the Stack table). The I4 growth is the largest
and the most defensible: it replaced an `UNRESOLVED`-ask-the-owner block with the
actual pins, which is the file doing its job.
Against the <200 target cited in the research. The overshoot bought accurate split
repo-local / `«ws»`-prefixed paths. Still far under the only ceiling that truncates
(Codex, 32 KiB).

**Recommendation: accept 211.** 200 is a soft guideline justified by token cost
and review burden, not a model limit. If the owner wants it under, the
`Common changes` table is the cheapest 11 lines — but report §3 rated that pattern
the single most transferable one found in real repos.

## 3. Suggested execution order

1. ~~**I6**~~ → still open — fire the Perfecto question; it is the only external
   dependency and the longest lead.
2. ~~**I1**~~ — ✅ done 2026-08-09 (Amendment A2).
3. ~~**I3**~~ — ✅ done 2026-08-09 (Amendment A3, option (a)).
4. ~~**I5**~~ — ✅ done 2026-08-09; all three resolved pre-gate, as intended.
5. ~~**I4**~~ — ✅ done 2026-08-09 (Amendment A5); resolved before T01, as intended.
6. ~~**I2**~~ — ✅ done 2026-08-09 (Amendment A4); resolved ahead of T01, not after.
7. ~~**I7**~~ — ✅ done 2026-08-09 (ADR 0016 *Accepted residual risk*); its open half is now question 2 of I6.
8. ~~**I8 / I9**~~ — ✅ done 2026-08-09. I8 deferral reaffirmed on evidence in ADR 0016's D7 note; I9 accepted at 237 lines.

I1 and I3 were the only items executable with zero owner input; both are closed,
and **I2 closed too** once the owner supplied the base package. Everything
remaining needs either the owner (I4, I7) or the vendor (I6). Owner decisions
**1 (base package), 2 (no-registry scope) and 7 (field shapes) are settled**;
3–6 and 8–10 stand.

**Amendment ledger on `spine.tasks.md`, all pending TASKS-OK:** A1 (T01,
`AGENTS.md` + `CLAUDE.md`), A2 (T01, coding-rules bundle install), A3 (T02, B-5
no-registry), A4 (T01, resolved binding replaces the template). None closes a
gate.

## 4. Do not

- **Do not implement o7**, derive an o7 plan, or derive o7 tasks. The gate is open
  and the spec says so explicitly (`o7 spec:3, :190-192`).
- **Do not scaffold a standalone o7 service.** o7 is a **module** inside the spine
  repo (`o7 spec:5`); ADR 0005:125-126's one-deployable CI check is **Accepted** and
  fails the build on a second deployable.
- **Do not delete or migrate o1.** Both pipelines stay live (`o7 spec:45, :140`).
  An agent tidying "duplicate" pin fields destroys the fork boundary.
- **Do not silently patch approved artifacts.** Amend visibly — Amendment A1 in
  `spine.tasks.md` is the precedent to copy.
- **Do not resolve the Postgres or ADR 0011 assumptions in passing.** Either is an
  sdd-replan event.
- **Do not treat report §5 as decided.** It is recommendations, and its Java 25
  baseline is superseded by the plan's Java 21.
- **Do not copy the o7 mock IR shape.** `TestCaseIR.json:5`,
  `provenance.irVersion:16` and `LocatorCandidate.manifest.json:3` still carry
  `irVersion`; H4's prohibition names only ReplayReport and lineage rows, so
  copying reintroduces a fork-boundary leak.

## 5. Decisions only the owner can make

| # | Decision | Blocks |
|---|---|---|
| ~~1~~ | ~~Base package for the spine repo~~ — **answered 2026-08-09: `com.bank.spine`** | ~~I2~~ closed |
| ~~2~~ | ~~No-registry rule: spine T02 now, or wait for ADR 0017~~ — **decided 2026-08-09: spine T02 now** (Amendment A3) | ~~I3~~ closed |
| ~~3~~ | ~~Formatter~~ — **decided 2026-08-09: palantir-java-format 2.97.0** (fluent-chain readability; architecture-tests is all long ArchUnit chains) | ~~I4~~ closed |
| ~~4~~ | ~~Static-analysis set~~ — **decided 2026-08-09: Error Prone + NullAway + Checkstyle** (Checkstyle was already approved via plan:69/T30) | ~~I4~~ closed |
| ~~5~~ | ~~Spring Boot version~~ — **decided 2026-08-09: the 4.1 line; exact patch pinned at T01 execution** | ~~I4~~ closed |
| 5b | **JDK distribution** — decided 2026-08-09: **Temurin 21.0.8+, not Oracle**. Listed because it was *not* an anticipated decision: NullAway's Java 21 fallback excludes Oracle JDK. A later Oracle mandate is an sdd-replan trigger for the null-safety row. | closed, but watch |
| 6 | Attribution trailer policy — `Generated-by:` / `Assisted-by:` / forbidden / no AI PRs | AGENTS.md working agreement (UNRESOLVED today) |
| ~~7~~ | ~~The three field-shape conflicts~~ — **all three answered 2026-08-09** (tri-state pair · `dryRun` inside `checks` · `gateVersion` on `irGate`, not F6) | ~~I5~~ closed |
| ~~8~~ | ~~Attestation posture (a)/(b)/(c)~~ — **decided 2026-08-09: (b), with (c) as named escalation; `NOT_APPLICABLE` added for the Perfecto deadlock** | ~~I7~~ closed |
| 9 | TASKS-OK on the spine board | everything in WP0 |
| 10 | o7 Stage-2 sign-off (owner + security owner) | all o7 work |
