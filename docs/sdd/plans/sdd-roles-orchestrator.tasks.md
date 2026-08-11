# Tasks: SDD Role Orchestrator — gate-runner + run-directory checks live (Track A, build item 2)

**Status:** IMPLEMENTED — **build-item gate GREEN 2026-08-07.** All 32 tasks landed in one sdd-implement session; extended `contract-lint selftest` passes all 14 sections (byte-identical across runs, **zero DEFERRED entries** — the DEFERRED era is over), and `validator/scripts/acceptance.sh` (clean copy, offline, sole dependency) exits 0. The four golden run sets reproduce byte-identically across double executions; resume completes the interrupted fixture byte-equal to the completed golden; a doctored ledger refuses to resume (exit 2, nothing written); the parent/child pair proves counter carry (child rework count 2 continuing the parent's 1). Tamper-verified before trusting: a doctored golden byte → `orchestrator-goldens` red; a silenced corpus defect (repaired broken-chain) → `invalid-corpus` red; a doctored VERSION → drift red. **Three defects were caught by the gate itself during bring-up** (honest notes): (1) the restamp script re-synced `artifacts[]` digests but not the matching `writes[].sha256_after` rows — cold-start went CHK-TREE-red; fixed in `regen_corpus.py` (validity-preserving writes sync) and re-run from the pre-restamp snapshot; (2) the runner recorded the rework edge on both the handoff and the rework entries — CHK-REWORK monotonicity correctly flagged the duplicate; the edge now lives only on the `rework` event entry; (3) the SpecKitMapping did not travel with the run, so resume-from-run-local-config broke S8 self-containment — genesis now copies config + registry + mapping into the run dir. Dev/acceptance interpreter unchanged from item 1 (python 3.12.2 via `--system-site-packages`; `requires-python >=3.11` holds; `PYTHON=` pins). Drafted 2026-08-07 from the clarified spec (C1–C4 locked); Stage-4 analyze run same day (§4).
**Spec:** `docs/sdd/specs/sdd-roles-orchestrator.spec.md` (v2) · **Plan:** `sdd-roles-orchestrator.plan.md` · **ADR:** `docs/architecture/adrs/tooling/sdd-roles/0002` (Proposed → Accepted at PLAN-OK)
**Gate for this build item:** extended `contract-lint selftest` green (zero DEFERRED, golden runs byte-identical, produced runs validate green) on a clean copy, offline, sole dependency — `validator/scripts/acceptance.sh` exit 0 (spec WHERE). Workspace check/test gates are `<none>`.

## 1. Checklist ("unit tests for English") + coverage matrix

Criterion IDs: FP1–FP14 = the spec's failure-path bullets in order; HP1–HP10 = happy-path bullets in order (WHERE = HP10). **Verdict: all 24 criteria are measurable; none flagged back to the spec.** The flip class is measurable *because* item 1 committed `expected_when_implemented` — the annotations are the oracle; the orchestrator class is measurable because goldens are committed bytes.

| ID | Criterion (compressed) | Measurement | Tasks |
|---|---|---|---|
| FP1 | CHK-CHAIN raw-byte chain + genesis marker | `broken-chain` flips to annotated fail | R06 |
| FP2 | CHK-TREE arms; workspace writes exempt | `unrecorded-write` → fail; `added-under-tests` → **pass** | R07 |
| FP3 | CHK-WRITER vs config gate-runner id | `rogue-writer` → fail | R08 |
| FP4 | CHK-GENESIS pins/anchoring/orphan/counter-carry | `missing-digests`, `orphan-chain` → fail; new `counter-not-carried` → fail | R09 |
| FP5 | CHK-GATE-BIND C2 binding (entry match, report-in-artifacts, input-tree equality) | `unbound-outcome` → fail; new `tree-mismatch` → fail | R10 |
| FP6 | CHK-SCOPE four sub-rules, history-resolved before-hash | `out-of-scope-write`, `maker-modified-tests` → fail | R11 |
| FP7 | CHK-REWORK bound within + across parent | `over-cap` → fail; new `over-cap-across-parent` → fail | R12 |
| FP8 | CHK-DECISIONS item-2 boilerplate reuse | `boilerplate-item2` → fail | R13 |
| FP9 | CHK-THRESH item-2 genesis anchoring | `genesis-pinned-item2` → fail | R14 |
| FP10 | CHK-DEFER inverted (no lingering DEFERRED) | new `deferred-after-implementation` fixture rejected | R16 |
| FP11 | `--resume` refuses doctored ledgers, writes nothing | tamper-refusal selftest section | R24, R28 |
| FP12 | bound-exceeded run fails (exit 2) yet validates green | rework golden + failed-run validation assertion | R22, R26, R27 |
| FP13 | red handoff never advances the conveyor | rework scenario branch coverage (repair path exists) | R22, R26 |
| FP14 | usage errors → exit 1, nothing written | runner usage cases in `errors/` family | R18 |
| HP1 | zero fn-less rows; zero DEFERRED; report shape unchanged | registry flip + report assertions | R15 |
| HP2 | every item-2 case verdicts per `expected_when_implemented`, no re-authoring | selftest flip interpretation | R17 |
| HP3 | VERSION 1.1.0 lockstep restamp; additions optional+closed | restamp + drift section green | R01–R03 |
| HP4 | runner source neutral (CHK-NEUTRAL covers new module) | live scan over `validator-src/**` (existing scope) | R18–R24 |
| HP5 | golden green run: byte-identical ×2, contract-lint green | golden-execution section | R26, R27 |
| HP6 | golden rework run: repair round + cross-stage edge + DebugReport | rework scenario + golden | R26 |
| HP7 | resume completes from ledger+contracts+workspace alone = golden | resume section | R24, R26, R28 |
| HP8 | parent continuation: genesis pins + carried counters | parent golden pair validates green | R20, R26 |
| HP9 | serialization through mapping rows at handoff; goldens carry copies | serialization presence section | R23, R26, R28 |
| HP10 | WHERE: clean copy, offline, sole dep → acceptance exit 0 | scripted acceptance run | R29–R31 |

## 2. Task list (R01–R32)

`[P]` = parallelizable with siblings once Depends met. Paths relative to `tooling/sdd-roles/`.

### WP0 — schema minors + the 1.1.0 restamp (corpus-first, again)

| ID | P | Task (file-level) | Depends | Pass/fail |
|---|---|---|---|---|
| R01 | | C1/C2 schema additions, all optional + closed: `role-registry` roles[].`invocation {prompt?, agent?, agents_file?, model?}`; `kernel-config` `gates[] {id, tool, argv[] (minItems 1), threshold?}`; `stage-ledger-entry` regular_entry `input_tree_digest?` | — | metaschema + closedness walk green; a 1.0.0-shaped artifact minus version string validates against 1.1.0 shapes |
| R02 | | `validator/scripts/regen_corpus.py`: restamp engine — version strings, chain recompute (raw-byte digests), `handoff_contract_digest` + artifact-ref + tree recompute, C2 cold-start/CHK-GATE-BIND regeneration (reports + `input_tree_digest` recorded at the `gate_run` entry), golden refresh hook (WP4); hard assertion: never writes an `expect.json` | R01 | script runs idempotently (second run = zero diffs) |
| R03 | | Execute the restamp: `kernel/VERSION` → 1.1.0; whole corpus restamped; **existing selftest green over the restamped corpus** (12 sections, item-2 cases still DEFERRED — the flip is WP2) | R02 | `contract-lint selftest` exit 0 pre-flip; drift section green; cold-start validates with the C2 shape |

### WP1 — the one formula source

| ID | P | Task (file-level) | Depends | Pass/fail |
|---|---|---|---|---|
| R04 | | `loader.py`: retain raw line bytes per ledger line (`Artifact.raw`); group ledger files in `Context.ledgers` (label → ordered [(raw, artifact)]); conventions doc-string updated | R03 | temp-copy load equality still holds (CHK-SELF section stays green) |
| R05 | | `ledger_model.py`: tree formula (`<path>\0<sha>\n` fold + digest), artifact-map replay (genesis/parent seed → per-entry maps), chain verify (raw bytes), genesis anchor resolution (config/registry digest equality), per-edge rework history (parent-linked), write-history resolution for CHK-SCOPE | R04 | module self-checks exercised via WP2 checks against the corpus (no pytest — selftest is the harness) |

### WP2 — the flip (7 + 2 live, DEFERRED era ends)

Shared bar: registry row gains its fn; the family's committed cases verdict exactly per `expected_when_implemented` (fail ⇒ exit 2 + named entry at annotated pointer; pass ⇒ exit 0, zero fail entries); new cases authored `{phase: "item-2", expected: "fail", …}` directly.

| ID | P | Task (file-level) | Depends | Pass/fail |
|---|---|---|---|---|
| R06 | [P] | CHK-CHAIN in `checks/run_directory.py` | R05 | shared bar (FP1) |
| R07 | [P] | CHK-TREE: digest arm, delta-coverage arm, ref-in-writes arm; workspace-write exemption | R05 | `unrecorded-write` fail; `added-under-tests` **exit-0 green under the whole live suite** (FP2) |
| R08 | [P] | CHK-WRITER (genesis-anchored config id) | R05 | shared bar (FP3) |
| R09 | [P] | CHK-GENESIS: pin presence, anchor equality, orphan (non-empty tree match w/o parent_run), counter-carry + NEW `counter-not-carried/` (parent+child pair) | R05 | both committed cases + new case fail per annotation (FP4) |
| R10 | [P] | CHK-GATE-BIND per C2 + NEW `tree-mismatch/` case | R05 | `unbound-outcome` + `tree-mismatch` fail (FP5) |
| R11 | [P] | CHK-SCOPE: hard-protected set (protected − tests_globs), write_scopes w/ tests-add exception, maker modify/delete under tests_globs, history-resolved `sha256_before` | R05 | two fail cases + the pass case per annotation (FP6) |
| R12 | [P] | CHK-REWORK: per-edge monotone counters ≤ max, parent-carried + NEW `over-cap-across-parent/` | R05 | `over-cap` + new case fail (FP7) |
| R13 | [P] | CHK-DECISIONS item-2 fn: canonical-byte dedup across distinct handoffs in one target | R05 | `boilerplate-item2` fails at second artifact's pointer (FP8) |
| R14 | [P] | CHK-THRESH item-2 fn: genesis anchor equality gates threshold resolution | R05 | `genesis-pinned-item2` fails (FP9) |
| R15 | | Registry flip: every row carries a fn (dual rows two live fns); `checks/deferred.py` **deleted**; `run_core` emits item-2 entries live; report contains zero `deferred` | R06–R14 | any validate report: 26 check ids, no deferred outcome (HP1) |
| R16 | | CHK-DEFER inversion in `registry.py`/`selftest.py` auditors + NEW fixture `CHK-DEFER/deferred-after-implementation/` (retiring `report-claims-green/`) | R15 | doctored lingering-DEFERRED report rejected; live reports pass (FP10) |
| R17 | | Selftest invalid-corpus reinterpretation: `expected: deferred` resolves through `expected_when_implemented`; valid + cold-start must be green under the full live suite | R15 | every former DEFERRED case verdicts per annotation without `expect.json` edits (HP2) |

### WP3 — gate-runner (parallel lane after WP1)

| ID | P | Task (file-level) | Depends | Pass/fail |
|---|---|---|---|---|
| R18 | | `runner.py` skeleton + `pyproject` console script `gate-runner`; argv contract (`run`/`--resume`/`--parent`/`--clock`/`--bind`/paths); F1 usage taxonomy (exit 1, nothing written); NEW `errors/` cases: runner missing-config + unknown-harness | R03 | both error cases exit 1 with empty run dir; `gate-runner --help` exit 0 |
| R19 | | Template fill (shlex-split + `{token}` substitution; unresolved ⇒ usage) + role invocation via `subprocess.run`; workspace scan/diff (F2 exclusions) → `writes[]` + `input_tree_digest` | R18 | fill rejects unknown tokens; scan of the workspace template reproduces a pinned map (scripted assertion in selftest §orchestrator) |
| R20 | | Genesis + ledger writing via `ledger_model`: compact-canonical lines, chain digests, config/registry pins, `--parent` (parent final-line digest + per-edge counter seed) | R05, R18 | a written ledger re-verifies under CHK-CHAIN/GENESIS/TREE functions directly |
| R21 | | Gate execution per `KernelConfig.gates[]`: run tool argv, record report artifacts at the `gate_run` entry with `input_tree_digest`, emit `GateOutcome` objects (threshold from named config values, `attempt_number`) | R19, R20 | outcomes bind under CHK-GATE-BIND against the entry (C2 procedure green) |
| R22 | | Conveyor branching: handoff finalization merge (draft + runner outcomes → canonical `handoff.json`, draft removed); in-process `run_validate` between runs; per-gate repair (attempt ≤ max) + cross-stage rework edges (per-edge counters ≤ max); bound-exceeded ⇒ final `failed` entry + exit 2; complete ⇒ exit 0 | R21 | branch coverage via the WP4 scenarios (green path, repair path, rework path, bound-exceeded path) |
| R23 | | Serialization (C4): at each handoff, copy `required_mappings` artifacts through `SpecKitMapping` rows into the workspace's declared roots (runner output, not in `writes[]`) | R22 | copies exist + byte-match sources after a scenario run |
| R24 | | `--resume`: verify existing ledger via the WP2 check fns; refuse on any red (exit 2, nothing appended); else reconstruct position (stage/attempt/counters) and continue | R22 | doctored-prefix fixture refused; interrupted fixture completes (FP11/HP7 substrate) |

### WP4 — orchestrator corpus + goldens

| ID | P | Task (file-level) | Depends | Pass/fail |
|---|---|---|---|---|
| R25 | | `kernel/corpus/orchestrator/`: `role_stub.py` + `gate_stub.py` (scenario-table-driven, attempt-aware, deterministic bytes); stub descriptor set (3 declared stub harnesses, full exit maps incl. 2/3); stub kernel-config (C1 `gates[]` → `{python}` stub argv), stub role-registry (C1 `invocation` values), stub speckit-mapping; `workspace-template/`; `scenarios/{green,rework,resume,parent}.json` | R01 | stub artifacts validate against 1.1.0 schemas; CHK-HARNESS-ROWS green on the stub descriptor set |
| R26 | | Generate + commit goldens via the pinned runner (`--clock fixed`, `--bind`): `runs/orchestrator-green/`, `runs/orchestrator-rework/` (attempt-2 repair, cross-stage edge w/ `DebugReport`, within bounds, ends green), `runs/orchestrator-resume/{interrupted,completed}/`, `runs/orchestrator-parent/{parent,child}/`; regen hook wired into `regen_corpus.py` | R22–R25 | each golden validates exit 0 under the full live suite; rework golden shows attempt 2 + rework edge + DebugReport ref (HP5/HP6/HP8/FP12/FP13) |
| R27 | | Selftest §golden-runs: execute green + rework scenarios twice each into temp dirs; byte-compare against goldens and between executions; `contract-lint` green over each produced dir; zero-DEFERRED assertion over every report | R26 | section green; a doctored golden byte flips it red (spot tamper check) |
| R28 | | Selftest §resume + §serialization: resume the committed interrupted fixture → byte-equals completed golden; doctored-prefix refusal (exit 2, ledger unchanged); serialization copies present + byte-correct in the post-run workspace | R24, R26 | section green (FP11, HP7, HP9) |

### WP5/WP6 — gate closure + records

| ID | P | Task (file-level) | Depends | Pass/fail |
|---|---|---|---|---|
| R29 | | Selftest arithmetic update: 26 families (bijection unchanged), zero DEFERRED anywhere, exit codes {0,1,2} exercised, golden-run coverage counted; full `contract-lint selftest` green | R17, R27, R28 | selftest exit 0, all sections |
| R30 | [P] | Docs: `ledger-chain.md` C2 amendment (+ gate-event `input_tree_digest`), `corpus-guide.md` (orchestrator fixtures, golden regeneration, flip semantics), `conformance.md` (runner-port admission via goldens), `validator/README.md` (third CLI), `ledger/README.md` | R26 | docs name the two-tree model + golden procedure; no harness tokens outside allowed scopes |
| R31 | | `validator/scripts/acceptance.sh` clean-copy offline run (unchanged contract, `PYTHON=` pin) | R29 | exit 0 (HP10) |
| R32 | | Records: spec/plan/tasks status flips (IMPLEMENTED + build record), `docs/architecture/log.md` entry, memory update; ADR 0002 Accepted-flip note verified (done at PLAN-OK) | R31 | statuses consistent; log entry present |

## 3. Dependency spine (critical path)

R01 → R02 → R03 → R04 → R05 → {R06–R14 [P] → R15 → R16/R17} ∥ {R18 → R19/R20 → R21 → R22 → R23/R24} → R25 → R26 → R27/R28 → R29 → R30/R31 → R32. Widest fan-out: after R05, nine check tasks run in parallel; the runner lane (R18–R24) needs only R03+R05 and runs beside WP2.

## 4. Stage-4 analyze verdict (run 2026-08-07)

**No CRITICAL findings** (no constitution-invariant violation, no zero-coverage criterion, no reference to a non-existent file/API). Detail:

- **Cross-artifact consistency:** spec target-artifact table ↔ plan §2 tree ↔ tasks are 1:1 (checked item-by-item); the CHK realization table covers exactly the 7 item-2 rows + 2 dual halves — no new check id is introduced (the 26-family bijection is untouched, matching the item-1 spec's single-enumeration clause). The C2 amendment is recorded in three places that must agree (spec C2, plan §3 binding row, R30's ledger-chain amendment) — flagged as a doc-sync point in R30's pass/fail.
- **Coverage:** all 24 EARS criteria map to tasks (§1 matrix, both directions); every task traces to ≥1 criterion or scaffold necessity (R02/R04/R05 are scaffold-necessity: the restamp engine and formula source have no EARS bullet of their own but every flip criterion depends on them).
- **Grounding (probed on this machine, 2026-08-07):** `tooling/sdd-roles/.venv` exists with `contract-lint`/`gate-wrap` installed (python 3.12.2, `--system-site-packages`, jsonschema 4.23.0 — inside the `>=4.21,<5` pin); baseline `contract-lint selftest` **exit 0, 12/12 sections, 12 deferred cases** (run at analyze time — the pre-item-2 gate is green before implementation starts, the Stage-4 baseline rule); `checks/deferred.py` exists (R15 deletes it); `registry.py` rows match the seven ids + two dual ids exactly; every corpus family/case named in §2 exists at its stated path; `expected_when_implemented` present on all 12 item-2 expect.json files (verified: 11 `fail` + 1 `pass`); no new dependency introduced by any task (stdlib only — `shlex`, `subprocess`, `os.walk`, `hashlib` all stdlib; the C3 sole-dependency clause holds).
- **Constitution:** every technology pick carries its envelope (plan §3); the G1 table names each new abstraction with the rejected simpler thing; ADR 0002 is the one Ask-first item and is drafted Proposed per the house rule; dependency inversion is load-bearing twice (checks+runner on `ledger_model`; corpus over implementations per ADR 0001/0002).
- **Baseline:** workspace gates `<none>`; the item's own gate substitutes (extended selftest via acceptance.sh), green-before-start verified above.

## 5. Next

**PLAN-OK gate (F1–F4 + SPEC-OK) → sdd-implement, R01 first.** Suggested order honors corpus-first: WP0 lands the restamped contract surface before any behavior; the WP2 flip and the WP3 runner then build against a stable 1.1.0 corpus; goldens (WP4) are generated, not hand-authored — the runner writes its own conformance fixtures under the pinned clock, and the selftest holds it to them forever after.
