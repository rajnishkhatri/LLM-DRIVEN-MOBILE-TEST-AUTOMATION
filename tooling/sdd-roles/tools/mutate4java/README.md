# mutate4java

The o7 mutation gate's engine: runs PIT (pitest) over a Maven Java workspace
and scores the suite by the fraction of generated mutants it detects. One of
the four Java gate tools of the R-KATA-STUDY equipment seam
(`kernel/docs/kata-seam.md`); built to the ir-gate-checker template
([ADR 0005](../../../../docs/architecture/adrs/tooling/sdd-roles/0005-ir-gate-first-class-gate-vocabulary.md)).

- **Tool id:** `mutate4java` (canon `gate_tool_allowlist`; the KernelConfig
  `mutation` row binds exactly this id)
- **Tool version:** `1.0.0`
- **Contract:** `o7-kata-seam.1`
- **Threshold (canon):** `mutation_score_min: 0.85` — echoed in every
  report, decided on the integer scale (below)
- **Engine:** `mvn test-compile <pitest>:mutationCoverage` with the PIT
  plugin invoked by full coordinates (`org.pitest:pitest-maven:1.16.1`) —
  the workspace pom needs **no PIT configuration** and the plugin version
  cannot drift per-workspace. XML output, untimestamped report dir.
- **Dependencies:** Python 3 stdlib + `mvn` on PATH (probed — exit 3 when
  absent). First-ever run needs network for the PIT plugin download.

## Invocation

```
mutate4java.py --workspace <dir> --report <out.json>
mutate4java.py selftest
```

KernelConfig row (`configs/o7/kernel-config.json`):

```json
{
  "id": "mutation",
  "tool": "mutate4java",
  "argv": ["{mutate4java}", "--workspace", "{workspace}", "--report", "{report}"],
  "threshold": "mutation_score_min"
}
```

with `--bind mutate4java=<absolute path to mutate4java.py>` at `gate-runner
run` time. Exit taxonomy: **0** green (report written); **2** red (report
written — fail-closed); **3** usage/environment error (nothing written).

## Verdict semantics — integer arithmetic only

A mutant counts as detected iff PIT marks `detected="true"` (KILLED,
TIMED_OUT, …). The decision value is the floor-scaled integer the kata rig
consumes (the rig is integer-only — `kernel/docs/kata-seam.md`):

```
mutation_score_scaled = detected * 10000 // total      (floor division)
green  iff  total > 0  and  mutation_score_scaled >= 8500
```

The float `mutation_score` in the report is display-rounded from the same
division; `threshold_scaled: 8500` records the integer form of the canon
0.85. Surviving/uncovered mutants are enumerated (class, method, line,
mutator, status) so a red is actionable.

Fail-closed paths (red with a `not_evaluable` reason): missing pom.xml;
engine failure before a mutations.xml exists — including a failing suite
(PIT runs the tests itself and aborts); unparseable XML; zero generated
mutants (vacuous); engine timeout (900 s).

## Report shape

Canonical JSON (sorted keys, 2-space indent, ASCII, trailing newline). No
clocks, no absolute paths; survivor list and status counts sorted:

```
artifact_type: "mutation_report", tool, tool_version, contract, engine,
inputs: {pom_sha256},
mutants: {total, detected, by_status: {STATUS: n}},
survivors: [{class, method, line, mutator, status} sorted],
mutation_score, mutation_score_scaled, not_evaluable: null | reason,
threshold: {name: "mutation_score_min", value: 0.85}, threshold_scaled: 8500,
verdict: green|red
```

## Fixtures + selftest

`fixtures/` holds 3 cases — `green` (boundary-tight tests kill 5/5 mutants,
scaled 10000), `red-surviving` (a suite that never probes the clamp
boundary: ConditionalsBoundary survives + an uncovered return mutant →
2/4, scaled 5000), `red-unevaluable` (no pom.xml). Each pins `case.json`
and `expected-report.json` (byte golden, written by this tool — the
ADR 0002 pattern). `selftest` copies each workspace to a temp dir, runs
every case twice (byte-identity — this also proves PIT's mutant set is
deterministic for the fixture), compares goldens, and probes the exit-3
usage paths.
