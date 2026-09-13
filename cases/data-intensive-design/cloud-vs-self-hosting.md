---
type: analysis
title: 'Cloud versus self-hosting'
description: 'Cloud vs self-hosting is a business-priority decision: core competency in-house, routine work outsourced. Cloud native disaggregates storage from compute.'
tags: [data-intensive-design, trade-offs, cloud-native, operations]
---

# Cloud versus self-hosting

**See also:** [chapter overview](overview.md) · [distributed vs single-node](distributed-vs-single-node.md) · [MDW storage/compute split](mdw-data-journey.md#3-transformation) · [references](references.md)

With anything an organization needs to do, one of the first questions is
whether it should be done in-house or outsourced: **build or buy?**

A common rule of thumb: things that are a **core competency** or a competitive
advantage should be done in-house; things that are non-core, routine, or
commonplace should be left to a vendor ([20](references.md)). Most companies
do not fabricate their own CPUs.

With software, two important decisions are **who builds** the software and
**who deploys** it. The spectrum:

- One extreme: bespoke software that you write and run in-house (more control,
  more investment).
- The other extreme: widely used cloud services or SaaS products implemented
  and operated by an external vendor, accessed only through a web interface or
  API (less control, less investment).
- Middle ground: off-the-shelf software (open source or commercial) that you
  **self-host** — for example, downloading MySQL and installing it on a server
  you control. That could be your own hardware (**on premises**, even if the
  server is in a rented datacenter rack) or a VM in the cloud (**infrastructure
  as a service**, IaaS). Taking open source and running a modified version is
  another point on the spectrum.

A related question is how you deploy services (Kubernetes, etc.). Choice of
deployment tooling is a smaller influence on data-system architecture than the
build/buy and cloud-native questions below.

## Pros and cons of cloud services

Using a cloud service, rather than running comparable software yourself,
outsources the operation of that software to the cloud provider. Whether that
is actually cheaper and easier than self-hosting depends on your skills and the
workload.

- If you already know how to deploy and operate the systems you need, and load
  is quite predictable (machine count does not fluctuate wildly), it is often
  cheaper to buy your own machines and run the software yourself
  ([21](references.md), [22](references.md)).
- If you need a system you don’t already know how to operate, adopting a cloud
  service is often easier and quicker than learning to manage it. Hiring and
  training staff specifically to maintain the system can get very expensive.
  You still need an operations team (see [operations in the cloud era](#operations-in-the-cloud-era)), but outsourcing basic system administration can free
  that team to focus on higher-level concerns.

Outsourcing to a company that specializes in running a system can result in
better service, since the provider gains operational expertise from many
customers. On the other hand, if you run the service, you can configure and
tune it for your particular workload. A cloud service would not likely make
those customizations on your behalf.

Cloud services are particularly valuable if **load varies a lot over time**. If
you provision machines for peak load but those resources are idle most of the
time, the system becomes less cost-effective. Cloud services can make it easier
to scale computing resources up or down in response to demand.

Analytical systems often have extremely variable load. Running a large
analytical query quickly requires a lot of computing resources in parallel; once
the query completes, those resources sit idle. Predefined queries (daily
reports) can be enqueued to smooth the load, but for interactive queries, the
faster you want them to complete, the more variable the workload becomes. If
the dataset is so large that querying it quickly requires significant
computing resources, using the cloud can save money, because you can return
unused resources rather than leaving them idle. For smaller datasets, this
difference is less significant.

The biggest downside of a cloud service is that **you have no control over
it**:

- If it is lacking a feature you need, all you can do is ask the vendor; you
  generally cannot implement it yourself.
- If the service goes down, all you can do is wait for it to recover.
- If you trigger a bug or a performance problem, diagnosing it is difficult.
  Self-hosted software gives you OS metrics, debugging information, and server
  logs. A vendor-hosted service usually does not.
- If the service shuts down, becomes unacceptably expensive, or the vendor
  changes the product in a way you don’t like, you are at their mercy;
  continuing to run an old version is usually not an option, so you are forced
  to migrate ([23](references.md)). Compatible APIs mitigate this; many cloud
  services have no standard APIs, which raises switching cost (**vendor
  lock-in**).
- If the cloud provider is in another country and a political conflict arises,
  you risk being locked out due to sanctions.
- The provider needs to be trusted to keep the data secure, which can
  complicate privacy and security compliance.

Despite these risks, it has become more and more popular to build new
applications on cloud services, or to adopt a **hybrid** approach. Cloud
services will not subsume all in-house data systems. Many older systems
predate the cloud, and specialist requirements that existing cloud services
cannot meet still need in-house systems. Very latency-sensitive applications
such as high-frequency trading require full control of the hardware.

## Cloud native system architecture

Besides a different economic model (subscribing to a service instead of buying
hardware and licensing software), the rise of the cloud has also changed how
data systems are implemented. **Cloud native** describes an architecture
designed to take advantage of cloud services.

In principle, almost any software you can self-host could also be provided as a
cloud service, and managed services now exist for many popular data systems.
Systems designed from the ground up to be cloud native have been shown to have
several advantages: better performance on the same hardware, faster recovery
from failures, quickly scaling compute to match load, and supporting larger
datasets ([24](references.md), [25](references.md), [26](references.md)).

| Category | Self-hosted systems | Cloud native systems |
|---|---|---|
| Operational / OLTP | MySQL, PostgreSQL, MongoDB | AWS Aurora ([24](references.md)), Azure SQL DB Hyperscale ([25](references.md)), Google Cloud Spanner |
| Analytical / OLAP | Teradata, ClickHouse, Spark | Snowflake ([26](references.md)), Google BigQuery, Azure Synapse Analytics |

### Layering of cloud services

Many self-hosted data systems have simple system requirements: a conventional
OS, data as files on a filesystem, communication via TCP/IP. A few depend on
special hardware (GPUs for ML, RDMA network interfaces), but on the whole
self-hosted software uses generic computing resources: CPUs, RAM, a filesystem,
and an IP network.

In a cloud, this type of software can run in an IaaS environment, using one or
more VMs (instances) with a certain allocation of CPUs, memory, disk, and
network bandwidth. Compared to physical machines, cloud instances can be
provisioned faster and come in a greater variety of sizes, but otherwise they
are similar: you can run any software you like, and you administer it yourself.

The key idea of cloud-native services is not only to use OS-managed computing
resources, but to **build upon lower-level cloud services** to create
higher-level ones:

- **Object storage** (Amazon S3, Azure Blob Storage, Cloudflare R2) stores
  large files. APIs are more limited than a typical filesystem (basic file
  reads and writes), but they hide the underlying physical machines. The
  service distributes data across many machines so you don’t worry about
  running out of disk on any one machine. Even if some machines or disks fail
  entirely, no data is lost.
- Many other services are built upon object storage. Snowflake is a
  cloud-based analytical database that relies on S3 for data storage
  ([26](references.md)); some other services, in turn, build upon Snowflake.

As always with abstractions, there is no one right answer. Higher-level
abstractions tend to be more oriented toward particular use cases. If your
needs match, using the existing higher-level system will probably meet them
with much less hassle than building from lower-level systems. If no high-level
system meets your needs, building from lower-level components is the only
option.

### Separation of storage and compute

In traditional computing, disk storage is regarded as durable (once written, it
will not be lost). To tolerate the failure of an individual hard disk, **RAID**
maintains copies on several disks attached to the same machine, transparent to
applications accessing the filesystem.

In the cloud, compute instances may also have local disks, but cloud-native
systems typically treat these disks more like an **ephemeral cache** and less
like long-term storage. The local disk becomes inaccessible if the instance
fails, or if the instance is replaced with a bigger or smaller one on a
different physical machine to adapt to load.

As an alternative, cloud services offer **virtual disk storage** that can be
detached from one instance and attached to another (Amazon EBS, Azure managed
disks, persistent disks in Google Cloud). A virtual disk is not a physical
disk, but a cloud service on a separate set of machines that emulates a block
device (typically 4 KiB blocks). This makes it possible to run traditional
disk-based software in the cloud, but the emulation introduces overheads that
cloud-designed systems can avoid ([24](references.md)). Virtual disks also make
the application very sensitive to network glitches, since every I/O operation
on the virtual block device is a network call ([27](references.md)).

Cloud-native services generally avoid virtual disks and instead build on
**dedicated storage services** optimized for particular workloads. Object
storage is designed for long-term storage of fairly large files (hundreds of
kilobytes to several gigabytes). Individual database rows are typically much
smaller; cloud databases typically manage smaller values in a separate service
and store larger data blocks (containing many individual values) in an object
store ([25](references.md), [28](references.md)).

In a traditional architecture, the same computer is responsible for both
storage (disk) and computation (CPU and RAM). In cloud-native systems these
responsibilities have become **separated, or disaggregated**
([9](references.md), [26](references.md), [29](references.md),
[30](references.md)): S3 only stores files; if you want to analyze that data,
you run the analysis code somewhere outside S3. That implies transferring data
over the network (see [distributed vs single-node](distributed-vs-single-node.md)).

Cloud-native systems are often **multitenant**: rather than a separate machine
for each customer, data and computation from several customers share the same
hardware ([31](references.md)). Multitenancy can enable better hardware
utilization, easier scalability, and easier management by the provider, but it
requires careful engineering so that one customer’s activity does not affect
performance or security for others ([32](references.md)).

## Operations in the cloud era

Traditionally, the people managing an organization’s server-side data
infrastructure were known as database administrators (DBAs) or system
administrators (sysadmins). More recently, many organizations have tried to
integrate software development and operations into teams with a shared
responsibility for backend services and data infrastructure; the **DevOps**
philosophy has guided this trend. Site reliability engineers (SREs) are
Google’s implementation of this idea ([33](references.md)).

The role of operations is to ensure that services are reliably delivered to
users (configuring infrastructure, deploying applications) and to ensure a
stable production environment (monitoring and diagnosing problems). For
self-hosted systems, operations traditionally involves significant work at the
level of individual machines: capacity planning, provisioning, moving services,
installing OS patches.

Many cloud services present an API that **hides the individual machines**.
Cloud storage replaces fixed-size disks with metered billing; you store data
without planning capacity in advance and are charged based on space used. Many
cloud services remain highly available even when individual machines have
failed.

This shift from machines to services has changed the role of operations. The
high-level goal of a reliable service remains the same; the processes and tools
have evolved. DevOps/SRE places greater emphasis on:

- Automation, preferring repeatable processes over manual one-off jobs
- Ephemeral VMs and services rather than long-running servers
- Frequent application updates
- Learning from incidents
- Preserving the organization’s knowledge about the system as people come and
  go ([34](references.md))

With the rise of cloud services, a **bifurcation of roles** has occurred.
Operations teams at infrastructure companies specialize in providing a reliable
service to a large number of customers, while customers of the service spend as
little time and effort as possible on infrastructure ([35](references.md)).

Customers still require operations, but they focus on different aspects:
choosing the most appropriate service for a given task, integrating services,
and migrating from one service to another. Metered billing removes traditional
capacity planning, but it is still important to know what resources you are
using so you don’t waste money. Capacity planning becomes **financial
planning**, and performance optimization becomes **cost optimization**
([36](references.md)). Cloud services also have resource limits or quotas
(maximum concurrent processes, etc.) that you need to plan for before you run
into them ([37](references.md)).

Adopting a cloud service can be easier and quicker than provisioning your own
infrastructure, although you still have to learn the service and perhaps work
around its limitations. Integration among services becomes a particular
challenge as a growing number of vendors offer an ever broader range of
services ([38](references.md), [39](references.md)). ETL is only part of the
story; operational cloud services also need to be integrated with each other.
At present we lack standards to facilitate this, so it often involves
significant manual effort.

Other operational aspects that cannot fully be outsourced: maintaining
application and library security, managing interactions between your own
services, monitoring load, and tracking down performance degradations or
outages. The cloud is changing the role of operations; the need for operations
is as great as ever.

**Architect takeaway:** treat build-vs-buy as a business-priority decision,
not a default. The architectural move that is actually new in the cloud is
**disaggregating storage from compute** — and accepting the network, tenancy,
and lock-in that come with it.
