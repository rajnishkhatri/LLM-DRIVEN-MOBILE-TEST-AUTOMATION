# ADR 0019. Gate intake quality at batch and row grain from one rule catalog

## Status
Accepted — 2026-09-23 (ratified as recommended; amendments below). Formerly: Proposed. Related: 0016, 0017, 0018.

## Context
Part 1 of the assignment asks for Glue Data Quality on structured data plus
custom checks. Two different failure classes must be caught:
- a **systemic** defect: a broken upstream export must not become 200
  human-review items;
- a **per-claim** defect: a bad row must not sink its batch.

Two grains need two gates:
- the Glue DQ catalog evaluation gives dataset-level rule outcomes and a score;
- per-row fate needs row-level checks.

The draft spec kept **two rule sources** (a DQDL file and Python twins) plus a
parity test, which **detects** drift. The component analysis flagged
connascence of meaning between them (`../components/logical-components.md` v2,
SD-1).

The assignment's API (`awsglue.data_quality.DataQualityRule`) does not exist;
Glue takes a DQDL string (spec P-d). A crawler per batch infers types from
exactly the dirty data the gate exists to catch, and adds 1–2 min.

Alternatives:
- **Engine:**
  - (a) Glue DQ batch gate + Lambda row gate;
  - (b) Lambda-only (all rules in Python);
  - (c) Glue ETL with `EvaluateDataQuality` row-level outcomes (needs PySpark
    — rejected in ADR 0016).
- **Rule source:** two sources + a parity test vs **one catalog that renders
  DQDL**.
- **Catalog:** a crawler per batch vs an **explicit all-string table with
  per-batch partition registration**.
- **When Glue DQ is down:** fail closed vs a deterministic fallback gate.

## Decision
We will evaluate intake quality at **two grains from one rule catalog**:
- **Batch gate — Glue DQ.** The ruleset is evaluated on the batch partition
  only (`pushDownPredicate`). A score below `dq.batch_min_score` (0.80), or a
  batch over 200 rows, quarantines the **whole batch** before any per-claim
  spend.
- **Row gate — Lambda.** Blocking rules quarantine the row; warning rules flag
  the claim, which routes it to review. A raw value that normalizes cleanly
  is *info*, not a warning.
- **One catalog.** `Intake Rule Catalog` defines every rule once (dimension,
  severity, row check) and **renders the DQDL**. That removes the drift class
  instead of detecting it. An escape-hatch rule type carries verbatim DQDL for
  rules the catalog cannot express (CustomSql, analyzers).

This ADR also records:
- **Catalog:** an explicit all-string `claims_intake` table (OpenCSVSerde,
  header skipped). The raw zone is strings; formats are validated by rules,
  and types are applied by the canonicalizer. Partitions are registered per
  batch by Admit. **No crawler on the hot path.** A one-time crawler run or
  Glue rule-recommendation run on the synthetic batch is allowed as a
  bootstrap aid.
- **Glue DQ outage:** **fail closed** (quarantine; re-run through the
  ADR 0017 lock takeover or a resubmission).
  **Deferred:** the deterministic fallback gate (the catalog evaluating batch
  aggregates in Lambda for ≤ 200 rows, marked `gate_engine: fallback`).
  Unlock: a batch SLO exists (`needs-input`).
- **Run hygiene:**
  - `ClientToken=<batch_id>-dq`;
  - `NumberOfWorkers=2`, `Timeout=10`;
  - `CloudWatchMetricsEnabled`, `ResultsS3Prefix=quality/dq-results/`;
  - on poll-budget exhaustion, call `CancelDataQualityRulesetEvaluationRun`.

Justification:
- **Technical:**
  - Each grain matches its failure class (shed a systemic defect early; isolate
    a local one).
  - One definition per rule makes the two gates semantically equal *by
    construction*.
  - Explicit schemas stop type inference from hiding the defects the gate
    exists to catch.
- **Business:**
  - Human-review capacity is protected from bad exports.
  - Upstream gets batch-level feedback (the quarantine record + an alarm).
  - DQ trends are visible over time (the assignment's explicit ask).

## Consequences
**Good:**
- Batch-level DQ history and metrics come from Glue.
- Row-level fate is deterministic and fast.
- The drift class is removed.
- The PoC cost is cents per run **[re-verify]**.

**Bad / accepted:**
- About 1–2 min of Spark start-up per batch.
- Analysts edit the catalog, not raw DQDL.
- Rules the catalog cannot express go through the verbatim escape hatch,
  outside the single-definition guarantee (kept small, and listed).
- Fail-closed means a Glue outage delays every batch until re-run.

**Losers:**
- (b) Lambda-only: no managed DQ history or result store — **observability**
  (the assignment's own ask).
- (c) Glue ETL: testability and the no-new-deps rule.
- Two rule sources + a parity test: detects drift after it is written instead
  of preventing it.
- A crawler per batch: integrity (type inference) + latency.

## Compliance
Offline fitness:
- The rendered DQDL equals the committed `glue/claims_intake.dqdl` snapshot
  (golden).
- Every catalog rule has a row check or is marked batch-only, and
  escape-hatch rules are listed explicitly (unit).
- Seeded corpus: 100 % of blocking defects quarantined, 100 % of warnings
  flagged, 0 blocking flags on clean claims (spec AC-Z9).
- A 201-row batch is quarantined with zero service calls.
- Stubber: budget exhaustion → the cancel call is issued.

`[gate]`: `create_data_quality_ruleset` accepts the rendered DQDL (syntax),
and the smoke's DQ score matches the fake's pinned score within the
documented tolerance.

## Amendments ratified 2026-09-23 (risk storm, `../risk/risk-storm-v2-data-prep.md` §5)
- **M2** ambiguity-aware canonicalizer: day≤12 dual-valid dates → blocking `dq_warn:ambiguous_date` unless independently corroborated; date order keyed by source/issuer, not channel.
- **M3** catalog hardening: completeness renders non-empty; header exact-match → `invalid_schema`; report_date ≥ loss_date; exactly one CSV per partition.
- **M17** pin the DQ config per batch at Admit; `config_source=fallback` → quarantine (fail closed); catalog hash stamped in the Glue ruleset description and compared.

Detailed EARS criteria land in the spec revision (R10).

## Amendment 2026-09-23 — one systemic defect quarantines the batch (LLD Q10-a)
Found at the LLD (Wave A review): with the score-only rule (15 batch rules,
a 0.80 minimum score), a batch is quarantined only when 4 rules fail. One
systemic defect, for example `currency` re-coded in every row, passes. Then
all 200 claims go to review, which is the flood this ADR exists to prevent.

We now quarantine the whole batch, before any per-claim spend, when
(`../design/lld-v2-data-prep.md` CAT-10, CAT-14):
- **any** batch-form rule fails → `dq_rule_failed`. Blocking rules use
  `t_block` = 0.80 and the warning rule `t_warn` = 0.50. Both are code
  constants and part of the catalog hash, so isolated bad rows do not trip
  the batch rule;
- or the score is below `dq.batch_min_score` → `dq_score_low` (the ratified
  rule, kept);
- or the run fails or its poll budget is spent → `dq_run_failed`;
- or one row-only warning hits more than half the rows → `dq_warn_systemic`,
  decided at the row gate, because the DQDL cannot see those rules.

A batch under 10 rows (`MIN_ROWS_BATCH_VERDICT`) skips the first two checks.
Its score is still recorded, and the row gate still applies.

- *Why this over the alternative:* the score-only rule, as first written,
  lets one systemic defect through.
- *Trade-off accepted:* the good rows of a batch with one systemic defect
  wait for a resubmission under a new batch id (LLD REC-09).

Approval criteria: not flagged (it narrows what reaches processing).
Approved by / date: Rajnish Khatri / 2026-09-23 ("Q10-a")

## Notes
Author: arch-decide (v2 HLD, provisional batch A2-a)
Approved by / date: Rajnish Khatri / 2026-09-23 ("ratify as recommended")
Superseded date:
Last modified: 2026-09-23 / Q10-a amendment (LLD)
