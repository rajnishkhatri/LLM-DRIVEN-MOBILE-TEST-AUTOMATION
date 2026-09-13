---
type: analysis
title: 'Quorums and fencing'
description: 'A node cannot trust “I am alive.” Majority decides death. A lease without a fencing token is split brain: the zombie still writes. The storage layer must reject stale tokens.'
tags: [data-intensive-design, distributed-systems, quorum, fencing, leases]
---

# Quorums and fencing

**See also:** [chapter overview](distributed-systems-overview.md) · [process pauses](process-pauses.md) · [leaderless quorums](leaderless-replication.md#using-quorums-for-reading-and-writing) · [single-leader failover](single-leader-replication.md#handling-node-outages) · [references](distributed-systems-references.md)

A node cannot know another node’s state except by messages. No
reply is not a state
([unreliable networks](unreliable-networks.md)). The
consequences sound philosophical: what is true here, and how
sure are we if perception is unreliable
([83](distributed-systems-references.md))? You do not need the
meaning of life. State a **system model**
([system models](system-models.md)) and design to it.

## The majority rules

Asymmetric fault: a node receives everything and cannot send
([22](distributed-systems-references.md)). It is healthy; the
others hear nothing; after a
[timeout](timeouts-and-delays.md) they declare it dead. It
screams “I’m not dead” on a one-way link.

Or it notices the missing acks, still cannot stop the funeral.

Or it
[pauses](process-pauses.md) for a minute, is loaded onto the
hearse, then sits up chatting. From its point of view almost no
time passed.

A node cannot trust its own judgment. A system that relies on
one node sticks when that node fails. Many algorithms vote —
a **quorum**
([leaderless](leaderless-replication.md#using-quorums-for-reading-and-writing)).
That includes declaring death. If a quorum says you are dead,
you step down, even if you feel fine.

The usual quorum is a **majority** (more than half). Other
shapes exist. Three nodes tolerate one fault; five tolerate
two. There is only one majority, so two conflicting decisions
cannot both have a majority. Consensus algorithms (next
chapter) use this.

## Distributed locks and leases

Locks and leases are a common bug farm
([84](distributed-systems-references.md)). A lease is a lock
that times out so a crashed, paused, or partitioned holder
does not block the cluster forever
([process pauses](process-pauses.md)). You want one of
something:

- One leader per shard — avoid
  [split brain](single-leader-replication.md#handling-node-outages).
- One writer of a file or object — avoid corruption.
- One worker on an input file — avoid wasted compute.

Several nodes simultaneously believing they hold the lease is
the case to design. Wasted compute is cheap. Two leaders or
two writers is data loss.

Figure 9-4 is not theoretical; HBase had it
([85](distributed-systems-references.md),
[86](distributed-systems-references.md)). Client 1 holds a
lease, pauses, the lease expires, client 2 writes, client 1
wakes and writes. Split brain on the file. A lock service
(usually a consensus system — next chapter) is not enough if
the *storage* side does not check who is current.

Figure 9-5: no pause. Client 1 crashes after sending a write
that sits in the network for a minute
([unreliable networks](unreliable-networks.md)). The lease
expires, client 2 writes, then client 1’s packet arrives.
Same corruption.

## Fencing tokens

A **zombie** is a former holder that has not noticed. You
cannot rule zombies out. You **fence** them so they cannot
split-brain.

Powering the VM off, pulling the NIC, or STONITH
([87](distributed-systems-references.md)) does not stop a
packet that is already in flight (Figure 9-5). Nodes can
STONITH each other
([19](distributed-systems-references.md)). Detection can be
too late.

Figure 9-6: every grant returns a **fencing token**, a number
that only increases. Every write to storage carries the token.
Storage remembers the highest token it has accepted and
rejects a lower one. Client 1 has 33, pauses, expires. Client
2 writes with 34. Client 1’s late write with 33 is refused.
The new holder should write immediately so zombies are fenced
as soon as that write lands.

Same idea as optimistic concurrency, except the fence is
permanent; an OCC abort can retry.

Names: Chubby **sequencer**
([88](distributed-systems-references.md)); Kafka **epoch**;
Paxos **ballot**; Raft **term**. ZooKeeper: `zxid` or
`cversion` ([85](distributed-systems-references.md)). etcd:
revision plus lease id
([89](distributed-systems-references.md)). Hazelcast
`FencedLock` ([90](distributed-systems-references.md)).

Storage must be able to test the token — or support a
conditional write (S3 conditional writes, Azure conditional
headers, GCS preconditions): succeed only if the object has
not changed since this client last read it.

### Several replicas

If you write one store that already has conditional writes,
the lock service is partly redundant
([91](distributed-systems-references.md),
[92](distributed-systems-references.md)); the lease can live
on that store
([93](distributed-systems-references.md)). A token still
helps when you write **several** services or replicas.

[Leaderless](leaderless-replication.md) plus
[LWW](conflict-resolution.md): put the fencing token in the
high bits of the timestamp (Figure 9-7). Every timestamp from
token 34 is greater than every timestamp from 33, even if the
zombie writes later. Client 2 reaches a quorum; replica 3 is
down; the zombie may write replica 3. A later quorum read
prefers 34…; read repair / anti-entropy overwrites 33….

It is not safe to assume only one holder. With tokens, the
zombie and the delayed packet do not have to be harmless
*by luck*.

**Architect takeaway:** “I hold the lock” is a local belief.
Make the *storage* (or every replica) reject a stale token.
STONITH is not a fence. Conditional writes on one object
store can replace a lock service; several stores need a
shared increasing token. A node that can mint a fake token
is a [Byzantine](byzantine-faults.md) problem — a different
model.
