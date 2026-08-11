# Reserved shape vocabulary

The shape vocabulary is **reserved and consistent across every view**. A shape
means exactly one kind of thing; a kind always renders as the same shape. This
is enforced in code (`scripts/ir_to_d2.py` maps IR `kind` → D2 class from
`references/d2-classes.d2`), so it cannot drift — do not restyle a node inline.

| IR `kind` | Shape | D2 class | Notes |
|---|---|---|---|
| `actor` | Stadium / pill outline | `actor` | A person. High border-radius makes the pill. |
| `system` | Plain rectangle | `system` | The whole system. On a Context canvas it is the heaviest element (2px stroke). |
| `container` | Plain rectangle | `container` | A container or component (lighter than the system box). |
| `component` | Plain rectangle | `container` | Same shape as container; the view level distinguishes them. |
| `external` | Double-bordered rectangle, label prefixed `EXT:` | `external` | An external system. The transformer adds the `EXT:` prefix. |
| `datastore` | Cylinder | `datastore` | **A datastore ONLY. Never use a cylinder for anything else.** |
| `infra` | White rectangle, dark stroke | `infra` | Deployment infrastructure (e.g. load balancer). |
| `boundary` | Dashed-outline container box | `boundary` | A boundary/grouping — never a node. |
| `process` | Dash-bordered rectangle | `process` | A runtime **process**, not a deployable artifact. The dash border carries the meaning in grayscale. |
| `not-a-component` | Hexagon | `not-a-component` | An element an ADR records is **deliberately not a component** (e.g. a library). The distinct shape says "not one of the boxes". |

## Module / domain colours (colour-tracking across views)

For a multi-module set, give each module a locked domain colour and apply the
**same** one in every view that contains it, so a reader tracks the module
across the zoom chain by eye (see [readability.md](readability.md) §7). The
classes `module-a` / `module-b` / `module-c` / `module-d` in
[d2-classes.d2](d2-classes.d2) carry pale-gold / green / blue / rose. Always
pair the colour with the module name in the label so the tracking survives
grayscale.

## Families (colour overlays, never the only channel)

A `family` on a node overlays a fill but keeps the kind's shape, so the meaning
survives grayscale:

| `family` | Fill meaning | Still shaped as |
|---|---|---|
| `evidence-gap` | Unresolved production evidence (provisional vendor, pending contract) — orange | its kind (usually `external`, double-bordered) |
| `faded` | Location-only element: reappears in a deeper view for context, not as subject — muted | its kind |

## The one rule that catches the common mistake

Cylinders are reserved for datastores; external systems use the `EXT:`
double-bordered rectangle. This corrects the frequent error of drawing an
external system as a cylinder. The linter (`shape-kind` check) fails a diagram
that renders a cylinder with no datastore in the IR.
