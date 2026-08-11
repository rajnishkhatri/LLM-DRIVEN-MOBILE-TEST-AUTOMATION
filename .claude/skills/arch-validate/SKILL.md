---
name: arch-validate
type: skill
description: >-
  Architect workflow stage 6: validate and govern the architecture — final
  diagram set (C4-flavored), the nine-intersections alignment checklist
  (implementation, infrastructure, data topology, engineering practices,
  team topology, integration, enterprise, business, GenAI), and governance
  wiring (fitness functions from ADR Compliance sections, team checklists).
  Use when a design "looks done", before implementation starts, when the
  user asks "is this aligned / production-ready / governable", or
  periodically on a live system. Do NOT use for finding risks by scoring
  (arch-risk), making new decisions (arch-decide), or drawing exploratory
  sketches mid-design (each stage owns its own working diagrams).
---

# Stage 6 — Validate, Diagram, Govern

> Binding: `.arch/binding.toml` (see arch-lifecycle). Methodology:
> `{{methodology_source}}` ch23 (`diagramming-arch.md`), ch26
> (`arch-intersection.md`), ch6 governance, ch24 checklists. Checklist:
> `references/intersections-checklist.md`. Diagram rules:
> `../arch-lifecycle/references/diagram-rules.md`.

Micro-loop: agent audits alignment and produces the deliverables → human
signs off per intersection → unresolved misalignments route back to the
owning stage (or spawn an ADR).

## Agent work

1. **Assemble the diagram set** with representational consistency: context →
   container → component views in `{{diagram_notation}}`, passing the six
   guideline checks (titles, lines with solid=sync/dotted=async, consistent
   shapes, labels, color+iconography, keys). SLAs and quantum boundaries on
   the container view. Store beside the artifacts they depict.
2. **Walk the nine intersections** (`arch-intersection.md:12-37`) using the
   reference checklist. For each: aligned / misaligned / unknown — with
   evidence (kata mode: reasoned from the statement; review mode: verified
   citations, e.g., does the source tree actually mirror the logical
   components?). "Unknown" is a legitimate verdict that names what probe
   would resolve it. Misalignments get a severity and an owner-stage
   (wrong data topology → arch-style; component/code drift →
   arch-components + a fitness function here).
3. **Wire governance.** Collect every ADR Compliance section and the
   fitness-function seeds from the characteristics worksheet into a
   governance table: what's automated (tool + rule sketch — ArchUnit /
   NetArchTest / PyTestArch / TSArch per platform,
   `arch-intersection.md:71`), what's manual (cadence + owner), what's
   ungoverned (flagged). Where the workspace has a coding-rules catalog
   (e.g., `tooling/coding-rules-skill/references/rules-catalog.md` +
   `archunit-seeds.md` for the o1 pipeline), its `[CI]`-marked rules ARE
   governance-table rows — inventory them by rule ID (CR-xx) instead of
   re-deriving them, and flag any catalog rule with no live gate as
   ungoverned. Fitness functions are checklists-for-computers,
   not an ivory tower: developers must understand each one's purpose before
   it's imposed (`MeasuringAndGoverning.md:131-135`).
4. **Team checklists where they earn their keep** (`making-teams-effective.md:259-335`):
   code-completion, testing edge-cases, software-release. Rules: only for
   error-prone non-procedural processes; as small as possible; automate
   items out of them over time; QA-found bugs and failed deploys feed the
   corresponding checklist.
5. **Report.** One validation report: diagram set, intersections verdict
   table, governance table, open items routed by owner-stage. Kata mode:
   this is the kata's closing artifact — include a retrospective against
   the top-3 characteristics ("did the design actually serve them?").

## Human gate

Sign-off is per intersection, not global — a bare "looks good" doesn't
close nine axes. Misalignments the human accepts as-is become recorded,
priced exceptions (mini-ADR or a Consequences note on an existing one).
Advance → implementation / next iteration; recurring re-entry is expected
("creating **or validating** a software architecture,"
`arch-intersection.md:10`).

## Constraints

- No diagram ships that fails the misinterpretation test: "an easily
  misinterpreted diagram is worse than no diagram at all"
  (`diagramming-arch.md:114`).
- Structure must match code in review mode: logical components ↔ directory
  structure/namespaces is a checkable claim, not an aspiration
  (`arch-intersection.md:64`).
- "That's an implementation detail" is the second-most-dangerous sentence in
  architecture (`arch-intersection.md:43`) — implementation, infrastructure,
  and data are in scope here precisely because they sink architectures.
- Unknown unknowns doctrine: don't demand Big-Design-Up-Front completeness;
  validate iteratively and favor evolvability
  (`arch-intersection.md:185-191`).
