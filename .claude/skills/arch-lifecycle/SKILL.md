---
name: arch-lifecycle
type: skill
description: >-
  Router for the software-architect workflow family (arch-*). Use when the
  user starts an architecture kata ("run a kata", "design a system for X"),
  asks to review an existing system's architecture end-to-end, or asks "which
  arch stage am I in / what's next". Routes to: arch-characteristics (derive
  the -ilities), arch-components (logical component design), arch-style
  (quanta + style selection), arch-decide (ADRs), arch-risk (risk matrix +
  risk storming), arch-validate (diagrams + intersections + governance). Do
  NOT use for a single stage the user already named — invoke that stage skill
  directly. Not for SDD code-change work (sdd-lifecycle) or knowledge curation
  (okf-curator).
---

# Architect Workflow — Lifecycle

> **Workspace binding.** Resolve each `{{placeholder}}` from `.arch/binding.toml`
> at the repo root, else first-run auto-adapt (see `FIRST_RUN.md` in this skill;
> schema in `binding.schema.md`). All arch-* siblings share this one binding —
> they do not carry their own copies.

Methodology source: `{{methodology_source}}` — the *Fundamentals of Software
Architecture* (Richards & Ford, 2nd ed.) study-notes bundle. Every stage skill
cites its chapters by `file.md:line`.

## The two modes

- **Kata mode** (practice, default): input is a kata statement (description,
  users, requirements, additional context — the format in
  `{{methodology_source}}/IdentifyingArchChar.md:72-88`). No repo evidence
  exists; premises come from the kata text and stated domain knowledge. The
  human plays the domain stakeholders at every gate.
- **Review mode** (real system): input is a repo and/or design doc. Evidence
  discipline applies: claims about the system need verified `file:line`
  citations (use `{{breadth_read_tool}}` for sweeps); hypotheses that reference
  code the repo doesn't contain are rejected. Entry point is often arch-risk
  or arch-validate rather than stage 1.

## The pipeline

Structural design is two activities — characteristics analysis and logical
component design — that "come together at a critical join point"
(`ArchitecturalChar.md:8`). They may run in either order or in parallel;
everything after the join is sequenced.

| # | Stage | Skill | Output artifact (home) |
|---|---|---|---|
| 1 | Derive + prioritize architecture characteristics | **arch-characteristics** | worksheet in `{{worksheet_home}}` |
| 2 | Logical component design (iterative cycle) | **arch-components** | component table + diagram in `{{component_home}}` |
| 3 | Quantum scoping + style selection | **arch-style** | style decision + topology in `{{worksheet_home}}` |
| 4 | Record architecturally significant decisions | **arch-decide** | ADRs in `{{adr_home}}` |
| 5 | Risk assessment + risk storming | **arch-risk** | risk report in `{{risk_home}}` |
| 6 | Diagram, intersections, governance | **arch-validate** | validated diagram set + checklist |

Routing rules:

- New kata / greenfield → start at 1 (or 1‖2), never at 3: style selection
  without a characteristics worksheet is the Accidental Architecture
  antipattern.
- "Should we use style X?" with no worksheet on file → arch-characteristics
  first; say why.
- Existing system, "is this architecture sound?" → arch-risk (with
  arch-validate's intersections checklist as the criteria menu).
- A stage's human gate failing loops back to that stage, not to 1.
- Stages 4–6 recur: ADRs are written whenever a significant decision lands
  (stage 3 always produces at least one), risk storming re-runs "after adding
  a major feature or at the end of every iteration" (`arch-risk.md:234`).

## Backdrop: the three laws

Every stage skill operates under (`laws-of-software-arch.md:10-14`):

1. **Everything in software architecture is a trade-off.** "If you think
   you've discovered something that isn't a trade-off, more likely you just
   haven't identified the trade-off… yet." The agent's job at every step is
   trade-off analysis, not advocacy — be an arbiter, not an evangelist.
2. **Why is more important than how.** Every artifact records the why; an
   undocumented decision is Groundhog Day fuel.
3. **Most decisions aren't binary — they're a spectrum.** Present options as
   positions on a spectrum with the trade-offs of each, and let the human
   place the cursor. An architecture decision is "one where each of the
   options has significant trade-offs" (`laws-of-software-arch.md:226`).

Division of labor (the book's own guidance on LLMs,
`arch-decisions.md:280`): the agent outlines trade-offs, validates premises,
and catches *missed* trade-offs; the human supplies context weighting and
makes the call. No stage skill ever auto-advances through its human gate.

**Batch runs (provisional-gate mode).** Only when the human has explicitly
asked for a multi-stage run (e.g. a kata test-drive) may gates be traversed
provisionally — under three rules: (1) every artifact's gate section reads
"GATE: PENDING HUMAN — recommendation …"; nothing is ever marked Accepted;
(2) gate-resident duties (e.g. arch-decide's first-use approval-criteria
conversation) are queued, never silently skipped; (3) the run ends with one
accumulated **ratification checklist** of every traversed gate and queued
duty, and outputs stay provisional until ratified. No other authority to
advance exists — do not invent one.

## Shared references

- `references/laws.md` — the laws, corollaries, and the trade-off-matrix
  procedure (used by arch-decide and any stage comparing options).
- `references/diagram-rules.md` — diagram guidelines used by every stage that
  emits a diagram (arch-components, arch-style, arch-risk, arch-validate).
- `references/research-2026.md` — externally verified 2025–2026 evidence:
  what this family adopted (ADR recency window, disclosure budgets),
  corrected (risk-panel independence claims, median merging, conditional
  deliberation), and what remains book-sourced-only (fitness-function
  generation, gate-integrity countermeasures). Re-research before treating
  its numbers as constants.

## Constraints

- Never strive for the best architecture; aim for the **least worst**
  (`ArchitecturalChar.md:250`). If a stage produces "the one true design,"
  that's a smell — re-present as trade-offs.
- Iterate. "All architectures become iterative because of unknown unknowns"
  (`laws-of-software-arch.md`, via `arch-intersection.md:189`). Artifacts are
  living documents; re-entry into any stage is normal, not failure.
- Generic advice is a defect: "Generic trade-off analysis isn't very useful —
  it only becomes valuable when applied in a specific context"
  (`laws-of-software-arch.md:212`). Every recommendation must bind to this
  kata's/system's stated context.
