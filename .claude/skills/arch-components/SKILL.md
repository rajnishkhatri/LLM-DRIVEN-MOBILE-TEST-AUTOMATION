---
name: arch-components
type: skill
description: >-
  Architect workflow stage 2: logical component design via the iterative
  identify → assign → analyze-roles → analyze-characteristics → restructure
  cycle. Use when the user asks "what are the components", "decompose this
  system", "is this component too big", or when a kata needs its logical
  architecture. Also for auditing an existing codebase's component structure
  (directory/namespace analysis, coupling metrics, connascence). Do NOT use
  for choosing the architecture style or quanta (arch-style), for deriving
  -ilities (arch-characteristics), or for physical/deployment topology.
---

# Stage 2 — Logical Components

> Binding: `.arch/binding.toml` (see arch-lifecycle). Methodology:
> `{{methodology_source}}` ch3 + ch8 (`Modularity.md`, `ComponentBased.md`).
> Reference: `references/component-cycle.md`. Diagram rules:
> `../arch-lifecycle/references/diagram-rules.md`.

Prerequisite: the characteristics worksheet — step 4 of the cycle cannot run
without it ("the architect must know the architectural characteristics
before building a logical architecture," `ComponentBased.md:262`). If none
exists, route to arch-characteristics or run both in parallel and join here.

Micro-loop: human supplies workflows/actors/stories → agent runs one full
cycle pass and shows its work → human accepts or redirects → repeat. "This
process is a feedback loop that essentially never stops"
(`ComponentBased.md:60`).

## Agent work (one pass of the Figure 8-6 cycle)

1. **Identify initial core components** — best guess, explicitly labeled as
   such; perfecting the first pass "when you know least about the system" is
   the named mistake (`ComponentBased.md:68`). Choose the approach and say
   why: **Workflow** (map major happy-path workflows, one component per
   step, reusing components across steps) or **Actor/Action** (better with
   multiple actors; the system itself is always an actor). Never the
   **Entity Trap** — reject any candidate named `*Manager/Supervisor/
   Controller/Handler/Engine/Processor` and re-derive from behavior. If the
   system truly is CRUD-only, say so: it needs a framework, not an
   architecture (`ComponentBased.md:155`).
2. **Assign requirements/stories to components.** A story that would
   otherwise be duplicated across N components forces a new shared component
   plus communication edges (`ComponentBased.md:193-197`) — duplication
   converts to coupling, visibly.
3. **Analyze roles & responsibilities.** Write a one-sentence role statement
   per component, then apply the **conjunction test**: "and / also / in
   addition / as well as" or comma-chains = too much responsibility
   (`ComponentBased.md:228`). Cross-check with the directory test (would all
   this code sensibly live in one namespace?). Split offenders; name the
   extracted components by verb-role (Validate Order, not Order Manager).
4. **Analyze architecture characteristics per component.** For each driving
   characteristic from the worksheet, ask which components it stresses
   unevenly: divergent load/reliability/availability inside one component —
   for instance, different actor classes with wildly different scale or
   availability stakes served by the same component → split it even when
   functionally cohesive. Cohesion alone does not license unbounded size.
   Only AFTER your own split analysis is written, self-check against
   `references/worked-answers.SEALED.md` — never earlier: it holds the
   book's worked kata splits, and naming them in this step seeded the
   answer during the GGG test-drive (SD1 class, 2026-07-25).
5. **Restructure + coupling pass.** Emit the revised component table
   (name / role / assigned stories / characteristics notes) and a mermaid
   component diagram. Run the coupling checks from the reference: fan-in/
   fan-out counts, Law-of-Demeter knowledge test (an intermediary that
   doesn't reduce efferent coupling is not a win — and Demeter
   *redistributes* coupling, it doesn't erase it), and name any connascence
   worth flagging in review mode. Write to
   `{{component_home}}<target>/logical-components.md`.

Review mode additions: derive the *actual* logical architecture from
directory structures/namespaces (leaf nodes = components,
`ComponentBased.md:26-31`), compare against the intended one, and cite
`file:line` for every structural claim. LCOM-style incidental-cohesion
finds (kitchen-sink utility classes) are reportable defects. Where the
workspace has a coding-rules catalog (e.g.,
`tooling/coding-rules-skill/references/rules-catalog.md` for the o1
pipeline), tag structural findings with its rule IDs — module-boundary
reach-in (CR-01), cycles (CR-02), layer-named packages (CR-03), public-by-
default types (CR-04) — so findings route into the same converge/review
vocabulary the coding agents use.

## Human gate

Human accepts the component set for this pass, or redirects: merge these /
split that / this story belongs elsewhere. Explicitly present the splits
made for characteristic reasons (step 4) as trade-offs — they add
communication edges. Not a one-time gate: expect re-entry whenever a feature
is added or changed. Advance → **arch-style** (the join point).

## Constraints

- Logical architecture only: components + interactions + actors. No UIs,
  databases-as-tech, services, or deployment units — those are physical
  architecture; skipping logical for physical yields "unstructured
  architectures that are hard to maintain, test, and deploy"
  (`ComponentBased.md:49`).
- Don't model every workflow — majors only; the rest evolve
  (`ComponentBased.md:83`).
- Attempting to divide a genuinely cohesive module "would only result in
  increased coupling and decreased readability" (`Modularity.md:52`) — the
  too-small tells matter as much as the too-big ones.
- Close every pass with: this is not the final design; choose the least
  worst trade-off set (`ComponentBased.md:388`).
