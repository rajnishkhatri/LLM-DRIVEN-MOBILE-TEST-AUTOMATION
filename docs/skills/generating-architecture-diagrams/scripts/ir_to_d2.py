#!/usr/bin/env python3
"""Deterministic IR -> D2 transformer.

Reads a fact-frozen IR (see references/ir-schema.md) and emits D2 source that
applies the reserved-vocabulary classes from references/d2-classes.d2. Because
the mapping is CODE, not prose, shape/line encoding is guaranteed consistent
across every view and cannot drift (diagramskill.md, "Render (deterministic)").

The transformer never invents text: node/edge labels and qualifiers are copied
verbatim from the IR. Its only editorial acts are (a) prefixing external labels
with `EXT:` if not already present, and (b) choosing solid vs dashed from the
edge `kind`.

Pure stdlib. Usage:
    python3 ir_to_d2.py IR.json [--classes d2-classes.d2] > out.d2
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_CLASSES = HERE.parent / "references" / "d2-classes.d2"

# Node-explainer mode is DENSITY-TRIGGERED (readability.md §2 / §10). When it
# fires, the canvas short label gets a "[n]" number prefix (symmetric with edge
# refs, a render affix like "EXT:") and the detail table becomes a numbered
# node walk-through. Below the trigger, the flat keyed table is used.
EXPLAINER_QUALIFIER_THRESHOLD = 3   # a node with >= this many detail lines is "dense"
EXPLAINER_EDGE_THRESHOLD = 12       # a view with >= this many edges is "dense"


def explainer_mode(ir: dict) -> bool:
    """True when this view is dense enough to warrant the numbered node explainer
    (any node carries >= N detail lines, OR the view has >= M edges)."""
    if len(ir.get("edges", [])) >= EXPLAINER_EDGE_THRESHOLD:
        return True
    for n in ir.get("nodes", []):
        d = n.get("detail")
        lines = len(d) if isinstance(d, list) else (1 if d else 0)
        if lines >= EXPLAINER_QUALIFIER_THRESHOLD:
            return True
    return False


def node_numbers(ir: dict) -> dict:
    """Assign a stable 1..N number to each node in IR order (locked, like edge
    refs). Only used in explainer mode. Returns {node_id: n}."""
    return {n["id"]: i for i, n in enumerate(ir.get("nodes", []), start=1)}

# IR kind -> D2 class. `family`/`emphasis` on a node can override the class
# (an external in the evidence-gap family renders orange, still double-bordered).
KIND_TO_CLASS = {
    "actor": "actor",
    "system": "system",
    "container": "container",
    "component": "container",
    "external": "external",
    "datastore": "datastore",
    "infra": "infra",
    "boundary": "boundary",
    # readability additions (see references/shape-vocabulary.md):
    "process": "process",              # dash-bordered = runtime process, not a deployable
    "not-a-component": "not-a-component",  # hexagon = deliberately not a component
}

# Shapes that must ONLY ever attach to one kind (checked here so a malformed IR
# fails at transform time, not silently at render time).
RESERVED_SHAPE_KINDS = {"datastore"}

# C4 Ch10 "add more words": the element template is Name / [Type] / Technology /
# Description. Type in square brackets kills the "is this box a system or a
# component?" ambiguity. We render the [Type] line ONLY for the kinds where the
# ambiguity actually bites — container/component — and only when the author has
# not already written a bracketed type into the label. Actors/datastores/
# externals carry their type in their reserved SHAPE, so a word is redundant
# there (and EXT: already says "external"). This is a render affix like EXT:/[n]
# — the verbatim label text is untouched; the affix is computed identically on
# the linter side so the verbatim check still passes.
TYPE_AFFIX_KINDS = {"container": "Container", "component": "Component"}


def type_affix(node: dict):
    """The bracketed type line to stack under the name, or None. Skipped when the
    author already put a '[...]' type in the label (no double type)."""
    word = TYPE_AFFIX_KINDS.get(node.get("kind"))
    if not word:
        return None
    if "[" in node.get("label", ""):
        return None  # author already carries an explicit [Type]
    tech = node.get("technology")
    return f"[{word}]" + (f" {tech}" if tech else "")


def esc(s: str) -> str:
    """Quote a D2 label.

    D2 double-quoted strings cannot span raw newlines, so a multi-line label
    (title + qualifier lines) is joined with the two-character escape ``\\n``,
    which D2 renders as a line break inside one <text> element. Embedded quotes
    and backslashes are escaped too.
    """
    s = s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    return '"' + s + '"'


def node_class(node: dict) -> str:
    kind = node["kind"]
    if kind not in KIND_TO_CLASS:
        sys.exit(f"ir_to_d2: unknown node kind {kind!r} on {node.get('id')!r}")
    # An orange evidence-gap external keeps the external shape but the gap fill.
    if node.get("family") == "evidence-gap":
        return "evidence-gap"
    if node.get("family") == "faded":
        return "faded"
    # Module/domain colour families (readability.md §7 colour-tracking): a module
    # keeps the SAME locked fill across every view. These classes exist in
    # d2-classes.d2; applying them here keeps the tracking un-driftable instead
    # of restyling nodes inline (SKILL.md gotcha "Don't restyle nodes inline").
    if node.get("family") in {"module-a", "module-b", "module-c", "module-d"}:
        return node["family"]
    return KIND_TO_CLASS[kind]


def node_label(node: dict, number: int = None) -> str:
    """Compose the SHORT canvas label: title + only the on-canvas qualifiers.

    Readability rule: `detail[]` is RELOCATED off the canvas into the node-detail
    table (see write_detail_tables); it is deliberately NOT included here.
    `qualifiers` is for the rare short line that stays on the canvas.

    External systems get an `EXT:` prefix if the model author didn't already
    write one, so the double-border convention is legible in grayscale.

    In explainer mode a stable "[n]" number prefix is added (a render affix, like
    `EXT:`), so the reader maps each node to its row in the numbered node
    explainer. The verbatim label text itself is unchanged, so the linter's
    verbatim check still sees it.
    """
    title = node["label"]
    if node["kind"] == "external" and not title.startswith("EXT:"):
        title = "EXT: " + title
    if number is not None:
        title = f"[{number}] " + title
    lines = [title]
    affix = type_affix(node)
    if affix is not None:
        lines.append(affix)                     # [Type] Technology, stacked under the name
    lines.extend(node.get("qualifiers", []))
    return "\n".join(lines)


def emit(ir: dict, classes_block: str) -> str:
    out = []
    view = ir.get("view", {})
    if view.get("title"):
        out.append(f"# {view['title']}")
    if view.get("caption"):
        # D2 top-level comment; the caption also belongs in the SVG <desc>,
        # which render.sh does not touch — the skill body notes this.
        out.append(f"# caption: {view['caption']}")
    direction = view.get("direction", "down")
    out.append(f"direction: {direction}")
    if view.get("grid_rows"):
        out.append(f"grid-rows: {view['grid_rows']}")
    if view.get("grid_columns"):
        out.append(f"grid-columns: {view['grid_columns']}")
    out.append("")
    out.append(classes_block.rstrip())
    out.append("")

    numbers = node_numbers(ir) if explainer_mode(ir) else {}
    for node in ir["nodes"]:
        cls = node_class(node)
        if node["kind"] in RESERVED_SHAPE_KINDS and cls != KIND_TO_CLASS[node["kind"]]:
            sys.exit(f"ir_to_d2: reserved kind {node['kind']!r} may not be reclassed")
        num = numbers.get(node["id"])
        near = node.get("near")
        near_clause = f"; near: {near}" if near else ""
        out.append(
            f"{node['id']}: {esc(node_label(node, num))} "
            f"{{ class: {cls}{near_clause} }}"
        )
    out.append("")

    for e in ir["edges"]:
        kind = e.get("kind", "sync")
        conn = "->"  # single-headed by design; no double-headed arrows, ever.
        # Readability: on dense views the canvas carries only a NUMBER; the full
        # claim lives in the edge-detail table. Prefer ref over a word label.
        if e.get("ref") is not None:
            canvas = str(e["ref"])
        else:
            canvas = e.get("label", "")
        label = f": {esc(canvas)}" if canvas != "" else ""
        line = f"{e['from']} {conn} {e['to']}{label}"
        style = []
        if kind == "async":
            style.append("style.stroke-dash: 3")   # dashed = asynchronous
        elif kind == "entangled":
            style.append("style.stroke-width: 4")   # thick = one marked entanglement edge
        elif kind != "sync":
            sys.exit(f"ir_to_d2: edge kind must be sync|async|entangled, got {kind!r}")
        if style:
            line += " { " + "; ".join(style) + " }"
        out.append(line)

    return "\n".join(out) + "\n"


# C4 Ch10: the meaning of every shape / line-style / colour actually used must be
# spelled out in a key. Because the render is deterministic, the key is generated
# TEXT describing only the notation THIS view uses — never a hand-kept boilerplate
# that could drift from the canvas.
KEY_KIND_GLOSS = {
    "actor": "stadium/pill = a person or role (actor)",
    "system": "heavy-stroke rectangle = the software system in focus",
    "container": "rectangle = an application or data store (C4 container)",
    "component": "rectangle = a grouping of code inside a container (C4 component)",
    "external": "double-bordered rectangle, `EXT:` = an external system we don't own",
    "datastore": "cylinder = a data store (used for datastores ONLY)",
    "infra": "rectangle = an infrastructure element",
    "boundary": "dashed-outline box = a boundary/grouping, not a node",
    "process": "dash-bordered rectangle = a runtime process, not a deployable",
    "not-a-component": "hexagon = an element deliberately NOT modelled as a component",
}
KEY_FAMILY_GLOSS = {
    "evidence-gap": "orange fill = unresolved production evidence (provisional/pending)",
    "faded": "faded fill/grey text = shown for context, not the subject of this view",
    "module-a": "module-a colour = the same module tracked by colour across every view",
    "module-b": "module-b colour = the same module tracked by colour across every view",
    "module-c": "module-c colour = the same module tracked by colour across every view",
    "module-d": "module-d colour = the same module tracked by colour across every view",
}
KEY_EDGE_GLOSS = {
    "sync": "solid arrow = synchronous call",
    "async": "dashed arrow = asynchronous message/event",
    "entangled": "thick arrow = a deliberately-marked entanglement edge",
}


def write_key(ir: dict) -> list:
    """Emit the diagram Key (C4 Ch10) as Markdown lines, listing ONLY the notation
    this view actually uses. Returns [] when the notation is trivial (one shape,
    all-sync, no colour families) — a key that restates the obvious is noise, and
    the linter's key check exempts that case symmetrically."""
    nodes = ir.get("nodes", [])
    kinds = [k for k in KEY_KIND_GLOSS if any(n.get("kind") == k for n in nodes)]
    families = [f for f in KEY_FAMILY_GLOSS if any(n.get("family") == f for n in nodes)]
    edge_kinds_present = {e.get("kind", "sync") for e in ir.get("edges", [])}
    edge_kinds = [k for k in KEY_EDGE_GLOSS if k in edge_kinds_present]
    # Trivial notation → no key (symmetric with the linter's exemption).
    non_sync = [k for k in edge_kinds if k != "sync"]
    if len(kinds) <= 1 and not families and not non_sync:
        return []
    lines = ["## Key", ""]
    for k in kinds:
        lines.append(f"- {KEY_KIND_GLOSS[k]}")
    for f in families:
        lines.append(f"- {KEY_FAMILY_GLOSS[f]}")
    for k in edge_kinds:
        lines.append(f"- {KEY_EDGE_GLOSS[k]}")
    if any(n.get("kind") in TYPE_AFFIX_KINDS for n in nodes):
        lines.append("- `[Type]` under a name = the element's C4 type (container/component)")
    lines.append("")
    return lines


def write_omitted(ir: dict) -> list:
    """Emit the 'not shown for brevity' note (C4 Ch12): crosscutting nodes
    (logging, audit) omitted to keep the canvas legible are declared in
    `view.omitted[]` and surfaced here so an omission is EXPLICIT and grounded,
    never mistaken for a dropped fact. Each entry: {label, note}."""
    omitted = ir.get("view", {}).get("omitted", [])
    if not omitted:
        return []
    lines = ["## Not shown for brevity", ""]
    for o in omitted:
        if isinstance(o, dict):
            label = o.get("label", "")
            note = o.get("note", "")
            lines.append(f"- **{label}** — {note}".rstrip(" —"))
        else:
            lines.append(f"- {o}")
    lines.append("")
    return lines


def write_detail_tables(ir: dict) -> str:
    """Render the per-view detail tables (Markdown) that carry the relocated
    facts. This is the companion artifact to the SVG — the reader treats
    label + table row as one unit (readability.md §2).

    Emits, as applicable:
      - a locator caption line (representational consistency)
      - a node-detail table keyed by node ID
      - an edge-detail table (numbered `| # | Edge | Mode | Claim |` when any
        edge has a ref; otherwise simple `| Edge | Detail |`)
    """
    view = ir.get("view", {})
    md = []
    title = view.get("title", view.get("id", "view"))
    md.append(f"# {title} — detail tables")
    md.append("")
    if view.get("caption"):
        md.append(f"> {view['caption']}")
        md.append("")

    # Locator line for non-context views.
    if view.get("opens"):
        parent = view.get("opens_from", "the previous view")
        comp = view.get("completeness", "")
        loc = f"**Locator:** this view opens `{view['opens']}` from `{parent}`."
        if comp.startswith("subset:"):
            base = comp.split(":", 1)[1]
            loc += f" It is a **subset** of `{base}` — not the complete edge set."
        elif comp == "complete":
            loc += " It is a **completeness reference** at this grain."
        md.append(loc)
        md.append("")

    # Node-detail table (only nodes that relocated something). In explainer mode
    # this becomes a NUMBERED walk-through so a reader maps the on-canvas "[n]"
    # prefix to a row; below the trigger it stays the flat keyed table.
    detailed = [n for n in ir["nodes"] if n.get("detail")]
    if detailed:
        numbers = node_numbers(ir) if explainer_mode(ir) else {}
        if numbers:
            md.append("## Node explainer (numbered — matches the `[n]` on the canvas)")
            md.append("")
            md.append("| # | Node | Detail the short label hides |")
            md.append("|---|------|------------------------------|")
            # walk in canvas-number order so the table reads top-to-bottom
            for n in sorted(detailed, key=lambda n: numbers[n["id"]]):
                joined = " ".join(n["detail"]) if isinstance(n["detail"], list) else str(n["detail"])
                md.append(f"| {numbers[n['id']]} | {n['id']} | {joined} |")
        else:
            md.append("## Node detail (keyed by node ID)")
            md.append("")
            md.append("| Node | Detail the short label hides |")
            md.append("|------|------------------------------|")
            for n in detailed:
                joined = " ".join(n["detail"]) if isinstance(n["detail"], list) else str(n["detail"])
                md.append(f"| {n['id']} | {joined} |")
        md.append("")

    # Edge-detail table.
    numbered = any(e.get("ref") is not None for e in ir["edges"])
    edge_detailed = [e for e in ir["edges"] if e.get("detail") or e.get("ref") is not None]
    if edge_detailed:
        md.append("## Edge detail")
        md.append("")
        if numbered:
            md.append("| # | Edge | Mode | Claim |")
            md.append("|---|------|------|-------|")
            for e in edge_detailed:
                ref = e.get("ref", "")
                mode = e.get("kind", "sync")
                claim = e.get("detail", e.get("label", ""))
                md.append(f"| {ref} | {e['from']} → {e['to']} | {mode} | {claim} |")
        else:
            md.append("| Edge | Detail the short label hides |")
            md.append("|------|------------------------------|")
            for e in edge_detailed:
                claim = e.get("detail", e.get("label", ""))
                md.append(f"| {e['from']} → {e['to']} | {claim} |")
        md.append("")

    # "Not shown for brevity" note (C4 Ch12) — declared omissions, kept grounded.
    md.extend(write_omitted(ir))
    # Diagram Key (C4 Ch10) — generated from the notation this view actually uses.
    md.extend(write_key(ir))

    return "\n".join(md) + "\n"


def write_view_md(ir: dict, svg_name: str) -> str:
    """The COMBINED per-view artifact (readability.md §10): the rendered image
    embedded FIRST, then the numbered node explainer + edge table beneath it — so
    image and its legend are one scrollable unit, not a cold separate file.

    `svg_name` is the image path AS REFERENCED FROM THE view.md (usually just the
    SVG basename, since render.sh writes both into the same OUTDIR).

    Export caveat (kept from readability.md §2): if a view's SVG is exported
    detached from this file (dropped into a slide), the honesty tags travel with
    the table, not the node. Re-inline the honesty tags onto the affected nodes
    for that standalone export. Short labels are the whole truth only WITH their
    table.
    """
    view = ir.get("view", {})
    title = view.get("title", view.get("id", "view"))
    md = [f"# {title}", ""]
    # Image first.
    md.append(f"![{title}]({svg_name})")
    md.append("")
    # Then the explainer + tables (write_detail_tables already emits caption,
    # locator, node explainer, and edge table). Strip its leading H1 so this file
    # has a single title.
    tables = write_detail_tables(ir)
    body = tables.split("\n", 1)[1] if tables.startswith("# ") else tables
    md.append(body.rstrip())
    md.append("")
    md.append("> **Export caveat:** if this diagram's SVG is used detached from "
              "this page (e.g. a slide), re-inline its honesty tags onto the "
              "affected nodes — off-canvas tags do not travel with a bare SVG.")
    md.append("")
    return "\n".join(md) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ir", help="path to the IR .json")
    ap.add_argument("--classes", default=str(DEFAULT_CLASSES),
                    help="path to the d2-classes.d2 block")
    ap.add_argument("--detail-out", default=None,
                    help="also write the flat per-view detail tables (Markdown) here "
                         "(for the SVG-alone path / backward compat)")
    ap.add_argument("--view-md-out", default=None,
                    help="also write the COMBINED view.md (image first, explainer "
                         "under it) here — the primary companion artifact")
    ap.add_argument("--svg-name", default=None,
                    help="image path referenced from the view.md (default: <view-id>.svg)")
    args = ap.parse_args()

    ir = json.loads(Path(args.ir).read_text(encoding="utf-8"))
    classes_block = Path(args.classes).read_text(encoding="utf-8")
    sys.stdout.write(emit(ir, classes_block))

    if args.detail_out:
        Path(args.detail_out).write_text(write_detail_tables(ir), encoding="utf-8")

    if args.view_md_out:
        svg_name = args.svg_name or f"{ir.get('view', {}).get('id', 'view')}.svg"
        Path(args.view_md_out).write_text(write_view_md(ir, svg_name), encoding="utf-8")


if __name__ == "__main__":
    main()
