---
type: research
title: 'Monolithic architecture — external research (2026-09-13)'
description: >-
  Source-verified research backing catalog E1: what a monolith is and is not
  (single deployable / usually one quantum; not a Big Ball of Mud; not E10),
  quantum count as a FACT, deployment and shared-DB coupling, team topology,
  when-to-use / when-not, migration in/out to E10/E6/E2, a local worked
  example, and a trade-off table. No library defaults.
tags: [research, system-design-patterns, E1, monolith]
---

# Monolithic architecture — external research (2026-09-13)

> **What this is.** Evidence pass for catalog **E1** (Group E decision bar).
> Does **not** run arch-style's four determinations or scoring micro-loop.
> Primary pages fetched 2026-09-13. Quantum count and recovered ratings are
> FACT from
> [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md)
> (Richards & Ford *Fundamentals of Software Architecture*, `cases/ArchitectureBook/`
> ch7, ch9–19). A `—` cell is **not** a rating. Unverified items stay in §8.
>
> **Cite, do not rewrite:**
> [boundaries-anatomy.md](../../../cases/coding-rules/boundaries-anatomy.md)
> (monolith = deployment mode),
> [independence.md](../../../cases/coding-rules/independence.md)
> (decoupling mode left open),
> [package.md](../../../cases/coding-rules/package.md)
> (unenforced packages → BBOM),
> [modular-pipeline-exercise.md](../../../cases/ml-solutions-arch/modular-pipeline-exercise.md)
> /
> [modular-design-principles.md](../../../cases/ml-solutions-arch/modular-design-principles.md)
> (in-process modularity ≠ distribution; shared DB + lock-step = distributed
> monolith),
> [distributed-vs-single-node.md](../../../cases/data-intensive-design/distributed-vs-single-node.md),
> [maintainability.md](../../../cases/data-intensive-design/maintainability.md),
> [aws/ch08.md](../../../cases/aws/ch08.md),
> [ADR 0005](../../architecture/adrs/application/mobile-test-automation/0005-adopt-plain-modular-monolith-partitioned-by-cluster.md),
> [style-decision.md](../../architecture/worksheets/mobile-test-automation/style-decision.md).

---

## 1. Scope and non-goals

**Owns** the monolithic *family* as a deployment and quantum decision: one
independently deployable unit, usually one architecture quantum, typically
one shared datastore — plus when-to-use / when-not, migration in/out, one
local worked example, and trade-offs without invented stars.

**E1 must point at E10.** Domain modules + published interfaces + enforced
seams on one deployable is a **modular monolith** — **E10's card**.

| Sibling | Why not this card |
|---|---|
| **E10 Modular monolith** | Own card. Ch11 ratings and too-big signs live there. E1's disciplined in-family destination. |
| **E2 Microservices** | Fine-grained, DB-per-service, most quanta of any style. A *destination*. |
| **E6 SOA / service-based** | Coarse services (book: usually ≤12, often one DB). First distributed hop; ADR 0005's named target. |
| **E3 Layered** | Common *internal* technical partition. Quanta 1; ratings `—`. |
| **E7 / E8** | Other internal shapes that still deploy as one quantum. |
| **B4 Strangler fig** | *Mechanism* to leave a live system. E1 decides whether / toward which style. |
| **E4 / A2 / B7** | Event-driven style and mechanisms. An internal queue does not make a monolith E4. |

**Non-goals.** Library defaults (Packwerk / ArchUnit / Spring Modulith
are E10 enforcement). Scoring via arch-style's four determinations.
Rewriting cited `cases/` notes. Filling missing star figures.

---

## 2. Lineage / vocabulary

**Lewis & Fowler, "Microservices" (2014-03-25).**
https://martinfowler.com/articles/microservices.html — foil definition: the
server-side app as **a single logical executable** (browser UI + one
process + one shared RDBMS). Any change rebuilds that executable. You may
still divide with classes/namespaces and run **cloned instances** behind a
load balancer. Named frustrations (not laws): tied change cycles; decaying
modules; scale-the-entire-app. Older Unix sense (Raymond): a system that
"got too big."

**Fowler, "MonolithFirst" (2015-06-03).**
https://martinfowler.com/bliki/MonolithFirst.html — almost all *successful*
microservice stories started as a monolith that was broken up; almost all
greenfield-as-microservices stories he had heard ended in trouble. YAGNI
plus unstable Bounded Contexts (a network "brushes a layer of treacle"
over seams). Advice is **tentative**. Four paths: (1) modularity in APIs
*and* data (few success stories); (2) peel edges, leave a quiet heart
(B4); (3) first monolith as **SacrificialArchitecture**; (4) two coarse
services ("duolith" = E6-shaped). You cannot assume an arbitrary monolith
decomposes.

**Fowler, "MicroservicePremium" (2015-05-13).**
https://martinfowler.com/bliki/MicroservicePremium.html — do not consider
microservices unless the system is **too complex to manage as a monolith**.
"The majority of software systems should be built as a single monolithic
application. Do pay attention to good modularity within that monolith."
Drivers: large teams, multi-tenancy, many interaction models,
independently evolving functions, scale, sheer size. CD-impossible and
irreplaceable-parts are **not essential** (Facebook, Etsy named). Module
boundaries *can* hold "in theory"; "in practice it seems too easy for
module boundaries to be breached." Inverse Conway in note 2; Thoughtworks
Radar: **Microservice Envy**.

**Fowler, "MicroservicePrerequisites" (2014-08-28)**
https://martinfowler.com/bliki/MicroservicePrerequisites.html — rapid
provisioning, basic monitoring, pipeline "no more than a couple of hours,"
DevOps collaboration. Exit competencies for E2; "really ought to" exist
for monoliths too. **"Design Stamina Hypothesis" (2007-06-20)**
https://martinfowler.com/bliki/DesignStaminaHypothesis.html — no-design
is faster until the **design payoff line** ("usually weeks not months").
Hypothesis, not a measured law; Shopify uses it to time BBOM → modular.

**Foote & Yoder, "Big Ball of Mud" (PLoP '97; HTML 1999-06-26).**
https://www.laputan.org/mud/ — "casually, even haphazardly, structured";
organization "dictated more by expediency than design." Forces include
Throwaway Code, Piecemeal Growth, Keep It Working, Reconstruction. **A
monolith is a deployable; a BBOM is a failure of internal structure.**

**Richards & Ford, *Fundamentals of Software Architecture*** (O'Reilly;
1st ed. 2020 ISBN 9781492043454; 2nd ed. adds ch11 —
https://www.oreilly.com/library/view/fundamentals-of-software/9781098175504/ch11.html).
Monolith **family** = quantum-1 styles: layered, modular monolith,
pipeline, microkernel. Decision tree (ch7, via style-selection): one
characteristics set → monolith family → persistence → done. 2nd-ed ch11
(paraphrase): still "deployed as a single unit of software"; isomorphism
is **domain** modules — E10's definition; E1 needs the "single unit"
half. **Cite
[style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md);
do not re-derive.** Skill: monolith bias when a single quantum suffices
(`ArchCharScope.md:94`); E10 is the recommended start when direction is
unclear (`Modular-monolith-arch.md:229`).

**Martin** ([boundaries-anatomy.md](../../../cases/coding-rules/boundaries-anatomy.md),
[independence.md](../../../cases/coding-rules/independence.md)): one
executable (binary / JAR / .EXE); source-level boundaries remain real;
crossings are chatty function calls; threads are **not** architectural
boundaries. Push decoupling to the point a service *could* form, stay
in-process as long as possible; a good architecture is born a monolith
and can later slide back into one.

**Microsoft Learn, "Common web application architectures"** (2026-09-13).
https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures
— "entirely self-contained, in terms of its behavior"; core in **its own
process**; "typically deployed as a single unit." Horizontal scale =
**duplicate the entire application**. Layers logical, tiers physical —
N-Layer on a single tier is "quite common." A container does not change
the quantum. e-commerce: browse/basket/pay/admin have uneven load, so
cloning scales cold parts with hot ones. Do not split until you can
deliver independent feature slices.

**Shopify.** "Deconstructing the Monolith" (Westeinde, 2019-02-21)
https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity
— decade-plus Rails, >1000 developers, **no boundaries**; 2016 tripwires
(fragile changes, cascading tests, steep onboarding). **Rejected
microservices**; moved **monolith → modular monolith**. "Under
Deconstruction" (2020-09-16)
https://shopify.engineering/shopify-monolith — 2.8M lines, 500k commits,
**37 components**, Packwerk on about a third; explicit team ownership.
An E1→E10 story, not E1→E2.

**Skelton & Pais, *Team Topologies*** (Fowler
https://martinfowler.com/bliki/TeamTopologies.html ; vendor page
https://teamtopologies.com/key-concepts-content/team-interaction-modeling-with-team-topologies).
Stream-aligned team: stable **5–9**, design/build/run, no hand-off. A
monolith too large for one team's cognitive load is a named reason to
find **fracture planes** (book pp. 115–123 — not fetched; §8).
**aws/ch08.md** "tightly integrated" is a *popular* definition and
**too strong** (tightness is the BBOM); same page then recommends
modular code "so that it can be deployed separately if necessary" — E10.

---

## 3. Mechanics (Group E decision bar)

### What the style is

One **deployable** — Fowler's "single logical executable," Microsoft's
"single unit," Martin's JAR/.EXE. Internally it may be folders, N layers
(E3), domain modules (E10), pipes, a microkernel, or a hexagon. Those are
*partitioning* choices. E1 records: **one process image, one release
train, one primary quantum.**

Replicas behind a load balancer are still one quantum (same bits, same
schema). A container does not split it. In-process calls are the
cost/simplicity win and the chatty-interface habit (Martin). Crossing a
process boundary is someone else's style.

### What the style is not

| Lookalike | Why it is not E1 |
|---|---|
| **Big Ball of Mud** | Expedient structure (Foote & Yoder). A monolith *may* be a BBOM; it need not be. Shopify 2016 was; 2019 target was not. |
| **Modular monolith (E10)** | Same deployable, **domain** modules, published APIs, enforcement. Book scores *that* style. |
| **Distributed monolith** | "Services" that share a DB and a lock-step release ([modular-design-principles.md](../../../cases/ml-solutions-arch/modular-design-principles.md)). Network tax of E2, quantum count still **one**. |
| **N independently deployable services** | E2 / E6. Own data + own release ⇒ left E1. |
| **Threads, packages, folders** | Organization, not quanta (Martin). |

### Typical quantum count — FACT

From
[style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md):

> Architecture quantum = smallest independently runnable part
> (`ArchCharScope.md:18`); independent deployability (**the DB is part of
> the quantum — single shared DB ⇒ quantum of one**, `:36`), high
> functional cohesion, low external static coupling, synchronous
> communication with other quanta (`:20-28`).

| Style (monolith family) | Quanta | Prose-recovered ratings | Cite |
|---|---|---|---|
| Layered (ch10) | **1** | **—** (file truncated; do not invent) | `LayeredArchStyle.md:12-26` |
| Modular monolith (ch11) | **1** | cost/simplicity/modularity HI; deploy/test 2★; scale/elasticity 1★; FT **unsupported** | `Modular-monolith-arch.md:216-225` — **E10 owns this row** |
| Pipeline (ch12) | **1** | cost/simplicity/modularity HI; deploy/test "average"; scale/elasticity 1★; FT unsupported | `Pipeline-arch-style.md:204-212` |
| Microkernel (ch13) | **1** | simplicity/cost HI; test/deploy/reliability/modularity/evolvability/responsiveness 3★; scale/elasticity/FT LO | `microkernel-arch-style.md:206-217` |

**E1 typical quantum count = 1.** One characteristics set → monolith
family. Multiple counteracting sets → leave. Shared database, even after
you carve HTTP endpoints, **collapses you back to one**. The book has
**no** star row labelled "Monolithic architecture." Layered stays `—`;
modular-monolith stars are E10's recovered numbers only.

### Deployment

One artifact, one pipeline, one infra set (Shopify; Microsoft "simplest
deployment model"). ADR 0005: CI asserts exactly one deployable. Release
coupling is total (Lewis/Fowler); Facebook/Etsy show CD still works.
Still E1: one VM / App Service / single container; several **identical**
replicas. A web+worker pair that **must** ship together and share a DB is
still one quantum.

### Data

The database is inside the quantum. A single shared DB is the usual
persistence and the coupling test that keeps the count at one. Richards &
Ford via the skill (`choosing-appropriate-arch.md:93,116`): single
relational DB is the default to **challenge**, not a law; **split tables
along domain components** from day one. Opposite-lifecycle tables should
not share foreign keys even on one engine
([style-decision.md](../../architecture/worksheets/mobile-test-automation/style-decision.md)
§3). ACID is cheap here and expensive after a split (E6 is the book's
"best distributed style for ACID needs"; E2 forbids cross-service txns).
A "microservice" fleet on one schema is E1 wearing E2's clothes.

### Team topology

One stream-aligned team (5–9, you-build-it-you-run-it) maps onto one
quantum. Lewis/Fowler: a *large* monolith team must divide along
**business** lines, not UI/server/DB. Organizational pain, not a style
defect: Shopify 2016 whole-graph onboarding; E10 too-big signs
(`Modular-monolith-arch.md:92-104`) — long changes, surprise breakage,
team collisions, slow startup. Leaving for team scale is Inverse Conway:
form teams on fracture planes, *then* extract (B4). Extracting first
produces a distributed monolith plus handoffs.

### Migration in / out

**In:** greenfield (MonolithFirst + MicroservicePremium; book prefers E10
partitioning when direction is unclear); BBOM → stay on one deployable
and impose seams (Shopify 2017–19), not E2; over-split services →
collapse quanta (Martin: slide back as operational need declines).

**Out, in cost order:** (1) **E1 → E10** in-process with compiler/CI
enforcement ([package.md](../../../cases/coding-rules/package.md);
Shopify Wedge/Packwerk; ADR 0005 ArchUnit) — **default first move**;
(2) **E10 → E6** (coarse services, often still one DB; ~12; heavy chatter
= wrong boundaries or wrong style); (3) **E6 / E10 → E2** via **B4**
after MicroservicePrerequisites and a *named* fracture (scale, residency,
cognitive load); (4) hybridizations that stay one quantum (E7 at a
volatile seam, E8 at the edges — ADR 0005 declined E7 as unwarranted
machinery, a local gate not a law). Do not skip to E2 to "get used to the
rhythm"; Fowler records that counter-argument and still advises against
it unless the team already has microservice experience.

### Worked example — mobile-test-automation

[style-decision.md](../../architecture/worksheets/mobile-test-automation/style-decision.md)
(2026-07-26) and
[ADR 0005](../../architecture/adrs/application/mobile-test-automation/0005-adopt-plain-modular-monolith-partitioned-by-cluster.md):
**one quantum**, one Spring Boot deployable, three modules on
characteristic clusters (conversion, validation-certification, evidence),
one primary datastore; pipeline kept as *internal flow*, not macro style.

Coupling test, not fashion: IR spine shared across nearly every
component; Preserve Provenance CA = 13 of 16 — "a single shared database
means a quantum of one"; a synchronous Certify→Models call would collapse
any split. Replay-on-devices looked extractable (divergent ops) and
failed: it writes the shared lineage store. Cluster C looked extractable
(retention) and failed: thirteen network contracts plus audit writes that
must share a *local* transaction with the state they describe. Rejected:
E2 (semantic coupling + fashion check); E3 as macro style; E6 *today* (no
quantum boundary). Destination: **E6**, with named flips (residency;
ADR 0017 — a second live execution backend reopens a *localized* SPI, not
the macro style). CI asserts exactly one deployable. E1 answered "one
quantum?"; the modules are **E10-shaped**. Smaller proof:
[modular-pipeline-exercise.md](../../../cases/ml-solutions-arch/modular-pipeline-exercise.md)
— five in-process classes; "add APIs and Docker" is when the quantum
would change.

### Trade-off table

Qualitative, source-backed. **No invented stars.** E10's 2★ / 1★ /
"unsupported" apply to the *modular* variant only.

| Concern | E1 wins | E1 loses | Source |
|---|---|---|---|
| Cycle time / YAGNI | One pipeline; no suite-of-services premium | Later cost if first seams are wrong and unenforced | MonolithFirst; Design Stamina; MicroservicePremium |
| Consistency | Cheap ACID; lineage can share a local txn with the write | Cross-feature txns become a trap after a naive split | style-decision §3–4; E2 "don't" |
| Ops (small team) | One artifact, one debugger, one on-call | Whole-graph onboarding once a BBOM forms | Shopify 2019; Microsoft |
| Scale / elasticity | Clone-the-app is simple | Hot path clones the cold path; E10 row scale/elasticity **1★** | Microsoft e-commerce; style-selection |
| Fault isolation | — | One process, one fate. E10 FT **unsupported**. Isolation is a reason to *leave*. | style-selection; Lewis/Fowler |
| Deploy / test | Cookie-cutter CD works (Facebook, Etsy) | Any change rebuilds everything; E10 deploy/test **2★** | MicroservicePremium; style-selection |
| Modularity | Possible (Martin; Fowler "in theory"; E10 with enforcement) | Boundaries breach under deadline | package.md; Foote & Yoder; Shopify |
| Team autonomy | One stream-aligned team maps 1:1 | Many teams on one release train collide | Team Topologies; MicroservicePremium n.2 |
| Network fallacies | Not paid *inside* the quantum | Paid the day you extract | style-selection ch9; aws/ch08 |
| Cost / simplicity | Recovered monolith-family rows: **HI** | Distributed styles invert this | style-selection matrix |

---

## 4. Verified defaults / standards

Omitted. Group E styles have no library-defaults section (catalog bar;
`_agent-brief.md`). Packwerk / ArchUnit / Spring Modulith / NetArchTest
are **E10 enforcement**, not E1 defaults.

---

## 5. Failure modes and when-not-to-use

**Failure modes of staying.** (1) **BBOM capture** — everything `public`
([package.md](../../../cases/coding-rules/package.md)); recovery is E10,
not E2. (2) **Distributed-monolith cargo cult** — HTTP + shared schema +
lock-step deploys ([modular-design-principles.md](../../../cases/ml-solutions-arch/modular-design-principles.md);
style-selection "Big Ball of Distributed Mud"). (3) **Scale-everything**
— Microsoft browse-vs-pay; extract *that* module (B4). (4) **Team
collisions** — Shopify 2016; first response is ownership + fracture
planes. (5) **Fashion** — Microservice Envy
(`choosing-appropriate-arch.md:13-38`).

**When to use.** One coherent characteristics set. New product, unknown
Bounded Contexts, need for feedback speed. A stream-aligned team can hold
the system. ACID / single-transaction lineage is driving. E2
prerequisites missing. Direction unclear: stay in the family; prefer
E10's partitioning.

**When not.** Multiple counteracting characteristic sets that fail the
coupling test (then E6/E2/E4 — re-check after choosing sync; sync merges
quanta). A named part must scale, fail, reside, or release
**independently** and is not coupled by a shared store or a synchronous
call. Fault isolation is a top characteristic (unsupported on recovered
family rows). Change is *technically* shaped **and** you need independent
deploy of those slices — not E10 either
(`Modular-monolith-arch.md:229-239`). Several stream-aligned teams blocked
on one train *and* fracture planes known → B4 toward E6/E2.

---

## 6. Cross-links

**E10** — in-family form; defer module topology, ch11 ratings, too-big
signs. **E2** — destination after prerequisites + named fracture. **E6**
— first distributed hop (ADR 0005). **E3 / E7 / E8** — internal shapes
inside one quantum. **B4** — leave mechanism. **B5 / B7** — the day a
write must survive an extract. **C5** — cloned instances are still E1.
ADRs 0005 / 0017 and style-decision — worked pick. `cases/` notes in the
header — cited, not rewritten.

---

## 7. Sources

Retrieved 2026-09-13 unless noted as an in-tree workspace note.
1. Lewis & Fowler, "Microservices" (2014-03-25). https://martinfowler.com/articles/microservices.html
2. Fowler, "MonolithFirst" (2015-06-03). https://martinfowler.com/bliki/MonolithFirst.html — "MicroservicePremium" (2015-05-13) https://martinfowler.com/bliki/MicroservicePremium.html — "MicroservicePrerequisites" (2014-08-28) https://martinfowler.com/bliki/MicroservicePrerequisites.html — "Design Stamina Hypothesis" (2007-06-20) https://martinfowler.com/bliki/DesignStaminaHypothesis.html
3. Foote & Yoder, "Big Ball of Mud" (PLoP '97; HTML 1999-06-26). https://www.laputan.org/mud/
4. Richards & Ford, *Fundamentals of Software Architecture* — via [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md). 2nd-ed ch11: https://www.oreilly.com/library/view/fundamentals-of-software/9781098175504/ch11.html
5. Microsoft Learn, "Common web application architectures." https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures
6. Westeinde, "Deconstructing the Monolith" (2019-02-21). https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity — Shopify, "Under Deconstruction" (2020-09-16). https://shopify.engineering/shopify-monolith
7. Team Topologies, "Team Interaction Modeling." https://teamtopologies.com/key-concepts-content/team-interaction-modeling-with-team-topologies — Fowler, "Team Topologies" bliki. https://martinfowler.com/bliki/TeamTopologies.html
8. Workspace notes listed in the header; `.cursor/skills/arch-style/SKILL.md` (monolith bias; E10 as recommended start).

---

## 8. Uncertain / left out

- **Star-rating figures** did not survive (`style-selection.md` header).
  Layered is `—`. No E1-family row. Do not fill.
- **`cases/ArchitectureBook/`** files cited by style-selection
  (`ArchCharScope.md`, `Modular-monolith-arch.md`, `LayeredArchStyle.md`,
  `choosing-appropriate-arch.md`, …) were **not in the main repo tree**
  on 2026-09-13. Claims recovered only via style-selection and the local
  style-decision; any number not in those two files is unverified.
- **Team Topologies fracture-plane catalog** (book pp. 115–123) not
  fetched. **Fowler 2015** calls monolith-first tentative; the
  start-distributed counter-argument remains **unsettled**.
- **Shopify later numbers** in secondary blogs were **not** on the
  2019/2020 primaries. Use only: >1000 developers (2019); 2.8M lines /
  500k commits / 37 components (2020-09-16). Packwerk 3.x is E10 history.
- **aws/ch08.md** "tightly integrated" over-claims. **Simon Brown GOTO
  2018** / **Dan Manges** not fetched (E10). **Head-count thresholds**
  (20 / 50 / 150) not on any primary fetched. **SacrificialArchitecture**
  bliki not fetched; meaning taken only from MonolithFirst.
