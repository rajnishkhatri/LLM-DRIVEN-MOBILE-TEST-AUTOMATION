---
type: analysis
title: 'Case study — Wilson & Gunkerk'
description: 'Fictitious Midwest pharma under 1 TB. They picked a cloud SMP MDW over a lake-first build. The lesson is size and growth, not a vendor.'
tags: [data-intensive-design, mdw, case-study, smp, migration]
---

# Case study — Wilson & Gunkerk

**See also:** [chapter overview](mdw-overview.md) · [trade-offs](mdw-tradeoffs.md) · [stepping stones](mdw-stepping-stones.md) · [distributed vs single-node](distributed-vs-single-node.md) · [cloud vs self-hosting](cloud-vs-self-hosting.md) · [OLTP vs OLAP](operational-vs-analytical.md)

Wilson & Gunkerk is a **fictitious** midsized pharmaceutical company
in the US Midwest. The numbers are teaching figures from the source
chapter, not measurements from this workspace.

They ran on-prem. Volume stayed **under 1 TB**. A lake or an MDW
had never been justified.

## The bind

Competition made “what happened last quarter” insufficient.
They needed market and customer behavior they could act on. The
existing system was the limit. Two options were on the table: a
fuller **data-lake** program, or a **cloud MDW**. Growth was the
uncertainty — new R&D would raise volume, but how far was unknown.

## The choice

They took a cloud MDW. The reasons in the source:

- current volume well under 1 TB; projected growth still **inside
  about 10 TB** (the same rule of thumb as the
  [overview](mdw-overview.md#why-the-hybrid-won))
- the move from on-prem warehouse to cloud warehouse was smaller
  than learning a lake-first stack
- **SMP rather than MPP** — cost matched a modest, manageable
  estate
- enough headroom that they did not have to over-buy

That is the
[small-estate exception](mdw-overview.md): do not stand up a lake
you will not use, and do not buy MPP for a box that still fits.

## What they claimed to get

The cutover is described as a few months, light disruption.

- **Analytics range.** Past descriptive-only work into predictive
  models — e.g. drug efficacy from demographics and genetic
  factors — by integrating more sources and using mining that the
  old system did not support.
- **Cost.** SMP performance without an MPP or lake-scale bill.
- **Optional later move.** Room to grow, or to add a lake, without
  paying for that option on day one.

## How to read it

The story is a size-and-growth argument, not a product review.
For a modest, warehouse-shaped estate, an MDW (even without a
serious lake) can be the honest target. The same facts flipped —
volume already past 10 TB, semi-structured load, or a user base
that is already on files — would have pointed at a
[stepping stone](mdw-stepping-stones.md) or a lakehouse, not at
SMP.

**Architect takeaway:** pick the architecture for the volume you
can defend and the skills you already have. Under a terabyte,
lake-first is often a fashion. Past the point where one SMP box
and a familiar warehouse model still work, it is a delay.
