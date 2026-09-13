---
type: analysis
title: 'Process pauses'
description: 'A thread can freeze for seconds — GC, steal time, paging, SIGSTOP — and wake sure it still holds the lease. Hard real-time can bound that; most data systems cannot afford it.'
tags: [data-intensive-design, distributed-systems, gc, leases, real-time]
---

# Process pauses

**See also:** [chapter overview](distributed-systems-overview.md) · [unreliable clocks](unreliable-clocks.md) · [quorums and fencing](quorums-and-fencing.md) · [single-leader failover](single-leader-replication.md#handling-node-outages) · [references](distributed-systems-references.md)

A [single-leader](single-leader-replication.md) shard accepts
writes only on the leader. How does the leader know it still is
the leader?

One answer is a **lease**: a lock with a timeout
([73](distributed-systems-references.md)). Only one holder.
Renew before expiry; on crash the lease lapses and someone else
takes over.

A typical request loop:

```text
while true:
    request = next()
    if lease.expiry - now() < 10s:
        lease = lease.renew()
    if lease.isValid():
        process(request)
```

Two bugs.

1. **Cross-node clocks.** Expiry was computed on another
   machine; `now()` is local. A few seconds of skew and the
   code is fiction. See
   [unreliable clocks](unreliable-clocks.md).
2. **The pause between the check and the work.** Even on a
   local monotonic clock: if the thread sleeps 15 s on
   `isValid`, the lease has expired, another node is leader,
   and this thread does not know. It processes the request
   anyway.

Is a 15-second pause realistic? Yes.

- Lock/queue contention; worse on large core counts
  ([74](distributed-systems-references.md)).
- Stop-the-world GC. Minutes, historically
  ([75](distributed-systems-references.md)); milliseconds if
  well tuned — still visible.
- VM suspend/resume and live migration; pause length follows
  dirty-memory rate
  ([76](distributed-systems-references.md)).
- Laptop lid, phone backgrounding.
- OS / hypervisor preemption (**steal time**). A long run
  queue delays the wakeup.
- Synchronous disk I/O, including lazy classloading
  ([77](distributed-systems-references.md)). I/O plus GC
  compound ([78](distributed-systems-references.md)). Network
  disks (EBS, NFS) add
  [network delay](unreliable-networks.md)
  ([31](distributed-systems-references.md)).
- Paging / thrashing. Servers often disable swap: kill the
  process rather than stall everyone.
- `SIGSTOP` / `SIGCONT` (Ctrl-Z). Accidental in ops.

A node must assume it can freeze in the middle of a function.
The rest of the world moves. Others declare it dead. It wakes
with no interrupt, no exception — only a later clock read.

Single-machine threads have mutexes, atomics, lock-free
structures. Those assume shared memory. A distributed system
has only messages on an
[unreliable network](unreliable-networks.md).

## Providing response time guarantees

Those pauses can be designed out. **Hard real-time** systems
(aircraft, rockets, airbags) must meet a deadline or the
system has failed. That is not the marketing “real-time” of
web push and stream processors.

The whole stack must play: an RTOS with reserved CPU slices;
documented worst-case library times; little or no dynamic
allocation; huge measurement. Most languages and tools do not
qualify. Cost is high; throughput often *lower* — timeliness
over utilization
([timeouts — latency versus utilization](timeouts-and-delays.md#latency-versus-utilization)).
Server-side data systems almost never buy this. They live with
pauses and clock noise.

## Limiting garbage collection

GC used to dominate pause time
([79](distributed-systems-references.md)). Modern collectors
(JVM: CMS, G1, ZGC, Epsilon, Shenandoah; Go: concurrent mark-
sweep) usually stay in milliseconds if tuned. Swift uses ARC;
Rust and Mojo track lifetimes in the type system.

Mitigations in a GC language: object pools, off-heap data;
treat a GC like a **planned outage** — drain the node, collect,
return to rotation
([80](distributed-systems-references.md),
[81](distributed-systems-references.md)); collect only
short-lived objects and restart before a full old-gen GC, one
node at a time, like a
[rolling upgrade](reliability.md)
([79](distributed-systems-references.md),
[82](distributed-systems-references.md)). These shrink the
impact; they do not prove a bound.

**Architect takeaway:** a lease check is stale the moment it
returns. Do not compare a remote expiry to `currentTimeMillis`.
Assume a pause long enough to lose the lease, then a write.
The fix is not a bigger safety margin; it is
[fencing](quorums-and-fencing.md#fencing-tokens) so the storage
layer rejects the zombie. Hard real-time is a product choice,
not a library flag.
