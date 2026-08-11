---
type: architecture
title: 'P3 — A committed test''s journey to the week-3 gate — detail tables'
description: 'Locator: this view opens SYS from p1-spine-context.'
tags: [architecture, presentation]
---

# P3 — A committed test's journey to the week-3 gate — detail tables

> How does a committed test become an auditable verdict? The replay leg of the spine at component grain — static gate first (seconds, zero device cost), then the queued device gate, then rule-based classification; every hop writes append-only lineage. Opens SYS from P1; gate clause b's ingestion path lives in P2 and the detailed set.

**Locator:** this view opens `SYS` from `p1-spine-context`. It is a **completeness reference** at this grain.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 1 | GIT | Holds the committed hand-written Appium reference test (week-3 gate, clause a); its credential resolves through an injected reference from the CI secret store, never a literal (M34) |
| 2 | STATIC | Format, mvn compile, Checkstyle, Error Prone, Thread.sleep ban, locator-manifest rule (manifest-only in the spine; object repository stubbed — C5). Runs first, completes in seconds, zero device cost |
| 3 | QUEUE | PostgreSQL-backed queue (C2, ADR 0007): transactional outbox on the producer, SKIP LOCKED consumer; bounded retry cap 3 with backoff, dead-letter quarantine + alert (M21); schema supports async-projection reuse (M17) |
| 4 | WORKER | Idempotent consumer — redelivery of the same request yields exactly one device run, no double-spent device minutes (ADR 0007) Holds NO gateway credential — the ADR 0013 credential-topology shape from the first commit Records the actual execution context alongside the requested set; a mismatch on any pinned facet quarantines with an alert (record-actual, M24) |
| 5 | EXEC | Separate OS process, spawned per run — shape committed now, sandbox technology weeks 3–8 (ADR 0013); single-run device session token; no long-lived credentials |
| 6 | PERFECTO | Device acquired from a pinned pool by capability set; TestNG with pinned Appium and driver versions; single run — the K-run policy is weeks 3–8. Smart Reporting formats covered by contract tests so vendor drift fails a test the day it appears (M10) |
| 7 | CLASSIFY | Rule-based against the fixed taxonomy (LOCATOR_NOT_FOUND, STALE_ELEMENT, TIMEOUT_SYNC, ASSERTION_MISMATCH, APP_CRASH, DATA_PRECONDITION, ENV_INFRA) — deterministic, explicitly not LLM work An unmapped outcome quarantines with an alert as a status, not an eighth class (M10a); ENV_INFRA re-queues, never counts against the test (M21) |
| 8 | LINEAGE | Every pipeline action writes its lineage row in the same local transaction as its state change (ADR 0007), carrying the applicable pinning fields (F6), the authenticated principal (M37), and the per-conversion hash-chain link (ADR 0012) App role holds INSERT/SELECT only; corrections are superseding appends, never updates (ADR 0012) |
| 9 | OBJ | Per-artifact SHA-256 recorded at landing, before any downstream read (hash-at-pull, M9); every artifact stored with data classification, retention date, and retention class (M39) |

## Edge detail

| Edge | Detail the short label hides |
|------|------------------------------|
| GIT → STATIC | The committed hand-written Appium test enters the replay pipeline from the repository |
| STATIC → QUEUE | On static-gate pass, the replay request is enqueued via the producer's transactional outbox (C2, ADR 0007) — one of the two async seams |
| WORKER → QUEUE | SELECT … FOR UPDATE SKIP LOCKED consumer; idempotency key = replay-request ID |
| WORKER → PERFECTO | Acquisition by capability set from the pinned Perfecto pool |
| WORKER → EXEC | One test-execution process per run (ADR 0013) |
| EXEC → PERFECTO | TestNG with pinned Appium; single-run device session token (ADR 0013) |
| WORKER → PERFECTO | Video, page source, network capture, screenshot — pulled after the run |
| WORKER → OBJ | SHA-256 at landing before any read (M9); screening at landing (M35); classification + retention class on every artifact (M39) |
| WORKER → CLASSIFY | Appium exception types + Perfecto failure reasons feed the deterministic rule table |
| STATIC → LINEAGE | Gate-run lineage rows also carry the CI-runner environment: runner-image digest + JDK/Maven/pipeline-tool versions (M28) |
| WORKER → LINEAGE | Actual-vs-requested execution context recorded with any delta explicit (M24); build identity of the worker recorded per emission (M32) |
| CLASSIFY → LINEAGE | The ReplayReport validates against the committed schema with the complete applicable pinning set (F6) — null or absent is never valid for a pinning field; outcome fields support deriving K-of-K later without vendor aggregates (M10b) |

## Not shown for brevity

- **Screening library** — every pulled artifact passes screening at landing (M35) — the library and its three call sites are shown in P2 (not shown here for brevity)
- **Ingestion CLI + hierarchy tool** — week-3 gate clause b (REAL_INGESTED ingestion from the M16 corpus) runs through the conversion module — see P2; this view shows clause a's replay leg only

## Key

- rectangle = a grouping of code inside a container (C4 component)
- double-bordered rectangle, `EXT:` = an external system we don't own
- cylinder = a data store (used for datastores ONLY)
- dash-bordered rectangle = a runtime process, not a deployable
- solid arrow = synchronous call
- dashed arrow = asynchronous message/event
- `[Type]` under a name = the element's C4 type (container/component)

