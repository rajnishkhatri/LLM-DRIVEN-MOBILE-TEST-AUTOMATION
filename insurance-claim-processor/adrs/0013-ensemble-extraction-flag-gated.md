# ADR 0013. Ensemble the extraction step across models, flag-gated

## Status
Accepted — **reverses (bounded)** the cascade-only scope in
`../assess/capability-brief.md` §4 ("Orchestration pattern: **cascade**, not
aggregation … Aggregation (vote three models) is for high-stakes diagnosis, not
a 2–3 doc PoC")

## Context
The capability brief chose cascade over aggregation for a 2–3 doc PoC and parked
ensembling. Best practice #5 asks for multi-model ensembling to improve
reliability/accuracy and reduce single-model dependency — a production driver.
Insurance extraction is exactly the "high-stakes" case the brief said
aggregation is *for* (a wrong `claim_amount` is a wrong payout), so the brief's
own reasoning supports enabling it at production scope. The summary step, by
contrast, is free text — not field-votable.

Alternatives: (a) stay cascade-only — rejected by the ask; (b) ensemble every
step including the summary — rejected (no sound vote over free text); (c)
**ensemble the extraction step only**, field-level majority + agreement score,
flag-gated for cost, disagreement → human review.

## Decision
We will ensemble the **extraction** step across the N models configured in
AppConfig (ADR 0010), invoked through the adapter (ADR 0011), combined per-field
by majority/agreement into one schema-valid result plus a per-field `agreement`
score. Ensembling is **OFF by default** and enabled only by feature flag
(ADR 0010) because it multiplies token cost. The summary stays single-model
cascade.

- IF members disagree beyond the agreement threshold on a required field, the
  field is low-confidence and the claim routes to **human review** — a split
  vote never auto-approves (integrity, AC-E1/F3).
- IF fewer than the quorum of members return a usable response, fall back to the
  single primary model (then degradation, ADR 0014) — never an empty ensemble.
- Members + combine outcome are recorded (`ensemble: {members[], agreement}`).

Business justification: ensembling cuts silent field errors on the highest-cost
mistakes (payout, PII) and reduces dependence on any one model's availability;
gating it behind a flag keeps the N× cost where it pays for itself.

## Consequences
Good: higher extraction reliability on the fields that matter; disagreement is
surfaced to a human rather than hidden; flag-gated cost; recorded provenance.
Bad: N× extraction token cost when on (bounded by the flag + quorum fallback); a
combine policy to maintain; latency of N calls (parallelizable in SFN later).
The bounded reversal keeps the brief's cascade for the summary intact — we did
not discard the brief, we narrowed its "no aggregation" to "no aggregation of
free text."

## Compliance
Fitness (offline): with the flag off, extraction is a single call (cost guard,
AC-O4); with it on, agreeing members produce one result + high agreement, and a
seeded disagreement forces `human_review` and never auto-approve (AC-O1, ties
AC-R3); a sub-quorum injected failure falls back to primary, never empty
(AC-O5); the summary is asserted single-model (AC-O3); `ensemble` recorded on
the result (AC-O4).

## Notes
Author: sdd-spec (model-resilience increment)
Approved by / date: Rajnish Khatri / 2026-09-21
Superseded date:
Last modified: 2026-09-21 / reverses (bounded) capability-brief §4 cascade-only
