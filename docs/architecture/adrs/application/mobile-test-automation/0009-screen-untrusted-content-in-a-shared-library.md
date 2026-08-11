---
type: architecture
title: ADR 0009 — Screen untrusted content in a shared library invoked at three trust boundaries
description: 'Records the decision the stage-2 gate made but no ADR owned: Screen Untrusted Content was demoted from a logical component to a shared library called by Ingest Test Sources, Acquire UI Evidence, and Invoke Models. One implementation survives, the structurally visible security boundary does not — so fitness function F3 becomes the boundary, and this ADR is its owner. Written in stage 4 review to close the orphaned-F3 defect; the upstream handoff listed F3 without listing an ADR to hold it.'
tags: [architecture, mobile-test-automation, adr, arch-decide]
---

# ADR 0009. Screen untrusted content in a shared library invoked at three trust boundaries

## Status

Accepted

## Context

**Why this ADR exists at all.** The stage-3 handoff listed seven fitness
functions and eight ADRs, but **F3 was named without an ADR to own it** — the
list carried the enforcement mechanism and dropped the decision it enforces.
The stage-4 review caught the orphan. This is a defect in the upstream handoff,
not a dropped item in stage 4, and it is recorded here rather than quietly
patched onto an adjacent ADR.

**Forces.** Test steps ingested from Octane, ALM/QC, and Excel are untrusted
input by the sources' own framing, and the security measures are explicit:
*"100% of ingested source text passes injection screening before reaching any
model"* and *"zero secret/PII detections in prompt payloads, traces, and stored
artifacts"* (worksheet §measures). Security & privacy is **top-3**.

Three components sit on independent trust boundaries and each needs injection
screening plus secret/PII redaction: **Ingest Test Sources** (untrusted source
text entering the system), **Acquire UI Evidence** (device page source and
screenshots, which can carry PII and secure-field content), and **Invoke
Models** (the egress chokepoint where anything reaching a provider is screened).
Per the duplication rule (`ComponentBased.md:193-197`), duplicating the logic
three times converts duplication into coupling, so it must be discharged once.

Pass 2 discharged it as a **component** with three afferent edges. The pass-3
gate directed a merge into the callers. Absorbing it into Ingest Test Sources
alone would have forced the other two either to duplicate the screening or to
depend on the source ingester — an inverted edge from the model-call chokepoint
back to ingestion. The merge was therefore **applied in reshaped form** as a
shared library, which was the correct reading of the gate's intent.

**Alternatives considered.**

- **Shared library, three call sites** (chosen at the stage-2 gate; recorded
  here).
- **Dedicated component with three afferent edges** — the boundary is visible
  in the structure and readable off the diagram; the gate directed it away as
  one of three merges reducing nineteen components to sixteen.
- **Absorb into Ingest Test Sources** — the literal merge; creates the inverted
  dependency from Invoke Models back to ingestion, and leaves evidence capture
  unscreened or duplicating.
- **Duplicate per caller** — no shared contract; fails the duplication rule and
  guarantees the three implementations drift.

**Qualification.** Nygard test: passes — it changes structure (removes a
component boundary), dependencies (three call sites instead of three afferent
edges), and serves a top-3 characteristic. Third-law test: passes — visible
boundary vs component count vs inverted coupling vs drift are all significant
trade-offs. Timing: already decided at the stage-2 gate; this ADR records a
decision in force, which the methodology requires for existing decisions
regardless of how obvious they seem.

### Trade-off matrix

| Contextual factor (weight) | Shared library (chosen) | Dedicated component | Absorb into ingestion | Duplicate per caller |
|---|---|---|---|---|
| One auditable implementation (5) | **++** one library, one red-team corpus | ++ same | + for one caller only | −− three, guaranteed drift |
| Boundary visible in the structure (4) | −− library call, not a structural edge | **++** readable off the diagram | − | −− |
| No inverted dependency (4) | **++** none | ++ none | −− model egress depends on ingestion | ++ none |
| Component-count discipline (3) | **++** honours the gate's reduction | − one more component | ++ | ++ |
| Cost of enforcing "all three screen" (3) | − needs F3; nothing structural forces it | **++** structural | − | −− |

## Decision

**We will implement injection screening and secret/PII redaction as one shared
library, invoked at all three trust boundaries — Ingest Test Sources, Acquire
UI Evidence, and Invoke Models — and not as a logical component.** The library
owns the red-team corpus and the detector rules; it is versioned and its
version is a pinning field on every screened payload's lineage row. No caller
implements its own screening, and no path reaches its egress without invoking
it.

### Boundary-scoping amendment (2026-07-27, stage-5 P1 mitigation M35)

**The three boundaries are defined by the data class that crosses them, not by
the named component that happens to carry it:** (1) untrusted source text
entering the system, (2) device-produced evidence entering the system, (3)
anything leaving toward a model provider. A second path into an existing class
invokes the existing call site; it is not a new boundary and not a fourth call
site.

Written because the P1 storming pass found two further paths carrying
device-produced evidence — the **device-gate artifact pull** from Perfecto Smart
Reporting, and the **hierarchy-capture tool's output**, which is the designed
input to the Phase-1 Copilot IDE path. Both fall inside boundary (2) under this
scoping. Two consequences follow and are binding:

- The artifact-pull step invokes the screening library at landing, alongside
  M9's hash-at-pull digest.
- The **Acquire UI Evidence call site is built in the spine, not deferred** —
  the hierarchy capture feeds the Copilot egress, which F3 structurally cannot
  observe, so screening at capture is the only technical control that path will
  ever have. Deferring it would leave a one-page working agreement as the sole
  protection on that egress.

Corpus fixtures derived from real source workbooks (M16) are committed only as
**screened output** carrying the library-version pinning field; unmarked fixture
files fail CI, and raw workbooks never enter the repository. A secrets scanner
does not substitute here — a workbook of real account numbers trips no secrets
rule.

**Flip-condition counter: 2 of 3.** The flip condition below was examined at the
P1 gate rather than sidestepped. The dedicated-component option was
reconsidered on this ADR's own matrix, which favours it on boundary-visibility
(weight 4) and enforcement cost (weight 3) — the library won on component-count
discipline (weight 3, the lowest weight) because the stage-2 gate directed a
merge. It was **rejected again for one reason**: this ADR already concedes that a
dependency edge proves availability, not invocation, so promotion buys a
readable boundary and a stronger ArchUnit half while F3's runtime half remains
the entire guarantee either way. **A third additional path, or any F3 violation,
forces the flip rather than inviting it.** **Amended 2026-07-31 (ADR 0014): the
counter is now 3 of 3 — see the ASH-Capture flip amendment below; the flip is
executed, ASH-repo-scoped.**

### ASH-Capture flip amendment (2026-07-31, ADR 0014 acceptance)

ASH-Capture adds new LLM ingress/egress paths — device observations
(screenshot + pruned tree) leaving toward the model and LLM-proposed candidate
actions and deep-link routes coming back for execution against an
authenticated banking-app session (call-site map CS1–CS7 in ADR 0014). On any
arithmetic this crosses the recorded flip condition: **the counter stands at
3 of 3 and the flip is executed rather than reconsidered**, per this ADR's own
"forces the flip rather than inviting it."

Scope of execution, per the owner's clarify decision (C3, 2026-07-31): **the
flip restructures where the new paths live** — in the ASH repo, screening is
promoted from a library call to a structurally visible **screen-gate
component**; the executor's only evidence-landing adapter and the proposer's
only channel adapter both route through it, ArchUnit-enforced (two-half F3
construction preserved). **The spine's three call sites are untouched** —
Replan R1 reaffirmed the spine screening tasks unchanged — and whether the
spine's screening must also be promoted is **recorded open**, routed to the
spine's own change process at its next gate. The discovery loop must not
execute against any device while this amendment is unmerged.

Status unchanged (Accepted) — the amendment executes the recorded flip
condition; it does not reverse the decision.

**Technical justification:**

- One implementation satisfies the duplication rule at all three boundaries
  without creating the inverted edge that absorbing it into ingestion would —
  the model-call chokepoint must not depend on the source ingester.
- The three boundaries are genuinely independent: source text, device evidence,
  and model egress fail differently and need the same detector, not the same
  caller.
- Screening at the **egress** boundary (Invoke Models) is the backstop that
  makes the other two recoverable: even if ingestion screening is bypassed by a
  future path, nothing reaches a provider unscreened.

**Business justification:**

- **Strategic positioning:** injection screening of untrusted test content is a
  named regulatory expectation in the banking context; one auditable
  implementation is a defensible answer, three divergent ones are not.
- **Cost:** one red-team corpus to maintain and one detector to tune, rather
  than three that each need their own upkeep.
- **Time to market:** a library is available to all three callers from week
  one, with no component contract to negotiate first.

## Consequences

- **The security boundary is no longer visible in the architecture.** This is
  the honest cost, recorded at the stage-2 gate and not softened here: nothing
  structural forces the three callers to invoke the library. A future component
  added to any of these three paths can omit the call and nothing in the
  deployed structure objects. **F3 is the boundary now** — it is not a
  confirmatory check, it is the whole guarantee.
- Stage 2 recorded the resulting **Static: Algorithm connascence** — one
  implementation prevents divergence of the algorithm, but invocation is
  unenforced by structure. F3 is that finding's handling.
- This is the second of two boundaries converted from structure to build-time
  governance at human gates (the other is the model-provider seam, ADR 0001).
  Stage 3 flagged the pattern: three of seven cross-cutting fitness functions
  now exist to hold boundaries that no longer exist in the structure, and
  arch-validate should treat F1–F3 as release-blocking.
- Forfeited from the dedicated-component option: the readable boundary and the
  structural guarantee. Forfeited from duplication: nothing worth naming.
- **Flip condition:** a fourth call site, or an F3 violation reaching a release
  branch, reopens the dedicated-component option — at that point the
  visible boundary is worth the component count. **Counter at 2 of 3** as of
  2026-07-27; see the boundary-scoping amendment for what was examined and why
  the flip was declined a second time.
- **Screening's failure mode is quarantine-and-review, not a hard stop** (P1
  mitigation M35): a blocking control with no sanctioned override manufactures
  unsanctioned ones. Overrides are recorded, attributable decisions under the
  no-silent-disable line (risk mitigation M18). The honest cost: a sanctioned
  override is itself a bypass — accepted because a recorded one is strictly
  better than the unrecorded kind. The library's call must be cheap
  (in-process, no network, one-line API); friction is the bypass mechanism.

## Compliance

- **F3 (automated, CI-blocking, load-bearing):** no ingestion, evidence-capture,
  or model-call path reaches its egress without a screening call. Statically
  assertable in part (ArchUnit: the three components' egress packages must
  depend on the screening library) and completed by a runtime assertion on the
  egress paths, because a dependency edge proves availability, not invocation.
  **Both halves are required** — the ArchUnit half alone would pass a component
  that imports the library and never calls it.
- **Red-team corpus regression (automated, per release):** the maintained
  corpus runs against the library; bypass rate is reported and a regression
  blocks the release. This is the stage-1 operational measure as a gate.
  **Amended 2026-07-27 (P1 mitigation M36), because "maintained" was carrying an
  owner, a cadence, and a standard that existed nowhere:**
  - **Owner: the security function that owns the secure-SDLC standard** (E6) —
    not the implementing team, and deliberately not the architecture owner, who
    already holds the judge-calibration chain and the ADR 0010 security-owner
    role.
  - **Cadence is a forcing function, not a calendar:** every quarantine event,
    every recorded screening override, and every injection-shaped input found in
    the wild becomes a corpus case. Upkeep is a byproduct of operations.
  - **No absolute adequacy floor** — undefinable for a red-team corpus, and any
    number set would be gamed. Instead the regression reports **case count,
    source mix (seeded / operational / external), and date of last addition
    alongside the bypass rate**, so an inadequate corpus refutes its own green
    result.
  - **External case source required:** operational growth is a feedback loop over
    what is already detected and cannot generate blind-spot cases, so the loop
    alone converges on confident blindness. An inheritable security-function
    corpus is the named source; its availability is a week-0 question.
- **Secret/PII egress detector (automated, operational):** zero detections in
  prompt payloads, traces, and stored artifacts; a detection is an incident,
  not a warning. **Amended 2026-07-27 (P1 mitigation M36):** the worksheet's
  *manual sampling* counterweight is **substituted** — random sampling against
  this system's near-zero base rate (mock data, evidence fact E2) has too little
  statistical power to challenge a zero, which is the false-confidence failure it
  was meant to catch. The corpus regression above is the detector's real test.
  The retained supplement is **novelty-based sampling**: payloads from source
  shapes not seen before (a new feeding team's format, a new app screen) plus a
  small fixed random draw, flagged into the existing review queue. Substitution
  of a top-3 measure recorded here rather than reinterpreted in passing.
- **Manual:** any new component on an ingestion, evidence-capture, or model-call
  path is reviewed for its screening call before merge; adding a fourth call
  site routes back to this ADR's flip condition.
- **Security-review queue entry (per ADR 0010):** PII, secrets, and three trust
  boundaries are all triggers here — the heaviest security load of any ADR in
  this set. The parallel review is queued at acceptance and drained before the
  target's first production release.

## Notes

Author: arch-decide stage 4 (agent draft, written during the stage-4 critical
review to close the orphaned-F3 defect)
Date: 2026-07-26
Approved by / date: Rajnish Khatri / 2026-07-26 (architecture gate).
**Security review queued as parallel work under ADR 0010, not as a status
blocker** — this ADR involves PII, secrets, and trust boundaries, three
triggers under the workspace approval criteria. The gate accepted on the
architecture merits and routed the security review to the parallel track that
ADR 0010 established for this target. A review finding arrives as a revision or
a superseding ADR, not as a retroactive hold on this status.
Superseded date: —
Last modified / by / what: 2026-07-26 / arch-decide gate / Proposed → Accepted;
security review reclassified from blocker to parallel track
Last modified / by / what: 2026-07-27 / stage-5 arch-risk (P1 mitigation M35,
accepted by owner at the gate) / boundary-scoping amendment added — boundaries
defined by data class rather than named component; artifact-pull and
hierarchy-capture paths bound into boundary (2); Acquire UI Evidence call site
required in the spine; corpus-fixture screening marker; quarantine-and-review
failure mode with recorded overrides; flip-condition counter recorded at 2 of 3
with the flip reconsidered and declined for stated reasons. Status unchanged
(Accepted) — the amendment narrows scope ambiguity, it does not reverse the
decision.
Last modified / by / what: 2026-07-27 / stage-5 arch-risk (P1 mitigation M36,
accepted by owner at the gate) / Compliance amended — red-team corpus given an
owner (the security function), an operational forcing function in place of a
cadence, and provenance-mix reporting in place of an undefinable adequacy floor;
the worksheet's manual-sampling counterweight substituted by corpus regression
plus novelty-based sampling, recorded as a substitution of a top-3 measure.
Last modified / by / what: 2026-07-31 / ADR 0014 acceptance (combined SPEC-OK
gate, owner; clarify C3) / ASH-Capture flip amendment added — the discovery
loop's LLM paths (CS1–CS7) cross the flip condition; counter recorded at 3 of
3 and the flip executed ASH-repo-scoped (screen-gate component,
ArchUnit-enforced); spine call sites untouched, spine-side promotion recorded
open and routed to the spine's own change process. Status unchanged (Accepted)
— the amendment executes the recorded flip condition, it does not reverse the
decision.
