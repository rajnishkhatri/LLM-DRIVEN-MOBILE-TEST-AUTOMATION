---
type: analysis
title: 'Event sourcing and CQRS'
description: 'Write an append-only log of immutable events; derive read-optimized views. Reproducible projections are the contract. Immutability collides with the right to erasure.'
tags: [data-intensive-design, data-models, event-sourcing, cqrs, derived-data]
---

# Event sourcing and CQRS

**See also:** [chapter overview](data-models-overview.md) · [systems of record vs derived data](operational-vs-analytical.md#systems-of-record-and-derived-data) · [star schemas](star-snowflake-analytics.md) · [evolvability](maintainability.md#evolvability-making-change-easy) · [privacy](law-and-society.md) · [references](data-models-references.md)

In the models discussed so far, data is queried in the same form as it is
written — JSON documents, rows in tables, or vertices and edges. In
complex applications it can be difficult to find a single representation
that satisfies all the ways the data needs to be queried and presented. In
those situations it can help to **write data in one form** and **derive
representations optimized for different types of reads**.

This is the idea in
[systems of record and derived data](operational-vs-analytical.md#systems-of-record-and-derived-data);
ETL into a [data warehouse](operational-vs-analytical.md) is one example.
Take it further: if you are going to derive one representation from
another anyway, choose representations optimized for writing and reading
respectively. How would you model data if you wanted to optimize only for
writing, and efficient queries were of no concern?

Perhaps the simplest, fastest, and most expressive way of writing data is
an **event log**: every time you want to write, encode it as a
self-contained string (perhaps JSON), including a timestamp, and append it
to a sequence of events. Events are **immutable**; you never change or
delete them, only append more events (which may supersede earlier ones).
An event can contain arbitrary properties.

## Conference bookings as events

A conference is a complex business domain: individual attendees register
and pay by card; companies order seats in bulk, pay by invoice, and later
assign seats to people; a certain number of seats may be reserved for
speakers, sponsors, volunteers. Reservations may be canceled; the
organizer might change capacity by moving to a different room. Simply
calculating available seats becomes a challenging query.

Every change to conference state (opening registrations, making and
canceling registrations) is first stored as an event. Whenever an event
is appended, several **materialized views** (also **projections** or
**read models**) are updated to reflect its effect. One view might collect
all information related to each booking’s status; another computes charts
for the organizer’s dashboard; a third generates files for the printer
that produces attendees’ badges.

Using events as the source of truth and expressing every state change as
an event is **event sourcing** ([65](data-models-references.md),
[66](data-models-references.md)). Maintaining separate read-optimized
representations and deriving them from the write-optimized representation
is **command query responsibility segregation (CQRS)**
([67](data-models-references.md)). The terms originated in the DDD
community; similar ideas have been around for a long time — for example,
in [state machine replication](replication-logs.md#statement-based-replication)
(shared logs are a later chapter).

When a user request comes in it is called a **command**, and it first
needs to be validated. Once the command has been executed and determined
valid (enough seats for a reservation), it becomes a **fact**, and the
corresponding event is added to the log. The event log should contain only
valid events; a consumer that builds a materialized view is not allowed to
reject an event.

Name events in the **past tense** (“the seats were booked”), because an
event is a record that something has happened. Even if the user later
cancels, the fact remains true that they formerly held a booking; the
cancellation is a separate event added later.

A similarity with a
[star-schema fact table](star-snowflake-analytics.md): both are
collections of events that happened in the past. Differences: fact-table
rows all have the same columns; event sourcing may have many event types,
each with different properties. A fact table is unordered; in event
sourcing **order matters** — if a booking is made and then canceled,
processing those events in the wrong order would not make sense.

## Advantages

- For the people developing the system, events better communicate **why**
  something happened. “The booking was canceled” is easier to understand
  than “the `active` column on row 4001 of `bookings` was set to false,
  three rows were deleted from `seat_assignments`, and a refund row was
  inserted into `payments`.” Those row modifications may still happen when
  a view processes the cancellation; driven by an event, the reason is
  clearer.
- Materialized views are derived from the event log in a **reproducible**
  way. You should always be able to delete the views and recompute them by
  processing the same events in the same order, using the same code. If
  there was a bug in view maintenance, delete the view and recompute with
  the new code. You can rerun as often as you like and inspect behavior.
- Multiple views, each optimized for particular queries. Stored in the
  same database as the events or a different one. Any data model;
  denormalized for fast reads. You can even keep a view only in memory, as
  long as it is OK to recompute it on restart.
- Presenting existing information in a new way is easy: build a new view
  from the existing log. Evolve by adding new event types or new
  properties on existing types (older events remain unmodified). Chain new
  behaviors off existing events (when an attendee cancels, offer the seat
  to the next person on the waiting list).
- If an event was written in error, write a subsequent **deletion event**
  to reverse it. Downstream views incorporate the deletion automatically.
  In a database where you update and delete directly, a committed
  transaction is often difficult to reverse. Event sourcing can therefore
  reduce irreversible actions (see
  [evolvability](maintainability.md#evolvability-making-change-easy)).
- The event log can serve as an **audit log**, valuable in regulated
  industries.
- Event logs can typically handle higher write throughput because of
  sequential access. A temporary burst can be absorbed; downstream view
  maintainers catch up at their own pace.

## Downsides

- Be careful if **external information** is involved. An event contains a
  price in one currency; a view needs another currency. Exchange rates
  fluctuate, so fetching the rate from an external source when processing
  the event would give a different result if you recomputed the view on
  another date. To keep processing **deterministic**, include the rate in
  the event itself, or query the historical rate at the event’s timestamp
  in a way that always returns the same result for the same timestamp.
- Immutability collides with personal data. Users may exercise a right
  (e.g. under the GDPR) to request deletion. If the log is per-user, you
  can delete that user’s log; that does not work if the log mixes users.
  You can store personal data outside the event, or encrypt it with a key
  you later delete (**crypto-shredding**
  ([68](data-models-references.md))), which also makes recomputing derived
  state harder. See [law and society](law-and-society.md).
- Reprocessing events requires care if there are **externally visible side
  effects** — you probably don’t want to resend confirmation emails every
  time you rebuild a view.

You can implement event sourcing on top of any database. Some systems are
specifically designed for it: EventStoreDB, MartenDB (PostgreSQL), Axon
Framework. You can also use [message brokers](event-driven-dataflow.md) such as
Apache Kafka to store the log, and stream processors to keep views up
to date (a later chapter).

The only important requirement: the event storage system must guarantee
that all materialized views process events in **exactly the same order**
as they appear in the log. That is not always easy in a distributed
system (a later chapter).

**Architect takeaway:** split write shape from read shape. The log is the
system of record; views are derived and rebuildable. Name events in the
past tense, keep processing deterministic, and have a plan for erasure
before you put personal data in an immutable log.
