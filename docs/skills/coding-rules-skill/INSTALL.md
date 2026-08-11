---
type: runbook
title: 'Coding-Rules Skill — Workspace Install Guide'
description: >-
  Step-by-step install of the coding-rules bundle into the o1 pipeline
  Java/Spring Boot repo: canonical catalog placement, binding resolution,
  Claude/Cursor/Copilot front-ends, CI wiring for the load-bearing
  ArchUnit/migration gates (F1/F2/F4), verification smoke sequence,
  maintenance rules, and troubleshooting. Canonical copy of
  tooling/coding-rules-skill/INSTALL.md.
tags: [runbook, coding-rules, skill-install, o1-pipeline]
---

# Installing the coding-rules skill into the o1 Java workspace

Step-by-step install of the coding-rules bundle into the o1 pipeline's
Java/Spring Boot repository, for all three coding agents (Claude Code,
Cursor, GitHub Copilot) plus the CI enforcement layer. Follow the steps in
order — the binding (step 2) must exist before any agent front-end is
useful, and the CI seeds (step 6) are what make the load-bearing rules
real.

Throughout, `$ARCH` is this Architect workspace (where the bundle lives)
and `$O1` is the target Java repo root.

```bash
export ARCH=/Users/rajnishkhatri/Documents/Architect
export O1=/path/to/o1-pipeline        # CHANGE ME
```

**Prerequisites in `$O1`:** Java 17+ toolchain (the catalog's patterns use
records), Gradle or Maven, the ADR 0005 module layout (three modules —
`conversion`, `validation-certification`, `evidence` — or the intent to
create it), and a git repo. If the module layout doesn't exist yet, install
anyway: the rules are most valuable *before* the first class is written.

---

## Step 1 — Canonical rule content (once)

The catalog and enforcement seeds live at a repo path all three agents
point to:

```bash
mkdir -p $O1/docs/coding-rules
cp $ARCH/tooling/coding-rules-skill/references/rules-catalog.md \
   $ARCH/tooling/coding-rules-skill/references/archunit-seeds.md \
   $O1/docs/coding-rules/
```

Do not edit rule content anywhere else — the front-ends are pointers, and
the Copilot condensed file (step 5) is *generated from* the catalog, never
a second source of truth.

## Step 2 — Resolve the binding

```bash
mkdir -p $O1/.sdd
cat $ARCH/tooling/coding-rules-skill/references/binding.template.toml >> $O1/.sdd/binding.toml
```

Then open `$O1/.sdd/binding.toml` and resolve **every** placeholder under
`[coding-rules]`. The skill is designed to *ask rather than guess* when the
binding is unresolved, so an unfinished binding degrades every interaction:

| Key | Set it to | Worked example (eval fixture) |
|---|---|---|
| `base_package` | the real root package | `com.bank.o1` |
| `modules.*` | the three Gradle/Maven module dirs | `conversion`, `validation-certification`, `evidence` |
| `seams.invoke_models_adapter` | ArchUnit glob of the ADR 0001 adapter package | `..conversion.invokemodels.adapter..` |
| `seams.storage_port_adapter` | glob of the ADR 0011 port adapter | `..evidence.storage.adapter..` |
| `seams.source_adapter_packages` (+ `_internal_`) | ingestion adapter globs (F2 scope) | `..conversion.ingestion..` |
| `seams.async_seam_packages` | the two ADR 0007 dispatch packages | `..replay.dispatch.. \| ..review.dispatch..` |
| `seams.provider_sdks.packages` | provider/gateway SDK roots to ban outside the seam | `org.springframework.ai`, + the Phase-2 gateway SDK when known |
| `thresholds.*` | leave defaults (CC 10/5, D 0.3) | changing one later is an ADR-level decision, not an edit |

## Step 3 — Claude Code front-end

```bash
mkdir -p $O1/.claude/skills/coding-rules
cp $ARCH/tooling/coding-rules-skill/claude/skills/coding-rules/SKILL.md \
   $O1/.claude/skills/coding-rules/
```

In-repo install is the recommended form: Claude Code discovers nested
`.claude/skills/` automatically and scopes the skill to work inside `$O1`.
The packaged `dist/coding-rules.skill` (Save-skill button) installs to a
*profile* instead — use that only for work outside the repo; it carries
bundled `references/` as a fallback and will ask for binding values it
can't resolve.

## Step 4 — Cursor front-end

```bash
mkdir -p $O1/.cursor/skills/coding-rules
cp $ARCH/tooling/coding-rules-skill/cursor/skills/coding-rules/SKILL.md \
   $O1/.cursor/skills/coding-rules/
```

## Step 5 — Copilot (both formats)

```bash
mkdir -p $O1/.github/instructions
cp $ARCH/tooling/coding-rules-skill/copilot/instructions/coding-rules.instructions.md \
   $O1/.github/instructions/
```

Then merge `$ARCH/tooling/coding-rules-skill/copilot/AGENTS-fragment.md`
into `$O1/AGENTS.md` (create the file if absent; paste the fragment as its
"Coding rules" section).

**Maintenance duty unique to Copilot:** the instructions file contains a
*condensed* rule list because Copilot injects it as always-on context.
Whenever the catalog changes, regenerate the condensed lines from it — this
is the only place rule text is duplicated by design.

## Step 6 — CI enforcement (the part that makes the rules real)

ADR 0001/0005/0006 make F1/F2/F4 **load-bearing**: their suppression
requires a superseding ADR. Wire them CI-blocking from day one.

1. Create an architecture-test source set and copy the seed classes from
   `$O1/docs/coding-rules/archunit-seeds.md` into it. Gradle dependency:

   ```groovy
   testImplementation 'com.tngtech.archunit:archunit-junit5:1.3.0'
   ```

2. Replace every `{{placeholder}}` in the seeds with the binding values
   from step 2. **On the first run, tighten the package globs to the real
   tree** — the seeds ship slightly generic. Record any weakening of a
   rule as a review finding, never a silent tweak.
3. Wire the three non-ArchUnit checks:
   - **F4 migration checks** (no cross-lifecycle FKs, retention-class
     CHECK totality, no payload columns) into the migration pipeline.
   - **PMD cyclomatic complexity** (hard ceiling 10) into the quality gate.
   - **Deployment-unit check** (exactly one deployable artifact) into the
     build script.
4. Run the D-metric (distance from main sequence) **alarming, not
   blocking**; its trend feeds the quarterly review ADR 0005 mandates.

Known seed calibrations from the eval campaign (already fixed in the
shipped seeds — listed so nobody "simplifies" them away): D-2 must match
JDK async primitives (`CompletableFuture`, executors), not just messaging
annotations; B-3b bans `java.nio.file` in the evidence module outside the
port adapter.

## Step 7 — Verify the install

Run this smoke sequence before declaring done:

1. `./gradlew test` (or the arch-test task) — the ArchUnit suite runs and
   is green on an empty/compliant tree. If a seed fails on day one, the
   glob is miscalibrated or the violation is real; both need a decision,
   not a suppression.
2. Ask **Claude Code** in the repo: *"what does CR-14 require for lineage
   writes?"* — the skill should trigger, resolve the binding, and answer
   from the catalog (not from memory).
3. Ask **Cursor** the same; confirm the skill loads.
4. Open any `.java` file and confirm **Copilot** shows the instructions
   file as applied context; ask it to review a scratch diff and check the
   findings cite `CR-xx` IDs.
5. Negative check: ask any agent to summarize a Clean Architecture book
   chapter — the skill should *not* trigger (the description's skip list
   covers education/summaries).

## Maintenance rules (post-install)

- **The catalog is canonical.** Hard cap 18 rules: adding one means
  removing/merging one, or justifying a cap raise in the same PR.
- **Threshold changes, new async seams, and new seam-crossing types are
  ADR-level decisions** (CR-15/CR-06/CR-18), not catalog edits.
- **Copilot condensed file** regenerates from the catalog on every catalog
  change (step 5 duty).
- **Quarterly:** review module-boundary violation trends and the D-metric
  trend per ADR 0005's cadence — a worsening trend is an extraction-trigger
  conversation, not a cleanup ticket.
- The sdd-bundle integration (pointers from sdd-implement/sdd-converge to
  this skill) is deliberately deferred; when it lands, it's a one-line
  reference in the sdd binding, not a copy of rule content.

## Troubleshooting

| Symptom | Cause → fix |
|---|---|
| Skill doesn't trigger on coding tasks | Front-end not at `.claude/skills/coding-rules/SKILL.md` (exact path), or you're outside the repo — the in-repo skill scopes to `$O1` |
| Skill answers with questions about packages/modules | Binding placeholders unresolved — finish step 2; asking instead of guessing is intended behavior |
| ArchUnit seed fails everywhere on first run | Globs don't match the real tree — tighten per step 6.2; don't disable the rule |
| `record`-related compile errors in seeds/tests | Toolchain below Java 17 — the catalog's patterns and the fixture both require 17+ |
| Copilot reviews don't cite CR-xx | Instructions file not under `.github/instructions/` with the `applyTo` frontmatter intact, or the file was edited instead of regenerated from the catalog |
| Someone proposes editing a threshold "to make CI green" | That's the CR-18 anti-pattern by name — route to an ADR |
