# Worked example — density-triggered decomposition

This is the canonical example for the **decomposition** mechanic
(references/readability.md §1). It is the real Mobile Test Automation container
view — 16 components in three clusters, 6 externals, **47 edges** — the exact set
the iteration-2 feedback said was "too cluttered as one canvas."

Every artifact here was produced by `scripts/render.sh`; nothing was hand-drawn.

## By-theme (the primary example)

`02-container.json` is the primary IR. Two nodes carry a decomposition `role`:
`PP` (Preserve Provenance) is `lineage-store`, `IM` (Invoke Models) is
`model-seam`. That is all the tagging the engine needs.

`render.sh 02-container.json .` produces:

| Artifact | What it is |
|---|---|
| `02-container.svg` / `@2x.png` / `.view.md` | the **primary** — the full 47-edge view, the authoritative whole |
| `overlays/02-container--structural.*` | base topology (20 edges) — **carries the thick entanglement edge 22** |
| `overlays/02-container--provenance.*` | the 13-edge fan-in into `PP` (edges 26–38), isolated |
| `overlays/02-container--model-call.*` | the model-call seam: callers into `IM` + `IM`→screening-library (edges 12–15, 25) |
| `overlays/02-container--external-boundary.*` | the 9 edges crossing to external systems (edges 39–47) |

The selector (`by-theme`) and the grouping are chosen **deterministically** from
the `role` tags — run it twice, get the same four overlays. Edge numbers are the
**primary's** numbers, preserved in every overlay (numbering locked), and
`union(overlays) == primary` exactly (parity — checked by the set-level linter).

## By-module (the second selector)

`module-wiring/03-container-module-wiring.json` sets `view.overlays: by-module`.
Its 23 edges split by the `module-a/b/c` family of each edge's endpoint into
MA (7 edges), MB (8), MC (3), and unclustered (5) — the same MB-owns-the-most
split the feedback diagnosed as "MB's wiring clashes with MA/MC in the middle."
This is how a set with module colours (but no `role` tags) decomposes.

## What to look at

Open a `*.view.md` — the rendered image sits above its numbered node explainer
and edge table, one scrollable unit. Compare `02-container@2x.png` (busy) with
`overlays/02-container--provenance@2x.png` (the fan-in alone, instantly legible).
That contrast is the whole point of the decomposition mechanic.
