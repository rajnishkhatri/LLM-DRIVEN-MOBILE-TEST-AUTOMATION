---
type: failure-taxonomy
title: 'Watch-out: the observability stack that replaced the feedback loop'
description: 'Failure trace: eval score drifted from week four with no hard alert. Nothing mapped slow quality drift to a review trigger, so the stakeholder noticed in week twelve.'
tags: [claude, certification, stakeholder-engagement]
---

# The observability stack that replaced the feedback loop

SETUP
An Architect who has built a rigorous observability stack has done the harder technical work. The dashboards are live, the alerts are configured, and the data is flowing. It is easy, and reasonable, to conclude that stakeholder feedback is covered.

## A reconstructed trace: ninety days of alert log against the stakeholder review calendar

The excerpt below places a deployment alert log next to its stakeholder review calendar over a ninety-day window. The alert log shows a sustained drift in output quality across weeks four through seven. The review calendar shows no review that happened in that window. A single row in a feedback-loop governance table would have connected the two. This shows what the gap looks like in the record.

| Window | Observability stack recorded | Stakeholder review calendar | What the loop should have done |
|---|---|---|---|
| Weeks 1–3 | Eval score steady at baseline, with latency and cost nominal. | Launch review held in week 1. | Nominal. No escalation needed. |
| Weeks 4–7 | Eval score drifting down week over week, with error rate flat, so no hard alert is fired. | No review scheduled or held. | A quality-drift trigger should have escalated to an Architect review by week 5, and onward to a stakeholder review once diagnosis confirmed the drift. |
| Weeks 8–12 | Score is still declining, and the stakeholder reports the output is "less useful lately." | Quarterly review finally surfaces it in week 12. | By design, the loop would have caught this seven weeks earlier. |

## The issue: the signals existed, but nothing decided they mattered

Every metric the deployment needed was already being collected. The eval score was visibly drifting downward since week four. What was missing was the decision layer: no governance rule mapped a slow quality drift to a review trigger. The drift never crossed an error-rate threshold, so no alert fired. A drift with no trigger is invisible until a human happens to notice. The stack was measuring the right thing and telling no one it mattered.

WHY THIS BROKE: MONITORING IS NOT A FEEDBACK LOOP

A dashboard collects and displays signals. A feedback loop maps each signal to a trigger, an owner, and a required action. The observability stack collected the signals but had no governance rule mapping any signal to a trigger or owner. Build the governance table that maps each signal to a trigger, an action, and an owner. Include both the slow drifts and the hard failures.
← Previous
Screen 9 of 20
☰ CONTENTS
Next →
