# Architecture characteristics — unified assistant ("Ari", governed router)

**Mode:** kata. Premises come from Dana's brief + the session premise audit
(5 claims refuted there; this sheet designs for the corrected framing).
**Cost of being wrong: high.** A cross-tenant leak is a reportable breach; a
confidently-wrong answer about money drives a bad treasury decision. Rigor on
isolation, provenance, and provability outweighs token-cost optimization.

**GATE: RATIFIED 2026-09-29.** Top-3 confirmed as proposed. Stakeholder
elevated **fault tolerance ("degrade, never die") to an explicit 4th driving
priority**. The auditability ↔ extensibility swap resolved in favor of
auditability. Demotions confirmed. Clinic pass (`sdp-resilience`) added **C9
idempotency on the ticket write** to demo scope (duplicate-injection test);
C1/C8/C10 stay brief-only, staged behind their CloudWatch signals.

---

## Domain ingest

| Field | From the kata |
|---|---|
| Description | One assistant embedded across four product surfaces, federating three capabilities: data Q&A (Omni, live), how-to (Confluence, RAG), get-unstuck (Jira ticket). Reframed: a governed router over deterministic code + LLM + human review layers |
| Users | Treasury customers (multi-tenant). Implicit actors: the four product teams (platform consumers), support agents, reviewers, phase-2 approvers |
| Requirements | Single input, streaming, history; embed-anywhere without the AI team; "GPT-4o"; 80% deflection; 6-week CAB demo; phase-2 actions "later" |
| Volume / latency / residency | **`needs-input`** (questions 3 & 5 for Dana). Treat as interactive chat, volume unknown |

## Driving characteristics (≤7)

| # | Characteristic | Src | Objective definition | Measure (kind) | Caveat |
|---|---|---|---|---|---|
| 1 | **Security — tenant isolation & entitlement** | implicit (treasury, multi-tenant) | Every backend call carries the end user's identity + tenant; entitlement enforced deterministically server-side; no answer contains data its asker isn't entitled to | Isolation violations = 0 on eval suite incl. cross-tenant probes (process) + prod metric alarmed (operational) + no adapter callable without an identity context (structural test) | Probes only prove the probes we imagined — pair with the prod alarm + CloudTrail audit |
| 2 | **Testability — of a stochastic system** | implicit (LLM + money) | Router, adapters, governance provable offline with no credentials; every quality claim (routing accuracy, grounding, refusal) is a golden-set number | Offline e2e green; every failure-taxonomy class has ≥1 eval; routing accuracy ≥ target (process) | Synthetic-only bias — production sampling closes it; say so |
| 3 | **Auditability — provenance per answer** | implicit (regulated) | Every answer reconstructable: route, confidence, source system + doc/query **version ids**, model + prompt version, entitlement scope | Complete provenance tuple on 100% of answers (structural test); decision-log completeness (operational) | Provenance pointing at mutable sources is theater — record versions |
| 4 | **Extensibility — streams as adapters** | explicit ("every surface, without the AI team") | A new capability/stream lands as a new adapter behind an existing port with zero core-file changes | Architecture test: imports point inward, core closed (structural); time-to-onboard an adapter (process) | Ports only we can implement = pseudo-extensibility; the reference adapter is the proof |
| 5 | **Fault tolerance — degrade, never die** | implicit (one front door) | One slow/down backend degrades that capability (answer degraded + ticket offered); the conversation continues | Injected Omni timeout → degraded path test green; per-adapter timeout budgets set (process/structural) | Bound retries — a retry storm on a sick backend is self-DoS |
| 6 | **Responsiveness** | explicit ("feel like ChatGPT") | Perceived-instant start on the fast path | TTFT p95 ≤ ~2s fast-path / ≤ ~5s LLM-fallback (operational; targets provisional, `needs-input`) | Averages hide the tail — report p95/p99 |
| 7 | **Cost-efficiency** | implicit (per-turn token spend) | Spend matches question difficulty; deterministic fast-path answers the known share for ~zero tokens | $/conversation; fast-path hit rate (operational) | The cheapest route that misroutes isn't cheaper |

### Ratified top 3 (any order) + elevated 4th

1. **Security (tenant isolation)** — the product-killing failure; also the seam phase-2 actions inherit.
2. **Testability (stochastic system)** — the only honest way to gate a non-deterministic router; everything the eval spec promises rests here.
3. **Auditability (provenance)** — an unattributed number about money is indefensible; provenance is also the eval signal and the adoption pitch.
4. **Fault tolerance (degrade, never die)** — elevated by the stakeholder at
   the gate: one front door multiplies the blast radius of failure; the
   ticket stream is the designed floor under the other two capabilities.

**Swap resolved at the gate:** auditability stays top-3 over extensibility —
a safe, provable, auditable router that's harder to extend beats an
extensible one that leaks (house precedent: the claim-processor sheet made
the same call).

**Elimination probe:** cull **cost-efficiency** first, then responsiveness.
Never cull security or auditability.

## Demoted / decomposed

- **"80% deflection"** — business outcome, not an -ility → handled via eval
  metrics: resolution rate + correct-handoff rate + capped confidently-wrong.
- **Configurability (model swap)** — handle via design: ModelPort / FM-adapter
  (ADR-②); the resolved model id lands in the provenance tuple.
- **"One consistent assistant"** — composite → one gateway + one governance
  plane + shared personality config; not a separate characteristic.
- **Avatar / personality** — product design, out of architectural scope.

## Others considered

Scalability / elasticity (`needs-input` volume) · availability (degrade-to-
ticket covers an assistive SLO; revisit if Ari becomes the primary interface)
· multilingual, accessibility (out of slice scope).

## Tension pairs

- **Security ↔ responsiveness:** entitlement check + output screen on every
  turn costs latency. Budget it; fail closed even when slow.
- **Security ↔ extensibility:** self-serve adapters vs central trust. Resolve:
  the governance gate lives in the core — adapters plug in *behind* it and
  cannot bypass it.
- **Auditability ↔ privacy/cost:** full prompt/response logs are PII-dense.
  Resolve: provenance tuple in the decision log; raw model I/O in a
  restricted store, access-gated.
- **Testability ↔ non-determinism:** deterministic-first path + temperature-0
  recorded fixtures for the LLM fallback; judge only the fuzzy remainder.
- **Responsiveness ↔ cost:** *synergy, not tension* — the deterministic
  fast-path serves both. Worth saying in the room.

## Clusters (input to style / ADR-①)

One governed interactive cluster — security + auditability + testability all
serve a single conversational surface. No counteracting public-scale vs
back-office split. **One quantum: hexagonal modular monolith.** The four
product surfaces are embed contexts, not quanta. Phase-2 actions join the
same quantum behind the same gate (their review-latency profile may argue a
second quantum later — noted, not assumed).

## Ubiquitous language

**Route** = capability decision (data / how-to / ticket / out-of-scope).
**Stream** = a pluggable capability behind a port. **Deflection ≠ resolution.**
**Provenance tuple** = (route, sources + versions, confidence, model + prompt
version, entitlement scope).
