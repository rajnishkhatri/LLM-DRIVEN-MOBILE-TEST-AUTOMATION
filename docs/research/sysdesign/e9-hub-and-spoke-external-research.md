---
type: research
title: 'Hub-and-spoke — external research (2026-09-13)'
description: >-
  Group E decision-depth pass for catalog E9: integration hub-and-spoke
  (Hohpe Message Broker / EAI broker) versus cloud WAN hub-spoke (Azure
  VNet, AWS Transit Gateway). style-selection.md has no row. No invented
  Richards & Ford star card.
tags: [research, system-design-patterns, E9, hub-and-spoke]
---

# Hub-and-spoke — external research (2026-09-13)

> Evidence pass for catalog **E9** (Group E). Not a Concept. Fetched
> 2026-09-13. Paraphrase; numbers exact. Unverified claims live in §8.
> **No library-defaults.** **Did not** run arch-style scoring.
>
> **SoT:** [`style-selection.md`](../../../.cursor/skills/arch-style/references/style-selection.md)
> (FSA; ch7, ch9–19). Matrix has Layered, Modular monolith, Pipeline,
> Microkernel, Service-based, Event-driven, Space-based,
> Orchestration-driven SOA, Microservices. **No Hub-and-spoke row.**
> **Do not invent stars.** Adjacent ESB is **E6**: taxonomy +
> ESB/orchestration engine; **quanta = 1**; deploy/test “disastrous”;
> simplicity/cost inverted.
>
> **Cite, do not rewrite.** [`ch08.md`](../../../cases/aws/ch08.md)
> (no hub-spoke string; gateway vs mesh; Kafka *brokers* as log
> servers), [`ch09.md`](../../../cases/aws/ch09.md) (VPC mesh vs
> Transit Gateway), [Figure 4-9](/Users/rajnishkhatri/Code/LLM-DRIVEN-MOBILE-TEST-AUTOMATION/cases/data-intensive-design/medallion-foundation-tenancy.md)
> (central onboarding, federated consume),
> [Figure 2-6](/Users/rajnishkhatri/Code/LLM-DRIVEN-MOBILE-TEST-AUTOMATION/cases/fincancial-data-architecture/architecture-components.md)
> (plate, not a style). Siblings: [E6](e6-soa-external-research.md),
> [E4](e4-event-driven-external-research.md), [C6](c6-api-gateway-external-research.md).

---

## 1. Scope and non-goals

**Owns** the *name* “hub-and-spoke” as it appears in two layers that
share a graph metaphor and almost nothing else. **This catalog card
carries meaning (1): enterprise integration hub** (active Message
Broker / EAI broker). Meaning (2) is a **lookalike**, not the style.

| Layer | Hub | Spoke | Traffic |
|---|---|---|---|
| **(1) Integration — this card** | Message Broker / EAI hub / iPaaS runtime: route, transform, translate protocol | Application, package, or SaaS adapter | Application messages |
| **(2) Network / WAN — lookalike** | Regional transit VNet / Transit Gateway: firewall, VPN/ExpressRoute, DNS | Workload VNet / VPC | IP packets |

Azure’s *Architecture styles* catalog (N-tier, Web-Queue-Worker,
Microservices, Event-driven, Big data, Big compute) does **not** list
hub-and-spoke; Azure publishes it under *networking*.

**What (1) is.** A topology that replaces a fully-connected
application graph with a centre that *brokers* messages. Hohpe
2003-11-12: undirected `n/2 · (n−1)`; directed `n · (n−1)`; 4 → 6,
8 → 28; a wheel has *n* edges. Hub decouples sender from receiver
(routing, logging, flow control). He: commonly referred to as
**Message Broker**. Pattern page: “Using a central Message Broker is
sometimes referred to as hub-and-spoke architectural style.”
Architecture pattern (peer of Pipes and Filters); internals are
Message Routers.

**What it is not.** Cloud WAN / VNet topology (Azure/AWS L3).
**Orchestration-driven SOA (E6)** — FSA ch17 *style* (taxonomy +
ESB, quanta = 1); Mason treats ESB as a *different* integration
architecture. **EDA broker/mediator (E4)** — event-*processor*
topologies. **API gateway / BFF / “API hub” (C6)** — north-south
façade; CAF: do **not** put Application Gateway in the *network*
hub. Point-to-point EAI. Hohpe **Message Bus** (closer to Mason’s
ESB column). An FSA style — **no matrix row**.

**Stays in siblings:** E6 (SOA *style* / residual “integration over
legacy”); E4; E2 (Lewis & Fowler: minimum centralized management);
C6; A2 (channels a hub may *use*); B4. **Non-goals.** Library
defaults. Scoring. Invented FSA stars. iPaaS SKUs as the style.
Hohpe book body beyond public pages. A Concept.

---

## 2. Lineage / vocabulary

**Hohpe, “Hub and Spoke…” (2003-11-12).**
https://www.enterpriseintegrationpatterns.com/ramblings/03_hubandspoke.html
— fetched 2026-09-13. Airline/FedEx metaphor. A “line” may be a
queue, topic, or URI — *physical* edge-count is not always the pain.
Lasting benefit: **active mediator**. Location transparency is “only
an illusion” without protocol translation **and** a Message
Translator. Without a **Canonical Domain Model** (vs “Semantic
Hub-and-Spoke” / “metadata hub”), n-square returns at *format*:
`n/2 · (n−1)` translators, or *n* (2*n* unidirectional) if each
participant maps only to canonical. Costs: **two hops** + routing;
hub as **throughput bottleneck**; mitigate by “centrally configured
at design-time, but distributed at run-time.” A model that suits
everyone is “all too rarely blessed with success.” Motivating
picture assumes a **fully connected, symmetric** graph; layered /
tree-shaped services make n-square recede (broker may still be a
directory).

**Message Broker / Canonical Data Model / Message Bus** (EIP public
pages, fetched 2026-09-13). Broker: decouple destination from
sender; keep **central control**. Scale-out if **stateless**
(Point-to-Point Channel ⇒ one instance consumes each message).
Specialized brokers avoid the “über-Message Broker,” risk “Message
Broker spaghetti.” **Hierarchy:** local broker for a “subnet,”
central only for cross-subnet (he compares this to a *network* of
subnets). Canonical: independent common format. 2 apps → 2 direct
translators vs 4 via canonical; 3 apps → 6 either way; 6 apps →
**30** direct vs **12** canonical. Bus: common data model, command
set, messaging infrastructure, Channel Adapters / Service
Activators — bus side of Mason’s split, not the EAI hub.

**Mason, “ESB and Hub n’ Spoke Architectures” (2011-06-28).**
https://blogs.mulesoft.com/dev-guides/how-to-tutorials/esb-or-not-to-esb-revisited-part-2/
— fetched 2026-09-13. **Two integration architectures, not one.**

- *Hub-and-spoke (EAI):* one location; usually application formats
  **directly** (no canonical); **state in a shared database**; scale
  by **clustering** (“vertical not horizontal”). Easy start; **small**
  number of points; PoC. Costs: **SPOF**; “not good for high number
  of transactions”; hard as systems accumulate; “bigger box.”
- *ESB:* canonical (typically XML); message is the contract;
  **adapter per system**; bus decoupling; usually **stateless**.
  Add participants without loading a single point; failure
  isolation. Costs: up-front canonical + adapter architecture. Best
  when “more than a few applications” and growth is expected.

**This conflict is the finding.** Hohpe’s public pages treat
hub-and-spoke *as* Message Broker and treat a canonical model as
how you finish location transparency. Mason treats hub-and-spoke as
the EAI form that usually *skips* canonical and parks state in a
shared DB, and treats ESB as the *other* architecture. FSA files the
ESB under **orchestration-driven SOA (E6)**, not as hub-and-spoke.
Azure/AWS reuse the same words for **L3**. These are not one style.

**MuleSoft EAI page.**
https://www.mulesoft.com/integration/enterprise-application-integration-and-esb
— fetched 2026-09-13. Point-to-point: 3 systems → 3 connectors, 5 →
10, 8–9 → “the 30s” → broker / hub-and-spoke EAI → bus → ESB. Broker:
loose (often async) coupling; central config. Costs: SPOF; bottleneck;
“difficult … across large geographical distances”; often heavyweight
proprietary. “Vast majority” failed + “2003 … 70 percent” study is
**unsourced** (§8). iPaaS on that page is a *hosting form*, not a
third topology.

**Azure hub-spoke (network) + *Architecture styles*.**
https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/hub-spoke
— `hub-spoke.yml` `ms.date: 04/10/2026`. Hub VNet = shared
networking, **regional**, primary egress. Spokes peer to **one hub
in the same region** in most scenarios. Peering is **nontransitive**.
CAF: hub in Connectivity subscription; spokes in application landing
zones; **do not** deploy Application Gateway as a shared hub
service. Traditional topology: customer-managed for single-region
or multi-region **without** global transit; Virtual WAN when
**more than two regions** plus global transit. VPN gateway: up to
**100** tunnels. Architecture-styles catalog: **hub-and-spoke
absent.**

**AWS Transit Gateway.**
https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/transit-gateway.html
— “Hub and spoke design for connecting VPCs and on-premises
networks”; Regional L3 virtual router; extra gateways = blast-radius
/ admin isolation, not HA. [`ch09.md`](../../../cases/aws/ch09.md):
peering mesh “hard to manage” past ~10 VPCs vs Transit Gateway.

**Workspace plates that use the drawing, not the style.** Figure 4-9:
“Hub-and-spoke: onboarding is centralized; consume is federated”
(org tenancy). Figure 2-6: a plate that “does **not** match” the
chapter’s eight components. `ch08.md` has **no** hub-spoke mention.

---

## 3. Mechanics (Group E depth bar)

### 3.1 Two topologies

```
  app ----  HUB / BROKER  ---- app          spoke VNet ---- HUB VNet ---- spoke VNet
        INTEGRATION (messages)                     NETWORK (L3 / peering)
```

| | Integration (E9) | Network (lookalike) |
|---|---|---|
| Node | Application / package / SaaS | VNet / VPC / branch |
| Hub job | Route, transform, translate, (sometimes) orchestrate | Route IP; inspect; shared DNS/Bastion/firewall; hybrid gateway |
| Spoke-to-spoke | Always via the hub (that *is* the style) | Via hub NVA/UDRs, **or** extra peering / AVNM (Azure allows bypass) |
| Transitivity | The hub *creates* it | Peering is **nontransitive**; hub / Virtual WAN / TGW *adds* it |
| Hub failure | Integration stops (Mason SPOF) | Routing / egress / hybrid stops; a spoke may still run locally |
| Scale | Cluster (Mason); stateless multi-instance or hierarchy (Hohpe) | Hub SKU / extra regional hubs / Virtual WAN |
| Canonical | Optional (Hohpe: required for real location transparency); Mason hub often **skips** it | CIDR plan; no application schema |

If a review cannot say which column it is in, it is not ready to
pick E9.

**E6 vs E9.** E6 is the SOA *style* (taxonomy + smart pipe, or the
modern ≤12-service variant). E9 is the *topology* of an active
centre. An ESB can sit on a bus (Mason) or be scored as ch17 SOA
(style-selection). “We have an ESB, therefore E9” or “we have
hub-spoke VNets, therefore E9” is the layer mix-up.

### 3.2 Integration mechanics

1. **Edge reduction.** Connectors grow ~n² (Hohpe; Mason 3 / 10 /
   “30s”). Hub: one adapter per participant.
2. **Active mediation.** Sender does not know the receiver’s location
   or, with a translator, its format (Hohpe). Mason hub usually maps
   **application formats directly** — cheaper start; n-square returns
   at metadata.
3. **State.** Mason: shared DB on the hub; cluster. Hohpe: prefer
   **stateless** internals so many instances can run.
4. **Canonical model.** Hohpe / Canonical Data Model: *n* or 2*n*
   maps instead of n². Usual walk from EAI hub toward ESB / Message
   Bus (E6 adjacency).
5. **Hierarchy.** Local brokers for a “subnet” of apps; central only
   for cross-subnet. Same *shape* as multi-hub WAN, still messages.

### 3.3 Quantum count — **not a style-selection FACT**

No Hub-and-spoke row ⇒ no official quanta cell. Ch7 machinery: the
DB is inside the quantum; single shared DB ⇒ quantum of one.

| Claim | Status |
|---|---|
| Orchestration-driven SOA = **1** quantum | FACT, style-selection ch17 — **E6**, not E9 |
| Mason hub shared-DB + cluster | Matches ch7 “shared DB ⇒ quantum of one” **for the hub process** |
| Spoke apps may already be their own deployables / DBs | The style inserts a mediator; it does not split them |
| “Typical E9 = 1 + N spokes” | **Not in style-selection.** Plausible; **uncertain** as a catalog FACT (§8) |
| Network hub-spoke quantum | **Not a software-architecture quantum question** |

Do not score E9. Do not print stars.

### 3.4 Worked example — four systems, two layers

**Integration.** Retailer: e-commerce order must land in ERP, WMS,
CRM. Point-to-point: Hohpe undirected `4/2 · 3 = 6`; directed
`4 · 3 = 12` if every system both sends and receives. A WMS vendor
change touches every partner that mapped to it. Hub: four adapters;
e-commerce emits “order placed”; hub validates, translates, routes.
Adding loyalty is one adapter **if** a usable canonical order
exists, else another pairwise map inside the hub. Mason’s “small /
PoC” bar fits four. If every request is “forward HTTP to ERP
unchanged,” you wanted C6 or a direct call, not E9.

**Network cut (not the style).** Four spoke VNets peered to a hub
with Firewall + ExpressRoute. The hub VNet does not create the ERP
order. CAF: Application Gateway lives **in the e-commerce spoke**.
Kill the integration hub: no new orders in ERP/WMS/CRM; UIs still
serve. Kill the network hub firewall: spoke-to-internet and
spoke-to-spoke-via-hub stop; a spoke that only needs its local DB
may still work. Different incidents.

### 3.5 When to use / when not / migration

**When — integration.** Hohpe: dense graph; location transparency +
central flow control; invest in translation (preferably canonical).
Mason: **small** number of points; PoC; “integration layer for an
application”; accept clustering. EAI page: packaged/legacy that
cannot be changed. FSA ch17 (E6 adjacency): residual “integration
architecture over legacy” — not a reason to start a *new*
application as a hub.

**When — network (not E9-as-style).** Azure: shared DNS/NTP/AD/
firewall; landing-zone split. CAF: single region, or multi-region
**without** global transit; VPN **< 100** tunnels/gateway. AWS
ch09 + TGW: more VPCs than a peering mesh wants (~10 in ch09);
hybrid VPN/DX onto one Regional router.

**When not — integration.** Graph already a **tree / layered**
(Hohpe “Your Mileage”) → direct calls or a thin directory. High
volume + “bigger box” is the only lever (Mason) → ESB / Message Bus
(E6 adjacency) or E4. Canonical cannot be agreed → scoped pair-maps
or ACL (E2/E10). Greenfield + DB-per-service → **E2**. HTTP edge
for one product → **C6**. Domain workflow in the *network* hub →
wrong layer.

**When not — network.** Same-region low-latency spoke-to-spoke that
must not hairpin a firewall (Azure: peer / AVNM; Private Link).
Global transit (CAF → Virtual WAN). Peering mesh of a **few** VPCs
(ch09: peering wins on cost/latency when N is small).

**In (integration).** Point-to-point spaghetti (Hohpe 8-node /
28-edge). In-process “integration layer” about to be reused. Vendor
EAI lift. iPaaS is **hosting**, not a new topology. **Out, cheapest
first:** (1) canonical inside the hub (still one quantum if the DB
stays shared); (2) adapters + bus (Mason ESB; Hohpe Message Bus) →
**E6** residual; (3) broker hierarchy; (4) strangle a spoke (**B4**)
with own API (**C6**) / events (E4/A2/B7); (5) do **not** declare
the hub a microservice — shared integration DB + sync returns is
still one hub quantum (ch7).

**In (network).** Peering mesh unmanageable (ch09); hybrid on-ramp;
landing-zone standard. **Out.** Virtual WAN; selective **direct**
spoke peering; extra regional hubs when one ExpressRoute / firewall
SKU ceilings out.

**Do not** migrate an integration problem by adding a Transit
Gateway, or a network problem by buying an ESB.

### 3.7 Trade-off table (integration style)

No FSA stars. Trade-offs of *choosing the integration hub*.

| Choice | Buys | Costs | Source |
|---|---|---|---|
| Hub vs point-to-point | Linear connectors (*n* vs ~n²); one place to log / control flow | Two hops + routing; throughput bottleneck | Hohpe 2003-11-12 |
| App formats in the hub (no canonical) | Fast start; no schema committee | n-square returns at *metadata* | Hohpe; Mason 2011 |
| Canonical domain model | *n* or 2*n* maps; location transparency is real | One model that “suits every participant” is rare | Hohpe; Canonical Data Model (6 apps: 30 vs 12) |
| Shared-DB clustered hub | Simple ops; PoC / few systems | SPOF; vertical scale; “not good for high number of transactions” | Mason 2011-06-28 |
| Stateless multi-instance broker | Throughput without a single process | Design-time centre still coupled; need Point-to-Point semantics | Hohpe Message Broker |
| Broker hierarchy | Avoids the über-broker | “Message Broker spaghetti” | Hohpe Message Broker |
| Hub as the *application* style | Residual fit over legacy (E6 adjacency) | Deploy/test “disastrous” is **E6, not E9** | style-selection ch17 |
| Adapters on a bus (ESB) | Horizontal add; failure isolation | Up-front canonical + adapter architecture | Mason 2011; Message Bus |
| Network hub-spoke *instead* | Shared firewall/DNS/hybrid on-ramp | Does **not** integrate applications | Azure 2026-04-10; AWS TGW |

---
## 4. Verified defaults / standards

Omitted as a **library-defaults** section (`_agent-brief.md`). Dated
facts that exist:

| Fact | Value | Source |
|---|---|---|
| style-selection row / FSA stars for E9 | **None — do not invent** | `style-selection.md` |
| Adjacent SOA quanta (E6) | **1** | style-selection ch17 |
| Edges | `n/2 · (n−1)` undirected; `n · (n−1)` directed; 4→6, 8→28 | Hohpe 2003-11-12 |
| Canonical maps | rambling: *n* or 2*n* vs n²; pattern: 2 apps 2 vs 4; 3=6; 6 apps **30 vs 12** | Hohpe + Canonical Data Model |
| Mason hub state | Shared DB; cluster to scale | 2011-06-28 |
| Azure hub-spoke `ms.date` | **2026-04-10**; peering nontransitive; hub regional | `hub-spoke.yml` + Architecture Center |
| CAF VPN heuristic | **< 100** tunnels/gateway for traditional hub-spoke | CAF traditional topology |
| AWS TGW | Regional L3 hub-and-spoke | whitepaper + how-it-works |
| Azure application-style catalog includes E9? | **No** | Architecture styles page |

All numeric rows fetched **2026-09-13**.

---
## 5. Failure modes and when-not-to-use

| Failure | Looks like | Counter |
|---|---|---|
| **Layer mix-up** | “We have hub-spoke, so ERP is integrated” | Name the §3.1 column first |
| **Style/topology collapse** | “We bought an ESB, therefore E9” (or E6) | Mason: ESB ≠ EAI hub; FSA: ESB lives in E6 |
| **n-square at metadata** | Translator per pair | Canonical maps, or admit pairwise cost |
| **Über-broker** | One unmaintainable centre | Hohpe hierarchy; split by subdomain |
| **SPOF / bottleneck** | All integrations die or queue | Stateless scale-out; ESB/bus |
| **Canonical-model politics** | Year-long schema committee | Bounded-context maps; ACL; stop |
| **Hub as application** | New features land in the broker | E6 residual only over *legacy* |
| **Gateway-in-the-hub** | Shared Application Gateway in the connectivity VNet | C6 with the workload spoke |
| **Nontransitive surprise** | Spoke A cannot reach B after both peer to the hub | UDRs + NVA, TGW tables, or extra peering — *on purpose* |
| **Distributed-layers cousin** | “Services” still sharing the hub DB | Split persistence before claiming extra quanta |

**Do not pick integration hub-and-spoke** as the macro application
style when the graph is not dense, volume will outgrow a clustered
hub, a canonical model cannot be afforded, or you are building new
independently deployable services. **Do not pick it at all** if the
problem is VNet isolation — that topology can sit *under* E2, E4,
or a monolith without becoming E9.

---
## 6. Cross-links

**E6** — ESB / orchestration engine (ch17, quanta = 1); Mason’s ESB
column is the usual *exit* from EAI hub. Do not merge. **E4** —
Hohpe Message Broker is E9, not EDA. **E2** — opposite
centralization. **C6** — north-south of *one* product; L7 inbound
stays in the spoke. **A2** — channels. **B4** — how a spoke leaves.
`style-selection.md` — **no E9 row**. `ch08.md` — **does not mention
hub-spoke**. `ch09.md` — VPC peering vs Transit Gateway
(**network**). Figure 4-9 — org-shape. Figure 2-6 — plate. Catalog
E9 row — status only; this note does not edit it.

---
## 7. Sources

Retrieved **2026-09-13**.

**Integration.** https://www.enterpriseintegrationpatterns.com/ramblings/03_hubandspoke.html (2003-11-12) · https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageBroker.html · https://www.enterpriseintegrationpatterns.com/patterns/messaging/CanonicalDataModel.html · https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageBus.html · https://blogs.mulesoft.com/dev-guides/how-to-tutorials/esb-or-not-to-esb-revisited-part-2/ (Mason, 2011-06-28) · https://www.mulesoft.com/integration/enterprise-application-integration-and-esb

**Network.** https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/hub-spoke (`ms.date` 2026-04-10) · https://raw.githubusercontent.com/MicrosoftDocs/architecture-center/main/docs/networking/architecture/hub-spoke.yml · https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/traditional-azure-networking-topology · https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/ · https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/transit-gateway.html · https://docs.aws.amazon.com/vpc/latest/tgw/how-transit-gateways-work.html

**Workspace.** `style-selection.md` · `cases/aws/ch08.md` ·
`cases/aws/ch09.md` · `medallion-foundation-tenancy.md` (main) ·
`architecture-components.md` (main) · catalog E9 row · E4 / E6 / C6
notes.

---
## 8. Uncertain / left out (excluded from any future Concept)

- **FSA star card for hub-and-spoke.** No style-selection row. **Do
  not invent ★.** Do not borrow SOA ch17 “disastrous” or EDA 4★/5★.
- **Typical quantum count of E9.** Not in style-selection. The hub
  *often* behaves as **one quantum** (Mason shared DB + cluster; ch7
  shared-DB rule) with spokes that may already be other quanta. Not
  an official matrix FACT. Network hub-spoke has no FSA quantum.
- **O’Reilly “Integration Hubs” video** (Richards/Ford): title
  seen, **body not fetched.** Packt “hub and spoke” chapter is not
  FSA. MuleSoft “70 percent … 2003 study”: unsourced. Gartner
  iPaaS: not fetched. Hohpe ch. 3 PDF (GoF Mediator): cited on E4,
  **not re-fetched.** `orchestration-driven-service-or-arch.md`:
  E6 owns it. FSA 2nd-ed TOC: same style set, no hub-and-spoke
  chapter. Airline ops research unused. Scoring loop not run.
