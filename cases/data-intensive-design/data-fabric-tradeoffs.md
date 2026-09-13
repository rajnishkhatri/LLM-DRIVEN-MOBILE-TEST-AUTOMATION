---
type: analysis
title: 'Data fabric trade-offs'
description: 'The upgrade buys variety, real-time, and governance. It pays in cost, training, and troubleshooting. Under ~10 TB or few sources, stay on the MDW.'
tags: [data-intensive-design, data-fabric, trade-offs, governance, real-time]
---
# Data fabric trade-offs

**See also:** [chapter overview](data-fabric-overview.md) · [eight extras](data-fabric-components.md) · [MDW trade-offs](mdw-tradeoffs.md) · [scalability](scalability.md) · [law and society](law-and-society.md) · [cloud vs self-hosting](cloud-vs-self-hosting.md)

The brochure says the MDW is rigid and the fabric is flexible.
The bill is the same class of cost as the
[MDW hybrid](mdw-tradeoffs.md) — copies, pipelines, skills —
plus the extras.

## What you buy

| Claim | What it actually is |
|---|---|
| Scale as types evolve | The MDW can get stiff when new shapes arrive. The fabric bet is “any size, speed, or type” — still only as true as the extras you wired. |
| Unified view | Varied sources behind one access path (API, driver, or virtual layer). Not automatic from adding a catalog. |
| Real-time | A warm path, not a property of the word “fabric.” Needed when the decision cannot wait for the batch — trading, ecommerce. |
| Governance | [Access policies](data-fabric-components.md#data-access-policies) on every request. Stronger story for multi-jurisdiction rules than an MDW that still hands out warehouse logins. |
| Future-proof | Marketing. The source says “to some extent.” New types still need a landing zone and a policy. |

## What you pay

| Cost | Why it shows up |
|---|---|
| Transition | Leaving an MDW is resource-heavy: money, training, integration. Expect early breakage. |
| Complexity | More moving parts than the hybrid. Troubleshooting gets harder; you need the skills in-house or on a contract. |
| Overbuy | Small estates with few sources and straightforward processing do not need the extras. The [MDW](mdw-overview.md) is enough — especially **under ~10 TB**. |
| Same silo risk | A catalog and an API do not unify data you never ingested or never governed. The fabric can be another place work hides. |

## How to read the brochure

“Seamless weave,” “singular view,” and “instant access” are true
of a fabric that actually added
[real-time, policies, and a catalog](data-fabric-overview.md#eight-extras)
and put every request through a mechanism that enforces them.
They are not true of an MDW that was renamed.

The source’s close: evaluate the need, the return, and the
long-term goal *before* the transition. That is the same last-
responsible-moment test as any other
[architecture decision](overview.md).

**Architect takeaway:** the upgrade is three extras you can
operate, not a new store. If the estate is small and the
questions are batch, stay on the MDW and spend the money on the
[copy and the model](mdw-tradeoffs.md). If the estate is large,
cross-border, or cannot wait for the batch, name the extras and
budget the people who will debug them.
