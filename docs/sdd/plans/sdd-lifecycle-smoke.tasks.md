# Tasks: SDD lifecycle smoke (THROWAWAY)

**Status:** **signed-off (2026-08-11)** — **THROWAWAY** · T1–T7 complete; Stage-10 owner SIGN-OFF  
**Spec:** `docs/sdd/specs/sdd-lifecycle-smoke.spec.md` (SPEC-OK) · **Plan:** `sdd-lifecycle-smoke.plan.md` (PLAN-OK)  
**Discipline:** markdown smoke — “red” = prove receipt missing / criterion unmet before writing it; paste gate output.

## Task list

| Id | Task (file-level) | Depends | ACs | Pass/fail criterion |
|----|-------------------|---------|-----|---------------------|
| **T1** | Confirm triplet paths: spec exists; this tasks file exists; plan exists — each header contains `THROWAWAY` | — | AC-1, AC-6, FR-4 | `test -f` all three; `rg -n 'THROWAWAY' docs/sdd/specs/sdd-lifecycle-smoke.spec.md docs/sdd/plans/sdd-lifecycle-smoke.plan.md docs/sdd/plans/sdd-lifecycle-smoke.tasks.md` matches each |
| **T2** | **Red:** show receipt absent (`test ! -f docs/research/sdd-lifecycle-smoke-receipt.md`); paste output | T1 | AC-2 | command exits 0 proving file missing |
| **T3** | Write `docs/research/sdd-lifecycle-smoke-receipt.md` with: title/status `THROWAWAY`, date, direction `D1`, path checklist (binding keys, six `sdd-*` SKILL.md paths, triplet paths), and a pasted real `check_gate` `SUMMARY:` line | T2 | AC-2, AC-5, FR-2 | file exists; contains `THROWAWAY` and `SUMMARY:` |
| **T4** | Quarantine check: this change’s touched paths are only under `docs/sdd/specs/sdd-lifecycle-smoke.*`, `docs/sdd/plans/sdd-lifecycle-smoke.*`, `docs/research/sdd-lifecycle-smoke-*` (no product specs / `tooling/` / skill trees) | T3 | AC-4, FR-3 | `git status --short` / diff path list shows no violations (or explicit empty if untracked-only in those dirs) |
| **T5** | Stage-8: from **repo root**, run `python3 tooling/skill-sync/skill_sync.py check`; paste full SUMMARY | T3 | AC-3, FR-5 | exit 0; `0 drifted` |
| **T6** | Stage-7 lightweight checklist (same-thread): walk AC-1..AC-9 against files; record pass/fail in receipt or chat | T4, T5 | AC-9 | every AC marked pass with evidence pointer |
| **T7** | Stage-9/10 clean converge: classify gaps (expect none); human sign-off; leave artifacts (C1) | T6 | AC-7, AC-8 | no Phase-N section needed; owner records sign-off |

## EARS coverage (1:1)

| AC | Covered by |
|----|------------|
| AC-1 triplet complete | T1 |
| AC-2 receipt exists | T2 (red) → T3 (green) |
| AC-3 check_gate green | T5 |
| AC-4 product quarantine | T4 |
| AC-5 THROWAWAY + SUMMARY in receipt | T3 |
| AC-6 throwaway header / non-product | T1 |
| AC-7 leave artifacts | T7 |
| AC-8 clean converge | T7 |
| AC-9 light Stage-7 | T6 |

## Stage-4 analyze (2026-08-11)

- **Cross-artifact:** AC-1..AC-9 each map to ≥1 task (table above). No
  zero-coverage criterion. C1/C2/C3 match T7/T7/T6. No CRITICAL findings.
- **Grounding:** Paths probed this session — binding keys present
  (`.sdd/binding.toml:12-16`); all six `.cursor/skills/sdd-*/SKILL.md` exist;
  triplet + brainstorm exist; receipt correctly **absent** pre-implement.
  No new dependency; no ⚠️ ADR trigger.
- **Baseline gates:** `python3 tooling/skill-sync/skill_sync.py check` →
  `SUMMARY: 5 families, 0 drifted, 0 shadow -> exit 0`. `test_gate` = `<none>`.
- **Minor fix during analyze:** spec status line now carries literal
  `THROWAWAY` (FR-4 / T1) — was only lowercase in the title before.
- **No CRITICAL.** Ready for human **TASKS-OK** → `sdd-implement` (T1…).

## Stage 9 — Convergence classify (2026-08-11, clean path C2)

| Finding | Class | Route |
|---------|-------|-------|
| *(none)* | — | no Phase-N section |

No `missing` / `partial` / `contradicts` / `unrequested` gaps vs SPEC-OK.

## Stage 10 — Sign-off (2026-08-11)

Owner replied **SIGN-OFF**. Checklist accepted: converged; `check_gate` green
(`SUMMARY: 5 families, 0 drifted, 0 shadow -> exit 0`); `test_gate` `<none>`;
no ADR; no comprehension gates; blast-radius leave-in-tree (C1). Artifacts
remain marked **THROWAWAY**.
