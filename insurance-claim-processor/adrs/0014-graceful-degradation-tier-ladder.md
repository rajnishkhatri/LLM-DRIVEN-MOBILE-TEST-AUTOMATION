# ADR 0014. Degrade through a model-tier ladder ending at human review

## Status
Accepted — **extends** ADR 0006 (document understanding) and the C11
graceful-degradation card (`../risk/resilience-clinic.md`)

## Context
C11 today is RAG-only: if policy retrieve is down, the summary is flagged
`ungrounded` but extraction still records (`UngroundedFallback` in
`../build/sfn/asl.json`). There is no fallback when the *model itself* is
unavailable — a breaker-open (ADR 0012) or exhausted retries currently fails the
execution. Best practice #6 asks for graceful degradation to more basic models
or rule-based systems so core functionality survives. Integrity is the driving
characteristic (capability-brief): a degraded result must never be mistaken for
a confident one.

Alternatives: (a) fail the claim when the advanced FM is down — rejected (loses
"core function stays up"); (b) auto-approve a cheaper model's output to keep
throughput — rejected (integrity: cheaper/rule-based output is lower
confidence); (c) a **tiered ladder** advanced FM → basic FM → rule-based →
human review, where any sub-advanced tier is recorded and always routes to
review.

## Decision
We will add a graceful-degradation ladder for the FM-dependent steps: advanced
FM → basic/cheaper FM → deterministic rule-based extractor → human review, with
the tier list configured in AppConfig (ADR 0010).

- A rule-based extractor produces the five-field schema shape from regex/keyword
  patterns when no FM is available, so intake continues.
- Any result produced **below** the advanced-FM tier is stamped
  `degradation_tier` and routes to **human review** — degraded output never
  auto-approves (integrity, AC-F3).
- Degradation applies only to understand/extract and summarize; S3 stays a hard
  dependency and the summary MAY be omitted/ungrounded (C11) rather than
  fabricated.
- The active tier + trigger (`breaker | exhausted_retry | config`) are recorded.

Business justification: during a model outage, claims keep being *received and
extracted* (durable core function) and queue for human review instead of
erroring — a review backlog is a recoverable cost; a dropped claim is not.

## Consequences
Good: core intake survives a full FM outage; integrity preserved (degraded ⇒
review, never auto-approve); tiers are config, not code (ADR 0010). Bad: a
rule-based extractor to build and keep honest (it is a floor, not a competitor
to the FM); more human-review volume during degradation (expected and bounded);
the ladder composes with the breaker and ensemble fallback — ordering matters
and is specified in the plan. Extends rather than replaces C11: RAG degradation
and model degradation now both exist, recorded distinctly.

## Compliance
Fitness (offline): with the advanced FM injected as unavailable, the pipeline
walks to the next tier and finally to the rule-based extractor, which yields a
schema-valid five-field result (AC-P1, P2); every sub-advanced result is
`degradation_tier`-stamped and routes to human_review, never auto_approve
(AC-P3, ties AC-R3); S3 stays hard and the summary may be ungrounded, not
fabricated (AC-P4); tier + trigger recorded (AC-P5).

## Notes
Author: sdd-spec (model-resilience increment)
Approved by / date: Rajnish Khatri / 2026-09-21
Superseded date:
Last modified: 2026-09-21 / extends ADR 0006 + C11
