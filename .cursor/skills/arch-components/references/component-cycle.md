# Component cycle instruments

Distilled from `cases/ArchitectureBook/Modularity.md` (ch3) and
`ComponentBased.md` (ch8).

## The cycle (Figure 8-6, `ComponentBased.md:55-62`)

identify initial core components → assign user stories → analyze roles &
responsibilities → analyze architecture characteristics → restructure →
(loop). Triggers: greenfield, or any feature addition/change.

## Identification approaches (`ComponentBased.md:66-155`)

| Approach | When | Mechanics | Notes |
|---|---|---|---|
| Workflow | default for request/journey-shaped systems | map major happy-path workflows; a component per step; steps may reuse components | fewer components than Actor/Action |
| Actor/Action | multiple actors; good generic default | list actors (the **system is always an actor**) → major actions → components per action, with reuse | more components |
| Entity Trap | **never** | entities → `<Entity> Manager` components | tells below |

**Entity Trap tells** (`:142-155`): suffix `Manager/Supervisor/Controller/
Handler/Engine/Processor`; name yields a tautology ("manages orders");
component becomes a dumping ground; coarse-grained, hard to maintain/test/
deploy. Escape hatch: truly CRUD-based system → CRUD framework / low-code,
"doesn't need an architecture" (`:155`).

## Sizing tells

**Too big** — conjunction test on the role statement ("and", "also", "as
well as", comma chains, `:228`); directory-volume test (`:230`); divergent
characteristics within one component (`:260`); drift over time even with
interrelated operations (`:204`).
**Too small / don't split** — splitting a cohesive module only adds coupling
(`Modularity.md:52`); too-few-operations test and knowledge-dependency test
(`Modularity.md:112-116`); an intermediary that leaves efferent coupling
unchanged is not an improvement (`ComponentBased.md:314`).
**Growth test** — expected to grow a lot? pre-plan extraction
(`Modularity.md:114`).

## Cohesion scale, best → worst (`Modularity.md:56-77`)

functional → sequential → communicational → procedural → temporal → logical
(StringUtils-style grab bags) → coincidental. Target: functional.
LCOM finds *structural* lack of cohesion only — it cannot judge logical fit
(`Modularity.md:143`).

## Coupling metrics (`Modularity.md:147-195`, `ComponentBased.md:277-295`)

- **Afferent (CA)** = incoming dependencies; **efferent (CE)** = outgoing.
- **Instability** I = CE / (CE + CA) — high I breaks easily when changed.
- **Abstractness** A = abstract / (abstract + concrete).
- **Distance from main sequence** — balance of A and I; Zone of Pain
  (concrete + stable), Zone of Uselessness (abstract + unstable).
- **Temporal coupling**: timing/transaction dependencies — invisible to
  tools; found via design docs or error conditions (`ComponentBased.md:295`).

## Law of Demeter procedure (`ComponentBased.md:297-321`)

Enumerate what the component *knows* (knowledge ⇒ coupling, even without
responsibility) → test each knowledge item for deferability (would pushing
it down actually reduce CE?) → push transferable knowledge to the component
that owns the data → **account honestly**: Demeter redistributes coupling
system-wide, it rarely reduces the total.

## Connascence (refactoring vocabulary, `Modularity.md:201-305`)

Static (prefer): Name → Type → Meaning/Convention → Position → Algorithm.
Dynamic (avoid): Execution → Timing → Values (distributed transactions!) →
Identity. Rules: convert strong → weak (Weirich's Rule of Degree); the
greater the distance between elements, the weaker the connascence must be
(Rule of Locality); minimize connascence crossing encapsulation boundaries,
maximize it within (Page-Jones). Review-comment idiom: "This is Connascence
of Meaning; refactor to Connascence of Name."

## Worked exemplars in the bundle

- Order-entry Workflow + Actor/Action mappings: `ComponentBased.md:85-136`.
- Role-statement split (Order Placement 8→5 responsibilities + 3 new
  components): `ComponentBased.md:206-254`.
- Kata worked passes: sealed in `worked-answers.SEALED.md` — open only
  after your own component analysis is written (SD1 class, 2026-07-25).
