# SELF-AUDIT — Determination 1 quantum map (style-decision)

Rendered: `docs/architecture/worksheets/mobile-test-automation/diagrams/`
via `docs/skills/generating-architecture-diagrams/scripts/render.sh`

Mode: **improve-existing** — topology ingested from the mermaid quantum map in
`style-decision.md` §2; readability pass applied (short labels, detail tables,
numbered edge refs, sync/async line kinds corrected to match edge claims,
module component lists relocated off-canvas, primary datastore grounded as
`view.omitted`). Auditor endpoint rolled up to quantum grain (was mermaid `MC`);
module membership retained in the Q qualifier + detail table.

Date: 2026-07-29

## Linter result

```
PASS  quantum-map: 9/9 canvas labels verbatim, 15 relocated facts, 15 <text> elements, 0 failure(s)
```

## Correctness checklist

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Titles | PASS | view title + every node labeled |
| 2 | Lines (sync solid / async dashed / no double-heads) | PASS | edge 1 dashed (async); 2–7 solid (sync); mermaid incorrectly used `-.->` for sync-labeled edges — corrected as representation |
| 3 | Shapes reserved & consistent | PASS | actors=pill, system=rect, EXT double-border, Git=cylinder |
| 4 | Labels verbatim + honesty tags | PASS | `needs-input` on omitted primary datastore / residency; no invented SLA/vendor/region |
| 5 | Colour never alone (grayscale legible) | PASS | `proofs/quantum-map-gray.png` — shapes + numbered refs survive |
| 6 | Keys / registers as real tables | PASS | Key + node/edge detail in `quantum-map.view.md` |
| 7 | Representational consistency (locator caption) | PASS | opens `Q` from `style-decision` |
| 8 | No invented facts | PASS | `forbidden-facts` clean (no Postgres/MinIO/cloud regions) |

## Readability self-audit

| Check | Result |
|---|---|
| One question per view | PASS — "one quantum, what sits outside" |
| Short labels + relocated detail | PASS — component lists and quantum claim in detail table |
| Numbered edge refs | PASS — 1–7; full claims in edge table |
| No orphan / floating modules | PASS — modules named on Q qualifier (renderer cannot nest) |
| Misinterpretation test | PASS — dashed = human async only; modules read as seams inside Q, not separate deployables |

## Fonts

D2 → SVG real-`<text>` (14 elements); web-safe fallback via skill driver.

## Could not render

- Nested quantum subgraph wrapping three module boxes (transformer cannot nest;
  `floating-boundary` forbidden). Module seams carried as Q canvas qualifier +
  detail rows instead.
- Primary datastore cylinder (Determination 2; residency `needs-input`) —
  grounded in `view.omitted`, not invented.
