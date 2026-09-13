---
type: reference
title: 'Microservice architecture'
description: >-
  A style, not a tactic: one application as independently deployable,
  domain-shaped services, each owning its data. Size is not the discriminator;
  coordinated releases, a shared domain library, or a shared DB are not this
  style. Distinguishes E6 SOA/service-based and E13 cells; C1/C2/C6 are the
  required tax on every sync hop, not the architecture.
tags: [system-design-patterns, architecture, microservices]
---

# Microservice architecture

**See also:** [monolithic architecture](Monolith.md) · [circuit breaker](CircuitBreaker.md) · [retry, backoff, and retry budgets](RetryBackoff.md) · [API gateway and backend-for-frontend](ApiGateway.md) · [timeouts and deadline propagation](TimeoutsDeadlines.md) · [bulkhead and isolation](Bulkhead.md) · [cloud application architectures](../aws/ch08.md) · [distributed versus single-node](../data-intensive-design/distributed-vs-single-node.md) · [distributed transactions](../data-intensive-design/distributed-transactions.md) · [microservices in ML](../ml-solutions-arch/microservices-in-ml.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/e2-microservices-external-research.md)

Microservice architecture is a **style**: one application as a suite of services, each in its own process, shaped around a **business capability**, **independently deployable**, and owning its own persistence. The network is the module boundary. That is a stronger claim than “many small HTTP processes,” and it is a different claim from the C-group cards — [breakers](CircuitBreaker.md), [retries](RetryBackoff.md), [timeouts](TimeoutsDeadlines.md), [bulkheads](Bulkhead.md), and the [gateway](ApiGateway.md) are **required tax on the hops this style creates**, not the style.

Quality attributes in play (workspace distillation of the style-selection matrix; star figures are missing and are not invented here): **deployability** and **test isolation** are definitional; **evolvability** is high when boundaries are stable; **scale / elasticity** is high *as a capability* (Fowler 2015: no convincing report that selective scale is cheaper than cookie-cutter monolith replicas); **fault tolerance** is high *only after* the C* tax — a synchronous call graph is otherwise *less* available than one process. The costs are distribution, eventual consistency, and Fowler’s **microservice premium** (provision, CD, monitoring, many repos). Performance is “often an issue.” [Distributed versus single-node](../data-intensive-design/distributed-vs-single-node.md) frames the style as primarily a **technical solution to a people problem**.

## Lineage and vocabulary

- **Lewis & Fowler, *Microservices* (2014-03-25).** First widely cited definition — and they refuse a formal one. Term: Venice May 2011; name May 2012. Netflix then said “fine-grained SOA.” Traits that still discriminate: componentization via *services* (not libraries); organization around business capabilities; products not projects; **smart endpoints, dumb pipes**; decentralized governance and **decentralized data**; infrastructure automation; design for failure; evolutionary design. Sidebar *How big?*: the name “lead[s] to an unfortunate focus on … size.” Range they reported: a two-pizza team (≤ ~12 people) down to half-a-dozen people / half-a-dozen services. Size is not the discriminator. Sidebar *SOA*: the term “means too many different things”; the common form they saw was ESBs integrating monoliths — that is catalog **E6**, not this card. Sidebar *Synchronous calls considered harmful*: Guardian = **one sync call per user request**; Netflix rebuilt the platform API around asynchrony. A service may be several processes shipped together (app + *its* database).
- **Newman.** Independently releasable services modeled around a business domain; “a type of [SOA], albeit one that is opinionated about how service boundaries should be drawn, and one in which **independent deployability is key**.” Shared databases are “especially problematic.” That principle is “the most important”; a shared domain-object library that forces client upgrades **loses** it. Asked “how big?”, answered “42” — then: size is how many services you can *operate*, not LOC. Transactions: “Avoid! … leave them till last.” SnapCI knew CI, still got boundaries wrong, **merged back**.
- **Fowler follow-ons (2014–2015).** *Prerequisites*: rapid provision, technical *and* business monitoring, rapid deploy → DevOps; start with a handful of services. *Premium*: **do not even consider** the style unless the system is too complex as a monolith; observed 60 people / 20 services vs 4 / 200. *Monolith First*: almost all successes started as a too-big monolith; almost all greenfield-as-microservices stories he had heard ended badly. *Trade-Offs*: buy boundaries / independent deploy / tech diversity; pay distribution / eventual consistency / ops complexity. **Coordinated releases “is not a microservice architecture.”**
- **Richards (2016) / Ford.** Antipattern = seemed good; pitfall = never was. **Data-Driven Migration**, **Timeout** (resolves to C1), **“I Was Taught to Share”**, **Reach-in Reporting**, **Grains of Sand**, **Jump on the Bandwagon**. Disintegrators (scope, volatility, scale, fault tolerance, security, extensibility) vs integrators (transactions, chatter, shared code, data relationships). Service-based (E6 modern variant) = “as far toward microservices as we can get, but we’re keeping a single database.” Data *inside* the service makes **transactionality an architecture decision**.
- **Richardson.** Data private, reachable **only** via the API; a transaction touches **that** DB. Physical options: private-tables / schema-per-service / server-per-service (enforce with grants). Writes across services → saga (catalog B5); reads → API composition or CQRS (E12). Distributed transactions “best avoided.”
- **Azure style page** (fetched 2026-09-13; `ms.date` not on the page). Bounded-context services, **own data**, polyglot persistence, gateway entry, messages for async. Chatty A→B→C is a design smell. “Functions that are likely to change together should be packaged and deployed together.” Antipatterns: no domain analysis; sharing **domain** libraries; exposing services to clients (C6); domain in the gateway.
- **Dehghani (2018-04-24).** “Size … matters least”; “microservices is a label and not the description.” Warm up on a decoupled edge; **minimize dependency back to the monolith**; do **not** extract a “session service”; decouple **vertically and release the data early**; **macro first, then micro**.

## What it is — and the look-alikes that are not

Six invariants. Miss one and you have another style wearing this label.

1. **Component = service** (out-of-process), not a library. May include the database process shipped with it.
2. **Independently deployable.** Change, test, and release *one* service without changing neighbors. Coordinated releases fail the test.
3. **Owns its state.** No other service’s transaction touches this data. The database is *inside* the quantum.
4. **Boundaries = business capability / bounded context**, not a technical layer (Conway).
5. **Dumb pipes** — HTTP or a fabric that only routes. An ESB that owns routing + transform + rules is E6.
6. **Failure is a design input.** C* tax on every synchronous hop.

| Look-alike | Why not E2 |
|---|---|
| **“Small services”** | Size is not the discriminator (Lewis/Fowler, Dehghani, Newman). A two-pizza service still qualifies; a 200-LOC class-as-HTTP is **Grains of Sand**. |
| **SOA-with-REST / ESB (E6)** | Same network, opposite governance: smart pipe, often a shared canonical model and a shared DB. Microservices are not “SOA with REST.” |
| **Service-based (E6 modern variant)** | Coarse domain services, **usually one database**. Style-selection: ≤12 services; **no 5★** — the differentiator is cost + simplicity. Shared DB ⇒ **one quantum**. That “~12” is an **E6** fact, not an E2 default. |
| **Modular monolith (E10)** | Domain modules, one runtime, one deployable. Newman’s cheap later-split: schema-per-future-module *inside* that runtime. |
| **Distributed monolith** | Many processes, lock-step release, shared tables, or a shared entity library. |
| **Event-driven architecture (E4)** | Events are a *comms choice* between quanta. Using a broker does not make the style EDA; needing a broker for every user action does not make E2 into E4. |
| **N-tier** | Technical layers, often one DB / one deployable ([ch08](../aws/ch08.md)). |
| **Cell-based (E13)** | A **cell** is a complete replica of the serving stack for a slice of the partition key — own data and logic, autonomous scale, failure contained to that slice ([ch08](../aws/ch08.md)). [Bulkhead](Bulkhead.md) uses cells as a C8 *tactic* and owns the blast-radius arithmetic; E13 owns whether the *system* is cell-based. A cell may *contain* a microservice graph; it does not *replace* the domain cut. Do not treat “we sharded the fleet” as “we have microservices,” or the reverse. |

E6 and E13 are the two most common mislabels. **E6** answers “how do we integrate coarse capabilities?” — historically with an orchestration engine / ESB (style-selection: residual fit is integration over legacy; “in practice it has mostly been a disaster” as an *application* architecture), or today as service-based: a UI plus a handful of domain services in front of **one** database. You still have process isolation; you do **not** have data isolation, so you do not have independent deployability of the *quantum*. **E13** answers “how much of the fleet can one poison tenant, bad deploy, or zonal loss take down?” by copying the *whole* serving stack. Cells partition *load and fate*; microservices partition *domain and ownership*. You can run E2 inside E13 (each cell hosts the same service graph) or run E13 in front of an E6/E10 core. Picking one does not pick the other.

## Quantum count — a fact, not a target

An architecture quantum is the smallest independently runnable part. **The database is part of the quantum**: a shared DB ⇒ a quantum of one, however many processes sit in front of it. After choosing sync vs async, **re-check** — sync can silently merge quanta (the caller inherits the callee’s characteristic set).

Style-selection comparison matrix (ch18):

| Style | Quanta |
|---|---|
| Layered / modular monolith / pipeline / microkernel | 1 |
| Service-based (E6) | ≥1 |
| Event-driven (E4) | 1–many |
| **Microservices (E2)** | **most of any style** |

That is a fact about the style’s topology, not a headcount to chase. Fowler’s 20-vs-200 observation and Newman’s “how many can you operate” are the constraint. Do not score monolith-vs-microservices on this card.

Coupling test (style-selection): two things are coupled if changing one might break the other. Shared tables fail it immediately. A blocking RPC on the user path fails it for *characteristics* even when the schemas are already split — checkout inherits payments’ availability, latency budget, and release nerve.

## Characteristics (honest `—`)

Star-rating figures did not survive into the workspace notes. Unrecovered cells stay `—`; E6’s recovered 4★ / 3★ / 2★ stay on E6.

| Characteristic | Microservices (prose) |
|---|---|
| Deploy / test | **HI** — definitional if independent deployability holds |
| Fault tolerance | **HI** — only if the C* tax is paid; a sync graph is otherwise *less* available |
| Scale / elasticity | **HI** as capability. Fowler 2015: no convincing “selective scale is cheaper than monolith replicas” report |
| Evolvability | **HI** when bounded contexts are stable |
| Performance | **“often an issue”** (ch18 prose) |
| Simplicity / cost | **—** (prose: the premium is high) |
| Stars 1–5 | **—** |

## Prerequisites and the C* tax

Fowler’s 2014 prerequisites are a gate, not a wishlist: rapid provision of a new service, monitoring of *technical and business* signals, and rapid (automated) deploy — which is to say a DevOps baseline — **before** a handful of services, not after twenty. Newman’s operational reading of “how big?” is the same gate from the other side: size is how many services you can operate.

The C-group cards are the per-hop bill this style invoices. They do not make a bad cut good ([ML patterns](../ml-solutions-arch/ml-microservices-patterns.md)).

| Tax | Owns | On this style |
|---|---|---|
| **C7** [timeouts](TimeoutsDeadlines.md) | How long one hop may run; remaining deadline downstream | A hung neighbor that never fails never increments a breaker |
| **C2** [retry + budget](RetryBackoff.md) | Whether, when, and how often to try again — **one layer** | Stacked app + mesh retries are the usual metastable loop |
| **C1** [breaker](CircuitBreaker.md) | Whether to call at all | Richards’ Timeout antipattern resolves here |
| **C8** [bulkhead](Bulkhead.md) | How much may run at once, per compartment | In-process pools are not cells (E13) |
| **C6** [gateway / BFF](ApiGateway.md) | North–south front door: route, offload, optional aggregate | Not a quantum. Not an orchestrator. Domain stays out. |

C4 (admit), C5 (host selection), and C9 (idempotency on the write that may have succeeded) show up the moment you retry or queue; they are still tactics. This card stops at naming the bill.

## Decision mechanics

### Bounded context

Cut on a **stable business capability**, usually after a monolith, modular monolith, or service-based system taught you where the seams are. Azure: functions that change together deploy together. Richards/Ford: start coarse; **integrators** (transactions, chatter, shared data relationships) argue for merging; **disintegrators** (volatility, scale, fault isolation, security, extensibility — including a hardware-class split such as GPU train vs CPU serve) argue for splitting. A preprocess RPC on the score path is the latency failure in [microservices-challenges.md](../ml-solutions-arch/microservices-challenges.md); the cut was wrong, not the transport.

### Independently deployable

The test is operational, not rhetorical: ship **one** service without a fleet release train and without forcing neighbors to rebuild. Failures of the test:

- Shared tables (one quantum pretending to be two).
- A shared **domain** library (`Customer` JARs). Platform libraries — logs, mTLS — are the usual exception (Richards; Azure; Newman).
- Chatty sync so a callee change *is* a caller change (Azure; Lewis/Fowler: a naive in-process → RPC cut is chatty — coarsen the contract).
- A coordinated release calendar (Fowler: then it is not this style).

Independent deployability is Newman’s forcing function: it produces contracts, information hiding, and team ownership. Inverse Conway only works if those teams actually exist.

### Data ownership

Richardson’s three physical options are implementation. The invariant is “no other service’s transaction touches this data.”

| Physical | Overhead | When |
|---|---|---|
| Private-tables-per-service | Lowest | Same engine; grants as the barrier |
| Schema-per-service | Low; ownership clearer | Default on a shared RDBMS |
| Database-server-per-service | Highest | Throughput, blast radius, or a polyglot engine |

Buy: schema autonomy, polyglot persistence. Pay: joins and multi-service writes become application problems (saga / composition / CQRS — catalog B5 / E12 / B7, not this card). Dual-write of two application stores is **permanent** inconsistency, not eventual.

Richards **Data-Driven Migration** vs Dehghani “release the data early” is not a contradiction. Richards: do not pay *N* schema moves while the service is still the wrong size (function first, data last; accept a short shared-schema window). Dehghani: do not leave a finished vertical slice stuck on the monolith DB forever. Sequence: extract coarse → stabilize the contract → cut the schema.

Reach-in reporting — another service’s DB as a read model — fails the invariant. So does a shared `CUSTOMERS` table behind two “services.”

### Sync vs async *between* quanta

The arch-style default is **sync**, async only when necessary — then check the feedback loop. This is a quantum-boundary decision, not a vote for E4.

| Choice | Buy | Pay | Quantum effect |
|---|---|---|---|
| **Sync RPC** | Simple workflow | Latency × availability product (Lewis/Fowler’s “multiplicative effect of downtime”) | **Can merge quanta.** Checkout that *must* sync-call payments *and* inventory inherits both characteristic sets. |
| **Async (events / queues)** | Decoupled runtime | Eventual consistency; an outbox/CDC path to publish safely | Preserves quanta if stale is acceptable. |
| **One sync hop, then events** | User-visible path = one network wait | Two comms styles to operate | [ML patterns](../ml-solutions-arch/ml-microservices-patterns.md): gateway → inference **sync**; train / eval / monitor **async**. |

Fowler 2015: most microservice stories he heard **needed** asynchrony for latency. Guardian’s “one sync call per user request” is the budget, not a slogan. Every remaining sync hop owes C1 + C2 + C7 + C8; the [gateway](ApiGateway.md) is the north–south front door, **not a quantum and not an orchestrator** (Azure: keep domain knowledge *out* of the gateway).

## When to use / when not

**Use** when the system is already too complex as a modular monolith (Fowler premium); you can name **stable** bounded contexts (usually after E1 / E10 / E6 taught them); you can staff the prerequisites *and* the C* tax; cross-capability work is **not** ACID-dominated (or you will coarsen until it isn’t); inverse-Conway product teams exist. A hardware-class split is a valid disintegrator — [microservices in ML](../ml-solutions-arch/microservices-in-ml.md).

**Do not** when:

- **Cross-service transactions dominate.** Style-selection / Richards–Ford: “don’t! Fix the service granularity instead.” Newman: leave that cluster last. Richards 2016: constant ACID-vs-BASE fighting ⇒ too fine. [Distributed transactions](../data-intensive-design/distributed-transactions.md): 2PC/XA is a single point of failure and fights independence. A saga is a *workflow*, not substitute ACID. If most user actions need a saga, the cut is wrong — do not “fix” it with a better orchestrator (that rebuilds SOA).
- The domain is **large and semantically coupled** (style-selection).
- No operational baseline (Fowler prerequisites; Newman: if two services already hurt, ten will).
- Greenfield, unknown domain (Monolith First; SnapCI; Newman) → E10, or E6 if you need a few processes but one database.
- Customer-installed on-prem with no isolation layer (Newman).
- Ultra-low-latency in-process needs ([ch21](../aws/ch21.md) HFT: a network hop is not feasible). [ch08](../aws/ch08.md): the monolith *skips* the network — that is an advantage, not a defect.
- [microservices-challenges.md](../ml-solutions-arch/microservices-challenges.md): **if the project is not big enough, do not**.

## Migration in / out

Mechanism is catalog **B4** (strangler / façade / branch-by-abstraction). This card owns the *destination* decision: a service-with-its-database, not a process in front of the old schema.

**In** (E1 / E10 / E6 → E2):

1. No big-bang (Fowler strangler; [ch08](../aws/ch08.md); Dehghani: each step an atomic improvement).
2. Prerequisites on one or two **edge** capabilities (Fowler 2014; Dehghani warm-up).
3. **E10 → E2:** module + schema-per-module already drawn; extract through a B4 façade.
4. **E1 → E2:** peel an edge; expect a “substantial monolith at the heart” (Monolith First). Do not extract a session / god service.
5. **E6 → E2:** split a coarse service only when a **disintegrator** wins *and* you split its **data**. Shared DB left in place ⇒ quantum count unchanged.
6. Function then data (Richards 2016); CDC/outbox (B7); an anti-corruption layer for leftover callers.
7. Macro then micro (Dehghani, Newman, Richards). Grains of Sand = skipping this.

**Out** is observed and allowed: SnapCI merged back. Transaction or choreography tests failing → consolidate, or drop to E6 / E10. Merging is cheaper than inventing a distributed transaction.

## Worked cut — place-order vs ML serving

Not a scored kata. Two shapes of the same tests (own state, independent deploy, one sync hop).

**Place-order (Richardson credit-limit / FTGO shape).** `Order` write + `Customer.creditLimit` as one ACID → **do not split**; one Ordering service owns the invariant, *or* accept a saga and a visible inconsistency window. Style-selection: don’t. Sync `Pricing` at checkout **merges** availability with Pricing (maybe your *one* Guardian hop; otherwise a replica or an async price). `Notification` = yes, async. Shared `CUSTOMERS` table = **not E2**.

**ML pipeline** (cite [microservices-in-ml.md](../ml-solutions-arch/microservices-in-ml.md) / [ml-microservices-patterns.md](../ml-solutions-arch/ml-microservices-patterns.md)). Preprocess / train / infer / monitor are services only with own runtime, cadence, and scale. Score path: **gateway → inference (sync)**; train / eval / monitor **events**. A shared feature-store database between preprocess and infer fails the boundary test. Isolation + own cadence + own scale is the test; a shared DB, a release train, or a notebook kernel fails it.

C* tax on every **sync** hop. That tax is not a reason to pick E2.

## Failure modes of the style

- **Distributed monolith.** Coordinated deploys, shared DB, or a shared entity library. You paid the network tax and kept the release tax.
- **Chatty calls / sync-merged quanta.** A→B→C on the user path (Azure smell). Every release of A needs B, or A’s latency budget *is* B’s tail. Coarsen the contract or go async; do not add a hop.
- **Grains of Sand** (Richards 2016 ch. 5). Service = class. Tests: scope (“and”s), transactions (BASE pain → coarsen), choreography (five 100 ms hops = 500 ms of cable — his illustration, not a budget). Start coarse.
- **Data-Driven Migration.** Tables move with every extract because the service is still the wrong size.
- **“I Was Taught to Share.”** Domain JARs recreate monolith change-control.
- **Reach-in Reporting.** Another service’s DB as a read model.
- **Timeout-as-availability.** Unbounded waits under load. C1 / C7 tax, not a bigger timeout.
- **Jump on the Bandwagon / Microservice Envy.** Fashion in place of a complexity argument.
- **Saga sprawl.** Most user actions need a saga ⇒ the cut is wrong.
- **Gateway-as-orchestrator.** Domain in C6 couples the services the gateway was meant to hide.
- **Unpaid C* tax.** Fault isolation was the reason you split; a naked sync graph multiplies downtime instead.

Named in the style-selection distillation, **not defined here** (source file missing from the tree): Entity-Trap, Front Controller, Big Ball of Distributed Mud. Do not treat the names as mechanics.

The style also pays the distributed-computing fallacies the workspace lists for any distributed pick — network / latency / bandwidth, **versioning is easy**, **compensating updates always work**, **observability is optional** — and pays them with C*, D*, and contract versioning, not with hope.

## Trade-offs

| Buy | Pay |
|---|---|
| Independent deploy / team autonomy (the people problem) | Fowler premium: provision, CD, monitoring, many repos |
| Firm module boundaries | Wrong boundary is treacle; a network refactor is expensive |
| DB-per-service, polyglot | Joins / writes become app problems (saga / composition / CQRS) |
| Per-service scale and runtime | Performance “often an issue”; chatty cuts miss the user path |
| Fault isolation *in principle* | Only after C* tax; sync graphs multiply downtime |
| Tech diversity / library-version escape | Governance sprawl (Azure); Newman’s polyglot ownership cost |
| Inverse Conway | You must actually *have* those teams |

E6 buys a few coarse processes and usually keeps one database — cheaper quantum count, weaker isolation. E13 buys blast-radius arithmetic (replica the *whole* serving stack per cell) and does not decide how you cut domains. E1 / E10 skip the network; start there unless the monolith is already too complex.

## Sources

Verified 2026-09-13; per-claim provenance and items deliberately left out (including unrecovered star ratings, Newman past the ch. 1 preview, and the missing `microservices-arch.md` file) are in the [external research note](../../docs/research/sysdesign/e2-microservices-external-research.md).

- Lewis & Fowler, *Microservices* (2014-03-25). Fowler, *Prerequisites* (2014-08-28), *Premium* (2015-05-13), *Monolith First* (2015-06-03), *Trade-Offs* (2015-07-01). Dehghani, *How to break a Monolith into Microservices* (2018-04-24).
- Newman, *Building Microservices* 2nd ed. ch. 1 preview; greenfield (2015-04-07); Devoxx Q&A (2015-06-22).
- Richards, *Microservices AntiPatterns and Pitfalls* (2016-07-06). Ford & Richards, Thoughtworks granularity podcast; InfoQ *Hard Parts* podcast.
- Richardson, database-per-service and microservice architecture patterns.
- Azure Architecture Center, *Microservices architecture style* (fetched 2026-09-13).
- Workspace: style-selection.md (quantum facts, matrix row, when-not wording); [aws/ch08.md](../aws/ch08.md); [distributed-vs-single-node.md](../data-intensive-design/distributed-vs-single-node.md); [distributed-transactions.md](../data-intensive-design/distributed-transactions.md); ML microservice notes.
