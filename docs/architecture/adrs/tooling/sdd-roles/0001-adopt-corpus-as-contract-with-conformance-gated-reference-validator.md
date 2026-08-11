---
type: architecture
title: 'ADR 1. Adopt corpus-as-contract with a conformance-gated reference validator'
description: 'Adopt the golden corpus + CHK table as the normative, language-neutral contract; one Python reference validator; ports admitted only on identical-verdict conformance.'
tags: [architecture, adr]
---

# ADR 1. Adopt corpus-as-contract with a conformance-gated reference validator

## Status

Accepted
<!-- Accepted at the sdd-roles-kernel PLAN-OK gate, 2026-08-07 (owner;
F1–F4 ratified as drafted). First ADR of the tooling/sdd-roles series
(C4, sdd-roles-kernel.spec.md); this series is distinct from
application/mobile-test-automation (ADRs 0001–0017 there). -->

## Context

The role kernel must be enforceable **identically on three harnesses** (Claude Code, Cursor, Copilot — the platform-agnostic rider ratified at the Stage-1 gate 2026-08-07), and the only enforcement point available on all three is a deterministic offline CLI. That forces the question this ADR answers: **where does the normative truth of the contract live, and in how many implementations?**

Alternatives considered:

- **Reference-implementation-as-contract** — the Python validator's behavior is the truth. Couples the contract to one runtime; a port's divergence is undetectable because there is nothing language-neutral to diverge *from*.
- **Prose/spec-only contract** — the CHK table stays a markdown artifact with no executable twin. This is the D2-refuted failure class (prose degrades into vibes); completion claims become reviewable-only.
- **N native implementations day one** (Java for JVM workspaces, TypeScript for Node) — triples maintenance, guarantees drift, and violates this workspace's no-fork precedent (`tooling/coding-rules-skill/`: one canonical source, thin front-ends).
- **Per-harness contracts** — violates S2 outright; rejected without further analysis.

## Decision

We will make the committed **golden corpus + CHK table the normative, language-neutral contract** for the role kernel; commit the schema family as **closed JSON Schema draft 2020-12** files sharing one `schema_version`; ship **exactly one reference implementation** — Python ≥3.11, single dependency (`jsonschema`), CLIs `contract-lint` and `gate-wrap`, exit codes {0 pass, 1 usage/internal error, 2 validation failure}; admit **alternate-language implementations only after they pass the identical golden corpus with identical verdicts** (conformance-gated ports); and compute all pass/fail verdicts **from tool exit codes alone** (closed `GateOutcome`, no verdict field expressible).

- **Technical:** an executable contract is the only kind that holds on three harnesses at once; the anti-gaming self-test (CHK-SELF: path-independence + report-names-check-id) makes the corpus adversarially meaningful rather than decorative; closed schemas make forbidden states (agent-asserted completion, arm-membership on roles) *inexpressible* instead of reviewed-for; the corpus mirrors the already-proven o7 IR-conformance pattern (`interpreterVersion` pinned on a committed corpus).
- **Business:** one implementation to maintain until a real consumer demands a port (cost); items 2–6 unblock immediately on a stable v1 contract instead of waiting for multi-language parity (time to market); the no-fork precedent is already validated in this workspace, so the maintenance model is known (strategic consistency).

## Consequences

- **+** Ports are cheap to *trust*: corpus pass with identical verdicts = admission; the reference implementation holds no privileged authority (a workspace whose stack is Java loses nothing but must earn parity).
- **+** The contract cannot drift silently: CHK-DEFER makes unimplemented checks loud, CHK-SELF kills hardcoded-verdict gaming, and the registry↔corpus bijection makes a check-without-cases (or cases-without-check) a self-test failure.
- **+** Swapping or adding validators is a provider swap, not a rewrite — the corpus stays fixed while implementations come and go.
- **−** Python ≥3.11 becomes a dev-time requirement in any workspace that runs the gate, until that workspace lands a conformance-gated port. Accepted; sign-off recorded at PLAN-OK.
- **−** Every check change requires corpus cases before it exists — deliberate friction: contract changes *should* be visible, reviewable diffs (the anti-Groundhog-Day property).
- **−** The corpus grows with every CHK addition; bounded by the one-family-per-check-id rule.
- What the losing options offered and why we passed: implementation-as-contract would have shipped days earlier but made every future port unverifiable; N-native would have bought per-stack comfort at ~3× carry cost and assured divergence — both trade a permanent structural weakness for a one-time convenience.

## Compliance

Automated — the validator's own `selftest` subcommand is the fitness function, run as this build item's gate on a clean clone, offline: **CHK-SELF** (anti-gaming: temp-path copy + report-names-check-id), **CHK-DET** (double-run byte-identity), **CHK-NET** (socket-denying guard), **CHK-DEFER** (no silent green on unimplemented checks), **CHK-NEUTRAL** (harness-token grep over schemas + validator source), plus the registry↔corpus bijection assertion. Port admission is manual + automated: run the candidate against the full corpus, require identical verdicts, record the admission in `docs/architecture/log.md`.

## Notes

Author: sdd-spec plan stage (drafted at plan time per C4)
Approved by / date: owner, 2026-08-07 (PLAN-OK — F1–F4 ratified as drafted)
Superseded date: —
Last modified / by / what: 2026-08-07 / tasks stage / status Proposed → Accepted at PLAN-OK
