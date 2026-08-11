#!/usr/bin/env python3
"""Generate `index.md` + `log.md` for an OKF bundle from its Concepts' frontmatter.

`index.md` lists every non-reserved `*.md` (directly, or recursively with
--recurse-index) as `- [title](relpath) — description`, read from each file's
frontmatter so the catalog never drifts from the files. `log.md` is seeded with one
dated entry; re-running regenerates `index.md` and re-seeds `log.md` (move existing
log lines you want to keep, or pass --append-log to keep the prior log body).

The conventions-doc link in each catalog is auto-computed relative to the bundle
dir from the binding's `conventions_doc` (resolution: `--binding PATH` →
`.okf/binding.toml` → the home repo's committed reference — see `_binding.py`).
`--depth-to-root` survives only as a legacy override; a wrong depth was the #1
source of a broken convention link in the catalog.

Usage:
    python make_bundle.py <recipes-home>/<topic> --title "<Topic> recipes"
    python make_bundle.py <bundle-dir> --title "<Title>" --note "Added Recipe N."
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _binding import (  # noqa: E402
    BindingNotFoundError,
    BindingParseError,
    resolve_binding,
)

RESERVED = {"index.md", "log.md", "README.md"}


def _fm(path: Path) -> dict[str, str]:
    t = path.read_text(encoding="utf-8")
    if not t.startswith("---\n"):
        return {}
    try:
        block = t[4 : t.index("\n---\n", 3)]
    except ValueError:
        return {}
    d: dict[str, str] = {}
    for line in block.splitlines():
        m = re.match(r"(\w+):\s*(.*)", line)
        if m:
            k, v = m.group(1), m.group(2).strip()
            if v.startswith("'") and v.endswith("'"):
                v = v[1:-1].replace("''", "'")
            d[k] = v
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--title", required=True)
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--recurse-index", action="store_true")
    ap.add_argument(
        "--depth-to-root",
        type=int,
        default=None,
        help="(legacy) number of ../ to reach the conventions doc's parent. "
        "Prefer --conventions-path or let the script compute the link.",
    )
    ap.add_argument(
        "--conventions-path",
        default=None,
        help="path to the convention doc, relative to the workspace root "
        "(default: the binding's conventions_doc)",
    )
    ap.add_argument(
        "--binding", help="path to the OKF binding TOML (else .okf/ discovery)"
    )
    ap.add_argument(
        "--note",
        default="Declared as an OKF bundle.",
        help="the log.md seed entry text",
    )
    args = ap.parse_args()

    # The binding supplies conventions_doc + the lint-gate hint. An explicit
    # --conventions-path works without a binding (the hint degrades to generic).
    lint_gate = "the OKF lint gate"
    conventions_path = args.conventions_path
    try:
        _, b = resolve_binding(args.binding, Path.cwd())
    except (BindingNotFoundError, BindingParseError) as exc:
        if conventions_path is None:
            print(f"make_bundle: {exc}", file=sys.stderr)
            return 2
        b = {}
    core = b.get("binding", {})
    conventions_path = conventions_path or core.get("conventions_doc")
    lint_gate = core.get("lint_gate", lint_gate)
    if not conventions_path:
        print(
            "make_bundle: no conventions doc — pass --conventions-path or set "
            "conventions_doc in the binding (see FIRST_RUN.md)",
            file=sys.stderr,
        )
        return 2

    base = Path(args.target)
    conv_name = Path(conventions_path).name
    # Link to the convention doc, computed relative to THIS bundle dir so it is
    # correct no matter how deep the bundle is (incl. a root-level bundle, where
    # a naive fixed depth gets the prefix wrong). --depth-to-root is honoured
    # only as a legacy override.
    if args.depth_to_root is not None:
        conv_link = "../" * args.depth_to_root + conv_name
    else:
        import os as _os

        conv_link = _os.path.relpath(conventions_path, base.as_posix())
    files = base.rglob("*.md") if args.recurse_index else base.glob("*.md")
    entries = []
    for f in sorted(files):
        if f.name in RESERVED:
            continue
        d = _fm(f)
        rel = f.relative_to(base).as_posix()
        entries.append(
            f"- [{d.get('title', f.stem)}]({rel}) — {d.get('description', '')}"
        )

    idx = (
        f"# {args.title} — bundle index\n\n"
        f"OKF bundle. Each entry is a typed Concept. See the convention in "
        f"[{conv_name}]({conv_link}).\n\n" + "\n".join(entries) + "\n"
    )
    (base / "index.md").write_text(idx, encoding="utf-8")

    log = (
        "---\n"
        "type: log\n"
        f"title: '{args.title} — bundle log'\n"
        "---\n\n"
        f"# {args.title} — bundle log\n\n"
        "Chronological history, newest first (ISO-8601).\n\n"
        f"- {args.date} — {args.note} Convention in "
        f"[{conv_name}]({conv_link}); linted by `{lint_gate}`.\n"
    )
    (base / "log.md").write_text(log, encoding="utf-8")
    print(f"{args.target}: index.md ({len(entries)} entries) + log.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
