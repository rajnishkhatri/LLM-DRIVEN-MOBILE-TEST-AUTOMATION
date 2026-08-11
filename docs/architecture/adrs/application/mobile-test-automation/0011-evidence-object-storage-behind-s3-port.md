---
type: architecture
title: ADR 0011 — Access evidence object storage through an S3-compatible port; bind production by the platform probe
description: 'The object-storage decision spun out of stage-5 risk mitigation M22 (the P2 register''s automatic 9), with M23''s backup/restore coherence rules as its own section: all evidence-artifact access goes through a thin S3-compatible port; dev/CI run containerized MinIO; the production binding is decided by the week-0 platform probe — an internal S3-compatible platform service if one exists (durability, backup, and on-call inherited from the team that already operates it), otherwise self-operated MinIO with object-lock immutability and a named durability/backup design. Restore coherence is governed by the restore-ordering invariant (object store restores to a point at or after the primary store''s) and a post-restore custody reconcile, with object immutability as the invariant''s precondition. Proposed — acceptance blocked on the probe answer; last responsible moment before the first real evidence artifact lands (~week 2, device gate).'
tags: [architecture, mobile-test-automation, adr, arch-decide]
---

# ADR 0011. Access evidence object storage through an S3-compatible port; bind production by the platform probe

## Status

**Proposed** — acceptance blocked on one named input: the **week-0 platform
probe** (does the bank already operate an internal S3-compatible object-storage
service?). Last responsible moment: **before the first real evidence artifact
lands** (~week 2, when the device gate first pulls Smart Reporting artifacts).
If the probe has not answered by then, the self-operated branch is taken by
default rather than letting a filesystem stopgap leak into the retention
design — the default is recorded here so silence has a defined outcome.

## Context

**Forces.** ADR 0006 decided the topology — device artifacts (video, page
source, screenshots, network captures; large, binary, PII-bearing) live in
object storage with the primary store holding references, classification, and
retention dates, never payloads — and the on-premises residency answer made
that storage **self-operated**, which ADR 0006 recorded as a weakened cost
claim but did not resolve. Stage-5 risk storming priced the unresolved half:
the P2 register's one *automatic 9* (M22 — technology unchosen, no
durability/backup design, for the store holding regulated evidence) and a
3×3 = 9 on cross-store restore incoherence (M23 — PostgreSQL and the object
store restoring to different points would strand lineage references). The
accepted M22 mitigation named this ADR as the vehicle and the week-0 platform
probe as its first input; the accepted M23 mitigation routes its two
backup/restore rules into this ADR's own section.

**The probe shapes the decision but does not block the seam.** Nearly every
credible candidate — internal platform services, MinIO, Ceph, appliances —
speaks the S3 API. That makes the *access path* decidable now and the
*production binding* decidable at the probe: the code binds to a thin
S3-compatible port either way, and switching binding is an
endpoint/credentials change, not a rewrite. Dev/CI run containerized MinIO
behind the same port from task zero (the D1 analog for the primary store).

**Alternatives considered.**

- **S3 port + probe-decided binding: platform service first, self-operated
  MinIO otherwise** (chosen).
- **Commit to self-operated MinIO now** — decides early what the probe may
  decide better; if an internal platform service exists, the team takes on
  durability, backup, and on-call that another team already carries.
  One honest flag either way: MinIO's AGPL license needs the bank's
  OSS-catalog check — a probe rider; if it fails, the self-operated branch
  re-opens on candidates (SeaweedFS, Garage, an appliance), not on the port.
- **Ceph** — mature and durable, but a distributed storage system with its
  own operational discipline; grossly oversized for one pipeline's evidence
  store, and weeks of hardening the schedule does not have.
- **Storage appliance** — strong durability with vendor support, but a
  procurement cycle stands between week 0 and the week-2 landing; viable
  later behind the same port, not a way to start.
- **Filesystem/NFS stopgap** — fastest to nothing: no object immutability, no
  retention machinery, no S3 semantics; the spine spec already lists "a
  filesystem stopgap would leak into the retention design" as a known break
  risk. Rejected outright.

**Qualification.** Nygard test: passes — dependencies, construction, and two
top-3 characteristics (security & privacy's retention machinery,
reproducibility's evidence custody). Third-law test: passes — every option
trades durability ownership, schedule, or operational burden. Timing: the
port and interim are needed now; the binding has a genuinely missing input —
hence Proposed with the probe as a named blocker and a recorded default,
mirroring the ADR 0006 pattern.

### Trade-off matrix

| Contextual factor (weight) | S3 port + probe binding | Commit MinIO now | Ceph | Appliance | Filesystem stopgap |
|---|---|---|---|---|---|
| Durability/backup ownership for regulated evidence (5) | **++** inherited from platform team if service exists; named design otherwise | − all on this team | + mature but self-run | ++ vendor-backed | −− none |
| Immutability + retention machinery (auditability) (5) | **++** object lock / versioning either branch | + object lock | + | ++ | −− |
| First real artifact lands ~week 2 (4) | **++** dev MinIO now, binding by probe | ++ | −− weeks of hardening | −− procurement | ++ |
| Operational burden / on-call (4) | **+** platform branch ++, self-op branch − | − new on-call | −− | + | − quiet until it corrupts |
| Cutover cost between branches (3) | **++** endpoint/credentials change | ++ same API | + | + | −− retention redesign |
| Cost (3) | **+** platform amortized; MinIO cheap + ops time | − ops time | −− | −− capex | ++ then very − |

## Decision

**We will access evidence object storage exclusively through a thin
S3-compatible storage port; dev and CI run containerized MinIO behind that
port from task zero; the production binding is decided by the week-0 platform
probe — the bank's internal S3-compatible platform service if one exists,
otherwise self-operated MinIO with object-lock immutability and a named
durability/backup design; and no evidence artifact is ever written outside
the port.**

The why front and center: the port is the part that is safe to decide now —
it makes the binding swappable for the price of an interface — while the
binding is the part the probe can decide better than we can, because an
existing platform service carries durability, backup, and on-call that this
team would otherwise have to build and staff. Deferring the *binding* to the
probe costs days; deferring the *port* would let a filesystem stopgap set the
retention design by accident.

**Technical justification:**

- Every candidate speaks S3, so one port covers both probe outcomes; cutover
  is endpoint + credentials, proven daily by dev/CI running MinIO against the
  same interface.
- Object immutability (write-once, object lock) is a *precondition* of the
  M23 restore-ordering invariant — an object store restored "ahead" of
  PostgreSQL holds only harmless orphans **only if** objects are never
  overwritten. The port's contract states it; both branches provide it.
- The classification + retention-date surface (ADR 0006) maps directly onto
  object metadata + lifecycle rules in either branch.

**Business justification:**

- **Cost:** the platform branch reuses storage the bank already amortizes and
  staffs; the self-operated branch is commodity hardware plus MinIO — the
  expensive part is on-call, which the probe exists to avoid.
- **Time to market:** dev/CI are unblocked now; the week-2 landing deadline
  is met on either branch because the binding is a configuration change.
- **Strategic positioning:** regulated evidence on infrastructure with a
  named durability and backup owner is the difference between an audit answer
  and an audit finding.

### Backup/restore coherence (the M23 section)

1. **Restore-ordering invariant:** restore the object store to a point **at
   or after** the primary store's restore point — never behind it. Sound
   because the spine spec mandates the write order (artifact lands first,
   lineage row second), so PostgreSQL only ever references objects that
   already exist; an "ahead" object store holds only orphans, never dangling
   references. Precondition: object immutability, stated above.
2. **Post-restore custody reconcile:** after any restore, re-run the custody
   check (CF1 machinery) over restored lineage — every reference must resolve
   and digest-match (M9/M15 digests); failures quarantine loudly (the M10a
   posture), never silently pass.
3. If the probe returns a platform service, the ordering rule becomes a
   written agreement with that team's backup regime rather than a runbook
   this team executes.

### Erasure under immutability (the M39 amendment, 2026-07-27)

**The collision this ADR created, and the mechanism that resolves it.** This ADR
mandates write-once objects and ADR 0012 mandates an append-only chained lineage;
P1 register entry P1-19 asks what happens when PII is discovered in evidence
*after* it has landed. **Immutability and erasure are directly opposed, and both
are mandatory** — no procedure resolves that, so a mechanism is required.

1. **Envelope encryption with a per-conversion key.** Evidence objects are
   written encrypted under a data key held in the secrets store the M33
   controls-baseline read names (the same store M34's credential indirection
   binds to). The object remains immutable and stored.
2. **Erasure is key destruction (crypto-shredding).** Destroying the key renders
   every object under it permanently unreadable while altering no object and no
   lineage row. It is the one construction that satisfies immutability and
   erasure simultaneously.
3. **Key destruction marks affected certification verdicts `EVIDENCE_DESTROYED`.**
   This is the consequence that must not be left implicit: erasure destroys the
   readability that custody-before-certify (CF1) and fidelity re-derivation (CF7)
   both depend on, so an erased verdict is no longer reconstructible. The system
   records that explicitly per verdict rather than leaving a verdict looking valid
   over unreadable backing. **You cannot both erase and retain audit
   reconstructibility; the design states which was given up, and when, and by
   which principal.**
4. **Break-glass procedure for what crypto-shredding cannot reach** — PII in the
   lineage rows themselves, which are chained and append-only under ADR 0012.
   This is an incident path involving the security function, not a routine
   capability, and any exercise of it is itself a recorded, attributable event.
5. **Timing.** The binding constraint is not "before any evidence lands" but
   **before the first evidence that must survive to the audit horizon**. Spine
   gate evidence is proof-of-concept output, so: spine object-lock retention is
   kept short and spine evidence stays plainly deletable; envelope encryption and
   key destruction are built before the first audit-retained artifact (weeks
   3–8). Recorded honestly: retrofitting encryption onto immutable objects has no
   cheap path — there is no in-place re-encryption and the plaintext originals
   cannot be deleted — so this timing is a deliberate bet on the spine's evidence
   being disposable, and it fails if spine evidence is later reclassified as
   retained.

## Consequences

- **The probe branches are asymmetric and the cost difference is real.**
  Platform branch: the risk collapses to integration-level and the M22
  automatic 9 dissolves onto a team already carrying it. Self-operated
  branch: this team acquires storage on-call, capacity planning, and a backup
  regime for regulated evidence — the full weight ADR 0006 flagged when
  on-premises made storage self-operated. The port makes the branches cheap
  to swap; it does not make them equally expensive to live in.
- **Dev/CI MinIO is not evidence-grade, and nothing in the spec gate says
  so.** M22's recorded trade-off: M19's corpus-class honesty covers *input*
  grade, not *storage* grade — the week-3 gate could pass on a dev-grade
  store. The guard is one plan-level line (carried to plan derivation): the
  production binding must be live before the first real evidence artifact
  lands.
- MinIO's AGPL license is an unverified assumption on the self-operated
  branch — the OSS-catalog check rides the probe; a failure re-opens the
  candidate list, not the port.
- Losing options' trade-offs: committing to MinIO now would have saved one
  decision round-trip at the risk of duplicating a platform service; Ceph
  and an appliance buy durability the schedule cannot pay for yet — the
  appliance stays viable *later* behind the same port; the filesystem
  stopgap's speed is a loan against the retention design.
- Imposes on future work: no evidence write outside the port; no mutable
  overwrite of a landed artifact; restores follow the ordering invariant and
  end with a custody reconcile.

## Compliance

- **Port-only access (automated, CI-blocking):** an ArchUnit-style dependency
  rule — no type outside the storage-port package references an S3/storage
  SDK or filesystem API for evidence paths. Same construction as F1/F2;
  arch-validate must inventory it alongside the F-series.
- **Immutability assertion (automated, startup/ops check):** evidence buckets
  verified write-once (object lock / versioning) at deployment; a mutable
  evidence bucket fails the check before any artifact lands.
- **Restore drill (manual, quarterly, joins ADR 0006's retention drill):**
  restore both stores honoring the ordering invariant in a staging copy, run
  the custody reconcile, prove zero dangling references — the coherence claim
  as an exercise, not an assumption.
- **Security-review queue entry (per ADR 0010):** this ADR stores PII-bearing
  regulated evidence; the review runs as parallel work, queue drained before
  first production release.
- **Anchor-bucket immutability (automated, deployment check; added by ADR 0012):**
  the write-once assertion covers the lineage chain-anchor bucket explicitly, not
  only evidence buckets — ADR 0012's tamper-evidence is exactly as strong as this
  check.
- **Erasure integrity (automated, per key destruction; added by the M39
  amendment):** destroying a data key marks every certification verdict
  referencing objects under that key as `EVIDENCE_DESTROYED`, recorded with the
  destroying principal; a key destruction that leaves a referencing verdict
  unmarked fails the check. Rehearsed in the quarterly drill below.
- **Restore drill (extended):** the drill also verifies ADR 0012's lineage chains
  against surviving anchors, and exercises one crypto-shred against a staging
  copy to prove the verdict-marking path works before it is needed in an
  incident.

## Notes

Author: arch-decide, invoked from stage-5 arch-risk (P2 mitigation M22/M23)
Date: 2026-07-27
Approved by / date: — (Proposed; acceptance blocked on the week-0 platform
probe, default branch recorded in Status). **Reviewed at gate 2026-07-27 by
Rajnish Khatri — confirmed as filed:** Proposed with the probe as the named
blocker and the self-operated default standing at the last responsible
moment. The probe answer (either branch) flips this to Accepted with the
binding named.
Superseded date: —
Last modified / by / what: 2026-07-27 / stage-5 arch-risk (P1 mitigation M39,
accepted by owner at the gate; **amendment ratified 2026-07-27 at the combined
gate** alongside ADR 0012/0013 acceptance and the spec's post-P1-mitigation
re-sign-off — the ADR itself stays Proposed pending the platform probe) /
erasure-under-immutability section added —
envelope encryption with per-conversion keys, crypto-shredding as the erasure
mechanism, verdicts marked `EVIDENCE_DESTROYED` on key destruction, a break-glass
path for lineage-resident PII, and the timing rule (build before the first
audit-retained artifact, keep spine object-lock retention short). Compliance
gained the anchor-bucket immutability check (ADR 0012), the erasure-integrity
check, and a restore-drill extension. Status unchanged (Proposed, still blocked
only on the week-0 platform probe) — the amendment adds a mechanism the decision
did not previously have; it does not alter the binding question.
