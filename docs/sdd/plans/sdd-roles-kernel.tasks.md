# Tasks: SDD Role Kernel — schema family + contract-lint + gate-wrap (Track A, build item 1)

**Status:** IMPLEMENTED — **build-item gate GREEN 2026-08-07.** All 44 tasks landed in one sdd-implement session; `contract-lint selftest` passes all 12 sections (byte-identical across runs), and `validator/scripts/acceptance.sh` (the spec WHERE criterion: clean copy, offline, sole dependency) exits 0 with 12 DEFERRED cases. Implementation notes: dev/acceptance interpreter is Python 3.12.2 via `--system-site-packages` (this machine's 3.11 lacks ensurepip/jsonschema; `requires-python >=3.11` holds, `PYTHON=` pins it); the five self-integrity checks run per-invocation in every `validate` report as well as under selftest (stronger than drafted); one implementation defect was caught by the selftest itself during bring-up (reports keyed by case basename collided across families — `missing-row` exists twice — fixed to corpus-relative labels). Drafted 2026-08-07 from the approved plan (PLAN-OK, F1–F4 ratified as drafted); Stage-4 analyze pass run same day (§5 — no CRITICAL findings; one plan count corrected during decomposition, recorded).
**Spec:** `docs/sdd/specs/sdd-roles-kernel.spec.md` (SIGNED OFF v3) · **Plan:** `sdd-roles-kernel.plan.md` (APPROVED) · **ADR:** `docs/architecture/adrs/tooling/sdd-roles/0001` (Accepted)
**Gate for this build item:** `contract-lint selftest` green on a clean clone, offline (the spec's WHERE criterion — task K43). Workspace check/test gates are `<none>`.

## 1. Checklist ("unit tests for English") + coverage matrix

Criterion IDs: FP = the spec's failure-path bullets in order (spec lines 99–119), HP = happy-path bullets (123–131). **Verdict: all 30 criteria are measurable; none flagged back to the spec.** Two resolved classes, per C5's normative Phase column: (a) the seven pure item-2 criteria are measurable in v1 **only** as committed-corpus-family + DEFERRED-reporting (full semantics land at item 2 — claiming them now would be the scope creep the plan forbids); (b) HP4's port rule is measurable now as a documented admission procedure plus corpus completeness (the admission *event* is future by nature).

| ID | Criterion (compressed) | v1 measurement | Tasks |
|---|---|---|---|
| FP1 | CHK-SCHEMA fails w/ artifact + schema + JSON pointer | invalid family + report naming | K17 |
| FP2 | CHK-EVIDENCE anti-BMAD (complete w/o green outcomes per registry) | invalid family | K22 |
| FP3 | GateOutcome verdict-like field → CHK-SCHEMA (closed) | named `verdict:"pass"` case | K07, K17 |
| FP4 | CHK-GATE-BIND (unbindable/fabricated outcome) | **item-2**: family + DEFERRED | K34, K35 |
| FP5 | CHK-CHAIN / CHK-WRITER / CHK-GENESIS incl. orphan chain | **item-2**: families + DEFERRED | K34, K35 |
| FP6 | CHK-TREE (writes[] must reproduce tree_digest) | **item-2**: family + DEFERRED | K34, K35 |
| FP7 | CHK-FENCE (full-sha256) / CHK-TAINT / CHK-TOOLBIND | invalid families | K19, K20, K21 |
| FP8 | CHK-PROV-PRESENT (discriminator on every field) | invalid family | K18 |
| FP9 | CHK-DECISIONS: floors (v1) + boilerplate-reuse (item-2) | v1 cases fail; item-2 case DEFERRED | K23, K34 |
| FP10 | CHK-REFS (dangling/drifted refs incl. report_ref) | invalid family vs cold-start fixture | K30 |
| FP11 | CHK-SCOPE incl. mechanical hardener rule | **item-2**: family + DEFERRED | K34, K35 |
| FP12 | CHK-REWORK (count > max across parent_run) | **item-2**: family + DEFERRED | K34, K35 |
| FP13 | CHK-ARM fails + ablation arm validates green | fail case + green pair | K24 |
| FP14 | CHK-THRESH (v1 committed-config; item-2 genesis-pinned) + CHK-PROTECT | `crap_relaxed` + omitted-key cases; item-2 case DEFERRED | K25, K26, K34 |
| FP15 | CHK-MAP vs KernelConfig-declared set + roots | invalid family | K27 |
| FP16 | CHK-NEUTRAL + CHK-HARNESS-ROWS self-test failure | doctored-fixture + missing-row/exit-map cases | K28, K39 |
| FP17 | CHK-DEBUG (rework → diagnostic role w/o DebugReport ref) | invalid family | K29 |
| FP18 | CHK-DET (double-run byte/exit divergence fails) | live double-run + differing-pair fixture | K37 |
| FP19 | CHK-NET (any network attempt fails) | socket-guard canary | K38 |
| FP20 | CHK-SELF (temp-copy stability + report names check id + pointer) | auditor over all invalid families | K40 |
| FP21 | CHK-DEFER (item-2 case reported non-DEFERRED = failure) | defer-auditor + doctored-report fixture | K36 |
| HP1 | 8 closed schemas, one schema_version, corpus meets bar | schema tasks + arithmetic assertion | K04–K13, K44 |
| HP2 | contract-lint offline deterministic {0,1,2}; gate-wrap Copilot-from-data | exit-contract checks + wrap corpus | K03, K31, K32 |
| HP3 | suite = exactly CHK v1 rows; report names every check; item-2 DEFERRED | registry↔corpus bijection + report | K03, K16, K34 |
| HP4 | alternate-language ports conformance-gated on identical corpus | documented admission procedure (C3) | K41 |
| HP5 | run-directory invocation → all applicable v1 checks + one JSON report, digestable | report model + cold-start run | K16, K30 |
| HP6 | cold-start fixture: every ref resolves at recorded sha256, zero chat/harness state | fixture construction + CHK-REFS green | K30 |
| HP7 | gate-wrap output + exit match active mapping row (per row, incl. exits 2, 3) | one corpus case per mapping row | K32 |
| HP8 | arm A/B/C/ablation selected by config alone — no schema-file change | arm corpus set over one registry, schemas untouched | K13, K24 |
| HP9 | WHERE gate: clean clone, offline, sole dependency → corpus behaves exactly as annotated | scripted acceptance run | K43, K44 |

## 2. Task list (K01–K44)

`[P]` = parallelizable with its sibling group once its Depends are met. All paths relative to `tooling/sdd-roles/`.

### WP0 — scaffold

| ID | P | Task (file-level) | Depends | Pass/fail |
|---|---|---|---|---|
| K01 | | Create the §2 plan tree: `kernel/{schemas,descriptors,docs,corpus/{valid,invalid,runs,errors}}`, `validator/src/sdd_roles_validator/checks/`, `ledger/.gitkeep` + `ledger/README.md` (writer: gate-runner only), `kernel/VERSION` containing `1.0.0` | — | tree matches plan §2 exactly; `cat kernel/VERSION` = `1.0.0` |
| K02 | | `validator/pyproject.toml`: `requires-python ">=3.11"`, deps `["jsonschema>=4.21,<5"]`, console scripts `contract-lint` → `sdd_roles_validator.cli:main`, `gate-wrap` → `sdd_roles_validator.gate_wrap:main` | K01 | `pip install -e validator/` succeeds on 3.11; both commands resolve; `contract-lint --help` exits 0 |
| K03 | | CLI skeletons + exit contract: `cli.py` (`validate`/`selftest` subcommands; usage error → exit 1, no report), `registry.py` (empty table `{check_id, phase, cluster, fn}`), `selftest.py` skeleton asserting registry↔corpus bijection + corpus-completeness (red until WP5) | K02 | `contract-lint validate /nonexistent` → 1; unknown subcommand → 1; `contract-lint selftest` → 2 with report naming missing families (the ratchet) |

### WP1 — schemas + valid corpus (the contract before the tool)

Each schema: JSON Schema 2020-12, `additionalProperties: false` throughout, per-file `$defs`, required `const` `schema_version: "1.0.0"` + required `const` `artifact_type`. Per-task pass/fail additionally: file validates against the 2020-12 metaschema AND its K13 valid case passes via `python -c` + jsonschema.

| ID | P | Task (file-level) | Depends | Pass/fail (beyond the shared bar) |
|---|---|---|---|---|
| K04 | [P] | `kernel/schemas/role-registry.schema.json`: role {id, tag: maker\|checker, gates[], write_scopes[], diagnostic_capability}; arms as named configs {roles[], ablation?}; **no arm-membership field on Role** | K01 | a Role object with `arms:` fails validation with an additionalProperties pointer |
| K05 | [P] | `kernel/schemas/handoff-contract.schema.json`: from/to role, stage_status enum, decisions[] floors (non-empty choice/rationale; `rejected_alternatives` minItems 1 **or** sentinel `alternatives_considered:"none"` + rationale, as oneOf), gate_outcomes[], completion evidence, rework edge {target_role, stage?, defect_shape?, surviving_mutants?, counter}, per-field provenance per plan §4 (conditionals: environment_quoted ⇒ fence; tool_output ⇒ tool) | K01 | sentinel-without-rationale fails; both decision branches validate |
| K06 | [P] | `kernel/schemas/stage-ledger-entry.schema.json`: spec artifact #3 field list verbatim incl. genesis variant (seq 0: kernel_config_digest, role_registry_digest, starting tree_digest, parent_run nullable), writes[] deltas, harness{name, resume_handle, agent_definition_digest}, writer | K01 | genesis and non-genesis variants both expressible; a non-genesis entry missing prev_entry_digest fails |
| K07 | [P] | `kernel/schemas/gate-outcome.schema.json`: {gate_id, tool, tool_version, exit_code, input_tree_digest, threshold{name,value}, attempt_number, report_ref{path,sha256}} — **closed; no verdict/status/result field exists** | K01 | `verdict:"pass"` case fails with pointer to the offending property (FP3) |
| K08 | [P] | `kernel/schemas/debug-report.schema.json`: failing test id, observed/expected, suspected locus, minimal repro | K01 | shared bar |
| K09 | [P] | `kernel/schemas/invocation-descriptor.schema.json`: set doc {declares[] (minItems 3, harness-name strings), rows[]}; row = {harness, command_template, agent_selection, auth_env_var, resume_semantics, output_parse_mode, exit_code_map} — **schema itself contains zero harness tokens (F3)** | K01 | metaschema pass + CHK-NEUTRAL-clean text (grep) |
| K10 | [P] | `kernel/schemas/speckit-mapping.schema.json`: rows kernel-artifact-type → target path | K01 | shared bar |
| K11 | [P] | `kernel/schemas/kernel-config.schema.json`: arm selection, named thresholds, `protected` object with the **7 required named keys** (F2; `speckit_constitution` const `.specify/memory/constitution.md`), gate-tool allowlist, required-mapping set, rework bounds, gate_runner id, enforcement_tier floor\|strong | K01 | config omitting any protected key fails schema-only validation (FP14/CHK-PROTECT substrate) |
| K12 | | Family-wide assertions: all 8 files carry const schema_version + const artifact_type, closed everywhere, no cross-file `$ref`, metaschema-valid — as a scripted check (becomes part of selftest drift section) | K04–K11 | script green over all 8; doctoring one const in a temp copy turns it red |
| K13 | | Valid corpus: ≥1 case per type under `kernel/corpus/valid/<Type>/` + `expect.json` `{expected: pass}` each; includes the **green C−dbg ablation arm** (S3), the arm A/B/C configs over one registry (HP8), a full protected-minimum KernelConfig; plus the committed descriptor instance `kernel/descriptors/invocation-descriptors.json` (3 rows, exit-code maps incl. "2" and "3" entries) | K04–K11 | every valid case passes jsonschema; descriptor instance passes K09 schema |
| K14 | | Drift check wired into selftest: `kernel/VERSION` ↔ each schema's const ↔ each corpus case's schema_version | K03, K12, K13 | selftest section green; temp-copy VERSION mutation flips it red |

### WP2 — validation engine + provenance cluster (v1 checks 1–5)

Check tasks share a bar: registry row `{check_id, phase: v1}` added; invalid family under `kernel/corpus/invalid/<CHK-ID>/` with `expect.json` per plan §4; `contract-lint validate` on each case → exit 2 with the report naming check id + failing JSON pointer exactly as annotated.

| ID | P | Task (file-level) | Depends | Pass/fail (beyond the shared bar) |
|---|---|---|---|---|
| K15 | | `loader.py`: path-independent artifact model — resolves schema by `artifact_type` content field, never filename/path; loads single artifacts, case dirs, run dirs | K13 | loading a case from corpus and from a tempdir copy yields equal models (scripted) |
| K16 | | `report.py`: canonical report per plan §4 (sorted keys + entry ordering, LF, ensure_ascii, 2-space, POSIX-relative paths, **no timestamps**; fields incl. phase + outcome pass\|fail\|deferred) | K03 | two consecutive runs on the same target → byte-identical report; report validates against a report JSON shape check |
| K17 | [P] | CHK-SCHEMA in `checks/provenance.py`* + family: `verdict-pass/` (FP3), `role-arms-field/`, `unparseable-json/` (exit 2, pointer `""`) | K15, K16 | three cases red exactly per expect.json |
| K18 | [P] | CHK-PROV-PRESENT + family: HandoffContract field lacking its provenance discriminator | K15, K16 | shared bar |
| K19 | [P] | CHK-FENCE + family: fence id ≠ sha256(bytes); truncated-prefix id; missing source_uri; missing retrieved_at | K15, K16 | all four cases red |
| K20 | [P] | CHK-TAINT + family: derived_from includes environment_quoted fence id, field provenance ≠ environment_quoted | K15, K16 | shared bar |
| K21 | [P] | CHK-TOOLBIND + family: tool id ∉ KernelConfig allowlist; missing tool_version; missing invocation digest | K15, K16 | all three cases red |

\* cluster module homes: provenance checks in `checks/provenance.py`, WP3 checks in `checks/config_registry.py`, stubs in `checks/deferred.py` — one function per CHK id, registered by row.

### WP3 — static config/registry cluster (v1 checks 6–14)

| ID | P | Task (file-level) | Depends | Pass/fail |
|---|---|---|---|---|
| K22 | [P] | CHK-EVIDENCE + family: `stage_status: complete` with a registry-assigned gate lacking a green GateOutcome (exit 0 + resolvable report) | K15, K16 | shared bar (FP2) |
| K23 | [P] | CHK-DECISIONS v1 + family: empty decisions[]; missing rationale; empty rejected_alternatives w/o sentinel; sentinel w/o rationale. Plus the **item-2 boilerplate-reuse case** committed with `{phase: item-2, expected: deferred, expected_when_implemented: fail}` | K15, K16 | v1 cases red; item-2 case DEFERRED |
| K24 | [P] | CHK-ARM + pair: arm referencing unknown role id → red; arm omitting the diagnostic-capability role w/o ablation → red; **with `ablation` marker → green** (FP13, S3) | K15, K16 | fail cases red; ablation case green; no schema file modified for any arm (HP8) |
| K25 | [P] | CHK-THRESH v1 + family: threshold absent; unnamed; `crap_relaxed/` value-mismatch vs committed KernelConfig (`crap_composite ≤ 6`). Plus item-2 genesis-pinned case `{expected: deferred, expected_when_implemented: fail}` | K15, K16 | v1 cases red; item-2 case DEFERRED |
| K26 | [P] | CHK-PROTECT + family: KernelConfig omitting one mandatory protected key (dropped-protected-path case) | K15, K16 | shared bar (FP14) |
| K27 | [P] | CHK-MAP + family: required-mapping member without a SpecKitMapping row; row targeting a path outside declared `.specify/` + `specs/` roots | K15, K16 | both cases red (FP15) |
| K28 | [P] | CHK-HARNESS-ROWS + family: declares member without a row; row exit-code map missing "2"; missing "3" | K15, K16 | all three red (FP16 half) |
| K29 | [P] | CHK-DEBUG + family: rework edge targeting the diagnostic-capability role with no DebugReport ref | K15, K16 | shared bar (FP17) |
| K30 | | Cold-start fixture `kernel/corpus/runs/cold-start/` (mini ledger w/ genesis + entries + artifacts at true sha256 + handoff + gate report; **zero conversational/harness-state references**) + CHK-REFS + family: missing-path ref; drifted-hash ref; drifted `GateOutcome.report_ref` | K15, K16 | fixture fully resolves (HP5/HP6); all three ref cases red (FP10) |

### WP4 — gate-wrap (parallel lane)

| ID | P | Task (file-level) | Depends | Pass/fail |
|---|---|---|---|---|
| K31 | | `gate_wrap.py`: run tool argv, capture exit code, translate per the active descriptor row, emit the row's decision output verbatim, exit per map; own usage/internal error → exit 1 (F1) | K02, K13 | unknown-harness invocation → 1; a mapped run reproduces the row's output + exit |
| K32 | | Mapping-row corpus: one case per exit-code-map row × 3 harness rows, incl. gate-tool exits **2 and 3** — stub tools via `sys.executable -c "raise SystemExit(N)"`; case = `invocation.json` + expected stdout + expected exit | K31 | every case green under selftest's gate-wrap section (HP7; FP16's wrapper half via K28 rows) |
| K33 | | `kernel/corpus/errors/` exit-1 family: contract-lint missing-target + unknown-subcommand; gate-wrap unknown-harness + missing-tool | K31 | each case exits 1 with no report (exit-code-1 coverage for HP1/HP9) |

### WP5 — self-integrity + phased checks

| ID | P | Task (file-level) | Depends | Pass/fail |
|---|---|---|---|---|
| K34 | | `checks/deferred.py`: DEFERRED stubs for the **7 item-2 checks** (CHK-CHAIN, CHK-TREE, CHK-WRITER, CHK-GENESIS, CHK-GATE-BIND, CHK-SCOPE, CHK-REWORK) + the item-2 sub-rows of CHK-DECISIONS/CHK-THRESH; report emits `outcome: deferred` per plan §4 dual-row rule | K16 | any report lists exactly 7 deferred rows + 2 dual item-2 entries; none green (HP3) |
| K35 | | Item-2 corpus families (all `{phase: item-2, expected: deferred, expected_when_implemented: …}`): broken prev-chain; unrecorded-write tree break; wrong writer; genesis missing digests + orphan-chain + counter-not-carried; unbound/fabricated GateOutcome + tree-mismatch; out-of-scope write + maker-modified-tests (and the `added`-under-tests **pass-when-implemented** case); rework count > max across parent_run | K06, K13, K30 | selftest reports every case DEFERRED — never green, never fail (FP4–FP6, FP11, FP12) |
| K36 | | CHK-DEFER: defer-auditor asserting every item-2-phase case reports DEFERRED + doctored-report fixture `invalid/CHK-DEFER/report-claims-green/` the auditor must reject | K34, K35 | live reports pass; doctored report red (FP21) |
| K37 | | CHK-DET: selftest double-run byte-compare (report + exit code) + differing-report-pair fixture the comparator must flag | K16, K17–K30 | live double-run identical; fixture pair red (FP18) |
| K38 | | CHK-NET: socket-denying guard (patch `socket.socket` + `socket.create_connection`) wrapping the selftest corpus run + guarded canary asserting the raise + post-run `sys.modules` scan for network modules in validator imports | K03 | canary red under guard; corpus run green under guard; module scan clean (FP19) |
| K39 | | CHK-NEUTRAL: token grep (`claude, cursor, copilot, anthropic, .claude/, .cursor/, .github/agents, .github/skills`, case-insensitive) over `kernel/schemas/**` + `validator/src/**` + registry check ids; exclusions `kernel/descriptors/` + `kernel/corpus/**`; + doctored-schema fixture under `invalid/CHK-NEUTRAL/` | K04–K11 | live tree clean; doctored fixture red (FP16 half, S2 proxy) |
| K40 | | CHK-SELF: auditor over **all** invalid families — copy each case dir to a tempdir, re-run, verdict must not change; report must name expect.check_id at expect.json_pointer; + doctored fixture (report omitting check id/pointer) | K17–K33, K35 | every family copy-stable; doctored fixture red (FP20) |

### WP6 — docs + acceptance

| ID | P | Task (file-level) | Depends | Pass/fail |
|---|---|---|---|---|
| K41 | [P] | `kernel/docs/`: `ledger-chain.md` (chain rule + the pinned `tree_digest` definition), `provenance.md` (S7 guide), `conformance.md` (C3 port-admission procedure — HP4), `corpus-guide.md` (layout, expect.json incl. `expected_when_implemented`, self-integrity canary patterns) | K01 (content after WP2–5 settle) | four files exist; conformance.md states the identical-verdict admission rule + log-recording step |
| K42 | [P] | `validator/README.md`: install, commands, exit codes (F1 scope), offline note (pre-fetched `jsonschema` wheel for the clean-clone run) | K31 | README covers all four; no harness tokens (CHK-NEUTRAL scope excludes README? **No** — README is under `validator/`, in scope: keep wording neutral) |
| K43 | | Acceptance script `validator/scripts/acceptance.sh`: fresh copy to temp dir, network guard env, `python3.11 -m venv` + install sole dependency from local wheel, `pip install -e`, `contract-lint selftest` | all K01–K42 | script exits 0; selftest report shows 17 v1 checks executed, 7 (+2 dual) DEFERRED, every corpus verdict per annotation, ≥1 case per exit code {0,1,2} (HP9) |
| K44 | | Wrap: run final `contract-lint selftest` + corpus-arithmetic assertion (§3) at repo root; record build-item completion in `docs/architecture/log.md` | K43 | selftest exit 0; arithmetic holds; log entry written |

## 3. Corpus arithmetic (asserted by selftest completeness + K44)

- **Valid:** ≥ 8 (one per schema type) + arm A/B/C + C−dbg ablation green case + full-protected KernelConfig + descriptor instance + cold-start fixture.
- **Invalid families:** 26 — 17 v1-fail families, 7 item-2 DEFERRED families, 2 dual-phase families carrying both a v1-fail case and an item-2 DEFERRED case.
- **Exit codes:** 0 (valid), 1 (`errors/` family), 2 (invalid families) — all three exercised (HP1, HP9).
- **gate-wrap:** one case per exit-code-map row per harness row (3 rows), including gate-tool exits 2 and 3 (HP7).

## 4. Dependency spine (critical path)

K01 → K02 → K03 → K04–K11 [P] → K12/K13 → K15/K16 → {K17–K30 [P] ∥ K31–K33} → K34/K35 → K36–K40 → K41/K42 [P] → K43 → K44. The gate-wrap lane (K31–K33) needs only K02+K13 and runs parallel to WP2/WP3. Widest fan-out: after K15/K16, thirteen check tasks are independently parallelizable.

## 5. Stage-4 analyze verdict (run 2026-08-07)

**No CRITICAL findings** (no constitution-invariant violation, no zero-coverage criterion, no reference to a non-existent file/API). Detail:

- **Cross-artifact consistency:** one defect found and fixed during decomposition — the plan said **six** item-2 DEFERRED stubs; the spec's CHK table has **seven** pure item-2 rows + 2 dual-phase rows. Plan corrected in four places under its §4 adjustable-values clause (header note records it); the earlier decision-log entry's "six" stands as written with the correction recorded in the 2026-08-07 PLAN-OK entry (house pattern: corrections annotate forward, log entries are not rewritten).
- **Plan §4 additions at tasks time** (both in the adjustable class, neither touches spec WHAT): `artifact_type` required const per schema — load-bearing for CHK-SELF path-independence (the loader resolves schemas from content, never paths); `expected_when_implemented` on item-2 expect.json so item 2 inherits executable annotations.
- **Coverage:** all 30 EARS bullets map to tasks (§1 matrix); all 26 CHK ids have an implementing (or DEFERRED-stub) task **and** a corpus-family task; every task traces to ≥1 criterion or scaffold necessity. Bijection holds in both directions.
- **Grounding (probed on this machine, 2026-08-07):** `python3.11` = 3.11.13 and `python3` = 3.12.2 present (≥3.11 ✓); `jsonschema` 4.23.0 installed, inside the `>=4.21,<5` pin — the offline clean-clone run can use a locally built wheel (K43 prerequisite noted); `tooling/sdd-roles/` does not yet exist (K01 creates it — no collision); `docs/architecture/adrs/tooling/sdd-roles/0001-…` exists (Accepted); `.sdd/binding.toml` carries `adr_home_sdd_roles` ✓; the o7 conformance-corpus precedent (`docs/sdd/specs/mobile-test-automation-o7-interpreter.spec.md`) exists ✓. New-dependency check: `jsonschema` is the single C3-declared dependency — no undeclared dependency introduced by any task.
- **Constitution:** trade-offs recorded per pick (plan §3 envelope column); no Ask-first item beyond the already-Accepted ADR 0001; the corpus-as-contract inversion is the plan's own G1-justified abstraction set — no new abstraction appears in tasks that the plan lacks.
- **Baseline:** workspace `check_gate`/`test_gate` = `<none>`; the build item's own gate (K43 selftest) substitutes, per the spec's acceptance bar.

## 6. Next

**Advance → sdd-implement, K01 first.** Suggested first session: WP0+WP1 complete (K01–K14) — that lands the entire contract surface (schemas + valid corpus + descriptor instance + drift ratchet) before any check logic, honoring the corpus-first order. The selftest ratchet (K03) stays red until WP5, turning green exactly when the build item is done — no separate progress tracking needed.
