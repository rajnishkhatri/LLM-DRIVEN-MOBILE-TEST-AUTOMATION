# ADR 0015. LLM normalizer (A0): DEFERRED at the 2026-08-01 gate, then RATIFIED by owner override 2026-08-02 (see Amendment)

## Status

**Accepted (2026-08-01) — AMENDED by owner override 2026-08-02: A0 RATIFIED.**
The original gate ruling below (FOLD now + DEFER the LLM stage) stands unaltered as
the record of what was decided on 2026-08-01; the 2026-08-02 override is additive
and is set out in **[Amendment — Owner override 2026-08-02](#amendment--owner-override-2026-08-02-a0-ratified-without-the-measured-trigger)**.

**Accepted** — 2026-08-01, at the sdd-spec Stage-2 gate (owner decision). The
disposition was adjudicated FOLD (deterministic) now + DEFER (the LLM stage),
RATIFY refused, from three independent lenses (security, value, lifecycle) that
converged FOLD at high confidence. The owner reviewed the A0 mock trio
(`mocks/o1-spine/NormalizedIntent.{input.txt,json}`) and named three reasons A0
felt necessary — messy real input, screen-context inference, one-intake-shape
consistency; each was decomposed against the evidence at the gate (see
**Decision → the owner's three reasons**), and the decomposition confirmed the
ruling rather than flipping it. The paired spine-spec amendment (M15 fold
criteria) carries its own sign-off at the spine gate.

<!-- Cross-references: ADR 0001 (F1 no-model-call seam), ADR 0009 (boundary-scoping amendment, screening call sites), ADR 0014 (fourth-LLM-surface / CS4 second-path precedent). Routed here by Replan R1 D2 as an explicit RATIFY-OR-DEFER decision. -->

## Context

Replan R1 D2 routed the proposed **A0 Normalizer** — an LLM intake stage drawn upstream of the deterministic A1 parser in `o1-pipeline-walkthrough.md` (§2.0:53–75) — here as a RATIFY-OR-DEFER decision. A0 claims to take free-form English or a manual test-script string (Octane/Jira/ALM/Excel), strip noise, canonicalize phrasing ("sign in"/"log in"/"login" → one form), and emit a `NormalizedIntent` (not a `TestCaseIR`) so A1's deterministic parser "succeeds more often" (walkthrough:55–57, :62–64). A1 and A2 still own the IR (walkthrough:59–60).

This is **not** "spec A0." A0 is **PROPOSED and unratified** (walkthrough:73), self-labelled `*[newly added this session]*` (walkthrough:53), and exists only in one chat session — it is item **N13 NEW** in the provenance ledger, "NOT in any ADR or the blueprint" (walkthrough:766). A 7-agent review confirmed it adds an untrusted-text-in / LLM-out injection surface with zero screening analysis (review finding #3 at review:52; Q4 at review:119; Q14 at review:135; rec #7 at review:166). The decision baseline is therefore **nothing exists yet**: the signed-off spine (`mobile-test-automation-spine.spec.md`) commits only a **deterministic ingestion CLI** — Excel (Apache POI) + Octane REST behind one adapter contract (spec.md:61, C1 at spec.md:26) — as intake.

Three dispositions were weighed:

- **(R) RATIFY** A0 as a weeks-3-8+ LLM stage in a non-spine module with an ADR 0009 call-site map.
- **(D) DEFER** A0 as a future feature; keep the deterministic ingestion CLI as the only intake.
- **(F) FOLD** the normalization A0 names — phrase-canonicalization + noise-strip — into deterministic patterns, adding no LLM and no new injection surface.

A0's enumerated operations (walkthrough:62–64) are lexical transforms — a synonym table and a regex-class noise pass — not semantic reasoning. The spine already performs "per-adapter deterministic canonicalization + source-snapshot digest at intake (M15)" (spec.md:61) and A1 already "Recognizes deterministic patterns (e.g. the login pattern)" (walkthrough:89). A0's asserted value — "makes A1 succeed more often" — has **no measured A1 parse-failure rate** behind it anywhere in the spec, plan, walkthrough, or review (review Q4 at review:119). Under Constitution A1/G1 (the simplest thing that satisfies the need), unquantified value is a real mark against the heaviest option.

## Decision

We will **DEFER the A0 LLM-normalizer stage** as an evidence-gated future re-open — deferred, not rejected outright — and **FOLD a minimal, deterministic phrase-canonicalization table + noise-strip ruleset into the already-signed-off per-adapter canonicalization surface (spec.md:61, M15)**, explicitly **NOT** into A1's "structure only, no semantics" contract (walkthrough:84).

Justification, each ground verified:

- **A0 is unratified and single-session.** §2.0 self-labels it NEW (walkthrough:53, :73); rec #7 rules it "cannot remain an audit-facing diagram fact with no decision behind it" (review:166). R carries the burden of proof; F and D build up from the signed-off spine.
- **A0's value is asserted, never measured.** The sole justification (walkthrough:56–57, :64) rests on no measured A1 parse-failure rate (review Q4 at review:119). Constitution A1/G1 forbids buying the heaviest option for an unquantified benefit.
- **The mechanism is deterministic table/rule work the spine already houses.** Folding three spellings of "login" into one form is a synonym table + a regex-class pass — the spine already does deterministic canonicalization per adapter (spec.md:61, :281–288) and A1 already recognizes deterministic patterns (walkthrough:89). An LLM is not required.
- **R buys the heaviest cost for the unmeasured value.** Under ADR 0001 F1, A0's model call must route through Invoke Models and live outside the spine repo or CI fails it. Under ADR 0009 as amended, A0's class-(1) intake and class-(3) egress each owe a screen-gate obligation. Under ADR 0014's logic, A0 is a **fourth LLM surface** into the same authoring arm (after CodeGen, A2-fallback, and the ASH proposer). The fold owes none of these because it adds no model call.

**Chosen deterministic mechanism (the folded capability).** Inside each ingestion adapter's existing deterministic canonicalization step (spec.md:281–288), pre-A1:

- **A committed, versioned, diffable phrase-canonicalization table** — a synonym → canonical-form map (e.g. `{sign in, log in, login} → login`), owned by the ingestion-adapter team, covered by the adapter's contract test, applied deterministically to the canonicalized source rendering.
- **A noise-strip ruleset** — deterministic rules removing boilerplate, headers, and step-numbering from the canonicalized payload before the source-snapshot digest is taken, so the digest and any future cache key (M15) key on canonical content.

Both are pure in-adapter string transforms: **zero model call, zero new class-(1) LLM-out path, zero class-(3) egress.** A1's structure-only contract is untouched — the fold lives upstream of A1, in the M15 adapter surface.

**The owner's three reasons, decomposed at the gate (the recorded rationale for
this disposition).** Reviewing the A0 mock, the owner named three reasons A0 felt
necessary. Each resolves without a front LLM stage:

- **(#3) One intake shape / consistency across sources** → served by **this
  deterministic fold**. Reducing Octane/Jira/Excel/free-form to a single
  `NormalizedIntent`-shaped canonical rendering is a *canonicalization* goal — the
  M15 per-adapter surface's exact purpose (spec.md:61, :281–288). Uniformity needs
  one shared output schema, not a model.
- **(#2) Screen-context inference** (e.g. "the app" / "home screen" →
  `screenContextHint: LoginScreen/HomeScreen`, visible in the mock) is genuine
  semantic work — but the walkthrough **already assigns screen-context
  normalization to A2**: "normalizes navigation → `NAVIGATE` + `screenContext`"
  (walkthrough:97/§2.2). A2 is already a deterministic-first / **LLM-fallback**
  stage inside the screened Invoke Models seam. So screen-context inference is a
  reason to use **A2 (which exists and is already screened)**, not to stand up a
  new A0 surface. **Scope ruling: screenContext stays A2's responsibility; the
  fold does not attempt it, and A0 is not resurrected to own it.**
- **(#1) Paraphrasing messy real prose** (real Octane/Jira/free-form English, far
  messier than the tidy mock) is the one thing a deterministic table genuinely
  cannot do — and is exactly **bucket (b)** below. It is real, unmeasured, and
  **already partly served by A2's post-A1 LLM fallback**. It is the measured
  re-open trigger, not a present ratification.

The mock (`mocks/o1-spine/NormalizedIntent.json`) confirms this: every transform
it actually shows — `phrasingVariantsAbsorbed: ["Sign in","log in","login"]`,
noise-paragraph stripping — is lexical (fold-served); its one semantic field,
`screenContextHint`, is A2's job.

## Consequences

**Flip-counter ruling (settled fact — the "ADR 0009 screening call-site map" this decision owes).** A0 trips **no fourth flip**. The counter is already **3 of 3 with the flip EXECUTED and ASH-repo-scoped** (0009:123–125, :127–149; ADR 0014 acceptance). The review's "flip counter already at 2-of-3 → a genuinely new path forces the flip" framing (review:52; Q14 at review:135) **predates ADR 0014's amendment and is stale**; it is re-derived here from ADR 0009 as it reads now. The controlling rule is the boundary-scoping amendment (0009:87–92): boundaries are defined by **data class, not component** — (1) untrusted source text entering, (2) device-produced evidence entering, (3) anything leaving toward a model provider — and "a second path into an existing class invokes the existing call site; it is not a new boundary and not a fourth call site" (0009:90–92). Mapping A0's two flows:

- **A0 raw-text intake** (Octane/Jira/ALM/Excel free-form) = class **(1)** untrusted source text. The spine already screens class (1) at the ingestion call site (spec.md:62). A0's intake is a **second path into class (1)** — it invokes the existing ingestion call site; not a new boundary, not a fourth call site (0009:90–92).
- **A0 model egress** (`NormalizedIntent` toward a provider) = class **(3)** model egress. The spine already screens class (3) at Invoke Models (ADR 0001 seam). A0's egress is a **second path into class (3)** — it invokes the existing call site; not a fourth.

This is categorically identical to how ADR 0014 ruled its own CS4: "Deep-link prompt egress | (3) — second path | invokes the existing CS2 call site (0009:90-92)" (0014:586). A0 introduces no novel class-(2)-derived egress of the kind that grounded ADR 0014's genuinely-new third path on CS2 (0014:591–593). **Consequence:** the flip ruling is **neutral between R and F** and thereby removes R's only structural argument — it does not grant R a free ride. A *ratified* A0 would still owe (a) its ADR 0009 call-site map onto the existing class-(1) and class-(3) call sites, (b) an sdd-replan amendment to the signed-off ingestion CLI, (c) F1 out-of-spine repo placement (ADR 0001), and (d) the post-0014 structurally-visible screen-gate obligation for LLM-adjacent paths in that arm. **The fold owes none of these** — it adds no model call — leaving F strictly cheaper on every remaining axis.

**Measured trigger that re-opens R (evidence gate).** DEFER of the LLM stage is unblocked only by a **measured A1 parse-failure rate**, recorded as a rider on the review's §12.4 measurement spike:

- Run A1's existing deterministic patterns (walkthrough:89) plus the signed-off ingestion CLI (spec.md:61) against the **M16 real-workbook corpus** (10–20 real workbooks, already a mandated week-0 spine artifact — spec.md:400–411 — so no new data-collection burden) **plus a real free-form-English intent sample** (the corpus is manual scripts and under-represents the natural-language intake A0 targets — walkthrough:55).
- Decompose the parse-failure rate by cause: **(a) fixable by synonym table + noise-strip rules** → the fold closes it; **(b) genuinely novel phrasing no finite rule anticipates** → only then does R's case open.
- Even bucket (b) is already partly served by **A2's existing deterministic-first / LLM-fallback stage** (walkthrough:106), which is post-A1 and already inside the screened Invoke Models seam. **R's value case opens only if the spike shows bucket (b) is both large AND un-served by A2's fallback.**

**Governing rationale.** Constitution A1/G1 — the simplest thing that satisfies the need. The LLM stage is the heaviest option and must beat the deterministic fold on evidence, which is absent. The fold captures the evidenced (lexical) value at zero trust-boundary cost.

**Losing option (R — RATIFY A0 as an LLM stage), and why we passed.** R would have bought automated paraphrase of arbitrarily malformed prose — a genuine residual the fold cannot fully cover (a deterministic table cannot paraphrase). We passed because that value is unmeasured (review Q4 at review:119), the flip ruling denies R its structural argument (neutral, above), R alone incurs the F1/0009/0014 costs enumerated above, and A2's existing LLM-fallback already absorbs part of bucket (b). R is the only disposition the current evidence actively refutes; it is preserved as a future, measured re-open, not a present ratification.

**Downside accepted.** The fold cannot paraphrase novel prose; if the spike shows a large, A2-unserved bucket (b), this deferral will have delayed a warranted A0. This is accepted because the deferral is explicitly evidence-gated and cheaply reversible, whereas ratifying now would pay the heaviest cost against an unmeasured benefit.

**Named future dependency (not decided here).** If the spike ever unblocks R, the repo-topology question — whether a ratified A0 co-locates with the ASH proposer behind the already-built ADR 0014 screen-gate (reusing sunk infrastructure) or gets its own non-spine module — is **parked behind the measured trigger**. Deciding it now would presuppose a RATIFY the evidence does not support. Recorded here as a future dependency only.

**Placement fork — RESOLVED at the gate (2026-08-01).** The one live fork was
whether even a minimal phrase-canonicalization table reads as materially expanding
the signed-off M15 adapter contract (→ DEFER-only, ship no fold now) or is a
legitimate minimal addition to it (→ FOLD now). The owner chose **FOLD now**. The
DEFER-only fallback is retained on record: if adapter-contract review during the
spine-spec amendment finds the table expands the contract beyond "minimal," it
reverts to DEFER-only — **never** RATIFY.

## Amendment — Owner override 2026-08-02 (A0 ratified without the measured trigger)

**What changed, and its basis.** The owner (Rajnish Khatri) has **RATIFIED A0** as
an owner override, effective 2026-08-02. This reverses the disposition of the
2026-08-01 gate (DEFER the LLM stage) for A0 only. It is an **owner override on
UNCHANGED evidence**: it is made **WITHOUT** the measured re-open trigger that this
ADR's own Consequences § set as the sole thing that unblocks R — namely a
**measured A1 parse-failure rate** from running A1's deterministic patterns + the
signed-off ingestion CLI against the **M16 real-workbook corpus plus a real
free-form-English intent sample**, decomposed into bucket **(a)** (fold-fixable)
and bucket **(b)** (genuinely novel phrasing, and shown large AND un-served by A2's
LLM fallback). That spike has **not** been run; bucket (a)/(b) is **not** measured.
The gate's evidentiary objection to R therefore still stands on the record — the
override does not claim the evidence now exists; it proceeds in spite of its
absence, as an owner prerogative. Everything in Context / Decision / Consequences
above remains the accurate account of why the gate deferred.

**Open follow-on obligations (a)–(d) — a ratified A0 owes all four; NONE is
discharged by this amendment.** Consequences § (this ADR, the "A *ratified* A0
would still owe…" paragraph) is explicit that a *ratified* A0 still owes each of
these. Ratifying by override does not pay them; it converts them from "costs R
would incur" into **OPEN follow-on work**:

- [ ] **(a) ADR 0009 call-site map.** Map A0's two flows onto the **existing**
  screening call sites — class **(1)** untrusted-text-in (ingestion call site,
  spec.md:62) and class **(3)** model-egress (Invoke Models, ADR 0001 seam). Not a
  new boundary map; an instantiation onto the existing ones. *(Obligation source:
  ADR 0015 Consequences § — "a *ratified* A0 would still owe … its ADR 0009
  call-site map"; the boundary-scoping basis for mapping onto existing call sites
  rather than a new boundary is ADR 0009:87–92.)*
- [ ] **(b) sdd-replan amendment to the ingestion CLI.** Amend the signed-off
  deterministic ingestion CLI spec to admit the A0 stage upstream of A1. *(Source:
  ADR 0015 Consequences §; the signed-off spine `mobile-test-automation-spine.spec.md`,
  spec.md:61.)*
- [ ] **(c) F1 out-of-spine-repo placement.** Any A0 model call must route through
  Invoke Models and live **outside the spine repo** — CI **fails** it if placed in
  the spine repo. *(Source: ADR 0001, F1 no-model-call-in-spine seam.)*
- [ ] **(d) Structurally-visible screen-gate obligation.** The post-ADR-0014
  structurally-visible screen-gate obligation for LLM-adjacent paths in the
  authoring arm applies to A0's flows. *(Source: ADR 0014.)*

These four are now tracked as follow-on work items, to be discharged before or as
part of A0's implementation; this amendment records the ratification decision, not
their completion.

**Flip-counter — accurate de-escalation (no fourth flip; do NOT read this as
lowering the obligations above).** Ratifying A0 does **not** trip a fourth
screening flip. The counter stays **3 of 3**, flip EXECUTED and ASH-repo-scoped.
A0's two flows are **second paths** into already-screened classes: raw-text intake
= a second path into class **(1)**; model egress = a second path into class **(3)**.
Per ADR 0009's boundary-scoping amendment, "a second path into an existing class
invokes the existing call site; it is not a new boundary and not a fourth call
site" (0009:90–92) — categorically identical to how ADR 0014 ruled its CS4
(0014:586). This is stated so the amendment does **not overstate** the risk of
ratifying: no new trust boundary is created. It is **not** a reason to hand-wave
obligations (a)–(d): those are the call-site-map, replan, placement, and screen-gate
duties a ratified A0 owes precisely *because* it invokes the existing class-(1) and
class-(3) call sites — the second-path finding is what routes A0 onto them, not what
excuses it from them.

**The deterministic fold is retained and coexists with A0.** Ratifying A0 does
**not** undo the FOLD that shipped. The committed, versioned phrase-canonicalization
table and the noise-strip ruleset remain in the M15 per-adapter canonicalization
surface (Decision §; spec.md:281–288), covered by the adapter contract tests. A0
sits **upstream** of the fold, not in place of it: A0 (if/when built out under
obligations (a)–(d)) feeds the same deterministic canonicalization the fold already
performs. Nothing already built is removed or superseded by this amendment.

**Last modified / by / what:** 2026-08-02 / Rajnish Khatri (owner override) / A0
RATIFIED by owner override on unchanged evidence — the measured A1 parse-failure-rate
trigger (M16 corpus + free-form sample, bucket-(a)/(b) decomposition) is expressly
**waived, not satisfied**; obligations (a)–(d) opened as follow-on work; flip counter
unchanged at 3-of-3 (A0 flows = second paths into classes (1) and (3), no fourth
flip); the deterministic fold retained and coexisting. Status line updated; H1
updated (filename unchanged as an immutable identifier). Prior record (Context /
Decision / Consequences, the 2026-08-01 gate) left intact.

## Compliance

- **F1 (ADR 0001):** unaffected by the fold — the fold adds no model call, so nothing new is subject to the no-model-call-in-spine CI rule. The rule stands as a guard: any future A0 model call CI-fails if placed in the spine repo.
- **F2 (ADR 0001):** the fold is in-adapter; no source-system type crosses the adapter boundary (spec.md:78–80). The phrase-canon table operates on the canonicalized rendering, and only the IR leaves ingestion.
- **F3 / ADR 0009:** the fold crosses **no trust boundary** and invokes **no new call site** — both A0-shaped flows are second paths into already-screened classes (1) and (3) (0009:90–92), and the fold instantiates neither. The existing ingestion-egress screening (F3, spec.md:81–84) already covers the canonicalized payload; the fold runs upstream of that screen and adds no egress. Static half + runtime half remain the whole guarantee, unchanged.
- **Contract test (M20):** the phrase-canon table and noise-strip rules are covered by each adapter's contract test, exercised against both fixture families from week 0 (spec.md:274–280).
- **Governance — manual review cadence:** the measured-trigger spike (M16 corpus + free-form sample, bucket-(a)/(b) decomposition) is reviewed at the next spine gate before any A0 re-open; the repo-topology question is reviewed only if the spike unblocks R.

## Notes

Author: sdd-synthesize (SDD Stage 2, Design synthesizer), invoked from Replan R1 D2 as an explicit RATIFY-OR-DEFER decision; disposition adjudicated FOLD (deterministic) now + DEFER (the LLM stage), RATIFY refused; three lenses (security, value, lifecycle) converged FOLD at high confidence
Date: 2026-07-31 (drafted); 2026-08-01 (accepted)
Approved by / date: Rajnish Khatri / 2026-08-01 (sdd-spec Stage-2 gate; owner
reviewed the A0 mock and confirmed the three-reason decomposition — fold #3, route
#2 to A2, defer #1)
Superseded date: —
Last modified / by / what: 2026-08-01 / sdd-spec Stage-2 gate (owner) / status
Proposed → Accepted; the owner's three reasons (messy input, screen-context,
consistency) decomposed and recorded in Decision; screenContext scope-ruled to A2;
placement fork resolved to FOLD-now (DEFER-only fallback retained)
Prior modification: 2026-07-31 / sdd-synthesize / initial draft — A0 LLM stage DEFERRED (evidence-gated re-open); minimal deterministic phrase-canonicalization + noise-strip FOLDED into the M15 per-adapter canonicalization surface, not A1; flip-counter ruling recorded as settled fact (A0 = second-path into classes (1) and (3), no fourth flip, mirroring 0014 CS4); cross-referenced ADRs 0001, 0009, 0014