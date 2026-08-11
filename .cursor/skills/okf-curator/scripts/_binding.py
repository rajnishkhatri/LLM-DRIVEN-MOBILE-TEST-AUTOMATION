"""Shared OKF workspace-binding loader for the bundled curator scripts.

Resolution order (see the skill's FIRST_RUN.md / binding.schema.md):

  1. an explicit ``--binding PATH`` (passed through as ``explicit``);
  2. ``.okf/binding.toml`` discovered by walking upward from ``start``;
  3. the committed reference two levels above this file's skill dir
     (``…/docs/skills/_okf/binding.reference.toml`` — present only inside the
     skill's home repo; absent in a foreign drop-in install).

Nothing resolvable → ``BindingNotFoundError`` pointing at FIRST_RUN.md. The
caller decides the exit code; no script may lint/scan with a guessed binding
(AP-6: undecidable → ask, never fabricate).

Pure stdlib (``tomllib``); no third-party dependency.
"""

from __future__ import annotations

import tomllib
from pathlib import Path, PurePosixPath


class BindingNotFoundError(RuntimeError):
    """No binding resolvable — the caller must hard-exit, not guess."""


class BindingParseError(RuntimeError):
    """The binding file exists but is not valid TOML."""


class BindingIncompleteError(RuntimeError):
    """The binding resolved but omits a key the run requires."""


def require(binding: dict, table: str, key: str, path: Path) -> object:
    """Return ``binding[table][key]``, or raise naming both the key and the file.

    A required key that is ABSENT is a setup error, never an empty result: a
    missing ``declared_bundles`` would otherwise lint zero bundles and exit 0,
    and a missing ``code_prefixes`` would report "no code changed" — clean
    answers the binding never actually asserted (AP-6: undecidable → say so).
    An explicitly empty list is a different, legal state and passes through.
    """
    section = binding.get(table)
    if not isinstance(section, dict) or key not in section:
        raise BindingIncompleteError(
            f"binding at {path} declares no [{table}].{key} — add it (see the "
            f"skill's binding.schema.md). Refusing to report a result the "
            f"binding does not declare."
        )
    return section[key]


def require_str_list(binding: dict, table: str, key: str, path: Path) -> list[str]:
    """``require`` + the value must be a list of strings.

    A bare string is iterable, so an un-shape-checked ``tuple(value)`` silently
    splits ``"kb/notes"`` into single CHARACTERS — one of which is ``/``, which
    then resolves to the filesystem root. Forgetting the TOML brackets is an
    ordinary first-run typo, so this is checked, not assumed.
    """
    value = require(binding, table, key, path)
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise BindingIncompleteError(
            f"[{table}].{key} in {path} must be a list of strings, got "
            f"{value!r} — did you forget the [brackets]?"
        )
    return value


def require_relative_paths(
    binding: dict, table: str, key: str, path: Path
) -> list[str]:
    """``require_str_list`` + every entry must stay inside the workspace root.

    These values are joined onto the root to reach files, so an absolute path or
    a ``..`` segment escapes the workspace: ``root / "/etc"`` IS ``/etc``. The
    binding is discovered by walking upward from cwd and would be committed to a
    repo, so a cloned workspace can supply it — treat it as input, not as
    trusted local config (ADR-0039 consequence).
    """
    values = require_str_list(binding, table, key, path)
    escaping = [
        v for v in values if PurePosixPath(v).is_absolute() or ".." in Path(v).parts
    ]
    if escaping:
        raise BindingIncompleteError(
            f"[{table}].{key} in {path} must contain workspace-relative paths; "
            f"refusing entries that escape the workspace root: {escaping}"
        )
    return values


def _committed_reference() -> Path:
    # <skill>/scripts/_binding.py → parents[2] == the skills home → _okf/…
    return Path(__file__).resolve().parents[2] / "_okf" / "binding.reference.toml"


def _discover(start: Path) -> Path | None:
    for candidate_root in (start, *start.parents):
        candidate = candidate_root / ".okf" / "binding.toml"
        if candidate.is_file():
            return candidate
    reference = _committed_reference()
    if reference.is_file():
        return reference
    return None


def resolve_binding(explicit: str | None, start: Path) -> tuple[Path, dict]:
    """Return ``(binding_path, parsed_dict)`` per the resolution order.

    Raises ``BindingNotFoundError`` when nothing resolves and
    ``BindingParseError`` (naming the file) on invalid TOML.
    """
    path = Path(explicit) if explicit else _discover(start.resolve())
    if path is None:
        raise BindingNotFoundError(
            "no OKF binding found: pass --binding PATH, or create .okf/binding.toml "
            "at the workspace root — see the skill's FIRST_RUN.md for the "
            "inspect->propose->confirm->persist flow. Refusing to lint a guessed "
            "bundle set."
        )
    if not path.is_file():
        raise BindingNotFoundError(f"binding file does not exist: {path}")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise BindingParseError(f"malformed binding TOML at {path}: {exc}") from exc
    return path, data
