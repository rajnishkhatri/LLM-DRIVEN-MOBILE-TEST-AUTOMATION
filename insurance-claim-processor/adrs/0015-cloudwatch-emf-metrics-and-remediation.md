# ADR 0015. Emit CloudWatch metrics via EMF and remediate via reversible flags

## Status
Accepted

## Context
CloudWatch is used only for Step Functions execution-history logs today
(design §5, ADR 0009). Best practice #7 asks for custom metrics + alarms to
detect model-performance degradation and trigger automated remediation. These
metrics are also the **prerequisite** the resilience clinic named for the
breaker (ADR 0012) and the comparison signal for A/B (ADR 0010). Two mechanism
choices: how metrics are emitted, and what remediation is allowed to do.

Emit alternatives: (a) `cloudwatch:PutMetricData` API calls — an extra
synchronous call per metric + a new IAM action; (b) **EMF** (Embedded Metric
Format) — structured JSON in the existing Lambda logs, extracted by CloudWatch
into metrics, no extra API and no IAM beyond Logs. Remediation alternatives:
(a) bounded reversible actions (flip an AppConfig flag / roll back an AppConfig
deployment); (b) broad actions (auto-scale, redeploy, delete) — rejected as
unsafe to automate on a model-quality signal.

## Decision
We will emit custom metrics via **EMF** through the existing safe logger, define
CloudWatch alarms on the model-health signals, and wire alarms to a remediation
Lambda that takes only **bounded, reversible** actions.

- Metrics: per-model latency, error rate by code (throttle/4xx/timeout/invalid),
  guardrail-intervention rate, ungrounded rate, HITL rate, ensemble
  disagreement, degradation-tier count, breaker transitions, `$/claim`.
- EMF passes through the redacting logger (ADR 0008 / AC-H1) — no raw PII beside
  a metric.
- Alarms → SNS → remediation Lambda flips an AppConfig flag (open breaker, switch
  to fallback model, disable ensemble) or triggers an AppConfig deployment
  rollback. No destructive or scaling action is automated.
- Every remediation (alarm → action) is itself emitted for audit.

Business justification: EMF gives the metrics at ~zero marginal cost and no new
IAM; reversible flag-based remediation lets the system self-protect during a
model regression while keeping every automated change auditable and one flag
away from manual override.

## Consequences
Good: the metric plane that unblocks the breaker (ADR 0012) and A/B (ADR 0010);
cheapest emit path, least IAM (Logs only); remediation is reversible and
auditable; percentile metrics feed alarm thresholds tuned from real p99/p99.9
(clinic §2). Bad: EMF schema discipline to keep (a malformed EMF line is a lost
metric, not an error); alarm tuning is ongoing; the remediation Lambda is a new
privileged actor — least-privilege: AppConfig write on the specific application
only (ADR 0009 style). Rejected `PutMetricData` would have cost an API call +
IAM per metric; broad remediation would automate actions too risky to trigger on
a noisy quality signal.

## Compliance
Fitness (offline): metric-emit is a pure function producing EMF-shaped JSON,
asserted by unit test; the emitter routes through the safe logger and a
PII-bearing metric context produces no raw SSN/PAN (AC-Q2, ties AC-H1); the
remediation decision (alarm state → action) is a pure, unit-tested mapping to a
bounded action set, and a destructive action is not representable (AC-Q4).
`[infra]`: alarms + SNS + remediation wiring recorded in `DEPLOY.md` and reviewed
(AC-Q3, Q4). `[gate]`: a live alarm drives a real AppConfig flag flip.

## Notes
Author: sdd-spec (model-resilience increment)
Approved by / date: Rajnish Khatri / 2026-09-21
Superseded date:
Last modified: 2026-09-21 / new
