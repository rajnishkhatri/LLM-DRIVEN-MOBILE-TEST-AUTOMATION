# Style selection data

Distilled from `cases/ArchitectureBook/` ch7, ch9–19.

> **Data gaps, be honest about them:** the book's star-rating scorecards are
> figures (images) that did not survive into the notes; only prose-stated
> ratings are reproduced below (`—` = not recoverable). `LayeredArchStyle.md`
> is truncated at 26 lines (topology only — no ratings, no when-to-use, and
> the Architecture Sinkhole antipattern it should define is only name-checked
> from ch13). Never present a `—` cell as a rating.

## Quantum machinery (ch7)

Architecture quantum = smallest independently runnable part
(`ArchCharScope.md:18`); features: independent deployability (the DB is part
of the quantum — single shared DB ⇒ quantum of one, `:36`), high functional
cohesion, low external implementation static coupling, synchronous
communication with other quanta (`:20-28`). Coupling test: "two things are
coupled if changing one might break the other" (`:52`). Scope rule: "higher
coupling is allowed for narrower scopes; the broader the scope, the looser
the coupling should be" (`:64-66`).

Decision tree (`:80-106`): one characteristics set? → monolith family →
persistence → done. Multiple sets? → distributed → quantum boundaries →
persistence (single DB or partitioned) → sync vs async between quanta
(sync can silently merge quanta — re-check boundaries after choosing).

## Comparison matrix

| Style | Topology | Partitioning | Quanta | Prose-recovered ratings | Cite |
|---|---|---|---|---|---|
| Layered (ch10) | 4 horizontal technical layers; 3 physical variants | technical | 1 | — (file truncated) | `LayeredArchStyle.md:12-26` |
| Modular monolith (ch11) | single deployable, domain modules | domain | 1 | cost/simplicity/modularity HI; deploy/test 2★; scale/elasticity 1★; fault tolerance unsupported | `Modular-monolith-arch.md:216-225` |
| Pipeline (ch12) | producer→transformer→tester→consumer filters, one-way pipes | technical | 1 | cost/simplicity/modularity HI; deploy/test "average"; scale/elasticity 1★; FT unsupported; distributing filters raises ops scores at cost of simplicity | `Pipeline-arch-style.md:204-212` |
| Microkernel (ch13) | core + plug-ins; registry; compile or runtime binding | both | 1 | simplicity/cost HI; test/deploy/reliability/modularity/evolvability/responsiveness 3★; scale/elasticity/FT LO | `microkernel-arch-style.md:206-217` |
| Service-based (ch14) | UI + ≤12 coarse domain services + usually one DB | domain | ≥1 | agility/test/deploy 4★, FT/availability 4★, scalability 3★, elasticity 2★; **no 5★ anywhere** — the pragmatic differentiator is cost+simplicity | `service-based-arch-style.md:141-147` |
| Event-driven (ch15) | processors + broker (or mediator); initiating→derived events | technical | 1–many | perf/scale/FT 4★ ("4 not 5 because of the database"); evolvability 5★; simplicity/testability LO | `event-driven-arch-style.md:633-637` |
| Space-based (ch16) | replicated in-memory PUs, data pumps, DB off the transaction path | technical | varies | elasticity/scale/perf 5★; testability 1★; cost HI | `space-based-arch-style.md:514-520` |
| Orchestration-driven SOA (ch17) | taxonomy layers + ESB/orchestration engine | technical (extreme) | 1 | deploy/test "disastrous"; simplicity/cost inverted | `orchestration-driven-service-or-arch.md:156-163` |
| Microservices (ch18) | fine-grained services, DB-per-service, API layer | domain (extreme) | most of any style | deploy/test/FT/scale/elasticity/evolvability HI; performance "often an issue" | `microservices-arch.md:296-305` |

## When to use / when not (compressed)

- **Modular monolith**: tight budget/time, unclear direction (start here,
  migrate later), DDD teams, domain-shaped change. Not for: high ops
  characteristics; technically-oriented change streams
  (`Modular-monolith-arch.md:229-239`).
- **Pipeline**: ordered deterministic one-way steps (ETL, EDI, Camel-style
  mediation). Not for: back-and-forth communication, nondeterministic flows
  → EDA (`Pipeline-arch-style.md:216-224`).
- **Microkernel**: product/customization domains (per-state rules, Jira/
  Eclipse-style extensibility), strong domain-to-architecture isomorphism.
  Watch: Volatile Core, Plug-In Dependencies; remote plug-ins make it
  distributed (`microkernel-arch-style.md:9,158-170,219-231`).
- **Service-based**: modularity without microservices' granularity tax; best
  distributed style for ACID needs; DDD fit; stepping-stone to
  microservices. Limits: ~12 services; heavy interservice chatter = wrong
  boundaries or wrong style (`service-based-arch-style.md:95-97,147-155`).
- **EDA**: react-to-things-that-happened domains; unknown/variable
  concurrency; 5★ evolvability. Not when processing is mostly
  request-based, when eventual consistency is unacceptable, or when
  processors keep needing sync calls (`event-driven-arch-style.md:647-688`).
- **Space-based**: variable, unpredictable, spiky load (>10k concurrent;
  ticketing/auctions). Not when most data must round-trip the DB; near-cache
  model not recommended (`space-based-arch-style.md:17,224,528`).
- **SOA (orchestration-driven)**: historical; residual fit = integration
  architecture over legacy. "In practice it has mostly been a disaster" as
  an application architecture (`orchestration-driven-service-or-arch.md:108-171`).
- **Microservices**: high functional+data modularity, extreme fault
  isolation, cloud-native. Not when transactions dominate across services
  ("don't! Fix the service granularity instead") or domain is large and
  semantically coupled (`microservices-arch.md:183-187,313-323`).

## Fallacies of distributed computing (ch9, all 11)

network is reliable / latency is zero (know p95–p99, not averages) /
bandwidth is infinite (stamp coupling) / network is secure / topology never
changes / only one administrator / transport cost is zero / network is
homogeneous / **versioning is easy** / **compensating updates always work** /
**observability is optional** (`Arch-style-foundations.md:207-319`). For any
distributed pick, state which fallacies the design pays for and how.

## Cross-style antipattern shortlist

Big Ball of Mud (`Arch-style-foundations.md:39`); Big Ball of Distributed
Mud, Grains of Sand, Entity-Trap services, Front Controller
(`microservices-arch.md:52,169,254-260`); Dynamic Quantum Entanglement
(`event-driven-arch-style.md:138`); shared entity-object library in
service-based (`service-based-arch-style.md:73-76`); Accidental SOA
(`orchestration-driven-service-or-arch.md:114`); modular monolith too-big
signs — long changes, surprise breakage, team collisions, slow startup
(`Modular-monolith-arch.md:92-104`).

## Worked selections — moved to a sealed file

The book's worked kata answers no longer live in this file: this reference
is loaded at step 0, and any whole-file read exposed them before the four
determinations were written — a fence inside a step-0 file is breached by
construction (SD1: Silicon Sandwiches test-drive 2026-07-24, recurred GGG
test-drive 2026-07-25). They now live in `worked-answers.SEALED.md`, which
step 6 of the SKILL opens only AFTER the determinations are written.
