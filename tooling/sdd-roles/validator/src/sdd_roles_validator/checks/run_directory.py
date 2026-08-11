"""Run-directory cluster — the item-2 suite live (spec sdd-roles-orchestrator,
C2 two-tree model): CHK-CHAIN, CHK-TREE, CHK-WRITER, CHK-GENESIS,
CHK-GATE-BIND, CHK-SCOPE, CHK-REWORK, plus the item-2 halves of CHK-DECISIONS
and CHK-THRESH.

All checks are vacuous when the target carries no ledger (pure artifact case
dirs) — they lint runs, not shapes. writes[] rows are partitioned exactly:
rows touching the tracked artifact map belong to CHK-TREE; rows touching
workspace paths belong to CHK-SCOPE. Neither judges the other's rows.
"""

from __future__ import annotations

import json

from ..scopes import (
    HARD_PROTECTED_KEYS,
    hard_patterns,
    match_any as _match_any,
    tests_patterns,
    write_tags,
)
from ..ledger_model import (
    EMPTY_TREE,
    artifacts_map,
    delta_findings,
    entry_maps,
    final_line_digest,
    rework_edges,
    tree_digest_of_map,
    verify_chain,
)

Finding = tuple[str, str, str]


def _data(art) -> dict:
    return art.data if isinstance(art.data, dict) else {}


def _genesis(entries) -> dict | None:
    if entries and _data(entries[0]).get("seq") == 0:
        return _data(entries[0])
    return None


def _parent_of(ctx, genesis: dict):
    """Locate the parent ledger (by run_id) among the target's ledgers."""
    parent = genesis.get("parent_run")
    if not isinstance(parent, dict):
        return None, None
    for name, entries in ctx.ledgers:
        g = _genesis(entries)
        if g is not None and g.get("run_id") == parent.get("run_id"):
            return name, entries
    return None, None


def _seed_map(ctx, entries) -> tuple[dict[str, str] | None, bool]:
    """Genesis tracked-artifact seed: empty for fresh runs, the parent's final
    map under parent_run (unknowable when the parent ledger is absent)."""
    genesis = _genesis(entries)
    if genesis is None:
        return {}, True
    if genesis.get("parent_run") is None:
        return {}, True
    _, parent_entries = _parent_of(ctx, genesis)
    if parent_entries is None:
        return None, False
    return artifacts_map(_data(parent_entries[-1])), True


def chk_chain(ctx) -> list[Finding]:
    findings: list[Finding] = []
    for _name, entries in ctx.ledgers:
        for idx, reason in verify_chain(entries):
            pointer = "/prev_entry_digest" if "prev_entry_digest" in reason else "/seq"
            findings.append((entries[idx].label, pointer, reason))
    return findings


def chk_tree(ctx) -> list[Finding]:
    findings: list[Finding] = []
    for _name, entries in ctx.ledgers:
        seed, seed_known = _seed_map(ctx, entries)
        maps = entry_maps(entries, seed or {})
        for i, art in enumerate(entries):
            data = _data(art)
            if art.parse_error or not data:
                continue
            if i == 0:
                if data.get("seq") != 0:
                    continue
                if seed_known and data.get("tree_digest") != tree_digest_of_map(seed or {}):
                    findings.append(
                        (
                            art.label,
                            "/tree_digest",
                            "genesis tree_digest does not match its starting artifact map",
                        )
                    )
                continue
            if data.get("artifacts") is None:
                continue
            recorded = data.get("tree_digest")
            if recorded != tree_digest_of_map(maps[i]):
                findings.append(
                    (
                        art.label,
                        "/tree_digest",
                        "tree_digest does not match the entry's artifact map",
                    )
                )
            if i >= 1 and (i > 1 or seed_known):
                for problem in delta_findings(maps[i - 1], maps[i], data.get("writes") or []):
                    findings.append((art.label, "/writes", problem))
    return findings


def chk_writer(ctx) -> list[Finding]:
    declared = (ctx.config or {}).get("gate_runner")
    if not declared:
        return []
    findings: list[Finding] = []
    for _name, entries in ctx.ledgers:
        for art in entries:
            data = _data(art)
            if data and data.get("writer") != declared:
                findings.append(
                    (
                        art.label,
                        "/writer",
                        "writer is not the KernelConfig-declared gate-runner",
                    )
                )
    return findings


def chk_genesis(ctx) -> list[Finding]:
    findings: list[Finding] = []
    for name, entries in ctx.ledgers:
        genesis = _genesis(entries)
        if genesis is None:
            continue
        label = entries[0].label
        for field, active in (
            ("kernel_config_digest", ctx.config_digest),
            ("role_registry_digest", ctx.registry_digest),
        ):
            pinned = genesis.get(field)
            if not pinned:
                findings.append((label, f"/{field}", f"genesis omits {field}"))
            elif active and pinned != active:
                findings.append(
                    (label, f"/{field}", f"genesis {field} does not match the active file digest")
                )
        if genesis.get("parent_run") is None:
            start = genesis.get("tree_digest")
            if start and start != EMPTY_TREE:
                for other_name, other_entries in ctx.ledgers:
                    if other_name == name:
                        continue
                    if any(_data(e).get("tree_digest") == start for e in other_entries):
                        findings.append(
                            (
                                label,
                                "/parent_run",
                                "orphan chain: starting tree continues another ledger's "
                                "recorded state without parent_run",
                            )
                        )
                        break
        else:
            parent_name, parent_entries = _parent_of(ctx, genesis)
            if parent_entries is not None:
                declared = (genesis.get("parent_run") or {}).get("final_entry_digest")
                actual = final_line_digest(parent_entries)
                if declared != actual:
                    findings.append(
                        (
                            label,
                            "/parent_run/final_entry_digest",
                            "parent_run final_entry_digest does not match the parent ledger",
                        )
                    )
                parent_last: dict[str, int] = {}
                for key, rw in rework_edges(parent_entries):
                    if isinstance(rw.get("count"), int):
                        parent_last[key] = rw["count"]
                seen: set[str] = set()
                for key, rw in rework_edges(entries):
                    if key in seen or key not in parent_last:
                        continue
                    seen.add(key)
                    if rw.get("count") != parent_last[key] + 1:
                        findings.append(
                            (
                                label,
                                "/parent_run",
                                f"rework counter for edge '{key}' not carried across "
                                f"parent_run (parent ended at {parent_last[key]})",
                            )
                        )
    return findings


def _iter_outcomes(ctx):
    for art in ctx.artifacts:
        if art.parse_error:
            continue
        if art.atype == "gate_outcome":
            yield art, "", art.data
        elif art.atype == "handoff_contract":
            for i, go in enumerate(art.data.get("gate_outcomes") or []):
                if isinstance(go, dict):
                    yield art, f"/gate_outcomes/{i}", go


def chk_gate_bind(ctx) -> list[Finding]:
    if not ctx.ledgers:
        return []
    declared = (ctx.config or {}).get("gate_runner")
    findings: list[Finding] = []
    for art, base, outcome in _iter_outcomes(ctx):
        gate_id = outcome.get("gate_id")
        ref = outcome.get("report_ref") if isinstance(outcome.get("report_ref"), dict) else {}
        bound = False
        for _name, entries in ctx.ledgers:
            for entry_art in entries:
                e = _data(entry_art)
                if e.get("event") not in ("gate_run", "passed"):
                    continue
                if declared and e.get("writer") != declared:
                    continue
                if gate_id not in (e.get("gates") or []):
                    continue
                if e.get("input_tree_digest") != outcome.get("input_tree_digest"):
                    continue
                arts = artifacts_map(e)
                if arts.get(str(ref.get("path", ""))) != ref.get("sha256"):
                    continue
                bound = True
                break
            if bound:
                break
        if not bound:
            findings.append(
                (
                    art.label,
                    base or "/report_ref",
                    "gate outcome cannot be bound to a gate-runner ledger entry "
                    "(gate id + report digest + input tree must all match)",
                )
            )
    return findings


def chk_scope(ctx) -> list[Finding]:
    if not ctx.ledgers:
        return []
    config = ctx.config or {}
    hard = hard_patterns(config)
    tests = tests_patterns(config)
    roles = {
        r.get("id"): r
        for r in ((ctx.registry_data or {}).get("roles") or [])
        if isinstance(r, dict)
    }
    findings: list[Finding] = []
    for _name, entries in ctx.ledgers:
        seed, _known = _seed_map(ctx, entries)
        maps = entry_maps(entries, seed or {})
        history: dict[str, str | None] = {}
        for i, art in enumerate(entries):
            data = _data(art)
            if i == 0 or not data:
                continue
            writes = data.get("writes") or []
            if not writes:
                continue
            tracked = set(maps[i - 1]) | set(maps[i])
            role = roles.get(data.get("role"))
            for j, w in enumerate(writes):
                if not isinstance(w, dict):
                    continue
                path = str(w.get("path") or "")
                if path in tracked:
                    continue  # tracked-artifact rows are CHK-TREE's domain
                ptr = f"/writes/{j}"
                if role is None:
                    findings.append(
                        (art.label, ptr, "role not in registry; write scopes unresolvable")
                    )
                    continue
                change = w.get("change")
                messages = {
                    "protected": "write inside the protected set",
                    "outside_scope": "write outside the role's write scopes",
                    "maker_tests": "maker-role write modifies or deletes under tests globs",
                }
                for tag in write_tags(path, change, role, hard, tests):
                    findings.append((art.label, ptr, messages[tag]))
                known = history.get(path, "__unknown__")
                if change == "added":
                    if known not in ("__unknown__", None):
                        findings.append(
                            (art.label, ptr, "added write contradicts recorded history")
                        )
                elif change in ("modified", "deleted") and known != "__unknown__":
                    if known is None or w.get("sha256_before") != known:
                        findings.append(
                            (art.label, ptr, "sha256_before contradicts recorded history")
                        )
                history[path] = None if change == "deleted" else w.get("sha256_after")
    return findings


def chk_rework(ctx) -> list[Finding]:
    findings: list[Finding] = []
    config_max = ((ctx.config or {}).get("rework") or {}).get("max")
    for _name, entries in ctx.ledgers:
        last: dict[str, int] = {}
        for art in entries:
            data = _data(art)
            rw = data.get("rework")
            if not isinstance(rw, dict):
                continue
            key = f"{rw.get('target_role')}::{rw.get('from_stage')}"
            count = rw.get("count")
            bound = config_max if isinstance(config_max, int) else rw.get("max")
            if isinstance(count, int) and isinstance(bound, int) and count > bound:
                findings.append(
                    (
                        art.label,
                        "/rework/count",
                        f"rework count {count} exceeds the bound {bound}",
                    )
                )
            if isinstance(count, int):
                prev = last.get(key)
                if prev is not None and count != prev + 1:
                    findings.append(
                        (
                            art.label,
                            "/rework/count",
                            f"rework count {count} does not continue {prev} for edge '{key}'",
                        )
                    )
                last[key] = count
    return findings


def chk_decisions_item2(ctx) -> list[Finding]:
    handoffs = [
        a for a in ctx.artifacts if a.atype == "handoff_contract" and not a.parse_error
    ]
    if len(handoffs) < 2:
        return []
    findings: list[Finding] = []
    seen: dict[str, tuple[str, str]] = {}
    for art in handoffs:
        for i, d in enumerate(art.data.get("decisions") or []):
            if not isinstance(d, dict):
                continue
            key = json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            ptr = f"/decisions/{i}"
            first = seen.get(key)
            if first is None:
                seen[key] = (art.label, ptr)
            elif first[0] != art.label:
                findings.append(
                    (
                        art.label,
                        ptr,
                        f"byte-identical decision item recurs across handoffs "
                        f"(first at {first[0]}{first[1]})",
                    )
                )
    return findings


def chk_thresh_item2(ctx) -> list[Finding]:
    if not ctx.ledgers or not ctx.config_digest:
        return []
    unanchored = False
    for _name, entries in ctx.ledgers:
        genesis = _genesis(entries)
        if genesis is None:
            continue
        pinned = genesis.get("kernel_config_digest")
        if pinned and pinned != ctx.config_digest:
            unanchored = True
            break
    if not unanchored:
        return []
    findings: list[Finding] = []
    for art, base, outcome in _iter_outcomes(ctx):
        if "threshold" in outcome:
            findings.append(
                (
                    art.label,
                    f"{base}/threshold",
                    "threshold resolution unanchored: genesis config pin does not "
                    "match the active config digest",
                )
            )
    return findings
