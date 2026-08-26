---
type: failure-taxonomy
title: 'Watch-out: the discovery call that turned into a design session'
description: 'Failure trace: two stakeholder statements produced a plausible sketch. Licensed authorization, PHI handling, and two-state retention never got asked, and they surfaced two weeks later in compliance review.'
tags: [claude, certification, stakeholder-engagement]
---

# The discovery call that turned into a design session

SETUP
Discovery is where the work starts. Design is where it accelerates. A good Architect begins forming a solution partway through the call. Sketching and visualizing it feels productive, and the stakeholder seems pleased to see progress. That is exactly the moment the questions stop.

## A reconstructed discovery call, where the questions stopped early

In the exchange below, the Architect hears two stakeholder statements and begins proposing a solution. The stakeholder confirms the initial proposal because it sounds competent. The constraints that would have ruled out that architecture are never identified. They emerge two weeks later during a compliance review. This section shows exactly where the question that would have caught each constraint belonged. Use this example to learn to recognize the pattern in your own calls.

RECONSTRUCTED EXCHANGE

Stakeholder: "We run a regional hospital network. Nurses spend forever writing up patient interactions. We want Claude to draft the clinical note from their dictation."

Architect: "Got it, that's just a clean augmented pattern. Claude takes the dictation, drafts the structured note, then writes it back. We can have a prototype next week."

Stakeholder: "That sounds right. There's a review step in there somewhere, but it's just a quick check."

Architect: "Sure, we'll add a review step. Let me start with the design."

## Constraints identified too late to be an easy fix

The "quick check" was not a convenience feature. The nursing workflow required a licensed clinician to authorize any model output before it reached the patient record. This made human authorization a required architectural gate as opposed to an optional addition. The dictation contained protected health information. Protected health information moved through the context window without the handling that the workflow required. The network spanned two states with different record-retention rules, and the single-region design never accounted for either. None of these requirements were unusual or hard to find. Each would have come out of a direct question in the must-prove and must-not-do categories, had the call not moved to sketching before those questions were asked.

WHY THIS BROKE: A COMPETENT SKETCH PROPOSAL ENDED THE QUESTIONS A DISCOVERY CALL EXISTS TO ASK

The sketch was plausible, and plausibility is what makes this dangerous. A stakeholder who hears a confident architecture assumes the Architect has the information to build it. The move that protects you is boring: finish the four-category question set before proposing anything, and treat every "it's just a review" as a constraint to chase down.
← Previous
Screen 3 of 20
☰ CONTENTS
Next →
