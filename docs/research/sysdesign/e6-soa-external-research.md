---
type: research
title: 'SOA and service-based architecture — external research (2026-09-13)'
description: >-
  Group E decision-depth pass for catalog E6: orchestration-driven SOA
  (ESB, taxonomy layers, orchestration engine; residual fit = legacy
  integration; disaster as application architecture) distinguished from
  modern service-based (UI + ≤12 domain services + usually one DB; no
  5★; cost+simplicity). Quantum counts as fact; when-to / when-not;
  migration E1/E10 toward E2. No library defaults.
tags: [research, system-design-patterns, E6, soa, service-based]
---

# SOA and service-based architecture — external research (2026-09-13)

> **What this is.** Catalog **E6** evidence pass (Group E decision bar).
> No library-defaults section — styles have none. Two named styles share
> this id because “SOA” is overloaded. Quantum counts are **facts** from
> [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md);
> this note does **not** run arch-style’s four determinations or scoring
> micro-loop. Primary pages fetched 2026-09-13. Unverified items stay in
> **Uncertain / left out**.
>
> **Cite, do not rewrite:**
> [aws/ch08.md](../../../cases/aws/ch08.md),
> [distributed-vs-single-node.md](../../../cases/data-intensive-design/distributed-vs-single-node.md),
> [rest-rpc-dataflow.md](../../../cases/data-intensive-design/rest-rpc-dataflow.md),
> [services.md](../../../cases/coding-rules/services.md),
> [ADR 0005](../../architecture/adrs/application/mobile-test-automation/0005-adopt-plain-modular-monolith-partitioned-by-cluster.md),
> [style-decision.md](../../architecture/worksheets/mobile-test-automation/style-decision.md).
> **E2** owns microservices. **E4** owns EDA. **C6** owns the gateway *component*.

---

## 1. Scope and non-goals

**Owns** two architecture *styles*, kept un-collapsed:

1. **Orchestration-driven SOA** (FSA ch17): technical taxonomy layers plus an ESB / orchestration engine. Residual fit is *integration over legacy*, not a greenfield application architecture.
2. **Service-based architecture** (FSA ch14): separately deployed UI + **≤12 coarse domain services** + **usually one database**. The pragmatic first distributed hop from E1/E10, and the usual stepping-stone toward E2.

**What it is not.** A protocol (SOAP is a wire — A1 / `rest-rpc-dataflow.md`). A product (an ESB is a *placement*). A claim that “we have services, therefore we have an architecture” (Martin, `services.md`). OASIS SOA-RM is an *abstract* vocabulary, not this card’s application style.

| Sibling | Why not this card |
|---|---|
| **E2** | Fine grain, **DB-per-service**, most quanta of any style, share-as-little. Microservices ≠ “SOA with REST.” |
| **E1 / ⊕E10** | One deployable / one quantum. E6 is the first *distributed* exit; E10 is the in-process modular form that should precede a split. |
| **E4** | Reaction-to-events as the default collaboration. A service-based system may *use* a broker without becoming E4. |
| **C6** | North-south façade / BFF. A gateway that starts orchestrating is ThoughtWorks’ overambitious-gateway failure — a slide back toward ESB-SOA. |
| **B4 / B5 / ⊕B7** | Cutover and write mechanisms the day you leave a shared-DB E6 toward E2. |
| **E3** | Technical layers *inside* a domain service do not make the macro style layered. |

Non-goals: library or ESB-product defaults; scoring monolith-vs-distributed; reconstructing missing star figures; writing a Concept.

---

## 2. Lineage / vocabulary

**Fowler, *Service Oriented Ambiguity* (2005-07-01)** — https://martinfowler.com/bliki/ServiceOrientedAmbiguity.html — fetched 2026-09-13. “SOA” already meant incompatible things: expose via web services (WS-* *or* any XML/HTTP); dissolve applications into core services plus UI aggregators; a standard enterprise backbone (“CORBA with angle brackets” in the worst form); or asynchronous document messaging (EAI without the vendor lock-in). He judged the term **beyond saving** — concrete ideas need independent names.

**OASIS SOA-RM v1.0** (members approved as OASIS Standard; announcement **2006-10-22**, press **2006-10-23**) — https://docs.oasis-open.org/soa-rm/v1.0/soa-rm.html · https://www.oasis-open.org/2006/10/22/members-approve-reference-model-for-service-oriented-architecture-soa-rm-as-oasis-standard/ — fetched 2026-09-13. An *abstract* framework, “not directly tied to any standards, technologies or other concrete implementation details.” A **service**: “a mechanism to enable access to one or more capabilities, where the access is provided using a prescribed interface and is exercised consistent with constraints and policies as specified by the service description.” Dynamics: **visibility** (awareness, willingness, reachability) → **interaction** (usually messages) → **real world effect**. Ownership boundaries are a *motivating consideration*. Vocabulary — **not** a license to install an ESB. **OASIS SOA-RAF v1.0** (Committee Specification 01, **2012-12-04**) — https://docs.oasis-open.org/soa-rm/soa-ra/v1.0/cs01/soa-ra-v1.0-cs01.html — still abstract; extra weight when integration crosses ownership boundaries. Not the FSA ch17 topology.

**The Open Group, “What Is SOA?”** (SOA Source Book; retrieved 2026-09-13) — https://collaboration.opengroup.org/projects/soa-book/pages.php?action=show&ggid=1314 — SOA = “an architectural style that supports service orientation.” A service is a logical representation of a repeatable business activity with a specified outcome; self-contained; may compose other services; a black box to consumers. Distinctive features include **service orchestration**, open-standards infrastructure, and **strong governance** plus a “Litmus Test” for a good service. That is the *enterprise* flavor Fowler already found ambiguous, and the pairing Richards later scores as the disaster row.

**Lewis & Fowler, *Microservices* (2014-03-25)** — https://martinfowler.com/articles/microservices.html — *Microservices and SOA* (fetched 2026-09-13). The style is similar to what *some* SOA advocates wanted. What they actually met, most of the time, was **ESBs used to integrate monolithic applications**; complexity hidden in the bus (Jim Webber: ESB = “Erroneous Spaghetti Box”); multi-year initiatives that cost millions and delivered nothing; centralized governance that inhibited change. Some reject the SOA label; others call microservices “SOA done right.” Netflix had been saying **fine-grained SOA**. Preference they name: **smart endpoints, dumb pipes** — domain logic in the service; choreography over WS-Choreography / BPEL / a central orchestrator. The term “microservices” exists *because* SOA would not stay still.

**Richards, *Software Architecture Patterns*** (O’Reilly, first release **2015-02-24**; retrieved 2026-09-13) — https://www.oreilly.com/content/software-architecture-patterns/ — SOA is “complex, expensive, ubiquitous, difficult to understand and implement, and is usually overkill for most applications.” Microservices simplify the service, drop orchestration needs, and simplify access. Three topologies he then still filed under *microservices*: API REST (fine-grained, C6-shaped); **application REST** (separately deployed UI talking to **larger, coarse-grained** service components — the shape FSA later names **service-based**); centralized messaging (lightweight broker, **not** “SOA-Lite”: no orchestration, transformation, or complex routing). Too-fine services that force UI/API orchestration “will quickly turn your lean microservices architecture into a heavyweight service-oriented architecture.” Shared-database reads are his stated alternative to inter-service calls for data.

**Richards, *Microservices vs. Service-Oriented Architecture*** (O’Reilly report, first release **2015-11-17**; PDF fetched 2026-09-13: https://www.developertoarchitect.com/downloads/microservices-vs-soa.pdf and F5 complimentary https://cdn.studio.f5.com/files/k6fem79d/production/3212071924d61ab917d2ee45b6098ca87ca71dfb.pdf). Mid-2000s SOA promised reuse and business/IT alignment; companies learned it was “big, expensive, complicated” and “took too long,” and failed projects drove it out of favor. He quotes OASIS-RM’s service definition, then adds what the RM does *not* specify: taxonomy, ownership, granularity. **SOA taxonomy (four types):** abstract **business services** (enterprise operations; often WSDL / BPEL; litmus: “Are we in the business of …?”); concrete shared **enterprise services** (`CreateCustomer`, `ValidateOrder`); fine-grained **application services** bound to one app; **infrastructure services** (audit, security, logging). Middleware bridges abstract business services to enterprise implementations. **Ownership** is split across business users, shared-services teams, app teams, infra teams, and the integration/middleware group — so one request is a multi-group coordination tax. **Share-as-much-as-possible** vs microservices’ **share-as-little-as-possible** (bounded context). SOA scope: large heterogeneous enterprise-wide systems with many shared components (his insurance example). Poor fit: small web apps, and workflow apps with few shared components. Mid-size systems that outgrow a thin API may *gain* SOA capabilities (transformation, orchestration, heterogeneous integration) — or an overbuilt SOA may shrink *to* microservices. That last sentence is a capability observation, not a recommendation to re-adopt ch17. ACID across remote services is not feasible; coarsen until the transaction sits in one service, or accept BASE.

**Microsoft Learn, “Service-oriented architecture”** (retrieved 2026-09-13) — https://learn.microsoft.com/en-us/dotnet/architecture/microservices/architect-microservice-container-applications/service-oriented-architecture — SOA was overused; common denominator = decompose into services (usually HTTP). Microservices *derive from* SOA but differ: large central brokers, organization-level orchestrators, and the ESB are “typical in SOA” and “**anti-patterns in the microservice community**.” Some people argue “The microservice architecture is SOA done right.” SOA is **less prescriptive**.

**Richards & Ford, *Fundamentals of Software Architecture*** (1st ed. 2020; 2nd ed. March 2025). Workspace SoT is [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md) (ch14 service-based; ch17 orchestration-driven SOA). 2nd-ed chapter bodies are paywalled (O’Reilly Access Denied, 2026-09-13) — §7. Cite the distillation for the comparison-matrix rows; do not re-derive.

**Martin, *Clean Architecture* ch27** (workspace [services.md](../../../cases/coding-rules/services.md)). Services are not an architecture. Decoupling at variables is real; coupling through **shared data** remains. Independently deployable only to the extent data/behavior coupling allows. Cross-cutting features (the “kitty problem”) force coordinated change across a functional service cut.

---

## 3. Mechanics (Group E decision depth)

### 3.1 What each style is

**Orchestration-driven SOA (ch17).** A technically partitioned enterprise topology: taxonomy layers (business / enterprise / application / infrastructure) stitched by a **service bus + orchestration engine** that owns routing, transformation, discovery, and often the transaction boundary. Reuse is the driving philosophy — write `CreateCustomer` once, call it from everywhere. Quantum machinery collapses this to **one quantum**: the shared bus, the shared enterprise services, and (usually) the shared data model are a single coupling domain. Style-selection partitioning: “**technical (extreme)**.”

**Service-based (ch14).** A **domain-partitioned** distributed application: a separately deployed UI (sometimes more than one), **≤12 coarse domain services** (order fulfillment, shipping — a *portion* of the app, not a getter), and **usually one database**. Services deploy like small monoliths. Communication is typically synchronous and should be **rare** — heavy chatter means the boundaries are wrong or the style is. This is Richards 2015’s “application REST” topology named as its own style. OASIS-RM still applies to both as a *vocabulary*. It does not choose the bus.

### 3.2 What each style is not

| Look-alike | Why not E6 |
|---|---|
| **E2 microservices** | Fine-grained, **DB-per-service**, polyglot persistence, share-as-little, most quanta. Service-based keeps ACID by *not* splitting the DB. Orchestration-SOA shares *more*, not less. |
| **E1 / distributed monolith** | Several HTTP endpoints on one schema *and* a lock-step release are still one quantum. If you cannot ship fulfillment without shipping, you have not left E1. |
| **E10 modular monolith** | Same domain cut, still one process. Extracting those modules *is* the E10→E6 move. |
| **C6 API gateway / BFF** | A dumb north-south hop. The moment the gateway owns BPEL-like flow, transformation, and canonical models, you have re-entered ch17. |
| **E4 mediator** | A workflow engine *inside* an event-driven style is not an enterprise SOA taxonomy. [aws/ch08.md](../../../cases/aws/ch08.md) orchestration vs choreography is a *collaboration* choice, not this style. |
| **SOAP / WS-*** | A protocol generation. You can do service-based over HTTP/JSON; you can do ch17 over REST. The style is where the logic and the data live. |
| **“We have services”** | Martin: expensive function calls. Taxonomy + bus, or coarse independently deployable domain services — pick one and name it. |

### 3.3 Quantum count — fact, not a score

From [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md) (do not re-run the determinations): architecture quantum = smallest independently runnable part. **The DB is part of the quantum — single shared DB ⇒ quantum of one.** Coupling test: “two things are coupled if changing one might break the other.” Sync between would-be quanta **silently merges them**. After choosing sync vs async, **re-check boundaries**.

| Style | Topology | Partitioning | Quanta (FACT) | Prose-recovered ratings | Cite |
|---|---|---|---|---|---|
| **Service-based (ch14)** | UI + ≤12 coarse domain services + usually one DB | domain | **≥1** | agility/test/deploy **4★**, FT/availability **4★**, scalability **3★**, elasticity **2★**; **no 5★ anywhere** — the pragmatic differentiator is **cost + simplicity** | `service-based-arch-style.md:141-147` |
| **Orchestration-driven SOA (ch17)** | taxonomy layers + ESB / orchestration engine | technical (extreme) | **1** | deploy/test “**disastrous**”; simplicity/cost **inverted** | `orchestration-driven-service-or-arch.md:156-163` |

Unrecovered star cells are **—**. Do not invent a blended “SOA” star row.

**How ≥1 happens in service-based.** One shared DB ⇒ **quantum of one** for anything that transactionally depends on that schema, even if processes deploy separately. Additional quanta appear only when a domain service gets **its own** persistence (or an independent UI with no shared store) *and* you do not re-entangle them with a synchronous call. That is why the row is “≥1” and not “12.” **≤12 is a service-count ceiling, not a quantum count.** Do not treat “12 services” as “12 quanta.” **Do not score candidates here.**

### 3.4 When to use / when not

**Service-based — use when** (style-selection `service-based-arch-style.md:95-97,147-155`): you want **modularity without microservices’ granularity tax**; **ACID** across a related dataset still matters (the book’s “**best distributed style for ACID needs**”); the domain already has DDD-shaped coarse seams (a handful of subdomains, not a hundred entities); you need a **stepping-stone to microservices** (deployable domain services first, database split later); team / ops maturity is enough for a few independently deployed units, not for a mesh + N databases + sagas.

**Service-based — do not use when:** you have **one characteristics set** and one team — stay E1/E10 (decision tree). ADR 0005 lost this row because Determination 1 found **no quantum boundary**. Inter-service chatter is constant: wrong boundaries or wrong style. Richards 2015: if the UI/API must orchestrate, services are too fine; if services call each other to finish one request, they are too fine or mis-partitioned. You have already crossed ~12 services and are splitting the DB — you have left this style for E2 (or a distributed mud). Fault isolation / independent scale of *data* is a top characteristic: elasticity is only **2★**; the shared DB is still one fate for storage.

**Orchestration-driven SOA — residual use** (style-selection `orchestration-driven-service-or-arch.md:108-171`): **historical.** Residual fit = **integration architecture over legacy** (package software, COBOL cores, heterogeneous ownership — Richards 2015 “heterogeneous interoperability”; OASIS-RAF’s crossing-ownership emphasis). “**In practice it has mostly been a disaster**” as an *application* architecture (style-selection; quoted in [style-decision.md](../../architecture/worksheets/mobile-test-automation/style-decision.md)). Reuse created coupling; coupling forced coordinated deployments and holistic tests; the integration team around the engine became the bureaucratic bottleneck (Richards’ ownership model; Conway). Do **not** pick ch17 for a new product because the Open Group page says “strong governance” and “orchestration.” Those sentences describe the style that FSA scores disastrous for deploy/test.

### 3.5 Migration in / out

**Into service-based (the usual E6):**

| From | Move | Notes |
|---|---|---|
| **E1 / E10** | Extract coarse domain services along *already published* module seams; keep the database at first | Book-recommended stepping-stone. ADR 0005 records this as the destination. Fowler’s coarse “duolith” is already E6-shaped. |
| **E2 gone wrong** | Merge chatty services; restore a shared DB *deliberately* for the ACID cluster | Richards 2015: coarsen to keep a transaction inside one service. E2’s own rule: don’t do cross-service transactions — fix granularity. |
| **ch17 SOA** | Collapse taxonomy layers into domain services; demote the ESB to a dumb pipe or C6 façade; stop sharing enterprise entity services | Extract *away* from the bus. Do not “replatform the ESB to Kubernetes” and call it modern. |

**Out of service-based:** (1) **Stay** — most systems that needed distribution for deploy/test/FT never need E2’s data split; cost+simplicity is the differentiator precisely because you can stop here. (2) **→ E2 via B4**, one service at a time, **after** you split *that* service’s data. Shared DB left in place ⇒ quantum count unchanged. Cross-service writes then pay B5/B7. (3) **→ E4** only if the collaboration itself becomes react-to-what-happened (E4 when-not: mostly request-based work stays here). (4) **Back to E1/E10** if the extra processes bought nothing (Martin: slide back to one executable as operational need declines).

**Out of orchestration-driven SOA:** treat the bus as a strangler façade (B4/C6). Accidental SOA (`orchestration-driven-service-or-arch.md:114`, name-check only — §7) is the failure mode of *recreating* this topology inside an E2/E6 program (gateway-as-ESB, shared entity library as enterprise service).

**Antipatterns this card must name** (style-selection cross-style shortlist): **Accidental SOA** — reconstructing taxonomy + smart pipe under new labels (definition **not asserted** — §7). **Shared entity-object library** in service-based (`service-based-arch-style.md:73-76`) — a schema or JAR of entities that forces lock-step rebuilds (mechanism **not asserted** — §7). **Entity-trap / Grains of Sand** — live on E2; the E6 warning is the inverse: do not pre-split into entity services (`GetCustomerName`) or you recreate the chatty SOA Richards said architects had to unlearn.

Fallacies you start paying the day you leave E1 (style-selection ch9): network unreliable / latency not zero / bandwidth finite (stamp coupling via fat entity payloads) / **versioning is easy** / **compensating updates always work** / **observability is optional**. Service-based pays fewer of them than E2 *only* while the DB stays shared and chatter stays low.

### 3.6 Worked example — not a scored kata

**Workspace (this system).** [style-decision.md](../../architecture/worksheets/mobile-test-automation/style-decision.md) (gate closed 2026-07-26) and [ADR 0005](../../architecture/adrs/application/mobile-test-automation/0005-adopt-plain-modular-monolith-partitioned-by-cluster.md) (accepted): **Not E6 today.** Determination 1: one quantum. The IR spine is shared; Preserve Provenance has CA = 13 of 16 components; a synchronous Certify→Models call would collapse a split. Service-based was “the strongest distributed candidate” and lost because there was **no quantum boundary**, its winning rows (FT 4★, scalability 3★) were **eliminated at stage 1**, and team maturity was `needs-input`. **Named migration target.** First extraction candidates: Replay-on-devices (if lab-side scaling becomes internal) and cluster C / evidence (if residency makes co-location *illegal*). Module seams were cut on those clusters so an E6 extract would follow code and schema lines already there. **Orchestration-driven SOA** was rejected in one line: historical; disaster as application architecture. No residual integration-over-legacy problem exists for this target. This is the book’s intended use of E6: **not the start**, the priced exit from E10 when a named fracture appears.

**Place-order (ACID cluster).** `Order` write + `Customer.creditLimit` as one ACID → keep them in **one** coarse Ordering service on the shared DB. That is E6 doing its job. Split those tables and you have left for E2 and must pay B5 — E2’s own when-not. `Notification` can be async without becoming E4. Shared `CUSTOMERS` table plus two “services” that cannot deploy apart = **not E6** (one quantum pretending to be two). Richards 2015 application-REST shape — separately deployed UI, coarse service components, shared-database reads instead of service-to-service calls — is E6 service-based without the later name.

### 3.7 Trade-off table

Qualitative, source-backed. Stars only where style-selection recovered them. **No invented cells.**

| Concern | Service-based (ch14) | Orchestration-driven SOA (ch17) | Source |
|---|---|---|---|
| **Cost / simplicity** | The differentiator: no 5★, but cheaper than E2/EDA | **Inverted** — reuse bought a coordination machine | style-selection matrix |
| **Deploy / test / agility** | **4★** — few independently shipped domain units | “**Disastrous**” — one request, many owners, bus in the middle | style-selection; Richards 2015 ownership |
| **Fault tolerance / availability** | **4★** — a dead domain service is not the whole UI process | One quantum through the engine; the bus is a fate-share | style-selection; Lewis/Fowler ESB critique |
| **Scalability / elasticity** | **3★ / 2★** — scale a service’s *compute*; the shared DB does not split | Heterogeneous integration scale, not elastic app scale | style-selection |
| **ACID / consistency** | Best distributed style for ACID (one DB, coarse services) | Distributed txns across enterprise services — Richards: not feasible; BASE or coarsen | style-selection when-to; Richards 2015 Transactions |
| **Reuse** | Deliberately low; duplicate small logic rather than share entities | Driving goal; enterprise services *are* reuse; coupling follows | Richards 2015 share-as-much vs share-as-little |
| **Governance / Conway** | App teams own domain services (like E2, fewer of them) | Business + shared-services + app + infra + middleware for *one* request | Richards 2015; Open Group “strong governance” |
| **Heterogeneous legacy integration** | Weak — not what the style is for | The residual reason to keep a bus | Richards 2015 Application Scope; OASIS-RAF ownership |
| **Stepping-stone** | Yes → E2 (data split later) | Poor → anything; extract *away* from the bus | style-selection |
| **Network fallacies** | Paid at service boundaries; limited by chatter rule | Paid *and* concentrated in the smart pipe | style-selection ch9; Fowler ESB |
| Other stars | **—** | **—** | figures missing |

---

## 4. Failure modes and when-not (of the style)

- **Vocabulary collapse.** Fowler 2005: the word does not decide. If you cannot say “ch17 bus” or “ch14 domain services,” you do not have a style decision.
- **Accidental SOA.** A C6 gateway or “composer service” accretes transformation, canonical models, and workflow. ThoughtWorks Hold on overambitious gateways ([C6](c6-api-gateway-external-research.md)).
- **Shared entity-object library.** Compile-time reuse that restores lock-step deploys (style-selection name-check). Martin’s data-coupling fallacy in JAR form.
- **Chatty entity services.** `GetCustomerAddress` + `UpdateCustomerName` — the granularity error SOA already burned on (Richards 2015). Fix: coarsen, or you have invented E2 minus independence.
- **Distributed monolith.** HTTP + one schema + one release train. Pays E6’s network tax without E6’s deploy 4★.
- **Kitty / cross-cut.** Functional service cuts that cannot absorb a new feature without touching every service (`services.md`). E6 does not repeal this; coarse *domain* services only help if the new feature sits inside one domain.
- **Fashion skip to E2.** Style-selection fashion check; this workspace’s microservices rejection. E6 exists so you do not have to.
- **Saga sprawl as a substitute for coarsening.** Most user actions need a saga ⇒ the cut is wrong (do not “fix” it with a better orchestrator — that rebuilds ch17).

**When not (summary).** Greenfield with one characteristics set → E1/E10. Extreme isolation / independent data scale → E2 (after prerequisites). React-to-events domain → E4. New application whose only “requirement” is reuse-via-ESB → do not pick ch17. Integration of heterogeneous *owned-by-someone-else* systems may still justify a *constrained* bus — that is an integration architecture, and it should be named as such, not as the application style.

---

## 5. Cross-links

| Id / note | Relationship |
|---|---|
| **E2** | Finer grain, DB-per-service, share-as-little. Destination after a named data fracture. Owns “how small.” |
| **E1 / ⊕E10** | Source of the usual extraction. E10 seams should *be* the future domain services. |
| **E4 / A2** | Optional async fabric between domain services; not implied by E6. |
| **C6** | Thin API / BFF in front of domain services. Must stay dumb. |
| **B4 / B5 / ⊕B7** | Leave E6 toward E2: façade, saga, outbox. |
| **A1 / `rest-rpc-dataflow.md`** | SOAP vs REST as wire, not style. |
| **`services.md`** | Services ≠ architecture; data coupling; kitty problem. |
| **`distributed-vs-single-node.md`** | Popular SOA → microservices refinement; DB-per-service cost. |
| [aws/ch08.md](../../../cases/aws/ch08.md) | Orchestration vs choreography as collaboration; gateway/mesh as tax; monolith skips the network. |
| [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md) | Quantum facts, both matrix rows, when-not wording, “disaster” line. |
| Workspace ADR 0005 / style-decision | Worked non-pick; E6 as priced exit. |
| Fallacies (style-selection ch9) | E6 pays them at service boundaries; ch17 concentrates them in the smart pipe. |

---

## 6. Sources

Fetched 2026-09-13.

- Fowler, *Service Oriented Ambiguity* (2005-07-01). https://martinfowler.com/bliki/ServiceOrientedAmbiguity.html
- OASIS, *Reference Model for Service Oriented Architecture* v1.0 (approved OASIS Standard; announcement 2006-10-22). https://docs.oasis-open.org/soa-rm/v1.0/soa-rm.html · https://www.oasis-open.org/2006/10/22/members-approve-reference-model-for-service-oriented-architecture-soa-rm-as-oasis-standard/
- OASIS, *Reference Architecture Foundation for SOA* v1.0 (Committee Specification 01, 2012-12-04). https://docs.oasis-open.org/soa-rm/soa-ra/v1.0/cs01/soa-ra-v1.0-cs01.html
- The Open Group SOA Working Group, “What Is SOA?” (SOA Source Book). https://collaboration.opengroup.org/projects/soa-book/pages.php?action=show&ggid=1314
- Lewis & Fowler, *Microservices* (2014-03-25), incl. *Microservices and SOA*. https://martinfowler.com/articles/microservices.html
- Mark Richards, *Software Architecture Patterns* (O’Reilly, 2015-02-24). https://www.oreilly.com/content/software-architecture-patterns/
- Mark Richards, *Microservices vs. Service-Oriented Architecture* (O’Reilly, 2015-11-17). https://www.developertoarchitect.com/downloads/microservices-vs-soa.pdf · F5 complimentary: https://cdn.studio.f5.com/files/k6fem79d/production/3212071924d61ab917d2ee45b6098ca87ca71dfb.pdf
- Microsoft Learn, “Service-oriented architecture.” https://learn.microsoft.com/en-us/dotnet/architecture/microservices/architect-microservice-container-applications/service-oriented-architecture
- Richards & Ford, *Fundamentals of Software Architecture* — via [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md) (ch7 quantum; ch14 service-based; ch17 orchestration-driven SOA). 2nd-ed ch14/ch17 HTML: Access Denied 2026-09-13.
- Workspace: `cases/coding-rules/services.md`; `cases/data-intensive-design/distributed-vs-single-node.md`, `rest-rpc-dataflow.md`; `cases/aws/ch08.md`; ADR 0005; style-decision.md.

---

## 7. Uncertain / left out

Must **not** be implied as fact in the Concept.

- **`cases/ArchitectureBook/` chapter files** cited by style-selection (`service-based-arch-style.md`, `orchestration-driven-service-or-arch.md`) were **not present** in the main-repo `cases/` tree on 2026-09-13 (searched). Line-anchored claims — quanta, recovered stars, “mostly been a disaster,” ≤12, “best distributed style for ACID,” Accidental SOA at `:114`, shared entity-object library at `:73-76` — rest on the **distillation** (and the local style-decision, which already quoted the disaster line). Treat any number not in style-selection as unverified.
- **Star-rating figures** did not survive into the notes (`style-selection.md` header). Unrecovered cells are **—**. Do not invent a blended “SOA” star row.
- **Accidental SOA** and **shared entity-object library** are name-checks only. Book paragraphs and suggested mitigations were not fetched. Secondary reader blogs were **not** used as definitions.
- **FSA 2nd-ed ch14/ch17 full chapter bodies** are paywalled (O’Reilly Access Denied 2026-09-13). Ratings, ≤12 / usually-one-DB, and quantum ≥1 / 1 come from style-selection only.
- **“4–12 services, average ~7”** appears in some secondary retellings of FSA 1st-ed ch13. The publisher HTML returned Access Denied 2026-09-13. **Not used as a fact.** Style-selection’s **≤12** ceiling is the verified service-count bound.
- **OASIS-RM calendar date on the spec itself** (often given as 2006-10-12) was **not** on the HTML body fetched. Approval is cited from the 2006-10-22 / 2006-10-23 OASIS announcement only.
- **OASIS-RAF** was fetched at front-matter depth (CS01, 2012-12-04; ownership-boundary emphasis). Concrete viewpoints and any numeric recommendations inside the 2012 body were not mined.
- **Hard Parts** five-step data-domain split — sequence (“domain services before database split”) is implied by style-selection’s stepping-stone line; step mechanics were not fetched.
- **Jim Webber, “Guerrilla SOA” (2006)** is named in Lewis & Fowler’s footnote; the talk body was not fetched. “Erroneous Spaghetti Box” is taken from that footnote only.
- **Thomas Erl** reference-architecture layer counts and **WS-*** stack defaults were not fetched and are not style facts.
- Printed ISBN on the fetched Richards PDF is `978-1-491-94161-4`; some catalogues list `978-1-491-95242-9` for the same report. Identity is by title + 2015-11-17 first release, not by picking one ISBN as canonical.
- Head-count or “N services per team” thresholds in tertiary blogs were not on any primary page fetched for this note.
- **Library, ESB-product, BPMN-engine, mesh defaults.** Out of scope (Group E).
