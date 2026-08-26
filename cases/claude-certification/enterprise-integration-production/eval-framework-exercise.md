---
type: validation-walkthrough
title: 'Exercise: define the evaluation framework'
description: 'Draft metrics and grading methods for a claims intake system across accuracy, latency, safety, security, and cost. Prefer code-based checks wherever the behavior is unambiguous.'
tags: [claude, certification, enterprise-integration-production]
---

Exercise: define the evaluation framework
THE BRIEF
A regional insurer is deploying a Claude system that reads a submitted claim, extracts structured fields (claimant, policy number, loss amount, date of loss), summarizes the narrative for an adjuster, and flags claims that may warrant fraud review. The system must respond within a few seconds, stay within a defined per-claim cost, never leak one claimant's data into another's summary, and never auto-deny a claim.
Draft the evaluation framework for this system. For each of the five dimensions below, write the metric, the grading method (code-based eval, LLM judge, or human review), and a one-sentence reason for your choice. Write your framework, then reveal the model answer below.

[Click-to-reveal an answer to compare with your response; feel free to ask Claude to compare what you've written with the provided answer.]

1. Accuracy: field extraction

2. Latency: response time

3. Safety: summary faithfulness and no auto-deny

4. Security: no cross-claimant data leakage

5. Cost: per-claim spend

Reveal model answer
Skip for now
MODEL ANSWER
1. Accuracy, field extraction: Code-based eval. The expected values (claimant name, policy number, loss amount, date of loss) are known and verifiable by exact or schema match. No interpretation required; a function checks the output against the ground truth.
2. Latency, response time: Code-based eval. Latency p95 is a number. The check is whether it falls below the target. No judgment involved.
3. Safety, summary faithfulness and no auto-deny: Two methods required. Code-based eval for the deny action (binary, either a denial was issued or it was not). LLM judge for summary faithfulness (whether the narrative accurately represents the source claim without fabrication is an interpretive task a function cannot encode).
4. Security, no cross-claimant data leakage: Code-based eval. Cross-claimant leakage can be checked by scanning each summary for identifiers that appear in any input claim other than the one being processed. Deterministic check, no interpretation needed.
5. Cost, per-claim spend: Code-based eval. Cost is a numeric value derived from input tokens, output tokens, model tier, and whether prompt caching applies. The check is whether it exceeds the ceiling.
Mark complete
← Previous
Screen 17 of 21
