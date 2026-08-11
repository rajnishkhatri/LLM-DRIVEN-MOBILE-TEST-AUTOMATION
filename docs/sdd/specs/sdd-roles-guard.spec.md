# Spec: SDD Roles Write Guard — D7 floor: live write-blocking + hook mounting (Track A, build item 3)

**Status:** SIGNED OFF v1 (SPEC-OK, owner, 2026-08-07 — combined gate with PLAN-OK; clarify C1–C4 LOCKED same day) · **IMPLEMENTED 2026-08-07** — gate record: `contract-lint selftest` exit 0, 16/16 sections byte-identical across double runs, zero DEFERRED, 12 flipped item-2 cases held, 23 guard decision cases, 4 mount goldens; `acceptance.sh` PASS on a clean offline copy (schema 1.2.0, validator 0.3.0); tamper-verified (doctored mount byte / decision expectation / hooked-golden digest char each flip exactly their section red); `runner.py`/`gate_wrap.py` byte-identical to item-2 close (S7 held). Honest notes in the tasks header.
**Home:** `tooling/sdd-roles/` (item-1 C1). **Process:** sdd-spec.
**Evidence:**
- `docs/research/role-agent-skills-external-research.md` — memo §3-D7 (floor tier: repo-scoped FS + block patches touching test folders + between-run gate re-verification; TDFlow mitigations), §4.8 (per-role write scopes as declarative kernel data; the shim is *generated from* the contract), §7 build order item 3, §7a owner lock "D7 tier: floor only".
- TDFlow (arXiv 2510.23761, Appendix C) — the tamper rubric source, fetched 2026-08-07: **12 categories** (the memo's "11-category" citation is corrected forward here, per C4; the memo is not rewritten), verbatim definitions on file in `kernel/docs/tamper-rubric.md` (this item authors it). Mitigation set verbatim: patch isolation, test protection, filesystem scoping, repeated prompting; 7 hacking instances / 800 audited runs (~0.9%), all counted as failures.
- `docs/sdd/specs/sdd-roles-kernel.spec.md` — item-1 rows this item executes: S1 ("the wrapper is *exercised* under hook mounting only at item 3"), S5 (shim generated from contract), S8 ("runtime enforcement at item 3"), out-of-scope ("live write-blocking and hook wiring (item 3)").
- `docs/sdd/specs/sdd-roles-orchestrator.spec.md` — item-2 rows this item builds on: S3 (runtime enforcement of other ledger writers routed here), S7 ("recording, not blocking (item 3 blocks)").
- ADR 0001 (corpus-as-contract), ADR 0002 (golden-run conformance) — both Accepted; this item extends ADR 0002 to guard decisions and hook mounting (C1).

## Scope decisions locked (derived from prior artifacts)

| id | decision |
|---|---|
| S1 | **This spec covers only build item 3**: (a) the `write-guard` CLI (4th console script; subcommands `decide` and `mount`); (b) additive hook-mounting fields on `InvocationDescriptor` rows, `schema_version` → **1.2.0** via the committed restamp (C2); (c) the corpus deltas: a guard **decision corpus** (`kernel/corpus/guard/`), **mount goldens**, and two new stub-harness golden run sets (hooked-block + unhooked negative control); (d) `kernel/docs/tamper-rubric.md` (C4) with per-category coverage mapping; (e) selftest/acceptance extensions gating all of it. The table-driven emitter stays item 4 (mount artifacts here are *harness config payloads generated from descriptor data*, not role/skill projections); role bodies item 5; the kata item 6; the D7 **strong tier is declined** (§7a owner lock — managed-settings/policy.d wiring is out of scope permanently for this track unless the owner reopens it). |
| S2 | **Harness particulars stay data — including hook protocols.** Guard source contains no harness token (CHK-NEUTRAL scope extends over the new module unchanged) and no harness-shaped parsing branch. Per-harness hook facts live in the descriptor row's new `hooks` object (C2): event names, mount path, command template, and a **JSON-pointer-driven request extraction table** (which pointers in the harness's hook payload yield the candidate paths and operation). The guard evaluates requests already normalized through that data; the neutral request shape is `{role, operation: create|modify|delete, paths[]}`. |
| S3 | **Fail-closed split (F-reading candidate).** Claude-style hooks treat exit 1 as *non-blocking* error — so a guard that exits 1 on evaluation failure silently allows the write through. Therefore: argv-level misuse (missing/unknown flags, unreadable descriptor file for `mount`) exits **1** (usage — a mount defect, prevented by golden-verified mount artifacts); every failure *while evaluating a request* (malformed request JSON, unknown role, unreadable/invalid config or registry, unresolvable path) exits **2 = block, reason `FAIL_CLOSED`**. A mounted guard never allows by accident. |
| S4 | **The decision procedure is normative data, evaluated in fixed order** (table below). Any path in the request that blocks ⇒ the whole request blocks with the first blocking path + reason code. Add-vs-modify is decided by **target existence on disk at decision time** (the live analogue of the retro-lint's history resolution). The guard is **clock-free**: identical request + config + registry + workspace state ⇒ identical bytes, no `--clock` needed. |
| S5 | **One rule source, two enforcement times.** The scope/protected/tests matching semantics are extracted into a shared module (`scopes.py`) consumed by BOTH `checks/run_directory.chk_scope` (retro) and the guard (live) — the mechanical rule cannot drift between them. Mirror claim (one-directional, honest): **guard-allow ⇒ retro-pass** for the write it allowed; the retro-lint + between-run gate re-verification (item 2) remain the backstop for channels hooks never see. The guard adds two live-only rules with no retro analogue (rationale in-table): repo-scope escapes and `.git/` writes — both invisible to the between-run scan (it excludes `.git/` and never sees outside-workspace paths), so live blocking is their *only* coverage. |
| S6 | **Stateless guard (C3).** The guard writes nothing, ever: decision + machine reason code on stdout (`allow` / `block <CODE> <path>`), human detail on stderr (harnesses feed stderr back to the agent on block). Ledgered truth stays exclusively with the between-run scan. Tamper-block event counts for the kata come from harness transcripts at item 6. No guard-writable channel exists for a role to spoof. |
| S7 | **Mounting is generation + protection, not runner behavior.** `write-guard mount --descriptors <file> --harness <h> ...` renders the row's `hooks` fields into the harness hook-config artifact (one hook rule per registry role, `--role` baked per rule; command template wraps the guard in `gate-wrap` so descriptor exit maps govern translation — the item-1 "exercised under hook mounting" clause executed). Mount output lands under a `harness_enablement`-protected path: a role attempting to edit or remove the mounted config is **live-blocked (`PROTECTED`)** and retro-caught — the anti-unhook rule. `gate-runner` itself changes **zero lines**: the unhooked negative control (FP11) proves the item-2 loop already catches what live blocking prevents. |
| S8 | **The gate is ADR 0002 extended — no new CHK ids (C1).** The 26-id CHK table stays the frozen validation enumeration. Guard behavior is gated by: the decision corpus (every case reproduces expected decision/exit/reason byte-identically), mount goldens (byte-compared per harness row), the two new golden run sets (byte-identical ×2 under the pinned clock, `contract-lint` green), and the 1.2.0 restamp (idempotent; expected verdicts preserved). All offline, all in `selftest`; `acceptance.sh` extended; validator `0.3.0`. |

## Clarify — C1–C4 (LOCKED 2026-08-07, owner — each locked as recommended)

| id | question | decision |
|---|---|---|
| C1 | Does the CHK table grow (e.g. CHK-GUARD/CHK-MOUNT), or does golden-decision conformance cover guard behavior? | **Golden-decision conformance, no new CHK ids.** Decision-table corpus + mount goldens + extended golden runs, gated in selftest byte-identically. The CHK table stays item 1's single enumeration of *validation* checks; guard decisions are *behavior*, exactly the class ADR 0002 was accepted for. Rejected: CHK amendment (every port would owe two more live checks for what goldens already pin). |
| C2 | Where do per-harness hook-mounting facts live? | **Extend descriptor rows, additive `schema_version` 1.2.0.** Memo §4.11 makes the InvocationDescriptor row THE per-harness fact table; rows gain an optional closed `hooks` object; whole-corpus restamp via committed `regen_corpus.py` (item-2 machinery, second exercise). Rejected: standalone hook-mount file (second per-harness table for item 4 to join and drift); no-schema generated artifacts (hook facts become code-embedded, violating CHK-NEUTRAL's spirit). |
| C3 | Guard audit trail at floor? | **Stateless.** stdout/stderr only; anything the role's process may write, the role can also fabricate or truncate — a guard audit file would be an advisory record at best and a spoof channel at worst. TDFlow's floor blocks silently and audits between runs; ours does too. Rejected: workspace scratch audit file. |
| C4 | The TDFlow source enumerates **12** rubric categories; the memo said 11. | **Adopt the verbatim 12-category rubric** as `kernel/docs/tamper-rubric.md` (source-cited), each category mapped to its coverage tier: `guard-blocked` / `retro-lint` / `gate-reverify` / `residual-manual`. The 11→12 correction is recorded forward here; the memo is not rewritten (house rule). The kata's any-tamper-fails rule reads its checklist from this doc. Rejected: kernel-native rubric (loses the 800-audited-runs provenance). |

## Problem

Items 1–2 made tampering *visible after the fact*: CHK-SCOPE/CHK-PROTECT fail the run record, and the gate-runner re-verifies between invocations. Nothing yet *prevents* a Bash-capable role from writing `tests/` or the gate configs mid-invocation — the exact behavior measured in the wild (EvilGenie: both Codex and Claude Code edited tests to pass). TDFlow's floor mitigations cut hacking to ~0.9% over 800 audited runs, and every ingredient is already declarative kernel data (protected set, write scopes, role tags, descriptor rows). Item 3 generates the live enforcement from that data — the memo's "shim generated from the contract" — and proves the whole chain offline: mount → hook fires → gate-wrap translates → guard blocks → between-run gate still green.

## Target artifact

| artifact | change |
|---|---|
| `validator/src/sdd_roles_validator/guard.py` | NEW — `write-guard` CLI: `decide` (neutral request in, decision out, exits {0,1,2} per S3/S4) and `mount` (descriptor `hooks` fields → harness hook-config artifact). |
| `validator/src/sdd_roles_validator/scopes.py` | NEW — shared rule module (S5): `_match_any`, hard-protected assembly, the tests diff-aware rule, scope matching. `checks/run_directory.py` refactored to import it (behavior byte-identical — existing corpus is the proof). |
| `kernel/schemas/invocation-descriptor.schema.json` | Additive optional `hooks` closed object on rows (events, mount_path, command_template, request extraction pointers). 1.2.0. |
| `kernel/descriptors/invocation-descriptors.json` | The three real-harness rows gain `hooks` data. |
| `kernel/corpus/guard/` | NEW decision corpus: per-case `{kernel-config, role-registry, workspace fixture, request.json, expect.json}`. |
| `kernel/corpus/orchestrator/` | Stub descriptor row gains `hooks`; new scenarios `hooked/` + `unhooked/`; stubs learn "guarded write" actions (consult mounted hook command before writing; honor block). |
| `kernel/corpus/runs/orchestrator-hooked/`, `-unhooked/` | NEW golden run sets (S7, FP11/HP4). |
| `kernel/docs/tamper-rubric.md` | NEW — verbatim 12 categories + coverage map (C4). |
| `kernel/docs/conformance.md` | Port admission gains #8: guard ports reproduce the decision corpus + mount goldens. |
| Whole corpus | `schema_version` 1.2.0 restamp via `regen_corpus.py` (validity-preserving, idempotent). |
| `selftest.py`, `acceptance.sh`, `pyproject.toml`, READMEs | New sections (guard-decisions, guard-mount, extended golden sets), arithmetic, `write-guard` console script, `0.3.0`. |

### Guard decision procedure (normative — fixed evaluation order per path)

| # | rule | outcome | reason code | retro analogue |
|---|---|---|---|---|
| 1 | Path fails to resolve inside the workspace root (absolute outside, `..` escape, or a symlinked ancestor resolving outside) | block | `REPO_SCOPE` | none — live-only (scan never sees outside paths) |
| 2 | Path under `.git/` | block | `VCS_INTERNAL` | none — live-only (scan excludes `.git/`) |
| 3 | Path under the run directory or any `protected.ledger_dir` path | block | `WRITER_ONLY` | CHK-WRITER / CHK-TREE domain |
| 4 | Path matches any hard-protected key (`kernel_config`, `role_registry`, `gate_configs`, `harness_enablement`, `speckit_constitution`) | block | `PROTECTED` | CHK-SCOPE "write inside the protected set" |
| 5 | Path matches `tests_globs` AND operation is `create` AND target absent on disk | *exempt from rule 7's scope arm; continue* | — | "added under tests passes" |
| 6 | Path matches `tests_globs` AND (operation `modify`/`delete` OR target exists) AND role tag is `maker` | block | `TESTS_PROTECTED` | CHK-SCOPE maker rule |
| 7 | Path matches no role `write_scopes` pattern (and rule 5 did not exempt it) | block | `SCOPE` | CHK-SCOPE scope arm |
| 8 | Otherwise | allow | — | — |

Matching semantics are `scopes.py`'s (exact / `dir/` prefix / fnmatch) — the same function the retro-lint calls. A `create` whose target already exists on disk is treated as `modify` (rule 6) — the disk is the live analogue of recorded history.

## Acceptance criteria (EARS)

### Failure paths first

- **FP1** IF a request path escapes the workspace root (absolute, `..`, or symlinked-ancestor escape), THEN `decide` MUST exit 2 with `block REPO_SCOPE <path>` on stdout.
- **FP2** IF a request path lies under `.git/`, THEN `decide` MUST block `VCS_INTERNAL`.
- **FP3** IF a request path lies under the run directory or a `ledger_dir` path, THEN `decide` MUST block `WRITER_ONLY`.
- **FP4** IF a request path matches any hard-protected key's patterns, THEN `decide` MUST block `PROTECTED` — including paths under `harness_enablement` (the anti-unhook rule, S7).
- **FP5** IF a `maker`-tagged role's request would modify or delete an existing file matching `tests_globs`, THEN `decide` MUST block `TESTS_PROTECTED`; WHERE the operation claims `create` but the target exists on disk, the same rule applies.
- **FP6** IF a request path matches no pattern in the role's `write_scopes` and is not a tests-add, THEN `decide` MUST block `SCOPE`.
- **FP7** IF any path in a multi-path request blocks, THEN the whole request MUST block, reporting the **first** blocking path and code in evaluation order.
- **FP8** IF the request is malformed JSON, names a role absent from the registry, or the config/registry cannot be read or fail schema validation, THEN `decide` MUST exit 2 with `block FAIL_CLOSED` — never exit 1, never allow (S3).
- **FP9** IF `decide` or `mount` argv is missing required flags or names an unknown flag, THEN exit MUST be 1 with usage on stderr and **no decision line on stdout**.
- **FP10** IF `mount` targets a harness whose descriptor row lacks the `hooks` object, THEN exit MUST be 1 (usage) and nothing written.
- **FP11** IF the `unhooked` stub scenario runs (no mount performed) and its role writes into `tests_globs`, THEN the write MUST land, and `gate-runner`'s between-run validation MUST fail the run (exit 2, `failed` entry recorded, CHK-SCOPE finding) — the item-2 backstop proven against the exact write the hook would have blocked, with **zero `gate-runner` line changes** (S7).
- **FP12** IF any golden byte differs (decision corpus expect, mount artifact, either new run set), THEN `selftest` MUST exit 2 naming the failing section.

### Happy path

- **HP1** WHEN any role requests `create` of a non-existing file matching `tests_globs` whose path is otherwise unprotected, THEN `decide` MUST allow (exit 0, stdout `allow`) even if `tests_globs` is absent from its `write_scopes`.
- **HP2** WHEN a role requests a write inside its `write_scopes` touching no protected pattern, THEN `decide` MUST allow; WHERE the request is identical and the workspace unchanged, output MUST be byte-identical across runs with no clock input (S4).
- **HP3** WHEN `mount` runs for each descriptor row carrying `hooks` (the three real harnesses + the stub row), THEN the rendered artifacts MUST byte-match the committed mount goldens, one hook rule per registry role, each command wrapped in `gate-wrap --harness <row>` (S7).
- **HP4** WHEN the `hooked` golden scenario runs, THEN the stub role's protected-write attempt MUST be blocked live (guard exit translated through `gate-wrap` per the stub row's exit map), the role MUST proceed per scenario, the run MUST complete green (`contract-lint` exit 0), the ledger MUST contain **no trace of the blocked write** (S6 stateless), and the run directory MUST be byte-identical across two executions under the pinned clock.
- **HP5** WHEN `selftest` executes the decision corpus, THEN every case MUST reproduce its expected decision, exit code, and reason code, and the section MUST be deterministic across double runs.
- **HP6** WHEN the 1.2.0 restamp runs over the committed corpus, THEN it MUST be validity-preserving (every expected verdict unchanged), idempotent (second run rewrites zero files), and MUST never write an `expect.json`.
- **HP7** WHEN `selftest` completes, THEN section count and arithmetic MUST cover the new sections with `deferred_entries == 0` still asserted, and `acceptance.sh` MUST pass on a clean offline copy.
- **HP8** WHEN a harness hook payload arrives via the descriptor row's extraction pointers (stub row exercises this shape), THEN the guard MUST derive `{paths, operation}` purely from that data — no harness-shaped branch in source (S2; CHK-NEUTRAL green over `guard.py`/`scopes.py`).

## Out of scope (later build items, for the avoidance of drift)

The D7 **strong tier** (managed-settings force-enabled plugin, root-owned `policy.d`) — declined by the §7a owner lock; per-harness role/skill **projections and packaging** (item 4 — the emitter will *copy* mount artifacts into projections, consuming the same descriptor data); role bodies (item 5); the kata and its tamper-block metrics from harness transcripts (item 6); **semantic** test-weakening detection (rubric categories 9–12 are mechanically undetectable at any tier — their coverage rows say `gate-reverify`/`residual-manual`, backstopped by the D4 mutation/CRAP gates and the kata's any-tamper-fails rule); provenance `derived_from` under-declaration auditing (item-1 S7 routed it to "D7/audit" — the rubric doc records it as `residual-manual`; no mechanical check is claimed).
