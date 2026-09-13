---
type: overview
title: 'Defining nonfunctional requirements'
description: 'Functional requirements say what the app does. NFRs — performance, reliability, scalability, maintainability — decide whether it is usable, and they need numbers.'
tags: [data-intensive-design, nfr, overview]
---

# Defining nonfunctional requirements

> The Internet was done so well that most people think of it as a natural
> resource like the Pacific Ocean, rather than something that was man-made.
> When was the last time a technology with a scale like that was so
> error-free?
>
> — Alan Kay, interview with *Dr. Dobb’s Journal* (2012)

If you are building an application, you will be driven by a list of
requirements. At the top of the list is most likely the **functionality** the
application must offer: what screens and buttons you need, and what each
operation is supposed to do. These are **functional requirements**.

You also have **nonfunctional requirements**: the app should be fast, reliable,
secure, legally compliant, and easy to maintain. These might not be written
down, because they seem obvious, but they are just as important as
functionality. An app that is unbearably slow or unreliable might as well not
exist.

Many NFRs, such as security, fall outside these notes. This chapter covers four
that shape data-system architecture, and the terminology used in later
chapters. Abstract definitions are dry, so the chapter opens with a worked
example: [home timelines on a social network](home-timeline-case-study.md).

Prior chapter: [trade-offs in data systems architecture](overview.md).

## Topic map

| NFR | The question | Concept |
|---|---|---|
| Case study | What does scale actually look like on a timeline? | [Social network home timelines](home-timeline-case-study.md) |
| Performance | How do we measure “fast”? | [Describing performance](performance.md) |
| Reliability | What does “keep working when things go wrong” mean? | [Reliability and fault tolerance](reliability.md) |
| Scalability | How do we add capacity as load grows? | [Scalability](scalability.md) |
| Maintainability | How do we keep the system cheap to run and change? | [Maintainability](maintainability.md) |

Citations for this chapter live in [NFR references](nfr-references.md). Chapter 1
citations stay in [trade-off references](references.md).

## Summary

- The timeline case study shows why average-case design fails at the tails
  (heavy follow graphs, celebrity fan-out) and why materializing a derived
  timeline trades write amplification for read speed.
- **Performance** is not one number. Throughput sets capacity and cost;
  response time is what users feel. Report percentiles, not just the mean.
  Queueing links the two: as throughput approaches capacity, response time
  explodes. Overload can become a metastable failure.
- **Reliability** is continuing to meet the SLO when parts go wrong. A
  **fault** is a part failing; a **failure** is the service missing its SLO.
  Hardware faults are mostly independent; software faults are often correlated;
  humans and incentives are part of the sociotechnical system.
- **Scalability** is not a yes/no label. Name the load parameters, then ask
  what happens if they grow. Shared-nothing can scale out; it also buys you a
  distributed system. Do not design more than about one order of magnitude
  ahead.
- **Maintainability** is most of the lifetime cost: operability, simplicity,
  evolvability. Minimize irreversibility.

**Architect takeaway:** write NFRs as measurable objectives (load, percentiles,
fault model, who operates it), not as adjectives. “Fast and reliable” is not a
requirement.

Next chapter: [data models and query languages](data-models-overview.md) —
relational vs document, graphs, event sourcing, and DataFrames.
