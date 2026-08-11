# coding-rules-skill — o1 pipeline coding rules bundle

A portable skill that gives coding agents (Claude, Cursor, GitHub Copilot)
the o1 pipeline's coding rules: 18 decidable rules with trade-off
justifications, patterns/anti-patterns, and enforcement channels, extracted
from `cases/coding-rules/` (Clean Architecture chapters + code metrics) and
specialized to the `mobile-test-automation` ADRs
(`docs/architecture/adrs/application/mobile-test-automation/`).

**Design: one canonical catalog, three thin front-ends.** Rule content lives
only in `references/rules-catalog.md`. The agent front-ends are pointers;
if you find rule text drifting into a front-end, that's a bug.

```
tooling/coding-rules-skill/
  references/
    rules-catalog.md          ← THE rules (CR-01..CR-18) + override table
    archunit-seeds.md         ← CI enforcement for the mechanical subset
    binding.template.toml     ← workspace placeholders ({{base_package}}, seams…)
  claude/skills/coding-rules/SKILL.md    ← Claude Code front-end
  cursor/skills/coding-rules/SKILL.md    ← Cursor front-end
  copilot/
    instructions/coding-rules.instructions.md  ← path-scoped Copilot instructions
    AGENTS-fragment.md                          ← paste-in AGENTS.md section
```

## Install into the o1 Java workspace

**Full step-by-step guide with binding checklist, CI wiring, verification
smoke sequence, and troubleshooting: [INSTALL.md](INSTALL.md).** The short
version:

1. **Canonical content (once):** copy `references/rules-catalog.md` and
   `references/archunit-seeds.md` to `docs/coding-rules/` in the target
   repo. Add `[coding-rules]` keys from `binding.template.toml` to the
   repo's `.sdd/binding.toml` and resolve every placeholder
   (`base_package`, seam globs, module names).
2. **Claude:** copy `claude/skills/coding-rules/` → `.claude/skills/coding-rules/`.
3. **Cursor:** copy `cursor/skills/coding-rules/` → `.cursor/skills/coding-rules/`.
4. **Copilot:** copy `copilot/instructions/coding-rules.instructions.md` →
   `.github/instructions/`; merge `copilot/AGENTS-fragment.md` into the
   repo's `AGENTS.md`. (The Copilot instructions file carries a condensed
   rule list because Copilot injects it as always-on context — when the
   catalog changes, regenerate the condensed list from it.)
5. **CI:** create the architecture-test module from `archunit-seeds.md`;
   tighten package globs on first run. F1/F2/F4 are load-bearing — wire them
   CI-blocking from day one (ADR 0001/0006 make their suppression an
   ADR-level event).

## Relationship to the other skill families

- **sdd-implement (Stage 6):** consult the catalog before writing code; the
  rules constrain the shape of green code. (Future integration: add a
  one-line pointer in the sdd bundle's binding/reference — deliberately not
  done yet; this bundle stands alone until the sdd integration is decided.)
- **code-review / sdd-converge (Stages 7/9–10):** findings cite rule IDs so
  gaps classify mechanically; CR-18 trends feed the converge report.
- **arch-\* family:** arch-validate's governance table inventories the
  ArchUnit seeds as fitness functions; arch-components review mode can cite
  CR-01..04 for structural findings. New rules flow *from* ADR Compliance
  sections *into* the catalog — never invented per-diff.

## Maintenance rules

- Hard cap 18: adding a rule means removing/merging one, or justifying a cap
  raise in the PR that does it.
- Threshold changes (CR-18) and new async seams / crossing types (CR-15/06)
  are ADR-level decisions, not catalog edits.
- The catalog cites source chapters by filename (`cases/coding-rules/*.md`
  in the Architect workspace); if that corpus moves, update the catalog
  header, not the rules.
