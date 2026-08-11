---
name: arch-risk
type: skill
description: >-
  Architect workflow stage 5: architecture risk analysis — risk matrix
  scoring, risk assessment reports, and the three-phase risk-storming
  workshop (identification, consensus, mitigation). Use when the user asks
  "what are the risks in this architecture", "risk-storm this", "score this
  risk", or after a major feature/iteration on a design. Solo mode simulates
  phase-1 participants with independent subagents. Do NOT use for user-story
  sizing (its variant exists but isn't architecture work), for making the
  mitigation decision itself (human owns cost trade-offs), or for generic
  code review.
---

# Stage 5 — Risk Analysis & Risk Storming

> Binding: `.arch/binding.toml` (see arch-lifecycle). Methodology:
> `{{methodology_source}}` ch22 (`arch-risk.md`). Instruments:
> `references/risk-storming.md`. Requires an architecture diagram as input
> (`arch-risk.md:68`) — if none exists, produce one first per
> `../arch-lifecycle/references/diagram-rules.md`.

Micro-loop: human picks the dimension(s) to storm → agent runs
identification and drafts consensus → human arbitrates disagreements and
owns mitigation cost calls.

## Agent work

1. **Set up the assessment frame.** Criteria = the system's most critical
   architecture characteristics from the worksheet (`arch-risk.md:33`);
   contexts = domains/subdomains — service-level is too fine-grained to see
   coordination risk (`:40`). Restrict each storming pass to a **single
   criterion or context** (`:91`); queue the rest as separate passes.
2. **Phase 1 — Identification, blind.** Spawn 3–5 subagent "participants"
   with distinct lenses (operations, security/data, implementation/
   dev-experience…), each scoring the diagram **without seeing the others'
   scores** — impact first, likelihood second; unknown likelihood defaults
   to 3; unknown-to-the-participant technology is an automatic 9
   (`:23,122-126`). Frame honestly: same-model lenses are **coverage** —
   each examines a different risk dimension — not statistically independent
   voters (2026 evidence: ~9 correlated judges ≈ 2.2 effective votes; see
   `../arch-lifecycle/references/research-2026.md` §3). More lenses ≠ less
   bias; cap at 5. Solo human participants fold in by submitting scores
   before any agent scores are revealed (`:66,79`).
3. **Phase 2 — Consensus, conditional.** Merge scores per diagram area:
   agreed cells close without discussion and numeric merges use the
   **median, never the mean** (research-2026.md §4); per-lens raw scores
   stay visible to the human. Deliberate only on (a) disagreements on level
   and (b) single-lens identifications — present the competing rationales
   (the ELB impact-vs-likelihood pattern) and drive to an agreed impact ×
   likelihood product. Log each lens's initial vs final position to expose
   anchoring (no movement) and conformity cascade (instant collapse). The
   facilitator can be outvoted (`:221`). Exit when every area has an agreed
   level.
4. **Phase 3 — Mitigation (human-gated per item).** For each medium/high
   risk, propose mitigations with rough cost/effort, iterating the book's
   loop: propose → price → present cost-vs-risk → if rejected, propose a
   cheaper partial mitigation (`:143`). For external dependencies, check
   SLAs/SLOs before inventing machinery — a published 99.99 % SLA can
   simply remove a risk (`:195`). Layer mitigations incrementally like the
   elasticity case: backpressure queue → priority (ambulance) channel →
   known-answer cache (`:208-212`).
5. **Record.** Risk assessment report to `{{risk_home}}<target>/risk-report.md`: matrix per
   criterion×context with the 1–9 products, row/column sums to rank
   criteria and contexts, direction markers vs the previous assessment
   (improving / worsening / static — include a key), the consensus log, and
   accepted/rejected mitigations. Update the architecture diagram with
   changes and SLAs. Stakeholder-facing summary shows high-risk only —
   filter the noise (`:44`). Significant mitigation decisions → arch-decide.

## Human gate

Two distinct roles, called out explicitly: as *participant/arbiter* in
phase 2 (their domain knowledge can overrule agent consensus — the
lone-identifier-with-experience case is why storming exists); as *business
stakeholder* in phase 3 — every mitigation with a cost is their accept /
reject / cheaper-alternative call. No auto-accepted mitigations. Cadence:
re-run after major features or at iteration end (`:234`).

## Constraints

- Scores come from the matrix (impact 1–3 × likelihood 1–3; bands 1–2 low,
  3–4 medium, 6–9 high) — never from vibes; the matrix exists to make risk
  "more objective" (`arch-risk.md:14`).
- Phase-1 blindness is inviolable: no participant (agent or human) sees
  another's scores before submitting. But never *claim* statistical
  independence for same-model lenses — their value is dimensional coverage;
  agent consensus is not evidence, which is why the human arbitrates the
  merge (research-2026.md §3–6).
- An unmitigated high risk in a live system outranks all forward-looking
  work — surface it as a blocking item (mirrors sdd-brainstorm's D0 rule).
- Risk storming shapes negotiation, not blame: outcomes are architecture
  changes and priced trade-offs, not fault-finding (`:145`).
