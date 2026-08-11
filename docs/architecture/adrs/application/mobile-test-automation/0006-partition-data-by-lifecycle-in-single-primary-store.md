---
type: architecture
title: ADR 0006 — Partition data by lifecycle in a single primary store
description: 'The data-topology decision from stage-3 Determination 2, accepted once the residency input arrived as on-premises: a single primary relational store with conversion-state and lineage in separate schemas and no cross-lifecycle foreign keys, blob storage for classified device artifacts with references in the primary store, Git as the already-decided conversion-asset store, and the external object repository unchanged. On-premises permits co-location, so the cluster-C extraction fallback does not fire and stage-3 Determination 1 stands — but it obliges self-operated object storage and exposes two adjacent residency questions this ADR does not own: the Perfecto device cloud and model-provider egress.'
tags: [architecture, mobile-test-automation, adr, arch-decide]
---

# ADR 0006. Partition data by lifecycle in a single primary store

## Status

Accepted — **the residency input arrived on 2026-07-26 as on-premises**, and
the security half of the blocker was discharged separately by ADR 0010. Both
conditions the Proposed status named are now closed.

## Context

**Forces.** No database is named anywhere in the sources — the largest gap the
stage-3 readiness audit found. Yet the requirements imply one: per-test
checkpoint/resume needs ACID; lineage is append-only, retention-governed, and
regulated; device artifacts (video, page source, network captures) are large,
binary, and PII-bearing; conversion assets (prompts, exemplars, golden set)
are **already decided as Git** in the sources. Four concerns, four different
profiles — and two of them (conversion state, lineage) have **opposite
lifecycles**: conversion state is disposable once a test is certified; lineage
outlives everything under a regulatory retention clock.

**The residency answer (2026-07-26): on-premises.** Lineage rows and device
artifacts stay inside the bank's own infrastructure. The consequence that
matters most for this ADR is a *negative* one: on-premises **permits**
co-location of the evidence store with the runtime, so the isolation scenario
below does not fire, the cluster-C revisit trigger stays unpulled, and stage-3
Determination 1 (one quantum) stands unchanged. The answer costs this ADR
nothing structurally and confirms the topology as drafted.

It does change one supporting claim and expose two questions this ADR does not
own — both recorded in Consequences rather than smoothed over: **object storage
becomes self-operated** rather than a commodity cloud service, and residency
for *test-derived data in transit* is not settled by an answer about where the
stores live.

**Alternatives considered.**

- **Single primary relational store, lifecycle-partitioned schemas** (chosen).
- **One store, one schema** — simplest day one; entangles opposite lifecycles,
  making retention deletion either impossible or unsafe. Retention is a
  stage-1 security measure, not housekeeping.
- **Store per cluster** — matches the module map, but Preserve Provenance has
  CA = 13: a separate lineage store turns in-transaction lineage writes
  (ADR 0007) into a distributed-consistency problem thirteen callers pay.
- **Artifacts in the database** — one store to govern; binary blobs bloat the
  transactional store and make retention deletion a table-surgery exercise.

**Qualification.** Nygard test: passes — structure, dependencies, and two
top-3 characteristics (reproducibility's pinning chain, security's retention).
Third-law test: passes. Timing: schema shape is week-one work, but the
residency input is genuinely missing — hence Proposed with a named blocker
rather than deferred-stub or premature acceptance.

### Trade-off matrix

| Contextual factor (weight) | Lifecycle-partitioned single store | One schema | Store per cluster |
|---|---|---|---|
| Retention deletion provably safe (5) | **++** no FK from lineage into disposable state | −− entangled | ++ physically separate |
| Lineage completeness — in-transaction writes (5) | **++** local transactions, one store | ++ same | −− distributed consistency for 13 callers |
| Reconstruction "from stored evidence alone" (4) | **++** one join surface, full pinning set co-located | + | − cross-store joins |
| Day-one simplicity (3) | + two schemas, one instance | ++ | −− |
| Later cluster-C extraction cost (2) | + schema line = future store line | −− | ++ already split |

## Decision

**We will keep one primary relational store, partitioned into a
conversion-state schema and a lineage schema with independent retention and
grant models and no foreign keys from lineage into conversion state; device
artifacts go to object/blob storage with the primary store holding references
plus classification plus retention date, never payloads; conversion assets
stay in Git; the external object repository for certified locators is
unchanged, written under single-writer discipline.**

**Technical justification:**

- The schema line is the lifecycle line: conversion state can be purged after
  certification without touching a chain that must survive an audit years
  later — and the purge is provably safe because no lineage row references it.
- Every lineage write carries the full pinning set (`irVersion`, `codeCommit`,
  `pipelineVersion`, `appiumVersion`, device/OS/model, `appVersion`, prompt
  version, model/provider version, judge calibration version). One primary
  store means reconstruction never joins across systems — the strongest
  argument for co-location, straight from the auditability measure.
- Blob references with classification and retention dates in the relational
  store give the retention job one queryable surface over PII-bearing
  artifacts.

**Business justification:**

- **Cost:** one database instance and commodity blob storage; no second
  datastore to license, operate, or audit.
- **Strategic positioning:** retention and reconstruction are the audit
  posture in a bank — this topology makes both demonstrable rather than
  asserted.
- **Time to market:** two schemas in one instance is week-one work; every
  alternative that scores better on some axis costs weeks of infrastructure.

## Consequences

- The lifecycle split is enforced by schema discipline (F4), not by physical
  separation — cheaper, but only as strong as the fitness function holding it.
- **The residency fallback did not fire** *(resolved 2026-07-26)*. It was
  recorded as: if residency requires the evidence store to live apart from the
  runtime, that is the cluster-C revisit trigger ("co-location illegal rather
  than merely untidy"), turning this into an *extraction* decision and
  re-opening stage-3 Determination 1 for cluster C. **On-premises permits
  co-location, so the trigger stays unpulled and Determination 1 stands.** The
  fallback is retained as a live revisit condition, not deleted: a later
  regulatory ruling that isolates evidence would fire it, and the schema
  partitioning chosen here is exactly what keeps that extraction affordable.
- **On-premises makes object storage self-operated, which weakens one claim
  above.** The business justification cites "commodity blob storage"; on
  premises that means an operated object store (MinIO, Ceph, or a storage
  appliance) with its own capacity planning, durability configuration, backup
  regime, and on-call. The topology decision is unaffected — artifact payloads
  still do not belong in the transactional store — but the *cost* argument is
  weaker than drafted, and the retention job now runs against infrastructure
  the team is accountable for rather than a managed service's lifecycle rules.
- **Two adjacent residency questions are now visible and are not answered by
  this ADR** — recorded here because this is where they became findable, and
  routed to the risk register rather than resolved by assumption:
  - **The Perfecto device cloud.** Device artifacts (video, page source,
    screenshots, network captures — the PII-bearing set this ADR classifies)
    are *produced* in a third-party device cloud and pulled back on-premises.
    An on-premises answer about where artifacts are **stored** does not settle
    where they are **generated**. Either Perfecto runs in a private/on-prem
    configuration, or an explicit residency exception covers device execution,
    or those artifacts must be treated as having already left the premises
    before this ADR's storage rules apply.
  - **Model-provider egress.** Prompt payloads leave through the Orchestrator
    AI gateway. If that gateway proxies to an externally hosted provider, test
    content crosses the boundary regardless of where the stores sit. ADR 0009's
    egress screening is the control that exists; whether it is the control
    residency requires is a separate question.
  Both are **inputs for stage 5 (arch-risk)**, not defects in this ADR.
- Imposes on future work: no component may write lineage anywhere but the
  lineage schema; artifact payloads never transit the primary store.

## Compliance

- **F4 (automated, CI-blocking):** schema migration checks — no foreign key
  from lineage schemas into conversion-state schemas; violation fails the
  migration.
- **F6 (automated, data-level) — owned by ADR 0002, asserted here for the
  data-topology angle:** the nightly pinning-set sample is what proves the
  lineage schema is self-sufficient for reconstruction. Not re-specified here;
  a change to F6 belongs in ADR 0002.
- **Retention drill (manual, quarterly):** purge a certified batch's
  conversion state in a staging copy and prove lineage reconstruction still
  passes — the deletion-safety claim as an exercise, not an assumption.
- **Security-review queue entry (per ADR 0010):** this ADR involves PII,
  retention, and trust boundaries. Under ADR 0010 the review runs as parallel
  work for this target rather than an acceptance blocker, so the enforceable
  obligation is the queue entry, drained before the target's first production
  release — **the security half no longer holds this ADR's status.**

### `capture_run_edges` retention-class enum (2026-08-01, ADR 0014 D-E / D4 rider)

ADR 0014 D-E staged every capture observation into `capture_run_edges`, a
run-scoped conversion-state table nothing else can load (0014:381-382); a run
ending in a terminal failure commits zero graph rows, and those staging rows
"keep the terminal outcome and a retention class (value deferred to D4)"
(0014:383-386). D4 re-routed that enum here — "retention *is* lifecycle," this
ADR's axis (0006:72-78) — as a named, required companion rider, leaving
`capture_run_edges`'s retention class open until it landed (0010:184-186). This
amendment supplies it. *It adds no new store, reverses no base decision, and
re-owns neither D4's provenance predicate (0010:175-186) nor D5's park-and-sweep
ruling (0007:117-133). It stays strictly on this ADR's conversion-state axis: no
value grants `capture_run_edges` survival past certification — the durable
audit-lifecycle copy of a successful run lives in `screen_graph_*` (0014:362-364),
outside this enum. Status stays Accepted.*

**The enum: three values, one per purge behavior the retention job can execute.**
`CHECK (retention_class IN ('CONSUMED','FORENSIC','PENDING_MINT'))`. Values earn
their place by a **distinct purge behavior at the retention job's decision point**,
not by which actor reclassifies them — the least-machinery test (A1). A fourth
value distinguishing *who* reclassifies (a parked-contended class vs an
escape-session class) is rejected: the retention job does the identical thing to
both — hold and wait — so the distinction is not a purge behavior and would be
machinery the job cannot act on differently.

- **`CONSUMED`** — a successful run whose staged edges were minted into
  `screen_graph_*` (0014:387, :448); the staging copy is now redundant against a
  durable audit-lifecycle copy (0014:362-364). Purge is **event-driven**: the mint
  transaction sets this class and deletes the rows in-band, *after its final CAS
  commit* — because staged edges are re-read during the D3 CAS rebase (0014:448)
  right up to the writer's final commit (0014:449), so the class encodes
  mint-**completion**, never mint-**intent**. The retention job is a pure backstop
  that deletes a `CONSUMED` straggler **only after a read confirms the durable
  `screen_graph_versions` row for its `capture_run_id` exists** (a read under the
  no-cross-lifecycle-FK rule, 0006:147-149 — never a foreign key), and **never on a
  TTL**: timing out a `CONSUMED` row whose mint crashed between the class flip and
  the commit would destroy a still-needed forensic observation stream.
- **`FORENSIC`** — a run reaching a terminal *failure* outcome (ABORT / CRASH /
  TIMEOUT / NO_PROGRESS / BUDGET_EXHAUSTED, 0014:383-384) that committed zero graph
  rows; the observation stream must survive the process for CRASH forensics
  (0014:389). This is the one **eventless** value — no future actor will re-class it
  — so it purges on a **bounded TTL** measured from `terminal_outcome_at`, capped at
  a **30-day maximum**. The maximum is a named, versioned config value governed by
  CF6's no-silent-disable rule (a change is a recorded decision, the M18/CF6
  precedent at 0014:417); it is a *forensic* window, deliberately set shorter than
  any audit-retention clock so it can never read as audit retention, and it never
  grants survival past certification (0006:82-84).
- **`PENDING_MINT`** — a run that may still mint: mid-run rows, `COMMIT_CONTENDED`
  batches parked for the sweeper (0014:457, 0007:117), and open escape-hatch
  sessions spanning human time (0014:390-391). The retention job **never touches it**;
  it is reclassified by another actor's event — the sweeper's commit or a completed
  escape session → `CONSUMED`, an abandoned one → `FORENSIC`. Parked and escape rows
  fold here rather than into own classes because the job's behavior for both is
  identical (hold, wait); the sweeper-vs-human distinction is *who* reclassifies, not
  *how* it purges, and park-liveness / stuck-sweeper alerting stays D5 / ADR 0007's
  concern (0007:117-133, F-D5b/F-D5c), not this enum's. The fold is robust to D5's
  still-open keep/kill of the buffer (0007's S2-gated ruling): if the park buffer is
  dropped, contended batches fail-loud-and-recapture and `PENDING_MINT` simply never
  sees a parked row.

No companion `retain_until` date column: the class plus `terminal_outcome_at` is
the queryable surface, and a stored retention date would duplicate a value the TTL
already derives. The blob-reference retention-*date* pattern (0006:90-92) is
deliberately not mirrored here — it is scoped to PII-bearing artifacts under an
audit clock, a different lifecycle from disposable staging state.

**Consequences rider (extends `## Consequences`, 0006:104-143).** The lifecycle
partition now covers a third retention profile — bounded-forensic disposable state
— strictly inside the conversion-state schema. `capture_run_edges` gains one
timestamp column, `terminal_outcome_at`, whose sole purpose is the `FORENSIC` TTL
basis; it did not previously exist (0014:386 keeps the terminal *outcome*, not a
timestamp), so it ships in the staging table's initial DDL alongside
`retention_class`. Imposes on future work: the retention job's `CONSUMED` path reads
`screen_graph_versions` but takes no foreign key on it; the mint transaction owns the
in-band `CONSUMED` delete; and no `capture_run_edges` value may ever be extended to
outlive certification without reopening this rider.

**Compliance rider (extends `## Compliance`, 0006:145-161).** These are
ADR-0006-owned mechanisms that arch-validate inventories alongside the F-series
(not F-numbered — this ADR's own convention, 0006:147-156, matching the D3
amendment's, 0012:209); they reuse the F4 migration-check *shape* (0006:147-149)
and the quarterly retention-drill *shape* (0006:154-156).

- **Retention-class CHECK totality (automated, CI-blocking):** a schema-migration
  assertion that `capture_run_edges.retention_class` carries
  `CHECK (retention_class IN ('CONSUMED','FORENSIC','PENDING_MINT'))` and is
  `NOT NULL` after the follow-up migration; an insert with any other value, or NULL,
  fails the migration — the F4 migration-check shape (0006:147-149).
- **Read-gated one-directional purge (automated, CI-blocking):** two assertions —
  (i) no foreign key exists in *either* direction between `screen_graph_*` and
  `capture_run_edges`, keeping the purge "provably safe because no lineage row
  references it" (0006:82-84) and re-asserting the no-cross-lifecycle-FK rule
  (0006:147-149); and (ii) the retention job's `CONSUMED` deletion confirms the
  durable `screen_graph_versions` row by `SELECT` before `DELETE` and contains no TTL
  branch for `CONSUMED` — a `CONSUMED` row whose durable row is absent is not deleted
  (the mint-crashed-pre-commit guard).
- **Retention drill — staging extension (manual, quarterly; extends 0006:154-156):**
  in a staging copy, prove all three classes discharge correctly without touching
  `screen_graph_*`: (a) a `CONSUMED` batch whose durable `screen_graph_versions` rows
  are present purges completely, and one whose durable rows are **absent** does **not**
  purge — the mint-crash guard as an exercise, not an assumption; (b) a `FORENSIC`
  batch older than its 30-day TTL purges and one inside it survives; (c) a
  `PENDING_MINT` batch is **never** touched regardless of age. Prove lineage
  reconstruction still passes after each purge (0006:154-156). Park-liveness and
  stuck-sweeper detection are not exercised here — they are D5 / ADR 0007's concern.

**Honest residual.** `CONSUMED` is not decidable from the class value in isolation
— its backstop requires a cross-schema read into `screen_graph_versions`; accepted
because the class remains the backstop's scan predicate and the audit surface
proving in-band purge fired, and the read is a lookup, not a foreign key (F4
preserved). The `FORENSIC` 30-day maximum is fixed here; its within-cap operational
value stays CF6-governed. This rider does not solve park-and-sweep liveness, the
buffer's keep/kill, or the escape-hatch abandonment *trigger* — the first two are D5 /
ADR 0007's (0007:117-133), the third is the escape-hatch mechanism's; this rider only
names the retention *behavior* of the rows those mechanisms produce.

## Notes

Author: arch-decide stage 4 (agent draft)
Date: 2026-07-26
Approved by / date: Rajnish Khatri / 2026-07-26. Both named blockers closed on
the same day: the security-owner half by ADR 0010 (security review moved to a
parallel non-blocking track for this target), and the residency half by the
input arriving as **on-premises**, which permits co-location and leaves the
drafted topology unchanged.
Superseded date: —
Last modified / by / what: 2026-07-26 / arch-decide gate / Proposed → Accepted;
residency answer recorded with its two adjacent exposures (Perfecto device
cloud, model-provider egress) routed to stage 5
Last modified / by / what: 2026-08-01 / ADR 0014 D4 rider (Replan R1, owner) /
`capture_run_edges` retention-class enum amendment added — a three-value enum
(`CONSUMED` event-purged in-band after mint + read-gated backstop / `FORENSIC`
bounded 30-day CF6-governed TTL from a new `terminal_outcome_at` column /
`PENDING_MINT` hands-off, folding parked-contended and escape-hatch rows) with two
CI-blocking checks (CHECK totality; read-gated one-directional purge) and a
three-class retention-drill extension. Closes D4's named-and-required companion
rider (0010:184-186); the enum stays strictly conversion-state, re-owns neither D4
nor D5, and leaves the follow-up migration one-cell (add-CHECK + one-constant
backfill) by shipping `terminal_outcome_at` in the staging table's interim DDL.
Status unchanged (Accepted) — an amendment that adds a retention profile inside the
existing lifecycle partition, reversing no base decision.
