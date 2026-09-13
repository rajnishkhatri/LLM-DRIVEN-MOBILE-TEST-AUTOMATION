---
type: research
title: 'Microkernel / plug-in architecture — external research (2026-09-13)'
description: >-
  Source-verified research backing catalog E7: application microkernel
  (core + plug-ins + registry; compile or runtime binding), quantum FACT = 1
  unless remote plug-ins make it distributed, Volatile Core / Plug-In
  Dependencies, Eclipse/Jira-style product customization, and the E8 / E11
  distinctions. No library defaults; no scoring loop.
tags: [research, system-design-patterns, E7, microkernel]
---

# Microkernel / plug-in architecture — external research (2026-09-13)

> Evidence pass for catalog **E7** (Group E; owner label “Micro Kernel -port”).
> Not a Concept. Fetched 2026-09-13. Group E bar: what the style is / is not;
> quantum as a **FACT** (no scoring micro-loop); when-to / when-not; migration;
> worked example; trade-off table; sources. **No library-defaults.**
> Workspace SoT:
> [style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md)
> (Richards & Ford FSA, ch7, ch9–19). Microkernel (ch13): **core + plug-ins;
> registry; compile or runtime binding**; partitioning **both**; **quanta = 1**;
> ratings **simplicity/cost HI; test/deploy/reliability/modularity/evolvability/
> responsiveness 3★; scale/elasticity/FT LO**. When-to: product/customization
> (per-state rules, Jira/Eclipse). Watch: **Volatile Core**, **Plug-In
> Dependencies**; **remote plug-ins make it distributed**. Cite
> `microkernel-arch-style.md:9,158-170,206-217,219-231` — **file absent**
> 2026-09-13; the comparison line is the workspace fact. A `—` cell is not a
> rating; this row has none.

---

## 1. Scope and non-goals

**Owns.** The *application* style called **microkernel** or **plug-in
architecture**: a stable **core system** plus independently developed
**plug-ins**, selected through a **registry**, bound at compile time or at
runtime. Product/customization isomorphism (Eclipse / Jira / OSGi-shaped
platforms; per-jurisdiction rules). Named risks **Volatile Core** and
**Plug-In Dependencies**. Quantum count **1**, and the one exception that
turns the style distributed.

**What it is.** Richards (*Software Architecture Patterns*, 2015-08-15): two
component types — a **core system** and **plug-in modules**. The core holds
minimal / general behaviour; plug-ins hold specialised, additional, or custom
processing. The core learns which plug-ins exist through a **registry**
(name, data contract, optional remote-access details). Plug-ins stay
independent of one another; the pattern “does not specify” the connection
mechanism, only that independence. FSA 2nd ed. ch13 (O’Reilly TOC + opening
snippet, 2026-09-13): “a relatively simple **monolithic** architecture”;
product packaged as “a single, monolithic deployment,” typically installed
on the customer site; also used for non-product custom apps whose problem is
customization. Workspace `style-selection.md` adds compile-or-runtime binding
and partitioning **both** (technical *and* domain).

**What it is not / stays in sibling ids.**

| It is not | Why |
|---|---|
| An **OS µ-kernel** (Mach, L4, MINIX, QNX) | Same *name*. Wikipedia (2026-09-13): near-minimum privileged code for address spaces, threads, IPC; drivers run as user-space **servers**. Application plug-ins usually share a process. Richards 2015 names the OS origin, then redefines the core as “general business logic sans custom code.” |
| **POSA Microkernel** (Buschmann et al., 1996) | Metapatterns.io (2026-09-13): “not … FSA.” Resource-sharing middleware. Ancestry of the name. |
| **Hexagonal / ports-and-adapters (E8)** | Cockburn (2005-09-04): a port is a *purposeful conversation*; adapters swap technologies. Ports are not a marketplace. A hexagon can have two ports and no registry. E7’s machinery is an **open, registered plug-in set**. A plug-in *contract* may be a port; that does not make every port a plug-in. |
| **Serverless & FaaS (E11)** | Roberts (2018-05-22): BaaS + **stateless, event-triggered, ephemeral** functions. A function is a *host*, not a product core + registry. Hosting a remote plug-in as a function *is* the distributed exception (§3.3). Metapatterns files FaaS under POSA, **not FSA**. |
| **Modular monolith (E10)** | Domain modules on one deployable; no registry required. ADR 0005: “Spring DI supplies the Strategy seam for free.” Compile-time Strategy ≠ microkernel. |
| **E2 / E6** | Independently deployable services. Remote plug-ins that grow their own store *leave* E7. E6 is the usual first hop. |
| Fowler **Plugin** (2003-03-05) / Martin ch.17 | Configuration-time class linking, or arrows-toward-policy plugins ([clean-architecture.md](../../../cases/coding-rules/clean-architecture.md)). Mechanisms, not a product-platform style. |
| **E1 / E3 / B4 / B6** | One-unit deploy and layered *core*; strangler is cutover; sidecar is attach. None is a registered feature plug-in. |

**Non-goals.** Library defaults (OSGi / Eclipse / Jira are *examples*).
Arch-style scoring. Invented FSA stars. Copying book figures. A Concept.

---

## 2. Lineage / vocabulary

**OS µ-kernel (analogy only).** Wikipedia (2026-09-13): near-minimum OS
mechanisms — address spaces, threads, IPC. Lineage: Brinch Hansen RC 4000
(1969); term by 1981; Mach; Liedtke L3/L4. MINIX 3 ≈ 12 000 LOC (Wikipedia
figure; not re-counted). **Do not inherit those numbers.** **POSA
Microkernel (1996)** is resource-sharing middleware, **not FSA**
(Metapatterns).

**Richards, *Software Architecture Patterns* (O’Reilly, 2015-08-15).**
https://www.oreilly.com/content/software-architecture-patterns/ — fetched
in full 2026-09-13. Mechanics, Eclipse + browser examples, insurance-claims
/ per-state plug-in worked example, connection options (OSGi, messaging,
web services, point-to-point object instantiation), contract versioning,
and the qualitative High/Low scorecard in §3.7 (a **different** book from
FSA). Also: the style “can be embedded or used as part of another
architecture pattern” for a specific volatile area; for product-based apps
it “should always be your first choice as a starting architecture.”

**Richards & Ford, FSA** (1st ed. ch12; 2nd ed. ch13). O’Reilly 2nd-ed.
TOC (search-indexed 2026-09-13; body **Access Denied**): Core, Plug-Ins,
Registry, Contracts, Common Risks (**Volatile Core**, **Plug-In
Dependencies**), Ratings. Opening snippet: single monolithic deployment;
US insurance per-state / international shipping. Ratings SoT is
`style-selection.md`; `microkernel-arch-style.md` is missing.

**Eclipse (product exemplar).** Kim Moir, AOSA vol. 1, “Eclipse”
https://aosabook.org/en/v1/eclipse.html — fetched 2026-09-13. Eclipse 1.0
(2001-11-07): “an IDE for anything and nothing in particular” — a
**framework**. Component = **plugin** (JAR + manifest). **Extension
points** (provider) / **extensions** (consumer). Startup: scan manifests →
in-memory **plugin registry** (cached); plugins **discovered**, not
**activated** until used (**lazy activation**). Eclipse 3.0: **OSGi**
(Equinox); plugins become **bundles**. Mantra: **“API is forever.”**
Helios (June 2010): 39 projects, 490 committers, 40+ companies.

**Jira Plugins2** (updated 2026-09-10)
https://developer.atlassian.com/server/jira/platform/plugins2-add-ons/ —
JAR + `atlassian-plugin.xml` modules, Universal Plugin Manager,
Marketplace. Unique add-on key. **OSGi Core R8** approved 2020-12-09
(https://docs.osgi.org/specification/osgi.core/8.0.0/framework.module.html):
one class loader per bundle; packages hidden unless exported. Richards
2015 lists OSGi as a *connection* option, not as the style.

**Cockburn** (2005-09-04) — sibling **E8**. **Fowler, Plugin** (2003-03-05)
— mechanism E7 *may* use. **Azure styles catalog** (fetched 2026-09-13):
N-tier, Web-Queue-Worker, Microservices, Event-driven, Big data, Big
compute. **No microkernel row.** Do not invent an Azure rating.

---

## 3. Mechanics (Group E depth bar)

### 3.1 Topology — core + plug-ins + registry

**Core.** Richards 2015: traditionally “only the minimal functionality
required to make the system operational”; in a business app, “the general
business logic sans custom code for special cases, special rules, or
complex conditional processing.” FSA opening snippet: the happy path
without customer-specific logic. The core **may itself** be layered.
Eclipse’s early picture: open / edit / save until plug-ins make it an IDE.

**Plug-ins.** Stand-alone modules with specialised processing, extra
features, or custom code. Richards 2015: generally independent; you *can*
design plug-ins that require others, but “keep the communication between
plug-ins to a minimum to avoid dependency issues.” Delivery: source, a
rules-engine instance, JAR, DLL, or (if you accept distribution) a remote
endpoint.

**Registry.** The core “needs to know about which plug-in modules are
available and how to get to them” (Richards 2015). Example entry:
tax-audit plug-in `AuditChecker`, input/output contract, format (XML),
optional WSDL if SOAP. Eclipse: in-memory map of extension point →
extensions, built by scanning manifests, cached on disk (AOSA). Jira:
`atlassian-plugin.xml` modules registered with Plugins2 and the Universal
Plugin Manager. Binding without a registry (a single Spring `@Bean`
selected by config) is **E10 / Strategy**, not this style — ADR 0005.

**Contracts.** Richards 2015: standard (XML / map) or custom (third-party).
Custom contracts get an **adapter** so the core does not grow per-plug-in
special cases. “Create a versioning strategy right from the start.”
Eclipse: “API is forever” (AOSA). A contract change is how Volatile Core
becomes expensive.

**Partitioning.** `style-selection.md`: **both** technical and domain. The
*cut* core vs plug-in is usually domain-shaped (per-state rules,
per-language tooling, per-app Jira module); the *core’s internals* are
often technical layers.

### 3.2 Binding time and process placement

Richards 2015 connection options (the style specifies none of them):

| Binding | What it is | Quantum effect |
|---|---|---|
| Point-to-point object instantiation | Compile- or load-time `new` / DI of a known type | Stays **1** |
| OSGi / Equinox / Plugins2 | Runtime bundle/JAR install, own class loader, lazy activation | Stays **1** while in-process and sharing the product’s store |
| Messaging or web services | Plug-in is a remote process | **Distributed** — `style-selection.md` watch; ch9 fallacies apply; **no longer one quantum** |

**In-process isolation is a dial, not a given.** OS µ-kernels isolate via
address spaces. Eclipse isolates via **per-bundle class loaders** and
exported-package visibility (AOSA; OSGi R8). A plain JAR-on-the-classpath
plug-in shares the host heap: a plug-in OOM takes the core with it. Do
not claim OS-grade fault isolation (`style-selection.md`: FT **LO**).

### 3.3 Quantum count — FACT = 1 (unless remote plug-ins)

Workspace `style-selection.md` matrix: Microkernel **Quanta = 1**.

Quantum (same file, ch7): smallest independently runnable part; **the
database is part of the quantum** — a single shared DB ⇒ quantum of one;
independent deployability; high functional cohesion; low external
implementation static coupling; synchronous communication with other
quanta. Coupling test: “two things are coupled if changing one might
break the other.”

Why the typical product stays at one: FSA / Richards call it a
“relatively simple **monolithic** architecture,” packaged as “a single,
monolithic deployment.” JAR/DLL plug-ins in the product process are not
independently runnable. A shared core database folds plug-ins back into
one quantum even if they look modular.

**The documented exception.** `style-selection.md`: “remote plug-ins make
it distributed.” Independently deployable remote plug-ins with their own
store and network calls are extra quanta — and you pay the eleven
fallacies (same file, ch9). Honest catalog home is then **E6 / E2**, with
a plug-in *façade*, not E7 with a larger star on scalability. Hosting
that remote plug-in on **E11** (a function) does not put the system back
to one quantum. Replicating the whole product behind a load balancer is
more instances of the **same** quantum, not more quanta.

### 3.4 Named risks — Volatile Core / Plug-In Dependencies

FSA 2nd-ed. TOC names both under **Common Risks**. Workspace
`style-selection.md` tells the reader to watch them
(`microkernel-arch-style.md:158-170`). The missing note is not in-tree;
definitions below are from Richards 2015 plus the workspace
style-decision. **Exact FSA sentences are unrecovered** (§8).

**Volatile Core.** The core’s interfaces or happy-path workflows change
often enough that plug-ins break on every release. Causes: variation
points misidentified; the core tries to do too much; or the domain’s
*real* volatility sat in the core (workspace: conversion flow rewritten
in Phase 2). Eclipse’s counter-measure: “API is forever” plus export-only
public API (AOSA).

**Plug-In Dependencies.** Plug-ins call each other (A requires B requires
C). Richards 2015 warns to minimise inter-plug-in communication. You lose
independent extension; compatibility matrices explode. Allowed exception:
the **core mediates**. Eclipse *does* allow `requires` / OSGi
`Import-Package` between bundles — that is the expensive, governed form
of the exception. Jira modules compose through the *platform*, not by one
add-on linking another as a library of record.

### 3.5 Worked example — insurance claims (Richards 2015) and Eclipse

**Claims processing (Richards 2015, paraphrase).** The **core** intakes,
validates, reserves, and pays — the happy path true in every US state.
Each **state** is a plug-in (code *or* a rules engine). Example: some
states allow free windshield replacement after rock damage; others do
not. The **registry** selects the jurisdiction. Adding Idaho does not
edit Texas or the core. Alternative: one giant rules engine that becomes
a **big ball of mud** — “an army of analysts, developers, and testers.”
This is the **domain-to-architecture isomorphism** `style-selection.md`
asks for.

**Eclipse (AOSA + Richards).** Downloaded SDK = platform (Platform + JDT
+ PDE); everything else is a plugin. A third party implements
`org.eclipse.ui.actionSets`; the registry finds it without loading
classes until the user clicks (lazy activation). Jira Plugins2 repeats
the shape with `atlassian-plugin.xml` and a marketplace.

**Workspace counter-example (when *not* to pay for the registry).**
[style-decision.md](../../architecture/worksheets/mobile-test-automation/style-decision.md)
§5 (gate closed 2026-07-26): the stage recommended registering source
adapters and reasoning providers as plug-ins. The gate **declined**: one
week-3 adapter does not need a registry; Spring DI already is the
Strategy seam; Volatile Core was live because Phase 2 rewrites
conversion. Cost accepted: no runtime structure; protection = ADR 0001 +
F1/F2. Flip condition (ADR 0005): a fourth source adapter or a second
concurrent provider **reopens** microkernel. Cite; do **not** re-score.

### 3.6 When to use / when not

**When.** Product/customization domains; per-state rules; Jira/Eclipse-style
extensibility; strong domain ↔ architecture isomorphism
(`style-selection.md`). Richards 2015: downloadable products, or internal
apps *released like* products; first-choice start when features will drip.
FSA opening snippet: also non-product custom apps (US insurance per state;
international shipping). Eclipse / Jira: third parties extend a platform
you do not recompile per customer. Richards “embed”: isolate *one* volatile
area; do not force the whole system into the style.

**When not.**

| Signal | Move toward |
|---|---|
| Variation sat in the *core* (Volatile Core) | Wrong partition or wrong style. Workspace: live risk on conversion. |
| One or two strategies, compile-time selection enough | **E10** + interfaces (ADR 0005). Registry is machinery. |
| Independent feature deploy / scale / FT as top-3 | Not this style (scale/elasticity/FT **LO**). First hop usually **E6**. |
| Remote plug-ins already independently deployed | Already distributed. Name E6/E2 (or E11 *hosting*); keep a plug-in *façade* only if the registry still earns its keep. |
| Domain-shaped change *without* a third-party ecosystem | E10 (modules) and/or E8 (ports) inside one quantum. |
| Extreme mechanism/policy split over hardware | POSA/OS Microkernel, not E7. |
| “Just put each plug-in on a function” | **E11 hosting** of the remote-plug-in exception, not E7. |
| Simple app, no customization | Richards 2015 ease-of-development **Low**. Do not buy the machinery. |

### 3.7 Migration in and out

**In.** Greenfield product (Richards: first choice). Extract
per-jurisdiction conditionals out of a rules-engine mud (Richards claims
example). Hybridize *one* seam of an E10/E3 system when a third-party
ecosystem appears (workspace flip). Adopt a host that already is one
(Eclipse RCP, Jira).

**Out (cheapest first).** (1) Drop the registry, keep the interfaces
(**E10**) — ADR 0005; fitness functions become load-bearing. (2) Invert
technology edges (**E8**) inside the core — no new quantum, no
marketplace. (3) Mediate remaining plug-in-to-plug-in calls through the
core. (4) Version the contract rather than growing the core. (5)
**Strangle** a plug-in out (**B4**) — do not “just make every plug-in a
REST service / function” (remote exception + ch9; **E11** if the host is
FaaS). (6) **E6** if multiple characteristics sets appear. (7) **E2**
only after granularity and data ownership are fixed.

**Do not** treat each *layer* of a layered core as a plug-in (E3
sinkhole). **Do not** call Spring/DI a completed microkernel.

### 3.8 Trade-off table (no invented FSA stars)

FSA ch13 scorecard: **only** the prose-recovered line in
`style-selection.md`. Richards 2015 High/Low is a different book.

| Concern | Tendency | Trade-off |
|---|---|---|
| **Cost / simplicity** | FSA: **HI** | Cheap vs E2/E6. Richards ease-of-development **Low** — registry, contracts, granularity, connection choices are real design cost. Both can be true: cheap *ops*, expensive *design*. |
| **Test / deploy / reliability / modularity / evolvability / responsiveness** | FSA: **3★** | Isolated plug-in tests and hot-deploy (Richards: test/deploy **High**) sit *inside* a 3★ band, not a 5★. |
| **Scale / elasticity / FT** | FSA: **LO** | Typical product is one process + one fate. Richards scalability **Low**. Class-loader isolation ≠ process isolation. |
| **Agility (Richards 2015)** | **High** | Changes isolate in plug-ins *if* the core is already stable. Volatile Core inverts this. |
| **Performance (Richards 2015)** | **High** | Trim unused features (his JBoss example). **Not** an FSA cell; FSA prints **responsiveness 3★**. |
| **Third-party ecosystem** | The win | Eclipse/Jira marketplace. Cost: “API is forever,” adapters for custom contracts, compatibility matrices. |
| **Remote / FaaS plug-ins** | Scale a feature | Leaves quantum **1**. Pay ch9; catalog home becomes E6/E2 (+ E11 host). |

---

## 4. Verified defaults / standards

**None.** Group E has no library defaults. OSGi / Eclipse / Jira APIs are
existence proofs, not defaults to copy.

---

## 5. Failure modes and when-not-to-use

| Failure | What it looks like | Counter |
|---|---|---|
| **Volatile Core** | Every core release breaks the field’s plug-ins | Re-partition; “API is forever”; versioned contracts; or leave |
| **Plug-In Dependencies** | A requires B requires C; combinatorial QA | Core mediates; forbid compile-time plug-in→plug-in deps |
| **Registry as costume jewelry** | One Strategy + a “plugin manager” + a config flag | E10 + DI; reopen E7 on the flip condition (ADR 0005) |
| **Remote plug-ins, still scored as one quantum** | Network + shared DB + “we’re still a monolith” | Recount quanta; name E6/E2; pay ch9 |
| **FaaS plug-ins labelled E7** | Each extension is a function; no stable core API | E11 hosting of a distributed plug-in, not one-quantum E7 |
| **Shared-DB coupling** | Plug-in schema changes break the core (and vice versa) | Separate store *or* accept quantum = 1 honestly |
| **False fault isolation** | One plug-in OOM takes the product down | Class-loader isolation ≠ process isolation; FT stays LO |
| **Over-pluggability / custom contracts** | Everything is an extension point; core grows `if (plugin == X)` | Plug real variation axes; adapter to the standard contract |
| **OS/POSA or ports called plug-ins** | IPC-budget review, or two adapters labelled “microkernel” | Keep E7 on the application side; that is E8 until a registry exists |

When-not is in §3.6. Short form: do not pick E7 as the macro style when
the core is volatile, when one compile-time Strategy suffices, when you
need ops the monolith cannot give, or when you remote/FaaS every plug-in
and still call it one quantum.

---

## 6. Cross-links

**E8** — ports ≠ plug-ins (technology vs product). **E11** — hosting; a
function may *host* a remote plug-in and that leaves quantum 1. **E10** —
same quantum, no registry (ADR 0005). **E2 / E6** — after remote plug-ins
become services. **E1 / E3** — one-unit deploy; layered *core*. **B4** —
strangle a plug-in out. **B6** — sidecar, different intent.
[style-selection.md](../../../.cursor/skills/arch-style/references/style-selection.md)
— quanta = 1; ratings; remote → distributed.
[style-decision.md](../../architecture/worksheets/mobile-test-automation/style-decision.md)
+ [ADR 0005](../../architecture/adrs/application/mobile-test-automation/0005-adopt-plain-modular-monolith-partitioned-by-cluster.md)
+ [ADR 0001](../../architecture/adrs/application/mobile-test-automation/0001-route-every-model-call-through-invoke-models.md)
— declined hybridization; flip condition.
[components.md](../../../cases/coding-rules/components.md) /
[boundaries.md](../../../cases/coding-rules/boundaries.md) — JAR/DLL and
dependency-rule plugins as *mechanism*, not E7.

---

## 7. Sources

Retrieved **2026-09-13**.
1. Richards, *Software Architecture Patterns*, 2015-08-15. https://www.oreilly.com/content/software-architecture-patterns/ — core + plug-ins + registry; Eclipse/browser; claims example; connection options; High/Low.
2. FSA 2nd ed. ch13 TOC + opening snippet. https://www.oreilly.com/library/view/fundamentals-of-software/9781098175504/ch13.html — named risks; “monolithic deployment”; customization domains. **Body Access Denied.**
3. Fowler, *Plugin*, 2003-03-05. https://martinfowler.com/eaaCatalog/plugin.html
4. Cockburn, HaT 2005.02, 2005-09-04. https://alistair.cockburn.us/hexagonal-architecture — E8.
5. Wikipedia, *Microkernel*. https://en.wikipedia.org/wiki/Microkernel — OS analogy only.
6. Metapatterns, *Microkernel*. https://metapatterns.io/implementation-metapatterns/microkernel/ — POSA ≠ FSA; FaaS filed under POSA.
7. Moir, AOSA “Eclipse”. https://aosabook.org/en/v1/eclipse.html — registry, lazy activation, OSGi/Equinox, “API is forever,” Helios counts.
8. Atlassian Plugins2 (updated 2026-09-10). https://developer.atlassian.com/server/jira/platform/plugins2-add-ons/
9. OSGi Core R8 module layer. https://docs.osgi.org/specification/osgi.core/8.0.0/framework.module.html — plus https://blog.osgi.org/2020/12/osgi-core-release-8-is-now-final-and.html (approved 2020-12-09).
10. Azure styles catalog. https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/ — **no** microkernel row.
11. Workspace: `style-selection.md`; ADR 0005; ADR 0001; `style-decision.md`.

---

## 8. Uncertain / left out (excluded from any future Concept)

- **`microkernel-arch-style.md` body.** Cited at :9, :158–170, :206–217,
  :219–231; **file absent** 2026-09-13. Do not back-fill from blogs.
- **Exact FSA wording** of Volatile Core / Plug-In Dependencies, and the
  2nd-ed. body (Spectrum of “Microkern-ality”, Data Topologies, Cloud,
  Governance, Team Topology). TOC + Access Denied; definitions above are
  Richards 2015 + the workspace style-decision.
- **FSA star-rating figure.** Prose-recovered line is the only allowed
  scorecard. Third-party tables conflict; unused. Richards 2015 High/Low
  is a different book — do not merge.
- **jessebellingham.com ch.12.** Claims remote plug-ins are “still a
  single quantum, because every request must first go through the core.”
  **Conflicts** with `style-selection.md`. Workspace SoT wins; unused.
- **POSA1 full text**, **Jira Cloud / Forge**, **browser-extension
  sandboxes**, Azure `ms.date` — not fetched.
- **Arch-style scoring loop** — not run, by Group E rule.

Not facts for a future Concept.
