# Plan: SDD Role Orchestrator — gate-runner + run-directory checks live (Track A, build item 2)

**Status:** APPROVED — **PLAN-OK recorded 2026-08-07; F1–F4 ratified as drafted** (owner; SPEC-OK granted at the same gate, house pattern). ADR 0002 flipped Proposed → Accepted same day.
**Spec:** `docs/sdd/specs/sdd-roles-orchestrator.spec.md` (v2, C1–C4 locked)
**Constitution:** `.cursor/rules/architecture-principles.mdc`
**Gates:** `<none>` in this workspace — the item-2 gate is `contract-lint selftest` (extended per spec) + the golden-run assertions, executed by `validator/scripts/acceptance.sh` (clean copy, offline, sole dependency).
**ADR posture:** **ONE new ADR — 0002** in `docs/architecture/adrs/tooling/sdd-roles/` (*Golden-run conformance for the gate orchestrator: stub-harness fixtures as the behavioral contract*), drafted **Proposed** (C3), flips Accepted at PLAN-OK. The C2 two-tree amendment is a spec-recorded normative clarification of `ledger-chain.md`, not a new decision record (it realizes S8; the item-1 spec's row wording is annotated forward, house rule). No other decision leaves the spec envelope.

## 1. Approach (A1 — simplest thing that satisfies the criteria)

One new module pair in the **existing** package: `ledger_model.py` (the ledger-chain formulas as functions: chain verify, artifact-map fold + digest, genesis anchoring, history replay) consumed by both `checks/run_directory.py` (the 7+2 checks) and `runner.py` (the `gate-runner` CLI) — one source for every digest rule, so the orchestrator cannot drift from the checks that judge it. Stdlib-only additions; checks stay plain functions in the data registry; the conveyor is a plain loop over arm roles with two bounded counters. Least machinery:

- **No framework, no plugin system, no async.** `subprocess.run` per invocation/gate, sorted `os.walk` scans, canonical JSON everywhere a byte is written.
- **No new dependency.** `gate-runner` is a third console script of the same package (spec home decision); C3's single-dependency clause is untouched.
- **No speculative harness code.** Template fill + exit-code branching consume descriptor rows; the only executables the gate ever spawns are `{python}`-bound interpreter stubs from corpus data (C3).
- **Checks validate the runner's own output in the same gate** — the orchestrator earns trust the way ports do: by the corpus, not by review (S3).

**G1 items — new abstractions, with the simpler thing rejected:**

| Abstraction | What it buys | Simpler thing rejected, why |
|---|---|---|
| `ledger_model.py` shared by checks + runner | One implementation of chain/tree/genesis rules; runner-vs-checks drift structurally impossible | Each side computes its own digests — two formula sources, the exact drift class item 1 eliminated for check lists |
| Handoff finalization split: role authors `handoff.draft.json`, runner merges its published tool-fact `gate_outcomes[]` → canonical `handoff.json` | Fabricated outcomes become *inexpressible in the final contract* (only runner-written outcomes exist), not merely bindable-and-caught | Role authors the complete handoff — outcomes would be role-claimed bytes; anti-BMAD would rest on CHK-GATE-BIND alone |
| Scenario-driven generic stubs (one `role_stub.py` + one `gate_stub.py`, per-scenario JSON behavior tables) | New orchestrator fixtures are corpus data, not new code; attempt-aware repair paths stay declarative | Bespoke stub script per scenario — code where data suffices, N scripts to review |
| `--bind key=value` template fill (machine values injected at invocation) | Committed fixtures stay byte-portable (no absolute paths); CHK-NEUTRAL scope extends cleanly over runner source | Hardcoded interpreter/fixture paths in committed descriptors — breaks byte-identity and portability |
| Committed `scripts/regen_corpus.py` | The 1.1.0 restamp + C2 regeneration + golden-run refresh is reproducible and reviewable (mass digest recompute is not hand-editable) | Throwaway uncommitted script (item-1 precedent) — acceptable for one-shot genesis, wrong for a restamp that item 3+ will need again |

## 2. Repository architecture (deltas over the item-1 tree)

```
tooling/sdd-roles/
├── kernel/
│   ├── VERSION                          1.0.0 → 1.1.0 (F4 restamp: all schema consts +
│   │                                    all corpus schema_version strings + digest recompute)
│   ├── schemas/                         3 files gain optional closed additions (C1/C2):
│   │   ├── role-registry.schema.json      roles[].invocation {prompt?, agent?, agents_file?, model?}
│   │   ├── kernel-config.schema.json      gates[] {id, tool, argv[], threshold?}
│   │   └── stage-ledger-entry.schema.json regular_entry.input_tree_digest? (gate events)
│   ├── corpus/
│   │   ├── invalid/                     families unchanged in count (26); new cases inside:
│   │   │   ├── CHK-GATE-BIND/tree-mismatch/          (C2 arm, fail)
│   │   │   ├── CHK-GENESIS/counter-not-carried/      (parent+child pair, fail)
│   │   │   ├── CHK-REWORK/over-cap-across-parent/    (parent+child pair, fail)
│   │   │   └── CHK-DEFER/deferred-after-implementation/  (replaces report-claims-green)
│   │   ├── runs/
│   │   │   ├── cold-start/              C2-regenerated (reports recorded at gate_run entry,
│   │   │   │                            input_tree_digest present, chains recomputed)
│   │   │   ├── orchestrator-green/      golden complete run (committed gate-runner output)
│   │   │   ├── orchestrator-rework/     golden: per-gate repair + cross-stage edge + DebugReport
│   │   │   ├── orchestrator-resume/     interrupted/ (prefix) + completed/ (golden result)
│   │   │   └── orchestrator-parent/     parent/ + child/ (continuation pair, carried counters)
│   │   └── orchestrator/                stub-harness fixture data (corpus, CHK-NEUTRAL-exempt):
│   │       ├── descriptors-stub.json    3 stub harness rows (full exit maps incl. 2/3)
│   │       ├── kernel-config-stub.json  gates[] → {python} gate_stub argv (C1 fields live here)
│   │       ├── role-registry-stub.json  roles[].invocation filled for stubs
│   │       ├── speckit-mapping-stub.json
│   │       ├── stubs/role_stub.py + stubs/gate_stub.py   (deterministic byte-writers)
│   │       ├── scenarios/<name>.json    (role,stage,attempt)→actions; (gate,attempt)→exit/report
│   │       └── workspace-template/      tiny workspace copied to temp per gate execution
│   └── docs/                            ledger-chain.md (C2 amendment), corpus-guide.md
│                                        (orchestrator-fixture rules), conformance.md (runner
│                                        port procedure: reproduce goldens byte-identically)
├── validator/
│   ├── pyproject.toml                   + console script gate-runner → sdd_roles_validator.runner:main
│   ├── scripts/
│   │   ├── acceptance.sh                unchanged contract (PYTHON= pin, offline, sole dep)
│   │   └── regen_corpus.py              F4 restamp + C2 regen + golden refresh (dev tooling,
│   │                                    never on the acceptance path)
│   └── src/sdd_roles_validator/
│       ├── ledger_model.py              chain/tree/genesis/replay — the ONE formula source
│       ├── checks/run_directory.py      CHK-CHAIN/TREE/WRITER/GENESIS/GATE-BIND/SCOPE/REWORK
│       │                                + chk_decisions_item2 + chk_thresh_item2
│       ├── checks/deferred.py           DELETED (registry rows all carry functions)
│       ├── runner.py                    gate-runner CLI + conveyor engine
│       ├── loader.py                    + raw line bytes per ledger line; multi-ledger targets
│       ├── registry.py                  rows flip to live fns; dual rows gain item-2 fns;
│       │                                CHK-DEFER auditor inverted (implemented ⇒ never deferred)
│       └── selftest.py                  invalid-corpus reinterpretation (expected_when_implemented);
│                                        + sections: flip-audit, golden-run byte-identity ×2,
│                                        resume, tamper-refusal, serialization presence
└── ledger/                              now actually populated by gate-runner runs (README updated)
```

## 3. Technology selections (inside spec envelopes)

| Concern | Pick | Envelope |
|---|---|---|
| Runner transport | `subprocess.run(argv, cwd=workspace)` — argv built by shlex-splitting the descriptor `command_template` then substituting `{placeholder}` tokens per split part; unresolved placeholder = usage error (exit 1) | S2, C3 |
| Template fill map | role `invocation` fields (C1) ∪ reserved `{workspace, run_dir, stage, role, attempt}` ∪ `--bind` pairs (machine values: `{python}`, `{fixture_dir}`) | S2 |
| Workspace scan | sorted `os.walk`, exclusions exactly `{run_dir, ledger_dir, .git}` (F2); file map path→sha256; `input_tree_digest` + `writes[]` diff from before/after maps | S7 |
| Ledger bytes | one compact canonical JSON line per entry (`sort_keys`, `ensure_ascii`, separators `(",", ":")`) + LF — matches committed fixture style; chain digest over exact raw bytes | S8, ledger-chain.md |
| Clock | `--clock fixed:<iso8601>` stamps every `ts` verbatim; `--clock wall` (default) uses UTC now; golden gate always pinned | S6 |
| Handoff finalization | draft + runner outcomes → `canonical_dumps`-style stable JSON (2-space, sorted) matching corpus artifact style; draft deleted after merge | §1 G1 |
| Gate reports | tool stubs write their own report files `reports/<gate>-a<attempt>.json`; runner records them as entry artifacts + emits outcome objects | C2 binding |
| Between-run validation | in-process `run_validate(run_dir, kernel_dir)` (same package import — no subprocess needed, NetGuard-safe as selftest already proves) | S4 |
| Serialization (C4) | copy handoff + current ledger file to `SpecKitMapping` targets under the workspace's declared roots at each handoff boundary; copies are runner outputs **not recorded in `writes[]`** (role-write audit domain only; golden byte-identity + a selftest presence assertion gate them) | S8/C4 |
| Resume verification | reuse the check functions over the existing ledger before continuing; any red = refuse (exit 2) | S5 |

## 4. Plan-level values the spec delegated

| Value | Setting |
|---|---|
| `gate-runner` exit taxonomy (F1) | `{0 run complete + final validation green, 1 usage/internal (unknown harness row, missing/invalid config/registry/descriptors, malformed clock, absent workspace, unresolved placeholder — nothing written), 2 run failed (gate red at bound, validation red at bound, resume refusal on doctored ledger)}` — an honestly-failed run's directory still validates green under `contract-lint` (failure lives in outcomes, never in ledger integrity) |
| Workspace scan exclusions (F2) | fixed in code: the active run directory, the configured ledger directory, `.git/` — not configurable (a config knob would let a run hide writes from its own scan) |
| Fixture home + binding convention (F3) | stub data under `kernel/corpus/orchestrator/` (corpus ⇒ CHK-NEUTRAL-exempt by existing scope); goldens under `kernel/corpus/runs/orchestrator-*/`; machine values injected only via `--bind python=… fixture_dir=…` |
| Restamp procedure (F4) | `scripts/regen_corpus.py`: flip every schema const + corpus `schema_version` string 1.0.0→1.1.0; recompute ledger chains, `handoff_contract_digest`s, artifact-ref digests, tree digests; apply the C2 cold-start/CHK-GATE-BIND regeneration; regenerate goldens by executing the runner pinned; `expect.json` files untouched (asserted by the script: it never writes one) |
| Rework counter model | per edge `(target_role, from_stage)`: counts start at 1, +1 per occurrence, cumulative across `parent_run` (child's first occurrence = parent's last + 1); per-gate repair uses `attempt_number` on outcomes bounded by the same `rework.max` (K=3 fixture value) |
| Boilerplate comparison (CHK-DECISIONS item-2) | canonical JSON bytes of the full decision item (provenance included) equal across two *distinct* handoff artifacts in one target ⇒ fail at the second artifact's pointer |
| Orphan rule detail | genesis with `parent_run: null` and a **non-empty** starting `tree_digest` equal to any entry `tree_digest` of another ledger in the target ⇒ orphan (empty-tree geneses are never orphans — every fresh run starts empty) |
| `resume_handle` / `agent_definition_digest` | handle = `"{role}-a{attempt}"` (runner-composed, deterministic — harness persistence is cache, S8); definition digest = sha256 of the resolved role-stub script bytes (the anti-shadowing pin exercised with real values) |
| CHK-DEFER inversion | auditor rule set: (a) any report row `outcome: deferred` for a check whose registry row carries a function ⇒ fail; (b) unimplemented phase rows (none exist after this item) must still report DEFERRED ⇒ the rule survives for any future phased check; fixture `deferred-after-implementation/` carries a report with a lingering DEFERRED row |
| Selftest flip interpretation | invalid-corpus section: `expected: deferred` cases now resolve through `expected_when_implemented` — `fail` ⇒ exit 2 + named check entry (+ pointer when annotated); `pass` ⇒ exit 0 and **zero fail entries of any check** (the added-under-tests case must be green under the whole live suite) |
| New-case annotations | new item-2 cases are authored directly as `{phase: "item-2", expected: "fail", exit_code: 2, json_pointer: …}` — the DEFERRED era is over when they land (they never carry `expected_when_implemented`) |

## 5. Work packages and dependency order

| WP | Content | Depends |
|---|---|---|
| **WP0** | Schema minors (C1/C2 optional closed fields), `VERSION` 1.1.0, `regen_corpus.py` restamp of the whole corpus (F4) incl. C2 cold-start/CHK-GATE-BIND regeneration; selftest drift + existing v1 checks stay green over the restamped corpus | — |
| **WP1** | `ledger_model.py` (chain verify, map fold + digest, genesis anchor, history replay incl. parent linkage) + `loader.py` raw-line-bytes extension; unit-style assertions live in selftest sections, not pytest | WP0 |
| **WP2** | `checks/run_directory.py`: the 7 checks + 2 dual item-2 halves; registry flip (all rows carry fns, `deferred.py` deleted); CHK-DEFER inversion; selftest invalid-corpus reinterpretation; new invalid cases (`tree-mismatch`, `counter-not-carried`, `over-cap-across-parent`, `deferred-after-implementation`); every former DEFERRED case verdicts per its annotation | WP1 |
| **WP3** | `runner.py`: argv/template fill, genesis (+`--parent`), conveyor loop (entered → invoke → scan → gates → outcomes → merge → validate → branch), bounded repair + cross-stage rework, `--resume` (verify-then-continue, refuse on red), serialization (C4), exit taxonomy (F1); `pyproject` third console script | WP1 (∥ WP2) |
| **WP4** | Orchestrator corpus: stubs, scenario tables, stub config/registry/descriptors/mapping, workspace template; generate + commit the four golden run sets via the pinned runner (green, rework, resume pair, parent pair) | WP3 |
| **WP5** | Selftest orchestrator sections: golden-run execution ×2 byte-identity, resume completion equals committed golden, tamper-refusal (doctored prefix ⇒ exit 2), serialization presence, arithmetic update (26 families, zero DEFERRED, exit codes {0,1,2}, golden-run coverage) | WP2, WP4 |
| **WP6** | Docs (ledger-chain C2 amendment, corpus-guide orchestrator rules, conformance runner-port extension, validator README, ledger README); ADR 0002 flip at PLAN-OK; `acceptance.sh` end-to-end on a clean offline copy; status flips + `docs/architecture/log.md` entry | WP5 |

Corpus arithmetic at completion: 26 invalid families (bijection unchanged — new cases join existing families); valid 8 + cold-start + 4 orchestrator golden sets; **zero DEFERRED entries anywhere**; exit codes {0,1,2} exercised; every stub descriptor mapping row still gate-wrap-covered (unchanged corpus); every golden run validates green with all 26 checks live.

## 6. Constitution alignment & risks

Alignment: single formula source (`ledger_model`) is dependency inversion doing load-bearing work — checks and runner both depend on the abstraction, neither on the other; the registry keeps open/closed extension (flipping a phase = giving a row its function; no dispatch edits); the handoff-finalization split assigns tool facts to the deterministic principal and judgment to roles — single responsibility at the contract level; every C1/C2 field addition is closed and optional (no silent breaking change; the restamp is loud and scripted); the golden-run gate extends corpus-as-contract (ADR 0001) to behavior instead of inventing a second conformance mechanism (ADR 0002 records exactly that).

Top risks: (1) **golden-run byte-identity across machines** — every byte the runner writes is canonical (compact-canonical ledger lines, canonical-dumps artifacts, pinned clock, POSIX-relative paths, `--bind`-isolated machine values); the double-execution section is the tripwire, and goldens are regenerated only by the committed script. (2) **restamp blast radius** (every corpus digest moves) — mitigated by doing it as WP0 with the *existing* v1 suite required green over the restamped corpus before any new check lands; the drift section catches any missed const. (3) **check/runner disagreement** — structurally reduced by `ledger_model`; the residual (runner semantics not covered by checks) is exactly what the golden `contract-lint`-green assertion covers. (4) **CHK-SCOPE role resolution on ledgers with unknown roles** — deterministic fail (“role not in registry ⇒ scopes unresolvable”), corpus-cased. (5) **selftest wall-time growth** (4 golden executions + temp copies) — bounded by fixture size; stubs are `-c`-scale scripts, workspaces a handful of files.

## 7. Gate

**CLOSED — PLAN-OK recorded 2026-08-07; F1–F4 ratified as drafted; SPEC-OK granted at the same combined gate.** ADR 0002 flipped to Accepted the same day. **sdd-implement ran 2026-08-07: all 32 tasks landed — extended `contract-lint selftest` green (14 sections, byte-identical, zero DEFERRED, 12 flipped cases) and the offline clean-copy acceptance run PASS** (tasks file header carries the build record incl. the three defects the gate itself caught during bring-up). The ratified readings, for the record:

- **F1 — `gate-runner` exit taxonomy:** `{0, 1, 2}` per §4 row 1, including the "honestly-failed run still validates green" rule (failure is an outcome, never ledger corruption).
- **F2 — workspace-scan exclusions fixed in code:** `{run_dir, ledger_dir, .git}` — deliberately not configurable, so a run cannot be configured to hide writes from its own scan.
- **F3 — fixture home + `--bind` convention:** stub data as corpus (`kernel/corpus/orchestrator/`), goldens under `runs/orchestrator-*/`, machine values only via `--bind` (byte-portable committed fixtures).
- **F4 — the 1.1.0 restamp:** whole-corpus version-string restamp with scripted digest recomputation (chains, handoff digests, refs, trees) via committed `regen_corpus.py`; `expect.json` annotations untouched (script-asserted); C2 fixture regeneration rides the same script.

On PLAN-OK: ADR 0002 flips Proposed → Accepted; tasks (`sdd-roles-orchestrator.tasks.md`) execute; the item-2 gate is the extended selftest via `acceptance.sh`.
