# Golden corpus authoring guide

Layout (`kernel/corpus/`):

```
valid/<TypeDir>/            one green case per schema type (8 dirs, fixed names:
                            RoleRegistry, HandoffContract, StageLedgerEntry,
                            GateOutcome, DebugReport, InvocationDescriptorSet,
                            SpecKitMapping, KernelConfig)
invalid/<CHK-ID>/<case>/    one family dir per CHK id (26, bijective with the
                            registry — selftest-enforced), ≥1 case each
runs/cold-start/            run-directory fixture: ledger + artifacts resolvable
                            at their recorded sha256, zero conversational state
errors/<case>/case.json     exit-1 usage cases (declarative argv specs)
gatewrap/<case>/invocation.json   one case per descriptor exit-code-map row
```

## Target-directory conventions (loader contract)

- Root-level `*.json` files are **kernel artifacts** (resolved by their
  `artifact_type` field — never by filename); `expect.json` / `invocation.json`
  are case metadata, not artifacts.
- Root-level `*.ndjson` files are stage ledgers, one artifact per line
  (reported as `name.ndjson#L<n>`).
- Files in **subdirectories** (`reports/`, `artifacts/`) are data referenced by
  artifact refs — CHK-REFS resolves them at their recorded sha256, so their
  bytes must not drift.

## expect.json (the annotation contract)

```json
{
  "check_id": "CHK-…",              // omitted on valid cases
  "phase": "v1" | "item-2",
  "expected": "pass" | "fail" | "deferred",
  "exit_code": 0 | 1 | 2,
  "json_pointer": "/…",             // a fail entry must appear at this pointer
  "expected_when_implemented": "pass" | "fail"   // item-2 families only
}
```

`expected: "deferred"` cases were the DEFERRED era's shape (C5). **Since build
item 2 the flip is live**: the selftest resolves `expected: "deferred"` through
`expected_when_implemented` — `fail` cases must exit 2 naming the check,
`pass` cases must exit 0 with zero fail entries under the whole live suite.
The annotations were not re-authored; new run-directory cases are authored
directly as `{phase: "item-2", "expected": "fail" | "pass"}`.

## Self-integrity families (fixture-mode)

CHK-DET / CHK-NET / CHK-NEUTRAL / CHK-SELF / CHK-DEFER cases are consumed by
the selftest's auditors, not by plain validate: a differing report pair, the
socket-guard canary, a token-bearing schema fixture, a report whose fail entry
names no pointer, and a report claiming green on an item-2 check. The corpus
tree itself is excluded from the live CHK-NEUTRAL scan (fixtures and
InvocationDescriptor instances legitimately carry harness tokens);
`kernel/neutral_tokens.json` holds the token list so the scanner source stays
token-free.

## Orchestrator fixtures and golden runs (build item 2, ADR 0002)

```
orchestrator/descriptors-stub.json   3 declared stub harnesses, full rows
orchestrator/goldens.json            the recipe table (scenario, runs, pinned clock)
orchestrator/stubs/                  role_stub.py + gate_stub.py (deterministic,
                                     scenario-table-driven, counter files under
                                     <workspace>/scratch/)
orchestrator/scenarios/<name>/       kernel-config + role-registry + speckit-mapping
                                     (C1 fields live here) + scenario.json + workspace-template/
runs/orchestrator-<name>/            committed golden output: run-dir/ + workspace-after/
                                     (orchestrator-resume: interrupted/ + completed/)
```

The selftest executes every recipe twice (machine values via `--bind` only)
and holds the runner to the goldens byte-for-byte, then validates each golden
run dir under the full live suite. Golden bytes are regenerated **only** by
`validator/scripts/regen_corpus.py goldens` — a behavioral change shows up as
a golden diff in review, never as a silent drift. Recipes may carry a
`mount` harness (a `write-guard mount` into the workspace precedes the run)
and a `red_check` id — a **negative-control set** whose committed run dir is
expected to validate red on exactly that check (`orchestrator-unhooked`).

## Guard fixtures (build item 3, D7 floor)

```
guard/common/                 kernel-config + role-registry + workspace/ shared
                              by the decision cases
guard/decisions/<case>/       case.json (role, stdin, argv_extra tokens,
                              optional setup) + request.json + expect.json
                              ({exit_code, stdout} — the decision line is
                              contract, plan F3)
guard/mounts/<harness>/       committed mount goldens (byte-portable: only
                              {role} is bound at mount time)
```

The `symlink-escape` setup is built by the selftest in a temp workspace at
run time — symlinks are never committed. Decision cases run twice and must
be byte-identical (the guard is clock-free). The `hooked`/`unhooked`
scenario pair holds the whole chain: mount → stub role consults the hook →
`gate-wrap` translates → `write-guard` blocks → the ledger shows no trace
(stateless guard, spec S6) — versus no mount → the rogue write lands → the
between-run validation fails the run on CHK-SCOPE (the item-2 backstop).

## Emitter fixtures (build item 4, ADR 0003)

`corpus/emitter/common/` is the shared catalog fixture — one role registry
(exercising `invocation` fields, both tags, and the `{args}` token) plus a
`bodies/` directory with a deliberate gap (one role has doctrine, two render
the placeholder marker). One catalog, many projections: every tree under
`corpus/emitter/<harness>/` is `role-emit project` output for one
projection-bearing descriptor row (the three real rows + the deliberately
alien `stub-epsilon` row), committed verbatim and reproduced byte-identically
×2 by the `emitter-projections` selftest section. `emitter/failures/` holds
the exit-2 render/verify cases (`case.json` + `expect_*` fragments; the
`errors/` family stays exit-1 per conformance rule #4): cap overflow,
unknown body stem, and a committed drifted tree for `verify`. Stamps derive
from kernel VERSION + catalog digest — regenerating after a catalog or
descriptor change is `role-emit project` per row (see Regeneration).

## Catalog projections (build item 5)

`kernel/catalog/` is **live normative data**, not fixture: the real 9-role /
4-arm registry (kata arms A, B, C, C-dbg) and the nine doctrine bodies
distilled from the committed Uncle Bob extracts (cited per body; gate names
unnumbered — thresholds are gate config; harness-neutral by the same token
list CHK-NEUTRAL uses). `corpus/catalog-projections/<harness>/` holds its
golden renders through the three real descriptor rows. The `catalog`
selftest section gates: registry schema-validity, bodies↔roles bijection
both ways, F2 layout markers (`Sources:`, `## Stage exit`, composite
`Merged role:` openers), the neutral scan over bodies and rendered cards,
golden reproduction ×2, and `verify` green in place. A doctrine edit is:
edit body → `role-emit project` per real row → commit the regenerated tree
(the ADR 0003 loop; an edit without regen is a red gate).

## Kata rig (build item 6)

`kernel/corpus/kata/` holds the study instrument's goldens. `preregistration.json`
and `workload.json` are copies of the live `kernel/catalog/kata-*.json` inputs
(the workload is a **placeholder** — its `provenance_note` records that the real
kata names, C1–C4, are filled at run time; the 12-instance / 240-cell shape is
the pre-registered count and is gate-pinned now). `plan.json` is the committed
`kata plan` expansion; `results-<branch>.json` + `verdict-<branch>.json` are the
five decision branches (`six-roles`, `three-roles`, `gates-not-roles`, `tamper`,
`solo`) plus the criterion-(i) conjunct fixtures (`conj-ia-only`,
`conj-margin-fail`) and the b_beats_a token fixture (`btok-fail`);
`wilson-exactness.json` pins the integer interval bounds; `scorecard.md` is the
`kata report` golden. `failures/` is the tamper trio (`prereg-edited`,
`results-inconsistent`, `stamp-mismatch` — declarative `case.json`, each exits 2
writing nothing, the `emitter/failures/` precedent). The `kata` selftest section
gates: the digest triangle (committed pre-registration block == frozen code
`PREREG_DIGEST`), plan/analyze/report reproduction ×2, all five decision reasons,
tamper precedence, Wilson exactness, and the failure trio. The LLM execution that
produces a real `kata_results` is the **deferred seam** (`kernel/docs/kata-seam.md`),
not exercised here. A criteria edit is loud by construction: it must change the
frozen code constants AND `kernel/catalog/kata-preregistration.json` AND re-pin
every results file, or the triangle reds the gate.

## Regeneration

Digest-bearing fixtures (fences, refs, ledger chains, tree digests) were
generated once by a throwaway script and are now plain committed files. Edit
by hand only if you recompute the affected digests; the selftest fails loudly
on any drift (that is its job). Family-wide restamps (schema_version bumps)
run through `validator/scripts/regen_corpus.py restamp`, which preserves the
validity relation: relations valid before the restamp are recomputed to stay
valid, deliberately-broken fixture relations keep their broken values, and
`expect.json` files are never written (script-asserted).
