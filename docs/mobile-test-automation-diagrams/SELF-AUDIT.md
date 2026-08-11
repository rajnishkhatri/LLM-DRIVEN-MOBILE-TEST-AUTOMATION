# SELF-AUDIT — Mobile Test Automation LLM Pipeline diagram set

Rendered: `docs/mobile-test-automation-diagrams/` via
`docs/skills/generating-architecture-diagrams/scripts/render.sh`
Mode: **improve-existing** (topology ingested from
`docs/architecture/components/mobile-test-automation/diagram-set.md` rev 4;
zero edges added/removed; grounded in
`docs/architecture/components/mobile-test-automation/logical-components.md` rev 3)
Date: 2026-07-28

## Linter results

| View | Result |
|---|---|
| `01-context` | `PASS  01-context: 18/18 canvas labels verbatim, 18 relocated facts, 18 <text> elements, 0 failure(s)` |
| `02-container` | `PASS  02-container: 16/16 canvas labels verbatim, 29 relocated facts, 31 <text> elements, 0 failure(s)` |
| `03-container-module-wiring` | `PASS  03-container-module-wiring: 19/19 canvas labels verbatim, 37 relocated facts, 41 <text> elements, 0 failure(s)` |
| set `03-container-module-wiring` + 4 overlays | `PASS  set 03-container-module-wiring: 4 overlays, 23 primary edges, 0 failure(s)` |
| `04-container-evidence` | `PASS  04-container-evidence: 13/13 canvas labels verbatim, 6 relocated facts, 13 <text> elements, 0 failure(s)` |
| `05-container-credentials` | `PASS  05-container-credentials: 11/11 canvas labels verbatim, 6 relocated facts, 11 <text> elements, 0 failure(s)` |
| `06-container-async` | `PASS  06-container-async: 12/12 canvas labels verbatim, 6 relocated facts, 11 <text> elements, 0 failure(s)` |
| `07-component` | `PASS  07-component: 24/24 canvas labels verbatim, 59 relocated facts, 59 <text> elements, 0 failure(s)` |
| set `07-component` + 4 overlays | `PASS  set 07-component: 4 overlays, 35 primary edges, 0 failure(s)` |
| `08-component-screening` | `PASS  08-component-screening: 10/10 canvas labels verbatim, 5 relocated facts, 9 <text> elements, 0 failure(s)` |
| `09-component-provenance` | `PASS  09-component-provenance: 18/18 canvas labels verbatim, 16 relocated facts, 18 <text> elements, 0 failure(s)` |
| overlays module-a/b/c/unclustered + structural/provenance/model-call/external-boundary | all PASS |

## Correctness checklist

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Titles | PASS | every node titled; view titles in D2 header + `view.md` |
| 2 | Lines (sync solid / async dashed / no double-heads) | PASS | linter clean; thick `CV → IM` entanglement (`stroke-width: 4`, kind `entangled`) |
| 3 | Shapes reserved & consistent | PASS | actors=pill, system/container/component=rect, EXT double-border, cylinder=datastore only, EXEC=`process`, LIB=`not-a-component` hexagon |
| 4 | Labels verbatim + honesty tags | PASS | `WORKING ASSUMPTION`, `BINDING PROBE-PENDING`, `PENDING`, `STUBBED IN SPINE`, `SLA: UNKNOWN (pending)`, `TECH: UNKNOWN` in detail tables |
| 5 | Colour never alone (grayscale legible) | PASS | `proofs/*-gray.png` for all primaries + overlays |
| 6 | Keys / registers as real tables | PASS | auto Key in each `*-detail.md` / `.view.md`; external-edge / async / provenance registers remain markdown tables in `diagram-set.md` |
| 7 | Representational consistency | PASS | C2a `opens: SYS` from `01-context`; C2b `opens: APP` from `02-container`; C3a `opens: APP`; overlays declare `subset:` of their base |
| 8 | No invented facts | PASS | linter `forbidden-facts` clean; Postgres retained only as documented WORKING ASSUMPTION |

## Readability self-audit (readability.md §9)

| Check | Result |
|---|---|
| One question per view | PASS — nine intentional views (C1–C3c) plus density-triggered C2b by-module and C3a by-theme overlays |
| Short labels + detail tables | PASS — heavy ADR/E-fact/M-rule text relocated; groundedness checked |
| No collisions on dense views | PASS — C2a/C2b/C3a use numbered edge refs; dense sets decompose |
| Locators | PASS — non-context views carry locator captions (`opens` / `completeness`) |
| Colour tracking | PASS — module-a/b/c locked across C2b–e and C3a–c |
| Overlay parity | PASS — set-level lint for C2b and C3a |

## Misinterpretation test (residual)

The fifteen residual risks in `diagram-set.md` §5 still apply; this render
does not close stage-5 probes (M1/M4/M5/M7/M33/ADR 0011). Representation
fixes that reduce skim risk:

- ENV/Q1 no longer appear as free-floating boxes (facts in `APP.detail[]`)
- Screening library remains a hexagon (`not-a-component`), not a component rect
- Entanglement edge stays thick on the C3a primary and structural overlay
- Overlay locators state `subset:` so C2c–e / C3b–c cannot be cited as complete

## Fonts

D2 embeds fonts in the SVG; labels are real `<text>` elements (linter
`real-text` clean).

## Could not render

Nothing required by the brief was omitted. Intentional mermaid-only narrative
(registers, six guideline checks, misinterpretation table, redraw triggers)
stays in `diagram-set.md` as markdown tables — same pattern as Silicon
Sandwiches.
