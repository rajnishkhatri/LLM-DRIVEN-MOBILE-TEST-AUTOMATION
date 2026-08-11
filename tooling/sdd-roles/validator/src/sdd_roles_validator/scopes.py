"""Shared write-scope rule core (item-3 spec S5): one rule source, two
enforcement times. `checks/run_directory.chk_scope` (retro, history-resolved)
and the `write-guard` CLI (live, disk-resolved) both evaluate writes through
these functions, so the mechanical rule cannot drift between them.

Pattern semantics are fixed: exact match, `dir/` prefix, or fnmatch glob.
"""

from __future__ import annotations

import fnmatch

HARD_PROTECTED_KEYS = (
    "kernel_config",
    "role_registry",
    "ledger_dir",
    "gate_configs",
    "harness_enablement",
    "speckit_constitution",
)


def match_any(path: str, patterns) -> bool:
    for pat in patterns or []:
        if not isinstance(pat, str) or not pat:
            continue
        if path == pat or (pat.endswith("/") and path.startswith(pat)):
            return True
        if any(ch in pat for ch in "*?[") and fnmatch.fnmatch(path, pat):
            return True
    return False


def hard_patterns(config) -> list[str]:
    protected = (config or {}).get("protected") or {}
    hard: list[str] = []
    for key in HARD_PROTECTED_KEYS:
        hard.extend(protected.get(key) or [])
    return hard


def tests_patterns(config) -> list[str]:
    return ((config or {}).get("protected") or {}).get("tests_globs") or []


def write_tags(path: str, change, role, hard, tests) -> list[str]:
    """Ordered violation tags for one write: 'protected', 'outside_scope',
    'maker_tests'. An `added` write under tests_globs is exempt from the
    scope arm (the mechanical diff-aware rule: any role may add tests).
    """
    tags: list[str] = []
    in_tests = match_any(path, tests)
    if match_any(path, hard):
        tags.append("protected")
    if change == "added" and in_tests:
        pass
    elif not match_any(path, (role or {}).get("write_scopes")):
        tags.append("outside_scope")
    if (role or {}).get("tag") == "maker" and in_tests and change in ("modified", "deleted"):
        tags.append("maker_tests")
    return tags
