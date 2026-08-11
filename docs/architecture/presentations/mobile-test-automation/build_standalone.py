#!/usr/bin/env python3
"""Build the self-contained spine-design-pack-standalone.md.

Takes spine-design-pack.md and produces a single shareable file:
- the four @2x PNGs embedded as base64 data URIs (no sibling files needed),
- the P1-P3 view.md node/edge tables inlined as appendices A1-A3,
- repo-relative links rewritten as plain repo paths (they cannot resolve
  once the file leaves the repo).

Re-run after any re-render of the diagrams:
    python3 build_standalone.py
"""

import base64
import re
from pathlib import Path

HERE = Path(__file__).parent
DECK = HERE / "spine-design-pack.md"
OUT = HERE / "spine-design-pack-standalone.md"

VIEWS = [
    ("p1-spine-context", "A1", "P1 node and edge details"),
    ("p2-module-map", "A2", "P2 node and edge details"),
    ("p3-replay-flow", "A3", "P3 node and edge details"),
]


def data_uri(png: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(png.read_bytes()).decode()


def appendix_body(view_id: str) -> str:
    """view.md minus its H1 and its image line, headings demoted two levels."""
    lines = (HERE / f"{view_id}.view.md").read_text().splitlines()
    out = []
    for ln in lines:
        if ln.startswith("# ") or re.match(r"^!\[.*\]\(.*\)$", ln):
            continue
        if ln.startswith("## "):
            ln = "##" + ln
        out.append(ln)
    return "\n".join(out).strip()


def slug(appendix_id: str, title: str) -> str:
    return re.sub(r"[^a-z0-9 -]", "", f"appendix {appendix_id} {title}".lower()).replace(" ", "-")


text = DECK.read_text()

# 1. Embed the four rendered PNGs as data URIs.
for png in sorted(HERE.glob("p*@2x.png")):
    text = text.replace(f"]({png.name})", f"]({data_uri(png)})")

# 2. Point the per-view detail links at the inlined appendices.
for view_id, appendix_id, title in VIEWS:
    text = re.sub(
        rf"\[{view_id}\.view\.md\]\({view_id}\.view\.md\)",
        f"[Appendix {appendix_id}](#{slug(appendix_id, title)})",
        text,
    )

# 3. Repo-relative links can't resolve outside the repo: flatten to repo paths.
def flatten_link(m: re.Match) -> str:
    label, target = m.group(1), m.group(2)
    parts = target.split("/")
    ups = len([p for p in parts if p == ".."])
    # Deck lives at docs/architecture/presentations/mobile-test-automation/.
    base = ["docs", "architecture", "presentations", "mobile-test-automation"]
    repo_path = "/".join(base[: len(base) - ups] + parts[ups:])
    return f"{label} (`{repo_path}`)"

text = re.sub(r"\[([^\]]+)\]\((\.\./[^)]+)\)", flatten_link, text)

# 4. Frontmatter + provenance note for the standalone artifact.
text = re.sub(
    r"\A---\n.*?\n---\n",
    """---
type: architecture
title: "High-level design pack — Weeks 0–3 Shared Spine (standalone)"
description: >-
  GENERATED single-file edition of spine-design-pack.md — diagrams embedded
  as data URIs, view tables inlined as appendices, repo links flattened to
  plain paths. Do not edit by hand; re-run build_standalone.py after any
  change to the deck or a re-render of the diagrams.
tags: [mobile-test-automation, presentation, design-pack, spine, standalone]
---
""",
    text,
    count=1,
    flags=re.DOTALL,
)

# 5. Append the three view appendices.
appendices = ["", "---", "", "## Appendices — diagram node and edge details", ""]
appendices.append(
    "*Inlined from the generated `*.view.md` files so this file is "
    "self-contained; the numbered rows match the `[n]` markers on each canvas.*"
)
for view_id, appendix_id, title in VIEWS:
    appendices += ["", f"### Appendix {appendix_id}: {title}", "", appendix_body(view_id)]
text = text.rstrip() + "\n" + "\n".join(appendices) + "\n"

OUT.write_text(text)
size_kb = OUT.stat().st_size // 1024
print(f"wrote {OUT.name} ({size_kb} KB)")
