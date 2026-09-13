---
type: analysis
title: 'MDW trade-offs'
description: 'The hybrid buys range, scale, and self-service BI. It pays in copies, pipelines, skills, and vendor gravity. Without governance the extra store becomes another silo.'
tags: [data-intensive-design, mdw, trade-offs, self-service-bi, vendor-lock-in]
---

# MDW trade-offs

**See also:** [chapter overview](mdw-overview.md) · [data journey](mdw-data-journey.md) · [lake and RDW roles](mdw-lake-and-rdw.md) · [data fabric trade-offs](data-fabric-tradeoffs.md) · [scalability](scalability.md) · [law and society](law-and-society.md) · [cloud vs self-hosting](cloud-vs-self-hosting.md)

The MDW is sold as “structure plus flexibility.” The bill is extra
copies and an integration problem you now own.

## What you buy

| Claim | What it actually is |
|---|---|
| Multiple sources | Structured and unstructured land in one estate. The lake takes variety; the RDW takes the slice that must serve. |
| Scalability | The lake side scales with object storage. The RDW side scales with the warehouse product — SMP until it does not; MPP after. |
| Real-time analysis | Possible when ingest is a stream and the serving path is kept warm. Not automatic from “we have a lake.” |
| Query performance | The RDW (and especially a star) is the fast path. The lake is the flexible path. Do not advertise lake latency as warehouse latency. |
| Modeling flexibility | SQL on the warehouse; files and engines of choice on the lake. Two models, not one that does both well. |
| Security | Leading warehouse products have mature row/column controls. The lake has different knobs. “The MDW is secure” means you designed both. |

The operational payoff that is easy to under-count: as data is
copied lake → RDW it is reshaped until a business user can drag
fields without writing a join. That is **self-service BI**. IT
pays up front so it stops being the bottleneck on every report.
That is a staffing architecture, not only a storage one.

## What you pay

| Cost | Why it shows up |
|---|---|
| Complexity | Two stores, two security models, hybrid ops. The integration *is* the architecture. |
| Money | Setup, keep-the-lights-on, and **duplicate storage plus the pipelines that keep the copies honest**. Small teams feel this first. |
| Skills | Lake compute, warehouse modeling, and the glue. Hire or train; the product UI does not remove the gap. |
| Silos | A second store without governance is another place data goes to hide. The hybrid can fragment the estate it was meant to unify. |
| Compliance | Diverse types and sources widen the surface
([law and society](law-and-society.md)). Lineage has to span both hops. |
| Vendor gravity | A cloud MDW is often one vendor’s warehouse + that vendor’s lake. Lock-in is a
[build-vs-buy](cloud-vs-self-hosting.md) outcome, not an accident. |

## How to read the brochure

“Integration, scale, real-time, security” are true of a *well-run*
MDW. They are not properties of buying the SKU. The failure mode
is the mid-2010s lake-only story in reverse: two platforms, no
shared model, and a report that still needs an engineer.

**Architect takeaway:** budget the copy. Storage is cheap; the
pipeline, the skills, and the governance of two serving surfaces
are not. Self-service BI is the reason to do the up-front model.
If you will not do that work, the RDW half is an expensive cache
of the lake.
