---
type: research
title: 'Client–server architecture — external research (2026-09-13)'
description: >-
  Group E decision-depth evidence pass for E5: what client–server is and
  is not, two-tier vs n-tier, fat vs thin vs mobile clients, the network
  as the coupling surface (fallacies), quantum count Uncertain (no
  style-selection row), when-to / when-not, migration, a worked example,
  and a trade-off table. No library defaults.
tags: [research, system-design-patterns, E5, client-server]
---

# Client–server architecture — external research (2026-09-13)

> Evidence pass for catalog **E5** (Group E). Not a Concept. Fetched
> 2026-09-13. Does **not** run arch-style’s four determinations or
> scoring micro-loop. **No library-defaults.** A `—` cell is **not**
> a rating.
>
> **[style-selection.md](../../../.claude/skills/arch-style/references/style-selection.md)
> has no Client–server row** (Richards & Ford ch7, ch9–19). No CS /
> N-tier stars, no typical quantum count. Quantum *machinery* is
> definition only. Typical quantum count is **Uncertain** (§3.2, §8)
> — do not invent.
>
> **Cite, do not rewrite:**
> [A1](a1-request-response-external-research.md) (REST/gRPC *wire*),
> [E1](e1-monolith-external-research.md) (monolith often *deployed as*
> the server),
> [E3](e3-layered-external-research.md) (layers *inside* a client or
> server),
> [rest-rpc-dataflow.md](../../../cases/data-intensive-design/rest-rpc-dataflow.md),
> [aws/ch08.md](../../../cases/aws/ch08.md),
> [style-decision.md](../../architecture/worksheets/mobile-test-automation/style-decision.md),
> [ADR 0005](../../architecture/adrs/application/mobile-test-automation/0005-adopt-plain-modular-monolith-partitioned-by-cluster.md).

---

## 1. Scope and non-goals

**Owns** the style: role asymmetry (client initiates, server reacts);
**two-tier vs n-tier** placement of UI / processing / data; **fat vs
thin vs mobile** clients; the **network as the coupling surface**
(fallacies — cite style-selection); when-to / when-not; migration
in/out; one worked example; a trade-off table. No invented stars.

**Siblings, not this card.** **A1** — REST/gRPC wire. **E3** —
logical layers *inside* a client, a server, or split. **E1 / ⊕E10**
— one deployable (often *the* server) and its domain modules.
**E2 / E6** — many (or ≤12 coarse) *server-side* quanta; each hop
is still CS. **C6** — gateway / BFF (still presentation). **⊕E11**
— who *runs* the server. **D2** — instruments the client. **E4 /
A2** — a queue between web and worker is not the system style.

**Non-goals.** Library defaults. Four determinations. Rewriting A1
or cited `cases/` notes. Filling a missing FSA star row.

---

## 2. Lineage / vocabulary

**Fielding 2000** §3.4.1 / §5.1.2
https://ics.uci.edu/~fielding/pubs/dissertation/net_arch_styles.htm ·
https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm —
CS is “the most frequently encountered” network-based style. Server
*listens*; client *initiates*; server rejects or performs and replies.
Andrews (via Fielding): client = triggering process; server =
reactive, usually long-lived, often multi-client. Basic CS does
**not** constrain state split (RPC/MOM are connectors). REST’s
*first* added constraint is CS. Variants: **LCS** = CS +
proxy/gateway (IS two-/three-/multi-tier); **CSS** = no session
state on the server; **RS** = state on the server (TELNET/FTP);
**RDA** = client sends SQL and must know the schema; **COD** =
know-how shipped to the client.

**Meier 2008-09-06**
https://learn.microsoft.com/en-us/archive/blogs/jmeier/layers-and-tiers
— *layer* = component type; *tier* = physical pattern (two-/three-/
N-tier). Same cut as Fowler 2015 and Azure.

**Microsoft 1998** (Wrox)
https://learn.microsoft.com/en-us/previous-versions/office/developer/server-technologies/aa480455(v=msdn.10)
— monolith (Word); **two-tier** = “traditional client-server” (UI +
rules on the client; Oracle/SQL Server; VB/PowerBuilder; variant:
stored procedures); **n-tier** (n ≥ 3): client never hits data.
**IIS 6 two-tier**
https://learn.microsoft.com/en-us/previous-versions/iis/6.0-sdk/ms524701(v=vs.90)
— bank-teller clients share one DB; server overwhelmed as clients
grow; rule changes become expensive source edits.

**IBM** (fetched 2026-09-13; `ms.date` not recovered)
https://www.ibm.com/think/topics/three-tier-architecture —
two-tier = original CS (direct data-tier access). Contacts app =
three-*layer*, one-*tier*. IBM’s “faster because teams per tier”
**contradicts** Fowler 2015 — contested, not a law.

**Azure N-tier** (fetched 2026-09-13; `ms.date` **not on page**)
https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/n-tier
· https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/
— **strict** vs **relaxed**; **closed** vs **open**. Closed limits
coupling, can create pass-through latency; open reduces hops. Several
layers may share one tier. Styles table: N-tier = “traditional
business domain; frequency of updates is low” vs Microservices =
“complicated domain; frequent updates.”

**Fowler.** *Presentation Domain Data Layering* (2015-08-26)
https://martinfowler.com/bliki/PresentationDomainDataLayering.html —
logical layers; BFF is still presentation. *First Law* (2004-11-01)
https://martinfowler.com/bliki/FirstLaw.html — “Don’t distribute your
objects.” *Remote Facade* (2003-03-05)
https://martinfowler.com/eaaCatalog/remoteFacade.html — coarse
facade, **no domain logic**. *Microservices and the First Law*
(2014-08-13)
https://martinfowler.com/articles/distributed-objects-microservices.html
— remote calls are orders of magnitude slower and can fail;
cookie-cutter replicas do not raise distribution complexity. Names
the **Fallacies** plus Waldo et al.

**Newman, BFF (2015-11-18)**
https://samnewman.io/patterns/architectural/bff/ — mobile:
less screen, fewer/different calls, battery + data-plan cost of many
connections. One BFF per *experience*. C6 owns the product.

**RFC 9110** §3.3 (June 2022)
https://www.rfc-editor.org/rfc/rfc9110.txt — HTTP “is a
client/server protocol.” Roles are **per connection**. Statelessness
is HTTP’s, not Fielding’s *basic* CS.

**RFC 5694** (Nov 2009)
https://www.rfc-editor.org/rfc/rfc5694.txt — P2P vs CS; no sharp
border; hybrids common. App. A: CS concentrates processing/storage.
NATs were designed not to break CS and *did* break receive-first P2P
until ICE-class traversal.

**van Steen & Tanenbaum** 4th ed. Landing page: cite “2023”; **v4.03**
January 2025. https://www.distributed-systems.net/index.php/books/ds4/
— chapter body **not** fetched (§8). 2nd-ed solutions: three-tier =
three logical layers, each *in principle* on a separate machine;
**vertical** vs **horizontal** distribution. 2016 paper: hide WAN
latency by moving form validation onto the client.

**Richards & Ford via style-selection.** Quantum definition + the
**eleven** fallacies (ch9). No CS row. Cite; do not re-derive.

---

## 3. Mechanics (Group E decision bar)

### 3.1 What the style is — and is not

**Is.** Role asymmetry: one side initiates; the other waits, performs
or rejects, and replies (Fielding §3.4.1). Unconstrained in basic CS:
state placement (CSS is extra); machine count (local sockets still
CS); server-process count (one origin, replica farm, or
server-as-client-of-DB — the last is how three-tier appears);
connector (RPC / HTTP / MOM). **A1 owns** REST/gRPC wire; this card
owns the roles. Buys (Fielding §5.1.2; Azure Benefits): independently
evolving clients; a server simplified toward data and rules; one
authoritative store; cheap lift-and-shift.

**Is not.** **E3** — Fowler 2015 / IBM Contacts: all three layers can
run in one process (fat client, or a monolith with no network).
Layers can live *inside* the client, *inside* the server, or be
split; E5 is who initiates across a process/network boundary.
**E1** — one deployable, often **the server** that clients call; can
also be Word-style with no client role (Microsoft 1998). E1 = how
many deployables; E5 = who calls whom. **P2P** — RFC 5694 §2: an
element both provides *and* requests; many clients ≠ P2P; hybrids
are first-class. **E2** — Azure: N-tier = *horizontal* tiers;
microservices = *vertical* split, own data; one API + many clients
is CS no matter how many LB replicas sit behind it. **HTTP / an
API** — RFC 9110 §3.3 is a *protocol* role. **⊕E11** — a function
still has clients; E11 starts when the server quantum is no longer a
long-lived process.

### 3.2 Typical quantum count — Uncertain

Style-selection’s matrix has **no Client–server row**.

| Claim | Status |
|---|---|
| Typical quantum count for E5 | **Uncertain** — do not invent |
| Star-rating scorecard for E5 | **—** (no row; not a rating) |

Quantum *machinery* (`ArchCharScope.md:18-36`) as definition only:
smallest independently runnable part; **DB is inside the quantum**;
shared DB ⇒ **one** on that side; sync can silently merge. Azure
*tiers* are scalability / security / reliability boundaries, not
automatically new quanta. Cookie-cutter replicas do **not** raise
the count (Fowler 2014). A second server-side thing with its *own*
data is a *style change* toward E2/E6. Do **not** treat “2+” as a
style-selection FACT. Org-unowned browsers as quanta: §8.

### 3.3 Two-tier vs n-tier (this card owns placement)

| Placement | Client holds | Middle | Data | Source |
|---|---|---|---|---|
| **Two-tier** | UI + usually rules | — | RDBMS (or rules in stored procedures) | Microsoft 1998; IBM; IIS |
| **Three-tier** | UI only | Rules; client never hits data | Store accepts middle only | Microsoft 1998; IBM; Azure |
| **N-tier** | UI | One or more middle tiers (optional queue) | Store; optional cache | Azure; Fielding LCS |

IBM: two-tier *is* the original CS. Microsoft 1998: “traditional
client-server” = two-tier. Closed+strict = walk the stack
(evolvability, latency); open+relaxed = skip hops. A CRUD-only
middle tier is Azure’s named challenge — E3’s Architecture Sinkhole
(Richards 2015; style-selection only name-checks it). Collapse the
hop; do not invent a new style.

### 3.4 Fat vs thin vs mobile client

| Kind | Where the application lives | Typical cost | Sources |
|---|---|---|---|
| **Fat** | Most app code (sometimes a local cache) on the client; server is files/DB | Version skew; install; client holds schema (RDA) | Microsoft 1998 / IIS; Fielding RDA |
| **Thin** | Presentation only (browser, remote display, generic session client) | Server-session / RS tax; network on every gesture | Fielding RS; Newman 2015 (install cost eliminated) |
| **Mobile (native)** | Fat-*ish* local UX, cache, offline, sensors; thin coarse API. Less screen, fewer/different calls, battery + data-plan cost of many connections | Store-update lag; chatty general-purpose APIs; one shared API as a release bottleneck | Newman BFF 2015; Fowler 2015 (BFF = presentation) |

COD (Fielding §3.5.3) thickens a thin Web client without a store
install; native mobile cannot use that as its primary ship path. C6
owns the BFF; E5 owns that mobile is a first-class CS variant.

### 3.5 The network as the coupling surface (fallacies)

The moment client and server are not one process, the design pays the
**fallacies of distributed computing** (style-selection ch9, all 11
— cite, do not re-derive):

> network is reliable / latency is zero (know p95–p99, not averages) /
> bandwidth is infinite (stamp coupling) / network is secure /
> topology never changes / only one administrator / transport cost is
> zero / network is homogeneous / **versioning is easy** /
> **compensating updates always work** / **observability is optional**
> (`Arch-style-foundations.md:207-319`).

Fowler 2014 points at the same list (plus Waldo et al.) as why a
remote call is not an in-process one. **This is E5’s coupling
surface.** A1 then specifies how REST/gRPC *express* it. Do not
rewrite A1.

CS-hop mapping (not new research): every gesture is remote unless
you batch (Remote Facade) or move work onto the client (2016 van
Steen paper) — design to p95–p99. Fat RDA / stamp-coupled DTOs hit
bandwidth (Newman: a mobile *product* constraint). Client is outside
the perimeter (Azure: data accepts *only* the middle tier). Clients
roam; NATs (RFC 5694 App. A); store-signed binaries. Inter-process
is “orders of magnitude” more expensive even on one machine (Remote
Facade). Mixed platforms are Azure’s N-tier *benefit* and an A6 tax.
Versioning: “servers upgrade first, clients second”
([rest-rpc-dataflow.md](../../../cases/data-intensive-design/rest-rpc-dataflow.md)).
Lost-reply vs lost-request is C9. D2 vs D3 split → D4/D5. The public
Internet *grew around* CS (clients open out). Reverse that and CS is
the wrong shape unless you add polling, WebSockets (A3), or a relay.

### 3.6 When to use / when not

**Use** when work is **request-shaped**, **authority is
centralized**, and **independent client evolution** matters more
than removing the server: UI vs storage evolve separately (Fielding
§5.1.2); one store clients must not bypass (Microsoft 1998; Azure
NSG); slow-changing domain or lift-and-shift (Azure); two-tier until
per-client DB connections or UI-buried rules break (IIS); endpoints
cannot receive unsolicited connections (RFC 5694 App. A); a
well-dimensioned server is acceptable (RFC 5694 §6: ordinary queries
still beat a DHT; battery peers consume more than CS clients that
sleep).

**Not** when work is peer-symmetric (P2P, maybe with a CS tracker);
when many server-side capabilities must release independently (E2;
Azure “monolithic design prevents independent deployment of
features”); when the middle tier only forwards CRUD; when the API is
100 fine-grained getters (First Law); when the default is reaction
to events (E4); when you refuse to run a server (E11).

### 3.7 Migration in / out

**In.** Single process → two-tier (pay the network + C9). Fat
two-tier → three *logical* layers, *then* three physical tiers —
layer *before* adding Web/mobile (Fowler). On-prem N-tier → cloud
N-tier with minimal refactor (Azure). Add CSS + cache +
intermediaries without leaving CS (Fielding §5.1.2–5.1.6).

**Out.** N-tier → Web-Queue-Worker (CS at the HTTP edge). N-tier →
E6/E2 via **B4** + C6 when update frequency justifies the tax. CS →
P2P/hybrid, keep CS for enrollment (RFC 5694 §2). Long-lived server
→ E11 (A3/A4 session assumptions usually break). **Do not add
tiers** that do not change scalability, reliability, or security
boundaries (Azure).

### 3.8 Worked example — CS around an E1/E10 server

[style-decision.md](../../architecture/worksheets/mobile-test-automation/style-decision.md)
(2026-07-26) +
[ADR 0005](../../architecture/adrs/application/mobile-test-automation/0005-adopt-plain-modular-monolith-partitioned-by-cluster.md):
**one quantum**, one Spring Boot deployable, one primary datastore.
That quantum is **deployed as a server**. Operators, CI, and device
runners *initiate*; the process *reacts*. Perimeter = **E5**. Body =
**E1 / E10**. Presentation/domain/persistence folders inside the JAR
are **E3 inside the server** (kata already rejected E3 as *macro*
style). Each unary hop is **A1**. Cookie-cutter replicas stay one
server-side quantum (shared DB). A future extract with its own store
would *leave* E5 — ADR 0005 names **E6**, not a CS-tier split.

**Two-tier pressure, same sources.** IIS bank-teller: fat client
knows the schema; one DB. Fits until client count overwhelms the
store or a Web/mobile channel appears. Three-tier: Remote Facade +
DTO (Fowler 2003); DB accepts only that tier (Azure NSG). Mobile:
do not hang a chatty general-purpose API off the same facade
(Newman); C6 decides the BFF. Style quantum count stays
**Uncertain**; the workspace pick is independently “one server-side
quantum.”

### 3.9 Trade-off table

Qualitative, source-backed. **No invented FSA stars.** E5 scorecard
= `—`.

| Concern | CS / N-tier wins | CS / N-tier loses | Source |
|---|---|---|---|
| Independent client evolution | Portable UI across org domains | Fat-client / store-update versioning | Fielding §5.1.2; Newman |
| Authority / security | One store; middle tier as internal firewall | Server (or tier) is the SPOF unless replicated | Microsoft 1998; IBM; Azure; RFC 5694 App. A |
| Ops / cost (small estate) | Few servers; cheap lift-and-shift | You *must* run a server; concentrated energy | Azure Benefits; RFC 5694 §6 |
| Feature deploy independence | — | N-tier is “monolithic” for features | Azure Challenges |
| Scale of one hot path | Scale a *tier* (Azure VMSS) | Two-tier: per-client DB connections; cookie-cutter clones cold with hot | IIS; Fowler 2014 |
| API grain | Coarse Remote Facade | Chatty objects / client-side SQL (RDA) | First Law; Fielding RDA |
| Network fallacies | Fits NAT/firewall Internet (clients open out) | Paid in full the day you leave one process | style-selection ch9; RFC 5694 App. A |
| vs P2P / E2 / E3 | Ordinary queries; battery clients sleep; layers *inside* a process stay cheap | No infrastructure / frequent independent server releases / distributing *at* layer boundaries (Fowler 2005 0/18) | RFC 5694 §6; Azure styles; E3 note |

---

## 4. Verified defaults / standards

Omitted. Group E has no library-defaults section. Hop tax is C7 / C2
/ C1 / C9. HTTP/gRPC versions and proxy idle are **A1**.

---

## 5. Failure modes and when-not-to-use

Server as **SPOF** (RFC 5694 App. A; IIS as clients grow) — mitigate
*inside* the style (replicas, HA data), not a silent slide into E2.
**Lost reply → duplicate execution** (C9; TCP does not help).
**Fat-client / store-update** version skew (IIS; RDA; Newman).
**CRUD-only middle tier** = slower two-tier (Azure; E3 sinkhole).
**Chatty objects** (First Law) — Remote Facade + DTO, not more
tiers. **Server session without affinity** (Fielding CSS; C5
stickiness). **Shared-DB “N-tier”** that thought it was many quanta.
**NAT mismatch** — CS assumes clients open out; reverse it →
polling, A3, or a relay. **D2 vs D3** observability split. Staffing
three tier-teams recreates Fowler’s layer-team antipattern.

**When-not** (restating §3.6): do not pick E5 as the *system* style
when work is peer-symmetric, when many server-side features must
release independently, when you are about to distribute objects, or
when you refuse to operate a server.

---

## 6. Cross-links

**A1** — wire under the CS roles. **E3** — layers inside client or
server. **E1 / ⊕E10** — the server body is often a monolith. **E2 /
E6** — next styles when the *server side* splits. **⊕E11** — server
quantum is no longer long-lived. **C6** — gateway / BFF. **D2 / D3
/ D4** — client vs server telemetry. **B4 / C5 / C7 / C1 / C2 / C9**
— leave-mechanism and hop tax. style-selection.md — quantum
definition; **no CS row**; fallacies ch9. rest-rpc-dataflow.md ·
aws/ch08.md — cite, do not rewrite.

---

## 7. Sources (retrieved **2026-09-13**)

1. [style-selection.md](../../../.claude/skills/arch-style/references/style-selection.md) — quantum machinery; matrix **omits** CS; fallacies ch9 (all 11).
2. Fielding 2000, Meier 2008, Microsoft 1998, IIS 6 two-tier, IBM three-tier, Azure N-tier + styles index — URLs in §2.
3. Fowler: Presentation Domain Data Layering (2015-08-26) · First Law (2004-11-01) · Remote Facade (2003-03-05) · Microservices and the First Law (2014-08-13).
4. Newman, BFF (2015-11-18). https://samnewman.io/patterns/architectural/bff/
5. RFC 9110 §3.3 (June 2022) https://www.rfc-editor.org/rfc/rfc9110.txt · RFC 5694 (Nov 2009) https://www.rfc-editor.org/rfc/rfc5694.txt
6. van Steen & Tanenbaum landing page (cite 2023; v4.03 Jan 2025) https://www.distributed-systems.net/index.php/books/ds4/ · 2nd-ed solutions https://www.distributed-systems.net/my-data/DS2/ds-solutions.pdf · 2016 paper https://www.distributed-systems.net/my-data/papers/2016.computing.pdf
7. In-tree notes listed in the header.

---

## 8. Uncertain / left out

- **Typical quantum count for E5.** No style-selection row. **Do
  not invent 2+.** Workspace “one server-side quantum” is a local
  pick. Browser / BFF as quanta left open (C6 owns the BFF).
- **Stars.** No CS row. `—` is not a rating.
- **`cases/ArchitectureBook/`** (`ArchCharScope.md`,
  `Arch-style-foundations.md`, …) **absent** 2026-09-13. Fallacies
  used only as style-selection recovered them (11 items).
  Deutsch/Gosling’s original eight not re-fetched.
- **Azure / IBM `ms.date`.** Pages fetched; edit day not in extract.
- **van Steen 4th-ed §2.3 / Figure 2.17.** Landing page + 2nd-ed
  solutions + 2016 paper only.
- **Sinha (1992), Umar (1997), Waldo et al. 1994, PEAA 2002 PDF** —
  not re-fetched. Two-tier history from Fowler’s later notes +
  Microsoft 1998.
- **Architecture Sinkhole** internals — E3 recovered them.
- No SLA, no vendor default timeout, no library version. Not facts
  for a future Concept.
