# sdd-roles validator — contract-lint + gate-wrap + gate-runner + write-guard + role-emit + kata (reference implementation)

Python ≥ 3.11, single dependency (`jsonschema >=4.21,<5`). The golden corpus
under `../kernel/corpus/` is the normative contract (see
`../kernel/docs/conformance.md`); this package is the conformance-gated
reference implementation, not the contract itself. Since build item 2 the
corpus also carries **golden runs** — committed `gate-runner` output the
implementation must reproduce byte-identically (ADR 0002).

## Install

```bash
python3 -m venv --system-site-packages .venv   # or a plain venv + jsonschema wheel
.venv/bin/pip install -e validator/ --no-deps --no-build-isolation
```

Offline installs: pre-fetch a `jsonschema` wheel (and its deps) into a
wheelhouse and `pip install --no-index --find-links <wheelhouse> jsonschema`,
or reuse a system-site interpreter that already has it. Nothing here touches
the network at runtime — CHK-NET enforces that with a socket-denying guard.

## Commands and exit codes (spec C3, plan F1 — both items)

| Command | 0 | 1 | 2 |
|---|---|---|---|
| `contract-lint validate <target> [--kernel DIR]` | all 26 live checks pass | usage/internal error (no report) | ≥1 check failed |
| `contract-lint selftest [--kernel DIR]` | corpus + golden runs behave exactly as annotated | usage/internal error | any self-test section failed |
| `gate-wrap --descriptors F --harness H -- <tool …>` | / mapped exits come from the descriptor row / | its own usage/internal errors | (mapped) |
| `gate-runner run\|resume …` | run complete, all gates green, final validation green | usage/internal error (nothing written) | run failed: gate red at the rework bound, validation red, or resume refusal — the ledger still validates green |
| `write-guard decide` (request on stdin) | write allowed (`allow`) | argv misuse only (no decision line) | write blocked (`block <CODE> <path>`) — **including every evaluation failure** (`FAIL_CLOSED`): a mounted guard never allows by accident |
| `write-guard mount --descriptors F --harness H --registry R --out DIR` | hook-config artifact rendered at the row's `mount_path` | usage error (unknown harness, row without `hooks`, unreadable inputs) | — |

`validate` prints one machine-readable JSON report: canonical bytes (sorted
keys + entries, LF, ASCII, no timestamps, target-relative labels) — two runs
on identical input are byte-identical, and the report is digestable as a
`report_ref`. Every one of the 26 CHK ids appears in every report with **no
DEFERRED rows** — the run-directory suite (CHK-CHAIN/TREE/WRITER/GENESIS/
GATE-BIND/SCOPE/REWORK + the item-2 halves of CHK-DECISIONS/CHK-THRESH) is
live; CHK-DEFER now fails any report that still carries a DEFERRED row for an
implemented check.

`selftest` is the build-item gate: registry↔corpus bijection, schema
drift/closedness, the full corpus sweep against every `expect.json`
(DEFERRED-era cases resolved through `expected_when_implemented`), double-run
determinism, the socket canary, the harness-token scan, temp-copy verdict
stability, DEFER auditing (both directions), the errors/ exit-1 family, the
gate-wrap mapping corpus, the **orchestrator golden runs** (executed twice,
byte-compared against the committed goldens, each validating green — the
`orchestrator-unhooked` negative control validating red on exactly
CHK-SCOPE), **resume + tamper-refusal** over the interrupted fixture, the
**guard decision corpus** (23 cases, double-run byte-identity, fail-closed
assertions, runtime-built symlink escape), and the **mount goldens**
(re-rendered twice per harness row, byte-compared).

## write-guard (build item 3 — the D7 floor)

The live enforcement shim, generated from the contract: `decide` evaluates
one write request through the 8-rule procedure (spec `sdd-roles-guard`
normative table) using the SAME rule module (`scopes.py`) the retro-lint's
CHK-SCOPE uses — one rule source, two enforcement times. Reason codes
(contract, plan F3): `REPO_SCOPE`, `VCS_INTERNAL`, `WRITER_ONLY`,
`PROTECTED`, `TESTS_PROTECTED`, `SCOPE`, `FAIL_CLOSED`. `mount` renders a
descriptor row's `hooks` object into the harness hook-config artifact, one
rule per registry role, wrapped in `gate-wrap` so descriptor exit maps govern
translation; only `{role}` is bound at mount time (artifacts stay
byte-portable). The stateless guard writes nothing — ledgered truth stays
with the between-run scan, and the mounted config itself sits under
`harness_enablement` protection (the anti-unhook rule).

## role-emit (build item 4 — the D6 table-driven emitter)

The projection emitter (ADR 0003: catalog-as-source): `project` renders the
canonical catalog (role registry + optional `--bodies` doctrine files)
through one descriptor row's `projection` target table into that harness's
layout — agent/skill cards from typed data, a kernel-skill card, an optional
manifest, and `mount-copy` targets that byte-copy the shared `render_mount`
output (`mounts.py`, the same function `write-guard mount` calls). Every
rendered file carries a clock-free stamp (`sdd-roles <schema_version>
catalog:<digest12>`); `mount-copy` files carry none (byte-identity wins).
Rendering is all-or-nothing: cap overflow, unresolved tokens, or unknown
body stems exit 2 with nothing written. `verify` re-renders and
byte-compares an emitted tree (drift/missing/extra → exit 2, deterministic
listing) — the CI drift command for committed projections.

```bash
role-emit project --kernel KERNEL --descriptors invocation-descriptors.json \
  --harness NAME --registry role-registry.json [--bodies DIR] --out DIR
role-emit verify  …same flags; --out is the tree to check…
```

Since build item 5 the **real catalog** ships at `kernel/catalog/` (9-role /
4-arm registry + nine cited doctrine bodies, kata arms A/B/C/C-dbg); its
renders through the three real harness rows are committed at
`kernel/corpus/catalog-projections/` and gated by the `catalog` selftest
section (bijection, layout markers, neutral scan, goldens ×2, verify green).
Provisioning a workspace for a harness is `role-emit project` over that
catalog — the deployment ADR 0003 promised.

## kata (build item 6 — the deterministic study instrument, ADR 0004)

The kata rig runs the §6 pre-registered A/B/C role-count experiment as three
pure, clock-free subcommands:

```bash
kata plan    --kernel KERNEL --registry role-registry.json \
  --prereg kata-preregistration.json --workload kata-workload.json \
  --reps 5 [--default-model UNBOUND] --out kata-plan.json
kata analyze --kernel KERNEL --plan kata-plan.json \
  --prereg kata-preregistration.json --results kata-results.json \
  --out kata-verdict.json
kata report  --kernel KERNEL --verdict kata-verdict.json --out scorecard.md
```

`plan` expands arms × instances × reps into a byte-stable `kata_plan` (240
cells: 4 arms × 12 instances × 5 reps), resolving each role's model at plan
time. `analyze` computes the pre-registered verdict — Wilson 95% intervals and
the criteria/kill-rule in exact integer arithmetic (scale 10000, z²=9604/2500,
`math.isqrt` + a ceil-sqrt correction, both bounds widened) — and is fail-closed
(exit 2, nothing written) on any stamp/digest/bijection/provenance/self-
consistency violation. `report` is a pure re-projection of the verdict, never
recomputing. The criteria are frozen in code and pinned by a **digest triangle**
(`PREREG_DIGEST` ↔ `kernel/catalog/kata-preregistration.json` ↔ every
`kata_results.prereg_digest`), so a post-hoc threshold edit reds the gate — the
anti-p-hacking core. Exit codes: 0 success; 1 argv/not-found/not-JSON; 2
schema/digest/stamp/bijection/provenance/self-consistency failure. The actual
LLM run that produces a real `kata_results` is the deferred seam
(`kernel/docs/kata-seam.md`); the rig itself is fully gated by the `kata`
selftest section.

## gate-runner

```bash
gate-runner run --kernel KERNEL --workspace WS --run-dir RD \
  --config kernel-config.json --registry role-registry.json \
  --descriptors invocation-descriptors.json --harness NAME \
  --run-id ID [--parent PARENT_RUN_ID] \
  [--clock fixed:<iso8601>|wall] [--bind key=value ...]
gate-runner resume …same flags, no --run-id…
```

The between-run loop per stage: `entered` → headless role invocation (command
template filled from descriptor row + role `invocation` values + `--bind`
pairs) → workspace scan/diff (`writes[]`, `input_tree_digest`) → gates from
`KernelConfig.gates[]` (per-attempt reports; `GateOutcome`s from exit codes
alone) → handoff finalization (role-authored `handoff.draft` + runner-authored
`gate_outcomes` → canonical per-stage `handoff-<run>-<seq>.json`) → spec-kit
serialization of `required_mappings` → `contract-lint` over the run dir →
branch: `passed`, bounded repair (`attempt ≤ rework.max`), or a `rework` jump
(per-edge counters, carried across `--parent`). The run directory is
append-only and self-contained: config, registry, and mapping copies travel
with it, so `resume` re-reads ledger + contracts + workspace and refuses
(exit 2, nothing written) if any live check rejects the existing run.

`--kernel` defaults are not provided for `gate-runner` — every path is
explicit; machine-specific values (interpreter, fixture dirs) enter only via
`--bind`, keeping committed fixtures byte-portable.
