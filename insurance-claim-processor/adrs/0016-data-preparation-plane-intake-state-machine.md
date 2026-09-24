# ADR 0016. Add the data-preparation plane as a second orchestrated workflow inside the existing quantum

## Status
Accepted — 2026-09-23 (ratified as recommended; amendments below). Formerly: Proposed — revised 2026-09-23 by the v2 HLD pass (it was never Accepted, so it
is modified rather than superseded). Extends ADR 0004 (a second Standard state
machine). Related: 0017–0022.

## Context
v1 is live (`../build/DEPLOY-LEDGER.md` Stage 9). It is an **orchestrated
workflow over a modular core**: one Python package in one zip, per-state
Lambdas, one Step Functions Standard machine, one bucket and one AppConfig
application. That is **one quantum** (`../worksheets/style-decision.md` v2,
review finding).

v2 must validate, enrich and format multimodal claim data *before* that
workflow (C1-a…C7-a). The claim now arrives as:
- a structured intake row;
- a narrative;
- document images;
- a call recording;
- the policy's loss runs.

Forces:
- **Characteristics:** v2's top 3 match v1's (integrity, privacy,
  auditability), with no counteracting clusters. There is an
  *operational* divergence: batch vs per-claim unit of work; config-heavy vs
  ADR-stable change; cost and throughput vs decision reliability
  (`../worksheets/characteristics-worksheet.md` v2).
- **Latency mismatch:** a v1 execution can wait up to 7 days for HITL (ADR
  0005). Intake must never wait for that.
- **Audit:** "which batch, which revision, which execution" must be answerable.

Alternatives (scored in style-decision v2):
- **Placement:**
  - (a) new states inside the v1 machine;
  - (b) a second workflow in the same quantum with a **pre-cut seam** (Q-1);
  - (c) a separate quantum now: own bucket, package and release train (Q-2).
- **Style:**
  - (A) orchestrated pipeline (Step Functions Map + Parallel);
  - (B) event-driven choreography (the assignment's shape, made robust);
  - (C) a Glue-native PySpark ETL pipeline.
- **Topology:** a fixed workflow vs a Strands agent choosing which services to
  call vs per-modality agents.

## Decision
We will add the data-preparation plane as a **second Step Functions Standard
workflow, `claim-processor-intake`, inside the existing quantum**: the same
package (new subpackage `dataprep/`), the same bucket, the same AppConfig
application. The seam is **pre-cut**, so it can become its own quantum when a
split trigger fires.

Justification first:
- **Technical:**
  - One characteristics cluster argues for the monolith family; a second quantum
    would buy isolation that async edges already provide.
  - Async edges both ways stop the 7-day HITL latency leaking into intake
    (Dynamic Quantum Entanglement, `ArchCharScope.md:72-74`).
  - The orchestrated pipeline keeps a recorded execution history and a real
    join for conservation accounting. Choreography would *reconstruct* that
    (fails on auditability); Glue ETL would add `pyspark`, violating the
    no-new-deps rule.
- **Business:** time to market. It reuses v1's style, package, runbook and
  deploy account. One builder, one release train, and cost stays within the
  existing $10 budget.

Shape:
- **One execution per batch.** Admit → Glue-DQ batch gate → row gate →
  `Map` over claims (MaxConcurrency 4) → a `Parallel` over sources →
  reconcile → assemble bundle → dispatch → account.
- **Not an agent.** The path is fixed and application-decided. Parallelism
  comes from a `Parallel` state, not from agents. Adjuster Q&A is a
  tool-less multi-turn call (ADR 0021).
- **Communication:**
  - Intake → v1 is **async** `StartExecution`, named
    `claim-<claim_id>-r<revision>`, with v1's existing input shape
    `{bucket, key}`.
  - v1 → intake feedback is **async choreography**: S3 Object Created →
    EventBridge. v1 makes no new outbound call.
  - Inside intake: orchestration, with the async services (Glue DQ,
    Transcribe) as start → budgeted poll.
- **Pre-cut seam** (this is what makes a later split cheap):
  - the bundle contract (`schema_version`, ADR 0017) is the only shared code;
  - separate IAM roles (ADR 0020);
  - single-writer prefixes (ADR 0017);
  - an import rule: v1 may import only `dataprep.contracts`.
- **One retry layer, owned by the orchestrator:** state `Retry` with full
  jitter and a max delay; intake SDK clients `max_attempts=1`
  (`../risk/resilience-clinic.md` v2 §3).
- **Split triggers** — make intake its own quantum when any of these fires:
  - a separate team owns intake;
  - intake code changes force risky v1 redeploys;
  - raw-media retention or residency diverges from claim records;
  - volume needs isolation beyond Map concurrency and reserved concurrency.

## Consequences
**Good:**
- v1's decision path, approval predicate and audit trail are unchanged. Its
  definition changes by one pass-through (the bundle fields in
  `UngroundedFallback`).
- Intake failures cannot break decisions in flight.
- One offline suite proves both sides of the contract, so there is no version
  skew.
- Execution history per batch, plus a named v1 run per claim revision.

**Bad / accepted:**
- Batch latency: the Glue DQ start-up is minutes. That is acceptable for
  back-office work; the SLO is `needs-input`.
- Adding a modality means editing the `Parallel` in the ASL. A microkernel-style
  reader registry is the future move if modalities multiply.
- Shared-bucket coupling stays until a split trigger fires. It is mitigated by
  single-writer prefixes and SD-4 (ADR 0017).
- Inline Map caps a batch at 200 rows. Distributed Map is the scale-out path.

**Losers:**
- (a) couples batch and claim lifecycles and redeploys the live machine for
  every intake change.
- (c) doubles release trains for one builder, for isolation already obtained.
- (B) loses on auditability and conservation.
- (C) loses on testability (new dependency, DPU minimums, awkward async
  services). Revisit it at thousands of rows per batch.
- The agent topology loses on determinism and audit.

## Compliance
Offline fitness (the `unittest` gate):
- **ASL structure:** Admit first; every async poll loop has a budget Choice;
  every `Task` has `TimeoutSeconds` greater than its Lambda timeout; every
  `Retry` has `JitterStrategy: FULL` and `MaxDelaySeconds`; each source branch
  has a `Catch`; Map `MaxConcurrency` ≤ 4; the execution has a
  `TimeoutSeconds`.
- **Dispatch:** the v1 start is named `claim-<id>-r<rev>`, and
  `ExecutionAlreadyExists` → `already_started`.
- **Import rule** (AST): `dataprep/contracts.py` imports no other
  `claim_processor` module; v1 modules import only `dataprep.contracts`.
- **Legacy:** all existing v1 tests pass unchanged (W4).

`[sfn]`: deploy-check both machines. `[gate]`: the smoke shows one intake
execution per batch and one v1 execution per claim revision.

## Amendments ratified 2026-09-23 (risk storm, `../risk/risk-storm-v2-data-prep.md` §5)
- **M14** execution-level watchdog: EventBridge rule on intake execution FAILED/TIMED_OUT/ABORTED → `batch_failed` summary + metric; alarm on intake `ExecutionsFailed`; DLQ on the trigger; reserved concurrency ≥ 20; inline-Map cap **50 rows**, Distributed Map (Standard child per claim) above; trimmed iteration outputs.
- **M18** fail closed on missing flags: a `bundles/` key whose state lacks `bundle_flags` → human review; `Record` re-checks routing for dict payloads; publish Lambda versions + alias-qualified ARNs when IaC lands.

Detailed EARS criteria land in the spec revision (R10).

## Notes
Author: arch-decide (v2 HLD, provisional batch A2-a)
Approved by / date: Rajnish Khatri / 2026-09-23 ("ratify as recommended")
Superseded date:
Last modified: 2026-09-23 / revised — the first draft framed intake as a
separate "plane" with implied separate-quantum semantics. Style-decision v2
fixed it as one quantum with a pre-cut seam. The service choices moved to ADR
0018 and the DQ gate to ADR 0019.
