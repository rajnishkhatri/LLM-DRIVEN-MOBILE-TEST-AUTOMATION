# Stage-0 threshold sweep report

Worker A. Grid-sweep of the stage-0 router's THRESHOLD (theta) and MARGIN over the 72-row golden set, measured against the actual `route_stage0` decision function.

Objective: **maximum fast-path coverage subject to fast-path precision >= 0.99** over the 64 routable rows (expected route not null). Ties broken toward the most stringent (largest theta, then largest margin).

CHOSEN theta=0.8 margin=0.5

At the chosen point: coverage=0.953 (61/64 routable rows decided on the fast path), precision=1.000. All 8 route=null rows fall through (gate 3), so they never enter this table.

## Grid (precision · coverage) per (theta, margin)

| theta \ margin | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 |
|---|---|---|---|---|---|
| 0.3 | 1.00·0.95 | 1.00·0.95 | 1.00·0.95 | 1.00·0.95 | 1.00·0.95 |
| 0.4 | 1.00·0.95 | 1.00·0.95 | 1.00·0.95 | 1.00·0.95 | 1.00·0.95 |
| 0.5 | 1.00·0.95 | 1.00·0.95 | 1.00·0.95 | 1.00·0.95 | 1.00·0.95 |
| 0.6 | 1.00·0.95 | 1.00·0.95 | 1.00·0.95 | 1.00·0.95 | 1.00·0.95 |
| 0.7 | 1.00·0.95 | 1.00·0.95 | 1.00·0.95 | 1.00·0.95 | 1.00·0.95 |
| 0.8 | 1.00·0.95 | 1.00·0.95 | 1.00·0.95 | 1.00·0.95 | 1.00·0.95 * |
| 0.9 | 1.00·0.62 | 1.00·0.62 | 1.00·0.62 | 1.00·0.62 | 1.00·0.62 |

Each cell is `precision·coverage`; `*` marks the chosen point. Precision holds at 1.00 across the grid (the rules only ever fire one capability per row; the Q-013/014/015 traps resolve DATA 0.8 vs TICKET 0.2 by a 0.6 margin), so coverage is the only free variable. theta=0.9 drops the DATA rows (weight 0.8 < 0.9) and margin>0.6 would drop the traps; the chosen point is the most stringent that still keeps full coverage.
