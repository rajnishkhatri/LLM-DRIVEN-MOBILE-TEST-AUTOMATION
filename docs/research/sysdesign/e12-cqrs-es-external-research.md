---
type: research
title: 'CQRS and event sourcing — external research (2026-09-13)'
description: >-
  Group E decision-depth note for catalog E12: CQRS ≠ event sourcing,
  write vs read models, event store as SoR vs projections, when-to /
  when-not, migration (ES inside E10, or pair with E4), worked
  conference-booking example, and trade-offs. Mechanisms stay in A2/B7/B5.
tags: [research, system-design-patterns, E12, cqrs, event-sourcing]
---

# CQRS and event sourcing — external research (2026-09-13)

> **What this is.** Evidence pass for catalog id **⊕E12** (Group E — Architectural styles). Decision depth only: what CQRS and event sourcing *are and are not*, that they can be adopted separately, write model vs read model, event store as source of truth vs projections, quantum implications of sharing or splitting stores, when-to / when-not, migration in or out (add ES *inside* **E10**, or pair with **E4**), a worked example, and a trade-off table. How an event travels on a channel lives in **[A2](a2-pubsub-queues-external-research.md)**. How a current-state write becomes a published event without a dual-write lives in **[B7](b7-outbox-cdc-external-research.md)**. Multi-step compensation lives in **[B5](b5-saga-external-research.md)**. The Concept (when written) should stay readable; this note keeps fetched facts, dates, and URLs.
>
> **Method.** Primary pages fetched 2026-09-13. Paraphrase; identifiers and dates reproduced exactly. Quantum count is recorded as a **FACT** only where sourced (style-selection ch7 machinery + Fowler/Azure share-vs-split). This note does **not** re-run arch-style’s four determinations or scoring loop. Items that could not be verified are in §8 and are **not** to be implied as fact.
>
> **Existing notes** (cite; do **not** rewrite): [event-sourcing-cqrs](../../../cases/data-intensive-design/event-sourcing-cqrs.md) (DDD-community terms, conference-booking projections, erasure vs immutability), [aws/ch08.md](../../../cases/aws/ch08.md) (CQRS one-paragraph; EDA vs event sourcing vs CDC; saga as the sibling transaction pattern). **E4** already owns broker vs mediator and flags Fowler 2017 “CQRS isn’t about events.”

---

## 1. Scope and non-goals

**Owns.** CQRS and event sourcing as *style-level* cards: a write-shaped model vs a read-shaped model (CQRS); an append-only event log as the system of record, with projections as derived views (event sourcing); the fact that the two patterns are independent and often paired; whether the read and write models share a quantum or split; when either is the right (or wrong) pick; how to migrate in or out; a worked example; a trade-off table.

**Does not own.**

| Sibling | Why it stays there |
|---|---|
| **E4** event-driven architecture | Style of *collaboration* (broker vs mediator; initiating → derived events). Fowler (2017-02-07): CQRS “isn’t really about events”; event sourcing “need not be asynchronous.” Using topics does not make you E12; keeping an event log as SoR does not make you E4. |
| **E10** modular monolith | The one-quantum structured host. E12 is an overlay *inside* a module / bounded context. Migration in is “add ES (or CQRS) inside E10,” not “leave E10.” |
| **A2** pub/sub, queues, streams | Wire semantics once an event is *on* a channel: competing consumers, fan-out, ordering, DLQ, reconnect. E12 names “events as integration” and points here. |
| **B7** transactional outbox & CDC | How a *current-state* write becomes a published event atomically. Event sourcing is B7’s *sibling* dual-write fix (the log *is* the write). CDC is not event sourcing — already contrasted in [aws/ch08.md](../../../cases/aws/ch08.md). Do not re-derive inbox/outbox. |
| **B5** saga | Multi-step compensation across services. CQRS/ES can emit the events a saga consumes; they do not replace compensation. Do not re-derive saga. |
| **E2** microservice architecture | Independently deployed, DB-per-service. Richardson-style “CQRS as a query complement to DB-per-service” is an overlay *inside* an E2 service, not E2 itself. |
| **C9** idempotency | Consumers of at-least-once projection events. Azure ES (2026) requires it; C9 owns the card. |

**Non-goals.** Library or event-store product defaults (Group E has none). Scoring monolith-vs-distributed. Re-deriving DLQ, outbox, CDC, or Kafka knobs. Writing a Concept. Rewriting the two linked `cases/` notes.

---

## 2. Lineage / vocabulary

**Meyer, Command–Query Separation (CQS).** *Object-Oriented Software Construction*; Fowler’s bliki restatement (2005-12-05) at https://martinfowler.com/bliki/CommandQuerySeparation.html — fetched 2026-09-13. Methods split into **queries** (return a result, no observable state change) and **commands** (change state, no return). Fowler accepts Meyer’s exceptions (stack `pop`). This is a *method* rule, not CQRS.

**Young, “CQRS, Task Based UIs, Event Sourcing agh!” (2010-02-16).** Original: http://codebetter.com/gregyoung/2010/02/16/cqrs-task-based-uis-event-sourcing-agh/ (live origin **502** this fetch; text verified from the attributed gist reprint https://gist.github.com/simonschoof/74e155447fbc2ac47b0f7c0bb5a5f778). **CQRS is the creation of two objects where there was previously one**, split on Meyer’s command/query definition, typically at the service boundary (`CustomerWriteService` / `CustomerReadService`). That is the *entirety* of the pattern. Explicitly **not**: eventual consistency, eventing, messaging, “having separated models for reading and writing” as a *required* extra, or event sourcing. Task-based UI is **not** required for CQRS (it *is* required for DDD’s application service layer, so the ubiquitous language has verbs other than Create/Update/Delete). Eventual consistency and messaging appear only *if* you later separate the data models. Hosting the read service on 25 servers and the write service on two is an *enabled* architecture, not CQRS itself.

**Young, *CQRS Documents* (November 2010).** https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf and https://cqrs.wordpress.com/documents/cqrs-introduction/ — both fetched 2026-09-13. After confusion with CQS, the name CQRS was chosen. Same Meyer definitions, but **objects are split** — one holds commands, one holds queries. The split is cheap: a thin read layer projects DTOs off the store and bypasses the domain; the command side keeps a behavioral contract and `GetById`. Consistency / storage / scale are *asymmetrical*: command wants transactional, near-3NF data; query can be eventually consistent and denormalized (1NF). “It is not possible to create an optimal solution for searching, reporting, and processing transactions utilizing a single model.” Events are named as the *best-known* integration between two stores, not as CQRS itself.

**Young, *CQRS Documents* § “CQRS and Event Sourcing.”** The pair is **symbiotic, not identical**. Event sourcing cannot answer “give me all users whose first name is Greg” — the domain’s only query is `GetById`. CQRS supplies the query side. Conversely, integrating two *relational* models plus a third event model is expensive; if the write-side persistence *is* the event model, that conversion cost disappears. Young’s cost claim that the combined shape is “less expensive in most cases” is **his 2010 analysis**, not a 2026 measurement (§8).

**Young, “CQRS is not an Architecture” (2012-09-09).** https://gregfyoung.wordpress.com/2012/09/09/cqrs-is-not-an-architecture/ — fetched 2026-09-13. CQRS and event sourcing are **architectural patterns inside a single system or component**. They are **not** architectural *styles*. SOA and EDA *are* styles (a system of systems). “The largest failure I see from people using event sourcing is that they try to use it everywhere.”

**Dahan, “Clarified CQRS” (2009-12-09).** https://udidahan.com/2009/12/09/clarified-cqrs/ — fetched 2026-09-13. Opening: people have been tying CQRS to event sourcing and overlaying layered-architecture assumptions. Drivers are **collaboration** (many actors on the same data) and **staleness** (shown data is already stale). Queries go to a store shaped like the view model (even `SELECT * FROM MyViewTable`); commands capture intent at the right grain (“make preferred” ≠ “edit the whole customer DTO”). Commands are **sent**, not published; events are published. Event sourcing is “another possible implementation” of the command side, next to transaction script / table module / domain model.

**Vernon, “Really Simple CQRS” (Kalele).** https://kalele.io/really-simple-cqrs/ — fetched 2026-09-13. Same Meyer → two-interface split (`ThingCommands` / `ThingQueries`). **CQRS is not a top-level architectural style** (contrast Layers, Ports and Adapters, which shape the whole application); it is an architecture *pattern* that influences the interior. Typical next step: two *state* models (command and query), at least logically segregated. The query model is built by **projecting** command-model changes — via Domain Events *or* by projecting the mutated aggregate’s full state (events are not required). “I don’t think that it is oversimplifying things to say that CQRS is just that simple.”

**Vernon, “And Then This Happened” (Kalele).** https://kalele.io/and-then-this-happened/ — fetched 2026-09-13. Two projection paths: emit `ThisHappended` and project the event, or project the Warble’s full state plus an `operation` / `reasonForChange`. `WarbleUpdated` “has actually said nothing.” Event *count* for a compound command (`doThisThat`) is a **business** question (shortcut of two facts vs one atomic fact), not a framework default. Do **not** adopt Domain Events just to reach “everybody knows Event Sourced models are the single source of truth.”

**Vernon, *Implementing Domain-Driven Design* (Addison-Wesley, 2013, ISBN 9780321834577).** Book body not re-fetched (§8). Public sample TOC (Pearson, fetched 2026-09-13): CQRS at p. 138 (including “Dealing with an Eventually Consistent Query Model”); Event Sourcing at p. 160, under Event-Driven Architecture, next to Pipes and Filters and Long-Running Processes / Sagas (those last two stay **E4 / B5**). Companion [IDDD_Samples](https://github.com/VaughnVernon/IDDD_Samples) README (fetched 2026-09-13): `iddd_collaboration` uses ES + CQRS; LevelDB event journal + MySQL read model; **one thread** persists both to keep them close without sharing a store or a transaction — two stores on purpose. `iddd_identityaccess` is ORM + REST, not ES: Vernon’s own samples do **not** event-source every bounded context.

**Vernon, *Effective Aggregate Design* Part II (2011).** https://www.dddcommunity.org/wp-content/uploads/files/pdf_articles/Vernon_2011_2.pdf — fetched 2026-09-13. Aggregates that reference only by identity make UI assembly expensive; **CQRS is the named escape** (cites Dahan, Fowler, Young). Transactional vs eventual consistency is **not** “classic DDD vs CQRS” — Evans’ test: if it is *this user’s* job to make the data consistent, try to keep it in one transaction (still obeying aggregate rules); if it is another user’s or the system’s job, allow eventual consistency.

**Fowler, “Event Sourcing” (2005-12-12).** https://martinfowler.com/eaaDev/EventSourcing.html — draft P of EAA material, not later corrected; fetched 2026-09-13. Every change is an event object stored in the sequence it was applied, for the same lifetime as the application state. Facilities: **complete rebuild**, **temporal query**, **event replay** (including late/out-of-order arrivals). Git/Subversion is the running example. Official SoR can be *either* the log *or* the current application state (the log then is audit/special processing). Snapshots are an optimization, not a second SoR. Hard parts in the same article: external updates (disable gateways on replay), external queries (pin the December-5 rate, do not re-fetch on December-20 replay), code/schema change. Parallel Models / Retroactive Events are **hard to retrofit** — if you reasonably expect them, decide now.

**Fowler, “CQRS” bliki (2011-07-14).** https://martinfowler.com/bliki/CQRS.html — fetched 2026-09-13. “A pattern that I first heard described by Greg Young.” Split the *conceptual model* into command and query models. Models “most commonly” run in different logical processes, perhaps on separate hardware; they **may share the same database** (the DB is the communication) or use **separate databases** (query side becomes a real-time ReportingDatabase, and you need a communication mechanism). Usually they are clearly separate models, not just two interfaces on one object. **When:** only on specific portions (a DDD Bounded Context), not the whole system. Benefits in two directions — a *minority* of complex domains, and high-performance read/write disparity. Otherwise use a ReportingDatabase for the hard queries and keep a shared model. **Majority of cases he had seen were harmful.**

**Fowler, “What do you mean by ‘Event-Driven’?” (2017-02-07; footnote 2017-02-08).** https://www.martinfowler.com/articles/201701-event-driven.html — fetched 2026-09-13. Four un-collapsed patterns (E4 already owns notification / ECST):

| Pattern | What it is | Style-level cost |
|---|---|---|
| **Event Sourcing** | Log is the principal source of truth; state is derived. Git. **Need not be async** (local `git commit` is synchronous). | Replay, audit, alternative histories, Memory Image; schema evolution and external-system replay are the hard parts. Most processing should read a *working copy*, not the log. |
| **CQRS** | Separate data structures for read and write. **Need not use events.** | Fowler’s colleagues are “deeply wary”; often misused. |

The project-manager story: “event sourcing doubled the work because we update two models” — that is **CQRS**, not event sourcing. The tech lead who blamed “lots of async” was paying a cost **neither** pattern requires.

**Microsoft Azure Architecture Center, CQRS pattern** (`ms.date` **2025-02-20**, GitHub `MicrosoftDocs/architecture-center` `docs/patterns/cqrs.md`; fetched 2026-09-13). https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs. Two implementation levels: **separate models in a single data store**, then **separate models in different data stores**. Messaging is **not** a requirement. When stores split, the write model publishes events; dual-write is the failure mode — use the Transactional Outbox (**B7**) and make the read-model consumer idempotent (**C9**). Combined-with-ES section: the event store *is* the write model and SoR; the read model is denormalized materialized views; snapshots exist because full replay of long histories is expensive.

**Microsoft Azure Architecture Center, Event Sourcing pattern** (`ms.date` **2026-03-27**, same repo `docs/patterns/event-sourcing.md`; fetched 2026-09-13). https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing. Lead warning: complex; costly to migrate *to or from*; constrains later decisions; “for most systems and most parts of a system, traditional data management is sufficient.” **Do not confuse an event store with an event-stream message broker** — Kafka-class brokers typically lack per-entity stream queries and optimistic concurrency; they fan out (A2), they are not a substitute SoR. Intent-focused events (`SeatsReserved`) beat state-delta events (`remaining seats = 42`). Crypto-shredding / externalize PII for erasure. Apply selectively (payment ledger, order pipeline); keep CRUD for profiles and config.

**Microsoft Patterns & Practices, *Exploring CQRS and Event Sourcing* (2012)** — workspace [data-models-references.md](../../../cases/data-intensive-design/data-models-references.md) [65]; conference-management sample. Azure’s 2026 ES page still uses that conference seat-reservation example. Journey GitHub `MicrosoftArchive/cqrs-journey` Reference 2 (fetched 2026-09-13): “not a top-level architectural approach”; Young/Dahan conversation: apply inside a Bounded Context; top-level looks like SOA or EDA.

**This workspace.** [event-sourcing-cqrs](../../../cases/data-intensive-design/event-sourcing-cqrs.md): command → validated **fact** → past-tense event; views must be **reproducible**; order matters (unlike a star-schema fact table); deletion event, not in-place delete; GDPR vs immutability / crypto-shredding [68]; side-effects must not re-fire on rebuild. [aws/ch08.md](../../../cases/aws/ch08.md): CQRS = separate command/query *interfaces*; ES = immutable events as SoR (complete rebuild, temporal query, replay); CDC captures *state* change without storing intent; saga is the sibling event-based *transaction* pattern.

---

## 3. Mechanics (Group E decision depth bar)

### 3.1 What the style is — and is not

**CQRS is.** Two models (typically two objects / two service surfaces) for the same information: a **command / write model** that accepts intent and mutates, a **query / read model** that returns data and does not. Young 2010: that split *is* the pattern. Fowler 2011: the conceptual integration point is no longer a single model. Vernon: two interfaces, then typically two state models; the query side is a projection.

**Event sourcing is.** The event log is the system of record; current state is a function of the ordered events. Fowler 2005/2017; Azure 2026; [event-sourcing-cqrs](../../../cases/data-intensive-design/event-sourcing-cqrs.md). Name events in the **past tense** because they are facts. Projections / materialized views are **derived** and must be rebuildable from the same log in the same order.

**CQRS ≠ event sourcing — they can be used separately.**

| Combination | What you have | Typical SoR | Async required? |
|---|---|---|---|
| **Neither** | CRUD / one model | Current-state rows | No |
| **CQRS only** | Two models; write side still stores current state | Write-side tables (or documents) | No. Young / Fowler / Azure / Vernon: messaging and Domain Events are optional. Same DB is the common first step. |
| **ES only** | Log is SoR; you still query by replaying or by a working copy that is *not* a separate query *model* | Event log | No. Fowler 2017: `git commit` is sync. |
| **CQRS + ES** | Log is the write model; projections are the query model | Event log | Often yes *between* store and projections, not as a definition. |

The arrow is one-way in practice: **event sourcing pulls you toward CQRS** (you cannot query “all Gregs” from a per-entity stream — Young 2010 documents; Azure “Event querying”). **CQRS needs nothing from event sourcing** (Fowler 2017; Young 2010; Dahan 2009; Vernon Kalele; Azure CQRS “messaging isn’t a requirement”).

**Is not.**

- **Not a Richards/Ford first-class style.** [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md) comparison matrix has Layered, Modular monolith, Pipeline, Microkernel, Service-based, Event-driven, Space-based, SOA, Microservices. **There is no CQRS/ES row, no star card, no quantum cell.** Young 2012 and Vernon Kalele: these are patterns *inside* a component; EDA and SOA (and Ports and Adapters) are the styles. This catalog still files E12 under Group E because the *decision* (when to overlay, when it splits a quantum) is style-level — do not invent stars.
- **Not E4.** Event notification / ECST / a broker topology can exist with a current-state SoR. Event sourcing can be in-process and synchronous.
- **Not CDC.** [aws/ch08.md](../../../cases/aws/ch08.md): CDC replicates state from a database log; event sourcing stores *intent* as SoR. B7’s outbox publishes a fact *about* a row that remains SoR.
- **Not “we added MediatR / two handler interfaces.”** Young’s split is about *responsibility and (optionally) models*, not a library. No library-defaults section on this card.
- **Not a top-level architecture for the whole system.** Fowler 2011 Bounded Context; Azure ES 2026 “not all-or-nothing”; Young 2012 “not everywhere”; Journey 2012; Vernon samples mix ES and ORM contexts.
- **Not a message broker as the event store.** Azure ES 2026, explicit.

### 3.2 Quantum implications — FACT only where sourced

[style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md) has **no E12 matrix row**. Do not invent a star rating or a canonical integer. What *is* sourced is ch7 quantum machinery (not a scoring pass):

- A quantum is the smallest independently runnable part. **The database is inside the quantum.** Single shared DB ⇒ quantum of one.
- Sync communication between quanta can silently merge them (re-check after choosing sync).

Mapped onto Fowler 2011 / Azure 2025 two levels, Young’s “25 + 2 servers,” and Vernon’s LevelDB journal + MySQL read model:

| Shape | Quanta (from ch7 + share/split) | What you bought | What you spent |
|---|---|---|---|
| CQRS **same store**, same deployable (Azure “foundational”; Fowler “DB as communication”) | **1** | Separate models / teams / query shapes; no dual-write | No independent scale of stores; lock contention can remain |
| CQRS **same store**, read replicas of the write DB | still **1** (replicas are not a second SoR; they share the schema lineage) | Read scale | Replica lag is *not* a second model; it is replication (B2) |
| CQRS **separate stores**, independently deployed, only async events between them | **2+** (write quantum + each independently persistable read model) | Independent scale, different storage tech, PE:05/PE:08 (Azure WAF table) | Eventual consistency; B7 dual-write; C9; schema on two sides |
| ES **in-process** working copy + log in one DB (including ES *inside* an E10 module) | **1** | Replay / audit without a network | Rebuild cost; erasure; no independent read scale |
| ES + **remote** projections with their own stores | **1 write + N read quanta** | Azure’s “independently scale reads and writes” | Projection lag; “what is current?”; replay vs live consumers |
| Thin HTTP from the query side back to the command side on every read | **entangled → 1** | Diagrams that look split | style-selection sync-merge; Fowler 2017 notification+callback |

Typical field shape (Young / Journey / Azure / Vernon samples): apply inside **one bounded context**; start at quantum 1; split stores only when read/write load or schema really diverge. Vernon’s `iddd_collaboration` already uses two stores in one thread — two *schemas*, still one process / one quantum until the projector can die without taking the writer.

Trade-off: splitting stores to claim “independent scale” while leaving both on one shared cluster and one release train advertises many quanta and ships one — the same “4 not 5 because of the database” caveat style-selection records for EDA.

### 3.3 When to use / when not

**Use CQRS** (union of Fowler 2011, Young 2010, Dahan 2009, Vernon 2011/Kalele, Azure 2025):

- The command model and the query model *interfere* — repositories grow paging/sorting getters, aggregates blur to feed DTOs, one model does neither job well (Young smells; Fowler “same conceptual model… does neither well”; Vernon: users view data in different quantities/shapes than they mutate).
- Collaborative, high-contention writes where a coarse “Save this DTO” causes merge conflicts; commands at task grain reduce the collision window (Dahan; Azure “collaborative environments”).
- Large **read/write disparity** so you want to scale or optimize the sides independently (Fowler; Young “two or more orders of magnitude”; Azure PE pillar).
- Task-based UI / complex DDD bounded context (Fowler; Young: DDD needs verbs). Azure: write model is a full command stack with aggregates; read model is DTOs, no domain logic.
- Aggregates that reference only by identity make UI assembly a multi-repository tax — Vernon 2011 names CQRS as the escape.
- Separate teams on write logic vs UI/query (Azure “separation of development concerns”) — buy only if the org actually splits that way.

**Do not use CQRS** when the domain is simple CRUD (Fowler: majority case; Azure “simple CRUD-style UI and data access are sufficient”). Prefer a **ReportingDatabase** for a few heavy queries (Fowler 2011) over splitting *all* queries. Do not apply to the whole system.

**Use event sourcing** (Fowler 2005 when-to; Azure 2026 when-to; [event-sourcing-cqrs](../../../cases/data-intensive-design/event-sourcing-cqrs.md)):

- You need **intent** in the data (`MovedHome`, `SeatsReserved`), not only the latest row.
- Audit, temporal query, rebuild, or parallel/retroactive models — Fowler: these are **hard to retrofit**; if you reasonably expect them, decide now.
- Write contention on a hot current-state row (Azure conference last-day bookings; append + optimistic concurrency on the stream).
- Multiple rebuildable views from one log (workspace note; Azure “change the format of materialized models”).
- The domain already speaks events, so the extra cost is small (Azure). Vernon: only after concrete scenarios prove Domain Events *strengthen the model*.

**Do not use event sourcing** when you only need current-state CRUD (Azure); for MVPs / short-lived systems (Azure: upfront event design + schema strategy + projections rarely pay back); when projections must be real-time consistent (eventual consistency is inherent); for mostly-static reference data; when the team has no event-driven operating skill (Azure: antipatterns are costly to reverse). Fowler: the event *interface* is awkward; pick it for a return, not as default.

**Do not combine them by default.** Azure CQRS: complexity “specifically when combined with Event Sourcing.” Fowler 2017: three separable costs (two models, a log, async). Pay only the ones the bounded context needs.

### 3.4 Migration in and out

**In — add ES (or CQRS) inside E10.** Young’s documents are an *incremental* path, not a big-bang style swap. The host stays the modular monolith (quantum **1**); the overlay is one module / bounded context:

1. **Keep CRUD** where the ubiquitous language *is* Create/Update/Delete (Young 2010; Azure ES selective-apply tip; Vernon’s `iddd_identityaccess` stays ORM).
2. **Task-based commands** on the write API (“Book seats”, not “Set ReservationStatus”) — Young / Azure CQRS. This is still one model, still E10.
3. **CQRS, same store** — split the service surface; thin read layer; domain loses query methods except `GetById` (Young). Quantum remains **1**. Fowler: this is already a mental leap; stop here if the pain was model complexity, not scale.
4. **Optional: separate read store still in-process** (Vernon’s LevelDB + MySQL in one thread). Two schemas, one deployable, still E10 / quantum 1.
5. **Optional: publish across the process boundary.** **B7** (outbox / CDC) so the row and the event commit together. **A2** for the channel. **C9** on the projector. Do **not** dual-write. [aws/ch08.md](../../../cases/aws/ch08.md) already owns the CDC taxonomy; do not treat CDC as “we are now event-sourced.”
6. **Optional: event-source the write model** in *that* bounded context. Azure: costly to migrate *to*; Fowler: Parallel Models / Retroactive Events are hard to retrofit, so this step is the one you do not casually reverse. Snapshots from day one if streams will be long (Azure; Fowler).
7. **Privacy before the first personal field hits an immutable log** — [event-sourcing-cqrs](../../../cases/data-intensive-design/event-sourcing-cqrs.md) (externalize or crypto-shred); Azure ES 2026 repeats both tactics.

Strangler (B4) is the cutover *mechanism* for a legacy module; Event Interception is the seam E4 already names. E12 is what you *install behind* that seam, not the strangler itself.

**In — pair with E4.** When the *collaboration* between contexts is already (or should be) reaction-to-facts, E4 owns broker vs mediator. E12 then supplies persistence *inside* a processor: the processor’s write model may be event-sourced; its projections may be the local read model; derived events still travel on A2. Fowler 2017 and E4 already warn: do not count “we have topics” as “we have a log as SoR.” Pairing is common (Azure ES “commonly combined with CQRS”; Azure EDA hybrid sentence names event sourcing); it stacks three costs (E4 async + CQRS two models + ES log). Pay only the ones that bounded context needs. [aws/ch08.md](../../../cases/aws/ch08.md) hybrid ecommerce (orchestrate the order core, choreograph notifications) still applies — E12 does not replace that E4/B5 choice.

**Hybrid (the common steady state).** Journey / Azure / Young 2012 / Vernon samples: CQRS+ES in the booking / ledger / collaboration context; CRUD for profile and config; E4 broker or B5 mediator for the *cross*-context flow.

**Out.**

- **From split-store CQRS, keep the write model:** stop projectors; serve queries from the write store or a replica; delete the second schema. You give back independent scale. The E10 host, if you never left it, is unchanged.
- **From ES:** Azure’s own warning — costly. Practical exit (not a vendor runbook): build a current-state store by replay, switch the SoR, keep the log as an *audit* (Fowler already allows “SoR = application state, log = audit”). You lose cheap rebuild of *new* views.
- **From “CQRS everywhere”:** Fowler 2011 / Young 2012 / Vernon samples — shrink back to the bounded contexts that earned it.

Distributed-computing fallacies this overlay pays for when stores or projections leave process (style-selection ch9 list — name, do not score): **the network is reliable** (A2 / B7); **latency is zero** (read-your-writes after a command); **versioning is easy** (Azure event versioning / upcasters / in-place migration as last resort); **compensating updates always work** (deletion events, B5); **observability is optional** (projection lag is a user-visible correctness bug).

### 3.5 Worked example — conference seat reservation

Verified from Azure ES 2026 (same conference domain as Microsoft Journey 2012 and the workspace [event-sourcing-cqrs](../../../cases/data-intensive-design/event-sourcing-cqrs.md) booking narrative). Paraphrase only; do not rewrite those notes.

**Domain fact.** A conference has a finite seat pool. Attendees book and cancel. Last-day load contends on “how many seats remain.” The workspace note adds bulk company orders, speaker holds, room-capacity changes — same shape: *availability is a query that fights the write model*.

**CRUD (not this card).** A `bookings` row plus a `seats_remaining` counter, updated in place. Azure: simple, and a bottleneck when many attendees book in a short window (row lock on the counter). Inside E10 this is just another module’s tables.

**CQRS only (same store, still E10).** Commands: `ReserveSeats`, `CancelReservation` (intent). Queries: `FindAvailability`, organizer dashboard DTOs, badge-print file — thin read layer, possibly SQL views in the *same* database. Quantum **= 1**. You have already split models; you have **not** made the log the SoR.

**CQRS, split stores.** Write model commits the reservation. An event `SeatsReserved(conferenceId, seats=2)` is appended via **B7** and carried on **A2** if it leaves process (Vernon’s one-thread two-store sample skips the broker). A projector updates a denormalized `availability` document / table. Read-your-writes is *not* guaranteed; the UI must treat staleness as Dahan’s designed-in property (or read a write-side confirmation DTO for that one command). Two persistable models → **two quanta** only if the projector’s store and deployable can die without taking the writer with it.

**Event sourced write + CQRS reads (Azure workflow).**

1. UI issues `ReserveSeats(2)`.
2. Command handler **rehydrates** `SeatAvailability` by reading that conference’s event stream (snapshot + tail).
3. Domain logic accepts or rejects (not enough seats). On accept it raises `SeatsReserved`.
4. Append to the event store with **optimistic concurrency** on the stream. Two handlers who both saw five seats: one append wins, the other reloads and retries (Azure). That is *not* a saga (B5) and not a broker topology (E4).
5. Handlers (A2 consumers, if remote) (a) persist the event if the queue was the ingest path Azure draws, (b) update the read-only availability view, (c) integrate (email, badge). Rebuild of (b) must **not** resend (c) — workspace note; Fowler gateway-on-replay.

**Cancellation** is a new `ReservationCanceled` event, not an update of `SeatsReserved`. The original fact remains (workspace: past tense; Azure compensating event).

**What this example does not decide.** Queue vs log vs bus (**A2**). Outbox vs “listen to the event store” (**B7**). Whether payment is a choreographed saga (**B5**). Whether the conference service is one of many E2 services, or a module inside E10. Whether *other* conference contexts (identity, billing) are event-sourced — Journey / Vernon samples say no.

### 3.6 Trade-off table

| Decision | Buy | Spend | Source |
|---|---|---|---|
| Adopt CQRS at all | Models that can each be good at one job; optional independent scale | Two conceptual models; Fowler’s “majority harmful” risk; productivity drag | Fowler 2011; Young 2010 |
| CQRS, **same** store | Split without dual-write or eventual consistency | No store-level scale-out; still one quantum | Fowler 2011; Azure 2025; style-selection DB-in-quantum |
| CQRS, **split** stores | Scale/tech per side; denormalized reads; security surface split | Lag; B7; C9; two schemas to evolve | Azure 2025; Young integration chapter; Vernon IDDD_Samples |
| ReportingDatabase instead of full CQRS | Offload *hard* queries; keep one model for the rest | Not a general query path | Fowler 2011 |
| Adopt ES | Rebuild, temporal query, audit, intent, append-only writes | Awkward interface; schema/upcast; external replay; erasure; costly exit | Fowler 2005; Azure 2026; workspace note |
| ES **without** CQRS | Sync working copy (git-shaped) | Cannot query across streams cheaply | Young 2010 docs; Azure “Event querying” |
| CQRS **+** ES | Write model *is* the integration model; cheap new views | Three costs stacked (models + log + usually async) | Young 2010 § intersection; Fowler 2017; Azure combine section |
| Add ES **inside E10** | Replay/audit without leaving the one-quantum host | Module complexity; erasure; still no 4★ FT | style-selection ch7; Azure selective-apply; Vernon samples |
| Pair with **E4** | Processors react; one processor may keep a log as SoR | Three costs; easy to confuse topics with a store | Fowler 2017; E4; Azure hybrid |
| Broker (Kafka, etc.) as the event *store* | Familiar A2 ops | No per-entity OCC / stream query — Azure says this is the wrong tool | Azure ES 2026 |
| ES everywhere | Cookie-cutter guideline | Young’s named largest failure | Young 2012; Vernon samples mix ES and ORM |
| Split quanta but share the DB | Diagrams | Actual quantum remains one | style-selection ch7 |

---

## 4. Verified editions / dated facts (no library defaults)

Group E has **no** library-defaults section. Dated facts this note relies on:

| Artifact | Date / edition | Fetched |
|---|---|---|
| Fowler, CommandQuerySeparation | 2005-12-05 | 2026-09-13 |
| Fowler, Event Sourcing | 2005-12-12 (draft; no later corrections) | 2026-09-13 |
| Dahan, Clarified CQRS | 2009-12-09 | 2026-09-13 |
| Young, “CQRS, Task Based UIs…” | 2010-02-16 | gist reprint 2026-09-13; live origin **502** |
| Young, *CQRS Documents* PDF + HTML intro | November 2010 | 2026-09-13 |
| Fowler, CQRS bliki | 2011-07-14 | 2026-09-13 |
| Vernon, *Effective Aggregate Design* Part II | 2011 | PDF 2026-09-13 |
| Microsoft *Exploring CQRS and Event Sourcing* | 2012 (ISBN 9781621140164) | Journey GitHub Reference 2 fetched; book body not re-fetched |
| Young, “CQRS is not an Architecture” | 2012-09-09 | 2026-09-13 (live HTML) |
| Vernon, *IDDD* | 2013, ISBN 9780321834577 | TOC via Pearson sample; book body not re-fetched |
| IDDD_Samples README | current `master` | 2026-09-13 |
| Fowler, “What do you mean by ‘Event-Driven’?” | 2017-02-07 / 2017-02-08 | 2026-09-13 |
| Vernon, Really Simple CQRS / And Then This Happened | Kalele (undated posts) | 2026-09-13 |
| Azure CQRS pattern | `ms.date` **2025-02-20** | 2026-09-13 |
| Azure Event Sourcing pattern | `ms.date` **2026-03-27** | 2026-09-13 |
| style-selection.md | workspace distillation of FSA 2nd ed. ch7 + style matrix (no E12 row) | read 2026-09-13 |

EventStoreDB / Marten / Axon / Kafka / XOOM product defaults are out of scope. The workspace note names EventStoreDB / Marten / Axon as *examples of stores*; this card does not version them. Vernon names XOOM / vlingo-symbio as tooling; not reviewed.

---

## 5. Failure modes and when-not-to-use

**Conflating the three costs.** Fowler 2017: two models (CQRS) ≠ a log as SoR (ES) ≠ async. Teams “doing event sourcing” who complain about updating two models are paying CQRS; teams who blame “lots of async” added E4/A2 on top.

**CQRS as a system-wide style.** Fowler 2011 / Young 2012 / Journey / Vernon Kalele: Bounded Context only. Cookie-cutter “every service is CQRS+ES” is Young’s named failure. Vernon’s own samples keep identity/access on ORM.

**Dual-write when stores split.** Azure CQRS points at Transactional Outbox. That is **B7**. Inventing a second `INSERT` into the broker after `COMMIT` is the bug B7 exists to remove. Do not re-derive the outbox here.

**Broker-as-store.** Azure ES 2026. You get A2 fan-out and lose per-entity concurrency and reload-by-id. Then “event sourcing” becomes an unqueryable heap.

**State-delta / `Updated` events.** Azure: `remaining = 42` is a change log without intent. Vernon: `WarbleUpdated` says nothing. New read models cannot reconstruct *why*. Workspace note: past-tense business facts.

**Non-deterministic projections.** Workspace note: do not re-fetch FX rates on replay; put the rate in the event (Fowler 2005 External Queries). Do not resend confirmation email on rebuild (workspace; Fowler gateway).

**Erasure vs immutability.** Workspace + Azure 2026: GDPR-style deletion collides with an append-only log. Design externalized PII or crypto-shredding *before* the first personal event. In-place rewrite of history is Azure’s last resort and breaks the audit trail.

**Read-your-writes surprise.** Dahan treats staleness as a given; Azure split-store CQRS calls it out. A UI that `GET`s the read model 50 ms after `POST` will flake. Either read from the write side for that confirmation, or show “accepted.”

**Optimistic-concurrency retry storms.** Azure’s two-handlers-see-five-seats story needs bounded retry (**C2**), not infinite reload. Not a reason to put a breaker on the event store without thinking (C1).

**Side-effectful “projections.”** Mixing “update the dashboard” with “charge the card” on the same consumer. Rebuild then double-charges. Split: state projections vs integration events (Azure: ES events are often too low-level; you may need separate integration events — A2). Compensation across *services* is **B5**, not a projector.

**Domain Events adopted to justify ES.** Vernon: walk concrete scenarios first; do not reverse the argument from “we want a log as SoR.”

**When-not (restated as failure modes of *choosing* the overlay).** Simple CRUD; short-lived MVP; real-time identical views required; static reference data; team cannot operate schema evolution / projection lag; applying ES because “we bought Kafka”; applying CQRS+ES to every E10 module or every E2 service.

---

## 6. Cross-links

- **Catalog of record:** [system-design-patterns-catalog.md](system-design-patterns-catalog.md) row ⊕E12 (“style-level card”; links the two `cases/` notes).
- **Style SoT:** [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md) — quantum machinery (DB ∈ quantum; sync merges); **no E12 matrix row**; E4 1–many and E2 “most of any style” are the styles this overlay sits *inside*; E10 quantum **1** is the usual host.
- **Linked notes (do not rewrite):** [event-sourcing-cqrs](../../../cases/data-intensive-design/event-sourcing-cqrs.md); [aws/ch08.md](../../../cases/aws/ch08.md).
- **E4** [e4-event-driven-external-research.md](e4-event-driven-external-research.md) — already flags Fowler 2017 “CQRS isn’t about events”; pairing path is §3.4.
- **E10** [e10-modular-monolith-external-research.md](e10-modular-monolith-external-research.md) — host for “add ES inside”; do not treat E12 as leaving E10.
- **E2** [e2-microservices-external-research.md](e2-microservices-external-research.md) — CQRS/ES as query/command complements, not the style.
- **A2** [a2-pubsub-queues-external-research.md](a2-pubsub-queues-external-research.md) — channels, delivery, DLQ; already points E12 at “retention-forever logs as SoR.”
- **B7** [b7-outbox-cdc-external-research.md](b7-outbox-cdc-external-research.md) — dual-write; ES as sibling SoR-is-the-log. Do not copy.
- **B5** [b5-saga-external-research.md](b5-saga-external-research.md) — compensation across steps; [aws/ch08.md](../../../cases/aws/ch08.md) saga paragraph. Do not copy.
- **B4** [b4-strangler-fig-external-research.md](b4-strangler-fig-external-research.md) — migration seam.
- **C9** — idempotent projectors (Azure ES).
- **References already in-tree:** [data-models-references.md](../../../cases/data-intensive-design/data-models-references.md) [65]–[68].

---

## 7. Sources

**Canon (fetched 2026-09-13).**
- https://martinfowler.com/bliki/CQRS.html (2011-07-14)
- https://martinfowler.com/eaaDev/EventSourcing.html (2005-12-12)
- https://www.martinfowler.com/articles/201701-event-driven.html (2017-02-07)
- https://martinfowler.com/bliki/CommandQuerySeparation.html (2005-12-05)
- https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf (Young, November 2010)
- https://cqrs.wordpress.com/documents/cqrs-introduction/ (HTML of the same introduction)
- http://codebetter.com/gregyoung/2010/02/16/cqrs-task-based-uis-event-sourcing-agh/ (Young, 2010-02-16; live **502**; text from attributed gist)
- https://gist.github.com/simonschoof/74e155447fbc2ac47b0f7c0bb5a5f778 (reprint of the 2010-02-16 post)
- https://gregfyoung.wordpress.com/2012/09/09/cqrs-is-not-an-architecture/ (2012-09-09; live HTML)
- https://udidahan.com/2009/12/09/clarified-cqrs/ (2009-12-09)
- https://kalele.io/really-simple-cqrs/ (Vernon)
- https://kalele.io/and-then-this-happened/ (Vernon)
- https://www.dddcommunity.org/wp-content/uploads/files/pdf_articles/Vernon_2011_2.pdf (*Effective Aggregate Design* Part II)
- https://github.com/VaughnVernon/IDDD_Samples (README: `iddd_collaboration` ES+CQRS; LevelDB + MySQL)
- https://ptgmedia.pearsoncmg.com/images/9780321834577/samplepages/0321834577.pdf (IDDD sample TOC only)
- https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs (`ms.date` 2025-02-20)
- https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing (`ms.date` 2026-03-27)
- https://raw.githubusercontent.com/MicrosoftDocs/architecture-center/main/docs/patterns/cqrs.md
- https://raw.githubusercontent.com/MicrosoftDocs/architecture-center/main/docs/patterns/event-sourcing.md
- https://github.com/MicrosoftArchive/cqrs-journey/blob/master/docs/Reference_02_CQRSIntroduction.markdown (not a top-level approach; Young/Dahan BC conversation)

**Workspace (do not rewrite).**
- `.cursor/skills/arch-style/references/style-selection.md`
- `cases/data-intensive-design/event-sourcing-cqrs.md`
- `cases/data-intensive-design/data-models-references.md` [65]–[68]
- `cases/aws/ch08.md`
- `docs/research/sysdesign/{e4,e10,e2,a2,b7,b5,b4}-*-external-research.md`

---

## 8. Uncertain / left out

- **Young 2010 live origin** — `codebetter.com` returned **502** this fetch. Body taken from an attributed gist reprint that names the same URL and date. Do not claim a 2026 live re-read of CodeBetter.
- **Young 2010 cost analysis** (“CQRS+ES is actually less expensive in most cases”) — not re-measured; do not assert as a 2026 fact.
- **Vernon *IDDD* book body** — not re-fetched (copyright). Claims used here are from the public Kalele essays, the 2011 *Effective Aggregate Design* PDF, the Pearson sample TOC, and the IDDD_Samples README. Do not invent page-level quotes from the book.
- **Kalele post dates** for “Really Simple CQRS” and “And Then This Happened” — pages are undated; treat as fetched 2026-09-13, not as a publication day.
- **FSA 2nd ed.** — no CQRS/ES chapter row in style-selection; do not invent stars or a quantum integer for E12. Book body not re-fetched.
- **Microsoft Journey 2012 book body** — not re-fetched; Azure 2026 conference example and the Journey GitHub “not a top-level approach” + Young/Dahan Bounded-Context conversation are the verified pieces. ISBN/authors from workspace [65].
- **Greg Young Code on the Beach 2014** ([66]) — talk; no transcript fetched.
- **Crypto-shredding** — mechanism named by workspace [68] and Azure 2026; Robinson 2019 article not re-fetched.
- **MediatR / Axon / EventStoreDB / Marten / Kafka-as-store / XOOM tuning** — out of scope (no library-defaults). Kafka’s lack of per-entity OCC is Azure’s claim, not a Kafka-config verification (A2 owns Kafka numbers).
- **“CQRS is not having separated models”** (Young 2010) vs Fowler/Azure/Vernon talking about separate models — Young means the *minimum* pattern is two *objects* at the boundary; separate *data* models are an enabled architecture, not CQRS itself. This note keeps both; do not collapse them into a contradiction.
- No controlled study comparing CQRS-same-store vs split-store operability was found; the trade-off table is sourced qualitative consensus.
- Wikipedia CQRS page’s “origin 2010 vs Dahan 2008” priority dispute — not adjudicated; both dated posts are cited.
