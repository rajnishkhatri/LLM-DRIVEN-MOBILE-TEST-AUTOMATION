# ADR 0010. Externalize model selection and feature flags to AWS AppConfig

## Status
Accepted

## Context
Model ids, the escalation threshold, and force-review flags are read once from
environment variables at Lambda cold start (`EscalationPolicy.from_env`,
`../build/claim_processor/config.py`). Changing a model — for a deprecation, a
price change, or a rollback after a bad release — therefore needs a config
deploy and a cold start. Best practices #1 and #3 ask for runtime
model-selection changes and feature-flagged rollout / A-B / rollback with no
deployment.

Alternatives: (a) keep env vars only — no runtime change, rejected by the ask;
(b) SSM Parameter Store + a hand-rolled poll — works but no typed feature flags,
no deployment strategy, no built-in alarm rollback; (c) a home-grown flags table
in DynamoDB — rebuilds AppConfig; (d) **AWS AppConfig** freeform config + feature
flags with deployment strategies and alarm-based auto-rollback.

## Decision
We will externalize model-selection parameters and feature flags to **AWS
AppConfig**, read at runtime through a `ConfigProvider` seam, with environment
variables and dataclass defaults kept as the **bootstrap fallback**.

- `ConfigProvider` wraps the `appconfigdata` client (`start_configuration_session`
  + `get_latest_configuration`), caches last-known-good, and re-polls on a
  bounded TTL. The client is **injected** (Stubber offline), like every other
  AWS client in this kata.
- Freeform config carries model ids, `amount_threshold`, `force_review_flags`,
  ensemble membership, and degradation tiers. Feature flags carry candidate
  rollout %, A/B enablement, ensemble on/off, and kill switches.
- On fetch failure or a malformed value, the provider returns last-known-good,
  then env/defaults — a claim never fails because config is unreachable.
- The resolved config is recorded on each result (`config_snapshot`).

Business justification: a model deprecation is a scheduled `ValidationException`
(capability-brief §5) — a runtime swap avoids an emergency deploy; feature flags
cut time-to-rollback of a bad model from a deploy cycle to one poll interval.

## Consequences
Good: model changes and rollbacks without deployment; typed flags enable #3; the
alarm-backed deployment strategy (ADR 0015) gives automatic rollback; the env
fallback keeps the offline suite and cold-start path working. Bad: a new managed
dependency and a config schema to version; one poll interval of staleness
(bounded; acceptable for back-office claims); config becomes a control surface
that itself needs least-privilege + audit (`config_snapshot`). Rejected
SSM/DynamoDB would have saved the new service but cost us the flag model,
deployment strategies, and alarm rollback we specifically need.

## Compliance
Fitness (offline): a Stubbed AppConfig session drives model selection; killing
the Stubber falls back to env then defaults (AC-K1); a malformed value is
rejected and last-known-good retained (AC-K4); every result carries
`config_snapshot` (AC-K5); no new pip dependency (AC-R1). `[gate]`: a live
AppConfig value change is adopted within one poll interval with no deploy
(AC-K3). Governance: config/flag changes ship via an AppConfig deployment
strategy with a bake alarm (ADR 0015 / AC-M4).

## Notes
Author: sdd-spec (model-resilience increment)
Approved by / date: Rajnish Khatri / 2026-09-21
Superseded date:
Last modified: 2026-09-21 / new
