---
type: analysis
title: 'Rebalancing'
description: 'Splitting and moving shards can be automatic, suggested-then-committed, or manual. Automation plus false failure detection can cascade. A human in the loop is slower and safer.'
tags: [data-intensive-design, sharding, rebalancing, operations, cascading-failure]
---

# Rebalancing

**See also:** [chapter overview](sharding-overview.md) · [key-range sharding](key-range-sharding.md) · [hash sharding](hash-sharding.md) · [request routing](request-routing.md) · [reliability](reliability.md) · [references](sharding-references.md)

Does splitting shards and moving them between nodes happen
automatically, or does a human decide?

Some systems split and move with no human in the loop. Others leave
sharding to an administrator. Middle ground: Couchbase and Riak
**suggest** an assignment and wait for an administrator to commit it.

## Why automate

Less day-to-day operational work. Some systems autoscale with
workload. Cloud databases such as DynamoDB are promoted as adding
and removing shards within minutes of a load change
([17](sharding-references.md), [27](sharding-references.md)).

## Why that is dangerous

Rebalancing is expensive: reroute requests, move a large amount of
data. Done carelessly, it overloads the network or the nodes and
hurts other traffic. Writes must continue during the move. Near
maximum write throughput, the split may not keep up with incoming
writes ([27](sharding-references.md)).

Automation plus **automatic failure detection** is the sharp edge.
One node is overloaded and slow. Others declare it dead and
rebalance away from it. That puts more load on the remaining nodes
and the network. Other nodes look dead. Cascading failure.

A human in the loop is slower than full automation and prevents
operational surprises. Manual rebalancing is also how you **preempt**
a known surge — Cyber Monday, World Cup ticket sales — instead of
reacting after the cluster is already on fire.

**Architect takeaway:** automatic rebalance is an elasticity
feature and a failure amplifier. If detection can be wrong, require
a commit step. Pre-split and pre-move for events you can name on a
calendar.
