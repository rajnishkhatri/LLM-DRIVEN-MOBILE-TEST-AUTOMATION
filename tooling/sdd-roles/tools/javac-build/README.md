# javac-build

The o7 build gate's engine: a deterministic wrapper around `mvn compile` for
a Maven Java workspace. One of the four Java gate tools of the R-KATA-STUDY
equipment seam (`kernel/docs/kata-seam.md`); built to the ir-gate-checker
template ([ADR 0005](../../../../docs/architecture/adrs/tooling/sdd-roles/0005-ir-gate-first-class-gate-vocabulary.md)
fixes the report/exit conventions all gate tools share).

- **Tool id:** `javac-build` (canon `gate_tool_allowlist`; the KernelConfig
  `build` row binds exactly this id)
- **Tool version:** `1.0.0` (carried in every report; the gate-runner
  refuses versionless outcomes)
- **Contract:** `o7-kata-seam.1`
- **Threshold (canon):** `build_errors_max: 0` — echoed in every report
- **Dependencies:** Python 3 stdlib + `mvn` on PATH (environment
  precondition, probed — exit 3 with a clear message when absent, never a
  fake report). First-ever run needs network for Maven plugin downloads.

## Invocation

```
javac_build.py --workspace <dir> --report <out.json>
javac_build.py selftest
```

No subcommand on the check path — the committed KernelConfig row invokes the
tool executable directly (`configs/o7/kernel-config.json`):

```json
{
  "id": "build",
  "tool": "javac-build",
  "argv": ["{javac_build}", "--workspace", "{workspace}", "--report", "{report}"],
  "threshold": "build_errors_max"
}
```

with `--bind javac_build=<absolute path to javac_build.py>` at `gate-runner
run` time (the file is executable; the runner execs argv[0] directly).

Exit taxonomy: **0** = green (report written); **2** = red (report written —
fail-closed, including every not-evaluable path); **3** = usage or
environment error (nothing written).

## Verdict semantics

Green iff the workspace is evaluable AND parsed compiler errors ≤
`build_errors_max` (0). Fail-closed paths — all red with a `not_evaluable`
reason in the report: missing workspace dir, no `pom.xml` at the workspace
root, engine failure without parseable compiler diagnostics, engine timeout
(900 s). The verdict basis is parsed `[ERROR] <file>:[line,col] message`
diagnostics (deduplicated, sorted), never the raw engine exit alone.

## Report shape

Canonical JSON (sorted keys, 2-space indent, ASCII, trailing newline). No
clocks, no absolute paths (diagnostic paths are workspace-relative), no
engine timings — byte-stable by construction:

```
artifact_type: "build_report", tool, tool_version, contract, engine,
inputs: {pom_sha256}, errors: [{path, line, col, message} sorted],
errors_total, not_evaluable: null | reason,
threshold: {name: "build_errors_max", value: 0}, verdict: green|red
```

## Fixtures + selftest

`fixtures/` holds 3 cases — `green` (compiles clean), `red-compile` (missing
semicolon → one diagnostic), `red-unevaluable` (no pom.xml → fail-closed
red). Each pins `case.json` (expected exit + verdict) and
`expected-report.json` (byte golden, written by this tool and held against
it — the ADR 0002 pattern). `selftest` copies each workspace to a temp dir
(fixtures stay byte-clean; no `target/` pollution), runs every case twice
(byte-identity), compares goldens, and probes the exit-3 usage paths.

Golden caveat: diagnostics text comes from the installed JDK/Maven; goldens
are pinned against the toolchain that wrote them (javac's `"';' expected"`
is stable across JDK 11–24, but a future toolchain that rewords diagnostics
legitimately breaks the golden — regenerate deliberately, never silently).
