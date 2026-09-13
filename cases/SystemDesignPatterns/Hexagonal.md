---
type: reference
title: 'Hexagonal architecture (ports and adapters)'
description: >-
  One pattern, two names (Cockburn): application at the center, ports as
  conversations, adapters as technology. Driving vs driven; domain is the
  dependency sink. Not layered (layers keep the store as sink), not a sidecar
  (adapter is in-process), not a modular monolith (E10 is the domain cut).
  Covers lineage, mechanics, test doubles, when-not-to-use, and migration.
tags: [system-design-patterns, architecture, hexagonal, ports-and-adapters]
---

# Hexagonal architecture (ports and adapters)

**See also:** [layered architecture (E3)](LayeredArchitecture.md) · [modular monolith (E10)](ModularMonolith.md) · [sidecar (B6)](Sidecar.md) · [strangler fig / ACL (B4)](StranglerFig.md) · [monolithic architecture (E1)](Monolith.md) · [package by component](../coding-rules/package.md) · [clean architecture](../coding-rules/clean-architecture.md) · [style-selection matrix](../../.cursor/skills/arch-style/references/style-selection.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/e8-hexagonal-external-research.md)

Hexagonal architecture is **one pattern with two names**. Cockburn (HaT TR 2005.02, 2005-09-04) named the parts **Ports and Adapters** and the drawing **Hexagonal Architecture**. The application sits on the *inside* and talks through **ports** (technology-independent conversations) to the *outside*. An **adapter** is the GoF mapping at that port — GUI, HTTP, FIT, SQL, file, mock. The inner hexagon does not know which adapter is plugged in. Intent, stated as operational isolation: run without a UI or a database; drive the same API from tests, humans, batch, or programs; keep working when a store is down; link applications without a human in the loop.

The hexagon is not a hexagon because six is important. It is a drawing that shows **inside / outside** and leaves room for more than two conversations. Two ports *look like* a layered stack; that resemblance is how the styles get collapsed. They are not the same cut.

Quality attributes in play: **testability of rules** (the app runs with a driving harness and driven doubles — no UI/DB required); **technology-change isolation** (swap SQL / HTTP / GUI without rewriting the inner API); **maintainability** at the technology edge (purpose-named ports stop a permutation of “versions of the app”). The costs are a mapper / DTO tax at every crossing, a composition root that must see both sides, extra types per port, and **no** extra quantum — the style buys neither feature-deploy, elasticity, nor fault isolation.

## What it is not

Nearby cards share a word, a drawing, or a quantum. They are not this style.

| Style | Cut | Dependency rule | When it wins |
|---|---|---|---|
| **E8 Hexagonal (this card)** | Inside / outside: *ports* (conversations) + *adapters* (technology) | Inward. The domain is the **sink**. | The domain must not compile against a DAL; more than two conversations; headless regression. |
| **[E3 Layered](LayeredArchitecture.md)** | Horizontal *technical* bands | Top → bottom. Persistence / database is the **sink**. | Change is technical (new screen, new report, swap ORM). |
| **[E10 Modular monolith](ModularMonolith.md)** | Vertical *domain* modules, one deployable | Module APIs. Same hosting quantum as E1. E8 is how *edges* meet technology; E10 often *uses* E8. | Change follows the domain. |
| **[B6 Sidecar](Sidecar.md)** | App *process* + helper *process*, co-scheduled | Out-of-process. Burns’s “adapter” sidecar *normalizes a container’s output*. Cockburn’s adapter is a **code module** in the same process. | Extensibility when the app has no plugin API; mesh / shipper placement. |
| **E7 Microkernel** | Core + plug-ins the core loads | Related “swap the outside”; different topology (plugin API, typically same address space). | Host that *has* a plugin contract. |
| **[B4 ACL](StranglerFig.md)** | *Semantic* translation at a legacy / bounded-context seam | An adapter *can implement* an ACL. ACL is not the style. Azure: facade between different models; do not put business rules in the ACL. | Two *models*, not two technologies. |
| **E1 / E2** | Deployability / quantum | Hexagonal can live in either; it does not add a quantum. | — |

**Clean / Onion are lineage, not a second card.** Martin (2012) lists hexagonal first among ancestors, then draws rings and the Dependency Rule (deps only inward). Palermo (2008) names Onion — “externalize infrastructure and write adapter code.” Microsoft (2021) collapses four names and then *uses Clean*. Folders labelled Clean whose compile-time arrows still run down onto a DAL are **E3 mechanics under an E8 name**.

**Not nestable.** Cockburn 2022: the boundary sits **only at the technology edge**. Nestable internals are Component + Strategy. Nested hexagons duplicate system tests until the inner ones die.

## Lineage and vocabulary

- **Cockburn, HaT TR 2005.02, 2005-09-04 (v 0.9).** Canon. Pattern: Ports and Adapters (Object Structural); alternative name: Hexagonal Architecture. Inside/outside; port-as-conversation; many adapters per port; primary/secondary = driving/driven; use cases at the inner hexagon; FIT + mock sequence; weather-alert known use. Do not collapse the date to “April 2005” (the 2022 index says “January, 2005”).
- **Cockburn, HaT TR 2022.01 (v3a, 2023-06-01).** Ports & Adapters = Component + Strategy with the boundary “just in front of external technologies.” **Not nestable.** No tests on **both** sides (driving harness + driven double) makes his “blood freeze.” **Configurator** (composition root) is outside the pattern definition. UML Provided = driving; Required = driven.
- **Fowler, *Presentation Domain Data Layering* (2015-08-26).** Default deps presentation → domain → data. A mapper so the domain does **not** depend on data sources “is often referred to as a Hexagonal Architecture” — a *variation of layering*, not a new top-level cut. Large systems should split top-level by **domain** (E10), layer *inside*.
- **Palermo, Onion (2008 / 2013).** Rings; coupling toward the center; database *external*. **Not appropriate for small websites.** Lineage.
- **Martin, *The Clean Architecture* (2012-08-13).** Ancestor list; Dependency Rule; use-case **output port** = a driven port. Workspace write-up: [clean-architecture.md](../coding-rules/clean-architecture.md).
- **Microsoft .NET *Common web application architectures*** (`ms.date` 2021-12-12). N-layer compile-time deps top → bottom (BLL depends on DAL). DIP + DDD “has gone by many names… Hexagonal… Ports-and-Adapters… Onion… or Clean.” For monoliths, Core + Infrastructure + UI “are all run as a single application.”
- **Brown, [package.md](../coding-rules/package.md).** Inside (domain) / outside (infrastructure); outside depends inward. Two infra trees invite the **Périphérique** skip (controller → repository).

| Term | Meaning here |
|---|---|
| **Inside / inner hexagon** | Application / domain. Use cases are written here. |
| **Port** | A purposeful conversation (an API). Many adapters may plug into one port. Named by *purpose*, not technology. |
| **Adapter** | GoF mapping at that port. Dev / test / prod stores may be three adapters on one port. |
| **Driving / primary** | An actor *drives* the app (use-case primary actor). Natural stand-in: a scripted driver. |
| **Driven / secondary** | The app *drives* a collaborator (use-case secondary actor). Natural stand-in: mock / in-memory / Loopback. |
| **Provided / Required (2022)** | Driving adapters call the application’s *provided* interface. The application calls *required* interfaces; driven adapters implement them. |
| **Configurator** | Composition root. Wires adapters. Outside the pattern definition. |
| **Quantum** | Smallest independently runnable unit. The database is inside it. Shared schema ⇒ 1. Hexagonal does not add one. |

## Decision mechanics

### Application at the center

```
                    driving adapters
                 (FIT, GUI, HTTP, CLI)
                          |
                          v
                 +--------port--------+
                 |                    |
     other  ---->|   APPLICATION      |---->  driven adapters
     ports       |   (inner hexagon)  |      (SQL, file, mock,
                 |                    |       email)
                 +--------------------+
```

Outside = humans, programs, devices, stores — **symmetric** at the architecture level. Left–right is implementation, not the architectural pretense: draw driving on the left (or top) and driven on the right (or bottom) to match a use-case context diagram. Do **not** short-circuit the pattern into “FIT on the left, mocks on the right” and skip the isolation goal.

Wiring is the Configurator. Microsoft 2021: the UI project may reference Infrastructure *only* so startup can bind interfaces — “limit actual references… to the app’s composition root.”

### Driving vs driven

| Side | Also called | Who is in charge | Natural test stand-in |
|---|---|---|---|
| Primary | Driving | An actor *drives* the app | Scripted driver (FIT / FitNesse in 2005; any API harness) |
| Secondary | Driven | The app *drives* a collaborator | Mock / in-memory substitute / Loopback |

The isolation goal is operational, not decorative. Stage 1 of Cockburn’s Discounter is FIT + a constant rate. Stage 3 replaces the constant with `MockRateRepository` in memory. Microsoft 2021: because Application Core does not depend on Infrastructure, unit tests of the core need no database. Interfaces without tests on **both** sides are not a component (Cockburn 2022). Trade-off: you must *write and keep* those tests or the boundary is fiction.

### Layers vs inverted ports (the E3 decision)

This is the E3 / E8 decision, not a drawing preference. [Layered](LayeredArchitecture.md) already draws it; the sink is the fact.

```
  Layered (E3)                         Hexagonal (E8)
  source                               source
    │  Presentation                      │  HTTP / UI adapter
    ▼                                    ▼
    │  Business                     inbound port
    ▼                                    ▼
    │  Persistence                     Domain  ← sink
    ▼                                    ▼
  sink  Database                    outbound port
                                         ▼
                                      SQL adapter
```

In classic layered, compile-time arrows run UI → BLL → DAL. **Presentation is the source. Persistence / database is the sink.** A store swap ripples up; business-layer tests need a database *unless* you invert.

Hexagonal **moves the sink**. Ports sit on the inside; adapters are the source; the domain depends on no DAL. Fowler is explicit: a mapper that frees the domain from data sources **is hexagonal**, not a thicker layered stack. Adding a “service layer” or an “application layer” does not invert anything — the sink is still the store.

Two ports *look like* a 3–5 layer stack. Cockburn wrote the hexagon **to get away from** that one-dimensional picture, for two reasons: (1) people do not treat layer lines as real, so logic leaks, and the organization adds “one more layer” with the same promise; (2) there may be **more than two** ports, so the architecture does not fit a stacked drawing.

Choose E3 when you accept the sink at the database (technical change, small unit, one team). Choose E8 *inside* the same quantum when the domain must not depend on a store at compile time. That is not “add a layer.”

| Question | E3 | E8 | E10 |
|---|---|---|---|
| Where do top-level modules come from? | Kind of work (UI, rules, SQL) | Inside vs outside (ports) | Domain / cluster |
| Where do compile-time arrows end? | DAL / database | Domain | Module API (hexagon may live *inside*) |
| What change is cheap? | New screen, new report, swap ORM | Swap an adapter (HTTP, SQL, test) | New or changed domain behavior |
| What change is expensive? | A use case that spans every band | A port that was drawn too wide | A technical swap that cuts every module |
| Same quantum? | 1 | Lives in 1 (does not add one) | 1 |

### Sidecar is a different adapter (the B6 decision)

[Sidecar](Sidecar.md) is *placement*: a helper **process** scheduled with the app and dying with it. Cockburn’s adapter implements a port **in process**. Burns’s 2015 adapter sidecar *normalizes a container’s output* (metrics exporter, log shape). Same English word, three cuts. A hexagonal rewrite and a sidecar can coexist — one is how the code is structured, the other is how a helper is deployed. Do not treat a mesh proxy as a driven port, and do not treat an in-process SQL mapper as a sidecar.

### Name ports by purpose, not technology

Weather-alert started as wire-feed / answering-machine / GUI / SQL interfaces. HTTP in + email out then looked like a permutation explosion. Shift: trigger in, notify out, administration, subscriber data. New adapters plug in; the inner API does not grow a technology name.

Cockburn’s 2005 personal count: typical apps show **2–4** ports (“four is most I have encountered to date”). That is not a maximum and not a law. Taste: neither “one port per use case” nor “one left + one right” is optimal. Known uses in the report: weather = four, coffee machine = four, hospital medication = three. “No particular damage” in choosing the “wrong” number. A `HttpPort` / `SqlPort` has already lost.

Ports that leak ORM types or row structures inward give none of the benefit (Martin: do not pass row structures inward).

### Quantum count — no matrix FACT

[style-selection.md](../../.cursor/skills/arch-style/references/style-selection.md) has **no hexagonal row**. There is no typical-quanta cell and no star scorecard. An absent row is not a 3★. **Do not score.**

Ch7 machinery still applies: architecture quantum = smallest independently runnable part; **the database is part of the quantum — single shared DB ⇒ quantum of one**.

| Hosting | What is sourced | What is not |
|---|---|---|
| Hexagon = the monolith | Microsoft 2021: Core + Infrastructure + UI “are all run as a single application”; “Externally, it’s a single container with a single process.” Fowler 2015: the hexagonal mapper is a *module*, “not necessarily” separately deployable. Cockburn’s Discounter is one process. One deployable + shared DB ⇒ **quantum 1**. | A style-level “E8 quanta = 1” matrix fact. |
| Each microservice is a hexagon | E2 already owns “most quanta of any style” when services are independently deployable with DB-per-service. Hexagonal *inside* those services does not create the extra quanta. | A sourced claim that *E8* has many quanta. |

Replicas behind a load balancer are more instances of the **same** quantum. Distributing UI / domain / persistence as three network services is E3’s rejected “distribute at layer boundaries” wearing hexagon labels; a shared DB still ⇒ one quantum.

## Worked example — Cockburn’s Discounter (2005)

Paraphrase of the report’s sample (Gyan Sharma / IHC). Two ports: amount from a user; rate from a store.

`discount(amount) = amount * rate(amount)`

| Stage | Driving | Driven | What it proves |
|---|---|---|---|
| **1** | FIT HTML table (`amount` / `discount()`) constructs `Discounter`. No GUI, no DB — the fixture *is* the driving adapter. | Constant rate | The app runs headless. |
| **2** | A GUI listener calls the same `discount`. | Still constant | Two driving adapters, one port. |
| **3** | Same driving adapters. | `RateRepository.getRate(amount)` owned by the app. `MockRateRepository` in-memory (≤100 → 0.01, ≤1000 → 0.02, else 0.05), injected. A later real adapter plugs the same port. | Swappable driven adapter; app ignorant of both technologies. |

Whole pattern at smallest size: **swappable driving adapters; one driven port with mock + real; app ignorant of both technologies.** Brown’s “view order status”: `domain`/`Orders` inside; outside depends inward — same arrow as the driven port.

This workspace’s chosen cut is **E10**, not a hexagon-as-top-level-packages: [ADR 0005](../../docs/architecture/adrs/application/mobile-test-automation/0005-adopt-plain-modular-monolith-partitioned-by-cluster.md) rejected Layered; domain clusters own the top-level modules. E8 is available *inside* a cluster if that cluster’s domain must not compile against a store.

## When to use

| Fit | Why |
|---|---|
| Headless regression; store down or replaced; same API from humans / batch / programs; more than two conversations | Isolation is the intent; the layered drawing does not fit (Cockburn 2005). |
| Domain must not compile against the DAL | Fowler’s mapper / DIP variation. |
| Long-lived business app; data-access fashion will change | Externalize infrastructure (Palermo 2008). |
| Module edges of an E10 monolith | Usual home. Each module owns ports; adapters live in delivery. |

## When not to use

| Anti-fit | Why | Toward |
|---|---|---|
| Small website / simple CRUD; ceremony exceeds the domain | Palermo: Onion “not appropriate for small websites”; Microsoft “all-in-one.” | Stay E3, or a single project. |
| Majority pass-through (E3 sinkhole reversed) | A hexagon around a no-op use case is more hops, not more isolation. | Collapse layers, or re-partition by domain (E10). |
| Nestable *internal* components with their own tests | E8 is not nestable. | Component + Strategy (Cockburn 2022), or E10 package-by-component. |
| Change is domain-shaped and top-level packages are still `web` / `services` / `repositories` | Fowler: domain modules on top, layers *inside*. | E10 first; add E8 *inside* modules if the DAL still owns the domain. |
| Independent feature deploy or extra quanta | E8 will not give you that. | E6 then E2; B4 to cut over. |
| The real problem is a *legacy semantic* boundary | Translation at a model seam, not a style. | **B4 ACL**. Do not put business rules in the ACL. |
| Teams would be split by rings (UI / domain / infra) | Same Conway failure Fowler rejected for layers. | Cross-functional teams; domain modules. |
| “We’ll put the HTTP client in its own hexagon on the network” | Distributing the hexagon pays the fallacies and does not add a quantum if the DB is still shared. | Keep the hexagon in-process; strangle a *domain slice* if you must leave. |

## Migration in / out

**In.** Invert the data dependency (cheapest E3 → E8: Fowler’s mapper / Cockburn Stage 3) — no new quantum. Publish the driving API and put the UI outside (Stage 1–2; MVC/MVP already do the *primary* side only). Name ports by purpose (weather). Inside E10, each module owns ports; adapters live in delivery. Partial adoption is allowed: one or two driven ports, no full ring.

**Out.** Thicken domain modules (E10) and enforce with the compiler. Collapse unused ports. Strangle a *domain slice* (B4), not a port-ring — a network client is E2/E6. ACL if models differ. Do **not** distribute the hexagon.

**Configurator is the seam.** Tests wire (app + driver + double); production wires (app + UI + real adapters). The inner hexagon stays.

## Failure modes

- **Logic leak into GUI or SQL.** Cockburn’s original bugaboo — the reason the hexagon exists. The port was never a real conversation.
- **Hexagon without tests on both sides.** Interfaces that nobody drives and nobody doubles. The boundary is fiction (2022 “blood freeze”).
- **Nested hexagons.** Duplicate system tests until they die. E8 is not nestable.
- **Port = technology** (`HttpPort`, `SqlPort`). You have labelled the adapter, not the conversation. Weather’s permutation explosion.
- **Hundreds of ports** / one port per use case. Ceremony without isolation.
- **DAL-shaped “port” that returns ORM entities.** Martin: do not pass row structures inward. You paid the types and kept the sink.
- **Périphérique skip** (Brown). Controller injects the repository and walks around the domain. Arrows may still look inward at the package level; authorization and rules are gone.
- **ACL confusion.** Legacy schema leaked into the domain “because we have an adapter.” If the problem is two *models*, you need an ACL, not another port name.
- **Distributed hexagon.** UI / domain / persistence as three network services. Shared DB ⇒ still one quantum; you paid the hops.
- **Team-per-ring.** UI / domain / infra teams recreate Fowler’s layer-team antipattern. Cross-functional teams own a domain + its adapters.
- **Label E8, mechanics E3.** Concentric folders, arrows still down onto the DAL.

## Trade-offs

No FSA scorecard exists for this style ([style-selection](../../.cursor/skills/arch-style/references/style-selection.md) has no row). These are source-backed costs of *choosing* E8 as the internal shape. Do not invent stars.

| Buy | Pay | Source |
|---|---|---|
| App runs with a driving harness and driven doubles; no UI/DB required | You must *write and keep* those tests or the boundary is fiction | Cockburn 2005 intent; 2022 “blood freeze” |
| Swap SQL / HTTP / GUI adapters without rewriting the inner API | Mapper / DTO tax at every crossing; ports that leak ORM types give none of the benefit | Cockburn weather use; Martin “what data crosses” |
| Domain does not compile against the store or the framework | Composition root must see both sides; easy to “cheat” from UI → infra (Brown Périphérique) | Fowler 2015 mapper; Microsoft 2021 composition root |
| Purpose-named ports stop permutation versions of the app | Extra types per port; a hexagon around CRUD is E3’s sinkhole plus ceremony | Cockburn 2005; E3 sinkhole |
| Adds **no** network and **no** independent scale by itself | Does **not** buy feature-deploy, elasticity, or fault isolation | ch7 machinery; Microsoft single-process runtime |
| One technology-edge hexagon is a maintainable system-test wall | Nested hexagons duplicate tests until they die | Cockburn 2022 |
| Cross-functional team owns a domain + its adapters | Ring-shaped teams recreate Fowler’s layer-team antipattern | Fowler 2015 |
| Adapter *can* translate | If the problem is two *models*, you need an ACL, not another port name | Azure 2026-05-28; B4 |

Layered decides **how technical work is stacked**. Hexagonal decides **where the dependency sink sits**. A modular monolith decides **how the domain is cut**. A sidecar decides **where a helper process lives**. Do not use one cut to do another cut’s job.

## Sources

Verified 2026-09-13; full URLs, per-claim provenance, and items deliberately left out (FSA stars, typical-quanta cell, book body, invented identity of Hexagonal = Onion = Clean) are in the [external research note](../../docs/research/sysdesign/e8-hexagonal-external-research.md).

- Cockburn, HaT TR 2005.02 (2005-09-04) — both names; inside/outside; driving/driven; Discounter; weather; port count as personal heuristic.
- Cockburn, HaT TR 2022.01 v3a (2023-06-01) — not nestable; tests both sides; Configurator; Provided/Required.
- Fowler, *Presentation Domain Data Layering* (2015-08-26) — hexagonal = mapper variation of layering; domain-on-top.
- Palermo, Onion part 1 (2008-07-29) / part 4 (2013-08-19) — shared premise; not for small websites.
- Martin, *The Clean Architecture* (2012-08-13) — ancestor list; Dependency Rule; output port.
- .NET *Common web application architectures* (`ms.date` 2021-12-12) — names collapsed; N-layer vs DIP; single-process monolith.
- Azure *Anti-Corruption Layer* (`ms.date` 2026-05-28) — ACL ≠ style; translate models; no business rules.
- [style-selection.md](../../.cursor/skills/arch-style/references/style-selection.md) — hexagonal **absent**; ch7 quantum machinery only.
- Brown, [package.md](../coding-rules/package.md) — inside/outside; Périphérique.
- [clean-architecture.md](../coding-rules/clean-architecture.md) — rings, lineage.
- [style-decision.md](../../docs/architecture/worksheets/mobile-test-automation/style-decision.md) + [ADR 0005](../../docs/architecture/adrs/application/mobile-test-automation/0005-adopt-plain-modular-monolith-partitioned-by-cluster.md) — Layered rejected; E10 chosen.
