# Spec: SDD Roles Catalog — the six role doctrine bodies as configs over the kernel (Track A, build item 5)

**Status:** SIGNED OFF v1 (SPEC-OK, owner, 2026-08-07 — combined gate with PLAN-OK; clarify C1–C4 LOCKED as recommended same day; F1–F4 ratified as drafted) · **IMPLEMENTED 2026-08-07** — gate record: `contract-lint selftest` exit 0, 19/19 sections byte-identical across double runs, zero DEFERRED, 3 catalog trees reproduced ×2 and verify-green in place, bodies↔roles bijective with zero neutral-token hits, largest Copilot card 3104 B vs the 30000 cap; `acceptance.sh` PASS on a clean offline copy (schema 1.3.0, validator 0.5.0); tamper trio verified-landed, each flipping `catalog` red alone (drift / bijection / smuggled token). Honest notes in the tasks header.
**Home:** `tooling/sdd-roles/` (item-1 C1). **Process:** sdd-spec.
**Evidence:**
- `cases/unclebobAgenicInstructions/ch1..ch6-agent-instructions.md` — the committed doctrine distillations (the extract layer, not the raw chapters). Ch6 §Role pipeline is the per-role primary source (specifier → coder → cleaner → architect → hardener → QA, per-role numbered rules); ch5 §Role separation + §Handoffs (role identity at startup, bias control, sparse handoffs, the Option-A/B acceptance-defect rule); ch1/ch4 (testing discipline, physical-barriers doctrine); ch2/ch3 (spec-as-law, track discipline, context hygiene).
- `docs/research/role-agent-skills-external-research.md` — **D2 REFUTED** (verbatim doctrine embedding: "persona prose measurably does nothing; instructions drift ~8 turns; spec caps bodies <5k tokens") — bodies are *distillations with citations*, never chapter dumps; **D4** (roles call gates; gate results as tool output; **thresholds as named parameters** — crap4java ships exit-2 default 8.0 vs the workspace CRAP≤6, so doctrine must not hard-wire gate numbers); §4 handoff rules (transport decisions, not status prose; agent-asserted completion schema-invalid); §6 kata arms A/B/C(+C-dbg) — the pre-registered design item 6 runs.
- `docs/sdd/specs/sdd-roles-emitter.spec.md` — item-4 rows this item executes: C2 ("item 5 changes card bytes *only* through the body slot"), out-of-scope ("role doctrine bodies (item 5 — they flow through the C2 slot without emitter changes)").
- ADR 0003 (catalog-as-source) — Accepted; this item authors the catalog that ADR governs. ADR 0001/0002 unchanged.

## Scope decisions locked (derived from prior artifacts)

| id | decision |
|---|---|
| S1 | **This spec covers only build item 5**: (a) the committed real catalog — `kernel/catalog/role-registry.json` (9 roles, 4 arms — C4) + `kernel/catalog/bodies/<role>.md` (9 doctrine bodies); (b) committed **catalog projection goldens** for the three real harness rows (`kernel/corpus/catalog-projections/<harness>/`), rendered by the item-4 emitter with **zero emitter changes**; (c) one new selftest section gating catalog validity + bijection + golden reproduction; (d) doc updates. **No schema change** — `schema_version` stays 1.3.0, no restamp; validator → **0.5.0**. The kata (item 6) consumes this catalog; harness-live runs stay item 6. |
| S2 | **Doctrine is distilled, cited, and harness-neutral.** Bodies draw from the committed extracts (primary: ch6's per-role sections; constitution rules from ch1–ch5 where they bind that role), each with a `Sources:` line citing chapters. No verbatim chapter embedding (D2). No harness names or harness-specific file names in body text (the same portability rule CHK-NEUTRAL enforces on source — "project memory", not a vendor filename); the emitter's neutral cards stay renderable under all three rows. |
| S3 | **Gate numbers live in gate config, not doctrine (D4).** Bodies name the kernel gates they must pass (`build`, `tests`, `crap`, `mutation`) and defer every numeric threshold to gate configuration — ch6's "CRAP ≤ 6" becomes "reduce until the `crap` gate passes (workspace-configured threshold; ch6's workspace used 6)". Non-gate heuristics that are doctrine, not thresholds (e.g. cleaner's "split files > 100 mutation sites"), stay verbatim with citation. |
| S4 | **Completion discipline is contract, restated as doctrine.** Every body ends with the same stage-exit rule: completion claims are gate results + handoff artifacts (the kernel's anti-BMAD rule); "done" without a green gate is schema-invalid. Backward edges (QA→coder, hardener→coder defect reports) are named in the checker bodies per memo §4.5. |
| S5 | **The catalog is live kernel data, drift-gated like all of it.** Registry schema-valid at 1.3.0; bodies↔roles bijection **both directions** (every body stem names a registry role; every role has a body — the item-4 placeholder marker must never appear in a rendered catalog tree). The three golden trees reproduce byte-identically ×2 under the committed emitter, and `role-emit verify` exits 0 on each committed tree (the ADR 0003 CI drift command, now protecting real doctrine). |
| S6 | **Invocation stays deployment-thin.** Role `invocation` carries only `prompt` (role identity + law pointer + `{args}`, per ch5 "role prompts must include role identity at startup"); `model`/`agent`/`agents_file` stay unset — deployment parameters for item 6, not catalog facts. |

## Clarify — C1–C4 (LOCKED 2026-08-07, owner — each locked as recommended)

| id | question | recommendation |
|---|---|---|
| C1 | Where does the real catalog live? | **`kernel/catalog/`** (registry + `bodies/`) — live normative data beside `kernel/descriptors/` (the committed-real-data precedent), validated by the selftest like everything else in `kernel/`. Goldens under `kernel/corpus/catalog-projections/` (separate family — the `emitter/` family's tree↔row bijection stays untouched). Rejected: corpus-only placement (the catalog is product data, not fixture); repo-top `dist/` (nothing outside `tooling/sdd-roles/` is gate-covered). |
| C2 | What may a body contain? | **Distilled operational doctrine with citations (S2/S3)**: per-role rules from ch6 + binding constitution rules from ch1–ch5, `Sources:` line, gate names without numbers, harness-neutral wording, target ≈≤3 KB each (hard-bounded by the per-target caps; D2's <5k-token ceiling holds with wide margin). Rejected: verbatim chapter embedding (D2 refuted — recurring token cost, drift); persona prose ("you are meticulous…" — measurably inert per the memo). |
| C3 | Gate shape? | **One new selftest section (`catalog`), no new CHK ids** — registry validity, bodies bijection, golden trees ×2, verify green; summary key `catalog_trees`; acceptance extended; validator 0.5.0. Golden-conformance precedent, fourth exercise. Rejected: CHK amendment; separate acceptance script. |
| C4 | Six bodies or nine? | **Nine — the six conveyor roles plus the three kata-arm composites (`solo`, `maker3`, `checker3`), composites authored as explicit merges** (headed "merged role: …" with the same sources). The kata compares arms A/B/C; if A and B render placeholder doctrine while C gets the real thing, the comparison measures doctrine presence, not role count — the exact confound the pre-registered design excludes. Rejected: six bodies only (confounds the kata); mechanical merge tooling (new machinery for what is a one-time authored merge; contradicts the verbatim-slot design). |

## Problem

Items 1–4 built the kernel, conveyor, guard, and emitter — all exercised against *fixture* roles (`gd-*`, `em-*`, stub scenarios). The actual doctrine this track exists to deploy — Uncle Bob's six-role conveyor discipline — still lives only in `cases/` extracts, unreachable by any harness. Item 5 authors it as catalog data: nine registry rows and nine cited doctrine bodies that flow through the item-4 body slot unchanged, render under all three real harness rows within caps, and land under the same byte-gate as everything else. When item 6 provisions a kata workspace, `role-emit project` over this catalog IS the deployment.

## Target artifact

| artifact | change |
|---|---|
| `kernel/catalog/role-registry.json` | NEW — the real registry: 9 roles (F1 normative table), 4 arms (A, B, C, C-dbg mirroring kata §6), `invocation.prompt` only (S6). 1.3.0, schema-valid. |
| `kernel/catalog/bodies/<role>.md` | NEW ×9 — distilled doctrine per C2/S2/S3/S4 (F2 layout). |
| `kernel/corpus/catalog-projections/{claude-code,cursor,copilot}/` | NEW golden trees — `role-emit project` output over the real catalog + real descriptor rows (F3). |
| `selftest.py` | + section `catalog` (S5 assertions; 19 sections), summary key `catalog_trees`. |
| `acceptance.sh` | + `catalog_trees == 3` assertion; header. |
| `kernel/docs/conformance.md`, `corpus-guide.md`, `validator/README.md` | Catalog family + port note (rule #9 extended: emitter ports also reproduce catalog-projections). |
| `validator/pyproject.toml`, `__init__.py` | 0.5.0. |

## Acceptance criteria (EARS)

### Failure paths first

- **FP1** IF any registry role lacks a body file, or any body stem names no registry role, THEN `selftest` MUST fail the `catalog` section naming the role/stem.
- **FP2** IF the item-4 placeholder marker appears anywhere in a committed catalog-projection tree, THEN the `catalog` section MUST fail (a role rendered without its doctrine).
- **FP3** IF any golden byte differs from the re-render, or `role-emit verify` exits non-zero on a committed tree, THEN `selftest` MUST exit 2 naming the section.
- **FP4** IF the registry fails schema validation at 1.3.0, THEN the `catalog` section MUST fail.
- **FP5** IF any body or rendered card contains a harness token (the CHK-NEUTRAL token list), THEN the `catalog` section MUST fail — doctrine is portable by construction, not by luck.

### Happy path

- **HP1** WHEN `role-emit project` runs for each real harness row over the real catalog, THEN the trees MUST byte-match the committed goldens ×2 with no clock input, every per-role card carrying its doctrine verbatim in the body slot.
- **HP2** WHEN any body is inspected, THEN it MUST carry the F2 layout (H1, `Sources:` citation line, stage-exit rule) with gate names unnumbered (S3) — asserted mechanically for the layout markers.
- **HP3** WHEN the Copilot agent-card target renders, THEN every card MUST clear its 30000-byte cap (implicit in HP1's render success — recorded because it is the one hard external limit).
- **HP4** WHEN `selftest` completes, THEN it MUST report 19 sections, `deferred_entries == 0`, `catalog_trees == 3`, and `acceptance.sh` MUST pass on a clean offline copy at 1.3.0 / 0.5.0.

## Out of scope (for the avoidance of drift)

The kata itself and any harness-live execution (item 6 — including binding `invocation.model`, kata workspace provisioning, and the tamper-block metrics); gate *implementations* (crap4java/mutate4java arrive with the kata workspace; the kernel gates stay config + stubs here); revising the memo or the raw chapters; per-harness body variants (if item 6 proves the need, that is a 1.4.0 additive descriptor field per the item-4 plan risk table); Track B orchestration.
