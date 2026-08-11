---
type: architecture
title: ADR 0002 — Include model and provider version in the response-cache key
description: 'Fixes the defect found in the stage-2 review: the blueprint keys the LLM response cache on hash(input + prompt_version) while also naming model deprecation as outside the team''s control, so a gateway model change would silently serve cached output from a different model. The key gains model and provider version; the honest price is cache invalidation and token re-spend on every model bump.'
tags: [architecture, mobile-test-automation, adr, arch-decide]
---

# ADR 0002. Include model and provider version in the response-cache key

## Status

Accepted

## Context

**Forces.** The blueprint specifies the deterministic-replay cache key as
`hash(input + prompt_version)` — and, separately, names gateway model
deprecation as a risk outside the team's control. Those two statements
conflict: when the Orchestrator AI gateway swaps or upgrades a model, the
two-field key still matches, and the cache **silently serves output produced
by a different model**. Reproducibility is a top-3 characteristic, and its
generation-stability measure ("identical output on cache hit") becomes
meaningless if "hit" can span model versions. Stage 3 filed this under the
*versioning-is-easy* fallacy — a cost that was being paid silently.

**Alternatives considered.**

- **Add model and provider version to the key** (chosen).
- **Keep the two-field key** — maximizes hit rate; preserves the silent
  cross-model reuse this ADR exists to eliminate.
- **Disable the cache** — no staleness possible, but every retry re-spends
  tokens and reintroduces generation nondeterminism the cache exists to pin.

**Qualification.** Nygard test: passes — a construction technique that
directly serves a top-3 non-functional characteristic. Third-law test: passes —
correctness vs hit rate vs cost are real trade-offs on every option. Timing:
must precede the first cached call; the defect is invisible in operation until
an audit fails, which is the worst possible discovery point.

### Trade-off matrix

| Contextual factor (weight) | Versioned key (chosen) | Two-field key | No cache |
|---|---|---|---|
| Reproducibility of a served response (5) | **++** hit ⇒ same model, same prompt, same input | −− hit can span models, silently | + re-derives, but nondeterministically |
| Auditability — verdict traceable to a model version (5) | **++** version is in the key and the entry | −− lineage records a version the response may not match | + traceable per call |
| Token cost (3) | + hits survive until a model bump | ++ maximal hit rate | −− every call is paid |
| Operational surprise (3) | **++** invalidation is visible and explainable | −− wrong answers with no signal | + none |

## Decision

**We will compose the response-cache key as
`hash(canonical input + promptVersion + modelId + modelVersion + provider)`,
and each cache entry will carry the full pinning set it was produced under.**
A lineage write that references a cached response records the versions from
the cache entry — never from the gateway's current state.

**Technical justification:**

- A cache hit now *proves* the pinned configuration matched, which is exactly
  what the reproducibility measure asserts; before, a hit merely asserted the
  input text matched.
- Invalidation-on-model-change converts a silent correctness failure into a
  visible, budgetable cost event.

**Business justification:**

- **Cost:** the token re-spend after a model bump is bounded and infrequent;
  a certification issued on a stale-model response in a regulated bank is not.
- **User satisfaction / trust:** reviewers and auditors can rely on "cache
  hit" meaning "same conditions," which keeps the replay story defensible.
- **Strategic positioning:** audit-readiness is the system's licence to
  operate in this domain; this closes a hole an auditor would find.

## Consequences

- Every gateway model change invalidates the affected cache population — the
  re-spend is the honest price of correctness, and it also acts as a signal:
  a spike in cache misses is now a *model-changed* alarm.
- Hit rate drops only at model-change boundaries; between bumps, behaviour is
  identical to the two-field key.
- The two losing options' benefits (maximal hit rate; zero staleness risk) are
  forfeited knowingly; both fail the top-3 rows of the matrix.
- Imposes on future work: any new cached model interaction (e.g. the fidelity
  judge in ADR 0004) must use the same key discipline — the judge's
  calibration version plays the same role there.

## Compliance

- **Automated (CI):** unit-level fitness test asserting the key-composition
  function includes all five fields; fails the build if a field is removed.
- **F6 (automated, data-level) — this ADR is F6's owner.** Every lineage write
  carries the complete pinning set including model and provider version;
  sampled nightly against the lineage schema. ADR 0004 and ADR 0006 assert F6
  from their own angles (judge calibration version; data topology) and
  reference it rather than re-specifying it — one check, one owner, three
  interested decisions.
- **Operational:** alert when the gateway-reported model version differs from
  the version on a cache entry being served (should be impossible — the alert
  is a canary for key-discipline regressions).

## Notes

Author: arch-decide stage 4 (agent draft)
Date: 2026-07-26
Approved by / date: Rajnish Khatri / 2026-07-26
Superseded date: —
Last modified / by / what: 2026-07-27 / stage-5 arch-risk (P2 mitigation M27, accepted by owner) / owning store named: the response cache lives in **PostgreSQL, its own schema** alongside the conversion-state, lineage, and queue schemas — small JSONB payloads keyed by the five-field key, lifecycle-distinct (evictable and rebuildable; the one store allowed to lose data, except entries referenced by certification verdicts, which are retention-bound per carry-forward rule CF7). M15's canonicalized-snapshot digest feeds the cache key's input-hash field.
