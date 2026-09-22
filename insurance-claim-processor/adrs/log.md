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
