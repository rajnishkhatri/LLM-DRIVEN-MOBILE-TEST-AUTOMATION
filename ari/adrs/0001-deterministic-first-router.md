# ADR 0001. Route deterministically first; ask a model only on ambiguity

## Status
Accepted

## Context
Ari routes each turn to one of three capabilities (data / how-to / ticket),
plus out-of-scope refusal, with more streams expected. In treasury the binding
constraint is **error cost** (worksheet top-3: security, testability,
auditability; elevated 4th: fault tolerance) — and a router that is itself an
unbounded LLM call makes every reliability claim statistical-only while every
turn pays model latency and cost. Volume/SLO are `needs-input` in the kata.

Alternatives: (a) **LLM-classifier primary** (Agent Squad routes everything) —
simplest build, but each turn pays the classifier, reliability claims lose
their deterministic floor, and injection reaches the router on every turn;
rejected as primary, kept as fallback. (b) **Free tool-calling agent** — max
flexibility; opaque routing, hard to audit, widest injection surface; rejected
(the road-not-taken named in the brief). (c) **Hand rules only** — fully
deterministic but brittle on paraphrase; rejected as sole mechanism.
(d) **Chosen:** deterministic stage-0 with LLM fallback.

## Decision
- **Stage-0 deterministic:** normalized patterns + intent heuristics with a
  confidence score; the unambiguous share routes for ~zero tokens (prior art:
  claim-processor ADR 0018, deterministic-first / FM-last — pattern quarried,
  not imported).
- **Stage-1 fallback:** Agent Squad LLM classifier only below the stage-0
  threshold; below the *classifier's* confidence → clarify or ticket. Never
  guess.
- **One guarded-call wrapper at the port boundary** for every adapter call:
  timeout budget (C7), degradation ladder with the ticket stream as floor
  (C11), a single jittered retry on idempotent reads only (C2), idempotency
  key = conversation+turn id on the ticket write (C9). Circuit breaker (C1)
  deliberately deferred behind its CloudWatch signal (per-adapter error +
  slow-call rate); the wrapper is where it slots later — a one-place change.
- **Degraded data path is deterministic:** when the data call fails, the model
  does not answer the data question. Honest failure + ticket offer.
- **Topology** (from the worksheet's clusters): one quantum — hexagonal
  modular monolith; ports & adapters; dependencies point inward; SSE at the
  delivery edge, per-request auth.

## Consequences
Good: most turns are ordinary, testable software; latency/cost/reliability
claims become assertable; the fallback threshold is a dial (0→1 converts the
system to classifier-primary) — mechanism-level reversal is cheap, with the
full accounting in **Reversal** below. Bad: two routing paths
to keep coherent — misroute is a standing failure-taxonomy class with evals
per path; stage-0 rules need curation as streams grow.

## Reversal

**The signals that would tell us it isn't working:** fast-path precision
below the bar on the golden set; rising fast-path-misroute rate in
production; coverage too low to pay for rule upkeep; rule curation outpacing
stream onboarding.

**Reverse to (a) classifier-primary — cheap in mechanism, not free in
commitments.** Mechanism: raise the threshold past 1.0; stage-0 goes inert.
What does *not* reverse: the cost-per-conversation model (every turn now
pays the classifier), the TTFT p95 budget, and the injection posture
(routing becomes model-exposed on every turn). Those commitments were
derived from the fast-path hit rate and must be re-stated to stakeholders.
Sunk: the rules file and its curation process (small).

**Reverse to (b) free tool-calling agent — expensive; not a dial.** The
routing seam, rule-id provenance, per-path eval structure, and ADR 0003's
before-the-model entitlement staging all re-open. That is a new ADR
superseding this one, not a rollback.

**What survives either reversal:** the guarded wrapper (C7/C11/C2/C9), the
ports and adapters, the golden set, and the provenance tuple (minus rule
ids). The hexagon localized the bet: the router *policy* is the replaceable
part; the expensive artifacts around it are not at risk.

**The road back (this door swings both ways).** After reversing to (a),
stage-0 keeps running in **shadow** — deterministic, so ~zero latency/token
cost and no side effects; every shadow-vs-live disagreement feeds rule
curation. Re-promotion requires the golden set + downstream success signals
to pass the bar — *agreement with the incumbent classifier is not
correctness* — and rolls out as a **policy canary** on the threshold dial
(per-cohort ramp, misroute ceiling as stop condition). Formal A/B is
rejected for this question (logs answer it; rare-event metrics won't power
an experiment at our volume). Conditions of existence: a named owner on a
review cadence, and exit criteria both ways — promote at the bar, or retire
the shadow after N idle weeks.

## Compliance
Golden-set routing accuracy reported per path; fast-path hit-rate metric;
injected-timeout test green (degrade + ticket offer, conversation survives);
duplicate-injection test on the ticket write; architecture test: imports point
inward and a new-adapter change touches zero core files.

## Notes
Author: session pipeline (sdd-brainstorm → arch-characteristics → arch-decide)
Approved by / date: Rajnish Khatri / 2026-09-30 (incl. Reversal + road-back)
Last modified: 2026-09-29 / new
