---
type: analysis
title: 'Unreliable networks'
description: 'Shared-nothing machines talk only by packets. Send a request, get no reply: lost, queued, crashed, paused, or the reply vanished. TCP does not make that go away.'
tags: [data-intensive-design, distributed-systems, network, tcp, partition]
---

# Unreliable networks

**See also:** [chapter overview](distributed-systems-overview.md) · [timeouts](timeouts-and-delays.md) · [scalability / shared-nothing](scalability.md#shared-memory-shared-disk-and-shared-nothing) · [REST and RPC](rest-rpc-dataflow.md) · [references](distributed-systems-references.md)

Mainframes bought reliability with redundant *components* (RAID
inside one box). The systems these notes care about are
[shared-nothing](scalability.md#shared-memory-shared-disk-and-shared-nothing):
machines with their own memory and disk, talking only over a
network. [Replication](replication-overview.md) is the redundancy.
Even “shared” object storage is reached by a network call.

The internet and most datacenter Ethernet are **asynchronous packet
networks**. A node can send a packet. The network does not promise
*when* it arrives, or *that* it arrives.

Send a request, expect a response. Figure 9-1 — you cannot tell
these apart:

1. The request was lost (unplugged cable).
2. The request is queued and will arrive later (congestion).
3. The remote node crashed or was powered down.
4. The remote node is paused
   ([GC, VM steal](process-pauses.md)) and will resume.
5. The node processed the request; the response was lost.
6. The node processed the request; the response is delayed.

The only signal is: no response yet. The usual handling is a
[timeout](timeouts-and-delays.md). After the timeout you still do
not know whether the remote side got the request — and a queued
copy may still be delivered.

## The limitations of TCP

Packets are a few kilobytes. Applications send larger messages.
TCP (and QUIC, SCTP, BitTorrent uTP) splits a stream, reorders,
checksums, and retransmits. Congestion control / flow control /
backpressure decides how fast to send
([5](distributed-systems-references.md)).

“Send” writes into an OS buffer. The stack emits a packet when the
congestion window allows. Switches and routers later. The receiver
acks into its own buffer, then wakes the application
([6](distributed-systems-references.md)).

That is not application-level reliability:

- TCP cannot tell a lost packet from a lost ack. Retransmit does
  not plug the cable back in. After a configurable timeout it
  errors to the application.
- Dedup and retransmission are **per connection**. Reconnect and
  retry, and you can duplicate.
- A connection closed with an error does not tell you how much the
  remote application processed ([6](distributed-systems-references.md)).
  A TCP ack means the *kernel* got the bytes; the process may have
  crashed before handling them. Confidence needs a positive
  response from the application
  ([7](distributed-systems-references.md) — the end-to-end
  argument).

TCP is still the right way to send messages bigger than a packet.
Once the connection is up, a length-prefixed frame carries many
requests. [HTTP and RPC](rest-rpc-dataflow.md) work that way.

UDP skips retransmission and flow control. Use it when late data
is worthless (VoIP, videoconference): fill the gap with silence
and let the human retry. Switch queues and scheduling delay
remain. See
[timeouts — TCP versus UDP](timeouts-and-delays.md#tcp-versus-udp).

## Network faults in practice

Decades of building networks have not made them reliable, even
inside one company’s datacenter
([8](distributed-systems-references.md)):

- One medium DC: about 12 network faults per month; half a single
  machine, half a rack ([9](distributed-systems-references.md)).
- Redundant switches do not remove human error (misconfiguration),
  a major cause of outages
  ([10](distributed-systems-references.md)).
- Wide-area fiber: cows, beavers, sharks, scavengers, sabotage
  [11]–[17].
- Cross-region RTTs of **minutes** at high percentiles
  ([18](distributed-systems-references.md)). Inside one DC, a
  switch upgrade can delay packets more than a minute
  ([19](distributed-systems-references.md)). Assume arbitrary
  delay.
- Partial interruption: A talks to B, B to C, A cannot reach C
  ([20](distributed-systems-references.md),
  [21](distributed-systems-references.md)). A NIC that drops all
  inbound and still sends outbound
  ([22](distributed-systems-references.md)). One direction working
  does not imply the other.
- A brief cut can have effects that outlast the cut
  ([8](distributed-systems-references.md),
  [20](distributed-systems-references.md),
  [23](distributed-systems-references.md)).

If the error path is untested, recovery can deadlock the cluster
([24](distributed-systems-references.md)) or delete the data
([25](distributed-systems-references.md)). Handling a fault does
not mean *tolerating* it — showing an error is valid if the
network is usually fine — but you must know the reaction and be
able to recover. Inject the fault
([system models](system-models.md#fault-injection)).

## Network partitions

A **network partition** (netsplit) cuts one part of the network
from the rest. It is not a special kind of fault — just an
interruption with a particular shape. It is **not**
[sharding](sharding-overview.md), which is also called
partitioning.

**Architect takeaway:** the network is not a function call. No
reply is not a boolean. Design every RPC for lost, late, and
duplicate; require an application ack for “this write happened.”
A partition is an ordinary timeout with a larger blast radius.
