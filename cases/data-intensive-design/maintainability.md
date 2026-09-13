---
type: analysis
title: 'Maintainability'
description: 'Most of the cost is after ship. Design for operability, simplicity, and evolvability, and minimize irreversible changes.'
tags: [data-intensive-design, nfr, maintainability, operability, evolvability]
---

# Maintainability

**See also:** [NFR overview](nfr-overview.md) · [operations in the cloud era](cloud-vs-self-hosting.md#operations-in-the-cloud-era) · [reliability](reliability.md) · [NFR references](nfr-references.md)

Software does not wear out or suffer material fatigue. Requirements evolve,
the environment changes (dependencies, platform), and bugs need fixing.

The majority of software cost is not initial development but **ongoing
maintenance**: fixing bugs, keeping systems operational, investigating
failures, adapting to new platforms, new use cases, repaying technical debt,
and adding features.

Maintenance is especially hard for **legacy** systems: outdated technologies
few engineers understand (mainframes, COBOL), lost institutional knowledge as
people leave, other people’s mistakes. Because computer systems intertwine
with the human organizations they support, maintenance is as much a people
problem as a technical one.

Every system we create today will become a legacy system if it is valuable
enough to survive. Design with maintenance in mind. We cannot always predict
which decisions will hurt, but three principles are widely applicable:

| Principle | Intent |
|---|---|
| **Operability** | Easy for the organization to keep the system running smoothly |
| **Simplicity** | Easy for new engineers to understand: well-understood patterns, no unnecessary complexity |
| **Evolvability** | Easy to change later for unanticipated use cases |

## Operability: making life easy for operations

Human processes are at least as important for reliable operations as software
tools. A common claim: good operations can work around incomplete software;
good software cannot run reliably with bad operations. See also
[operations in the cloud era](cloud-vs-self-hosting.md#operations-in-the-cloud-era).

At thousands of machines, manual maintenance is unreasonably expensive;
**automation is essential**. Automation is also a two-edged sword. Edge cases
(rare failures) still need manual intervention, and those leftover cases tend
to be the most complex — so more automation requires a *more* skilled
operations team. An automated system that goes wrong is often harder to
troubleshoot than one that relies on an operator for some actions. More
automation is not always better for operability; the sweet spot depends on the
application and organization.

Good operability makes **routine tasks easy**, so operations can focus on
high-value work. Data systems help by:

- Exposing key metrics to monitoring and supporting
  [observability](distributed-vs-single-node.md#problems-with-distributed-systems)
- Avoiding dependency on individual machines (take one down for maintenance;
  the system continues)
- Providing documentation and an easy operational model (“If I do X, Y
  happens”)
- Good defaults, with freedom to override
- Self-healing where appropriate, with manual control when needed
- Predictable behavior, minimizing surprises

## Simplicity: managing complexity

Small projects can have simple, expressive code. As they grow they often
become hard to understand. Complexity slows everyone who works on the system
and raises maintenance cost. A project mired in complexity is sometimes called
a **big ball of mud**.

When complexity makes maintenance hard, budgets and schedules overrun. Changing
complex software has a greater risk of bugs: hidden assumptions, unintended
consequences, unexpected interactions. Reducing complexity improves
maintainability; **simplicity should be a key goal**.

Simple systems are easier to understand, so solve a given problem in the
simplest way possible. That is easier said than done. Simplicity is often
subjective: one system hides a complex implementation behind a simple
interface; another has a simple implementation that exposes more internals —
which is simpler?

One attempt splits complexity into **essential** (inherent in the problem
domain) and **accidental** (limitations of tooling). The distinction is
flawed, because the boundary shifts as tooling evolves.

One of the best tools for managing complexity is **abstraction**. A good
abstraction hides implementation detail behind a clean façade and can be reused
across applications — reuse is not only cheaper than reimplementing, it
concentrates quality improvements. High-level languages hide machine code and
syscalls; SQL hides on-disk structures, concurrency, and crash recovery. You
are still using the lower layer; you are not thinking about it directly.

Application-level abstractions (design patterns, domain-driven design) sit on
top of general-purpose ones these notes care about: transactions, indexes,
event logs.

## Evolvability: making change easy

Requirements will not stay unchanged. You learn new facts, unanticipated use
cases appear, priorities shift, users want features, platforms change, law
changes, growth forces architectural change.

Agile working patterns are a process framework for adapting. Technical tools
from that community (TDD, refactoring) help at the level of a single codebase.
These notes look for agility at the level of a **system of several
applications or services**. That system-level agility is **evolvability**.

Ease of change is closely linked to simplicity and abstractions. Loosely
coupled, simple systems are usually easier to modify than tightly coupled,
complex ones.

A major factor that makes change difficult in large systems is
**irreversibility**. Migrating from one database to another is much higher
stakes if you cannot switch back. Minimizing irreversibility improves
flexibility.

**Architect takeaway:** budget maintenance as the main cost. Operability is
what operations can actually do on a Tuesday; simplicity is what a new
engineer can hold in their head; evolvability is whether you can reverse a
decision. Prefer reversible steps over clever ones.
