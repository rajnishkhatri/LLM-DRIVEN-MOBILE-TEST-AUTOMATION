---
type: analysis
title: 'System models and testing'
description: 'Partial synchrony plus crash-recovery is the useful model. Safety never lies; liveness may wait. TLA+ checks a spec; Jepsen and DST check the code. The model is not the machine.'
tags: [data-intensive-design, distributed-systems, system-model, safety, liveness, dst]
---

# System models and testing

**See also:** [chapter overview](distributed-systems-overview.md) · [byzantine faults](byzantine-faults.md) · [quorums and fencing](quorums-and-fencing.md) · [reliability](reliability.md) · [references](distributed-systems-references.md)

Algorithms need a formal **system model**: which faults you
assume, stripped of hardware brand. Consensus (next chapter)
is proved inside a model.

## Timing

| Model | Assumption |
|---|---|
| **Synchronous** | Bounded network delay, bounded pauses, bounded clock error. Not zero — a known cap ([108](distributed-systems-references.md)). Unrealistic for Ethernet/IP. |
| **Partially synchronous** | Synchronous *most* of the time; bounds can shatter, then delay, pauses, and clock error become arbitrary ([108](distributed-systems-references.md)). The realistic datacenter. |
| **Asynchronous** | No timing assumptions, no clock, no timeouts. Very restrictive. Some algorithms still exist. |

## Nodes

| Model | Assumption |
|---|---|
| **Crash-stop** (fail-stop) | A node fails only by crashing, then is gone forever ([109](distributed-systems-references.md)). |
| **Crash-recovery** | Crash at any time; may return. Stable storage survives; memory does not. |
| **Degraded / partial** | Slow, not dead. NIC drops to 1 Kb/s ([110](distributed-systems-references.md)); GC dominates ([111](distributed-systems-references.md)); worn SSDs, heat, firmware ([112](distributed-systems-references.md)). **Limping**, **gray failure**, **fail-slow** ([113](distributed-systems-references.md)) — often worse than a clean crash. A background thread deadlocks while health checks still pass ([114](distributed-systems-references.md)). |
| **Byzantine** | Anything, including deceit. See [Byzantine faults](byzantine-faults.md). |

The useful default for real systems: **partial synchrony +
crash-recovery**. Unbounded delay, pauses, and slow nodes are
in; malice is out.

## Correctness: safety and liveness

Write the properties you want. For a
[fencing-token](quorums-and-fencing.md#fencing-tokens)
generator:

- **Uniqueness** — no two grants return the same token.
- **Monotonic sequence** — if *x* finished before *y* started,
  then `tx < ty`.
- **Availability** — a non-crashed requester eventually gets
  a reply.

An algorithm is correct in a model if those properties hold
in every situation the model allows. If every node crashes
or every delay is infinite, nothing makes progress. Split
the properties
([116](distributed-systems-references.md)):

**Safety** — once violated, you can point at the moment
(a duplicate token). The damage cannot be undone.

**Liveness** — may fail to hold *yet* (request in flight);
there is always hope. The word “eventually” is a tell.
[Eventual consistency](replication-lag.md) is a liveness
property ([115](distributed-systems-references.md)).

Informal slogans (“nothing bad” / “something good”) are
value judgments. Use the precise split.

Distributed algorithms typically require **safety in every
situation the model allows** — even if all nodes crash, do
not return a wrong result. Liveness may have caveats: a
reply only if a majority is up and the network eventually
heals. Partial synchrony *requires* that outages are finite.

## The model is not the machine

Crash-recovery assumes the disk survives. Firmware that
does not see the drives
([118](distributed-systems-references.md)), a wiped volume
([117](distributed-systems-references.md)), and a node with
amnesia all break quorum algorithms that trust “I stored
this.” A richer “stable storage *usually* survives” model
is harder to reason about.

Theory may declare some events impossible. A real program
still needs a branch for the impossible — even if that
branch is `printf` and `exit` for a human
([119](distributed-systems-references.md)). That is the
gap between computer science and software engineering.
The abstraction is still how you make the problem small
enough to think.

## Formal methods and randomized testing

Concurrency, partial failure, and delay explode the state
space. Two complementary answers: prove the *algorithm*;
test the *implementation*. AWS, FoundationDB, and
TigerBeetle combine them
([120](distributed-systems-references.md),
[121](distributed-systems-references.md),
[122](distributed-systems-references.md),
[123](distributed-systems-references.md)).

### Model checking

Write a spec in TLA+, Gallina, FizzBee. A model checker
walks states and looks for broken invariants. It does not
prove the infinite space; you bound messages or shrink the
model. Still finds bugs prose misses: viewstamped
replication data loss from an ambiguous description
([127](distributed-systems-references.md)). CockroachDB,
TiDB, Kafka use specs
([124](distributed-systems-references.md),
[125](distributed-systems-references.md),
[126](distributed-systems-references.md)).

The spec is not the code. They drift
([128](distributed-systems-references.md)). Checking
equivalence needs instrumentation
([129](distributed-systems-references.md)).

## Fault injection

Put the implementation in a production-like (or production)
environment and break it: kill, pause, unmount, partition.
Netflix Chaos Monkey
([130](distributed-systems-references.md)) popularized
production injection —
[chaos engineering](reliability.md#fault-tolerance).
Coordinators pick faults; scripts use `kill`, `umount`,
firewall rules. Jepsen packages injectors and has found
serious bugs in widely used stores
([131](distributed-systems-references.md),
[132](distributed-systems-references.md),
[133](distributed-systems-references.md)).

## Deterministic simulation testing

DST explores a state space like a model checker, but on
**your code**. Network, I/O, and clocks become mocks the
simulator orders. Failures replay. Three insertion points:

- **Application-level** — build for it. FoundationDB’s Flow
  ([134](distributed-systems-references.md)); TigerBeetle’s
  single event-loop state machine
  ([135](distributed-systems-references.md)).
- **Runtime-level** — patch the async runtime (FrostDB /
  Go ([136](distributed-systems-references.md)); Rust
  MadSim over Tokio, S3, Kafka).
- **Machine-level** — a hypervisor that answers every
  nondeterministic syscall deterministically (Antithesis).
  Whole containers become a replayable cluster.

Mocked clocks mean a timeout can fire without waiting wall
time. Hash-iteration order and allocator failure remain
easy ways to leak nondeterminism.

Determinism shows up elsewhere for the same reason:
[event sourcing](event-sourcing-cqrs.md) replays a log;
[workflows](durable-workflows.md) require deterministic
definitions; state-machine replication (next chapter)
executes the same transactions on each replica —
[statement-based logs](replication-logs.md#statement-based-replication)
and
[serial stored procedures](serializability.md#actual-serial-execution)
are earlier variants.

**Architect takeaway:** name the model (almost always
partial sync + crash-recovery, honest nodes). Require
safety when the network is down; let liveness wait for
repair. TLA+ the protocol; Jepsen or DST the binary. Budget
an “impossible” handler. A gray failure is in the model
whether you wrote it down or not.
