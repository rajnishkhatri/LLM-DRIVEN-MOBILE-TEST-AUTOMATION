# SELF-AUDIT — <view name>

Rendered: `<view-id>.svg` + `<view-id>@2x.png` + `proofs/<view-id>-gray.png`
Linter: paste the `lint_diagram.py` output line here.

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Titles | PASS/FAIL | every node/boundary/view titled |
| 2 | Lines (sync solid / async dashed / no double-heads) | PASS/FAIL | linter `no-double-arrow`: … |
| 3 | Shapes reserved & consistent | PASS/FAIL | linter `shape-kind`: … |
| 4 | Labels verbatim + honesty tags | PASS/FAIL | linter `verbatim-labels`: N/N |
| 5 | Colour never alone (grayscale legible) | PASS/FAIL | `proofs/<view-id>-gray.png` attached; legible? |
| 6 | Keys / registers as real tables | PASS/FAIL | … |
| 7 | Representational consistency (locator caption + accent) | PASS/FAIL | … |
| 8 | No invented facts | PASS/FAIL | linter `forbidden-facts`: none |

## Fonts

State whether fonts are embedded or converted-to-`<text>`-with-web-safe-fallback.

## Could not render

List anything the brief asked for that you could not produce, and why. If a
required fact was missing, say you stopped and asked rather than inventing it.
