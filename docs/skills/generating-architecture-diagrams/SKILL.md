---
name: generating-architecture-diagrams
type: skill
description: >-
  Generates NEW C4-flavored architecture diagrams AND improves the readability
  of EXISTING ones, with verbatim labels, honesty tags, and no invented facts,
  all proven by a deterministic linter. Self-sustained: given only a folder or a
  terse trigger it auto-detects whether to generate or improve and runs the
  whole render-lint-self-audit loop, asking only when a required
  architecture fact is missing. Use whenever the user mentions "architecture
  diagram", "C4", "context / container / component diagram", "system diagram",
  "diagram this architecture", "make these diagrams readable", "declutter these
  diagrams", "split / decompose a dense diagram", "improve the diagrams", or
  asks to draw / redraw / render / tidy a system's topology. Portable across
  Claude Code, Cursor, GitHub Copilot, and any coding agent. Do NOT use for
  exploratory whiteboard sketches mid-design (draw those
  inline), for non-architecture flowcharts/charts (use a charting skill), for
  choosing the architecture itself (that's the arch-* workflow), or for
  book-figure / pattern / design-concept illustrations (e.g., Clean
  Architecture rings, dependency-rule figures, principle diagrams) — those
  need hand-authored geometry (manual nesting, positions, arrowhead
  contrasts) that this pipeline cannot express.
---

# Generating architecture diagrams

Turn an architecture spec or logical model into a C4-flavored diagram set — or
take an *existing* set that has become an unreadable wall of text and make it
legible — that honors the book's diagram guidelines, uses a strict reserved
shape vocabulary with **short labels + relocated detail tables**, **verbatim
labels**, and **honesty tags**, **invents no facts**, renders to real-`<text>`
SVG (D2-first), and **proves its own correctness** with a deterministic linter +
grayscale proof + self-audit.

Two things make this skill different from "draw me a diagram":

- **Correctness is enforced, not hoped for.** The reliability mechanism is
  **deterministic detection, LLM-only correction**: a linter (not self-critique)
  finds every error and hands you its exact message; you fix the IR and
  re-render. The same model that made an error has the same blind spot reviewing
  it, so the linter is load-bearing — never skip it.
- **Readability is a first-class goal.** A diagram can be 100% correct and still
  unreadable. This skill front-loads the legibility moves (one question per
  view, short labels with detail in tables, numbered edge refs, locator
  captions) that dense sets otherwise only reach after many hand-revisions. See
  [references/readability.md](references/readability.md). Readability edits are
  *representation only — zero topology change*; the linter guarantees every fact
  moved off a node reappears in a table.

**Out of scope: concept/pattern figures.** The IR/renderer is a *topology
compiler*: enum C4 kinds, one arrow type (sync/async/entangled), auto-layout,
no container nesting. Book-style concept figures carry their lesson in the
*geometry* — concentric rings, grids, drawn boundary lines, an
implements-vs-calls arrowhead contrast — which this pipeline cannot express,
and the linter cannot check that declared geometry matches rendered geometry.
For those figures, hand-author the D2 or Mermaid directly instead.

**All paths below are relative to this skill directory**
(`docs/skills/generating-architecture-diagrams/`).

## Self-sustained: what to do with just a folder or a terse trigger

This skill runs from a minimal prompt ("diagram this", "make these readable", or
just a path). You do not need a step-by-step instruction — carry your own:

1. **Locate the target.** Look at the path or folder you were given. Find the
   architecture inputs: an existing `diagram-set.md` (mermaid or otherwise), a
   `logical-components.md` / component model, or an arch-* worksheet. If nothing
   is named, look under `docs/architecture/…`, `.arch/…`, or the current dir.
2. **Classify the task.**
   - There is already a `diagram-set.md` and the ask is to tidy / clarify /
     declutter / make-readable → **improve-existing** (do not change topology).
   - There is a logical model but no diagram set, or the ask is to draw / render
     / generate → **generate-new**.
3. **Proceed autonomously.** Run the workflow below to completion — author or
   ingest the IR, render, lint, self-audit, emit. Only **stop and ask** when a
   required architecture *fact* is genuinely missing or ambiguous (an unknown
   SLA, an undecided vendor) — never stop just for a mode confirmation. When you
   do stop, ask the one specific question, not "how would you like to proceed?".
4. **Report what you did**: which files you read, generate-vs-improve, which
   views you produced, the linter result, and anything you had to leave as an
   explicit honesty tag.

### Improving an existing set without changing the architecture

When the input is an existing `diagram-set.md`, ingest it into the IR *without
altering topology*: every node, edge, and fact becomes an IR entry; the short
name becomes `label`, the crammed-on detail becomes `detail[]`. Then apply the
readability moves and render. The groundedness contract holds: the linter's
`grounded-relocation` check fails if any ingested fact has no table home, so
"nothing dropped, only relocated" is provable, not promised. Do not add or
remove an edge; a topology change is a different task (that's the arch-*
workflow, not this skill).

## Prerequisites

The pipeline needs the `d2` CLI, `rsvg-convert`, and Python 3 with Pillow. On
macOS:

```bash
brew install d2 librsvg
python3 -m pip install --quiet Pillow
```

Verify:

```bash
d2 --version && rsvg-convert --version | head -1 && python3 -c "import PIL; print('Pillow', PIL.__version__)"
```

(In this repo `d2 --version` prints `0.7.1`; Pillow `10.4.0` was already present
via Anaconda; `rsvg-convert` from Homebrew's `librsvg`.)

## The workflow

1. **Author or ingest the IR** (LLM). Map the spec (generate) or the existing
   diagram set (improve) into `ir.json` — one file per view. Kinds are enums;
   the short name is `label`; heavy detail (ADR tags, evidence facts, honesty
   tags) goes in `detail[]` so it renders in a table, not on the node; unknowns
   become explicit honesty tags; there are no fillable numeric fields to invent
   into. If a required fact is ambiguous, **stop and ask** — do not default.
   See [references/ir-schema.md](references/ir-schema.md).
2. **Apply readability** (LLM). Before rendering, run the legibility pass:
   one question per view (split overloaded views into base + overlays), short
   labels with detail relocated, numbered edge refs on dense views, a locator
   caption (`view.opens` / `view.completeness`) on every non-context view,
   consistent module colours. See [references/readability.md](references/readability.md).
3. **Render** (deterministic). Run the driver (below). It emits the D2, the
   SVG, the @2x PNG, the grayscale proof, and the **combined `view.md`** (the
   rendered image with the numbered node explainer + edge table beneath it).
3.5. **Decompose dense views** (deterministic). The driver runs `decompose.py`
   automatically: if a view is dense (**≥ 30 edges**, or a node with **≥ 12**
   incident edges) it keeps the full view as the authoritative **primary** and
   emits companion **overlay** views — one per *theme* (structural / provenance /
   model-call / external-boundary, from node `role` tags) or per *module* (from
   the module `family`), chosen **deterministically** from the IR so the same
   source always splits the same way. Overlays are additive; the primary stays
   the whole. Edge numbering is **locked** across the primary and every overlay,
   and the linter proves `union(overlays) == primary` (nothing dropped, nothing
   invented). Sparse views are not split. See [readability.md](references/readability.md) §1.
4. **Lint** (deterministic). Per view, run `lint_diagram.py` with `--detail`
   (correctness + readability/groundedness: relocated facts landed, locator
   present, edge refs resolve, node explainer resolves, canvas not overloaded,
   no free-floating boundary box). For a decomposed set, the driver also runs the
   **set-level** lint (`--primary … --overlays …`): overlay parity, drill-down
   links resolve, entanglement preserved. Fix any FAIL by editing the IR, then
   re-render. Cap at ~3 iterations; escalate to the human on repeated failure.
5. **Self-audit**. Score the checklist from the linter output + the rendered
   proof, using [assets/self-audit-template.md](assets/self-audit-template.md),
   including the readability self-audit (readability.md §9) and the
   misinterpretation test.

## Run (agent path) — the driver

`scripts/render.sh IR.json OUTDIR` runs the whole render phase. Proven on the
bundled worked example (Silicon Sandwiches Context view):

```bash
bash scripts/render.sh \
  assets/examples/silicon-sandwiches/ir.json \
  assets/examples/silicon-sandwiches
```

It prints (and produces, in `OUTDIR`) — the driver renders the primary, then
runs `decompose.py`, which for this sparse view emits no overlays:

```
render.sh: …/01-context.svg has 21 <text> elements
grayscale proof -> …/proofs/01-context-gray.png
render.sh: primary -> …/01-context.svg , …/01-context.view.md
primary	01-context	selector=none	trigger=10 edges, max degree 10 — below trigger
decompose: no overlays for 01-context (10 edges, max degree 10 — below trigger).
render.sh: done -> …/01-context.svg (+ 0 overlays)
```

Then lint the result against its IR. **Always pass `--detail`** — the render
step produces `<view-id>-detail.md`, and the linter's key + groundedness checks
require it (without it the C4 key check fails, since any non-trivial view must
carry a key):

```bash
python3 scripts/lint_diagram.py \
  --ir assets/examples/silicon-sandwiches/ir.json \
  --svg assets/examples/silicon-sandwiches/01-context.svg \
  --d2 assets/examples/silicon-sandwiches/01-context.d2 \
  --proof assets/examples/silicon-sandwiches/proofs/01-context-gray.png \
  --detail assets/examples/silicon-sandwiches/01-context-detail.md
```

A clean render prints and exits 0:

```
PASS  01-context: 35/35 canvas labels verbatim, 0 relocated facts, 21 <text> elements, 0 failure(s)
```

The linter exits **1** on any failure — label drift, an invented fact (in the
SVG *or* the detail table), a double-headed arrow, a flattened (non-`<text>`)
SVG, an undersized font, a cylinder used for a non-datastore, a missing
grayscale proof, a relocated fact that never landed in a detail table, a
non-context view with no locator caption, an unresolved edge ref, a node
overloaded with on-canvas text, **an on-canvas `[n]` with no numbered explainer
row, or a free-floating `boundary` box** (relocate its fact into the bounded
node's `detail[]` instead — the transformer cannot nest). In **set mode** it also
fails on **broken overlay parity** (an edge dropped from or invented by the
split, or a ref that drifted), a **dangling drill-down link** (a locator naming a
view that was never produced), or a **softened entanglement edge**.

### The scripts

| Script | Does |
|---|---|
| `scripts/ir_to_d2.py` | IR → D2 source (reserved-vocabulary classes) **+ the combined `view.md`** (image first, numbered node explainer + edge table under it). |
| `scripts/decompose.py` | Density-triggered decomposition: primary + deterministic theme/module overlays, numbering locked, parity-checked. |
| `scripts/render.sh` | The driver: renders the primary, decomposes if dense, renders every overlay, runs the set-level lint. Real-`<text>` guard throughout. |
| `scripts/grayscale_proof.py` | Pillow desaturate → `proofs/*-gray.png` (colour-never-alone proof). |
| `scripts/lint_diagram.py` | The deterministic gate. **Per-view**: verbatim labels, shape↔kind, no-double-arrow, real-`<text>`, min-font, forbidden-facts, grayscale-proof, relocation grounded, locator, edge/node-explainer refs resolve, no floating boundary. **C4-Book (iteration 3)**: diagram key present, container technology present, `[Type]` on containers/components, specific edge verbs, deployment-nouns-off-non-deployment-views, grounded omission. **Set-level** (`--primary/--overlays`): overlay parity, drill-down links, entanglement preserved. |
| `scripts/test_c4_signals.py` | Negative+positive tests for the six C4-Book checks (each fires on violation, passes when clean; incl. false-positive guards). `python3 scripts/test_c4_signals.py` → 22 asserts. |

## The rules (references)

- [readability.md](references/readability.md) — **the legibility layer**: one question per view (incl. **density-triggered decomposition** into primary + overlays), short labels + detail tables, the **combined `view.md`**, numbered edge refs, un-nesting, layout direction, locator captions, colour-tracking, registers. Read this whenever a set is dense or the ask is "make it readable".
- [shape-vocabulary.md](references/shape-vocabulary.md) — reserved shapes ↔ kinds. Cylinder = datastore only; hexagon = not-a-component; dash-border = process.
- [line-semantics.md](references/line-semantics.md) — solid = sync, dashed = async, thick = one marked entanglement edge, no double-heads.
- [honesty-tags.md](references/honesty-tags.md) — `SLA: UNKNOWN`, `PROVISIONAL`, `PROPOSED ADR`; no invented facts.
- [ir-schema.md](references/ir-schema.md) — the fact-frozen IR contract (incl. `detail[]`, edge refs, `view.opens`/`completeness`).
- [acceptance-checklist.md](references/acceptance-checklist.md) — the checks and the fix loop.
- [d2-classes.d2](references/d2-classes.d2) — the canonical classes block the transformer embeds.

This skill **extends** the family's prose diagram rules in
`.cursor/skills/arch-lifecycle/references/diagram-rules.md` (the six guideline
checks and representational consistency) — read those for the "why"; this skill
adds the strict vocabulary, the IR, and the enforcement tooling.

## Worked example

[assets/examples/silicon-sandwiches/](assets/examples/silicon-sandwiches/)
holds the gold-standard Context-view slice: `ir.json`, the rendered
`01-context.svg` / `@2x.png`, `proofs/01-context-gray.png`, and `SELF-AUDIT.md`.
The full three-view Silicon Sandwiches deliverable (Container, Component,
registers, key, poster) is specified in
`.arch/components/silicon-sandwiches/designer-agent-prompt.md`.

[assets/examples/mobile-test-automation/](assets/examples/mobile-test-automation/)
is the **decomposition** worked example: a real 47-edge container view split
deterministically into a primary + four theme overlays (structural / provenance /
model-call / external-boundary), plus a by-module example. See its
[README](assets/examples/mobile-test-automation/README.md) — it shows the
primary-stays-whole + numbering-locked + parity guarantees on a genuinely dense
set.

## Gotchas

- **`grep -c "<text"` lies.** D2 puts the whole SVG on one line, so a line-count
  reports `1` even with many labels. Count occurrences with `grep -o "<text" | wc -l`.
  The driver and linter both do this.
- **D2 double-quoted labels can't span raw newlines.** Multi-line labels use the
  two-character escape `\n` inside the quotes; `ir_to_d2.py` emits that. A raw
  newline gives `unexpected map termination character }`.
- **The pill actor is a high `border-radius`, not a shape.** D2 has no "stadium"
  shape; `border-radius: 999` on a rectangle makes the pill (see `d2-classes.d2`).
- **Externals get their `EXT:` prefix from the transformer**, not the IR. Write
  the plain name in `ir.json`; don't double-prefix.
- **Don't restyle nodes inline.** Shape/colour consistency across views comes
  from the classes block — edit `d2-classes.d2`, not individual nodes.

## Mermaid fallback

D2 is the proven strict path (real `<text>`, reserved shapes, grayscale). The
repo's arch-* family and `.arch/binding.toml` default to **mermaid**
(`flowchart`, `-->` sync / `-.->` async). Mermaid is a legitimate fallback for
quick inline diagrams, but for the strict deliverable its default
`<foreignObject>` HTML labels are dropped by non-browser SVG consumers — you
must set `htmlLabels: false`, and even then its `<text>` support is partial.
This skill does not bundle or prove a mermaid renderer; use D2 for anything that
must pass the linter.

## Install into another repo / agent

See [INSTALL.md](INSTALL.md) for the per-agent install matrix (Claude Code,
Cursor, GitHub Copilot, any other agent).
