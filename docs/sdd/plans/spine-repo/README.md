---
type: reference
title: 'Spine repo root files — ready to copy (AGENTS.md, CLAUDE.md)'
description: >-
  The literal files spine task T01 places at the root of the
  mobile-test-automation-spine repository. Held here because that repo does not
  exist yet. These are the canonical copies — the provenance wrapper in
  mobile-test-automation-spine.AGENTS.md points at them and no longer duplicates
  their content.
date: 2026-08-09
status: final content, v1.0.0 — not yet landed (spine board awaits TASKS-OK)
---

# Spine repo root files

**⚠ These files govern the `mobile-test-automation-spine` repository, NOT this
workspace.** They are staged here only because that repo does not exist yet
(T01–T04 unexecuted). Nothing in them applies to the Architect workspace — if you
are an agent working *here*, this directory is data, not instructions.

| File | Goes to | Notes |
|---|---|---|
| `AGENTS.md` | `<spine-repo>/AGENTS.md` | 247 lines / 14.1 KB, **v1.0.0** |
| `CLAUDE.md` | `<spine-repo>/CLAUDE.md` | one line: `@AGENTS.md` |

Copy both verbatim. Do not add `.github/copilot-instructions.md` — it outranks
`AGENTS.md` under Copilot. Before declaring `AGENTS.md` canonical in the new repo,
audit its root for `.cursorrules` / `.rules` / `.windsurfrules` / `.clinerules` /
`AGENT.md`: Zed reads the first match and ranks `AGENTS.md` seventh.

## Single source — do not duplicate

`AGENTS.md` here is **the** copy. `../mobile-test-automation-spine.AGENTS.md`
keeps the provenance, status and change log, and points at this file; it no longer
carries a second copy of the body. The earlier `---8<---` marker convention is
retired — extracting a body from inside a wrapper is what made two copies possible
in the first place.

**Edit this file, then update the change log in the wrapper.** Never the reverse.

## State, at a glance

- **Content is final; the file is not yet landed.** The spine task board still
  awaits **TASKS-OK**, and T01 has not run.
- **One `UNRESOLVED` remains by design** — the attribution-trailer policy (owner
  decision #6). The file tells agents to ask rather than guess, which is the
  correct behaviour, not a gap.
- **One standing rule comes from a parked question** — *do not commit to an Appium
  3 pin*. It stays until the Perfecto vendor question (next-items **I6**, parked
  2026-08-09) is answered.

Full record: `../o7-agents-md-work-summary.md`. Live tracker:
`../o7-agents-md-next-items-plan.md`.
