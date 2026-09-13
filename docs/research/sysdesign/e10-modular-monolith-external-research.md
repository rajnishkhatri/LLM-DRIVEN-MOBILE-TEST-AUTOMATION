---
type: research
title: 'Modular monolith — external research (2026-09-13)'
description: >-
  Source-verified research backing catalog E10: domain modules inside one
  deployable (quantum FACT = 1), module vs process boundaries, shared DB
  still one quantum, when-to / when-not, E1→E10→E6/E2 via B4, a local
  worked example, and the ch11 trade-off row. Not BBOM, not distributed.
tags: [research, system-design-patterns, E10, modular-monolith]
---

# Modular monolith — external research (2026-09-13)

> **What this is.** Evidence pass for catalog **⊕E10** (Group E). Not a
> Concept. Does **not** run arch-style's four determinations or scoring
> micro-loop. Pages fetched 2026-09-13. Quantum count and recovered
> ratings are **FACT** from
> [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md)
> (Richards & Ford, distilled from `cases/ArchitectureBook/` ch7,
> ch9–19). A `—` cell is **not** a rating. Unverified items stay in §8.
>
> **E1 points here; this card points back.** E1 owns the *family*. **This
> card owns the modular variant** — domain modules, published interfaces,
> enforced seams, ch11 ratings, too-big signs. Not BBOM. Not distributed.
>
> **Cite, do not rewrite:**
> [package.md](../../../cases/coding-rules/package.md)
> (Brown: compiler over post-hoc checkers),
> [boundaries-anatomy.md](../../../cases/coding-rules/boundaries-anatomy.md)
> /
> [independence.md](../../../cases/coding-rules/independence.md)
> (Martin: one executable; source-level seams stay real),
> [modular-design-principles.md](../../../cases/ml-solutions-arch/modular-design-principles.md)
> /
> [modular-pipeline-exercise.md](../../../cases/ml-solutions-arch/modular-pipeline-exercise.md)
> /
> [modular-scalar.md](../../../cases/ml-solutions-arch/modular-scalar.md)
> /
> [microservices-challenges.md](../../../cases/ml-solutions-arch/microservices-challenges.md)
> (in-process modularity ≠ distribution; shared DB + lock-step =
> distributed monolith; Iris walk-through is E10),
> [ADR 0005](../../architecture/adrs/application/mobile-test-automation/0005-adopt-plain-modular-monolith-partitioned-by-cluster.md)
> /
> [ADR 0017](../../architecture/adrs/application/mobile-test-automation/0017-keep-the-modular-monolith-for-o7-record-the-execution-backend-flip-trigger.md)
> /
> [style-decision.md](../../architecture/worksheets/mobile-test-automation/style-decision.md).
> `cases/ArchitectureBook/` (`Modular-monolith-arch.md`) was **not in
> the main-repo tree** on 2026-09-13 — cite style-selection only.

---

## 1. Scope and non-goals

**Owns** the *modular* monolith: **one independently deployable unit**
partitioned into **domain modules** with published APIs and enforced
seams. Module boundaries ≠ process boundaries. A shared database still
keeps **quantum count = 1**. When-to / when-not, migration
**E1 → E10 (carve modules) → E6 / E2 (extract via B4)**, one local
worked example, and the book's recovered trade-off row.

| Sibling | Why not this card |
|---|---|
| **E1 Monolithic architecture** | The *family*. E1 decides "one quantum?"; E10 decides the partition. E1 defers ch11 ratings and too-big signs here; this card sends BBOM back. |
| **E2 Microservices** | Fine-grained, DB-per-service. A *destination*. |
| **E6 SOA / service-based** | Coarse services (book: usually ≤12, often one DB). First distributed hop; ADR 0005's target. |
| **E3 Layered** | Horizontal *technical* partition. Quanta 1; ratings `—`. |
| **E8 Hexagonal** | Inside/outside + ports. A module *may* be hexagonal; not a synonym. |
| **E7 Microkernel** | Core + plug-ins + registry. Hybridization; ADR 0005 declined it locally. |
| **B4 Strangler fig** | *Mechanism* to leave a live E10. |

**Non-goals.** Library defaults. Scoring via arch-style's four
determinations. Rewriting cited `cases/` notes. Filling missing star
figures. Reconstructing unfetched ch11 mediator / peer-to-peer bodies.

---

## 2. Lineage / vocabulary

**Richards & Ford, *Fundamentals of Software Architecture*, 2nd ed.**
O'Reilly ISBN 9781098175504. Ch11 is **new** — Ford
(https://nealford.com/books/SAF2e.html, fetched 2026-09-13): added
because the ecosystem moved. O'Reilly ch11 landing
https://www.oreilly.com/library/view/fundamentals-of-software/9781098175504/ch11.html
returned **Access Denied** 2026-09-13. **Cite
[style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md);
do not re-derive.** Recovered: single deployable, domain modules;
quanta **1**; **cost/simplicity/modularity HI; deploy/test 2★;
scale/elasticity 1★; FT unsupported** (`:216-225`). When-to: tight
budget/time, unclear direction, DDD teams, domain-shaped change. **Not**
for high ops or technically-oriented change (`:229-239`). Too-big:
long changes, surprise breakage, team collisions, slow startup
(`:92-104`).

**Fowler** — fetched 2026-09-13. "MonolithFirst" (2015-06-03)
https://martinfowler.com/bliki/MonolithFirst.html — successful
microservice stories started as a monolith that was broken up;
greenfield-as-microservices ended in trouble. YAGNI plus unstable
Bounded Contexts (a network "brushes a layer of treacle" over seams).
The *logical* path is APIs **and** data layout — he had **few** success
stories of that path (note 1: you cannot assume an arbitrary monolith
decomposes). Other paths: peel edges (B4); SacrificialArchitecture;
"duolith" (E6-shaped). Advice is **tentative**. "MicroservicePremium"
(2015-05-13) https://martinfowler.com/bliki/MicroservicePremium.html —
do not consider microservices unless the system is **too complex to
manage as a monolith**. "Do pay attention to good modularity within
that monolith." Boundaries hold "in theory"; "in practice it seems too
easy for module boundaries to be breached" — why E10 is its own card.
"PresentationDomainDataLayering" (2015-08-26)
https://martinfowler.com/bliki/PresentationDomainDataLayering.html —
layers work at *small* grain; once a layer gets big, "split your top
level into **domain oriented modules which are internally layered**."
That is E3 → E10. Splitting *teams* by technical layers is the
anti-pattern.

**Simon Brown, "Modular monoliths" / package-by-component** (~2013;
GOTO Berlin 2018-11-01
https://gotober.com/2018/sessions/515/modular-monoliths ; collection
https://simonbrown.je/modular-monolith/ ; slides
https://static.simonbrown.je/modular-monoliths.pdf — fetched 2026-09-13).
"If you can't build a well-structured monolith, what makes you think
microservices is the answer?" Four cuts; only the last is E10's native:
package-by-layer (E3), package-by-feature, ports-and-adapters (E8),
**package-by-component** (business logic + persistence behind one
published interface; UI outside). If every type is `public`, all four
collapse. Prefer the **compiler** over ArchUnit-after-the-fact.
[package.md](../../../cases/coding-rules/package.md) is this chapter.
Slides: modularity ⊥ deployment-unit count — BBOM, modular monolith,
microservices, distributed BBOM sit on that 2×2.

**Shopify Engineering** — fetched 2026-09-13. "Deconstructing the
Monolith" (Westeinde, 2019-02-21)
https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity
— **>1000 developers**, no boundaries; 2016 tripwires. **Rejected
microservices**; moved **monolith → modular monolith**: one application,
strictly enforced domain boundaries; ~6000 classes reorganized; public
API + exclusive data; Wedge scored violations. "Under Deconstruction"
(Müller, 2020-09-16) https://shopify.engineering/shopify-monolith —
**2.8M** lines, **500k** commits, **37 components**, Packwerk on about
a third. Dense/cyclic graphs make public interfaces extra indirection;
prefer **functional** cohesion. Extract a service only for a named
reason (storefront throughput; card-vault residency). "A Packwerk
Retrospective" (2024-02-07)
https://shopify.engineering/a-packwerk-retrospective — static
constant-reference checker + `package_todo.yml`; privacy checks removed
in **3.0**. Isolating "Platform Essentials" took **months** after todos
hit zero. Domain buckets ≠ runtime function.

**Thoughtworks, Garg (2023-06-03).**
https://www.thoughtworks.com/en-us/insights/blog/microservices/modular-monolith-better-way-build-software
— fetched 2026-09-13. Modules independently developed and tested;
**deployed as a single unit**; extractable business-capability
boundaries. Microservices are an **end-goal**, not a starting point.
Leave E10 when modules must scale differently, the team outgrows one
release train, diverse technology is required, or the domain is well
understood *and* complexity needs encapsulating as services. The
holiday "extract then merge back" sketch is unverified (§8).

**Martin** ([boundaries-anatomy.md](../../../cases/coding-rules/boundaries-anatomy.md)):
one executable; source-level seams stay real; crossings are chatty
function calls. Stay in-process as long as a service *could* form.

---

## 3. Mechanics (Group E decision bar)

### What the style is

A **modular monolith** is **one deployable** whose **top-level**
organisation is **business domain**, not technical layer (Richards &
Ford via style-selection; Shopify: strictly enforced domain boundaries;
Brown: package-by-component inside one execution environment).

Minimum mechanical properties (not a library checklist): (1) **one
process image, one release train, one primary quantum** — replicas and
containers do not split it; (2) **domain modules** as the top-level
cut, each with a **published** interface (Shopify: cross-component
ActiveRecord associations always violate); (3) **enforced seams** —
compiler / module system / checker; if everything is `public`, E3 / E8
/ E10 are the same graph (Brown); (4) **acyclic module graph**, or
inversion of control where a cycle would form (Shopify 2020: cycles
mean "they are really one thing"; in-process pub-sub still E10, not
E4); (5) **data ownership at the module** even on a shared engine —
Fowler's extractability precondition (MonolithFirst note 1).

**Module boundary vs process boundary.** A module boundary is a
*source-level* seam: compiler visibility, a published type, a forbidden
import. Crossing it is a function call. A process boundary is a
*quantum* seam: its own deployable, its own failure domain, usually its
own datastore. E10 has the first and refuses the second. Crossing to
another process is someone else's style (E6 / E2). That is the
cost/simplicity win and the chatty-interface habit (Martin).

**Shared database still one quantum.** From
[style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md)
ch7: architecture quantum = smallest independently runnable part
(`ArchCharScope.md:18`); **the DB is part of the quantum — single shared
DB ⇒ quantum of one** (`:36`). Carving HTTP endpoints on one schema
does not raise the count. Sync calls between attempted quanta silently
merge them (decision tree `:80-106`).

### What the style is not

| Lookalike | Why it is not E10 |
|---|---|
| **Big Ball of Mud (E1 gone wrong)** | Expedient structure. No published APIs. Shopify 2016 was this; 2019's target was E10. **Send BBOM back to E1.** |
| **E1 as a family** | E1 answers "one quantum?" E10 is one *partitioning* of that family. |
| **Package-by-layer (E3)** | Technical buckets. Fowler 2015: promote domain modules; keep layers *inside*. |
| **Package-by-feature, all types public** | Vertical folders without encapsulation (Brown). |
| **Hexagon (E8)** | Inside/outside + ports. Orthogonal sibling cut. |
| **Distributed monolith** | "Services" + one schema + lock-step ([modular-design-principles.md](../../../cases/ml-solutions-arch/modular-design-principles.md)). Quantum still **one**. |
| **Microservices (E2)** | Own process + own DB. Extracting a module *is* the E10→E2 move. |

### Typical quantum count — FACT

Do **not** re-run the determinations; do **not** re-score.

| Style | Topology | Partitioning | Quanta (FACT) | Prose-recovered ratings | Cite |
|---|---|---|---|---|---|
| **Modular monolith (ch11)** | single deployable, domain modules | domain | **1** | **cost/simplicity/modularity HI; deploy/test 2★; scale/elasticity 1★; fault tolerance unsupported** | `Modular-monolith-arch.md:216-225` via style-selection |

**E10 typical quantum count = 1.** Reproduce the row; do not re-score.
No other star cells recovered. Do not borrow E7's evolvability 3★.

### When to use / when not

**When to use** (book `:229-239` + Fowler + Shopify / Thoughtworks):
tight budget / time; direction unclear (**start here, migrate later**);
DDD / Bounded-Context teams and **domain-shaped** change; one
characteristics set (decision tree → monolith family); a stream-aligned
team can hold the system (module ownership first — Shopify 2020); ACID
/ single-transaction lineage is driving; extractability later without
paying process distance now.

**When not:** **high operational characteristics** (scale/elasticity
**1★**, FT **unsupported** — isolation is a reason to *leave*);
**technically-oriented change streams** (E3 / E7, not E10; `:229-239`;
ADR 0005 corrected a pipeline-stage cut); a named part must scale,
fail, reside, or release independently and is not coupled by a shared
store or a sync call (Shopify: storefront, card vault); several teams
blocked on one train *and* fracture planes known → B4 toward E6/E2;
diverse technology / independent runtimes (Thoughtworks).

### Migration: E1 → E10 → E6 / E2 via B4

**In (carve modules, stay one deployable).**

| From | Move |
|---|---|
| Greenfield | Start E10, not E2 (MonolithFirst + MicroservicePremium; book `:229`). Design APIs **and** data (Fowler path 1) *and* enforce them (Brown) or you get a BBOM — which is E1's failure mode, not this style. |
| **E1 BBOM** | **E1 → E10:** stay on one deployable; impose domain seams. Shopify 2017–19: reorganize by real-world concepts, public APIs, score violations. Müller 2020: pick the incomplete-state that is useful (ownership-first vs spin-off-clean). |
| E3 layered | Promote domain modules to the *top* level; keep layers inside (Fowler 2015; Brown package-by-component). The Architecture Sinkhole is a reason to leave E3, not a reason to jump to E2. |
| Over-split E2 | Collapse quanta (Martin: slide back as operational need declines). |

**Out (extract via B4).** Order of cost, not fashion. **Do not skip to
E2 to "get used to the rhythm"** (Fowler recorded the counter-argument
and still advised against it). (1) Stay E10 until a named fracture is
real and MicroservicePrerequisites exist (E2 owns that list). Fowler
note 1: most systems "can't be sensibly broken apart" if they acquired
too many dependencies — E10's job is to make that false *before*
extract. (2) **E10 → E6** (coarse services, often still one DB; ~12;
heavy chatter = wrong boundaries). ADR 0005 names this destination.
(3) **E10 / E6 → E2 via B4** — one module at a time from a
low-dependency edge (Fowler's peel). Shopify extracted only for
throughput or residency. (4) Hybridizations that stay one quantum
(E7 / E8); local gate declined E7 — a local decision, not a law.
Thoughtworks's "extract with minimal effort" is aspiration; Shopify's
Platform Essentials isolation (months after Packwerk-zero) is measured
cost. Pulling a module that still shares a table is a distributed
monolith.

### Worked example — mobile-test-automation

[style-decision.md](../../architecture/worksheets/mobile-test-automation/style-decision.md)
(gate closed 2026-07-26) and
[ADR 0005](../../architecture/adrs/application/mobile-test-automation/0005-adopt-plain-modular-monolith-partitioned-by-cluster.md):
**one quantum**, one Spring Boot deployable, **three domain modules** on
characteristic clusters (conversion, validation-certification,
evidence), one primary datastore; pipeline kept as *internal flow*, not
macro style. ADR 0017 re-affirms the same quantum for the o7 fork.

Why E10 not E3: the blueprint's five names were **technical pipeline
stages** — "the shape the modular-monolith style explicitly warns
against." Re-partitioned onto stage-1 clusters. Why not E2: IR spine
shared; Preserve Provenance CA = 13 of 16 — shared DB ⇒ quantum of
one; a sync Certify→Models call would collapse any split.
Replay-on-devices and cluster C looked extractable and failed (shared
lineage store; thirteen in-process contracts plus audit writes that
must share a local transaction). Rejected: E2 (semantic coupling +
fashion check); E3 as macro style; E6 *today* (no quantum boundary).
Destination: **E6**, via B4 when a named flip fires (residency; ADR 0017
— a second live execution backend reopens a *localized* SPI). CI
asserts exactly one deployable. **E1 answered "one quantum?"; this card
answers "domain modules, not pipeline stages."** Smaller proof:
[modular-pipeline-exercise.md](../../../cases/ml-solutions-arch/modular-pipeline-exercise.md)
— five in-process classes; "add APIs and Docker" is when the quantum
would change.

### Trade-off table

Qualitative, source-backed. **No invented stars.** 2★ / 1★ /
"unsupported" are style-selection recovered facts.

| Concern | E10 wins | E10 loses | Source |
|---|---|---|---|
| Cost / simplicity | Book: **HI**. One pipeline; no suite-of-services premium | Later cost if seams are never enforced | style-selection; MicroservicePremium |
| Modularity | Book: **HI** *when* APIs + data + enforcement hold | Boundaries breach under deadline; a checker can encode a *wrong* graph | style-selection; Fowler "in practice"; Shopify 2024 |
| Deploy / test | Cookie-cutter CD still works | Any change rebuilds everything; book **2★** | style-selection |
| Scale / elasticity | Clone-the-app is simple | Hot path clones the cold path; book **1★** | style-selection |
| Fault isolation | — | One process, one fate. Book: FT **unsupported** | style-selection |
| Extractability | Wrong cut is a refactor, not a multi-repo migration | Fowler had few path-1 success stories; Shopify isolation cost is months even at Packwerk-zero | MonolithFirst n.1; Packwerk 2024 |
| Consistency | In-process + one DB = cheap ACID | Shared schema becomes the trap the day you extract | style-decision; E2 "don't" |
| Team autonomy | Module ownership inside one train (Shopify 37 components) | Many teams on one release still collide; too-big signs = long changes, surprise breakage, team collisions, slow startup | Shopify 2020; style-selection `:92-104` |
| Network fallacies | Not paid *inside* the quantum | Paid the day you extract | style-selection ch9 |

---

## 4. Verified defaults / standards

Omitted. Group E styles have no library-defaults section
(`_agent-brief.md`). Packwerk, ArchUnit, Spring Modulith, and NetArchTest
are **enforcement mechanisms** cited as existence proofs, not defaults
to copy.

---

## 5. Failure modes and when-not-to-use

**Failure modes.** (1) **Folders without encapsulation** — all types
`public` (Brown); E10 collapses to E3's graph; recovery is access
modifiers, not HTTP. (2) **Public API on a cyclic graph** — Shopify
2020: interfaces leak the old control flow. (3) **Domain labels that
ignore runtime function** — Packwerk 2024: "shop billing settings"
including fraud lived in Billing by name. (4) **Informational cohesion
around tables** — change locality stays poor. (5) **Distributed-monolith
cargo cult** — HTTP + shared schema + lock-step deploys. (6) **Checker
theatre** — zero Packwerk todos ≠ bootable. (7) **Too-big signs ignored**
(book `:92-104`) — long changes, surprise breakage, team collisions,
slow startup; first response is re-cut, not a mesh. (8) **Fashion skip**
— Microservice Envy (MicroservicePremium).

**When not** is under Mechanics (high ops, technical change streams,
named independent-scale / residency / release fracture, or several
teams blocked on one train with known planes).

---

## 6. Cross-links

**E1** — family owner; **must point here**; **this card points back**
(BBOM / "one quantum?" stay on E1). **E2** — destination after
prerequisites + named fracture. **E6** — first distributed hop; ADR
0005's target. **E3 / E7 / E8** — internal shapes (E3 usual *from*;
E7/E8 optional hybridizations). **B4** — leave mechanism. **B5 / B7**
— the day a write must survive an extract. **C5** — clones of one
quantum. ADRs 0005 / 0017, style-decision — worked pick.
`cases/coding-rules/package.md`, `cases/ml-solutions-arch/modular-*` —
cited, not rewritten.

---

## 7. Sources

Retrieved 2026-09-13 unless noted as an in-tree workspace note.

1. Richards & Ford, *Fundamentals of Software Architecture* 2nd ed. — via [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md) (ch7 quantum; ch11 row, when-to, too-big signs). Ford's 2nd-ed note: https://nealford.com/books/SAF2e.html . O'Reilly ch11 landing (body Access Denied): https://www.oreilly.com/library/view/fundamentals-of-software/9781098175504/ch11.html
2. Fowler, "MonolithFirst" (2015-06-03). https://martinfowler.com/bliki/MonolithFirst.html — "MicroservicePremium" (2015-05-13) https://martinfowler.com/bliki/MicroservicePremium.html — "PresentationDomainDataLayering" (2015-08-26) https://martinfowler.com/bliki/PresentationDomainDataLayering.html
3. Simon Brown, modular-monolith / package-by-component. https://simonbrown.je/modular-monolith/ ; GOTO Berlin 2018: https://gotober.com/2018/sessions/515/modular-monoliths ; slides: https://static.simonbrown.je/modular-monoliths.pdf
4. Westeinde, "Deconstructing the Monolith" (2019-02-21). https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity — Müller, "Under Deconstruction" (2020-09-16). https://shopify.engineering/shopify-monolith — McGibbon & Salzberg, "A Packwerk Retrospective" (2024-02-07). https://shopify.engineering/a-packwerk-retrospective
5. Garg / Thoughtworks, "When (modular) monolith is the better way to build software" (2023-06-03). https://www.thoughtworks.com/en-us/insights/blog/microservices/modular-monolith-better-way-build-software
6. Workspace notes listed in the header; `.cursor/skills/arch-style/SKILL.md` (monolith bias; E10 as recommended start).

---

## 8. Uncertain / left out

- **O'Reilly ch11 body** Access Denied 2026-09-13. Ratings / too-big
  signs / when-to recovered only via style-selection
  (`Modular-monolith-arch.md:92-104, 216-239`). That file is **not in
  the main-repo or worktree tree** (search = 0). Any number not in
  style-selection is unverified. Star figures did not survive — do not
  fill cells; do not borrow E7's evolvability 3★. Ch11 mediator /
  peer-to-peer TOC entries: bodies not fetched.
- **Fowler 2015** calls monolith-first **tentative**; the
  start-distributed counter-argument is **unsettled**. Path-1 had few
  success stories *by his own count*.
- **Thoughtworks 2023** holiday extract-and-merge is an author sketch.
- **Dan Manges (2018-01-23)**
  https://medium.com/@dan_manges/the-modular-monolith-rails-architecture-fb1023826fc4
  — Shopify 2019 points at it; primary **timed out** 2026-09-13. No
  Manges numbers used.
- **GOTO 2018 transcript** not fetched (abstract + site + PDF only).
  **Head-count thresholds** (20 / 50 / 150) not on any primary. Library
  versions omitted (no defaults section). Team Topologies pp. 115–123
  not fetched. **Khononov / coupling.dev** not fetched this pass.
