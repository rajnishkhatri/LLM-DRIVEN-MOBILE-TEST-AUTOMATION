---
type: architecture
title: ADR 0017 — Keep the modular monolith for o7; core+plugin stays declined, and the flip trigger is narrowed to a second live execution backend
description: 'Records the o7 fork''s style-level decision, which ADR 0016 left inherited rather than re-checked: the plain Spring Boot modular monolith of ADR 0005 holds for o7, and the microkernel/core+plugin hybridization declined at the ADR 0005 gate stays declined. o7''s new seam-shaped realities — the C-MIG driver seam (Appium java-client 10.x live + raw-W3C stub, C1), the interpreter-as-product with a conformance corpus (C3), and the closed opcode set as a governance-gated extension point (spec.md:92) — do NOT trip ADR 0005''s recorded flip condition ("a fourth source adapter or a second concurrent reasoning provider"): o7 adds no source adapter, and o7 is LLM-free on the replay path so the reasoning-provider count is zero. o7 does introduce a third, previously uncontemplated axis — execution-backend plurality — so this ADR narrows the trigger, recording a NEW flip condition on that axis (a second live execution backend on the driver seam reopens the localized driver-seam SPI, option 3, jointly with C1). Supersedes nothing; re-affirms ADR 0005 and cross-references ADR 0016. A plugin registry is disqualified today because its runtime late-binding surface fights o7''s three top characteristics (determinism, auditability, pinning-integrity) head-on.'
tags: [architecture, mobile-test-automation, adr, arch-decide, o7-interpreter-fork]
---

# ADR 0017. Keep the modular monolith for o7; the core+plugin move stays declined, and the flip trigger is narrowed to a second live execution backend

## Status

**Proposed** — 2026-08-05, awaiting the owner's SDD Stage-2 gate (the same gate
as ADR 0016). This ADR records a **style-level** decision for the **o7
interpreter fork** that ADR 0016 legitimately left *inherited* rather than
re-checked: ADR 0016 is the executable-shape decision (interpreter vs codegen)
and explicitly scopes the macro style as carried over — *"a second-language
runtime would fork the build, the CI, and the pinning story for no gain"*
(0016:99–103), *"ADR 0005 (Spring Boot modular monolith — H-SB inherits the
stack)"* (0016:380–381). It never records the **style-level flip-condition
check** against o7's new seam realities. That check is the one genuinely
undocumented style decision the o7 fork introduces, and this ADR exists to
record it.

**Supersedes nothing.** Supersede links are ADR→ADR and imply a *reversal*;
this ADR keeps ADR 0005's style decision intact and re-affirms it for o7. It is
**not** an amendment to ADR 0005's decision body either — o7 changes none of ADR
0005's four determinations. The spine-spec surfaces o7 does touch (the F6 pinning
set, the M37 attribution locus, the M24 pinned-facet set, and the
replay-pipeline-v1 row) are already carried by **ADR 0016's Consequences and its
paired sdd-replan** (0016:257–281); this ADR does not duplicate them.

## Context

**Forces.** The owner proposed, at the o7 brainstorm, a **core+plugin
architecture** for o7 in place of the modular monolith. Read precisely, "core +
plugin" is the **microkernel** style (`microkernel-arch-style.md`, ch13), and the
proposal is three distinct bets that must not be conflated:

1. **Microkernel as the o7 macro style** — the whole interpreter pipeline as
   core + runtime-loadable plug-ins.
2. **A microkernel SPI localized to the driver / adapter / model-provider seams**
   — a scoped plug-in registry *inside* the plain modular monolith. This is the
   **exact "hybridization" ADR 0005 already analyzed, and which won the
   evolvability sub-analysis and lost at the gate** — declined as *"unwarranted
   machinery for the one adapter the week-3 gate needs, and Spring DI supplies the
   Strategy seam for free"* (0005:32–35).
3. **Keep the plain modular monolith** (0005:69–76), which o7's own founding ADR
   inherited as H-SB (0016:99–103, spine o7 spec:5).

ADR 0005 recorded a precise, disjunctive **flip condition** for reopening the
microkernel: *"a fourth source adapter or a second concurrent reasoning provider
reopens the microkernel (jointly with ADR 0001)"* (0005:111–112). The o7 question
is therefore narrow and testable: **do o7's committed new realities trip that
condition, or is core+plugin still unwarranted machinery?**

**The three o7 realities that pattern-match to a microkernel — and why the match
is superficial.**

- **The C-MIG driver seam.** o7 drives Appium through the official java-client
  10.x with a **raw-W3C fallback behind an interface seam** (C-MIG; 0016:169–173).
  Per **C1** the raw-W3C adapter is an **unimplemented stub behind the seam**,
  activated only when a concrete java-client limitation forces it, with the
  activation **recorded in lineage** (o7 spec:58, :129). This is a seam with **one
  live implementation** — Strategy-via-DI, not a plug-in registry.
- **The interpreter-as-product with a conformance corpus.** o7 owns the
  interpreter as a maintained product gated by a committed **IR-conformance
  corpus** that must pass before any `interpreterVersion` is pinned (C3; o7
  spec:60; 0016:353–358). This looks like "core + validated plug-ins against a
  corpus," but the corpus gates **one** `interpreterVersion` as a single
  behavioral unit (0016:200) — evidence *for* a monolith, not for independently
  released plug-ins.
- **The closed opcode set as an extension point.** The opcode set
  `{TAP, TYPE, SWIPE, WAIT, ASSERT, LAUNCH, NAVIGATE}` and assertion kinds
  `{TEXT_EQUALS, ELEMENT_PRESENT, VALUE_CHECK}` are **closed**, and *"a vendor or
  authoring extension that adds an opcode is a spec change, never a silent runtime
  capability"* (o7 spec:92). This is a **governance-gated, compile/spec-time**
  extension point — the structural *opposite* of a runtime-discoverable plug-in
  registry.

**Alternatives considered** (full matrix and per-characteristic scoring in the o7
style analysis; driving set inherited from the stage-1 worksheet §5, re-weighted
for o7 in the matrix below):

- **Plain modular monolith (chosen).** The incumbent (ADR 0005), inherited by ADR
  0016 as H-SB. Fits o7; its one soft rib is evolvability at the seams, protected
  by convention (ADR 0001 + fitness functions F1/F2) rather than by structure
  (0005:101–107).
- **Microkernel as the macro style** — **disqualified**. A runtime-plug-in style
  adopted by a pipeline whose top three characteristics all *foreclose* runtime
  variation, and whose one extension point is deliberately closed. Scores negative
  on all three top-3 rows.
- **Localized microkernel SPI at the driver seam** (the declined ADR 0005
  hybridization) — **contained, declined now, one narrow trigger recorded**. Earns
  exactly one row (evolvability) that o7 already banks via the plain Spring-DI
  driver seam, and pays auditability + pinning surface for plug-in plurality o7
  does not have.
- **Pipeline as the macro style** — rejected for o7 for the same reason as the
  spine (0005:41–43): the bounded repair loops and human escalation are
  back-and-forth, not one-way filters.

**Qualification.** Nygard test: passes — this is a structure decision (does o7
introduce a runtime plug-in seam, or not), affecting the reproducibility/pinning
trust boundary. Third-law test: passes — every option carries significant
trade-offs (evolvability structure vs audit/pinning surface vs build cost).
Timing — last responsible moment: the **executable-shape** decision is at its
last responsible moment now (ADR 0016); the **seam-registry** decision is **not**
— its retrofit cost is low because the seam boundary already exists in code (C1),
so it is safely deferrable to when a second live backend lands. Deciding the
macro style to the extent of *"stay modular monolith"* is at its last responsible
moment (implementation of T30–T32 cannot start without it); promoting the seam to
a registry is not.

### Trade-off matrix (driving characteristics as rows, weighted for o7)

Weights reflect o7's driving set. The three top characteristics carry the
decision; evolvability and testability are real but secondary; fault tolerance,
scalability, and elasticity were **eliminated at spine stage 1** (worksheet §6)
and carry ~0 weight — a style is not rewarded for them here. Scores: `++` strong
fit, `+` fit, `0` neutral/contained, `−` poor, `−−` disqualifying.

| Driving characteristic (o7 weight) | Modular monolith (chosen) | Microkernel as macro style | Localized SPI at driver seam |
|---|:---:|:---:|:---:|
| **Determinism / K-integrity** — pass^k, `healPolicy: NONE`, no runtime AI (**5, top**) | **+** enables it cheaply; determinism itself is bought by construction, not by the style | **−** a runtime plug-in surface is the adaptivity o7 bars (o7 spec:92, :136) | **0** the guarantee lives at the IR gate, not in how the driver binds |
| **Auditability & traceability** — `irDigest`+`interpreterVersion`, reviewed = executed (**5, top**) | **++** one trust boundary, in-transaction lineage "trivial in one process" (0005:63, :86–87) | **−** behavior spread across independently-versioned plug-ins → a version matrix to reconstruct | **−** the registry itself becomes a thing to pin and attest (0016:154) |
| **Pinning-integrity / reproducibility** — F6 complete-or-invalid, corpus gates the version (**5, top**) | **++** one deployable makes F6 and the C3 corpus single-process invariants (o7 spec:99–102) | **−** fragments one `interpreterVersion` into a core × N-plugin version matrix (0016:200) | **−** adds pinning surface with no reproducibility gain for one live driver |
| Maintainability / evolvability — driver seam, closed-opcode extension point (**3**) | **0** modularity HI but nothing structural at the seams (0005:64, :101–107) | **+** the only monolithic style the book rates for evolvability (3★), but capped — o7's variability is one live driver + a closed set | **+** the registry *is* the seam — but the benefit is already banked by Spring DI (0005:35) |
| Testability — IR gate, dry-run, conformance corpus, seam-contract test (**3**) | **+** in-process gates + no-device dry-run + corpus are cheap to exercise | **0** plug-in-boundary tests o7 does not need; enlarges the corpus obligation | **0** the interface seam already gives mockability; a registry adds a discovery path to test |
| Fault tolerance / scalability / elasticity (**~0** — eliminated at spine stage 1) | − | −− | − |

**Weighted verdict.** The modular monolith is the only candidate positive or
neutral on every weighted row, and `++` on the two rows (auditability,
pinning-integrity) where distribution or plug-in fragmentation can only add
correlation/version-matrix tax. Microkernel-as-macro-style goes **negative on all
three top rows** to buy a capped `+` on a weight-3 row — a losing trade at o7's
weighting, and disqualified. The localized SPI earns its single `+` on
evolvability, which the incumbent already banks via the plain Spring-DI seam, so
its **net weighted delta over the incumbent is negative** — it adds
auditability/pinning surface for plurality o7 does not have. This is the weighted
verdict for *this* fork, not the generic style ranking.

## Decision

**We will keep the plain Spring Boot modular monolith of ADR 0005 for the o7
interpreter fork, and we will not adopt a core+plugin (microkernel)
architecture** — neither as the macro style nor as a plug-in registry localized to
the driver / adapter / model-provider seams. The interpreter is a Spring Boot
module hosted by the existing device-gate worker inside the
`validation-certification` topology, and the execution-plan renderer lives in the
existing `evidence` module (C4; o7 spec:5, :85), consistent with ADR 0005's
three-module cluster partitioning. The **C-MIG driver seam is a plain Spring-DI
Strategy seam** (interface + one live java-client 10.x implementation, with the
raw-W3C adapter a stub behind it per C1), **not a plug-in registry.**

**We record that o7 does not trip ADR 0005's flip condition, and we narrow the
trigger.** ADR 0005's condition — *"a fourth source adapter or a second concurrent
reasoning provider"* — is **not tripped** by o7 (disposition below). o7 introduces
a **third axis ADR 0005 never contemplated: execution-backend plurality.** We add
a **new, sharper flip trigger on that axis** (Consequences), so the reopening
question is governed rather than left to drift.

The why, front and center: **make the reviewed artifact the executed artifact,
and keep "what ran" a two-value answer.** o7's whole thesis (0016:154) is that the
committed IR at `irDigest`, walked by the interpreter at one `interpreterVersion`
Git SHA, *is* the executed artifact and *is* the complete audit answer. A plug-in
registry inserts a third runtime variable — which plug-in versions bound at
runtime — that is not captured by those two pins. Everything below follows from
refusing that third variable while o7 has no plurality that needs it.

**Technical justification:**

- **The flip condition is untripped, on both disjuncts, strictly.** o7 adds **no
  source adapter** — ingestion (Excel/Octane behind the C1 adapter contract) is
  inherited unchanged from the spine (o7 spec:20); the driver seam is a *different
  axis* (device-driving, not source-ingestion), and conflating the two is a
  category error. And o7 is **LLM-free on the replay path** (0016:290–291; o7
  spec:71) — the reasoning-provider count on the executed path is **zero**, not "a
  second," so the model-provider seam the condition guards is structurally inert.
- **A plug-in registry fights the three top characteristics head-on** (the hidden
  trade-off, per the First Law — see Consequences): it is a runtime late-binding
  surface exactly where o7 spent its effort closing runtime-variation surfaces
  (`healPolicy: NONE`, `cloudAdaptivityDisabled` per session — o7 spec:103, :136),
  it inserts a binding not captured by `irDigest` + `interpreterVersion` (breaking
  F6 complete-or-invalid unless the plug-in set is also pinned — o7 spec:99), and
  it turns the C3 conformance corpus from "one version behaves" into "every
  admissible plug-in combination behaves" — a combinatorial blow-up of the release
  gate that guards the OpenTest/Selenium-IDE die-unmaintained failure mode
  (0016:254, :356).
- **The evolvability o7 needs is already banked structurally at zero registry
  cost.** The C-MIG interface seam holds the migration path open (0016:169–173);
  Spring DI selects the one live implementation by configuration; the C1
  lineage-recorded-activation rule (o7 spec:129) makes any future raw-W3C fallback
  an evidenced event rather than silent adaptivity. That single rule delivers the
  auditability a registry would otherwise threaten.
- **The closed opcode set is anti-extensibility by design and must stay that way**
  (o7 spec:92). A microkernel's value proposition is runtime-discoverable
  extension; o7's one extension point is a governance-gated spec change. Adopting a
  style whose reason to exist is the thing o7 structurally bars is fashion
  overriding fit.

**Business justification:**

- **Time to market / cost:** the least machinery that reaches the o7 week-gate
  (o7 spec:130) — no registry, no plug-in versioning, no combinatorial conformance
  matrix. The interpreter ships as one module against one corpus.
- **Audit posture (strategic positioning, in a banking context):** a bank auditor
  asking "what exactly ran?" gets the two-value answer — *the committed IR at this
  `irDigest`, walked by the interpreter at this `interpreterVersion`* (0016:238–239)
  — instead of a plug-in version matrix. Preserving that answer is the strategic
  asset; a registry would degrade it.
- **Strategic positioning (kept, not spent):** the migration path stays priced and
  named. The seam boundary already exists in code (C1), so if the
  execution-backend axis ever goes plural, promoting the seam to a registry is a
  local change at that moment — not a rewrite, and not a cost paid on speculation
  now.

## Consequences

- **The declined registry's benefit, stated plainly (the honest gap).** The driver
  seam and the closed-opcode extension point have **no runtime structure**; their
  protection is the C-MIG interface seam + Spring DI + the ArchUnit/fitness rules
  (F1/F2 from ADR 0001, and T02's no-per-test-generated-Java rule from ADR 0016) —
  build-time rules that *"exist only if the team builds and maintains them"*
  (0005:101–107). Evolvability remains convention-and-CI-protected for o7, exactly
  as for the spine. This is the cost accepted for the audit and pinning gains
  above.
- **The hidden trade-off, recorded because a plug-in registry looks free and is
  not** (First Law, Corollary 1). A registry buys evolvability by introducing a
  runtime dynamic-binding + reflection/discovery surface that is paid three times
  over on o7's top-3 rows: (1) a new "which plug-in versions bound at runtime"
  variable that F6 must now pin or be incomplete (o7 spec:99); (2) a runtime-
  variation surface of the same family o7 bars by construction (o7 spec:136); (3) a
  conformance obligation that expands from one `interpreterVersion` to every
  admissible plug-in combination (0016:356). The evolvability `+` it buys is
  already delivered by a compile-time Spring-DI seam at zero cost. The C3
  conformance corpus is therefore **evidence for the monolith** — it treats
  `interpreterVersion` as one indivisible pinned unit.
- **NEW flip trigger — the execution-backend axis (this ADR's substantive
  addition).** o7 introduces an axis ADR 0005 never named: plurality of
  **execution backends** on the driver seam. The reopening trigger for the
  **localized driver-seam SPI (the option-3 hybridization)** is:

  > A **second *live* execution backend** on the driver seam — the raw-W3C adapter
  > promoted from stub to live *concurrently with* the java-client, or a third
  > backend (e.g. the recorded Robot Framework fallback, 0016:311) hosted
  > concurrently — reopens the localized driver-seam SPI, **jointly with the C1
  > lineage-recorded-activation rule** (o7 spec:129).

  **Precondition today: unmet.** There is one live driver (java-client 10.x) and
  one stub (raw-W3C). A seam with one live implementation is Strategy-via-DI; the
  registry is warranted only when there are ≥2 live backends to register and
  version independently. **The macro-microkernel (option 2) is not reopened by
  this trigger and effectively never under o7's constraints — it would additionally
  require the opcode set to *open* to third-party runtime-discoverable extension,
  which o7 spec:92 structurally bars.**
- **Losing options' trade-offs.** Microkernel-as-macro-style would have bought a
  runtime plug-in registry sized for volatile, independently-deployable extensions
  — paying the **Volatile Core** antipattern *inverted* (a plug-in split around a
  deliberately stable core) and **Plug-In Dependencies** (a version matrix against
  the single-`interpreterVersion` pin). The localized SPI would have bought
  *structural* evolvability at the one seam ADR 0005 left convention-protected — a
  real benefit — but for plurality o7 does not have, at the cost of the audit and
  pinning surface above; it is declined now and reopened only by the new trigger.
- **This ADR imposes on future work.** No runtime plug-in registry may be
  introduced at the driver / adapter / model-provider seams without either this
  ADR's new execution-backend trigger firing (≥2 live backends) or a superseding
  ADR; the driver seam stays a Spring-DI Strategy seam with the raw-W3C path a
  lineage-recorded fallback (C1); the opcode set stays closed and extension stays a
  spec change (o7 spec:92); the one-deployable CI check (0005:126) continues to
  bind for o7.
- **Relationship to the other o7 determinations (unchanged, recorded for
  completeness).** o7 reopens none of ADR 0005's Determinations 1–3: one quantum
  (o7 adds no trust boundary — 0016:72), one primary store (ADR 0006), sync with
  the two async seams (ADR 0007 / C2). This ADR is Determination-4 only.

## Compliance

- **No-plugin-registry-at-the-seams rule (automated, CI-blocking):** an ArchUnit
  rule that the driver / source-adapter / model-provider seams are bound by Spring
  DI (interface + injected implementation), with **no** service-registry /
  runtime-discovery / classpath-scanning binding mechanism at those seams. A
  registry-shaped binding fails the build until this ADR's execution-backend
  trigger has fired and a superseding or amending ADR is on file. This is the
  structural guard that keeps "what ran" a two-value pin answer.
- **One-live-driver assertion at the seam (automated, CI-blocking):** CI asserts
  exactly one *live* driver adapter behind the C-MIG seam (java-client 10.x); the
  raw-W3C adapter remains a stub. A second live adapter appearing is the
  execution-backend trigger — it must fail the build until the reopening ADR
  exists, so the trigger cannot be crossed silently. (Pairs with the C1
  lineage-recorded-activation criterion, o7 spec:129.)
- **Closed-opcode enforcement (automated, at the IR gate — inherited):** the
  `opcodeClosed` check (o7 spec:92, :119) already fails any IR referencing an
  opcode or assertion kind outside the closed set; this ADR records that this check
  *is* the governance gate that keeps the one extension point compile/spec-time,
  and that relaxing it toward runtime extensibility is a style change requiring a
  superseding ADR, not a configuration toggle.
- **Manual review (flip-trigger discipline):** the new execution-backend flip
  trigger is revisited automatically the first time a second live backend is
  proposed (raw-W3C promotion, or the Robot Framework fallback hosted
  concurrently) — the localized-SPI option is put back on the table at that review
  with this ADR's matrix as the starting point, not re-derived from scratch.
- **Cadence:** folds into ADR 0005's quarterly module-boundary review — a
  worsening trend of seam-boundary violations or a second-backend proposal is a
  reopening conversation, not a cleanup ticket.

## Notes

Author: arch-decide (SDD Stage 2), from the o7 core+plugin-vs-monolith style
analysis (2026-08-05). Driving characteristics inherited from the stage-1
worksheet §5, re-weighted for o7 in the matrix (top-3: determinism/K-integrity,
auditability, pinning-integrity; FT/scalability/elasticity eliminated at spine
stage 1). The style scoring, the adversarial flip-condition test, and the
synthesis were produced by a multi-agent analysis; every citation was verified
against source before drafting.

Date: 2026-08-05 (drafted).

Approval classification (per `.arch/adrs/common/approval-criteria.md`):
**Security trigger applies** — the decision governs the reproducibility/pinning
trust boundary (whether a runtime plug-in binding, uncaptured by `irDigest` +
`interpreterVersion`, may exist), which is a trust-boundary / control question →
designated security owner's approval required. No cost trigger (no new spend; the
decision *declines* machinery). No cross-team trigger (single team, single
deployable). Record approver and date below on ratification.

Approved by / date: pending — awaits the owner's SDD Stage-2 gate (same gate as
ADR 0016).

Superseded date: — (supersedes no ADR; re-affirms ADR 0005 for o7 and narrows its
flip trigger).

Cross-references: ADR 0005 (the modular-monolith style decision re-affirmed here;
its flip condition tested and narrowed — 0005:32–35 decline rationale, 0005:64
microkernel evolvability row, 0005:101–107 convention-protected seams,
0005:111–114 flip condition), ADR 0016 (o7 founding decision; H-SB stack
inheritance 0016:99–103, the C-MIG driver seam 0016:169–173, LLM-free replay path
0016:290–291, "reviewed artifact is the executed artifact" 0016:154, the C3
conformance-corpus release gate 0016:353–358), ADR 0001 (F1/F2 convention-only
seam protection), ADR 0006 (single primary store — Determination 2 unchanged),
ADR 0007 (async seams / transactional outbox — Determination 3 unchanged). o7-spec
anchors: driver seam / C1 spec:51, :58, :129; closed opcode set spec:92, :119;
LLM-free replay spec:71; F6 complete-or-invalid spec:99–102; C3 corpus spec:60,
:86, :102; C4 renderer placement spec:85; determinism rationale spec:70; week-gate
spec:130.

Last modified / by / what: 2026-08-05 / arch-decide (SDD Stage 2) / initial draft
— Status Proposed, awaiting the owner's Stage-2 gate.

## Gate

GATE: PENDING HUMAN — agent recommendation: accept as Proposed → Accepted at the
o7 Stage-2 gate (with the security owner's approval per the classification above),
ratifying specifically: (a) **keep the plain modular monolith for o7**; (b)
**core+plugin declined** — microkernel-as-macro-style disqualified, the localized
driver-seam SPI contained/deferred, not adopted; (c) the flip condition is
**untripped** on both recorded disjuncts; (d) the **new execution-backend flip
trigger** (a second live driver backend reopens the localized SPI, jointly with
C1) is recorded and governed by the two CI assertions in Compliance. What would
move the cursor toward reopening: a second *live* execution backend on the driver
seam (raw-W3C promoted, or Robot Framework hosted concurrently). What would move
the cursor toward the macro microkernel: the opcode set opening to third-party
runtime-discoverable extension — which o7 spec:92 currently bars.
