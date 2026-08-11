---
type: reference
title: 'AGENTS.md workstream — work summary (next-items plan I1–I9)'
description: >-
  What was executed against o7-agents-md-next-items-plan.md on 2026-08-09: eight
  of nine items closed, four spine-board amendments (A2–A5), two new ADR 0016
  sections, the resolved coding-rules binding, and four silent-failure defects
  found in the coding-rules bundle. Records decisions with their provenance, the
  three places the plan itself was wrong, and the single item still open. Closes
  no gate.
date: 2026-08-09
status: reference — the live tracker is o7-agents-md-next-items-plan.md
next_items_plan: o7-agents-md-next-items-plan.md
agents_md_draft: mobile-test-automation-spine.AGENTS.md
spine_tasks: mobile-test-automation-spine.tasks.md
spine_binding: mobile-test-automation-spine.binding.toml
---

# AGENTS.md workstream — work summary

**What this is.** A record of the work executed against
`o7-agents-md-next-items-plan.md`, written so a cold reader can see what changed,
why, and what is still open without re-deriving any of it. The **plan remains the
live tracker** — its `progress:` frontmatter is authoritative if the two ever
disagree.

**What this is not.** Not a spec, plan, or ADR. It derives no tasks, and **it
closes no gate.** Both gates that were open before this work are still open.

## Bottom line

| | |
|---|---|
| Items closed | **8 of 9** (I1–I5, I7–I9). **I6 parked by owner** 2026-08-09. |
| Spine-board amendments | **A2–A6** — all visible, all pending TASKS-OK |
| ADR 0016 | Two new sections + a four-state amendment. **Still Proposed.** |
| Files touched | 13 + 3 created (`spine-repo/`) |
| Defects found and fixed | **4**, all silent-failure class |
| Owner decisions taken | 8 (**#1–#5, #5b, #7, #8**) |
| Owner decisions still open | **3** (#6 attribution trailer, #9 TASKS-OK, #10 o7 Stage-2) |

**Gates verified unchanged:** spine task board still **awaiting TASKS-OK**; ADR
0016 and ADR 0017 both still **Proposed**. Nothing here was allowed to move one.

## Decisions taken, with provenance

| # | Decision | Value | Source of authority |
|---|---|---|---|
| 1 | Spine base package | `com.bank.spine` | **Owner** — the only value with no derivation |
| 2 | No-registry rule scope | Spine **T02 now**, not gated on ADR 0017 | Approved `plan:14`; ADR 0001:36-38 also declines the registry and **is Accepted** |
| 3 | Formatter | Spotless + **palantir-java-format 2.97.0** | Owner; project convention, no ecosystem standard exists |
| 4 | Static analysis | **Error Prone + NullAway + Checkstyle** | Owner; Checkstyle already approved via `plan:69`/T30 |
| 5 | Spring Boot | The **4.1 line**; exact patch pinned at T01 execution | Owner; 3.5 OSS support ended, 4.0 EOL 2026-12-31 |
| 5b | JDK distribution | **Temurin 21.0.8+**, not Oracle | Owner; forced by NullAway's Java 21 fallback |
| 7 | Three o7 field shapes | structured `cloudAdaptivity`; `dryRun` **inside** `checks`; `gateVersion` on `irGate` but **not** in F6 | Owner; ADR 0016 + spec both said seven checks |
| 8 | Attestation posture | **(b)** post-run assertion, **(c)** named as escalation | Owner; recorded as accepted residual risk |

## Where the work landed

**Spine task board** (`mobile-test-automation-spine.tasks.md`) — four amendments,
each with its own visible section in the A1 style. No EARS criterion was added,
removed, or reinterpreted by any of them.

- **A2** (T01) — installs the coding-rules bundle `AGENTS.md` points at. Steps 3–5
  of `INSTALL.md` deliberately excluded: per-agent front-ends would recreate the
  competing-instruction-file condition T01 asserts against.
- **A3** (T02) — adds ArchUnit **B-5**, no plug-in registry at the three CR-08
  seams, on approved-plan authority with **no ADR 0017 dependency**.
- **A4** (T01) — installs the **resolved** binding instead of the template.
- **A5** (T01) — pins the six stack dimensions for the POM.

**ADR 0016** — *Accepted residual risk* section (attestation) and a substantially
enriched **D7** note (in-toto). Compliance clause amended to the four-state
attestation. Status untouched.

**o7 spec** — pre-gate amendment section recording the I5 field shapes and the I7
posture. The spec is **unsigned**, so this corrects it *before* signature rather
than patching an approved artifact.

**Final files** — `spine-repo/AGENTS.md` (v1.0.0, 247 lines) + `spine-repo/CLAUDE.md`,
saved as literal files with a README. The `---8<---` marker convention is retired
(**A6**) so the body exists exactly once; the old draft keeps provenance and the
change log and points at it.

**New artifact** — `mobile-test-automation-spine.binding.toml`, the resolved
`[coding-rules]` binding, held in the workspace because the spine repo does not
exist yet.

**Mocks** — `IRGate.report.json`, `ReplayReport.json` and the o7 mocks `README.md`
corrected to the resolved shapes, with an explicit warning that the ReplayReport
now depicts a **post-confirmation** state that cannot be produced today.

**Coding-rules bundle** — seeds, binding template and `INSTALL.md` fixed; dist
mirror re-synced and `.skill` rebuilt (4 files, verified).

## The four defects

All four share a failure mode: **they fail quietly.** A green run proved nothing
against any of them. Three surfaced only when a real binding was resolved against
the seeds — which is the argument for resolving one *before* T01 rather than
during it.

| # | Defect | Why it was invisible |
|---|---|---|
| 1 | `" \| "`-joined multi-glob strings fed to `resideOutsideOfPackage` / `resideInAPackage`, which take **one** identifier | Matches no package; in `noClasses().that()` **exclusion** position that **widens** D-2/B-2 to the whole build, so legitimate seam code fails first and reads as a false positive — inviting the weakening the seeds forbid |
| 2 | B-1 referenced `{{provider_sdk_packages}}`, matching **no binding key**, beside a hardcoded copy of the same list | Worked *by accident* off the hardcoded copy. Adding the Phase-2 gateway SDK to the binding would silently not have been enforced — on **F1, load-bearing** |
| 3 | Provider-SDK values were bare roots with no trailing `..` | Inert while #2 kept them unread; silently under-banning once B-1 was routed through the binding |
| 4 | `INSTALL.md` specified `archunit-junit5:1.3.0` in **Gradle** syntax | Under Boot 4.1's JUnit 6 BOM the artifact must be `archunit-junit6`. **The wrong engine suffix discovers no `@ArchTest` at all** — the suite reports success having run nothing |

All fixed in `references/` **and** the template, so the o1 arm benefits.
**No re-check was needed** — the owner confirmed no o1 workspace exists yet, so
nothing was ever installed from the pre-fix bundle.

**Transferable check** these share: *if this silently matched nothing, would the
build go green or red?* Exclusion-position selectors invert the intuition —
never-matching makes them stricter, not looser, and the noise lands on innocent
code.

## Three places the plan itself was wrong

Recorded because a cold reader would otherwise trust them.

1. **I5 mis-framed the `gateVersion` conflict** as "present in the mocks, absent
   from the spec's F6 set". Not a contradiction: `gateVersion` is established o1
   convention (`StaticGate.report.json:6`, same auditPin pattern) and **F6 governs
   `ReplayReport`, a different artifact**. The real gap was narrower — the
   ReplayReport recorded the gate's verdicts while dropping the pin its own
   reproducibility claim rests on.
2. **I4 called the static-analysis set open.** `plan:69` and **T30** already
   approve Spotless + Checkstyle + Error Prone + custom Checkstyle checks, and the
   `Thread.sleep` ban (**FP7**, a Never-block rule) *is* one of those custom
   checks. Report §5's "skip Checkstyle" was written before the plans directory was
   read — the same gap that produced its Java 25 baseline.
3. **I4 omitted a decision that turned out to be load-bearing.** NullAway's
   JSpecify mode targets Java 25; its Java 21 fallback requires JDK 21.0.8+
   **except Oracle JDK**. The plan pins "Java 21" and names no vendor, so the
   distribution became a real decision — on Oracle the null-safety row is simply
   unavailable.

Also corrected: the plan's operational note said to copy into
`dist/coding-rules/`. The mirror is **not flat** — it is
`dist/coding-rules/references/`, and the flat copy silently produces a 5-file
archive. The note now carries the right path and a `unzip -l` check.

## What is still open

**I6 — the Perfecto vendor contact. ⏸ PARKED by owner 2026-08-09 — not closed.**
One channel, two questions.

1. **Appium 3 on real devices** — supported, or emulator/simulator only? Blocks
   the pinning strategy.
2. **Does Scriptless self-healing touch code-path Appium sessions?** ⚠ **This one
   gates every o7 run.** Perfecto documents no code-path AI toggle and no way to
   attest one, so `cloudAdaptivity.perfectoAI` currently resolves to `UNKNOWN`,
   which quarantines. A **written** "no" is the only thing that makes
   `NOT_APPLICABLE` valid. Absence of a statement is not a guarantee.

Question 2 outranks question 1 in urgency: it blocks runs, not just a version pin.

**⚠ Parking is safe only while o7 is out of scope.** The Stage-2 gate is open, so
no o7 run can happen and nothing is currently blocked. **Unpark before that gate
closes** — otherwise the first real run quarantines and records no verdict. Q1's
consequence is already carried as a standing rule in `AGENTS.md` (*do not commit
to an Appium 3 pin*), so parking costs nothing there.

**Owner decisions #6, #9, #10** — the attribution-trailer policy (the last
`UNRESOLVED` in `AGENTS.md`), TASKS-OK on the spine board, and the o7 Stage-2
sign-off, which still needs **two** signatures.

## Two things to watch

- **A later Oracle JDK mandate is an sdd-replan trigger** for the null-safety row
  — not a silent drop of NullAway.
- **`NOT_APPLICABLE` must not become an escape hatch.** It is valid only with a
  referenced written vendor confirmation; unreferenced it is a schema violation,
  never a default and never an engineer's judgement call.

## Deliberately not done

- **No o7 implementation, plan, or task derivation.** The gate is open and the
  spec says so.
- **PIT / mutation testing not wired** — deferred on a **blocker, not cost**:
  whether `pitest-junit5-plugin` works against JUnit Jupiter 6 is unverified.
- **in-toto (D7) not built** — deferral reaffirmed on evidence. ⚠ **SLSA v1.2 has
  Build and Source tracks only; there is no test track.** A `ReplayReport`
  attestation is not a SLSA artifact and must never be called one.
- **SBOM, dependency locking, reproducible builds, Sonar** — additive, block
  nothing in the scaffold.
- **`AGENTS.md` length not trimmed** — **247 lines / 14.1 KB** accepted at final. The <200
  figure is a soft guideline, not a model limit; the only truncating ceiling is
  Codex's 32 KiB.
