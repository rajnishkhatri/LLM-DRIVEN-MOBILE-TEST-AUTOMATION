# Stage ledger: chain, genesis, and tree digests (normative)

Ledger of record: append-only NDJSON, one file per run (`<run-id>.ndjson`),
written only by the deterministic gate-runner (`KernelConfig.gate_runner`). All
harness persistence is cache, never truth (spec S8). These rules are enforced
by the run-directory check suite (CHK-CHAIN/TREE/WRITER/GENESIS/GATE-BIND/
SCOPE/REWORK — **live since build item 2**; DEFERRED-era annotations flipped
via `expected_when_implemented`).

## Two trees (item-2 spec C2, normative amendment)

A run involves **two distinct trees**, and every digest names exactly one:

- **`tree_digest`** (every entry) — the **run-directory tracked-artifact map**:
  digest over the entry's `artifacts[]` snapshot. It starts empty (a fresh
  run's genesis digests the empty map) and grows as the run records handoffs,
  reports, and evidence. `writes[]` rows touching tracked paths must exactly
  explain successive map deltas (CHK-TREE); rows touching workspace paths are
  CHK-SCOPE's domain — the two checks partition `writes[]` exactly.
- **`input_tree_digest`** (gate events, additive since 1.1.0) — the
  **workspace tree** the gate tools consumed (same formula over the workspace
  file map, excluding the run dir, the ledger dir, and VCS internals). A
  `GateOutcome` binds to a ledger entry only when gate id, report digest in
  the entry's `artifacts[]`, writer, **and** `input_tree_digest` all match
  (CHK-GATE-BIND) — a gate run on a different tree is structurally rejectable.

The item-1 CHK table's phrase "input_tree_digest ≠ the ledger tree_digest at
that entry" is realized by this two-tree model (recorded forward here and in
the item-2 spec; the committed fixtures always encoded the artifacts-map
reading — verified byte-for-byte at item-2 grounding).

## Entry chain (CHK-CHAIN)

- `prev_entry_digest` of entry N (seq ≥ 1) = **sha256 of the exact raw UTF-8
  bytes of the preceding NDJSON line, without its trailing newline**.
- Genesis (`seq: 0`) carries `prev_entry_digest: null` — the genesis marker rule.
- Lines are compact JSON (no inner newlines); the digest is over the bytes as
  committed, not over any re-serialization.

## Genesis pinning (CHK-GENESIS)

The `seq: 0` entry pins: `kernel_config_digest` and `role_registry_digest`
(sha256 of the committed config/registry file bytes), the starting
`tree_digest`, and `parent_run: {run_id, final_entry_digest} | null`.
Config- and registry-resolved checks (CHK-THRESH's run-scoped half, CHK-WRITER)
resolve against the **genesis-pinned** digests — a mid-run config edit cannot
re-anchor them. A fresh run continuing another ledger's tree state without
`parent_run` is an orphan chain; rework counters carry across `parent_run`
links (CHK-REWORK).

## Tree digest (CHK-TREE)

`tree_digest` = sha256 over the concatenation of one line per tracked artifact,
**bytewise-sorted by path**:

```
<posix-relative-path> NUL <sha256-of-file> LF
```

(The empty tree digests the empty string.) The tracked map is the entry's
`artifacts[]` snapshot (see *Two trees* above); applying entry N's tracked
`writes[]` deltas to entry N−1's map must reproduce entry N's map and digest —
an unrecorded tracked write breaks the chain deterministically and offline.
Under `parent_run`, the genesis map seeds from the parent's final snapshot
(the same run directory continues; ledger files stay per-run).

## Field realization note

The spec's shape notation `artifacts{path: sha256}` is realized as a **closed
array of `{path, sha256}` objects** — arbitrary-key maps cannot be closed under
`additionalProperties: false` (C2), and closedness wins. Same information,
schema-enforceable form.
