# Stage ledger directory

Append-only NDJSON ledgers, one file per run: `<run-id>.ndjson`.

Written **only** by the deterministic gate-runner (`gate-runner`, build item 2
— the `writer` principal declared in the KernelConfig) — never by any role.
Live write-blocking arrives at build item 3; since item 2 the run-directory
check suite (CHK-CHAIN/TREE/WRITER/GENESIS/GATE-BIND/SCOPE/REWORK) lints every
ledger structurally: chains over raw line bytes, genesis pinning against the
run's own config/registry copies, artifact-map tree digests, write scopes, and
rework bounds. This directory is a member of the KernelConfig's mandatory
protected set.

A run's ledger lives in its run directory during execution; this directory is
the workspace-level home for runs executed against this repository.
