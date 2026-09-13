---
type: reference
title: 'Hub-and-spoke'
description: >-
  Enterprise integration hub: an active Message Broker / EAI centre that
  replaces a fully-connected application graph. Not cloud WAN hub-spoke,
  not SOA/ESB (E6), not an API gateway (C6). Covers Hohpe vs Mason
  vocabulary, edge-count math, canonical-model cost, hub-as-SPOF, when
  not to use, migration, and the lookalike network topology.
tags: [system-design-patterns, architecture, hub-and-spoke, integration]
---

# Hub-and-spoke

**See also:** [SOA / service-based (E6)](ServiceOriented.md) · [API gateway and BFF (C6)](ApiGateway.md) · [event-driven architecture (E4)](EventDriven.md) · [pub/sub, queues, and streams (A2)](PubSubQueues.md) · [strangler fig (B4)](StranglerFig.md) · [microservices (E2)](Microservices.md) · [style-selection matrix](../../.cursor/skills/arch-style/references/style-selection.md) · [VPC mesh vs Transit Gateway](../aws/ch09.md) · [Figure 4-9 (org drawing, not this style)](../data-intensive-design/medallion-foundation-tenancy.md) · [Figure 2-6 (plate, not this style)](../fincancial-data-architecture/architecture-components.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/e9-hub-and-spoke-external-research.md)

Catalog **E9** is the **enterprise integration hub**: a centre that *brokers* application messages — Hohpe's Message Broker, the EAI "hub-and-spoke" of Mason and the MuleSoft EAI page. The same words appear on Azure VNet / AWS Transit Gateway diagrams. That is a **lookalike graph**, not this style. Pick the column in the two-layer table before you pick E9.

The style replaces a fully-connected application graph with one adapter per participant and an **active mediator** that routes, translates, logs, and (sometimes) orchestrates. Hohpe (2003-11-12): a wheel has *n* edges; the fully-connected undirected graph has `n/2 · (n−1)` (4 → 6, 8 → 28); directed is `n · (n−1)`. The lasting benefit is not fewer cables — a "line" may already be a queue, topic, or URI — it is **location transparency that is real only with protocol translation and a Message Translator**. Without a **Canonical Domain Model**, n-square returns at *format*.

Quality attributes in play, stated without a star card — [style-selection](../../.cursor/skills/arch-style/references/style-selection.md) has **no Hub-and-spoke row**; do not invent one, and do not borrow ch17's "disastrous" or EDA's 4★/5★.

| Attribute | What the sources actually say | Not a rating |
|---|---|---|
| **Coupling / evolvability of *participants*** | Linear adapters (*n*) instead of pairwise maps (~n²). A new spoke is one adapter **if** a usable canonical exists. | No ★ cell |
| **Operability** | One place to log, route, and control flow (Hohpe). | No ★ cell |
| **Throughput / scale** | Hohpe: hub is a bottleneck; mitigate with stateless scale-out or a hierarchy. Mason: clustered shared-DB hub is "not good for high number of transactions"; scale is "bigger box." | Do not borrow EDA 4★ |
| **Fault isolation** | Mason EAI hub = **SPOF**. Mason ESB column (E6 adjacency) is the form that claims failure isolation. | Do not borrow microservices HI |
| **Simplicity / cost of start** | Mason: easy PoC, small number of points. Hohpe: a shared model that suits everyone is rare. | Do not invert E6's "simplicity/cost inverted" onto E9 |
| **Deploy / test** | **Not scored for E9.** "Disastrous" is ch17 SOA — **E6**. | Honest `—` |

Azure's *Architecture styles* catalog (N-tier, Web-Queue-Worker, Microservices, Event-driven, Big data, Big compute) does **not** list hub-and-spoke; Azure publishes the name under *networking*.

```
  app ----  HUB / BROKER  ---- app          spoke VNet ---- HUB VNet ---- spoke VNet
        INTEGRATION (messages)                     NETWORK (L3 / peering)
```

## Lineage and vocabulary

- **Hohpe, "Hub and Spoke…" (2003-11-12).** Airline / FedEx metaphor. Using a central Message Broker is "sometimes referred to as hub-and-spoke architectural style." Architecture pattern, peer of Pipes and Filters; internals are Message Routers. Location transparency is "only an illusion" without protocol translation **and** a Message Translator. A model that suits everyone is "all too rarely blessed with success." The motivating picture assumes a **fully connected, symmetric** graph; layered or tree-shaped services make n-square recede (the broker may still be a directory). Mitigate the bottleneck by "centrally configured at design-time, but distributed at run-time."
- **Hohpe, Message Broker / Canonical Data Model / Message Bus** (EIP public pages, fetched 2026-09-13). Broker: decouple destination from sender; keep **central control**. Scale-out if **stateless** (Point-to-Point Channel ⇒ one instance consumes each message). Specialized brokers avoid the "über-Message Broker," at the risk of "Message Broker spaghetti." **Hierarchy:** local broker for a "subnet," central only for cross-subnet. Canonical: independent common format. 2 apps → 2 direct translators vs 4 via canonical; 3 apps → 6 either way; 6 apps → **30** direct vs **12** canonical. Bus: common data model, command set, messaging infrastructure, Channel Adapters / Service Activators — the bus side of Mason's split, **not** the EAI hub.
- **Mason, "ESB and Hub n' Spoke Architectures" (2011-06-28).** **Two integration architectures, not one.** *Hub-and-spoke (EAI):* one location; usually application formats **directly** (no canonical); **state in a shared database**; scale by **clustering** ("vertical not horizontal"). Easy start; **small** number of points; PoC. Costs: **SPOF**; "not good for high number of transactions"; hard as systems accumulate; "bigger box." *ESB:* canonical (typically XML); message is the contract; **adapter per system**; bus decoupling; usually **stateless**. Add participants without loading a single point; failure isolation. Costs: up-front canonical + adapter architecture. Best when "more than a few applications" and growth is expected.
- **This conflict is the finding.** Hohpe's public pages treat hub-and-spoke *as* Message Broker and treat a canonical model as how you finish location transparency. Mason treats hub-and-spoke as the EAI form that usually *skips* canonical and parks state in a shared DB, and treats ESB as the *other* architecture. FSA files the ESB under **orchestration-driven SOA (E6)**, not as hub-and-spoke.
- **MuleSoft EAI page** (fetched 2026-09-13). Point-to-point: 3 systems → 3 connectors, 5 → 10, 8–9 → "the 30s" → broker / hub-and-spoke EAI → bus → ESB. Broker: loose (often async) coupling; central config. Costs: SPOF; bottleneck; "difficult … across large geographical distances"; often heavyweight proprietary. iPaaS on that page is a *hosting form*, not a third topology. The page's "vast majority failed" / "2003 … 70 percent" study is **unsourced** — excluded here.
- **Azure hub-spoke (network) + Architecture styles.** `hub-spoke.yml` `ms.date: 04/10/2026`. Hub VNet = shared networking, **regional**, primary egress. Spokes peer to **one hub in the same region** in most scenarios. Peering is **nontransitive**. CAF: hub in Connectivity subscription; spokes in application landing zones; **do not** deploy Application Gateway as a shared hub service. Traditional topology: customer-managed for single-region or multi-region **without** global transit; Virtual WAN when **more than two regions** plus global transit. VPN gateway: up to **100** tunnels. Application-style catalog: **hub-and-spoke absent.**
- **AWS Transit Gateway** + [ch09.md](../aws/ch09.md): "Hub and spoke design for connecting VPCs and on-premises networks"; Regional L3 virtual router. Peering mesh "hard to manage" past ~10 VPCs vs Transit Gateway. Extra gateways = blast-radius / admin isolation, not HA. [ch08.md](../aws/ch08.md) has **no** hub-spoke mention (Kafka *brokers* there are log servers).
- **Workspace plates that use the drawing, not the style.** [Figure 4-9](../data-intensive-design/medallion-foundation-tenancy.md): "Hub-and-spoke: onboarding is centralized; consume is federated" (org tenancy). [Figure 2-6](../fincancial-data-architecture/architecture-components.md): a plate that "does **not** match" the chapter's eight components.

## What the style is — and is not

**Is.** A topology that replaces a fully-connected *application* graph with a centre that brokers messages. Spoke-to-spoke application traffic always goes via the hub — that *is* the style.

**Is not.**

| Confusion | Why it is a different card |
|---|---|
| **Cloud WAN / VNet hub-spoke** | L3 packets, peering, firewall, VPN / ExpressRoute / Transit Gateway. Azure publishes it under *networking*. Does **not** integrate ERP with WMS. |
| **Orchestration-driven SOA / ESB (E6)** | FSA ch17 *style*: taxonomy + ESB / orchestration engine; **quanta = 1**; deploy/test "disastrous"; residual fit = "integration architecture over legacy." Mason treats ESB as a *different* integration architecture from the EAI hub. "We bought an ESB, therefore E9" is the collapse. |
| **EDA broker / mediator (E4)** | Event-*processor* topologies. Hohpe's Message Broker as an *integration architecture* is this card; an initiating→derived event graph is [E4](EventDriven.md). A request-driven hub that happens to use a queue is still E9. |
| **API gateway / BFF / "API hub" (C6)** | North-south façade for *one* product. CAF: do **not** put Application Gateway in the *network* hub. If every request is "forward HTTP to ERP unchanged," you wanted [C6](ApiGateway.md) or a direct call, not E9. |
| **Hohpe Message Bus** | Shared model + command set + infrastructure; participants speak the bus. Closer to Mason's ESB column / E6 adjacency than to the EAI hub. |
| **Point-to-point EAI** | The graph this style is meant to replace. |
| **An FSA style with stars** | **No matrix row.** Adjacent ESB ratings stay on E6. |
| **iPaaS SKU** | Hosting form of a hub, not a third topology. |

**E6 vs E9 vs C6.** E6 is the SOA *style* — historically taxonomy layers + a smart pipe / ESB / orchestration engine (style-selection: residual fit is integration over legacy; "in practice it has mostly been a disaster" as an *application* architecture; quanta = **1**), or today the modern service-based variant (UI + ≤12 coarse domain services, usually one DB). E9 is the *topology* of an active integration centre. C6 is the north-south edge of one product: TLS, authn, routing, optional aggregation — **"Business logic should never be offloaded to the gateway"** ([ApiGateway.md](ApiGateway.md)). An ESB can sit on a bus (Mason) or be scored as ch17 SOA; it does not become E9 by purchase order, and hub-spoke VNets do not become E9 by drawing.

Lewis & Fowler's SOA sidebar ([Microservices.md](Microservices.md)) is the same split from the other side: the common form they saw was ESBs integrating monoliths — **E6**, not independently deployable services, and not this card. [E4](EventDriven.md) already warns that a single über-mediator routing every domain is Hohpe's unmaintainable broker *and* style-selection's Accidental SOA: federate by domain; do not treat that mediator as "we adopted EDA."

## Decision mechanics

### Two layers

| | Integration (this card) | Network (lookalike) |
|---|---|---|
| Node | Application / package / SaaS | VNet / VPC / branch |
| Hub job | Route, transform, translate, (sometimes) orchestrate | Route IP; inspect; shared DNS / Bastion / firewall; hybrid gateway |
| Spoke-to-spoke | Always via the hub | Via hub NVA/UDRs, **or** extra peering / AVNM (Azure allows bypass) |
| Transitivity | The hub *creates* it | Peering is **nontransitive**; hub / Virtual WAN / TGW *adds* it |
| Hub failure | Integration stops (Mason SPOF) | Routing / egress / hybrid stops; a spoke may still run locally |
| Scale | Cluster (Mason); stateless multi-instance or hierarchy (Hohpe) | Hub SKU / extra regional hubs / Virtual WAN |
| Canonical | Optional (Hohpe: required for real location transparency); Mason hub often **skips** it | CIDR plan; no application schema |

If a review cannot say which column it is in, it is not ready to pick E9.

### Integration mechanics

1. **Edge reduction.** Connectors grow ~n². Hub: one adapter per participant.

| Participants | Undirected edges (Hohpe `n/2 · (n−1)`) | Directed (Hohpe `n · (n−1)`) | MuleSoft / Mason point-to-point gloss |
|---|---|---|---|
| 3 | 3 | 6 | 3 connectors |
| 4 | **6** | **12** | — |
| 5 | 10 | 20 | 10 connectors |
| 6 | 15 | 30 | Canonical page: **30** direct translators vs **12** via canonical |
| 8 | **28** | 56 | 8–9 systems → "the 30s" |

A wheel has *n* edges. The physical-cable count is not always the pain — Hohpe: a "line" may already be a queue, topic, or URI.

2. **Active mediation.** Sender does not know the receiver's location or, with a translator, its format (Hohpe). Mason's hub usually maps **application formats directly** — cheaper start; n-square returns at metadata.
3. **State.** Mason: shared DB on the hub; cluster. Hohpe: prefer **stateless** internals so many instances can run (Point-to-Point Channel ⇒ one instance consumes each message).
4. **Canonical model.** Hohpe / Canonical Data Model: *n* or 2*n* unidirectional maps instead of n². Break-even vs pairwise is early (3 apps: 6 either way). The usual walk from EAI hub toward ESB / Message Bus is an **E6 adjacency**, not a rename of this card.
5. **Hierarchy.** Local brokers for a "subnet" of apps; central only for cross-subnet. Same *shape* as multi-hub WAN, still messages. Specialized brokers avoid the über-broker and risk "Message Broker spaghetti."

### Hohpe vs Mason — pick the fork, do not average them

| Fork | Hohpe Message Broker | Mason EAI hub |
|---|---|---|
| Canonical | How location transparency *finishes* | Usually **skipped**; app formats mapped directly |
| State | Prefer stateless so instances scale out | Shared DB; cluster ("vertical not horizontal") |
| Scale story | Design-time centre, run-time distribution; or a hierarchy | "Bigger box" |
| Exit when volume grows | Stateless multi-instance / hierarchy | ESB / bus — Mason's *other* architecture (E6 adjacency) |
| Best fit he names | Dense symmetric graph + translation investment | Small number of points; PoC; integration layer for *an* application |

Averaging the two into "the hub-and-spoke style" hides the decision. A review that cannot say whether the hub holds a shared DB and pairwise maps, or a canonical model and stateless instances, is not ready to operate the centre — let alone to call it E6 or E2.

### Quantum count — not a style-selection FACT

No Hub-and-spoke row ⇒ no official quanta cell. Do not score E9. Do not print stars.

Ch7 machinery still applies to *whatever you built*: the database is inside the quantum; a single shared DB ⇒ quantum of one.

| Claim | Status |
|---|---|
| Orchestration-driven SOA = **1** quantum | FACT, style-selection ch17 — **E6**, not E9 |
| Mason hub shared-DB + cluster | Matches ch7 "shared DB ⇒ quantum of one" **for the hub process** |
| Spoke apps may already be their own deployables / DBs | The style inserts a mediator; it does not split them |
| "Typical E9 = 1 + N spokes" | **Not in style-selection.** Plausible; **not a catalog FACT** |
| Network hub-spoke quantum | **Not a software-architecture quantum question** |

Declaring the hub a microservice while it still owns a shared integration DB and returns synchronously does not create extra quanta (ch7).

### Worked example — four systems, two layers

**Integration (the style).** Retailer: an e-commerce order must land in ERP, WMS, CRM. Point-to-point: Hohpe undirected `4/2 · 3 = 6`; directed `4 · 3 = 12` if every system both sends and receives. A WMS vendor change touches every partner that mapped to it. Hub: four adapters; e-commerce emits "order placed"; hub validates, translates, routes. Adding loyalty is one adapter **if** a usable canonical order exists, else another pairwise map inside the hub. Mason's "small / PoC" bar fits four.

Two forks on the same four systems:

- **Mason start.** Hub stores in-flight state in a shared DB; maps e-commerce XML to ERP IDoc, WMS flat file, CRM SOAP *directly*. Week one is cheap. The fifth package (loyalty) adds three more maps, not one. Volume growth means a bigger cluster, not another instance of a stateless broker. This is the SPOF form.
- **Hohpe finish.** A canonical `Order` plus four maps (or eight unidirectional). Location transparency is real. The fifth package maps only to canonical. The hub process can be run in several instances *if* internals are stateless and the channel is Point-to-Point. Walking from here onto a bus (common command set, Channel Adapters) is Mason's ESB column — file that move as **E6**, do not relabel the card.

**What this example does not decide.** Channel type (queue vs topic vs URI) is [A2](PubSubQueues.md). A north-south HTTP façade in front of e-commerce is [C6](ApiGateway.md). If the hub starts owning the *order workflow* as an application — steps, restarts, compensation — you have walked toward **E6** residual SOA (or an [E4](EventDriven.md) mediator), not "done E9 harder."

**Network cut (not the style).** Four spoke VNets peered to a hub with Firewall + ExpressRoute. The hub VNet does not create the ERP order. CAF: Application Gateway lives **in the e-commerce spoke**. Kill the integration hub: no new orders in ERP / WMS / CRM; UIs still serve. Kill the network hub firewall: spoke-to-internet and spoke-to-spoke-via-hub stop; a spoke that only needs its local DB may still work. Different incidents.

## When to use / when not / migration

**When — integration.** Hohpe: dense graph; location transparency + central flow control; invest in translation (preferably canonical). Mason: **small** number of points; PoC; "integration layer for an application"; accept clustering. EAI page: packaged / legacy that cannot be changed. FSA ch17 (E6 adjacency): residual "integration architecture over legacy" — not a reason to start a *new* application as a hub.

**When — network (not E9-as-style).** Azure: shared DNS / NTP / AD / firewall; landing-zone split. CAF: single region, or multi-region **without** global transit; VPN **< 100** tunnels/gateway. AWS ch09 + TGW: more VPCs than a peering mesh wants (~10 in ch09); hybrid VPN / DX onto one Regional router.

**When not — integration.** Graph already a **tree / layered** (Hohpe "Your Mileage") → direct calls or a thin directory. High volume + "bigger box" is the only lever (Mason) → ESB / Message Bus (E6 adjacency) or [E4](EventDriven.md). Canonical cannot be agreed → scoped pair-maps or ACL ([E2](Microservices.md) / E10). Greenfield + DB-per-service → **E2**. HTTP edge for one product → **C6**. Domain workflow in the *network* hub → wrong layer.

**When not — network.** Same-region low-latency spoke-to-spoke that must not hairpin a firewall (Azure: peer / AVNM; Private Link). Global transit (CAF → Virtual WAN). Peering mesh of a **few** VPCs (ch09: peering wins on cost/latency when N is small).

**In (integration).** Point-to-point spaghetti (Hohpe 8-node / 28-edge). In-process "integration layer" about to be reused. Vendor EAI lift. iPaaS is **hosting**, not a new topology.

**Out, cheapest first.** (1) Canonical inside the hub (still one quantum if the DB stays shared). (2) Adapters + bus (Mason ESB; Hohpe Message Bus) → **E6** residual. (3) Broker hierarchy. (4) Strangle a spoke ([B4](StranglerFig.md)) with own API ([C6](ApiGateway.md)) / events ([E4](EventDriven.md) / [A2](PubSubQueues.md)). (5) Do **not** declare the hub a microservice — shared integration DB + sync returns is still one hub quantum (ch7).

**In (network).** Peering mesh unmanageable (ch09); hybrid on-ramp; landing-zone standard. **Out.** Virtual WAN; selective **direct** spoke peering; extra regional hubs when one ExpressRoute / firewall SKU ceilings out.

Do **not** migrate an integration problem by adding a Transit Gateway, or a network problem by buying an ESB.

## When not to use

Do **not** pick integration hub-and-spoke as the macro *application* style when:

- the graph is already a **tree or layered** — Hohpe's "Your Mileage": n-square recedes; a directory may be enough;
- volume will outgrow a clustered shared-DB hub and "bigger box" is the only lever (Mason);
- a canonical model cannot be afforded or agreed — you will pay n-square at metadata, which is the original pain in a new place;
- you are building new independently deployable services with DB-per-service — that is **E2**, and Lewis & Fowler's minimum centralized management is the opposite bet;
- the need is an HTTP edge for one product — **C6**;
- the need is react-to-facts-that-happened among processors you already own — **E4**, not a Message Broker as the application;
- you are starting a *new* application and the only citation is FSA ch17 residual "integration over legacy" — that residual is **E6**, and it is not a reason to begin here.

Do **not** pick E9 *at all* if the problem is VNet isolation, hybrid on-ramp, or landing-zone split. That topology can sit *under* E2, E4, or a monolith without becoming this style.

## Failure modes

The distinctive failure of this style is the **hub as SPOF**. On Mason's form it is definitional: one location, shared DB, cluster. When that centre is down or saturated, *every* integration that went through it stops — ERP, WMS, and CRM go quiet together, even if each package is healthy. Hohpe names the same shape as a **throughput bottleneck** and offers the mitigations (stateless instances, design-time centre / run-time distribution, hierarchy). Those mitigations do not appear for free on a clustered EAI box: if the hub still holds the only copy of in-flight state, extra instances are not extra quanta and not extra fate. The network lookalike has a *different* outage: kill the hub firewall and spoke-to-spoke-via-hub plus egress die; a spoke that only needs its local DB may still serve. Do not rehearse one incident and call it the other.

The other failures are how teams *get* to that SPOF, or how they misname it.

| Failure | Looks like | Counter |
|---|---|---|
| **Hub as SPOF / bottleneck** | All integrations die or queue when the centre is down or saturated | Hohpe: stateless multi-instance, design-time centre / run-time distribution, or a hierarchy. Mason: that clustered shared-DB hub *is* the SPOF — exit toward ESB / bus. |
| **Layer mix-up** | "We have hub-spoke, so ERP is integrated" | Name the two-layer column first |
| **Style / topology collapse** | "We bought an ESB, therefore E9" (or E6) | Mason: ESB ≠ EAI hub; FSA: ESB lives in E6 |
| **n-square at metadata** | Translator per pair inside the hub | Canonical maps, or admit pairwise cost |
| **Über-broker** | One unmaintainable centre | Hohpe hierarchy; split by subdomain |
| **Canonical-model politics** | Year-long schema committee | Bounded-context maps; ACL; stop |
| **Hub as the application** | New features land in the broker | E6 residual only over *legacy* |
| **Gateway-in-the-hub** | Shared Application Gateway in the connectivity VNet | C6 with the workload spoke |
| **Nontransitive surprise** | Spoke A cannot reach B after both peer to the hub | UDRs + NVA, TGW tables, or extra peering — *on purpose* (network lookalike) |
| **Distributed-layers cousin** | "Services" still sharing the hub DB | Split persistence before claiming extra quanta |

## Trade-offs

No FSA stars. Trade-offs of *choosing the integration hub*.

| Choice | Buys | Costs | Source |
|---|---|---|---|
| Hub vs point-to-point | Linear connectors (*n* vs ~n²); one place to log / control flow | Two hops + routing; throughput bottleneck | Hohpe 2003-11-12 |
| App formats in the hub (no canonical) | Fast start; no schema committee | n-square returns at *metadata* | Hohpe; Mason 2011 |
| Canonical domain model | *n* or 2*n* maps; location transparency is real | One model that "suits every participant" is rare | Hohpe; Canonical Data Model (6 apps: 30 vs 12) |
| Shared-DB clustered hub | Simple ops; PoC / few systems | SPOF; vertical scale; "not good for high number of transactions" | Mason 2011-06-28 |
| Stateless multi-instance broker | Throughput without a single process | Design-time centre still coupled; need Point-to-Point semantics | Hohpe Message Broker |
| Broker hierarchy | Avoids the über-broker | "Message Broker spaghetti" | Hohpe Message Broker |
| Hub as the *application* style | Residual fit over legacy (E6 adjacency) | Deploy/test "disastrous" is **E6, not E9** | style-selection ch17 |
| Adapters on a bus (ESB) | Horizontal add; failure isolation | Up-front canonical + adapter architecture | Mason 2011; Message Bus |
| Network hub-spoke *instead* | Shared firewall / DNS / hybrid on-ramp | Does **not** integrate applications | Azure 2026-04-10; AWS TGW |

No library-defaults section — Group E has none. iPaaS SKUs, vendor broker product defaults, and WAN gateway limits beyond the dated facts below stay out.

### Dated facts (not library defaults)

| Fact | Value | Source |
|---|---|---|
| style-selection row / FSA stars for E9 | **None — do not invent** | `style-selection.md` |
| Adjacent SOA quanta (E6) | **1** | style-selection ch17 |
| Edges | `n/2 · (n−1)` undirected; `n · (n−1)` directed; 4→6, 8→28 | Hohpe 2003-11-12 |
| Canonical maps | rambling: *n* or 2*n* vs n²; pattern: 2 apps 2 vs 4; 3=6; 6 apps **30 vs 12** | Hohpe + Canonical Data Model |
| Mason hub state | Shared DB; cluster to scale | 2011-06-28 |
| Azure hub-spoke `ms.date` | **2026-04-10**; peering nontransitive; hub regional | Architecture Center |
| CAF VPN heuristic | **< 100** tunnels/gateway for traditional hub-spoke | CAF traditional topology |
| Azure application-style catalog includes E9? | **No** | Architecture styles page |

All numeric rows fetched **2026-09-13**. No invented SLAs.

## Sources

Verified 2026-09-13; the full URL list, per-claim provenance, and items deliberately left out (invented FSA stars, typical "1 + N" quantum as FACT, unsourced "70 percent" study, unfetched O'Reilly *Integration Hubs* video) are in the [external research note](../../docs/research/sysdesign/e9-hub-and-spoke-external-research.md). Adjacent SOA quanta (**1**) and "disastrous" deploy/test are **E6** facts from [style-selection.md](../../.cursor/skills/arch-style/references/style-selection.md) ch17. Items already in this tree are cited, not rewritten.

- Integration: Hohpe, *Hub and Spoke* (2003-11-12); EIP Message Broker, Canonical Data Model, Message Bus; Mason, *ESB and Hub n' Spoke Architectures* (2011-06-28); MuleSoft EAI page (hosting-form claim only).
- Network lookalike: Azure Architecture Center hub-spoke (`ms.date` 2026-04-10) and *Architecture styles* (E9 absent); CAF traditional topology (VPN **< 100** tunnels/gateway); AWS Transit Gateway whitepaper + how-it-works; [ch09.md](../aws/ch09.md).
- Workspace: style-selection.md (no E9 row); [ch08.md](../aws/ch08.md) (does **not** mention hub-spoke); [E4](EventDriven.md); [C6](ApiGateway.md); [E2](Microservices.md); Figure 4-9; Figure 2-6.
