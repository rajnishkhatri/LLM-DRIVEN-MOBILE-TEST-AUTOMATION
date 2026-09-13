---
type: log
title: 'AWS Claude / Bedrock — bundle log'
---

# AWS Claude / Bedrock — bundle log

Chronological history, newest first (ISO-8601).

- 2026-08-27 — **Flagged course-era claims against the mid-2026 platform** (external-research audit for the architect-explainer brainstorm, [brainstorm](../../../docs/research/aws-ai-architect-explainer-brainstorm.md); notes left as-is — the delta is the explainer's job): (1) the prefill + stop-sequence extraction pattern (taught in `bedrock-converse-api.md`, reused by `prompt-evaluation.md` and `rag.md`) returns HTTP 400 on Claude 4.6+/5-generation models — current replacements are tool-schema extraction or structured outputs; (2) manual extended-thinking `budget_tokens` (`extended-thinking-and-vision.md`) is deprecated/rejected on current models in favor of adaptive thinking + effort; (3) `mcp.md`'s transport list (stdio/HTTP/WebSockets) predates the stateless 2026-07-28 MCP spec (Streamable HTTP; Roots/Sampling/Logging deprecated); (4) `prompt-caching.md`'s flat 5-min TTL / 1024-token minimum is now per-model (512/1024/4096) with an optional 1-hour TTL and 1.25×/2×/0.1× pricing; (5) model references (Claude 3.5/3.7-era ids, `str_replace_editor` tool names, "Claude often serializes tool calls") are one-to-two generations stale. The tool loop, the MCP control split, and the eval-decides doctrine remain current.
- 2026-08-27 — Promoted aws-claude/ as a nested OKF topic bundle: split the prompt-engineering course dump into 10 Concepts (Converse API, eval, techniques, tool use, RAG, thinking/vision, caching, MCP, Claude Code, agents/computer-use). Convention in [CONVENTIONS.md](../../../docs/CONVENTIONS.md); linted by `python .cursor/skills/okf-curator/scripts/okf_lint.py`.
