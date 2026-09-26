# sdp-* pattern-card template (FROZEN 2026-09-13)

The one operational card template for the `sdp-*` family. **Frozen** after the
first three distillations — CircuitBreaker (C1), RetryBackoff (C2),
TimeoutsDeadlines (C7) — confirmed their intersection is identical (spec
`sdp-resilience.spec.md` AC-11). Copy this skeleton for every new card; the other
four wave-1 cards (Bulkhead C8, Idempotency C9, LoadShedding C10,
GracefulDegradation C11) must conform without editing the template. `sdp_card_lint.py`
enforces the mechanical subset (`id`, `## Trade-offs`, `## Sources`, an intro).

The **design record** is the spec's "card template" section; this file is the
working skeleton. If they ever disagree, the spec wins and this file is corrected.

```markdown
---
id: <catalog-id, e.g. C8>
title: <Pattern name>
description: <one line — clinic/action framing: diagnose → select → tune → verify>
tags: [system-design, resilience, ...]
---

# <Pattern>
See also: ../../../../cases/SystemDesignPatterns/<Concept>.md   <!-- NON-load-bearing bonus -->

<Intro paragraph, no heading: definition + motivation + the quality attributes and
their cost. The card must be self-contained — readable without following any link.>

## Lineage and vocabulary

## <Mechanics …>            <!-- 1–N pattern-specific sections; keep the source's real mechanics -->

## Configuration & verified defaults    <!-- canonical name; fold library-defaults / OS-floor here -->

## Where it lives

## Observability

## Tuning

## Alternatives that beat a <pattern>    <!-- carries the "when NOT to use it" material -->

## Worked calibration — <scenario>

## Testing and operating

## Failure modes

## <Pattern> around LLM provider APIs

## Trade-offs        <!-- REQUIRED (lint) -->

## Sources           <!-- REQUIRED (lint) — carry the source Concept's real citations, by name -->
```

## Consumer-seam anchors (J1 — reserved, none built)

Each of the six consumer output shapes is a **projection** of sections above, not a
new section: mitigation → Failure modes + Configuration + Trade-offs · fitness
function → Observability · ADR option → Trade-offs + Alternatives · verify task →
Configuration + Tuning · what-breaks → Failure modes + Alternatives ·
tool-call-resilience → the LLM-provider section.

## Frozen mechanics bands (record of the 7 wave-1 cards)

The template held across all seven — every card carries the 12 intersection sections;
only the mechanics band varies (the template's "1–N pattern-specific sections").

| Card | id | Mechanics band (the variable part) |
|---|---|---|
| CircuitBreaker | C1 | three states · what counts as a failure · half-open probe design · state scope |
| RetryBackoff | C2 | what is worth retrying · backoff & jitter · retry budgets · amplification & the one-layer rule · idempotency · timeouts-deadlines-breaker · strategy comparison |
| TimeoutsDeadlines | C7 | five timers that share a name · remaining-time budgets & grpc-timeout · cancellation · hedging vs retry |
| Bulkhead | C8 | thread-pool vs semaphore isolation · connection-pool isolation · Envoy limits ≠ breaker · shuffle sharding · cells as a tactic · Little's-law sizing |
| Idempotency | C9 | HTTP safety ≠ app idempotency · the key protocol · key lifecycle · inbox (at-least-once + idempotent consumer) · TTL window · retries only if callee idempotent · dedup-store variants |
| LoadShedding | C10 | goodput vs throughput · shed early, never the ping · queue discipline (FIFO/LIFO/CoDel) · adaptive concurrency · 503 vs 429 vs degraded · backpressure vs shed |
| GracefulDegradation | C11 | two directions, one contract · what you serve instead (fallback taxonomy) · kill switches · stale serving (RFC 5861) |
