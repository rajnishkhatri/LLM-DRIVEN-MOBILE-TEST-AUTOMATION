# Spec: SDD Roles Emitter — D6 table-driven projections (Track A, build item 4)

**Status:** SIGNED OFF v1 (SPEC-OK, owner, 2026-08-07 — combined gate with PLAN-OK; clarify C1–C4 LOCKED as recommended same day; F1–F4 ratified as drafted) · **IMPLEMENTED 2026-08-07** — gate record: `contract-lint selftest` exit 0, 18/18 sections byte-identical across double runs, zero DEFERRED, 12 flipped item-2 cases held, 23 guard decisions, 4 mount goldens, 4 emitter trees reproduced ×2; `acceptance.sh` PASS on a clean offline copy (schema 1.3.0, validator 0.4.0); tamper trio verified-landed (doctored golden card byte → `emitter-projections`+`emitter-verify` red; silenced failure case → `arithmetic` red; un-drifted negative control → `emitter-verify` red alone); ADR 0003 Accepted. Honest notes in the tasks header.
**Home:** `tooling/sdd-roles/` (item-1 C1). **Process:** sdd-spec.
**Evidence:**
- `docs/research/role-agent-skills-external-research.md` — memo §3-D6 (reshaped: spec-kit demonstrates 50+ harnesses vary only on `{directory, file format, invocation prefix, $ARGUMENTS support}` — generation is a table, not bespoke emitters; two projection rows named: Copilot dual-target `.github/agents/*.agent.md` 30k-cap + `.github/skills/*/SKILL.md`, Cursor loose-file `.claude/` subset version-stamped for CI drift detection "because Cursor reads only literal directories, never Claude's plugin cache"; do **not** emit `speckit.*` lifecycle commands), §7 build item 4, §7a rider (platform-agnostic: canonical form = harness-neutral catalog; **the Claude plugin is a projection, not the canonical source**), §8 open item 1 (SKILL.md char-cap unknown — needs-probe, NOT resolved here).
- `docs/sdd/specs/sdd-roles-guard.spec.md` — item-3 rows this item executes: S1 ("mount artifacts here are *harness config payloads*, not role/skill projections"), out-of-scope ("the emitter will *copy* mount artifacts into projections, consuming the same descriptor data"); C2 precedent (descriptor row = THE per-harness fact table, additive minor restamp).
- `docs/sdd/specs/sdd-roles-kernel.spec.md` — item-1 harness-neutral authoring rules (portable frontmatter subset; typed schemas) that the emitted cards must respect.
- ADR 0001 (corpus-as-contract), ADR 0002 (golden-run conformance) — both Accepted; this item extends ADR 0002 to projections (C3) and raises **ADR 0003** (catalog-as-source: projections are build outputs, hand-edits are drift).

## Scope decisions locked (derived from prior artifacts)

| id | decision |
|---|---|
| S1 | **This spec covers only build item 4**: (a) the `role-emit` CLI (5th console script; subcommands `project` and `verify`); (b) additive `projection` object on `InvocationDescriptor` rows, `schema_version` → **1.3.0** via the committed restamp (C1); (c) the corpus deltas: golden projection trees per real-harness row + a stub-harness row (`kernel/corpus/emitter/`), errors-family additions; (d) `kernel/docs/conformance.md` port admission #9; (e) selftest/acceptance extensions gating all of it; validator **0.4.0**. Role **bodies** stay item 5 (they enter through a declared slot, C2); the kata item 6; plugin *publishing* (zips, marketplaces, install UX) is not a build item at all. |
| S2 | **Harness particulars stay data — including layout.** Emitter source contains no harness token and no per-harness branch; everything that varies lives in the row's `projection` object: a target table of `{kind, path_template, format, char_cap, args_token}` rows (F1 freezes the shape). Adding a harness = adding a descriptor row — **zero source changes** (the D6 lesson made structural). CHK-NEUTRAL's sweep extends over the new module unchanged. |
| S3 | **Cards render from typed catalog data only, deterministically.** One neutral card template renders each registry role (id, tag, gates, write_scopes, diagnostic_capability, invocation); the per-target `format` map controls frontmatter keys and layout. The doctrine body is a **declared slot**: `--bodies <dir>` (optional) maps `<role>.md` files in verbatim; absent body → committed placeholder marker. Item 5 changes card bytes *only* through that slot. No prose is synthesized: the description field derives mechanically from typed fields. |
| S4 | **Mount artifacts are copied, not re-derived.** WP0 extracts `write-guard mount`'s rendering into an importable pure function (certified byte-identical against the existing mount goldens *before any feature lands* — the item-3 `scopes.py` discipline). The emitter calls that function and writes the result into each projection tree at the projection-declared `mount-copy` path. One rendering source, two consumers (C4). |
| S5 | **Projections are build outputs with drift detection.** Every emitted file carries a version stamp derived from `(kernel schema_version, catalog digest)` — **clock-free** (no dates; the digest is the freshness signal). `role-emit verify` re-renders and byte-compares against an emitted tree: drift/missing/extra paths → exit 2, deterministic listing. This is the memo's Cursor CI requirement generalized to all rows. Hand-editing a projection is definitionally drift (ADR 0003). |
| S6 | **Caps are data, enforced at render.** Per-target optional `char_cap`; a rendered file exceeding its cap → exit 2 naming target and sizes, **nothing written** (all-or-nothing render, F3). Copilot `.agent.md` targets carry `30000` (memo-confirmed); SKILL.md targets carry `null` until §8 open item 1 is probed — the probe stays open, not resolved by this spec. |
| S7 | **The gate is ADR 0002 extended — no new CHK ids (C3).** Projection behavior is gated by: golden projection trees (byte-compared ×2 per row, real three + stub), the mount-copy identity assertion (HP3), verify green/red pair, errors-family cases, the 1.3.0 restamp (idempotent, validity-preserving), and the `speckit.`-emission sweep (FP6). All offline, all in `selftest`; `acceptance.sh` extended. |

## Clarify — C1–C4 (LOCKED 2026-08-07, owner — each locked as recommended)

| id | question | recommendation |
|---|---|---|
| C1 | Where do per-harness projection facts live? | **Extend descriptor rows, additive `schema_version` 1.3.0.** Item-3 C2 made the InvocationDescriptor row THE per-harness fact table; projections are the same class of fact. Whole-corpus restamp via committed `regen_corpus.py` (third exercise). Rejected: standalone projection-table file (a second per-harness table the emitter must join with `hooks` — the exact drift C2-item-3 rejected); bespoke per-harness emitter classes (refuted by the D6 evidence directly). |
| C2 | What do cards contain before item 5 authors doctrine bodies? | **Typed-data cards + declared body slot.** Cards render now from registry typed fields; the body slot takes `--bodies` files verbatim, placeholder marker when absent. Goldens committed over a dedicated emitter catalog fixture (`corpus/emitter/common/` — a registry exercising `invocation` fields, both tags, and present-vs-absent bodies) and the three real descriptor rows. Rejected: defer all card emission to item 5 (ships the emitter ungated against its real content class); synthesized prose descriptions (nondeterministic, ungrounded). |
| C3 | Does the CHK table grow (e.g. CHK-EMIT), or does golden-projection conformance cover it? | **Golden-projection conformance, no new CHK ids** — same reasoning the owner locked at item-3 C1: the CHK table stays item 1's enumeration of *validation* checks; projections are *behavior*, ADR 0002's class. Rejected: CHK amendment (every port would owe live checks for what goldens already pin). |
| C4 | Relationship to `write-guard mount` — subsume or compose? | **Compose.** Extract the render function (WP0, byte-certified by existing goldens), keep the `write-guard mount` CLI unchanged (it is runtime setup, item 3's concern), emitter imports the function for `mount-copy` targets. Rejected: subsume mount into `role-emit` (breaks item-3 goldens and conflates packaging with runtime setup); subprocess shell-out (fragile; two invocation paths to keep honest). |

## Problem

Items 1–3 built a harness-neutral kernel, orchestrator, and live guard — but nothing yet *installs* roles into a harness. The §7a rider makes the requirement explicit: Claude Code, Cursor, and Copilot must all be first-class, the canonical form is the neutral catalog, and every harness surface — including the Claude plugin — is a projection. Spec-kit's 50-harness table proves projection is data, not code. Item 4 builds that table's executor: catalog in, per-harness trees out, byte-deterministic, drift-gated, with the item-3 mount artifacts riding along so a projected workspace arrives guard-ready.

## Target artifact

| artifact | change |
|---|---|
| `validator/src/sdd_roles_validator/emitter.py` | NEW — `role-emit` CLI: `project` (catalog → per-harness trees) and `verify` (re-render + byte-compare, drift → exit 2). |
| `validator/src/sdd_roles_validator/mounts.py` | NEW — `render_mount(row, registry) -> dict` extracted from `guard.py` (WP0; `guard.mount` refactored onto it, byte-identical — existing mount goldens are the proof). |
| `kernel/schemas/invocation-descriptor.schema.json` | Additive optional `projection` closed object on rows (F1 shape). 1.3.0. |
| `kernel/descriptors/invocation-descriptors.json` | The three real rows gain `projection` data (normative table below). |
| `kernel/corpus/orchestrator/descriptors-stub.json` | Stub row gains `projection` (layout unlike any real row — proves table-generality). |
| `kernel/corpus/emitter/` | NEW: `common/` catalog fixture (registry + bodies dir) + golden projection trees `claude-code/`, `cursor/`, `copilot/`, `stub-epsilon/`. |
| `kernel/corpus/errors/` | + `emit-no-projection-row` (exit 1). **Decomposition correction #1 (tasks header):** the three exit-2 cases (`cap-exceeded`, `unknown-body-role`, `verify-drift`) live in `kernel/corpus/emitter/failures/` — conformance rule #4 fixes `errors/` as the exit-1 family. |
| `kernel/docs/conformance.md` | Port admission gains #9: emitter ports reproduce the projection goldens byte-identically from descriptor `projection` data. |
| `docs/architecture/adrs/tooling/sdd-roles/0003-…` | NEW ADR 0003 (catalog-as-source; projections are generated artifacts, hand-edits are drift) — Proposed with the plan, Accepted at gate close. |
| Whole corpus | `schema_version` 1.3.0 restamp via `regen_corpus.py restamp --to 1.3.0`. |
| `selftest.py`, `acceptance.sh`, `pyproject.toml`, READMEs | New sections (`emitter-projections`, `emitter-verify`), arithmetic, `role-emit` console script, `0.4.0`. |

### Normative projection rows (the memo's D6 table, made data — exact field shape frozen at F1)

| harness | targets |
|---|---|
| `claude-code` | `manifest` → `.claude-plugin/plugin.json`; `agent-card` → `agents/{role}.md`; `kernel-skill` → `skills/sdd-roles/SKILL.md`; `mount-copy` → `hooks/hooks.json` |
| `cursor` | `agent-card` → `.claude/agents/{role}.md` (Cursor-supported frontmatter subset); `kernel-skill` → `.claude/skills/sdd-roles/SKILL.md`; `mount-copy` → `.cursor/hooks.json` |
| `copilot` | `agent-card` → `.github/agents/{role}.agent.md` (`char_cap` 30000); `skill-card` → `.github/skills/{role}/SKILL.md` (dual-target; `char_cap` null pending §8-1); `mount-copy` → `.github/copilot/hooks.json` |
| `stub-epsilon` (corpus) | deliberately alien layout/format keys — the generality proof |

Target kinds enum: `{manifest, agent-card, skill-card, kernel-skill, mount-copy}`. `speckit.*` lifecycle commands are never a target (D6 rule; FP6 sweeps for regressions).

## Acceptance criteria (EARS)

### Failure paths first

- **FP1** IF `project`/`verify` targets a harness whose descriptor row lacks the `projection` object, THEN exit MUST be 1 (usage) and nothing written.
- **FP2** IF any rendered target exceeds its `char_cap`, THEN `project` MUST exit 2 naming the target, rendered size, and cap — and MUST write **nothing** (all-or-nothing render).
- **FP3** IF a template token in any `path_template`/format template cannot be resolved, THEN `project` MUST exit 2 naming the token and target — never emit a file containing an unresolved `{token}`.
- **FP4** IF `verify` finds any drifted, missing, or extra path against the re-render, THEN it MUST exit 2 listing offending relative paths in deterministic order.
- **FP5** IF `--bodies` contains a file whose stem matches no registry role id, THEN `project` MUST exit 2 (fail-closed — bodies must map onto the catalog).
- **FP6** IF any committed projection golden contains the token `speckit.`, THEN `selftest` MUST fail the emitter section (the D6 never-emit rule, enforced against template drift).
- **FP7** IF any golden byte differs (projection trees, verify pair), THEN `selftest` MUST exit 2 naming the failing section.
- **FP8** IF argv is missing required flags or names an unknown flag, THEN exit MUST be 1 with usage on stderr and nothing written.

### Happy path

- **HP1** WHEN `project` runs for each of the three real rows over the emitter catalog fixture, THEN the emitted trees MUST byte-match the committed goldens, byte-identical across double runs, with no clock input.
- **HP2** WHEN `project` runs for the stub row, THEN its golden MUST reproduce — a layout/format unlike any real harness, proving the table (not the code) carries the shape.
- **HP3** WHEN a projection includes a `mount-copy` target, THEN its bytes MUST equal `render_mount(row, registry)` output exactly — the same function `write-guard mount` calls (S4/C4), asserted in selftest.
- **HP4** WHEN `verify` runs over an untouched emitted tree THEN exit MUST be 0; WHEN any single emitted byte is doctored THEN `verify` MUST exit 2 — both directions gated in selftest.
- **HP5** WHEN any emitted file is inspected, THEN it MUST carry the version stamp (F2 format) derived from kernel `schema_version` + catalog digest — **except `mount-copy` files, which carry no stamp: HP3's byte-identity with `render_mount` output wins** (decomposition correction #2, tasks header); WHERE the catalog input differs by one byte, the stamp MUST differ.
- **HP6** WHEN a registry role carries `invocation` fields, THEN its cards MUST render them (with the row's `args_token` substituted where declared); WHEN `--bodies` supplies a body, THEN it MUST appear verbatim in the body slot; absent → the committed placeholder marker.
- **HP7** WHEN the 1.3.0 restamp runs, THEN it MUST be validity-preserving, idempotent, and MUST never write an `expect.json`.
- **HP8** WHEN `selftest` completes, THEN section count and arithmetic MUST cover the new sections (18 total) with `deferred_entries == 0` still asserted, CHK-NEUTRAL green over `emitter.py`/`mounts.py`, and `acceptance.sh` MUST pass on a clean offline copy.

## Out of scope (for the avoidance of drift)

Role doctrine bodies (item 5 — they flow through the C2 slot without emitter changes); the kata and any harness-live install/run (item 6); plugin publishing (zips, marketplace metadata, install UX — no build item); resolving the SKILL.md char-cap probe (memo §8 open item 1 — `char_cap` stays null until probed); emitting `speckit.*` lifecycle commands (never — D6; the spec-kit interop remains item 2's serialization mapping); Cursor headless smoke-test (memo §8 open item 2 — kata-blocking, not emitter-blocking); Track B orchestration.
