# crap4java

The o7 CRAP gate's engine: runs the suite under the JaCoCo agent and scores
every method with the classic crap4j composite
`CRAP(m) = comp(m)^2 * (1 - cov(m))^3 + comp(m)`. One of the four Java gate
tools of the R-KATA-STUDY equipment seam (`kernel/docs/kata-seam.md`); built
to the ir-gate-checker template
([ADR 0005](../../../../docs/architecture/adrs/tooling/sdd-roles/0005-ir-gate-first-class-gate-vocabulary.md)).

- **Tool id:** `crap4java` (canon `gate_tool_allowlist`; the KernelConfig
  `crap` row binds exactly this id)
- **Tool version:** `1.0.0`
- **Contract:** `o7-kata-seam.1`
- **Threshold (canon):** `crap_composite: 6` — the per-method ceiling
  (workspace CRAP≤6, kata-seam C8 — deliberately tighter than the crap4j
  folklore default of 30). Green iff no method's rounded CRAP exceeds it.
- **Engine:** `mvn <jacoco>:prepare-agent test <jacoco>:report` with the
  JaCoCo plugin invoked by full coordinates
  (`org.jacoco:jacoco-maven-plugin:0.8.12`) — the workspace pom needs **no
  JaCoCo configuration** and the plugin version cannot drift per-workspace.
- **Inputs to the score:** JaCoCo XML — `COMPLEXITY` counter
  (missed+covered) as comp(m), `LINE` counter fraction as cov(m). Methods
  with no line counter (abstract/interface) are skipped.
- **Dependencies:** Python 3 stdlib + `mvn` on PATH (probed — exit 3 when
  absent). First-ever run needs network for the JaCoCo plugin download.

## Invocation

```
crap4java.py --workspace <dir> --report <out.json>
crap4java.py selftest
```

KernelConfig row (`configs/o7/kernel-config.json`):

```json
{
  "id": "crap",
  "tool": "crap4java",
  "argv": ["{crap4java}", "--workspace", "{workspace}", "--report", "{report}"],
  "threshold": "crap_composite"
}
```

with `--bind crap4java=<absolute path to crap4java.py>` at `gate-runner run`
time. Exit taxonomy: **0** green (report written); **2** red (report
written — fail-closed); **3** usage/environment error (nothing written).

## Verdict semantics + fail-closed paths

Green iff evaluable AND ≥ 1 method measured AND `over_threshold_count == 0`
(no method's CRAP, rounded to 2 dp, exceeds 6). Red with a `not_evaluable`
reason when: pom.xml missing; the engine fails before a JaCoCo XML exists —
**including failing tests** (this gate measures the coverage of a passing
suite; the `tests` gate owns failures); unparseable XML; zero measured
methods (vacuous); engine timeout (900 s). Scores are rounded (coverage
4 dp, CRAP 2 dp) BEFORE comparison, so the numbers in the report are the
decision basis.

## Report shape

Canonical JSON (sorted keys, 2-space indent, ASCII, trailing newline). No
clocks, no absolute paths. The `crap` object carries exactly the fields the
kata extraction step reads (`kernel/docs/kata-seam.md`):

```
artifact_type: "crap_report", tool, tool_version, contract, engine,
inputs: {pom_sha256}, methods_total,
crap: {max, mean, over_threshold_count,
       per_method: [{method: "pkg.Cls#name(desc)", complexity, coverage, crap} sorted]},
not_evaluable: null | reason,
threshold: {name: "crap_composite", value: 6}, verdict: green|red
```

## Fixtures + selftest

`fixtures/` holds 3 cases — `green` (fully covered simple methods, max CRAP
2.0), `red-crap` (a complexity-5 method with zero coverage → CRAP 30.0 > 6),
`red-unevaluable` (no pom.xml). Each pins `case.json` and
`expected-report.json` (byte golden, written by this tool — the ADR 0002
pattern). `selftest` copies each workspace to a temp dir, runs every case
twice (byte-identity), compares goldens, and probes the exit-3 usage paths.
