---
type: validation-walkthrough
title: 'Checkpoint: cost and reliability calculator'
description: 'Find a configuration that meets an $800/month ceiling and 3s p95. Prompt caching on a stable 5,000-token system prompt is the load-bearing lever.'
tags: [claude, certification, enterprise-integration-production]
---

Cost & reliability calculator
Use the calculator to explore configurations. Adjust the model tier, prompt caching, max_tokens cap, and call-volume multiplier; the readouts show monthly cost and p95 latency for each setting. Your goal: find a configuration that meets both the cost ceiling and the latency target at the same time. The calculator only displays values; it does not score your exploration. (Figures are representative for modeling; confirm current rates at publish time.)

Scenario
A customer service agent processes 50,000 requests per month. The system prompt is 5,000 tokens and stable across requests. Average user input is 300 tokens, average output is 400 tokens. The cost ceiling is $800/month. The p95 latency target is 3 seconds.
Model tier

Prompt caching

On
Max_tokens cap: 512

Call-volume multiplier: 1.0×

EST. MONTHLY COST
$720
Cost ceiling: $800/mo
P95 LATENCY
2.5s
Latency target: ≤3s
Decision: Once you have a configuration that meets both targets, which lever did the most work to get there?

A. Switching to Opus, because the most capable model is always safest.
Incorrect: Opus is the most expensive tier and would push cost over the ceiling at this volume.
B. Turning prompt caching on, because the 5,000-token system prompt is stable across all 50,000 requests, so caching it cuts the dominant input-cost driver.
Correct.
C. Raising the max_tokens cap, because more headroom improves quality.
Incorrect: a higher cap raises cost and latency; it does not help meet either target.
Submit
Skip for now
CORRECT
Right. The stable 5,000-token system prompt is read on every one of the 50,000 calls, so caching it is the single lever that moves cost the most. With caching on at the Haiku or Sonnet tier, both the cost ceiling and the 3-second p95 target are reachable.
← Previous
Screen 7 of 21
☰ CONTENTS
