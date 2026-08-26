---
type: validation-walkthrough
title: 'Checkpoint: justify the feasibility call'
description: 'For each scenario, name both the feasibility verdict and the single load-bearing constraint. A verdict without the constraint is not defensible.'
tags: [claude, certification, enterprise-integration-production]
---

Justify the feasibility call
For each scenario, choose the option that names both the correct feasibility verdict and the single load-bearing constraint behind it. The verdict alone is not enough, the constraint is what makes the verdict defensible.

SCENARIO 1 OF 3
A professional-services firm wants a research assistant that summarizes 10–40 page industry reports and drafts client briefings. 50 reports per week, briefings within 24 hours, $500/month ceiling.

A. Not feasible, the reports are too long for the context window.
B. Feasible as scoped, input size fits the context window, and volume, latency, and cost are all within range at the Sonnet tier; no AI property presents a disqualifying constraint.
C. Feasible with constraints, needs a human review gate on every briefing.
CORRECT.
All four AI properties are evaluated. The input size (10–40 pages) fits well within Sonnet's context window. Volume (50/week) is low and easily handled. The 24-hour latency target is generous. The $500/month ceiling is feasible at the Sonnet tier for this volume. No AI property presents a disqualifying constraint.
SCENARIO 2 OF 3
A logistics company wants a delay predictor that reads unstructured carrier emails, extracts delay reasons and new ETAs, and writes them to the order-management system. 5,000 emails/day, under 10 seconds, $1,000/month.

A. Feasible as scoped, Haiku with caching handles the volume and latency.
B. Not feasible, the volume is too high.
C. Feasible with constraints, the load-bearing constraint is extraction accuracy on a transactional write, so it requires a code-based eval on extraction accuracy plus a human review gate on low-confidence extractions before writing to the system of record.
CORRECT.
The load-bearing constraint is extraction accuracy on a transactional write. Getting the ETA wrong and writing it to the order-management system has real downstream consequences. A code-based eval on extraction accuracy is appropriate because the output is structured (dates and reasons) and scoreable against the carrier email. Low-confidence extractions need a human gate before the write.
SCENARIO 3 OF 3
A financial-services firm wants real-time trading recommendations from current market conditions plus its proprietary model, delivered in under 2 seconds.

A. Not feasible as described, the load-bearing constraint is the live-state knowledge gap: real-time market data requires a tool call to a live feed, and whether that round trip fits inside the 2-second budget must be validated before any feasibility verdict can be issued.
B. Feasible as scoped, Claude already knows current market conditions.
C. Feasible with constraints, just add a human gate.
CORRECT.
Claude's training data has a knowledge cutoff, real-time market data is not available in the model's base knowledge. The system needs a tool call to a live data feed. Whether that round trip, tool call, data retrieval, model response, fits inside a 2-second budget must be tested before any feasibility verdict can be issued. Issuing a feasibility verdict before this is confirmed is the same mistake as the scoping call that skipped the constraints.
Skip for now
← Previous
Screen 10 of 21
☰ CONTENTS
Next →
