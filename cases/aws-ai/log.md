---
type: log
title: 'AWS AI agents — bundle log'
---

# AWS AI agents — bundle log

Chronological history, newest first (ISO-8601).

- 2026-08-27 — **Recorded the two-book provenance seam** (surfaced by the aws-ai architect-explainer brainstorm audit, [brainstorm](../../docs/research/aws-ai-architect-explainer-brainstorm.md)): ch01–ch07 derive from Packt "AI Agents on AWS" (Strands/AgentCore stack, `github.com/PacktPublishing/AI-Agents-on-AWS`, Figure N.N numbering); ch08–ch10 derive from "Using Amazon Bedrock" (`github.com/renaldig/Using-Amazon-Bedrock`, console-first, Figure N-N numbering). The seam is load-bearing: ch08's agent-security guidance targets classic managed Bedrock Agents (`create_agent` action groups — a product generation now in maintenance mode as "Bedrock Agents Classic", closed to new customers 2026-07-30), not the AgentCore stack of ch01–07; do not present the two halves as one coherent stack without translation. Known content flags, left as-is (no rewrites): ch09's `invoke_claude` helper sends a legacy Text-Completions body (`Human:/Assistant:`, `max_tokens_to_sample`) to a Claude Sonnet 4 model id — invalid on Bedrock (Claude 3+ requires the Messages API) — and its Knowledge Base console walkthrough predates the real data-source + vector-store + sync flow; ch10's `amazon.titan-tg1-large`, Redshift `dc2.large`, and "Claude 3.5 Sonnet" references are legacy-era.
- 2026-08-12 — Promoted chapter notes to an OKF bundle (typed frontmatter, zero-padded names, catalog). Convention in [CONVENTIONS.md](../../docs/CONVENTIONS.md); linted by `python .cursor/skills/okf-curator/scripts/okf_lint.py`.
