# O7 Spine — Mock Artifact Index

End-to-end mock coverage of the **O7 pipeline** — the interpreter-based fork of
O1. O7 shares O1's spine *contract* (committed reviewed artifacts, an LLM-free
deterministic replay spine, SHA-pinned auditability) but replaces O1's per-test
**code-generation** stage with a **version-pinned, LLM-free interpreter** that
executes the committed `TestCaseIR` directly over Appium/Perfecto.

> **Fork lineage.** O7 forks the O1 spine. Where an artifact is *unchanged from
> O1*, this set does not duplicate it — see `../o1-spine/` (the parent) for the
> shared authoring-arm mocks (`NormalizedIntent.*`, `TestCaseIR.skeleton.json`,
> `LoginScreen.*`, `ASHCapture.*`, `LocatorResolution.*`). This set carries only
> the artifacts O7 **changes or adds**: the v2 interpreter IR, the IR gate (which
> replaces `StaticGate.report.json`), the re-based `ReplayReport`, and the
> rendered execution plan. There is **no `LoginTest.java`** — O7 generates no code.
>
> Design source: `../../mobile-test-automation-interpreter-spine-brainstorm.md`
> (bundle F-B · E2 · H-SB · C-MIG · R-YES · A-STD; review resolved R4 + R2).
> Walkthrough: `../../o7-pipeline-walkthrough.md`.

Scenario throughout: **ACC-2087** — "Send $25 to a saved Zelle recipient and see
the confirmation" (Octane source). Flow: **Sign in → Home → Pay & Transfers →
Zelle → Send money.** iOS / iPhone 15 / iOS 17.4, on the Perfecto cloud.

---

## What O7 changes vs O1 (the fork delta)

| O1 artifact (`../o1-spine/`) | O7 artifact (here) |
|---|---|
| `TestCaseIR.json` (opcode IR, no runtime fields) | `TestCaseIR.json` — **v2**: adds `timeoutMs`, `syncAfter`, `healPolicy` per step |
| `LoginTest.java` (generated executable) | **deleted** — the committed IR *is* the executable |
| `StaticGate.report.json` (format/compile/checkstyle/errorprone) | `IRGate.report.json` — schema · opcode-closed · bounded-waits · no-orphan · no-literal-creds · ambiguity-clear · dry-run |
| `ReplayReport.json` (pins `codeCommit`) | `ReplayReport.json` — **re-based**: pins `irDigest` + `interpreterVersion`; Perfecto versions as captured evidence; `cloudAdaptivity` + `commitPrincipal` + `noveltyFlag` |
| — | `ExecutionPlan.acc-2087.md` — **new** (E2): human-readable plan rendered from `irDigest`, attached as evidence |
| `LocatorCandidate.manifest.json` | unchanged in shape; O7 copy carries the ACC-2087 Zelle locators |

---

### Field-shape corrections, 2026-08-09 (owner decisions — next-items I5 + I7)

These mocks were edited to match the resolved field shapes. Read the o7 spec's
**pre-gate amendment** section and ADR 0016's **Accepted residual risk** section
before treating any of this as settled.

- `IRGate.report.json` — **`dryRun` moved inside `checks`** as the seventh entry.
  It was a sibling, which contradicted the spec, ADR 0016 and `ReplayReport.irGate`
  (all say seven), and let an "all checks PASS" loop over `checks{}` skip it.
- `ReplayReport.json` — **`irGate` gained `gateVersion`**, matching
  `IRGate.report.json`. It is deliberately **not** part of the F6 applicable set.
- `ReplayReport.json` — **`cloudAdaptivity` is a four-state pair**
  (`DISABLED` | `ENABLED` | `UNKNOWN` | `NOT_APPLICABLE`), not a boolean.

> ⚠ **This mock depicts a POST-confirmation state and cannot be produced today.**
> Perfecto documents no code-path AI toggle and no way to attest one, so
> `perfectoAI` currently resolves to **`UNKNOWN`**, which **quarantines** — the run
> would record no verdict, and this file's `"verdict": "PASS"` would be
> unreachable. `NOT_APPLICABLE` becomes valid only once Perfecto confirms in
> writing that Scriptless self-healing does not touch code-path Appium sessions
> (folded into the open vendor contact, next-items I6). The `attestationRef` here
> is a placeholder, not a real reference.

---

## Pipeline flow (O7)

```
        AUTHORING ARM (LLM-bounded, forked unchanged from O1)          SPINE (LLM-free — O7 delta)
  ─────────────────────────────────────────────────────────────  ───────────────────────────────────

  Octane ACC-2087
        │
        ▼
  ingest → A1 parse → A2 interpret → capture + locator resolution
                          │ (skeleton, shared with O1)      │ LocatorCandidate.manifest.json
                          ▼                                 ▼
             ══ committed TestCaseIR.json (v2) + manifest ══ git commit (SERVICE principal, R1/R4) ══
                                                             │
                                                    ┌────────▼─────────┐   ┌──────────────┐   ┌──────────┐
                                                    │ IRGate.report    │──►│ interpreter  │──►│ Replay   │
                                                    │ (replaces static)│   │ (no codegen) │   │ Report   │
                                                    └──────────────────┘   └──────────────┘   └────┬─────┘
                                                                                                   │
                                                                        §7 human evaluator (R4) ◄──┘
                                                                        novelty-sampled (R2); CERTIFY = individual principal
```

---

## Files in this set

| File | What it is | Fork status |
|---|---|---|
| `TestCaseIR.json` | The committed executable — v2 IR with runtime fields, 11 Zelle steps | **changed** (v2) |
| `LocatorCandidate.manifest.json` | The 10 committed Zelle locators the IR references | forked (ACC-2087 data) |
| `IRGate.report.json` | Deterministic pre-device gate result | **new** (replaces `StaticGate.report.json`) |
| `ReplayReport.json` | The verdict artifact, re-based audit pin + A-STD evidence bundle | **changed** (re-based) |
| `ExecutionPlan.acc-2087.md` | E2 human-readable plan, rendered from `irDigest`, evidence-not-pin | **new** |
| `README.md` | This index | — |

For every artifact **not** listed here (normalized intent, skeleton, page source,
object spy, ASH capture, locator-resolution prompts), use the O1 parent set at
`../o1-spine/` — O7 does not change them.
