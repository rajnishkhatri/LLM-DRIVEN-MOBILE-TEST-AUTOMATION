# Tasks: SDD Roles Write Guard — D7 floor (Track A, build item 3)

**Spec:** `docs/sdd/specs/sdd-roles-guard.spec.md` · **Plan:** `docs/sdd/plans/sdd-roles-guard.plan.md`
**Status:** IMPLEMENTED 2026-08-07 — all 28 tasks landed; gate green (16/16 sections ×2 byte-identical, zero DEFERRED, 23 guard cases, acceptance PASS, tamper trio verified, G21 zero-runner-diff byte-verified).

**Honest notes (defects caught during bring-up, all by the gate/process itself):**
1. **CHK-NEUTRAL caught `guard.py`'s own docstring** — the phrase "Claude-semantics" tripped the harness-token scan on the first golden regeneration (every between-run validation went red); reworded neutrally. The per-invocation self-integrity scan covered the new module automatically — the anti-rot design working as intended.
2. **Schema closedness walker rejected the dictionary-shaped `operation.map`** — the house rule is "no open-key objects anywhere"; converted to `{from, to}` row-array form mirroring `exit_code_map` (F2's field set preserved, representation adjusted — recorded here, not silently).
3. **CHK-ARM flagged the unhooked scenario's lone-maker arm** (arms need a diagnostic-capable role unless declared); resolved with the schema's `ablation` marker (`no-diagnostic-lone-maker`) — the honest declared form, not a fake checker.
4. **The first tamper-3 attempt was a no-op**: the sed pattern ("coder stage complete") lives in the handoff artifact, not the ledger line, so the file never changed and green was legitimate. Redone by flipping a real digest hex char → `orchestrator-goldens` red. Lesson recorded: tamper verification must verify the tamper itself landed.

## Task list (G01–G28, dependency spine WP0→WP6)

| id | wp | task | done-when |
|---|---|---|---|
| G01 | WP0 | Extract `scopes.py`: `match_any`, hard-protected assembly, tests diff-aware rule, scope-arm decision as pure functions over `(config, registry, role_id)` | module imports clean; no behavior change intended |
| G02 | WP0 | Refactor `checks/run_directory.py` (`chk_scope` + `HARD_PROTECTED_KEYS`/`_match_any` consumers) onto `scopes.py` | grep shows single definition site |
| G03 | WP0 | Certify WP0 | `contract-lint selftest` exit 0, report byte-identical to the 2026-08-07 baseline (14 sections, 12 flipped) |
| G04 | WP1 | Schema: additive optional `hooks` closed object per plan F2 on descriptor rows | schema 2020-12 valid; closed; existing fixtures still validate pre-restamp |
| G05 | WP1 | Data: `hooks` rows for claude-code/cursor/copilot in `kernel/descriptors/invocation-descriptors.json` + stub row in `descriptors-stub.json` | rows schema-valid |
| G06 | WP1 | `regen_corpus.py restamp --to <version>` parametrization | `--to 1.1.0` on current corpus = 0 rewrites (idempotence unchanged) |
| G07 | WP1 | Run `restamp --to 1.2.0`; add valid-corpus InvocationDescriptorSet case exercising `hooks` | restamp idempotent on 2nd run; never writes expect.json |
| G08 | WP1 | Post-restamp certification | selftest exit 0; all expected verdicts preserved |
| G09 | WP2 | `guard.py` CLI skeleton: argv parse, `decide` stdin protocol, F1 exit split, F3 decision line | FP9 behavior exact (exit 1, no stdout decision line) |
| G10 | WP2 | Decision core: rules 1–8 in spec order over `scopes.py`; ancestor-walk symlink resolution; exists-despite-create | unit-exercised via corpus only (no pytest — house rule) |
| G11 | WP2 | Decision corpus ~18 cases: FP1 (abs / `..` / symlink-setup), FP2, FP3 (run-dir + ledger), FP4 (each hard key incl. anti-unhook), FP5 (modify, delete, create-but-exists), FP6, FP7 (first-block order), FP8 (malformed / unknown role / invalid config), HP1, HP2, HP8 (pointer-extraction payload) | each case: config+registry+workspace+request+expect |
| G12 | WP2 | selftest `guard-decisions` section: run every case ×2, byte-compare {exit, stdout, reason}; symlink case built in temp at run time per plan risk row | section green, deterministic |
| G13 | WP3 | `guard.py mount`: render per F2 (one rule per registry role, `--role` baked, `gate-wrap`-wrapped command), canonical JSON bytes | renders for all 4 rows |
| G14 | WP3 | Commit mount goldens ×4 under `kernel/corpus/guard/mounts/<harness>/` | bytes stable across double render |
| G15 | WP3 | selftest `guard-mount` section + `corpus/errors/` cases: FP10 (row without hooks), FP9 mount-argv | section green |
| G16 | WP4 | `role_stub.py` `guarded_write` action: read mounted config at descriptor `mount_path`, invoke hook command, honor exit | stub row payload shape ≠ neutral shape (HP8 live proof) |
| G17 | WP4 | `scenarios/hooked/`: config/registry/mapping/scenario/workspace-template; recipe = mount → gate-runner; blocked attempt on a protected path mid-scenario | scenario deterministic |
| G18 | WP4 | `scenarios/unhooked/`: same role behavior, no mount; rogue tests-write lands | FP11 shape |
| G19 | WP4 | `goldens.json` recipes + `regen_corpus.py goldens`; commit `runs/orchestrator-hooked/` + `-unhooked/` | goldens committed with workspace-after |
| G20 | WP4 | selftest sections: hooked (×2 byte-identity, contract-lint 0, ledger contains no blocked-write trace) + unhooked (gate-runner exit 2, `failed` entry, CHK-SCOPE finding named) | sections green |
| G21 | WP4 | Assert `gate-runner`/`runner.py` diff = 0 lines for item 3 (S7) | diff empty vs item-2 close |
| G22 | WP5 | `kernel/docs/tamper-rubric.md`: verbatim 12 categories (source-cited), coverage column {guard-blocked, retro-lint, gate-reverify, residual-manual}, 11→12 correction note | every category has exactly one primary coverage tier |
| G23 | WP5 | `conformance.md` #8 guard-port admission; corpus-guide + validator/README + ledger README updates | docs current |
| G24 | WP5 | CHK-NEUTRAL green over `guard.py`/`scopes.py`; confirm rubric doc placement is outside token-scan scope | selftest neutral section green |
| G25 | WP6 | `acceptance.sh` guard assertions; selftest arithmetic/summary keys; `__init__`/pyproject → 0.3.0; `write-guard` console script | clean-copy acceptance PASS |
| G26 | WP6 | Final certification: selftest ×2 byte-identical, sections count updated, `deferred_entries == 0` | FINAL GATE EXIT 0 |
| G27 | WP6 | Tamper-verification trio: doctored mount-golden byte → guard-mount red; doctored decision expect → guard-decisions red; scenario re-allow → golden-run red | each red in the named section, then restored green |
| G28 | — | Flip spec/plan/tasks to IMPLEMENTED with build record + honest notes; `docs/architecture/log.md` entry; memory update | records written |

## Coverage matrix

| criterion | tasks |
|---|---|
| FP1–FP8 | G10, G11, G12 |
| FP9 | G09, G15 |
| FP10 | G13, G15 |
| FP11 | G18, G19, G20 |
| FP12 | G12, G15, G20, G27 |
| HP1, HP2 | G10, G11, G12 |
| HP3 | G13, G14, G15 |
| HP4 | G16, G17, G19, G20 |
| HP5 | G11, G12 |
| HP6 | G06, G07, G08 |
| HP7 | G25, G26 |
| HP8 | G11 (pointer case), G16 (stub payload shape) |

## Stage-4 analyze (grounded, 2026-08-07)

- Baseline gate: `contract-lint selftest` exit 0, **14 sections pass, 12 flipped cases, 0 deferred entries, validator 0.2.0, schema 1.1.0** — the WP0 byte-identity reference exists and is green.
- `chk_scope` ground truth read from source: hard-protected arm (all roles), `added`+tests exemption (all roles), scope arm, maker-tag modify/delete arm, history-resolution arm — `scopes.py` extraction boundary is exactly the first four (the history arm stays retro-only; the live analogue is disk existence, spec S4). No contradiction found between spec table and implemented retro semantics.
- Role `tag` enum is closed `{maker, checker}` — rule 6 is fully determined by existing data; **no new role field needed** (a would-be `may_modify_tests` flag is rejected as schema creep).
- Descriptor row schema is closed with 7 required fields — `hooks` must be optional to keep old fixtures valid pre-restamp (G04 ordering constraint verified).
- `regen_corpus.py` restamp + goldens machinery exists from item 2 (single `--to` parametrization needed); recipe runner supports mount-before-runner steps as plain recipe entries.
- Risk singled out: symlink corpus case portability → runtime-setup decision (plan §6) folded into G12, not a committed symlink.
- No CRITICAL findings. Verdict: **ready for the combined gate.**
