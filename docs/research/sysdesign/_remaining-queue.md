---
type: analysis
title: Remaining topic queue (supervisor)
description: Post-wave-3 queue. All 41 assigned ids landed; nothing left to launch.
tags: [system-design-patterns, supervisor]
---

# Remaining launch queue

The original remaining-queue is **empty**. All 41 assigned ids exist on disk as `docs/research/sysdesign/*-external-research.md` after wave 3 closed.

Launched and landed:

| Wave | Count | Topics |
|---|---|---|
| 1 | 16 | A1–A6, D1–D5, C7, B1–B4 |
| 2 | 16 | B5–B8, C3–C6, C8–C11, E1–E4 |
| 3 | 9 | E5–E13 |

**Still missing — relaunch:** none. No wave-1 (or later) id failed to land.

**Thin follow-ups:** none. File measurement: every note is ≥150 lines and has the eight required sections. Shortest that still clears the bar is E6 (231 lines) — not a relaunch.

C1/C2 remain skipped (already Concepts). No further research-agent launches in this one-shot run.
