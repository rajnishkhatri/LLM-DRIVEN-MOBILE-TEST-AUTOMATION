---
type: research
title: 'Layered architecture — external research (2026-09-13)'
description: >-
  Source-verified research for catalog E3: n-tier presentation–business–
  persistence–database, closed vs open layers, three physical variants,
  Architecture Sinkhole, quantum count 1, when-to-use vs domain-change
  streams, and the hexagonal (E8) distinction. FSA star ratings remain —.
tags: [research, system-design-patterns, E3, layered]
---

# Layered architecture — external research (2026-09-13)

> Evidence pass for catalog **E3** (Group E). Not a Concept. Fetched
> 2026-09-13; paraphrase; unverified claims in §8.
>
> **Group E bar.** What the style is and is not; quantum count as a
> **FACT** (no scoring micro-loop); when-to-use / when-not; migration
> in/out; worked example; trade-off table; sources. **No
> library-defaults.**
>
> **Workspace gap.**
> [style-selection.md](../../../.claude/skills/arch-style/references/style-selection.md)
> records `LayeredArchStyle.md` as **truncated at 26 lines** (topology
> only). Layered star ratings are `—`. Architecture Sinkhole is only
> **name-checked** there. This note never invents a `—` cell as a
> rating. Sinkhole is recovered from Richards 2015 (§3.5). The truncated
> file itself was **not found** in the main repo or this worktree
> (filename search = 0 files).

---

## 1. Scope and non-goals

**Owns.** Horizontal **technical** partitioning: presentation / business /
persistence / database (n-tier; 3- or 5-layer stacks are the same style);
**closed vs open** layers and layers of isolation; **logical layers vs
physical tiers** (one box vs split); **Architecture Sinkhole**; quantum
**1**; when-to-use (simplicity, technical change) vs when-not (domain
change streams → E10 / services). Ports-and-adapters (E8) is **not**
“more layers.”

| Sibling | Why not this card |
|---|---|
| **E8 Hexagonal** | Inside/outside + ports; DIP so the domain does not depend on a DAL. |
| **E1 Monolith** | The *family*. Layered is one *technical* partitioning of a monolith. |
| **⊕E10 Modular monolith** | Same quantum (1), **domain** modules. Usual exit when change follows the domain. |
| **E5 Client–server** | Who calls whom on a network. A 2-tier split can *host* layers; it does not define them. |
| **E2 / E6 / B4** | Distributed destinations, or how to *leave* a live layered system. |

**Non-goals.** Re-scoring the mobile-test-automation kata (already
rejected layered). OSI network layers. Library defaults. Invented FSA
stars. Rewriting [package.md](../../../cases/coding-rules/package.md) or
[clean-architecture.md](../../../cases/coding-rules/clean-architecture.md).

---

## 2. Lineage / vocabulary

**Buschmann et al., POSA vol. 1 (Wiley, Aug 1996), pattern *Layers*.**
“From Mud to Structure” (with Pipes and Filters, Blackboard). Book and
name confirmed (archived Wiley listing; Calgary POSA table). Chapter
body **not** fetched — opaque vs transparent layers stay Uncertain (§8).

**Fowler, *Layering Principles* (2005-01-07).**
https://martinfowler.com/bliki/LayeringPrinciples.html — workshop vote,
not a standard. Strong yes: low coupling / high cohesion; SoC; no
business logic in UI or inbound handlers; no cycles; layers are
**logical** and do **not** imply distribution (`11/0`); lower does not
depend on upper. Strong no: **teams by layer** (`1/22`); **distribute at
layer boundaries** (`0/18`); rethrow at every boundary (`0/15`). Adjacent-
only: split (`4/4`).

**Fowler, *Presentation Domain Data Layering* (2015-08-26).**
https://martinfowler.com/bliki/PresentationDomainDataLayering.html —
presentation / domain / data-access. Extra layers (service, Presentation
Model) do not break it. Dependencies top → bottom. A mapper that frees
the domain from data sources **is hexagonal**, not a thicker stack.
Logical ≠ physical (laptop; desktop+DB; rich client + BFF-as-
presentation). **Granularity:** once a layer is large, do **not** keep
presentation-domain-data as the top-level modules — split by **domain**,
layer *inside*. Anti-pattern: teams = layers. “Developers don’t have to
be full-stack but teams should be.”

**Richards, *Software Architecture Patterns* (O’Reilly, 2015-08-15).**
https://www.oreilly.com/content/software-architecture-patterns/ — fetched
in full. Layered = **n-tier**. Four standard layers; business+persistence
may collapse (SQL in business) → three; large apps may grow past four.
Closed/open, isolation, open shared-services layer, **Sinkhole + 80/20**,
Low/High analysis (**not** FSA stars).

**Richards & Ford, FSA ch10.** Recoverable from style-selection only: “4
horizontal technical layers; 3 physical variants”; partitioning =
**technical**; quanta = **1**; ratings = `—`. When-to-use is missing.
Secondary notes (jessebellingham 2026-06-18; bagerbach 2025-10-31)
paraphrase the same topology; their star tables are **not** copied as
FSA ratings.

**Microsoft, layers vs tiers.** Azure *N-tier Architecture Style*
https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/n-tier
(fetched 2026-09-13; `ms.date` not recovered). Layers = logical +
one-way dependency; tiers = machines. Closed = next layer down only;
open = any layer below. Several layers on one tier is normal. .NET
*Common web application architectures*
https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures
— UI / BLL / DAL; N-layer on one tier is common; compile-time arrows
UI → BLL → DAL, which is why Clean/hexagonal **inverts** persistence
(E8, not E3).

**Cockburn, *Hexagonal Architecture* (HaT 2005.02, 2005-09-04).**
https://alistair.cockburn.us/hexagonal-architecture — the hexagon exists
**to get away from the one-dimensional layered picture**. Ports
(conversations) + adapters; inside/outside, not up/down. Full card:
**E8**.

| Term | Meaning here |
|---|---|
| **Layer** | Logical band of technically similar components. Not a process. |
| **Tier** | Physical deployment (process / machine / subnet). |
| **Closed / open** | Must enter this layer to go lower / may skip it. |
| **Technical partitioning** | Group by kind of work (UI, rules, SQL), not by domain. |
| **Quantum** | Smallest independently runnable unit; DB is inside it. Shared DB ⇒ 1. |

---

## 3. Mechanics (Group E depth bar)

### 3.1 What the style is — and is not

**Is.** Monolith-family, **technically partitioned**. Usual four
(Richards 2015 + style-selection topology):

| Layer | Responsibility |
|---|---|
| **Presentation** | UI / inbound protocol. Does not know tables or SQL. |
| **Business** | Calculate, aggregate, authorize, decide. |
| **Persistence** | DAOs / SQL / mappers. Hides the dialect. |
| **Database** | The store; often a separate *product* and *tier*. |

A presentation rewrite (Richards: JSP → JSF) leaves business alone **if**
the contract holds. Fowler’s reason to layer even without
substitutability: **narrowed scope of attention**.

**Is not.** (1) **Not E8 / Clean / onion** — those invert so the domain
does not depend on the DAL; classic layered *does*. Fowler’s
domain-freeing mapper *is* hexagonal. Martin’s
[clean-architecture.md](../../../cases/coding-rules/clean-architecture.md)
uses “layers” for concentric policy rings — different rule. (2) **Not
any monolith** — E10 is one quantum partitioned by *domain*; Brown
([package.md](../../../cases/coding-rules/package.md)) notes two layered
codebases from different domains look the same (web / services /
repositories). (3) **Not E5** — 2-tier or 3-tier hosting does not define
the logical layers. (4) **Not OSI**.

### 3.2 Closed vs open (layers of isolation)

Richards 2015: a **closed** layer must be entered to reach anything
below (presentation → business → persistence → database). Isolation
means a SQL change or a UI-framework swap stays in that layer plus its
contract partner; if presentation can reach persistence, a persistence
change hits **both** business and presentation.

**Open on purpose:** a shared-services layer (utilities, audit, logging)
under business so presentation cannot see it. If that layer were
closed, business would have to walk *through* utilities to reach
persistence. Mark it **open** so business may use it *or* skip.
Undocumented open/closed is how the style becomes a ball of mud.

Azure: closed can create **needless network traffic** when a tier only
forwards; open creates **more couplings**. Brown: **strict** = adjacent
only; **relaxed** = may skip (CQRS reads sometimes intended; a
controller injecting a repository and skipping authorization is not).
Package-by-component *enforces* what layered only *states*.

### 3.3 Physical variants (one box vs split)

**FACT (style-selection):** three physical variants. Logical layers need
not map 1:1 to tiers (Fowler, Azure, .NET). Count is FACT; the
*groupings* are reading-note recovery (book figure not in-repo):

| Variant | Deployable grouping | Motive |
|---|---|---|
| **1** | `(presentation + business + persistence)` + **database** | Default app-server + product DB. |
| **2** | `presentation` + `(business + persistence)` + **database** | Split UI (browser / BFF) from business. Extra hop. |
| **3** | All four (DB in-process / in-memory) | Small apps, tests, one box. |

Azure’s VM picture (WAF → web VMSS → business VMSS → SQL, subnet + NSG
so data accepts only business) is a *stricter physical* n-tier, not a
fourth logical layer. Trade-off: scale and a security boundary vs
latency; features still cannot deploy independently. Fowler 2005:
**0/18** against distributing at layer boundaries — a cost, not a
virtue of the style.

### 3.4 Quantum count — FACT = 1

Style-selection matrix: Layered **quanta = 1**. The DB is inside the
quantum; a shared schema keeps one quantum even if presentation is a
separate process (change the schema → the other deployable can break).
Cloning the same app behind a load balancer is still one quantum. Do
**not** score characteristics.

### 3.5 Architecture Sinkhole — verified (Richards 2015)

**Verified** from the O’Reilly 2015-08-15 report, not from the truncated
workspace file.

Requests walk every layer as **pass-throughs**: presentation forwards
“get customer,” business forwards, persistence runs one SQL, data
returns with **no** aggregation, calculation, or transform. Cost:
allocation and latency for no isolation.

Every layered system has some. Richards’s **80/20 heuristic** (not a
dataset): ~20% pass-through / ~80% real work is typical; if the ratio
**reverses**, either **open** some layers (cheaper path, worse change
control) or the style is **wrong** for the domain.

Azure (same phenomenon, no name): a middle tier that only does CRUD
“adds latency and complexity without delivering meaningful value.”

This repo already names sinkhole as the decay mode of technical
partitioning: [style-decision.md](../../architecture/worksheets/mobile-test-automation/style-decision.md)
and ADR 0005 rejected Layered *without* stars (notes truncated);
[rules-catalog.md](../../../tooling/coding-rules-skill/references/rules-catalog.md)
CR-03 forbids layer-named packages (`controllers`, `services`,
`repositories`).

### 3.6 Worked example (Richards 2015 customer retrieve)

Screen → **customer delegate** (knows the business module + contract) →
**customer** business object, which aggregates: **customer DAO** +
**order DAO** each run SQL. Combined model walks back up. Not a
sinkhole when the business object aggregates; is one when “get
customer” is a single table and every layer is a one-line forward.
Technology is incidental (JSF/Spring/JDBC or ASP.NET/ADO).

**Workspace counter-example.** Change streams are domain clusters
(conversion, validation-certification, evidence). Horizontal layers
would spread each change across presentation + business + persistence.
Chosen style: **E10**, not E3.

### 3.7 Trade-off table (no invented FSA stars)

FSA ch10 scorecard: **`—`**. Richards 2015 is a **different** book
(Low/High prose, fetched 2026-09-13), plus Azure / Fowler:

| Concern | Tendency | Trade-off |
|---|---|---|
| **Cost / familiarity** | High (Richards: ease of development High) | Conway match; Azure “less learning curve.” Degrades as the unit grows (secondary; not scored). |
| **Simplicity** | High | Easy start (Fowler). Two domains look identical (Brown). |
| **Technical-change isolation** | High *if closed + contracts hold* | UI or SQL swap can stay local. A domain change touches every layer. |
| **Testability** | Richards 2015: **High** (mock a layer) | .NET e-book: UI→BLL→DAL makes business tests need a DB unless you invert (E8). Sources disagree on *business*-layer testability; both agree you can stub edges. |
| **Deployability** | Richards: **Low** | Three-line change redeploys the unit. Azure: no independent feature deploy. |
| **Performance** | Richards: **Low** | Extra hops; closed + sinkhole = paid latency. Cache or open a layer (each costs isolation). |
| **Scale / elasticity** | Richards scalability: **Low** | Clone the whole app or split a tier. Quantum stays 1. |
| **Agility / domain change** | Richards agility: **Low** | Isolation helps technical churn; the monolith + coupling slow business churn. |
| **Fault isolation** | Weak | One OOM / bad deploy takes the unit. Azure replicas are per *tier*, not per feature. |
| **Physical n-tier security** | Azure strength | Data subnet accepts only business. Cost: hops, ops, harder test/monitor. |

Those Low/High cells are **not** the missing FSA figure.

---

## 4. Verified defaults / standards

**None.** Group E has no library or protocol defaults. Closed/open,
80/20, and “three variants” are style heuristics.

---

## 5. Failure modes and when-not-to-use

### 5.1 When to use

| Fit | Why | Source |
|---|---|---|
| Small / simple / uncertain final style | Cheap start; no distributed tax. “Good starting point… when you are not sure.” | Richards 2015; Azure “requirements still evolving” |
| **Technically** oriented change | Next work is “new screen / new report / swap ORM.” Isolation pays. | Contrast with E10 (not for technical change streams) |
| Lift-and-shift / hybrid | Existing n-tier maps onto Azure VMs with little redesign. | Azure |
| Specialists on **one** team | Code may be layered; teams must not be. | Fowler 2005 / 2015 |

### 5.2 When not

| Anti-fit | Why | Toward |
|---|---|---|
| **Domain-shaped change streams** | Each change edits every layer; sinkhole ratio flips. Fowler: domain modules on top, layers inside. | **E10**, later E6 / E2 |
| Independent feature deploy / scale / FT | Quantum 1; DB in the quantum. Richards deploy/scale Low. | E6 / E2 (pay the fallacies) |
| Domain must not depend on the DB at compile time | Layered points the wrong way. | **E8** *inside* the quantum — not “add a layer” |
| Majority pass-through CRUD | Sinkhole. Opening all layers leaves folders, not isolation. | Collapse layers, or re-partition by domain |
| Teams = layers | Fowler `1/22`. Friction + distance from users. | Cross-functional teams; E10 ownership |
| This workspace’s kata | Technical pipeline modules *are* the sinkhole invitation. Already rejected. | E10 chosen; E6 named migration |

### 5.3 Migration in / out

**In.** Accidental architecture: “just start coding,” packages `web` /
`service` / `dao` (Richards; style-selection names Architecture by
Implication / Accidental Architecture). Framework templates emit
package-by-layer (Brown).

**Out.** (1) Tactical: open pure-sinkhole layers (Richards); accept
weaker isolation. (2) Structural: invert *top-level* modules to domain /
components; keep presentation-domain-data *inside* (Fowler + Brown
package-by-component). (3) Invert the persistence **port** (E8) — still
one quantum. (4) Strangle a live unit (B4). (5) Do **not** jump to
microservices because the layers feel messy (Fowler *Microservice
Premium*; this workspace already named E6 as the first distributed
step).

**Cost.** Every open layer you add to kill sinkholes is coupling you
unwind later. A “just this once” controller → repository skip is
Brown’s relaxed diagram: still acyclic, still wrong.

### 5.4 Other failure modes

Sinkhole majority (ceremony, no isolation). Relaxed layering that skips
authorization (Brown). Public-everything packages — Brown: four “styles”
collapse to the same graph. Distribute every layer (Fowler rejected;
Azure still does it for security and you pay hops). Layer-named
top-level packages on a domain-change product (CR-03 / ADR 0005).
Folders labelled Clean Architecture that still depend downward onto the
DAL (label E8, mechanics E3).

---

## 6. Cross-links

[style-selection.md](../../../.claude/skills/arch-style/references/style-selection.md)
— topology, technical partitioning, quanta = 1, ratings `—`.
[style-decision.md](../../architecture/worksheets/mobile-test-automation/style-decision.md)
+ [ADR 0005](../../architecture/adrs/application/mobile-test-automation/0005-adopt-plain-modular-monolith-partitioned-by-cluster.md)
— Layered rejected; E10 chosen so pipeline stages do not become layers.
[package.md](../../../cases/coding-rules/package.md) — strict/relaxed,
package-by-component. [clean-architecture.md](../../../cases/coding-rules/clean-architecture.md)
— E8 family. Catalog **E8 / E1 / E10 / E5 / B4** as in §1.

---

## 7. Sources (retrieved 2026-09-13)

| Source | URL | Used for |
|---|---|---|
| Richards, *Software Architecture Patterns*, 2015-08-15 | https://www.oreilly.com/content/software-architecture-patterns/ | Four layers; closed/open; isolation; **Sinkhole + 80/20**; customer example; Low/High |
| Fowler, *Presentation Domain Data Layering*, 2015-08-26 | https://martinfowler.com/bliki/PresentationDomainDataLayering.html | Three layers; logical ≠ physical; hexagonal mapper; domain-on-top |
| Fowler, *Layering Principles*, 2005-01-07 | https://martinfowler.com/bliki/LayeringPrinciples.html | Logical layers; do not distribute / team by layer |
| Cockburn, HaT 2005.02, 2005-09-04 | https://alistair.cockburn.us/hexagonal-architecture | Hexagon vs one-dimensional layers (E8) |
| Azure *N-tier Architecture Style* | https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/n-tier | Layers vs tiers; closed/open; CRUD waste; when-to-use |
| .NET *Common web application architectures* | https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures | N-layer on one tier; UI/BLL/DAL; DIP → Clean |
| Workspace style-selection | `.claude/skills/arch-style/references/style-selection.md` | Quanta = 1; 4 layers; 3 variants; ratings `—` |
| Brown (in-tree) | `cases/coding-rules/package.md` | Package-by-layer; strict/relaxed |
| Buschmann et al., POSA vol. 1, Aug 1996 | Wiley listing (archived) | *Layers* name and date only |

Reading notes used **only** for the three physical groupings (not as FSA
stars): jessebellingham ch10
(https://jessebellingham.com/reading-list/books/fundamentals-of-software-architecture/part-2-architecture-styles/chapter-10-layered-architecture-style)
and bagerbach (https://bagerbach.com/books/fundamentals-of-software-architecture/).

---

## 8. Uncertain / left out

- **FSA ch10 star ratings.** Workspace `—`. jessebellingham’s 1–5 table
  is a third-party paraphrase of a missing figure. **Not asserted.**
- **`LayeredArchStyle.md` body.** Cited as :12–26; file **absent**.
  Topology taken from style-selection only.
- **POSA *Layers* internals** (opaque/transparent). Book confirmed;
  chapter not fetched.
- **Azure `ms.date`.** Page fetched; stamp not in the extract.
- **80/20.** Richards heuristic, not a dataset.
- **Physical variant groupings.** Count is FACT; the three
  parentheses-groupings are reading-note consensus.
- **FSA 2nd ed. ch10** (`9781098175504`). Not fetched.
- **“Keep reuse / inheritance shallow to ease later migration.”**
  jessebellingham only — Uncertain as a book claim.
- OSI, MVC-as-layered, Java EE official tier counts, Spring layer
  stereotypes. Left out.
- Scoring this system. Already done; not re-run.

Items in this section are **not** facts for a future Concept.
