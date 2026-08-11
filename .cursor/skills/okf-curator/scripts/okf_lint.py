#!/usr/bin/env python3
"""OKF (Open Knowledge Format) bundle linter — the bundled portable engine.

Checks that a workspace's declared knowledge bundles conform to its OKF
convention (the binding's ``conventions_doc``):

  * each bundle has an ``index.md`` and a ``log.md`` (FAIL if missing);
  * every authored ``.md`` carries parseable YAML frontmatter with a non-empty
    ``type`` field (WARN — non-blocking, matches OKF's permissive consumer rule
    so a workspace can backfill incrementally);
  * every relative markdown link and ``[[wiki-link]]`` resolves (WARN on a
    broken link — OKF treats a broken link as not-yet-written knowledge, so it
    is surfaced for rot-visibility but does not fail the run).

All workspace-specific inputs come from the OKF binding (ADR-0039): the
``[lint]`` table supplies ``declared_bundles``, ``evidence_segments``,
``evidence_suffixes``, ``run_dir_pattern``, and ``reserved``. Resolution order
(see ``_binding.py``): ``--binding PATH`` → ``.okf/binding.toml`` walking up
from cwd → the home repo's committed reference. **No binding → exit 2 with a
FIRST_RUN pointer — never lint a guessed bundle set.** A binding that resolves
but declares no ``declared_bundles`` key exits 2 for the same reason: linting
zero bundles and printing success would assert a clean tree the binding never
declared.

Exit codes: 0 = structurally sound (warnings allowed); 1 = a hard structural
failure (a declared bundle missing, or missing ``index.md``/``log.md``);
2 = binding not found / malformed / missing a required key.

Pure stdlib, no third-party dependency. Run from anywhere::

    python okf_lint.py [--binding PATH] [--root WORKSPACE_ROOT]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _binding import (  # noqa: E402
    BindingIncompleteError,
    BindingNotFoundError,
    BindingParseError,
    require_relative_paths,
    resolve_binding,
)

# Workspace-neutral defaults for [lint] keys a binding may omit. declared_bundles
# is REQUIRED: an absent key (or a typo'd one) exits 2 rather than lint zero
# bundles and report success. An explicitly empty list is legal, and marked.
_DEFAULT_RESERVED = ("index.md", "log.md", "README.md")
_DEFAULT_EVIDENCE_SEGMENTS = ("outputs",)
_DEFAULT_EVIDENCE_SUFFIXES = ("-workspace",)
_DEFAULT_RUN_DIR = r"^run-\d+$"

# Configured from the binding in main() before the walk (kept as module globals
# so the check functions below stay line-identical to the pre-ADR-0039 engine).
BUNDLES: tuple[str, ...] = ()
RESERVED: set[str] = set(_DEFAULT_RESERVED)
EVIDENCE_SEGMENTS: tuple[str, ...] = _DEFAULT_EVIDENCE_SEGMENTS
EVIDENCE_SUFFIXES: tuple[str, ...] = _DEFAULT_EVIDENCE_SUFFIXES
_RUN_DIR = re.compile(_DEFAULT_RUN_DIR)

# Markdown inline link: [text](target).  We ignore anchors and external URLs.
_MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
# Wiki link: [[name]] (optionally [[name|alias]]).
_WIKI_LINK = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
# Fenced code block (``` or ~~~) and inline code span (`...`). Stripped before
# link scanning so shell/code syntax like `if [[ -n "$X" ]]` isn't mistaken for
# a wiki-link, and code containing [text](paren) isn't mistaken for a link.
_FENCE = re.compile(r"^[ \t]*(```|~~~).*?^[ \t]*\1[ \t]*$", re.DOTALL | re.MULTILINE)
_INLINE_CODE = re.compile(r"`[^`\n]*`")


def _configure(binding: dict, binding_path: Path) -> None:
    """Load the [lint] table into the module globals the walk reads.

    ``declared_bundles`` is required (``require`` raises naming the key and the
    file); the other four have workspace-neutral defaults documented in
    binding.schema.md as "default fine".
    """
    global BUNDLES, RESERVED, EVIDENCE_SEGMENTS, EVIDENCE_SUFFIXES, _RUN_DIR
    BUNDLES = tuple(
        require_relative_paths(binding, "lint", "declared_bundles", binding_path)
    )
    lint = binding.get("lint", {})
    RESERVED = set(lint.get("reserved", _DEFAULT_RESERVED))
    EVIDENCE_SEGMENTS = tuple(lint.get("evidence_segments", _DEFAULT_EVIDENCE_SEGMENTS))
    EVIDENCE_SUFFIXES = tuple(lint.get("evidence_suffixes", _DEFAULT_EVIDENCE_SUFFIXES))
    _RUN_DIR = re.compile(lint.get("run_dir_pattern", _DEFAULT_RUN_DIR))


def _strip_code(text: str) -> str:
    """Remove fenced code blocks and inline code spans (link scanning only)."""
    text = _FENCE.sub("", text)
    return _INLINE_CODE.sub("", text)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontmatter_block(text: str) -> str | None:
    """Return the raw YAML frontmatter block, or None if absent.

    We only need to detect presence of a non-empty ``type:`` key, so a light
    line scan beats pulling in a YAML parser.
    """
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return None


def _has_nonempty_type(frontmatter: str) -> bool:
    for line in frontmatter.splitlines():
        stripped = line.strip()
        if stripped.startswith("type:"):
            value = stripped[len("type:") :].strip().strip("'\"")
            return bool(value)
    return False


def _is_external(target: str) -> bool:
    target = target.strip()
    return (
        target.startswith(("http://", "https://", "mailto:", "#", "data:"))
        or target.startswith("<")  # angle-bracket autolinks / placeholders
    )


def _link_resolves(source: Path, target: str, root: Path) -> bool | None:
    """True/False if a markdown link target exists; None to skip (external/anchor).

    A link counts as resolved if it exists EITHER relative to the source file's
    directory (normal markdown) OR relative to the workspace root. Docs frequently
    link source files as ``services/x.py`` (root-relative), which is a valid,
    working reference even though it doesn't resolve from the doc's own folder.
    """
    target = target.split("#", 1)[0].strip()  # drop anchor
    if not target or _is_external(target):
        return None
    if target.startswith("/"):
        return (root / target.lstrip("/")).exists()
    candidates = (
        (source.parent / target),
        (root / target),
    )
    return any(c.exists() for c in candidates)


def _is_evidence(md: Path, bundle_dir: Path) -> bool:
    """True if ``md`` lives in a generated eval-evidence/run-artifact tree."""
    parts = md.relative_to(bundle_dir).parts
    for part in parts:
        if part in EVIDENCE_SEGMENTS or _RUN_DIR.match(part):
            return True
        if any(part.endswith(suffix) for suffix in EVIDENCE_SUFFIXES):
            return True
    return False


def _wiki_name_resolves(name: str, bundle_dir: Path) -> bool:
    """A [[name]] link resolves if ``<name>.md`` exists somewhere in the bundle."""
    name = name.strip()
    if not name:
        return False
    return any(p.stem == name for p in bundle_dir.rglob("*.md"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--binding", help="path to the OKF binding TOML (else .okf/ discovery)"
    )
    parser.add_argument(
        "--root",
        default=".",
        help="workspace root the binding's paths are relative to (default: cwd)",
    )
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        binding_path, binding = resolve_binding(args.binding, root)
        _configure(binding, binding_path)
    except (BindingNotFoundError, BindingParseError, BindingIncompleteError) as exc:
        print(f"okf_lint: {exc}", file=sys.stderr)
        return 2

    failures: list[str] = []
    warnings: list[str] = []

    for bundle in BUNDLES:
        bundle_dir = root / bundle
        if not bundle_dir.is_dir():
            failures.append(f"{bundle}: declared bundle directory does not exist")
            continue

        for reserved in ("index.md", "log.md"):
            if not (bundle_dir / reserved).is_file():
                failures.append(f"{bundle}: missing required {reserved}")

        # Nested declared bundles own their own files — don't double-lint them
        # when walking a parent bundle (a parent bundle vs a deeper declared bundle inside it).
        nested = tuple(
            root / b
            for b in BUNDLES
            if b != bundle and (root / b).is_relative_to(bundle_dir)
        )

        for md in sorted(bundle_dir.rglob("*.md")):
            if any(md.is_relative_to(n) for n in nested):
                continue  # owned by a deeper declared bundle
            if _is_evidence(md, bundle_dir):
                continue  # generated artifact, not an authored Concept
            rel = md.relative_to(root)
            text = _read(md)

            # type-frontmatter check (WARN only)
            if md.name not in RESERVED:
                fm = _frontmatter_block(text)
                if fm is None or not _has_nonempty_type(fm):
                    warnings.append(f"{rel}: missing non-empty `type` frontmatter")

            # Strip code so shell/code syntax isn't mistaken for a link.
            prose = _strip_code(text)

            # markdown link resolution (WARN on broken — not-yet-written knowledge)
            for target in _MD_LINK.findall(prose):
                ok = _link_resolves(md, target, root)
                if ok is False:
                    warnings.append(f"{rel}: broken link -> {target}")

            # wiki-link resolution (WARN on broken)
            for name in _WIKI_LINK.findall(prose):
                if not _wiki_name_resolves(name, bundle_dir):
                    warnings.append(f"{rel}: broken wiki-link -> [[{name}]]")

    for w in warnings:
        print(f"WARN  {w}")
    for f in failures:
        print(f"FAIL  {f}")

    # An empty declaration is legal (a workspace mid-adoption) but must never
    # read as a healthy run — say it, don't let `0 bundle(s)` imply "all clean".
    if not BUNDLES:
        print(
            f"\nokf_lint: no bundles declared in {binding_path} — nothing to lint. "
            "Add directories to [lint].declared_bundles."
        )

    print(
        f"\nokf_lint: {len(BUNDLES)} bundle(s), "
        f"{len(warnings)} warning(s), {len(failures)} failure(s)"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
