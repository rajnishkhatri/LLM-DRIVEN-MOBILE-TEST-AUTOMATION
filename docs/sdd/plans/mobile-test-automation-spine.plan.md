# Plan: Mobile Test Automation — Weeks 0–3 Shared Spine

**Status:** APPROVED — PLAN-OK recorded 2026-07-28. Both gate items ratified as drafted: (1) the five-Maven-module reading of ADR 0005's "three modules" (three cluster modules + `spine-contracts` kernel + `screening` library + thin `app` assembly), and (2) the §4 plan-level values (retry cap 3, 30-day spine retention, 24h anchor interval).
**Spec:** `docs/sdd/specs/mobile-test-automation-spine.spec.md` (signed off 2026-07-27, post-P1-mitigation baseline)
**Constitution:** `.cursor/rules/architecture-principles.mdc`
**Gates:** `<none>` in this workspace — the *new repo's* CI is itself a deliverable (task zero)
**ADR posture:** **no new ADR raised.** Every plan decision lands inside the envelope of ADRs 0001–0013; plan-level picks are recorded here per C2/C3 ("technology is plan-level"). Two standing flags carried, not created: ADR 0011 is **Proposed / PROBE-PENDING** (plan builds to its port with the MinIO default), and PostgreSQL is a **working assumption** pending the bank-catalog confirmation (misinterpretation risk #5) — either resolving against us is an sdd-replan event, not a silent patch.

## 1. Approach (A1 — simplest thing that satisfies the criteria)

Build the spine as **one Maven reactor, one Spring Boot deployable**, in a new repository, with the least machinery that satisfies every EARS criterion:

- **No broker.** The C2 queue seam is a **PostgreSQL-backed queue** (outbox table + `SELECT … FOR UPDATE SKIP LOCKED` consumer). ADR 0007's shape (transactional outbox, idempotent consumer) is fully expressible in the primary store; a broker is a later swap behind the same schema, which the M17 projection-reuse criterion already requires the schema to survive.
- **No registry, no plug-in machinery.** Source adapters are Spring-selected implementations of one interface (the gate's declined-microkernel decision, ADR 0005/0001); F1/F2 ArchUnit rules are the boundary, per the style decision.
- **No UI, no LLM call, no gateway credential anywhere** — by construction; F1 makes it CI-fail.

**G1 items — new abstractions, with the simpler thing rejected:**

| Abstraction | What it buys | Simpler thing rejected, why |
|---|---|---|
| `spine-contracts` Maven module (the three IR records + marker enums + JSON-schema export) | One home for the spine every module shares; schema-drift check has one target | Records living in their producer modules — makes `evidence` depend on both other clusters to type lineage references, inverting the CA=13 dependency direction |
| `screening` Maven module (own artifact, own version) | The library-version marker on screened fixtures (M35) needs a real, citable version; three call sites across two cluster modules need one dependency | Package inside `conversion` — would force `validation-certification` (artifact-pull landing site) to depend on `conversion`, an edge the module map forbids |
| Object-storage **port** interface + MinIO adapter | ADR 0011 is Proposed; the port makes the probe outcome a provider swap | Direct MinIO/S3 SDK calls — turns the pending probe into a rewrite |

**Gate item (interpretation of ADR 0005) — RATIFIED at PLAN-OK 2026-07-28:** the spec says "three modules." The reactor below has five Maven modules: the three **cluster modules** (`conversion`, `validation-certification`, `evidence`) plus two non-cluster artifacts (`spine-contracts`, `screening`) and the thin `app` assembly. Reading taken: ADR 0005's "three modules" governs *domain-logic partitioning by cluster*; a shared contracts kernel and a shared library are not a fourth domain partition.

## 2. Repository architecture

```
mobile-test-automation-spine/          (new repo — S2)
├── pom.xml                            reactor + enforcer + pinned plugin versions
├── spine-contracts/                   TestCaseIR, LocatorCandidate, ReplayReport (Java records,
│                                      Jackson); PinnedValue marker enum {REAL, NOT_APPLICABLE,
│                                      UNPINNABLE_PHASE1(reserved)}; corpusClass; retentionClass;
│                                      victools JSON-schema export + committed schemas + drift check
├── screening/                         injection screening + secret/PII redaction; one-line API;
│                                      library version constant; red-team corpus + regression report
│                                      (count / source mix / last-addition date / bypass rate — M36)
├── conversion/                        packages: ingestion (adapter contract, excel/, octane/,
│                                      canonicalization, snapshot digest), hierarchytool (capture,
│                                      prune, pool-identity), assets (stub pkg reserved)
├── validation-certification/          packages: staticgate, devicegate (worker, artifact pull,
│                                      record-actual), classification (taxonomy rules, quarantine),
│                                      replayreport, objectrepo (port + read-only stub — C5)
├── evidence/                          packages: lineage (append-only writes, principal, hash chain,
│                                      supersede reads), outbox+queue, objectstorage (S3 port +
│                                      MinIO adapter), anchoring (job + verification), retention
├── app/                               Spring Boot main; wiring; the single deployable (ADR 0005)
├── architecture-tests/  (or in app/)  ArchUnit: F1 F2 F3-static F4 + module-boundary + no-gateway-
│                                      credential-in-devicegate (ADR 0013 shape)
├── db/migration/                      Flyway; V1 = lineage core + grants (INSERT/SELECT-only app
│                                      role; DDL under migration role) + principal constraints
└── ci/                                pipeline-as-code: runner image pinned BY DIGEST (M28);
                                       gitleaks warn-only (M34); ephemeral-volume config check (M40);
                                       fixture screening-marker check (M35); grant assertion job
```

Component → home mapping (spine subset of the 16): Ingest Test Sources and Acquire UI Evidence → `conversion`; Verify Statically, Replay on Devices, Classify Replay Outcome → `validation-certification`; Preserve Provenance → `evidence`. Coordinate Conversion exists only as the thin CI-side enqueue path in the spine (no reasoning-path orchestration until weeks 3–8).

## 3. Technology selections (plan-level, inside ADR envelopes)

| Concern | Pick | Envelope |
|---|---|---|
| Language/build | Java 21, Maven multi-module | blueprint premise |
| Store | PostgreSQL 16, JSONB for IR payloads, Flyway | C3 (working assumption — catalog check pending) |
| Queue/outbox | Postgres tables, SKIP LOCKED consumer, idempotency key = replay-request ID | C2, ADR 0007 |
| Fitness functions | ArchUnit (F1, F2, F3-static, F4, module boundaries); F3-runtime = egress assertion in code | style decision §7 |
| Schema export | victools → committed JSON Schema, regenerate-and-diff in build | spec (named) |
| Static gate | Spotless(format) + `mvn compile` + Checkstyle + Error Prone + custom Checkstyle checks (`Thread.sleep` ban, locator-manifest rule) | spec |
| Device gate | TestNG + pinned Appium client; Perfecto capability-set acquisition | spec |
| Object storage | AWS SDK S3 client behind the port; MinIO default | ADR 0011 (Proposed) |
| Secrets scan | gitleaks, warn-only (blocking flip = CF8, weeks 3–8 entry) | M34 |
| CI tests infra | Testcontainers (Postgres, MinIO) — inherently ephemeral, satisfying M40 | M40 |
| Reference-test credential | CI secret store injection; vault binds later as provider swap | M34 |

## 4. Plan-level values the spec delegated

Ratified at PLAN-OK 2026-07-28; all config-shaped, adjustable without re-opening the plan.

| Value | Setting | Note |
|---|---|---|
| Device retry cap / backoff (M21) | cap **3**, backoff 1m → 5m → 15m, then dead-letter + alert | config, not code |
| Anchoring interval (ADR 0012) | every **24h** + on release; stale alert at >36h | chain verification per release + after restore |
| Spine object-lock retention (M39) | **30 days**, retention class `SPINE_POC` | deliberately short per spec |
| Real-input floor (M19, week-3 gate clause b) | **OPEN — set when the M16 corpus returns.** Placeholder: ≥5 distinct real workbooks to `REAL_INGESTED` | gate task blocks on this being set, not on a guess |
| Service principals (M37) | `svc-ingestion-cli`, `svc-devicegate-worker`, `svc-pipeline` | DB CHECK: principal NOT NULL, `system` rejected |

## 5. Work packages and dependency order

Task zero is WP0 by spec mandate (M18): **scaffold + F1–F4 wired CI-blocking + ADR 0012 grant assertion + warn-only secrets scan, before any feature commit.**

| WP | Content | Depends | Week |
|---|---|---|---|
| **WP0** | Task zero: reactor scaffold, empty-but-shaped modules, CI with F1–F4, Flyway V1 (lineage core + grants), grant assertion (Testcontainers proves app role can't UPDATE/DELETE), gitleaks, M40 volume check, runner digest pin | — | 0 |
| **WP1** | `spine-contracts`: records, marker enums, corpusClass, retentionClass, schema export + drift check, F6 validation (null-never-valid) | WP0 | 0–1 |
| **WP2** | `evidence` core: append-only lineage + principal enforcement + hash chain (in-tx) + build-identity capture (M32), outbox/queue schema (projection-reusable, M17), S3 port + MinIO adapter, anchoring job + verification | WP1 | 1 |
| **WP3** | `screening` library: API, redaction + injection rules, versioning, red-team corpus + regression report, quarantine-with-recorded-override path | WP0 | 1 (parallel WP2) |
| **WP4** | Ingestion: adapter contract + canonicalization contract, Excel/POI + Octane REST adapters, snapshot digest + stored snapshot (M15), screening at egress + F3 runtime half, dual-fixture contract suite (M20), ambiguity flags, vault-key schema rule, fixture-marker CI check | WP1–3 | 1–2 |
| **WP5** | Hierarchy tool: Perfecto session, `getPageSource` + Object Spy + pruned tree, screening at capture (M35), device/pool identity + off-pool flag (M24) | WP1–3 | 2 (parallel WP4) |
| **WP6** | Replay pipeline: static gate; outbox enqueue; idempotent worker (pinned pool, TestNG, **no gateway credential** — ADR 0013 shape, asserted); artifact pull with hash-at-pull (M9) + screening at landing; record-actual (M24); classification rules + quarantine-unknown (M10a) + ENV_INFRA requeue/cap/DLQ (M21); ReplayReport + F6; Smart Reporting contract tests (M10) | WP1–3 | 2–3 (parallel WP4/5) |
| **WP7** | Week-3 gate: committed hand-written Appium test (credential-injected, M34) end to end on a real Perfecto device → valid ReplayReport (clause a); M16 corpus ingested `REAL_INGESTED` at the floor (clause b); gate evidence recorded in lineage | WP4, WP6 | 3 |

**External critical path (week-0 probe basket coupling):** Perfecto credentials + pinned pool and Octane API key gate WP5/WP6/WP4 respectively; the **M16 corpus** gates WP4's real fixtures and WP7 clause b; PostgreSQL catalog confirmation gates WP2 finality; MinIO provisioning gates WP2's storage leg. None gates WP0/WP1/WP3 — start there regardless.

## 6. Constitution alignment & risks

Trade-offs surfaced per decision (broker-less queue, module-count reading, MinIO default); every abstraction carries its G1 justification; language-agnostic where possible, Java where the blueprint fixes it. Top risks: Perfecto/Octane access slipping the gate for non-engineering reasons (spec's own known break risk — WP7 is the only WP that hard-requires them); the module-count reading being rejected at this gate (contained — tree reshuffle, no schema impact); M16 corpus arriving late (floor stays OPEN, clause-b task blocks honestly rather than passing on fixtures).

## 7. Gate

**CLOSED — PLAN-OK recorded 2026-07-28.** Both flagged items ratified as drafted. Next: `mobile-test-automation-spine.tasks.md` (atomic tasks, EARS criteria mapped 1:1, dependency/parallelization markers), then the Stage-4 analyze pass (spec ↔ plan ↔ tasks ↔ constitution + grounding).
