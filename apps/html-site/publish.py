#!/usr/bin/env python3
"""Copy the html-site allowlist into dist/ and check relative-link closure.

stdlib only (pathlib, shutil, tomllib, html.parser, argparse). Python >= 3.11.

Usage (from repo root):
  python3 apps/html-site/publish.py              # wipe dist/, copy, check
  python3 apps/html-site/publish.py --check DIR  # closure check only
  python3 apps/html-site/publish.py --selftest   # AC-3 fail + AC-4 pass + AC-7 + missing canonical

Local preview (FR-8):
  python3 apps/html-site/publish.py
  python3 -m http.server 8124 --bind 127.0.0.1 -d apps/html-site/dist
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

try:
    import tomllib
except ImportError:  # pragma: no cover — same floor as skill-sync; fail loud
    sys.stderr.write("publish.py: Python >= 3.11 required (tomllib)\n")
    sys.exit(1)


APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent.parent

_SKIP_PREFIXES = ("http:", "https:", "mailto:", "data:", "javascript:")


class ConfigError(Exception):
    """Usage/config (bad/missing manifest, missing canonical). Exit 1."""


class CheckError(Exception):
    """Closure or byte-identity failure. Exit 2."""


class _RefParser(HTMLParser):
    """Collect href/src attribute values. html.parser does not see URLs in JS."""

    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, val in attrs:
            if key in ("href", "src") and val is not None:
                self.refs.append(val)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def _ignored(url: str) -> bool:
    s = url.strip()
    if not s or s.startswith("#"):
        return True
    lower = s.lower()
    return any(lower.startswith(p) for p in _SKIP_PREFIXES)


def _load_manifest(manifest_path: Path) -> tuple[str, list[dict[str, str]]]:
    if not manifest_path.is_file():
        raise ConfigError(f"manifest not found: {manifest_path}")
    try:
        data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"manifest unparsable: {e}") from e
    catalog = data.get("catalog")
    if not isinstance(catalog, str) or not catalog:
        raise ConfigError("manifest: catalog must be a non-empty string")
    rows = data.get("document")
    if not isinstance(rows, list) or not rows:
        raise ConfigError("manifest: at least one [[document]] row required")
    documents: list[dict[str, str]] = []
    for row in rows:
        source, publish_as = row.get("source"), row.get("publish_as")
        if not isinstance(source, str) or not isinstance(publish_as, str):
            raise ConfigError(f"document row malformed: {row!r}")
        documents.append({"source": source, "publish_as": publish_as})
    return catalog, documents


def check_tree(tree: Path, err: io.TextIOBase | None = None) -> int:
    """FR-5 / AC-3 / AC-4: fail naming any relative href/src missing from the tree."""
    sink = err if err is not None else sys.stderr
    if not tree.is_dir():
        raise ConfigError(f"check dir not found: {tree}")
    root = tree.resolve()
    missing: list[str] = []
    html_files = sorted(p for p in root.rglob("*.html") if p.is_file())
    for html in html_files:
        parser = _RefParser()
        parser.feed(html.read_text(encoding="utf-8"))
        parser.close()
        for raw in parser.refs:
            if _ignored(raw):
                continue
            stripped = raw.split("#", 1)[0]
            if not stripped:
                continue
            target = (html.parent / stripped).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                # Path escaped the publish tree — named failure, not in-tree.
                missing.append(stripped)
                continue
            if not target.is_file():
                missing.append(stripped)
    if missing:
        for m in missing:
            sink.write(f"missing: {m}\n")
        return 2
    return 0


def publish(repo_root: Path, app_dir: Path, err: io.TextIOBase | None = None) -> int:
    """Wipe dist/, copy catalog + documents byte-for-byte, then closure-check."""
    sink = err if err is not None else sys.stderr
    catalog_name, documents = _load_manifest(app_dir / "manifest.toml")
    catalog_src = app_dir / catalog_name
    if not catalog_src.is_file():
        raise ConfigError(f"catalog not found: {catalog_src}")

    copies: list[tuple[Path, str]] = []
    for row in documents:
        src = repo_root / row["source"]
        if not src.is_file():
            raise ConfigError(f"canonical not found: {row['source']}")
        copies.append((src, row["publish_as"]))

    dist = app_dir / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)

    (dist / catalog_name).write_bytes(catalog_src.read_bytes())
    for src, publish_as in copies:
        dest = dist / publish_as
        dest.write_bytes(src.read_bytes())
        if dest.read_bytes() != src.read_bytes():
            sink.write(f"identity: {publish_as} is not byte-identical to {src}\n")
            return 2
    return check_tree(dist, err=sink)


def _capture(fn, *args) -> tuple[int, str]:
    buf = io.StringIO()
    try:
        code = fn(*args, err=buf)
        return int(code), buf.getvalue()
    except ConfigError as e:
        return 1, str(e)
    except CheckError as e:
        return 2, str(e)
    except NotImplementedError as e:
        return 99, f"NotImplementedError: {e}"


def cmd_selftest() -> int:
    """Three required sections (AC-3, AC-4, missing canonical) plus AC-7 copy identity."""
    problems: list[str] = []

    # AC-3: v3 HTML whose href names the atlas; atlas absent → exit 2 naming it.
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp)
        (tree / "ccar-p-prep-guide-v3.html").write_text(
            '<a href="claude-architect-m1-atlas.html">atlas</a>\n',
            encoding="utf-8",
        )
        code, err = _capture(check_tree, tree)
        if code != 2 or "claude-architect-m1-atlas.html" not in err:
            problems.append(
                "AC-3: expected exit 2 naming claude-architect-m1-atlas.html; "
                f"got exit {code}: {err.strip()!r}"
            )
        else:
            sys.stdout.write("AC-3: pass\n")

    # AC-4: v1 publish tree (catalog + v3 + atlas) → exit 0.
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp)
        (tree / "index.html").write_text(
            '<a href="ccar-p-prep-guide-v3.html">v3</a>'
            '<a href="claude-architect-m1-atlas.html">atlas</a>\n',
            encoding="utf-8",
        )
        (tree / "ccar-p-prep-guide-v3.html").write_text(
            '<a href="claude-architect-m1-atlas.html">atlas</a>\n',
            encoding="utf-8",
        )
        (tree / "claude-architect-m1-atlas.html").write_text(
            "<p>atlas leaf</p>\n",
            encoding="utf-8",
        )
        code, err = _capture(check_tree, tree)
        if code != 0:
            problems.append(f"AC-4: expected exit 0; got exit {code}: {err.strip()!r}")
        else:
            sys.stdout.write("AC-4: pass\n")

    # Missing canonical → exit 1.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        app = root / "apps" / "html-site"
        app.mkdir(parents=True)
        (app / "index.html").write_text("<html></html>\n", encoding="utf-8")
        (app / "manifest.toml").write_text(
            'catalog = "index.html"\n\n'
            "[[document]]\n"
            'source = "docs/does-not-exist.html"\n'
            'publish_as = "does-not-exist.html"\n',
            encoding="utf-8",
        )
        code, err = _capture(publish, root, app)
        if code != 1:
            problems.append(
                f"missing-canonical: expected exit 1; got exit {code}: {err.strip()!r}"
            )
        else:
            sys.stdout.write("missing-canonical: pass\n")

    # AC-7: published bytes equal the fixture canonical.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        app = root / "apps" / "html-site"
        docs = root / "docs"
        app.mkdir(parents=True)
        docs.mkdir()
        payload = b"<html>canonical-bytes</html>\n"
        (docs / "page.html").write_bytes(payload)
        (app / "index.html").write_bytes(b"<html>catalog</html>\n")
        (app / "manifest.toml").write_text(
            'catalog = "index.html"\n\n'
            "[[document]]\n"
            'source = "docs/page.html"\n'
            'publish_as = "page.html"\n',
            encoding="utf-8",
        )
        code, err = _capture(publish, root, app)
        dist_page = app / "dist" / "page.html"
        if code != 0:
            problems.append(f"AC-7: expected publish exit 0; got {code}: {err.strip()!r}")
        elif not dist_page.is_file() or dist_page.read_bytes() != payload:
            got = dist_page.read_bytes() if dist_page.is_file() else None
            problems.append(f"AC-7: published bytes != canonical; got {got!r}")
        else:
            sys.stdout.write("AC-7: pass\n")

    for problem in problems:
        sys.stderr.write(f"selftest FAIL: {problem}\n")
    if problems:
        sys.stdout.write(f"selftest: {len(problems)} failing section(s)\n")
        return 2
    sys.stdout.write("selftest: pass\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", metavar="DIR", help="closure check only (no copy)")
    group.add_argument("--selftest", action="store_true", help="temp fixtures; AC-3/AC-4/AC-7")
    args = parser.parse_args(argv)
    try:
        if args.selftest:
            return cmd_selftest()
        if args.check is not None:
            tree = Path(args.check)
            if not tree.is_dir():
                raise ConfigError(f"check dir not found: {tree}")
            return check_tree(tree)
        return publish(REPO_ROOT, APP_DIR)
    except ConfigError as e:
        sys.stderr.write(f"publish.py: {e}\n")
        return 1
    except CheckError as e:
        sys.stderr.write(f"publish.py: {e}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
