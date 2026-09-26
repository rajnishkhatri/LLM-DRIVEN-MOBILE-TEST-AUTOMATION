---
type: analysis
title: 'Sysdesign skill family (sdp-*) — sdd-spec handover'
description: >-
  Stage-1 to Stage-2 bridge for the sdp-* system-design skill family: the
  accepted gate slate (S1, T2b, E1+E2+E4, P1 then P2, V1+V3+V5, N-b, J1),
  the validated hypotheses to carry, and the open questions sdd-spec must
  resolve. Does not write the spec, the cards, the skills, or the manifest.
tags: [sdd, spec, system-design-patterns, sdp, handover, skills]
---

# Sysdesign skill family (`sdp-*`) — sdd-spec handover

**For:** the next session running `/sdd-spec` (SDD Stage 2). Assume fresh context.
**Stage:** Stage 1 (brainstorm) is **COMPLETE** — the human gate closed 2026-09-13. This file is the Stage-1 to Stage-2 bridge. Do **not** re-open the gate. Do **not** write skills, cards, a manifest entry, or any implementation in the spec chat — Stage 2 writes the **spec** (and ADRs) that will govern them.
**Owner authority:** the picks are the human's. Where the owner diverged from the pre-gate review recommendation, §1 flags it — treat those as settled, not as openings.

**Read order for the new session:**
1. This file (slate + carry-forward).
2. `system-design-patterns-skill-mece-handover.md` — the live gate structure (§8), the consumer/steering dimension (§13), the recorded answers (§14).
3. `system-design-patterns-catalog.md` — the 43-topic catalog of record (ids A1–E13, group membership, per-card links).
4. `cases/SystemDesignPatterns/CircuitBreaker.md` and `RetryBackoff.md` — the operational depth bar the cards distil from.
5. `.cursor/skills/aws-ai-lifecycle/SKILL.md` + `evals/evals.json` — the sibling-family shape and the eval precedent.

---

## 1. Accepted direction — the gate slate (2026-09-13)

`S1 · T2b · E1+E2+E4 · P1→P2 (Z-spec) · V1+V3+V5 · N-b (sdp-*) · J1`

| Q | Id | Meaning | Divergence from review |
|---|---|---|---|
| Q1 scope | **S1** | Family teaches the **tactical loop only** (the 34 A/B/C/D Concepts as source). The 13 style Concepts stay in the bundle (R4) and feed `arch-style`. | none (review recommended S1) |
| Q2 topology | **T2b** | **Job-shaped** category skills: `sdp-resilience` / `-messaging` / `-data` / `-traffic` / `-coordination`, under a router. Commit now. | Owner chose T2b over the review's `T2-defer`. Consequence in §5.1. |
| Q3 entry | **E1 + E2 + E4** | Primary = **symptom/clinic** (E1); bypasses = **name lookup** (E2) and **code/diff in hand** (E4, first-class for coding agents). NFR entry (E3) not opened. | none |
| Q4 pipeline | **P1 → P2** | Hand-distilled cards now (P1) vs a frozen template; generator (P2) fast-follow after the template is proven; IR (P3) deferred but alive (consumer/MCP/Copilot drivers). Zip = **Z-spec** (decide in the spec). | none |
| Q5 quality | **V1 + V3 + V5** | Trigger+answer evals (V1), fitness recipes in each card's verify section (V3), card-template lint (V5). OKF lint + skill-sync (V4) is the always-on floor. Evals not deferred. | none |
| Q6 name | **N-b** | Prefix `sdp-*`; working router `sdp-patterns`. | Owner chose N-b over the review's N-a (`sysdesign-*`). Watch item in §5.2. |
| Q7 joins | **J1** | Seams only this iteration; no join built. First join to build later = **arch-risk**. | none |

Plus the **consumer/steering dimension** (mece §13): the *card*, not the skill, is the unit other families consume; cards must be addressable + self-contained + trade-off-carrying; six consumer join shapes reserved.

---

## 2. What Stage 2 (sdd-spec) must produce

1. **A spec** under `docs/sdd/specs/` for **wave 1** of the `sdp-*` family (the resilience slice — not the whole catalog).
2. **ADR(s)** for the ask-first items: a **new skill family** and a **new skill-sync manifest family** are "new abstraction / new node" class changes.
3. **The spec only** — not the cards, not the SKILL.md files, not the `manifest.toml` edit. Those are Stage-3 (implement) work this spec governs.

---

## 3. The v1 thing being specified (concrete)

- A `sdp-*` family: router `sdp-patterns` + first category skill **`sdp-resilience`** (job-shaped, T2b).
- **Entry:** clinic-primary (E1) with name (E2) and code/diff (E4) bypasses. The clinic surfaces trade-offs before recommending (constitution + the CircuitBreaker "check the raw error rate first" doctrine) and must recognize out-of-scope **style** symptoms and hand off to `arch-style` — that handoff is the S1 boundary made operational.
- **Content:** hand-distilled **cards** (P1) from the tactical Concepts, in the skill's `references/`. **Thin slice = 3 cards:** CircuitBreaker, RetryBackoff, TimeoutsDeadlines.
- **First-skill membership (draft from mece §8 — spec confirms):** own = CircuitBreaker, RetryBackoff, TimeoutsDeadlines, Bulkhead, Idempotency, LoadShedding, GracefulDegradation (7, all catalog group C). Cross-link, do not own = FailoverHealth (C3), CachingStrategies (B3), OutboxCdc (B7).
- **Quality:** V1 evals (trigger + answer) at the thin slice; V3 fitness recipes per card; V5 card-template lint.
- **Joins:** none (J1); reserve the §13 consumer output shapes.

---

## 4. Validated hypotheses to carry (mece §7 / brainstorm §9 — re-verify file:line before quoting)

- **H1** registering a family is a generic manifest entry, no code (re-open `tooling/skill-sync/skill_sync.py` + `manifest.toml`).
- **H2** per-skill `references/` progressive disclosure is the house pattern (every arch-*/aws-ai skill carries it).
- **H3** cards must **stand alone**; the Concept link is a bonus (a portable zip ships skill dirs only).
- **Hs1/Hs3** scope = the tactical loop; the arch-* gap is pattern **mechanics** (grep: zero circuit/bulkhead/saga/outbox/idempotency/rate-limit hits across arch-*).
- **Hq1/Hq2** evals are the only behavioral quality gate (`test_gate = <none>`); fitness = recipes, not executable code (no app stack in this repo).

---

## 5. Open questions the spec MUST resolve (spec-time tasks)

### 5.1 T2b is an untested bet — specify its killing test
The job-cut's trigger fitness is **PLAUSIBLE, not validated** (mece Ht2b). The spec must define the **V1 trigger eval** that tests whether real symptoms cluster inside one job bucket (resilience/messaging/data/traffic/coordination) or hop buckets. This is the mece §7 killing test, now a spec deliverable — the evidence the owner deferred by committing to T2b now.

### 5.2 Other tasks
- **Freeze ONE card template** after the first 3 distillations (CircuitBreaker/RetryBackoff/TimeoutsDeadlines), not before. S1 drops the style-card shape, so one operational template.
- **Evals-format compatibility** — probe `aws-ai-lifecycle/evals/evals.json` shape before committing the eval format.
- **Portable zip in v1? (Z-spec)** — decide standalone cards vs card+Concept-link. §13 requires addressable + self-contained cards either way; the zip only decides whether the Concept link may be load-bearing.
- **§13 consumer invariant** — the card template must give every card a **stable id**, self-containment, and an explicit trade-off surface; **V5 lints it**. Reserve the six consumer join output shapes (mitigation / fitness-function / ADR-option / verify-task / what-breaks / tool-call-resilience).
- **`sdp-*` vs `sdd-*` disambiguation** — skill descriptions/triggers must not mis-fire against the `sdd-*` family (one-character prefix distance; owner accepted N-b knowingly). Router suffix `sdp-patterns` vs house `sdp-lifecycle` is a spec sub-decision.
- **First join = arch-risk** (J1 defers building it) — reserve the mitigation output shape so the later join is a projection, not a redesign.

---

## 6. Constraints & gates

- **Constitution** `.cursor/rules/architecture-principles.mdc` — the pattern-card contract: definition, motivation, example/diagram, **trade-offs on every decision**, cited sources. A card without trade-offs or sources violates it.
- **check_gate** `python3 tooling/skill-sync/skill_sync.py check` (currently 6 families, 0 drifted, 0 shadow).
- **OKF lint** `python .cursor/skills/okf-curator/scripts/okf_lint.py` — bundle stays exit 0 (2 known non-bundle warnings).
- **test_gate = `<none>`** → the V1 eval set IS the family's quality gate.

---

## 7. Do NOT

- Re-open Q1–Q7 (owner closed them; §1 is the record) or the closed C1–C5 / R1–R5 decisions.
- Write cards, SKILL.md files, the manifest entry, or any implementation — Stage 2 writes the **spec** only.
- Re-derive mechanism notes that already exist — link `cases/data-intensive-design/*` and `cases/aws/ch08.md` instead.

---

## 8. Paths

| What | Path |
|---|---|
| Slate + carry (this file) | `docs/research/sysdesign/system-design-patterns-skill-spec-handover.md` |
| Live gate + §13 + §14 record | `docs/research/sysdesign/system-design-patterns-skill-mece-handover.md` |
| Historical brainstorm | `docs/research/sysdesign/system-design-patterns-skill-brainstorm.md` |
| Catalog of record | `docs/research/sysdesign/system-design-patterns-catalog.md` |
| Depth bar | `cases/SystemDesignPatterns/CircuitBreaker.md` · `RetryBackoff.md` |
| Sibling family shape | `.cursor/skills/aws-ai-lifecycle/SKILL.md` |
| Eval precedent | `.cursor/skills/aws-ai-lifecycle/evals/evals.json` |
| Manifest | `tooling/skill-sync/manifest.toml` |
| Spec home (output) | `docs/sdd/specs/` |
| First-join target | `.cursor/skills/arch-risk/SKILL.md` |

---

## 9. Closed — do not re-litigate

C1 broader catalog · C2 CircuitBreaker/RetryBackoff = depth bar · C3 new sibling family, independent-first · C4 Copilot deferred · C5 CB deepening done · R4 styles live in the bundle · R5 research closed · G3 moot · the Q1–Q7 slate (§1).
