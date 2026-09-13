---
type: guide
title: 'Extended thinking and vision'
description: 'Extended thinking is eval-gated and billed as tokens. Vision needs the same prompt discipline as text — step-by-step and few-shot beat a one-line caption.'
tags: [claude, bedrock, aws-claude, capabilities]
---

# Extended thinking and vision

Two Converse capabilities that are easy to turn on and expensive to use badly.

## Extended thinking

Claude can reason in a separate thinking block before the user-visible answer. The response contains a reasoning content part (thinking text plus a cryptographic signature that prevents tampering) and a text part. Safety systems may **redact** thinking into encrypted content; applications must handle that block.

Trade-offs: higher accuracy on hard tasks; you pay for thinking tokens; latency goes up.

When to enable: run [prompt evals](prompt-evaluation.md) first. Turn thinking on only if accuracy is still short after prompt work. There is no universal rule — the eval decides.

API: a thinking flag plus `thinking_budget` (minimum 1024 tokens). The budget is a ceiling on thinking tokens; tune it with evals, not folklore. A magic string exists to force redacted content so you can test handling — not for production prompts.

## Image support

Claude accepts images as message parts alongside text. Limits: at most 20 images per request across all messages; size/dimension caps apply; tokens scale with pixel area (height × width). One image part per image.

Accuracy is mostly a **prompting** problem, not an image-quality problem. A weak prompt ("How many marbles?") miscounts (13 instead of 12). Apply the same techniques as [text prompting](prompt-techniques.md):

1. **Step-by-step analysis** — sequential steps, a recount/verify pass, compare results.
2. **One-shot / multi-shot** — alternate image parts with text parts: example image → explanation → target image → question.

Worked domain: insurance fire-risk from satellite imagery — identify the residence, tree density, fire-service access, roof overhang, then a structured score and summary. The criteria live in the prompt, not in hope.
