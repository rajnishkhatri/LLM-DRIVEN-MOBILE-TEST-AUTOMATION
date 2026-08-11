---
type: design-agent-prompt
title: SDD Lifecycle — Three-Audience PPTX Presentation Prompt
description: Self-contained design-agent prompt that instructs an agent to produce a three-audience PowerPoint presentation of the SDD 10-stage workflow. Inlines full source from the lifecycle and five stage-owning skill files; no external file reads required.
tags: [design-agent, sdd, lifecycle, pptx, developers, architects, managers, anti-slop]
source: .claude/skills/sdd-lifecycle/SKILL.md + sdd-brainstorm + sdd-spec + sdd-replan + sdd-implement + sdd-converge
---

# Design-Agent Prompt — SDD Lifecycle Three-Audience PPTX Presentation

## What you're building

One PowerPoint file — `SDD Lifecycle — Three-Audience Presentation.pptx` —
that explains the 10-stage software-development workflow to three audiences
simultaneously: **Developer** (task-execution discipline), **Architect**
(constitution + decision records), and **Manager** (human-gatekeeping
contract). The three-audience framing lives in the **speaker notes** of
every slide — one notes panel with three labeled sections, so a presenter
reads the room and uses the right frame.

It is an explanatory deck for a one-hour stakeholder briefing — not a
training manual, not a process spec, not an interactive tool. The
deliverable is the `.pptx` itself; how you produce it (python-pptx,
Node, manual XML, whatever) is your choice. The constraints below govern
the deck, not the toolchain.

> **Terminology rule.** Never surface the internal skill-file identifiers
> (`sdd-brainstorm`, `sdd-spec`, `sdd-replan`, `sdd-implement`,
> `sdd-converge`, `EARS`, `SKILL.md`) in slide titles, body text, or
> speaker notes. Translate every concept into plain language. Internal
> names are tooling implementation details; audiences engage with concepts.

## Constraints

1. **One `.pptx` file.** Opens cleanly in PowerPoint, Keynote, and Google
   Slides. No external dependencies to view it.
2. **16:9 aspect ratio.** Slide dimensions 13.33" × 7.5" (or the equivalent
   EMU value your toolchain uses). Do not default to 4:3.
3. **Action title on every slide — section headers included.** A complete
   sentence that states a conclusion (has a subject and a verb; states a
   claim, not a category). Example of failure: "The Enforcement Layer".
   Example of pass: "Five automatic mechanisms enforce the rules at write,
   command, and merge time." Section-header titles carry their section's
   mini-Complication — the tension the section resolves — so each section
   opens a fresh attention cycle. Sole exception: Slide 1's deck title may
   be a name.
4. **Titles Test (preflight).** Before building any slide, draft all 22
   titles as an ordered list and verify they convey the complete argument
   on their own. Only once the titles pass the test do you build the slides.
   The titles list is the first artifact; emit it as `TITLES.md` alongside
   the `.pptx`.
5. **Speaker notes format** on every slide (three-section, labeled):
   ```
   [Developer] <framing for developer audience>

   [Architect] <framing for architect audience>

   [Manager] <framing for manager audience>
   ```
6. **Clean design.** Define a `PALETTE` (in your toolchain or as a comment
   in `COVERAGE.md`): Developer `#3B82F6` (blue), Architect `#F59E0B`
   (amber), Manager `#10B981` (green). Warning color: `#EF4444` (red) for
   "what goes wrong" slides. Neutral background: `#F8FAFC`. Table header
   rows use a dark neutral fill with white text; body rows alternate
   neutral and white. Do not scatter hex codes — centralize the palette.
7. **Slide-number footer** on every content slide (not section headers,
   not the title slide): bottom-right, 9pt, neutral color.
8. **No duplication.** If your toolchain is code-based, define helpers for
   repeated slide shapes (stage card, table builder, notes formatter). Do
   not inline the same shape-drawing logic more than once (5-line clone
   tripwire).
9. **Circuit breaker.** If a slide cannot be built from content in §A–§F
   without fabricating spec, emit a placeholder slide titled
   `TODO: <what's missing>` and flag it in `COVERAGE.md`. Three failed
   attempts at the same slide = placeholder + flag, not a fourth variation.
10. **PDF-export safe.** The deck must export cleanly to PDF via
    PowerPoint's File → Export — no content cut off, no missing glyphs.
    Avoid emoji as semantic markers (rendering varies by OS); prefer filled
    shapes or unicode symbols with broad font coverage.

================================================================
== INLINED SOURCE: SDD LIFECYCLE + FIVE STAGE-OWNING PHASES   ==
================================================================

### §A. The 10-stage workflow map

The lifecycle is an ordered sequence of 10 stages grouped into five
conceptual phases. Each stage is a **human↔agent micro-loop**: the human
initiates or gates → the agent does the work → the human gatekeeps
(advance or loop back). No stage runs to completion without a gate.

**Plain-language stage names (use these verbatim in slide body text):**

| Stage # | UI name | Phase | Gate type |
|---|---|---|---|
| 1 | Explore & Ideate | Discover | Human gate — direction accepted |
| 2 | Write acceptance criteria | Specify | Human gate — spec approved |
| 3 | Clarify ambiguities | Specify | Sub-step within Stage 2 |
| 4 | Plan + task list | Specify | Human gate — tasks approved |
| 5 | Mid-flight adjustment | Replan | Human gate — replan approved |
| 6 | Build | Implement | Per-task: auto + human gate |
| 7 | Review the diff | Implement | Automatic gate — code reviewer |
| 8 | Run the tests | Implement | Automatic gate — test suite |
| 9 | Classify the gaps | Converge | Sub-step within Stage 10 |
| 10 | Sign off | Converge | Human gate — 6-criteria checklist |

**The five phases** (used as the grouping on the Slide 7 flow diagram):
Discover (1) · Specify (2–4) · Replan (5) · Implement (6–8) · Converge (9–10).

**The micro-loop contract (render as a two-column text block on Slide 13):**
```
Human initiates  →  Agent produces artifact  →  Human gates
                                                  ├── ADVANCE → next stage
                                                  └── REJECT  → loop back
                                                       Never free-run past a gate.
```

**Three governing principles (use as the Mini-A on Slide 5):**
1. The spec precedes the code — acceptance criteria are human-approved
   before any implementation starts.
2. The constitution is enforced mechanically — automated tests, hooks, and
   merge-time ratchets enforce engineering rules at every commit.
3. Mid-flight adjustment is first-class — replanning is a designed-in
   stage, not a failure state.

### §B. Stage 1 — Explore & Ideate

**Agent work:** reads engineering rules for every folder the idea touches;
audits every load-bearing premise (verified / refuted / unverifiable) —
refuted premises are corrected and re-posed before generating directions;
generates ~6 candidate directions (3 following existing repo patterns +
3 exploratory); validates every hypothesis against actual files, never
memory.

**Human gate:** direction-level acceptance; options are labeled (bare "yes"
is not valid); loop back if no direction survives invariant-checking.

**What goes wrong without this stage:**
- False premise → implementation solves the wrong problem.
- All directions are variations of one approach → trade-offs never surfaced.
- A chosen direction violates an invariant → found late, after
  implementation.

**Audience notes:**
- [Developer] Before writing any code, we verify that the problem we think
  we're solving is the problem that actually exists in the codebase —
  against the real files, not memory.
- [Architect] Every direction is checked against the layering invariants
  before it can be chosen. A direction that needs a new abstraction must
  name what it buys and what simpler thing was rejected.
- [Manager] The human gate here is direction selection — not rubber-stamping
  a plan the agent already wrote. The human picks which of ~6 vetted options
  to specify next.

### §C. Stages 2–4 — Specify, Clarify, Plan, Tasks

**Agent work:** writes acceptance criteria (one testable claim each, failure
paths first); runs structured ambiguity pass ≤5 questions before planning;
writes architecture plan derived from spec AND engineering invariants; a
plan needing a structural decision (new abstraction, new dep, new node)
raises a decision record — spec = what, decision record = why; decomposes
into atomic tasks (file-level, dependency-ordered, pass/fail 1:1 from
criteria); cross-checks spec ↔ plan ↔ tasks ↔ engineering rules; confirms
test suite is green before implementation starts.

**Two hard human gates:** (1) spec approved; (2) tasks approved.
**Keystone rule:** no implementation starts without both gates cleared.

**What goes wrong without this stage:**
- Scope expands silently during implementation.
- New abstractions or dependencies added without approval.
- Baseline already broken before new code is written.

**Audience notes:**
- [Developer] Every task maps 1:1 to an acceptance criterion. You know
  exactly what "done" looks like for your task before you write a line.
- [Architect] The plan is checked against the engineering invariants
  before any code. A new abstraction must justify itself with a decision
  record — the ratchet is the mechanical backstop.
- [Manager] Two explicit human gates: you approve the spec (what you're
  building) and the task list (how it's decomposed). Implementation cannot
  start until you clear both.

### §D. Stage 5 — Mid-flight Adjustment

**Triggers:** blocked task; human scope change; review finding that
invalidates a task; sign-off gate sending the loop back.

**Agent work:** reads the current externalized task list (state lives in the
plan document, not only in context — survives session resets); proposes
re-prioritization with a reason per task; if scope changed, propagates
backwards to the spec first.

**Routing:** scope changed → Stage 2; ordering only → rewrite task list;
priorities only → Stage 6 (Build).

**Circuit breaker:** three failed attempts at the same task → mandatory stop
and re-plan. Never emit a fourth variation of the same broken code.

**What goes wrong without this stage:**
- Blocked tasks cause thrashing: four variations of the same broken code.
- Scope changes absorbed silently into implementation.
- State lives only in context → lost on session reset.

**Audience notes:**
- [Developer] Three failed attempts is the hard stop. You route to re-plan,
  not a fourth try. The circuit breaker prevents thrashing.
- [Architect] A scope change always propagates backwards to the spec first.
  The spec is the source of truth; code follows.
- [Manager] Mid-flight adjustment is a first-class stage, not a failure
  state. The human gate is approving the re-prioritization. The plan doc is
  updated so the replan survives session resets.

### §E. Stage 6 — Build

**Per-task loop:**
1. Take the first unblocked task; respect dependency/parallelization markers.
2. Red first: write the test for the task's acceptance criterion, run it,
   paste the failing output. Then implement; paste the passing output.
   A test that never failed proves nothing.
3. Verify the task's own pass/fail criteria — iterate bounded by the spec.
4. Run the check gate after changes; test suite must stay green.
5. Blocked → Stage 5. All tasks green → Stage 7 (Review).

**Three backpressure rules:**
- Three strikes → re-plan. Three failed attempts = stop, not a fourth try.
- Small diffs. A task that balloons past readable size → split, not push.
- Defensive coding is not free. A try/except / return None / or <default>
  must name the specific failure it catches — never fabricate a value to
  paper over an undecidable case.

**Automatic enforcement (fires without human action):**
1. Write-time format/lint hook → advisory, never blocks an edit.
2. Command-time deny-list backstop → fires before a shell command runs.
3. Turn-end decision-record reminder → advisory if structural seam touched.
4. Merge-time test-weakening ratchet → CI-fail on deleted test or
   unjustified skip. Waiver: explicit token in commit message.
5. Merge-time decision-record ratchet → CI-fail on structural change with
   no filed decision record. Waiver: explicit token in commit message.

**Audience notes:**
- [Developer] Red first — paste the failing output, then implement, then
  paste the passing output. A test that never failed proves nothing. The
  paste is the evidence.
- [Architect] Merge-time ratchets enforce the constitution mechanically: a
  deleted test or an unjustified skip fails CI. These can't be bypassed
  without an explicit waiver token in the commit message.
- [Manager] "Tests pass" without the output is not a result. The team shows
  evidence, not assertions.

### §F. Stages 9–10 — Classify Gaps & Sign Off

**Gap classification (Stage 9):**

| Class | Meaning | Route |
|---|---|---|
| Missing | Planned, not implemented | Fix task → Stage 6 |
| Partial | Implemented, criterion unmet | Fix task → Stage 6 |
| Contradicts | Conflicts with spec/plan | Stage 2 — spec problem |
| Unrequested | Built but not in the spec | Stage 2 — de-scope or spec it |

New fix tasks appended to the task list — never rewrite existing tasks.

**Sign-off checklist (Stage 10) — six criteria, human-answered, not
agent-declared:**

| # | Criterion | Evidence required |
|---|---|---|
| 1 | Converged | Every criterion has a passing test; no missing/partial/contradicts gaps |
| 2 | Gates green | Check gate AND test suite green — paste the actual output |
| 3 | Decision records filed | Every structural trigger has a filed record + index/log entries |
| 4 | Comprehension gates answered | Every gate that fired was answered by the human in their own words |
| 5 | Eval captured | Every LLM call recorded per the eval-capture rule |
| 6 | Blast-radius cleanup | Delete what the change added that the final shape no longer needs |

**Bounded:** if convergence is not reached within the agreed iteration
ceiling, stop and force human review — the loop never calls itself done.

**Audience notes:**
- [Developer] Sign-off is the six-criteria checklist. You paste the gate
  output, not a summary. You clean up what you added that the final shape
  no longer needs.
- [Architect] Criterion 3 is the decision-record gate — every structural
  seam touched must have a filed record before sign-off. The merge-time
  ratchet is the mechanical backstop.
- [Manager] Sign-off is human-answered, not agent-declared. You clear the
  six criteria. "Converged" means every acceptance criterion you approved
  in Stage 2 has a passing test.

================================================================
== END INLINED SOURCE                                          ==
================================================================

## Slide deck structure (22 slides)

> **Attention-cycle structure.** Section 1 (Slides 3–5) models the full
> Mini-Situation → Mini-Complication → macro Question → Mini-Answer cycle
> explicitly. Sections 2–5 each open a fresh cycle through their section
> header: the header title states the section's mini-Complication (the
> tension), and the section's content slides deliver the mini-Answers
> (claim titles) with evidence after each answer, never before. A separate
> Mini-Situation slide per section would balloon the deck past its one-hour
> briefing budget — that tradeoff is deliberate. A section whose header
> fails to state a tension is flat-lined and must be re-titled.

Each entry maps to one slide. `layout` is a hint (Title Slide / Section
Header / Title and Content / Title Only + shapes / Two-Content); use
whatever your toolchain provides that fits.

### Section 0 — Title

**Slide 1** (layout: Title Slide)
- Title: `Building Software That Can Be Explained Line-by-Line`
- Subtitle: `A 10-Stage Workflow with Human Gates, Automatic Ratchets, and Verifiable Sign-off`
- Notes:
  [Developer] You leave with the per-task discipline — red test, paste output, advance.
  [Architect] You leave with the ratchet model — what enforces the rules and what waivers look like.
  [Manager] You leave with the gatekeeping contract — where you steer and what "done" means.

---

### Section 1 — Why this exists

**Slide 2** (layout: Section Header)
- Title: `Faster shipping has made "when to stop" the hardest question in software.`
- Notes:
  [Developer] The next three slides set up why the per-task discipline exists.
  [Architect] The next three slides frame the problem the constitution solves.
  [Manager] The next three slides name the three failures your gate prevents.

**Slide 3** (layout: Title and Content) — Mini-S
- Title: `AI agents and development teams can ship features faster than ever.`
- Body (2 bullets — shared ground, audience already knows this):
  - Development cycles have compressed. AI agents write and test code in
    minutes, not days.
  - The constraint is no longer writing — it is knowing when to stop and why.
- Notes: [Developer] This is the context you already live in. [Architect]
  This is the context that makes governance harder. [Manager] This is the
  context that makes the gatekeeping contract more important, not less.

**Slide 4** (layout: Title and Content) — Mini-C + macro Question
- Title: `Without a gatekeeping contract, fast shipping produces three compounding problems.`
- Body (3 bullets — use warning accent `#EF4444` for bullet markers):
  - Scope expands silently — no acceptance criteria bound what gets built.
  - Tests prove the implementation, not the requirement — they green-light
    the wrong behavior.
  - "Done" is declared by the agent, not evidenced by the human — drift
    accumulates invisibly.
- Closing line (visually distinct — larger, centered, below the bullets;
  this is the macro Question the whole deck answers, and the hook that
  works for all three audiences simultaneously): *How do you keep
  agent-speed shipping without losing control of what gets built?*
- Notes: [Developer] These are not hypothetical. Each one has a concrete
  failure mode you can name. [Architect] The second failure — tests that
  green-light wrong behavior — is the hardest to detect after the fact.
  [Manager] The third failure — agent-declared done — is the one that reaches
  you last and costs the most to unwind. (All) Pause on the closing
  question — it is the question the rest of the deck answers.

**Slide 5** (layout: Title and Content) — Mini-A
- Title: `A 10-stage workflow with 5 human gates and 5 automatic mechanisms prevents all three.`
- Body (3 bullets — one per governing principle from §A):
  - The spec precedes the code — acceptance criteria are human-approved
    before any implementation starts.
  - The constitution is enforced mechanically — automated checks and
    merge-time ratchets enforce engineering rules at every commit.
  - Mid-flight adjustment is first-class — replanning is a designed-in
    stage, not a failure state.
- Notes: [Developer] The three principles translate directly to the per-task
  loop you run. [Architect] The second principle is the one the ratchets
  implement mechanically. [Manager] The first and third principles are the
  two moments where your gate matters most.

---

### Section 2 — The Workflow

**Slide 6** (layout: Section Header)
- Title: `Most process diagrams hide who decides — this workflow marks every human decision.`
- Notes:
  [Developer] The next five slides walk you through each phase — find yourself at Build.
  [Architect] The next five slides show where the constitution is checked at each gate.
  [Manager] The next five slides mark every lock — every moment the workflow pauses for you.

**Slide 7** (layout: Title Only + shapes) — Flow diagram
- Title: `Ten stages, five phases, five human gates — each stage is a bounded loop.`
- Body: render the 10-stage flow as a sequence of rounded-rectangle shapes.
  Each stage card: 1.1" × 0.55", 0.15" gap between cards, 5 cards per row,
  2 rows. Group into 5 phases by background fill color — use five light
  tints of a single neutral hue (e.g. slate at 5 lightness steps), NOT the
  three audience accent colors, which are reserved for audience labeling.
  Connect cards with thin arrows within each row; show the row-to-row wrap
  with a curved arrow. Stages 1, 2, 4, 5, and 10 (the five stage-level
  human gates) get a small filled circle (0.12" diameter, warning red
  `#EF4444`) overlaid on the top-right corner of the card — do not use
  emoji glyphs (rendering varies by OS). Stage 6 does NOT get a dot: its
  human check lives inside the per-task loop, not at the stage boundary
  (Slide 10 covers it). Below the flow, a one-line legend:
  `● = stage-level human gate`. No table on this slide — the stage list
  lives in the §A reference table and is not duplicated here.
- Notes: [Developer] Find yourself at Stage 6 (Build) — that is where most
  of your work lives. [Architect] The Specify phase (2–4) is where the
  constitution is checked before code. [Manager] The red dot marks every
  moment where the workflow pauses for your decision.

**Slide 8** (layout: Title and Content) — Discover phase
- Title: `Direction is chosen from evidence, not assumption — every premise is audited first.`
- Body (3 bullets from §B):
  - The agent audits every load-bearing premise against actual codebase
    files — verified, refuted, or flagged as unverifiable.
  - ~6 candidate directions are generated: 3 following existing patterns +
    3 exploratory. Six variations of one approach is a rejection signal.
  - Every hypothesis is validated against real file paths, not memory. A
    hypothesis that references something the codebase does not contain is
    rejected.
- Notes: copy the [Developer]/[Architect]/[Manager] lines from §B's
  "Audience notes" subsection, then append this worked-example trace after
  the [Manager] section: "In the worked example: the premise 'a badge
  component is available' was refuted — the codebase contained no badge
  component. The direction was corrected to reuse StatusChip before any
  spec was written." (Notes only — never in slide body.)

**Slide 9** (layout: Title and Content) — Specify phase
- Title: `Acceptance criteria and task list both require explicit human approval before any code is written.`
- Body (3 bullets from §C):
  - Each acceptance criterion is one testable claim, with failure paths
    specified first.
  - A plan needing a structural decision — new abstraction, new dependency,
    new framework node — raises a decision record before implementation.
  - A cross-check confirms spec ↔ plan ↔ tasks are internally consistent
    and reference only files that exist.
- Callout box (distinct background fill): **Keystone rule:** no
  implementation starts without spec approval AND task approval.
- Notes: copy the [Developer]/[Architect]/[Manager] lines from §C's
  "Audience notes" subsection.

**Slide 10** (layout: Title and Content) — Build phase
- Title: `Every task starts with a failing test — the paste proves the test really failed.`
- Body (numbered list — the per-task loop from §E):
  1. Take the first unblocked task.
  2. Write the test. Run it. Paste the failing output.
  3. Implement. Paste the passing output.
  4. Run the check gate. Keep the test suite green.
  5. Blocked → re-plan. All tasks green → Review.
- Sub-bullets (three backpressure rules, indented):
  - Three failed attempts → stop and re-plan, not a fourth variation.
  - A task that balloons past readable size → split, not push harder.
  - A defensive fallback must name the failure it catches — never paper
    over an undecidable case.
- Notes: copy the [Developer]/[Architect]/[Manager] lines from §E's
  "Audience notes" subsection, then append this worked-example trace after
  the [Manager] section: "In the worked example: task T1's failing output
  was 'FAILED: AssertionError: expected badge element, got null'; after
  implementation, 'PASSED: badge renders with count=3 after 3 questions
  answered'." (Notes only — never in slide body.)

**Slide 11** (layout: Title and Content) — Converge phase
- Title: `Sign-off is human-answered and evidence-based — the agent cannot declare itself done.`
- Body:
  - Gaps are classified before any fix is written (missing / partial /
    contradicts / unrequested).
  - New fix tasks are appended — existing tasks are never rewritten.
  - The six sign-off criteria require pasted evidence, not summaries.
- Notes: copy the [Developer]/[Architect]/[Manager] lines from §F's
  "Audience notes" subsection.

---

### Section 3 — The Human Gatekeeping Contract

**Slide 12** (layout: Section Header)
- Title: `An agent that grades its own work will always pass itself.`
- Notes:
  [Developer] The next three slides define the loop you run inside every task.
  [Architect] The next three slides define where the agent cannot pass its own gate.
  [Manager] The next three slides name the five moments where you steer, not rubber-stamp.

**Slide 13** (layout: Title and Content) — Micro-loop
- Title: `Every stage is a bounded human↔agent loop — the agent never advances itself.`
- Body: the micro-loop contract from §A rendered as a monospace text block
  inside a shape:
  ```
  Human initiates
    → Agent produces artifact
      → Human gates
          ├── ADVANCE → next stage
          └── REJECT  → loop back
                         Never free-run past a gate.
  ```
- Notes: [Developer] The "loop back" path is not an error — it is the normal
  correction mechanism. [Architect] The gate is where the constitution is
  checked; the agent cannot pass its own gate. [Manager] "Never free-run past
  a gate" means the human steer is structurally required, not advisory.

**Slide 14** (layout: Title and Content) — 5 human gates
- Title: `Five moments where the human steers — not rubber-stamps — before the workflow advances.`
- Body: 5-row table (Stage | What the human decides):

  | Stage | What the human decides |
  |---|---|
  | Explore & Ideate | Which direction to specify next — chosen from ~6 vetted options |
  | Write acceptance criteria | Whether the acceptance criteria are complete and testable |
  | Plan + task list | Whether the task list is atomic and dependency-ordered |
  | Mid-flight adjustment | Whether the re-prioritization is correct |
  | Sign off | Whether all 6 evidence criteria are satisfied |

- Notes: [Developer] Each gate is explicit — there is no implicit advance.
  [Architect] Each gate is also a constitution-check point — the spec,
  plan, and task list are checked against the engineering invariants
  before approval.
  [Manager] At each gate, you are deciding to advance or loop — not
  approving what the agent already committed to. The decision is yours.

**Slide 15** (layout: Title and Content) — Circuit breaker
- Title: `Three failed attempts triggers a mandatory re-plan — not a fourth variation of the same code.`
- Body:
  - Attempt 1 and 2: iterate bounded by the spec.
  - Attempt 3: stop. Route to mid-flight adjustment.
  - A fourth variation without replanning is thrashing, not progress.
- Design: render a counter graphic — four shapes in a horizontal row,
  1.5" × 1.5" each, 0.3" gap, centered vertically on the slide. First three
  are rounded rectangles in neutral fill labeled "1", "2", "3"; the fourth
  is an octagon in warning color `#EF4444` labeled "STOP: Re-plan".
- Notes: [Developer] The counter is explicit — you know when you hit it. It
  is not a judgment; it is a circuit breaker. [Architect] The replan always
  reads the externalized task list, not just in-context state — it survives
  session resets. [Manager] The circuit breaker is a cost-control mechanism.
  A fourth try without new information is waste, not persistence.

---

### Section 4 — What Cannot Be Skipped

**Slide 16** (layout: Section Header)
- Title: `Rules that rely on someone remembering them get skipped under deadline pressure.`
- Notes:
  [Developer] The next two slides show what fires automatically — no action needed from you.
  [Architect] The next two slides show the ratchets that enforce the invariants at merge time.
  [Manager] The next two slides answer "can this be bypassed?" — yes, with a recorded waiver.

**Slide 17** (layout: Title and Content) — Enforcement layer
- Title: `Five automatic mechanisms enforce the rules at write, command, and merge time.`
- Body: 5-row table from §E (When | What it enforces | Consequence | Waiver):

  | When | What | Consequence | Waiver |
  |---|---|---|---|
  | Write-time | Format / lint | Advisory | — |
  | Command-time | Deny-list backstop | Blocking | — |
  | Turn-end | Decision-record reminder | Advisory | — |
  | Merge-time | Test-weakening ratchet | CI-fail | Token in commit message |
  | Merge-time | Decision-record ratchet | CI-fail | Token in commit message |

- Notes:
  [Developer] Three of the five are advisory or invisible to you — only the
  two merge-time ratchets can fail your CI, and both tell you exactly why.
  [Architect] The two ratchets are the mechanical enforcement of the
  invariants: a deleted test and a missing decision record each fail CI
  deterministically — no reviewer judgment involved.
  [Manager] None of these mechanisms require anyone to remember anything.
  They fire automatically; the only human involvement is writing a waiver
  when there is a good reason.

**Slide 18** (layout: Title and Content) — Waivers
- Title: `Every ratchet has a waiver — but the waiver is a recorded line in the commit log.`
- Body (3 bullets):
  - CI-fail ratchets are not bureaucratic obstacles — they are the
    mechanical backstop for the engineering rules.
  - The waiver is a specific token added to the commit message; it appears
    in the repository's commit history permanently.
  - Bypassing is never silent. The waiver is the evidence trail.
- Notes: [Developer] You use the waiver when you have a good reason — and
  you write the reason in the commit. [Architect] The waiver token is what
  the invariant tests check for; a missing waiver = a failed test in CI.
  [Manager] "Can this be bypassed?" Yes, with an explicit waiver permanently
  visible in the commit history. No silent bypass exists.

---

### Section 5 — What "Done" Actually Means

**Slide 19** (layout: Section Header)
- Title: `"Done" is the cheapest word to say and the most expensive to get wrong.`
- Notes:
  [Developer] The next two slides define what you paste at sign-off — output, not summary.
  [Architect] The next two slides define the decision-record gate and the evidence column.
  [Manager] The next two slides define the six criteria you clear before accepting the work.

**Slide 20** (layout: Title and Content) — Sign-off checklist
- Title: `Done means six human-answered criteria with pasted evidence — not agent-asserted summaries.`
- Body: render the sign-off table from §F as a 6-row table
  (# | Criterion | Evidence required). Row 6 is the blast-radius cleanup
  criterion, numbered `6` — the cleanup is a sign-off criterion in its own
  right, not an afterthought.
- Notes: copy the [Developer]/[Architect]/[Manager] lines from §F's
  "Audience notes" subsection, then append this worked-example trace after
  the [Manager] section: "In the worked example: the 'Gates green'
  criterion was satisfied with pasted evidence — 'make check exit 0 ·
  pytest 47 passed'." (Notes only — never in slide body.)

**Slide 21** (layout: Title and Content) — Evidence vs assertion
- Title: `"Tests pass" without the output is not a result.`
- Body: a 2-column, 1-row table. Left cell = assertion (warning red
  fill `#EF4444`, white text): "All tests pass. The feature is complete."
  — No output. No trace. Not reviewable. Right cell = evidence (neutral
  fill): paste of `pytest 47 passed in 3.2s` + `make check exit 0` —
  Reviewable. Reproducible. Sign-off criterion 2 satisfied.
- Notes: [Developer] You paste the output as part of the task verification
  loop — not as a formality, but as the proof. [Architect] The evidence is
  what the sign-off gate checks; the agent cannot satisfy criterion 2 by
  summarizing. [Manager] The discipline is simple: show the output, not a
  summary. This is what distinguishes a trustworthy handoff from a hopeful
  one.

---

### Section 6 — Closing

**Slide 22** (layout: Title Slide) — Call to action
- Title: `The workflow exists so that every change can be explained — line-by-line, gate-by-gate.`
- Subtitle (three lines, one per audience; render each line's leading
  audience label in that audience's accent color from the PALETTE —
  Developer blue, Architect amber, Manager green; this is the one place
  the audience accents appear on a slide surface):
  - Developer: Start with the failing test. End with pasted evidence.
  - Architect: Let the ratchets enforce what convention cannot.
  - Manager: Your five gates are where the work steers — not where it stops.
- Notes: [Developer] The failing test is the starting point; the paste is the
  proof. Everything between is bounded by the spec. [Architect] The ratchets
  fail CI before the problem reaches production. Your job is to keep the
  decision records honest. [Manager] You steer at five explicit moments. That
  is the contract. Everything else runs — and when it blocks, it routes back
  to you.

================================================================
== END SLIDE STRUCTURE                                         ==
================================================================

## Inlined sample change

```python
SAMPLE_CHANGE = {
    "request": "Add a per-session question-count badge to the coach dashboard.",
    "stage_artifacts": {
        1: {
            "premises": [
                {
                    "claim": "Coach dashboard exists",
                    "status": "verified",
                    "evidence": "frontend/app/dashboard/page.tsx:1",
                },
                {
                    "claim": "Session state is persisted",
                    "status": "verified",
                    "evidence": "frontend/hooks/useCoachSession.ts:34",
                },
                {
                    "claim": "Badge component is available",
                    "status": "refuted",
                    "correction": (
                        "No badge component exists. "
                        "Closest match: StatusChip in "
                        "frontend/components/ui/StatusChip.tsx:12"
                    ),
                },
            ],
            "chosen_direction": (
                "Reuse StatusChip with a session-scoped counter — "
                "follows existing repo pattern (StatusChip.tsx:12); "
                "no new abstraction."
            ),
        },
        2: {
            "criteria": [
                "WHEN a coaching session is active, the dashboard SHALL "
                "display a question-count badge.",
                "IF the session has zero questions answered, the badge "
                "SHALL show '0'.",
                "WHEN the session ends, the badge SHALL persist the final "
                "count until the next session starts.",
            ],
            "ambiguities_resolved": [
                "Q: Does the badge reset on page reload mid-session? "
                "A: No — persists from session state.",
            ],
        },
        4: {
            "tasks": [
                {
                    "id": "T1",
                    "file": "frontend/app/dashboard/page.tsx",
                    "criterion": "criterion 1",
                    "depends_on": [],
                },
                {
                    "id": "T2",
                    "file": "frontend/hooks/useCoachSession.ts",
                    "criterion": "criteria 2 and 3",
                    "depends_on": ["T1"],
                },
            ],
        },
        5: {
            "triggered": False,
            "note": (
                "No blocked tasks; no scope change. "
                "Stage 5 (mid-flight adjustment) not entered for this change."
            ),
        },
        6: {
            "T1": {
                "red":   "FAILED: AssertionError: expected badge element, got null",
                "green": "PASSED: badge renders with count=3 after 3 questions answered  (1 test)",
                "check": "make check exit 0",
            },
        },
        9: {
            "gaps": [],
            "note": "All acceptance criteria passing. No gaps classified.",
        },
        10: {
            "checklist": [
                {
                    "criterion": "Converged",
                    "status": "pass",
                    "evidence": "3 criteria, 3 passing tests",
                },
                {
                    "criterion": "Gates green",
                    "status": "pass",
                    "evidence": "make check exit 0 · pytest 47 passed",
                },
                {
                    "criterion": "Decision records filed",
                    "status": "pass",
                    "evidence": "No new abstraction introduced — G1 not triggered; no record required",
                },
                {
                    "criterion": "Comprehension gates answered",
                    "status": "pass",
                    "evidence": "G1 not triggered",
                },
                {
                    "criterion": "Eval captured",
                    "status": "pass",
                    "evidence": "No LLM calls in this change",
                },
                {
                    "criterion": "Blast-radius cleanup",
                    "status": "pass",
                    "evidence": "console.log removed from SessionContext.tsx:88",
                },
            ],
        },
    },
}
```

The sample change is referenced in the speaker notes of Slides 8, 10, and
20 as a concrete trace: "In the worked example: [what happened at this
stage for this change]." It must not appear in slide body text — notes
only.

> **Partial trace.** The sample has artifacts for Stages 1, 2, 4, 5, 6, 9,
> and 10, but only Stages 1, 6, and 10 are traced in the deck (Slides 8,
> 10, 20). The other stage artifacts (2, 4, 5, 9) are reference material
> for you, the deck-builder — they ground your understanding of the
> workflow but are not surfaced on slides. Do not invent slides to show
> them; the one-hour briefing budget does not accommodate a full trace.

## Invariants

- No internal skill-file identifiers (`sdd-*`, `EARS`, `SKILL.md`) appear
  in slide titles, body text, or speaker notes at any point.
- Action title on every slide, section headers included (verb + claim;
  never a topic label; Slide 1's deck title exempt). Section-header titles
  state the section's mini-Complication.
- Speaker notes on every slide in the three-section labeled format.
- No fabricated numbers — counts come from `SAMPLE_CHANGE` or are
  explicitly flagged as illustrative in notes.
- No duplication: helper functions (or equivalent reuse) for repeated
  patterns; no 5-line clone.
- `TITLES.md` emitted alongside the deck — the 22 titles in order, so the
  argument is readable from titles alone without opening the `.pptx`.
- Circuit breaker: placeholder slide + `TODO:` title rather than invented
  content; flagged in `COVERAGE.md`.
- Do not collapse the three audiences into one label — the differentiated
  framing is the core value the speaker notes deliver.

## Deliverables

1. `SDD Lifecycle — Three-Audience Presentation.pptx` — the deck.
2. `TITLES.md` — the 22 slide titles in order (the Titles Test artifact).
3. `COVERAGE.md` — a coverage table listing every §A–§F element, the
   slide(s) it appears on, and whether it is fully covered, partially
   covered, or a placeholder. This is the review entry point: a reviewer
   reads `TITLES.md` first (does the argument hold?), then `COVERAGE.md`
   (is every source element surfaced?), then samples the `.pptx`.

## What "done" means

A reviewer who reads `TITLES.md`, reads `COVERAGE.md`, and opens the
`.pptx` walks away confirming: (a) the titles alone tell the complete
argument; (b) every slide has a three-section speaker notes panel; (c) the
10-stage flow diagram is present and legible on Slide 7; (d) the sign-off
table is present with the evidence column on Slide 20; (e) the enforcement
table is present with the waiver column on Slide 17; (f) no internal
skill-file identifiers appear anywhere in the deck; (g) the deck exports
cleanly to PDF with no content cut off and no missing glyphs.

If any of those seven is missing, the deck has failed.
