---
name: arch-decide
type: skill
description: >-
  Architect workflow stage 4: make and record architecturally significant
  decisions as ADRs. Use when a decision lands in any stage ("write the ADR
  for this", "should we use X or Y" where both options carry significant
  trade-offs), when auditing an existing system's undocumented decisions, or
  when a standard needs justification. Applies the last-responsible-moment
  test, the trade-off matrix, and the 7-section ADR template with Proposed →
  Accepted → Superseded status flow. Do NOT use for style selection analysis
  itself (arch-style), for risk scoring (arch-risk), or for trivial choices
  where one option has no significant downside — those aren't architecture
  decisions.
---

# Stage 4 — Architectural Decisions (ADRs)

> Binding: `.arch/binding.toml` (see arch-lifecycle). Methodology:
> `{{methodology_source}}` ch21 (`arch-decisions.md`) + ch27 laws. Template:
> `references/adr-template.md`. Trade-off matrix:
> `../arch-lifecycle/references/laws.md`.

Micro-loop: agent qualifies the decision, runs the trade-off analysis, and
drafts the ADR in **Proposed** status → human is the approval authority →
Accepted (or revised, or deferred with a named revisit trigger).

## Agent work

1. **Qualify: is this architecturally significant?** Nygard test
   (`arch-decisions.md:55`): does it affect structure, non-functional
   characteristics, dependencies, interfaces, or construction techniques?
   Technology choices count when they exist to serve a characteristic
   (`:53`). And the Third-Law test: do *all* options carry significant
   trade-offs? If not, it's not an ADR — say so and stop. When an upstream
   stage hands over a decisions-requiring-ADRs list (arch-style always
   emits one), account for every item: each must leave this stage
   **Written** (its own ADR), **Merged** (named in the covering ADR: "this
   ADR also records …"), or **Deferred** (stub per step 2). Silently
   dropping a handed-over item is a defect.
2. **Timing check — last responsible moment** (`:16`): is there enough
   information to justify the decision, and does the cost of further
   deferral now exceed the risk of deciding? If genuinely premature, record
   a *deferred* stub with the specific information that would unlock it
   (anti–Covering-Your-Assets without falling into Analysis Paralysis).
3. **Load decision context, then run the trade-off matrix** (laws.md):
   before drafting, read the **3–5 most recent Accepted ADRs** in the
   relevant `{{adr_home}}` scope — a small recency window achieves
   near-parity with full decision history (EASE 2026; see
   `../arch-lifecycle/references/research-2026.md` §2) — plus any older ADR
   the current decision plausibly touches (supersession candidates,
   cross-cutting standards). Then build the matrix: options × contextual
   factors, weighted for *this* context (Out-of-Context antipattern check).
   In review mode, premises about the current system need verified
   citations.
4. **Demand both justifications** (`:29-35`): technical AND business (the
   four common business justifications: cost, time to market, user
   satisfaction, strategic positioning). No business value = litmus-test
   failure — flag the decision for reconsideration, not just the ADR.
5. **Draft the ADR** per the template: numbered title; Status **Proposed**;
   Context (forces + alternatives, concise); Decision in affirmative
   commanding voice ("We will use…") with the why front and center;
   Consequences including the losing options' trade-offs; **Compliance**
   (how it will be governed — automatable fitness function or manual
   review, feeding arch-validate); **Notes** (author/dates). File it in
   `{{adr_home}}` under `common/`, `application/<app>/`, `integration/`, or
   `enterprise/` scope.
6. **Wire supersession.** If this replaces an Accepted ADR, mark both sides
   ("Superseded by N" / "supersedes M", `:92-104`). Never supersede a
   Proposed ADR — modify it until Accepted.

Existing systems (`:262-268`): work backwards — pick the significant
in-place decisions, reconstruct why (or mark unknown), validate or
invalidate against current context, and record. Uncovered "no good reason"
answers are findings, not embarrassments.

## Human gate

The human is the review board. Present: the decision one-liner, the weighted
matrix, both justifications, and the consequences — then ask for Accepted /
revise / defer. Also surface the **approval-criteria conversation** on first
use (`:106-110`): what cost / cross-team impact / security threshold should
route future ADRs to a higher authority instead of same-session acceptance?
Record the agreed thresholds in `{{adr_home}}/common/approval-criteria.md`.

## Constraints

- Communication rule (`:39-49`): when telling others, state the *nature and
  context* plus a link to the ADR — never paste the decision body into
  chat/email as a second system of record. Notify only people the decision
  directly impacts.
- Why > how throughout: the Decision section leads with justification;
  "understanding why a decision was made is far more important than
  understanding how something works" (`:122`).
- Every significant decision gets documented "no matter how obvious"
  (`:173`).
- LLM humility clause (`:270-280`): the agent outlines and stress-tests
  trade-offs; the weighting and the call belong to the human. Never mark an
  ADR Accepted without an explicit human yes.
