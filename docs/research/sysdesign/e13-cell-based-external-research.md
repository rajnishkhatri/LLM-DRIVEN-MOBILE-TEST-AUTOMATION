---
type: research
title: 'Cell-based architecture — external research (2026-09-13)'
description: >-
  Group E decision-depth pass for catalog E13: complete-stack replicas as
  blast-radius units; cell routing and size vs failure domain; quantum FACT
  (one design quantum stamped N times — style-selection has no cell row);
  when-to / when-not; migration; AWS cellular worked cut. C8 owns shuffle
  sharding and cells-as-tactic. No library defaults.
tags: [research, system-design-patterns, E13, cell-based]
---

# Cell-based architecture — external research (2026-09-13)

> **What this is.** Catalog **⊕E13** (Group E). No scoring loop. **C8**
> owns cells as a 1/*N* *tactic* and shuffle-shard math; this card owns
> the *style*. Quantum FACT from
> [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md)
> — **no cell-based row**; a `—` is not a rating. WA / REL10 / Vogels /
> Azure fetched **2026-09-13**. Unverified → §8.
>
> **Cite, do not rewrite:**
> [c8-bulkhead-external-research.md](c8-bulkhead-external-research.md)
> (1/*N* tactic; 28-vs-56),
> [bulkhead-isolation-external-research.md](bulkhead-isolation-external-research.md),
> [Bulkhead.md](../../../cases/SystemDesignPatterns/Bulkhead.md),
> [aws/ch08.md](../../../cases/aws/ch08.md) (cellular paragraph —
> own-store matches WA; **"can communicate with other cells" is too
> strong**),
> [sharding-multitenancy.md](../../../cases/data-intensive-design/sharding-multitenancy.md)
> (Oliveira 2023 as
> [8](../../../cases/data-intensive-design/sharding-references.md)).

---

## 1. Scope and non-goals

**This note owns** cell-based architecture as a *style*: *N* complete,
independently operable copies of a workload (compute + data + control
inside the cell), plus a thin shared **cell router** and a **control
plane** that places tenants and provisions cells. Decision depth: what
the style is and is not; typical quantum count as a FACT; cell routing;
cell size vs failure domain; when-to / when-not; migration in and out;
a worked AWS-cellular cut; a qualitative trade-off table. No invented
stars.

A cell is **not** a thread pool, a semaphore, or a shuffle shard. Those
are isolation *tactics* (**C8**). Azure Bulkhead (fetched 2026-09-13;
C8 recorded `ms.date` **2026-03-19**) now writes that bulkhead is
"also known as a *cell-based architecture*." That equation is Azure's.
This catalog keeps **C8** for capacity partitions and **E13** for the
deployable-copy style.

**Stays in sibling catalog ids**

| Id | Why it is not this card |
|---|---|
| **C8** | Pools, shuffle sharding, cells as a *percentage* blast-radius tactic. Owns Infima / Route 53 combination counts. |
| **C5** | Cloning *inside* one cell. The cell router is a sticky partition-key map, not an LB of identical hosts. |
| **C6** | One *implementation* of a cell router (WA names API Gateway + a mapping store). |
| **C3** | AZ / Region evacuation. WA: cells are **not** designed as failover domains. |
| **C10** | What to drop when a cell hits its known maxima. |
| **B1 / B2** | Autoscalers and `L = λW` (B1); partition-key / intra-cell storage (B2). Scale-out *by adding cells* is this style's growth rule. |
| **E1 / E10 / E2 / E6 / E11** | Inner template / host of the cell. A cell can wrap a monolith, a service fleet, or Regional serverless. |

**Non-goals.** Library defaults. Scoring via arch-style's four
determinations. Rewriting C8's shuffle-shard math. Inventing SLAs,
cell counts, or vendor RTO numbers beyond fetched *guidance*.

---

## 2. Lineage / vocabulary

| Term | Meaning | Named source |
|---|---|---|
| **Cell** | Complete independent instance of the workload. Does not share state with other cells. | WA *What is…* / *Cell design* (2023-09-20) |
| **Cell router** | Thinnest shared layer: partition key → one cell; one client endpoint. **Cannot** use the cell strategy on itself. | WA *Cell routing*; REL10-BP03 |
| **Control plane** | Provision / migrate / deploy / monitor cells. | WA *Control plane and data plane* |
| **Data plane** | Router + cells in steady state. Must serve if the control plane is down (REL11-BP04 static stability). | Same |
| **Partition key** | Grain of the service (`customer ID`, `resource ID`, or composite). On (or deterministically inferable from) most calls. | WA *What is…*; REL10-BP03 |
| **Cell zero** | The current un-celled stack, treated as the first cell when migrating. | WA *Best practices* |
| **Shuffle shard** | Overlapping virtual shards; **not** a cell. Inside a cell only. | WA FAQ; **C8** owns the tactic |

**Shared metaphor, different unit.** WA opens with the same ship
bulkhead Nygard used in *Release It!*. Nygard's bulkhead is dedicated
*capacity* (C8). A cell is a dedicated *copy of the system*.

**AWS / Vogels.** WA PDF (first published **2023-09-20**; contributor
Robisson Oliveira; history = initial publication only): AWS service
teams have used cells "for more than a decade" as isolation *beyond*
AZ and Region. Vogels, "Looking back at 10 years of
compartmentalization at AWS" (**2018-03-26**): AZ launch 2008-03-26;
Regions as "hardest boundaries" (full S3/DynamoDB/RDS stacks); then
services "compartmentalized even within zones" — **HyperPlane** (NAT
Gateway, NLB, PrivateLink) "internally subdivided into cells that each
handle a distinct set of customers." AZ/Region *counts* on that page
are 2018 — do not treat as current. Vogels, "On building scalable
control planes" (**2026-08**): EC2's second internal shard "was …
cells" per zone; account-vs-resource key is service-specific (Amazon
practice, not a customer how-to).

**REL10-BP03** (Reliability Pillar, fetched 2026-09-13): bulkheads
"*also known as cell-based architectures*"; 10 cells → 90% of requests
unaffected; anti-patterns = unbounded growth, deploy-all-cells, shared
state (except the router), fat router, cross-cell chatter. The 2023
PDF further-reading still says **REL10-BP04**; the live page is
**REL10-BP03**.

**Azure vocabulary drift.** Bulkhead page (fetched 2026-09-13): synonym
plus *connection-pool* diagrams — C8 grain. Azure WAF
*self-preservation* (same day): **Deployment Stamps** = "stamp …
service unit, scale unit, or cell"; **Bulkhead** = pools. Use the
synonym as drift, not this catalog's definition.

**Workspace.** [aws/ch08.md](../../../cases/aws/ch08.md) cellular
paragraph: self-contained store + logic; failure in one cell does not
affect others; cells can evolve independently. **"Can communicate with
other cells" over-claims** — WA: no cross-cell API, no shared DB/S3;
scatter-gather goes *back through the router*.
[sharding-multitenancy.md](../../../cases/data-intensive-design/sharding-multitenancy.md):
a cell "groups services and storage for a set of tenants."

**Shuffle sharding stays C8.** MacCárthaigh 2014-04-14 and Builders'
Library "Workload isolation using shuffle-sharding": 4×2 → 25%; 2-of-8
**56 permutations** (2014) vs **28 combinations** (Builders' Library);
Route 53 `C(2048,4)`. Overlapping membership is the opposite of "share
no state." WA FAQ: shuffle-shard *inside* a cell; **not** across cells.

---

## 3. Mechanics (Group E decision depth bar)

### 3.1 What the style is — and is not

A **cell-based architecture** partitions a workload into *N* **complete
stack replicas**. WA *Cell design*: if the workload is "an Application
Load Balancer, some EC2 instances, and an Amazon RDS database," cell 2
is **another deployment of those three** — not a second microservice
or thread pool. Each cell handles a partition-key subset; owns its
data store and compute; is unaware of siblings in the ideal (no
cross-cell API, no shared DB/S3; separate accounts encouraged); and
has **known maxima** (TPS, tenants, GB) it may not exceed. Growth is
**scale-out by adding cells**. WA: a 30-host fleet can stay 30 hosts
behind a router — placement, not automatically a 2× bill (headroom
and dedicated-tenancy SKUs still cost).

```
clients ──► cell router (shared, thin, hash/map) ──► cell i (full stack)
control plane ── provisions cells, writes the map, migrates tenants
```

The **router** cannot use the cell strategy on itself: no business
logic; cryptographic hash + modulo is the named cheap map; keep
serving healthy cells when one is unreachable. WA cites MacCárthaigh
*Reliability, constant work, and a good cup of coffee* (essay not
re-fetched — §8). The **control plane** writes the map; the **data
plane** must be statically stable (in-memory map survives control-plane
or even S3 loss). WA CAP gloss: control planes prefer **CP**; data
planes prefer **AP** (stale mappings).

| Lookalike | Why it is not E13 |
|---|---|
| **In-process bulkhead (C8)** | Caps *capacity* on a shared host/heap/deploy. |
| **Shuffle shard (C8)** | Overlapping workers + retry. Inside a cell only. |
| **LB clones (C5 / E1)** | Same schema, same blast radius for poison or a bad deploy. |
| **DB shard only** | B2 / [sharding-multitenancy.md](../../../cases/data-intensive-design/sharding-multitenancy.md). The style copies **services and storage**. |
| **Microservices (E2)** | Different services, different data. Cells stamp the *same* design. E2 can live *inside* a cell. |
| **Multi-AZ / Region (C3)** | Provider boundaries. Cells add a *workload* boundary. Not failover domains. |
| **Azure Bulkhead synonym** | Pools. Azure's closer *style* analog is **Deployment Stamps**. |

### 3.2 Typical quantum count — FACT

From
[style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md)
(do **not** re-run determinations): quantum = smallest independently
runnable part; **the DB is inside the quantum — single shared DB ⇒
quantum of one**; sync can silently merge quanta. The comparison
matrix has layered through microservices. **No cell-based row. No
prose-recovered stars.** Do not invent a rating.

| Question | Answer | Why |
|---|---|---|
| Independently runnable unit? | **One cell** (full stack + *its* DB) | WA: cell 2 is another ALB+EC2+RDS. |
| Shared DB? | **Collapses to one quantum** | Book `:36`. Cell costumes on one store. |
| *N* cells = *N* *design* quanta? | **Usually no** | Same characteristics set, code, schema *shape*, release-train design. |
| Typical count? | **1 design quantum, stamped *N* times, plus 1 shared router** | WA: typically **many identical cells** (sizing page: operate "tens, hundreds or more"). |
| Silent merge? | Cross-cell sync, shared S3/DB, fat router | Book sync-merge; WA: cross-cell deps "quickly eliminate the benefits." |

**E13 typical quantum count = 1 design quantum × *N* identical copies.**
FACT about the style's shape (WA replicas + book machinery), not a
book rating. Fallacies this style pays for when real (ch9 — name, do
not score): network is reliable; latency is zero; topology never
changes; versioning is easy; observability is optional.

### 3.3 Cell routing and mapping

The key must match the grain of the service. `CustomerID` first; a
whale that outgrows one cell must not freeze scale-out — add a second
dimension or a **dedicated cell**. Placement is control-plane work;
the data plane only evaluates the loaded map. Scatter-gather must be
the **minority** and go **back through the router**.

| Algorithm | State | Add/remove cells | Failure mode |
|---|---|---|---|
| **Full mapping** | Every key → cell | Easy targeted moves | Map is a critical R/W dep; large state |
| **Prefix / range** | Ranges → cell | Lower cardinality | Hot keys inside a range |
| **Naïve modulo / fixed N** | Cell count only | **Remap everyone** | Churn on every scale-out |
| **Consistent hashing** | Small, stable (Ring / Karger; Lamping/Veach; Appleton/O'Reilly) | Low churn | High peak-to-average; WA usual = tens of thousands of logical buckets + a small bucket→cell table |

**Override table** (all but native full-map): quarantine, tests, whales.
Router *products* WA names as examples, not defaults: Route 53,
API Gateway + mapping store, compute + S3 map (static-stability
sketch), SQS/MSK as a non-HTTP "router." Product SLAs on those pages
are *those products'*, not cell availability. The router must stay a
**subset** of the un-celled app's scaling problems — and should
itself be built as a cellular component.

### 3.4 Cell size vs failure domain

WA *Cell sizing* — three opposing forces: **big enough** for the
largest tenant and for economies of scale; **small enough** to test at
full scale and stay under account/quotas. Name TPS / tenants / GB.
WA arithmetic (C8 already quotes the tactic): **10 cells → ~10% blast
radius; 100 → ~1%.** That 1/*N* is 100% for *those* tenants. Smaller
cells: more replicas, smaller slice, cheaper to test. Larger: fewer
replicas, better utilization, bigger slice, closer to quotas.

| | **Multi-AZ (Regional) cell** | **Single-AZ cell** |
|---|---|---|
| Shape | Replica rides Regional / serverless services | Follows AZ boundaries (EC2-like) |
| Wins | Self-resilience; less DR machinery | Precise "which AZ is sick" |
| Loses | Weak against *gray* zonal failure | Three zonal routers; AZ-scoped services only; extra DR; **replicating state to another AZ can break "no shared state"** |
| AZ death | Cell keeps running for its tenants | That AZ's cells die (WA example: four zonal cells ≈ one third of customers — *their* sketch) |

WA: cells isolate cascading failures (overload, bad deploy, poison
pill) — **not** failover domains. If you are not exposing AZ-scoped
resources, **prefer Multi-AZ cells**. Deploy in waves (canary-per-cell);
deploy-all-cells is a REL10-BP03 anti-pattern. Observability must be
**cell-aware**; fleet-aggregate dashboards hide the property you bought.

### 3.5 Migration in / out

**In** (WA *Best practices* + *Cell migration*): (1) current stack =
**cell zero**, router in front; (2) **more than one cell on day one**;
(3) **migration mechanism on day one**; (4) stateful move = **clone**
(non-authoritative) → **flip authoritative** → **redirect** →
**forget**, or a control-plane coordinated flip so the destination is
ready first; (5) temporary dual-map / redirect window is shared fate —
keep it short and one-way; (6) failure-mode worksheet per component
("are siblings impacted?").

**Out.** Collapse to cell zero if ops tax exceeds isolation. Changing
the *inner* style (E1→E10→E6) without changing *N* is not leaving
E13. Adding shuffle sharding *inside* a cell is C8. Sharing a database
is leaving the style while keeping the bill.

### 3.6 Worked example — multi-tenant checkout

Design drill from fetched WA pages, not a vendor engagement.

**Workload.** Checkout API; almost every call has `customerId`. A
poison `POST /capture` or a bad build must not take the fleet. Some
enterprises pay for a dedicated cell.

**Cell template.** ALB + compute + isolated store (WA's RDS, or a
per-cell table/account). Named maxima. Inner style E1 or E6 — E13
only requires a *complete* copy that does not touch another copy's
store. **Not** a cell: eight workers on one schema (C5); Hikari pools
(C8); a 2-of-8 shuffle shard of those workers (C8).

**Router / control plane.** Thin `H(customerId) mod N` while *N* is
stable; override table for dedicated / quarantine. When *N* changes,
logical buckets + bucket→cell table — not naïve-modulo the world.
Control plane places tenants on the coldest cell under its tested
max; whale move = clone → flip → override → forget. Routers serve the
last loaded map if the control plane dies (on-board stops; checkout
does not). Checkout exposes no AZ-scoped resources → **Multi-AZ
cells**. Wave 0 = canary; never one pipeline that stamps all *N*.

**C8 stops at the cell wall.** Payment vs inventory *pools* and a
2-of-8 worker shuffle shard stay *inside* a hot cell (C8: 28
combinations or 2014's 56 permutations — one convention). Route 53's
2048×4 shuffle-shard is the DNS *product's* story, not this map.

**Game day.** Drain cell 2; 1 and 3 still serve; only cell 2's
dashboard burns; a canary-scoped bad build stays on the canary. A
shared-DB "cell" that fails this was never E13.

### 3.7 Trade-off table

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
| Inner modularity | Orthogonal to E1/E2 | Does not fix a BBOM inside the template | style-selection (no cell row) |
| Shuffle overlap | — | Across cells undoes exclusive state | WA FAQ; C8 |

---

## 4. Verified editions / dated facts (no library defaults)

| Artifact | Date | Fetched |
|---|---|---|
| WA *Reducing the Scope of Impact with Cell-Based Architecture* | first published **2023-09-20**; PDF history = initial only | 2026-09-13 (HTML + PDF) |
| REL10-BP03 | live **REL10-BP03** (PDF further-reading still REL10-BP04) | 2026-09-13 |
| Vogels, 10 years of compartmentalization | **2018-03-26** | 2026-09-13 |
| Vogels, On building scalable control planes | **2026-08** | 2026-09-13 |
| MacCárthaigh, Shuffle Sharding | **2014-04-14** | numbers owned by C8 |
| Azure Bulkhead | C8 `ms.date` **2026-03-19** | body 2026-09-13 |
| style-selection.md | FSA ch7 + ch10–18 matrix; **no cell row** | read 2026-09-13 |

---

## 5. Failure modes and when-not-to-use

**Failure modes.** (1) Shared fate through the back door — one DB, S3
bucket, lock, account-limit, or global table. (2) Fat router. (3)
Cross-cell chatter as the majority path. (4) Shuffle-shard *across*
cells (WA FAQ forbids; C8 owns *inside*). (5) Cells as failover
domains (zonal replica re-shares state — use Multi-AZ or named C3 DR).
(6) Unbounded cell growth. (7) Deploy-all-cells. (8) Whale on
`CustomerID` with no second dimension or dedicated-cell path. (9)
Naïve-modulo remap storm. (10) Control plane on the data path
(violates REL11-BP04). (11) Aggregate-only ops. (12) Migration that
skips clone→flip→redirect→forget (two writers or a black hole).

**When to use** (WA *When to use*, not a scorecard): downtime has huge
customer / reputational / financial impact; FSI "critical to economic
stability"; ultra-scale "too big/critical to fail"; candidate
*targets* **RPO < 5 s** / **RTO < 30 s** (characteristics, not
measured SLAs); multi-tenant services that need a **dedicated cell**.
WA's question: 100% of customers at a 5% failure rate, or 5% of
customers at 100%? Cells pick the second. Also a fit when almost every
call has a stable partition key, a cell can be capped and tested at
full scale, and the feared failures are poison / bad deploy / noisy
tenant — not "AZ dies."

**When not.** WA disadvantages: redundant-stack complexity; higher
infra cost (RIs / Savings Plans only *narrow* the delta); specialized
ops for *N* replicas; you must build the router. Skip E13 when one
stack is still testable; there is no stable key or most traffic is
cross-key; cells would share one database (silently **one quantum**,
book `:36`); a team cannot yet operate *two* cells; pool-grain
isolation is enough (**C8**); the open question is still
monolith-vs-microservices (E1/E10/E6 first); or you want overlapping
retry isolation more than exclusive state (shuffle sharding *inside*
one cell — C8).

---

## 6. Cross-links

| Target | Relationship |
|---|---|
| **C8** | Tactics. Do not re-derive 28 / 56 / `C(2048,4)`. |
| **C5 / C6** | In-cell clones; API Gateway as *a* router. |
| **C3 / C10 / C4** | DR of zonal cells; shed/throttle at known maxima. |
| **B1 / B2** | Add cells to scale; shard *inside* a cell. |
| **E1 / E10 / E2 / E6 / E11** | Inner template / host. |
| **D1 / D3 / D4** | Cell-aware telemetry. |
| Workspace | ch08 cellular paragraph; sharding-multitenancy; Bulkhead.md; C8 notes. |
| style-selection.md | **No cell row** — honesty + quantum machinery only. |

---

## 7. Sources

Retrieved **2026-09-13** unless already in-tree.

1. AWS WA, *Reducing the Scope of Impact with Cell-Based Architecture* (**2023-09-20**). https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/what-is-a-cell-based-architecture.html — *What is…*, *Why / When to use*, *Cell design / sizing / routing*, *Control / data plane*, *migration / deployment / observability*, *Best practices*, *FAQ*. PDF: https://docs.aws.amazon.com/pdfs/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/reducing-scope-of-impact-with-cell-based-architecture.pdf
2. REL10-BP03. https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_fault_isolation_use_bulkhead.html
3. Vogels, "Looking back at 10 years of compartmentalization at AWS" (2018-03-26). https://www.allthingsdistributed.com/2018/03/ten-years-of-aws-compartimentalization.html — HyperPlane cells.
4. Vogels, "On building scalable control planes" (2026-08). https://www.allthingsdistributed.com/2026/08/on-building-scalable-control-planes.html — EC2 zone→cell shard.
5. MacCárthaigh, "Shuffle Sharding…" (2014-04-14). https://aws.amazon.com/blogs/architecture/shuffle-sharding-massive-and-magical-fault-isolation/ — tactic; **C8** owns the numbers.
6. Builders' Library "Workload isolation using shuffle-sharding" (body **not** re-fetched — §8). https://builder.aws.com/content/3F06NpJ8YeoIGP8VHTw4n81pFn8/workload-isolation-using-shuffle-sharding — historical: https://aws.amazon.com/builders-library/workload-isolation-using-shuffle-sharding/
7. Azure Bulkhead pattern. https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead
8. Azure WAF self-preservation. https://learn.microsoft.com/en-us/azure/well-architected/reliability/self-preservation — stamps vs pools.
9. [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md) — ch7 quantum; ch10–18 styles; **no cell entry**.
10. Workspace: `cases/aws/ch08.md`; `cases/data-intensive-design/sharding-multitenancy.md` + `sharding-references.md` [8]; `cases/SystemDesignPatterns/Bulkhead.md`; [c8-bulkhead-external-research.md](c8-bulkhead-external-research.md); [bulkhead-isolation-external-research.md](bulkhead-isolation-external-research.md).

---

## 8. Uncertain / left out

- **No book rating.** Do not fill stars. **REL10-BP03** live vs PDF **REL10-BP04**. PDF history after 2023-09-20: none (wrapper © 2026 ≠ revision).
- **Builders' Library** shuffle-sharding body: C8 saw **409** / JS shell. 2048 / 4 / ~730 billion / 28 stay C8 first-pass; 2014 56 / 1/1680 were re-read on C8. Do not mix conventions.
- MacCárthaigh "constant work" essay, WA observability essays, Physalia / ARC338, Infima repo: not fetched.
- **RPO < 5 s / RTO < 30 s** are WA *when-to characteristics*, not SLAs. Router-page product SLAs ≠ cell availability. "30 hosts stay 30" is a sketch.
- Vogels 2018 AZ/Region counts are dated; this note uses the HyperPlane-cell *mechanism*. Azure Bulkhead `ms.date` from C8 (**2026-03-19**); this session's conversion hid the field.
- ch08 "cells communicate" not used as definition. Azure's synonym not adopted. Industry write-ups (Slack, DoorDash, Stripe) and "start at 10 cells" blogs: not fetched. WA-named Code* helpers not versioned.
