---
type: architecture
title: ADR 0005 — Build one deployable, a modular monolith partitioned by cluster
description: 'Records the stage-3 style determination as decided at its gate: a plain modular monolith (the recommended microkernel hybridization was declined), one deployable Spring Boot runtime, three modules on the stage-1 cluster lines — conversion, validation-certification, evidence — with the blueprint''s five pipeline-stage names demoted to packages, pipeline kept as internal flow, and service-based named as the migration target. The forfeited evolvability structure and its compensating controls (ADR 0001, F1/F2) are in the Consequences.'
tags: [architecture, mobile-test-automation, adr, arch-decide]
---

# ADR 0005. Build one deployable: a modular monolith partitioned by cluster

## Status

Accepted

## Context

**Forces.** Stage 3 answered its four determinations: one architecture quantum
for both phases (the IR spine, the CA = 13 provenance contract, and the
certification→gateway edge all fail the coupling test for a split); default
synchronous communication with two async seams (ADR 0007); one primary
datastore (ADR 0006). The blueprint arrived with a style premise — *"the
runtime is a Spring Boot modular monolith"* — which the stage treated as a
candidate under test, not a decision. It survived, with one correction and one
gate variance.

**The correction:** the blueprint's five modules (ingestion, hierarchy-tool,
conversion, replay, certification) partition along *technical pipeline
stages* — the shape the modular-monolith style explicitly warns against, and
what pulls a monolith toward the layered Architecture Sinkhole. The stage-1
clusters — conversion, validation-certification, evidence — are
characteristic-shaped and split cleanly later.

**The variance:** the stage recommended hybridizing with a microkernel at the
source-adapter and model-provider seams; the gate **declined** it — a plug-in
registry is unwarranted machinery for the one adapter the week-3 gate needs,
and Spring DI supplies the Strategy seam for free.

**Alternatives considered** (full matrix in the style decision §5):

- **Microkernel hybridization** — won the analysis, lost at the gate; the only
  monolithic style the book rates for evolvability (3★).
- **Pipeline as macro style** — strongest isomorphism to the happy path; fails
  on the two bounded repair loops and the human escalation ("not for
  back-and-forth communication").
- **Service-based** — the strongest distributed candidate; loses today because
  Determination 1 found no quantum boundary and its winning rows (FT 4★,
  scalability) were eliminated at stage 1. **Named as the migration target.**
- **Event-driven, microservices, layered, space-based, SOA** — rejected on
  reproducibility/traceability damage, semantic coupling through the IR spine,
  technical partitioning, or no domain fit (microservices additionally failed
  the fashion check).

**Qualification.** Nygard test: passes by definition — this is the structure
decision. Third-law test: passes — every shortlisted option carries
significant trade-offs. Timing: implementation cannot start without a style;
last responsible moment reached.

### Trade-off matrix (condensed; top-3 characteristics as rows)

| Driving characteristic | Modular monolith | Microkernel hybrid | Service-based |
|---|---|---|---|
| **Reproducibility** | **+** one process, one clock, one transaction boundary | + same, provider isolated at a runtime seam | − verdict pinning needs distributed correlation |
| **Security & privacy** | **+** one trust boundary to audit | + same | − more surface, network-security fallacy paid |
| **Verifiability** | **+** gates run in-process, conjunction is one decision | + same | + workable at higher cost |
| Evolvability (driving, displaced) | − nothing structural at the two seams | **++** the registry *is* the seam | + service contracts |
| Cost + simplicity + week-3 gate | **++** | − registry machinery | −− distribution tax, `needs-input` on team maturity |

## Decision

**We will build the pipeline as a single architecture quantum: one deployable
Spring Boot modular monolith, partitioned into three modules on the stage-1
cluster lines** — `conversion` (10 components), `validation-certification`
(5 components), `evidence` (Preserve Provenance and its read model) — **with
the blueprint's five names retained as packages inside those modules, and
pipeline kept as the internal flow topology, not the macro style.** Phase 2
grows the `conversion` module in place; it does not spawn a second deployable.

**Technical justification:**

- It wins all three top-3 characteristic rows outright and costs almost
  nothing in the rows (scalability, elasticity, fault tolerance) that were
  eliminated at stage 1 — the weighted verdict, not the generic one.
- The module seams are the characteristic clusters, so a future extraction
  (service-based, if ever triggered) cuts along boundaries that already exist
  in the code and the schemas (ADR 0006).
- In-process gates and in-transaction lineage writes — the mechanics behind
  the verifiability and auditability measures — are trivial in one process and
  the hard case in any distributed option.

**Business justification:**

- **Time to market:** the least machinery that reaches the week-3 Excel-first
  gate; no service contracts, no registry, no broker topology beyond ADR 0007.
- **Cost:** one deployable, one primary store; the dominant costs stay where
  the sources put them (device minutes, tokens), not in infrastructure.
- **Strategic positioning:** keeps the Phase 2 premise ("nothing else moves")
  testable — F5 below — and preserves a named, priced migration path instead
  of a rewrite.

## Consequences

- **The declined microkernel's cost, stated plainly:** the source-adapter and
  model-provider seams have no runtime structure. Their entire protection is
  ADR 0001 plus fitness functions F1/F2 — build-time dependency rules that
  exist only if the team builds and maintains them. Evolvability was displaced
  from the top 3 *on the condition that structure would protect it*; that
  condition is now discharged by convention enforced in CI, and the stage-1
  worksheet records this consequence.
- Fault tolerance is unsupported by the style — accepted, since it was
  eliminated at stage 1; recoverability is delivered by checkpoint/resume
  (ADR 0007), not redundancy.
- **Flip condition:** a fourth source adapter or a second concurrent reasoning
  provider reopens the microkernel (jointly with ADR 0001); a residency ruling
  forcing evidence isolation reopens Determination 1 for cluster C only
  (ADR 0006).
- **Migration destination:** service-based; the first extraction candidates
  and their named triggers are Replay on Devices (if lab-side scaling ever
  becomes internal) and cluster C (if co-location becomes illegal rather than
  untidy).

## Compliance

- **Module-boundary rules (automated, CI-blocking):** ArchUnit — the three
  modules may be imported only via their published interface packages; no
  cross-module reach-in.
- **Deployment-unit check (automated):** CI asserts exactly one deployable
  artifact; a second fails the build until a superseding ADR exists.
- **F5 (automated, at Phase 2 cutover):** the cutover changes zero files in
  the `validation-certification` and `evidence` modules — the "nothing else
  moves" premise as a test.
- **F1/F2** govern the two convention-protected seams; they live in ADR 0001.
- **Cadence:** quarterly architecture review of module-boundary violation
  trends; a worsening trend is an extraction-trigger conversation, not a
  cleanup ticket.

## Notes

Author: arch-decide stage 4 (agent draft)
Date: 2026-07-26
Approved by / date: Rajnish Khatri / 2026-07-26
Superseded date: —
Last modified / by / what: —
