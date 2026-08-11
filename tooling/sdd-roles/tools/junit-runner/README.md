# junit-runner

The o7 tests gate's engine: a deterministic wrapper around `mvn test` +
surefire XML parsing for a Maven Java workspace. One of the four Java gate
tools of the R-KATA-STUDY equipment seam (`kernel/docs/kata-seam.md`); built
to the ir-gate-checker template
([ADR 0005](../../../../docs/architecture/adrs/tooling/sdd-roles/0005-ir-gate-first-class-gate-vocabulary.md)
fixes the report/exit conventions all gate tools share).

- **Tool id:** `junit-runner` (canon `gate_tool_allowlist`; the KernelConfig
  `tests` row binds exactly this id)
- **Tool version:** `1.0.0`
- **Contract:** `o7-kata-seam.1`
- **Threshold (canon):** `tests_failures_max: 0` — echoed in every report;
  failures and errors BOTH count against it
- **Dependencies:** Python 3 stdlib + `mvn` on PATH (probed — exit 3 when
  absent, never a fake report). First-ever run needs network for Maven
  plugin downloads.

## Invocation

```
junit_runner.py --workspace <dir> --report <out.json>
junit_runner.py selftest
```

KernelConfig row (`configs/o7/kernel-config.json`):

```json
{
  "id": "tests",
  "tool": "junit-runner",
  "argv": ["{junit_runner}", "--workspace", "{workspace}", "--report", "{report}"],
  "threshold": "tests_failures_max"
}
```

with `--bind junit_runner=<absolute path to junit_runner.py>` at
`gate-runner run` time. Exit taxonomy: **0** green (report written); **2**
red (report written — fail-closed); **3** usage/environment error (nothing
written).

## Verdict semantics

Green iff the workspace is evaluable AND the suite discovered ≥ 1 test AND
`failures + errors ≤ tests_failures_max` (0). The verdict basis is the
surefire `TEST-*.xml` result files, never the raw engine exit alone.

**Zero tests is RED**, not green: a vacuous pass is fail-open — deleting the
suite must never turn this gate green (the same reasoning that write-protects
`tests/**` in the canon protected set). Other fail-closed paths: missing
pom.xml, unparseable surefire XML, suite-count/parsed-case inconsistency,
engine failure without result files, engine timeout (900 s).

## Report shape

Canonical JSON (sorted keys, 2-space indent, ASCII, trailing newline). No
clocks, no absolute paths, no per-test timings:

```
artifact_type: "tests_report", tool, tool_version, contract, engine,
inputs: {pom_sha256},
counts: {tests, failures, errors, skipped},
failing: [{test: "cls#method", kind: failure|error, message} sorted],
failures_total, not_evaluable: null | reason,
threshold: {name: "tests_failures_max", value: 0}, verdict: green|red
```

`message` is the first line of the surefire failure/error message (assertion
text — deterministic), falling back to the exception type.

## Fixtures + selftest

`fixtures/` holds 3 cases — `green` (3 passing tests), `red-failing` (one
assertion failure among passing tests), `red-unevaluable` (no pom.xml).
Each pins `case.json` and `expected-report.json` (byte golden, written by
this tool — the ADR 0002 pattern). `selftest` copies each workspace to a
temp dir, runs every case twice (byte-identity), compares goldens, and
probes the exit-3 usage paths.
