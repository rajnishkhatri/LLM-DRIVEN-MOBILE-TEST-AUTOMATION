# Diagram rules for arch-* artifacts

Distilled from `cases/ArchitectureBook/diagramming-arch.md` (ch23). Applies to
every diagram an arch-* skill emits (default notation: `{{diagram_notation}}`,
C4-flavored).

## Representational consistency (the governing rule)

Always show where a part sits in the whole **before** zooming into it
(`:14`): overview topology → the relationship between it and the sub-part →
the sub-part. Never present a fragment cold. "Showing a portion without
indicating its place within the overall architecture will confuse viewers."

## C4 levels (`:52-68`)

Context (system + users + external dependencies) → Container (deployment
boundaries; the ops/architect meeting point) → Component (the architect's
view — arch-components' output lives here) → Class (only if needed; plain UML
class diagrams survive). Use the level that matches the stage; risk storming
needs at least a Container-level diagram as input.

## The six guideline checks (`:79-114`)

1. **Titles** on every element unless truly well-known to the audience.
2. **Lines**: thick and visible; arrows show direction of information flow.
   **Solid = synchronous, dotted = asynchronous** — the one near-universal
   standard (`:91`). Be consistent with arrowhead semantics.
3. **Shapes**: no industry standard; keep a consistent personal/org set.
   Book's convention: 3-D boxes = deployable artifacts, rectangles =
   containers, cylinders = databases (`:97`).
4. **Labels** on every item where any ambiguity is possible.
5. **Color**: use it to distinguish artifacts, but never color alone —
   pair with unique iconography/shape for accessibility (`:110`).
6. **Keys**: if any shape could be misread, add a key. "An easily
   misinterpreted diagram is worse than no diagram at all" (`:114`).

## Fidelity discipline

Low-fidelity first; iterate before investing in polish (**Irrational
Artifact Attachment** antipattern, `:27` — ephemeral early artifacts prevent
over-attachment). Standards with exceptions: "establish standards but allow
reasonable exceptions" (`:118`).

## Mermaid conventions for this family

- `flowchart` or `graph` for topology; `-->` sync, `-.->` async.
- One diagram per file section; title as a markdown heading directly above.
- Quantum boundaries as `subgraph` blocks; SLAs/ratings as node annotations
  (risk storming expects SLAs on the diagram, `arch-risk.md:197`).
