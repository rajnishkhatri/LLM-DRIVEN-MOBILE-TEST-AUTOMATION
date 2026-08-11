# Risk matrix + storming instruments

From `cases/ArchitectureBook/arch-risk.md` (ch22).

## The risk matrix (`:10-25`)

Two dimensions only: **impact** and **likelihood**, each low (1) / medium
(2) / high (3); risk = product.

| | Likelihood 1 | Likelihood 2 | Likelihood 3 |
|---|---|---|---|
| **Impact 1** | 1 LOW | 2 LOW | 3 MEDIUM |
| **Impact 2** | 2 LOW | 4 MEDIUM | 6 HIGH |
| **Impact 3** | 3 MEDIUM | 6 HIGH | 9 HIGH |

Bands: 1–2 low (green), 3–4 medium (yellow), 6–9 high (red); pair color
with shading/symbols for accessibility. Rules: **impact first, likelihood
second; unsure likelihood ⇒ 3 until confirmed** (`:23`). **Unproven/unknown
technology ⇒ automatic 9** — the matrix doesn't apply (`:122,126`).

## Assessment report (`:27-56`)

Rows = risk criteria (the critical architecture characteristics); columns =
contexts (domains/subdomains — not services, too fine-grained `:40`). Sum
rows to rank criteria, columns to rank contexts (`:42`). Stakeholder view:
filter to high-risk only — signal over noise (`:44`). Direction (third
dimension, `:49-51`): mark each cell improving / worsening / static
relative to the last assessment, with a key; direction comes from
continuous fitness-function measurements where they exist.

## Risk storming phases (`:60-145`)

**Participants**: multiple architects + senior developers and tech leads
(implementation perspective + they learn the architecture, `:64`).
Facilitator = the architect running it. Input: comprehensive or contextual
architecture diagram, sent with the invitation (criteria/context to
analyze, logistics, `:81`).

1. **Identification (solo)** — each participant scores areas independently
   (`:79-85`); multi-dimension sessions annotate the criterion next to each
   score (`:87`). One criterion/context per session whenever possible
   (`:91`).
2. **Consensus** — post all scores on the diagram. Unanimous areas close.
   Discuss: level disagreements; single-identifier areas. Canonical
   resolutions: impact-true-but-likelihood-low (ELB, clustered → down to
   3); lone-identifier-with-scar-tissue (Push Expansion Servers crash under
   load → without them "no one would have seen the high risk until well
   into production"); "What's a Redis cache?" → automatic 9, then either
   change the technology or pay for training (`:99-128`). Ends when all
   areas agreed (`:130`).
3. **Mitigation (with paying stakeholders)** — changes range from full
   redesign to targeted refactoring (add a backpressure queue). Negotiation
   loop: propose → price → cost-vs-risk → cheaper compromise if rejected
   ($50k cluster-split rejected → $16k two-domain split accepted, `:143`).

## Worked mitigation shapes (nursing-hotline case, `:151-230`)

- **Availability**: split single DB → clustered nurse-profile DB +
  single-instance case-notes DB; external systems → look up SLAs (legally
  binding) / SLOs (not): Diagnostics Engine 99.99 % = 52.6 min/yr →
  risk removed; put SLAs on the diagram (`:193-197`).
- **Elasticity**: 500 req/s ceiling → (1) async queues for backpressure —
  good but wait times remain; (2) two channels, nurses prioritized
  (ambulance pattern); (3) outbreak cache server so peak queries never
  reach the engine (`:206-212`).
- **Security**: shared API gateway = high (3×2=6) → separate gateways per
  user type so non-nurse traffic can't reach medical records; facilitator
  initially scored it 2 and was talked up — consensus is bidirectional
  (`:221-223`).

## Cadence (`:234`)

Not one-time: after major features, at iteration ends, during refactors.
Variant: user-story risk (impact-if-not-done × likelihood-not-done) during
grooming (`:149`) — out of scope for this skill but worth naming.
