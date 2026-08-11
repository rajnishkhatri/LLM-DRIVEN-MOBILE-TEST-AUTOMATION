---
type: architecture
title: ADR 0007 — Queue device replay and human decisions; write provenance synchronously via a transactional outbox
description: 'The communication decision from stage-3 Determination 3: exactly two asynchronous seams (the rate-limited device lab and human review), everything else synchronous in-process, and lineage writes synchronous in the same local transaction as the state change they describe — realized at the async seams as a transactional outbox on the producer with idempotent consumers, never a distributed transaction across the queue.'
tags: [architecture, mobile-test-automation, adr, arch-decide]
---

# ADR 0007. Queue device replay and human decisions; write provenance synchronously via a transactional outbox

## Status

Accepted

## Context

**Forces.** Two downstream dependencies break the synchronous default. The
Perfecto device lab is rate-limited and capacity-bounded — synchronous calls
against simultaneous demand produce timeouts and duplicated device spend, and
device minutes are the system's dominant cost. Human reviewers respond in
hours or days — an async edge in the middle of the state machine by nature.
Meanwhile lineage has the opposite requirement: the stage-1 measure is 100%
completeness, and an async audit write that fails after its state change
commits is a lineage gap — an auditability failure, not a performance detail.
The naive reading of "same transaction" at a queue boundary would mean a
distributed transaction spanning database and broker, which is its own trap.

**Alternatives considered.**

- **Two queues + transactional outbox + idempotent consumers** (chosen).
- **All-synchronous** — no broker to run; collapses against the rate-limited
  lab and blocks the state machine on human latency measured in days.
- **Distributed (XA) transactions across the queue** — makes "same
  transaction" literal; fragile, throughput-hostile, and couples the database
  to the broker's transaction manager.
- **Async lineage writes too** — maximal decoupling; institutionalizes the
  lineage-gap failure mode the auditability measure forbids.

**Qualification.** Nygard test: passes — dependencies, interfaces, and two
driving characteristics (reliability/recoverability, auditability). Third-law
test: passes. Timing: the checkpoint/resume mechanism is the first thing the
state machine needs; last responsible moment reached.

### Trade-off matrix

| Contextual factor (weight) | Queues + outbox (chosen) | All-sync | XA across queue | Async lineage |
|---|---|---|---|---|
| Lineage completeness under failure (5) | **++** enqueue recorded atomically with state | ++ trivial | ++ literal | −− gaps by design |
| Zero duplicated device runs (5) | **++** queue + idempotency keys | −− retries duplicate spend | + | + |
| Resume across human latency (4) | **++** persist-and-resume is native | −− threads parked for days | − | + |
| Operational simplicity (3) | − a broker and an outbox relay to run | ++ nothing | −− XA coordinator | − |
| Throughput at the seams (2) | + | − | −− XA overhead | ++ |

## Decision

**We will place queues at exactly two seams — Coordinate Conversion → Replay
on Devices, and Coordinate Conversion → Route Human Decisions — and keep every
other component-to-component call synchronous and in-process. Every write to
Preserve Provenance is synchronous, in the same *local* transaction as the
state change it describes. At the two async seams this means: the producer
records the enqueue via a transactional outbox in the same local transaction
as its state change; consumers are idempotent and write their own lineage in
their own local transaction; no distributed transaction ever spans the
queue.**

**Technical justification:**

- The device seam is the textbook async case: rate-limited downstream plus
  simultaneous demand. A queue is also what makes "interrupted batch resumes
  with zero duplicated device runs" achievable — the queue holds intent, the
  checkpoint holds progress, idempotency keys make redelivery harmless.
- The human seam needs the same persist-and-resume machinery, so the second
  queue is nearly free once the first exists.
- The outbox pattern delivers the atomicity the lineage measure needs with
  only local transactions — each side of the queue is individually ACID, and
  the seam tolerates redelivery instead of pretending it cannot happen.

**Business justification:**

- **Cost:** device minutes are the dominant cost; zero duplicated device runs
  is a direct spend control, and it falls out of this design rather than
  being policed manually.
- **User satisfaction:** reviewers work at their own pace without holding the
  batch hostage; QA engineers get resumable batches instead of restarted ones.
- **Strategic positioning:** "no missing link in the chain" survives failure
  scenarios, which is what the audit posture rests on.

## Consequences

- A message broker and an outbox relay become operational dependencies —
  accepted; they are the only broker infrastructure in the design (ADR 0003
  deliberately avoided an event backbone).
- Redelivery is possible by design, so idempotency keys on both consumers are
  mandatory, not defensive — a duplicate device-run request that slips through
  is real money.
- **No third queue without a superseding ADR** — the two seams were derived
  from characteristics, not convenience; a new one must be too.
- Forfeited: XA's literal one-transaction story (traded for two provably
  atomic local ones); all-sync's zero infrastructure (collapses at the lab).

## Compliance

- **Lineage completeness check (automated, data-level):** periodic
  reconstruction over recent batches asserting no missing link between state
  changes, outbox records, and consumer-side lineage.
- **Redelivery chaos test (automated, staging, per release):** inject
  duplicate deliveries at both seams; assert zero duplicate device runs and
  zero duplicate lineage rows.
- **Manual (architecture review):** any proposed new queue or any lineage
  write moved out of transaction routes back to this ADR.

### ASH-Capture graph-mutation ruling (2026-08-01, ADR 0014 acceptance / Replan R1 D5)

ADR 0014 (Accepted 2026-07-31) defers its graph-mutation invocation model to this ADR by named interface (0014:66-67, :108, :462, :740, :758). This amendment rules the two questions D5 routed here. It **executes this ADR's own deferral pointer and strengthens the two-seam invariant; it does not add, move, or reverse a seam.**

**Ruling 1 — ScreenGraph mutations are synchronous same-local-transaction writes, not a third seam.** Edge commits at discovery completion (README:239), drift-repair re-versioning (README:305-341), and quarantine supersessions (0014:429-441, README:333) are `Preserve Provenance`-class writes and fall under this ADR's synchronous default (0007:57-63): each mints its graph version, rows, and chain row "in one local transaction" (0014:448) with device work held strictly outside it (0014:449-450). This ADR therefore **ratifies ADR 0014 D-D's rejection of walkthrough §13.6** (o1-pipeline-walkthrough.md:979-980, "route graph mutations through the existing outbox") as a positive 0007 ruling: graph mutations do **not** route through the outbox, do **not** open a third seam, and no distributed transaction spans a queue (0007:61-63). The outbox continues to serve exactly the two derived seams (0007:55-56, :95); the graph write path is in-process and locally ACID, which is what lets it inherit this ADR's lineage-completeness guarantee (0007:73-75) rather than the async-lineage failure mode this ADR forbids (0007:35-36). This closes the audit gap in which the §13.6 rejection lived in only one of the two ADRs it constrains — a reader of ADR 0014 alone could not verify the outbox rejection was authorized by 0007's own owner until now.

**Ruling 2 — park-and-sweep is a PERMITTED bounded intra-process-family retry buffer, not a prohibited third queue — narrowly and non-precedentially.** The `COMMIT_CONTENDED` park + sweeper re-drive (0014:457-466) buffers rows in `capture_run_edges`, a run-scoped staging table the Capture Executor's own process family owns and which nothing else can load (0014:381-382, :463-464). It is **not a seam between components** — the object this ADR's "no third queue" rule (0007:95) governs (0007:55-56, seams between named pipeline components). The eventual commit still writes snapshot + chain row in one local transaction (0007:57-63; 0014:464). The carve-out rests on **two required, structural bounds**: (a) **single-owner** — only the executor process family enqueues and drains it; the moment any second component reads or drives it, it becomes a seam and routes back here (0007:108); (b) **non-precedential** — this permission licenses no future queue-shaped mechanism to escape the two-seam rule by asserting single ownership; each such mechanism routes back to this ADR independently (0007:108). *(A prior "non-lossy-by-recompute" rationale is deliberately **not** relied on as a load-bearing bound — see Ruling 3, which shows it is false for quarantine/BROKEN commits; recompute-safety is a note scoped to re-verification results only, not a justification for the carve-out.)*

**Ruling 3 — the fail-loud-and-recapture fallback is conformant ONLY for re-verification results, never for quarantine/BROKEN/promotion commits.** Per ADR 0014's own record (0014:465-466), had this ruling disallowed the buffer, the fallback was fail-loud-and-recapture. This ADR permits the buffer but does **not mandate** it: the primary deliverable (the hierarchy dump) ships regardless of commit contention (0014:460), and **re-verification results are deterministically re-derivable by replay** (0014:412), so a contended re-verification commit loses only device-minutes on recapture. **But quarantine supersessions (0014:429-441, README:333) and BROKEN markings ride the same CAS writer (0014:442-449) and are human/screening-originated (0014:431) — they are NOT replay-derivable.** Therefore a run whose contended batch contains a `QUARANTINED` or `BROKEN` transition **must park (or fail loud AND raise an incident), never silently recapture** — recapture would silently drop a lineage-material event. Fail-loud-and-recapture is a conformant fallback *only* for runs whose contended commits are re-verification results.

**Which one ships is evidence-gated on the S2 spike, not a reversal of either ruling.** Because commits are totally ordered per `app_version` by construction (0014:467-469) and the graph is a few thousand edges (o1-pipeline-walkthrough.md:864-865), CAS contention is *expected* to be negligible — in which case the buffer earns no keep and fail-loud (bounded to re-verification per Ruling 3) wins on A1/G1 least-machinery. That is a measurable claim: **measured graph-commit CAS-contention rate is added to S2's pre-registered keep/kill threshold set** (alongside escape-hatch rate, hash stability, device-minutes, human touches — 0014:702), so the buffer-vs-fail-loud choice is retired or falsified by data with thresholds recorded *before* measuring, rather than defaulting to the more complex option by inertia. Below threshold, the buffer is dropped by recorded operating decision — no further ADR needed, since both are conformant implementations of this ruling.

Status unchanged (**Accepted**) — this amendment closes a deferral this ADR named and strengthens the two-seam invariant; it does not add, move, or reverse a seam, and moves no lineage write out of its local transaction. Recorded here rather than reinterpreted in passing.

**Consequences riders (appended to `## Consequences`, 0007:87-98):**
- **The graph write path inherits the two-seam invariant, and the §13.6 rejection is now grounded on both sides.** The outbox-routing rejection (0014:359-360) is authorized by this ADR's own owner, mirroring the two-sided ADR 0009 flip (recorded in both 0009 and 0014 D-H) so neither ADR asserts an unconfirmed claim about the other.
- **Imposes on future work:** the `capture_run_edges` park-and-sweep carve-out is non-precedential — any second component that reads or drives it, and any new queue-shaped mechanism claiming a "same process family" carve-out, routes back to this ADR (0007:108, extended).

**Compliance riders (appended to `## Compliance`, 0007:100-109).** All are **F-candidates** (mirroring ADR 0014's F8-F12 CANDIDATE series, 0014:765-767) until ratified, extending this ADR's existing lineage-completeness and redelivery checks to the ScreenGraph write path.

- **F-D5a — graph-writes-are-synchronous (automated, CI-blocking, ArchUnit + Testcontainers):** an ArchUnit half proving no broker/queue-producer/outbox-relay type is reachable from the ScreenGraph write path (extends the F8 executor rule barring broker/queue types from either channel package, 0014:774-775); a Testcontainers proof that a graph-version commit writes version + rows + chain row in exactly one local transaction with no outbox row emitted. Enforces Ruling 1.
- **F-D5b — no-third-seam / park-and-sweep single-owner (automated, CI-blocking):** an assertion that `capture_run_edges` is enqueued and drained by the executor process family only — no second component holds a read or drive path to it (Ruling 2 bound a); a test that a parked `COMMIT_CONTENDED` batch, once swept, still commits snapshot + chain in one local transaction and emits no cross-component message. Reuses ADR 0014's F10 fork-unrepresentable construction (0014:789-798) as the commit-atomicity harness.
- **F-D5c — fallback-conformance, quarantine-aware (automated, per release):** with the sweeper disabled, (i) a triple-CAS-failure batch of **re-verification results** degrades to fail-loud-and-recapture with the hierarchy dump still delivered (0014:460) and zero silently-dropped re-verification (0014:459); AND (ii) a triple-CAS-failure batch containing a `QUARANTINED` or `BROKEN` transition **must NOT degrade to silent recapture** — it must fail loud with an incident (0009:210-214 shape), proving the fallback's safe set is bounded to recomputable commits (Ruling 3).
- **Manual (architecture review), extending 0007:108:** any second component that reads or drives `capture_run_edges`, and any new queue-shaped mechanism claiming the "same process family" carve-out, routes back to this ADR — the carve-out is explicitly non-precedential.
- **S2 evidence gate (per Replan R1):** the S2 spike records measured graph-commit CAS-contention rate against a pre-registered keep/kill threshold for the buffer; below threshold, the buffer is dropped in favor of fail-loud-and-recapture (bounded per Ruling 3) by recorded operating decision.

## Notes

Author: arch-decide stage 4 (agent draft)
Date: 2026-07-26
Approved by / date: Rajnish Khatri / 2026-07-26
Superseded date: —
Last modified / by / what: —
Last modified / by / what: 2026-08-01 / ADR 0014 acceptance (Replan R1 D5, owner) / ASH-Capture graph-mutation ruling added — rules ScreenGraph mutations synchronous same-local-transaction writes (ratifying ADR 0014 D-D's rejection of walkthrough §13.6 as a positive 0007 ruling, grounding it on both sides) and permits the park-and-sweep buffer as a non-precedential intra-process-family retry over capture_run_edges on two structural bounds (single-owner, non-precedential); fail-loud-and-recapture is a conformant fallback ONLY for deterministically re-derivable re-verification results — quarantine/BROKEN commits must park or fail-loud-with-incident, never silently recapture; the keep/kill choice is S2-evidence-gated on measured CAS-contention rate. Status unchanged (Accepted) — the amendment strengthens the two-seam invariant and adds, moves, or reverses no seam.
