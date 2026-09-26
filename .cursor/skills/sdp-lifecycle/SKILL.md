---
name: sdp-lifecycle
type: skill
description: >-
  Router for the system-design tactical-patterns clinic (the sdp-* family): given
  a reliability or overload symptom, diagnose it, pick the right pattern(s), apply
  the knobs, and verify — the tactical loop arch-* does not cover. Routes to:
  sdp-resilience (circuit breakers, retries + backoff, timeouts/deadlines, bulkheads,
  idempotency, load shedding, graceful degradation) — the only category built today;
  sdp-messaging / sdp-data / sdp-traffic / sdp-coordination are reserved for later
  waves. Use this whenever someone describes an availability or overload symptom
  ("my p99 is climbing and taking the connection pool down", "retries are hammering
  a sick dependency", "one slow downstream is taking everything with it"), NAMES a
  tactical pattern ("should I add a circuit breaker?", "explain bulkheads"), or hands
  you code or a diff to check for a missing/mis-set pattern — even if they never say
  the word "pattern" or "resilience". Do NOT use for which architecture STYLE to pick
  — monolith vs microservices, how many quanta, sync-vs-async BETWEEN services — hand
  those to arch-style. Not the SDD lifecycle (sdd-*: spec / plan / tasks / implement).
---

# System-Design Patterns Clinic — Router (`sdp-lifecycle`)

> **Reference.** Every card obeys the constitution's pattern contract
> (`.cursor/rules/architecture-principles.mdc`: definition · motivation ·
> example/diagram · **trade-offs on every decision** · cited sources). Pattern
> cards live in each category skill's `references/<Pattern>.md`, addressed by a
> stable catalog id (e.g. `C1`). This family has no separate binding file — it
> reads the workspace constitution directly.

This is a **clinic**, not an encyclopedia. The job is to move an agent from a
symptom to a *calibrated, trade-off-aware* change — not to recite pattern
definitions. The four steps below are **sections of one reasoning loop**, not
separate skills.

## The clinic loop

1. **Diagnose** — turn the symptom into candidate patterns. Resist naming a
   pattern before you can name the failure it addresses.
2. **Select** — pick the *combination* (resilience patterns travel in packs: a
   breaker without a timeout is half a control loop). Point at the cards.
3. **Apply** — set the knobs from the card's Configuration section, with the
   card's defaults as a starting point, not a policy.
4. **Verify** — use the card's fitness recipe (a metric → an assertion) so the
   change is checkable, not hopeful.

## The map — categories → cards

| Category | Skill | Symptoms it owns | Cards |
|---|---|---|---|
| **Resilience / availability** | **`sdp-resilience`** *(built)* | cascading failure, retry storms, missing timeouts, one bad dependency sinking the service, overload | CircuitBreaker (C1) · RetryBackoff (C2) · TimeoutsDeadlines (C7) · Bulkhead (C8) · Idempotency (C9) · LoadShedding (C10) · GracefulDegradation (C11) |
| Messaging / async | `sdp-messaging` | *reserved — later wave* | — |
| Data / scaling | `sdp-data` | *reserved — later wave* | — |
| Traffic / edge | `sdp-traffic` | *reserved — later wave* | — |
| Coordination / consistency | `sdp-coordination` | *reserved — later wave* | — |

Today the clinic has one room. If a symptom clearly belongs to a reserved
category, say so plainly rather than forcing it into resilience — that honesty is
also the signal that tells us whether the job-shaped split is holding.

## Routing rules

- **Symptom / clinic is the primary entry (E1).** A described failure ("p99 is
  walking upstream", "we fell over when the DB got slow") routes into the loop
  above, into `sdp-resilience` for availability/overload symptoms.
- **Name lookup is a bypass (E2).** "Explain the bulkhead pattern" / "what's a
  circuit breaker" → go straight to that card; still surface its trade-offs.
- **Code / diff in hand is a bypass (E4).** "This HTTP client sets no timeout" /
  a pasted retry loop → identify the missing or mis-set pattern and open its card.
  This is the first-class path for a coding agent.
- **Trade-offs before the recommendation, always.** Never drop a pattern as *the*
  answer. Name what it costs and the confirming metric to check first (a breaker
  is worthless if you have not looked at the raw error rate — CircuitBreaker
  doctrine). The constitution requires this; the clinic enforces it.

## Handoff with the arch-* family (loose coupling)

- **Architecture STYLE questions are not ours.** "Monolith or microservices?",
  "how many quanta?", "sync or async *between services*?", "which architecture
  style?" → **hand off to `arch-style`.** Do **not** run arch-style's four
  determinations here. Where a card needs a style fact, it **cites**
  `arch-style/references/style-selection.md` as FACT — it does not re-derive it.
  (`arch-style` reciprocally disclaims "intra-service design patterns" — the
  boundary is mutual.)
- **`sdp-*` is not `sdd-*`.** One character apart, opposite jobs: `sdd-*` runs the
  spec-driven *lifecycle* (spec/plan/tasks/implement). "Spec this", "run the sdd
  lifecycle", "replan the tasks" are never ours.
- **Consumers (later).** Cards are built to be cited by `arch-risk` (mitigations),
  `arch-validate` (fitness functions), `arch-decide` (ADR options), `sdd-spec`
  (verify lists), `sdd-brainstorm` (what-breaks), `aws-ai-design` (LLM tool-call
  resilience). No join is built this wave — the card sections are the seams.

## Constraints

- **The card is the unit.** Every card stands alone (readable without its source
  Concept), carries a stable `id`, and carries an explicit trade-off surface.
- **Cite, don't invent — and name the card by id.** Defaults, failure modes, and
  sources come from the cards (distilled from `cases/SystemDesignPatterns/`), not
  from memory; say which card you used (e.g. "Bulkhead C8") so the answer is
  addressable by the operator and by the consumer skills.
- **Recommend, then let the human decide.** Surface the trade-off; the operator
  owns the cost.
