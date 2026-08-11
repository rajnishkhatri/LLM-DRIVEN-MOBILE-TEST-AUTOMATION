# Plan: SDD Roles Catalog — doctrine bodies as configs (Track A, build item 5)

**Spec:** `docs/sdd/specs/sdd-roles-catalog.spec.md` (SIGNED OFF v1). **Status:** IMPLEMENTED 2026-08-07 — §7 gate CLOSED same day; build record in spec header + tasks header; WP0–WP6 all landed (K01–K11).
**House constraints carried:** offline + deterministic gate; single dependency; corpus-first; selftest is the gate; no new CHK ids (C3); zero emitter/schema changes (item-4 C2 executed as written).

## 1. Abstractions (G1 table)

| abstraction | decision | rejected alternative |
|---|---|---|
| Catalog placement | `kernel/catalog/` = live normative data (registry + bodies), sibling of `kernel/descriptors/`; `kernel/corpus/catalog-projections/` = its golden renders. The `emitter/` corpus family is untouched (fixture catalog keeps proving the *machinery*; the new family proves the *content*). | Folding real trees into `corpus/emitter/` (breaks that section's tree↔row bijection); replacing the `em-*` fixture with the real catalog (fixture cases would then churn on every doctrine edit). |
| Body authoring | Nine hand-authored markdown files, distilled per spec S2–S4 from the committed extracts; composites (`solo`, `maker3`, `checker3`) are explicit authored merges labeled as such. Content is data — a doctrine edit is: edit body → re-run `role-emit project` per row → commit regenerated goldens (the ADR 0003 loop). | Generation from the extracts (a distillation pipeline is judgment, not projection); six bodies + placeholder composites (C4 confound). |
| Catalog gate | One selftest section `catalog`: (1) registry schema-valid; (2) bodies↔roles bijection both ways; (3) F2 layout markers + FP5 neutral-token scan over bodies **and** rendered trees; (4) render ×2 per real row, `_compare_trees` vs goldens; (5) `role-emit verify` exit 0 per tree. Summary `catalog_trees`. | Two sections (validation vs goldens — one content family, one section; the failure detail names which half); reusing `emitter-projections` (different catalog, different family, different failure semantics). |
| Neutral-token scan on doctrine | Reuse `load_neutral_tokens` + `scan_neutral_text` (registry.py) over `kernel/catalog/bodies/*.md` and every rendered `.md` in the golden trees. This extends CHK-NEUTRAL's *token list* to content portability without touching the CHK table (the scan is a section assertion, not a new check id). | A new CHK id (C3 rejected); manual review only (drift-prone — exactly what the token list exists to catch). |
| Versioning | Validator 0.5.0 (new gate surface), `schema_version` stays 1.3.0 — no schema fields change, no restamp, no golden regen outside the new family. | Bumping to 1.4.0 "for the catalog" (nothing additive in any schema; SemVer says no). |

## 2. Repo tree delta

```
tooling/sdd-roles/
├── kernel/
│   ├── catalog/                       # NEW — the real catalog (ADR 0003's source)
│   │   ├── role-registry.json         # 9 roles, 4 arms (F1), invocation.prompt only
│   │   └── bodies/                    # 9 doctrine bodies (F2 layout)
│   │       ├── specifier.md  coder.md  cleaner.md  architect.md  hardener.md  qa.md
│   │       └── solo.md  maker3.md  checker3.md      # authored merges (C4)
│   └── corpus/catalog-projections/    # NEW golden family — real catalog × real rows
│       ├── claude-code/  cursor/  copilot/
├── validator/
│   ├── src/sdd_roles_validator/selftest.py   # + catalog section (19), catalog_trees key
│   ├── scripts/acceptance.sh                 # + catalog_trees == 3
│   └── pyproject.toml / __init__.py          # 0.5.0
```

## 3. Tech selections

Unchanged house stack; no new code paths beyond the selftest section (the emitter renders, the section compares). Bodies are UTF-8 markdown, LF, ≈≤3 KB each (the ratified F2 H1 form carries an em-dash; caps count UTF-8 bytes).

## 4. Delegated normative values — F-readings (owner, at the gate)

| id | reading |
|---|---|
| F1 | **The registry, frozen** (tag / gates / write_scopes / diagnostic_capability; `invocation.prompt` carries role identity + law pointer + `{args}` per S6): |

| role | tag | gates | write_scopes | diag | doctrine primary source |
|---|---|---|---|---|---|
| `specifier` | maker | — | `specs/` | no | ch6 §Specifier, ch2, ch5 §architect-role |
| `coder` | maker | `build`, `tests` | `src/`, `tests/` | no | ch6 §Coder, ch5 §coder, ch1 |
| `cleaner` | maker | `build`, `tests`, `crap` | `src/` | no | ch6 §Cleaner, ch4 §quality-barriers |
| `architect` | maker | `build`, `tests` | `src/`, `tests/`, `docs/adr/` | no | ch6 §Architect, ch4 §dependency-rule |
| `hardener` | checker | `tests`, `mutation` | `tests/`, `specs/` | no | ch6 §Hardener, ch4 §mutation |
| `qa` | checker | `build`, `tests`, `crap` | `src/`, `tests/` | yes | ch6 §QA, ch3 §roles, ch5 |
| `solo` | maker | `build`, `tests`, `crap`, `mutation` | `src/`, `tests/`, `specs/` | yes | merge: all six (arm A) |
| `maker3` | maker | `build`, `tests`, `crap` | `src/`, `tests/` | no | merge: coder+cleaner (arm B) |
| `checker3` | checker | `tests`, `mutation` | `src/`, `tests/` | yes | merge: qa+hardener (arm B) |

Arms: `A` = [solo]; `B` = [specifier, maker3, checker3]; `C` = [specifier, architect, coder, cleaner, hardener, qa]; `C-dbg` = C minus qa, `ablation: "diagnostic-debug"` — mirroring kata §6 and the CHK-ARM rule (every arm has a diagnostic role or an ablation marker). Notes: maker-tagged roles get tests-add-only for free (guard rule 5/6); `hardener` writes `specs/` only for the ch6 Gherkin-mutation NOOP-example rule, stated restrictively in its body; `architect` owns `docs/adr/` (ch6: partition decisions recorded, the one doc scope in the conveyor).

| id | reading |
|---|---|
| F2 | **Body layout, frozen**: H1 `# <role> — role doctrine` · one-line role charter · `Sources: ch…` citation line · numbered rule sections distilled per S2–S4 · closing section `## Stage exit` restating the gate/handoff contract (S4). Composites open with `**Merged role:** …` naming their parents. The strings `Sources:` and `## Stage exit` are the mechanical layout markers HP2 asserts. |
| F3 | **Goldens**: exactly the three real-row trees (the stub row is fixture-land, item-4 family); rendered with `--bodies kernel/catalog/bodies --registry kernel/catalog/role-registry.json`; committed verbatim; `verify` green in place is the standing CI drift command for doctrine. |
| F4 | **Versions**: validator `0.5.0`; `schema_version` unchanged at 1.3.0 (no restamp); acceptance asserts 19 sections, `catalog_trees == 3`, `emitter_trees == 4` retained. No new ADR — ADR 0003 already governs; this item is its first real payload. |

## 5. Work packages

| wp | scope | proof |
|---|---|---|
| WP0 | Registry (F1) + schema-validate | jsonschema green at 1.3.0 |
| WP1 | Six primary bodies (F2, S2–S4) | layout markers + neutral scan clean |
| WP2 | Three composite bodies (C4) | same |
| WP3 | Generate + commit the three golden trees; caps clear (HP3) | `role-emit project` exit 0 ×3; verify green |
| WP4 | Selftest `catalog` section + arithmetic 19 + summary key; acceptance | 19/19 ×2 byte-identical |
| WP5 | Docs (conformance #9 note, corpus-guide, README) + 0.5.0 | validate green |
| WP6 | Gate close: double selftest, acceptance, tamper trio, headers, log, memory | records in tasks header |

## 6. Risks

| risk | mitigation |
|---|---|
| Distillation drifts from source intent | Every body cites chapters; the raw extracts stay committed beside the raw chapters; a reviewer diffs doctrine against `ch6-agent-instructions.md` §role directly. |
| Doctrine edits forgotten in goldens | Impossible silently: `catalog` section re-renders ×2 and verify runs in place — a body edit without golden regen is a red gate. |
| Kata later needs different scopes/gates per arm | Registry is data; arm-level overrides would be a kernel-config concern for item 6, not a body rewrite. |
| "hardener writes specs/" too permissive | Body restricts to NOOP-example removal (ch6 §Hardener.3); guard still blocks everything outside `tests/`+`specs/`; QA validates spec changes downstream. |

## 7. Gate — combined SPEC-OK + PLAN-OK (OPEN)

Awaiting owner: C1–C4 locks (spec), F1–F4 readings above. On close: Stage-3 tasks (`docs/sdd/plans/sdd-roles-catalog.tasks.md`), then implementation; build-gate target: selftest 19/19 ×2 byte-identical, zero DEFERRED, acceptance PASS, tamper trio verified-landed.
