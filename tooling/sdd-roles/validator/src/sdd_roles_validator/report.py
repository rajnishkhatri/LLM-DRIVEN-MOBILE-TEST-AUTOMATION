"""Canonical, deterministic report model (plan §4).

Byte rules: sorted keys, 2-space indent, ensure_ascii, LF, trailing newline,
POSIX-relative artifact labels, no timestamps — two runs on identical input
must be byte-identical (CHK-DET).
"""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class Entry:
    check_id: str
    phase: str
    outcome: str  # pass | fail | deferred
    artifact: str
    json_pointer: str
    detail: str

    def as_dict(self) -> dict:
        return {
            "check_id": self.check_id,
            "phase": self.phase,
            "outcome": self.outcome,
            "artifact": self.artifact,
            "json_pointer": self.json_pointer,
            "detail": self.detail,
        }


def canonical_dumps(obj) -> str:
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def sort_entries(entries: list[Entry]) -> list[Entry]:
    return sorted(
        entries,
        key=lambda e: (e.check_id, e.phase, e.artifact, e.json_pointer, e.detail),
    )


def build_report(
    schema_version: str,
    validator_version: str,
    target: str,
    entries: list[Entry],
) -> dict:
    ordered = sort_entries(entries)
    summary = {
        "pass": sum(1 for e in ordered if e.outcome == "pass"),
        "fail": sum(1 for e in ordered if e.outcome == "fail"),
        "deferred": sum(1 for e in ordered if e.outcome == "deferred"),
    }
    exit_code = 2 if summary["fail"] else 0
    return {
        "schema_version": schema_version,
        "validator_version": validator_version,
        "target": target,
        "checks": [e.as_dict() for e in ordered],
        "summary": summary,
        "exit_code": exit_code,
    }
