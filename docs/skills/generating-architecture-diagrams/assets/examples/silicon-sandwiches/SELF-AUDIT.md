# SELF-AUDIT — Silicon Sandwiches, Context view (01-context)

Rendered: `01-context.svg` + `01-context@2x.png` + `proofs/01-context-gray.png`
Linter: `PASS  01-context: 21/21 canvas labels verbatim, 14 relocated facts, 21 <text> elements, 0 failure(s)`

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Titles | PASS | all 11 nodes titled; view title in the D2 header comment |
| 2 | Lines (sync solid / async dashed / no double-heads) | PASS | linter `no-double-arrow`: clean; 9 solid + 1 dashed (dispatch notification) |
| 3 | Shapes reserved & consistent | PASS | linter `shape-kind`: clean; actors=pill, system=rect(2px), externals=EXT double-border; no cylinder (none needed at Context) |
| 4 | Labels verbatim + honesty tags | PASS | linter `verbatim-labels`: 21/21 canvas; honesty tags relocated into the detail table ("PROVISIONAL", "risk cells 4 and 5 remain HIGH", "needs-input:data-constraints") |
| 5 | Colour never alone (grayscale legible) | PASS | `proofs/01-context-gray.png` — pills, EXT double-borders, and dashed async edge all readable desaturated |
| 6 | Keys / registers as real tables | N/A | Context view is a single diagram; the shared key panel is a separate deliverable (not part of this slice) |
| 7 | Representational consistency (locator caption + accent) | PARTIAL | the caption ("opened in the Container view") is carried on the SYS node; the accent-stroke tie-in belongs to the Container view, not rendered in this single-view slice |
| 8 | No invented facts | PASS | linter `forbidden-facts`: no AWS/Azure/GCP/region/Redis/Kafka/Postgres/99.99 patterns |

## Fonts

D2 renders labels as real `<text>` elements (21 of them) with the built-in
Source Sans Pro at `font-size:16px`. Text is searchable/translatable/editable —
not outlined paths or raster.

## Could not render

This is a **representative slice** (Context view only), authored to prove the
IR → D2 → SVG → @2x PNG → grayscale → lint pipeline end-to-end. The full
Silicon Sandwiches deliverable (Container view, Component view, SLA register,
async register, key panel, poster) is out of scope for this proof and is
specified in
`.arch/components/silicon-sandwiches/designer-agent-prompt.md`. Nothing in the
Context view was blocked or required inventing a fact.
