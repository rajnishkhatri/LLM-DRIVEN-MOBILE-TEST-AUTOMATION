# Spec — claim processor model resilience (AppConfig + adapter + breaker + ensemble + degradation + observability)

**Stage:** sdd-spec (Stages 2–4). **Status:** APPROVED 2026-09-21 — in
sdd-implement (ADRs 0010–0015 Accepted). **New increment (Wave 3).** The prior spec
(`./claim-processor-real-aws.spec.md`) stays **FROZEN** — do not rewrite it;
this file is additive.
**Binding:** `.sdd` `[roots] claim-document-processor = insurance-claim-processor/`.
**Design:** `../design/solution-design.md` §1–§7 (+ a §8 addendum this plan
raises), ADRs **0010–0015** (this increment), and the decisions they amend:
`../risk/resilience-clinic.md` §3/§5 (C1 deferral) and
`../assess/capability-brief.md` §4 (cascade-only).
**Test gate:** offline `unittest` in `../build/` (no creds, `aws_profile`
`<none>`); real AWS behind `CLAIM_PROCESSOR_REAL_AWS=1` + a separate human gate.

**Verification tags:** `[off]` provable offline (Stubber/unit/grep);
`[gate]` requires the real-AWS gate; `[sfn]` proven at the state-machine layer
(Step Functions Local / deploy check); `[infra]` proven by the manual runbook /
deploy config review (AppConfig deployment strategy, CloudWatch alarms, SNS →
remediation wiring), not by unit tests.

## Why this increment

The PoC deliberately deferred two of these controls: the resilience clinic
named the **circuit breaker (C1)** "not applied until the metrics exist," and
the capability brief chose **cascade, not aggregation** for a 2–3 doc PoC.
This increment promotes the design to production-grade **model resilience**:
model choice becomes runtime configuration; providers sit behind an adapter;
new models roll out gradually / A-B / roll back; the system degrades instead
of failing when a model is down; and real CloudWatch metrics both feed the
breaker and drive bounded automated remediation. The two reversals are
recorded as **superseding ADRs** (0012, 0013), as ADR 0004 superseded 0003.

## Scope

**In:** (K) AppConfig configuration plane with env bootstrap fallback; (L) a
Bedrock-family foundation-model adapter; (M) feature-flag progressive delivery
(gradual rollout, A/B, kill-switch, alarm-backed rollback); (N) a Step
Functions circuit breaker driven by a measured signal; (O) multi-model
**extraction** ensembling, flag-gated; (P) a model-tier graceful-degradation
ladder ending at human review; (Q) CloudWatch custom metrics via EMF + alarms
+ bounded, reversible automated remediation; (R) offline-first + integrity
invariants preserved.

**Out:** cross-provider adapters beyond Bedrock (OpenAI / Anthropic-direct) —
adapter is Bedrock-family only (confirmed); CDK/IaC automation of AppConfig,
alarms, SNS (manual `DEPLOY.md` runbook only, as the prior increment);
ensembling the **summary**; auto-scaling or any destructive remediation;
provisioned throughput; a datastore-backed breaker (DynamoDB token-bucket) —
rejected in ADR 0012.

---

## K. Configuration plane — AWS AppConfig (best-practice #1)

- **AC-K1** `[off]` IF AppConfig is unreachable, or returns an empty/invalid
  document, THEN the system SHALL use the last-known-good cached config, and
  if none is cached, the env/default bootstrap (`EscalationPolicy` defaults) —
  a claim SHALL NEVER fail because config fetch failed. *(fail-safe; ADR-0010)*
- **AC-K2** `[off]` The system SHALL source model-selection parameters
  (extract/summary/understand model ids, `amount_threshold`,
  `force_review_flags`, ensemble membership, degradation tiers) through a
  `ConfigProvider` that reads AWS AppConfig at runtime `[gate]` and is
  Stubber-injectable offline `[off]`; env vars remain the **bootstrap
  fallback only**. *(ADR-0010; extends `config.py`)*
- **AC-K3** `[off]` WHEN a value changes in AppConfig, the running system
  SHALL adopt it within one polling interval WITHOUT a code deployment or
  restart; the poll/cache-TTL logic is unit-tested `[off]` and the live
  refresh is `[gate]`. *(ADR-0010; #1 runtime change)*
- **AC-K4** `[off]` IF an AppConfig value is malformed (non-numeric threshold,
  unknown model-id shape), THEN the system SHALL reject that value, retain the
  last-known-good, and emit a `config_rejected` metric — a bad config SHALL
  NOT widen auto-approve. *(integrity; ADR-0010 / ADR-0015)*
- **AC-K5** `[off]` The resolved configuration in force for a claim SHALL be
  recorded on the result as `config_snapshot` (model ids, flag states,
  ensemble set, tier). *(audit; ADR-0010; extends §7 contract)*

## L. Foundation-model adapter — Bedrock families (best-practice #2)

- **AC-L1** `[off]` IF a model family returns a response shape the adapter
  does not recognize, THEN the adapter SHALL raise a typed `AdapterError`
  (never a bare `KeyError`) and the caller SHALL route to degradation (P) —
  a malformed FM response SHALL NEVER become an extraction. *(ADR-0011)*
- **AC-L2** `[off]` The system SHALL invoke every foundation model through one
  `ModelAdapter` interface that normalizes the request (text+image content
  blocks, `inferenceConfig`, `guardrailConfig`) and the response (`text`,
  resolved `model_id`, `usage`, `stop_reason`, guardrail intervention) across
  Bedrock families (Claude, Nova), so pipeline / ensemble / degradation code
  is provider-shape-agnostic. *(ADR-0011; formalizes `invoker.py`)*
- **AC-L3** `[off]` WHERE a family needs family-specific shaping (Nova vs
  Claude image block, system-prompt placement, structured-output mode), the
  adapter SHALL encapsulate it; callers SHALL NOT branch on model family.
  *(ADR-0011)*
- **AC-L4** `[off]` The adapter SHALL preserve the frozen invariants: exactly
  one app-level call (no nested retry — C2), no legacy completions contract
  (A1), `guardrailConfig` passthrough (A5), resolved id recorded (A4).
  *(regression guard on ADR-0001 / 0008; ADR-0011)*
- **AC-L5** `[off]` The adapter SHALL return a normalized per-call outcome
  (`ok | throttled | timed_out | invalid | guardrail_intervened`) that the
  breaker (N) and metrics (Q) consume. *(ADR-0011 / 0012 / 0015)*

## M. Progressive delivery — feature flags (best-practice #3)

- **AC-M1** `[off]` IF a feature flag is absent or the flag source is
  unavailable, THEN the system SHALL apply the flag's **safe default**
  (candidate rollout = 0 %, ensemble = off, breaker = enabled, degradation =
  enabled) — flags fail to the conservative behavior. *(ADR-0010)*
- **AC-M2** `[off]` WHERE a rollout flag assigns a percentage to a candidate
  model, the system SHALL route that fraction using a **deterministic**
  assignment keyed on `claim_key`, so a re-run of the same key gets the same
  variant (C9 idempotency preserved). *(ADR-0010; #3 gradual rollout)*
- **AC-M3** `[off]` WHERE an A/B flag is enabled, the system SHALL record the
  assigned `model_variant` (`control|candidate` + resolved model id) on the
  result so outcomes are comparable in CloudWatch (Q). *(ADR-0010 / 0015; #3 A/B)*
- **AC-M4** `[infra]` The AppConfig deployment strategy for model/flag changes
  SHALL use a bake window bound to a CloudWatch alarm; IF the alarm fires
  during bake, THEN AppConfig SHALL auto-roll-back the deployment.
  *(ADR-0010 / 0015; #3 quick rollback)*
- **AC-M5** `[off]` A kill-switch flag SHALL force a specific model or the
  ensemble OFF for all claims within one polling interval, with no deployment.
  *(ADR-0010; #3 rollback)*

## N. Circuit breaker — Step Functions (best-practice #4)

- **AC-N1** `[off]` The breaker's "open" decision SHALL be driven by a
  **measured signal** (per-model error/timeout rate from Q), NOT by raw
  invocation count — a breaker SHALL NOT trip on slow successes.
  *(resilience-clinic C1 doctrine; ADR-0012 supersedes the C1 deferral)*
- **AC-N2** `[sfn]` WHILE a model's breaker is open, the workflow SHALL route
  new claims for that model to the fallback/degraded path (P) via a `Choice`
  on breaker state, WITHOUT invoking the failing model. *(ADR-0012)*
- **AC-N3** `[off]` The breaker state SHALL be read from **shared** state
  (a CloudWatch-alarm-backed AppConfig flag — recommended) so it is
  consistent across independent SFN executions; an in-process breaker
  (invisible across executions) SHALL NOT be used. *(ADR-0012; stateless-orchestration failure mode)*
- **AC-N4** `[sfn]` WHEN the signal recovers below the close threshold, the
  breaker SHALL half-open (probe a bounded number of claims) then close.
  *(ADR-0012)*
- **AC-N5** `[off]` Breaker `open|half_open|closed` transitions SHALL be
  recorded (metric + on-result `breaker_state`). *(audit; ADR-0012 / 0015)*

## O. Multi-model ensembling — extraction (best-practice #5)

- **AC-O1** `[off]` IF ensemble members disagree beyond the agreement
  threshold on a required field, THEN that field SHALL be marked low-confidence
  and the claim SHALL route to human review — a split vote SHALL NEVER
  auto-approve. *(integrity, extends AC-E1/F3; ADR-0013)*
- **AC-O2** `[off]` WHERE the ensemble flag is enabled, extraction SHALL invoke
  the N configured models through the adapter (L) and combine per-field by
  majority/agreement into one schema-valid result plus a per-field `agreement`
  score. *(ADR-0013; #5)*
- **AC-O3** `[off]` Ensembling SHALL apply to the **extraction** step only;
  summary generation SHALL remain single-model cascade (free text is not
  field-votable). *(ADR-0013 supersedes capability-brief §4 cascade-only, bounded)*
- **AC-O4** `[off]` Ensembling SHALL be OFF by default and enabled only by flag
  (M) because it multiplies token cost; the members and combine outcome SHALL
  be recorded (`ensemble: {members[], agreement}`). *(cost/audit; ADR-0013 / 0010)*
- **AC-O5** `[off]` IF fewer than the required quorum of members return a
  usable response (throttle/timeout/adapter-invalid), THEN the system SHALL
  fall back to the single primary model's result (or degradation P if that
  also fails) — it SHALL NEVER emit an empty ensemble. *(resilience; ADR-0013 / 0014)*

## P. Graceful degradation ladder (best-practice #6)

- **AC-P1** `[off]` IF the advanced FM is unavailable (breaker open — N, or
  retries exhausted), THEN the system SHALL degrade through the configured
  ladder in order: advanced FM → basic/cheaper FM → deterministic rule-based
  extractor → human review. *(ADR-0014; extends ADR-0006 / C11; #6)*
- **AC-P2** `[off]` A rule-based extractor SHALL produce the five-field schema
  shape from deterministic patterns (regex/keyword) when no FM is available,
  so core intake continues. *(ADR-0014; #6 rule-based floor)*
- **AC-P3** `[off]` Any result produced **below** the advanced-FM tier SHALL be
  marked `degradation_tier` and SHALL route to human review — a degraded
  extraction SHALL NEVER auto-approve. *(integrity, extends AC-F3; ADR-0014)*
- **AC-P4** `[off]` Degradation SHALL apply only to the FM-dependent steps
  (understand/extract, summarize); the S3 hard dependency and the HITL contract
  are unchanged, and a summary MAY be omitted/ungrounded (C11) rather than
  fabricated. *(bounds; ADR-0014)*
- **AC-P5** `[off]` The active tier and its trigger
  (`breaker|exhausted_retry|config`) SHALL be recorded on the result.
  *(audit; ADR-0014 / 0015)*

## Q. Observability + automated remediation (best-practice #7)

- **AC-Q1** `[off]` The system SHALL emit CloudWatch custom metrics via **EMF**
  (structured log — no `put_metric_data` API call, no IAM beyond CloudWatch
  Logs) covering at least: per-model latency, error rate by code
  (throttle/4xx/timeout/invalid), guardrail-intervention rate, ungrounded
  rate, HITL rate, ensemble-disagreement rate, degradation-tier count, breaker
  transitions, and `$/claim` (from `usage`). *(ADR-0015; #7)*
- **AC-Q2** `[off]` EMF output SHALL pass through the safe logger (AC-H1) so no
  raw PII is emitted alongside a metric. *(regression guard on AC-H1; ADR-0015)*
- **AC-Q3** `[infra]` CloudWatch alarms SHALL be defined for model-error-rate,
  latency-p99, and cost-per-claim breaching configured thresholds. *(ADR-0015; #7 alarms)*
- **AC-Q4** `[infra]` WHEN an alarm enters ALARM, THEN a remediation Lambda
  SHALL take a **bounded, reversible** action — flip an AppConfig flag (open
  breaker / switch to fallback model / disable ensemble) or trigger an
  AppConfig deployment roll-back — and SHALL NOT take any destructive or
  non-reversible action. *(ADR-0015 / 0012 / 0010; #7 automated remediation)*
- **AC-Q5** `[off]` Each remediation action (alarm → action taken) SHALL itself
  be emitted/recorded so automated config changes are auditable. *(ADR-0015)*

## R. Cross-cutting — offline-first + integrity + contract

- **AC-R1** `[off]` The offline suite SHALL pass with no AWS credentials and
  **no new pip dependency** beyond `boto3`/`botocore` (AppConfig Data API is in
  botocore; EMF is structured logging; both are Stubber/assert-provable).
  *(AC-J1 parity)*
- **AC-R2** `[gate]` All real-AWS behavior (AppConfig fetch, alarm→remediation,
  breaker-flag round-trip, live A/B) SHALL require `CLAIM_PROCESSOR_REAL_AWS=1`.
  *(AC-J2 parity)*
- **AC-R3** `[off]` The clean auto-approve predicate (AC-E1) SHALL remain the
  single approval gate: **no** path added by this increment — ensemble split
  (O1), degraded tier (P3), rejected config (K4), breaker-open (N2) — SHALL
  auto-approve; each routes to human review. *(integrity invariant; extends AC-F3)*
- **AC-R4** `[off]` The provenance tuple SHALL be extended with
  `config_snapshot`, `model_variant`, `ensemble`, `degradation_tier`,
  `breaker_state`, `remediation` — all optional/defaulted so pre-increment
  results still serialize. *(AC-F1 parity; extends `models.py`)*

---

## Clarify pass — RESOLVED (2026-09-21)

Framing confirmed by the human (id-labelled), plus recommended defaults for
the rest. **Items marked ⚠️ are the ones most worth a second look at the plan
gate.**

1. **Scope of this pass** = spec → plan → tasks, then STOP at the human gate
   (implementation is a separate sdd-implement). *(confirmed)*
2. **The two reversals** (breaker N, ensembling O) = production-tier with
   **superseding ADRs** (0012 supersedes the clinic C1 deferral; 0013
   supersedes capability-brief cascade-only). *(confirmed)*
3. **Adapter breadth** (L) = **Bedrock model families only** (Claude/Nova via
   Converse); cross-provider is out of scope. *(confirmed)*
4. **Config refresh mechanism** = AppConfig Data API
   (`start_configuration_session` + `get_latest_configuration`) behind a
   `ConfigProvider`, env/default bootstrap fallback, last-known-good cache.
   *(recommended default — no new pip dep, mirrors the injected-client DI pattern)*
5. ⚠️ **Breaker state mechanism** = CloudWatch composite alarm as the trip
   signal + an **AppConfig flag** the workflow reads (Choice on breaker
   state). Rejected: DynamoDB token-bucket (extra infra + hot-path writes),
   in-process breaker (blind across SFN executions). *(recommended — unifies
   #4+#7+#1; confirm at gate — it is the largest new architectural seam)*
6. **Ensemble target** = extraction only, field-level majority + agreement
   score, flag-gated, disagreement → HITL. Summary stays single-model.
   *(recommended default)*
7. **Degradation ladder** = advanced FM → basic FM → rule-based → HITL; any
   sub-advanced tier never auto-approves. *(recommended default)*
8. **Metrics mechanism** = EMF (no `put_metric_data`), through the safe
   logger. *(recommended default — cheapest, least IAM)*
9. **Remediation blast radius** = config-flag flips + AppConfig rollback only;
   never destructive/auto-scaling. *(recommended default — reversible, auditable)*

## Coverage → best practices

#1 AppConfig externalize → **K**. #2 adapter → **L**. #3 feature flags
(rollout/A-B/rollback) → **M**. #4 SFN circuit breaker → **N**. #5 ensembling
→ **O**. #6 graceful degradation → **P**. #7 CloudWatch metrics/alarms/
remediation → **Q**. Offline-first + integrity → **R** (threads through all).
