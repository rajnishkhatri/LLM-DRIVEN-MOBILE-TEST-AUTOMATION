# Conformance: the corpus is the contract (C3)

The **golden corpus + the spec's CHK table is the normative, language-neutral
contract** for the role kernel. The Python implementation under `validator/`
is the *reference* implementation — it holds no privileged authority (ADR 0001,
`docs/architecture/adrs/tooling/sdd-roles/`).

## Port admission procedure

A workspace whose stack is Java (or any language) MAY use an alternate-language
implementation of `contract-lint` + `gate-wrap` **only after** it passes the
identical golden corpus with identical verdicts:

1. For every case under `kernel/corpus/valid/` and `kernel/corpus/runs/`:
   exit 0, no fail entries.
2. For every case under `kernel/corpus/invalid/` with `expected: "fail"`:
   exit 2 and a fail entry naming the annotated `check_id` at the annotated
   `json_pointer`.
3. For every case with `expected: "deferred"`: exit 0 and a DEFERRED entry for
   the annotated check — **never green, never fail** (CHK-DEFER).
4. Every case under `kernel/corpus/errors/`: exit 1.
5. Every case under `kernel/corpus/gatewrap/`: the mapped decision output and
   wrapper exit, byte-exact.
6. The port must implement the self-integrity semantics: deterministic output
   (CHK-DET), offline operation (CHK-NET), the harness-token scan (CHK-NEUTRAL),
   temp-copy verdict stability + report naming (CHK-SELF), and DEFERRED
   reporting (CHK-DEFER).

7. **gate-runner ports** (since build item 2, ADR 0002): reproduce every
   committed golden run (`kernel/corpus/runs/orchestrator-*/`) **byte-
   identically** under the pinned clock (`orchestrator/goldens.json` recipes,
   machine values via `--bind` only), including the resume completion of the
   interrupted fixture and the tamper-refusal behavior (doctored ledger ⇒
   exit 2, nothing written). A port's runs must validate green under the full
   26-check live suite.

8. **write-guard ports** (since build item 3, D7 floor): reproduce the guard
   decision corpus (`kernel/corpus/guard/decisions/` — every case's exit code
   and decision line byte-exactly, fail-closed semantics included), render
   every committed mount golden (`kernel/corpus/guard/mounts/<harness>/`)
   byte-identically from descriptor `hooks` data, and reproduce the
   `orchestrator-hooked` / `orchestrator-unhooked` golden pair (live block
   leaves no ledger trace; the unhooked control validates red on exactly
   CHK-SCOPE). The scope rules MUST come from the same rule source the port's
   retro CHK-SCOPE uses (spec S5: one rule source, two enforcement times).

9. **role-emit ports** (since build item 4, ADR 0003): reproduce every
   committed projection tree (`kernel/corpus/emitter/<harness>/`)
   **byte-identically** from descriptor `projection` data over the shared
   catalog fixture (`emitter/common/`), with `verify` exiting 0 on each
   committed tree and 2 on the committed drifted fixture
   (`emitter/failures/verify-drift/`). `char_cap` counts UTF-8 **bytes** of
   the rendered file. `mount-copy` targets MUST byte-equal the port's own
   mount rendering for the same row and registry (one rendering source —
   the item-3 rule applied to packaging), and MUST NOT carry a stamp. A
   failed render writes nothing (`emitter/failures/` cases are the proof).
   Since build item 5, ports also reproduce the **real-catalog** projection
   goldens (`kernel/corpus/catalog-projections/<harness>/` — the committed
   `kernel/catalog/` registry + doctrine bodies rendered through the three
   real descriptor rows, byte-identically, verify exit 0 in place).
10. **kata ports** (since build item 6, ADR 0004): reproduce the kata rig's
    deterministic outputs **byte-identically** — `plan` over the committed
    registry + workload + reps equals `kernel/corpus/kata/plan.json` (240
    cells); `analyze` over each `results-<branch>.json` + the committed
    pre-registration equals `verdict-<branch>.json` (all five decision
    reasons); `report` equals `scorecard.md`. The **digest triangle** MUST
    hold: the port's frozen criteria constants, the committed
    `kernel/catalog/kata-preregistration.json` constants block, and every
    `kata_results.prereg_digest` share one sha256; a port MUST refuse (exit 2)
    a pre-registration whose stored digest disagrees with its own constants or
    with the frozen code, a results file whose `plan_stamp`/`prereg_digest`
    mismatches, an observation set that does not biject the plan cells, and any
    observation with `provenance != "tool_output"` or a `final_all_gates_pass`
    that contradicts its per-gate `final_pass` (the `kata/failures/` cases are
    the proof). Wilson bounds are exact integers (scale 10000, z**2=9604/2500,
    both bounds widened via ceil-sqrt); the committed `wilson-exactness.json`
    table pins them. C-dbg is a non-decisional ablation (zero criterion
    operands); the result-level tamper rule makes any tamper instance
    `winner: none` / `tamper-invalid` before any interval math.

Record each admission (implementation, version, corpus schema_version, date)
in `docs/architecture/log.md`. A port that later diverges on any corpus case
loses admission until re-passed.

## Change discipline

Every check change lands as: CHK-table row (spec) + corpus family + validator
implementation, in one change. The selftest's registry↔corpus bijection makes
a check without cases (or cases without a check) a gate failure — there is no
second list to drift.

`schema_version` (kernel/VERSION, mirrored as a `const` in every schema)
follows SemVer: item-2 additive fields are minor bumps; breaking changes are
major and require regenerating annotations.
