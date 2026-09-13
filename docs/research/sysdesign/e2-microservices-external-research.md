---
type: research
title: 'Microservice architecture — external research (2026-09-13)'
description: >-
  Group E decision-depth pass for catalog E2: what the style is and is not,
  DB-per-service, independent deployability, sync-vs-async between quanta,
  quantum count as a fact, when-not (cross-service transactions), migration
  from E1/E10/E6 via B4, and C* resilience as required tax.
tags: [research, system-design-patterns, E2, microservices]
---

# Microservice architecture — external research (2026-09-13)

> **What this is.** Catalog **E2** evidence pass (Group E decision bar). No
> library-defaults section — styles have none. Quantum count is a **fact**
> from [style-selection.md](../../../.claude/skills/arch-style/references/style-selection.md);
> this note does **not** run arch-style’s four determinations or scoring
> micro-loop. Primary pages fetched 2026-09-13. Unverified items stay in
> **Uncertain / left out**.
>
> **Cite, do not rewrite:**
> [aws/ch08.md](../../../cases/aws/ch08.md),
> [ml-microservices-patterns.md](../../../cases/ml-solutions-arch/ml-microservices-patterns.md),
> [microservices-in-ml.md](../../../cases/ml-solutions-arch/microservices-in-ml.md),
> [microservices-challenges.md](../../../cases/ml-solutions-arch/microservices-challenges.md),
> [distributed-vs-single-node.md](../../../cases/data-intensive-design/distributed-vs-single-node.md),
> [rest-rpc-dataflow.md](../../../cases/data-intensive-design/rest-rpc-dataflow.md),
> [distributed-transactions.md](../../../cases/data-intensive-design/distributed-transactions.md).
> C* cards are **required tax**, not this card.

---

## 1. Scope and non-goals

**Owns** the *style*: one application as independently deployable,
domain-shaped services, each with its own persistence, talking over the
network. Decision depth: what it is / is not; quantum count as fact;
when-to / when-not; migration in/out; worked cut; trade-off table.

| Sibling | Why not this card |
|---|---|
| **E1 / ⊕E10** | Starting / cheaper one-quantum styles (monolith, modular monolith). |
| **E6** | Orchestration-driven SOA *and* modern service-based (UI + ≤12 domain services, usually one DB). Microservices ≠ “SOA with REST.” |
| **E4** | Style-level EDA. Microservices *use* events; they are not EDA. |
| **B4** | Incremental-cutover *mechanism* into E2. |
| **B5 / ⊕B7** | Saga and outbox/CDC *mechanisms*. This card only names the when-not. |
| **C6** | North-south gateway / BFF. Azure: keep domain knowledge *out* of the gateway. |
| **C1 / C2 / ⊕C7 / ⊕C8** | Breaker, retry/budget, timeouts, bulkhead. **Required tax**, not the style. |
| **⊕E11 / ⊕E12** | FaaS is a host; CQRS/ES are Richardson’s query/write complements. |

Non-goals: scoring monolith-vs-microservices; library/mesh defaults; rewriting the cited `cases/` notes.

---

## 2. Lineage / vocabulary

**Lewis & Fowler, *Microservices* (2014-03-25)** — https://martinfowler.com/articles/microservices.html — first widely cited definition, and they refuse a formal one. Style = one application as a suite of services, **each in its own process**, lightweight comms (often HTTP), **around business capabilities**, **independently deployable** by automation, **bare minimum of centralized management**, possibly polyglot language *and* store. Term: Venice May 2011; name May 2012. Netflix then said “fine-grained SOA.” Nine traits: componentization via services; capability organization; products not projects; **smart endpoints, dumb pipes**; decentralized governance; **decentralized data**; infrastructure automation; design for failure; evolutionary design. Sidebar *How big?*: the name “lead[s] to an unfortunate focus on … size.” Range: two-pizza team (≤ ~12 people) down to half-a-dozen people / half-a-dozen services. Size is not the discriminator. Sidebar *SOA*: the term “means too many different things”; the common form they saw was ESBs integrating monoliths. Sidebar *Synchronous calls considered harmful*: Guardian = **one sync call per user request**; Netflix rebuilt the platform API around asynchrony. Decentralized data: own DB / polyglot persistence; **transactionless** coordination; eventual consistency + compensations. A service may be several processes shipped together (app + *its* database).

**Newman.** 2nd ed. ch. 1 (O’Reilly preview, 2026-09-13): “independently releasable services … modeled around a business domain”; “a type of [SOA], albeit one that is opinionated about how service boundaries should be drawn, and one in which **independent deployability is key**.” Shared databases are “especially problematic.” Devoxx Q&A (2015-06-22, https://samnewman.io/blog/2015/06/22/answering-questions-from-devoxx-on-microservices/): that principle is “the most important”; a shared domain-object library that forces client upgrades **loses** it. Asked “how big?”, answered “42” — then: size is how many services you can *operate*, not LOC. Transactions: “Avoid! … leave them till last.” Greenfield (2015-04-07, https://samnewman.io/blog/2015/04/07/microservices-for-greenfield/): SnapCI knew CI, still got boundaries wrong, **merged back**; split only *clear* edges; if two services already hurt, ten will. Schema-per-future-module inside a monolith keeps the later data split cheap. Customer-installed on-prem fits badly.

**Fowler follow-ons (fetched 2026-09-13).** *Prerequisites* (2014-08-28, https://martinfowler.com/bliki/MicroservicePrerequisites.html): rapid provision, monitoring (technical *and* business), rapid deploy → DevOps; a handful of services first. *Premium* (2015-05-13, https://martinfowler.com/bliki/MicroservicePremium.html): **do not even consider** the style unless the system is too complex as a monolith; Radar *Microservice Envy*; observed 60 people / 20 services vs 4 / 200. *Monolith First* (2015-06-03, https://martinfowler.com/bliki/MonolithFirst.html): almost all successes started as a too-big monolith; almost all greenfield-as-microservices stories he had heard ended badly. Variants: modular then split; peel edges; sacrificial monolith; coarse “duolith.” *Trade-Offs* (2015-07-01, https://martinfowler.com/articles/microservice-trade-offs.html): buy boundaries / independent deploy / tech diversity; pay distribution / eventual consistency / ops complexity. Coordinated releases “is not a microservice architecture.” No convincing “selective scale is cheaper than cookie-cutter monolith replicas” report.

**Richards (fetched 2026-09-13).** *Microservices AntiPatterns and Pitfalls* (O’Reilly, July 2016, ISBN 978-1-491-96331-9; first release 2016-07-06), https://www.developertoarchitect.com/downloads/microservices-pitfalls.pdf — antipattern = seemed good (Koenig); pitfall = never was (Ford). **Data-Driven Migration**: function *and* data together → repeated schema moves; “functionality first, data last.” **Timeout**: doubled-under-load wait → breaker (C1 tax). **“I Was Taught to Share”**: share-as-little-as-possible; domain JARs recreate monolith change-control (platform/security.jar is the exception). **Reach-in Reporting**: another service’s DB. **Grains of Sand**: service = class; tests = scope, **ACID need**, **choreography** (five 100 ms hops = 500 ms of cable); start coarse. **Jump on the Bandwagon**; **Give It a Rest**. Thoughtworks podcast with Ford (https://www.thoughtworks.com/en-us/insights/podcasts/technology-podcasts/software-service-granularity-getting-it-right): **disintegrators** (scope, volatility, scale, FT, security, extensibility) vs **integrators** (transactions, chatter, shared code, data relationships). Service-based (E6) = “as far toward microservices as we can get, but we’re keeping a single database.” InfoQ *Hard Parts* (https://www.infoq.com/podcasts/software-architecture-hard-parts/): data *inside* the service makes **transactionality an architecture decision**.

**Richardson.** https://microservices.io/patterns/data/database-per-service.html · https://microservices.io/patterns/microservices.html — data private, reachable **only** via the API; a transaction touches **that** DB. Physical: private-tables / schema-per-service / server-per-service (enforce with grants). Writes → saga (B5); reads → API composition or CQRS (E12). Distributed transactions “best avoided.”

**Azure style page** (fetched 2026-09-13; `ms.date` **not on page** — §7) — https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/microservices — bounded-context services, **own data**, polyglot persistence, gateway entry, messages for async. Chatty A→B→C is a design smell. “Functions that are likely to change together should be packaged and deployed together.” Antipatterns: no domain analysis; sharing **domain** libraries; exposing services to clients (C6); domain in the gateway.

**Dehghani (2018-04-24)** — https://martinfowler.com/articles/break-monolith-into-microservices.html — “size … matters least”; “microservices is a label and not the description.” Journey: warm up on a decoupled edge; **minimize dependency back to the monolith**; do **not** extract a “session service”; decouple **vertically and release the data early**; **macro first, then micro**; each step an atomic improvement.

**Workspace.** [style-selection.md](../../../.claude/skills/arch-style/references/style-selection.md) (FSA ch7+ch18). Cited `microservices-arch.md` is **not in the tree** (§7). Quantum = smallest independently runnable part; **the DB is part of the quantum** (shared DB ⇒ quantum of one). After choosing sync vs async, **re-check** — **sync can silently merge quanta**. Ch18 row: fine-grained services, DB-per-service, API layer; domain (extreme); **quanta = most of any style**; deploy/test/FT/scale/elasticity/evolvability **HI**; performance “often an issue.” Stars **—**. When-not: transactions dominate (“don’t! Fix the service granularity instead”) or the domain is large and semantically coupled. Named (file missing): Big Ball of Distributed Mud, Grains of Sand, Entity-Trap, Front Controller. [aws/ch08.md](../../../cases/aws/ch08.md): monolith *skips* the network (an advantage); each service “may require its own database.” [distributed-vs-single-node.md](../../../cases/data-intensive-design/distributed-vs-single-node.md): “primarily a **technical solution to a people problem**.” [microservices-in-ml.md](../../../cases/ml-solutions-arch/microservices-in-ml.md): isolation + own cadence + own scale; shared DB / release train / notebook kernel **fails** the test.

---

## 3. Mechanics (Group E decision depth)

### 3.1 What it is

1. Component = **service** (out-of-process), not a library
   (Lewis/Fowler). May include the DB process shipped with it.
2. **Independently deployable.** Fowler: coordinated releases ⇒ not
   this style. Newman: that forcing function produces contracts,
   information hiding, and team ownership.
3. **Owns its state.** Richardson’s three physical options are
   implementation; the invariant is “no other service’s transaction
   touches this data.” Richards/Ford: the DB is *inside* the quantum.
4. Boundaries = **business capability / bounded context**, not
   technical layer (Conway).
5. **Dumb pipes** (HTTP or a fabric that only routes). An ESB that
   owns routing + transform + rules is E6, not E2.
6. Failure is a design input. C* tax on every sync hop.

Stronger than “many small HTTP processes.”

### 3.2 What it is not

| Look-alike | Why not E2 |
|---|---|
| **“Small services”** | Size is not the discriminator (Lewis/Fowler, Dehghani, Newman). A two-pizza service still qualifies; a 200-LOC class-as-HTTP is **Grains of Sand**. |
| **SOA-with-REST / ESB** | Same network, opposite governance: smart pipe, often shared canonical model + DB. **E6.** |
| **Service-based** | E6 modern variant: coarse domain services, **usually one DB**. Style-selection: ≤12; **no 5★** — differentiator is cost+simplicity. Shared DB ⇒ **one quantum**. |
| **Modular monolith** | **E10.** Newman Asterix: schema-per-future-module *inside* one runtime. |
| **Distributed monolith** | Many processes, lock-step release, or shared entity library (Fowler fn. 2; Newman; Richards share-nothing). |
| **EDA** | **E4.** Events are a comms *choice* between quanta. |
| **N-tier** | Technical layers, often one DB / one deployable (ch08). |

### 3.3 Quantum count — fact, not a score

Style-selection comparison matrix (ch18):

| Style | Quanta |
|---|---|
| Layered / modular monolith / pipeline / microkernel | 1 |
| Service-based | ≥1 |
| Event-driven | 1–many |
| **Microservices** | **most of any style** |

Not a target headcount. Fowler’s 20-vs-200 and Newman’s “how many can
you operate” are the constraint. E6’s “~12” is an **E6** fact, not an
E2 default. **Do not score candidates here.**

Coupling test: shared DB ⇒ same quantum. Sync between mismatched
characteristic-sets **collapses them** (inherit the slower partner).
Re-check boundaries after choosing sync vs async.

### 3.4 DB-per-service

| Physical (Richardson) | Overhead | When |
|---|---|---|
| Private-tables-per-service | Lowest | Same engine; grants as the barrier |
| Schema-per-service | Low; ownership clearer | Default on a shared RDBMS |
| Database-server-per-service | Highest | Throughput, blast radius, or polyglot engine |

Buy: schema autonomy, polyglot. Pay: joins and multi-service writes
(B5 / E12 / B7 — not this card). Dual-write of two app stores is
**permanent** inconsistency (B4/B7), not eventual.

Richards **Data-Driven Migration** vs Dehghani “release the data
early”: not a contradiction. Richards = do not pay *N* schema moves
while the service is still the wrong size (function first, data last,
accept a short shared-schema window). Dehghani = do not leave a
finished vertical slice stuck on the monolith DB forever. Sequence:
extract coarse → stabilize contract → cut schema.

### 3.5 Independent deployability

Test: change, test, release **one** service without changing
neighbors. Failures: shared tables; shared **domain** library
(Newman, Azure, Richards); a fleet release train; chatty sync so a
callee change is a caller change (Azure; Lewis/Fowler: naive
in-process → RPC is chatty — coarsen the contract). Platform
libraries (logs, mTLS) are the usual exception; `Customer` JARs are
not.

### 3.6 Sync vs async *between* quanta

Arch-style default: **sync**, async only when necessary — then check
the feedback loop.

| Choice | Buy | Pay | Quantum effect |
|---|---|---|---|
| **Sync RPC** | Simple workflow | Latency × availability product (Lewis/Fowler “multiplicative effect of downtime”) | **Can merge quanta.** Checkout that *must* sync-call payments *and* inventory inherits both characteristic sets. |
| **Async (events/queues)** | Decoupled runtime | Eventual consistency; B7 to publish safely | Preserves quanta if stale is acceptable. |
| **One sync hop, then events** | User SLO = one network wait | Two comms styles | [ml-microservices-patterns.md](../../../cases/ml-solutions-arch/ml-microservices-patterns.md): gateway → inference **sync**; train/eval/monitor **async**. |

Fowler 2015: most microservice stories he heard **needed** asynchrony
for latency. This is **not** E4 (broker vs mediator). It is whether a
quantum boundary may be a blocking call.

### 3.7 Characteristics (prose-recovered; honest `—`)

Star-rating **figures are missing**. Unrecovered cells are `—`.

| Characteristic | Microservices (prose) |
|---|---|
| Deploy / test | **HI** (definitional) |
| Fault tolerance | **HI** — only if C* tax is paid; a sync graph is otherwise *less* available |
| Scale / elasticity | **HI** as capability. Fowler 2015: no convincing “selective scale is cheaper than monolith replicas” report |
| Evolvability | **HI** |
| Performance | **“often an issue”** |
| Simplicity / cost | **—** (prose: premium is high) |
| Stars 1–5 | **—** |

E6’s recovered 4★/3★/2★ stay on E6.

### 3.8 When to use / when not

**Use** when: the system is already too complex as a modular monolith
(Fowler premium); you can name **stable** bounded contexts (usually
after E1/E10/E6 taught them); you can staff prerequisites + C* tax;
cross-capability work is **not** ACID-dominated (or you will coarsen
until it isn’t); inverse-Conway small product teams exist. Hardware
class split (GPU train vs CPU serve) is a valid disintegrator —
[microservices-in-ml.md](../../../cases/ml-solutions-arch/microservices-in-ml.md).

**Do not** when:

- **Cross-service transactions dominate.** Style-selection /
  Richards-Ford: “don’t! Fix the service granularity instead.”
  Newman: leave that cluster last. Richards 2016: constant
  ACID-vs-BASE fighting ⇒ too fine. [distributed-transactions.md](../../../cases/data-intensive-design/distributed-transactions.md):
  2PC/XA is a SPOF and fights independence. B5 is a *workflow*, not
  substitute ACID.
- Domain is **large and semantically coupled** (style-selection).
- No operational baseline (Fowler prerequisites; Newman “two already
  hurt”).
- Greenfield, unknown domain (Monolith First; SnapCI; Asterix) →
  E10, or E6 if you need a few processes but one DB.
- Customer-installed on-prem with no isolation layer (Newman).
- Ultra-low-latency in-process needs ([aws/ch21.md](../../../cases/aws/ch21.md)
  HFT: a network hop is not feasible).
- [microservices-challenges.md](../../../cases/ml-solutions-arch/microservices-challenges.md):
  **if the project is not big enough, do not**.

### 3.9 Migration in / out (via B4)

**In** (E1 / E10 / E6 → E2). Mechanism is **B4**. Style sequence:

1. No big-bang (Fowler strangler; ch08; Dehghani atomic steps).
2. Prerequisites on one or two **edge** capabilities (Fowler 2014;
   Dehghani warm-up).
3. **E10 → E2:** module + schema-per-module already drawn; extract
   through a B4 façade or Branch by Abstraction.
4. **E1 → E2:** peel an edge; expect a “substantial monolith at the
   heart” (Monolith First). Do not extract a session/god service.
5. **E6 → E2:** split a coarse service only when a **disintegrator**
   wins *and* you split its **data**. Shared DB left in place ⇒
   quantum count unchanged.
6. Function then data (Richards 2016); CDC/outbox (B7); ACL for
   leftover callers (B4 companion).
7. Macro then micro (Dehghani, Newman, Richards). Grains of Sand =
   skipping this.

**Out.** Observed and allowed: SnapCI merged back. Transaction or
choreography tests failing → consolidate (or drop to E6/E10). Merging
is cheaper than inventing a distributed transaction. B4 owns traffic
knobs; this card owns the decision that the destination is a
service-with-its-DB.

### 3.10 Worked example — checkout vs ML serving

Not a scored kata.

**Place-order (Richardson credit-limit / FTGO shape).**
`Order` write + `Customer.creditLimit` as one ACID → **do not split**;
one Ordering service owns the invariant, *or* accept B5 and a visible
window. Style-selection: don’t. Sync `Pricing` at checkout **merges**
availability with Pricing (maybe your *one* Guardian hop; else a
replica). `Notification` = yes, async + B7. Shared `CUSTOMERS` table
= **not E2** (one quantum pretending to be two).

**ML pipeline** (cite
[ml-microservices-patterns.md](../../../cases/ml-solutions-arch/ml-microservices-patterns.md)
/ [microservices-in-ml.md](../../../cases/ml-solutions-arch/microservices-in-ml.md)).
Preprocess / train / infer / monitor are services only with own
runtime, cadence, and scale. Score path: **gateway → inference
(sync)**; train/eval/monitor **events + saga**. A preprocess RPC on
the score path is the latency failure in
[microservices-challenges.md](../../../cases/ml-solutions-arch/microservices-challenges.md).
Shared feature-store DB between preprocess and infer fails the
boundary test.

C* tax on every **sync** hop. That tax is not a reason to pick E2.

### 3.11 Trade-off table

| Buy | Pay |
|---|---|
| Independent deploy / team autonomy (the people problem) | Fowler premium: provision, CD, monitoring, many repos |
| Firm module boundaries | Wrong boundary is treacle; network refactor is expensive |
| DB-per-service, polyglot | Joins/writes become app problems (saga / composition / CQRS) |
| Per-service scale and runtime | Performance “often an issue”; chatty cuts miss SLOs |
| Fault isolation *in principle* | Only after C* tax; sync graphs multiply downtime |
| Tech diversity / library-version escape | Governance sprawl (Azure); Newman polyglot ownership cost |
| Inverse Conway | You must actually *have* those teams |

---

## 4. Failure modes and when-not (of the style)

- **Grains of Sand** (Richards 2016 ch. 5). Service = class. Tests:
  scope (“and”s), transactions (BASE pain → coarsen), choreography
  (too many hops). Start coarse.
- **Data-Driven Migration** (ch. 1). Tables move with every extract.
- **“I Was Taught to Share”** (ch. 3). Domain JARs across services.
- **Reach-in Reporting** (ch. 4). Another service’s DB as a read
  model.
- **Timeout-as-availability** (ch. 2). C1/C7 tax.
- **Jump on the Bandwagon** (ch. 7). Fowler Envy; fashion check.
- **Distributed monolith.** Coordinated deploys; shared DB; shared
  entity library.
- **Sync-merged quanta.** Every release of A needs B, or A’s SLO is
  B’s p99.
- **Entity-Trap / Front Controller / Big Ball of Distributed Mud.**
  **Named** in style-selection (`microservices-arch.md:52,169,254-260`);
  source file missing — **definitions not asserted** (§7).
- **Saga sprawl.** Most user actions need a saga ⇒ the cut is wrong
  (do not “fix” it with a better orchestrator — that rebuilds SOA).
- **Gateway-as-orchestrator.** Azure + C6: domain in the gateway
  couples services.

When-not list is in §3.8; the headline remains: **don’t do
cross-service transactions — fix granularity.**

---

## 5. Cross-links

| Id / note | Relationship |
|---|---|
| **C1 / C2 / ⊕C7 / ⊕C8** | **Required tax** on every sync hop. Lewis/Fowler already point at Nygard; Richards’ Timeout antipattern resolves to a breaker. |
| **C6** | Front door. Not a quantum. Not an orchestrator. |
| **E4 / A2** | Async *between* quanta. |
| **B5 / ⊕B7** | Mechanisms for writes DB-per-service made hard. |
| **B4** | How E1/E10/E6 become E2. |
| **E1 / E10 / E6** | Origins and cheaper alternatives. |
| **⊕E12** | Richardson query complement. |
| [aws/ch08.md](../../../cases/aws/ch08.md) | Monolith / N-tier / microservice evolution; saga / gateway / mesh as tax. |
| ML microservices notes | Worked ML cut; “patterns do not make a bad cut good.” |
| DDIA notes in the header | People-problem framing; encoding; why 2PC is not the way out. |
| [style-selection.md](../../../.claude/skills/arch-style/references/style-selection.md) | Quantum facts, matrix row, when-not wording. |
| Fallacies (style-selection ch9) | E2 pays: network/latency/bandwidth, **versioning is easy**, **compensating updates always work**, **observability is optional**. Pay with C*/D*/A6. |

---

## 6. Sources

Fetched 2026-09-13.

- Lewis & Fowler, *Microservices* (2014-03-25). https://martinfowler.com/articles/microservices.html
- Fowler, *Prerequisites* (2014-08-28), *Premium* (2015-05-13), *Monolith First* (2015-06-03), *Trade-Offs* (2015-07-01), guide hub. https://martinfowler.com/bliki/MicroservicePrerequisites.html · https://martinfowler.com/bliki/MicroservicePremium.html · https://martinfowler.com/bliki/MonolithFirst.html · https://martinfowler.com/articles/microservice-trade-offs.html · https://martinfowler.com/microservices/
- Dehghani (2018-04-24). https://martinfowler.com/articles/break-monolith-into-microservices.html
- Newman, 2nd ed. ch. 1 preview. https://www.oreilly.com/library/view/building-microservices-2nd/9781492034018/ch01.html
- Newman, greenfield (2015-04-07); Devoxx Q&A (2015-06-22). https://samnewman.io/blog/2015/04/07/microservices-for-greenfield/ · https://samnewman.io/blog/2015/06/22/answering-questions-from-devoxx-on-microservices/
- Richards, *AntiPatterns and Pitfalls* (2016-07-06). https://www.developertoarchitect.com/downloads/microservices-pitfalls.pdf
- Ford & Richards, Thoughtworks granularity podcast; InfoQ *Hard Parts* podcast. https://www.thoughtworks.com/en-us/insights/podcasts/technology-podcasts/software-service-granularity-getting-it-right · https://www.infoq.com/podcasts/software-architecture-hard-parts/
- Richardson, DB-per-service + architecture pattern. https://microservices.io/patterns/data/database-per-service.html · https://microservices.io/patterns/microservices.html
- Azure style page. https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/microservices
- Workspace: style-selection.md; aws/ch08.md; ML + DDIA notes in the header.

---

## 7. Uncertain / left out

Must **not** be implied as fact in the Concept.

- **`cases/ArchitectureBook/microservices-arch.md` is not in the
  tree** (searched MAIN `cases/` and both arch-style reference
  trees). Style-selection cites `:52,169,183-187,254-260,296-305,313-323`.
  “Most of any style,” HI / “often an issue,” “don’t! Fix the service
  granularity instead,” and the *names* Entity-Trap / Front Controller
  / Big Ball of Distributed Mud therefore rest on the **distillation**,
  not a fetched FSA chapter. Those three antipatterns are **not
  defined** above.
- **Star ratings** for microservices: `—`. E6’s recovered stars stay
  on E6.
- **Azure `ms.date`.** Not on the 2026-09-13 fetch. Treat as “as
  fetched.”
- **Newman 2nd ed. beyond the ch. 1 preview** — not used.
- **Richards *Microservices vs. SOA* (Nov 2015, ISBN 978-1491956687).**
  `developertoarchitect.com/books.html` returned HTTP 409. Not used.
  E6 needs its own primary pass.
- **FSA / Hard Parts chapter text.** Podcasts only. Disintegrator
  lists are Ford speaking on the Thoughtworks page.
- **Guardian / Netflix originals** behind Lewis/Fowler’s report —
  not re-fetched.
- **Headcount / service-count defaults.** None. 20-vs-200 is an
  observation.
- **Library, mesh, Kubernetes defaults.** Out of scope (C*/B6).
- Unofficial FSA note sites seen in search — **not** cited.
