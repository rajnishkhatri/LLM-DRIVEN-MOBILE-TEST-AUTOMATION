# ir-gate-checker

The o7 IR gate's engine: a deterministic, pre-device, zero-compilation checker
for a committed `TestCaseIR` + `LocatorCandidate` manifest. Pinned as the ONLY
valid backing tool for kernel gate id `ir-gate` by
[ADR 0005](../../../../docs/architecture/adrs/tooling/sdd-roles/0005-ir-gate-first-class-gate-vocabulary.md);
check semantics come from the o7 interpreter spec
(`docs/sdd/specs/mobile-test-automation-o7-interpreter.spec.md`, "IR gate" row
+ EARS failure paths).

- **Tool id:** `ir-gate-checker` (KernelConfig `gates[]` rows for `ir-gate`
  MUST bind exactly this id — retro-linted by CHK-IRGATE-PIN)
- **Tool version:** `1.0.0` (carried in every report; the gate-runner refuses
  versionless outcomes)
- **Contract:** `o7-spec-derived.1` — see the schema-authority seam below
- **Dependencies:** Python 3 stdlib only (invoked as `{python} <path>`, like
  every gate tool: bindings are KernelConfig data, not kernel code)

## Invocation

```
python3 ir_gate_checker.py check --ir <ir.json> [--manifest <manifest.json>] --report <out.json>
python3 ir_gate_checker.py selftest
python3 ir_gate_checker.py seal --ir <draft.json> --out <sealed.json>   # authoring utility
```

Exit taxonomy (ADR 0005): **0** = all seven checks pass (report written);
**2** = any violation (report still written, enumerating all seven);
**3** = argv/usage error (nothing written). Gate-wrap descriptor rows must map
tool exits 2 and 3.

KernelConfig binding row (the shape ADR 0005 freezes):

```json
{
  "id": "ir-gate",
  "tool": "ir-gate-checker",
  "argv": ["{python}", "tools/ir-gate-checker/ir_gate_checker.py", "check",
           "--ir", "<committed IR path>", "--manifest", "<committed manifest path>",
           "--report", "{report}"],
  "threshold": "ir_gate_violations_max"
}
```

with `"ir-gate-checker"` in `gate_tool_allowlist` and threshold
`{"name": "ir_gate_violations_max", "value": 0}` declared.

## The seven checks

All seven ALWAYS run — no short-circuit (a short-circuiting check is the
mutant the hardener doctrine names). Any check that cannot evaluate its
property (unreadable/unparseable input) **fails** with a `not evaluable`
violation: fail-closed, never fail-open. Verdict is `green` iff
`violations_total == 0` (the ADR threshold).

| Check | Rejects when |
|---|---|
| `schemaValid` | IR unparseable; unknown/missing fields (closed shape); `healPolicy` ≠ `"NONE"`; malformed types; **broken seal** — `irDigest` ≠ sha256 of the canonical IR (compact sorted-key JSON, `irDigest` field removed) |
| `opcodeClosed` | opcode outside `{TAP, TYPE, SWIPE, WAIT, ASSERT, LAUNCH, NAVIGATE}`; assertion kind outside `{TEXT_EQUALS, ELEMENT_PRESENT, VALUE_CHECK}` |
| `boundedWaits` | any step lacking `timeoutMs`, or `timeoutMs` not a finite integer > 0 (determinism control — an unbounded wait breaks the `pass^k` premise) |
| `locatorManifest` | manifest absent/unreadable/shapeless; orphan `locatorRef` not in the manifest; duplicate manifest refs; empty candidate cascade (vacuously exhausted → would hard-fail on device) |
| `noLiteralCreds` | a step marked `sensitive: true` carrying a literal value; any literal value (step `value`, assertion `expected`) matching the fixed credential-token list below — vault-key indirection (`{"vaultRef": ...}`) is the only valid form |
| `ambiguityClear` | any step with `ambiguous: true` — resolved before commit, never at replay |
| `dryRun` | structural walk failure: empty `steps`; per-opcode field contract broken (see table in the source); `TEXT_EQUALS`/`VALUE_CHECK` without `expected`, `ELEMENT_PRESENT` with it. Walks only closed-set opcodes — closure itself is `opcodeClosed`'s finding |

Credential-token list, `o7-spec-derived.1` (case-insensitive substrings —
extending it is a contract change): `password`, `passwd`, `secret`, `token`,
`api_key`, `apikey`, `bearer`, `credential`, `private_key`.

## Report shape

Canonical JSON (sorted keys, 2-space indent, ASCII, trailing newline), no
absolute paths — byte-stable by construction:

```
artifact_type: "ir_gate_report", tool, tool_version, contract,
inputs: {ir_sha256, manifest_sha256}, ir_digest: {declared, computed},
checks: [ {id, outcome: pass|fail, violations: [{pointer, detail}]} ×7 in spec order ],
violations_total, threshold: {name: "ir_gate_violations_max", value: 0},
verdict: green|red
```

## Schema-authority seam (read before "fixing" a mismatch)

The **authoritative** `TestCaseIR` JSON Schema is the o7 Spring Boot repo's
T05-regenerated schema (Java records → committed schema; drift fails CI
there). That repo is separate and the schema does not exist here, so this tool
enforces a **spec-derived contract** — every rule above traces to a spec line
(EARS failure paths, S3/S4/S9, the IR-gate row). At integration time the two
must be reconciled deliberately: divergence is a seam decision recorded
against ADR 0005, not a silent edit on either side.

## Fixtures + selftest

`fixtures/` holds 8 cases — `green` (the sealed Zelle ACC-2087 send-money
shape) and one `red-<check>` per check, each an isolated single-check delta
off green with a correct seal (except `red-schemaValid`, whose broken seal IS
the delta). Each case pins `case.json` (expected exit + expected red checks)
and `expected-report.json` (byte golden, written by this tool and held
against it forever after — the ADR 0002 pattern). `selftest` runs every case
twice (byte-identity), compares goldens, and probes the exit-3 usage paths.
