---
type: analysis
title: 'Request routing'
description: 'A key lives on one shard. Find the node: any replica forwards, a routing tier maps, or the client already knows. The map needs consensus or gossip; cutover still drops in-flight requests.'
tags: [data-intensive-design, sharding, request-routing, service-discovery, consensus]
---

# Request routing

**See also:** [chapter overview](sharding-overview.md) · [service discovery](rest-rpc-dataflow.md#load-balancers-service-discovery-and-service-meshes) · [leader failover](single-leader-replication.md#handling-node-outages) · [quorum limits](leaderless-replication.md#limitations-of-quorum-consistency) · [rebalancing](rebalancing.md) · [references](sharding-references.md)

You have sharded the dataset and you can
[rebalance](rebalancing.md). Remaining question: for a given key,
which IP and port?

That is **request routing**. It is close to
[service discovery](rest-rpc-dataflow.md#load-balancers-service-discovery-and-service-meshes).
The difference: application instances are usually stateless — a load
balancer may pick any of them. A sharded database can handle a key
only on a node that is a replica of the shard that owns that key.

Routing must know key → shard and shard → node. Three approaches
(Figure 7-7):

| Approach | Path | Role of the node |
|---|---|---|
| **Any node** | Client hits any replica (often via round-robin). | If it owns the shard, serve; else forward, wait, reply. |
| **Routing tier** | All clients hit a proxy first. | The tier is a shard-aware load balancer; it does not serve data. |
| **Sharding-aware client** | Client connects to the right node. | No intermediary. |

## The hard questions

1. **Who assigns shards to nodes?** A single coordinator is simple.
   Then: how is it fault-tolerant? If the role fails over, how do you
   prevent [split-brain](single-leader-replication.md#handling-node-outages)
   — two coordinators with contradictory maps?
2. **How does the router learn the map?** The router may be a node,
   the routing tier, or the client.
3. **Cutover.** While a shard moves, the new node has taken over but
   requests to the old node are still in flight. What happens to
   those?

## Coordination service

Many systems keep the assignment in ZooKeeper or etcd (Figure 7-8).
Consensus (a later chapter) gives fault tolerance and split-brain
protection. Each node registers. ZooKeeper holds the authoritative
shard → node map. The routing tier or a sharding-aware client
subscribes. Ownership change or node add/remove notifies the router.

Examples: HBase and SolrCloud use ZooKeeper; Kubernetes uses etcd
for instance placement. MongoDB is similar with its own config
servers and `mongos` as the routing tier. Kafka, YugabyteDB, TiDB,
and ScyllaDB ([28](sharding-references.md)) use built-in Raft for
this coordination.

**Gossip** is the other bet. Riak spreads cluster-state changes
among nodes. Weaker than consensus: split-brain is possible —
different parts of the cluster disagree which node owns a shard.
[Leaderless](leaderless-replication.md#limitations-of-quorum-consistency)
stores can tolerate that because they already make weak consistency
guarantees.

Clients still need IPs for the routing tier or a random node. Those
change slower than shard assignment, so DNS is often enough.

This section is about finding the shard for **one key** — the OLTP
case. Analytical databases shard too, but a query usually aggregates
and joins across many shards in parallel (a later chapter).

**Architect takeaway:** the routing map is a consensus problem
whether you notice it or not. A smart client, a proxy, or
forwarding nodes are three places to put the same map. Gossip is
cheaper and admits split-brain; use it only if the store already
lives with that.
