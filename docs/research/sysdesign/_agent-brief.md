---
type: analysis
title: 'Sysdesign catalog research — shared agent brief'
description: Shared contract for one-shot catalog research agents. Not a topic note.
tags: [system-design-patterns, research, supervisor]
---

# Shared research-agent brief (2026-09-13)

> Closed-run artifact. Notes now live in `docs/research/sysdesign/`. Do not relaunch against a worktree.

You write **one** research note. You do **not** write a Concept. You do **not** edit `cases/SystemDesignPatterns/` except to *read* CircuitBreaker.md / RetryBackoff.md as the depth-bar example.

## Paths

- **Write notes here:** `docs/research/sysdesign/`
- Gold-standard research notes (imitate structure, not topic):
  - `docs/research/sysdesign/circuit-breaker-external-research.md`
  - `docs/research/sysdesign/retry-backoff-external-research.md`
- Gold-standard Concepts (depth bar only — do not write Concepts):
  - `cases/SystemDesignPatterns/CircuitBreaker.md`
  - `cases/SystemDesignPatterns/RetryBackoff.md`
- Catalog of record: `docs/research/sysdesign/system-design-patterns-catalog.md`

Existing `cases/` notes live in the **main repo** (many are untracked and not in this worktree). Read them from the main-repo path. Cite them; never rewrite or re-derive them.

## Frontmatter (required)

```yaml
---
type: research
title: '<Topic> — external research (2026-09-13)'
description: >-
  One-sentence evidence-pass description.
tags: [research, system-design-patterns, <id>, <slug-words>]
---
```

## Body sections (required, in order)

1. **Scope and non-goals** — what this note owns; what stays in sibling catalog ids
2. **Lineage / vocabulary** — named sources, dates
3. **Mechanics** at the **group depth bar** (do not undershoot)
4. **Verified defaults / standards** where the bar requires them (libraries, protocols, OTel, SRE) — versions + fetch dates
5. **Failure modes and when-not-to-use**
6. **Cross-links** to sibling catalog ids and existing `cases/` notes
7. **Sources** — real URLs, retrieved 2026-09-13
8. **Uncertain / left out** — unverified claims; must NOT be implied as fact

Optional operational subsections (Groups B/C): knobs, observability, tuning, worked calibration, placement.

## Rules

- External-verify with WebSearch/WebFetch. Fetch the primary page for every numeric default.
- No invented SLAs, vendor defaults, or dates.
- Language-agnostic unless citing a specific library (then give version + registry date).
- Trade-offs on every recommendation.
- Do not copy substantial copyrighted book text; cite and summarize.
- Do not write exploits or attack procedures.
- Do not start a skill family. Do not write OKF Concepts.
- Today is **2026-09-13**.
- Target length: match gold-standard research notes in *density*, not necessarily page count. A thin survey is a failure. Prefer 150–400 lines of verified substance over padding.

## Group depth bars

- **A Communication:** wire semantics, connection lifecycle, scaling limits and fan-out, failure and reconnect, proxy/LB interactions, verified defaults, when-not-to-use.
- **B Scaling / C Availability:** CircuitBreaker.md bar — mechanics and variants, knobs with verified defaults, observability, tuning, worked calibration, failure modes, sources.
- **D Reliability:** signals and semantics, golden-metric frameworks, OpenTelemetry, alerting policy, tool-neutral defaults, failure modes of monitoring itself.
- **E Styles:** what the style is and is not, typical quantum count as a FACT (do NOT run arch-style’s four determinations / scoring micro-loop), when-to-use / when-not, migration in/out, worked example, trade-off table, sources. **No library-defaults section.** Cite `.cursor/skills/arch-style/references/style-selection.md` (main or worktree).
