# Plan — claim processor model resilience

**Stage:** sdd-spec (Plan). **Status:** APPROVED 2026-09-21 — in sdd-implement.
**Spec:** `../specs/claim-processor-model-resilience.spec.md` (Wave 3, additive;
the real-AWS spec stays frozen). **ADRs:** **0010–0015** (raised by this plan,
filed Proposed). **Constitution:** `.cursor/rules/architecture-principles.mdc`
(SOLID, DI, testability, coupling/cohesion, trade-off surfacing).

## Architecture stance (simplest thing — A1)

Keep the modular-monolith core (`invoker`/`validator`/`rag`/`prompts`/`store`/
`routing`/`review`/`pipeline`) and the Step Functions topology **unchanged in
responsibility**; add model resilience as **thin, injected, pure-where-possible
seams** around it:

- **Config becomes runtime, not import-time.** A `ConfigProvider` reads AppConfig
  through an injected `appconfigdata` client with a last-known-good cache and the
  existing `EscalationPolicy` env/defaults as bootstrap fallback. No module
  imports a client at load (DI preserved).
- **Models sit behind one adapter.** `ModelAdapter` (Bedrock families only)
  normalizes request/response + a typed call outcome; ensemble, degradation,
  breaker, and metrics compose over it and never see a raw Bedrock response.
- **The new behaviors are pure functions + small injected classes** — flag
  evaluation, the breaker decision, the ensemble combine, the degradation ladder,
  the EMF emitter, and the remediation mapping are all unit-testable offline with
  no AWS call.
- **The breaker reuses the metric, not a new datastore.** Its trip signal is the
  CloudWatch metric (ADR 0015) surfaced as an AppConfig flag (ADR 0010) — no
  DynamoDB, honoring the resilience-clinic "confirm the metric first" rule.

**Two new abstractions (G1), each justified:**

- `ModelAdapter` (ADR 0011) — *buys* uniform multi-model composition + a single
  outcome vocabulary for ensemble/degradation/breaker/metrics. *Simpler thing
  rejected:* branch on model family in the pipeline (ensembling would multiply
  those branches; violates OCP/SRP).
- `ConfigProvider` (ADR 0010) — *buys* runtime model/flag changes with no
  deploy + a Stubber-injectable seam. *Simpler thing rejected:* read env at
  import (cannot change at runtime — the whole point of #1/#3).

Everything else (breaker, ensemble, degrade, metrics, remediation) is a
function/small class, **not** a framework — deliberately below the ADR bar.

## ADR triggers (raised by this plan)

| ADR | Decision | Kind | ⚠️ |
|---|---|---|---|
| 0010 | AppConfig config + flag plane | new | |
| 0011 | Bedrock-family FM adapter | new (G1) | |
| 0012 | Measured circuit breaker | **amends** clinic C1 deferral | ⚠️ breaker-state mechanism — confirm at gate |
| 0013 | Flag-gated extraction ensembling | **reverses (bounded)** capability-brief §4 | ⚠️ reverses a documented decision |
| 0014 | Graceful-degradation ladder | **extends** ADR 0006 + C11 | |
| 0015 | CloudWatch EMF + reversible remediation | new | |

## File-level touchpoints

**New (`build/claim_processor/`):**

| File | Purpose | AC |
|---|---|---|
| `config_provider.py` | `ConfigProvider` over injected `appconfigdata`; last-known-good cache; env/default fallback; malformed-value rejection | K1,K2,K4 |
| `adapter.py` | `ModelAdapter` iface + `BedrockConverseAdapter` (Claude/Nova); `AdapterError`; `CallOutcome` enum + `AdapterResult` | L1–L5 |
| `flags.py` | feature-flag eval: deterministic `claim_key` assignment, safe defaults, kill-switch | M1,M2,M5 |
| `breaker.py` | **pure** breaker decision over injected signal/flag; open/half-open/closed | N1,N3,N4,N5 |
| `ensemble.py` | field-level majority + `agreement`; quorum fallback | O1,O2,O3,O5 |
| `degrade.py` | tier-ladder walker + `RuleBasedExtractor` (regex/keyword 5-field) | P1–P5 |
| `metrics.py` | EMF emitter **through `logging_safe`**; metric vocabulary; no `put_metric_data` | Q1,Q2 |
| `remediation.py` | **pure** alarm-state → bounded-action mapping (destructive not representable) | Q4,Q5 |

**Change (existing):**

| File | Change | AC |
|---|---|---|
| `models.py` | extend `ProcessingResult`: `config_snapshot`, `model_variant`, `ensemble`, `degradation_tier`, `breaker_state`, `remediation` (all optional/defaulted) | R4,K5,M3,N5,O4,P5 |
| `config.py` | `EscalationPolicy` gains `ensemble_models`, `degradation_tiers`, flag fields; `from_env` stays bootstrap | K2,K3 |
| `invoker.py` | becomes the Claude/Nova impl behind `ModelAdapter`; return normalized outcome (logic preserved) | L2,L4 |
| `pipeline.py` | extract via adapter + ensemble(if flag) + degradation ladder; A/B variant; record new fields; emit metrics; C9 unchanged | K5,L,M2,M3,O,P,Q1,R4 |
| `routing.py` | predicate signals: degraded tier / ensemble split / rejected config / breaker-open → `human_review` (never auto) | R3,O1,P3,K4 |
| `understand.py` | tier swap on degradation; image blocks via adapter | L3,P1 |
| `sfn/asl.json` | add `BreakerCheck` `Choice` before model steps → degraded path; keep Retry/Catch/`waitForTaskToken` | N2,N4 |
| `handler.py` | thin adapters for breaker Choice + new step I/O | N2 |
| `iam/*.json` | step-lambda `appconfigdata` read; **new** least-priv remediation role (AppConfig write on the app only); **no** `PutMetricData` (EMF via Logs) | Q1,least-priv |
| `DEPLOY.md` *(also prior T-15)* | AppConfig app/env/profile + deployment strategy w/ bake alarm; CloudWatch alarms; SNS → remediation Lambda | M4,Q3,Q4 |
| `tests/` | new suites per module (all `[off]`) | all |
| `design/solution-design.md` | add **§8** model-resilience addendum linking ADRs 0010–0015 | traceability |

## Migration steps (Wave 3, in order)

**3a — foundation (unblocks the rest):** `ConfigProvider` (K) · `ModelAdapter`
+ `invoker` refit (L) · `ProcessingResult` fields (R4) · `EscalationPolicy`
extension (K). *No behavior change yet; seams in place.*

**3b — resilience behaviors (pure, unit-first):** `flags` (M) · `breaker`
decision (N off-layer) · `degrade` ladder + rule-based floor (P) · `ensemble`
combine (O) · `routing` integrity wiring (R3). *All offline-provable.*

**3c — orchestration + observability:** `pipeline` wiring (adapter/flags/
ensemble/degrade/metrics) · `metrics` EMF (Q) · `remediation` mapping (Q) ·
ASL `BreakerCheck` + degraded path + `handler` (N `[sfn]`).

**3d — infra + gate:** IAM deltas + policy-lint · `DEPLOY.md` (AppConfig
deployment strategy, alarms, SNS→remediation) `[infra]` · offline sweep green,
no new pip dep (R1) · gated real-AWS smoke (R2) · design §8 addendum.

## Constitution alignment

- **DI / testability:** `appconfigdata` and Bedrock clients stay injected; the
  breaker reads an injected signal, not a module global; offline suite stays the
  gate (AC-R1).
- **SRP / cohesion:** eight new single-purpose modules; no god-object; the
  `pipeline` orchestrates, it does not implement the combine/ladder/emit.
- **Coupling / DIP:** `ModelAdapter` and `ConfigProvider` invert model and
  config dependencies; callers depend on interfaces; `RetrieverProtocol`
  unchanged.
- **Trade-offs surfaced:** in ADRs 0010–0015 (two are amend/reverse with
  rejected alternatives spelled out); the plan adds none silently.

## Slop-reduction ownership (Runbook A1/A7/G1)

- **A1 — simplest thing:** breaker reuses the metric (no DynamoDB); EMF over
  `PutMetricData` (no API/IAM); adapter Bedrock-only (no cross-provider layer);
  ensemble extraction-only, flag-gated off by default.
- **A7 — spec before code:** every AC in the spec predates any module here.
- **G1 — new abstractions declared:** exactly two (`ModelAdapter`,
  `ConfigProvider`), each with its rejected simpler alternative above.

## Grounding / dependencies (for Analyze)

- Probe every touched path exists in `build/claim_processor/` (verified:
  config/invoker/models/pipeline/routing/understand/review/rag/store/
  logging_safe/handler; `sfn/asl.json`; `iam/*.json`).
- **No new pip dependency:** `appconfigdata` ships in botocore; EMF is
  structured logging; CloudWatch alarms / SNS / AppConfig deployment are
  deploy-time (`DEPLOY.md`), not a Python dep. Confirm no `moto`/`Pillow` added.
- New AWS APIs referenced (re-verify at build): `appconfigdata`
  `StartConfigurationSession` / `GetLatestConfiguration`; AppConfig deployment
  strategies + `StartDeployment`/`StopDeployment` (rollback); CloudWatch EMF +
  alarms; SNS; all valid.
- `[sfn]` `BreakerCheck` Choice needs SFN-Local for live assertion; step logic
  is still covered by offline unit tests.
- **Baseline (observed 2026-09-21):** offline suite **127 tests OK
  (skipped=1)** = the pre-implementation baseline. `check_gate` (skill-sync):
  `7 families, 0 drifted, 0 shadow -> exit 0` from repo root.

## Human plan gate

Approve the plan + ADRs 0010–0015, **or** name changes — especially the two
⚠️ items: the **breaker-state mechanism** (CloudWatch-alarm + AppConfig flag vs
a DynamoDB token-bucket) and the **ensembling reversal** (bounded to
extraction). On "yes" → **tasks are already drafted** in
[`claim-processor-model-resilience.tasks.md`](./claim-processor-model-resilience.tasks.md);
advance to Analyze sign-off, then **sdd-implement**.
