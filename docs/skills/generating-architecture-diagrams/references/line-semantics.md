# Line semantics

The one near-universal standard in architecture diagrams: **solid = synchronous,
dashed = asynchronous** (Ch. 23, `diagram-rules.md`). This family holds it
strictly.

| IR edge `kind` | Line | Meaning |
|---|---|---|
| `sync` | Solid arrow | Synchronous request/response |
| `async` | Dashed arrow (`style.stroke-dash: 3`) | Asynchronous — event / notification |

## Rules

- **Arrowhead shows direction of information flow *at initiation*.** Responses
  are implied and never drawn.
- **No double-headed arrows anywhere.** The transformer only emits `->`
  (single-headed). The linter (`no-double-arrow` check) fails any SVG
  connection with a `marker-start`, or any D2 source using `<->` / `<-`.
- **Pending-ness is carried by text tags only, never by line style.** A dashed
  line means async and nothing else — never "proposed" or "not yet built".
  Proposed/provisional state is written into the label (see
  [honesty-tags.md](honesty-tags.md)).

## Async edge chips (optional)

At the Component level, asynchronous edges can carry an `A1`..`An` chip so a
companion register can enumerate their transport semantics. Encode the chip in
the edge label text (`"A1: order accepted (async)"`) so it is verbatim-checked
like any other label.
