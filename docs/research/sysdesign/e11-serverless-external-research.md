---
type: research
title: 'Serverless and FaaS — external research (2026-09-13)'
description: >-
  Group E decision-depth pass for catalog E11: BaaS plus FaaS (functions
  as the unit of deployment, not of domain); cold start / timeout / vendor
  orchestration as characteristics; E4 vs E11; migration in/out of E2/E10.
tags: [research, system-design-patterns, E11, serverless, faas]
---

# Serverless and FaaS — external research (2026-09-13)

> **What this is.** ⊕E11 decision-depth pass. No library-defaults; no
> scoring loop. Quantum is **not** in
> [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md)
> (no FSA serverless row) — typical cut is **ch7 machinery** only.
> Fetched 2026-09-13. Unverified → §8. Cite, do not rewrite:
> [distributed-vs-single-node.md](../../../cases/data-intensive-design/distributed-vs-single-node.md),
> [modular-implementation.md](../../../cases/ml-solutions-arch/modular-implementation.md),
> [aws/ch08.md](../../../cases/aws/ch08.md) (choreography / orchestration;
> **Lambda architecture ≠ FaaS**),
> [aws/ch11.md](../../../cases/aws/ch11.md), [aws/ch14.md](../../../cases/aws/ch14.md),
> [aws/ch07.md](../../../cases/aws/ch07.md). E2: E11 is a *hosting* option.

---

## 1. Scope and non-goals

**Owns** the *style / hosting decision*: vendor allocates and frees
compute per event or request, billed for execution. **BaaS + FaaS**
compose. Decision depth: what it is / is not; quantum from **ch7
machinery** (not an invented FSA cell); when-to / when-not; migration
in/out of **E2** and **E10**; worked cut; trade-off table.

| Sibling | Why not this card |
|---|---|
| **E2** | Domain-shaped services, DB-per-service. A function can *host* a service; FaaS does not make you E2. |
| **E10** | One deployable, domain modules, quantum FACT = 1. Usual *source* when an edge is peeled; usual *merge* target. |
| **E4** | Collaboration style (broker / mediator). FaaS is a common *actuator*. Buying Lambda does not make the system E4. |
| **E5** | Request/response topology. Roberts’ SPA / mobile + BaaS is E5 *plus* E11. |
| **B1** | Scaler math (`L = λW`, HPA). This card names scale-to-zero as a *motive*. |
| **B4** | Incremental cutover *mechanism* into or out of E11. |
| **B5** | Workflow that *outlives* one invoke (Durable Functions / Step Functions). [aws/ch08.md](../../../cases/aws/ch08.md) owns choreography vs orchestration. |
| **C6** | HTTP front door. Roberts: the gateway is itself BaaS. |
| **C7** | How to pick a timeout. This card only treats **timeout as a characteristic** (a hard box exists). |

**Non-goals.** Lambda / SAM tutorial. Timeout or memory *tables* as if
they were the style. Scoring FaaS-vs-Kubernetes. Invented cold-start
SLAs. Rewriting cited `cases/` notes. Collapsing E11 with ch08’s
**Lambda architecture** (batch + speed + serving).

---

## 2. Lineage / vocabulary

**Janakiraman on Fowler, “Serverless” (2016-06-20).**
https://martinfowler.com/bliki/Serverless.html — fetched 2026-09-13.
No always-on server process: third-party services, client-side control
flow, short-lived hosted RPCs (FaaS). Bursty-traffic economics vs
fabric overhead; ops did **not** disappear.

**Roberts on Fowler, “Serverless Architectures” (2018-05-22).**
https://martinfowler.com/articles/serverless.html — this catalog’s
definition. Two overlapping ideas, not “no servers”:

1. **BaaS.** Third-party cloud services for server-side logic and state
   (auth, hosted DB, object store). Typically a rich client talks to
   them directly. Word around **2012** (Ken Fromm); popularity after
   **Lambda (2014)** and **API Gateway (2015-07)**.
2. **FaaS.** Team-written logic in **stateless, event-triggered,
   ephemeral** compute, **fully managed**. Restriction is
   **operational** (state, duration, startup), not linguistic.

Sidebar: servers exist; the product org is **not looking after** them.

**Operational FaaS (same essay).** No provisioned server and **no
long-lived server application** — the difference from containers and
PaaS. Scale is per-event. Local memory / disk is not durable across
invocations. Duration is **capped**. Cold start = new container + host
process; warm start reuses one. An **API gateway** is configured HTTP
whose handlers are often functions (itself BaaS). Roberts’ “five
minutes” is **stale as a 2026 product number** (§8).

**CNCF Serverless WG (2018-02-14).**
https://www.cncf.io/blog/2018/02/14/cncf-takes-first-step-towards-serverless-computing/
— fetched 2026-09-13. “A **finer-grained deployment model** where
applications, bundled as one or more **functions**, are uploaded …
executed, scaled, and billed in response to the exact demand.” Same
BaaS / FaaS split; BaaS often *holds the state* functions cannot. That
sentence is the “functions as the unit of **deployment**, not of
**domain**” hook: CNCF is talking about *how you ship*, not bounded
contexts. Whitepaper landing:
https://github.com/cncf/wg-serverless/tree/master/whitepapers/serverless-overview

**What isn’t Serverless (Roberts).**

| Look-alike | Why not E11 FaaS |
|---|---|
| **PaaS** | Cockcroft: if it starts in 20 ms and runs half a second, call it serverless. Most PaaS still asks “how many dynos?” |
| **Containers / K8s** | You still size the cluster or HPA. “Serverless containers” (Fargate) are the *narrowing gap*, not identity. |
| **#NoOps** | Monitor, deploy, secure, debug, scale *downstream* remain. Majors: the abstraction leaks. |
| **Stored-proc-as-a-service** | Tiny DB-adjacent subset. Fournier’s debt warning is about *that* subset. |
| **ch08 Lambda architecture** | Nathan Marz batch + speed + serving ([aws/ch08.md](../../../cases/aws/ch08.md)). Name collision only. |

**Azure Architecture Center (fetched 2026-09-13).**
[Styles index](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/)
lists N-tier, Web-Queue-Worker, Microservices, Event-driven, Big data,
Big compute. **Serverless is not a row.** Web-Queue-Worker names Azure
Functions as a *managed worker*. `…/architecture-styles/serverless` →
**404** this fetch (§8).

**style-selection.md.** **Does not mention serverless.** The book’s
spike-load style is **space-based** (ch16): in-memory PUs, data pumps,
**DB off the transaction path**. E11 also targets idle-to-spike
economics; it is **not** space-based (default path *does* round-trip a
managed DB). Do not invent stars.

**This workspace.**
[distributed-vs-single-node.md](../../../cases/data-intensive-design/distributed-vs-single-node.md):
metered billing for *code execution*; time limits; slow first invoke;
“serverless” on BigQuery / Kafka = autoscale + metered billing.
[modular-implementation.md](../../../cases/ml-solutions-arch/modular-implementation.md):
Serverless and FaaS are **one style** listed twice.
[aws/ch11.md](../../../cases/aws/ch11.md): Lambda on a compute-platform
menu. [aws/ch07.md](../../../cases/aws/ch07.md): Knative reintroduces a
cluster.

---

## 3. Mechanics (Group E decision depth bar)

### 3.1 What the style is — functions deploy, domains do not

**Is.** Default server-side compute is not an always-on process the
team patches and sizes, but a vendor-managed execution that starts
because an event or request arrived and stops (or freezes) when that
unit of work ends.

| Member | Team writes | Vendor runs |
|---|---|---|
| **FaaS** | Handler (one function ≈ one *deployable*) | Ephemeral environments, scale-out, OS |
| **BaaS** | Config + client / SDK calls | Auth, DB, object store, gateway, bus |

They compose. SPA + Cognito + DynamoDB + one authorizer = BaaS-heavy
E11. Queue workers with no client = FaaS-heavy E11. Both are E11.

**The unit of deployment is the function. The unit of domain is not.**
CNCF’s “bundled as functions” is a *shipping* grain. E2 / E10 still own
bounded contexts. Twenty zip files on one orders table are **one
domain** wearing twenty deployables. Do not FaaSify a class. Do not
treat function count as a target headcount.

**Is not:** “no servers”; E2 (test is DB-per-service + no lock-step
release); E4 (HTTP function returning a body is still **A1**; an SQS
trigger is an **A2 / E4 *edge*** — events are how E4 *collaborates*,
functions are how E11 *computes*); managed containers as a synonym
(Cloud Run / Fargate / App Runner keep a **long-lived process** that
serves many concurrent requests — Roberts’ neighbour, not FaaS); ch16
space-based; ch08 Lambda architecture.

### 3.2 Typical quantum — FACT from ch7 machinery only

style-selection ch7: quantum = smallest independently runnable part;
**the database is part of the quantum** (shared DB ⇒ **quantum of
one**); sync between mismatched characteristic-sets silently merges
them. **No FSA serverless cell.** Do not invent “quanta = most of any
style” by analogy with microservices.

> One function is **not** a quantum. The quantum is the function **+
> its managed data store + its sync callers**.

| Deployable | Quantum? | Why |
|---|---|---|
| One function, own trigger, own data | **Often one** | Independently deployable; platform *is* the runtime |
| N functions, one shared table / RDS | **One** | Shared DB is the API (`:36`) |
| Function + API Gateway + the table it owns | **One** | Gateway is a front door (C6) |
| Function that *must* sync-call another on the user path | **At risk of one** | Sync merge; Guardian hop still couples availability |
| BaaS-only client + Firebase | **One** (+ client) | No independently operable server-side quantum |

FaaS makes the *deploy* cheap and leaves the *data* and *IAM* expensive.
### 3.3 Characteristics (cold start, timeout, vendor orchestration)

Style characteristics, not a product tutorial. Fetch dates. **No
memory / timeout tables.** **Vendor orchestration:** the platform
*is* the cluster: create /
destroy environments, bind triggers, bill per invoke (Roberts 2018;
CNCF 2018; Kleppmann). You do not staff HPA for the function. You
still staff **downstream** saturation — functions stampede a shared DB
(B1). The trigger fabric is **vendor-shaped**; rewriting the handler
does not port it (Roberts lock-in). Classic FaaS usually has **no
sidecar** (B6). Need a sidecar → you left classic FaaS.

**Timeout as a box.** Every sourced definition: invocations are
**duration-capped** (Roberts 2018; Kleppmann; [aws/ch11.md](../../../cases/aws/ch11.md)
“maximum 15-minute invocation”; sync HTTP often tighter — ch11 names
API Gateway **29 s** as the binding user-path box). C7 owns the number
*inside* the box. Characteristic: **long-running synchronous work is
the wrong shape**. Durable Functions / Step Functions (ch08
orchestration; B5) checkpoint across many invocations — they are not
a raised FaaS duration. Roberts’ “five minutes” is historical (§8).

**Cold start.** New environment + host + init; warm start reuses one
(Roberts 2018). “A few milliseconds to several seconds,”
workload-shaped; async high-volume processors often do not care; a
low-latency trading path would (Intent Media click-processor vs a
trading app — **no ms SLA here**). [aws/ch11.md](../../../cases/aws/ch11.md)
paraphrases AWS (“100 ms to one second”; “typically … 1% of
invocations”) and names provisioned concurrency / SnapStart. That is
a **book paraphrase**, not a 2026 official stat (§8). Treat cold start
as an **undeclared tail**: async path, pre-init, or leave FaaS.

### 3.4 When to use / when not

**Use** when most hold (Roberts + Kleppmann + this workspace’s compute
menu): traffic is **occasional or spiky** enough that an always-on
replica wastes its life; work is **event-shaped** (object, row, queue,
webhook, schedule) or a coarse HTTP verb that fits the **front-door**
box; the team wants **ops offload** and will accept vendor
orchestration of the trigger fabric; state lives in a backing service;
the slice is an **edge** of E1 / E10 / E2 / E5, not the ACID core.

**Do not** when: work is **long-running and synchronous**; the design
needs **stable in-process state** or a large local cache (space-based
is the other spike answer, and it keeps data *off* the DB path);
collaboration is **chatty sync** across many functions on the user
path; cross-function ACID dominates (a saga of Lambdas is B5); tail
latency *is* the product; every replica needs B6 / GPU / a custom
image; you would FaaSify an E10 monolith into grains of sand — start
E10, extract **one** trigger. Space-based when-to (>10k concurrent,
ticketing) is **not** automatically E11 when-to: E11 usually puts the
DB *on* the request path.

### 3.5 Distinguishing E4 — events as style vs functions as compute

| | **E4 Event-driven** | **E11 Serverless / FaaS** |
|---|---|---|
| Question | How do components *collaborate*? | How is *compute hosted*? |
| Unit | Processor + initiating / derived events | Function (deploy) + BaaS (state / door) |
| Topology | Broker or mediator ([e4](e4-event-driven-external-research.md); ch08 choreography vs orchestration) | Vendor trigger fabric + ephemeral execution |
| Quantum | FACT **1–many** (style-selection ch15) | **No FSA row.** Apply ch7: function + store + sync callers |
| Lawful without the other | In-process bus inside E10; long-lived Kafka consumers on E2 | HTTP function behind a gateway, no broker (still A1) |

A queue-triggered function is **E11 hosting an E4 / A2 edge**. An HTTP
function that waits on three sync callees is **E11 hosting a badly cut
request path**. Do not say “we are event-driven” because the trigger
dropdown includes SQS.

### 3.6 Migration in / out of E2 and E10

**E10 / E1 → E11.** Mechanism is often **B4** (peel an edge) or a new
subscription, not a rewrite. Pick event-shaped work or a coarse HTTP
verb that fits the front-door timeout. Extract **functionality first**,
leave the table (Richards 2016 — same as E2): you now have E11 hosting
and **still one quantum**. Split the store only if the function has a
different characteristic-set *and* you can tolerate the consistency
window — that is the moment the peel *might* become a second quantum.
Cap concurrency at `downstream_budget / per_invoke_cost`. Do not move
checkout ACID onto a graph of sync functions.

**E2 → E11.** Hosting swap for *one* service whose traffic is spiky or
event-shaped. You remain E2 only if DB-per-service and independent
release still hold. Twenty Lambdas on one table are **one quantum**
that used to be called a service. [aws/ch14.md](../../../cases/aws/ch14.md)
already prefers separate Lambdas per API as a *future compute-swap*
seam, not as proof of multiple quanta.

**E11 → E10.** Merge handlers back when utilization is uniformly high
(Roberts: FaaS can *cost more* than a full-time host), when chatty
sync has reappeared, or when the team cannot operate a fabric of
functions + IAM. The store was probably never split — deployable
change, not a data migration.

**E11 → E2, or to a managed container.** Hitting the duration /
front-door box as a *design* constant → process (Cloud Run / App
Runner / Container Apps) or **B5** if it is a workflow. Cold-start
jitter after pre-init still hurts → min-instances managed container.
Need sidecar / GPU / custom image → you left FaaS. Shared-DB
functions that ship as a set → admit one quantum; merge (E10) or
become E6; **do not** relabel as E2. Own store *and* a named
disintegrator → then it can become an E2 service (E2 owns the C*
tax). ch14 already treats Lambda → App Runner / ECS as a **compute
swap**.

### 3.7 Worked example — pet-store, click logger, URL shortener

Not a scored kata. Same quantum rule.

**Roberts pet-store (UI-driven).** Auth → Cognito / Auth0 (BaaS).
Client reads listings from a hosted DB. Search = one HTTP function
behind a gateway; Purchase = another (security). Choreography, not a
central arbiter — **E4-shaped collaboration on E11 compute**, not “we
bought E4.” If Search and Purchase share the schema and cannot deploy
alone, you have **one** quantum and two zip files. Binding user-path
timeout is the **gateway**, not the function max.

**Roberts click-processor (message-driven).** Redirect *now*; click
message on a bus; FaaS updates advertiser budget. Small change vs a
long-lived consumer — why async is the popular FaaS fit. Quantum =
processor + budget store. C7: function timeout sits *inside* bus
visibility timeout (A2).

**Workspace URL shortener ([aws/ch14.md](../../../cases/aws/ch14.md)).**
Day-0: separate Lambdas per API, DynamoDB, API Gateway, Cognito.
Automatic scale **and** p100 from cold start. Separate Lambdas are a
future compute-swap seam: they share the short-URL table, so the
quantum is **one** until the table splits.

C* tax on every **sync** hop is C1 / C2 / C7, not a reason to pick E11.

### 3.8 Trade-off table (qualitative — no invented stars)

| Buy | Pay |
|---|---|
| No standing host; scale-to-zero idle cost | Cold start (ms–seconds, workload-shaped). Pre-init buys tail with idle spend |
| Per-request billing on spiky / rare work | Uniform high utilization can cost *more* than a box (Roberts: do the math) |
| Independent *deploy* of a handler | Shared DB / IAM / account concurrency **merges** quanta |
| Elasticity without staffing HPA | Burst is platform-rate-limited; HTTP front door often tighter than the function |
| BaaS commoditises auth / DB | Vendor control; **lock-in on the trigger fabric**; client logic repeated per platform |
| “No sysadmin” | Request / trace / log, not a node. No sidecar unless you leave FaaS. Short-lived debug is a different discipline |
| Fast first deploy on a mature event | Cambrian explosion of functions + IAM (Roberts security) |

No FSA stars. A `—` cell is not a rating.

---

## 4. Dated facts (no library-defaults section)

Group E has **no** library-defaults section. Do **not** copy timeout /
memory / concurrency quota tables into the Concept. Dated facts:
Janakiraman 2016-06-20; Roberts 2018-05-22; CNCF WG 2018-02-14; Azure
styles index (no serverless row; `…/serverless` → 404) fetched
2026-09-13; style-selection ch7, **no serverless row**;
[aws/ch11.md](../../../cases/aws/ch11.md) 15 min / 29 s / cold-start
is a book paraphrase, not a 2026 vendor fetch. Platform maxima belong
in C7. They are not the style.

---

## 5. Failure modes and when-not-to-use

- **Shared-DB fake quanta** / lock-step migrations — distributed
  monolith with a nicer bill.
- **FaaSification / grains of sand** — functions used as a *domain*
  grain (Roberts “beyond FaaSification”).
- **E11 confused with E4** (§3.5) or with **ch08 Lambda architecture**.
- **Front-door / function timeout mismatch** — fails as **C7**; the
  published max is not the budget.
- **Account-concurrency stampede / DoS yourself** (Roberts); B1
  “scale-out kills the database.”
- **Cold-start as an undeclared SLO**; **sync-merged availability**
  (three functions × three cold starts × three error budgets).
- **BaaS-only, then a second client** (logic repeated per platform).
- **Calling it space-based** (ch16); **sidecar-shaped** needs on FaaS
  (wanted B6 + a process); **self-hosted “FaaS” on K8s** (ch07 Knative
  — programming model may look like E11, ops does not).

When-not is in §3.4. Choosing E11 because the slide said “serverless”
is E2’s Jump-on-the-Bandwagon with a different logo.

---

## 6. Cross-links

- Catalog ⊕E11; style SoT [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md) (ch7; **no serverless row**; ch16 is the book’s spike style). Main: `/Users/rajnishkhatri/Code/LLM-DRIVEN-MOBILE-TEST-AUTOMATION/.cursor/skills/arch-style/references/style-selection.md`.
- **E2** hosting option; **E10** peel source / merge target; **E4** style (FaaS is an actuator; ch08 choreography vs orchestration).
- **B1 / B6 / C6 / C7 / B4 / B5** — scaler math; sidecar usually absent; gateway as BaaS door; timeout numbers; peel; durable work.
- Cases in the header.

---

## 7. Sources

Fetched 2026-09-13.
https://martinfowler.com/articles/serverless.html (Roberts, 2018-05-22) ·
https://martinfowler.com/bliki/Serverless.html (Janakiraman, 2016-06-20) ·
https://www.cncf.io/blog/2018/02/14/cncf-takes-first-step-towards-serverless-computing/ ·
https://github.com/cncf/wg-serverless/tree/master/whitepapers/serverless-overview ·
https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/
(serverless **not** in the table; `…/serverless` → 404). Workspace:
style-selection.md; `cases/` notes in the header; e2 / e4 / e10.

---

## 8. Uncertain / left out

- **FSA serverless chapter** — none in style-selection. Do not invent
  ratings or a quantum cell. Typical cut is **ch7 applied**.
- **Azure “Serverless architecture style” page** — 404 on 2026-09-13.
  **Roberts 2018 “five minutes”** — superseded; vendor maxima
  **deliberately not tabulated**.
- **Cold-start distributions** in [aws/ch11.md](../../../cases/aws/ch11.md)
  are a book paraphrase, not a 2026 official stat. **API Gateway HTTP
  APIs (v2), Function URLs, Lambda@Edge, durable-execution wall-clock
  max** — not fetched.
- **OpenFaaS / Knative** — named, not reviewed (reintroduce a cluster).
  **Adzic & Chatley** — not fetched. **CloudEvents** — 2018 draft; A2 /
  A6 own formats. No FaaS vs managed-container TCO study; trade-offs
  are qualitative consensus.

---
