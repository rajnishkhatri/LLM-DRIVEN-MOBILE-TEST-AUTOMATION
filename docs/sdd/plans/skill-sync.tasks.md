# Tasks: Skill-Surface Sync Guard (skill-sync)

**Status:** executed (2026-08-10) — TASKS-OK same day; T1.1–T6.2 + P2.1–P2.8 all complete with evidence; owner sign-off recorded
**Spec:** `docs/sdd/specs/skill-sync.spec.md` (SPEC-OK) · **Plan:** `skill-sync.plan.md` (PLAN-OK)
Discipline: red first per task — the selftest section is written failing
before the feature exists; failing output pasted, then passing.

## Task list

| Id | Task (file-level) | Depends | ACs | Pass/fail criterion |
|---|---|---|---|---|
| **T1.1** | Write `tooling/skill-sync/manifest.toml` (literal from plan) | — | AC-4 seed | `python3 -c "import tomllib,pathlib;tomllib.loads(pathlib.Path('tooling/skill-sync/manifest.toml').read_text())"` succeeds |
| **T1.2** | `skill_sync.py`: selftest skeleton + six check sections (clean · changed · missing-file · missing-dir · extra · bad-manifest) asserting exit codes AND literal grammar lines — **run it: RED** (features unimplemented) | T1.1 | AC-1..5, 10 | selftest exits non-zero listing the six failing sections; output pasted |
| **T1.3** | Implement manifest load/validate (fail-closed), sorted walk + byte-compare, report grammar, `check` CLI with `--manifest/--root` | T1.2 | AC-1..5, 9 | the six T1.2 sections pass; output pasted |
| **T2.1** [P] | Shadow leg: red section (SHADOW line present, exit unchanged) → implement `--user-scope` + name-intersection + line emit | T1.3 | AC-7 | shadow section red-then-green; both outputs pasted |
| **T3.1** [P] | `fix` leg: red sections (fix-drifted → mirrored; fix-extra → `DELETED` line; re-check governs exit) → implement mirror ops confined to projection dirs | T1.3 | AC-6, 8 | fix sections red-then-green; both outputs pasted |
| **T4.1** | Real-tree baseline: full `selftest` + `check` from repo root ×2 (determinism) | T2.1, T3.1 | AC-9, 10, 11(pre) | selftest exit 0; check exit 0, all five `OK` lines + `SHADOW sdd-brainstorm` + `SUMMARY`; two runs byte-identical; output pasted |
| **T5.1** | Bind the gate: edit `.sdd/binding.toml` `check_gate` → `"python3 tooling/skill-sync/skill_sync.py check"`; run the bound command verbatim | T4.1 | AC-11 | bound command exits 0 with T4.1's output; pasted |
| **T6.1** [P] | Doc sync: `docs/skills/sdd-usage-guide.md` — Part 0.3 binding row, Stage 8 section, big-map Stage-8 row, Part 0 tool mention | T5.1 | FR-7 | no stale "gates are `<none>`" claim remains in those spots (grep evidence) |
| **T6.2** [P] | Append 2–4 line decision entry to `docs/architecture/log.md` | T5.1 | FR-7 | entry present, cites spec + C1/C2 |

[P] = parallelizable within its row's dependency level.

## EARS coverage (1:1)

| AC | Covered by |
|---|---|
| AC-1 CHANGED | T1.2/T1.3 (changed section) |
| AC-2 MISSING file + dir | T1.2/T1.3 (missing-file, missing-dir) |
| AC-3 EXTRA | T1.2/T1.3 (extra) |
| AC-4 fail-closed config | T1.1 + T1.2/T1.3 (bad-manifest) |
| AC-5 OK/SUMMARY grammar | T1.2/T1.3 (clean) + T4.1 (real tree) |
| AC-6 fix mirrors, re-check exits | T3.1 |
| AC-7 SHADOW advisory | T2.1 + T4.1 (live `sdd-brainstorm`) |
| AC-8 write confinement | T3.1 (fixture asserts tree outside projections untouched; check leaves fixtures unchanged) |
| AC-9 stdlib/single-file/deterministic | T1.3 (construction) + T4.1 (×2 byte-identical) |
| AC-10 selftest green | T1–T3 aggregate, final at T4.1 |
| AC-11 bound-gate green baseline | T4.1 (pre) + T5.1 (bound) |

## Stage-4 analyze (2026-08-10)

- **Cross-artifact:** every AC has ≥1 owning task (table above — no
  zero-coverage criterion); no task exceeds its spec authority; C1/C2 locked
  in spec match T2.1/T3.1 semantics. No CRITICAL findings.
- **Grounding:** all manifest paths exist on disk (verified this session:
  6 bundle skills, 7 `.cursor` arch dirs, both goldens dirs, coding-rules
  `references/` + `dist/`); `python3` = 3.12.2 with `tomllib` importable;
  `~/.claude/skills` exists (shadow default). No new dependency;
  no ⚠️ ADR trigger — decision-log entry owned by T6.2.
- **Baseline gates:** `check_gate`/`test_gate` are `<none>` today — baseline
  trivially green; this change *establishes* the first real gate (T5.1).
- **Specifier drive-mode note:** scenario-law conversion (§3.1 drive mode) is
  deliberately skipped — the selftest fixtures ARE this change's executable
  law (G/W/T feature files would duplicate them). Recorded here so the skip
  is a decision, not an omission.

## Phase 2 — Convergence (2026-08-10, from Stage-7 fresh-context review; all 8 findings owner-accepted)

Classification: none `contradicts`, none `unrequested`. Grammar changes in
P2.2/P2.3 are owner-consented spec amendments (accepted at the findings gate),
recorded as dated amendment notes in the spec — not silent edits.

| Id | Task | source-ref | gap-type | Pass/fail criterion |
|---|---|---|---|---|
| **P2.1** | Cross-projection collapse: new red fixture section `cross-projection` (CHANGED in one projection + MISSING in the other → exactly ONE line, worst kind MISSING) → implement per-relpath worst-kind collapse → green | F1 | `partial` | section red-then-green, outputs pasted |
| **P2.2** | Projection-prefixed FIXED lines: amend spec grammar (`FIXED <family> WROTE\|DELETED <projection>/<relpath>`), update fix fixture literals red → implement → green | F2 | `partial` | amended literals red-then-green |
| **P2.3** | Grammar notes: worst-kind rule (P2.1) + `shadow` declared an invariant unit token (no pluralization, `file-pairs` precedent) | F4 (+F1) | `partial` (doc) | spec grammar section carries both notes |
| **P2.4** | Guide Part 0.1 truth: Claude Code column → ✅ "(provisioned 2026-08-10)", reframe 0.2 as fresh-clone/re-provision instructions | F3 | `missing` (doc) | no false ❌ claims remain; grep evidence |
| **P2.5** | Shadow names: only directories count — red assertion (loose file with project name must NOT shadow) → `is_dir()` filter → green | F5 | `partial` | shadow section red-then-green |
| **P2.6** | AC-4 disambiguation: `ERROR:` diagnostics to stderr; bad-manifest section asserts stdout lines empty (red) → implement → green | F6 | `partial` | section red-then-green |
| **P2.7** | Manifest comment: `_sdd/` deliberately unguarded (documentation of scope) | F7 | `partial` (doc) | comment present |
| **P2.8** | Binding comment: gate must run from repo root (CWD-sensitive, fails loud otherwise) | F8 | `partial` (doc) | comment present |

Order: P2.1→P2.2 sequential (both touch findings/report code); P2.5/P2.6 [P]
after; P2.3/P2.4/P2.7/P2.8 [P] doc tasks anytime; close with full selftest +
bound gate ×2 (Stage 8 evidence).
