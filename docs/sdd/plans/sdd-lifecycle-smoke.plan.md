# Plan: SDD lifecycle smoke (THROWAWAY)

**Status:** **signed-off (2026-08-11)** — **THROWAWAY** · PLAN-OK executed  
**Spec:** `docs/sdd/specs/sdd-lifecycle-smoke.spec.md` (SPEC-OK 2026-08-11)  
**Direction:** D1 · Change class: throwaway / exploratory

## Shape (A1 — least machinery)

Markdown only. No Python, no new abstraction, no binding edits, no skill-tree edits.

```
docs/sdd/specs/sdd-lifecycle-smoke.spec.md          # exists (SPEC-OK)
docs/sdd/plans/sdd-lifecycle-smoke.plan.md          # this file
docs/sdd/plans/sdd-lifecycle-smoke.tasks.md         # after PLAN-OK
docs/research/sdd-lifecycle-smoke-brainstorm.md     # exists (Stage 1)
docs/research/sdd-lifecycle-smoke-receipt.md        # Stage 6 deliverable
```

**G1:** none — no new abstraction. Simpler thing rejected already at brainstorm (D4 stop-early; D6 probe script).

## File-level touchpoints

| Path | Action | FR/AC |
|------|--------|-------|
| `docs/sdd/plans/sdd-lifecycle-smoke.tasks.md` | create | FR-1, AC-1 |
| `docs/research/sdd-lifecycle-smoke-receipt.md` | create at implement | FR-2, AC-2, AC-5 |
| Spec / plan / tasks / receipt headers | ensure `THROWAWAY` | FR-4, AC-6, AC-7 |
| Product specs, `tooling/**`, `.cursor/skills/**`, `.claude/skills/**` | **do not touch** | FR-3, AC-4 |

## Stage map (this smoke)

| Stage | Owner | This change |
|-------|-------|-------------|
| 1 | done | brainstorm D1 |
| 2–4 | in flight | spec SPEC-OK → plan → tasks → analyze |
| 5 | skip unless blocked | — |
| 6 | `sdd-implement` | write receipt; run `check_gate` |
| 7 | same-thread checklist (C3) | FR/AC vs files |
| 8 | `python3 tooling/skill-sync/skill_sync.py check` | must exit 0 |
| 9–10 | `sdd-converge` clean path (C2) | no Phase-N; leave artifacts (C1) |

## Constitution / Ask-first

- Constitution: `.cursor/rules/architecture-principles.mdc` (design-workspace framing).
- Ask-first: **none** — no new dep, service, shared-kernel type, or abstraction.
- ADR: not required; optional 2–4 lines in `docs/architecture/log.md` at sign-off if you want a breadcrumb (not an AC).

## Risks

| Risk | Mitigation |
|------|------------|
| Mistaken for product law | THROWAWAY in every artifact header |
| Accidental tooling/skill edit | AC-4 quarantine; tasks list explicit forbid |
| Gate run from wrong CWD | Always run `check_gate` from repo root (binding comment) |

## Migration / rollback

No migration. Rollback = delete the throwaway files (not required at sign-off per C1).
