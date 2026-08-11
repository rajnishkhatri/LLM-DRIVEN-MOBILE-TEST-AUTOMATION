# Tasks: SDD Roles Catalog — doctrine bodies as configs (build item 5)

**Plan:** `docs/sdd/plans/sdd-roles-catalog.plan.md` (gate CLOSED 2026-08-07). Statuses updated in place; flipped only on evidence (item-4 lesson holds).

| id | wp | task | status |
|---|---|---|---|
| K01 | WP0 | `kernel/catalog/role-registry.json` — 9 roles / 4 arms per F1, `invocation.prompt` only; schema-valid at 1.3.0 | done |
| K02 | WP1 | Six primary bodies (`specifier`, `coder`, `cleaner`, `architect`, `hardener`, `qa`) — F2 layout, S2–S4 rules | done |
| K03 | WP2 | Three composite bodies (`solo`, `maker3`, `checker3`) — explicit merges | done |
| K04 | WP3 | Generate + commit `catalog-projections/{claude-code,cursor,copilot}/`; verify green in place | done |
| K05 | WP4 | selftest `catalog` section (registry valid · bijection both ways · layout markers · neutral scan over bodies + rendered trees · goldens ×2 · verify green); arithmetic 19; `catalog_trees` key | done |
| K06 | WP4 | `acceptance.sh`: `catalog_trees == 3`, header | done |
| K07 | WP5 | Docs: conformance rule #9 note, corpus-guide catalog family, README catalog section | done |
| K08 | WP5 | 0.5.0 (`pyproject.toml`, `__init__.py`), editable reinstall | done |
| K09 | WP6 | Gate: double selftest 19/19 byte-identical, zero DEFERRED; acceptance clean-copy PASS | done |
| K10 | WP6 | Tamper trio — verified landed, reverted byte-exact | done |
| K11 | WP6 | Spec/plan headers, `docs/architecture/log.md`, memory | done |

**Build gate record (2026-08-07):** selftest 19/19 ×2 **byte-identical report files** (`cmp` clean), zero DEFERRED, 12 flipped item-2 cases, 23 guard decisions, 4 emitter trees, **3 catalog trees**; `acceptance.sh` PASS on a clean offline copy (schema 1.3.0, validator 0.5.0). Bodies: 9 files, 1.9–2.4 KB each, zero neutral-token hits, F2 markers present, stems↔roles bijective; largest rendered Copilot card 3104 bytes against the 30000 cap. Tamper trio, each verified **landed** before its run and reverted byte-exact, final run byte-identical to the gate run:
- T1 doctrine byte edited without golden regen (`coder.md`) → `catalog` red alone on render-vs-golden drift — the ADR 0003 edit-without-regen scenario proven live;
- T2 silenced body (`qa.md` removed) → `catalog` red alone: "role 'qa' has no doctrine body" (FP1 bijection);
- T3 harness token smuggled into `specifier.md` → `catalog` red alone, the neutral scan naming the token (FP5).

**Honest notes:**
- **Runbook defect, caught by the runbook itself:** the tamper-trio compound command exceeded the 10-minute Bash cap mid-T2 and was killed with the T2 tamper still applied on disk (`qa.md` sitting in the scratchpad, catalog at 8 bodies). Caught immediately because tampers are applied from kept backups with state re-verified before every run; restored first, then T2/T3 re-run as isolated background commands. Lesson recorded: at 19 sections a gate run is ~3–5 minutes — one selftest per command, background it.
- Plan §3 said "ASCII markdown" while the ratified F2 H1 form carries an em-dash — F2 (ratified) wins; §3 corrected before authoring, noted here.
- Cursor agent cards render the literal `{args}` placeholder in invocation prompts (the cursor row's `args_token` is null; item-4 correction #3 renders verbatim when null). Intentional and golden-pinned: binding Cursor's argument convention is a descriptor-row edit for item 6, not a body edit.
