#!/usr/bin/env python3
"""skill-sync — manifest-driven drift guard for skill-surface copies.

check    byte-compare every source<->projection pair per the manifest; report
         drift (grammar: docs/sdd/specs/skill-sync.spec.md). Read-only.
fix      make projections exact mirrors of their sources (full mirror, C2),
         then re-run check; the re-check result is the exit code.
selftest fixture-based self-verification (spec FR-5).

Exit codes: 0 clean/green · 1 usage/config error · 2 drift (or failed
selftest / post-fix re-check). Stdlib only; Python >= 3.11 (tomllib) — the
repo's existing validator floor. Spec: SPEC-OK 2026-08-10.
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

try:
    import tomllib
except ImportError:  # pragma: no cover — spec AC-9 floor; fail loud, never silently green
    sys.stderr.write("skill-sync: Python >= 3.11 required (tomllib)\n")
    sys.exit(1)


class ManifestError(Exception):
    """Manifest missing/unparsable/naming a nonexistent source (spec AC-4)."""


# ---------------------------------------------------------------------------
# Core (T1.3). Determinism by construction: sorted walks, manifest order,
# findings deduped across projections by (kind, relpath) — the grammar has no
# projection column, and one drifted pair anywhere makes the relpath drifted.
# ---------------------------------------------------------------------------
_KIND_RANK = {"CHANGED": 0, "MISSING": 1, "EXTRA": 2}


def load_manifest(root: Path, manifest_path: Path) -> list[dict]:
    if not manifest_path.is_file():
        raise ManifestError(f"manifest not found: {manifest_path}")
    try:
        data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise ManifestError(f"manifest unparsable: {e}")
    fams = data.get("family")
    if not isinstance(fams, list) or not fams:
        raise ManifestError("manifest: at least one [[family]] entry required")
    out: list[dict] = []
    for f in fams:
        fid, src, projs = f.get("id"), f.get("source"), f.get("projections")
        if not (isinstance(fid, str) and isinstance(src, str) and isinstance(projs, list) and projs):
            raise ManifestError(f"family entry malformed (id/source/projections): {f!r}")
        members = f.get("members")
        if members is not None and not (
            isinstance(members, list) and members and all(isinstance(m, str) for m in members)
        ):
            raise ManifestError(f"family {fid}: members must be a non-empty list of strings")
        sdir = root / src
        if members:
            for m in members:
                if not (sdir / m).is_dir():
                    raise ManifestError(f"family {fid}: source member missing: {src}/{m}")
        elif not sdir.is_dir():
            raise ManifestError(f"family {fid}: source dir missing: {src}")
        out.append(
            {"id": fid, "source": sdir, "members": members, "projections": [(root / p, p) for p in projs]}
        )
    return out


def _walk_files(base: Path, prefix: str = "") -> dict[str, Path]:
    """Sorted map of posix relpath -> file Path. Files only (spec grammar)."""
    found: dict[str, Path] = {}
    if not base.is_dir():
        return found
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames.sort()
        for fn in sorted(filenames):
            p = Path(dirpath) / fn
            found[prefix + p.relative_to(base).as_posix()] = p
    return found


def _source_map(fam: dict) -> dict[str, Path]:
    if fam["members"]:
        m: dict[str, Path] = {}
        for name in fam["members"]:
            m.update(_walk_files(fam["source"] / name, name + "/"))
        return m
    return _walk_files(fam["source"])


def _family_findings(fam: dict) -> tuple[list[tuple[int, str, str]], int]:
    source_map = _source_map(fam)
    findings: set[tuple[int, str, str]] = set()
    for proj_abs, proj_rel in fam["projections"]:
        if fam["members"]:
            for name in fam["members"]:
                if not (proj_abs / name).is_dir():
                    findings.add((1, "MISSING", name + "/"))  # dir reported once, files not enumerated
                    continue
                for rel, spath in source_map.items():
                    if not rel.startswith(name + "/"):
                        continue
                    target = proj_abs / rel
                    if not target.is_file():
                        findings.add((1, "MISSING", rel))
                    elif target.read_bytes() != spath.read_bytes():
                        findings.add((0, "CHANGED", rel))
                for rel in _walk_files(proj_abs / name, name + "/"):
                    if rel not in source_map:
                        findings.add((2, "EXTRA", rel))
        else:
            if not proj_abs.is_dir():
                findings.add((1, "MISSING", proj_rel.rstrip("/") + "/"))
                continue
            for rel, spath in source_map.items():
                target = proj_abs / rel
                if not target.is_file():
                    findings.add((1, "MISSING", rel))
                elif target.read_bytes() != spath.read_bytes():
                    findings.add((0, "CHANGED", rel))
            for rel in _walk_files(proj_abs):
                if rel not in source_map:
                    findings.add((2, "EXTRA", rel))
    # F1/P2.1 (spec amendment A2): one line per relpath — cross-projection
    # divergence collapses to the worst kind. MISSING beats CHANGED; EXTRA
    # relpaths are disjoint from source relpaths, so they never collide.
    worst: dict[str, tuple[int, str]] = {}
    for rank, kind, rel in findings:
        held = worst.get(rel)
        if held is None or (kind == "MISSING" and held[1] == "CHANGED"):
            worst[rel] = (rank, kind)
    collapsed = sorted((rank, kind, rel) for rel, (rank, kind) in worst.items())
    return collapsed, len(source_map) * len(fam["projections"])


def _shadow_names(fams: list[dict], user_scope: Path) -> list[str]:
    """P6: user-scope names colliding with project skill names (spec FR-4).

    Project skill names = basenames of `.claude/skills/`-rooted projection
    member dirs. Advisory only (C1) — callers never let this touch the exit.
    """
    project: set[str] = set()
    for fam in fams:
        for _abs, rel in fam["projections"]:
            posix = rel.rstrip("/")
            if posix == ".claude/skills" and fam["members"]:
                project.update(fam["members"])
            elif posix.startswith(".claude/skills/"):
                project.add(Path(posix).name)
    if not user_scope.is_dir():  # machine without a user-scope skills dir: nothing can shadow
        return []
    # F5/P2.5: only directories are skills — a loose file with a skill name cannot shadow
    return sorted(project & {p.name for p in user_scope.iterdir() if p.is_dir()})


def run_check(root: Path, manifest_path: Path, user_scope: Path) -> tuple[list[str], int]:
    try:
        fams = load_manifest(root, manifest_path)
    except ManifestError as e:
        sys.stderr.write(f"ERROR: {e}\n")  # F6/P2.6: diagnostics to stderr; stdout report stays empty (AC-4)
        return ([], 1)
    lines: list[str] = []
    ok_lines: list[str] = []
    drifted = 0
    for fam in fams:
        findings, pairs = _family_findings(fam)
        if findings:
            drifted += 1
            lines.extend(f"DRIFT {fam['id']} {kind} {rel}" for _, kind, rel in findings)
        else:
            n_proj = len(fam["projections"])
            ok_lines.append(
                f"OK {fam['id']} ({pairs} file-pairs / {n_proj} projection{'s' if n_proj != 1 else ''})"
            )
    shadows = _shadow_names(fams, user_scope)
    lines.extend(f"SHADOW {n}" for n in shadows)
    lines.extend(ok_lines)
    code = 2 if drifted else 0
    lines.append(f"SUMMARY: {len(fams)} families, {drifted} drifted, {len(shadows)} shadow -> exit {code}")
    return lines, code


def run_fix(root: Path, manifest_path: Path, user_scope: Path) -> tuple[list[str], int]:
    """Full mirror (C2): write missing/changed, delete extras — confined to
    manifest projection dirs (AC-8) — then re-run check; its result is the
    exit code (AC-6). Part 0.2 of the usage guide, as code."""
    try:
        fams = load_manifest(root, manifest_path)
    except ManifestError as e:
        sys.stderr.write(f"ERROR: {e}\n")  # F6/P2.6: same stderr discipline as check
        return ([], 1)
    lines: list[str] = []
    for fam in fams:
        source_map = _source_map(fam)
        for proj_abs, proj_rel in fam["projections"]:
            proj_prefix = proj_rel.rstrip("/")  # A1 (F2): FIXED lines carry the projection
            for rel, spath in source_map.items():
                target = proj_abs / rel
                if not target.is_file() or target.read_bytes() != spath.read_bytes():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(spath.read_bytes())
                    lines.append(f"FIXED {fam['id']} WROTE {proj_prefix}/{rel}")
            scan_roots = (
                [(proj_abs / m, m + "/") for m in fam["members"]] if fam["members"] else [(proj_abs, "")]
            )
            for base, prefix in scan_roots:
                for rel, p in _walk_files(base, prefix).items():
                    if rel not in source_map:
                        p.unlink()
                        lines.append(f"FIXED {fam['id']} DELETED {proj_prefix}/{rel}")
    check_lines, code = run_check(root, manifest_path, user_scope)
    return lines + check_lines, code


# ---------------------------------------------------------------------------
# Selftest fixtures (spec FR-5) — sections assert exit codes AND literal
# report-grammar lines. Each section builds a fresh tree under a temp dir.
# ---------------------------------------------------------------------------
_MANIFEST_FIXTURE = """\
[[family]]
id = "alpha"
source = "src-alpha"
members = ["a1", "a2"]
projections = [".claude/skills", "alt-proj"]

[[family]]
id = "beta"
source = "src-beta"
projections = ["proj-beta"]
"""


def _w(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _build_ws(tmp: Path) -> tuple[Path, Path, Path]:
    """Clean two-family workspace: alpha (members, 2 projections), beta (flat)."""
    ws = tmp / "ws"
    for base in ("src-alpha", ".claude/skills", "alt-proj"):
        _w(ws / base / "a1" / "f1.txt", "one\n")
        _w(ws / base / "a1" / "sub" / "f2.txt", "two\n")
        _w(ws / base / "a2" / "g.txt", "gee\n")
    _w(ws / "src-beta" / "b.txt", "bee\n")
    _w(ws / "proj-beta" / "b.txt", "bee\n")
    manifest = ws / "manifest.toml"
    manifest.write_text(_MANIFEST_FIXTURE, encoding="utf-8")
    user = tmp / "user-skills"
    user.mkdir()
    return ws, manifest, user


_CLEAN_LINES = [
    "OK alpha (6 file-pairs / 2 projections)",
    "OK beta (1 file-pairs / 1 projection)",
    "SUMMARY: 2 families, 0 drifted, 0 shadow -> exit 0",
]


def _expect(errs: list[str], cond: bool, msg: str) -> None:
    if not cond:
        errs.append(msg)


def _t_clean(tmp: Path) -> list[str]:
    ws, mf, user = _build_ws(tmp)
    lines, code = run_check(ws, mf, user)
    errs: list[str] = []
    _expect(errs, code == 0, f"exit: expected 0, got {code}")
    _expect(errs, lines == _CLEAN_LINES, f"lines: expected {_CLEAN_LINES}, got {lines}")
    return errs


def _t_changed(tmp: Path) -> list[str]:
    ws, mf, user = _build_ws(tmp)
    _w(ws / ".claude/skills" / "a1" / "f1.txt", "ALTERED\n")
    lines, code = run_check(ws, mf, user)
    errs: list[str] = []
    _expect(errs, code == 2, f"exit: expected 2, got {code}")
    _expect(errs, "DRIFT alpha CHANGED a1/f1.txt" in lines, f"missing CHANGED line: {lines}")
    _expect(errs, "OK beta (1 file-pairs / 1 projection)" in lines, "beta OK line absent")
    _expect(errs, not any(l.startswith("OK alpha") for l in lines), "drifted alpha must not report OK")
    _expect(errs, "SUMMARY: 2 families, 1 drifted, 0 shadow -> exit 2" in lines, f"summary wrong: {lines}")
    return errs


def _t_missing_file(tmp: Path) -> list[str]:
    ws, mf, user = _build_ws(tmp)
    (ws / ".claude/skills" / "a1" / "sub" / "f2.txt").unlink()
    lines, code = run_check(ws, mf, user)
    errs: list[str] = []
    _expect(errs, code == 2, f"exit: expected 2, got {code}")
    _expect(errs, "DRIFT alpha MISSING a1/sub/f2.txt" in lines, f"missing MISSING line: {lines}")
    return errs


def _t_missing_dir(tmp: Path) -> list[str]:
    import shutil

    ws, mf, user = _build_ws(tmp)
    shutil.rmtree(ws / ".claude/skills" / "a2")
    lines, code = run_check(ws, mf, user)
    errs: list[str] = []
    _expect(errs, code == 2, f"exit: expected 2, got {code}")
    _expect(errs, "DRIFT alpha MISSING a2/" in lines, f"missing dir line: {lines}")
    _expect(errs, not any("a2/g.txt" in l for l in lines), "missing dir must not enumerate contained files")
    return errs


def _t_extra(tmp: Path) -> list[str]:
    ws, mf, user = _build_ws(tmp)
    _w(ws / ".claude/skills" / "a1" / "stray.txt", "stray\n")
    lines, code = run_check(ws, mf, user)
    errs: list[str] = []
    _expect(errs, code == 2, f"exit: expected 2, got {code}")
    _expect(errs, "DRIFT alpha EXTRA a1/stray.txt" in lines, f"missing EXTRA line: {lines}")
    return errs


def _t_cross_projection(tmp: Path) -> list[str]:
    """F1/P2.1: same relpath CHANGED in one projection, MISSING in the other
    -> exactly one DRIFT line, worst kind (MISSING over CHANGED)."""
    ws, mf, user = _build_ws(tmp)
    _w(ws / ".claude/skills" / "a1" / "f1.txt", "ALTERED\n")
    (ws / "alt-proj" / "a1" / "f1.txt").unlink()
    lines, code = run_check(ws, mf, user)
    errs: list[str] = []
    _expect(errs, code == 2, f"exit: expected 2, got {code}")
    _expect(errs, "DRIFT alpha MISSING a1/f1.txt" in lines, f"worst-kind MISSING line absent: {lines}")
    _expect(
        errs,
        "DRIFT alpha CHANGED a1/f1.txt" not in lines,
        f"collapsed relpath must not also report CHANGED: {lines}",
    )
    return errs


def _t_bad_manifest(tmp: Path) -> list[str]:
    ws, mf, user = _build_ws(tmp)
    errs: list[str] = []
    mf.write_text("not = [broken", encoding="utf-8")
    lines1, code = run_check(ws, mf, user)
    _expect(errs, code == 1, f"unparsable manifest: expected exit 1, got {code}")
    _expect(errs, lines1 == [], f"AC-4 (F6): stdout report must be empty on config error, got {lines1}")
    mf.write_text(
        _MANIFEST_FIXTURE.replace('source = "src-alpha"', 'source = "nope"'), encoding="utf-8"
    )
    lines2, code = run_check(ws, mf, user)
    _expect(errs, code == 1, f"nonexistent source: expected exit 1, got {code}")
    _expect(errs, lines2 == [], f"AC-4 (F6): stdout report must be empty on config error, got {lines2}")
    return errs


def _t_shadow(tmp: Path) -> list[str]:
    ws, mf, user = _build_ws(tmp)
    (user / "a1").mkdir()  # user-scope name colliding with project skill a1
    (user / "a2").write_text("loose file, not a skill dir\n", encoding="utf-8")  # F5/P2.5
    lines, code = run_check(ws, mf, user)
    errs: list[str] = []
    _expect(errs, code == 0, f"advisory (C1): expected exit 0, got {code}")
    _expect(errs, "SHADOW a1" in lines, f"missing SHADOW line: {lines}")
    _expect(errs, "SHADOW a2" not in lines, f"loose files must not shadow (F5): {lines}")
    _expect(errs, "SUMMARY: 2 families, 0 drifted, 1 shadow -> exit 0" in lines, f"summary wrong: {lines}")
    return errs


def _t_fix_drifted(tmp: Path) -> list[str]:
    ws, mf, user = _build_ws(tmp)
    _w(ws / ".claude/skills" / "a1" / "f1.txt", "ALTERED\n")
    (ws / ".claude/skills" / "a1" / "sub" / "f2.txt").unlink()
    lines, code = run_fix(ws, mf, user)
    errs: list[str] = []
    _expect(errs, code == 0, f"post-fix re-check governs exit: expected 0, got {code}")
    _expect(errs, "FIXED alpha WROTE .claude/skills/a1/f1.txt" in lines, f"missing projection-prefixed WROTE line (A1): {lines}")
    _expect(errs, "FIXED alpha WROTE .claude/skills/a1/sub/f2.txt" in lines, f"missing projection-prefixed WROTE (restored) line (A1): {lines}")
    _expect(
        errs,
        (ws / ".claude/skills/a1/f1.txt").read_bytes() == (ws / "src-alpha/a1/f1.txt").read_bytes(),
        "f1.txt not mirrored back to source bytes",
    )
    _expect(errs, "SUMMARY: 2 families, 0 drifted, 0 shadow -> exit 0" in lines, f"re-check summary wrong: {lines}")
    return errs


def _t_fix_extra(tmp: Path) -> list[str]:
    ws, mf, user = _build_ws(tmp)
    _w(ws / ".claude/skills" / "a1" / "stray.txt", "stray\n")
    outside = ws / "src-alpha" / "a1" / "f1.txt"
    before = outside.read_bytes()
    lines, code = run_fix(ws, mf, user)
    errs: list[str] = []
    _expect(errs, code == 0, f"post-fix re-check governs exit: expected 0, got {code}")
    _expect(errs, "FIXED alpha DELETED .claude/skills/a1/stray.txt" in lines, f"missing projection-prefixed DELETED line (C2/A1): {lines}")
    _expect(errs, not (ws / ".claude/skills/a1/stray.txt").exists(), "stray not deleted (C2 full mirror)")
    _expect(errs, outside.read_bytes() == before, "fix wrote outside projection dirs (AC-8 violation)")
    return errs


_SECTIONS: list[tuple[str, object]] = [
    ("clean", _t_clean),
    ("changed", _t_changed),
    ("missing-file", _t_missing_file),
    ("missing-dir", _t_missing_dir),
    ("extra", _t_extra),
    ("cross-projection", _t_cross_projection),
    ("bad-manifest", _t_bad_manifest),
    ("shadow", _t_shadow),
    ("fix-drifted", _t_fix_drifted),
    ("fix-extra", _t_fix_extra),
]


def cmd_selftest() -> int:
    failed = 0
    for name, fn in _SECTIONS:
        with tempfile.TemporaryDirectory() as td:
            errs = fn(Path(td))  # type: ignore[operator]
        print(f"[{'PASS' if not errs else 'FAIL'}] {name}")
        for e in errs:
            print(f"    - {e}")
        failed += 1 if errs else 0
    print(f"selftest: {len(_SECTIONS) - failed}/{len(_SECTIONS)} sections pass")
    return 0 if failed == 0 else 2


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="skill-sync", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("check", "fix"):
        p = sub.add_parser(c)
        p.add_argument("--root", default=".", help="workspace root (default: cwd)")
        p.add_argument("--manifest", default=None, help="manifest path (default: <root>/tooling/skill-sync/manifest.toml)")
        p.add_argument("--user-scope", default=None, help="user-scope skills dir (default: ~/.claude/skills)")
    sub.add_parser("selftest")
    args = ap.parse_args(argv)

    if args.cmd == "selftest":
        return cmd_selftest()

    root = Path(args.root).resolve()
    manifest = Path(args.manifest) if args.manifest else root / "tooling/skill-sync/manifest.toml"
    user_scope = Path(args.user_scope) if args.user_scope else Path.home() / ".claude" / "skills"
    run = run_check if args.cmd == "check" else run_fix
    lines, code = run(root, manifest, user_scope)
    for l in lines:
        print(l)
    return code


if __name__ == "__main__":
    sys.exit(main())
