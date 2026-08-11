#!/usr/bin/env python3
"""Relocate docs and rewrite EVERY reference to them, safely.

Moving a doc is the one OKF operation that can silently break things: links that
point AT it, and the moved file's OWN outbound relative links, all shift. This
tool moves files and rewrites both directions, by RESOLVED TARGET (not blind
string replace), covering the three reference forms that bit in practice:
  1. markdown links            `[text](path)` / `[text](../path)`
  2. agent context @-mentions  (the binding's `context_mention_prefix`,
                                LOAD-BEARING in agent context files)
  3. bare path mentions        `<docs-home>/NAME.md`

Anything more exotic (a path built by string concatenation in code, an aliased
parent-dir prefix, a link in a `.canvas` file) is NOT rewritten — grep for the
old path afterwards, per the skill's gotchas.

The docs home and mention prefix come from the OKF binding (`docs_home`,
`context_mention_prefix`; resolution: `--binding PATH` → `.okf/binding.toml` →
the home repo's committed reference — see `_binding.py`).

Always dry-run first (`--plan`). Untracked files fall back to a plain `mv` when
`git mv` fails. After applying, verify with `git status` rename count + a
repo-wide grep that no reference resolves to an OLD location.

Move spec: repeatable `--move OLD_RELPATH=NEW_RELPATH`, both relative to the
docs home.

Usage:
    python relocate.py --plan  --move OLD.md=newdir/OLD.md
    python relocate.py --apply --move OLD.md=newdir/OLD.md --move B.md=c/B.md
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _binding import (  # noqa: E402
    BindingNotFoundError,
    BindingParseError,
    resolve_binding,
)

SCAN_SUFFIXES = {".py", ".md", ".ts", ".tsx", ".json", ".toml", ".txt", ".yml", ".yaml"}
SKIP_DIRS = {"node_modules", ".venv", ".git", "__pycache__", ".next", "dist", "build"}

_MD_LINK = re.compile(r"(?<!\!)(\[[^\]]*\]\()([^)]+)(\))")

# Configured from the binding in main() (placeholders until then — the script
# hard-exits without a resolvable binding, so these are never used as-is).
DOCS = Path(".")
_DOCS_PREFIX = ""
_AT_MENTION: re.Pattern[str] | None = None
_BARE_DOCS = re.compile(r"$^")  # replaced in main()
LINT_GATE = "the OKF lint gate"


def _configure(binding: dict) -> None:
    global DOCS, _DOCS_PREFIX, _AT_MENTION, _BARE_DOCS, LINT_GATE
    core = binding.get("binding", {})
    docs_home = core.get("docs_home") or "."
    _DOCS_PREFIX = docs_home if docs_home.endswith("/") else docs_home + "/"
    DOCS = Path(_DOCS_PREFIX.rstrip("/"))
    mention = core.get("context_mention_prefix", "<none>")
    path_re = rf"({re.escape(_DOCS_PREFIX)}[A-Za-z0-9_./-]+\.md)"
    _AT_MENTION = re.compile("@" + path_re) if mention != "<none>" else None
    _BARE_DOCS = re.compile(rf"(?<![\w@.]){path_re}")
    LINT_GATE = core.get("lint_gate", LINT_GATE)


def _iter_text_files():
    for dirpath, dirnames, filenames in os.walk("."):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if Path(fn).suffix in SCAN_SUFFIXES:
                yield Path(dirpath) / fn


def _docs_rel(token: str) -> str | None:
    """Return the docs-home-relative path or None."""
    if token.startswith(_DOCS_PREFIX):
        return token[len(_DOCS_PREFIX) :]
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--plan", action="store_true", help="dry run (default)")
    g.add_argument("--apply", action="store_true")
    ap.add_argument(
        "--move",
        action="append",
        default=[],
        required=True,
        help="OLD=NEW, both relative to the docs home",
    )
    ap.add_argument(
        "--binding", help="path to the OKF binding TOML (else .okf/ discovery)"
    )
    args = ap.parse_args()

    try:
        _, b = resolve_binding(args.binding, Path.cwd())
    except (BindingNotFoundError, BindingParseError) as exc:
        print(f"relocate: {exc}", file=sys.stderr)
        return 2
    _configure(b)

    old2new = dict(m.split("=", 1) for m in args.move)
    apply = args.apply

    def resolves_to_moved(source: Path, target: str) -> str | None:
        raw = target.split("#", 1)[0].strip()
        if not raw or raw.startswith(("http://", "https://", "mailto:", "#", "<")):
            return None
        for base in (source.parent, Path(".")):
            try:
                rel = (base / raw).resolve().relative_to(DOCS.resolve()).as_posix()
            except (ValueError, OSError):
                continue
            if rel in old2new:
                return rel
        dr = _docs_rel(raw)
        return dr if dr in old2new else None

    # census
    refs: dict[str, set[str]] = {o: set() for o in old2new}
    mention_rxs = [rx for rx in (_AT_MENTION, _BARE_DOCS) if rx is not None]
    for f in _iter_text_files():
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for m in _MD_LINK.finditer(text):
            o = resolves_to_moved(f, m.group(2))
            if o:
                refs[o].add(str(f))
        for rx in mention_rxs:
            for m in rx.finditer(text):
                dr = _docs_rel(m.group(1))
                if dr in old2new:
                    refs[dr].add(str(f))

    print("== MOVE MAP ==")
    for o, n in old2new.items():
        print(
            f"  {_DOCS_PREFIX}{o:42} -> {_DOCS_PREFIX}{n}   "
            f"({len(refs[o])} referencing files)"
        )
    if not apply:
        print("\n(plan only; re-run with --apply)")
        return 0

    # move (git mv; plain mv fallback for untracked); idempotent
    for o, n in old2new.items():
        (DOCS / n).parent.mkdir(parents=True, exist_ok=True)
        src, dst = DOCS / o, DOCS / n
        if dst.exists() and not src.exists():
            continue
        if not src.exists():
            print(f"  WARN missing source: {_DOCS_PREFIX}{o}")
            continue
        r = subprocess.run(
            ["git", "mv", str(src), str(dst)], capture_output=True, text=True
        )
        if r.returncode != 0:
            src.rename(dst)
            print(f"  (untracked) mv {_DOCS_PREFIX}{o} -> {_DOCS_PREFIX}{n}")

    # rewrite inbound refs (everywhere) + outbound refs (in the moved files)
    def rewrite(path: Path) -> bool:
        text = path.read_text(encoding="utf-8")
        orig = text

        def md_sub(m):
            target = m.group(2)
            o = resolves_to_moved(path, target)
            if not o:
                return m.group(0)
            anchor = "#" + target.split("#", 1)[1] if "#" in target else ""
            new_target = os.path.relpath(DOCS / old2new[o], path.parent) + anchor
            return m.group(1) + new_target + m.group(3)

        def at_sub(m):
            dr = _docs_rel(m.group(1))
            return f"@{_DOCS_PREFIX}{old2new[dr]}" if dr in old2new else m.group(0)

        def bare_sub(m):
            dr = _docs_rel(m.group(1))
            if dr not in old2new:
                return m.group(0)
            return _DOCS_PREFIX + old2new[dr]

        text = _MD_LINK.sub(md_sub, text)
        if _AT_MENTION is not None:
            text = _AT_MENTION.sub(at_sub, text)
        text = _BARE_DOCS.sub(bare_sub, text)
        if text != orig:
            path.write_text(text, encoding="utf-8")
            return True
        return False

    # also fix the moved files' OWN outbound relative links (depth changed)
    for o, n in old2new.items():
        moved = DOCS / n
        if not moved.exists():
            continue
        text = moved.read_text(encoding="utf-8")
        old_parent = (DOCS / o).parent

        def out_sub(m):
            target = m.group(2)
            raw = target.split("#", 1)[0]
            anchor = target[len(raw) :]
            if not raw or raw.startswith(("http", "mailto:", "#", "/", "<")):
                return m.group(0)
            old_abs = (old_parent / raw).resolve()
            if not old_abs.exists():
                return m.group(0)
            new_rel = os.path.relpath(old_abs, moved.parent)
            return (
                m.group(1) + new_rel + anchor + m.group(3)
                if new_rel != raw
                else m.group(0)
            )

        new_text = _MD_LINK.sub(out_sub, text)
        if new_text != text:
            moved.write_text(new_text, encoding="utf-8")

    changed = sum(rewrite(f) for f in _iter_text_files())
    print(
        f"\nmoved={len(old2new)}; rewrote inbound references in {changed} files "
        "(outbound links in moved files fixed separately)"
    )
    print(
        "VERIFY: git status rename count, then grep that no ref resolves to an "
        f"OLD path, then `{LINT_GATE}`."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
