<!-- AGENTS.md fragment — paste into the target repo's AGENTS.md (used by
     Copilot coding agent and other AGENTS.md-aware tools). Keep this block
     short; the authority is docs/coding-rules/rules-catalog.md. -->

## Coding rules (binding)

This workspace enforces 18 ADR-anchored coding rules — full catalog with
justifications, patterns, and anti-patterns:
**`docs/coding-rules/rules-catalog.md`** (rule IDs `CR-01`–`CR-18`;
ArchUnit/PMD/migration seeds in `docs/coding-rules/archunit-seeds.md`).
Precedence: ADR > catalog > generic clean-architecture advice.

Non-negotiables to know before writing any Java here:

1. **Module boundaries [CR-01]:** `conversion`, `validation-certification`,
   and `evidence` talk only through `..api..` packages.
2. **The Invoke Models seam [CR-05/06]:** all model calls go through one
   adapter; only the committed IR vocabulary crosses it. No provider SDK
   types anywhere else. This rule is load-bearing (ADR 0001) — a bypass is
   an architecture breach.
3. **Storage port [CR-07]:** evidence artifacts only via the S3 port; never
   the filesystem, never payload columns in the database.
4. **Framework-free core [CR-11]:** no Spring/JPA imports in
   `domain`/`usecase` packages; wiring happens in `@Configuration` at the
   composition root.
5. **Lineage discipline [CR-14/15]:** lineage writes are in-transaction to
   the lineage schema; async exists at exactly two decided seams (outbox +
   idempotent consumers); new queues need an ADR.
6. **LLM authority [CR-16, security]:** the model proposes; determinism
   disposes. No LLM output acts without a deterministic gate; generated code
   runs credential-isolated in a separate process.

When reviewing, tag findings with rule IDs, and verify behavior, not just
shape — a well-shaped no-op on a seam or audit path (an adapter that never
calls its client, hardcoded pinning literals, a lineage write that silently
does nothing) is a finding even when the placement is compliant. If a
`[CI]`-marked rule can be violated without a red build, report the missing
ArchUnit gate as its own finding.
