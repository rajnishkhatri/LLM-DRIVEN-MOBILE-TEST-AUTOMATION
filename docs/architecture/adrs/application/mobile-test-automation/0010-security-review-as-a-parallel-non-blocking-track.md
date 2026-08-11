---
type: architecture
title: ADR 0010 — Run security review as a parallel track that can revise but not block
description: 'Target-scoped override of the workspace ADR approval criteria for mobile-test-automation: an ADR triggering a security threshold may be Accepted at the architecture gate without the security owner''s prior sign-off, with the review queued as parallel work whose output is a revision or a superseding ADR rather than a retroactive status hold. Records that the security-owner role is held by the architecture owner for Phase 1, and states plainly that the resulting control is neither independent nor blocking — a named input to stage-5 risk analysis.'
tags: [architecture, mobile-test-automation, adr, arch-decide, governance]
---

# ADR 0010. Run security review as a parallel track that can revise but not block

## Status

Accepted

## Context

**Why this ADR exists.** The stage-4 critical review found that three of the
nine ADRs written for this target trigger the workspace security threshold —
0006 (PII, retention, trust boundaries), 0008 (identity, authentication,
authorization, and the auditor trust boundary), and 0009 (PII, secrets, and
three trust boundaries) — and that the three were resolved inconsistently:
0006 held at Proposed, 0008 Accepted with an outstanding note, 0009 initially
drafted as Proposed and then Accepted at the gate. Same policy, three
outcomes.

**Forces.** The workspace criteria are unambiguous
(`.arch/adrs/common/approval-criteria.md`): *"require the designated security
owner's approval for any change involving payment data, PII,
identity/authentication/authorization, secrets, trust boundaries, encryption
requirements, tenant isolation, or relaxation of an existing control."* Against
that sit three facts. First, **no separate security owner was designated** when
the nine ADRs were written, so under a strict reading every ADR touching a
trust boundary was permanently unapprovable — an unfillable requirement, which
is why practice diverged from policy rather than the reverse. Second, Phase 1's
week-3 gate does not survive a serially blocking review of three foundational
ADRs. Third, security & privacy is a **top-3 characteristic** here, so the
answer cannot be to drop the review.

A policy that practice ignores is worse than either a stricter policy or a
looser one, because it produces an audit trail that misrepresents what the
organization actually does. The gap must close from one side or the other.

**Alternatives considered.**

- **Parallel non-blocking review, target-scoped** (chosen).
- **Strict serial blocking** — the policy as written. Correct on the merits and
  unaffordable in Phase 1; it would hold three foundational ADRs, and with the
  role dual-hatted it would block on a signature the same person supplies
  anyway, purchasing delay without independence.
- **Leave the divergence in place** — three ADRs, three handlings, an
  outstanding note that nothing retires. Rejected: it is the current state, and
  it is the one option that guarantees the inconsistency reaches arch-validate.
- **Blanket exemption for this target** — removes the review rather than
  rescheduling it. Rejected: it forfeits the finding stream entirely, which is
  the one property worth keeping.
- **Amend the workspace criteria for all targets** — over-reaches. The
  justification here is local (unfilled role, Phase 1 timeline), so the override
  should be local too.

**Qualification.** Nygard test: passes on governance rather than structure —
it changes who must approve decisions affecting a top-3 characteristic, and
the ADR set's own status semantics. Third-law test: passes — speed and
unblocking are bought with independence and veto authority, and both sides are
material. Timing: the last responsible moment is now, because three ADR
statuses hang on it and stage 5 must score the result.

### Trade-off matrix

| Contextual factor (weight) | Parallel non-blocking (chosen) | Strict serial blocking | Leave divergence | Blanket exemption |
|---|---|---|---|---|
| Security findings still produced (5) | **++** review happens, output is a revision | ++ | + inconsistently | −− none |
| Review can stop a bad decision (5) | −− cannot block | **++** | − sometimes | −− |
| Reviewer independent of decider (4) | −− dual-hatted, see Consequences | − dual-hatted anyway | − | n/a |
| Phase 1 week-3 gate reachable (4) | **++** nothing held | −− three ADRs held | + | ++ |
| Policy describes actual practice (4) | **++** exactly | − aspirational | −− actively false | + |
| Reversible when a real owner exists (3) | **++** flip condition named | n/a | − | − |

## Decision

**For the mobile-test-automation target only, an ADR that triggers a security
threshold under the workspace approval criteria may be Accepted at the
architecture gate without the security owner's prior sign-off. The security
review is queued as parallel work and tracked to completion; its output is a
revision to the ADR or a superseding ADR, never a retroactive hold on a status
already granted.**

Three things follow from that and are decided here:

- **The security-owner role for this target is held by the architecture owner
  (Rajnish Khatri) for Phase 1**, until a separate owner is designated. It is
  recorded as dual-hatted rather than vacant, because a named non-independent
  reviewer produces findings and a vacant role produces nothing.
- **The workspace criteria are not modified.**
  `.arch/adrs/common/approval-criteria.md` stands as written for every other
  target. This ADR is a scoped override and states its own precedence: where
  the two conflict, this ADR governs artifacts under
  `docs/architecture/**/mobile-test-automation/`, and only those.
- **The three affected ADRs resolve as follows.** 0008 and 0009 keep their
  Accepted status, and their outstanding-approval notes are restated as queued
  parallel reviews rather than defects. 0006's security half is discharged,
  leaving the **residency input as its only remaining acceptance blocker**.

**Technical justification:**

- The review's value is its findings, not its veto. A finding delivered in week
  five as a revision reaches the code at the same point in the build as a
  finding delivered in week two as a block, because none of these three ADRs
  reaches implementation before then.
- The decisions most in need of security scrutiny here — ADR 0009's screening
  library and ADR 0006's PII retention — already carry automated, release-
  blocking compliance (F3's two halves, the red-team corpus regression, the
  secret/PII egress detector, the retention drill). Those gates do not depend
  on a signature and cannot be bypassed by an unreviewed ADR.

**Business justification:**

- **Time to market:** three foundational ADRs unblock, and the week-3 Phase 1
  gate stays reachable.
- **Cost:** avoids purchasing delay for a signature the same person supplies —
  the strict reading's cost is real and its benefit, under a dual-hatted role,
  is close to zero.
- **Strategic positioning:** a written policy that matches observed practice
  survives an audit; one that does not is a finding on its own, independent of
  whether the underlying decisions were sound.

## Consequences

- **The security control is now neither independent nor blocking, and this is
  the honest cost.** An approval control derives its force from three
  properties: the reviewer is independent of the decision-maker, the review can
  stop the decision, and it happens in time to matter. This ADR removes the
  second, and the dual-hatted role removes the first. **Only timeliness and
  visibility survive.** The review still runs and still produces findings — it
  simply cannot say no. For a **top-3** characteristic that is a material
  weakening, and it is recorded here rather than framed as a process
  improvement.
- **This is a named input to stage 5 (arch-risk)** and should be scored there,
  not treated as settled by this ADR. The residual risk is a security finding
  that arrives after the decision it would have prevented has been built on.
- **The parallel queue must actually exist**, or this ADR is a blanket
  exemption wearing different words. The Compliance section makes the queue the
  enforceable part; without it, the distinction between "deferred" and
  "skipped" is rhetorical.
- ADR 0006 is reduced to a single blocker (residency), which makes its status
  legible: it is waiting on an input, not on a signature.
- **Flip conditions**, any one of which reopens this decision: a separate
  security owner is designated (at which point independence is recoverable and
  blocking authority should be reconsidered); the system begins handling
  production PII rather than test-derived data; or a parallel review produces a
  finding that would have blocked an ADR already built on — the failure mode
  this ADR accepts, made real.

## Compliance

- **Security-review queue entry (manual, at every acceptance):** any ADR
  accepted while triggering a criteria threshold gets a queue entry at the
  moment of acceptance, naming the specific trigger. **Zero ADRs accepted with
  a trigger and no entry** — this is the assertion that separates deferral from
  exemption.
- **Queue drain before release (manual, release-blocking):** no security-review
  entry may be open at the target's first production release. Deferral within
  Phase 1 is the concession; deferral past it is not.
- **Dual-hat reporting (manual, per iteration):** while the role remains
  dual-hatted, it is restated in the risk register every iteration. The
  intent is that it stays visible rather than becoming ambient.
- **Scope assertion (manual, at review):** this override is cited by any ADR
  relying on it. An ADR under a different target invoking it is a review
  failure.

### Prod-grade-data definition amendment (2026-08-01, ADR 0014 D4 routing)

ADR 0014 gated all discovery and probing on an environment attestation and reserved a `dataClass` field whose only defined behavior is a hard suspension: `PRODUCTION_DERIVED` refuses discovery until a superseding recorded decision under ADR 0010/D4 (0014:666-668; spec.md:313-316, EARS `d4-suspension`). ASH's whole safety posture is *environmental* (walkthrough:730) — the LLM drives an authenticated banking-app session on real devices (0014:74-77), and the injection blast radius is bounded not by the denylist (defence-in-depth only) but by the promise that the data the loop can reach is synthetic. But no ADR defined "prod-grade": ADR 0014 uses the adjective (0014:60-62) and deferred the definition as D4 (0014:666; routed to this ADR because 0010:147-148 already carries the matching flip trigger). This amendment supplies the predicate.

*It does not modify the workspace approval criteria, the parallel-non-blocking-track posture, the dual-hatted security-owner role, or the flip conditions already listed (0010:79-100, :145-150). It **sharpens one existing flip condition** — 0010:147-148's "production PII rather than test-derived data" — into a decidable predicate. The `dataClass` suspension is a **runtime discovery-execution** gate, a different object from 0010's non-blocking scope, which is the **ADR-approval gate** (0010:79-84); making a runtime gate decidable does not add a blocking gate to the approval process. Status stays Accepted.*

**The line: production-realistic-synthetic vs production-derived** — classed by the **provenance** of every value the discovery loop can read or commit, not by whether it *looks* real:

- **`SYNTHETIC` (production-realistic synthetic).** Every account, balance, name, IBAN, payee, PIN/OTP, and transaction visible in the environment is **generated or manually authored test data** that has never been derived, copied, seeded, masked, or subset from any production record. "Production-realistic" describes *format fidelity* only (a synthetic IBAN passes checksum validation) — it admits no production lineage. This is the class ASH's committed `capture-input-corpus` already requires (0014:645-646) and the walkthrough assumes throughout (walkthrough:730).
- **`PRODUCTION_DERIVED`.** Any value copied, masked, tokenized, subset, sampled, or otherwise *originated* from a production record — **including masked or de-identified production data**. Masking does not demote it: the PII flip (0010:147-148) is triggered by *handling production data*, not by whether it is currently readable. This is the class ADR 0014 suspends discovery on (0014:666-668).

**One provenance root — corpus AND environment, not corpus alone (load-bearing).** `dataClass=SYNTHETIC` holds only when **everything the loop can read or type** is synthetic. The `SYNTHETIC` provenance manifest MUST cover both the committed input corpus (0014:645-646) *and* the environment's resident/readable data under one committed origin assertion. This closes a live false-green: a `SYNTHETIC` corpus in a `PRODUCTION_DERIVED` environment would let the loop *read* real customer values off live screens even while it only *types* synthetic ones, defeating the injection-blast-radius argument (0014:154). "Synthetic" is a property of everything the loop can touch, not only what it types.

**Which side ASH's capture environment falls on — and the exact PII-flip trigger.** ASH's designed environment is `SYNTHETIC`: committed synthetic corpus (0014:645-646), vault-held *test* credentials (0014:550-551), the lower test env inside the secure network of constraint A11 (walkthrough:807). **The PII flip of 0010:147-148 fires when, and only when, the resolved `dataClass` attestation is `PRODUCTION_DERIVED`.** On that event two distinct things happen: (a) ADR 0014's `d4-suspension` gate refuses all discovery and probing (0014:666-668; spec.md:313-316) — a *runtime execution* halt; and (b) 0010:147-148's flip condition is triggered, **reopening this ADR's parallel-non-blocking-track decision** per 0010:145-150 — a *governance* event, because a system handling production PII is exactly the separate-security-owner / blocking-authority-reconsidered case this ADR named (0010:88-91). Suspension without reopening would let ASH silently halt while the ADR governing its security posture stays unexamined — the exact "deferred vs skipped" gap this ADR warns against (0010:139-142).

**Decidability — positive and falsifiable, matching `envClass`.** `dataClass=SYNTHETIC` is not a self-declaration. It holds only when the environment answers a **positive provenance check**: a committed manifest asserting every in-scope dataset's origin is a synthetic generator or authored fixture (no production source, no masking step over a production source), plus a per-run assertion — parallel to the `env-attestation` build-failing test (spec.md:306-312) — that no dataset in scope lists a production-derived origin. **Absence of a `SYNTHETIC` attestation defaults `dataClass` to `PRODUCTION_DERIVED`** (deny-by-default, mirroring 0014:659-668's `envClass` startup assertion), so an unattested environment suspends rather than silently proceeds; a masking step over production data fails the check by construction.

**Scope boundary (what this amendment does NOT decide).** It defines the *provenance predicate* and pins the flip trigger. It does **not** define the *retention-class enum* ADR 0014 also routed to D4 for `capture_run_edges` (0014:363-367) — that is disposable-conversion-state lifecycle data on ADR 0006's axis (0006:72-78), and its retention values are a **named, required companion ADR 0006 rider**. Until that rider lands, 0014:363-367's `capture_run_edges` retention class stays open. This split is deliberate and named: this ADR owns the provenance line because it owns the flip trigger; ADR 0006 owns retention because retention *is* lifecycle. Recorded here rather than reinterpreted in passing.

**Compliance riders (appended to `## Compliance`, 0010:152-167).** These continue this ADR's manual-plus-CI style; the automated startup/provenance checks are ADR 0014 F-candidates extending F11 (`env-attestation`), ratified-with-the-owning-gate per 0014:765-766.

- **`dataClass` startup attestation (automated, startup + CI-blocking; extends ADR 0014 F11, 0014:799-806):** the capture worker's resolved config MUST carry a `dataClass` attestation. **IF** no `SYNTHETIC` provenance manifest is present and validated at startup, **THEN** `dataClass` resolves to `PRODUCTION_DERIVED` and discovery/probing are disabled (deny-by-default), with a build-failing regression test — the same positive-check discipline `envClass=RESETTABLE_TEST` carries (spec.md:306-312). An environment that merely omits the attestation fails closed.
- **Provenance-integrity assertion (automated; extends ADR 0014 F11):** the `SYNTHETIC` manifest MUST fail validation if any in-scope dataset's committed origin lists a production source, a masking/tokenization step over a production source, or a subset/sample of a production table — **and the manifest MUST cover both the input corpus (0014:645-646) and the environment's resident data** (the one-provenance-root clause). Masked production data attests `PRODUCTION_DERIVED`, never `SYNTHETIC`.
- **`PRODUCTION_DERIVED` runtime transition (automated, per-run — a NEW enforceable line, extending this ADR's Compliance):** **WHERE** the resolved `dataClass=PRODUCTION_DERIVED`, the worker MUST refuse all discovery and probing (satisfying `d4-suspension`, spec.md:313-316) AND MUST write an **attributable lineage/incident record** for the transition (the incident shape of 0014:562-564 / 0009:210-214), naming the trigger. This runtime transition is deliberately **not** filed to the ADR-acceptance security-review queue (0010:154-158), which is an acceptance-time queue with no runtime-event shape; the runtime event is an incident record, and it *separately* triggers the governance reopening below.
- **Security-review queue entry on governance reopen (manual, per ADR 0010 — reuses 0010:154-161 shape):** the `PRODUCTION_DERIVED` transition reopens this ADR per 0010:145-150; the reopened decision, when next re-accepted, gets its queue entry at that acceptance moment per the existing 0010:154 mechanism, drained before the target's first production release (0010:159-161). Zero reopenings without an entry.
- **Dual-hat attestation ownership (manual, per environment — respects 0010:88-91, :162-164):** the `SYNTHETIC` provenance manifest is signed by the designated security owner (dual-hatted for Phase 1); while dual-hatted, the attestation's non-independence is restated in the risk register per 0010:162-164, so the environmental-safety predicate inherits the same honesty posture as the review backing it.

## Notes

Author: arch-decide stage 4 (agent draft, written at the gate that resolved the
0008 / 0009 security-approval inconsistency)
Date: 2026-07-26
Approved by / date: Rajnish Khatri / 2026-07-26, in both capacities — the
architecture gate and, per the Decision above, the security-owner role for this
target. The non-independence is the point being recorded, not an oversight.
Superseded date: —
Last modified / by / what: —
Last modified / by / what: 2026-08-01 / ADR 0014 D4 routing (owner, dual-hatted security role) / Prod-grade-data definition amendment added — defines SYNTHETIC vs PRODUCTION_DERIVED as a provenance predicate (masked production data is PRODUCTION_DERIVED; deny-by-default when unattested; one manifest covers corpus AND environment) so ADR 0014's `dataClass` attestation is machine-checkable parallel to `envClass`; a PRODUCTION_DERIVED attestation both suspends discovery at runtime and reopens this ADR as a governance event, with the runtime transition filed as an incident record (not the acceptance-time queue). Retention-class enum for capture_run_edges (0014:363-367) is a named companion ADR 0006 rider, left open. Status unchanged (Accepted) — the amendment sharpens an existing flip condition into a decidable predicate; it does not reverse the parallel-non-blocking-track decision.
