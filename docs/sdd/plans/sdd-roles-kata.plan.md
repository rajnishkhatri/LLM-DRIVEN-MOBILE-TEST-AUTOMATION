# Plan: SDD Roles Kata Rig — the deterministic study instrument (Track A, build item 6)

**Spec:** `docs/sdd/specs/sdd-roles-kata.spec.md` (SIGNED OFF v2). **Status:** IMPLEMENTED 2026-08-08 — combined SPEC-OK+PLAN-OK gate CLOSED; WP0–WP7 all landed (KA01–KA22); build record in the tasks file. Spec-review criticals folded (F2 two-conjunct C_i + b_beats_a token gate + widened Wilson; F3 winner map; WP3/WP4 full restamp + projection regen).
**House constraints carried:** offline + deterministic gate; single dependency (jsonschema); corpus-first; `contract-lint selftest` is the gate; clock-free digest-stamped rendering; all-or-nothing writes; exit taxonomy 1=argv / 2=render-or-validation; NO new CHK ids (tampers live in a `kata/failures/` family, not `invalid/CHK-*`); the LLM run is a deferred, documented seam.

## 1. Abstractions (G1 table)

| abstraction | decision | rejected alternative |
|---|---|---|
| Rig placement | `kata` is a **new 6th console script** (`sdd_roles_validator.kata`), one module = one artifact family — a distinct principal (study instrument), not a mode of `gate-runner` (the ledger writer) or `role-emit` (the projector). Pure `render_plan`/`analyze` live here; the frozen constants + integer stats live in a sibling `kata_analyzer.py`. | Subcommands bolted onto `role-emit` (conflates projection with measurement; pollutes that CLI's exit contract); a mode of `gate-runner` (the runner writes ledgers — the analyzer must be side-effect-free and ledger-independent). |
| Deterministic/deferred split | Built: `plan`/`analyze`/`report` — pure, clock-free, byte-identical ×2, golden-gated. Deferred: the LLM driver + crap4java/mutate4java implementations, specified only in `kernel/docs/kata-seam.md`. The seam feeds the **existing, unchanged** `gate-runner run` conveyor and emits a `kata_results` file; the analyzer is the sole consumer. | Building a live orchestrator now (needs cursor/copilot CLIs — absent — and a multi-hour LLM budget; and would let the analysis be tuned to data, defeating pre-registration). |
| Pre-registration binding | **Digest triangle** (spec S3): `PREREG_CONSTANTS` frozen in `kata_analyzer.py`; `PREREG_DIGEST = sha256(canonical_dumps(PREREG_CONSTANTS))` at import; the `kata` section asserts the committed `kata-preregistration.json` canonical constants block == `PREREG_DIGEST`; every `kata_results.prereg_digest` must == `PREREG_DIGEST` or `analyze` refuses (exit 2). | Golden-only (a coordinated same-commit threshold+golden edit passes — no cross-artifact bind); thresholds supplied by the results file (lets data pick its own bar). |
| Statistics | Integer fixed-point (spec S4): scale `S=10000`, `z²=9604/2500`, `math.isqrt` only, floor-lower/ceil-upper (conservative widening — makes criterion (i) *harder*, never falsely declares non-overlap), token ratios cross-multiplied. ONE frozen Wilson expression; a golden-fragility comment forbids post-cut refactor. | `float`→`Decimal` quantize (libm `sqrt` can cross a rounding boundary before quantize → cross-machine byte drift; the gate's ×2 identity would be luck, not proof). |
| Verdict | Single closed shape (spec S5): `winner∈{A,B,C,none}` × `decision_reason∈{tamper-invalid,gates-not-roles,six-roles-earned,three-roles,default-solo}`; precedence `tamper→kill→C→B→default`; C−dbg is a non-decisional `ablation` block; criteria carry operands. | Bare boolean flags (scorecard can't self-substantiate); an exit code encoding "criteria met" (couples the decision to process control — the verdict is *content*, `analyze` exits 0 whenever it computed a well-formed verdict). |
| Metrics | Lossless per-cell (spec S6): all 8 §6 metrics on `kata_results.observations[*]`; analyzer aggregates to `k/n` internally but the file stays lossless so the real run is re-analyzable. | Pre-aggregated `{k,n,tokens,tamper}` observations (drops 6 of 8 metrics; the real run could never be re-analyzed for a secondary metric — the faithfulness checker's rejected design). |
| Gate | One `Section("kata")` (spec S7): plan ×2 vs golden + cell count; analyze over 5 branch fixtures ×2 vs 5 verdict goldens (all 5 reasons); Wilson-exactness fixture; report ×2 vs scorecard golden + neutral scan; `kata/failures/` tamper trio; `kata` errors family; `arithmetic` additions. No new CHK id; invalid-family count stays 26. | New `CHK-KATA-*` ids under `invalid/` (forces registry.CHECKS + structure-bijection + the 26 count to move — needless blast radius for section-level negative controls that items 4/5 model as a `failures/` family). |
| Versioning | Whole-kernel `VERSION` 1.3.0 → **1.4.0** (additive: 5 new schemas + `invocation.model` population + cursor `args_token`), validator 0.5.0 → **0.6.0**. Atomic restamp of every schema const + descriptor + `corpus/valid/**` + `corpus/runs/**` + catalog. | Stamping new schemas 1.3.0 (the `schema-drift` section forbids a mixed set — one VERSION drives every const; a 1.3.0-new schema reds the first sweep and mislabels an additive change). |

## 2. Repo tree delta

```
tooling/sdd-roles/
├── kernel/
│   ├── VERSION                                    # 1.3.0 → 1.4.0
│   ├── schemas/
│   │   ├── kata-preregistration.schema.json       # NEW  kata_preregistration
│   │   ├── kata-workload.schema.json              # NEW  kata_workload
│   │   ├── kata-plan.schema.json                  # NEW  kata_plan
│   │   ├── kata-results.schema.json               # NEW  kata_results
│   │   ├── kata-verdict.schema.json               # NEW  kata_verdict
│   │   └── *.schema.json                          # EDIT const 1.3.0 → 1.4.0 (×8 existing)
│   ├── catalog/
│   │   ├── kata-preregistration.json              # NEW  frozen constants (C5–C8); == PREREG_DIGEST
│   │   ├── kata-workload.json                     # NEW  placeholder 12 instances (CLARIFY: C1–C4)
│   │   └── role-registry.json                     # EDIT invocation.model populated; restamp 1.4.0
│   ├── descriptors/invocation-descriptors.json    # EDIT cursor args_token bound; restamp 1.4.0
│   ├── corpus/
│   │   ├── kata/                                   # NEW golden family
│   │   │   ├── preregistration.json  workload.json  plan.json
│   │   │   ├── results-{six-roles,three-roles,gates-not-roles,tamper,solo}.json
│   │   │   ├── verdict-{six-roles,three-roles,gates-not-roles,tamper,solo}.json
│   │   │   ├── wilson-exactness/{results.json,verdict.json}
│   │   │   ├── scorecard.md
│   │   │   └── failures/{prereg-edited,verdict-drift,results-inconsistent}/case.json
│   │   ├── valid/{KataPreregistration,KataWorkload,KataPlan,KataResults,KataVerdict}/  # NEW ×5 + expect.json
│   │   ├── errors/kata-{no-subcmd,unknown-subcmd,missing-out,missing-plan}/case.json  # NEW
│   │   └── valid/**, runs/**                       # EDIT restamp 1.4.0
│   └── docs/
│       ├── kata-seam.md                            # NEW  deferred LLM-run driver spec
│       └── conformance.md, corpus-guide.md         # EDIT kata family + port rule #10
├── validator/
│   ├── src/sdd_roles_validator/
│   │   ├── kata.py                                 # NEW  CLI (plan/analyze/report + render_plan)
│   │   ├── kata_analyzer.py                        # NEW  PREREG_CONSTANTS, PREREG_DIGEST, integer stats
│   │   ├── loader.py                               # EDIT KNOWN_TYPES/SCHEMA_FILES +5
│   │   ├── emitter.py                              # EDIT CONSOLE_SCRIPTS + kata
│   │   └── selftest.py                             # EDIT CLI_MODULES+kata, VALID_DIRS+5, Section("kata"), arithmetic
│   ├── scripts/acceptance.sh                       # EDIT kata_* assertions; header
│   ├── README.md                                   # EDIT
│   └── pyproject.toml / __init__.py                # EDIT + kata script; validator 0.6.0
└── docs/architecture/adrs/tooling/sdd-roles/0004-kata-rig-deterministic-instrument.md  # NEW
```

## 3. Tech selections

Unchanged house stack (py3.11+, jsonschema, `canonical_dumps`). New surface is two pure modules; `math.isqrt` (stdlib) is the only added primitive. Schemas are Draft 2020-12, closed at every level (`additionalProperties:false`), consts for `schema_version`/`artifact_type` (the `schema-drift` + closedness sections gate this). No new dependency (C3 single-dependency clause holds).

## 4. Delegated normative values — F-readings (owner, at the gate)

| id | reading |
|---|---|
| **F1** | **The pre-registration constants, frozen** (`kata-preregistration.json` + `PREREG_CONSTANTS`), C5–C8 baked: `arms=["A","B","C","C-dbg"]`, `reps=5`, `instance_count=12`, `primary_metric="final_all_gates_pass"`, `interval_method="wilson"`, `wilson_z_num=9604`, `wilson_z_den=2500`, `scale=10000`; `criteria={c_over_a_pp:10, c_over_a_intervals:"non-overlapping", c_over_a_token_ratio_max:3, c_over_b_pp:5, b_over_a_pp:5, b_over_a_token_ratio_max:2, kill_a_within_c_pp:5, kill_a_token_num:1, kill_a_token_den:2, tamper_zero_tolerance:true}`. These are the pre-registration; ratifying F1 IS ratifying the experiment's immutable analysis. |
| **F2** | **Predicate set + precedence, frozen** (integer, S=10000; every `rate`/`k`/`n` derives from `primary_metric = final_all_gates_pass`): `C_i = (rate(C)-rate(A) >= 1000) and (wilson_lo(C) > wilson_hi(A))` — **two explicit conjuncts** (i-a point-margin, i-b strict non-overlap; touching = overlap = fail); `C_ii = tok_C <= 3*tok_A`; `C_iii = rate(C)-rate(B) >= 500`; `b_beats_a = (rate(B)-rate(A) >= 500) and (tok_B <= 2*tok_A)` — **both conjuncts** (the ≤2× token gate is normative, not just evidence-line); `kill = (rate(A) >= rate(C)-500) and (tok_A*2 <= tok_C)`; `tamper_fail = any(row.tamper_instance) or sum(tamper_events)>0`. Precedence: `tamper_fail → kill → (C_i∧C_ii∧C_iii) → b_beats_a → default-solo`. All bar comparisons `>=` (boundary passes, §6 "≥"). **Wilson bounds (both widened, never narrowing):** `ceil_sqrt(X) = h if h*h==X else h+1 (h=isqrt(X))`; `wilson_lo = max(0, floor(center*S) - ceil_sqrt(rad))`, `wilson_hi = min(S, ceil(center*S) + ceil_sqrt(rad))` — `# do not refactor after golden cut`. C−dbg contributes **zero** operands to any predicate. |
| **F3** | **Verdict + report shape, frozen**: `winner∈{A,B,C,none}`, `decision_reason∈{tamper-invalid,gates-not-roles,six-roles-earned,three-roles,default-solo}`, bound by the frozen map `tamper-invalid→none, gates-not-roles→A, six-roles-earned→C, three-roles→B, default-solo→A`; `arms[]` arm_stat with k/n/rate10k/wilson bounds/tokens/mutation/crap/wall-clock/per-gate-first-attempt/handoff/tamper; `ablation` block (C minus C−dbg point-margin + interval-overlap, **diagnostic only, no operand contribution**); `criteria[]` self-describing with operands (incl. C_i's two conjuncts and b_beats_a's token conjunct). Report is a pure re-projection (never recomputes). Golden branches: `six-roles / three-roles / gates-not-roles / tamper / solo`, plus the two-conjunct criterion-(i) fixtures and a `three-roles`-token-fail fixture (B clears +5pp but exceeds 2× tokens → must not win). Tamper verdict reports pre-void per-arm k/n for self-substantiation; no criterion boolean true. |
| **F4** | **Bindings + versions, frozen**: `invocation.model` populated per role (F1-of-item-5 registry unchanged otherwise); `--default-model` default `"UNBOUND"` (C6); cursor projection `args_token` bound (S8); `VERSION=1.4.0`, validator `0.6.0`; acceptance asserts the new `kata` section + `kata_cells==240`, `kata_result_branches==5`, `kata_verdict_goldens==5`, valid-corpus over 13 types, `catalog_trees==3`/`emitter_trees==4`/`guard_cases==23`/`flipped_cases==12` retained. ADR 0004 drafted Proposed. |

## 5. Work packages

| wp | scope | proof |
|---|---|---|
| WP0 | Five schemas (closed, 1.4.0) + `loader` type additions | jsonschema metaschema + closedness green; valid-corpus targets validate |
| WP1 | `kata_analyzer.py`: `PREREG_CONSTANTS`, `PREREG_DIGEST`, integer `wilson_interval`/`rate10k`/`evaluate` (F2) | Wilson-exactness fixture: committed bounds == isqrt computation for known (k,n) |
| WP2 | `kata.py`: `plan`/`analyze`/`report` (pure, clock-free, all-or-nothing, exit taxonomy) | argv/errors family exit 1; render failures exit 2 writing nothing |
| WP3 | Committed pre-registration + placeholder workload + `role-registry.json` model population + cursor `agent-card` `args_token`; **full 1.4.0 restamp**: 8 existing schema consts, all `corpus/valid/**` + `corpus/invalid/**` (incl. `CHK-SCOPE/added-under-tests/ledger.ndjson`), `descriptors`, `catalog/role-registry.json` (via `regen_corpus.py` where it applies) | schema-drift green; PREREG_DIGEST == committed block |
| WP4 | Golden corpus: plan.json, 5 results + 5 verdict branches, Wilson-exactness + two-conjunct-(i) + token-fail fixtures, scorecard.md; **regenerate** `corpus/runs/**` (runner), `corpus/catalog-projections/**` + `corpus/emitter/**` (emitter, with the new `kata` CONSOLE_SCRIPTS line) for the 1.4.0 stamp | render ×2 byte-identical vs goldens; orchestrator/catalog/emitter sections green |
| WP5 | `Section("kata")` + `arithmetic` additions + `acceptance.sh` + valid-corpus 8→13 | selftest 20/20 ×2 byte-identical, zero DEFERRED |
| WP6 | `kernel/docs/kata-seam.md` + conformance #10 + corpus-guide + README; validator 0.6.0 | validate green; seam doc names the exact `kata_results` contract |
| WP7 | Gate close: double selftest, acceptance, tamper trio (each flips `kata` alone), ADR 0004, headers, log, memory | records in tasks header |

## 6. Risks

| risk | mitigation |
|---|---|
| 1.4.0 restamp blast radius (all corpus/descriptor/catalog + `invocation.model` restamps every catalog/emitter projection golden) | One atomic sequence (WP3→WP4); any miss reds `schema-drift`/`valid-corpus`/`catalog`. Use `regen_corpus.py` for the mechanical restamp; regenerate projection goldens via `role-emit project`. |
| Frozen Wilson expression is golden-fragile | By design (pre-registration immutability). Pin the ONE cross-multiplied form; `# do not refactor after golden cut` comment; the ×2 byte test is the guard. |
| A synthetic branch fixture accidentally satisfies two reasons | The precedence order makes the outcome deterministic regardless; but each fixture is *constructed* to make its reason the FIRST-firing one, and HP2 asserts the tamper branch yields `tamper-invalid` even when raw operands would clear a bar (proves precedence, not just outcome). |
| Placeholder workload mistaken for the real one | `CLARIFY:` marker in `kata-workload.json` + the C1 row; the arithmetic pins 12/240 (the pre-registration count) so the shape is real even while names are placeholders. |
| `invocation.model` population contradicts item-5 S6 | Acknowledged: item-5 S6 explicitly left `model` as "a deployment parameter for item 6"; this item is that item. ADR 0004 records the change; the registry stays schema-valid (schema already allowed `invocation.model`). |
| Tamper compound command hits the Bash 10-min cap (item-5 lesson) | One gate run per command, backgrounded; tampers applied and reverted one at a time with kept backups. |

## 7. Gate — combined SPEC-OK + PLAN-OK (OPEN)

Awaiting owner: C1–C8 spec locks (C1–C4 owner-decided 2026-08-08 = placeholder; C5–C8 defaulted); F1–F4 readings above; ADR 0004 Proposed→Accepted. On close: Stage-3 tasks (`docs/sdd/plans/sdd-roles-kata.tasks.md`), then implementation; build-gate target: selftest 20/20 ×2 byte-identical, zero DEFERRED, acceptance PASS at 1.4.0/0.6.0, tamper trio verified-landed each flipping `kata` alone.
