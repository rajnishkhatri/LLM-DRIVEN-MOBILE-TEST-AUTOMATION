# Spec: Skill-Surface Sync Guard (skill-sync)

**Status:** **signed-off (2026-08-10) — implemented.** Full same-day lifecycle
pass: SPEC-OK (specifier check-mode audit folded) → PLAN-OK → TASKS-OK →
implemented red-first → fresh-context review (8 findings, all accepted) →
Phase-2 convergence (grammar amendments A1–A3 below) → Stage-8 gates green
(selftest 10/10; bound gate exit 0 ×2 byte-identical) → owner sign-off.
**Direction:** D1+D2 with P6 rider (brainstorm 2026-08-10, lifecycle test-drive)
**Change class:** operational guard; no new dependency; no ⚠️ Ask-first trigger →
decision-log entry, no ADR. The `check_gate` binding edit is the owner-gated
consequence, consented through this lifecycle's own gates.

**Clarify decisions (locked 2026-08-10):**
| ID | Question | Decision |
|----|----------|----------|
| C1 | Shadow finding (P6) exit semantics | **Advisory** — `SHADOW <name>` is reported, exit code unaffected. User scope is not repo-governed; forced jointly by AC-11's green-baseline demand + the live `sdd-brainstorm` shadow (specifier audit). |
| C2 | `fix` semantics for EXTRA files | **Full mirror** — extras deleted, each deletion reported. Projection dirs are wholly generated. |

**Open questions:** none.

## Problem

Provisioning (2026-08-10) created byte-copies of skill bodies across surfaces:
`tooling/sdd-skills-bundle/` → `.claude/skills/` + `.cursor/skills/` (sdd),
`.cursor/skills/` → `.claude/skills/` (arch), kernel corpus goldens →
`.claude/agents/` + `.claude/skills/sdd-roles/` (roles), plus the pre-existing
`references/` ↔ `dist/` pair inside coding-rules. **No wired detection exists**
for the sdd/arch legs; the roles leg's verifier (`role-emit verify`) is unwired
here; coding-rules has the policy ("drift is a bug") with no mechanism. This
repo is **not a git repository** — no VCS diff, no history: drift is silent and
permanent. Additionally (P6, observed live): user-scope `~/.claude/skills`
names can shadow project skills (`sdd-brainstorm` today), a same-class hazard.

## Scope — manifest v1 families

| Family | Source (canonical) | Projection(s) |
|---|---|---|
| sdd | `tooling/sdd-skills-bundle/<skill>/` (×6) | `.claude/skills/<skill>/`, `.cursor/skills/<skill>/` |
| arch | `.cursor/skills/arch-*/` (×7, living home) | `.claude/skills/arch-*/` |
| role-agents | `tooling/sdd-roles/kernel/corpus/catalog-projections/claude-code/agents/` | `.claude/agents/` |
| kernel-card | `…/catalog-projections/claude-code/skills/sdd-roles/` | `.claude/skills/sdd-roles/` |
| coding-rules-dist | `tooling/coding-rules-skill/references/` | `tooling/coding-rules-skill/dist/coding-rules/references/` |

**Shadow scope (P6):** names in the user-scope skills dir (default
`~/.claude/skills`, overridable via `--user-scope <dir>`) ∩ project skill
names (basenames of manifest projection dirs under `.claude/skills/`).

## Report grammar (normative examples — fixtures assert these literally)

```
DRIFT sdd CHANGED sdd-spec/SKILL.md
DRIFT sdd MISSING sdd-replan/FIRST_RUN.md
DRIFT sdd MISSING sdd-implement/
DRIFT arch EXTRA arch-style/notes.txt
SHADOW sdd-brainstorm
OK role-agents (9 file-pairs / 1 projection)
SUMMARY: 5 families, 2 drifted, 1 shadow -> exit 2
```

Rules: one line per finding, sorted (families in manifest order, findings by
kind then path). **Pair unit = file pair** (one source file × one projection).
An entirely missing projection directory reports **once**, kind `MISSING`,
path with trailing `/` (contained files not enumerated). Directories
themselves are otherwise not compared — files only; empty source dirs
produce no pairs.

**Amendments (2026-08-10, owner-accepted at the Stage-7 findings gate):**
- **A1 (F2):** `fix` lines carry the projection —
  `FIXED <family> WROTE|DELETED <projection>/<relpath>`
  (e.g. `FIXED sdd WROTE .cursor/skills/sdd-spec/SKILL.md`), so multi-projection
  repairs are auditable.
- **A2 (F1):** one `DRIFT` line per relpath — cross-projection divergence
  collapses to the worst kind (`MISSING` over `CHANGED`; `EXTRA` relpaths
  never collide with source relpaths).
- **A3 (F4):** `shadow` in the `SUMMARY` line is an invariant unit token,
  never pluralized (`file-pairs` precedent).
- **A4 (post-sign-off, 2026-08-10):** AC-11's "known `SHADOW sdd-brainstorm`
  advisory" clause was true at sign-off; the shadow was resolved the same day
  (user-scope copy archived to `~/.claude/skills.archive/`, owner-directed),
  so the live baseline is now shadow-free. AC-11's green-baseline core is
  unchanged.

## Functional requirements

- **FR-1 Manifest.** A committed declarative manifest (`tooling/skill-sync/manifest.toml`):
  one entry per family — id, source dir, ≥1 projection dirs. The tool reads
  paths from the manifest only; no hardcoded surfaces.
- **FR-2 `check`.** Recursive byte-comparison of every source↔projection pair.
  Deterministic report per the grammar above. Read-only. Exit: 0 clean,
  2 any drift, 1 usage/config error.
- **FR-3 `fix`.** Make every projection an exact mirror of its source — create
  missing, overwrite changed, **delete extras with a per-deletion report line**
  (C2) — then internally re-run check; the re-check result is the exit code.
  This is Part 0.2 of the usage guide, promoted from prose to executable.
- **FR-4 Shadows (in `check`).** Compare user-scope skill names (default
  `~/.claude/skills`, `--user-scope <dir>` for tests) against project skill
  names; overlap ⇒ `SHADOW <name>` line; **exit code unaffected** (C1).
- **FR-5 `selftest`.** Fixture-based self-verification in a temp dir, each
  section asserting exit code AND literal report lines: clean · changed ·
  missing-file · missing-dir · extra · bad-manifest (a committed literal
  broken example) · shadow (advisory: line present, exit unchanged) ·
  fix-drifted (tree mirrored afterward, re-check governs exit) ·
  fix-extra (file deleted + `DELETED` line). Exit 0 iff all sections behave.
  (Repo precedent: ir-gate-checker's fixture selftest.)
- **FR-6 Gate binding.** After selftest is green: `.sdd/binding.toml`
  `check_gate = "python3 tooling/skill-sync/skill_sync.py check"`. Reversible
  (`<none>` restores today).
- **FR-7 Doc sync.** Update `docs/skills/sdd-usage-guide.md` statements that
  gates are `<none>` (Part 0.3 table, Stage 8, big map) + add the tool to
  Part 0; 2–4 line entry in `docs/architecture/log.md`.

## Acceptance criteria (EARS — failure paths first)

- **AC-1** IF any projected file differs byte-wise from its source THEN
  `check` exits 2 AND the report carries `DRIFT <family> CHANGED <relpath>`.
- **AC-2** IF a source file has no counterpart in a projection THEN `check`
  exits 2 with `DRIFT <family> MISSING <relpath>`; IF an entire projection
  directory is absent THEN exactly one `MISSING` line naming the directory
  with trailing `/` (contained files not enumerated).
- **AC-3** IF a projection contains a file its source lacks THEN `check`
  exits 2 with `DRIFT <family> EXTRA <relpath>`.
- **AC-4** IF the manifest is missing, unparsable, or names a nonexistent
  source directory THEN the tool exits 1 and writes nothing (fail-closed
  config).
- **AC-5** WHEN all pairs are byte-identical, `check` exits 0 and prints one
  `OK <family> (<n> file-pairs / <m> projections)` line per family + the
  `SUMMARY` line, per the report grammar.
- **AC-6** WHEN `fix` runs on a drifted tree, afterwards every projection
  mirrors its source exactly (extras deleted per C2, each with a `DELETED`
  line) AND the embedded re-check governs the exit code.
- **AC-7** WHERE a user-scope skill name equals a project skill name, `check`
  output contains `SHADOW <name>` AND the exit code is unaffected (C1).
- **AC-8** Ubiquitous: `check` writes nothing; `fix` writes only inside
  manifest-declared projection directories.
- **AC-9** Ubiquitous: single file, Python stdlib only, ≥3.11 (the repo's
  existing validator floor), deterministic sorted output, no network.
- **AC-10** WHEN `selftest` runs, every FR-5 fixture section behaves as
  annotated and the tool exits 0.
- **AC-11** WHEN the gate is bound (FR-6), running the bound command from the
  repo root on today's tree reproduces AC-5 behavior plus the known
  `SHADOW sdd-brainstorm` advisory line (green baseline).

## Out of scope / deferred

D4 symlink probe · D5 provenance sidecars (not consented) · D6 emitter
generalization (deferred behind drift recurrence or a 3rd harness) · the
Copilot condensed variant (intentional generated divergence — excluded by
manifest) · catalog→goldens verification (owned upstream by `role-emit
verify` + kernel selftest) · resolving the `sdd-brainstorm` shadow itself
(user-scope action, outside the repo).
