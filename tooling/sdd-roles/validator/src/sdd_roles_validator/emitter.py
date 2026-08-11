"""role-emit CLI: the D6 table-driven projection emitter (spec sdd-roles-emitter).

project  render the canonical catalog (role registry + optional doctrine
         bodies) through one descriptor row's ``projection`` target table
         into that row's harness layout, all-or-nothing.
verify   re-render and byte-compare against an emitted tree; any drifted,
         missing, or extra path exits 2 with a deterministic listing.

Everything harness-shaped is descriptor data (spec S2): target kinds, paths,
formats, frontmatter key maps, char caps, argument tokens. This module knows
only the neutral card grammar. Rendering is clock-free (spec S5): every
rendered file carries a stamp derived from the kernel schema_version and a
catalog digest — except ``mount-copy`` targets, which byte-copy the shared
``render_mount`` output (one rendering source; decomposition correction #2).

Exit taxonomy (plan F3): argv-level misuse — including a row without a
``projection`` object — exits 1 with usage on stderr and nothing written;
every render/verify-time failure (schema-invalid inputs, cap exceeded,
unresolved token, unknown body stem, drift) exits 2, also writing nothing.

The literal token ``{args}`` inside registry ``invocation`` string fields
renders as the target's ``args_token`` when non-null, verbatim otherwise
(decomposition correction #3).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from .mounts import render_mount
from .report import canonical_dumps

CATALOG_NAME = "sdd-roles"
DOCTRINE_PLACEHOLDER = "<!-- doctrine: pending (build item 5) -->"
INVOCATION_KEYS = ("prompt", "agent", "agents_file", "model")
PER_ROLE_KINDS = ("agent-card", "skill-card")
DEFAULT_FRONT_MATTER = [{"key": "stamp", "source": "stamp"}]

CONSOLE_SCRIPTS = [
    ("contract-lint", "validate artifacts and run the corpus selftest gate"),
    ("gate-wrap", "translate gate tool exits through descriptor exit maps"),
    ("gate-runner", "run the between-run conveyor (sole ledger writer)"),
    ("write-guard", "live write decisions (decide) and hook mounting (mount)"),
    ("role-emit", "project the catalog into harness layouts (project / verify)"),
    ("kata", "the deterministic kata study instrument (plan / analyze / report)"),
]


class Usage(Exception):
    pass


class RenderFailure(Exception):
    pass


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_flags(args: list[str], spec: dict[str, bool]) -> dict[str, str]:
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


# ---------------------------------------------------------------- render --


def _role_description(role: dict) -> str:
    gates = ", ".join(role.get("gates") or []) or "none"
    scopes = ", ".join(role.get("write_scopes") or []) or "none"
    text = f"{role['tag']} role; gates: {gates}; writes: {scopes}"
    if role.get("diagnostic_capability"):
        text += "; diagnostic-capable"
    return text


def _catalog_description(registry: dict) -> str:
    return (
        f"SDD role conveyor catalog; roles: {len(registry.get('roles') or [])}; "
        f"arms: {len(registry.get('arms') or [])}"
    )


def _fm_value(source: str, role: dict | None, registry: dict, stamp: str) -> str:
    if source == "stamp":
        return stamp
    if role is None:
        return CATALOG_NAME if source == "id" else _catalog_description(registry)
    return role["id"] if source == "id" else _role_description(role)


def _front_matter(target: dict, role: dict | None, registry: dict, stamp: str) -> str:
    rows = target.get("front_matter") or DEFAULT_FRONT_MATTER
    lines = ["---"]
    for entry in rows:
        value = _fm_value(entry["source"], role, registry, stamp)
        quoted = value.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'{entry["key"]}: "{quoted}"')
    lines.append("---")
    return "\n".join(lines) + "\n"


def _sub_args(text: str, args_token) -> str:
    if args_token is not None:
        return text.replace("{args}", args_token)
    return text


def _role_card(target: dict, role: dict, registry: dict, stamp: str) -> str:
    args_token = target.get("args_token")
    out = [_front_matter(target, role, registry, stamp)]
    out.append(f"\n# {role['id']}\n\n{_role_description(role)}\n")
    out.append("\n## Contract\n\n")
    out.append(f"- tag: {role['tag']}\n")
    out.append(f"- gates: {', '.join(role.get('gates') or []) or 'none'}\n")
    scopes = ", ".join(f"`{s}`" for s in role.get("write_scopes") or []) or "none (read-only)"
    out.append(f"- write scopes: {scopes}\n")
    out.append(f"- diagnostic capability: {'yes' if role.get('diagnostic_capability') else 'no'}\n")
    out.append("\n## Invocation\n\n")
    invocation = role.get("invocation") or {}
    lines = [
        f"- {key}: {_sub_args(invocation[key], args_token)}\n"
        for key in INVOCATION_KEYS
        if key in invocation
    ]
    if args_token is not None:
        lines.append(f"- arguments token: {args_token}\n")
    out.extend(lines or ["- none declared\n"])
    out.append("\n## Doctrine\n\n")
    return "".join(out)


def _kernel_skill(target: dict, registry: dict, stamp: str) -> str:
    out = [_front_matter(target, None, registry, stamp)]
    out.append(f"\n# {CATALOG_NAME} kernel\n\n{_catalog_description(registry)}\n")
    out.append("\n## Console scripts\n\n")
    for name, blurb in CONSOLE_SCRIPTS:
        out.append(f"- {name}: {blurb}\n")
    out.append("\n## Roles\n\n")
    for role in registry.get("roles") or []:
        out.append(f"- {role['id']}: {_role_description(role)}\n")
    return "".join(out)


def _manifest(registry: dict, version: str, stamp: str) -> bytes:
    return canonical_dumps(
        {
            "name": CATALOG_NAME,
            "description": _catalog_description(registry),
            "version": version,
            "stamp": stamp,
        }
    ).encode("utf-8")


def _fill_path(template: str, role_id: str | None) -> str:
    filled = template.replace("{role}", role_id) if role_id is not None else template
    if "{" in filled or "}" in filled:
        token = filled[filled.index("{") :] if "{" in filled else filled
        raise RenderFailure(f"{template}: unresolved token {token.split('/')[0]}")
    parts = filled.split("/")
    if filled.startswith("/") or ".." in parts or "" in parts:
        raise RenderFailure(f"{template}: path escapes the projection root")
    return filled


def render_projection(
    row: dict, registry: dict, bodies: dict[str, bytes], version: str
) -> dict[str, bytes]:
    """Render one descriptor row's projection targets over the catalog.
    Returns {relative-posix-path: bytes}; raises RenderFailure fail-closed."""
    projection = row.get("projection")
    roles = registry.get("roles") or []
    role_ids = {r["id"] for r in roles}
    unknown = sorted(set(bodies) - role_ids)
    if unknown:
        raise RenderFailure(f"bodies name unknown roles: {', '.join(unknown)}")

    hasher = hashlib.sha256()
    hasher.update(canonical_dumps(registry).encode("utf-8"))
    hasher.update(canonical_dumps(row).encode("utf-8"))
    for stem in sorted(bodies):
        hasher.update(stem.encode("utf-8") + b"\x00" + bodies[stem])
    stamp = f"{CATALOG_NAME} {version} catalog:{hasher.hexdigest()[:12]}"

    files: dict[str, bytes] = {}

    def emit(target: dict, relpath: str, data: bytes) -> None:
        cap = target.get("char_cap")
        if cap is not None and len(data) > cap:
            raise RenderFailure(
                f"{relpath}: rendered size {len(data)} bytes exceeds char_cap {cap}"
            )
        if relpath in files:
            raise RenderFailure(f"{relpath}: two targets render the same path")
        files[relpath] = data

    for target in projection["targets"]:
        kind = target["kind"]
        template = target["path_template"]
        if kind in PER_ROLE_KINDS:
            if "{role}" not in template:
                raise RenderFailure(f"{template}: per-role target lacks {{role}}")
            for role in roles:
                body = bodies.get(role["id"])
                doctrine = (
                    body.decode("utf-8").rstrip("\n") + "\n"
                    if body is not None
                    else DOCTRINE_PLACEHOLDER + "\n"
                )
                text = _role_card(target, role, registry, stamp) + doctrine
                emit(target, _fill_path(template, role["id"]), text.encode("utf-8"))
        elif kind == "kernel-skill":
            emit(
                target,
                _fill_path(template, None),
                _kernel_skill(target, registry, stamp).encode("utf-8"),
            )
        elif kind == "manifest":
            emit(target, _fill_path(template, None), _manifest(registry, version, stamp))
        else:  # mount-copy (schema-closed enum)
            hooks = row.get("hooks")
            if not isinstance(hooks, dict):
                raise RenderFailure(f"{template}: mount-copy requires a hooks object")
            emit(
                target,
                _fill_path(template, None),
                render_mount(row["harness"], hooks, roles),
            )
    return files


# ------------------------------------------------------------------- cli --


def _load_inputs(flags: dict[str, str]):
    kernel = Path(flags["kernel"])
    version_file = kernel / "VERSION"
    if not version_file.is_file():
        raise Usage("kernel directory has no VERSION file")
    version = version_file.read_text(encoding="utf-8").strip()

    descriptors_path = Path(flags["descriptors"])
    if not descriptors_path.is_file():
        raise Usage("descriptor file not found")
    try:
        doc = _read_json(descriptors_path)
    except (OSError, ValueError):
        raise Usage("descriptor file is not valid JSON")
    rows = doc.get("rows", []) if isinstance(doc, dict) else []
    row = next(
        (r for r in rows if isinstance(r, dict) and r.get("harness") == flags["harness"]),
        None,
    )
    if row is None:
        raise Usage(f"no descriptor row for harness '{flags['harness']}'")
    if not isinstance(row.get("projection"), dict):
        raise Usage(f"descriptor row for '{flags['harness']}' has no projection object")

    registry_path = Path(flags["registry"])
    if not registry_path.is_file():
        raise Usage("registry file not found")
    try:
        registry = _read_json(registry_path)
    except (OSError, ValueError):
        raise Usage("registry file is not valid JSON")

    bodies: dict[str, bytes] = {}
    if "bodies" in flags:
        bodies_dir = Path(flags["bodies"])
        if not bodies_dir.is_dir():
            raise Usage("bodies directory not found")
        for path in sorted(bodies_dir.glob("*.md")):
            bodies[path.stem] = path.read_bytes()

    # Fail-closed render: both catalog inputs must satisfy their schemas.
    try:
        import jsonschema

        from .loader import SCHEMA_FILES

        jsonschema.validate(
            registry, _read_json(kernel / "schemas" / SCHEMA_FILES["role_registry"])
        )
        jsonschema.validate(
            doc, _read_json(kernel / "schemas" / SCHEMA_FILES["invocation_descriptor_set"])
        )
    except Usage:
        raise
    except Exception:
        raise RenderFailure("registry or descriptor set fails schema validation")

    return row, registry, bodies, version


_FLAGS = {
    "kernel": True,
    "descriptors": True,
    "harness": True,
    "registry": True,
    "out": True,
    "bodies": False,
}


def project(args: list[str]) -> int:
    flags = _parse_flags(args, _FLAGS)
    row, registry, bodies, version = _load_inputs(flags)
    files = render_projection(row, registry, bodies, version)
    out_root = Path(flags["out"])
    for relpath in sorted(files):
        dest = out_root / relpath
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(files[relpath])
    sys.stdout.write(f"projected {flags['harness']}: {len(files)} files\n")
    return 0


def verify(args: list[str]) -> int:
    flags = _parse_flags(args, _FLAGS)
    row, registry, bodies, version = _load_inputs(flags)
    files = render_projection(row, registry, bodies, version)
    out_root = Path(flags["out"])
    if not out_root.is_dir():
        raise RenderFailure(f"emitted tree not found: {flags['out']}")
    on_disk = {
        p.relative_to(out_root).as_posix(): p.read_bytes()
        for p in sorted(out_root.rglob("*"))
        if p.is_file()
    }
    problems = []
    for relpath in sorted(set(files) | set(on_disk)):
        if relpath not in on_disk:
            problems.append(f"missing {relpath}")
        elif relpath not in files:
            problems.append(f"extra {relpath}")
        elif files[relpath] != on_disk[relpath]:
            problems.append(f"drift {relpath}")
    if problems:
        sys.stdout.write("".join(line + "\n" for line in problems))
        sys.stderr.write(
            f"role-emit: verify failed for '{flags['harness']}': "
            f"{len(problems)} path(s) diverge\n"
        )
        return 2
    sys.stdout.write(f"verified {flags['harness']}: {len(files)} files\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if not args:
            raise Usage("subcommand required: project | verify")
        cmd, rest = args[0], args[1:]
        if cmd == "project":
            return project(rest)
        if cmd == "verify":
            return verify(rest)
        raise Usage(f"unknown subcommand '{cmd}'")
    except Usage as u:
        sys.stderr.write(f"role-emit: error: {u}\n")
        return 1
    except RenderFailure as r:
        sys.stderr.write(f"role-emit: render failure: {r}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
