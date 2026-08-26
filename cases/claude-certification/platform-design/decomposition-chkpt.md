---
type: validation-walkthrough
title: 'Checkpoint: sort field-service capabilities by owner'
description: 'Place eight field-service capabilities into Claude, existing systems, or human buckets using the four-properties lens.'
tags: [claude, certification, platform-design, checkpoint]
---

Sort the field-service capabilities
A field-service partner has handed you a request list for a knowledge assistant their engineers will use on-site. Click a capability to select it, then click the right owner bucket to place it. All 8 items must be placed before submitting.

Summarize the engineer's case notes into a one-page handover
Return the current stock level of part SKU 78-A at the closest warehouse
Approve a refund above £2,000 if the engineer requests one
Extract the part number from a photo of the unit label
Calculate the total billable time across three job tickets
Draft a follow-up email to the customer explaining the delay
Tell the engineer whether the warranty applies to this serial number
Decide whether to escalate a safety incident to the field manager
CLAUDE
Summarize the engineer's case notes into a one-page handover
Extract the part number from a photo of the unit label
Draft a follow-up email to the customer explaining the delay
EXISTING SYSTEMS
Return the current stock level of part SKU 78-A at the closest warehouse
Calculate the total billable time across three job tickets
Tell the engineer whether the warranty applies to this serial number
HUMAN
Approve a refund above £2,000 if the engineer requests one
Decide whether to escalate a safety incident to the field manager
Submit
Skip for now
Cleanly decomposed. Everything in the What Claude does bucket is a task where next-token prediction is in its capability zone; every authoritative or consequential item went elsewhere. That's the lens at work.

Decompose the request
A partner brief is below. For each step, select the right owner: what Claude does, what existing systems do, or what humans do. The previous checkpoint tested whether you could recognize the four properties; this one tests whether you can decompose the split.

THE BRIEF
A regional logistics partner wants an assistant that, for each inbound shipping exception: reads the carrier's free-text exception note, decides whether the shipment qualifies for an automatic refund under the partner's published policy, looks up the customer's contract tier, drafts a notification to the customer, and issues the refund.
Read the carrier's free-text exception note	Claude  Existing System  Human
Decide whether the shipment qualifies for an automatic refund under the partner's published policy	Claude  Existing System  Human
Look up the customer's contract tier	Claude  Existing System  Human
Draft the customer notification	Claude  Existing System  Human
Issue the refund	Claude  Existing System  Human
Submit
Skip for now