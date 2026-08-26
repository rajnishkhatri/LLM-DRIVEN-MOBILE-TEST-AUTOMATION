---
type: validation-walkthrough
title: 'Checkpoint: find the undocumented assumption'
description: 'Three requirements trace to something the stakeholder said; sixty-day transcript retention does not. An unsourced assumption is the item that nobody remembers deciding.'
tags: [claude, certification, stakeholder-engagement]
---

# Checkpoint: find the undocumented assumption

Try it now. Below is a discovery-call summary and the requirements document an Architect produced from it. Three items trace to something the stakeholder said; one is an assumption the Architect made without surfacing the constraint underneath it. Choose the item that is the undocumented assumption, then confirm that no stakeholder statement supports it.

REQUIREMENTS DOCUMENT

1. Claude drafts the customer email, but a person actually sends it.
2. Responses must return within a two-second perceived budget.
3. Refunds above the threshold route to a human approver.
4. Conversation transcripts are retained for sixty days for analytics.

WHAT THE STAKEHOLDER SAID

- "Anything big requires a person's sign off."
- "Draft the reply, but we send it ourselves."
- "It has to feel instant to the user."

Part 1: Which item is the undocumented assumption?

- A. Item 1, email drafting with human send
- B. Item 2, two-second latency budget
- C. Item 3, refund routing to human approver
- D. Item 4, sixty-day transcript retention

Reveal model answer
Skip for now

MODEL ANSWER

D. Item 4, sixty-day transcript retention.

Item 1 traces to "Draft the reply, but we send it ourselves." Item 2 traces to "It has to feel instant to the user" (the two-second figure is a translation of "instant," and should still be labeled as an assumption to confirm, but it has a stakeholder source). Item 3 traces to "Anything big requires a person's sign off." Item 4 has no stakeholder statement behind it. Retention period and analytics purpose were never said. An unsourced assumption is the most dangerous kind, because nobody remembers deciding it.
← Previous
Screen 4 of 20
☰ CONTENTS
Next →
