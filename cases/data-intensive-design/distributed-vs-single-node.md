---
type: analysis
title: 'Distributed versus single-node systems'
description: 'Distribute for inherent multi-user, HA, scale, latency, elasticity, or residency — not by default. A single node is often simpler and cheaper.'
tags: [data-intensive-design, trade-offs, distributed-systems, microservices, serverless]
---

# Distributed versus single-node systems

**See also:** [chapter overview](overview.md) · [cloud vs self-hosting](cloud-vs-self-hosting.md) · [operational vs analytical](operational-vs-analytical.md) · [replication](replication-overview.md) · [sharding](sharding-overview.md) · [partial failure](distributed-systems-overview.md) · [references](references.md)

A system that involves several machines communicating via a network is a
**distributed system**. Each participating process is a **node**. Reasons you
might want this:

**Inherent distribution.** If an application involves two or more interacting
users, each using their own device, the system is unavoidably distributed: the
communication between the devices will have to occur via a network.

**Requests between cloud services.** If data is stored in one service but
processed in another, that data must be transferred over the network.
Cloud-native systems and microservices are therefore distributed.

**Fault tolerance / high availability.** If the application needs to continue
working even if one machine (or several machines, or the network, or an entire
datacenter) goes down, multiple machines give you redundancy. When one fails,
another can take over.

**Scalability.** If data volume or computing requirements grow bigger than a
single machine can handle, you can potentially spread the load across multiple
machines.

**Latency.** If you have users around the world, you might want servers in
various regions so each user can be served from a geographically close server,
avoiding a round trip halfway around the world.

**Elasticity.** If the application is busy at some times and idle at others, a
cloud deployment can scale up or down so you pay only for resources you are
actively using. This is more difficult on a single machine, which needs to be
provisioned for maximum load even when barely used.

**Specialized hardware.** Different parts of the system can take advantage of
different hardware. An object store may use machines with many disks but few
CPUs; a data analysis system may use machines with lots of CPU and memory but
no disks; a machine learning system may use GPUs (much more efficient than CPUs
for training deep neural networks).

**Legal compliance.** Some countries have **data residency** laws that require
data about people in their jurisdiction to be stored and processed
geographically within that country ([40](references.md)). Scope varies — in
some cases only medical or financial data; in others broader. A service with
users in several such jurisdictions will have to distribute data across servers
in several locations.

**Sustainability.** If you have flexibility on where and when to run jobs, you
might run them at a time and in a place where plenty of renewable electricity
is available, and avoid running them when the power grid is under strain. This
can reduce carbon emissions and take advantage of cheap power
([41](references.md), [42](references.md)).

These reasons apply both to services you write yourself and to off-the-shelf
software such as databases.

## Problems with distributed systems

Every request and API call that traverses the network needs to deal with the
possibility of failure. The network may be interrupted, or the service may be
overloaded or crash, and any request may time out without a response. In that
case we don’t know whether the service received the request, and simply
retrying it might not be safe.

Although datacenter networks are fast, a call to another service is still
vastly slower than calling a function in the same process ([43](references.md)).
When operating on large volumes of data, rather than transferring the data from
storage to a separate machine that processes it, it can be faster to **bring
the computation to the machine that already has the data** ([44](references.md)).
More nodes are not always faster; in some cases a simple single-threaded
program on one computer can perform significantly better than a cluster with
over 100 CPU cores ([45](references.md)).

Troubleshooting a distributed system is often difficult — if the system is
slow, where does the problem lie? Techniques for diagnosing problems are
developed under **observability** ([46](references.md), [47](references.md)):
collecting data about execution and querying it for both high-level metrics and
individual events. Tracing tools such as OpenTelemetry, Zipkin, and Jaeger
track which client called which server for which operation and how long each
call took ([48](references.md)).

Databases provide various mechanisms for ensuring data consistency. When each
service has its own database, maintaining consistency **across** those services
becomes the application’s problem. **Distributed transactions** are a possible
technique, but they are rarely used in a microservices context because they run
counter to making services independent from each other, and many databases
don’t support them ([49](references.md)).

For all these reasons, performing a task on a single machine is often much
simpler and cheaper than setting up a distributed system ([22](references.md),
[45](references.md), [50](references.md)). CPUs, memory, and disks have grown
larger, faster, and more reliable. Combined with single-node databases such as
DuckDB, SQLite, and KùzuDB, many workloads can now run on a single node.

## Microservices and serverless

The most common way of distributing a system across multiple machines is to
divide them into clients and servers and let the clients make requests to the
servers. Most commonly HTTP is used. The same process may be both a server
(handling incoming requests) and a client (making outbound requests).

This way of building applications has traditionally been called a
**service-oriented architecture (SOA)**; more recently the idea has been
refined into a **microservices architecture** ([51](references.md),
[52](references.md)). In a microservices architecture:

- A service has one well-defined purpose (e.g. S3: file storage).
- Each service exposes an API that clients call via the network.
- Each service has one team responsible for its maintenance.

A complex application is decomposed into multiple interacting services, each
managed by a separate team. Cloud-native systems make heavy use of this
decomposition; on-premises systems can use a service-oriented approach too.

Advantages of splitting into services:

- Each service can be updated independently, reducing coordination among teams.
- Each service can be assigned the hardware resources it needs.
- Hiding implementation details behind an API means service owners can change
  the implementation without affecting clients.

In terms of data storage, it is common for **each service to have its own
databases** and not to share databases between services. Sharing a database
would effectively make the entire database structure part of the service’s API,
and then that structure would be difficult to change. Shared databases could
also cause one service’s queries to negatively impact the performance of other
services.

On the other hand, many services breed complexity:

- Testing a service during development can require running all the services it
  depends on.
- Each service requires infrastructure for deploying releases, adjusting
  hardware to match load, collecting logs, monitoring health, and alerting
  on-call. Orchestration frameworks such as Kubernetes have become a popular
  way of deploying services because they provide a foundation for this
  infrastructure.
- Microservice APIs can be challenging to evolve. Clients expect certain
  fields. Adding or removing fields can cause clients to fail — often not
  discovered until late, when the updated API is deployed to staging or
  production. API description standards such as OpenAPI and gRPC help manage
  the client/server relationship.

Microservices are primarily a **technical solution to a people problem**:
allowing different teams to make progress independently without coordinating.
This is valuable in a large company. In a small company with fewer teams, using
microservices is likely unnecessary overhead; implementing the application in
the simplest way possible is preferable ([51](references.md)).

**Serverless**, or **function as a service (FaaS)**, is another approach to
deploying services, in which infrastructure management is outsourced to a cloud
vendor ([32](references.md)). With VMs you explicitly choose when to start or
shut down an instance; with serverless, the provider automatically allocates
and frees hardware based on incoming requests ([53](references.md)). Just as
cloud storage replaced capacity planning with metered billing, serverless
brings metered billing to code execution: you pay only for the time application
code is running.

To offer those benefits, many serverless providers impose a time limit on
function execution and limit runtime environments, and services might suffer
from slow start times when a function is first invoked. The term “serverless”
can also be misleading: each execution still runs on a server, but subsequent
executions might run on a different one. Infrastructure services such as
BigQuery and various Kafka offerings have adopted “serverless” terminology to
signal that they autoscale and bill by usage rather than machine instances.

## Cloud computing versus supercomputing

Cloud computing is not the only way of building large-scale computing systems;
an alternative is **high-performance computing (HPC)**, also known as
supercomputing. Although there are overlaps, HPC often has different priorities
and uses different techniques:

- Supercomputers are typically used for computationally intensive scientific
  tasks: weather forecasting, climate modeling, molecular dynamics, complex
  optimization, partial differential equations. Cloud computing tends to be
  used for online services and business data systems that need to serve user
  requests with high availability.
- A supercomputer typically runs large batch jobs that checkpoint state to
  disk from time to time. If a node fails, a common solution is to stop the
  entire cluster workload, repair the faulty node, and restart from the last
  checkpoint ([54](references.md), [55](references.md)). With cloud services,
  stopping the entire cluster is usually not desirable.
- Supercomputer nodes typically communicate through shared memory and RDMA,
  which support high bandwidth and low latency but assume a high level of
  trust among users ([56](references.md)). In cloud computing, the network and
  machines are often shared by mutually untrusting organizations, requiring
  stronger security: resource isolation (VMs), encryption, and authentication.
- Cloud datacenter networks are often based on IP and Ethernet, arranged in
  Clos topologies to provide high bisection bandwidth ([54](references.md),
  [57](references.md)). Supercomputers often use specialized topologies such as
  multidimensional meshes and toruses ([58](references.md)), which yield better
  performance for HPC workloads with known communication patterns.
- Cloud computing allows nodes to be distributed across multiple geographic
  regions; supercomputers generally assume all their nodes are close together.

Large-scale analytical systems sometimes share characteristics with
supercomputing, which is why these techniques are worth knowing if you work in
that area. These notes are mostly concerned with services that need to be
continually available.

**Architect takeaway:** distribute when the problem is inherently distributed
(users, regions, residency, HA, scale). Do not distribute to look modern. Each
network hop is a failure domain, a latency tax, and — once each service owns
its own database — a consistency problem the application now owns.
