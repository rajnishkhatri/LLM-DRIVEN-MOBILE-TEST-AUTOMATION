# Spec: Mobile Test Automation — Weeks 0–3 Shared Spine

**Status:** SIGNED OFF (re-sign-off 2026-08-10, **post-erosion-gate baseline** — marker M44 added; prior baselines: post-P1-mitigation 2026-07-27, A0-fold clarification 2026-08-01) — ready for plan + tasks. Gate history: signed off 2026-07-26; re-opened/re-closed 2026-07-27 for the P3 fold-in; re-opened/re-closed 2026-07-27 for the P2 batch fold-in (M24/M28/M30/M32 + CF6/CF7); re-opened/re-closed 2026-07-27 for the P1 fold-in (M34–M40 + CF8–CF11) at a **combined gate** that also accepted ADR 0012 and ADR 0013 and ratified the ADR 0011 M39 amendment.
**Target:** mobile-test-automation, roadmap milestone 1 (weeks 0–3, "shared spine")
**Implementation home:** a **separate Spring Boot repository** — this workspace holds the spec, plan, and architecture artifacts; the plan's first tasks scaffold the new repo. Locked at spec scoping, 2026-07-26.
**Acceptance bar:** the blueprint's week-3 gate — *"one hand-written Appium test flows end to end and yields a valid ReplayReport"* (`docs/research/blueprint-revision-v2.md:123`) — **plus the M19 real-input clause** added 2026-07-27: ingestion must have produced `REAL_INGESTED` IR from real source material (see the WHERE criterion, clause b).

**Prior artifacts (constraints, not proposals — do not re-decide):**

- `docs/architecture/worksheets/mobile-test-automation/characteristics-worksheet.md` — top 3: reproducibility, security & privacy, verifiability
- `docs/architecture/components/mobile-test-automation/logical-components.md` — 16 components, 3 clusters
- `docs/architecture/worksheets/mobile-test-automation/style-decision.md` — one quantum, plain modular monolith, fitness functions F1–F7
- `docs/architecture/adrs/application/mobile-test-automation/` — ADRs 0001–0010 Accepted 2026-07-26 (0009 amended 2026-07-27, M35/M36); ADR 0011 Proposed (platform probe open; M39 erasure amendment ratified 2026-07-27); ADRs 0012–0013 Accepted 2026-07-27 at this spec's combined gate

**Scope decisions locked (2026-07-26):**

| ID | Decision |
|----|----------|
| S1 | Spec covers the weeks 0–3 shared spine only; Phase-1-live (weeks 3–8) gets its own spec |
| S2 | Implementation lands in a separate repo; spec + plan are the handoff artifact |

**Clarify decisions locked (2026-07-26):**

| ID | Decision |
|----|----------|
| C1 | Ingestion = **Excel (POI) + Octane REST** — two adapters behind one contract, proving it source-agnostic rather than Excel-shaped; ALM/QC stays additive later |
| C2 | The **queued device-replay seam is built now** (ADR 0007): CI enqueues, the device-gate worker consumes, producer writes via transactional outbox. Broker may start as a DB-backed queue; technology is plan-level |
| C3 | Primary store working assumption = **PostgreSQL** (on-prem, JSONB for IR payloads, row-level grants on lineage, DB-backed queue/outbox); swappable if the bank's catalog dictates |
| C4 | Full pinning set in the schemas from day one; fields with no spine meaning (prompt/model/provider/judge-calibration versions) carry an **explicit NOT_APPLICABLE marker**, never null — weeks 3–8 flips them to required-real without a migration. The marker enum also **reserves `UNPINNABLE_PHASE1`** (M12, ADR 0001 notes): the provenance class for fields the Phase-1 Copilot workflow structurally cannot fill; unused in the spine, present in the committed schema so weeks 3–8 needs no schema bump, rejected by the Phase 2 implementation at cutover |
| C5 | Static-gate locator rule validates against the committed **`LocatorCandidate` manifest only**; the object repository sits behind an interface with a read-only stub — real read integration arrives with Resolve Elements, write-back with certification |

**Open questions:** none.

## Problem

Everything after week 3 depends on a spine that does not exist yet: the schema
contracts (`TestCaseIR`, `LocatorCandidate`, `ReplayReport`), an ingestion path
that turns manual-test exports into IR, a hierarchy tool that captures device
UI evidence, and the deterministic replay pipeline that turns committed test
code into a classified, pinned, auditable verdict. Phase 1's Copilot-assisted
conversion (weeks 3–8) consumes all four; Phase 2 swaps the reasoning engine
and changes nothing else. The blueprint's load-bearing premise — *"Phase 1 is
not a throwaway prototype, it is the asset factory and data flywheel for
Phase 2"* — holds only if the spine is built with the decided architecture
from the first commit: the module boundaries, the append-only provenance
contract, and the fitness functions that are now the **only** protection for
three characteristics (style-decision §7).

The spine contains **no LLM call anywhere**. The week-3 gate exercises a
hand-written test precisely so the pipeline is proven before any generated
code reaches it.

## Target artifact

A new Spring Boot repository (Java, Maven) containing:

| Item | Content |
|------|---------|
| Module structure | Single deployable; three modules partitioned by cluster — `conversion`, `validation-certification`, `evidence` (ADR 0005). The blueprint's five names (ingestion, hierarchy-tool, conversion, replay, certification) survive as packages inside |
| Schema contracts | `TestCaseIR`, `LocatorCandidate`, `ReplayReport` as Java records with Jackson; JSON Schema exported via victools and committed |
| Ingestion CLI | Excel adapter (Apache POI) **and Octane REST adapter** (C1) emitting schema-valid IR through one adapter contract; contract tests bound to the **contract**, exercising both fixture families regardless of adapter completion (M20); per-adapter deterministic canonicalization + source-snapshot digest at intake (M15) |
| Screening library | Injection screening + secret/PII redaction, invoked at **three spine call sites**: the ingestion boundary, the hierarchy-capture output (the Acquire UI Evidence boundary — built in the spine, not deferred, because it is the designed Copilot IDE input and F3 structurally cannot see that egress), and the device-gate artifact pull at landing (ADR 0009 as amended, M35); versioned, red-team corpus seeded. The call is cheap by stated criterion — in-process, no network, one-line API — and the failure mode is quarantine-and-review with recorded, attributable overrides (M35) |
| Hierarchy tool | CLI + service against a live Perfecto device: full `getPageSource` XML, Object Spy output, and a pruned tree (interactive elements + ancestors) |
| Replay queue seam | CI enqueues replay requests; the device-gate worker consumes them; producer-side transactional outbox, idempotent consumer (ADR 0007, C2). DB-backed queue acceptable at first. Queue hygiene: bounded retry cap, backoff, dead-letter quarantine with alert (M21); schema supports async-projection reuse (M17/CF3) |
| Replay pipeline v1 | Static gate (format, `mvn compile`, Checkstyle, Error Prone, locator-manifest rule) → device gate (pinned Perfecto pool, TestNG, pinned Appium, single run for the spine) → rule-based classification → `ReplayReport` |
| Provenance schema | Append-only lineage store in PostgreSQL (C3), lifecycle-partitioned from conversion state (ADR 0006), written in the same local transaction as the state change it describes (ADR 0007); carries the source-snapshot digest (M15), per-artifact pull digests (M9), the `corpusClass` field (M19), the **authenticated principal** (M37), the **per-conversion hash-chain link** (ADR 0012), and a **retention-class field** (M39). Grants: the application role holds `INSERT`/`SELECT` only on lineage tables, DDL under a separate migration role; corrections are superseding appends, never updates (ADR 0012) |
| Object-repository seam | Interface with a read-only stub (C5); the static gate needs only the committed manifest |
| Fitness functions | F1–F4 as CI-blocking ArchUnit (or equivalent) rules from the first commit; F3's runtime half on the ingestion egress path. **Task zero:** the repository scaffold (empty-but-shaped three-module tree) plus F1–F4 wired CI-blocking precedes any feature commit — a build without the fitness functions wired is not a valid baseline (M18). Task zero also wires the **ADR 0012 grant assertion** (the app role cannot `UPDATE`/`DELETE` lineage tables) and the **warn-only secrets scan** on committed code (M34 — flips to blocking at weeks 3–8 entry, CF8). Disabling or weakening any F1–F7 requires a recorded decision, never just a commit (working-agreement rule, M3/M18) |

## Acceptance criteria (EARS)

### Failure paths first

- **IF** any type outside the model-boundary adapter package references a
  provider SDK, gateway client, or Copilot-specific construct, **THEN** the CI
  build MUST fail (**F1**, ADR 0001). The spine makes no model calls; the rule
  exists from the first commit so the seam never erodes.
- **IF** a source-system type (POI class, Octane/ALM DTO) crosses out of its
  source adapter, **THEN** the CI build MUST fail — the IR is the only thing
  that leaves ingestion (**F2**, ADR 0001).
- **IF** an ingestion path reaches its egress without a call to the screening
  library, **THEN** the CI build MUST fail (static half) **and** the runtime
  assertion MUST reject the payload (runtime half) (**F3**, ADR 0009 — both
  halves required; a dependency edge proves availability, not invocation).
- **IF** a lineage schema declares a foreign key into a conversion-state
  schema, **THEN** the CI build MUST fail (**F4**, ADR 0006 — retention
  deletion must stay safe).
- **IF** a `ReplayReport` or lineage row is missing any pinning field —
  applicable fields with a real value (`irVersion`, `codeCommit`,
  `pipelineVersion`, `appiumVersion`, device/OS/model, `appVersion`),
  not-yet-applicable fields with the explicit NOT_APPLICABLE marker (prompt,
  model/provider, judge-calibration versions; C4) — **THEN** the report MUST
  fail schema validation and no verdict may be recorded (**F6**). Null or
  absent is never valid for a pinning field. The marker enum includes the
  reserved `UNPINNABLE_PHASE1` value (C4, M12) — invalid in the spine, used
  in weeks 3–8 for Copilot-unfillable fields, rejected by Phase 2.
  Gate-run lineage rows (static and device) additionally carry the
  **CI-runner environment** — the runner-image digest plus JDK/Maven/
  pipeline-tool versions; the runner image is pinned **by digest** in CI
  configuration, never a floating tag (record-actual, risk mitigation M28).
  The prompt-version field's value-space is defined now: when it flips to
  required-real in weeks 3–8, its value MUST be the **Git commit SHA of the
  prompts-repository state** — content-addressed by construction; a branch
  name, tag, or semantic-version label is never a valid value (risk
  mitigation M30).
- **IF** the same replay request is delivered to the device-gate worker more
  than once, **THEN** exactly one device run MUST result — the consumer is
  idempotent, and a redelivery MUST NOT double-spend device minutes
  (ADR 0007, C2).
- **IF** test code contains `Thread.sleep`, **THEN** the static gate MUST fail
  it (explicit waits only; the lint rule is a determinism control, not style).
- **IF** a locator in test code is absent from the committed
  `LocatorCandidate` manifest, **THEN** the static gate MUST fail the test
  before any device is acquired (manifest-only in the spine; the
  object-repository lookup is a stubbed interface, C5).
- **IF** a device run fails for infrastructure reasons, **THEN** classification
  MUST be `ENV_INFRA` and the run MUST re-queue — never heal, never count
  against the test. Re-queue carries a **bounded, configurable retry cap with
  backoff between attempts** (values are plan-level); **IF** the cap is
  exhausted, **THEN** the run MUST dead-letter into a persisted quarantine
  state with an alert — never silently dropped, never retried further. The
  quarantine record's shape matches the future review-queue record so
  weeks 3–8 inherits it as a review item (queue hygiene, risk mitigation
  M21).
- **IF** ingested test data contains a literal secret or credential rather
  than a vault-key reference, **THEN** IR schema validation MUST reject the
  document (vault-key indirection is enforced at the schema, not by review).
- **IF** a provenance write fails, **THEN** the state change it describes MUST
  roll back with it (same local transaction) — a lineage gap is an
  auditability failure, not a logging warning (ADR 0007).
- **IF** a pulled device artifact is read by any downstream step before its
  SHA-256 digest is recorded in the append-only lineage row for the pull,
  **THEN** that read MUST fail — evidence without a landing digest does not
  exist as far as the pipeline is concerned (**hash-at-pull**, risk
  mitigation M9).
- **IF** a `TestCaseIR` reaches ingestion egress without a source-snapshot
  digest — the SHA-256 of the canonicalized source payload, computed at
  intake and written to append-only lineage — **THEN** schema validation MUST
  reject it. Downstream artifacts bind to the hashed snapshot, never to the
  live Octane/workbook reference (**hash-at-ingest**, risk mitigation M15).
- **IF** an ingestion-derived lineage row or gate-evidence record is missing
  its corpus class — a required `corpusClass` field, `REAL_INGESTED` or
  `FIXTURE` — **THEN** it MUST fail schema validation; absent is never valid,
  so a fixtures-only green cannot be misreported (risk mitigation M19).
- **IF** a device run yields a failure reason or exception type with no
  deterministic mapping in the classification rules, **THEN** the run MUST
  quarantine with an alert — recorded as an unmapped-classification outcome
  **distinct from the seven taxonomy classes** (a status, not an eighth
  class), never defaulted into any of them. Vendor taxonomy drift surfaces
  loud, not as a confident wrong diagnosis (**quarantine-unknown**, risk
  mitigation M10a).
- **IF** a device run's actually-reported execution context mismatches the
  requested set on any **pinned** facet (device model, OS version, Appium
  version), **THEN** the run MUST quarantine with an alert — the same
  persisted quarantine status as unmapped classifications, never silently
  counted as a normal run. A substituted device is not the run that was
  pinned (**record-actual**, risk mitigation M24).
- **IF** a lineage row lacks an authenticated principal — an **individual**
  principal for human actions, a **per-component service principal**
  (ingestion CLI, device-gate worker, pipeline service) for automated ones —
  **THEN** the row MUST be invalid at the database level. Service accounts
  are non-interactive, and a catch-all `system` principal is never valid —
  it would recreate the shared-login hole on the service side
  (schema-enforced attribution, risk mitigation M37).
- **IF** the application role attempts `UPDATE` or `DELETE` on a lineage
  table, **THEN** the database MUST refuse it (grants defined in the first
  migration) **and** a CI-blocking assertion MUST prove the refusal holds
  (task-zero wiring). Every legitimate correction is a compensating
  **superseding append**, never an edit; readers resolve the latest
  non-superseded row (ADR 0012, risk mitigation M38).
- **IF** a lineage row commits without its per-conversion hash-chain link —
  the predecessor row's digest, computed inside the same write transaction —
  **THEN** the write MUST fail; a partially chained lineage is not
  representable. A chain-verification mismatch quarantines with an alert,
  never a warning (ADR 0012, risk mitigation M38).
- **IF** an evidence artifact or lineage row lands without a retention-class
  field, **THEN** it MUST fail validation — the class is recorded at landing,
  while the context exists, so retention enforcement becomes a query rather
  than a forensic exercise once the M33 Q4 mandate returns (risk mitigation
  M39).
- **IF** the hierarchy tool's capture output is written for IDE/workspace
  use, or a pulled device artifact is landed, without a screening-library
  call, **THEN** the same two-half F3 construction applies: the static half
  fails CI and the runtime half rejects the payload. Both paths carry
  device-produced evidence — boundary (2) of ADR 0009 as amended; the
  capture-side call site is the only technical chokepoint the Copilot IDE
  egress will ever have (risk mitigation M35).
- **IF** a committed test fixture derived from real source material lacks
  the screening-library-version marker, **THEN** CI MUST fail — fixtures are
  **screened output only**, and raw workbooks never enter the repository.
  The M34 secrets scan is deliberately not relied on here: a workbook full
  of real account numbers trips no secrets rule (risk mitigation M35).
- **IF** the screening library flags a payload, **THEN** the payload MUST
  quarantine for review rather than hard-stop the pipeline; releasing it is
  a recorded, attributable override under the no-silent-disable line (M18).
  A blocking control with no sanctioned override manufactures unsanctioned
  ones; a recorded bypass is strictly better than the unrecorded kind (risk
  mitigation M35).
- **IF** test code (the reference test included — it authenticates) needs a
  credential, **THEN** it MUST resolve it through an **injected reference**,
  never a literal: interim provider is the CI secret store, and the
  M33-named vault binds later as a provider swap, not a code rewrite
  (credential indirection by construction, risk mitigation M34). A literal
  in committed code is flagged by the **warn-only** secrets scan — warn-only
  is a recorded owner ruling for the spine, with the blocking flip a dated
  weeks-3–8 entry criterion (CF8).
- **IF** a dev or CI container configuration declares a named volume or
  bind mount for a data directory, **THEN** the CI configuration check MUST
  fail — dev/CI data stores are **ephemeral-only by construction**; the
  M39 retention-class field makes any dev-class artifact identifiable and
  deletable (risk mitigation M40).

### Happy path

- **Ubiquitous:** the repository MUST build as a single deployable Spring Boot
  application with three modules — `conversion`, `validation-certification`,
  `evidence` — and a module-boundary check that fails the build on a violation
  (ADR 0005).
- **Ubiquitous:** the repository's first commit (task zero) MUST contain the
  three-module scaffold with F1–F4 wired as CI-blocking rules, preceding any
  feature code; a build without the fitness functions wired is not a valid
  baseline (M18). Task zero also wires the ADR 0012 grant assertion (the app
  role cannot `UPDATE`/`DELETE` lineage tables — CI-blocking) and the
  warn-only secrets scan (M34; blocking flip is CF8's dated obligation).
- **Ubiquitous:** `TestCaseIR`, `LocatorCandidate`, and `ReplayReport` MUST
  exist as Java records with Jackson bindings, and their JSON Schema exports
  MUST be committed and regenerated by the build (drift between record and
  schema fails CI).
- **WHEN** an engineer runs the ingestion CLI against an Excel workbook or an
  Octane test (REST, API-key auth), **THEN** it MUST emit schema-valid
  `TestCaseIR` JSON carrying the source reference **plus the
  canonicalized-snapshot digest** (M15) for provenance, with every
  step's text having passed the screening library, and ambiguous steps flagged
  in the IR rather than silently resolved. Both adapters implement the same
  contract; no source-system type crosses the adapter boundary (F2).
- **WHEN** an engineer runs the hierarchy tool against a live Perfecto device,
  **THEN** it MUST write the full `getPageSource` XML, the Object Spy output,
  and a pruned tree containing interactive elements plus their ancestors,
  suitable for IDE/workspace context — **every output passing the screening
  library at capture, before it is written** (the Acquire UI Evidence call
  site, M35: this output is the designed Copilot IDE input and no fitness
  function can see that egress). Every capture MUST record the device
  and pool identity it ran against; captures from outside the pinned pool
  are flagged in the capture record (M24 — the flag's consumer is weeks 3–8
  certification, per the carry-forward rider below).
- **WHEN** a committed test enters the replay pipeline, **THEN** the static
  gate MUST run first and complete in seconds with zero device cost, rejecting
  on format, compilation, Checkstyle, Error Prone, or the locator-manifest
  rule.
- **WHEN** the static gate passes, **THEN** a replay request MUST be enqueued
  via the producer's transactional outbox (C2); **WHEN** the device-gate
  worker consumes it, **THEN** it MUST acquire a device from a pinned Perfecto
  pool by capability set, execute via TestNG with pinned Appium and driver
  versions, run once (single-run gate for the spine; K-run policy is
  weeks 3–8), and pull the Smart Reporting artifacts for the run, computing
  and recording a per-artifact SHA-256 digest in lineage at landing
  (hash-at-pull, M9) and passing each pulled artifact through the screening
  library at landing (boundary (2) of ADR 0009 as amended, M35). The worker
  MUST hold **no gateway credential** — executing test code needs no model
  access; this is the ADR 0013 credential-topology shape from the first
  commit. The worker MUST record the **actual** execution
  context as the session reports it — device model/ID, OS version, Appium
  server version, available stack identifiers — alongside the requested set
  in the run's lineage row, with any delta explicit (record-actual, M24).
- **WHEN** device runs complete, **THEN** classification MUST be rule-based
  against the fixed taxonomy (`LOCATOR_NOT_FOUND`, `STALE_ELEMENT`,
  `TIMEOUT_SYNC`, `ASSERTION_MISMATCH`, `APP_CRASH`, `DATA_PRECONDITION`,
  `ENV_INFRA`) — deterministic rules mapping Appium exception types and
  Perfecto failure reasons; explicitly not LLM work.
- **Ubiquitous:** the Perfecto Smart Reporting response formats the pipeline
  consumes MUST be covered by contract tests against recorded fixtures, so
  vendor format drift fails a test the day it appears (M10, register
  entries S2/S3).
- **Ubiquitous:** the shared ingestion contract MUST carry a contract-test
  suite exercising it against fixture sets from **both** source families (the
  M16 real-workbook corpus; Octane record fixtures), running in CI from
  week 0 regardless of either adapter's completion state. Deferring an
  adapter is a recorded schedule decision; removing its fixture family from
  the contract suite is not permitted by that deferral
  (contract-neutrality by construction, risk mitigation M20).
- **Ubiquitous:** each ingestion adapter MUST define a deterministic
  canonicalization of its source payload as part of the adapter contract
  (Octane: the record's fields in canonical serialization; Excel: workbook +
  row range with normalized cell rendering), covered by that adapter's
  contract test. The canonicalized snapshot itself is stored in object
  storage under the standard classification/retention rules, so an auditor
  can reconstruct the exact intake, not just detect a mismatch. The same
  canonicalization feeds any future cache key (M15).
- **Ubiquitous:** every device artifact (video, page source, network capture,
  screenshot) MUST be stored in object storage with a data classification, a
  retention date, and a **retention class** (M39); the primary store holds
  references, never payloads (ADR 0006). Spine object-lock retention is
  deliberately **short** — spine gate evidence is proof-of-concept output and
  stays deletable; envelope encryption + crypto-shredding (ADR 0011 as
  amended) are built before the first artifact that must survive to the
  audit horizon, in weeks 3–8, not week 2 (M39).
- **Ubiquitous:** every pipeline action MUST write its lineage row to the
  append-only provenance schema in the same local transaction as its state
  change, carrying the applicable pinning fields (ADR 0006, ADR 0007, F6),
  the authenticated principal (M37), and the per-conversion chain link
  (ADR 0012).
- **Ubiquitous:** lineage chain heads MUST be anchored into the immutable
  evidence object store through the ADR 0011 port at a defined interval; a
  stale anchor is an alert, because a silently stopped anchoring job leaves
  the window since the last anchor unprotected (ADR 0012). Chain
  verification — recompute, compare to anchors — runs per release and after
  every restore.
- **Ubiquitous:** the quarantine/review record shape (M21/CF4) MUST carry a
  **sampling flag** for novelty-based review — payloads from source shapes
  not seen before, plus a small fixed random draw (M36; substitutes the
  worksheet's manual-sampling measure, recorded in the risk report). The
  red-team corpus regression MUST report **case count, source mix
  (seeded / operational / external), and date of last addition alongside
  the bypass rate**, so an inadequate corpus refutes its own green result
  (M36; ADR 0009 Compliance as amended).
- **Ubiquitous:** every CLI and tool emission (ingestion CLI, hierarchy tool,
  pipeline service/worker) MUST record its own **build identity** — the Git
  commit SHA embedded at build time — in the lineage rows and artifacts it
  writes, so build skew between separately-run executables is visible per
  artifact (record-actual, risk mitigation M32).
- **Ubiquitous:** per-run `ReplayReport` and lineage records MUST carry
  outcome fields sufficient to derive a K-of-K pass count later **without any
  vendor aggregate** — the schema foundation for the carried-forward certify
  read-source rule (M10b).
- **Ubiquitous:** the outbox/queue schema (C2) MUST support reuse as an
  async, retryable, idempotent projection channel — the mechanism the
  carried-forward certify-locally/publish-async rule (M17) reuses instead of
  adding infrastructure.
- **WHERE** the week-3 gate is exercised, two binding clauses:
  **(a) one hand-written Appium test, committed to the repo, MUST flow end to
  end — static gate, device gate on a real Perfecto device, classification —
  and yield a `ReplayReport` that validates against the committed schema with
  a complete applicable pinning set** (the replay leg is hand-written by
  design — corpus class does not apply to it); **(b) the ingestion CLI MUST
  have produced schema-valid, screening-passed `TestCaseIR` from real source
  material — at minimum the M16 Excel corpus — recorded as `REAL_INGESTED` in
  lineage.** Fixture-only ingestion evidence does not satisfy the gate; the
  numeric real-input floor is plan-level, set when the M16 corpus request
  returns (risk mitigation M19).

## Non-goals (weeks 3+ or explicitly excluded)

- Any LLM or model call, Copilot prompt assets (`copilot-instructions.md`,
  `*.prompt.md`), exemplar library — weeks 3–8
- ALM/QC adapter — later roadmap; additive behind the adapter contract that
  Excel and Octane already prove (C1)
- K-run policy, flakiness thresholds, certification gates, fidelity judging —
  weeks 3–8+
- Locator healing / repair loops — Phase 2 machinery
- Review-queue UI and human-decision routing — the spine has no HITL surface
- Metrics dashboard / provenance read model — the write contract is in scope,
  the projection is not
- Object-repository read integration and write-back — stubbed interface only
  (C5); nothing is certified in the spine
- Envelope encryption + crypto-shredding machinery — **designed now**
  (ADR 0011 as amended, M39), **built before the first audit-retained
  artifact** in weeks 3–8; the spine's short object-lock retention is the
  posture that makes this deferral honest
- Sandbox technology for generated-code execution — the **shape** (separate
  process, no credentials) is committed by ADR 0013 and the device-gate
  worker builds to it; the technology choice is weeks 3–8, before the first
  generated script executes
- Phase 2 anything (Orchestrator AI integration, generation services)

## Carry-forward rules (bound now, enforced by the weeks 3–8 spec)

Seven accepted risk mitigations govern machinery the spine does not build
(certification, Octane write-back, the review queue). Writing them as EARS
criteria here would put permanently-unverifiable clauses on the week-3 gate,
so they are recorded as carry-forwards instead — each paired with the spine
schema provision that must not preclude it.

**The weeks 3–8 spec MUST import this list at its scoping step; dropping an
entry is a recorded decision, not an omission.**

| # | Rule | Source | Spine provision (built now) |
|---|------|--------|------------------------------|
| CF1 | **Custody-before-certify** — certification may not issue until every evidence artifact is pulled, hashed, and landed on-prem; the certify component checks all references resolve locally before writing a verdict | M6 | Hash-at-pull lineage digests + object-storage landing (this spec) give the precondition something to check |
| CF2 | **Certify read-source** — K/K derives from bank-held, hash-bound per-run records, never a vendor aggregate | M10b | Per-run outcome fields sufficient for K/K derivation (ubiquitous criterion above) |
| CF3 | **Certify-locally, publish-async** — verdict + certified locators write to bank-held lineage first; Octane publication is an async, retryable, idempotent projection, never a precondition | M17 | The C2 outbox/queue schema supports the projection reuse (ubiquitous criterion above) |
| CF4 | **Review-record calibration fields** — every human-reviewed conversion captures its quality judgment in labeled-set format, exported to the golden-set store; Phase 2's judge-calibration set accumulates as a byproduct | M11 | The M21 quarantine record already matches the review-queue record shape; the labeled-set fields join that record definition |
| CF5 | **Published-asset-version verdict field** (conditional) — if the M7 probe confirms Octane asset versioning, the certification verdict records the published asset version | S7 / M7 | Verdict schema is weeks 3–8; no spine provision needed beyond noting the pending probe |
| CF6 | **K-integrity** — K is a pinned, versioned config value; every verdict's lineage records K-configured vs. K-executed; certify refuses a verdict whose executed count is below configured K; changing K is a recorded decision (M18's no-silent-disable extended to gate thresholds: K, pass rate, locator stability) | M25 | Per-run outcome fields (M10b criterion) already support deriving K-executed; the spine's single-run gate is the honest K=1 baseline — no schema change needed. **D6 (2026-08-01 decision log, first exercise of this row's recorded-decision clause):** replay K pinned at 1 for the spine; a raise to 3/5 is a pre-registered CF6 entry criterion gated on the S2 flake-base-rate threshold — **event-anchored, not calendar-anchored**: no certification verdict may be issued while the K re-decision is un-taken (schedule may slide; the verdict-issuing event is the forcing function). Inconclusive S2 → hold K=1 with a bounded re-run deadline; D6 fixes the decision branches, S2 sets the numeric threshold |
| CF7 | **Fidelity re-derivation** — the certification verdict binds to the *cached judge response*: cache key, judge prompt version (a Git commit SHA per M30), calibration-set version, and input/output hashes recorded in verdict lineage; re-derivation is deterministic cache replay, never a fresh model call. Residual recorded: the retention floor (S19/M1) must cover verdict-referenced cache entries — the "rebuildable" cache (M27) gains a retention-bound row class | M29 | Cache store exists by decision (M27 — PostgreSQL schema, ADR 0002 Notes); M15 canonicalization feeds the cache key; verdict schema is weeks 3–8 |
| CF8 | **Vault-key indirection, warn-to-blocking flip** — generated tests reference vault keys, never literal values; the M33-named vault binds as the indirection provider; the secrets scan flips from warn-only to **blocking** as a weeks-3–8 *entry criterion*, not an aspiration ("blocking later" is the promise most likely to evaporate); certification refuses a test whose code carries a literal credential | M34 | Credential-indirection failure-path criterion + warn-only secrets scan in task zero (this spec) — indirection removes the place a literal would go, which is what makes warn-only survivable |
| CF9 | **Advisory judge, never autonomous** — the fidelity judge's grade advises a human certifier; certification is an attributable individual decision (protects M37's principal-attribution, bounds MRM scope). The model inventory (Copilot, gateway model, judge — purpose, version, output consumer) is a week-0 artifact stating "MRM applicability unverified" on its face | M41 | None needed — a constraint on the weeks-3–8 certification design; the M37 principal schema (this spec) is what the human verdict lands on |
| CF10 | **Generated-code execution isolation** — the execution context holds no long-lived credentials, receives a short-lived single-run device session token, never holds the gateway credential; generated code runs in a **separate OS process** (shape committed now, sandbox technology at the last responsible moment); static capability rules (no filesystem outside workspace, no arbitrary egress, no process spawn, no reflection) gate execution as a supplement, not the control | M42 / ADR 0013 | The spine's device-gate worker is built without the gateway credential from the first commit (device-gate criterion above) — the credential-topology shape that makes the weeks-3–8 retrofit unnecessary |
| CF11 | **Auditor-export inheritance** — export authorization rides M37's individual principals and the M33 Q2 IdP; bundle handling rides M33 Q3 classification; contents carry M39 retention classes; and **every export is itself an attributable lineage event** — who exported what, when, recorded rather than reconstructed | M43 | The M37 principal schema and M39 retention-class field (this spec) are the fields the export event inherits |

Rider (M24): certified locators require **pinned-pool capture provenance** or
a recorded decision accepting off-pool evidence — the certification-side
consumer of the off-pool flag the hierarchy-tool criterion above builds.

## Known break risks

- **Perfecto and Octane access are on the critical path** — the week-3 gate
  needs a real device run, and C1 adds Octane REST (API-key auth) to the
  spine; credentials, pool access, and network paths to both must exist early,
  or the gate slips for non-engineering reasons.
- **The Excel adapter meets real workbooks** — the sources call Excel "the
  least deterministic input"; a green contract test on a clean fixture does
  not mean the messy real workbook parses. Mitigate: the **M16 week-0 corpus
  request** — 10–20 representative real workbooks across the feeding teams,
  requested before the adapter is written; the effective contract is derived
  from the corpus and encoded as the adapter's contract-test fixtures. The
  same corpus is the M19 gate clause's real-input source and the Excel half
  of the M20 dual-fixture suite. **Raw workbooks stay in a controlled
  location and never enter Git** — committed fixtures are screened output
  carrying the library-version marker, enforced by the M35 CI check (a real
  manual test script carries account numbers, hostnames, and names
  regardless of what the flows run against; E2 does not cover it).
- **Fitness functions are load-bearing, not confirmatory** — F1–F3 are the
  only protection for boundaries that no longer exist in the structure
  (style-decision §7). If the ArchUnit rules are cut for time, three
  characteristics silently lose all protection.
- **On-premises object storage is self-operated** (ADR 0006) — MinIO/Ceph or
  an appliance needs provisioning before artifacts can be stored; a filesystem
  stopgap would leak into the retention design.

## Clarify pass

Run 2026-07-26, five questions asked one at a time, all answered; decisions
recorded as C1–C5 in the locked-decisions table above and folded into the
criteria. One answer varied from the recommendation, recorded with its
rationale: **C1** chose Excel + Octane over Excel-only (proves the adapter
contract source-agnostic early, at the cost of a second external credential
dependency in the spine). The other four followed the recommendation.

## Risk-mitigation edit pass (2026-07-27)

Stage-5 (arch-risk) pass P3 routed eleven accepted mitigation rules plus three
riders to this spec. All were reviewed one at a time with the owner and folded
in as decided:

| # | Rule | Decision | Landed as |
|---|------|----------|-----------|
| 1 | Hash-at-pull (M9) | Accepted as proposed | Failure-path criterion + device-gate pull clause |
| 2 | Hash-at-ingest + canonicalization (M15) | Accepted, **with snapshot storage** | Failure-path criterion, IR digest field, canonicalization criterion |
| 3 | Queue hygiene (M21) | Accepted as proposed | ENV_INFRA criterion amended: cap, backoff, persisted quarantine + alert |
| 4 | Corpus class + real-input floor (M19) | Accepted, both halves | `corpusClass` failure-path criterion + second binding clause on the week-3 gate |
| 5 | Dual-fixture contract tests (M20) | Accepted as proposed | Ubiquitous criterion binding both fixture families to the contract |
| 6 | Task-zero F1/F2 wiring (M18) | Accepted as proposed | Ubiquitous task-zero criterion + fitness-function row; no-silent-disable referenced to the working agreement |
| 7 | Quarantine-unknown (M10a) | Recommendation applied (question skipped) | Failure-path criterion (status, not eighth class) + Smart Reporting contract-test criterion |
| 8–11 | Certification-stage rules (M6, M10b, M17, M11) + S7 | Accepted as carry-forwards | Carry-forward section CF1–CF5 + two spine-real schema criteria (K/K outcome fields; outbox projection reuse) |
| R2 | `UNPINNABLE_PHASE1` reservation (M12) | Accepted | C4 amended + F6 criterion notes the reserved value |
| R3 | Workbook corpus 10–20 (M16) | Accepted | Known-break-risk paragraph updated |

## P2 batch risk-mitigation edit pass (2026-07-27)

Stage-5 (arch-risk) pass P2 routed four field rules plus two carry-forward
rows to this spec. All six were reviewed one at a time with the owner and
accepted as proposed:

| # | Rule | Decision | Landed as |
|---|------|----------|-----------|
| 1 | Record-actual execution context (M24) | Accepted, all three parts | Pinned-facet-mismatch quarantine (failure path), actual-vs-requested lineage fields on the device-gate clause, hierarchy-capture pool provenance + off-pool flag, CF rider on certified-locator provenance |
| 2 | CI-runner pinning (M28) | Accepted, both parts | F6 criterion amended: gate-run lineage carries runner-image digest + JDK/Maven/tool versions; runner image pinned by digest, never a floating tag |
| 3 | Prompt version = Git commit SHA (M30) | Accepted | F6 criterion amended: the prompt-version field's future value-space is the prompts-repository commit SHA; labels/tags never valid |
| 4 | CLI/tool build identity (M32) | Accepted | New ubiquitous criterion: every CLI/tool emission records its build-time Git SHA in the lineage rows it writes |
| 5 | CF6 K-integrity (M25) | Accepted | Carry-forward row: K-configured vs. K-executed, certify refuses under-K, K changes are recorded decisions |
| 6 | CF7 fidelity re-derivation (M29) | Accepted | Carry-forward row: verdict binds to the cached judge response; re-derivation is cache replay; verdict-referenced cache entries retention-bound |

## P1 risk-mitigation edit pass (2026-07-27)

Stage-5 (arch-risk) pass P1 routed ten spec-routed rules plus four
carry-forward rows to this spec. By owner direction the pass was applied as
a batch and taken at **one combined gate** together with ADR 0012/0013
acceptance and the ADR 0011 M39 amendment (departure from the one-at-a-time
review used for P3/P2, recorded here).

| # | Rule | Source | Landed as |
|---|------|--------|-----------|
| 1 | Credential indirection by construction | M34 | Failure-path criterion (injected reference, CI-secret-store interim, vault as provider swap); warn-only secrets scan in task zero, flip dated via CF8 |
| 2 | Acquire UI Evidence call site built in the spine | M35 | Hierarchy-tool criterion amended (screening at capture); screening-library row names all three call sites |
| 3 | Artifact-pull screening at landing | M35 | Device-gate clause amended + failure-path criterion (two-half F3 construction on boundary (2)) |
| 4 | Screened-fixture markers with a CI check | M35 | Failure-path criterion (unmarked fixture fails CI; raw workbooks never in Git) + known-break-risk paragraph |
| 5 | Cheap-call criterion + quarantine-and-review failure mode | M35 | Screening-library row (in-process, no network, one-line API) + failure-path criterion (recorded attributable overrides, M18) |
| 6 | Novelty-sampling flag + corpus provenance-mix reporting | M36 | Ubiquitous criterion (sampling flag on the M21/CF4 record shape; regression reports count / source mix / last addition beside bypass rate) |
| 7 | Schema-enforced individual principal, per-component service principals | M37 | Failure-path criterion (DB-level invalid without principal; non-interactive service accounts; no catch-all `system`) + lineage-write criterion + provenance-schema row |
| 8 | Lineage hash chain, grants, no-UPDATE assertion, supersede semantics | M38 / ADR 0012 | Two failure-path criteria (chain link in same transaction; grant refusal + CI assertion in task zero) + anchoring ubiquitous criterion (interval anchors, stale-anchor alert, verification per release/restore) |
| 9 | Retention-class field + short spine object-lock retention | M39 / ADR 0011 amendment | Failure-path criterion (missing class fails validation) + object-storage criterion (short retention, crypto-shredding before first audit-retained artifact) + non-goals entry |
| 10 | Ephemeral-only dev/CI data directories | M40 | Failure-path criterion (named volume / bind mount fails the CI configuration check) |
| CF8–CF11 | Vault-key indirection flip; advisory judge; execution isolation; auditor-export inheritance | M34 / M41 / M42–ADR 0013 / M43 | Four carry-forward rows, each with its spine provision named; the device-gate worker's no-gateway-credential shape is spine-real (CF10) |

## Amendment — A0-fold (2026-08-01, sdd-replan-class, scoped to M15)

**Source decision:** [ADR 0015](../../architecture/adrs/application/mobile-test-automation/0015-defer-the-llm-normalizer-a0-and-fold-deterministic-canonicalization-into-ingestion.md) (Accepted 2026-08-01) — Replan R1 D2. The proposed **A0 LLM normalizer** is **deferred** (evidence-gated future re-open, not rejected); a **minimal deterministic phrase-canonicalization table + noise-strip ruleset** is **folded** into the already-decided M15 per-adapter canonicalization surface (the `Ingestion CLI` row above), **not** into A1's structure-only contract. This is the smallest possible re-open — a clarifying amendment to existing M15 behaviour, adding no new M-number, no model call, no new ADR 0009 call site (the fold crosses no trust boundary), and no F1 out-of-spine placement.

**Scope ruling carried from ADR 0015:** screen-context inference (`screenContextHint`) stays **A2's** responsibility (walkthrough §2.2 already assigns `screenContext` to A2, inside the screened Invoke Models seam); the fold does not attempt it and A0 is not resurrected to own it. The fold is purely lexical (synonym-table + noise-strip).

**Placement fork:** RESOLVED to FOLD-now by owner at the gate; DEFER-only fallback retained on record (drop the fold clauses, keep only the deferral + WHERE gate) **iff** adapter-contract review finds the table expands the M15 contract beyond "minimal" — never RATIFY.

**Landed as:**

| # | Rule | Source | Landed as |
|---|------|--------|-----------|
| A0-1 | M15 canonicalization MAY include a committed/versioned/diffable phrase-canonicalization table + noise-strip ruleset, applied to the canonicalized rendering **before** the source-snapshot digest; owned by the adapter team, contract-tested (M20); pure deterministic string transforms upstream of A1 | ADR 0015 / M15 | `Ingestion CLI` row clarified (appended clause below) |
| A0-2 | Unpinned mapping fails CI | ADR 0015 | **IF** an adapter's phrase-canon table or noise-strip ruleset is applied but not committed/versioned/diffable (a live/unpinned mapping), **THEN** the CI build MUST fail — an unreconstructable canonicalization breaks the M15 snapshot-digest auditability |
| A0-3 | No model call in the fold | F1 / ADR 0001 / ADR 0015 | **IF** any ingestion-adapter canonicalization step (incl. phrase-canon/noise-strip) issues a model call, **THEN** the CI build MUST fail — the fold is deterministic by construction; a model call there is an out-of-spine surface belonging behind Invoke Models |
| A0-4 | Deterministic apply feeds the digest | ADR 0015 / M15 | **WHEN** an adapter canonicalizes, **THEN** it MAY deterministically apply the table + ruleset before emitting the snapshot, and that snapshot MUST be the input to the M15 digest (provenance keys on canonical content); no `NormalizedIntent` type and no LLM output crosses the adapter boundary — only the IR leaves ingestion (F2) |
| A0-5 | Contract-tested both families | M20 | **Ubiquitous:** each adapter's table + ruleset MUST be exercised by that adapter's contract test against both fixture families (M16 real-workbook corpus; Octane record fixtures) from week 0; a change to the table is a reviewable commit, never a silent runtime override |
| A0-6 | Evidence gate for the deferred A0 re-open | ADR 0015 (rider on the §12.4 spike) | **WHERE** the A0 LLM-normalizer re-open is evaluated (a future decision, not this baseline), one binding precondition: the A1 parse-failure rate MUST have been measured on the M16 corpus **plus a real free-form-English sample**, decomposed into (a) fold-fixable and (b) genuinely-novel-phrasing, with (b) further gated on whether A2's existing LLM-fallback already absorbs it. Absent that measurement, A0-as-an-LLM-stage stays deferred |

**Appended clause to the `Ingestion CLI` target-artifact row (M15):** per-adapter deterministic canonicalization MAY include the committed phrase-canonicalization table (synonym → canonical-form, e.g. `{sign in, log in, login} → login`) and deterministic noise-strip ruleset (boilerplate, headers, step-numbering), applied before the source-snapshot digest; pure in-adapter deterministic string transforms — no model call, crossing no trust boundary, invoking no ADR 0009 call site, requiring no F1 out-of-spine placement (ADR 0015); upstream of A1, A1's structure-only contract untouched.

**Task-board impact:** none of T01–T43 are invalidated. The fold lands inside **T17/T18/T19** (the adapter canonicalization contract + Excel/Octane adapters) and its CI guards inside **T02** (F1/F2 ArchUnit) and **T22/T24** (contract-test + fixture-marker checks); A0-6 is a rider on the future measurement spike, not a spine task. These are clarifications to existing task scope, not new tasks — reflected at Stage-3 task-refresh, not as a board change here.

## Amendment — Test-suite-erosion gate (2026-08-10, sdd-spec-class, net-new marker M44) — SPEC-OK 2026-08-10

> **Status of this amendment.** **SPEC-OK recorded 2026-08-10 (owner).** It
> re-opened the 2026-07-27 signed-off baseline to add one net-new marker (M44)
> and its criteria M44-1..M44-6, and is now **closed** — the current baseline.
> A7's sdd-spec dependency is thereby satisfied; A7 now **rides the pending
> board TASKS-OK like A1–A6** (it does not land on this spec closure). The
> staged `AGENTS.md` deltas apply at that board gate, not here.

**Source decision:** the 2026-08-10 conservative adoption study
(`docs/research/spine-agents-md-adoption-study.md` §6) and its ratification in
`mobile-test-automation-spine.tasks.md` **Amendment A7** (four owner decisions,
RATIFIED 2026-08-10). Provenance is an **adoption study, not an arch-risk
Stage-5 pass** — recorded as such: the gate is adopted on the **CR-18 + T22/M20
precedent** basis, not a new risk-storm finding. It **generalizes M20** — the
contract-neutrality rule, *"removing a fixture family from the contract suite is
not permitted by a deferral"* — from *ingestion fixture families* to *the whole
JUnit Jupiter suite*.

**Marker-ID note (open at SPEC-OK).** `M44` continues the risk-mitigation series
because the gate is a recorded, gate-enforced mitigation of a decay risk and a
sibling of M20; no new namespace is minted (a one-rule namespace would be slop).
If the owner prefers a different ID or series at SPEC-OK, it is a find-replace —
nothing downstream has bound to `M44` yet.

**What it is (one line):** a git-range test-inventory diff that fails CI when a
commit range **silently** weakens the suite — a removed test method, a newly
`@Disabled` one, or one neutralized by `assumeTrue(false)` — unless the range
carries a `TEST-WEAKEN-OK: <recorded-decision ref>` waiver naming why the weaker
suite is still sound.

**Scope ruling (greenfield-honest).** The gate is a **range diff**, so at task
zero — no prior inventory — it is **inert**, and it never requires tests to
exist; it forbids the **silent removal** of tests that do. It is made verifiable
at the week-3 gate not by waiting for an organic erosion event but by a
**self-test that deliberately weakens a canary and asserts the gate fires** —
the exact **M20/T22 meta-test** construction the gate was ratified on. This is
why the criterion is not a permanently-unverifiable week-3 clause (contrast the
carry-forwards CF1–CF11, whose machinery the spine does not build): the erosion
gate's machinery *and* its proof-of-firing are both spine-real.

**Enforcement split by reliability (owner decision 3).** The **deterministic**
signals block from commit one; the **gutted-assertion-body** heuristic is
**warn-only, indefinitely** — a body-shape signal is false-positive-prone, and a
blocking control that cries wolf manufactures un-waivered bypasses (the same
reasoning as the M35 screening quarantine-not-hard-stop line).

**Waiver (owner decision 4).** The `TEST-WEAKEN-OK` token MUST cite a recorded
decision — a decisions-log line or an ADR (M3/M18) — never bare text; a token
with no resolvable ref fails the same as no token.

**Landed as:**

| # | Rule | Source | Landed as |
|---|------|--------|-----------|
| M44-1 | Silent removal / disable fails CI | study §6 / M20 grown | **IF** a commit range removes a JUnit Jupiter test method (`@Test`, `@ParameterizedTest`, `@RepeatedTest`, `@TestFactory`, `@TestTemplate`), adds `@Disabled` to one, or neutralizes one with `assumeTrue(false)` / `assumeFalse(true)`, **AND** the range carries no `TEST-WEAKEN-OK: <ref>` line, **THEN** the CI build MUST fail — deterministic signals, blocking from the first commit that has a prior inventory to diff against |
| M44-2 | Waiver cites a recorded decision | M3/M18 | **IF** a `TEST-WEAKEN-OK` waiver names no resolvable recorded-decision ref (a decisions-log line or an ADR), **THEN** the build MUST fail as if unwaived — the waiver records *why the weaker suite is still sound*, attributably, never bare text |
| M44-3 | Gutted body is warn-only | owner decision 3 | **IF** a retained test method has its body stripped of assertions / `fail()` (the gutted-assertion heuristic), **THEN** CI MUST emit a **warning only** and MUST NOT fail the build — a false-positive-prone body-shape signal never gates CI |
| M44-4 | Inventory is source-derivable | — | **Ubiquitous:** the test inventory (fully-qualified method identity) MUST be derivable from committed source alone, so the range diff is deterministic and needs no test *execution* to enumerate |
| M44-5 | Self-test / meta-test | M20 / T22 | **Ubiquitous:** the gate MUST ship a self-test that deliberately removes-or-disables a canary test in a throwaway range and asserts the gate fails — the M20/T22 meta-test construction; a gate that cannot demonstrate its own firing is not a valid baseline (M18) |
| M44-6 | Static `@Disabled` assist | ArchUnit | **IF** a committed test carries `@Disabled` whose declared reason does not name a `TEST-WEAKEN-OK` ref, **THEN** the architecture-test build MUST fail — a deterministic current-tree assist to M44-1 that also catches a `@Disabled` predating the range window |

**Staged `AGENTS.md` deltas (apply on TASKS-OK per A7 — the v1.0.0 file is
content-final, so these are staged, not yet written):** the `Never weaken the
test suite` Never-list line, the definition-of-done step, and the Common-changes
row, all as drafted in tasks.md A7, referencing enforcer **T04** and marker
**M44**.

**Task-board impact:** no T01–T43 task is invalidated. The gate lands in **T04**
(the range check), its task-zero CI wiring + the M44-6 ArchUnit assist in
**T02**, and the M44-5 self-test rides the **T22** meta-test slot — the T04 + T02
scope A7 already ratified. Reflected at Stage-3 task-refresh, not a board change
here.

## Sign-off gate

**Re-opened and re-closed 2026-08-10 (test-suite-erosion gate amendment, above)**
— owner **SPEC-OK** recorded. Adds net-new marker **M44** (six criteria,
M44-1..M44-6) generalizing M20 from ingestion fixture families to the JUnit
Jupiter suite; contradicts no ADR (**not** sdd-replan-class); enforcement split
by reliability (deterministic signals block, gutted-body warn-only); waiver
cites a recorded decision. This is the **post-erosion-gate baseline**. tasks.md
A7's sdd-spec dependency is now satisfied; A7 joins A1–A6 on the pending
**board TASKS-OK**, on which A7 lands, `[A7]` tags go on T04/T02, and the staged
`AGENTS.md` deltas apply (this spec closure does not land them).

**Re-opened and re-closed 2026-08-01 (A0-fold amendment, above)** — owner
sign-off at the sdd-spec Stage-2 gate for ADR 0015, folded in as a single
approve-all clarification: ADR 0015 Proposed → Accepted; the M15 fold clause +
criteria A0-1..A0-6 added; A1 contract untouched; screenContext scope-ruled to
A2. This is the **post-A0-fold baseline**.

**Closed — human re-sign-off recorded 2026-07-27** at the **combined gate**
covering the P1 fold-in (third risk-mitigation edit pass; ten rules +
CF8–CF11, applied as a batch by owner direction), ADR 0012 acceptance,
ADR 0013 acceptance, and ratification of the ADR 0011 M39 amendment — one
decision, approve-all. This is the **post-P1-mitigation baseline**; plan +
tasks may proceed. Prior closures remain on record: 2026-07-26
(pre-mitigation baseline), 2026-07-27 (post-P3-mitigation baseline),
2026-07-27 (post-P2-mitigation baseline). Any further risk-storming
mitigation that changes scope re-opens this gate via sdd-replan.
