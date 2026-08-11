#!/usr/bin/env python3
"""Deterministic diagram linter — the load-bearing reliability mechanism.

Detection is deterministic and runs in milliseconds; it never hallucinates a
passing result. Correction is left to the LLM, fed this linter's exact
messages. That division (detection deterministic, correction LLM) is far more
reliable than LLM self-critique, whose worst failure mode is confidently
approving wrong output (diagramskill.md, "Deterministic validation beats
self-critique").

Generalized from docs/silicon-sandwiches-diagrams/verify_labels.py: that
prototype hardcoded one diagram's labels. This reads the fact-frozen IR
(references/ir-schema.md) as the contract and checks any rendered SVG (plus its
optional D2 source and grayscale proof) against it.

Checks (each maps to a rule in references/acceptance-checklist.md):
  1. verbatim-labels : every IR node/edge label appears verbatim in the SVG
  2. shape-kind      : cylinders only for datastore kind; EXT: only on external
  3. no-double-arrow : no double-headed arrows (SVG marker-start / D2 <-> <-)
  4. real-text       : SVG has real <text> elements, not paths/raster
  5. min-font        : no <text> below the minimum font-size (default 11px)
  6. forbidden-facts : no invented vendor/region/SLA patterns from the IR
  7. grayscale-proof : the grayscale proof PNG exists (colour never alone)

Exit 0 iff all checks pass. Pure stdlib. Usage:
    python3 lint_diagram.py --ir IR.json --svg VIEW.svg \\
        [--d2 VIEW.d2] [--proof proofs/VIEW-gray.png] [--min-font 11]
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

# Reuse the ONE source of truth for tag derivation + parity, so the linter checks
# exactly what decompose.py sliced and ir_to_d2.py numbered (no drift).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from decompose import parity as decomp_parity  # noqa: E402
from ir_to_d2 import explainer_mode, node_numbers  # noqa: E402


# ---- text extraction (kept from verify_labels.py) ---------------------------

def svg_texts(raw: str):
    """Return the list of raw <text>...</text> run contents (unescaped)."""
    runs = re.findall(r"<text[^>]*>(.*?)</text>", raw, re.S)
    return [html.unescape(r) for r in runs]


def normalize(s: str) -> str:
    """Collapse whitespace and fold dash/quote variants the renderer may set.

    The renderer is permitted to re-break lines and normalize punctuation, but
    NOT to reword. Comparing normalized strings catches paraphrase/truncation
    while tolerating a legitimate line re-break.
    """
    s = s.replace("–", "-").replace("—", "-")
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip()


# ---- the checks -------------------------------------------------------------

def required_labels(ir: dict):
    """Every label that must appear ON THE CANVAS (the SVG): node short titles,
    on-canvas qualifier lines, and word edge labels. `detail[]` is deliberately
    RELOCATED off the canvas — it is checked against the detail table instead
    (see relocated_facts / check_grounded_relocation). Edges using a numbered
    `ref` carry only the number on canvas, so their claim is a relocated fact,
    not a canvas label."""
    labels = []
    for n in ir.get("nodes", []):
        title = n["label"]
        if n["kind"] == "external" and not title.startswith("EXT:"):
            title = "EXT: " + title
        labels.append(title)
        labels.extend(n.get("qualifiers", []))
    for e in ir.get("edges", []):
        # A word label on the canvas only when there is no numbered ref.
        if e.get("label") and e.get("ref") is None:
            labels.append(e["label"])
    return labels


def relocated_facts(ir: dict):
    """Every fact the IR moved OFF the canvas into a detail table: node detail[]
    strings and edge detail strings (and the claim of any numbered-ref edge).
    These must appear in the detail-table artifact — the groundedness contract
    that makes 'nothing dropped, only relocated' enforceable."""
    facts = []
    for n in ir.get("nodes", []):
        d = n.get("detail")
        if isinstance(d, list):
            facts.extend(d)
        elif d:
            facts.append(d)
    for e in ir.get("edges", []):
        if e.get("detail"):
            facts.append(e["detail"])
    return facts


def check_verbatim_labels(ir, svg_joined, fails):
    for needle in required_labels(ir):
        if normalize(needle) not in svg_joined:
            fails.append(f"verbatim-labels: MISSING {needle!r}")


def check_grounded_relocation(ir, detail_joined, fails):
    """Groundedness: every relocated fact must land in the detail table. Without
    this, moving detail off a node could silently drop it — the exact failure
    the readability technique risks. Only runs when a detail table is provided."""
    if detail_joined is None:
        # No detail table supplied; if the IR relocated facts, that's a gap.
        if relocated_facts(ir):
            fails.append("grounded-relocation: IR has relocated detail[] but no "
                         "--detail table was provided to check it landed")
        return
    for fact in relocated_facts(ir):
        if normalize(fact) not in detail_joined:
            fails.append(f"grounded-relocation: relocated fact absent from detail table: {fact!r}")


def check_locator_caption(ir, detail_joined, fails):
    """Representational consistency: a non-context view must locate itself in its
    parent (readability.md §6). Checked against the detail-table artifact, which
    is where the transformer writes the locator line."""
    view = ir.get("view", {})
    if view.get("level") == "context":
        return  # the context view opens nothing
    if not view.get("opens"):
        fails.append("locator-caption: non-context view does not declare view.opens "
                     "(no representational-consistency locator)")
        return
    if detail_joined is not None and "locator" not in detail_joined.lower():
        fails.append("locator-caption: detail table has no Locator line")


def check_edge_refs_resolve(ir, detail_joined, fails):
    """Every numbered canvas edge ref must resolve to exactly one detail row."""
    if detail_joined is None:
        return
    for e in ir.get("edges", []):
        if e.get("ref") is not None and not e.get("detail"):
            fails.append(f"edge-refs: edge {e['from']}->{e['to']} has ref "
                         f"{e['ref']} but no detail claim to resolve it")


def check_label_density(ir, max_lines, fails):
    """De-clutter: a node's ON-CANVAS text (short label + on-canvas qualifiers)
    should be short. Heavy detail belongs in detail[], not on the node. Flags a
    node whose canvas lines exceed the budget so it gets relocated."""
    for n in ir.get("nodes", []):
        canvas_lines = 1 + len(n.get("qualifiers", []))
        if canvas_lines > max_lines:
            fails.append(f"label-density: node {n['id']!r} shows {canvas_lines} lines "
                         f"on canvas (budget {max_lines}); move detail to detail[]")


def check_node_explainer(ir, detail_joined, fails):
    """When explainer mode is triggered, every node that relocated detail must
    have a numbered explainer row (symmetric to the edge-ref check). The canvas
    carries a `[n]` prefix; the reader must be able to resolve every one."""
    if not explainer_mode(ir):
        return
    if detail_joined is None:
        return  # nothing to check against
    numbers = node_numbers(ir)
    for n in ir.get("nodes", []):
        if not n.get("detail"):
            continue
        num = numbers[n["id"]]
        # The explainer row starts "| <num> | <id> |"; normalize() collapsed the
        # table, so look for the "| n | id " signature.
        if f"| {num} | {n['id']} " not in detail_joined and \
           f"|{num}|{n['id']}" not in detail_joined.replace(" ", ""):
            fails.append(f"node-explainer: node {n['id']!r} shows [{num}] on canvas "
                         f"but has no numbered explainer row")


def check_no_floating_boundary(ir, fails):
    """ENV/Q1 policy (iteration 2): a boundary/quantum fact must be RELOCATED into
    the bounded node's detail[] text — NOT drawn as a free-floating boundary box
    that reads as a legend item rather than a container. Until true nested
    containment lands, a `kind: boundary` node with NO members enclosing it is
    forbidden; the transformer cannot nest, so such a node can only mislead."""
    for n in ir.get("nodes", []):
        if n.get("kind") == "boundary":
            fails.append(f"floating-boundary: node {n['id']!r} is kind 'boundary' — "
                         "the transformer cannot nest, so this renders as a "
                         "free-floating box that misleads. Relocate the "
                         "boundary/quantum fact into the bounded node's detail[] "
                         "instead (iteration-2 policy).")


def check_forbidden_facts(ir, svg_joined, fails):
    for pat in ir.get("forbidden_facts", []):
        if re.search(pat, svg_joined, re.I):
            fails.append(f"forbidden-facts: invented pattern {pat!r} present")


# ---- C4-Book signals (iteration 3, see docs/research/c4-book-signal-triage.md)

# Deployment nouns forbidden on a container/component/context/landscape view.
# C4 rule (Ch4/Ch8): "say nothing about deployment" on a container diagram —
# clusters, replicas, load balancers, regions belong on a DEPLOYMENT diagram,
# which most software has several of (one per environment). Showing them on a
# container view fixes it to a single environment and misleads. Enforced as an
# automatic extension of forbidden-facts, ACTIVE ONLY for non-deployment views.
# Only HIGH-SIGNAL deployment nouns — words that almost never mean anything but
# deployment topology. Deliberately EXCLUDES "cluster" and "namespace": both are
# legitimately used for LOGICAL groupings on component views ("Cluster A" = a
# grouping of components, not a compute cluster), so gating them by default would
# fire false positives. A Kubernetes/compute cluster is caught by its specific
# nouns (kubernetes/k8s/pod/replica) instead.
DEPLOYMENT_NOUNS = [
    r"\bkubernetes\b", r"\bk8s\b", r"\bpods?\b", r"\breplica(?:s|set)?\b",
    r"\bload[- ]?balancer\b", r"\bautoscal", r"\bavailability zone\b", r"\bAZ-?\d",
    r"\bhelm chart\b", r"\bfargate\b", r"\bECS task\b", r"\bnode ?pool\b",
    r"\b(?:us|eu|ap|sa|ca)-(?:east|west|north|south|central)-\d\b",  # region codes
]


def check_deployment_nouns(ir, svg_joined, fails):
    """A container/component/context/landscape view must not name deployment
    topology (C4 Ch4/Ch8). Deployment diagrams (view.level == 'deployment') are
    exactly where these belong, so they are exempt. An IR that legitimately needs
    a deployment noun on such a view can opt out with view.allow_deployment: true
    (the escape hatch — used rarely, e.g. an infra node whose name IS a LB)."""
    view = ir.get("view", {})
    if view.get("level") == "deployment" or view.get("allow_deployment"):
        return
    for pat in DEPLOYMENT_NOUNS:
        m = re.search(pat, svg_joined, re.I)
        if m:
            fails.append(f"deployment-noun: {m.group(0)!r} names deployment topology on a "
                         f"{view.get('level', '?')} view — deployment belongs on a "
                         "deployment diagram (C4 Ch4/Ch8). Move it, or set "
                         "view.allow_deployment if this view genuinely is about an "
                         "infrastructure element.")


# Vague edge verbs. C4 rule (Ch10): "avoid general words such as 'uses'"; label
# every arrow with a SPECIFIC verb describing intent. The preposition half
# (end with to/from/with) is guidance, not enforced — a heuristic mis-fires too
# often. Only the banned-word slice is deterministic enough to gate.
BANNED_EDGE_LABELS = {
    "uses", "use", "used by", "using",
    "calls", "call",              # too generic on its own; "makes API calls to" is fine
    "connects to", "connects", "talks to", "communicates with",
    "interacts with", "depends on", "links to", "relates to",
    "sends to", "gets from",      # missing WHAT is sent/gotten
}


def check_edge_label_verbs(ir, fails):
    """Reject a bare vague verb as an edge's on-canvas word label (C4 Ch10). Only
    checks WORD labels — a numbered `ref` edge carries its verb in the detail
    claim, checked elsewhere. Matches the whole normalized label, so a specific
    phrase that merely CONTAINS 'uses' (e.g. 'uses OAuth to authenticate with')
    passes; only a label that IS the vague word fails."""
    for e in ir.get("edges", []):
        if e.get("ref") is not None:
            continue  # numbered edge: verb lives in the detail claim
        label = e.get("label", "")
        if label and normalize(label).lower() in BANNED_EDGE_LABELS:
            fails.append(f"edge-verb: edge {e['from']}->{e['to']} label {label!r} is a "
                         "vague verb (C4 Ch10: use a specific verb + preposition, "
                         "e.g. 'makes API requests to', not 'uses')")


def check_technology_present(ir, fails):
    """C4 rule (Ch4/Ch10): a CONTAINER carries its technology choice; a missing
    technology is the book's #1 anti-pattern. Scoped to `kind: container` ONLY —
    components are in-process and the book explicitly says component-to-component
    technology is unneeded (Ch5), and datastores/externals/actors carry no tech.
    A container may satisfy this with a `technology` field OR an explicit
    honesty tag (TECH: UNKNOWN / TBD) in a qualifier/detail, matching the
    skill's existing 'unknowns become explicit tags' mechanic."""
    for n in ir.get("nodes", []):
        if n.get("kind") != "container":
            continue
        if n.get("technology"):
            continue
        blob = " ".join([n.get("label", "")] + list(n.get("qualifiers", []))
                        + (n.get("detail", []) if isinstance(n.get("detail"), list) else []))
        if re.search(r"\bTECH:\s*(UNKNOWN|TBD|PROVISIONAL)", blob, re.I):
            continue
        fails.append(f"technology: container {n['id']!r} has no technology (field or "
                     "'TECH: UNKNOWN' honesty tag) — C4 Ch4 requires the technology "
                     "choice on a container, or an explicit unknown.")


def check_key_present(ir, detail_joined, fails):
    """C4 rule (Ch10, the most-repeated): "always include a key". The diagram must
    be interpretable when extracted from its explaining doc, so any notation that
    carries meaning (>1 shape-class in use, async/entangled line-styles, or a
    colour-coding family) needs a key entry.

    Enforced against the detail-table / view.md artifact (where a prose key
    belongs — the render is deterministic, so the key is TEXT, not a drawn box).
    A view whose notation is trivial (one shape, all-sync, no families) needs no
    key and is exempt. `view.key: false` is an explicit opt-out for a view that
    genuinely needs none but tripped the heuristic."""
    view = ir.get("view", {})
    if view.get("key") is False:
        return
    nodes = ir.get("nodes", [])
    kinds = {n.get("kind") for n in nodes}
    families = {n.get("family") for n in nodes if n.get("family")}
    edge_kinds = {e.get("kind", "sync") for e in ir.get("edges", [])}
    # What notation is actually in play beyond the trivial baseline?
    needs_key = (len(kinds) > 1) or bool(families) or (edge_kinds - {"sync"})
    if not needs_key:
        return
    if detail_joined is None:
        fails.append("key: view uses >1 shape/line/colour notation but no detail "
                     "artifact was provided to hold the key (C4 Ch10: always "
                     "include a key)")
        return
    if "key" not in detail_joined.lower() and "legend" not in detail_joined.lower():
        fails.append("key: view uses meaningful notation (multiple shapes / async "
                     "or entangled lines / colour families) but the detail artifact "
                     "has no Key or Legend section (C4 Ch10: always include a key).")


def check_real_text(texts, fails):
    if len(texts) < 1:
        fails.append("real-text: SVG has no <text> elements (flattened to paths/raster?)")


def check_min_font(raw, min_font, fails):
    for size in re.findall(r"font-size:\s*(\d+(?:\.\d+)?)px", raw):
        if float(size) < min_font:
            fails.append(f"min-font: font-size {size}px below minimum {min_font}px")
            return  # one report is enough


def check_no_double_arrow(raw, d2_src, fails):
    # SVG side: a single-headed arrow has marker-end only; marker-start on a
    # connection means a second arrowhead.
    if re.search(r'<[^>]*class="[^"]*connection[^"]*"[^>]*marker-start=', raw):
        fails.append("no-double-arrow: a connection carries marker-start (double-headed)")
    # D2 authoring side: <-> is a double-headed connector; <- is a reversed one
    # the transformer never emits. Catch either if a hand-edited .d2 sneaks in.
    if d2_src is not None:
        for m in re.findall(r"[A-Za-z0-9_.]+\s*(<->|<-)\s*[A-Za-z0-9_.]+", d2_src):
            fails.append(f"no-double-arrow: D2 source uses {m!r} connector")
            break


def check_shape_kind(ir, raw, fails):
    # Cylinders are reserved for datastore. If the SVG renders a cylinder but no
    # IR node is a datastore, something mis-mapped.
    has_cylinder = "cylinder" in raw
    has_datastore = any(n["kind"] == "datastore" for n in ir.get("nodes", []))
    if has_cylinder and not has_datastore:
        fails.append("shape-kind: SVG has a cylinder but IR declares no datastore")
    # EXT: prefix should only mark external nodes. Every EXT:-labelled node in
    # the IR must be kind external (transform guarantees it; guard hand-edits).
    for n in ir.get("nodes", []):
        if n["label"].startswith("EXT:") and n["kind"] != "external":
            fails.append(f"shape-kind: node {n['id']!r} labelled EXT: but kind={n['kind']!r}")


def check_grayscale_proof(proof, fails):
    if proof is None:
        return  # not requested
    if not Path(proof).exists():
        fails.append(f"grayscale-proof: proof image missing at {proof}")


# ---- set-level checks (decomposition: primary + overlays) -------------------

def check_overlay_parity(primary_ir, overlay_irs, fails):
    """The load-bearing groundedness check for decomposition: the union of all
    overlay edge sets equals the primary's edge set exactly, and every overlay
    edge keeps the primary's `ref` (numbering locked). Reuses decompose.parity so
    the linter checks precisely what the engine produced."""
    missing, extra, conflicts = decomp_parity(primary_ir, overlay_irs)
    for k in missing:
        fails.append(f"overlay-parity: primary edge {k} appears in NO overlay "
                     "(a fact was dropped by the split)")
    for k in extra:
        fails.append(f"overlay-parity: overlay edge {k} is not in the primary "
                     "(an edge was invented by the split)")
    for (frm, to, pref, oref) in conflicts:
        fails.append(f"overlay-parity: edge {frm}->{to} has ref {oref} in an overlay "
                     f"but {pref} in the primary (numbering not locked)")


def check_drilldown_links(view_irs, fails, strict=False):
    """A view's `opens_from` must name a view id that EXISTS in the produced set.
    This is the real Eval-1 bug: a locator said 'opens C2a' but C2a was never
    produced, leaving a dangling drill-down link.

    Scope: a set-lint owns the decomposition set (a primary + its overlays), which
    all share the primary's id stem (before `--`). A link to a DIFFERENT-STEM view
    (a container primary opening from its context view) is one grain UP and is
    produced by a sibling render.sh call, so it is out of scope here — skipped
    unless `strict` (a whole-project lint that produced every level together)."""
    produced = {v.get("view", {}).get("id") for v in view_irs}
    stems = {(pid or "").split("--", 1)[0] for pid in produced}
    for v in view_irs:
        view = v.get("view", {})
        parent = view.get("opens_from")
        if not parent or parent in produced:
            continue
        parent_stem = parent.split("--", 1)[0]
        in_scope = strict or parent_stem in stems
        if in_scope:
            fails.append(f"drilldown-link: view {view.get('id')!r} locator names parent "
                         f"{parent!r}, but {parent!r} was not produced in this set")


def check_entanglement_preserved(primary_ir, overlay_irs, fails):
    """Every `entangled` edge in the primary that lands in an overlay must still be
    `kind: entangled` there — readability may relocate a fact, never soften a
    marked one (feedback: the entanglement edge must survive the readability pass,
    not get smoothed away)."""
    ent = {(e["from"], e["to"]) for e in primary_ir.get("edges", [])
           if e.get("kind") == "entangled"}
    for ov in overlay_irs:
        for e in ov.get("edges", []):
            if (e["from"], e["to"]) in ent and e.get("kind") != "entangled":
                fails.append(f"entanglement: edge {e['from']}->{e['to']} is entangled in "
                             f"the primary but {e.get('kind')!r} in overlay "
                             f"{ov.get('view', {}).get('id')!r} (softened)")


def lint_set(primary_path, overlay_paths, fails, strict_drilldown=False):
    """Set-level lint: parity + drill-down + entanglement across a primary and its
    overlays. Per-view correctness is still each view's own `lint` invocation.

    `strict_drilldown` treats EVERY `opens_from` as in-scope — use it only for a
    whole-project lint that produced all levels together; a single view's
    render.sh set does not include the grain above it."""
    primary_ir = json.loads(Path(primary_path).read_text(encoding="utf-8"))
    overlay_irs = [json.loads(Path(p).read_text(encoding="utf-8")) for p in overlay_paths]
    check_overlay_parity(primary_ir, overlay_irs, fails)
    check_entanglement_preserved(primary_ir, overlay_irs, fails)
    # drill-down integrity spans the whole produced set (primary + overlays)
    check_drilldown_links([primary_ir] + overlay_irs, fails, strict=strict_drilldown)
    return primary_ir, overlay_irs


# ---- driver -----------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ir", help="the view IR (per-view mode)")
    ap.add_argument("--svg", help="the rendered SVG (per-view mode)")
    ap.add_argument("--d2", default=None, help="optional D2 source for authoring-level checks")
    ap.add_argument("--proof", default=None, help="optional grayscale proof PNG to require")
    ap.add_argument("--detail", default=None,
                    help="optional detail-table Markdown to check relocated facts landed")
    ap.add_argument("--min-font", type=float, default=11.0)
    ap.add_argument("--max-canvas-lines", type=int, default=3,
                    help="max on-canvas lines per node before detail must be relocated")
    # Set-level mode: parity + drill-down + entanglement across a decomposed set.
    ap.add_argument("--primary", default=None,
                    help="SET MODE: the primary view IR to check overlays against")
    ap.add_argument("--overlays", nargs="*", default=None,
                    help="SET MODE: the overlay IRs produced by decompose.py")
    ap.add_argument("--strict-drilldown", action="store_true",
                    help="SET MODE: enforce EVERY opens_from (whole-project lint "
                         "that produced all levels together)")
    args = ap.parse_args()

    # ---- set-level mode -----------------------------------------------------
    if args.primary is not None:
        fails = []
        primary_ir, overlay_irs = lint_set(args.primary, args.overlays or [], fails,
                                           strict_drilldown=args.strict_drilldown)
        pid = primary_ir.get("view", {}).get("id", args.primary)
        n_ov = len(overlay_irs)
        n_edges = len(primary_ir.get("edges", []))
        print(f"{'PASS' if not fails else 'FAIL'}  set {pid}: "
              f"{n_ov} overlays, {n_edges} primary edges, {len(fails)} failure(s)")
        for f in fails:
            print(f"       {f}")
        sys.exit(1 if fails else 0)

    # ---- per-view mode (default; backward compatible) -----------------------
    if not args.ir or not args.svg:
        ap.error("per-view mode requires --ir and --svg (or use --primary/--overlays for set mode)")

    ir = json.loads(Path(args.ir).read_text(encoding="utf-8"))
    raw = Path(args.svg).read_text(encoding="utf-8")
    d2_src = Path(args.d2).read_text(encoding="utf-8") if args.d2 else None
    detail_joined = None
    if args.detail:
        detail_joined = normalize(Path(args.detail).read_text(encoding="utf-8"))

    texts = svg_texts(raw)
    svg_joined = normalize(" ".join(texts))

    fails = []
    # Correctness checks (the original gate).
    check_verbatim_labels(ir, svg_joined, fails)
    check_shape_kind(ir, raw, fails)
    check_no_double_arrow(raw, d2_src, fails)
    check_real_text(texts, fails)
    check_min_font(raw, args.min_font, fails)
    check_forbidden_facts(ir, svg_joined, fails)
    check_grayscale_proof(args.proof, fails)
    # C4-Book correctness signals (iteration 3).
    check_deployment_nouns(ir, svg_joined, fails)
    check_edge_label_verbs(ir, fails)
    check_technology_present(ir, fails)
    check_key_present(ir, detail_joined, fails)
    # Invented facts / deployment nouns must not hide in the detail table either.
    if detail_joined is not None:
        check_forbidden_facts(ir, detail_joined, fails)
        check_deployment_nouns(ir, detail_joined, fails)

    # Readability + groundedness checks (the improvement).
    check_grounded_relocation(ir, detail_joined, fails)
    check_locator_caption(ir, detail_joined, fails)
    check_edge_refs_resolve(ir, detail_joined, fails)
    check_label_density(ir, args.max_canvas_lines, fails)
    # Decomposition-era per-view checks (iteration 2).
    check_node_explainer(ir, detail_joined, fails)
    check_no_floating_boundary(ir, fails)

    view = ir.get("view", {}).get("id", args.svg)
    total_labels = len(required_labels(ir))
    label_fails = sum(1 for f in fails if f.startswith("verbatim-labels"))
    n_relocated = len(relocated_facts(ir))
    print(f"{'PASS' if not fails else 'FAIL'}  {view}: "
          f"{total_labels - label_fails}/{total_labels} canvas labels verbatim, "
          f"{n_relocated} relocated facts, "
          f"{len(texts)} <text> elements, {len(fails)} failure(s)")
    for f in fails:
        print(f"       {f}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
