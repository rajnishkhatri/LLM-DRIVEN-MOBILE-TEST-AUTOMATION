# Acceptance checklist

Distilled from the six diagram-guideline checks (Ch. 23,
`arch-lifecycle/references/diagram-rules.md`) and the Silicon Sandwiches
designer brief. Each check maps to a deterministic linter check where possible;
the rest are self-audited from the render.

| # | Check | Enforced by |
|---|---|---|
| 1 | **Titles** — every node, boundary, and view carries a visible title. | self-audit (labels present ⇒ titles present) |
| 2 | **Lines** — every arrow directional; solid = sync, dashed = async, used nowhere else; no double-headed arrows. | linter `no-double-arrow` + self-audit |
| 3 | **Shapes** — stadium / rectangle / double-bordered-`EXT` / cylinder used strictly as defined; no cylinder outside datastores. | linter `shape-kind` |
| 4 | **Labels** — every edge/node label present and **verbatim**; every honesty tag rendered. | linter `verbatim-labels` |
| 5 | **Colour never alone** — grayscale proof of the view is fully readable; attach the proof. | linter `grayscale-proof` (exists) + self-audit (legible) |
| 6 | **Keys** — a key panel exists where any shape could be misread; registers render as real tables. | self-audit |
| 7 | **Representational consistency** — each deeper view locates itself in the previous one (accent stroke + locator caption); no fragment shown cold. | linter `locator-caption` + self-audit |
| 8 | **No invented facts** — no vendor/region/SLA/count/latency beyond the IR; honesty tags carry the gaps. | linter `forbidden-facts` (SVG + detail table) + `real-text` + `min-font` |

### C4-Book notation checks (Ch4/Ch10/Ch12)

Reconciled 1:1 with the C4 review checklist (Appendix A). Each row is either an
existing check (above) or a new deterministic one added in iteration 3.

| # | Check | Enforced by | Appendix-A row |
|---|---|---|---|
| C1 | **Diagram key** — any view using >1 shape / async-or-entangled lines / a colour family must carry a generated Key section. | linter `key` + `ir_to_d2.write_key` | *"key to describe any notation used"* |
| C2 | **Element type** — every container/component shows its C4 `[Type]` under the name (a render affix; label text untouched). | `ir_to_d2.type_affix` + self-audit | *"understand the type of every element"* |
| C3 | **Technology present** — every `kind:container` names its technology, or carries a `TECH: UNKNOWN` honesty tag. Scoped to containers (components are in-process; C4 Ch5). | linter `technology` | *"understand the technology choices … where applicable"* |
| C4 | **Specific edge verbs** — no bare vague verb (`uses`, `calls`, `connects to`, …) as an on-canvas edge label; use a verb + preposition. | linter `edge-verb` + readability.md guidance | *"every arrow labeled with intent"* |
| C5 | **Deployment stays off** — no deployment topology (kubernetes/pod/replica/LB/region codes) on a non-deployment view. | linter `deployment-noun` | *(C4 Ch4/Ch8 rule; guards abstraction-level clarity)* |
| C6 | **Grounded omission** — a crosscutting node omitted for legibility is declared in `view.omitted[]` and surfaced as a "not shown for brevity" note, never silently dropped. | `ir_to_d2.write_omitted` + self-audit | *(C4 Ch12 rule; keeps omissions honest)* |

The remaining Appendix-A rows (title present, scope clear, every element named,
colours/shapes/icons/border-styles understood, description matches direction) map
onto rows 1–8 and R1–R11 above — nothing in the review checklist is unmapped.

### Readability checks (the legibility layer — see [readability.md](readability.md))

| # | Check | Enforced by |
|---|---|---|
| R1 | **Grounded relocation** — every fact moved off a node lands in a detail table; nothing dropped. | linter `grounded-relocation` |
| R2 | **De-cluttered canvas** — no node overloaded with on-canvas text; heavy detail is in `detail[]`. | linter `label-density` |
| R3 | **Edge refs resolve** — every numbered canvas edge has exactly one detail-table row. | linter `edge-refs` |
| R4 | **One question per view** — each view answers a single question (base + overlays). | self-audit |
| R5 | **Colour tracking** — each module/domain is the same colour in every view. | self-audit |

### Decomposition checks (dense views → primary + overlays — see [readability.md](readability.md) §1)

| # | Check | Enforced by |
|---|---|---|
| R6 | **Decomposed when dense** — a view ≥30 edges (or a node ≥12 incident edges) is split into a primary + deterministic overlays, not shipped as one overlapping canvas. | `decompose.py` (density gate) + self-audit |
| R7 | **Overlay parity** — `union(overlay edges) == primary edges`; no edge dropped or invented; every edge's `ref` matches across primary and overlays. | linter set-mode `overlay-parity` |
| R8 | **Drill-down links resolve** — every `opens_from` names a view that was actually produced; no dangling locator. | linter set-mode `drilldown-link` |
| R9 | **Entanglement preserved** — every marked entanglement edge stays `kind:entangled` (thick) in every overlay it lands in. | linter set-mode `entanglement` |
| R10 | **Node explainer resolves** — in explainer mode, every on-canvas `[n]` has exactly one numbered explainer row. | linter `node-explainer` |
| R11 | **No floating boundary** — no free-floating `boundary` box; boundary/quantum facts relocated into the bounded node's `detail[]`. | linter `floating-boundary` |

## Self-audit

After rendering, write a `SELF-AUDIT.md` scoring each row pass/fail **from the
linter's machine output and the rendered proof**, not from imagination — the
same model that made an error has the same blind spot reviewing it. Use
[`assets/self-audit-template.md`](../assets/self-audit-template.md). List
explicitly anything you could not render and why.

## The loop

`generate IR → render → lint → self-audit → fix`. Any linter FAIL feeds its
exact message back to edit the IR (or `d2-classes.d2`), then re-render. Cap
iterations (~3); on repeated failure, **stop and ask the human** rather than
inventing a fact to make a check pass.
