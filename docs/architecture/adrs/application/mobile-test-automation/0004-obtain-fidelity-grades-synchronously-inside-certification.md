---
type: architecture
title: ADR 0004 — Obtain fidelity grades synchronously inside certification
description: 'Resolves the entanglement created when the stage-2 gate merged the semantic-fidelity judge into Certify Conversion: certification calls the Orchestrator AI gateway synchronously. Accepted at one quantum because no quantum collapse occurs and certification is not latency-sensitive; the live cost — gateway availability, rate limits, per-verdict token spend — is named and mitigated by treating grades as recorded evidence that are never re-derived on retry. One expiry condition: cluster B extraction changes this edge first.'
tags: [architecture, mobile-test-automation, adr, arch-decide]
---

# ADR 0004. Obtain fidelity grades synchronously inside certification

## Status

Accepted

## Context

**Forces.** The stage-2 gate merged the semantic-fidelity judge into Certify
Conversion **against recommendation**, with the consequence recorded rather
than absorbed: the certification gate — a cluster-B component that must issue
reproducible verdicts — now makes a nondeterministic model call through the
Orchestrator AI gateway. Stage 1 recorded the resulting tension pair
(Verifiability ↔ Reproducibility, worksheet §8); stage 2 escalated the
question: **how does certification obtain a fidelity grade without cluster B
inheriting cluster A's characteristics?** Stage 3 resolved it in passing
(style decision §4) once Determination 1 answered *one quantum*, and handed
the record here; this ADR carries the full trade-off analysis behind that
resolution rather than making the call afresh.

**Alternatives considered.**

- **Synchronous call at one quantum, grade treated as recorded evidence**
  (chosen).
- **Asynchronous grade request** — certification enqueues, resumes on the
  grade's arrival; decouples availability but adds a third async seam and a
  wait state to a gate that runs after the waiting is already over.
- **Grade in cluster A, certification consumes a recorded result** — restores
  the model-free gate; reintroduces the separate-judge shape the human gate
  explicitly merged away, and adds a cross-module handshake for a result only
  certification uses.

**Qualification.** Nygard test: passes — dependencies and a non-functional
characteristic (reproducibility of verdicts). Third-law test: passes — all
three options carry significant trade-offs. Timing: certification is roadmap
week-6 work, but the seam shape affects the state machine now.

### Trade-off matrix

| Contextual factor (weight) | Sync at one quantum | Async grade | Grade in cluster A |
|---|---|---|---|
| Simplicity of the certification gate (5) | **++** one in-process sequence with one remote call | −− wait-state + resume in the gate | − cross-module handshake |
| Verdict reproducibility (5) | **+** grade recorded with calibration version, never re-derived | + same, more moving parts | + same |
| Isolation from gateway availability (3) | − live coupling, mitigated below | ++ decoupled | ++ decoupled |
| Latency of certification (1) | ○ irrelevant — runs after minutes of device runs | ○ | ○ |
| Respects the stage-2 gate's merge decision (3) | **++** | + | −− un-merges it by the back door |

## Decision

**We will let Certify Conversion call Invoke Models synchronously for the
fidelity grade, and treat every grade as recorded evidence:** the grade is
written to lineage with the judge's calibration version pinned; a grade
obtained earlier remains valid; **certification never re-grades on retry**;
and a gateway outage delays new grades without invalidating existing ones.

**Technical justification:**

- The *quantum-collapse* cost of Dynamic Quantum Entanglement only
  materializes across a quantum boundary. At one quantum (stage 3,
  Determination 1) cluster B already shares deployment, datastore, and
  lifecycle with cluster A — the sync call changes no deployment property.
- Certification is not latency-sensitive: it runs after K device runs that
  took minutes; a gateway call adds nothing perceptible.
- The recorded-evidence discipline is what squares a nondeterministic grader
  with a reproducible verdict: the verdict cites a pinned, immutable grade
  rather than re-deriving one.

**Business justification:**

- **Cost:** the per-verdict token spend is bounded (one grade per
  certification, never repeated on retry); both alternatives spend the same
  tokens plus additional machinery.
- **Time to market:** no third queue, no cross-module callback protocol before
  the certification milestone.
- **User satisfaction:** reviewers see a gate that either has a grade or says
  why not — no half-graded limbo states.

## Consequences

- **Live coupling, paid from day one** (stated, not hidden): certification now
  carries the gateway's availability and rate-limit profile and a per-verdict
  token cost, where previously only conversion did. The mitigation above is in
  force immediately, not contingently.
- The judge's calibration state becomes a *precondition* of certification —
  the Timing connascence recorded in stage 2 §9. Compliance rule F7 below is
  its enforcement.
- **Expiry condition:** if cluster B is ever extracted (the Determination-1
  revisit trigger), this edge is the first thing that must change — to an
  async grade, or to grading in cluster A with certification consuming a
  recorded result. The superseding ADR should start from this one's
  alternatives table.

## Compliance

- **F7 (automated, release-blocking):** certification refuses to issue a
  verdict when the judge's calibration record is absent or older than the
  current gateway model version.
- **F6 (automated, data-level) — owned by ADR 0002, asserted here for the
  calibration angle:** every verdict's lineage row carries the judge's
  calibration version as a pinning field.
- **Manual (on every gateway model change):** recalibration of the judge
  (TPR/TNR > 90% on the calibration set) before certification resumes — the
  operational half of F7.

## Notes

Author: arch-decide stage 4 (agent draft)
Date: 2026-07-26
Approved by / date: Rajnish Khatri / 2026-07-26
Superseded date: —
Last modified / by / what: —
