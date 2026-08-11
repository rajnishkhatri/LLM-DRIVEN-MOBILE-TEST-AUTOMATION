---
type: runbook
title: Coding-rules — deferred for this design workspace
description: >-
  Thin workspace pointer: coding-rules is not mounted in
  LLM-DRIVEN-MOBILE-TEST-AUTOMATION; install into the spine/o1 Java delivery
  repo when that repo exists.
tags: [coding-rules, deferred, instructions]
---

# Coding-rules — instructions for this workspace

**Not mounted here.** This design repo holds the installable bundle and
catalog references; it does **not** install coding-rules into Cursor or Claude
Code for day-to-day work.

| Need | Doc |
|---|---|
| Clone / skill family map | [../SETUP.md](../SETUP.md) §7 |
| Install into spine/o1 | [coding-rules-skill/INSTALL.md](coding-rules-skill/INSTALL.md) or `tooling/coding-rules-skill/INSTALL.md` |
| Bundle SoT | `tooling/coding-rules-skill/` |
| SDD / roles context | [sdd-usage-guide.md](sdd-usage-guide.md) |

---

## Why deferred

coding-rules (CR-01…CR-18 + ArchUnit seeds) targets the **spine/o1 Java
delivery repo**: `base_package`, module dirs, seam globs, and CI enforcement.
Those binding keys have no analog in this markdown/design workspace. Mounting
the skill here would either ask forever for unresolved placeholders or invent
Java layout that does not exist.

skill-sync may mirror catalog files under `tooling/coding-rules-skill/dist/` —
that is a **catalog mirror**, not an agent skill mount.

---

## When the delivery repo exists

1. Follow `tooling/coding-rules-skill/INSTALL.md` (catalog → binding → Claude →
   Cursor → Copilot condensed list → CI seeds).
2. Resolve **every** `[coding-rules]` placeholder in that repo’s
   `.sdd/binding.toml` before expecting useful answers.
3. Pair with the **coder** role / `sdd-implement` there — not in this repo.

---

## What to do in *this* repo instead

- Specs / plans: [sdd-lifecycle-instructions.md](sdd-lifecycle-instructions.md)
- Architecture decisions: [arch-lifecycle-instructions.md](arch-lifecycle-instructions.md)
- Case write-ups under OKF: [okf-curator-instructions.md](okf-curator-instructions.md)
  (`cases/coding-rules` is a declared OKF bundle for *documentation about*
  rules, not the runtime skill)

---

## Smoke / anti-smoke

Do **not** run install steps that copy coding-rules into
`.cursor/skills/coding-rules/` or `.claude/skills/coding-rules/` in this repo.

Optional read-only check that the bundle is present:

```bash
test -f tooling/coding-rules-skill/INSTALL.md && test -f tooling/coding-rules-skill/references/rules-catalog.md && echo "coding-rules bundle present (not mounted)"
```
