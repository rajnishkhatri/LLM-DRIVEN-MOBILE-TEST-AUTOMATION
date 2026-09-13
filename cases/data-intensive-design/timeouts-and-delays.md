---
type: analysis
title: 'Timeouts and unbounded delays'
description: 'A timeout is the only sure fault detector, and it is a guess. Packet delay is unbounded. Circuit switching buys a bound; packet switching buys utilization. There is no correct constant timeout.'
tags: [data-intensive-design, distributed-systems, timeout, fault-detection, queueing]
---

# Timeouts and unbounded delays

**See also:** [chapter overview](distributed-systems-overview.md) · [unreliable networks](unreliable-networks.md) · [process pauses](process-pauses.md) · [performance](performance.md) · [references](distributed-systems-references.md)

Load balancers drop dead backends. A
[single-leader](single-leader-replication.md#handling-node-outages)
database promotes a follower. Both need to know a node is dead.
The network makes that a guess.

Sometimes you get an explicit no: RST/FIN on a closed port; a
crash-notification script (HBase
([26](distributed-systems-references.md))); a switch management
API; ICMP Destination Unreachable. None of those is available on
the public internet, in a shared DC without switch access, or
when the management path is itself partitioned. The router has no
magic detector.

Assume silence. Retry a few times, wait, declare dead. The node
may still be alive. Too short a timeout: false death, duplicate
work ([quorums and fencing](quorums-and-fencing.md)). Too long:
users wait. Transferring a “dead” node’s load onto an already
overloaded cluster can
[cascade](performance.md#when-an-overloaded-system-wont-recover)
— in the extreme, every node declares every other node dead.

## There is no correct constant

Imagine a network that delivers every packet within *d* or loses
it, and a live node that always handles a request within *r*.
Then `2d + r` is a sound timeout: miss it and the network or the
node is broken.

Most systems have neither bound. Asynchronous networks have
**unbounded delay**. Servers do not guarantee a maximum handle
time ([process pauses](process-pauses.md#providing-response-time-guarantees)).
Failure detection needs the *tail*, not the average: one RTT spike
breaks a tight timeout.

## Queueing is why delay varies

Road congestion is the analogy. Packet delay is mostly
**queueing** ([27](distributed-systems-references.md)):

- Several senders, one destination link: the switch serializes.
  A full queue **drops** the packet. Retransmit. The network is
  “fine.”
- The destination CPU is busy: the OS queues the request
  ([28](distributed-systems-references.md)). Arbitrary wait.
- A hypervisor pauses a VM for tens of milliseconds; inbound
  packets buffer in the monitor
  ([29](distributed-systems-references.md)).
- TCP’s own congestion window queues at the *sender* before the
  packet enters the network.

TCP retransmission looks like delay to the application, not like
loss.

Public clouds and multi-tenant DCs share links, NICs, and CPUs.
A noisy neighbor can saturate a path
([30](distributed-systems-references.md),
[31](distributed-systems-references.md)). You do not control
that load. Measure RTT over a long window, many machines, and
pick a timeout as a trade-off between detection delay and false
death. Better: adapt. The **Φ accrual** failure detector
([32](distributed-systems-references.md)) (Akka, Cassandra
([33](distributed-systems-references.md))) tracks the observed
distribution. TCP retransmission timeouts do the same
([5](distributed-systems-references.md)).

## TCP versus UDP

Videoconference and VoIP often use UDP. The trade-off is
reliability versus *variability* of delay: no flow control, no
retransmit, so some of the delay sources disappear. Switch
queues and scheduling remain. Late audio is worthless — fill
with silence; the human retries.

## Synchronous versus asynchronous networks

Why not fix this in hardware?

A classical telephone network (non-cellular, non-VoIP) is
extremely reliable. A call establishes a **circuit**: reserved
bandwidth on the whole path until hangup
([34](distributed-systems-references.md)). ISDN: 4,000 frames/s,
16 bits per frame per direction — 16 bits every 250 µs, guaranteed
([35](distributed-systems-references.md)). No queueing, so
**bounded delay**. That is a **synchronous** network.

A TCP connection is not a circuit. It opportunistically uses
whatever bandwidth is free. Idle TCP uses almost none. Ethernet
and IP are **packet-switched**: they queue; delay is unbounded;
there is no circuit.

Datacenters and the internet optimize for **bursty** traffic. A
web page, an email, a file has no particular bits-per-second
requirement — finish as soon as possible. Guess a circuit
bandwidth too low and you waste capacity; too high and the
circuit cannot be admitted. TCP adapts.

### Latency versus utilization

Variable delay is **dynamic resource partitioning**. A 10,000-call
trunk statically reserves a slot even if you are the only caller.
The internet jostles packet-by-packet and utilizes the wire
better — cheaper bytes, queues as the cost. CPUs do the same:
time-sharing a core beats pinning cycles to a thread
([36](distributed-systems-references.md)); the cloud packs VMs
onto one machine for the same reason.

Bounded delay is possible if you statically partition (dedicated
hardware, exclusive bandwidth). You pay in utilization. Multi-
tenancy is cheaper and jittery. Variable delay is a cost/benefit
choice, not a law of nature.

### Hybrids and QoS

ATM tried to mix circuit and packet; it stayed in telco cores.
InfiniBand does end-to-end flow control at the link layer
([37](distributed-systems-references.md)) and still congests
([38](distributed-systems-references.md)). QoS (priority,
scheduling, admission control) and L4S can emulate a circuit or
give a *statistical* bound
([27](distributed-systems-references.md),
[34](distributed-systems-references.md)). Linux `tc` can
reprioritize. Multi-tenant DCs, public clouds, and the public
internet do not turn this on. Deployed technology does not let
you promise delay or reliability. Timeouts stay experimental.

ISP peering and BGP look more like circuits — at the *network*
level, on a long timescale, not per host connection.

**Architect takeaway:** pick a timeout from measured jitter, or
adapt it. Do not copy a constant from another system. A
“synchronous network” assumption (bounded *d*, bounded *r*) is
false on Ethernet/IP; protocols that need it
([3PC](distributed-transactions.md), hard real-time) do not
travel. Buy a bound only if you will pay the utilization.
