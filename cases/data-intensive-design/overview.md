---
type: overview
title: 'Trade-offs in data systems architecture'
description: 'Data-intensive applications make data management the primary challenge. Architecture here is a set of trade-offs, not a single right stack.'
tags: [data-intensive-design, trade-offs, overview]
---

# Trade-offs in data systems architecture

> There are no solutions; there are only trade-offs. […] But you try to get the
> best trade-off you can get, and that’s all you can hope for.
>
> — Thomas Sowell, interview with Fred Barnes (2005)

Data is central to much application development today. With web and mobile
apps, software as a service (SaaS), and cloud services, it has become normal to
store data from many different users in a shared server-based data
infrastructure. Data from user activity, business transactions, devices, and
sensors needs to be stored and made available for analysis. As users interact
with an application, they both read the data that is stored and generate more
data.

Small amounts of data, which can be stored and processed on a single machine,
are often fairly easy to deal with. As the data volume or the rate of queries
grows, it needs to be distributed across multiple machines, which introduces
many challenges. As the needs of the application become more complex, it is no
longer sufficient to store everything in one system, and it might be necessary
to combine multiple storage or processing systems that provide different
capabilities.

**Data-intensive** applications are those where data management is one of the
primary challenges in developing the application ([1](references.md)). While
in compute-intensive systems the challenge is parallelizing a very large
computation, in data-intensive applications we usually worry more about storing
and processing large data volumes, managing changes to data, ensuring
consistency in the face of failures and concurrency, and making sure services
are highly available.

Typical building blocks include databases, caches, search indexes, stream
processors, and batch processors — glued together with application code. If you
are doing exactly what the data systems were designed for, this process can be
quite easy. As the application becomes more ambitious, challenges arise: many
database systems with different characteristics, various approaches to caching
and search indexes, and the difficulty of combining tools when a single tool
cannot do the job alone.

No one approach is fundamentally better than others; everything has pros and
cons. The work is to ask the right questions so you can evaluate and compare
data systems for a particular application.

## Why these trade-offs show up

Many of the ideas here have their origin in enterprise software (the software
needs and engineering practices of large organizations), since historically
only large organizations had the large data volumes that required sophisticated
technical solutions. If your data volume is small enough, you can simply keep
it in a spreadsheet. More recently it has also become common for smaller
companies and startups to manage large data volumes and build data-intensive
systems.

One of the key challenges is that different people need to do very different
things with data. You and your team will have one set of priorities, while
another team may have entirely different goals, even though you might be
working with the same dataset. Those goals might not be explicitly articulated,
which can lead to misunderstandings and disagreement about the right approach.

## Topic map

Four contrasting pairs, plus shared terminology. Each is its own Concept so an
agent can pull one axis without the whole chapter.

| Axis | The question | Concept |
|---|---|---|
| Operational vs analytical | Who uses the data, and with what access pattern? | [Operational versus analytical systems](operational-vs-analytical.md) |
| Cloud vs self-hosting | Who builds the software, and who operates it? | [Cloud versus self-hosting](cloud-vs-self-hosting.md) |
| Distributed vs single-node | Do we actually need a network of machines? | [Distributed versus single-node systems](distributed-vs-single-node.md) |
| Law and society | Whose rights constrain the design? | [Data systems, law, and society](law-and-society.md) |

Citations for this chapter live in [References](references.md). Next:
[defining nonfunctional requirements](nfr-overview.md).

## Summary

Recognize that many questions do not have one right answer, but several
possibilities that each have pros and cons.

- Operational (OLTP) and analytical (OLAP) systems differ in access pattern,
  audience, and data layout. Data warehouses and data lakes receive feeds from
  operational systems via ETL. The distinction between a **system of record**
  and **derived data** is how you use a tool, not which tool you bought.
- Cloud vs self-hosting is a cost-and-control decision that depends on skills
  and workload shape. Cloud-native designs change the architecture itself —
  notably by separating storage and compute.
- Cloud systems are intrinsically distributed. Do not rush into distribution
  if a single machine will do.
- Architecture is determined not only by the business deploying the system,
  but also by privacy regulations that protect the people whose data is being
  processed.

**Architect takeaway:** pick the trade-off you can live with; do not hunt for
the stack that erases the trade-off.

Next chapter: [defining nonfunctional requirements](nfr-overview.md) — performance,
reliability, scalability, and maintainability as measurable objectives.
