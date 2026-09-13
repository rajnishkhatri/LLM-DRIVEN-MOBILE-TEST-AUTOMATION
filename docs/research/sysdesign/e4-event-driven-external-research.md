---
type: research
title: 'Event-driven architecture — external research (2026-09-13)'
description: >-
  Group E decision-depth note for catalog E4: what EDA is and is not,
  broker vs mediator as topologies, quantum count 1–many from
  style-selection, when-to / when-not, migration, worked example, and
  trade-offs. Mechanisms stay in A2/B7.
tags: [research, system-design-patterns, E4, event-driven]
---

# Event-driven architecture — external research (2026-09-13)

> **What this is.** The evidence pass for catalog id **E4** (Group E — Architectural styles). Style and decision depth only. Mechanisms — channels, delivery claims, competing consumers, fan-out, ordering, DLQ, reconnect — live in **[A2](a2-pubsub-queues-external-research.md)**. How a write becomes an event atomically lives in **[B7](b7-outbox-cdc-external-research.md)**. The Concept (when written) should stay readable; this note keeps fetched facts, dates, and URLs.
>
> **Method.** Primary pages fetched 2026-09-13. Paraphrase; identifiers and dates reproduced exactly. Quantum count and the 2nd-edition star ratings are taken as **facts from** [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md) — this note does **not** re-run arch-style’s four determinations or scoring loop. Items that could not be verified are in §8 and are **not** to be implied as fact.
>
> **Existing notes** (cite; do not rewrite; MAIN repo cases): [event-driven-dataflow](../../../cases/data-intensive-design/event-driven-dataflow.md) (broker job, queue vs topic), [event-sourcing-cqrs](../../../cases/data-intensive-design/event-sourcing-cqrs.md) (E12 persistence style), [aws/ch08.md](../../../cases/aws/ch08.md) (choreography vs orchestration; outbox one-liner; EDA vs event sourcing), [distributed-transactions](../../../cases/data-intensive-design/distributed-transactions.md) (B5 / exactly-once processing), [B4 strangler](b4-strangler-fig-external-research.md) (Event Interception as a migration seam).

---

## 1. Scope and non-goals

**Owns.** Event-driven architecture as a *style*: processors that react to things that happened, wired through a broker **or** a mediator; the initiating-event → derived-event shape; quantum count; when the style is the right (or wrong) pick; how to migrate in or out; a worked example; a trade-off table. Broker vs mediator are **topologies of the style**, not A2 channel kinds.

**Does not own.**

| Sibling | Why it stays there |
|---|---|
| **A2** pub/sub, queues, streams | Wire semantics, competing consumers, fan-out, ordering, DLQ, consumer groups, reconnect, proxy/LB. A2 already flags E4 as “style, quanta, migration.” |
| **B7** transactional outbox & CDC | How a local write becomes an event *without* a dual-write. E4 names the seam and points here. |
| **B5** saga | Multi-step compensation once you have chosen choreography (broker) or orchestration (mediator). Azure’s EDA page names both and then stops. |
| **E12** CQRS & event sourcing | A persistence / read-model style that *often rides* events. Fowler (2017-02-07): CQRS “isn’t really about events”; event sourcing can be synchronous. Related, not identical. |
| **E2** microservice architecture | Domain-partitioned, independently deployed services. EDA can stand alone, sit *inside* one service, or be the async fabric *between* services. Using Kafka does not make you E2; splitting a DB does not make you E4. |
| **A1** request–response | The request-based model EDA is defined against. A reply-queue over a broker is A1 wearing A2 clothes, not this style. |
| **E9** hub-and-spoke | Hohpe’s Message Broker as an *integration* architecture. Overlaps the mediator vocabulary; not the EDA style card. |
| **C9 / C10** | Idempotency of consumers; backpressure. Named as costs of the style, not restated. |

**Non-goals.** Library or broker defaults (Group E has none). Scoring monolith-vs-distributed. Re-deriving DLQ, outbox, or CDC. Writing a Concept.

---

## 2. Lineage / vocabulary

**Hohpe & Woolf, *Enterprise Integration Patterns* (Addison-Wesley, 2003).** Three names this catalog must not collapse:

- **Message Broker** (architecture pattern, not a product): a central component that receives messages, decides the destination, and routes. Hohpe’s public pattern page (fetched 2026-09-13) calls it the hub-and-spoke style and compares it to Pipes and Filters at a larger scope. The ch. 3 extract on enterpriseintegrationpatterns.com names it **the integration equivalent of the GoF Mediator**. Trade-off he states on the same page: central maintenance vs a **throughput bottleneck**; mitigate with stateless scale-out, or a *hierarchy* of brokers so a local broker handles a “subnet” and only cross-subnet traffic hits the centre. The 2003-11-12 rambling *Hub and Spoke* adds protocol translation and a Message Translator: without translation, location transparency is an illusion; the hub also recreates the n-squared problem at the *metadata* level unless you adopt a canonical model.
- **Message Bus**: shared infrastructure plus a common command set (usually a canonical data model). Participants speak the bus; the bus is not an active per-message mediator. Already distinguished in [A2 §2](a2-pubsub-queues-external-research.md).
- **Event-Driven Consumer** (endpoint pattern): the messaging system *hands* a message to a callback; the receiver has no running thread until delivery. Opposite of a Polling Consumer. **This is not the EDA style.** A request-driven monolith can use an event-driven consumer on a queue; an EDA processor can poll. Hohpe’s own warning (Messaging Endpoints intro): event-driven consumers process as fast as messages arrive and can overload the server — throttle by limiting consumer count.

**Fowler, “Focusing on Events” (undated P of EAA draft; linked from the 2017 note).** Enterprise applications as systems that react to events from the outside world; the 1980s structured-design lineage; Event Messages decouple identity (broadcast without naming the receiver) and time (queue until the receiver is ready).

**Fowler, “Event Collaboration” (2006-06-19).** Components raise events on state change; others listen. The sender does not name the recipient. Adding a risk-tracker does not require changing the stock exchange — you subscribe. Coupling *moves* from request interfaces to event schemas: change an event and you still have repercussions. Commands phrased as events are a trap (he later names this “passive-aggressive command”). Just raising an event is not enough when you need a job done — someone must *accept* it.

**Fowler, “What do you mean by ‘Event-Driven’?” (2017-02-07).** ThoughtWorks summit: the word “event” hides four different things. Keep them un-collapsed:

| Pattern | What it is | Style-level cost |
|---|---|---|
| **Event Notification** | “Something changed”; often an id + a link back. Source does not care about the response. | Lowest coupling; a logical flow that spans notifications is **invisible in any program text** — you reconstruct it from a live system. |
| **Event-Carried State Transfer** | The event carries the changed data so consumers stop calling back. | Resilience and lower load on the source; many copies; consumers must maintain state. Azure (2026) restates this as “all attributes in the payload” vs “keys only.” |
| **Event Sourcing** | The event log *is* the source of truth; current state is derived. Git is the example. **Need not be asynchronous.** | Replay, audit, alternative histories; schema evolution and external-system replay are the hard parts. **E12.** |
| **CQRS** | Separate models for write and read. **Need not use events.** | Fowler is “deeply wary”; majority of cases he had seen were harmful. **E12.** |

**Richards, *Software Architecture Patterns* (O’Reilly, first release 2015-02-24).** Public report that first popularised the **mediator vs broker** pair as EDA *topologies*. Mediator: event queue → mediator → processing events on dedicated channels → processors; the mediator knows the steps, does not do the business work. Broker: no central mediator; processors consume, act, and publish the next derived event in a relay-race chain; unused events are normal (they leave room to evolve). Same insurance-relocation example in both topologies (see §3.5). Ratings in this 2015 report are High/Low prose, **not** the later star card — do not mix them.

**Richards & Ford, *Fundamentals of Software Architecture*, 2nd ed. (O’Reilly, March 2025), ch. 15 *Event-Driven Architecture Style*.** Workspace distillation is [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md) (loaded as the arch-style SoT). Opening sentence recovered from the O’Reilly chapter listing (fetched 2026-09-13; full chapter body is paywalled — §8): EDA is a distributed, asynchronous style of decoupled processors that trigger and respond to events; it can be a **standalone style or embedded** in another (the example given is event-driven microservices). 1st edition placed the same chapter at ch. 14 (2020). This note treats the 2nd-edition comparison-matrix row as the rating source of record.

**Azure Architecture Center, “Event-Driven Architecture Style”** (`ms.date` **2026-03-06**, fetched 2026-09-13). Independent restatement of broker vs mediator; when-to / when-not; payload fat vs thin; hybrid with microservices, pipes-and-filters, and event sourcing. The page’s pub/sub-vs-stream and competing-consumers rows are **A2** — cited there, not re-derived.

**AWS, “What is an Event-Driven Architecture?”** (product page, fetched 2026-09-13). Three components: producers, a **router**, consumers. An event is a state change or update; it may carry state or be an identifier. Marketing claims (cut cost because push-not-poll; EventBridge vs SNS as the two “router” types) are vendor positioning, not style facts. Useful only for the producer / router / consumer vocabulary and the “indirection means dynamic tracking, not static call-graph tracking” caveat — the same trap Fowler named in 2017.

**This workspace’s [aws/ch08.md](../../../cases/aws/ch08.md).** Choreography = broker-shaped (no central coordinator; services react). Orchestration = mediator-shaped (a coordinator owns the flow). Hybrid: orchestrate the order core, choreograph notifications and analytics. State-oriented EDA vs event sourcing is an *implementation* fork, not a topology fork — event sourcing is **E12**.

---

## 3. Mechanics (Group E decision depth bar)

### 3.1 What the style is — and is not

**Is.** A system whose default collaboration is *reaction to facts that already happened*. An **initiating event** enters; processors do a single business task and emit **derived / processing events**; no processor needs to know who is listening. Richards 2015 and Azure 2026 both split the style into two topologies (broker, mediator). style-selection.md records the topology as “processors + broker (or mediator); initiating→derived events” and the partitioning as **technical**.

**Is not.**

- **Not “we bought a broker.”** Queues, topics, and logs are A2 primitives. A synchronous order API that writes to SQS and waits on a reply queue is still request-based (Azure’s own request-response-messaging escape hatch; Hohpe Request-Reply).
- **Not Hohpe’s Event-Driven Consumer.** Push vs poll is an endpoint choice.
- **Not microservices (E2).** Independent deployability and DB-per-service are E2 decisions. EDA can live in one deployable.
- **Not CQRS / event sourcing (E12).** Event sourcing is a way to persist; CQRS is a way to split models. Fowler 2017: people who “did event sourcing” and then complained that every change meant updating two models were usually doing CQRS; people who blamed “lots of async” were paying a cost that neither pattern requires.
- **Not a workflow engine.** A mediator *uses* an orchestrator (Camel, a BPM, a saga orchestrator — B5); the style question is whether *anyone* owns the multi-step state.
- **Not notification-as-command.** Fowler 2017: if the source expects the recipient to act, send a command. Styling it as an event hides the dependency and is the “passive-aggressive command.”

Request-based contrast (Richards/Ford, recovered from the chapter listing + Azure when-not): “get my last six months of order history” is a deterministic, data-driven request — it belongs on A1, not on an event bus.

### 3.2 Broker vs mediator — topologies, not A2 mechanics

These are **who owns the workflow**, not queue-vs-topic.

| | **Broker topology** | **Mediator topology** |
|---|---|---|
| **Who owns multi-step state?** | No one. Each processor acts and publishes what *it* did. Azure: “no component owns or is aware of the state of any multistep business transaction.” | The mediator. It keeps state, handles errors, and can restart. Processors answer the mediator; they do not broadcast completion to the world (Azure; Richards 2015). |
| **What travels** | Facts / derived events (“address changed”). Unused events are normal — they are the evolvability hook (Richards 2015). | Commands / processing events on designated channels, often queues (Azure). Consumers are *expected* to process them. |
| **Control vs decoupling** | Highest decoupling, dynamic subscribers, no central restart. Distributed transactions are risky; inconsistency is a designed-in possibility (Azure). | More control, better distributed error handling, potentially better consistency; more coupling; the mediator is a bottleneck and a reliability concern (Azure). |
| **Closest siblings** | Choreography ([aws/ch08.md](../../../cases/aws/ch08.md)); A2 pub/sub or log. | Orchestration; B5 saga-orchestration; Hohpe Message Broker / E9. |
| **When** | Simple or independently evolvable flows; you want 5★ evolvability (style-selection). | Multiple coordinated steps, conditional paths, restart-from-step-N (Richards 2015 stock-trade / relocation; Azure). |

Do **not** recast this as “Kafka = broker, Step Functions = mediator.” A Kafka topic plus a process manager that consumes and dispatches commands *is* mediator topology. A fleet of EventBridge rules with no owner of the order *is* broker topology. The product is A2; the topology is E4.

Hohpe’s bottleneck warning applies to the **mediator** (and to a mediating Message Broker), not to a dumb log. A2 already owns dumb-vs-mediating *brokers* as products; here the word “mediator” means the workflow owner.

### 3.3 Quantum count — FACT from style-selection

From [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md) comparison matrix (Event-driven, ch15):

| Cell | Fact |
|---|---|
| Topology | processors + broker (or mediator); initiating→derived events |
| Partitioning | technical |
| **Quanta** | **1–many** |
| Prose-recovered ratings | perf / scale / FT **4★** (“4 not 5 because of the database”); **evolvability 5★**; simplicity / testability **LO** |

This note does **not** score those stars. It records them.

**Why the range is 1–many** (quantum machinery in the same file, ch7):

- A quantum is the smallest independently runnable part. **The database is inside the quantum.** A single shared DB ⇒ quantum of one, regardless of how many processor *classes* you drew.
- EDA can be **standalone or embedded** (Richards/Ford 2nd ed. opening). An in-process event bus inside a modular monolith is EDA at **quantum = 1**. Independently deployed processors, each with its own store, are **many**.
- Sync communication between quanta **can silently merge them**. style-selection’s decision tree: after you pick async-vs-sync, re-check boundaries. The named antipattern is **Dynamic Quantum Entanglement** (`event-driven-arch-style.md:138`, cited from style-selection): processors that keep needing request/response calls are not independently runnable — they have collapsed.

Trade-off: many quanta buy the 4★ scale/FT story and the 5★ evolvability (add a subscriber, do not touch the publisher). They spend the LO simplicity/testability, and they spend the database caveat (the 4-not-5): if every processor still hits one shared DB, you advertised many quanta and shipped one.

### 3.4 When to use / when not

**Use** (union of style-selection compressed row + Azure 2026 when-to + Fowler 2017 notification/ECST):

- The domain is *react-to-things-that-happened*, not “answer this query” (style-selection; Richards request-vs-event contrast).
- Several subsystems must process the **same** event, and you do not want point-to-point wiring (Azure). New consumers without modifying producers is the 5★ evolvability claim.
- Concurrency is unknown or variable; processors should scale independently (style-selection; Azure “independent scalability and reliability goals”).
- Real-time / near-real-time reaction, including CEP / windowed aggregation and high-velocity ingest (Azure IoT / stream-processing rows — the *need*; the product is A2).
- You can tolerate **eventual consistency** across processors (every sourced when-not is the inverse).

**Do not use** (style-selection `event-driven-arch-style.md:647-688` + Azure when-not + Richards 2015 considerations):

- Processing is **mostly request-based** and sync A1 already meets latency and throughput. Azure: the operational overhead of brokers, async error handling, and eventual consistency is not justified for straightforward interactions.
- Eventual consistency is **unacceptable** — you cannot tolerate a window where parts of the system disagree. Richards 2015: if a single unit of work must be split across processors, this is probably the wrong pattern; plan granularity so events that must be atomic stay in one processor.
- Processors **keep needing sync calls** to each other (style-selection). That is Dynamic Quantum Entanglement, not EDA.
- The team cannot operate distributed async systems. Azure names debugging, monitoring, and error-recovery as a different skill set that hits delivery timelines. Fowler 2017: the flow is not in the program text.
- You chose EDA to get a workflow engine. Buy a mediator / B5; do not pretend choreography will reconstruct the audit trail (this workspace’s [ADR 0003](../../architecture/adrs/application/mobile-test-automation/0003-coordinate-conversion-with-central-orchestration.md) is the same decision: reproducibility beat fan-out).

Pipeline (style-selection): ordered, deterministic, one-way steps stay **pipeline**; back-and-forth or nondeterministic flows are the EDA cue.

### 3.5 Migration in and out

**In (from a request-based monolith or modular monolith).**

1. Keep the request path for queries that are still requests (order history). Do not “event-wash” reads.
2. Introduce a seam that *sees* the write. Fowler’s strangler **Event Interception** is the named seam ([B4](b4-strangler-fig-external-research.md)); Asset Capture is the data-side twin. Do not big-bang the core.
3. Publish from that seam with **B7** (transactional outbox / CDC). Dual-writing the DB and the bus is the failure mode B7 exists to remove. [aws/ch08.md](../../../cases/aws/ch08.md) already separates CDC (replicate state) from event sourcing (intent as source of truth) — do not blur them on the way in.
4. First subscribers should be **side effects that can be late**: email, analytics, search index. That is broker topology on purpose. Azure’s hybrid sentence: EDA combines with microservices, pipes-and-filters, and event sourcing; it is rarely the only style.
5. Split a processor into its own quantum only when it has its own persistence. Shared DB keeps you at quantum 1 (style-selection).

**Hybrid (the common steady state).** [aws/ch08.md](../../../cases/aws/ch08.md) ecommerce: orchestrate payment → inventory → confirm → ship (mediator / B5); emit `OrderShipped` and let notification and analytics choreograph (broker). Azure: same idea — typical combinations include E2, pipes-and-filters, and E12.

**Broker → mediator (or the reverse).** Promote when you can no longer see or restart the flow (Fowler’s notification trap; Azure “no built-in mechanism for restarting”). Demote when the mediator is the change hotspot and the steps have become independently evolvable (Richards 2015: broker is easier to deploy because a processor change does not force a mediator change).

**Out.**

- Sync calls creeping back → collapse those processors into one quantum or replace the hop with A1 inside a larger service. That is leaving EDA for those edges, not “fixing” it with retries (C2).
- Strong consistency required across the whole business transaction → move that slice to a single processor, a mediator + B5, or (if the domain is large and semantically coupled) question E2 granularity (style-selection microservices when-not).
- The event log has become the system of record → you have migrated *into* E12, not “done EDA harder.” Fowler: most processing should still read a working copy, not the log.

Distributed-computing fallacies this style pays for (style-selection ch9 list — name, do not score): **the network is reliable** (A2 redelivery / B7); **latency is zero** (notification + callback = hidden sync); **bandwidth is infinite** (event-carried state transfer / stamp coupling); **versioning is easy** (Azure schema-evolution challenge; A6); **compensating updates always work** (B5); **observability is optional** (Azure: retrofit is substantially harder than designing correlation ids in).

### 3.6 Worked example — insured person relocates

Verified from Richards 2015 (same initiating event in both topologies). Paraphrase only.

**Initiating event:** `RelocationRequested` (customer moved).

**Request-based (not this style).** A UI asks “recalculate this customer’s quote.” That is A1. Do not put it on the bus unless something *happened*.

**Broker topology (choreography).**

1. `CustomerProcessor` receives the initiating event, writes the new address (local TX + **B7** to publish), emits `CustomerAddressChanged`.
2. `QuoteProcessor` and `ClaimsProcessor` both subscribe. Quote recalculates rates and emits `QuoteRecalculated`. Claims updates an open claim and emits `ClaimUpdated`.
3. Further processors may or may not care. An unused `ClaimUpdated` is not a bug — it is the evolvability slot (Richards 2015).
4. **No one** can restart “the relocation.” If claims fails after quote succeeded, the system is inconsistent until a human or a later compensating event (B5 choreography) intervenes. Azure states this directly.

**Mediator topology (orchestration).**

1. Initiating event lands on a queue in front of a `RelocationMediator`.
2. The mediator (not the processors) knows the steps: change address, then in parallel recalc quote and update claims. It emits *processing* events onto dedicated channels and waits.
3. Processors do one task and reply to the mediator. They do not advertise to the rest of the system.
4. Payment-like failure (Richards’ later retail telling, Azure’s restart story): the mediator stops, persists, and resumes at the failed step. That is why you accepted the bottleneck.

**Quantum count on this example.**

- One database shared by customer, quote, and claims → **quantum = 1**, even if three processes listen. style-selection: the DB is part of the quantum.
- Three services, three stores, only async derived events between them → **three quanta**.
- QuoteProcessor HTTP-gets CustomerProcessor on every event → **entangled**; the pair is one quantum pretending to be two.

**What this example does not decide.** Which channel (queue vs topic vs log), DLQ policy, or outbox poller — **A2 / B7**. Whether claims is event-sourced — **E12**. Whether the mediator is a saga orchestrator — **B5**.

### 3.7 Trade-off table

| Decision | Buy | Spend | Source |
|---|---|---|---|
| Adopt EDA at all | Independent consumers; 5★ evolvability; 4★ perf/scale/FT; temporal decoupling | LO simplicity/testability; eventual consistency; flow not in the source; schema governance | style-selection; Azure; Fowler 2017 |
| Broker topology | Dynamic subscribers; no single workflow SPOF; relay-race scale-out | No restart; inconsistency windows; “what happened?” is a correlation exercise | Azure; Richards 2015; Fowler notification trap |
| Mediator topology | Owned state, restart, clearer audit of the *path* | Coupling to the mediator; deploy coupling (2015); bottleneck / reliability concern | Azure; Richards 2015 |
| Event notification (thin) | Small contracts; single system of record | Callback storms; hidden sync; source stays on the read path | Fowler 2017; Azure “keys only” |
| Event-carried state transfer (fat) | Consumers survive source outage; lower source load | Copies; conflicting systems of record after updates; stamp coupling | Fowler 2017; Azure “all attributes” |
| Embed EDA in E2 | Per-service scale + async fabric | Two styles’ failure modes at once; easy to confuse “we have topics” with “we have quanta” | Richards/Ford opening; Azure hybrid |
| Promote a slice to E12 | Replay, audit, temporal query | Working-copy vs log confusion; erasure vs immutability ([event-sourcing-cqrs](../../../cases/data-intensive-design/event-sourcing-cqrs.md)) | Fowler 2005 / 2017; E12 |
| Keep quantum = 1 (in-process bus) | Avoid network fallacies; cheaper ops | Do not claim 4★ FT; the process is the blast radius | style-selection quantum machinery |
| Split quanta without splitting the DB | Diagrams that look distributed | Actual quantum remains one; “4 not 5 because of the database” | style-selection |

---

## 4. Verified editions / dated facts (no library defaults)

Group E has **no** library-defaults section. The dated facts this note relies on:

| Artifact | Date / edition | Fetched |
|---|---|---|
| Hohpe & Woolf, *EIP* | 2003 (book); Message Broker and Event-Driven Consumer pattern pages current | 2026-09-13 |
| Hohpe, *Hub and Spoke* rambling | 2003-11-12 | 2026-09-13 |
| Fowler, Event Sourcing | 2005-12-12 | 2026-09-13 |
| Fowler, Event Collaboration | 2006-06-19 | 2026-09-13 |
| Fowler, CQRS | 2011-07-14 | 2026-09-13 |
| Fowler, “What do you mean by ‘Event-Driven’?” | 2017-02-07 (footnote tweak 2017-02-08) | 2026-09-13 |
| Richards, *Software Architecture Patterns* | first release 2015-02-24; 3rd release 2017-06-22 | 2026-09-13 |
| Richards & Ford, *FSA* 2nd ed. | O’Reilly listing **March 2025**; ch. 15 EDA (1st ed. was ch. 14) | listing 2026-09-13; **chapter body 403** |
| Azure EDA style page | `ms.date` **2026-03-06** (GitHub `architecture-center` source) | 2026-09-13 |
| style-selection.md | workspace distillation of ch7 + ch15 row | read 2026-09-13 |

CloudEvents, AsyncAPI, and vendor SDK retry/DLQ numbers are out of scope (A2 / A6 / C2).

---

## 5. Failure modes and when-not-to-use

**The invisible flow.** Fowler 2017: a logical process that is only the sum of notifications cannot be read from the code. Azure 2026: no shared call context; correlation ids must be designed in. This workspace’s ADR 0003 rejected choreography for exactly this audit gap.

**Passive-aggressive commands.** An event that secretly means “you must do X.” Recipients cannot ignore it, but the schema claims they may. Use a command on a point-to-point channel (mediator / B5 / A2 queue), or accept that unused events are legal (broker).

**Quantum collapse / Dynamic Quantum Entanglement.** Sync hops between processors silently merge quanta (style-selection). Symptom: you still have a broker, but every event handler immediately HTTP-GETs the publisher (thin notification without accepting the source as a runtime dependency).

**Shared-DB “distributed” EDA.** style-selection: 4★ not 5★ *because of the database*. Many processor processes, one schema → one quantum. Failure isolation is fictional.

**Inconsistency without an owner.** Azure broker topology: no restart, no replay of the *business transaction*. Poison-message and DLQ behaviour are A2; *who decides to compensate* is B5. Confusing those two is how an order ships without payment.

**Dual-write on the way in.** Publishing in a second transaction after the DB commit. B7 exists so this note does not invent an outbox.

**Event-sourcing / CQRS conflation.** Fowler 2017 project-manager story: “event sourcing doubled the work because we update two models” — that is CQRS. Adding async on top is a third cost. E12 owns the persistence trade-offs, including erasure vs an immutable log ([event-sourcing-cqrs](../../../cases/data-intensive-design/event-sourcing-cqrs.md)).

**Schema and stamp coupling.** Azure: producers and consumers deploy independently; an unknown field or a new required field breaks the other side. Fat events duplicate systems of record. This is A6 + Fowler ECST; the style failure is “we made evolvability 5★ at the *topology* and 1★ at the *contract*.”

**Over-fine or over-coarse events.** Azure: too many fine events saturate the system and make rollback worse; too-fat events force every consumer to inspect payloads they do not need. Example they give: a compliance component may need only `compliant` / `noncompliant`.

**Mediator as accidental SOA.** A single über-mediator that routes every domain is Hohpe’s unmaintainable broker and style-selection’s Accidental SOA (E6/E9). Federate mediators by domain (Richards 2015 / later tellings).

**Request-reply over the bus as “we are event-driven.”** Azure documents the pattern and immediately says it “effectively turns this pattern into a synchronous process.” Count those edges as A1 when judging the style.

**When-not (restated as failure modes of *choosing* the style).** Mostly-request domains; EC forbidden; processors that cannot stop calling each other; a team that cannot debug async. Richards 2015: splitting an atomic unit of work across processors is a signal to pick a different pattern, not to add more topics.

---

## 6. Cross-links

- **Catalog of record:** [system-design-patterns-catalog.md](system-design-patterns-catalog.md) row E4 (“style-level; mechanisms live in A2/B7”).
- **Style SoT:** [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md) — quantum machinery, ch15 row (1–many, 4★/5★/LO), EDA when-to/when-not, Dynamic Quantum Entanglement.
- **A2** [a2-pubsub-queues-external-research.md](a2-pubsub-queues-external-research.md) — channels, delivery, DLQ, competing consumers. Do not copy.
- **B7** [b7-outbox-cdc-external-research.md](b7-outbox-cdc-external-research.md) — dual-write / outbox / CDC. Also [aws/ch08.md](../../../cases/aws/ch08.md) transactional-outbox paragraph; [replication-logs](../../../cases/data-intensive-design/replication-logs.md).
- **B5** — [aws/ch08.md](../../../cases/aws/ch08.md) choreography/orchestration; [distributed-transactions](../../../cases/data-intensive-design/distributed-transactions.md); [durable-workflows](../../../cases/data-intensive-design/durable-workflows.md).
- **E12** — [event-sourcing-cqrs](../../../cases/data-intensive-design/event-sourcing-cqrs.md); Fowler 2005/2017; [aws/ch08.md](../../../cases/aws/ch08.md) EDA-vs-ES note.
- **E2** — sibling style card (not written here). Azure hybrid; Richards/Ford “embedded in event-driven microservices.”
- **B4** [b4-strangler-fig-external-research.md](b4-strangler-fig-external-research.md) — Event Interception as the migration seam.
- **A1** [a1-request-response-external-research.md](a1-request-response-external-research.md) — the model EDA is defined against.
- **This tree:** [event-driven-dataflow](../../../cases/data-intensive-design/event-driven-dataflow.md); ADR 0003 (orchestration over choreography for an audit-shaped flow).

---

## 7. Sources

**Style / decision (fetched 2026-09-13).**
- https://learn.microsoft.com/azure/architecture/guide/architecture-styles/event-driven (`ms.date` 2026-03-06; GitHub source `MicrosoftDocs/architecture-center` `docs/guide/architecture-styles/event-driven.md`)
- https://www.martinfowler.com/articles/201701-event-driven.html (2017-02-07)
- https://martinfowler.com/eaaDev/EventCollaboration.html (2006-06-19)
- https://martinfowler.com/eaaDev/EventSourcing.html (2005-12-12)
- https://martinfowler.com/bliki/CQRS.html (2011-07-14)
- https://martinfowler.com/eaaDev/EventNarrative.html (*Focusing on Events*)
- https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageBroker.html
- https://www.enterpriseintegrationpatterns.com/patterns/messaging/EventDrivenConsumer.html
- https://www.enterpriseintegrationpatterns.com/docs/EnterpriseIntegrationPatterns_HohpeWoolf_ch03.pdf
- https://www.enterpriseintegrationpatterns.com/ramblings/03_hubandspoke.html (2003-11-12)
- https://www.enterpriseintegrationpatterns.com/patterns/messaging/RequestReply.html (named by Azure; not re-derived)
- https://aws.amazon.com/event-driven-architecture/
- https://www.oreilly.com/library/view/fundamentals-of-software/9781098175504/ (2nd ed. listing, March 2025; ch. 15 title)
- Richards, *Software Architecture Patterns*, O’Reilly, Feb 2015 (ISBN 978-1-491-92424-2) — public report; broker/mediator + relocation example. **Do not copy body into the Concept.**

**Workspace (do not rewrite).**
- `.cursor/skills/arch-style/references/style-selection.md`
- `cases/data-intensive-design/event-driven-dataflow.md`
- `cases/data-intensive-design/event-sourcing-cqrs.md`
- `cases/aws/ch08.md`
- `docs/research/sysdesign/a2-pubsub-queues-external-research.md`
- `docs/research/sysdesign/b4-strangler-fig-external-research.md`
- `docs/architecture/adrs/application/mobile-test-automation/0003-coordinate-conversion-with-central-orchestration.md`

---

## 8. Uncertain / left out

- **FSA 2nd ed. ch. 15 body** — O’Reilly HTML returned **403** this fetch. Opening sentence and “standalone or embedded” recovered from the chapter listing / search snippet only. Star ratings and the 1–many quantum cell are taken from style-selection.md (itself distilled from `event-driven-arch-style.md`, **which is not present in this worktree**). The book’s scorecard *figures* did not survive into those notes — style-selection already marks other styles’ `—` cells; the EDA prose ratings above are the ones it recovered. Do not invent additional stars.
- **Publication day** of the 2nd edition: O’Reilly listing “March 2025”; some retailers print 2025-04-22. Month is enough; day is unverified.
- **Richards 2015 High/Low** ratings (agility/deploy high, test/dev low, perf/scale high) are a *different card* from the 2nd-edition stars. Not used as 2026 facts.
- **“Dozen to several hundred event queues”** (Richards 2015 mediator) — 2015-era order of magnitude, not a 2026 default.
- **PlaceOrder retail example** appears in later secondary tellings of Richards/Ford; the 2015 public report’s worked example is insurance **relocation**. This note uses relocation. Do not cite PlaceOrder as fetched from the 2nd-ed chapter.
- **Dynamic Quantum Entanglement** — cited via style-selection to `event-driven-arch-style.md:138` and `ArchCharScope.md:72-74`. Those files were not re-read in this worktree; the definition used here is the style-selection prose (sync calls merge quanta).
- AWS EventBridge vs SNS “two types of routers,” cost-because-push, and durability/ordering advice on the marketing page — product guidance, not style defaults.
- CloudEvents / AsyncAPI / specific broker versions — not fetched; A2/A6 own them.
- Azure “client acknowledge mode” and “last participant support” — named on the EDA page; semantics not re-verified against a protocol spec (A2).
- NServiceBus / MassTransit as Azure’s “basic event correlation” examples — named, not reviewed.
- No controlled study comparing broker vs mediator operability was found; the trade-off table is sourced qualitative consensus, not a measurement.

---
