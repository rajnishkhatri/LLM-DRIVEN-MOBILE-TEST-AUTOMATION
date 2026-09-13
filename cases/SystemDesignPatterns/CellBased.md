---
type: reference
title: 'Cell-based architecture'
description: >-
  A style, not a tactic: N complete-stack replicas as blast-radius units,
  plus a thin cell router and a control plane that places tenants. Distinguishes
  C8 pools/shuffle-shards, B2 data shards, E2 domain services, and C3 failover
  domains. Quantum FACT: one design quantum stamped N times. No library defaults.
tags: [system-design-patterns, architecture, cell-based]
---

# Cell-based architecture

**See also:** [bulkhead and isolation (C8)](Bulkhead.md) · [data partitioning (B2)](Partitioning.md) · [microservices (E2)](Microservices.md) · [failover and health checks (C3)](FailoverHealth.md) · [load balancing (C5)](LoadBalancing.md) · [API gateway (C6)](ApiGateway.md) · [load shedding (C10)](LoadShedding.md) · [scaling strategies (B1)](ScalingStrategies.md) · [monolith (E1)](Monolith.md) · [cloud application architectures](../aws/ch08.md) · [sharding and multitenancy](../data-intensive-design/sharding-multitenancy.md) · [style-selection facts](../../.cursor/skills/arch-style/references/style-selection.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/e13-cell-based-external-research.md)

Cell-based architecture is a **style**: *N* complete, independently operable copies of a workload — compute, data, and in-cell control — plus a thin shared **cell router** and a **control plane** that places tenants and provisions cells. Each cell serves a partition-key subset, owns its store, and has **known maxima** (TPS, tenants, GB) it may not exceed. Growth is **scale-out by adding cells**, not by growing one stack.

That is a different claim from the cards that share the word. [C8](Bulkhead.md) owns cells as a **1/*N* tactic** (and shuffle sharding as overlapping isolation). [B2](Partitioning.md) owns how a *record* finds its shard. [E2](Microservices.md) partitions *domain and ownership*. [C3](FailoverHealth.md) evacuates an AZ or Region. This card owns whether the *system* is a stamped fleet of blast-radius cells.

Quality attributes in play: **fault isolation** and **blast-radius control** (a poison tenant, bad deploy, or noisy neighbour stays inside its cell), **testability at full scale** (cap the cell; simulate the largest tenant that fits), and **scale under account/quotas** (add a known-size replica). The costs are redundant stacks, a specialized ops tax on *N* replicas, a shared-fate router you must keep thinner than the app, and cross-key features that become minority-or-else. AWS Well-Architected (WA) asks: 100% of customers at a 5% failure rate, or 5% of customers at 100%? Cells pick the second. That 1/*N* is still **100% for those tenants**.

[aws/ch08.md](../aws/ch08.md) is right on self-contained store + logic and independent evolution. **"Can communicate with other cells" over-claims** — WA: no cross-cell API, no shared DB/S3; scatter-gather goes *back through the router*.

## Three units — do not collapse them

| Card | Unit | Question it answers |
|---|---|---|
| **[C8](Bulkhead.md)** | Capacity compartment (pool, semaphore, shuffle shard; cells as a *percentage*) | How much may run at once, and what fraction a poison request can hit? |
| **[B2](Partitioning.md)** | Data shard (key-range, hash, composite) | Where does this *record* live? |
| **E13 (this card)** | Availability cell (complete stack replica) | How much of the *fleet* can one tenant, deploy, or noisy neighbour take? |

A tenant-aligned partition key is how the three *compose*: B2's `tenantId` can sit *inside* a cell; C8's 2-of-8 shuffle shard can sit *inside* a hot cell; E13 is the deployable wall around both. Hashing records across a shared schema is still one quantum. Shuffle-sharding workers that share a DB is still C8. Neither is this style.

The inner template is orthogonal. A cell can wrap a monolith, a modular monolith, a service-based core, a microservice graph, or Regional serverless (E1 / E10 / E6 / E2 / E11). E13 only requires a *complete* copy that does not touch another copy's store. It does not fix a Big Ball of Mud inside the template, and it does not decide how you cut domains.

## Lineage and vocabulary

- **Nygard, *Release It!***. Same ship-bulkhead metaphor. Nygard's bulkhead is dedicated *capacity* — [C8](Bulkhead.md). A cell is a dedicated *copy of the system*.
- **AWS Well-Architected, *Reducing the Scope of Impact with Cell-Based Architecture*** (first published **2023-09-20**, fetched 2026-09-13). The style card of record. A cell is a complete independent instance and does not share state with siblings. The **cell router** is the thinnest shared layer: partition key → one cell, one client endpoint; it **cannot** use the cell strategy on itself. The **control plane** provisions, migrates, deploys, and monitors. The **data plane** (router + cells in steady state) must keep serving if the control plane is down — REL11-BP04 static stability. WA CAP gloss: control planes prefer **CP**; data planes prefer **AP** (stale mappings). **Cell zero** is the current un-celled stack treated as the first cell when migrating. A **shuffle shard** is not a cell — inside a cell only; [C8](Bulkhead.md) owns the tactic.
- **REL10-BP03** (Reliability Pillar, fetched 2026-09-13). Bulkheads "*also known as cell-based architectures*"; 10 cells → 90% of requests unaffected. Anti-patterns: unbounded growth, deploy-all-cells, shared state (except the router), fat router, cross-cell chatter. The 2023 PDF further-reading still says **REL10-BP04**; the live page is **REL10-BP03**.
- **Vogels, "Looking back at 10 years of compartmentalization at AWS" (2018-03-26).** AZ launch 2008-03-26; Regions as hardest boundaries (full S3/DynamoDB/RDS stacks); then services compartmentalized *within* zones — **HyperPlane** (NAT Gateway, NLB, PrivateLink) "internally subdivided into cells that each handle a distinct set of customers." AZ/Region *counts* on that page are 2018 — do not treat as current.
- **Vogels, "On building scalable control planes" (2026-08).** EC2's second internal shard "was … cells" per zone; account-vs-resource key is service-specific (Amazon practice, not a customer how-to).
- **Azure vocabulary drift.** Azure Bulkhead (C8 `ms.date` **2026-03-19**) now writes that bulkhead is "also known as a *cell-based architecture*." That equation is Azure's. Azure WAF *self-preservation*: **Deployment Stamps** = "stamp … service unit, scale unit, or cell"; **Bulkhead** = pools. This catalog keeps **C8** for capacity partitions and **E13** for the deployable-copy style. Azure's closer *style* analog is stamps, not the Bulkhead page.
- **This tree.** [sharding-multitenancy.md](../data-intensive-design/sharding-multitenancy.md) (Oliveira 2023 as [8](../data-intensive-design/sharding-references.md)): a cell "groups services and storage for a set of tenants." [C8](Bulkhead.md) already quotes the 10%/1% arithmetic and owns Infima / Route 53 combination counts — do not re-derive 28 / 56 / `C(2048,4)` here.

**Partition key.** Grain of the service (`customer ID`, `resource ID`, or composite). On, or deterministically inferable from, most calls. Placement is control-plane work; the data plane only evaluates the loaded map.

## What the style is — and is not

WA *Cell design*: if the workload is "an Application Load Balancer, some EC2 instances, and an Amazon RDS database," cell 2 is **another deployment of those three** — not a second microservice or a thread pool. Each cell handles a key subset; owns its data store and compute; is unaware of siblings in the ideal (no cross-cell API, no shared DB/S3; separate accounts encouraged); and has named maxima. A 30-host fleet can stay 30 hosts behind a router — **placement**, not automatically a 2× bill (headroom and dedicated-tenancy SKUs still cost). That "30 hosts stay 30" is a sketch, not a cost model.

```
clients ──► cell router (shared, thin, hash/map) ──► cell i (full stack)
control plane ── provisions cells, writes the map, migrates tenants
```

| Lookalike | Why it is not E13 |
|---|---|
| **In-process bulkhead (C8)** | Caps *capacity* on a shared host / heap / deploy. |
| **Shuffle shard (C8)** | Overlapping workers + client retry. Opposite of "share no state." WA FAQ: *inside* a cell; **not** across cells. |
| **LB clones (C5 / E1)** | Same schema, same blast radius for poison or a bad deploy. The cell router is a sticky partition-key map, not an LB of identical hosts. |
| **DB shard only (B2)** | [Partitioning](Partitioning.md) places a *record*. The style copies **services and storage**. A cell *contains* partitions. |
| **Microservices (E2)** | Different services, different data. Cells stamp the *same* design. E2 can live *inside* a cell; sharding the fleet is not cutting domains. |
| **Multi-AZ / Region (C3)** | Provider boundaries. Cells add a *workload* boundary. **Not** failover domains. |
| **Azure Bulkhead synonym** | Pools. Use **Deployment Stamps** if you need Azure's style analog. |

[E2](Microservices.md) and [C8](Bulkhead.md) are the two most common mislabels. Microservices partition *domain*; cells partition *load and fate*. You can run E2 inside E13 (each cell hosts the same service graph) or run E13 in front of an E1 / E10 / E6 core. Picking one does not pick the other. C8's 1/*N* percentage is the *tactic* this style uses; a semaphore is not a cell architecture.

## Typical quantum count — FACT

From [style-selection.md](../../.cursor/skills/arch-style/references/style-selection.md). Do **not** re-run the four determinations. Quantum = smallest independently runnable part; **the DB is inside the quantum — a single shared DB ⇒ quantum of one**; sync can silently merge quanta. The comparison matrix runs layered through microservices. **No cell-based row. No prose-recovered stars.** A `—` is not a rating.

| Question | Answer | Why |
|---|---|---|
| Independently runnable unit? | **One cell** (full stack + *its* DB) | WA: cell 2 is another ALB+EC2+RDS. |
| Shared DB? | **Collapses to one quantum** | Book `:36`. Cell costumes on one store. |
| *N* cells = *N* *design* quanta? | **Usually no** | Same characteristics set, code, schema *shape*, release-train design. |
| Typical count? | **1 design quantum, stamped *N* times, plus 1 shared router** | WA: typically **many identical cells** (sizing page: operate "tens, hundreds or more"). |
| Silent merge? | Cross-cell sync, shared S3/DB, fat router | Book sync-merge; WA: cross-cell deps "quickly eliminate the benefits." |

**E13 typical quantum count = 1 design quantum × *N* identical copies.** A FACT about the style's shape (WA replicas + book machinery), not a book rating. Fallacies this style pays for when real (style-selection ch9 — name, do not score): the network is reliable; latency is zero; topology never changes; versioning is easy; observability is optional.

## Decision mechanics

### Cell size vs failure domain

WA *Cell sizing* — three opposing forces: **big enough** for the largest tenant and for economies of scale; **small enough** to test at full scale and stay under account/quotas. Name TPS / tenants / GB. WA arithmetic (C8 already quotes the tactic): **10 cells → ~10% blast radius; 100 → ~1%.** Smaller cells: more replicas, smaller slice, cheaper to test. Larger: fewer replicas, better utilization, bigger slice, closer to quotas. A whale that outgrows one cell on a 1-D key must not freeze scale-out — add a second dimension or a **dedicated cell**.

| | **Multi-AZ (Regional) cell** | **Single-AZ cell** |
|---|---|---|
| Shape | Replica rides Regional / serverless services | Follows AZ boundaries (EC2-like) |
| Wins | Self-resilience; less DR machinery | Precise "which AZ is sick" |
| Loses | Weak against *gray* zonal failure | Three zonal routers; AZ-scoped services only; extra DR; **replicating state to another AZ can break "no shared state"** |
| AZ death | Cell keeps running for its tenants | That AZ's cells die (WA sketch: four zonal cells ≈ one third of customers) |

WA: cells isolate cascading failures (overload, bad deploy, poison pill) — **not** failover domains. If you are not exposing AZ-scoped resources, **prefer Multi-AZ cells**. Zonal loss and Region evacuation stay on [C3](FailoverHealth.md). Deploy in waves (canary-per-cell); deploy-all-cells is a REL10-BP03 anti-pattern. Observability must be **cell-aware**; fleet-aggregate dashboards hide the property you bought.

### Routing

The key must match the grain of the service. `CustomerID` first. Scatter-gather must be the **minority** and go **back through the router**. The router must stay a **subset** of the un-celled app's scaling problems — and should itself be built as a cellular component. No business logic; cryptographic hash + modulo is the named cheap map; keep serving healthy cells when one is unreachable.

| Algorithm | State | Add/remove cells | Failure mode |
|---|---|---|---|
| **Full mapping** | Every key → cell | Easy targeted moves | Map is a critical R/W dep; large state |
| **Prefix / range** | Ranges → cell | Lower cardinality | Hot keys inside a range |
| **Naïve modulo / fixed N** | Cell count only | **Remap everyone** | Churn on every scale-out |
| **Consistent hashing** | Small, stable (Ring / Karger; Lamping/Veach; Appleton/O'Reilly) | Low churn | High peak-to-average; WA usual = tens of thousands of logical buckets + a small bucket→cell table |

**Override table** (all but native full-map): quarantine, tests, whales. Router *products* WA names as examples, not defaults: Route 53, API Gateway + mapping store ([C6](ApiGateway.md) is *a* implementation), compute + S3 map (static-stability sketch), SQS/MSK as a non-HTTP "router." Product SLAs on those pages are *those products'*, not cell availability.

### Control plane vs data plane

The control plane writes the map, provisions cells, migrates tenants, and rolls deploys. The data plane only *evaluates* the loaded map. REL11-BP04: the data plane must be **statically stable** — an in-memory map survives control-plane or even S3 loss. On-board of new tenants can stop; checkout must not. Put the control plane on the request path and you have invented a fleet-wide dependency that cells were meant to escape.

Placement policy is control-plane work: put a tenant on the coldest cell under its tested max; whale move = clone → flip → override → forget. [C10](LoadShedding.md) is what a cell does when it hits those named maxima — not a reason to grow the cell without bound.

WA *Control plane and data plane*: the router is data-plane. A mapping read on every request that goes back to the control store is a control-plane hop you did not budget. Cache the map; refresh it out of band; fail toward the last good map (AP / stale mappings). Host and AZ *evacuation* stay on [C3](FailoverHealth.md) — cells are not designed as failover domains.

### Cell-aware operations

The property you bought is per-cell. Fleet-aggregate error rate, a single deploy pipeline, and a shared on-call dashboard all erase it. Emit error rate, saturation against named maxima, and deploy generation **per cell**. Game-day a drain: siblings keep serving; only that cell's dashboard burns. A canary is a cell (or a slice of one), not a percentage of a shared fleet — deploy-all-cells is how a bad build recovers the 100% blast radius.

## When to use

WA *When to use*, not a scorecard: downtime has huge customer / reputational / financial impact; FSI "critical to economic stability"; ultra-scale "too big/critical to fail"; multi-tenant services that need a **dedicated cell**. Candidate *targets* **RPO < 5 s** / **RTO < 30 s** are WA *when-to characteristics*, **not measured SLAs** and not this card's promise. Also a fit when almost every call has a stable partition key, a cell can be capped and tested at full scale, and the feared failures are poison / bad deploy / noisy tenant — not "AZ dies."

## When not to use

WA disadvantages: redundant-stack complexity; higher infra cost (RIs / Savings Plans only *narrow* the delta); specialized ops for *N* replicas; you must build the router. Skip E13 when:

- One stack is still testable at full scale.
- There is no stable key, or most traffic is cross-key (global joins / uniqueness become the majority path).
- Cells would share one database — silently **one quantum**, book `:36`.
- A team cannot yet operate *two* cells.
- Pool-grain isolation is enough — stay on [C8](Bulkhead.md).
- The open question is still monolith-vs-microservices ([E1](Monolith.md) / E10 / E6 / [E2](Microservices.md) first). Changing the *inner* style without changing *N* is not this decision.
- You want overlapping retry isolation more than exclusive state (shuffle sharding *inside* one cell — C8).

## Migration in / out

**In** (WA *Best practices* + *Cell migration*):

1. Current stack = **cell zero**; put the router in front.
2. **More than one cell on day one** — a single cell is costumes.
3. **Migration mechanism on day one**.
4. Stateful move = **clone** (non-authoritative) → **flip authoritative** → **redirect** → **forget**, or a control-plane coordinated flip so the destination is ready first.
5. Temporary dual-map / redirect window is shared fate — keep it short and one-way.
6. Failure-mode worksheet per component ("are siblings impacted?").

**Out.** Collapse to cell zero if the ops tax exceeds isolation. Changing the *inner* style (E1→E10→E6) without changing *N* is not leaving E13. Adding shuffle sharding *inside* a cell is C8. Sharing a database is leaving the style while keeping the bill.

## Worked example — multi-tenant checkout

Design drill from fetched WA pages, not a vendor engagement.

**Workload.** Checkout API; almost every call has `customerId`. A poison `POST /capture` or a bad build must not take the fleet. Some enterprises pay for a dedicated cell.

**Cell template.** ALB + compute + isolated store (WA's RDS, or a per-cell table/account). Named maxima. Inner style E1 or E6 — E13 only requires a *complete* copy that does not touch another copy's store. **Not** a cell: eight workers on one schema ([C5](LoadBalancing.md)); Hikari pools ([C8](Bulkhead.md)); a 2-of-8 shuffle shard of those workers (C8 — 28 combinations or 2014's 56 permutations; pick one convention and leave it on C8).

**Router / control plane.** Thin `H(customerId) mod N` while *N* is stable; override table for dedicated / quarantine. When *N* changes, logical buckets + bucket→cell table — not naïve-modulo the world. Control plane places tenants on the coldest cell under its tested max; whale move = clone → flip → override → forget. Routers serve the last loaded map if the control plane dies (on-board stops; checkout does not). Checkout exposes no AZ-scoped resources → **Multi-AZ cells**. Wave 0 = canary; never one pipeline that stamps all *N*.

**C8 stops at the cell wall.** Payment vs inventory *pools* and a 2-of-8 worker shuffle shard stay *inside* a hot cell. Route 53's 2048×4 shuffle-shard is the DNS *product's* story, not this map.

**Game day.** Drain cell 2; 1 and 3 still serve; only cell 2's dashboard burns; a canary-scoped bad build stays on the canary. A shared-DB "cell" that fails this was never E13. [C3](FailoverHealth.md) is the drill for "AZ dies," not this one.

## Failure modes of the style

- **Shared fate through the back door.** One DB, S3 bucket, lock, account-limit, or global table. Five "cells" in front of one store are [B2](Partitioning.md) costumes. The bulkhead is only as real as the deepest shared resource.
- **Shared control plane on the data path.** Violates REL11-BP04. A mapping-store outage, a deploy-orchestrator hang, or an S3 read on every request turns the control plane into the blast radius cells were bought to shrink. Data plane serves the last loaded map; on-board can wait.
- **Cell identity leakage.** WA's contract is **one client endpoint** and cells that do not know their siblings. Leak the cell id into a public URL, a client cookie, an SDK pin, or a downstream callback and the *client* becomes a second router — `clone → flip → redirect → forget` cannot forget. Leak tenant or cell membership into a shared cache, log index, or uniqueness table and siblings couple through that store. Keep cell identity inside the control plane's map; clients see a partition key, not a cell.
- **Fat router.** Business logic on the one shared component is a fleet-wide blast radius. [C8](Bulkhead.md) already names this; it is how E13 dies.
- **Cross-cell chatter as the majority path.** WA: those deps "quickly eliminate the benefits." Scatter-gather back through the router, and keep it the minority.
- **Shuffle-shard *across* cells.** WA FAQ forbids. Overlapping membership undoes exclusive state. C8 owns *inside*.
- **Cells as failover domains.** A zonal replica that re-shares state to survive AZ loss is [C3](FailoverHealth.md) wearing a cell badge. Prefer Multi-AZ cells, or name the DR.
- **Unbounded cell growth.** Named maxima exist so [C10](LoadShedding.md) has a number. Growing one cell until it is the old monolith wastes the style.
- **Deploy-all-cells.** REL10-BP03 anti-pattern. One pipeline that stamps all *N* is a fleet-wide bad build.
- **Whale on `CustomerID`** with no second dimension or dedicated-cell path. Scale-out freezes on one tenant.
- **Naïve-modulo remap storm.** Changing *N* reshuffles everyone. Logical buckets + a bucket→cell table, or a full map.
- **Skipped clone→flip→redirect→forget.** Two writers, or a black hole. The dual-map window *is* shared fate.
- **Aggregate-only ops.** Fleet dashboards hide the cell that is on fire. Cell-aware telemetry is part of the style, not a D-group extra.

## Trade-offs

Qualitative. **No invented stars.**

| Concern | Cells win | Cells lose | Source |
|---|---|---|---|
| Blast radius | *N* → ~1/*N* of keys (10 → 10%, 100 → 1%) | That 1/*N* is 100% for those tenants | WA *What is…*, *When to use* |
| Testability | Cap the cell; simulate the largest tenant that fits | Router × *N* is still untested as one system | WA *Why use* |
| Scale | Add a known-size cell; stay under quotas | Whale on a 1-D key blocks scale-out | WA *Cell sizing* |
| Deploy | Canary-per-cell phase dimension | *N* production pipelines | WA deployment; REL10-BP03 |
| MTBF / MTTR | WA: smaller, familiar units | *N*× events unless those claims hold | WA *Why use* |
| AZ / gray | Multi-AZ cells ride Regional services | Zonal cells die with the AZ; replicas re-share state | WA *Cell design* |
| Router | One client endpoint | Shared fate; must stay thinner than the app | WA *Cell routing* |
| Cost | 30 hosts can stay 30 *in the sketch* | Redundant stacks, idle headroom, specialized ops | WA *When to use* |
| Cross-key features | Per-cell ACID stays cheap | Global joins / uniqueness become minority-or-else | WA *Cell partition* |
| Inner modularity | Orthogonal to E1 / E2 / E6 | Does not fix a BBOM inside the template | style-selection (no cell row) |
| Shuffle overlap | — | Across cells undoes exclusive state | WA FAQ; C8 |

[C8](Bulkhead.md) decides **how much may run at once, per compartment**. [B2](Partitioning.md) decides **where a record lives**. [E2](Microservices.md) decides **how you cut domains**. [C3](FailoverHealth.md) decides **when a destination is dead**. This style decides **how much of the fleet one poison tenant, bad deploy, or noisy neighbour can take**.

## Sources

Verified 2026-09-13; the full URL list, per-claim provenance, and items deliberately left out are in the [external research note](../../docs/research/sysdesign/e13-cell-based-external-research.md). Shuffle-shard combination counts stay on [C8](Bulkhead.md). Quantum machinery is FACT from [style-selection.md](../../.cursor/skills/arch-style/references/style-selection.md) — **no cell row**, do not fill stars.

- Canon: AWS WA, *Reducing the Scope of Impact with Cell-Based Architecture* (2023-09-20) — *What is…*, *Why / When to use*, *Cell design / sizing / routing*, *Control / data plane*, *migration / deployment / observability*, *Best practices*, *FAQ*. REL10-BP03. Vogels, *10 years of compartmentalization* (2018-03-26) and *On building scalable control planes* (2026-08).
- Azure drift: Bulkhead pattern (`ms.date` 2026-03-19); WAF self-preservation (stamps vs pools).
- Tactic, not this card: MacCárthaigh, *Shuffle Sharding* (2014-04-14); Builders' Library shuffle-sharding — numbers owned by C8.
- This tree: [Bulkhead.md](Bulkhead.md); [c8-bulkhead-external-research.md](../../docs/research/sysdesign/c8-bulkhead-external-research.md); [aws/ch08.md](../aws/ch08.md) (cellular paragraph — own-store matches WA); [sharding-multitenancy.md](../data-intensive-design/sharding-multitenancy.md).
