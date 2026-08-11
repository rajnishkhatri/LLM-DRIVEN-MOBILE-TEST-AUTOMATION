---
name: arch-characteristics
type: skill
description: >-
  Architect workflow stage 1: derive, define, and prioritize architecture
  characteristics ("-ilities") for a kata or system. Use when the user starts
  a kata, says "what characteristics does this system need", "derive the
  -ilities", "translate these business drivers", or challenges an existing
  characteristics list. Produces the ≤7 worksheet with a top-3, each
  characteristic objectively defined and measurable. Do NOT use for component
  design (arch-components), style choice (arch-style), or writing fitness
  functions into a real CI (that's implementation follow-through recorded by
  arch-validate).
---

# Stage 1 — Architecture Characteristics

> Binding: `.arch/binding.toml` (see arch-lifecycle). Methodology:
> `{{methodology_source}}` ch4–6 (`ArchitecturalChar.md`,
> `IdentifyingArchChar.md`, `MeasuringAndGoverning.md`).
> Reference tables: `references/characteristics-catalog.md`.

Micro-loop: human supplies the *domain problem* (kata statement or system
context) → agent extracts, tests, defines, and drafts priorities → human
plays the domain stakeholders at the gate.

## Agent work

1. **Ingest the domain.** Kata mode: parse description / users / requirements
   / additional context. Review mode: sweep the repo + docs with
   `{{breadth_read_tool}}`; every claimed capability needs a verified
   citation.
2. **Extract candidates from three sources** (`IdentifyingArchChar.md:10`):
   domain concerns (translate stakeholder language via the Table 5-1 map —
   "time to market" → agility/testability/deployability), explicit
   requirement statements (user counts → scalability; bursts → elasticity),
   and implicit domain knowledge (availability, security, and
   domain-specific ones — say which domain fact implies each). Mark each
   candidate `explicit` / `implicit`.
3. **Apply the 3-part test to every candidate**
   (`ArchitecturalChar.md:19-43`): (a) nondomain design consideration,
   (b) requires structural support — ask "can design alone satisfy it, or
   does the structure have to change?", (c) critical to success. Candidates
   failing (b) get demoted to "handle via design" — listed, not dropped
   silently. Failing (c) → "Others Considered".
4. **Decompose composites** (`MeasuringAndGoverning.md:24`): agility,
   user satisfaction, and friends have no direct measure — replace each with
   its measurable constituents before prioritizing. Flag any false
   equivalence (e.g., agility ≡ time to market) explicitly.
5. **Give every survivor an objective definition + a measure**
   (`MeasuringAndGoverning.md:26-54`): what number, measured how
   (operational / structural / process measure), with the caveat class
   (averages hide outliers — pair max with mean; coverage without assertions
   is gamed). These become fitness-function seeds for arch-validate.
6. **Draft the worksheet** (`IdentifyingArchChar.md:207-218`): ≤7 driving
   characteristics (pull implicit ones into the driving column only when
   they need special design attention), an "Others Considered" list, and a
   *proposed* top-3 with the reasoning. Also run the elimination probe: "if
   we had to drop one, which — and why?" Write to
   `{{worksheet_home}}<target>/characteristics-worksheet.md`.
7. **Check for divergent clusters** (`ArchCharScope.md:112-126`): if the
   candidates form groups that counteract each other (public-facing
   scale/availability vs back-office security/auditability), record the
   clusters — that's arch-style's quantum input. One-set-for-the-whole-system
   is the "fatal flaw" (`ArchCharScope.md:8`); don't average clusters away.

## Human gate

The human is the domain stakeholder panel. They confirm or amend:
(a) the ≤7 driving list, (b) the **top 3, in any order** — never ask them to
fully rank all seven ("a fool's errand," `IdentifyingArchChar.md:218`),
(c) any demotions from step 3. A rejected framing loops back to step 2 with
the correction recorded in the worksheet. Advance → **arch-components** (or
arch-style if components already exist; the two may run in parallel).

## Constraints

- **Fewest possible, not most** (`ArchitecturalChar.md:43`): each supported
  characteristic adds complexity; overspecifying is as damaging as
  underspecifying. Trying to support everything = generic-architecture
  antipattern (`ArchitecturalChar.md:254`).
- Characteristics interact synergistically — note the tension pairs in the
  worksheet (security↔performance, deployability↔auditability).
- Disambiguate contested terms in-line (interoperability vs compatibility,
  availability vs reliability, the two learnabilities) — the org's ubiquitous
  language starts in this worksheet (`MeasuringAndGoverning.md:26`).
- "There are no wrong answers in architecture, only expensive ones."
