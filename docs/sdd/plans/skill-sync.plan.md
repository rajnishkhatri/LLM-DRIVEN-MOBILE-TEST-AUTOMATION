# Plan: Skill-Surface Sync Guard (skill-sync)

**Status:** executed (2026-08-10) — PLAN-OK same day; all tasks + Phase-2 convergence complete; change signed off
**Spec:** `docs/sdd/specs/skill-sync.spec.md` (SPEC-OK 2026-08-10)

## Shape (A1 — least machinery)

One stdlib Python file + one TOML manifest. No package, no classes beyond
what stdlib hands us, no third-party deps.

```
tooling/skill-sync/
  skill_sync.py     (~220 lines: argparse, tomllib, pathlib, shutil, tempfile)
  manifest.toml     (the 5 families, literal)
```

**G1 note (the one "abstraction"):** the manifest. What it buys: surfaces are
declared data, so the roles-leg regen, a future harness, or a family removal
is a manifest edit, not a code edit. Simpler thing rejected: hardcoding the
five family paths in-script — rejected because the brainstorm's D6 horizon
(more harnesses) makes path churn the *expected* change, and a wrong hardcode
fails silent (checks nothing) while a wrong manifest fails loud (AC-4 exit 1).

## Manifest v1 (literal)

```toml
# skill-sync manifest — source of truth per family; projections are generated.
[[family]]
id = "sdd"
source = "tooling/sdd-skills-bundle"
members = ["sdd-lifecycle","sdd-brainstorm","sdd-spec","sdd-replan","sdd-implement","sdd-converge"]
projections = [".claude/skills", ".cursor/skills"]

[[family]]
id = "arch"
source = ".cursor/skills"
members = ["arch-lifecycle","arch-characteristics","arch-components","arch-style","arch-decide","arch-risk","arch-validate"]
projections = [".claude/skills"]

[[family]]
id = "role-agents"
source = "tooling/sdd-roles/kernel/corpus/catalog-projections/claude-code/agents"
projections = [".claude/agents"]

[[family]]
id = "kernel-card"
source = "tooling/sdd-roles/kernel/corpus/catalog-projections/claude-code/skills/sdd-roles"
projections = [".claude/skills/sdd-roles"]

[[family]]
id = "coding-rules-dist"
source = "tooling/coding-rules-skill/references"
projections = ["tooling/coding-rules-skill/dist/coding-rules/references"]
```

Two entry shapes: `members` families pair `<source>/<m>/` ↔ `<proj>/<m>/`
per member; member-less families pair `<source>/` ↔ `<proj>/` directly.
(Buys: one sdd entry instead of twelve; the tool logic is one loop either way.)

## CLI + exit codes (spec FR-2/3/4/5)

```
python3 tooling/skill-sync/skill_sync.py check    [--manifest P] [--user-scope D] [--root D]
python3 tooling/skill-sync/skill_sync.py fix      [same flags]
python3 tooling/skill-sync/skill_sync.py selftest
```

0 = clean/green · 1 = usage/config (bad manifest, missing source) · 2 = drift
(check) or post-fix re-check failure. `--root` defaults to CWD; exists so
selftest can point the tool at fixture trees (same seam ir-gate-checker uses).

## Algorithm (deterministic by construction)

1. Load manifest (`tomllib`); validate shape + source existence → else exit 1,
   nothing written (AC-4). Resolve every path against `--root`.
2. Per family, per projection: sorted `os.walk` of source (files only);
   byte-compare (`Path.read_bytes()` equality) → `CHANGED`/`MISSING`; sorted
   walk of projection for `EXTRA`; absent projection dir → single `MISSING`
   line, trailing `/` (AC-2). Findings sorted kind-then-path; families in
   manifest order.
3. Shadows: `sorted(names(user_scope) ∩ project_names)` where project names =
   basenames of `.claude/skills/`-rooted projection member dirs; emit
   `SHADOW <n>`, never touching exit (AC-7/C1).
4. `check`: print findings + `OK`/`SUMMARY` per grammar; exit 0/2 (AC-1..5).
5. `fix`: apply mirror ops (write missing/changed, delete extras) printing
   `FIXED <family> WROTE|DELETED <path>`, writes confined to projection dirs
   (AC-8), then re-run step 2–4 internally; re-check result is the exit (AC-6).
6. `selftest`: build fixture trees under `tempfile.TemporaryDirectory()`; run
   the FR-5 nine sections by invoking the tool's own functions with `--root`
   pointing at fixtures; assert exit codes AND literal report lines (AC-10).

## File touchpoints

| Op | File | Why |
|---|---|---|
| NEW | `tooling/skill-sync/skill_sync.py` | the tool |
| NEW | `tooling/skill-sync/manifest.toml` | the surfaces, declared |
| EDIT | `.sdd/binding.toml` | `check_gate` `<none>` → bound command (FR-6) |
| EDIT | `docs/skills/sdd-usage-guide.md` | Part 0.3 gate row, Stage 8 section, big-map Stage-8 row, Part 0 tool mention (FR-7) |
| APPEND | `docs/architecture/log.md` | 2–4 line decision entry (FR-7) |

## Order (Stage-3 task seeds, TDD per task)

T1 manifest + `check` happy/failure paths (selftest sections: clean, changed,
missing-file, missing-dir, extra, bad-manifest — red first, then implement) →
T2 shadows (section: shadow) → T3 `fix` (sections: fix-drifted, fix-extra) →
T4 real-tree run: green baseline + `SHADOW sdd-brainstorm` (AC-11 evidence) →
T5 bind `check_gate` + rerun via bound command → T6 docs + decision log.

## Risks / notes

- `python3` on PATH is Anaconda 3.12.2 here; floor 3.11 (tomllib). A machine
  below the floor fails **loud** (SyntaxError/ImportError → non-zero), never
  silently green. Same floor as the validator — no new toolchain demand.
- Runtime: ~1.4k file-pairs worst case, byte reads only → well under 1 s.
- Constitution (arch principles): trade-offs stated (G1 above, C1/C2 in spec);
  no invariant machinery exists in this repo to violate; decision-log duty
  covered by T6.
