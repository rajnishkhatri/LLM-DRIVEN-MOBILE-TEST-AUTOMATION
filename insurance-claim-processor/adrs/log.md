# ADR log — insurance claim document processor

Append-only. Newest last. Index: [`index.md`](index.md).

- (LLD) ADRs **0001–0009** filed as **Proposed** across the assess → design →
  decide → validate pass. 0004 amends 0003 (Step Functions reopened by the
  hard audit requirement + the HITL durable wait).
- 2026-09-21 — **Model-resilience increment.** ADRs **0010–0015** filed as
  **Proposed** (sdd-spec Stages 2–4; plan/tasks behind the human gate):
  - 0010 AppConfig config + feature-flag plane (best practices #1, #3).
  - 0011 Bedrock-family foundation-model adapter (#2).
  - 0012 measured circuit breaker — **amends** the resilience-clinic C1
    deferral (#4).
  - 0013 flag-gated extraction ensembling — **reverses (bounded)** the
    capability-brief §4 cascade-only scope (#5).
  - 0014 graceful-degradation tier ladder — **extends** ADR 0006 + C11 (#6).
  - 0015 CloudWatch EMF metrics + reversible remediation (#7); the metric
    plane 0012 and 0010's A/B depend on.
  Spec: [`../specs/claim-processor-model-resilience.spec.md`](../specs/claim-processor-model-resilience.spec.md).
- 2026-09-23 — **v2 data-preparation increment.** ADR **0016** filed as
  **Proposed** (compact sdd-spec per C7-a: brainstorm + spec + plan + tasks in
  one file). Separate intake state machine (Glue DQ batch/row gates,
  Comprehend, Textract Queries, Transcribe w/ PII redaction, loss-run
  summaries) → per-claim bundle → unchanged v1 workflow; human-approved
  feedback proposals via a second AppConfig profile. Extends 0004, 0010, 0015.
  Spec: [`../specs/claim-processor-data-prep.spec.md`](../specs/claim-processor-data-prep.spec.md).
- 2026-09-23 — **v2 HLD pass (arch-* + aws-ai-* + sdp-*, provisional batch
  A2-a).** ADR **0016 revised** (plane = second orchestrated workflow inside
  the existing quantum, pre-cut seam — was implying a separate quantum) and
  **0017–0022 filed as Proposed**. Hand-off accounting:
  *Written* — plane placement (0016), data topology (0017), service set
  (0018), DQ engine (0019), PII point (0020), formatting contract (0021),
  feedback loop (0022). *Merged* — communication + not-an-agent + one retry
  layer → 0016; ingestion contract + batch lock/takeover → 0017; document
  path + transcription tier + sentiment bias guard → 0018; SD-1 rule catalog
  + no-crawler → 0019; four-layer PII + IAM separation → 0020; adjuster
  dialog (SD-3) + H1 image cap → 0021. *Deferred* — upload API/SFTP (unlock:
  partner onboarding), raw-media retention (unlock: retention policy), Athena
  over quality/ (unlock: quarantine volume), Glue-DQ fallback gate (unlock:
  batch SLO), v1 retry amplification 5×5 (routed to v1 re-entry; unlock:
  Bedrock throttle-vs-retry metric). *Not ADR-significant* — SD-2 module
  layout (spec construction detail). First-use **approval-criteria** duty
  QUEUED (no `approval-criteria.md` exists) — see the HLD ratification
  checklist.
- 2026-09-23 — **Ratified as recommended** (Rajnish Khatri): ADRs **0016–0022
  Accepted** with the risk-storm amendments (M1–M10, M12–M18) recorded per ADR;
  M11 routed to v1 re-entry. **Still open:** R7q (approval criteria — first-use
  duty) and R8c (account-level AI-services opt-out, M7). **R0 done first:** live
  v1 defects D0-a (Catch without ResultPath ×6) and D0-b (summary Converse
  without guardrailConfig, AC-A5) fixed test-first and redeployed — see
  `../build/DEPLOY-LEDGER.md` "Hotfix R0".
- 2026-09-23 — **F14 fixed (option F14-a, owner-approved):** ADR 0008 amended.
  With a guardrail, only claim-derived text is guarded input (`guardContent`);
  our instructions and policy excerpts are not. v1 AC-A5a is added. Deployed:
  smoke #3 auto-approved, and an injected claim is still blocked. See
  `../build/DEPLOY-LEDGER.md` "Fix F14". Carrying the rule into v2 (the ADR 0021
  formatting contract) is open HLD item **H-F14**.
- 2026-09-23 — **Sequence corrected by the owner:** finalize the HLD, then the
  LLD, then the spec (the implementation plan). The early R10 spec revision was
  stopped with no changes. **Deploys are manual** and owner-run, as in v1. R0
  and F14 had been deployed by the agent. Stale "pending your approval" text
  in the Accepted ADRs 0020 and 0021 was corrected.
- 2026-09-23 — **Owner decisions:**
  - **R7q-a:** approval criteria adopted, in `approval-criteria.md`. There are
    five triggers. Applied retroactively, they flag 0001, 0004–0010, 0015 and
    0016–0022 for the go-live review.
  - **R8c-a:** opt out of all AI services (ADR 0020 M7). The owner performs it;
    ledger "Stage A".
  - **H-F14-a:** input tagging in the v2 formatting contract; images are plain
    blocks (ADR 0021 amendment).
  - **D-a:** keep the agent-deployed live state.
  - A consistency pass then folds the ratified amendments into the HLD
    artifacts (`../design/hld-v2-fold-map.md`).

- 2026-09-23 — **LLD Wave A, checkpoint 1** (`../design/lld-v2-data-prep.md`
  Appendix A.1). Three owner decisions amend Accepted ADRs:
  - **0021, Q1-a (flagged, criterion 5):** extraction sees evidence only; for
    a bundle key the decision uses the canonical intake values of the three
    M1 fields; two or more FM-absent → `bundle:fm_evidence_missing`. Approved
    on its own ("Q1-a approved"; tightened diff: "Q1 tightened ok").
  - **0022, Q8-b (not flagged):** a create-only revision marker; any other
    revision of the claim → `resubmission_review`; no re-run exception.
  - **0019, Q10-a (not flagged):** any failed batch rule, a low score, or a
    systemic row warning quarantines the whole batch.
  - Also decided in the LLD, with no ADR change: Q2–Q7 and Q9 "a".
- 2026-09-24 — **LLD Waves B and C written** (`../design/lld-v2-data-prep.md`
  §3–§11). One ADR amendment is **Proposed**, not Accepted: **0020**, the
  intake-plane IAM and PII detail (five v2 identities incl. the new
  `claim-processor-dq-owner`, two resource policies, L4, v1 narrowing, the
  Layer 2 type lists). Flagged (1, 2); it waits for the owner's own approval
  at checkpoint 2 (LLD Appendix B). The governance table gained G39–G49.
- 2026-09-24 — **LLD checkpoint 2 answered, except the IAM diff**
  (`../design/lld-v2-data-prep.md` Appendix B). The owner replied "B6-6-a,
  B4-5-a, B3.1-a, B4-1-a, B4-2-a, B4-3-a, B5-1-a, C10-1-a, C10-2-a, defaults
  ok".
  - **0020, approved in part (flagged 1, 2).** B6-6-a (`ask` runs as v1's
    `operator` role, which v2 now creates) and B4-5-a (transcript
    encryption) were each approved on their own.
  - **The IAM diff is held.** The two independent reviews of Waves B and C
    changed it: two unused intake grants removed, one list prefix added, and
    three reads designed away. The owner approves the corrected diff on its
    own.
  - Also decided in the LLD, with no ADR change: B3.1-a (10,800 s, Map
    concurrency 4), B4-1-a, B4-2-a, B4-3-a, B5-1-a, C10-1-a (`say`-rendered
    calls), C10-2-a (51-row batch B0003), and the twelve defaults (B6-1 = b:
    no machine logging).
- 2026-09-24 — **ADR 0020's LLD amendment Accepted; LLD checkpoint 2
  closed.** The owner approved the corrected IAM diff on its own ("IAM ok";
  LLD §6.13, Appendix C) and accepted the reviews' six new defaults ("B.5
  ok": B4-6 – B4-10, B7-5; no ADR change). The two independent reviews of
  LLD Waves B and C (70 findings) are folded in; F15 was rejected after the
  AWS docs were re-read. Next: the owner's LLD sign-off, then the spec
  revision (sdd-spec; `../design/spec-v2-handover.md`).
- 2026-09-24 — **LLD FINAL.** The owner signed off
  `../design/lld-v2-data-prep.md` ("LLD signed off"). Next: the spec
  revision with sdd-spec, from `../design/spec-v2-handover.md`.
