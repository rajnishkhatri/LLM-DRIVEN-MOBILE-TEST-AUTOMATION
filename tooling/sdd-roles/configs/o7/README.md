# o7 productive KernelConfig

The committed, run-facing KernelConfig for o7 conveyor runs — the config that
un-bricks the arms after
[ADR 0005](../../../../docs/architecture/adrs/tooling/sdd-roles/0005-ir-gate-first-class-gate-vocabulary.md):
it binds all five gate ids the catalog roles declare, including the frozen
`ir-gate` → `ir-gate-checker` row (threshold `ir_gate_violations_max: 0`,
tool in the allowlist, CHK-IRGATE-PIN-clean by construction). The sibling
`speckit-mapping.json` is required by the runner's serialize step and travels
with the config (the runner copies both into every run dir at genesis — runs
stay self-contained).

**Arm:** `B` (specifier → maker3 → checker3) — the ownership guide's
"fastest honest adoption" pick. For the full line (closest to o7's
philosophy), change the one field to `"arm": "C"`; every gate row already
covers arms A, B, C, and C-dbg (their gate unions are identical).

## Invocation

```
.venv/bin/gate-runner run \
  --kernel kernel \
  --workspace <o7-workspace> \
  --run-dir <run-dir> \
  --config configs/o7/kernel-config.json \
  --registry kernel/catalog/role-registry.json \
  --descriptors kernel/descriptors/invocation-descriptors.json \
  --harness <harness-row> \
  --run-id <id> \
  --bind python=<python3 path> \
  --bind sdd_roles_root=<absolute path to tooling/sdd-roles> \
  --bind javac_build=<path> \
  --bind junit_runner=<path> \
  --bind crap4java=<path> \
  --bind mutate4java=<path> \
  --bind args="<stage task text>" \
  --bind agents_file='<inline agents JSON (claude-code row)>'
```

Machine values arrive only as `--bind` pairs so this committed config stays
byte-portable (the runner's own rule). Token map:

| Token | Meaning | Status |
|---|---|---|
| `{python}` | Python 3 for the ir-gate-checker | available |
| `{sdd_roles_root}` | absolute path of `tooling/sdd-roles` | available |
| `{javac_build}` `{junit_runner}` `{crap4java}` `{mutate4java}` | the four Java gate-tool executables | **built 2026-08-09** — `tools/<tool-id>/<tool_id>.py` (executable; bind the absolute path) |
| `{args}` | the stage task text delivered to every live role (ADR 0006 runner-contract channel) | **required bind for live runs** — omitting it fails at fill time |
| `{agents_file}` | agent definition for the claude-code row | live runs on CLI 2.1.185: bind an inline JSON object (e.g. derived from the projection card), not a file path (ADR 0006 binding note) |

Runner-supplied tokens (never bound): `{workspace}` `{run_dir}` `{report}`
`{role}` `{stage}` `{attempt}` `{next_role}` (validator ≥ 0.7.1 — the arm
successor; the final stage points to the arm's entry stage).

Every gate tool must write a JSON report at `{report}` carrying a non-empty
`tool_version` (the runner refuses reportless or versionless outcomes) and
exit 0 green / non-zero red. `ir-gate-checker` already meets this contract
(exit 0/2/3; see `tools/ir-gate-checker/README.md`); the four Java tools must
meet it when they land.

## Workspace layout this config assumes

| Path | What |
|---|---|
| `ir/testcase-ir.json` | the committed, sealed `TestCaseIR` (the ir-gate row's `--ir`) |
| `ir/locator-manifest.json` | the committed `LocatorCandidate` manifest |
| `src/**`, `tests/**`, `src/test/**` | module source + suites (tests globs are protected) |
| `.sdd-roles/` | pinned config/registry copies, gate configs, ledger dir (protected set) |
| `.specify/memory/constitution.md` | the protected speckit constitution |
| `.specify/`, `specs/` | speckit roots — handoffs/ledgers/debug reports serialize here per `speckit-mapping.json` |

## What still blocks a full productive run

Preflight passes with this config (verified — see the probe results recorded
with ADR 0005's build notes). 2026-08-09 update: the four Java gate tools
are built (all five gate rows executable — Appendix C probes 8/8 in the
next-items plan), and the live invocation channel is closed by ADR 0006
(run-dir + task + successor + draft obligation ride the command template).
Remaining live blockers are harness availability only: copilot and cursor
CLIs are absent (R-COPILOT-LIVE / R-CURSOR-LEG). The claude-code leg runs.
