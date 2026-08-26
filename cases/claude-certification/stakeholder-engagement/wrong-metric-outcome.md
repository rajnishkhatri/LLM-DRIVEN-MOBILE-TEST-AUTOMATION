---
type: failure-taxonomy
title: 'Watch-out: the outcome document that measured the wrong thing'
description: 'Failure trace: volume, latency, and error rate proved the system ran. The CFO asked what claim-processing time did before and after, and the document could not answer.'
tags: [claude, certification, stakeholder-engagement]
---

# The outcome document that measured the wrong thing

SETUP
A deployment that performed well during a controlled rollout has data behind it. An Architect closing the engagement has everything they need to write the outcome document. Writing it quickly from the metrics already on hand feels like the right move, and the engagement is over before anyone notices what the document cannot answer.

## An anecdote: the outcome document that could not survive a CFO's first question

An Architect produced a customer outcome document using the metrics easiest to export from the observability stack: request volume, average latency, and error rate. The customer sponsor took it to their CFO to justify expanding the deployment. The CFO's first question was what the deployment had saved or produced in business terms, and the document could not answer it. The two fields that would have made it usable were never filled in. This is how that played out.

The sponsor opened with the document as written: "Here's the deployment. Forty thousand requests a month, sub-two-second average latency, error rate under half a percent."

The CFO: "That tells me it runs. What did it do for us? What were claim processing times before this, and what are they now? Because that's the number that justifies spending more."

The sponsor had no evidence to point to. The document measured that the system worked, but it didn't measure what it changed.

## What broke: the document captured technical metrics without business outcomes

Volume, latency, and error rate are real and worth tracking, but none of them are a business outcome. The fields that would have made the document usable for the CFO conversation were the before-and-after on the business metric the use case targeted, claims-processing time, and the control that made that comparison auditable. Without the before number, there is no story. Without control, the after number is an assertion. The document was complete as a technical record and useless as a case for expansion.

WHY THIS BROKE: THE EASY-TO-EXPORT METRICS ARE RARELY THOSE THAT JUSTIFY COST

The observability stack collects your technical metrics for free, but without anchoring them in business data you are left with dashboards that look informative and mean nothing. The outcome document exists for a different reader: the sponsor who must justify the deployment upward. Capture the before metric at the start, name the control that makes the comparison auditable, and add the reuse note, so the document can do the one job a technical dashboard cannot.
← Previous
Screen 15 of 20
☰ CONTENTS
Next →
