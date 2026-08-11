---
name: arch-style
type: skill
description: >-
  Architect workflow stage 3: quantum scoping and architecture style
  selection — the join point of characteristics + components. Use when the
  user asks "monolith or distributed", "which architecture style", "how many
  quanta", "sync or async between these services", or wants a style
  trade-off comparison. Requires a characteristics worksheet (arch-
  characteristics) and benefits from a component table (arch-components).
  Do NOT use to derive characteristics or components, to write the ADR
  itself (arch-decide records the outcome), or for intra-service design
  patterns.
---

# Stage 3 — Quanta & Style Selection

> Binding: `.arch/binding.toml` (see arch-lifecycle). Methodology:
> `{{methodology_source}}` ch7 + ch9–19. Reference:
> `references/style-selection.md` (includes known gaps in the bundle's
> ratings data). Trade-off matrix: `../arch-lifecycle/references/laws.md`.

Micro-loop: agent runs the four determinations and presents a scored
comparison of 2–3 candidate styles → human picks → outcome flows to
arch-decide as ADR(s).

## Agent work

1. **Confirm decision-readiness** (`choosing-appropriate-arch.md:44-68`):
   domain understood, characteristics worksheet on file, data architecture
   constraints, cloud/on-prem intent, organizational factors (budget, M&A
   posture), process/team maturity. Missing inputs are named, not assumed —
   each becomes a `needs-input` tag on affected candidates.
2. **Determination 1 — one quantum or many?** Cluster the worksheet's
   characteristics (arch-characteristics step 7 output). One coherent set →
   monolithic family; multiple counteracting sets → distributed
   (`ArchCharScope.md:92-94`). Apply the coupling test to proposed
   boundaries: "two things are coupled if changing one might break the
   other" — shared database ⇒ same quantum (`ArchCharScope.md:52`). Emit the
   quantum map (clusters → dotted boundaries on the component diagram).
3. **Determination 2 — where does data live?** Monolith → single relational
   DB is the default assumption to challenge, not a law; consider splitting
   tables along domain components to ease future migration
   (`choosing-appropriate-arch.md:93,116`). Distributed → which services
   persist, and how workflows flow through the data.
4. **Determination 3 — sync or async?** Default synchronous, async only when
   necessary (`choosing-appropriate-arch.md:98-102`) — and check the
   feedback loop: synchronous calls between mismatched quanta collapse them
   into one and inherit the slower partner's characteristics
   (`ArchCharScope.md:72-74`, Dynamic Quantum Entanglement).
5. **Score candidate styles.** Shortlist 2–3 styles consistent with
   determinations 1–3; build the trade-off matrix (laws.md procedure) with
   the **driving characteristics as rows**, using the reference's
   prose-recovered ratings and when-to-use/when-not tables. Check
   domain/architecture isomorphism (customization-shaped domain →
   microkernel; discrete-processor-shaped → space-based; semantically
   coupled multi-page-form domain → *not* microservices,
   `choosing-appropriate-arch.md:70-85`). For distributed candidates, walk
   the 11 fallacies as a risk pre-scan and note which ones this design will
   pay for.
6. **Name the least-worst pick with its losing alternatives.** Output =
   chosen style (+ hybridizations), quantum map, per-quantum communication
   type, and the list of decisions requiring ADRs (style choice always;
   plus any data-topology and sync/async calls with significant
   trade-offs). The follow-on list must include edge/access topology:
   the component stage deliberately excludes UIs, so unless client/UI
   structure per actor class and the API/edge layer are surfaced here as
   determinations or ADR candidates, no later stage will (the GGG
   test-drive's one genuine miss, 2026-07-25). Write to
   `{{worksheet_home}}<target>/style-decision.md`.
   Only AFTER all determinations are written, open
   `references/worked-answers.SEALED.md` and cross-check as a self-check
   diff. Never open it earlier: it holds the book's answers to its own
   katas and anchors the analysis (SD1, Silicon Sandwiches test-drive
   2026-07-24; recurred 2026-07-25 when the answers still lived inside
   the step-0 reference — that is why they are sealed in a file no
   earlier step names). If sealed content somehow entered context early,
   disclose it prominently in the artifact.

## Human gate

Human confirms each determination separately — quantum count, data
placement, communication types, style — not one bundled "yes"
(conflated-axes rule). If the human's pick contradicts a determination
(e.g., microservices with one shared DB), surface the contradiction as a
named antipattern with its cost, then defer: it's their call, recorded with
consequences in the ADR. Advance → **arch-decide** (mandatory), then
**arch-risk**.

## Constraints

- Style follows characteristics — never lead with a style. "The real
  differences between styles concern not the domain, but how well each style
  supports various architectural characteristics"
  (`choosing-appropriate-arch.md:52`).
- Monolith bias when a single quantum suffices: it "reduc[es] the number of
  subsequent choices" (`ArchCharScope.md:94`); modular monolith is the
  book's recommended starting point when direction is unclear
  (`Modular-monolith-arch.md:229`).
- Fashion check (`choosing-appropriate-arch.md:13-38`): note when a
  candidate is favored because it's current fashion rather than fit.
- The bundle's star-rating figures are missing (images) — say so when a
  rating is prose-reconstructed vs unavailable; never invent stars.
