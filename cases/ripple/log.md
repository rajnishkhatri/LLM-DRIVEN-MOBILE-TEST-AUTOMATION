---
type: log
title: 'Ripple interview — bundle log'
---

# Ripple interview — bundle log

Chronological history, newest first (ISO-8601).

- **2026-10-03** — Replaced [ari-v2-breakdown.md](ari-v2-breakdown.md). The
  previous draft (its own app.py, Redis, per-session dollar figures,
  tickets created on the first turn) is retired. The concept is now the
  v2 implementation design: SCQA, functional / non-functional / out-of-scope
  partition, three pillars grounded in the running demo and ADR 0001–0003,
  and the eight-step build sequence. No code or ADR edits in this pass.
- **2026-10-02** — Added [panel-answer-anchors.md](panel-answer-anchors.md):
  pyramid answer anchors for the full scripted panel (17 questions + 4
  pressure probes). Running the script's Q14 trap query live exposed two
  new warts — greedy Tier-A `h-how-do` decisively routes mixed-intent
  questions, and the HOWTO no-match path returns an empty answer at
  confidence 1.0 with no sources — both added to the code-tour card's
  warts list (now seven).
- **2026-10-02** — Added [code-tour-talk-track.md](code-tour-talk-track.md),
  captured from the module-by-module code rehearsal (all modules hand-driven
  at the terminal, gates run live, 22 interviewer Q&As answered and
  compressed — the 22nd, on test-case selection and rejection, added in
  the same session). Companion to the eval-layer track.
- **2026-09-30** — Added [eval-layer-talk-track.md](eval-layer-talk-track.md),
  captured from the eval-spec working session (golden set + taxonomy + gates
  walkthrough). Promoted `cases/ripple` to a declared OKF bundle: index + log
  created, typed frontmatter added to the pre-existing influence cards,
  binding updated.
- **(earlier)** — [ripple-influence-round-cards.md](ripple-influence-round-cards.md)
  authored before the bundle existed.
