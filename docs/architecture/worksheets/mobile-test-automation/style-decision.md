---
type: architecture
title: Style decision and quantum map — Mobile Test Automation LLM Pipeline
description: 'Stage-3 (arch-style) quantum scoping and style selection for the mobile-test-automation target, gate closed with one variance: decision-readiness audit with named missing inputs, the four determinations (one quantum, four-concern data topology, two async seams, plain modular monolith after the gate declined the recommended microkernel hybridization), a trade-off matrix over the driving characteristics, the losing candidates and why they lost, the edge/access topology the component stage excluded, the eight-ADR plus seven-fitness-function follow-on list handed to stage 4, and the adjudicated post-gate critical review (five precision corrections accepted, no determination changed).'
tags: [architecture, mobile-test-automation, arch-style, kata]
---

# Style Decision & Quantum Map — Mobile Test Automation LLM Pipeline

- **Target:** mobile-test-automation
- **Artifact home:** `docs/architecture/` (per the `[roots]` override in `.arch/binding.toml`)
- **Stage:** 3 (arch-style)
- **Mode:** kata (premises = research synthesis + blueprint v2 + compass artifact + stage-1 worksheet rev 3 + stage-2 components rev 3)
- **Date:** 2026-07-26
- **Status:** **GATE CLOSED 2026-07-26, with one variance** — all four determinations confirmed separately per the conflated-axes rule. Determination 4 varied from the recommendation: the gate declined the microkernel hybridization in favour of a plain modular monolith. See §8. **Post-gate critical review adjudicated 2026-07-26** — five findings accepted (wording and precision corrections, no determination changed), one rejected. See §9.
- **Inputs:** stage-1 top 3 = **reproducibility, security & privacy, verifiability**; four more driving = evolvability/replaceability, reliability & recoverability, auditability & traceability, interoperability. Stage-2 set = **16 components in 3 clusters**.
- **Methodology:** `cases/ArchitectureBook` ch7 (quantum), ch9 (fallacies), ch10–18 (styles), ch19 (`choosing-appropriate-arch.md`), ch27 (`laws-of-software-arch.md`). Trade-off procedure from `arch-lifecycle/references/laws.md`.

---

## 0a. Disclosure — anchoring exposure, declared per the stage's own rule

The stage instructions seal the book's worked kata answers in
`arch-style/references/worked-answers.SEALED.md` and require disclosure if that content reaches context
before the determinations are written. It did not — but an equivalent exposure did, and the rule's intent
covers it.

**What happened.** Step 1 of this stage directs a read of `choosing-appropriate-arch.md:44-68` for the
decision-readiness criteria, and step 4 directs `:98-102` for the sync/async default. That file is 192
lines and was read whole. Lines 106–191 of it *are* the book's worked answers for Silicon Sandwiches
(single quantum; modular monolith vs microkernel; sync throughout) and Going, Going, Gone (distributed;
microservices; async where quanta mismatch; five quanta). **The seal does not cover the methodology
chapter itself, only the skill's reference copy — so the fence has a second gap.**

**Honest assessment of the effect.** No answer was available to copy: both worked katas are unrelated
domains (a sandwich shop and an online auction), and this target is a test-conversion pipeline. But the
anchoring risk is real and specific: seeing "single quantum ⇒ modular monolith *or* microkernel" before
building the shortlist may have shaped the shortlist in §5.

**So the convergence is downgraded to weakened evidence.** It remains true that the pick here is
independently supported by two target-specific facts the book's katas do not contain — the coupling test
on the IR spine and the CA = 13 provenance contract (§2), and a driving characteristic *displaced from the
top 3 at a human gate* that needs compensating structure (§5, worksheet §7). What cannot be claimed is
that the shortlist was formed blind. The genuine divergence from the anchor is also recorded: the book
presented modular monolith and microkernel as **alternatives**; this stage picks a **hybridization** of
both, for a reason specific to this target.

**Suggested fix to the skill family, for whoever maintains it:** the seal should cover ch19's worked case
studies in the methodology bundle too, or step 1 should cite a line range and forbid the whole-file read.
Recording it here because this is the third recurrence of the same class of defect (SD1, 2026-07-24;
recurred 2026-07-25).

---

## 0. A premise that must be handled honestly before anything else

The blueprint already names a style: *"the runtime is a Spring Boot modular monolith"*
(`blueprint-revision-v2.md:11`). The stage constraint says **style follows characteristics — never lead
with a style** (`choosing-appropriate-arch.md:52`).

Both can be true without contradiction, but only if this stage does real work rather than ratifying the
premise. So the premise is treated as a **candidate under test**, not as a decision already taken. It is
scored against the alternatives in §5 on the characteristics the stage-1 worksheet actually derived, and
§5 states plainly where it strains and what the failing conditions would look like.

What this stage found: the premise survives as the macro style, but **not in the form the blueprint
states it.** A plain five-module monolith does not protect the characteristic that lost its top-3 rank,
and the blueprint's module list is partitioned along the *pipeline stages*, which is a technical
partitioning that the modular monolith style is explicitly not for. Both are corrected in §5.

---

## 1. Decision-readiness audit

Per `choosing-appropriate-arch.md:44-68`. Missing inputs are **named, not assumed**; each becomes a
`needs-input` tag on the determinations it affects.

| Factor | Status | Evidence or gap |
|---|---|---|
| **The domain** | Ready | Journey-shaped: manual asset in, certified test out. Five workflows modeled in stage 2 §2 |
| **Characteristics analysis** | Ready | Stage-1 worksheet rev 3, gate closed, seven driving with measures |
| **Data architecture** | **`needs-input` — the largest gap** | No database is named anywhere in the sources. "Per-test persistence, so an interrupted batch resumes" (`:67`) implies one; nothing states technology, schema plan, retention design, or where device artifacts (video, page source, network captures) are stored. This is load-bearing for cluster C, which is regulated. §3 proposes a topology and flags every assumption |
| **Cloud vs on-prem intent** | **`needs-input`** | Mixed and unstated for the pipeline's own runtime. Perfecto is SaaS; Orchestrator AI is an internal gateway; Octane and ALM/QC are enterprise systems; the worksheet mentions "on-prem/VPC LLM" only as a candidate source. The evidence store's residency has regulatory consequences in a banking context and cannot be inferred |
| **Organizational factors** | **`needs-input`** | No infrastructure budget stated. Only *device minutes* are named as a cost driver (`:105`). No M&A posture. The absence of an infra budget matters because it is the usual argument against a distributed style, and here it cannot be invoked as evidence |
| **Process / team / operational maturity** | Partial | Inferable but not stated: CI exists (`:49`), OpenTelemetry and a trace store are specified (`:37`), and the roadmap runs weeks 0–22 as a single workstream, which implies a small team. **Team size and Agile/ops maturity are not stated** — decisive for any distributed candidate, since `:68` names exactly that as the reason microservices fails in immature organizations |
| **Domain/architecture isomorphism** | Ready | Two strong shapes found, §5 |

**Effect of the gaps.** Determination 2 is the one materially weakened — it is presented as a
recommendation with its assumptions labeled, not as a settled topology. Determinations 1, 3 and 4 are
robust to the gaps, because they turn on coupling and characteristic divergence rather than on
infrastructure. Any distributed candidate carries a `needs-input` tag for team maturity throughout.

---

## 2. Determination 1 — one quantum, or many?

**Answer: one quantum. Two candidates for extraction were examined and both fail the coupling test today.**

### Why the divergent clusters do *not* imply distribution

Stage 1 §10 found three clusters with genuinely counteracting characteristic sets, which is normally the
distributed signal (`ArchCharScope.md:92-94`). But the quantum is defined by *coupling*, not by
characteristic divergence, and the coupling test is: **"two things are coupled if changing one might break
the other"** (`ArchCharScope.md:52`). Applied to the three clusters:

| Coupling found | Reading |
|---|---|
| The IR spine — `TestCaseIR`, `LocatorCandidate`, `ReplayReport` — is shared across nearly every component (stage 2 §9, static Connascence of Name + Type) | A schema change breaks all three clusters simultaneously. They are coupled by construction, and deliberately so: "the schemas are the spine; every module is swappable as long as the schemas hold" (`blueprint-revision-v2.md:21`) |
| Preserve Provenance has **CA = 13 of 16** components (stage 2 §8) | If lineage is one store, thirteen components are in its quantum. A single shared database means a quantum of one (`ArchCharScope.md:36`) |
| Certify Conversion → Invoke Models, synchronous, crosses B→A (stage 2 §1a) | Synchronous calls between mismatched quanta collapse them into one and the caller inherits the slower partner's characteristics — Dynamic Quantum Entanglement (`ArchCharScope.md:72-74`) |

So the clusters are **module boundaries, not quantum boundaries.** That is not a downgrade: keeping them
as named module seams with the tables partitioned to match (§3) is precisely what makes a later split
cheap (`choosing-appropriate-arch.md:116`).

### The phase asymmetry, resolved

The quantum count is not the same in both phases, and this is the determination's most useful finding.

| | Cluster A (conversion) | Clusters B + C | Quantum count |
|---|---|---|---|
| **Phase 1** | Conversion reasoning performed by a human in an IDE with Copilot; two cluster-A components ship as CLIs (ingestion, hierarchy tool) and Route Human Decisions runs as a service | Automated services | **One.** Phase 1 conversion contributes **no service components for the reasoning path** — the human plus IDE is a workflow with tooling. Cluster A is thinner in Phase 1, not absent: its CLIs, the review queue, and the asset library are already runtime concerns *(wording corrected after the post-gate review, §9 — an earlier draft said cluster A was "not in the architecture," which its own CLIs contradict)* |
| **Phase 2** | Becomes services in the same runtime | Unchanged | **One**, *if and only if* Phase 2 adds modules inside the existing quantum |

This makes the blueprint's central promise falsifiable rather than rhetorical. *"Phase 2 replaces the
human driver with orchestration code. Nothing else moves"* (`:55`) holds **only** if Phase 2 grows a
module rather than spawning a quantum. Recommending one quantum for both phases is therefore the reading
that keeps the program's own premise intact — and it is testable as a fitness function.

### The two extraction candidates, and why both fail today

| Candidate | Case for extraction | Why it fails the coupling test now |
|---|---|---|
| **Replay on Devices** | The system's dominant cost, rate-limited by lab capacity, inherently flaky, runs on a CI cadence — the most operationally divergent component in the set | It writes lineage to the shared provenance store and reads committed code and pinned capability sets. It needs *asynchronous decoupling*, which §4 grants, but async workers over a shared store are **the same quantum**, not a new one. Extraction buys independent scaling of something whose scarcity is external (the lab), so it buys nothing |
| **Preserve Provenance / cluster C** | Genuinely different lifecycle — append-only, retention-governed, "outlives both other clusters"; regulated; the one component an auditor must reach without touching the running system | It is the single most-depended-on contract in the system (CA = 13). Extracting it converts thirteen in-process contract calls into thirteen network calls, and audit writes must be transactionally consistent with the state changes they describe (§4) — which a network boundary makes materially harder. **Revisit when** the retention or residency requirement makes co-location illegal rather than merely untidy |

**Quantum map.** One quantum, containing all sixteen components; three module boundaries drawn on the
cluster lines; two async seams inside the quantum (§4); five external integration points outside it.

**Rendered (skill pipeline):**
[`diagrams/quantum-map.view.md`](diagrams/quantum-map.view.md)
· [svg](diagrams/quantum-map.svg)
· [PNG](diagrams/quantum-map@2x.png)
· [grayscale proof](diagrams/proofs/quantum-map-gray.png)
· IR [`diagrams/ir/quantum-map.json`](diagrams/ir/quantum-map.json)
· [SELF-AUDIT](diagrams/SELF-AUDIT.md).

![Determination 1 — Quantum map: one quantum, three module seams](diagrams/quantum-map.svg)

> One architecture quantum (`conversion-and-certification runtime`) with three module seams named on
> the box (conversion · validation-certification · evidence). Numbered edges 1–7; full claims and the
> per-module component lists live in the [combined view](diagrams/quantum-map.view.md). Solid = sync,
> dashed = async. Primary datastore omitted here (Determination 2; residency `needs-input`).

**Confirm separately:** one quantum for both phases; clusters as module seams rather than deployment
boundaries; both extraction candidates deferred with the named revisit triggers.

---

## 3. Determination 2 — where does data live?

`needs-input` on data architecture and residency (§1). What follows is a recommendation with its
assumptions labeled, not a settled topology. The monolith-means-one-relational-database assumption is
challenged rather than inherited (`choosing-appropriate-arch.md:93`).

**Four data concerns with genuinely different profiles — and one of them is already decided.**

| Concern | Profile | Recommendation | Basis |
|---|---|---|---|
| **Conversion state** — per-test checkpoint/resume, retry budgets, state transitions | Transactional, small, high write frequency, needs ACID or resume is incorrect | Relational, in the primary store | "Explicit state transitions and per-test persistence, so an interrupted batch resumes" (`:67`) |
| **Lineage metadata** — source asset → IR → prompt/model version → commit → runs → human decisions | Append-only, immutable, retention-governed, regulated, read-heavy for the metrics projection | Relational, in the primary store, **in its own schema with its own retention and grant model** | Stage 1 auditability measures; stage 2 §8 |
| **Device artifacts** — video, page source, network captures, screenshots | Large, binary, PII-bearing, classified, retention-bounded | Object/blob storage; the store holds **references plus classification plus retention date**, never the payload | Stage 1: "classify and redact at capture, retain references plus redacted evidence, bound retention" |
| **Conversion assets** — prompts, house rules, exemplars, golden set | Versioned, reviewed, diffable | **Git — already decided in the sources, not a database question.** "Versioned in Git", "same Git paths", "committed to the repo" (`:47,59,60`) | This is why version identity is free and why Retrieve Conversion Assets is a stable component |

Plus one external store unchanged: the **object repository** for certified locators, written under
single-writer discipline (`:105`).

**The recommendation that matters most.** Even inside one database, **partition the tables along the
module lines from day one** — conversion-state tables separate from lineage tables, with no foreign keys
from lineage into conversion state. The book's reason is migration cost
(`choosing-appropriate-arch.md:116`); the stronger reason here is that the two have **opposite
lifecycles**: conversion state is disposable once a test is certified, lineage is retained for years under
a regulatory clock. A schema that entangles them makes retention deletion either impossible or unsafe —
and retention is a stage-1 security measure, not housekeeping.

**Data-flow consequence for reproducibility.** Every write to lineage must carry the full pinning set
(`irVersion`, `codeCommit`, `pipelineVersion`, `appiumVersion`, device/OS/model, `appVersion`, prompt
version, model/provider version, and — new in stage 2 rev 3 — the judge's calibration version). If any
pinning field is written to a different store than the verdict it belongs to, reconstruction requires a
join across systems and the auditability measure "reconstructs from stored evidence alone" fails. This is
the strongest argument in this section for a single primary store.

**Confirm separately:** the four-concern split; Git as the asset store (already implied by the sources);
table partitioning along module lines with no cross-lifecycle foreign keys; blob storage for artifacts
with references in the primary store.

---

## 4. Determination 3 — synchronous or asynchronous?

Default synchronous; asynchronous only where necessary (`choosing-appropriate-arch.md:98-102`). Three
seams earn async. Everything else stays synchronous, including one place where async would be actively
harmful.

| Seam | Verdict | Reasoning |
|---|---|---|
| **Coordinate Conversion → Replay on Devices** | **Async — necessary** | This is the GGG payment case exactly (`choosing-appropriate-arch.md:184`): a rate-limited downstream plus simultaneous demand equals timeouts and reliability headaches. Device acquisition is capacity-bounded, K runs take minutes, and the whole tiered-gate design exists because device work is scarce while static rejection is free. A queue in front of device replay is also what makes "interrupted batch resumes with zero duplicated device runs" achievable |
| **Coordinate Conversion → Route Human Decisions** | **Async — necessary** | Humans respond in hours or days. Already identified in stage 2 §6 as "an asynchronous edge in the middle of the state machine." The state machine must persist and resume across it, which is the same checkpoint mechanism the device seam needs |
| **Certify Conversion → Invoke Models** (the fidelity grade) | **Synchronous — accepted, with a stated expiry condition. This is ADR-4** | See below |
| **All component-to-component calls inside a module** | Synchronous | In-process, fast, and simplicity is the monolith's whole advantage |
| **Every write to Preserve Provenance** | **Synchronous, and in the same *local* transaction as the state change it describes** | Async audit writes create lineage gaps under failure, and a lineage gap is an auditability failure, not a performance detail. The stage-1 measure is "100% lineage completeness — no missing link in the chain." This is a case where the convenient answer is the wrong one, so it is stated rather than left to inference. **At the two async seams this rule means local transactions on each side of the queue** — the producer records the enqueue via a transactional outbox in the same transaction as its state change, and the consumer writes its own lineage in its own transaction with idempotent handling — **never a distributed transaction spanning the queue** (clarified after the post-gate review, §9; carried into ADR-7) |

### ADR-4 resolved: accept the entanglement synchronously — no quantum collapse, but a live availability coupling

The pass-3 gate merged the fidelity judge into Certify Conversion, which made cluster B call the gateway
synchronously. The escalation was correct, and the resolution is this:

**The *quantum-collapse* cost of Dynamic Quantum Entanglement only materializes across a quantum
boundary.** With Determination 1 answering *one quantum*, cluster B and cluster A already share a
deployment, a datastore, and a lifecycle — so cluster B inheriting cluster A's provider dependency
changes no *deployment* property it did not already have. Certification is also not latency-sensitive:
it runs after K device runs that took minutes, so a gateway call adds nothing perceptible.

**What is still paid from day one, stated rather than hidden** *(correction from the post-gate review,
§9 — an earlier draft called this an "expiry condition," which mislabeled a live cost as a future
one)*: certification now carries the gateway's **availability and rate-limit profile, and a per-verdict
token cost**, where previously only conversion did. Mitigation, in force immediately: certification
treats a fidelity grade as **recorded evidence** with the judge's calibration version pinned — a grade
obtained earlier remains valid, certification never re-grades on retry, and a gateway outage delays
new grades without invalidating existing ones.

One genuine expiry condition remains in the ADR:

1. **If cluster B is ever extracted** (the Determination-1 revisit trigger), this edge is the first thing
   that must change — to an async grade, or to grading in cluster A with certification consuming a
   recorded result.

### ADR-3 resolved: orchestration, not choreography

Deferred from stage 2 §8 (Coordinate Conversion at CE = 11, I = 1.00). **Recommendation: keep central
orchestration.**

| | Central orchestration (recommended) | Event-driven choreography |
|---|---|---|
| Fan-out | CE = 11 concentrated in one component | Distributed; no single high-fan-out component |
| Reproducibility (top-3) | **Strong** — one place holds state transitions and retry budgets, so a verdict's path is a readable sequence | **Weak** — reconstructing "what happened in what order" from events is the known cost, and reconstruction is the auditability measure |
| Traceability (driving) | Straightforward | The book rates EDA's simplicity and testability LO for exactly this reason |
| Fit to the domain | The flow is a bounded sequence with two bounded loops and an escalation | Choreography suits "react to things that happened"; this is request-shaped batch work |

Orchestration is not free: CE = 11 with I = 1.00 remains real, and the mitigation stands from stage 2 §8 —
the coordinator must depend only on stable contracts and must not hold policy that belongs to Certify
Conversion. **It is acceptable because nothing depends on it (CA = 0)**, which is the condition that makes
maximal instability correct for an orchestrator rather than dangerous.

**Confirm separately:** the two async seams; synchronous provenance writes in-transaction; ADR-4's
"accept synchronously, with expiry conditions"; ADR-3's central orchestration.

---

## 5. Determination 4 — style selection

### Shortlist and why these three

Candidates consistent with one quantum (§2). Distributed styles are scored as the losing alternatives
rather than excluded silently.

**Isomorphism check** (`choosing-appropriate-arch.md:70-85`) — two shapes found in this domain, and one
anti-shape:

- **Pipeline shape.** The domain is literally producer → transformer → tester → consumer: ingest,
  interpret, resolve, generate, verify, replay, certify. Strong isomorphism.
- **Customization shape.** Two seams vary independently of the core: **source adapters** (Excel, then
  Octane, then ALM/QC — additive on the roadmap) and **reasoning providers** (Copilot → Orchestrator AI →
  future). That is microkernel-shaped, and it is the shape that carries the characteristic which lost its
  top-3 rank.
- **Anti-shape: this domain is semantically coupled.** The IR spine crosses nearly every component, and
  certification plus publication must be atomic. `choosing-appropriate-arch.md:85` names a semantically
  coupled domain as the case that suits an *intentionally coupled* style and matches microservices poorly.

### Trade-off matrix — driving characteristics as rows

Weighting per the procedure in `laws.md:41-174`. **Ratings marked `[book]` are prose-recovered from the
style notes; ratings marked `[reasoned]` are this analysis, because the book's star charts cover a
different characteristic vocabulary (scalability, elasticity, fault tolerance) than the one stage 1
derived (reproducibility, auditability, verifiability). No star figures survived into the notes; none are
invented here.**

| Driving characteristic (top 3 in bold) | Modular monolith | Microkernel hybrid | Pipeline (as macro style) | Service-based | Microservices |
|---|---|---|---|---|---|
| **Reproducibility** | `[reasoned]` **+** one process, one clock, one transaction boundary | `[reasoned]` **+** same, plus provider version isolated at one seam | `[reasoned]` **+** deterministic one-way flow is its definition | `[reasoned]` **−** verdict spans services; pinning needs distributed correlation | `[reasoned]` **−−** worst case for reconstructing a single verdict |
| **Security & privacy** | `[reasoned]` **+** one trust boundary to audit; screening library at three call sites | `[reasoned]` **+** same | `[reasoned]` **+** same | `[reasoned]` **−** more boundaries, more surface, network security fallacy paid | `[reasoned]` **−−** most surface |
| **Verifiability** | `[reasoned]` **+** gates run in-process; conjunction is a single decision | `[reasoned]` **+** same | `[reasoned]` **−** the two bounded repair loops and the human escalation are *back-and-forth*, which pipeline explicitly excludes | `[reasoned]` **+** gates as services is workable | `[reasoned]` **+** workable, at high cost |
| Evolvability / replaceability | `[book]` modularity HI, but **nothing structural protects the two seams** | `[book]` **evolvability 3★ — the highest of the monolithic family**; plug-in registry is the seam | `[book]` modularity HI; **wrong axis** — technical partitioning, not customization | `[book]` agility 4★ | `[book]` evolvability HI |
| Reliability & recoverability | `[book]` FT unsupported — but FT is *not* a driving characteristic here; recoverability is, and checkpoint/resume delivers it | `[book]` reliability 3★ | `[book]` FT unsupported | `[book]` FT/availability 4★ | `[book]` FT HI |
| Auditability & traceability | `[reasoned]` **+** in-transaction lineage writes are trivial | `[reasoned]` **+** same | `[reasoned]` **+** same | `[reasoned]` **−** in-transaction audit across services is the hard case | `[reasoned]` **−−** |
| Interoperability | `[reasoned]` **○** adapters possible but not structurally enforced | `[reasoned]` **+** adapters *are* plug-ins; the contract is the registry | `[reasoned]` **○** | `[reasoned]` **+** | `[reasoned]` **+** |
| *Context: cost + simplicity* | `[book]` HI | `[book]` HI | `[book]` HI | `[book]` the pragmatic differentiator | `[book]` lowest |
| *Context: team maturity required* | Low | Low | Low | Moderate `needs-input` | **High `needs-input`** — `:68` names this as the failure mode |
| *Context: week-3 first-value gate* | **+** | **+** | **+** | **−** | **−−** |

**Weighting note, to avoid the Out of Context antipattern (`laws.md:206-212`).** Scalability, elasticity
and fault tolerance are where the distributed styles win, and all three were **eliminated at stage 1** —
the workload is a bounded internal batch over an existing manual suite, not open-ended growth. Scoring
generically would hand this to service-based on its 4★ row. Weighted for *this* system, those rows carry
near-zero weight and the reproducibility, auditability and security rows carry the most.

### The pick, as decided at the gate: plain modular monolith, modules re-partitioned by cluster, pipeline as the internal flow

**Gate variance, recorded.** This stage recommended a **microkernel hybridization** at two seams. The gate
**declined the hybridization** and chose a plain modular monolith. The recommendation and the reason it
lost are preserved below in "The microkernel hybridization that was declined," and the consequences are
carried into ADR-1 and the fitness-function list. One of the three corrections to the blueprint's premise
therefore falls away; the other two stand.

1. ~~**Add the microkernel hybridization, explicitly.**~~ **Declined at the gate** — see below.
2. **Re-partition the modules by domain, not by pipeline stage.** The blueprint's five modules —
   ingestion, hierarchy-tool, conversion, replay, certification — are partitioned along *technical*
   pipeline stages. The modular monolith style is explicitly **not** for "technically-oriented change
   streams" (`Modular-monolith-arch.md:229-239`), and a technical partitioning is what pulls a monolith
   toward layered architecture and the Architecture Sinkhole. Use the three cluster boundaries from stage
   1 instead — conversion, validation-certification, evidence — which are characteristic-shaped and
   therefore split cleanly later. The blueprint's five names survive as *packages inside* those modules.
3. **Keep pipeline as the internal flow topology, not the macro style.** The one-way flow is real and
   should be visible in the code, but pipeline as a macro style fails on the two bounded repair loops and
   the human escalation — "not for back-and-forth communication" (`Pipeline-arch-style.md:216-224`).

**Why this is the least worst, not the best** (`ArchitecturalChar.md:250`). It wins the three top-3
characteristic rows outright, costs almost nothing in the rows that were eliminated at stage 1, matches
the pipeline isomorphic shape in the domain, and reaches the week-3 gate with the least machinery. It
loses on fault tolerance and scalability — accepted deliberately, since both were eliminated at stage 1 —
and it declines the one structural protection available for evolvability, which is the live cost.

### The microkernel hybridization that was declined

The recommendation was to register source adapters (Excel, Octane, ALM/QC) and reasoning providers
(Copilot, Orchestrator AI, future) as plug-ins behind Ingest Test Sources and Invoke Models. Microkernel is
the only monolithic style the book rates for evolvability at all (3★,
`microkernel-arch-style.md:206-217`), and the customization isomorphism is a real match.

**The case for declining it is genuinely strong, which is why this is a variance and not a defect:**

- Three source adapters and two providers do not need a registry. Spring's dependency injection already
  supplies the Strategy seam for free — an interface plus implementations, selected by configuration. A
  plug-in registry with runtime binding is machinery bought for extensibility this system may never use.
- The roadmap is Excel-first and needs exactly **one** adapter at week 3. Building a registry to hold one
  plug-in is the "spec the simplest thing" case, and the elimination probe in worksheet §7 already named
  interoperability as the driver it would drop first.
- Microkernel carries its own named antipatterns — Volatile Core and Plug-In Dependencies
  (`microkernel-arch-style.md:158-170`) — and a volatile core is a live risk here, since the conversion
  flow is exactly what Phase 2 rewrites.

**What it costs, stated plainly.** The two seams lose their **runtime structure.** Nothing in the
deployed system prevents a caller from bypassing Invoke Models to reach a provider directly, or from
letting source-specific shape leak past an adapter into the IR. What remains available is **build-time
governance**: F1 and F2 can be implemented as compile-time dependency rules (ArchUnit or equivalent)
that fail the CI build on violation — materially stronger than social convention, but weaker than a
registry, and **entirely contingent on the team building and maintaining those rules** *(precision
added after the post-gate review, §9; the contingency is deliberately not softened)*. That matters more
here than it usually would, because Evolvability was displaced from the top 3 at the stage-1 gate *on
the condition that structure would protect it instead* (worksheet §7). With the microkernel declined,
**the whole of that protection is now ADR-1 plus two fitness functions** — so both become load-bearing
rather than confirmatory, and neither is optional. This is recorded as the gate's accepted consequence,
and it is the first thing to revisit if a fourth source adapter or a second concurrent provider appears.

### The losing alternatives and why they lost

| Style | Why it lost |
|---|---|
| **Microkernel hybridization** | **Won the analysis, lost at the gate.** The gate judged a plug-in registry to be machinery unwarranted by one week-3 adapter, and preferred Spring DI plus fitness functions for the same seams. Full reasoning and the accepted cost are above |
| **Pipeline as macro style** | Strongest isomorphic match to the happy path, but the design has two bounded loops and a human escalation. "Not for back-and-forth communication, nondeterministic flows → EDA" (`:216-224`). Survives as the internal flow pattern |
| **Layered** | Not scored on ratings — the notes for it are truncated to topology only, so no ratings exist to present. Rejected on reasoning: a technical partitioning that would put the pipeline stages in horizontal layers, inviting the Architecture Sinkhole antipattern |
| **Service-based** | The strongest distributed candidate and the right first step *if* a split is ever needed — best distributed style for ACID needs, ~12-service ceiling fits sixteen components. Loses today because Determination 1 found no quantum boundary, its winning rows (FT 4★, scalability 3★) were eliminated at stage 1, and it carries a `needs-input` on team maturity. **Named as the migration target** so the split has a destination |
| **Event-driven** | Evolvability 5★ is genuinely attractive and it is the choreography option from ADR-3. Loses on simplicity and testability LO, on reproducibility and traceability (the top-3 and driving rows it damages most), and on fit — "not when processing is mostly request-based" (`:647-688`). This is batch request-shaped work |
| **Microservices** | **Fashion check (`:13-38`): this is the fashionable answer and it is wrong here.** The domain is semantically coupled through the IR spine, certification and publication must be atomic, the workload is a bounded batch, and team maturity is unknown. `microservices-arch.md:313-323` says don't — fix granularity instead |
| **Space-based** | The domain is not discrete-processor-shaped and there is no spiky concurrent load. Rejected on isomorphism |
| **Orchestration-driven SOA** | Historical; "in practice it has mostly been a disaster" as an application architecture |

### Fallacies of distributed computing — what this design pays for anyway

A monolith does not escape the fallacies; it pays them at its integration boundaries. Five of the eleven
are live here (`Arch-style-foundations.md:207-319`):

| Fallacy | Where it bites | How the design pays |
|---|---|---|
| The network is reliable | Perfecto lab and the Orchestrator AI gateway | Bounded retries (3 static, 3 device), `ENV_INFRA` as a distinct failure class that re-queues and never heals, retry/backoff at one choke point |
| Latency is zero | 30s generation budget; gateway latency named as a risk | Async device seam; **know p95–p99, not averages** — the stage-1 caveat class already requires reporting max variance alongside the mean |
| The network is secure | Untrusted manual-test text; PII in artifacts; vault-keyed test data | Screening library at three trust boundaries; vault-key indirection enforced at the IR schema |
| **Versioning is easy** | Model deprecation is named as outside the team's control | ADR-2 (cache key must include model and provider version) exists precisely because this fallacy was being paid silently |
| **Observability is optional** | — | OpenTelemetry with LLM spans to a self-hostable trace store is already specified, and auditability makes it non-negotiable |

---

## 6. Edge and access topology

The component stage deliberately excluded UIs, so unless this is surfaced here, **no later stage will**
(the GGG test-drive's one genuine miss, 2026-07-25). Four actor classes, and they do not share an access
path.

| Actor class | Phase | Access path | Why it is architecturally significant |
|---|---|---|---|
| **QA engineer** | Phase 1 (primary), Phase 2 (escape hatch) | IDE with Copilot + two CLIs (ingestion, hierarchy-tool). **No web UI needed** | The cheapest finding in this section: Phase 1's main user interface is the IDE and the terminal, so Phase 1 needs no UI build at all. That is why the week-3 gate is reachable |
| **Reviewer** | Both | **Web UI — the HITL review queue.** Needs authenticated identity, authorization, and attribution of every approval, override and correction | Stage-1 auditability requires "every human approval, override, and correction attributable to an identity." That is an authenticated application, not a page. It is the one UI that must exist in Phase 1 |
| **Auditor** | Both | **Read-only export path, not a dashboard** | The stage-1 measure is reconstruction "from stored evidence alone, **without access to the running system**." A UI over the live database does not satisfy that. This implies an export or archival capability, which no component currently owns — **the gap this section exists to catch** |
| **Delivery lead** | Both | Metrics dashboard over the Preserve Provenance read model | Read-only projection; no write path |
| **Phase 2 orchestrator** | Phase 2 | Headless, internal — no edge at all | Reinforces Determination 1: Phase 2 adds no new edge, which is consistent with "nothing else moves" |

**API / edge layer.** One authenticated internal API serving the review queue and the dashboard; the CLIs
speak to the runtime directly; the auditor path is an export rather than an endpoint. A BFF layer is *not*
warranted — there is one web client, not several device classes. Recorded as ADR-8.

---

## 7. Follow-on ADR list handed to Stage 4

Four were already owed from stages 1–2; this stage answers two of them and adds four more. Style choice
always produces an ADR; data topology and the sync/async calls qualify because each option carries
significant trade-offs (`laws.md:226`).

| ID | Decision | Scope | Status entering Stage 4 |
|---|---|---|---|
| **ADR-1** | Model boundary — Invoke Models as sole model-call seam, Phase 1 → Phase 2 swap surface, IR spine stability | application | **Mandatory, and load-bearing after the gate declined the microkernel.** It is now the *entire* compensating control for Evolvability's displacement (worksheet §7), since no structural seam backs it up. Must specify the seam as a Spring interface with configuration-selected implementations, and must name the fitness functions as its Compliance section |
| **ADR-2** | Cache key must include model and provider version | application | Owed from stage 2 §9; reinforced by the versioning fallacy (§5) |
| **ADR-3** | Central orchestration vs event-driven choreography | application | **Answered here** — central orchestration, with the CE = 11 mitigation. ADR records the reasoning and the losing option |
| **ADR-4** | How certification obtains a fidelity grade without cluster B inheriting cluster A's characteristics | application | **Answered here** — accept synchronously at one quantum, with **one** named expiry condition *(corrected 2026-07-26 in the stage-4 review: the post-gate adjudication of §4 reclassified the second "expiry condition" as a live cost paid from day one, and this row was not swept at the time)* |
| **ADR-5** | Architecture style: **plain modular monolith**; modules partitioned by cluster, not by pipeline stage; pipeline as internal flow | application | New. Must record two things beyond the choice: the correction to the blueprint's five-module technical partitioning, and the **microkernel hybridization as the rejected alternative** with its forfeited evolvability protection in the Consequences section |
| **ADR-6** | Data topology: single primary store with lifecycle-partitioned schemas, blob storage for classified artifacts, Git as the asset store, and the retention/immutability design | common | New. Carries the `needs-input` on residency — **cannot be closed without the cloud/on-prem answer** |
| **ADR-7** | Async seams: queue in front of device replay, queue for human decisions, and synchronous in-transaction provenance writes | application | New. The in-transaction rule is the non-obvious half, and its precise form at the async seams — transactional outbox on the producer side, idempotent consumers, local transactions only, no distributed transaction across the queue — is part of the ADR's scope (§4) |
| **ADR-8** | Edge and access topology: review-queue UI as the only Phase 1 UI, auditor export path, CLI-only for engineers, no BFF | integration | New. **Includes the unowned-capability finding** — no component currently owns the auditor export |
| **ADR-9** *(added 2026-07-26 by the stage-4 review)* | Screening demoted from a component to a shared library invoked at three trust boundaries | application | **This list's own defect.** F3 was handed over without an ADR to own it, so the decision it enforces went unrecorded. Filed as ADR 0009. See the note below |

**Defect in this handoff, found in the stage-4 review and left visible.** The table above shipped with
eight rows while the fitness-function table below named **F3 as load-bearing** — an assertion holding a
boundary that the stage-2 gate removed. A fitness function is the *enforcement* of a decision, never a
substitute for recording it, so F3 arrived at stage 4 with no ADR to live in and would have reached
arch-validate as an orphan. The missing decision is now **ADR-9**. Two of the three merges directed at the
stage-2 gate produced ADR-owed decisions this way; the metrics read-model merge did not, because it changed
no boundary. The general lesson for future handoffs: **every fitness function in the table below must name
an owning ADR in the table above**, and the two tables should be reconciled before the handoff closes.

**Fitness functions this stage implies** (for arch-validate to formalize). Two gate decisions converted
runtime structure into build-time governance, so the first three are **load-bearing, not confirmatory** —
they are the only thing holding a boundary that no longer exists in the deployed structure.
**Mechanism note:** F1, F2, and F4 are statically assertable — compile-time dependency rules (ArchUnit
or equivalent) that fail the CI build; F5–F7 need runtime or data-level checks and are correspondingly
easier to skip, which is why they are named here rather than left to arch-validate to discover. **F3 is
both** *(refined 2026-07-26 by ADR 0009)*: a static rule can assert that the three egress packages depend
on the screening library, but a dependency edge proves availability, not invocation, so a runtime
assertion on the egress paths is required to complete it. Either half alone passes a component that
imports the library and never calls it.

| # | Assertion | What it replaces | Why load-bearing |
|---|---|---|---|
| **F1** | No type outside the model-boundary adapter references a provider SDK, gateway client, or Copilot-specific construct | The microkernel plug-in registry, declined at this gate | Without it, provider specifics leak and the Phase 2 swap surface erodes silently — the failure ADR-1 exists to prevent |
| **F2** | No source-system type crosses out of a source adapter; the IR is the only thing that leaves ingestion | The microkernel plug-in registry, declined at this gate | Without it the IR turns source-shaped, which the worksheet's elimination probe named as the exact cost of dropping interoperability |
| **F3** | No ingestion, evidence-capture, or model-call path reaches its egress without a screening call | The Screen Untrusted Content component, demoted to a library at the stage-2 gate | Security & privacy is top-3, and this is now its **only** guarantee at those three boundaries — the structural one is exactly what the demotion removed *(wording corrected 2026-07-26: "only structural guarantee" was self-contradictory)*. Owned by ADR 0009 |
| F4 | No foreign key from lineage schemas into conversion-state schemas | — | Asserts the lifecycle split (§3) so retention deletion stays safe |
| F5 | Phase 2 cutover changes zero files in the `validation-certification` and `evidence` modules | — | Asserts "nothing else moves" (§2) and the stage-1 evolvability measure |
| F6 | Every lineage write carries the complete pinning set, including model/provider version and judge calibration version | — | Asserts reproducibility's structural measure and closes the ADR-2 defect |
| F7 | Certification refuses to issue a verdict when the judge's calibration record is absent or older than the current model version | — | Asserts the Timing connascence created by the stage-2 judge merge (stage 2 §9) |

**Owning ADR for each** *(map added 2026-07-26 in the stage-4 review, after F3 was found orphaned)*:
F1 and F2 → ADR 0001; **F3 → ADR 0009**; F4 → ADR 0006; F5 → ADR 0005; F6 → ADR 0002 as primary owner,
asserted from their own angles by ADR 0004 and ADR 0006; F7 → ADR 0004.

**Pattern worth naming.** Three of seven fitness functions now exist to compensate for boundaries removed
at human gates. That is a legitimate trade — cheaper structure paid for with enforced convention — but it
means the fitness-function suite is not a nice-to-have in this design. If it is not built, three
characteristics lose their only protection. Stage 6 (arch-validate) should treat F1–F3 as release-blocking.

**These seven are the cross-cutting subset, not the whole governance surface** *(clarified 2026-07-26 in
the stage-4 review)*. F1–F7 are the assertions this stage could derive from style and topology alone. The
nine ADRs written in stage 4 add roughly fourteen more mechanisms in their own Compliance sections — the
CA = 0 rule (ADR 0003), module-boundary and single-deployable checks (ADR 0005), the redelivery chaos test
and lineage-completeness reconstruction (ADR 0007), attribution completeness and the reconstruction drill
(ADR 0008), the contract-parity check at Phase 2 cutover (ADR 0001), the retention drill (ADR 0006), the
red-team corpus regression and secret/PII egress detector (ADR 0009), plus several manual cadences.
**arch-validate must inventory every ADR's Compliance section, not just this table**, or it will arrive
with about a third of the governance surface.

---

## 8. Gate status — CLOSED 2026-07-26, with one variance

Each determination was confirmed separately (conflated-axes rule); no bundled yes was accepted.

- [x] **Determination 1 — quantum count:** confirmed. One quantum for both phases; clusters as module seams; Replay on Devices and cluster C deferred with named revisit triggers (§2)
- [x] **Determination 2 — data placement:** confirmed as a recommendation. Four-concern split; Git as asset store; lifecycle-partitioned schemas with no cross-lifecycle foreign keys; blob storage with references in the primary store (§3) — *residency still `needs-input`, which blocks ADR-6 only*
- [x] **Determination 3 — communication:** confirmed on all four points. Async for device replay and human decisions; synchronous in-transaction provenance writes (local transactions + outbox at the async seams); ADR-4 accepted synchronously with its live availability coupling named and one expiry condition; ADR-3 central orchestration (§4)
- [x] **Determination 4 — style: confirmed with variance.** Plain modular monolith; **the recommended microkernel hybridization was declined**; modules re-partitioned by cluster rather than pipeline stage; pipeline retained as internal flow; service-based named as the migration target (§5)
- [x] **Edge topology** accepted, including the finding that no component owns the auditor export path (§6)
- [x] **ADR list** accepted for Stage 4 (§7)

**The one variance, and how it was handled.** The gate declined this stage's style recommendation. Per the
human-gate rule, the contradiction was named with its cost and then deferred to the decision-maker: the
recommendation, the reasons for declining it (which are strong), and the forfeited evolvability protection
are all recorded in §5, and the consequence is carried into ADR-1 and fitness functions F1–F2 rather than
absorbed silently. **No antipattern was created** — a plain modular monolith is internally consistent with
all three other determinations. What changed is that evolvability's protection moved from structure to
enforced convention.

**Reading recorded for confirmation.** The gate selected "plain modular monolith — skip the microkernel
hybridization" and did **not** select the separate option to retain the blueprint's five pipeline-stage
modules. This artifact therefore takes the re-partitioning correction (modules by cluster) as **accepted**.
If that reading is wrong, §5 correction 2 and the §2 quantum map both need revising.

**Three inputs still missing** and their effect: data residency (blocks ADR-6), team size and Agile/ops
maturity (would change the weighting of any distributed candidate), infrastructure budget (currently only
device minutes are treated as cost). **The residency answer has a named fallback path:** if it comes back
requiring the evidence store to live apart from the runtime, that is exactly the cluster-C revisit
trigger in §2 ("co-location illegal rather than merely untidy") — ADR-6 then becomes an extraction
decision, not a schema decision, and Determination 1 re-opens for cluster C only.

**If a determination is rejected**, the loop-back is to this stage, not to stage 1 — unless the rejection
changes the cluster reading, in which case stage 1 §10 re-opens.

**Advance →** arch-decide (mandatory), then arch-risk.

---

## 9. Adjudication of the post-gate critical review (2026-07-26)

A critical review after gate closure produced six findings. None reverses a determination; four corrected
overstatements or omissions, one was accepted in part, one rejected. **No gate decision changed**, so the
gate remains closed; the corrections are annotated in place with pointers back here.

| Finding | Verdict | Disposition |
|---|---|---|
| "The entanglement costs nothing at one quantum" overstates — gateway availability/rate-limit/token cost is paid from day one, not an "expiry condition" | **Accepted** | §4 heading and body rewritten: quantum-collapse cost is zero at one quantum; the availability coupling is live and its mitigation (grades as recorded evidence, no re-grading on retry) is in force immediately. One genuine expiry condition remains |
| "Same transaction" for provenance writes is underspecified at the async seams — readable as a distributed transaction across a queue | **Accepted** | §4 row clarified: local transactions on each side, transactional outbox on the producer, idempotent consumers, never a distributed transaction. Carried into ADR-7's scope |
| "Cluster A is not in the architecture in Phase 1" is factually wrong — ingestion and the hierarchy tool ship as cluster-A CLIs, and Route Human Decisions runs as a service | **Accepted** | §2 phase table corrected: Phase 1 conversion contributes no *service components for the reasoning path*; cluster A is thinner, not absent |
| Residency is flagged `needs-input` but never connected to a decision hook | **Accepted** | §8 now names the fallback: a residency answer forcing evidence isolation fires the §2 cluster-C revisit trigger, making ADR-6 an extraction decision and re-opening Determination 1 for cluster C only |
| "Conventions, not structure" overstates — F1/F2/F4 can be compile-time dependency rules that fail the build, which is structural governance, not social convention | **Accepted in part** | §5 and §7 corrected to name the mechanism (build-time dependency rules, ArchUnit or equivalent) and to distinguish statically-assertable fitness functions from runtime/data ones. The load-bearing warning — no protection exists unless the rules are built — survives verbatim in force |
| Implied: naming the enforcement mechanism reduces the cost of declining the microkernel | **Rejected** | Build-time rules exist only if the team builds and maintains them. The artifact's claim that the protection is contingent rather than automatic is the accurate one; precision was added, softening was not |
