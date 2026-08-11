# Characteristics catalog + tests + measures

Distilled from `cases/ArchitectureBook/` ch4–6. Citations are `file.md:line`.

## The 3-part test (`ArchitecturalChar.md:19`)

An architecture characteristic must: **(1)** specify a nondomain design
consideration, **(2)** influence some structural aspect of the design,
**(3)** be critical or important to success. Operative question for (2):
"Can the architect implement it via design, or does it require special
structural consideration?" — security usually passes via design in a
monolith; scalability cannot ("no amount of clever design will allow a
monolithic architecture to scale beyond a certain point,"
`ArchitecturalChar.md:38`). Operational characteristics most often need
structural support (`:40`).

## Domain-concern translation (Table 5-1, `IdentifyingArchChar.md:18-38`)

| Domain concern | Characteristics |
|---|---|
| Mergers & acquisitions | interoperability, scalability, adaptability, extensibility |
| Time to market | agility*, testability, deployability |
| User satisfaction | performance, availability, fault tolerance, testability, deployability, agility*, security |
| Competitive advantage | agility*, testability, deployability, scalability, availability, fault tolerance |
| Time and budget | simplicity, feasibility |

\* composite — decompose before use. Known decompositions: agility →
modularity + deployability + testability (`MeasuringAndGoverning.md:22`,
`ArchCharScope.md:122`).

## Category tables (ch4)

**Operational** (Table 4-1, `ArchitecturalChar.md:59-87`): availability,
continuity (DR), performance, recoverability, reliability/safety,
robustness, scalability.
**Structural** (Table 4-2, `:95-127`): configurability, extensibility,
installability, leverageability/reuse, localization, maintainability,
portability, upgradeability.
**Cloud** (Table 4-3, `:133-149`): on-demand scalability, on-demand
elasticity, zone-based availability, region-based privacy/security.
**Cross-cutting** (Table 4-4, `:157-193`): accessibility, archivability,
authentication, authorization, legal, privacy, security, supportability,
usability.
Any list is necessarily incomplete (`:195`); ISO 25010 category list at
`:199-236` (book excludes "functional suitability" — it's requirements, not
architecture).

**Disambiguations** (`:195-197`): interoperability = ease of integration
(published APIs) vs compatibility = industry/domain standards; learnability
(users learn) vs learnability (system self-optimizes); available ≠ reliable
(IP delivers but reorders).

## Explicit vs implicit (`ArchitecturalChar.md:45`)

Explicit = stated in requirements. Implicit = necessary but unstated
(availability, security, and per-domain ones — e.g., data integrity in
medical devices). Deriving implicit ones is the analysis-phase job. Kata
tell: user counts imply scalability; mealtime/burst domains imply elasticity
even when unstated (`IdentifyingArchChar.md:130-144`).

## The worksheet procedure (`IdentifyingArchChar.md:201-218`)

≤7 driving-characteristic slots (six or eight also fine — the point is a
short list); a column of common implicit ones to "pull in" only when they
need special design; an Others-Considered overflow; stakeholders check the
**top 3 in any order**. Full-ranking attempts waste time and burn consensus.
Elimination probe: "which would you cull first?" — usually an explicit one;
implicit ones support general success (`:197`).

## Measures (ch6)

| Kind | Examples | Caveats |
|---|---|---|
| Operational (`MeasuringAndGoverning.md:28-34`) | mean + **max** response time; scale-over-time statistical models with alarm-on-deviation; performance budgets (first contentful paint, first CPU idle) | averages hide the 1%-tail (`:30`) |
| Structural (`:36-44`) | cyclomatic complexity; cycle detection (JDepend); distance-from-main-sequence with threshold (ideal 0.0, tolerance ~0.5, project-dependent); ArchUnit/NetArchTest layer rules | CC can't split essential vs accidental complexity; code metrics can't see the database (`ArchCharScope.md:10`) |
| Process (`:46-54`) | code coverage; deployment success %, duration, deploy-caused bugs | 100% coverage with weak assertions is gamed — require ≥1 assertion per test (`:170`) |

**Fitness function** = "any mechanism that provides an objective integrity
assessment of some architecture characteristic or combination" (`:72`).
Authoring loop: define desirable relationship → write verification → wire
into continuous build → set threshold. Consent rule: developers must
understand a fitness function's purpose before it's imposed (`:133`).

## Antipatterns to name when seen

- **Generic architecture** — supporting every characteristic (`ArchitecturalChar.md:254`).
- **One-set-for-the-whole-system** — the "fatal flaw"; check for clusters (`ArchCharScope.md:8`).
- **Composite tunnel-vision** — optimizing one constituent of a composite
  ("fast but never available," the end-of-day-pricing example,
  `IdentifyingArchChar.md:44-58`).
- **Definition drift** — departments disagreeing on "performance"; fix with
  ubiquitous language (`MeasuringAndGoverning.md:19-26`).
