# Mock Artifact Suite — Six-Way Comparison (O1–O6)

Illustrative artifacts for the six architecture options evaluated in the ARB comparison
(`docs/research/mobile-test-automation-poc-arb-comparison.md`) and the SDD Stage-1 brainstorm
(`docs/research/mobile-test-automation-poc-brainstorm.md`).

## Purpose

These mocks make the architectural differences between the six options **concrete** rather than
slogan-level. Each option produces different artifacts with different shapes, audit pins, and
control surfaces. Reading the same test scenario rendered in each option's artifact form is the
fastest way to see what each option actually *commits to*, *audits against*, and *controls for*.

## Shared scenario

All six options render the **same** test: `ACC-1042 — Login with valid credentials shows welcome`.

Steps: tap username → type username → tap password → type password → tap Login → assert welcome text.

This is a critical-path banking flow (auth), which is exactly where the §8.8 risk-register
controls (human-confirm, never-heal classes) bite hardest — so the contrast between options that
carry those controls and those that don't is visible in the artifacts themselves.

## Grounding

The `TestCaseIR` / `Step` / `Locator` / `Assertion` record shapes are faithful to
`docs/research/mobile-test-automation-brainstorm.md:199-241`. The `LocatorCandidate` manifest and
the static-gate / `codeCommit` pinning are faithful to `docs/research/blueprint-revision-v2.md:33-105`.
The O3 runtime extensions (per-step timeout/sync, `healPolicy`, `irDigest`) are the three fields
the brainstorm §7.3 identifies as the gap between an authoring contract and an execution contract.

These are **illustrative mocks**, not committed repo schemas. They are designed to be read
side-by-side; numbers, hashes, and confidence values are placeholders.

## Directory layout

| Option | Path | Artifacts | Audit pin | Key contrast |
|---|---|---|---|---|
| O1 Spine | `o1-spine/` | IR + manifest + Java + report (4) | `codeCommit` (git SHA) | Discipline spread across 4 artifacts; static gate + code review enforce it |
| O2 Pure interpreter | `o2-pure-interpreter/` | IR + report (2) | `irDigest` (weak) | Fewest artifacts; controls that make O3 survivable are **absent** — the danger is in what's missing |
| O3 Hybrid | `o3-hybrid/` | IR + report (2) | `irDigest` | 2 artifacts, but the IR is fatter — all discipline pushed into the IR itself |
| O4 Perfecto AI | `o4-perfecto/` | Scriptless test + Appium JS export + vendor report (3) | vendor license + export SHA | Black-box internals; the export is the audit bridge |
| O5 Maestro | `o5-maestro/` | YAML flow + report (2) | YAML commit SHA | Committed DSL, deterministic runtime, no runtime self-heal; iOS sim-only caveat |
| O6 Meta-TestGen | `o6-meta-testgen/` | 3 candidates + filter results + accepted test + labels (7) | accepted-test commit SHA | Regenerate-and-filter; the accept/reject labels *are* the flywheel data |

## How to read them

Start with `o1-spine/` (the production north-star) and `o3-hybrid/` (the proposed POC) — they are
the two the ARB comparison lands on, and the contrast between them (4 light artifacts vs 2 heavy
ones; `codeCommit` vs `irDigest`; static gate vs heal-policy-in-IR) is the spine of the whole
decision. Then read `o2-pure-interpreter/` to see exactly which O3 controls are dropped, and why
O2 is compliance-fatal. Then `o4`/`o5`/`o6` for the vendor / OSS / assured-generation alternatives.
