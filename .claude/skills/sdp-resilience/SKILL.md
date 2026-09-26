---
name: sdp-resilience
type: skill
description: >-
  System-design clinic for resilience & availability tactics — the intra-service
  reliability patterns arch-* does not cover (part of the sdp-* family). Covers
  circuit breakers, retries + backoff + jitter, timeouts / deadlines / budgets,
  bulkheads, idempotency, load shedding, and graceful degradation. Use this when
  someone asks "should I add a circuit breaker here?", "why are my retries making
  the outage worse?", "what timeout should I set?", "how do I stop one slow
  dependency taking the whole service down?", "we melted under load — what do I
  add?", or hands you code with a missing/mis-set timeout, retry, or breaker — even
  if they never say "resilience" or "pattern". It surfaces the trade-off and asks
  for the confirming metric BEFORE recommending, never a bare pattern-drop. Do NOT
  use for architecture STYLE selection — monolith vs microservices, how many quanta,
  sync-vs-async between services — that is arch-style. Not the SDD lifecycle (sdd-*).
---

# Resilience & Availability Clinic (`sdp-resilience`)

> **Reference.** Cards live in `references/<Pattern>.md`, each addressed by its
> catalog id (C1, C2, …) and self-contained. Every card obeys the constitution's
> pattern contract (`.cursor/rules/architecture-principles.mdc`): definition ·
> motivation · example/diagram · **trade-offs on every decision** · cited sources.
> Routing and the `arch-style` handoff are governed by the `sdp-lifecycle` router.

## When this fires

A described availability/overload **symptom** (primary), a **named** pattern
("explain bulkheads"), or **code/a diff** exhibiting a missing or mis-set pattern.
For a style/quantum/topology question, stop and hand off to `arch-style`.

## Agent work

Run these as one loop — do not skip to step 3.

1. **Diagnose the symptom → candidate patterns.** Map what is failing to what
   addresses it. Cascading failure / a sick dependency dragging callers down →
   CircuitBreaker (C1). Retry storms, amplification → RetryBackoff (C2). Unbounded
   waits, threads parked on a slow call → TimeoutsDeadlines (C7). One dependency
   consuming all capacity → Bulkhead (C8). Duplicate/retried side effects →
   Idempotency (C9). Demand over capacity → LoadShedding (C10). Partial-failure
   UX → GracefulDegradation (C11).
2. **Confirm the metric exists — before tuning anything.** The class failure here
   is dropping a pattern in without the signal that would tell you it is needed or
   working. Ask for the raw error rate, the p99, the saturation metric first. A
   circuit breaker on a service whose "failures" are actually a slow dependency
   just converts a slowdown into an outage. Name the trade-off out loud.
3. **Select the combination.** These patterns are a control loop, not a menu: a
   breaker needs a timeout to define "failure fast"; a retry needs a budget and an
   idempotent target; load shedding needs a priority. Point at each relevant card.
4. **Apply the knobs.** Use the card's *Configuration & verified defaults* as a
   starting point, then calibrate to the numbers from step 2 (the card's *Worked
   calibration* shows the arithmetic). Defaults are a start, not a policy.
5. **Verify.** Use the card's fitness recipe (a metric → an assertion) so the
   change is checkable. State how you would know it regressed.

## Cards

**Owned (this skill):**

| Card | id | Status |
|---|---|---|
| [Circuit breaker](references/CircuitBreaker.md) | C1 | built |
| [Retry & backoff](references/RetryBackoff.md) | C2 | built |
| [Timeouts & deadlines](references/TimeoutsDeadlines.md) | C7 | built |
| [Bulkhead](references/Bulkhead.md) | C8 | built |
| [Idempotency](references/Idempotency.md) | C9 | built |
| [Load shedding](references/LoadShedding.md) | C10 | built |
| [Graceful degradation](references/GracefulDegradation.md) | C11 | built |

**Cross-link — referenced, not owned here:** FailoverHealth (C3), CachingStrategies
(B3 → `sdp-data`), OutboxCdc (B7 → `sdp-data`). Name them when relevant and point
onward rather than absorbing them.

## Human gate

Recommend with the trade-off and the confirming metric on the table; the operator
owns the cost and makes the call. Do not silently apply knobs to their code.

## Constraints

- **Trade-offs before the recommendation.** Never a bare pattern-drop (constitution).
- **Style questions → `arch-style`.** Do not run its four determinations; cite
  `style-selection.md` as FACT if a style fact is needed.
- **Cite the card, not memory — and name it by id.** Defaults, failure modes, and
  sources come from the cards; each stands alone and carries its sources. Say which
  card you used, in the answer (e.g. "CircuitBreaker C1", "TimeoutsDeadlines C7"):
  the operator can then open it, and the consumer skills (arch-risk, arch-validate,
  sdd-spec) cite cards by id — card content without the card's name is not
  traceable.
