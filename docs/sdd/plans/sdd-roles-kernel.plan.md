# Plan: SDD Role Kernel — schema family + contract-lint validator + gate-wrap (Track A, build item 1)

**Status:** APPROVED — **PLAN-OK recorded 2026-08-07; F1–F4 ratified as drafted** (owner). Two post-approval amendments applied same day at tasks time, both inside the §4 adjustable-values class (recorded in the decision log): the item-2 stub count corrected **six → seven** (the CHK table has 7 pure item-2 rows + 2 dual-phase rows; §1/§2/§5/§6 fixed), and two delegated values added to §4 (`artifact_type` discriminator; `expected_when_implemented` annotation).
**Spec:** `docs/sdd/specs/sdd-roles-kernel.spec.md` (signed off 2026-08-07; C1–C5 locked, S1–S9 scope-locked)
**Constitution:** `.cursor/rules/architecture-principles.mdc`
**Gates:** `<none>` in this workspace — the committed golden corpus + the validator's `selftest` subcommand IS this build item's gate (spec acceptance bar).
**ADR posture:** **ONE new ADR raised per C4** — ADR 0001 in the new series `docs/architecture/adrs/tooling/sdd-roles/` (*Adopt corpus-as-contract with a conformance-gated reference validator*), drafted **Proposed**, flips Accepted at PLAN-OK. `.sdd/binding.toml` amended with the second ADR seam (C4). No other decision leaves the spec's envelope.

## 1. Approach (A1 — simplest thing that satisfies the criteria)

One Python package, two console entry points (`contract-lint`, `gate-wrap`), checks implemented as a **data registry** mirroring the CHK table, and a **corpus-first build order**: schemas + corpus cases land before the check logic that consumes them (A7 applied at artifact level — the contract exists before the tool that enforces it). Least machinery:

- **No framework, no plugin system, no config DSL.** `argparse` + `jsonschema` + `hashlib`; checks are plain functions keyed by CHK id.
- **No test framework in the acceptance path.** The clean-clone bar allows only the C3-declared dependency, so the gate executable is `contract-lint selftest` (stdlib), not a pytest suite.
- **No run-directory machinery beyond CHK-REFS.** The seven item-2 checks (CHK-CHAIN, CHK-TREE, CHK-WRITER, CHK-GENESIS, CHK-GATE-BIND, CHK-SCOPE, CHK-REWORK) exist only as registry rows that report DEFERRED plus their committed corpus cases (C5) — zero speculative implementation.

**G1 items — new abstractions this plan introduces, with the simpler thing rejected:**

| Abstraction | What it buys | Simpler thing rejected, why |
|---|---|---|
| `selftest` subcommand as the build-item gate executable | One body implements CHK-SELF/DET/NET/NEUTRAL/DEFER *and* serves as the clean-clone acceptance runner | pytest dev-suite — a second dependency, violating the "only the C3-declared dependency installed" acceptance clause |
| Sidecar `expect.json` per corpus case | Case artifacts stay byte-pristine and schema-exact; annotations survive the CHK-SELF temp-copy unchanged | Annotations embedded in case artifacts — closed schemas make extra fields schema-invalid, and embedding changes the very bytes/digests the cases pin |
| Check registry as data (`{check_id, phase, cluster, fn}`) + selftest-asserted **registry↔corpus bijection** | The spec's "single enumeration — no second list to drift" clause gets an executable mirror: a CHK row without a corpus family (or vice versa) fails selftest | Hardcoded call sequence — drift between spec table, code, and corpus becomes reviewable-only, the exact failure the clause exists to prevent |
| `declares[]` inside the InvocationDescriptor **set document** (F3) | Harness names live *only* in ID instances, so CHK-NEUTRAL stays a clean grep; the three-harness floor is expressed neutrally as `minItems: 3` (a count, not a name) | Harness list in `KernelConfig` — would put harness tokens in a non-ID instance, forcing exclusion creep into the CHK-NEUTRAL scope |

## 2. Repository architecture (C1 home)

```
tooling/sdd-roles/
├── kernel/
│   ├── VERSION                          schema_version single source: 1.0.0 (F4)
│   ├── schemas/                         8 closed JSON Schema 2020-12 files (C2), per-file $defs,
│   │                                    schema_version as required const in each:
│   │                                    role-registry / handoff-contract / stage-ledger-entry /
│   │                                    gate-outcome / debug-report / invocation-descriptor /
│   │                                    speckit-mapping / kernel-config  (.schema.json)
│   ├── descriptors/
│   │   └── invocation-descriptors.json  committed set instance: declares[] (3 harnesses) + rows[]
│   │                                    incl. exit-code maps w/ gate-tool exit-2/exit-3 rows —
│   │                                    the ONLY non-corpus home of harness tokens (S2/F3)
│   ├── docs/                            ledger-chain + tree_digest definition; provenance guide;
│   │                                    conformance-port rule (C3); corpus authoring guide
│   └── corpus/
│       ├── valid/<Type>/                ≥1 case per schema type; incl. the green ablation-arm
│       │                                case (S3) and a full KernelConfig with protected minimum
│       ├── invalid/<CHK-ID>/<case>/     artifact(s) + expect.json — one family per CHK id (26),
│       │                                incl. the 7 item-2 families expecting DEFERRED (C5)
│       ├── runs/cold-start/             run-directory fixture: ledger + artifacts resolvable at
│       │                                recorded sha256 (CHK-REFS in v1; item-2 checks' target)
│       └── errors/                      exit-1 usage cases (missing target, malformed invocation)
├── validator/
│   ├── pyproject.toml                   requires-python ">=3.11"; deps: jsonschema only (C3)
│   ├── src/sdd_roles_validator/
│   │   ├── cli.py                       contract-lint: validate | selftest subcommands
│   │   ├── gate_wrap.py                 gate-wrap: descriptor-driven exit-code translation
│   │   ├── registry.py                  the CHK table as data (id, phase, cluster, fn)
│   │   ├── loader.py                    path-independent artifact model (all checks consume
│   │   │                                loaded objects, never filesystem paths — CHK-SELF)
│   │   ├── checks/                      provenance.py, config_registry.py, deferred.py
│   │   ├── report.py                    canonical deterministic JSON report (CHK-DET)
│   │   └── selftest.py                  corpus run + DET double-run + NET socket guard +
│   │                                    NEUTRAL grep + SELF temp-copy + DEFER + bijection
│   └── README.md
└── ledger/                              .gitkeep + README (writer: gate-runner only — item 2+;
                                         exists so the protected-set path is real)
```

## 3. Technology selections (plan-level, inside spec envelopes)

| Concern | Pick | Envelope |
|---|---|---|
| Language/runtime | Python ≥3.11, stdlib + `jsonschema >=4.21,<5` (sole dependency, pinned major) | C3 |
| Schema dialect | JSON Schema draft 2020-12, committed files, `additionalProperties: false` everywhere; per-file `$defs`; **no `allOf` composition across closed objects** (the closed-schema × `$ref` composition trap — see risk 1) | C2 |
| Hashing | `hashlib.sha256`, full digests only (no truncated prefixes anywhere) | S7/S8 |
| CLI | `argparse`, console-script entry points `contract-lint` + `gate-wrap` | C3 |
| Report bytes | Canonical JSON: sorted keys, LF endings, `ensure_ascii`, 2-space indent, POSIX-relative paths, **no timestamps** | CHK-DET |
| Gate executable | `contract-lint selftest` (stdlib harness; dev-time pytest optional but never on the acceptance path) | acceptance bar |
| gate-wrap corpus stubs | `sys.executable -c "raise SystemExit(N)"` stub tools per mapping row (portable, offline, deterministic) | CHK-NET/DET |
| Install for acceptance run | `pip install -e validator/` on a clean clone, offline (deps pre-fetched wheel or vendored note in README) | acceptance bar |

## 4. Plan-level values the spec delegated

All adjustable without re-opening the plan unless marked (F*) — those are the flagged readings.

| Value | Setting |
|---|---|
| `schema_version` (F4) | **1.0.0** at first commit; SemVer discipline documented: item-2+ additive fields = minor, breaking = major (C5's whole argument is that no item-2 bump is expected) |
| Provenance object shape (S7) | `{source: role_authored\|tool_output\|environment_quoted, derived_from: [id…], fence?: {fence_id: <full sha256>, source_uri, retrieved_at}, tool?: {id, version, invocation_digest}}`; schema conditionals: `environment_quoted` ⇒ `fence` required; `tool_output` ⇒ `tool` required (allowlist membership is CHK-TOOLBIND, checked against KernelConfig) |
| Report format | `{schema_version, validator_version, target, checks: [{check_id, phase, outcome: pass\|fail\|deferred, artifact, json_pointer, detail}], summary: {pass, fail, deferred}, exit_code}`; entries sorted by (check_id, artifact, json_pointer) |
| Dual-phase rows (CHK-DECISIONS, CHK-THRESH) | **Two report entries each**: `phase: "v1"` pass/fail + `phase: "item-2"` DEFERRED — the no-silent-green rule applied to split rows; both sub-phases have corpus cases |
| `expect.json` sidecar | `{check_id, phase, expected: pass\|fail\|deferred, exit_code?, json_pointer?}` — unified across valid, invalid, and DEFERRED families; item-2 families additionally carry `expected_when_implemented: pass\|fail` so item 2 inherits executable annotations without re-authoring |
| `artifact_type` discriminator | Every schema carries a required `const` `artifact_type` (e.g. `"handoff_contract"`) so the loader resolves the applicable schema from content, never from filename or path — load-bearing for CHK-SELF's temp-copy path-independence |
| Error taxonomy | Unparseable JSON artifact = **validation failure** (exit 2, CHK-SCHEMA, pointer `""`); missing target path / bad CLI args = **usage** (exit 1, no report). Corpus `errors/` cases exercise exit 1 via selftest |
| CHK-NET mechanism | selftest patches `socket.socket` + `socket.create_connection` to raise before the in-process corpus run, and scans `sys.modules` post-run for network modules (`urllib.request`, `http.client`, …) in validator imports |
| CHK-DET mechanism | selftest runs the full corpus validation twice, byte-compares report + exit code (canonical JSON rules make PYTHONHASHSEED irrelevant by construction) |
| CHK-SELF mechanism | per invalid case: copy case dir to a tempdir (tempfile use lives in selftest only, never in check logic), re-run, assert identical verdict; assert the report names `expect.check_id` at `expect.json_pointer` |
| CHK-NEUTRAL scope | tokens `claude, cursor, copilot, anthropic, .claude/, .cursor/, .github/agents, .github/skills` (case-insensitive) over `kernel/schemas/**` + `validator/src/**` + registry check-ids; **exclusions:** `kernel/descriptors/` + `kernel/corpus/**` |
| `tree_digest` definition (pinned now, verified at item 2) | sha256 over bytewise-sorted lines `<posix-path>\0<sha256>\n` of the artifact map; documented in `kernel/docs/` so genesis fixtures pin real values |
| Protected-set shape (F2) | `KernelConfig.protected` = object with **7 required named keys** (`kernel_config`, `role_registry`, `ledger_dir`, `tests_globs`, `gate_configs`, `harness_enablement`, `speckit_constitution` — the last defaulting `const` to `.specify/memory/constitution.md`), each a non-empty path array. CHK-PROTECT corpus case = one key omitted |
| Harness declaration (F3) | descriptor set = `{declares: [name…] (minItems 3), rows: […]}`; CHK-HARNESS-ROWS = rows ⊇ declares ∧ every row's exit-code map carries gate-tool exit-2 and exit-3 entries |
| Exit-code scope (F1) | `contract-lint` = exactly {0, 1, 2}. `gate-wrap`: **mapped exits are InvocationDescriptor data** (Copilot's any-non-zero-is-deny lives in its row); the wrapper's *own* usage/internal failure = exit 1 |
| Fixture constants | rework `max: 3` (kata K=3 precedent); named threshold `crap_composite ≤ 6` + the invalid `crap_relaxed` case; gate-runner principal `sdd-roles-gate-runner` |

## 5. Work packages and dependency order

| WP | Content | Depends |
|---|---|---|
| **WP0** | Scaffold §2 tree; `pyproject.toml` (py≥3.11, jsonschema pin); `VERSION` = 1.0.0; CLI skeletons with exit-code contract (usage → 1); empty registry + selftest skeleton that already fails on registry↔corpus mismatch | — |
| **WP1** | The 8 closed schemas + one valid corpus case per type (incl. green ablation arm, full protected-minimum KernelConfig) + committed 3-row descriptor instance; selftest drift checks: VERSION ↔ per-schema `const` ↔ corpus `schema_version` | WP0 |
| **WP2** | Provenance cluster: CHK-SCHEMA, CHK-PROV-PRESENT, CHK-FENCE, CHK-TAINT, CHK-TOOLBIND + `loader.py` artifact model + `report.py` + their invalid families (incl. the named `verdict: "pass"` GateOutcome and `arms:` Role cases) | WP1 |
| **WP3** | Static config/registry cluster: CHK-EVIDENCE, CHK-DECISIONS(v1), CHK-ARM (fail + green-ablation pair), CHK-THRESH(v1) (`crap_relaxed`), CHK-PROTECT, CHK-MAP, CHK-HARNESS-ROWS, CHK-DEBUG; build `runs/cold-start/` fixture and implement CHK-REFS against it | WP2 |
| **WP4** | `gate-wrap`: descriptor-driven translation + decision-output emission; corpus case per mapping row × 3 harness rows, incl. gate-tool exits 2 and 3; wrapper usage-error case | WP1 (∥ WP2/WP3) |
| **WP5** | Self-integrity: DEFERRED stubs for the 7 item-2 checks (+ the 2 dual-phase item-2 sub-rows) + their committed corpus families; CHK-DEFER, CHK-DET (double-run), CHK-NET (socket guard), CHK-NEUTRAL (grep), CHK-SELF (temp-copy + report-naming); `errors/` exit-1 family | WP2–WP4 |
| **WP6** | Kernel docs (ledger chain + `tree_digest`, provenance guide, C3 conformance-port rule, corpus guide); **clean-clone offline acceptance run** executing the spec's WHERE clause end-to-end; record ADR 0001 Accepted + log entry | WP5 |

Corpus arithmetic at completion: 8+ valid cases, 26 invalid families (CHK-ARM ships a fail+pass pair; dual-phase rows ship both sub-phase cases), ≥1 case per exit code {0,1,2}, one case per gate-wrap mapping row. WP6 is the acceptance criterion executed literally.

## 6. Constitution alignment & risks

Alignment: every technology pick carries its spec envelope (trade-offs surfaced, no silent decisions); check modules are single-responsibility keyed by CHK id; the registry gives open/closed extension (a new check = registry row + corpus family, no dispatch edits); dependency inversion is load-bearing, not decorative — checks consume the loaded artifact model, never paths, which is precisely what makes CHK-SELF's path-independence hold; C3 inverts implementation privilege (language-neutral corpus is the contract; the Python implementation is a replaceable adapter behind a conformance gate — the no-fork precedent generalized).

Top risks: (1) **closed-schema × `$ref` composition** — `additionalProperties: false` does not see across `allOf`/`$ref` boundaries in 2020-12; mitigated structurally (flat closed objects, per-file `$defs`, no cross-closed-object composition) and the corpus's extra-field cases would catch a leak; (2) **byte-determinism across OS/Python versions** — canonical JSON rules pinned in §4, CHK-DET is the tripwire; (3) **CHK-NEUTRAL grep precision** — scope and token list pinned in §4 and versioned in the registry, false positives fixable by neutral rewording, never by exclusion creep; (4) **item-2 scope creep** — only CHK-REFS may touch the run fixture in v1; the DEFERRED stub list is closed at seven (+ the two dual-phase sub-rows); (5) **dual-phase under-coverage** — the corpus arithmetic in §5 counts sub-phase cases explicitly, and CHK-DEFER fails selftest if a stub reads green.

## 7. Gate

**CLOSED — PLAN-OK recorded 2026-08-07; F1–F4 ratified as drafted.** ADR 0001 flipped to Accepted the same day. `sdd-roles-kernel.tasks.md` drafted + Stage-4 analyze run same day. **sdd-implement ran 2026-08-07: all 44 tasks landed — `contract-lint selftest` green (12/12 sections, byte-identical across runs) and the offline clean-copy acceptance run PASS** (tasks file header carries the build record). The ratified readings, for the record:

- **F1 — exit-code scope:** C3's {0,1,2} binds `contract-lint` fully; `gate-wrap`'s mapped exits are descriptor data (its own usage/internal errors = 1). This is the spec's own happy-path reading made explicit.
- **F2 — CHK-PROTECT mechanism:** required-named-keys object instead of the spec's parenthetical `contains` constraints — identical invariant (a KernelConfig cannot omit a mandatory member and validate), schema-enforceable without hardcoding workspace paths.
- **F3 — harness declaration home:** `declares[]` lives in the InvocationDescriptor set document, keeping every harness token inside ID instances (CHK-NEUTRAL stays a clean grep; the three-harness floor is a neutral `minItems: 3`).
- **F4 — `schema_version` = 1.0.0** at first commit with documented SemVer discipline.
