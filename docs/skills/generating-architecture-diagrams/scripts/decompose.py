#!/usr/bin/env python3
"""Deterministic density-triggered decomposition.

A dense view (many edges, or one node with a large fan-in/out) is unreadable as a
single canvas even when every edge is numbered — the *routing* still collides.
The fix (references/readability.md §1) is to keep the full view as the
authoritative PRIMARY and emit companion OVERLAYS, each showing a
deterministically-selected subset of the primary's edges.

The selection is CODE, not judgement, so the same IR always yields the same
overlays (the "two runs picked different slices" failure this closes). Two
selectors, both tag-driven:

  by-theme   : group edges by `theme` in {structural, provenance, model-call,
               external-boundary}. `theme` is usually derived from node tags
               (target kind==external; target role==lineage-store; target/source
               role==model-seam) — never from keyword matching.
  by-module  : group edges by the module family (module-a/b/c/d) of the edge's
               module endpoint.

Two guarantees (references/ir-schema.md "Decomposition fields"):
  * numbering locked — an edge keeps its `ref` in the primary and every overlay;
  * parity — union(overlay edges) == primary edges, exactly.

`derive_theme` / `derive_module` are imported by ir_to_d2.py and lint_diagram.py
so the tag logic lives in ONE place and cannot drift.

Pure stdlib. Usage:
    python3 decompose.py PRIMARY_IR.json --out-dir DIR \\
        [--selector auto|by-theme|by-module|none] \\
        [--edge-threshold 30] [--fanout-threshold 12]
Prints a manifest (one line per artifact) to stdout; writes overlay IRs to DIR.
Exit 0 always on a well-formed IR; exit 2 on a malformed one.
"""
import argparse
import json
import sys
from collections import Counter, OrderedDict
from pathlib import Path

DEFAULT_EDGE_THRESHOLD = 30
DEFAULT_FANOUT_THRESHOLD = 12
MODULE_FAMILIES = ("module-a", "module-b", "module-c", "module-d")

# Human-readable overlay questions, keyed by theme, used to author the overlay
# caption (readability.md §6 subset form). Pure formatting — no facts invented.
THEME_QUESTION = {
    "structural": "the structural topology — orchestration fan-out, handoffs, and the marked entanglement edge",
    "provenance": "the provenance/lineage writes into the append-only store",
    "model-call": "the model-call seam and its gateway",
    "external-boundary": "the edges that cross the system's external boundary",
}


# ---- deterministic tag derivation (the single source of truth) --------------

def _nodes_by_id(ir):
    return {n["id"]: n for n in ir.get("nodes", [])}


def derive_theme(edge, nodes_by_id):
    """Return the edge's theme. An explicit edge['theme'] always wins; otherwise
    derive it from node tags in priority order (external-boundary > provenance >
    model-call > structural). Deterministic; no keyword matching."""
    explicit = edge.get("theme")
    if explicit:
        return explicit
    tgt = nodes_by_id.get(edge["to"], {})
    src = nodes_by_id.get(edge["from"], {})
    # A marked entanglement edge is a STRUCTURAL fact by definition — it is drawn
    # thick precisely so it reads in the base topology and "can't be skimmed
    # past" (readability line-semantics). Classify it structural regardless of
    # what it connects, so it appears in the base topology overlay, not buried in
    # a theme slice. (An explicit theme above still wins if the author insists.)
    if edge.get("kind") == "entangled":
        return "structural"
    if tgt.get("kind") == "external":
        return "external-boundary"
    if tgt.get("role") == "lineage-store":
        return "provenance"
    # model-call: target OR source is the model seam (the seam's own outbound
    # call to the gateway is a model-call edge too). Pure role check.
    if tgt.get("role") == "model-seam" or src.get("role") == "model-seam":
        return "model-call"
    return "structural"


def derive_module(edge, nodes_by_id):
    """Return the module key for by-module grouping, or None. Explicit
    edge['module'] wins; else the family of whichever endpoint is a module node
    (source preferred, then target). Only module-a/b/c/d count as module families."""
    explicit = edge.get("module")
    if explicit:
        return explicit
    for end in (edge["from"], edge["to"]):
        fam = nodes_by_id.get(end, {}).get("family")
        if fam in MODULE_FAMILIES:
            return fam
    return None


# ---- density gate + selector choice -----------------------------------------

def _degree(ir):
    """incident-edge count per node id (in + out)."""
    deg = Counter()
    for e in ir.get("edges", []):
        deg[e["from"]] += 1
        deg[e["to"]] += 1
    return deg


def should_decompose(ir, edge_thr, fanout_thr):
    """The density gate. Returns (bool, reason) so the trigger is logged, never
    silent. Fires on total edge count OR a single node's incident-edge degree."""
    n_edges = len(ir.get("edges", []))
    if n_edges >= edge_thr:
        return True, f"{n_edges} edges >= edge-threshold {edge_thr}"
    deg = _degree(ir)
    if deg:
        node, d = deg.most_common(1)[0]
        if d >= fanout_thr:
            return True, f"node {node!r} has degree {d} >= fanout-threshold {fanout_thr}"
    return False, f"{n_edges} edges, max degree {max(deg.values()) if deg else 0} — below trigger"


def choose_selector(ir, override):
    """Pick the selector DETERMINISTICALLY from the IR (the fix for 'same source,
    different slice'). Author override via --selector or view.overlays wins;
    otherwise: by-theme when any node carries a non-default role (a theme signal
    is present), else by-module when module families exist, else none."""
    if override and override != "auto":
        return override
    view_pref = ir.get("view", {}).get("overlays", "auto")
    if view_pref and view_pref != "auto":
        return view_pref
    nodes = ir.get("nodes", [])
    if any(n.get("role") in ("lineage-store", "model-seam") for n in nodes):
        return "by-theme"
    if any(n.get("family") in MODULE_FAMILIES for n in nodes):
        return "by-module"
    return "none"


# ---- overlay construction ----------------------------------------------------

def _group_edges(ir, selector, nodes_by_id):
    """Return an OrderedDict key -> [edges] using the chosen selector. Order is
    first-appearance so overlay ids are stable across runs."""
    groups = OrderedDict()
    for e in ir.get("edges", []):
        if selector == "by-theme":
            key = derive_theme(e, nodes_by_id)
        elif selector == "by-module":
            key = derive_module(e, nodes_by_id) or "unclustered"
        else:
            raise ValueError(f"unknown selector {selector!r}")
        groups.setdefault(key, []).append(e)
    return groups


def _overlay_caption(ir, selector, key, edges):
    primary_id = ir.get("view", {}).get("id", "the primary view")
    opens = ir.get("view", {}).get("opens")
    where = f" opening `{opens}`" if opens else ""
    if selector == "by-theme":
        q = THEME_QUESTION.get(key, f"the {key} edges")
        return (f"This view is a subset of `{primary_id}`{where} — only {q}. "
                f"Edge numbers match the primary; see `{primary_id}` for the complete edge set.")
    return (f"This view is a subset of `{primary_id}`{where} — only the edges owned by "
            f"`{key}`. Edge numbers match the primary; see `{primary_id}` for the complete edge set.")


def build_overlays(ir, selector):
    """Emit one overlay IR per group. Each overlay:
      * reuses primary node ids (colour-tracking) restricted to endpoints touched;
      * keeps every edge's original `ref` (numbering locked);
      * keeps `kind:entangled` on marked edges;
      * declares completeness subset:<primary> and copies opens/opens_from so the
        locator caption renders and the drill-down link resolves.
    Returns a list of (overlay_id, overlay_ir)."""
    nodes_by_id = _nodes_by_id(ir)
    primary_id = ir.get("view", {}).get("id", "view")
    groups = _group_edges(ir, selector, nodes_by_id)
    overlays = []
    for key, edges in groups.items():
        touched = OrderedDict()
        for e in edges:
            for end in (e["from"], e["to"]):
                if end in nodes_by_id and end not in touched:
                    touched[end] = nodes_by_id[end]
        overlay_id = f"{primary_id}--{key}"
        base_view = dict(ir.get("view", {}))
        base_view.update({
            "id": overlay_id,
            "title": f"{base_view.get('title', primary_id)} — {key} overlay",
            "caption": _overlay_caption(ir, selector, key, edges),
            "completeness": f"subset:{primary_id}",
            "primary_of": primary_id,   # tool-set back-link (ir-schema)
            "opens_from": primary_id,   # an overlay drills down FROM its primary,
                                        #   not from the primary's own parent
            "overlays": "none",         # an overlay is never itself decomposed
        })
        # `opens` (the box) carries through from the primary view dict already.
        overlay_ir = {
            "view": base_view,
            "nodes": list(touched.values()),
            "edges": [dict(e) for e in edges],   # refs preserved verbatim
            "forbidden_facts": ir.get("forbidden_facts", []),
        }
        overlays.append((overlay_id, overlay_ir))
    return overlays


# ---- parity (the groundedness of the split) ---------------------------------

def _edge_key(e):
    return (e["from"], e["to"], e.get("ref"))


def parity(primary_ir, overlay_irs):
    """Return (missing_from_overlays, extra_in_overlays, ref_conflicts).
    All three must be empty for the decomposition to be grounded."""
    prim = {_edge_key(e): e for e in primary_ir.get("edges", [])}
    seen = {}
    ref_conflicts = []
    for ov in overlay_irs:
        for e in ov.get("edges", []):
            k = _edge_key(e)
            seen[k] = e
            # ref must match the primary's ref for the same from/to
            for pe in primary_ir.get("edges", []):
                if pe["from"] == e["from"] and pe["to"] == e["to"] and pe.get("ref") != e.get("ref"):
                    ref_conflicts.append((e["from"], e["to"], pe.get("ref"), e.get("ref")))
    missing = [k for k in prim if k not in seen]
    extra = [k for k in seen if k not in prim]
    return missing, extra, ref_conflicts


# ---- driver -----------------------------------------------------------------

def decompose(ir, selector_override, edge_thr, fanout_thr):
    """Return (selector, trigger_reason, overlays[list of (id, ir)]). overlays is
    empty when the view is below the density trigger or selector resolves none."""
    fire, reason = should_decompose(ir, edge_thr, fanout_thr)
    selector = choose_selector(ir, selector_override)
    forced = bool(selector_override and selector_override != "auto") or \
        ir.get("view", {}).get("overlays") in ("by-theme", "by-module")
    if selector == "none" or (not fire and not forced):
        return selector, reason, []
    overlays = build_overlays(ir, selector)
    # A single-group decomposition is pointless (the overlay == the primary).
    if len(overlays) < 2:
        return selector, reason + " (single group — no split)", []
    return selector, reason, overlays


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ir", help="path to the PRIMARY view IR .json")
    ap.add_argument("--out-dir", required=True, help="where overlay IRs are written")
    ap.add_argument("--selector", default="auto",
                    choices=["auto", "by-theme", "by-module", "none"])
    ap.add_argument("--edge-threshold", type=int, default=DEFAULT_EDGE_THRESHOLD)
    ap.add_argument("--fanout-threshold", type=int, default=DEFAULT_FANOUT_THRESHOLD)
    args = ap.parse_args()

    try:
        ir = json.loads(Path(args.ir).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"decompose: cannot read IR: {exc}")
    if "edges" not in ir or "nodes" not in ir:
        sys.exit("decompose: IR missing nodes/edges")

    selector, reason, overlays = decompose(
        ir, args.selector, args.edge_threshold, args.fanout_threshold)

    primary_id = ir.get("view", {}).get("id", Path(args.ir).stem)
    print(f"primary\t{primary_id}\tselector={selector}\ttrigger={reason}")

    if not overlays:
        print(f"decompose: no overlays for {primary_id} ({reason}).")
        return

    # Parity must hold before anything is written — fail loud otherwise.
    missing, extra, conflicts = parity(ir, [ov for _, ov in overlays])
    if missing or extra or conflicts:
        sys.exit(f"decompose: PARITY BROKEN missing={missing} extra={extra} "
                 f"ref_conflicts={conflicts}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for overlay_id, overlay_ir in overlays:
        path = out_dir / f"{overlay_id}.json"
        path.write_text(json.dumps(overlay_ir, indent=2), encoding="utf-8")
        print(f"overlay\t{overlay_id}\t{len(overlay_ir['edges'])} edges\t-> {path}")


if __name__ == "__main__":
    main()
