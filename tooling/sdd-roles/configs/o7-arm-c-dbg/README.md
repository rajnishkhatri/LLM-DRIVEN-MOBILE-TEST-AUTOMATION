# o7 KernelConfig — arm `C-dbg` (ablation)

Study equipment, not a second source of truth. `kernel-config.json` here is a
**byte-copy of [`../o7/kernel-config.json`](../o7/kernel-config.json) with the
single `"arm"` field changed to `"C-dbg"`** — nothing else differs, and
`speckit-mapping.json` is the identical sibling (sha256
`162cb24b2831c3cb3620880ec0763c2eff171abbda46099840a4f4b2a4f308ed`). The
runner copies both into the run dir at genesis, so each run stays
self-contained.

Role sequence resolved from the registry's `arms[]`: specifier → architect → coder → cleaner → hardener (5 roles, diagnostic-debug ablation).

The gate rows are unchanged because every arm's gate union is identical — that
is why only the one field moves. Read [`../o7/README.md`](../o7/README.md) for
the invocation, the token map, and the workspace layout; all of it applies here
verbatim except `--config configs/o7-arm-c-dbg/kernel-config.json`.

**To re-derive** (per item P1 of the kata study execution plan): copy
`configs/o7/kernel-config.json`, change the one line, and confirm
`diff` reports exactly one changed line. Verified 2026-08-09:
`contract-lint validate configs/o7-arm-c-dbg --kernel kernel` → exit 0, 29/0;
dry `Runner` construction resolves the sequence above.
