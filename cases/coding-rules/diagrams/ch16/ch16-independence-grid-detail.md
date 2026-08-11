# Ch.16 Independence - layers x use-cases grid (illustrative order system) — detail tables

> An illustrative order-processing system decomposed along BOTH axes at once: horizontal layers (UI / application rules / domain rules) and vertical use cases (AddOrder, DeleteOrder, TrackOrder). The TrackOrder column is NEW - it adds a fresh column of components and touches none of the existing cells. No edges cross columns: use cases are decoupled from each other. No edges cross rows outside a column: layers are decoupled from each other. This is the grid Clean Architecture Ch.16 asks for.

**Locator:** this view opens `ORDSYS` from `01-context`. It is a **completeness reference** at this grain.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 1 | A_UI | layer: UI (changes when UX changes) use case: AddOrder |
| 2 | A_APP | layer: application-specific rules (input validation) use case: AddOrder |
| 3 | A_DOM | layer: application-independent domain rules (pricing) use case: AddOrder |
| 4 | D_UI | layer: UI use case: DeleteOrder |
| 5 | D_APP | layer: application-specific rules (cancellation workflow) use case: DeleteOrder |
| 6 | D_DOM | layer: domain rules (cancellation policy) use case: DeleteOrder |
| 7 | T_UI | layer: UI use case: TrackOrder (NEW column) new file - no existing component edited |
| 8 | T_APP | layer: application-specific rules (query validation) use case: TrackOrder (NEW column) new file - no existing component edited |
| 9 | T_DOM | layer: domain rules (shipment lookup) use case: TrackOrder (NEW column) new file - no existing component edited |

## Not shown for brevity

- **Database access layer** — each use case would also own a thin DB-access component; omitted here to keep the grid legible - the decoupling lesson is unchanged

## Key

- rectangle = a grouping of code inside a container (C4 component)
- module-c colour = the same module tracked by colour across every view
- solid arrow = synchronous call
- `[Type]` under a name = the element's C4 type (container/component)

