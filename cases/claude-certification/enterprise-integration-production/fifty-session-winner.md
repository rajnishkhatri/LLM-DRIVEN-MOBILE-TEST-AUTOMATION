---
type: failure-taxonomy
title: 'Watch-out: the 50-session winner that wasn''t'
description: 'Failure trace: a 50-session prompt comparison looked like a 6-point win. The sample was underpowered, inputs were uncontrolled, and the metric was chosen after the fact.'
tags: [claude, certification, enterprise-integration-production]
---

The 50-session winner that wasn't
WHY THIS MISTAKE IS EASY TO MAKE
Running a proper A/B test takes time, requires sample size calculation, and can take days or weeks to reach significance. Comparing 50 sessions of the new version to 50 sessions of the old version takes an afternoon. A 50-session comparison that looks positive is a confirmation check rather than a meaningful test. The sample is too small to distinguish signal from noise.
The prompt change that looked like a win
The following is a composite representing a pattern that surfaces in teams that have a working system and want to improve it but do not have a formal experimentation process.

A team running a customer service agent wanted to test a revised instruction in the system prompt. They ran the new version against 50 customer sessions and the old version against 50 sessions. The task success rate was 68% on the new version and 62% on the old version. They declared the new version a winner and deployed it.

Two weeks later, the task success rate on the new version had settled at 61%. The apparent 6-point gain had disappeared.

What broke
The comparison had three problems, any of which was sufficient to invalidate the result.

The sample size was too small. A 6-point difference on a metric with high variance requires a sample size in the hundreds to reach statistical significance. At 50 sessions per group, the observed difference was within the noise floor.
The input distribution was not controlled. The 50 sessions in the treatment group happened to contain fewer edge-case inputs than the 50 sessions in the control group. The apparent improvement was partly an artifact of which inputs were routed to which group.
The primary metric was not pre-specified. The team compared the task success rate because it moved in the right direction. If it had moved in the wrong direction, they would have looked at another metric. Selecting the metric after seeing the result turns a test into a search for whatever metric happened to move.
WHAT TO WATCH OUT FOR
An underpowered experiment with metric selection after the fact produces confirmation rather than evidence, since the result reflects the hypothesis you started with. The result was noise, and the noise looked like a signal because the sample was too small to tell the difference.
← Previous
Screen 15 of 21
☰ CONTENTS
Next →
