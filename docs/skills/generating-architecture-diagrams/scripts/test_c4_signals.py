#!/usr/bin/env python3
"""Negative + positive tests for the C4-Book signals (iteration 3).

Each new linter check must FAIL when its rule is violated and PASS when clean —
otherwise the check is decorative. This exercises the six signals from
docs/research/c4-book-signal-triage.md at the function level (no render needed),
plus a couple of false-positive guards that motivated the final scoping.

Run:  python3 scripts/test_c4_signals.py   (exit 0 = all asserts held)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint_diagram as L
import ir_to_d2 as T

PASS = 0
FAILED = []


def check(name, cond):
    global PASS
    if cond:
        PASS += 1
    else:
        FAILED.append(name)


def fails_for(prefix, **ir):
    """Run the relevant per-view checks over an IR dict and return the failures
    whose message starts with `prefix`."""
    ir.setdefault("view", {"id": "t", "level": "container", "title": "T"})
    ir.setdefault("nodes", [])
    ir.setdefault("edges", [])
    ir.setdefault("forbidden_facts", [])
    detail = T.write_detail_tables(ir)
    detail_joined = L.normalize(detail)
    svg_joined = L.normalize(" ".join(
        [n.get("label", "") for n in ir["nodes"]]
        + [q for n in ir["nodes"] for q in n.get("qualifiers", [])]
        + [d for n in ir["nodes"] for d in (n.get("detail", []) if isinstance(n.get("detail"), list) else [])]
    ))
    f = []
    L.check_deployment_nouns(ir, svg_joined, f)
    L.check_edge_label_verbs(ir, f)
    L.check_technology_present(ir, f)
    L.check_key_present(ir, detail_joined, f)
    return [x for x in f if x.startswith(prefix)]


# --- #6 deployment nouns -----------------------------------------------------
check("deploy: catches kubernetes on container view",
      fails_for("deployment-noun",
                nodes=[{"id": "A", "kind": "container", "label": "App",
                        "technology": "Java", "qualifiers": ["runs on Kubernetes pods"]}]))
check("deploy: exempt on a deployment view",
      not fails_for("deployment-noun",
                    view={"id": "d", "level": "deployment", "title": "D"},
                    nodes=[{"id": "A", "kind": "container", "label": "App",
                            "technology": "Java", "qualifiers": ["runs on Kubernetes pods"]}]))
check("deploy: 'Cluster A' logical grouping does NOT fire (false-positive guard)",
      not fails_for("deployment-noun",
                    nodes=[{"id": "A", "kind": "component", "label": "Coordinate",
                            "qualifiers": ["Cluster A"]}]))
check("deploy: region code fires",
      fails_for("deployment-noun",
                nodes=[{"id": "A", "kind": "container", "label": "App",
                        "technology": "Java", "qualifiers": ["hosted in us-east-1"]}]))

# --- #4 vague edge verbs -----------------------------------------------------
check("edge-verb: bare 'uses' fires",
      fails_for("edge-verb",
                nodes=[{"id": "A", "kind": "container", "label": "A", "technology": "x"},
                       {"id": "B", "kind": "container", "label": "B", "technology": "y"}],
                edges=[{"from": "A", "to": "B", "kind": "sync", "label": "uses"}]))
check("edge-verb: specific phrase containing 'uses' passes",
      not fails_for("edge-verb",
                    nodes=[{"id": "A", "kind": "container", "label": "A", "technology": "x"},
                           {"id": "B", "kind": "container", "label": "B", "technology": "y"}],
                    edges=[{"from": "A", "to": "B", "kind": "sync",
                            "label": "uses OAuth to authenticate with"}]))
check("edge-verb: numbered-ref edge is exempt (verb lives in the claim)",
      not fails_for("edge-verb",
                    nodes=[{"id": "A", "kind": "container", "label": "A", "technology": "x"},
                           {"id": "B", "kind": "container", "label": "B", "technology": "y"}],
                    edges=[{"from": "A", "to": "B", "kind": "sync", "ref": 1,
                            "label": "uses", "detail": "makes API requests to B over HTTP"}]))

# --- #3 technology present ---------------------------------------------------
check("tech: container without technology fires",
      fails_for("technology",
                nodes=[{"id": "A", "kind": "container", "label": "App"}]))
check("tech: container with technology passes",
      not fails_for("technology",
                    nodes=[{"id": "A", "kind": "container", "label": "App", "technology": "Java"}]))
check("tech: TECH: UNKNOWN honesty tag passes",
      not fails_for("technology",
                    nodes=[{"id": "A", "kind": "container", "label": "App",
                            "qualifiers": ["TECH: UNKNOWN"]}]))
check("tech: a COMPONENT without technology does NOT fire (scoped to containers)",
      not fails_for("technology",
                    nodes=[{"id": "A", "kind": "component", "label": "Logic"}]))

# --- #1 key present ----------------------------------------------------------
# The transformer auto-generates the key, so a pipeline-rendered view always has
# one. The check exists to catch a STRIPPED/hand-authored detail artifact whose
# key was removed — simulate that by passing a detail string with no Key section.
def _key_fails(ir, detail_joined):
    ir.setdefault("view", {"id": "t", "level": "container"})
    ir.setdefault("nodes", []); ir.setdefault("edges", [])
    f = []
    L.check_key_present(ir, detail_joined, f)
    return [x for x in f if x.startswith("key")]

check("key: multi-shape view whose detail LACKS a key fires",
      _key_fails({"nodes": [{"id": "A", "kind": "container", "label": "A"},
                            {"id": "D", "kind": "datastore", "label": "DB"}]},
                 L.normalize("a detail table with node rows but no such section")))
check("key: multi-shape view WHOSE detail HAS the generated key passes",
      not fails_for("key",
                    nodes=[{"id": "A", "kind": "container", "label": "A", "technology": "x"},
                           {"id": "D", "kind": "datastore", "label": "DB"}]))
check("key: trivial one-shape all-sync view is exempt",
      not fails_for("key",
                    nodes=[{"id": "A", "kind": "container", "label": "A", "technology": "x"},
                           {"id": "B", "kind": "container", "label": "B", "technology": "y"}],
                    edges=[{"from": "A", "to": "B", "kind": "sync", "ref": 1,
                            "detail": "sends orders to"}]))
# The generated key is what makes a multi-shape view pass — prove write_key emits it.
_ir_multi = {"view": {"id": "t", "level": "container"},
             "nodes": [{"id": "A", "kind": "container", "label": "A", "technology": "x"},
                       {"id": "D", "kind": "datastore", "label": "DB"}],
             "edges": [], "forbidden_facts": []}
check("key: write_key emits a Key for a multi-shape view",
      any("## Key" in ln for ln in T.write_key(_ir_multi)))
check("key: write_key emits nothing for a trivial view",
      T.write_key({"nodes": [{"id": "A", "kind": "container", "label": "A"}],
                   "edges": []}) == [])

# --- #2 [Type] affix ---------------------------------------------------------
check("type: container gets [Container] affix",
      T.type_affix({"kind": "container", "label": "App", "technology": "Java"}) == "[Container] Java")
check("type: datastore gets NO affix",
      T.type_affix({"kind": "datastore", "label": "DB"}) is None)
check("type: author's own [bracket] suppresses the affix",
      T.type_affix({"kind": "container", "label": "App [legacy]"}) is None)
check("type: node_label leaves the verbatim title intact",
      T.node_label({"kind": "container", "label": "Web App", "technology": "React"}).split("\n")[0] == "Web App")

# --- #5 not-shown-for-brevity ------------------------------------------------
_omit = T.write_omitted({"view": {"omitted": [
    {"label": "Logging", "note": "all components write logs here (not shown for brevity)"}]}})
check("omit: omitted node surfaces a grounded note",
      any("Logging" in ln for ln in _omit) and any("Not shown for brevity" in ln for ln in _omit))
check("omit: no omissions => no section",
      T.write_omitted({"view": {}}) == [])


# --- report ------------------------------------------------------------------
print(f"{PASS} assertions held, {len(FAILED)} failed")
for name in FAILED:
    print(f"  FAILED: {name}")
sys.exit(1 if FAILED else 0)
