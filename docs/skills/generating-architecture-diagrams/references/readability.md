# Readability & explainability

A diagram can be perfectly correct — every label verbatim, every fact grounded —
and still be an unreadable wall of text. Correctness is necessary, not
sufficient. This reference is the *legibility* layer: the concrete moves that
make a C4 set easy to look at and easy to explain, without loosening a single
fact.

These techniques are not invented here. They are distilled from a real set
(`docs/architecture/components/mobile-test-automation/diagram-set.md`) that
reached legibility only after **four hand revisions** — each revision note
documents a specific readability failure and its fix. The point of this
reference is to **front-load those moves** so a diagram is born readable instead
of being revised into readability four times.

**The governing constraint:** every readability edit is *representation only —
zero topology change*. Detail moves; facts never disappear. "Nothing was
dropped; it was relocated" is the phrase to keep in mind. The linter enforces
this (see [acceptance-checklist.md](acceptance-checklist.md), the groundedness
checks) — readability can never cost a fact.

## Table of contents

1. [One question per view](#1-one-question-per-view)
2. [Short labels + detail tables](#2-short-labels--detail-tables)
3. [Numbered edge refs (collision control)](#3-numbered-edge-refs)
4. [Un-nesting](#4-un-nesting)
5. [Layout direction](#5-layout-direction)
6. [Representational consistency & locator captions](#6-representational-consistency)
7. [Colour-tracking across views](#7-colour-tracking-across-views)
8. [Registers](#8-registers)
9. [The readability self-audit](#9-the-readability-self-audit)
10. [The combined view.md](#10-the-combined-viewmd)

---

## 1. One question per view

**The move:** each view answers exactly *one* question. When a view is trying
to answer several — "what talks to what" *and* "which module owns which edge"
*and* "who holds which credential" — split it into a structure-only **base
view** plus focused **overlays**, one question each.

**Why:** packing every concern into one canvas is what makes rendered views
overlap and become unreadable. Splitting by question is the single highest-
leverage de-clutter — it turns one dense master diagram into a guided sequence a
reader can follow.

**How to decide the split:** write the one-sentence question each view answers
*before* drawing it. If you can't state it in one sentence, or the sentence has
an "and" joining two different concerns, split. A worked inventory:

| View | The single question it answers |
|---|---|
| Context | Who and what does the system touch? |
| Container — topology | What containers exist, and what talks to what? |
| Container — module wiring | Which module owns which store/external edge? |
| Container — evidence/data flows | Where do the important artifacts go? |
| Container — credential topology | Who holds which credential — and who does not? |
| Container — async edges | Which edges are queued, and on what machinery? |
| Component — module flow | How does a request move through the components? |
| Component — a specific boundary | Where does <this concern> get handled? |

**Base vs overlay:** the base view carries the *complete* set of edges at its
grain. An overlay repeats a *subset* of the base view's elements to answer one
narrow question. An overlay is never the complete edge set — and it must say so
(see §6).

### Density-triggered decomposition (the automated move)

Numbered edge refs (§3) fix *label* collisions but not *routing* density: a view
with a 13-edge fan-in or 47 edges still overlaps no matter how short the labels.
The fix is mechanical and runs automatically in the pipeline
(`scripts/decompose.py`):

- **Keep the full view as the authoritative PRIMARY.** Nothing is removed from it;
  it stays the whole truth at its grain.
- **Emit companion OVERLAYS**, each a deterministically-selected subset of the
  primary's edges — one readable question each. Overlays are *additive*.
- **Two selectors, both tag-driven** (never a keyword guess):
  - *by-theme* — group edges into `structural` (incl. the marked entanglement
    edge), `provenance` (writes into a `role: lineage-store` node), `model-call`
    (to/from a `role: model-seam` node), `external-boundary` (to a `kind:
    external` node). Used when the IR carries `role` tags.
  - *by-module* — group edges by the `module-a/b/c` family of their module
    endpoint. Used when the IR has module families but no roles.
- **Trigger, don't apply universally:** decompose only when a view has **≥ 30
  edges** *or* a node with **≥ 12** incident edges. Sparser views stay a single
  labeled diagram — a split there would just add a lookup step for no gain.

**Determinism is the point.** The selector and the grouping are chosen from the
IR by code, so the *same source always produces the same overlays* — this closes
the "two runs on the same diagram picked different slices" failure. If you want a
specific split, set `view.overlays` to `by-theme` / `by-module` / `none`; the
default `auto` decides from the density trigger and the tags present.

**The two guarantees** (linter-enforced, see §9 and acceptance-checklist R6–R9):

1. *Numbering locked* — an edge keeps its `ref` in the primary and in every
   overlay, so "edge 22 is the entanglement" reads the same everywhere.
2. *Parity* — `union(overlay edges) == primary edges`, exactly. The split is a
   re-view, never an edit: no edge is dropped and none is invented. Each overlay
   declares `completeness: subset:<primary>` and locates itself (§6).

A marked `entangled` edge is classified `structural`, so it always appears in the
base-topology overlay (drawn thick), never buried in a theme slice — the one
finding the reader must not miss stays in the first, most-structural view.

---

## 2. Short labels + detail tables

**The move:** the label on the canvas is a **short name only**. All the
detail — ADR tags, evidence facts, honesty tags, rule references, SLAs — moves
into a **per-view detail table keyed by node ID**, rendered directly below the
diagram. The reader treats *label + table row as one unit*.

**Why:** a node that carries five qualifier lines is unreadable at any zoom, and
the lines collide with neighbours. Moving detail to a table keeps the canvas
scannable while losing nothing — the table is part of the diagram, not an
appendix.

**The table structures** (reproduce these exactly — the linter checks them):

Node-detail table:

```
| Node | Detail the short label hides |
|------|------------------------------|
| SYS  | ACCEPTED: modular monolith, ONE quantum (ADR 0005) … opened in C2a |
| PGW  | PROVISIONAL vendor — contract/tier/SLA pending … SLA: UNKNOWN (pending) |
```

Edge-detail table (simple):

```
| Edge      | Detail the short label hides |
|-----------|------------------------------|
| CUST → SYS | browse offer, place order, pay online (sync) |
```

**Groundedness:** every string you take *off* a node must appear *in* that
view's detail table. This is the load-bearing invariant — the linter fails a
render where a relocated fact has no table home. That is what makes "nothing
dropped, only relocated" a guarantee rather than a hope.

**Dense views get a numbered node explainer.** When a view is dense (any node
carries ≥ 3 relocated detail lines, or the view has ≥ 12 edges), the canvas short
label gets a `[n]` number prefix and the node-detail table becomes a *numbered
walk-through* keyed to those numbers — the same collision-free pattern used for
edges (§3), extended to nodes. The reader maps `[3]` on the canvas to explainer
row 3. Below that trigger, the simple keyed table is clearer. The renderer does
this automatically; the linter checks every `[n]` resolves to a row.

**One export caveat worth stating in the self-audit:** if a single view is
exported detached from its table (dropped into a slide), the honesty tags travel
with the node, not the table. When that will happen, re-inline the honesty tags
onto the affected nodes for that export. Short labels are the whole truth only
*with* their table.

---

## 3. Numbered edge refs

**The move:** on dense views, put only a **number** (`1..N`) on each edge; the
full claim lives in a numbered edge-detail table. Mode (sync/async) is carried
by the line style *and* restated in the table.

```
| # | Edge      | Mode | Claim |
|---|-----------|------|-------|
| 1 | QA → APP  | sync | 2 CLIs (ingestion + hierarchy-tool), no BFF (ADR 0008) |
| 6 | APP → PG  | sync | State + lineage, same local transaction (ADR 0007) |
```

**Why:** word labels on edges land on node borders and subgraph lines under an
auto-layout engine, producing exactly the collisions that make a view look
broken. A number is one glyph — it never collides. The reader reads each number
against the table.

**Scope it:** number edges **only where word labels would collide** — the dense
container-topology and module-wiring views. Sparser views (a component boundary
with four edges) keep short verb labels, which are more immediately readable when
they fit. Don't number a view that isn't crowded; that just adds a lookup step
for no gain.

---

## 4. Un-nesting

**The move:** remove subgraph nesting that a parent view already established.
When a drill-down view repeats the deployment boundary and quantum wrapper that
its parent view already drew, those wrappers only crush the canvas — drop them.

**Why:** deep nesting (four levels of boxes-in-boxes) leaves no room for the
content. The parent view is the completeness reference for those boundaries;
the child doesn't need to redraw them, only to name that it lives inside them
(a caption does that in one line).

**Keep nesting where it *introduces* a boundary** (the view that first shows the
deployment boundary and quantum needs those subgraphs). Drop it in the
drill-down that would merely repeat them.

---

## 5. Layout direction

**The move:** choose `direction` per view by the shape of what it shows.

- **Wide topology** (many containers side by side, lots of cross-edges) → **left-
  to-right** (`right`). LR spreads a wide graph horizontally so edges and labels
  stop stacking on top of each other.
- **Flows and fan-ins** (a request moving through components; many writers into
  one sink) → **top-to-bottom** (`down`). These read as a vertical progression.

**Why:** the default direction fights a graph whose natural axis is the other
way, forcing crossings. Matching direction to the dominant axis removes
crossings for free. When a subgraph's internal stack reads better vertically
inside an LR view, set the inner direction independently.

---

## 6. Representational consistency

**The move:** every deeper view **opens by locating itself in the previous
one**, in one caption line, and declares whether it is a *complete* view or a
*subset* overlay. No fragment is ever presented cold.

The caption pattern:
- A drill-down: *"This view opens the `<BOX>` box from `<parent view>` at
  `<grain>` grain."*
- An overlay: *"This view is a subset of `<base view>` — only the elements and
  edges that `<answer this view's one question>`."*

**Completeness references:** name the views that carry the *complete* edge set at
each grain (e.g. container-grain, module-grain, component-grain). Every overlay
is provably a subset of one of them. State it, because a reader who cites an
overlay in a design argument would otherwise think they'd seen every edge — the
most consequential misreading a split set can cause.

**Why:** showing a portion without indicating its place in the whole is the
classic source of confusion (Ch. 23). The caption + completeness reference is
what lets a reader zoom in without ever losing where they are.

**Views at one level redraw as a set.** A topology change that touches one
container view must be checked against all the container views — they share an
element inventory, so an edit to one can silently contradict another.

---

## 7. Colour-tracking across views

**The move:** a semantic element keeps the *same* fill/stroke in every view that
contains it. Module A is the same colour in the container view, the module-wiring
view, and the component view — so a reader tracks it across the zoom chain by
eye.

**Why:** if a module is gold here and green there, the reader can't follow it
across views and the set stops feeling like one system. Lock the domain palette
once (in the shared key) and apply it identically everywhere.

**Colour is never the only channel** (the grayscale rule): every fill is paired
with a shape difference and/or a text tag, so the tracking survives monochrome.

---

## 8. Registers

Some information is a *table*, not a diagram. Render these as real tables beside
the views they annotate:

- **External-edge register** — every external edge, its mode, its standing
  (what's known/unknown), and the probe that would resolve each unknown.
  `| Edge | Mode | Standing | Probe that resolves it |`
- **Async register** — every asynchronous edge, its transport, and a note.
  `| Tag | Edge | Transport | Note |` — plus a **"deliberately synchronous"**
  companion table (`| Edge | Why sync is the decided answer |`) that records the
  edges where async would have been the convenient-but-wrong answer. This guards
  against *async-by-omission*: a reader can otherwise assume an unlisted edge is
  sync by accident rather than by decision.

**Why:** a register carries per-edge detail that would never fit on the canvas,
and the "deliberately synchronous" table makes a *decision* visible that a
diagram of only-the-async-edges would leave invisible.

---

## 9. The readability self-audit

After rendering, in addition to the correctness checklist, confirm:

- **One question per view** — you can state each view's question in one sentence
  with no "and".
- **Short labels** — no node carries more than its short name on the canvas;
  every hidden detail is in the view's node-detail table.
- **No collisions** — dense views use numbered edge refs; no word label sits on
  a node border or subgraph line.
- **Locators** — every non-context view names the box it opens and its base
  view; overlays declare "subset of <base>".
- **Colour tracking** — each module/domain is the same colour everywhere.
- **Decomposed when dense** — any view over the density trigger (≥30 edges, or a
  node with ≥12 incident edges) was split into a primary + overlays, not shipped
  as one overlapping canvas.
- **Parity holds** — `union(overlays) == primary`; every overlay declares
  `subset:<primary>`; edge numbers match across the primary and every overlay.
- **Drill-down links resolve** — every locator names a view that was actually
  produced (no dangling "opens X" where X doesn't exist).
- **Entanglement survives** — every marked entanglement edge is still thick in
  the overlay it lands in.
- **Grounded** — every fact in the source (or the input diagram set) is present
  in a label or a table; zero topology edges added or removed.

The **misinterpretation test** is the sharpest self-audit: for each way the
diagram could be *misread*, name the countermeasure already in the set and the
residual exposure. "An easily misinterpreted diagram is worse than no diagram at
all." If a view could be read as the complete edge set when it's an overlay, or
a rolled-up edge read as "any module may call that external", the countermeasure
is the completeness reference and the locator caption — make sure they're
present.

---

## 10. The combined view.md

**The move:** the primary artifact for each view is a single `view.md` — the
rendered image **first**, then the numbered node explainer and the edge table
**directly beneath it**, so image and legend are one scrollable unit. Not a cold
`*-detail.md` in a separate file the reader has to hunt for.

**Why:** a short label is only the whole truth *with* its table (§2). Putting the
table under the image keeps that pairing intact — the reader never has to hold a
number in their head while opening another file. `render.sh` emits
`<view-id>.view.md` for every view (primary and overlay); the flat `*-detail.md`
still exists for the SVG-alone export path.

**The export caveat still applies:** if you lift the bare SVG out of its
`view.md` (into a slide), re-inline the honesty tags onto the affected nodes —
off-canvas tags do not travel with a detached SVG. The `view.md` states this at
its foot so a reader who copies the image is warned.

### A note on layout direction after numbering (§5 revisited)

Numbered edge refs remove the *word-label collision* reason for choosing
`direction: right`. Once a dense view is numbered (and especially once it is
decomposed), retry `direction: down` — a vertical layout usually narrows the
canvas and reads as a progression. Choose direction by the shape of what's left
*after* decomposition, not before.
