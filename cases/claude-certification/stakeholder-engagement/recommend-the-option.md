---
type: validation-walkthrough
title: 'Checkpoint: recommend the option and name the missing element'
description: 'Recommend the logging-in option for a regulated high-volume insurer. Option B is missing reversal cost; option C violates the audit-trail constraint.'
tags: [claude, certification, stakeholder-engagement]
---

# Checkpoint: recommend the option and name the missing element

Try it now. Read the one-paragraph stakeholder briefing and the three option presentations written in plain language. One option is technically accurate and presented comprehensively. One is technically accurate, but its presentation is missing an element. One is inappropriate for the stated constraints. Recommend the option to put forward, then name the single element missing from the second option's presentation.

BRIEFING

A mid-sized insurer wants Claude to draft adjuster responses to policyholder queries. The workflow is covered by state insurance regulation with an audit-trail obligation. Volume is high and steady. The sponsor cares about response quality and about keeping a defensible record of every automated interaction.

| Option | Presentation as shown |
|---|---|
| A | Workflow pattern with per-interaction logging built in. Gains: full audit trail, quality gate before sending. Gives up: a small latency cost from the logging step. Reversal: minor, logging can be tuned without redesign. |
| B | Workflow pattern that trades the logging step for lower latency. Gains: faster responses. Gives up: per-interaction audit detail. |
| C | Single augmented call with no logging and no human gate, chosen for lowest build cost. |

Part 1: Which option should you recommend?

- A. Option A, logging built in, full audit trail
- B. Option B, trades logging for lower latency
- C. Option C, no logging, no human gate

Reveal model answer
Skip for now

MODEL ANSWER

Recommend option A. The audit-trail obligation is a must-prove constraint from discovery; logging is load-bearing, not optional. Option C is inappropriate for the stated constraints: it drops both logging and a human gate in a regulated, high-volume workflow. Option B is technically accurate as a tradeoff (latency versus audit detail) but its presentation is missing the reversal-cost element: what it costs to restore logging after the system is built around the latency gain, and the compliance exposure of any gap period. That missing third element is the one that would have changed the meeting.
← Previous
Screen 7 of 20
☰ CONTENTS
Next →
