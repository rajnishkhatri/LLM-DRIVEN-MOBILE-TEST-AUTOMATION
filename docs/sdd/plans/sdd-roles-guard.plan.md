# Plan: SDD Roles Write Guard — D7 floor (Track A, build item 3)

**Spec:** `docs/sdd/specs/sdd-roles-guard.spec.md` (SIGNED OFF v1). **Status:** IMPLEMENTED 2026-08-07 — §7 gate CLOSED same day; build record in spec header + tasks header; WP0–WP6 all landed (G01–G28).
**House constraints carried:** offline + deterministic gate; single dependency (`jsonschema`); canonical JSON bytes; corpus-first; selftest is the gate; no new CHK ids (C1).

## 1. Abstractions (G1 table)

| abstraction | decision | rejected alternative |
|---|---|---|
| Rule core | `scopes.py` — pure functions over `(config, registry)`: pattern matching, hard-protected assembly, the tests diff-aware rule. Imported by BOTH `chk_scope` (retro) and `guard.py` (live). Extraction is behavior-preserving: the existing corpus green run is the proof (WP0 lands before any new feature). | Duplicate the rules in guard.py (the exact drift S5 forbids); make chk_scope call the guard CLI (subprocess per write row — absurd cost, and retro needs history semantics, not disk semantics). |
| Guard CLI | One console script `write-guard`, subcommands `decide` / `mount` (mirrors `contract-lint validate`/`selftest` precedent). `decide` reads the neutral request JSON on stdin; workspace/config/registry/run-dir via flags. | Two console scripts (pyproject noise, no isolation gain); folding into `gate-runner` (the guard must be invocable by a *harness hook* with no runner alive). |
| Request extraction | Descriptor `hooks.request` carries JSON-pointer arrays (`paths_pointers[]`, `operation` pointer + value map with a `default`). Guard applies pointers mechanically; the stub row's payload shape differs from a plausible real-harness shape on purpose, proving shape-independence (HP8). | Per-harness parser branches in source (CHK-NEUTRAL violation in spirit and eventually in tokens); requiring harnesses to emit the neutral shape (no harness does). |
| Mount rendering | `hooks.command_template` + `hooks.mount_path` + `hooks.events[]` render to one JSON hook-config artifact per harness: an object keyed by event, each event listing one rule per registry role (`matcher` = role id, `command` = filled template with `--role` baked). Canonical JSON bytes → golden-comparable. | Freeform per-harness template files in the repo (a second projection mechanism pre-empting item 4); rendering inside gate-runner (mounting is setup-time, not run-time — S7). |
| Blocked-write behavior in stubs | Scenario action `guarded_write`: stub invokes the mounted hook command (read from the mounted config at the descriptor-declared `mount_path` under the workspace), passes its payload on stdin, honors exit (0 → write; nonzero → skip write, record nothing). Counter mechanics unchanged from item 2. | Stubs calling `write-guard` directly (would bypass mount + gate-wrap — the chain under test); simulating the block in the recipe (nothing live would be exercised). |
| Restamp | `regen_corpus.py restamp` gains `--to <version>` (default stays the current target); same validity-preserving pipeline, now 1.1.0 → 1.2.0. Idempotence and never-writes-expect assertions unchanged. | A fresh one-shot script (the committed machinery exists precisely for this). |

## 2. Repo tree delta

```
tooling/sdd-roles/
├── kernel/
│   ├── schemas/invocation-descriptor.schema.json   # + optional hooks object (closed), 1.2.0
│   ├── descriptors/invocation-descriptors.json     # 3 real rows gain hooks data
│   ├── corpus/
│   │   ├── guard/<case-name>/                      # NEW decision corpus (~18 cases)
│   │   │   ├── kernel-config.json / role-registry.json
│   │   │   ├── workspace/…                         # tiny fixture tree (existence drives rules 5/6)
│   │   │   ├── request.json                        # neutral request OR raw payload + pointers case
│   │   │   └── expect.json                         # {exit, stdout, reason_code}
│   │   ├── orchestrator/
│   │   │   ├── descriptors-stub.json               # stub row gains hooks
│   │   │   ├── scenarios/hooked/ + unhooked/       # NEW (config/registry/mapping/scenario/workspace-template)
│   │   │   └── stubs/role_stub.py                  # + guarded_write action
│   │   └── runs/orchestrator-hooked/ + -unhooked/  # NEW golden sets
│   └── docs/tamper-rubric.md                       # NEW (C4, verbatim 12 + coverage map)
├── validator/
│   ├── src/sdd_roles_validator/
│   │   ├── scopes.py                               # NEW shared rule core (WP0)
│   │   ├── guard.py                                # NEW write-guard CLI
│   │   ├── checks/run_directory.py                 # refactored onto scopes.py (byte-identical behavior)
│   │   └── selftest.py                             # + guard-decisions, guard-mount, 2 golden sets
│   ├── scripts/regen_corpus.py                     # restamp --to 1.2.0
│   └── pyproject.toml                              # write-guard entry, 0.3.0
```

## 3. Tech selections

Python 3.12.2 venv (`--system-site-packages`, house note), `jsonschema` sole dependency, JSON Schema 2020-12 closed schemas, canonical JSON bytes (sort_keys/ensure_ascii/LF), `Path.resolve(strict=False)` + ancestor-walk for symlink-escape detection (rule 1 resolves the deepest *existing* ancestor; a path whose resolved ancestor exits the workspace root blocks `REPO_SCOPE`).

## 4. Delegated normative values — F-readings (owner, at the gate)

| id | reading |
|---|---|
| F1 | **Fail-closed split** (spec S3): argv-level misuse → exit 1, no decision line; any request-evaluation failure → exit 2 `block FAIL_CLOSED`. Rationale: Claude-semantics hooks treat exit 1 as non-blocking, so evaluation errors must block; argv errors are mount defects and mounts are golden-verified. |
| F2 | **`hooks` object shape** (closed, all fields required when present): `{events[] (minItems 1), mount_path (workspace-relative, must match a `harness_enablement` pattern — schema `minLength 1`, placement asserted by the mount goldens), command_template (must contain `{role}`, `{config}`, `{registry}`, `{workspace}`, `{descriptors}`, `{harness}` tokens as needed; template-fill reuses the runner's `{token}` regex), request: {paths_pointers[] (minItems 1), operation: {pointer, map, default}}}`. |
| F3 | **Decision-line protocol + reason codes frozen**: stdout exactly one line — `allow\n` or `block <CODE> <path>\n`; codes = {REPO_SCOPE, VCS_INTERNAL, WRITER_ONLY, PROTECTED, TESTS_PROTECTED, SCOPE, FAIL_CLOSED} (spec table order); human detail on stderr only. Codes are contract (decision corpus asserts them byte-for-byte). |
| F4 | **Versions**: `schema_version` 1.2.0 (additive minor per ADR 0001), validator `0.3.0`, restamp via `regen_corpus.py restamp --to 1.2.0` (validity-preserving, idempotent, never writes `expect.json`). |

## 5. Work packages

| wp | content | gate evidence |
|---|---|---|
| WP0 | Extract `scopes.py`; refactor `chk_scope` onto it. **No corpus change.** | selftest green, byte-identical to pre-WP0 report (the refactor is invisible). |
| WP1 | Schema `hooks` object; real descriptor rows + stub row gain data; `restamp --to 1.2.0`; new InvocationDescriptorSet valid-corpus case exercising `hooks`. | selftest green post-restamp; idempotence run rewrites 0 files. |
| WP2 | `guard.py decide` + decision corpus (~18 cases: FP1–FP9 + HP1/HP2/HP8 coverage incl. symlink escape, exists-despite-create, multi-path first-block, pointer-extraction case, FAIL_CLOSED trio) + selftest `guard-decisions` section (double-run byte-identity). | section green; every FP/HP row below maps to ≥1 case. |
| WP3 | `guard.py mount` + mount goldens (claude-code, cursor, copilot, stub rows) + selftest `guard-mount` section (render ×2, byte-compare; FP10 usage case in `corpus/errors/`). | section green. |
| WP4 | Stub `guarded_write` action; `hooked/` + `unhooked/` scenarios; recipes (mount step for hooked only); golden sets committed via `regen_corpus.py goldens`; selftest executes both ×2 (HP4 byte-identity + green; FP11 exit 2 + CHK-SCOPE finding + failed entry). | sections green; `gate-runner` diff = 0 lines (S7 assertion in tasks). |
| WP5 | `tamper-rubric.md` (verbatim 12, coverage column per category, 11→12 correction note); `conformance.md` #8 guard-port admission; README/corpus-guide/ledger-chain touch-ups. | docs exist; CHK-NEUTRAL still green (rubric doc lives in kernel/docs — outside token-scan scope, verify). |
| WP6 | `acceptance.sh` (+ guard sections asserted), arithmetic/summary keys, `0.3.0`, final certification: double selftest byte-identity, clean-copy acceptance, **tamper-verification** (doctor a mount golden byte → guard-mount red; doctor a decision `expect.json` → guard-decisions red; re-allow a blocked case in stub scenario → golden-run red). | FINAL GATE EXIT 0 ×2; three tampers each red in the named section. |

## 6. Risks

| risk | mitigation |
|---|---|
| Symlink-escape detection differs across platforms (macOS `/tmp` symlink, case-insensitivity) | Rule-1 resolution normalizes both root and candidate through `resolve()`; decision corpus includes a symlink case built by the selftest **in a temp dir at run time** (symlinks don't commit portably) — the corpus case carries a `setup` recipe, not a committed symlink. |
| WP0 refactor silently changes retro behavior | WP0 lands alone; gate = byte-identical selftest report before/after (no corpus delta in the same change). |
| Stub hook chain accidentally depends on wall clock or absolute paths | Goldens run under pinned clock + `--bind` machine-value injection (item-2 machinery); mount templates use `{workspace}`-relative paths only. |
| Restamp touches golden run bytes (configs embed `schema_version`) | Same class as item 2's restamp: goldens regenerate via the committed recipe runner after restamp; `regen_corpus.py goldens` re-executes, selftest certifies. |

## 7. Gate — combined SPEC-OK + PLAN-OK (CLOSED 2026-08-07, owner)

SPEC-OK granted on `sdd-roles-guard.spec.md` v1 and PLAN-OK with **F1–F4 ratified as drafted** (fail-closed exit split; closed `hooks` object shape; frozen decision-line protocol + 7 reason codes; schema 1.2.0 / validator 0.3.0 via `restamp --to`). Both via AskUserQuestion, recommended options selected. Implementation authorized G01–G28.
