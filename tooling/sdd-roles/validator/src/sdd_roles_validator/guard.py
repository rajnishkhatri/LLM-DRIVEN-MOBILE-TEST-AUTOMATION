"""write-guard CLI: the D7-floor live enforcement shim (spec sdd-roles-guard).

decide  evaluate one write request against the kernel contract (protected set
        + role write scopes, via the shared scopes.py rule core) and the
        workspace; stdout is exactly one line — ``allow`` or
        ``block <CODE> <path>`` — with human detail on stderr.
mount   render a descriptor row's ``hooks`` fields into the harness
        hook-config artifact, one rule per registry role.

Exit taxonomy (plan F1, fail-closed split): argv-level misuse exits 1 with no
decision line (a mount defect — mounts are golden-verified); every failure
while evaluating a request exits 2 as ``block FAIL_CLOSED -`` so a mounted
guard can never allow by accident (some harness hook protocols treat exit 1
as non-blocking). The guard is stateless and clock-free: it writes nothing,
and identical inputs produce identical bytes.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from .mounts import render_mount
from .scopes import hard_patterns, match_any, tests_patterns, write_tags

OPERATIONS = ("create", "modify", "delete")


class Usage(Exception):
    pass


class Block(Exception):
    def __init__(self, code: str, path: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.path = path
        self.detail = detail


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_flags(args: list[str], spec: dict[str, bool]) -> dict[str, str]:
    """spec maps --flag name (sans dashes) -> required?"""
    out: dict[str, str] = {}
    i = 0
    while i < len(args):
        token = args[i]
        if not token.startswith("--") or token[2:] not in spec:
            raise Usage(f"unrecognized argument '{token}'")
        if i + 1 >= len(args):
            raise Usage(f"missing value for '{token}'")
        out[token[2:]] = args[i + 1]
        i += 2
    for name, required in spec.items():
        if required and name not in out:
            raise Usage(f"--{name} is required")
    return out


# ---------------------------------------------------------------- decide --


def _pointer(doc, ptr: str):
    """Minimal RFC 6901 resolver; None on any miss."""
    if not ptr.startswith("/"):
        return None
    node = doc
    for raw in ptr[1:].split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict):
            if key not in node:
                return None
            node = node[key]
        elif isinstance(node, list):
            if not key.isdigit() or int(key) >= len(node):
                return None
            node = node[int(key)]
        else:
            return None
    return node


def _canonical_abs(root: Path, raw: str) -> str | None:
    """Absolute, symlink-resolved, normalized form of `raw` (resolved against
    `root` when relative), or None on an unresolvable cycle. Symlinks in
    existing ancestors are resolved BEFORE lexical `..` collapse (the
    permissive order would launder link-escapes), iterating to a fixpoint so
    links exposed by the collapse are resolved too."""
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = root / candidate
    text = str(candidate)
    for _ in range(8):
        probe, tail = Path(text), []
        while not probe.exists() and probe.parent != probe:
            tail.append(probe.name)
            probe = probe.parent
        real = probe.resolve()
        for name in reversed(tail):
            real = real / name
        normalized = os.path.normpath(str(real))
        if normalized == text:
            break
        text = normalized
    else:
        return None
    return text


def _contained_rel(root: Path, raw: str) -> str | None:
    """Workspace-relative posix path of `raw`, or None when it escapes the
    root (or is unresolvable). Canonicalization — including the link-escape
    laundering defense — lives in `_canonical_abs`."""
    text = _canonical_abs(root, raw)
    if text is None:
        return None
    try:
        rel = Path(text).relative_to(root)
    except ValueError:
        return None
    return rel.as_posix() or None


def _request_from_payload(payload, hooks: dict) -> tuple[list[str], str]:
    request = hooks.get("request") or {}
    paths = []
    for ptr in request.get("paths_pointers") or []:
        value = _pointer(payload, ptr)
        if isinstance(value, str) and value:
            paths.append(value)
    operation_spec = request.get("operation") or {}
    value = _pointer(payload, operation_spec.get("pointer") or "")
    operation = operation_spec.get("default")
    for row in operation_spec.get("map") or []:
        if isinstance(row, dict) and row.get("from") == value:
            operation = row.get("to")
            break
    return paths, operation


def decide(args: list[str]) -> int:
    flags = _parse_flags(
        args,
        {
            "kernel": True,
            "config": True,
            "registry": True,
            "workspace": True,
            "run-dir": True,
            "role": True,
            "descriptors": False,
            "harness": False,
            "request": False,
        },
    )
    if ("descriptors" in flags) != ("harness" in flags):
        raise Usage("--descriptors and --harness must be given together")

    # From here on every failure is an evaluation failure: block, fail-closed.
    try:
        return _decide_inner(flags)
    except Block as b:
        sys.stdout.write(f"block {b.code} {b.path}\n")
        sys.stderr.write(f"write-guard: {b.detail}\n")
        return 2


def _fail(detail: str) -> Block:
    return Block("FAIL_CLOSED", "-", detail)


def _decide_inner(flags: dict[str, str]) -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw)
    except (OSError, ValueError):
        raise _fail("request is not valid JSON")

    kernel = Path(flags["kernel"])
    try:
        import jsonschema

        from .loader import SCHEMA_FILES

        config = _read_json(Path(flags["config"]))
        registry = _read_json(Path(flags["registry"]))
        jsonschema.validate(config, _read_json(kernel / "schemas" / SCHEMA_FILES["kernel_config"]))
        jsonschema.validate(
            registry, _read_json(kernel / "schemas" / SCHEMA_FILES["role_registry"])
        )
    except Exception:
        raise _fail("config or registry unreadable or schema-invalid")

    role = next(
        (r for r in registry.get("roles", []) if isinstance(r, dict) and r.get("id") == flags["role"]),
        None,
    )
    if role is None:
        raise _fail(f"role '{flags['role']}' not in registry")

    if "descriptors" in flags:
        try:
            rows = _read_json(Path(flags["descriptors"])).get("rows", [])
        except (OSError, ValueError):
            raise _fail("descriptor file unreadable")
        row = next((r for r in rows if r.get("harness") == flags["harness"]), None)
        if row is None or not isinstance(row.get("hooks"), dict):
            raise _fail(f"no hooks row for harness '{flags['harness']}'")
        paths, operation = _request_from_payload(payload, row["hooks"])
    else:
        paths = payload.get("paths") if isinstance(payload, dict) else None
        operation = payload.get("operation") if isinstance(payload, dict) else None

    if not isinstance(paths, list) or not paths or not all(isinstance(p, str) and p for p in paths):
        raise _fail("request yields no candidate paths")
    if operation not in OPERATIONS:
        raise _fail(f"request operation is not one of {OPERATIONS}")

    workspace = Path(flags["workspace"]).resolve()
    if not workspace.is_dir():
        raise _fail("workspace root is not a directory")
    run_dir = Path(flags["run-dir"]).resolve()

    hard = hard_patterns(config)
    tests = tests_patterns(config)
    ledger_pats = ((config.get("protected") or {}).get("ledger_dir")) or []

    for raw_path in paths:
        _evaluate(raw_path, operation, role, workspace, run_dir, hard, tests, ledger_pats)

    sys.stdout.write("allow\n")
    return 0


def _evaluate(raw_path, operation, role, workspace, run_dir, hard, tests, ledger_pats) -> None:
    # ADR 0006 handoff-draft carve-out (amendment 2026-08-10): the current
    # stage role may CREATE or MODIFY exactly <run_dir>/handoff.draft — the
    # transient note the gate-runner reads and then unlinks. Checked BEFORE
    # containment because the run dir routinely sits OUTSIDE the workspace
    # (copy-per-cell isolation), where REPO_SCOPE would otherwise pre-empt the
    # write. The candidate is symlink-resolved (_canonical_abs) and compared to
    # the LEXICAL draft path, so a handoff.draft symlink cannot launder a write
    # onto a protected or escaping target: it resolves away from the literal
    # path, misses this exemption, and falls through to normal evaluation.
    # delete is never exempt (the runner owns the unlink); every other run-dir
    # path stays writer-only.
    if operation in ("create", "modify"):
        draft = os.path.normpath(str(run_dir / "handoff.draft"))
        if _canonical_abs(workspace, raw_path) == draft:
            return

    rel = _contained_rel(workspace, raw_path)
    if rel is None:
        raise Block("REPO_SCOPE", raw_path, "path escapes the workspace root")
    target = workspace / rel

    if rel == ".git" or rel.startswith(".git/"):
        raise Block("VCS_INTERNAL", rel, "VCS internals are not writable by roles")

    inside_run_dir = target == run_dir or run_dir in target.parents
    if inside_run_dir or match_any(rel, ledger_pats):
        raise Block("WRITER_ONLY", rel, "only the gate-runner writes the run directory and ledger")

    # The retro-lint's change vocabulary, resolved live from the disk: a
    # create whose target already exists is a modify (spec S4).
    exists = target.exists()
    if operation == "delete":
        change = "deleted"
    elif operation == "create" and not exists:
        change = "added"
    else:
        change = "modified"

    tags = write_tags(rel, change, role, hard, tests)
    if "protected" in tags:
        raise Block("PROTECTED", rel, "path is in the protected set")
    if "maker_tests" in tags:
        raise Block("TESTS_PROTECTED", rel, "maker roles may add tests, never modify or delete them")
    if "outside_scope" in tags:
        raise Block("SCOPE", rel, "path is outside the role's write scopes")


# ----------------------------------------------------------------- mount --


def mount(args: list[str]) -> int:
    flags = _parse_flags(
        args, {"descriptors": True, "harness": True, "registry": True, "out": True}
    )
    path = Path(flags["descriptors"])
    if not path.is_file():
        raise Usage("descriptor file not found")
    try:
        rows = _read_json(path).get("rows", [])
    except (OSError, ValueError):
        raise Usage("descriptor file is not valid JSON")
    row = next((r for r in rows if isinstance(r, dict) and r.get("harness") == flags["harness"]), None)
    if row is None:
        raise Usage(f"no descriptor row for harness '{flags['harness']}'")
    hooks = row.get("hooks")
    if not isinstance(hooks, dict):
        raise Usage(f"descriptor row for '{flags['harness']}' has no hooks object")
    registry_path = Path(flags["registry"])
    if not registry_path.is_file():
        raise Usage("registry file not found")
    try:
        roles = _read_json(registry_path).get("roles", [])
    except (OSError, ValueError):
        raise Usage("registry file is not valid JSON")

    dest = Path(flags["out"]) / hooks["mount_path"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(render_mount(flags["harness"], hooks, roles))
    sys.stdout.write(f"mounted {hooks['mount_path']}\n")
    return 0


# ------------------------------------------------------------------ main --


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if not args:
            raise Usage("subcommand required: decide | mount")
        cmd, rest = args[0], args[1:]
        if cmd == "decide":
            return decide(rest)
        if cmd == "mount":
            return mount(rest)
        raise Usage(f"unknown subcommand '{cmd}'")
    except Usage as u:
        sys.stderr.write(f"write-guard: error: {u}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
