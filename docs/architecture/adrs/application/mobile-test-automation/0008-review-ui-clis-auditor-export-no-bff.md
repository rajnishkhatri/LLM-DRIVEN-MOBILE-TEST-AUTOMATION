---
type: architecture
title: ADR 0008 — Serve reviewers a web queue, engineers CLIs, and auditors an export — no BFF
description: 'The edge and access topology from stage-3 §6: the HITL review queue is the only Phase 1 web UI (authenticated, with every approval attributable to an identity), QA engineers use the two CLIs and the IDE with no web UI built for them, the auditor path is a versioned read-only export rather than a dashboard, and no BFF layer exists for one web client. Closes the unowned-capability finding by assigning the auditor export to Preserve Provenance.'
tags: [architecture, mobile-test-automation, adr, arch-decide]
---

# ADR 0008. Serve reviewers a web queue, engineers CLIs, and auditors an export — no BFF

## Status

Accepted

## Context

**Forces.** The component stage deliberately excluded UIs, so stage 3 §6
surfaced the edge topology before it fell through the stages. Four actor
classes do not share an access path: QA engineers (Phase 1's primary users)
work in the IDE and terminal; reviewers need an authenticated queue where
every approval, override, and correction is attributable to an identity
(stage-1 auditability); auditors must reconstruct "from stored evidence alone,
**without access to the running system**" — a measure a dashboard over the
live database cannot satisfy; the delivery lead needs a read-only metrics
view. Stage 3 also found a gap: **no component owned the auditor export
path.**

**Alternatives considered.**

- **Per-actor paths: review-queue UI + CLIs + versioned export, one internal
  API, no BFF** (chosen).
- **One web portal for everyone** — builds Phase 1 UI the engineers don't
  need (their interface is the IDE — the reason the week-3 gate is reachable),
  and still fails the auditor measure.
- **Auditor dashboard instead of export** — fails the measure by definition:
  it *is* access to the running system.
- **BFF layer** — justified by multiple device classes; there is exactly one
  web client here.

**Qualification.** Nygard test: passes — interfaces (how the system is
accessed) and two driving characteristics (auditability, security). Third-law
test: passes — each option trades build cost against the auditability measure.
Timing: the review UI is the one Phase 1 UI and gates the HITL workflow; last
responsible moment reached.

### Trade-off matrix

| Contextual factor (weight) | Per-actor paths (chosen) | One portal | Auditor dashboard | + BFF |
|---|---|---|---|---|
| Auditor measure — reconstruction w/o system access (5) | **++** export satisfies it by construction | −− | −− | n/a |
| Phase 1 build cost / week-3 gate (5) | **++** one UI, and only the one that must exist | −− three UIs | + | − extra layer |
| Attribution of human decisions (4) | **++** one authenticated app, purpose-built | + | n/a | + |
| Engineer workflow fit (3) | **++** IDE + CLIs, zero context switch | − portal detour | n/a | n/a |
| Future multi-client flexibility (1) | − none reserved | + | n/a | ++ |

## Decision

**We will expose one authenticated internal API serving exactly two web
surfaces — the HITL review queue (the only Phase 1 UI, with authenticated
identity, authorization, and attribution of every approval, override, and
correction) and the read-only metrics dashboard over the Preserve Provenance
read model. The two CLIs (ingestion, hierarchy tool) speak to the runtime
directly. The auditor path is a versioned, read-only export owned by Preserve
Provenance — closing the unowned-capability finding — and no BFF layer is
built.**

**Technical justification:**

- Preserve Provenance is cluster C, the system of record with the append-only
  contract; the export is a projection of what it already owns, so assigning
  ownership there adds a responsibility without adding a dependency edge.
- The export satisfies the auditability measure *by construction*: what the
  auditor receives is stored evidence, decoupled from the runtime's
  availability and access control surface.
- One web client means the internal API can serve it directly; a BFF would be
  a layer with exactly one consumer.

**Business justification:**

- **Time to market:** Phase 1 ships one UI instead of three — a large part of
  why the week-3 gate is reachable at all.
- **Strategic positioning:** handing an auditor a self-contained export is a
  materially stronger regulatory posture than provisioning them a login.
- **User satisfaction:** engineers keep their IDE workflow; reviewers get a
  purpose-built queue rather than a corner of a portal.

## Consequences

- **Preserve Provenance's role grows** (export responsibility). Its stage-2
  role entry should be annotated on acceptance of this ADR — the growth is a
  projection over existing data, not a new write path, so it does not disturb
  the CA = 13 write contract. If export demands ever diverge (formats,
  regulators, cadence), re-extracting an export component is the recorded
  growth trigger.
- The export format becomes a versioned contract with the same discipline as
  any other (a format change is a contract change, not a report tweak).
- The review UI needs authentication and authorization from day one — there
  is no anonymous phase; this is what makes attribution complete rather than
  retrofitted.
- Forfeited: the portal's single-front-door story and the BFF's multi-client
  headroom — both reserved machinery for demand that does not exist.

## Compliance

- **Attribution completeness (automated, data-level):** every approval,
  override, and correction row carries an authenticated identity; sampled
  nightly, zero anonymous rows tolerated.
- **Reconstruction drill (manual, semi-annual):** perform the audit
  reconstruction exercise from an export alone, on a machine with no runtime
  access — the auditor measure as a rehearsal.
- **Structural (automated):** CI asserts no second web client and no BFF
  module exist; adding either requires a superseding ADR.
- **Security-review queue entry (per ADR 0010):** this ADR mandates identity,
  authentication, and authorization for the review UI and defines the auditor
  trust boundary — two triggers under the workspace criteria. Under ADR 0010
  the review runs as parallel work rather than an acceptance blocker, so the
  enforceable obligation is the **queue entry naming both triggers**, drained
  before the target's first production release.

## Notes

Author: arch-decide stage 4 (agent draft)
Date: 2026-07-26
Approved by / date: Rajnish Khatri / 2026-07-26 (architecture gate).
**Security review queued as parallel work under ADR 0010, not outstanding as a
defect.** The stage-4 review flagged that this ADR was Accepted despite two
security triggers while ADR 0006 was held at Proposed on the same criteria; the
gate resolved that inconsistency by scoping security review to a parallel,
non-blocking track for this target. This acceptance stands, and a review
finding would arrive as a revision or a superseding ADR.
Superseded date: —
Last modified / by / what: 2026-07-26 / arch-decide gate / security-approval
note restated as an ADR 0010 queue entry; status unchanged throughout
