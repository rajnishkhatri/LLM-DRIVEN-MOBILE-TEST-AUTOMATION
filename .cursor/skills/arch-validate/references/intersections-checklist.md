# The nine intersections checklist

From `cases/ArchitectureBook/arch-intersection.md` (ch26). Verdict per row:
aligned / misaligned (severity + owner-stage) / unknown (+ resolving probe).

| # | Intersection | Check question | Sub-checks |
|---|---|---|---|
| 1 | **Implementation** (`:12,45-94`) | Is the implementation aligned with operational characteristics, constraints, and internal structure? | (a) implementation choices serve the *same goals* as the architecture (the 80k-user replicated-cache OOM: "both teams made good decisions, but in service of different goals," `:60`); (b) source tree mirrors logical components — governable via ArchUnit / ArchUnitNet / NetArchTest / PyTestArch / TSArch (`:71`); (c) constraints identified, communicated, and governed (`:80-94`) |
| 2 | **Infrastructure** (`:15,96-110`) | Does deployment infrastructure support the operational concerns? | "Can support" ≠ "will" (Pets.com, `:100`); cross-region/zone deployment can cancel cache benefits; co-location boosts performance but hurts FT/availability/elasticity (`:108`) |
| 3 | **Data topology** (`:18,112-137`) | Does the data topology match the style? | monolithic vs domain vs DB-per-service ↔ style table; DB-type superpowers match the system's (scalability/elasticity → key-value, columnar); data structure fit (key-value pairs in an RDBMS = misalignment; polyglot when feasible); read/write priority: write-heavy → columnar, read-heavy → key-value/document/graph, balanced → relational/NewSQL (`:137`) |
| 4 | **Engineering practices** (`:21,139-155`) | Do build/test/deploy practices match the style? | microservices + waterfall/manual-ops = failure mode; migration needs tight feedback loops, Strangler pattern, feature toggles (`:145`); fitness functions in place for the composite chain (time to market → agility → maintainability+testability+deployability, `:155`) |
| 5 | **Team topology** (`:24,157-163`) | Is team partitioning aligned with architecture partitioning? | domain-partitioned cross-functional teams ↔ domain-partitioned styles; UI/backend/DB teams ↔ layered; business-function + data-sync teams ↔ space-based (`:161`) |
| 6 | **Systems integration** (`:27,165-169`) | Do integrations preserve each side's characteristics? | four checks (`:169`): protocols; contract types; characteristics compatibility (callee scales/performs to caller's needs?); does the integration preserve each system's quantum? |
| 7 | **Enterprise** (`:30,171-175`) | Aligned with org frameworks, standards, security practices? | else "a failed 'one-off' solution and scrapped" (`:175`) |
| 8 | **Business environment** (`:33,177-193`) | Domain-to-architecture isomorphism with the business's actual posture? | cost-cutting ↛ microservices/space-based; M&A-expansion ↛ rigid monoliths (`:181`); design for unknown unknowns via evolvability, not BDUF (`:187`); residuality lens: business changes as stressors, architecture answers as residues (`:193`) |
| 9 | **Generative AI** (`:36,195-219`) | Does LLM usage (in the system) stay swappable and evaluated? | abstraction + modularity to swap LLMs; rails + evals; observability for comparing engines (Langfuse-class tooling, `:203`) |

## Governance instruments to wire (ch6 + ch24)

- **Fitness functions**: from ADR Compliance sections + worksheet measure
  definitions. Families: metrics, monitors, unit-test libraries, chaos
  engineering (`MeasuringAndGoverning.md:74`); production governance à la
  Simian Army — conformity/security/janitor checks (`:172-176`). Threshold
  + CI wiring per function; consent rule before imposing (`:131-135`).
- **Checklists** (`making-teams-effective.md:259-335`): code-completion
  ("definition of done"), testing edge-cases (QA-found bug ⇒ new entry),
  software release (failed deploy ⇒ root cause ⇒ new entry). Keep small;
  automate items out; "the obvious stuff is what usually gets missed."
- **Metric-gaming watch**: assertion-free tests against coverage targets
  (`MeasuringAndGoverning.md:170`); fitness functions "prevent accidental
  lapses," not dedicated rule-breakers.
