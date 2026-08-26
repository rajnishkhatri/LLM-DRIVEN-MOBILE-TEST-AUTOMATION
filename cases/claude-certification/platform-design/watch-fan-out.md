---
type: failure-taxonomy
title: 'Watch-out: when fan-out hid a dropped unit'
description: 'Failure trace: a 50-section contract review reported 48 reviewed because synthesis counted returned results, not dispatched units. Coverage was assumed, not verified.'
tags: [claude, certification, platform-design, failure-taxonomy]
---

When fan-out hid a dropped unit
The trace

A compliance team built a multi-agent system to check a 50-section vendor contract against an internal policy checklist. The orchestrator fanned the work out to one subagent per section, each returning a pass/flag verdict, and synthesized a clean summary: "48 sections reviewed, 3 flagged." The summary read as complete and was circulated to the legal lead.

Two sections had never been reviewed. One subagent had timed out and returned nothing; another had failed to parse a scanned page and returned an empty result. The orchestrator, given no coverage check, counted only the results it received and reported "48 reviewed", but there were 50 sections, and nobody had told the synthesis step to reconcile the count.

What broke and why

No coverage check at synthesis. The orchestrator synthesized over the results it happened to receive, with no rule that the number of results must equal the number of units dispatched.
A recoverable failure was never recovered. A timed-out subagent is the recoverable case, but only if something retries it or flags the gap. Here the failure was silent because nothing was watching the boundary.
Confident synthesis over incomplete work. The output's fluency masked the gap. A multi-agent system fails most dangerously when the summary looks complete and is not.
WHY THIS BROKE
Completeness was assumed, not verified. The orchestrator dispatched 50 units and reported on the results it received. Two units never came back, and nothing in the design noticed the difference. Three gaps lined up to let that through.
The count was never reconciled. The synthesis step added up the verdicts it received and stopped there. No rule said the number of results had to match the number of units dispatched, so 48 returned results became "48 reviewed" instead of "two are missing."
A recoverable failure had nothing watching it. A timed-out subagent and an empty parse result are both the recoverable case, but only when something retries the unit or flags the gap. No component owned the subagent boundary, so both failures passed silently.
The output read as complete. The summary was fluent and well-formed, which is exactly what made the gap invisible. A multi-agent system fails most dangerously when a confident summary is built over work that was never finished. The fix is a coverage check at synthesis: results returned must equal units dispatched, or the run flags the difference before anyone reads the summary.
← Prev
Screen 14 of 34
☰ CONTENTS
Next →
Critique the orchestration design
DRAFT ARCHITECTURE SUBMITTED FOR REVIEW
Below is a draft multi-agent architecture submitted for review: an orchestrator fanning a large document-classification job out to subagents. Six components are listed. Select the three that carry a control or failure-boundary defect.
Select exactly 3 components that carry a control or failure-boundary defect.

1

Orchestrator decomposes the corpus into per-document units
↓
2

Subagents run in parallel, each returns a verdict
↓
3

Synthesis sums returned verdicts into a report
↓
4

Irreversible action (auto-archive) taken with no human gate
5

No retry or gap-flag on a failed subagent
6

Shared trace ID propagated to every subagent
Submit
Skip for now
You found all three. Notice what they share: each is a place where a failure or a high-stakes action crosses a boundary unobserved. That's where multi-agent designs break.
← Prev
