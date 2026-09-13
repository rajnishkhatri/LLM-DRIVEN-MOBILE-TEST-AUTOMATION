---
type: overview
title: 'The trouble with distributed systems'
description: 'A single computer is usually all-or-nothing. Several machines share a network: parts fail, packets vanish, clocks lie, processes freeze. Partial failure is the defining property.'
tags: [data-intensive-design, distributed-systems, partial-failure, fault-tolerance, overview]
---

# The trouble with distributed systems

> They’re funny things, Accidents. You never have them till you’re
> having them.
>
> — A. A. Milne, *The House at Pooh Corner* (1928)

[Reliability](reliability.md) is continuing to meet the SLO when
parts go wrong. Anticipating the parts is the hard work. The happy
path is tempting; faults are the edge cases. In a large enough
system a one-in-a-million event happens every day.

A program on one machine is mostly deterministic. Hardware
corruption exists
([hardware faults](reliability.md#hardware-and-software-faults))
but is rare enough that we pretend the machine is an idealized
model: a CPU instruction does the same thing; a write stays written.
When the hardware does fail, the usual outcome is a **total** crash
— kernel panic, blue screen — not a wrong answer. That is a
deliberate design: a crash is easier than a silent lie.

Several machines on a network are a different physical world.
Faults are frequent. Some nodes work while others are broken in
unpredictable ways. That is a **partial failure**, and it is
**nondeterministic**: the same multi-node operation sometimes works
and sometimes does not. You may not even know which
([1](distributed-systems-references.md),
[2](distributed-systems-references.md),
[4](distributed-systems-references.md)).

Coda Hale’s list: long-lived partitions inside one DC, PDU
failures, switch failures, accidental rack power-cycles, whole-DC
backbone and power failures, and a hypoglycemic driver putting a
Ford pickup through the HVAC
([3](distributed-systems-references.md)).

If the system **tolerates** partial failure, it can be more reliable
than one node: a [rolling upgrade](reliability.md) reboots one
machine at a time while the service stays up. Suspicion, pessimism,
and paranoia pay off. Test the unlikely cases; they will happen.

Prior chapter: [transactions](transactions-overview.md). Why
distribute at all — and when not to — is
[distributed versus single-node](distributed-vs-single-node.md).
Consensus algorithms that cope with these faults are the next
chapter (not yet filed).

## Topic map

| Topic | The question | Concept |
|---|---|---|
| Networks | Request sent, no reply. Lost, down, or reply lost? | [Unreliable networks](unreliable-networks.md) |
| Timeouts | How long is dead? Delay is unbounded. | [Timeouts and unbounded delays](timeouts-and-delays.md) |
| Clocks | NTP, LWW timestamps, TrueTime. Who got there first? | [Unreliable clocks](unreliable-clocks.md) |
| Pauses | GC, VM steal, SIGSTOP. The lease expired while you slept. | [Process pauses](process-pauses.md) |
| Quorums | A node cannot trust its own “I am alive.” | [Quorums and fencing](quorums-and-fencing.md) |
| Byzantine | Nodes that lie, not just crash. When is that the model? | [Byzantine faults](byzantine-faults.md) |
| Models | Sync / partial-sync / async. Safety vs liveness. How we test. | [System models and testing](system-models.md) |

Citations for this chapter live in
[distributed-systems references](distributed-systems-references.md).
Earlier chapters keep their own lists:
[trade-off references](references.md),
[NFR references](nfr-references.md),
[data-model references](data-models-references.md),
[storage references](storage-references.md),
[encoding references](encoding-references.md),
[replication references](replication-references.md),
[sharding references](sharding-references.md),
[transaction references](transactions-references.md).

## Summary

Partial failure is the defining property. A packet may be lost or
arbitrarily delayed; the reply too. A clock may jump, drift, or
disagree with its neighbor. A process may freeze, be declared dead,
and wake without noticing. There is no shared memory and no common
knowledge ([83](distributed-systems-references.md)) — only messages
on an [unreliable network](unreliable-networks.md).

Detecting the fault is already hard. Most algorithms use a
[timeout](timeouts-and-delays.md); a timeout cannot tell a dead node
from a slow network. Limping (gray, fail-slow) nodes that still
answer health checks are worse.

A single node cannot safely decide for the cluster. Use a
[quorum](quorums-and-fencing.md). Assume the node will pause, the
clock will lie, and a delayed packet will arrive after the lease
has moved on. [Fencing tokens](quorums-and-fencing.md#fencing-tokens)
stop the zombie; they do not stop a
[Byzantine](byzantine-faults.md) liar.

None of this is a law of nature. Bounded delay and hard real-time
are possible; they cost utilization
([timeouts](timeouts-and-delays.md#synchronous-versus-asynchronous-networks),
[process pauses](process-pauses.md#providing-response-time-guarantees)).
Most data systems choose cheap and unreliable over expensive and
reliable.

If the problem fits on one machine — an embedded store, a single
node — keep it there
([distributed versus single-node](distributed-vs-single-node.md)).
Scale, locality, and fault tolerance are the reasons not to.

**Architect takeaway:** write the fault model before the algorithm.
Datacenter Ethernet is an asynchronous packet network: no bound on
delay, no way to tell lost from late. Time-of-day clocks are not
an event order. A lease without a fencing token is a
split-brain waiting to happen. Safety properties must hold when
the network is down; liveness may wait for repair. Prove the
protocol in a [system model](system-models.md), then test the
implementation — the model is not the machine.

Next chapter (consensus, linearizability, total order) is not yet
filed in this bundle.
