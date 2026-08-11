---
type: architecture
title: ADR 0001 — Route every model call through a single Invoke Models seam
description: 'Mandatory ADR from the stage-1 gate: Invoke Models as the sole model-call seam, realized as a Spring interface with configuration-selected implementations, with the Phase 1 → Phase 2 swap surface and IR-spine stability as its scope. This ADR plus fitness functions F1/F2 is the entire compensating control for Evolvability after the stage-3 gate declined the microkernel — build-time governance with no runtime seam behind it.'
tags: [architecture, mobile-test-automation, adr, arch-decide]
---

# ADR 0001. Route every model call through a single Invoke Models seam

## Status

Accepted

## Context

**Decision-context load (skill step 3):** these are the first ADRs for the
`mobile-test-automation` target — the recency window in `docs/architecture/adrs/`
is empty by fact, not omission. The workspace approval criteria
(`.arch/adrs/common/approval-criteria.md`) apply; this decision does not cross
their cost or security thresholds by itself.

**Forces.** Evolvability/replaceability was displaced from the top-3
characteristics at the stage-1 gate **on the explicit condition that structure
would protect it instead** (worksheet §7). The stage-3 gate then declined the
microkernel hybridization that would have made the protection architectural
(style decision §5). What remains is this ADR and two fitness functions — there
is no runtime seam behind them. The program's central premise depends on the
boundary holding: *"Phase 2 replaces the human driver with orchestration code.
Nothing else moves"* (`blueprint-revision-v2.md:55`). The reasoning provider
changes across the roadmap (Copilot → Orchestrator AI → future), and model
deprecation is named in the sources as outside the team's control.

**Alternatives considered.**

- **A single adapter seam** — one Spring interface, implementations selected by
  configuration (chosen).
- **Microkernel plug-in registry** — runtime-enforced boundary; declined at the
  stage-3 gate as machinery unwarranted by the one adapter the week-3 roadmap
  gate needs.
- **Direct gateway/SDK use per component** — fastest locally; each call site
  couples to the provider and the Phase 2 swap surface erodes silently.

**Qualification.** Nygard test: passes — fixes dependencies, interfaces, and a
construction technique in service of a driving characteristic. Third-law test:
passes — registry machinery vs contingent enforcement vs silent erosion are all
significant trade-offs. Timing: last responsible moment — the seam must exist
before the first component that calls a model is written; deferral cost now
exceeds decision risk.

### Trade-off matrix (options × factors, weighted for this system)

| Contextual factor (weight) | Single seam | Plug-in registry | Direct per-component calls |
|---|---|---|---|
| Phase 1 → 2 swap surface — the program premise (5) | **++** one adapter to replace | ++ same, plus runtime binding | −− swap touches every call site |
| Week-3 first-value gate / least machinery (5) | **++** an interface and a config flag | − registry built for one plug-in | ++ nothing to build |
| Evolvability protection strength (4) | + build-time rules, contingent on CI | **++** runtime-enforced | −− none |
| Pinning-field capture in one place (4) | **++** seam owns cache, screening, versions | ++ same | −− scattered, gaps likely |
| Simplicity for a small team (3) | **++** idiomatic Spring DI | − registry contracts to maintain | + familiar, until the swap |

## Decision

**We will route every model call — Phase 1 tooling and Phase 2 orchestration
alike — through one Invoke Models seam:** a Spring interface with
implementations selected by configuration, nothing selected at runtime.

**The seam ships with two named implementations across the roadmap, and the
cutover between them is a configuration change and nothing else**
*(refinement recorded at the gate, 2026-07-26)*:

1. **Phase 1 — Copilot-backed implementation.** Copilot chat / agent reasoning
   performs the generation; the adapter mediates the exchange — it assembles
   the prompt context from the versioned Git assets, hands it to the Copilot
   workflow, receives the result, and captures every pinning field the
   provider exposes (prompt version, tool and model identifiers as available).
2. **Phase 2 — direct gateway implementation.** Spring AI `ChatClient` against
   Orchestrator AI, with the full pinning set (prompt version, model and
   provider version) captured on every call.

Behind the seam and invisible outside it, in both implementations: the
provider/gateway mechanics, prompt assembly, the screening-library call at
egress, the response cache (keyed per ADR 0002), and pinning-field capture.
**The IR spine — `TestCaseIR`, `LocatorCandidate`, `ReplayReport` — is the
only vocabulary that crosses the seam in either direction**; no provider type,
gateway construct, or Copilot-specific shape leaves it, and no source-system
type enters it. Because the contract is provider-agnostic and exercised from
week one by the Copilot implementation, Phase 2 replaces an implementation
that already has a proven contract, not an interface designed on paper.

**Seam-vocabulary amendment (2026-07-31, ADR 0014 acceptance).** Two
ASH-Capture types join the crossing vocabulary: `ObservationPacket`
(screenshot + pruned tree + signature context, into the proposer) and
`CandidateActionSet` (≤K proposed candidate actions, out of the proposer; its
`locator` field reuses the existing `LocatorCandidate` type). Both are
committed, versioned schemas living in the ASH repo; no provider, gateway, or
Copilot-specific shape crosses with them, and the spine-side crossing
vocabulary is unchanged. Without this amendment the ASH proposer would either
violate this ADR's contract or smuggle a second contract past it — recorded
here so the seam stays the single, complete inventory of what may cross.

**Technical justification:**

- The Phase 1 → Phase 2 cutover becomes measurable: *files changed outside the
  adapter = 0* is the stage-1 evolvability measure, and it is only decidable if
  a single adapter exists.
- Every cross-cutting model-call obligation — screening, caching, version
  pinning — has exactly one enforcement point instead of N call sites, which is
  what makes fitness functions F1/F3/F6 assertable at all.
- IR-spine stability is the blueprint's own swap guarantee ("every module is
  swappable as long as the schemas hold"); this seam is where that guarantee is
  either kept or lost.

**Business justification:**

- **Strategic positioning:** the Phase 2 swap is the program's promise to its
  sponsors; this boundary is what makes it a config change instead of a rewrite.
- **Cost:** avoids the future rewrite and avoids the registry machinery the
  gate judged unwarranted — the cheap middle of the three options.
- **Time to market:** an interface plus Spring DI costs hours, not the weeks a
  plug-in framework would take from the week-3 gate.

## Consequences

- **The protection is contingent, and that is the accepted risk.** With the
  microkernel declined, nothing in the deployed system prevents a bypass. F1
  and F2 (below) are build-time dependency rules that live only in CI: if they
  are not built and maintained, Evolvability has no protection at all. This is
  recorded verbatim from the stage-1 worksheet §7 and stage-3 §5.
- The seam concentrates the gateway's availability and rate-limit profile at
  one choke point — already accepted and mitigated in ADR 0004 for the one
  cluster-B caller.
- **Flip condition:** a fourth source adapter or a second *concurrent*
  reasoning provider reopens the declined microkernel hybridization; the
  superseding ADR would cover both this decision and ADR 0005's style choice.
- What the losing options gave up: the registry's runtime enforcement
  (forfeited at the stage-3 gate, recorded there); direct calls' zero build
  cost (forfeited knowingly — it is the failure mode this ADR exists to
  prevent).

## Compliance

- **F1 (automated, CI-blocking, load-bearing):** ArchUnit rule — no type
  outside the Invoke Models adapter package references a provider SDK, gateway
  client, or Copilot-specific construct. Runs on every commit; a violation
  fails the build.
- **F2 (automated, CI-blocking, load-bearing):** ArchUnit rule — no
  source-system type crosses out of a source adapter; the IR is the only thing
  that leaves ingestion. (Filed here because IR-spine stability is this ADR's
  scope.)
- **Manual:** quarterly boundary review by the architecture owner; any F1/F2
  suppression or rule deletion requires a superseding ADR, not a code review.
- **Contract-parity check (automated, at Phase 2 cutover):** the golden-set
  parity run executes against both implementations of the seam; divergence
  beyond the certified thresholds blocks the cutover. This is the test that
  the "config change and nothing else" promise is real.

## Notes

**Prompt parity (recorded from the stage-5 P3 arbitration, 2026-07-27).**
Phase 1's agentic loop is invoked manually in Copilot chat **using the same
versioned production prompts from Git that the Phase 2 pipeline will use**.
The seam contract is therefore exercised with production prompt assets from
day one — Phase 2 replaces the driver of a proven exchange, not an interface
designed on paper. This fact overrode two automatic 9s on the P1→P2 cutover
seam during risk storming (risk report, P3 consensus log).

**Phase-1 pinning posture (recorded from stage-5 mitigation M12, 2026-07-27).**
Because of prompt parity, the Copilot-backed implementation captures **real**
values for prompt version and input/output hashes from day one. Fields the
Copilot workflow structurally cannot fill — the underlying model version and
sampling parameters — are recorded as **`UNPINNABLE_PHASE1`**, a distinct
enum value from `NOT_APPLICABLE`, so every flywheel-corpus entry carries a
queryable provenance class. The C4 required-real flip at cutover is
schema-enforced: the Phase 2 implementation rejects `UNPINNABLE_PHASE1`.

Author: arch-decide stage 4 (agent draft)
Date: 2026-07-26
Approved by / date: Rajnish Khatri / 2026-07-26
Superseded date: —
Last modified / by / what: 2026-07-31 / ADR 0014 acceptance (combined SPEC-OK
gate, owner) / seam-vocabulary amendment — `ObservationPacket` and
`CandidateActionSet` (ASH-Capture proposer I/O; locator reuses
`LocatorCandidate`) added to the crossing vocabulary; spine-side vocabulary
and decision unchanged
Prior modification: 2026-07-27 / stage-5 P3 mitigation / recorded the
prompt-parity fact and the Phase-1 pinning posture (`UNPINNABLE_PHASE1`
provenance class, schema-enforced flip) in Notes; decision unchanged
Prior modification: 2026-07-26 / gate refinement / named the two
implementations explicitly (Phase 1 Copilot chat/agent, Phase 2 direct
gateway calls) with config-only cutover and the contract-parity compliance
check; accepted
