---
type: analysis
title: 'Reliability and fault tolerance'
description: 'Reliability is continuing to meet the SLO when parts go wrong. A fault is a part; a failure is the service. Hardware is mostly independent; software faults correlate.'
tags: [data-intensive-design, nfr, reliability, fault-tolerance, chaos]
---

# Reliability and fault tolerance

**See also:** [NFR overview](nfr-overview.md) · [home timelines](home-timeline-case-study.md) · [distributed vs single-node](distributed-vs-single-node.md) · [replication](replication-overview.md) · [sharding](sharding-overview.md) · [ACID](acid.md) · [partial failure](distributed-systems-overview.md) · [fault injection](system-models.md#fault-injection) · [NFR references](nfr-references.md)

Typical expectations for software to “work correctly”:

- The application performs the function the user expected.
- It can tolerate the user making mistakes or using it in unexpected ways.
- Performance is good enough for the required use case, under expected load
  and data volume.
- The system prevents unauthorized access and abuse.

**Reliability** is, roughly, continuing to work correctly even when things go
wrong. To be precise about “things going wrong,” distinguish **faults** from
**failures** ([37](nfr-references.md), [38](nfr-references.md),
[39](nfr-references.md)):

| Term | Meaning |
|---|---|
| **Fault** | A particular *part* of a system stops working correctly — one hard drive, one machine crash, one dependency outage |
| **Failure** | The system *as a whole* stops providing the required service — it does not meet the [SLO](performance.md#use-of-response-time-metrics) |

The distinction is the same event at different levels. If a hard drive stops
working, the drive has failed. If the system is only that one drive, the
service has also failed. If the system has multiple drives and a copy of the
data elsewhere, the drive failure is only a **fault** from the bigger system’s
point of view, and the bigger system might tolerate it.

## Fault tolerance

A system is **fault-tolerant** if it continues providing the required service
despite certain faults. If it cannot tolerate a certain part becoming faulty,
that part is a **single point of failure (SPOF)**: a fault there escalates to
failure of the whole system.

In the [timeline case study](home-timeline-case-study.md), a machine involved
in fan-out might crash while updating materialized timelines. Tolerance means
another machine can take over without missing posts and without duplicating
them (**exactly-once semantics** — a later chapter).

Fault tolerance is always limited to a **certain number of certain types** of
faults: at most two disks at once, or one of three nodes. It does not make
sense to tolerate *any* number of faults; if all nodes crash, nothing can be
done.

Counterintuitively, it can make sense to **increase** the rate of faults by
triggering them deliberately — randomly killing processes without warning.
That is **fault injection**. Many critical bugs are poor error handling
([40](nfr-references.md)); deliberate faults keep the tolerance machinery
exercised. **Chaos engineering** is the discipline of gaining confidence in
fault-tolerance mechanisms through such experiments ([41](nfr-references.md)).

We generally prefer tolerating faults over preventing them, except where no
cure exists. Security is the usual example: if an attacker has already
exfiltrated sensitive data, that event cannot be undone. These notes mostly
cover faults that can be cured.

## Hardware and software faults

Hardware faults come to mind first. Book-cited rates (not measurements from
this workspace):

- About 2%–5% of magnetic hard drives fail per year; in a cluster of 10,000
  disks, expect on average one disk failure per day. Disks are getting more
  reliable, but rates remain significant.
- About 0.5%–1% of SSDs fail per year. Small bit errors are corrected
  automatically; uncorrectable errors occur about once per year per drive even
  when fairly new — a higher rate than magnetic drives.
- Power supplies, RAID controllers, and memory modules also fail, less often
  than drives.
- About 1 in 1,000 machines has a CPU core that occasionally computes the
  wrong result (manufacturing defects). Sometimes that crashes; sometimes the
  program returns the wrong result.
- RAM can be corrupted by cosmic rays or physical defects. Even with ECC, more
  than 1% of machines encounter an uncorrectable error in a given year,
  typically crashing the machine. Some pathological access patterns flip bits
  with high probability.
- An entire datacenter might become unavailable (power, network
  misconfiguration) or be destroyed (fire, flood, earthquake). A solar storm
  can damage power grids and undersea cables. Rare, but catastrophic if the
  service cannot tolerate losing a datacenter.

On a small system you often need not worry, as long as faulty hardware is easy
to replace. At large scale, hardware faults are **part of normal operation**.

### Tolerating hardware faults through redundancy

The first response is redundancy of individual components: RAID across disks,
dual power supplies, hot-swappable CPUs, batteries and diesel for the
datacenter. That can keep a *machine* running for years.

Redundancy is most effective when component faults are **independent**.
Experience shows significant correlations: a whole rack or datacenter still
goes unavailable more often than we would like.

Hardware redundancy increases single-machine uptime. A
[distributed system](distributed-vs-single-node.md) can tolerate losing a whole
datacenter. Cloud systems therefore focus less on making individual machines
reliable and more on making **services** highly available by tolerating faulty
nodes in software. **Availability zones** identify which resources are
physically co-located — more likely to fail together than geographically
separated resources.

The techniques in later chapters tolerate loss of machines, racks, or AZs,
generally by letting a machine in one datacenter take over when another fails
or becomes unreachable.

Systems that can lose entire machines also have an operational advantage: a
single-server system needs planned downtime to reboot for OS patches; a
multi-node system can patch with a **rolling upgrade** (one node at a time)
without affecting users.

### Software faults

Hardware failures can be weakly correlated but are still mostly independent: if
one disk fails, others in the same machine will likely be fine for a while.
**Software faults are often highly correlated**, because many nodes run the
same software and thus the same bugs. They are harder to anticipate and cause
many more system failures than uncorrelated hardware faults. Examples:

- A bug that fails every node at once in particular circumstances (leap-second
  hangs; SSD firmware that dies after exactly 32,768 hours).
- A runaway process that exhausts a shared limited resource (CPU, memory,
  disk, network, threads).
- A dependency that slows, hangs, or returns corrupted responses.
- Interaction between systems that produces emergent behavior absent from
  isolated tests.
- **Cascading failures**, where one component overloads the next.

The bugs often lie dormant until an unusual set of circumstances reveals an
assumption about the environment that usually holds and then stops holding.

There is no quick fix. Small things help: think about assumptions and
interactions; test thoroughly; isolate processes; allow crash-and-restart;
avoid feedback loops such as [retry storms](performance.md#when-an-overloaded-system-wont-recover);
measure, monitor, and analyze production behavior.

Citations [42]–[71] in the source chapter are not in the dump we have; see
[NFR references](nfr-references.md).

## Humans and reliability

Humans design, build, and operate these systems. Unlike machines, they do not
just follow rules — creativity and adaptation are a strength, and also a
source of mistakes. One study of large internet services found **configuration
changes by operators** were the leading cause of outages; hardware (servers or
network) played a role in only 10%–25% of cases.

It is tempting to label this “human error” and tighten procedures. Blaming
people is counterproductive. What we call human error is usually a **symptom**
of a problem in the sociotechnical system in which people are trying to do
their jobs. Complex systems also have emergent behavior from unexpected
interactions.

Technical measures help: thorough testing (handwritten and property tests on
random inputs), rollback for config, gradual rollouts, monitoring and
[observability](distributed-vs-single-node.md#problems-with-distributed-systems),
interfaces that make the right thing easy. They all cost time and money.
Organizations often prioritize revenue-generating features over resilience.
Then, when a preventable mistake occurs, blaming the person who made it misses
the organization’s priorities.

**Blameless postmortems:** after an incident, people share full details without
fear of punishment, so others can learn. That may surface a need to change
priorities, invest in neglected areas, change incentives, or raise a systemic
issue to management.

Be suspicious of simplistic answers. “Bob should have been more careful” is
not productive; neither is “rewrite the backend in Haskell.” Learn how the
sociotechnical system actually works from the people who run it, and improve
it from that feedback.

## How important is reliability?

Reliability is not only for nuclear plants and air traffic control. Bugs in
business applications lose productivity (and create legal risk if figures are
wrong). Ecommerce outages cost revenue and reputation.

In many applications a few minutes or even hours of outage is tolerable;
**permanent data loss or corruption** would be catastrophic. A parent storing
all pictures of their children in your photo app: how would they feel if that
database corrupted? Would they know how to restore from backup?

The Post Office Horizon scandal is a reminder that unreliable software can
harm people: hundreds of UK sub-postmasters were convicted of theft or fraud
because accounting software showed a shortfall; many shortfalls were bugs.
English law assumed computers operate correctly unless shown otherwise.
Software engineers may laugh at bug-free software; that is little solace to
people wrongly imprisoned, bankrupted, or worse.

Sometimes we sacrifice reliability to reduce development cost (a prototype for
an unproven market). Be conscious of when you are cutting corners, and of the
consequences.

**Architect takeaway:** write the fault model. Name what you will tolerate
(disk, node, AZ) and what you will not (correlated software bugs, silent
corruption, human config mistakes). Fault injection tests the former;
blameless postmortems and rollback test the latter. Reliability you cannot
restore (exfiltration, unrecoverable photos) must be prevented, not tolerated.
