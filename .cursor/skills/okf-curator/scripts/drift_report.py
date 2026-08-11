#!/usr/bin/env python3
"""Report authored docs that may be stale relative to recent code changes.

Given a git ref (default `HEAD~3`), list the code/pipeline files changed since
that ref, then scan the OKF knowledge plane (the binding's `knowledge_globs`)
for Concepts that *mention* those changed paths. Those are the documents most
likely to have drifted and worth a human read.

This is a **report, not an auto-edit** — it cannot know whether a doc is actually
stale, only that it talks about something that just changed. Treat the output as a
worklist for routine (1) "document the feature" / routine (4) "keep it extractable".

Workspace inputs come from the OKF binding: `knowledge_globs` (where authored
knowledge lives), `[drift].code_prefixes` (which changed paths count as code),
`[drift].exclude_segments` (evidence noise filter), and `lint_gate` (the
follow-up hint). Resolution: `--binding PATH` → `.okf/binding.toml` → the home
repo's committed reference (see `_binding.py`).

Usage:
    python drift_report.py                 # since HEAD~3
    python drift_report.py --since v1.2.0
    python drift_report.py --since main --paths <subsystem-a>/ <subsystem-b>/
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _binding import (  # noqa: E402
    BindingIncompleteError,
    BindingNotFoundError,
    BindingParseError,
    require_relative_paths,
    require_str_list,
    resolve_binding,
)

# Configured from the binding in main() — where authored knowledge lives
# (evidence trees excluded), which changed paths count as *code*, and the
# workspace's lint-gate hint. See binding.schema.md.
KNOWLEDGE_GLOBS: tuple[str, ...] = ()
EXCLUDE_SEGMENTS: tuple[str, ...] = ()
CODE_PREFIXES: tuple[str, ...] = ()
LINT_GATE = "the OKF lint gate"


def _changed_files(since: str, restrict: list[str]) -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--name-only", f"{since}...HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    files = []
    for f in out:
        if restrict and not any(f.startswith(p) for p in restrict):
            continue
        if not restrict and not any(f.startswith(p) for p in CODE_PREFIXES):
            continue
        files.append(f)
    return files


def _is_knowledge(path: Path) -> bool:
    s = "/" + path.as_posix()
    if any(seg in s for seg in EXCLUDE_SEGMENTS):
        return False
    return path.name not in ("index.md", "log.md")


# A basename is too generic to match on its own (README.md in 40 dirs is noise).
_GENERIC_BASENAMES = {
    "README.md",
    "index.md",
    "log.md",
    "__init__.py",
    "config.json",
    "package.json",
    "conftest.py",
    "server.py",
    "main.py",
    "utils.py",
}

# Identifier definitions worth correlating to docs by NAME (a doc that describes
# the architecture but never names a brand-new public symbol is a drift candidate
# even if it doesn't reference the changed file path).
_SYMBOL_DEF = re.compile(
    r"^\s*(?:export\s+)?(?:async\s+)?(?:class|def|interface|type|enum)\s+([A-Z][A-Za-z0-9_]+)",
    re.MULTILINE,
)


def _added_symbols(since: str, changed: list[str]) -> set[str]:
    """Public-looking symbols ADDED to changed code in the diff window."""
    try:
        diff = subprocess.run(
            ["git", "diff", f"{since}...HEAD", "--", *changed],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return set()
    syms: set[str] = set()
    for line in diff.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            for m in _SYMBOL_DEF.finditer(line[1:]):
                syms.add(m.group(1))
    return syms


def _path_anchored(changed_path: str, text: str) -> bool:
    """True if the doc references the full path, or its basename in a non-generic,
    path-like context (preceded by `/` or a word boundary that isn't bare prose)."""
    if changed_path in text:
        return True
    name = Path(changed_path).name
    if name in _GENERIC_BASENAMES:
        return False  # too generic to count on its own
    # require the basename to appear as part of a path or in code-ish context
    return bool(
        re.search(rf"[\w./-]+/{re.escape(name)}\b", text)
        or re.search(rf"[`'\"]{re.escape(name)}[`'\"]", text)
    )


def main() -> int:
    global KNOWLEDGE_GLOBS, EXCLUDE_SEGMENTS, CODE_PREFIXES, LINT_GATE
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="HEAD~3")
    ap.add_argument(
        "--paths", nargs="*", default=[], help="restrict changed-code prefixes"
    )
    ap.add_argument(
        "--symbols",
        action="store_true",
        help="also flag docs missing brand-new public symbols (deeper, slower)",
    )
    ap.add_argument(
        "--binding", help="path to the OKF binding TOML (else .okf/ discovery)"
    )
    args = ap.parse_args()

    try:
        binding_path, b = resolve_binding(args.binding, Path.cwd())
        # Required: without these the scan silently matches nothing and the
        # report would assert "no code changed" / "no docs reference it" — a
        # conclusion about the workspace drawn from missing config (AP-6).
        # `--paths` supplies the code scope directly, so it substitutes for
        # code_prefixes in that mode.
        # knowledge_globs reaches files, so it is containment-checked;
        # code_prefixes is only ever a startswith() test, so shape is enough.
        KNOWLEDGE_GLOBS = tuple(
            require_relative_paths(b, "binding", "knowledge_globs", binding_path)
        )
        CODE_PREFIXES = (
            ()
            if args.paths
            else tuple(require_str_list(b, "drift", "code_prefixes", binding_path))
        )
    except (BindingNotFoundError, BindingParseError, BindingIncompleteError) as exc:
        print(f"drift_report: {exc}", file=sys.stderr)
        return 2
    core, drift = b.get("binding", {}), b.get("drift", {})
    EXCLUDE_SEGMENTS = tuple(drift.get("exclude_segments", ()))
    LINT_GATE = core.get("lint_gate", LINT_GATE)

    changed = _changed_files(args.since, args.paths)
    docs_only = _docs_only_window(args.since)

    print(f"# Drift report — code changed since {args.since}\n")
    if docs_only:
        print(
            "> NOTE: the commits in this window are **docs-only** (frontmatter/links). "
            "Widen the window (e.g. `--since HEAD~7` or a feature-branch base) to reach "
            "the real code changes, or the report below will be empty/misleading.\n"
        )
    if not changed:
        print(
            f"No code/pipeline changes since {args.since} (matched by prefix). "
            "Try a wider --since or different --paths."
        )
        return 0

    docs = [p for g in KNOWLEDGE_GLOBS for p in Path(".").glob(g) if _is_knowledge(p)]
    print(f"{len(changed)} changed code/pipeline file(s):")
    for c in changed:
        print(f"  - {c}")
    print()

    added = _added_symbols(args.since, changed) if args.symbols else set()
    if args.symbols:
        print(
            f"New public symbols added in window ({len(added)}): "
            f"{', '.join(sorted(added)) or '(none)'}\n"
        )

    # hit = (doc, list of (kind, evidence))
    hits: dict[str, list[tuple[str, str]]] = {}
    for doc in docs:
        try:
            text = doc.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        why: list[tuple[str, str]] = []
        for c in changed:
            if _path_anchored(c, text):
                why.append(("path", c))
        if args.symbols and added:
            # an architecture/reference doc that names the changed area but is
            # MISSING a brand-new symbol is a likely-stale candidate
            named_area = any(_path_anchored(c, text) for c in changed)
            missing = sorted(s for s in added if s not in text)
            if named_area and missing:
                why.append(("symbol-absent", ", ".join(missing[:6])))
        if why:
            hits[doc.as_posix()] = why

    if not hits:
        print(
            "No authored docs reference the changed paths. "
            "Either the change needs a NEW recipe, or it's purely internal."
        )
        return 0

    print(
        f"## {len(hits)} doc(s) correlate with changed code — review for staleness:\n"
    )
    print(
        "Match types: **path** = references a changed file path; "
        "**symbol-absent** = describes the changed area but is missing a brand-new symbol.\n"
    )
    for doc, why in sorted(hits.items()):
        print(f"- **{doc}**")
        for kind, ev in why:
            print(f"    ↳ [{kind}] `{ev}`")
    print(
        "\nThis correlates mentions, it does not prove staleness — read each. "
        "Update prose/Status where stale, or write a new recipe for net-new behaviour. "
        f"Then run `{LINT_GATE}`."
    )
    return 0


def _docs_only_window(since: str) -> bool:
    """True if every file changed in the window is under the knowledge roots."""
    prefixes = tuple(p for p in (g.split("*", 1)[0] for g in KNOWLEDGE_GLOBS) if p)
    if not prefixes:
        return False
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", f"{since}...HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
    except subprocess.CalledProcessError:
        return False
    return bool(out) and all(f.startswith(prefixes) for f in out)


if __name__ == "__main__":
    raise SystemExit(main())
