# IR schema — the fact-frozen contract

The IR (intermediate representation) is a small JSON document that holds the
**logical model** of one view. It is the contract between the LLM phase (which
authors it) and the deterministic render phase (which draws it). Because every
label is captured verbatim and marked immutable, "verbatim labels" and "no
invented facts" become *enforceable* rather than *hoped for*.

The worked example is
[`assets/examples/silicon-sandwiches/ir.json`](../assets/examples/silicon-sandwiches/ir.json).

## Shape

```jsonc
{
  "view": {
    "id": "01-context",          // used as the output filename stem
    "level": "context",          // context | container | component | class
    "title": "…",                // rendered as a D2 comment + belongs in <title>
    "caption": "…",              // the locator caption; belongs in <desc>
    "direction": "down",         // D2 layout direction: down | right | …
    "grid_rows": 3,              // optional fixed canvas grid; pair with
    "grid_columns": 3,           // grid_columns to prevent routing collisions
    "opens": "SYS",              // (readability) the node/box this view zooms
                                 //   into from its parent; drives the locator
    "opens_from": "01-context",  // (readability) the parent view id — MUST be
                                 //   a view that actually exists in the
                                 //   produced set; see warning below
    "completeness": "complete",  // (readability) complete | subset:<base-view-id>
    "overlays": "auto",          // (decomposition) auto | by-theme | by-module |
                                 //   none — how dense views get sliced; see
                                 //   "Decomposition fields" below
    "omitted": [                 // (C4 Ch12) crosscutting nodes left off for
      {"label": "Logging",       //   legibility, surfaced as a grounded
       "note": "all components write logs here (not shown for brevity)"}
    ],                           //   "not shown for brevity" note — never silent
    "key": true,                 // (C4 Ch10) set false to opt a view OUT of the
                                 //   key requirement (rare; default is on when
                                 //   the notation is non-trivial)
    "allow_deployment": false    // escape hatch: true lets a view name deployment
                                 //   topology (only for a genuine infra element)
  },
  "nodes": [
    {
      "id": "SYS",               // short code; becomes the element id (diffable)
      "kind": "system",          // enum: actor|system|container|component|
                                 //       external|datastore|infra|boundary|
                                 //       process|not-a-component
      "label": "…",              // SHORT canvas name — VERBATIM, never reworded
      "technology": "…",         // (C4 Ch4) the tech choice for a CONTAINER; the
                                 //   transformer stacks it under the name as
                                 //   "[Container] <tech>". Required on containers
                                 //   (or a TECH: UNKNOWN honesty tag). Optional
                                 //   elsewhere.
      "near": "top-left",        // optional D2 placement hint: top-left |
                                 //   top-center | top-right | center-left |
                                 //   center-right | bottom-left | bottom-center |
                                 //   bottom-right. Use only to prevent routing
                                 //   collisions; it never changes topology.
      "qualifiers": ["…"],       // VERBATIM extra lines that STAY on the canvas
                                 //   (keep to 0–1; prefer detail[] for the rest)
      "detail": ["…", "…"],      // (readability) VERBATIM facts RELOCATED off the
                                 //   canvas into the node-detail table. Every
                                 //   string here must land in the table.
      "role": "standard",        // (decomposition) lineage-store | model-seam |
                                 //   standard (default). A semantic tag that
                                 //   makes theme-overlays deterministic; does
                                 //   NOT change the rendered shape/class.
      "family": "evidence-gap",  // optional: evidence-gap | faded |
                                 //   module-a | module-b | module-c
      "emphasis": "heaviest"     // optional hint (advisory only)
    }
  ],
  "edges": [
    {
      "from": "CUST",            // node id
      "to": "SYS",               // node id
      "kind": "sync",            // enum: sync | async | entangled
                                 //   (solid | dashed | thick-marked)
      "label": "…",              // SHORT verb label OR "" when using ref
      "ref": 1,                  // (readability) numbered canvas ref for dense
                                 //   views; the full claim goes in `detail`
      "detail": "…",             // (readability) VERBATIM full claim for the
                                 //   edge-detail table (required when ref set)
      "theme": "structural",     // (decomposition) structural | provenance |
                                 //   model-call | external-boundary — usually
                                 //   DERIVED (see below); an explicit value wins
      "module": "module-a"       // (decomposition) explicit module key for
                                 //   by-module overlays; usually DERIVED from the
                                 //   family of the edge's module endpoint
    }
  ],
  "forbidden_facts": [           // regex patterns the linter must NOT find
    "99\\.99", "\\bAWS\\b", "us-east", "\\bRedis\\b"
  ]
}
```

## Readability fields (short label + relocated detail)

A node's `label` is the **short canvas name**. The heavy detail — ADR tags,
evidence facts, honesty tags, rule references — goes in `detail[]`, which the
renderer emits as a **node-detail table keyed by node ID** *below* the diagram,
not onto the node. See [readability.md](readability.md).

The groundedness contract: **every string in `detail[]` must appear in the
rendered detail table.** The linter fails a render where a relocated fact has no
table home — that is what makes "nothing dropped, only relocated" a guarantee.

For dense views, set an edge `ref` number and put the full claim in the edge
`detail`; the canvas shows the number, the edge-detail table resolves it.

**Warning — `opens` / `opens_from` must be real.** These fields MUST name a
view that actually exists (or will exist) in the produced set — never invent a
notional parent (e.g. `opens_from: "01-context"` when no `01-context` view is
being produced) just to satisfy the locator lint check. If the view genuinely
has no parent view, that is a signal the view may not belong in this skill's
C4 zoom chain at all.

## Decomposition fields (dense views → primary + overlays)

A dense view (many edges, or one node with a large fan-in/out) is unreadable as
a single canvas even with numbered edges — the *routing* still collides. The fix
(see [readability.md](readability.md) §1) is to keep the full view as the
authoritative **primary** and emit **companion overlays**, each showing a
deterministically-selected subset of the primary's edges. `scripts/decompose.py`
does this; these fields drive it.

**`view.overlays`** — `auto` (default) decomposes only when the density trigger
fires (`≥ 30 edges` OR a node with `≥ 12` incident edges). `by-theme` / `by-module`
force a selector even below the trigger; `none` suppresses decomposition even when
dense. The default `auto` means an existing IR behaves exactly as before until it
is genuinely dense.

**`node.role`** — the semantic tag that makes *theme* overlays deterministic
(never a keyword guess):

- `lineage-store` — the append-only provenance/lineage sink. Every edge whose
  **target** is a `lineage-store` node is theme `provenance`. (In the case study,
  `Preserve Provenance` with its 13-edge fan-in.)
- `model-seam` — the single model-call choke point. An edge is theme `model-call`
  iff its **target** is a `model-seam` node **or** its **source** is a `model-seam`
  node (the seam's own outbound call to the gateway external). No text matching.
- `standard` (default) — no special role.

`role` is a **decomposition tag only**; it does not alter the rendered shape or
class (that stays governed by `kind`), so it never touches the grayscale-stable
vocabulary.

**`edge.theme`** — `structural | provenance | model-call | external-boundary`.
Usually **omit it** and let the transformer derive it deterministically:

0. `structural` if the edge is `kind: entangled` — a marked entanglement is a
   structural fact by definition (drawn thick so it reads in the base topology and
   can't be skimmed past), so it belongs in the base-topology overlay, never
   buried in a theme slice;
1. else `external-boundary` if the edge's target `kind == external`;
2. else `provenance` if target `role == lineage-store`;
3. else `model-call` if target or source `role == model-seam`;
4. else `structural`.

An explicit `theme` on the edge always wins over derivation (an escape hatch for
the rare edge the rules mis-bucket).

**`edge.module`** — the module key for *by-module* overlays. Usually omit it: the
transformer derives it from the `family` (`module-a/b/c`) of the edge's module
endpoint. Set it explicitly only to override.

### The two guarantees decomposition must keep

1. **Numbering locked.** An edge keeps its `ref` number in the primary and in
   every overlay it appears in — so a reader who learns "edge 22 is the
   entanglement" reads 22 the same way everywhere. `decompose.py` copies refs; it
   never renumbers.
2. **Parity (nothing dropped, nothing invented).** The union of all overlay edge
   sets equals the primary's edge set exactly — `union(overlays) == primary`. The
   linter's `check_overlay_parity` fails any set where an edge is missing from
   every overlay or appears with a different `ref`. This is what makes "the split
   is only a re-view, not an edit" provable. Every overlay also declares
   `completeness: "subset:<primary-id>"` and carries the primary's `opens` /
   `opens_from` so its locator caption renders and the drill-down link resolves.

An `entangled` edge stays `kind: entangled` (thick) in every overlay it lands in
— readability may relocate a fact, never soften a marked one.

## The rules the schema enforces

1. **`kind` is an enum.** No free-text shape choice — the transformer maps kind
   → reserved shape, so shape can't drift.
2. **Every label is a verbatim string.** The model author may set line breaks
   and typographic hierarchy at render time, but may not summarize, truncate,
   or reword. The linter compares normalized strings.
3. **No fillable numeric fields.** There is nowhere for the model to write an
   invented SLA / count / latency. Unknowns go in `qualifiers` as an explicit
   honesty tag (see [honesty-tags.md](honesty-tags.md)).
4. **`forbidden_facts`** names the invented-fact patterns that must never
   appear. Seed it with vendor/region/SLA markers relevant to the domain.

## C4-Book notation rules the schema enforces (iteration 3)

Distilled from Simon Brown's C4 book (the full per-signal triage lives in this
repo at `docs/research/c4-book-signal-triage.md`, outside the portable skill
bundle); each is a deterministic linter check, not prose advice:

5. **Technology on containers (Ch4).** A `kind:container` node must carry a
   `technology` (rendered as `[Container] <tech>` under the name) or an explicit
   `TECH: UNKNOWN` honesty tag. Scoped to containers only — components are
   in-process, and Ch5 says component-to-component technology is unneeded.
6. **Element `[Type]` (Ch10).** Container/component nodes render a bracketed type
   under the name (a render affix, like `EXT:` — the verbatim label is untouched).
7. **Diagram key (Ch10, most-repeated rule).** Any view whose notation is
   non-trivial (>1 shape, an async/entangled line, or a colour family) gets a
   generated **Key** section in its detail artifact, describing exactly the
   notation it uses. `view.key: false` opts a view out.
8. **Deployment stays off non-deployment views (Ch4/Ch8).** High-signal
   deployment nouns (kubernetes/pod/replica/load-balancer/region-codes) are
   forbidden unless `view.level == "deployment"` or `view.allow_deployment`. The
   word *cluster* is deliberately NOT gated (it also means a logical grouping).
9. **Specific edge verbs (Ch10).** A bare vague verb (`uses`, `calls`,
   `connects to`, …) as an on-canvas edge label fails; use a verb + preposition
   ("makes API requests to"). Numbered-`ref` edges are exempt (the verb lives in
   the claim).
10. **Grounded omission (Ch12).** A crosscutting node left off for legibility is
    declared in `view.omitted[]` and surfaced as a "not shown for brevity" note —
    an omission is explicit, never a silently dropped fact.

## Multi-view sets

One IR file per view. Keep the same node `id`s across views so an element is
trackable from Context → Container → Component, and so
representational-consistency captions can reference "the box you came from".

Overlay IRs are **generated**, not hand-authored: `decompose.py` writes them with
id `<primary-id>--<selector-key>` (e.g. `02-container--provenance`,
`03-module-wiring--module-b`). They reuse the primary's node ids and edge refs, so
they belong to the same set and track by colour and by number.
