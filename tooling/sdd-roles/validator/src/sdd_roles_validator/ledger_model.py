"""The ledger-chain formulas as functions — the ONE source both the
run-directory checks and the gate-runner consume (plan §1: runner-vs-checks
drift is structurally impossible because neither owns a private copy).

Definitions realized here are normative per kernel/docs/ledger-chain.md
(as amended by the item-2 spec C2 two-tree model):
- entry chain: prev_entry_digest = sha256 of the preceding raw line bytes;
- tree_digest: digest over the entry's artifacts[] map (run-directory tracked
  artifacts), one `<posix-path> NUL <sha256> LF` line per artifact, bytewise-
  sorted by path; the empty map digests the empty string;
- input_tree_digest: the workspace tree at gate time (same formula over the
  workspace file map) — a different tree, recorded on gate events;
- genesis anchoring: kernel_config_digest / role_registry_digest = sha256 of
  the active config/registry file bytes.
"""

from __future__ import annotations

import hashlib
from typing import Iterable

EMPTY_TREE = hashlib.sha256(b"").hexdigest()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tree_digest_of_map(tree: dict[str, str]) -> str:
    blob = b"".join(
        path.encode("utf-8") + b"\x00" + digest.encode("utf-8") + b"\n"
        for path, digest in sorted(tree.items())
    )
    return sha256_hex(blob)


def artifacts_map(entry: dict) -> dict[str, str]:
    """The tracked-artifact map an entry declares (artifacts[] snapshot)."""
    out: dict[str, str] = {}
    for a in entry.get("artifacts") or []:
        if isinstance(a, dict) and isinstance(a.get("path"), str):
            out[a["path"]] = str(a.get("sha256", ""))
    return out


def verify_chain(entries: list) -> list[tuple[int, str]]:
    """Chain findings over one ledger's ordered Artifact list: (index, reason).
    Uses raw line bytes; parse errors are CHK-SCHEMA's domain and are skipped
    here except where they break the byte chain (raw is always present)."""
    findings: list[tuple[int, str]] = []
    for i, art in enumerate(entries):
        data = art.data if isinstance(art.data, dict) else {}
        seq = data.get("seq")
        if i == 0:
            if seq != 0:
                findings.append((i, "ledger does not start at a genesis entry (seq 0)"))
            elif data.get("prev_entry_digest") is not None:
                findings.append((i, "genesis prev_entry_digest is not null"))
            continue
        if seq != i:
            findings.append((i, f"seq {seq} breaks the strict 0..N sequence at position {i}"))
        want = sha256_hex(entries[i - 1].raw or b"")
        if data.get("prev_entry_digest") != want:
            findings.append((i, "prev_entry_digest does not match the preceding raw line bytes"))
    return findings


def entry_maps(entries: list, seed: dict[str, str] | None = None) -> list[dict[str, str]]:
    """Per-entry tracked-artifact maps: genesis map = seed (empty for fresh
    runs, the parent's final map under parent_run), then each regular entry's
    own artifacts[] snapshot."""
    maps: list[dict[str, str]] = []
    for i, art in enumerate(entries):
        data = art.data if isinstance(art.data, dict) else {}
        if i == 0:
            maps.append(dict(seed or {}))
        else:
            maps.append(artifacts_map(data))
    return maps


def delta_findings(prev_map: dict[str, str], cur_map: dict[str, str], writes: Iterable[dict]) -> list[str]:
    """Arm (ii) of CHK-TREE: the tracked-map delta must be exactly covered by
    the entry's writes[] rows (with history-true change kinds and hashes);
    writes to paths outside both maps are workspace writes — not judged here."""
    problems: list[str] = []
    write_rows = {w.get("path"): w for w in writes if isinstance(w, dict)}
    tracked = set(prev_map) | set(cur_map)
    for path in sorted(set(cur_map) - set(prev_map)):
        w = write_rows.get(path)
        if w is None:
            problems.append(f"tracked artifact '{path}' appears with no covering write")
        elif w.get("change") != "added" or w.get("sha256_after") != cur_map[path]:
            problems.append(f"write for added artifact '{path}' contradicts the map")
        elif w.get("sha256_before") is not None:
            problems.append(f"added artifact '{path}' claims a prior hash")
    for path in sorted(set(prev_map) - set(cur_map)):
        w = write_rows.get(path)
        if w is None:
            problems.append(f"tracked artifact '{path}' vanishes with no covering delete")
        elif w.get("change") != "deleted" or w.get("sha256_before") != prev_map[path]:
            problems.append(f"delete of artifact '{path}' contradicts recorded history")
    for path in sorted(set(cur_map) & set(prev_map)):
        if cur_map[path] != prev_map[path]:
            w = write_rows.get(path)
            if w is None:
                problems.append(f"tracked artifact '{path}' changes with no covering write")
            elif (
                w.get("change") != "modified"
                or w.get("sha256_before") != prev_map[path]
                or w.get("sha256_after") != cur_map[path]
            ):
                problems.append(f"modify of artifact '{path}' contradicts recorded history")
    for path, w in sorted(write_rows.items()):
        if path in tracked:
            change = w.get("change")
            if change == "added" and path in prev_map:
                problems.append(f"write claims to add already-tracked artifact '{path}'")
            if change in ("modified", "deleted") and path not in prev_map:
                problems.append(f"write claims to {change} untracked artifact '{path}'")
    return problems


def final_line_digest(entries: list) -> str | None:
    if not entries or entries[-1].raw is None:
        return None
    return sha256_hex(entries[-1].raw)


def rework_edges(entries: list) -> list[tuple[str, dict]]:
    """Ordered (edge_key, rework_obj) pairs over one ledger."""
    out: list[tuple[str, dict]] = []
    for art in entries:
        data = art.data if isinstance(art.data, dict) else {}
        rw = data.get("rework")
        if isinstance(rw, dict):
            key = f"{rw.get('target_role')}::{rw.get('from_stage')}"
            out.append((key, rw))
    return out
