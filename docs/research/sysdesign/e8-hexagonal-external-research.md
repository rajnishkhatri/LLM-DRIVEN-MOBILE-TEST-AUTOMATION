---
type: research
title: 'Hexagonal architecture (ports and adapters) — external research (2026-09-13)'
description: >-
  Source-verified research for catalog E8: Cockburn Ports and Adapters
  (hexagonal is the drawing name), application at the center, driving vs
  driven ports, in-memory adapters, Clean/Onion as lineage only, and the
  E3 layered / B4 ACL distinctions. Matrix quantum cell is absent.
tags: [research, system-design-patterns, E8, hexagonal, ports-and-adapters]
---

# Hexagonal = ports-and-adapters — external research (2026-09-13)

> Evidence pass for catalog **E8** (Group E). Not a Concept. Fetched
> 2026-09-13; paraphrase; unverified claims in §8. Group E bar: what
> the style is / is not; quantum as **FACT** only when sourced (no
> scoring micro-loop); when-to / when-not; migration; worked example;
> trade-off table; sources. **No library-defaults.**
> [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md)
> has **no hexagonal row** — do not invent stars or a typical-quanta
> cell. Ch7 quantum *machinery* still applies.

---

## 1. Scope and non-goals

**Owns.** One pattern, **two names** (Cockburn 2005.02): **Ports and
Adapters** (purpose of the parts) and **Hexagonal Architecture** (the
drawing). Application at the center; ports = intent; adapters =
technology; driving vs driven; in-memory test adapters; hosting
without inventing a quantum rating; when-to / migration; one worked
example; trade-off table.

**What it is.** Application on the *inside* talks through ports to
the *outside*. Port = technology-independent conversation; adapter =
technology mapping (GUI, FIT, HTTP, SQL, mock). The app does not
know which adapter is plugged in. Intent (Cockburn 2005-09-04): run
without UI or DB; drive from tests, humans, batch, or programs; keep
working when a store is down; link applications without a human.

**What it is not — sibling ids**

| Id / label | Why it is not this card |
|---|---|
| **E3 Layered** | Technical layers, top→bottom deps, Sinkhole. Two ports *look like* a 3–5 layer stack; people then “do not take the lines seriously.” Hexagon = **inside/outside**, more than two ports. Fowler’s domain-freeing mapper *is* hexagonal — a DIP of layered, not “more layers.” Gold: `e3-layered-external-research.md`. |
| **Clean / Onion** | Lineage only (§2). Martin 2012 lists hexagonal as ancestor, then draws rings + the Dependency Rule. Palermo 2008 names Onion. Microsoft 2021 collapses four names and writes Clean. **One Cockburn card.** |
| **⊕E10 Modular monolith** | Domain modules in one deployable. E8 is how *edges* meet technology. E10 often *uses* E8. |
| **E1 / E2** | Deployability / quantum. Hexagonal can live in either; it does not add a quantum. |
| **B4 ACL** | Evans / Azure: *semantic* translation at a legacy / bounded-context seam. An adapter *can implement* an ACL. ACL is not the style. |
| **E7 Microkernel** | Core + plug-ins; related “swap the outside”; different topology. |
| Nestable “hexagon everywhere” | Cockburn 2022: boundary **only at the technology edge**; **not nestable**. Nestable internals = Component + Strategy. |
| Six sides as a law | “The hexagon is not a hexagon because the number six is important” (2005). Room to draw ports. |

**Non-goals.** Library defaults. Arch-style scoring. Invented FSA
stars. A Clean / Onion Concept. Copying *Hexagonal Architecture
Explained* (2024/2025). Starting a skill family.

---

## 2. Lineage / vocabulary

**Cockburn, HaT TR 2005.02, 2005-09-04 (v 0.9).**
https://alistair.cockburn.us/hexagonal-architecture — fetched
2026-09-13. **Canon.** Pattern: **Ports and Adapters (Object
Structural)**; alternative name: **Hexagonal Architecture**. Intent,
inside/outside, port-as-conversation, many adapters per port, FIT +
mock sequence, primary/secondary = driving/driven, use cases at the
inner hexagon, typical port count 2–4, weather-alert known use, GoF
Adapter as the mechanism. Same page cites FIT, Pedestal, Checks,
Martin DIP (2003), Fowler DI, Freeman mocks, Loopback.

**Cockburn 2022 index.**
https://alistaircockburn.com/Articles/Hexagonal-Architecture —
“Original… / January, 2005”; “still valid”; 2022 “major meme.” Date
tension with 2005-09-04 → §8.

**Cockburn, HaT TR 2022.01 (v3a, 2023-06-01).**
https://alistaircockburn.com/Component%20plus%20strategy.pdf —
Ports & Adapters = Component + Strategy with the boundary “just in
front of external technologies.” **Not nestable.** No tests on
**both** sides (driving harness + driven double) makes his “blood
freeze.” **Configurator** (composition root) is outside the pattern
definition. UML Provided = driving; Required = driven.

**Fowler, *Presentation Domain Data Layering* (2015-08-26).**
https://martinfowler.com/bliki/PresentationDomainDataLayering.html —
Default deps presentation → domain → data. A mapper so the domain
does **not** depend on data sources “is often referred to as a
**Hexagonal Architecture**” — a *variation of layering*, not a new
top-level cut. Large systems should split top-level by **domain**
(E10), layer *inside*.

**Palermo, Onion part 1 (2008-07-29) / part 4 (2013-08-19).**
https://jeffreypalermo.com/2008/07/the-onion-architecture-part-1/ —
Rings; coupling toward the center; database *external*. Shared
premise with hexagonal: “Externalize infrastructure and write
adapter code.” **Not appropriate for small websites.** Part 4:
independent object model; inner layers define interfaces; coupling
toward center; core runs without infrastructure. **Lineage, not a
second card.**

**Martin, *The Clean Architecture* (2012-08-13).**
https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
— Hexagonal first among ancestors (GOOS, Onion, DCI, BCE). Then
**Dependency Rule** (deps only inward) and four schematic circles.
Use-case **output port** = a driven port. Workspace:
[`clean-architecture.md`](../../../cases/coding-rules/clean-architecture.md).
**Lineage, not a second card.**

**Microsoft .NET *Common web application architectures*.**
https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures
— `ms.date` 2021-12-12. N-layer compile-time deps **top → bottom**
(BLL depends on DAL). DIP + DDD “has gone by many names…
Hexagonal… Ports-and-Adapters… Onion… or Clean”; the e-book then
**uses Clean**. For monoliths, Core + Infrastructure + UI “are all
run as a single application.”

**Brown, *package.md*.** Inside (domain) / outside (infrastructure);
outside depends inward. “View order status” in §3.5. Two infra trees
invite the **Périphérique** skip (controller → repository).
Package-by-component is his E10-shaped enforcement.

**Book, cite-only.** Cockburn & Garrido de Paz, *Hexagonal
Architecture Explained* (preview 2024-05-08; updated ed. listed
2025-04-15). Mechanics from the 2005 report and 2022 TR, not the
book.

**Vocabulary.** **Inside** = application/domain. **Port** = purposeful
conversation (API; many adapters). **Adapter** = GoF mapping at that
port. **Driving / primary** = actor drives the app; **driven /
secondary** = app drives a collaborator. **Configurator** =
composition root (outside the pattern definition).

---

## 3. Mechanics (Group E depth bar)

### 3.1 Topology — application at the center

```
                    driving adapters
                 (FIT, GUI, HTTP, CLI)
                          |
                          v
                 +--------port--------+
                 |                    |
     other  ---->|   APPLICATION      |---->  driven adapters
     ports       |   (inner hexagon)  |      (SQL, file, mock,
                 |                    |       email, coin box)
                 +--------------------+
```

Inside = application/domain (use cases written here). Port = “a
purposeful conversation” (an API). Adapter = technology mapping
(dev/test/prod DBs may be three adapters on one port). Outside =
humans, programs, devices, stores — symmetric at the architecture
level.

**Left–right is implementation, not the architectural pretense.**
Cockburn 2005: **primary / secondary**, “also called **driving**
adapters and **driven** adapters.”

| Side | Also called | Who is in charge | Natural test stand-in |
|---|---|---|---|
| Primary | Driving | An actor *drives* the app (use-case primary actor) | Scripted driver (FIT / FitNesse in 2005; any API harness) |
| Secondary | Driven | The app *drives* a collaborator (use-case secondary actor) | Mock / in-memory substitute / Loopback |

Draw driving on the left (or top), driven on the right (or bottom)
to match a use-case context diagram. Do **not** short-circuit the
pattern into “FIT on the left, mocks on the right” and skip the
isolation goal.

**Provided vs required (2022 vocabulary).** Driving adapters call
the application’s *provided* interface. The application calls
*required* interfaces; driven adapters implement them. Wiring is
the Configurator. Microsoft 2021: the UI project may reference
Infrastructure *only* so startup can bind interfaces — “limit
actual references… to the app’s composition root.”

### 3.2 Why the hexagon (and why two ports lie)

Many apps have only two ports (user dialog, database dialog). That
*looks* like a layered stack. Two problems (Cockburn 2005):

1. People do not treat layer lines as real, so logic leaks — the
   organization adds “one more layer” with the same promise, and a
   few years later the new layer is also contaminated.
2. There may be **more than two** ports, so the architecture does
   not fit a one-dimensional drawing.

The hexagon shows inside/outside and leaves room for 2–4 ports
(“four is most I have encountered to date” — personal count, §8).
Taste: neither “one port per use case” nor “one left + one right”
is optimal. Known uses: weather = four (feed, admin, notified
subscribers, subscriber DB); coffee machine = four; hospital
medication = three. “No particular damage” in choosing the “wrong”
number.

**Name ports by purpose, not technology.** Weather-alert started
as wire-feed / answering-machine / GUI / SQL interfaces; HTTP in +
email out looked like a permutation explosion. Shift: trigger in,
notify out, administration, subscriber data. New adapters plug in.

### 3.3 Testability via in-memory adapters

Cockburn’s isolation goal is operational, not decorative: the app
must run with a driving harness and a driven double so regression
tests do not need a UI or a database. Stage 1 of the Discounter
sample is FIT + a constant rate; Stage 3 replaces the constant with
`MockRateRepository` in memory. Microsoft 2021: because Application
Core does not depend on Infrastructure, unit tests of the core need
no database. Cockburn 2022: interfaces without tests on **both**
sides are not a component.

Trade-off: you must *write and keep* those tests. Nested hexagons
duplicate system tests until the inner ones die (Cockburn 2022).

### 3.4 Quantum count — no matrix FACT

[`style-selection.md`](../../../.cursor/skills/arch-style/references/style-selection.md)
does **not** list hexagonal. There is no typical-quanta cell and no
star row. A `—` cell is not a rating; an **absent** row is not a
3★. **Do not score.**

Ch7 machinery still applies: architecture quantum = smallest
independently runnable part; **the database is part of the quantum
— single shared DB ⇒ quantum of one**.

| Hosting | What is sourced | What is not |
|---|---|---|
| Hexagon = the monolith | Microsoft 2021: Core + Infrastructure + UI “are all run as a single application”; “Externally, it’s a single container with a single process.” Fowler 2015: the hexagonal mapper is a *module*, “not necessarily” separately deployable. Cockburn’s Discounter is one process. Applying ch7: one deployable + shared DB ⇒ **quantum 1**. | A style-level “E8 quanta = 1” matrix fact. |
| Each microservice is a hexagon | E2 already owns “most quanta of any style” (style-selection ch18) when services are independently deployable with DB-per-service. Hexagonal *inside* those services does not create the extra quanta. | A sourced claim that *E8* has many quanta. Uncertain as an E8 property (§8). |

Replicas behind a load balancer are more instances of the **same**
quantum. Distributing UI / domain / persistence as three network
services is E3’s rejected “distribute at layer boundaries” wearing
hexagon labels; a shared DB still ⇒ one quantum.

### 3.5 Worked example — Cockburn’s Discounter (2005)

Paraphrase of the report’s sample (Gyan Sharma / IHC). Two ports:
amount from a user; rate from a store.

`discount(amount) = amount * rate(amount)`

**Stage 1.** FIT HTML table (`amount` / `discount()`) drives a
fixture that constructs `Discounter`. No GUI, no DB — the fixture
*is* the driving adapter. **Stage 2.** A GUI listener calls the
same `discount`. Two driving adapters, one port. **Stage 3.**
`RateRepository.getRate(amount)` is owned by the app.
`MockRateRepository` is in-memory (≤100 → 0.01, ≤1000 → 0.02, else
0.05) and injected via constructor (or a later real adapter).

Whole pattern at smallest size: **swappable driving adapters; one
driven port with mock + real; app ignorant of both technologies.**
Brown’s “view order status” (`package.md`): `domain`/`Orders`
inside; outside depends inward — same arrow as the driven port.

### 3.6 Trade-off table (no invented FSA stars)

No FSA scorecard exists for this style. These are source-backed
trade-offs of *choosing* E8 as the internal shape.

| Dimension | Pays you | Costs you | Source |
|---|---|---|---|
| Testability of rules | App runs with a driving harness and driven doubles; no UI/DB required | You must *write and keep* those tests or the boundary is fiction | Cockburn 2005 intent; 2022 “blood freeze” |
| Technology change | Swap SQL / HTTP / GUI adapters without rewriting the inner API | Mapper / DTO tax at every crossing; ports that leak ORM types give none of the benefit | Cockburn weather use; Martin “what data crosses” |
| Dependency direction | Domain does not compile against the store or the framework | Composition root must see both sides; easy to “cheat” from UI → infra (Brown Périphérique) | Fowler 2015 mapper; Microsoft 2021 composition root |
| Isolation vs hops | Purpose-named ports stop permutation versions of the app | Extra types per port; a hexagon around CRUD is E3’s sinkhole plus ceremony | Cockburn 2005; E3 sinkhole |
| Quantum / ops | Adds **no** network and **no** independent scale by itself | Does **not** buy feature-deploy, elasticity, or fault isolation | ch7 machinery; Microsoft single-process runtime |
| Scope of the ring | One technology-edge hexagon is a maintainable system-test wall | Nested hexagons duplicate tests until they die | Cockburn 2022 |
| Team shape | Cross-functional team owns a domain + its adapters | Ring-shaped teams recreate Fowler’s layer-team antipattern | Fowler 2015 |
| Versus ACL | Adapter *can* translate | If the problem is two *models*, you need an ACL, not another port name | Azure 2026-05-28; B4 |

---

## 4. Verified defaults / standards

**None.** Group E has no library or protocol defaults. Port-count
intuition (2–4) and “not nestable” are heuristics, not knobs.

---

## 5. Failure modes and when-not-to-use

### 5.1 When to use

| Fit | Why | Source |
|---|---|---|
| Headless regression tests; store down or replaced; same API from humans / batch / programs; more than two conversations | Isolation is the intent; layered drawing does not fit | Cockburn 2005 |
| Domain must not compile against the DAL | Mapper / DIP variation | Fowler 2015; Microsoft 2021 |
| Long-lived business app; data-access fashion will change | Externalize infrastructure | Palermo 2008 |
| Module edges of an E10 monolith | Usual home | Brown; E10 sibling |

### 5.2 When not

| Anti-fit | Why | Toward |
|---|---|---|
| Small website / simple CRUD; ceremony exceeds the domain | Palermo: Onion “not appropriate for small websites”; Microsoft “all-in-one” | Stay E3, or a single project |
| Majority pass-through (E3 sinkhole reversed) | A hexagon around a no-op use case is more hops, not more isolation | Collapse layers, or re-partition by domain (E10) |
| Nestable *internal* components with their own tests | E8 is not nestable | Component + Strategy (Cockburn 2022), or E10 package-by-component |
| Change is domain-shaped and top-level packages are still `web` / `services` / `repositories` | Fowler: domain modules on top, layers *inside* | E10 first; add E8 *inside* modules if the DAL still owns the domain |
| Independent feature deploy or extra quanta | E8 will not give you that | E6 then E2; B4 to cut over |
| The real problem is a *legacy semantic* boundary | Translation at a model seam, not a style | **B4 ACL**. Azure: facade/adapter between different models; do not put business rules in the ACL |
| Teams would be split by rings (UI / domain / infra) | Same Conway failure Fowler rejected for layers | Cross-functional teams; domain modules |

### 5.3 Migration in / out

**In.** Invert the data dependency (cheapest E3 → E8: Fowler’s
mapper / Cockburn Stage 3) — no new quantum. Publish the driving
API and put the UI outside (Stage 1–2; MVC/MVP already do the
*primary* side only). Name ports by purpose (weather). Inside E10,
each module owns ports; adapters live in delivery. Partial
adoption: one or two driven ports, no full ring.

**Out.** Thicken domain modules (E10) and enforce with the
compiler. Collapse unused ports. Strangle a *domain slice* (B4),
not a port-ring — a network client is E2/E6 and pays ch9
fallacies; ACL if models differ. Do **not** distribute the hexagon.

**Configurator is the seam.** Tests wire (app + driver + double);
production wires (app + UI + real adapters). Inner hexagon stays.

### 5.4 Other failure modes

Logic leak into GUI or SQL (Cockburn’s original bugaboo). Hexagon
without tests on both sides. Nested hexagons. Port = technology
(`HttpPort`, `SqlPort`). Hundreds of ports. DAL-shaped “port” that
returns ORM entities / row types (Martin: do not pass row
structures inward). Distributed hexagon. ACL confusion — legacy
schema leaked into the domain “because we have an adapter.”
Périphérique skip (Brown). Team-per-ring.

---

## 6. Cross-links

[style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md)
— **no E8 row**; ch7 only; **do not score**.
[e3-layered-external-research.md](e3-layered-external-research.md)
— layers vs ports. **E3 is not this card.**
[b4-strangler-fig-external-research.md](b4-strangler-fig-external-research.md)
— ACL at a legacy seam (Azure `ms.date` 2026-05-28).
[e1-monolith-external-research.md](e1-monolith-external-research.md)
— internal shape, still one quantum when hosted as E1.
[`package.md`](../../../cases/coding-rules/package.md) /
[`clean-architecture.md`](../../../cases/coding-rules/clean-architecture.md)
— Brown inside/outside; Martin rings (lineage).
[style-decision.md](../../architecture/worksheets/mobile-test-automation/style-decision.md)
+ [ADR 0005](../../architecture/adrs/application/mobile-test-automation/0005-adopt-plain-modular-monolith-partitioned-by-cluster.md)
— Layered rejected; E10 chosen. Catalog **E8 / E3 / E10 / E1 / E2 / B4 / E7**.

---

## 7. Sources (retrieved 2026-09-13)

| Source | URL | Used for |
|---|---|---|
| Cockburn, HaT TR 2005.02, 2005-09-04 | https://alistair.cockburn.us/hexagonal-architecture | Both names; inside/outside; driving/driven; Discounter; weather; port count |
| Cockburn 2022 index | https://alistaircockburn.com/Articles/Hexagonal-Architecture | “January, 2005” label; still valid; 2022 meme |
| Cockburn, HaT TR 2022.01 v3a, 2023-06-01 | https://alistaircockburn.com/Component%20plus%20strategy.pdf | Not nestable; tests both sides; Configurator; Provided/Required |
| Fowler, *Presentation Domain Data Layering*, 2015-08-26 | https://martinfowler.com/bliki/PresentationDomainDataLayering.html | Hexagonal = mapper variation of layering; domain-on-top |
| Palermo, Onion part 1, 2008-07-29 | https://jeffreypalermo.com/2008/07/the-onion-architecture-part-1/ | Shared premise; not for small websites |
| Palermo, Onion part 4, 2013-08-19 | https://jeffreypalermo.com/2013/08/onion-architecture-part-4-after-four-years/ | Four tenets |
| Martin, *The Clean Architecture*, 2012-08-13 | https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html | Ancestor list; Dependency Rule; output port |
| .NET *Common web application architectures* | https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures | Names collapsed; N-layer vs DIP; single-process monolith (`ms.date` 2021-12-12) |
| Azure *Anti-Corruption Layer* | https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer | ACL ≠ style; translate models; no business rules (`ms.date` 2026-05-28) |
| Workspace style-selection | `.cursor/skills/arch-style/references/style-selection.md` | Hexagonal **absent**; ch7 quantum machinery |
| Brown (in-tree) | `cases/coding-rules/package.md` | Inside/outside; Périphérique |
| Martin (in-tree) | `cases/coding-rules/clean-architecture.md` | Rings — lineage |

**Book bibliographic only.**
https://books.google.com/books/about/Hexagonal_Architecture_Explained.html?id=Eim20AEACAAJ
(2024-05-08 preview).

---

## 8. Uncertain / left out

- **Typical quantum count of style E8.** Matrix row **absent**.
  Monolith hosting ⇒ quantum 1 is ch7 + Microsoft’s single-process
  picture, not an FSA cell. “Many when each microservice is a
  hexagon” is **E2’s** count. **Not a style FACT.**
- **Essay dates.** Canon **2005-09-04** vs index **January, 2005**.
  Do not collapse to “April 2005.”
- **FSA stars for hexagonal.** No row. Do not back-fill.
- **Book body.** Bibliographic only.
- **“Four is most I have encountered.”** Personal 2005 count, not
  a maximum.
- **80/20.** None found for hexagonal; do not borrow E3’s
  sinkhole heuristic.
- **Microsoft Hexagonal = Onion = Clean.** Family evidence, not
  identity. One Cockburn card.
- **GOOS, Pedestal, C2 wiki, Fowler hexagonal bliki, Azure style
  page for hexagonal** — not fetched / do not exist. Do not invent.
- **Scoring micro-loop** — not run.

Items in this section are **not** facts for a future Concept.
