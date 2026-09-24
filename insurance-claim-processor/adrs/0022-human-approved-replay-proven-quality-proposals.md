# ADR 0022. Improve data quality through human-approved, replay-proven configuration proposals

## Status
Accepted — 2026-09-23 (ratified as recommended; amendments below). Formerly: Proposed. Extends ADR 0010 (a second AppConfig profile, `data-quality`) and
ADR 0015 (bounded, reversible, auditable changes). Related: 0019, 0021.

## Context
Part 4.3 of the assignment asks for a "feedback loop to improve data quality
based on model responses". The richest under-used signals are:
- (1) **FM-vs-source disagreement** per field: the FM read "11 March" while
  intake parsed `11/03/2026` as 3 Nov;
- (2) **reviewer `field_changes`**: ground truth, live only once F2 (HITL)
  ships.

A loop that retunes rules *by itself* can silently widen acceptance upstream
of the approval gate (the configurability ↔ integrity tension in the v2
worksheet). C4-a (confirmed) says: propose only; a human approves.

Alternatives:
- **Apply:** (a) auto-apply learned changes; (b) **proposals + human approval
  + rollout with rollback**; (c) reports only, no structured proposals.
- **Proposal generation:** (i) an FM writes rules or regex; (ii) **a bounded,
  typed proposal set, validated by deterministic replay**.
- **Where config lives:** (i) code constants; (ii) a JSON object in S3; (iii)
  **a second AppConfig profile** with deployment strategies.

## Decision
We will turn disagreement signals into **bounded, typed proposals** that are
proven by **deterministic replay** and applied only by a **human**, through an
AppConfig deployment of the `data-quality` profile (the existing linear-bake
strategy, rollback-able).

- **Measure** (always on, event-driven): each v1 record for a bundle
  (`pending-review/bundles/*` or `results/bundles/*` → EventBridge) yields a
  feedback record — per field, agree/disagree against each source, raw and
  normalized values. Names are stored only as a boolean match. It also emits
  `FieldDisagreement{Field, Channel}`. Reviewer `field_changes` take
  precedence when present.
- **Propose** (on demand: `python -m claim_processor dq propose`). The types
  are limited to `set_date_order{channel, order}`, `add_date_format{format}`
  (from a fixed candidate list) and `adjust_threshold{key, value}`. A pattern
  qualifies only with ≥ 3 supporting claims **and** a replay fix rate ≥ 80 %.
  Quarantine records count as evidence. Each proposal carries claim ids,
  counts and before/after.
- **Apply:** a human deploys the new config version. Reprocessing goes through
  a **resubmission batch** (`revision + 1`), so each revision keeps its own
  audit trail.

Justification:
- **Technical:**
  - Integrity: nothing widens acceptance without a human.
  - Auditability: proposal → approver → config version → the bundles that used
    it.
  - Determinism: replay is offline and involves no FM calls.
  - Reversibility: an AppConfig rollback.
- **Business:**
  - Upstream format drift (a partner sending DMY dates) is fixed at the root
    once, instead of adjusters correcting dates claim by claim.
  - The loop's value is measurable: fix rate, and the disagreement trend
    before and after.

## Consequences
**Good:**
- The under-used signals become governed improvements.
- The proposal surface is small and reviewable.
- Every change is replayed before it is proposed and reversible after it
  ships.
- It reuses the config plane and its rollback (ADR 0010 / 0015).

**Bad / accepted:**
- A human is in the loop, so fixes arrive at human speed.
- The bounded set cannot express novel fixes; those become a spec change.
- Evidence thresholds (3 / 80 %) are PoC defaults.
- The reviewer signal waits for F2.
- EventBridge redelivery could double-count metrics. Mitigation: a conditional
  first write per `(claim, revision, stage)` gates emission (clinic v2 C9).

**Losers:**
- (a) Auto-apply: integrity. A self-tuning gate upstream of approval is the
  failure the plane exists to prevent.
- (c) Reports only: no structured, replayable, one-click-deployable change.
- (i) FM-written rules: unbounded change surface, non-reproducible.
- Code constants: every fix needs a deploy.
- A JSON object in S3: no rollout safety.

## Compliance
Offline fitness:
- **Proposal type set:** a free-form or destructive change cannot be
  represented (typed enum + schema test, as `remediation.py:27` does for v1).
- **Seeded corpus:** exactly one `set_date_order{partner, DMY}` proposal, with
  a replay fix rate of 100 % on its supporting claims (spec AC-Z9).
- **No FM client** reachable from `proposals.py` (AST rule).
- Feedback records store names only as a boolean match.
- A 412 on the first-write key suppresses a duplicate metric.

`[gate]`: the smoke's second batch (resubmission after the human applies the
proposal) clears the seeded date mismatches.

## Amendments ratified 2026-09-23 (risk storm, `../risk/risk-storm-v2-data-prep.md` §5)
- **M5** revision and replay governance: resubmission of a decided claim → human review only (unless a DQ-owner-tagged proposal re-run); replay over the whole channel/partner scope reporting fixed/broken/unchanged (any break blocks); scope keyed by partner id; the measuring prompt hides the intake record; degraded results excluded.

Detailed EARS criteria land in the spec revision (R10).

## Amendment 2026-09-23 — every resubmission goes to review; no exception (LLD Q8-b)
Found at the LLD (Wave A review): M5's rule had two holes.
- **A race.** "Resubmission of a *decided* claim" misses a revision that is
  dispatched but not yet recorded, or r2 arriving before r1. Both revisions
  could auto-approve.
- **A forgeable exception.** "Unless a DQ-owner-tagged proposal re-run"
  trusted a CSV column that the upstream writes.

We now:
- write a create-only **revision marker**
  (`processed/claims/<claim_id>/r<rev>/intake.json`) at the row gate, before
  any per-claim work (`../design/lld-v2-data-prep.md` REC-11);
- raise blocking `resubmission_review` whenever a marker exists for **any
  other** revision of the claim, earlier or later, decided or in flight
  (REC-12);
- honour **no exception**. `rerun_proposal_id` is kept for lineage only.

- *Why this over the alternatives:* a verified exception (the raw row
  unchanged, the claim in the accepted proposal's `replay.fixed`, and the
  batch on that proposal's deployed label) would widen what can auto-approve
  (flagged, criterion 5) and adds machinery. The first draft had the race.
- *Trade-off accepted:* every data-quality re-run of a claim lands in review.
  The loop's effect is still visible: the re-run clears the fixed flags, so
  the `[gate]` check above ("the smoke's second batch … clears the seeded
  date mismatches") still holds.

Approval criteria: not flagged (it narrows what can auto-approve).
Approved by / date: Rajnish Khatri / 2026-09-23 ("Q8-b")

## Notes
Author: arch-decide (v2 HLD, provisional batch A2-a)
Approved by / date: Rajnish Khatri / 2026-09-23 ("ratify as recommended")
Superseded date:
Last modified: 2026-09-23 / Q8-b amendment (LLD)
