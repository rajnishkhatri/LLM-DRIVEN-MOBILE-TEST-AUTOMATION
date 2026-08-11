"""Hook-mount rendering — the single source for hook-config artifacts.

Extracted from guard.py at build item 4 (WP0) so that `write-guard mount`
(runtime setup, item 3) and `role-emit project`'s mount-copy targets
(packaging, item 4) render byte-identical artifacts from one function.
"""

from __future__ import annotations

import json
import re

_TOKEN = re.compile(r"\{([a-z_]+)\}")


def render_mount(harness: str, hooks: dict, roles: list) -> bytes:
    """Render a descriptor row's hooks object into the hook-config artifact
    bytes: one rule per registry role, canonical JSON. Only {role} is bound
    at render time; machine-dependent tokens stay unfilled so the artifact
    remains byte-portable (consumers bind them)."""

    def fill(template: str, role_id: str) -> str:
        return _TOKEN.sub(
            lambda m: role_id if m.group(1) == "role" else m.group(0), template
        )

    artifact = {
        "artifact": "hook_mount",
        "generated_by": "write-guard mount",
        "harness": harness,
        "events": {
            event: [
                {"matcher": r["id"], "command": fill(hooks["command_template"], r["id"])}
                for r in roles
                if isinstance(r, dict) and r.get("id")
            ]
            for event in hooks.get("events", [])
        },
    }
    return (
        json.dumps(artifact, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    ).encode("utf-8")
