---
type: analysis
title: 'Scalability'
description: 'Scalability is not a yes/no label. Name the load parameters, then ask what happens if they grow. Shared-nothing scales out and buys you a distributed system.'
tags: [data-intensive-design, nfr, scalability, shared-nothing, load]
---

# Scalability

**See also:** [NFR overview](nfr-overview.md) · [home timelines](home-timeline-case-study.md) · [performance](performance.md) · [distributed vs single-node](distributed-vs-single-node.md) · [cloud vs self-hosting](cloud-vs-self-hosting.md#separation-of-storage-and-compute) · [replication](replication-overview.md) · [sharding](sharding-overview.md) · [NFR references](nfr-references.md)

Even if a system is reliable today, it may not stay that way. One common
reason is **increased load**: 10,000 concurrent users become 100,000, or 1
million records become 10 million.

**Scalability** is the ability to cope with increased load. Comments like
“you’re not Google — just use a relational database” are sometimes right and
sometimes not; it depends on the application.

If you are building a new product with few users, the overriding goal is
usually to keep the system **simple and flexible** so you can change features
as you learn. Worrying about hypothetical future scale is often wasted effort
(premature optimization) and can lock you into an inflexible design.

Scalability is not a one-dimensional label. It is meaningless to say “X is
scalable.” Discussing it means questions like:

- If the system grows in a particular way, what are our options for coping?
- How can we add computing resources to handle the additional load?
- Based on current growth projections, when will we hit the limits of the
  current architecture?

If the application becomes popular, you will learn where the bottlenecks are
and along which dimensions you need to scale. *Then* it is time to apply
scalability techniques.

## Understanding load

First, understand **current load**. Only then can you ask “what if it
doubles?” Often this is a [throughput](performance.md) measure: requests per
second, gigabytes of new data per day, checkouts per hour. Sometimes you care
about the peak of a variable quantity, such as simultaneously online users in
the [timeline case study](home-timeline-case-study.md).

Other statistical characteristics of the load affect access patterns:

- Read/write ratio
- Cache hit rate
- Data items per user (followers, in the case study)

Perhaps the average case matters; perhaps the bottleneck is a small number of
extreme cases. It depends on the application.

Once you understand load, investigate growth in two ways:

1. Increase load, **keep resources unchanged** — how does performance change?
2. Increase load, **add resources** to keep performance unchanged — how much
   do you need to add?

Usually the goal is to keep performance within the [SLA](performance.md#use-of-response-time-metrics)
while minimizing cost. More compute costs more. Hardware price/performance
changes over time.

If doubling resources lets you handle twice the load at the same performance,
you have **linear scalability** — considered a good thing. Occasionally you
can handle twice the load with *less* than double the resources (economies of
scale, better peak distribution). Much more likely, cost grows **faster than
linearly**. Example: with a lot of data, a single write may involve more work
than with a small dataset, even if the request size is the same.

## Shared-memory, shared-disk, and shared-nothing

The simplest way to add hardware is to move to a more powerful machine. Individual
CPU cores are no longer getting significantly faster, but you can buy (or rent)
more cores, RAM, and disk. That is **vertical scaling** or **scaling up**.

Parallelism on one machine uses multiple processes or threads. Threads in the
same process share RAM: a **shared-memory architecture**. Cost grows faster
than linearly — a high-end machine with twice the resources typically costs
*more* than twice as much, and bottlenecks mean it is unlikely to handle twice
the load.

**Shared-disk:** several machines with independent CPUs and RAM, data on an
array of disks shared over a fast network (NAS or SAN). Traditional for
on-premises data warehousing. Contention and locking limit scalability.

**Shared-nothing** (also **horizontal scaling** or **scaling out**): a
distributed system, each node with its own CPUs, RAM, and disks. Coordination
is at the software level, over a conventional network.

Advantages of shared-nothing: potential to scale linearly; use whatever
hardware has the best price/performance (especially in the cloud); adjust
resources as load changes; greater fault tolerance across datacenters and
regions. Downsides: explicit **sharding**, and all the complexity of
[distributed systems](distributed-vs-single-node.md).

Some cloud-native databases use separate services for storage and transaction
execution ([separation of storage and compute](cloud-vs-self-hosting.md#separation-of-storage-and-compute)),
with multiple compute nodes sharing a storage service. That resembles
shared-disk, but avoids older scalability problems by offering a specialized
API rather than a filesystem (NAS) or block device (SAN).

## Principles for scalability

Architecture at large scale is usually **highly specific to the application**.
There is no generic one-size-fits-all scalable architecture (“magic scaling
sauce”). A system for 100,000 requests/second of 1 kB looks very different
from one for 3 requests/minute of 2 GB — same data throughput (100 MB/s),
different design.

An architecture that is right for one load level is unlikely to cope with
**10×** that load. On a fast-growing service you will probably rethink
architecture on every order-of-magnitude increase. It is usually not worth
planning more than **one order of magnitude** ahead.

A good general principle: break the system into smaller components that can
operate largely independently. That is the idea behind
[microservices](distributed-vs-single-node.md#microservices-and-serverless),
sharding, stream processing, and shared-nothing. The hard part is where to
draw the line.

Another principle: **do not make things more complicated than necessary**. If
a single-machine database will do, it is probably preferable to a distributed
setup. Autoscaling is cool; if load is fairly predictable, a manually scaled
system may have fewer operational surprises. Five services is simpler than
fifty. Good architectures mix approaches pragmatically.

**Architect takeaway:** name the load (which metric, average vs tail) before
you name the scale-out trick. Shared-nothing is a distributed system, not a
free linear multiplier. Design for the next 10×, not the imaginary 1000×.
