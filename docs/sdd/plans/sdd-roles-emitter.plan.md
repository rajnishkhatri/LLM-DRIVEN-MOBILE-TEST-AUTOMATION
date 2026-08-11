# Plan: SDD Roles Emitter — D6 table-driven projections (Track A, build item 4)

**Spec:** `docs/sdd/specs/sdd-roles-emitter.spec.md` (SIGNED OFF v1). **Status:** IMPLEMENTED 2026-08-07 — §7 gate CLOSED same day; build record in spec header + tasks header; WP0–WP6 all landed (E01–E25); ADR 0003 Accepted.
**House constraints carried:** offline + deterministic gate; single dependency (`jsonschema`); canonical JSON bytes; corpus-first; selftest is the gate; no new CHK ids (C3); clock-free tools.

## 1. Abstractions (G1 table)

| abstraction | decision | rejected alternative |
|---|---|---|
| Renderer core | `emitter.py` — one pure function `render_projection(row, registry, bodies, kernel_version) -> dict[relpath, bytes]`; caps and token-resolution enforced on the in-memory dict **before any write** (FP2/FP3 all-or-nothing). CLI subcommands are thin wrappers: `project` writes the dict; `verify` renders and byte-compares. | Streaming per-file writes (leaves partial trees on cap failure); separate render paths for project vs verify (two truths — verify must re-run the *same* function). |
| Projection table | Data on the descriptor row (C1): closed `projection` object, target rows `{kind, path_template, format, char_cap, args_token}`. One neutral card template in source; per-target `format` maps frontmatter keys/layout. Adding a harness = adding a row. | Per-harness emitter classes (bespoke emitters, refuted by D6); templates as loose files in the repo (untyped, unvalidated, a second authoring surface). |
| Mount seam | WP0: extract `render_mount(row, registry)` from `guard.mount` into `mounts.py`; `guard.py` refactored onto it. Certification: existing mount goldens + guard sections green **before any emitter feature lands** (the item-3 `scopes.py` discipline, second exercise). Emitter imports the function for `mount-copy` targets. | Duplicate rendering in emitter.py (drift between mounted config and projected copy — the exact class S4 forbids); subprocess to `write-guard mount` (fragile argv coupling; two invocation paths). |
| Version stamp | Derived, clock-free: `catalog_digest = sha256(canonical registry bytes ‖ canonical descriptor-row bytes ‖ sorted bodies bytes)`, stamp = F2 format string carrying kernel `schema_version` + first 12 hex chars. Markdown targets: frontmatter key; JSON targets: top-level key. | Timestamps (breaks byte-determinism and the house clock-free rule); git SHA (workspace is not necessarily a repo; corpus must be self-contained). |
| Golden layout | `kernel/corpus/emitter/<harness>/` holds the emitted tree verbatim (golden-comparable with the existing `_compare_trees` helper); ONE shared catalog fixture `emitter/common/` (registry exercising `invocation` + both tags, plus a bodies dir with a deliberate gap) drives all four trees — one catalog, many projections. | Reusing `guard/common/` (2 thin roles, no `invocation` — can't exercise the card renderer) or `valid/RoleRegistry` (editing it ripples into item-1 goldens); per-tree registries (hides catalog-sharing); tar/zip goldens (not diffable, breaks byte-audit). |
| Restamp | `regen_corpus.py restamp --to 1.3.0` — committed machinery, third exercise; idempotence and never-writes-expect assertions unchanged. | One-shot script (the machinery exists precisely for this). |

## 2. Repo tree delta

```
tooling/sdd-roles/
├── kernel/
│   ├── schemas/invocation-descriptor.schema.json   # + optional projection object (closed), 1.3.0
│   ├── descriptors/invocation-descriptors.json     # 3 real rows gain projection data (spec normative table)
│   ├── corpus/
│   │   ├── orchestrator/descriptors-stub.json      # stub row gains projection (alien layout)
│   │   ├── emitter/                                # NEW
│   │   │   ├── common/       (role-registry.json + bodies/ — the shared catalog fixture)
│   │   │   ├── claude-code/  (.claude-plugin/plugin.json, agents/*.md, skills/sdd-roles/SKILL.md, hooks/hooks.json)
│   │   │   ├── cursor/       (.claude/agents/*.md, .claude/skills/sdd-roles/SKILL.md, .cursor/hooks.json)
│   │   │   ├── copilot/      (.github/agents/*.agent.md, .github/skills/<role>/SKILL.md, .github/copilot/hooks.json)
│   │   │   └── stub-epsilon/ (alien layout)
│   │   └── errors/ + emit-no-projection-row, emit-cap-exceeded,
│   │                 emit-unknown-body-role, emit-verify-drift
│   └── docs/conformance.md                         # port admission #9
├── validator/
│   ├── src/sdd_roles_validator/
│   │   ├── mounts.py                               # NEW (WP0) render_mount extracted from guard.py
│   │   ├── guard.py                                # refactored onto mounts.py (byte-identical behavior)
│   │   ├── emitter.py                              # NEW role-emit CLI (project / verify)
│   │   └── selftest.py                             # + emitter-projections, emitter-verify (18 sections)
│   ├── scripts/regen_corpus.py                     # restamp --to 1.3.0
│   └── pyproject.toml                              # role-emit entry, 0.4.0
docs/architecture/adrs/tooling/sdd-roles/0003-…     # ADR 0003 catalog-as-source (Proposed → Accepted at gate)
```

## 3. Tech selections

Unchanged house stack: Python 3.12.2 venv (`--system-site-packages`), `jsonschema` sole dependency, JSON Schema 2020-12 closed schemas, canonical JSON bytes (sort_keys/ensure_ascii/LF); markdown emitted as UTF-8 LF with frontmatter rendered from the format map in declared key order (deterministic — no dict-iteration order reliance).

## 4. Delegated normative values — F-readings (owner, at the gate)

| id | reading |
|---|---|
| F1 | **`projection` object shape** (closed, all fields required unless marked): `{targets[] (minItems 1)}`; target = `{kind (enum manifest|agent-card|skill-card|kernel-skill|mount-copy), path_template (relative, must not escape the projection root; per-role kinds must contain "{role}"), format (enum json|markdown), front_matter (array of {key, source} pairs; markdown only), char_cap (integer|null), args_token (string|null)}`. The spec's normative table fixes the three real rows' values; the stub row is deliberately alien. |
| F2 | **Version-stamp format frozen**: `sdd-roles <schema_version> catalog:<digest12>` — markdown targets carry it as frontmatter key `stamp`, JSON targets as top-level key `"stamp"`; `digest12` = first 12 hex of sha256 over canonical registry bytes ‖ canonical row bytes ‖ sorted `--bodies` file bytes. No clock input anywhere (S5). |
| F3 | **Exit protocol**: argv-level misuse (missing/unknown flags, row without `projection`) → exit 1, usage on stderr, nothing written; render-time failure (cap exceeded, unresolved token, unknown body role) → exit 2 naming the target, **nothing written** (all-or-nothing); `verify` drift → exit 2 with deterministic path listing; success → 0. Mirrors the item-3 F1/F3 split: 1 = misuse, 2 = the tool speaking its contract. |
| F4 | **Versions**: `schema_version` 1.3.0 (additive minor per ADR 0001), validator `0.4.0`, restamp via `regen_corpus.py restamp --to 1.3.0`; ADR 0003 Accepted at gate close. |

## 5. Work packages

| wp | scope | proof |
|---|---|---|
| WP0 | Extract `mounts.py::render_mount` from `guard.mount`; refactor guard onto it. | Existing mount goldens + all 16 item-3 sections green, byte-identical — certified before any feature. |
| WP1 | Schema `projection` object (F1); three real rows + stub row gain data; restamp `--to 1.3.0` whole corpus. | Schema-drift section green; restamp idempotent ×2; expected verdicts preserved. |
| WP2 | `emitter.py`: render core (cards from typed data, body slot, stamps, caps, mount-copy via WP0 seam) + `role-emit project/verify` CLI + pyproject 0.4.0. | Unit of proof is WP3's goldens — no separate harness. |
| WP3 | Emit + commit golden trees (3 real + stub); errors-family cases ×4. | `emitter-projections` section: trees reproduce ×2; errors cases hit expected exits. |
| WP4 | Selftest sections (`emitter-projections`, `emitter-verify` incl. doctored-byte red half, FP6 speckit sweep, HP3 mount-identity assertion), arithmetic 18, acceptance.sh extension. | 18/18 ×2 byte-identical; acceptance PASS on clean offline copy. |
| WP5 | Docs: conformance #9, READMEs, ADR 0003 (Proposed), `docs/architecture/log.md` entry. | contract-lint validate green over changed corpus artifacts. |
| WP6 | Gate close records: spec/plan headers, tamper trio (doctored golden card byte / doctored stamp / silenced section), memory + log. | Each tamper flips exactly its section red; verified the tamper *landed* (item-3 lesson). |

## 6. Risks

| risk | mitigation |
|---|---|
| Frontmatter "supported subset" drift (Cursor/Copilot accept different keys than we emit) | Keys are per-target `format` data — a subset correction is a descriptor-row edit + golden regen, zero source change; kata (item 6) is the live check. |
| 30k cap is measured in chars vs bytes ambiguity | F1 `char_cap` counts UTF-8 bytes of the rendered file (conservative; documented in conformance #9). |
| Body slot shape too narrow for item 5 (roles may need per-harness body variants) | Slot takes verbatim markdown per role; per-harness variance stays in format maps — if item 5 truly needs per-harness bodies, that is a 1.4.0 additive descriptor field, not an emitter rewrite. |
| Golden bloat (9 roles × 4 trees) | Corpus registry fixture already drives guard cases; trees are small text files; acceptance size unchanged in kind from item-3's run-set goldens. |

## 7. Gate — combined SPEC-OK + PLAN-OK (CLOSED 2026-08-07, owner)

C1–C4 locked as recommended; F1–F4 ratified as drafted; ADR 0003 Accepted at build-gate close. Stage-3 tasks: `docs/sdd/plans/sdd-roles-emitter.tasks.md`. Build-gate record target: selftest 18/18 ×2 byte-identical, zero DEFERRED, acceptance PASS on clean offline copy, tamper trio verified (each tamper confirmed landed).
