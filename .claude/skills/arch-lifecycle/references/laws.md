# The laws of software architecture + the trade-off-matrix procedure

Distilled from `cases/ArchitectureBook/laws-of-software-arch.md` (ch27).

## The three laws

1. **Everything in software architecture is a trade-off.** (`:10`)
2. **Why is more important than how.** (`:12`)
3. **Most architecture decisions aren't binary but rather exist on a spectrum
   between extremes.** (`:14`, `:218`)

## Corollaries of the First Law

- **Corollary 1 — Missing trade-offs** (`:180`): "If you think you've
  discovered something that isn't a trade-off, more likely you just haven't
  identified the trade-off… yet." When a decision seems free: keep looking.
  Canonical hidden trade-off: effective code reuse requires *abstraction AND
  low volatility* (`:188-190`) — which is why plumbing (frameworks, libraries,
  platforms) reuses well and domain concepts reuse terribly (this underlies
  DDD's bounded context).
- **Corollary 2 — You can't do it just once** (`:194-196`): dozens of
  variables (complexity, team experience, budget, team topology, schedule…)
  feed each analysis; subtle differences flip outcomes. Re-run the analysis
  even for seemingly similar situations. "The real job is trade-off analysis,
  not making permanent, perfect decisions."

## Definition that gates arch-decide

"A software architecture decision is one where each of the options has
significant trade-offs." (`:226`) If one option has no significant downside
in this context, it's a design/implementation choice — don't ADR it, just do
it and note it.

## The trade-off-matrix procedure (`:41-174`)

1. Answer "It depends!" with **"Depends on what?"** — enumerate the
   contextual factors (organization, technology landscape, team capabilities,
   budget) that actually differentiate the options here.
2. Build a matrix: options as columns, factors as rows; score each cell
   `+`/`−` (or short phrases).
3. **Weight by context** — the Out of Context antipattern (`:206-212`) is
   understanding the trade-offs but weighting them generically. Ask: "do all
   criteria have equal weight *for this organization, now*?" Reweighting can
   flip the winner.
4. Return to the stated goals and pick the option that best fits them; record
   the losing options and why they lost (feeds the ADR Context/Consequences).

## Stance rules

- Be an **arbiter, not an evangelist** (`:24-28`): yesterday's best practice
  is tomorrow's antipattern; decision makers want sober objectivity.
- Decisions live on spectrums (`:222-232`): present a slider, not a coin
  flip. We decide "in a swamp of uncertainty" — say what is unknown and what
  new information would move the cursor.
